"""
SemVer 2.0.0 precedence implementation.

Public API:
  parse(version: str) -> dict
  compare(a: str, b: str) -> int
  sort_versions(versions: list[str]) -> list[str]

CLI:
  python solution.py compare A B
  python solution.py sort V1 V2 ...
"""

import re
import sys
from functools import cmp_to_key

_DIGIT_ONLY = re.compile(r'^[0-9]+$')


def _parse_identifiers(s: str, context: str) -> list:
    """Split s on '.' and validate each identifier is non-empty."""
    if not s:
        raise ValueError(f"Empty {context} section")
    parts = s.split('.')
    for p in parts:
        if not p:
            raise ValueError(f"Empty identifier in {context}: {s!r}")
    return parts


def parse(version: str) -> dict:
    """
    Parse a SemVer string and return a dict with keys:
      major (int), minor (int), patch (int),
      prerelease (list[str]), build (list[str])
    Raises ValueError for malformed input.
    """
    # Step 1: separate build metadata (split on first '+')
    if '+' in version:
        core_and_pre, build_str = version.split('+', 1)
        build = _parse_identifiers(build_str, 'build')
    else:
        core_and_pre = version
        build = []

    # Step 2: separate prerelease (split on first '-')
    if '-' in core_and_pre:
        core_str, pre_str = core_and_pre.split('-', 1)
        prerelease = _parse_identifiers(pre_str, 'prerelease')
    else:
        core_str = core_and_pre
        prerelease = []

    # Step 3: parse the numeric core (MAJOR.MINOR.PATCH)
    core_parts = core_str.split('.')
    if len(core_parts) != 3:
        raise ValueError(
            f"Version core must have exactly 3 parts, got {len(core_parts)}: {core_str!r}"
        )
    major_s, minor_s, patch_s = core_parts
    for label, s in (('major', major_s), ('minor', minor_s), ('patch', patch_s)):
        if not s:
            raise ValueError(f"Empty {label} in version core: {version!r}")
        if not _DIGIT_ONLY.match(s):
            raise ValueError(
                f"Non-numeric {label} in version core: {s!r}"
            )

    return {
        'major': int(major_s),
        'minor': int(minor_s),
        'patch': int(patch_s),
        'prerelease': prerelease,
        'build': build,
    }


def _id_key(ident: str):
    """
    Return a comparable key for a single prerelease identifier.
    Numeric identifiers sort before alphanumeric ones.
    """
    if _DIGIT_ONLY.fullmatch(ident):
        return (0, int(ident), '')
    return (1, 0, ident)


def compare(a: str, b: str) -> int:
    """
    Compare two version strings by SemVer 2.0.0 precedence.
    Returns -1, 0, or 1. Build metadata is ignored.
    Raises ValueError if either argument is malformed.
    """
    pa = parse(a)
    pb = parse(b)

    # Compare numeric core
    for key in ('major', 'minor', 'patch'):
        va, vb = pa[key], pb[key]
        if va < vb:
            return -1
        if va > vb:
            return 1

    # Prerelease comparison
    pre_a = pa['prerelease']
    pre_b = pb['prerelease']

    # A version without prerelease has higher precedence than one with
    has_pre_a = len(pre_a) > 0
    has_pre_b = len(pre_b) > 0

    if has_pre_a and not has_pre_b:
        return -1
    if not has_pre_a and has_pre_b:
        return 1
    if not has_pre_a and not has_pre_b:
        return 0

    # Both have prerelease: compare identifier by identifier
    for id_a, id_b in zip(pre_a, pre_b):
        ka = _id_key(id_a)
        kb = _id_key(id_b)
        if ka < kb:
            return -1
        if ka > kb:
            return 1

    # All shared identifiers equal: more identifiers = higher precedence
    if len(pre_a) < len(pre_b):
        return -1
    if len(pre_a) > len(pre_b):
        return 1

    return 0


def sort_versions(versions: list) -> list:
    """
    Return a new list of version strings sorted ascending by SemVer precedence.
    Stable: versions of equal precedence preserve input order.
    """
    return sorted(versions, key=cmp_to_key(compare))


def _main():
    argv = sys.argv[1:]
    if not argv:
        print("Usage: solution.py compare A B | sort V1 V2 ...", file=sys.stderr)
        sys.exit(1)

    subcommand = argv[0]

    if subcommand == 'compare':
        if len(argv) != 3:
            print("Usage: solution.py compare A B", file=sys.stderr)
            sys.exit(1)
        try:
            result = compare(argv[1], argv[2])
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        print(result)

    elif subcommand == 'sort':
        if len(argv) < 2:
            print("Usage: solution.py sort V1 V2 ...", file=sys.stderr)
            sys.exit(1)
        versions = argv[1:]
        try:
            sorted_versions = sort_versions(versions)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        for v in sorted_versions:
            print(v)

    else:
        print(f"Unknown subcommand: {subcommand!r}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    _main()
