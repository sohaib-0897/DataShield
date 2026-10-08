"""Synthetic annotation integrity fixtures, never natural-corpus performance."""
from copy import deepcopy
import hashlib
import json

import pytest

from research.contextual_feasibility import screen
from research import contextual_feasibility as feasibility


def document(text='😀 Alice Acme', reviewed=None):
    return {'doc_id': 'fixture', 'text': text, 'dataset_type': 'train',
            'quality_checked': ['one'] if reviewed is None else reviewed,
            'task': 'fixture-subject', 'meta': {}, 'annotations': {'one': {
                'entity_mentions': [mention(text, 2, 7)]}}}


def mention(text, start, end, label='PERSON', identifier='one'):
    return {'entity_type': label, 'start_offset': start, 'end_offset': end,
            'span_text': text[start:end], 'identifier_type': 'DIRECT',
            'confidential_status': None, 'entity_mention_id': identifier}


def test_reviewed_presence_disagreement_is_not_a_negative_or_training_gate():
    doc = document(reviewed=['one', 'two'])
    doc['annotations']['two'] = {'entity_mentions': []}
    original = deepcopy(doc)
    result = screen([doc], 'train')
    assert result['screening']['documents_with_reviewed_disagreement'] == 1
    assert result['screening']['consensus_spans'] == 0
    assert result['independent_exhaustiveness_verified'] is False
    assert result['unannotated_text_is_verified_negative'] is False
    assert doc == original


def test_unicode_offsets_and_nested_spans_preserved_but_adjacency_not_overlap():
    doc = document()
    doc['annotations']['one']['entity_mentions'] += [
        mention(doc['text'], 2, 12, 'ORG', 'two'),
        mention(doc['text'], 7, 12, 'MISC', 'three')]
    result = screen([doc], 'train')['screening']
    assert result['consensus_spans'] == 3
    assert result['consensus_overlap_pairs'] == 2
    assert result['documents_with_consensus_overlap'] == 1


@pytest.mark.parametrize('corruption', ['offset', 'text', 'reviewer', 'boolean_offset'])
def test_invalid_annotations_fail_before_reporting(corruption):
    doc = document()
    span = doc['annotations']['one']['entity_mentions'][0]
    if corruption == 'offset':
        span['end_offset'] = 100
    elif corruption == 'text':
        span['span_text'] = 'unbound annotation'
    elif corruption == 'boolean_offset':
        span['start_offset'] = True
    else:
        doc['quality_checked'] = ['absent-reviewer']
    with pytest.raises(ValueError):
        screen([doc], 'train')


def test_unreviewed_source_and_long_text_never_silently_become_eligible():
    doc = document(reviewed=[])
    result = screen([doc], 'train')
    assert result['screening']['unreviewed_documents'] == 1
    assert result['screening']['consensus_spans'] == 0
    doc = document('😀 Alice Acme' + ' ' * 32768)
    assert screen([doc], 'train')['screening']['reviewed_documents_over_text_bound'] == 1


def test_candidate_return_bound_does_not_drop_gold():
    text = ' '.join(['Alice'] * 101)
    doc = document(text)
    doc['annotations']['one']['entity_mentions'] = [
        mention(text, i * 6, i * 6 + 5, identifier=str(i)) for i in range(101)]
    result = screen([doc], 'train')['screening']
    assert result['consensus_spans'] == 101
    assert result['reviewed_documents_over_result_bound'] == 1


def pinned_fixture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / 'research/local'
    source = root / 'source'
    source.mkdir(parents=True)
    entries = []
    for name in feasibility.FILES:
        if name in ('echr_train.json', 'echr_dev.json'):
            doc = document()
            doc['dataset_type'] = 'dev' if 'dev' in name else 'train'
            content = json.dumps([doc]).encode()
        else:
            # Deliberately non-JSON test: bytes must verify without being parsed.
            content = b'inert synthetic provenance fixture'
        (source / name).write_bytes(content)
        blob = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content)
        entries.append({'path': name, 'type': 'blob', 'size': len(content),
                        'sha': blob.hexdigest()})
    tree = root / 'tree.json'
    tree.write_text(json.dumps({'sha': feasibility.REVISION, 'truncated': False,
                               'tree': entries}))
    monkeypatch.setattr(feasibility, 'TREE_SHA256', hashlib.sha256(tree.read_bytes()).hexdigest())
    return source, tree


def test_test_partition_is_hash_only_and_assessment_leaves_sources_unchanged(tmp_path, monkeypatch):
    source, tree = pinned_fixture(tmp_path, monkeypatch)
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    result = feasibility.assess(source, tree)
    assert result['test_access'] == 'hash only; no test JSON parsed'
    assert set(result['splits']) == {'train', 'dev'}
    assert result['labels_created'] == 0 and result['model_selected'] is False
    assert before == {p.name: p.read_bytes() for p in source.iterdir()}


@pytest.mark.parametrize('corruption', ['short_write', 'same_size_corruption'])
def test_partial_and_corrupt_pinned_sources_rejected_without_repair(tmp_path, monkeypatch, corruption):
    source, tree = pinned_fixture(tmp_path, monkeypatch)
    path = source / 'echr_train.json'
    content = path.read_bytes()
    damaged = content[:-1] if corruption == 'short_write' else b'x' + content[1:]
    path.write_bytes(damaged)
    with pytest.raises(ValueError):
        feasibility.assess(source, tree)
    assert path.read_bytes() == damaged


def test_source_paths_cannot_escape_private_root(tmp_path, monkeypatch):
    source, tree = pinned_fixture(tmp_path, monkeypatch)
    outside = tmp_path / 'outside'
    outside.mkdir()
    with pytest.raises(ValueError):
        feasibility.assess(outside, tree)
