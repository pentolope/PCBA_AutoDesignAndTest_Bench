#!/usr/bin/env python3
"""What the thirty-two boards are, and how far each has got.

Reads `boards_index.json` for the catalogue and, where a board submodule is
checked out, that board's own `board/requirements.json` and design sources for
its state. Nothing is inferred from a name: a board counts as designed only when
a KiCad board file is actually present in its checkout.

    python3 scripts/board_status.py             # table
    python3 scripts/board_status.py --json      # the same, machine-readable
    python3 scripts/board_status.py --missing   # only boards not checked out
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def board_files(path):
    """Every .kicad_pcb belonging to THIS board, and none belonging to another.

    Recursive, because a board file in a subdirectory is still this board's.
    Submodule-aware, because a naive recursive glob walks straight into
    `tooling/PCBA_AutoDesignAndTest` and finds the toolkit's own test fixtures -
    which would report all thirty-two undesigned boards as designed, the exact
    fail-open in the opposite direction. A directory holding `.git` is another
    repository's root; its contents are not this board's design.
    """
    found = []
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames
                       if not os.path.exists(os.path.join(dirpath, d, ".git"))]
        found += [os.path.join(dirpath, f)
                  for f in filenames if f.endswith(".kicad_pcb")]
    return found


def board_state(entry):
    sub = "boards/%02d_%s" % (entry["benchmark_id"], entry["repo"])
    path = os.path.join(ROOT, sub)
    state = {
        "benchmark_id": entry["benchmark_id"],
        "repo": entry["repo"],
        "title": entry["title"],
        "category": entry["category"],
        "difficulty": entry["difficulty"],
        "detail": entry["detail"],
        "layers": entry["layers"],
        "path": sub,
        "checked_out": False,
        "fixed_requirements": None,
        "open_decisions": None,
        "decisions_made": None,
        "designed": False,
    }
    if not os.path.isdir(path) or not os.listdir(path):
        return state
    state["checked_out"] = True
    state["designed"] = bool(board_files(path))
    req_path = os.path.join(path, "board", "requirements.json")
    if os.path.isfile(req_path):
        try:
            req = json.load(open(req_path, encoding="utf-8"))
        except ValueError:
            return state
        opens = req.get("open_decisions", [])
        state["fixed_requirements"] = len(req.get("fixed_requirements", []))
        state["open_decisions"] = len(opens)
        state["decisions_made"] = sum(1 for o in opens if o.get("chosen"))
    return state


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--missing", action="store_true",
                    help="list only boards that are not checked out")
    opts = ap.parse_args()

    index_path = os.path.join(ROOT, "boards_index.json")
    if not os.path.isfile(index_path):
        sys.exit("boards_index.json not found; run this from a clone of the "
                 "benchmark repository")
    index = json.load(open(index_path, encoding="utf-8"))
    rows = [board_state(e) for e in sorted(index, key=lambda e: e["benchmark_id"])]

    if opts.missing:
        rows = [r for r in rows if not r["checked_out"]]
        if not rows:
            print("All 32 board submodules are checked out.")
            return 0
    if opts.json:
        json.dump(rows, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    name_w = max(len(r["repo"]) for r in rows) if rows else 4
    cat_w = max(len(r["category"]) for r in rows) if rows else 8
    print(f"{'#':>2}  {'repository':<{name_w}}  {'category':<{cat_w}}  "
          f"{'dif':>3} {'det':>3}  {'layers':<10} {'req':>4} {'open':>5}  state")
    print("-" * (name_w + cat_w + 48))
    for r in rows:
        if not r["checked_out"]:
            state = "not checked out"
        elif r["designed"]:
            made, total = r["decisions_made"], r["open_decisions"]
            state = "designed" + (f" ({made}/{total} decisions recorded)"
                                  if total else "")
        else:
            state = "scaffolded, not designed"
        req = "-" if r["fixed_requirements"] is None else r["fixed_requirements"]
        opn = "-" if r["open_decisions"] is None else r["open_decisions"]
        print(f"{r['benchmark_id']:>2}  {r['repo']:<{name_w}}  "
              f"{r['category']:<{cat_w}}  {r['difficulty']:>3} {r['detail']:>3}  "
              f"{r['layers']:<10} {req:>4} {opn:>5}  {state}")

    out = sum(1 for r in rows if not r["checked_out"])
    designed = sum(1 for r in rows if r["designed"])
    print(f"\n{len(rows)} boards: {designed} designed, "
          f"{len(rows) - designed - out} scaffolded, {out} not checked out.")
    if out:
        print("Run: git submodule update --init --recursive")
    return 0


if __name__ == "__main__":
    sys.exit(main())
