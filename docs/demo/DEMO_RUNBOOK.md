# DataShield demonstration from this checkout

Verified on Linux on 2026-10-09, from `feat/cert-ml-nlp` source `9abe174` plus
the demo helpers in this commit. Read the [verification receipt](verification.json).
The existing implementation memory and latest B2, DS3 and NLP follow-up reports
were read. Existing uncommitted implementation/status/report edits were preserved.

## Preparation and boundaries

All commands below run from the literal trailing-tilde repository directory:

```bash
cd '/home/sohaib/Insider_Threat_Test_Dataset/DataShield~'
.local/phase0-venv/bin/python -B scripts/demo/showcase.py --help
```

The compatible environment and dependencies already exist here. Use this Python,
not an arbitrary system interpreter: the supplied-span loader requires Python
3.14.4, scikit-learn 1.9.1, NumPy 2.5.3 and joblib 1.6.0. Frontend dependencies
are already in `frontend/node_modules`; no install or model download is required.

The verified disposable session is `.local/demo/showcase/`. To prepare it only
if absent:

```bash
if [ ! -f .local/demo/showcase/config.json ]; then
  .local/phase0-venv/bin/python -B scripts/demo/showcase.py prepare
fi
```

Preparation creates a **new SQLite demo database**, its schema, generated admin
credentials, seven clearly synthetic pipeline events and two rule alerts. It
refuses an existing session; it never resets or reseeds one. For a fresh independent
session use `--session rehearsal2 prepare`, and pass `--session rehearsal2` to
each subsequent helper. Stop existing demo servers before reusing the same ports.
The seed helper prints its old port 3001; this runbook's dashboard is **3101**.

Each helper loads only its session configuration before importing the application.
The configuration explicitly clears anomaly/sensitivity artifact settings, points
the runtime registry at an unused session directory, and enables
`DATASHIELD_SPAN_ADVISORY_ENABLED=true` **only for the disposable demo process**.
`DATASHIELD_SPAN_ARTIFACT` and its selection pin reference the unchanged local DS2
artifact. Live `.env`, PostgreSQL/SQLite stores, passwords, policies, registry,
model files and enforcement code are untouched. No model is registered/activated.
The supplied-span flag adds category advice; it cannot change rule decisions.

Generated credentials/configuration, browser captures, builds and databases remain
ignored under `.local/`; replay outputs remain under ignored `research/local/demo/`.
Read the generated local login privately, before presenting:

```bash
.local/phase0-venv/bin/python -B scripts/demo/showcase.py credentials
```

## 1. Start the dashboard

Terminal A, from repository root:

```bash
.local/phase0-venv/bin/python -B scripts/demo/showcase.py backend
```

Terminal B, from repository root:

```bash
.local/phase0-venv/bin/python -B scripts/demo/showcase.py frontend
```

The latter builds the existing React app into the session's `frontend-build/` on
first startup, then serves it on loopback with SPA route fallback. Subsequent
starts reuse that build. This avoids the existing CRA development-server
`allowedHosts[0]` startup error without modifying frontend configuration or
disabling host checks. The build fixes its API URL to `http://127.0.0.1:8100`.

```bash
curl --fail --silent http://127.0.0.1:8100/health
curl --fail --silent http://127.0.0.1:8100/ready
```

Expected: `{"status":"ok"}` and `{"status":"ready"}`. Open
**http://localhost:3101/login**, log in as `demo.admin` with the generated password.
Use this exact frontend hostname, matching the isolated CORS origin.

| URL | Show | Expected |
|---|---|---|
| `http://localhost:3101/` | Security overview | At least seven synthetic events and two alerts |
| `http://localhost:3101/alerts` | Investigate a seeded USB/upload alert | `RULE`, `HEURISTIC`, weighted risk and masked detections |
| `http://localhost:3101/users` | Select `synthetic.employee` | Persisted activity, channels and risk timeline |
| `http://localhost:3101/reports` | Reports | Actual demo event/alert aggregates |
| `http://localhost:3101/system` | System status | Rule `patterns-v1`, behavior `HEURISTIC`, production model unavailable |
| `http://localhost:3101/policies` | Existing defaults | Threshold 55; view without saving |
| `http://127.0.0.1:8100/docs` | API documentation | Actual FastAPI routes; authenticated calls require credentials |

**Say:** “These alerts passed through the application’s real rule and risk
pipeline. Their input events are synthetic. The dashboard distinguishes pattern
rules from behavioral heuristics; the production anomaly model is unavailable.”

Do not run `reset_demo.ps1`, seed against a live DB, activate a model, save a
policy, or click BLOCK as part of this tour. These are unnecessary for this demo.

## 2. Native monitoring with disposable fixture files

Terminal C:

```bash
.local/phase0-venv/bin/python -B scripts/demo/showcase.py monitor
```

Expected: `Monitoring .../.local/demo/showcase/fixtures`. This is the existing
`agents.filesystem.main()` collector, limited to this folder and `.txt` files.
It sends real agent-authenticated `POST /api/v1/events` and heartbeats to the
isolated backend. It does not scan home folders or physical USB devices.

Terminal D:

```bash
.local/phase0-venv/bin/python -B scripts/demo/showcase.py trigger
```

Expected: `Moved disposable fixture into .txt: synthetic-....txt`. The helper
writes an inert CNIC-shaped example to a `.pending` file and renames it to `.txt`.
The collector logs `type=moved`, an event ID and normally `alert=None`. The
persisted event is `FILE_MOVE`; the rule document classification is
`restricted`, score 90. A fresh monitoring identity has insufficient behavioral
history; its first move risk was **36**, below the unchanged alert threshold 55.
An alert is not required for collection to work. Show the monitor user under
User activity and its FILE timeline; reload the view after delivery.

**Known collector limitation:** with installed Watchdog 6.0.0, create/modify/delete
callbacks have an empty `dest_path`. The current handler chooses that path and
ignores those callbacks. A native move has a real destination and works. This
demo uses that existing supported path; no live collector fix or general coverage
claim is made. Native Linux inotify, the move, sampling, authentication, ingestion,
masked metadata and stored rule assessment were actually verified.

**Say:** “This file move was observed by Linux inotify and delivered by the real
collector. Pattern rules recognize the synthetic identifier. Collection and
classification can succeed without crossing the alert threshold.”

Stop Terminal C with Ctrl+C before the automated verification below, to avoid
two observers watching the same fixture.

## 3. CERT historical replay in separate research storage

Use a new output directory on every run. This invokes an existing research CLI;
it does not import rows into the dashboard, retrain models or start monitors.

```bash
mkdir -p research/local/demo
DS_REPLAY_BASE=$(mktemp -d research/local/demo/replay-XXXXXX)
.local/phase0-venv/bin/python -B -m research.advisory_replay \
  --benchmark research/local/phase3_benchmark_v1 \
  --output "$DS_REPLAY_BASE/cert"
```

Expected: both `preserved_flask` and `upstream_fastapi` checks report
`windows: 38`, `available: 38`, `fallbacks: 0`, `frozen_scores_equal: true`,
`repeated_payload_equal: true`, `original_payload_preserved: true`,
`persisted_rows: 38`; `artifact_loads: 1`, `automated_blocking: false`.
Two separate SQLite advisory sidecars and `report.json` appear inside the new
output. The genuine January CERT test prefix has **zero positives**: this proves
replay/serialization/idempotency, not detection quality. The preserved rule
payload is explicitly a replay fixture, not a CERT application policy.

Optional, already verified: first/last eligible June known-user windows through
the frozen numeric, text and combined models:

```bash
.local/phase0-venv/bin/python -B -m research.nlp_replay \
  --prepared research/local/nlp_june_stream.sqlite \
  --benchmark research/local/nlp_known_users_v1 \
  --report "$DS_REPLAY_BASE/nlp-boundaries.json"
```

Expected: two observations, three models per observation,
`frozen_score_match_1e_12: true`, `original_rules_preserved: true`,
`automated_blocking: false`. The prepared SQLite is opened read-only; only temporary
cohort tables and a new report are written. This checks six boundary scores,
not the whole held-out set. No archive rescan, ingestion or training is needed.

**Say:** “These are frozen historical CERT windows, scored offline. The sidecars
are separate research storage. Models reproduce their saved scores and preserve
the rule response; their scores are not calibrated probabilities or live blocks.”

## 4. Supplied-span NLP with the actual artifact

```bash
.local/phase0-venv/bin/python -B scripts/demo/showcase.py spans --http
```

The helper logs in using the isolated credentials and calls the actual authenticated
`POST http://127.0.0.1:8100/api/v1/advisory/supplied-spans`. ADMIN/ANALYST access
is required. There is no supplied-span form in the current dashboard; show this
terminal response. To demonstrate the same local model without HTTP:

```bash
.local/phase0-venv/bin/python -B scripts/demo/showcase.py spans
```

Actual request (also saved as `.local/demo/showcase/spans.json`):

```json
{"text":"Alice visited London on 12 March 2020.","spans":[{"start":0,"end":5},{"start":14,"end":20},{"start":24,"end":37}]}
```

| Supplied slice | Start | Exclusive end | Verified prediction |
|---|---:|---:|---|
| `Alice` | 0 | 5 | PERSON |
| `London` | 14 | 20 | LOC |
| `12 March 2020` | 24 | 37 | DATETIME |

Offsets count **Unicode code points**, not UTF-8 bytes or JavaScript UTF-16 units.
Expected response: `advisory: true`, `model_version: tab-supplied-span-ds2-v1`,
the three categories above, and eight raw LinearSVC margins per span. Even a
winning margin may be negative; these are not probabilities/confidence scores.

Actual trusted local artifact:
`research/local/document_sensitivity/ds2_models_v2/entity.joblib`
(TF-IDF word/character features + LinearSVC; entity-only selected on validation).
Model SHA-256:
`23a14f549c57ef866f42ed6549c90e9c55483cbf3bea6764bf626e73c492f8c1`.
Operator-pinned `selection.json` SHA-256:
`f820f6eb6c0656b0aad22407cf75665d2deeaf20b95cbc679b075a81604b7477`.
The loader verifies the pin, model/training-contract hashes and exact software
versions. Missing/incompatible artifacts produce HTTP 503; disabled advice
produces 404; invalid offsets produce 422. Failed loads cache until restart.

**Say:** “I supplied these boundaries myself. The trained classifier assigns
entity categories to those slices; it does not discover spans or decide whether
the whole document is confidential. Advice creates no events, alerts or blocks.”

## 5. Measured evaluation, with populations kept separate

```bash
.local/phase0-venv/bin/python -B scripts/demo/showcase.py results
```

This reads existing committed aggregate JSON reports; it does not rerun evaluation.
All values below are fractions.

| Evaluation | Method | Precision | Recall | F1 | Average precision |
|---|---|---:|---:|---:|---:|
| Original CERT, 11,753 test windows / 8 positives | Isolation Forest | .002063 | .375 | .004104 | .003097 |
| Separate known-user CERT, 10,553 / 8 | Numeric | .002198 | .125 | .004320 | .007826 |
| Same known-user population | Text | .500000 | .125 | .200000 | .154422 |
| Same known-user population | Combined | .074074 | .250 | .114286 | .167069 |

TAB supplied-span classification: **6,713 test spans in 127 legal-domain documents**;
selected entity-only macro F1 **.776293**, micro F1 **.885595**. Bounded context
macro/micro F1 **.737904/.878147**; majority baseline **.068135/.374646**.
These are conditional on supplied reviewed spans, not automatic detection or
organizational document sensitivity.

Text's .50 precision means **one true and one false alert**, with seven missed
positives. Eight positives constrain all CERT claims. The original strict
unseen-user text held-outs are empty; quality is unavailable under that objective.
Do not compare the two different CERT populations as an improvement experiment.

Latest B2 structured execution processed 390 documents / 2,231,093 characters
and returned zero candidates. Independent detection P/R/F1 and policy sensitivity
remain unavailable: exhaustive natural annotations, contextual detector artifact,
owner-approved policy/context and independent sensitivity labels are missing.
The zero cross-ontology boundary diagnostic is not four-kind recall or proof
that documents are safe. Extraction and rule evidence exist; learned whole-document
sensitivity is unfinished. No `NORMAL/HIGH/CRITICAL` model claim is supported.

Sources: [original CERT](../implementation/phase6/evaluation.md),
[known-user follow-up](../implementation/nlp-followup/report.md),
[DS3 supplied-span diagnostics](../implementation/document-sensitivity/ds3-report.md),
[latest B2 limitations](../implementation/phase-b2/report.md).

**Say:** “The numbers are measured, but the populations and tasks differ. Historical
behavior results are limited by eight positives. Supplied-span F1 describes legal
entity categories. Independent document sensitivity has not been established.”

## Repeat verification and manual steps

With isolated backend/frontend running and Terminal C's monitor stopped:

```bash
.local/phase0-venv/bin/python -B scripts/demo/showcase.py verify-http
node scripts/demo/check_dashboard.cjs showcase
```

The first performs actual HTTP login/authentication rejection, seeded alert evidence,
supplied-span success/invalid offsets/no event-or-alert side effects, and a bounded
native Observer → unchanged Handler/send → authenticated HTTP → stored FILE_MOVE
check. It records unchanged policies and an empty model registry. The browser tour
checks overview, investigation, reports, status, activity, policies and audit with
zero API/page errors, without saving a policy or recording a decision.
Chrome exists here at `/opt/google/chrome/chrome`; elsewhere set
`DATASHIELD_DEMO_CHROME` to an installed compatible Chrome executable.

`showcase.py verify` is also available as an **explicit Python handler** check;
it authenticates via the real functions and uses real inotify, replacing only HTTP
delivery. Its receipt explicitly says HTTP/browser are not tested by that command.

Verified receipts/capture:
`.local/demo/showcase/{http-verification.json,browser-verification.json,verification.json,dashboard.png}`;
research receipts: `research/local/demo/cert-replay-showcase/report.json`,
`nlp-boundary-showcase.json`, `frozen-preservation.json`.
The public [verification receipt](verification.json) contains only aggregate facts.

Manual steps remaining: start the two demo services after stopping them; privately
retrieve the generated password, open the browser and perform the narrated tour.
Stop demo processes with Ctrl+C; retain the disposable outputs. Ports 8100/3101
must be free. No teardown removes data or touches a live service.

Unavailable/unverified here: Windows WMI USB insertion/removal and removable-drive
transfer detection, native legacy Windows interception, and physical devices.
Network collection is browser connection metadata, not proof of upload; it was
not started against real processes. `agents.upload` requires a cooperating upload
client, not universal browser interception. This SQLite demo does not verify a
PostgreSQL deployment, Docker or real endpoint blocking. Earlier socket restrictions
blocked HTTP/browser startup; after access was restored, the HTTP and browser
checks above passed. CRA's raw development-server startup remains blocked by its
existing allowed-host issue; the verified production-build server is used here.

## 3–4 minute narration (about 460 words; prepare servers first)

**0:00–0:45 — dashboard.**
“DataShield brings endpoint telemetry, rule classification and analyst review
into one dashboard. This instance uses a disposable database and synthetic events,
so the demonstration does not change live records. Here are the overview and
alerts. Opening an alert shows identity, channel, weighted risk contributions
and masked evidence. The analysis sources matter: sensitivity comes from pattern
rules, and behavior comes from a deterministic heuristic. A production anomaly
model is not active. These are the application's existing rules and thresholds.”

**0:45–1:20 — monitoring.**
“Now I will move a disposable text file into the monitored fixture folder. Linux
inotify observes the move, and the real agent authenticates to the isolated API.
The synthetic identifier is classified by the current pattern rule. The event
appears in the user timeline. A file observation need not become an alert: this
fresh user has insufficient behavioral history, and its initial risk is below
the existing threshold. This demonstration verifies the move path; create and
modify coverage has a known Watchdog compatibility issue. Windows USB monitoring
needs separate Windows and device testing.”

**1:20–2:00 — historical ML.**
“This terminal now replays frozen CERT historical windows. They are offline
research inputs, stored separately from the dashboard. Both application advisory
adapters reproduce the saved model scores, retain the rule response and write
separate sidecars. Repeating an observation is idempotent. The small January
replay has no positive examples, so it demonstrates compatibility rather than
detection quality. The June boundary check additionally reproduces numeric,
text and combined scores. None of these research models changes a live decision
or enables model-driven blocking.”

**2:00–2:40 — supplied-span NLP.**
“For this example I explicitly supplied Alice, London and the date as three spans.
The authenticated advisory API loads the actual pinned TF-IDF and LinearSVC
artifact, and returns PERSON, LOC and DATETIME. The offsets count Unicode
characters, with an exclusive end. The scores are uncalibrated margins. The
classifier requires the boundaries; it does not automatically find every entity
or label a whole document confidential. It creates no alerts or enforcement
decisions. Category classification is a separate task from both behavioral ML
and document sensitivity.”

**2:40–3:35 — evidence and unfinished work.**
“The evaluation view reads frozen measured reports. In the separate known-user
CERT test, text precision is one half, but that represents just one true alert
and one false alert, while missing seven positives. Combined detects two of
eight. The original unseen-user text held-outs are empty. On reviewed legal
supplied spans, the selected classifier has macro F1 around point seven seven six.
That is not document-sensitivity accuracy. Independent natural detection labels,
an automatic contextual detector and owner-approved organizational sensitivity
labels are still missing. The demonstrated boundaries are live rules, offline
historical ML, and supplied-span category advice; whole-document learned
sensitivity and broad Windows enforcement remain unfinished or unverified.”
