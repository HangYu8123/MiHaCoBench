"""
Easy 05 — tiny_template: minimal Jinja-like template renderer.
Uses standard library only (re module).
"""

import re


def _html_escape(s: str) -> str:
    """Escape &, <, >, and " in that order."""
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    return s


def _lookup(context: dict, path: str):
    """
    Look up a dotted path in context.
    Returns the value if found, or None if any key is missing.
    """
    parts = path.split(".")
    value = context
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def render(template: str, context: dict) -> str:
    """
    Render a Jinja-like template string with the given context dict.

    Supports:
    - Variable substitution: {{ name }}, {{ a.b }}, {{ name|safe }}
    - Conditionals: {% if name %}...{% endif %}, {% if not name %}...{% endif %}
    - Loops: {% for x in items %}...{% endfor %}
    """
    result = []
    pos = 0
    length = len(template)

    # Pattern to match tags
    tag_pattern = re.compile(r'\{\{.*?\}\}|\{%.*?%\}', re.DOTALL)

    # We'll process top-level tokens, handling block structures
    # First tokenize the template
    tokens = _tokenize(template)
    # Then evaluate the token stream
    output = _evaluate(tokens, context, loop_var=None, loop_value=None)
    return output


def _tokenize(template: str):
    """
    Tokenize the template into a list of tokens.
    Each token is a tuple: ('text', text) | ('var', expr) | ('block', content)
    """
    tokens = []
    pos = 0
    length = len(template)
    tag_pattern = re.compile(r'(\{\{.*?\}\}|\{%.*?%\})', re.DOTALL)

    for m in tag_pattern.finditer(template):
        start, end = m.start(), m.end()
        if start > pos:
            tokens.append(('text', template[pos:start]))
        tag = m.group(0)
        if tag.startswith('{{'):
            # Variable tag
            expr = tag[2:-2].strip()
            tokens.append(('var', expr))
        else:
            # Block tag
            content = tag[2:-2].strip()
            tokens.append(('block', content))
        pos = end

    if pos < length:
        tokens.append(('text', template[pos:]))

    return tokens


def _evaluate(tokens, context: dict, loop_var, loop_value):
    """
    Evaluate a list of tokens against the context.
    loop_var: the loop variable name (if inside a for loop), else None
    loop_value: the current loop element value, else None
    Returns the rendered string.
    """
    result = []
    i = 0
    n = len(tokens)

    while i < n:
        kind, value = tokens[i]

        if kind == 'text':
            result.append(value)
            i += 1

        elif kind == 'var':
            # Variable substitution
            expr = value
            safe = False
            if '|' in expr:
                parts = expr.split('|', 1)
                expr = parts[0].strip()
                filter_name = parts[1].strip()
                if filter_name == 'safe':
                    safe = True

            # Resolve the variable
            resolved = _resolve_var(expr, context, loop_var, loop_value)
            if resolved is None:
                rendered = ''
            else:
                rendered = str(resolved)

            if not safe:
                rendered = _html_escape(rendered)

            result.append(rendered)
            i += 1

        elif kind == 'block':
            block_content = value

            if block_content.startswith('if '):
                # {% if name %} or {% if not name %}
                condition_expr = block_content[3:].strip()
                negate = False
                if condition_expr.startswith('not '):
                    negate = True
                    condition_expr = condition_expr[4:].strip()

                # Find matching endif
                body_tokens, skip = _collect_block(tokens, i + 1, 'endif')
                i = skip  # i now points past the endfor/endif token

                # Evaluate condition - check loop var first, then context
                if loop_var is not None and condition_expr == loop_var:
                    val = loop_value
                else:
                    val = context.get(condition_expr)
                is_truthy = bool(val)
                if negate:
                    is_truthy = not is_truthy

                if is_truthy:
                    result.append(_evaluate(body_tokens, context, loop_var, loop_value))

            elif block_content.startswith('for '):
                # {% for x in items %}
                m = re.match(r'^for\s+(\w+)\s+in\s+(\w+)$', block_content)
                if not m:
                    i += 1
                    continue
                var_name = m.group(1)
                items_name = m.group(2)

                # Find matching endfor
                body_tokens, skip = _collect_block(tokens, i + 1, 'endfor')
                i = skip

                # Lookup items in context
                items = context.get(items_name)
                if items:
                    try:
                        for element in items:
                            result.append(_evaluate(body_tokens, context, var_name, element))
                    except TypeError:
                        pass  # Not iterable

            elif block_content == 'endif' or block_content == 'endfor':
                # Should not encounter these here at top level in normal usage
                # but skip them
                i += 1
            else:
                # Unknown block, skip
                i += 1

        else:
            i += 1

    return ''.join(result)


def _collect_block(tokens, start: int, end_tag: str):
    """
    Collect tokens for a block body, handling nested same-type blocks.
    Returns (body_tokens, next_index) where next_index points to the token AFTER the end tag.

    For simplicity (spec says nesting for-in-for is not required), we find the
    first matching end_tag at the same nesting level.
    """
    # Determine opening tag prefix based on end_tag
    if end_tag == 'endif':
        open_prefix = 'if '
    elif end_tag == 'endfor':
        open_prefix = 'for '
    else:
        open_prefix = None

    depth = 1
    body_tokens = []
    i = start
    n = len(tokens)

    while i < n:
        kind, value = tokens[i]
        if kind == 'block':
            if value == end_tag:
                depth -= 1
                if depth == 0:
                    return body_tokens, i + 1
                else:
                    body_tokens.append((kind, value))
            elif open_prefix and value.startswith(open_prefix):
                depth += 1
                body_tokens.append((kind, value))
            else:
                body_tokens.append((kind, value))
        else:
            body_tokens.append((kind, value))
        i += 1

    # If we didn't find the end tag, return what we have
    return body_tokens, i


def _resolve_var(expr: str, context: dict, loop_var, loop_value):
    """
    Resolve a variable expression (possibly dotted) against context.
    If expr starts with loop_var, use the loop value instead.
    Returns the resolved value or None if not found.
    """
    parts = expr.split('.')

    if loop_var is not None and parts[0] == loop_var:
        # First part is the loop variable
        value = loop_value
        for part in parts[1:]:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value
    else:
        # Look up in context
        value = context
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value
