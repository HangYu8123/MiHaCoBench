import re


def parse_ini(text: str) -> dict[str, dict[str, object]]:
    """Parse an INI file string into a nested dict with coercion and interpolation."""
    # Step 1: Parse lines into raw {section -> {key: str_value}} dict
    raw: dict[str, dict[str, str]] = {}
    current_section = "default"

    for line in text.splitlines():
        stripped = line.strip()

        # Skip blank lines
        if not stripped:
            continue

        # Skip comment lines (first non-whitespace char is # or ;)
        if stripped[0] in ('#', ';'):
            continue

        # Section header
        if stripped.startswith('[') and stripped.endswith(']'):
            current_section = stripped[1:-1].strip()
            if current_section not in raw:
                raw[current_section] = {}
            continue

        # Key/value pair: find whichever separator (= or :) comes first
        eq_pos = line.find('=')
        colon_pos = line.find(':')

        # Treat missing separator as effectively infinity
        if eq_pos == -1:
            eq_pos = len(line) + 1
        if colon_pos == -1:
            colon_pos = len(line) + 1

        sep = min(eq_pos, colon_pos)

        # If no separator found, skip this line
        if sep >= len(line):
            continue

        key = line[:sep].strip()
        value = line[sep + 1:].strip()

        if current_section not in raw:
            raw[current_section] = {}
        raw[current_section][key] = value

    # Step 2: Coerce each raw string value
    def coerce(v: str) -> object:
        # Try int first: guard that str(int(v)) == v.strip()
        try:
            int_val = int(v)
            if str(int_val) == v.strip():
                return int_val
        except (ValueError, TypeError):
            pass

        # Try float
        try:
            return float(v)
        except (ValueError, TypeError):
            pass

        # Try bool
        lower_v = v.lower()
        if lower_v in ('true', 'yes'):
            return True
        if lower_v in ('false', 'no'):
            return False

        # Keep as str
        return v

    result: dict[str, dict[str, object]] = {}
    for section, pairs in raw.items():
        result[section] = {}
        for key, val_str in pairs.items():
            result[section][key] = coerce(val_str)

    # Prune empty "default" section (if no keys appeared before first section header)
    if "default" in result and not result["default"]:
        del result["default"]

    # Step 3: Interpolation — only for values that are str
    token_pattern = re.compile(r'\$\{([^}]+)\}')

    def resolve_value(value: str, section_name: str, key_name: str) -> str:
        """Iteratively resolve ${section.key} references in a string value."""
        max_iters = 100
        for _ in range(max_iters):
            tokens = token_pattern.findall(value)
            if not tokens:
                # Stable — no more references
                return value

            old_value = value
            for token in tokens:
                # token should be "section.key"
                parts = token.split('.', 1)
                if len(parts) != 2:
                    raise ValueError(
                        f"Invalid interpolation token '${{{token}}}' in [{section_name}].{key_name}"
                    )
                ref_section, ref_key = parts[0], parts[1]

                if ref_section not in result:
                    raise ValueError(
                        f"Interpolation references non-existent section '{ref_section}' "
                        f"in [{section_name}].{key_name}"
                    )
                if ref_key not in result[ref_section]:
                    raise ValueError(
                        f"Interpolation references non-existent key '{ref_key}' "
                        f"in section '{ref_section}' (referenced from [{section_name}].{key_name})"
                    )

                resolved = result[ref_section][ref_key]
                value = value.replace('${' + token + '}', str(resolved))

            # Check stability
            if value == old_value:
                # No progress made despite tokens found — this shouldn't happen
                # since we resolved tokens above, but guard just in case
                return value

        # If we exhausted iterations, cycle detected
        raise ValueError(
            f"Cycle detected during interpolation in [{section_name}].{key_name}"
        )

    # Apply interpolation to all string values
    for section_name, pairs in result.items():
        for key_name, val in pairs.items():
            if isinstance(val, str):
                result[section_name][key_name] = resolve_value(val, section_name, key_name)

    return result
