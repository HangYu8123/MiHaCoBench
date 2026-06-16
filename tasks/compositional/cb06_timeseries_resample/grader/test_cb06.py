"""Grader for compositional/cb06_timeseries_resample.

Tests the public contract only (see TASK.md).
Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The dataset is a fixed, deterministic readings list built inline. Its FIRST grid
bucket is legitimately empty (a NaN-valued reading whose bucket mean is NaN), and
interior-only interpolation leaves that leading bucket NaN. It also contains one
clear spike and one interior gap that interpolation fills to the linear midpoint.

The broken reference computes z-scores with the default nan_policy="propagate"
and non-NaN-aware numpy.mean/std, so the single leading NaN poisons every
statistic: mean becomes NaN and the real spike is never flagged.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "compositional", "cb06_timeseries_resample"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

resample_clean = gu.load_callable(SOL, "solution.py", "resample_clean")

FREQ = "1min"

# Fixed deterministic readings. Grid is 1-minute buckets 00:00 .. 00:18.
#   * bucket 00:00 -> a single NaN-valued reading => leading empty bucket that
#     interior-only interpolation must NOT fill.
#   * bucket 00:04 -> no reading => interior gap, must interpolate to the linear
#     midpoint of bucket 00:03 (14.0) and bucket 00:05 (16.0) == 15.0.
#   * bucket 00:10 -> a clear spike of 100.0.
#   * bucket 00:14 -> a duplicate timestamp; LAST occurrence (11.0) is kept.
READINGS = [
    {"ts": "2026-01-01T00:00:30", "value": float("nan")},  # 00:00 leading NaN bucket
    {"ts": "2026-01-01T00:01:30", "value": 10.0},
    {"ts": "2026-01-01T00:02:15", "value": 12.0},
    {"ts": "2026-01-01T00:03:40", "value": 14.0},
    # 00:04 -> interior gap (interpolated to 15.0)
    {"ts": "2026-01-01T00:05:10", "value": 16.0},
    {"ts": "2026-01-01T00:06:20", "value": 11.0},
    {"ts": "2026-01-01T00:07:05", "value": 13.0},
    {"ts": "2026-01-01T00:08:50", "value": 9.0},
    {"ts": "2026-01-01T00:09:40", "value": 14.0},
    {"ts": "2026-01-01T00:10:20", "value": 100.0},  # SPIKE
    {"ts": "2026-01-01T00:11:00", "value": 12.0},
    {"ts": "2026-01-01T00:12:30", "value": 10.0},
    {"ts": "2026-01-01T00:13:15", "value": 15.0},
    {"ts": "2026-01-01T00:14:00", "value": 555.0},  # duplicate ts -> dropped
    {"ts": "2026-01-01T00:14:00", "value": 11.0},   # duplicate ts -> kept (last)
    {"ts": "2026-01-01T00:15:45", "value": 13.0},
    {"ts": "2026-01-01T00:16:10", "value": 12.0},
    {"ts": "2026-01-01T00:17:30", "value": 14.0},
    {"ts": "2026-01-01T00:18:50", "value": 10.0},
]

LEADING_BUCKET = "2026-01-01T00:00:00"
MIDGAP_BUCKET = "2026-01-01T00:04:00"
SPIKE_BUCKET = "2026-01-01T00:10:00"

_result = resample_clean(READINGS, FREQ)


# ---------------------------------------------------------------------------
# Test 1: return type and required keys, with consistent list lengths
# ---------------------------------------------------------------------------
def test_return_type_and_keys():
    required = {"index", "values", "outliers", "n_interpolated", "mean", "std"}
    assert isinstance(_result, dict), "resample_clean() must return a dict"
    missing = required - set(_result.keys())
    assert not missing, f"Missing top-level keys: {missing}"
    n = len(_result["index"])
    assert len(_result["values"]) == n, "values length must match index length"
    assert len(_result["outliers"]) == n, "outliers length must match index length"
    assert all(isinstance(b, bool) for b in _result["outliers"]), "outliers must be bools"
    assert isinstance(_result["n_interpolated"], int), "n_interpolated must be int"


# ---------------------------------------------------------------------------
# Test 2: leading empty bucket is present and stays None (not filled)
# ---------------------------------------------------------------------------
def test_leading_bucket_stays_none():
    idx = _result["index"]
    assert LEADING_BUCKET in idx, f"grid must include the leading bucket {LEADING_BUCKET}"
    pos = idx.index(LEADING_BUCKET)
    assert _result["values"][pos] is None, (
        "leading empty bucket must stay None (limit_area='inside' must not fill it)"
    )


# ---------------------------------------------------------------------------
# Test 3: interior gap interpolated to the linear midpoint
# ---------------------------------------------------------------------------
def test_interior_gap_interpolated():
    idx = _result["index"]
    assert MIDGAP_BUCKET in idx, f"grid must include the interior-gap bucket {MIDGAP_BUCKET}"
    pos = idx.index(MIDGAP_BUCKET)
    val = _result["values"][pos]
    assert val is not None, "interior gap must be interpolated, not left None"
    # midpoint of bucket 00:03 (14.0) and 00:05 (16.0)
    assert gu.close(val, 15.0, rtol=1e-6), f"interior gap should interpolate to 15.0, got {val}"


# ---------------------------------------------------------------------------
# Test 4: n_interpolated equals the known count (1)
# ---------------------------------------------------------------------------
def test_n_interpolated_count():
    assert _result["n_interpolated"] == 1, (
        f"exactly one interior bucket should be interpolated, got {_result['n_interpolated']}"
    )


# ---------------------------------------------------------------------------
# Test 5: mean and std are finite and match an independent computation
# ---------------------------------------------------------------------------
def test_mean_std_match_independent():
    present = [v for v in _result["values"] if v is not None]
    assert len(present) >= 2, "dataset should have multiple non-empty buckets"
    exp_mean = float(np.mean(present))
    exp_std = float(np.std(present, ddof=1))
    assert math.isfinite(_result["mean"]), "mean must be finite (NaN buckets must be ignored)"
    assert math.isfinite(_result["std"]), "std must be finite (NaN buckets must be ignored)"
    assert gu.close(_result["mean"], exp_mean, rtol=1e-6), (
        f"mean mismatch: got {_result['mean']}, expected {exp_mean}"
    )
    assert gu.close(_result["std"], exp_std, rtol=1e-6), (
        f"std mismatch: got {_result['std']}, expected {exp_std}"
    )


# ---------------------------------------------------------------------------
# Test 6: empty readings raises ValueError
# ---------------------------------------------------------------------------
def test_empty_readings_raises():
    with pytest.raises(ValueError):
        resample_clean([], FREQ)


# ---------------------------------------------------------------------------
# Test 7: an unparseable timestamp raises ValueError
# ---------------------------------------------------------------------------
def test_bad_timestamp_raises():
    bad = [
        {"ts": "2026-01-01T00:00:00", "value": 1.0},
        {"ts": "definitely-not-a-timestamp", "value": 2.0},
    ]
    with pytest.raises(ValueError):
        resample_clean(bad, FREQ)


# ---------------------------------------------------------------------------
# Test 8: an invalid frequency raises ValueError
# ---------------------------------------------------------------------------
def test_bad_freq_raises():
    good = [
        {"ts": "2026-01-01T00:00:00", "value": 1.0},
        {"ts": "2026-01-01T00:05:00", "value": 2.0},
    ]
    with pytest.raises(ValueError):
        resample_clean(good, "not-a-frequency")


# ---------------------------------------------------------------------------
# Test 9: constant-value input -> no outliers, finite mean, no crash
# ---------------------------------------------------------------------------
def test_constant_input_no_outliers():
    const = [
        {"ts": "2026-01-01T00:00:00", "value": 5.0},
        {"ts": "2026-01-01T00:01:00", "value": 5.0},
        {"ts": "2026-01-01T00:02:00", "value": 5.0},
    ]
    res = resample_clean(const, FREQ)
    assert not any(res["outliers"]), "a constant series must produce no outliers"
    assert math.isfinite(res["mean"]), "constant series must yield a finite mean"
    assert gu.close(res["mean"], 5.0, rtol=1e-6), "constant mean should equal the constant"


# ---------------------------------------------------------------------------
# Test 10: surface-form — must use scipy.stats.zscore
# ---------------------------------------------------------------------------
def test_source_uses_zscore():
    usage = gu.source_uses(SOL, ["scipy.stats.zscore", "zscore"])
    assert usage["scipy.stats.zscore"] or usage["zscore"], (
        "solution.py must use scipy.stats.zscore (surface-form constraint)"
    )


# ---------------------------------------------------------------------------
# Test 11: FAIL_TO_PASS discriminator — leading NaN must not poison results.
# Gold: mean is finite AND the spike bucket is flagged True.
# Broken (propagate + non-nan-aware mean): mean is NaN AND spike not flagged.
# ---------------------------------------------------------------------------
def test_leading_nan_does_not_poison_outliers_and_mean():
    idx = _result["index"]
    assert SPIKE_BUCKET in idx, f"grid must include the spike bucket {SPIKE_BUCKET}"
    spike_pos = idx.index(SPIKE_BUCKET)
    assert math.isfinite(_result["mean"]), (
        "mean must stay finite despite a leading empty bucket "
        "(use numpy.nanmean, not numpy.mean)"
    )
    assert _result["outliers"][spike_pos] is True, (
        "the spike bucket must be flagged as an outlier despite a leading empty "
        "bucket (use scipy.stats.zscore(nan_policy='omit'))"
    )
    # the spike should be the ONLY outlier on this dataset
    assert sum(_result["outliers"]) == 1, (
        f"exactly one outlier expected (the spike), got {sum(_result['outliers'])}"
    )


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail)
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
