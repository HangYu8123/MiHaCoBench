"""Generate the oracle-grounded mutation corpus for swe_bench/swe03_template_render.

Independent oracle: **jinja2** (a real, third-party template engine — TRUE external
ground truth, not authored here). The task's mini-template syntax ({{ var }},
{{ a.b }}, {% for x in items %}...{% endfor %}) is a subset of jinja2's, so jinja2
renders the same inline templates. We configure ``ChainableUndefined`` so a missing
variable (and missing dotted lookups) render as '' — matching the task spec.

Provenance: template loop-variable scoping — cf. jinja2 issue #641 (2.9 tightened
loop scope so loop vars no longer leak to the outer scope). The corpus
cross-validates the gold engine against jinja2 and keeps templates that kill real
wrong renderers (the __broken scope-leak variant + AST mutants of renderer.py).

Run:  python3 experiment_mihaco/mutation_gen/gen_swe03.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiment_mihaco"))

import jinja2  # noqa: E402

from _lib import grading_utils as gu  # noqa: E402
import _mutation_seed as ms  # noqa: E402

CATEGORY, TASK_ID = "swe_bench", "swe03_template_render"
GOLD_DIR = gu.GOLD_ROOT / CATEGORY / TASK_ID
BROKEN_DIR = gu.GOLD_ROOT / CATEGORY / f"{TASK_ID}__broken"

_LEXER = (GOLD_DIR / "lexer.py").read_text()
_PARSER = (GOLD_DIR / "parser.py").read_text()
_RENDERER = (GOLD_DIR / "renderer.py").read_text()

# Gold render (load the real package by path).
gold = gu.load_callable(GOLD_DIR, "renderer.py", "render")

# --- Independent external oracle: jinja2 ------------------------------------ #
_ENV = jinja2.Environment(undefined=jinja2.ChainableUndefined, autoescape=False,
                          keep_trailing_newline=True)


def oracle(template: str, context: dict) -> str:
    return _ENV.from_string(template).render(context)


# --- Wrong renderers: the real __broken + AST mutants of renderer.py -------- #
def _wrong_fns():
    wrongs = []
    try:
        wrongs.append(("__broken", gu.load_callable(BROKEN_DIR, "renderer.py", "render")))
    except Exception:
        pass
    for label, mutant_renderer in ms.generate_mutants(_RENDERER):
        try:
            fn = ms.load_callable_from_package(
                {"lexer.py": _LEXER, "parser.py": _PARSER, "renderer.py": mutant_renderer},
                "renderer.py", "render")
            wrongs.append((label, fn))
        except Exception:
            continue
    return wrongs


# --- Deterministic template/context generator (jinja2-equivalent subset) ----- #
_RNG = random.Random(20260616)
_VARS = ["x", "y", "z", "row", "col", "item", "name", "val"]   # excludes reserved 'loop'
_KEYS = ["a", "b", "c", "name", "val"]
_WORDS = ["A", "B", "C", "1", "2", "3", "hi", "ok", ""]


def _rand_text():
    return "".join(_RNG.choice(["-", ":", ",", " ", "[", "]", "|", "x"]) for _ in range(_RNG.randint(0, 3)))


def _gen_template_and_context(depth=0):
    """Return (template_str, context_dict) within the supported subset."""
    ctx: dict = {}
    parts: list[str] = []
    n_segments = _RNG.randint(1, 3)
    for _ in range(n_segments):
        kind = _RNG.choice(["text", "var", "dotted", "loop"]) if depth < 2 else _RNG.choice(["text", "var"])
        if kind == "text":
            parts.append(_rand_text())
        elif kind == "var":
            v = _RNG.choice(_VARS + _KEYS)
            if _RNG.random() < 0.7:           # present 70% of the time, else missing -> ''
                ctx[v] = _RNG.choice(_WORDS)
            parts.append("{{ " + v + " }}")
        elif kind == "dotted":
            outer, inner = _RNG.choice(_KEYS), _RNG.choice(_KEYS)
            if _RNG.random() < 0.7:
                ctx[outer] = {inner: _RNG.choice(_WORDS)}
            parts.append("{{ " + f"{outer}.{inner}" + " }}")
        else:  # loop
            var = _RNG.choice(_VARS)
            items_key = "items" + str(_RNG.randint(0, 3))
            ctx[items_key] = [_RNG.choice(_WORDS) for _ in range(_RNG.randint(0, 3))]
            body_tmpl, body_ctx = _gen_template_and_context(depth + 1)
            # merge nested context (loop var is bound by the loop, not the context)
            for k, val in body_ctx.items():
                if k != var:
                    ctx.setdefault(k, val)
            parts.append("{% for " + var + " in " + items_key + " %}"
                         + "{{ " + var + " }}" + body_tmpl + "{% endfor %}")
    return "".join(parts), ctx


def _inputs():
    out = [(_gen_template_and_context()) for _ in range(2500)]
    # explicit high-value cases (scope-leak discriminators)
    out += [
        ("{% for x in items %}{{ x }}{% endfor %}|{{ x }}", {"x": "orig", "items": ["a", "b"]}),
        ("{% for x in rows %}[{% for x in cols %}{{ x }},{% endfor %}{{ x }}]{% endfor %}",
         {"rows": ["A", "B"], "cols": ["1", "2"]}),
        ("{% for row in rows %}{{ row }}:{% for label in cols %}{{ label }}{% endfor %};{% endfor %}{{ label }}",
         {"label": "L", "rows": ["A", "B"], "cols": ["1", "2"]}),
        ("{{ user.name }}", {"user": {"name": "Bob"}}),
        ("{{ missing }}", {}),
        ("{% for x in empty %}{{ x }}{% endfor %}end", {"empty": []}),
    ]
    return out


def main() -> int:
    wrongs = _wrong_fns()
    # Filter inputs jinja2 cannot render (keeps the oracle total): build_corpus
    # asserts gold==oracle, so pre-drop any input where jinja2 raises.
    safe = []
    for tmpl, ctx in _inputs():
        try:
            oracle(tmpl, ctx)
        except Exception:
            continue
        safe.append((tmpl, ctx))
    corpus = ms.build_corpus(gold, oracle, wrongs, safe, max_keep=120)
    out = ms.write_corpus(ROOT / "tasks" / CATEGORY / TASK_ID, corpus, meta_extra={
        "oracle": "jinja2 (ChainableUndefined) — true external template engine",
        "provenance": "jinja2 issue #641 (loop-variable scope tightened in 2.9); template loop scoping",
        "input_seed": 20260616,
        "jinja2_version": jinja2.__version__,
    })
    print(f"wrote {out}")
    print("meta:", corpus["meta"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
