# Document sensitivity supervision search and interface

Local search (2026-10-08): repository `research/`, `ml/`, tests and documentation;
recursive file-name search in Documents, Desktop, Downloads and
Insider_Threat_Test_Dataset, CSV/JSONL/Parquet/sensitivity/label names (excluding
environments, node_modules, Git metadata and known ignored research outputs). Downloaded training_features.csv/features.csv
are behavioral feature exports, not independently annotated documents. Original
rule policies, parser synthetic fixtures and CERT answers are ineligible.
No independently labeled sensitivity corpus was found in this search scope.

Official sources reviewed online on 2026-10-08:

| Candidate/source | Supervision and license assessment | Decision |
|---|---|---|
| [CMU Enron](https://www.cs.cmu.edu/~enron/) | Real emails, research distribution with privacy caution; no explicit general dataset license on page. Linked annotations are topics, sentiment or speech acts, not sensitivity. | No download; lacks target labels. |
| [Presidio research](https://github.com/data-privacy-stack/presidio-research) (Microsoft URL redirects here) | PII recognition/evaluation and template/fake-PII generator. MIT code license; fake identities have separate CC BY-SA 3.0 US attribution. | No download; synthetic PII spans cannot validate sensitivity. |
| [Ai4Privacy official catalog](https://www.ai4privacy.com/datasets/pii-masking-400k/) | Synthetic NER/PII masking, custom licenses requiring release-specific review; extended 200K has 54 entities. | No download; entity labels are not policy sensitivity labels. |
| [Learning Agency PII competition](https://www.kaggle.com/competitions/pii-detection-removal-from-educational-data/data) | Educational essay PII token labels; official data page did not expose license terms to this browser. Permission not verified. | No download; label mismatch and license/access unresolved. |

The search does not prove that no suitable corpus exists anywhere. None of the
reviewed sources establishes independent DataShield sensitivity evaluation.
No third-party corpus was downloaded or relabeled. Public release alone does
not imply non-sensitive status. Presence/absence of regex PII does not establish
policy sensitivity; model-generated labels are also ineligible ground truth.

`research.sensitivity_training` is a runnable offline binary interface. Supply a
policy reviewed corpus with `sensitive` / `not_sensitive` annotations, independent
human provenance and permission. Define sensitivity under the policy in the
manifest; do not collapse public/internal/confidential/restricted without a
reviewed binary mapping. Include ordinary confidential content without PII and
public content with legitimate PII, realistic supported document formats/domains,
multiple independent source families, and both classes in all fixed partitions.
At least two documents/class in training and one/class validation/test are
execution minima only; scientifically useful validation needs substantially more
independent positives/negatives and uncertainty estimates. Group by authors,
threads, document family and near duplicates when assigning `group_id`. The code
checks group and normalized bag equality, not semantic near-duplicate detection;
corpus review must resolve that before evaluation.

The manifest is JSON with fields: `task: "document_sensitivity"`,
`labels: {"not_sensitive": 0, "sensitive": 1}`, `label_origin: "independent_human"`,
`policy_definition`, `annotation_method`, `annotator_provenance`, `source`,
`license`, `permitted_use`, `split_objective`, `jsonl` (relative file), `sha256`
(the JSONL digest). Each JSONL record has exactly `document_id`, `group_id`,
`text`, `label` and `split` (`train`, `validation`, `test`). Fixed splits must be
independently declared; include time restrictions in corpus curation where the
objective needs later-time evaluation. Metadata claims must be audited: validating
a manifest cannot prove annotator independence or legal permission.

```bash
.local/phase0-venv/bin/python -B -m research.sensitivity_training \
  --manifest research/local/sensitivity-corpus/manifest.json \
  --output research/local/sensitivity-evaluation-v1
```

Only explicit `--fixture-only` accepts `synthetic_fixture` supervision, with
`FIXTURE_ONLY_NOT_VALIDATED` status. Tests run synthetic documents to verify
execution and leakage refusal. No sensitivity model was trained on real data;
no sensitivity accuracy or DataShield deployment validation is claimed. Training
fits TF-IDF and balanced logistic on train only; validation freezes a threshold
before test scoring. It reports confusion, precision/recall/F1/AP/prevalence and
false alerts per 1,000 documents, uncalibrated margins and reload/refit checks.
Raw contents and model artifacts remain in ignored research/local; no activation.
