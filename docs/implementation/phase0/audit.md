# Phase 0: checkout comparison and regression baseline

Updated 2026-10-07. **Phase remains incomplete:** native dependencies/frontend tooling
and remote checkpoint verification are unavailable. This is the current audit;
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
| Downloaded Flask original | 18 passed, 4 skipped, no failures/errors | `phase0_baseline.json`; initial safe check |
| Preserved Flask copy | 18 passed, 4 skipped, no failures/errors | `preserved_flask_baseline.json`; synthetic fixtures/temp DBs/policies |
| Existing upstream CERT-format tests | 2 passed | `python3 -B -m pytest -q tests/test_cert_loader.py -p no:cacheprovider` |
| Full existing upstream pytest | Collection stopped with 7 errors | `upstream_baseline.json`; missing Flask/Pydantic/SQLAlchemy/FastAPI dependencies |
| Frontend Jest/build | Not run | Node and npm unavailable; no dependency directories copied |
| Native Windows / PostgreSQL | Not run | Parser/logging mocks are not endpoint or database-service validation |

The preserved Flask tests exercise logging/schema idempotence, user isolation, filename/hash
signals, API fields, rules, role/settings persistence, decisions/scoring, deduplication,
CSV export, and synthetic copy/upload detection. Process starts are prohibited; no watchers,
servers, physical devices or live policies were used. Four hourly-feature checks require
native Linux pandas: both empty, activity only, transfer only, and global-user aggregation.
They remain skipped; empty-table success or failure must not be invented.

The upstream isolation wrapper copies tracked Python/config into a temporary directory and
sets synthetic secrets and SQLite-only storage. The legacy API test's test-specific database
is also inside that temporary copy. Its failures reproduce the dependency baseline established
before modifications. The repository's prior claims of 34 Python and 7 frontend passes remain
historical evidence, not results reproduced in this environment.

Source and live-file integrity observations are in `phase0_preservation*.json`; no content is
stored there. The downloaded originals and all upstream files except the intentionally extended
`.gitignore` are checked against their pre-work hashes. The preservation snapshot excludes
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

The isolated venv was created here, but pip could not resolve pandas (`No matching distribution
found for pandas`). System dependencies remain unavailable. The current Flask-only checks
used pure-Python Flask packages in the supplied Windows venv via `--dependency-root`; the
Windows pandas build fails on `os.add_dll_directory` and was not emulated.

With Node/npm installed, run `npm ci`, `npm test`, and `npm run build` inside `frontend/`.
Do not run E2E against a live stack or reseed existing accounts; a disposable service setup
is required for any additional integration check.

GitHub fetch, push preflight, actual push, and remote SHA verification all fail with
`Could not resolve host: github.com` (exit 128). The push log is `.local/phase0-push.log`.
An incomplete phase is preserved as a local WIP commit; no successful GitHub checkpoint
is claimed. With working network access, run:

```bash
git fetch origin
git status --short
git push -u origin feat/cert-ml-nlp
git rev-parse HEAD
git ls-remote origin refs/heads/feat/cert-ml-nlp
```

Inspect divergence first and never force-push. Remaining Phase 0 work: resolve dependencies,
finish skipped feature tests/full regression/frontend checks, review any genuine baseline
failures, and verify the required remote checkpoint before advancing to Phase 1.
