"""Grader for complex/c05_etl_framework. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The grader exercises the Pipeline facade via:
  - from_yaml() + run() for extraction, filtering, renaming, deriving, aggregating
  - query() for SQL access to the loaded table
  - Error cases (missing columns, pre-run query)
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "complex", "c05_etl_framework"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Data directory committed alongside this task (absolute path, never relative)
# __file__ is at tasks/complex/c05_etl_framework/grader/test_c05.py
# parents[0] = grader/, parents[1] = c05_etl_framework/, parents[2] = complex/
DATA_DIR = str(
    Path(__file__).resolve().parents[1] / "data"
)

# Load the Pipeline class from the solution's pipeline.py
Pipeline = gu.load_callable(SOL, "pipeline.py", "Pipeline")


# ---------------------------------------------------------------------------
# YAML specs used across tests
# ---------------------------------------------------------------------------

YAML_FULL = """
extract:
  csv: sales.csv
transforms:
  - op: filter
    column: quantity
    op_kind: ">"
    value: 5
  - op: rename
    mapping:
      unit_price: price
  - op: derive
    column: revenue
    expr: "quantity * price"
  - op: aggregate
    group_by:
      - product
    agg:
      revenue: sum
      quantity: sum
load:
  table: sales_summary
"""

YAML_FILTER_ONLY = """
extract:
  csv: sales.csv
transforms:
  - op: filter
    column: quantity
    op_kind: ">"
    value: 5
load:
  table: filtered_sales
"""

YAML_RENAME_ONLY = """
extract:
  csv: sales.csv
transforms:
  - op: rename
    mapping:
      unit_price: price
      order_id: id
load:
  table: renamed_sales
"""

YAML_DERIVE_ONLY = """
extract:
  csv: sales.csv
transforms:
  - op: derive
    column: revenue
    expr: "quantity * unit_price"
load:
  table: derived_sales
"""

YAML_AGGREGATE_ONLY = """
extract:
  csv: sales.csv
transforms:
  - op: aggregate
    group_by:
      - region
    agg:
      quantity: sum
load:
  table: region_summary
"""

YAML_NO_TRANSFORMS = """
extract:
  csv: sales.csv
transforms: []
load:
  table: raw_load
"""


# ---------------------------------------------------------------------------
# Test 1: from_yaml returns a Pipeline instance
# ---------------------------------------------------------------------------

def test_from_yaml_returns_pipeline():
    """from_yaml must return a Pipeline instance without error."""
    p = Pipeline.from_yaml(YAML_FULL, data_dir=DATA_DIR)
    assert p is not None
    # Must have a run method
    assert callable(getattr(p, "run", None))
    assert callable(getattr(p, "query", None))


# ---------------------------------------------------------------------------
# Test 2: filter — correct number of rows after filter quantity > 5
# ---------------------------------------------------------------------------

def test_filter_row_count():
    """Filter quantity > 5 should leave exactly 9 rows (from the committed CSV)."""
    p = Pipeline.from_yaml(YAML_FILTER_ONLY, data_dir=DATA_DIR)
    df = p.run()
    # From data/sales.csv, rows with quantity > 5: order_ids 1,4,5,7,9,10,11,12,15 = 9
    assert len(df) == 9


# ---------------------------------------------------------------------------
# Test 3: filter — all retained rows satisfy the predicate
# ---------------------------------------------------------------------------

def test_filter_predicate_satisfied():
    """Every row returned by filter quantity > 5 must have quantity > 5."""
    p = Pipeline.from_yaml(YAML_FILTER_ONLY, data_dir=DATA_DIR)
    df = p.run()
    assert (df["quantity"] > 5).all(), "Some filtered rows have quantity <= 5"


# ---------------------------------------------------------------------------
# Test 4: rename — columns are renamed correctly
# ---------------------------------------------------------------------------

def test_rename_columns():
    """Rename transform should rename unit_price→price and order_id→id."""
    p = Pipeline.from_yaml(YAML_RENAME_ONLY, data_dir=DATA_DIR)
    df = p.run()
    assert "price" in df.columns, "column 'price' missing after rename"
    assert "id" in df.columns, "column 'id' missing after rename"
    assert "unit_price" not in df.columns, "old column 'unit_price' still present"
    assert "order_id" not in df.columns, "old column 'order_id' still present"
    # Values unchanged
    assert gu.close(float(df["price"].iloc[0]), 2.50)


# ---------------------------------------------------------------------------
# Test 5: derive — revenue column is correct
# ---------------------------------------------------------------------------

def test_derive_revenue_values():
    """DeriveColumn should add revenue = quantity * unit_price correctly."""
    p = Pipeline.from_yaml(YAML_DERIVE_ONLY, data_dir=DATA_DIR)
    df = p.run()
    assert "revenue" in df.columns, "derived column 'revenue' missing"
    # Row 0: quantity=10, unit_price=2.50 → revenue=25.0
    assert gu.close(float(df["revenue"].iloc[0]), 25.0)
    # Row 1: quantity=5, unit_price=1.20 → revenue=6.0
    assert gu.close(float(df["revenue"].iloc[1]), 6.0)
    # Row 2: quantity=3, unit_price=2.50 → revenue=7.5
    assert gu.close(float(df["revenue"].iloc[2]), 7.5)


# ---------------------------------------------------------------------------
# Test 6: aggregate — correct group-by results
# ---------------------------------------------------------------------------

def test_aggregate_region_quantity():
    """Aggregate quantity sum by region should produce 4 rows with correct sums."""
    p = Pipeline.from_yaml(YAML_AGGREGATE_ONLY, data_dir=DATA_DIR)
    df = p.run()
    # All 4 regions should appear
    assert set(df["region"]) == {"north", "south", "east", "west"}
    # Build lookup: region → total quantity
    # From data/sales.csv:
    # north: 10+3+2+11 = 26
    # south: 5+12+9 = 26  (but wait: south rows are order 2,5,11,15)
    # south: 5+12+9+7 = 33
    # east: 8+7+15+5 = 35
    # west: 4+6+3 = 13
    qty_by_region = dict(zip(df["region"], df["quantity"]))
    assert qty_by_region["north"] == 26
    assert qty_by_region["south"] == 33
    assert qty_by_region["east"] == 35
    assert qty_by_region["west"] == 13


# ---------------------------------------------------------------------------
# Test 7: full pipeline — aggregate sums correct after filter+rename+derive
# ---------------------------------------------------------------------------

def test_full_pipeline_aggregate_values():
    """Full pipeline: filter→rename→derive→aggregate should give correct revenue sums."""
    p = Pipeline.from_yaml(YAML_FULL, data_dir=DATA_DIR)
    df = p.run()
    # After filter (quantity > 5) and derive (revenue = quantity * price):
    # apple: order_ids 1,7,10,11 → revenues 25.0, 17.5, 37.5, 22.5 → sum=102.5
    # banana: order_ids 5,12 → revenues 14.4, 13.2 → sum=27.6
    # cherry: order_ids 4,9,15 → revenues 24.0, 18.0, 21.0 → sum=63.0
    rev_by_product = dict(zip(df["product"], df["revenue"]))
    assert gu.close(rev_by_product["apple"], 102.5, rtol=1e-3)
    assert gu.close(rev_by_product["banana"], 27.6, rtol=1e-3)
    assert gu.close(rev_by_product["cherry"], 63.0, rtol=1e-3)


# ---------------------------------------------------------------------------
# Test 8: full pipeline — quantity sums after filter
# ---------------------------------------------------------------------------

def test_full_pipeline_quantity_sums():
    """Full pipeline aggregate quantity sum per product must be correct."""
    p = Pipeline.from_yaml(YAML_FULL, data_dir=DATA_DIR)
    df = p.run()
    # apple: 10+7+15+9 = 41; banana: 12+11 = 23; cherry: 8+6+7 = 21
    qty_by_product = dict(zip(df["product"], df["quantity"]))
    assert qty_by_product["apple"] == 41
    assert qty_by_product["banana"] == 23
    assert qty_by_product["cherry"] == 21


# ---------------------------------------------------------------------------
# Test 9: query() returns matching rows from the loaded table
# ---------------------------------------------------------------------------

def test_query_returns_correct_rows():
    """query() must return rows consistent with the loaded aggregate table."""
    p = Pipeline.from_yaml(YAML_FULL, data_dir=DATA_DIR)
    p.run()
    rows = p.query("SELECT product, quantity FROM sales_summary ORDER BY product")
    assert len(rows) == 3
    row_map = {r["product"]: r["quantity"] for r in rows}
    assert row_map["apple"] == 41
    assert row_map["banana"] == 23
    assert row_map["cherry"] == 21


# ---------------------------------------------------------------------------
# Test 10: query() before run() raises RuntimeError
# ---------------------------------------------------------------------------

def test_query_before_run_raises_runtime_error():
    """query() must raise RuntimeError if called before run()."""
    p = Pipeline.from_yaml(YAML_FULL, data_dir=DATA_DIR)
    with pytest.raises(RuntimeError):
        p.query("SELECT 1")


# ---------------------------------------------------------------------------
# Test 11: filter with missing column raises ValueError
# ---------------------------------------------------------------------------

def test_filter_missing_column_raises_value_error():
    """Filter on a non-existent column must raise ValueError."""
    bad_yaml = """
extract:
  csv: sales.csv
transforms:
  - op: filter
    column: nonexistent_col
    op_kind: ">"
    value: 5
load:
  table: bad
"""
    p = Pipeline.from_yaml(bad_yaml, data_dir=DATA_DIR)
    with pytest.raises(ValueError):
        p.run()


# ---------------------------------------------------------------------------
# Test 12: aggregate with missing group_by column raises ValueError
# ---------------------------------------------------------------------------

def test_aggregate_missing_column_raises_value_error():
    """Aggregate on a missing group_by column must raise ValueError."""
    bad_yaml = """
extract:
  csv: sales.csv
transforms:
  - op: aggregate
    group_by:
      - not_a_real_column
    agg:
      quantity: sum
load:
  table: bad
"""
    p = Pipeline.from_yaml(bad_yaml, data_dir=DATA_DIR)
    with pytest.raises(ValueError):
        p.run()


# ---------------------------------------------------------------------------
# Test 13: no-transform pipeline loads all 15 rows
# ---------------------------------------------------------------------------

def test_no_transforms_all_rows_loaded():
    """Without transforms, all 15 rows from the CSV must be loaded."""
    p = Pipeline.from_yaml(YAML_NO_TRANSFORMS, data_dir=DATA_DIR)
    df = p.run()
    assert len(df) == 15
    assert set(df.columns) == {"order_id", "region", "product", "quantity", "unit_price", "discount"}


# ---------------------------------------------------------------------------
# Test 14: run() is idempotent (second call replaces the table)
# ---------------------------------------------------------------------------

def test_run_is_idempotent():
    """Calling run() twice must not raise; the second run replaces the table."""
    p = Pipeline.from_yaml(YAML_AGGREGATE_ONLY, data_dir=DATA_DIR)
    df1 = p.run()
    df2 = p.run()
    assert len(df1) == len(df2)
    rows = p.query("SELECT COUNT(*) AS n FROM region_summary")
    assert rows[0]["n"] == 4


# ---------------------------------------------------------------------------
# Test 15: query() with a more complex SQL expression works
# ---------------------------------------------------------------------------

def test_query_with_where_clause():
    """query() must support WHERE clauses."""
    p = Pipeline.from_yaml(YAML_FULL, data_dir=DATA_DIR)
    p.run()
    rows = p.query("SELECT product, revenue FROM sales_summary WHERE product = 'apple'")
    assert len(rows) == 1
    assert gu.close(float(rows[0]["revenue"]), 102.5, rtol=1e-3)


# ---------------------------------------------------------------------------
# Advisory test — code quality (never asserted as pass/fail)
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory code quality metrics — printed only, never gated."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
