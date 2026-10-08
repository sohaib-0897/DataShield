# DataShield implementation memory

## Resume protocol and goal
- Read applicable AGENTS.md and this file first; inspect Git status, branch, remote, and current code.
- Original Phases 0–6/NLP follow-up and DS1/DS2 complete; stop after DS2; DS3 requires a new request.
- Verify the previous checkpoint and pending push before starting another phase.
- Goal: preserve completed CERT workflow; establish defensible content labels, evaluation and advisory integration.
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
- User-provided checkout was clean on main at 74efcfd420d9e4442397d1c1276db67853a590f1.
- Origin: https://github.com/sohaib-0897/DataShield.git; verified matches requested repository.
- Dedicated branch: feat/cert-ml-nlp, created from existing checkout; no reset or merge performed.
- User confirms manual push succeeded; branch now tracks origin/feat/cert-ml-nlp.
- Phase 0 handoff published 2026-10-08; fresh GitHub branch SHA equals HEAD: 3548f75cb805f3645f65a1ab55f38773e8b0fc5b.
- No AGENTS.md found in actual checkout, parent workspace, ancestors, or downloaded source.
- Downloaded original: /home/sohaib/Downloads/AI-DLP-Agent (user-confirmed implementation to preserve).
- Preserved copy: legacy/downloaded_flask/; 19 top-level .py/.html files, no live/config/document files.
- Original 19 files copied byte-for-byte; existing .gitattributes normalizes committed text to LF.
- Provenance/raw+normalized hashes: docs/implementation/phase0/source_reconciliation.json.
- No upstream application files replaced; only additive source/tests/docs and ignore protections.

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
| 5 | Advisory adapters, status/explanations, deterministic replay | 3 + 4 | completed (bounded) |
| 6 | Full run, fair comparisons, error analysis, handover | 1–5 | completed (bounded; full memory-limited) |
| DS1 | Sensitivity taxonomy, dataset/license research, annotation plan | NLP follow-up | complete; acquisition blocked |
| DS2 | Acquisition, grouped splits, CPU supplied-span baseline/evaluation | DS1 + suitable labels | complete; offline TAB task only |
| DS3 | Further evaluation/optional shadow integration | DS2 + explicit request | pending; separate session |

## Completed acceptance history
- Original Phases 0–6 and NLP follow-up are complete at bounded acceptance.
- Detailed contracts, exact commands and historical results: docs/implementation/phase0–6/ and nlp-followup/.
- Preserve source/live/archive checks, frozen features/models and strict-cohort results; do not rerun CERT work.
- DS1 source/license/taxonomy/annotation evidence: docs/implementation/document-sensitivity/report.md.

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
- npm findings: 106 groups (3 low/36 moderate/65 high/2 critical), cached then freshly confirmed in Phase 6.
- Production-declared: 2 moderate React Router groups; dev graph: 104, including critical proxy-addr/shell-quote.
- Dev tooling also runs under current Docker npm start; no package/lockfile upgrades or audit fix applied.
- npm review: phase0/npm_audit_review.md (historical cache), phase6/npm-review.md/json (fresh registry audit).
- Current GitHub publication/npm registry access works; historical DNS failures remain documented.
- Native Windows monitors, physical devices and PostgreSQL integration were not verified in this environment.
- No monitors/servers started; no live content logged; baseline/current source hashes are verified separately.
- Pre-existing Flask findings: global feature users mix, watchdog summaries omit changes, permitted after-hours hidden.
- Bounded data/artifacts ignored; Phase 2 label/features evidence: docs/implementation/phase2/.

## Current checkpoint and NLP follow-up
- Original Phases 0–6 passed bounded acceptance; no Phase 7 was added.
- Historical exact SHAs/phase results: docs/implementation/publication.json and phase0–6 reports.
- Phase 6: 978,908 events, 95,930 fully observed windows, positives 14/19/8 across 58,258/25,919/11,753.
- Numeric precision was poor; strict text 54,763/0/0; no activation or sensitivity corpus claim.
- Follow-up authorized 2026-10-08, starting clean/fresh remote SHA 216a0eb2a49161ab2f185af7dec53e035c278a35.
- All 3,291 January and 96,063 June windows/text match frozen original artifacts exactly.
- Streaming June preparation: 425 MiB peak RSS, 122.668s resumed + 6.480s initial checkpoint.
- Full parity verification: 928 MiB / 56.333s; idempotent replay 4.219s / zero new rows/users.
- Transactions commit complete users; partial users roll back; read-only originals and hash/provenance guards.
- Root cause strict empty cohorts: every later eligible user already seen; not a label/text mapping defect.
- Original strict results retained; separately declared known-user/content-disjoint chronological experiment.
- Alternative sizes 54,763/23,616/10,553, positives 14/19/8; no identifiers/answers/future evidence as features.
- Numeric/text/combined test precision .002198/.50/.074074; recall .125/.125/.25; F1 .004320/.20/.114286.
- AP .007826/.154422/.167069; false alerts/1,000 windows 43.020942/.094760/2.368995.
- Same 10,553 test windows / 8 positives; train-only transforms, validation thresholds, refit/hash replay equal.
- Training/reproduction 499.263s / 8.52 GiB peak RSS; full-release fitting still resource-limited.
- Separate sensitivity interface runnable; only synthetic tests; independent supervision remains unavailable.
- Shadow defaults disabled; six actual scores match, rule fallback/provenance/schema tests pass; no activation.
- Final isolated regressions 151 passes + 22 preserved Flask passes; no skips, one existing warning.
- Originals/live/copies/archives/application trees and frozen January/June research artifacts preserved.
- Detailed commands/results: docs/implementation/nlp-followup/report.md, streaming.md, sensitivity.md and JSON evidence.
- Streaming milestone verified: 3500e23d1a57e224280a83af837a8e4faf2c937f; evaluation verified: 521331df8f651aa1c3797d488a913964f3581c55.
- Both normal pushes/fresh remote SHA equalities succeeded; documentation closure follows; final HEAD via Git.
- DS1 complete; started clean at local/fresh remote b881673ea91e5a31bc7036caebe8f62236079a06; no CERT rerun.
- DS1 taxonomy, seven-source/license registry, blank human-review CLI and bounded TAB inventory implemented.
- DS1 evidence/commands/recovery: docs/implementation/document-sensitivity/report.md and adjacent JSON/guide/plan.
- TAB selected only for supplied-span semantic categories; metadata verified; corpus downloads incomplete/timed out.
- No organizational corpus/labels, real sensitivity training/evaluation or activation; raw/partial storage ignored.
- DS1 checks: 175 isolated + 22 Flask passes; 42 targeted; 388.340 MiB peak / 22.78s full check; originals preserved.
- DS2 acceptance: source/version/chunk/near-duplicate grouped splits, train-only transforms, validation thresholds.
- DS3 acceptance: untouched natural test cohort, per-class P/R/F1/AP/confusion, rule comparison/error analysis.
- Organizational labels require policy/context and human review; categories alone cannot assign NORMAL/HIGH/CRITICAL.
- DS2 complete: 2026-10-08; clean start local/fresh remote 67f6c02149558ec1205dd0e3eabd4ef8a5ea9a5d.
- No AGENTS.md found; all runtime/live/rule decisions and 13 frozen artifacts preserved; no model activation.
- Pinned TAB acquired and checksum/schema/license verified: 1,268 documents, 155,006 raw annotation records.
- Task ONLY supplied-span entity-category classification; original annotations retained; eight identity-mapped TAB classes.
- Reviewed unanimous spans; group controls quarantine 7 train/3 dev documents; 686 unreviewed documents excluded.
- Frozen train/validation/test: 22,939/6,810/6,713 spans, 326/124/127 documents, 325/124/125 families.
- Family overlap zero; repeated vocabulary remains (disclosed); exhaustive five-word Jaccard >=.8 and subject controls.
- CPU TF-IDF/LinearSVC train-only fits; validation selects entity-only (.8190 macro F1) over context (.7509).
- Final test entity macro/micro F1 .7763/.8856; context .7379/.8781; majority .0681/.3746.
- Two independent fits have identical artifact hashes/reload scores; raw margins are not probabilities.
- Final preparation 26.92s/455.863 MiB; training 81.67s/908.094 MiB; evaluation 21.62s/349.953 MiB.
- Organizational sensitivity BLOCKED: zero independent labels; exact packet/next owner-review action in ds2-human-annotation-packet.json.
- All raw corpus/manifests/models remain in ignored research/local/document_sensitivity/; final folders use v2.
- Actual commands, per-class results, resources and limitations: docs/implementation/document-sensitivity/ds2-report.md.
- Verification/publication evidence: adjacent ds2-verification.json; final SHA via Git; normal push/fresh remote equality required.
- Stop after DS2. Exact next human action: owner-approved policy/context and authorized 100-document blind-review pilot.
