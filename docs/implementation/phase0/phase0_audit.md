# Phase 0 audit and regression baseline — 2026-10-07

Historical initial inspection, before the user supplied the `DataShield~` checkout.
Current checkout comparison/status and runnable repository commands are in `audit.md`
alongside this file. The supplied-source findings below still apply; the initial
checkout/network statements describe that earlier snapshot.

**Status: blocked, with independent audit and available regression checks finished.**
The user confirmed `/home/sohaib/Downloads/AI-DLP-Agent` contains the implementation to continue.
It has no Git metadata. The requested clone into
`/home/sohaib/Insider_Threat_Test_Dataset/DataShield` failed with
`Could not resolve host: github.com`. Consequently remote comparison, source reconciliation,
branch creation, commit, push, and remote checkpoint verification have not happened.
These documents and checks are currently in the parent writable workspace and must be
transferred selectively into the real repository after cloning. Production files are unchanged.

## Inspection and preservation

No AGENTS.md was found in the current workspace, its ancestors, the downloaded source,
or the searched Downloads/Documents/Desktop trees. Re-check the real checkout after cloning.
No FYP report was found in those searched locations. No project test suite, requirements
file, or pyproject.toml was found. `check_db.py` and `check_transfers.py` read live telemetry;
they are inspection scripts and were not run as regression tests.

Before/after SHA-256, size, and modification-time observations match for 30 source/live files.
The manifest covers top-level Python/HTML and all existing `data/` files, including DB,
policy, CSVs, and monitor logs. No live event or policy contents are included in these documents.
Archive preservation uses unchanged size/mtime/inode observations, not full archive hashes;
full provenance hashing is deferred to Phase 1. No archives were extracted or moved.
See `phase0_preservation_before.json` and `phase0_preservation.json`.

## Architecture and platform assumptions

| Component | Implemented behavior and preservation constraint |
|---|---|
| `agent.py` | Watchdog created/modified/deleted/moved file events, filename sensitivity, activity logging. Starts DB initialization, observer, and busy loop at import; never import in ingestion/training/tests. |
| `windows_monitor.py` | Security log events 4663/4660; watched-folder filter, allowed application list, access-code classifier, three-second deduplication, handle-based deletion correlation with ten-second expiry. Requires Win32 event APIs, Windows auditing configuration, and suitable Security log permissions. |
| `usb_monitor.py` | WMI USB disk/partition/logical-drive enumeration; two-second polling and insert/remove activity. Requires COM/WMI. |
| `usb_copy_monitor.py` | Watches a fixed `E:` location; matches completed-copy SHA-256 against known files, logs `SENSITIVE_USB_COPY`. No general automatic removable-drive watch selection. |
| `local_copy_monitor.py` | Watches a fixed Windows project folder, ignores originals beneath sensitive-files directory, logs matching copies as `SENSITIVE_LOCAL_COPY`. |
| `google_drive_monitor.py` | Watches fixed `G:\My Drive`, logs matching local synchronized-folder files as `SENSITIVE_CLOUD_COPY`; it does not verify remote cloud receipt. |
| `upload_server.py` | Flask test server on localhost:5000; saves uploads and logs known SHA-256 matches as `SENSITIVE_UPLOAD`. This is not endpoint-wide network upload monitoring. Import creates upload directory and builds fingerprints; tests import only inside temporary storage with fingerprint building patched. |
| `sensitivity.py` | Four hardcoded Windows file policies; case-insensitive basename lookup using host path semantics and chunked SHA-256. Fingerprints are built at monitor startup, not automatically refreshed. |
| `database.py` | Append logging to CWD-relative `data/activity.db`, naive local ISO wall-clock timestamps, `getpass.getuser()` identity. `CREATE TABLE IF NOT EXISTS`, not a versioned migration system. |
| `behavioral_monitor.py` | Foreground process/window title and keyboard/mouse idle time sampled every five seconds; idle threshold 60 seconds; writes separate `behavior_events`. Windows GUI/ctypes and psutil dependencies. |
| `baseline.py` | Prints historical activity/user summaries. No learned or persisted baseline, no chronological cutoff. |
| `behavior.py` | Recent activity/transfers aggregates, username filtering when supplied, 60-minute default; fixed 09:00–17:00 work hours. Does not aggregate `behavior_events` idle samples. |
| `feature_builder.py` | Non-overlapping global hourly windows of activity/transfers; CSV includes no username. No user baselines, feature availability contract, or missingness mask. |
| `prepare_training.py` | Filters rows with nonzero numeric feature sum and saves CSV. No training. |
| `risk_engine.py` | Sensitive/repeated/critical/write/after-hours count score. Component caps total 85 despite `/100` presentation. Levels LOW/MEDIUM/HIGH/CRITICAL at 25/50/75. |
| `dashboard.py`, `dashboard.html` | Flask console at localhost:8000, SQLite queries, JSON role/settings policy, persisted analyst statuses, severity rules and monitor subprocess controls. |

Hardcoded roots refer to `C:\Users\Crown Tech\Desktop\AI-DLP-Agent`.
Most scripts use CWD-relative SQLite paths; dashboard uses its own absolute source-folder path.
Dashboard main changes CWD before initialization; other launch paths can split storage.
Live inference adapters must make the DB path explicit without changing existing defaults.
Windows Security events parse `SubjectUserName`, but `log_activity` stores the process user's
`getpass` identity and a fresh receipt timestamp. Multi-user attribution and event-time limitations
must be accounted for before endpoint models are described as validated.

## SQLite and policy contracts

The existing live schema was inspected with `mode=ro&immutable=1` and `PRAGMA query_only=ON`.
Only table schemas and aggregate row counts were read; no event contents or usernames were read.
It matches the inspected initializer definitions. See `phase0_live_schema.json`.

| Table | Existing columns | Baseline row count |
|---|---|---:|
| activity | id, timestamp, username, event_type, file_path, sensitivity, application | 5 |
| transfers | id, timestamp, username, event_type, source_path, destination_path, sensitivity, destination_type, file_hash | 2 |
| behavior_events | id, timestamp, username, event_type, application, window_title, idle_seconds | 241 |
| alert_state | alert_id, status, updated | 1 |

Dashboard `data/policy.json` contains roles, assignments, disabled rules, and settings.
Defaults: work_start=9, work_end=17, half_life_h=6, saturation=50, flag_floor=60, auto_approve=True.
`load_policy()` creates defaults when missing/invalid; tests redirect it before use.
`save_policy()` retains unknown top-level extensions during supported API updates.
Role definitions and sensitive-file list have no editing API in this implementation.

## Dashboard API contracts

| Route | Method | Existing response contract |
|---|---|---|
| `/` | GET | Dashboard HTML |
| `/api/users` | GET | List: name, role, device, score, raw, flagged, level, behavior, last_seen, open_alerts, critical, now |
| `/api/alerts` | GET | List: id, ts, user, severity, title, file, detail, rule, status; optional reason/esc/permitted; user/window/status/permitted filtering |
| `/api/alerts/<aid>` | POST | `{ok:true}`; stores requested analyst status in alert_state |
| `/api/alerts.csv` | GET | CSV: time,user,severity,title,file,detail,status |
| `/api/events` | GET | Activity/transfer columns plus kind; user/window/category filters; at most 80 rows |
| `/api/timeline` | GET | Twelve buckets: start, activity, transfers |
| `/api/rules` | GET | Eight definitions: id,name,source,severity,iso,why,enabled,hits |
| `/api/rules/<rid>` | POST | `{ok:true}`; toggles disabled rule |
| `/api/settings` | GET/POST | Existing settings object; unknown submitted setting keys ignored |
| `/api/roles` | GET | roles, assign, users |
| `/api/roles/assign` | POST | `{ok:true}`; assignment or removal for Unassigned |
| `/api/policies` | GET | files list with name,path,sensitivity,exists,accesses,transfers |
| `/api/monitors` | GET | Seven entries: key,script,name,desc,running,exited,log |
| `/api/monitors/<key>` | POST | Same monitor list; start/terminate subprocess |
| `/api/reset` | POST | `{ok:true}`; deletes live event/alert rows. Route inventoried only; never invoked. |

Dashboard rule IDs R01–R08 cover removable copies, cloud-folder copies, local uploads,
local copies, moves, unauthorized file access, out-of-hours severity escalation, and USB insertion.
The dashboard score uses severity weights (25/15/6/1), exponential time decay, status
factors (open=1, suspicious=2, others=0), saturation, and a suspicious-user floor.
This differs from `risk_engine.calculate_dlp_score`; integration must retain separate definitions.
Alerts are deduplicated by user/title/file within 30 seconds. Queries cap activity/transfer
rows before deduplication; high-volume windows can omit older relevant events.

## Pre-existing findings and unavailable checks

1. Feature builder mixes users: no username grouping or output field; source inspection establishes this.
   A characterization test will reproduce it when Linux pandas becomes available.
2. Both-empty tables have an early empty-DataFrame return. Activity-only and transfer-only
   runtime checks are pending; do not assume their success or failure from source alone.
3. `MODIFIED`/`DELETED` from agent.py are accepted by dashboard alerts, but behavior/features
   count only `FILE_WRITE`/`FILE_DELETE`, so those summaries omit watchdog changes.
4. `behavior_events` samples are visible in dashboard latest-app context but absent from legacy
   hourly features/recent summaries. No behavioral anomaly model exists.
5. Role-permitted after-hours access is hidden as `permitted` and bypasses R07 escalation.
   The corresponding baseline characterization passes, but behavior conflicts with comments
   promising after-hours human review. Preserve until a scoped correction is authorized.
6. On Ubuntu the hardcoded Windows basenames are not interpreted as Windows paths.
   Filename-policy tests use synthetic host-native paths; they do not validate Windows path handling.
7. Numeric settings clamp at a minimum of 1; midnight work_start=0 cannot be saved through API.
8. Upload filename joins are unbounded/unsanitized; startup fingerprints can become stale.
   Record for later scoped work; Phase 0 does not alter these existing behaviors.
9. Missing system Flask/pandas/sklearn and Windows compiled packages are environment limits,
   not introduced application regressions. Importing Windows pandas fails at `os.add_dll_directory`.

No ingestion, CERT labeling, model training/loading, text extraction/classification, feature
contract, chronological evaluation, or historical replay implementation was found.
There is no independently labeled document-sensitivity corpus identified at this point.

## Regression evidence and exact commands

Result: **22 checks attempted, 18 passed, 4 skipped, 0 failures, 0 errors**.
Available checks cover append logging/schema idempotence, empty behavior, user isolation,
parameterized usernames, score caps/level boundaries, filename/hash signals, API fields,
role/settings/rule persistence, analyst decisions and scores, CSV export, deduplication,
out-of-hours escalation, USB autoapproval, and synthetic hash matching in copy/upload handlers.
No subprocesses or observers ran. Monitor controls use fake processes. Windows event parsing
and behavior logging use mocked Win32 imports only. Native Security log subscription,
audit configuration, deletion correlation end-to-end, foreground GUI/idle APIs, physical USB,
real cloud syncing, and endpoint event collection remain unverified on Ubuntu.

```bash
python3 -B tools/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output docs/phase0_preservation_before.json
python3 -B tests/phase0_regression.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dependency-root /home/sohaib/Downloads/AI-DLP-Agent/venv/Lib/site-packages --report docs/phase0_baseline.json > docs/phase0_baseline.log 2>&1
python3 -B tools/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output docs/phase0_preservation.json --compare docs/phase0_preservation_before.json
wc -l DATASHIELD_IMPLEMENTATION.md
```

Pure-Python Flask and its dependencies were imported from the existing Windows venv
using `--dependency-root`; no packages were copied or installed. Linux pandas is still required.
Skipped checks remain explicit in JSON/log and keep Phase 0 incomplete. With native Linux
dependencies, omit `--dependency-root` and run against the reconciled checkout.
The suite exits nonzero for failures/errors; its successful exit with skips is not phase acceptance.
Detailed results are in `phase0_baseline.json` and `phase0_baseline.log`.

## Dataset identity and research separation

Neither `proj/dataset` nor `dataset` exists in the writable workspace. The archives remain at
`/home/sohaib/Downloads/{r4.2.tar.bz2,answers.tar.bz2,SEI_Insider_README.txt}`.
The source has an empty `Dataset` directory, which is not the requested path.
Record/use these existing archive paths after confirming them in Phase 1; avoid copying large files.
No README/archive/header inspection or label mapping has been performed yet.
About 424 GiB is available on the workspace filesystem; `/tmp` is a 7.7 GiB tmpfs.
Research events must use a separate `research/local/cert_r42.sqlite` or equivalent explicit path.
Research artifacts, extracted logs, and datasets must be excluded from Git before ingestion.

## Recovery and checkpoint

The failed command was:

```bash
git clone https://github.com/sohaib-0897/DataShield.git /home/sohaib/Insider_Threat_Test_Dataset/DataShield
```

Run it from a terminal/environment with working GitHub DNS and network access.
This failure occurred before authentication; repository access and remote URL cannot yet be verified.
No local checkpoint or push exists, and no fake Git repository was created.
After clone: read AGENTS.md, inspect status/origin/history, fetch, create/resume `feat/cert-ml-nlp`,
compare relevant source files with the download, and reconcile deliberately before editing.
Transfer only these new phase documents/tests/tools; exclude environments, caches, logs containing
live content, live DBs, policies, sensitive documents, credentials, and datasets from source transfers.
Use native Linux dependencies to run all pending feature checks against both original and reconciled
source; record existing failures separately and repair any reconciliation regression.
One isolated dependency setup, from a terminal with package-index network access, is:

```bash
python3 -m venv /tmp/datashield-phase0-venv
/tmp/datashield-phase0-venv/bin/python -m pip install flask pandas watchdog psutil
```

Use that interpreter for the documented regression command and omit `--dependency-root`.
Then update the status file inside DataShield, review/stage phase files only, commit, push without
force, and compare remote branch SHA with local HEAD. The exact next phase is finishing Phase 0.
