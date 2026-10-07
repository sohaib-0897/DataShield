from datetime import datetime, timedelta
import json
from pathlib import Path

import pytest

from ml.features.windows import CHANNELS, FEATURE_NAMES, build_windows, matrix
from research import cert_features as features
from research.cert_ingest import atomic_json, encoded, hash_file
import hashlib

BASE = datetime(2010, 1, 4, 8)
COVERAGE = {c: (BASE, BASE + timedelta(hours=12)) for c in CHANNELS}


def event(user='a', hour=8, identity='1', channel='FILE', pc='pc1'):
    metadata = {'id': identity, 'date': f'01/04/2010 {hour:02d}:10:00', 'user': user, 'pc': pc,
                'filename': 'report.txt', 'content': 'words'}
    return {'dataset_sha256': 'd', 'source_file': channel.lower() + '.csv', 'source_id': identity,
            'username': user, 'pc': pc, 'channel': channel, 'timestamp_local': f'2010-01-04T{hour:02d}:10:00',
            'metadata_json': json.dumps(metadata)}


def observable(e, incident='incident', scenario='1', row=1):
    return {'source': e['source_file'], 'id': e['source_id'], 'metadata': json.loads(e['metadata_json']),
            'incident': incident, 'scenario': scenario, 'row': row}


def test_exact_join_does_not_label_users_history_or_other_sources():
    bad = event(identity='bad')
    other_source = event(identity='bad', channel='HTTP')
    good = event(identity='good')
    labels, audit = features.join_labels([bad, other_source, good], [observable(bad)])
    assert [labels[('d', e['source_file'], e['source_id'])]['label'] for e in [bad, other_source, good]] == [1, 0, 0]
    assert audit['unmatched_observables'] == 0
    assert labels[('d', 'file.csv', 'bad')]['provenance'][0]['row'] == 1


@pytest.mark.parametrize('field', ['user', 'date', 'pc', 'filename', 'content'])
def test_scoped_id_with_different_fields_stays_unknown(field):
    e = event()
    answer = observable(e)
    answer['metadata'][field] = 'different'
    labels, audit = features.join_labels([e], [answer])
    assert labels[('d', 'file.csv', '1')]['label'] is None
    assert audit['ambiguous_or_conflicting'] == 1
    assert audit['unmatched_observables'] == 1


def test_multiple_incidents_are_ambiguous_and_unmatched_audited():
    e = event()
    labels, audit = features.join_labels([e], [observable(e, 'one'), observable(e, 'two'), observable(event(identity='missing'))])
    assert labels[('d', 'file.csv', '1')]['label'] is None
    assert audit['unmatched_observables'] == 3


def test_users_and_past_baselines_are_isolated():
    windows = build_windows([event('a'), event('b', identity='b1'), event('b', identity='b2'),
                             event('a', 9, 'a2'), event('b', 9, 'b3')], COVERAGE)
    at9 = {w['user']: w['features'] for w in windows if w['start'].endswith('09:00:00')}
    assert at9['a']['past_mean_total'] == 1
    assert at9['b']['past_mean_total'] == 2
    assert at9['a']['total_over_past_mean'] == 1
    assert at9['b']['total_over_past_mean'] == .5


def test_future_invariance_input_order_and_adjacent_windows():
    early = [event(), event(hour=9, identity='2')]
    before = build_windows(early, COVERAGE)
    after = build_windows([event(hour=11, identity='future', pc='future-pc'), *reversed(early)], COVERAGE)
    assert before == after[:2]
    assert before[0]['end'] == before[1]['start']
    assert before[0]['features']['cold_start'] == 1
    assert before[0]['features']['novel_pc_fraction'] is None
    assert before[1]['features']['novel_pc_fraction'] == 0


def test_missing_channel_is_not_zero_and_partial_window_not_baseline():
    coverage = {c: bounds for c, bounds in COVERAGE.items() if c != 'HTTP'}
    windows = build_windows([event(), event(hour=9, identity='2')], coverage)
    for w in windows:
        assert w['features']['http_count'] is None
        assert w['features']['http_available'] == 0
        assert w['features']['file_count'] == 1
        assert w['features']['history_windows'] == 0
        assert not w['fully_observed']
    assert build_windows([], COVERAGE) == []
    assert len(matrix(windows)[0]) == len(FEATURE_NAMES)
    assert all('user' not in name and 'label' not in name and 'scenario' not in name for name in FEATURE_NAMES)


def test_work_hours_and_partial_source_edges():
    e = event()
    assert build_windows([e], COVERAGE)[0]['features']['after_hours_fraction'] == 1
    assert build_windows([e], COVERAGE, work_start=8, work_end=16)[0]['features']['after_hours_fraction'] == 0
    coverage = {**COVERAGE, 'FILE': (BASE + timedelta(minutes=1), BASE + timedelta(hours=12))}
    assert not build_windows([e], coverage)[0]['fully_observed']
    with pytest.raises(ValueError):
        build_windows([e], COVERAGE, work_start=17, work_end=9)


def answer_manifest(tmp_path):
    # The first observable lives in inspector's header, not its row cache.
    e = event()
    values = ['file', *json.loads(e['metadata_json']).values()]
    master = tmp_path / 'master.jsonl'
    master.write_text(encoded(['4.2', '1', 'r4.2-1-a.csv', 'a', '01/04/2010 08:00:00', '01/04/2010 09:00:00']) + '\n')
    rows = tmp_path / 'rows.jsonl'
    rows.write_text('')
    members = [{'name': 'answers/insiders.csv', 'header': ['dataset', 'scenario', 'details', 'user', 'start', 'end'],
                'cache': master.name, 'cache_hash': hash_file(master)['sha256'], 'complete': True},
               {'name': 'answers/r4.2-1/r4.2-1-a.csv', 'header': values, 'cache': rows.name,
                'cache_hash': hash_file(rows)['sha256'], 'complete': True}]
    data = {'version': 'cert-r42-ingestion-v1', 'all_members_validated': True, 'members': members,
            'input': {'sha256': 'a' * 64}}
    data['manifest_sha256'] = hashlib.sha256(encoded(data).encode()).hexdigest()
    manifest = tmp_path / 'manifest.json'
    atomic_json(manifest, data)
    return manifest


def test_actual_answer_file_granularity_restores_first_observable(tmp_path):
    manifest = answer_manifest(tmp_path)
    inspected, incidents, rows = features.load_answers(manifest, tmp_path)
    assert len(incidents) == 1 and len(rows) == 1
    assert rows[0]['id'] == '1' and rows[0]['row'] == 1
    data = json.loads(manifest.read_text())
    data['members'][1]['complete'] = False
    data.pop('manifest_sha256')
    data['manifest_sha256'] = hashlib.sha256(encoded(data).encode()).hexdigest()
    atomic_json(manifest, data)
    with pytest.raises(ValueError, match='incomplete'):
        features.load_answers(manifest, tmp_path)


def test_unsorted_prefix_fails_coverage():
    events = [event(channel=c) for c in CHANNELS]
    events = [event(hour=9, identity='later'), *events]
    with pytest.raises(ValueError, match='chronological'):
        features.coverage_from_events(events)


def test_live_and_unknown_store_rejected(tmp_path):
    import sqlite3
    database = tmp_path / 'live.sqlite'
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE events(secret TEXT)')
    with pytest.raises(ValueError, match='Incompatible'):
        features.read_events(database, tmp_path)
    with pytest.raises(ValueError, match='inside'):
        features.read_events(Path('/tmp/live.sqlite'), tmp_path)


def test_observable_subject_can_differ_from_incident_actor(tmp_path):
    manifest = answer_manifest(tmp_path)
    data = json.loads(manifest.read_text())
    data['members'][1]['header'][3] = 'victim'
    data.pop('manifest_sha256')
    data['manifest_sha256'] = hashlib.sha256(encoded(data).encode()).hexdigest()
    atomic_json(manifest, data)
    _, incidents, rows = features.load_answers(manifest, tmp_path)
    assert incidents[0]['user'] == 'a'
    assert rows[0]['metadata']['user'] == 'victim'
    labels, _ = features.join_labels([event(user='victim')], rows)
    assert labels[('d', 'file.csv', '1')]['label'] == 1
