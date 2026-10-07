import bz2
import csv
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tarfile

import pytest

spec = importlib.util.spec_from_file_location('cert_ingest', Path(__file__).resolve().parents[1] / 'research/cert_ingest.py')
cert = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cert)
RELEASE_SOURCES = cert.SOURCES


@pytest.fixture(autouse=True)
def sources(monkeypatch):
    # Minimal source contract; release-contract checks below use the real mapping.
    monkeypatch.setattr(cert, 'SOURCES', {'file.csv': {'header': ['id', 'date', 'user', 'pc', 'filename', 'content'],
                                                    'channel': 'FILE', 'action': 'copy', 'resource': 'filename'}})


def csv_bytes(rows, header=None):
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(header or cert.SOURCES['file.csv']['header'])
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def row(identity='event-1', user='u1', content='quoted, content\nsecond line'):
    return [identity, '01/02/2010 03:04:05', user, 'pc1', 'C:\\test.txt', content]


def make_archive(tmp_path, entries=None, multistream=False):
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode='w') as tar:
        for name, content, kind in entries or [('r4.2/file.csv', csv_bytes([row()]), None)]:
            member = tarfile.TarInfo(name)
            if kind:
                member.type = kind
                member.linkname = '../../escape'
                tar.addfile(member)
            else:
                member.size = len(content)
                tar.addfile(member, io.BytesIO(content))
    raw = payload.getvalue()
    path = tmp_path / 'r4.2.tar.bz2'
    if multistream:
        middle = len(raw) // 2
        path.write_bytes(bz2.compress(raw[:middle]) + bz2.compress(raw[middle:]))
    else:
        path.write_bytes(bz2.compress(raw))
    return path


def scan(tmp_path, entries=None, rows=10, **kwargs):
    archive = make_archive(tmp_path, entries)
    folder = tmp_path / 'local'
    manifest = cert.inspect_archive(archive, folder, rows=rows, reserve=0, progress=None, **kwargs)
    return manifest, folder, folder / 'events.sqlite'


@pytest.mark.parametrize('name', ['../escape.csv', '/absolute.csv', 'r4.2/../../escape.csv', 'C:/escape.csv', 'r4.2\\escape.csv'])
def test_unsafe_paths(tmp_path, name):
    with pytest.raises(ValueError, match='Unsafe'):
        scan(tmp_path, [(name, b'data', None)])
    assert not list((tmp_path / 'local').glob('*/manifest.json'))
    assert not (tmp_path / 'escape.csv').exists()


@pytest.mark.parametrize('kind', [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE, tarfile.CHRTYPE])
def test_links_and_special_files_rejected(tmp_path, kind):
    with pytest.raises(ValueError, match='forbidden'):
        scan(tmp_path, [('r4.2/file.csv', b'', kind)])


def test_duplicate_paths_and_size_budget(tmp_path):
    with pytest.raises(ValueError, match='Duplicate'):
        scan(tmp_path, [('r4.2/file.csv', csv_bytes([row()]), None)] * 2)
    with pytest.raises(ValueError, match='expanded-size'):
        scan(tmp_path, max_expanded=1)


def test_multistream_crc_and_truncation(tmp_path):
    archive = make_archive(tmp_path, multistream=True)
    manifest = cert.inspect_archive(archive, tmp_path / 'good', reserve=0, progress=None)
    assert cert.verified_manifest(manifest, tmp_path / 'good')['all_members_validated']
    archive.write_bytes(archive.read_bytes()[:-20])
    with pytest.raises((EOFError, OSError, tarfile.ReadError)):
        cert.inspect_archive(archive, tmp_path / 'bad', reserve=0, progress=None)
    assert not list((tmp_path / 'bad').glob('*/manifest.json'))


def test_idempotency_preserves_raw_data_and_user_identity(tmp_path):
    manifest, folder, database = scan(tmp_path, [('r4.2/file.csv', csv_bytes([row(), row('event-2', 'u2')]), None)])
    report = cert.ingest(manifest, folder, database, reserve=0, progress_log=None)
    again = cert.ingest(manifest, folder, database, reserve=0, progress_log=None)
    assert report == again
    assert report['events'] == 2 and report['errors'] == 0
    with sqlite3.connect(database) as db:
        events = db.execute('SELECT username,timestamp_raw,timestamp_local,timezone_basis,channel,action,metadata_json FROM events ORDER BY source_id').fetchall()
    assert [e[0] for e in events] == ['u1', 'u2']
    assert events[0][1:6] == ('01/02/2010 03:04:05', '2010-01-02T03:04:05', 'unspecified_release_local', 'FILE', 'copy')
    assert json.loads(events[0][6])['content'] == row()[-1]
    assert not report['labels_created']


def test_atomic_resume_and_bound_extension(tmp_path):
    manifest, folder, database = scan(tmp_path, [('r4.2/file.csv', csv_bytes([row(str(i)) for i in range(8)]), None)])
    def interrupted(source, position):
        raise RuntimeError('simulated interruption after committed chunk')
    with pytest.raises(RuntimeError):
        cert.ingest(manifest, folder, database, chunk=2, reserve=0, after_chunk=interrupted, progress_log=None)
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT count(*) FROM events').fetchone()[0] == 2
        assert db.execute('SELECT processed FROM progress').fetchone()[0] == 2
    small = cert.ingest(manifest, folder, database, limit=4, chunk=2, reserve=0, progress_log=None)
    assert small['events'] == 4 and not small['full_dataset_ingested']
    full = cert.ingest(manifest, folder, database, limit=10, chunk=3, reserve=0, progress_log=None)
    assert full['events'] == 8 and full['full_dataset_ingested']


def test_uncommitted_chunk_rolls_back(tmp_path, monkeypatch):
    manifest, folder, database = scan(tmp_path, [('r4.2/file.csv', csv_bytes([row(str(i)) for i in range(6)]), None)])
    original = cert.normalize
    def interrupted(filename, header, values):
        if values[0] == '3':
            raise RuntimeError('uncommitted chunk interruption')
        return original(filename, header, values)
    monkeypatch.setattr(cert, 'normalize', interrupted)
    with pytest.raises(RuntimeError):
        cert.ingest(manifest, folder, database, chunk=2, reserve=0, progress_log=None)
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT count(*) FROM events').fetchone()[0] == 2
        assert db.execute('SELECT processed FROM progress').fetchone()[0] == 2
    monkeypatch.setattr(cert, 'normalize', original)
    assert cert.ingest(manifest, folder, database, reserve=0, progress_log=None)['events'] == 6


def test_row_reconciliation_duplicates_conflicts_and_malformed_rows(tmp_path):
    malformed = row('bad-time')
    malformed[1] = 'invalid'
    missing = row('bad-user')
    missing[2] = ''
    data = [row(), row(), row(content='conflicting content'), [], ['short'], malformed, missing]
    manifest, folder, database = scan(tmp_path, [('r4.2/file.csv', csv_bytes(data), None)])
    report = cert.ingest(manifest, folder, database, chunk=2, reserve=0, progress_log=None)
    assert report['progress'] == [{'source': 'file.csv', 'processed': 7, 'valid': 2, 'inserted': 1, 'duplicates': 1, 'invalid': 5}]
    with sqlite3.connect(database) as db:
        reasons = {r[0] for r in db.execute('SELECT reason FROM diagnostics')}
    assert reasons == {'conflicting_source_id', 'empty_row', 'field_count', 'invalid_timestamp', 'missing_user'}


def test_empty_source_and_unsupported_header(tmp_path):
    manifest, folder, database = scan(tmp_path, [('r4.2/file.csv', csv_bytes([]), None)])
    assert cert.ingest(manifest, folder, database, reserve=0, progress_log=None)['events'] == 0
    manifest, folder, database = scan(tmp_path, [('r4.2/file.csv', b'id,date\n1,date\n', None)])
    with pytest.raises(ValueError, match='header'):
        cert.ingest(manifest, folder, database, reserve=0, progress_log=None)


def test_cache_and_manifest_integrity(tmp_path):
    manifest, folder, database = scan(tmp_path)
    data = json.loads(manifest.read_text())
    cache = folder / data['members'][0]['cache']
    cache.write_text('[]\n')
    with pytest.raises(ValueError, match='prefix changed'):
        cert.ingest(manifest, folder, database, reserve=0, progress_log=None)
    data['all_members_validated'] = False
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='manifest changed'):
        cert.ingest(manifest, folder, database, reserve=0, progress_log=None)


def test_symlink_and_external_research_destinations(tmp_path):
    folder = tmp_path / 'local'
    folder.mkdir()
    (folder / 'escape').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='Symlinked'):
        cert.local_path(folder, folder / 'escape' / 'activity.db')
    with pytest.raises(ValueError, match='inside'):
        cert.local_path(folder, tmp_path / 'activity.db')
    with pytest.raises(ValueError, match='inside'):
        cert.local_path(folder, folder / '..' / 'activity.db')


def test_disk_limits_before_scan_and_during_ingestion(tmp_path, monkeypatch):
    manifest, folder, database = scan(tmp_path)
    from collections import namedtuple
    Usage = namedtuple('Usage', 'total used free')
    monkeypatch.setattr(cert.shutil, 'disk_usage', lambda _: Usage(100, 99, 1))
    with pytest.raises(OSError, match='disk space'):
        cert.inspect_archive(tmp_path / 'r4.2.tar.bz2', folder, reserve=100, progress=None)
    with pytest.raises(OSError, match='disk space'):
        cert.ingest(manifest, folder, database, reserve=100, progress_log=None)
    assert not database.exists()


def test_prefix_quota_and_record_limits(tmp_path, monkeypatch):
    manifest, folder, database = scan(tmp_path, [('r4.2/file.csv', csv_bytes([row(str(i)) for i in range(20)]), None)], rows=3)
    info = cert.verified_manifest(manifest, folder)
    assert info['members'][0]['cached_rows'] == 3 and not info['members'][0]['complete']
    assert cert.ingest(manifest, folder, database, reserve=0, progress_log=None)['events'] == 3
    with pytest.raises(ValueError, match='exceeds prepared prefix'):
        cert.ingest(manifest, folder, database, limit=4, reserve=0, progress_log=None)
    with pytest.raises(ValueError, match='cache budget'):
        scan(tmp_path, max_cache=1)
    monkeypatch.setattr(cert, 'MAX_RECORD', 50)
    with pytest.raises(ValueError, match='Oversized'):
        scan(tmp_path)


def test_malformed_csv_fails_closed(tmp_path):
    with pytest.raises(csv.Error):
        scan(tmp_path, [('r4.2/file.csv', b'id,date,user,pc,filename,content\n"unterminated', None)])


def test_all_actual_release_sources_and_cross_file_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(cert, 'SOURCES', RELEASE_SOURCES)
    entries = []
    for filename, definition in RELEASE_SOURCES.items():
        values = {'id': 'same-id', 'date': '01/02/2010 03:04:05', 'user': 'u1', 'pc': 'pc1',
                  'filename': 'C:\\fixture.txt', 'url': 'https://example.invalid/a',
                  'activity': 'Logon' if filename == 'logon.csv' else 'Connect',
                  'to': 'recipient@example.invalid', 'cc': '', 'bcc': '',
                  'from': 'sender@example.invalid', 'size': '42', 'attachments': '2', 'content': 'fixture'}
        header = definition['header']
        entries.append(('r4.2/' + filename, csv_bytes([[values[c] for c in header]], header), None))
    entries.append(('r4.2/LDAP/2010-01.csv', b'user_id,role\nu1,ITAdmin\n', None))
    manifest, folder, database = scan(tmp_path, entries)
    report = cert.ingest(manifest, folder, database, reserve=0, progress_log=None)
    assert report['events'] == 5 and report['errors'] == 0
    with sqlite3.connect(database) as db:
        actual = dict(db.execute('SELECT source_file,action FROM events'))
        assert actual == {'file.csv': 'copy_to_removable_media', 'http.csv': 'visit',
                          'email.csv': 'send', 'logon.csv': 'Logon', 'device.csv': 'Connect'}
        assert db.execute("SELECT channel FROM events WHERE source_file='http.csv'").fetchone()[0] == 'HTTP'
        meta = json.loads(db.execute("SELECT metadata_json FROM events WHERE source_file='email.csv'").fetchone()[0])
        assert meta['attachments'] == '2' and 'attachment_count' not in meta


def test_action_contract_and_missing_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(cert, 'SOURCES', RELEASE_SOURCES)
    with pytest.raises(ValueError, match='unsupported_action'):
        cert.normalize('logon.csv', RELEASE_SOURCES['logon.csv']['header'], ['1', '01/02/2010 03:04:05', 'u1', 'pc1', 'Unlock'])
    manifest, folder, database = scan(tmp_path)
    with pytest.raises(ValueError, match='Missing release'):
        cert.ingest(manifest, folder, database, reserve=0, progress_log=None)
    assert not database.exists()


def test_existing_unknown_database_is_untouched(tmp_path):
    manifest, folder, database = scan(tmp_path)
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE activity (note TEXT)')
        db.execute("INSERT INTO activity VALUES ('preserve me')")
    before = cert.hash_file(database)
    with pytest.raises(ValueError, match='not a CERT'):
        cert.ingest(manifest, folder, database, reserve=0, progress_log=None)
    assert cert.hash_file(database) == before


def test_disk_failure_mid_chunk_leaves_consistent_resume(tmp_path, monkeypatch):
    manifest, folder, database = scan(tmp_path, [('r4.2/file.csv', csv_bytes([row(str(i)) for i in range(5)]), None)])
    original = cert.require_space
    calls = 0
    def failure(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError('disk full fixture')
        return original(*args, **kwargs)
    monkeypatch.setattr(cert, 'require_space', failure)
    with pytest.raises(OSError, match='disk full'):
        cert.ingest(manifest, folder, database, chunk=2, reserve=0, progress_log=None)
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT processed FROM progress').fetchone()[0] == 2
        assert db.execute('SELECT count(*) FROM events').fetchone()[0] == 2
    monkeypatch.setattr(cert, 'require_space', original)
    assert cert.ingest(manifest, folder, database, reserve=0, progress_log=None)['events'] == 5


def test_cli_rejects_changed_source_and_live_destination(tmp_path, monkeypatch):
    manifest, folder, database = scan(tmp_path)
    # Place a fake script in tmp/research so CLI output confinement is tested.
    monkeypatch.setattr(cert, '__file__', str(tmp_path / 'research/cert_ingest.py'))
    config = tmp_path / 'paths.json'
    config.write_text(json.dumps({'research_database': str(tmp_path / 'activity.db')}))
    with pytest.raises(ValueError, match='inside'):
        cert.main(['--config', str(config), 'ingest', '--manifest', str(manifest), '--report', str(folder / 'report.json')])
    import shutil
    cli_folder = tmp_path / 'research/local'
    shutil.copytree(folder, cli_folder)
    cli_manifest = cli_folder / manifest.relative_to(folder)
    config.write_text(json.dumps({'research_database': str(cli_folder / 'events.sqlite'),
                                 'r42_archive': str(tmp_path / 'r4.2.tar.bz2')}))
    (tmp_path / 'r4.2.tar.bz2').write_bytes(b'changed source fixture')
    with pytest.raises(ValueError, match='no longer matches'):
        cert.main(['--config', str(config), 'ingest', '--manifest', str(cli_manifest), '--report', str(cli_folder / 'report.json')])
    assert not (cli_folder / 'events.sqlite').exists()


def test_concurrent_writer_is_rejected_and_lock_released(tmp_path):
    manifest, folder, database = scan(tmp_path, [('r4.2/file.csv', csv_bytes([row(str(i)) for i in range(4)]), None)])
    attempts = []
    def other_writer(source, processed):
        with pytest.raises(RuntimeError, match='writer is active'):
            cert.ingest(manifest, folder, database, reserve=0, progress_log=None)
        attempts.append(processed)
    report = cert.ingest(manifest, folder, database, chunk=2, reserve=0, after_chunk=other_writer, progress_log=None)
    assert attempts == [2, 4]
    assert cert.ingest(manifest, folder, database, reserve=0, progress_log=None) == report


def test_release_documents_have_aggregate_metadata_budget(tmp_path):
    entries = [('r4.2/readme-1.txt', b'fixture documentation', None),
               ('r4.2/readme-2.txt', b'additional fixture documentation', None)]
    with pytest.raises(ValueError, match='metadata exceeds'):
        scan(tmp_path, entries, max_metadata=100)
    assert not list((tmp_path / 'local').glob('*/manifest.json'))
