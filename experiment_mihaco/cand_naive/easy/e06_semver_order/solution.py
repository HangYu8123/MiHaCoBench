"""
SemVer 2.0.0 implementation — Easy 06 semver_order
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
        plus_idx = version.index('+')
        build_str = version[plus_idx + 1:]
        version_without_build = version[:plus_idx]
    else:
        build_str = None
        version_without_build = version

    # Split off pre-release (first '-' after the core)
    # We need to find the '-' that separates core from pre-release.
    # The core is MAJOR.MINOR.PATCH — find the first '-' after the core.
    # Strategy: find the first '-' that is NOT inside the core numeric portion.
    # The core must match \d+\.\d+\.\d+ so find that first.

    core_match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version_without_build)
    if not core_match:
        raise ValueError(f"Malformed version (invalid core): {version!r}")

    core_end = core_match.end()
    remainder_after_core = version_without_build[core_end:]

    if remainder_after_core == '':
        prerelease_str = None
    elif remainder_after_core.startswith('-'):
        prerelease_str = remainder_after_core[1:]
    else:
        raise ValueError(f"Malformed version (unexpected characters after core): {version!r}")

    # Validate core parts (no leading zeros per strict SemVer, but spec says
    # "non-numeric core part" — let's also check for leading zeros)
    major_str, minor_str, patch_str = core_match.group(1), core_match.group(2), core_match.group(3)

    # Check for leading zeros (SemVer disallows them for numeric identifiers)
    # The spec says raise on "non-numeric core part" — leading zeros are not mentioned,
    # but SemVer 2.0.0 forbids them. We'll be strict.
    for part_str, name in [(major_str, 'major'), (minor_str, 'minor'), (patch_str, 'patch')]:
        if len(part_str) > 1 and part_str[0] == '0':
            raise ValueError(f"Malformed version (leading zero in {name}): {version!r}")

    major = int(major_str)
    minor = int(minor_str)
    patch = int(patch_str)

    # Parse pre-release identifiers
    if prerelease_str is None:
        prerelease = []
    else:
        if prerelease_str == '':
            raise ValueError(f"Malformed version (empty pre-release): {version!r}")
        prerelease = prerelease_str.split('.')
        for ident in prerelease:
            if ident == '':
                raise ValueError(f"Malformed version (empty pre-release identifier): {version!r}")
            # Validate: only alphanumerics and hyphens allowed
            if not re.match(r'^[0-9A-Za-z-]+$', ident):
                raise ValueError(f"Malformed version (invalid pre-release identifier {ident!r}): {version!r}")
            # Numeric identifiers must not have leading zeros
            if re.match(r'^[0-9]+$', ident) and len(ident) > 1 and ident[0] == '0':
                raise ValueError(f"Malformed version (leading zero in numeric pre-release identifier {ident!r}): {version!r}")

    # Parse build metadata identifiers
    if build_str is None:
        build = []
    else:
        if build_str == '':
            raise ValueError(f"Malformed version (empty build metadata): {version!r}")
        build = build_str.split('.')
        for ident in build:
            if ident == '':
                raise ValueError(f"Malformed version (empty build metadata identifier): {version!r}")
            # Validate: only alphanumerics and hyphens allowed
            if not re.match(r'^[0-9A-Za-z-]+$', ident):
                raise ValueError(f"Malformed version (invalid build identifier {ident!r}): {version!r}")

    return {
        'major': major,
        'minor': minor,
        'patch': patch,
        'prerelease': prerelease,
        'build': build,
    }


def _compare_prerelease_ident(a_ident: str, b_ident: str) -> int:
    """Compare two pre-release identifiers per SemVer rules."""
    a_is_numeric = re.match(r'^[0-9]+$', a_ident) is not None
    b_is_numeric = re.match(r'^[0-9]+$', b_ident) is not None

    if a_is_numeric and b_is_numeric:
        # Numeric comparison
        ai, bi = int(a_ident), int(b_ident)
        if ai < bi:
            return -1
        elif ai > bi:
            return 1
        return 0
    elif a_is_numeric and not b_is_numeric:
        # Numeric < alphanumeric
        return -1
    elif not a_is_numeric and b_is_numeric:
        # Alphanumeric > numeric
        return 1
    else:
        # Both alphanumeric: ASCII lexical comparison
        if a_ident < b_ident:
            return -1
        elif a_ident > b_ident:
            return 1
        return 0


def compare(a: str, b: str) -> int:
    """
    Compare two version strings per SemVer 2.0.0 precedence.
    Returns -1, 0, or 1.
    Raises ValueError if either is malformed.
    """
    pa = parse(a)
    pb = parse(b)

    # 1. Compare major, minor, patch numerically
    for key in ('major', 'minor', 'patch'):
        if pa[key] < pb[key]:
            return -1
        elif pa[key] > pb[key]:
            return 1

    # 2. Pre-release presence: with pre-release < without pre-release
    a_has_pre = len(pa['prerelease']) > 0
    b_has_pre = len(pb['prerelease']) > 0

    if a_has_pre and not b_has_pre:
        return -1
    elif not a_has_pre and b_has_pre:
        return 1
    elif not a_has_pre and not b_has_pre:
        return 0

    # 3. Both have pre-release: compare identifier by identifier
    a_pre = pa['prerelease']
    b_pre = pb['prerelease']

    min_len = min(len(a_pre), len(b_pre))
    for i in range(min_len):
        result = _compare_prerelease_ident(a_pre[i], b_pre[i])
        if result != 0:
            return result

    # All shared identifiers equal: more identifiers = higher precedence
    if len(a_pre) < len(b_pre):
        return -1
    elif len(a_pre) > len(b_pre):
        return 1
    return 0


def sort_versions(versions: list) -> list:
    """
    Return a new list of version strings sorted ascending by SemVer precedence.
    Stable: equal-precedence versions keep their input order.
    """
    # Validate all versions first (parse raises ValueError on bad input)
    for v in versions:
        parse(v)

    def cmp(a, b):
        return compare(a, b)

    return sorted(versions, key=cmp_to_key(cmp))


def main():
    import argparse

    parser = argparse.ArgumentParser(description='SemVer 2.0.0 tool')
    subparsers = parser.add_subparsers(dest='command')

    compare_parser = subparsers.add_parser('compare')
    compare_parser.add_argument('A')
    compare_parser.add_argument('B')

    sort_parser = subparsers.add_parser('sort')
    sort_parser.add_argument('versions', nargs='+')

    args = parser.parse_args()

    if args.command == 'compare':
        try:
            result = compare(args.A, args.B)
            print(result)
            sys.exit(0)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == 'sort':
        try:
            sorted_versions = sort_versions(args.versions)
            for v in sorted_versions:
                print(v)
            sys.exit(0)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help(sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
