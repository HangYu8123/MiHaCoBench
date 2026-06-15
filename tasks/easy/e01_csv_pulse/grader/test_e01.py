"""Grader for easy/e01_csv_pulse. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
"""
import json
import math

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "easy", "e01_csv_pulse"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
summarize = gu.load_callable(SOL, "solution.py", "summarize")

ROWS = [
    {"city": "A", "temp": "10", "humidity": "30", "note": "x"},
    {"city": "B", "temp": "20", "humidity": "50", "note": "y"},
    {"city": "C", "temp": "30", "humidity": "70", "note": "z"},
    {"city": "D", "temp": "40", "humidity": "", "note": "w"},
]


def test_numeric_columns_detected():
    res = summarize(ROWS)
    assert set(res) == {"temp", "humidity"}  # city/note are non-numeric → omitted


def test_temp_statistics_exact():
    s = summarize(ROWS)["temp"]
    assert s["count"] == 4
    assert gu.close(s["mean"], 25.0)
    assert gu.close(s["median"], 25.0)       # (20+30)/2
    assert gu.close(s["min"], 10.0)
    assert gu.close(s["max"], 40.0)
    # population std of [10,20,30,40] = sqrt(125) ≈ 11.18034
    assert gu.close(s["std"], math.sqrt(125.0))


def test_empty_cells_skipped():
    s = summarize(ROWS)["humidity"]
    assert s["count"] == 3                    # the "" was skipped
    assert gu.close(s["mean"], 50.0)
    assert gu.close(s["median"], 50.0)


def test_mixed_column_is_omitted():
    rows = [{"v": "1"}, {"v": "2"}, {"v": "oops"}]
    assert "v" not in summarize(rows)


def test_all_empty_column_omitted():
    rows = [{"v": ""}, {"v": ""}]
    assert summarize(rows) == {}


def test_median_odd_count():
    rows = [{"v": "1"}, {"v": "100"}, {"v": "7"}]
    assert gu.close(summarize(rows)["v"]["median"], 7.0)


def test_float_values():
    rows = [{"p": "1.5"}, {"p": "2.5"}, {"p": "3.5"}]
    s = summarize(rows)["p"]
    assert gu.close(s["mean"], 2.5)
    assert gu.close(s["std"], math.sqrt(((1.0) + 0.0 + 1.0) / 3))  # var of [1.5,2.5,3.5]=2/3


def test_cli_full(tmp_path):
    csv_path = tmp_path / "in.csv"
    csv_path.write_text("a,b\n1,x\n2,y\n3,z\n")
    proc = gu.run_cli(SOL, [str(csv_path)], timeout=30)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert set(out) == {"a"}
    assert gu.close(out["a"]["mean"], 2.0)


def test_cli_single_column(tmp_path):
    csv_path = tmp_path / "in.csv"
    csv_path.write_text("a,b\n1,10\n2,20\n3,30\n")
    proc = gu.run_cli(SOL, [str(csv_path), "--column", "b"], timeout=30)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert gu.close(out["mean"], 20.0)


def test_cli_bad_column_errors(tmp_path):
    csv_path = tmp_path / "in.csv"
    csv_path.write_text("a,b\n1,x\n2,y\n")
    proc = gu.run_cli(SOL, [str(csv_path), "--column", "b"], timeout=30)  # b is non-numeric
    assert proc.returncode != 0


@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted as pass/fail
