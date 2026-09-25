# Technical fact sheet

Reference for the implemented pre-CERT prototype. This documentation pass makes no new runtime, hardware, training, or benchmark claim.

## Components and contracts

| Area | Implemented fact |
| --- | --- |
| Backend | Python / FastAPI; active application in `backend/app/`. |
| Database and persistence | PostgreSQL; SQLAlchemy ORM; events, risks, alerts, evidence, decisions, audit, and reports use stored data. |
| Migrations | Alembic in `backend/migrations/`; root `alembic.ini`; head `9e20ab47c132`. |
| Frontend | React, React Router v6, Tailwind CSS, Recharts; UI reads the API. |
| Containerization | Docker Compose; host monitoring agents run outside containers. |
| Endpoint monitoring | Python / Watchdog; WMI volume-change notifications and Windows `GetDriveTypeW` for removable drives; psutil for browser connection metadata. |
| User authentication | Argon2 password hashes through pwdlib; HS256 JWTs expire after eight hours; active-user lookup on authenticated requests. No refresh or individual-token revocation. |
| Roles | ADMIN, ANALYST, VIEWER. Decisions/report export: ADMIN or ANALYST. Policies, user/model management, full Audit log: ADMIN. |
| Agent authentication | Shared `X-Agent-Key`; a prototype boundary, not per-endpoint identity provisioning. |
| Telemetry | FILE, USB, UPLOAD, NETWORK; CLOUD is also accepted by the event schema/data adapter. NETWORK observations are connection metadata only. |
| Behavior states | MODEL, HEURISTIC, INSUFFICIENT_HISTORY, UNAVAILABLE. No trained behavior model is active in the validated demo. |
| Sensitivity states | RULE, DECLARED, UNAVAILABLE; optional MODEL adapter is implemented but not demonstrated as an active trained classifier. |
| Feature / scoring versions | `event-window-v2` / `weighted-v1`; default feature window duration 60 minutes. |
| Duplicate delivery | Stable `source_event_id`, existing-event lookup, database uniqueness, bounded agent retries. No durable offline delivery guarantee. |
| UI refresh | Shared overview/investigation/system/audit loader polls every 15 seconds; not a WebSocket stream. |
| Upload decisions | Below-threshold policy auto-allow or analyst ALLOW/BLOCK for escalated requests. Cooperating caller must enforce it; RESOLVE is a workflow state. |
| Data handling | Bounded sample scanning; event metadata allowlist; discarded sample text; masked matches. Resource paths and notes are not automatically anonymized. |

## Risk explanation

Default weighted score: `0.20 * behavior + 0.30 * sensitivity + 0.20 * activity + 0.20 * channel + 0.10 * history`, using rounded contributions and a maximum total of 100. Default alert threshold: 55. Severity boundaries: MEDIUM 35, HIGH 65, CRITICAL 85; below 35 is LOW.

Historical input is half the most recent prior risk, bounded by the scorer. Components and contributions are stored with each assessment, along with policy threshold and source/version labels. Default values are configurable; the displayed alert's stored explanation is the authority for that result. These are triage scores, not calibrated probabilities.

Without a configured behavior artifact, at least three eligible prior feature windows are required. The heuristic uses the current count's excess over the prior mean, scaled by 30 and capped at 100. Runtime windows are recorded per event, so overlapping windows are possible. A configured behavior artifact failure yields UNAVAILABLE rather than silently claiming a heuristic or model result.

## Validation baseline and provenance

| Check | Recorded result and scope |
| --- | --- |
| Python tests | 34 passed in the structural verification. |
| Jest | 7 passed in the structural verification. |
| Production build | Passed in the structural verification. |
| Playwright | 1 passed in the last fully credentialed validation. Not rerun for presentation: existing demo password unavailable. |
| Docker / database | Prior validated stack had PostgreSQL healthy, backend `/ready` = ready, frontend HTTP 200, and database revision `9e20ab47c132`. |
| Remote CI | [Structural commit 08712d2: PASS](https://github.com/sohaib-0897/DataShield/actions/runs/36196257681), including API and frontend jobs. |
| Dependencies | Latest recorded declared Python audit: no known vulnerabilities; frontend production audit: 2 moderate React Router v6 advisories. No v7 upgrade in this pass. |
| Physical USB | Not tested in the recorded validation. Synthetic USB events are not hardware evidence. |
| ML quality | No authentic CERT evaluation, no active trained behavior model, no accuracy/precision/recall claim. |

The presentation pass checks documentation and links. It does not repeat the runtime baseline. See the [validation record](pre-fyp-hardening-checklist.md) for earlier results and historical failures.

## Latest verified local 10,000-alert benchmark

These are the latest verified measurements supplied for this presentation pass from the local Docker/PostgreSQL environment. They were not rerun here. They describe local API query timings, not universal latency, an SLA, ingestion throughput, or model quality. Environment and workload differences affect results.

| Query | Median (ms) | p95 (ms) |
| --- | ---: | ---: |
| Alerts listing | 205.32 | 564.47 |
| Severity filter | 166.54 | 248.10 |
| Status filter | 164.56 | 180.60 |
| Channel filter | 184.07 | 207.70 |
| User filter | 345.10 | 577.57 |
| Date filter | 80.28 | 107.99 |
| Report summary | 56.82 | 159.03 |
| Alert detail | 41.03 | 66.49 |

The benchmark utility lives at `scripts/benchmark/benchmark_alerts.py`. It writes temporary synthetic database fixtures and is intentionally not run for presentation polish. Do not describe its 10,000-alert dataset as CERT or a model evaluation dataset.

## Presentation boundaries

No arbitrary HTTPS payload interception; no reversal of completed filesystem activity; cooperating clients enforce upload decisions. TLS is expected through deployment/proxy configuration for non-local use. Shared agent keys, missing JWT refresh/revocation, and pending physical USB validation remain explicit limitations. Future model integration requires licensed source data, held-out evaluation, and reviewed activation; neither synthetic data nor outlier counts establish detection quality.
