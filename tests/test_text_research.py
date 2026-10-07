from datetime import datetime, timedelta
import json

import pytest

from ml.features.windows import CHANNELS, build_windows
from research import text_study as text
from research.behavioral_ml import chronological_split


def sample_study():
    base = datetime(2010, 1, 4, 8)
    events = []
    # Identity-disjoint times and different keyword bags across partitions.
    extra = ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot']
    for hour in range(6):
        for user in range(4):
            malicious = user >= 2
            content = ('suspicious secret export' if malicious else 'ordinary project meeting') + ' ' + extra[hour] + ' ' + ['able', 'baker', 'calm', 'deft'][user]
            events.append({'dataset_sha256': 'd', 'source_file': 'http.csv', 'source_id': f'{hour}-{user}',
                           'username': f'{hour}-{user}', 'pc': 'pc', 'channel': 'HTTP',
                           'timestamp_local': (base + timedelta(hours=hour, minutes=10)).isoformat(),
                           'metadata_json': json.dumps({'content': content})})
    ws = build_windows(events, {c: (base, base + timedelta(hours=6)) for c in CHANNELS})
    for w in ws:
        h, u = map(int, w['user'].split('-'))
        w['label'] = int(u >= 2)
        scenario = '1' if h < 3 else '2' if h < 4 else '3'
        w['label_provenance'] = [{'scenario': scenario, 'incident': 'i' + scenario}] if w['label'] else []
    features = {'windows': ws, 'artifact_sha256': 'f', 'store_sha256': 's', 'dataset_sha256': 'd'}
    numeric = {'feature_artifact_sha256': 'f', 'store_sha256': 's', 'splits': chronological_split(ws)[1]}
    return features, events, numeric


def test_sanitizer_keeps_topic_words_and_removes_identity_resources_header():
    normalized = text.normalize_keywords('d0cf11e0a1b11ae1 ABC1234 PC-1234 user@example.invalid http://example.invalid secret project {EVENT-ID}', file_content=True)
    assert normalized == 'secret project'
    assert text.normalize_keywords('Project 123abc') == 'project'


def test_identity_duplicate_and_scenario_leakage_controls():
    features, events, _ = sample_study()
    splits = chronological_split(features['windows'])[0]
    splits = {k: text.attach_text(v, events) for k, v in splits.items()}
    # Duplicate text bag in a new identity is rejected even if order differs.
    duplicate = dict(splits['train'][0], user='new', text='reordered words')
    identity = dict(splits['validation'][0], user=splits['train'][1]['user'])
    splits['validation'].extend([duplicate, identity])
    clean, audit = text.leakage_control(splits)
    assert audit['partitions']['validation']['removed'] == {'past_duplicate_keyword_bag': 1, 'seen_identity': 1}
    assert audit['scenario_disjoint']
    splits['test'][0]['label_provenance'] = [{'scenario': '1', 'incident': 'i1'}]
    _, audit = text.leakage_control(splits)
    assert not audit['scenario_disjoint'] and not audit['incident_disjoint']


def test_zero_supervision_is_unavailable_with_no_fabricated_comparison():
    feature, events, numeric = sample_study()
    for w in feature['windows']:
        w['label'] = 0
        w['label_provenance'] = []
    numeric['splits'] = chronological_split(feature['windows'])[1]
    report = text.study(feature, events, numeric)
    assert report['comparison_status'] == 'UNAVAILABLE' and report['comparison'] is None
    assert 'insufficient_training_classes' in report['unavailable_reasons']
    assert report['document_sensitivity_corpus'] == 'NOT_ESTABLISHED'


def test_supported_text_model_fits_training_vocabulary_and_common_numeric_cohort(tmp_path):
    feature, events, numeric = sample_study()
    report = text.study(feature, events, numeric, output=tmp_path)
    assert report['comparison_status'] == 'COMPLETED'
    assert report['comparison']['common_population'] == {'train': 12, 'validation': 4, 'test': 8}
    import joblib
    model = joblib.load(tmp_path / 'text.joblib')
    vocabulary = model.named_steps['tfidf'].vocabulary_
    assert 'delta' not in vocabulary and 'echo' not in vocabulary and 'foxtrot' not in vocabulary
    assert 'secret' in vocabulary and 'alpha' in vocabulary
    assert report['comparison']['text']['serialized_replay_equal']
    assert report['comparison']['text']['test']['windows'] == 8
    assert report['comparison']['numeric_refit_on_same_population']['isolation_forest']['windows'] == 8


def test_snapshot_mismatch_missing_events_and_scenario_refuse_training(tmp_path):
    feature, events, numeric = sample_study()
    wrong = {**numeric, 'feature_artifact_sha256': 'different'}
    with pytest.raises(ValueError, match='snapshot'):
        text.study(feature, events, wrong)
    with pytest.raises(ValueError, match='Missing event'):
        text.study(feature, events[1:], numeric)
    feature['windows'][-1]['label_provenance'] = [{'scenario': '1', 'incident': 'i1'}]
    report = text.study(feature, events, numeric)
    assert report['comparison_status'] == 'UNAVAILABLE'
    assert 'overlapping_scenario_or_incident_groups' in report['unavailable_reasons']
