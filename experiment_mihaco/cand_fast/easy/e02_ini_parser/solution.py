"""
INI-file parser with value coercion and interpolation.
"""
import re


def parse_ini(text: str) -> dict[str, dict[str, object]]:
    """
    Parse an INI-format string and return a nested dict of
    {section: {key: coerced_value}}.
    """
    # Step 1: Parse raw key/value pairs per section
    raw: dict[str, dict[str, str]] = {}
    current_section = None

    for line in text.splitlines():
        stripped = line.strip()

        # Skip blank lines and comment lines
        if not stripped:
            continue
        if stripped[0] in ('#', ';'):
            continue

        # Section header
        m = re.fullmatch(r'\[(.+)\]', stripped)
        if m:
            current_section = m.group(1).strip()
            if current_section not in raw:
                raw[current_section] = {}
            continue

        # Key/value pair — find whichever separator (= or :) comes first
        eq_pos = stripped.find('=')
        col_pos = stripped.find(':')

        if eq_pos == -1 and col_pos == -1:
            # No separator — skip line
            continue

        if eq_pos == -1:
            sep_pos = col_pos
        elif col_pos == -1:
            sep_pos = eq_pos
        else:
            sep_pos = min(eq_pos, col_pos)

        key = stripped[:sep_pos].strip()
        value = stripped[sep_pos + 1:].strip()

        section_name = current_section if current_section is not None else "default"
        if section_name not in raw:
            raw[section_name] = {}
        raw[section_name][key] = value

    # Step 2: Coerce values
    def coerce(value: str) -> object:
        # 1. Try int — only if round-trip matches
        _looks_like_int = False
        try:
            int_val = int(value)
            if str(int_val) == value:
                return int_val
            else:
                # Parsed as int but round-trip failed (e.g. "007", "+1", " 3")
                # Mark as int-like to skip float coercion (keep as string)
                _looks_like_int = True
        except (ValueError, OverflowError):
            pass

        # 2. Try float — but skip if it looks like a malformed integer
        if not _looks_like_int:
            try:
                float_val = float(value)
                return float_val
            except (ValueError, OverflowError):
                pass

        # 3. Boolean true
        if value.lower() in ('true', 'yes'):
            return True

        # 4. Boolean false
        if value.lower() in ('false', 'no'):
            return False

        # 5. Keep as string
        return value

    coerced: dict[str, dict[str, object]] = {}
    for section, pairs in raw.items():
        coerced[section] = {}
        for key, val in pairs.items():
            coerced[section][key] = coerce(val)

    # Step 3: Interpolation — only on values that are still str
    _TOKEN_RE = re.compile(r'\$\{([^}]+)\}')

    def resolve(value: str, visited: set) -> str:
        """Iteratively resolve ${section.key} tokens in a string value."""
        for _ in range(1000):
            tokens = _TOKEN_RE.findall(value)
            if not tokens:
                break

            new_value = value
            for token in tokens:
                # Split on first dot only
                parts = token.split('.', 1)
                if len(parts) != 2:
                    raise ValueError(
                        f"Invalid interpolation reference: ${{{token}}}"
                    )
                ref_section, ref_key = parts[0], parts[1]

                if ref_section not in coerced:
                    raise ValueError(
                        f"Interpolation error: section '{ref_section}' not found"
                    )
                if ref_key not in coerced[ref_section]:
                    raise ValueError(
                        f"Interpolation error: key '{ref_key}' not found in section '{ref_section}'"
                    )

                ref_val = coerced[ref_section][ref_key]
                new_value = new_value.replace(f'${{{token}}}', str(ref_val), 1)

            if new_value == value:
                break
            value = new_value
        else:
            # Exhausted iterations without stabilizing — cycle detected
            if _TOKEN_RE.search(value):
                raise ValueError(
                    f"Cycle detected in interpolation: '{value}'"
                )

        return value

    # Apply interpolation to all string values
    for section in coerced:
        for key in coerced[section]:
            val = coerced[section][key]
            if isinstance(val, str):
                coerced[section][key] = resolve(val, set())

    return coerced
