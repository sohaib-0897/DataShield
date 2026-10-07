# Phase 2 — exact ground truth and versioned features

Completed on the bounded Phase 1 population. No additional r4.2 events were
imported. The 10,000-event store was opened read-only; labels and window artifacts
live separately in ignored `research/local/`. Application code, policies, data,
legacy sources and archives are preserved. No model is active.

## Answers contract and traceability

The supplied answers README establishes `insiders.csv` as the incident master and
variable-length, interleaved observable files with a leading source type. A full,
bounded inspection of the small answers archive retained every record and verified
all caches. There are 70 r4.2 incidents (30 scenario 1, 30 scenario 2, 10 scenario 3)
and 7,323 observables: 3,860 HTTP, 2,785 device, 470 email, 198 logon, 10 file.
The inspected observable files have no header: the inspector's `header` field
contains the first observable and the label reader restores it. Master filenames
are basenames; resolve them uniquely within their release/scenario subdirectory.
Truncated master/observable caches, ambiguous files, unsupported row shapes and
observable timestamps outside incident bounds fail explicitly.

Match dataset + source-file + original ID, then require equality of **every**
original CSV field (including user, PC, timestamp, resource and content). Labels
include incident filename and observable row provenance only in the local artifact.
Same-ID conflicts and multiple incident matches stay unknown and are excluded from
evaluation. Never propagate a label across a user's history. Absence from complete
release answers means a negative benchmark label, not proven real-world innocence.

An initial strict actor/subject check exposed 50 real identity differences in
scenario 3 (30 email, 20 logon). The supplied `answers/scenarios.txt` describes
keylogger use followed by impersonation of a supervisor. The master actor is
therefore separate from the observable account; exact matching uses the account
recorded in the observable. A regression fixture covers this case. Scenario text
and identities never enter inference features.

All 10,000 ingested events are negative; all 7,323 answers are unmatched in this
prefix. The actual incident-master range is June 10, 2010–April 29, 2011; ingested
sources cover January 2–5, 2010. This is expected limited coverage, not evidence of
missed detections or full-data reconciliation. No ambiguous events were observed.

## Shared feature contract

`ml/features/windows.py` provides pure, reusable normalized-event window building.
`research/cert_features.py` is the CERT adapter. Schema `cert-user-hour-v1` uses
nonoverlapping, half-open, release-local user hours. No UTC conversion is asserted.
Work hours default to 09:00–17:00 Monday–Friday and are configurable; this assumption
is not a release label. Emit active user-hours only, not invented inactive hours.

Stable features are the five source counts, total, after-hours fraction, distinct
PC count, fraction of new PCs compared with that user's past, past mean total,
current/past ratio, history-window count, cold-start indicator and five availability
bits. User IDs, PC IDs, source IDs, resources, text, answer labels, incident actors,
scenario IDs, LDAP and psychometrics are excluded from the numeric matrix. PCs are
used only for past-only within-user novelty. Event keys and label provenance are
separate evaluation data.

Coverage is conservatively inferred from each chronologically ordered source
prefix's first/last timestamps. Reject unsorted prefixes. A count is available only
when its entire hour lies inside that source interval. Missing counts are null with
availability zero; missing channels are not zero observed events. Total/combined
features are null unless all sources cover the hour. Baselines update only after a
complete user window, using completed fully observed windows for that user. Cold
starts have null means/ratios/novelty. Appending future events under the same coverage
contract cannot change earlier windows. Train-fitted imputation is Phase 3 work.

Actual output: 3,291 active user-hours, 164 fully observed hours, zero unknown labels.
The common full-hour interval is January 2, 2010 08:00–12:00. Truncated-source hours
remain available for audit but are excluded from numeric benchmarking. This small
population is not the full CERT distribution.

The live upstream `event-window-v2` contract uses per-event rolling windows and
other channels; legacy hourly code mixes users. Neither is interchangeable with
this schema. No existing live feature code is changed and no research artifact can
be used as a compatible live model. Phase 5 may add explicit adapters; research and
live models must remain separate when coverage differs.

## Commands and acceptance

Run from the repository root (module execution supplies the correct import path):

```bash
# A new complete answers scan; prints the new manifest path.
python3 -B -c "from pathlib import Path; from research.cert_ingest import inspect_archive; print(inspect_archive(Path('/home/sohaib/Downloads/answers.tar.bz2'), Path('research/local').absolute(), rows=100000, progress=None))"
python3 -B -m research.cert_features --database research/local/cert_r42.sqlite --answers research/local/scan-i4h4v35l/manifest.json --output research/local/phase2_features_v1.json --report research/local/phase2_acceptance_v1.json
.local/phase0-venv/bin/python -B -m pytest -q tests/test_cert_features.py tests/test_cert_ingestion.py
```

Actual manifest path for this acceptance is shown above. Outputs refuse overwrite;
choose new names for a repeat. Limits default to 100,000 events and inspection to
128 MiB retained prefixes with a 256 MiB disk reserve. Exceeding the event bound
fails before materialization. Work on a separately bounded store for larger runs.
Atomic artifacts allow rerunning after interruption with a new name; ingestion's
committed progress remains the resume mechanism.

Acceptance: 43 targeted passes (28 ingestion + 15 feature/label cases), no skips.
An independent feature replay produced an identical artifact fingerprint. Tests
cover all-fields joins, scoped IDs, ambiguous/unmatched labels, impersonated users,
first-observable restoration, incomplete answers, two-user isolation, future
invariance, missing sources, partial hours, cold starts, work hours and unsafe stores.
Existing isolated regression suite: 62 passes, one pre-existing deprecation warning;
this run covered the tracked baseline/Phase 1 tests before staging the new tests.
Original preservation: 30 source/live hashes and three archive stat records match
Phase 0. See `acceptance.json` and `verification.json`; no frontend code changed.
