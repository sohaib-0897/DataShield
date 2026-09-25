"""Persistent normalized telemetry and analyst workflow."""
import uuid
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .core import Base, now


def uid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "ds_users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="VIEWER")
    department: Mapped[str | None] = mapped_column(String(128))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Endpoint(Base):
    __tablename__ = "ds_endpoints"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    machine_id: Mapped[str] = mapped_column(String(128), unique=True)
    hostname: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("ds_users.id"))
    platform: Mapped[str | None] = mapped_column(String(64))
    agent_version: Mapped[str | None] = mapped_column(String(64))
    last_seen: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class Event(Base):
    __tablename__ = "ds_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("ds_users.id"), index=True)
    endpoint_id: Mapped[str | None] = mapped_column(ForeignKey("ds_endpoints.id"), index=True)
    timestamp: Mapped[object] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)
    channel: Mapped[str] = mapped_column(String(16))
    event_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(512))
    resource_type: Mapped[str | None] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(64), default="agent")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    validation_state: Mapped[str] = mapped_column(String(16), default="VALID")
    processing_state: Mapped[str] = mapped_column(String(16), default="PROCESSED")
    user: Mapped[User | None] = relationship()
    endpoint: Mapped[Endpoint | None] = relationship()
    __table_args__ = (Index("ix_ds_events_user_time", "user_id", "timestamp"),)


class InvalidEvent(Base):
    __tablename__ = "ds_invalid_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    reason: Mapped[str] = mapped_column(String(512))
    source_event_id: Mapped[str | None] = mapped_column(String(128))
    received_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)


class DocumentMetadata(Base):
    __tablename__ = "ds_documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    event_id: Mapped[str] = mapped_column(ForeignKey("ds_events.id"), unique=True)
    filename: Mapped[str | None] = mapped_column(String(255))
    extension: Mapped[str | None] = mapped_column(String(32))
    mime_type: Mapped[str | None] = mapped_column(String(128))
    sha256: Mapped[str | None] = mapped_column(String(64))
    size: Mapped[int | None] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(32))
    score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(32))
    model_version: Mapped[str | None] = mapped_column(String(64))


class FeatureWindow(Base):
    __tablename__ = "ds_feature_windows"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("ds_users.id"), index=True)
    window_start: Mapped[object] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[object] = mapped_column(DateTime(timezone=True))
    values: Mapped[dict] = mapped_column(JSON)
    schema_version: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)


class RiskAssessment(Base):
    __tablename__ = "ds_risk_assessments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("ds_users.id"), index=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("ds_events.id"), unique=True)
    feature_window_id: Mapped[str | None] = mapped_column(ForeignKey("ds_feature_windows.id"))
    anomaly_score: Mapped[float] = mapped_column(Float)
    sensitivity_score: Mapped[float] = mapped_column(Float)
    activity_severity: Mapped[float] = mapped_column(Float)
    channel_score: Mapped[float] = mapped_column(Float)
    historical_risk: Mapped[float] = mapped_column(Float)
    final_risk_score: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(16))
    scoring_version: Mapped[str] = mapped_column(String(32))
    explanation: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)


class Alert(Base):
    __tablename__ = "ds_alerts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("ds_users.id"), index=True)
    endpoint_id: Mapped[str | None] = mapped_column(ForeignKey("ds_endpoints.id"))
    event_id: Mapped[str] = mapped_column(ForeignKey("ds_events.id"), unique=True)
    risk_assessment_id: Mapped[str] = mapped_column(ForeignKey("ds_risk_assessments.id"))
    type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(16), index=True)
    status: Mapped[str] = mapped_column(String(16), default="OPEN", index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now, index=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    assigned_to: Mapped[str | None] = mapped_column(ForeignKey("ds_users.id"))
    decision: Mapped[str | None] = mapped_column(String(16))
    decision_timestamp: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    endpoint: Mapped[Endpoint | None] = relationship()
    event: Mapped[Event] = relationship()
    risk: Mapped[RiskAssessment] = relationship()
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="alert")


class Evidence(Base):
    __tablename__ = "ds_evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    alert_id: Mapped[str] = mapped_column(ForeignKey("ds_alerts.id"), index=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("ds_events.id"))
    evidence_type: Mapped[str] = mapped_column(String(64))
    value: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)
    alert: Mapped[Alert] = relationship(back_populates="evidence")


class Policy(Base):
    __tablename__ = "ds_policies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class AuditLog(Base):
    __tablename__ = "ds_audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("ds_users.id"))
    action: Mapped[str] = mapped_column(String(64), index=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(36), index=True)
    timestamp: Mapped[object] = mapped_column(DateTime(timezone=True), default=now, index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    source_ip: Mapped[str | None] = mapped_column(String(64))


class ModelVersion(Base):
    __tablename__ = "ds_model_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    model_type: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(64))
    artifact_path: Mapped[str] = mapped_column(String(512))
    feature_schema_version: Mapped[str] = mapped_column(String(32))
    dataset_id: Mapped[str] = mapped_column(String(128))
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="CANDIDATE")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint("model_type", "version"),)
