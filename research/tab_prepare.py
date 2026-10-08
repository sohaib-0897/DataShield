"""Freeze offline supplied-span category manifests; never infer organizational labels."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from research.cert_ingest import atomic_json, hash_file, local_path
from research.tab_inventory import ENTITY_TYPES, inventory
from research.tab_acquire import TREE_SHA256, verify_blob

VERSION = 'tab-supplied-span-ds2-v1'
TASK = 'supplied-span entity-category classification; spans are provided'
CLASSES = sorted(ENTITY_TYPES)


def normalized(text):
    return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKC', text).casefold()))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def consensus(doc):
    """Use only reviewed sets; keep exact-span category unanimity, no voting gold."""
    reviewed = doc['quality_checked']
    sets = {}
    duplicate_counts = Counter()
    for annotator, annotation in doc['annotations'].items():
        values = defaultdict(set)
        totals = Counter()
        for m in annotation['entity_mentions']:
            span = (m['start_offset'], m['end_offset'])
            values[span].add(m['entity_type']); totals[span] += 1
        duplicate_counts['duplicate_offsets_within_annotation_set'] += sum(v-1 for v in totals.values())
        duplicate_counts['conflicting_duplicate_offsets_within_annotation_set'] += sum(len(v)>1 for v in values.values())
        if annotator in reviewed:
            sets[annotator] = values
    all_spans = defaultdict(set)
    for ann in doc['annotations'].values():
        for m in ann['entity_mentions']:
            all_spans[(m['start_offset'], m['end_offset'])].add(m['entity_type'])
    audit = Counter(raw_exact_spans=len(all_spans), raw_category_disagreements=sum(len(v) > 1 for v in all_spans.values()))
    audit.update(duplicate_counts)
    if not sets:
        audit['unreviewed_documents'] += 1
        return [], dict(audit)
    union = set().union(*(set(v) for v in sets.values()))
    kept = []
    for span in sorted(union):
        labels = [s.get(span) for s in sets.values()]
        if None in labels:
            audit['reviewed_boundary_or_presence_disagreements'] += 1
        elif any(len(v) != 1 for v in labels) or len(set().union(*labels)) != 1:
            audit['reviewed_category_disagreements'] += 1
        else:
            kept.append((*span, next(iter(labels[0]))))
    audit['eligible_consensus_spans'] = len(kept)
    # Boundary overlaps remain an audit outcome; they are not entity detection examples.
    ends = []
    for start, end in sorted(union):
        audit['overlapping_reviewed_span_pairs'] += sum(e > start for e in ends)
        ends.append(end)
    return kept, dict(audit)


def group_documents(docs, threshold=.8):
    parent = list(range(len(docs)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    edges = []
    def union(i, j, reason):
        a, b = find(i), find(j)
        if a != b: parent[max(a,b)] = min(a,b)
        edges.append([i, j, reason])
    seen = {}
    shingles = []
    for i, d in enumerate(docs):
        norm = normalized(d['text'])
        keys = [('doc_id', d['doc_id']), ('normalized_text', digest(norm))]
        # Source task is the protected subject; applicant identifies related cases.
        for field, value in [('protected_subject', d['task']), ('applicant', d['meta'].get('applicant', ''))]:
            key = normalized(value)
            if key: keys.append(('subject', key))
        for key in keys:
            if key in seen: union(i, seen[key], key[0])
            else: seen[key] = i
        words = norm.split()
        shingles.append(set(tuple(words[k:k+5]) for k in range(max(0,len(words)-4))))
    # Exhaustive length-filtered comparison; no approximate candidate search misses.
    near_count = 0
    for i, left in enumerate(shingles):
        for j in range(i):
            right = shingles[j]
            if not left or not right or min(len(left),len(right))/max(len(left),len(right)) < threshold: continue
            common = len(left & right)
            if common / (len(left)+len(right)-common) >= threshold:
                near_count += 1; union(i,j,'five_word_jaccard_ge_0.8')
    groups = [digest(sorted(docs[j]['doc_id'] for j in range(len(docs)) if find(j)==find(i))) for i in range(len(docs))]
    return groups, edges, near_count


def prepare(directory, output):
    folder = Path('research/local').absolute()
    directory, output = local_path(folder,directory), local_path(folder,output)
    if output.exists(): raise ValueError('New preparation output required')
    tree_path = directory.parent / 'tab-tree.json'
    if hash_file(tree_path)['sha256'] != TREE_SHA256: raise ValueError('Pinned tree mismatch')
    tree = json.loads(tree_path.read_text())
    from research.tab_inventory import FILES
    for entry in tree['tree']:
        if entry['path'] in FILES: verify_blob(directory / entry['path'], entry)
    inv = inventory(directory,folder)  # Completeness, pinned acquisition, schema, offsets before preparation.
    docs = []
    for split in ('train','dev','test'):
        docs.extend(json.loads((directory/f'echr_{split}.json').read_text()))
    if len(docs)>2000: raise ValueError('Document bound exceeded')
    groups, edges, near = group_documents(docs)
    assignments = defaultdict(set)
    for d,g in zip(docs,groups): assignments[g].add(d['dataset_type'])
    # Preserve official test; quarantine related earlier materials. Validation wins over train.
    preferred = {g: 'test' if 'test' in s else 'dev' if 'dev' in s else 'train' for g,s in assignments.items()}
    output.mkdir(parents=True,mode=0o700)
    audit, records, manifest = Counter(), {s:[] for s in ('train','validation','test')}, []
    repeated = defaultdict(set)
    for i,(d,g) in enumerate(zip(docs,groups)):
        spans, findings = consensus(d);audit.update(findings)
        retained = preferred[g] == d['dataset_type']
        split = 'validation' if d['dataset_type']=='dev' else d['dataset_type']
        if not retained: audit['quarantined_family_overlap_documents'] += 1
        for ann in d['annotations'].values():
            for m in ann['entity_mentions']:
                repeated[(m['entity_type'],normalized(m['span_text']))].add(i)
        doc_entry={'source_doc_sha256':digest(d['doc_id']), 'text_sha256':hashlib.sha256(d['text'].encode()).hexdigest(),
                   'original_record_sha256':digest(d), 'group':g, 'official_split':d['dataset_type'],
                   'retained':retained, 'reviewed_sets':len(d['quality_checked']), 'eligible_spans':len(spans)}
        manifest.append(doc_entry)
        if retained:
            for start,end,label in spans:
                # No metadata, task, reviewer ID, masking/confidential labels in inputs.
                records[split].append({'id':digest([d['doc_id'],start,end]),'group':g,
                    'document':doc_entry['source_doc_sha256'],'start':start,'end':end,'label':label,
                    'entity':d['text'][start:end],
                    'context':d['text'][max(0,start-160):start]+' [SPAN] '+d['text'][start:end]+' [/SPAN] '+d['text'][end:end+160],
                    'ambiguous_raw_category':len({m['entity_type'] for a in d['annotations'].values() for m in a['entity_mentions']
                        if (m['start_offset'],m['end_offset'])==(start,end)})>1})
    # Repeated text/identities are audited, not equated with document families (e.g. court/location names).
    repetitions={'entity_strings_in_multiple_documents':sum(len(v)>1 for v in repeated.values()),
                 'entity_strings_in_multiple_official_splits':sum(len({docs[i]['dataset_type'] for i in v})>1 for v in repeated.values()),
                 'person_strings_in_multiple_official_splits':sum(k[0]=='PERSON' and len({docs[i]['dataset_type'] for i in v})>1 for k,v in repeated.items())}
    hashes={}
    for split,rows in records.items():
        atomic_json(output/f'{split}.json',rows);(output/f'{split}.json').chmod(0o600)
        hashes[split]=hash_file(output/f'{split}.json')
    atomic_json(output/'documents.json',manifest)
    atomic_json(output/'group-edges.json',edges)
    group_sets={s:{r['group'] for r in rows} for s,rows in records.items()}
    assert not any(group_sets[a]&group_sets[b] for a,b in [('train','validation'),('train','test'),('validation','test')])
    report={'version':VERSION,'task':TASK,'revision':inv['revision'],'license':inv['license'],
        'acquisition':inv['acquisition'],'source_inventory':inv['splits_as_supplied_not_training_approved'],
        'classes':CLASSES,'mapping':{c:c for c in CLASSES},'organizational_category_mapping':None,
        'unsupported_organizational_targets':['PERSONAL_INFORMATION','FINANCIAL_INFORMATION','CREDENTIALS','BUSINESS_CONFIDENTIAL','NORMAL','HIGH','CRITICAL'],
        'annotation_policy':'reviewed sets only; exact spans unanimous across every reviewed set; disagreements abstain; unreviewed documents excluded',
        'grouping':'source doc_id, NFKC lowercase alphanumeric normalized text, protected task/applicant identity, exhaustive five-word Jaccard >=0.8; transitive closure',
        'official_split_policy':'official test unchanged; quarantine earlier overlapping families; validation wins over train',
        'documents':len(docs),'groups':len(assignments),'cross_official_split_groups':sum(len(v)>1 for v in assignments.values()),
        'near_duplicate_pairs':near,'group_edge_reasons':dict(Counter(e[2] for e in edges)),
        'annotation_audit':dict(audit),'repeated_mentions':repetitions,
        'splits':{s:{'spans':len(rows),'documents':len({r['document'] for r in rows}),'groups':len(group_sets[s]),
                     'class_counts':dict(Counter(r['label'] for r in rows))} for s,rows in records.items()},
        'manifest_hashes':hashes,'document_manifest':hash_file(output/'documents.json'),
        'group_edges':hash_file(output/'group-edges.json'),'cross_split_group_overlap':0,
        'context_characters_each_side':160,'fit_partition':'train','selection_partition':'validation',
        'test_access':'mechanical inventory/grouping only; no fitted transforms or model selection',
        'organizational_labels':False,'live_activation':False}
    atomic_json(output/'preparation.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();r=prepare(a.directory,a.output)
    print(json.dumps({'splits':r['splits'],'audit':r['annotation_audit']}))


if __name__=='__main__': main()
