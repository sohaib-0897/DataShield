# Phase 3 — reproducible chronological behavioral benchmark

Bounded acceptance completed using Phase 2's frozen `cert-user-hour-v1` artifact.
This is an offline research model; no runtime registry, environment flag, API,
policy or application file is changed. Model files, exact partition identities and
scores remain ignored under `research/local/phase3_benchmark_v1/`.

## Population, fitting and leakage controls

The real 10,000-event prefix yields 3,291 active user-hours. Exclude 3,127 hours
with incomplete source coverage; retain 164 fully observed hours. Chronological
boundaries are shared by every user and selected from distinct observed hours
using a 60/20/20 rule, with at least one hour per partition. With four hours this
means 2/1/1 hours, not an exact percentage of rows:

| Partition | Local time on January 2, 2010 | Windows | Users | Positives |
|---|---|---:|---:|---:|
| Train | 08:00–10:00 | 83 | 45 | 0 |
| Validation | 10:00–11:00 | 43 | 43 | 0 |
| Test | 11:00–12:00 | 38 | 38 | 0 |

Purge intervals crossing partition boundaries; no overlaps occurred here. Audit
exact event-key disjointness across all partitions, including nonadjacent ones.
Unknown labels cannot enter training/evaluation. No class balancing, label-based
filtering or test selection changes natural prevalence. Isolation Forest trains
on every eligible training window; contamination by unknown attacks is possible
in broader runs and this population assumption is explicit.

The fixed numeric feature matrix contains only Phase 2 feature names. Median
imputation (missing indicators, retained all-empty features) and standard scaling
fit **only the 83 training rows**. Cold-start nulls remain explicit until fitting;
an all-empty training feature has zero fill and an indicator. Reproducibility
metadata records fitted statistics and row counts. Prior observed per-user windows
may update baselines across split boundaries, as in online inference; future
windows and labels never enter those baselines. Splits are disjoint event windows,
not independent users; this benchmark measures later time on observed users.

CPU Isolation Forest: 200 trees, maximum 83 sampled training rows, seed 42,
one worker. Higher `-score_samples` is more anomalous, not a probability. A simple
median/scaling/logistic baseline is implemented but requires at least two examples
of each class in training and both classes in validation. This real subset cannot
support it. Two-class synthetic fixtures test the implementation without being
reported as CERT detection results.

With two-class validation, maximize validation F1 and break ties toward the higher
threshold. Otherwise use the predeclared 1% **validation alert budget**, not an
accuracy objective. Strict `score > threshold` handles ties conservatively. For
43 zero-positive validation rows, at most floor(0.01 × 43) = 0 alerts are allowed,
so the threshold is the largest validation score, 0.6281862828734063. The test
partition is never used for tuning; the budget need not hold on later test data.

## Actual results and limits

Held-out test: 38 windows, 38 evaluated user-days, zero positives, 2 alerts.
Confusion: TN=36, FP=2, FN=0, TP=0. Precision=0; false-positive rate and false alerts
per evaluated user-day=0.05263157894736842. Recall, F1 and PR-AUC are **undefined**
and serialized as null. No scenarios or incident detection timing are supported.
The denominator is observed active users on this partial day, not complete daily
surveillance. The pipeline reports positive scenario counts and first alert from
first labeled test-window start only when such observations exist; it does not
claim whole-incident onset timing.

One local measurement: training 0.1423 seconds; batch score of 38 held-out windows
0.00954 seconds, or 0.2511 ms/window. This excludes archive processing, ingestion,
window generation and live network/API latency; it is not a throughput guarantee.
See `benchmark.json` for exact values and dependency versions. Independent training
produced identical scores/thresholds and identical joblib SHA-256; serialization
reload produced identical predictions. Artifact SHA-256 is
`8b2335bd964a2bf723da0fbf50ab32cbf88f3a47b052f06186ebbf068331ab42`.

Zero-positive January prefixes cannot establish detection improvement, calibrated
probabilities, recall, supervised performance or sensitivity classification.
A broader chronological population containing June–April incident observables is
needed for those claims. This is completed bounded pipeline acceptance, with
conditional supervised evaluation unavailable, not full-dataset completion.

## Commands and acceptance

From the repository root, reuse the isolated Python environment:

```bash
.local/phase0-venv/bin/python -B -m research.behavioral_ml --features research/local/phase2_features_v1.json --output research/local/phase3_benchmark_v1
.local/phase0-venv/bin/python -B -m pytest -q tests/test_behavioral_research.py tests/test_cert_features.py tests/test_cert_ingestion.py
```

The directory refuses overwrite; use a new name for another run. Defaults are
200 trees and one CPU worker; trees are bounded to 1–1,000. Phase 2 caps event
materialization; original ingestion remains chunked/resumable. Failed fitting
can restart from the frozen feature artifact, with no archive rescan or live data
access. Use `requirements-research.txt` in an isolated environment if dependencies
are missing; exact measured versions are in `benchmark.json`. Artifacts are only
loaded from this locally created run during verification; no external model is
unpickled or registered.

Acceptance tests cover chronological/global boundaries, overlap purge, duplicate
event rejection, natural prevalence, unknown/missing exclusions, training-only
imputation/scaling, validation-only thresholding, zero-positive/null metrics,
supported two-class metrics, conditional supervised fitting and artifact replay.
51 targeted tests passed (8 new numeric checks + prior 43); no skips/failures.
A staged-source isolated full regression run is recorded in `verification.json`.
No frontend changes require repeating its already passing baseline.
