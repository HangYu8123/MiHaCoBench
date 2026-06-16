"""Authoring-time toolkit for mutation-seeded, oracle-grounded grader corpora.

This module is **authoring/experiment tooling only** — it is NOT imported by any
grader at grade time. Its job is to GENERATE the committed, hidden corpus files
``tasks/<category>/<task_id>/expected/mutation_corpus.json`` used by the
mutation-based grader tests.

Methodology (EvalPlus / differential + mutation testing):

* **Independent oracle.** The "expected" answer for every corpus input is decided
  by an oracle that does NOT share code with the gold solution — a trusted stdlib/
  third-party engine where one exists (``re`` for wildcard matching, ``jinja2`` for
  templating), otherwise a structurally-different brute force. ``build_corpus``
  asserts ``gold(x) == oracle(x)`` on every kept input, so the corpus also
  *cross-validates the AI-authored gold* against an independent source of truth.

* **Mutation seeding from real wrong solutions.** Candidate wrong solutions come
  from (a) AST mutation operators applied to the gold (ROR / AOR / boolean / int
  ±1) and (b) hand-written "common-mistake" implementations passed in by the
  caller, plus the task's own ``__broken`` reference. We keep the *minimal* set of
  inputs (greedy set cover) that makes ≥1 wrong solution disagree with the gold —
  these inputs empirically discriminate real failure modes rather than guessed
  ones. Mutants that no input can kill are reported as likely-equivalent and are
  excluded from the kill-rate denominator.

References: EvalPlus (NeurIPS 2023, arxiv 2305.01210); mutmut / cosmic-ray
operator sets; differential & metamorphic testing.
"""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

# --------------------------------------------------------------------------- #
# Load a callable from a source string (for executing mutants / wrong sources)
# --------------------------------------------------------------------------- #
def load_callable_from_source(source: str, name: str, filename: str = "<mutant>") -> Callable:
    """Compile ``source`` in a fresh namespace and return its callable ``name``."""
    namespace: dict[str, Any] = {}
    exec(compile(source, filename, "exec"), namespace)  # noqa: S102 - authoring tool
    fn = namespace.get(name)
    if not callable(fn):
        raise ValueError(f"source does not define a callable named {name!r}")
    return fn


def load_callable_from_package(files: dict[str, str], entry_module: str, name: str) -> Callable:
    """Write a multi-file solution (``{filename: source}``) to a temp dir and import
    ``name`` from ``entry_module``. Used to load AST-mutated variants of one module
    of a multi-file gold (the other modules are written unchanged). The entry module
    is loaded under a unique name so repeated calls do not collide."""
    import importlib.util
    import sys
    import tempfile
    import uuid

    d = Path(tempfile.mkdtemp(prefix="mutpkg_"))
    for fname, src in files.items():
        (d / fname).write_text(src)
    sys.path.insert(0, str(d))
    try:
        modname = f"mutpkg_{uuid.uuid4().hex}_{Path(entry_module).stem}"
        spec = importlib.util.spec_from_file_location(modname, d / entry_module)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return getattr(mod, name)
    finally:
        if str(d) in sys.path:
            sys.path.remove(str(d))


# --------------------------------------------------------------------------- #
# Mutation operators (single-point AST mutation; one mutant per eligible node)
# --------------------------------------------------------------------------- #
_ROR = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
        ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
_AOR = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult}
_BOR = {ast.And: ast.Or, ast.Or: ast.And}


class _OneMutation(ast.NodeTransformer):
    """Mutate exactly the ``target``-th eligible node (counted in a fixed order)."""

    def __init__(self, target: int) -> None:
        self.target = target
        self.index = -1
        self.applied = False

    def _hit(self) -> bool:
        self.index += 1
        return self.index == self.target

    def visit_Compare(self, node: ast.Compare):  # noqa: N802
        self.generic_visit(node)
        if len(node.ops) == 1 and type(node.ops[0]) in _ROR and self._hit():
            node.ops = [_ROR[type(node.ops[0])]()]
            self.applied = True
        return node

    def visit_BinOp(self, node: ast.BinOp):  # noqa: N802
        self.generic_visit(node)
        if type(node.op) in _AOR and self._hit():
            node.op = _AOR[type(node.op)]()
            self.applied = True
        return node

    def visit_BoolOp(self, node: ast.BoolOp):  # noqa: N802
        self.generic_visit(node)
        if type(node.op) in _BOR and self._hit():
            node.op = _BOR[type(node.op)]()
            self.applied = True
        return node

    def visit_Constant(self, node: ast.Constant):  # noqa: N802
        if isinstance(node.value, int) and not isinstance(node.value, bool) and self._hit():
            return ast.copy_location(ast.Constant(value=node.value + 1), node)
        return node


def _count_eligible(source: str) -> int:
    m = _OneMutation(target=-2)  # never hits → just counts
    m.visit(ast.parse(source))
    return m.index + 1


def generate_mutants(source: str) -> list[tuple[str, str]]:
    """Return ``[(label, mutant_source), ...]`` — one single-point mutant per
    eligible operator/constant node. Mutants that fail to unparse are skipped."""
    out: list[tuple[str, str]] = []
    for idx in range(_count_eligible(source)):
        tree = ast.parse(source)
        mut = _OneMutation(idx)
        mut.visit(tree)
        if not mut.applied:
            continue
        ast.fix_missing_locations(tree)
        try:
            out.append((f"mut{idx}", ast.unparse(tree)))
        except Exception:  # pragma: no cover - defensive
            continue
    return out


# --------------------------------------------------------------------------- #
# Corpus construction (cross-validate gold vs oracle; keep discriminating inputs)
# --------------------------------------------------------------------------- #
class _Crash:
    """Sentinel: a wrong solution raised — counts as a disagreement (killed)."""


def _safe_call(fn: Callable, args: Sequence[Any]):
    # Deep-copy so a wrong solution that MUTATES its argument in place (e.g. a
    # template engine with a context scope-leak bug) cannot corrupt the input for
    # the next call or the stored corpus.
    try:
        return fn(*copy.deepcopy(args))
    except Exception:  # noqa: BLE001 - a crash is a (killable) wrong answer
        return _Crash


def build_corpus(
    gold: Callable,
    oracle: Callable,
    wrong_fns: Sequence[tuple[str, Callable]],
    inputs: Iterable[Sequence[Any]],
    *,
    normalize: Callable[[Any], Any] = lambda x: x,
    max_keep: int = 200,
) -> dict[str, Any]:
    """Build a discriminating, oracle-grounded corpus.

    Parameters
    ----------
    gold     : the gold callable (e.g. ``gold(text, pattern)``).
    oracle   : an INDEPENDENT reference deciding the true answer; must agree with
               ``gold`` on every kept input (raises ``AssertionError`` otherwise —
               that signals a real bug in the gold or the oracle).
    wrong_fns: ``[(label, fn), ...]`` mutants / common-mistake / __broken wrongs.
    inputs   : iterable of argument tuples to probe.
    normalize: maps a raw return value to a JSON-comparable canonical form (applied
               to gold/oracle/wrong outputs before comparison and before storing
               ``expected``).
    max_keep : cap on committed corpus size (greedy set cover stops early).

    Returns a dict ``{"cases": [{"args", "expected"}], "meta": {...}}`` ready to be
    written to ``expected/mutation_corpus.json``.
    """
    candidates: list[dict[str, Any]] = []  # {"args", "expected", "kills": set[int]}
    killable: set[int] = set()
    n_probed = 0
    for args in inputs:
        n_probed += 1
        pristine = copy.deepcopy(list(args))  # stored verbatim; never mutated below
        g = normalize(gold(*copy.deepcopy(args)))
        o = normalize(oracle(*copy.deepcopy(args)))
        assert g == o, (
            f"GOLD disagrees with the independent ORACLE on args={args!r}: "
            f"gold={g!r} oracle={o!r} — fix the gold or the oracle before committing."
        )
        kills: set[int] = set()
        for wi, (_label, wfn) in enumerate(wrong_fns):
            wv = _safe_call(wfn, args)
            if wv is _Crash or normalize(wv) != g:
                kills.add(wi)
        if kills:
            killable |= kills
            candidates.append({"args": pristine, "expected": g, "kills": kills})

    # Greedy set cover: fewest inputs that kill every killable wrong solution.
    kept: list[dict[str, Any]] = []
    covered: set[int] = set()
    pool = list(candidates)
    while pool and covered != killable and len(kept) < max_keep:
        pool.sort(key=lambda c: len(c["kills"] - covered), reverse=True)
        best = pool.pop(0)
        if not (best["kills"] - covered):
            break
        kept.append(best)
        covered |= best["kills"]

    n_cover = len(kept)
    # Top up beyond the minimal cover with additional discriminating inputs (most
    # kills first) so the committed corpus stays robust against UNSEEN candidate
    # bugs, not just the known mutant population.
    pool.sort(key=lambda c: len(c["kills"]), reverse=True)
    for c in pool:
        if len(kept) >= max_keep:
            break
        kept.append(c)

    total_wrongs = len(wrong_fns)
    equivalent = total_wrongs - len(killable)  # never killed by ANY probed input
    meta = {
        "n_probed": n_probed,
        "n_kept": len(kept),
        "n_cover": n_cover,
        "n_wrong_solutions": total_wrongs,
        "killed": len(covered),
        "killable": len(killable),
        "likely_equivalent": equivalent,
        "kill_rate": round(len(covered) / len(killable), 4) if killable else None,
    }
    cases = [{"args": c["args"], "expected": c["expected"]} for c in kept]
    return {"cases": cases, "meta": meta}


def write_corpus(task_dir: Path | str, corpus: dict[str, Any], meta_extra: dict | None = None) -> Path:
    """Write ``corpus`` to ``<task_dir>/expected/mutation_corpus.json`` (hidden from
    the agent — ``expected/`` is never copied by ``--scaffold-candidate``)."""
    task_dir = Path(task_dir)
    out = task_dir / "expected" / "mutation_corpus.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if meta_extra:
        corpus = {**corpus, "meta": {**corpus.get("meta", {}), **meta_extra}}
    out.write_text(json.dumps(corpus, indent=2, sort_keys=False))
    return out
