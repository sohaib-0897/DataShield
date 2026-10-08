# NLP follow-up: measured processing, evaluation and limits

Authorized autonomous follow-up, 2026-10-08, `feat/cert-ml-nlp`, starting clean
local/fresh remote `216a0eb2a49161ab2f185af7dec53e035c278a35`. The original
implementation plan ended at Phase 6; this report is a separately authorized
follow-up. Original Phase 4/6 protocols, reports, datasets and models are retained.

## Root cause and exact stage trace

The verified original r4.2 scan covered 32,770,222 source rows. The frozen,
predeclared June 7–21 all-user interval retained 978,908 events, not a full-release
import. Channels: FILE 13,173; HTTP 849,096; EMAIL 78,602; LOGON 25,717; USB
12,320. The complete answer manifest contains 7,323 r4.2 observables. Scoped
source ID plus **all original source fields**, including content/account/date,
joins 70 positives and 978,838 benchmark negatives, zero ambiguous/unknowns;
7,253 answer rows lie outside the retained event cohort. No actor-history label
propagation. Negatives mean absence from the benchmark's complete answers.

940,871 FILE/HTTP/EMAIL content events sanitize to nonempty text; 6,600 repeated
normalized bags. Content only enters text: strip FILE hex header, Unicode and
whitespace normalization, account/PC/address/URL/opaque-ID removal and alphabetic
topic words. No resources, recipient addresses, event IDs, answer metadata or
post-window observations enter predictive text. Join events by frozen event keys;
concatenate in original source_file/source_row order. Bags sort tokens retaining
multiplicity, catching reordered exact content duplicates without learning a
vocabulary. Exact bags do not detect every semantic near duplicate.

96,063 active user-hours aggregate events. 133 incomplete-coverage windows are
excluded (all benchmark negatives); 95,930 fully observed windows contain 41
positive windows and 95,889 negatives. Known channel absence is distinct from
unavailable coverage. Per-user baselines only use completed, fully observed past
windows. Label a window positive if any exact event is positive, unknown if any
ambiguous event and no positive, otherwise benchmark negative.

The same 60/20/20 distinct-hour chronological boundaries as Phase 6 remain:
validation starts 2010-06-15T04:00:00, test starts 2010-06-17T16:00:00. Windows
are disjoint hourly intervals with no event overlap or purging needed. Partial
source edges do not feed history. Train/validation/test positives are 14/19/8.

| Stage | Train | Validation | Test |
|---|---:|---:|---:|
| Fully observed exactly labeled | 58,258 | 25,919 | 11,753 |
| Nonempty mapped text | 54,763 | 24,652 | 10,988 |
| Original strict identity filter | 54,763 | 0 | 0 |
| Original strict final duplicate filter | 54,763 | 0 | 0 |
| Separate known-user, content-disjoint final cohort | 54,763 | 23,616 | 10,553 |
| Alternative positives / negatives | 14 / 54,749 | 19 / 23,597 | 8 / 10,545 |

All 25,919 validation and 11,753 test eligible rows belong to previously observed
identities. The original removal priority reports 1,267/765 missing-text rows,
then 24,652/10,988 seen-identity rows, hiding duplicate rejections. Independently
of identity, 1,036 validation and 435 test rows contain prior-partition content
bags. They are all benchmark negatives; no positive was deleted to obtain clean
metrics. Discarded earlier windows also remain prior observations for both
identity and duplicate checks. `cohort-audit.json` exposes stages, classes and
independent versus priority rejection counts.

**No filtering, label join, chronological boundary or text mapping defect caused
the empty held-out populations.** Full row-by-row parity confirms all 96,063
feature/label/event-key/text/bag results. The strict unseen-user-at-later-time
objective is infeasible on this stable workforce interval. Empty held-outs make
reported incident/scenario disjointness vacuous; this is unavailable evaluation,
not successful generalization. No vocabulary/model was fitted for that protocol.
The nullable-resource issue encountered implementing streaming was corrected; it
was not the cause of the original empty cohorts.

## Separate scientifically limited experiment

`protocol.md` was declared before follow-up test scoring. The alternative asks
whether keyword/numeric signals detect **later activity from the known population**.
It permits continuing users/incidents by objective, discloses overlap, and retains
strict chronological and per-event duplicate-content controls. This is not a
replacement result for the original unseen-user/new-incident/new-scenario study.
Training/test share 968 users, one incident and two scenarios; validation/test
share 968 users, three incidents and two scenarios. Observed past behavior crosses
time boundaries as online history; labels and future observations do not.

Numeric-only, text-only and concatenated numeric+TF-IDF logistic regressions use
exactly the same eligible windows. Median imputation/scaling and TF-IDF vocabulary/
IDF fit training only. TF-IDF: max 10,000 terms, uni/bigrams, sublinear TF. Balanced
class weights apply only during training; seed 42, max_iter 1000, all fits converged.
Validation alone chooses strict score > threshold maximizing F1, ties favoring
higher thresholds. All three thresholds were written to `frozen_thresholds.json`
before loading test rows for scoring. No test resampling or post-test tuning.
Decision-function outputs are **uncalibrated margins**, not probabilities.

Test population: 10,553 windows; 8 positives / 10,545 benchmark negatives;
prevalence 0.075808%, 1,827 observed user-days, three incidents (scenarios 2/3).
This is natural prevalence **within the explicitly content-disjoint population**;
compare these models with each other, not directly with the different Phase 6
11,753-window population. All original Phase 6 results remain intact.

| Baseline | TN | FP | FN | TP | Precision | Recall | F1 | Average precision | False alerts / 1,000 windows |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Numeric | 10,091 | 454 | 7 | 1 | .002198 | .125 | .004320 | .007826 | 43.020942 |
| Text | 10,544 | 1 | 7 | 1 | .500000 | .125 | .200000 | .154422 | .094760 |
| Combined | 10,520 | 25 | 6 | 2 | .074074 | .250 | .114286 | .167069 | 2.368995 |

`comparison.json` records full precision/recall/F1/AP, prevalence, confusion,
validation metrics, frozen thresholds, timing, group overlap and model/software
provenance. Average precision uses continuous margins, not threshold decisions.
All three serialized reloads and independent refits reproduced test scores,
validation thresholds and artifact hashes. No test-dependent winner was selected
or activated. Vocabulary boundary and test-label perturbation tests verify fitting
independence. Original strict metrics remain undefined/unavailable, not zero.

Text's .50 precision is just one true and one false alert. Combined detects two
of three scenario-3 windows and no scenario-2 windows; numeric and text each detect
one scenario-3 window and no scenario-2 windows. All methods miss all five
scenario-2 positives. None of the eight positive windows has FILE signals; none
of the errors is a cold start. Numeric has 454 false alerts, 22 after hours/49
with FILE events. Text's one false alert occurs during work hours with no FILE events.
Combined has 25 false alerts, nine after hours/three with FILE events. Associations
are descriptive, not causal. `error_analysis.positive_scenarios` in the saved
comparison counts observable provenance records, while `test.scenarios` correctly
counts distinct labeled windows; do not conflate those granularities.

Eight test positives and three supported continuing incidents cannot establish
robust deployment quality. CERT topic keyword content is synthetic, so lexical
success need not transfer to real documents or endpoints. No calibrated risk,
new-incident/general workforce improvement or automatic blocking is established.

## Processing, resources and reproducibility

[Streaming evidence](streaming.md) contains exact commands/checkpoints. Actual
stream preparation retained all 978,908 events and 96,063 windows, 940,871 texts,
using 425.313 MiB peak RSS. Twenty-user checkpoint took 6.480 seconds; resume of
953 remaining users took 122.668 seconds. Completed replay took 4.219 seconds,
added no users/rows and left the prepared DB unchanged. Full frozen parity took
56.333 seconds / 928.453 MiB; January parity passed before larger June processing.
Fixture interruption inside a user transaction rolls back all partial windows,
bags and checkpoint counts; recomputed history is past-only. Hash/settings guards
reject changed source/answer inputs or incompatible output schemas.

The complete three-model training/validation/test plus independent refits took
499.263 seconds, **8,726.004 MiB peak RSS (8.52 GiB)**. The 16 GiB RAM/4 GiB swap
machine completed it, but TF-IDF candidate vocabulary construction and full
training matrices still materialize. The stream preparation memory improvement
does not make full-release model fitting bounded. The training interface refuses
oversized cohort payloads, but that bound is not an RSS limit. Full 32.77M-row
import/preparation/evaluation was not run; resources for full training remain a
blocker requiring external-memory vocabulary/fit design or explicit training
sampling (training only) in a separately declared experiment.

```bash
# Runnable follow-up, from repository root; preserve outputs by choosing new names.
.local/phase0-venv/bin/python -B -m research.nlp_evaluate --prepared research/local/nlp_june_stream.sqlite --output research/local/nlp_known_users_v1
.local/phase0-venv/bin/python -B -m research.nlp_replay --prepared research/local/nlp_june_stream.sqlite --benchmark research/local/nlp_known_users_v1 --report research/local/nlp_actual_shadow_replay_final.json
.local/phase0-venv/bin/python -B -m pytest -q tests/test_nlp_followup.py tests/test_stream_prepare.py
.local/phase0-venv/bin/python -B scripts/verification/phase0_upstream_baseline.py --report .local/nlp-isolated-tests-final.json --log .local/nlp-isolated-tests-final.log
.local/phase0-venv/bin/python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --require-no-skips --report .local/nlp-preserved-flask-tests.json
python3 -B scripts/verification/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output .local/nlp-preservation.json --compare docs/implementation/phase0/phase0_preservation_before.json
```

Python 3.14.4, sklearn 1.9.1, numpy 2.5.3, joblib 1.6.0. Existing ignored
environment reused. No dependencies installed/updated. Final test counts and
publication are in `verification.json` and `publication.json` alongside this report.
No raw text, identities, predictions keyed to users, datasets or models enter Git;
only code, aggregate/hash evidence and docs. Artifact paths (all ignored):
`research/local/nlp_january_stream.sqlite`, `nlp_june_stream.sqlite` (936 MiB),
`nlp_known_users_v1/` (models, scores, frozen thresholds, report), and
`nlp_actual_shadow_replay_final.json`. Frozen January/June research artifacts and
original archives/live files are unchanged.

## Sensitivity and advisory integration

[Supervision search and exact corpus contract](sensitivity.md) records local and
official public-source review. No defensible independently labeled sensitivity
corpus was available among reviewed sources; no third-party dataset was downloaded.
The runnable separate sensitivity interface was exercised only by synthetic tests
with `FIXTURE_ONLY_NOT_VALIDATED` status. CERT/PII/model/rule labels cannot enter
independent evaluation. No authentic sensitivity model/training/accuracy claim.

`research.nlp_shadow.NLPShadow` defaults disabled and only supplies offline shadow
evidence. It preserves the original response/rule decision, accepts completed fully
observed CERT-schema windows with normalized text, and validates a deliberately
pinned local report, feature/software/schema/provenance, threshold/cohort and all
model digests before unpickling trusted local artifacts. Changed/incompatible/
missing inputs fall back to rules. Model bytes are hash checked before loading.
No runtime routes, services, policies or registry were wired/changed. First/last
eligible test windows yielded six matching scores within 1e-12, preserved rule
responses and no automated blocking; this is compatibility acceptance, not live
endpoint evaluation. Existing Flask/FastAPI advisory regressions also pass.

Exact next engineering step: predeclare an external-memory training-vocabulary/
sparse-matrix preparation experiment, verify its feature/score parity against the
frozen known-user run, then attempt a larger chronological cohort within measured
resources. Independently human-annotated policy sensitivity documents are a
separate data prerequisite. Strict unseen-user/generalization remains unavailable;
Windows/device, PostgreSQL and Docker deployment verification remain unperformed.
