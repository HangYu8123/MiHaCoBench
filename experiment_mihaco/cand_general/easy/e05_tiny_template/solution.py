"""
Tiny Jinja-like template renderer.
Public contract: render(template: str, context: dict) -> str
"""

import re

# Compiled regex for tokenizing: splits on {{ ... }} and {% ... %} tags.
# The capturing group means re.split returns interleaved [literal, tag, literal, tag, ...]
_TAG_RE = re.compile(r'(\{\{.*?\}\}|\{%.*?%\})', re.DOTALL)


def _html_escape(s: str) -> str:
    """HTML-escape the four special characters in the mandatory order."""
    # Order is critical: & must come first to avoid double-escaping
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '&quot;')
    return s


def _resolve_raw(key_path: str, context: dict):
    """
    Resolve a dotted key path against context.
    Returns the raw Python object (could be list, dict, etc.) or None on failure.
    Returns None for missing keys / type errors.
    """
    parts = key_path.split('.')
    current = context
    try:
        for part in parts:
            if not isinstance(current, dict):
                return None
            current = current[part]
        return current
    except (KeyError, TypeError):
        return None


def _resolve(key_path: str, context: dict) -> str:
    """
    Resolve a dotted key path against context, returning a string.
    Returns "" on missing keys / type errors.
    """
    value = _resolve_raw(key_path, context)
    if value is None:
        return ""
    return str(value)


def _render_tokens(tokens: list, context: dict) -> str:
    """
    Walk the token list with an integer cursor, producing the rendered string.
    """
    output_parts = []
    i = 0
    n = len(tokens)

    while i < n:
        token = tokens[i]
        i += 1

        if token.startswith('{{'):
            # Variable tag: {{ expr }}
            inner = token[2:-2].strip()  # strip {{ and }} and outer whitespace

            # Detect |safe filter — handle whitespace around the pipe
            # Split on '|' to check for safe filter
            pipe_idx = inner.rfind('|')
            escape = True
            key_path = inner

            if pipe_idx != -1:
                filter_part = inner[pipe_idx + 1:].strip()
                if filter_part == 'safe':
                    escape = False
                    key_path = inner[:pipe_idx].strip()

            value = _resolve(key_path, context)
            if escape:
                value = _html_escape(value)
            output_parts.append(value)

        elif token.startswith('{%'):
            # Block tag: {% ... %}
            inner = token[2:-2].strip()  # strip {% and %} and outer whitespace
            parts = inner.split()

            if not parts:
                # Empty block tag, ignore
                continue

            if parts[0] == 'if':
                # {% if name %} or {% if not name %}
                if len(parts) >= 3 and parts[1] == 'not':
                    # {% if not name %}
                    var_name = parts[2]
                    condition = not bool(context.get(var_name))
                elif len(parts) >= 2:
                    # {% if name %}
                    var_name = parts[1]
                    condition = bool(context.get(var_name))
                else:
                    condition = False

                # Collect body tokens until matching {% endif %} at depth 0
                body_tokens = []
                depth = 0
                while i < n:
                    t = tokens[i]
                    i += 1
                    if t.startswith('{%'):
                        t_inner = t[2:-2].strip()
                        t_parts = t_inner.split()
                        if t_parts and t_parts[0] == 'if':
                            depth += 1
                            body_tokens.append(t)
                        elif t_parts and t_parts[0] == 'endif':
                            if depth == 0:
                                break  # Found the matching endif
                            depth -= 1
                            body_tokens.append(t)
                        else:
                            body_tokens.append(t)
                    else:
                        body_tokens.append(t)

                if condition:
                    output_parts.append(_render_tokens(body_tokens, context))

            elif parts[0] == 'endif':
                # Top-level endif without matching if — ignore
                continue

            elif parts[0] == 'for':
                # {% for x in items %}
                # Expected: parts = ['for', 'x', 'in', 'items']
                if len(parts) >= 4 and parts[2] == 'in':
                    loop_var = parts[1]
                    items_key = parts[3]
                else:
                    # Malformed for tag, skip body
                    loop_var = None
                    items_key = None

                # Collect body tokens until matching {% endfor %} at depth 0
                body_tokens = []
                depth = 0
                while i < n:
                    t = tokens[i]
                    i += 1
                    if t.startswith('{%'):
                        t_inner = t[2:-2].strip()
                        t_parts = t_inner.split()
                        if t_parts and t_parts[0] == 'for':
                            depth += 1
                            body_tokens.append(t)
                        elif t_parts and t_parts[0] == 'endfor':
                            if depth == 0:
                                break  # Found the matching endfor
                            depth -= 1
                            body_tokens.append(t)
                        else:
                            body_tokens.append(t)
                    else:
                        body_tokens.append(t)

                # Look up items using raw resolve (need actual iterable, not str)
                if items_key is not None:
                    items = _resolve_raw(items_key, context)
                else:
                    items = None

                # If missing, None, empty string, or not iterable: skip loop
                if items is None or items == '' or items == []:
                    pass  # zero iterations
                else:
                    try:
                        for element in items:
                            # Create a new context with the loop variable bound
                            iter_context = {**context, loop_var: element}
                            output_parts.append(_render_tokens(body_tokens, iter_context))
                    except TypeError:
                        pass  # Not iterable — zero iterations

            elif parts[0] == 'endfor':
                # Top-level endfor without matching for — ignore
                continue

            else:
                # Unknown block tag, ignore
                continue

        else:
            # Literal text — append as-is
            output_parts.append(token)

    return ''.join(output_parts)


def render(template: str, context: dict) -> str:
    """
    Render a tiny Jinja-like template string against the given context dict.

    Supports:
      - {{ var }} and {{ a.b.c }} variable substitution (HTML-escaped by default)
      - {{ var|safe }} to disable escaping
      - {% if name %} / {% if not name %} ... {% endif %} conditionals
      - {% for x in items %} ... {% endfor %} loops

    Missing keys resolve to empty string "".
    """
    tokens = _TAG_RE.split(template)
    return _render_tokens(tokens, context)
