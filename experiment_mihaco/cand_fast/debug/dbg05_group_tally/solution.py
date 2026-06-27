def tally_by_group(label: str, value, groups: dict | None = None) -> dict:
    if groups is None:
        groups = {}
    groups.setdefault(label, []).append(value)
    return groups
