import re


def _html_escape(s: str) -> str:
    """HTML-escape a string; & must be escaped first to avoid double-escaping."""
    return (
        s.replace('&', '&amp;')
         .replace('<', '&lt;')
         .replace('>', '&gt;')
         .replace('"', '&quot;')
    )


def _dotted_lookup(key: str, ctx: dict) -> object:
    """Dotted key lookup returning the actual value, or None on any miss."""
    val = ctx
    for part in key.split('.'):
        if not isinstance(val, dict):
            return None
        if part not in val:
            return None
        val = val[part]
    return val


def _render_tokens(tokens: list, ctx: dict) -> str:
    """Walk a flat token list and render to a string given context ctx."""
    result = []
    # suppress_stack: list of bools; True means the current block is suppressed.
    suppress_stack = [False]
    i = 0

    while i < len(tokens):
        token = tokens[i]
        suppressed = suppress_stack[-1]

        if token.startswith('{{') and token.endswith('}}'):
            # Variable tag: {{ varname }} or {{ varname|safe }}
            inner = token[2:-2].strip()
            if '|' in inner:
                var_part, filt_part = inner.split('|', 1)
                var_name = var_part.strip()
                use_safe = (filt_part.strip() == 'safe')
            else:
                var_name = inner
                use_safe = False

            if not suppressed:
                val = _dotted_lookup(var_name, ctx)
                if val is None:
                    val = ''
                s = str(val)
                if not use_safe:
                    s = _html_escape(s)
                result.append(s)

        elif token.startswith('{%') and token.endswith('%}'):
            # Control tag
            inner = token[2:-2].strip()
            parts = inner.split()
            tag_name = parts[0] if parts else ''

            if tag_name == 'if':
                if len(parts) >= 3 and parts[1] == 'not':
                    # {% if not name %}
                    name = parts[2]
                    val = ctx.get(name)
                    condition = not bool(val)
                else:
                    # {% if name %}
                    name = parts[1] if len(parts) >= 2 else ''
                    val = ctx.get(name)
                    condition = bool(val)
                # Push suppressed state: suppressed if already suppressed OR condition is False
                suppress_stack.append(suppressed or not condition)

            elif tag_name == 'endif':
                if len(suppress_stack) > 1:
                    suppress_stack.pop()

            elif tag_name == 'for':
                # {% for x in items %}
                # parts: ['for', 'x', 'in', 'items']
                loop_var = parts[1] if len(parts) > 1 else ''
                items_key = parts[3] if len(parts) > 3 else ''
                items_val = _dotted_lookup(items_key, ctx)

                # Collect body tokens until the matching {% endfor %}
                i += 1
                body_tokens = []
                depth = 0
                while i < len(tokens):
                    t = tokens[i]
                    if t.startswith('{%') and t.endswith('%}'):
                        t_parts = t[2:-2].strip().split()
                        t_tag = t_parts[0] if t_parts else ''
                        if t_tag == 'for':
                            depth += 1
                            body_tokens.append(t)
                        elif t_tag == 'endfor':
                            if depth == 0:
                                break  # found our endfor; i points at it
                            depth -= 1
                            body_tokens.append(t)
                        else:
                            body_tokens.append(t)
                    else:
                        body_tokens.append(t)
                    i += 1
                # i now points at the {% endfor %} token (consumed here)

                if not suppressed:
                    # Iterate items if non-empty and iterable (but not a bare string alone)
                    if (
                        items_val is not None
                        and items_val != ''
                        and hasattr(items_val, '__iter__')
                    ):
                        for elem in items_val:
                            child_ctx = {**ctx, loop_var: elem}
                            result.append(_render_tokens(body_tokens, child_ctx))
                # If suppressed, body is silently skipped.

            elif tag_name == 'endfor':
                # Not reached in normal flow — consumed by the for handler above.
                pass

        else:
            # Literal text — emit as-is unless suppressed
            if not suppressed:
                result.append(token)

        i += 1

    return ''.join(result)


def render(template: str, context: dict) -> str:
    """Render a minimal Jinja-like template string using context dict.

    Supports:
      - {{ var }} / {{ a.b }} variable substitution with HTML escaping
      - {{ var|safe }} to disable escaping
      - {% if name %} / {% if not name %} ... {% endif %}
      - {% for x in items %} ... {% endfor %}
    """
    # Tokenize once: splits on {{ ... }} and {% ... %}, capturing the delimiters.
    # Result interleaves literal text (even indices) and tags (odd indices).
    tokens = re.split(r'({{.*?}}|{%.*?%})', template, flags=re.DOTALL)
    return _render_tokens(tokens, context)
