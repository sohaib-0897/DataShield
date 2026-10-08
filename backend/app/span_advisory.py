"""Authenticated opt-in endpoint; no persistence, sensitivity or enforcement calls."""
import os

from fastapi import APIRouter, HTTPException

from ml.supplied_spans import ArtifactUnavailable, SuppliedSpanRequest, service

router = APIRouter()


@router.post('/api/v1/advisory/supplied-spans')
def classify_spans(payload: SuppliedSpanRequest):
    if os.getenv('DATASHIELD_SPAN_ADVISORY_ENABLED', 'false').lower() != 'true':
        raise HTTPException(404, 'Supplied-span advisory is disabled')
    try:
        return service.get().classify(payload)
    except ArtifactUnavailable as exc:
        raise HTTPException(503, str(exc)) from None
    except Exception:
        raise HTTPException(503, 'Supplied-span inference unavailable') from None
