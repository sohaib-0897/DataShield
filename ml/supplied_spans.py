"""Local, advisory supplied-span categories. Never produces sensitivity/risk labels.

Only operator-pinned, locally trained DS2 entity pipelines may be deserialized.
Both success and failure are cached until process restart; no text is persisted.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
from threading import Lock

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, model_validator

CATEGORIES = ['CODE', 'DATETIME', 'DEM', 'LOC', 'MISC', 'ORG', 'PERSON', 'QUANTITY']
VERSION = 'tab-supplied-span-ds2-v1'
TASK = 'supplied-span entity-category classification; spans are provided'
SCORE_KIND = 'uncalibrated LinearSVC decision margins; not probabilities'


class Span(BaseModel):
    model_config = ConfigDict(extra='forbid')
    start: StrictInt = Field(ge=0)
    end: StrictInt = Field(gt=0)


class SuppliedSpanRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: StrictStr = Field(min_length=1, max_length=32768)
    spans: list[Span] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def check_offsets(self):
        try:
            size = len(self.text.encode('utf-8'))
        except UnicodeEncodeError:
            raise ValueError('Text must be valid Unicode') from None
        if size > 131072:
            raise ValueError('Text byte limit exceeded')
        for span in self.spans:
            if not (span.start < span.end <= len(self.text)) or span.end-span.start > 4096:
                raise ValueError('Invalid span bounds or span size')
            if not self.text[span.start:span.end].strip():
                raise ValueError('Span must contain non-whitespace text')
        return self


class ArtifactUnavailable(RuntimeError):
    pass


def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_metadata(path):
    if path.stat().st_size > 1024**2:
        raise ValueError('Metadata size limit')
    return json.loads(path.read_text(encoding='utf-8'))


class SuppliedSpanClassifier:
    def __init__(self, directory, selection_sha256):
        import joblib
        import numpy as np
        import sklearn
        from sklearn.pipeline import FeatureUnion, Pipeline
        from sklearn.svm import LinearSVC
        from sklearn.feature_extraction.text import TfidfVectorizer

        folder = Path(directory)
        selection_path = folder/'selection.json'
        if not re.fullmatch(r'[0-9a-f]{64}', selection_sha256 or '') or file_hash(selection_path) != selection_sha256:
            raise ValueError('Operator-pinned selection digest required')
        meta = read_metadata(selection_path)
        if (meta.get('version') != VERSION or meta.get('task') != TASK
                or meta.get('status') != 'OFFLINE_RESEARCH_ONLY' or meta.get('live_activation') is not False
                or meta.get('selected_mode') != 'entity' or meta.get('score_kind') != SCORE_KIND
                or meta.get('fit_partition') != 'train' or meta.get('selection_partition') != 'validation'
                or meta.get('test_loaded') is not False):
            raise ValueError('Unsupported supplied-span artifact contract')
        software = {'python': platform.python_version(), 'sklearn': sklearn.__version__,
                    'numpy': np.__version__, 'joblib': joblib.__version__}
        if meta.get('software') != software:
            raise ValueError('Artifact software mismatch')
        contract_path = folder/'training_contract.json'
        if file_hash(contract_path) != meta['contract']['sha256']:
            raise ValueError('Training contract digest mismatch')
        contract = read_metadata(contract_path)
        if (contract.get('task') != TASK or contract.get('live_activation') is not False
                or contract.get('preparation') != meta.get('preparation') or contract.get('config') != meta.get('config')):
            raise ValueError('Training contract mismatch')
        path = folder/'entity.joblib'
        if path.stat().st_size > 64*1024**2 or file_hash(path) != meta['models']['entity']['artifact']['sha256']:
            raise ValueError('Artifact digest or size mismatch')
        # Pin is provided by the operator, not inferred from untrusted metadata.
        model = joblib.load(path)
        if (type(model) is not Pipeline or list(model.named_steps) != ['features', 'classifier']
                or type(model['features']) is not FeatureUnion or type(model['classifier']) is not LinearSVC
                or list(model.classes_) != CATEGORIES):
            raise ValueError('Unsupported pipeline or categories')
        transformers = model['features'].transformer_list
        if ([name for name, _ in transformers] != ['word', 'char']
                or any(type(value) is not TfidfVectorizer for _, value in transformers)
                or transformers[0][1].ngram_range != (1, 2) or transformers[1][1].ngram_range != (3, 5)
                or transformers[0][1].analyzer != 'word' or transformers[1][1].analyzer != 'char'):
            raise ValueError('Unsupported text features')
        self.model = model
        self.version = VERSION
        self.selection_sha256 = selection_sha256

    def classify(self, request: SuppliedSpanRequest):
        import numpy as np
        values = [request.text[s.start:s.end] for s in request.spans]
        scores = self.model.decision_function(values)
        if scores.shape != (len(values), len(CATEGORIES)) or not np.isfinite(scores).all():
            raise ArtifactUnavailable('Supplied-span model returned incompatible scores')
        return {'task': TASK, 'advisory': True, 'model_version': self.version,
                'selection_sha256': self.selection_sha256, 'score_kind': SCORE_KIND,
                'offset_unit': 'Unicode code points; start inclusive, end exclusive',
                'predictions': [{'start': s.start, 'end': s.end, 'category': CATEGORIES[int(row.argmax())],
                                 'scores': dict(zip(CATEGORIES, map(float, row)))}
                                for s, row in zip(request.spans, scores)]}


class AdvisoryService:
    """One lazy model load per process, including concurrent callers."""
    def __init__(self):
        self._lock = Lock()
        self._attempted = False
        self._classifier = None

    def get(self):
        with self._lock:
            if not self._attempted:
                self._attempted = True
                try:
                    directory = os.environ['DATASHIELD_SPAN_ARTIFACT']
                    pin = os.environ['DATASHIELD_SPAN_SELECTION_SHA256']
                    self._classifier = SuppliedSpanClassifier(directory, pin)
                except Exception:
                    # Fixed message avoids exposing artifact paths or any text.
                    self._classifier = None
            if self._classifier is None:
                raise ArtifactUnavailable('Supplied-span artifact absent or incompatible; configure and restart')
            return self._classifier


service = AdvisoryService()
