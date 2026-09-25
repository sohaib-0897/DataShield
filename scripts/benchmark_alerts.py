"""Repeatable PostgreSQL/API benchmark; creates explicitly tagged benchmark rows."""
import json
import logging
import os
import platform
import statistics
import time
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select, update

from app.core import SessionLocal, now, password_hash, token_for
from app.main import app
from app.models import Alert, AuditLog, Endpoint, Event, RiskAssessment, User


def measure(client, headers, label, params=None, repeats=7):
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        response = client.get("/api/v1/alerts", headers=headers, params=params or {})
        response.raise_for_status()
        samples.append((time.perf_counter() - started) * 1000)
    return {"query": label, "samples": repeats, "median_ms": round(statistics.median(samples), 2),
            "p95_ms": round(sorted(samples)[min(len(samples)-1, int(len(samples)*.95))], 2)}


def main():
    logging.getLogger("datashield").setLevel(logging.WARNING)
    count = int(os.getenv("DATASHIELD_BENCHMARK_ALERTS", "10000"))
    if count < 10000:
        raise SystemExit("DATASHIELD_BENCHMARK_ALERTS must be at least 10000")
    cutoff_time = now()
    with SessionLocal.begin() as session:
        user = session.scalar(select(User).where(User.username == "benchmark.user"))
        if user is None:
            user = User(username="benchmark.user", role="ADMIN", password_hash=password_hash.hash("benchmark-only-password"))
            session.add(user)
            session.flush()
        endpoint = session.scalar(select(Endpoint).where(Endpoint.machine_id == "BENCHMARK-ENDPOINT"))
        if endpoint is None:
            endpoint = Endpoint(machine_id="BENCHMARK-ENDPOINT", hostname="benchmark-host", user_id=user.id)
            session.add(endpoint)
            session.flush()
        existing = session.scalar(select(Alert.id).where(Alert.title == "BENCHMARK ONLY").limit(1))
        if existing is not None:
            benchmark_events = select(Event.id).where(Event.source_event_id.like("benchmark-%"))
            session.execute(update(RiskAssessment).where(RiskAssessment.event_id.in_(benchmark_events)).values(
                explanation={"anomaly_source": "BENCHMARK", "classifier_source": "BENCHMARK",
                             "scoring_version": "benchmark-v1", "components": {}, "contributions": {}}))
        if existing is None:
            for offset in range(0, count, 500):
                events, risks, alerts = [], [], []
                for index in range(offset, min(offset + 500, count)):
                    event_id, risk_id, alert_id = str(uuid4()), str(uuid4()), str(uuid4())
                    timestamp = cutoff_time - timedelta(days=index % 30, minutes=index % 1440)
                    channel = ("FILE", "USB", "UPLOAD", "CLOUD", "NETWORK")[index % 5]
                    event = Event(id=event_id, source_event_id=f"benchmark-{index}", user_id=user.id, endpoint_id=endpoint.id,
                                  timestamp=timestamp, received_at=timestamp, channel=channel, event_type="BENCHMARK_EVENT",
                                  resource_id=f"benchmark-resource-{index}", source="benchmark", details={"synthetic": True, "benchmark": True})
                    risk = RiskAssessment(id=risk_id, user_id=user.id, event_id=event_id, anomaly_score=0, sensitivity_score=0,
                                          activity_severity=0, channel_score=0, historical_risk=0, final_risk_score=float(index % 100),
                                          severity=("LOW", "MEDIUM", "HIGH", "CRITICAL")[index % 4], scoring_version="benchmark-v1",
                                          explanation={"anomaly_source": "BENCHMARK", "classifier_source": "BENCHMARK",
                                                       "scoring_version": "benchmark-v1", "components": {}, "contributions": {}})
                    alert = Alert(id=alert_id, user_id=user.id, endpoint_id=endpoint.id, event_id=event_id, risk_assessment_id=risk_id,
                                  type="BENCHMARK_EVENT", severity=risk.severity,
                                  status=("OPEN", "INVESTIGATING", "RESOLVED", "DISMISSED")[index % 4],
                                  title="BENCHMARK ONLY", description="Synthetic performance fixture",
                                  created_at=timestamp, updated_at=timestamp)
                    events.append(event); risks.append(risk); alerts.append(alert)
                session.add_all(events)
                session.flush()
                session.add_all(risks)
                session.flush()
                session.add_all(alerts)
                session.flush()
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.username == "benchmark.user"))
        token = token_for(user)
        alert_id = session.scalar(select(Alert.id).where(Alert.title == "BENCHMARK ONLY").order_by(Alert.created_at.desc()))
    headers = {"Authorization": f"Bearer {token}"}
    queries = [
        ("alerts listing", {"size": 50}),
        ("severity filter", {"severity": "HIGH", "size": 50}),
        ("status filter", {"status": "OPEN", "size": 50}),
        ("channel filter", {"channel": "USB", "size": 50}),
        ("user filter", {"user": "benchmark.user", "size": 50}),
        ("date filter", {"start": (cutoff_time-timedelta(days=7)).isoformat(), "end": cutoff_time.isoformat(), "size": 50}),
    ]
    results = []
    with TestClient(app) as client:
        logging.getLogger("datashield").setLevel(logging.WARNING)
        for label, params in queries:
            results.append(measure(client, headers, label, params))
        report_samples = []
        for _ in range(7):
            started = time.perf_counter()
            response = client.get("/api/v1/reports/summary?days=30", headers=headers)
            response.raise_for_status()
            report_samples.append((time.perf_counter()-started)*1000)
        results.append({"query": "report summary aggregation", "samples": len(report_samples),
                        "median_ms": round(statistics.median(report_samples), 2),
                        "p95_ms": round(sorted(report_samples)[6], 2)})
        detail_samples = []
        for _ in range(7):
            started = time.perf_counter()
            response = client.get(f"/api/v1/alerts/{alert_id}", headers=headers)
            response.raise_for_status()
            detail_samples.append((time.perf_counter()-started)*1000)
        results.append({"query": "alert detail lookup", "samples": len(detail_samples),
                        "median_ms": round(statistics.median(detail_samples), 2),
                        "p95_ms": round(sorted(detail_samples)[6], 2)})
    from sqlalchemy import text
    with SessionLocal() as session:
        db_version = session.scalar(text("SELECT version()"))
    # Remove only this script's tagged fixtures so running a benchmark cannot pollute
    # the supervisor demo or erase unrelated event/analyst history.
    with SessionLocal.begin() as session:
        benchmark_events = select(Event.id).where(Event.source_event_id.like("benchmark-%"))
        session.execute(delete(Alert).where(Alert.title == "BENCHMARK ONLY"))
        session.execute(delete(RiskAssessment).where(RiskAssessment.event_id.in_(benchmark_events)))
        session.execute(delete(Event).where(Event.source_event_id.like("benchmark-%")))
        benchmark_endpoint = session.scalar(select(Endpoint).where(Endpoint.machine_id == "BENCHMARK-ENDPOINT"))
        if benchmark_endpoint is not None:
            endpoint_in_use = session.scalar(select(Event.id).where(Event.endpoint_id == benchmark_endpoint.id).limit(1))
            endpoint_in_alert = session.scalar(select(Alert.id).where(Alert.endpoint_id == benchmark_endpoint.id).limit(1))
            if endpoint_in_use is None and endpoint_in_alert is None:
                session.delete(benchmark_endpoint)
                session.flush()
        benchmark_user = session.scalar(select(User).where(User.username == "benchmark.user"))
        if benchmark_user is not None:
            user_references = (
                session.scalar(select(Event.id).where(Event.user_id == benchmark_user.id).limit(1)),
                session.scalar(select(RiskAssessment.id).where(RiskAssessment.user_id == benchmark_user.id).limit(1)),
                session.scalar(select(Alert.id).where(Alert.user_id == benchmark_user.id).limit(1)),
                session.scalar(select(Alert.id).where(Alert.assigned_to == benchmark_user.id).limit(1)),
                session.scalar(select(AuditLog.id).where(AuditLog.actor_id == benchmark_user.id).limit(1)),
                session.scalar(select(Endpoint.id).where(Endpoint.user_id == benchmark_user.id).limit(1)),
            )
            if not any(user_references):
                session.delete(benchmark_user)
    payload = {"generated_at": now().isoformat(), "database": db_version.split(",")[0],
               "machine": platform.platform(), "python": platform.python_version(), "benchmark_alert_count": count,
               "fixture": "synthetic database rows tagged benchmark; not demo evidence", "results": results}
    destination = Path("artifacts/benchmarks/latest.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
