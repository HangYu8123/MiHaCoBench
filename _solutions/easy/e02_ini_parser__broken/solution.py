"""Deliberately-broken reference for easy/e02_ini_parser.

Two planted defects:
  1. Does NOT perform interpolation — ${section.key} references are left as
     literal strings instead of being expanded.  This fails the interpolation
     success test and the missing-reference ValueError test.
  2. Mis-coerces booleans: only "true"/"false" are recognised; "yes"/"no" are
     left as strings.  This fails the bool coercion test for "yes"/"no".
"""
from __future__ import annotations


def _coerce(value: str) -> object:
    """Coerce value — BUG: 'yes'/'no' not treated as bool."""
    try:
        iv = int(value)
        if str(iv) == value:
            return iv
    except (ValueError, TypeError):
        pass
    try:
        return float(value)
    except (ValueError, TypeError):
        pass
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    # BUG: 'yes' and 'no' fall through and remain as strings.
    return value


def parse_ini(text: str) -> dict[str, dict[str, object]]:
    """Parse INI text — BUG: no interpolation performed."""
    raw_sections: dict[str, dict[str, str]] = {}
    current_section = "default"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line[0] in ("#", ";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1].strip()
            if current_section not in raw_sections:
                raw_sections[current_section] = {}
            continue
        eq_pos = line.find("=")
        col_pos = line.find(":")
        if eq_pos == -1 and col_pos == -1:
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

    # Coerce but NO interpolation step.
    parsed: dict[str, dict[str, object]] = {}
    for section, kvs in raw_sections.items():
        parsed[section] = {}
        for key, raw_val in kvs.items():
            parsed[section][key] = _coerce(raw_val)

    # BUG: interpolation expansion is deliberately omitted.
    return parsed
