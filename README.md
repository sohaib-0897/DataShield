# DataShield

**AI-Assisted Multi-Layer Data Loss Prevention & Insider Risk Prototype**

DataShield turns Windows endpoint and cooperating-client telemetry into explainable risk assessments, masked evidence, and an analyst investigation workflow.

[![CI](https://github.com/sohaib-0897/DataShield/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/sohaib-0897/DataShield/actions/workflows/ci.yml)

**FastAPI | PostgreSQL | React | Windows monitoring | Docker | Academic prototype**

## What DataShield does

DataShield helps an analyst connect file activity, removable-media activity, and upload attempts to the employee, endpoint, sensitivity findings, and prior activity behind an alert. It records the reasoning and the analyst's response in PostgreSQL.

## Architecture overview

Windows agents and cooperating upload clients send events to FastAPI. The service validates and normalizes them, applies sensitivity analysis, aggregates behavior features, and calculates weighted risk. React presents the persisted alerts, evidence, audit records, and reports through the API.

See the [architecture diagram and response flow](docs/architecture/architecture.md). Network monitoring supplies connection metadata only; upload enforcement requires a cooperating client.

## Key capabilities

- **Endpoint telemetry:** Watchdog file events, Windows removable-drive monitoring, cooperating upload requests, and optional browser connection metadata.
- **Explainable triage:** sensitivity findings, activity features, explicitly labeled behavioral analysis, and a stored risk breakdown.
- **Investigation:** filterable alerts, masked detections, supporting events, analyst decisions, and audit history.
- **Persistence and access:** PostgreSQL records, duplicate-event handling, JWT sessions, ADMIN / ANALYST / VIEWER roles, and reporting.

## Demo and screenshots

The existing synthetic scenario follows `synthetic.employee` from three earlier normal activities to a sensitive file, removable-media transfer, and upload attempt. Current behavior analysis is **HEURISTIC**; the scenario does not demonstrate a trained anomaly model.

Use the [FYP demo runbook](docs/fyp/fyp-demo-runbook.md), [3-5 minute spoken script](docs/fyp/demo-script.md), or [60-90 second video script](docs/fyp/portfolio-video-script.md). The [nine-shot screenshot plan](docs/fyp/screenshots.md) specifies framing, synthetic selections, and privacy checks. Reviewed application captures are pending access to the existing demo login; no illustrative images are presented as application evidence.

## Technology stack

| Area | Implementation |
| --- | --- |
| API and persistence | Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic |
| Analyst interface | React, React Router v6, Tailwind CSS, Recharts |
| Endpoint collection | Python, Watchdog, WMI / Windows drive APIs, psutil |
| Access control | JWT, Argon2 password hashing, server-side RBAC |
| Delivery and checks | Docker Compose, GitHub Actions, pytest, Jest, Playwright |

## Repository structure

```text
DataShield/
+-- backend/       FastAPI app and Alembic migrations
+-- frontend/      React UI and e2e/ browser workflow
+-- agents/        Filesystem, USB, upload, network, shared delivery
+-- ml/            data/, training/, registry/; ignored artifacts
+-- scripts/       demo/, migration/, verification/, benchmark/
+-- tests/         Automated suites and isolated manual/ procedures
+-- docs/          Architecture, development, operations, FYP, ML, security
+-- legacy/        flask/ and windows/ migration/history references
+-- docker-compose.yml
+-- README.md
```

The supported backend is `backend/app/`. Retained Flask code is not the Compose runtime.

## Quick start

For a **new local checkout**, use Docker Desktop and PowerShell at the repository root. Create `.env` only if absent and configure distinct random values for `DATASHIELD_JWT_SECRET`, `DATASHIELD_AGENT_KEY`, and a URL-safe `DATASHIELD_DB_PASSWORD` (at least 32 characters each).

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Configure the local secrets before startup.
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://localhost:8001/ready
```

Dashboard: <http://localhost:3001> | API documentation: <http://localhost:8001/docs> | PostgreSQL: local port `5434`.

For an existing installation, retain its Compose project and any volume override. Use its existing account and data. The [runbook](docs/fyp/fyp-demo-runbook.md) separates first-time synthetic setup from presentation of an already validated database; seeding again changes the demo account password.

## Testing

With the [development dependencies installed](CONTRIBUTING.md), run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

From `frontend/`:

```powershell
$env:CI = 'true'
npm test -- --watchAll=false
Remove-Item Env:CI -ErrorAction SilentlyContinue
npm run build
# Requires the existing demo password in this shell and the running stack:
$env:DATASHIELD_FRONTEND_URL = 'http://localhost:3001'
npm run test:e2e
```

Playwright reads `DATASHIELD_DEMO_ADMIN_PASSWORD` and records a BLOCK decision on a synthetic alert. See [testing](docs/development/testing.md) for setup and scope.

## ML status

No CERT dataset is included and no trained behavior model is active. Without a configured artifact, behavior reports `HEURISTIC` or `INSUFFICIENT_HISTORY`; an unavailable configured behavior artifact reports `UNAVAILABLE`. `MODEL` is reserved for an explicitly configured artifact that passes the required provenance and evaluation checks.

Optional preparation, IsolationForest training, artifact registry, and sensitivity-model adapters exist. Authentic CERT evaluation and model-quality claims remain pending. See [ML pipeline](docs/ml/ml-pipeline.md) and [CERT integration](docs/ml/cert-integration.md).

## Security and prototype boundaries

- No arbitrary HTTPS payload interception; ALLOW / BLOCK enforcement requires a cooperating upload client.
- Completed filesystem actions are not reversed.
- Agents share a prototype key. JWT refresh and individual-token revocation are not implemented.
- Stored detection matches are masked and scanned text is discarded; metadata and resource identifiers still need privacy review before sharing.
- Non-local deployment requires TLS through the deployment/proxy configuration.
- Physical USB validation has not been recorded; synthetic USB events do not establish hardware validation.

See [security boundaries and dependency findings](docs/security/security.md). This is an academic prototype; risk scores express triage priorities, not probabilities of malicious intent.

## Documentation

- **Understand:** [architecture](docs/architecture/architecture.md), [database](docs/architecture/database.md), [API](docs/development/api.md), [repository history](docs/architecture/repository-audit.md)
- **Present:** [runbook](docs/fyp/fyp-demo-runbook.md), [demo script](docs/fyp/demo-script.md), [video script](docs/fyp/portfolio-video-script.md), [screenshots](docs/fyp/screenshots.md)
- **Defend:** [technical facts](docs/fyp/technical-facts.md), [20 defense questions](docs/fyp/defense-questions.md), [CV and portfolio copy](docs/fyp/portfolio-copy.md)
- **Operate:** [demo setup](docs/operations/demo.md), [USB procedure](docs/operations/usb-testing.md), [testing](docs/development/testing.md), [validation record](docs/fyp/pre-fyp-hardening-checklist.md)

## Project status

The structural baseline has 34 passing Python tests, 7 passing Jest tests, a successful production build, and [passing CI at structural commit 08712d2](https://github.com/sohaib-0897/DataShield/actions/runs/36196257681). One Playwright walkthrough passed in the last fully credentialed validation; the presentation pass did not rerun it because the existing password was unavailable. Alembic head remains `9e20ab47c132`.

Local benchmark measurements and their limits are recorded in the [technical fact sheet](docs/fyp/technical-facts.md). Presentation preparation does not activate a model or create a release tag.
