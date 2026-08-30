# PCBA_AutoDesignAndTest_Bench — the 32-board benchmark umbrella

## Mission

The catalogue, the protocol and the results for a 32-board PCBA auto-design
benchmark. The boards themselves are thirty-two separate repositories, mounted
here as submodules under `boards/`.

This repository holds **no board content**. If you are editing a design, you are
in the wrong repository — work in the board's own repository, and update the
submodule pointer here afterwards, with authorisation.

## What lives here, and what does not

Here:

- `boards_index.json` — the catalogue, byte for byte as supplied. Not edited.
- `BENCHMARK.md` — the attempt protocol, defined once for all thirty-two boards.
- `scripts/` — the graph check and the status table. Compact, no board content.
- `results/` — compact per-attempt results.

Not here, and not to be added:

- copies of any board's build tree, KiCad files, candidates or releases
- a copy of the toolkit or of KiCad Routing Tools — they are reached through the
  boards, at one pinned commit each
- a second copy of the attempt protocol inside a board repository

## The graph is the product

```
bench -> boards/NN_PCBA_* -> tooling/PCBA_AutoDesignAndTest -> tooling/KiCadRoutingTools
```

All thirty-two boards must resolve the **same** toolkit commit and the **same**
router commit. Bumping one board's toolkit pin without the other thirty-one
silently makes the suite incomparable, so bump them together and re-run:

```bash
python3 scripts/check_graph.py
```

Submodule directories are named `NN_RepoName` to match the seed pack, which is
the only reason `boards_index.json` can be kept unmodified and still have its
`brief` paths resolve. Renaming a submodule directory breaks the catalogue.

## Rules

1. Do not edit any board's `BRIEF.md`, from here or anywhere.
2. Do not edit `boards_index.json`. It is the supplied catalogue of record; a
   board's own `benchmark/metadata.json` must agree with it, and `check_graph.py`
   checks that rather than assuming it.
3. Do not commit, push, change a remote, or update a submodule pointer without
   explicit user authorisation.
4. Do not commit disposable output. Weight here is paid thirty-two times over.
5. Report a board as designed only when a board file exists. `board_status.py`
   checks for one rather than believing a name.

## Publishing discipline

Before any push of cycle work, run `/claim-audit` on the drafted commit message
and report, then `/accountability-review`. A benchmark's own claims about itself
are held to the standard it holds its boards to.

## Running

```bash
git clone --recursive https://github.com/pentolope/PCBA_AutoDesignAndTest_Bench.git
```

```bash
python3 scripts/check_graph.py
```

```bash
python3 scripts/board_status.py
```
