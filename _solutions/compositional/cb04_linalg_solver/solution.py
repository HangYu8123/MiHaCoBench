"""Gold reference for compositional/cb04_linalg_solver — Linear System Analysis.

Composes pandas (data loading), numpy.linalg (solve, cond, eigvals, det).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def analyze_system(df: pd.DataFrame) -> dict:
    """Analyze a square linear system encoded in a pandas DataFrame.

    The DataFrame has columns x0, x1, ..., x{n-1}, b where A is the n x n
    matrix formed by the first n columns and b is the RHS vector.

    Returns a dict with keys:
      solution             - list[float], solution vector x of Ax=b
      condition_number     - float, numpy.linalg.cond(A)
      eigenvalue_magnitudes- list[float], |eigenvalues| sorted descending
      determinant          - float, numpy.linalg.det(A)
      well_conditioned     - bool, True iff condition_number < 1e4

    Raises ValueError if the system is not square (n_cols != n_rows + 1).
    """
    n_rows = len(df)
    n_cols = len(df.columns)

    # Must have exactly n_rows+1 columns (n_rows for A, 1 for b)
    if n_cols != n_rows + 1:
        raise ValueError(
            f"Non-square system: expected {n_rows + 1} columns for a "
            f"{n_rows}x{n_rows} matrix plus RHS, got {n_cols} columns."
        )

    # Extract A and b via pandas/numpy
    b_col = df.columns[-1]
    a_cols = df.columns[:-1]
    A = df[a_cols].to_numpy(dtype=float)
    b = df[b_col].to_numpy(dtype=float)

    # 1. Solve A x = b
    x = numpy_linalg_solve(A, b)

    # 2. Condition number
    cond = float(np.linalg.cond(A))

    # 3. Eigenvalues — magnitudes sorted descending
    eigvals = np.linalg.eigvals(A)
    magnitudes = sorted(np.abs(eigvals).tolist(), reverse=True)

    # 4. Determinant
    det = float(np.linalg.det(A))

    # 5. Well-conditioned flag
    well_conditioned = bool(cond < 1e4)

    return {
        "solution": [float(v) for v in x],
        "condition_number": cond,
        "eigenvalue_magnitudes": magnitudes,
        "determinant": det,
        "well_conditioned": well_conditioned,
    }


def numpy_linalg_solve(A: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Wrapper that makes the surface-form check for numpy.linalg.solve explicit."""
    return np.linalg.solve(A, b)
