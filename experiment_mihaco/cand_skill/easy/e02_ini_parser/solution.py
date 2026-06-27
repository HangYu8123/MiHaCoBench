"""
INI-file parser with value coercion and ${section.key} interpolation.
Standard library only; no configparser.
"""

import re


def _coerce(value: str) -> object:
    """Apply the 5-step coercion priority chain to a stripped string value."""
    v = value.strip()

    # 1. Integer: int() succeeds AND round-trip matches (no leading zeros, no dot)
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

    # 3. Bool true
    if v.lower() in {"true", "yes"}:
        return True

    # 4. Bool false
    if v.lower() in {"false", "no"}:
        return False

    # 5. Keep as str
    return v


def _resolve_interpolation(result: dict) -> dict:
    """
    Resolve ${section.key} references in all string values.
    Iterates per-value until stable or cycle detected (raises ValueError).
    """
    # Compute total key count for cycle guard
    total_keys = sum(len(section_dict) for section_dict in result.values())
    max_iters = total_keys + 2  # safe upper bound

    _REF_PATTERN = re.compile(r'\$\{([^}]+)\}')

    for section_name, section_dict in result.items():
        for key in list(section_dict.keys()):
            value = section_dict[key]

            # Only string values may contain interpolation tokens
            if not isinstance(value, str):
                continue

            # Iterate until stable
            for iteration in range(max_iters):
                refs = _REF_PATTERN.findall(value)
                if not refs:
                    break  # stable, no more tokens

                substituted = False
                for ref in refs:
                    parts = ref.split(".", 1)
                    if len(parts) != 2:
                        raise ValueError(
                            "Malformed interpolation reference '${" + ref + "}': "
                            "expected 'section.key' format"
                        )
                    ref_section, ref_key = parts[0], parts[1]

                    if ref_section not in result:
                        raise ValueError(
                            "Interpolation error: section '" + ref_section + "' not found "
                            "(referenced as '${" + ref + "}')"
                        )
                    if ref_key not in result[ref_section]:
                        raise ValueError(
                            "Interpolation error: key '" + ref_key + "' not found in "
                            "section '" + ref_section + "' "
                            "(referenced as '${" + ref + "}')"
                        )

                    resolved = str(result[ref_section][ref_key])
                    placeholder = "${" + ref + "}"
                    value = value.replace(placeholder, resolved)
                    substituted = True

                if not substituted:
                    # refs were found but none were substituted — shouldn't happen
                    break
            else:
                # Exceeded max iterations → cycle
                raise ValueError(
                    f"Interpolation cycle detected for key '{key}' "
                    f"in section '{section_name}'"
                )

            section_dict[key] = value

    return result


def parse_ini(text: str) -> dict[str, dict[str, object]]:
    """
    Parse an INI-format string into a nested dict.

    Returns dict[section_name, dict[key, coerced_value]].
    Pre-section keys go under "default". Last write wins for duplicate keys.
    Raises ValueError on bad interpolation references or cycles.
    """
    result: dict[str, dict[str, object]] = {}
    default_section: dict[str, object] = {}
    current_section_name: str | None = None
    current_section: dict[str, object] = default_section

    for line in text.splitlines():
        stripped = line.strip()

        # Skip blank lines
        if not stripped:
            continue

        # Skip comment lines
        if stripped[0] in ('#', ';'):
            continue

        # Section header
        if stripped.startswith('[') and stripped.endswith(']'):
            section_name = stripped[1:-1].strip()
            current_section_name = section_name
            if section_name not in result:
                result[section_name] = {}
            current_section = result[section_name]
            continue

        # Key/value pair: split on first '=' or ':', whichever comes first
        eq_pos = stripped.find('=')
        co_pos = stripped.find(':')

        candidates = [p for p in [eq_pos, co_pos] if p != -1]
        if not candidates:
            # No separator — skip malformed line
            continue

        sep = min(candidates)
        key = stripped[:sep].strip()
        value_raw = stripped[sep + 1:].strip()

        if not key:
            continue  # malformed key

        coerced = _coerce(value_raw)
        current_section[key] = coerced

    # Attach default section only if it has entries
    if default_section:
        # Merge: if "default" section was also set via [default] header, merge
        # pre-header keys take lower priority (last-write-wins still applies)
        if "default" not in result:
            result["default"] = {}
        # Pre-section keys go in first, then any [default] section keys override
        merged = {**default_section, **result["default"]}
        result["default"] = merged

    # Interpolation pass
    _resolve_interpolation(result)

    return result
