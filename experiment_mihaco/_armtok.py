#!/usr/bin/env python3
"""Per-arm token attribution for the full-79 naive/fast/skill run.

Classifies every agent-*.jsonl transcript by ARM via the prompt marker
(no-harness baseline | FAST-harness | SKILL-harness) and sums real per-turn
usage (input+output+cache). Also breaks down by subagent role.

Usage: python3 _armtok.py <transcript_dir> [<transcript_dir> ...]
"""
import json, sys
from pathlib import Path

USAGE = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")

def arm_of(text):
    t = text.lower()
    if "no-harness baseline" in t: return "naive"
    if "skill-harness" in t: return "skill"
    if "fast-harness" in t: return "fast"
    return "UNKNOWN"

def role_of(text):
    t = text.lower()
    if "planner" in t or "debugger executing step 2" in t: return "plan"
    if "devil's advocate" in t or "challenge subagent" in t: return "devil"
    if "researcher" in t or "online research subagent" in t: return "research"
    if "implementer" in t or "baseline implementer" in t: return "impl"
    return "other"

def scan(path):
    usage = {k: 0 for k in USAGE}; turns = 0; chunks = []
    for line in Path(path).read_text(errors="replace").splitlines():
        line = line.strip()
        if not line: continue
        try: obj = json.loads(line)
        except json.JSONDecodeError: continue
        msg = obj.get("message")
        if isinstance(msg, dict):
            u = msg.get("usage")
            if isinstance(u, dict):
                for k in USAGE: usage[k] += int(u.get(k, 0) or 0)
                turns += 1
            c = msg.get("content")
            if isinstance(c, str): chunks.append(c)
            elif isinstance(c, list):
                for x in c:
                    if isinstance(x, dict) and isinstance(x.get("text"), str): chunks.append(x["text"])
    return usage, turns, "\n".join(chunks)

dirs = sys.argv[1:]
arms = {}
for d in dirs:
    for j in sorted(Path(d).glob("agent-*.jsonl")):
        usage, turns, text = scan(j)
        a = arm_of(text); r = role_of(text)
        tot = sum(usage[k] for k in USAGE)
        A = arms.setdefault(a, {"count": 0, "turns": 0, "output": 0, "cache_read": 0, "total": 0, "roles": {}})
        A["count"] += 1; A["turns"] += turns; A["output"] += usage["output_tokens"]
        A["cache_read"] += usage["cache_read_input_tokens"]; A["total"] += tot
        R = A["roles"].setdefault(r, {"count": 0, "total": 0})
        R["count"] += 1; R["total"] += tot

print(f"{'arm':8}{'agents':>8}{'turns':>8}{'output_tok':>13}{'cache_read':>14}{'TOTAL_tok':>14}")
order = ["naive", "fast", "skill", "UNKNOWN"]
for a in order:
    if a not in arms: continue
    d = arms[a]
    print(f"{a:8}{d['count']:>8}{d['turns']:>8}{d['output']:>13,}{d['cache_read']:>14,}{d['total']:>14,}")
print()
for a in order:
    if a not in arms: continue
    rs = arms[a]["roles"]
    rstr = "  ".join(f"{r}:{rs[r]['count']}({rs[r]['total']:,})" for r in ("plan","devil","research","impl","other") if r in rs)
    print(f"  {a}: {rstr}")
