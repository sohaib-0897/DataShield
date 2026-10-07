from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json

import numpy as np
import pytest

from ml.features.windows import CHANNELS, FEATURE_NAMES, VERSION, build_windows, matrix
from research import behavioral_ml as ml
from research.cert_ingest import atomic_json, encoded


def windows():
    base = datetime(2010, 1, 4, 8)
    events = []
    for hour in range(6):
        for user in range(4):
            for n in range(1 + user):
                events.append({'username': str(user), 'pc': 'pc', 'channel': 'FILE',
                               'timestamp_local': (base + timedelta(hours=hour, minutes=n)).isoformat(),
                               'dataset_sha256': 'd', 'source_file': 'file.csv', 'source_id': f'{hour}-{user}-{n}'})
    ws = build_windows(events, {c: (base, base + timedelta(hours=6)) for c in CHANNELS})
    for w in ws:
        w['label'] = int(w['user'] in ('2', '3'))
        w['label_provenance'] = [{'incident': 'one', 'scenario': '1'}] if w['label'] else []
    return ws


def test_splits_global_chronology_natural_prevalence_and_no_event_overlap():
    ws = windows()
    splits, audit = ml.chronological_split(ws)
    assert [len(splits[k]) for k in ('train', 'validation', 'test')] == [12, 4, 8]
    for name in splits:
        assert sum(w['label'] for w in splits[name]) / len(splits[name]) == .5
    assert max(w['end'] for w in splits['train']) <= min(w['start'] for w in splits['validation'])
    assert max(w['end'] for w in splits['validation']) <= min(w['start'] for w in splits['test'])
    assert audit['purged_overlaps'] == 0


def test_overlap_purged_and_repeated_event_rejected():
    ws = windows()
    ws[8]['end'] = ws[12]['end']
    splits, audit = ml.chronological_split(ws)
    assert audit['purged_overlaps'] == 1
    ws = windows()
    ws[-1]['event_keys'] = ws[0]['event_keys']
    with pytest.raises(ValueError, match='Duplicate'):
        ml.chronological_split(ws)


def test_missing_unknown_and_insufficient_partitions():
    ws = windows()
    ws[0]['fully_observed'] = False
    ws[1]['label'] = None
    _, audit = ml.chronological_split(ws)
    assert audit['excluded_windows'] == 2
    with pytest.raises(ValueError, match='three'):
        ml.chronological_split(ws[:4])


def test_preprocessing_fits_only_training_and_threshold_independent_of_test():
    splits, _ = ml.chronological_split(windows())
    models, supervision = ml.fit_models(splits['train'], splits['validation'], trees=10)
    assert supervision['status'] == 'trained'
    model = models['isolation_forest']['pipeline']
    train_matrix = np.array(matrix(splits['train']))
    index = FEATURE_NAMES.index('total_count')
    assert model.named_steps['imputer'].statistics_[index] == np.median(train_matrix[:, index])
    assert model.named_steps['scale'].n_samples_seen_ == len(splits['train'])
    threshold = models['isolation_forest']['threshold']
    extreme = deepcopy(splits['test'])
    for w in extreme:
        w['features']['total_count'] = 1000000
        w['label'] = 1 - w['label']
    ml.measured_metrics(extreme, ml.score_model('isolation_forest', model, np.array(matrix(extreme))), threshold)
    assert models['isolation_forest']['threshold'] == threshold
    again, _ = ml.fit_models(splits['train'], splits['validation'], trees=10)
    assert again['isolation_forest']['threshold'] == threshold
    assert np.array_equal(models['isolation_forest']['validation_scores'], again['isolation_forest']['validation_scores'])


def test_zero_positive_metrics_and_validation_budget():
    ws = windows()[:4]
    for w in ws:
        w['label'] = 0
        w['label_provenance'] = []
    scores = [.1, .2, .3, .4]
    threshold, strategy = ml.select_threshold([0] * 4, scores, budget=.25)
    assert threshold == .3
    metrics = ml.measured_metrics(ws, scores, threshold)
    assert metrics['confusion'] == {'tn': 3, 'fp': 1, 'fn': 0, 'tp': 0}
    assert metrics['precision'] == 0
    assert metrics['recall'] is None and metrics['f1'] is None and metrics['pr_auc_average_precision'] is None
    assert metrics['false_alerts_per_evaluated_user_day'] == .25
    no_alerts = ml.measured_metrics(ws, scores, .4)
    assert no_alerts['precision'] is None
    for budget in [0, .01, .25, .5]:
        value, _ = ml.select_threshold([0] * 4, [1] * 4, budget=budget)
        assert sum(s > value for s in [1] * 4) <= int(4 * budget)


def test_f1_threshold_ties_and_meaningful_positive_metrics():
    threshold, strategy = ml.select_threshold([0, 0, 1, 1], [.1, .2, .8, .9])
    assert threshold == .2
    metrics = ml.measured_metrics(windows()[:4], [.1, .2, .8, .9], threshold)
    assert metrics['precision'] == metrics['recall'] == metrics['f1'] == 1
    assert metrics['pr_auc_average_precision'] == 1
    assert metrics['scenarios']['1']['detected_windows'] == 2
    assert metrics['supported_incidents'] == metrics['detected_incidents'] == 1
    assert metrics['median_first_alert_seconds_from_first_labeled_window_start'] == 3600


def test_no_supervised_model_without_supported_training_validation():
    splits, _ = ml.chronological_split(windows())
    for w in splits['train']:
        w['label'] = 0
    models, supported = ml.fit_models(splits['train'], splits['validation'], trees=5)
    assert set(models) == {'isolation_forest'} and supported['status'] == 'unavailable'


def test_local_artifacts_replay_and_refuse_overwrite(tmp_path):
    data = {'feature_version': VERSION, 'feature_names': FEATURE_NAMES, 'windows': windows(),
            'dataset_sha256': 'd' * 64, 'store_sha256': 's' * 64, 'answers_sha256': 'a' * 64}
    data['artifact_sha256'] = hashlib.sha256(encoded(data).encode()).hexdigest()
    path = tmp_path / 'features.json'
    atomic_json(path, data)
    output = tmp_path / 'model'
    report = ml.benchmark(path, tmp_path, output, trees=10)
    assert report['status'] == 'RESEARCH_ONLY_NOT_REGISTRABLE'
    assert report['supervised']['status'] == 'trained'
    for name, item in report['models'].items():
        assert item['restored_scores_equal'] and item['independent_training_equal'] and item['replay_artifact_hash_equal']
        assert (output / f'{name}.joblib').exists()
        assert item['preprocessing_fit_rows'] == 12
    with pytest.raises(ValueError, match='exists'):
        ml.benchmark(path, tmp_path, output, trees=10)
    assert json.loads((output / 'report.json').read_text())['feature_version'] == VERSION


def test_fast_threshold_matches_all_strict_candidates():
    from research.behavioral_ml import select_threshold
    rng = np.random.default_rng(55)
    for _ in range(20):
        y = rng.integers(0, 2, 100)
        scores = np.round(rng.random(100), 1)  # Deliberate ties.
        candidates = [float(np.nextafter(scores.min(), -np.inf)), *np.unique(scores)]
        def objective(threshold):
            predicted = scores > threshold
            tp = int(((y == 1) & predicted).sum())
            fp = int(((y == 0) & predicted).sum())
            fn = int(((y == 1) & ~predicted).sum())
            return (2*tp/(2*tp+fp+fn) if tp else 0), threshold
        assert select_threshold(y, scores)[0] == max(candidates, key=objective)
