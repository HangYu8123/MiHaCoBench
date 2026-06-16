"""INI-file parser with type coercion and interpolation."""

import re

_INTERP_PATTERN = re.compile(r'\$\{([^}]+)\}')


def _coerce(v: str) -> object:
    """Apply coercion rules to a stripped string value."""
    # 1. Integer: must round-trip through str(int(...))
    try:
        int_val = int(v)
        if str(int_val) == v:
            return int_val
    except (ValueError, TypeError):
        pass

    # 2. Float
    try:
        return float(v)
    except (ValueError, TypeError):
        pass

    # 3. Bool True
    if v.lower() in {"true", "yes"}:
        return True

    # 4. Bool False
    if v.lower() in {"false", "no"}:
        return False

    # 5. String
    return v


def parse_ini(text: str) -> dict[str, dict[str, object]]:
    """Parse INI-format text and return a nested dict with coerced values.

    Sections map to dicts of key -> coerced value. Keys before any section
    go into "default". String values may contain ${section.key} references
    which are resolved iteratively.

    Raises ValueError if an interpolation reference is missing or cycles.
    """
    result: dict[str, dict[str, object]] = {}
    current_section = "default"

    for raw_line in text.splitlines():
        line = raw_line.strip()

        # Skip blank lines and comments
        if not line or line[0] in ('#', ';'):
            continue

        # Section header
        if line.startswith('[') and line.endswith(']'):
            section_name = line[1:-1].strip()
            current_section = section_name
            if section_name not in result:
                result[section_name] = {}
            continue

        # Key/value pair: find the first occurrence of '=' or ':'
        eq_pos = line.find('=')
        col_pos = line.find(':')

        # Determine the separator position (take the earlier one present)
        if eq_pos == -1 and col_pos == -1:
            # No separator — skip line
            continue
        elif eq_pos == -1:
            sep_pos = col_pos
        elif col_pos == -1:
            sep_pos = eq_pos
        else:
            sep_pos = min(eq_pos, col_pos)

        key = line[:sep_pos].strip()
        value_str = line[sep_pos + 1:].strip()

        if not key:
            # Empty key — skip
            continue

        coerced = _coerce(value_str)

        # Ensure section exists (handles keys before any section header)
        if current_section not in result:
            result[current_section] = {}

        result[current_section][key] = coerced

    # Interpolation pass — only for str-typed values
    for section in result:
        for key in result[section]:
            if not isinstance(result[section][key], str):
                continue

            value = result[section][key]
            for _ in range(1000):
                match = _INTERP_PATTERN.search(value)
                if match is None:
                    break  # Stable — no more references

                def make_replacer(res):
                    def replacer(m):
                        token = m.group(1)
                        parts = token.split('.', 1)
                        if len(parts) != 2:
                            raise ValueError(
                                f"Invalid interpolation token: ${{{token}}}"
                            )
                        ref_sec, ref_key = parts
                        if ref_sec not in res:
                            raise ValueError(
                                f"Interpolation references unknown section: "
                                f"'{ref_sec}'"
                            )
                        if ref_key not in res[ref_sec]:
                            raise ValueError(
                                f"Interpolation references unknown key: "
                                f"'{ref_key}' in section '{ref_sec}'"
                            )
                        return str(res[ref_sec][ref_key])
                    return replacer

                new_value = _INTERP_PATTERN.sub(make_replacer(result), value)
                if new_value == value:
                    # No substitution made progress — cycle or unresolvable
                    raise ValueError(
                        f"Interpolation cycle or unresolvable reference in "
                        f"section '{section}', key '{key}': {value!r}"
                    )
                value = new_value
            else:
                raise ValueError(
                    f"Interpolation did not terminate (cycle detected) in "
                    f"section '{section}', key '{key}'"
                )

            result[section][key] = value

    return result
