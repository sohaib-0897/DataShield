# DataShield

DataShield is an academic data loss prevention and insider-risk prototype that turns endpoint and cooperating-client telemetry into explainable alerts for analysts.

## What DataShield Does

- Collects Windows endpoint telemetry for file and removable-media activity; network agents record connection metadata only.
- Accepts upload approval requests from cooperating clients. A block decision is enforced by those clients.
- Classifies sensitivity with bounded rules and stores masked detection evidence.
- Combines activity features with a behavioral analysis interface and explicitly labeled heuristic fallback.
- Produces explainable risk scores, evidence-backed alerts, analyst decisions, and audit records.
- Provides a React analyst dashboard backed by persistent PostgreSQL data, reports, and audit history.

## Current ML Status

No CERT dataset is included, and no trained behavior model is currently activated. Runtime behavior analysis is reported as HEURISTIC, INSUFFICIENT_HISTORY, or UNAVAILABLE unless a reviewed model is explicitly activated. No model-quality or detection-performance claims are made.

## Architecture

Windows agents and cooperating upload clients send telemetry to the FastAPI service. The service classifies and scores events, stores records in PostgreSQL, and exposes alerts and reports to the React dashboard. See [Architecture](docs/architecture/architecture.md) and [Database](docs/architecture/database.md).

## Repository Structure

    DataShield/
    ├── backend/       FastAPI application and Alembic migrations
    ├── frontend/      React dashboard and Playwright tests
    ├── agents/        Host-side filesystem, USB, upload, and network clients
    ├── ml/            Data preparation, model registry, and training tools
    ├── scripts/       Demo, migration, verification, and benchmark commands
    ├── tests/         Automated tests; manual hardware tests are isolated
    ├── docs/          Architecture, development, FYP, ML, operations, security
    ├── legacy/        Retained Flask and Windows-service code
    ├── docker-compose.yml
    └── README.md

The supported runtime is backend/app/. Code under legacy/ is retained for migration, regression testing, or historical reference and is not started by Compose.

## Quick Start

Use Docker Desktop and PowerShell from the repository root. Create a local environment file only if one does not already exist, then set distinct random values for DATASHIELD_JWT_SECRET, DATASHIELD_AGENT_KEY, and URL-safe DATASHIELD_DB_PASSWORD in that file.

    if (-not (Test-Path .env)) { Copy-Item .env.example .env }
    docker compose up --build -d
    docker compose ps
    Invoke-RestMethod http://localhost:8001/ready

The dashboard is at http://localhost:3001, the API at http://localhost:8001, and PostgreSQL is bound to local port 5434. Keep .env private; do not commit it.

## Demo

Set a unique synthetic demo password in the current PowerShell session, then seed the demo account and scenario:

    $env:DATASHIELD_DEMO_ADMIN_PASSWORD = 'choose-a-unique-password-of-at-least-12-characters'
    docker compose exec -T -e "DATASHIELD_DEMO_ADMIN_PASSWORD=$env:DATASHIELD_DEMO_ADMIN_PASSWORD" backend python scripts/demo/seed_demo.py

Sign in as demo.admin at http://localhost:3001. The seed creates synthetic events and sets that account's password. For the ordered workflow and recovery notes, see the [FYP demo runbook](docs/fyp/fyp-demo-runbook.md).

## Testing

From the repository root:

    .\.venv\Scripts\python.exe -m pytest -q

From frontend/ in PowerShell:

    $env:CI = 'true'
    npm test -- --watchAll=false
    Remove-Item Env:CI -ErrorAction SilentlyContinue
    npm run build

For the browser workflow, start and seed the demo, set DATASHIELD_FRONTEND_URL to http://localhost:3001 and DATASHIELD_DEMO_ADMIN_PASSWORD in the same shell, then run npm run test:e2e from frontend/.

## Security and Prototype Boundaries

DataShield is an academic prototype, not a production deployment. It does not inspect or intercept arbitrary HTTPS traffic. Upload blocking requires a cooperating client, and completed filesystem operations cannot be reversed. Agents currently share a prototype credential; use a deployment proxy with TLS for traffic outside the local development environment. See [Security](docs/security/security.md).

## ML and CERT Integration

The repository includes optional data preparation, training, evaluation safeguards, and model-registry code. No dataset is downloaded and training does not activate a model. Review [ML pipeline](docs/ml/ml-pipeline.md) and [CERT integration](docs/ml/cert-integration.md) before working with a licensed dataset.

## Documentation

- [API](docs/development/api.md) and [testing](docs/development/testing.md)
- [Architecture](docs/architecture/architecture.md), [database](docs/architecture/database.md), and [repository audit](docs/architecture/repository-audit.md)
- [Demo operations](docs/operations/demo.md), [USB test procedure](docs/operations/usb-testing.md), and [FYP runbook](docs/fyp/fyp-demo-runbook.md)
- [Pre-FYP hardening checklist](docs/fyp/pre-fyp-hardening-checklist.md) and [screenshots plan](docs/fyp/screenshots.md)
