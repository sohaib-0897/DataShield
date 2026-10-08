"""Synthetic guard fixtures only; these tests are not corpus evaluation."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from research import tab_acquire, tab_baseline, tab_prepare
from research.cert_ingest import atomic_json, hash_file


def doc(text='Alpha Beta Gamma Delta Epsilon Zeta', task='subject-a', applicant='applicant-a', label='PERSON'):
    mention={'start_offset':0,'end_offset':5,'entity_type':label,'span_text':text[:5]}
    return {'doc_id':task,'text':text,'task':task,'meta':{'applicant':applicant},
            'quality_checked':['one'],'annotations':{'one':{'entity_mentions':[mention]}}}


def test_reviewed_unanimity_and_presence_abstention():
    d=doc();d['quality_checked'].append('two')
    d['annotations']['two']={'entity_mentions':[dict(d['annotations']['one']['entity_mentions'][0],entity_type='ORG')]}
    rows,audit=tab_prepare.consensus(d)
    assert not rows and audit['reviewed_category_disagreements']==1
    d['annotations']['two']['entity_mentions']=[]
    assert tab_prepare.consensus(d)[1]['reviewed_boundary_or_presence_disagreements']==1


def test_conflicting_duplicate_offsets_never_silently_overwrite():
    d=doc();d['annotations']['one']['entity_mentions'].append(dict(d['annotations']['one']['entity_mentions'][0],entity_type='ORG'))
    rows,audit=tab_prepare.consensus(d)
    assert not rows and audit['conflicting_duplicate_offsets_within_annotation_set']==1


def test_unreviewed_annotations_are_not_gold_and_are_preserved():
    d=doc();d['quality_checked']=[];before=json.dumps(d,sort_keys=True)
    assert not tab_prepare.consensus(d)[0]
    assert json.dumps(d,sort_keys=True)==before


def test_grouping_transitive_subject_version_and_near_duplicate():
    a=doc(task='one');b=doc(text='Different entirely unique content here',task='two')
    c=doc(text='different ENTIRELY unique content here!',task='three',applicant='third')
    groups,edges,near=tab_prepare.group_documents([a,b,c])
    assert len(set(groups))==1 and near==1
    assert {e[2] for e in edges}>={'subject','normalized_text'}


def test_grouping_does_not_merge_unrelated_cases():
    groups,_,_=tab_prepare.group_documents([doc(),doc('Unrelated text has distinct words here',task='other',applicant='other')])
    assert len(set(groups))==2


def test_pin_size_and_content_required(tmp_path):
    p=tmp_path/'partial';p.write_bytes(b'abc')
    entry={'size':4,'sha':'x'}
    with pytest.raises(ValueError,match='Incomplete'):tab_acquire.verify_blob(p,entry)
    entry={'size':3,'sha':'0'*40}
    with pytest.raises(ValueError,match='blob'):tab_acquire.verify_blob(p,entry)
    entry['sha']=hashlib.sha1(b'blob 3\0abc').hexdigest()
    assert tab_acquire.verify_blob(p,entry)==hash_file(p)


def test_acquisition_partial_resume_and_no_manifest_on_failure(tmp_path,monkeypatch):
    root=tmp_path/'research/local';root.mkdir(parents=True);monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(tab_acquire,'FILES',('LICENSE.txt',))
    content=b'The MIT License fixture'
    tree={'sha':tab_acquire.REVISION,'truncated':False,'tree':[{'path':'LICENSE.txt','type':'blob','size':len(content),
          'sha':hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()}]}
    tree_path=root/'tree.json';atomic_json(tree_path,tree)
    monkeypatch.setattr(tab_acquire,'TREE_SHA256',hash_file(tree_path)['sha256'])
    dest=root/'download';dest.mkdir();partial=dest/'LICENSE.txt.partial';partial.write_bytes(content[:5])
    calls=[]
    def fail(cmd,**kw):calls.append(cmd);return SimpleNamespace(returncode=28)
    result=tab_acquire.acquire(dest,tree_path,attempts=1,timeout=1,runner=fail)
    assert result['status']=='ACQUISITION_BLOCKED' and not (dest/'acquisition.json').exists()
    assert '--continue-at' in calls[0] and partial.read_bytes()==content[:5]
    def finish(cmd,**kw):partial.write_bytes(content);return SimpleNamespace(returncode=0)
    assert tab_acquire.acquire(dest,tree_path,attempts=1,timeout=1,runner=finish)['trusted_manifest']


def test_invalid_pinned_completion_is_quarantined(tmp_path,monkeypatch):
    root=tmp_path/'research/local';root.mkdir(parents=True);monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(tab_acquire,'FILES',('LICENSE.txt',))
    tree={'sha':tab_acquire.REVISION,'truncated':False,'tree':[{'path':'LICENSE.txt','type':'blob','size':3,'sha':'0'*40}]}
    t=root/'tree.json';atomic_json(t,tree);monkeypatch.setattr(tab_acquire,'TREE_SHA256',hash_file(t)['sha256'])
    out=root/'acquire'
    def corrupt(cmd,**kw):Path(cmd[cmd.index('--output')+1]).write_bytes(b'bad');return SimpleNamespace(returncode=0)
    assert not tab_acquire.acquire(out,t,attempts=1,timeout=1,runner=corrupt)['trusted_manifest']
    assert len(list(out.glob('*.invalid-*.partial')))==1 and not (out/'LICENSE.txt').exists()


def test_training_only_vocabulary_and_repeatable_margins():
    texts=['PERSON name Alice','PERSON name Bob','ORG institution Court','ORG institution Bank']*3
    labels=['PERSON','PERSON','ORG','ORG']*3
    first=tab_baseline.pipeline().fit(texts,labels);second=tab_baseline.pipeline().fit(texts,labels)
    before=first['features'].transformer_list[0][1].vocabulary_.copy()
    scores=first.decision_function(['validationOnlyTerm Alice','testOnlyTerm Court'])
    assert 'validationonlyterm' not in before and 'testonlyterm' not in before
    assert first['features'].transformer_list[0][1].vocabulary_==before
    assert np.array_equal(scores,second.decision_function(['validationOnlyTerm Alice','testOnlyTerm Court']))


def test_undefined_metrics_support_and_abstention():
    r=tab_baseline.metrics(['PERSON','PERSON'],['ABSTAIN','ABSTAIN'])
    assert r['per_class']['ORG']['recall'] is None
    assert r['per_class']['PERSON']['precision'] is None
    assert r['per_class']['PERSON']['recall']==0 and r['per_class']['PERSON']['f1']==0
    assert r['predicted_rows']==0 and len(r['confusion_matrix'])==9


def test_frozen_manifest_change_is_rejected(tmp_path):
    p=tmp_path/'train.json';atomic_json(p,[{'label':'PERSON','entity':'Alice','context':'Alice'}])
    report={'manifest_hashes':{'train':hash_file(p)}}
    assert tab_baseline.load_split(tmp_path,'train',report)
    p.write_text('[]')
    with pytest.raises(ValueError,match='manifest'):tab_baseline.load_split(tmp_path,'train',report)


def test_no_test_load_during_training(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    root=tmp_path/'research/local/prepared';root.mkdir(parents=True)
    rows=[{'label':c,'entity':c+' specimen text','context':c+' bounded context', 'group':'train'}
          for c in tab_prepare.CLASSES for _ in range(3)]
    val=[dict(r,group='validation') for r in rows]
    atomic_json(root/'train.json',rows);atomic_json(root/'validation.json',val)
    (root/'test.json').write_text('UNREADABLE HELD OUT TEST')
    prep={'version':tab_prepare.VERSION,'task':tab_prepare.TASK,'cross_split_group_overlap':0,
          'manifest_hashes':{s:hash_file(root/f'{s}.json') for s in ('train','validation','test')}}
    atomic_json(root/'preparation.json',prep)
    real_loader=tab_baseline.load_split;calls=[]
    def guarded(root,split,report):
        assert split!='test';calls.append(split);return real_loader(root,split,report)
    monkeypatch.setattr(tab_baseline,'load_split',guarded)
    result=tab_baseline.train(root,tmp_path/'research/local/models')
    assert calls==['train','validation'] and result['test_loaded'] is False


def test_official_test_wins_over_family_related_train_and_validation(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    root=tmp_path/'research/local/source';root.mkdir(parents=True)
    tree_path=root.parent/'tab-tree.json';atomic_json(tree_path,{'tree':[]})
    monkeypatch.setattr(tab_prepare,'TREE_SHA256',hash_file(tree_path)['sha256'])
    monkeypatch.setattr(tab_prepare,'inventory',lambda *a:{'revision':'fixture','license':'MIT','acquisition':{},
                                                        'splits_as_supplied_not_training_approved':{}})
    for split in ('train','dev','test'):
        d=doc(task=split,applicant='same-family');d['dataset_type']=split
        atomic_json(root/f'echr_{split}.json',[d])
    out=tmp_path/'research/local/prepared'
    report=tab_prepare.prepare(root,out)
    assert report['splits']['train']['spans']==report['splits']['validation']['spans']==0
    assert report['splits']['test']['spans']==1 and report['cross_split_group_overlap']==0
    manifest=json.loads((out/'documents.json').read_text())
    assert [r['official_split'] for r in manifest if r['retained']]==['test']
    assert report['annotation_audit']['quarantined_family_overlap_documents']==2


def test_range_unsupported_partial_is_preserved_before_bounded_restart(tmp_path,monkeypatch):
    root=tmp_path/'research/local';root.mkdir(parents=True);monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(tab_acquire,'FILES',('LICENSE.txt',))
    content=b'The MIT License fixture';out=root/'acquire';out.mkdir()
    (out/'LICENSE.txt.partial').write_bytes(content[:5])
    tree={'sha':tab_acquire.REVISION,'truncated':False,'tree':[{'path':'LICENSE.txt','type':'blob','size':len(content),
          'sha':hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()}]}
    t=root/'tree.json';atomic_json(t,tree);monkeypatch.setattr(tab_acquire,'TREE_SHA256',hash_file(t)['sha256'])
    calls=[]
    def runner(cmd,**kw):
        calls.append(cmd)
        if len(calls)==1:return SimpleNamespace(returncode=33)
        Path(cmd[cmd.index('--output')+1]).write_bytes(content)
        return SimpleNamespace(returncode=0)
    assert tab_acquire.acquire(out,t,attempts=2,timeout=1,runner=runner)['trusted_manifest']
    assert '--continue-at' in calls[0] and '--continue-at' not in calls[1]
    assert next(out.glob('*.range-unsupported-*.partial')).read_bytes()==content[:5]
