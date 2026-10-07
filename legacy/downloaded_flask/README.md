# Preserved downloaded Flask/SQLite application

These 19 Python/HTML files were copied byte-for-byte from the implementation at
`/home/sohaib/Downloads/AI-DLP-Agent`. Existing Git attributes normalize text to LF;
the manifest records original and normalized hashes. This application differs from both the
current FastAPI backend and the older SQLAlchemy Flask utilities in `legacy/flask`.
No upstream source files were replaced. See
`docs/implementation/phase0/source_reconciliation.json` for hashes and provenance.

The downloaded original remains intact, including its live database and policies.
Those files, environments, datasets, credentials, and sensitive documents were not
copied here. The current Compose runtime and migration history are unchanged.

This implementation is preserved for compatible DataShield enhancements. Do not
import `agent.py`: it initializes storage and starts a monitor at import time.
Run the isolated baseline from repository root instead:

```bash
python -B tests/phase0_regression.py --source-root legacy/downloaded_flask
```

Missing dependencies appear as skips and do not constitute complete verification.
Native Windows monitoring remains a separate validation requirement.

An explicit manual Flask launch is `python legacy/downloaded_flask/dashboard.py`
(localhost port 8000). The script creates its own new local `data/` storage when
run, rather than opening the downloaded original's files. It retains the original
Windows paths and monitor assumptions; inspect the audit before operating monitors.
Never start it alongside another service using port 8000, and never use its reset
route on live data. No monitor or dashboard server was launched during this audit.
