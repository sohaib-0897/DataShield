# Pre-FYP release-candidate gap audit

Prior integration verification on 2026-09-25 used the active FastAPI/React/PostgreSQL source and preserved the local Compose volume. The fresh PostgreSQL migration ran against a separate temporary database that was dropped afterward. The release-freeze verification attempt is recorded separately below; it must not be read as a second successful integration run.

| Area | Status | Evidence / remaining limit |
|---|---|---|
| Supported runtime and architecture | PASS | Docker runs the FastAPI API and React UI. Flask-era files remain migration/history references only. |
| Empty PostgreSQL schema migration | PASS | Temporary PostgreSQL database applied both Alembic revisions to `9e20ab47c132`, then the temporary database was removed. |
| Compose rebuild and service readiness | PASS | `docker compose up --build -d`; backend `/ready` returned ready; frontend returned HTTP 200. |
| Synthetic scenario | PASS | Seven idempotent events flow through ingestion; USB and upload produced alerts and the seeded source reports `HEURISTIC`. Seed prints counts and no secrets. |
| Browser workflow | PASS | Playwright Chromium against Compose/PostgreSQL: login, overview, alert list, investigation, confirmed BLOCK, audit log, reports, model status, user activity, and policy settings. One browser walkthrough passed. |
| Backend suite | PASS | 34 tests passed. Includes exact report fixtures, JWT expiration/inactive-user checks, and candidate artifact safeguards. One Starlette/httpx deprecation warning remains. |
| Frontend tests and production build | PASS | 7 Jest tests passed; production build compiled. React Router v6 emits its upstream future-flag warnings. |
| Database restart persistence | PASS | After backend and PostgreSQL restarts, readiness remained healthy; synthetic event, BLOCK decision, and audit rows remained present. |
| Live API smoke | PASS | Ready, login, ingestion, duplicate suppression, masked evidence, heuristic source, BLOCK decision, audit, and reports passed. The smoke run observed 9 recent events and 4 alerts. |
| Reporting | PASS | Report fixture asserts exact counts, unique detection-alert count, pending decisions, event/risk daily aggregates, user ranking, and exclusion of all aggregates outside the requested range. |
| Performance | PASS | 10,000 PostgreSQL alerts; seven samples per query. Tagged rows and unused benchmark-only account/endpoint were removed. See results below / ignored `artifacts/benchmarks/latest.json`. |
| Model artifact safety | PASS WITH HUMAN PROVENANCE LIMIT | Dataset fingerprint and explicit `--real-dataset`/`--synthetic-test` choice required. Synthetic test artifacts cannot register. Activation requires a distinct held-out fingerprint, `REVIEWED` state, and bounded labeled metrics. Metadata review is still an operator attestation, not a cryptographic CERT signature. |
| User session and RBAC | PASS WITH PROTOTYPE LIMIT | Logout clears browser token; expired JWT and inactive user reject; role guards remain server-side. No refresh or revocation; JWT lifetime is eight hours. |
| Agent credentials | INTENTIONAL LIMIT | Shared agent key retained to avoid changing the stable host-agent protocol; no per-endpoint token provisioning/rotation. |
| Physical device behavior | NOT TESTED | No physical USB validation was performed. Exact synthetic manual steps are in `docs/usb-testing.md`. |
| Python dependencies | PASS FOR DECLARED SET | `pip-audit -r requirements-dev.txt`: no known vulnerabilities. A full scan of the reused virtual environment separately reported undeclared packages and a local unresolvable distribution. |
| npm dependencies | PARTIAL | Two moderate production React Router advisories at 6.30.6; full CRA development tree has 31 findings (9 low, 8 moderate, 14 high). Non-forced `npm audit fix` did not clear them; forced resolution proposes breaking/invalid versions. |
| CI | CONFIGURATION REVIEWED, REMOTE NOT RUN | Workflow orders PostgreSQL service, Alembic, backend tests, frontend tests, and build. No remote GitHub Actions run is claimed. Browser test remains an optional local workflow. |
| Accessibility | QUICK PASS | Explicit form labels, semantic table headers/nav, keyboard focus, alert/status messages and disabled controls added. No formal WCAG audit claimed. |
| Repository secret/path search | PASS | No active-source TODO/FIXME/HACK, `console.log`, personal absolute path, or matching hard-coded credential found. `.env.example` is intentionally tracked; real `.env` and generated artifacts are ignored. |

### 10,000-alert benchmark

PostgreSQL 16.15 in the local Docker/WSL2 environment; seven measured samples per query. Timings are environment-specific, not an SLA.

| Query | Median ms | p95 ms |
|---|---:|---:|
| Alerts listing | 34.44 | 51.40 |
| Severity filter | 28.09 | 35.53 |
| Status filter | 34.25 | 39.15 |
| Channel filter | 27.21 | 44.47 |
| User filter | 97.27 | 155.85 |
| Date filter | 25.55 | 29.34 |
| Report summary | 55.02 | 61.96 |
| Alert detail | 16.44 | 23.63 |

The one known sizeable feature-development phase is authentic CERT evaluation and model review. It cannot be completed before the licensed dataset and ground-truth evaluation data are available.

### Release-freeze verification attempt (2026-09-25)

- Backend: `34 passed`; one Starlette/httpx deprecation warning.
- Frontend: `7 passed`; optimized production build compiled successfully. npm emitted its `--watchAll` CLI notice, and React Router v6 emitted upstream future-flag notices.
- Python dependency audit: `pip-audit -r requirements-dev.txt` found no known vulnerabilities. `npm audit --omit=dev` still reports two moderate React Router v6 advisories; no breaking upgrade was forced.
- Docker: the explicitly requested `docker compose down -v` removed the local Compose volume. Both application images built, but subsequent `docker compose up` attempts hung before creating services; `/ready`, frontend HTTP, migration, demo seed, live smoke, restart persistence, and a fresh benchmark therefore could not be reverified in this attempt.
- Browser E2E: Playwright/Chromium ran but failed at navigation with `ERR_CONNECTION_REFUSED` for `http://localhost:3001`, because Compose had not started the frontend. This is not a passing browser validation.
- Performance: the table above and ignored `artifacts/benchmarks/latest.json` are the earlier completed 10,000-alert run, not a benchmark rerun during this freeze attempt.
- The local `gh` executable is unavailable, so remote GitHub Actions status has not been verified.

Do not call this release freeze fully verified or create the release tag until the Docker-backed checks can be completed successfully.
