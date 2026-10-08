"""B1 private metadata-only development ledger; no training, scoring or new labels."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import platform

from research.cert_ingest import atomic_json, hash_file, local_path
from research.tab_acquire import TREE_SHA256, verify_blob
from research.tab_inventory import FILES, FILE_LIMIT, REVISION, inspect_documents
from research.tab_prepare import CLASSES, consensus, digest, group_documents, normalized

VERSION = 'automatic-span-development-b1-v1'
PROTOCOL_SHA256 = 'b748d50cecad815613e8fee7abe5797aabadc48ebb5b4d5715e9f688fe95dba3'
DOCUMENTS_SHA256 = 'c090b12b6a52e0d2d029e3345ee025d52348e7c4e35d7b83ca9820e82f6bf3ae'
STRUCTURED = ('email_address', 'cnic_like', 'iban', 'credential_assignment')
TARGET_SCOPE = {
    'CODE': 'Released identifying-code spans; no exhaustive email/CNIC/IBAN/credential-kind review',
    'DATETIME': 'Released dates/times/durations; generic legal-reference years may be deliberately omitted',
    'DEM': 'Released demographic attributes; legal-professional professions/titles may be deliberately omitted',
    'LOC': 'Released anonymity-task locations; broad-category independent exhaustive review absent',
    'MISC': 'Released other person-related attributes; generic legal-reference parts may be omitted',
    'ORG': 'Released anonymity-task organizations; broad-category independent exhaustive review absent',
    'PERSON': 'Released anonymity-task people; broad-category independent exhaustive review absent',
    'QUANTITY': 'Released meaningful quantities; neither exhaustive financial prose nor policy levels',
}


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def overlap_pairs(spans):
    ends, count = [], 0
    for start, end, _ in sorted(spans):
        ends = [e for e in ends if e > start]
        count += len(ends)
        ends.append(end)
    return count


def build(documents, frozen, source_hashes, guideline_hash):
    """Reaudit train/dev relations, then conservatively merge frozen test families."""
    if len(frozen) > 2000 or len(documents) > 2000:
        raise ValueError('Document bound exceeded')
    by_id = {row['source_doc_sha256']: row for row in frozen}
    if len(by_id) != len(frozen) or any(r['official_split'] not in {'train', 'dev', 'test'} for r in frozen):
        raise ValueError('Invalid frozen document ledger')
    for split in ('train', 'dev'):
        inspect_documents([d for d in documents if d['dataset_type'] == split], split)
    actual = {digest(d['doc_id']): d for d in documents}
    expected = {k for k, r in by_id.items() if r['official_split'] != 'test'}
    if set(actual) != expected or len(actual) != len(documents):
        raise ValueError('Every train/dev source document must be accounted for exactly once')
    for key, doc in actual.items():
        row = by_id[key]
        if (row['original_record_sha256'] != digest(doc)
                or row['text_sha256'] != text_hash(doc['text'])
                or row['official_split'] != doc['dataset_type']
                or not isinstance(doc['quality_checked'], list)
                or row['reviewed_sets'] != len(doc['quality_checked'])):
            raise ValueError('Frozen provenance/review references do not match source')

    # No held-out text is parsed. The prior pinned all-source graph supplies its links.
    groups, edges, near = group_documents(documents)
    parent = {key: key for key in by_id}
    def find(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key
    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[max(a, b)] = min(a, b)
    seen = {}
    for row in frozen:
        key, value = row['source_doc_sha256'], row['group']
        if value in seen:
            union(key, seen[value])
        else:
            seen[value] = key
    seen = {}
    for doc, group in zip(documents, groups):
        key = digest(doc['doc_id'])
        if group in seen:
            union(key, seen[group])
        else:
            seen[group] = key
    # Raw-text duplicate links include historical metadata, never historical text.
    raw_seen, raw_pairs = {}, 0
    for row in frozen:
        value, key = row['text_sha256'], row['source_doc_sha256']
        if value in raw_seen:
            raw_pairs += 1
            union(key, raw_seen[value])
        else:
            raw_seen[value] = key
    members = defaultdict(list)
    for key in by_id:
        members[find(key)].append(key)
    families = {key: digest(sorted(keys)) for keys in members.values() for key in keys}
    assignments = defaultdict(set)
    for key, row in by_id.items():
        assignments[families[key]].add(row['official_split'])
    preferred = {g: 'test' if 'test' in s else 'dev' if 'dev' in s else 'train'
                 for g, s in assignments.items()}

    records = []
    for key in sorted(by_id):
        original = by_id[key]
        family = families[key]
        doc = actual.get(key)
        reasons = []
        if original['official_split'] == 'test':
            reasons.append('HISTORICAL_TEST_NEVER_DEVELOPMENT')
        elif preferred[family] == 'test':
            reasons.append('FAMILY_TOUCHES_HISTORICAL_TEST')
        if not original['retained']:
            reasons.append('ORIGINAL_DS2_FAMILY_QUARANTINE')
        if preferred[family] != original['official_split'] and preferred[family] != 'test':
            reasons.append('TRAIN_FAMILY_RESERVED_FOR_OFFICIAL_DEV')
        spans, audit, per_class = [], {}, Counter()
        if doc is not None:
            spans, audit = consensus(doc)
            if len(spans) != original['eligible_spans']:
                raise ValueError('Consensus count differs from frozen ledger')
            per_class.update(label for _, _, label in spans)
            if not doc['quality_checked']:
                reasons.append('NO_REVIEWED_ANNOTATIONS')
            if (audit.get('reviewed_boundary_or_presence_disagreements', 0)
                    or audit.get('reviewed_category_disagreements', 0)):
                reasons.append('REVIEWED_ANNOTATION_DISAGREEMENT')
            if len(doc['text']) > 32768 or len(doc['text'].encode('utf-8')) > 131072:
                reasons.append('TEXT_INPUT_BOUND_EXCEEDED')
        overlaps = overlap_pairs(spans)
        eligible = not reasons
        partition = ('validation' if original['official_split'] == 'dev' else 'train') if eligible else None
        coverage = {c: {'release_guideline_scope_intended': doc is not None and bool(doc['quality_checked']),
                        'unanimous_reference_spans': per_class[c] if doc is not None else None,
                        'coverage_scope_and_limit': TARGET_SCOPE[c],
                        'independent_exhaustive_coverage_verified': False,
                        'unannotated_text_confirmed_negative': False}
                    for c in CLASSES}
        records.append({
            'source_document_id_sha256': key,
            'source_revision': REVISION,
            'source_file': 'echr_' + original['official_split'] + '.json',
            'source_file_sha256': source_hashes['echr_' + original['official_split'] + '.json']['sha256'],
            'source_record_sha256': original['original_record_sha256'],
            'text_sha256': original['text_sha256'],
            'normalized_text_sha256': text_hash(normalized(doc['text'])) if doc else None,
            'family_id': family, 'historical_DS2_family_id': original['group'],
            'official_split': original['official_split'], 'development_split': partition,
            'family_reserved_split': preferred[family],
            'original_DS2_quarantined': not original['retained'],
            'reference_exclusion_reasons': sorted(reasons),
            'release_reference_eligible': eligible,
            'flat_nonoverlap_reference_eligible': eligible and overlaps == 0,
            'flat_subset_exclusion_reasons': sorted(reasons + (['OVERLAPPING_REFERENCE_SPANS'] if overlaps else [])),
            'independent_contextual_detection_eligible': False,
            'structured_detection_eligible': {kind: False for kind in STRUCTURED},
            'annotation_coverage': coverage,
            'reviewed_sets': original['reviewed_sets'],
            'reviewed_set_ids_sha256': digest(sorted(doc['quality_checked'])) if doc else None,
            'annotation_provenance': 'released machine-assisted human review; independence/exhaustiveness not verified',
            'guideline_sha256': guideline_hash,
            'consensus_spans': len(spans) if doc else None,
            'overlapping_consensus_pairs': overlaps if doc else None,
            'over_result_cap': len(spans) > 100 if doc else None,
            'text_characters': len(doc['text']) if doc else None,
            'text_utf8_bytes': len(doc['text'].encode('utf-8')) if doc else None,
            'source_text_complete': doc is not None,
            'extraction_coverage': 'SOURCE_JSON_TEXT_ONLY_NO_ORIGINAL_CONTAINER' if doc else 'HISTORICAL_METADATA_ONLY',
            'original_container_sha256': None,
            'external_case_version_links': 'not supplied; only release IDs/subject/applicant/text relations auditable',
            'annotation_audit': audit,
        })
    manifest = {'version': VERSION, 'protocol_sha256': PROTOCOL_SHA256,
                'source_revision': REVISION, 'source_hashes': source_hashes,
                'frozen_documents_sha256': DOCUMENTS_SHA256,
                'software': {'python': platform.python_version()},
                'model_artifact_sha256': None, 'model_selected': False,
                'ontology': {'classes': CLASSES, 'scope': 'released TAB guideline with explicit omission exceptions',
                             'guideline_sha256': guideline_hash},
                'ontology_sha256': digest({'classes': CLASSES, 'guideline_sha256': guideline_hash}),
                'configuration': {'near_duplicate_five_word_jaccard': 0.8,
                                  'split_priority': ['test', 'dev', 'train'],
                                  'disagreements': 'exclude whole document',
                                  'result_cap': 'retain all reference spans; no cap-based exclusion',
                                  'independent_coverage': 'never inferred from release review metadata'},
                'relations': {'recomputed_train_dev_edge_reasons': dict(Counter(e[2] for e in edges)),
                              'train_dev_near_duplicate_pairs': near,
                              'raw_exact_duplicate_links_all_source_metadata': raw_pairs,
                              'historical_test_text_parsed': False,
                              'historical_family_graph': 'pinned DS2 all-source groups; conservatively merged with fresh train/dev audit'},
                'records': records, 'training_or_scoring': False, 'live_activation': False}
    manifest['configuration_sha256'] = digest(manifest['configuration'])
    manifest['software_sha256'] = digest(manifest['software'])
    manifest['payload_sha256'] = digest(manifest)
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest):
    """Reject corruption, split leakage and fabricated independent eligibility."""
    payload = {k: v for k, v in manifest.items() if k != 'payload_sha256'}
    if (manifest.get('version') != VERSION or manifest.get('protocol_sha256') != PROTOCOL_SHA256
            or manifest.get('payload_sha256') != digest(payload)
            or manifest.get('configuration_sha256') != digest(manifest['configuration'])
            or manifest.get('software_sha256') != digest(manifest['software'])
            or manifest['ontology']['classes'] != CLASSES
            or manifest.get('ontology_sha256') != digest({'classes': CLASSES,
                'guideline_sha256': manifest['ontology']['guideline_sha256']})
            or manifest.get('model_selected') is not False
            or manifest.get('training_or_scoring') is not False
            or manifest.get('live_activation') is not False):
        raise ValueError('Manifest digest or task boundary mismatch')
    ids, groups, source_splits = set(), defaultdict(set), defaultdict(set)
    for row in manifest['records']:
        if row['official_split'] not in {'train', 'dev', 'test'}:
            raise ValueError('Invalid official split')
        source_splits[row['family_id']].add(row['official_split'])
    reserved = {g: 'test' if 'test' in s else 'dev' if 'dev' in s else 'train'
                for g, s in source_splits.items()}
    for row in manifest['records']:
        key = row['source_document_id_sha256']
        if key in ids:
            raise ValueError('Duplicate manifest document')
        ids.add(key)
        if (set(row['annotation_coverage']) != set(CLASSES)
                or set(row['structured_detection_eligible']) != set(STRUCTURED)
                or row['guideline_sha256'] != manifest['ontology']['guideline_sha256']):
            raise ValueError('Incomplete target coverage/ontology declaration')
        if row['family_reserved_split'] != reserved[row['family_id']]:
            raise ValueError('Family reservation disagrees with all-source metadata')
        if (row['independent_contextual_detection_eligible'] is not False
                or any(row['structured_detection_eligible'].values())
                or any(c['independent_exhaustive_coverage_verified']
                       or c['unannotated_text_confirmed_negative'] for c in row['annotation_coverage'].values())):
            raise ValueError('Independent exhaustive coverage is unavailable')
        eligible = row['release_reference_eligible']
        if type(eligible) is not bool or eligible != (not row['reference_exclusion_reasons']):
            raise ValueError('Exclusion/eligibility mismatch')
        if eligible:
            expected = 'validation' if row['official_split'] == 'dev' else 'train'
            if (row['official_split'] == 'test' or row['family_reserved_split'] == 'test'
                    or row['original_DS2_quarantined'] or row['reviewed_sets'] < 1
                    or not row['source_text_complete'] or row['text_characters'] > 32768
                    or row['text_utf8_bytes'] > 131072
                    or row['development_split'] != expected
                    or row['family_reserved_split'] != row['official_split']
                    or row['annotation_audit'].get('reviewed_boundary_or_presence_disagreements', 0)
                    or row['annotation_audit'].get('reviewed_category_disagreements', 0)):
                raise ValueError('Invalid development eligibility')
            groups[row['family_id']].add(expected)
        elif row['development_split'] is not None:
            raise ValueError('Excluded document has a development split')
        if row['flat_nonoverlap_reference_eligible'] != (eligible and row['overlapping_consensus_pairs'] == 0):
            raise ValueError('Flat subset silently flattens or drops overlap')
    if any(len(splits) != 1 for splits in groups.values()):
        raise ValueError('Cross-split family leakage')
    return True


def summarize(manifest):
    validate_manifest(manifest)
    rows = manifest['records']
    all_reasons = Counter(reason for r in rows for reason in r['reference_exclusion_reasons'])
    partitions = {}
    for split in ('train', 'validation'):
        chosen = [r for r in rows if r['development_split'] == split]
        flat = [r for r in chosen if r['flat_nonoverlap_reference_eligible']]
        partitions[split] = {'release_reference_documents': len(chosen),
                             'release_reference_families': len({r['family_id'] for r in chosen}),
                             'reference_spans_unclipped': sum(r['consensus_spans'] for r in chosen),
                             'flat_nonoverlap_documents': len(flat),
                             'over_result_cap_documents': sum(r['over_result_cap'] for r in chosen),
                             'class_reference_spans': {c: sum(r['annotation_coverage'][c]['unanimous_reference_spans']
                                                            for r in chosen) for c in CLASSES}}
    return {'version': VERSION, 'protocol_sha256': PROTOCOL_SHA256,
            'manifest_payload_sha256': manifest['payload_sha256'],
            'source_documents_accounted_for': len(rows),
            'development_source_documents': sum(r['official_split'] != 'test' for r in rows),
            'historical_test_documents_excluded': sum(r['official_split'] == 'test' for r in rows),
            'release_reference_eligible': sum(r['release_reference_eligible'] for r in rows),
            'excluded_all_source': sum(not r['release_reference_eligible'] for r in rows),
            'excluded_development_source': sum(not r['release_reference_eligible'] and r['official_split'] != 'test' for r in rows),
            'independent_exhaustive_contextual_eligible': 0,
            'independent_structured_eligible': {k: 0 for k in STRUCTURED},
            'reason_counts_nonexclusive': dict(all_reasons),
            'primary_exclusive_reason_counts': dict(Counter(r['reference_exclusion_reasons'][0] if r['reference_exclusion_reasons']
                                                           else 'RELEASE_REFERENCE_ELIGIBLE' for r in rows)),
            'all_source_families': len({r['family_id'] for r in rows}),
            'test_related_development_by_official_split': dict(Counter(r['official_split'] for r in rows
                if 'FAMILY_TOUCHES_HISTORICAL_TEST' in r['reference_exclusion_reasons'])),
            'original_DS2_quarantined_documents': sum(r['original_DS2_quarantined'] for r in rows),
            'eligible_family_split_overlap': 0, 'partitions': partitions,
            'relations': manifest['relations'],
            'independent_negative_coverage_verified': False,
            'reference_scope': 'TAB release-relative legal anonymity guideline; not exhaustive broad NER',
            'per_target_coverage_scope': TARGET_SCOPE,
            'missing_structured_kind_annotations': list(STRUCTURED),
            'training_or_scoring': False, 'live_activation': False}


def create(directory, tree_path, frozen_path, protocol_path, output):
    root = Path('research/local').absolute()
    directory, tree_path, frozen_path, output = [local_path(root, p) for p in
                                               (directory, tree_path, frozen_path, output)]
    if output.exists():
        raise ValueError('New output directory required; preserve existing manifests')
    if hash_file(protocol_path)['sha256'] != PROTOCOL_SHA256:
        raise ValueError('Frozen B protocol mismatch')
    if hash_file(tree_path)['sha256'] != TREE_SHA256 or hash_file(frozen_path)['sha256'] != DOCUMENTS_SHA256:
        raise ValueError('Pinned source tree or historical family ledger mismatch')
    tree = json.loads(tree_path.read_text())
    if tree.get('sha') != REVISION or tree.get('truncated') is not False:
        raise ValueError('Pinned tree revision mismatch')
    entries = [e for e in tree['tree'] if e['path'] in FILES]
    if len(entries) != len(FILES) or {e['path'] for e in entries} != set(FILES):
        raise ValueError('Incomplete source file inventory')
    hashes = {}
    for entry in entries:
        if entry['type'] != 'blob' or not 0 < entry['size'] <= FILE_LIMIT:
            raise ValueError('Source file bound exceeded')
        hashes[entry['path']] = verify_blob(local_path(root, directory / entry['path']), entry)
    documents = []
    for split in ('train', 'dev'):
        value = json.loads(local_path(root, directory / f'echr_{split}.json').read_text())
        if not isinstance(value, list) or len(value) > 2000:
            raise ValueError('Source document bound exceeded')
        documents.extend(value)
    manifest = build(documents, json.loads(frozen_path.read_text()), hashes, hashes['guidelines.md']['sha256'])
    # Recheck pinned inputs before publication; never accept a mid-read source change.
    for name, expected in hashes.items():
        if hash_file(local_path(root, directory / name)) != expected:
            raise ValueError('Source changed during audit')
    if hash_file(frozen_path)['sha256'] != DOCUMENTS_SHA256 or hash_file(protocol_path)['sha256'] != PROTOCOL_SHA256:
        raise ValueError('Frozen contract changed during audit')
    output.mkdir(mode=0o700)
    atomic_json(output / 'manifest.json', manifest)
    (output / 'manifest.json').chmod(0o600)
    report = summarize(manifest)
    report['manifest_file'] = hash_file(output / 'manifest.json')
    atomic_json(output / 'audit.json', report)
    (output / 'audit.json').chmod(0o600)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--tree', required=True, type=Path)
    parser.add_argument('--frozen-documents', required=True, type=Path)
    parser.add_argument('--protocol', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(create(args.directory, args.tree, args.frozen_documents, args.protocol, args.output)))


if __name__ == '__main__':
    main()
