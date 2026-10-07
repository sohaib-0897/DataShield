import json

from research.comparison import compare, error_summary, rule_score


def test_fixed_rule_requires_both_signals():
    assert rule_score({'features': {'file_count': 2, 'after_hours_fraction': 0}}) == 0
    assert rule_score({'features': {'file_count': 0, 'after_hours_fraction': 1}}) == 0
    assert rule_score({'features': {'file_count': 2, 'after_hours_fraction': .5}}) == 1


def test_common_population_union_and_undefined_metrics(tmp_path):
    windows = [{'user': 'synthetic', 'start': f'2010-06-20T{h:02}:00:00', 'end': f'2010-06-20T{h+1:02}:00:00',
                'event_keys': [['d', 's', str(h)]], 'label': 0,
                'features': {'file_count': h, 'after_hours_fraction': 1, 'cold_start': 0}} for h in range(3)]
    (tmp_path/'report.json').write_text(json.dumps({'feature_artifact_sha256': 'a'*64,
        'models': {'isolation_forest': {'threshold': .5, 'threshold_partition': 'validation'}}}))
    (tmp_path/'partitions.json').write_text(json.dumps({'splits': {'test': windows}}))
    (tmp_path/'isolation_forest_scores.json').write_text(json.dumps({'test': [.6,.1,.2]}))
    report = compare(tmp_path)
    methods = report['methods']
    assert {m['cohort_sha256'] for m in methods.values()} == {report['cohort_sha256']}
    assert methods['rule_or_isolation_forest']['test']['alerts'] == 3
    assert all(m['test']['recall'] is None and m['test']['f1'] is None for m in methods.values())
    assert 'synthetic' not in json.dumps(report)
