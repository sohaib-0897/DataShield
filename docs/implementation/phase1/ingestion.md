# Phase 1: release-aware bounded CERT ingestion

Phase 0 publication was verified before this work. The supplied general README,
r4.2/readme.txt, answers/readme.txt, all archive member paths/types and actual CSV
headers were inspected. Input SHA-256 hashes and metadata-only inventory are in
`release_inspection.json`. No application loader, monitor, server, policy, live
database, schema or model was changed.

## Established release contract

| Source | Research channel | Action | Resource | Preservation |
|---|---|---|---|---|
| file.csv | FILE | copy_to_removable_media | filename | Release README states every row is a copy to removable media; no activity column exists |
| device.csv | USB | Original activity | Unavailable | Connect/Disconnect validated without changing case; no device identity is invented |
| logon.csv | LOGON | Original activity | Unavailable | Logon/Logoff validated; missing logons and screen-unlock ambiguity remain source limitations |
| http.csv | HTTP | visit | url | Browsing evidence; no cloud-upload action inferred and no URLs contacted |
| email.csv | EMAIL | send | to | Actual `attachments` column retained; README calls it attachment_count; cc/bcc/from/size/content preserved |

The real file/http/email schemas differ from the old expected-format loader.
`research/cert_ingest.py` is independent of that loader and all application code.
`release_inspection.json` contains exact headers; changed/missing event-source
headers fail before event insertion. All original CSV fields remain strings in
metadata, including content and original date, ID, user, PC and action. Fields
without an activity column use the documented release semantic above. Content
represents synthetic topic keywords; file content also has a hexadecimal header.
It is not an extracted document body or a document-sensitivity label.

No inspected documentation establishes a timezone. Timestamps retain original
strings plus a naive ISO representation and `unspecified_release_local` basis.
UTC conversion, work-hour assumptions and cross-source time alignment remain
explicit Phase 2 decisions. IDs are scoped to source file and dataset hash;
the README warns that IDs are not necessarily globally unique.

LDAP and psychometric files are inventoried and locally cached, but not imported
as events or inference features. The psychometric README describes signals latent
in actual deployment. Answers are separately inventoried; the master header is
dataset/scenario/details/user/start/end and observables have mixed record types
with variable-length rows. No label joins run in Phase 1. The release README
contains both dense-needle language and an inconsistent threat-count statement;
no ground-truth count is inferred from that prose.

## Safety, isolation and recovery

The CLI consumes ignored `.local/cert_paths.json`, referencing the original inputs
in Downloads and a database confined to `research/local`. No archive is relocated
or duplicated. Only bounded CSV prefixes are retained. Raw prefixes, release
documents, answers metadata, SQLite stores and logs are ignored. Committed evidence
contains counts, source hashes and schemas, with no raw rows or incident identities.

Inspection validates every tar member before publishing a usable manifest. It
rejects absolute paths, traversal, Windows path forms, duplicate canonical names,
all symlinks/hard links and special files. It never uses tar member names as output
filesystem paths and never calls extractall. BZ2File handles the supplied archive's
concatenated bzip2 streams; compressed EOF/CRC/truncation errors fail inspection.
The initial Python tar streaming attempt failed at a compression-stream boundary;
the BZ2File adapter and multi-stream/truncation fixtures resolved that limitation.

Defaults bound expanded member bytes to 32 GiB, member count to 100,000, prefix
cache to 128 MiB, each CSV field to 8 MiB, each logical CSV record to 16 MiB, aggregate archive metadata to 16 MiB, and
preserve at least 256 MiB free disk space. CSV and disk-budget failures leave
unpublished staging directories; they are not trusted or ingested. Incomplete
archive preparation restarts its scan. Once a manifest is published, ingestion
resumes from committed record positions without rescanning compressed members.

Input and cached-prefix SHA-256 hashes are verified; the CLI rehashes the original
archive before ingestion. An inspection stores a fixed maximum row prefix.
Increasing `--limit` resumes within that prepared prefix; limits beyond it fail.
Preparing a different prefix for a store with existing progress fails explicitly;
retain the original manifest or use a new isolated research database. A limit
below already committed progress also fails.

SQLite event insertion, row diagnostics and progress counters commit in the same
bounded transaction. Uncommitted chunks roll back; committed chunks survive
interruption. A separate SQLite writer lock rejects concurrent ingestion and
releases on crash/exit. Unknown existing databases and incompatible research
schema versions are rejected. Database/report/cache paths reject symlinked
ancestors and cannot escape the research directory. Reports cannot replace
inspection manifests or databases.

Research tables are `datasets`, `events`, `diagnostics`, and `progress`, with a
CERT application ID and schema version 1. Events contain dataset hash, source
file, original source ID and record position, username, PC, original/local time,
timezone basis, channel, action, resource, full source metadata and row hash.
Exact duplicate source IDs are counted without another insertion; conflicting
content for the same scoped ID is diagnosed. Empty rows, field-count mismatches,
missing identity/resource fields, invalid timestamps and unsupported actions have
reason codes without logging raw data. Unrecoverable CSV syntax fails preparation.

Counters reconcile `processed = valid + invalid`, `valid = inserted + duplicates`,
and persisted event/error counts against progress. Reported row counts refer only
to the bounded prefix, not to full-source row counts or natural prevalence.

## Commands and measured acceptance

From the checkout root:

```bash
python3 -B research/cert_ingest.py --config .local/cert_paths.json inspect --rows 2000
python3 -B research/cert_ingest.py --config .local/cert_paths.json ingest --manifest research/local/scan-cbxzpxey/manifest.json --limit 1000 --chunk 250 --report research/local/phase1_1000.json
python3 -B research/cert_ingest.py --config .local/cert_paths.json ingest --manifest research/local/scan-cbxzpxey/manifest.json --limit 2000 --chunk 250 --report research/local/phase1_2000.json
```

Use the actual manifest path printed by inspection; the path above records this
run. Repeating the same ingestion command is idempotent. The Python API offers an
`after_chunk` callback used only by acceptance tests to simulate interruption after
a committed chunk. Fixtures also interrupt inside an uncommitted chunk.

Measured acceptance and preservation results are recorded in `acceptance.json`
and `preservation.json`; the test summary is in `tests.json`. Full ingestion,
labeling, features, training, evaluation and activation remain pending later
phases. This bounded prefix establishes pipeline mechanics; it is not a detection
benchmark or evidence of improved model performance.

Actual results on 2026-10-08: 28 safety/recovery tests passed with no skips or
failures. The bounded real run resumed from 250 committed file events to 5,000
events, then 10,000 events (2,000 per source), with zero errors or duplicates.
API and CLI repeats produced identical counters and inserted no new rows. All
10,000 rows' original fields and metadata matched their hashed prefix cache.
Preparation validated 16,181,487,042 member bytes while retaining only 6,252,530
cache bytes; it took 542.616 seconds, separate from the initial inventory scan.
Original source/live hashes (30), input stat records (3), preserved normalized
source hashes (19), and upstream application trees all remained unchanged.
