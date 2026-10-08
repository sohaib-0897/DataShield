"""Independent offline annotation packets; content never implies policy level.

Packets are private ignored artifacts. Blank review slots are not labels.
No application policy, rule classifier, model, split or training is changed.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path

from research.cert_ingest import atomic_json, local_path
from research.documents import extract_document

VERSION = 'document-taxonomy-annotation-v1'
CATEGORIES = frozenset(('PERSONAL_INFORMATION', 'FINANCIAL_INFORMATION', 'CREDENTIALS', 'BUSINESS_CONFIDENTIAL'))
LEVELS = frozenset(('NORMAL', 'HIGH', 'CRITICAL'))


def packet(path, *, source_id, family_id, policy_version=None):
    if not source_id or not family_id:
        raise ValueError('Explicit source/family grouping required')
    extracted = extract_document(path)
    # Existing extractor handles bounds and changed files. Digest binds reviewed
    # extracted content; original-file provenance is supplied by corpus inventory.
    return {'version': VERSION, 'source_id': source_id, 'family_id': family_id,
            'policy_version': policy_version, 'extraction_status': extracted['status'],
            'truncated': extracted['truncated'], 'text': extracted['text'],
            'text_sha256': hashlib.sha256(extracted['text'].encode()).hexdigest(),
            'reviews': [{'reviewer_id': None, 'label_origin': 'independent_human',
                         'categories': None, 'organizational_level': None, 'context': None}
                        for _ in range(2)], 'adjudication': None,
            'status': 'AWAITING_INDEPENDENT_REVIEWS', 'training_eligible': False}


def validate_review(review):
    if not isinstance(review, dict) or review.get('label_origin') != 'independent_human':
        raise ValueError('Only independent human reviews are ground truth')
    if not isinstance(review.get('reviewer_id'), str) or not review['reviewer_id'].strip():
        raise ValueError('Reviewer provenance required')
    categories = review.get('categories')
    if not isinstance(categories, list) or any(c not in CATEGORIES for c in categories) or len(set(categories)) != len(categories):
        raise ValueError('Explicit reviewed categories required')
    level = review.get('organizational_level')
    if level is not None and level not in LEVELS:
        raise ValueError('Unsupported organizational level')
    if level is not None or 'BUSINESS_CONFIDENTIAL' in categories:
        context = review.get('context')
        required = ('owner_review_id', 'policy_version', 'authorized_audience', 'release_status', 'harm_rationale')
        if not isinstance(context, dict) or any(not isinstance(context.get(k), str) or not context[k].strip() for k in required):
            raise ValueError('Organizational level requires owner/policy/context evidence')
    return tuple(sorted(categories)), level


def adjudicate(value):
    """Validate completed independent judgments; no label inferred from text/rules."""
    result = deepcopy(value)
    if result.get('version') != VERSION or not result.get('source_id') or not result.get('family_id'):
        raise ValueError('Incompatible annotation packet')
    if result.get('extraction_status') != 'OK' or result.get('truncated') is not False:
        raise ValueError('Unavailable/partial extraction cannot support these text labels')
    text = result.get('text')
    if not isinstance(text, str) or not text.strip() or hashlib.sha256(text.encode()).hexdigest() != result.get('text_sha256'):
        raise ValueError('Reviewed text digest mismatch')
    reviews = result.get('reviews')
    if not isinstance(reviews, list) or len(reviews) != 2:
        raise ValueError('Two independent reviews required')
    judgments = [validate_review(r) for r in reviews]
    for review in reviews:
        if review.get('context') and review['context'].get('policy_version') != result.get('policy_version'):
            raise ValueError('Annotation policy version mismatch')
    if reviews[0]['reviewer_id'] == reviews[1]['reviewer_id']:
        raise ValueError('Two different reviewers required')
    if judgments[0] == judgments[1]:
        chosen = reviews[0]
    else:
        resolution = result.get('adjudication')
        if not isinstance(resolution, dict) or not isinstance(resolution.get('reason'), str) or not resolution['reason'].strip():
            raise ValueError('Disagreement requires documented adjudication')
        validate_review(resolution)
        if resolution['reviewer_id'] in {r['reviewer_id'] for r in reviews}:
            raise ValueError('Disagreement requires a third reviewer')
        chosen = resolution
    if chosen.get('context') and chosen['context']['policy_version'] != result.get('policy_version'):
        raise ValueError('Annotation policy version mismatch')
    result.update(status='HUMAN_REVIEWED', categories=list(chosen['categories']),
                  organizational_level=chosen.get('organizational_level'),
                  category_training_eligible=True,
                  organizational_training_eligible=chosen.get('organizational_level') is not None,
                  training_eligible=True)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', type=Path, help='Local document to extract into a blank review packet')
    mode.add_argument('--adjudicate', type=Path, help='Private packet with completed human reviews')
    p.add_argument('--source-id')
    p.add_argument('--family-id')
    p.add_argument('--policy-version')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    folder = Path('research/local').absolute()
    output = local_path(folder, a.output)
    if output.exists():
        raise ValueError('Preserve previous packet; new output required')
    if a.prepare:
        result = packet(a.prepare, source_id=a.source_id, family_id=a.family_id, policy_version=a.policy_version)
    else:
        source = local_path(folder, a.adjudicate)
        if source.stat().st_size > 4 * 1024**2:
            raise ValueError('Annotation packet byte bound exceeded')
        result = adjudicate(json.loads(source.read_text()))
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    atomic_json(output, result)
    output.chmod(0o600)
    print(json.dumps({'status': result['status'], 'training_performed': False}))


if __name__ == '__main__':
    main()
