"""Opt-in offline extraction + automatic detection; print redacted evidence only."""
import argparse
import json

from ml.content_detection import VERSION, detect_content
from research.documents import extract_document


def document_candidates(path):
    extraction = extract_document(path)
    available = extraction['status'] == 'OK'
    return {'version': VERSION, 'extraction_status': extraction['status'],
            'extraction_truncated': extraction['truncated'],
            'extracted_chars': len(extraction['text']),
            'detection_status': 'AVAILABLE' if available else 'UNAVAILABLE_EXTRACTION',
            'detection': detect_content(extraction['text']) if available else None,
            'extraction_complete': available and not extraction['truncated'],
            'organizational_sensitivity': None, 'review_needed': True,
            'automated_blocking': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path')
    args = parser.parse_args()
    print(json.dumps(document_candidates(args.path), sort_keys=True))


if __name__ == '__main__':
    main()
