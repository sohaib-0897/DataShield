"""Synthetic evidence-lane, full-review and exact-span evaluation contracts."""
from copy import deepcopy
import json

import pytest

from ml.content_detection import detect_content
from research.detection_evaluation import run
from research.detection_manifest import text_hash
from research.independent_span_evaluation import evaluate
from research.span_evaluation import (compare_reference, cluster_interval, independent_counts,
                                      summarize_independent, evaluate_independent)
from research.span_review import (TARGETS, blank_packet, validate_document_review, validate_packet)
from research.tab_prepare import digest


def compare(predictions, gold, same=True):
    return compare_reference(predictions, gold, text_length=200,
                             prediction_targets=['PERSON', 'ORG'],
                             reference_targets=['PERSON', 'ORG'], identical_ontology=same)


def complete_review(values=None, text='😀 Alice works here'):
    values = [[2, 7, 'PERSON']] if values is None else values
    def review(key):
        return {'reviewer_id': key, 'completed_at': '2026-10-08T12:00:00+00:00',
                'independent': True, 'saw_predictions_or_release_annotations': False,
                'text_sha256': text_hash(text), 'exhaustive_targets': TARGETS.copy(),
                'spans': deepcopy(values)}
    reviews = [review('synthetic-A'), review('synthetic-B')]
    adjudication = review('synthetic-C')
    adjudication.update(review_sha256=[digest(r) for r in reviews],
                        full_text_exhaustive_check=True, unresolved_disagreements=0, disputed_spans=[])
    return {'text': text, 'text_sha256': text_hash(text), 'reviews': reviews, 'adjudication': adjudication}


def test_release_unmatched_and_wrong_type_are_unreviewed_never_precision():
    result = compare([(0, 5, 'ORG'), (10, 15, 'PERSON')], [(0, 5, 'PERSON')])
    assert result['exact_boundary_matches'] == 1
    assert result['annotated_typed_span_recovery_count'] == 0
    assert result['category_agreement_at_exact_boundaries'] == 0
    assert result['typed_unmatched_predictions_unreviewed'] == 2
    assert result['boundary_unmatched_predictions_unreviewed'] == 1
    assert not {'precision', 'f1', 'fp', 'tn'} & result.keys()


def test_duplicates_nested_gold_and_adjacency_not_relaxed():
    result = compare([(0, 10, 'ORG'), (0, 10, 'ORG'), (10, 15, 'PERSON')],
                     [(0, 10, 'ORG'), (2, 5, 'PERSON'), (15, 20, 'PERSON')])
    assert result['duplicate_predictions'] == 1
    assert result['reference_spans_unclipped'] == 3
    assert result['exact_boundary_matches'] == 1
    assert result['annotated_typed_span_recovery'] == 1 / 3


def test_cross_ontology_boundary_diagnostic_cannot_claim_category_agreement():
    result = compare_reference([(0, 5, 'email_address')], [(0, 5, 'CODE')], text_length=20,
                               prediction_targets=['email_address'], reference_targets=['CODE'])
    assert result['exact_boundary_matches'] == 1
    assert result['annotated_typed_span_recovery'] is None
    assert result['category_agreement_at_exact_boundaries'] is None
    with pytest.raises(ValueError):
        compare_reference([], [], text_length=20, prediction_targets=['email_address'],
                          reference_targets=['CODE'], identical_ontology=True)


@pytest.mark.parametrize('prediction', [[True, 2, 'PERSON'], [-1, 2, 'PERSON'],
    [1, 201, 'PERSON'], [1, 1, 'PERSON'], [1, 2, 'CODE'], [1.0, 2, 'PERSON']])
def test_invalid_offsets_and_unknown_ontology_rejected(prediction):
    with pytest.raises(ValueError):
        compare([prediction], [])


def test_empty_denominators_are_null_with_no_negative_claim():
    result = compare([], [])
    assert result['annotated_typed_span_recovery'] is None
    assert result['category_agreement_at_exact_boundaries'] is None
    assert result['unannotated_text_is_confirmed_negative'] is False


def test_unverified_absence_cannot_enter_independent_counts():
    with pytest.raises(ValueError):
        independent_counts([], {'spans': [], 'exhaustive_targets': TARGETS}, text_length=20, targets=TARGETS)


def test_unicode_offsets_review_and_wrong_category_metrics():
    row = complete_review()
    verified = validate_document_review(row)
    assert row['text'][2:7] == 'Alice'
    counts = independent_counts([(2, 7, 'ORG')], verified, text_length=len(row['text']), targets=['PERSON', 'ORG'])
    result = summarize_independent([{'family_id': 'one', 'counts': counts}], ['PERSON', 'ORG'])
    assert result['per_target']['PERSON']['fn'] == 1
    assert result['per_target']['ORG']['fp'] == 1
    assert result['micro']['f1'] == 0
    assert result['category_agreement_at_exact_boundaries'] == 0
    assert result['span_true_negatives_accuracy_specificity'] is None
    assert result['per_target']['PERSON']['average_precision'] is None


def test_reviewed_absence_document_rates_are_distinct_and_macro_excludes_undefined():
    targets = ['PERSON', 'ORG', 'MISC']
    positive = validate_document_review(complete_review())
    negative = validate_document_review(complete_review([]))
    rows = [{'family_id': 'a', 'counts': independent_counts([(2, 7, 'PERSON')], positive, text_length=18, targets=targets)},
            {'family_id': 'b', 'counts': independent_counts([(2, 7, 'ORG')], negative, text_length=18, targets=targets)}]
    result = evaluate_independent(rows, targets)
    doc = result['per_target']['ORG']['document']
    assert doc['false_positive_documents_per_1000'] == 500
    assert doc['false_positive_rate'] == .5
    assert result['macro_undefined_targets'] == ['MISC']
    assert result['macro_f1'] == .5
    assert result['intervals']['MISC/f1']['valid_replicates'] == 0
    assert result['intervals']['micro/f1']['valid_replicates'] == 2000


def test_actual_cap_keeps_all_gold_in_recall_denominator():
    tokens = [f'u{i}@example.invalid' for i in range(130)]
    text = ' '.join(tokens)
    gold, offset = [], 0
    for token in tokens:
        gold.append([offset, offset + len(token), 'email_address']); offset += len(token) + 1
    review = validate_document_review(complete_review(gold, text))
    detection = detect_content(text)
    assert detection['spans_truncated'] and detection['candidate_count'] == 130
    predictions = [(s['start'], s['end'], s['kind']) for s in detection['spans']]
    counts = independent_counts(predictions, review, text_length=len(text), targets=['email_address'])
    assert counts['targets']['email_address']['tp'] == 100
    assert counts['targets']['email_address']['fn'] == 30


def test_cluster_reproducible_whole_families_and_small_sample_null():
    rows = [{'family_id': 'a', 'v': 1}, {'family_id': 'a', 'v': 3}, {'family_id': 'b', 'v': 8}]
    def statistic(sample):
        assert sum(r['family_id'] == 'a' for r in sample) % 2 == 0
        return sum(r['v'] for r in sample) / len(sample)
    assert cluster_interval(rows, statistic) == cluster_interval(rows, statistic)
    assert cluster_interval(rows[:2], statistic)['lower'] is None
    with pytest.raises(ValueError):
        cluster_interval(rows, statistic, replicates=10)


@pytest.mark.parametrize('mutation', ['text', 'coverage', 'blindness', 'identity', 'adjudicator',
    'unresolved', 'binding', 'offset', 'duplicate', 'missing_spans', 'timestamp', 'disputes'])
def test_incomplete_or_forged_review_declarations_rejected(mutation):
    row = complete_review()
    if mutation == 'text': row['text'] += '!'
    if mutation == 'coverage': row['reviews'][0]['exhaustive_targets'].pop()
    if mutation == 'blindness': row['reviews'][0]['saw_predictions_or_release_annotations'] = True
    if mutation == 'identity': row['reviews'][1]['reviewer_id'] = row['reviews'][0]['reviewer_id']
    if mutation == 'adjudicator': row['adjudication']['reviewer_id'] = row['reviews'][0]['reviewer_id']
    if mutation == 'unresolved': row['adjudication']['unresolved_disagreements'] = 1
    if mutation == 'binding': row['adjudication']['review_sha256'] = ['0'*64, '0'*64]
    if mutation == 'offset': row['reviews'][0]['spans'][0][1] = 100
    if mutation == 'duplicate': row['reviews'][0]['spans'] *= 2
    if mutation == 'missing_spans': del row['reviews'][0]['spans']
    if mutation == 'timestamp': row['reviews'][0]['completed_at'] = '2026-10-08'
    if mutation == 'disputes': row['adjudication']['disputed_spans'] = [[0, 1, 'PERSON']]
    with pytest.raises(ValueError): validate_document_review(row)


def test_actual_conflict_can_be_resolved_without_silently_discarding_it():
    row = complete_review()
    row['reviews'][1]['spans'] = [[2, 7, 'ORG']]
    row['adjudication']['review_sha256'] = [digest(r) for r in row['reviews']]
    row['adjudication']['disputed_spans'] = [[2, 7, 'ORG'], [2, 7, 'PERSON']]
    result = validate_document_review(row)
    assert result['spans'] == [(2, 7, 'PERSON')]


def test_packet_is_blank_prediction_free_and_cannot_be_scored_as_human_truth():
    documents, records = {}, []
    for i in range(15):
        key = digest(i)
        documents[key] = {'text': '😀 Alice works here'}
        records.append({'source_document_id_sha256': key, 'family_id': key,
                        'development_split': 'validation', 'text_sha256': text_hash(documents[key]['text'])})
    packet = blank_packet(records, documents, protocol_sha256='p', manifest_sha256='m', scope_sha256='s')
    assert len(packet['documents']) == 12
    assert packet == blank_packet(list(reversed(records)), documents, protocol_sha256='p', manifest_sha256='m', scope_sha256='s')
    assert all(r['reviews'] == [None, None] and r['adjudication'] is None for r in packet['documents'])
    assert 'prediction' not in json.dumps(packet).lower()
    with pytest.raises(ValueError):
        validate_packet(packet, records, protocol_sha256='p', manifest_sha256='m', scope_sha256='s')
    packet['custodian_authorization'] = 'synthetic declaration only'
    for row in packet['documents']:
        row.update(complete_review())
    assert len(validate_packet(packet, records, protocol_sha256='p', manifest_sha256='m', scope_sha256='s')) == 12
    packet['documents'][0]['family_id'] = 'wrong'
    with pytest.raises(ValueError):
        validate_packet(packet, records, protocol_sha256='p', manifest_sha256='m', scope_sha256='s')


def test_interrupted_output_preserved_without_reading_inputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr('research.detection_evaluation.BASE', tmp_path / 'research/local')
    output = tmp_path / 'research/local/interrupted'
    output.mkdir(parents=True)
    partial = output / 'evaluation.json.partial'
    partial.write_text('incomplete evidence')
    with pytest.raises(ValueError, match='preserve'):
        run(tmp_path/'missing', tmp_path/'missing', tmp_path/'missing', tmp_path/'missing', tmp_path/'missing', output)
    assert partial.read_text() == 'incomplete evidence'


def test_private_path_escape_rejected_without_input_access(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match='research/local'):
        run(tmp_path/'missing', tmp_path/'missing', tmp_path/'missing', tmp_path/'missing', tmp_path/'missing', tmp_path/'public')


def test_independent_cli_rejects_blank_reviews_before_detector_execution(tmp_path, monkeypatch):
    root = tmp_path / 'research/local'
    root.mkdir(parents=True)
    packet = root / 'blank.json'
    packet.write_text('{}')
    monkeypatch.setattr('research.independent_span_evaluation.BASE', root)
    monkeypatch.setattr('research.independent_span_evaluation.validate_inputs',
                        lambda *args: ({'records': []}, {}, {'human_packet': {'scope_sha256': 's'}, 'detector_source_sha256': 'd'}))
    monkeypatch.setattr('research.independent_span_evaluation.hash_file',
                        lambda p: {'sha256': 's' if 'scope' in str(p) else 'd'})
    monkeypatch.setattr('ml.content_detection.detect_content', lambda *args: pytest.fail('Blank reviews must not execute detector'))
    with pytest.raises(ValueError, match='authorized'):
        evaluate(packet, root/'manifest', root/'source', root/'independent.json')
    assert not (root/'independent.json').exists()


def test_frozen_human_population_cannot_be_silently_reduced():
    documents, records = {}, []
    for i in range(3):
        key = digest(i)
        documents[key] = {'text': '😀 Alice works here'}
        records.append({'source_document_id_sha256': key, 'family_id': key,
                        'development_split': 'validation', 'text_sha256': text_hash(documents[key]['text'])})
    packet = blank_packet(records, documents, protocol_sha256='p', manifest_sha256='m', scope_sha256='s')
    packet['custodian_authorization'] = 'synthetic declaration'
    for row in packet['documents']: row.update(complete_review())
    packet['documents'].pop()
    with pytest.raises(ValueError, match='population'):
        validate_packet(packet, records, protocol_sha256='p', manifest_sha256='m', scope_sha256='s')
