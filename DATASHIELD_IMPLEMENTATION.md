# DataShield implementation memory

## Resume protocol and goal
- Read applicable AGENTS.md and this file first; inspect Git status, branch, remote, and current code.
- Current authorization: execute Phases 2–4 sequentially; finish acceptance before advancing.
- Verify the previous checkpoint and pending push before starting another phase.
- Goal: safe CERT r4.2 ingestion, ground truth/features, behavioral ML, NLP, evaluation, advisory integration.
- Keep this file strictly below 200 lines; detailed evidence lives in docs/implementation/phase0/.
- Preserve both supplied Flask/SQLite application and existing upstream FastAPI/PostgreSQL/React runtime.
- No framework/database migration is authorized or needed; use additive shared modules/adapters.
- Retain monitor behavior/logging, API fields/routes, policies/roles/decisions, and rule fallback.
- New model decisions default to advisory/shadow; no new automatic blocking.
- Never start monitors during ingestion/training/tests; never touch physical devices in automated tests.
- Never reset live data, overwrite policies, discard user work, force-push, or merge into main automatically.
- Never commit source data, live DBs, sensitive documents, credentials, environments, or large models.

## Verified checkout and reconciliation (2026-10-08)
- Actual checkout: /home/sohaib/Insider_Threat_Test_Dataset/DataShield~ (literal trailing tilde).
- Parent workspace .git is only an empty read-only placeholder; run Git inside actual checkout.
- User-provided checkout was clean on main at 74efcfd420d9e4442397d1c1276db67853a590f1.
- Local origin/main has that same SHA; remote freshness remains unverified because DNS is unavailable.
- Origin: https://github.com/sohaib-0897/DataShield.git; verified matches requested repository.
- Dedicated branch: feat/cert-ml-nlp, created from existing checkout; no reset or merge performed.
- User confirms manual push succeeded; branch now tracks origin/feat/cert-ml-nlp.
- At resume, HEAD/cached remote matched ea65336f41c233114b8a5e8761811db7695bc922; user confirms its push.
- Phase 0 handoff published 2026-10-08; fresh GitHub branch SHA equals HEAD: 3548f75cb805f3645f65a1ab55f38773e8b0fc5b.
- No AGENTS.md found in actual checkout, parent workspace, ancestors, or downloaded source.
- Downloaded original: /home/sohaib/Downloads/AI-DLP-Agent (user-confirmed implementation to preserve).
- Preserved copy: legacy/downloaded_flask/; 19 top-level .py/.html files, no live/config/document files.
- Original 19 files copied byte-for-byte; existing .gitattributes normalizes committed text to LF.
- Provenance/raw+normalized hashes: docs/implementation/phase0/source_reconciliation.json.
- No upstream application files replaced; only additive source/tests/docs and ignore protections.
- Source versions have different schema/API/event/scoring contracts; do not substitute one for the other.
- FYP reference documentation exists under docs/fyp/; no standalone supplied FYP report found.

## Dataset and storage separation
- Requested proj/dataset and workspace dataset subfolder do not exist; do not create duplicate archives.
- Actual r4.2: /home/sohaib/Downloads/r4.2.tar.bz2 (4,824,287,500 bytes).
- Actual answers: /home/sohaib/Downloads/answers.tar.bz2 (1,254,678 bytes).
- Actual README: /home/sohaib/Downloads/SEI_Insider_README.txt (1,446 bytes).
- Local path configuration: .local/cert_paths.json (ignored); consumed by research/cert_ingest.py.
- Research DB: research/local/cert_r42.sqlite; bounded 10,000 events; research/local/ is ignored.
- Forbidden research destination: downloaded original data/activity.db or any production DB.
- Preserved Flask's legacy/downloaded_flask/data/ is separate and ignored; no live DB copied there.
- Upstream production store remains PostgreSQL; migrations must not run against live data for this work.
- Phase 1 ingestion and Phase 2 bounded labels/features complete; models remain isolated research only.
- About 424 GiB free in workspace filesystem; /tmp is a 7.7 GiB tmpfs.

## Verified supplied Flask architecture
- legacy/downloaded_flask/database.py: SQLite activity/transfers, naive receipt timestamps, getpass identity.
- agent.py: watchdog events; DB/observer/busy loop start at import, so never import during research.
- windows_monitor.py: Security 4663/4660, app filtering, deduplication, handle deletion correlation.
- usb_monitor.py: WMI device polling; copy monitors: USB/local/Google Drive watched-folder hash matching.
- upload_server.py: localhost upload test gateway; sensitivity.py: filename policies and SHA-256.
- behavioral_monitor.py: Win32 foreground app/idle samples in behavior_events, five-second interval.
- baseline.py: historical printed summaries; behavior.py: recent optional-user summaries, fixed work hours.
- feature_builder.py: global hourly mixes users; both-empty/activity-only/transfer-only checks pass.
- prepare_training.py filters/exports CSV only; risk_engine.py is capped rules with 25/50/75 levels.
- dashboard.py/dashboard.html: JSON policies, roles, alert_state, analyst decisions, monitor controls.
- Dashboard score uses alert decay/weights/saturation and differs from legacy risk_engine score.
- Original live columns inspected read-only; 5 activity, 2 transfers, 241 behavior, 1 alert-state rows.
- Windows identity parsed from Security events is not passed to log_activity's getpass-based logger.

## Verified upstream architecture and existing components
- backend/app/main.py: FastAPI /api/v1 ingestion, alerts/evidence/decisions, reports, users, policy, models.
- backend/app/core.py/models.py: SQLAlchemy/PostgreSQL sessions, JWT/Argon2/RBAC, normalized persistence.
- backend/migrations/: existing Alembic head 9e20ab47c132; legacy SQLAlchemy tables remain supported.
- frontend/src/: React analyst workflows; agents/: filesystem, USB, upload and network collectors.
- backend/app/analysis.py: numeric features event-window-v2, heuristic behavior, weighted-v1 scoring.
- Upstream live features filter user in ingestion, but rolling per-event windows overlap.
- ml/data/loader.py: three expected CSV mappings, UTC assumption; http visits mapped to CLOUD.
- ml/data/prepare_dataset.py: JSONL preparation; lacks safe extraction/resume/full diagnostics.
- ml/training/train_anomaly.py: optional IsolationForest candidate, chronological 80/20 split, no labels/evaluation.
- Training hourly features duplicate live rolling-window logic; availability and partition purging are absent.
- ml/registry/: artifact compatibility/provenance guards; no bundled or active trained model found.
- backend/app/sensitivity.py: rule/declared text classification and optional model interface; no file extraction.
- Runtime artifact loaders load per assessment; model caching/advisory integration remains future work.
- Upstream config defaults and model guards remain intact; no new weights/models activated.
- legacy/flask/ is a different SQLAlchemy Flask app, not the supplied SQLite dashboard; keep both.

## Phase table
| Phase | Scope | Depends on | Status |
|---|---|---|---|
| 0 | Audit, source preservation, isolated baseline, plan/checkpoint | published and freshly verified | completed |
| 1 | Actual release inspection and safe resumable ingestion | completed 0 | completed |
| 2 | Exact-event labels and shared per-user features | 1 | completed (bounded) |
| 3 | Reproducible behavioral ML and held-out evaluation | 2 | completed (bounded) |
| 4 | CERT text study and document extraction/evidence | 2 + numeric benchmark 3 | completed (bounded; comparison unavailable) |
| 5 | Advisory adapters, status/explanations, deterministic replay | 3 + 4 | pending |
| 6 | Full run, fair comparisons, error analysis, handover | 1–5 | pending |

## Phase acceptance and verification
### 0 — audit and baseline
- Audit actual checkout plus supplied implementation; compare before transferring source; preserve both.
- Acceptance: isolated regression baseline, preserved originals/upstream behavior, accurate plan, commit/push.
- Commands: python -B -m pytest -q; python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --require-no-skips.
- Commands: python -B scripts/verification/phase0_preservation.py --help; git diff --check; wc -l DATASHIELD_IMPLEMENTATION.md.
- Also npm ci/test/build in frontend with native tooling; see docs/implementation/phase0/audit.md.
### 1 — dataset inspection and safe ingestion
- Read actual README, release docs, archive members and headers before mapping semantics.
- Implement traversal/link rejection, disk checks, chunking, resumable progress, deduplication/diagnostics.
- Preserve source IDs/users/times/actions/channels/resources/metadata in separate research storage.
- Acceptance: bounded subset, idempotent rerun/resume, source hashes, counts/errors, documented mappings.
- Checks: unsafe archives, interrupted rerun, empty/malformed rows, disk limits, count reconciliation + regressions.
- CLI: python3 -B research/cert_ingest.py --config .local/cert_paths.json inspect --rows 2000; ingest commands in docs/implementation/phase1/ingestion.md.
### 2 — ground truth and shared features
- Inspect answers' actual granularity; exact matching, unmatched/ambiguous audits, separate scenario metadata.
- Build versioned per-user windows, past-only baselines, configurable work hours and explicit availability.
- Acceptance: traceable labels, isolated users, no future leakage, documented research/live contracts.
- Checks: answer joins, two-user fixtures, empty/missing signals, cold starts, future invariance + regressions.
- Record exact label/feature commands when implemented; do not label a malicious user's entire history.
### 3 — behavioral ML and evaluation
- Reproducible CPU IsolationForest and simple supervised baseline if positives support it.
- Chronological train/validation/test; purge overlapping windows; training/past-only fitting.
- Validation-only thresholds/tuning; natural held-out prevalence; audit zero-positive partitions honestly.
- Acceptance: actual runs, reproducible versioned artifacts, leakage checks, measured subset/full coverage.
- Checks: split audit, deterministic replay/training, artifact hashes, preprocessing fit boundaries + regressions.
- Report precision/recall/F1/PR-AUC/confusion, false alerts per user-day, volume, latency and supported scenarios/timing.
### 4 — NLP and documents
- CERT text detection and independently labeled document sensitivity are separate tasks.
- TF-IDF+linear comparison only with usable supervision; prevent duplicate-text/identity/scenario leakage.
- Bounded TXT/PDF/DOCX extraction, unsupported/encrypted/scanned/malformed/empty handling, PII evidence.
- Acceptance: extraction/evidence tests, preserved hash/filename signals, honest supervision/model claims.
- Checks: extraction/evidence fixtures, duplicate/leakage audit, numeric vs text comparison + regressions.
- Synthetic documents are test/demo only; no raw sensitive-content logging or invented validated corpus.
### 5 — advisory integration
- Shared inference contract with compatible adapters for preserved Flask and existing upstream application.
- Cache compatible artifacts; flags/shadow default; additive persistence; rule fallback on missing/failing models.
- Expose separate rule/anomaly/content/combined signals, versions and evidence; avoid double counting.
- Acceptance: enabled/disabled/failure regressions, preserved API/workflows/policies, isolated deterministic replay.
- Checks: adapter contracts, schema compatibility, fallback and replay timestamps; no new automatic blocking.
### 6 — full run and handover
- Smoke then full run if resources permit; keep smoke/full results separate; fair common-population comparisons.
- Acceptance: measured results, error analysis, exact pipeline/startup commands, limitations, handover/checkpoints.
- Checks: full pipeline where feasible, rule/ML/combined population audit, integration/regressions.
- Distinguish CERT synthetic-benchmark results from real endpoint/hardware validation.

## Decisions, evidence, and current limitations
- Research schema v1; timezone unspecified; exact all-source-field label joins, separate incident actors.
- Answer-derived identifiers/scenarios never enter inference; unavailable signals are not genuine zero counts.
- Separate research/live artifacts if feature coverage differs; chronological disjoint evaluation windows.
- IsolationForest scores are not probabilities; anomaly training population assumption must be documented.
- Fusion/model thresholds remain unvalidated; no detection improvement or sensitivity-model accuracy claim.
- Detailed audit: docs/implementation/phase0/audit.md; historical supplied-code audit: phase0_audit.md alongside it.
- Copy manifest: docs/implementation/phase0/source_reconciliation.json; original hashes: phase0_preservation*.json.
- Historical baseline: 18 Flask passes/4 skips; later failed dependency attempts preserved in original JSONs.
- Completed feature report: 4 passed, no skips/errors; 22 distinct Flask checks passed across recorded runs.
- Completed upstream isolated baseline: exit 0, 34 passed, 1 Starlette/httpx deprecation warning, no collection errors.
- Reports: docs/implementation/phase0/upstream_baseline_completed.json and remaining_feature_checks_completed.json.
- Frontend terminal results: npm ci exit 0, 7 tests passed, production build compiled; npm logs corroborate exit 0.
- Closure/preservation evidence: docs/implementation/phase0/closure_verification.json; earlier reports remain untouched.
- Upstream source/lock unchanged; only intentional .gitignore/docs changes; 19 preserved source hashes match.
- Staged review retains one original whitespace-only line in imported risk_engine.py; other new files pass whitespace checks.
- Original 30 source/live hashes and three archive-stat records remain unchanged; final_preservation_check.json records checks.
- Native deps now installed: .local/phase0-venv (Python 3.14.4); Node 22.22.1/npm 9.2.0 available.
- npm findings: 106 package groups (3 low/36 moderate/65 high/2 critical), reproduced from install cache.
- Production-declared: 2 moderate React Router groups; dev graph: 104, including critical proxy-addr/shell-quote.
- Dev tooling also runs under current Docker npm start; no package/lockfile upgrades or audit fix applied.
- Review: docs/implementation/phase0/npm_audit_review.md and npm_audit_review.json (cached, not fresh registry audit).
- GitHub works with elevated access; sandbox DNS remains restricted; installed baseline checks are complete.
- Native Windows monitors, physical devices and PostgreSQL integration were not verified in this environment.
- No monitors/servers started; no live content logged; baseline/current source hashes are verified separately.
- Pre-existing Flask findings: global feature users mix, watchdog summaries omit changes, permitted after-hours hidden.
- Bounded data/artifacts ignored; Phase 2 label/features evidence: docs/implementation/phase2/.

## Current phase, checkpoint, and exact next action
- User authorized Phases 2–4 sequentially without routine confirmation; implementation/acceptance now finished.
- Phase 0 verified handoff: 3548f75cb805f3645f65a1ab55f38773e8b0fc5b; baseline results preserved above.
- Phase 1 verified implementation: 07a39cadc924357b2b93e984e2bfd23e73ebf991; final start HEAD 4c5a52ed.
- Phase 1: 10,000 events/zero errors, interrupted resume/idempotency; 28 safety tests; no full ingestion claim.
- Phase 2 pushed/freshly verified: f958802f6f22b5a0fe46f3ee725c15177cf2e51f.
- Phase 2: exact labels, 10,000 negatives, 7,323 unmatched observables, zero ambiguous; 50 impersonated subjects.
- Phase 2: 3,291 active user-hours/164 fully observed; past-only users, availability, configurable work hours.
- Phase 2: 43 targeted + 62 isolated tracked passes; deterministic feature replay; docs/implementation/phase2/.
- Phase 3 pushed/freshly verified: 63595ab35986bdc495ed916f24735312f559752a.
- Phase 3: 83/43/38 chronological train/val/test windows, zero positives; seed 42/200 trees/one CPU worker.
- Phase 3: train-only preprocessing, validation-only threshold; deterministic scores/serialized artifact hashes.
- Test TN36/FP2/FN0/TP0; precision 0; recall/F1/PR-AUC null; false alerts/evaluated user-day 0.05263.
- Phase 3: 51 targeted/85 isolated full passes; supervised unavailable; docs/implementation/phase3/.
- Phase 4: 6,000 texts/111 duplicate bags; filtered train/val/test 81/1/0; supervised comparison unavailable.
- Phase 4: bounded TXT/PDF/DOCX, explicit unavailable outcomes, redacted PII + independent filename/hash evidence.
- Phase 4: ten synthetic actual parser checks; 75 targeted/109 isolated full passes, no skips, one prior warning.
- Phase 4: text/feature replay passed; no sensitivity corpus/model claim; docs/implementation/phase4/.
- Final preservation: 30 original/live hashes, 19 copied normalized hashes, three input stats unchanged.
- Original application trees unchanged; research data/models ignored; no model activation or policy changes.
- Phase 4 pushed/freshly verified: dcf66aab4619f13598aa8558df80842db0920fca.
- Publication checkpoints/final resume instructions: CONTEXT.md and docs/implementation/publication.json.
- Phase 5/6 remain pending/outside this request; Windows/PostgreSQL and npm findings remain unverified/open.
- Exact next step: begin Phase 5 explicit advisory adapter contracts on a new request, keeping shadow/rule fallback.
- For detection-quality comparisons, first prepare a broader chronological CERT cohort with positive examples.
- Independent document-sensitivity supervision is also required before a trained sensitivity accuracy claim.
