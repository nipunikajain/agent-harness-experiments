"""Build the static research-queue dashboard.

Reads ``queue.md`` (scout proposals) and the results table in ``README.md`` (tested verdicts)
and writes a single self-contained ``index.html``. Standard library only, so the GitHub Pages
workflow needs no install step.

    python dashboard/build.py [--out _site]

The dashboard is a read-only view: ``queue.md`` and ``README.md`` stay the source of truth.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "template.html"

SECTION_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})\b")
ENTRY_RE = re.compile(r"^### \[(.+?)\]\((\S+?)\)")
FIELD_RE = re.compile(r"^- ([A-Za-z ]+?):\s*(.*)$")

STATUSES = ("proposed", "queued", "testing", "done", "rejected")

# --------------------------------------------------------------------------------------
# Categories. An entry can pin its own with a `- Category: <name>` line in queue.md;
# otherwise it is scored against these keyword patterns and the best-scoring category wins,
# ties going to the earlier one. A title hit outweighs the claim, whose hits are capped so
# one repeated word cannot decide it. Matching is on title + claim only: "Why it matters"
# mentions this repo's harness results in nearly every entry.
# --------------------------------------------------------------------------------------
FALLBACK_CATEGORY = "Harness design & evolution"
CATEGORIES: list[tuple[str, str]] = [
    (
        "Security & safety",
        r"prompt[- ]injection|attack|poison|security|red-?team|least-privilege|safety|unsafe"
        r"|adversarial|governance|defen[sc]e|vulnerab|identity confusion|abstain|abstention"
        r"|escalation|evasion|exploit|attest|covert",
    ),
    (
        "Memory",
        r"\bmemor(?:y|ies)\b",
    ),
    (
        "Context management",
        r"context (?:management|engineering|compaction|rot|construction|pruning)|compaction"
        r"|context-management|long-context|context window|\bcontext\b",
    ),
    (
        "MCP & tool use",
        r"\bMCP\b|model context protocol|tool[- ]call|tool description|tool[- ]selection"
        r"|tool[- ]us(?:e|ing)|tool registry|\btools?\b",
    ),
    (
        "Multi-agent & orchestration",
        r"multi-agent|orchestrat|sub-?agents?|coordinat|\bMAS\b|decentralized",
    ),
    (
        "Serving & inference",
        r"KV[- ]?cache|speculative decoding|vLLM|\bserving\b|inference (?:server|engine|cost)"
        r"|throughput|prefix cach|quantization|MLX\b|keepalive|decode|router",
    ),
    (
        "Evaluation & benchmarks",
        r"benchmark|\bbench\b|evaluat|audit|validity|judges?\b|pass@k|measur|empirical study",
    ),
    (
        FALLBACK_CATEGORY,
        r"harness|self-evolv|scaffold|\bloop\b|skill",
    ),
]
_CATEGORY_PATTERNS = [(name, re.compile(pat, re.IGNORECASE)) for name, pat in CATEGORIES]


def categorize(title: str, claim: str) -> str:
    # Spelled out, the protocol's name would count as a "context" hit.
    title, claim = (re.sub(r"model context protocol", "MCP", t, flags=re.I) for t in (title, claim))
    best, best_score = FALLBACK_CATEGORY, 0
    for name, pattern in _CATEGORY_PATTERNS:
        score = 4 * len(pattern.findall(title)) + min(len(pattern.findall(claim)), 3)
        if score > best_score:
            best, best_score = name, score
    return best


# --------------------------------------------------------------------------------------
# Per-entry facts pulled out of the free-text fields, for the at-a-glance chips.
# --------------------------------------------------------------------------------------
_NEEDS_GPU_RE = re.compile(
    r"needs? (?:a |raw |an? )?(?:GPU|local|open-weight)|GPU-required|not feasible on CPU"
    r"|not reproducible (?:via|through) the Claude API|Modal (?:GPU|A10G|T4|cost)",
    re.IGNORECASE,
)
_COST_RE = re.compile(r"cost[^$]{0,40}\$(\d+)(?:\s*[-–]\s*\$?(\d+))?", re.IGNORECASE)
_ARXIV_RE = re.compile(r"arxiv\.org/abs/(\d{4}\.\d{4,5})")
_DATE_RE = re.compile(r"(?:submitted|published|week of)\s+(\d{4}-\d{2}(?:-\d{2})?)")


def compute_needs(testability: str) -> str:
    return "gpu" if _NEEDS_GPU_RE.search(testability) else "api"


def cost_range(testability: str) -> str | None:
    m = _COST_RE.search(testability)
    if not m:
        return None
    low, high = m.group(1), m.group(2)
    return f"${low}–{high}" if high else f"${low}"


def source_kind(url: str) -> str:
    if "arxiv.org" in url:
        return "arXiv"
    if "github.com" in url:
        return "GitHub"
    return "Blog"


def normalize_status(raw: str) -> str:
    word = raw.strip().split()[0].lower() if raw.strip() else ""
    return word if word in STATUSES else "proposed"


def short_name(title: str) -> str:
    """The handle people use for a paper: the part before the colon, if it is short."""
    head = title.split(":", 1)[0].strip().strip('"“”')
    return head if len(head) <= 28 else ""


# --------------------------------------------------------------------------------------
# Parsers
# --------------------------------------------------------------------------------------
def parse_queue(text: str) -> list[dict]:
    entries: list[dict] = []
    run_date: str | None = None
    current: dict | None = None
    for line in text.splitlines():
        if m := SECTION_RE.match(line):
            run_date, current = m.group(1), None
        elif m := ENTRY_RE.match(line):
            if run_date is None:
                continue
            current = {"title": m.group(1), "url": m.group(2), "run": run_date, "fields": {}}
            entries.append(current)
        elif current is not None and (m := FIELD_RE.match(line)):
            current["fields"][m.group(1).strip().lower()] = m.group(2).strip()
        elif line.startswith("#") or line.strip() == "---":
            current = None

    # Runs that were merged late can re-propose a link an earlier run already had; keep the
    # earliest proposal of each.
    entries.sort(key=lambda e: e["run"])
    seen: set[str] = set()
    out = []
    for e in entries:
        key = e["url"].rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        f = e["fields"]
        claim, testability, source = f.get("claim", ""), f.get("testability", ""), f.get("source", "")
        url = e["url"] if e["url"].startswith(("https://", "http://")) else ""
        arxiv = _ARXIV_RE.search(url)
        published = _DATE_RE.search(source)
        out.append(
            {
                "id": len(out),
                "title": e["title"],
                "short": short_name(e["title"]),
                "url": url,
                "run": e["run"],
                "status": normalize_status(f.get("status", "")),
                "category": f.get("category") or categorize(e["title"], claim),
                "claim": claim,
                "why": f.get("why it matters", ""),
                "testability": testability,
                "source": source,
                "kind": source_kind(url),
                "arxiv": arxiv.group(1) if arxiv else None,
                "published": published.group(1) if published else None,
                "compute": compute_needs(testability),
                "cost": cost_range(testability),
            }
        )
    return out


def parse_scoreboard(text: str) -> list[dict]:
    """Rows of the `## Results log` table in README.md."""
    rows: list[dict] = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("| Technique |"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5 or set(cells[0]) <= {"-", " "}:
            continue
        link = re.search(r"\]\(([^)]+)\)", cells[4])
        rows.append(
            {
                "technique": cells[0],
                "date": cells[1],
                "result": cells[2],
                "verdict": cells[3],
                "link": link.group(1) if link else "",
            }
        )
    return rows


def build(out_dir: Path, repo_url: str) -> dict:
    entries = parse_queue((ROOT / "queue.md").read_text(encoding="utf-8"))
    if not entries:
        sys.exit("No entries parsed from queue.md — refusing to publish an empty dashboard.")
    scoreboard = parse_scoreboard((ROOT / "README.md").read_text(encoding="utf-8"))
    data = {
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "repo": repo_url,
        "categories": [name for name, _ in CATEGORIES],
        "entries": entries,
        "scoreboard": scoreboard,
    }
    # The JSON is inlined in a <script> block, so no literal "<" may survive in it.
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", payload, 1)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="_site", help="output directory (default: _site)")
    parser.add_argument(
        "--repo-url",
        default="https://github.com/nipunikajain/agent-harness-experiments",
        help="repository URL used for links back to queue.md and experiment notes",
    )
    args = parser.parse_args()
    data = build(ROOT / args.out, args.repo_url.rstrip("/"))
    latest = max(e["run"] for e in data["entries"])
    print(
        f"Built {args.out}/index.html: {len(data['entries'])} entries, "
        f"{len(data['scoreboard'])} tested, latest run {latest}"
    )


if __name__ == "__main__":
    main()
