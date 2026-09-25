"""Create a local admin and pass clearly synthetic events through the real pipeline."""
import os
import sys
from datetime import timedelta
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.core import SessionLocal, now, password_hash, require_secrets
from app.main import ingest_one
from app.models import AuditLog, Event, RiskAssessment, User
from app.schemas import EventIn


def main():
    require_secrets()
    password = os.getenv("DATASHIELD_DEMO_ADMIN_PASSWORD")
    if not password or len(password) < 12:
        raise SystemExit("Set DATASHIELD_DEMO_ADMIN_PASSWORD to at least 12 characters")
    with SessionLocal() as session:
        admin = session.scalar(select(User).where(User.username == "demo.admin"))
        if admin is None:
            admin = User(username="demo.admin", email="demo.admin@example.invalid", role="ADMIN", password_hash=password_hash.hash(password))
            session.add(admin)
        else:
            admin.password_hash = password_hash.hash(password)
            admin.active = True
        session.flush()
        session.add(AuditLog(action="DEMO_ADMIN_SEEDED", entity_type="user", entity_id=admin.id, details={"source": "seed_demo"}))
        session.commit()
    scenarios = [
        ("FILE", "FILE_CREATE", "synthetic-normal-1.txt", {"filename": "synthetic-normal-1.txt", "synthetic": True}, timedelta(hours=6)),
        ("FILE", "FILE_MODIFY", "synthetic-normal-2.txt", {"filename": "synthetic-normal-2.txt", "synthetic": True}, timedelta(hours=4)),
        ("FILE", "FILE_CREATE", "synthetic-normal-3.txt", {"filename": "synthetic-normal-3.txt", "synthetic": True}, timedelta(hours=2)),
        ("FILE", "FILE_CREATE", "synthetic-sensitive.txt", {"filename": "synthetic-sensitive.txt", "sample_text": "Synthetic CNIC 12345-1234567-1", "synthetic": True}, timedelta(minutes=4)),
        ("USB", "USB_INSERT", "E:", {"device_id": "SYNTHETIC-USB", "synthetic": True}, timedelta(minutes=3)),
        ("USB", "USB_FILE_TRANSFER", "synthetic-sensitive.txt", {"sample_text": "Synthetic CNIC 12345-1234567-1", "synthetic": True}, timedelta(minutes=2)),
        ("UPLOAD", "UPLOAD_ATTEMPT", "synthetic-sensitive.txt", {"filename": "synthetic-sensitive.txt", "upload_id": "synthetic-upload-v2", "sample_text": "Synthetic CNIC 12345-1234567-1", "synthetic": True}, timedelta(minutes=1)),
    ]
    with SessionLocal() as session:
        scenario_alerts = 0
        for index, (channel, kind, resource, metadata, age) in enumerate(scenarios):
            data = EventIn(source_event_id=f"synthetic-demo-v2-{index}", username="synthetic.employee", machine_id="SYNTHETIC-ENDPOINT-001",
                           hostname="synthetic-workstation", timestamp=now() - age, channel=channel,
                           event_type=kind, resource_id=resource, metadata=metadata, source="synthetic-demo")
            result = ingest_one(session, data)
            scenario_alerts += bool(result.get("alert_id"))
            print(f"{kind:<20} {'duplicate' if result['duplicate'] else 'created':<10} {'alert ' + result['alert_id'] if result.get('alert_id') else 'no alert'}")
        session.commit()
    with SessionLocal() as session:
        latest_explanation = session.scalar(
            select(RiskAssessment.explanation)
            .join(Event, RiskAssessment.event_id == Event.id)
            .where(Event.source_event_id.like("synthetic-demo-v2-%"))
            .order_by(Event.timestamp.desc())
            .limit(1)
        ) or {}
    behavior_source = latest_explanation.get("anomaly_source", "UNAVAILABLE")
    print("\nDemo scenario ready\n-------------------")
    print(f"Synthetic events: {len(scenarios)}")
    print(f"Alerts in scenario: {scenario_alerts}")
    print("Behavior source: HEURISTIC (deterministic demo rule; not a trained model)" if behavior_source == "HEURISTIC" else f"Behavior source: {behavior_source}")
    print("Login user: demo.admin")
    print("Dashboard: http://localhost:3001")


if __name__ == "__main__": main()
