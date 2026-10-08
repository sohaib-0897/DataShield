# DS1 handoff: taxonomy, source review and annotation readiness

2026-10-08. **First new phase only is complete, with corpus acquisition blocked.**
No document-sensitivity training, model evaluation, organizational annotation,
CERT ingestion/training rerun, model activation or policy change occurred.

## Checkpoint and preserved behavior

Started clean on `feat/cert-ml-nlp`; actual local HEAD and fresh GitHub branch
both matched `b881673ea91e5a31bc7036caebe8f62236079a06`. Origin matches
`https://github.com/sohaib-0897/DataShield.git`. No AGENTS.md found in the
checkout or ancestors. Read DATASHIELD_IMPLEMENTATION.md, CONTEXT.md and the
complete prior NLP follow-up report before edits.

Reviewed Flask filename/hash policies, dashboard alert semantics, FastAPI
rule/optional-model interfaces, React fields, bounded TXT/PDF/DOCX extraction,
and the independent binary training interface. All remain unchanged. Original
strict-cohort results and the separately declared known-user experiment remain
historical evidence, not document-sensitivity labels or a new run.

## Decisions and deliverables

- [Taxonomy and human-label guide](taxonomy-and-annotation.md) separates four
  content categories from owner/context-dependent NORMAL/HIGH/CRITICAL levels.
  Unknown remains unknown; public email/financial text does not establish
  confidentiality. No automatic mapping of current FastAPI four-level policies.
- [Dataset registry](dataset-research.md) records primary sources, labels,
  annotation provenance, licenses, access, sizes/counts, privacy/domain limits
  and rejection reasons for seven candidates. Local searches found no independent
  organizational sensitivity corpus. No unrelated targets were relabeled.
- TAB is selected **only for a potential provided-entity-span semantic-category
  benchmark** in English legal text. MIT corpus terms permit acquisition with
  notices retained. Human-reviewed machine-assisted annotations have documented
  disagreements. TAB is not document-sensitivity ground truth; no policy levels
  or independent credential/business-confidential document targets exist there.
- [Acquisition evidence](acquisition-status.json) pins upstream revision
  `558e09e26d6b36f5f78440074e6a233946d98bd9`, records expected Git blob IDs/sizes,
  verifies all three metadata files against that tree and captures partial-file
  SHA-256/bytes. No corpus manifest was published; actual row/class inventory
  remains unavailable. Source-reported 1,014/127/127 documents and class counts
  are explicitly distinguished from local observations.
- `research.tab_inventory` provides bounded acquisition, safe selected-member
  archive import with Git blob validation, source SHA-256 verification, offset
  and label schema checks, aggregate counters and exact cross-split overlap
  findings. It never fits a model or declares supplied splits leakage-free.
  Near-duplicate/case/subject grouping remains DS2 work.
- `research.document_annotation` creates blank private packets through the
  existing extractor and validates independent review declarations, context,
  policy/text provenance, abstention and third-reviewer disagreement resolution.
  Synthetic tests validate guards only. The standalone CLI ran on an inert
  extraction fixture, producing **no labels** and no trained artifact.
- [Later phase contract](later-phases.md) specifies grouping/duplicate controls,
  training-only CPU TF-IDF/linear baselines, validation-only threshold selection,
  untouched natural test populations, compatible rule comparisons, undefined
  metrics, error strata and honest score reporting. Extraction failures/partial
  text remain explicit coverage outcomes; existing fallbacks stay intact.

## Acquisition blocker and recovery

Ignored private storage: `research/local/document_sensitivity/` (directory mode
700). Metadata in `tab_v1/` and `tab_558e09e/`; pinned API `tab-tree.json`.
Four incomplete `.partial` downloads are preserved for audit, **untrusted**.
Direct raw acquisition suffered TLS/read timeouts. A pinned compressed archive
failed with HTTP/2 CANCEL (curl exit 92); HTTP/1.1 retry timed out (exit 28) after
240.002 seconds, receiving 489,298 bytes. No complete dataset downloaded.

Commands used, from repository root (failed destinations are preserved):

```bash
git status --short
git rev-parse HEAD
git ls-remote origin refs/heads/feat/cert-ml-nlp
git ls-remote https://github.com/NorskRegnesentral/text-anonymization-benchmark.git refs/heads/master
curl --fail --location 'https://api.github.com/repos/NorskRegnesentral/text-anonymization-benchmark/git/trees/558e09e26d6b36f5f78440074e6a233946d98bd9' --output research/local/document_sensitivity/tab-tree.json
.local/phase0-venv/bin/python -B -m research.tab_inventory --acquire --directory research/local/document_sensitivity/tab_558e09e --report research/local/document_sensitivity/tab-inventory.json
curl --http1.1 --silent --show-error --fail --location --proto '=https' --proto-redir '=https' --connect-timeout 10 --max-time 240 --max-filesize 67108864 --output research/local/document_sensitivity/tab-source-http1-558e09e.zip.partial 'https://codeload.github.com/NorskRegnesentral/text-anonymization-benchmark/zip/558e09e26d6b36f5f78440074e6a233946d98bd9'
```

DS2 recovery starts by acquiring a complete pinned archive over a working
connection into a **new** ignored file, allowing a longer bounded download:

```bash
curl --http1.1 --silent --show-error --fail --location --proto '=https' --proto-redir '=https' --connect-timeout 10 --max-time 1800 --max-filesize 67108864 --output research/local/document_sensitivity/tab-source-retry-558e09e.zip.partial 'https://codeload.github.com/NorskRegnesentral/text-anonymization-benchmark/zip/558e09e26d6b36f5f78440074e6a233946d98bd9'
# Only after curl succeeds; keep the archive and do not execute its scripts:
.local/phase0-venv/bin/python -B -m research.tab_inventory --archive research/local/document_sensitivity/tab-source-retry-558e09e.zip.partial --tree research/local/document_sensitivity/tab-tree.json --directory research/local/document_sensitivity/tab_verified_retry --report research/local/document_sensitivity/tab-inventory-retry.json
```

Neither recovery command was run in DS1. A `.partial` suffix is not evidence of
completion: ZIP structure, expected size, six pinned Git blobs and SHA-256 must
pass before a trusted manifest exists. If still unavailable, record that blocker
and continue the independent authorized annotation preparation. Never treat
partial files or source-reported counts as a prepared corpus.

## Verification and actual resource use

See [verification.json](verification.json); raw logs are ignored under `.local/`.

```bash
.local/phase0-venv/bin/python -B -m pytest -q tests/test_document_sensitivity_phase1.py tests/test_document_research.py -p no:cacheprovider
/usr/bin/time -v -o .local/ds1-isolated-resource.txt .local/phase0-venv/bin/python -B scripts/verification/phase0_upstream_baseline.py --report .local/ds1-isolated-tests.json --log .local/ds1-isolated-tests.log
/usr/bin/time -v -o .local/ds1-flask-resource.txt .local/phase0-venv/bin/python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --require-no-skips --report .local/ds1-preserved-flask-tests.json
python3 -B scripts/verification/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output .local/ds1-preservation.json --compare docs/implementation/phase0/phase0_preservation_before.json
git diff b881673 -- backend frontend ml legacy research/documents.py research/sensitivity_training.py docs/implementation/nlp-followup
git diff --check
git check-ignore research/local/document_sensitivity/tab-tree.json
wc -l DATASHIELD_IMPLEMENTATION.md
```

- Isolated full suite: **175 passed**, no skips/collection errors; existing
  Starlette deprecation warning only. Pytest 20.06s; total command wall 22.78s;
  maximum RSS 397,660 KiB (388.340 MiB). Existing regression fitting uses only
  small fixtures, not a real sensitivity corpus or repeated CERT experiment.
- Preserved Flask: **22 passed**, no skips; command wall 1.48s, maximum RSS
  103,680 KiB. Tests use temporary SQLite, fake processes/devices and no monitors.
- New schema/annotation/overlap/hash tests plus existing extraction tests check
  malformed/encrypted/scanned/empty/oversized inputs and preservation of fallback.
- Targeted extraction/new-phase checks: **42 passed**, pytest 7.01s / command
  wall 8.06s, 118,072 KiB maximum RSS. Blank packet CLI: wall .30s / 24,088 KiB;
  inert fixture only, no labels or model.
- Source/live files: all 30 hash/stat entries match original baseline; all three
  original dataset archive/readme stat observations match. This is not a new
  whole-archive content hash. Application/prior-report Git diff is empty.
- [Frozen artifact checks](frozen-preservation.json): all **13 match**, including
  historical/June stores/features/models, three known-user models, cohort,
  thresholds and prepared store. Features use canonical payload hashes via the
  existing verifier; an initial whole-file/payload comparison was corrected,
  preserving that diagnostic in `.local/ds1-frozen-rawhash-check.json`. No frozen
  files changed. Raw hash stage 4.605s; canonical feature check command 6.22s /
  801,832 KiB (783.039 MiB), the largest observed DS1 command RSS. This checks
  preservation only; it does not recompute features, labels, scores or training.
- DATASHIELD_IMPLEMENTATION.md is **197 lines**, below the 200-line limit.
- Raw text/documents, partial archives, fixtures, review packets, environments and
  models are ignored. No runtime policy, model-loading behavior or active artifact
  changed. No real corpus preparation/training memory/runtime claim is made.

## Next session

“Start next phase” means **DS2 only**: verify Git checkpoint/push, retry and verify
the pinned acquisition, reconcile annotations and audit source/case/subject/version
groups and duplicates, freeze train/validation/test manifests, then fit only the
supported lightweight provided-span baseline if labels/splits are defensible.
Organizational classification remains blocked pending owner policy/examples and
the 100-document pilot plus proposed 1,200-document independently reviewed corpus.
DS3 evaluation/error analysis/optional advisory integration is a separate later
phase. Stop at this DS1 handoff; no automatic continuation into DS2.

Publication commands: `git diff --cached --check`; stage relevant source/tests/docs
only; commit; `git push origin feat/cert-ml-nlp`; verify
`git ls-remote origin refs/heads/feat/cert-ml-nlp` equals `git rev-parse HEAD` and
`git status --short` is empty. If push fails, preserve local HEAD and recover with
`git push origin feat/cert-ml-nlp` (never force). Final checkpoint is Git HEAD and
fresh remote verification; parent is the recorded starting SHA above.
