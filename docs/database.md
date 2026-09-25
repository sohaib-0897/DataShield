# PostgreSQL development database

`docker compose up -d db` starts PostgreSQL on local port 5434 with a persistent named volume. For local Python, set `DATABASE_URL=postgresql+psycopg://datashield:datashield_local_only@localhost:5434/datashield` in ignored `.env`. Then run `python -m alembic upgrade head` before starting FastAPI. The backend Docker service runs migrations automatically at startup.

The initial migration preserves original Flask tables. The second migration creates UUID keyed normalized DataShield tables for users, endpoints, events, invalid diagnostics, documents, feature windows, risk assessments, alerts, evidence, policies, audit logs, and model versions. New API routes use the normalized tables. Do not run the legacy Flask server as the primary API.

Use `python -m alembic current` to inspect the revision. `docker compose restart backend` keeps events and decisions in PostgreSQL. Local unit tests use SQLite isolation; CI also applies Alembic to PostgreSQL.

For an existing database containing original Flask alerts, run `python scripts/migrate_legacy.py` after migrations. The command copies alerts idempotently, marks historic risk unassessed, masks old matches, and leaves old tables available for review.
