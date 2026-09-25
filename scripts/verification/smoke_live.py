"""Live synthetic API smoke test; set DATASHIELD_DEMO_ADMIN_PASSWORD."""
import os
import uuid
import time
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv


def main():
    load_dotenv()
    base = os.getenv("DATASHIELD_URL", "http://localhost:8000")
    password = os.environ["DATASHIELD_DEMO_ADMIN_PASSWORD"]
    session = httpx.Client(timeout=5)
    for attempt in range(20):
        try:
            if session.get(base + "/ready").json()["status"] == "ready":
                break
        except httpx.HTTPError:
            pass
        time.sleep(1)
    else:
        raise RuntimeError("Backend did not become ready within 20 seconds")
    response = session.post(base + "/api/v1/auth/login", json={"username": "demo.admin", "password": password})
    response.raise_for_status()
    session.headers["Authorization"] = "Bearer " + response.json()["access_token"]
    agent_headers = {"X-Agent-Key": os.environ["DATASHIELD_AGENT_KEY"]}
    payload = {"source_event_id": "synthetic-smoke-" + str(uuid.uuid4()), "username": "synthetic.employee", "machine_id": "SYNTHETIC-ENDPOINT-001",
               "hostname": "synthetic-workstation", "timestamp": datetime.now(timezone.utc).isoformat(), "channel": "UPLOAD",
               "event_type": "UPLOAD_ATTEMPT", "resource_id": "synthetic-smoke.txt",
               "metadata": {"filename": "synthetic-smoke.txt", "sample_text": "Synthetic CNIC 12345-1234567-1", "synthetic": True}}
    submitted = session.post(base + "/api/v1/events", json=payload, headers=agent_headers)
    submitted.raise_for_status()
    assert submitted.json()["alert_id"]
    duplicate = session.post(base + "/api/v1/events", json=payload, headers=agent_headers)
    duplicate.raise_for_status()
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["event_id"] == submitted.json()["event_id"]
    assert duplicate.json()["alert_id"] == submitted.json()["alert_id"]
    report = session.get(base + "/api/v1/reports/summary")
    report.raise_for_status()
    assert report.json()["events"] >= 6
    alerts = session.get(base + "/api/v1/alerts")
    alerts.raise_for_status()
    assert alerts.json()["total"] >= 1
    target = alerts.json()["items"][0]["id"]
    detail = session.get(base + "/api/v1/alerts/" + target)
    detail.raise_for_status()
    assert detail.json()["riskBreakdown"]["contributions"]
    assert detail.json()["anomalySource"] == "HEURISTIC"
    assert detail.json()["classifierSource"] == "RULE"
    assert any(row["type"] == "DETECTIONS" for row in detail.json()["evidence"])
    assert "12345-1234567-1" not in str(detail.json()["evidence"])
    decision = session.post(base + "/api/v1/alerts/" + target + "/decisions", json={"action": "BLOCK", "notes": "Synthetic smoke test"})
    decision.raise_for_status()
    assert decision.json()["status"] == "BLOCKED"
    logs = session.get(base + "/api/v1/audit")
    logs.raise_for_status()
    assert any(row["entity_id"] == target and row["action"] == "ALERT_DECISION" for row in logs.json())
    session.close()
    print(f"ready, login, ingestion, duplicate, {report.json()['events']} events, {alerts.json()['total']} alerts, evidence, decision, audit: PASS")


if __name__ == "__main__": main()
