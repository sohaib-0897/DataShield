# Testing

`python -m pytest -q` runs regression and synthetic pipeline tests. Tests use isolated SQLite databases (in-memory and test-specific files) and never scan personal folders. They cover ingestion, idempotency, masking, risk, RBAC, JWT/inactive-user boundaries, decisions, audit records, malformed batches, reporting, and model artifact guards.

Run `npm test -- --watchAll=false` and `npm run build` in `frontend`. An optional browser walkthrough uses Playwright: install the Chromium browser with `npx playwright install chromium`, use the existing validated demo stack/account (or seed only a new disposable installation), set `DATASHIELD_FRONTEND_URL` and the existing `DATASHIELD_DEMO_ADMIN_PASSWORD`, then run `npm run test:e2e`. The E2E check requires running services and performs a BLOCK decision on the seeded demo alert.

Docker Compose is the PostgreSQL/migration integration path. For a planned persistence check, use existing synthetic records, restart the backend container with the same Compose project/volume configuration, and query those records with a valid JWT. A documentation pass does not require this restart. Local browser walkthroughs can use another disposable database, but they do not replace PostgreSQL validation. No CERT quality metrics are claimed.
