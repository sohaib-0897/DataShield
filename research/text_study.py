"""CERT keyword detection study; separate from document sensitivity labels."""
import argparse
from collections import Counter
import hashlib
from pathlib import Path
import re
import time
import unicodedata

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ml.features.windows import matrix
from research.behavioral_ml import (chronological_split, fit_models, measured_metrics, score_model,
                                    select_threshold)
from research.cert_features import load_artifact, read_events
from research.cert_ingest import atomic_json, encoded, hash_file, local_path, require_space
import json

VERSION = 'cert-keyword-text-research-v1'


def normalize_keywords(content, *, file_content=False):
    text = unicodedata.normalize('NFKC', content)
    if file_content:
        text = re.sub(r'^\s*[0-9a-fA-F]{8,}\b', ' ', text)
    # Explicitly remove release account/PC IDs and address/URL-like tokens BEFORE
    # retaining alphabetic topic words. Resources/recipients are never passed in.
    text = re.sub(r'\b[A-Za-z]{3}\d{4}\b|\bPC-\d+\b|\{[^}]*\}|\bhttps?://\S+|\b\S+@\S+\b', ' ', text, flags=re.I)
    tokens = re.findall(r'(?<![\w])[a-z]{2,}(?![\w])', text.lower())
    return ' '.join(tokens)


def attach_text(windows, events):
    index = {(e['dataset_sha256'], e['source_file'], e['source_id']): e for e in events}
    rows = []
    for w in windows:
        words, digests = [], set()
        for key in w['event_keys']:
            e = index.get(tuple(key))
            if e is None:
                raise ValueError('Missing event in frozen feature artifact')
            if e['channel'] not in {'FILE', 'HTTP', 'EMAIL'}:
                continue
            content = json.loads(e['metadata_json']).get('content', '')
            normalized = normalize_keywords(content, file_content=e['channel'] == 'FILE')
            if normalized:
                words.append(normalized)
                # Exact bag-of-words fingerprint also catches reordered keyword
                # duplicates; multiplicities retained, no learned vocabulary.
                canonical = ' '.join(sorted(normalized.split()))
                digests.add(hashlib.sha256(canonical.encode()).hexdigest())
        rows.append({**w, 'text': ' '.join(words), 'text_hashes': digests})
    return rows


def leakage_control(splits):
    """Later partitions drop past identities/duplicate text; chronological order stays fixed."""
    seen_users, seen_text = set(), set()
    clean, audit = {}, {}
    for name in ('train', 'validation', 'test'):
        clean[name] = []
        removed = Counter()
        # Use previous partition groups, not earlier rows in the same partition.
        for w in splits[name]:
            if not w['text']:
                removed['missing_text'] += 1
            elif w['user'] in seen_users:
                removed['seen_identity'] += 1
            elif w['text_hashes'] & seen_text:
                removed['past_duplicate_keyword_bag'] += 1
            else:
                clean[name].append(w)
        audit[name] = {'before': len(splits[name]), 'after': len(clean[name]), 'removed': dict(removed)}
        # Even discarded rows' groups remain past observations, conservatively.
        seen_users.update(w['user'] for w in splits[name])
        seen_text.update(h for w in splits[name] for h in w['text_hashes'])
    scenario_sets = {k: {p['scenario'] for w in v for p in w.get('label_provenance', [])} for k, v in clean.items()}
    incident_sets = {k: {p['incident'] for w in v for p in w.get('label_provenance', [])} for k, v in clean.items()}
    shared_scenarios = scenario_sets['train'] & (scenario_sets['validation'] | scenario_sets['test']) | scenario_sets['validation'] & scenario_sets['test']
    shared_incidents = incident_sets['train'] & (incident_sets['validation'] | incident_sets['test']) | incident_sets['validation'] & incident_sets['test']
    # Scenario/incident labels are AUDIT ONLY. If groups overlap, refuse a quality
    # comparison; do not drop malicious test rows to manufacture a clean result.
    return clean, {'partitions': audit, 'shared_scenario_count': len(shared_scenarios),
                   'shared_incident_count': len(shared_incidents),
                   'scenario_disjoint': not shared_scenarios, 'incident_disjoint': not shared_incidents,
                   'identity_policy': 'drop later users observed in any prior partition',
                   'duplicate_policy': 'drop later windows containing any prior normalized keyword bag'}


def study(feature, events, numeric_report, *, output=None, seed=42):
    if numeric_report['feature_artifact_sha256'] != feature['artifact_sha256'] or numeric_report['store_sha256'] != feature['store_sha256']:
        raise ValueError('Numeric benchmark does not match frozen feature/source snapshot')
    splits, split_audit = chronological_split(feature['windows'])
    if split_audit != numeric_report['splits']:
        raise ValueError('Numeric benchmark partition mismatch')
    text_splits = {k: attach_text(v, events) for k, v in splits.items()}
    clean, audit = leakage_control(text_splits)
    train_counts = Counter(w['label'] for w in clean['train'])
    validation_counts = Counter(w['label'] for w in clean['validation'])
    reasons = []
    if min(train_counts[0], train_counts[1]) < 2:
        reasons.append('insufficient_training_classes')
    if min(validation_counts[0], validation_counts[1]) < 1:
        reasons.append('insufficient_validation_classes')
    if not clean['test']:
        reasons.append('empty_held_out_cohort_after_leakage_controls')
    if not audit['scenario_disjoint'] or not audit['incident_disjoint']:
        reasons.append('overlapping_scenario_or_incident_groups')
    all_texts = [normalize_keywords(json.loads(e['metadata_json']).get('content', ''), file_content=e['channel'] == 'FILE')
                 for e in events if e['channel'] in {'FILE', 'HTTP', 'EMAIL'}]
    report = {'version': VERSION, 'task': 'CERT malicious event-window keyword detection; NOT document sensitivity',
              'dataset_sha256': feature['dataset_sha256'], 'store_sha256': feature['store_sha256'],
              'feature_artifact_sha256': feature['artifact_sha256'], 'full_dataset': False,
              'events': len(events), 'text_source_events': len(all_texts),
              'nonempty_sanitized_text_events': sum(bool(t) for t in all_texts),
              'duplicate_normalized_keyword_bags': len(all_texts) - len({' '.join(sorted(t.split())) for t in all_texts}),
              'original_numeric_population': {k: len(v) for k, v in splits.items()},
              'leakage_audit': audit, 'train_class_counts': dict(train_counts), 'validation_class_counts': dict(validation_counts),
              'comparison_status': 'UNAVAILABLE' if reasons else 'COMPLETED', 'unavailable_reasons': reasons,
              'comparison': None, 'document_sensitivity_corpus': 'NOT_ESTABLISHED', 'live_activation': False,
              'text_sources': 'content keyword fields only; file hex headers removed; no resources or identities',
              'held_out_prevalence_policy': 'no class resampling; report filtered common cohort explicitly'}
    if reasons:
        return report
    if output is None:
        raise ValueError('Supported study requires a local output directory')
    # Usability decisions use train/validation labels. Test labels only supply
    # evaluation and group-leakage audits, never fit/threshold/tuning inputs.
    start = time.perf_counter()
    pipeline = Pipeline([('tfidf', TfidfVectorizer(max_features=10000, ngram_range=(1, 2), sublinear_tf=True)),
                         ('linear', LogisticRegression(random_state=seed, max_iter=1000, class_weight='balanced'))])
    pipeline.fit([w['text'] for w in clean['train']], [w['label'] for w in clean['train']])
    train_seconds = time.perf_counter() - start
    val_scores = pipeline.predict_proba([w['text'] for w in clean['validation']])[:, 1]
    threshold, strategy = select_threshold([w['label'] for w in clean['validation']], val_scores)
    start = time.perf_counter()
    scores = pipeline.predict_proba([w['text'] for w in clean['test']])[:, 1]
    latency = time.perf_counter() - start
    joblib.dump(pipeline, output / 'text.joblib')
    restored = joblib.load(output / 'text.joblib')
    if not np.array_equal(scores, restored.predict_proba([w['text'] for w in clean['test']])[:, 1]):
        raise RuntimeError('Text serialization replay failed')
    numeric, supported = fit_models(clean['train'], clean['validation'], seed=seed)
    numeric_metrics = {name: measured_metrics(clean['test'], score_model(name, item['pipeline'], np.array(matrix(clean['test']))), item['threshold'])
                       for name, item in numeric.items()}
    report['comparison'] = {'common_population': {k: len(v) for k, v in clean.items()},
                            'text': {'test': measured_metrics(clean['test'], scores, threshold), 'threshold': threshold,
                                     'threshold_strategy': strategy, 'threshold_partition': 'validation',
                                     'artifact_sha256': hash_file(output / 'text.joblib')['sha256'],
                                     'training_seconds': train_seconds, 'batch_inference_seconds': latency,
                                     'serialized_replay_equal': True, 'vocabulary_fit_partition': 'train',
                                     'score_kind': 'uncalibrated_class_probability'},
                            'numeric_refit_on_same_population': numeric_metrics}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--features', required=True, type=Path)
    parser.add_argument('--database', required=True, type=Path)
    parser.add_argument('--numeric-report', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--max-events', type=int, default=100000)
    parser.add_argument('--max-metadata-mib', type=int, default=128)
    parser.add_argument('--max-feature-mib', type=int, default=64)
    args = parser.parse_args()
    folder = Path('research/local').absolute()
    output = local_path(folder, args.output)
    if output.exists():
        raise ValueError('Output exists; use a new directory')
    require_space(folder, 16 * 1024**2)
    features = load_artifact(args.features, folder, args.max_feature_mib * 1024**2)
    database = local_path(folder, args.database)
    if hash_file(database)['sha256'] != features['store_sha256']:
        raise ValueError('Research store changed since frozen features')
    numeric = json.loads(local_path(folder, args.numeric_report).read_text())
    events = read_events(database, folder, args.max_events, args.max_metadata_mib * 1024**2)
    output.mkdir()
    report = study(features, events, numeric, output=output)
    atomic_json(output / 'report.json', report)
    print(encoded(report))


if __name__ == '__main__':
    main()
