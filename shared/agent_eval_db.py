"""Grader for the mini-SQL DB-harness experiment.

The agent must produce ``solution.py`` exposing a class ``Database`` with ``execute(sql)``.
Each feature is a short SQL battery; it passes iff the agent's engine returns the same
SELECT results as the reference engine (`shared/_db_reference.py`) on that battery. Truth is
defined by the reference running live, so there are no hand-transcribed expected outputs to
get wrong.

Non-ORDER-BY queries are compared as multisets (SQL leaves row order undefined without an
ORDER BY); ordering features compare the exact sequence. Floats (AVG) compare with tolerance.
"""

from __future__ import annotations

import contextlib
import importlib.util
import signal
import uuid
from pathlib import Path

from shared import _db_reference


@contextlib.contextmanager
def _time_limit(seconds: float):
    """Abort agent code that hangs (bad loop in solution.py) so a paid run can't stall.

    SIGALRM-based; only effective on the main thread (where the grader runs)."""
    def _handler(signum, frame):
        raise TimeoutError("grading timed out")

    old = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)

# A people/orders dataset reused (self-contained per feature, so checks never share state).
_PEOPLE = [
    "CREATE TABLE people (id, name, age, city)",
    "INSERT INTO people VALUES (1, 'Alice', 30, 'NYC')",
    "INSERT INTO people VALUES (2, 'Bob', 25, 'LA')",
    "INSERT INTO people VALUES (3, 'Carol', 35, 'NYC')",
    "INSERT INTO people VALUES (4, 'Dave', 28, 'SF')",
    "INSERT INTO people VALUES (5, 'Eve', 35, 'LA')",
]


def _f(fid, name, sqls, ordered=False, setup=_PEOPLE):
    return {"id": fid, "name": name, "sqls": list(setup) + list(sqls), "ordered": ordered}


FEATURES = [
    _f("f01", "create_insert_select", ["SELECT * FROM people"]),
    _f("f02", "select_columns", ["SELECT name, age FROM people"]),
    _f("f03", "where_eq", ["SELECT name FROM people WHERE city = 'NYC'"]),
    _f("f04", "where_neq", ["SELECT name FROM people WHERE city != 'NYC'"]),
    _f("f05", "where_lt", ["SELECT name FROM people WHERE age < 30"]),
    _f("f06", "where_gt", ["SELECT name FROM people WHERE age > 30"]),
    _f("f07", "where_range", ["SELECT name FROM people WHERE age >= 28 AND age <= 35"]),
    _f("f08", "where_and", ["SELECT name FROM people WHERE city = 'NYC' AND age > 30"]),
    _f("f09", "where_or", ["SELECT name FROM people WHERE city = 'SF' OR age = 25"]),
    _f("f10", "order_by_asc", ["SELECT name, age FROM people ORDER BY age"], ordered=True),
    _f("f11", "order_by_desc", ["SELECT name, age FROM people ORDER BY age DESC"], ordered=True),
    _f("f12", "limit", ["SELECT name, age FROM people ORDER BY age LIMIT 2"], ordered=True),
    _f("f13", "offset", ["SELECT name, age FROM people ORDER BY age LIMIT 2 OFFSET 2"], ordered=True),
    _f("f14", "distinct", ["SELECT DISTINCT city FROM people"]),
    _f("f15", "count_star", ["SELECT COUNT(*) FROM people"]),
    _f("f16", "sum", ["SELECT SUM(age) FROM people"]),
    _f("f17", "avg", ["SELECT AVG(age) FROM people"]),
    _f("f18", "min_max", ["SELECT MIN(age), MAX(age) FROM people"]),
    _f("f19", "group_by_count", ["SELECT city, COUNT(*) FROM people GROUP BY city"]),
    _f("f20", "group_by_sum", ["SELECT city, SUM(age) FROM people GROUP BY city"]),
    _f("f21", "like_prefix", ["SELECT name FROM people WHERE name LIKE 'A%'"]),
    _f("f22", "like_contains", ["SELECT name FROM people WHERE name LIKE '%e%'"]),
    _f("f23", "in_list", ["SELECT name FROM people WHERE city IN ('NYC', 'SF')"]),
    _f("f24", "between", ["SELECT name FROM people WHERE age BETWEEN 28 AND 35"]),
    _f("f25", "update", [
        "UPDATE people SET age = 31 WHERE name = 'Alice'",
        "SELECT name, age FROM people WHERE name = 'Alice'",
    ]),
    _f("f26", "delete", [
        "DELETE FROM people WHERE city = 'LA'",
        "SELECT COUNT(*) FROM people",
    ]),
    _f("f27", "is_null", [
        "SELECT name FROM nn WHERE phone IS NULL",
    ], setup=[
        "CREATE TABLE nn (name, phone)",
        "INSERT INTO nn VALUES ('Al', '555')",
        "INSERT INTO nn (name) VALUES ('Bo')",
    ]),
    _f("f28", "inner_join", [
        "SELECT people.name, orders.amount FROM people JOIN orders ON people.id = orders.pid",
    ], setup=_PEOPLE + [
        "CREATE TABLE orders (oid, pid, amount)",
        "INSERT INTO orders VALUES (1, 1, 100)",
        "INSERT INTO orders VALUES (2, 1, 50)",
        "INSERT INTO orders VALUES (3, 3, 75)",
    ]),
    _f("f29", "left_join", [
        "SELECT people.name, orders.amount FROM people LEFT JOIN orders ON people.id = orders.pid",
    ], setup=_PEOPLE + [
        "CREATE TABLE orders (oid, pid, amount)",
        "INSERT INTO orders VALUES (1, 1, 100)",
        "INSERT INTO orders VALUES (3, 3, 75)",
    ]),
    _f("f30", "drop_table", [
        "DROP TABLE people",
        "CREATE TABLE people (id, name)",
        "SELECT * FROM people",
    ]),
]


def _import_solution(workspace: Path):
    sol = Path(workspace) / "solution.py"
    if not sol.exists():
        return None
    mod_name = f"_dbsol_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(mod_name, sol)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _norm(rows, ordered):
    """Coerce a SELECT result to a comparable canonical form."""
    out = []
    for row in rows:
        cells = []
        for x in tuple(row):
            cells.append(round(x, 6) if isinstance(x, float) else x)
        out.append(tuple(cells))
    if not ordered:
        out = sorted(out, key=lambda t: repr(t))
    return out


def _run_battery(db, sqls, ordered):
    """Run a battery; return the normalized result of each SELECT (None if it raised)."""
    results = []
    for sql in sqls:
        try:
            r = db.execute(sql)
        except Exception:
            return None  # any error anywhere in the battery => not implemented correctly
        if sql.strip().lower().startswith("select"):
            try:
                results.append(_norm(r, ordered))
            except Exception:
                return None
    return results


def _check_one(make_db_agent, feature):
    ref_results = _run_battery(_db_reference.Database(), feature["sqls"], feature["ordered"])
    agent_db = make_db_agent()
    if agent_db is None:
        return False
    agent_results = _run_battery(agent_db, feature["sqls"], feature["ordered"])
    return agent_results is not None and agent_results == ref_results


def run_checks(workspace: Path, n_features: int) -> dict:
    module = None
    try:
        with _time_limit(5):
            module = _import_solution(workspace)
    except Exception:
        module = None

    def make_db_agent():
        if module is None or not hasattr(module, "Database"):
            return None
        try:
            return module.Database()
        except Exception:
            return None

    feats = FEATURES[:n_features]
    per_feature = []
    for feature in feats:
        try:
            with _time_limit(5):
                ok = _check_one(make_db_agent, feature)
        except Exception:
            ok = False
        per_feature.append({"id": feature["id"], "name": feature["name"], "passed": ok})

    return {
        "passed": sum(1 for f in per_feature if f["passed"]),
        "total": len(feats),
        "per_feature": per_feature,
    }


def summary_text(result: dict) -> str:
    lines = [f"{result['passed']}/{result['total']} features passing:"]
    for f in result["per_feature"]:
        lines.append(f"  [{'PASS' if f['passed'] else 'FAIL'}] {f['id']} {f['name']}")
    return "\n".join(lines)
