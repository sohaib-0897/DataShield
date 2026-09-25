"""The synthetic scenario must create a real heuristic assessment and alert."""
import sys
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core import Base
from app.models import Alert, Evidence, Event, RiskAssessment, User
from scripts import seed_demo


def test_seed_demo_uses_pipeline_and_is_idempotent(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(seed_demo, "SessionLocal", sessions)
    monkeypatch.setenv("DATASHIELD_DEMO_ADMIN_PASSWORD", "synthetic-demo-test-password")
    monkeypatch.delenv("DATASHIELD_ANOMALY_ARTIFACT", raising=False)
    seed_demo.main()
    seed_demo.main()
    with sessions() as session:
        assert session.scalar(select(func.count(Event.id))) == 7
        assert session.scalar(select(func.count(Alert.id))) >= 1
        assert session.scalar(select(RiskAssessment).where(RiskAssessment.explanation["anomaly_source"].as_string() == "HEURISTIC"))
        detections = session.scalars(select(Evidence).where(Evidence.evidence_type == "DETECTIONS")).all()
        assert detections
        assert all("12345-1234567-1" not in str(row.value) for row in detections)


def test_sensitive_alert_report_counts_alerts_not_detection_rows(monkeypatch):
    """Two DETECTIONS rows attached to one alert contribute one alert to the report."""
    from fastapi.testclient import TestClient
    from app.core import token_for
    from app.main import app
    import app.main as api

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)
    original = api.SessionLocal
    api.SessionLocal = sessions
    try:
        monkeypatch.setenv("DATASHIELD_JWT_SECRET", "test-jwt-secret-at-least-32-characters")
        monkeypatch.setenv("DATASHIELD_AGENT_KEY", "test-agent-key-at-least-32-characters")
        monkeypatch.setenv("DATASHIELD_DEMO_ADMIN_PASSWORD", "synthetic-demo-test-password")
        from app.core import settings
        settings.cache_clear()
        monkeypatch.setattr(seed_demo, "SessionLocal", sessions)
        monkeypatch.delenv("DATASHIELD_ANOMALY_ARTIFACT", raising=False)
        seed_demo.main()
        with sessions.begin() as session:
            expected = session.scalar(select(func.count(func.distinct(Evidence.alert_id))).where(Evidence.evidence_type == "DETECTIONS"))
            alert = session.scalar(select(Alert).join(Evidence, Evidence.alert_id == Alert.id)
                                   .where(Evidence.evidence_type == "DETECTIONS").limit(1))
            assert alert is not None
            session.add(Evidence(alert_id=alert.id, event_id=alert.event_id, evidence_type="DETECTIONS",
                                 value={"detections": [{"type": "EMAIL"}]}))
            admin = session.scalar(select(User).where(User.username == "demo.admin"))
            token = token_for(admin)
        with TestClient(app) as client:
            response = client.get("/api/v1/reports/summary", headers={"Authorization": "Bearer " + token}, params={"days": 30})
            assert response.status_code == 200
            assert response.json()["alerts_with_sensitive_detections"] == expected
    finally:
        api.SessionLocal = original
        settings.cache_clear()
        engine.dispose()
