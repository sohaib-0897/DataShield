"""Isolated API checks using synthetic events; no agents or real files."""
import os

os.environ['DATASHIELD_API_KEY'] = 'test-only-key'

import pytest
import admin_server as server


@pytest.fixture
def client():
    server.app.config['TESTING'] = True
    server.upload_alerts.clear()
    server.file_activity_alerts.clear()
    server.http_upload_decisions.clear()
    server.allowed_uploads.clear()
    server.upload_alert_id_counter = 1
    server.file_activity_alert_id_counter = 1
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
    assert len(server.allowed_uploads) == (1 if decision == 'allow' else 0)


def test_invalid_decision_does_not_create_state(client):
    assert client.post('/upload_decision', json={'alert_id': 1, 'decision': 'invalid'}).status_code == 400
    assert client.post('/upload_decision', json={'alert_id': 99, 'decision': 'block'}).status_code == 404
    assert server.http_upload_decisions == {}


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
