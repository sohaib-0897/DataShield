# DataShield implementation memory

## Resume protocol and goal
- Read applicable AGENTS.md and this file first; inspect Git status, branch, remote, and current code.
- Execute exactly one phase per request; finish an unfinished phase before advancing.
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

## Verified checkout and reconciliation (2026-10-07)
- Actual checkout: /home/sohaib/Insider_Threat_Test_Dataset/DataShield~ (literal trailing tilde).
- Parent workspace .git is only an empty read-only placeholder; run Git inside actual checkout.
- User-provided checkout was clean on main at 74efcfd420d9e4442397d1c1276db67853a590f1.
- Local origin/main has that same SHA; remote freshness remains unverified because DNS is unavailable.
- Origin: https://github.com/sohaib-0897/DataShield.git; verified matches requested repository.
- Dedicated branch: feat/cert-ml-nlp, created from existing checkout; no reset or merge performed.
- User confirms manual push succeeded; branch now tracks origin/feat/cert-ml-nlp.
- At resume, HEAD and cached remote branch both equaled db47089b00b4613ea981f44182081d3ec0a5196e.
- Fresh remote SHA query still fails: Could not resolve host: github.com; no live verification claimed.
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
- Local path configuration: .local/cert_paths.json (ignored); no ingestion CLI consumes it yet.
- Planned research DB: research/local/cert_r42.sqlite; research/local/ is ignored.
- Forbidden research destination: downloaded original data/activity.db or any production DB.
- Preserved Flask's legacy/downloaded_flask/data/ is separate and ignored; no live DB copied there.
- Upstream production store remains PostgreSQL; migrations must not run against live data for this work.
- Archive extraction, README/header inspection, ingestion, labeling, authentic training/evaluation: not run.
- About 424 GiB free in workspace filesystem; /tmp is a 7.7 GiB tmpfs.

## Verified supplied Flask architecture
- legacy/downloaded_flask/database.py: SQLite activity/transfers, naive receipt timestamps, getpass identity.
- agent.py: watchdog events; DB/observer/busy loop start at import, so never import during research.
- windows_monitor.py: Security 4663/4660, app filtering, deduplication, handle deletion correlation.
- usb_monitor.py: WMI device polling; copy monitors: USB/local/Google Drive watched-folder hash matching.
- upload_server.py: localhost upload test gateway; sensitivity.py: filename policies and SHA-256.
- behavioral_monitor.py: Win32 foreground app/idle samples in behavior_events, five-second interval.
- baseline.py: historical printed summaries; behavior.py: recent optional-user summaries, fixed work hours.
- feature_builder.py: global hourly activity/transfers, mixes users; both-empty early return in code.
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
| 0 | Audit, source preservation, isolated baseline, plan/checkpoint | remaining dependency/regression checks | blocked |
| 1 | Actual release inspection and safe resumable ingestion | completed 0 | pending |
| 2 | Exact-event labels and shared per-user features | 1 | pending |
| 3 | Reproducible behavioral ML and held-out evaluation | 2 | pending |
| 4 | CERT text study and document extraction/evidence | 2 + numeric benchmark 3 | pending |
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
- Record exact ingestion CLI when implemented; existing expected-format loader is not r4.2 validation.
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
- Research schema/label granularity/timezone mapping remain deferred until actual release inspection.
- Answer-derived identifiers/scenarios never enter inference; unavailable signals are not genuine zero counts.
- Separate research/live artifacts if feature coverage differs; chronological disjoint evaluation windows.
- IsolationForest scores are not probabilities; anomaly training population assumption must be documented.
- Fusion/model thresholds remain unvalidated; no detection improvement or sensitivity-model accuracy claim.
- Detailed audit: docs/implementation/phase0/audit.md; historical supplied-code audit: phase0_audit.md alongside it.
- Copy manifest: docs/implementation/phase0/source_reconciliation.json; original hashes: phase0_preservation*.json.
- Supplied baseline: 22 attempted, 18 passed, 4 pandas checks skipped; zero failures/errors.
- Prior passing checks were not repeated; four pending feature checks retried separately: 0 passed, 4 skipped, exit 2.
- New evidence: docs/implementation/phase0/remaining_feature_checks.json and dependency_readiness.json.
- Final integrity: 110 upstream files checked; only .gitignore changed; 19 source copy hashes match.
- Staged review retains one original whitespace-only line in imported risk_engine.py; other new files pass whitespace checks.
- Original 30 source/live hashes and three archive-stat records remain unchanged; final_preservation_check.json records checks.
- Preserved copy baseline: same 18 passed/4 skipped; real Flask loaded from existing pure-Python venv packages.
- Upstream existing CSV loader: 2 passed; full pytest stops at 7 missing-dependency collection errors.
- Native dependencies still missing; explicit PyPI install retry failed to resolve pandas (exit 1).
- Native isolated venv: 0/17 required module imports available; GitHub/PyPI/npm DNS all fail.
- Node/npm unavailable; frontend tests/build not rerun. Prior upstream claims are historical, not current evidence.
- Native Windows monitors, physical devices and PostgreSQL integration were not verified in this environment.
- No monitors/servers started; no live content logged; baseline/current source hashes are verified separately.
- Pre-existing Flask findings: global feature users mix, watchdog summaries omit changes, permitted after-hours hidden.
- New model artifacts, CERT research data, authentic evaluation results: none.

## Current phase, checkpoint, and exact next action
- Current phase: 0 blocked on native dependencies/tooling; Phase 1 remains pending.
- Previous phase WIP checkpoint: db47089b00b4613ea981f44182081d3ec0a5196e (manual push confirmed by user).
- Base upstream SHA: 74efcfd420d9e4442397d1c1276db67853a590f1.
- Intended current commit: chore: WIP phase 0 dependency checks and manual push status.
- Git author identity inferred from existing base commit and configured only in this repository.
- Resolve this checkpoint SHA using git log -1; avoid editing this file just to record its own commit SHA.
- Previous push blocker resolved manually; session GitHub DNS restriction still limits fetch/new pushes.
- Exact next action: install dependencies/tooling from a working terminal, then run outstanding checks per audit.md.
- Harness --test selects unfinished checks; --require-no-skips returns exit 2 for skips, preserving default behavior.
- Current checkpoint push preflight failed (DNS); new checkpoint publication remains pending.
- Recovery: install requirements-dev.txt plus pandas in a native Linux venv; install frontend Node/npm dependencies.
- Run unfinished full upstream/frontend checks and four feature cases; do not erase historical baseline failures/skips.
- With working GitHub DNS/network: git fetch origin; inspect divergence; git push -u origin feat/cert-ml-nlp.
- Verify git ls-remote origin refs/heads/feat/cert-ml-nlp equals local checkpoint; never force-push.
- Do not advance to Phase 1 until Phase 0 checks and pending checkpoint push/verification are resolved.
