"""Isolated API checks using synthetic events; no agents or real files."""
import os
import subprocess
import sys
from pathlib import Path

os.environ['DATASHIELD_API_KEY'] = 'test-only-key'
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(__file__).resolve().parent / '.test_api.sqlite3')

import pytest
from legacy.flask import admin_server as server
from legacy.flask.database import Base, engine
from legacy.flask import models  # noqa: F401


@pytest.fixture
def client():
    server.app.config['TESTING'] = True
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with server.app.test_client() as client:
        yield client


HEADERS = {'X-API-KEY': 'test-only-key'}


def test_alerts_require_configured_key(client):
    assert client.get('/alerts').status_code == 401
    assert client.get('/alerts', headers={'X-API-KEY': 'wrong'}).status_code == 401
    assert client.get('/alerts', headers=HEADERS).get_json() == []


@pytest.mark.parametrize('decision', ['allow', 'block'])
def test_upload_review_round_trip(client, decision):
    payload = {
        'client': 'demo-workstation', 'filename': 'synthetic.txt',
        'upload_id': 'synthetic-upload', 'upload_url': 'https://example.com/upload',
        'sensitive': True, 'sensitive_matches': ['00000-0000000-0'],
    }
    assert client.post('/upload_alert', json=payload).status_code == 401
    assert client.post('/upload_alert', headers=HEADERS, json=payload).status_code == 200
    alerts = client.get('/alerts', headers=HEADERS).get_json()
    assert len(alerts) == 1
    assert alerts[0]['type'] == 'upload'
    assert client.get('/check_decision/synthetic-upload', headers=HEADERS).get_json()['status'] == 'pending'
    result = client.post('/upload_decision', json={'alert_id': alerts[0]['id'], 'decision': decision})
    assert result.status_code == 200
    assert client.get('/check_decision/synthetic-upload', headers=HEADERS).get_json() == {
        'status': 'decided', 'decision': decision,
    }
    assert client.get('/alerts', headers=HEADERS).get_json() == []
    page = client.get('/allowed_uploads').get_data(as_text=True)
    assert ('synthetic.txt' in page) == (decision == 'allow')


def test_invalid_decision_does_not_create_state(client):
    assert client.post('/upload_decision', json={'alert_id': 1, 'decision': 'invalid'}).status_code == 400
    assert client.post('/upload_decision', json={'alert_id': 99, 'decision': 'block'}).status_code == 404
    assert client.get('/pending_decisions', headers=HEADERS).get_json() == {}


def test_file_event_preview_escapes_markup(client):
    payload = {
        'activity': 'created', 'client': 'demo-workstation',
        'filename': 'synthetic.txt', 'file_path': 'synthetic.txt',
        'preview': '<script>alert(1)</script> 00000-0000000-0',
        'sensitive': True, 'sensitive_matches': ['00000-0000000-0'],
    }
    assert client.post('/file_activity_alert', headers=HEADERS, json=payload).status_code == 200
    alerts = client.get('/alerts', headers=HEADERS).get_json()
    assert len(alerts) == 1
    assert alerts[0]['type'] == 'file_activity'
    response = client.get('/view_file_activity/1')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert '<script>alert(1)</script>' not in page
    assert '&lt;script&gt;' in page
    assert '00000-0000000-0' in page


def test_alerts_and_decisions_survive_backend_restart(client):
    upload = {'client': 'restart-demo', 'filename': 'persist.txt',
              'upload_id': 'restart-upload', 'upload_url': 'https://example.com/upload'}
    activity = {'client': 'restart-demo', 'filename': 'activity.txt',
                'activity': 'created', 'file_path': 'activity.txt'}
    assert client.post('/upload_alert', headers=HEADERS, json=upload).status_code == 200
    assert client.post('/file_activity_alert', headers=HEADERS, json=activity).status_code == 200
    alerts = client.get('/alerts', headers=HEADERS).get_json()
    upload_id = next(item['id'] for item in alerts if item['type'] == 'upload')
    assert client.post('/upload_decision', json={'alert_id': upload_id, 'decision': 'allow'}).status_code == 200

    code = (
        "from legacy.flask import admin_server as s\n"
        "c = s.app.test_client()\n"
        "h = {'X-API-KEY': 'test-only-key'}\n"
        "a = c.get('/alerts', headers=h).get_json()\n"
        "assert len(a) == 1 and a[0]['type'] == 'file_activity'\n"
        "assert c.get('/check_decision/restart-upload', headers=h).get_json()['decision'] == 'allow'\n"
        "assert 'persist.txt' in c.get('/allowed_uploads').get_data(as_text=True)\n"
    )
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).resolve().parents[1] / 'backend')
    subprocess.run([sys.executable, '-c', code], env=env, check=True)
