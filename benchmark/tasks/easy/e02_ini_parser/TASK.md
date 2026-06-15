# Easy 02 — `ini_parser`: INI-file parser with coercion and interpolation

**Created:** 2026-06-15 · **Category:** easy · **Weight:** 1

Implement a small, single-file INI-file parser. Write your solution as
`solution.py`. Use the **standard library only**. Do not use `configparser`.

## Public contract (must match exactly)

```python
def parse_ini(text: str) -> dict[str, dict[str, object]]:
    ...
```

`text` is the raw INI file content as a string.

### Structural rules

* **Sections** are introduced by a line of the form `[name]` (strip surrounding
  whitespace from the line before checking; the section name is the text between
  the brackets, stripped of leading/trailing whitespace).
* **Key/value pairs** are lines containing `=` or `:` as the separator
  (whichever appears first). Both the key and the value are stripped of leading
  and trailing whitespace.
* **Comments** are lines whose first non-whitespace character is `#` or `;`.
  They are ignored entirely.
* **Blank lines** (after stripping) are ignored.
* Keys that appear **before any section header** are placed in a section called
  `"default"`.
* If the same key appears more than once in a section, the **last** value wins.

### Value coercion (applied in this order)

1. If the value (after stripping) looks like an integer (`int(value)` succeeds
   and `str(int(value)) == value.strip()`), coerce to `int`.
2. Else if it looks like a float (`float(value)` succeeds), coerce to `float`.
3. Else if the value is `"true"`, `"yes"` (case-insensitive) → `True` (`bool`).
4. Else if the value is `"false"`, `"no"` (case-insensitive) → `False` (`bool`).
5. Otherwise keep as `str`.

### Interpolation

A string value (after the coercion step above yields a `str`) may contain
references of the form `${section.key}`. Each such reference must be replaced
by the **string representation** of the resolved value from `section` → `key`
in the same parsed result.

* Resolve iteratively until the value is stable (no remaining `${...}` tokens).
* If a reference points to a non-existent section or key, raise `ValueError`.
* If resolution does not terminate (cycle detected), raise `ValueError`.

The returned dict maps section names to dicts of `{key: coerced_value}`.

### Example

```ini
; global defaults
[server]
host = localhost
port = 8080
enabled = yes

[database]
host = ${server.host}
port = 5432
name = mydb

[paths]
base = /var
data = ${paths.base}/data
```

`parse_ini(text)` should return (approximately):

```python
{
    "server": {"host": "localhost", "port": 8080, "enabled": True},
    "database": {"host": "localhost", "port": 5432, "name": "mydb"},
    "paths": {"base": "/var", "data": "/var/data"},
}
```

## Notes

* Determinism: identical input ⇒ identical output.
* The grader imports `parse_ini` by file path; keep all logic in `solution.py`.
* No CLI is required for this task.
