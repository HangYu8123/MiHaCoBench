#!/usr/bin/env python3
"""Distribute generated solutions from the workflow output into candidate roots.

Reads the workflow result JSON (which contains one record per arm-task with a
list of {filename, content}) and writes each file to
``experiment_mihaco/cand_<arm>/<category>/<task_id>/<filename>``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent


def main(output_file: str) -> int:
    raw = json.loads(Path(output_file).read_text())
    # The workflow's return value may be at top level or under "result".
    results = None
    for container in (raw, raw.get("result", {}) if isinstance(raw, dict) else {}):
        if isinstance(container, dict) and "results" in container:
            results = container["results"]
            break
    if results is None:
        print("ERROR: could not locate 'results' array in output", file=sys.stderr)
        return 1

    manifest = []
    for rec in results:
        arm, cat, tid = rec["arm"], rec["cat"], rec["id"]
        out_dir = EXP / f"cand_{arm}" / cat / tid
        out_dir.mkdir(parents=True, exist_ok=True)
        files = rec.get("files") or []
        names = []
        for f in files:
            (out_dir / f["filename"]).write_text(f["content"])
            names.append(f"{f['filename']}({len(f['content'])}b)")
        manifest.append((arm, cat, tid, rec.get("subagents"), rec.get("qa_blocking"), names))

    manifest.sort()
    print(f"Distributed {len(results)} arm-task solution sets:\n")
    cur = None
    for arm, cat, tid, sub, qab, names in manifest:
        if arm != cur:
            print(f"=== arm: {arm} ===")
            cur = arm
        qa = "" if qab is None else f" qa_blocking={qab}"
        print(f"  {cat:13} {tid:26} subagents={sub}{qa}  files: {', '.join(names)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
