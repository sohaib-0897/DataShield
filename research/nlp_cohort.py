"""Disk-backed stage audit of the retained strict and separate known-user cohorts."""
from collections import Counter
import json
import sqlite3

from research.cert_ingest import local_path, hash_file
from research.stream_prepare import configure

NAMES=('train','validation','test')


def cohort(prepared, folder):
    db=sqlite3.connect(local_path(folder,prepared).as_uri()+'?mode=ro',uri=True)
    configure(db)
    fingerprint=hash_file(prepared)['sha256']
    db.execute('BEGIN')
    if (db.execute('PRAGMA application_id').fetchone()[0],db.execute('PRAGMA user_version').fetchone()[0]) != (1146307412,1):
        db.close();raise ValueError('Incompatible preparation')
    report=json.loads(db.execute("SELECT value FROM meta WHERE key='report'").fetchone()[0])
    if not report['complete']:
        db.close();raise ValueError('Incomplete preparation')
    # Only temporary tables are written; the prepared snapshot remains immutable.
    db.execute('''CREATE TEMP TABLE partitions(start TEXT,user TEXT,part INTEGER,label INTEGER,
      has_text INTEGER,seen_identity INTEGER DEFAULT 0,seen_duplicate INTEGER DEFAULT 0,PRIMARY KEY(start,user))''')
    hours=[r[0] for r in db.execute("SELECT DISTINCT start FROM windows WHERE json_extract(payload,'$.fully_observed')=1 AND json_extract(payload,'$.label') IN (0,1) ORDER BY start")]
    if len(hours)<3:
        db.close();raise ValueError('Need three eligible hours')
    val,test=hours[max(1,int(len(hours)*.6))],hours[min(len(hours)-1,max(max(1,int(len(hours)*.6))+1,int(len(hours)*.8)))]
    for start,user,payload,text in db.execute('SELECT start,user,payload,text FROM windows ORDER BY start,user'):
        w=json.loads(payload)
        if not w['fully_observed'] or w['label'] not in (0,1):continue
        if w['end']<=start or w['end']> (val if start<val else test if start<test else w['end']):
            db.close();raise ValueError('Unexpected overlap; hourly windows required')
        part=0 if start<val else 1 if start<test else 2
        db.execute('INSERT INTO partitions(start,user,part,label,has_text) VALUES (?,?,?,?,?)',(start,user,part,w['label'],int(bool(text))))
    db.execute('CREATE TEMP TABLE identity_first AS SELECT user,min(part) part FROM partitions GROUP BY user')
    db.execute('CREATE UNIQUE INDEX temp.identity_index ON identity_first(user)')
    db.execute('''CREATE TEMP TABLE bag_first AS SELECT b.hash,min(p.part) part FROM window_bags b
      JOIN partitions p USING(start,user) GROUP BY b.hash''')
    db.execute('CREATE UNIQUE INDEX temp.bag_index ON bag_first(hash)')
    db.execute('''UPDATE partitions SET seen_identity=EXISTS(SELECT 1 FROM identity_first f WHERE f.user=partitions.user AND f.part<partitions.part),
      seen_duplicate=EXISTS(SELECT 1 FROM window_bags b JOIN bag_first f USING(hash)
      WHERE b.start=partitions.start AND b.user=partitions.user AND f.part<partitions.part)''')
    audit={};strict={};known={}
    for part,name in enumerate(NAMES):
        stage={}
        for key,condition in [('eligible','1'),('nonempty_text','has_text'),('after_identity','has_text AND NOT seen_identity'),
                              ('strict_final','has_text AND NOT seen_identity AND NOT seen_duplicate'),
                              ('known_user_content_disjoint','has_text AND NOT seen_duplicate')]:
            counts=Counter({str(label):n for label,n in db.execute(f'SELECT label,count(*) FROM partitions WHERE part=? AND {condition} GROUP BY label',(part,))})
            stage[key]={'windows':sum(counts.values()),'class_counts':dict(counts)}
        stage['independent_rejection_flags']={key:db.execute(f'SELECT count(*) FROM partitions WHERE part=? AND {condition}',(part,)).fetchone()[0]
            for key,condition in [('missing_text','NOT has_text'),('seen_identity','seen_identity'),('past_duplicate_bag','seen_duplicate')]}
        stage['strict_removal_priority']={key:db.execute(f'SELECT count(*) FROM partitions WHERE part=? AND {condition}',(part,)).fetchone()[0]
            for key,condition in [('missing_text','NOT has_text'),('seen_identity','has_text AND seen_identity'),('past_duplicate_bag','has_text AND NOT seen_identity AND seen_duplicate')]}
        audit[name]=stage
        strict[name]=stage['strict_final'];known[name]=stage['known_user_content_disjoint']
    if hash_file(prepared)['sha256'] != fingerprint:
        db.close();raise ValueError('Prepared snapshot changed')
    return db, {'preparation':report,'prepared_sha256':fingerprint,
                'all_windows_by_coverage_and_class':[{'fully_observed':bool(full),'label':label,'windows':count} for full,label,count in
                    db.execute("SELECT json_extract(payload,'$.fully_observed'),json_extract(payload,'$.label'),count(*) FROM windows GROUP BY 1,2")],
                'validation_start':val,'test_start':test,'stages':audit,'original_strict':strict,'known_users_alternative':known,
                'controls':{'chronological':True,'event_windows_disjoint':True,'duplicates':'normalized per-event keyword bags, including reordered words; prior discarded rows retained',
                            'identity_strict':'exclude all users seen in any earlier partition','identity_alternative':'known population, continuing incidents permitted and disclosed'}}


def rows(db, part, max_text_bytes=512*1024**2):
    result=[];used=0
    for payload,text in db.execute('''SELECT w.payload,w.text FROM windows w JOIN partitions p USING(start,user)
      WHERE p.part=? AND p.has_text AND NOT p.seen_duplicate ORDER BY start,user''',(part,)):
        used+=len(text.encode())+len(payload.encode())
        if used>max_text_bytes:raise ValueError('Training cohort memory bound exceeded')
        w=json.loads(payload);w.pop('event_keys');w['text']=text;result.append(w)
    return result


def group_audit(splits):
    groups={name:{'users':{w['user'] for w in values},'incidents':{p['incident'] for w in values for p in w['label_provenance']},
                  'scenarios':{p['scenario'] for w in values for p in w['label_provenance']}} for name,values in splits.items()}
    return {f'{a}_{b}':{key:len(groups[a][key]&groups[b][key]) for key in ('users','incidents','scenarios')}
            for a,b in [('train','validation'),('train','test'),('validation','test')]}
