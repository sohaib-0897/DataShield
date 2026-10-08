"""Bounded local candidate detection, independent of TAB models and live rules.

Results contain offsets and validation reasons, never matched values. A candidate
category is not a confidentiality decision or an independently reviewed label.
"""
import re

VERSION = 'structured-content-detectors-v1'
MAX_CHARS = 32768
MAX_BYTES = 131072
MAX_SPANS = 100
OFFSET_UNIT = 'unicode_code_points; start inclusive, end exclusive'

EMAIL = re.compile(r"(?<![\w.!#$%&'*+/=?^`{|}~@-])"
                   r"[A-Za-z0-9.!#$%&'*+/=?^`{|}~-]{1,64}@[A-Za-z0-9.-]{1,253}"
                   r"(?![\w@.-])")
CNIC = re.compile(r'(?<![\w-])[0-9]{5}-[0-9]{7}-[0-9](?![\w-])')
# SWIFT IBAN Registry release 103 (Sep 2026), DE/GB/PK only. These
# national structures and MOD97 check digits do not prove an account exists.
IBAN_STRUCTURES = {'DE': r'DE[0-9]{20}', 'GB': r'GB[0-9]{2}[A-Z]{4}[0-9]{14}',
                   'PK': r'PK[0-9]{2}[A-Z]{4}[A-Z0-9]{16}'}
IBANS = {}
for _country, _length in [('DE', 22), ('GB', 22), ('PK', 24)]:
    _groups, _tail = divmod(_length, 4)
    _spaced = rf'{_country}[0-9]{{2}}(?: [A-Z0-9]{{4}}){{{_groups-1}}}'
    if _tail:
        _spaced += rf' [A-Z0-9]{{{_tail}}}'
    IBANS[_country] = re.compile(rf'(?<!\w)(?:{_spaced}|{_country}[0-9]{{2}}[A-Z0-9]{{{_length-4}}})(?!\w)')

# Deliberately limited to same-line explicit assignments; quoted values have
# no escapes, unquoted values are ASCII tokens. Offsets identify the value only.
CREDENTIAL = re.compile(
    r'''(?<![\w"'-])(?P<quote>["']?)(?P<key>password|api_key|access_token|client_secret)(?P=quote)'''
    r'''[ \t]{0,8}[:=][ \t]{0,8}(?:"(?P<double>[^"\r\n\\]{8,256})"'''
    r'''|'(?P<single>[^'\r\n\\]{8,256})'|(?P<bare>[A-Za-z0-9_./+!@#$%^-]{8,256})(?![\w./+!@#$%^-]))''',
    re.IGNORECASE | re.ASCII)

LIMITATIONS = {
    'email_address': ['ASCII unquoted addresses only; no DNS, mailbox or ownership verification',
                      'Public contact information does not establish confidentiality'],
    'cnic_like': ['Format only; no official issuance, checksum or identity verification'],
    'iban': ['Only DE, GB and PK; uppercase compact or single-space four-character groups',
             'Structure/checksum only; no account, ownership or confidentiality verification'],
    'credential_assignment': ['Only explicit password/api_key/access_token/client_secret assignments',
                              '8–256 characters; examples/placeholders may match; validity is unverified',
                              'No obfuscated, escaped, multiline, key-block or prose secret detection'],
}


def valid_email(value):
    local, domain = value.rsplit('@', 1)
    labels = domain.split('.')
    return (len(value) <= 254 and not local.startswith('.') and not local.endswith('.')
            and '..' not in local and len(labels) >= 2
            and all(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', p) for p in labels)
            and re.fullmatch(r'[A-Za-z]{2,63}', labels[-1]) is not None)


def valid_iban(value):
    compact = value.replace(' ', '')
    structure = IBAN_STRUCTURES.get(compact[:2])
    if not structure or not re.fullmatch(structure, compact):
        return False
    if not 2 <= int(compact[2:4]) <= 98:
        return False
    rearranged = compact[4:] + compact[:4]
    digits = ''.join(c if c.isdigit() else str(ord(c)-55) for c in rearranged)
    return int(digits) % 97 == 1


def detect_content(text, *, max_spans=MAX_SPANS):
    """Detect supported candidates without caller spans or classifier inference.

    Reject excess input rather than silently truncate. Output truncation retains
    the earliest candidates by offset, reports total accepted candidates and
    remains incomplete. Overlaps may have different meanings; never sum as risk.
    """
    if not isinstance(text, str) or len(text) > MAX_CHARS or '\0' in text:
        raise ValueError('Expected bounded text without NUL characters')
    try:
        size = len(text.encode('utf-8'))
    except UnicodeEncodeError:
        raise ValueError('Expected valid Unicode text') from None
    if size > MAX_BYTES or type(max_spans) is not int or not 1 <= max_spans <= MAX_SPANS:
        raise ValueError('Detection bounds exceeded')
    spans = []

    def add(start, end, kind, category, checks):
        spans.append({'start': start, 'end': end, 'kind': kind, 'category': category,
                      'status': 'CANDIDATE', 'method': 'DETERMINISTIC_PATTERN_AND_VALIDATION',
                      'detector_version': VERSION, 'evidence': {'checks_passed': checks},
                      'limitations': list(LIMITATIONS[kind])})

    for match in EMAIL.finditer(text):
        value = match.group()
        # One sentence period is a delimiter; consecutive periods stay malformed.
        value = value[:-1] if value.endswith('.') and not value.endswith('..') else value
        if valid_email(value):
            add(match.start(), match.start()+len(value), 'email_address', 'PERSONAL_INFORMATION',
                ['ascii_mailbox_syntax', 'domain_label_syntax'])
    for match in CNIC.finditer(text):
        add(match.start(), match.end(), 'cnic_like', 'PERSONAL_INFORMATION', ['ascii_5_7_1_format'])
    for pattern in IBANS.values():
        for match in pattern.finditer(text):
            if valid_iban(match.group()):
                add(match.start(), match.end(), 'iban', 'FINANCIAL_INFORMATION',
                    ['supported_national_structure', 'mod97_check_digits'])
    for match in CREDENTIAL.finditer(text):
        group = next(g for g in ('double', 'single', 'bare') if match.group(g) is not None)
        if not match.group(group).strip():
            continue
        add(match.start(group), match.end(group), 'credential_assignment', 'CREDENTIALS',
            ['explicit_secret_field_assignment', 'bounded_nonempty_value'])
    spans.sort(key=lambda s: (s['start'], s['end'], s['kind']))
    return {'version': VERSION, 'task': 'automatic_structured_content_candidate_detection',
            'offset_unit': OFFSET_UNIT, 'input_chars': len(text), 'input_bytes': size,
            'spans': spans[:max_spans], 'candidate_count': len(spans),
            'spans_truncated': len(spans) > max_spans,
            'detection_complete': len(spans) <= max_spans,
            'coverage': {'supported_kinds': list(LIMITATIONS),
                         'unsupported': ['contextual PERSON/ORG/LOC/DEM/MISC/DATETIME/QUANTITY NER',
                                         'general financial prose', 'BUSINESS_CONFIDENTIAL',
                                         'other identifier/contact/secret formats']},
            'warnings': ['Candidates are not independently verified labels or evidence of confidentiality',
                         'No matches does not establish benign content; unsupported categories remain unknown',
                         'No TAB classifier, organizational policy, learned sensitivity or risk decision applied']}
