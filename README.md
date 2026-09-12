# DataShield

**A Windows-focused data loss prevention prototype with a React analyst dashboard and Python monitoring agents.**

DataShield brings file activity alerts, sensitive-content previews, and upload approval decisions into one review workflow. Built as a final-year project, it demonstrates endpoint monitoring, REST API integration, and an investigation interface.

[Architecture](docs/architecture.md) · [Demo walkthrough](docs/demo.md) · [Development](CONTRIBUTING.md)

## What works

- Monitor file creation, modification, movement, and deletion with a Watchdog-based desktop agent.
- Detect CNIC-shaped identifiers using regular expressions and highlight matches in previews.
- Send alerts to a Flask API and review them in React alert and investigation pages.
- Record allow/block decisions and expose them to cooperating upload clients through polling.
- Explore dashboard, user activity, and report views built with Tailwind CSS and Recharts.

**Project status:** a local demonstration prototype. Alert ingestion and decisions use live API state; user activity and reporting endpoints return sample data. Risk scores are fixed or rule-based. No trained AI model is included. The monitoring scripts do not establish tamper resistance or universal HTTP/HTTPS upload interception.

## Stack

| Layer | Technologies |
| --- | --- |
| Dashboard | React 18, React Router, Axios, Tailwind CSS, Recharts |
| API | Python, Flask, Flask-Cors |
| Endpoint agents | Watchdog, psutil, Tkinter, Windows service scripts |
| Validation | pytest API tests, React production build, GitHub Actions |

## Quick start

Use Python 3.11+ and Node.js 22. Windows is required for the service and deployment scripts; the API and dashboard can run separately on other platforms. Run the following from the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
$env:DATASHIELD_API_KEY = 'replace-with-your-local-demo-key'
python backend/admin_server.py
```

In another terminal:

```powershell
cd frontend
Copy-Item .env.example .env
# Set REACT_APP_API_KEY in .env to the same value as DATASHIELD_API_KEY.
npm ci
npm start
```

Open **http://localhost:3000**. The API and legacy admin page run at **http://127.0.0.1:5000**. Restart the frontend after changing its environment file.

Follow the [synthetic demo](docs/demo.md) to generate an alert without starting endpoint monitors. To explore desktop monitoring on Windows, activate the virtual environment, set the same `DATASHIELD_API_KEY`, and run `python backend/upload_monitor_agent.py`. The GUI starts monitoring when you click **Start Monitoring**.

## Repository layout

```text
DataShield/
├── backend/                # Flask API, endpoint agents, Windows utilities
├── frontend/               # React application and dependency lockfile
├── tests/                  # Isolated API regression tests
│   └── manual/             # Original scripts requiring running services
├── docs/                   # Architecture and reproducible demo
├── .github/workflows/      # Automated API tests and frontend build
├── requirements-dev.txt
└── start_dlp_system.bat    # Optional Windows multi-component launcher
```

## Validation

```powershell
python -m pytest -q
cd frontend
npm run build
```

Automated tests exercise authentication, alert ingestion, decision polling, and sensitive preview escaping without monitoring personal folders. Original manual scripts are excluded from pytest discovery because they require running services and may create files in user directories.

## Engineering boundaries and next steps

- State is held in memory and resets when the API restarts. Persistent storage and durable audit records are future work.
- Some legacy admin routes lack authentication. The API binds to loopback by default; use synthetic data locally. Browser API keys are visible in the bundle and are not a production authentication solution.
- File activity decisions record analyst intent; they do not reverse completed filesystem operations. Enforcement depends on a cooperating client.
- Production work would include consistent authorization, validated payloads, unique IDs across alert types, restricted preview access, hardened CORS/CSP, and a supported deployment model.
- Reports and user analytics need real event aggregation before their sample values can be interpreted as measurements.

These boundaries are documented so reviewers can distinguish implemented behavior from the project's planned direction.
