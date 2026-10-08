# DS2/DS3 contract — planning only in DS1

No fitting, threshold selection, test scoring, policy adapter activation or
organizational validation ran in DS1. Preserve original CERT strict-cohort
results and separately named known-user experiment without rerunning either.

## DS2: corpus, frozen groups and baseline

1. Verify acquisition hashes and label provenance before reading documents for
   preparation. Preserve unmodified release files and source assignments.
   TAB is a separate provided-span semantic-type experiment; human organizational
   document categories/levels are another corpus/task/manifest. Never flatten
   them into the existing binary sensitive/not_sensitive interface.
2. Define document/source/case family, related versions and protected-subject
   grouping before splitting. All chunks, spans and annotator copies of the same
   document stay in its group. Use exact file/text and normalized-text hashes;
   audit near-duplicates with deterministic five-word shingles and Jaccard >=.8
   as a prespecified review trigger. Group confirmed related documents including
   cross-source versions. Freeze normalization and review decisions; publish
   cross-split exact/near-duplicate and family overlap counts. No metadata IDs,
   filenames, reviewer names, task protected-person identities or answer metadata
   enter predictive text. Source IDs are for grouping/provenance only. Actual
   entity text is an input to this declared span task; subject/family grouping
   must prevent memorized identities from crossing held-out boundaries.
3. Keep TAB test assignments quarantined and unchanged. Mechanical label-count
   inventory is allowed; modelers do not inspect test texts/errors for selection.
   If test overlaps train/dev families, quarantine related training/dev material
   rather than transfer test documents into training. Record exclusions. If
   leakage-free coverage or class support is inadequate, report infeasibility
   and define a separately versioned group split; do not silently replace the
   official protocol or manufacture negatives.
4. TAB annotator copies are competing human judgments, not repeated training
   samples. Use quality-review metadata and source instructions to define a
   prespecified canonical set; unresolved differences require human adjudication
   or abstention. Report coverage/agreement. A machine choice is not new gold.
5. Freeze train/validation/test manifests, groups, provenance, task, label schema
   and software versions before fitting. For organizational examples, use the
   family-level natural holdout in the labeling guide; pilot/enriched examples
   stay outside held-out evaluation. No class balancing of validation/test.
6. CPU baseline: sparse TF-IDF word unigrams/bigrams plus character 3–5 grams
   (bounded maximum features, float32 where supported), logistic regression or
   a linear margin classifier. Begin with one declared configuration (e.g.
   40k word + 40k character features, minimum document frequency 2, L2/C=1,
   deterministic seed). Select vocabulary/IDF/text transforms on training only;
   a fixed tokenizer has no fitted global corpus state. Character features help
   names/code patterns but increase memorization risk, hence duplicate/family
   controls. Estimate memory first and cap CPU threads and rows; abort/reduce a
   separately declared training configuration if machine bounds are exceeded.
7. Train eight-class TAB provided-span semantics only where reconciled labels
   support each class. Context window and span boundaries are declared inputs;
   never include the task target or the other labels. Text-only vs span+local
   context may be a separately predeclared experiment. No claim of detection
   recall/whole-document confidentiality from oracle spans.
8. Organizational categories would require multi-label one-vs-rest classification;
   levels require separately approved context-aware supervision, with context
   fields explicitly declared and leakage-reviewed. Missing context is abstention,
   never NORMAL. Do not train either on TAB aliases, regex labels or fixtures.
9. Class weighting/sampling only on training, logged separately. Use validation
   only to select per-class thresholds, abstention settings and any hyperparameter
   choice; freeze them before test. Raw margins are scores, not probabilities.
   A calibration claim needs separate held-out calibration and reliability checks
   with adequate data. Do not publish predict_proba as calibrated by default.

DS2 completion requires actual corpus/split counts, leakage evidence, training
commands/runtime/peak memory and artifact provenance. If human organizational
labels remain unavailable, report that branch blocked and complete only the
defensible narrow task. Keep raw text, private labels, models and environments
ignored. Artifacts remain inactive.

## DS3: independent evaluation and optional advisory shadow

- Score the same eligible held-out population once with frozen settings; retain
  natural prevalence. Report per-class counts/prevalence, precision/recall/F1,
  TP/FP/FN/TN, multiclass and/or per-class confusion matrices, PR-AUC (state
  average-precision versus interpolated convention), abstention/coverage and
  document-level false alerts per 1,000 where a document alert target exists.
  Undefined metrics remain null with reasons (no positives, no negatives or no
  predictions); zero is not a substitute for undefined. Report small-sample
  uncertainty and cross-group error concentrations.
- Compare with existing deterministic detectors on compatible targets only.
  Email/CNIC detectors are not an eight-class semantic classifier; report their
  supported target coverage and abstentions separately. TAB CODE is broader than
  email/CNIC and does not make all codes credentials. For a human document
  corpus compare frozen rules on the same independently reviewed documents;
  never use rule outputs as gold or equate old four-level and new three-level
  policies. Public PII false positives deserve a separate audit.
- Error strata must cover public PII, ordinary financial reports, owner-confirmed
  business-confidential material, inert credential examples, unsupported inputs
  and extraction exclusions. TAB cannot fill missing organizational strata;
  explicitly report them unavailable. Review test errors after frozen reporting,
  preserve the test’s historical result, and use a new test for follow-up selection.
- Reproduce fits/scores from seed/manifests; reload artifacts and verify schema,
  source/split digests, provenance/software, output mapping and advisory status.
  Compare schema-safe fallback on corrupt/missing/incompatible artifacts.
- Any shadow output is separately named content categories, raw score,
  extraction coverage, source/model version and unknown policy level; original
  rule decisions remain intact. Never activate blocking, change policy, or attach
  an uncalibrated category margin to the active probability interface. Optional
  integration requires its own phase acceptance and contextual-label availability.

## TXT/PDF/DOCX handling contract

Reuse `research.documents`; do not change currently supported behavior. TXT
decoding failure is MALFORMED; whitespace-only text EMPTY. PDFs require text
layers: ENCRYPTED is unavailable, SCANNED_OR_NO_TEXT needs a separately validated
OCR pipeline (none added), malformed PDF is MALFORMED. DOCX uses bounded ZIP/XML
parsing; malformed paths/XML or expansion fail explicitly; OLE/encrypted/legacy
containers are ENCRYPTED_OR_LEGACY_UNSUPPORTED. Unsupported extensions stay
UNSUPPORTED. No failed extraction is a sensitivity-negative example.

Existing default limits: 2 MiB input, 32,768 text characters, 40 PDF pages,
512 DOCX entries, 16 MiB total expanded XML / 4 MiB per entry, 5 CPU seconds,
512 MiB address space, 8 seconds wall timeout. TOO_LARGE/LIMIT_EXCEEDED/TIMEOUT,
UNREADABLE/UNSAFE_PATH/INPUT_CHANGED/MISSING_DEPENDENCY remain explicit outcomes.
Successful truncation remains flagged; exclude it from full-document training
and organizational packet acceptance. A later chunk model must account for
partial coverage and keep every chunk/version in one source-family split.
Filename/hash rules remain independent fallback signals. No OCR, archive
framework, document sanitization or live monitor behavior is changed in DS1.
