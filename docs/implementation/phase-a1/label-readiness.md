# A1 label readiness and owner/reviewer instructions

2026-10-08. **Blocked: zero independently reviewed organizational documents verified.**
The 100-document pilot is still proposed, not independently reviewed or approved.
No authorized 100-document inventory or owner-approved policy was supplied in this
session. A blank packet is not a review. Do not fabricate reviewers or labels.

## What was checked

Read DS1 taxonomy/annotation guide, DS2 human-packet specification and DS3 report;
inspect the actual `research/document_annotation.py` preparation/adjudication code.
Bounded filename search covered checkout/private research storage, .local,
Downloads, Documents and Desktop for annotation/review/pilot/policy/label names,
excluding dependencies. Inspect nonbenchmark private JSON candidates as well.
Only `research/local/document_sensitivity/interface_fixture/blank-packet.json`
was an organizational packet candidate: AWAITING_INDEPENDENT_REVIEWS, two blank
review slots. The live legacy policy file is enforcement configuration, not an
owner-approved corpus policy/review record; it was not reused as supervision.
No claim is made about inaccessible/off-machine records or arbitrary unnamed files.
Fresh synthetic CLI validation in A1 makes a new blank packet, never human labels.

## Minimum owner decisions/actions

1. Provide an authorized, de-identified 100-document **pilot** inventory in private
   ignored storage, with source/family IDs, document versions/chunk parents,
   original-container SHA-256, organization, authorization/retention reference and
   withdrawal handling. Supply only authorized documents and inert secret examples.
2. Approve a versioned organizational policy and digest plus review-time audience,
   release state, owner authority, potential harm and intended use. The existing
   DS1 NORMAL/HIGH/CRITICAL definitions are proposals, not owner approval.
3. Appoint two independent reviewers and a distinct conflict adjudicator through
   the owner governance process; record training, access authorization and blindness.
   Give reviewers the same approved context, hiding model/rule outputs, proposed
   split, other reviews and adjudication. The agent does not assign identities.
4. Confirm pilot sampling includes public contact/financial text, restricted
   examples, inert secrets, ambiguous material and extraction failures. Families
   are sampled together; mark pilot-only and exclude from final test.

The previous 1200-document proposal is provisional. After the pilot, C1 examines
actual class/family support, ambiguity and agreement to justify any further sample
size. There are currently no class counts or agreement metrics to report.

## Exact packet workflow

Reuse `research/document_annotation.py` v1 and the specification at
`../document-sensitivity/ds2-human-annotation-packet.json`. No private packet is
committed. Commands below require real authorized inputs/IDs; placeholders are not
approval, labels or executable demonstration data:

```bash
.local/phase0-venv/bin/python -B -m research.document_annotation --prepare /authorized/document.docx --source-id SOURCE_ID --family-id FAMILY_ID --policy-version OWNER_APPROVED_VERSION --output research/local/document_sensitivity/annotations/blank-SOURCE_ID.json
.local/phase0-venv/bin/python -B -m research.document_annotation --adjudicate research/local/document_sensitivity/annotations/reviewed-SOURCE_ID.json --output research/local/document_sensitivity/annotations/accepted-SOURCE_ID.json
```

Use a fresh destination each time. Preparation sets both reviews' `reviewer_id`,
`categories`, `organizational_level`, `context` to null and makes no label. Record
private container provenance separately: packet digest binds extracted Unicode
text, not the original container. Preserve failed/partial extraction as an excluded
coverage outcome; do not call it NORMAL or use a partial packet for whole-document labels.

Give each reviewer a separate copy with one assigned review slot; keep the other
review hidden. Store the original individual copies and a custodian merge trail.
Each review needs the actual reviewer ID, independent_human origin, timestamp,
categories (explicit [] only after reviewing), level or null, uncertainty/reason,
and evidence offsets bound to the packet text SHA-256. Store timestamp/span/audit
fields alongside v1 reviews; v1 does not validate/export these governance fields.
For any policy level, including NORMAL, and BUSINESS_CONFIDENTIAL, context requires
owner_review_id, matching policy_version, authorized_audience, release_status and
harm_rationale. Missing context remains unknown, never implicitly NORMAL.

Merge completed reviews privately without deleting originals. Differences require
a distinct third reviewer, reason and owner clarification; unresolved items abstain.
Review a sample of agreements and disputed CRITICAL judgments; freeze a new guide
version only after owner review. A changed guide requires fresh experiment/splits.
Hold future final-test documents with a separate custodian, outside guide development,
model-assisted labeling and training. Audit duplicates/near-duplicates/families
before splitting. No actual holdout has been created from absent documents.

## Remaining interface/governance gaps

V1 checks text digest, complete extraction, declared human origin, distinct reviewer
IDs, taxonomy, matching policy context and disagreement resolution. It does not
prove authorization, reviewer independence/blindness or validate review timestamps,
source inventory, evidence offsets, family relations or original-container hashes.
Its `training_eligible` declaration is not the C training authorization gate.
C1 must add/validate these exports and audit external provenance before training.
TAB machine-assisted entity categories, CERT attack labels, rule outputs, filename
policies, synthetic fixtures and this agent's detector candidates are forbidden
substitutes for independent organizational sensitivity supervision.
