# A2 — recovery, contextual-span feasibility and evaluation protocol

Recovered 2026-10-08 in the existing literal-tilde checkout on `feat/cert-ml-nlp`.
Starting HEAD: `d6cd80977df31dddf1fe8ce3756ec9dff9541537`, clean index/worktree,
cached origin divergence 0/0. No applicable AGENTS.md in checkout or ancestors.
The parent workspace's old Phase 0 pointer is stale; the repository status file
and Git history are authoritative. Parent files were preserved.

## What had finished before shutdown

Git history contains A1 source `ebc23dbbe63b9933829bee812ae9438f6d9d06e3`
and its publication receipt `d6cd809`, after the reported DS3 checkpoint
`22dc822c75cf6f1e106980bbd974fd576d025588`. A1's detector/extraction bridge,
66 contract tests, 287 isolated regression passes, 22 Flask passes, preservation
and source-SHA CI receipt exist and agree with the source. Historical source CI
37770109324 passed; recovery freshly verified closure-SHA CI 37770400258 success
through the GitHub connector and fresh remote equality through direct Git commands.
There was no uncommitted/staged A2 work or local commit ahead of cached origin.
`git fsck --full` succeeds; dangling blobs remain preserved, no corrupt objects.

## Recovery evidence and preserved interruption remnants

Ignored evidence is in `.local/phase-a2-recovery/`. [verification.json](verification.json)
contains sanitized outcomes. No ingestion, feature preparation, fitting or frozen
test scoring was rerun. No monitor, PostgreSQL service or model flag was started.

- All 13 canonical artifacts pass `scripts/verification/ds2_frozen_preservation.py`.
  Feature artifacts use the established canonical payload verifier, not file hashes.
- All 60 files in A1's private snapshot and all 12 DS3-bound inputs match; six
  TAB source files independently pass pinned Git blob IDs/sizes and SHA-256.
- Selected DS2 artifact loads through the existing operator-pinned classifier's
  software/digest/type/schema checks; no inference or runtime activation.
- Four SQLite databases pass read-only `quick_check`: CERT smoke 10,000 events,
  phase6 cohort 978,908 events, June preparation 96,063 windows/973 completed users,
  January preparation 3,291 windows/1,000 completed users. Preparation checkpoint
  window sums match actual tables. The retained 20-user partial June report is
  superseded by the completed checkpoint/report, not unfinished training.
- Three inspection manifests verify their canonical digests; all 406 cache files
  verify recorded hashes, row counts and complete JSONL lines. Bounded CSV prefixes
  are intentional; these checks do not assert full-release ingestion.
- Four historical TAB partial downloads remain untouched and untrusted: ZIPs
  379,336/489,298 bytes have no complete ZIP directory; JSON partials
  5,242,880/1,196,023 bytes are not acquisition inputs. A separate complete
  `tab_ds2/` acquisition already exists; no redownload is needed.
- Original/live 30 hash entries, 19 normalized Flask copies and three archive
  stat observations match. Archive stat checks are not fresh full archive hashes.

Accessible processes are limited to the sandbox PID namespace, so host liveness
cannot be established from `ps` alone. PostgreSQL PID/socket lock files and SQLite
writer-lock databases were preserved; no lock was removed or service restarted.
No accessible preparation/training job or Git index lock was observed. This phase
uses read-only inputs and isolated tests, so it does not need a host restart.

## Annotation feasibility: source screening, not B1 population selection

`research/contextual_feasibility.py` validates the pinned six-file tree and source
bytes before parsing train/dev. Test is hash-only. It reuses strict offset/schema
validation and reviewed exact-span unanimity without creating labels, new groups,
splits or training exports. Raw texts/reviewer IDs remain private; aggregate evidence
is [annotation-screening.json](annotation-screening.json).

| Source-screen quantity | Train | Dev |
|---|---:|---:|
| Source documents | 1,014 | 127 |
| Documents with reviewed sets | 328 | 127 |
| Unreviewed documents | 686 | 0 |
| Unanimous reviewed spans before family quarantine | 23,013 | 6,980 |
| Documents with reviewed presence/boundary/category disagreement | 0 | 61 |
| Documents with overlapping consensus spans | 43 | 5 |
| Consensus overlap pairs | 151 | 12 |
| Reviewed documents exceeding text/UTF-8 bounds | 0 | 0 |
| Reviewed documents with >100 consensus spans | 70 | 10 |

These counts precede B1 family/exclusion gates and differ intentionally from frozen
DS2 manifests. Do not replace DS2's 326/124/127 document populations or results.
The pinned TAB guideline instructs reviewers to correct preannotations and add
missed mentions: this supports an intended exhaustive, machine-assisted release
reference, not proof of independent completeness on natural organizational text.
Exact-span consensus removes disputed mentions; treating the resulting unannotated
regions as negatives would conceal disputes. Overlaps also prevent a lossless
export to a flat nonoverlap NER representation. Preserve annotations and report
excluded documents; do not silently flatten or manufacture negative tokens.

Full-span fitting/export is **not ready**. B1 must freeze a separately versioned,
family-safe eligible development population and explicitly gate disagreements,
overlaps and annotation coverage. A conditional release-reference experiment is
possible after those gates; independent natural-target accuracy needs independent
exhaustive annotation. Organizational sensitivity still lacks authorized inventory,
owner-approved versioned policy/context and blind reviews/adjudication.

## Local contextual NER feasibility

The frozen protocol was written without selecting any model/configuration.
As a feasibility reference, official [3.8.0 model metadata](https://github.com/explosion/spacy-models/blob/master/meta/en_core_web_sm-3.8.0.json)
lists spaCy `en_core_web_sm` as English, CPU-oriented, 12 MB, MIT, requiring
spaCy >=3.8.0,<3.9.0; its source list includes licensed OntoNotes and WordNet.
Model licensing does not grant redistribution of training corpora. Its 18-label
ontology lacks TAB DEM/MISC/CODE; shared names do not guarantee identical scope.
Neither spaCy nor this model is installed in the existing Python 3.14.4 environment.
Wheel/runtime compatibility and local load/inference/RSS are unverified. No install,
model acquisition, speed claim or local model selection occurred.

The official [EntityRecognizer contract](https://spacy.io/api/entityrecognizer)
requires nonoverlapping token spans and flags sensitivity to boundary agreement.
Combined with the actual overlap/disagreement findings, this is a conditional
candidate rather than a validated eight-class replacement. Future use needs pinned
artifact/dependency hashes, retained license notices, compatible isolated runtime,
native-label or explicitly reviewed ontology contract and bounded local probe.
No mapping to financial/credential/business-confidential sensitivity is approved.
Source checks used public documentation only; no document text was transmitted.

## Frozen B evaluation contract

[evaluation-protocol.json](evaluation-protocol.json) is
`automatic-content-evaluation-b-v1`; SHA-256
`b748d50cecad815613e8fee7abe5797aabadc48ebb5b4d5715e9f688fe95dba3`.
No detector/model selection or B manifest creation preceded this freeze.

It separates structured-kind detection, contextual release-reference detection,
historical supplied-span category classification and unavailable organizational
sensitivity. It fixes Unicode offsets, exact one-to-one typed matching, duplicate
handling, null metric denominators, micro/macro aggregation, family bootstrap,
common populations, exclusion/abstention coverage, result caps and resource limits.
There is no finite span-negative universe for TN/specificity. Document false-positive
rates require the matching reviewed reference and are separate from FP/1,000 docs.
Model score AP needs meaningful ranking/support; deterministic candidates provide none.
No synthetic fixture is independent corpus validation.

Historical DS2 test texts/errors have already been inspected in DS3: they cannot
be a new untouched test for this follow-up. B1 may use family-safe original train/dev
for development, preserving official fit/selection roles and excluding historical
test-related families. A new custodian-held natural holdout is needed for new final
accuracy claims. B1/B2 selection, scoring and new training were not executed here.

## Verification and reproduction

12 new tests cover disputed/unreviewed negatives, Unicode offsets, overlap versus
adjacency, complete-write/hash failures, no test parsing, private path bounds and
preservation. The full local suite stalls at the unchanged FastAPI authorization test because
local socketpair send fails EPERM in this sandbox; its 75s diagnostic timed out
after 19 passes and preserved thread stacks. A supplemental isolated run passed
290 tests with the nine FastAPI client checks explicitly deselected, one historical
warning; 22 preserved Flask checks passed. No test source or requirement was changed.
Full exact-SHA CI is the pending independent verification gate, not a claimed local
pass. Local logs: regression-diagnostic.log and regression-available.log in the
ignored recovery directory. All outcomes are recorded in verification.json. Existing backend/frontend/agents/legacy/dependencies, active
policies, supplied-span interface and prior reports remain unchanged.

From repository root, using new ignored output names on every reproduction:

```bash
.local/phase0-venv/bin/python -B -m research.contextual_feasibility --directory research/local/document_sensitivity/tab_ds2 --tree research/local/document_sensitivity/tab-tree.json --output research/local/document_sensitivity/phase_a2_feasibility.json
.local/phase0-venv/bin/python -B -m pytest -q tests/test_contextual_feasibility.py -p no:cacheprovider
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .local/phase0-venv/bin/python -B scripts/verification/phase0_upstream_baseline.py --report .local/phase-a2-recovery/regression.json --log .local/phase-a2-recovery/regression.log
.local/phase0-venv/bin/python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --require-no-skips --report .local/phase-a2-recovery/flask.json
OPENBLAS_NUM_THREADS=1 .local/phase0-venv/bin/python -B scripts/verification/ds2_frozen_preservation.py --output research/local/document_sensitivity/phase_a2_recovery_frozen.json
python3 -B scripts/verification/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output .local/phase-a2-recovery/live.json --compare docs/implementation/phase0/phase0_preservation_before.json
git diff --check
git diff --cached --check
wc -l DATASHIELD_IMPLEMENTATION.md
```

## Boundary, blockers and publication

A2 independent work is complete at its assessment/protocol boundary; contextual
model execution and independent labels remain blocked, not completed validation.
Owner action: supply authorized de-identified pilot inventory, approved versioned
policy/context, two blind independent reviews and distinct conflict adjudication;
separate final-test custody and exhaustive target-span review are required for
new independent end-to-end detection claims. Native Windows checks remain unverified
and belong to F1, not a reason to alter Linux acceptance or enforcement.

Compound sandbox commands initially failed GitHub DNS; direct approved Git
commands succeeded. Fresh fetch/ls-remote confirmed recovered HEAD equals origin.
The shell gh CLI remains network-blocked, but GitHub connector GET freshly verified
A1 closure CI 37770400258 success. Use connector GET for exact-SHA push runs (the
specialized commit-workflow tool filters PR events and cannot establish push CI).
A2 normal source commit/push and exact-SHA CI remain pending below; publication
receipt/actual source SHA will be recorded after the normal commit/push attempt.

```bash
cd /home/sohaib/Insider_Threat_Test_Dataset/DataShield~
git push origin feat/cert-ml-nlp
git rev-parse HEAD
git ls-remote origin refs/heads/feat/cert-ml-nlp
gh run list --branch feat/cert-ml-nlp --limit 5 --json databaseId,headSha,status,conclusion
```

Stop here. Next session: finish any outstanding A2 exact-SHA verification first,
then **B1 only**:
family and annotation-coverage audit plus separately versioned eligible development
manifest under this frozen protocol. Do not proceed directly to B2/C/D or repeat
historical ingestion/fitting/evaluation.
