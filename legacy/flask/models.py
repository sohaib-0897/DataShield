"""Persistence schema for the current analyst review workflow."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from legacy.flask.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)


class Event(Base):
    __tablename__ = 'events'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'))
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)
    user: Mapped[User | None] = relationship()


class Alert(Base):
    __tablename__ = 'alerts'
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey('events.id'), unique=True)
    status: Mapped[str] = mapped_column(String(32), default='pending', nullable=False)
    event: Mapped[Event] = relationship()
    evidence: Mapped['AlertEvidence | None'] = relationship(back_populates='alert', uselist=False)


class AlertEvidence(Base):
    __tablename__ = 'alert_evidence'
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey('alerts.id'), unique=True)
    preview: Mapped[str | None] = mapped_column(Text)
    sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    matches: Mapped[list] = mapped_column(JSON, default=list)
    alert: Mapped[Alert] = relationship(back_populates='evidence')


class AnalystDecision(Base):
    __tablename__ = 'analyst_decisions'
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey('alerts.id'), nullable=False)
    upload_id: Mapped[str | None] = mapped_column(String(255), index=True)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)
    alert: Mapped[Alert] = relationship()


class Policy(Base):
    __tablename__ = 'policies'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey('alerts.id'))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
