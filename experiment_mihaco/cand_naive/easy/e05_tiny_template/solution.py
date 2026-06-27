"""
Tiny Jinja-like template renderer.
Supports:
  - {{ var }} and {{ a.b.c }} variable substitution (HTML-escaped by default)
  - {{ var|safe }} to disable escaping
  - {% if name %} ... {% endif %}
  - {% if not name %} ... {% endif %}
  - {% for x in items %} ... {% endfor %}
"""

import re


def _html_escape(s: str) -> str:
    """Escape &, <, >, and " in that order."""
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    return s


def _lookup(context: dict, key_path: str):
    """
    Resolve a dotted key path in context.
    Returns the value or None if any key is missing.
    """
    parts = key_path.split(".")
    value = context
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def _render_block(template: str, context: dict) -> str:
    """Render a template string given a context dict."""
    result = []
    i = 0
    n = len(template)

    while i < n:
        # Look for next tag: {{ or {%
        var_pos = template.find("{{", i)
        tag_pos = template.find("{%", i)

        # Determine which comes first
        if var_pos == -1 and tag_pos == -1:
            # No more tags, append rest
            result.append(template[i:])
            break

        if var_pos == -1:
            next_pos = tag_pos
            next_type = "tag"
        elif tag_pos == -1:
            next_pos = var_pos
            next_type = "var"
        else:
            if var_pos <= tag_pos:
                next_pos = var_pos
                next_type = "var"
            else:
                next_pos = tag_pos
                next_type = "tag"

        # Append literal text before the tag
        result.append(template[i:next_pos])

        if next_type == "var":
            # Find closing }}
            end = template.find("}}", next_pos + 2)
            if end == -1:
                # No closing, treat as literal
                result.append(template[next_pos:])
                i = n
                continue
            inner = template[next_pos + 2:end].strip()
            # Check for |safe filter
            safe = False
            if "|" in inner:
                parts = inner.split("|", 1)
                key_path = parts[0].strip()
                filter_name = parts[1].strip()
                if filter_name == "safe":
                    safe = True
            else:
                key_path = inner

            value = _lookup(context, key_path)
            if value is None:
                str_value = ""
            else:
                str_value = str(value)

            if not safe:
                str_value = _html_escape(str_value)

            result.append(str_value)
            i = end + 2

        else:  # next_type == "tag"
            # Find closing %}
            end = template.find("%}", next_pos + 2)
            if end == -1:
                # No closing, treat as literal
                result.append(template[next_pos:])
                i = n
                continue

            tag_content = template[next_pos + 2:end].strip()
            i = end + 2

            # Parse the tag
            if tag_content.startswith("if "):
                # Conditional: {% if name %} or {% if not name %}
                condition = tag_content[3:].strip()
                negate = False
                if condition.startswith("not "):
                    negate = True
                    condition = condition[4:].strip()

                # Find matching {% endif %}
                body, after = _find_block_end(template, i, "if")
                i = after

                # Evaluate condition
                value = context.get(condition)
                is_truthy = bool(value)
                if negate:
                    is_truthy = not is_truthy

                if is_truthy:
                    result.append(_render_block(body, context))

            elif tag_content.startswith("for "):
                # Loop: {% for x in items %}
                m = re.match(r'^for\s+(\w+)\s+in\s+(\w+)$', tag_content)
                if m:
                    loop_var = m.group(1)
                    items_key = m.group(2)

                    # Find matching {% endfor %}
                    body, after = _find_block_end(template, i, "for")
                    i = after

                    items = context.get(items_key)
                    if items:
                        for item in items:
                            # Create a new context with loop variable
                            loop_context = dict(context)
                            loop_context[loop_var] = item
                            result.append(_render_block(body, loop_context))
                else:
                    # Malformed for tag, skip
                    body, after = _find_block_end(template, i, "for")
                    i = after

            elif tag_content in ("endif", "endfor"):
                # These should be consumed by their opener; if we see them here,
                # they're stray — just skip
                pass
            else:
                # Unknown tag, skip
                pass

    return "".join(result)


def _find_block_end(template: str, start: int, block_type: str) -> tuple:
    """
    Find the matching end tag ({% endif %} or {% endfor %}) for a block,
    handling nesting of the same block type.

    Returns (body_text, position_after_end_tag).
    """
    end_tag = "end" + block_type
    depth = 1
    i = start
    n = len(template)

    while i < n:
        tag_pos = template.find("{%", i)
        if tag_pos == -1:
            # No more tags — malformed template, return everything
            return template[start:], n

        end = template.find("%}", tag_pos + 2)
        if end == -1:
            return template[start:], n

        tag_content = template[tag_pos + 2:end].strip()

        if tag_content.startswith(block_type + " ") or tag_content == block_type:
            depth += 1
        elif tag_content == end_tag:
            depth -= 1
            if depth == 0:
                return template[start:tag_pos], end + 2

        i = end + 2

    # No matching end found
    return template[start:], n


def render(template: str, context: dict) -> str:
    """
    Render a template string with the given context dictionary.

    Supports:
    - {{ var }} — HTML-escaped variable substitution
    - {{ var|safe }} — raw variable substitution (no escaping)
    - {{ a.b.c }} — dotted dict access
    - {% if name %} ... {% endif %} — conditional
    - {% if not name %} ... {% endif %} — negated conditional
    - {% for x in items %} ... {% endfor %} — loop
    """
    return _render_block(template, context)
