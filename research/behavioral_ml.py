"""Offline, bounded, chronological CERT models; never registers or activates models."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import platform
import time

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.features.windows import FEATURE_NAMES, VERSION, matrix
from research.cert_features import load_artifact
from research.cert_ingest import atomic_json, encoded, hash_file, local_path, require_space

MODEL_VERSION = 'cert-behavior-research-v1'


def chronological_split(windows):
    eligible = sorted((w for w in windows if w['fully_observed'] and w['label'] in (0, 1)),
                      key=lambda w: (w['start'], w['user']))
    hours = sorted({w['start'] for w in eligible})
    if len(hours) < 3:
        raise ValueError('Need at least three distinct fully observed hours')
    first = max(1, int(len(hours) * .6))
    second = min(len(hours) - 1, max(first + 1, int(len(hours) * .8)))
    val_start, test_start = hours[first], hours[second]
    splits = {'train': [], 'validation': [], 'test': []}
    purged = 0
    # Works for nonoverlapping hourly features and rejects/purges overlaps if a
    # future adapter supplies longer intervals. Splits group ALL users by time.
    for w in eligible:
        if w['end'] <= w['start']:
            raise ValueError('Invalid window interval')
        if w['start'] < val_start:
            if w['end'] <= val_start:
                splits['train'].append(w)
            else:
                purged += 1
        elif w['start'] < test_start:
            if w['end'] <= test_start:
                splits['validation'].append(w)
            else:
                purged += 1
        else:
            splits['test'].append(w)
    if any(not v for v in splits.values()):
        raise ValueError('Empty chronological partition after purge')
    for left, right in [('train', 'validation'), ('validation', 'test')]:
        if max(w['end'] for w in splits[left]) > min(w['start'] for w in splits[right]):
            raise ValueError('Overlapping partitions')
        keys = {tuple(k) for w in splits[left] for k in w['event_keys']}
        if keys & {tuple(k) for w in splits[right] for k in w['event_keys']}:
            raise ValueError('Duplicate event across partitions')
    # Non-adjacent partitions must also be disjoint.
    keys = {tuple(k) for w in splits['train'] for k in w['event_keys']}
    if keys & {tuple(k) for w in splits['test'] for k in w['event_keys']}:
        raise ValueError('Duplicate event across train and test')
    audit = {name: {'windows': len(rows), 'positives': sum(w['label'] for w in rows),
                    'users': len({w['user'] for w in rows}),
                    'start': min(w['start'] for w in rows), 'end': max(w['end'] for w in rows)}
             for name, rows in splits.items()}
    return splits, {'partitions': audit, 'purged_overlaps': purged, 'excluded_windows': len(windows) - len(eligible),
                    'validation_start': val_start, 'test_start': test_start,
                    'policy': '60/20/20 of distinct chronological hours; all users share boundaries'}


def select_threshold(labels, scores, *, budget=.01):
    """Validation only. Strict score > threshold; no test inputs are accepted."""
    y = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    if len(y) != len(scores) or not len(y) or not np.isfinite(scores).all() or not 0 <= budget < 1:
        raise ValueError('Invalid validation scores/budget')
    if y.sum() and (y == 0).sum():
        candidates = [float(np.nextafter(scores.min(), -np.inf)), *map(float, np.unique(scores))]
        def objective(threshold):
            predicted = scores > threshold
            tp = int(((y == 1) & predicted).sum())
            fp = int(((y == 0) & predicted).sum())
            fn = int(((y == 1) & ~predicted).sum())
            f1 = 2 * tp / (2 * tp + fp + fn) if tp else 0
            return f1, threshold
        threshold = max(candidates, key=objective)
        return threshold, 'validation_max_f1_ties_prefer_higher_threshold'
    allowed = int(len(scores) * budget)
    threshold = float(np.sort(scores)[len(scores) - allowed - 1])
    return threshold, 'validation_alert_budget_no_two_class_supervision'


def measured_metrics(windows, scores, threshold):
    y = np.array([w['label'] for w in windows], dtype=int)
    scores = np.asarray(scores)
    predictions = scores > threshold
    tn, fp, fn, tp = map(int, confusion_matrix(y, predictions, labels=[0, 1]).ravel())
    positives = tp + fn
    user_days = len({(w['user'], w['start'][:10]) for w in windows})
    scenarios = defaultdict(lambda: {'positive_windows': 0, 'detected_windows': 0})
    incidents = defaultdict(list)
    for w, detected in zip(windows, predictions):
        for scenario in {p['scenario'] for p in w.get('label_provenance', [])}:
            scenarios[scenario]['positive_windows'] += 1
            scenarios[scenario]['detected_windows'] += int(detected)
        for incident in {p['incident'] for p in w.get('label_provenance', [])}:
            incidents[incident].append((w['start'], w['end'], bool(detected)))
    lags = []
    for rows in incidents.values():
        detected = [end for _, end, flag in rows if flag]
        if detected:
            lags.append((datetime.fromisoformat(min(detected)) - datetime.fromisoformat(min(start for start, _, _ in rows))).total_seconds())
    return {'windows': len(windows), 'positive_windows': positives, 'prevalence': positives / len(windows),
            'precision': tp / (tp + fp) if tp + fp else None,
            'recall': tp / positives if positives else None,
            'f1': 2 * tp / (2 * tp + fp + fn) if positives else None,
            'pr_auc_average_precision': float(average_precision_score(y, scores)) if positives and tn + fp else None,
            'confusion': {'tn': tn, 'fp': fp, 'fn': fn, 'tp': tp},
            'false_positive_rate': fp / (tn + fp) if tn + fp else None,
            'alerts': int(predictions.sum()), 'evaluated_user_days': user_days,
            'false_alerts_per_evaluated_user_day': fp / user_days,
            'false_alerts_per_active_user_hour': fp / len(windows),
            'scenarios': dict(scenarios), 'supported_incidents': len(incidents), 'detected_incidents': len(lags),
            'median_first_alert_seconds_from_first_labeled_window_start': float(np.median(lags)) if lags else None,
            'timing_basis': 'window end relative to first labeled TEST window start; not full incident onset',
            'undefined_reason': 'no_positive_windows' if not positives else None}


def fit_models(train, validation, *, seed=42, trees=200, budget=.01):
    X = np.asarray(matrix(train), dtype=float)
    validation_X = np.asarray(matrix(validation), dtype=float)
    train_y = [w['label'] for w in train]
    val_y = [w['label'] for w in validation]
    models = {}
    anomaly = Pipeline([('imputer', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True)),
                        ('scale', StandardScaler()),
                        ('model', IsolationForest(n_estimators=trees, max_samples=min(256, len(train)),
                                                  random_state=seed, n_jobs=1, contamination='auto'))])
    anomaly.fit(X)
    val_scores = -anomaly.score_samples(validation_X)
    threshold, strategy = select_threshold(val_y, val_scores, budget=budget)
    models['isolation_forest'] = {'pipeline': anomaly, 'threshold': threshold, 'threshold_strategy': strategy,
                                 'score_kind': 'negative_score_samples_not_probability', 'validation_scores': val_scores}
    train_counts, val_counts = Counter(train_y), Counter(val_y)
    supported = min(train_counts[0], train_counts[1]) >= 2 and min(val_counts[0], val_counts[1]) >= 1
    if supported:
        linear = Pipeline([('imputer', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True)),
                           ('scale', StandardScaler()),
                           ('model', LogisticRegression(random_state=seed, max_iter=1000, class_weight='balanced'))])
        linear.fit(X, train_y)
        scores = linear.predict_proba(validation_X)[:, 1]
        threshold, strategy = select_threshold(val_y, scores, budget=budget)
        models['logistic_regression'] = {'pipeline': linear, 'threshold': threshold, 'threshold_strategy': strategy,
                                       'score_kind': 'uncalibrated_class_probability', 'validation_scores': scores}
    return models, {'status': 'trained' if supported else 'unavailable',
                    'reason': None if supported else 'need >=2/class in train and both classes in validation',
                    'train_class_counts': dict(train_counts), 'validation_class_counts': dict(val_counts)}


def score_model(name, pipeline, X):
    return -pipeline.score_samples(X) if name == 'isolation_forest' else pipeline.predict_proba(X)[:, 1]


def benchmark(feature_path, folder, output, *, seed=42, trees=200, budget=.01, replay=True):
    output = local_path(folder, output)
    if output.exists():
        raise ValueError('Output exists; retain it and use a new artifact directory')
    if not 1 <= trees <= 1000 or not 0 <= seed <= 2**32 - 1:
        raise ValueError('Invalid bounded model settings')
    require_space(folder, 16 * 1024**2)
    feature = load_artifact(feature_path, folder)
    splits, split_audit = chronological_split(feature['windows'])
    start = time.perf_counter()
    models, supervised = fit_models(splits['train'], splits['validation'], seed=seed, trees=trees, budget=budget)
    training_seconds = time.perf_counter() - start
    # Create artifacts only after prerequisites/fit succeed. Persist exact partitions
    # and predictions locally; no usernames/event keys enter committed reports.
    output.mkdir()
    atomic_json(output / 'partitions.json', {'splits': splits, 'audit': split_audit})
    model_reports = {}
    test_X = np.asarray(matrix(splits['test']), dtype=float)
    repeated = fit_models(splits['train'], splits['validation'], seed=seed, trees=trees, budget=budget)[0] if replay else None
    for name, item in models.items():
        pipeline = item['pipeline']
        start = time.perf_counter()
        test_scores = score_model(name, pipeline, test_X)
        inference_seconds = time.perf_counter() - start
        model_path = output / f'{name}.joblib'
        joblib.dump(pipeline, model_path)
        restored = joblib.load(model_path)
        restored_equal = np.array_equal(test_scores, score_model(name, restored, test_X))
        repeat_equal = None if repeated is None else (np.array_equal(test_scores, score_model(name, repeated[name]['pipeline'], test_X)) and
                                                       item['threshold'] == repeated[name]['threshold'])
        if not restored_equal or repeat_equal is False:
            raise RuntimeError('Reproducibility check failed')
        replay_hash_equal = None
        if repeated is not None:
            replay_path = output / f'{name}_replay.joblib'
            joblib.dump(repeated[name]['pipeline'], replay_path)
            replay_hash_equal = hash_file(model_path)['sha256'] == hash_file(replay_path)['sha256']
            if not replay_hash_equal:
                raise RuntimeError('Model artifact hashes differ on deterministic replay')
        atomic_json(output / f'{name}_scores.json', {'validation': item['validation_scores'].tolist(), 'test': test_scores.tolist(),
                                                   'threshold': item['threshold']})
        model_reports[name] = {'score_kind': item['score_kind'], 'threshold': item['threshold'],
                               'threshold_strategy': item['threshold_strategy'], 'threshold_partition': 'validation',
                               'validation': measured_metrics(splits['validation'], item['validation_scores'], item['threshold']),
                               'test': measured_metrics(splits['test'], test_scores, item['threshold']),
                               'artifact_sha256': hash_file(model_path)['sha256'], 'restored_scores_equal': restored_equal,
                               'independent_training_equal': repeat_equal, 'replay_artifact_hash_equal': replay_hash_equal,
                               'batch_inference_seconds': inference_seconds,
                               'mean_inference_ms_per_window': inference_seconds * 1000 / len(test_X),
                               'imputer_statistics': pipeline.named_steps['imputer'].statistics_.tolist(),
                               'preprocessing_fit_rows': int(pipeline.named_steps['scale'].n_samples_seen_)}
    report = {'version': MODEL_VERSION, 'status': 'RESEARCH_ONLY_NOT_REGISTRABLE', 'feature_version': VERSION,
              'feature_names': FEATURE_NAMES, 'dataset_sha256': feature['dataset_sha256'],
              'feature_artifact_sha256': feature['artifact_sha256'], 'store_sha256': feature['store_sha256'],
              'answers_sha256': feature['answers_sha256'], 'seed': seed, 'trees': trees, 'cpu_workers': 1,
              'software': {'python': platform.python_version(), 'sklearn': sklearn.__version__, 'numpy': np.__version__, 'joblib': joblib.__version__},
              'splits': split_audit, 'models': model_reports, 'supervised': supervised,
              'training_seconds': training_seconds, 'full_dataset': False, 'preprocessing_fit_partition': 'train',
              'anomaly_training_population': 'all eligible chronological training windows; no label-based cleaning',
              'baseline_history_policy': 'observed past windows allowed online across boundaries; labels never used',
              'validation_alert_budget': budget, 'evaluated_windows': sum(len(v) for v in splits.values()),
              'quality_claim_supported': all(any(w['label'] == 1 for w in splits[k]) for k in splits),
              'latency_basis': 'local CPU batch score, excludes event ingestion/window preparation; one observation'}
    atomic_json(output / 'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--features', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--trees', type=int, default=200)
    parser.add_argument('--validation-alert-budget', type=float, default=.01)
    args = parser.parse_args()
    result = benchmark(args.features, Path('research/local').absolute(), args.output,
                       seed=args.seed, trees=args.trees, budget=args.validation_alert_budget)
    print(encoded(result))


if __name__ == '__main__':
    main()
