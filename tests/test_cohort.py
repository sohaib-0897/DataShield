import io
import json
from pathlib import Path
import sqlite3
import tarfile

import pytest

from research.cert_ingest import SOURCES, ingest, verified_manifest
from research.cohort import cohort_scan


def fixture(path, *, reverse=False, unsafe=False):
    import csv
    with tarfile.open(path, 'w:bz2') as tar:
        for filename, spec in SOURCES.items():
            stream = io.StringIO()
            writer = csv.writer(stream)
            writer.writerow(spec['header'])
            days = [1, 7, 8, 9, 10]
            if reverse: days.reverse()
            for index, day in enumerate(days):
                data = dict.fromkeys(spec['header'], 'value')
                data.update(id=f'id-{day}', date=f'06/{day:02}/2010 10:00:00', user='AAA0001', pc='PC-1', activity='Logon' if filename == 'logon.csv' else 'Connect')
                writer.writerow([data[k] for k in spec['header']])
            raw = stream.getvalue().encode()
            info = tarfile.TarInfo('../escape' if unsafe else f'r4.2/{filename}')
            info.size = len(raw)
            tar.addfile(info, io.BytesIO(raw))


def test_cohort_keeps_natural_population_and_original_rows(tmp_path):
    archive, folder = tmp_path/'sample.bz2', tmp_path/'research'
    fixture(archive)
    manifest = cohort_scan(archive, folder, '2010-06-07', '2010-06-10', progress=None)
    value = verified_manifest(manifest, folder)
    assert value['full_source_scan'] and not value['full_dataset_retained']
    assert all(m['cached_rows'] == 3 for m in value['members'])
    db = folder/'events.sqlite'
    first = ingest(manifest, folder, db, chunk=2, progress_log=None)
    assert first['events'] == 15 and first['errors'] == 0
    assert first['full_dataset_ingested'] is False
    assert ingest(manifest, folder, db, chunk=2, progress_log=None) == first
    with sqlite3.connect(db) as con:
        assert {r[0] for r in con.execute('SELECT source_row FROM events')} == {2,3,4}
        assert {r[0] for r in con.execute('SELECT username FROM events')} == {'AAA0001'}


@pytest.mark.parametrize('failure', ['reverse', 'unsafe', 'events', 'cache'])
def test_cohort_rejects_failures_without_manifest(tmp_path, failure):
    archive, folder = tmp_path/'sample.bz2', tmp_path/'research'
    fixture(archive, reverse=failure=='reverse', unsafe=failure=='unsafe')
    settings = {'max_events': 2} if failure == 'events' else {'max_cache': 20} if failure == 'cache' else {}
    with pytest.raises(ValueError):
        cohort_scan(archive, folder, '2010-06-07', '2010-06-10', progress=None, **settings)
    assert not list(folder.rglob('manifest.json'))


def test_cohort_resume_committed_chunks(tmp_path):
    archive, folder = tmp_path/'sample.bz2', tmp_path/'research'
    fixture(archive)
    manifest = cohort_scan(archive, folder, '2010-06-07', '2010-06-10', progress=None)
    db = folder/'events.sqlite'
    def interrupt(source, count): raise RuntimeError('interrupted')
    with pytest.raises(RuntimeError):
        ingest(manifest, folder, db, chunk=2, progress_log=None, after_chunk=interrupt)
    result = ingest(manifest, folder, db, chunk=2, progress_log=None)
    assert result['events'] == 15
