"""
SemVer 2.0.0 precedence tool.

Public API:
    parse(version: str) -> dict
    compare(a: str, b: str) -> int
    sort_versions(versions: list[str]) -> list[str]
"""

import sys
from functools import cmp_to_key


def _validate_identifier_not_empty(identifiers: list, context: str) -> None:
    """Raise ValueError if any identifier is empty."""
    for ident in identifiers:
        if ident == "":
            raise ValueError(
                f"Empty identifier in {context}."
            )


def parse(version: str) -> dict:
    """Parse a SemVer 2.0.0 version string into a dict.

    Returns a dict with keys: major, minor, patch, prerelease, build.
    Raises ValueError on malformed input.
    """
    if not version:
        raise ValueError("Empty version string.")

    # Step 1: strip build metadata (everything after first '+')
    if "+" in version:
        rest, _, build_str = version.partition("+")
        if build_str == "":
            raise ValueError(
                f"Empty build metadata section in {version!r}."
            )
        build = build_str.split(".")
        _validate_identifier_not_empty(build, "build metadata")
    else:
        rest = version
        build = []

    # Step 2: strip pre-release (everything after first '-' in what remains)
    if "-" in rest:
        core_str, _, pre_str = rest.partition("-")
        if pre_str == "":
            raise ValueError(
                f"Empty pre-release section in {version!r}."
            )
        prerelease = pre_str.split(".")
        _validate_identifier_not_empty(prerelease, "pre-release")
    else:
        core_str = rest
        prerelease = []

    # Step 3: parse MAJOR.MINOR.PATCH
    core_parts = core_str.split(".")
    if len(core_parts) != 3:
        raise ValueError(
            f"Version core must have exactly 3 parts (MAJOR.MINOR.PATCH), "
            f"got {len(core_parts)} in {version!r}."
        )

    # Validate and convert each core part
    core_values = []
    for part in core_parts:
        if part == "":
            raise ValueError(
                f"Empty core part in {version!r}."
            )
        if not part.isdigit():
            raise ValueError(
                f"Non-numeric core part {part!r} in {version!r}."
            )
        # Reject leading zeros (e.g., "01")
        if len(part) > 1 and part[0] == "0":
            raise ValueError(
                f"Leading zeros in core part {part!r} in {version!r}."
            )
        core_values.append(int(part))

    major, minor, patch = core_values

    # Step 4: validate pre-release identifiers (leading zeros on numeric are forbidden)
    for ident in prerelease:
        if ident.isdigit() and len(ident) > 1 and ident[0] == "0":
            raise ValueError(
                f"Leading zeros in numeric pre-release identifier {ident!r} "
                f"in {version!r}."
            )

    return {
        "major": major,
        "minor": minor,
        "patch": patch,
        "prerelease": prerelease,
        "build": build,
    }


def _cmp(x, y) -> int:
    """Three-way comparison: -1 if x < y, 0 if x == y, 1 if x > y."""
    if x < y:
        return -1
    if x > y:
        return 1
    return 0


def _compare_prerelease(a_pre: list, b_pre: list) -> int:
    """Compare two pre-release identifier lists according to SemVer rules."""
    for a_id, b_id in zip(a_pre, b_pre):
        a_num = a_id.isdigit()
        b_num = b_id.isdigit()

        if a_num and b_num:
            # Both numeric: compare as integers
            result = _cmp(int(a_id), int(b_id))
        elif a_num and not b_num:
            # Numeric < alphanumeric
            result = -1
        elif not a_num and b_num:
            # Alphanumeric > numeric
            result = 1
        else:
            # Both alphanumeric: ASCII lexical comparison
            result = _cmp(a_id, b_id)

        if result != 0:
            return result

    # All common identifiers are equal; the longer list wins
    return _cmp(len(a_pre), len(b_pre))


def compare(a: str, b: str) -> int:
    """Compare two SemVer strings.

    Returns -1 if a < b, 0 if equal precedence, 1 if a > b.
    Raises ValueError if either argument is malformed.
    """
    pa = parse(a)
    pb = parse(b)

    # Step 1: compare major.minor.patch
    for key in ("major", "minor", "patch"):
        result = _cmp(pa[key], pb[key])
        if result != 0:
            return result

    # Step 2: handle pre-release precedence
    a_has_pre = bool(pa["prerelease"])
    b_has_pre = bool(pb["prerelease"])

    if not a_has_pre and not b_has_pre:
        return 0
    if a_has_pre and not b_has_pre:
        # a has pre-release, b does not → a has lower precedence
        return -1
    if not a_has_pre and b_has_pre:
        # b has pre-release, a does not → a has higher precedence
        return 1

    # Both have pre-release
    return _compare_prerelease(pa["prerelease"], pb["prerelease"])


def sort_versions(versions: list) -> list:
    """Return a new list of version strings sorted ascending by SemVer precedence.

    The sort is stable: versions of equal precedence preserve input order.
    Build metadata is preserved verbatim in the returned strings.
    """
    return sorted(versions, key=cmp_to_key(compare))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: solution.py compare A B | sort V1 V2 ...", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "compare":
        if len(sys.argv) != 4:
            print("Usage: solution.py compare A B", file=sys.stderr)
            sys.exit(1)
        a_arg, b_arg = sys.argv[2], sys.argv[3]
        try:
            result = compare(a_arg, b_arg)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(result)

    elif cmd == "sort":
        if len(sys.argv) < 3:
            print("Usage: solution.py sort V1 V2 ...", file=sys.stderr)
            sys.exit(1)
        versions_arg = sys.argv[2:]
        try:
            sorted_versions = sort_versions(versions_arg)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        for v in sorted_versions:
            print(v)

    else:
        print(f"Unknown command: {cmd!r}. Use 'compare' or 'sort'.", file=sys.stderr)
        sys.exit(1)
