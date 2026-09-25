"""Minimal structured request logging without payloads or credentials."""
import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "level": record.levelname,
                           "operation": getattr(record, "operation", "log"), "message": record.getMessage(),
                           "method": getattr(record, "method", None), "path": getattr(record, "path", None),
                           "status": getattr(record, "status", None), "duration_ms": getattr(record, "duration_ms", None)})


def configure():
    logger = logging.getLogger("datashield")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger
