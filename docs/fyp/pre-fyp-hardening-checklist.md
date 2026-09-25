# Pre-FYP validation record

The structural verification at commit `08712d2` passed: 34 Python tests, 7 Jest tests, frontend build, healthy preserved Docker stack, `/ready`, frontend HTTP 200, and Alembic head `9e20ab47c132`. [Remote CI passed](https://github.com/sohaib-0897/DataShield/actions/runs/36196257681). The presentation pass changes documentation only; E2E was not rerun because the existing demo password was unavailable.

The detailed live smoke, one passing credentialed browser walkthrough, and persistence results below are earlier completed validation records. The older failed release-freeze attempt is retained at the end as history, not the current stack status. No fresh integration or physical hardware validation is claimed by this document update.

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
| Physical device behavior | NOT TESTED | No physical USB validation was performed. Exact synthetic manual steps are in `docs/operations/usb-testing.md`. |
| Python dependencies | PASS FOR DECLARED SET | `pip-audit -r requirements-dev.txt`: no known vulnerabilities. A full scan of the reused virtual environment separately reported undeclared packages and a local unresolvable distribution. |
| npm dependencies | PARTIAL | Two moderate production React Router advisories at 6.30.6; full CRA development tree has 31 findings (9 low, 8 moderate, 14 high). Non-forced `npm audit fix` did not clear them; forced resolution proposes breaking/invalid versions. |
| CI | PASS AT STRUCTURAL COMMIT | Remote run 36196257681 passed for `08712d2`; PostgreSQL/Alembic, backend tests, frontend tests, and build. Browser test remains an optional local workflow. |
| Accessibility | QUICK PASS | Explicit form labels, semantic table headers/nav, keyboard focus, alert/status messages and disabled controls added. No formal WCAG audit claimed. |
| Repository secret/path search | PASS | No active-source TODO/FIXME/HACK, `console.log`, personal absolute path, or matching hard-coded credential found. `.env.example` is intentionally tracked; real `.env` and generated artifacts are ignored. |

### Latest verified 10,000-alert benchmark

The current reference values are in the [technical fact sheet](technical-facts.md#latest-verified-local-10000-alert-benchmark): alerts listing median 205.32 ms / p95 564.47 ms, with the full eight-query table there. These supersede the earlier local timing table. They are the latest verified values supplied for presentation, not a rerun during this documentation pass or universal performance guarantees.

The one known sizeable feature-development phase is authentic CERT evaluation and model review. It cannot be completed before the licensed dataset and ground-truth evaluation data are available.

### Historical failed release-freeze attempt (2026-09-25)

- Backend: `34 passed`; one Starlette/httpx deprecation warning.
- Frontend: `7 passed`; optimized production build compiled successfully. npm emitted its `--watchAll` CLI notice, and React Router v6 emitted upstream future-flag notices.
- Python dependency audit: `pip-audit -r requirements-dev.txt` found no known vulnerabilities. `npm audit --omit=dev` still reports two moderate React Router v6 advisories; no breaking upgrade was forced.
- Docker: the explicitly requested `docker compose down -v` removed the local Compose volume. Both application images built, but subsequent `docker compose up` attempts hung before creating services; `/ready`, frontend HTTP, migration, demo seed, live smoke, restart persistence, and a fresh benchmark therefore could not be reverified in this attempt.
- Browser E2E: Playwright/Chromium ran but failed at navigation with `ERR_CONNECTION_REFUSED` for `http://localhost:3001`, because Compose had not started the frontend. This is not a passing browser validation.
- Performance: that attempt did not rerun the benchmark. Earlier measurements were subsequently superseded by the latest verified values linked above.
- At that earlier attempt, `gh` was unavailable and remote GitHub Actions status was not verified. The later structural CI result is linked above.

That failed attempt was not fully verified. Subsequent restored-volume and structural verification established the current baseline at the top of this document. Release tagging remains a separate operator decision; no tag is created by presentation preparation.
