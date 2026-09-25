"""Historical alerts keep identity and masked evidence during migration."""
import sys
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
from app.core import Base as NewBase
from app.models import Alert as NewAlert, Evidence
from legacy.flask.database import Base as OldBase
from legacy.flask.models import Alert as OldAlert, AlertEvidence, Event as OldEvent
from scripts.migration import migrate_legacy


def test_legacy_import_is_idempotent_and_masks(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    OldBase.metadata.create_all(engine)
    NewBase.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(migrate_legacy, "SessionLocal", sessions)
    with sessions.begin() as session:
        session.add(OldAlert(event=OldEvent(kind="upload", payload={"filename":"synthetic.txt", "upload_id":"synthetic-legacy"}, timestamp="2026-01-01T00:00:00"),
                             evidence=AlertEvidence(preview="secret raw text", sensitive=True, matches=["12345-1234567-1"])))
    migrate_legacy.main()
    migrate_legacy.main()
    with sessions() as session:
        rows = session.scalars(select(NewAlert)).all()
        assert len(rows) == 1
        assert rows[0].severity == "UNKNOWN"
        evidence = session.scalar(select(Evidence))
        assert "12345-1234567-1" not in str(evidence.value)
        assert "***" in str(evidence.value)
