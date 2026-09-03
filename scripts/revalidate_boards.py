#!/usr/bin/env python3
"""Rebuild and revalidate every board in the bench against the shared toolkit.

Each board's `tooling/PCBA_AutoDesignAndTest` is a committed symlink into this
bench's `toolkit/PCBA_AutoDesignAndTest` checkout, and the toolkit is a
source-closure member - so advancing the toolkit invalidates every board's
committed artifacts at once. This turns the recovery into one command:

    python3 scripts/revalidate_boards.py [--boards 01,04]
                                         [--steps check,build,validate,release]
                                         [--allow-dirty-toolkit]

Per board (independently; one failure does not stop the others):

  check     run.py check-board       names what is stale and which input
                                     moved; informational, never counted as
                                     a failure, because staleness before the
                                     rebuild is the situation this exists for
  build     run.py build             regenerate the fabrication outputs
  validate  run.py validate --write  record the verdict beside them
  release   run.py release-check     a real verdict - run it as
                                     `--steps release` after committing the
                                     boards; before the commit it is blocked
                                     by the dirty tree, by design

The default steps are `build,validate`: the recovery itself. Exit zero means
every requested verdict-bearing step passed on every board.

The bench toolkit checkout must be clean: artifacts rebuilt under a dirty
toolkit are recorded against code no commit names, which is exactly the
staleness this exists to clear. Nothing here commits, pushes or tags. Exit is
nonzero if any requested step failed on any board.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH_TOOLKIT = os.path.join(BENCH, "toolkit", "PCBA_AutoDesignAndTest")
TOOLKIT_REL = os.path.join("tooling", "PCBA_AutoDesignAndTest")
STEPS = ("check", "build", "validate", "release")


def run(args, cwd=None, log=None):
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write("$ {}\n{}{}\n".format(" ".join(args), proc.stdout,
                                           proc.stderr))
    return proc


def boards(selector):
    found = []
    for manifest in sorted(glob.glob(
            os.path.join(BENCH, "boards", "*", "board", "manifest.json"))):
        root = os.path.dirname(os.path.dirname(manifest))
        name = os.path.basename(root)
        if selector and not any(name.startswith(pick) or pick in name
                                for pick in selector):
            continue
        found.append((name, root, manifest))
    return found


def classify_check(proc):
    """One word for a check-board run; only staleness is informational.

    Findings before a rebuild are the situation the recovery exists for, so
    they are informational - but a check that DIED (no display, a refusal, a
    traceback) said nothing about staleness and must not be dressed as it,
    and a board on which nothing ran must never read as passing.
    """
    if proc.returncode == 0:
        return "ok"
    if "BOARD CHECK FAILED" in proc.stdout:
        changed = set()
        for hit in re.findall(r"changed: ([^;\n]+)", proc.stdout):
            changed.update(part.strip() for part in hit.split(","))
        changed -= {""}
        if changed and changed <= {"<toolkit>", "<configuration>"}:
            return "stale(toolkit)"
        if changed:
            return "stale(design)"
        return "stale"
    if "BOARD CHECK REFUSED" in proc.stdout:
        return "refused"
    # Only a POSITIVE old-toolkit signal is n/a: the usage banner of a
    # toolkit that predates check-board names the package but not the
    # command. A missing interpreter target or any other exit-2 is a
    # failure - "can't open file" is not an old toolkit, it is no toolkit.
    if proc.returncode == 2 \
            and "pcbqa" in (proc.stdout + proc.stderr) \
            and "check-board" not in (proc.stdout + proc.stderr):
        return "n/a"                      # this toolkit predates check-board
    return "exit {}".format(proc.returncode)


def toolkit_cmd(root, manifest, *args):
    return [sys.executable, os.path.join(root, TOOLKIT_REL, "run.py"),
            *args, manifest]


def main(argv):
    parser = argparse.ArgumentParser(
        description="rebuild and revalidate the bench's boards")
    parser.add_argument("--boards", default="",
                        help="comma-separated selectors matched against the "
                             "board directory name (default: all)")
    parser.add_argument("--steps", default="build,validate",
                        help="comma-separated subset of: " + ",".join(STEPS))
    parser.add_argument("--allow-dirty-toolkit", action="store_true",
                        help="proceed although the bench toolkit checkout is "
                             "dirty (results will be bound to uncommitted "
                             "code; development only)")
    args = parser.parse_args(argv)

    requested = {s for s in args.steps.split(",") if s}
    if not requested:
        print("no steps requested; running nothing is not \"every step "
              "passed\"")
        return 2
    unknown = sorted(requested - set(STEPS))
    if unknown:
        print("unknown step(s): {}".format(unknown))
        return 2
    # Canonical order regardless of how they were typed: a verdict recorded
    # before the build that replaces its artifacts would be about nothing.
    steps = [s for s in STEPS if s in requested]
    selector = [s for s in args.boards.split(",") if s]

    status = run(["git", "-C", BENCH_TOOLKIT, "status", "--porcelain"])
    if status.returncode != 0:
        print("REFUSED: the bench toolkit's git status cannot be read: "
              + status.stderr.strip())
        return 2
    if status.stdout.strip() and not args.allow_dirty_toolkit:
        print("REFUSED: the bench toolkit checkout is dirty; artifacts "
              "rebuilt now would be bound to code no commit names. Commit "
              "the toolkit first, or pass --allow-dirty-toolkit for a "
              "development run.")
        return 2

    chosen = boards(selector)
    if not chosen:
        print("no board with a board/manifest.json matches")
        return 2
    logdir = tempfile.mkdtemp(prefix="bench_revalidate_")
    head = run(["git", "-C", BENCH_TOOLKIT, "rev-parse", "--short", "HEAD"])
    # Under --allow-dirty-toolkit the running code is NOT that commit, and
    # a header claiming it is would be false exactly where identity matters.
    dirty = "+dirty (uncommitted changes; results are bound to code no " \
            "commit names)" if status.stdout.strip() else ""
    print("toolkit: {} @ {}{}".format(os.path.realpath(BENCH_TOOLKIT),
                                      head.stdout.strip() or "?", dirty))
    print("logs: {}\n".format(logdir))

    results = {}
    for name, root, manifest in chosen:
        results[name] = {}
        log = os.path.join(logdir, name + ".log")
        # What actually runs is whatever the board's tooling path resolves
        # to. A missing toolkit is a failure, not a pass-by-absence; a
        # DIFFERENT toolkit would bind artifacts to code this bench never
        # verified, so it is refused by name.
        board_toolkit = os.path.join(root, TOOLKIT_REL)
        if not os.path.isfile(os.path.join(board_toolkit, "run.py")):
            results[name] = {step: "missing-toolkit" for step in steps}
            print("{:36s} {}".format(name, "  ".join(
                "{}:missing-toolkit".format(s) for s in steps)))
            continue
        if os.path.realpath(board_toolkit) != os.path.realpath(BENCH_TOOLKIT):
            results[name] = {step: "foreign-toolkit" for step in steps}
            print("{:36s} {}  ({} resolves to {})".format(
                name, "  ".join("{}:foreign-toolkit".format(s)
                                for s in steps),
                TOOLKIT_REL, os.path.realpath(board_toolkit)))
            continue
        for step in steps:
            command = {
                "check": toolkit_cmd(root, manifest, "check-board"),
                "build": toolkit_cmd(root, manifest, "build"),
                "validate": toolkit_cmd(root, manifest, "validate",
                                        "--write"),
                "release": toolkit_cmd(root, manifest, "release-check"),
            }[step]
            proc = run(command, cwd=root, log=log)
            if step == "check":
                results[name][step] = classify_check(proc)
                continue
            results[name][step] = "ok" if proc.returncode == 0 \
                else "exit {}".format(proc.returncode)
            if proc.returncode != 0 and step == "build":
                break                     # nothing downstream is meaningful
        line = "  ".join("{}:{}".format(s, results[name].get(s, "-"))
                         for s in steps)
        print("{:36s} {}".format(name, line))

    failed = [name for name, steps_run in results.items()
              if not steps_run
              or any(v not in ("ok", "n/a", "-") and not v.startswith("stale")
                     for v in steps_run.values())]
    if failed:
        print("\n{} board(s) need attention: {}".format(
            len(failed), ", ".join(failed)))
        print("per-board logs are under {}".format(logdir))
        return 1
    print("\nevery requested step passed on every board")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
