# Future CERT integration

No CERT data is included. Place licensed files under ignored `ml/data/raw/`. The loader expects `file.csv`, `device.csv`, and `http.csv` with `id,date,user,pc`; `file.csv` also needs `filename,activity`, `device.csv` needs `activity`, and `http.csv` needs `url`. Adapt mappings for the actual release. Missing columns raise an explicit error. Current adapter interprets timestamps as UTC; verify the actual dataset timezone.

## CERT handoff

1. Put the licensed release under ignored `ml/data/raw/`; do not commit it.
2. Inspect its release documentation, columns, timestamp timezone, identities, and ground-truth labels. Adjust the adapter mapping deliberately if the release differs.
3. Prepare normalized events with `python -m ml.data.prepare_dataset --input ml/data/raw --output ml/data/prepared/events.jsonl`; review valid/invalid diagnostics, sample rows, and the SHA-256 fingerprint.
4. Train with `python -m ml.training.train_anomaly --dataset ml/data/prepared/events.jsonl --output ml/artifacts/anomaly/cert-candidate-v1 --real-dataset`. Normal training output is `CANDIDATE` and `NOT_EVALUATED`; `--synthetic-test` creates a non-registrable test artifact. One of the two data-kind flags is required, so an unattended command cannot silently declare its input real.
5. Evaluate the candidate against a separately held-out, labeled CERT partition using a documented time-aware split. Record sample counts, precision, recall, F1, false-positive rate, split details, and that partition's fingerprint. The current training script reports only an outlier count, which is diagnostic and must not be presented as an evaluation metric.
6. Review the evaluation and artifact metadata. Add the held-out result as `evaluation_status: REVIEWED` and an `evaluation` object containing a distinct SHA-256 `dataset_id` and metrics (`precision`, `recall`, `f1`, `false_positive_rate`, `sample_count`). This review is an intentional human step; training does not activate a model.
7. Copy the artifact beneath `ml/artifacts`, register its relative path through `POST /api/v1/models`, then intentionally activate the returned candidate ID with `POST /api/v1/models/{id}/activate`. The server rejects missing fingerprints, test artifacts, unreviewed candidates, malformed metrics, and evaluation fingerprints matching the training data.
8. Restart the backend, check `/api/v1/system/status` for `MODEL` and the expected version, then compare model-source assessments with the heuristic on the same reviewed scenario. Preserve the heuristic comparison and evaluation report for the FYP write-up.

A successful training command is not evidence of detection quality. No authentic CERT metrics are available yet. The one shared agent key, eight-hour JWT lifetime, and localhost-only demo posture remain documented prototype limits.
