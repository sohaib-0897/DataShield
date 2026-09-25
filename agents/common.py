"""Normalized event delivery with bounded retries."""
import os
import platform
import time
import uuid
from datetime import datetime, timezone

import requests


def event(channel, event_type, resource_id=None, metadata=None):
    hostname = platform.node() or "unknown-host"
    return {"source_event_id": str(uuid.uuid4()), "username": os.getenv("USERNAME") or os.getenv("USER") or "unknown-user",
            "machine_id": os.getenv("DATASHIELD_MACHINE_ID", hostname), "hostname": hostname,
            "timestamp": datetime.now(timezone.utc).isoformat(), "channel": channel, "event_type": event_type,
            "resource_id": resource_id, "metadata": metadata or {}, "agent_version": "1.0"}


def send(payload, attempts=4):
    url = os.getenv("DATASHIELD_URL", "http://127.0.0.1:8000")
    key = os.environ["DATASHIELD_AGENT_KEY"]
    for index in range(attempts):
        try:
            response = requests.post(url + "/api/v1/events", json=payload, headers={"X-Agent-Key": key}, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if index == attempts - 1:
                raise
            time.sleep(min(2 ** index, 8))


def heartbeat():
    hostname = platform.node() or "unknown-host"
    response = requests.post(os.getenv("DATASHIELD_URL", "http://127.0.0.1:8000") + "/api/v1/endpoints/heartbeat",
                             json={"machine_id": os.getenv("DATASHIELD_MACHINE_ID", hostname), "hostname": hostname, "agent_version": "1.0"},
                             headers={"X-Agent-Key": os.environ["DATASHIELD_AGENT_KEY"]}, timeout=5)
    response.raise_for_status()
    return response.json()
