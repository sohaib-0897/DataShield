"""Document classification contract and optional reviewed artifact adapter."""
import json
import os
from pathlib import Path
from typing import Protocol

from .analysis import classify as rule_classify


class SensitivityClassifier(Protocol):
    def classify(self, document_metadata: dict, extracted_text: str) -> dict: ...


class RuleBasedSensitivityClassifier:
    def classify(self, document_metadata: dict, extracted_text: str) -> dict:
        class Document:
            metadata = {**document_metadata, "sample_text": extracted_text}
        return rule_classify(Document())


class ModelSensitivityClassifier:
    """Loads only a locally configured, reviewed scikit text pipeline."""
    def __init__(self, directory):
        import joblib
        folder = Path(directory)
        metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
        if metadata.get("model_type") != "sensitivity-text" or metadata.get("status") != "ACTIVE" or metadata.get("input_schema") != "text-v1":
            raise ValueError("Incompatible or inactive sensitivity artifact")
        self.model = joblib.load(folder / "model.joblib")
        self.version = metadata["version"]

    def classify(self, document_metadata: dict, extracted_text: str) -> dict:
        if not extracted_text.strip():
            return {"label": "unclassified", "score": 0.0, "confidence": 0.0, "source": "UNAVAILABLE", "model_version": None, "detections": []}
        probabilities = self.model.predict_proba([extracted_text[:32768]])[0]
        index = int(probabilities.argmax())
        label = str(self.model.classes_[index]).lower()
        if label not in {"public", "internal", "confidential", "restricted"}:
            raise ValueError("Artifact returned an unsupported label")
        return {"label": label, "score": {"public": 0.0, "internal": 20.0, "confidential": 70.0, "restricted": 90.0}[label],
                "confidence": float(probabilities[index]), "source": "MODEL", "model_version": self.version, "detections": []}


def classify_document(event):
    artifact = os.getenv("DATASHIELD_SENSITIVITY_ARTIFACT")
    if artifact:
        return ModelSensitivityClassifier(artifact).classify(event.metadata, str(event.metadata.get("sample_text", "")))
    return RuleBasedSensitivityClassifier().classify(event.metadata, str(event.metadata.get("sample_text", "")))
