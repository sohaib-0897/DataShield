"""DataShield FastAPI entry point. Agents and analysts use separate credentials."""
import hmac
import csv
import io
import json
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy import case, desc, func, or_, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from .analysis import FEATURE_SCHEMA_VERSION, assess, behavior, features
from .core import SessionLocal, now, password_hash, require_secrets, settings, token_for
from .models import Alert, AuditLog, DocumentMetadata, Endpoint, Event, Evidence, FeatureWindow, InvalidEvent, ModelVersion, Policy, RiskAssessment, User
from .schemas import DecisionIn, EventIn, LoginIn, ModelRegistration, PolicyConfig, PolicyIn, UserCreate
from .sensitivity import classify_document
from .logging import configure

@asynccontextmanager
async def lifespan(application):
    require_secrets()
    configure()
    yield


RELEASE_VERSION = "0.9.0-pre-cert"
app = FastAPI(title="DataShield API", version=RELEASE_VERSION, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings()["origin"]], allow_methods=["GET", "POST", "PUT"], allow_headers=["Authorization", "Content-Type", "X-Agent-Key"])


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    if request.url.path == "/api/v1/events" and hmac.compare_digest(request.headers.get("X-Agent-Key", ""), settings()["agent_key"]):
        body = exc.body if isinstance(exc.body, dict) else {}
        raw_body = exc.body if isinstance(exc.body, (bytes, str)) else await request.body()
        if not body and isinstance(raw_body, (bytes, str)) and len(raw_body) <= 262144:
            try:
                parsed = json.loads(raw_body)
                body = parsed if isinstance(parsed, dict) else {}
            except (ValueError, TypeError):
                pass
        reason = "; ".join(f"{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in exc.errors())[:500]
        try:
            with SessionLocal.begin() as session:
                session.add(InvalidEvent(reason=reason, source_event_id=str(body.get("source_event_id", ""))[:128]))
        except SQLAlchemyError:
            import logging
            logging.getLogger("datashield").error("invalid_event_diagnostic_failed", extra={"operation": "ingestion"})
    return JSONResponse(status_code=422, content={"detail": [{"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]} for error in exc.errors()]})


@app.middleware("http")
async def request_log(request: Request, call_next):
    started = time.monotonic()
    response = await call_next(request)
    import logging
    logging.getLogger("datashield").info("request", extra={"operation": "http", "method": request.method,
        "path": request.url.path, "status": response.status_code, "duration_ms": round((time.monotonic()-started)*1000, 2)})
    return response


@app.middleware("http")
async def body_limit(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH") and not request.headers.get("content-length"):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=411, content={"detail": "Content-Length required"})
    if request.headers.get("content-length"):
        from fastapi.responses import JSONResponse
        try:
            length = int(request.headers["content-length"])
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})
        if length < 0:
            return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})
        if length > 262144:
            return JSONResponse(status_code=413, content={"detail": "Request exceeds 256 KiB"})
    return await call_next(request)


def db():
    with SessionLocal() as session:
        yield session


def actor(authorization: str | None = Header(None), session: Session = Depends(db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")
    try:
        payload = jwt.decode(authorization[7:], settings()["jwt_secret"], algorithms=["HS256"])
        user = session.get(User, payload["sub"])
    except (jwt.PyJWTError, KeyError):
        user = None
    if user is None or not user.active or not user.password_hash:
        raise HTTPException(401, "Invalid session")
    return user


def analyst(user: User = Depends(actor)):
    if user.role not in ("ADMIN", "ANALYST"):
        raise HTTPException(403, "Analyst role required")
    return user


def admin(user: User = Depends(actor)):
    if user.role != "ADMIN":
        raise HTTPException(403, "Admin role required")
    return user


def agent(x_agent_key: str | None = Header(None)):
    if not x_agent_key or not hmac.compare_digest(x_agent_key, settings()["agent_key"]):
        raise HTTPException(401, "Invalid agent credential")


def audit(session, action, entity_type, entity_id=None, actor_id=None, details=None, ip=None):
    session.add(AuditLog(action=action, entity_type=entity_type, entity_id=entity_id, actor_id=actor_id, details=details or {}, source_ip=ip))


def policy(session):
    row = session.scalar(select(Policy).where(Policy.name == "default"))
    return PolicyConfig.model_validate(row.config) if row and row.enabled else PolicyConfig()


def model_root():
    from pathlib import Path
    return Path(os.getenv("DATASHIELD_MODEL_ROOT", "ml/artifacts")).resolve()


def anomaly_result(values, prior, session, window_minutes):
    active = session.scalar(select(ModelVersion).where(ModelVersion.model_type == "anomaly", ModelVersion.status == "ACTIVE").limit(1))
    artifact = active.artifact_path if active else os.getenv("DATASHIELD_ANOMALY_ARTIFACT")
    if artifact:
        try:
            from ml.registry import load_artifact, score, validate_activation_evaluation
            model, metadata = load_artifact(artifact)
            validate_activation_evaluation(metadata)
            if metadata["window_minutes"] != window_minutes:
                raise ValueError("Policy window duration differs from model training")
            return {"score": score(model, values), "source": "MODEL", "reason": "IsolationForest decision score transformed to prototype 0-100 scale", "model_version": metadata["version"]}
        except (FileNotFoundError, ValueError, ImportError, KeyError, OSError) as exc:
            import logging
            logging.getLogger("datashield").error("anomaly_artifact_unavailable", extra={"operation": "inference", "error_type": type(exc).__name__})
            return {"score": 0.0, "source": "UNAVAILABLE", "reason": "Configured anomaly artifact is unavailable or incompatible", "model_version": None}
    return behavior(values, prior)


def alert_json(a: Alert, detail=False):
    result = {"id": a.id, "title": a.title, "user": a.user.username, "user_id": a.user_id,
              "endpoint": a.endpoint.hostname if a.endpoint else None,
              "machine_id": a.endpoint.machine_id if a.endpoint else None,
              "timestamp": a.created_at.isoformat(), "channel": a.event.channel.lower(), "type": a.type.lower(), "activity": a.event.event_type,
              "file": a.event.resource_id, "resource": a.event.resource_id, "riskScore": a.risk.final_risk_score,
              "severity": a.severity.lower(), "status": a.status.lower(), "decision": a.decision,
              "anomalySource": a.risk.explanation["anomaly_source"], "classifierSource": a.risk.explanation["classifier_source"]}
    if detail:
        result.update(riskBreakdown=a.risk.explanation, evidence=[{"type": e.evidence_type, "value": e.value, "timestamp": e.created_at.isoformat()} for e in a.evidence],
                      event={"id": a.event.id, "timestamp": a.event.timestamp.isoformat(), "channel": a.event.channel,
                             "event_type": a.event.event_type, "resource": a.event.resource_id, "metadata": a.event.details},
                      sensitiveMatches=[v for e in a.evidence if e.evidence_type == "DETECTIONS" for v in e.value.get("detections", [])])
    return result


def ingest_one(session: Session, payload: EventIn):
    existing = session.scalar(select(Event).where(Event.source_event_id == payload.source_event_id))
    if existing:
        alert = session.scalar(select(Alert).where(Alert.event_id == existing.id))
        return {"event_id": existing.id, "duplicate": True, "alert_id": alert.id if alert else None}
    user = session.scalar(select(User).where(User.username == payload.username))
    if user is None:
        user = User(username=payload.username, role="VIEWER")
        session.add(user)
        session.flush()
    endpoint = session.scalar(select(Endpoint).where(Endpoint.machine_id == payload.machine_id))
    if endpoint is None:
        endpoint = Endpoint(machine_id=payload.machine_id, hostname=payload.hostname)
        session.add(endpoint)
        session.flush()
    endpoint.hostname, endpoint.agent_version, endpoint.last_seen = payload.hostname, payload.agent_version, now()
    endpoint.user_id = user.id
    try:
        classification = classify_document(payload)
    except (FileNotFoundError, ValueError, ImportError, KeyError, OSError) as exc:
        import logging
        logging.getLogger("datashield").error("sensitivity_artifact_unavailable", extra={"operation": "inference", "error_type": type(exc).__name__})
        from .sensitivity import RuleBasedSensitivityClassifier
        classification = RuleBasedSensitivityClassifier().classify(payload.metadata, str(payload.metadata.get("sample_text", "")))
        classification["fallback_reason"] = "Configured sensitivity artifact is unavailable or incompatible"
    safe_metadata = {k: v for k, v in payload.metadata.items() if k in {"filename", "extension", "mime_type", "size", "sha256", "upload_id", "destination", "device_id", "sensitivity_label", "synthetic", "drive", "process_name", "remote_port"}}
    safe_metadata["classified_sensitivity_label"] = classification["label"]
    event = Event(source_event_id=payload.source_event_id, user_id=user.id, endpoint_id=endpoint.id, timestamp=payload.timestamp,
                  channel=payload.channel.value, event_type=payload.event_type, resource_id=payload.resource_id,
                  resource_type=payload.resource_type, source=payload.source, details=safe_metadata)
    session.add(event)
    session.flush()
    if payload.channel.value in ("FILE", "UPLOAD", "CLOUD"):
        session.add(DocumentMetadata(event_id=event.id, filename=safe_metadata.get("filename"), extension=safe_metadata.get("extension"),
                                     mime_type=safe_metadata.get("mime_type"), size=safe_metadata.get("size"), sha256=safe_metadata.get("sha256"),
                                     label=classification["label"], score=classification["score"], confidence=classification["confidence"],
                                     source=classification["source"], model_version=classification.get("model_version")))
    config = policy(session)
    end = payload.timestamp + timedelta(microseconds=1)
    start = end - timedelta(minutes=config.feature_window_minutes)
    recent = session.scalars(select(Event).where(Event.user_id == user.id, Event.timestamp >= start, Event.timestamp < end)).all()
    values = features(recent, start, end)
    window = FeatureWindow(user_id=user.id, window_start=start, window_end=end, values=values, schema_version=FEATURE_SCHEMA_VERSION)
    session.add(window)
    session.flush()
    prior = session.scalars(select(FeatureWindow).where(FeatureWindow.user_id == user.id, FeatureWindow.window_end < start).order_by(desc(FeatureWindow.window_end)).limit(8)).all()
    behavioral = anomaly_result(values, [w.values.get("total_event_count", 0) for w in prior], session, config.feature_window_minutes)
    previous_risk = session.scalar(select(RiskAssessment.final_risk_score).where(RiskAssessment.user_id == user.id).order_by(desc(RiskAssessment.created_at)).limit(1)) or 0
    breakdown = assess(payload, classification, behavioral, previous_risk * .5, config)
    risk = RiskAssessment(user_id=user.id, event_id=event.id, feature_window_id=window.id, anomaly_score=behavioral["score"],
                          sensitivity_score=classification["score"], activity_severity=breakdown["components"]["activity"],
                          channel_score=breakdown["components"]["channel"], historical_risk=breakdown["components"]["history"],
                          final_risk_score=breakdown["score"], severity=breakdown["severity"], scoring_version=breakdown["scoring_version"], explanation=breakdown)
    session.add(risk)
    session.flush()
    alert_id = None
    if breakdown["score"] >= config.alert_threshold:
        alert = Alert(user_id=user.id, endpoint_id=endpoint.id, event_id=event.id, risk_assessment_id=risk.id,
                      type=payload.event_type, severity=breakdown["severity"], title=f"{payload.event_type.replace('_', ' ').title()} requires review",
                      description=f"{payload.channel.value} activity exceeded the configured risk threshold")
        session.add(alert)
        session.flush()
        alert_id = alert.id
        session.add(Evidence(alert_id=alert.id, event_id=event.id, evidence_type="RISK_BREAKDOWN", value=breakdown))
        if classification["detections"]:
            session.add(Evidence(alert_id=alert.id, event_id=event.id, evidence_type="DETECTIONS", value={"detections": classification["detections"]}))
        audit(session, "ALERT_CREATED", "alert", alert.id, details={"event_id": event.id, "score": breakdown["score"]})
    return {"event_id": event.id, "duplicate": False, "alert_id": alert_id, "risk": breakdown}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready(session: Session = Depends(db)):
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(503, "Database unavailable")
    return {"status": "ready"}


@app.post("/api/v1/auth/login")
def login(data: LoginIn, request: Request, session: Session = Depends(db)):
    user = session.scalar(select(User).where(User.username == data.username))
    valid = bool(user and user.active and user.password_hash and password_hash.verify(data.password, user.password_hash))
    audit(session, "LOGIN_SUCCESS" if valid else "LOGIN_FAILURE", "user", user.id if user else None, actor_id=user.id if valid else None, ip=request.client.host if request.client else None)
    session.commit()
    if not valid:
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": token_for(user), "token_type": "bearer", "role": user.role, "username": user.username}


@app.get("/api/v1/auth/me")
def me(user: User = Depends(actor)):
    return {"id": user.id, "username": user.username, "role": user.role}


@app.post("/api/v1/events")
def ingest(data: EventIn, _: None = Depends(agent), session: Session = Depends(db)):
    try:
        result = ingest_one(session, data)
        session.commit()
        return result
    except IntegrityError:
        # Concurrent retries can both pass the pre-insert lookup. The unique source ID
        # remains authoritative; return the committed event instead of a spurious 500.
        session.rollback()
        existing = session.scalar(select(Event).where(Event.source_event_id == data.source_event_id))
        if existing is None:
            raise
        alert = session.scalar(select(Alert).where(Alert.event_id == existing.id))
        return {"event_id": existing.id, "duplicate": True, "alert_id": alert.id if alert else None}


@app.post("/api/v1/events/batch")
def ingest_batch(rows: list[dict], _: None = Depends(agent), session: Session = Depends(db)):
    if len(rows) > 100:
        raise HTTPException(413, "Batch limit is 100 events")
    results = []
    for index, row in enumerate(rows):
        try:
            data = EventIn.model_validate(row)
            with session.begin_nested():
                result = ingest_one(session, data)
            results.append({"index": index, "status": "accepted", **result})
        except (ValidationError, ValueError, SQLAlchemyError) as exc:
            reason = str(exc)[:500]
            session.add(InvalidEvent(reason=reason, source_event_id=str(row.get("source_event_id", ""))[:128] if isinstance(row, dict) else ""))
            results.append({"index": index, "status": "invalid", "error": reason})
    session.commit()
    return {"results": results}


@app.post("/api/v1/endpoints/heartbeat")
def heartbeat(data: dict, _: None = Depends(agent), session: Session = Depends(db)):
    machine_id = str(data.get("machine_id", ""))[:128]
    if not machine_id:
        raise HTTPException(422, "machine_id required")
    endpoint = session.scalar(select(Endpoint).where(Endpoint.machine_id == machine_id))
    if endpoint is None:
        endpoint = Endpoint(machine_id=machine_id, hostname=str(data.get("hostname", machine_id))[:255])
        session.add(endpoint)
    endpoint.last_seen, endpoint.agent_version = now(), str(data.get("agent_version", "unknown"))[:64]
    session.commit()
    return {"status": "ONLINE", "machine_id": machine_id}


@app.get("/api/v1/alerts")
def alerts(status: str | None = None, severity: str | None = None, channel: str | None = None, user: str | None = None, search: str | None = None,
           start: datetime | None = None, end: datetime | None = None,
           sort_by: str = Query("created_at", pattern="^(created_at|risk_score|severity|user)$"), descending: bool = True,
           page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200), _: User = Depends(actor), session: Session = Depends(db)):
    stmt = select(Alert).join(Event).join(User, Alert.user_id == User.id).join(RiskAssessment, Alert.risk_assessment_id == RiskAssessment.id).options(selectinload(Alert.user), selectinload(Alert.endpoint), selectinload(Alert.event), selectinload(Alert.risk))
    if status: stmt = stmt.where(Alert.status == status.upper())
    if severity: stmt = stmt.where(Alert.severity == severity.upper())
    if channel: stmt = stmt.where(Event.channel == channel.upper())
    if user: stmt = stmt.where(User.username.ilike(f"%{user}%"))
    if search:
        term = f"%{search[:100]}%"
        stmt = stmt.where(or_(User.username.ilike(term), Event.resource_id.ilike(term), Event.event_type.ilike(term)))
    if start: stmt = stmt.where(Alert.created_at >= start)
    if end: stmt = stmt.where(Alert.created_at < end)
    sort_column = {"created_at": Alert.created_at, "risk_score": RiskAssessment.final_risk_score, "severity": Alert.severity, "user": User.username}[sort_by]
    stmt = stmt.order_by(sort_column.desc() if descending else sort_column.asc(), Alert.id)
    return {"items": [alert_json(a) for a in session.scalars(stmt.offset((page-1)*size).limit(size))],
            "total": session.scalar(select(func.count()).select_from(stmt.subquery()))}


@app.get("/api/v1/alerts/{alert_id}")
def alert_detail(alert_id: str, _: User = Depends(actor), session: Session = Depends(db)):
    alert = session.scalar(select(Alert).where(Alert.id == alert_id).options(selectinload(Alert.user), selectinload(Alert.endpoint), selectinload(Alert.event), selectinload(Alert.risk), selectinload(Alert.evidence)))
    if not alert: raise HTTPException(404, "Alert not found")
    result = alert_json(alert, True)
    result["audit"] = [{"action": row.action, "timestamp": row.timestamp.isoformat(), "details": row.details} for row in session.scalars(select(AuditLog).where(AuditLog.entity_id == alert.id).order_by(AuditLog.timestamp))]
    document = session.scalar(select(DocumentMetadata).where(DocumentMetadata.event_id == alert.event_id))
    result["sensitivity"] = ({"label": document.label, "score": document.score, "confidence": document.confidence,
                              "source": document.source, "model_version": document.model_version} if document else
                             {"label": alert.event.details.get("classified_sensitivity_label", "unclassified"),
                              "score": alert.risk.sensitivity_score, "confidence": None,
                              "source": alert.risk.explanation.get("classifier_source", "UNAVAILABLE"),
                              "model_version": alert.risk.explanation.get("classifier_model_version")})
    start, end = alert.event.timestamp - timedelta(hours=1), alert.event.timestamp + timedelta(hours=1)
    result["supporting_events"] = [{"id": row.id, "timestamp": row.timestamp.isoformat(), "channel": row.channel,
                                    "event_type": row.event_type, "resource": row.resource_id}
                                   for row in session.scalars(select(Event).where(Event.user_id == alert.user_id,
                                       Event.timestamp >= start, Event.timestamp <= end)
                                       .order_by(Event.timestamp).limit(50))]
    result["decision_history"] = result["audit"]
    return result


@app.post("/api/v1/alerts/{alert_id}/decisions")
def decide(alert_id: str, data: DecisionIn, request: Request, user: User = Depends(analyst), session: Session = Depends(db)):
    alert = session.get(Alert, alert_id)
    if not alert: raise HTTPException(404, "Alert not found")
    previous = alert.status
    alert.status = {"ALLOW": "ALLOWED", "BLOCK": "BLOCKED", "DISMISS": "DISMISSED", "RESOLVE": "RESOLVED", "INVESTIGATE": "INVESTIGATING"}[data.action]
    alert.decision, alert.decision_timestamp, alert.assigned_to = data.action, now(), user.id
    audit(session, "ALERT_DECISION", "alert", alert.id, user.id, {"previous": previous, "new": alert.status, "notes": data.notes}, request.client.host if request.client else None)
    session.commit()
    return {"id": alert.id, "status": alert.status, "decision": alert.decision}


@app.get("/api/v1/decisions/{upload_id}")
def poll_decision(upload_id: str, _: None = Depends(agent), session: Session = Depends(db)):
    event = session.scalar(select(Event).where(Event.details["upload_id"].as_string() == upload_id).order_by(desc(Event.received_at)).limit(1))
    alert = session.scalar(select(Alert).where(Alert.event_id == event.id)) if event else None
    if event and not alert:
        return {"decision": "allow", "source": "POLICY_AUTO_ALLOW", "alert_id": None}
    return {"decision": alert.decision.lower() if alert and alert.decision in ("ALLOW", "BLOCK") else "pending",
            "source": "ANALYST" if alert and alert.decision in ("ALLOW", "BLOCK") else "AWAITING_ANALYST",
            "alert_id": alert.id if alert else None}


@app.get("/api/v1/events")
def events(page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200), _: User = Depends(actor), session: Session = Depends(db)):
    rows = session.scalars(select(Event).order_by(desc(Event.timestamp)).offset((page-1)*size).limit(size)).all()
    return {"items": [{"id": e.id, "timestamp": e.timestamp.isoformat(), "channel": e.channel, "event_type": e.event_type, "resource_id": e.resource_id, "metadata": e.details, "user_id": e.user_id} for e in rows],
            "total": session.scalar(select(func.count(Event.id)))}


@app.get("/api/v1/reports/summary")
def summary(days: int = Query(30, ge=1, le=365), _: User = Depends(actor), session: Session = Depends(db)):
    cutoff = now() - timedelta(days=days)
    by_severity = dict(session.execute(select(Alert.severity, func.count(Alert.id)).where(Alert.created_at >= cutoff).group_by(Alert.severity)).all())
    by_status = dict(session.execute(select(Alert.status, func.count(Alert.id)).where(Alert.created_at >= cutoff).group_by(Alert.status)).all())
    by_channel = dict(session.execute(select(Event.channel, func.count(Alert.id)).join(Alert, Alert.event_id == Event.id).where(Alert.created_at >= cutoff).group_by(Event.channel)).all())
    decision_group = case((Alert.decision.is_(None), "PENDING"), else_=Alert.decision)
    decisions = dict(session.execute(select(decision_group, func.count(Alert.id)).where(Alert.created_at >= cutoff).group_by(decision_group)).all())
    daily = [{"date": str(day), "alerts": count} for day, count in session.execute(select(func.date(Alert.created_at), func.count(Alert.id)).where(Alert.created_at >= cutoff).group_by(func.date(Alert.created_at)).order_by(func.date(Alert.created_at))).all()]
    event_daily = [{"date": str(day), "events": count} for day, count in session.execute(select(func.date(Event.received_at), func.count(Event.id)).where(Event.received_at >= cutoff).group_by(func.date(Event.received_at)).order_by(func.date(Event.received_at))).all()]
    risk_daily = [{"date": str(day), "average_risk": round(float(score), 2)} for day, score in session.execute(select(func.date(RiskAssessment.created_at), func.avg(RiskAssessment.final_risk_score)).where(RiskAssessment.created_at >= cutoff).group_by(func.date(RiskAssessment.created_at)).order_by(func.date(RiskAssessment.created_at))).all()]
    users = [{"user": name, "risk": score} for name, score in session.execute(select(User.username, func.max(RiskAssessment.final_risk_score)).join(RiskAssessment, RiskAssessment.user_id == User.id).where(RiskAssessment.created_at >= cutoff).group_by(User.username).order_by(desc(func.max(RiskAssessment.final_risk_score))).limit(10)).all()]
    return {"alerts": session.scalar(select(func.count(Alert.id)).where(Alert.created_at >= cutoff)),
            "events": session.scalar(select(func.count(Event.id)).where(Event.received_at >= cutoff)),
            "events_today": session.scalar(select(func.count(Event.id)).where(Event.received_at >= now().replace(hour=0, minute=0, second=0, microsecond=0))),
            "by_severity": by_severity, "by_status": by_status, "by_channel": by_channel, "decisions": decisions, "daily": daily,
            "event_daily": event_daily, "risk_daily": risk_daily,
            "alerts_with_sensitive_detections": session.scalar(
                select(func.count(func.distinct(Evidence.alert_id)))
                .join(Alert, Evidence.alert_id == Alert.id)
                .where(Evidence.evidence_type == "DETECTIONS", Alert.created_at >= cutoff)
            ),
            "risky_users": users}


@app.get("/api/v1/reports/export")
def export_report(request: Request, days: int = Query(30, ge=1, le=365), user: User = Depends(analyst), session: Session = Depends(db)):
    cutoff = now() - timedelta(days=days)
    rows = session.execute(select(func.date(Alert.created_at), func.count(Alert.id)).where(Alert.created_at >= cutoff).group_by(func.date(Alert.created_at)).order_by(func.date(Alert.created_at))).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "alerts"])
    writer.writerows(rows)
    audit(session, "REPORT_EXPORTED", "report", actor_id=user.id, details={"days": days}, ip=request.client.host if request.client else None)
    session.commit()
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=datashield-alerts.csv"})


@app.get("/api/v1/users/activity")
def users_activity(_: User = Depends(actor), session: Session = Depends(db)):
    event_counts = select(Event.user_id.label("user_id"), func.count(Event.id).label("event_count")).group_by(Event.user_id).subquery()
    alert_counts = select(Alert.user_id.label("user_id"), func.count(Alert.id).label("alert_count")).group_by(Alert.user_id).subquery()
    risk_max = select(RiskAssessment.user_id.label("user_id"), func.max(RiskAssessment.final_risk_score).label("max_risk")).group_by(RiskAssessment.user_id).subquery()
    rows = session.execute(select(User.id, User.username, User.department,
        func.coalesce(event_counts.c.event_count, 0), func.coalesce(alert_counts.c.alert_count, 0),
        func.coalesce(risk_max.c.max_risk, 0))
        .outerjoin(event_counts, event_counts.c.user_id == User.id)
        .outerjoin(alert_counts, alert_counts.c.user_id == User.id)
        .outerjoin(risk_max, risk_max.c.user_id == User.id).order_by(User.username)).all()
    return [{"id": user_id, "username": username, "department": department,
             "events": event_count, "alerts": alert_count, "risk": risk}
            for user_id, username, department, event_count, alert_count, risk in rows]


@app.get("/api/v1/users/{user_id}/timeline")
def user_timeline(user_id: str, days: int = Query(30, ge=1, le=365), _: User = Depends(actor), session: Session = Depends(db)):
    user = session.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    cutoff = now() - timedelta(days=days)
    events = session.scalars(select(Event).where(Event.user_id == user_id, Event.timestamp >= cutoff).order_by(desc(Event.timestamp)).limit(200)).all()
    risks = session.scalars(select(RiskAssessment).where(RiskAssessment.user_id == user_id, RiskAssessment.created_at >= cutoff).order_by(desc(RiskAssessment.created_at)).limit(200)).all()
    recent_alerts = session.scalars(select(Alert).where(Alert.user_id == user_id, Alert.created_at >= cutoff)
        .options(selectinload(Alert.user), selectinload(Alert.endpoint), selectinload(Alert.event), selectinload(Alert.risk))
        .order_by(desc(Alert.created_at)).limit(20)).all()
    channels = {}
    for row in events:
        channels[row.channel] = channels.get(row.channel, 0) + 1
    highest_risk = max(risks, key=lambda row: row.final_risk_score, default=None)
    latest_risk = risks[0] if risks else None
    return {"user": user.username, "events": [{"id": row.id, "timestamp": row.timestamp, "channel": row.channel, "event_type": row.event_type, "resource_id": row.resource_id} for row in events],
            "channels": channels,
            "risk_trend": [{"timestamp": row.created_at, "score": row.final_risk_score, "severity": row.severity,
                            "behavior_source": row.explanation.get("anomaly_source", "UNAVAILABLE")} for row in risks],
            "latest_risk": {"score": latest_risk.final_risk_score, "severity": latest_risk.severity,
                            "behavior_source": latest_risk.explanation.get("anomaly_source", "UNAVAILABLE")} if latest_risk else None,
            "highest_risk": {"score": highest_risk.final_risk_score, "severity": highest_risk.severity} if highest_risk else None,
            "recent_alerts": [alert_json(row) for row in recent_alerts]}


@app.get("/api/v1/policies")
def get_policies(_: User = Depends(actor), session: Session = Depends(db)):
    row = session.scalar(select(Policy).where(Policy.name == "default"))
    return {"enabled": row.enabled if row else True, "version": row.version if row else 0, "config": policy(session).model_dump()}


@app.put("/api/v1/policies")
def set_policies(data: PolicyIn, request: Request, user: User = Depends(admin), session: Session = Depends(db)):
    row = session.scalar(select(Policy).where(Policy.name == "default"))
    if row is None:
        row = Policy(name="default", description="Main alert and risk policy", config=data.config.model_dump())
        session.add(row)
    else:
        row.version += 1
    row.enabled, row.config = data.enabled, data.config.model_dump()
    session.flush()
    audit(session, "POLICY_CHANGED", "policy", row.id, user.id, {"version": row.version}, request.client.host if request.client else None)
    session.commit()
    return {"version": row.version}


@app.get("/api/v1/system/status")
def system_status(_: User = Depends(actor), session: Session = Depends(db)):
    active = session.scalar(select(ModelVersion).where(ModelVersion.model_type == "anomaly", ModelVersion.status == "ACTIVE").limit(1))
    artifact = active.artifact_path if active else os.getenv("DATASHIELD_ANOMALY_ARTIFACT")
    active_version = None
    model_error = None
    if artifact:
        from ml.registry import load_artifact, validate_activation_evaluation
        try:
            _, metadata = load_artifact(artifact)
            validate_activation_evaluation(metadata)
            active_version = metadata["version"]
        except (FileNotFoundError, ValueError, ImportError, KeyError, OSError) as exc:
            model_error = f"Configured artifact unavailable or incompatible ({type(exc).__name__})"
    sensitivity = {"source": "RULE", "model_version": "patterns-v1", "configured_model": "NOT_CONFIGURED"}
    sensitivity_artifact = os.getenv("DATASHIELD_SENSITIVITY_ARTIFACT")
    if sensitivity_artifact:
        try:
            from .sensitivity import ModelSensitivityClassifier
            classifier = ModelSensitivityClassifier(sensitivity_artifact)
            sensitivity = {"source": "MODEL", "model_version": classifier.version, "configured_model": "ACTIVE"}
        except (FileNotFoundError, ValueError, ImportError, KeyError, OSError) as exc:
            sensitivity = {"source": "RULE", "model_version": "patterns-v1", "configured_model": "UNAVAILABLE",
                           "fallback_reason": type(exc).__name__}
    endpoints = session.scalars(select(Endpoint)).all()
    def age(last_seen):
        return now() - (last_seen.replace(tzinfo=timezone.utc) if last_seen.tzinfo is None else last_seen)
    return {"version": RELEASE_VERSION, "database": "READY", "anomaly_model": "MODEL" if active_version else "UNAVAILABLE", "model_error": model_error, "active_model_version": active_version,
            "behavior_source": "MODEL" if active_version else "HEURISTIC", "production_model_available": bool(active_version),
            "sensitivity": sensitivity, "feature_schema_version": FEATURE_SCHEMA_VERSION, "last_event": session.scalar(select(func.max(Event.received_at))),
            "endpoints": [{"hostname": e.hostname, "machine_id": e.machine_id, "last_seen": e.last_seen, "status": "ONLINE" if e.last_seen and age(e.last_seen) < timedelta(minutes=5) else "STALE" if e.last_seen and age(e.last_seen) < timedelta(hours=1) else "OFFLINE"} for e in endpoints]}


@app.get("/api/v1/audit")
def audit_logs(_: User = Depends(admin), session: Session = Depends(db)):
    return [{"id": row.id, "action": row.action, "entity_type": row.entity_type, "entity_id": row.entity_id, "timestamp": row.timestamp, "details": row.details} for row in session.scalars(select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(200))]


@app.post("/api/v1/users")
def create_user(data: UserCreate, request: Request, current: User = Depends(admin), session: Session = Depends(db)):
    if session.scalar(select(User).where(User.username == data.username)):
        raise HTTPException(409, "Username already exists")
    row = User(username=data.username, email=data.email, password_hash=password_hash.hash(data.password), role=data.role, department=data.department)
    session.add(row)
    session.flush()
    audit(session, "USER_CREATED", "user", row.id, current.id, {"role": row.role}, request.client.host if request.client else None)
    session.commit()
    return {"id": row.id, "username": row.username, "role": row.role}


@app.get("/api/v1/models")
def models(_: User = Depends(admin), session: Session = Depends(db)):
    return [{"id": row.id, "model_type": row.model_type, "version": row.version, "feature_schema_version": row.feature_schema_version,
             "dataset_id": row.dataset_id, "metrics": row.metrics, "status": row.status, "created_at": row.created_at} for row in session.scalars(select(ModelVersion).order_by(desc(ModelVersion.created_at)))]


@app.post("/api/v1/models")
def register_model(data: ModelRegistration, request: Request, user: User = Depends(admin), session: Session = Depends(db)):
    from ml.registry import load_artifact
    folder = (model_root() / data.artifact_name).resolve()
    if not folder.is_relative_to(model_root()):
        raise HTTPException(422, "Artifact path must be inside the model root")
    try:
        _, metadata = load_artifact(folder, allow_test=True)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        raise HTTPException(422, f"Invalid artifact: {exc}")
    if session.scalar(select(ModelVersion).where(ModelVersion.model_type == "anomaly", ModelVersion.version == metadata["version"])):
        raise HTTPException(409, "Model version already registered")
    if metadata["status"] != "CANDIDATE":
        raise HTTPException(422, "Only unevaluated or reviewed candidates may be registered")
    row = ModelVersion(model_type="anomaly", version=metadata["version"], artifact_path=str(folder),
                       feature_schema_version=metadata["feature_schema_version"], dataset_id=metadata["dataset_id"],
                       metrics=metadata.get("metrics", {}), status="CANDIDATE")
    session.add(row)
    session.flush()
    audit(session, "MODEL_REGISTERED", "model", row.id, user.id, {"version": row.version}, request.client.host if request.client else None)
    session.commit()
    return {"id": row.id, "status": row.status}


@app.post("/api/v1/models/{model_id}/activate")
def activate_model(model_id: str, request: Request, user: User = Depends(admin), session: Session = Depends(db)):
    from ml.registry import load_artifact, validate_activation_evaluation
    row = session.get(ModelVersion, model_id)
    if not row: raise HTTPException(404, "Model not found")
    if row.status != "CANDIDATE": raise HTTPException(422, "Only a candidate artifact can be activated")
    try:
        _, metadata = load_artifact(row.artifact_path)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        raise HTTPException(422, f"Artifact is incompatible: {exc}")
    try:
        validate_activation_evaluation(metadata)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    for previous in session.scalars(select(ModelVersion).where(ModelVersion.model_type == row.model_type, ModelVersion.status == "ACTIVE")):
        previous.status = "ARCHIVED"
    row.status = "ACTIVE"
    audit(session, "MODEL_ACTIVATED", "model", row.id, user.id, {"version": row.version}, request.client.host if request.client else None)
    session.commit()
    return {"id": row.id, "status": row.status}
