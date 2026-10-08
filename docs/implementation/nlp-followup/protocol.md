# Declared NLP follow-up protocol

Declared before fitting or inspecting follow-up test predictions (2026-10-08).
Keep Phase 4/6 strict unseen-user/incident/scenario experiment unchanged.

The separate `known-users-later-time-v1` experiment estimates malicious keyword
window detection on later activity from the existing population. Use the frozen
June 7–21 cohort and original 60/20/20 distinct-hour boundaries. Seen users and
continuing incidents are allowed by this objective and disclosed; this cannot
measure unseen-user, new-incident or new-scenario generalization. No identity,
resource, answer/scenario metadata or future evidence enters model inputs.

Require fully observed, exactly labeled windows and nonempty sanitized content.
Reject any later window containing an event keyword bag observed in any earlier
partition, including discarded windows. Preserve natural prevalence within this
explicit content-disjoint eligible population; report exclusions by class.
Training vocabulary: TF-IDF, 10,000 terms, uni/bigrams, sublinear TF. Numeric median
imputation and scaling fit training only. Numeric/text/concatenated sparse-feature
logistic regression: balanced training class weights, seed 42, max_iter 1000.
Select strict-score F1 threshold using validation only, ties choose higher.
Freeze all thresholds before reading test labels for metrics/error analysis.
No post-test model selection. Scores are uncalibrated decision evidence.
Report confusion, precision/recall/F1/AP, prevalence, false alerts per 1,000
windows, cohort and group overlap, replay. Missing classes yield honest undefined
metrics or unavailable training; no fabricated positives or held-out resampling.

Sensitivity classification requires independently annotated documents with
policy-defined sensitivity labels; CERT malicious observables are ineligible.
PII spans, model/rule labels and synthetic fixtures cannot validate sensitivity.
All outputs are offline research only, no activation or policy changes.
