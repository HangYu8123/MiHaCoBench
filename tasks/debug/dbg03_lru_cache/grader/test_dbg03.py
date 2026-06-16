"""Grader for debug/dbg03_lru_cache. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold (fixed) reference, FAILS on the broken
(still-buggy) reference. The FAIL_TO_PASS tests observe eviction *order* after a
read (a hit must refresh recency); the PASS_TO_PASS tests guard basic get/put,
overflow eviction without an intervening read, and the capacity invariant.
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "debug", "dbg03_lru_cache"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
RecentCache = gu.load_callable(SOL, "solution.py", "RecentCache")


# ---- FAIL_TO_PASS: read must refresh recency -------------------------------- #
def test_get_refreshes_recency():
    c = RecentCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1          # "a" is now most-recently-used; "b" is LRU
    c.put("c", 3)                   # must evict "b", not "a"
    assert c.get("a") == 1
    assert c.get("c") == 3
    assert c.get("b") is None


def test_repeated_reads_keep_key_alive():
    c = RecentCache(2)
    c.put("x", 10)
    c.put("y", 20)
    for _ in range(3):
        assert c.get("x") == 10     # keep "x" hot
    c.put("z", 30)                  # evicts the cold "y"
    assert c.get("y") is None
    assert c.get("x") == 10


# ---- PASS_TO_PASS: behaviour the buggy cache already handles ----------------- #
def test_basic_put_get():
    c = RecentCache(2)
    c.put("a", 1)
    assert c.get("a") == 1
    assert c.get("missing") is None


def test_overflow_evicts_lru_without_reads():
    c = RecentCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)                   # no intervening get → "a" is LRU → evicted
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_update_existing_key_value():
    c = RecentCache(2)
    c.put("a", 1)
    c.put("a", 99)
    assert c.get("a") == 99


def test_put_existing_key_refreshes_recency():
    c = RecentCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 99)                  # updating "a" must make it most-recently-used
    c.put("c", 3)                   # → evict "b", not "a"
    assert c.get("a") == 99
    assert c.get("c") == 3
    assert c.get("b") is None


def test_overflow_keeps_only_most_recent_without_reads():
    c = RecentCache(3)
    for i in range(10):
        c.put(i, i * i)             # no intervening reads → 3 most-recently-put survive
    assert c.get(7) == 49 and c.get(8) == 64 and c.get(9) == 81
    assert all(c.get(gone) is None for gone in range(7))


def test_capacity_must_be_positive():
    with pytest.raises(ValueError):
        RecentCache(0)


@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted as pass/fail
