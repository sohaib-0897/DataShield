"""Synthetic fixtures verify schema/guards only; no performance measurement."""
from copy import deepcopy
import hashlib
import json
import zipfile

import pytest

from research import document_annotation as annotation
from research import tab_inventory as tab


def review(name, categories=None, level=None):
    return {'reviewer_id': name, 'label_origin': 'independent_human',
            'categories': categories or [], 'organizational_level': level, 'context': None}


def blank(tmp_path):
    path = tmp_path / 'public.txt'
    path.write_text('Public contact: test@example.invalid. Published revenue: 100.')
    return annotation.packet(path, source_id='synthetic-source', family_id='synthetic-family', policy_version='fixture-v1')


def context():
    return dict(owner_review_id='synthetic-owner-review', policy_version='fixture-v1',
                authorized_audience='public', release_status='approved_public', harm_rationale='approved publication')


def test_packet_never_infers_categories_or_normal_from_public_email(tmp_path):
    value = blank(tmp_path)
    assert value['status'] == 'AWAITING_INDEPENDENT_REVIEWS'
    assert not value['training_eligible']
    assert all(r['categories'] is None and r['organizational_level'] is None for r in value['reviews'])
    with pytest.raises(ValueError, match='Reviewer'):
        annotation.adjudicate(value)


def test_category_only_human_review_keeps_organizational_level_unknown(tmp_path):
    value = blank(tmp_path)
    value['reviews'] = [review(n, ['PERSONAL_INFORMATION', 'FINANCIAL_INFORMATION']) for n in ('one', 'two')]
    result = annotation.adjudicate(value)
    assert result['category_training_eligible'] and not result['organizational_training_eligible']
    assert result['organizational_level'] is None and value['training_eligible'] is False


@pytest.mark.parametrize('level', ['NORMAL', 'HIGH', 'CRITICAL'])
def test_all_policy_levels_require_context_even_normal(tmp_path, level):
    value = blank(tmp_path)
    value['reviews'] = [review(n, level=level) for n in ('one', 'two')]
    with pytest.raises(ValueError, match='context'):
        annotation.adjudicate(value)
    for r in value['reviews']:
        r['context'] = context()
    assert annotation.adjudicate(value)['organizational_level'] == level


def test_business_confidential_requires_context(tmp_path):
    value = blank(tmp_path)
    value['reviews'] = [review(n, ['BUSINESS_CONFIDENTIAL']) for n in ('one', 'two')]
    with pytest.raises(ValueError, match='context'):
        annotation.adjudicate(value)


@pytest.mark.parametrize('origin', ['rule', 'model', 'CERT', 'synthetic_fixture'])
def test_nonhuman_origins_are_not_ground_truth(tmp_path, origin):
    value = blank(tmp_path)
    value['reviews'] = [review(n) for n in ('one', 'two')]
    value['reviews'][0]['label_origin'] = origin
    with pytest.raises(ValueError, match='independent human'):
        annotation.adjudicate(value)


def test_disagreement_requires_distinct_third_reviewer_and_reason(tmp_path):
    value = blank(tmp_path)
    value['reviews'] = [review('one'), review('two', ['PERSONAL_INFORMATION'])]
    with pytest.raises(ValueError, match='adjudication'):
        annotation.adjudicate(value)
    value['adjudication'] = dict(review('one'), reason='fixture explanation')
    with pytest.raises(ValueError, match='third reviewer'):
        annotation.adjudicate(value)
    value['adjudication'] = dict(review('three', ['PERSONAL_INFORMATION']), reason='fixture explanation')
    assert annotation.adjudicate(value)['categories'] == ['PERSONAL_INFORMATION']


@pytest.mark.parametrize('mutation', ['digest', 'truncated', 'status', 'same_reviewer', 'policy'])
def test_annotation_provenance_and_extraction_guards(tmp_path, mutation):
    value = blank(tmp_path)
    value['reviews'] = [review(n, level='NORMAL') for n in ('one', 'two')]
    for r in value['reviews']:
        r['context'] = context()
    if mutation == 'digest':
        value['text'] += 'changed'
    elif mutation == 'truncated':
        value['truncated'] = True
    elif mutation == 'status':
        value['extraction_status'] = 'SCANNED_OR_NO_TEXT'
    elif mutation == 'same_reviewer':
        value['reviews'][1]['reviewer_id'] = 'one'
    else:
        value['reviews'][0]['context']['policy_version'] = 'different'
    with pytest.raises(ValueError):
        annotation.adjudicate(value)


def doc(split='train'):
    return {'doc_id': 'synthetic-doc', 'text': 'Person', 'dataset_type': split,
            'task': 'synthetic task', 'meta': {}, 'quality_checked': ['reviewer'],
            'annotations': {'reviewer': {'entity_mentions': [
                {'entity_type': 'PERSON', 'identifier_type': 'DIRECT', 'confidential_status': None,
                 'start_offset': 0, 'end_offset': 6, 'span_text': 'Person', 'entity_mention_id': 'mention'}]}}}


def test_inventory_aggregates_only_no_private_text_ids_or_reviewers():
    report, ids, texts = tab.inspect_documents([doc()], 'train')
    assert report['counts']['quality_reviewed_annotation_sets'] == 1
    assert report['entity_type_annotation_counts'] == {'PERSON': 1}
    assert ids == {'synthetic-doc'} and len(texts) == 1
    assert all(s not in json.dumps(report) for s in ('synthetic-doc', 'reviewer', 'Person'))


@pytest.mark.parametrize('mutation', ['offset', 'label', 'duplicate_id', 'quality'])
def test_invalid_upstream_schema_fails_closed(mutation):
    value = doc()
    documents = [value]
    mention = value['annotations']['reviewer']['entity_mentions'][0]
    if mutation == 'offset':
        mention['end_offset'] = 5
    elif mutation == 'label':
        mention['entity_type'] = 'SENSITIVE'
    elif mutation == 'duplicate_id':
        documents += [deepcopy(value)]
    else:
        value['quality_checked'] = ['missing-reviewer']
    with pytest.raises(ValueError):
        tab.inspect_documents(documents, 'train')


def archive_fixture(tmp_path, bad_hash=False):
    archive = tmp_path / 'source.zip'
    tree = {'sha': tab.REVISION, 'truncated': False, 'tree': []}
    with zipfile.ZipFile(archive, 'w') as stream:
        for name in tab.FILES:
            body = b'The MIT License' if name == 'LICENSE.txt' else b'{}'
            stream.writestr(f'text-anonymization-benchmark-{tab.REVISION}/{name}', body)
            tree['tree'].append({'path': name, 'size': len(body),
                                 'sha': hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()})
    if bad_hash:
        tree['tree'][0]['sha'] = '0' * 40
    tree_path = tmp_path / 'tree.json'
    tree_path.write_text(json.dumps(tree))
    return archive, tree_path


def test_archive_hash_mismatch_never_publishes_destination(tmp_path):
    archive, tree = archive_fixture(tmp_path, bad_hash=True)
    output = tmp_path / 'acquired'
    with pytest.raises(ValueError, match='blob mismatch'):
        tab.import_archive(archive, tree, output, tmp_path)
    assert not output.exists()


def test_archive_only_imports_reviewed_members_and_preserves_outputs(tmp_path):
    archive, tree = archive_fixture(tmp_path)
    with zipfile.ZipFile(archive, 'a') as stream:
        stream.writestr('../escape.py', 'not executed')
    output = tmp_path / 'acquired'
    manifest = tab.import_archive(archive, tree, output, tmp_path)
    assert set(p.name for p in output.iterdir()) == set(tab.FILES) | {'acquisition.json'}
    assert len(manifest['files']) == 6 and not (tmp_path.parent / 'escape.py').exists()
    with pytest.raises(ValueError, match='Preserve'):
        tab.import_archive(archive, tree, output, tmp_path)
    (output / 'README.md').write_text('modified')
    with pytest.raises(ValueError, match='changed'):
        tab.inventory(output, tmp_path)


def test_inventory_exposes_cross_split_overlap_without_training_approval(tmp_path):
    output = tmp_path / 'acquired'
    output.mkdir()
    entries = []
    for name in tab.FILES:
        if name.startswith('echr_'):
            split = name.removeprefix('echr_').removesuffix('.json')
            body = json.dumps([doc(split)]).encode()
        else:
            body = b'The MIT License'
        (output / name).write_bytes(body)
        entries.append({'file': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
                        'url': f'https://raw.githubusercontent.com/NorskRegnesentral/text-anonymization-benchmark/{tab.REVISION}/{name}'})
    (output / 'acquisition.json').write_text(json.dumps(
        {'repository': tab.REPOSITORY, 'revision': tab.REVISION, 'license': 'MIT', 'files': entries}))
    report = tab.inventory(output, tmp_path)
    for split in ('dev', 'test'):
        assert report['splits_as_supplied_not_training_approved'][split]['shared_exact_texts_with_earlier_splits'] == 1
        assert report['splits_as_supplied_not_training_approved'][split]['shared_document_ids_with_earlier_splits'] == 1
    assert not report['training_performed'] and not report['validation_performed']
    assert report['near_duplicate_case_family_audit'] == 'PENDING_DS2'
