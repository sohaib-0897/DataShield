"""Synthetic detector contracts, not corpus accuracy or organizational labels."""
import json
import subprocess
import sys

import pytest

from ml.content_detection import MAX_CHARS, detect_content
from research import automatic_content


def kinds(text):
    return [s['kind'] for s in detect_content(text)['spans']]


def test_automatic_offsets_unicode_and_redacted_evidence():
    email, cnic = 'alice+ops@example.invalid', '12345-1234567-1'
    text = f'😀 e\u0301 public: {email}. identifier: {cnic}'
    result = detect_content(text)
    assert kinds(text) == ['email_address', 'cnic_like']
    for span, expected in zip(result['spans'], (email, cnic)):
        assert text[span['start']:span['end']] == expected
        assert span['category'] == 'PERSONAL_INFORMATION'
        assert span['status'] == 'CANDIDATE' and span['evidence']['checks_passed']
        assert expected not in json.dumps(result)
    assert 'unicode_code_points' in result['offset_unit']


@pytest.mark.parametrize('text', ['.alice@example.invalid', 'alice..ops@example.invalid',
                                'alice.@example.invalid', 'alice@-example.invalid',
                                'alice@example-.invalid', 'alice@example..invalid',
                                'alice@example.invalid..', 'alice@example.123',
                                'a'*65+'@example.invalid', 'a@'+'b'*64+'.invalid',
                                'élise@example.invalid', 'alice@examplé.invalid'])
def test_malformed_or_unsupported_emails_do_not_match_prefixes(text):
    assert kinds(text) == []


@pytest.mark.parametrize('iban', ['DE89370400440532013000', 'DE89 3704 0044 0532 0130 00',
                                'GB29NWBK60161331926819', 'GB29 NWBK 6016 1331 9268 19',
                                'PK36SCBL0000001123456702', 'PK36 SCBL 0000 0011 2345 6702'])
def test_supported_iban_structure_checksum_and_offsets(iban):
    text = f'Public example account ({iban}), not a confidentiality judgment.'
    result = detect_content(text)
    span, = result['spans']
    assert text[span['start']:span['end']] == iban and span['kind'] == 'iban'
    assert span['category'] == 'FINANCIAL_INFORMATION'
    assert 'mod97_check_digits' in span['evidence']['checks_passed']


@pytest.mark.parametrize('iban', ['DE88370400440532013000', 'GB29NWBK6016133192681',
                                'PK36SCBL00000011234567021', 'NL91ABNA0417164300',
                                'de89370400440532013000', 'DE89\t3704 0044 0532 0130 00',
                                'xDE89370400440532013000', 'DE89370400440532013000x'])
def test_invalid_or_unsupported_ibans_abstain(iban):
    assert kinds(iban) == []


@pytest.mark.parametrize('text', ['١٢٣٤٥-١٢٣٤٥٦٧-١', 'x12345-1234567-1',
                                '12345-1234567-12', '1234512345671'])
def test_cnic_is_explicit_ascii_shape_only(text):
    assert kinds(text) == []


@pytest.mark.parametrize('key,value', [('password', 'inert-secret-123'),
                                    ('api_key', 'placeholder123'),
                                    ('access_token', 'not-a-real-token'),
                                    ('CLIENT_SECRET', 'another-fixture')])
def test_credential_assignments_are_candidates_and_value_offsets(key, value):
    text = f'😀 {{"{key}": "{value}"}}'
    span, = detect_content(text)['spans']
    assert text[span['start']:span['end']] == value
    assert span['category'] == 'CREDENTIALS' and span['status'] == 'CANDIDATE'
    assert value not in json.dumps(span)


@pytest.mark.parametrize('text', ['A password must be chosen carefully.', 'username=alice@example.invalid',
                                'password=short', 'password="        "',
                                'password="escaped\\nvalue"', 'password="line\nbreak-secret"',
                                '"password=inert-secret-123', 'password"=inert-secret-123',
                                '"password\'=inert-secret-123',
                                'password='+('a'*257), 'password="'+('a'*257)+'"'])
def test_secret_discussion_and_unsupported_assignments_not_credentials(text):
    assert 'credential_assignment' not in kinds(text)


def test_public_contact_unknown_entities_and_no_model_or_policy_call(monkeypatch):
    import ml.supplied_spans
    monkeypatch.setattr(ml.supplied_spans.service, 'get', lambda: pytest.fail('No TAB classifier should load'))
    assert kinds('Alice joined Example Corp in London in 2024.') == []
    result = detect_content('Public directory: support@example.invalid')
    assert result['spans'][0]['category'] == 'PERSONAL_INFORMATION'
    assert 'sensitivity' not in result and 'score' not in result
    assert 'BUSINESS_CONFIDENTIAL' in result['coverage']['unsupported']


def test_result_limit_preserves_earliest_offsets_and_reports_incomplete():
    text = 'api_key=inert-secret-123 ' + ' '.join(f'u{i}@example.invalid' for i in range(130))
    result = detect_content(text)
    assert result['candidate_count'] == 131 and len(result['spans']) == 100
    assert result['spans'][0]['kind'] == 'credential_assignment'
    assert result['spans_truncated'] and not result['detection_complete']
    assert len(detect_content(text, max_spans=1)['spans']) == 1


@pytest.mark.parametrize('text,max_spans', [(None, 100), (123, 100), ('a'*(MAX_CHARS+1), 100),
                                          ('\ud800', 100), ('a\0b', 100), ('ok', True),
                                          ('ok', 0), ('ok', 101)])
def test_invalid_inputs_are_rejected_without_echo(text, max_spans):
    with pytest.raises(ValueError) as exc:
        detect_content(text, max_spans=max_spans)
    assert 'surrogates' not in str(exc.value)


def test_empty_and_maximum_input_contract():
    assert detect_content('')['candidate_count'] == 0
    assert detect_content('😀'*MAX_CHARS)['input_bytes'] == 131072


@pytest.mark.parametrize('status,truncated', [('UNREADABLE', False), ('MALFORMED', False),
                                           ('ENCRYPTED', False), ('SCANNED_OR_NO_TEXT', False),
                                           ('UNSUPPORTED', False), ('TIMEOUT', False),
                                           ('EMPTY', False), ('OK', True)])
def test_extraction_unavailable_and_truncated_are_explicit(monkeypatch, status, truncated):
    monkeypatch.setattr(automatic_content, 'extract_document',
                        lambda path: {'status': status, 'truncated': truncated,
                                      'text': 'public@example.invalid' if status == 'OK' else ''})
    result = automatic_content.document_candidates('ignored')
    assert not result['extraction_complete']
    assert result['review_needed'] and result['organizational_sensitivity'] is None
    assert result['automated_blocking'] is False
    assert (result['detection'] is not None) == (status == 'OK')


def test_actual_txt_cli_redacts_text_and_reports_no_sensitivity(tmp_path):
    path = tmp_path/'inert.txt'
    path.write_text('Public: public@example.invalid; api_key=inert-secret-123', encoding='utf-8')
    result = subprocess.run([sys.executable, '-B', '-m', 'research.automatic_content', str(path)],
                            capture_output=True, text=True, check=True, timeout=15)
    assert not result.stderr and 'public@example.invalid' not in result.stdout
    assert 'inert-secret-123' not in result.stdout
    value = json.loads(result.stdout)
    assert value['extraction_complete'] and value['detection']['candidate_count'] == 2
    assert value['organizational_sensitivity'] is None and value['review_needed']
