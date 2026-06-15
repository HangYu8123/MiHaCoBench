"""Grader for easy/e03_freq_lru.  Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

Broken variant defects:
  1. Uses LFU eviction instead of LRU  -> test_lru_eviction_order FAILS
  2. histogram() retains evicted keys   -> test_evicted_key_absent_from_histogram FAILS
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "easy", "e03_freq_lru"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
FreqLRU = gu.load_callable(SOL, "solution.py", "FreqLRU")


# ---------------------------------------------------------------------------
# Test 1 — basic put and get
# ---------------------------------------------------------------------------
def test_basic_put_and_get():
    cache = FreqLRU(3)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    assert cache.get("b") == 2
    assert len(cache) == 2


# ---------------------------------------------------------------------------
# Test 2 — get miss returns None and changes nothing
# ---------------------------------------------------------------------------
def test_get_miss_returns_none():
    cache = FreqLRU(2)
    cache.put("x", 42)
    result = cache.get("missing")
    assert result is None
    assert len(cache) == 1                    # no phantom insertion
    hist = cache.histogram()
    assert "missing" not in hist              # miss leaves no histogram trace


# ---------------------------------------------------------------------------
# Test 3 — LRU eviction order (this is the critical correctness test)
#
# Sequence:
#   put a, put b, put c  (capacity=3, all resident; order LRU->MRU: a,b,c)
#   get a                (a accessed -> order: b,c,a)
#   put d                (capacity full -> evict LRU = b)
#   => b should be gone, a/c/d present
# ---------------------------------------------------------------------------
def test_lru_eviction_order():
    cache = FreqLRU(3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    cache.get("a")       # refresh a -> LRU order: b, c, a
    cache.put("d", 4)    # evict b (least recently used)

    assert len(cache) == 3
    assert cache.get("b") is None    # b was evicted
    assert cache.get("a") == 1      # a survived
    assert cache.get("c") == 3      # c survived
    assert cache.get("d") == 4      # d was just inserted


# ---------------------------------------------------------------------------
# Test 4 — get hit refreshes recency (another LRU scenario)
#
# Sequence:
#   put a, put b  (capacity=2; LRU->MRU: a, b)
#   get a         (a refreshed -> order: b, a)
#   put c         (evict LRU = b, not a)
# ---------------------------------------------------------------------------
def test_get_refreshes_recency():
    cache = FreqLRU(2)
    cache.put("a", 10)
    cache.put("b", 20)
    cache.get("a")        # refresh a -> b is now LRU
    cache.put("c", 30)    # b should be evicted, not a

    assert cache.get("b") is None
    assert cache.get("a") == 10
    assert cache.get("c") == 30


# ---------------------------------------------------------------------------
# Test 5 — histogram counts (get-hits + puts combined)
# ---------------------------------------------------------------------------
def test_histogram_counts():
    cache = FreqLRU(5)
    cache.put("k", 0)     # freq k=1
    cache.put("k", 1)     # freq k=2 (update existing)
    cache.get("k")        # freq k=3
    cache.get("k")        # freq k=4
    cache.put("m", 99)    # freq m=1
    cache.get("m")        # freq m=2

    hist = cache.histogram()
    assert hist["k"] == 4
    assert hist["m"] == 2


# ---------------------------------------------------------------------------
# Test 6 — evicted key is absent from histogram
# ---------------------------------------------------------------------------
def test_evicted_key_absent_from_histogram():
    cache = FreqLRU(2)
    cache.put("a", 1)   # freq a=1
    cache.put("a", 2)   # freq a=2
    cache.put("a", 3)   # freq a=3  (a accessed 3 times — high freq but NOT MRU anymore
                        #            after b is inserted and accessed)
    cache.put("b", 10)  # freq b=1; LRU order: a (older), b (newer)
    cache.get("b")      # freq b=2; b refreshed -> LRU order: a, b
    # Now put c — evict LRU = a (even though a has higher freq than b)
    cache.put("c", 20)  # evicts a

    hist = cache.histogram()
    assert "a" not in hist             # evicted key must not appear
    assert "b" in hist
    assert "c" in hist
    assert len(cache) == 2


# ---------------------------------------------------------------------------
# Test 7 — capacity <= 0 raises ValueError
# ---------------------------------------------------------------------------
def test_capacity_zero_raises():
    with pytest.raises(ValueError):
        FreqLRU(0)


def test_capacity_negative_raises():
    with pytest.raises(ValueError):
        FreqLRU(-5)


# ---------------------------------------------------------------------------
# Test 8 — put updating existing key increments count, no eviction
# ---------------------------------------------------------------------------
def test_put_update_existing_no_eviction():
    cache = FreqLRU(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 99)   # update existing — should NOT evict b
    assert len(cache) == 2
    assert cache.get("a") == 99
    assert cache.get("b") == 2
    hist = cache.histogram()
    assert hist["a"] == 3   # put + put-update + get == 3 accesses
    assert hist["b"] == 2   # put + get == 2 accesses


# ---------------------------------------------------------------------------
# Test 9 — len() stays within capacity
# ---------------------------------------------------------------------------
def test_len_stays_within_capacity():
    capacity = 4
    cache = FreqLRU(capacity)
    for i in range(20):
        cache.put(i, i * i)
        assert len(cache) <= capacity


# ---------------------------------------------------------------------------
# Test 10 — histogram keys match resident keys exactly
# ---------------------------------------------------------------------------
def test_histogram_keys_match_resident_keys():
    cache = FreqLRU(3)
    cache.put("x", 1)
    cache.put("y", 2)
    cache.put("z", 3)
    cache.put("w", 4)   # evicts x (LRU)
    hist = cache.histogram()
    assert set(hist.keys()) == {"y", "z", "w"}


# ---------------------------------------------------------------------------
# Advisory: code quality (never asserted as pass/fail)
# ---------------------------------------------------------------------------
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never gated
