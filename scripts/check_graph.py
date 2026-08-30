#!/usr/bin/env python3
"""Prove the submodule graph a recursive clone is supposed to produce.

    PCBA_AutoDesignAndTest_Bench
      └─ boards/NN_PCBA_*                     (32 board repositories)
           └─ tooling/PCBA_AutoDesignAndTest  (the shared toolkit)
                └─ tooling/KiCadRoutingTools  (the router, pcba-autonomy)

Four levels, and nothing is believed because a path exists. A submodule counts
as present only when its content is there and identifiable, the recorded commit
matches the checked-out one, and every board resolves the same toolkit commit
and the same router commit as every other board — a benchmark whose boards run
different toolkits is not one benchmark.

Also checks the coherence that makes the catalogue usable: that every
`boards_index.json` entry's brief path resolves inside this checkout, that each
board's own `benchmark/metadata.json` agrees with the catalogue, and that the
brief digest each board recorded still describes its brief's bytes.

    python3 scripts/check_graph.py            # after a recursive clone
    python3 scripts/check_graph.py --shallow  # graph only; skip board content

Exit status is 0 only when every check passed.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER = "pentolope"
TOOLKIT_PATH = "tooling/PCBA_AutoDesignAndTest"
KRT_PATH = "tooling/KiCadRoutingTools"
TOOLKIT_MARKERS = ("run.py", "pcbqa", "profiles")
KRT_MARKERS = ("build_router.py", "kicad_routing_plugin")

failures = []
notes = []


def fail(msg):
    failures.append(msg)


def git(repo, *args):
    """Run git in `repo`; return stdout stripped, or None if it failed."""
    try:
        out = subprocess.run(("git", "-C", repo) + args, capture_output=True,
                             text=True, check=True)
    except (subprocess.CalledProcessError, OSError):
        return None
    return out.stdout.strip()


def declared_submodules(repo):
    """{path: url} from a repository's committed .gitmodules."""
    path = os.path.join(repo, ".gitmodules")
    if not os.path.isfile(path):
        return {}
    raw = git(repo, "config", "--file", ".gitmodules", "--get-regexp",
              r"^submodule\..*\.(path|url)$")
    if raw is None:
        return {}
    paths, urls = {}, {}
    for line in raw.splitlines():
        key, _, value = line.partition(" ")
        name = key[len("submodule."):].rsplit(".", 1)[0]
        if key.endswith(".path"):
            paths[name] = value
        elif key.endswith(".url"):
            urls[name] = value
    return {paths[n]: urls.get(n, "") for n in paths if n in paths}


def recorded_commit(repo, path):
    """The gitlink commit HEAD records for a submodule path."""
    out = git(repo, "ls-tree", "HEAD", path)
    if not out:
        return None
    fields = out.split()
    return fields[2] if len(fields) >= 3 and fields[0] == "160000" else None


def populated(path, markers):
    return all(os.path.exists(os.path.join(path, m)) for m in markers)


def check_submodule(parent, sub_path, expect_url_suffix, markers, label,
                    require_checkout=True):
    """Declared, recorded, checked out, identifiable. Returns the commit.

    With `require_checkout` false, the declaration and the recorded gitlink are
    still proved -- that is what `--shallow` is for, and it is a real check: a
    missing .gitmodules entry, a wrong URL or an absent gitlink all still fail.
    What it does not do is demand content that a bare clone has not fetched.
    """
    declared = declared_submodules(parent)
    if sub_path not in declared:
        fail(f"{label}: {sub_path} is not declared in .gitmodules")
        return None
    url = declared[sub_path]
    if not url.rstrip("/").removesuffix(".git").endswith(expect_url_suffix):
        fail(f"{label}: {sub_path} points at {url!r}, "
             f"expected a URL ending {expect_url_suffix!r}")
    rec = recorded_commit(parent, sub_path)
    if rec is None:
        fail(f"{label}: {sub_path} is declared but HEAD records no gitlink")
        return None
    full = os.path.join(parent, sub_path)
    if not os.path.isdir(full) or not os.listdir(full):
        if not require_checkout:
            return rec
        fail(f"{label}: {sub_path} is not checked out "
             f"(run: git submodule update --init --recursive)")
        return None
    if not populated(full, markers):
        fail(f"{label}: {sub_path} is checked out but does not look like "
             f"itself (missing one of {', '.join(markers)})")
        return None
    head = git(full, "rev-parse", "HEAD")
    if head != rec:
        fail(f"{label}: {sub_path} is at {head} but HEAD records {rec}")
    return rec


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shallow", action="store_true",
                    help="check the submodule graph only; skip board content")
    opts = ap.parse_args()

    index_path = os.path.join(ROOT, "boards_index.json")
    if not os.path.isfile(index_path):
        sys.exit("boards_index.json not found; run this from a clone of the "
                 "benchmark repository")
    index = json.load(open(index_path, encoding="utf-8"))
    if len(index) != 32:
        fail(f"boards_index.json has {len(index)} entries, expected 32")

    declared = declared_submodules(ROOT)
    board_subs = {p: u for p, u in declared.items() if p.startswith("boards/")}
    if len(board_subs) != 32:
        fail(f"{len(board_subs)} board submodules declared, expected 32")

    toolkit_commits, krt_commits, ok_boards = {}, {}, 0

    for entry in index:
        repo = entry["repo"]
        sub = "boards/%02d_%s" % (entry["benchmark_id"], repo)
        label = repo
        before = len(failures)

        if sub not in board_subs:
            fail(f"{label}: no submodule declared at {sub}")
            continue
        deep = not opts.shallow
        check_submodule(ROOT, sub, f"/{OWNER}/{repo}", ("BRIEF.md",),
                        label, require_checkout=deep)
        board = os.path.join(ROOT, sub)
        if not os.path.isdir(board) or not os.listdir(board):
            if opts.shallow:
                ok_boards += 1 if len(failures) == before else 0
                continue
            continue

        # level 3 and 4: the toolkit, and the router inside it
        tk = check_submodule(board, TOOLKIT_PATH,
                             f"/{OWNER}/PCBA_AutoDesignAndTest",
                             TOOLKIT_MARKERS, label, require_checkout=deep)
        if tk:
            toolkit_commits.setdefault(tk, []).append(repo)
            toolkit = os.path.join(board, TOOLKIT_PATH)
            if os.path.isdir(toolkit) and os.listdir(toolkit):
                krt = check_submodule(toolkit, KRT_PATH,
                                      f"/{OWNER}/KiCadRoutingTools",
                                      KRT_MARKERS, f"{label} -> toolkit",
                                      require_checkout=deep)
                if krt:
                    krt_commits.setdefault(krt, []).append(repo)
            elif not opts.shallow:
                fail(f"{label}: toolkit is not checked out, so its router "
                     f"submodule cannot be proved")
            else:
                notes.append("router pins not read: toolkit not checked out "
                             "(--shallow)")

        if not opts.shallow:
            # the catalogue's brief path must resolve, in this checkout
            brief = os.path.join(ROOT, entry["brief"])
            if not os.path.isfile(brief):
                fail(f"{label}: boards_index.json brief path "
                     f"{entry['brief']!r} does not resolve")
            # the board's own catalogue entry must agree with the catalogue
            meta_path = os.path.join(board, "benchmark", "metadata.json")
            if not os.path.isfile(meta_path):
                fail(f"{label}: benchmark/metadata.json is missing")
            else:
                meta = json.load(open(meta_path, encoding="utf-8"))
                for key in ("repo", "title", "category", "difficulty",
                            "detail", "layers", "stress", "benchmark_id"):
                    if meta.get(key) != entry.get(key):
                        fail(f"{label}: metadata.json {key}={meta.get(key)!r} "
                             f"disagrees with boards_index.json "
                             f"{entry.get(key)!r}")
            # the brief digest the board recorded must describe its brief
            req_path = os.path.join(board, "board", "requirements.json")
            if not os.path.isfile(req_path):
                fail(f"{label}: board/requirements.json is missing")
            else:
                req = json.load(open(req_path, encoding="utf-8"))
                actual = sha256_file(os.path.join(board, "BRIEF.md"))
                recorded = req.get("brief", {}).get("sha256")
                if recorded != actual:
                    fail(f"{label}: requirements.json records brief sha256 "
                         f"{recorded} but BRIEF.md hashes to {actual}")
                if not req.get("fixed_requirements"):
                    fail(f"{label}: requirements.json fixes no requirements")
                if not req.get("open_decisions"):
                    fail(f"{label}: requirements.json records no open decisions")
            for required in ("README.md", "CLAUDE.md",
                             "board/manifest.template.json",
                             "board/toolchain.json", "docs/status.md"):
                if not os.path.exists(os.path.join(board, required)):
                    fail(f"{label}: {required} is missing")

        if len(failures) == before:
            ok_boards += 1

    if len(toolkit_commits) > 1:
        fail("boards resolve %d different toolkit commits; they must share one: "
             % len(toolkit_commits) +
             "; ".join(f"{c[:12]} <- {len(r)} board(s)"
                       for c, r in sorted(toolkit_commits.items())))
    if len(krt_commits) > 1:
        fail("boards resolve %d different KiCadRoutingTools commits; they must "
             "share one: " % len(krt_commits) +
             "; ".join(f"{c[:12]} <- {len(r)} board(s)"
                       for c, r in sorted(krt_commits.items())))

    print("bench -> board -> toolkit -> KiCadRoutingTools")
    print(f"  boards fully checked   {ok_boards}/32")
    for name, commits in (("toolkit", toolkit_commits),
                          ("KiCadRoutingTools", krt_commits)):
        if len(commits) == 1:
            commit, repos = next(iter(commits.items()))
            print(f"  {name:<22} {commit[:12]}  resolved by {len(repos)}/32 boards")
        elif not commits:
            print(f"  {name:<22} not resolved by any board")
    for note in sorted(set(notes)):
        print("  note: " + note)

    if failures:
        print(f"\n{len(failures)} problem(s):", file=sys.stderr)
        for f in failures:
            print("  - " + f, file=sys.stderr)
        return 1
    print("\nGraph and catalogue coherent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
