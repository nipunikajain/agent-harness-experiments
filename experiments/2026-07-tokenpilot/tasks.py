"""Deterministic multi-hop 'referral chain' task over a small local web of noisy-HTML documents.

This is the FIXED task shared by both conditions (baseline and TokenPilot). Nothing here depends
on the harness strategy — only on the seed — so a given seed produces byte-identical documents and
questions for both conditions. The only thing that differs between conditions is how the harness
(intervention.py) *ingests* the tool observations these docs produce.

Each question is a chain of K record documents. The starting record is named in the question; each
record's main content points to the id of the NEXT record in the chain; the final record names a
destination city, which is the answer. Solving a question therefore requires opening K documents in
sequence and following the pointer each time — a long-horizon trajectory whose context accumulates.

Every record is wrapped in ~3 KB of HTML boilerplate (nav, cookie banner, inline scripts, styling,
legal footer). That boilerplate is pure token noise: TokenPilot's observation reduction is supposed
to strip it while preserving the pointer / destination fact. If reduction were too aggressive it
would drop the pointer and the chain would break — exactly the failure mode we want to be able to
see. Because a chain accumulates several large observations, this task also gives the eviction and
prompt-caching mechanisms something substantial to act on.
"""

from __future__ import annotations

import random
import re

CITIES = ["Lagos", "Osaka", "Quito", "Tromso", "Perth", "Recife", "Nantes", "Dhaka",
          "Tallinn", "Merida", "Bergen", "Kochi", "Cusco", "Ghent", "Hobart", "Leon"]

# ~3 KB of boilerplate chrome wrapped around every record. Deterministic (no per-doc state) so it
# strips/dedupes identically for every document — mirrors real, repeated page chrome.
_HEAD = (
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<script>window.__cfg={ab:1,exp:'ctrl',region:'intl',flags:['x','y','z']};"
    "function track(e){/* analytics beacon */}function consent(){/* cmp */}</script>"
    "<style>.nav{display:flex;gap:12px}.footer{color:#888;font-size:11px}"
    ".banner{background:#eee;padding:8px}.crumbs{color:#aaa}</style></head><body>"
    "<nav class='nav'><a href='/'>Home</a><a href='/dir'>Directory</a><a href='/records'>Records</a>"
    "<a href='/help'>Help</a><a href='/status'>System status</a><a href='/login'>Sign in</a></nav>"
    "<div class='crumbs'>Home &rsaquo; Records &rsaquo; Referral registry &rsaquo; Entry</div>"
    "<div class='banner'>We use cookies and similar technologies to operate this internal site, "
    "remember your preferences, and measure usage. By continuing to browse the referral registry "
    "you acknowledge our internal cookie policy. You can manage non-essential cookies at any time "
    "from the preferences panel in your account settings. This banner will not be shown again on "
    "this device for the remainder of your session.</div>"
)
_FOOT = (
    "<div class='footer'><p>&copy; 2026 IntraCorp Referral Registry. All rights reserved.</p>"
    "<p>Terms of Service &middot; Privacy Policy &middot; Acceptable Use Policy &middot; Data "
    "Retention Schedule &middot; Contact the internal help desk for access issues.</p>"
    "<p>This registry page is confidential and intended solely for authorized internal use. Do not "
    "forward, distribute, or reproduce its contents outside the organization. Access is logged.</p>"
    "<p>If you believe you have reached this page in error, return to the directory and re-run your "
    "query. Stale links are pruned nightly by the registry maintenance job.</p>"
    "<script>track('pageview');consent();</script></div></body></html>"
)


def _rid(q: int, node: int) -> str:
    return f"record/{q}-{node}"


def build_world(seed: int, n_questions: int = 5, chain_len: int = 4):
    """Deterministically build the document set and the list of chain-following questions.

    Returns (docs, questions). Each question is a dict {id, prompt, answer, chain} where `chain`
    is the ordered list of record ids that must be opened (used only for logging, never shown).
    """
    rng = random.Random(seed)
    docs: dict[str, str] = {}
    questions = []

    for q in range(n_questions):
        # A random permutation of node indices so the pointer order is not the id order — the
        # agent must actually read each pointer rather than guessing record/q-0, record/q-1, ...
        nodes = list(range(chain_len))
        rng.shuffle(nodes)
        city = rng.choice(CITIES)
        chain_ids = [_rid(q, n) for n in nodes]

        for i, node in enumerate(nodes):
            rid = _rid(q, node)
            if i < chain_len - 1:
                nxt = _rid(q, nodes[i + 1])
                fact = (f"<p>This record is an intermediate hop in a referral chain.</p>"
                        f"<p>Next record: <b>{nxt}</b>.</p>"
                        f"<p>Continue to the next record to proceed toward the destination.</p>")
            else:
                fact = (f"<p>This record is the final hop in the referral chain.</p>"
                        f"<p>Final destination city: <b>{city}</b>.</p>"
                        f"<p>The chain ends here; no further records follow.</p>")
            docs[rid] = (
                _HEAD
                + f"<main class='content'><h1>Registry record {rid}</h1>"
                + "<p>Status: active. Verified: yes. Registry segment: referral.</p>"
                + fact
                + "<p>This entry is maintained by the registry service and is reviewed "
                  "periodically for accuracy as part of routine data hygiene.</p></main>"
                + _FOOT
            )

        start = chain_ids[0]
        questions.append({
            "id": f"q{q}",
            "prompt": (f"Trace the referral chain that begins at document '{start}'. Open each "
                       f"record, follow its 'Next record' pointer to the following record, and "
                       f"continue until you reach the final record. Report ONLY the destination "
                       f"city named in that final record."),
            "answer": city,
            "chain": chain_ids,
        })
    return docs, questions


# --------------------------------------------------------------------------------------
# Observation reduction — the deterministic rule-based pass used by the TokenPilot condition.
# Baseline appends the raw HTML instead. Kept here so the exact same document strings feed both.
# --------------------------------------------------------------------------------------
def reduce_observation(html: str, max_chars: int = 600) -> str:
    """Strip HTML chrome, keep the main content, truncate to `max_chars`.

    Keeps only the <main class='content'> region, drops <script>/<style>, strips remaining tags and
    entities, collapses whitespace, dedupes repeated lines, then truncates. Intended to preserve the
    'Next record' pointer or 'Final destination city' fact while discarding nav/cookie/footer noise.
    """
    m = re.search(r"<main[^>]*>(.*?)</main>", html, flags=re.DOTALL | re.IGNORECASE)
    core = m.group(1) if m else html
    core = re.sub(r"<script.*?</script>", " ", core, flags=re.DOTALL | re.IGNORECASE)
    core = re.sub(r"<style.*?</style>", " ", core, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", core)
    text = re.sub(r"&[a-z]+;", " ", text)
    lines = [ln.strip() for ln in re.split(r"[\n.]", text) if ln.strip()]
    seen, deduped = set(), []
    for ln in lines:
        if ln not in seen:
            seen.add(ln)
            deduped.append(ln)
    out = re.sub(r"\s+", " ", ". ".join(deduped)).strip()
    if len(out) > max_chars:
        out = out[:max_chars] + " …[truncated; use recover() for full document]"
    return out


def grade(submitted: str, expected: str) -> bool:
    """Correct iff the expected destination city appears as a standalone word in the submission.

    The prompt asks for a bare city name, but a correct answer wrapped in a sentence still counts.
    City names in this world are distinct tokens, so a word-boundary match is unambiguous. The same
    rule is applied to both conditions, so it cannot bias the direction of the comparison.
    """
    if not submitted:
        return False
    return re.search(rf"\b{re.escape(expected.lower())}\b", submitted.lower()) is not None
