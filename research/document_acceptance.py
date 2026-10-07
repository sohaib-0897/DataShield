"""Run bounded SYNTHETIC extraction acceptance and publish text-free evidence."""
import argparse
from importlib.metadata import version
from pathlib import Path
import time

from research.cert_ingest import atomic_json, encoded, local_path, require_space
from research.document_fixtures import make_fixtures
from research.documents import DEFAULTS, document_evidence

EXPECTED = {'report.txt': 'OK', 'report.pdf': 'OK', 'report.docx': 'OK', 'encrypted.pdf': 'ENCRYPTED',
            'no_text.pdf': 'SCANNED_OR_NO_TEXT', 'empty.txt': 'EMPTY', 'unsupported.xlsx': 'UNSUPPORTED',
            'malformed.pdf': 'MALFORMED', 'malformed.docx': 'MALFORMED', 'malformed.txt': 'MALFORMED'}


def accept(output, folder):
    output = local_path(folder, output)
    if output.exists():
        raise ValueError('Acceptance output exists; preserve it and choose a new directory')
    require_space(folder)
    output.mkdir()
    fixture_paths = make_fixtures(output / 'synthetic_documents')
    start = time.perf_counter()
    results = {}
    for path in fixture_paths:
        result = document_evidence(path)
        if result['extraction_status'] != EXPECTED[path.name]:
            raise RuntimeError('Synthetic extraction acceptance status mismatch')
        if path.name.startswith('report.') and {e['type'] for e in result['pii_evidence']} != {'email_address', 'cnic_like'}:
            raise RuntimeError('Synthetic evidence acceptance mismatch')
        results[path.name] = result
    report = {'kind': 'SYNTHETIC_TEST_ONLY_NOT_A_SENSITIVITY_CORPUS', 'documents': len(results),
              'passed_status_checks': len(results), 'results': results, 'limits': DEFAULTS,
              'timeout_seconds': 8, 'seconds': time.perf_counter() - start,
              'software': {p: version(p) for p in ('pypdf', 'python-docx', 'lxml')},
              'raw_text_logged': False, 'sensitivity_model_trained': False, 'live_data_used': False}
    atomic_json(output / 'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = accept(args.output, Path('research/local').absolute())
    print(encoded({k: v for k, v in report.items() if k != 'results'}))


if __name__ == '__main__':
    main()
