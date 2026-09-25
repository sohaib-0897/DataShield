# FYP defense: 20 questions

Answers describe the implemented repository. Default policy values can be changed by an administrator; cite the values stored with the displayed alert when discussing a particular result. See the [technical facts](technical-facts.md) and [architecture](../architecture/architecture.md).

## 1. Why FastAPI?

**Short answer:** It provides a typed API contract for agents and the React dashboard.

**Technical answer:** Pydantic validates normalized requests, FastAPI dependencies enforce authentication and roles, and OpenAPI exposes the API contract. The project is a modular monolith; choosing FastAPI does not by itself make ingestion asynchronous, distributed, or production-ready.

## 2. Why PostgreSQL?

**Short answer:** Investigation records need durable storage and relationships between events, alerts, evidence, and decisions.

**Technical answer:** PostgreSQL provides transactions, foreign keys, uniqueness constraints, indexed queries, and JSON metadata. SQLAlchemy maps those records and Alembic versions the schema. The preserved Compose volume provides persistence across container restarts; a volume is not a substitute for a verified backup.

## 3. Why is Flask still in the repository?

**Short answer:** Flask is retained for migration and historical regression coverage; FastAPI is the supported backend.

**Technical answer:** `legacy/flask/` retains the original table definitions and application history. Alembic and the explicit legacy import utility still need those definitions. The new runtime uses typed normalized event contracts. Flask was not inherently incapable of the task; keeping the historical boundary explicit avoids confusing two different generations of the API.

## 4. Why normalize events?

**Short answer:** Different telemetry sources need a common identity, timestamp, channel, and resource structure for analysis.

**Technical answer:** `EventIn` requires source event ID, user, machine, hostname, timezone-aware timestamp, channel, and event type. It normalizes timestamps to UTC and bounds metadata. The same ingestion function can then classify, aggregate, score, and persist FILE, USB, UPLOAD, NETWORK, and supported CLOUD events. The network collector does not infer an upload from a connection.

## 5. What is the difference between sensitivity and anomaly?

**Short answer:** Sensitivity concerns the information involved; behavioral analysis concerns the activity pattern.

**Technical answer:** Sensitivity uses bounded CNIC/email rules or declared labels by default. Behavioral features describe activity counts, channels, timing, and related indicators. The current fallback compares event counts against earlier windows. A sensitive document is not automatically malicious, and unusual activity is not proof of sensitive content. Separate source labels preserve that distinction.

## 6. How is risk calculated?

**Short answer:** It is a weighted composite of behavior, sensitivity, activity, channel, and prior risk.

**Technical answer:** Defaults are 0.20, 0.30, 0.20, 0.20, and 0.10 respectively. Components use a 0-100 scale; contributions are rounded and their sum is capped at 100. The historical input is half the most recent prior assessment, bounded by the scorer. Default alert threshold is 55, with severity cutoffs at 35, 65, and 85. The score is not a calibrated probability of insider misconduct.

## 7. Why use heuristics now?

**Short answer:** There is no reviewed trained behavior artifact or authentic CERT evaluation to justify a model claim.

**Technical answer:** Without a configured artifact, fewer than three prior feature windows produces `INSUFFICIENT_HISTORY`. Otherwise the count rule computes `min(100, 30 * max(0, current_count - prior_mean) / max(prior_mean, 1))`. Up to eight eligible prior windows are considered. The windows are recorded per event and are not necessarily disjoint calendar hours. The `HEURISTIC` label identifies this limitation.

## 8. Where would CERT fit?

**Short answer:** It would provide authentic source activity and ground truth for preparation and held-out evaluation.

**Technical answer:** `ml.data.prepare_dataset` maps operator-supplied CSVs to normalized JSONL; `ml.training.train_anomaly` builds candidate IsolationForest artifacts. No CERT data is bundled. Candidate provenance, a distinct held-out dataset fingerprint, reviewed labeled metrics, and artifact compatibility are required by the activation checks. Training's outlier count is not an accuracy metric. Metadata checks rely on honest human review; they do not independently certify the origin of the dataset.

## 9. How are duplicate events prevented?

**Short answer:** Retries reuse a stable source event ID that the API checks and the database makes unique.

**Technical answer:** An existing ID returns its stored event/alert association with `duplicate: true`. Agent retries resend the same payload. The unique constraint also protects concurrent ingestion. Separate collector callbacks with different IDs are separate events; the filesystem agent's short debounce helps reduce repeated callbacks, but the system does not promise global exactly-once delivery or a durable offline queue.

## 10. How does RBAC work?

**Short answer:** The API checks active users and their ADMIN, ANALYST, or VIEWER role.

**Technical answer:** Authenticated active users can read investigations and reports. ADMIN and ANALYST may record decisions and export reports; administrative functions such as policy changes, user/model management, and the full Audit log require ADMIN. The UI hides restricted controls, but server dependencies enforce the permission. The synthetic demo uses ADMIN to show the complete workflow.

## 11. How do agents authenticate?

**Short answer:** Agents send a shared key in `X-Agent-Key`, separate from user JWT sessions.

**Technical answer:** The server compares it with the configured agent key using a constant-time comparison. This prototype has no per-device provisioning, revocation, or key rotation workflow. A shared key does not independently prove a claimed endpoint identity. Use protected transport outside localhost; per-endpoint credentials are future hardening work.

## 12. How does USB monitoring work?

**Short answer:** WMI observes volume arrival/removal and Watchdog observes files on mounted drives.

**Technical answer:** `agents.usb` subscribes to `Win32_VolumeChangeEvent` and starts or stops drive watchers. The filesystem handler uses `GetDriveTypeW` to classify created/moved files on removable drives as `USB_FILE_TRANSFER`. This is destination observation, not proof of a source-to-destination copy. Physical USB validation was not recorded; the synthetic scenario validates the pipeline only.

## 13. Can DataShield block HTTPS uploads?

**Short answer:** Only a cooperating client can enforce its upload approval response; arbitrary browser HTTPS uploads are not intercepted.

**Technical answer:** `agents.upload.request_approval` submits an upload attempt and polls the decision API. The caller must transfer only when permitted. Below-threshold events can be policy auto-allowed; escalated requests await an analyst, and polling may time out. The psutil network agent observes browser TCP metadata on ports 80/443, not encrypted payloads or proven file transfers.

## 14. Can it reverse a file copy?

**Short answer:** No. It records and assesses observed operations.

**Technical answer:** Watchdog notifications describe operations that have occurred. An analyst BLOCK on an alert records a decision but cannot roll back a completed file copy. `RESOLVE` changes the investigation state; it is not an enforcement response to upload callers. Kernel enforcement or transactional file rollback is outside the implemented design.

## 15. What happens if a model is unavailable?

**Short answer:** The response reports the actual source and preserves the distinction between a failed artifact and the normal heuristic path.

**Technical answer:** With no behavior artifact configured, history determines `HEURISTIC` or `INSUFFICIENT_HISTORY`. A configured behavior artifact that cannot load or fails compatibility/evaluation checks yields `UNAVAILABLE` with a zero behavior component; other components still contribute. A configured sensitivity artifact failure falls back to rule classification with a recorded fallback reason. Operators must not present degraded analysis as trained-model coverage.

## 16. How is sensitive information protected?

**Short answer:** Scanned text is bounded and discarded; matched evidence is masked before storage.

**Technical answer:** Event metadata is allowlisted and CNIC/email detections retain type, count, and masked examples. The active API does not serve arbitrary file previews. Masking does not anonymize the entire event: resource identifiers, filenames, destinations, and decision notes can still contain private information. Screenshots need a separate privacy review, and non-local transport requires TLS. Passwords use Argon2 hashes; JWTs are signed and expire after eight hours, with no refresh or individual-token revocation.

## 17. How is persistence verified?

**Short answer:** PostgreSQL stores the records, and prior validation confirmed that events, decisions, and audit rows survived restarts.

**Technical answer:** SQLAlchemy transactions persist the connected records; Alembic maintains schema history at `9e20ab47c132`. The named PostgreSQL volume outlives container restarts. Prior restart verification is recorded in the validation checklist; it was not repeated during this documentation pass. Automated isolated database tests and CI PostgreSQL migration checks complement the live test but do not replace backup/restore verification.

## 18. What are the main prototype limitations?

**Short answer:** Analysis and enforcement have explicit scope, and deployment controls still need hardening.

**Technical answer:** Current behavior is heuristic, authentic CERT evaluation is pending, and no detection-accuracy claim is made. There is no arbitrary HTTPS interception or rollback of completed filesystem actions. Agents share a key, JWTs have no refresh/revocation, retries have no durable offline spool, and physical USB validation is unrecorded. Known React Router v6 advisories are documented. These are deployment and evaluation constraints, not hidden completed features.

## 19. How would it scale?

**Short answer:** The current design supports a measured local prototype workload; larger-scale capacity is unproven.

**Technical answer:** Indexed filters and pagination support retrieval, but ingestion performs classification, feature queries, and scoring in the application request path. A 10,000-alert local benchmark measures specific queries, not fleet ingestion capacity or a throughput guarantee. Future work would profile concurrent ingestion, connection use, historical window queries, and retention before introducing queues or separate workers. Those changes are proposals, not current capabilities.

## 20. What would you change for production?

**Short answer:** Strengthen identity, operations, transport, evaluation, and endpoint delivery before expanding functionality.

**Technical answer:** Priorities include per-endpoint credentials, rotation and revocation, a reviewed session lifecycle, TLS, access/retention policies, recoverable backups, dependency remediation, and durable agent delivery. Validate physical devices and evaluate genuine labeled data for false positives and missed detections. Production enforcement would need explicit endpoint/client integration and a separate security review. No production readiness or enterprise-scale guarantee is claimed.
