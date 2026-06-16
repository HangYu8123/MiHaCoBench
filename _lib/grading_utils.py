"""HarnessFlow PyBench — shared grading utilities.

Every task grader imports from this module so that solution resolution, isolation,
import-by-path, timeouts, complexity estimation, plot validation, artifact
provenance, and the advisory code-quality report are implemented **once** and
behave identically across all 79 tasks.

Design decisions (grounded in the Step-3 challenge + research):

* **Solution resolution & isolation.** A grader never hard-codes the path to the
  code under test. It calls :func:`resolve_solution_dir`, which honours the
  ``PYBENCH_SOLUTION_DIR`` / ``PYBENCH_CANDIDATE_ROOT`` / ``PYBENCH_VARIANT``
  environment contract and otherwise defaults to the *gold* reference under
  ``benchmark/_solutions/`` — a tree that is deliberately **separate** from the
  task directory the agent under test is shown.

* **Import by file path.** :func:`load_module` uses
  ``importlib.util.spec_from_file_location`` so the candidate's internal module
  names/structure do not matter — only the public contract in ``TASK.md``.

* **Complexity is gated by feasibility, not by a stopwatch.** The robust,
  non-flaky way to reject a wrong Big-O is a large adversarial input under a
  tight timeout (see :func:`time_limit` / :func:`run_within`). The empirical
  curve fit (:func:`estimate_time_complexity`) is a *soft* signal only.

* **Readability is advisory.** :func:`code_quality_report` returns objective
  AST-derived proxies; it is never a pass/fail gate.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
import os
import signal
import subprocess
import sys
import threading
import time
import tracemalloc
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

# benchmark/ root (parent of _lib/)
PYBENCH_ROOT = Path(__file__).resolve().parents[1]
GOLD_ROOT = PYBENCH_ROOT / "_solutions"

# Per-category default grader time budgets (seconds). See RUBRIC.md.
TIME_BUDGETS = {
    "easy": 30,
    "complex": 120,
    "data_analysis": 90,
    "algorithmic": 30,
    "long_horizon": 15,  # per step
    "ml": 120,
    "debug": 30,
    "swe_bench": 60,      # multi-file fault-localization mini-repos (SWE-bench style)
    "compositional": 60,  # multi-library composition (BigCodeBench style)
    "competitive": 30,    # contest-level; tight gate so wrong complexity times out (LiveCodeBench/APPS style)
}


# --------------------------------------------------------------------------- #
# Solution resolution & isolation
# --------------------------------------------------------------------------- #
def resolve_solution_dir(category: str, task_id: str) -> Path:
    """Return the directory holding the code under test for ``<category>/<task_id>``.

    Resolution order:

    1. ``PYBENCH_SOLUTION_DIR`` — an absolute path to the solution for *this*
       task (single-task mode). Must not live inside ``benchmark/tasks/`` (that
       would mean the candidate could read the grader/spec — an isolation
       violation), unless it is the gold tree under ``_solutions``.
    2. ``PYBENCH_CANDIDATE_ROOT`` — a root containing ``<category>/<task_id>/``.
    3. Default: the gold reference under ``benchmark/_solutions``. When
       ``PYBENCH_VARIANT=broken`` the deliberately-broken gold variant
       (``<task_id>__broken``) is used instead — this is how the runner proves a
       grader actually discriminates.
    """
    direct = os.environ.get("PYBENCH_SOLUTION_DIR")
    if direct:
        p = Path(direct).resolve()
        tasks_root = (PYBENCH_ROOT / "tasks").resolve()
        if tasks_root in p.parents or p == tasks_root:
            raise RuntimeError(
                f"PYBENCH_SOLUTION_DIR ({p}) is inside the task tree — isolation "
                "violation: candidate solutions must live outside benchmark/tasks/."
            )
        return p

    root_env = os.environ.get("PYBENCH_CANDIDATE_ROOT")
    if root_env:
        return (Path(root_env).resolve() / category / task_id)

    variant = os.environ.get("PYBENCH_VARIANT", "").strip().lower()
    name = f"{task_id}__broken" if variant == "broken" else task_id
    return GOLD_ROOT / category / name


def require_solution_dir(category: str, task_id: str) -> Path:
    """Like :func:`resolve_solution_dir` but fail loudly if it does not exist."""
    d = resolve_solution_dir(category, task_id)
    if not d.is_dir():
        raise FileNotFoundError(
            f"solution dir for {category}/{task_id} not found: {d}\n"
            "Set PYBENCH_SOLUTION_DIR or PYBENCH_CANDIDATE_ROOT, or implement the "
            "gold reference under benchmark/_solutions/."
        )
    return d


# --------------------------------------------------------------------------- #
# Import-by-path
# --------------------------------------------------------------------------- #
def load_module(solution_dir: Path | str, module_filename: str, alias: str | None = None):
    """Import ``module_filename`` (e.g. ``"solution.py"``) from ``solution_dir``.

    ``solution_dir`` is prepended to ``sys.path`` so intra-package relative-ish
    imports (``import models``) inside a multi-file solution resolve. The module
    is registered in ``sys.modules`` under ``alias`` (default: the file stem) so
    that dataclasses / pickling behave.
    """
    solution_dir = Path(solution_dir).resolve()
    path = solution_dir / module_filename
    if not path.exists():
        raise FileNotFoundError(f"required module '{module_filename}' missing in {solution_dir}")
    if str(solution_dir) not in sys.path:
        sys.path.insert(0, str(solution_dir))
    name = alias or path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot build import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_cli(solution_dir: Path | str, args: Sequence[Any], timeout: float = 60,
            entry: str = "solution.py", env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run ``python <entry> <args...>`` with ``cwd=solution_dir`` in a subprocess.

    Always sets ``MPLBACKEND=Agg`` (headless plotting) and ``PYTHONHASHSEED=0``
    (determinism). Returns the ``CompletedProcess`` (check ``.returncode`` /
    ``.stdout`` / ``.stderr`` in the grader).
    """
    solution_dir = Path(solution_dir).resolve()
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONHASHSEED="0")
    if env_extra:
        env.update(env_extra)
    cmd = [sys.executable, entry, *[str(a) for a in args]]
    return subprocess.run(cmd, cwd=str(solution_dir), env=env,
                          capture_output=True, text=True, timeout=timeout)


def load_callable(solution_dir: Path | str, module_filename: str, name: str) -> Callable:
    """Import ``module_filename`` and return its attribute ``name`` (must be callable)."""
    module = load_module(solution_dir, module_filename)
    if not hasattr(module, name):
        raise AttributeError(f"{module_filename} does not define required name '{name}'")
    obj = getattr(module, name)
    if not callable(obj):
        raise TypeError(f"'{name}' in {module_filename} is not callable")
    return obj


# --------------------------------------------------------------------------- #
# Timeouts (the real complexity gate)
# --------------------------------------------------------------------------- #
class TimeoutExceeded(Exception):
    """Raised when a guarded block exceeds its wall-clock budget."""


def _async_raise(target_tid: int, exc_type: type) -> bool:
    """Inject ``exc_type`` into the thread whose id is ``target_tid`` (CPython).

    Returns True iff exactly one thread state was modified. Used by the
    non-SIGALRM fallback of :func:`time_limit`. A CPython *asynchronous*
    exception is delivered only between bytecode instructions, so it interrupts
    pure-Python runaway loops (the wrong-Big-O case) but cannot pre-empt a single
    long call that sits inside a C extension.
    """
    import ctypes
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_ulong(target_tid), ctypes.py_object(exc_type))
    if res > 1:  # pragma: no cover - defensive: never leave >1 thread injected
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(target_tid), None)
    return res == 1


def _sigalrm_gate_available() -> bool:
    """True when :func:`time_limit` can use SIGALRM (POSIX, main thread)."""
    return hasattr(signal, "setitimer") and threading.current_thread() is threading.main_thread()


def complexity_gate_mechanism() -> str:
    """How :func:`time_limit` will enforce a budget on this platform *right now*.

    * ``"sigalrm"`` — hard wall-clock gate (POSIX main thread); can interrupt
      anything, including time spent in C code.
    * ``"thread-watchdog"`` — portable fallback; interrupts pure-Python runaway
      loops only (cannot pre-empt a long call inside a C extension).
    * ``"none"`` — no enforcement available (a wrong-complexity solution is not
      rejected); only on an interpreter without ``ctypes`` and without SIGALRM.

    Surfaced by ``run_benchmark.py --preflight`` so an unsound platform is loud,
    not silent.
    """
    if _sigalrm_gate_available():
        return "sigalrm"
    try:
        import ctypes  # noqa: F401
    except Exception:  # pragma: no cover - interpreter without ctypes
        return "none"
    return "thread-watchdog"


@contextmanager
def time_limit(seconds: float):
    """Wall-clock guard for in-process calls — the *hard* complexity gate.

    An asymptotically-wrong solution blows the budget on a large adversarial
    input and is rejected, while constant factors are irrelevant because the
    input is large enough to dominate them.

    On a POSIX main thread this uses ``SIGALRM`` and can interrupt anything,
    including time spent in C code. Where SIGALRM is unavailable — Windows, or
    any non-main-thread caller — it falls back to a watchdog thread that injects
    :class:`TimeoutExceeded` into the calling thread (see :func:`_async_raise`):
    that interrupts pure-Python runaway loops (the wrong-Big-O case) but cannot
    pre-empt a single long call inside a C extension, and if even that is
    unavailable it warns loudly rather than silently not enforcing. Prefer a
    POSIX main-thread run for the strongest gate; see
    :func:`complexity_gate_mechanism`.
    """
    if seconds <= 0:
        yield
        return

    if _sigalrm_gate_available():
        def _handler(signum, frame):  # noqa: ARG001
            raise TimeoutExceeded(f"exceeded {seconds:g}s time budget")

        prev_timer = signal.getitimer(signal.ITIMER_REAL)  # (value, interval); value>0 => outer timer armed
        old_handler = signal.signal(signal.SIGALRM, _handler)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            yield
        finally:
            signal.signal(signal.SIGALRM, old_handler)
            # Restore any outer timer instead of blindly zeroing it, so a nested
            # time_limit cannot silently disable an enclosing one.
            if prev_timer[0] > 0:
                signal.setitimer(signal.ITIMER_REAL, prev_timer[0], prev_timer[1])
            else:
                signal.setitimer(signal.ITIMER_REAL, 0)
        return

    # --- Portable fallback: no SIGALRM (Windows or non-main-thread caller) --- #
    try:
        import ctypes  # noqa: F401
    except Exception:  # pragma: no cover - exotic interpreter without ctypes
        warnings.warn(
            "time_limit: neither SIGALRM nor ctypes is available — the complexity "
            "gate is NOT enforced here; a wrong-complexity solution will not time out.",
            RuntimeWarning, stacklevel=2)
        yield
        return

    target_tid = threading.get_ident()
    fired = threading.Event()

    def _interrupt():
        fired.set()
        _async_raise(target_tid, TimeoutExceeded)

    timer = threading.Timer(seconds, _interrupt)
    timer.daemon = True
    timer.start()
    try:
        yield
    finally:
        timer.cancel()
        # If the watchdog fired right at the boundary, clear any async exception
        # still pending in this thread so it cannot leak past the guarded block.
        if fired.is_set():
            try:
                import ctypes
                ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(target_tid), None)
            except Exception:  # pragma: no cover
                pass


def run_within(seconds: float, fn: Callable, *args, **kwargs):
    """Call ``fn(*args, **kwargs)`` under a :func:`time_limit`. Returns its result."""
    with time_limit(seconds):
        return fn(*args, **kwargs)


# --------------------------------------------------------------------------- #
# Empirical complexity estimation (SOFT signal only)
# --------------------------------------------------------------------------- #
COMPLEXITY_ORDER: list[str] = [
    "O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n^2)", "O(n^3)", "O(2^n)",
]

_COMPLEXITY_FUNCS: dict[str, Callable[[float], float]] = {
    "O(1)": lambda n: 1.0,
    "O(log n)": lambda n: math.log2(max(n, 2)),
    "O(n)": lambda n: n,
    "O(n log n)": lambda n: n * math.log2(max(n, 2)),
    "O(n^2)": lambda n: n * n,
    "O(n^3)": lambda n: n ** 3,
    "O(2^n)": lambda n: 2.0 ** min(n, 30),
}


def measure_runtime(make_input: Callable[[int], Any],
                    run: Callable[[Any], Any],
                    sizes: Sequence[int],
                    repeats: int = 3) -> dict[int, float]:
    """Return ``{n: best_of_repeats_seconds}`` for ``run(make_input(n))``.

    ``make_input`` is called *outside* the timed region; only ``run`` is timed.
    The minimum across repeats is used to suppress OS jitter.
    """
    out: dict[int, float] = {}
    for n in sizes:
        best = math.inf
        for _ in range(max(1, repeats)):
            payload = make_input(n)  # rebuild each repeat so a run() that mutates its
            t0 = time.perf_counter()  # input cannot make later repeats artificially fast
            run(payload)
            best = min(best, time.perf_counter() - t0)
        out[n] = best
    return out


def _fit_residual(sizes: Sequence[float], times: Sequence[float], f: Callable[[float], float]) -> float:
    """Normalised residual of fitting ``times ~ a * f(n)`` with a >= 0 (1-param LSQ)."""
    fs = [f(n) for n in sizes]
    denom = sum(v * v for v in fs)
    if denom == 0:
        return math.inf
    a = sum(t * v for t, v in zip(times, fs)) / denom
    if a < 0:
        a = 0.0
    ss_res = sum((t - a * v) ** 2 for t, v in zip(times, fs))
    ss_tot = sum((t - (sum(times) / len(times))) ** 2 for t in times) or 1e-30
    return ss_res / ss_tot


def estimate_time_complexity(timings: dict[int, float],
                             simplicity_bias: float = 0.15,
                             reliable_residual: float = 0.1) -> dict[str, Any]:
    """Fit measured ``{n: seconds}`` against each complexity class.

    Returns ``{"label", "residuals", "ranked", "reliable"}``. Residuals are
    normalised (0 = perfect fit, ~1 = no better than the mean). The simplicity
    bias is a *multiplicative* window around the best residual, so for a clean
    fit (best ≈ 0) it is tight and distinguishes adjacent classes, while for a
    poor/noisy fit the label is inherently untrustworthy — which is exactly when
    ``reliable`` is False (best residual exceeds ``reliable_residual``, or every
    timing is below timer resolution). **Soft signal only** — never gate on this.
    """
    sizes = sorted(timings)
    times = [timings[n] for n in sizes]
    if not times or max(times) <= 0:
        return {"label": "O(1)", "residuals": {}, "ranked": list(COMPLEXITY_ORDER), "reliable": False}
    residuals = {label: _fit_residual(sizes, times, f) for label, f in _COMPLEXITY_FUNCS.items()}
    best = min(residuals.values())
    candidates = [c for c in COMPLEXITY_ORDER if residuals[c] <= best * (1.0 + simplicity_bias)]
    label = candidates[0] if candidates else min(residuals, key=residuals.get)
    ranked = sorted(residuals, key=residuals.get)
    return {"label": label, "residuals": residuals, "ranked": ranked,
            "reliable": best <= reliable_residual}


def within_one_tier(measured_label: str, target_label: str) -> bool:
    """True if ``measured`` is no worse than one complexity tier above ``target``."""
    return COMPLEXITY_ORDER.index(measured_label) <= COMPLEXITY_ORDER.index(target_label) + 1


def measure_peak_memory(fn: Callable, *args, **kwargs) -> int:
    """Peak heap bytes allocated during ``fn(*args, **kwargs)`` via ``tracemalloc``.

    Leaves any tracing session the caller already started intact (only stops
    tracing if this call started it), and resets the peak so the measurement
    reflects ``fn`` alone.
    """
    was_tracing = tracemalloc.is_tracing()
    if not was_tracing:
        tracemalloc.start()
    tracemalloc.reset_peak()
    try:
        fn(*args, **kwargs)
        _, peak = tracemalloc.get_traced_memory()
        return int(peak)
    finally:
        if not was_tracing:
            tracemalloc.stop()


# --------------------------------------------------------------------------- #
# Plot / artifact validation
# --------------------------------------------------------------------------- #
def png_is_valid(path: Path | str, min_bytes: int = 3000, require_variation: bool = True) -> bool:
    """True if ``path`` is a non-trivial PNG: opens, has size, and (optionally)
    has real visual variation (not a single flat colour)."""
    path = Path(path)
    if not path.exists() or path.stat().st_size < min_bytes:
        return False
    try:
        from PIL import Image  # local import: Pillow is a grader-only dep
    except Exception:  # pragma: no cover
        return path.stat().st_size >= min_bytes
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            if not require_variation:
                return True
            extrema = im.convert("RGB").getextrema()
            return any(lo != hi for lo, hi in extrema)
    except Exception:
        return False


def count_valid_pngs(directory: Path | str, **kwargs) -> int:
    """Number of valid PNGs directly under ``directory``."""
    directory = Path(directory)
    return sum(1 for p in directory.glob("*.png") if png_is_valid(p, **kwargs))


# --------------------------------------------------------------------------- #
# Provenance helpers (long-horizon cascade enforcement)
# --------------------------------------------------------------------------- #
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    """Deterministic JSON encoding for provenance hashing of step artifacts."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_provenance_chain(solution_dir: Path | str, input_file: Path | str, n_steps: int,
                         out_dir: Path | str, timeout_per_step: float = 15,
                         entry: str = "solution.py") -> list[dict]:
    """Drive a long-horizon CLI chain and verify the provenance links.

    For ``k`` in ``1..n_steps`` runs
    ``python <entry> --step k --in <prev> --out <out_dir>/stepK.json`` where
    ``<prev>`` is ``input_file`` for step 1 and the previous step's artifact
    afterwards. Each step is expected to write JSON of the shape
    ``{"step": k, "data": <result>, "provenance": <sha256 of the file it read>}``.

    The candidate's *own* step ``k-1`` output is fed into step ``k`` (so an error
    cascades), and ``provenance`` is checked against the SHA-256 of the consumed
    file (so re-implementing earlier steps from scratch cannot fake the link).

    Returns one record per attempted step:
    ``{"step", "ran", "prov_ok", "data", "err"}``. The chain stops at the first
    step that fails to produce a readable artifact.
    """
    results: list[dict] = []
    prev = Path(input_file)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for k in range(1, n_steps + 1):
        out = out_dir / f"step{k}.json"
        try:
            proc = run_cli(solution_dir, ["--step", k, "--in", str(prev), "--out", str(out)],
                           timeout=timeout_per_step, entry=entry)
        except subprocess.TimeoutExpired:
            results.append({"step": k, "ran": False, "prov_ok": False, "data": None, "err": "timeout"})
            break
        if proc.returncode != 0 or not out.exists():
            results.append({"step": k, "ran": False, "prov_ok": False, "data": None,
                            "err": (proc.stderr or proc.stdout or "")[-300:]})
            break
        try:
            j = json.loads(out.read_text())
        except Exception as exc:  # noqa: BLE001
            results.append({"step": k, "ran": False, "prov_ok": False, "data": None, "err": str(exc)})
            break
        prov_ok = j.get("provenance") == sha256_file(prev)
        results.append({"step": k, "ran": True, "prov_ok": prov_ok, "data": j.get("data"), "err": None})
        prev = out
    return results


# --------------------------------------------------------------------------- #
# Numeric comparison helper
# --------------------------------------------------------------------------- #
def close(actual: float, expected: float, rtol: float = 1e-4, atol: float = 1e-8) -> bool:
    """Scalar approximate equality (numpy-free, safe for plain floats).

    Exact equality short-circuits (so ``inf == inf`` is close); any other
    non-finite operand is never close (``nan``, or mismatched ``inf``).
    """
    a, e = float(actual), float(expected)
    if a == e:
        return True
    if math.isnan(a) or math.isnan(e) or math.isinf(a) or math.isinf(e):
        return False
    return abs(a - e) <= atol + rtol * abs(e)


# --------------------------------------------------------------------------- #
# Surface-form constraints (DS-1000 style)
# --------------------------------------------------------------------------- #
def source_uses(solution_dir: Path | str, needles: Iterable[str],
                module_glob: str = "*.py") -> dict[str, bool]:
    """Return ``{needle: present}`` — whether each substring appears in any source
    file of the solution. Used to require the *intended* statistical/library call
    (e.g. ``scipy.stats.ttest_ind``) rather than a hand-rolled approximation."""
    text = "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                     for p in Path(solution_dir).rglob(module_glob))
    return {needle: (needle in text) for needle in needles}


# --------------------------------------------------------------------------- #
# Advisory code-quality report (NEVER a pass/fail gate)
# --------------------------------------------------------------------------- #
def _cyclomatic_complexity(node: ast.AST) -> int:
    """Approximate McCabe complexity: 1 + branch/loop/boolean decision points."""
    count = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While,
                              ast.ExceptHandler, ast.With, ast.AsyncWith, ast.Assert)):
            count += 1
        elif isinstance(child, ast.BoolOp):
            count += len(child.values) - 1
        elif isinstance(child, ast.comprehension):
            count += 1 + len(child.ifs)
        elif isinstance(child, ast.IfExp):
            count += 1
        elif isinstance(child, (ast.Match,)):
            count += 1
    return count


def code_quality_report(path_or_dir: Path | str) -> dict[str, Any]:
    """Objective, deterministic code-quality proxies (advisory only).

    Returns docstring coverage, function-length stats, naming conformance
    (snake_case), max/avg cyclomatic complexity and total SLOC. These *describe*
    a submission; they never decide pass/fail (readability is human-judged).
    """
    path = Path(path_or_dir)
    files = [path] if path.is_file() else sorted(path.rglob("*.py"))
    funcs = 0
    documented = 0
    snake_ok = 0
    lengths: list[int] = []
    complexities: list[int] = []
    sloc = 0
    import re
    snake_re = re.compile(r"^_?[a-z][a-z0-9_]*$")
    for f in files:
        try:
            src = f.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src)
        except Exception:
            continue
        sloc += sum(1 for ln in src.splitlines() if ln.strip() and not ln.strip().startswith("#"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs += 1
                if ast.get_docstring(node):
                    documented += 1
                if snake_re.match(node.name) or node.name.startswith("__"):
                    snake_ok += 1
                if node.end_lineno and node.lineno:
                    lengths.append(node.end_lineno - node.lineno + 1)
                complexities.append(_cyclomatic_complexity(node))
    return {
        "n_functions": funcs,
        "docstring_coverage": round(documented / funcs, 3) if funcs else 0.0,
        "naming_snake_case": round(snake_ok / funcs, 3) if funcs else 0.0,
        "avg_function_len": round(sum(lengths) / len(lengths), 1) if lengths else 0.0,
        "max_function_len": max(lengths) if lengths else 0,
        "avg_cyclomatic": round(sum(complexities) / len(complexities), 2) if complexities else 0.0,
        "max_cyclomatic": max(complexities) if complexities else 0,
        "sloc": sloc,
    }
