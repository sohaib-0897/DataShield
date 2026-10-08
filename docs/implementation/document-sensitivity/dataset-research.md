# Primary dataset research and selection

Reviewed 2026-10-08. Existing local corpus search found only behavioral feature
CSVs, CERT events/answers, unlabeled documents and synthetic fixtures; none
provided independent organizational sensitivity ground truth. No existing corpus
is overwritten. Counts below are source-reported unless an acquired inventory
explicitly reports actual counts. “Not verified” is not a claim of absence.

## Selected narrowly: Text Anonymization Benchmark (TAB)

- Official [repository](https://github.com/NorskRegnesentral/text-anonymization-benchmark),
  [paper](https://aclanthology.org/2022.cl-4.19/) and
  [annotation guidelines](https://github.com/NorskRegnesentral/text-anonymization-benchmark/blob/master/guidelines.md).
  Source revision fixed at `558e09e26d6b36f5f78440074e6a233946d98bd9`.
  HTTPS raw files or a pinned GitHub archive provide access without credentials.
- [License](https://github.com/NorskRegnesentral/text-anonymization-benchmark/blob/master/LICENSE.txt):
  MIT; corpus README explicitly adopts MIT. Preserve Norsk Regnesentral
  copyright and permission notice in copies/substantial redistributions. Code
  and corpus license were checked separately; this is not an assumption that a
  code license covers every other corpus. Raw documents remain outside Git.
- 1,268 English ECHR cases, Introduction/Statement of Facts extracts in JSON
  with original text and standoff spans. Source train/dev/test: 1,014/127/127
  documents; annotation sets 1,112/541/555. Not original whole PDF/DOCX files.
- Twelve law students annotated natural court material using machine
  preannotations which they corrected/extended; the paper reports changes or
  additions to roughly 24% of spans. Some sets were quality-reviewed by a second
  annotator. This is **human-reviewed, machine-assisted natural text**, not
  annotation from a blank page, fully double-reviewed gold, or synthetic data.
- Entity labels: PERSON, CODE, LOC, ORG, DEM, DATETIME, QUANTITY, MISC.
  Identifier judgments: DIRECT, QUASI, NO_MASK. Personal confidential attributes:
  BELIEF, POLITICS, SEX, ETHNIC, HEALTH, NOT_CONFIDENTIAL, and not-applicable
  values. Masking depends on the protected person specified in the task.
  None is an organizational NORMAL/HIGH/CRITICAL judgment. QUANTITY does not
  establish financial content. ORG does not establish business confidentiality.
- Supported future task: **semantic category classification of supplied entity
  spans** in this legal domain. The model is given annotation span boundaries;
  this is not entity detection or document-sensitivity classification. A supplied
  span benchmark cannot prove whole-document detection recall or negatives for
  unannotated material. No TAB label is remapped to DataShield policy levels.
- Public legal text can still expose personal/medical/sexual details. License is
  not privacy clearance: restrict local access, avoid raw text, names, task
  identities or annotator IDs in logs/Git, and honor withdrawals and applicable
  requirements before downstream redistribution. Legal narrative, demographic
  and judicial conventions differ from corporate documents and credentials.
- DS1 inventory validates source hashes/schema/offsets and counts only. DS2
  must reconcile annotator sets without treating repeated judgments as separate
  documents, audit case/subject families and near-duplicates, and preserve the
  original release/splits before declaring any split trainable.

Source-reported semantic class counts (paper Table 3, all splits/annotator
records combined, **not locally verified or independent document counts**):

| TAB class | Meaning from official guide | Mention records |
|---|---|---:|
| DATETIME | Specific dates, times and durations | 53,668 |
| ORG | Named institutions/organizations | 40,695 |
| PERSON | Personal names, aliases, initials and usernames | 24,322 |
| LOC | Places, addresses and named infrastructure | 9,982 |
| DEM | Demographic/occupation/physical/health attributes | 8,683 |
| MISC | Other descriptions about an individual | 7,044 |
| CODE | Identifying numbers/codes, including phone/passport identifiers | 6,471 |
| QUANTITY | Quantities including percentages and monetary amounts | 4,141 |

Source total 155,006 mention records, 108,151 distinct entities and 2,208 document
annotation sets; quality-reviewed sets 328/313/315. Confidential-attribute counts
(paper Table 4): HEALTH 2,320; POLITICS 1,039; ETHNIC 806; BELIEF 655; SEX 516;
NOT_CONFIDENTIAL 149,670. Source Table 5 exact-span entity-type Fleiss kappa .67;
confidential-attribute kappa .30. These disagreement/preannotation limitations
motivate reconciliation before fitting. None is DataShield performance evidence.

## Other credible candidates and why not acquired

| Candidate / primary source | Labels and annotation provenance | Size / language / format | Rights, access and decision |
|---|---|---|---|
| [Monsanto taboo corpus, LREC paper](https://aclanthology.org/2020.lrec-1.158/) and [official implementation](https://github.com/neerbek/taboo-mon) | Four case-specific sensitive notions GHOST/TOXIC/CHEMI/REGUL; gold sentence judgments by three human raters, majority aggregation. Silver sentence labels propagated from documents are weak supervision, not gold. | English corporate litigation material extracted from PDFs/emails. Source gold 1,073 sentence-task records: 200 positive / 873 negative; train/dev/test 540/257/276, positives 103/43/54. Source silver 15,074 with 7,537 positive. Fair agreement reported (kappa about .33). | MIT code does not settle source litigation PDF/corpus redistribution rights. Legacy external download links and full gold-source linkage/access not verified; no acquisition. Potential business-context research fit, but public litigation status/topic does not define DataShield policy level; severe company/legal-domain mismatch and personal-data risk. |
| [CUAD, Atticus Project](https://www.atticusprojectai.org/cuad/) | Human annotations under legal-expert supervision; 41 commercial contract clause categories for contract review. Not confidentiality levels or personal-information annotation. | 510 English contracts; 13,000+ annotations; PDF/text and structured annotations. Per-clause counts not verified in this session. | Official release CC BY 4.0; attribution/change notices apply; linked public downloads. Acquisition permitted in principle but not selected: a confidentiality clause is not proof that a whole public contract is sensitive. Contract-domain mismatch; possible personal names in public filings. |
| [SARA official repository](https://github.com/JackMcKechnie/SARA) | Enron subset with 53 topic relevance categories from student annotation; IR relevance assessments separate. Topic/secrecy/sentiment relevance is not document sensitivity. Do not pool later machine extensions with human judgments. | 1,702 English emails; text and structured relevance/category records; category counts not verified. | Assessments CC BY-NC 4.0 per official README; underlying Enron/LDC sources have separate rights. No acquisition: unrelated labels and noncommercial/separate source constraints. Natural email has identifiers/private correspondence despite public release. |
| [Ai4Privacy official dataset page](https://www.ai4privacy.com/datasets/pii-masking-400k/) | Synthetic/generated PII span labels, not independent human judgments on natural organizational documents. | 400k release advertises 406,896 rows, six languages and 17 entities; earlier 200k release has different schema/counts (209k, four languages, 54 entities). Text/structured spans. Per-class counts not verified. | Release-specific/custom licensing needs exact downloadable terms; no acquisition or redistribution pending that check. Can support explicitly synthetic extraction stress tests, never independent organizational validation. |
| [Presidio research official project](https://github.com/data-privacy-stack/presidio-research) | Template/generator-based synthetic PII examples; machine/template truth. | Generator and text/span fixtures; no fixed natural independently labeled organizational corpus size. | MIT code; third-party fake-name resources include separate CC BY-SA terms. No acquisition: useful synthetic testing only. No policy context or independently labeled natural documents. |
| [Learning Agency educational PII competition](https://www.kaggle.com/competitions/pii-detection-removal-from-educational-data/data) | PII token detection task; organizational sensitivity is not a target. Annotation provenance and exact current download terms were not accessible from the official page here. | English educational essays; official accessible response did not establish exact release/class counts in this session. | Gated competition access/terms must be verified before acquisition; none downloaded. Educational-domain mismatch; student personal data needs restricted handling. Do not infer license from mirrors. |

No unrelated topics, sentiment, spam or CERT malicious-activity targets were
reassigned as sensitivity labels. Public synthetic, weak, machine-assisted human
and independent organizational annotations remain distinct evidence classes.

## What can and cannot be trained next

TAB supports a declared, conditional personal-entity semantic-category baseline
only after DS2 grouping and annotation reconciliation. It supplies no validated
financial/credential/business-confidential document labels and no organizational
levels. A separate document corpus needs the human work in
[taxonomy-and-annotation.md](taxonomy-and-annotation.md). If TAB acquisition or
group audits remain blocked, continue the private annotation workflow and leave
training blocked; do not substitute invented labels or synthesize performance.
