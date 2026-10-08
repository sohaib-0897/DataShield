# DataShield implementation memory

## Resume contract
- Existing checkout: `/home/sohaib/Insider_Threat_Test_Dataset/DataShield~`; literal trailing tilde.
- Origin: https://github.com/sohaib-0897/DataShield.git; branch: feat/cert-ml-nlp.
- Read applicable AGENTS.md, this file, CONTEXT.md and referenced phase report before work.
- No AGENTS.md found in checkout/ancestors during A1 audit; recheck on resume.
- Execute exactly one bounded phase per request; resume unfinished verification/publication first.
- Keep this file strictly below 200 lines; details belong in separate reports.
- Preserve post-checkpoint work; no reset, force push, unrelated upgrades or replacement checkout.
- Preserve both FastAPI/PostgreSQL/React and legacy Flask/SQLite apps, monitors and policies.
- Use temporary DBs, fake devices and isolated checks; never import/start physical monitors for research.
- New functionality stays offline or disabled by default; no model enforcement activation.
- Never commit data, private documents/packets, models, live DBs, credentials, caches or environments.

## Current phase and publication
- Recovery 2026-10-08: clean `feat/cert-ml-nlp` at d6cd80977df31dddf1fe8ce3756ec9dff9541537.
- A1 source ebc23db + receipt d6cd809 verified; fresh fetch/remote equal, closure CI 37770400258 success.
- A2 implementation DONE: pinned train/dev annotation screening and frozen B evaluation protocol.
- A2 publication/full exact-SHA CI PENDING; finish this gate before B1; no B work executed.
- Details: `docs/implementation/phase-a2/report.md`, annotation-screening.json, evaluation-protocol.json.
- Protocol automatic-content-evaluation-b-v1 frozen before model selection; digest in detailed report.
- Local 12 new/290 supplemental Python +22 Flask passes; 9 API tests unavailable due socketpair EPERM.
- Full local suite timed out at unchanged FastAPI test; traceback retained, tests not weakened.
- All 13 canonical artifacts, 60 A1 private files, 12 DS3 inputs, six TAB sources and 30 live entries match.
- Four SQLite read-only quick_checks OK, checkpoint totals reconcile; three manifests/406 caches validate.
- Four historical TAB partials/DB locks preserved; no job/service restarted; host PID visibility limited.
- Initial staged/uncommitted work absent; no applicable AGENTS.md found; unrelated parent files preserved.
- Labels BLOCKED: authorized inventory, approved versioned policy/context and blind reviews absent.
- Contextual fitting/export BLOCKED: completeness/overlap/family gates and compatible local model unverified.
- Direct Git network and GitHub connector reads work; shell gh remains network-blocked.
- If push fails: retain local commit, `git push origin feat/cert-ml-nlp`; never force-push.
- Ignored recovery/artifact evidence: `.local/phase-a2-recovery/`, `research/local/document_sensitivity/phase_a2_*`.
- Exact next phase after A2 verification: B1 family/coverage audit and versioned eligible development manifest.

## Remaining bounded plan
| Phase | Deliverable / gate | Status |
|---|---|---|
| A1 | Audit labels/packet workflow; deterministic detection and bounded extraction bridge | complete (bounded offline), source published/CI passed |
| A2 | Contextual full-span/local NER feasibility; freeze B protocol before selection | implementation done; exact-SHA CI pending |
| B1 | Audit evaluation families/annotation coverage; separately version eligible development population | next after A2 CI |
| B2 | Fixed detector/category/end-to-end metrics, failure analysis and resources | pending B1 |
| C1 | Analyze independent pilot; strengthen training/export validation, or record exact blockers | pending labels; interface work possible |
| C2 | Grouped CPU sensitivity experiment vs approved policy, only if defensible | blocked labels/policy |
| D1 | Disabled authenticated automatic advice; extraction bounds, schema/cache/failure tests | pending A/B contracts |
| D2 | Separate dashboard advice and regression/fallback checks; no enforcement changes | pending D1 |
| E1 | Diagnose CERT errors; predeclare new past-only versioned experiment/population | pending; original results retained |
| E2 | Run fixed behavioral experiment, common-population comparisons and honest negative findings | pending E1 |
| F1 | Linux smoke/replay and runnable Windows native verification harness | pending integrations |
| F2 | Demonstration/handover, limitations and reviewable activation proposal only | pending F1; native checks conditional |
- Split again if a row exceeds a bounded session; never mark blocked/skipped work completed.
- C can provide policy-derived advisory only after explicit owner-approved versioned policy/context.
- Missing context produces review-needed/unknown, never inferred NORMAL.

## Architecture and integration boundaries
- `research/documents.py`: offline TXT/PDF/DOCX bounded subprocess extraction; redacted legacy patterns.
- Existing extraction: 2 MiB file, 40 pages, 32768 text characters, 8s wall, 5 CPU seconds, 512 MiB.
- Keep extraction statuses/truncation explicit; encrypted/scanned/malformed/unsupported are unavailable.
- `research/document_annotation.py`: blank private packets + declaration validation; not proof of independence.
- `ml/supplied_spans.py`: eight TAB supplied-span categories, operator-pinned artifacts, cached success/failure.
- `backend/app/span_advisory.py`: POST /api/v1/advisory/supplied-spans; ADMIN/ANALYST authentication.
- DATASHIELD_SPAN_ADVISORY_ENABLED=false; existing interface and enforcement unchanged.
- Existing rules: `backend/app/analysis.py`, `backend/app/sensitivity.py`, legacy sensitivity/dashboard.
- Existing behavior: `ml/registry/`, `backend/app/advisory.py`, shared research adapters; keep rule fallback.
- `ml/content_detection.py`: structured-content-detectors-v1; offline-only; no runtime calls.
- `research/automatic_content.py`: opt-in extraction bridge; redacted offsets; policy null/review-needed.
- 32768 chars/131072 bytes, 100 returned candidates; DE/GB/PK IBAN structure/checksum; no new dependency.
- D adds separately flagged API later; A2 assesses unsupported contextual entities before evaluation.
- Detection, supplied-span classification, policy sensitivity, learned sensitivity and behavior are distinct tasks.
- No automatic mapping from TAB/CERT outputs or current four-level policy to NORMAL/HIGH/CRITICAL.
- Do not send/log whole documents externally; no persistence/alert creation from A1 evidence.

## Frozen datasets, artifacts and completed history
- Phases 0–6 + NLP follow-up + DS1–DS3 complete at documented bounded acceptance.
- Detailed historical reports: `docs/implementation/phase0/` through `phase6/`, `nlp-followup/`.
- DS1: `docs/implementation/document-sensitivity/report.md`, taxonomy-and-annotation.md, dataset-research.md.
- DS2/DS3: same directory, ds2-report.md, ds3-report.md and sanitized adjacent JSON evidence.
- Original Flask source `/home/sohaib/Downloads/AI-DLP-Agent`; 19 preserved files in legacy/downloaded_flask/.
- Actual CERT r4.2/answers archives and README in `/home/sohaib/Downloads/`; `.local/cert_paths.json` ignored.
- Stores/features/models: ignored `research/local/`; preserve strict cohort and known-user experiments separately.
- CERT phase6: 978908 events; 95930 full windows; original test 11753 / 8 positives, poor precision.
- Strict text cohort 54763/0/0; every later eligible user already seen; never weaken identity controls.
- Separate known-user test 10553 / 8 positives: numeric/text/combined precision .002198/.50/.074074;
  recall .125/.125/.25, AP .007826/.154422/.167069; offline/shadow only, no deployment claim.
- TAB pinned upstream 558e09e26d6b36f5f78440074e6a233946d98bd9; MIT with notices retained privately.
- Private TAB source: research/local/document_sensitivity/tab_ds2/; no new acquisition/training needed.
- Frozen manifests/models/evaluation: ds2_prepared_v2/, ds2_models_v2/, ds2_evaluation_v2/ under same root.
- Diagnostics: ds3_diagnostics_v2/; all 1268 documents accounted for, 577 used/681 unreviewed/10 quarantined.
- Frozen documents 326/124/127, spans 22939/6810/6713; 325/124/125 families, no cross-split family overlap.
- Selected supplied-span macro/micro F1 .776293/.885595; legal-domain subset, no detector sensitivity claim.
- DS2 task/version `tab-supplied-span-ds2-v1`; TF-IDF + LinearSVC, raw uncalibrated margins.
- Selection pin f820f6eb6c0656b0aad22407cf75665d2deeaf20b95cbc679b075a81604b7477.
- Runtime artifact requires recorded Python 3.14.4/sklearn 1.9.1/NumPy 2.5.3/joblib 1.6.0; explicit failure otherwise.
- DS3 reports 221 isolated/22 Flask tests; all 13 canonical frozen artifacts and DS2 files preserved.
- GitHub checkpoint 22dc822 CI 37768161104 freshly observed success in A1 audit.
- pypdf CI omission fixed historically: requirements-dev.txt includes requirements-research.txt; no change needed.

## A1 acceptance and verification commands (repository root)
- Supported candidates must have valid Unicode code-point offsets, category, method, redacted evidence/limits.
- Validate email syntax and supported IBAN structure/checksum; CNIC shape/credentials remain unconfirmed candidates.
- Bound inputs/results; reject malformed/oversized inputs; no TAB model call or policy/risk output.
- Synthetic fixtures test contracts only; corpus P/R/F1 belongs to B, never infer coverage from fixture passes.
- Verify actual blank CLI leaves labels null; record missing decisions/provenance and reviewer instructions.
- Reuse canonical verifier: scripts/verification/ds2_frozen_preservation.py; never substitute feature file hashes.
- Snapshot private DS2/DS3 files read-only; preserve historical reports and all existing application trees.
```bash
.local/phase0-venv/bin/python -B -m pytest -q tests/test_content_detection.py -p no:cacheprovider
OPENBLAS_NUM_THREADS=1 .local/phase0-venv/bin/python -B scripts/verification/phase0_upstream_baseline.py --report .local/phase-a1/regression.json --log .local/phase-a1/regression.log
.local/phase0-venv/bin/python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --require-no-skips --report .local/phase-a1/flask.json
.local/phase0-venv/bin/python -B scripts/verification/ds2_frozen_preservation.py --output research/local/document_sensitivity/phase_a1_frozen.json
python3 -B scripts/verification/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output .local/phase-a1/live.json --compare docs/implementation/phase0/phase0_preservation_before.json
git diff --check
git diff --cached --check
wc -l DATASHIELD_IMPLEMENTATION.md
git push origin feat/cert-ml-nlp
git ls-remote origin refs/heads/feat/cert-ml-nlp
gh run list --branch feat/cert-ml-nlp --limit 3 --json databaseId,headSha,status,conclusion
```
- Stage new Python/tests before isolated runner: it copies tracked/index-listed Python source only.
- Dependencies unchanged; use existing `.local/phase0-venv/`; clean dependency check if configuration changes.
- If push fails retain local checkpoint, record error/recover via `git push origin feat/cert-ml-nlp`.

## Known limitations and human actions
- No owner-approved organizational policy/context or independently labeled organizational corpus verified.
- Existing packet declarations need container provenance/timestamps/span-export validation before C training.
- Reviewer identities, authorization and blindness require external governance; code cannot prove them.
- Pilot is guide-development only, excluded from final test; assess required later counts from actual evidence.
- Original proposal of 1200 documents is not an unconditional count requirement; C analyzes class/family support.
- Full-release CERT fitting memory-limited; eight test positives constrain certainty; no improvement promised.
- Native Windows/physical monitors not verified here; Linux extraction uses POSIX resource limits.
- Local upload test server does not prove general browser interception; supported channel claims stay narrow.
- Existing npm vulnerabilities and Starlette warning remain historical; no unrelated dependency upgrades.

## A1 verified results
- Evidence: docs/implementation/phase-a1/report.md, label-readiness.md and verification.json.
- 66 detector checks; 287 isolated full-suite and 22 preserved Flask passes, no failures/skips; old warning.
- All 13 canonical frozen, 60 private files, 12 DS3-bound inputs, 6 TAB source files, 19 normalized copies match.
- Original/live 30 entries and 3 archive stat observations match; existing application/dependencies unchanged.
- Synthetic 32768-character smoke median 7.938–26.434 ms, max 34.227 ms, process peak 26.484 MiB.
- No corpus detection accuracy measured; no new model or policy; zero independent labels/pilot reviews verified.
- Inert packet CLI validated blank slots and rejection by adjudication; actual owner actions in label-readiness.md.
