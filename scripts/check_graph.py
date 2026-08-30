#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER = "pentolope"
TOOLKIT = "tooling/PCBA_AutoDesignAndTest"
KRT = "tooling/KiCadRoutingTools"
TOOLKIT_MARKERS = ("run.py", "pcbqa", "profiles")
KRT_MARKERS = ("build_router.py", "kicad_routing_plugin")
BOARD_MARKERS = ("BRIEF.md", "benchmark/metadata.json")
META_KEYS = ("repo", "title", "category", "difficulty", "detail", "layers",
             "stress", "benchmark_id")

findings = []


def add(code, **kw):
    findings.append(dict(code=code, **kw))


def git(repo, *args):
    try:
        r = subprocess.run(("git", "-C", repo) + args, capture_output=True,
                           text=True, check=True)
    except (subprocess.CalledProcessError, OSError):
        return None
    return r.stdout.strip()


def declared(repo):
    out = git(repo, "config", "--file", ".gitmodules", "--get-regexp",
              r"^submodule\..*\.(path|url)$")
    if out is None:
        return {}
    paths, urls = {}, {}
    for line in out.splitlines():
        key, _, val = line.partition(" ")
        name = key[len("submodule."):].rsplit(".", 1)[0]
        if key.endswith(".path"):
            paths[name] = val
        else:
            urls[name] = val
    return {paths[n]: urls.get(n, "") for n in paths}


def gitlink(repo, path):
    out = git(repo, "ls-tree", "HEAD", path)
    if not out:
        return None
    f = out.split()
    return f[2] if len(f) >= 3 and f[0] == "160000" else None


def submodule(parent, path, expect, markers, ctx, require_checkout):
    d = declared(parent)
    if path not in d:
        add("submodule_undeclared", path=path, **ctx)
        return None
    url = d[path].rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    if not url.endswith(expect):
        add("submodule_url_mismatch", path=path, url=d[path],
            expected_suffix=expect, **ctx)
    rec = gitlink(parent, path)
    if rec is None:
        add("gitlink_missing", path=path, **ctx)
        return None
    full = os.path.join(parent, path)
    if not os.path.isdir(full) or not os.listdir(full):
        if not require_checkout:
            return rec
        add("submodule_not_checked_out", path=path, **ctx)
        return None
    missing = [m for m in markers if not os.path.exists(os.path.join(full, m))]
    if missing:
        add("submodule_unidentifiable", path=path, missing=missing, **ctx)
        return None
    head = git(full, "rev-parse", "HEAD")
    if head != rec:
        add("gitlink_mismatch", path=path, head=head, recorded=rec, **ctx)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shallow", action="store_true")
    opts = ap.parse_args()
    deep = not opts.shallow

    index_path = os.path.join(ROOT, "boards_index.json")
    if not os.path.isfile(index_path):
        add("catalogue_missing", path="boards_index.json")
        json.dump({"findings": findings}, sys.stdout, indent=1)
        sys.stdout.write("\n")
        return 1
    index = json.load(open(index_path, encoding="utf-8"))
    if len(index) != 32:
        add("catalogue_size", count=len(index), expected=32)

    board_subs = {p: u for p, u in declared(ROOT).items()
                  if p.startswith("boards/")}
    if len(board_subs) != 32:
        add("board_submodule_count", count=len(board_subs), expected=32)

    toolkit_commits, krt_commits = {}, {}

    for e in index:
        repo = e["repo"]
        sub = "boards/%02d_%s" % (e["benchmark_id"], repo)
        ctx = {"repo": repo, "submodule": sub}
        submodule(ROOT, sub, f"/{OWNER}/{repo}", BOARD_MARKERS, ctx, deep)
        board = os.path.join(ROOT, sub)
        if not os.path.isdir(board) or not os.listdir(board):
            continue

        tk = submodule(board, TOOLKIT, f"/{OWNER}/PCBA_AutoDesignAndTest",
                       TOOLKIT_MARKERS, ctx, deep)
        if tk:
            toolkit_commits.setdefault(tk, []).append(repo)
            toolkit = os.path.join(board, TOOLKIT)
            if os.path.isdir(toolkit) and os.listdir(toolkit):
                krt = submodule(toolkit, KRT, f"/{OWNER}/KiCadRoutingTools",
                                KRT_MARKERS, ctx, deep)
                if krt:
                    krt_commits.setdefault(krt, []).append(repo)
            elif deep:
                add("toolkit_not_checked_out", **ctx)

        brief = os.path.join(ROOT, e["brief"])
        if not os.path.isfile(brief):
            add("brief_path_unresolved", brief=e["brief"], **ctx)

        meta_path = os.path.join(board, "benchmark", "metadata.json")
        if not os.path.isfile(meta_path):
            add("metadata_missing", **ctx)
        else:
            meta = json.load(open(meta_path, encoding="utf-8"))
            for k in META_KEYS:
                if meta.get(k) != e.get(k):
                    add("metadata_mismatch", key=k, board_value=meta.get(k),
                        catalogue_value=e.get(k), **ctx)

    for name, commits in (("toolkit", toolkit_commits), ("krt", krt_commits)):
        resolved = sum(len(r) for r in commits.values())
        if len(commits) > 1:
            add("pin_divergence", level=name,
                commits={c: len(r) for c, r in commits.items()})
        if 0 < resolved < len(index):
            add("pin_partially_resolved", level=name, resolved=resolved,
                expected=len(index))

    report = {
        "boards": len(index),
        "shallow": opts.shallow,
        "toolkit": {c: len(r) for c, r in toolkit_commits.items()},
        "krt": {c: len(r) for c, r in krt_commits.items()},
        "findings": findings,
    }
    json.dump(report, sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
