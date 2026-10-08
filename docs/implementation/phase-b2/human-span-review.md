# Exhaustive span review handoff

The private blank packet is
`research/local/document_sensitivity/b2_evaluation_v1_final/span-review-pilot.json`.
It contains full original text for **12 validation documents in 12 families**,
selected without predictions by the frozen seed-42 family-hash ordering. All
review slots, adjudication and custodian authorization are null. Keep it private;
do not put completed reviews or text in Git or external services.

This is the smallest **initial guide pilot**, not a claim that twelve documents
suffice for twelve target categories or a final evaluation. Existing release
annotations are insufficient even for verified negatives. After this pilot,
inspect actual positive/negative document and family support, ambiguity and
interval width. Freeze any subsequent natural development population and revised
scope **before** scoring it; do not enrich it using detector predictions. A final
evaluation requires new authorized families held by an independent custodian,
outside the pilot and every historically inspected test. No unconditional sample
count or general accuracy claim is justified before actual target support exists.

1. The custodian verifies permission to review the release text, source/container
   provenance (original containers are absent here), reviewer identities and
   independence. Copy the blank packet to a **new** private directory such as
   `research/local/document_sensitivity/b2_human_reviews_v1/packet.json`; preserve
   the original. Record the authorization reference in `custodian_authorization`.
2. Use [span-review-scope.json](span-review-scope.json), whose digest is frozen in
   [run-contract.json](run-contract.json). Review **all twelve targets** across the
   full digest-bound text. The eight contextual categories include an explicit
   pilot extension for release-guide omission exceptions. They do not inherit
   exhaustive labels from TAB. The four structured kinds identify literal shapes
   and explicit assignment values; they never assert issued identity, real
   account, valid secret or confidentiality. Use human review and independent
   IBAN checks, never the detector output as gold.
3. Provide two separate blind copies to different authorized reviewers. Neither
   sees the other review, released annotations or model predictions. Preserve both
   originals. Each uses original Unicode code-point `[start,end)` offsets; retain
   overlaps/nesting and every annotation, including more than 100. Explicit `[]`
   denotes absence **only after** all twelve targets have been exhaustively
   checked. Unknown scope/presence/type/boundary or incomplete scan is unresolved,
   never a confirmed negative.
4. A distinct third reviewer sees the completed independent reviews, checks the
   entire text, resolves every difference, and preserves a dispute ledger. The
   compiled packet keeps both originals and the adjudication. Incomplete or
   unresolved documents block this fixed pilot; do not silently drop them or
   change membership after inspecting predictions. A changed scope/eligible
   population needs a separate preregistered version.
5. Lock and hash the compiled gold before exposing predictions. Review unmatched
   predictions separately against the full text after scoring; missing labels,
   annotation omissions and detector errors are separate outcomes. Preserve the
   initial scores and gold. Corrections require a new annotation version and a
   separately identified rerun. Released-reference unmatched predictions remain
   **unreviewed**, never automatically false positives.

Each non-null review object requires `reviewer_id`, timezone-bearing
`completed_at`, `independent: true`,
`saw_predictions_or_release_annotations: false`, the unchanged `text_sha256`,
the complete `exhaustive_targets` list from the packet, and an explicit `spans`
list of `[start,end,target]`. Use no labels for `NORMAL/HIGH/CRITICAL` here.
Adjudication also requires `review_sha256` (ordered canonical digests of the two
review objects, calculated with `research.tab_prepare.digest`),
`full_text_exhaustive_check: true`, `unresolved_disagreements: 0`, and
`disputed_spans` (sorted symmetric difference of the two exact typed span sets).
The validator checks declarations and bindings; only the custodian can verify
actual authorization, independence and completeness.

After real human completion, run from the existing checkout:

```bash
.local/phase0-venv/bin/python -B -m research.span_review \
  --packet research/local/document_sensitivity/b2_human_reviews_v1/packet.json \
  --manifest research/local/document_sensitivity/b1_development_v1_final/manifest.json

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
.local/phase0-venv/bin/python -B -m research.independent_span_evaluation \
  --packet research/local/document_sensitivity/b2_human_reviews_v1/packet.json \
  --manifest research/local/document_sensitivity/b1_development_v1_final/manifest.json \
  --directory research/local/document_sensitivity/tab_ds2 \
  --output research/local/document_sensitivity/b2_human_reviews_v1/independent-evaluation-v1.json
```

These commands reject the blank packet. The scorer validates the **entire frozen
pilot before inference**, creates a separate digest-bound independent-review
receipt, and scores four structured kinds only. It reports exact span and
document counts, null denominators, macro membership and family-cluster intervals.
There is no AP for deterministic candidates and no contextual metric without a
validated raw-text detector. Its output is conditional **guide-pilot development
evidence**, not final-test evidence, and never changes B1 eligibility or DS2.
Incomplete writes and previous outputs must be preserved; use a new output name.

Organizational sensitivity has a separate owner-approved versioned policy/context
and separate blind document-label workflow in
[A1 label readiness](../phase-a1/label-readiness.md). Span-review authorization and
entity annotations do not supply sensitivity approval or labels. C1 must examine
that separate pilot and its export/provenance gates; native Windows verification
also remains separate.
