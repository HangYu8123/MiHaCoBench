"""Grader for swe_bench/swe06_lru_writeback. Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.
The broken variant's ``LRU.put`` returns early on an existing key without
overwriting the stored value, so after a write-through update the cache keeps
serving the stale value. The symptom is observed via ``KV.get`` (kv.py); the
root cause is in cache.py.

Tests:
  PASS_TO_PASS (gold AND broken) — fresh writes, read-through, KeyError, eviction:
    1. test_set_then_get_fresh_key      — basic set then get of a fresh key
    2. test_get_falls_through_to_backing — key only in backing is read + cached
    3. test_absent_key_raises_keyerror  — truly absent key raises KeyError
    4. test_eviction_drops_lru          — capacity 2, 3rd key evicts the LRU one
    5. test_eviction_via_backing_fallback — evicted key still served via backing
    6. test_miss_sentinel_semantics     — MISS distinct from None; get() returns it
    7. test_invalidate_drops_key        — invalidate removes a cached key

  FAIL_TO_PASS (gold true, broken false) — existing-key overwrite:
    8. test_update_existing_key_via_set — kv.set then kv.get returns the NEW value
    9. test_repeated_updates_reflect_latest — many updates always show latest write
   10. test_cache_put_overwrites_existing — LRU.put on existing key overwrites value

  Advisory:
   11. test_code_quality_report
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "swe_bench", "swe06_lru_writeback"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load each of the three modules separately (multi-file solution).
_store_mod = gu.load_module(SOL, "store.py", alias="store")
_cache_mod = gu.load_module(SOL, "cache.py", alias="cache")
_kv_mod = gu.load_module(SOL, "kv.py", alias="kv")

Backing = getattr(_store_mod, "Backing")
LRU = getattr(_cache_mod, "LRU")
MISS = getattr(_cache_mod, "MISS")
KV = getattr(_kv_mod, "KV")


# ===========================================================================
# PASS_TO_PASS tests — fresh writes, read-through, KeyError, eviction
# ===========================================================================

def test_set_then_get_fresh_key():
    """Basic write-through: set a fresh key, then get returns that value."""
    kv = KV(Backing(), capacity=4)
    kv.set("a", 1)
    assert kv.get("a") == 1


def test_get_falls_through_to_backing():
    """A key present only in the backing store is read through and cached."""
    backing = Backing()
    backing.set("seed", 99)          # bypass the cache entirely
    kv = KV(backing, capacity=4)
    assert kv.get("seed") == 99      # miss -> backing read -> cache populate
    # A second read returns the same value (now served from the cache).
    assert kv.get("seed") == 99


def test_absent_key_raises_keyerror():
    """A truly absent key surfaces KeyError through the facade."""
    kv = KV(Backing(), capacity=4)
    with pytest.raises(KeyError):
        kv.get("never_set")


def test_eviction_drops_lru():
    """Capacity 2: inserting a 3rd distinct key evicts the least-recently-used."""
    cache = LRU(capacity=2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)                # "a" is LRU and must be evicted
    assert cache.get("a") is MISS, "least-recently-used key should be evicted"
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_eviction_via_backing_fallback():
    """An evicted key is no longer cached but is still served via the backing store."""
    backing = Backing()
    kv = KV(backing, capacity=2)
    kv.set("a", 1)
    kv.set("b", 2)
    kv.set("c", 3)                   # write-through; cache evicts the LRU "a"
    # All three remain retrievable because writes went through to the backing.
    assert kv.get("a") == 1
    assert kv.get("b") == 2
    assert kv.get("c") == 3


def test_miss_sentinel_semantics():
    """MISS is a sentinel distinct from None; get() returns it for an uncached key."""
    assert MISS is not None
    cache = LRU(capacity=2)
    assert cache.get("absent") is MISS
    cache.put("k", None)             # legitimately cache a None value
    assert cache.get("k") is None    # a cached None is NOT a miss
    assert cache.get("k") is not MISS


def test_invalidate_drops_key():
    """invalidate removes a cached key; a later get is a miss."""
    cache = LRU(capacity=4)
    cache.put("k", 7)
    assert cache.get("k") == 7
    cache.invalidate("k")
    assert cache.get("k") is MISS
    cache.invalidate("k")            # invalidating an absent key is a no-op


# ===========================================================================
# FAIL_TO_PASS tests — existing-key overwrite (broken variant fails these)
# ===========================================================================

def test_update_existing_key_via_set():
    """Overwriting an existing key via kv.set must make kv.get return the NEW value.

    SYMPTOM of the planted bug: the cache keeps serving the stale value because
    LRU.put returns early on an existing key without overwriting it.
    """
    kv = KV(Backing(), capacity=4)
    kv.set("k", 1)
    assert kv.get("k") == 1
    kv.set("k", 2)                   # overwrite existing key (write-through)
    assert kv.get("k") == 2, "kv.get must reflect the latest write, not the stale value"


def test_repeated_updates_reflect_latest():
    """Repeated overwrites of the same key always reflect the most recent write."""
    kv = KV(Backing(), capacity=4)
    for v in (10, 20, 30, 40, 50):
        kv.set("counter", v)
        assert kv.get("counter") == v, f"expected {v} after writing it"
    assert kv.get("counter") == 50


def test_cache_put_overwrites_existing():
    """LRU.put on an existing key overwrites its stored value (root-cause check)."""
    cache = LRU(capacity=4)
    cache.put("x", "old")
    assert cache.get("x") == "old"
    cache.put("x", "new")            # existing key -> overwrite
    assert cache.get("x") == "new", "LRU.put must overwrite an existing key's value"


# ===========================================================================
# Advisory code quality
# ===========================================================================

@pytest.mark.code_quality
def test_code_quality_report():
    """Advisory only — never asserted as pass/fail."""
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
