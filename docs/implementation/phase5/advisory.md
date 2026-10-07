# Phase 5 — explicit shadow integration

`ml/advisory.py` provides a shared contract and Flask/FastAPI adapters. Nothing is
installed into a running application by default. The caller explicitly invokes
`attach(original_response, rule_result, completed_window, observed_at=..., ...)`.
The returned copy retains every existing response field and adds
`research_advisory`; it does not change decisions, scores, policies or thresholds.
Existing live features (`event-window-v2`) cannot satisfy the CERT contract and
return `FEATURE_SCHEMA_MISMATCH`. No live CERT prediction or detection improvement
is claimed. A separate live artifact/coverage contract is still required.

Disabled is the default; the only accepted mode is shadow. Missing windows,
incomplete channels, future/incomplete windows, invalid values, absent artifacts,
wrong schemas/software/provenance, altered artifacts and inference errors retain
rule fallback. Exceptions are represented by reason codes without exception text.
Cold-start null features use the model's training-fitted imputer; unavailable
channels cannot be substituted with zero counts. No fusion score exists: rule,
anomaly and content evidence remain separate with `UNVALIDATED_NO_FUSION` status,
so an existing PII rule is never added a second time.

The artifact directory must be deliberately chosen by trusted local application
code. Pin the SHA-256 of its `report.json` when constructing `ShadowEngine`.
Validate the pin, model digest, research-only status, ordered feature names,
software, dataset/store/answer/feature provenance and validation threshold before
unpickling a locally trained artifact. A digest pin does not make an untrusted
pickle safe. Cache by file inode/size/mtime/ctime, reject symlink ancestors and
invalidate on changes; no automatic registration/activation is implemented.

`AdvisoryStore` is a separate SQLite sidecar, with its own application ID/schema
version. It refuses an existing application database, appends idempotently by
explicit replay key and rejects conflicting replays. Inference-input digests bind
replay records even when different inputs produce the same Isolation Forest score.
Only scalar public rule fields and redacted content pattern types/counts cross
into the sidecar. Filename/hash labels remain independent; no document text,
paths, usernames, event keys or PII values enter advisory records.
Persistence failure returns a status and leaves the original response intact.

Both adapters offer explicit `install(app, authorization)` methods for additive
read-only JSON status and HTML evidence views. Flask routes are
`/research/advisory` and `/research/advisory/ui`; FastAPI routes add `/api/v1`.
Flask's callback must return the host's denied response or None; FastAPI uses the
host's existing analyst dependency. Tests verify authorization on both routes.
The HTML escapes persisted content and explains shadow status and unvalidated
combined scoring. No current routes/UI/workflows are replaced. Installation is
optional and was tested in disposable framework apps, not native deployments.

Example host wiring, after importing the existing app in its normal environment:

```python
from ml.advisory import UpstreamAdvisoryAdapter, ShadowEngine, AdvisoryStore
adapter = UpstreamAdvisoryAdapter(ShadowEngine(), AdvisoryStore('/deliberate/local/advisory.sqlite'))
adapter.install(app, existing_analyst_dependency)
# Host code may attach advisory evidence to a copy of its existing response.
# Actual live windows retain their schema and report incompatibility with CERT.
response = adapter.attach(existing_response, existing_rule_result, live_window,
                          observed_at=explicit_event_time, replay_key=stable_key)
```

Preserved Flask uses `FlaskAdvisoryAdapter` identically, with its authorization
callback. Do not import `agent.py` or launch monitors for research verification.
`ShadowEngine(enabled=True, artifact=local_run, report_sha256=pinned_digest)` is
reserved for deliberate offline CERT replay with fully observed completed windows.

Actual Phase 5 acceptance: both adapters replayed the 38 frozen Phase 3 held-out
windows; scores matched within 1e-12, repeated payloads were identical, original
payloads stayed unchanged, each sidecar contained 38 rows, and one model load was
shared across adapters. This is integration acceptance, not new quality evidence.
The constant rule fixture is explicitly not a CERT policy benchmark. Commands:

```bash
.local/phase0-venv/bin/python -B -m pytest -q tests/test_advisory.py
.local/phase0-venv/bin/python -B -m research.advisory_replay --benchmark research/local/phase3_benchmark_v1 --output research/local/phase5_replay_v1
.local/phase0-venv/bin/python -B scripts/verification/phase0_upstream_baseline.py --report docs/implementation/phase5/isolated-tests.json --log .local/phase5-isolated.log
```

Replay output refuses overwrite. Models/sidecars remain ignored. An initial
conflict test exposed that two different inputs can yield the same anomaly score;
adding the input digest fixed replay identity rather than weakening the check.
Native Windows and PostgreSQL remain unverified; all persistence tests use
isolated SQLite storage. Detailed counts appear in `verification.json`.
