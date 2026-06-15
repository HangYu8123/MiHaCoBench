"""Gold reference for easy/e02_ini_parser — INI-file parser with coercion and interpolation."""
from __future__ import annotations

import re


def _coerce(value: str) -> object:
    """Coerce a stripped string value to int, float, bool, or str."""
    # 1. Integer check: round-trips through int exactly.
    try:
        iv = int(value)
        if str(iv) == value:
            return iv
    except (ValueError, TypeError):
        pass
    # 2. Float check.
    try:
        return float(value)
    except (ValueError, TypeError):
        pass
    # 3/4. Boolean check (case-insensitive).
    lower = value.lower()
    if lower in ("true", "yes"):
        return True
    if lower in ("false", "no"):
        return False
    # 5. Keep as string.
    return value


_REF_RE = re.compile(r"\$\{([^}]+)\}")


def _resolve(section_name: str, key: str, raw: str,
             parsed: dict[str, dict[str, object]],
             in_progress: set[tuple[str, str]]) -> object:
    """Iteratively expand ${section.key} references in *raw* (a str value).

    Raises ValueError on missing reference or detected cycle.
    """
    anchor = (section_name, key)
    if anchor in in_progress:
        raise ValueError(
            f"Interpolation cycle detected at [{section_name}] {key!r}"
        )
    in_progress = in_progress | {anchor}

    max_iter = 200
    current = raw
    for _ in range(max_iter):
        match = _REF_RE.search(current)
        if match is None:
            break
        ref = match.group(1)
        if "." not in ref:
            raise ValueError(f"Invalid interpolation reference: ${{{{ {ref} }}}}")
        ref_section, ref_key = ref.split(".", 1)
        if ref_section not in parsed:
            raise ValueError(
                f"Interpolation references unknown section [{ref_section}]"
            )
        if ref_key not in parsed[ref_section]:
            raise ValueError(
                f"Interpolation references unknown key {ref_key!r} "
                f"in section [{ref_section}]"
            )
        replacement = str(parsed[ref_section][ref_key])
        current = current[: match.start()] + replacement + current[match.end() :]
    else:
        raise ValueError("Interpolation did not stabilise — possible cycle")
    return current


def parse_ini(text: str) -> dict[str, dict[str, object]]:
    """Parse an INI-formatted string and return a nested dict.

    Sections: [name]
    Key/value: key = value  OR  key: value  (first separator wins)
    Comments:  lines starting with # or ; are ignored.
    Blank lines are ignored.
    Keys before any section go under 'default'.
    Duplicate key in a section: last value wins.
    Value coercion: int > float > bool > str.
    Interpolation: ${section.key} references are expanded iteratively.
    Raises ValueError on missing reference or cycle.
    """
    raw_sections: dict[str, dict[str, str]] = {}
    current_section = "default"

    for raw_line in text.splitlines():
        line = raw_line.strip()

        # Skip blank lines and comments.
        if not line or line[0] in ("#", ";"):
            continue

        # Section header.
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1].strip()
            if current_section not in raw_sections:
                raw_sections[current_section] = {}
            continue

        # Key/value pair — split on first '=' or ':'.
        eq_pos = line.find("=")
        col_pos = line.find(":")
        if eq_pos == -1 and col_pos == -1:
            # Malformed line — ignore.
            continue
        if eq_pos == -1:
            sep = col_pos
        elif col_pos == -1:
            sep = eq_pos
        else:
            sep = min(eq_pos, col_pos)

        key = line[:sep].strip()
        value = line[sep + 1 :].strip()

        if current_section not in raw_sections:
            raw_sections[current_section] = {}
        raw_sections[current_section][key] = value

    # First pass: coerce all values.
    parsed: dict[str, dict[str, object]] = {}
    for section, kvs in raw_sections.items():
        parsed[section] = {}
        for key, raw_val in kvs.items():
            parsed[section][key] = _coerce(raw_val)

    # Second pass: expand string values that contain ${...} references.
    for section, kvs in parsed.items():
        for key, val in kvs.items():
            if isinstance(val, str) and "${" in val:
                parsed[section][key] = _resolve(section, key, val, parsed, set())

    return parsed
