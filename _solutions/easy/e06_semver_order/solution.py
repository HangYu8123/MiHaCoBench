"""Gold reference for easy/e06_semver_order — SemVer 2.0.0 precedence (stdlib only)."""
from __future__ import annotations

import argparse
import sys


def _split_identifiers(section: str) -> list[str]:
    """Split a dot-separated section, raising ValueError on any empty identifier."""
    parts = section.split(".")
    for part in parts:
        if part == "":
            raise ValueError(f"empty identifier in {section!r}")
    return parts


def parse(version: str) -> dict:
    """Parse ``MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`` into its components.

    Raises ``ValueError`` for any malformed version (see TASK.md).
    """
    if not isinstance(version, str) or version == "":
        raise ValueError("version must be a non-empty string")

    rest = version
    # Build metadata is introduced by the FIRST '+'.
    build: list[str] = []
    if "+" in rest:
        rest, build_section = rest.split("+", 1)
        build = _split_identifiers(build_section)

    # Pre-release is introduced by the FIRST '-' in what remains.
    prerelease: list[str] = []
    if "-" in rest:
        core_section, pre_section = rest.split("-", 1)
        prerelease = _split_identifiers(pre_section)
    else:
        core_section = rest

    core_parts = core_section.split(".")
    if len(core_parts) != 3:
        raise ValueError(f"version core must have 3 parts: {core_section!r}")
    nums = []
    for part in core_parts:
        if part == "" or not part.isdigit():
            raise ValueError(f"non-numeric version core part: {part!r}")
        nums.append(int(part))

    return {
        "major": nums[0],
        "minor": nums[1],
        "patch": nums[2],
        "prerelease": prerelease,
        "build": build,
    }


def _cmp(x: int, y: int) -> int:
    return (x > y) - (x < y)


def _compare_identifier(a: str, b: str) -> int:
    """Compare two pre-release identifiers per SemVer rule 11.4."""
    a_num = a.isdigit()
    b_num = b.isdigit()
    if a_num and b_num:
        return _cmp(int(a), int(b))  # numeric identifiers compared numerically
    if a_num and not b_num:
        return -1  # numeric has lower precedence than alphanumeric
    if not a_num and b_num:
        return 1
    return _cmp((a > b) - (a < b), 0)  # both alphanumeric → ASCII lexical


def _compare_prerelease(a: list[str], b: list[str]) -> int:
    """Compare two (non-empty-equivalent) pre-release identifier lists."""
    # A version WITH a pre-release is lower than one WITHOUT.
    if not a and not b:
        return 0
    if not a:
        return 1  # a has no pre-release → higher precedence
    if not b:
        return -1
    for ia, ib in zip(a, b):
        c = _compare_identifier(ia, ib)
        if c != 0:
            return c
    # All shared identifiers equal → the longer list wins.
    return _cmp(len(a), len(b))


def compare(a: str, b: str) -> int:
    """Return -1/0/1 comparing ``a`` and ``b`` by SemVer 2.0.0 precedence."""
    pa = parse(a)
    pb = parse(b)
    for key in ("major", "minor", "patch"):
        c = _cmp(pa[key], pb[key])
        if c != 0:
            return c
    return _compare_prerelease(pa["prerelease"], pb["prerelease"])


def _precedence_key(version: str):
    """A key usable with cmp_to_key-style comparison; here we delegate to compare."""
    return version


def sort_versions(versions: list[str]) -> list[str]:
    """Return ``versions`` sorted ascending by precedence (stable; strings preserved)."""
    import functools

    return sorted(versions, key=functools.cmp_to_key(compare))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SemVer 2.0.0 precedence tool.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("a")
    p_cmp.add_argument("b")

    p_sort = sub.add_parser("sort")
    p_sort.add_argument("versions", nargs="+")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "compare":
            print(compare(args.a, args.b))
            return 0
        if args.cmd == "sort":
            for v in sort_versions(args.versions):
                print(v)
            return 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2  # pragma: no cover - argparse enforces a subcommand


if __name__ == "__main__":
    raise SystemExit(main())
