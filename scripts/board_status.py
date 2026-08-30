#!/usr/bin/env python3
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def board_files(path):
    found = []
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames
                       if not os.path.exists(os.path.join(dirpath, d, ".git"))]
        found += [os.path.relpath(os.path.join(dirpath, f), path)
                  for f in filenames if f.endswith(".kicad_pcb")]
    return sorted(found)


def main():
    index_path = os.path.join(ROOT, "boards_index.json")
    if not os.path.isfile(index_path):
        return 1
    index = json.load(open(index_path, encoding="utf-8"))
    rows = []
    for e in sorted(index, key=lambda x: x["benchmark_id"]):
        sub = "boards/%02d_%s" % (e["benchmark_id"], e["repo"])
        path = os.path.join(ROOT, sub)
        checked_out = os.path.isdir(path) and bool(os.listdir(path))
        rows.append({
            "benchmark_id": e["benchmark_id"],
            "repo": e["repo"],
            "category": e["category"],
            "difficulty": e["difficulty"],
            "detail": e["detail"],
            "layers": e["layers"],
            "submodule": sub,
            "checked_out": checked_out,
            "board_files": board_files(path) if checked_out else [],
        })
    json.dump(rows, sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
