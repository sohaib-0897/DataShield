"""Synthetic B1 ledger guards, never detector performance or human review evidence."""
from copy import deepcopy
import json

import pytest

from research.detection_manifest import build, summarize, validate_manifest, text_hash
from research.tab_prepare import consensus, digest


def doc(key, split='train', text='Alice works here', reviewed=True, subject=None):
    mention = {'entity_type': 'PERSON', 'start_offset': 0, 'end_offset': 5,
               'span_text': text[:5], 'identifier_type': 'DIRECT',
               'confidential_status': None, 'entity_mention_id': 'one'}
    return {'doc_id': key, 'dataset_type': split, 'text': text,
            'quality_checked': ['one'] if reviewed else [],
            'task': subject or key, 'meta': {'applicant': subject or key},
            'annotations': {'one': {'entity_mentions': [mention]}}}


def frozen_row(doc, group=None, retained=True):
    return {'source_doc_sha256': digest(doc['doc_id']), 'text_sha256': text_hash(doc['text']),
            'original_record_sha256': digest(doc), 'group': group or digest(doc['doc_id']),
            'official_split': doc['dataset_type'], 'retained': retained,
            'reviewed_sets': len(doc['quality_checked']), 'eligible_spans': len(consensus(doc)[0])}


def manifest(documents=None, historical=None):
    if documents is None:
        documents = [doc('alpha'), doc('beta', 'dev', 'Other completely different corpus')]
    rows = [frozen_row(d) for d in documents]
    rows += historical or []
    hashes = {'echr_' + s + '.json': {'sha256': digest(s), 'bytes': 1} for s in ('train', 'dev', 'test')}
    return build(documents, rows, hashes, '0' * 64)


def resign(value):
    value['payload_sha256'] = digest({k: v for k, v in value.items() if k != 'payload_sha256'})


def test_absent_reference_class_never_confirms_negative_or_exhaustive_coverage():
    value = manifest()
    row = next(r for r in value['records'] if r['official_split'] == 'train')
    assert row['release_reference_eligible']
    assert row['annotation_coverage']['CODE']['unanimous_reference_spans'] == 0
    assert not row['annotation_coverage']['CODE']['unannotated_text_confirmed_negative']
    assert not row['independent_contextual_detection_eligible']
    assert not any(row['structured_detection_eligible'].values())
    assert summarize(value)['independent_exhaustive_contextual_eligible'] == 0


def test_zero_mention_reviewed_document_is_retained_only_as_release_reference():
    documents = [doc('alpha'), doc('beta', 'dev', 'Other independent words')]
    documents[0]['annotations']['one']['entity_mentions'] = []
    value = manifest(documents)
    row = next(r for r in value['records'] if r['official_split'] == 'train')
    assert row['consensus_spans'] == 0 and row['release_reference_eligible']
    assert all(not c['unannotated_text_confirmed_negative'] for c in row['annotation_coverage'].values())


def test_no_raw_text_reviewer_or_subject_leaks_and_build_is_read_only():
    documents = [doc('private-case', subject='private-person'),
                 doc('private-other', 'dev', 'Other unrelated corpus')]
    documents[0]['annotations']['private-reviewer'] = documents[0]['annotations'].pop('one')
    documents[0]['quality_checked'] = ['private-reviewer']
    before = deepcopy(documents)
    value = manifest(documents)
    encoded = json.dumps(value)
    assert documents == before
    for secret in ('private-case', 'private-person', 'private-reviewer', documents[0]['text'],
                   '"span_text":', '"applicant":'):
        assert secret not in encoded
    assert value['training_or_scoring'] is False and value['model_selected'] is False


def test_historical_test_family_blocks_train_without_loading_test_text():
    documents = [doc('alpha'), doc('beta', 'dev', 'Other unrelated corpus')]
    old = frozen_row(doc('held-out', 'test', 'Historical never parsed'))
    old['group'] = digest('alpha')
    value = manifest(documents, [old])
    row = next(r for r in value['records'] if r['official_split'] == 'train')
    assert not row['release_reference_eligible']
    assert 'FAMILY_TOUCHES_HISTORICAL_TEST' in row['reference_exclusion_reasons']
    assert value['relations']['historical_test_text_parsed'] is False
    assert next(r for r in value['records'] if r['official_split'] == 'test')['consensus_spans'] is None


def test_exact_and_normalized_near_versions_are_grouped_with_dev_winning():
    documents = [doc('alpha', text='Alpha Beta Gamma Delta Epsilon Zeta'),
                 doc('beta', 'dev', 'alpha BETA gamma delta epsilon zeta!')]
    value = manifest(documents)
    assert len({r['family_id'] for r in value['records']}) == 1
    assert value['relations']['train_dev_near_duplicate_pairs'] == 1
    assert summarize(value)['partitions']['train']['release_reference_documents'] == 0
    assert summarize(value)['partitions']['validation']['release_reference_documents'] == 1


def test_transitive_subject_link_preserves_test_quarantine_across_version():
    documents = [doc('alpha', subject='shared-person'),
                 doc('beta', 'dev', 'Other unrelated corpus', subject='shared-person')]
    old = frozen_row(doc('held-out', 'test', 'Historical never parsed'))
    old['group'] = digest('alpha')
    value = manifest(documents, [old])
    assert len({r['family_id'] for r in value['records']}) == 1
    assert summarize(value)['release_reference_eligible'] == 0


@pytest.mark.parametrize('case', ['unreviewed', 'presence', 'category', 'too_long'])
def test_whole_document_exclusion_prevents_partial_gold_negatives(case):
    documents = [doc('alpha'), doc('beta', 'dev', 'Other unrelated corpus')]
    d = documents[0]
    if case == 'unreviewed':
        d['quality_checked'] = []
    elif case == 'too_long':
        d['text'] += ' ' * 32768
    else:
        d['quality_checked'].append('two')
        d['annotations']['two'] = deepcopy(d['annotations']['one'])
        if case == 'presence':
            d['annotations']['two']['entity_mentions'] = []
        else:
            d['annotations']['two']['entity_mentions'][0]['entity_type'] = 'ORG'
    value = manifest(documents)
    row = next(r for r in value['records'] if r['official_split'] == 'train')
    assert not row['release_reference_eligible'] and row['development_split'] is None


def test_overlap_subset_does_not_drop_gold_and_result_cap_does_not_select_population():
    text = ' '.join(['Alice'] * 101)
    documents = [doc('alpha', text=text), doc('beta', 'dev', 'Other unrelated corpus')]
    spans = documents[0]['annotations']['one']['entity_mentions']
    spans[:] = [dict(spans[0], start_offset=i * 6, end_offset=i * 6 + 5,
                     entity_mention_id=str(i)) for i in range(101)]
    spans.append(dict(spans[0], end_offset=11, span_text=text[:11],
                      entity_type='ORG', entity_mention_id='nested'))
    value = manifest(documents)
    row = next(r for r in value['records'] if r['official_split'] == 'train')
    assert row['release_reference_eligible'] and row['over_result_cap']
    assert row['consensus_spans'] == 102
    assert not row['flat_nonoverlap_reference_eligible']
    assert 'OVERLAPPING_REFERENCE_SPANS' in row['flat_subset_exclusion_reasons']


@pytest.mark.parametrize('mutation', ['coverage', 'test_split', 'split_leak', 'digest', 'ontology', 'missing_target'])
def test_manifest_integrity_and_semantic_guards(mutation):
    value = manifest()
    row = value['records'][0]
    if mutation == 'coverage':
        row['annotation_coverage']['CODE']['unannotated_text_confirmed_negative'] = True
    elif mutation == 'test_split':
        row['official_split'] = 'test'
    elif mutation == 'split_leak':
        value['records'][1]['family_id'] = row['family_id']
    elif mutation == 'ontology':
        value['ontology']['classes'] = ['NORMAL']
    elif mutation == 'missing_target':
        del row['annotation_coverage']['CODE']
    else:
        row['reviewed_sets'] += 1
    if mutation != 'digest':
        resign(value)
    with pytest.raises(ValueError):
        validate_manifest(value)


def test_original_frozen_record_changes_and_missing_docs_rejected():
    documents = [doc('alpha'), doc('beta', 'dev', 'Other unrelated corpus')]
    rows = [frozen_row(d) for d in documents]
    rows[0]['original_record_sha256'] = '0' * 64
    hashes = {'echr_' + s + '.json': {'sha256': digest(s)} for s in ('train', 'dev', 'test')}
    with pytest.raises(ValueError, match='provenance'):
        build(documents, rows, hashes, '0' * 64)
    with pytest.raises(ValueError, match='accounted'):
        build(documents, rows + [frozen_row(doc('absent'))], hashes, '0' * 64)


def test_cli_preserves_existing_manifest_directory_before_any_source_read(tmp_path, monkeypatch):
    from research.detection_manifest import create
    monkeypatch.chdir(tmp_path)
    root = tmp_path / 'research/local'
    output = root / 'existing'
    output.mkdir(parents=True)
    manifest_file = output / 'manifest.json'
    manifest_file.write_bytes(b'incomplete user-owned diagnostic artifact')
    before = manifest_file.read_bytes()
    with pytest.raises(ValueError, match='preserve existing'):
        create(root / 'source', root / 'tree', root / 'frozen', tmp_path / 'protocol', output)
    assert manifest_file.read_bytes() == before
