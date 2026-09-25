# FYP demonstration runbook

## Pre-demo

From the repository root, set three different random values in ignored `.env`: `DATASHIELD_JWT_SECRET` and `DATASHIELD_AGENT_KEY` (at least 32 characters each), plus a 32-character URL-safe `DATASHIELD_DB_PASSWORD`. Do not use a shared/repository default.

```powershell
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://localhost:8001/ready
curl.exe -L --fail --silent --output NUL --write-out "%{http_code}" http://localhost:3001
$env:DATASHIELD_DEMO_ADMIN_PASSWORD = 'choose-a-unique-password-of-at-least-12-characters'
docker compose exec -T -e "DATASHIELD_DEMO_ADMIN_PASSWORD=$env:DATASHIELD_DEMO_ADMIN_PASSWORD" backend python scripts/demo/seed_demo.py
```

Sign in at <http://localhost:3001> as `demo.admin` with that password. The seed is synthetic and idempotent. For a clean scenario, set `DATASHIELD_DEMO_ADMIN_PASSWORD` and run `./scripts/demo/reset_demo.ps1` from PowerShell. It prompts for `RESET LOCAL DATASHIELD`, removes this checkout's Compose database volume, rebuilds, waits for `/ready` (startup applies Alembic migrations), and seeds. This deletes the local Compose database volume contents. Do not point this Compose project at a shared or production database.

## Demo order

1. Explain the overview as stored PostgreSQL counts.
2. Show the endpoint status page and event activity.
3. Show the three earlier synthetic normal events.
4. Show the sensitive synthetic file, USB insertion/transfer, and cooperating upload events.
5. Open the resulting alert from Alerts.
6. Explain the score using the displayed risk factor contributions and policy threshold.
7. State clearly: sensitivity is `RULE` pattern/declared classification; behavior says `HEURISTIC` after enough history or `INSUFFICIENT_HISTORY`. No trained model is supplied.
8. Inspect event metadata, masked detections, evidence and timeline.
9. Add a note and choose Investigate, Allow, Block, Dismiss, or Resolve. Block affects cooperating upload clients only.
10. Show the alert decision and audit trail.
11. Show Reports and its selected date range.
12. Briefly show System/Model status and the feature schema.

## Recovery

- Docker unhealthy: `docker compose ps`, `docker compose logs db backend`.
- Migration failure: `docker compose logs backend`; correct the reported DB/config issue, then `docker compose up -d backend` (startup runs Alembic before serving).
- Port conflict: stop the local process using 5434, 8001, or 3001, or edit Compose port mappings and restart.
- Wrong password: rerun `scripts/demo/seed_demo.py` with `DATASHIELD_DEMO_ADMIN_PASSWORD` set; it resets only `demo.admin`'s password.
- Stale demo: use the clean scenario reset above. It erases the Compose database volume.
- Frontend cannot reach API: check <http://localhost:8001/ready>, the browser console, and `REACT_APP_API_URL`; the Docker frontend expects the host API at port 8001.

## Supervisor questions

- **Where is the AI?** The repository includes optional IsolationForest training and artifact loading infrastructure. No trained model is active in this demo.
- **Why is the model inactive?** The CERT data and reviewed model artifact are unavailable; enabling an unvalidated model would be misleading.
- **What dataset will be used?** The future workflow accepts licensed CERT Insider Threat CSVs through the documented adapter; schema and timestamps must be checked against the specific release.
- **What does the anomaly model learn?** Candidate IsolationForest learns patterns in hourly per-user behavior feature vectors; it does not produce calibrated probabilities.
- **How is risk calculated?** A validated weighted sum of anomaly, sensitivity, activity, channel and bounded historical-risk components, then configurable severity and alert thresholds.
- **How will false positives be reduced?** Evaluate with authentic held-out data, tune reviewed policies, inspect explanations, and measure operational false-positive rates before claiming improvement.
- **Can it block HTTPS uploads?** No. It observes limited browser connection metadata. Blocking is available only to a cooperating upload client.
- **Can file operations be reversed?** No. The system records and triages observed activity; it cannot reverse completed local operations.
- **Why PostgreSQL?** It provides durable relational records, constraints, indexed filters, JSON metadata, and multi-user persistence.
- **Why FastAPI?** It offers typed request validation, generated API documentation, and a clear API boundary for agents and the React client.
- **How is sensitive content protected?** Only bounded text is inspected transiently; stored event metadata is allowlisted and detections are masked. Use TLS for non-local traffic.
- **What happens when the model fails?** An unavailable/incompatible artifact is labeled `UNAVAILABLE`; ingestion continues and does not claim a heuristic result for that event.
- **How is this different from rule-based DLP?** Current sensitivity and fallback behavior are explicitly rule based. The architecture can host a reviewed behavioral model later, but this is not a demonstrated trained-model result.
