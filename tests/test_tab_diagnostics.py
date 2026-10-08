"""Read-only DS3 audit and uncertainty guards, using inert data."""
import json

import numpy as np
import pytest

from research.tab_diagnostics import audit_documents, bootstrap, document_reason, matrix_statistics
from research.tab_prepare import digest
from research.cert_ingest import hash_file


def test_document_reasons_are_exclusive_and_handle_empty_reviewed_docs():
    for retained,reviewed,eligible,expected in [
        (False,0,0,'quarantined_unreviewed'),(False,1,2,'quarantined_reviewed'),
        (True,0,0,'unreviewed_nonquarantined'),(True,1,0,'reviewed_no_unanimous_spans'),(True,1,2,'used')]:
        assert document_reason({'retained':retained,'reviewed_sets':reviewed,'eligible_spans':eligible}) == expected


def test_document_bootstrap_preserves_cluster_dependence_and_is_repeatable():
    # Each of two documents has ten perfectly correlated successes/failures.
    rows = [{'document':d,'label':'PERSON'} for d in ('a','b') for _ in range(10)]
    pred = ['PERSON']*10+['ORG']*10
    strata = {'full':list(range(20)),'seen':list(range(10)),'unseen':list(range(10,20))}
    result = bootstrap(rows,pred,strata,replicates=200,seed=7)
    assert result == bootstrap(rows,pred,strata,replicates=200,seed=7)
    assert result['strata']['full']['micro_f1']['lower'] == 0
    assert result['strata']['full']['micro_f1']['upper'] == 1
    assert result['strata']['paired_seen_minus_unseen']['micro_f1']['lower'] == 1
    assert result['strata']['seen']['micro_f1']['valid_replicates'] < 200


def test_bootstrap_undefined_per_class_precision_is_not_invented():
    matrices = np.zeros((1,8,8),dtype=int);matrices[0,6,5] = 2
    result = matrix_statistics(matrices)
    assert np.isnan(result['precision'][0,6])
    assert result['recall'][0,6] == 0 and result['f1'][0,6] == 0
    assert np.isnan(result['recall'][0,5]) and np.isnan(result['f1'][0,5])
    assert result['macro_f1'][0] == 0


def test_source_documents_all_accounted_without_writing(tmp_path):
    entries = [];acquisition = []
    for split in ('train','dev','test'):
        doc = {'doc_id':split,'dataset_type':split,'text':'inert','quality_checked':[], 'annotations':{}}
        path = tmp_path/f'echr_{split}.json';path.write_text(json.dumps([doc]))
        acquisition.append({'file':path.name,**hash_file(path)})
        entries.append({'source_doc_sha256':digest(split),'original_record_sha256':digest(doc),
                        'official_split':split,'retained':True,'reviewed_sets':0,'eligible_spans':0,'group':split})
    path = tmp_path/'documents.json';path.write_text(json.dumps(entries))
    before = {p.name:p.read_bytes() for p in tmp_path.iterdir()}
    counts,ledger = audit_documents(tmp_path,tmp_path,{s:[] for s in ('train','validation','test')},{'acquisition':{'files':acquisition}})
    assert counts['exclusive_document_reasons'] == {'unreviewed_nonquarantined':3}
    assert len(ledger) == 3
    assert before == {p.name:p.read_bytes() for p in tmp_path.iterdir()}
    (tmp_path/'echr_test.json').write_text('[]')
    with pytest.raises(ValueError,match='changed'):audit_documents(tmp_path,tmp_path,{s:[] for s in ('train','validation','test')},{'acquisition':{'files':acquisition}})
