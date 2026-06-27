import re


def parse_ini(text: str) -> dict[str, dict[str, object]]:
    """Parse an INI file and return a dict of sections mapping to dicts of key/value pairs."""
    result: dict[str, dict[str, str]] = {}
    current_section = "default"

    for line in text.splitlines():
        stripped = line.strip()

        # Skip blank lines and comments
        if not stripped or stripped[0] in ('#', ';'):
            continue

        # Section header
        if stripped.startswith('[') and stripped.endswith(']'):
            current_section = stripped[1:-1].strip()
            if current_section not in result:
                result[current_section] = {}
            continue

        # Key/value pair — find first = or :
        eq_pos = stripped.find('=')
        col_pos = stripped.find(':')

        if eq_pos == -1 and col_pos == -1:
            # No separator — skip
            continue

        if eq_pos == -1:
            sep_pos = col_pos
        elif col_pos == -1:
            sep_pos = eq_pos
        else:
            sep_pos = min(eq_pos, col_pos)

        key = stripped[:sep_pos].strip()
        value = stripped[sep_pos + 1:].strip()

        if current_section not in result:
            result[current_section] = {}
        result[current_section][key] = value

    # Coerce values
    coerced: dict[str, dict[str, object]] = {}
    for section, kv in result.items():
        coerced[section] = {}
        for key, value in kv.items():
            coerced[section][key] = _coerce(value)

    # Interpolation
    _interpolate_all(coerced)

    return coerced


def _coerce(value: str) -> object:
    """Coerce a string value to int, float, bool, or str."""
    # Try int
    try:
        int_val = int(value)
        if str(int_val) == value.strip():
            return int_val
    except (ValueError, TypeError):
        pass

    # Try float
    try:
        return float(value)
    except (ValueError, TypeError):
        pass

    # Try bool
    if value.lower() in ('true', 'yes'):
        return True
    if value.lower() in ('false', 'no'):
        return False

    return value


_REF_PATTERN = re.compile(r'\$\{([^}]+)\}')


def _interpolate_all(data: dict[str, dict[str, object]]) -> None:
    """Resolve all ${section.key} references in-place."""
    # We need to resolve references in string values
    for section in data:
        for key in data[section]:
            if isinstance(data[section][key], str):
                data[section][key] = _resolve(data, section, key, set())


def _resolve(data: dict[str, dict[str, object]], section: str, key: str, visiting: set) -> object:
    """Resolve interpolation for a single key, detecting cycles."""
    value = data[section][key]
    if not isinstance(value, str):
        return value

    node = (section, key)
    if node in visiting:
        raise ValueError(f"Cycle detected in interpolation: {section}.{key}")

    visiting = visiting | {node}

    def replace_ref(match):
        ref = match.group(1)
        parts = ref.split('.', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid interpolation reference: ${{{ref}}}")
        ref_section, ref_key = parts[0].strip(), parts[1].strip()
        if ref_section not in data:
            raise ValueError(f"Unknown section in interpolation: {ref_section}")
        if ref_key not in data[ref_section]:
            raise ValueError(f"Unknown key in interpolation: {ref_section}.{ref_key}")
        # Recursively resolve the referenced value first
        resolved = _resolve(data, ref_section, ref_key, visiting)
        # Update the stored value so it's memoized
        data[ref_section][ref_key] = resolved
        return str(resolved)

    # Iteratively resolve until stable
    max_iterations = 1000
    for _ in range(max_iterations):
        if _REF_PATTERN.search(value) is None:
            break
        value = _REF_PATTERN.sub(replace_ref, value)
    else:
        raise ValueError(f"Interpolation did not terminate for {section}.{key}")

    return value
