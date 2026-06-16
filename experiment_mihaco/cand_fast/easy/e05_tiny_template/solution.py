"""
Tiny template renderer — stdlib only (re module).
Public contract: def render(template: str, context: dict) -> str
"""
import re

# Tokenizer: splits template into literal text and tags
_TOKEN_RE = re.compile(r'(\{\{.*?\}\}|\{%.*?%\})', re.DOTALL)


def _html_escape(s: str) -> str:
    """HTML-escape a string. & must be first to avoid double-encoding."""
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '&quot;')
    return s


def _resolve_dotted(context: dict, key_path: str):
    """
    Resolve a dotted key path against context.
    Returns the value or '' on any lookup failure.
    """
    keys = key_path.split('.')
    val = context
    try:
        for key in keys:
            val = val[key]
    except (KeyError, TypeError, IndexError):
        return ''
    return val


def _tokenize(template: str):
    """
    Return a list of (kind, content) tuples where kind is one of:
      'text'  — literal text
      'var'   — {{ ... }} tag, content is the inner string (stripped)
      'block' — {% ... %} tag, content is the inner string (stripped)
    """
    parts = _TOKEN_RE.split(template)
    tokens = []
    for part in parts:
        if part.startswith('{{') and part.endswith('}}'):
            inner = part[2:-2].strip()
            tokens.append(('var', inner))
        elif part.startswith('{%') and part.endswith('%}'):
            inner = part[2:-2].strip()
            tokens.append(('block', inner))
        else:
            tokens.append(('text', part))
    return tokens


# Regex patterns for block tag parsing
_IF_RE = re.compile(r'^if\s+(\w+)$')
_IF_NOT_RE = re.compile(r'^if\s+not\s+(\w+)$')
_FOR_RE = re.compile(r'^for\s+(\w+)\s+in\s+(\w+)$')
_ENDIF_RE = re.compile(r'^end\s*if$')
_ENDFOR_RE = re.compile(r'^end\s*for$')

# Regex for variable tags: name (dotted) with optional |safe
_VAR_RE = re.compile(r'^([\w.]+)\s*(?:\|\s*safe\s*)?$')
_VAR_SAFE_RE = re.compile(r'^([\w.]+)\s*\|\s*safe\s*$')


def _render_tokens(tokens, start: int, context: dict):
    """
    Render tokens starting at index `start` until the end or a block stop tag.
    Returns (rendered_string, next_index) where next_index is the index of the
    token that caused the stop (endif/endfor) or len(tokens) if we exhausted all.
    """
    result = []
    i = start
    while i < len(tokens):
        kind, content = tokens[i]

        if kind == 'text':
            result.append(content)
            i += 1

        elif kind == 'var':
            # Determine safe vs escaped
            safe = bool(_VAR_SAFE_RE.match(content))
            # Extract key path (strip |safe if present)
            key_part = content.split('|')[0].strip()
            val = _resolve_dotted(context, key_part)
            s = str(val) if not isinstance(val, str) else val
            if not safe:
                s = _html_escape(s)
            result.append(s)
            i += 1

        elif kind == 'block':
            # Check for stop tags first
            if _ENDIF_RE.match(content) or _ENDFOR_RE.match(content):
                # Stop and return; caller handles this token
                return ''.join(result), i

            m_if = _IF_RE.match(content)
            m_if_not = _IF_NOT_RE.match(content)
            m_for = _FOR_RE.match(content)

            if m_if:
                name = m_if.group(1)
                cond = bool(context.get(name))
                # Render inner tokens
                inner_str, end_i = _render_tokens(tokens, i + 1, context)
                if cond:
                    result.append(inner_str)
                # Skip past the endif token
                i = end_i + 1

            elif m_if_not:
                name = m_if_not.group(1)
                cond = bool(context.get(name))
                inner_str, end_i = _render_tokens(tokens, i + 1, context)
                if not cond:
                    result.append(inner_str)
                i = end_i + 1

            elif m_for:
                loop_var = m_for.group(1)
                items_key = m_for.group(2)
                items = context.get(items_key)
                # Collect inner tokens until endfor
                # We need to find the matching endfor
                inner_str, end_i = _render_tokens(tokens, i + 1, context)
                # end_i points to the endfor token; we need raw inner tokens
                inner_tokens = tokens[i + 1: end_i]

                # Iterate items
                if items:
                    try:
                        it = iter(items)
                    except TypeError:
                        it = iter([])
                    for element in it:
                        # Augment context with loop variable (no mutation of original)
                        loop_context = {**context, loop_var: element}
                        chunk, _ = _render_tokens(inner_tokens, 0, loop_context)
                        result.append(chunk)
                # Skip past the endfor token
                i = end_i + 1

            else:
                # Unknown block tag — treat as literal text? Or ignore.
                # Per spec, only defined tags are used; skip unknown.
                i += 1

        else:
            i += 1

    return ''.join(result), i


def render(template: str, context: dict) -> str:
    """Render a tiny Jinja-like template against context."""
    tokens = _tokenize(template)
    result, _ = _render_tokens(tokens, 0, context)
    return result
