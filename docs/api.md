# API

OpenAPI is at `/docs`; `/health` and `/ready` are public. Interactive routes require `Authorization: Bearer <JWT>`. Agent routes use `X-Agent-Key`.

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/login` | Public | Login |
| GET | `/api/v1/auth/me` | User | Current identity |
| POST | `/api/v1/events` | Agent | One event |
| POST | `/api/v1/events/batch` | Agent | Up to 100 independently validated events |
| GET | `/api/v1/events` | User | Paginated events |
| POST | `/api/v1/endpoints/heartbeat` | Agent | Update last seen |
| GET | `/api/v1/alerts` | User | Filtered, paginated alerts |
| GET | `/api/v1/alerts/{id}` | User | Evidence and risk breakdown |
| POST | `/api/v1/alerts/{id}/decisions` | Analyst/Admin | Decision and notes |
| GET | `/api/v1/decisions/{upload_id}` | Agent | Upload polling; below-threshold attempts return `allow` with `source: POLICY_AUTO_ALLOW`, alerts await an analyst |
| GET | `/api/v1/reports/summary` | User | Stored analytics |
| GET | `/api/v1/reports/export` | Analyst/Admin | Audited daily CSV export |
| GET | `/api/v1/users/activity` | User | Per user counts |
| GET | `/api/v1/users/{id}/timeline` | User | Recent events and risk trend |
| GET/PUT | `/api/v1/policies` | User/Admin | Policy |
| GET | `/api/v1/system/status` | User | Database, model, endpoint status |
| GET | `/api/v1/audit` | Admin | Audit actions |
| POST | `/api/v1/users` | Admin | Create interactive user |
| GET/POST | `/api/v1/models` | Admin | List/register local artifacts |
| POST | `/api/v1/models/{id}/activate` | Admin | Activate compatible non-test artifact |

Events require `source_event_id`, `username`, `machine_id`, `hostname`, timezone aware `timestamp`, `channel`, and upper case `event_type`. Channels: `FILE`, `USB`, `CLOUD`, `UPLOAD`, `NETWORK`. Metadata limit: 16 KiB. A malformed batch item yields `invalid` and a diagnostic row; other items continue. Authenticated invalid single events return 422 and create a bounded diagnostic row. Duplicate source IDs return `duplicate: true`.

Alert listing supports `search`, `status`, `severity`, `channel`, `user`, `start`, `end`, `sort_by`, `descending`, `page`, and `size`. Report summary accepts `days=1..365` and returns real alert, event, and average risk daily aggregates, breakdowns, risky users, and a count of alerts with sensitive detections.
