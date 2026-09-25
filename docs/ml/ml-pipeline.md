# ML pipeline

There is no bundled trained model. Default behavior uses a deterministic count rule when three prior windows exist; with less history it reports `INSUFFICIENT_HISTORY`. The rule assigns 30 points per multiple above mean prior event count, capped at 100. `RULE` sensitivity detects CNIC and email patterns; `DECLARED` sensitivity uses an explicit label. Neither is an AI prediction.

`prepare_dataset.py` streams CSV to normalized JSONL. `train_anomaly.py` aggregates user/hour windows, fits IsolationForest with seed 42, saves `model.joblib` and `metadata.json`, and records a SHA-256 dataset fingerprint and holdout outlier count. That count is diagnostic only, not accuracy. Training requires either `--synthetic-test` or the explicit `--real-dataset` attestation; omitted or conflicting data-kind flags stop before training. Test artifacts are rejected for registration and inference. A configured `DATASHIELD_ANOMALY_ARTIFACT` can select an artifact without a database registry entry only after the artifact contract passes. Real CERT evaluation and quality claims remain pending the dataset.

After reviewing a genuine candidate, an admin can register and activate it with PowerShell:

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/auth/login -ContentType application/json -Body (@{username='demo.admin';password=$env:DATASHIELD_DEMO_ADMIN_PASSWORD} | ConvertTo-Json)
$headers = @{Authorization="Bearer $($login.access_token)"}
$model = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/models -Headers $headers -ContentType application/json -Body (@{artifact_name='anomaly/candidate-v1'} | ConvertTo-Json)
Invoke-RestMethod -Method Post -Uri "http://localhost:8001/api/v1/models/$($model.id)/activate" -Headers $headers
```

The feature window policy must remain at 60 minutes for this training command. Newly trained candidates are explicitly `REAL_UNVERIFIED` (meaning only that the synthetic-test switch was not used), have `evaluation_status: NOT_EVALUATED`, and cannot be activated. `dataset_id` must be a SHA-256 fingerprint. Before activation, a separately reviewed held-out evaluation must be written to the artifact metadata with its own distinct SHA-256 `dataset_id`, `evaluation_status: REVIEWED`, and numeric `precision`, `recall`, `f1`, `false_positive_rate`, and positive `sample_count`. These values must come from genuine labeled held-out data; the app does not manufacture or calculate them from IsolationForest's uncalibrated scores. Registering a candidate never activates it. Activation is an explicit admin call and fails closed if any provenance/evaluation field is absent or invalid. The Docker backend mounts `ml/artifacts` read only, so train or copy the candidate there on the host first.
