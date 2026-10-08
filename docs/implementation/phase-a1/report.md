# A1 — label readiness and bounded automatic detection

Started 2026-10-08 at clean local/fresh remote
`22dc822c75cf6f1e106980bbd974fd576d025588` on `feat/cert-ml-nlp` in the existing
literal-tilde checkout. Repository URL matches the user request; fresh fetch
reports divergence 0/0. No applicable AGENTS.md found. Read implementation memory,
CONTEXT and DS1–DS3 reports before planning. No later user changes existed to reconcile.
The new bounded A–F plan is in DATASHIELD_IMPLEMENTATION.md; execute A1 only here.

## Changes and boundaries

`ml/content_detection.py` v1 is a shared, standard-library-only local detector.
It requires text only; no caller spans, learned model, network access, persistence,
policy or risk calculation. `research/automatic_content.py` is an explicit offline
CLI bridge to the existing extraction subprocess. Existing deterministic live
email/CNIC rules and their enforcement behavior remain unchanged. Nothing calls
this module automatically; no application flag/API/UI has been added or enabled.
Supplied-span advice remains separate and disabled by default.

| Kind | Candidate category | Validation / coverage |
|---|---|---|
| email_address | PERSONAL_INFORMATION | ASCII unquoted mailbox syntax, local dot checks, domain labels; no DNS/ownership |
| cnic_like | PERSONAL_INFORMATION | ASCII 5-7-1 shape only; no issuance/identity/checksum claim |
| iban | FINANCIAL_INFORMATION | DE/GB/PK national structure and MOD97; uppercase compact or canonical single-space groups |
| credential_assignment | CREDENTIALS | Explicit password/api_key/access_token/client_secret assignment, 8–256 character same-line value; candidates include inert examples |

IBAN source: [SWIFT registry release 103, September 2026](https://www.swift.com/resource/iban-registry-pdf),
structure/check-digit description p7, DE p24, GB p35, PK p71. Inspected official
registry in A1; country format constants are versioned in source. No full registry,
external account lookup or new dependency is required. Checksum-valid examples
can be public/inert and do not establish account existence or confidentiality.
This intentionally supports only those three countries; changes require a new version.

No general phone/address/person/organization/date/location/demographic NER,
financial prose, key blocks or BUSINESS_CONFIDENTIAL inference. The existing TAB
supplied-span model classifies eight entity categories, using released reviewed
legal annotations; those targets are incompatible with DS1 whole-document categories.
It is never called on these pattern candidates. Full-span annotation feasibility
and any local contextual NER provenance/license/resource assessment belong to A2.
No pretrained artifact acquired or frozen model retrained.

## Output and bounds

Offsets count Unicode code points, start inclusive/end exclusive, including
original IBAN spaces. Credential offsets cover the value only. Each span returns
category, kind, CANDIDATE status, deterministic method, detector version,
validation reason codes and limitations. No snippets, matched values or secret
fingerprints appear. Public PII and inert credentials remain candidates, not verified
secrets or sensitivity judgments. Score/probability/margin fields are absent.

Reject nontext, malformed Unicode, NUL, >32768 characters/>131072 UTF-8 bytes;
max_spans is an integer 1–100 (booleans rejected). Text is never silently truncated
by the detector. All supported patterns are scanned within the fixed text bound;
return earliest 100 candidates by offset with total candidate_count, spans_truncated
and detection_complete. That flag describes result enumeration for supported
patterns only, not universal detection coverage. Overlapping kinds may coexist;
counts do not represent independent incidents and must never be summed as risk.

The bridge preserves extraction status, extracted length and truncation. It detects
only for OK extraction; failures return unavailable detection rather than no-sensitive-
content. Partial extraction remains explicit. `extraction_complete` describes parser
coverage only; unsupported entities still remain unknown. Organizational sensitivity
is always null, review_needed true, automated_blocking false. No entire document,
path, text or filename is included in CLI evidence. No logs or output files are written
by the detector/bridge. Existing extraction bounds/status handling remain intact.

## Label readiness

[Owner/reviewer instructions and audit](label-readiness.md) distinguish the existing
inert blank packet from the proposed 100-document pilot. Zero independent reviews,
organizational labels, approved policy or agreement/class metrics were verified.
No packet for 100 real documents can be generated until authorized inventory exists.
Fresh CLI validation uses an inert fixture and produces two blank slots only.
The old v1 declaration validator's export/governance gaps remain explicit; C1 must
validate those before any real sensitivity training. Pilot documents cannot be final
test. No reviewer identity, approval or adjudication was generated by this agent.

## Verification

[Sanitized verification](verification.json): **66 new detector checks**, **287 isolated
full-suite passes**, **22 preserved Flask passes**, no failures/skips; one pre-existing
Starlette/httpx warning. Isolated checks copy tracked/index-listed Python sources
into a temporary directory with synthetic credentials and SQLite. New tests cover
automatic text-only detection separately from supplied-span model classification,
Unicode offsets/redaction, checksum rejection, public PII/placeholder ambiguity,
input/result bounds, actual TXT CLI and extraction failure/truncation contracts.
Existing actual TXT/PDF/DOCX parser and authenticated supplied-span tests remain in
the full suite. No native Windows or live PostgreSQL validation is claimed.

Read-only preservation: all **13 frozen artifacts** match the existing canonical
feature verifier; all **60 pre-existing private DS2/DS3 files**, **12 DS3-bound input
hashes**, **six pinned TAB source hashes**, **30 original/live hash entries**,
**19 normalized preserved copies** and **three archive stat observations** match.
All pre-existing backend/frontend/agents/legacy, extraction, annotation, supplied-span,
dependencies/workflow and DS1–DS3 report diffs are empty. No acquisition, feature
preparation, fitting or frozen evaluation was repeated. Bound inputs matching DS3
confirm the reported 1268 accounting and frozen 326/124/127 population without
rewriting its diagnostic/evaluation. Archive stats are not complete archive hashes.

Synthetic maximum-input smoke: 20 calls each for five fixed cases (ASCII/Unicode
no-match, candidate overflow, malformed email and long secret assignment). Across
cases, median 7.938–26.434 ms, maximum 34.227 ms; one Python process peak 26.484 MiB.
Overflow produced 1820 candidates, returned 100 with explicit truncation. These
are local contract/resource observations, not natural-document P/R/F1 or general
latency guarantees. Detector max-size tests are deterministic; timing is not a CI
pass threshold. The actual inert extraction+CLI command resources are recorded
separately in verification.json.

Actual commands, from repository root (retain ignored logs/private evidence):

```bash
.local/phase0-venv/bin/python -B -m pytest -q tests/test_content_detection.py -p no:cacheprovider
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /usr/bin/time -v -o .local/phase-a1/regression-resource.txt .local/phase0-venv/bin/python -B scripts/verification/phase0_upstream_baseline.py --report .local/phase-a1/regression.json --log .local/phase-a1/regression.log
/usr/bin/time -v -o .local/phase-a1/flask-resource.txt .local/phase0-venv/bin/python -B tests/phase0_regression.py --source-root legacy/downloaded_flask --require-no-skips --report .local/phase-a1/flask.json
/usr/bin/time -v -o .local/phase-a1/frozen-resource.txt .local/phase0-venv/bin/python -B scripts/verification/ds2_frozen_preservation.py --output research/local/document_sensitivity/phase_a1_frozen.json
python3 -B scripts/verification/phase0_preservation.py --source-root /home/sohaib/Downloads/AI-DLP-Agent --dataset-root /home/sohaib/Downloads --output .local/phase-a1/live.json --compare docs/implementation/phase0/phase0_preservation_before.json
.local/phase0-venv/bin/python -B -m research.document_annotation --prepare .local/phase-a1/inert-document.txt --source-id synthetic-a1-source --family-id synthetic-a1-family --policy-version synthetic-unapproved-fixture --output research/local/document_sensitivity/phase_a1_fixture/blank-packet.json
/usr/bin/time -v -o .local/phase-a1/cli-resource.txt .local/phase0-venv/bin/python -B -m research.automatic_content .local/phase-a1/inert-document.txt > .local/phase-a1/cli-evidence.json
git diff --check
git diff --cached --check
wc -l DATASHIELD_IMPLEMENTATION.md
git push origin feat/cert-ml-nlp
git ls-remote origin refs/heads/feat/cert-ml-nlp
gh run list --branch feat/cert-ml-nlp --limit 3 --json databaseId,headSha,status,conclusion
```

Inline read-only checks hash each pre-existing private file against the A1 start
snapshot (`.local/phase-a1/private-before.json`), compare DS3 `input_hashes`, DS2
acquisition hashes and the preserved-copy normalized manifest. No source content
is printed. Frozen feature checks use the canonical verifier, not these file hashes.
The inert fixture contains public@example.invalid and api_key=inert-secret-123;
the CLI output contains only offsets/check codes. Packet status is awaiting reviews,
all label fields remain null, and existing adjudication rejects it.

No dependency configuration changed; existing environment was used. A2 must
freeze the evaluation protocol before choosing a contextual model/configuration;
A1 engineering fixtures must not be passed off as independent corpus validation.
Publication is a normal branch push; final remote SHA and current CI are inspected
at the boundary. Resolve phase SHA with `git log -1 --format=%H -- ml/content_detection.py`.
Next requested phase: A2 contextual-span feasibility and frozen B evaluation protocol.


## Verified publication receipt

Source checkpoint `ebc23dbbe63b9933829bee812ae9438f6d9d06e3` pushed normally;
fresh GitHub branch SHA equals local HEAD and working tree was clean.
[CI 37770109324](https://github.com/sohaib-0897/DataShield/actions/runs/37770109324)
completed successfully for that exact SHA: 287 Python tests (one existing warning),
seven frontend tests, production build and CI PostgreSQL migrations. This clean
CI result is separate from local temporary-SQLite/fixture verification and does
not establish native Windows or live PostgreSQL monitoring.

A1 is complete at its bounded offline acceptance. This documentation-only
receipt/closure checkpoint follows the verified source; its normal push/fresh
remote equality and current exact-SHA CI are checked in the phase-end handoff.
No failed publication is pending; on resume verify HEAD/remote/CI before A2.
If a subsequent push fails, retain the local closure checkpoint and recover with
`git push origin feat/cert-ml-nlp`; never force-push. No implementation work is
pending in A1. Stop here. A2 handles contextual feasibility and freezes the
end-to-end evaluation protocol before model selection or B execution.
