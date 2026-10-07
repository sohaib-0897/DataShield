"""Opt-in shadow inference. This contract cannot supply enforcement decisions.

Only load locally trained joblib files with an explicitly pinned report digest.
CERT models require CERT coverage; no live feature conversion is implied.
"""
from copy import deepcopy
from datetime import datetime
import hashlib
import html
import json
import math
from pathlib import Path
import re
import sqlite3
from threading import RLock

from ml.features.windows import CHANNELS, FEATURE_NAMES, VERSION

CONTRACT = 'datashield-advisory-v1'
MODEL_VERSION = 'cert-behavior-research-v1'
HEX = re.compile(r'[0-9a-f]{64}')


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            value.update(block)
    return value.hexdigest()


class ShadowEngine:
    def __init__(self, *, enabled=False, artifact=None, report_sha256=None, mode='shadow'):
        if mode != 'shadow':
            raise ValueError('Only shadow mode is supported')
        self.enabled = enabled
        self.artifact = Path(artifact) if artifact else None
        self.report_sha256 = report_sha256
        self._cached = None
        self._signature = None
        self._lock = RLock()
        self.loads = 0

    def _load(self):
        import joblib
        import sklearn
        import numpy
        if self.artifact is None:
            raise FileNotFoundError('No artifact')
        report_path = self.artifact / 'report.json'
        model_path = self.artifact / 'isolation_forest.joblib'
        if any(p.is_symlink() for p in (self.artifact, *self.artifact.parents, report_path, model_path)):
            raise ValueError('Symlink artifact')
        if report_path.stat().st_size > 1024**2 or model_path.stat().st_size > 64 * 1024**2:
            raise ValueError('Artifact size bound')
        signature = tuple((p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns)
                          for p in (report_path, model_path))
        if self._cached is not None and signature == self._signature:
            return self._cached
        self._cached = self._signature = None
        if not HEX.fullmatch(str(self.report_sha256)) or digest(report_path) != self.report_sha256:
            raise ValueError('Untrusted report')
        report = json.loads(report_path.read_text())
        if (report['version'] != MODEL_VERSION or report['status'] != 'RESEARCH_ONLY_NOT_REGISTRABLE'
                or report['feature_version'] != VERSION or tuple(report['feature_names']) != FEATURE_NAMES
                or report['preprocessing_fit_partition'] != 'train'):
            raise ValueError('Incompatible contract')
        for key in ('dataset_sha256', 'store_sha256', 'answers_sha256', 'feature_artifact_sha256'):
            if not HEX.fullmatch(str(report.get(key))):
                raise ValueError('Missing provenance')
        if report['software']['sklearn'] != sklearn.__version__ or report['software']['numpy'] != numpy.__version__:
            raise ValueError('Incompatible software')
        item = report['models']['isolation_forest']
        if (item['threshold_partition'] != 'validation' or not math.isfinite(item['threshold'])
                or item['score_kind'] != 'negative_score_samples_not_probability'
                or not HEX.fullmatch(str(item['artifact_sha256']))
                or digest(model_path) != item['artifact_sha256']):
            raise ValueError('Invalid model provenance/threshold')
        # The digest pin is a trust boundary, not a sandbox for arbitrary pickle.
        model = joblib.load(model_path)
        if model.n_features_in_ != len(FEATURE_NAMES):
            raise ValueError('Incompatible model shape')
        after = tuple((p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns)
                      for p in (report_path, model_path))
        if signature != after:
            raise ValueError('Artifact changed during load')
        self._signature, self._cached = signature, (model, report)
        self.loads += 1
        return self._cached

    def observe(self, rule, window=None, *, content=None, observed_at):
        """Use replay's explicit timestamp; never read wall clock or enforcement state."""
        datetime.fromisoformat(observed_at)
        # Only public, scalar rule fields cross into persistence/UI.
        rule_signal = {key: rule[key] for key in ('score', 'severity', 'rule_version', 'scoring_version')
                       if key in rule and isinstance(rule[key], (str, int, float, type(None)))}
        anomaly = {'status': 'DISABLED', 'score': None, 'alert': None, 'model_version': None}
        if self.enabled:
            try:
                if window is None:
                    anomaly['status'] = 'FEATURES_UNAVAILABLE'
                elif window.get('feature_version') != VERSION:
                    anomaly['status'] = 'FEATURE_SCHEMA_MISMATCH'
                elif (window.get('fully_observed') is not True or
                      any(window['features'].get(f'{c.lower()}_available') != 1 for c in CHANNELS)):
                    anomaly['status'] = 'FEATURES_UNAVAILABLE'
                else:
                    start, end = map(datetime.fromisoformat, (window['start'], window['end']))
                    when = datetime.fromisoformat(observed_at)
                    if start.tzinfo or end.tzinfo or when.tzinfo or (end-start).total_seconds() != 3600 or end > when:
                        raise ValueError('Incomplete/invalid release-local window')
                    values = [window['features'][key] for key in FEATURE_NAMES]
                    if any(v is not None and (isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v)) for v in values):
                        raise ValueError('Invalid numeric feature')
                    import numpy as np
                    with self._lock:
                        model, report = self._load()
                        score = float(-model.score_samples(np.array([[np.nan if v is None else v for v in values]]))[0])
                    if not math.isfinite(score):
                        raise ValueError('Nonfinite score')
                    item = report['models']['isolation_forest']
                    anomaly = {'status': 'AVAILABLE', 'score': score, 'alert': score > item['threshold'],
                               'threshold': item['threshold'], 'threshold_partition': 'validation',
                               'score_kind': item['score_kind'], 'model_version': report['version'],
                               'artifact_sha256': item['artifact_sha256'], 'report_sha256': self.report_sha256,
                               'dataset_sha256': report['dataset_sha256'], 'answers_sha256': report['answers_sha256'],
                               'feature_artifact_sha256': report['feature_artifact_sha256']}
            except FileNotFoundError:
                anomaly['status'] = 'ARTIFACT_UNAVAILABLE'
            except Exception:
                # No exception messages: parsers/model failures can contain private data.
                anomaly['status'] = 'MODEL_OR_INPUT_INVALID'
        safe_content = {'status': 'UNAVAILABLE', 'model_status': 'UNAVAILABLE_NO_LABELED_CORPUS'}
        if content is not None and content.get('version') == 'document-extraction-evidence-v1':
            safe_content.update(status=content.get('extraction_status', 'UNAVAILABLE'),
                                available=content.get('content_available') is True,
                                truncated=content.get('extraction_truncated') is True,
                                evidence=[{'type': e['type'], 'count': e['count']}
                                          for e in content.get('pii_evidence', [])
                                          if e.get('type') in {'cnic_like', 'email_address'} and isinstance(e.get('count'), int)],
                                source='RULE_PATTERNS',
                                filename_label=content.get('filename_label') if content.get('filename_label') in {'public', 'internal', 'confidential', 'restricted'} else None,
                                hash_label=content.get('hash_label') if content.get('hash_label') in {'public', 'internal', 'confidential', 'restricted'} else None)
        return {'contract_version': CONTRACT, 'mode': 'shadow', 'observed_at': observed_at,
                'feature_version': window.get('feature_version') if window else None,
                'window_sha256': hashlib.sha256(json.dumps({k: window.get(k) for k in ('start', 'end', 'feature_version', 'features', 'fully_observed')}, sort_keys=True).encode()).hexdigest() if window else None,
                'rule': rule_signal, 'anomaly': anomaly, 'content': safe_content,
                'combined': {'status': 'UNVALIDATED_NO_FUSION', 'score': None,
                             'explanation': 'Separate evidence only; content rules are not counted again.'},
                'enforcement': 'EXISTING_DETERMINISTIC_POLICY', 'automated_blocking': False,
                'fallback': anomaly['status'] != 'AVAILABLE'}


class AdvisoryStore:
    """Separate append-only SQLite sidecar. Never migrate an existing app database."""
    APP_ID = 0x44534144

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if any(p.is_symlink() for p in (self.path, *self.path.parents)):
            raise ValueError('Unsafe sidecar path')
        with sqlite3.connect(self.path) as db:
            app_id = db.execute('PRAGMA application_id').fetchone()[0]
            tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if tables and (app_id != self.APP_ID or db.execute('PRAGMA user_version').fetchone()[0] != 1):
                raise ValueError('Refuse existing/incompatible database')
            db.execute(f'PRAGMA application_id={self.APP_ID}')
            db.execute('PRAGMA user_version=1')
            db.execute('CREATE TABLE IF NOT EXISTS advisory (key TEXT PRIMARY KEY, payload TEXT NOT NULL)')

    def append(self, key, result):
        if result.get('contract_version') != CONTRACT:
            raise ValueError('Incompatible observation')
        payload = json.dumps(result, sort_keys=True, allow_nan=False)
        if len(payload.encode()) > 16384 or not key or len(key) > 128:
            raise ValueError('Sidecar bound')
        with sqlite3.connect(self.path) as db:
            previous = db.execute('SELECT payload FROM advisory WHERE key=?', (key,)).fetchone()
            if previous and previous[0] != payload:
                raise ValueError('Conflicting replay key')
            db.execute('INSERT OR IGNORE INTO advisory VALUES (?,?)', (key, payload))

    def recent(self, limit=100):
        if not 1 <= limit <= 100:
            raise ValueError('Bounded read required')
        with sqlite3.connect(f'{self.path.absolute().as_uri()}?mode=ro', uri=True) as db:
            return [json.loads(row[0]) for row in db.execute('SELECT payload FROM advisory ORDER BY rowid DESC LIMIT ?', (limit,))]


class AdvisoryAdapter:
    application = 'shared'

    def __init__(self, engine=None, store=None):
        self.engine = engine or ShadowEngine()
        self.store = store

    def attach(self, original, rule, window=None, *, observed_at, content=None, replay_key=None):
        result = self.engine.observe(rule, window, observed_at=observed_at, content=content)
        result['application'] = self.application
        result['persistence_status'] = 'DISABLED'
        if self.store is not None and replay_key is not None:
            try:
                # Status is deterministic so repeated writes remain idempotent.
                result['persistence_status'] = 'AVAILABLE'
                self.store.append(replay_key, result)
            except Exception:
                result['persistence_status'] = 'UNAVAILABLE'
        response = deepcopy(original)
        if 'research_advisory' in response:
            raise ValueError('Existing advisory field must not be overwritten')
        response['research_advisory'] = result
        return response

    def status(self):
        try:
            results = self.store.recent() if self.store else []
            persistence = 'AVAILABLE' if self.store else 'DISABLED'
        except Exception:
            results, persistence = [], 'UNAVAILABLE'
        return {'contract_version': CONTRACT, 'application': self.application, 'mode': 'shadow',
                'enabled': self.engine.enabled, 'automated_blocking': False,
                'results': results, 'persistence_status': persistence}

    def render(self):
        return ('<!doctype html><meta charset="utf-8"><title>DataShield advisory</title>'
                '<h1>Research advisory</h1><p>Shadow evidence. Existing policies determine enforcement. '
                'Anomaly scores are not probabilities; combined scoring is unvalidated.</p><pre>'
                + html.escape(json.dumps(self.status(), indent=2)) + '</pre>')


class FlaskAdvisoryAdapter(AdvisoryAdapter):
    application = 'preserved_flask'

    def install(self, app, authorize):
        """Explicit installation; caller supplies existing analyst authorization."""
        from flask import jsonify
        def status():
            denied = authorize()
            if denied is not None:
                return denied
            return jsonify(self.status())
        app.add_url_rule('/research/advisory', 'research_advisory', status, methods=['GET'])
        def view():
            denied = authorize()
            return denied if denied is not None else self.render()
        app.add_url_rule('/research/advisory/ui', 'research_advisory_ui', view, methods=['GET'])


class UpstreamAdvisoryAdapter(AdvisoryAdapter):
    application = 'upstream_fastapi'

    def install(self, app, analyst_dependency):
        from fastapi import Depends
        @app.get('/api/v1/research/advisory', dependencies=[Depends(analyst_dependency)])
        def status():
            return self.status()

        from fastapi.responses import HTMLResponse
        @app.get('/api/v1/research/advisory/ui', dependencies=[Depends(analyst_dependency)], response_class=HTMLResponse)
        def view():
            return self.render()
