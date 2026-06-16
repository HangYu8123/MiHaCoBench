"""Grader for data_analysis/d08_multiple_comparisons.

Tests the public contract only (see TASK.md). References are computed INLINE
with scipy plus a hand-written Holm-Bonferroni step — no expected/ fixtures.

Validity invariant: PASSES on the gold reference (Holm correction applied),
FAILS on the broken reference (correction skipped, so the discriminator pair is
wrongly marked significant and n_significant_pairs is too high).

Discriminator on the committed dataset: A_vs_B has raw_p ~ 0.0356 (significant
under raw pairwise t-tests) but Holm-adjusted p ~ 0.0711 (NOT significant). So
the corrected count of significant pairs is 4, while the naive count is 5.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import scipy.stats

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "data_analysis", "d08_multiple_comparisons"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

TASK_DIR = Path(__file__).resolve().parents[1]
DATA_CSV = TASK_DIR / "data" / "groups.csv"

ALPHA = 0.05

# Load the analyze callable and the committed dataset.
analyze = gu.load_callable(SOL, "solution.py", "analyze")
_df = pd.read_csv(DATA_CSV)
_result = analyze(_df)


# --------------------------------------------------------------------------- #
# Inline reference computation (scipy + hand-written Holm step-down)
# --------------------------------------------------------------------------- #
def _holm(named_pvals):
    """Holm-Bonferroni step-down adjustment: list of (name, raw_p) -> {name: adj_p}."""
    m = len(named_pvals)
    order = sorted(range(m), key=lambda i: named_pvals[i][1])
    adj = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * named_pvals[idx][1])
        adj[idx] = min(running, 1.0)
    return {named_pvals[i][0]: adj[i] for i in range(m)}


def _reference(df):
    labels = sorted(df["group"].unique())
    groups = {lab: df.loc[df["group"] == lab, "value"].to_numpy(dtype=float)
              for lab in labels}
    means = {lab: float(np.mean(groups[lab])) for lab in labels}
    n = {lab: int(len(groups[lab])) for lab in labels}
    f, p = scipy.stats.f_oneway(*[groups[lab] for lab in labels])
    named = []
    raw_lookup = {}
    for x, y in combinations(labels, 2):
        key = f"{x}_vs_{y}"
        _, rp = scipy.stats.ttest_ind(groups[x], groups[y], equal_var=True)
        named.append((key, float(rp)))
        raw_lookup[key] = float(rp)
    adj_lookup = _holm(named)
    sig = {k: (adj_lookup[k] < ALPHA) for k in raw_lookup}
    n_sig = sum(1 for k in sig if sig[k])
    return {
        "labels": labels,
        "group_means": means,
        "n_per_group": n,
        "anova_f": float(f),
        "anova_p": float(p),
        "raw_p": raw_lookup,
        "adj_p": adj_lookup,
        "significant": sig,
        "n_significant_pairs": int(n_sig),
    }


REF = _reference(_df)

# Sanity-check that the committed dataset really embodies the intended twist:
# the omnibus is significant, and exactly one pair flips from raw-significant to
# Holm-non-significant. This protects the grader from a silently-changed dataset.
assert REF["anova_p"] < ALPHA, "dataset omnibus must be significant"
_RAW_SIG = {k for k, v in REF["raw_p"].items() if v < ALPHA}
_ADJ_SIG = {k for k, v in REF["adj_p"].items() if v < ALPHA}
_DISC = _RAW_SIG - _ADJ_SIG
assert len(_DISC) == 1, f"expected exactly one discriminator pair, got {_DISC}"
DISCRIMINATOR = next(iter(_DISC))
assert REF["n_significant_pairs"] < len(_RAW_SIG), (
    "corrected count must be lower than the naive raw count"
)


# --------------------------------------------------------------------------- #
# Test 1: return type and required top-level keys
# --------------------------------------------------------------------------- #
def test_return_type_and_keys():
    required = {
        "group_means", "n_per_group", "anova_f", "anova_p",
        "omnibus_significant", "pairs", "n_significant_pairs",
    }
    assert isinstance(_result, dict), "analyze() must return a dict"
    missing = required - set(_result.keys())
    assert not missing, f"Missing top-level keys: {missing}"


# --------------------------------------------------------------------------- #
# Test 2: pairs structure — all C(K,2) keys present, each with the right schema
# --------------------------------------------------------------------------- #
def test_pairs_structure():
    pairs = _result["pairs"]
    assert isinstance(pairs, dict), "pairs must be a dict"
    expected_keys = set(REF["raw_p"].keys())
    assert set(pairs.keys()) == expected_keys, (
        f"pairs keys mismatch: got {set(pairs.keys())}, expected {expected_keys}"
    )
    for key, info in pairs.items():
        assert set(info.keys()) == {"raw_p", "adj_p", "significant"}, (
            f"pair {key} has wrong sub-keys: {set(info.keys())}"
        )
        assert isinstance(info["significant"], bool), (
            f"pair {key} 'significant' must be a bool"
        )


# --------------------------------------------------------------------------- #
# Test 3: group means correct (PASS_TO_PASS)
# --------------------------------------------------------------------------- #
def test_group_means():
    gm = _result["group_means"]
    assert isinstance(gm, dict), "group_means must be a dict"
    assert set(gm.keys()) == set(REF["group_means"].keys()), "group_means labels mismatch"
    for lab, ref in REF["group_means"].items():
        assert gu.close(gm[lab], ref, rtol=1e-4), (
            f"group_means['{lab}'] mismatch: got {gm[lab]}, expected {ref}"
        )


# --------------------------------------------------------------------------- #
# Test 4: sample sizes correct (PASS_TO_PASS)
# --------------------------------------------------------------------------- #
def test_n_per_group():
    n = _result["n_per_group"]
    assert isinstance(n, dict), "n_per_group must be a dict"
    assert set(n.keys()) == set(REF["n_per_group"].keys()), "n_per_group labels mismatch"
    for lab, ref in REF["n_per_group"].items():
        assert n[lab] == ref, f"n_per_group['{lab}'] mismatch: got {n[lab]}, expected {ref}"


# --------------------------------------------------------------------------- #
# Test 5: ANOVA F / p match the inline f_oneway reference; omnibus significant
# --------------------------------------------------------------------------- #
def test_anova_matches_reference():
    f = _result["anova_f"]
    p = _result["anova_p"]
    assert isinstance(f, float), "anova_f must be a float"
    assert isinstance(p, float), "anova_p must be a float"
    assert gu.close(f, REF["anova_f"], rtol=1e-3), (
        f"anova_f mismatch: got {f}, expected {REF['anova_f']}"
    )
    assert gu.close(p, REF["anova_p"], rtol=1e-3), (
        f"anova_p mismatch: got {p}, expected {REF['anova_p']}"
    )
    assert _result["omnibus_significant"] is True, "omnibus_significant must be True"
    assert p < ALPHA, f"anova_p must be < {ALPHA}, got {p}"


# --------------------------------------------------------------------------- #
# Test 6: raw pairwise p-values match the inline ttest_ind reference
# --------------------------------------------------------------------------- #
def test_raw_pvalues_match_reference():
    pairs = _result["pairs"]
    for key, ref_raw in REF["raw_p"].items():
        got = pairs[key]["raw_p"]
        assert gu.close(got, ref_raw, rtol=1e-3), (
            f"raw_p for {key} mismatch: got {got}, expected {ref_raw}"
        )


# --------------------------------------------------------------------------- #
# Test 7: adjusted p-values match the inline Holm reference and are >= raw
#         (FAIL_TO_PASS — broken sets adj_p = raw_p, so the discriminator fails)
# --------------------------------------------------------------------------- #
def test_adjusted_pvalues_match_holm_reference():
    pairs = _result["pairs"]
    for key, ref_adj in REF["adj_p"].items():
        got = pairs[key]["adj_p"]
        assert gu.close(got, ref_adj, rtol=1e-3), (
            f"adj_p for {key} mismatch: got {got}, expected Holm value {ref_adj}"
        )
        # A correction never makes a p-value smaller.
        assert got >= pairs[key]["raw_p"] - 1e-9, (
            f"adj_p for {key} must be >= raw_p (got adj={got}, raw={pairs[key]['raw_p']})"
        )


# --------------------------------------------------------------------------- #
# Test 8: the discriminator pair — raw-significant but NOT Holm-significant
#         (FAIL_TO_PASS — gold demotes it; broken keeps it significant)
# --------------------------------------------------------------------------- #
def test_discriminator_pair_demoted_by_correction():
    pairs = _result["pairs"]
    info = pairs[DISCRIMINATOR]
    # The raw p-value is below alpha (significant before correction)...
    assert info["raw_p"] < ALPHA, (
        f"{DISCRIMINATOR} raw_p should be < {ALPHA}, got {info['raw_p']}"
    )
    # ...but the Holm-adjusted p-value strictly inflates it past alpha...
    assert info["adj_p"] > info["raw_p"], (
        f"{DISCRIMINATOR} adj_p ({info['adj_p']}) must exceed raw_p "
        f"({info['raw_p']}) after Holm correction"
    )
    assert gu.close(info["adj_p"], REF["adj_p"][DISCRIMINATOR], rtol=1e-3), (
        f"{DISCRIMINATOR} adj_p mismatch: got {info['adj_p']}, "
        f"expected {REF['adj_p'][DISCRIMINATOR]}"
    )
    # ...so the corrected significance flag is False.
    assert info["significant"] is False, (
        f"{DISCRIMINATOR} must NOT be significant after Holm correction "
        f"(adj_p={info['adj_p']})"
    )


# --------------------------------------------------------------------------- #
# Test 9: n_significant_pairs equals the corrected count (lower than raw count)
#         (FAIL_TO_PASS — broken counts the discriminator as significant)
# --------------------------------------------------------------------------- #
def test_n_significant_pairs_is_corrected_count():
    n_sig = _result["n_significant_pairs"]
    assert isinstance(n_sig, int), "n_significant_pairs must be an int"
    assert n_sig == REF["n_significant_pairs"], (
        f"n_significant_pairs mismatch: got {n_sig}, "
        f"expected corrected count {REF['n_significant_pairs']}"
    )
    raw_sig_count = sum(1 for k, v in REF["raw_p"].items() if v < ALPHA)
    assert n_sig < raw_sig_count, (
        f"corrected count ({n_sig}) must be lower than the naive raw count "
        f"({raw_sig_count})"
    )
    # Cross-check: the per-pair significant flags agree with the corrected count.
    flagged = sum(1 for info in _result["pairs"].values() if info["significant"])
    assert flagged == n_sig, (
        f"sum of significant flags ({flagged}) != n_significant_pairs ({n_sig})"
    )


# --------------------------------------------------------------------------- #
# Test 10: surface-form check — must use scipy.stats.f_oneway
# --------------------------------------------------------------------------- #
def test_source_uses_f_oneway():
    usage = gu.source_uses(SOL, ["f_oneway"])
    assert usage["f_oneway"], (
        "solution.py must invoke scipy.stats.f_oneway (surface-form constraint)"
    )


# --------------------------------------------------------------------------- #
# Test 11: CLI writes results.json with required keys and correct corrected count
# --------------------------------------------------------------------------- #
def test_cli_results_json(tmp_path):
    proc = gu.run_cli(
        SOL, ["--data", str(DATA_CSV), "--output-dir", str(tmp_path)], timeout=60,
    )
    assert proc.returncode == 0, f"CLI exited non-zero:\n{proc.stderr}"
    results_path = tmp_path / "results.json"
    assert results_path.exists(), "results.json was not written"
    data = json.loads(results_path.read_text())
    required = {
        "group_means", "n_per_group", "anova_f", "anova_p",
        "omnibus_significant", "pairs", "n_significant_pairs",
    }
    missing = required - set(data.keys())
    assert not missing, f"results.json missing keys: {missing}"
    assert data["omnibus_significant"] is True, "results.json omnibus_significant must be True"
    assert data["n_significant_pairs"] == REF["n_significant_pairs"], (
        f"results.json n_significant_pairs mismatch: got {data['n_significant_pairs']}, "
        f"expected {REF['n_significant_pairs']}"
    )
    # The discriminator pair must be demoted in the written artifact too.
    assert data["pairs"][DISCRIMINATOR]["significant"] is False, (
        f"results.json {DISCRIMINATOR} must not be significant after correction"
    )


# --------------------------------------------------------------------------- #
# Test 12: CLI writes at least 2 valid PNG files
# --------------------------------------------------------------------------- #
def test_cli_pngs(tmp_path):
    proc = gu.run_cli(
        SOL, ["--data", str(DATA_CSV), "--output-dir", str(tmp_path)], timeout=60,
    )
    assert proc.returncode == 0, f"CLI exited non-zero:\n{proc.stderr}"
    n_pngs = gu.count_valid_pngs(tmp_path)
    assert n_pngs >= 2, (
        f"Expected at least 2 valid PNG files, found {n_pngs}. "
        f"Files: {list(tmp_path.glob('*.png'))}"
    )


# --------------------------------------------------------------------------- #
# Advisory: code quality (never asserted as pass/fail)
# --------------------------------------------------------------------------- #
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
