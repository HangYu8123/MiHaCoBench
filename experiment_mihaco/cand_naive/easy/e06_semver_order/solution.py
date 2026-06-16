"""
SemVer 2.0.0 precedence tool.
"""

import re
import sys
from functools import cmp_to_key


def parse(version: str) -> dict:
    """
    Parse a version string of the form MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD].

    Returns a dict with keys: major, minor, patch, prerelease, build.
    Raises ValueError on malformed input.
    """
    # Split off build metadata first (first '+')
    if '+' in version:
        idx = version.index('+')
        core_pre = version[:idx]
        build_str = version[idx + 1:]
    else:
        core_pre = version
        build_str = None

    # Split off pre-release (first '-' after the version core)
    # The core is MAJOR.MINOR.PATCH, so find '-' after the third numeric segment
    # We split on '-' but need to distinguish from a dash in the core
    # The core is always MAJOR.MINOR.PATCH with no dashes, so first '-' is prerelease
    if '-' in core_pre:
        idx2 = core_pre.index('-')
        core = core_pre[:idx2]
        pre_str = core_pre[idx2 + 1:]
    else:
        core = core_pre
        pre_str = None

    # Parse the core: must be exactly MAJOR.MINOR.PATCH
    core_parts = core.split('.')
    if len(core_parts) != 3:
        raise ValueError(f"Invalid version core (must be MAJOR.MINOR.PATCH): {version!r}")

    parsed_core = []
    for part in core_parts:
        if part == '':
            raise ValueError(f"Empty core part in version: {version!r}")
        if not re.match(r'^[0-9]+$', part):
            raise ValueError(f"Non-numeric core part {part!r} in version: {version!r}")
        parsed_core.append(int(part))

    major, minor, patch = parsed_core

    # Parse pre-release identifiers
    if pre_str is not None:
        if pre_str == '':
            raise ValueError(f"Empty pre-release section in version: {version!r}")
        prerelease = pre_str.split('.')
        for ident in prerelease:
            if ident == '':
                raise ValueError(f"Empty pre-release identifier in version: {version!r}")
    else:
        prerelease = []

    # Parse build metadata identifiers
    if build_str is not None:
        if build_str == '':
            raise ValueError(f"Empty build metadata section in version: {version!r}")
        build = build_str.split('.')
        for ident in build:
            if ident == '':
                raise ValueError(f"Empty build metadata identifier in version: {version!r}")
    else:
        build = []

    return {
        'major': major,
        'minor': minor,
        'patch': patch,
        'prerelease': prerelease,
        'build': build,
    }


def _is_numeric_identifier(s: str) -> bool:
    """Return True if s consists entirely of digits."""
    return bool(re.match(r'^[0-9]+$', s))


def _compare_prerelease(pre_a: list, pre_b: list) -> int:
    """
    Compare two pre-release identifier lists per SemVer 2.0.0.
    Returns -1, 0, or 1.
    """
    # If one has pre-release and the other doesn't, that's handled outside.
    # This function compares two non-empty lists.
    for i in range(min(len(pre_a), len(pre_b))):
        ia = pre_a[i]
        ib = pre_b[i]
        a_num = _is_numeric_identifier(ia)
        b_num = _is_numeric_identifier(ib)

        if a_num and b_num:
            # Both numeric: compare numerically
            na, nb = int(ia), int(ib)
            if na < nb:
                return -1
            elif na > nb:
                return 1
            # equal, continue
        elif a_num and not b_num:
            # Numeric < alphanumeric
            return -1
        elif not a_num and b_num:
            # Alphanumeric > numeric
            return 1
        else:
            # Both alphanumeric: compare lexically (ASCII)
            if ia < ib:
                return -1
            elif ia > ib:
                return 1
            # equal, continue

    # All common identifiers are equal; longer list wins
    if len(pre_a) < len(pre_b):
        return -1
    elif len(pre_a) > len(pre_b):
        return 1
    return 0


def compare(a: str, b: str) -> int:
    """
    Compare two version strings per SemVer 2.0.0 precedence.
    Returns -1 (a < b), 0 (equal), or 1 (a > b).
    Raises ValueError on malformed input.
    """
    pa = parse(a)
    pb = parse(b)

    # Step 1: Compare major, minor, patch numerically
    for key in ('major', 'minor', 'patch'):
        va, vb = pa[key], pb[key]
        if va < vb:
            return -1
        elif va > vb:
            return 1

    # Step 2: Pre-release precedence
    has_pre_a = len(pa['prerelease']) > 0
    has_pre_b = len(pb['prerelease']) > 0

    if has_pre_a and not has_pre_b:
        # a has pre-release, b doesn't -> a < b
        return -1
    elif not has_pre_a and has_pre_b:
        # b has pre-release, a doesn't -> a > b
        return 1
    elif has_pre_a and has_pre_b:
        return _compare_prerelease(pa['prerelease'], pb['prerelease'])

    # Both have no pre-release (and core is equal)
    return 0


def sort_versions(versions: list) -> list:
    """
    Return a new list of the same strings sorted ascending by SemVer precedence.
    Stable sort: versions of equal precedence keep their input order.
    Raises ValueError if any version is malformed.
    """
    # Validate all versions first
    for v in versions:
        parse(v)

    def cmp(a, b):
        return compare(a, b)

    return sorted(versions, key=cmp_to_key(cmp))


def main():
    import argparse

    parser = argparse.ArgumentParser(description='SemVer 2.0.0 tool')
    subparsers = parser.add_subparsers(dest='command')

    cmp_parser = subparsers.add_parser('compare', help='Compare two versions')
    cmp_parser.add_argument('A', help='First version')
    cmp_parser.add_argument('B', help='Second version')

    sort_parser = subparsers.add_parser('sort', help='Sort versions')
    sort_parser.add_argument('versions', nargs='+', help='Versions to sort')

    args = parser.parse_args()

    if args.command == 'compare':
        try:
            result = compare(args.A, args.B)
            print(result)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == 'sort':
        try:
            sorted_versions = sort_versions(args.versions)
            for v in sorted_versions:
                print(v)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help(sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
