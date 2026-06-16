# Compositional 04 — `linalg_solver`: Linear System Analysis

**Created:** 2026-06-15 · **Category:** compositional · **Weight:** 4

Implement a function that loads a square linear system from a CSV file and
performs a full numerical analysis using **numpy** and **scipy** together with
**pandas** for data loading. Write your solution as `solution.py`.

## Input data

The file `data/system.csv` (provided) encodes an **n × n** matrix **A** plus a
right-hand-side vector **b**. The first `n` columns are the rows of **A** and
the last column (named `b`) contains the RHS.  The header row names the columns
`x0, x1, ..., x{n-1}, b`.

A non-square or otherwise malformed input (wrong column count) should raise
`ValueError`.

## Public contract

```python
def analyze_system(df: pandas.DataFrame) -> dict:
    ...
```

`df` is a `pandas.DataFrame` as returned by `pandas.read_csv`. The function
must:

1. Extract the square matrix **A** (all columns except `b`) and vector **b**
   from the dataframe using **pandas** / **numpy**.
2. Solve the system **A x = b** with `numpy.linalg.solve`.
3. Compute the condition number with `numpy.linalg.cond`.
4. Compute eigenvalues with `numpy.linalg.eigvals`, then return their
   **magnitudes** sorted in **descending order**.
5. Compute the determinant with `numpy.linalg.det`.

Return a `dict` with **exactly** these keys (no extras, no missing):

| Key | Type | Meaning |
|---|---|---|
| `solution` | `list[float]` | The solution vector **x** (length n) |
| `condition_number` | `float` | `numpy.linalg.cond(A)` |
| `eigenvalue_magnitudes` | `list[float]` | `abs(eigenvalues)` sorted **descending** |
| `determinant` | `float` | `numpy.linalg.det(A)` |
| `well_conditioned` | `bool` | `True` iff `condition_number < 1e4` |

If the dataframe does not encode a **square** system (number of columns ≠
n + 1 where n = number of rows), raise `ValueError`.

## Surface-form constraint

Your solution **must** use `numpy.linalg` directly (e.g., call
`numpy.linalg.solve`, `numpy.linalg.cond`, `numpy.linalg.eigvals`,
`numpy.linalg.det`). Do not use `scipy.linalg` as the primary solver.

## Notes

* Floats in the returned dict are compared by the grader with a tolerance —
  do not round.
* Eigenvalue magnitudes must be sorted **strictly descending by absolute
  value** (largest first).
* `well_conditioned` must be a Python `bool`, not a numpy boolean.
* The committed dataset `data/system.csv` is a 5 × 5 well-conditioned system
  with integer entries and a unique solution.
