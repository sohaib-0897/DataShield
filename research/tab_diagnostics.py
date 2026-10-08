"""DS3 read-only audit of frozen DS2 manifests/predictions; no fit or selection."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

import numpy as np

from research.cert_ingest import atomic_json, hash_file, local_path
from research.tab_baseline import bounded_json, load_split, metrics
from research.tab_prepare import CLASSES, TASK, consensus, digest, normalized


def document_reason(entry):
    if not entry['retained']:
        return 'quarantined_reviewed' if entry['reviewed_sets'] else 'quarantined_unreviewed'
    if not entry['reviewed_sets']:
        return 'unreviewed_nonquarantined'
    if not entry['eligible_spans']:
        return 'reviewed_no_unanimous_spans'
    return 'used'


def audit_documents(source, prepared, splits, prep):
    entries = bounded_json(prepared/'documents.json')
    by_doc = {e['source_doc_sha256']: e for e in entries}
    if len(by_doc) != len(entries):
        raise ValueError('Duplicate source document')
    acquisition = {e['file']: e for e in prep['acquisition']['files']}
    family_splits = defaultdict(set)
    for entry in entries:
        family_splits[entry['group']].add(entry['official_split'])
    priority = {g: 'test' if 'test' in parts else 'dev' if 'dev' in parts else 'train'
                for g,parts in family_splits.items()}
    if any(e['retained'] != (e['official_split'] == priority[e['group']]) for e in entries):
        raise ValueError('Frozen family quarantine priority changed')
    split_counts = {}; ledger = []; totals = Counter(); audit = Counter()
    all_ids = set()
    for official, partition in [('train', 'train'), ('dev', 'validation'), ('test', 'test')]:
        path = source/f'echr_{official}.json'
        if hash_file(path)['sha256'] != acquisition[path.name]['sha256']:
            raise ValueError('Source corpus changed')
        docs = bounded_json(path)
        expected = {}; reasons = Counter(); span_counts = Counter()
        for doc in docs:
            key = digest(doc['doc_id']); entry = by_doc[key]
            if key in all_ids or digest(doc) != entry['original_record_sha256'] or entry['official_split'] != official:
                raise ValueError('Document identity/record mismatch')
            all_ids.add(key)
            spans, findings = consensus(doc); audit.update(findings)
            if len(spans) != entry['eligible_spans'] or len(doc['quality_checked']) != entry['reviewed_sets']:
                raise ValueError('Frozen consensus mismatch')
            reason = document_reason(entry); reasons[reason] += 1; totals[reason] += 1
            span_counts['eligible_before_quarantine'] += len(spans)
            if not entry['retained']:
                span_counts['quarantined_eligible_spans'] += len(spans)
            else:
                for start, end, label in spans:
                    sid = digest([doc['doc_id'], start, end])
                    expected[sid] = {'id': sid, 'document': key, 'group': entry['group'],
                                     'start': start, 'end': end, 'label': label, 'entity': doc['text'][start:end],
                                     'context': doc['text'][max(0,start-160):start]+' [SPAN] '+doc['text'][start:end]+' [/SPAN] '+doc['text'][end:end+160],
                                     'ambiguous_raw_category': len({m['entity_type'] for a in doc['annotations'].values()
                                         for m in a['entity_mentions'] if (m['start_offset'],m['end_offset'])==(start,end)}) > 1}
            ledger.append({**entry, 'reason': reason, 'preferred_family_official_split':priority[entry['group']],
                           'frozen_partition': partition if reason == 'used' else None})
        actual = {r['id']: r for r in splits[partition]}
        if len(actual) != len(splits[partition]) or actual != expected:
            raise ValueError('Every frozen span must match the original reviewed consensus')
        if reasons['used'] != len({r['document'] for r in actual.values()}):
            raise ValueError('Used document count mismatch')
        split_counts[partition] = {'source_documents': len(docs), 'document_reasons': dict(reasons),
                                   'spans': len(actual), **span_counts}
    if all_ids != set(by_doc):
        raise ValueError('Every source document must be accounted for')
    return {'source_documents': len(entries), 'exclusive_document_reasons': dict(totals),
            'partitions': split_counts, 'consensus_audit': dict(audit),
            'quarantine_by_source_and_preferred_split':dict(Counter(
                e['official_split']+'->'+priority[e['group']] for e in entries if not e['retained'])),
            'every_document_and_span_accounted_for': True}, ledger


def matrix_statistics(matrices):
    """One row per replicate; undefined precision/recall stays NaN."""
    support = matrices.sum(axis=2); predicted = matrices.sum(axis=1)
    tp = np.diagonal(matrices, axis1=1, axis2=2)
    def divide(a, b):
        return np.divide(a, b, out=np.full(a.shape, np.nan, dtype=float), where=b != 0)
    p = divide(tp, predicted); r = divide(tp, support)
    f = divide(2*tp, support+predicted)
    f[support == 0] = np.nan
    macro = divide(np.nansum(f, axis=1), np.sum(support > 0, axis=1))
    micro = divide(tp.sum(axis=1), support.sum(axis=1))
    return {'macro_f1': macro, 'micro_f1': micro, 'precision': p, 'recall': r, 'f1': f}


def interval(values):
    valid = values[np.isfinite(values)]
    return {'lower': float(np.percentile(valid, 2.5)) if len(valid) else None,
            'upper': float(np.percentile(valid, 97.5)) if len(valid) else None,
            'valid_replicates': len(valid)}


def bootstrap(rows, predictions, strata, *, replicates=2000, seed=42):
    if not rows or replicates < 100 or replicates > 10000:
        raise ValueError('Bootstrap requires rows and 100..10000 replicates')
    documents = sorted({r['document'] for r in rows}); index = {d:i for i,d in enumerate(documents)}
    classes = {c:i for i,c in enumerate(CLASSES)}
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(len(documents), np.full(len(documents), 1/len(documents)), size=replicates)
    result = {}; statistics = {}
    for name, ids in strata.items():
        blocks = np.zeros((len(documents), len(CLASSES), len(CLASSES)), dtype=np.int64)
        for i in ids:
            row = rows[i]
            blocks[index[row['document']], classes[row['label']], classes[predictions[i]]] += 1
        samples = np.tensordot(weights, blocks, axes=(1,0))
        stats = matrix_statistics(samples); statistics[name] = stats
        result[name] = {'macro_f1': interval(stats['macro_f1']), 'micro_f1': interval(stats['micro_f1']),
                        'per_class': {c:{m:interval(stats[m][:,i]) for m in ('precision','recall','f1')}
                                      for i,c in enumerate(CLASSES)},
                        'replicates_missing_truth_classes': int(np.sum((samples.sum(axis=2)==0).any(axis=1)))}
    if 'seen' in statistics and 'unseen' in statistics:
        result['paired_seen_minus_unseen'] = {m:interval(statistics['seen'][m]-statistics['unseen'][m])
                                              for m in ('macro_f1','micro_f1')}
    return {'method':'document cluster percentile bootstrap; whole documents resampled with replacement',
            'confidence':0.95, 'replicates':replicates, 'seed':seed, 'resampling_documents':len(documents),
            'estimand':'span-weighted metrics; macro includes classes with positive truth support in each replicate',
            'limitations':'conditional on this legal corpus/model; residual correlation across related documents/families not removed; no calibration or domain guarantee',
            'strata':result}


def diagnose(source, prepared, models, evaluation, output, replicates=2000):
    folder = Path('research/local').absolute()
    source, prepared, models, evaluation, output = [local_path(folder,p) for p in (source,prepared,models,evaluation,output)]
    if output.exists():
        raise ValueError('New diagnostic output required; DS2 outputs are immutable')
    prep = bounded_json(prepared/'preparation.json',1024**2)
    selection = bounded_json(models/'selection.json',1024**2)
    frozen = bounded_json(evaluation/'evaluation.json',1024**2)
    # The committed DS2 evidence is the trust anchor, not just mutable private files.
    evidence = Path('docs/implementation/document-sensitivity')
    if (prep != bounded_json(evidence/'ds2-preparation.json',1024**2)
            or selection != bounded_json(evidence/'ds2-baseline.json',1024**2)
            or frozen != bounded_json(evidence/'ds2-evaluation.json',1024**2)):
        raise ValueError('Private DS2 contract differs from committed checkpoint')
    if (selection['preparation'] != hash_file(prepared/'preparation.json')
            or frozen['selection'] != hash_file(models/'selection.json')):
        raise ValueError('Frozen model/split binding changed')
    splits = {s:load_split(prepared,s,prep) for s in ('train','validation','test')}
    audit, ledger = audit_documents(source,prepared,splits,prep)
    test = splits['test']; train = splits['train']
    stored = bounded_json(evaluation/'predictions.json')
    if stored['ids'] != [r['id'] for r in test] or stored['truth'] != [r['label'] for r in test]:
        raise ValueError('Frozen predictions do not join to the frozen test')
    for mode, predictions in stored['predictions'].items():
        if len(predictions) != len(test) or any(p not in CLASSES for p in predictions):
            raise ValueError('Prediction schema mismatch')
        recomputed = metrics(stored['truth'],predictions)
        for key in ('per_class','confusion_matrix','macro_f1','micro_f1'):
            reference = frozen['models'][mode][key]
            if key == 'per_class':
                reference = {c:{**v,'average_precision':None} for c,v in reference.items()}
            if recomputed[key] != reference:
                raise ValueError('Frozen prediction/metric mismatch')
    selected = selection['selected_mode']; pred = stored['predictions'][selected]
    vocabulary = defaultdict(set)
    for row in train:
        vocabulary[normalized(row['entity'])].add(row['label'])
    repeated = Counter(normalized(r['entity']) for r in test)
    counts = Counter(r['label'] for r in train)
    strata = {'full':list(range(len(test))), 'seen':[], 'unseen':[], 'ambiguous_raw_category':[],
              'seen_with_conflicting_training_categories':[], 'rare_training_classes_le_1000':[], 'repeated_test_string':[]}
    for i,row in enumerate(test):
        key = normalized(row['entity'])
        strata['seen' if key in vocabulary else 'unseen'].append(i)
        if row['ambiguous_raw_category']: strata['ambiguous_raw_category'].append(i)
        if len(vocabulary.get(key,())) > 1: strata['seen_with_conflicting_training_categories'].append(i)
        if counts[row['label']] <= 1000: strata['rare_training_classes_le_1000'].append(i)
        if repeated[key] > 1: strata['repeated_test_string'].append(i)
    strata_metrics = {name:{**metrics([test[i]['label'] for i in ids],[pred[i] for i in ids]),
                           'documents':len({test[i]['document'] for i in ids}),
                           'unique_normalized_strings':len({normalized(test[i]['entity']) for i in ids})}
                      for name,ids in strata.items()}
    for new,old in [('seen','entity_text_seen_in_training'),('unseen','entity_text_unseen_in_training')]:
        if strata_metrics[new]['confusion_matrix'] != frozen['strata'][old]['confusion_matrix']:
            raise ValueError('Seen/unseen diagnostic differs from frozen DS2')
    summary = {'phase':'DS3','task':TASK,'training_or_selection_rerun':False,'test_retuning':False,
               'document_accounting':audit,'strata':strata_metrics,
               'normalization':'NFKC, casefold, Unicode word tokens, whitespace joined; exact normalized string membership, independent of class',
               'training_vocabulary':{'strings':len(vocabulary),'strings_with_multiple_categories':sum(len(v)>1 for v in vocabulary.values())},
               'candidate_test_metrics':frozen['models'], 'candidate_validation_metrics':{m:v['validation'] for m,v in selection['models'].items()},
               'bootstrap':bootstrap(test,pred,{k:strata[k] for k in ('full','seen','unseen')},replicates=replicates),
               'input_hashes':{str(p):hash_file(p) for base in (prepared,models,evaluation) for p in sorted(base.iterdir()) if p.is_file()},
               'organizational_sensitivity':'BLOCKED: requires independent human labels and owner-approved versioned policy/context'}
    output.mkdir(parents=True,mode=0o700)
    atomic_json(output/'diagnostics.json',summary)
    atomic_json(output/'document-accounting.json',ledger)
    (output/'document-accounting.json').chmod(0o600)
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source','prepared','models','evaluation','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--replicates',type=int,default=2000)
    a = p.parse_args()
    result = diagnose(a.source,a.prepared,a.models,a.evaluation,a.output,a.replicates)
    print(json.dumps({'phase':'DS3','documents_accounted_for':result['document_accounting']['source_documents'],
                      'test_rows':result['strata']['full']['rows'],'training_rerun':False}))


if __name__ == '__main__': main()
