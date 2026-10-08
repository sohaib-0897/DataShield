"""Offline binary document-sensitivity interface requiring independent supervision.

Manifest declares policy, permission, annotation provenance and fixed splits.
JSONL content is local only. Fixture runs are explicitly unvalidated.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import time

import joblib
import numpy as np
from sklearn.metrics import average_precision_score, confusion_matrix

from research.behavioral_ml import select_threshold
from research.cert_ingest import atomic_json, encoded, hash_file, local_path
from research.nlp_baselines import LinearBaseline

VERSION='document-sensitivity-supervision-v1'
LABELS={'not_sensitive':0,'sensitive':1}


def read_corpus(manifest_path,folder,*,max_bytes=64*1024**2,fixture=False):
    manifest_path=local_path(folder,manifest_path)
    if manifest_path.stat().st_size>1024**2:raise ValueError('Manifest memory bound')
    meta=json.loads(manifest_path.read_text())
    if meta.get('task')!='document_sensitivity' or meta.get('labels')!=LABELS:
        raise ValueError('Independent document sensitivity labels required')
    for name in ('policy_definition','annotation_method','annotator_provenance','source','license','permitted_use','split_objective'):
        if not isinstance(meta.get(name),str) or not meta[name].strip():raise ValueError('Missing supervision/permission provenance')
    expected='synthetic_fixture' if fixture else 'independent_human'
    if meta.get('label_origin')!=expected:raise ValueError('CERT, rule, model and synthetic labels cannot validate sensitivity')
    path=local_path(folder,manifest_path.parent/meta['jsonl'])
    if path.stat().st_size>max_bytes:raise ValueError('Corpus memory bound')
    if hash_file(path)['sha256']!=meta.get('sha256'):raise ValueError('Corpus digest mismatch')
    splits={k:[] for k in ('train','validation','test')};ids=set();bags={};groups={}
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            r=json.loads(line)
            if set(r)!={'document_id','group_id','text','label','split'}:raise ValueError('Unexpected corpus fields')
            if r['split'] not in splits or r['label'] not in LABELS:raise ValueError('Invalid split/label')
            if not all(isinstance(r[k],str) and r[k].strip() for k in ('document_id','group_id','text')):raise ValueError('Empty document/group/content')
            if r['document_id'] in ids:raise ValueError('Duplicate document')
            ids.add(r['document_id']);part=r['split']
            # Conservative keyword bag equality catches reordered copies. Exact
            # case-insensitive content also catches punctuation-only documents.
            digest=hashlib.sha256(' '.join(sorted(r['text'].lower().split())).encode()).hexdigest()
            for mapping,key in ((bags,digest),(groups,r['group_id'])):
                if key in mapping and mapping[key]!=part:raise ValueError('Cross-split duplicate/group leakage')
                mapping[key]=part
            splits[part].append({'text':r['text'],'label':LABELS[r['label']]})
    for k,rows in splits.items():
        counts=Counter(w['label'] for w in rows)
        if min(counts[0],counts[1])<(2 if k=='train' else 1):raise ValueError('Need both classes in fixed splits (>=2/class train)')
    return meta,splits


def evaluate(manifest,output,folder,fixture=False):
    output=local_path(folder,output)
    if output.exists():raise ValueError('New output required')
    started=time.perf_counter();meta,splits=read_corpus(manifest,folder,fixture=fixture)
    model=LinearBaseline('text').fit(splits['train'])
    val=model.scores(splits['validation'])
    threshold,strategy=select_threshold([w['label'] for w in splits['validation']],val)
    output.mkdir();atomic_json(output/'frozen_threshold.json',{'threshold':threshold,'partition':'validation','strategy':strategy})
    scores=model.scores(splits['test']);y=np.array([w['label'] for w in splits['test']])
    tn,fp,fn,tp=map(int,confusion_matrix(y,scores>threshold,labels=[0,1]).ravel())
    joblib.dump(model,output/'text.joblib');restored=joblib.load(output/'text.joblib');replay=LinearBaseline('text').fit(splits['train'])
    if not np.array_equal(scores,restored.scores(splits['test'])) or not np.array_equal(scores,replay.scores(splits['test'])):
        raise RuntimeError('Sensitivity replay failed')
    result={'version':VERSION,'status':'FIXTURE_ONLY_NOT_VALIDATED' if fixture else 'OFFLINE_INDEPENDENT_CORPUS_EVALUATION',
            'manifest_sha256':hash_file(manifest)['sha256'],'corpus_sha256':meta['sha256'],
            'supervision':{k:meta[k] for k in ('label_origin','policy_definition','annotation_method','annotator_provenance','source','license','permitted_use','split_objective')},
            'splits':{k:{'documents':len(ws),'class_counts':dict(Counter(w['label'] for w in ws))} for k,ws in splits.items()},
            'threshold':threshold,'threshold_strategy':strategy,'threshold_partition':'validation','vocabulary_fit_partition':'train',
            'test':{'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn),'f1':2*tp/(2*tp+fp+fn),
                    'average_precision':float(average_precision_score(y,scores)),'confusion':{'tn':tn,'fp':fp,'fn':fn,'tp':tp},
                    'prevalence':float(y.mean()),'false_alerts_per_1000_documents':1000*fp/len(y)},
            'score_kind':'uncalibrated_linear_decision_function','replay_equal':True,'artifact_sha256':hash_file(output/'text.joblib')['sha256'],
            'seconds':time.perf_counter()-started,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            'live_activation':False,'validated_for_datashield':False}
    atomic_json(output/'report.json',result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--fixture-only',action='store_true');a=p.parse_args()
    print(encoded(evaluate(a.manifest,a.output,Path('research/local').absolute(),a.fixture_only)))

if __name__=='__main__':main()
