"""Private, blank exhaustive entity-span review packets, distinct from sensitivity.

Validation checks declarations/bindings, not the truth of human independence.
Custodian authorization and reviewer governance remain external requirements.
"""
from datetime import datetime
import argparse
import hashlib
import json
from pathlib import Path

from research.detection_manifest import STRUCTURED, text_hash
from research.span_evaluation import spans
from research.tab_prepare import CLASSES, digest

VERSION = 'exhaustive-span-review-b2-v1'
TARGETS = CLASSES + list(STRUCTURED)


def blank_packet(records, documents, *, protocol_sha256, manifest_sha256, scope_sha256):
    """Select 12 validation families without viewing predictions; guide pilot only."""
    candidates = [r for r in records if r['development_split'] == 'validation']
    families = sorted({r['family_id'] for r in candidates},
                      key=lambda key: hashlib.sha256(('42:' + key).encode()).hexdigest())[:12]
    chosen = sorted((r for r in candidates if r['family_id'] in families),
                    key=lambda r: r['source_document_id_sha256'])
    packet = {'version': VERSION, 'purpose': 'GUIDE_PILOT_NOT_FINAL_EVALUATION',
              'protocol_sha256': protocol_sha256, 'manifest_sha256': manifest_sha256,
              'scope_sha256': scope_sha256, 'target_categories': TARGETS,
              'custodian_authorization': None, 'documents': []}
    for row in chosen:
        doc = documents[row['source_document_id_sha256']]
        if text_hash(doc['text']) != row['text_sha256']:
            raise ValueError('Review text binding mismatch')
        packet['documents'].append({'source_document_id_sha256': row['source_document_id_sha256'],
            'family_id': row['family_id'], 'development_split': 'validation',
            'text_sha256': row['text_sha256'], 'text': doc['text'],
            'original_container_sha256': None, 'container_provenance_status': 'release JSON text only',
            'reviews': [None, None], 'adjudication': None})
    return packet


def _completed_review(value, text, targets):
    if (not isinstance(value, dict) or not isinstance(value.get('reviewer_id'), str)
            or not value['reviewer_id'].strip() or value.get('independent') is not True
            or value.get('saw_predictions_or_release_annotations') is not False
            or value.get('text_sha256') != text_hash(text)
            or not isinstance(value.get('exhaustive_targets'), list)
            or len(value['exhaustive_targets']) != len(targets)
            or set(value['exhaustive_targets']) != set(targets)):
        raise ValueError('Complete blind exhaustive review declarations required')
    try:
        timestamp = datetime.fromisoformat(value['completed_at'])
        if timestamp.tzinfo is None:
            raise ValueError('Review timestamp must include timezone')
    except (KeyError, TypeError, ValueError):
        raise ValueError('Review completion timestamp required') from None
    values, duplicates = spans(value.get('spans', []), len(text), targets)
    if duplicates or 'spans' not in value:
        raise ValueError('Explicit unique spans required, including [] for reviewed absence')
    return values


def validate_document_review(row, *, targets=TARGETS):
    text = row['text']
    if row.get('text_sha256') != text_hash(text):
        raise ValueError('Original text digest mismatch')
    reviews = row.get('reviews')
    if not isinstance(reviews, list) or len(reviews) != 2:
        raise ValueError('Exactly two independent reviews required')
    first, second = (_completed_review(r, text, targets) for r in reviews)
    if reviews[0]['reviewer_id'] == reviews[1]['reviewer_id']:
        raise ValueError('Independent reviewer identities must differ')
    adjudication = row.get('adjudication')
    if (not isinstance(adjudication, dict)
            or adjudication.get('reviewer_id') in {r['reviewer_id'] for r in reviews}
            or adjudication.get('review_sha256') != [digest(r) for r in reviews]
            or adjudication.get('full_text_exhaustive_check') is not True
            or adjudication.get('unresolved_disagreements') != 0):
        raise ValueError('Distinct digest-bound exhaustive adjudication required')
    # Adjudicator sees the individual reviews, but no detector/release labels.
    resolved = _completed_review(adjudication, text, targets)
    disputed = first ^ second
    if adjudication.get('disputed_spans') != [list(s) for s in sorted(disputed)]:
        raise ValueError('Every review disagreement must be retained for adjudication')
    return {'evidence_lane': 'independent_exhaustive_review',
            'exhaustive_targets': list(targets), 'spans': sorted(resolved),
            'review_binding_sha256': digest(row),
            'governance': 'validated declarations only; custodian must verify actual independence/authorization'}


def validate_packet(packet, records, *, protocol_sha256, manifest_sha256, scope_sha256):
    if (packet.get('version') != VERSION or packet.get('protocol_sha256') != protocol_sha256
            or packet.get('manifest_sha256') != manifest_sha256 or packet.get('scope_sha256') != scope_sha256
            or packet.get('target_categories') != TARGETS
            or packet.get('purpose') != 'GUIDE_PILOT_NOT_FINAL_EVALUATION'
            or not isinstance(packet.get('custodian_authorization'), str)
            or not packet['custodian_authorization'].strip()):
        raise ValueError('Versioned authorized guide-pilot packet required')
    by_id = {r['source_document_id_sha256']: r for r in records}
    seen, checked = set(), []
    if not isinstance(packet.get('documents'), list) or not packet['documents']:
        raise ValueError('Review documents required')
    for row in packet['documents']:
        key = row['source_document_id_sha256']
        original = by_id.get(key)
        if (key in seen or not original or original['development_split'] != 'validation'
                or row.get('development_split') != 'validation'
                or row.get('family_id') != original['family_id'] or row.get('text_sha256') != original['text_sha256']):
            raise ValueError('Review source/family/partition binding mismatch')
        seen.add(key)
        checked.append(validate_document_review(row))
    candidates = [r for r in records if r['development_split'] == 'validation']
    families = sorted({r['family_id'] for r in candidates},
                      key=lambda key: hashlib.sha256(('42:' + key).encode()).hexdigest())[:12]
    expected = {r['source_document_id_sha256'] for r in candidates if r['family_id'] in families}
    if seen != expected:
        raise ValueError('Frozen pilot population must be complete; no prediction-based selection')
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    from research.cert_ingest import hash_file, local_path
    from research.detection_evaluation import MANIFEST_SHA256, CONTRACT_SHA256, read_json
    from research.detection_manifest import PROTOCOL_SHA256, validate_manifest
    root = Path('research/local').absolute()
    packet_path, manifest_path = (local_path(root, p) for p in (args.packet, args.manifest))
    contract_path = Path('docs/implementation/phase-b2/run-contract.json')
    if hash_file(manifest_path)['sha256'] != MANIFEST_SHA256 or hash_file(contract_path)['sha256'] != CONTRACT_SHA256:
        raise ValueError('Frozen manifest/run contract mismatch')
    manifest = read_json(manifest_path, 8 * 1024**2); validate_manifest(manifest)
    contract = read_json(contract_path, 1024**2)
    packet = read_json(packet_path, 8 * 1024**2)
    checked = validate_packet(packet, manifest['records'], protocol_sha256=PROTOCOL_SHA256,
                              manifest_sha256=MANIFEST_SHA256,
                              scope_sha256=contract['human_packet']['scope_sha256'])
    print(json.dumps({'documents_validated': len(checked), 'purpose': packet['purpose'],
                      'actual_independence_verified_by_code': False, 'final_evaluation_eligible': False}))


if __name__ == '__main__':
    main()
