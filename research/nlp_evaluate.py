"""Separate known-user later-time CERT experiment, preserving the strict study."""
import argparse
from collections import Counter
from contextlib import closing
import json
from pathlib import Path
import platform
import resource
import time

import joblib
import numpy as np
import sklearn

from ml.features.windows import FEATURE_NAMES
from research.behavioral_ml import measured_metrics, select_threshold
from research.cert_ingest import atomic_json, encoded, hash_file, local_path, require_space
from research.nlp_baselines import LinearBaseline
from research.nlp_cohort import cohort, rows, group_audit

VERSION='cert-known-users-nlp-v1'


def metrics(values,scores,threshold):
    value=measured_metrics(values,scores,threshold)
    value['false_alerts_per_1000_windows']=value['confusion']['fp']*1000/len(values)
    return value


def errors(values,scores,threshold):
    bins={name:[] for name in ('tp','fp','tn','fn')}
    for w,score in zip(values,scores):
        name=('tp' if w['label'] else 'fp') if score>threshold else ('fn' if w['label'] else 'tn')
        bins[name].append(w)
    return {name:{'windows':len(ws),'after_hours_windows':sum(w['features']['after_hours_fraction']>0 for w in ws),
                  'file_windows':sum(w['features']['file_count']>0 for w in ws),
                  'cold_start_windows':sum(w['features']['cold_start'] for w in ws),
                  'text_word_count_mean':float(np.mean([len(w['text'].split()) for w in ws])) if ws else None,
                  'positive_scenarios':dict(Counter(p['scenario'] for w in ws for p in w['label_provenance']))}
            for name,ws in bins.items()}


def evaluate(prepared,output,folder):
    output=local_path(folder,output)
    if output.exists():raise ValueError('Preserve outputs; new directory required')
    require_space(folder,64*1024**2)
    started=time.perf_counter();db,audit=cohort(prepared,folder)
    with closing(db):
        output.mkdir();atomic_json(output/'cohort.json',audit)
        train,validation=rows(db,0),rows(db,1)
        reasons=[]
        if min(Counter(w['label'] for w in train)[k] for k in (0,1))<2:reasons.append('insufficient_train_classes')
        if min(Counter(w['label'] for w in validation)[k] for k in (0,1))<1:reasons.append('insufficient_validation_classes')
        if not audit['known_users_alternative']['test']['windows']:reasons.append('empty_test')
        report={'version':VERSION,'status':'RESEARCH_ONLY_NOT_REGISTRABLE','protocol':'known-users-later-time-v1',
                'task':'CERT malicious event-window keywords; not sensitivity', 'comparison_status':'UNAVAILABLE' if reasons else 'COMPLETED',
                'unavailable_reasons':reasons,'feature_version':'cert-user-hour-v1','feature_names':FEATURE_NAMES,
                'preparation_contract':audit['preparation'],'prepared_sha256':audit['prepared_sha256'],
                'cohort_sha256':hash_file(output/'cohort.json')['sha256'],'models':{},
                'score_kind':'uncalibrated_linear_decision_function','seed':42,'fit_partition':'train','threshold_partition':'validation',
                'software':{'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,'joblib':joblib.__version__},
                'live_activation':False,'full_dataset':False,'document_sensitivity_validation':'NOT_ESTABLISHED'}
        if not reasons:
            fitted={};thresholds={}
            for mode in ('numeric','text','combined'):
                begin=time.perf_counter();model=LinearBaseline(mode).fit(train)
                validation_scores=model.scores(validation)
                threshold,strategy=select_threshold([w['label'] for w in validation],validation_scores)
                fitted[mode]=model;thresholds[mode]={'threshold':threshold,'strategy':strategy}
                report['models'][mode]={'threshold':threshold,'threshold_strategy':strategy,'fit_rows':len(train),
                    'validation':metrics(validation,validation_scores,threshold),'training_and_validation_seconds':time.perf_counter()-begin}
            # This immutable artifact exists before test rows are loaded/scored.
            atomic_json(output/'frozen_thresholds.json',thresholds)
            report['frozen_thresholds_sha256']=hash_file(output/'frozen_thresholds.json')['sha256']
            test=rows(db,2)
            report['group_overlap']=group_audit({'train':train,'validation':validation,'test':test})
            report['common_population']=audit['known_users_alternative']
            for mode,model in fitted.items():
                begin=time.perf_counter();scores=model.scores(test);latency=time.perf_counter()-begin
                joblib.dump(model,output/f'{mode}.joblib')
                reload=joblib.load(output/f'{mode}.joblib')
                replay=LinearBaseline(mode).fit(train)
                replay_threshold=select_threshold([w['label'] for w in validation],replay.scores(validation))[0]
                joblib.dump(replay,output/f'{mode}_replay.joblib')
                equal=bool(np.array_equal(scores,reload.scores(test)) and np.array_equal(scores,replay.scores(test)) and replay_threshold==thresholds[mode]['threshold'])
                hash_equal=hash_file(output/f'{mode}.joblib')['sha256']==hash_file(output/f'{mode}_replay.joblib')['sha256']
                if not equal or not hash_equal:raise RuntimeError('Reproducibility failure')
                item=report['models'][mode];threshold=item['threshold']
                item.update(test=metrics(test,scores,threshold),error_analysis=errors(test,scores,threshold),
                            artifact_sha256=hash_file(output/f'{mode}.joblib')['sha256'],replay_scores_threshold_equal=equal,
                            replay_artifact_hash_equal=hash_equal,batch_inference_seconds=latency,
                            vocabulary_size=len(model.tfidf.vocabulary_) if mode!='numeric' else None)
                atomic_json(output/f'{mode}_scores.json',{'test':scores.tolist(),'validation':model.scores(validation).tolist(),'threshold':threshold})
        if hash_file(prepared)['sha256']!=audit['prepared_sha256']:raise ValueError('Prepared snapshot changed during evaluation')
        report.update(seconds=time.perf_counter()-started,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
        atomic_json(output/'report.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(encoded(evaluate(a.prepared,a.output,Path('research/local').absolute())))

if __name__=='__main__':main()
