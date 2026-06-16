"""
Semantic-version precedence tool (SemVer 2.0.0).

Public API:
    parse(version: str) -> dict
    compare(a: str, b: str) -> int
    sort_versions(versions: list[str]) -> list[str]

CLI:
    python solution.py compare A B
    python solution.py sort V1 V2 ...
"""

import sys
import argparse
import functools


def parse(version: str) -> dict:
    """Parse a SemVer 2.0.0 version string into a dict.

    Returns dict with keys: major, minor, patch, prerelease, build.
    Raises ValueError on malformed input.
    """
    if not isinstance(version, str):
        raise ValueError(f"version must be a string, got {type(version)}")

    # Step 1: Strip build metadata (everything after the first '+')
    if '+' in version:
        core_and_pre, build_str = version.split('+', 1)
        if not build_str:
            raise ValueError(f"Empty build metadata in {version!r}")
        build_parts = build_str.split('.')
        for ident in build_parts:
            if not ident:
                raise ValueError(f"Empty build identifier in {version!r}")
    else:
        core_and_pre = version
        build_parts = []

    # Step 2: Strip pre-release (everything after the first '-' in core_and_pre)
    if '-' in core_and_pre:
        core_str, pre_str = core_and_pre.split('-', 1)
        if not pre_str:
            raise ValueError(f"Empty pre-release section in {version!r}")
        pre_parts = pre_str.split('.')
        for ident in pre_parts:
            if not ident:
                raise ValueError(f"Empty pre-release identifier in {version!r}")
            # Check for leading zeros in purely numeric identifiers
            if ident.isdigit() and len(ident) > 1 and ident[0] == '0':
                raise ValueError(
                    f"Leading zero in numeric pre-release identifier {ident!r} in {version!r}"
                )
    else:
        core_str = core_and_pre
        pre_parts = []

    # Step 3: Parse the core (MAJOR.MINOR.PATCH)
    core_pieces = core_str.split('.')
    if len(core_pieces) != 3:
        raise ValueError(
            f"Version core must have exactly 3 parts (MAJOR.MINOR.PATCH), got {core_str!r}"
        )

    major_str, minor_str, patch_str = core_pieces

    for label, val in (('major', major_str), ('minor', minor_str), ('patch', patch_str)):
        if not val:
            raise ValueError(f"Empty {label} part in {version!r}")
        if not val.isdigit():
            raise ValueError(f"Non-numeric {label} part {val!r} in {version!r}")
        # Check for leading zeros
        if len(val) > 1 and val[0] == '0':
            raise ValueError(f"Leading zero in {label} part {val!r} in {version!r}")

    return {
        'major': int(major_str),
        'minor': int(minor_str),
        'patch': int(patch_str),
        'prerelease': pre_parts,
        'build': build_parts,
    }


def _compare_pre(pre_a: list, pre_b: list) -> int:
    """Compare two pre-release identifier lists per SemVer 2.0.0 rules.

    Returns -1, 0, or 1.
    """
    # Compare pairwise
    for a_ident, b_ident in zip(pre_a, pre_b):
        a_numeric = a_ident.isdigit()
        b_numeric = b_ident.isdigit()

        if a_numeric and b_numeric:
            # Both purely numeric: compare as integers
            a_val = int(a_ident)
            b_val = int(b_ident)
            if a_val < b_val:
                return -1
            if a_val > b_val:
                return 1
        elif not a_numeric and not b_numeric:
            # Both alphanumeric: compare as ASCII strings
            if a_ident < b_ident:
                return -1
            if a_ident > b_ident:
                return 1
        else:
            # Mixed: numeric has LOWER precedence than alphanumeric
            if a_numeric:
                return -1  # a is numeric (lower), b is alphanumeric (higher)
            else:
                return 1   # b is numeric (lower), a is alphanumeric (higher)

    # All shared identifiers are equal; more identifiers = higher precedence
    if len(pre_a) < len(pre_b):
        return -1
    if len(pre_a) > len(pre_b):
        return 1
    return 0


def compare(a: str, b: str) -> int:
    """Compare two SemVer version strings.

    Returns -1 if a < b, 0 if a == b, 1 if a > b (by precedence).
    Build metadata is ignored.
    Raises ValueError on malformed input.
    """
    pa = parse(a)
    pb = parse(b)

    # Step 1: Compare major.minor.patch numerically
    core_a = (pa['major'], pa['minor'], pa['patch'])
    core_b = (pb['major'], pb['minor'], pb['patch'])

    if core_a < core_b:
        return -1
    if core_a > core_b:
        return 1

    # Step 2: Pre-release comparison
    pre_a = pa['prerelease']
    pre_b = pb['prerelease']

    # A version WITH pre-release < same version WITHOUT pre-release
    if pre_a and not pre_b:
        return -1
    if not pre_a and pre_b:
        return 1
    if not pre_a and not pre_b:
        return 0

    # Both have pre-release: compare identifiers
    return _compare_pre(pre_a, pre_b)


def sort_versions(versions: list) -> list:
    """Sort a list of version strings ascending by SemVer 2.0.0 precedence.

    Returns a new list with original strings preserved verbatim.
    Sort is stable: versions of equal precedence retain their input order.
    Raises ValueError if any version is malformed.
    """
    return sorted(versions, key=functools.cmp_to_key(compare))


def main():
    parser = argparse.ArgumentParser(description='SemVer 2.0.0 tool')
    subparsers = parser.add_subparsers(dest='command')

    # compare subcommand
    compare_parser = subparsers.add_parser('compare', help='Compare two versions')
    compare_parser.add_argument('a', help='First version')
    compare_parser.add_argument('b', help='Second version')

    # sort subcommand
    sort_parser = subparsers.add_parser('sort', help='Sort versions')
    sort_parser.add_argument('versions', nargs='+', help='Versions to sort')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    try:
        if args.command == 'compare':
            result = compare(args.a, args.b)
            print(result)
        elif args.command == 'sort':
            sorted_versions = sort_versions(args.versions)
            for v in sorted_versions:
                print(v)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
