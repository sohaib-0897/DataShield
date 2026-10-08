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
- B2 only, clean start 86719f8ddd81cd9c056cb87ce6de7da5ab429b47; fresh remote matched.
- Exact starting CI 37797706716 success; no subsequent staged/uncommitted user changes found.
- No applicable AGENTS.md found in checkout/ancestors; original A2 protocol byte-identical.
- B2 runnable harness/structured evaluation/human handoff COMPLETE; natural/contextual metrics BLOCKED.
- Source commit and normal push pending; exact-SHA complete CI pending (local socket restriction retained).
- Details: `docs/implementation/phase-b2/report.md`, evaluation.json, verification.json, synthetic-checks.json.
- Frozen run contract automatic-content-b2-run-v1 pins source, manifest, seed and scope before scoring.
- B1 automatic-span-development-b1-v1 verified: file/payload/source/reference/coverage/family gates passed.
- Authoritative B1: `research/local/document_sensitivity/b1_development_v1_final/manifest.json`.
- File SHA 3bfd2e38073d6904de16c47e3f0a0bb01ddf6ca6fdc375386e199c66b6b6df5b; unchanged.
- Reference train/validation: 326/64 docs, 325/64 families, 22939/3992 spans; eligible family overlap 0.
- Flat subset 283/59; overlaps 43/5; gold-over-cap 70/10 retained; original DS2 populations unchanged.
- Excluded: 751 development sources and all 127 historical test docs; test bytes hashed, JSON never parsed.
- Independent exhaustive eligibility still ZERO for eight contextual categories and four structured kinds.
- Structured raw-text detection actually ran on all 390 eligible docs /2231093 characters: ZERO candidates.
- Cross-ontology exact-boundary diagnostic: 0/22939 train, 0/3992 validation; not four-kind recall.
- Typed annotation recovery/category agreement null: no identical TAB mapping; unmatched predictions unreviewed.
- No independent P/R/F1, confirmed negatives, policy metrics or original-container end-to-end metrics claimed.
- Final private outputs: `research/local/document_sensitivity/b2_evaluation_v1_final/`; first run preserved.
- `research/detection_evaluation.py`: pinned inputs and aggregate release-boundary/resources/strata evidence.
- `research/span_evaluation.py`: exact typed/boundary lanes, null metrics, family bootstrap, no reference FP/F1.
- `research/independent_span_evaluation.py`: runnable fixed pilot scoring after real exhaustive review gate.
- Contextual gate BLOCKED: no selected pinned NER artifact; spacy/model/transformers/torch/stanza absent.
- TAB entity/context models classify SUPPLIED spans; preserved, never loaded as detectors or test-rescored.
- Contextual source/license/ontology metadata stays conditional; load/inference/runtime/offset checks SKIPPED.
- Actual blank human packet: final output `span-review-pilot.json`, 12 validation docs/12 families, all null.
- `docs/implementation/phase-b2/human-span-review.md` gives exact private files/schema/commands.
- Pilot is guide development only; custodian permission, two blind full-target reviews, third adjudication missing.
- Missing natural support determines later preregistered evaluation size; final new holdout must be independent.
- Organizational policy/context/labels remain separate from span annotations and permission; none fabricated.
- Checks: 118 targeted +342 supplemental Python (9 socket-restricted deselected) +22 Flask pass, one old warning.
- Actual extraction bridge: 13 synthetic cases, 6 complete; failures/partial remain unknown, no risk decisions.
- Preservation: all 13 canonical artifacts, 69 prior private files, 4 partials and 30 live entries match.
- Ignored evidence/resources under `.local/phase-b2/`; whole harness 6.359s/166.137 MiB; no general speed claim.
- No training/tuning/model selection/download, policy/enforcement, dependencies or workflow changes.
- Native Windows, real human annotations and contextual runtime remain unverified separate gates.
- Stop B2. Exact next phase: C1 only, organizational-pilot readiness and training/export provenance validation.
- C1 must record missing independent policy/context/reviews; do not start C2 training or invent approvals.
- If publication fails preserve commit; recover with `git push origin feat/cert-ml-nlp`; never force-push.

## Remaining bounded plan
| Phase | Deliverable / gate | Status |
|---|---|---|
| A1 | Audit labels/packet workflow; deterministic detection and bounded extraction bridge | complete (bounded offline), source published/CI passed |
| A2 | Contextual full-span/local NER feasibility; freeze B protocol before selection | complete bounded assessment; published/CI passed |
| B1 | Family/coverage audit and separately versioned development manifest | complete audit/manifest; published/full CI passed |
| B2 | Fixed detector/category/end-to-end metrics, failure analysis and resources | bounded harness/structured run complete; independent/contextual metrics blocked |
| C1 | Analyze independent pilot; strengthen training/export validation, or record exact blockers | next only; labels/policy pending, interface work possible |
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
