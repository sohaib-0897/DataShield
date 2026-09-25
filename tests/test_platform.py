"""Synthetic-only tests of normalized ingestion and analyst workflow."""
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

os.environ["DATASHIELD_JWT_SECRET"] = "test-only-jwt-secret-32-characters-long"
os.environ["DATASHIELD_AGENT_KEY"] = "test-only-agent-secret-32-characters-long"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pytest
import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.analysis import assess, behavior, classify, detections, features
from app.core import Base, now, password_hash, settings
from app.main import agent, app, db
from app.models import Alert, AuditLog, Event, InvalidEvent, User
from app.schemas import EventIn, PolicyConfig


@pytest.fixture
def client(monkeypatch):
    settings.cache_clear()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)
    import app.main as main_module
    monkeypatch.setattr(main_module, "SessionLocal", sessions)
    def local_db():
        with sessions() as session:
            yield session
    app.dependency_overrides[db] = local_db
    app.dependency_overrides[agent] = lambda: None
    with sessions.begin() as session:
        session.add(User(username="analyst", role="ANALYST", password_hash=password_hash.hash("test-password-long")))
        session.add(User(username="viewer", role="VIEWER", password_hash=password_hash.hash("test-password-long")))
        session.add(User(username="admin", role="ADMIN", password_hash=password_hash.hash("test-password-long")))
    with TestClient(app) as test_client:
        yield test_client, sessions
    app.dependency_overrides.clear()
    settings.cache_clear()
    engine.dispose()


def token(client, username):
    r = client.post("/api/v1/auth/login", json={"username": username, "password": "test-password-long"})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def event(id="synthetic-001"):
    return {"source_event_id": id, "username": "synthetic.employee", "machine_id": "SYNTHETIC-PC", "hostname": "synthetic-pc",
            "timestamp": datetime.now(timezone.utc).isoformat(), "channel": "UPLOAD", "event_type": "UPLOAD_ATTEMPT",
            "resource_id": "synthetic.txt", "metadata": {"filename": "synthetic.txt", "upload_id": "synthetic-upload", "sample_text": "12345-1234567-1", "synthetic": True}}


def test_pipeline_decision_audit_and_idempotency(client):
    http, sessions = client
    submitted = http.post("/api/v1/events", json=event())
    assert submitted.status_code == 200, submitted.text
    alert_id = submitted.json()["alert_id"]
    assert alert_id
    duplicate = http.post("/api/v1/events", json=event()).json()
    assert duplicate["duplicate"] is True
    assert duplicate["event_id"] == submitted.json()["event_id"]
    assert duplicate["alert_id"] == alert_id
    headers = token(http, "analyst")
    assert http.get("/api/v1/alerts?channel=UPLOAD&sort_by=risk_score&descending=false", headers=headers).json()["total"] == 1
    assert http.get("/api/v1/alerts?channel=USB", headers=headers).json()["total"] == 0
    assert http.get("/api/v1/alerts?search=synthetic.txt", headers=headers).json()["total"] == 1
    detail = http.get(f"/api/v1/alerts/{alert_id}", headers=headers).json()
    activity = http.get("/api/v1/users/activity", headers=headers).json()
    synthetic_user = next(row for row in activity if row["username"] == "synthetic.employee")
    assert synthetic_user["events"] == 1 and synthetic_user["alerts"] == 1
    assert synthetic_user["risk"] == detail["riskScore"]
    report = http.get("/api/v1/reports/summary", headers=headers).json()
    assert report["alerts"] == 1
    assert report["events"] == 1
    assert report["by_channel"] == {"UPLOAD": 1}
    assert report["by_status"] == {"OPEN": 1}
    assert report["by_severity"] == {detail["severity"].upper(): 1}
    assert report["risky_users"] == [{"user": "synthetic.employee", "risk": detail["riskScore"]}]
    assert sum(row["events"] for row in report["event_daily"]) == 1
    assert sum(row["alerts"] for row in report["daily"]) == 1
    assert report["risk_daily"][0]["average_risk"] == detail["riskScore"]
    assert report["event_daily"] and report["risk_daily"]
    assert report["alerts_with_sensitive_detections"] == 1
    assert report["decisions"].get("PENDING", 0) >= 1
    assert http.get("/api/v1/reports/export", headers=token(http, "viewer")).status_code == 403
    exported = http.get("/api/v1/reports/export", headers=headers)
    assert exported.status_code == 200 and exported.text.startswith("date,alerts")
    assert detail["classifierSource"] == "RULE"
    assert detail["anomalySource"] == "INSUFFICIENT_HISTORY"
    assert detail["riskBreakdown"]["contributions"]["sensitivity"] > 0
    assert "***" in str(detail["sensitiveMatches"])
    assert "12345-1234567-1" not in str(detail)
    viewer = token(http, "viewer")
    assert http.post(f"/api/v1/alerts/{alert_id}/decisions", headers=viewer, json={"action": "BLOCK"}).status_code == 403
    assert http.post(f"/api/v1/alerts/{alert_id}/decisions", headers=headers, json={"action": "BLOCK", "notes": "Synthetic case"}).status_code == 200
    assert http.get("/api/v1/reports/summary", headers=headers).json()["decisions"]["BLOCK"] == 1
    assert http.get("/api/v1/decisions/synthetic-upload").json()["decision"] == "block"
    with sessions() as session:
        assert session.scalar(select(Event).where(Event.source_event_id == "synthetic-001"))
        assert session.get(Alert, alert_id).status == "BLOCKED"
        assert session.scalar(select(AuditLog).where(AuditLog.action == "ALERT_DECISION"))
    old = now() - timedelta(days=40)
    with sessions.begin() as session:
        alert = session.get(Alert, alert_id)
        alert.created_at = old
        alert.event.received_at = old
        alert.risk.created_at = old
    ranged = http.get("/api/v1/reports/summary?days=7", headers=headers).json()
    assert ranged["alerts"] == ranged["events"] == ranged["alerts_with_sensitive_detections"] == 0
    assert ranged["by_severity"] == ranged["by_status"] == ranged["by_channel"] == ranged["decisions"] == {}
    assert ranged["daily"] == ranged["event_daily"] == ranged["risk_daily"] == ranged["risky_users"] == []


def test_batch_rejects_one_row_without_losing_other(client):
    http, _ = client
    bad = event("bad")
    bad["timestamp"] = "invalid"
    result = http.post("/api/v1/events/batch", json=[bad, event("good")])
    assert result.status_code == 200, result.text
    assert [x["status"] for x in result.json()["results"]] == ["invalid", "accepted"]


def test_low_risk_upload_is_auto_allowed_and_bad_artifact_does_not_stop_ingestion(client, monkeypatch):
    http, _ = client
    plain = event("plain-upload")
    plain["metadata"] = {"upload_id": "plain-upload-id", "filename": "ordinary.txt", "synthetic": True}
    result = http.post("/api/v1/events", json=plain)
    assert result.status_code == 200, result.text
    assert result.json()["alert_id"] is None
    decision = http.get("/api/v1/decisions/plain-upload-id").json()
    assert decision == {"decision": "allow", "source": "POLICY_AUTO_ALLOW", "alert_id": None}

    monkeypatch.setenv("DATASHIELD_ANOMALY_ARTIFACT", "missing-synthetic-artifact")
    anomalous = event("missing-artifact-event")
    anomalous["metadata"]["upload_id"] = "missing-artifact-upload"
    submitted = http.post("/api/v1/events", json=anomalous)
    assert submitted.status_code == 200, submitted.text
    detail = http.get(f"/api/v1/alerts/{submitted.json()['alert_id']}", headers=token(http, "analyst")).json()
    assert detail["anomalySource"] == "UNAVAILABLE"
    status = http.get("/api/v1/system/status", headers=token(http, "analyst"))
    assert status.status_code == 200
    assert status.json()["anomaly_model"] == "UNAVAILABLE"


def test_boundaries_and_auth(client):
    http, sessions = client
    assert http.get("/api/v1/alerts").status_code == 401
    assert http.post("/api/v1/auth/login", json={"username":"analyst","password":"wrong"}).status_code == 401
    agent_headers = {"X-Agent-Key": os.environ["DATASHIELD_AGENT_KEY"]}
    assert http.post("/api/v1/events", headers=agent_headers, json={**event(), "metadata": {"oversized": "x"*17000}}).status_code == 422
    assert http.post("/api/v1/events", headers=agent_headers, json={**event(), "timestamp": "2020-01-01"}).status_code == 422
    with sessions() as session:
        assert session.scalar(select(InvalidEvent).where(InvalidEvent.source_event_id == "synthetic-001"))
    assert http.post("/api/v1/endpoints/heartbeat", json={"machine_id":"FAKE-PC","hostname":"fake"}).status_code == 200
    app.dependency_overrides.pop(agent)
    assert http.post("/api/v1/events", json=event("no-key")).status_code == 401
    assert http.post("/api/v1/events", headers={"X-Agent-Key":"incorrect"}, json=event("wrong-key")).status_code == 401
    app.dependency_overrides[agent] = lambda: None
    assert http.post("/api/v1/users", headers=token(http, "viewer"), json={"username":"new.viewer","password":"another-long-password","role":"VIEWER"}).status_code == 403
    created = http.post("/api/v1/users", headers=token(http, "admin"), json={"username":"new.viewer","password":"another-long-password","role":"VIEWER"})
    assert created.status_code == 200
    assert http.post("/api/v1/auth/login", json={"username":"new.viewer","password":"another-long-password"}).status_code == 200


def test_inactive_users_and_expired_jwts_are_rejected(client):
    http, sessions = client
    with sessions.begin() as session:
        analyst_user = session.scalar(select(User).where(User.username == "analyst"))
        analyst_id = analyst_user.id
        session.add(User(username="inactive.user", role="ANALYST", active=False,
                         password_hash=password_hash.hash("test-password-long")))
    expired = jwt.encode({"sub": analyst_id, "exp": now() - timedelta(seconds=5)},
                         settings()["jwt_secret"], algorithm="HS256")
    assert http.get("/api/v1/alerts", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    assert http.post("/api/v1/auth/login", json={"username": "inactive.user", "password": "test-password-long"}).status_code == 401


def test_rules_features_and_behavior():
    assert detections("12345-1234567-1")[0]["masked"][0] != "12345-1234567-1"
    data = EventIn.model_validate(event())
    start = data.timestamp.replace(minute=0, second=0, microsecond=0)
    values = features([data], start, start + timedelta(hours=1))
    assert values["upload_count"] == 1
    assert values["unusual_extension_count"] == 0
    assert behavior(values, [1,1,1])["source"] == "HEURISTIC"
