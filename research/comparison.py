"""Fixed research rule/model/union comparison on identical frozen test windows.

The research rule is not a translation of live endpoint policy; CERT does not
supply role, filename sensitivity, hash policy or transfer-permission evidence.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

from research.behavioral_ml import measured_metrics
from research.cert_ingest import atomic_json, encoded, hash_file, local_path


def rule_score(window):
    # Predeclared, untuned benchmark heuristic: removable FILE copy in a user-hour
    # containing out-of-hours activity. Not necessarily an after-hours FILE copy.
    f = window['features']
    return float(f['file_count'] > 0 and f['after_hours_fraction'] > 0)


def error_summary(windows, scores, threshold):
    groups = {name: {'windows': 0, 'cold_starts': 0, 'file_copy_windows': 0,
                     'after_hours_windows': 0, 'scenarios': Counter()}
              for name in ('true_positive', 'false_positive', 'false_negative', 'true_negative')}
    for w, score in zip(windows, scores, strict=True):
        predicted, truth = score > threshold, w['label'] == 1
        name = 'true_positive' if predicted and truth else 'false_positive' if predicted else 'false_negative' if truth else 'true_negative'
        g = groups[name]
        g['windows'] += 1
        g['cold_starts'] += w['features']['cold_start'] == 1
        g['file_copy_windows'] += w['features']['file_count'] > 0
        g['after_hours_windows'] += w['features']['after_hours_fraction'] > 0
        g['scenarios'].update({p['scenario'] for p in w.get('label_provenance', [])})
    return {k: {**v, 'scenarios': dict(v['scenarios'])} for k, v in groups.items()}


def compare(benchmark):
    report = json.loads((benchmark/'report.json').read_text())
    if report.get('partitions_sha256') and hash_file(benchmark/'partitions.json')['sha256'] != report['partitions_sha256']:
        raise ValueError('Frozen partition snapshot changed')
    windows = json.loads((benchmark/'partitions.json').read_text())['splits']['test']
    cohort = hashlib.sha256(encoded([(w['user'], w['start'], w['end'], w['event_keys']) for w in windows]).encode()).hexdigest()
    rules = np.array([rule_score(w) for w in windows])
    methods = {'fixed_research_rule': (rules, .5)}
    for name, model in report['models'].items():
        pinned = report.get('score_artifacts_sha256', {}).get(name)
        if pinned and hash_file(benchmark/f'{name}_scores.json')['sha256'] != pinned:
            raise ValueError('Frozen scores changed')
        scores = json.loads((benchmark/f'{name}_scores.json').read_text())
        if len(scores['test']) != len(windows) or model['threshold_partition'] != 'validation':
            raise ValueError('Frozen score/threshold population mismatch')
        methods[name] = (np.array(scores['test']), model['threshold'])
        methods[f'rule_or_{name}'] = ((rules > .5) | (np.array(scores['test']) > model['threshold']), .5)
    results = {name: {'cohort_sha256': cohort, 'test': measured_metrics(windows, scores, threshold),
                      'errors': error_summary(windows, scores, threshold)} for name, (scores, threshold) in methods.items()}
    return {'version': 'cert-common-population-comparison-v1', 'feature_artifact_sha256': report['feature_artifact_sha256'],
            'common_test_windows': len(windows), 'cohort_sha256': cohort, 'methods': results,
            'rule': 'file_count > 0 AND after_hours_fraction > 0; fixed, untuned research heuristic',
            'combined': 'fixed Boolean OR of heuristic and validation-thresholded model; advisory benchmark only',
            'prevalence_policy': 'all eligible frozen test windows; no balancing or label-based exclusions',
            'endpoint_policy_comparison': 'UNAVAILABLE: CERT lacks role/hash/sensitivity/permission evidence',
            'live_activation': False, 'full_dataset': False,
            'limitation': 'descriptive bounded later-time benchmark; not unseen-user or endpoint detection quality'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--benchmark', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    folder = Path('research/local').absolute()
    output = local_path(folder, a.output)
    if output.exists(): raise ValueError('Preserve prior comparison')
    atomic_json(output, compare(local_path(folder, a.benchmark)))
    print(encoded({'report': str(output)}))


if __name__ == '__main__':
    main()
