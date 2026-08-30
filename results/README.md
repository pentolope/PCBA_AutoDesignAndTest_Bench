# Results

Compact per-attempt results. Empty until the first attempt.

One file per attempt, named for the board and the attempt, carrying:

- the three commits that identify it — board, toolkit, router
- the toolkit's gate matrix, including `NOT_APPLICABLE` gates with their reasons
- which open decisions were answered, and how many were left open
- any entry added to that board's `fixed_requirements`, with its brief evidence
- wall-clock and token cost, if measured

The evidence for a result is the artefact the toolkit recomputes, not a summary
of it — so a result records what was measured and where, and never a number
whose provenance died with the run that produced it.

Build trees, candidate pools, routing output, release packages and field-solver
dumps do not belong here. They are regenerated from the recorded commits.

See [../BENCHMARK.md](../BENCHMARK.md).
