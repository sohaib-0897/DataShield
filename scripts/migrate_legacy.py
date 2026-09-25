"""Copy historical Flask alerts into UUID keyed tables without raw previews."""
import sys
import uuid
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.core import SessionLocal, now
from app.models import Alert, AuditLog, Event, Evidence, RiskAssessment, User
from models import Alert as OldAlert, AnalystDecision, User as OldUser


NAMESPACE = uuid.UUID("82b5f35f-09cd-46cc-b44d-a93980a05e42")


def stable(kind, old_id):
    return str(uuid.uuid5(NAMESPACE, f"legacy-{kind}-{old_id}"))


def main():
    copied = 0
    with SessionLocal() as session:
        for old in session.scalars(select(OldAlert).order_by(OldAlert.id)).all():
            alert_id = stable("alert", old.id)
            if session.get(Alert, alert_id):
                continue
            event_old = old.event
            old_user = session.get(OldUser, event_old.user_id) if event_old.user_id else None
            username = old_user.name if old_user else "legacy.unknown"
            user = session.scalar(select(User).where(User.username == username))
            if user is None:
                user = User(username=username, role="VIEWER")
                session.add(user)
                session.flush()
            payload = event_old.payload or {}
            resource = payload.get("file_path") or payload.get("filename")
            try:
                from datetime import datetime, timezone
                timestamp = datetime.fromisoformat(event_old.timestamp.replace("Z", "+00:00"))
                if timestamp.tzinfo is None: timestamp = timestamp.replace(tzinfo=timezone.utc)
            except ValueError:
                timestamp = now()
            channel = "UPLOAD" if event_old.kind == "upload" else "FILE"
            event = Event(id=stable("event", event_old.id), source_event_id=f"legacy-{event_old.id}", user_id=user.id,
                          timestamp=timestamp, channel=channel, event_type="UPLOAD_ATTEMPT" if channel == "UPLOAD" else "FILE_" + str(payload.get("activity", "ACTIVITY")).upper(),
                          resource_id=str(resource)[:512] if resource else None, source="legacy-import",
                          details={k: str(v)[:255] for k, v in payload.items() if k in {"filename", "upload_id", "file_size"}},
                          processing_state="LEGACY_UNASSESSED")
            session.add(event)
            decision = session.scalar(select(AnalystDecision).where(AnalystDecision.alert_id == old.id).order_by(AnalystDecision.id.desc()).limit(1))
            status = "ALLOWED" if decision and decision.decision == "allow" else "BLOCKED" if decision and decision.decision == "block" else "DISMISSED" if old.status == "dismissed" else "OPEN"
            risk = RiskAssessment(id=stable("risk", old.id), user_id=user.id, event_id=event.id, anomaly_score=0, sensitivity_score=0,
                                  activity_severity=0, channel_score=0, historical_risk=0, final_risk_score=0,
                                  severity="UNKNOWN", scoring_version="legacy-unassessed", explanation={"contributions": {}, "anomaly_source": "UNAVAILABLE",
                                  "classifier_source": "UNAVAILABLE", "scoring_version": "legacy-unassessed", "policy_threshold": None})
            session.add(risk)
            alert = Alert(id=alert_id, user_id=user.id, event_id=event.id, risk_assessment_id=risk.id, type=event.event_type,
                          severity="UNKNOWN", status=status, title="Imported legacy alert", description="Historical alert; risk was not recomputed",
                          decision=decision.decision.upper() if decision else None)
            session.add(alert)
            session.flush()
            if old.evidence and old.evidence.matches:
                masked = [str(value)[:2] + "***" + str(value)[-2:] for value in old.evidence.matches[:20]]
                session.add(Evidence(alert_id=alert.id, event_id=event.id, evidence_type="LEGACY_MASKED_MATCHES", value={"masked": masked}))
            session.add(AuditLog(action="LEGACY_IMPORTED", entity_type="alert", entity_id=alert.id, details={"legacy_id": old.id}))
            copied += 1
        session.commit()
    print(f"Imported {copied} legacy alerts; original tables remain available")


if __name__ == "__main__": main()
