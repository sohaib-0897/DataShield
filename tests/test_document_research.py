import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

import pytest

from research import documents as docs
from research.document_fixtures import TEXT, make_fixtures, write_docx, write_pdf


@pytest.mark.parametrize('suffix', ['txt', 'pdf', 'docx'])
def test_real_extractors_and_private_redacted_evidence(tmp_path, suffix):
    files = make_fixtures(tmp_path)
    path = tmp_path / f'report.{suffix}'
    extracted = docs.extract_document(path)
    assert extracted['status'] == 'OK'
    assert 'test@example.invalid' in extracted['text']
    evidence = docs.document_evidence(path)
    assert evidence['content_available']
    assert {e['type'] for e in evidence['pii_evidence']} == {'cnic_like', 'email_address'}
    serialized = json.dumps(evidence)
    assert 'test@example.invalid' not in serialized and '12345-1234567-1' not in serialized
    assert TEXT not in serialized and 'report.' not in serialized
    assert not evidence['automated_blocking']
    assert evidence['sensitivity_model_status'] == 'UNAVAILABLE_NO_LABELED_CORPUS'


@pytest.mark.parametrize('filename,status', [('encrypted.pdf', 'ENCRYPTED'), ('no_text.pdf', 'SCANNED_OR_NO_TEXT'),
                                            ('empty.txt', 'EMPTY'), ('unsupported.xlsx', 'UNSUPPORTED'),
                                            ('malformed.pdf', 'MALFORMED'), ('malformed.docx', 'MALFORMED'),
                                            ('malformed.txt', 'MALFORMED')])
def test_unavailable_outcomes_are_explicit(tmp_path, filename, status):
    make_fixtures(tmp_path)
    result = docs.document_evidence(tmp_path / filename)
    assert result['extraction_status'] == status
    assert result['pii_evidence'] == [] and not result['content_available']


def test_filename_hash_signals_survive_unavailable_content(tmp_path):
    path = tmp_path / 'Salary.xlsx'
    path.write_bytes(b'synthetic file')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    evidence = docs.document_evidence(path, filename_labels={'salary.xlsx': 'HIGH'}, known_hashes={digest: 'CRITICAL'})
    assert evidence['filename_label'] == 'HIGH' and evidence['hash_label'] == 'CRITICAL'
    assert evidence['sha256'] == digest and evidence['extraction_status'] == 'UNSUPPORTED'
    assert docs.document_evidence(path)['filename_label'] is None


def test_document_size_text_and_page_bounds(tmp_path):
    path = tmp_path / 'long.txt'
    path.write_text(TEXT * 5)
    assert docs.extract_document(path, max_bytes=2)['status'] == 'TOO_LARGE'
    result = docs.extract_document(path, max_chars=15)
    assert result['status'] == 'OK' and result['truncated'] and len(result['text']) == 15
    write_pdf(tmp_path / 'pages.pdf', pages=2)
    assert docs.extract_document(tmp_path / 'pages.pdf', max_pages=1)['status'] == 'LIMIT_EXCEEDED'
    write_docx(tmp_path / 'empty.docx', text='')
    assert docs.extract_document(tmp_path / 'empty.docx')['status'] == 'EMPTY'


@pytest.mark.parametrize('name,body,status', [('../escape.xml', b'<x/>', 'MALFORMED'),
                                              ('word/document.xml', b'<!DOCTYPE x><x/>', 'MALFORMED'),
                                              ('word/document.xml', b'x' * 100000, 'LIMIT_EXCEEDED')])
def test_unsafe_docx_xml_paths_and_expansion(tmp_path, name, body, status):
    path = tmp_path / 'unsafe.docx'
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, body)
    assert docs.extract_document(path)['status'] == status
    assert not (tmp_path.parent / 'escape.xml').exists()


def test_symlinks_unreadable_and_encrypted_container(tmp_path):
    path = tmp_path / 'real.txt'
    path.write_text(TEXT)
    link = tmp_path / 'link.txt'
    link.symlink_to(path)
    assert docs.document_evidence(link)['extraction_status'] == 'UNSAFE_PATH'
    assert docs.document_evidence(link)['sha256'] is None
    assert docs.extract_document(tmp_path / 'missing.txt')['status'] == 'UNREADABLE'
    ole = tmp_path / 'encrypted.docx'
    ole.write_bytes(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1')
    assert docs.extract_document(ole)['status'] == 'ENCRYPTED_OR_LEGACY_UNSUPPORTED'


def test_timeouts_and_changed_inputs_do_not_log_content(tmp_path, monkeypatch, capsys):
    path = tmp_path / 'private.txt'
    path.write_text(TEXT)
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired('fixture', 1)
    monkeypatch.setattr(docs.subprocess, 'run', timeout)
    assert docs.document_evidence(path)['extraction_status'] == 'TIMEOUT'
    def changed(*args, **kwargs):
        path.write_text('changed synthetic input')
        return subprocess.CompletedProcess([], 0, stdout=json.dumps(docs.private_result('OK', TEXT)).encode(), stderr=b'')
    monkeypatch.setattr(docs.subprocess, 'run', changed)
    evidence = docs.document_evidence(path)
    assert evidence['extraction_status'] == 'INPUT_CHANGED' and evidence['sha256'] is None
    assert evidence['pii_evidence'] == []
    assert capsys.readouterr().out == ''


def test_pii_evidence_bounds_and_negative_text():
    assert docs.pii_evidence('ordinary synthetic text') == []
    evidence = docs.pii_evidence(' '.join(['test@example.invalid'] * 25), max_spans=3)[0]
    assert evidence['count'] == 25 and len(evidence['spans']) == 3 and evidence['spans_truncated']
    with pytest.raises(ValueError):
        docs.extract_document(Path('any.txt'), max_bytes=0)
