"""Grader for harness/h08_txnkv. Tests the PUBLIC contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS on the broken reference.

The broken reference's ``rollback_to(name)`` (a) discards the savepoint ``name``
itself, so a second ``rollback_to(name)`` raises, and (b) fails to undo a
delete-tombstone created after the savepoint. Basic set/get/delete/keys/TTL and
the begin/commit/rollback machinery are identical to the gold, so only the
savepoint-reuse and tombstone-undo tests fail on the broken variant.

Every test is granular (one behavior / interaction each) so per-behavior partial
credit is meaningful. Expected values are hand-written — the gold is never
imported here.
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "harness", "h08_txnkv"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

Store = getattr(gu.load_module(SOL, "solution.py"), "Store")


def make() -> "Store":
    return Store()


# ===========================================================================
# Clock & basic CRUD
# ===========================================================================
def test_initial_clock_is_zero():
    assert make().now() == 0


def test_tick_advances_clock():
    s = make()
    s.tick(3)
    assert s.now() == 3
    s.tick(0)
    assert s.now() == 3
    s.tick(7)
    assert s.now() == 10


def test_set_then_get():
    s = make()
    s.set("a", "1")
    assert s.get("a") == "1"


def test_get_absent_key_is_none():
    assert make().get("missing") is None


def test_set_overwrites_value():
    s = make()
    s.set("a", "1")
    s.set("a", "2")
    assert s.get("a") == "2"


def test_delete_present_returns_true_and_removes():
    s = make()
    s.set("a", "1")
    assert s.delete("a") is True
    assert s.get("a") is None


def test_delete_absent_returns_false():
    s = make()
    assert s.delete("nope") is False


def test_delete_return_is_strict_bool():
    s = make()
    s.set("a", "1")
    r = s.delete("a")
    assert r is True and isinstance(r, bool)
    r2 = s.delete("a")
    assert r2 is False and isinstance(r2, bool)


# ===========================================================================
# keys() / prefix scan
# ===========================================================================
def test_keys_sorted_no_prefix():
    s = make()
    for k in ["banana", "apple", "cherry", "apricot"]:
        s.set(k, "1")
    assert s.keys() == ["apple", "apricot", "banana", "cherry"]


def test_keys_prefix_filter_sorted():
    s = make()
    for k in ["banana", "apple", "cherry", "apricot"]:
        s.set(k, "1")
    assert s.keys("ap") == ["apple", "apricot"]


def test_keys_empty_store():
    assert make().keys() == []
    assert make().keys("x") == []


def test_keys_excludes_deleted():
    s = make()
    s.set("a", "1")
    s.set("ab", "2")
    s.delete("a")
    assert s.keys() == ["ab"]


# ===========================================================================
# TTL
# ===========================================================================
def test_ttl_visible_before_expiry():
    s = make()
    s.set("t", "v", ttl=5)
    assert s.get("t") == "v"
    s.tick(4)
    assert s.get("t") == "v"


def test_ttl_expires_when_now_ge_expiry():
    s = make()
    s.set("t", "v", ttl=5)
    s.tick(5)  # now == expiry -> expired (>=)
    assert s.get("t") is None


def test_ttl_expired_excluded_from_keys():
    s = make()
    s.set("keep", "v")
    s.set("temp", "v", ttl=2)
    s.tick(2)
    assert s.keys() == ["keep"]


def test_ttl_none_clears_prior_expiry():
    s = make()
    s.set("t", "v", ttl=3)
    s.set("t", "v2")  # ttl=None must clear the expiry
    s.tick(1000)
    assert s.get("t") == "v2"


def test_ttl_reset_extends_with_current_clock():
    s = make()
    s.set("t", "v", ttl=2)
    s.tick(1)              # now=1, expiry still 2
    s.set("t", "v2", ttl=5)  # now=1 -> new expiry 6
    s.tick(4)              # now=5 < 6
    assert s.get("t") == "v2"
    s.tick(1)              # now=6 >= 6
    assert s.get("t") is None


def test_delete_of_expired_key_returns_false():
    s = make()
    s.set("t", "v", ttl=2)
    s.tick(2)
    assert s.delete("t") is False


# ===========================================================================
# Transactions: begin / commit / rollback (incl. nesting)
# ===========================================================================
def test_buffered_write_visible_in_txn():
    s = make()
    s.set("a", "1")
    s.begin()
    s.set("a", "2")
    assert s.get("a") == "2"


def test_commit_merges_into_committed():
    s = make()
    s.begin()
    s.set("a", "1")
    s.commit()
    assert s.get("a") == "1"
    # after commit there is no active txn; a plain set goes to committed store
    s.set("b", "2")
    assert s.get("b") == "2"


def test_rollback_discards_buffered_writes():
    s = make()
    s.set("a", "1")
    s.begin()
    s.set("a", "2")
    s.set("b", "3")
    s.rollback()
    assert s.get("a") == "1"
    assert s.get("b") is None


def test_nested_commit_merges_into_parent_frame():
    s = make()
    s.set("a", "1")
    s.begin()            # F1
    s.set("a", "2")
    s.begin()            # F2
    s.set("a", "3")
    s.set("b", "x")
    assert s.get("a") == "3"
    s.commit()           # F2 -> F1
    assert s.get("a") == "3"
    assert s.get("b") == "x"
    # not yet committed to the store: rolling back F1 reverts to committed.
    s.rollback()
    assert s.get("a") == "1"
    assert s.get("b") is None


def test_nested_commit_then_outer_commit_persists():
    s = make()
    s.begin()
    s.set("a", "1")
    s.begin()
    s.set("a", "2")
    s.commit()  # inner -> outer
    s.commit()  # outer -> committed
    assert s.get("a") == "2"


def test_keys_reflects_txn_overlay():
    s = make()
    s.set("a", "1")
    s.begin()
    s.set("b", "2")
    s.delete("a")
    assert s.keys() == ["b"]
    s.rollback()
    assert s.keys() == ["a"]


# ===========================================================================
# Delete tombstone semantics inside a transaction
# ===========================================================================
def test_delete_in_txn_shadows_committed():
    s = make()
    s.set("a", "1")
    s.begin()
    assert s.delete("a") is True
    assert s.get("a") is None  # tombstone within the frame


def test_delete_tombstone_undone_by_rollback():
    s = make()
    s.set("a", "1")
    s.begin()
    s.delete("a")
    s.rollback()
    assert s.get("a") == "1"  # committed value restored


def test_delete_tombstone_merges_on_commit():
    s = make()
    s.set("a", "1")
    s.begin()
    s.delete("a")
    s.commit()
    assert s.get("a") is None  # delete persisted to committed store


# ===========================================================================
# Savepoints: rollback_to / release
# ===========================================================================
def test_rollback_to_undoes_writes_since_savepoint():
    s = make()
    s.set("k", "base")
    s.begin()
    s.set("k", "v1")
    s.savepoint("sp")
    s.set("k", "v2")
    s.rollback_to("sp")
    assert s.get("k") == "v1"


def test_rollback_to_keeps_transaction_open():
    s = make()
    s.begin()
    s.set("k", "v1")
    s.savepoint("sp")
    s.set("k", "v2")
    s.rollback_to("sp")
    # txn still open: a further write is buffered, and commit is required to
    # persist. A spurious extra commit/rollback would raise; here it must not.
    s.set("m", "n")
    s.commit()
    assert s.get("k") == "v1"
    assert s.get("m") == "n"


def test_rollback_to_is_reusable_FAIL_TO_PASS():
    """A second rollback_to(name) must still work — the savepoint is kept.

    The broken variant discards the savepoint on the first rollback_to, so the
    second one raises ValueError.
    """
    s = make()
    s.begin()
    s.set("k", "v1")
    s.savepoint("sp")
    s.set("k", "v2")
    s.rollback_to("sp")
    assert s.get("k") == "v1"
    s.set("k", "v3")
    s.rollback_to("sp")  # must NOT raise; sp is still valid
    assert s.get("k") == "v1"


def test_delete_tombstone_undone_by_rollback_to_FAIL_TO_PASS():
    """A delete made after a savepoint must be undone by rollback_to.

    The broken variant leaves the tombstone in place, so the key stays absent.
    """
    s = make()
    s.set("d", "present")
    s.begin()
    s.savepoint("sp")
    assert s.delete("d") is True
    assert s.get("d") is None
    s.rollback_to("sp")
    assert s.get("d") == "present"


def test_rollback_to_only_undoes_after_savepoint():
    s = make()
    s.begin()
    s.set("a", "before")
    s.savepoint("sp")
    s.set("b", "after")
    s.rollback_to("sp")
    assert s.get("a") == "before"  # write before sp survives
    assert s.get("b") is None       # write after sp undone


def test_savepoint_rewrite_moves_position():
    s = make()
    s.begin()
    s.set("k", "v1")
    s.savepoint("sp")
    s.set("k", "v2")
    s.savepoint("sp")   # re-mark moves sp to "now"
    s.set("k", "v3")
    s.rollback_to("sp")
    assert s.get("k") == "v2"  # only the write after the moved sp is undone


def test_rollback_to_discards_later_savepoints():
    s = make()
    s.begin()
    s.savepoint("a")
    s.set("k", "v1")
    s.savepoint("b")
    s.set("k", "v2")
    s.rollback_to("a")  # discards savepoint b
    assert s.get("k") is None
    with pytest.raises(ValueError):
        s.rollback_to("b")


def test_rollback_to_keeps_earlier_savepoints():
    s = make()
    s.begin()
    s.set("k", "v0")
    s.savepoint("a")
    s.set("k", "v1")
    s.savepoint("b")
    s.set("k", "v2")
    s.rollback_to("b")
    assert s.get("k") == "v1"
    s.rollback_to("a")  # earlier savepoint still valid
    assert s.get("k") == "v0"


def test_release_forgets_without_undo():
    s = make()
    s.begin()
    s.set("x", "1")
    s.savepoint("sp")
    s.set("x", "2")
    s.release("sp")
    assert s.get("x") == "2"  # writes kept
    with pytest.raises(ValueError):
        s.rollback_to("sp")    # sp forgotten


def test_release_drops_later_savepoints():
    s = make()
    s.begin()
    s.savepoint("a")
    s.savepoint("b")
    s.release("a")  # drops a and b
    with pytest.raises(ValueError):
        s.rollback_to("b")


def test_savepoints_are_per_frame():
    s = make()
    s.begin()
    s.savepoint("sp")
    s.begin()  # inner frame has no savepoints
    with pytest.raises(ValueError):
        s.rollback_to("sp")


# ===========================================================================
# TTL x transactions
# ===========================================================================
def test_ttl_set_in_txn_then_commit_evaluated_by_clock():
    s = make()
    s.begin()
    s.set("e", "v", ttl=3)  # now=0 -> absolute expiry 3
    s.commit()
    assert s.get("e") == "v"
    s.tick(3)
    assert s.get("e") is None  # evaluated at access, not at commit


def test_ttl_set_in_txn_discarded_on_rollback():
    s = make()
    s.set("e", "old")
    s.begin()
    s.set("e", "new", ttl=10)
    s.rollback()
    assert s.get("e") == "old"  # buffered ttl write discarded


def test_ttl_buffered_expiry_visible_in_txn():
    s = make()
    s.begin()
    s.set("e", "v", ttl=2)
    assert s.get("e") == "v"
    s.tick(2)
    assert s.get("e") is None  # expires even while still buffered


# ===========================================================================
# Exception contract (assert TYPES)
# ===========================================================================
def test_tick_negative_raises():
    with pytest.raises(ValueError):
        make().tick(-1)


def test_set_ttl_zero_or_negative_raises():
    s = make()
    with pytest.raises(ValueError):
        s.set("a", "1", ttl=0)
    with pytest.raises(ValueError):
        s.set("a", "1", ttl=-5)


def test_commit_without_txn_raises():
    with pytest.raises(ValueError):
        make().commit()


def test_rollback_without_txn_raises():
    with pytest.raises(ValueError):
        make().rollback()


def test_savepoint_without_txn_raises():
    with pytest.raises(ValueError):
        make().savepoint("sp")


def test_rollback_to_without_txn_raises():
    with pytest.raises(ValueError):
        make().rollback_to("sp")


def test_release_without_txn_raises():
    with pytest.raises(ValueError):
        make().release("sp")


def test_rollback_to_unknown_name_raises():
    s = make()
    s.begin()
    with pytest.raises(ValueError):
        s.rollback_to("never")


def test_release_unknown_name_raises():
    s = make()
    s.begin()
    with pytest.raises(ValueError):
        s.release("never")


# ===========================================================================
# Advisory: code quality (never asserted as pass/fail)
# ===========================================================================
@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
