"""Grader for compositional/cb01_log_analytics.

Tests the public contract only (see TASK.md).
Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken reference uses mean latency instead of p95, so p95_latency values
differ from expected; slowest_endpoint and anomalies may also differ.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "compositional", "cb01_log_analytics"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Committed dataset and precomputed ground truth
TASK_DIR = Path(__file__).resolve().parents[1]
DATA_CSV = TASK_DIR / "data" / "access_log.csv"
EXPECTED_FILE = TASK_DIR / "expected" / "cb01.json"

with open(EXPECTED_FILE) as _f:
    EXPECTED = json.load(_f)

# Load analyze_logs callable and the dataset once
analyze_logs = gu.load_callable(SOL, "solution.py", "analyze_logs")
_df = pd.read_csv(DATA_CSV)
_result = analyze_logs(_df)


# ---------------------------------------------------------------------------
# Test 1: return type and required top-level keys
# ---------------------------------------------------------------------------
def test_return_type_and_keys():
    required = {"per_endpoint", "slowest_endpoint", "anomalies"}
    assert isinstance(_result, dict), "analyze_logs() must return a dict"
    missing = required - set(_result.keys())
    assert not missing, f"Missing top-level keys: {missing}"


# ---------------------------------------------------------------------------
# Test 2: per_endpoint sub-keys and types
# ---------------------------------------------------------------------------
def test_per_endpoint_structure():
    pe = _result["per_endpoint"]
    assert isinstance(pe, dict), "per_endpoint must be a dict"
    for ep, info in pe.items():
        assert isinstance(info, dict), f"per_endpoint[{ep!r}] must be a dict"
        sub_keys = {"count", "p95_latency", "error_rate"}
        missing = sub_keys - set(info.keys())
        assert not missing, f"per_endpoint[{ep!r}] missing keys: {missing}"
        assert isinstance(info["count"], int), f"count for {ep!r} must be int"
        assert isinstance(info["p95_latency"], float), f"p95_latency for {ep!r} must be float"
        assert isinstance(info["error_rate"], float), f"error_rate for {ep!r} must be float"


# ---------------------------------------------------------------------------
# Test 3: per_endpoint counts match expected exactly
# ---------------------------------------------------------------------------
def test_per_endpoint_counts():
    pe = _result["per_endpoint"]
    expected_pe = EXPECTED["per_endpoint"]
    assert set(pe.keys()) == set(expected_pe.keys()), (
        f"Endpoint set mismatch: got {set(pe.keys())}, expected {set(expected_pe.keys())}"
    )
    for ep in expected_pe:
        got = pe[ep]["count"]
        exp = expected_pe[ep]["count"]
        assert got == exp, f"count mismatch for {ep!r}: got {got}, expected {exp}"


# ---------------------------------------------------------------------------
# Test 4: per_endpoint p95_latency matches expected within rtol=1e-3
# ---------------------------------------------------------------------------
def test_per_endpoint_p95_latency():
    pe = _result["per_endpoint"]
    expected_pe = EXPECTED["per_endpoint"]
    for ep in expected_pe:
        got = pe[ep]["p95_latency"]
        exp = expected_pe[ep]["p95_latency"]
        assert gu.close(got, exp, rtol=1e-3), (
            f"p95_latency mismatch for {ep!r}: got {got:.4f}, expected {exp:.4f}"
        )


# ---------------------------------------------------------------------------
# Test 5: per_endpoint error_rate matches expected within rtol=1e-3
# ---------------------------------------------------------------------------
def test_per_endpoint_error_rate():
    pe = _result["per_endpoint"]
    expected_pe = EXPECTED["per_endpoint"]
    for ep in expected_pe:
        got = pe[ep]["error_rate"]
        exp = expected_pe[ep]["error_rate"]
        assert gu.close(got, exp, rtol=1e-3), (
            f"error_rate mismatch for {ep!r}: got {got:.6f}, expected {exp:.6f}"
        )


# ---------------------------------------------------------------------------
# Test 6: slowest_endpoint is the endpoint with maximum p95_latency
# ---------------------------------------------------------------------------
def test_slowest_endpoint():
    pe = _result["per_endpoint"]
    slowest = _result["slowest_endpoint"]
    assert isinstance(slowest, str), "slowest_endpoint must be a str"
    # Verify it actually has the max p95
    max_p95 = max(info["p95_latency"] for info in pe.values())
    assert gu.close(pe[slowest]["p95_latency"], max_p95, rtol=1e-6), (
        f"slowest_endpoint={slowest!r} does not have max p95 ({pe[slowest]['p95_latency']:.3f} vs {max_p95:.3f})"
    )
    assert slowest == EXPECTED["slowest_endpoint"], (
        f"slowest_endpoint: got {slowest!r}, expected {EXPECTED['slowest_endpoint']!r}"
    )


# ---------------------------------------------------------------------------
# Test 7: anomalies set matches expected exactly
# ---------------------------------------------------------------------------
def test_anomalies():
    anomalies = _result["anomalies"]
    assert isinstance(anomalies, list), "anomalies must be a list"
    got_set = set(anomalies)
    exp_set = set(EXPECTED["anomalies"])
    assert got_set == exp_set, (
        f"anomalies mismatch: got {sorted(got_set)}, expected {sorted(exp_set)}"
    )


# ---------------------------------------------------------------------------
# Test 8: empty DataFrame raises ValueError
# ---------------------------------------------------------------------------
def test_empty_dataframe_raises():
    import pandas as pd
    empty = pd.DataFrame(columns=["endpoint", "latency_ms", "status"])
    with pytest.raises(ValueError):
        analyze_logs(empty)


# ---------------------------------------------------------------------------
# Test 9: surface-form — must use groupby and numpy percentile/quantile
# ---------------------------------------------------------------------------
def test_source_uses_groupby_and_percentile():
    usage = gu.source_uses(SOL, ["groupby"])
    assert usage["groupby"], "solution.py must call .groupby() (surface-form constraint)"
    # Either numpy.percentile or pandas .quantile is acceptable
    pct_usage = gu.source_uses(SOL, ["percentile", "quantile"])
    assert pct_usage["percentile"] or pct_usage["quantile"], (
        "solution.py must use numpy.percentile or pandas .quantile for p95 computation"
    )


# ---------------------------------------------------------------------------
# Test 10: CLI writes results.json with correct keys and values
# ---------------------------------------------------------------------------
def test_cli_results_json(tmp_path):
    proc = gu.run_cli(
        SOL,
        ["--data", str(DATA_CSV), "--output-dir", str(tmp_path)],
        timeout=60,
    )
    assert proc.returncode == 0, f"CLI exited non-zero:\n{proc.stderr}"
    results_path = tmp_path / "results.json"
    assert results_path.exists(), "results.json was not written"
    data = json.loads(results_path.read_text())
    required_keys = {"per_endpoint", "slowest_endpoint", "anomalies"}
    missing = required_keys - set(data.keys())
    assert not missing, f"results.json missing keys: {missing}"
    # Spot-check p95 for one endpoint
    ep = EXPECTED["slowest_endpoint"]
    assert ep in data["per_endpoint"], f"results.json missing endpoint {ep!r}"
    assert gu.close(
        data["per_endpoint"][ep]["p95_latency"],
        EXPECTED["per_endpoint"][ep]["p95_latency"],
        rtol=1e-3,
    ), f"results.json p95_latency for {ep!r} is wrong"
    assert data["slowest_endpoint"] == EXPECTED["slowest_endpoint"], (
        f"results.json slowest_endpoint mismatch"
    )


# ---------------------------------------------------------------------------
# Test 11: CLI writes a valid latency.png
# ---------------------------------------------------------------------------
def test_cli_latency_png(tmp_path):
    proc = gu.run_cli(
        SOL,
        ["--data", str(DATA_CSV), "--output-dir", str(tmp_path)],
        timeout=60,
    )
    assert proc.returncode == 0, f"CLI exited non-zero:\n{proc.stderr}"
    png_path = tmp_path / "latency.png"
    assert png_path.exists(), "latency.png was not written"
    assert gu.png_is_valid(png_path), (
        f"latency.png is not a valid PNG or has no visual content"
    )


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail)
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
