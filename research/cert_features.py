"""Exact r4.2 ground truth and features in separate, ignored research artifacts."""
import argparse
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import sqlite3

from research.cert_ingest import SOURCES, atomic_json, encoded, hash_file, local_path, require_space, verified_manifest
from ml.features.windows import CHANNELS, FEATURE_NAMES, VERSION, build_windows

LABEL_VERSION = 'cert-r42-exact-observable-v1'


def cached_rows(member, folder):
    with (folder / member['cache']).open(encoding='utf-8') as stream:
        for line in stream:
            yield json.loads(line)


def load_answers(manifest, folder):
    """Observable files have NO header: inspector's header is the first event."""
    inspected = verified_manifest(manifest, folder)
    by_name = defaultdict(list)
    for member in inspected['members']:
        by_name[PurePosixPath(member['name']).name].append(member)
    masters = by_name['insiders.csv']
    if len(masters) != 1 or masters[0]['header'] != ['dataset', 'scenario', 'details', 'user', 'start', 'end']:
        raise ValueError('Unsupported master answers contract')
    if not masters[0]['complete']:
        raise ValueError('Incomplete master answers')
    observables, incidents = [], []
    for row in cached_rows(masters[0], folder):
        if len(row) != 6:
            raise ValueError('Malformed master answers')
        release, scenario, detail, user, start, end = row
        if release != '4.2':
            continue
        start = datetime.strptime(start, '%m/%d/%Y %H:%M:%S')
        end = datetime.strptime(end, '%m/%d/%Y %H:%M:%S')
        matches = by_name[detail]
        if len(matches) != 1 or not matches[0]['name'].startswith(f'answers/r4.2-{scenario}/'):
            raise ValueError('Missing or ambiguous incident file')
        member = matches[0]
        if not member['complete'] or scenario not in {'1', '2', '3'} or start > end:
            raise ValueError('Unsupported or incomplete incident')
        incident = {'detail': detail, 'scenario': scenario, 'user': user,
                    'start': start.isoformat(), 'end': end.isoformat()}
        incidents.append(incident)
        for position, values in enumerate([member['header'], *cached_rows(member, folder)], 1):
            source = f'{values[0]}.csv' if values else ''
            if source not in SOURCES or len(values) != len(SOURCES[source]['header']) + 1:
                raise ValueError('Unsupported observable record')
            metadata = dict(zip(SOURCES[source]['header'], values[1:]))
            when = datetime.strptime(metadata['date'], '%m/%d/%Y %H:%M:%S')
            if not start <= when <= end:
                raise ValueError('Observable outside incident time')
            observables.append({'source': source, 'id': metadata['id'], 'metadata': metadata,
                                'incident': detail, 'scenario': scenario, 'row': position})
    if not incidents:
        raise ValueError('No r4.2 incidents')
    return inspected, incidents, observables


def join_labels(events, observables):
    """Require scoped ID AND all source fields; conflicts remain unknown, never benign."""
    index = defaultdict(list)
    for observable in observables:
        index[(observable['source'], observable['id'])].append(observable)
    labels, reasons = {}, Counter()
    matched = set()
    for event in events:
        key = (event['dataset_sha256'], event['source_file'], event['source_id'])
        candidates = index[(event['source_file'], event['source_id'])]
        actual = json.loads(event['metadata_json'])
        if not candidates:
            labels[key] = {'label': 0, 'provenance': [], 'reason': 'not_in_complete_answers'}
            reasons['negative'] += 1
            continue
        exact = [o for o in candidates if o['metadata'] == actual]
        if len(exact) != len(candidates) or len({o['incident'] for o in exact}) != 1:
            labels[key] = {'label': None, 'provenance': [], 'reason': 'ambiguous_or_conflicting'}
            reasons['ambiguous_or_conflicting'] += 1
            continue
        labels[key] = {'label': 1, 'reason': 'exact_all_fields',
                       'provenance': [{'incident': o['incident'], 'row': o['row'], 'scenario': o['scenario']} for o in exact]}
        reasons['positive'] += 1
        for o in exact:
            matched.add((o['incident'], o['row']))
    reasons['unmatched_observables'] = sum((o['incident'], o['row']) not in matched for o in observables)
    return labels, dict(reasons)


def read_events(database, folder, max_events=100000):
    database = local_path(folder, database)
    if not database.is_file():
        raise ValueError('Missing research store')
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
        if db.execute('PRAGMA application_id').fetchone()[0] != 0x43455254 or db.execute('PRAGMA user_version').fetchone()[0] != 1:
            raise ValueError('Incompatible CERT store')
        db.row_factory = sqlite3.Row
        if db.execute('SELECT count(*) FROM events').fetchone()[0] > max_events:
            raise ValueError('Event memory bound exceeded; use a bounded research store')
        events = [dict(r) for r in db.execute('SELECT * FROM events ORDER BY source_file,source_row')]
    if not events or len({e['dataset_sha256'] for e in events}) != 1:
        raise ValueError('Require one nonempty dataset')
    if any(e['timezone_basis'] != 'unspecified_release_local' for e in events):
        raise ValueError('Unsupported timestamp basis')
    return events


def coverage_from_events(events):
    times = defaultdict(list)
    for e in events:
        times[e['channel']].append(datetime.fromisoformat(e['timestamp_local']))
    if set(times) != set(CHANNELS):
        raise ValueError('Missing CERT source coverage')
    if any(values != sorted(values) for values in times.values()):
        raise ValueError('Prefixes are not chronological; cannot establish coverage')
    return {c: (min(v), max(v)) for c, v in times.items()}


def prepare(database, answer_manifest, folder, output, *, work_start=9, work_end=17, max_events=100000):
    output = local_path(folder, output)
    if output.exists():
        raise ValueError('Artifact already exists; preserve it and choose a new output')
    require_space(folder)
    answers, incidents, observables = load_answers(answer_manifest, folder)
    events = read_events(database, folder, max_events)
    labels, audit = join_labels(events, observables)
    coverage = coverage_from_events(events)
    windows = build_windows(events, coverage, work_start=work_start, work_end=work_end)
    for w in windows:
        joined = [labels[tuple(key)] for key in w['event_keys']]
        w['label'] = 1 if any(x['label'] == 1 for x in joined) else None if any(x['label'] is None for x in joined) else 0
        w['label_provenance'] = [p for x in joined for p in x['provenance']]
    # Identity/provenance below are evaluation join keys, NEVER matrix inputs.
    artifact = {'feature_version': VERSION, 'label_version': LABEL_VERSION, 'feature_names': FEATURE_NAMES,
                'dataset_sha256': events[0]['dataset_sha256'], 'store_sha256': hash_file(database)['sha256'],
                'answers_sha256': answers['input']['sha256'], 'answer_manifest_sha256': answers['manifest_sha256'],
                'work_hours': [work_start, work_end], 'weekdays': [0, 1, 2, 3, 4],
                'coverage': {c: [a.isoformat(), b.isoformat()] for c, (a, b) in coverage.items()},
                'windows': windows}
    artifact['artifact_sha256'] = hashlib.sha256(encoded(artifact).encode()).hexdigest()
    atomic_json(output, artifact)
    report = {'feature_version': VERSION, 'label_version': LABEL_VERSION, 'dataset_sha256': artifact['dataset_sha256'],
              'store_sha256': artifact['store_sha256'], 'answers_sha256': artifact['answers_sha256'],
              'feature_artifact_sha256': artifact['artifact_sha256'], 'events': len(events), 'full_dataset': False,
              'incidents': len(incidents), 'observables': len(observables),
              'scenarios': dict(Counter(i['scenario'] for i in incidents)),
              'observable_actor_identity_differences': sum(o['metadata']['user'] != next(i['user'] for i in incidents if i['detail'] == o['incident']) for o in observables),
              'labels': audit,
              'windows': len(windows), 'fully_observed_windows': sum(w['fully_observed'] for w in windows),
              'unknown_windows': sum(w['label'] is None for w in windows), 'coverage': artifact['coverage'],
              'work_hours': artifact['work_hours'], 'active_user_hours_only': True}
    return report


def load_artifact(path, folder):
    path = local_path(folder, path)
    value = json.loads(path.read_text())
    expected = value.pop('artifact_sha256')
    if hashlib.sha256(encoded(value).encode()).hexdigest() != expected:
        raise ValueError('Feature artifact changed')
    value['artifact_sha256'] = expected
    if value['feature_version'] != VERSION or tuple(value['feature_names']) != FEATURE_NAMES:
        raise ValueError('Incompatible feature contract')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--answers', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--work-start', type=int, default=9)
    parser.add_argument('--work-end', type=int, default=17)
    parser.add_argument('--max-events', type=int, default=100000)
    args = parser.parse_args()
    folder = Path('research/local').absolute()
    report_path = local_path(folder, args.report)
    if report_path.exists() or report_path == args.output.absolute() or report_path == args.database.absolute() or report_path == args.answers.absolute():
        raise ValueError('Report must be a new separate artifact')
    report = prepare(args.database, args.answers, folder, args.output, work_start=args.work_start,
                     work_end=args.work_end, max_events=args.max_events)
    atomic_json(report_path, report)
    print(encoded(report))


if __name__ == '__main__':
    main()
