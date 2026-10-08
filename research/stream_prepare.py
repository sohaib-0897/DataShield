"""Resumable read-only CERT preparation. RAM is bounded by one user-hour.

SQLite transactions publish one complete user at a time; interruption rolls back
that user. Past history is count/sum plus observed PCs, never all past events.
Raw text and join identities remain only in ignored research/local.
"""
import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime
import hashlib
from itertools import groupby
import json
from pathlib import Path
import resource
import sqlite3
import time

from ml.features.windows import CHANNELS, build_windows
from research.cert_features import ExactLabelJoiner, load_answers
from research.cert_ingest import atomic_json, encoded, hash_file, local_path, require_space
from research.text_study import normalize_keywords

VERSION = 'cert-stream-preparation-v1'
SCHEMA = '''
PRAGMA application_id=1146307412;
PRAGMA user_version=1;
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE completed(user TEXT PRIMARY KEY,counts TEXT NOT NULL);
CREATE TABLE windows(start TEXT,user TEXT,payload TEXT NOT NULL,text TEXT NOT NULL,
 PRIMARY KEY(start,user));
CREATE TABLE bags(hash TEXT PRIMARY KEY);
CREATE TABLE window_bags(start TEXT,user TEXT,hash TEXT,PRIMARY KEY(start,user,hash));
CREATE INDEX bag_lookup ON window_bags(hash);
CREATE TABLE matched(incident TEXT,row INTEGER,PRIMARY KEY(incident,row));
'''


def configure(db):
    db.execute('PRAGMA cache_size=-8192')
    db.execute('PRAGMA temp_store=FILE')
    db.execute('PRAGMA busy_timeout=1000')


def verify_source(db):
    if (db.execute('PRAGMA application_id').fetchone()[0], db.execute('PRAGMA user_version').fetchone()[0]) != (0x43455254, 1):
        raise ValueError('Incompatible CERT store')
    if db.execute("SELECT count(*) FROM events WHERE timezone_basis != 'unspecified_release_local'").fetchone()[0]:
        raise ValueError('Unsupported timestamp basis')
    datasets = db.execute('SELECT DISTINCT dataset_sha256 FROM events').fetchall()
    if len(datasets) != 1:
        raise ValueError('Require one nonempty dataset')
    # Original source position ordering establishes channel coverage, not a sort
    # that conceals an out-of-order source. SQL temporary sorts stay on disk.
    bad = db.execute('''SELECT count(*) FROM (
      SELECT timestamp_local,lag(timestamp_local) OVER (
        PARTITION BY source_file ORDER BY source_row) previous FROM events
    ) WHERE timestamp_local < previous''').fetchone()[0]
    if bad:
        raise ValueError('Sources are not chronological')
    coverage = {c: (datetime.fromisoformat(a), datetime.fromisoformat(b)) for c,a,b in
                db.execute('SELECT channel,min(timestamp_local),max(timestamp_local) FROM events GROUP BY channel')}
    if set(coverage) != set(CHANNELS):
        raise ValueError('Missing source coverage')
    return datasets[0][0], coverage


def prepared_hour(rows, coverage, history, joiner):
    # Preserve frozen event-key and text order: source_file/source_row, not event
    # timestamp order inside the hour. The hour boundary is always chronological.
    rows.sort(key=lambda e: (e['source_file'], e['source_row']))
    w = build_windows(rows, coverage)[0]
    count, total, seen = history
    mean = total / count if count else None
    pcs = {e['pc'] for e in rows}
    f = w['features']
    f.update(past_mean_total=mean, history_windows=count, cold_start=int(not count),
             total_over_past_mean=len(rows) / mean if w['fully_observed'] and mean else None,
             novel_pc_fraction=len(pcs - seen) / len(pcs) if w['fully_observed'] and count else None)
    if len(pcs | seen) > 50000:
        raise ValueError('Past PC state memory bound exceeded')
    if w['fully_observed']:
        history[0] += 1
        history[1] += len(rows)
        seen.update(pcs)
    joined = [joiner.label(e) for e in rows]
    w['label'] = 1 if any(x['label'] == 1 for x in joined) else None if any(x['label'] is None for x in joined) else 0
    w['label_provenance'] = [p for x in joined for p in x['provenance']]
    texts, hashes, nonempty = [], set(), 0
    for e in rows:
        if e['channel'] not in {'FILE', 'HTTP', 'EMAIL'}:
            continue
        normalized = normalize_keywords(json.loads(e['metadata_json']).get('content', ''), file_content=e['channel'] == 'FILE')
        if normalized:
            texts.append(normalized)
            hashes.add(hashlib.sha256(' '.join(sorted(normalized.split())).encode()).hexdigest())
            nonempty += 1
    counts = Counter()
    counts.update({0: 'negative', 1: 'positive', None: 'ambiguous_or_conflicting'}[x['label']] for x in joined)
    counts.update(events=len(rows), text_source_events=sum(e['channel'] in {'FILE','HTTP','EMAIL'} for e in rows),
                  nonempty_sanitized_text_events=nonempty, windows=1, fully_observed_windows=int(w['fully_observed']))
    return w, ' '.join(texts), hashes, counts


def prepare(database, answers, output, folder, *, stop_after_users=None, interrupt_after_windows=None,
            max_hour_bytes=16*1024**2, max_hour_events=50000):
    if max_hour_bytes < 1 or max_hour_events < 1:
        raise ValueError('Positive hour bounds required')
    database, output = local_path(folder, database), local_path(folder, output)
    if database == output:
        raise ValueError('Separate output required')
    require_space(folder)
    started = time.perf_counter()
    fingerprint = hash_file(database)['sha256']
    inspected, incidents, observables = load_answers(answers, folder)
    joiner = ExactLabelJoiner(observables)
    with closing(sqlite3.connect(database.as_uri()+'?mode=ro', uri=True)) as source, closing(sqlite3.connect(output)) as target:
        configure(source); configure(target)
        source.row_factory = sqlite3.Row
        source.execute('BEGIN')
        dataset, coverage = verify_source(source)
        contract = {'version': VERSION, 'store_sha256': fingerprint, 'dataset_sha256': dataset,
                    'answers_sha256': inspected['input']['sha256'], 'answer_manifest_sha256': inspected['manifest_sha256'],
                    'coverage': {c:[a.isoformat(),b.isoformat()] for c,(a,b) in coverage.items()},
                    'max_hour_bytes': max_hour_bytes, 'max_hour_events': max_hour_events,
                    'work_hours':[9,17], 'feature_version':'cert-user-hour-v1', 'label_version':'cert-r42-exact-observable-v1'}
        tables = target.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if not tables:
            target.executescript(SCHEMA)
            target.execute('INSERT INTO meta VALUES (?,?)', ('contract',encoded(contract)))
            target.commit()
        elif target.execute('PRAGMA application_id').fetchone()[0] != 1146307412 or target.execute('PRAGMA user_version').fetchone()[0] != 1:
            raise ValueError('Incompatible preparation output')
        if target.execute("SELECT value FROM meta WHERE key='contract'").fetchone()[0] != encoded(contract):
            raise ValueError('Resume provenance/parameters mismatch')
        processed, window_count = 0, 0
        for (user,) in source.execute('SELECT DISTINCT username FROM events ORDER BY username'):
            if target.execute('SELECT 1 FROM completed WHERE user=?',(user,)).fetchone():
                continue
            history, counters = [0, 0, set()], Counter()
            try:
                target.execute('BEGIN IMMEDIATE')
                cursor = source.execute('SELECT * FROM events WHERE username=? ORDER BY timestamp_local,source_file,source_row',(user,))
                for _, group in groupby(cursor, key=lambda e:e['timestamp_local'][:13]):
                    rows, used = [], 0
                    for row in group:
                        used += len(row['metadata_json'].encode()) + len((row['resource'] or '').encode())
                        if used > max_hour_bytes or len(rows) >= max_hour_events:
                            raise ValueError('User-hour memory bound exceeded')
                        rows.append(dict(row))
                    w, text, hashes, counts = prepared_hour(rows, coverage, history, joiner)
                    counters.update(counts)
                    target.execute('INSERT INTO windows VALUES (?,?,?,?)',(w['start'],user,encoded(w),text))
                    target.executemany('INSERT OR IGNORE INTO bags VALUES (?)', ((h,) for h in hashes))
                    target.executemany('INSERT INTO window_bags VALUES (?,?,?)', ((w['start'],user,h) for h in hashes))
                    target.executemany('INSERT OR IGNORE INTO matched VALUES (?,?)',((p['incident'],p['row']) for p in w['label_provenance']))
                    window_count += 1
                    if interrupt_after_windows and window_count == interrupt_after_windows:
                        raise InterruptedError('Injected interruption before user checkpoint')
                target.execute('INSERT INTO completed VALUES (?,?)',(user,encoded(counters)))
                target.commit()
            except BaseException:
                target.rollback()
                raise
            processed += 1
            if processed % 50 == 0:
                print(encoded({'completed_users_this_run':processed}), flush=True)
            if stop_after_users and processed >= stop_after_users:
                break
        counters = Counter()
        for (counts,) in target.execute('SELECT counts FROM completed'):
            counters.update(json.loads(counts))
        complete = target.execute('SELECT count(*) FROM completed').fetchone()[0] == source.execute('SELECT count(DISTINCT username) FROM events').fetchone()[0]
        if hash_file(database)['sha256'] != fingerprint:
            raise ValueError('Source changed during preparation')
        report = {**contract, **counters, 'complete':complete, 'users_processed_this_run':processed,
                  'completed_users':target.execute('SELECT count(*) FROM completed').fetchone()[0],
                  'unmatched_observables':len(observables)-target.execute('SELECT count(*) FROM matched').fetchone()[0],
                  'duplicate_normalized_keyword_bags': counters['nonempty_sanitized_text_events']-target.execute('SELECT count(*) FROM bags').fetchone()[0],
                  'seconds_this_run':time.perf_counter()-started, 'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                  'checkpoint_unit':'atomic complete user; incomplete user rolls back', 'full_dataset':False,
                  'live_activation':False}
        if processed or not target.execute("SELECT 1 FROM meta WHERE key='report'").fetchone():
            target.execute('INSERT OR REPLACE INTO meta VALUES (?,?)',('report',encoded(report)))
            target.commit()
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--database',type=Path,required=True); p.add_argument('--answers',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True); p.add_argument('--report',type=Path,required=True)
    p.add_argument('--stop-after-users',type=int)
    a=p.parse_args(); folder=Path('research/local').absolute()
    report_path=local_path(folder,a.report)
    if report_path.exists() or report_path in {a.database.absolute(),a.output.absolute(),a.answers.absolute()}:
        raise ValueError('Report must be new and separate')
    result=prepare(a.database,a.answers,a.output,folder,stop_after_users=a.stop_after_users)
    atomic_json(report_path,result); print(encoded(result))

if __name__=='__main__':
    main()
