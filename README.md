# DataShield

**AI-Assisted Multi-Layer Data Loss Prevention & Insider Risk Prototype**

DataShield is an academic security operations prototype. Windows host agents and cooperating clients submit file, removable-media, and upload-attempt telemetry to a normalized FastAPI pipeline backed by PostgreSQL. Sensitivity rules, feature windows, and explicitly labeled heuristic behavior analysis contribute to explainable risk scores and evidence-backed alerts for the React analyst dashboard.

| Implemented | Awaiting real dataset |
| --- | --- |
| ✓ Multi-channel monitoring and event ingestion | ○ CERT-trained anomaly model |
| ✓ Sensitivity rules and feature engineering | ○ Authentic ML evaluation |
| ✓ Heuristic behavior analysis and explainable risk scoring | |
| ✓ Evidence-backed alert investigation, RBAC, and audit logging | |
| ✓ PostgreSQL-backed reporting | |

**Release:** `0.9.0-pre-cert`. This is not a production deployment. The current behavior source is a deterministic heuristic or insufficient history; no trained model performance is claimed. See the [demo runbook](docs/fyp-demo-runbook.md).

## Status

Implemented: persistent normalized events, idempotency, batch validation, bounded sensitive pattern scanning, feature windows, explained risk scores, threshold alerts, evidence, analyst actions, audit logs, database reports, agent heartbeats, role based access, and synthetic demo seeding.

No CERT data or trained model is included. Behavior results are `INSUFFICIENT_HISTORY` or a deterministic `HEURISTIC` based on prior event counts; a configured artifact failure returns `UNAVAILABLE`. Document classification is `RULE`, `DECLARED`, or `UNAVAILABLE`. Optional candidate IsolationForest training machinery is provided; no detection quality has been measured. Cooperating uploads below the alert threshold are automatically allowed by policy; escalated uploads wait for an analyst's allow/block decision. `BLOCK` is enforced only by cooperating upload clients. Completed file operations cannot be reversed. Legacy psutil/network scripts are retired because connection metadata cannot establish that an HTTPS upload happened.

## Docker launch

Use Docker Desktop. From this directory:

```powershell
Copy-Item .env.example .env
# Set both API secrets and DATASHIELD_DB_PASSWORD to distinct random values (DB password URL-safe; at least 32 characters).
docker compose up --build -d
docker compose exec -e DATASHIELD_DEMO_ADMIN_PASSWORD=choose-a-long-demo-password backend python scripts/seed_demo.py
```

Visit <http://localhost:3001>; sign in as `demo.admin` with the supplied password. API: <http://localhost:8001>. OpenAPI: <http://localhost:8001/docs>. PostgreSQL: local port 5434. Docker ports bind to localhost. The seed command passes seven clearly synthetic events through the real pipeline, with normal activity in three earlier windows followed by sensitive file, USB, and upload activity. It is idempotent for events; each run sets the demo admin password to the supplied value.

For a repeatable clean demo, set `$env:DATASHIELD_DEMO_ADMIN_PASSWORD` to a unique value of at least 12 characters and run `./scripts/reset_demo.ps1`; type `RESET LOCAL DATASHIELD` when prompted. It deletes this checkout's local Compose database volume, rebuilds/migrates, then seeds. It is not for a shared or production database.

## Local development

Use Python 3.11+, Node.js, and PostgreSQL. Run `docker compose up -d db`, then:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
# Set DATABASE_URL to postgresql+psycopg://datashield:<DATASHIELD_DB_PASSWORD>@localhost:5434/datashield; set all three secrets.
.\.venv\Scripts\python.exe -m alembic upgrade head
$env:DATASHIELD_DEMO_ADMIN_PASSWORD='choose-a-long-demo-password'
.\.venv\Scripts\python.exe scripts/seed_demo.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

In another shell, copy `frontend/.env.example` to `frontend/.env`, run `npm ci` and `npm start` in `frontend`. For the local frontend on port 3000, set `DATASHIELD_FRONTEND_ORIGIN=http://localhost:3000` in the root `.env`.

Host agents run outside Docker. Install them with `python -m pip install -r requirements-agents.txt`. Set `DATASHIELD_AGENT_KEY` to the root secret and, for Docker, `DATASHIELD_URL=http://localhost:8001` (local development uses port 8000). Set `DATASHIELD_MONITOR_FOLDERS` to explicit paths separated by the OS path separator, then run `python -m agents.filesystem`. Windows USB events use `python -m agents.usb`. A cooperating client calls `agents.upload.request_approval(path, destination)` before transferring. Tests never scan user folders.

Optional `python -m agents.network` records new browser TCP connections to ports 80/443 as `NETWORK_CONNECTION` metadata. It does not inspect HTTPS content or infer an upload.

## Dataset and training

No dataset is downloaded. Put licensed CERT style CSVs in `ml/data/raw/` and run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
.\.venv\Scripts\python.exe -m ml.training.prepare_dataset --input ml/data/raw --output ml/data/prepared/events.jsonl
.\.venv\Scripts\python.exe -m ml.training.train_anomaly --dataset ml/data/prepared/events.jsonl --output ml/artifacts/anomaly/candidate-v1 --real-dataset
```

Review source mapping, fingerprint, time splitting, and evaluation before activating a candidate. Synthetic training runs must use `--synthetic-test`; candidate activation requires a distinct held-out dataset fingerprint and reviewed labeled evaluation metrics. Training never activates a candidate. Follow the explicit [CERT handoff](docs/cert-integration.md).

## Verification and layout

Run `.\.venv\Scripts\python.exe -m pytest -q`, `npm test -- --watchAll=false` (with `CI=true`), and `npm run build` inside `frontend`. For browser E2E, start/seed the demo, install Chromium with `npx playwright install chromium`, set `DATASHIELD_FRONTEND_URL=http://localhost:3001` and `DATASHIELD_DEMO_ADMIN_PASSWORD`, then run `npm run test:e2e` in `frontend`. Run `.\.venv\Scripts\python.exe -m pip_audit` and `npm audit --omit=dev` in `frontend` for security checks. FastAPI in `backend/app/` is the supported runtime; Alembic applies a retained legacy schema migration followed by the normalized platform migration. Flask files remain only for migration/history and are not started by Docker or the React UI.

For a local PostgreSQL performance run, start Compose and run `docker compose exec -T backend python scripts/benchmark_alerts.py`. It creates 10,000 tagged synthetic benchmark alerts and writes measured API timings and container context to ignored `artifacts/benchmarks/latest.json`, then deletes those tagged rows. See [the demonstration runbook](docs/fyp-demo-runbook.md) for the ordered walkthrough and recovery steps.

See [architecture](docs/architecture.md), [API](docs/api.md), [demo](docs/demo.md), [ML pipeline](docs/ml-pipeline.md), [CERT integration](docs/cert-integration.md), [security](docs/security.md), and [testing](docs/testing.md).
