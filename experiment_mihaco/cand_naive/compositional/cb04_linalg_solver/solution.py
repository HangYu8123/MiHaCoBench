import numpy as np
import pandas as pd


def analyze_system(df: pd.DataFrame) -> dict:
    """
    Analyze a square linear system encoded in a DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with columns x0, x1, ..., x{n-1}, b where the first n columns
        form matrix A and the last column is the RHS vector b.

    Returns
    -------
    dict with keys: solution, condition_number, eigenvalue_magnitudes,
                    determinant, well_conditioned
    """
    n_rows = len(df)
    n_cols = len(df.columns)

    # Validate square system: must have exactly n+1 columns for an n×n system
    if n_cols != n_rows + 1:
        raise ValueError(
            f"DataFrame does not encode a square system: "
            f"{n_rows} rows but {n_cols} columns (expected {n_rows + 1})."
        )

    # Extract A (all columns except 'b') and b vector
    A = df.iloc[:, :-1].to_numpy(dtype=float)
    b = df.iloc[:, -1].to_numpy(dtype=float)

    # Solve A x = b
    x = np.linalg.solve(A, b)

    # Condition number
    condition_number = float(np.linalg.cond(A))

    # Eigenvalues magnitudes sorted descending
    eigenvalues = np.linalg.eigvals(A)
    eigenvalue_magnitudes = sorted(np.abs(eigenvalues).tolist(), reverse=True)

    # Determinant
    determinant = float(np.linalg.det(A))

    # Well-conditioned check
    well_conditioned = bool(condition_number < 1e4)

    return {
        "solution": x.tolist(),
        "condition_number": condition_number,
        "eigenvalue_magnitudes": eigenvalue_magnitudes,
        "determinant": determinant,
        "well_conditioned": well_conditioned,
    }
