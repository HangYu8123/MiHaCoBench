import numpy
import pandas


def analyze_system(df: pandas.DataFrame) -> dict:
    """
    Analyze a square linear system encoded in a DataFrame.

    The DataFrame has n rows and n+1 columns: the first n columns are the
    rows of matrix A, and the last column (named 'b') is the RHS vector.

    Parameters
    ----------
    df : pandas.DataFrame
        Input data with columns x0, x1, ..., x{n-1}, b.

    Returns
    -------
    dict with keys:
        solution              : list[float]  - solution vector x
        condition_number      : float        - numpy.linalg.cond(A)
        eigenvalue_magnitudes : list[float]  - |eigenvalues| sorted descending
        determinant           : float        - numpy.linalg.det(A)
        well_conditioned      : bool         - True iff condition_number < 1e4
    """
    n_rows = len(df)
    n_cols = len(df.columns)

    if n_cols != n_rows + 1:
        raise ValueError(
            f"Expected {n_rows + 1} columns (n={n_rows} for A plus 1 for b), "
            f"got {n_cols}."
        )

    # Extract A (all columns except the last) and b (last column named 'b')
    A = df.iloc[:, :-1].to_numpy(dtype=float)
    b = df['b'].to_numpy(dtype=float)

    # Solve A x = b
    x = numpy.linalg.solve(A, b)

    # Condition number
    cond = float(numpy.linalg.cond(A))

    # Eigenvalue magnitudes sorted descending
    eigs = numpy.linalg.eigvals(A)
    mags_sorted = sorted(numpy.abs(eigs).tolist(), reverse=True)

    # Determinant
    det = float(numpy.linalg.det(A))

    # Well-conditioned flag (explicit Python bool)
    well = bool(cond < 1e4)

    return {
        "solution": x.tolist(),
        "condition_number": cond,
        "eigenvalue_magnitudes": mags_sorted,
        "determinant": det,
        "well_conditioned": well,
    }
