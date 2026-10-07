"""Full safe archive scan, retaining a predeclared contiguous chronological cohort.

All users and events within [start,end) are retained; answers are never consulted.
Indexed caches preserve ORIGINAL CSV record positions and reuse chunked ingestion.
"""
import argparse
import bz2
import csv
from datetime import datetime
import hashlib
import io
from pathlib import Path, PurePosixPath
import tarfile
import tempfile
import time

from research.cert_ingest import (ForwardMember, RecordLines, MAX_FIELD, SOURCES, VERSION,
                                  atomic_json, encoded, hash_file, local_path, require_space,
                                  safe_member, stat_identity)


def cohort_scan(archive_path, folder, start, end, *, max_cache=1024**3, max_events=1000000,
                max_expanded=32*1024**3, progress=print):
    start, end = datetime.fromisoformat(start), datetime.fromisoformat(end)
    if start.tzinfo or end.tzinfo or start >= end or min(max_cache, max_events, max_expanded) < 1:
        raise ValueError('Invalid bounded cohort settings')
    folder = local_path(folder, folder)
    folder.mkdir(parents=True, exist_ok=True)
    require_space(folder, max_cache)
    before, fingerprint = stat_identity(archive_path), hash_file(archive_path)
    staging = Path(tempfile.mkdtemp(prefix='cohort-', dir=folder))
    seen, members, selected, cached, expanded = set(), [], 0, 0, 0
    begin, last_log = time.monotonic(), time.monotonic()
    csv.field_size_limit(MAX_FIELD)
    with bz2.BZ2File(archive_path, 'rb') as source, tarfile.open(fileobj=source, mode='r|') as archive:
        for member in archive:
            if len(members) >= 100000:
                raise ValueError('Member count budget')
            name = safe_member(member, seen)
            expanded += member.size
            if expanded > max_expanded:
                raise ValueError('Expanded size budget')
            record = {'name': name, 'bytes': member.size, 'type': 'file' if member.isfile() else 'directory'}
            filename = PurePosixPath(name).name
            if member.isfile() and name == f'r4.2/{filename}' and filename in SOURCES:
                target = staging/f'rows-{len(members):05d}.jsonl'
                raw = io.BufferedReader(ForwardMember(archive.extractfile(member)))
                with io.TextIOWrapper(raw, encoding='utf-8-sig', newline='') as text, target.open('x') as output:
                    lines = RecordLines(text)
                    reader = csv.reader(lines, strict=True)
                    header = next(reader, [])
                    lines.reset()
                    if header != SOURCES[filename]['header']:
                        raise ValueError('Unsupported release header')
                    previous, count, rows = None, 0, 0
                    for rows, values in enumerate(reader, 1):
                        lines.reset()
                        if len(values) != len(header):
                            raise ValueError('Malformed source row during chronological scan')
                        date = values[1]
                        # Fixed release format; fromisoformat avoids expensive strptime
                        # calls for the full archive. Strict shape/calendar validation.
                        if len(date) != 19 or date[2] != '/' or date[5] != '/' or date[10] != ' ':
                            raise ValueError('Unsupported release timestamp')
                        when = datetime.fromisoformat(date[6:10]+'-'+date[:2]+'-'+date[3:5]+'T'+date[11:])
                        if previous is not None and when < previous:
                            raise ValueError('Nonchronological source; coverage cannot be inferred')
                        previous = when
                        if start <= when < end:
                            line = encoded({'source_row': rows, 'values': values})+'\n'
                            cached += len(line.encode())
                            selected += 1
                            if cached > max_cache or selected > max_events:
                                raise ValueError('Cohort cache/event budget exceeded; no manifest published')
                            output.write(line)
                            count += 1
                        now = time.monotonic()
                        if now-last_log >= 30:
                            require_space(folder)
                            if progress:
                                progress(encoded({'source': filename, 'scanned_rows': rows, 'selected_rows': count,
                                                  'total_selected': selected, 'cache_bytes': cached,
                                                  'elapsed_seconds': round(now-begin, 1)}))
                            last_log = now
                record.update(header=header, cache=str(target.relative_to(folder)), cache_hash=hash_file(target)['sha256'],
                              cached_rows=count, complete=True, cache_format='indexed-v1', source_rows=rows)
            members.append(record)
            if progress:
                progress(encoded({'member': name, 'selected_rows': record.get('cached_rows'),
                                  'source_rows': record.get('source_rows'), 'elapsed_seconds': round(time.monotonic()-begin, 1)}))
        while source.read(1024**2):
            pass
    if stat_identity(archive_path) != before:
        raise ValueError('Archive changed')
    if {m['name'] for m in members if 'cache' in m} != {f'r4.2/{s}' for s in SOURCES}:
        raise ValueError('Missing release event source')
    result = {'version': VERSION, 'archive': archive_path.name, 'input': fingerprint,
              'row_bound_per_member': max_events, 'members': members, 'expanded_bytes': expanded,
              'cached_bytes': cached, 'all_members_validated': True, 'elapsed_seconds': round(time.monotonic()-begin, 3),
              'cohort': {'start_inclusive': start.isoformat(), 'end_exclusive': end.isoformat(),
                         'selection': 'all users/events in predeclared contiguous interval; labels not consulted'},
              'full_source_scan': True, 'full_dataset_retained': False}
    result['manifest_sha256'] = hashlib.sha256(encoded(result).encode()).hexdigest()
    manifest = staging/'manifest.json'
    atomic_json(manifest, result)
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--start', required=True)
    p.add_argument('--end', required=True)
    p.add_argument('--max-events', type=int, default=1000000)
    p.add_argument('--max-cache-mib', type=int, default=1024)
    a = p.parse_args()
    manifest = cohort_scan(a.archive, Path('research/local').absolute(), a.start, a.end,
                           max_events=a.max_events, max_cache=a.max_cache_mib*1024**2)
    print(encoded({'manifest': str(manifest)}))


if __name__ == '__main__':
    main()
