"""B2 fixed-population structured execution and release-boundary diagnostics.

Writes private artifacts only under research/local. Never parses historical test
JSON, deserializes a supplied-span classifier or invents independently complete
annotations. No candidate selection, fitting, tuning or activation.
"""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import platform
import resource
import statistics
import time

from research.cert_ingest import atomic_json, hash_file, local_path
from research.detection_manifest import (DOCUMENTS_SHA256, PROTOCOL_SHA256, STRUCTURED,
                                        overlap_pairs, summarize, text_hash, validate_manifest)
from research.span_evaluation import cluster_interval, compare_reference, ratio
from research.span_review import blank_packet
from research.tab_prepare import CLASSES, consensus, digest, normalized

VERSION = 'automatic-content-evaluation-b2-v1'
MANIFEST_SHA256 = '3bfd2e38073d6904de16c47e3f0a0bb01ddf6ca6fdc375386e199c66b6b6df5b'
MANIFEST_PAYLOAD = '210d34c33b6c34b98ed48a4b1e442df4df184279a7f26b9c56360a2e47abce00'
CONTRACT_SHA256 = '7564cf4b88fd343b4823fcef8d3c6cd70c998d461cb18df46dafa5879ec2af50'
BASE = Path('research/local').absolute()


def read_json(path, maximum):
    if path.stat().st_size > maximum:
        raise ValueError('Metadata/source size bound exceeded')
    return json.loads(path.read_text(encoding='utf-8'))


def validate_inputs(manifest_path, directory, protocol_path, contract_path):
    manifest_path, directory = (local_path(BASE, p) for p in (manifest_path, directory))
    if (hash_file(manifest_path)['sha256'] != MANIFEST_SHA256
            or hash_file(protocol_path)['sha256'] != PROTOCOL_SHA256
            or hash_file(contract_path)['sha256'] != CONTRACT_SHA256):
        raise ValueError('Frozen manifest/protocol/B2 run contract mismatch')
    manifest = read_json(manifest_path, 8 * 1024**2)
    validate_manifest(manifest)
    if manifest['payload_sha256'] != MANIFEST_PAYLOAD:
        raise ValueError('Manifest canonical payload mismatch')
    frozen = local_path(BASE, BASE / 'document_sensitivity/ds2_prepared_v2/documents.json')
    if hash_file(frozen)['sha256'] != DOCUMENTS_SHA256:
        raise ValueError('Frozen historical document-family metadata mismatch')
    # All source bytes verified, including test; only train/dev JSON is parsed.
    for name, item in manifest['source_hashes'].items():
        if hash_file(local_path(BASE, directory / name)) != item:
            raise ValueError('Pinned source blob mismatch')
    by_id = {r['source_document_id_sha256']: r for r in manifest['records']}
    documents = {}
    for split in ('train', 'dev'):
        source = read_json(directory / f'echr_{split}.json', 64 * 1024**2)
        if not isinstance(source, list) or len(source) > 2000:
            raise ValueError('Source document bound exceeded')
        for doc in source:
            key = digest(doc['doc_id'])
            row = by_id.get(key)
            if key in documents or not row or row['official_split'] != split:
                raise ValueError('Unexpected, duplicate or historical source document')
            references, audit = consensus(doc)
            if (digest(doc) != row['source_record_sha256']
                    or text_hash(doc['text']) != row['text_sha256']
                    or text_hash(normalized(doc['text'])) != row['normalized_text_sha256']
                    or digest(sorted(doc['quality_checked'])) != row['reviewed_set_ids_sha256']
                    or len(doc['quality_checked']) != row['reviewed_sets']
                    or len(references) != row['consensus_spans'] or audit != row['annotation_audit']
                    or overlap_pairs(references) != row['overlapping_consensus_pairs']
                    or len(doc['text']) != row['text_characters']
                    or len(doc['text'].encode()) != row['text_utf8_bytes']
                    or any(sum(t == c for _, _, t in references)
                           != row['annotation_coverage'][c]['unanimous_reference_spans'] for c in CLASSES)):
                raise ValueError('Source/reference/coverage binding mismatch')
            documents[key] = doc
    if set(documents) != {k for k, r in by_id.items() if r['official_split'] != 'test'}:
        raise ValueError('Incomplete development source accounting')
    return manifest, documents, read_json(contract_path, 1024**2)


def contextual_gate():
    names = ('spacy', 'en_core_web_sm', 'transformers', 'torch', 'stanza')
    available = {name: importlib.util.find_spec(name) is not None for name in names}
    return {'status': 'BLOCKED_NO_SELECTED_PINNED_AUTOMATIC_CONTEXTUAL_DETECTOR',
            'package_discovery': available, 'model_selected': False, 'model_loaded': False,
            'inference_executed': False, 'artifact_sha256': None, 'runtime_limits_validated': False,
            'ontology_mapping': None, 'unsupported_or_ambiguous_TAB_targets': CLASSES,
            'candidate_reference': {'source': 'https://github.com/explosion/spacy-models/blob/master/meta/en_core_web_sm-3.8.0.json',
                'version': 'en_core_web_sm 3.8.0 (A2 metadata only, not installed or selected)',
                'license': 'MIT per A2 official model metadata; no local artifact/license verified',
                'native_ontology': '18 OntoNotes-derived labels; no TAB CODE/DEM/MISC; shared names not equivalent',
                'offset_convention': 'spaCy character offsets are Python Unicode code points; not locally verified',
                'limits': 'nonoverlapping token entities; English; spaCy >=3.8.0,<3.9.0 per A2 metadata',
                'runtime_check': 'package discovery only; load/inference/dependency compatibility skipped'},
            'supplied_span_artifacts': {'source': 'research/local/document_sensitivity/ds2_models_v2/',
                'version': 'tab-supplied-span-ds2-v1',
                'selection_sha256': 'f820f6eb6c0656b0aad22407cf75665d2deeaf20b95cbc679b075a81604b7477',
                'task': 'TF-IDF/LinearSVC classification of supplied entity or supplied context spans',
                'automatic_detector': False, 'loaded_or_scored': False,
                'supported_ontology': CLASSES, 'training_source_license': 'TAB MIT; repository model redistribution license not verified'},
            'required_action': 'Preregister a pinned local automatic detector and identical/native ontology contract; validate compatible CPU runtime within frozen limits before contextual scoring; do not substitute TAB classifier'}


def aggregate(rows):
    result = {'documents': len(rows), 'families': len({r['family_id'] for r in rows}),
              'processed_characters': sum(r['input_chars'] for r in rows),
              'returned_predictions': sum(r['comparison']['returned_unique_predictions'] for r in rows),
              'candidate_count_before_result_cap': sum(r['candidate_count'] for r in rows),
              'prediction_truncated_documents': sum(r['spans_truncated'] for r in rows),
              'gold_over_100_documents': sum(r['over_result_cap'] for r in rows),
              'overlapping_reference_documents': sum(r['overlapping_reference'] for r in rows),
              'reference_spans_unclipped': sum(r['comparison']['reference_spans_unclipped'] for r in rows),
              'exact_boundary_matches': sum(r['comparison']['exact_boundary_matches'] for r in rows),
              'unmatched_predictions_unreviewed': sum(r['comparison']['boundary_unmatched_predictions_unreviewed'] for r in rows),
              'duplicate_predictions': sum(r['comparison']['duplicate_predictions'] for r in rows),
              'predictions_by_kind': {k: sum(r['predictions_by_kind'].get(k, 0) for r in rows) for k in STRUCTURED},
              'matched_reference_categories_boundary_only': {c: sum(r['matched_reference_categories'].get(c, 0) for r in rows) for c in CLASSES},
              'annotated_typed_span_recovery': None, 'category_agreement': None,
              'typed_unavailable_reason': 'Structured kinds and TAB classes have no identical declared semantics; no mapping approved',
              'independent_metrics': None, 'precision': None, 'f1': None,
              'negative_coverage': 'unknown; unmatched predictions are unreviewed, not FP',
              'extraction': 'source JSON full-text only; no original container extraction measured'}
    result['exact_boundary_reference_recovery'] = ratio(result['exact_boundary_matches'], result['reference_spans_unclipped'])
    def boundary_recovery(sample):
        return ratio(sum(r['comparison']['exact_boundary_matches'] for r in sample),
                     sum(r['comparison']['reference_spans_unclipped'] for r in sample))
    result['boundary_recovery_family_interval'] = cluster_interval(rows, boundary_recovery)
    return result


def run(manifest_path, directory, protocol_path, contract_path, scope_path, output):
    output = local_path(BASE, output)
    if output.exists() or output.with_suffix('.partial').exists():
        raise ValueError('New B2 output required; preserve prior/incomplete writes')
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    manifest, documents, contract = validate_inputs(manifest_path, directory, protocol_path, contract_path)
    if hash_file(scope_path)['sha256'] != contract['human_packet']['scope_sha256']:
        raise ValueError('Preregistered human scope mismatch')
    if hash_file(Path('ml/content_detection.py'))['sha256'] != contract['detector_source_sha256']:
        raise ValueError('Fixed detector source mismatch')
    load_start = time.perf_counter()
    from ml.content_detection import VERSION as detector_version, detect_content
    cold_load = time.perf_counter() - load_start
    if detector_version != contract['detector_version']:
        raise ValueError('Fixed detector version mismatch')
    rows, statuses, timings, cpu_timings = [], Counter(), [], []
    for row in manifest['records']:
        if not row['release_reference_eligible']:
            continue
        doc = documents[row['source_document_id_sha256']]
        start, cpu = time.perf_counter(), time.process_time()
        # ONLY raw text goes into the detector; no reference spans, IDs or metadata.
        try:
            detection = detect_content(doc['text'])
        except ValueError:
            statuses['UNAVAILABLE_DETECTOR_INPUT'] += 1
            continue
        elapsed, elapsed_cpu = time.perf_counter() - start, time.process_time() - cpu
        timings.append(elapsed); cpu_timings.append(elapsed_cpu)
        statuses['AVAILABLE'] += 1
        predictions = [(s['start'], s['end'], s['kind']) for s in detection['spans']]
        references, _ = consensus(doc)
        comparison = compare_reference(predictions, references, text_length=len(doc['text']),
                                       prediction_targets=STRUCTURED, reference_targets=CLASSES)
        pbound = {(s, e) for s, e, _ in predictions}
        rows.append({'document_id_sha256': row['source_document_id_sha256'], 'family_id': row['family_id'],
            'split': row['development_split'], 'text_sha256': row['text_sha256'],
            'input_chars': len(doc['text']), 'input_bytes': len(doc['text'].encode()),
            'overlapping_reference': bool(row['overlapping_consensus_pairs']),
            'over_result_cap': row['over_result_cap'], 'spans_truncated': detection['spans_truncated'],
            'candidate_count': detection['candidate_count'], 'predictions': predictions,
            'predictions_by_kind': dict(Counter(s[2] for s in predictions)),
            'matched_reference_categories': dict(Counter(t for s, e, t in references if (s, e) in pbound)),
            'comparison': comparison, 'wall_seconds': elapsed, 'cpu_seconds': elapsed_cpu})
    partitions = {}
    for split in contract['partitions']:
        chosen = [r for r in rows if r['split'] == split]
        partitions[split] = aggregate(chosen)
        partitions[split]['strata'] = {name: aggregate(subset) for name, subset in {
            'flat_nonoverlap': [r for r in chosen if not r['overlapping_reference']],
            'overlapping_gold': [r for r in chosen if r['overlapping_reference']],
            'gold_over_result_cap': [r for r in chosen if r['over_result_cap']],
            'prediction_truncated': [r for r in chosen if r['spans_truncated']]}.items()}
    packet = blank_packet(manifest['records'], documents, protocol_sha256=PROTOCOL_SHA256,
                          manifest_sha256=MANIFEST_SHA256, scope_sha256=contract['human_packet']['scope_sha256'])
    report = {'version': VERSION, 'run_contract_sha256': CONTRACT_SHA256,
        'protocol_sha256': PROTOCOL_SHA256, 'manifest_file_sha256': MANIFEST_SHA256,
        'manifest_payload_sha256': MANIFEST_PAYLOAD, 'manifest_gate': summarize(manifest),
        'detector': {'version': detector_version, 'source_sha256': contract['detector_source_sha256'],
                     'source': 'ml/content_detection.py', 'license': 'no repository LICENSE found; no new redistribution claim',
                     'ontology': list(STRUCTURED), 'offsets': 'original Unicode code points; half-open',
                     'max_characters': 32768, 'max_bytes': 131072, 'max_returned_spans': 100,
                     'automatic_raw_text_execution': True, 'TAB_mapping': None, 'model_artifact': None},
        'lanes': {'independent': {'eligible_documents': 0, 'metrics': None,
                      'reason': 'No independently exhaustive natural target reviews; B1 eligibility remains unchanged'},
                  'release_reference': {'scope': 'cross-ontology exact-boundary diagnostic only; not eight-class detector performance',
                      'partitions': partitions},
                  'synthetic': {'evidence': 'tests/test_span_evaluation.py and tests/test_content_detection.py',
                      'real_world_performance': False, 'executed_by_this_cli': False}},
        'coverage': {'all_source_metadata': 1268, 'development_source_documents': 1141,
            'eligible_reference_inputs': 390, 'detector_status_counts': dict(statuses),
            'historical_test_excluded': 127, 'historical_test_access': 'hash only; no JSON parsing',
            'container_extraction': 'not available for source JSON; end-to-end original-container metrics unavailable',
            'excluded_documents_are_negatives': False, 'unavailable_inputs_are_negatives': False},
        'contextual_gate': contextual_gate(),
        'human_handoff': {'packet': 'span-review-pilot.json', 'purpose': packet['purpose'],
            'documents': len(packet['documents']), 'families': len({r['family_id'] for r in packet['documents']}),
            'completed_reviews': 0, 'labels_created': 0, 'custodian_authorization': None,
            'scope_sha256': contract['human_packet']['scope_sha256']},
        'resources': {'python': platform.python_version(), 'workers': 1, 'detector_threads': 1,
            'cold_detector_import_seconds': cold_load, 'warm_documents': len(timings),
            'warm_wall_median_seconds': statistics.median(timings) if timings else None,
            'warm_wall_p95_seconds': sorted(timings)[int(.95 * (len(timings) - 1))] if timings else None,
            'warm_wall_max_seconds': max(timings, default=None), 'warm_cpu_max_seconds': max(cpu_timings, default=None),
            'processed_characters': sum(r['input_chars'] for r in rows),
            'whole_harness_wall_seconds_before_write': time.perf_counter() - wall_start,
            'whole_harness_cpu_seconds_before_write': time.process_time() - cpu_start,
            'whole_process_peak_RSS_MiB': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
            'contextual_load_or_inference': 'skipped; gate blocked, no artifact loaded'},
        'boundaries': {'training_tuning_model_selection': False, 'live_activation': False,
                       'policy_or_enforcement_changes': False, 'independent_labels_fabricated': False}}
    output.mkdir(parents=True, mode=0o700)
    for name, value in [('document-results.json', rows), ('span-review-pilot.json', packet)]:
        atomic_json(output / name, value); (output / name).chmod(0o600)
    report['private_output_hashes'] = {name: hash_file(output / name) for name in ('document-results.json', 'span-review-pilot.json')}
    report['source_hashes'] = {str(p): hash_file(p) for p in map(Path,
        ['research/detection_evaluation.py', 'research/span_evaluation.py', 'research/span_review.py'])}
    atomic_json(output / 'evaluation.json', report); (output / 'evaluation.json').chmod(0o600)
    print(json.dumps({'version': VERSION, 'partitions': {s: {k: v[k] for k in
        ('documents', 'returned_predictions', 'exact_boundary_matches', 'unmatched_predictions_unreviewed')}
        for s, v in partitions.items()}, 'contextual_gate': report['contextual_gate']['status']}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, default=Path('docs/implementation/phase-a2/evaluation-protocol.json'))
    parser.add_argument('--contract', type=Path, default=Path('docs/implementation/phase-b2/run-contract.json'))
    parser.add_argument('--scope', type=Path, default=Path('docs/implementation/phase-b2/span-review-scope.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.manifest, args.directory, args.protocol, args.contract, args.scope, args.output)


if __name__ == '__main__':
    main()
