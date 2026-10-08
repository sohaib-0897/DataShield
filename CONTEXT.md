# Document sensitivity DS3 completed — 2026-10-08

DS3 only: clean start at verified local/remote DS2 checkpoint
9933e063c0783a66694474b755bdf6b76fa00a1d; no applicable AGENTS.md found.
Frozen predictions/manifests audited without acquisition or training. All 1,268
documents accounted for: 577 used, 681 nonquarantined unreviewed, ten quarantined
(five reviewed/five unreviewed). Frozen populations remain 326/124/127.
Selected test macro/micro F1 .776293/.885595; 2,000 document-bootstrap 95% intervals
.735357–.815250/.859797–.910754. Seen/unseen micro F1 .976505/.807266;
results remain legal-domain supplied-span categories, not entity detection or
whole-document confidentiality. No tuning against test diagnostics.

Added an optional analyst-authenticated FastAPI supplied-span endpoint, disabled
by default. Callers supply text and Unicode code-point offsets; bounded requests,
operator-pinned local compatible artifact, once-per-process cache, explicit failures,
category/version/uncalibrated margins only. No sensitivity/risk/decision coupling,
external text transfer, text logging or persistence. Actual frozen-model interface
replays all 6,713 predictions exactly. Checks: 221 isolated, 22 Flask, 88 final
targeted passes; all 13 frozen artifacts, DS2 files and original/live preservation
match. Fixed the observed DS2 pypdf CI failure by including research dependencies
in development requirements; extraction tests remain enabled. Source checkpoint
9130a96e2909ff5f09ba9ff9fec0160b9316e4a6 pushed normally and freshly matched the
remote. GitHub CI run 37767822921 passed: 221 Python tests, seven frontend tests
and production build. Final documentation SHA/latest CI are reported in the final handoff.

Stop after DS3. Organizational sensitivity remains blocked on independent labels
and owner-approved policy/context. Exact next human action: authorized de-identified
100-document pilot, versioned policy/context and two blind reviewers plus adjudicator.
Detailed evidence/configuration/commands: docs/implementation/document-sensitivity/ds3-report.md.

Historical handoffs below are retained; their old pending statuses are superseded.

---

# Document sensitivity DS2 completed — 2026-10-08

DS2 executed only, starting clean on feat/cert-ml-nlp at local/fresh remote
67f6c02149558ec1205dd0e3eabd4ef8a5ea9a5d. No AGENTS.md found. The user explicitly
included final evaluation in DS2; historical DS1 wording assigning evaluation to
DS3 is superseded for this request. Stop here; no runtime/shadow integration.

- Official pinned TAB acquisition succeeded; six source files have matching sizes,
  Git blob IDs and local SHA-256. 1,268 documents / 155,006 raw annotation records.
- Supported task: supplied-span entity-category classification only (eight TAB classes).
  Original annotations retained; reviewed exact-span unanimity, abstentions for conflicts.
- Family/subject/normalized/near-duplicate controls quarantine 7 train and 3 dev cases.
  Frozen train/validation/test: 22,939/6,810/6,713 spans; 326/124/127 documents.
- Train-only TF-IDF + CPU LinearSVC. Validation selected entity text; both candidate
  models frozen before final test. Test macro/micro F1 .7763/.8856; majority .0681/.3746.
- Repeated vocabulary remains; unseen entity text is weaker. Legal-domain results
  do not establish entity detection, whole-document sensitivity or policy levels.
- Independent fits reproduce hashes; reload scores match; scores are uncalibrated margins.
- New artifacts offline and ignored under research/local/document_sensitivity/ (v2 folders).
  All 13 frozen artifacts, original/live files, archive stats and application trees preserved.
- Independently reviewed organizational labels absent. Exact owner policy/context,
  provenance and blind-review pilot packet: ds2-human-annotation-packet.json in report directory.
- Detailed evidence, checks, resources, commands and next action:
  docs/implementation/document-sensitivity/ds2-report.md and adjacent ds2-*.json.
- Final publication: normal push to the existing branch; fresh remote must equal local
  HEAD. Resolve SHA with git rev-parse HEAD; final handoff reports actual push outcome.
- Exact next human action: owner supplies authorized de-identified 100-document pilot
  and approved versioned policy/context; two independent reviewers, third for conflicts.

Historical handoffs below are retained; their old pending statuses are superseded.

---

# Document sensitivity DS1 complete — 2026-10-08

This session executed DS1 only. “Start next phase” means DS2 only: verify the
current Git checkpoint/push, retry pinned TAB acquisition, validate hashes/schema,
reconcile annotations and audit case/subject/source/version/duplicate groups,
freeze splits, then train a CPU baseline only if supported labels are defensible.
Do not repeat CERT ingestion/training, replace the original strict-cohort result,
or combine the known-user experiment with document-sensitivity evidence.

- Started clean `feat/cert-ml-nlp`, local/fresh remote both
  `b881673ea91e5a31bc7036caebe8f62236079a06`; no AGENTS.md found.
- Separate content categories PERSONAL_INFORMATION / FINANCIAL_INFORMATION /
  CREDENTIALS / BUSINESS_CONFIDENTIAL from context-dependent NORMAL/HIGH/CRITICAL.
  Public PII or financial text alone cannot assign a policy level; unknown stays null.
- Seven primary-source dataset/license reviews. TAB selected narrowly for provided
  entity-span semantic categories, never whole-document organizational sensitivity.
  Natural human-reviewed machine-assisted annotations; disagreements remain relevant.
- MIT release pinned at `558e09e26d6b36f5f78440074e6a233946d98bd9`.
  Three metadata files match official Git blobs; actual corpus acquisition blocked
  by raw-download and archive timeouts. Four partial files are untrusted; no
  acquisition manifest or actual corpus counts. Storage: ignored private
  `research/local/document_sensitivity/`; download recovery in DS1 report.
- Blank private annotation CLI and context/two-reviewer/adjudication validation
  implemented; existing bounded extractors reused. Standalone fixture CLI assigns
  no labels. Human work still needed: owner-approved policy/examples, 100-document
  pilot, proposed 1,200-document corpus with two independent reviews plus resolution.
- No real sensitivity fitting/evaluation, no organizational labels produced and
  no active artifact/policy/runtime changes. CERT/historical artifacts preserved.
- Verification: 175 isolated pytest + 22 Flask passes; 42 targeted tests.
  Full check 22.78s / 388.340 MiB peak RSS, existing Starlette warning only.
  All 30 source/live hash/stat entries and three archive/readme stats unchanged.
  All 13 frozen artifact checks match; read-only canonical feature verification
  command 6.22s / 783.039 MiB, the largest observed DS1 command peak.
- Detailed status, commands, blockers, artifact paths and exact next actions:
  `docs/implementation/document-sensitivity/report.md`; taxonomy/guide,
  dataset-research.md, later-phases.md and aggregate JSON evidence alongside it.
- Final checkpoint is current Git HEAD on feat/cert-ml-nlp; publication is a
  normal push and fresh `ls-remote` equality, reported at phase handoff.
  DS3 evaluation/error analysis/optional shadow remains a separate later phase.

# Historical completed NLP follow-up — 2026-10-08

User-authorized autonomous NLP follow-up is complete at bounded evaluation.
Start was clean `feat/cert-ml-nlp`, local/fresh remote matched
216a0eb2a49161ab2f185af7dec53e035c278a35. No AGENTS.md found.

- Streaming prepared 978,908 events / 96,063 windows, exact feature/label/key/text/
  bag parity with every frozen January and June window. Peak RSS 425 MiB;
  20-user checkpoint 6.480s + resumed 122.668s; idempotency 4.219s / zero new rows.
- Strict 54,763/0/0 remains unavailable: all later eligible identities already seen.
  No label, split or text-to-window defect. Missing-text/duplicate/identity stages
  and per-class counts are independently recorded; original results retained.
- Separately predeclared known-user/content-disjoint chronological experiment:
  54,763/23,616/10,553 windows, 14/19/8 positives; no held-out resampling.
- Numeric/text/combined logistic test TN/FP/FN/TP: 10091/454/7/1;
  10544/1/7/1; 10520/25/6/2. Precision .002198/.50/.074074,
  recall .125/.125/.25; F1 .004320/.20/.114286; AP .007826/.154422/.167069.
  False alerts/1,000 windows 43.020942/.094760/2.368995. Eight positives are limited.
- Train-only transforms, validation-only thresholds frozen before test; all three
  independent fits/reloads/scores/thresholds/artifact hashes reproduce. No activation.
- Training/reproduction: 499.263s / 8.52 GiB peak RSS. Full-release training still
  requires bounded vocabulary/matrices or more resources; no full-release run claim.
- Local/official public corpus review found no defensible policy sensitivity labels;
  no dataset downloaded. Separate runnable sensitivity interface tested only using
  explicitly unvalidated synthetic fixtures; CERT/PII/rule/model labels refused.
- NLP shadow loader defaults disabled; schema/digest/provenance/software/fallback
  tests pass. Six actual boundary-window scores match within 1e-12; rules preserved.
- Final isolated regression: 151 passed, no skips, one existing Starlette warning;
  preserved Flask: 22 passes. Original/live/copies/archives/application trees and
  frozen January/June research artifacts preserved. Raw text/data/models remain ignored.
- Authoritative detailed handoff: docs/implementation/nlp-followup/report.md;
  commands/resources in streaming.md, corpus requirement in sensitivity.md;
  comparison.json/cohort-audit.json/verification.json/publication.json hold evidence.
- Streaming milestone pushed/freshly verified at 3500e23d1a57e224280a83af837a8e4faf2c937f.
  Evaluation milestone pushed/freshly verified at 521331df8f651aa1c3797d488a913964f3581c55.
  This documentation closure follows; resolve final HEAD using git rev-parse HEAD.
  Normal final push/fresh remote equality reported in handoff; no force push/main merge.
- Exact next engineering step: predeclare external-memory training vocabulary/sparse
  matrix preparation, prove feature/score parity on this frozen run, then attempt
  larger chronological processing. Independent sensitivity corpus remains separate.

Historical handoffs below are preserved and superseded by this pointer.

---

# Completed continuation — 2026-10-08

The user-authorized remaining Phases 5–6 are complete at bounded acceptance.
The implementation plan ends at 6; no Phase 7 was added. Initial clean HEAD/fresh
remote matched dd4761fb97e22d3d43c25db6f7e1cd9f0f1bdee7 (divergence 0/0).
No AGENTS.md exists in the checkout/ancestors. Routine tested commits and normal
pushes were authorized; no merge into main/force push was performed.

- Phase 5: 22 adapter checks/131 isolated full passes; both adapters replayed all
  38 historical test windows with score equality, preserved rule responses and
  idempotent separate persistence. Explicit disabled/shadow defaults; optional
  authorized JSON/HTML views. Live/CERT schema mismatch falls back to rules.
  Published/freshly matched 6d51b5cf3a004d1dec0925859253f613b54d2d9c.
- Phase 6 evidence: published/freshly matched 85e253e3ddcc5f1690f0a9d4010cb870280ed9a1.
  Tooling checkpoint e49fb55297a6800d657132a9805f8d166f3bba1e is also recorded.
  Full safe archive scan: 32,770,222 source rows, 28 members/16.18 GB expanded.
  Predeclared June 7–21 cohort retains 978,908 events, 70 exact attack observables;
  zero errors/duplicates; indexed original source positions; idempotent replay.
- 95,930 fully observed windows; chronological train/validation/test counts
  58,258/25,919/11,753 with 14/19/8 positives. All test windows retained naturally.
  IF test TN10,294/FP1,451/FN5/TP3 (recall .375, precision .002063, F1 .004104).
  Logistic TN11,197/FP548/FN7/TP1 (recall .125, precision .001821, F1 .003591).
  Thresholds validation-only; both fits/scores/serialized hashes reproduced.
  Poor precision; eight test positives do not establish deployment quality.
- Fixed research heuristic/model/OR comparison uses one frozen common test cohort;
  OR adds false alerts without recall gain. This is not live endpoint policy.
  Numeric evaluation measures later time on observed users/continuing incidents;
  shared groups are disclosed, not unseen-user/incident generalization.
- 940,871 sanitized text events; strict text train/validation/test 54,763/0/0.
  Text comparison remains unavailable after identity controls. No sensitivity
  corpus/model accuracy claim; synthetic parser fixtures remain test evidence.
- Phase 6: 142 isolated pytest + 22 preserved Flask passes, no skips, one existing
  Starlette/httpx warning. Peak text RSS 3.73 GiB; full-release materialization
  exceeds available memory in the current pipeline. Full scan is not full eval.
- 30 original source/live hashes, 19 copied normalized sources, three input stats,
  upstream application trees and historical January research fingerprints match.
  Raw data/model files remain ignored; no activation or enforcement change.
- Fresh npm audit confirms 106 open findings (including two production-declared
  moderate groups); Docker still executes development tooling. No force upgrade.
  Windows monitoring/physical devices, PostgreSQL and Docker remain unverified.
- Authoritative status (under 200 lines): DATASHIELD_IMPLEMENTATION.md.
  Evidence: docs/implementation/phase5/advisory.md and phase6/evaluation.md,
  comparison.json, benchmark.json, text-study.json, verification.json, handover.md.
  Publication checkpoints: docs/implementation/publication.json; resolve final
  HEAD using git rev-parse HEAD. Final normal push/fresh SHA equality is checked
  after the closure commit and reported to the user.
- Exact next engineering step: implement streaming feature/text preparation with
  parity against this frozen bounded cohort before full-release evaluation.

Historical handoffs below are preserved and superseded by this pointer and the
user's latest authorization. Do not interpret their pending phases/old blockers
as current. There are no remaining phases in the existing plan.

---

# Current resume pointer — 2026-10-08

The authorized autonomous continuation through Phases 2–4 is finished at bounded
acceptance. Authoritative compact status: `DATASHIELD_IMPLEMENTATION.md` (191 lines).
Detailed commands/results: `docs/implementation/phase2/features.md`,
`phase3/behavioral-ml.md`, and `phase4/nlp-documents.md` under the same directory.
Historical handoffs below are preserved; their pending/one-phase-only instructions
are superseded by the user's later authorization and this current pointer.

- Branch `feat/cert-ml-nlp`; Phases 2, 3 and 4 each committed, pushed normally and
  freshly verified against GitHub. Exact SHAs: `docs/implementation/publication.json`.
- Latest implementation SHA: `dcf66aab4619f13598aa8558df80842db0920fca`.
  This documentation closure commit follows it; resolve current HEAD with
  `git rev-parse HEAD`. Its final push/fresh equality is verified after committing.
- Phase 2: 10,000 exact negative labels, 7,323 unmatched answer observables,
  zero ambiguous joins; 164 fully observed of 3,291 active user-hours.
- Phase 3: IsolationForest on chronological 83/43/38 windows. Held-out TN36/FP2,
  zero positives; recall/F1/PR-AUC undefined. Threshold/preprocessing/replay verified.
- Phase 4: 6,000 texts/111 duplicate bags; strict text cohort 81/1/0.
  Supervised comparison unavailable. Bounded TXT/PDF/DOCX extraction and redacted
  rule PII evidence preserve independent filename/hash signals. No sensitivity corpus.
- Final tests: 75 targeted research + 109 isolated full-suite passes, no skips;
  ten actual synthetic parser/status checks passed. One pre-existing warning.
- Original/live/archive/copied-source preservation passed; application trees
  unchanged; raw datasets/model files ignored; no model activation/policy changes.
- Data limitations: bounded January prefixes have no attack labels; broader
  chronological data with positives and a separate sensitivity corpus are needed.
- Native Windows/physical-device and PostgreSQL checks remain unverified;
  existing npm findings and development-server Docker exposure remain open.
- Exact next action on a new request: begin Phase 5 explicit shadow/advisory
  adapter contracts and fallback tests. Phase 5/6 are pending/outside this request.

---

# DataShield restart handoff — 2026-10-08

Historical handoff below; recovery succeeded in the continuation recorded at the end.
DATASHIELD_IMPLEMENTATION.md holds the current phase status; see the resume pointer above.

## Read first and current boundary

Read this file, applicable AGENTS.md, `DATASHIELD_IMPLEMENTATION.md`, and
`docs/implementation/phase0/audit.md` before doing further work.
No AGENTS.md was found in the checkout or its ancestors during the audit; check again.
Phase 0 functional checks are finished. Publication/fresh remote verification is the
remaining gate. Phase 1 has not started. This handoff request authorizes no Phase 1 work.
On a subsequent request to continue, resolve that gate before advancing.
The status file is 180 lines and must remain strictly below 200 lines.

## Exact repository and Git state

- Checkout: `/home/sohaib/Insider_Threat_Test_Dataset/DataShield~`.
  The trailing tilde is a literal part of the directory name; quote the path.
- Branch: `feat/cert-ml-nlp`; upstream: `origin/feat/cert-ml-nlp`.
- Origin: `https://github.com/sohaib-0897/DataShield.git`.
- HEAD immediately before this handoff commit:
  `344deb0eb9a2f1b8df4c7cfe465ad6d75e46f4ae`.
- That checkpoint's message: `docs: verify phase 0 baseline and npm audit scope`.
- Working tree/index were clean before creating this file; no unrelated changes existed.
- Cached `origin/feat/cert-ml-nlp` currently points to
  `344deb0eb9a2f1b8df4c7cfe465ad6d75e46f4ae`. This is a local ref, not a fresh GitHub query.
- Latest remote SHA explicitly confirmed by the user via successful manual push:
  `ea65336f41c233114b8a5e8761811db7695bc922`.
  The newer cached ref is consistent with a later push but is not independently verified.
- Latest freshly verified remote SHA in this agent session: **none**. Direct
  `git ls-remote` failed with `Could not resolve host: github.com` (exit 128);
  the alternate GitHub API web request also failed.
- Original upstream base: `74efcfd420d9e4442397d1c1276db67853a590f1`.
- Earlier source/audit WIP: `db47089b00b4613ea981f44182081d3ec0a5196e`.
- The handoff commit changes only `CONTEXT.md`; resolve its full SHA with
  `git log -1 --format='%H %s' -- CONTEXT.md`. Its own SHA cannot be embedded in itself.
- This file's push outcome is recorded at the end after the single authorized attempt.
  The general status file still records the earlier blocker until verified recovery.

## Original scope and phase plan

Implement release-aware CERT r4.2 ingestion, exact ground truth, behavioral ML,
NLP, defensible evaluation, and advisory integration while preserving the application.
The full acceptance criteria/dependencies/check commands are in
`DATASHIELD_IMPLEMENTATION.md`; it is the persistent implementation plan.

| Phase | Scope | Current status / dependency |
|---|---|---|
| 0 | Architecture audit, source preservation, isolated regression baseline | Checks finished; remote verification blocked |
| 1 | README/release/member/header inspection; safe resumable bounded ingestion | Pending; completed/published 0 required |
| 2 | Exact-event labels, versioned per-user windows, past-only baselines | Pending; requires 1 |
| 3 | CPU Isolation Forest, supervised baseline if supported, chronological evaluation | Pending; requires 2 |
| 4 | CERT text study; separate document extraction/sensitivity evidence | Pending; requires 2 and numeric benchmark 3 |
| 5 | Flagged advisory inference, compatible persistence/UI, isolated replay | Pending; requires 3 and 4 |
| 6 | Resource-permitting full runs, fair comparisons, error analysis, handover | Pending; requires 1–5 |

Execute exactly one phase per subsequent phase request and stop at its boundary.
Split oversized phases in the status file before starting. Record actual results,
not intended success. Preserve reports; do not repeat unchanged completed checks.
Update the status file at phase start/checkpoints/end, check its line count, stage
only phase files, commit/push normally, and verify the remote SHA. Never force-push
or merge into main automatically. Routine checkpoint commits/pushes are authorized.

## Preservation and verified architecture

- User's original source: `/home/sohaib/Downloads/AI-DLP-Agent` (no Git metadata).
- Its 19 top-level Python/HTML files were copied additively to `legacy/downloaded_flask/`.
  Original files remain intact; manifest records raw and Git LF-normalized hashes.
- Downloaded app uses Flask, SQLite telemetry, JSON policies/roles/analyst decisions,
  watchdog/Windows Security monitoring, WMI USB, local/USB/Google Drive hash copies,
  upload test server, filename/hash sensitivity, app/idle telemetry and rule scoring.
- Important preserved modules: `agent.py`, `windows_monitor.py`, `usb_monitor.py`,
  `upload_server.py`, `sensitivity.py`, `database.py`, `behavioral_monitor.py`,
  `baseline.py`, `behavior.py`, `feature_builder.py`, `prepare_training.py`,
  `risk_engine.py`, `dashboard.py`, `dashboard.html` under `legacy/downloaded_flask/`.
- `agent.py` starts monitoring/busy loop at import: never import it during research/tests.
- Upstream is a newer, different FastAPI/PostgreSQL/React app, preserved unchanged:
  `backend/app/main.py`, `core.py`, `models.py`, `analysis.py`, `sensitivity.py`,
  `backend/migrations/`, `frontend/src/`, `agents/`, `ml/data/`, `ml/training/`, `ml/registry/`.
- `legacy/flask/` is a third, SQLAlchemy Flask variant; do not substitute these apps.
- Do not migrate frameworks/databases or replace newer upstream functionality.
- Preserve monitor/logging behavior, schemas/data, routes/response fields, alerts,
  role assignments, policy semantics/settings, analyst decisions, rule-only fallback.
- Never reset live data, overwrite policies, discard user changes, or start monitors,
  servers, physical-device checks, live migrations or account seeding during research.
- Automated checks use temporary storage and mocked Windows dependencies. Mocked
  parser/logging checks do not verify Windows endpoints. New models default to shadow/
  advisory mode; no new automatic blocking. Use additive modules/flags/adapters.
- Exclude datasets, live DBs/documents, credentials, environments, caches, and large
  models from commits/pushes. This handoff contains no credentials or dataset contents.

## Dataset paths and decisions still needed

- Actual inputs remain `/home/sohaib/Downloads/r4.2.tar.bz2`,
  `/home/sohaib/Downloads/answers.tar.bz2`, and
  `/home/sohaib/Downloads/SEI_Insider_README.txt`.
- Requested `proj/dataset` and workspace dataset subfolder were absent; do not duplicate
  or relocate archives. Ignored `.local/cert_paths.json` records the actual paths.
- Planned separate research store: `research/local/cert_r42.sqlite` (ignored).
  Never ingest CERT into original `data/activity.db` or upstream production PostgreSQL.
- No actual release-header inspection, extraction, ingestion, labeling, model training,
  or authentic CERT evaluation has run. No new model artifact is active.
- Phase 1 must inspect supplied README/release docs/archive members/actual headers
  before choosing mappings. Reject traversal/escaping links; check disk space; chunk,
  log progress, resume, deduplicate, hash inputs and reconcile valid/error counts.
- Preserve actual IDs/users/timestamps/channels/actions/resources/metadata. Do not invent
  sensitivity labels, Windows app events, cloud uploads or unsupported actions.
- Research schema, timestamp assumptions and exact labeling granularity are undecided.
  Match malicious events where supported; do not label all history of malicious users.
- Answer/scenario metadata must stay outside inference features. Isolate users; use
  versioned shared features, past-only baselines, configurable work hours, cold-start
  handling, and explicit missing-signal availability rather than genuine zero counts.
- Use separate CERT/live models if signal coverage differs. Existing CERT loader's
  UTC and HTTP-to-CLOUD assumptions are not verified r4.2 semantics.
- Chronological train/validation/test, purge overlapping-window leakage, fit using
  training/past only, tune thresholds on validation only; keep natural test prevalence.
- Isolation Forest scores are not probabilities; document anomaly training population.
  Report zero-positive splits honestly, measured precision/recall/F1/PR-AUC/confusion,
  false alerts/user-day, volume, latency and supported scenario/detection timing.
- CERT malicious-activity labels are not document-sensitivity labels. Text classifiers
  require usable supervision and identity/duplicate/scenario leakage controls. No genuine
  sensitivity corpus is established; extraction/rules/interfaces must be described honestly.
- Model thresholds/fusion weights remain unvalidated; preserve filename/hash policy
  evidence and rule fallback; do not claim detection improvements without measurements.

## Phase 0 measured results and limitations

- Backend isolated baseline: exit 0, **34 passed**, one Starlette/httpx deprecation warning.
  SQLite/temp-copy checks; PostgreSQL integration remains **unverified**.
- Remaining hourly-feature checks: **4 passed, no skips/failures/errors** (both empty,
  activity only, transfers only, existing global-user aggregation characterization).
- Initial Flask checks: 18 passed/4 skipped. Together with the completed feature checks,
  22 distinct cases passed; no single native 22-case run is claimed. Historical reports kept.
- Frontend: **7 passed**; `npm ci` succeeded; **production build succeeded**.
  Counts/compile were user-verified; npm logs corroborate exit 0, build manifest exists.
- Preservation checks passed: 30 original source/live-file hashes, 19 preserved-source
  normalized hashes, and three archive size/mtime/inode observations unchanged.
  Archive integrity observation is stat comparison, not full archive hashing.
- Upstream application source/manifests/lockfile unchanged; only intentional prior docs/
  ignore additions. Original copied `risk_engine.py` retains a whitespace-only line.
- Native Windows monitoring and physical-device behavior remain **unverified**.
- Known existing gaps remain: global legacy hourly features mix users; watchdog summaries
  omit some changes; role-permitted after-hours alerts can be hidden. Upstream hourly
  training/live rolling windows differ, overlap, and lack complete availability contracts.
- No checks rerun for this documentation-only handoff; no live data/application changes.

## Dependencies and safe verification commands

- Existing Python environment: `.local/phase0-venv/` in this checkout; Python 3.14.4.
- Node 22.22.1 / npm 9.2.0 are available normally; frontend dependencies are in
  `frontend/node_modules/`, existing compiled output in `frontend/build/` (ignored).
- Dependencies are installed. Do not recreate the environment/reinstall by default.
  If missing after restart: install `requirements-dev.txt` and pandas into a local venv.
- These commands are for future justified rechecks; use new report/log names to retain
  completed evidence. Do not run a generic backend suite against a configured live DB.

```bash
cd '/home/sohaib/Insider_Threat_Test_Dataset/DataShield~'
.local/phase0-venv/bin/python -B scripts/verification/phase0_upstream_baseline.py --report .local/upstream_restart.json --log .local/upstream_restart.log
.local/phase0-venv/bin/python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --require-no-skips --report .local/flask_restart.json
python3 -B scripts/verification/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output .local/preservation_restart.json --compare docs/implementation/phase0/phase0_preservation_before.json
```

Frontend recheck commands, only if needed: inside `frontend/`,
`CI=true npm test -- --watchAll=false` then `npm run build`. `npm ci` is the reproducible reinstall
command if needed; it may require network access. Do not force upgrades or run audit fix.
Python installation recovery, only if needed: `python3 -m venv .local/phase0-venv`
then `.local/phase0-venv/bin/python -m pip install -r requirements-dev.txt pandas`.
Optional activation: `source .local/phase0-venv/bin/activate`; explicit interpreter
paths above work without activation.

## npm audit and deployment exposure

The successful install reported **106 vulnerable package groups: 3 low, 36 moderate,
65 high, 2 critical**. Cached install advisories matched against the unchanged lockfile
reproduce these totals; a fresh npm audit failed on registry DNS. These include indirect
dependency findings, not 106 demonstrated application exploits.

- Production-declared: **2 moderate** React Router / React Router DOM groups.
- Development-only graph: **104** (3 low, 34 moderate, 65 high, 2 critical).
- Critical packages: `proxy-addr@2.0.7` through Express development-server tooling;
  `shell-quote@1.10.0` through launch-editor/react-dev-utils.
- `frontend/Dockerfile` runs `npm start` (CRA development server). Dev dependencies
  therefore execute in the current Docker runtime; compiled static output is different.
- No exploit/reachability proof or harmlessness claim; findings remain unresolved.
  No package/lockfile upgrade, forced audit fix, or framework migration was performed.

## Evidence and plan locations (relative to checkout)

- Authoritative implementation plan/status: `DATASHIELD_IMPLEMENTATION.md`.
- Current audit: `docs/implementation/phase0/audit.md`.
- Detailed supplied-source audit: `docs/implementation/phase0/phase0_audit.md`.
- Completed backend: `docs/implementation/phase0/upstream_baseline_completed.json`.
- Completed features: `docs/implementation/phase0/remaining_feature_checks_completed.json`.
- Closure/results/evidence hashes: `docs/implementation/phase0/closure_verification.json`.
- Preservation: `docs/implementation/phase0/phase0_preservation_before.json`,
  `phase0_preservation.json`, `final_preservation_check.json` in the same directory.
- Copy provenance: `docs/implementation/phase0/source_reconciliation.json`.
- npm review: `docs/implementation/phase0/npm_audit_review.md` and `npm_audit_review.json`.
- Security history: `docs/security/security.md`; FYP reference material: `docs/fyp/`.
- Historical baseline/dependency reports remain in `docs/implementation/phase0/`;
  do not overwrite them. Local logs/caches/env/path configuration live in ignored `.local/`.
- Earlier failed reviewed push: `.local/phase0-reviewed-push.log`.
- No research evaluation results/models exist yet; research artifacts must stay separate.

## Outstanding work and exact recovery steps

No functional Phase 0 checks or source reconciliation remain outstanding. Only GitHub
publication/verification blocks closure. Before advancing, check actual HEAD and changes;
this documentation commit makes HEAD newer than the reviewed Phase 0 checkpoint.
The parent workspace status file is merely a resume pointer; use this repository's files.

```bash
cd '/home/sohaib/Insider_Threat_Test_Dataset/DataShield~'
git status --short
git branch --show-current
git remote -v
git log -3 --oneline
git fetch origin
git rev-list --left-right --count HEAD...origin/feat/cert-ml-nlp
git push origin feat/cert-ml-nlp
git rev-parse HEAD
git ls-remote origin refs/heads/feat/cert-ml-nlp
```

Stop on failed fetch/push or unexpected divergence; never force-push/reset/merge main.
Compare the freshly queried branch SHA with HEAD; cached equality alone is insufficient.
Once verified, update Phase 0 status/audit to reflect publication and mark 0 completed.
Then, on authorization to proceed, update status before starting Phase 1: inspect actual
README/release documentation/archive members/CSV headers, design supported mappings,
implement/test isolated safe resumable ingestion, run bounded real-data acceptance checks
and preservation regressions, commit/push/verify, and stop at the Phase 1 boundary.

## This handoff push outcome

Exactly one normal `git push origin feat/cert-ml-nlp` was attempted on 2026-10-08.
It failed with exit 128: `Could not resolve host: github.com`. The local log is
`.local/context-handoff-push.log` (ignored). No remote publication is claimed.
Only `CONTEXT.md` was committed. After the failed push, the unpublished handoff
commit was amended to include this actual outcome; no second push was attempted.
The final handoff SHA is available from `git log -1 --format='%H' -- CONTEXT.md`.
The working tree is intended to be clean after the amendment; verify with `git status`.
The implementation status/audit and all historical reports were left unchanged.
Recovery: restart the terminal, fetch/inspect divergence, push this local branch
normally, and verify GitHub's branch SHA equals local HEAD using the commands above.
Phase 1 remains pending. Windows monitoring/PostgreSQL remain unverified.

## Continuation recovery — 2026-10-08

The user explicitly authorized recovery and Phase 1. Elevated-access fetch and
normal push succeeded; fresh GitHub branch SHA `3548f75cb805f3645f65a1ab55f38773e8b0fc5b`
matched local HEAD. The earlier no-Phase-1 authorization applied to the old handoff
request. Phase 0 is now complete; consult DATASHIELD_IMPLEMENTATION.md for Phase 1 progress.

## Phase 1 completed — 2026-10-08

Phase 1 now meets bounded acceptance: release-aware isolated ingestion, 10,000
real events, zero errors, interrupted resume and idempotent API/CLI repeats,
28 passing safety tests, unchanged originals/live files/archives/applications.
The implementation checkpoint `07a39cadc924357b2b93e984e2bfd23e73ebf991` was pushed
normally and freshly verified against GitHub. The documentation closure commit
can be resolved using `git log -1 -- DATASHIELD_IMPLEMENTATION.md`; routine normal
push/fresh verification also applies to it. Raw data remains ignored. No labels,
models, live migration or automatic blocking were introduced. Phase 2 is pending
and requires a new request. Consult docs/implementation/phase1/ingestion.md and
the compact status file for exact commands, evidence and remaining limitations.

## Autonomous Phases 2–4 continuation — 2026-10-08

The user authorized implementing, testing, documenting, committing and pushing
Phases 2–4 sequentially without routine confirmation. This overrides earlier
one-phase-only handoff instructions. Initial clean HEAD and fresh GitHub branch
SHA matched 4c5a52ed8b6df96359ca45fe13035211993040de; no AGENTS.md found.
Phase 2 bounded acceptance is complete: exact source-field labels, 10,000 negatives,
7,323 unmatched observables from 70 incidents, zero ambiguous events; actor/subject
impersonation semantics preserved. 3,291 user-hours, 164 fully observed; 43 targeted
passes and 62 isolated tracked regression passes. Feature replay identical and
original/live/archive preservation passed. Commands/evidence: docs/implementation/phase2/.
Publish/verify this checkpoint, then proceed to Phase 3 and Phase 4 as authorized.
No full-dataset or supervised performance claim is supported by this zero-positive
January prefix. Raw artifacts are ignored; application behavior is untouched.

## Phase 3 bounded acceptance — 2026-10-08

Phase 2 checkpoint f958802f6f22b5a0fe46f3ee725c15177cf2e51f was pushed and
freshly matched GitHub before Phase 3. Frozen features support 83 train, 43
validation, 38 test windows; all zero-positive. CPU IsolationForest trained with
training-only preprocessing; validation-only 1% alert budget selected threshold.
Held-out TN36/FP2/FN0/TP0; precision 0, recall/F1/PR-AUC null. False alerts per
evaluated user-day 0.05263. Supervised baseline implemented but unavailable on
this real prefix. Independent training and serialized reload scores/hashes match.
51 targeted passes; full isolated staged-source regression evidence will be in
docs/implementation/phase3/verification.json. No active model or live changes.
After publishing/verifying this checkpoint proceed to Phase 4, as authorized;
text supervision is likewise unavailable on this prefix. Numeric report and
exact commands: docs/implementation/phase3/behavioral-ml.md and benchmark.json.

## Phase 4 bounded acceptance — 2026-10-08

Phase 3 checkpoint 63595ab35986bdc495ed916f24735312f559752a was pushed and
freshly verified before Phase 4. Real text study: 6,000 keyword events, 111 duplicate
bags, zero positives. Identity/duplicate controls retain 81/1/0 train/val/test
windows; supervised numeric/text comparison is unavailable, with no invented metrics.
TXT/PDF/DOCX extraction runs in bounded subprocesses, handles unavailable outcomes,
produces redacted rule PII evidence, and preserves separate caller filename/hash
signals. Ten synthetic actual parser checks passed; 75 targeted tests/no skips.
No genuine sensitivity corpus, trained text/sensitivity model, active research model,
live data/policy modification or full ingestion is claimed. Commands and exact
results: docs/implementation/phase4/nlp-documents.md, text_study.json and
document_acceptance.json. Full isolated regression/preservation verification and
publication are the final closure steps. Phase 5/6 remain outside this request.

## Phase 4 verification closure — 2026-10-08

109 tests passed in the staged-source isolated full suite, no skips, one existing
Starlette/httpx warning. 75 targeted research tests and ten actual synthetic
document status checks passed. Text replay and the feature replay after memory
guards are identical. Thirty original/live hashes, nineteen preserved normalized
hashes and three archive stat records match; all original application trees are
unchanged. Phase 4 verification: docs/implementation/phase4/verification.json.
Commit/push/fresh SHA verification closes this phase; publication evidence and a
new current resume pointer will be recorded after that success. Phase 5/6 remain
pending and outside this request. No new live model, policy, schema or data change.
