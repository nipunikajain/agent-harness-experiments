"""Reference implementation of the mini-SQL engine used to grade the DB-harness experiment.

This is the *source of truth*: the grader runs each test query against both the agent's
solution and this reference, and a feature passes iff they agree. The agent NEVER sees this
file — it only gets the prose contract in task/contract.md, which describes exactly this
dialect.

Dialect (intentionally small and regular so it is unambiguous):
  CREATE TABLE t (c1, c2, ...)
  DROP TABLE t
  INSERT INTO t VALUES (v, ...)         -- values in column order
  INSERT INTO t (c1, c2) VALUES (v, v)  -- explicit columns; unset columns become NULL
  UPDATE t SET c = v [, c2 = v2] [WHERE cond]
  DELETE FROM t [WHERE cond]
  SELECT [DISTINCT] select_list FROM t [[INNER|LEFT] JOIN t2 ON a.c = b.c]
         [WHERE cond] [GROUP BY col] [HAVING cond]
         [ORDER BY col [ASC|DESC]] [LIMIT n] [OFFSET n]

Values: integer literals (optionally negative), 'single-quoted strings', or NULL.
Predicates: col {= != < > <= >=} val | col IN (v, ...) | col BETWEEN v AND v |
            col LIKE 'pat' (% = any run, _ = one char) | col IS [NOT] NULL
Conditions combine with AND / OR (AND binds tighter than OR; no parentheses).
SELECT returns a list of tuples. `SELECT *` yields columns in CREATE-TABLE order (for joins,
left table's columns then right table's). Aggregates: COUNT(*), COUNT(col), SUM, AVG, MIN, MAX
(AVG returns a float; SUM/MIN/MAX/COUNT(col) ignore NULLs). Rows are in insertion order unless
ORDER BY is given.
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(
    r"""\s*(?:
        (?P<str>'(?:[^']|'')*')        |
        (?P<num>-?\d+)                 |
        (?P<op><=|>=|!=|=|<|>)         |
        (?P<punc>[(),.*])             |
        (?P<word>[A-Za-z_][A-Za-z0-9_]*)
    )""",
    re.VERBOSE,
)

_KEYWORDS = {
    "create", "table", "drop", "insert", "into", "values", "update", "set", "delete",
    "select", "distinct", "from", "inner", "left", "join", "on", "where", "group", "by",
    "having", "order", "asc", "desc", "limit", "offset", "and", "or", "in", "between",
    "like", "is", "not", "null", "count", "sum", "avg", "min", "max",
}


def _tokenize(sql: str):
    toks = []
    i = 0
    while i < len(sql):
        m = _TOKEN_RE.match(sql, i)
        if not m or m.end() == i:
            if sql[i:].strip() == "":
                break
            raise ValueError(f"cannot tokenize near: {sql[i:i+20]!r}")
        i = m.end()
        if m.group("str") is not None:
            toks.append(("val", m.group("str")[1:-1].replace("''", "'")))
        elif m.group("num") is not None:
            toks.append(("val", int(m.group("num"))))
        elif m.group("op") is not None:
            toks.append(("op", m.group("op")))
        elif m.group("punc") is not None:
            toks.append(("punc", m.group("punc")))
        else:
            w = m.group("word")
            lw = w.lower()
            toks.append(("kw", lw) if lw in _KEYWORDS else ("id", w))
    return toks


class _Cursor:
    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def next(self):
        t = self.peek()
        self.i += 1
        return t

    def eat_kw(self, kw):
        t, v = self.peek()
        if t == "kw" and v == kw:
            self.i += 1
            return True
        return False

    def expect_kw(self, kw):
        if not self.eat_kw(kw):
            raise ValueError(f"expected keyword {kw!r}, got {self.peek()}")

    def expect_punc(self, p):
        t, v = self.next()
        if t != "punc" or v != p:
            raise ValueError(f"expected {p!r}, got {(t, v)}")

    def at_punc(self, p):
        t, v = self.peek()
        return t == "punc" and v == p


_NULL = object()  # sentinel produced by the NULL keyword during parsing


class Database:
    def __init__(self):
        self.tables: dict[str, dict] = {}

    # ---- public API ----
    def execute(self, sql: str):
        cur = _Cursor(_tokenize(sql))
        t, v = cur.peek()
        if t != "kw":
            raise ValueError(f"unexpected start: {(t, v)}")
        handler = {
            "create": self._create, "drop": self._drop, "insert": self._insert,
            "update": self._update, "delete": self._delete, "select": self._select,
        }.get(v)
        if handler is None:
            raise ValueError(f"unsupported statement: {v}")
        return handler(cur)

    # ---- statements ----
    def _create(self, cur):
        cur.expect_kw("create")
        cur.expect_kw("table")
        name = self._ident(cur)
        cur.expect_punc("(")
        cols = [self._ident(cur)]
        while cur.at_punc(","):
            cur.next()
            cols.append(self._ident(cur))
        cur.expect_punc(")")
        self.tables[name] = {"columns": cols, "rows": []}

    def _drop(self, cur):
        cur.expect_kw("drop")
        cur.expect_kw("table")
        name = self._ident(cur)
        self.tables.pop(name, None)

    def _insert(self, cur):
        cur.expect_kw("insert")
        cur.expect_kw("into")
        name = self._ident(cur)
        table = self.tables[name]
        cols = table["columns"]
        target_cols = cols
        if cur.at_punc("("):
            cur.next()
            target_cols = [self._ident(cur)]
            while cur.at_punc(","):
                cur.next()
                target_cols.append(self._ident(cur))
            cur.expect_punc(")")
        cur.expect_kw("values")
        cur.expect_punc("(")
        vals = [self._value(cur)]
        while cur.at_punc(","):
            cur.next()
            vals.append(self._value(cur))
        cur.expect_punc(")")
        row = {c: None for c in cols}
        for c, val in zip(target_cols, vals):
            row[c] = None if val is _NULL else val
        table["rows"].append(row)

    def _update(self, cur):
        cur.expect_kw("update")
        name = self._ident(cur)
        table = self.tables[name]
        cur.expect_kw("set")
        assigns = []
        while True:
            col = self._ident(cur)
            t, v = cur.next()
            if not (t == "op" and v == "="):
                raise ValueError("expected = in SET")
            assigns.append((col, self._value(cur)))
            if cur.at_punc(","):
                cur.next()
                continue
            break
        cond = self._where(cur)
        for row in table["rows"]:
            if cond is None or cond(self._scope(name, row)):
                for col, val in assigns:
                    row[col] = None if val is _NULL else val

    def _delete(self, cur):
        cur.expect_kw("delete")
        cur.expect_kw("from")
        name = self._ident(cur)
        table = self.tables[name]
        cond = self._where(cur)
        table["rows"] = [
            r for r in table["rows"] if not (cond is None or cond(self._scope(name, r)))
        ]

    def _select(self, cur):
        cur.expect_kw("select")
        distinct = cur.eat_kw("distinct")
        items = self._select_list(cur)
        cur.expect_kw("from")
        base = self._ident(cur)
        working = [self._scope(base, r) for r in self.tables[base]["rows"]]
        select_cols = self.tables[base]["columns"]

        join = None
        if (cur.peek()[1] in ("inner", "left")) or cur.peek()[1] == "join":
            kind = "inner"
            if cur.eat_kw("inner"):
                pass
            elif cur.eat_kw("left"):
                kind = "left"
            cur.expect_kw("join")
            jt = self._ident(cur)
            cur.expect_kw("on")
            lcol = self._qualcol(cur)
            t, v = cur.next()
            if not (t == "op" and v == "="):
                raise ValueError("JOIN ON supports = only")
            rcol = self._qualcol(cur)
            join = (kind, base, jt, lcol, rcol)
            working = self._do_join(base, jt, kind, lcol, rcol)
            select_cols = self.tables[base]["columns"] + self.tables[jt]["columns"]

        cond = self._where(cur)
        if cond is not None:
            working = [r for r in working if cond(r)]

        group_col = None
        if cur.eat_kw("group"):
            cur.expect_kw("by")
            group_col = self._qualcol(cur)

        order_col, order_desc = None, False
        if cur.eat_kw("order"):
            cur.expect_kw("by")
            order_col = self._qualcol(cur)
            if cur.eat_kw("desc"):
                order_desc = True
            else:
                cur.eat_kw("asc")

        limit = offset = None
        if cur.eat_kw("limit"):
            limit = self._value(cur)
        if cur.eat_kw("offset"):
            offset = self._value(cur)

        has_agg = any(it[0] == "agg" for it in items)
        if group_col is not None or has_agg:
            rows = self._aggregate(items, working, group_col, select_cols)
        else:
            if order_col is not None:
                working = self._order(working, order_col, order_desc)
            rows = [self._project(items, r, select_cols) for r in working]

        if (group_col is not None or has_agg) and order_col is not None:
            # ordering after aggregation: order by a selected output column name
            rows = self._order_tuples(rows, items, order_col, order_desc, select_cols)

        if distinct:
            seen = set()
            deduped = []
            for r in rows:
                if r not in seen:
                    seen.add(r)
                    deduped.append(r)
            rows = deduped

        if offset:
            rows = rows[offset:]
        if limit is not None:
            rows = rows[:limit]
        return rows

    # ---- helpers ----
    def _ident(self, cur):
        t, v = cur.next()
        if t != "id":
            raise ValueError(f"expected identifier, got {(t, v)}")
        return v

    def _qualcol(self, cur):
        t, v = cur.next()
        if t != "id":
            raise ValueError(f"expected column, got {(t, v)}")
        if cur.at_punc("."):
            cur.next()
            t2, v2 = cur.next()
            return f"{v}.{v2}"
        return v

    def _value(self, cur):
        t, v = cur.peek()
        if t == "kw" and v == "null":
            cur.next()
            return _NULL
        if t == "val":
            cur.next()
            return v
        raise ValueError(f"expected value, got {(t, v)}")

    def _scope(self, table, row):
        """A working row carries both bare and table-qualified column keys."""
        scoped = dict(row)
        for k, val in row.items():
            scoped[f"{table}.{k}"] = val
        return scoped

    def _do_join(self, lt, rt, kind, lcol, rcol):
        out = []
        lrows = self.tables[lt]["rows"]
        rrows = self.tables[rt]["rows"]
        for lr in lrows:
            ls = self._scope(lt, lr)
            matched = False
            for rr in rrows:
                rs = self._scope(rt, rr)
                if ls.get(lcol) == rs.get(rcol) and ls.get(lcol) is not None:
                    merged = dict(ls)
                    merged.update(rs)
                    out.append(merged)
                    matched = True
            if not matched and kind == "left":
                merged = dict(ls)
                for c in self.tables[rt]["columns"]:
                    merged.setdefault(c, None)
                    merged[f"{rt}.{c}"] = None
                out.append(merged)
        return out

    def _select_list(self, cur):
        if cur.at_punc("*"):
            cur.next()
            return [("star",)]
        items = [self._select_item(cur)]
        while cur.at_punc(","):
            cur.next()
            items.append(self._select_item(cur))
        return items

    def _select_item(self, cur):
        t, v = cur.peek()
        if t == "kw" and v in ("count", "sum", "avg", "min", "max"):
            cur.next()
            cur.expect_punc("(")
            if cur.at_punc("*"):
                cur.next()
                arg = "*"
            else:
                arg = self._qualcol(cur)
            cur.expect_punc(")")
            return ("agg", v, arg)
        return ("col", self._qualcol(cur))

    def _where(self, cur):
        if cur.eat_kw("where"):
            return self._condition(cur)
        return None

    def _condition(self, cur):
        # OR of AND-groups (AND binds tighter)
        ors = [self._and_group(cur)]
        while cur.eat_kw("or"):
            ors.append(self._and_group(cur))
        return lambda row: any(g(row) for g in ors)

    def _and_group(self, cur):
        ands = [self._predicate(cur)]
        while cur.eat_kw("and"):
            ands.append(self._predicate(cur))
        return lambda row: all(p(row) for p in ands)

    def _predicate(self, cur):
        col = self._qualcol(cur)
        t, v = cur.peek()
        if t == "op":
            cur.next()
            val = self._value(cur)
            rv = None if val is _NULL else val
            return self._cmp(col, v, rv)
        if t == "kw" and v == "is":
            cur.next()
            neg = cur.eat_kw("not")
            cur.expect_kw("null")
            return (lambda row: row.get(col) is not None) if neg else (lambda row: row.get(col) is None)
        if t == "kw" and v == "in":
            cur.next()
            cur.expect_punc("(")
            vals = [self._value(cur)]
            while cur.at_punc(","):
                cur.next()
                vals.append(self._value(cur))
            cur.expect_punc(")")
            vals = [None if x is _NULL else x for x in vals]
            return lambda row: row.get(col) in vals
        if t == "kw" and v == "between":
            cur.next()
            lo = self._value(cur)
            cur.expect_kw("and")
            hi = self._value(cur)
            return lambda row: row.get(col) is not None and lo <= row.get(col) <= hi
        if t == "kw" and v == "like":
            cur.next()
            pat = self._value(cur)
            rx = re.compile("^" + re.escape(pat).replace("%", ".*").replace("_", ".") + "$", re.S)
            return lambda row: row.get(col) is not None and bool(rx.match(str(row.get(col))))
        raise ValueError(f"bad predicate near {(t, v)}")

    def _cmp(self, col, op, rv):
        def f(row):
            lv = row.get(col)
            if lv is None or rv is None:
                return False
            try:
                if op == "=":
                    return lv == rv
                if op == "!=":
                    return lv != rv
                if op == "<":
                    return lv < rv
                if op == ">":
                    return lv > rv
                if op == "<=":
                    return lv <= rv
                if op == ">=":
                    return lv >= rv
            except TypeError:
                return False
        return f

    def _order(self, rows, col, desc):
        return sorted(rows, key=lambda r: (r.get(col) is None, r.get(col)), reverse=desc)

    def _agg_value(self, fn, arg, group):
        if fn == "count":
            if arg == "*":
                return len(group)
            return sum(1 for r in group if r.get(arg) is not None)
        vals = [r.get(arg) for r in group if r.get(arg) is not None]
        if fn == "sum":
            return sum(vals)
        if fn == "min":
            return min(vals) if vals else None
        if fn == "max":
            return max(vals) if vals else None
        if fn == "avg":
            return (sum(vals) / len(vals)) if vals else None

    def _aggregate(self, items, working, group_col, select_cols):
        if group_col is None:
            groups = [(None, working)] if working else [(None, [])]
        else:
            order = []
            buckets = {}
            for r in working:
                k = r.get(group_col)
                if k not in buckets:
                    buckets[k] = []
                    order.append(k)
                buckets[k].append(r)
            groups = [(k, buckets[k]) for k in order]

        out = []
        for key, grp in groups:
            tup = []
            for it in items:
                if it[0] == "agg":
                    tup.append(self._agg_value(it[1], it[2], grp))
                elif it[0] == "col":
                    tup.append(key if it[1] == group_col else (grp[0].get(it[1]) if grp else None))
                elif it[0] == "star":
                    raise ValueError("SELECT * with aggregation is unsupported")
            out.append(tuple(tup))
        return out

    def _project(self, items, row, select_cols):
        if items and items[0][0] == "star":
            return tuple(row.get(c) for c in select_cols)
        tup = []
        for it in items:
            if it[0] == "col":
                tup.append(row.get(it[1]))
            else:
                raise ValueError("aggregate in non-aggregate projection")
        return tuple(tup)

    def _order_tuples(self, rows, items, order_col, desc, select_cols):
        # locate the output column index matching order_col (by col name or agg arg)
        idx = None
        for j, it in enumerate(items):
            if it[0] == "col" and (it[1] == order_col or it[1].split(".")[-1] == order_col):
                idx = j
                break
        if idx is None:
            return rows
        return sorted(rows, key=lambda t: (t[idx] is None, t[idx]), reverse=desc)
