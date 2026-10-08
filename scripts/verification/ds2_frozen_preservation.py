"""Read-only 13-artifact check using the existing canonical feature verifier."""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from research.cert_features import load_artifact
from research.cert_ingest import atomic_json, hash_file, local_path


def verify(root):
    folder=root/'research/local';checks={};expected={}
    for phase,feature,store in [(3,'phase2_features_v1.json','cert_r42.sqlite'),(6,'phase6_features.json','phase6_cohort.sqlite')]:
        report=json.loads((root/f'docs/implementation/phase{phase}/benchmark.json').read_text())
        prefix=f'phase{phase}_benchmark_v1'
        value=load_artifact(folder/feature,folder,max_bytes=512*1024**2)
        checks[prefix+'/features']=value['artifact_sha256']==report['feature_artifact_sha256']
        expected[prefix+'/features']=report['feature_artifact_sha256'];del value
        checks[prefix+'/store']=hash_file(folder/store)['sha256']==report['store_sha256']
        expected[prefix+'/store']=report['store_sha256']
        for model,item in report['models'].items():
            key=prefix+'/'+model;expected[key]=item['artifact_sha256']
            checks[key]=hash_file(folder/prefix/(model+'.joblib'))['sha256']==expected[key]
    report=json.loads((root/'docs/implementation/nlp-followup/comparison.json').read_text())
    for model,item in report['models'].items():
        key='nlp_known_users_v1/'+model;expected[key]=item['artifact_sha256']
        checks[key]=hash_file(folder/'nlp_known_users_v1'/(model+'.joblib'))['sha256']==expected[key]
    for name,key in [('cohort.json','cohort_sha256'),('frozen_thresholds.json','frozen_thresholds_sha256')]:
        artifact='nlp_known_users_v1/'+name;expected[artifact]=report[key]
        checks[artifact]=hash_file(folder/'nlp_known_users_v1'/name)['sha256']==expected[artifact]
    expected['nlp_june_stream.sqlite']=report['prepared_sha256']
    checks['nlp_june_stream.sqlite']=hash_file(folder/'nlp_june_stream.sqlite')['sha256']==report['prepared_sha256']
    assert len(checks)==13
    return {'read_only_preservation_checks':checks,'expected_hashes':expected,'all_match':all(checks.values()),
            'feature_hash_contract':'existing research.cert_features.load_artifact canonical JSON payload; others whole-file SHA-256',
            'no_preparation_or_training_rerun':True}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    root=Path(__file__).resolve().parents[2];out=local_path(root/'research/local',a.output)
    if out.exists():raise ValueError('New preservation report required')
    started=time.perf_counter();result=verify(root);result['seconds']=time.perf_counter()-started
    atomic_json(out,result);print(json.dumps({'checks':13,'all_match':result['all_match']}))
    return 0 if result['all_match'] else 1


if __name__=='__main__':raise SystemExit(main())
