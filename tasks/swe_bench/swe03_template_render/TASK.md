# SWE 03 — `template_render`: Minimal multi-module template engine

**Created:** 2026-06-15 · **Category:** swe_bench · **Weight:** 6

Implement a minimal text template engine split across **three modules**:

| File | Responsibility |
|------|----------------|
| `lexer.py` | Tokenize a template string into a flat list of tokens |
| `parser.py` | Build a simple node tree from the token list |
| `renderer.py` | **Facade** — re-exports `render(template: str, context: dict) -> str` |

Use the **standard library only** (no third-party template engines).

---

## Template syntax

### Variable tags

```
{{ name }}
```

Look up `name` in `context` and insert its string representation.
Whitespace inside `{{` / `}}` is ignored.

**Dotted lookup** — `{{ user.name }}` resolves `context["user"]["name"]` (dict
access only).  Multiple dots are chained.

**Missing variable** — If any step of the lookup fails, the tag is replaced
with an empty string `""`.

### Loop blocks

```
{% for item in items %}...{% endfor %}
```

Look up `items` in `context`.  If it is a non-empty iterable, render the body
once per element with the loop variable (`item`) bound to that element.
If `items` is missing or empty the block renders as `""`.

**Nested loops** — `{% for %}` blocks may be nested arbitrarily:

```
{% for row in rows %}{% for cell in cells %}{{ row }}-{{ cell }} {% endfor %}{% endfor %}
```

Loop variables are **block-scoped**: a loop binds its variable only for the
duration of its own body and must not leak into the surrounding scope after the
block ends.  In particular, any variable that already existed in the context
before a loop must retain its original value once the loop completes, and an
outer loop's variable must be unaffected by an inner loop.

---

## Public contract

### `lexer.py`

```python
class TokenType:
    TEXT = "TEXT"
    VAR  = "VAR"
    FOR  = "FOR"
    ENDFOR = "ENDFOR"

class Token:
    type: str       # one of TokenType.*
    value: str      # raw content: TEXT=literal, VAR=var path, FOR="loop_var|items_var"
```

```python
def tokenize(template: str) -> list[Token]
```

Returns the ordered list of tokens.  `FOR` token `value` is
`"<loop_var>|<items_var>"`.

### `renderer.py` (facade)

```python
def render(template: str, context: dict) -> str
```

The only callable the agent needs to export from `renderer.py`.
Internally it may use `parser.py` (and `lexer.py` through `parser.py`), but
the grader only calls `render` from `renderer.py`.

---

## Constraints

* Dotted lookup on a loop variable works: `{{ x.key }}` during
  `{% for x in items %}` resolves `element["key"]`.
* Missing variable at any depth → empty string (no exception).
* Empty loop list → zero iterations, empty output for that block.
* The grader imports `lexer.py` and `renderer.py` directly.
