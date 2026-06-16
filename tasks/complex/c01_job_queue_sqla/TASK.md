# Complex 01 — `job_queue_sqla`: Priority Job Queue with SQLAlchemy ORM

**Created:** 2026-06-15 · **Category:** complex · **Weight:** 5

Implement a priority job queue backed by SQLAlchemy 2.0 ORM with dependency
resolution. Use **SQLAlchemy 2.0** and the **standard library only** (no other
third-party packages). Structure your solution as multiple modules:

```
models.py       — SQLAlchemy 2.0 ORM Base, Job, and Dependency models
repository.py   — Low-level DB access helpers (session management)
scheduler.py    — Claim/complete/fail logic and dependency checking
queue_api.py    — Public facade (the grader imports THIS file only)
```

Use an in-memory SQLite database (`"sqlite:///:memory:"`) by default — no external
server required.

## Public contract (in `queue_api.py`)

The grader imports `queue_api.py` and uses only these names:

```python
class JobQueue:
    def __init__(self, url: str = "sqlite:///:memory:", max_retries: int = 3) -> None:
        """Create engine, create all ORM tables, ready for use."""
        ...

    def submit(
        self,
        name: str,
        payload: dict | None = None,
        priority: int = 0,
        depends_on: list[int] | None = None,
    ) -> int:
        """Submit a new job; returns the new job's integer id.

        The new job starts with status ``"pending"``.
        ``depends_on`` is a list of job ids that must be ``"done"`` before this
        job is claimable.  An empty list or ``None`` means no dependencies.
        """
        ...

    def claim(self) -> dict | None:
        """Return the highest-priority claimable job and mark it ``"running"``.

        A job is **claimable** iff:
          - its status is ``"pending"``, AND
          - every job listed in its ``depends_on`` has status ``"done"``.

        Tie-breaking when multiple jobs are claimable:
          1. Higher ``priority`` value wins (larger int = higher priority).
          2. Among equal priority, lower ``id`` wins (submission order).

        Returns ``{"id": int, "name": str, "payload": dict|None, "priority": int}``
        or ``None`` if nothing is claimable.
        """
        ...

    def complete(self, job_id: int, result: dict | None = None) -> None:
        """Mark job ``job_id`` as ``"done"`` and store optional ``result`` dict."""
        ...

    def fail(self, job_id: int) -> None:
        """Record a failure attempt for ``job_id``.

        Counting rule (increment **first**, then compare):
          1. Increment ``attempts`` by 1 to count this failure.
          2. If the **new** ``attempts`` value is ``< max_retries``: set status
             back to ``"pending"`` (the job will be retried).
          3. If the **new** ``attempts`` value is ``>= max_retries``: set status
             to ``"failed"`` (permanent).

        Equivalently, ``max_retries`` is the maximum *total* number of attempts.
        Example (``max_retries=3``): the 1st and 2nd ``fail()`` return the job to
        ``"pending"``; the 3rd ``fail()`` marks it ``"failed"``.
        """
        ...

    def status(self, job_id: int) -> str:
        """Return the current status string for ``job_id`` (one of
        ``"pending"``, ``"running"``, ``"done"``, ``"failed"``).
        """
        ...

    def stats(self) -> dict:
        """Return a dict with counts for every status:
        ``{"pending": n, "running": n, "done": n, "failed": n}``.
        All four keys are always present (count is 0 when no jobs have that status).
        """
        ...
```

## Data model requirements

Your `models.py` must define:

- A `Job` table with at least: `id` (PK), `name` (str), `payload` (JSON or Text),
  `priority` (int, default 0), `status` (str, default `"pending"`),
  `attempts` (int, default 0), `result` (JSON or Text, nullable).
- A `Dependency` table (or equivalent) that records `(job_id, depends_on_id)` pairs.

## Notes

- The queue must be instantiated with `JobQueue()` (no args) for testing.
- `payload` and `result` must round-trip through the DB (dict → stored → dict back).
- Determinism: given identical calls, results are identical.
- All status values are lowercase strings: `"pending"`, `"running"`, `"done"`, `"failed"`.
