"""Grader for swe_bench/swe09_evolve_ttl_index. Public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
The broken variant's ``Store.range_invalidate`` pops victims directly from the
primary map without routing through ``_unlink``, so the secondary index keeps
ghost keys. The symptom is observed via ``DB.query_by_field`` / ``index_is_consistent``
(db.py + index.py); the root cause is in store.py.

  PASS_TO_PASS (gold AND broken):
    1. test_put_get_basic                 — set then get
    2. test_absent_key_raises             — get on absent key raises KeyError
    3. test_eviction_updates_index        — LRU eviction also clears the index
    4. test_ttl_expiry_updates_index      — expired key gone from store + index
    5. test_delete_updates_index          — delete clears store + index
    6. test_query_by_field_basic          — index reflects normal puts
    7. test_overwrite_changes_field       — overwrite re-points the index
    8. test_range_invalidate_removes_keys — removed keys raise KeyError on get

  FAIL_TO_PASS (gold true, broken false):
    9. test_range_invalidate_clears_index — no ghost keys in query_by_field
   10. test_range_invalidate_keeps_invariant — index_is_consistent() stays True
   11. test_reput_after_range_invalidate — re-put returns only the fresh key

  Advisory:
   12. test_code_quality_report
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "swe_bench", "swe09_evolve_ttl_index"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

_index_mod = gu.load_module(SOL, "index.py", alias="index")
_store_mod = gu.load_module(SOL, "store.py", alias="store")
_db_mod = gu.load_module(SOL, "db.py", alias="db")

FieldIndex = getattr(_index_mod, "FieldIndex")
Store = getattr(_store_mod, "Store")
DB = getattr(_db_mod, "DB")


class FakeClock:
    """A controllable zero-arg clock for deterministic TTL tests."""

    def __init__(self) -> None:
        self.t = 0

    def __call__(self):
        return self.t

    def advance(self, dt) -> None:
        self.t += dt


def _db(capacity=8):
    return DB(capacity=capacity, clock=FakeClock())


# ===========================================================================
# PASS_TO_PASS
# ===========================================================================

def test_put_get_basic():
    db = _db()
    db.put("a", 1, field_value=10)
    assert db.get("a") == 1


def test_absent_key_raises():
    db = _db()
    with pytest.raises(KeyError):
        db.get("nope")


def test_eviction_updates_index():
    db = _db(capacity=2)
    db.put("a", 1, field_value=10)
    db.put("b", 2, field_value=10)
    db.put("c", 3, field_value=10)  # evicts LRU "a"
    with pytest.raises(KeyError):
        db.get("a")
    assert db.query_by_field(10) == {"b", "c"}
    assert db.index_is_consistent()


def test_ttl_expiry_updates_index():
    clock = FakeClock()
    db = DB(capacity=8, clock=clock)
    db.put("a", 1, field_value=10, ttl=5)
    assert db.get("a") == 1
    clock.advance(6)  # now past expiry
    with pytest.raises(KeyError):
        db.get("a")
    assert db.query_by_field(10) == set()
    assert db.index_is_consistent()


def test_delete_updates_index():
    db = _db()
    db.put("a", 1, field_value=10)
    db.delete("a")
    with pytest.raises(KeyError):
        db.get("a")
    assert db.query_by_field(10) == set()
    assert db.index_is_consistent()


def test_query_by_field_basic():
    db = _db()
    db.put("a", 1, field_value=10)
    db.put("b", 2, field_value=10)
    db.put("c", 3, field_value=20)
    assert db.query_by_field(10) == {"a", "b"}
    assert db.query_by_field(20) == {"c"}
    assert db.query_by_field(99) == set()


def test_overwrite_changes_field():
    db = _db()
    db.put("a", 1, field_value=10)
    db.put("a", 1, field_value=20)  # same key, new field value
    assert db.query_by_field(10) == set()
    assert db.query_by_field(20) == {"a"}
    assert db.index_is_consistent()


def test_range_invalidate_removes_keys():
    # Both gold and broken remove from the primary store, so get() raises either way.
    db = _db()
    db.put("a", 1, field_value=10)
    db.put("b", 2, field_value=12)
    db.put("c", 3, field_value=30)
    db.range_invalidate(5, 15)  # removes a (10) and b (12)
    with pytest.raises(KeyError):
        db.get("a")
    with pytest.raises(KeyError):
        db.get("b")
    assert db.get("c") == 3


# ===========================================================================
# FAIL_TO_PASS — index consistency after range_invalidate (broken fails these)
# ===========================================================================

def test_range_invalidate_clears_index():
    db = _db()
    db.put("a", 1, field_value=10)
    db.put("b", 2, field_value=12)
    db.put("c", 3, field_value=30)
    db.range_invalidate(5, 15)
    assert db.query_by_field(10) == set(), "index must not keep ghost keys after range_invalidate"
    assert db.query_by_field(12) == set()
    assert db.query_by_field(30) == {"c"}


def test_range_invalidate_keeps_invariant():
    db = _db()
    for i, key in enumerate(["a", "b", "c", "d", "e"]):
        db.put(key, i, field_value=i * 5)  # fields 0,5,10,15,20
    db.range_invalidate(5, 15)  # removes b(5), c(10), d(15)
    assert db.index_is_consistent(), "store/index invariant violated after range_invalidate"
    assert db.query_by_field(5) == set()
    assert db.query_by_field(0) == {"a"}
    assert db.query_by_field(20) == {"e"}


def test_reput_after_range_invalidate():
    db = _db()
    db.put("a", 1, field_value=10)
    db.range_invalidate(10, 10)          # remove "a"
    db.put("z", 9, field_value=10)        # fresh key, same field value
    assert db.query_by_field(10) == {"z"}, "must return only the fresh key, not a ghost"
    assert db.index_is_consistent()


# ===========================================================================
# Advisory
# ===========================================================================

@pytest.mark.code_quality
def test_code_quality_report():
    print("code_quality:", gu.code_quality_report(SOL))
