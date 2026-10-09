"""Disposable DataShield demo; does not configure the live application.

Run from the repository root with the existing compatible research environment.
Local verification calls real handlers/authentication explicitly, not HTTP/ASGI.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'backend')]
PIN = 'f820f6eb6c0656b0aad22407cf75665d2deeaf20b95cbc679b075a81604b7477'
ARTIFACT = ROOT / 'research/local/document_sensitivity/ds2_models_v2'
EXAMPLE = {'text': 'Alice visited London on 12 March 2020.',
           'spans': [{'start': 0, 'end': 5}, {'start': 14, 'end': 20}, {'start': 24, 'end': 37}]}


def dump(value):
    print(json.dumps(value, indent=2))


def session_path(name):
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in name):
        raise ValueError('Session name must contain only letters, numbers, hyphens or underscores')
    path = ROOT / '.local/demo' / name
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Symlinked demo paths are forbidden')
    return path


def prepare(folder):
    if folder.exists():
        raise SystemExit('Demo session already exists; reuse it or select a new --session name')
    folder.mkdir(parents=True, exist_ok=False, mode=0o700)
    (folder / 'fixtures').mkdir()
    env = {
        'DATABASE_URL': 'sqlite:///' + str(folder / 'dashboard.sqlite'),
        'DATASHIELD_JWT_SECRET': secrets.token_urlsafe(36),
        'DATASHIELD_AGENT_KEY': secrets.token_urlsafe(36),
        'DATASHIELD_DEMO_ADMIN_PASSWORD': secrets.token_urlsafe(18),
        'DATASHIELD_FRONTEND_ORIGIN': 'http://localhost:3101',
        'DATASHIELD_URL': 'http://127.0.0.1:8100',
        'DATASHIELD_ANOMALY_ARTIFACT': '',
        'DATASHIELD_SENSITIVITY_ARTIFACT': '',
        'DATASHIELD_MODEL_ROOT': str(folder / 'unconfigured-model-registry'),
        'DATASHIELD_SPAN_ADVISORY_ENABLED': 'true',
        'DATASHIELD_SPAN_ARTIFACT': str(ARTIFACT),
        'DATASHIELD_SPAN_SELECTION_SHA256': PIN,
        'DATASHIELD_MONITOR_FOLDERS': str(folder / 'fixtures'),
        'DATASHIELD_MACHINE_ID': 'DISPOSABLE-DEMO-ENDPOINT',
        'DATASHIELD_SCAN_BYTES': '8192',
        'DATASHIELD_EXTENSIONS': '.txt',
        'USER': 'synthetic.demo.monitor', 'USERNAME': 'synthetic.demo.monitor',
        'REACT_APP_API_URL': 'http://127.0.0.1:8100',
        'PORT': '3101', 'HOST': '127.0.0.1', 'BROWSER': 'none',
    }
    for name, content in [('config.json', json.dumps(env)),
                          ('environment.sh', '\n'.join('export ' + k + '=' + shlex.quote(v) for k, v in env.items()) + '\n')]:
        path = folder / name
        path.touch(mode=0o600, exist_ok=False)
        path.write_text(content)
    (folder / 'spans.json').write_text(json.dumps(EXAMPLE) + '\n')
    configure(folder)
    from app.core import Base, engine
    import app.models  # register the unchanged tables in this new SQLite DB
    Base.metadata.create_all(engine)
    from scripts.demo.seed_demo import main
    main()
    print('Disposable session:', folder)
    print('Use showcase.py credentials for the generated local login.')
    print('This demo dashboard uses http://localhost:3101 (seed helper prints its old default).')


def configure(folder):
    env = json.loads((folder / 'config.json').read_text())
    if env['DATABASE_URL'] != 'sqlite:///' + str(folder / 'dashboard.sqlite'):
        raise ValueError('Demo database must be inside the disposable session')
    # Explicit empty overrides prevent load_dotenv from adopting live artifacts.
    os.environ.update(env)
    return env


def trigger(folder):
    target = folder / 'fixtures' / ('synthetic-' + secrets.token_hex(4) + '.txt')
    staging = target.with_suffix('.pending')
    staging.write_text('Disposable fixture: synthetic CNIC 12345-1234567-1\n')
    staging.rename(target)
    print('Moved disposable fixture into .txt:', target.name)
    return target


def spans(http=False):
    from ml.supplied_spans import SuppliedSpanClassifier, SuppliedSpanRequest
    request = SuppliedSpanRequest.model_validate(EXAMPLE)
    if http:
        import requests
        base = os.environ['DATASHIELD_URL']
        response = requests.post(base + '/api/v1/auth/login', json={
            'username': 'demo.admin', 'password': os.environ['DATASHIELD_DEMO_ADMIN_PASSWORD']}, timeout=5)
        response.raise_for_status()
        response = requests.post(base + '/api/v1/advisory/supplied-spans', json=EXAMPLE,
                                 headers={'Authorization': 'Bearer ' + response.json()['access_token']}, timeout=10)
        response.raise_for_status()
        result = response.json()
    else:
        result = SuppliedSpanClassifier(ARTIFACT, PIN).classify(request)
    assert result['advisory'] is True and result['selection_sha256'] == PIN
    assert not {'sensitivity', 'risk', 'decision', 'confidence'} & result.keys()
    dump(result)
    return result


def verify(folder):
    """Actual pipeline + inotify; replace only HTTP delivery with explicit auth/handlers."""
    from fastapi import HTTPException
    from starlette.requests import Request
    from sqlalchemy import func, select
    from app import main as api, span_advisory
    from app.core import SessionLocal
    from app.models import Alert, DocumentMetadata, Event, ModelVersion, RiskAssessment
    from app.schemas import EventIn, LoginIn
    from ml.supplied_spans import SuppliedSpanRequest
    from agents import filesystem
    from watchdog.observers import Observer

    def denied(call, code):
        try:
            call()
        except HTTPException as exc:
            assert exc.status_code == code
        else:
            raise AssertionError('Expected access rejection')

    request = Request({'type': 'http', 'client': ('127.0.0.1', 1), 'headers': []})
    with SessionLocal() as db:
        assert api.ready(db) == {'status': 'ready'}
        denied(lambda: api.agent('invalid'), 401)
        denied(lambda: api.actor(None, db), 401)
        denied(lambda: api.login(LoginIn(username='demo.admin', password='invalid-password'), request, db), 401)
        login = api.login(LoginIn(username='demo.admin', password=os.environ['DATASHIELD_DEMO_ADMIN_PASSWORD']), request, db)
        user = api.actor('Bearer ' + login['access_token'], db)
        api.analyst(user)
        before = api.get_policies(user, db)
        initial_events = db.scalar(select(func.count(Event.id)))
        initial_alerts = db.scalar(select(func.count(Alert.id)))
        for row in api.alerts(sort_by='created_at', page=1, size=50, _=user, session=db)['items']:
            detail = api.alert_detail(row['id'], user, db)
            assert detail['anomalySource'] == 'HEURISTIC' and detail['classifierSource'] == 'RULE'
            assert '12345-1234567-1' not in str(detail['evidence'])
        with patch.dict(os.environ, {'DATASHIELD_SPAN_ADVISORY_ENABLED': 'false'}):
            denied(lambda: span_advisory.classify_spans(SuppliedSpanRequest.model_validate(EXAMPLE)), 404)
        inference = span_advisory.classify_spans(SuppliedSpanRequest.model_validate(EXAMPLE))
        assert db.scalar(select(func.count(Event.id))) == initial_events
        assert db.scalar(select(func.count(Alert.id))) == initial_alerts
        assert api.get_policies(user, db) == before
        assert db.scalar(select(func.count(ModelVersion.id))) == 0

    delivered, failures = [], []
    def deliver(payload):
        try:
            api.agent(os.environ['DATASHIELD_AGENT_KEY'])
            with SessionLocal() as db:
                result = api.ingest(EventIn.model_validate(payload), None, db)
                duplicate = api.ingest(EventIn.model_validate(payload), None, db)
                assert duplicate['duplicate'] is True and duplicate['event_id'] == result['event_id']
            delivered.append((payload, result))
            return result
        except Exception as exc:
            failures.append(type(exc).__name__)
            raise

    observer = Observer()
    observer.schedule(filesystem.Handler(), str(folder / 'fixtures'), recursive=False)
    with patch.object(filesystem, 'send', deliver):
        observer.start()
        try:
            target = trigger(folder)
            deadline = time.monotonic() + 10
            while not delivered and not failures and time.monotonic() < deadline:
                time.sleep(.05)
        finally:
            observer.stop()
            observer.join(timeout=5)
    assert not observer.is_alive() and not failures and delivered, (failures, delivered)
    with SessionLocal() as db:
        user = api.actor('Bearer ' + login['access_token'], db)
        assert api.get_policies(user, db) == before
        assert db.scalar(select(func.count(ModelVersion.id))) == 0
        for payload, result in delivered:
            assert payload['resource_id'] == str(target)
            document = db.scalar(select(DocumentMetadata).where(DocumentMetadata.event_id == result['event_id']))
            risk = db.scalar(select(RiskAssessment).where(RiskAssessment.event_id == result['event_id']))
            assert document.source == 'RULE' and document.label == 'restricted' and document.score == 90
            assert risk.explanation['classifier_source'] == 'RULE'
            assert risk.explanation['anomaly_source'] in {'HEURISTIC', 'INSUFFICIENT_HISTORY'}
            if result['alert_id']:
                detail = api.alert_detail(result['alert_id'], user, db)
                assert '12345-1234567-1' not in str(detail['evidence'])
        report = api.summary(30, user, db)
        status = api.system_status(user, db)
        assert status['behavior_source'] == 'HEURISTIC' and status['sensitivity']['source'] == 'RULE'
    result = {'verification_transport': 'explicit authenticated Python handlers; HTTP/browser NOT tested',
              'native_observer': type(observer).__name__, 'delivered_fixture_events': len(delivered),
              'native_fixture_alerts': sum(bool(r['alert_id']) for _, r in delivered),
              'native_fixture_rule_classification': 'restricted / score 90',
              'events': report['events'], 'events_before_native_fixture': initial_events,
              'credentials_rejected': True, 'rule_alerts_and_masked_evidence': True,
              'event_retry_idempotent': True, 'policies_unchanged': True, 'registered_models': 0,
              'span_categories': [p['category'] for p in inference['predictions']],
              'span_inference_creates_no_events_or_alerts': True}
    (folder / 'verification.json').write_text(json.dumps(result, indent=2))
    dump(result)


def results():
    def load(path):
        return json.loads((ROOT / 'docs/implementation' / path).read_text())
    print('Saved measured results; no fitting or rescoring. P/R/F1/AP are fractions.')
    for title, data, key in [('CERT original: 11,753 test windows / 8 positives', load('phase6/comparison.json'), 'methods'),
                             ('CERT known users: 10,553 test windows / 8 positives', load('nlp-followup/comparison.json'), 'models')]:
        print('\n' + title)
        for name, item in data[key].items():
            m = item['test']
            print(f"{name}: P={m['precision']:.6f} R={m['recall']:.6f} F1={m['f1']:.6f} AP={m['pr_auc_average_precision']:.6f}")
    print('\nTAB supplied spans: 6,713 test spans in 127 legal-domain documents')
    for name in ('entity', 'context', 'majority'):
        m = load('document-sensitivity/ds2-evaluation.json')['models'][name]
        print(f"{name}: macro F1={m['macro_f1']:.6f} micro F1={m['micro_f1']:.6f}")
    print('\nStrict unseen-user CERT held-outs empty; independent document sensitivity unavailable.')
    print('B2: 390 documents, zero structured candidates; independent detection P/R/F1 unavailable.')


def frontend(folder):
    """Build into the disposable session, then serve SPA routes on loopback."""
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import urlsplit
    build = folder / 'frontend-build'
    if not (build / 'index.html').exists():
        subprocess.run(['npm', 'run', 'build'], cwd=ROOT / 'frontend', check=True,
                       env={**os.environ, 'CI': 'true', 'BUILD_PATH': str(build)})
    class SPA(SimpleHTTPRequestHandler):
        def do_GET(self):
            if not Path(self.translate_path(self.path)).exists() and not Path(urlsplit(self.path).path).suffix:
                self.path = '/index.html'
            super().do_GET()
    print('Disposable dashboard: http://localhost:3101', flush=True)
    with ThreadingHTTPServer(('127.0.0.1', 3101), partial(SPA, directory=str(build))) as server:
        server.serve_forever()


def verify_http(folder):
    """Real HTTP, production filesystem Handler and native Observer, with no patches."""
    import requests
    from agents.filesystem import Handler
    from watchdog.observers import Observer
    base = os.environ['DATASHIELD_URL']
    with requests.Session() as client:
        client.trust_env = False
        def call(method, path, **kwargs):
            response = client.request(method, base + path, timeout=10, **kwargs)
            response.raise_for_status()
            return response.json()
        assert call('GET', '/ready') == {'status': 'ready'}
        assert client.get(base + '/api/v1/system/status', timeout=5).status_code == 401
        assert client.post(base + '/api/v1/events', json={}, timeout=5).status_code == 401
        response = client.post(base + '/api/v1/auth/login', json={
            'username': 'demo.admin', 'password': 'invalid-password'}, timeout=5)
        assert response.status_code == 401
        login = call('POST', '/api/v1/auth/login', json={
            'username': 'demo.admin', 'password': os.environ['DATASHIELD_DEMO_ADMIN_PASSWORD']})
        client.headers['Authorization'] = 'Bearer ' + login['access_token']
        assert call('GET', '/api/v1/auth/me')['role'] == 'ADMIN'
        policy = call('GET', '/api/v1/policies')
        before = call('GET', '/api/v1/reports/summary')
        inference = call('POST', '/api/v1/advisory/supplied-spans', json=EXAMPLE)
        assert [p['category'] for p in inference['predictions']] == ['PERSON', 'LOC', 'DATETIME']
        assert call('GET', '/api/v1/reports/summary') == before
        invalid = client.post(base + '/api/v1/advisory/supplied-spans', json={
            **EXAMPLE, 'spans': [{'start': 0, 'end': 1000}]}, timeout=5)
        assert invalid.status_code == 422 and EXAMPLE['text'] not in invalid.text
        alerts = call('GET', '/api/v1/alerts')['items']
        assert alerts
        detail = call('GET', '/api/v1/alerts/' + alerts[0]['id'])
        assert detail['classifierSource'] == 'RULE' and detail['anomalySource'] == 'HEURISTIC'
        assert '12345-1234567-1' not in str(detail['evidence'])
        observer = Observer()
        observer.schedule(Handler(), str(folder / 'fixtures'), recursive=False)
        observer.start()
        observed = None
        try:
            target = trigger(folder)
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                rows = call('GET', '/api/v1/events', params={'size': 100})['items']
                observed = next((row for row in rows if row['resource_id'] == str(target)), None)
                if observed:
                    break
                time.sleep(.1)
        finally:
            observer.stop()
            observer.join(timeout=5)
        assert observed and not observer.is_alive()
        assert observed['channel'] == 'FILE' and observed['event_type'] == 'FILE_MOVE'
        assert '12345-1234567-1' not in str(observed['metadata'])
        assert call('GET', '/api/v1/policies') == policy
        assert call('GET', '/api/v1/models') == []
        status = call('GET', '/api/v1/system/status')
        assert status['behavior_source'] == 'HEURISTIC' and status['sensitivity']['source'] == 'RULE'
        result = {'transport': 'real loopback HTTP; native inotify; unchanged agents.filesystem.Handler/send',
                  'ready_login_authentication': True, 'span_categories': ['PERSON', 'LOC', 'DATETIME'],
                  'invalid_offsets_http_status': 422, 'span_inference_creates_no_events_or_alerts': True,
                  'native_event': observed['event_type'], 'rule_evidence_masked': True,
                  'policies_unchanged': True, 'registered_models': 0,
                  'events_before_monitor': before['events'],
                  'events_after_monitor': call('GET', '/api/v1/events')['total']}
        (folder / 'http-verification.json').write_text(json.dumps(result, indent=2))
        dump(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', default='showcase')
    parser.add_argument('command', choices=['prepare', 'backend', 'frontend', 'monitor', 'trigger', 'spans', 'verify', 'verify-http', 'credentials', 'results'])
    parser.add_argument('--http', action='store_true', help='Use the real supplied-span HTTP endpoint (spans only)')
    args = parser.parse_args()
    if args.http and args.command != 'spans':
        parser.error('--http is supported only for spans')
    os.chdir(ROOT)
    if args.command == 'results':
        results()
        return
    folder = session_path(args.session)
    if args.command == 'prepare':
        prepare(folder)
        return
    configure(folder)
    if args.command == 'credentials':
        print('demo.admin\n' + os.environ['DATASHIELD_DEMO_ADMIN_PASSWORD'])
    elif args.command == 'backend':
        import uvicorn
        uvicorn.run('app.main:app', host='127.0.0.1', port=8100)
    elif args.command == 'frontend':
        frontend(folder)
    elif args.command == 'monitor':
        from agents.filesystem import main as monitor
        monitor()
    elif args.command == 'trigger':
        trigger(folder)
    elif args.command == 'spans':
        spans(args.http)
    elif args.command == 'verify':
        verify(folder)
    elif args.command == 'verify-http':
        verify_http(folder)


if __name__ == '__main__':
    main()
