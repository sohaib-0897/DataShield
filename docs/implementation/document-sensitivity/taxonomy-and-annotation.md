# Task definition and independent annotation plan

DS1 decision, 2026-10-08. This is a proposed offline taxonomy; it changes no
application rules, roles, API fields, alerts, policies, or active models.

## Two separate targets

| Content target (multi-label) | Inclusion | Boundary / exclusion |
|---|---|---|
| PERSONAL_INFORMATION | Information about an identifiable person, including direct identifiers and contextual attributes | Public employee contact information still has this category. Not an automatic confidentiality judgment; anonymous aggregate statistics alone are insufficient. |
| FINANCIAL_INFORMATION | Accounts, balances, payments, compensation, financial forecasts or statements | Published annual reports belong here but may be NORMAL. Numbers, dates and TAB QUANTITY alone are insufficient. |
| CREDENTIALS | Authentication secrets: passwords, bearer/API tokens, private signing keys, recovery codes | A username/email alone is personal information, not a secret; public keys and generic discussion of passwords are not credentials. Use inert examples for annotation; never collect operational secrets. |
| BUSINESS_CONFIDENTIAL | Nonpublic organizational plans, contracts, designs or commercial material with an owner-confirmed restriction | A word such as “confidential,” a topic, a court allegation or a nondisclosure clause alone is insufficient. Requires contextual evidence. |

An empty **reviewed** category list means none of these categories found. A blank
list field (`null`) means unreviewed, never negative. Ambiguous content remains
unresolved and excluded pending review. Categories may coexist. Their presence
does not determine an organizational level.

| Proposed policy level | Owner-confirmed meaning |
|---|---|
| NORMAL | Approved for public/routine distribution under the supplied policy and audience; no additional protection in the proposed three-level taxonomy |
| HIGH | Restricted organizational distribution; unauthorized disclosure could cause material personal, contractual or business harm |
| CRITICAL | Strictly limited distribution with severe potential harm; e.g. owner-confirmed high-impact secrets or highly restricted identifiable records |
| Unknown (`null`, not a fourth model class) | Policy, release authority, audience, or impact evidence missing/ambiguous |

Example: a published financial report may be FINANCIAL_INFORMATION + NORMAL; a
public directory may be PERSONAL_INFORMATION + NORMAL. An internal personnel
file can contain the same category with HIGH/CRITICAL according to the owner’s
policy. A secrets tutorial with inert examples does not prove real credentials or
CRITICAL sensitivity. Labels describe the document **at the recorded review
time**, not later disclosure or policy changes.

## Compatibility with current application

- Preserved Flask `sensitivity.py` uses basename/hash declarations and
  NORMAL/HIGH/CRITICAL; its dashboard checks permissions, external transfers and
  hours. Alert severity LOW/MEDIUM/HIGH/CRITICAL is a separate event judgment.
  Risk-score bands are another separate quantity.
- FastAPI `analysis.py` currently maps its email/CNIC rules to `restricted`, and
  supports public/internal/confidential/restricted declarations. This historical
  behavior is preserved even where it differs from this proposed taxonomy.
- There is no lossless mapping of that four-level vocabulary into the proposed
  three levels without an approved policy. Future adapter must preserve the
  original value and record a separately reviewed mapping; DS1 defines none.
- The React dashboard displays existing label/score/source/version. Rule
  confidence is not empirical model calibration. The optional active sensitivity
  adapter’s probability contract must not accept an uncalibrated category score.
- Content-only classification and owner/context policy assignment must remain
  visibly separate. No new model activation or automatic blocking is authorized.

## Exact human work still needed

No independently labeled organizational corpus was found in the repository or
existing Documents/Desktop/Downloads/workspace files. CERT activity labels,
historical filename/hash declarations, regex matches and synthetic interface
fixtures are not independent organizational ground truth.

Proposed initial workload (a requirement, **zero such annotations completed**):

1. Obtain authorized, de-identified examples and an owner-approved versioned
   policy. Owner supplies source organization, document family/version relation,
   release state, intended audience, impact, provenance and review timestamp.
   Record authorization/retention and revoke access to withdrawn documents.
   Do not solicit live credentials or copy unrelated private files into a corpus.
2. Pilot 100 documents covering public PII, ordinary financial text, restricted
   business material, inert credential examples and supported/unsupported input
   formats. Two trained reviewers independently label content and, where
   contextual evidence exists, policy level. Pilot documents train annotators;
   they are excluded from the final test and marked as pilot-only.
3. Freeze the guide/policy after owner review of pilot disagreements. Sample
   1,200 additional documents from the authorized target population, by document
   family rather than individual chunks. This is a planned minimum, not a
   promise of adequate rare-class power. Audit grouping before sampling.
4. Reserve 20% of independent families as an untouched test set and 20% as
   validation; use 60% for training. Sizes may differ from 720/240/240 documents
   because families stay together. Preserve natural validation/test prevalence.
   Collect enriched rare-class examples only into a separately tagged training
   supplement. Freeze selection, provenance and hashes before model fitting.
5. Two independent reviewers per document: 200 pilot reviews + 2,400 corpus
   reviews, plus a third reviewer for every disagreement. Give reviewers the
   approved contextual packet but hide rule/model outputs, splits and other
   reviewers’ judgments. A document owner confirms authority/context but cannot
   replace the two independent content judgments.
6. Record span evidence, exclusions, confidence/uncertainty, reviewer IDs,
   revision, timestamp and reason. Compute category-specific agreement and
   weighted policy-level agreement on the pilot; publish actual agreement, not a
   presumed value. Third reviewer resolves documented differences with owner
   clarification; unresolved items remain abstentions. Re-review a random 10%
   of agreed labels plus all disputed CRITICAL labels for quality assurance.
7. Hold test labels with a separate custodian. Never use test error findings for
   model selection; a changed guide requires a newly versioned experiment and
   fresh independent holdout. Report unresolved/extraction-excluded coverage.

If fewer independent examples or no positive held-out cases exist, report the
limitation and undefined metrics. Do not balance held-out populations or label
absence as a negative. Organizational labels require context even for NORMAL;
category-only documents can be independently labeled with policy level unknown.

## Runnable packet interface

`research.document_annotation` wraps the existing bounded extractor, records
source/family grouping and the extracted-text SHA-256, and creates two blank
review slots. Packets contain private text and must stay in ignored research
storage. Human identity/independence and authorization need external governance;
schema validation cannot prove them. The interface validates their declarations.

From repository root (use real authorized paths/IDs; do not execute placeholders):

```bash
.local/phase0-venv/bin/python -B -m research.document_annotation --prepare /authorized/example.docx --source-id source-001 --family-id family-001 --policy-version approved-v1 --output research/local/document_sensitivity/annotations/blank-001.json
# Reviewers fill separate private copies; merge their judgments with a human audit trail.
.local/phase0-venv/bin/python -B -m research.document_annotation --adjudicate research/local/document_sensitivity/annotations/reviewed-001.json --output research/local/document_sensitivity/annotations/accepted-001.json
```

No automatic labels or inferred NORMAL. Category-only reviews retain `null`
policy level. Policy judgments and BUSINESS_CONFIDENTIAL require owner reference,
policy version, audience, release state and harm rationale. Both reviewers must
be distinct; disagreements require a distinct third reviewer and reason. Digest,
policy-version, complete extraction and new-output guards reject invalid packets.
This is annotation readiness, not model training or validated classification.

Raw file hashes/authorized provenance belong in a separate private source
inventory; a packet’s digest binds reviewed extracted text, not the original
container. Keep adjudicated labels separate from synthetic, weak and machine
labels. DS2 must add evidence-span/group/provenance export validation before any
organizational training.
