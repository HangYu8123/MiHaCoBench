"""Deliberately-broken reference for easy/e06_semver_order.

Planted defect: pre-release identifiers are ALWAYS compared as strings (no
numeric handling). So "11" < "9" lexically, and a purely numeric identifier is
NOT treated as lower precedence than an alphanumeric one. The version core
parsing, build-metadata handling, and "pre-release < release" rule are all
correct, so the module imports and runs cleanly; only the identifier-level
precedence is wrong. This MUST fail the grader (proves the grader discriminates).
"""
from __future__ import annotations

import argparse
import sys


def _split_identifiers(section: str) -> list[str]:
    parts = section.split(".")
    for part in parts:
        if part == "":
            raise ValueError(f"empty identifier in {section!r}")
    return parts


def parse(version: str) -> dict:
    if not isinstance(version, str) or version == "":
        raise ValueError("version must be a non-empty string")

    rest = version
    build: list[str] = []
    if "+" in rest:
        rest, build_section = rest.split("+", 1)
        build = _split_identifiers(build_section)

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


def _cmp(x, y) -> int:
    return (x > y) - (x < y)


def _compare_identifier(a: str, b: str) -> int:
    # BUG: always compare identifiers as raw strings — numeric identifiers are
    # NOT compared numerically and are NOT ranked below alphanumeric ones.
    return _cmp(a, b)


def _compare_prerelease(a: list[str], b: list[str]) -> int:
    if not a and not b:
        return 0
    if not a:
        return 1
    if not b:
        return -1
    for ia, ib in zip(a, b):
        c = _compare_identifier(ia, ib)
        if c != 0:
            return c
    return _cmp(len(a), len(b))


def compare(a: str, b: str) -> int:
    pa = parse(a)
    pb = parse(b)
    for key in ("major", "minor", "patch"):
        c = _cmp(pa[key], pb[key])
        if c != 0:
            return c
    return _compare_prerelease(pa["prerelease"], pb["prerelease"])


def sort_versions(versions: list[str]) -> list[str]:
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
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
