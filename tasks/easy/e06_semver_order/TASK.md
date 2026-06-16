# Easy 06 — `semver_order`: Semantic-version precedence (SemVer 2.0.0)

**Created:** 2026-06-16 · **Category:** easy · **Weight:** 1

Implement a small, single-file semantic-versioning tool. Write your solution as
`solution.py`. Use the **standard library only** (e.g. `argparse`, `sys`). Do not
read any file.

The rules below are the SemVer 2.0.0 precedence rules. They are dense; read them
carefully — the numeric-vs-alphanumeric pre-release distinction is the trap.

## Public contract (must match exactly)

### `parse(version: str) -> dict`

```python
def parse(version: str) -> dict:
    ...
```

Parse a version string of the form `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]` and
return a dict with exactly these keys:

| key | type | meaning |
|---|---|---|
| `major` | `int` | major version |
| `minor` | `int` | minor version |
| `patch` | `int` | patch version |
| `prerelease` | `list[str]` | the dot-separated pre-release identifiers (may be empty `[]`) |
| `build` | `list[str]` | the dot-separated build-metadata identifiers (may be empty `[]`) |

The pre-release section is introduced by the first `-` after the version core,
the build section by the first `+`. (Build may follow a pre-release, e.g.
`1.0.0-alpha+exp.1`.) Identifiers are split on `.`.

Raise `ValueError` on a **malformed** version, including (non-exhaustive):

* missing one of the three core parts (e.g. `1.0`, `1`),
* a non-numeric core part (e.g. `1.x.0`, `1.0.beta`),
* an **empty identifier** anywhere — an empty core part (`1..0`), an empty
  pre-release identifier (`1.0.0-` or `1.0.0-alpha..1`), or an empty build
  identifier (`1.0.0+` or `1.0.0+x..y`).

### `compare(a: str, b: str) -> int`

```python
def compare(a: str, b: str) -> int:
    ...
```

Return `-1`, `0`, or `1` according to SemVer 2.0.0 **precedence** (`-1` if `a`
sorts before `b`, `1` if after, `0` if equal precedence):

1. Compare `major`, then `minor`, then `patch`, **numerically**.
2. A version **with** a pre-release has **LOWER** precedence than the same
   version **without** one — e.g. `1.0.0-alpha < 1.0.0`.
3. When both have a pre-release, compare identifiers left to right:
   * identifiers consisting of **only digits** compare **NUMERICALLY**
     (so `alpha.9 < alpha.11`);
   * identifiers with letters compare **lexically in ASCII order**;
   * a purely **numeric** identifier always has **LOWER** precedence than an
     alphanumeric one (so `1.0.0-1 < 1.0.0-alpha`);
   * if all identifiers that exist in both are equal, the version with **MORE**
     identifiers has the **higher** precedence (e.g.
     `1.0.0-alpha < 1.0.0-alpha.1`).
4. **BUILD metadata is IGNORED** for precedence:
   `1.0.0+build1 == 1.0.0+build2 == 1.0.0`.

`compare` raises `ValueError` if either argument is malformed (same rule as
`parse`).

### `sort_versions(versions: list[str]) -> list[str]`

```python
def sort_versions(versions: list[str]) -> list[str]:
    ...
```

Return a new list of the **same strings** sorted **ascending by precedence**.
Build metadata is preserved verbatim in the returned strings but is irrelevant to
ordering. The sort is **stable**: versions of equal precedence keep their input
order.

## CLI contract

```
python solution.py compare A B
python solution.py sort V1 V2 ...
```

* `compare A B` — print `-1`, `0`, or `1` (the result of `compare(A, B)`) to
  **stdout** and exit `0`.
* `sort V1 V2 ...` — print the sorted versions, **one per line**, to stdout and
  exit `0`.
* On a malformed version, print an error to **stderr** and exit with a
  **non-zero** status.

## Notes

* Determinism: identical input ⇒ identical output.
* Numeric pre-release identifiers are compared as integers, not strings — so
  `alpha.9 < alpha.11` and `alpha.2 < alpha.10`.
