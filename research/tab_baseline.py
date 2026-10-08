"""CPU-only TAB supplied-span baseline; separate train and final evaluation commands."""
import argparse
import os

# Bound BLAS/OpenMP before scientific imports in the standalone CLI.
for variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[variable] = '1'
from collections import Counter
import json
from pathlib import Path
import platform
import resource
import time

import joblib
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score

from research.cert_ingest import atomic_json, hash_file, local_path
from research.documents import PATTERNS
from research.tab_prepare import CLASSES, TASK, VERSION, normalized

CONFIG = {'seed':42,'C':1.0,'word_features':20000,'char_features':20000,'min_df':2,
          'context_characters_each_side':160,'maximum_rows':100000,'maximum_input_bytes':80*1024**2,
          'cpu_seconds':300,'address_space_bytes':4*1024**3,'selection':'validation macro F1; ties prefer entity',
          'prediction':'multiclass argmax; no threshold tuning','class_weight':None,
          'pr_auc':'average precision; >=5 positives and >=5 negatives per class',
          'modes':['entity','context']}


def bounded_json(path, max_bytes=80*1024**2):
    if path.stat().st_size>max_bytes: raise ValueError('Input byte bound exceeded')
    return json.loads(path.read_text())


def load_split(root, split, report):
    path=root/f'{split}.json'
    if hash_file(path)!=report['manifest_hashes'][split]: raise ValueError('Frozen manifest mismatch')
    rows=bounded_json(path)
    if not rows or len(rows)>CONFIG['maximum_rows']: raise ValueError('Span count bound')
    if any(r['label'] not in CLASSES or not r['entity'] or len(r['context'])>len(r['entity'])+340 for r in rows):
        raise ValueError('Span schema mismatch')
    return rows


def pipeline():
    return Pipeline([('features',FeatureUnion([
        ('word',TfidfVectorizer(ngram_range=(1,2),min_df=2,max_features=20000,dtype=np.float32)),
        ('char',TfidfVectorizer(analyzer='char',ngram_range=(3,5),min_df=2,max_features=20000,dtype=np.float32))])),
        ('classifier',LinearSVC(C=1.0,random_state=42,dual='auto',max_iter=5000))])


def metrics(truth,pred,scores=None):
    counts=Counter(truth)
    per={}
    for i,c in enumerate(CLASSES):
        tp=sum(t==c and p==c for t,p in zip(truth,pred));fp=sum(t!=c and p==c for t,p in zip(truth,pred))
        fn=counts[c]-tp
        per[c]={'support':counts[c],'tp':tp,'fp':fp,'fn':fn,
                'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/counts[c] if counts[c] else None,
                'f1':2*tp/(2*tp+fp+fn) if counts[c] else None,
                'average_precision':float(average_precision_score(np.array(truth)==c,scores[:,i]))
                     if scores is not None and counts[c]>=5 and len(truth)-counts[c]>=5 else None}
    labels=CLASSES+(['ABSTAIN'] if 'ABSTAIN' in pred else [])
    return {'per_class':per,'macro_f1':float(f1_score(truth,pred,labels=[c for c in CLASSES if counts[c]],average='macro',zero_division=0)),
            'macro_class_policy':'classes with positive truth support; undefined per-class precision remains null',
            'micro_f1':float(f1_score(truth,pred,labels=CLASSES,average='micro',zero_division=0)),
            'confusion_labels':labels,'confusion_matrix':confusion_matrix(truth,pred,labels=labels).tolist(),
            'rows':len(truth),'predicted_rows':sum(p!='ABSTAIN' for p in pred)}


def inputs(rows,mode): return [r[mode] for r in rows]


def train(prepared,output):
    folder=Path('research/local').absolute();prepared=local_path(folder,prepared);output=local_path(folder,output)
    if output.exists(): raise ValueError('New model output required')
    report=bounded_json(prepared/'preparation.json',1024**2)
    if report['version']!=VERSION or report['task']!=TASK or report['cross_split_group_overlap']!=0:
        raise ValueError('Unsupported task/split contract')
    train_rows=load_split(prepared,'train',report);val=load_split(prepared,'validation',report)
    if set(r['label'] for r in train_rows)!=set(CLASSES): raise ValueError('Missing training class')
    if {r['group'] for r in train_rows}&{r['group'] for r in val}: raise ValueError('Group leakage')
    output.mkdir(parents=True,mode=0o700)
    # Training inputs and candidate configuration frozen BEFORE any fit. Never load test here.
    atomic_json(output/'training_contract.json',{'config':CONFIG,'preparation':hash_file(prepared/'preparation.json'),
                                               'manifest_hashes':report['manifest_hashes'],'task':TASK,'live_activation':False})
    models={};y=[r['label'] for r in train_rows];yv=[r['label'] for r in val]
    for mode in CONFIG['modes']:
        started=time.perf_counter();model=pipeline();model.fit(inputs(train_rows,mode),y)
        pred=model.predict(inputs(val,mode)).tolist();scores=model.decision_function(inputs(val,mode))
        if list(model.classes_)!=CLASSES: raise ValueError('Class order mismatch')
        path=output/f'{mode}.joblib';joblib.dump(model,path,compress=3);path.chmod(0o600)
        reloaded=joblib.load(path)
        if not np.array_equal(scores,reloaded.decision_function(inputs(val,mode))): raise ValueError('Reload score mismatch')
        models[mode]={'artifact':hash_file(path),'validation':metrics(yv,pred,scores),
                      'seconds':time.perf_counter()-started,'train_rows':len(y),'reload_equal':True}
    selected=max(CONFIG['modes'],key=lambda m:models[m]['validation']['macro_f1'])
    majority=Counter(y).most_common(1)[0][0]
    result={'version':VERSION,'task':TASK,'status':'OFFLINE_RESEARCH_ONLY','live_activation':False,
            'score_kind':'uncalibrated LinearSVC decision margins; not probabilities','config':CONFIG,
            'preparation':hash_file(prepared/'preparation.json'),'contract':hash_file(output/'training_contract.json'),
            'software':{'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,'joblib':joblib.__version__},
            'models':models,'selected_mode':selected,'majority_class':majority,
            'majority_validation':metrics(yv,[majority]*len(yv)),
            'fit_partition':'train','selection_partition':'validation','test_loaded':False}
    atomic_json(output/'selection.json',result)
    return result


def evaluate(prepared,model_root,output):
    folder=Path('research/local').absolute()
    prepared,model_root,output=[local_path(folder,p) for p in (prepared,model_root,output)]
    if output.exists(): raise ValueError('Final evaluation is immutable; new output required')
    prep=bounded_json(prepared/'preparation.json',1024**2)
    selection=bounded_json(model_root/'selection.json',1024**2)
    if (selection['version'] != VERSION or selection['task'] != TASK or selection['live_activation'] is not False
            or selection['fit_partition'] != 'train' or selection['selection_partition'] != 'validation'
            or selection['test_loaded'] is not False or selection['config'] != CONFIG):
        raise ValueError('Offline task/model contract mismatch')
    software={'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,'joblib':joblib.__version__}
    if selection['software'] != software: raise ValueError('Reproduction software mismatch')
    if selection['preparation']!=hash_file(prepared/'preparation.json') or selection['contract']!=hash_file(model_root/'training_contract.json'):
        raise ValueError('Model/split contract changed')
    test=load_split(prepared,'test',prep);train_rows=load_split(prepared,'train',prep)
    if {r['group'] for r in test}&{r['group'] for r in train_rows}:raise ValueError('Test group leakage')
    y=[r['label'] for r in test];outputs={};predictions={}
    seen={normalized(r['entity']) for r in train_rows};counts=Counter(r['label'] for r in train_rows)
    for mode in CONFIG['modes']:
        path=model_root/f'{mode}.joblib'
        if hash_file(path)!=selection['models'][mode]['artifact']:raise ValueError('Artifact changed')
        model=joblib.load(path)  # Only locally trained/pinned artifacts, never downloaded models.
        if list(model.classes_)!=CLASSES:raise ValueError('Class order mismatch')
        pred=model.predict(inputs(test,mode)).tolist();scores=model.decision_function(inputs(test,mode))
        outputs[mode]=metrics(y,pred,scores);predictions[mode]=pred
    majority=selection['majority_class'];outputs['majority']=metrics(y,[majority]*len(y))
    # Existing rules only recognize email/CNIC patterns. Conditional CODE proxy;
    # abstain for other inputs, never equate CODE with credentials/sensitivity.
    rule_pred=['CODE' if any(p.fullmatch(r['entity']) for p in PATTERNS.values()) else 'ABSTAIN' for r in test]
    outputs['existing_email_cnic_CODE_proxy']=metrics(y,rule_pred)
    selected=selection['selected_mode'];pred=predictions[selected]
    strata={
        'entity_text_seen_in_training':[i for i,r in enumerate(test) if normalized(r['entity']) in seen],
        'entity_text_unseen_in_training':[i for i,r in enumerate(test) if normalized(r['entity']) not in seen],
        'person_name_seen_in_training':[i for i,r in enumerate(test) if r['label']=='PERSON' and normalized(r['entity']) in seen],
        'ambiguous_raw_category':[i for i,r in enumerate(test) if r['ambiguous_raw_category']],
        'least_supported_training_classes':[i for i,r in enumerate(test) if counts[r['label']]<=1000]}
    result={'version':VERSION,'task':TASK,'selection':hash_file(model_root/'selection.json'),
            'selected_mode':selected,'models':outputs,'score_kind':selection['score_kind'],'test_manifest':prep['manifest_hashes']['test'],
            'strata':{s:metrics([y[i] for i in ids],[pred[i] for i in ids]) if ids else {'rows':0,'status':'UNAVAILABLE'} for s,ids in strata.items()},
            'domain':'English ECHR legal narratives only; corporate documents/credentials/policy sensitivity unvalidated',
            'organizational_labels':False,'live_activation':False}
    output.mkdir(parents=True,mode=0o700)
    atomic_json(output/'evaluation.json',result)
    atomic_json(output/'predictions.json',{'ids':[r['id'] for r in test],'truth':y,'predictions':predictions})
    (output/'predictions.json').chmod(0o600)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['train','evaluate'])
    p.add_argument('--prepared',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--models',type=Path);a=p.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU,(CONFIG['cpu_seconds'],CONFIG['cpu_seconds']))
    resource.setrlimit(resource.RLIMIT_AS,(CONFIG['address_space_bytes'],CONFIG['address_space_bytes']))
    r=train(a.prepared,a.output) if a.command=='train' else evaluate(a.prepared,a.models,a.output)
    print(json.dumps({'task':r['task'],'selected_mode':r['selected_mode'],'live_activation':False}))


if __name__=='__main__':main()
