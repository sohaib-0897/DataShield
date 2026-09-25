"""Strict boundary contracts for agents and analysts."""
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class Channel(str, Enum):
    FILE = "FILE"
    USB = "USB"
    CLOUD = "CLOUD"
    UPLOAD = "UPLOAD"
    NETWORK = "NETWORK"


class EventIn(BaseModel):
    source_event_id: str = Field(min_length=1, max_length=128)
    username: str = Field(min_length=1, max_length=128)
    machine_id: str = Field(min_length=1, max_length=128)
    hostname: str = Field(min_length=1, max_length=255)
    timestamp: datetime
    channel: Channel
    event_type: str = Field(pattern=r"^[A-Z][A-Z0-9_]{1,63}$")
    resource_id: str | None = Field(default=None, max_length=512)
    resource_type: str | None = Field(default=None, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)
    agent_version: str = Field(default="1.0", max_length=64)
    source: str = Field(default="agent", max_length=64)

    @field_validator("timestamp")
    @classmethod
    def aware_time(cls, value):
        if value.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        if value > datetime.now(timezone.utc).replace(microsecond=0) and (value - datetime.now(timezone.utc)).total_seconds() > 300:
            raise ValueError("timestamp is too far in the future")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def bounded_metadata(self):
        if len(json.dumps(self.metadata, default=str).encode()) > 16384:
            raise ValueError("metadata exceeds 16 KiB")
        return self


class DecisionIn(BaseModel):
    action: str = Field(pattern="^(ALLOW|BLOCK|DISMISS|RESOLVE|INVESTIGATE)$")
    notes: str = Field(default="", max_length=2000)


class PolicyConfig(BaseModel):
    alert_threshold: int = Field(default=55, ge=0, le=100)
    medium_threshold: int = Field(default=35, ge=0, le=100)
    high_threshold: int = Field(default=65, ge=0, le=100)
    critical_threshold: int = Field(default=85, ge=0, le=100)
    weights: dict[str, float] = Field(default_factory=lambda: {"anomaly": .20, "sensitivity": .30, "activity": .20, "channel": .20, "history": .10})
    feature_window_minutes: int = Field(default=60, ge=5, le=1440)

    @model_validator(mode="after")
    def check(self):
        if not (self.medium_threshold < self.high_threshold < self.critical_threshold):
            raise ValueError("severity thresholds must increase")
        if set(self.weights) != {"anomaly", "sensitivity", "activity", "channel", "history"} or any(v < 0 for v in self.weights.values()) or abs(sum(self.weights.values()) - 1) > .0001:
            raise ValueError("risk weights must be nonnegative and sum to one")
        return self


class PolicyIn(BaseModel):
    enabled: bool
    config: PolicyConfig


class LoginIn(BaseModel):
    username: str
    password: str


class ModelRegistration(BaseModel):
    artifact_name: str = Field(pattern=r"^[A-Za-z0-9_./-]{1,128}$")


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9._-]+$")
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=12, max_length=128)
    role: str = Field(pattern="^(ADMIN|ANALYST|VIEWER)$")
    department: str | None = Field(default=None, max_length=128)
