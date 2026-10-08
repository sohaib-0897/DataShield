import hashlib
import json
import sqlite3

import joblib
import numpy as np
import pytest

from research.cert_ingest import atomic_json, encoded, hash_file
from research.nlp_baselines import LinearBaseline
from research.nlp_cohort import cohort, rows
from research.nlp_evaluate import evaluate
from research.sensitivity_training import read_corpus, evaluate as sensitivity_evaluate
from research.stream_prepare import SCHEMA
from research.text_study import attach_text
from tests.test_text_research import sample_study


def prepared_fixture(tmp_path):
    feature,events,_=sample_study();path=tmp_path/'prepared.sqlite'
    values=attach_text(feature['windows'],events)
    # Recurring user IDs. The strict protocol rejects all later windows;
    # known-user objective preserves chronological content-disjoint rows.
    with sqlite3.connect(path) as db:
        db.executescript(SCHEMA);db.execute('INSERT INTO meta VALUES (?,?)',('report',encoded({'complete':True})))
        for w in values:
            w['user']=w['user'].split('-')[1]
            text=w.pop('text');bags=w.pop('text_hashes')
            db.execute('INSERT INTO windows VALUES (?,?,?,?)',(w['start'],w['user'],encoded(w),text))
            db.executemany('INSERT OR IGNORE INTO bags VALUES (?)',((h,) for h in bags))
            db.executemany('INSERT INTO window_bags VALUES (?,?,?)',((w['start'],w['user'],h) for h in bags))
    return path


def test_independent_stage_flags_and_duplicate_drop(tmp_path):
    path=prepared_fixture(tmp_path);db,audit=cohort(path,tmp_path)
    assert audit['original_strict']['validation']['windows']==0
    assert audit['original_strict']['test']['windows']==0
    assert audit['known_users_alternative']['validation']['windows']==4
    assert len(rows(db,2))==8
    db.close()
    with sqlite3.connect(path) as db:
        h=db.execute('SELECT hash FROM window_bags ORDER BY start,user LIMIT 1').fetchone()[0]
        start,user=db.execute('SELECT start,user FROM windows ORDER BY start DESC,user LIMIT 1').fetchone()
        db.execute('INSERT INTO window_bags VALUES (?,?,?)',(start,user,h))
    db,audit=cohort(path,tmp_path)
    assert audit['known_users_alternative']['test']['windows']==7
    assert audit['stages']['test']['independent_rejection_flags']['past_duplicate_bag']==1
    db.close()


def test_baseline_train_vocabulary_threshold_reload_common_population(tmp_path):
    path=prepared_fixture(tmp_path);report=evaluate(path,tmp_path/'run',tmp_path)
    assert report['comparison_status']=='COMPLETED'
    assert report['group_overlap']['train_test']['users']==4
    for mode in ('numeric','text','combined'):
        item=report['models'][mode]
        assert item['test']['windows']==8 and item['replay_scores_threshold_equal'] and item['replay_artifact_hash_equal']
        model=joblib.load(tmp_path/'run'/f'{mode}.joblib')
        if mode!='numeric':assert not {'delta','echo','foxtrot'} & model.tfidf.vocabulary_.keys()
    assert (tmp_path/'run'/'frozen_thresholds.json').exists()
    with pytest.raises(ValueError,match='Preserve'):evaluate(path,tmp_path/'run',tmp_path)


def sensitivity_fixture(tmp_path):
    records=[]
    for split,terms in [('train',['alpha','bravo']),('validation',['charlie']),('test',['delta'])]:
        for term in terms:
            for label,text in [('not_sensitive','public published weather'),('sensitive','protected private information')]:
                key=split+term+label
                records.append({'document_id':key,'group_id':key,'text':text+' '+term,'label':label,'split':split})
    data=tmp_path/'documents.jsonl';data.write_text(''.join(encoded(r)+'\n' for r in records))
    meta={k:'synthetic test only' for k in ('policy_definition','annotation_method','annotator_provenance','source','license','permitted_use','split_objective')}
    meta.update(task='document_sensitivity',labels={'not_sensitive':0,'sensitive':1},label_origin='synthetic_fixture',jsonl=data.name,sha256=hash_file(data)['sha256'])
    manifest=tmp_path/'manifest.json';atomic_json(manifest,meta)
    return manifest,records


def test_sensitivity_fixture_executes_but_cannot_validate(tmp_path):
    manifest,_=sensitivity_fixture(tmp_path)
    with pytest.raises(ValueError,match='cannot validate'):read_corpus(manifest,tmp_path)
    result=sensitivity_evaluate(manifest,tmp_path/'fixture',tmp_path,fixture=True)
    assert result['status']=='FIXTURE_ONLY_NOT_VALIDATED' and not result['validated_for_datashield']
    assert result['replay_equal'] and result['test']['confusion']['tp']>=0


def test_sensitivity_refuses_rule_cert_model_duplicate_and_group_labels(tmp_path):
    manifest,records=sensitivity_fixture(tmp_path);meta=json.loads(manifest.read_text())
    for origin in ('CERT','rule','model'):
        atomic_json(manifest,{**meta,'label_origin':origin})
        with pytest.raises(ValueError,match='cannot validate'):read_corpus(manifest,tmp_path)
    for field in ('text','group_id'):
        changed=[dict(r) for r in records];changed[-1][field]=changed[0][field]
        data=tmp_path/'documents.jsonl';data.write_text(''.join(encoded(r)+'\n' for r in changed))
        atomic_json(manifest,{**meta,'sha256':hash_file(data)['sha256']})
        with pytest.raises(ValueError,match='leakage'):read_corpus(manifest,tmp_path,fixture=True)


def test_nlp_shadow_preserves_rules_refuses_schema_tamper_and_provenance(tmp_path):
    from research.nlp_shadow import NLPShadow
    path=prepared_fixture(tmp_path);output=tmp_path/'shadow-run';report=evaluate(path,output,tmp_path)
    # Fixture provenance is explicitly fake and only used to exercise guards.
    report['preparation_contract']={'complete':True,**{k:'a'*64 for k in ('dataset_sha256','store_sha256','answers_sha256','answer_manifest_sha256')}}
    atomic_json(output/'report.json',report)
    pin=hash_file(output/'report.json')['sha256']
    db,_=cohort(path,tmp_path);window=rows(db,2)[0];db.close();text=window.pop('text')
    original={'decision':'ALLOW','rule_score':5}
    default=NLPShadow().attach(original,window,text,observed_at=window['end'])
    assert default['nlp_research_shadow']['status']=='DISABLED' and original=={'decision':'ALLOW','rule_score':5}
    shadow=NLPShadow(enabled=True,artifact=output,report_sha256=pin,folder=tmp_path)
    result=shadow.attach(original,window,text,observed_at=window['end'])
    assert result['nlp_research_shadow']['status']=='SHADOW_SCORED'
    assert result['decision']=='ALLOW' and result['rule_score']==5
    assert not result['nlp_research_shadow']['automated_blocking']
    assert text not in encoded(result) and window['user'] not in result['nlp_research_shadow']
    wrong={**window,'feature_version':'event-window-v2'}
    assert shadow.attach(original,wrong,text,observed_at=window['end'])['nlp_research_shadow']['status']=='FEATURE_SCHEMA_MISMATCH'
    assert shadow.attach(original,window,text+' ABC1234',observed_at=window['end'])['nlp_research_shadow']['status']=='UNSANITIZED_OR_EMPTY_TEXT'
    report['preparation_contract']['answers_sha256']='missing'
    atomic_json(output/'report.json',report);shadow.pin=hash_file(output/'report.json')['sha256']
    assert shadow.attach(original,window,text,observed_at=window['end'])['nlp_research_shadow']['status']=='ARTIFACT_PROVENANCE_MISMATCH'
    report['preparation_contract']['answers_sha256']='a'*64
    atomic_json(output/'report.json',report);shadow.pin=hash_file(output/'report.json')['sha256']
    with (output/'combined.joblib').open('ab') as f:f.write(b'tampered')
    assert shadow.attach(original,window,text,observed_at=window['end'])['nlp_research_shadow']['status']=='ARTIFACT_HASH_MISMATCH'


def test_test_labels_cannot_affect_vocabulary_scaling_or_validation_threshold(tmp_path):
    from research.behavioral_ml import select_threshold
    path=prepared_fixture(tmp_path);db,_=cohort(path,tmp_path)
    train,validation,test=rows(db,0),rows(db,1),rows(db,2);db.close()
    original=LinearBaseline('combined').fit(train)
    threshold=select_threshold([w['label'] for w in validation],original.scores(validation))[0]
    for w in test:w['label']=1-w['label'];w['text']='testexclusive vocabulary'
    repeat=LinearBaseline('combined').fit(train)
    assert original.tfidf.vocabulary_==repeat.tfidf.vocabulary_
    assert 'testexclusive' not in repeat.tfidf.vocabulary_
    assert np.array_equal(original.numeric.named_steps['scale'].mean_,repeat.numeric.named_steps['scale'].mean_)
    assert threshold==select_threshold([w['label'] for w in validation],repeat.scores(validation))[0]
