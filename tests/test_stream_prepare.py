import json
import sqlite3
from datetime import datetime

import pytest

from ml.features.windows import CHANNELS, build_windows
from research.cert_features import ExactLabelJoiner, join_labels
from research.cert_ingest import SCHEMA, encoded
from research.stream_prepare import prepared_hour, prepare
from tests.test_cert_features import event, observable, answer_manifest, COVERAGE


def source(tmp_path):
    path=tmp_path/'source.sqlite'
    with sqlite3.connect(path) as db:
        db.executescript(SCHEMA);db.execute('PRAGMA application_id=1128616532');db.execute('PRAGMA user_version=1')
        for hour in range(8,11):
            for i,c in enumerate(CHANNELS):
                e=event(hour=hour,identity=f'{c}{hour}',channel=c);e['source_row']=hour
                db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                           (e['dataset_sha256'],e['source_file'],e['source_id'],hour,e['username'],e['pc'],'date',e['timestamp_local'],
                            'unspecified_release_local',c,'action',None,e['metadata_json'],'hash'))
    return path


def test_stream_hour_parity_past_only_and_unknown_label():
    events=[dict(event(hour=h,identity=f'{h}-{c}',channel=c),source_row=h) for h in range(8,11) for c in CHANNELS]
    events[-1]['pc']='future'
    obs=[observable(events[0]),observable(events[1],incident='one'),observable(events[1],incident='two')]
    expected=build_windows(events,COVERAGE);labels,_=join_labels(events,obs)
    history=[0,0,set()];joiner=ExactLabelJoiner(obs)
    for h,w in enumerate(expected,8):
        rows=[e for e in events if datetime.fromisoformat(e['timestamp_local']).hour==h]
        rows.sort(key=lambda e:(e['source_file'],e['source_row']))
        # Match frozen source ordering.
        frozen=build_windows(rows,COVERAGE)[0]
        actual,text,bags,counts=prepared_hour(rows,COVERAGE,history,joiner)
        assert actual['features']==w['features']
        assert actual['event_keys']==frozen['event_keys']
        joined=[labels[tuple(k)] for k in actual['event_keys']]
        assert actual['label']==(1 if any(x['label']==1 for x in joined) else None if any(x['label'] is None for x in joined) else 0)
        assert text and bags


def test_interruption_rollback_resume_idempotency_and_provenance(tmp_path):
    path=source(tmp_path);answers=answer_manifest(tmp_path);out=tmp_path/'prepared.sqlite'
    with pytest.raises(InterruptedError):prepare(path,answers,out,tmp_path,interrupt_after_windows=2)
    with sqlite3.connect(out) as db:
        assert db.execute('SELECT count(*) FROM windows').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM completed').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM bags').fetchone()[0]==0
    first=prepare(path,answers,out,tmp_path);second=prepare(path,answers,out,tmp_path)
    assert first['complete'] and first['events']==15 and first['windows']==3
    assert second['users_processed_this_run']==0
    for key in ('events','windows','negative','positive','duplicate_normalized_keyword_bags'):
        assert first.get(key)==second.get(key)
    with pytest.raises(ValueError,match='mismatch'):prepare(path,answers,out,tmp_path,max_hour_events=1)


def test_bounds_and_incompatible_input(tmp_path):
    path=source(tmp_path);answers=answer_manifest(tmp_path)
    with pytest.raises(ValueError,match='memory bound'):prepare(path,answers,tmp_path/'small.sqlite',tmp_path,max_hour_bytes=1)
    with sqlite3.connect(path) as db:db.execute('PRAGMA application_id=0')
    with pytest.raises(ValueError,match='Incompatible'):prepare(path,answers,tmp_path/'bad.sqlite',tmp_path)
