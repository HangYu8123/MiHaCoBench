# Easy 05 — `tiny_template`: minimal Jinja-like template renderer

**Created:** 2026-06-15 · **Category:** easy · **Weight:** 1

Implement a tiny template renderer. Write your solution as `solution.py`.
Use the **standard library only** (e.g. `re`). Do not import third-party
template engines.

## Public contract (must match exactly)

```python
def render(template: str, context: dict) -> str:
    ...
```

`template` is a string that may contain the constructs described below.
`context` is a plain Python `dict` (values may themselves be dicts or lists).
The function returns the fully-rendered string.

### Variable substitution

`{{ name }}` — Look up `name` in `context` and replace the tag with its string
representation. Whitespace inside the braces is ignored (`{{ name }}`,
`{{name}}`, and `{{  name  }}` are all equivalent).

**Dotted lookup** `{{ a.b }}` — Look up `a` in `context` to get a value, then
access key `b` on that value (dict access only; no attribute access is required).
Multiple dots (e.g. `{{ a.b.c }}`) are chained the same way.

**HTML escaping (default-on):** the substituted string is HTML-escaped before
insertion — the four characters `&`, `<`, `>`, and `"` are replaced with their
HTML entities (`&amp;`, `&lt;`, `&gt;`, `&quot;`) in that order. This applies
to both plain and dotted variable tags.

**`|safe` filter** — `{{ name|safe }}` (or `{{ a.b|safe }}`) disables escaping
for that tag; the raw string is inserted as-is. Whitespace around the pipe is
ignored.

**Missing variable** — If the key path does not exist in `context` (including
a missing intermediate key), the tag is replaced with an empty string `""`.

### Conditionals

```
{% if name %}...{% endif %}
{% if not name %}...{% endif %}
```

Perform a truthiness test on `context[name]` (plain key only, no dotted lookup
required for `if`). A missing key is treated as falsy.

* `{% if name %}...{% endif %}` — renders the body if the value is truthy.
* `{% if not name %}...{% endif %}` — renders the body if the value is falsy
  (or missing).

Whitespace inside `{%` / `%}` tags is ignored.

### Loops

```
{% for x in items %}...{% endfor %}
```

Looks up `items` in `context`. If the value is a non-empty iterable, renders
the body once for each element, replacing `{{ x }}` with the string form of the
element (HTML-escaped by default; `{{ x|safe }}` disables escaping). Dotted
access on the loop variable is supported: `{{ x.key }}` looks up `key` on the
current element (dict access).

If `items` is missing or empty (empty list, `None`, etc.), the loop body is
emitted **zero** times.

The loop variable `x` is **not** visible outside the `{% for %}...{% endfor %}`
block.

## Notes

* Tags are rendered left to right; nesting of `if` inside `for` is supported
  (but nesting `for` inside `for` is not required).
* The template may contain any text outside tags; that text is preserved as-is.
* Determinism: identical inputs produce identical output.
