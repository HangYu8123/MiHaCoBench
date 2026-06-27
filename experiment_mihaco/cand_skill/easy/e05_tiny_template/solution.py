"""
Tiny Jinja-like template renderer.
Public contract: render(template: str, context: dict) -> str
"""

import re


def _html_escape(s: str) -> str:
    """Escape HTML special characters in order: & < > "."""
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )


def _lookup(key: str, context: dict):
    """
    Walk a dotted key path through nested dicts.
    Returns (True, value) if found, (False, None) if any segment is missing.
    """
    parts = key.split(".")
    current = context
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _tokenize(template: str):
    """
    Split template into alternating literal/tag tokens.
    Capturing group ensures delimiters appear in result.
    """
    return re.split(r"({{.*?}}|{%.*?%})", template, flags=re.DOTALL)


def _render_tokens(tokens, context: dict) -> str:
    """
    Core render loop. Processes a list of tokens with the given context.
    Handles variable substitution, if/endif, and for/endfor.
    """
    output = []
    i = 0
    n = len(tokens)

    while i < n:
        token = tokens[i]

        # Literal text — emit as-is
        if not (token.startswith("{{") or token.startswith("{%")):
            output.append(token)
            i += 1
            continue

        # Variable tag: {{ expr }}
        if token.startswith("{{"):
            inner = token[2:-2].strip()
            # Detect |safe filter (strip whitespace around pipe parts)
            parts = [p.strip() for p in inner.split("|")]
            safe = len(parts) > 1 and parts[-1] == "safe"
            expr = parts[0]
            found, value = _lookup(expr, context)
            if found:
                s = str(value)
                output.append(s if safe else _html_escape(s))
            # else: emit empty string (nothing appended)
            i += 1
            continue

        # Control tag: {% ... %}
        inner = token[2:-2].strip()
        parts = inner.split()

        # {% if name %} or {% if not name %}
        if parts[0] == "if":
            negate = len(parts) >= 3 and parts[1] == "not"
            key = parts[2] if negate else parts[1]
            # Plain key lookup (no dotted lookup for if conditions)
            value = context.get(key)
            condition = bool(value)
            if negate:
                condition = not condition

            if condition:
                # Consume tokens for the true branch until matching {% endif %}
                # (or {% else %}, not required here)
                i += 1
                depth = 0
                branch_tokens = []
                while i < n:
                    t = tokens[i]
                    if t.startswith("{%"):
                        t_inner = t[2:-2].strip().split()
                        if t_inner[0] in ("if", "for"):
                            depth += 1
                            branch_tokens.append(t)
                        elif t_inner[0] in ("endif", "endfor"):
                            if depth == 0:
                                i += 1
                                break
                            depth -= 1
                            branch_tokens.append(t)
                        else:
                            branch_tokens.append(t)
                    else:
                        branch_tokens.append(t)
                    i += 1
                # Render the collected branch tokens
                output.append(_render_tokens(branch_tokens, context))
            else:
                # Skip tokens until matching {% endif %}
                i += 1
                depth = 0
                while i < n:
                    t = tokens[i]
                    if t.startswith("{%"):
                        t_inner = t[2:-2].strip().split()
                        if t_inner[0] in ("if", "for"):
                            depth += 1
                        elif t_inner[0] in ("endif", "endfor"):
                            if depth == 0:
                                i += 1
                                break
                            depth -= 1
                    i += 1
            continue

        # {% for x in items %}
        if parts[0] == "for" and len(parts) == 4 and parts[2] == "in":
            loop_var = parts[1]
            items_key = parts[3]
            found, items_value = _lookup(items_key, context)
            items_list = list(items_value) if found and items_value else []

            # Collect body tokens until matching {% endfor %}
            i += 1
            depth = 0
            body_tokens = []
            while i < n:
                t = tokens[i]
                if t.startswith("{%"):
                    t_inner = t[2:-2].strip().split()
                    if t_inner[0] in ("if", "for"):
                        depth += 1
                        body_tokens.append(t)
                    elif t_inner[0] in ("endif", "endfor"):
                        if depth == 0:
                            i += 1
                            break
                        depth -= 1
                        body_tokens.append(t)
                    else:
                        body_tokens.append(t)
                else:
                    body_tokens.append(t)
                i += 1

            # Render body for each element
            for element in items_list:
                # Fresh merged context per iteration — never mutate original
                iter_context = {**context, loop_var: element}
                output.append(_render_tokens(body_tokens, iter_context))
            continue

        # {% endif %} or {% endfor %} encountered standalone — ignore
        i += 1

    return "".join(output)


def render(template: str, context: dict) -> str:
    """Render a tiny Jinja-like template against the given context dict."""
    tokens = _tokenize(template)
    return _render_tokens(tokens, context)
