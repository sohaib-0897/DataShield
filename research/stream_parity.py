"""Full row/text parity against a frozen materialized CERT artifact."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import resource
import sqlite3
import time

from research.cert_features import load_artifact
from research.cert_ingest import atomic_json, encoded, local_path, hash_file
from research.text_study import attach_text


def verify(prepared, frozen, database, folder, max_bytes=512*1024**2):
    started=time.perf_counter()
    feature=load_artifact(frozen,folder,max_bytes)
    with closing(sqlite3.connect(local_path(folder,prepared).as_uri()+'?mode=ro',uri=True)) as db, closing(sqlite3.connect(local_path(folder,database).as_uri()+'?mode=ro',uri=True)) as source:
        source.row_factory=sqlite3.Row
        contract=json.loads(db.execute("SELECT value FROM meta WHERE key='contract'").fetchone()[0])
        if contract['store_sha256'] != feature['store_sha256'] or hash_file(database)['sha256'] != feature['store_sha256']:
            raise ValueError('Snapshot mismatch')
        windows=feature.pop('windows')
        if db.execute('SELECT count(*) FROM windows').fetchone()[0] != len(windows):
            raise AssertionError('Window counts differ')
        for w in windows:
            payload,text=db.execute('SELECT payload,text FROM windows WHERE start=? AND user=?',(w['start'],w['user'])).fetchone()
            if json.loads(payload) != w:
                raise AssertionError('Feature/label/event-order parity failed')
            events=[]
            for key in w['event_keys']:
                row=source.execute('SELECT * FROM events WHERE dataset_sha256=? AND source_file=? AND source_id=?',key).fetchone()
                if row is None:
                    raise AssertionError('Missing frozen event')
                events.append(dict(row))
            expected=attach_text([w],events)[0]
            if expected['text'] != text:
                raise AssertionError('Text ordering/mapping parity failed')
            actual={h for (h,) in db.execute('SELECT hash FROM window_bags WHERE start=? AND user=?',(w['start'],w['user']))}
            if actual != expected['text_hashes']:
                raise AssertionError('Bag parity failed')
    return {'frozen_artifact_sha256':feature['artifact_sha256'],'windows_compared':len(windows),
            'features_labels_event_keys_text_bags_equal':True,'seconds':time.perf_counter()-started,
            'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('prepared','frozen','database','report'):p.add_argument('--'+arg,required=True,type=Path)
    a=p.parse_args();folder=Path('research/local').absolute();output=local_path(folder,a.report)
    if output.exists() or output in {a.prepared.absolute(),a.frozen.absolute(),a.database.absolute()}:
        raise ValueError('New separate report required')
    result=verify(a.prepared,a.frozen,a.database,folder);atomic_json(output,result);print(encoded(result))

if __name__=='__main__':main()
