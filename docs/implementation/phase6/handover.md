# Pipeline and runtime handover

Run all research commands from the literal-tilde checkout:

```bash
cd '/home/sohaib/Insider_Threat_Test_Dataset/DataShield~'
```

Reuse `.local/phase0-venv`; isolated research dependencies are listed in
`requirements-research.txt`. Never install them into a live endpoint environment
or point CERT ingestion at the application database. Original archives remain
in Downloads; local path configuration and every raw artifact stay ignored.

For a new run, retain existing artifacts and choose new output names. The exact
cohort interval was selected before evaluation; repeating or expanding a study
requires a separately declared interval, not selection based on test performance.

```bash
# Full archive scan, bounded retained cohort. Interrupted scans restart safely.
.local/phase0-venv/bin/python -B -u -m research.cohort --archive /home/sohaib/Downloads/r4.2.tar.bz2 --start 2010-06-07T00:00:00 --end 2010-06-21T00:00:00
# Copy the existing local config into .local/cert_phase6_paths.json, changing only
# research_database to research/local/phase6_cohort.sqlite. Use the printed manifest.
.local/phase0-venv/bin/python -B research/cert_ingest.py --config .local/cert_phase6_paths.json ingest --manifest research/local/cohort-tf2zqu5i/manifest.json --chunk 2000 --report research/local/phase6_ingestion.json
# Rerun the same ingestion command to resume committed chunks or verify idempotency.
.local/phase0-venv/bin/python -B -m research.cert_features --database research/local/phase6_cohort.sqlite --answers research/local/scan-i4h4v35l/manifest.json --output research/local/phase6_features.json --report research/local/phase6_features_report.json --max-events 1000000 --max-metadata-mib 768
.local/phase0-venv/bin/python -B -m research.behavioral_ml --features research/local/phase6_features.json --output research/local/phase6_benchmark_v1 --max-feature-mib 512
.local/phase0-venv/bin/python -B -m research.comparison --benchmark research/local/phase6_benchmark_v1 --output research/local/phase6_comparison.json
.local/phase0-venv/bin/python -B -m research.text_study --features research/local/phase6_features.json --database research/local/phase6_cohort.sqlite --numeric-report research/local/phase6_benchmark_v1/report.json --output research/local/phase6_text_v1 --max-events 1000000 --max-metadata-mib 768 --max-feature-mib 512
```

The actual published manifest is `research/local/cohort-tf2zqu5i/manifest.json`;
`cohort-scan.json` records its digest and source counts. Scan caches preserve original CSV row positions. The frozen historical
store/features/benchmark remain separate. Larger materialization bounds are
explicit opt-ins after resource review; the default 128 MiB metadata/64 MiB
artifact rejection guards remain intact. Do not attempt full release preparation
with the current materializing feature/text implementation. A streaming path or
sufficient measured memory is required first. Full source scanning is not full
release ingestion/evaluation.

The January smoke command was separately run into `phase6_smoke_v1`; its results
must not be pooled with the June cohort. Comparison heuristics are fixed research
signals; they do not reproduce live role/hash/sensitivity policy. Combined OR is
an unvalidated benchmark decision rule, not a runtime enforcement threshold.
Thresholds/preprocessing use validation/training only. Natural test prevalence
and null metrics must be preserved. Repeated fit, serialized reload and artifact
hash checks are required by the benchmark; do not convert null recall to zero.

Safe regression commands:

```bash
.local/phase0-venv/bin/python -B scripts/verification/phase0_upstream_baseline.py --report .local/new-isolated-tests.json --log .local/new-isolated-tests.log
.local/phase0-venv/bin/python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --require-no-skips --report .local/new-preserved-tests.json
python3 -B scripts/verification/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output .local/new-preservation.json --compare docs/implementation/phase0/phase0_preservation_before.json
git diff --check
```

The isolated runner copies tracked Python sources to disposable storage. Stage
new test/modules first when validating uncommitted work; the runner cannot test
untracked code. It uses synthetic credentials and temporary SQLite, not PostgreSQL.
Preserved Flask tests mock Windows dependencies and do not validate a real endpoint.

Existing upstream startup (for a deliberate local deployment with configured
secrets and a disposable database), unchanged by these phases:

```bash
# Populate .env using .env.example with locally chosen secrets; never commit it.
docker compose up --build
# Browser: http://localhost:3001 ; API: http://localhost:8001
# The backend startup runs existing migrations; choose storage deliberately.
```

Docker is not available in this session. The default frontend container starts
the development server and still executes audited development dependencies; see
`npm-review.md`. No container/startup/PostgreSQL verification is claimed.
For the established local frontend flow, `npm start --prefix frontend` uses
`http://localhost:8000` by default; set `REACT_APP_API_URL` to the intended API
before startup. No server was launched during these phases.

The supplied original Flask app retains its normal Windows setup/start command
`python dashboard.py` from its own directory. Do not launch research against its
live files or import `agent.py` to test it. Native endpoint/device verification
must use a deliberate Windows test machine with isolated test storage; no physical
USB or account/policy change was executed here.

Opt-in advisory host wiring is documented in `../phase5/advisory.md`. Defaults
are disabled/shadow; only read-only status/evidence views are installed explicitly
with existing analyst authorization. Current live features report schema mismatch
with CERT research artifacts. No research artifact is registered/activated, and
no research prediction can supply a blocking decision through this contract.

The plan ends at Phase 6. The next engineering prerequisite for full-release
quality work is streaming feature/text preparation under measured memory bounds.
Independent sensitivity labels, a live signal-compatible artifact and native
Windows/PostgreSQL verification remain separate prerequisites for their claims.
