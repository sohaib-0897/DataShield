"""Inert interface fixtures; synthetic fits are not independent evaluation."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import platform
import sys

import joblib
import numpy as np
import pytest
import sklearn
from pydantic import ValidationError

from ml import supplied_spans as spans
from research.tab_baseline import CONFIG, pipeline


@pytest.fixture
def artifact(tmp_path):
    model = pipeline().fit([c+' synthetic specimen '+str(i) for c in spans.CATEGORIES for i in range(3)],
                           [c for c in spans.CATEGORIES for i in range(3)])
    joblib.dump(model,tmp_path/'entity.joblib')
    preparation = {'sha256':'0'*64,'bytes':1}
    contract = {'config':CONFIG,'preparation':preparation,'task':spans.TASK,'live_activation':False}
    (tmp_path/'training_contract.json').write_text(json.dumps(contract))
    meta = {'version':spans.VERSION,'task':spans.TASK,'status':'OFFLINE_RESEARCH_ONLY','live_activation':False,
            'selected_mode':'entity','score_kind':spans.SCORE_KIND,'fit_partition':'train','selection_partition':'validation',
            'test_loaded':False,'config':CONFIG,'preparation':preparation,
            'software':{'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,'joblib':joblib.__version__},
            'contract':{'sha256':spans.file_hash(tmp_path/'training_contract.json')},
            'models':{'entity':{'artifact':{'sha256':spans.file_hash(tmp_path/'entity.joblib')}}}}
    (tmp_path/'selection.json').write_text(json.dumps(meta))
    return tmp_path,spans.file_hash(tmp_path/'selection.json')


def test_unicode_supplied_offsets_category_scores_and_no_text(artifact):
    classifier = spans.SuppliedSpanClassifier(*artifact)
    request = spans.SuppliedSpanRequest(text='😀 PERSON synthetic specimen',spans=[{'start':2,'end':8}])
    result = classifier.classify(request)
    assert result['predictions'][0]['category'] in spans.CATEGORIES
    assert set(result['predictions'][0]['scores']) == set(spans.CATEGORIES)
    assert result['model_version'] == spans.VERSION and result['advisory'] is True
    assert 'uncalibrated' in result['score_kind'] and 'not probabilities' in result['score_kind']
    assert request.text not in json.dumps(result)
    assert not {'sensitivity','risk','label','confidence','decision'} & result.keys()


@pytest.mark.parametrize('payload',[
    {'text':'hello'}, {'text':'hello','spans':[]}, {'text':12,'spans':[{'start':0,'end':1}]},
    {'text':'hello','spans':[{'start':True,'end':2}]}, {'text':'hello','spans':[{'start':'0','end':2}]},
    {'text':'hello','spans':[{'start':-1,'end':2}]}, {'text':'hello','spans':[{'start':1,'end':1}]},
    {'text':'hello','spans':[{'start':0,'end':6}]}, {'text':'hello','spans':[{'start':3,'end':2}]},
    {'text':'   ','spans':[{'start':0,'end':1}]}, {'text':'x'*32769,'spans':[{'start':0,'end':1}]},
    {'text':'x'*4097,'spans':[{'start':0,'end':4097}]}, {'text':'x','spans':[{'start':0,'end':1}]*101},
    {'text':'\ud800','spans':[{'start':0,'end':1}]}, {'text':'x','spans':[{'start':0,'end':1}],'category':'NORMAL'},
])
def test_bad_requests_are_rejected(payload):
    with pytest.raises(ValidationError): spans.SuppliedSpanRequest.model_validate(payload)


@pytest.mark.parametrize('field,value',[('task','document sensitivity'),('selected_mode','context'),('live_activation',True),
                                      ('software',{}),('version','unknown'),('test_loaded',True)])
def test_incompatible_metadata_rejected_before_deserialization(artifact,monkeypatch,field,value):
    root,_ = artifact
    meta = json.loads((root/'selection.json').read_text());meta[field] = value
    (root/'selection.json').write_text(json.dumps(meta))
    monkeypatch.setattr(joblib,'load',lambda p:pytest.fail('Must reject before joblib load'))
    with pytest.raises(ValueError):spans.SuppliedSpanClassifier(root,spans.file_hash(root/'selection.json'))


def test_unpinned_or_corrupt_artifact_rejected(artifact,monkeypatch):
    root,pin = artifact
    monkeypatch.setattr(joblib,'load',lambda p:pytest.fail('Must reject before joblib load'))
    with pytest.raises(ValueError,match='pin'):spans.SuppliedSpanClassifier(root,'0'*64)
    (root/'entity.joblib').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='digest'):spans.SuppliedSpanClassifier(root,pin)


def test_unsupported_categories_rejected(artifact):
    root,pin = artifact
    model = joblib.load(root/'entity.joblib');model['classifier'].classes_[0] = 'NORMAL'
    joblib.dump(model,root/'entity.joblib')
    meta = json.loads((root/'selection.json').read_text())
    meta['models']['entity']['artifact']['sha256'] = spans.file_hash(root/'entity.joblib')
    (root/'selection.json').write_text(json.dumps(meta))
    with pytest.raises(ValueError,match='categories'):spans.SuppliedSpanClassifier(root,spans.file_hash(root/'selection.json'))


@pytest.mark.parametrize('failure',[False,True])
def test_single_load_under_concurrency_and_cached_failure(monkeypatch,failure):
    calls = []
    sentinel = object()
    def load(*args):
        calls.append(args)
        if failure:raise FileNotFoundError('private path')
        return sentinel
    monkeypatch.setenv('DATASHIELD_SPAN_ARTIFACT','synthetic')
    monkeypatch.setenv('DATASHIELD_SPAN_SELECTION_SHA256','0'*64)
    monkeypatch.setattr(spans,'SuppliedSpanClassifier',load)
    service = spans.AdvisoryService()
    def get(_):
        try:return service.get()
        except spans.ArtifactUnavailable as exc:
            assert 'private path' not in str(exc)
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(get,range(16)))
    assert len(calls) == 1 and all(r is (None if failure else sentinel) for r in results)


def test_api_auth_flag_failure_validation_and_no_text_logging(monkeypatch,caplog,artifact):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
    from app.main import app, analyst, actor
    from app import span_advisory
    from fastapi.testclient import TestClient
    from types import SimpleNamespace
    request = {'text':'PRIVATE_SYNTHETIC_SENTINEL PERSON','spans':[{'start':27,'end':33}]}
    monkeypatch.delenv('DATASHIELD_SPAN_ADVISORY_ENABLED',raising=False)
    app.dependency_overrides[actor] = lambda:SimpleNamespace(role='VIEWER')
    try:
        with TestClient(app) as client:
            assert client.post('/api/v1/advisory/supplied-spans',json=request).status_code == 403
            app.dependency_overrides[analyst] = lambda:None
            monkeypatch.setattr(span_advisory,'service',spans.AdvisoryService())
            monkeypatch.setattr(spans,'SuppliedSpanClassifier',lambda *a:pytest.fail('Disabled must never load'))
            assert client.post('/api/v1/advisory/supplied-spans',json=request).status_code == 404
            monkeypatch.setenv('DATASHIELD_SPAN_ADVISORY_ENABLED','true')
            monkeypatch.delenv('DATASHIELD_SPAN_ARTIFACT',raising=False)
            assert client.post('/api/v1/advisory/supplied-spans',json=request).status_code == 503
            response = client.post('/api/v1/advisory/supplied-spans',json={**request,'spans':[{'start':0,'end':1000}]})
            assert response.status_code == 422 and request['text'] not in response.text
            assert request['text'] not in caplog.text
    finally:
        app.dependency_overrides.clear()


def test_api_success_has_no_persistence_and_enforcement_is_unchanged(monkeypatch,artifact):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
    from app.main import app, analyst
    from app import span_advisory
    import app.main as main_module
    from app.sensitivity import classify_document
    from app.analysis import assess
    from app.schemas import PolicyConfig
    from types import SimpleNamespace
    from fastapi.testclient import TestClient
    classifier = spans.SuppliedSpanClassifier(*artifact)
    monkeypatch.setattr(span_advisory.service,'get',lambda:classifier)
    monkeypatch.setattr(main_module,'SessionLocal',lambda:pytest.fail('Advice must not persist data'))
    monkeypatch.delenv('DATASHIELD_SENSITIVITY_ARTIFACT',raising=False)
    event = SimpleNamespace(event_type='UPLOAD_ATTEMPT',channel='UPLOAD',metadata={'sample_text':'Synthetic 12345-1234567-1'})
    behavioral = {'score':70,'source':'HEURISTIC','reason':'synthetic'}
    policy = PolicyConfig(); policy_before = policy.model_dump()
    monkeypatch.setenv('DATASHIELD_SPAN_ADVISORY_ENABLED','false')
    before = classify_document(event)
    risk_before = assess(event,before,behavioral,20,policy)
    monkeypatch.setenv('DATASHIELD_SPAN_ADVISORY_ENABLED','true')
    app.dependency_overrides[analyst] = lambda:None
    try:
        with TestClient(app) as client:
            response = client.post('/api/v1/advisory/supplied-spans',json={'text':'PERSON synthetic specimen','spans':[{'start':0,'end':6}]})
        assert response.status_code == 200
        assert not {'risk','sensitivity','decision'} & response.json().keys()
        assert classify_document(event) == before
        assert assess(event,classify_document(event),behavioral,20,policy) == risk_before
        assert policy.model_dump() == policy_before
    finally:
        app.dependency_overrides.clear()
