#!/usr/bin/env python3
"""Per-arm token attribution for the MiHaCoBench harness experiment.

The workflow subagents' .meta.json files do not carry the EXP-<arm>-<role>
labels, but each transcript's first user message (the agent prompt) contains a
distinctive role marker. We classify every agent-*.jsonl transcript into an
(arm, role) by that marker and sum the real per-turn token usage.

Usage:
    python3 experiment_mihaco/_tokscan.py <workflow_transcript_dir> [--out tokens.json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

USAGE_KEYS = ("input_tokens", "output_tokens",
              "cache_creation_input_tokens", "cache_read_input_tokens")

# Ordered (marker -> (arm, role)); first match wins.
RULES = [
    ("no-harness baseline", ("naive", "impl")),
    ("general-harness implementer (revision)", ("general", "revise")),
    ("general-harness implementer", ("general", "impl")),
    ("fast-harness implementer", ("fast", "impl")),
    ("Focus Analyst", ("general", "focus")),
    ("Broad Analyst", ("general", "broad")),
    ("Free Analyst", ("general", "free")),
    ("Senior Engineer. Three analysts", ("general", "senior")),
    ("QA Engineer", ("general", "qa")),
    ("Critically challenge the [final plan]", ("general", "devil")),
    ("Verify the correct current library APIs", ("general", "research")),
    ("anticipate how a naive implementation", ("fast", "devil")),
    ("best-practice patterns needed to implement THIS task", ("fast", "research")),
]


def classify(text: str):
    low = text.lower()
    for marker, tag in RULES:
        if marker.lower() in low:   # case-insensitive: tolerate prompt-casing drift
            return tag
    return ("UNKNOWN", "UNKNOWN")


def file_usage_and_text(path: Path):
    usage = {k: 0 for k in USAGE_KEYS}
    turns = 0
    chunks = []
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = obj.get("message")
        if isinstance(msg, dict):
            u = msg.get("usage")
            if isinstance(u, dict):
                for k in USAGE_KEYS:
                    usage[k] += int(u.get(k, 0) or 0)
                turns += 1
            content = msg.get("content")
            if isinstance(content, str):
                chunks.append(content)
            elif isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and isinstance(c.get("text"), str):
                        chunks.append(c["text"])
    usage["turns"] = turns
    usage["total_tokens"] = sum(usage[k] for k in USAGE_KEYS)
    return usage, "\n".join(chunks)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript_dir")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    arms: dict[str, dict] = {}
    roles: dict[str, dict] = {}
    files = []
    for jsonl in sorted(Path(args.transcript_dir).glob("agent-*.jsonl")):
        usage, text = file_usage_and_text(jsonl)
        arm, role = classify(text)
        for bucket, key in ((arms, arm), (roles, f"{arm}:{role}")):
            d = bucket.setdefault(key, {k: 0 for k in USAGE_KEYS} | {"turns": 0, "count": 0})
            for k in USAGE_KEYS:
                d[k] += usage[k]
            d["turns"] += usage["turns"]
            d["count"] += 1
        files.append({"file": jsonl.name, "arm": arm, "role": role,
                      "total_tokens": usage["total_tokens"], "output_tokens": usage["output_tokens"]})
    for d in list(arms.values()) + list(roles.values()):
        d["total_tokens"] = sum(d[k] for k in USAGE_KEYS)

    order = ["naive", "fast", "general", "UNKNOWN"]
    print(f"{'arm':<10}{'subagents':>10}{'turns':>8}{'output':>12}{'cache_read':>14}{'TOTAL':>14}")
    grand = 0
    for arm in order:
        if arm not in arms:
            continue
        d = arms[arm]
        grand += d["total_tokens"]
        print(f"{arm:<10}{d['count']:>10}{d['turns']:>8}{d['output_tokens']:>12,}"
              f"{d['cache_read_input_tokens']:>14,}{d['total_tokens']:>14,}")
    print(f"{'GRAND':<10}{sum(a['count'] for a in arms.values()):>10}"
          f"{'':>8}{'':>12}{'':>14}{grand:>14,}")

    if "naive" in arms and arms["naive"]["total_tokens"]:
        base = arms["naive"]["total_tokens"]
        print("\nToken multiple vs naive:")
        for arm in ["naive", "fast", "general"]:
            if arm in arms:
                print(f"  {arm:<8} {arms[arm]['total_tokens'] / base:.2f}x")

    out = {"arms": arms, "roles": roles, "files": files, "grand_total_tokens": grand}
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2))
        print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
