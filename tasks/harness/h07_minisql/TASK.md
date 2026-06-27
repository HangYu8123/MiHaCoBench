# Harness 07 — `minisql`: In-Memory SQL Query Engine

**Created:** 2026-06-18 · **Category:** harness · **Weight:** 6

Build, from scratch, a small in-memory SQL database that parses and executes a
fixed subset of SQL. The work is broad rather than deep: dozens of small,
**independently graded** rules (literal parsing, type checking, three-valued
WHERE logic, GROUP BY, six aggregate behaviours, multi-key ORDER BY with a
precise NULL-ordering rule, DISTINCT, LIMIT/OFFSET, and a family of error
conditions). Each rule is checked on its own, so getting most of them right
still loses points for any single rule you drop.

You may (and should) split the implementation across **two or more modules**
(e.g. a tokenizer, a parser, an execution engine), but everything must be
reachable through a single file **`solution.py`** that defines the `Database`
class. The grader imports `solution.py` and uses only `Database`. Use only the
Python standard library (no third-party packages).

## Public contract

### class `Database`

A `Database()` instance holds tables in memory. It exposes one method:

```python
execute(self, sql: str) -> list[dict] | None
```

Run **one** SQL statement. A `SELECT` returns a `list[dict]` mapping each output
column name to its value, with one dict per result row **in result order**.
Every other statement (`CREATE TABLE`, `INSERT`) returns `None`.

* **Keywords are case-insensitive** (`select`, `SELECT`, `Select` are the same);
  **identifiers (table and column names) are case-sensitive**.
* **Values** are Python `int`, `str`, or `None` (SQL `NULL`). No other types.
* **Whitespace** between tokens is insignificant.

The engine supports **exactly** the statements and rules below. Anything outside
this grammar — including a syntactically malformed statement, or a reference to
an unknown table or unknown column **anywhere** in a statement — raises
`ValueError`.

---

### 1. `CREATE TABLE`

```
CREATE TABLE <table> (<col1> <TYPE>, <col2> <TYPE>, ...)
```

* Column types are exactly `INT` and `TEXT` (case-insensitive keywords).
* **All columns are nullable.**
* Re-creating a table that already exists raises `ValueError`.
* At least one column is required; a duplicate column name raises `ValueError`.

Returns `None`.

### 2. `INSERT`

```
INSERT INTO <table> (<c1>, <c2>, ...) VALUES (<v1>, <v2>, ...)   -- named columns
INSERT INTO <table> VALUES (<v1>, <v2>, ...)                     -- positional, ALL columns in declared order
```

**Literals** allowed as values:

* **integers**: `42`, `-7` (an optional leading `-` directly before digits);
* **strings**: single-quoted, e.g. `'hi'`. A doubled single quote `''` inside
  the quotes is an **escaped single quote** (`'it''s'` is the 4-character string
  `it's`);
* `NULL`.

**Type checking** (per target column):

* an `INT` column accepts an **integer literal** or `NULL`;
* a `TEXT` column accepts a **string literal** or `NULL`;
* any other combination raises `ValueError`.

For the positional form, the number of values must equal the number of columns.
For the named form, every named column must exist, names must be unique, and the
number of values must equal the number of named columns; columns not listed are
set to `NULL`. An unknown table, an unknown column, or a wrong number of values
raises `ValueError`.

Returns `None`.

### 3. `SELECT`

```
SELECT [DISTINCT] <select-list>
FROM <table>
[WHERE <condition>]
[GROUP BY <col> [, <col> ...]]
[ORDER BY <col> [ASC|DESC] [, <col> [ASC|DESC] ...]]
[LIMIT <n>] [OFFSET <m>]
```

Clauses, when present, appear in the order shown. `LIMIT` and `OFFSET` may appear
in either order relative to each other, each at most once.

#### 3a. select-list

Either `*`, or a comma-separated list whose entries are each one of:

* a **column name**, or
* an **aggregate call**: `COUNT(*)`, `COUNT(col)`, `SUM(col)`, `AVG(col)`,
  `MIN(col)`, `MAX(col)`.

Any entry may carry an alias: `<entry> AS <name>`.

**Result key for each entry**: the **alias** if one is given; otherwise the exact
source text of the entry — for a column that is the column name (e.g. `"score"`),
and for an aggregate the canonical spelling with no internal spaces (e.g.
`"COUNT(*)"`, `"SUM(score)"`). (`COUNT( * )` and `COUNT(*)` both produce the key
`"COUNT(*)"`.)

`SELECT *` returns every column of the table, in declared order, under its own
name. `*` may not be combined with `GROUP BY` or with aggregates (doing so raises
`ValueError`).

#### 3b. `WHERE <condition>` — three-valued (Kleene) logic

A condition is built from:

* **comparisons** between a **column** and a **literal**, in either order:
  `col = 5`, `5 = col`, `col <> 'x'`, `col < 10`, `col <= 10`, `col > 10`,
  `col >= 10`. The six operators are `=`, `<>`, `<`, `<=`, `>`, `>=`.
* `col IS NULL` and `col IS NOT NULL`.
* combinations with `AND`, `OR`, `NOT`, and parentheses. Precedence, loosest to
  tightest: `OR` < `AND` < `NOT` < (comparison / `IS [NOT] NULL`). `AND`/`OR`
  are left-associative.

**Truth values are TRUE, FALSE, or UNKNOWN.** A row is kept **iff** the WHERE
condition evaluates to **TRUE** (both FALSE and UNKNOWN drop the row).

* **Any comparison in which the column value is `NULL` (or the compared literal
  is `NULL`) yields UNKNOWN** — including `=` and `<>`. (So `x = 5` is UNKNOWN
  when `x` is NULL, and `x <> 5` is also UNKNOWN when `x` is NULL.)
* `IS NULL` / `IS NOT NULL` always yield TRUE or FALSE, **never** UNKNOWN.
* Kleene combinators:
  * `NOT TRUE = FALSE`, `NOT FALSE = TRUE`, `NOT UNKNOWN = UNKNOWN`.
  * `AND`: `TRUE AND x = x`; `FALSE AND x = FALSE`; `UNKNOWN AND TRUE = UNKNOWN`;
    `UNKNOWN AND FALSE = FALSE`; `UNKNOWN AND UNKNOWN = UNKNOWN`.
  * `OR`: `FALSE OR x = x`; `TRUE OR x = TRUE`; `UNKNOWN OR FALSE = UNKNOWN`;
    `UNKNOWN OR TRUE = TRUE`; `UNKNOWN OR UNKNOWN = UNKNOWN`.

**Type rule for comparisons**: comparing an `INT` column to a string literal, or
a `TEXT` column to an integer literal, raises `ValueError` (a `NULL` literal is
always type-compatible and yields UNKNOWN). Non-NULL comparisons: integers
compare by numeric value; strings compare **lexicographically by Unicode code
point**.

#### 3c. `GROUP BY`

* With `GROUP BY`, **every select-list entry that is not inside an aggregate**
  must name a column that appears in the `GROUP BY` list, otherwise `ValueError`.
* Rows are grouped by the **tuple of `GROUP BY` column values**. `NULL` forms its
  own group, and two `NULL`s in the same grouping column are the **same** group.
  Group output order follows first appearance of each group key in table
  (insertion) order; use `ORDER BY` if you need a specific order.
* **Without `GROUP BY` but with at least one aggregate** in the select-list, the
  whole (post-WHERE) table is a **single group**. If there are **zero** rows, the
  aggregates still produce **exactly one** result row.
* **Without `GROUP BY` and without aggregates**, the select is a plain row
  projection (one output row per input row).

#### 3d. aggregates

Computed over the rows of a group:

* `COUNT(*)` — number of rows in the group.
* `COUNT(col)` — number of rows where `col` **IS NOT NULL**.
* `SUM(col)` — sum of the non-NULL values; **`NULL`** if there are no non-NULL
  values. `SUM` over integers is an **`int`**.
* `AVG(col)` — mean of the non-NULL values using **real division** (always a
  **`float`**); **`NULL`** if there are no non-NULL values.
* `MIN(col)` / `MAX(col)` — min / max of the non-NULL values; **`NULL`** if there
  are no non-NULL values.

#### 3e. `ORDER BY`

* A comma-separated list of `col [ASC|DESC]` keys (default `ASC`), applied
  **left to right** (the leftmost key is most significant).
* Each `col` must be a column of the **source table**. (Ordering by an aggregate
  or by an output alias is **not** supported and raises `ValueError`.) An ORDER
  BY column need **not** appear in the select-list; for a `GROUP BY` query it
  must be one of the grouping columns.
* The sort is **stable**: rows that compare equal on all keys keep their prior
  (insertion / pre-sort) order.
* **NULL ordering** (this is the rule most implementations get wrong): under
  `ASC`, `NULL`s sort **before** all non-NULL values; under `DESC`, `NULL`s sort
  **after** all non-NULL values.

#### 3f. `LIMIT` / `OFFSET`

* Both take **non-negative integers**; a negative value raises `ValueError`.
* Applied **after** `ORDER BY`: `OFFSET m` skips the first `m` result rows, then
  `LIMIT n` caps the result to at most `n` rows. (If both are present, skip then
  cap.)

#### 3g. `DISTINCT`

* `SELECT DISTINCT ...` removes duplicate result rows. Two result rows are
  duplicates iff **every** selected value is equal, treating `NULL` as equal to
  `NULL` for this purpose.
* `DISTINCT` is applied **before** `ORDER BY` / `LIMIT` / `OFFSET`. The first
  occurrence of each distinct row is the one kept.

### 4. Errors

Any syntactically malformed statement, an unsupported statement, or a reference
to an unknown table or unknown column anywhere raises `ValueError`. (Negative
`LIMIT`/`OFFSET` and the type mismatches described above are also `ValueError`.)

---

## Worked examples

Assume:

```python
db = Database()
db.execute("CREATE TABLE t (id INT, name TEXT, score INT)")
db.execute("INSERT INTO t (id, name, score) VALUES (1, 'alice', 10)")
db.execute("INSERT INTO t VALUES (2, 'bob', NULL)")
db.execute("INSERT INTO t (id, name, score) VALUES (3, 'cara', 20)")
db.execute("INSERT INTO t (id, name) VALUES (4, 'dan')")   # score defaults to NULL
```

**Basic SELECT**

```python
db.execute("SELECT name, score FROM t")
# [{'name': 'alice', 'score': 10},
#  {'name': 'bob',   'score': None},
#  {'name': 'cara',  'score': 20},
#  {'name': 'dan',   'score': None}]
```

**WHERE with NULL (the NULL row is dropped — UNKNOWN is not TRUE)**

```python
db.execute("SELECT id FROM t WHERE score <> 10")
# [{'id': 3}]                 # id=2 and id=4 have NULL score -> UNKNOWN -> dropped
```

**IS NULL / IS NOT NULL**

```python
db.execute("SELECT id FROM t WHERE score IS NULL")       # [{'id': 2}, {'id': 4}]
db.execute("SELECT id FROM t WHERE score IS NOT NULL")   # [{'id': 1}, {'id': 3}]
```

**Three-valued combinators**

```python
db.execute("SELECT id FROM t WHERE NOT (score > 5)")          # []  (TRUE->NOT FALSE; NULL->NOT UNKNOWN)
db.execute("SELECT id FROM t WHERE score > 15 OR score IS NULL")
# [{'id': 2}, {'id': 3}, {'id': 4}]
```

**GROUP BY with COUNT / AVG, AVG ignoring NULL**

```python
db.execute("CREATE TABLE s (g TEXT, v INT)")
db.execute("INSERT INTO s VALUES ('a', 1)")
db.execute("INSERT INTO s VALUES ('a', 3)")
db.execute("INSERT INTO s VALUES ('a', NULL)")
db.execute("INSERT INTO s VALUES ('b', 5)")
db.execute("SELECT g, COUNT(*), COUNT(v), SUM(v), AVG(v) FROM s GROUP BY g ORDER BY g")
# [{'g': 'a', 'COUNT(*)': 3, 'COUNT(v)': 2, 'SUM(v)': 4, 'AVG(v)': 2.0},
#  {'g': 'b', 'COUNT(*)': 1, 'COUNT(v)': 1, 'SUM(v)': 5, 'AVG(v)': 5.0}]
```

**Aggregate over an empty table → one row, NULLs for SUM/AVG/MIN/MAX, 0 for COUNT**

```python
db.execute("CREATE TABLE e (v INT)")
db.execute("SELECT COUNT(*), SUM(v), AVG(v), MIN(v), MAX(v) FROM e")
# [{'COUNT(*)': 0, 'SUM(v)': None, 'AVG(v)': None, 'MIN(v)': None, 'MAX(v)': None}]
```

**ORDER BY with NULLs (ASC → NULLs first; DESC → NULLs last)**

```python
db.execute("SELECT id, score FROM t ORDER BY score ASC")
# [{'id': 2, 'score': None}, {'id': 4, 'score': None},
#  {'id': 1, 'score': 10},   {'id': 3, 'score': 20}]

db.execute("SELECT id, score FROM t ORDER BY score DESC")
# [{'id': 3, 'score': 20},   {'id': 1, 'score': 10},
#  {'id': 2, 'score': None}, {'id': 4, 'score': None}]
```

**Multi-key ORDER BY (column need not be selected); stable on ties**

```python
db.execute("CREATE TABLE m (a INT, b INT, id INT)")
db.execute("INSERT INTO m VALUES (1, 2, 10)")
db.execute("INSERT INTO m VALUES (1, 1, 11)")
db.execute("INSERT INTO m VALUES (2, 1, 12)")
db.execute("INSERT INTO m VALUES (1, 2, 13)")
db.execute("SELECT id FROM m ORDER BY a ASC, b DESC")
# [{'id': 10}, {'id': 13}, {'id': 11}, {'id': 12}]   # (1,2):10,13 stable, then (1,1):11, then (2,1):12
```

**DISTINCT with NULLs (NULL equals NULL for dedup), applied before ORDER BY**

```python
db.execute("CREATE TABLE d (a INT, b TEXT)")
db.execute("INSERT INTO d VALUES (1, 'x')")
db.execute("INSERT INTO d VALUES (1, 'x')")
db.execute("INSERT INTO d VALUES (NULL, 'y')")
db.execute("INSERT INTO d VALUES (NULL, 'y')")
db.execute("INSERT INTO d VALUES (2, NULL)")
db.execute("SELECT DISTINCT a, b FROM d ORDER BY a ASC")
# [{'a': None, 'b': 'y'}, {'a': 1, 'b': 'x'}, {'a': 2, 'b': None}]
```

**LIMIT / OFFSET (after ordering)**

```python
db.execute("SELECT id FROM t ORDER BY id LIMIT 2 OFFSET 1")   # [{'id': 2}, {'id': 3}]
```

## Notes

* `Database.execute` mutates the database only for `CREATE`/`INSERT`; `SELECT` is
  read-only.
* Determinism: results are fully determined by the data and the statement; no
  randomness or seeds are involved.
* Assert exception **types** (`ValueError`), never messages.
