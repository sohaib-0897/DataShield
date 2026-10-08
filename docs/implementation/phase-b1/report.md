# B1 — family, coverage and development-manifest audit

Executed B1 only in the existing `DataShield~` checkout on `feat/cert-ml-nlp`,
starting clean at `a038b0c3a5169cb9af968746626017bcaa376b54`. Fresh remote SHA
matched, and exact-SHA CI 37793680451 was freshly verified successful through the
GitHub connector. No applicable AGENTS.md was found in the checkout/ancestors.
No subsequent staged/uncommitted work needed reconciliation. Read implementation
memory, current CONTEXT, the A2 report and the frozen B protocol before auditing.

## Scope and artifacts

`research/detection_manifest.py` creates a private, metadata-only ledger with all
1,268 source documents accounted for; it never exports text, matched values, raw
source/subject/reviewer identifiers or training examples. It performs no fitting,
tuning, model inference/selection, acquisition or enforcement change. Native Windows
and contextual-model runtime validation remain separate tasks.

Version: **`automatic-span-development-b1-v1`**. Authoritative ignored outputs:

- `research/local/document_sensitivity/b1_development_v1_final/manifest.json`
- Same directory: `audit.json`; public aggregate evidence: [audit.json](audit.json).
- Manifest file SHA-256: `3bfd2e38073d6904de16c47e3f0a0bb01ddf6ca6fdc375386e199c66b6b6df5b`.
- Canonical payload SHA-256: `210d34c33b6c34b98ed48a4b1e442df4df184279a7f26b9c56360a2e47abce00`.
- Source protocol remains byte-identical: `automatic-content-evaluation-b-v1`,
  SHA-256 `b748d50cecad815613e8fee7abe5797aabadc48ebb5b4d5715e9f688fe95dba3`.

The earlier `b1_development_v1/` candidate is preserved as diagnostic evidence and
is superseded by the explicitly named final output, which adds per-target scope and
software digest declarations. Do not select artifacts by filename presence alone.
Reload verification validates payload/file hashes, target declarations, ontology,
eligibility, split isolation and equality of the persisted aggregate audit.

Each document records hashed source ID, record/text/source-file provenance,
historical and B1 family IDs, original/reserved/development partitions, quarantine,
all exclusion reasons, review-set digest/count, eight separate coverage entries,
unaltered reference counts, overlap/cap strata and text bounds. Container digest
is null because original PDF/DOCX containers are unavailable: source JSON text is
complete for this text-only release audit, not proof of original parser coverage.
Source revision, guideline, software, ontology, configuration and protocol digests
are recorded. Model artifact digest is explicitly null; no model was selected.

## Family and duplicate controls

All six pinned TAB files verify their sizes/Git blob IDs/SHA-256 before use. Train
and dev alone are parsed. Each source record, text hash, review count and unanimous
span count must match the frozen DS2 document ledger, whose canonical file hash is
`c090b12b6a52e0d2d029e3345ee025d52348e7c4e35d7b83ca9820e82f6bf3ae`.
Historical test text/annotations are never parsed in B1; prior pinned family metadata
supplies all previously audited historical-test links and raw text hashes.

Fresh train/dev grouping uses source IDs, exact normalized text, protected task and
applicant identity, plus exhaustive length-filtered five-word-shingle Jaccard >=0.8.
The length filter cannot exclude a pair meeting that threshold. Transitive closure
conservatively merges these relations with the frozen all-source graph and raw-text
duplicate links. No prediction, class balance or performance result affects grouping.

- All-source families: **1,249**; seven span multiple official source partitions.
- Raw exact duplicate links: **0**; fresh normalized exact duplicate links: **0**.
- Fresh train/dev near-duplicate pairs: **2**; subject edges: **14**.
- Historical test-related development exclusions: **10**, seven train/three dev;
  all ten original DS2 quarantine entries remain recorded and excluded.
- Eligible train/validation family overlap: **0**. Official dev wins related
  train/dev families; historical test wins all related development material.

Version identity is auditable only within the pinned release and known family graph.
External case versions/container relations are not supplied, so no claim of complete
external-version discovery or an independent new holdout is made.

## Counts and eligibility

Two eligibility tracks are explicitly different: conditional **TAB released-reference
matching under its legal anonymity guideline**, and **independent exhaustive target
detection**. The latter has zero eligible documents; the former is a development
reference, not independent gold or an untouched final test.

| Quantity | Train | Official dev → validation | Historical test |
|---|---:|---:|---:|
| Source documents | 1,014 | 127 | 127 |
| Released-reference eligible documents | 326 | 64 | 0 |
| Eligible families | 325 | 64 | 0 |
| Excluded source documents | 688 | 63 | 127 |
| Unclipped reference spans | 22,939 | 3,992 | unavailable in this audit |
| Flat nonoverlap reference subset | 283 | 59 | 0 |
| Eligible documents over 100-span result cap | 70 | 10 | not inspected |

Total: **390 released-reference eligible; 751 train/dev exclusions; 878 exclusions
across all source partitions**. All 127 historical test documents stay outside B1.
The flat subset excludes another 43 train/five validation overlap documents, without
flattening annotations or removing spans from the overlap-aware ledger. The 100-result
cap does not select the population: future capped output must retain all reference
spans in the recall denominator and report the capped stratum.

Nonexclusive exclusion counts: 686 documents lack reviewed annotations, 61 dev
documents have reviewed presence/boundary/category disputes, ten development
documents touch test families and 127 are historical test. Reasons overlap. Exclusive
accounting: 390 eligible +681 unreviewed +60 disputed +10 test-family +127 historical
test =1,268. No eligible reviewed source exceeds the input text/UTF-8 bounds.

Original DS2 populations **326/124/127**, manifests, models and results remain intact.
B1 excludes whole disputed dev documents, so its new validation population is 64;
it does not replace DS2's legitimate supplied-span consensus task or historical score.

## Per-target annotation coverage

The pinned guide instructs correction/addition of missed preannotations and includes
human quality review. However, its Exceptions section permits omission of legal
professionals' titles/professions and parts of generic legal references, including
years. Review metadata proves release status, not independent exhaustive coverage.
Agreement on recorded spans cannot prove that all target occurrences were recorded.

| Target | Train reference spans | Validation reference spans | Broad target completeness |
|---|---:|---:|---|
| CODE | 765 | 153 | Not independently verified; no specific structured-kind labels |
| DATETIME | 8,346 | 1,336 | Deliberate generic legal-reference year omissions allowed |
| DEM | 1,271 | 230 | Deliberate legal-professional title/profession omissions allowed |
| LOC | 1,418 | 247 | Not independently verified beyond guideline scope |
| MISC | 969 | 154 | Person-related scope; generic legal-reference parts may be omitted |
| ORG | 6,158 | 1,106 | Not independently verified beyond guideline scope |
| PERSON | 3,185 | 619 | Not independently verified beyond guideline scope |
| QUANTITY | 827 | 147 | Meaningful quantities; no exhaustive financial-content review |

These are span reference counts, not counts of independently reviewed negative
documents. Every target/document has `unannotated_text_confirmed_negative=false`
and `independent_exhaustive_coverage_verified=false`. No independently exhaustive
contextual category has an eligible population. No target-specific exhaustive
annotations exist for email_address, cnic_like, iban or credential_assignment;
all four independent structured-kind populations are **zero**. TAB CODE cannot be
aliased to credentials/CNIC/IBAN, nor QUANTITY to financial confidentiality.

Conditional future release-matching P/R/F1 must be named release-relative: an
unmatched prediction is unmatched to the reference, not confirmed incorrect natural
text. Broad detection accuracy, true-negative/FPR claims and organizational levels
remain unavailable. No P/R/F1 or category accuracy was calculated in B1.

Exact annotation action: define category/kind scope without implicit guideline
exceptions; have authorized independent reviewers exhaustively annotate full, digest-
bound source text, explicitly review absent targets and resolve boundary/presence/type
disputes. Preserve individual reviews, review provenance, family/container-version
links and adjudication. Human reviewers must handle intentional omissions and
overlaps; this agent did not add/adjudicate labels. Use separate family-safe final
holdout custody outside guide development and historical inspected test. Organizational
levels additionally require the already specified owner-approved policy/context.

## Verification and preservation

19 targeted tests cover historical/transitive test quarantine, train/dev priority,
exact/near version grouping, whole disputed-document exclusions, unreviewed/zero-span
coverage, nonoverlap/cap handling, privacy, corrupt manifests, missing targets/ontology
and preservation of existing outputs. Supplemental isolated regressions passed 306
tests with nine known socket-restricted FastAPI tests explicitly deselected; final
three additional guards passed in the 19-test targeted run. No old tests were changed.
Final exact-SHA full CI is the publication gate; results are recorded in
[verification.json](verification.json). Existing Flask fixture regression: 22 passes.

All **13 canonical frozen artifacts** match the established feature verifier;
**64 pre-existing private DS2/DS3/A2 files**, including partial downloads, are unchanged.
Original/live **30 entries** and three archive stat observations match. No datasets,
private manifest, packets, models, databases, secrets or environments enter Git.
Existing backend/frontend/agents/legacy/ML/dependencies/workflow and A2 protocol
diffs are empty. No locks removed, monitors/services started or recovery checks
unrelated to B1 repeated. Archive observations are not fresh full archive hashes.
Final audit: 16.81s wall, 412.070 MiB peak RSS on this machine; no model resources
or general inference-performance claim follows from this metadata audit.

Actual reproduction commands (new ignored output path required):

```bash
.local/phase0-venv/bin/python -B -m research.detection_manifest --directory research/local/document_sensitivity/tab_ds2 --tree research/local/document_sensitivity/tab-tree.json --frozen-documents research/local/document_sensitivity/ds2_prepared_v2/documents.json --protocol docs/implementation/phase-a2/evaluation-protocol.json --output research/local/document_sensitivity/b1_development_v1_final
.local/phase0-venv/bin/python -B -m pytest -q tests/test_detection_manifest.py -p no:cacheprovider
OPENBLAS_NUM_THREADS=1 .local/phase0-venv/bin/python -B scripts/verification/ds2_frozen_preservation.py --output research/local/document_sensitivity/phase_b1_frozen.json
.local/phase0-venv/bin/python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --require-no-skips --report .local/phase-b1/flask.json
python3 -B scripts/verification/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output .local/phase-b1/live.json --compare docs/implementation/phase0/phase0_preservation_before.json
git diff --check
git diff --cached --check
wc -l DATASHIELD_IMPLEMENTATION.md
git push origin feat/cert-ml-nlp
git ls-remote origin refs/heads/feat/cert-ml-nlp
```

## Boundary and next action

B1 audit/manifest work is complete; publication and exact-SHA CI receipt follow.
Stop before B2. **Next phase: B2 only**, fixed detector/category/end-to-end reporting,
failure analysis and resources, subject to the frozen input/reference/model gates.
First validate the final manifest/hash and per-target coverage; independent structured,
broad contextual and organizational evaluation remains blocked on the human actions
above. A compatible contextual detector/ontology must be separately preregistered and
runtime-validated before contextual scoring; none is selected here. Do not fabricate
metrics or silently widen the release-reference population to make B2 runnable.
