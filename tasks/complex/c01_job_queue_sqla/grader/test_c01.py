"""Grader for complex/c01_job_queue_sqla.

Tests the public contract only (see TASK.md).  Each test exercises one
aspect of ``JobQueue`` so a partially-correct solution earns partial credit.

Validity invariant:
  PASSES  on the gold reference (all N tests pass).
  FAILS   on the broken reference (>=1 test fails — the dependency tests).
"""
from __future__ import annotations

import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "complex", "c01_job_queue_sqla"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)

# Load the facade module and grab JobQueue — other modules (models, repository,
# scheduler) are imported transitively; the grader never names them directly.
_mod = gu.load_module(SOL, "queue_api.py")
JobQueue = _mod.JobQueue


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fresh_queue(max_retries: int = 3) -> "JobQueue":
    """Return a new in-memory JobQueue instance (fresh DB each call)."""
    return JobQueue(url="sqlite:///:memory:", max_retries=max_retries)


# ---------------------------------------------------------------------------
# Test 1 — submit returns a positive integer id; initial status is "pending"
# ---------------------------------------------------------------------------

def test_submit_returns_id_and_status_pending():
    q = fresh_queue()
    jid = q.submit("task-a")
    assert isinstance(jid, int), "submit() must return an int"
    assert jid > 0, "job id should be positive"
    assert q.status(jid) == "pending", "new job must start as 'pending'"


# ---------------------------------------------------------------------------
# Test 2 — payload round-trips through the DB unchanged
# ---------------------------------------------------------------------------

def test_payload_roundtrip():
    q = fresh_queue()
    payload = {"alpha": 1, "beta": [2, 3], "gamma": None}
    jid = q.submit("payload-job", payload=payload)
    result = q.claim()
    assert result is not None, "claim() must return a dict for a pending job"
    assert result["payload"] == payload, "payload must round-trip unchanged"


# ---------------------------------------------------------------------------
# Test 3 — dependency: first claim returns the prerequisite, not the dependent
# ---------------------------------------------------------------------------

def test_dependency_order_first_claim_is_prereq():
    """Submit A then B depends_on=[A]. First claim must return A, not B."""
    q = fresh_queue()
    a_id = q.submit("job-A")
    b_id = q.submit("job-B", depends_on=[a_id])

    claimed = q.claim()
    assert claimed is not None, "claim() must return a job when one is claimable"
    assert claimed["id"] == a_id, (
        f"Expected job-A (id={a_id}) to be claimed first; "
        f"got id={claimed['id']} — dependency check failed"
    )
    _ = b_id  # referenced to avoid unused-variable warning


# ---------------------------------------------------------------------------
# Test 4 — dependency: after completing prereq, dependent becomes claimable
# ---------------------------------------------------------------------------

def test_dependency_order_second_claim_after_complete():
    """After complete(A), claim() must return B (which depended on A)."""
    q = fresh_queue()
    a_id = q.submit("job-A")
    b_id = q.submit("job-B", depends_on=[a_id])

    first = q.claim()
    assert first is not None
    assert first["id"] == a_id

    # B is still blocked — nothing more should be claimable yet.
    assert q.claim() is None, "B must not be claimable while A is still running"

    q.complete(a_id)
    second = q.claim()
    assert second is not None, "B should be claimable after A is done"
    assert second["id"] == b_id, "B must be returned after A is completed"


# ---------------------------------------------------------------------------
# Test 5 — priority ordering among independent jobs
# ---------------------------------------------------------------------------

def test_priority_ordering():
    """Higher priority wins; lower id breaks ties."""
    q = fresh_queue()
    lo_id = q.submit("low-priority", priority=0)
    hi_id = q.submit("high-priority", priority=10)
    mid_id = q.submit("mid-priority", priority=5)

    first = q.claim()
    assert first is not None
    assert first["id"] == hi_id, "highest-priority job must be claimed first"

    second = q.claim()
    assert second is not None
    assert second["id"] == mid_id

    third = q.claim()
    assert third is not None
    assert third["id"] == lo_id

    _ = lo_id, mid_id  # suppress unused warnings


# ---------------------------------------------------------------------------
# Test 6 — fail() retries until max_retries, then marks "failed"
# ---------------------------------------------------------------------------

def test_fail_retries_then_failed():
    """With max_retries=3, fail() 3 times → 'failed'."""
    q = fresh_queue(max_retries=3)
    jid = q.submit("retry-job")

    # Attempt 1 — should go back to pending (attempts=1 < 3)
    q.claim()
    q.fail(jid)
    assert q.status(jid) == "pending", "after 1st fail, status must be 'pending'"

    # Attempt 2 — should go back to pending (attempts=2 < 3)
    q.claim()
    q.fail(jid)
    assert q.status(jid) == "pending", "after 2nd fail, status must be 'pending'"

    # Attempt 3 — attempts reaches max_retries → 'failed'
    q.claim()
    q.fail(jid)
    assert q.status(jid) == "failed", "after max_retries failures, status must be 'failed'"


# ---------------------------------------------------------------------------
# Test 7 — complete() sets status to "done" and stores result
# ---------------------------------------------------------------------------

def test_complete_stores_result():
    q = fresh_queue()
    jid = q.submit("result-job")
    q.claim()
    result = {"output": 42, "tag": "ok"}
    q.complete(jid, result=result)
    assert q.status(jid) == "done"


# ---------------------------------------------------------------------------
# Test 8 — stats() always returns all four status keys with correct counts
# ---------------------------------------------------------------------------

def test_stats_correctness():
    q = fresh_queue()
    # Empty queue — all zeros.
    s = q.stats()
    assert set(s.keys()) >= {"pending", "running", "done", "failed"}, (
        "stats() must return all four status keys"
    )
    assert all(v == 0 for v in s.values()), "empty queue must have zero counts"

    # Submit two, claim one, complete it.
    jid1 = q.submit("j1")
    jid2 = q.submit("j2")
    q.claim()  # j1 is now running
    q.complete(jid1)

    s = q.stats()
    assert s["done"] == 1, f"expected done=1, got {s['done']}"
    assert s["pending"] == 1, f"expected pending=1, got {s['pending']}"
    assert s["running"] == 0, f"expected running=0, got {s['running']}"
    _ = jid2  # suppress unused


# ---------------------------------------------------------------------------
# Test 9 — claim returns None when nothing is claimable (all blocked/empty)
# ---------------------------------------------------------------------------

def test_claim_none_when_empty():
    q = fresh_queue()
    assert q.claim() is None, "claim() must return None on an empty queue"


# ---------------------------------------------------------------------------
# Test 10 — multiple dependencies: job blocked until ALL prereqs done
# ---------------------------------------------------------------------------

def test_multiple_dependencies_all_must_be_done():
    """Job C depends on both A and B; claimable only when both are done."""
    q = fresh_queue()
    a_id = q.submit("A")
    b_id = q.submit("B")
    c_id = q.submit("C", depends_on=[a_id, b_id])

    # Claim and complete A.
    ca = q.claim()
    assert ca["id"] == a_id
    q.complete(a_id)

    # C is still blocked (B not done).
    cb = q.claim()
    assert cb is not None
    assert cb["id"] == b_id, "B should be claimable now (no deps)"
    # Don't complete B yet — C must still be blocked.
    assert q.claim() is None, "C must be blocked while B is still running"

    q.complete(b_id)

    # Now C is claimable.
    cc = q.claim()
    assert cc is not None
    assert cc["id"] == c_id, "C must become claimable once both A and B are done"


# ---------------------------------------------------------------------------
# Test 11 — tie-break by lower id among equal priority
# ---------------------------------------------------------------------------

def test_tiebreak_lower_id_wins():
    q = fresh_queue()
    id1 = q.submit("first", priority=5)
    id2 = q.submit("second", priority=5)
    id3 = q.submit("third", priority=5)

    first_claim = q.claim()
    assert first_claim["id"] == id1, "lowest id wins among equal priority"

    second_claim = q.claim()
    assert second_claim["id"] == id2

    third_claim = q.claim()
    assert third_claim["id"] == id3


# ---------------------------------------------------------------------------
# Test 12 — submit with no payload stores None; claim returns None payload
# ---------------------------------------------------------------------------

def test_no_payload_is_none():
    q = fresh_queue()
    jid = q.submit("no-payload-job")
    claimed = q.claim()
    assert claimed is not None
    assert claimed["payload"] is None, "absent payload must come back as None"
    _ = jid


# ---------------------------------------------------------------------------
# Advisory code-quality test (never asserted, just reported)
# ---------------------------------------------------------------------------

@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)
