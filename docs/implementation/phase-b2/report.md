# B2 — bounded detector evaluation and exhaustive-review handoff

Executed B2 only in the existing literal-tilde `DataShield~` checkout, branch
`feat/cert-ml-nlp`, from `86719f8ddd81cd9c056cb87ce6de7da5ab429b47`.
Initial worktree/index were clean; fresh remote HEAD matched that checkpoint and
exact-SHA GitHub Actions run 37797706716 succeeded. No subsequent legitimate
changes were discarded. No applicable AGENTS.md was found in checkout/ancestors.
A1/A2 ingestion, fitting and recovery diagnostics were not repeated.

## Gates and fixed execution contract

The frozen A2 protocol remains byte-identical: version
`automatic-content-evaluation-b-v1`, SHA-256
`b748d50cecad815613e8fee7abe5797aabadc48ebb5b4d5715e9f688fe95dba3`.
[run-contract.json](run-contract.json) was written before scoring, pins detector
source, original manifest, population, empty TAB mapping, seed and scope. Its hash
is `7564cf4b88fd343b4823fcef8d3c6cd70c998d461cb18df46dafa5879ec2af50`.
No model, population or rule was selected/tuned from these results.

B1 manifest `automatic-span-development-b1-v1` was reloaded and its semantic
validator passed. File SHA-256:
`3bfd2e38073d6904de16c47e3f0a0bb01ddf6ca6fdc375386e199c66b6b6df5b`;
canonical payload SHA-256:
`210d34c33b6c34b98ed48a4b1e442df4df184279a7f26b9c56360a2e47abce00`.
All six original source-file hashes and pinned DS2 document metadata passed.
Train/dev source records, original and normalized text hashes, review-set digests,
consensus spans, per-category counts, dispute audits and overlaps matched the
manifest. Family reservations, exclusions and intended uses remain unchanged.
Historical test bytes were hashed mechanically; their JSON/text/annotations were
never parsed or used for scoring. No B1 population reconstruction was necessary.

| Population | Train | Validation |
|---|---:|---:|
| Release-reference eligible documents / families | 326 / 325 | 64 / 64 |
| Supplied release annotations, unclipped | 22,939 | 3,992 |
| Separately named flat nonoverlap subset | 283 | 59 |
| Documents with overlapping references | 43 | 5 |
| Documents with more than 100 reference spans | 70 | 10 |

All 127 historical test documents remain excluded. Development exclusions remain
751; 390 of 1,141 train/dev sources are release-reference eligible. Eligible
train/validation family overlap is zero. All eight contextual categories and four
structured kinds still have **zero independently exhaustive eligible documents**.
Guide exceptions, machine-assisted annotation provenance and unknown negative
coverage remain explicit; empty/unannotated text never becomes verified negative.

## Runnable work and actual results

`research/detection_evaluation.py` validates the frozen gates before running
`structured-content-detectors-v1` on raw text alone. No offsets, labels, IDs,
filenames or metadata enter the detector. `research/span_evaluation.py` implements
exact one-to-one typed and boundary matching, duplicate accounting, intact nested
gold, null denominators and whole-family percentile bootstrap (2,000, seed 42).
Release comparisons never emit FP/TN or conventional precision/F1.

The final executed private output is
`research/local/document_sensitivity/b2_evaluation_v1_final/`:
`evaluation.json`, `document-results.json`, and `span-review-pilot.json`.
The first `b2_evaluation_v1/` run is retained; final execution followed added human
validation guards and produced identical counts. [evaluation.json](evaluation.json)
contains the sanitized aggregate, actual execution source hashes, output hashes,
strata and resources. No private document rows or review content are published.

| Actual structured execution | Train | Validation |
|---|---:|---:|
| Available full source-JSON documents | 326 | 64 |
| Characters processed | 1,898,512 | 332,581 |
| Returned / pre-cap candidates | 0 / 0 | 0 / 0 |
| Exact matches to released annotation boundaries | 0 / 22,939 | 0 / 3,992 |
| Unmatched predictions awaiting review | 0 | 0 |
| Prediction truncations / duplicate predictions | 0 / 0 | 0 / 0 |

All four kinds returned zero candidates. The **cross-ontology exact-boundary
diagnostic** is 0% in both partitions; conditional family-bootstrap intervals are
[0,0], with 2,000 valid replicates. Flat, overlapping and gold-over-cap strata
remain separately reported with every gold annotation intact. This diagnostic is
not four-kind recall or eight-class end-to-end performance: TAB has no exhaustive
email/CNIC/IBAN/credential annotations, and no identical structured-kind-to-TAB
mapping is approved. Typed annotated-span recovery and category agreement are
**unavailable**, not zero. Empty predictions do not prove any document benign.

The independent lane is **unavailable** on real text: zero exhaustive reviews,
no confirmed natural negatives, and no independent P/R/F1 or document error rate.
`research/independent_span_evaluation.py` is runnable after genuine completion of
the fixed private pilot. It validates the entire authorized digest-bound packet
before inference, retains a separately versioned review receipt, computes four-kind
span/document metrics and family intervals, and leaves contextual scoring null.
It preserves B1 eligibility. The actual blank-packet invocation was rejected and
wrote no independent result. Code can validate declarations, not prove actual
reviewer independence or authorization.

## Contextual detector and artifact boundary

Actual package discovery in Python 3.14.4 found no `spacy`, `en_core_web_sm`,
`transformers`, `torch` or `stanza`. No pinned automatic contextual artifact/model
was selected or available in the existing research artifact directories. Contextual
load, inference, dependency compatibility, cold load, RSS limits and category
mapping gates therefore **did not pass** and were not simulated.

The existing DS2 `entity.joblib` and `context.joblib` remain supplied-span
TF-IDF/LinearSVC classifiers; `ml/supplied_spans.py` requires caller-provided
offsets and classifies their slices. Context features do not make the latter a
span detector. Selection pin remains
`f820f6eb6c0656b0aad22407cf75665d2deeaf20b95cbc679b075a81604b7477`;
canonical preservation verified their integrity. Neither was deserialized,
reclassified, rescored against test or used as an automatic baseline.

[A2's official-source assessment](../phase-a2/report.md#local-contextual-ner-feasibility)
records the conditional spaCy en_core_web_sm 3.8.0 candidate: English, MIT model
metadata, spaCy >=3.8,<3.9, 18 native labels lacking TAB CODE/DEM/MISC, nonoverlapping
token entities. It remains metadata-only, uninstalled and unselected. No local
license/artifact/dependency/offset compatibility claim is made. Shared entity names
do not establish identical scope. All TAB mappings remain unsupported or ambiguous.
For any future contextual scoring, preregister an actual artifact/source/version,
hashes, license notices and native/identical ontology contract, then validate CPU
load/inference under frozen 2 GiB /5 CPU s /8 wall s per-input bounds and 60 s load.
No large model download, training or dependency upgrade was attempted.

## Human work, unavailable strata and resources

[human-span-review.md](human-span-review.md) specifies the actual private packet,
full twelve-target scope, two blind reviews, separate adjudicator, unresolved
document exclusion, gold locking and subsequent unmatched-prediction audit.
The 12-document/12-family selection is a minimal **guide pilot**, not an asserted
adequate twelve-category evaluation or final holdout. All slots remain null.
Counts/ambiguity/interval support must determine the next preregistered natural
population; final-test families must be new and independently held.

No real authorized organizational-sensitivity reviews, owner-confirmed business
confidential stratum, structured natural target positives/negatives, unsupported
language labels or original source containers exist for this evaluation.
Original-container end-to-end and policy metrics remain unavailable. Span
annotations/permission are separate from owner-approved organizational policy and
document-level sensitivity labels. Native Windows remains a separate task.

[synthetic-checks.json](synthetic-checks.json) records **13 actual extraction
bridge fixtures**, six complete extractions plus explicit partial/unavailable
inputs: public contact, inert assignment, financial prose, contextual entities,
unsupported-language text, DOCX, encrypted/scanned/malformed PDF, malformed TXT,
oversized, truncated and unsupported files. Three positive functional fixtures
returned a candidate; no organizational sensitivity or automated blocking occurred.
These are code contracts, not performance measurements on natural target data.

Final structured import: 5.470 ms. Warm inference on 390 common inputs: median
1.576 ms, empirical p95 4.026 ms, max 5.752 ms; max per-document CPU 5.754 ms.
Harness wall/CPU before write: 6.359/6.356 s; peak process RSS 166.137 MiB;
2,231,093 characters, one worker/thread. Source parsing/validation/bootstrap are
included in whole-harness resources. Contextual resources are **skipped**, not
passed. Concurrent regression checks and host conditions preclude general speed
claims. Synthetic extraction wall 2.146 s; parent peak RSS 47.453 MiB is not an
aggregate subprocess-memory measurement.

## Verification, preservation and publication

[verification.json](verification.json): 118 targeted tests passed (33 new B2
synthetic contracts plus existing B1/detector guards); isolated supplemental
Python regression 342 passed, nine socket-restricted API tests explicitly
deselected, one existing warning; preserved Flask 22 passed. No weakened tests,
new dependencies or changes to application/frontend/workflow/enforcement code.
The local socket blocker was already established in A2; no repeated hanging
FastAPI diagnostics. Full exact-SHA GitHub CI remains the complete regression gate.

All **13 canonical artifacts** passed the existing canonical payload verifier.
All 69 pre-existing private files, including four interrupted partial downloads,
match the pre-B2 snapshot. Original DS2 splits, models, frozen results, all
historical reports, policies, application interfaces and protocol are unchanged.
Original/live baseline: 30 entries plus three archive stat observations unchanged;
no unnecessarily repeated archive rehash, monitor, database or model job restart.
Evidence is retained under ignored `.local/phase-b2/`; no datasets, review content,
binaries, live databases, secrets or environments are staged.

Publication: source commit/normal push and exact-SHA CI receipt pending. If blocked,
retain the commit and run `git push origin feat/cert-ml-nlp`; never force-push.

B2's runnable harness, bounded structured evaluation and human handoff are complete;
independent natural and contextual metrics remain blocked as specified above.
**Stop B2. Next phase: C1 only**, analyze the separately authorized organizational
pilot if supplied and strengthen training/export provenance validation; record
missing policy/context/review gates explicitly. Do not start C2 fitting. Pending
span human reviews and contextual runtime can be resumed only as separately
authorized gate work, using the exact private files and commands in the handoff.
