import numpy as np
import pandas as pd


def analyze_system(df: pd.DataFrame) -> dict:
    """Analyze a square linear system encoded in a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns x0, x1, ..., x{n-1}, b representing
        the augmented matrix [A | b] of an n x n linear system.

    Returns
    -------
    dict with keys:
        solution              - list[float], solution vector x
        condition_number      - float, numpy.linalg.cond(A)
        eigenvalue_magnitudes - list[float], |eigenvalues| sorted descending
        determinant           - float, numpy.linalg.det(A)
        well_conditioned      - bool, True iff condition_number < 1e4

    Raises
    ------
    ValueError
        If the number of columns != n + 1 (non-square system) or if the
        'b' column is missing.
    """
    n = len(df)

    # Validate: must have exactly n+1 columns for a square system
    if len(df.columns) != n + 1:
        raise ValueError(
            f"Non-square system: expected {n + 1} columns for {n} rows, "
            f"got {len(df.columns)} columns."
        )

    # Validate: 'b' column must exist
    if 'b' not in df.columns:
        raise ValueError("DataFrame must have a column named 'b' for the RHS vector.")

    # Extract matrix A and vector b
    A = df.drop(columns=['b']).to_numpy(dtype=float)
    b = df['b'].to_numpy(dtype=float)

    # Solve Ax = b
    x = np.linalg.solve(A, b)

    # Condition number (2-norm, SVD-based)
    cond = np.linalg.cond(A)

    # Eigenvalues — may be complex for non-symmetric A; take magnitudes
    eigvals = np.linalg.eigvals(A)
    abs_eigvals = np.abs(eigvals)

    # Determinant
    det = np.linalg.det(A)

    return {
        "solution": x.tolist(),
        "condition_number": float(cond),
        "eigenvalue_magnitudes": sorted(abs_eigvals.tolist(), reverse=True),
        "determinant": float(det),
        "well_conditioned": bool(cond < 1e4),
    }
