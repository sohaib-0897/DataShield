"""Bounded resumable acquisition of pinned TAB files. No partial corpus is parsed."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from research.cert_ingest import atomic_json, hash_file, local_path, require_space
from research.tab_inventory import FILES, FILE_LIMIT, REPOSITORY, REVISION

TREE_SHA256 = '763e40625473fe9555d390e26efb959ba955ff0cb135dbeb0a14bb39085a1f87'


def verify_blob(path, entry):
    if path.stat().st_size != entry['size']:
        raise ValueError('Incomplete pinned file')
    digest = hashlib.sha1(b'blob ' + str(entry['size']).encode() + b'\0')
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            digest.update(block)
    if digest.hexdigest() != entry['sha']:
        raise ValueError('Pinned Git blob mismatch')
    return hash_file(path)


def acquire(directory, tree_path, *, attempts=2, timeout=120, runner=subprocess.run):
    if not 1 <= attempts <= 3 or not 1 <= timeout <= 300:
        raise ValueError('Acquisition bounds exceeded')
    folder = Path('research/local').absolute()
    directory = local_path(folder, directory)
    tree_path = local_path(folder, tree_path)
    if hash_file(tree_path)['sha256'] != TREE_SHA256:
        raise ValueError('DS1 pinned tree checksum mismatch')
    tree = json.loads(tree_path.read_text())
    if tree['sha'] != REVISION or tree.get('truncated') is not False:
        raise ValueError('Untrusted tree')
    entries = {e['path']: e for e in tree['tree'] if e['path'] in FILES}
    if set(entries) != set(FILES) or any(e['type'] != 'blob' or e['size'] > FILE_LIMIT for e in entries.values()):
        raise ValueError('Incomplete pinned tree')
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    require_space(folder, 256 * 1024**2)
    journal, verified = [], []
    for name in FILES:
        entry = entries[name]
        path, partial = directory / name, directory / (name + '.partial')
        url = f'https://raw.githubusercontent.com/NorskRegnesentral/text-anonymization-benchmark/{REVISION}/{name}'
        if not path.exists():
            for attempt in range(attempts):
                # Resume only this pinned URL's private partial. curl rejects a
                # server ignoring Range; preserve that file and restart elsewhere.
                cmd = ['curl', '--http1.1', '--silent', '--show-error', '--fail', '--location',
                       '--proto', '=https', '--proto-redir', '=https', '--connect-timeout', '10',
                       '--max-time', str(timeout), '--max-filesize', str(entry['size']),
                       '--output', str(partial)]
                if partial.exists() and partial.stat().st_size:
                    cmd += ['--continue-at', '-']
                started = time.perf_counter()
                try:
                    result = runner(cmd + [url], capture_output=True, text=True, timeout=timeout + 15)
                except subprocess.TimeoutExpired:
                    result = argparse.Namespace(returncode=124)
                if partial.exists(): partial.chmod(0o600)
                journal.append({'file': name, 'attempt': attempt + 1, 'seconds': time.perf_counter() - started,
                                'curl_exit': result.returncode, 'bytes': partial.stat().st_size if partial.exists() else 0,
                                'resumed': '--continue-at' in cmd})
                atomic_json(directory / 'attempts.json', journal)
                if result.returncode == 0:
                    try:
                        verify_blob(partial, entry)
                    except ValueError:
                        partial.rename(directory / f'{name}.invalid-{time.time_ns()}.partial')
                        continue
                    partial.rename(path)
                    path.chmod(0o600)
                    break
                if result.returncode in (33, 36) and partial.exists():
                    partial.rename(directory / f'{name}.range-unsupported-{time.time_ns()}.partial')
            if not path.exists():
                return {'status': 'ACQUISITION_BLOCKED', 'failed_file': name, 'attempts': journal,
                        'trusted_manifest': False, 'partial_data_parsed': False}
        hashes = verify_blob(path, entry)
        if name == 'LICENSE.txt' and b'The MIT License' not in path.read_bytes():
            raise ValueError('License mismatch')
        verified.append({'file': name, 'url': url, **hashes, 'git_blob_sha1': entry['sha']})
    manifest = {'repository': REPOSITORY, 'revision': REVISION, 'license': 'MIT', 'files': verified,
                'acquisition_method': 'bounded HTTPS curl; resumable where supported; DS1 pinned Git blobs',
                'tree': hash_file(tree_path)}
    atomic_json(directory / 'acquisition.json', manifest)
    return {'status': 'ACQUIRED_PINNED_FILES', 'acquisition': manifest, 'attempts': journal,
            'trusted_manifest': True, 'partial_data_parsed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--tree', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--attempts', type=int, default=2)
    parser.add_argument('--timeout', type=int, default=120)
    args = parser.parse_args()
    report = local_path(Path('research/local').absolute(), args.report)
    if report.exists():
        raise ValueError('New report required')
    result = acquire(args.directory, args.tree, attempts=args.attempts, timeout=args.timeout)
    atomic_json(report, result)
    print(json.dumps({'status': result['status'], 'report': str(report)}))
    return 0 if result['trusted_manifest'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
