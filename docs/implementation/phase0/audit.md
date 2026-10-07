# Phase 0: checkout comparison and regression baseline

Updated 2026-10-08. **Functional Phase 0 checks are finished; reviewed checkpoint
publication/remote verification remains pending because this session lacks GitHub DNS.** This is the current audit;
`phase0_audit.md` retains the earlier detailed inspection of the supplied Flask source.

## Checkout and preservation decision

The user supplied a clean checkout at `/home/sohaib/Insider_Threat_Test_Dataset/DataShield~`
(the tilde is part of its directory name), on main at
`74efcfd420d9e4442397d1c1276db67853a590f1`. Its origin is
`https://github.com/sohaib-0897/DataShield.git`, and cached origin/main matches that SHA.
Fetch fails because github.com cannot be resolved; cached refs do not prove current remote state.
Branch `feat/cert-ml-nlp` was created from the existing checkout without resetting or merging.
No applicable AGENTS.md was found. Existing `docs/fyp/` documents intended requirements
and historical validation; these claims were checked against code and are not fresh test results.

The downloaded implementation at `/home/sohaib/Downloads/AI-DLP-Agent` is a different
Flask/SQLite application. Its 19 top-level Python/HTML files were copied additively to
`legacy/downloaded_flask/`. No upstream runtime file was replaced and the original remains intact.
No environments, databases, policies, logs with live content, sensitive documents, credentials,
or datasets were transferred. `source_reconciliation.json` records source and LF-normalized
Git hashes; existing `.gitattributes` normalizes text endings on commit.
Staged whitespace inspection flags one whitespace-only line already present in the imported
`risk_engine.py` (line 88). It was retained to preserve source bytes; all other phase files
pass the whitespace check. This is recorded separately from test failures.

| Concern | Downloaded implementation | Existing upstream implementation | Reconciliation |
|---|---|---|---|
| Dashboard | Flask HTML, `/api/*`, monitor controls | React plus FastAPI `/api/v1/*`, JWT/RBAC | Retain both; no route replacement |
| Storage | sqlite3 activity/transfers/behavior/alert_state, JSON policy | SQLAlchemy/PostgreSQL normalized events/alerts/evidence/policies/audit | No data transfer or schema migration |
| Collection | Security 4663/4660, WMI polling, fixed-folder SHA-256 copies | Configured Watchdog, WMI drive notifications, cooperating uploads, connection metadata | Preserve existing agents and source files |
| Sensitivity | Four filename policies and known SHA-256 content | Bounded CNIC/email rules, declared label, optional model adapter | Future adapters retain each source signal |
| Behavior | Per-user recent summary; global hourly CSV; no model fitting | Per-user rolling windows, heuristic, optional IsolationForest trainer/registry | Shared contract is future work; neither silently replaced |
| Analyst decisions | approved/suspicious/open status and role permissions | ALLOW/BLOCK/DISMISS/RESOLVE/INVESTIGATE with audit/RBAC | Preserve independent policy/decision semantics |

Only filenames `database.py` and `sensitivity.py` have same-name upstream counterparts,
and their APIs/implementations differ. This is preservation rather than replacing newer code.
Existing backend/frontend/agent code, migration history, and Compose startup remain unchanged.

## Verified implementation and gaps

See `phase0_audit.md` for the supplied Flask API fields, schemas, monitor assumptions and
pre-existing issues. `api_inventory.json` inventories 42 route decorators across the current
FastAPI backend, preserved Flask dashboard and its upload gateway using AST inspection.
Upstream API contracts also appear in `docs/development/api.md`; model/schema definitions
and actual code are authoritative. The 42-route count is not dynamic route execution evidence.

Upstream already implements a three-file expected-format CSV loader, streaming JSONL
preparation, optional CPU IsolationForest training, artifact provenance/evaluation guards,
numeric feature functions, sensitivity rules and classifier interfaces. It does not supply
an evaluated CERT model or independent document-sensitivity corpus.
The existing loader interprets timestamps as UTC and labels HTTP visits with channel CLOUD;
release-aware research mapping must be established from actual r4.2 files in Phase 1.
No existing adapter mapping is silently reused as verified CERT semantics.

The trainer uses hourly user groups and a chronological 80/20 row split. It reports outlier
counts, not precision/recall. There are no exact ground-truth joins, validation partition,
threshold selection, natural-prevalence metrics, or boundary-window purge checks.
Training features duplicate live feature logic; live windows roll per event and overlap.
Missing inputs currently default to zeros. Feature availability and shared contracts remain
Phase 2 work. Runtime history must be made defensible for research replay, including events
ingested out of order; current prior-risk lookup orders by assessment creation time.

Runtime artifact loaders are invoked per assessment and are not cached. With no configured
artifact, upstream behavior is HEURISTIC/INSUFFICIENT_HISTORY; failed configured artifacts
report UNAVAILABLE while deterministic activity/channel scoring remains available.
Default upstream weights and thresholds are documented in `docs/fyp/technical-facts.md`.
No model was trained, activated or assigned new fusion weights by this phase.

## Current measured baseline

| Check | Actual result | Evidence/limits |
|---|---|---|
| Downloaded Flask original (initial) | 18 passed, 4 skipped, no failures/errors | Historical `phase0_baseline.json`; initial safe check |
| Preserved Flask copy (initial) | 18 passed, 4 skipped, no failures/errors | Historical `preserved_flask_baseline.json` |
| Four outstanding feature checks | 4 passed, no skips/failures/errors | `remaining_feature_checks_completed.json`; native pandas, temporary SQLite |
| Existing upstream CERT-format tests | 2 passed | `python3 -B -m pytest -q tests/test_cert_loader.py -p no:cacheprovider` |
| Full existing upstream pytest | Exit 0, 34 passed, 1 warning | `upstream_baseline_completed.json`; earlier 7 dependency errors remain historical |
| Frontend Jest | 7 passed | User's verified terminal count; npm test log exit 0 |
| Frontend install/build | npm ci exit 0; production build compiled | User's verified terminal result, npm logs exit 0, existing build asset manifest |
| Native Windows / PostgreSQL | Not run | Parser/logging mocks are not endpoint or database-service validation |

The preserved Flask tests exercise logging/schema idempotence, user isolation, filename/hash
signals, API fields, rules, role/settings persistence, decisions/scoring, deduplication,
CSV export, and synthetic copy/upload detection. Process starts are prohibited; no watchers,
servers, physical devices or live policies were used. Four hourly-feature checks require
native Linux pandas: both empty, activity only, transfer only, and global-user aggregation.
They now pass with native pandas. The global-user aggregation test confirms the known
legacy behavior: two users in the same hour are combined. Passing that characterization
does not mean the legacy builder isolates users; correcting research features is Phase 2 work.
There are 22 distinct passing Flask checks across the initial 18-pass run and completed
four-case run; no single new 22-test native run is claimed or repeated.

The upstream isolation wrapper copies tracked Python/config into a temporary directory and
sets synthetic secrets and SQLite-only storage. The legacy API test's test-specific database
is also inside that temporary copy. The completed report records 34 passes and one
Starlette/httpx TestClient deprecation warning. It is a warning, not a test failure.
Historical missing-dependency errors remain in `upstream_baseline.json`.
The frontend test count is attributed to the user's verified terminal result; npm command
logs corroborate exit 0. `closure_verification.json` identifies evidence paths and hashes.

Source and live-file integrity observations are in `phase0_preservation*.json`; no content is
stored there. The downloaded originals and all upstream files except the intentionally extended
`.gitignore` and the intentionally updated security documentation are checked against their pre-work hashes. The preservation snapshot excludes
newly added files from the upstream comparison.

## Paths and exact recovery/check commands

Archives are still in `/home/sohaib/Downloads`. Requested workspace `proj/dataset` and
`dataset` paths do not exist. `.local/cert_paths.json` records actual archive paths and a
separate future `research/local/cert_r42.sqlite`; it is ignored and no ingestion consumes it yet.
No archive or sensitive document was moved, duplicated, extracted, or ingested.

Run from the actual checkout, using an environment with package/network access:

```bash
python3 -m venv .local/phase0-venv
.local/phase0-venv/bin/python -m pip install -r requirements-dev.txt pandas
.local/phase0-venv/bin/python -B scripts/verification/phase0_upstream_baseline.py --report docs/implementation/phase0/upstream_baseline.json --log .local/phase0_upstream_isolated.log
.local/phase0-venv/bin/python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --report docs/implementation/phase0/preserved_flask_baseline.json
python3 -B scripts/verification/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output .local/preservation_after.json --compare docs/implementation/phase0/phase0_preservation_before.json
```

Initially, pip could not resolve pandas and the first Flask-only checks used pure-Python
Flask from the Windows venv; those historical dependency failures remain in the original
reports. Native dependencies are now installed in `.local/phase0-venv`, and the four
previously skipped cases have completed. Node 22.22.1 and npm 9.2.0 are also available.

With Node/npm installed, run `npm ci`, `npm test`, and `npm run build` inside `frontend/`.
Do not run E2E against a live stack or reseed existing accounts; a disposable service setup
is required for any additional integration check.

The user subsequently confirmed a successful manual push of `db47089b00b4613ea981f44182081d3ec0a5196e`.
At resume, local HEAD and cached `origin/feat/cert-ml-nlp` matched that SHA; upstream tracking is configured.
This resolves the previous checkpoint's push blocker. A fresh remote SHA query still fails
with `Could not resolve host: github.com` (exit 128); cached equality is not live verification.
New checkpoint pushes from this session may still require a manual push. With working access, run:

```bash
git fetch origin
git status --short
git push -u origin feat/cert-ml-nlp
git rev-parse HEAD
git ls-remote origin refs/heads/feat/cert-ml-nlp
```

Inspect divergence first and never force-push. Remaining Phase 0 work is publishing and
verifying this reviewed checkpoint. No functional baseline checks remain unfinished.

## Historical remaining-check retry after manual push

The prior passing checks were not repeated. An explicit PyPI installation retry still failed
with `No matching distribution found for pandas` (exit 1). Native isolated venv imports are
unavailable for all 17 required modules checked; Node/npm are absent. Direct DNS lookups for
GitHub, PyPI and npm's registry all fail with temporary name-resolution errors. No unsupported
Python-version claim is inferred from pip's error. See `dependency_readiness.json`.

Only the four previously skipped feature checks were attempted. They again skipped because
pandas is unavailable: **0 passed, 4 skipped, no test failures/errors**. A new strict harness
flag returns exit 2 for this incomplete run, even though unittest prints `OK (skipped=4)`.
The separate `remaining_feature_checks.json` preserves this result without overwriting the
earlier 18-pass/4-skip baseline. Backend and frontend suites were not rerun with unchanged,
missing dependencies; their previous failures/unavailable status remain recorded.

From a terminal with native dependencies and working package-index access:

```bash
cd '/home/sohaib/Insider_Threat_Test_Dataset/DataShield~'
.local/phase0-venv/bin/python -m pip install -r requirements-dev.txt pandas
.local/phase0-venv/bin/python -B scripts/verification/phase0_upstream_baseline.py --report docs/implementation/phase0/upstream_baseline_completed.json --log .local/phase0_upstream_completed.log
.local/phase0-venv/bin/python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --test test_feature_both_sources_empty --test test_feature_activity_only --test test_feature_transfer_only --test test_feature_existing_global_aggregation_characterization --require-no-skips --report docs/implementation/phase0/remaining_feature_checks_completed.json
cd frontend
npm ci
CI=true npm test
npm run build
```

Install Node/npm first if unavailable; repository CI uses Node 22 and Python 3.11.
Keep the prior result files as historical evidence. Record genuine feature failures separately
if native pandas exposes them; Phase 0 identifies pre-existing defects rather than rewriting
the feature builder prematurely. All checks use synthetic/temp storage; no live stack restart,
migration, seeding, reset, or endpoint collection is part of these commands.

## Reviewed closure — 2026-10-08

The completed user-generated JSON reports were read and validated against the current
checkpoint `ea65336f41c233114b8a5e8761811db7695bc922`. The backend report has exit 0,
34 passes and one deprecation warning; the four feature cases have no skips/failures/errors.
The user's frontend results are 7 passes, successful npm ci, and successful production
compilation. Read-only npm logs corroborate command exit 0 and the build asset manifest
exists. Completed checks were not repeated; every earlier report was retained.

All 30 original source/live-file hashes, the 19 preserved source hashes, and all three
archive size/mtime/inode observations remain unchanged. Upstream application source,
package manifest and lockfile are unchanged. `closure_verification.json` records the
evidence and preservation checks. Native Windows monitoring and PostgreSQL service
integration remain explicitly unverified; Linux/SQLite/mocked tests do not replace them.

The npm scope review is in [npm_audit_review.md](npm_audit_review.md), with summarized
cached evidence in `npm_audit_review.json`. It reproduces the user's 106 finding groups:
two moderate production-declared React Router groups and 104 dev groups, including
two critical groups. Current Docker uses CRA's development server, so install-time
scope is not proof of runtime inapplicability. These pre-existing findings remain open;
no forced upgrade, audit fix, package edit, or framework migration was performed.

No functional Phase 0 check remains incomplete. This reviewed checkpoint still needs
publication and remote verification; GitHub fetch/query/actual push fail on DNS here.
The actual push failure is recorded in ignored `.local/phase0-reviewed-push.log` (exit 128).
Phase 1 has not started. After publishing/verifying this checkpoint, complete Phase 0's
status and start Phase 1: inspect the supplied README/release documentation/archive members
and actual CSV headers before implementing mappings or extracting/ingesting any records.
