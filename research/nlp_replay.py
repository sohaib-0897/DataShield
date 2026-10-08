"""Compare first/last eligible held-out windows through the offline shadow loader."""
import argparse
from contextlib import closing
import json
from pathlib import Path

import numpy as np

from research.cert_ingest import atomic_json, encoded, hash_file, local_path
from research.nlp_cohort import cohort
from research.nlp_shadow import NLPShadow


def replay(prepared,benchmark,report_path,folder):
    benchmark=local_path(folder,benchmark);report_path=local_path(folder,report_path)
    if report_path.exists() or report_path==prepared:raise ValueError('New separate replay report required')
    engine=NLPShadow(enabled=True,artifact=benchmark,report_sha256=hash_file(benchmark/'report.json')['sha256'],folder=folder)
    db,_=cohort(prepared,folder)
    with closing(db):
        # Only boundary rows need loading; score arrays are small, bounded by the
        # held-out cohort's recorded size. No application services are started.
        query='''SELECT w.payload,w.text FROM windows w JOIN partitions p USING(start,user)
        WHERE p.part=2 AND p.has_text AND NOT p.seen_duplicate ORDER BY start {order},user {order} LIMIT 1'''
        boundary=[db.execute(query.format(order=direction)).fetchone() for direction in ('ASC','DESC')]
        results=[]
        for index,row in zip((0,-1),boundary):
            if row is None:raise ValueError('No held-out windows')
            payload,text=row;window=json.loads(payload);original={'decision':'ALLOW','rule_score':5}
            result=engine.attach(original,window,text,observed_at=window['end'])
            evidence=result['nlp_research_shadow']
            if evidence['status']!='SHADOW_SCORED':raise RuntimeError(evidence['status'])
            if original!={'decision':'ALLOW','rule_score':5} or result['decision']!='ALLOW' or result['rule_score']!=5:
                raise RuntimeError('Rule response changed')
            for mode,values in evidence['models'].items():
                path=local_path(folder,benchmark/f'{mode}_scores.json')
                if path.stat().st_size>64*1024**2:raise ValueError('Score memory bound')
                score=json.loads(path.read_text())['test'][index]
                if not np.isclose(values['score'],score,rtol=0,atol=1e-12):raise RuntimeError('Frozen score mismatch')
            results.append(evidence)
        report={'observations':2,'models_per_observation':3,'frozen_score_match_1e_12':True,
                'original_rules_preserved':True,'automated_blocking':False,'results':results}
        atomic_json(report_path,report)
        return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('prepared','benchmark','report'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();print(encoded(replay(a.prepared,a.benchmark,a.report,Path('research/local').absolute())))

if __name__=='__main__':main()
