"""Read-only train/dev annotation screening; never creates gold or selects a model."""
import argparse
from collections import Counter
import json
from pathlib import Path

from research.cert_ingest import atomic_json, hash_file, local_path
from research.tab_acquire import TREE_SHA256, verify_blob
from research.tab_inventory import FILE_LIMIT, FILES, REVISION, inspect_documents
from research.tab_prepare import consensus

VERSION = 'contextual-span-feasibility-a2-v1'


def screen(documents, split):
    """Counts are source screening, before B1 family/exhaustiveness eligibility."""
    structural, _, _ = inspect_documents(documents, split)
    counts = Counter(documents=0, reviewed_documents=0, unreviewed_documents=0,
                     documents_with_reviewed_disagreement=0,
                     documents_with_consensus_overlap=0,
                     reviewed_documents_over_text_bound=0,
                     reviewed_documents_over_result_bound=0,
                     reviewed_documents_with_zero_consensus=0,
                     consensus_spans=0, consensus_overlap_pairs=0)
    annotation_audit, classes = Counter(), Counter()
    for doc in documents:
        if not isinstance(doc['quality_checked'], list):
            raise ValueError('Explicit reviewed annotation IDs required')
        spans, audit = consensus(doc)
        annotation_audit.update(audit)
        counts['documents'] += 1
        reviewed = bool(doc['quality_checked'])
        counts['reviewed_documents' if reviewed else 'unreviewed_documents'] += 1
        if not reviewed:
            continue
        counts['documents_with_reviewed_disagreement'] += int(bool(
            audit.get('reviewed_boundary_or_presence_disagreements', 0)
            or audit.get('reviewed_category_disagreements', 0)))
        counts['reviewed_documents_over_text_bound'] += int(
            len(doc['text']) > 32768 or len(doc['text'].encode('utf-8')) > 131072)
        counts['reviewed_documents_over_result_bound'] += int(len(spans) > 100)
        counts['reviewed_documents_with_zero_consensus'] += int(not spans)
        counts['consensus_spans'] += len(spans)
        classes.update(label for _, _, label in spans)
        # Half-open offsets: adjacency is not overlap. Do not flatten nested gold.
        ends, overlaps = [], 0
        for start, end, _ in spans:
            ends = [previous for previous in ends if previous > start]
            overlaps += len(ends)
            ends.append(end)
        counts['consensus_overlap_pairs'] += overlaps
        counts['documents_with_consensus_overlap'] += int(bool(overlaps))
    return {'structural': structural, 'screening': dict(counts),
            'consensus_class_counts': dict(sorted(classes.items())),
            'annotation_audit': dict(annotation_audit),
            'unannotated_text_is_verified_negative': False,
            'independent_exhaustiveness_verified': False,
            'population_status': 'SOURCE_SCREEN_ONLY_NOT_B1_ELIGIBLE_MANIFEST'}


def assess(directory, tree_path):
    root = Path('research/local').absolute()
    directory, tree_path = local_path(root, directory), local_path(root, tree_path)
    if tree_path.stat().st_size > 1024**2 or hash_file(tree_path)['sha256'] != TREE_SHA256:
        raise ValueError('Pinned TAB tree mismatch')
    tree = json.loads(tree_path.read_text(encoding='utf-8'))
    if tree.get('sha') != REVISION or tree.get('truncated') is not False:
        raise ValueError('Incomplete or incompatible TAB tree')
    selected = [entry for entry in tree['tree'] if entry['path'] in FILES]
    if len(selected) != len(FILES) or {e['path'] for e in selected} != set(FILES):
        raise ValueError('Incomplete pinned file inventory')
    hashes = {}
    for entry in selected:
        if entry['type'] != 'blob' or not 0 < entry['size'] <= FILE_LIMIT:
            raise ValueError('Unsupported pinned file bounds')
        path = local_path(root, directory / entry['path'])
        hashes[entry['path']] = verify_blob(path, entry)
    # Verify test bytes mechanically; never parse test text/annotations here.
    reports = {}
    for split in ('train', 'dev'):
        path = local_path(root, directory / f'echr_{split}.json')
        documents = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(documents, list) or len(documents) > 2000:
            raise ValueError('Source document bound exceeded')
        reports[split] = screen(documents, split)
    return {'version': VERSION, 'source_revision': REVISION, 'source_hashes': hashes,
            'splits': reports, 'test_access': 'hash only; no test JSON parsed',
            'full_span_training_ready': False,
            'blocking_gates': ['independent exhaustive target review',
                              'B1 versioned family-safe eligible population',
                              'compatible locally verified model/environment'],
            'model_selected': False, 'labels_created': 0,
            'training_or_scoring_executed': False, 'live_activation': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--tree', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = local_path(Path('research/local').absolute(), args.output)
    if output.exists():
        raise ValueError('New feasibility output required; preserve existing evidence')
    report = assess(args.directory, args.tree)
    atomic_json(output, report)
    print(json.dumps({'version': VERSION, 'full_span_training_ready': False,
                      'splits': {k: v['screening'] for k, v in report['splits'].items()}}))


if __name__ == '__main__':
    main()
