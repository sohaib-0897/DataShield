"""Acquire and structurally audit the reviewed TAB release; never train or split.

Raw judgments/annotator IDs stay in ignored research/local. Reports contain only
hashes, counters and schema findings. Upstream split assignments are preserved.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import time
import urllib.request
import zipfile

from research.cert_ingest import atomic_json, hash_file, local_path, require_space

REVISION = '558e09e26d6b36f5f78440074e6a233946d98bd9'
REPOSITORY = 'https://github.com/NorskRegnesentral/text-anonymization-benchmark'
FILES = ('LICENSE.txt', 'README.md', 'guidelines.md', 'echr_train.json', 'echr_dev.json', 'echr_test.json')
ENTITY_TYPES = frozenset(('PERSON', 'CODE', 'LOC', 'ORG', 'DEM', 'DATETIME', 'QUANTITY', 'MISC'))
IDENTIFIER_TYPES = frozenset(('DIRECT', 'QUASI', 'NO_MASK'))
CONFIDENTIAL_TYPES = frozenset(('BELIEF', 'POLITICS', 'SEX', 'ETHNIC', 'HEALTH', 'NOT_CONFIDENTIAL'))
FILE_LIMIT = 64 * 1024**2


def import_archive(archive_path, tree_path, output, folder):
    """Import only six reviewed files; verify pinned Git blob IDs before publish.

    GitHub's pinned tree response must be independently acquired over HTTPS.
    Never extract archive paths, execute source code, or trust a partial download.
    """
    archive_path = local_path(folder, archive_path)
    tree_path = local_path(folder, tree_path)
    output = local_path(folder, output)
    if output.exists():
        raise ValueError('Preserve acquisition; choose a new output directory')
    if archive_path.stat().st_size > FILE_LIMIT or tree_path.stat().st_size > 1024**2:
        raise ValueError('Archive/tree byte bound exceeded')
    tree = json.loads(tree_path.read_text())
    if tree.get('sha') != REVISION or tree.get('truncated') is not False:
        raise ValueError('Pinned tree provenance mismatch')
    expected = {e['path']: e for e in tree['tree'] if e['path'] in FILES}
    if set(expected) != set(FILES):
        raise ValueError('Missing reviewed files in pinned tree')
    require_space(folder, 256 * 1024**2)
    prefix = f'text-anonymization-benchmark-{REVISION}/'
    entries = []
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        # Validate every selected member before creating any trusted destination.
        for name in FILES:
            full = prefix + name
            if names.count(full) != 1:
                raise ValueError('Missing or duplicate archive member')
            info = archive.getinfo(full)
            if info.file_size != expected[name]['size'] or info.file_size > FILE_LIMIT:
                raise ValueError('Archive member size mismatch')
            value = archive.read(info)
            git_hash = hashlib.sha1(b'blob ' + str(len(value)).encode() + b'\0' + value).hexdigest()
            if git_hash != expected[name]['sha']:
                raise ValueError('Pinned Git blob mismatch')
            if name == 'LICENSE.txt' and b'The MIT License' not in value:
                raise ValueError('Reviewed license contract changed')
        output.mkdir(parents=True, mode=0o700)
        for name in FILES:
            value = archive.read(prefix + name)
            with (output / name).open('xb') as stream:
                stream.write(value)
            (output / name).chmod(0o600)
            entries.append({'file': name, 'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest(),
                            'git_blob_sha1': expected[name]['sha'],
                            'url': f'https://raw.githubusercontent.com/NorskRegnesentral/text-anonymization-benchmark/{REVISION}/{name}'})
    manifest = {'repository': REPOSITORY, 'revision': REVISION, 'license': 'MIT', 'files': entries,
                'acquisition_method': 'pinned GitHub archive; every selected member verified against pinned API tree',
                'archive_url': f'https://codeload.github.com/NorskRegnesentral/text-anonymization-benchmark/zip/{REVISION}',
                'archive': hash_file(archive_path), 'tree': hash_file(tree_path)}
    atomic_json(output / 'acquisition.json', manifest)
    return manifest


def acquire(output, folder):
    """New destination only; a failed download never publishes acquisition.json."""
    output = local_path(folder, output)
    if output.exists():
        raise ValueError('Preserve acquisition; choose a new output directory')
    require_space(folder, 256 * 1024**2)
    output.mkdir(parents=True, mode=0o700)
    entries = []
    for name in FILES:
        url = f'https://raw.githubusercontent.com/NorskRegnesentral/text-anonymization-benchmark/{REVISION}/{name}'
        path = output / name
        partial = output / (name + '.partial')
        started = time.perf_counter()
        with urllib.request.urlopen(url, timeout=20) as response, partial.open('xb') as stream:
            digest, size = hashlib.sha256(), 0
            for block in iter(lambda: response.read(1024**2), b''):
                size += len(block)
                if size > FILE_LIMIT:
                    raise ValueError('TAB download byte bound exceeded')
                digest.update(block)
                stream.write(block)
        partial.rename(path)
        if name == 'LICENSE.txt' and 'The MIT License' not in path.read_text():
            raise ValueError('Reviewed license contract changed')
        entries.append({'file': name, 'url': url, 'bytes': size, 'sha256': digest.hexdigest(),
                        'seconds': time.perf_counter() - started})
        print(json.dumps({'downloaded_file': name, 'bytes': size}), flush=True)
    manifest = {'repository': REPOSITORY, 'revision': REVISION, 'license': 'MIT', 'files': entries}
    atomic_json(output / 'acquisition.json', manifest)
    return manifest


def inspect_documents(documents, split):
    """Validate offsets and count separate annotator sets, not independent samples."""
    if not isinstance(documents, list) or not documents:
        raise ValueError('TAB requires a nonempty document list')
    ids, texts = set(), set()
    counts, entities, identifiers, confidential = Counter(), Counter(), Counter(), Counter()
    findings = Counter()
    for doc in documents:
        if not isinstance(doc, dict) or not {'doc_id', 'text', 'annotations', 'dataset_type', 'quality_checked', 'task', 'meta'} <= doc.keys():
            raise ValueError('Unsupported TAB document schema')
        if not isinstance(doc['doc_id'], str) or not doc['doc_id'] or doc['doc_id'] in ids:
            raise ValueError('Duplicate or missing TAB document ID')
        if doc['dataset_type'] != split or not isinstance(doc['text'], str) or not doc['text'].strip():
            raise ValueError('Invalid TAB split/text')
        if not isinstance(doc['annotations'], dict) or not doc['annotations']:
            raise ValueError('Missing TAB annotations')
        ids.add(doc['doc_id'])
        text_hash = hashlib.sha256(doc['text'].encode()).hexdigest()
        if text_hash in texts:
            findings['duplicate_document_text_within_split'] += 1
        texts.add(text_hash)
        counts['documents'] += 1
        counts['text_characters'] += len(doc['text'])
        counts['documents_over_extractor_character_limit'] += int(len(doc['text']) > 32768)
        # quality_checked can be release-specific metadata. Count its actual
        # structure, never guess that any truthy value means all reviews complete.
        if isinstance(doc['quality_checked'], list):
            reviewed = doc['quality_checked']
            if len(set(reviewed)) != len(reviewed) or any(a not in doc['annotations'] for a in reviewed):
                raise ValueError('Invalid TAB quality-review references')
            counts['quality_reviewed_annotation_sets'] += len(reviewed)
            counts['quality_checked_documents'] += int(bool(reviewed))
        elif isinstance(doc['quality_checked'], dict):
            counts['quality_reviewed_annotation_sets'] += sum(v is True for v in doc['quality_checked'].values())
        elif type(doc['quality_checked']) is bool:
            counts['quality_checked_documents'] += int(doc['quality_checked'])
        else:
            findings['quality_checked_non_boolean_metadata'] += 1
        for annotation in doc['annotations'].values():
            if not isinstance(annotation, dict) or not isinstance(annotation.get('entity_mentions'), list):
                raise ValueError('Unsupported TAB annotation schema')
            counts['annotation_sets'] += 1
            mention_ids = set()
            for mention in annotation['entity_mentions']:
                required = {'entity_type', 'start_offset', 'end_offset', 'span_text', 'identifier_type', 'confidential_status', 'entity_mention_id'}
                if not isinstance(mention, dict) or not required <= mention.keys():
                    raise ValueError('Unsupported TAB mention schema')
                start, end = mention['start_offset'], mention['end_offset']
                if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(doc['text']):
                    raise ValueError('TAB span offset outside text')
                if doc['text'][start:end] != mention['span_text']:
                    raise ValueError('TAB span text/offset mismatch')
                if mention['entity_mention_id'] in mention_ids:
                    raise ValueError('Duplicate mention in annotator set')
                mention_ids.add(mention['entity_mention_id'])
                if mention['entity_type'] not in ENTITY_TYPES or mention['identifier_type'] not in IDENTIFIER_TYPES:
                    raise ValueError('Unexpected TAB entity/identifier label')
                # Confidential attributes are only applicable to some entities.
                label = mention['confidential_status']
                if label is not None and label not in CONFIDENTIAL_TYPES:
                    raise ValueError('Unexpected TAB confidential attribute')
                counts['mention_annotation_records'] += 1
                entities[mention['entity_type']] += 1
                identifiers[mention['identifier_type']] += 1
                confidential[label or 'NOT_APPLICABLE'] += 1
    report = {'counts': dict(counts), 'entity_type_annotation_counts': dict(entities),
              'identifier_type_annotation_counts': dict(identifiers),
              'confidential_status_annotation_counts': dict(confidential), 'findings': dict(findings),
              'count_unit': 'raw mention annotation records; multi-annotator mentions are not independent examples'}
    return report, ids, texts


def inventory(directory, folder):
    directory = local_path(folder, directory)
    started = time.perf_counter()
    manifest_path = local_path(folder, directory / 'acquisition.json')
    if manifest_path.stat().st_size > 1024**2:
        raise ValueError('Acquisition manifest byte bound')
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('revision') != REVISION or manifest.get('repository') != REPOSITORY or manifest.get('license') != 'MIT':
        raise ValueError('TAB acquisition provenance mismatch')
    entries = manifest.get('files', [])
    if len(entries) != len(FILES) or {e['file'] for e in entries} != set(FILES):
        raise ValueError('Incomplete TAB acquisition')
    for entry in entries:
        expected_url = f'https://raw.githubusercontent.com/NorskRegnesentral/text-anonymization-benchmark/{REVISION}/{entry["file"]}'
        if entry['url'] != expected_url:
            raise ValueError('TAB source URL mismatch')
        path = local_path(folder, directory / entry['file'])
        if path.stat().st_size > FILE_LIMIT or hash_file(path) != {'sha256': entry['sha256'], 'bytes': entry['bytes']}:
            raise ValueError('TAB file changed or byte bound exceeded')
    reports, prior_ids, prior_text = {}, set(), set()
    for split in ('train', 'dev', 'test'):
        values = json.loads((directory / f'echr_{split}.json').read_text())
        report, ids, texts = inspect_documents(values, split)
        report['shared_document_ids_with_earlier_splits'] = len(ids & prior_ids)
        report['shared_exact_texts_with_earlier_splits'] = len(texts & prior_text)
        reports[split] = report
        prior_ids.update(ids)
        prior_text.update(texts)
        del values
    return {'version': 'tab-acquisition-inventory-v1', 'source': REPOSITORY, 'revision': REVISION,
            'license': 'MIT; retain copyright and permission notice', 'acquisition': manifest,
            'splits_as_supplied_not_training_approved': reports,
            'tasks_supported': ['provided-entity-span semantic category classification'],
            'organizational_level_labels': False, 'near_duplicate_case_family_audit': 'PENDING_DS2',
            'training_performed': False, 'validation_performed': False,
            'seconds': time.perf_counter() - started,
            'peak_rss_mib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--acquire', action='store_true')
    p.add_argument('--archive', type=Path)
    p.add_argument('--tree', type=Path)
    a = p.parse_args()
    folder = Path('research/local').absolute()
    report = local_path(folder, a.report)
    if report.exists() or report == a.directory.absolute():
        raise ValueError('New separate report required')
    if bool(a.archive) != bool(a.tree) or (a.archive and a.acquire):
        raise ValueError('Use either direct acquisition or archive plus pinned tree')
    if a.archive:
        import_archive(a.archive, a.tree, a.directory, folder)
    elif a.acquire:
        acquire(a.directory, folder)
    result = inventory(a.directory, folder)
    atomic_json(report, result)
    print(json.dumps({'training_performed': False, 'report': str(report), 'seconds': result['seconds']}))

if __name__ == '__main__':
    main()
