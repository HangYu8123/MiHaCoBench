import re


def parse_ini(text: str) -> dict[str, dict[str, object]]:
    """Parse an INI-format string and return a dict of sections to key/value dicts.

    Structural rules:
    - Sections: [name]
    - Key/value pairs: key = value or key : value (first separator wins)
    - Comments: lines starting with # or ; (after stripping)
    - Blank lines are ignored
    - Keys before any section go into "default"
    - Duplicate keys: last value wins

    Value coercion (in order):
    1. int (if str(int(v)) == v.strip())
    2. float
    3. bool: true/yes -> True, false/no -> False
    4. str

    Interpolation:
    - String values may contain ${section.key} references
    - Resolved iteratively until stable
    - ValueError on missing section/key or cycle
    """
    result: dict[str, dict[str, object]] = {}
    current_section = "default"

    for line in text.splitlines():
        stripped = line.strip()

        # Skip blank lines
        if not stripped:
            continue

        # Skip comments
        if stripped[0] in ('#', ';'):
            continue

        # Check for section header
        if stripped.startswith('[') and stripped.endswith(']'):
            section_name = stripped[1:-1].strip()
            current_section = section_name
            if current_section not in result:
                result[current_section] = {}
            continue

        # Key/value pair: find first = or :
        eq_pos = stripped.find('=')
        colon_pos = stripped.find(':')

        if eq_pos == -1 and colon_pos == -1:
            # No separator found, skip line
            continue

        if eq_pos == -1:
            sep_pos = colon_pos
        elif colon_pos == -1:
            sep_pos = eq_pos
        else:
            sep_pos = min(eq_pos, colon_pos)

        key = stripped[:sep_pos].strip()
        value_str = stripped[sep_pos + 1:].strip()

        if current_section not in result:
            result[current_section] = {}

        result[current_section][key] = _coerce(value_str)

    # Perform interpolation on all string values
    _interpolate_all(result)

    return result


def _coerce(value: str) -> object:
    """Apply value coercion in the specified order."""
    stripped = value.strip()

    # 1. Try int
    try:
        int_val = int(stripped)
        if str(int_val) == stripped:
            return int_val
    except (ValueError, OverflowError):
        pass

    # 2. Try float
    try:
        float_val = float(stripped)
        return float_val
    except (ValueError, OverflowError):
        pass

    # 3. Bool true/yes
    if stripped.lower() in ('true', 'yes'):
        return True

    # 4. Bool false/no
    if stripped.lower() in ('false', 'no'):
        return False

    # 5. Keep as str
    return stripped


_INTERP_RE = re.compile(r'\$\{([^}]+)\}')


def _interpolate_all(result: dict[str, dict[str, object]]) -> None:
    """Resolve ${section.key} interpolation for all string values in-place."""
    # We need to resolve references; iterate over all string values
    # and resolve them using the full result dict.
    # We do this iteratively with a visited set to detect cycles.

    for section in result:
        for key in result[section]:
            if isinstance(result[section][key], str):
                result[section][key] = _resolve(result, section, key, set())


def _resolve(result: dict, section: str, key: str, visiting: set) -> object:
    """Resolve the value at result[section][key], following ${...} references."""
    ref_key = (section, key)
    if ref_key in visiting:
        raise ValueError(f"Cycle detected at ${{{section}.{key}}}")

    value = result[section][key]

    if not isinstance(value, str):
        return value

    if not _INTERP_RE.search(value):
        return value

    visiting = visiting | {ref_key}

    # Iterative resolution to handle chained references
    max_iterations = 1000
    for _ in range(max_iterations):
        if not isinstance(value, str) or not _INTERP_RE.search(value):
            break

        def replace_ref(m):
            ref = m.group(1)
            parts = ref.split('.', 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid interpolation reference: ${{{ref}}}")
            ref_section, ref_key_name = parts[0].strip(), parts[1].strip()

            if ref_section not in result:
                raise ValueError(f"Unknown section '{ref_section}' in interpolation ${{{ref}}}")
            if ref_key_name not in result[ref_section]:
                raise ValueError(f"Unknown key '{ref_key_name}' in section '{ref_section}' in interpolation ${{{ref}}}")

            # Check for cycle
            if (ref_section, ref_key_name) in visiting:
                raise ValueError(f"Cycle detected at ${{{ref_section}.{ref_key_name}}}")

            # Recursively resolve the referenced value
            resolved = _resolve(result, ref_section, ref_key_name, visiting)
            return str(resolved)

        new_value = _INTERP_RE.sub(replace_ref, value)
        if new_value == value:
            break
        value = new_value
    else:
        raise ValueError("Interpolation did not terminate (possible cycle)")

    return value
