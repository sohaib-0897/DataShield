# Streaming preparation milestone

Start: clean `feat/cert-ml-nlp`, local and freshly queried remote both
`216a0eb2a49161ab2f185af7dec53e035c278a35`. No applicable AGENTS.md found.
Read CONTEXT.md, DATASHIELD_IMPLEMENTATION.md (the implementation plan), and
Phase 4–6 reports before editing. User authorized this separate follow-up.

`research.stream_prepare` uses a read-only source snapshot, verified complete
answer manifest, reusable exact scoped-ID/all-fields answer index, source-position
chronology check, and disk-backed SQLite sorting. A user-hour is capped at 16 MiB
metadata/resource bytes and 50,000 events; past PC state at 50,000 PCs. History
stores completed fully observed window count/sum and PCs for one user. Source
coverage, naive release-local time, active hours, work hours, availability and
past-only features keep the original semantics. Windows/text keep original
source_file/source_row order within hours. Output order is start,user.

Transactions commit one complete user; a process interruption rolls back the
current user. Resume recomputes that user from its earliest event, never from a
future baseline. Contract hashes/settings reject changed source/answers. Source
hashes match before/after; original DB is never indexed or modified. The output
has its own application_id/user_version, per-user counters, matched answer rows,
window bags and provenance. An unchanged completed rerun writes nothing.
A failed initial run can leave an empty preparation DB, safely resumable.
An initial check exposed nullable `resource`; handling None corrected it without
changing normalization, labels or features.

Measured commands (from repository root, existing ignored environment):

```bash
.local/phase0-venv/bin/python -B -m research.stream_prepare --database research/local/cert_r42.sqlite --answers research/local/scan-i4h4v35l/manifest.json --output research/local/nlp_january_stream.sqlite --report research/local/nlp_january_stream.json
.local/phase0-venv/bin/python -B -m research.stream_parity --prepared research/local/nlp_january_stream.sqlite --frozen research/local/phase2_features_v1.json --database research/local/cert_r42.sqlite --report research/local/nlp_january_parity.json
.local/phase0-venv/bin/python -B -m research.stream_prepare --database research/local/phase6_cohort.sqlite --answers research/local/scan-i4h4v35l/manifest.json --output research/local/nlp_june_stream.sqlite --report research/local/nlp_june_stream_partial.json --stop-after-users 20
.local/phase0-venv/bin/python -B -m research.stream_prepare --database research/local/phase6_cohort.sqlite --answers research/local/scan-i4h4v35l/manifest.json --output research/local/nlp_june_stream.sqlite --report research/local/nlp_june_stream.json
.local/phase0-venv/bin/python -B -m research.stream_prepare --database research/local/phase6_cohort.sqlite --answers research/local/scan-i4h4v35l/manifest.json --output research/local/nlp_june_stream.sqlite --report research/local/nlp_june_idempotent.json
.local/phase0-venv/bin/python -B -m research.stream_parity --prepared research/local/nlp_june_stream.sqlite --frozen research/local/phase6_features.json --database research/local/phase6_cohort.sqlite --report research/local/nlp_june_parity.json
.local/phase0-venv/bin/python -B -m pytest -q tests/test_stream_prepare.py tests/test_cert_features.py tests/test_text_research.py
```

| Actual run | Rows/windows | Seconds | Peak RSS MiB |
|---|---|---:|---:|
| January preparation | 10,000 / 3,291 | 5.900 | 425.313 |
| January all-row feature/label/key/text/bag parity | 3,291 windows | 0.469 | 425.313 |
| June stopped checkpoint | 14,136 / 1,976, 20 users | 6.480 | 425.313 |
| June resume | total 978,908 / 96,063, 973 users; 953 new users | 122.668 | 425.313 |
| June completed replay | zero new users/rows | 4.219 | 425.313 |
| June all-row feature/label/key/text/bag parity | 96,063 windows | 56.333 | 928.453 |

All 96,063 windows equal frozen Phase 6, not just sampled rows. Full sanitized
text/order and keyword bag hashes equal legacy attach_text on each frozen
window. Legacy event contents are fetched one window at a time for parity;
only the frozen JSON feature artifact is materialized during verification.
Counters match 978,838 negative/70 positive events, 7,253 unmatched observables,
zero unknowns, 95,930 fully observed windows, 940,871 text events and 6,600
repeated normalized bags. Stream preparation peak stayed 425 MiB as event
population increased nearly 98-fold. This is a measured bounded run, not a
full-release throughput/memory guarantee.

24 targeted tests passed at this milestone. Fixtures inject interruption inside
a user transaction, assert all partial windows/bags/checkpoint rows roll back,
resume and repeat, reject changed parameters/input schema/byte bounds, and check
past-only feature/exact label parity. Larger source ingestion still uses the
existing safe archive/cache pipeline; no complete 32.77M-row import was attempted.
Original archive scan and frozen historical/June artifacts remain untouched.
