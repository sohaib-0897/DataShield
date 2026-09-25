# Testing

`python -m pytest -q` runs regression and synthetic pipeline tests. Tests use isolated in-memory SQLite and never scan personal folders. They cover ingestion, idempotency, masking, risk, RBAC, JWT/inactive-user boundaries, decisions, audit records, malformed batches, reporting, and model artifact guards.

Run `npm test -- --watchAll=false` and `npm run build` in `frontend`. An optional browser walkthrough uses Playwright: install the Chromium browser with `npx playwright install chromium`, start the demo stack, seed it, set `DATASHIELD_FRONTEND_URL` and `DATASHIELD_DEMO_ADMIN_PASSWORD`, then run `npm run test:e2e`. The E2E check requires running services and performs a BLOCK decision on the seeded demo alert.

Docker Compose is the PostgreSQL/migration integration path. To check persistence, seed the demo, restart the backend container, and query alerts with a valid JWT. Local browser walkthroughs can use another disposable database, but they do not replace PostgreSQL validation. No CERT quality metrics are claimed.
