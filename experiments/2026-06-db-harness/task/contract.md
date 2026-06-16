TASK: Implement a tiny in-memory SQL database engine in `solution.py`.

Expose a class `Database` with a single method `execute(sql: str)`. Statements that change
state (CREATE, DROP, INSERT, UPDATE, DELETE) return None. SELECT returns a list of tuples.

Support EXACTLY this dialect (keywords are case-insensitive; identifiers are case-sensitive):

CREATE TABLE t (c1, c2, ...)            -- columns are untyped, names only
DROP TABLE t
INSERT INTO t VALUES (v1, v2, ...)      -- values given in column order
INSERT INTO t (c1, c3) VALUES (v1, v3)  -- explicit columns; unlisted columns become NULL
UPDATE t SET c1 = v1 [, c2 = v2] [WHERE cond]
DELETE FROM t [WHERE cond]
SELECT [DISTINCT] <select_list> FROM t
    [ [INNER|LEFT] JOIN t2 ON t.cA = t2.cB ]
    [ WHERE cond ] [ GROUP BY col ] [ ORDER BY col [ASC|DESC] ] [ LIMIT n ] [ OFFSET n ]

VALUES / literals:
- integers: 30, -5
- strings: 'Alice'  (single-quoted; '' is an escaped quote)
- NULL  -> Python None

select_list is `*` or a comma list of items; an item is a column name, a table-qualified
name `t.col`, or an aggregate: COUNT(*), COUNT(col), SUM(col), AVG(col), MIN(col), MAX(col).

Rows:
- `SELECT *` returns columns in CREATE TABLE order. For a JOIN, the left table's columns come
  first, then the right table's.
- Each returned row is a tuple in select-list order. `SELECT name, age` -> (name, age).
- Without ORDER BY, return rows in insertion order. (The grader treats non-ORDER-BY results
  as unordered, so exact order only matters when ORDER BY is present.)

WHERE conditions:
- comparisons: col = v, col != v, col < v, col > v, col <= v, col >= v
- col IN (v1, v2, ...)
- col BETWEEN lo AND hi        (inclusive)
- col LIKE 'pat'               (% matches any run of chars, _ matches one char)
- col IS NULL / col IS NOT NULL
- combine predicates with AND / OR. AND binds tighter than OR. No parentheses.
- Any comparison with NULL on either side is false (NULL never matches =, <, >, etc.).

Aggregates:
- COUNT(*) counts rows; COUNT(col) counts non-NULL values.
- SUM/MIN/MAX/AVG ignore NULLs. AVG returns a float (e.g. 30.6). With no GROUP BY, an
  aggregate select returns a single row: `SELECT COUNT(*) FROM t` -> [(5,)].
- GROUP BY col: one output row per distinct value of col, in first-appearance order.
  `SELECT city, COUNT(*) FROM people GROUP BY city` -> [('NYC', 2), ('LA', 2), ...].

JOIN:
- `INNER JOIN ... ON a.x = b.y` keeps only matching pairs.
- `LEFT JOIN` keeps every left row; unmatched right columns are NULL.

Worked examples (people: id,name,age,city = (1,Alice,30,NYC)(2,Bob,25,LA)(3,Carol,35,NYC)):
- SELECT name FROM people WHERE city = 'NYC'      -> [('Alice',), ('Carol',)]
- SELECT name, age FROM people ORDER BY age DESC  -> [('Carol',35), ('Alice',30), ('Bob',25)]
- SELECT COUNT(*) FROM people                     -> [(3,)]
- SELECT city, COUNT(*) FROM people GROUP BY city -> [('NYC', 2), ('LA', 1)]
- SELECT name FROM people WHERE name LIKE 'A%'     -> [('Alice',)]

The features below are graded by running SQL batteries and comparing your engine's SELECT
results to a reference engine implementing exactly this contract.
