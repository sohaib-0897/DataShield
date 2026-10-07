"""Replay frozen CERT test windows through both opt-in advisory adapters."""
import argparse
import json
from pathlib import Path

from ml.advisory import AdvisoryStore, FlaskAdvisoryAdapter, ShadowEngine, UpstreamAdvisoryAdapter, digest
from research.cert_ingest import atomic_json, local_path


def replay(benchmark, output, folder):
    benchmark, output = local_path(folder, benchmark), local_path(folder, output)
    if output.exists():
        raise ValueError('Preserve prior replay; choose a new output')
    report = json.loads((benchmark/'report.json').read_text())
    partitions = json.loads((benchmark/'partitions.json').read_text())['splits']['test']
    expected = json.loads((benchmark/'isolation_forest_scores.json').read_text())['test']
    output.mkdir(parents=True)
    engine = ShadowEngine(enabled=True, artifact=benchmark, report_sha256=digest(benchmark/'report.json'))
    checks = {}
    for cls in (FlaskAdvisoryAdapter, UpstreamAdvisoryAdapter):
        store = AdvisoryStore(output/f'{cls.application}.sqlite')
        adapter = cls(engine, store)
        available, fallback, matched = 0, 0, 0
        for index, (window, score) in enumerate(zip(partitions, expected, strict=True)):
            original = {'score': 15, 'severity': 'LOW', 'rule_version': 'replay-fixture-not-cert-policy'}
            result = adapter.attach(original, original, window, observed_at=window['end'], replay_key=str(index))
            assert result == adapter.attach(original, original, window, observed_at=window['end'], replay_key=str(index))
            assert all(result[k] == v for k, v in original.items())
            advice = result['research_advisory']
            available += advice['anomaly']['status'] == 'AVAILABLE'
            matched += abs(advice['anomaly']['score'] - score) < 1e-12
            fallback += advice['fallback']
        checks[cls.application] = {'windows': len(partitions), 'available': available, 'fallbacks': fallback,
                                  'frozen_scores_equal': matched == len(partitions), 'repeated_payload_equal': True,
                                  'original_payload_preserved': True, 'persisted_rows': len(store.recent())}
    if not all(c['available'] == c['windows'] and c['frozen_scores_equal'] for c in checks.values()):
        raise RuntimeError('Advisory replay failed')
    summary = {'contract_version': 'datashield-advisory-v1', 'coverage': 'frozen bounded Phase 3 test cohort',
               'model_report_sha256': digest(benchmark/'report.json'), 'checks': checks, 'artifact_loads': engine.loads,
               'automated_blocking': False, 'rule_fixture_is_detection_evaluation': False,
               'postgresql': 'UNVERIFIED', 'native_windows': 'UNVERIFIED'}
    atomic_json(output/'report.json', summary)
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--benchmark', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(replay(a.benchmark, a.output, Path('research/local').absolute()), indent=2))


if __name__ == '__main__':
    main()
