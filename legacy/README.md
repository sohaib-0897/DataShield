# Retained legacy code

The supported runtime is the FastAPI application in `backend/app/`. Nothing under
this directory is started by Docker Compose.

- `flask/` keeps the former Flask API, test upload server, original SQLAlchemy
  schema, and development seed. The original schema is still registered by
  Alembic and is read by `scripts/migration/migrate_legacy.py`; migration tests
  also exercise the retained Flask routes.
- `windows/` keeps the former Windows service, deployment helper, and monitoring
  utilities. These are historical and are not the supported host agents; use
  `agents/` for the current module entry points.
