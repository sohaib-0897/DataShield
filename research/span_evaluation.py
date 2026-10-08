"""Offline exact-span evidence lanes. No oracle detector inputs or policy labels.

Independent metrics require validated exhaustive reviews. Released annotation
comparisons measure recovery, with unmatched predictions remaining unreviewed.
"""
from collections import Counter, defaultdict
import random


def spans(values, text_length, targets):
    result = []
    for value in values:
        if (not isinstance(value, (list, tuple)) or len(value) != 3
                or type(value[0]) is not int or type(value[1]) is not int
                or not 0 <= value[0] < value[1] <= text_length or value[2] not in targets):
            raise ValueError('Invalid original-text offsets or ontology')
        result.append(tuple(value))
    return set(result), len(result) - len(set(result))


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def compare_reference(predictions, references, *, text_length, prediction_targets,
                      reference_targets, identical_ontology=False):
    """Exact boundaries only across ontologies; typed recovery requires identity.

    Never emits FP, TN, precision or F1 for incomplete release annotations.
    Duplicates collapse, overlapping reference spans remain intact.
    """
    predicted, duplicates = spans(predictions, text_length, prediction_targets)
    gold, gold_duplicates = spans(references, text_length, reference_targets)
    if identical_ontology and tuple(prediction_targets) != tuple(reference_targets):
        raise ValueError('Identical declared semantics required for typed comparison')
    pbound = Counter((s, e) for s, e, _ in predicted)
    gbound = Counter((s, e) for s, e, _ in gold)
    boundary_matches = sum(min(count, gbound[key]) for key, count in pbound.items())
    typed = len(predicted & gold) if identical_ontology else None
    return {'returned_unique_predictions': len(predicted), 'duplicate_predictions': duplicates,
            'reference_spans_unclipped': len(gold), 'duplicate_reference_spans': gold_duplicates,
            'exact_boundary_matches': boundary_matches,
            'exact_boundary_reference_recovery': ratio(boundary_matches, len(gold)),
            'boundary_unmatched_predictions_unreviewed': len(predicted) - boundary_matches,
            'annotated_typed_span_recovery_count': typed,
            'annotated_typed_span_recovery': ratio(typed, len(gold)) if typed is not None else None,
            'typed_unmatched_predictions_unreviewed': len(predicted) - typed if typed is not None else None,
            'category_agreement_at_exact_boundaries': ratio(typed, boundary_matches) if typed is not None else None,
            'category_agreement_boundary_support': boundary_matches if typed is not None else None,
            'typed_unavailable_reason': None if identical_ontology else 'No identical declared target semantics/mapping',
            'unannotated_text_is_confirmed_negative': False}


def _metrics(tp, fp, fn):
    return {'tp': tp, 'fp': fp, 'fn': fn, 'precision': ratio(tp, tp + fp),
            'recall': ratio(tp, tp + fn), 'f1': ratio(2 * tp, 2 * tp + fp + fn),
            'undefined': {name: reason for name, denominator, reason in
                          [('precision', tp + fp, 'no predictions'),
                           ('recall', tp + fn, 'no reviewed targets'),
                           ('f1', 2 * tp + fp + fn, 'no predictions or reviewed targets')]
                          if not denominator}}


def independent_counts(predictions, review, *, text_length, targets):
    """Review must come from span_review.validate_document_review, never TAB.

    No meaningful ranks for deterministic rules: AP remains unavailable.
    All gold is retained when returned predictions hit the result cap.
    """
    if (review.get('evidence_lane') != 'independent_exhaustive_review'
            or not targets or not set(targets) <= set(review.get('exhaustive_targets', []))
            or not review.get('review_binding_sha256')):
        raise ValueError('Validated exhaustive target review required')
    predicted, duplicates = spans(predictions, text_length, targets)
    all_gold, _ = spans(review['spans'], text_length, review['exhaustive_targets'])
    gold = {s for s in all_gold if s[2] in targets}
    counts = {}
    for target in targets:
        p = {v for v in predicted if v[2] == target}
        g = {v for v in gold if v[2] == target}
        counts[target] = {'tp': len(p & g), 'fp': len(p - g), 'fn': len(g - p),
                          'document_tp': int(bool(p) and bool(g)),
                          'document_fp': int(bool(p) and not g),
                          'document_fn': int(bool(g) and not p),
                          'document_tn': int(not p and not g)}
    boundary = compare_reference(predictions, sorted(gold), text_length=text_length,
                                 prediction_targets=targets, reference_targets=targets,
                                 identical_ontology=True)
    return {'targets': counts, 'duplicate_predictions': duplicates,
            'boundary_matches': boundary['exact_boundary_matches'],
            'typed_matches': boundary['annotated_typed_span_recovery_count']}


def summarize_independent(rows, targets):
    per_target = {}
    for target in targets:
        total = Counter()
        for row in rows:
            total.update(row['counts']['targets'][target])
        metric = _metrics(*(total[k] for k in ('tp', 'fp', 'fn')))
        dtp, dfp, dfn, dtn = (total[k] for k in ('document_tp', 'document_fp', 'document_fn', 'document_tn'))
        metric['document'] = {**_metrics(dtp, dfp, dfn), 'tn': dtn,
                              'false_positive_documents_per_1000': ratio(1000 * dfp, len(rows)),
                              'false_positive_rate': ratio(dfp, dfp + dtn),
                              'positive_documents': dtp + dfn, 'negative_documents': dfp + dtn}
        metric['average_precision'] = None
        metric['average_precision_reason'] = 'Deterministic candidates have no meaningful ranked scores'
        per_target[target] = metric
    totals = [sum(m[k] for m in per_target.values()) for k in ('tp', 'fp', 'fn')]
    defined = [t for t in targets if per_target[t]['f1'] is not None]
    return {'documents': len(rows), 'families': len({r['family_id'] for r in rows}),
            'per_target': per_target, 'micro': _metrics(*totals),
            'macro_f1': ratio(sum(per_target[t]['f1'] for t in defined), len(defined)),
            'macro_included_targets': defined, 'macro_undefined_targets': [t for t in targets if t not in defined],
            'category_agreement_at_exact_boundaries': ratio(
                sum(r['counts']['typed_matches'] for r in rows),
                sum(r['counts']['boundary_matches'] for r in rows)),
            'span_true_negatives_accuracy_specificity': None,
            'span_negative_universe': 'undefined; no fixed universe of negative spans'}


def cluster_interval(rows, statistic, *, replicates=2000, seed=42):
    """Percentile bootstrap of whole families; intervals are corpus conditional."""
    if replicates != 2000 or seed != 42:
        raise ValueError('Frozen protocol requires 2000 replicates and seed 42')
    families = defaultdict(list)
    for row in rows:
        families[row['family_id']].append(row)
    keys = sorted(families)
    if len(keys) < 2:
        return {'lower': None, 'upper': None, 'valid_replicates': 0,
                'reason': 'fewer than two families', 'replicates': replicates}
    rng, samples = random.Random(seed), []
    for _ in range(replicates):
        sampled = [r for _ in keys for r in families[rng.choice(keys)]]
        value = statistic(sampled)
        if value is not None:
            samples.append(value)
    samples.sort()
    def percentile(q):
        position = (len(samples) - 1) * q
        lower = int(position)
        upper = min(lower + 1, len(samples) - 1)
        return samples[lower] + (samples[upper] - samples[lower]) * (position - lower)
    return {'lower': percentile(.025) if samples else None,
            'upper': percentile(.975) if samples else None,
            'valid_replicates': len(samples), 'replicates': replicates, 'seed': seed,
            'reason': None if samples else 'statistic undefined in every replicate',
            'scope': '95% family-cluster percentile interval; conditional on corpus and detector'}


def evaluate_independent(rows, targets):
    """Fixed deterministic metrics plus family intervals on validated count rows."""
    result = summarize_independent(rows, targets)
    result['intervals'] = {}
    for target in targets:
        for metric in ('precision', 'recall', 'f1'):
            def statistic(sample, target=target, metric=metric):
                return summarize_independent(sample, targets)['per_target'][target][metric]
            result['intervals'][target + '/' + metric] = cluster_interval(rows, statistic)
        for metric in ('false_positive_documents_per_1000', 'false_positive_rate'):
            def statistic(sample, target=target, metric=metric):
                return summarize_independent(sample, targets)['per_target'][target]['document'][metric]
            result['intervals'][target + '/document/' + metric] = cluster_interval(rows, statistic)
    for metric in ('precision', 'recall', 'f1'):
        result['intervals']['micro/' + metric] = cluster_interval(rows,
            lambda sample, metric=metric: summarize_independent(sample, targets)['micro'][metric])
    result['intervals']['macro_f1'] = cluster_interval(rows,
        lambda sample: summarize_independent(sample, targets)['macro_f1'])
    return result
