"""Grader for compositional/cb09_streaming_covariance. Public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The discriminator is ``test_numerical_stability_large_offset``: a 200k-point
stream with values around 1e9 and true variance ~100. The stable (Welford) gold
matches a trusted reference computed on the small-magnitude noise arrays; the
naive sum-of-squares (broken) cancels catastrophically and is hundreds off, so it
fails. All small-magnitude tests pass on both variants (they are contract checks,
not the discriminator).
"""
from __future__ import annotations

import numpy as np
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "compositional", "cb09_streaming_covariance"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
streaming_stats = gu.load_callable(SOL, "solution.py", "streaming_stats")


# ---------------------------------------------------------------------------
# 1. Small case vs numpy (population statistics).
# ---------------------------------------------------------------------------

def test_small_vs_numpy():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [2.0, 1.0, 4.0, 3.0, 7.0]
    res = streaming_stats(zip(xs, ys))
    assert res["n"] == 5
    assert gu.close(res["mean_x"], float(np.mean(xs)))
    assert gu.close(res["mean_y"], float(np.mean(ys)))
    assert gu.close(res["var_x"], float(np.var(xs)))       # ddof=0
    assert gu.close(res["var_y"], float(np.var(ys)))
    assert gu.close(res["cov"], float(np.cov(xs, ys, bias=True)[0, 1]))
    assert gu.close(res["corr"], float(np.corrcoef(xs, ys)[0, 1]))


# ---------------------------------------------------------------------------
# 2/3. Perfect positive / negative linear relationships.
# ---------------------------------------------------------------------------

def test_perfect_positive_correlation():
    xs = list(range(1, 21))
    ys = [2 * x + 1 for x in xs]
    res = streaming_stats(zip(xs, ys))
    assert gu.close(res["corr"], 1.0)


def test_perfect_negative_correlation():
    xs = list(range(1, 21))
    ys = [-3 * x + 5 for x in xs]
    res = streaming_stats(zip(xs, ys))
    assert gu.close(res["corr"], -1.0)


# ---------------------------------------------------------------------------
# 4. Empty input -> ValueError.
# ---------------------------------------------------------------------------

def test_empty_raises():
    with pytest.raises(ValueError):
        streaming_stats(iter([]))


# ---------------------------------------------------------------------------
# 5. Zero-variance x -> corr defined as 0.0 (no divide-by-zero).
# ---------------------------------------------------------------------------

def test_constant_x_corr_zero():
    xs = [4.0] * 10
    ys = [float(i) for i in range(10)]
    res = streaming_stats(zip(xs, ys))
    assert gu.close(res["var_x"], 0.0, atol=1e-9)
    assert res["corr"] == 0.0


# ---------------------------------------------------------------------------
# 6. Single pass: a generator that refuses to be iterated twice.
# ---------------------------------------------------------------------------

def test_single_pass_only():
    class OneShot:
        def __init__(self, data):
            self._data = data
            self._used = False

        def __iter__(self):
            if self._used:
                raise AssertionError("stream iterated more than once")
            self._used = True
            return iter(self._data)

    data = [(float(i), float(2 * i)) for i in range(50)]
    res = streaming_stats(OneShot(data))
    assert res["n"] == 50
    assert gu.close(res["corr"], 1.0)


# ---------------------------------------------------------------------------
# 7. Bounded memory: consuming a large generator must not scale with n.
# ---------------------------------------------------------------------------

def test_bounded_memory():
    def gen(n):
        for i in range(n):
            yield (float(i % 1000), float((i * 7) % 1000))

    peak = gu.measure_peak_memory(lambda: streaming_stats(gen(300_000)))
    # An O(1) accumulator stays in the kilobytes; materialising 300k pairs would
    # cost tens of MB. 5 MB cleanly separates the two.
    assert peak < 5_000_000, f"peak memory {peak} bytes suggests the stream was materialised"


# ---------------------------------------------------------------------------
# 8. THE DISCRIMINATOR — large constant offset, true variance ~100.
# ---------------------------------------------------------------------------

def test_numerical_stability_large_offset():
    rng = np.random.default_rng(2026)
    n = 200_000
    noise_x = 10.0 * rng.standard_normal(n)               # std 10 -> var ~100
    noise_y = 0.7 * noise_x + 5.0 * rng.standard_normal(n)
    offset_x = 1.0e9
    offset_y = -3.0e8

    # Trusted reference on the SMALL-magnitude noise (variance is shift-invariant).
    ref_var_x = float(np.var(noise_x))                    # ddof=0
    ref_var_y = float(np.var(noise_y))
    ref_cov = float(np.cov(noise_x, noise_y, bias=True)[0, 1])
    ref_mean_x = offset_x + float(np.mean(noise_x))
    ref_mean_y = offset_y + float(np.mean(noise_y))

    def stream():
        for i in range(n):
            yield (offset_x + float(noise_x[i]), offset_y + float(noise_y[i]))

    res = streaming_stats(stream())
    assert res["n"] == n
    # Means: trivially accurate either way.
    assert gu.close(res["mean_x"], ref_mean_x, rtol=1e-9)
    assert gu.close(res["mean_y"], ref_mean_y, rtol=1e-9)
    # Variances / covariance: only a numerically stable method survives the offset.
    assert gu.close(res["var_x"], ref_var_x, rtol=1e-6), f"var_x={res['var_x']} ref={ref_var_x}"
    assert gu.close(res["var_y"], ref_var_y, rtol=1e-6), f"var_y={res['var_y']} ref={ref_var_y}"
    assert gu.close(res["cov"], ref_cov, rtol=1e-6), f"cov={res['cov']} ref={ref_cov}"


# ---------------------------------------------------------------------------
# 9. Surface-form: numpy must be used.
# ---------------------------------------------------------------------------

def test_source_uses_numpy():
    assert gu.source_uses(SOL, ["numpy"])["numpy"], "solution must use numpy"


# ---------------------------------------------------------------------------
# 10. Advisory code-quality report (never asserted).
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never a gate
