"""Explicit offline NLP shadow replay. No runtime wiring or model activation.

Only load locally trained trusted pickle artifacts with independently pinned
report digest. Digests do not make arbitrary third-party pickle code safe.
"""
from copy import deepcopy
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import platform
import re

import joblib
import numpy as np
import sklearn

from ml.features.windows import CHANNELS, FEATURE_NAMES, VERSION
from research.cert_ingest import hash_file, local_path
from research.nlp_evaluate import VERSION as REPORT_VERSION
from research.text_study import normalize_keywords


class NLPShadow:
    def __init__(self, *, enabled=False, artifact=None, report_sha256=None, folder=None):
        self.enabled=enabled;self.artifact=artifact;self.pin=report_sha256
        self.folder=Path('research/local').absolute() if folder is None else folder

    def attach(self, original, window, text, *, observed_at):
        response=deepcopy(original)
        result={'status':'DISABLED','mode':'shadow','automated_blocking':False,'fallback':'existing_rules',
                'task':'CERT malicious window; NOT document sensitivity','score_kind':'uncalibrated_linear_decision_function'}
        response['nlp_research_shadow']=result
        if not self.enabled:return response
        try:
            if not window or window.get('feature_version')!=VERSION:
                result['status']='FEATURE_SCHEMA_MISMATCH';return response
            if not window.get('fully_observed') or datetime.fromisoformat(window['end'])>datetime.fromisoformat(observed_at):
                result['status']='INCOMPLETE_WINDOW';return response
            if tuple(window['features'])!=FEATURE_NAMES and set(window['features'])!=set(FEATURE_NAMES):
                result['status']='FEATURE_SCHEMA_MISMATCH';return response
            if any(window['features'].get(c.lower()+'_available')!=1 or window['features'].get(c.lower()+'_count') is None for c in CHANNELS):
                result['status']='INCOMPLETE_CHANNELS';return response
            if any(v is not None and (not isinstance(v,(int,float)) or not np.isfinite(v)) for v in window['features'].values()):
                result['status']='INVALID_FEATURES';return response
            if not text or normalize_keywords(text)!=text:
                result['status']='UNSANITIZED_OR_EMPTY_TEXT';return response
            root=local_path(self.folder,self.artifact);report_path=local_path(self.folder,root/'report.json')
            if report_path.stat().st_size>1024**2 or hash_file(report_path)['sha256']!=self.pin:
                result['status']='REPORT_PIN_MISMATCH';return response
            report=json.loads(report_path.read_text())
            valid=(report['version']==REPORT_VERSION and report['status']=='RESEARCH_ONLY_NOT_REGISTRABLE' and
                   report['comparison_status']=='COMPLETED' and report['feature_version']==VERSION and
                   tuple(report['feature_names'])==FEATURE_NAMES and report['protocol']=='known-users-later-time-v1' and
                   report['score_kind']=='uncalibrated_linear_decision_function' and report['fit_partition']=='train' and
                   report['threshold_partition']=='validation' and report['live_activation'] is False)
            provenance=report['preparation_contract']
            valid=valid and provenance['complete'] and all(re.fullmatch('[0-9a-f]{64}',v) for v in
                (report['prepared_sha256'],report['cohort_sha256'],report['frozen_thresholds_sha256'],provenance['dataset_sha256'],
                 provenance['store_sha256'],provenance['answers_sha256'],provenance['answer_manifest_sha256']))
            if not valid:
                result['status']='ARTIFACT_PROVENANCE_MISMATCH';return response
            expected={'python':platform.python_version(),'sklearn':sklearn.__version__,'numpy':np.__version__,'joblib':joblib.__version__}
            if report['software']!=expected:
                result['status']='SOFTWARE_MISMATCH';return response
            for filename,key in [('cohort.json','cohort_sha256'),('frozen_thresholds.json','frozen_thresholds_sha256')]:
                if hash_file(local_path(self.folder,root/filename))['sha256']!=report[key]:
                    result['status']='ARTIFACT_PROVENANCE_MISMATCH';return response
            models={}
            # Validate every digest/schema/threshold before unpickling any model.
            for mode in ('numeric','text','combined'):
                path=local_path(self.folder,root/f'{mode}.joblib');item=report['models'][mode]
                if path.stat().st_size>64*1024**2 or hash_file(path)['sha256']!=item['artifact_sha256'] or not np.isfinite(item['threshold']):
                    result['status']='ARTIFACT_HASH_MISMATCH';return response
                data=path.read_bytes()
                if hashlib.sha256(data).hexdigest()!=item['artifact_sha256']:
                    result['status']='ARTIFACT_HASH_MISMATCH';return response
                models[mode]=data
            scores={}
            for mode,data in models.items():
                model=joblib.load(io.BytesIO(data))
                if model.mode!=mode or model.fit_rows!=report['models'][mode]['fit_rows']:
                    result['status']='MODEL_SCHEMA_MISMATCH';return response
                score=float(model.scores([{**window,'text':text}])[0])
                if not np.isfinite(score):raise ValueError('Invalid score')
                scores[mode]={'score':score,'threshold_exceeded':score>report['models'][mode]['threshold']}
            result.update(status='SHADOW_SCORED',models=scores,report_sha256=self.pin)
        except Exception:
            result['status']='ARTIFACT_OR_INFERENCE_UNAVAILABLE'
        return response
