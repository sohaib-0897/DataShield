"""Cooperating upload client approval contract, not universal browser interception."""
import os
import time
import uuid
from pathlib import Path

import requests

from .common import event, send


def request_approval(path, destination, timeout=60):
    upload_id = str(uuid.uuid4())
    file = Path(path)
    payload = event("UPLOAD", "UPLOAD_ATTEMPT", file.name, {"upload_id": upload_id, "filename": file.name,
                      "extension": file.suffix.lower(), "size": file.stat().st_size, "destination": destination})
    result = send(payload)
    base = os.getenv("DATASHIELD_URL", "http://127.0.0.1:8000")
    headers = {"X-Agent-Key": os.environ["DATASHIELD_AGENT_KEY"]}
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        response = requests.get(base + "/api/v1/decisions/" + upload_id, headers=headers, timeout=5)
        response.raise_for_status()
        decision_result = response.json()
        decision = decision_result["decision"]
        if decision in ("allow", "block"):
            return {"decision": decision, "source": decision_result["source"], "event_id": result["event_id"], "alert_id": result["alert_id"]}
        time.sleep(2)
    return {"decision": "timeout", "event_id": result["event_id"], "alert_id": result["alert_id"]}
