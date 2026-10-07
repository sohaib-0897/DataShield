# Phase 6 — measured bounded evaluation and handover

Implementation and bounded acceptance are complete. Full-release materialized
evaluation is resource-limited in the current pipeline; no full evaluation or
endpoint validation is claimed. The existing implementation plan ends at 6.

## Actual source and cohort coverage

The full r4.2 archive was CRC/EOF validated: 28 members, 16,181,487,042 expanded
bytes and 32,770,222 event-source rows. Retain every user/event in the predeclared
2010-06-07 00:00 inclusive through 2010-06-21 00:00 exclusive interval. This is
978,908 events (13,173 file; 849,096 HTTP; 25,717 logon; 78,602 email; 12,320
device), not a full-release import. Zero invalid rows, duplicates or ID conflicts.
Indexed caches retain exact original CSV positions; SQLite chunk progress survived
fixture interruptions. The actual idempotency replay added no rows and preserved
every counter. Source/cache hashes are recorded in `cohort-scan.json`/`ingestion.json`.

The complete verified answers map joins 70 exact malicious event observables and
978,838 benchmark negatives, with 7,253 unmatched answer observables and zero
unknown/ambiguous joins. This does not propagate labels across actor histories.
All original CSV fields must match, including account, timestamp and content.
The master actor/observable subject distinction remains important for scenario 3.
Negatives mean absence from supplied complete benchmark answers, not proved
real-world innocence. Labels/scenarios/identifiers never enter numeric features.

96,063 active user-hours yield 95,930 fully observed windows. Exclude 133 hours
with partial source coverage by availability, without class-based filtering.
Version/work hours/past-only per-user baseline match Phase 2. Missing hours do
not imply observed inactivity; unknown signal counts are not zero.

| Partition | Windows | Positives | Start | End (exclusive) |
|---|---:|---:|---|---|
| train | 58,258 | 14 | 2010-06-07T07:00:00 | 2010-06-15T04:00:00 |
| validation | 25,919 | 19 | 2010-06-15T04:00:00 | 2010-06-17T16:00:00 |
| test | 11,753 | 8 | 2010-06-17T16:00:00 | 2010-06-20T16:00:00 |

All users share chronological boundaries; event keys and windows are disjoint.
No overlapping windows required purging. Training alone fits imputation/scaling;
validation alone selects the strict F1-maximizing thresholds, with ties preferring
the higher threshold. Test data never tunes models, budgets, thresholds or cohort
selection. Isolation Forest uses every eligible training window, without label
cleaning; logistic regression uses balanced class weights only during training.
Validation/test preserve their natural prevalence. Numeric inputs contain no user,
PC identifier, incident or scenario identifiers; PC novelty is past-only per user.

This is later-time evaluation on observed users, not unseen-user/incident quality.
970 users overlap train/test. One incident overlaps train/test, three overlap
validation/test and two scenarios overlap each pair. No future events or labels
enter features; past windows may include earlier activity from continuing incidents.
Do not claim independence/generalization to new users/incidents from these metrics.
`population-audit.json` exposes these limitations; strict text controls below
refuse an identity/incident-contaminated text comparison.

## Common-population results and errors

The held-out population is identical for every method: 11,753 windows, 8 positives
(0.0680677% prevalence), 970 users, 1,919 observed user-days, three supported
incidents, scenarios 2 and 3. User-day rates refer to observed partial days, not
complete daily surveillance. The research rule is fixed before evaluation:
`file_count > 0 AND after_hours_fraction > 0`. This identifies an hourly co-occurrence,
not necessarily an after-hours file copy. It is not the application policy: CERT
has no role, protected hash, sensitivity, upload permission or blocking evidence.
Combined decisions are a fixed Boolean OR; no learned fusion or policy change.

| Method | TN | FP | FN | TP | Precision | Recall | F1 | PR-AP | FP/observed user-day |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fixed_research_rule | 11,581 | 164 | 8 | 0 | 0.000000 | 0.000 | 0.000000 | 0.000681 | 0.085461 |
| isolation_forest | 10,294 | 1,451 | 5 | 3 | 0.002063 | 0.375 | 0.004104 | 0.003097 | 0.756123 |
| logistic_regression | 11,197 | 548 | 7 | 1 | 0.001821 | 0.125 | 0.003591 | 0.007288 | 0.285565 |
| rule_or_isolation_forest | 10,293 | 1,452 | 5 | 3 | 0.002062 | 0.375 | 0.004101 | 0.001199 | 0.756644 |
| rule_or_logistic_regression | 11,036 | 709 | 7 | 1 | 0.001408 | 0.125 | 0.002786 | 0.000772 | 0.369463 |

The rule misses all eight positives because their hours have no FILE signal; its
164 false-positive hours have legitimate benchmark FILE/out-of-hours co-occurrence.
Isolation Forest detects all three scenario-3 positive windows and misses all five
scenario-2 windows. Of 1,451 false-positive hours, 708 include out-of-hours activity
and 453 include FILE copies. Logistic detects one scenario-3 window and misses the
other two plus all five scenario-2 windows; 30 of its 548 false-positive hours are
after hours and 67 include FILE copies. No test errors are cold starts. These are
descriptive aggregate associations, not causal explanations or labeled innocence.

The OR variants add false alerts without detecting another positive. Precision
and F1 are very low for both models; no deployment improvement, calibrated risk
or validated fusion is established. Eight positives provide limited support. No
post-test tuning was attempted. Anomaly scores are not probabilities; balanced
logistic outputs are uncalibrated. Binary-rule/OR PR-AP has a coarser ranking than
continuous model scores. All confusion/metric/error values are in `comparison.json`.

First alert timing is measured from the first labeled TEST window start to the
detected window end, not full incident onset. Isolation Forest detects one of
three supported incidents with 3,600-second timing; logistic one with 86,400
seconds. This does not establish endpoint response latency.

Independent fits, reloads, predictions, thresholds and serialized model digests
matched for both models. Fixed seed 42, 200 trees and one CPU worker; anomaly
sample bound 256. Training took 2.3131 seconds. Test batch inference means were
0.008084 ms/window for Isolation Forest and 0.000254 ms/window for logistic,
excluding ingestion/features/network/UI. These are single local observations.
`benchmark.json` records software, model hashes and exact validation thresholds.

## Text, document and shadow acceptance

940,871 content events were sanitized; 6,600 duplicate normalized keyword bags
were found. Strict chronological identity/duplicate controls leave train/validation/
test populations 54,763/0/0. Training has 14 positives but validation/test are empty
after removing past identities and missing text. No balancing, malicious-row
dropping to clean scenario groups, fixture positives or relaxed controls are used.
TF-IDF comparison is unavailable, not zero accuracy. The independent sensitivity
corpus remains NOT_ESTABLISHED. Phase 4 parser/rule tests remain tests, not real
sensitivity evaluation. `text-study.json` retains the complete aggregate audit.

Both Phase 5 adapters also scored the first and last expanded held-out windows
with frozen-score equality; four observations shared one artifact load and retained
rule results. This is an artifact compatibility smoke check, not a replay of all
11,753 windows through application services. Phase 5 separately replayed all 38
historical smoke windows through both adapters and persisted idempotent sidecars.
Nothing was installed into a running app, activated or used to block transfers.

## Acceptance, preservation and remaining limits

142 isolated pytest checks passed, no skips, one existing Starlette/httpx warning.
The 22 preserved Flask checks also passed with no skips; Windows dependencies were
mocked. Tooling tests cover cohort selection/unsafe archives/budgets/chronology,
indexed row positions, interruption/resume, unavailable models/signals, artifact
hash/schema/provenance, sidecar schema, authorization, replay, fixed unions and
threshold equivalence. An initial larger-bound regression captured defaults too
early; runtime defaults and the existing positive-bound error contract were restored.
The original byte-bound rejection test was preserved. Full source checks follow
the staged-source disposable SQLite runner; no live database tests were used.

30 original source/live hashes, 19 copied LF-normalized source hashes, three input
stat records and all upstream application trees are unchanged. Historical January
store/features/model fingerprints match. No raw rows, text, model binaries, live
files, secrets, environments or large artifacts are staged. The fresh npm review
confirms 106 open findings and development tooling in Docker; no force upgrade.

Measured peak RSS: features 2.83 GiB, benchmark 0.98 GiB, text 3.73 GiB. Scan took
660.858 seconds; ingestion 98.82 seconds; idempotency 13.12 seconds; features 21.75
seconds; benchmark with replay 9.98 seconds; text 84.89 seconds. The two-week cohort
fits measured available memory; all 32.77 million rows cannot be materialized by
the current pipeline within it. Disk was sufficient; no credential/network blocker
remained for publication or npm audit. Full-release evaluation remains pending a
streaming preparation path or sufficient memory. Model/feature/text artifacts stay
in ignored `research/local/`, not the runtime registry.

Native Windows monitors/physical devices and PostgreSQL are unverified. Docker
binary is absent, so container/startup verification is also unverified. Sensitivity
supervision and unseen-user held-out text are missing. Existing endpoint policies
and application behavior are preserved, with research adapters disabled by default.

Exact commands and startup limitations are in `handover.md`; resource details in
`preflight.json`/`resource-results.json`; preservation in `preservation.json`; fresh
npm review in `npm-review.md`. No Phase 7 exists or was added. Exact next engineering
step: implement streaming feature/text preparation with parity against the frozen
bounded cohort before attempting full-release chronological evaluation.
