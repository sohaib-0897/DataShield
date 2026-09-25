# CV and portfolio copy

## One-line portfolio version

Built DataShield, a Python/FastAPI, PostgreSQL, and React DLP prototype that turns Windows endpoint telemetry into explainable risk assessments, masked evidence, and audited analyst decisions.

## Two-bullet CV version

- Built a Docker Compose DLP prototype using Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, and React, with Watchdog/Windows endpoint collection and normalized event ingestion with duplicate handling.
- Implemented JWT/Argon2 authentication, role-based access, sensitivity rules, explicitly labeled behavior heuristics, weighted risk explanations, alert investigation, analyst decisions, and persistent audit/reporting.

## Longer project-page version

DataShield is an academic data loss prevention and insider-risk prototype focused on explaining why endpoint activity needs review. Python collectors observe file and removable-media activity, while cooperating clients submit upload approval requests. An optional network collector records browser connection metadata.

FastAPI validates normalized events and handles repeated delivery using stable source event IDs. SQLAlchemy and Alembic support PostgreSQL persistence for events, feature windows, risk assessments, alerts, evidence, and audit records. The React interface lets analysts filter alerts, inspect masked sensitivity findings and risk contributions, record decisions, and review activity reports. JWT sessions, Argon2 password hashing, and server-side roles separate administrative, analyst, and viewer access. Docker Compose and GitHub Actions support reproducible validation.

The demonstrated behavior analysis is heuristic. Candidate model training and registry infrastructure are present, but no trained behavior model is active and no authentic CERT evaluation is claimed. Upload blocking depends on a cooperating client; the system does not inspect arbitrary HTTPS payloads or reverse completed filesystem operations. Shared agent credentials and the absence of JWT refresh/revocation remain prototype limitations.

## GitHub About text

The presentation pass found no available `gh` executable, so metadata was not changed. Paste this exact description in the repository's About settings:

> AI-assisted multi-layer DLP and insider-risk prototype with FastAPI, PostgreSQL, React, Windows endpoint monitoring, explainable risk scoring, and evidence-backed alert investigation.

The current topics still include `flask`; replace that topic with `fastapi` when editing About. Suggested concise set: `data-loss-prevention`, `cybersecurity`, `insider-threat`, `fastapi`, `postgresql`, `react`, `docker`, `python`, `security-monitoring`.

Keep repository visibility, name, and default branch unchanged. Pair the copy with [reviewed synthetic screenshots](screenshots.md) and the [short video](portfolio-video-script.md) once captured.
