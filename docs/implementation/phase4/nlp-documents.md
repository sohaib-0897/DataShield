# Phase 4 — CERT text study and separate document evidence

Completed bounded extraction/evidence acceptance and the real CERT text feasibility
and leakage audit. Conditional supervised text/numeric comparison is unavailable
on this prefix. No model was trained on CERT text, no genuine document sensitivity
corpus exists, and no research model or extractor is activated in the application.
Phase 3 prerequisite was pushed and freshly verified at
`63595ab35986bdc495ed916f24735312f559752a` before this phase.

## CERT text is an attack-detection task

The supplied release says HTTP/email/file content is synthetic topic keywords,
with a hex header for file content. These are not extracted document bodies or
sensitivity labels. `research/text_study.py` uses content only, strips file hex
headers, normalizes Unicode/whitespace, removes account/PC identifiers, opaque IDs,
addresses and URLs, and retains alphabetic topic words. Event IDs, identities,
resources/recipient addresses, answer metadata, LDAP and scenarios never enter
TF-IDF. Whole source events remain unchanged in the read-only research store.

A frozen Phase 2 feature fingerprint and the Phase 3 numeric report must match,
including exact chronological partition audit. Derive text from the **same event
keys** and require the source-store hash to match. No arbitrary text population is
presented as a comparison to the numeric benchmark.

Leakage controls are stricter for text: later partitions exclude any user already
observed in an earlier partition, and any window with a normalized keyword bag
observed earlier. Bag fingerprints retain word multiplicities but ignore order,
so reordered duplicate keyword documents do not cross partitions. Missing-text
windows are also excluded. Audit incident/scenario overlap from evaluation labels;
if groups overlap, refuse a quality comparison instead of deleting malicious test
rows. No vocabulary, scaler, class weights or thresholds learn from held-out text.

Actual real-prefix findings:

| Measure | Result |
|---|---:|
| Source events | 10,000 |
| Text source events | 6,000 (file/HTTP/email) |
| Nonempty sanitized texts | 6,000 |
| Duplicate normalized keyword bags | 111 |
| Original numeric train/validation/test | 83 / 43 / 38 |
| After text leakage controls | 81 / 1 / 0 |
| Retained train/validation positive labels | 0 / 0 |

Train loses two missing-text windows. Validation loses 42 previously seen users.
Test loses 37 previously seen users and one missing-text window. No held-out text
cohort remains; no positive supervision exists even before filtering. The status
is `UNAVAILABLE`, comparison metrics are null, and no text model file is produced.
The independent study replay is identical. These are coverage constraints, not
text detection scores or evidence of superiority of either approach.

The supported pathway implements training-only TF-IDF (10,000 maximum features,
unigrams/bigrams, sublinear frequency) plus linear logistic regression, with
validation-only F1 thresholds. It requires at least two train examples/class,
both validation classes, nonempty held-out rows and disjoint incident/scenario
groups. When supported, numeric IsolationForest/logistic models are refitted on
exactly the retained text cohort and measured with the same labels, prevalence and
metric definitions. No test resampling/tuning occurs. This pathway passed a
**synthetic fixture** with training vocabulary/reload/common-population assertions;
its metrics are not included as authentic CERT results.

## Bounded document extraction and evidence

`research/documents.py` is a separate offline interface. It does not import or
change application policies/classifiers, and does not assign learned sensitivity.
Supported types: UTF-8 TXT, PDF with extractable text, DOCX paragraphs and table
cells. No OCR, attachments, macros, embedded document extraction or network fetch.

The parser runs as an isolated subprocess with Linux/POSIX CPU/address-space
limits: default input 2 MiB, text 32,768 characters, PDF 40 pages, DOCX 512 ZIP
entries/16 MiB total expanded/4 MiB per entry, five CPU seconds, 512 MiB address
space and eight seconds wall timeout. Reject unsafe/duplicate ZIP paths, symlinks,
XML DTD/entities, encrypted ZIP entries and disproportionate expansion. Reject
symlinked input paths. Detect file changes across extraction/hashing. Source files
are only read, never rewritten. Bounded full-file hashes allow up to 16 MiB
independently of extraction; oversized hashes report unavailable.

Explicit outcomes include `OK`, `EMPTY`, `UNSUPPORTED`, `ENCRYPTED`,
`SCANNED_OR_NO_TEXT`, `MALFORMED`, `TOO_LARGE`, `LIMIT_EXCEEDED`, `TIMEOUT`,
`UNREADABLE`, `UNSAFE_PATH`, `INPUT_CHANGED`, and `MISSING_DEPENDENCY`. OLE-format
DOCX reports `ENCRYPTED_OR_LEGACY_UNSUPPORTED`, since the signature alone cannot
distinguish encrypted Office packages from mislabeled legacy files. A no-text PDF
is not asserted to be scanned: the status includes both possibilities. Text-limit
success is explicitly marked truncated; absence of findings is not proof that
unextracted content has none. Windows process limits remain unverified.

Private extraction returns text to the caller. Public evidence and the CLI emit
only status, character count, truncation, hash, caller-supplied filename/hash labels
and pattern types/counts/character offsets. No raw PII values, snippets, filenames,
paths or document text are emitted. CNIC-like and email regex evidence is named
`RULE_PATTERNS`; it is not a sensitivity model or a validated accuracy claim.
Filename matching is case-insensitive by basename (including Windows path forms).
Filename and known-hash labels remain independent when extraction is unsupported,
encrypted, malformed or empty. Neither signal is overridden by absent PII.
The preserved legacy and upstream sensitivity code is unchanged.

## Commands, actual acceptance and limitations

```bash
# Already installed into the ignored isolated environment; application dependencies unchanged.
.local/phase0-venv/bin/python -m pip install 'pypdf>=6,<7' 'python-docx>=1.2,<2'
.local/phase0-venv/bin/python -B -m research.text_study --features research/local/phase2_features_v1.json --database research/local/cert_r42.sqlite --numeric-report research/local/phase3_benchmark_v1/report.json --output research/local/phase4_text_study_v1
.local/phase0-venv/bin/python -B -m research.document_acceptance --output research/local/phase4_documents_v1
.local/phase0-venv/bin/python -B -m pytest -q tests/test_document_research.py tests/test_text_research.py tests/test_behavioral_research.py tests/test_cert_features.py tests/test_cert_ingestion.py
# Redacted standalone evidence; substitute a deliberate local document path.
.local/phase0-venv/bin/python -B -m research.documents research/local/phase4_documents_v1/synthetic_documents/report.txt
```

Outputs refuse overwrite. The fixture generator writes ten synthetic documents
only into ignored research storage. Ten actual parser/status checks passed; TXT,
PDF and DOCX each produced CNIC-like/email evidence. The remaining fixtures cover
unsupported, encrypted, no-text, empty and malformed documents. Measured extraction
acceptance took 0.6278 seconds across ten documents on this machine; no throughput
or sensitivity quality is inferred. Versions: pypdf 6.19.0, python-docx 1.2.0,
lxml 6.1.3. `document_acceptance.json` contains text-free measured evidence.

75 targeted tests passed with no skips (18 document, 5 text, 8 numeric, 16 feature,
28 ingestion). Additional fixtures cover ZIP safety/expansion, PDF page bounds,
text truncation, hash/filename fallback, symlinks, timeouts, changed inputs, bounded
PII spans, vocabulary boundaries, duplicate/user/scenario leakage and unavailable
supervision. A fixture initially failed because its numeric audit still described
positive labels after the fixture changed them to zero; regenerating that fixture
prerequisite fixed it without weakening the snapshot guard. See verification for
full isolated regressions and original preservation.

Phase 4 also added 128 MiB metadata and 64 MiB feature-artifact read bounds before
materialization, and a read transaction for the research snapshot. Event count
bounds alone cannot bound large CSV fields. Boundary tests cover these guards;
Phase 2's frozen real artifact remains identical.

Remaining data prerequisites: a broader chronological CERT cohort with positives,
enough unseen-user/duplicate-disjoint held-out text, and a separate independently
labeled document sensitivity corpus. No full ingestion, OCR, real sensitive file
study, supervised CERT comparison, native Windows monitoring or PostgreSQL check
is claimed. Phase 5 is outside this request; advisory integration remains pending.
