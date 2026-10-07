# Historical Phase 6 tooling checkpoint

Superseded by `evaluation.md` and `verification.json`; the final bounded run is complete.

Phase 5 implementation `6d51b5cf3a004d1dec0925859253f613b54d2d9c` was normally
pushed and freshly verified before starting Phase 6. The plan ends at Phase 6.

Smoke run reproduced the frozen January benchmark; results are retained separately
in `smoke-benchmark.json`. Its zero-positive metrics remain undefined.
`preflight.json` records source size, available memory/disk, strict bounds and the
cohort interval selected before reading any new test labels. Full materialization
is beyond available memory in the existing event/text pipeline; no full evaluation
is claimed. A full CRC-validated source scan will retain the two-week June cohort.

New scanner: safe paths/member budgets, bounded indexed caches, exact original row
positions, strict chronological/header checks, hash-verified manifest only after
EOF, no answer consultation. Existing chunked ingestion resumes/idempotently
replays those caches without touching the historical store. A failed scan leaves
unpublished staging files and restarts; committed ingestion chunks resume.
Feature/model/text CLIs accept explicit larger bounds, with unchanged defaults.
The original byte-bound rejection tests remain enforced.

New comparison: fixed research FILE/after-hours heuristic, models and fixed OR on
one identical frozen held-out cohort, without changing endpoint policy. Exact
partitions and score artifacts now have report-bound hashes. Grouped errors report
only feature/scenario summaries, never user/event/text identifiers.
Threshold search uses sorting/cumulative counts for the same strict validation F1
objective/tie break; synthetic exhaustive parity checks protect this optimization.
Advisory hardening additionally rejects missing fully observed counts and malformed
sidecar schemas. These are extensions of Phase 5 within the current milestone.

Fresh npm review is in `npm-review.md`/`npm-review.json`. Network/registry access
worked; all findings remain open. No package/toolchain/Docker default was changed.
Docker binary, Windows hardware and PostgreSQL checks remain unverified.

This is a tested tooling milestone; expanded real evaluation is still running.
Final acceptance/results/error analysis/handover will follow without confirmation.
