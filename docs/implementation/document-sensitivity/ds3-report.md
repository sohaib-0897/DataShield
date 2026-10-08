# DS3: frozen evaluation diagnostics and optional supplied-span advice

Executed DS3 only on `feat/cert-ml-nlp`, starting from clean local HEAD and fresh
remote SHA `9933e063c0783a66694474b755bdf6b76fa00a1d`. No applicable AGENTS.md was
found in the checkout, workspace or ancestors. Read implementation memory,
CONTEXT.md and the DS2 report before work. No later user changes existed to reconcile.
No acquisition, training, model selection, frozen-manifest rewrite or test retuning
ran. Original DS2 results and models remain intact. Stop after DS3.

## Corpus accounting

The 1,268 source documents are **not** 1,268 supervised benchmark documents.
The official source split is 1,014 train / 127 dev / 127 test. Review metadata is
highly asymmetric: all 686 documents without quality-reviewed annotations are
in official training. Thus this benchmark conditions on released human review;
it does not measure performance over the full source population or random
corporate documents. Human corrections to machine-assisted annotations are not
new independent organizational sensitivity labels.

`research.tab_diagnostics` verifies source hashes against committed DS2 evidence,
original-record hashes against frozen document entries, and reconstructs every
eligible reviewed unanimous span to compare its complete record against the
unchanged frozen manifest. Every document gets exactly one reason in an ignored
private ledger; none is silently unused. Frozen family priority is independently
checked against official split memberships. The original grouping/splits are reused.

| Exclusive document disposition | Official train | Official dev | Official test | Total |
|---|---:|---:|---:|---:|
| Used in frozen benchmark | 326 | 124 | 127 | 577 |
| Unreviewed, outside quarantined families | 681 | 0 | 0 | 681 |
| Quarantined, with reviewed annotations | 2 | 3 | 0 | 5 |
| Quarantined, without reviewed annotations | 5 | 0 | 0 | 5 |
| Reviewed but no unanimous spans | 0 | 0 | 0 | 0 |
| Total original documents | 1,014 | 127 | 127 | 1,268 |

The two overlapping exclusion criteria are not added twice: **686 unreviewed =
681 nonquarantined + five quarantined**. All ten quarantines are earlier material
related to official test families (seven train→test, three dev→test). DS2's
transitive subject/content/near-duplicate family controls prioritize official test;
they exclude 74 otherwise eligible training spans and 170 dev spans, not any test
documents. There are 582 reviewed documents before the five reviewed quarantines.
Every retained reviewed document has at least one eligible span.

Reviewed exact offsets must be present in every reviewed set and unanimous in
category. Presence/boundary differences discard 3,321 distinct reviewed offsets;
category disagreements discard 162. Before quarantine 36,706 spans are eligible;
244 quarantined spans leave **36,462 = 22,939 train + 6,810 validation + 6,713 test**.
Raw annotation multiplicity is not extra training support: 155,006 raw records,
108,016 within-document distinct offsets, 936 raw category disagreements,
17 duplicate-offset records (seven conflicting), 1,395 overlapping reviewed span
pairs. The original raw annotations and conflict metadata are preserved.

Frozen documents/families remain 326/325 train, 124/124 validation and 127/125 test;
cross-partition family overlap remains zero. Related documents can remain together
within test. No frozen split changed. [Aggregate accounting and metrics](ds3-diagnostics.json)
contain complete counts; `research/local/document_sensitivity/ds3_diagnostics_v2/document-accounting.json`
contains the private per-document hashes, dispositions, eligible counts and family
priority, including each of the ten quarantines. It is excluded from Git.

## Metrics and errors

DS3 joins the immutable DS2 predictions by exact hashed span ID and truth in
frozen manifest order. Both candidate confusion matrices and per-class P/R/F1
recompute identically to committed DS2 results. Average precision is retained
from the original margin-based evaluation; DS3 does not invent AP from predictions.
Validation metrics, both test candidates, majority and the narrow abstaining
email/CNIC CODE proxy remain available in the diagnostic JSON.

| System | Validation macro F1 | Test macro F1 | Test micro F1 |
|---|---:|---:|---:|
| Entity-only, selected in DS2 | .818999 | .776293 | .885595 |
| Bounded context, fixed DS2 candidate | .750880 | .737904 | .878147 |
| Training-majority DATETIME | — | .068135 | .374646 |

Context did not improve this frozen aggregate result; this is not a reason to
retune its representation on test. The existing email/CNIC proxy has zero test
coverage, so conditional precision is undefined and it is not a fair eight-class
competitor. These results cannot establish automatic entity detection.

| Selected model class | Precision | Recall | F1 | Support | Document-bootstrap 95% F1 interval |
|---|---:|---:|---:|---:|---|
| CODE | .979730 | .884146 | .929487 | 328 | .8431–.9829 |
| DATETIME | .992866 | .996024 | .994442 | 2,515 | .9910–.9972 |
| DEM | .555556 | .662021 | .604134 | 287 | .5424–.6772 |
| LOC | .818182 | .688017 | .747475 | 484 | .6925–.8018 |
| MISC | .405882 | .359375 | .381215 | 192 | .2737–.4931 |
| ORG | .929870 | .831591 | .877989 | 1,722 | .8449–.9099 |
| PERSON | .786977 | .967391 | .867908 | 1,012 | .8243–.9061 |
| QUANTITY | .769634 | .849711 | .807692 | 173 | .6619–.9085 |

Selected test confusion matrix: rows are true categories; columns predictions.

| True \ Predicted | CODE | DATETIME | DEM | LOC | MISC | ORG | PERSON | QUANTITY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CODE | 290 | 4 | 0 | 0 | 0 | 0 | 26 | 8 |
| DATETIME | 2 | 2,505 | 3 | 0 | 0 | 0 | 1 | 4 |
| DEM | 0 | 4 | 190 | 8 | 27 | 20 | 34 | 4 |
| LOC | 0 | 0 | 24 | 333 | 10 | 63 | 53 | 1 |
| MISC | 0 | 8 | 38 | 2 | 69 | 15 | 36 | 24 |
| ORG | 0 | 0 | 74 | 57 | 50 | 1,432 | 106 | 3 |
| PERSON | 0 | 2 | 9 | 4 | 10 | 8 | 979 | 0 |
| QUANTITY | 4 | 0 | 4 | 3 | 4 | 2 | 9 | 147 |

There are 768 errors. The largest confusions are ORG→PERSON 106, ORG→DEM 74,
LOC→ORG 63 and ORG→LOC 57. PERSON recall is high but 265 non-PERSON spans are
predicted PERSON. MISC gets only 69/192 correct; DEM and LOC also lose substantial
recall. Entity-only inputs cannot resolve identical strings used for organizations,
locations or personal attributes in different contexts. This is an interpretation
of aggregate category/vocabulary evidence, not newly adjudicated gold or a claim
that every individual error has the same cause. No raw legal span examples are published.

220 accepted test spans still have disagreement among **all raw** annotator sets,
even though the reviewed subset is unanimous: micro/macro F1 .450000/.349630.
Those span boundaries/categories should not be treated as externally adjudicated.
Reviewed overlapping spans likewise test caller-supplied spans, not extraction
coverage. Training classes with <=1,000 examples are CODE (765), MISC (969) and
QUANTITY (827): their 693 test spans yield micro F1 .730159, conditional macro
F1 .762819. Rare labels are not uniformly weak—CODE performs well—while broad
MISC and QUANTITY show wider intervals. No resampling/rebalancing or refitting occurred.

## Seen versus unseen entity strings

Membership is exact equality after the existing DS2 NFKC/casefold/Unicode-word
normalization, independently of class; it is not an embedding similarity test.
The 9,970 unique normalized training strings include 68 strings with multiple
training categories. Test contains 3,861 unique strings; 1,327 seen and 2,534 unseen.
Both strata touch all 127 test documents and retain their natural span prevalence.

| Test stratum | Spans | Macro F1 | Micro F1 | Document-bootstrap 95% micro F1 interval |
|---|---:|---:|---:|---|
| Full | 6,713 | .776293 | .885595 | .859797–.910754 |
| Seen in training | 3,107 | .937098 | .976505 | .964149–.987154 |
| Unseen in training | 3,606 | .702746 | .807266 | .769672–.844674 |

| Class | Seen support | Seen F1 | Unseen support | Unseen F1 |
|---|---:|---:|---:|---:|
| CODE | 57 | .938053 | 271 | .927593 |
| DATETIME | 1,447 | .999654 | 1,068 | .987413 |
| DEM | 106 | .942857 | 181 | .434368 |
| LOC | 271 | .891945 | 213 | .554974 |
| MISC | 14 | .880000 | 178 | .344214 |
| ORG | 916 | .970053 | 806 | .754310 |
| PERSON | 258 | .994220 | 754 | .830167 |
| QUANTITY | 38 | .880000 | 135 | .788927 |

All 258 seen true PERSON spans are correct, but three false PERSON predictions
remain within the entire seen stratum. Its PERSON F1 is therefore .994220;
the DS2 true-PERSON-only stratum's perfect score uses a narrower denominator.
156 test spans from 20 strings with conflicting training categories have micro
F1 .730769: 42 of these errors are LOC→ORG. Repetition alone does not resolve
contextual ambiguity. 3,860 spans use strings repeated within test; micro F1
.879016, so within-test repetition is not synonymous with training exposure.
DS2's raw vocabulary audit (4,267 strings crossing official splits) has a different
denominator from reviewed frozen training membership and is retained unchanged.

Using 2,000 bootstrap replicates and seed 42, whole test documents are resampled
with replacement; all spans from each sampled document stay together. This
preserves within-document dependence and yields span-weighted metrics. The same
weights are used for full/seen/unseen and their paired differences. The seen-minus-
unseen micro F1 gap is .169239; its 95% interval is .133150–.204047. Full macro
F1 interval is .735357–.815250; unseen macro .657615–.743703. Seen macro has a
wide .800091–.967395 interval: 113/2,000 replicates lack at least one true category.
Macro averages classes with positive truth support per replicate, consistently
with DS2; per-class undefined precision/recall stays unavailable, with valid
replicate counts recorded. This support variation limits seen macro comparisons.

Intervals are conditional on the frozen model, reviewed legal subset and document
resampling assumption. The 127 documents include 125 families, so remaining
cross-document family dependence is not fully removed. These are diagnostic
uncertainty intervals, not calibration, deployment validation, or grounds to tune on test.

English ECHR legal narratives, public PII and frequent courts/dates differ from
corporate financial, credential and business material. The benchmark cannot
measure missing entities, unknown spans, public-PII policy false alarms, whole-
document confidentiality, organizational restriction or extraction performance.

## Optional interface, implemented and disabled

Inspected FastAPI `backend/app/main.py`, its sensitivity interfaces and local model
registry before adding a separate router and `ml/supplied_spans.py`. Existing
`classify_document`/risk/scoring/ingestion/transfer/policy paths are untouched.
No database/schema/UI/monitor migration or model activation occurred. The preserved
Flask apps remain unchanged; no shadow inference runs automatically on documents.

`POST /api/v1/advisory/supplied-spans` requires the existing ADMIN/ANALYST bearer
authentication. `DATASHIELD_SPAN_ADVISORY_ENABLED` defaults to false (authenticated
calls return 404). When enabled, missing/incompatible local artifacts return 503.
Invalid requests return 422 with the existing sanitized validation response.
The existing HTTP 256 KiB body limit remains in force.

Example inert request: `{"text":"Alice","spans":[{"start":0,"end":5}]}`.
Offsets count **Unicode code points**, start inclusive/end exclusive; JavaScript
UTF-16 offsets must be converted by the caller. Text is required, at most 32,768
characters / 131,072 UTF-8 bytes; 1–100 explicit spans, each 1–4,096 characters.
Reject boolean/string offsets, reversed/out-of-bounds/empty/whitespace spans,
malformed Unicode and unknown fields. Spans may overlap; no detection is inferred.

Return category, model version, selection digest, offsets and eight clearly named
**uncalibrated LinearSVC decision margins, not probabilities**. No confidence,
NORMAL/HIGH/CRITICAL sensitivity, risk, block or policy decision is returned.
Text is neither echoed, persisted, logged nor sent externally; middleware logs
method/path/status/duration only. There is no external inference client.

Operator configuration requires trusted local `DATASHIELD_SPAN_ARTIFACT` pointing
to the existing DS2 model directory and `DATASHIELD_SPAN_SELECTION_SHA256` pinned
to `f820f6eb6c0656b0aad22407cf75665d2deeaf20b95cbc679b075a81604b7477` for this checkpoint.
Only the selected entity pipeline is supported. Before deserialization, verify the
selection pin, offline task/version/status, train/validation selection, metadata
size, model size/hash and training-contract hash/binding. Require exact recorded
Python 3.14.4 / sklearn 1.9.1 / NumPy 2.5.3 / joblib 1.6.0 compatibility. Other
environments explicitly fail; no implicit conversion/refitting is authorized.
Validate pipeline/feature types and exact eight-category order, then finite score
shape at inference. Artifact directories/pins cannot be supplied by API callers.

Lazy initialization uses a process lock and caches success **and failure** until
restart, so concurrent requests load once; each server worker has its own instance.
Configuration or artifact changes require restart. No runtime flag was enabled.
The actual frozen model replayed all 6,713 selected test predictions through bounded
explicit-span requests with zero differences; a second service lookup returns the
same instance. Synthetic fixtures verify concurrency, absent/corrupt/incompatible
artifacts, categories, offsets, authorization, disabled behavior and text-free
validation/logging. Successful endpoint testing prevents persistence access;
existing isolated regression tests verify enforcement behavior separately.

## Checks, preservation and CI dependency repair

- Isolated tracked-source suite: **221 passed**, no failures/skips, existing
  Starlette/httpx deprecation warning. Final targeted suite: **88 passed**, including
  32 new interface/diagnostic cases and actual TXT/PDF/DOCX extraction tests.
- Preserved Flask: **22 passed**, no skips, temporary SQLite/policies and mocked devices.
- All **13 frozen artifacts** match via the existing canonical feature verifier
  and whole-file hashes for other artifacts. No CERT preparation/scoring/training rerun.
- All 30 original/live hash entries, 19 preserved normalized source copies and
  three archive stat observations match. Archive stats are not full archive hashing.
- Snapshot comparison preserves every pre-existing DS2 private source/partial/
  manifest/model/evaluation file and historical report, plus frontend/legacy/agents
  trees. Only the intentional four-line router registration changes existing
  application source; new modules and environment examples are additive.
- No monitors/server, physical devices, production migrations, live DB write,
  sensitivity activation or policy/decision change. Native Windows/PostgreSQL
  runtime integration is outside the local test evidence.

GitHub DS2 run [37763602469](https://github.com/sohaib-0897/DataShield/actions/runs/37763602469)
failed with 11 extraction-test failures: `ModuleNotFoundError: No module named 'pypdf'`.
The local environment masked that dependency omission. `requirements-dev.txt`
now includes `requirements-research.txt`, installing both pypdf and python-docx
through the workflow's existing dev install; no tests are skipped or weakened.
Dependency dry-run succeeds, and all extraction tests pass locally. Published
source checkpoint `9130a96e2909ff5f09ba9ff9fec0160b9316e4a6` pushed normally and
freshly matched the remote. [GitHub CI run 37767822921](https://github.com/sohaib-0897/DataShield/actions/runs/37767822921)
completed successfully: **221 Python tests** (including extraction, no skips),
**seven frontend tests**, successful production build and CI PostgreSQL migrations.
The existing Starlette warning remains. This is separate CI evidence, not local
PostgreSQL runtime validation. The final documentation checkpoint's fresh remote
SHA and latest CI status are reported in the final handoff.

[Verification evidence](ds3-verification.json) records resources, snapshots,
interface replay, checks and prior CI observation; [frozen preservation](ds3-frozen-preservation.json)
records canonical hashes. Implementation memory is strictly below 200 lines.
Only source/tests/configuration and aggregate documentation are committed; private
text, per-document ledger, models, databases, datasets, environments and credentials
remain ignored. Publication is a normal branch push, with fresh remote SHA equality;
final commit SHA and actual latest CI status are supplied in the final handoff.

Exact executed commands from the repository root (outputs are immutable/new):

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /usr/bin/time -v -o .local/ds3-diagnostics-final-resource.txt .local/phase0-venv/bin/python -B -m research.tab_diagnostics --source research/local/document_sensitivity/tab_ds2 --prepared research/local/document_sensitivity/ds2_prepared_v2 --models research/local/document_sensitivity/ds2_models_v2 --evaluation research/local/document_sensitivity/ds2_evaluation_v2 --output research/local/document_sensitivity/ds3_diagnostics_v2
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /usr/bin/time -v -o .local/ds3-regression-resource.txt .local/phase0-venv/bin/python -B scripts/verification/phase0_upstream_baseline.py --report .local/ds3-regression.json --log .local/ds3-regression.log
DATASHIELD_JWT_SECRET=synthetic-test-jwt-secret-32-characters DATASHIELD_AGENT_KEY=synthetic-test-agent-secret-32-characters DATABASE_URL=sqlite:// OPENBLAS_NUM_THREADS=1 /usr/bin/time -v -o .local/ds3-targeted-resource.txt .local/phase0-venv/bin/python -B -m pytest -q tests/test_span_advisory.py tests/test_tab_diagnostics.py tests/test_tab_ds2.py tests/test_document_sensitivity_phase1.py tests/test_document_research.py -p no:cacheprovider
/usr/bin/time -v -o .local/ds3-flask-resource.txt .local/phase0-venv/bin/python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --require-no-skips --report .local/ds3-flask.json
/usr/bin/time -v -o .local/ds3-live-resource.txt python3 -B scripts/verification/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output .local/ds3-live.json --compare docs/implementation/phase0/phase0_preservation_before.json
/usr/bin/time -v -o .local/ds3-frozen-resource.txt .local/phase0-venv/bin/python -B scripts/verification/ds2_frozen_preservation.py --output research/local/document_sensitivity/ds3-frozen-check.json
.local/phase0-venv/bin/python -m pip install --dry-run -r requirements-dev.txt --report .local/ds3-dependency-resolution.json
git diff --check
git diff --cached --check
wc -l DATASHIELD_IMPLEMENTATION.md
git push origin feat/cert-ml-nlp
git ls-remote origin refs/heads/feat/cert-ml-nlp
gh run list --branch feat/cert-ml-nlp --limit 4 --json databaseId,headSha,status,conclusion,name
```

Initial diagnostic v1 is retained privately; v2 adds explicit quarantine family
priority counts, with identical predictions/metrics/bootstrap intervals. Source
model inference replay was an isolated local inline Python command loading the
same pinned model, joining frozen entities in batches of 100 with explicit
offsets and asserting all predictions equal; its aggregate result/resources are
recorded in verification JSON. It fit nothing and saved no text or new model.

## Human-label blocker and exact next action

Organizational sensitivity remains **BLOCKED**: no independently reviewed
organizational label corpus was added. TAB categories do not map to DS1 document
categories or NORMAL/HIGH/CRITICAL. Existing sensitivity interfaces remain separate
and cannot be validated by rule labels, CERT outcomes, TAB labels or synthetic tests.

Owner's exact next action is unchanged: supply an authorized de-identified
100-document blind-review pilot plus approved versioned policy and release/
audience/harm context, original-container provenance and family/version relations,
authorization/retention terms, two independent reviewers and a third adjudicator.
Use the DS1 blank-packet workflow and [DS2 human annotation packet](ds2-human-annotation-packet.json).
Unknown labels remain null; freeze the guide after pilot review before any larger
independently supervised corpus or new sensitivity training. Stop after DS3.
