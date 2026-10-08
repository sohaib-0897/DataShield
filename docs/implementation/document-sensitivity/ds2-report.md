# DS2: offline supplied-span entity-category baseline

Completed 2026-10-08. Started clean on `feat/cert-ml-nlp` at
`67f6c02149558ec1205dd0e3eabd4ef8a5ea9a5d`; fresh remote SHA matched. No applicable
AGENTS.md was found in the checkout, parent workspace or ancestors. Read the
implementation memory, CONTEXT.md and complete DS1 report. No subsequent changes
existed to reconcile. DS1 and CERT work were preserved, not repeated. The user's
DS2 request expressly includes final evaluation; it supersedes the historical
DS1 plan assigning that evaluation to DS3. Stop after DS2; no integration occurred.

The **only supported task is supplied-span entity-category classification**:
span boundaries are inputs. This is not automatic entity detection, whole-document
sensitivity classification, or a validated NORMAL/HIGH/CRITICAL classifier. The
new models are offline research artifacts and have no runtime registry/wiring.

## Acquisition and provenance

Retried the official DS1 [TAB repository](https://github.com/NorskRegnesentral/text-anonymization-benchmark/tree/558e09e26d6b36f5f78440074e6a233946d98bd9)
raw HTTPS sources at pinned revision `558e09e26d6b36f5f78440074e6a233946d98bd9`.
All six files completed on their first DS2 attempt: LICENSE.txt, README.md,
guidelines.md and the train/dev/test JSONs. Sizes and Git blob SHA-1 IDs match the
DS1 pinned tree, whose SHA-256 is checked independently against DS1 evidence.
New local SHA-256 checksums are recorded in [ds2-acquisition.json](ds2-acquisition.json).
No separate publisher SHA-256 archive checksum was available; Git blob identities
are the available publisher checksums, not a cryptographic signature.

`research.tab_acquire` limits attempts to two and each transfer to 120 seconds,
with a ten-second connect timeout, explicit byte bounds, HTTPS-only redirects and
an outer subprocess deadline. It resumes its own pinned-file partials using HTTP
Range when supported; if Range is rejected, it preserves that partial separately
and restarts within the attempt budget. No manifest is published until every
file passes size/blob/license checks. Tests cover timeout/incomplete acquisition,
corrupt completion, successful resume and Range rejection. Successful DS2 transfer
needed no actual resume; support was tested with inert fixtures. Original DS1
partials were untouched and never parsed. Partial bytes are never training data.

MIT corpus licensing is confirmed by the pinned README and license; the complete
copyright/permission notice remains beside the private corpus. JSON structure,
all offsets, span text, label vocabularies and reviewed-set references pass the
existing inventory. Preparation rechecks pinned blobs independently of mutable
acquisition metadata. Raw files remain unmodified in private ignored storage.

## Actual annotations and taxonomy reconciliation

The acquired files contain **1,268 documents, 2,208 annotation sets and 155,006
raw mention-annotation records**. Actual raw class counts match the DS1 paper
counts. There are 956 quality-reviewed sets across 582 documents. These are
machine-assisted annotations corrected by humans, with review metadata; multiple
annotators are competing judgments, not independent copies of a training sample.

| Original TAB target | Raw records | Mapping decision |
|---|---:|---|
| CODE | 6,471 | Keep CODE; identifiers are not necessarily credentials |
| DATETIME | 53,668 | Keep DATETIME; dates/durations do not imply confidentiality |
| DEM | 8,683 | Keep DEM; contextual personal attributes remain entity semantics |
| LOC | 9,982 | Keep LOC; locations/addresses are not organizational policy labels |
| MISC | 7,044 | Keep MISC; broad residual descriptions need cautious interpretation |
| ORG | 40,695 | Keep ORG; organization names are not business-confidential labels |
| PERSON | 24,322 | Keep PERSON; supplied names/aliases are not whole-document labels |
| QUANTITY | 4,141 | Keep QUANTITY; a number/amount alone does not establish financial content |

All eight observed categories are supported in their original vocabulary; no
unexpected source category occurred. **No mapping** into the DS1 four document
categories or three organizational levels is justified. Identifier masking and
confidential-attribute annotations are preserved in the original files but never
become model inputs, labels or sensitivity substitutes.

Canonical benchmark policy was declared before fitting: use `quality_checked`
sets only; retain an exact span once only if every reviewed set contains it and
agrees on its category. Unreviewed documents, reviewed presence/boundary differences
and category conflicts abstain. This policy does not create newly adjudicated gold;
its result is conditional on released human review and agreement. Original
annotations, annotation IDs and disagreements stay in the untouched source files.

The audit finds 108,016 distinct within-document exact-offset spans, 936 spans
with raw category disagreement, 3,321 reviewed presence/boundary disagreements,
162 reviewed category disagreements and 1,395 overlapping reviewed span pairs.
It also finds 17 duplicate-offset records within individual sets, seven with
conflicting categories in unreviewed sets. The explicit conflict guard prevents
silent last-record replacement; agreeing duplicates are counted once. Reviewed
unanimous overlapping spans remain supplied-span examples, within one family.
The six agreeing reviewed duplicate records do not change retained sample counts.

## Family audit, exclusions and frozen manifests

Grouping uses original document ID; NFKC/case-folded alphanumeric normalized
content; protected task/applicant identity; and exhaustive length-filtered
five-word-shingle comparisons with Jaccard >=0.8. All matching relationships are
closed transitively. Metadata is used only for grouping/provenance, never predictive
inputs. This handles observed copies/related cases and near duplicates; source
metadata supplies no authoritative external version lineage, so unseen relations
cannot be certified. The available inputs have no separate chunk/version objects;
all annotator sets and spans inherit their source document's family.

There are 1,249 observed families, six near-duplicate pairs and seven families
crossing official splits. Official splits therefore are not accepted unchanged as
leakage-safe. Official test documents/assignments are preserved; related earlier
material is quarantined, with validation taking priority over training. Seven train
and three dev documents are quarantined, excluding 244 otherwise eligible spans.
686 documents lack reviewed sets; five also belong to the quarantined families.
These overlapping exclusion reasons are not added as independent document counts.
681 non-quarantined unreviewed documents plus ten quarantined documents leave
577 benchmark documents. Exclusions and edge reasons are recorded privately.

| Frozen partition | Documents | Families | Supplied spans |
|---|---:|---:|---:|
| Train | 326 | 325 | 22,939 |
| Validation | 124 | 124 | 6,810 |
| Test | 127 | 125 | 6,713 |

| Class | Train | Validation | Test |
|---|---:|---:|---:|
| CODE | 765 | 397 | 328 |
| DATETIME | 8,346 | 2,470 | 2,515 |
| DEM | 1,271 | 327 | 287 |
| LOC | 1,418 | 457 | 484 |
| MISC | 969 | 183 | 192 |
| ORG | 6,158 | 1,640 | 1,722 |
| PERSON | 3,185 | 1,150 | 1,012 |
| QUANTITY | 827 | 186 | 173 |

Retained family overlap is zero. Repeated vocabulary remains: 9,098 entity strings
occur in multiple documents, 4,267 cross official splits, including 370 PERSON
strings. Generic/referenced entities such as courts, locations and dates do not
establish a common source family. Protected subjects/applicants are grouped;
this is **family-disjoint, not entity-vocabulary-disjoint** evaluation. Counts are
span-weighted and repeated mentions are correlated; no independent-sample uncertainty
or unseen-name generalization claim follows from pooled scores.

Manifests, source/text/record hashes, reviewed-set counts and exclusions were frozen
before final training in `ds2_prepared_v2/`. Model selection never loaded the test
manifest. Mechanical test inventory/grouping/consensus preparation accessed raw
annotations but no model fitting, tuning or manual test-text inspection occurred.
Validation/test prevalence was not balanced. [ds2-preparation.json](ds2-preparation.json)
contains the aggregate source/split counts and hashes; private per-document manifests
and original annotation content are excluded from Git.

## CPU training and measured held-out results

Prespecified sparse TF-IDF word 1–2 grams plus character 3–5 grams, minimum frequency
2, at most 20,000 features per channel, float32 features, LinearSVC C=1, no class
weighting, seed 42. BLAS/OpenMP threads are capped at one; commands enforce 300 CPU
seconds, 4 GiB address space, 100,000 rows and 80 MiB input-file bounds. No row
sampling was necessary. Only training fits vocabulary, IDF and classifier.

Two declared inputs: entity text alone, and the supplied span with marked boundaries
and at most 160 original characters on each side. Context is justified by ambiguity
of names/abbreviations, but it is tested as a separate candidate. Validation macro
F1 selects the candidate; ties prefer entity-only. Prediction is multiclass argmax,
with no threshold search, calibration, refit on validation or probability claim.
The scores are **uncalibrated decision margins**.

Validation macro F1: entity **0.818999**, context **0.750880**. Entity-only is selected
before test access. Both predeclared candidates and the training-majority baseline
are evaluated on the same frozen test population, without subsequent selection.

| Test system | Macro F1 | Micro F1 |
|---|---:|---:|
| Selected entity-only | 0.776293 | 0.885595 |
| Bounded context | 0.737904 | 0.878147 |
| Training-majority DATETIME | 0.068135 | 0.374646 |

| Selected model class | Precision | Recall | F1 | AP | Support |
|---|---:|---:|---:|---:|---:|
| CODE | .979730 | .884146 | .929487 | .966630 | 328 |
| DATETIME | .992866 | .996024 | .994442 | .999770 | 2,515 |
| DEM | .555556 | .662021 | .604134 | .690263 | 287 |
| LOC | .818182 | .688017 | .747475 | .829762 | 484 |
| MISC | .405882 | .359375 | .381215 | .423202 | 192 |
| ORG | .929870 | .831591 | .877989 | .948901 | 1,722 |
| PERSON | .786977 | .967391 | .867908 | .979024 | 1,012 |
| QUANTITY | .769634 | .849711 | .807692 | .777710 | 173 |

AP means one-versus-rest average precision from margin scores, not interpolated
PR area and not calibration. All eight full-test classes exceed the declared five
positive/five negative support minimum. Scoreless majority/rule systems have null
AP; undefined precision/recall remain null. Confusion matrices, TP/FP/FN and all
candidate per-class results are in [ds2-evaluation.json](ds2-evaluation.json).

Existing `research.documents` email/CNIC patterns are compared only as a narrow
CODE proxy with abstention elsewhere; this is not an eight-category detector.
No test span matches either pattern: zero coverage, undefined conditional precision,
and no meaningful claim of rule superiority/inferiority. CODE remains broader than
these patterns and never maps to credentials or organizational levels.

MISC is weak (69/192 correct); DEM and LOC also trail common classes. The largest
confusions include ORG→PERSON (106), ORG→DEM (74) and LOC→ORG (63). No raw examples
are published. For the selected model, seen entity text has 3,107 spans and macro/
micro F1 .937098/.976505; unseen text has 3,606 and .702746/.807266. All 258 repeated
PERSON spans are correct, underscoring the easier repeated-name stratum. 220 spans
with raw category disagreement have macro/micro F1 .349630/.450000. Categories
with <=1,000 training spans yield 693 test examples and macro/micro F1 .762819/
.730159; this conditional macro averages only classes with positive truth support.
These findings were examined after reporting was frozen and did not trigger tuning.

English legal narratives differ from corporate financial/credential/business
materials. Public legal PII does not imply organizational restriction. TAB cannot
validate extraction coverage, unknown spans, public PII policy false alarms, ordinary
financial reports, business confidentiality or credential-policy strata.

Two independent fits on identical frozen rows produce identical compressed model
hashes; serialized reload validation margins match exactly. The initial v1 preparation
and fit are retained privately: the subsequent duplicate-offset guard changed audit
metadata, but actual eligible rows/manifests and both model hashes were unchanged.
Final v2 artifacts bind the expanded audit. [ds2-reproduction.json](ds2-reproduction.json)
and [ds2-baseline.json](ds2-baseline.json) record hashes/configuration/software.

## Organizational sensitivity remains blocked

The bounded local search covered checkout/research storage and workspace,
Downloads, Documents and Desktop annotation/review filenames. Only existing rules,
source, synthetic tests and the DS1 inert blank packet were found; **zero independent
organizational documents or policy/context labels were verified**. Filename/hash
policies, CERT labels, TAB labels and synthetic examples cannot fill this gap.
No organizational fitting or evaluation ran.

The exact required packet and next human action are in
[ds2-human-annotation-packet.json](ds2-human-annotation-packet.json). Owner must supply
an approved versioned policy plus authorized de-identified 100-document pilot,
original-container hashes, family/version relations, authorization/retention and
audience/release/harm context. Generate private blank packets through the DS1 CLI;
two blind independent reviewers supply timestamped labels/evidence, with a distinct
third reviewer for conflicts. Unknown remains null. Freeze the guide after pilot
review before the proposed 1,200-document corpus; pilot is not final test data.
The existing CLI validates declarations, not external independence/authorization;
container provenance, evidence spans and timestamps require export validation
before organizational training. No new labels or private documents were invented.

## Preservation, resources and exact commands

[ds2-verification.json](ds2-verification.json) records measured stage wall times and
maximum RSS separately, including initial preparation/independent fitting. Peaks
are GNU time per-command process/child maxima, not simultaneous aggregate memory.

| Stage / final command | Wall seconds | Peak MiB |
|---|---:|---:|
| Acquisition | 32.65 | 43.492 |
| Final preparation | 26.92 | 455.863 |
| Final training/validation/reload | 81.67 | 908.094 |
| Final evaluation | 21.62 | 349.953 |
| Frozen preservation | 12.98 | 789.117 |
| Original/live/archive preservation | .13 | 20.734 |
| Preserved Flask regressions | 1.83 | 101.461 |

Initial preparation: 23.74s / 455.602 MiB; independent initial fit: 82.03s /
900.336 MiB. Those runs are included in resource evidence, not hidden as final-only
costs. Test was evaluated once. Regression fixtures use inert synthetic examples;
they are not independent corpus validation.

- Pre-existing isolated suite: 175 passed, no failures/skips, existing Starlette
  httpx deprecation warning. Final isolated suite: **189 passed**, same warning.
- Targeted DS2 + document checks: **56 passed**, including 14 DS2 guards.
- Preserved Flask: **22 passed**, no skips/errors, temporary DBs/mocked devices.
- Original/live: all 30 hash entries and three archive stat observations match.
  Archive stat preservation is not a new whole-CERT-archive hash.
- All **13 frozen artifacts match**, using existing `research.cert_features.load_artifact`
  for canonical feature payloads and whole-file SHA-256 elsewhere. No feature,
  ingestion, scoring or CERT-training rerun. [Frozen evidence](ds2-frozen-preservation.json).
- Application/backend/frontend/ml/legacy/agents trees and prior reports remain
  unchanged. No monitor/server, production migration, active model or decision change.
- Implementation memory is 172 lines, strictly below 200. No pre-existing failure
  or DS2 regression remains. Native Windows/hardware/PostgreSQL checks remain outside
  this offline phase's evidence; no new claim is made.

Exact executed corpus/model commands, from the existing repository root:

```bash
/usr/bin/time -v -o .local/ds2-acquisition-resource.txt .local/phase0-venv/bin/python -B -m research.tab_acquire --directory research/local/document_sensitivity/tab_ds2 --tree research/local/document_sensitivity/tab-tree.json --report research/local/document_sensitivity/ds2-acquisition.json --attempts 2 --timeout 120
/usr/bin/time -v -o .local/ds2-preparation-resource.txt .local/phase0-venv/bin/python -B -m research.tab_prepare --directory research/local/document_sensitivity/tab_ds2 --output research/local/document_sensitivity/ds2_prepared_v1
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /usr/bin/time -v -o .local/ds2-training-resource.txt .local/phase0-venv/bin/python -B -m research.tab_baseline train --prepared research/local/document_sensitivity/ds2_prepared_v1 --output research/local/document_sensitivity/ds2_models_v1
/usr/bin/time -v -o .local/ds2-preparation-final-resource.txt .local/phase0-venv/bin/python -B -m research.tab_prepare --directory research/local/document_sensitivity/tab_ds2 --output research/local/document_sensitivity/ds2_prepared_v2
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /usr/bin/time -v -o .local/ds2-training-final-resource.txt .local/phase0-venv/bin/python -B -m research.tab_baseline train --prepared research/local/document_sensitivity/ds2_prepared_v2 --output research/local/document_sensitivity/ds2_models_v2
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /usr/bin/time -v -o .local/ds2-evaluation-resource.txt .local/phase0-venv/bin/python -B -m research.tab_baseline evaluate --prepared research/local/document_sensitivity/ds2_prepared_v2 --models research/local/document_sensitivity/ds2_models_v2 --output research/local/document_sensitivity/ds2_evaluation_v2
```

Exact final verification commands (initial regression used `before` filenames):

```bash
/usr/bin/time -v -o .local/ds2-targeted-resource.txt .local/phase0-venv/bin/python -B -m pytest -q tests/test_tab_ds2.py tests/test_document_sensitivity_phase1.py tests/test_document_research.py -p no:cacheprovider
/usr/bin/time -v -o .local/ds2-final-regression-resource.txt .local/phase0-venv/bin/python -B scripts/verification/phase0_upstream_baseline.py --report .local/ds2-final-regression.json --log .local/ds2-final-regression.log
/usr/bin/time -v -o .local/ds2-flask-resource.txt .local/phase0-venv/bin/python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --require-no-skips --report .local/ds2-flask.json
/usr/bin/time -v -o .local/ds2-live-preservation-resource.txt python3 -B scripts/verification/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output .local/ds2-live-preservation.json --compare docs/implementation/phase0/phase0_preservation_before.json
/usr/bin/time -v -o .local/ds2-frozen-resource.txt .local/phase0-venv/bin/python -B scripts/verification/ds2_frozen_preservation.py --output research/local/document_sensitivity/ds2-frozen-check.json
git diff 67f6c02149558ec1205dd0e3eabd4ef8a5ea9a5d -- backend frontend ml legacy agents research/documents.py research/document_annotation.py research/sensitivity_training.py docs/implementation/nlp-followup
git diff --check
git diff --cached --check
wc -l DATASHIELD_IMPLEMENTATION.md
```

Private artifact root: `research/local/document_sensitivity/`. Source: `tab_ds2/`;
final manifests and grouping evidence: `ds2_prepared_v2/`; configuration, software,
validation selection and inactive models: `ds2_models_v2/`; evaluation and hashed
prediction join records: `ds2_evaluation_v2/`. Original DS1 partials and initial v1
runs remain preserved. Everything under research/local is ignored. Public evidence
contains only aggregate metrics, counters, hashes and source URLs, not corpus text,
per-document identifiers, raw predictions or binaries.

For reproducibility, use the recorded environment/software and a **new** output
folder: all preparation/model/evaluation outputs refuse overwrite. Acquisition is
resumable in its pinned directory, with a new report path; it re-verifies existing
complete files before proceeding. Source script hashes are in verification evidence.
No further evaluation or new phase is needed for this DS2 checkpoint.

Publication uses only relevant source/tests/documentation: review staged files,
commit, `git push origin feat/cert-ml-nlp`, then compare `git ls-remote origin
refs/heads/feat/cert-ml-nlp` with `git rev-parse HEAD`. Exact final SHA and actual
push outcome are recorded in the final handoff and Git; they cannot be embedded
in their own commit. If publication fails, keep the local commit and recover with
`git push origin feat/cert-ml-nlp`; never force-push. The exact next substantive
human action is the owner-approved policy/context and blind-review pilot above.
