"""Evaluate structured kinds on a complete authorized independent guide pilot.

Requires real exhaustive blind reviews, not released annotations or generated
labels. Pilot metrics are conditional development evidence, never final test.
Contextual metrics remain unavailable without a validated automatic detector.
"""
import argparse
import json
from pathlib import Path
import resource
import time

from research.cert_ingest import atomic_json, hash_file, local_path
from research.detection_evaluation import (BASE, CONTRACT_SHA256, MANIFEST_SHA256,
                                           read_json, validate_inputs)
from research.detection_manifest import PROTOCOL_SHA256, STRUCTURED
from research.span_evaluation import evaluate_independent, independent_counts
from research.span_review import validate_packet


def evaluate(packet_path, manifest_path, directory, output):
    output = local_path(BASE, output)
    packet_path = local_path(BASE, packet_path)
    if output.exists() or output.with_suffix(output.suffix + '.partial').exists():
        raise ValueError('New private independent evaluation output required')
    start, cpu = time.perf_counter(), time.process_time()
    manifest, documents, contract = validate_inputs(manifest_path, directory,
        Path('docs/implementation/phase-a2/evaluation-protocol.json'),
        Path('docs/implementation/phase-b2/run-contract.json'))
    scope_path = Path('docs/implementation/phase-b2/span-review-scope.json')
    if (hash_file(scope_path)['sha256'] != contract['human_packet']['scope_sha256']
            or hash_file(Path('ml/content_detection.py'))['sha256'] != contract['detector_source_sha256']):
        raise ValueError('Frozen human scope/detector mismatch')
    packet = read_json(packet_path, 8 * 1024**2)
    checked = validate_packet(packet, manifest['records'], protocol_sha256=PROTOCOL_SHA256,
        manifest_sha256=MANIFEST_SHA256, scope_sha256=contract['human_packet']['scope_sha256'])
    # Nothing is detected until the entire frozen pilot passes the review gate.
    from ml.content_detection import detect_content
    rows, review_manifest = [], []
    for row, review in zip(packet['documents'], checked):
        doc = documents[row['source_document_id_sha256']]
        result = detect_content(doc['text'])
        predictions = [(s['start'], s['end'], s['kind']) for s in result['spans']]
        rows.append({'family_id': row['family_id'],
            'counts': independent_counts(predictions, review, text_length=len(doc['text']), targets=STRUCTURED),
            'result_truncated': result['spans_truncated']})
        review_manifest.append({'document_id_sha256': row['source_document_id_sha256'],
            'family_id': row['family_id'], 'text_sha256': row['text_sha256'],
            'review_binding_sha256': review['review_binding_sha256'], 'exhaustive_targets': review['exhaustive_targets']})
    metrics = evaluate_independent(rows, STRUCTURED)
    report = {'version': 'independent-span-guide-pilot-b2-v1',
        'evidence_lane': 'independent_exhaustive_review', 'purpose': packet['purpose'],
        'final_test_eligible': False, 'scope': 'conditional development guide pilot; not general performance',
        'review_packet_hash': hash_file(packet_path), 'manifest_sha256': MANIFEST_SHA256,
        'protocol_sha256': PROTOCOL_SHA256, 'run_contract_sha256': CONTRACT_SHA256,
        'scope_sha256': contract['human_packet']['scope_sha256'],
        'detector_source_sha256': contract['detector_source_sha256'],
        'B1_eligibility_modified': False, 'review_manifest_version': 'independent-span-guide-pilot-b2-v1',
        'review_manifest': review_manifest, 'structured_metrics': metrics,
        'contextual_metrics': None, 'contextual_reason': 'No validated automatic contextual detector',
        'result_truncated_documents': sum(r['result_truncated'] for r in rows),
        'coverage': {'all_preregistered_pilot_inputs': len(rows), 'complete_source_JSON_inputs': len(rows),
                     'original_container_extraction': 'unavailable', 'excluded_incomplete_reviews': 0},
        'governance': 'Custodian must independently verify authorization, reviewer independence and full-text completeness; code checks declarations only',
        'resources': {'wall_seconds_before_write': time.perf_counter() - start,
                      'cpu_seconds_before_write': time.process_time() - cpu,
                      'peak_RSS_MiB': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024},
        'live_activation': False}
    output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(output, report); output.chmod(0o600)
    print(json.dumps({'version': report['version'], 'documents': len(rows), 'final_test_eligible': False}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    evaluate(args.packet, args.manifest, args.directory, args.output)


if __name__ == '__main__':
    main()
