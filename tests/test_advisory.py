from copy import deepcopy
from pathlib import Path
import json
import sqlite3

import joblib
import numpy as np
import pytest
import sklearn

from ml.advisory import (AdvisoryStore, FlaskAdvisoryAdapter, ShadowEngine,
                         UpstreamAdvisoryAdapter, digest)
from ml.features.windows import FEATURE_NAMES, VERSION
from research.behavioral_ml import fit_models


@pytest.fixture
def setup(tmp_path):
    windows = []
    for hour in range(6):
        values = dict.fromkeys(FEATURE_NAMES, 1)
        values['total_count'] = hour + 1
        windows.append({'feature_version': VERSION, 'fully_observed': True, 'features': values,
                        'start': f'2010-01-02T{hour:02}:00:00', 'end': f'2010-01-02T{hour+1:02}:00:00', 'label': 0})
    model = fit_models(windows[:4], windows[4:5], trees=10)[0]['isolation_forest']
    folder = tmp_path/'model'
    folder.mkdir()
    joblib.dump(model['pipeline'], folder/'isolation_forest.joblib')
    report = {'version': 'cert-behavior-research-v1', 'status': 'RESEARCH_ONLY_NOT_REGISTRABLE',
              'feature_version': VERSION, 'feature_names': FEATURE_NAMES, 'preprocessing_fit_partition': 'train',
              'software': {'sklearn': sklearn.__version__, 'numpy': np.__version__},
              **dict.fromkeys(('dataset_sha256', 'store_sha256', 'answers_sha256', 'feature_artifact_sha256'), 'a'*64),
              'models': {'isolation_forest': {'threshold': model['threshold'], 'threshold_partition': 'validation',
                         'score_kind': model['score_kind'], 'artifact_sha256': digest(folder/'isolation_forest.joblib')}}}
    (folder/'report.json').write_text(json.dumps(report))
    engine = ShadowEngine(enabled=True, artifact=folder, report_sha256=digest(folder/'report.json'))
    return engine, windows[-1], report


def observe(engine, w=None):
    return engine.observe({'score': 80, 'severity': 'HIGH', 'private': 'secret'}, w, observed_at='2010-01-02T06:00:00')


def test_cache_and_replay(setup):
    engine, w, _ = setup
    first = observe(engine, w)
    assert first == observe(engine, w)
    assert engine.loads == 1
    assert first['anomaly']['status'] == 'AVAILABLE'
    assert first['automated_blocking'] is False
    assert first['combined']['score'] is None
    assert 'private' not in first['rule']


@pytest.mark.parametrize('adapter', [FlaskAdvisoryAdapter, UpstreamAdvisoryAdapter])
def test_compatible_payload_and_persistence(setup, tmp_path, adapter):
    engine, w, _ = setup
    original = {'score': 80, 'decision': 'BLOCK', 'nested': {'rules': [1, 2]}}
    before = deepcopy(original)
    store = AdvisoryStore(tmp_path/'advisory.sqlite')
    a = adapter(engine, store)
    result = a.attach(original, original, w, observed_at=w['end'], replay_key='window-1')
    assert original == before
    assert {k: v for k, v in result.items() if k != 'research_advisory'} == before
    assert result == a.attach(original, original, w, observed_at=w['end'], replay_key='window-1')
    assert len(store.recent()) == 1
    w['features']['total_count'] = 900
    conflict = a.attach(original, original, w, observed_at=w['end'], replay_key='window-1')
    assert conflict['research_advisory']['persistence_status'] == 'UNAVAILABLE'
    assert len(store.recent()) == 1


def test_flags_missing_and_schema(setup):
    engine, w, _ = setup
    assert observe(ShadowEngine(), w)['anomaly']['status'] == 'DISABLED'
    assert observe(ShadowEngine(enabled=True), w)['anomaly']['status'] == 'ARTIFACT_UNAVAILABLE'
    assert observe(engine)['anomaly']['status'] == 'FEATURES_UNAVAILABLE'
    w['feature_version'] = 'event-window-v2'
    assert observe(engine, w)['anomaly']['status'] == 'FEATURE_SCHEMA_MISMATCH'
    with pytest.raises(ValueError):
        ShadowEngine(mode='enforce')


@pytest.mark.parametrize('mutation', ['missing_channel', 'incomplete', 'future', 'nan', 'missing_key'])
def test_feature_availability_and_completion(setup, mutation):
    engine, w, _ = setup
    if mutation == 'missing_channel':
        w['features']['http_available'] = 0
    elif mutation == 'incomplete':
        w['fully_observed'] = False
    elif mutation == 'future':
        w['end'] = '2010-01-02T07:00:00'
    elif mutation == 'nan':
        w['features']['total_count'] = float('nan')
    else:
        del w['features']['total_count']
    assert observe(engine, w)['fallback'] is True


@pytest.mark.parametrize('mutation', ['feature', 'hash', 'threshold', 'provenance', 'software', 'version'])
def test_invalid_artifacts_fail_before_unpickle(setup, mutation, monkeypatch):
    engine, w, report = setup
    if mutation == 'feature': report['feature_version'] = 'other'
    elif mutation == 'hash': report['models']['isolation_forest']['artifact_sha256'] = 'b'*64
    elif mutation == 'threshold': report['models']['isolation_forest']['threshold_partition'] = 'test'
    elif mutation == 'provenance': del report['answers_sha256']
    elif mutation == 'software': report['software']['sklearn'] = 'wrong'
    else: report['version'] = 'v99'
    p = engine.artifact/'report.json'
    p.write_text(json.dumps(report))
    engine.report_sha256 = digest(p)
    def forbidden(*a, **kw): raise AssertionError('Must not unpickle')
    monkeypatch.setattr(joblib, 'load', forbidden)
    assert observe(engine, w)['anomaly']['status'] == 'MODEL_OR_INPUT_INVALID'


def test_untrusted_pin_and_cache_invalidation(setup):
    engine, w, _ = setup
    assert observe(engine, w)['anomaly']['status'] == 'AVAILABLE'
    (engine.artifact/'isolation_forest.joblib').write_bytes(b'bad-model')
    assert observe(engine, w)['fallback']
    assert engine.loads == 1
    engine.report_sha256 = 'c'*64
    assert observe(engine, w)['fallback']


def test_model_exception_and_redaction(setup, monkeypatch):
    engine, w, _ = setup
    observe(engine, w)
    def failing(*args): raise RuntimeError('private text')
    monkeypatch.setattr(engine._cached[0], 'score_samples', failing)
    content = {'version': 'document-extraction-evidence-v1', 'extraction_status': 'OK', 'content_available': True, 'text': 'secret',
               'pii_evidence': [{'type': 'email_address', 'count': 1, 'value': 'secret'}]}
    result = engine.observe({}, w, content=content, observed_at=w['end'])
    assert result['fallback']
    assert 'secret' not in json.dumps(result) and 'private text' not in json.dumps(result)
    assert result['content']['evidence'] == [{'type': 'email_address', 'count': 1}]


def test_refuse_live_database(tmp_path):
    path = tmp_path/'live.sqlite'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE activity (id INTEGER)')
    before = path.read_bytes()
    with pytest.raises(ValueError): AdvisoryStore(path)
    assert path.read_bytes() == before


def test_flask_status_requires_authorization():
    from flask import Flask
    app = Flask('synthetic')
    FlaskAdvisoryAdapter().install(app, lambda: ('denied', 403))
    assert app.test_client().get('/research/advisory').status_code == 403
    assert app.test_client().get('/research/advisory/ui').status_code == 403
    other = Flask('allowed')
    FlaskAdvisoryAdapter().install(other, lambda: None)
    result = other.test_client().get('/research/advisory').json
    assert b'Shadow evidence' in other.test_client().get('/research/advisory/ui').data
    assert result['enabled'] is False and result['automated_blocking'] is False


def test_fastapi_status_requires_authorization():
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    app = FastAPI()
    def denied(): raise HTTPException(403)
    UpstreamAdvisoryAdapter().install(app, denied)
    assert TestClient(app).get('/api/v1/research/advisory').status_code == 403
    assert TestClient(app).get('/api/v1/research/advisory/ui').status_code == 403
    other = FastAPI()
    UpstreamAdvisoryAdapter().install(other, lambda: None)
    assert TestClient(other).get('/api/v1/research/advisory').json()['mode'] == 'shadow'
    assert 'Shadow evidence' in TestClient(other).get('/api/v1/research/advisory/ui').text


def test_sidecar_failure_keeps_rules(setup):
    engine, w, _ = setup
    class Broken:
        def append(self, *args): raise OSError('permission')
        def recent(self): raise OSError('permission')
    adapter = FlaskAdvisoryAdapter(engine, Broken())
    result = adapter.attach({'score': 90}, {'score': 90}, w, observed_at=w['end'], replay_key='1')
    assert result['score'] == 90
    assert result['research_advisory']['persistence_status'] == 'UNAVAILABLE'
    assert adapter.status()['persistence_status'] == 'UNAVAILABLE'


def test_unsupported_content_keeps_independent_signals(setup):
    engine, w, _ = setup
    content = {'version': 'document-extraction-evidence-v1', 'extraction_status': 'UNSUPPORTED',
               'content_available': False, 'filename_label': 'restricted', 'hash_label': 'confidential'}
    result = engine.observe({'score': 90}, w, content=content, observed_at=w['end'])
    assert result['content']['filename_label'] == 'restricted'
    assert result['content']['hash_label'] == 'confidential'
    assert result['rule']['score'] == 90
    assert result['combined']['score'] is None
