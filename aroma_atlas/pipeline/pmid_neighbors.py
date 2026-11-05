#!/usr/bin/env python3
"""Bounded Europe PMC bulk metadata lookup of actual cited MED/PMID identifiers.

Admissions are provisional until the normal final rescreen/anchors/audit/export.
No title-derived identifiers, credentials, inferred citations or reference imports.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import re
import sqlite3
import time
import uuid
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote

import requests

import atlas
import neighbors

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'pmid-neighbors-v1'
ENDPOINT = atlas.BASE + '/search'
MAX_REQUESTS = 100
MAX_BATCH_SIZE = 100
MAX_ATTEMPTS = 3
TERMINAL = {'accepted', 'rejected', 'date_rejected', 'invalid_record', 'identity_conflict', 'not_returned'}


def numeric_pmid(value):
    """Preserve exact IDs; do not infer PMIDs from titles, DOIs or free text."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return ''
    value = str(value)
    return value if re.fullmatch(r'[1-9][0-9]{0,8}', value) else ''


def init():
    atlas.init()
    c = atlas.connect()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS pmid_neighbor_checkpoint(
      pmid TEXT PRIMARY KEY,status TEXT,attempts INTEGER NOT NULL DEFAULT 0,updated TEXT,
      retry_after TEXT NOT NULL DEFAULT '',error TEXT NOT NULL DEFAULT '',paper TEXT NOT NULL DEFAULT '',
      last_request INTEGER,last_run TEXT);
    CREATE TABLE IF NOT EXISTS pmid_neighbor_origins(
      pmid TEXT,citing_paper TEXT,citing_doi TEXT,citing_pmid TEXT,target_source TEXT,
      target_id TEXT,raw_doi TEXT,supplied_title TEXT,citing_queries TEXT,first_run TEXT,
      PRIMARY KEY(pmid,citing_paper,target_source,target_id));
    CREATE TABLE IF NOT EXISTS pmid_neighbor_requests(
      id INTEGER PRIMARY KEY,run TEXT,started TEXT,finished TEXT,requested_pmids TEXT,
      request_url TEXT,request_params TEXT,response_url TEXT,http_status INTEGER,
      response_headers TEXT,response_body TEXT,outcome TEXT,error TEXT);
    CREATE TABLE IF NOT EXISTS pmid_neighbor_records(
      request INTEGER,ordinal INTEGER,returned_source TEXT,returned_id TEXT,raw TEXT,
      outcome TEXT,screening TEXT,paper TEXT,PRIMARY KEY(request,ordinal));
    CREATE TABLE IF NOT EXISTS pmid_neighbor_runs(
      id TEXT PRIMARY KEY,started TEXT,finished TEXT,stopped TEXT,cooldown_until TEXT,report TEXT);
    CREATE TABLE IF NOT EXISTS pmid_neighbor_canonical_archive(
      id INTEGER PRIMARY KEY,paper TEXT,archived_at TEXT,run TEXT,request INTEGER,ordinal INTEGER,
      reason TEXT,canonical_row TEXT,raw TEXT,refs_row TEXT,fingerprint TEXT);
    CREATE TRIGGER IF NOT EXISTS pmid_neighbor_archive_no_update
      BEFORE UPDATE ON pmid_neighbor_canonical_archive BEGIN
      SELECT RAISE(ABORT,'canonical metadata archive is immutable'); END;
    CREATE TRIGGER IF NOT EXISTS pmid_neighbor_archive_no_delete
      BEFORE DELETE ON pmid_neighbor_canonical_archive BEGIN
      SELECT RAISE(ABORT,'canonical metadata archive is immutable'); END;
    CREATE TABLE IF NOT EXISTS pmid_neighbor_enrichments(
      id INTEGER PRIMARY KEY,run TEXT,request INTEGER,ordinal INTEGER,pmid TEXT,paper TEXT,
      outcome TEXT,screening TEXT,changes TEXT,archive INTEGER,updated TEXT);
    ''')
    c.commit()
    c.close()


def freeze_context():
    """Hash once, before the first write; use one frozen review map throughout."""
    code = {name: neighbors.file_hash(Path(__file__).with_name(name))
            for name in ['pmid_neighbors.py', 'atlas.py', 'neighbors.py', 'supplement.py']}
    allowlists = {str(path): neighbors.file_hash(path) for name, path in vars(atlas).items()
                  if name.endswith('ALLOWLIST') and isinstance(path, Path) and path.exists()}
    review_files = {str(path): neighbors.file_hash(path) for path in atlas.review_paths() if path.exists()}
    review = json.loads(json.dumps(atlas.review_exclusions()))
    return {'frozen_at': atlas.now(), 'hashes': code, 'allowlist_hashes': allowlists,
            'review_hashes': review_files, 'review_exclusions': review,
            'review_decision_hash': hashlib.sha256(json.dumps(review, sort_keys=True).encode()).hexdigest()}


def public_context(context):
    return {k: v for k, v in context.items() if k != 'review_exclusions'}


def write_report(report, requested_path):
    """Never replace a previously saved report, including a legacy live-run file."""
    if requested_path is None:
        return
    path = Path(requested_path)
    if path.exists():
        path = path.with_name(path.stem+'_'+report['run']+path.suffix)
    report['report_file'] = str(path)
    with path.open('x') as handle:
        handle.write(json.dumps(report, indent=2)+'\n')


def select_candidates(c, limit=2000, min_citers=2, at=None):
    at = at or atlas.now()
    known = {numeric_pmid(r[0]) for r in c.execute('SELECT pmid FROM papers WHERE pmid!=""')}
    known.update(numeric_pmid(r[0]) for r in c.execute("SELECT source_id FROM papers WHERE source='MED'"))
    known.update(numeric_pmid(r[0]) for r in c.execute('''SELECT a.source_id FROM source_alias a
        JOIN papers p ON p.id=a.paper WHERE a.source IN ('MED','PMID')'''))
    tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    states = {}
    if 'pmid_neighbor_checkpoint' in tables:
        states = {r[0]: r[1:] for r in c.execute(
            'SELECT pmid,status,attempts,retry_after FROM pmid_neighbor_checkpoint')}
    query = '''SELECT r.paper,p.doi,p.pmid,p.tracks,r.target_source,r.target_id,r.doi,r.title
               FROM raw_refs r JOIN papers p ON p.id=r.paper
               WHERE p.accepted=1 AND r.target_source IN ('MED','PMID')
               ORDER BY r.paper,r.target_source,r.target_id'''
    entries = {}
    for pid, _, _, tracks, _, target, _, title in c.execute(query):
        pmid = numeric_pmid(target)
        if not pmid or pmid in known or not neighbors.core_tracks(tracks):
            continue
        state = states.get(pmid)
        if state and (state[0] in TERMINAL or state[1] >= MAX_ATTEMPTS or state[2] > at):
            continue
        entry = entries.setdefault(pmid, {'pmid': pmid, 'citers': set(), 'title_signal': False, 'origins': []})
        entry['citers'].add(pid)
        if not entry['title_signal']:
            entry['title_signal'] = neighbors.title_signal(title)
    chosen = [e for e in entries.values() if e['title_signal'] or len(e['citers']) >= min_citers]
    chosen.sort(key=lambda e: (-int(e['title_signal']), -len(e['citers']), int(e['pmid'])))
    chosen = chosen[:limit]
    selected = {e['pmid']: e for e in chosen}
    for pid, doi, citing_pmid, tracks, source, target, raw_doi, title in c.execute(query):
        pmid = numeric_pmid(target)
        if pmid in selected and neighbors.core_tracks(tracks):
            selected[pmid]['origins'].append({'citing_paper': pid, 'citing_doi': doi,
                'citing_pmid': citing_pmid, 'target_source': source, 'target_id': target,
                'raw_doi': raw_doi, 'supplied_title': title or ''})
    for entry in chosen:
        entry['citing_papers'] = len(entry.pop('citers'))
        for origin in entry['origins']:
            origin['citing_queries'] = [r[0] for r in c.execute(
                'SELECT query FROM provenance WHERE paper=? ORDER BY query', (origin['citing_paper'],))]
    return chosen


def query_params(pmids):
    if not 1 <= len(pmids) <= MAX_BATCH_SIZE or len(set(pmids)) != len(pmids) or not all(numeric_pmid(p) == p for p in pmids):
        raise ValueError('batch requires 1..100 distinct exact numeric PMID strings')
    return {'query': '('+' OR '.join('EXT_ID:'+p for p in pmids)+') AND SRC:MED AND FIRST_PDATE:[1800-01-01 TO '+atlas.CUTOFF+']',
            'format': 'json', 'resultType': 'core', 'pageSize': len(pmids), 'synonym': 'false'}


class StopHarvest(RuntimeError):
    pass


class Client:
    def __init__(self, max_requests=20, interval=1., max_seconds=600):
        if not 0 <= max_requests <= MAX_REQUESTS:
            raise ValueError('max_requests must be 0..100')
        if not math.isfinite(interval) or interval < 1:
            raise ValueError('interval must be at least one second')
        if not 1 <= max_seconds <= 3600:
            raise ValueError('max_seconds must be 1..3600')
        self.maximum, self.interval, self.max_seconds = max_requests, interval, max_seconds
        self.count, self.last, self.started = 0, 0, time.monotonic()
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'AromaResearchAtlas/1.0 (public cited PMID metadata research)'

    def available(self):
        return self.count < self.maximum and time.monotonic()-self.started < self.max_seconds

    def get(self, pmids):
        delay = max(0, self.interval-(time.monotonic()-self.last))
        if not self.available() or delay > 60 or time.monotonic()-self.started+delay >= self.max_seconds:
            raise StopHarvest('request or elapsed-time budget reached')
        params = query_params(pmids)
        time.sleep(delay)
        self.last = time.monotonic()
        self.count += 1
        return self.session.get(ENDPOINT, params=params, timeout=(15, 45), allow_redirects=False)


def remember_origins(candidates, run_id):
    c = atlas.connect()
    for candidate in candidates:
        pmid = candidate['pmid']
        c.execute('''INSERT OR IGNORE INTO pmid_neighbor_checkpoint(pmid,status,updated,last_run)
                     VALUES(?,'pending',?,?)''', (pmid, atlas.now(), run_id))
        for o in candidate['origins']:
            c.execute('INSERT OR IGNORE INTO pmid_neighbor_origins VALUES(?,?,?,?,?,?,?,?,?,?)',
                      (pmid, o['citing_paper'], o['citing_doi'], o['citing_pmid'], o['target_source'],
                       o['target_id'], o['raw_doi'], o['supplied_title'], json.dumps(o['citing_queries']), run_id))
    c.commit()
    c.close()


def begin_request(pmids, run_id):
    params = query_params(pmids)
    c = atlas.connect()
    url = requests.Request('GET', ENDPOINT, params=params).prepare().url
    cur = c.execute('''INSERT INTO pmid_neighbor_requests
        (run,started,requested_pmids,request_url,request_params,outcome) VALUES(?,?,?,?,?,'in_progress')''',
        (run_id, atlas.now(), json.dumps(pmids), url, json.dumps(params)))
    request_id = cur.lastrowid
    for pmid in pmids:
        c.execute('''UPDATE pmid_neighbor_checkpoint SET status='in_progress',attempts=attempts+1,
            updated=?,last_request=?,last_run=? WHERE pmid=?''', (atlas.now(), request_id, run_id, pmid))
    c.commit()
    c.close()
    return request_id


def checkpoint(pmid, status, error='', retry_after='', paper=''):
    c = atlas.connect()
    c.execute('''UPDATE pmid_neighbor_checkpoint SET status=?,updated=?,error=?,retry_after=?,paper=?
                 WHERE pmid=?''', (status, atlas.now(), error, retry_after, paper, pmid))
    c.commit()
    c.close()


def finish_request(request_id, outcome, error='', response=None):
    c = atlas.connect()
    if response is not None:
        c.execute('''UPDATE pmid_neighbor_requests SET response_url=?,http_status=?,response_headers=?,
            response_body=? WHERE id=?''', (response.url, response.status_code,
                json.dumps(dict(response.headers)), response.text, request_id))
    c.execute('UPDATE pmid_neighbor_requests SET finished=?,outcome=?,error=? WHERE id=?',
              (atlas.now(), outcome, error, request_id))
    c.commit()
    c.close()


def response_rows(response, pmids, request_id, persist=True):
    """Validate the entire identity envelope before ingesting any returned record."""
    payload = response.json()
    if not isinstance(payload, dict) or payload.get('errCode'):
        raise ValueError('missing successful Europe PMC result envelope')
    result_list = payload.get('resultList')
    rows = result_list.get('result') if isinstance(result_list, dict) else None
    if not isinstance(rows, list):
        raise ValueError('missing Europe PMC result rows')
    if persist:
        c = atlas.connect()
        for ordinal, row in enumerate(rows):
            record = row if isinstance(row, dict) else {}
            c.execute('INSERT OR IGNORE INTO pmid_neighbor_records VALUES(?,?,?,?,?,?,?,?)',
                      (request_id, ordinal, str(record.get('source', '')), str(record.get('id', '')),
                       json.dumps(row), 'unvalidated', '{}', ''))
        c.commit()
        c.close()
    count = payload.get('hitCount')
    if isinstance(count, bool) or not isinstance(count, int) or count != len(rows) or len(rows) > len(pmids):
        raise ValueError('incomplete or inconsistent batch hitCount; requested coverage remains unknown')
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('malformed Europe PMC record')
        pmid = numeric_pmid(row.get('id'))
        if row.get('source') != 'MED' or pmid not in pmids:
            raise ValueError('returned source/ID is outside the exact requested MED batch')
        if pmid in seen or (row.get('pmid') not in (None, '') and numeric_pmid(row['pmid']) != pmid):
            raise ValueError('duplicate or conflicting returned PMID identity')
        seen.add(pmid)
    return rows


def date_eligibility(row):
    first = row.get('firstPublicationDate')
    if isinstance(first, str):
        try:
            when = dt.date.fromisoformat(first)
            return '1800-01-01' <= when.isoformat() <= atlas.CUTOFF, {'firstPublicationDate': first, 'basis': 'native firstPublicationDate'}
        except ValueError:
            pass
    year = str(row.get('pubYear') or '')
    eligible = bool(re.fullmatch(r'\d{4}', year) and 1800 <= int(year) < int(atlas.CUTOFF[:4]))
    return eligible, {'firstPublicationDate': first, 'pubYear': year,
                      'basis': 'known earlier publication year' if eligible else 'missing, invalid or non-past date evidence'}


def screen(row):
    """Use the native classifier and publication-type gates without weakening scope."""
    for key in ['title', 'abstractText', 'doi', 'authorString', 'pmcid']:
        if key in row and row[key] is not None and not isinstance(row[key], str):
            raise ValueError('malformed Europe PMC '+key)
    types = row.get('pubTypeList', {})
    if not isinstance(types, dict) or not isinstance(types.get('pubType', []), list) or not all(isinstance(t, str) for t in types.get('pubType', [])):
        raise ValueError('malformed publication types')
    ji = row.get('journalInfo') or {}
    if not isinstance(ji, dict) or not isinstance(ji.get('journal') or {}, dict):
        raise ValueError('malformed journal metadata')
    journal_title = (ji.get('journal') or {}).get('title') or row.get('journalTitle', '')
    if journal_title is not None and not isinstance(journal_title, str):
        raise ValueError('malformed journal title')
    cited = row.get('citedByCount', 0)
    if cited is not None and (isinstance(cited, bool) or not re.fullmatch(r'\d+', str(cited))):
        raise ValueError('malformed citation count')
    year = row.get('pubYear') or ''
    if year and not re.fullmatch(r'\d{4}', str(year)):
        raise ValueError('malformed publication year')
    ok, category, tracks, evidence = atlas.classify(atlas.clean(row.get('title')), atlas.clean(row.get('abstractText')))
    types_text = ' '.join(types.get('pubType', [])).lower()
    excluded_type = any(t in types_text for t in ['patent', 'book review', 'retract', 'erratum'])
    if excluded_type:
        ok = False
        evidence.append('excluded publication type')
    eligible, date_evidence = date_eligibility(row)
    return {'accepted_metadata': bool(ok and eligible), 'scope_accepted': bool(ok),
            'date_eligible': eligible, 'category': category, 'tracks': tracks,
            'excluded_publication_type': excluded_type,
            'evidence': evidence, 'date_evidence': date_evidence,
            'classifier': 'atlas.classify plus native atlas.ingest pubType gates', 'cutoff': atlas.CUTOFF}


def exact_identity(c, pmid, doi):
    dangling = c.execute('''SELECT 1 FROM source_alias a LEFT JOIN papers p ON p.id=a.paper
        WHERE a.source IN ('MED','PMID') AND a.source_id=? AND p.id IS NULL''', (pmid,)).fetchone()
    if dangling:
        raise ValueError('dangling exact PMID alias; final identity audit required')
    identities = c.execute('''SELECT id,doi FROM papers WHERE pmid=? OR (source='MED' AND source_id=?) OR id=?
        UNION SELECT p.id,p.doi FROM source_alias a JOIN papers p ON p.id=a.paper
        WHERE a.source IN ('MED','PMID') AND a.source_id=?''', (pmid, pmid, 'pmid:'+pmid, pmid)).fetchall()
    ids = {p[0] for p in identities}
    if len(ids) > 1:
        raise ValueError('multiple existing exact PMID identities; final identity audit required')
    if identities:
        if doi and identities[0][1] and neighbors.canonical_doi(identities[0][1]) != doi:
            alias = c.execute("SELECT paper FROM source_alias WHERE source='DOI' AND source_id=?", (doi,)).fetchone()
            if not alias or alias[0] != identities[0][0]:
                raise ValueError('returned DOI conflicts with existing exact PMID identity without proved DOI alias')
        return identities[0][0]
    if doi:
        existing = c.execute('''SELECT id FROM papers WHERE doi=?
            ORDER BY accepted DESC,length(abstract) DESC,id LIMIT 1''', (doi,)).fetchone()
        if existing:
            return existing[0]
        alias = c.execute('''SELECT p.id FROM source_alias a JOIN papers p ON p.id=a.paper
                             WHERE a.source='DOI' AND a.source_id=?''', (doi,)).fetchone()
        if alias:
            return alias[0]
    return ''


def paper_row(c, paper):
    cursor = c.execute('SELECT * FROM papers WHERE id=?', (paper,))
    values = cursor.fetchone()
    return dict(zip([d[0] for d in cursor.description], values)) if values else None


def reviewed_screening(screening, paper, pmid, doi, context, extra_doi=''):
    result = {**screening, 'evidence': list(screening['evidence'])}
    matches = {key: context['review_exclusions'][key] for key in [paper, 'pmid:'+pmid, 'doi:'+doi, 'doi:'+extra_doi]
               if key in context['review_exclusions']}
    if matches:
        result['accepted_metadata'] = False
        result['tracks'] = []
        result['review_exclusions'] = matches
        for review in matches.values():
            result['evidence'].append('AI diagnostic review exclusion ('+review['verdict']+'): '+review['reason'])
    return result


def archive_canonical(c, old, run_id, request_id, ordinal, reason):
    refs = c.execute('SELECT * FROM refs WHERE paper=?', (old['id'],)).fetchone()
    serialized = json.dumps(old, sort_keys=True, ensure_ascii=False)
    fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
    return c.execute('''INSERT INTO pmid_neighbor_canonical_archive
        (paper,archived_at,run,request,ordinal,reason,canonical_row,raw,refs_row,fingerprint)
        VALUES(?,?,?,?,?,?,?,?,?,?)''', (old['id'], atlas.now(), run_id, request_id, ordinal,
        reason, serialized, old['raw'], json.dumps(refs) if refs else '', fingerprint)).lastrowid


def native_values(row, paper, screening):
    """Actual native MED fields and its unmerged raw response, with stable atlas ID."""
    pmid = numeric_pmid(row['id'])
    ji = row.get('journalInfo') or {}
    journal = (ji.get('journal') or {}).get('title') or row.get('journalTitle', '')
    return {'id': paper, 'doi': neighbors.canonical_doi(row.get('doi')),
            'title': atlas.clean(row.get('title')), 'year': int(row.get('pubYear') or row['firstPublicationDate'][:4]),
            'authors': row.get('authorString', ''), 'journal': journal,
            'abstract': atlas.clean(row.get('abstractText')), 'citations': row.get('citedByCount', 0),
            'pmid': pmid, 'pmcid': row.get('pmcid', ''), 'source': 'MED', 'source_id': pmid,
            'category': screening['category'], 'tracks': json.dumps(screening['tracks']),
            'evidence': json.dumps(screening['evidence']), 'accepted': int(screening['accepted_metadata']),
            'raw': json.dumps(row, separators=(',', ':'))}


def enrich_canonical(c, old, row, screening, context, run_id, request_id, ordinal, existing=True):
    pmid, paper = numeric_pmid(row['id']), old['id']
    screening = reviewed_screening(screening, paper, pmid, neighbors.canonical_doi(old['doi']), context,
                                  neighbors.canonical_doi(row.get('doi')))
    new_ab = atlas.clean(row.get('abstractText'))
    richer = bool(new_ab and len(new_ab) > len(atlas.clean(old['abstract'])))
    promote = bool(existing and ((old['source'] != 'MED' and richer) or screening['excluded_publication_type']))
    changes = {'promoted': False, 'scope_changed': False, 'activated_existing': False,
               'removed_existing': False, 'pmid_filled': False, 'refs_reset': False,
               'archive': None, 'canonical_accepted': bool(old['accepted'])}
    new = native_values(row, paper, screening) if promote else dict(old)
    # Existing exact DOI remains available even when native MED lists a different,
    # previously proved alias. Never merge old/new provider payloads into a raw record.
    if promote and old['doi']:
        new['doi'] = old['doi']
    if not promote and not old['pmid']:
        new['pmid'] = pmid
    if not promote and screening.get('review_exclusions'):
        new['accepted'] = 0
        new['tracks'] = '[]'
        evidence = json.loads(old['evidence'] or '[]')
        new['evidence'] = json.dumps(list(dict.fromkeys(evidence+screening['evidence'])))
    if new != old:
        changes['archive'] = archive_canonical(c, old, run_id, request_id, ordinal,
            'native MED primary promotion' if promote else 'exact PMID fill or frozen review exclusion')
        if old['source'] and old['source_id']:
            c.execute('INSERT OR IGNORE INTO source_alias VALUES(?,?,?)', (old['source'], old['source_id'], paper))
        fields = [key for key in new if key != 'id']
        c.execute('UPDATE papers SET '+','.join(key+'=?' for key in fields)+' WHERE id=?',
                  tuple(new[key] for key in fields)+(paper,))
        changes['promoted'] = promote
        changes['pmid_filled'] = not bool(old['pmid']) and bool(new['pmid'])
        changes['scope_changed'] = bool(old['accepted']) != bool(new['accepted'])
        changes['activated_existing'] = not bool(old['accepted']) and bool(new['accepted'])
        changes['removed_existing'] = bool(old['accepted']) and not bool(new['accepted'])
        if promote and old['source'] != 'MED':
            refs = c.execute('SELECT error FROM refs WHERE paper=?', (paper,)).fetchone()
            if refs and str(refs[0] or '').startswith(('Crossref ', 'OpenAlex ', 'Semantic Scholar ')):
                c.execute('DELETE FROM refs WHERE paper=?', (paper,))
                changes['refs_reset'] = True
    changes['canonical_accepted'] = bool(new['accepted'])
    return screening, changes


def enrichment_event(c, run_id, request_id, ordinal, pmid, paper, outcome, screening, changes):
    c.execute('''INSERT INTO pmid_neighbor_enrichments
        (run,request,ordinal,pmid,paper,outcome,screening,changes,archive,updated) VALUES(?,?,?,?,?,?,?,?,?,?)''',
        (run_id, request_id, ordinal, pmid, paper, outcome, json.dumps(screening), json.dumps(changes),
         changes.get('archive'), atlas.now()))


def ingest_record(row, candidate, request_id, screening, context=None, run_id='', ordinal=None, allow_new=True):
    context = context or freeze_context()
    pmid = candidate['pmid']
    doi = neighbors.canonical_doi(row.get('doi'))
    if row.get('doi') and not doi:
        raise ValueError('malformed DOI cannot establish exact identity')
    c = atlas.connect()
    try:
        paper = exact_identity(c, pmid, doi)
    finally:
        c.close()
    reused = bool(paper)
    query = VERSION+':'+pmid
    if not paper:
        if not allow_new:
            raise ValueError('cached enrichment requires a currently proved existing exact identity')
        native = dict(row)
        native['id'], native['source'], native['pmid'], native['doi'] = pmid, 'MED', pmid, doi
        native['pubYear'] = str(row.get('pubYear') or row.get('firstPublicationDate', '')[:4])
        atlas.ingest([native], query)
        paper = 'pmid:'+pmid
    c = atlas.connect()
    old = paper_row(c, paper)
    screening, changes = enrich_canonical(c, old, row, screening, context, run_id, request_id, ordinal, reused)
    for source in ['MED', 'PMID']:
        old = c.execute('SELECT paper FROM source_alias WHERE source=? AND source_id=?', (source, pmid)).fetchone()
        if old and old[0] != paper:
            c.close()
            raise ValueError('existing source alias conflicts with exact metadata identity')
        c.execute('INSERT OR IGNORE INTO source_alias VALUES(?,?,?)', (source, pmid, paper))
    c.execute('INSERT OR IGNORE INTO provenance VALUES(?,?)', (paper, query))
    for origin in candidate['origins']:
        c.execute('INSERT OR IGNORE INTO provenance VALUES(?,?)',
                  (paper, 'pmid-neighbor:'+origin['citing_paper']+'|pmid:'+pmid))
    accepted = bool(c.execute('SELECT accepted FROM papers WHERE id=?', (paper,)).fetchone()[0])
    enrichment_event(c, run_id, request_id, ordinal, pmid, paper,
                     'promoted' if changes['promoted'] else 'retained', screening, changes)
    c.commit()
    c.close()
    return paper, reused, bool(not reused and accepted), screening, changes


def finish_record(request_id, ordinal, outcome, screening, paper=''):
    c = atlas.connect()
    c.execute('''UPDATE pmid_neighbor_records SET outcome=?,screening=?,paper=?
        WHERE request=? AND ordinal=?''', (outcome, json.dumps(screening), paper, request_id, ordinal))
    c.commit()
    c.close()


def cached_records(c, limit=10000):
    return c.execute('''SELECT r.request,r.ordinal,r.raw,r.outcome,q.requested_pmids,q.response_body
        FROM pmid_neighbor_records r JOIN pmid_neighbor_requests q ON q.id=r.request
        WHERE q.http_status=200 AND q.outcome='complete'
        AND r.outcome IN ('accepted','rejected','identity_conflict')
        ORDER BY r.request,r.ordinal LIMIT ?''', (limit,)).fetchall()


def enrich_cached(max_records=10000, report_path=None):
    """Re-evaluate verified cached MED metadata without altering original evidence."""
    if not 0 <= max_records <= 10000 or atlas.CUTOFF != '2026-10-26':
        raise ValueError('cached enrichment requires 0..10000 records and cutoff 2026-10-26')
    context = freeze_context()
    init()
    run_id, started = str(uuid.uuid4()), atlas.now()
    c = atlas.connect()
    records = cached_records(c, max_records)
    c.execute('INSERT INTO pmid_neighbor_runs VALUES(?,?,NULL,?,?,?)',
              (run_id, started, '', '', json.dumps({'mode': 'enrich-cached', **public_context(context)})))
    c.commit()
    c.close()
    totals = {'selected_cached_records': len(records), 'validated_cached_records': 0,
              'promoted': 0, 'scope_changed': 0, 'activated_existing': 0, 'removed_existing': 0,
              'pmid_filled': 0, 'refs_reset': 0, 'retained': 0, 'held_conflicts': 0,
              'invalid_cache_or_record': 0, 'date_rejected': 0,
              'new_candidates': 0, 'accepted_new_provisional': 0}
    proofs = {}
    for request_id, ordinal, raw, previous_outcome, requested, body in records:
        paper, screening, changes, outcome, pmid = '', {}, {}, 'invalid_cache', ''
        try:
            row = json.loads(raw)
            pmid = numeric_pmid(row.get('id')) if isinstance(row, dict) else ''
            if request_id not in proofs:
                try:
                    response = SimpleNamespace(json=lambda: json.loads(body))
                    proofs[request_id] = response_rows(response, json.loads(requested), request_id, persist=False)
                except (ValueError, TypeError, AttributeError) as exc:
                    proofs[request_id] = str(exc)
            proof = proofs[request_id]
            if isinstance(proof, str) or ordinal >= len(proof) or proof[ordinal] != row:
                raise ValueError('cached source row does not match its complete original batch proof')
            screening = screen(row)
            totals['validated_cached_records'] += 1
            if not screening['date_eligible']:
                outcome = 'date_rejected'
                totals['date_rejected'] += 1
            else:
                c = atlas.connect()
                origins = [{'citing_paper': r[0]} for r in c.execute(
                    'SELECT citing_paper FROM pmid_neighbor_origins WHERE pmid=? ORDER BY citing_paper', (pmid,))]
                alias = c.execute("SELECT paper FROM source_alias WHERE source='DOI' AND source_id=?",
                                  (neighbors.canonical_doi(row.get('doi')),)).fetchone()
                c.close()
                if previous_outcome == 'identity_conflict' and not alias:
                    raise ValueError('previous identity conflict remains held without a proved DOI alias')
                paper, reused, _, screening, changes = ingest_record(
                    row, {'pmid': pmid, 'origins': origins}, request_id, screening,
                    context, run_id, ordinal, allow_new=False)
                for key in ['promoted', 'scope_changed', 'activated_existing', 'removed_existing', 'pmid_filled', 'refs_reset']:
                    totals[key] += int(changes[key])
                totals['retained'] += int(not changes['promoted'])
                outcome = 'promoted' if changes['promoted'] else 'retained'
                checkpoint(pmid, 'accepted' if screening['accepted_metadata'] else 'rejected', paper=paper)
                # ingest_record already appended a new immutable-source event; it
                # never updates the old request/record/run whose metadata is reused.
                continue
        except (ValueError, TypeError, AttributeError, KeyError) as exc:
            screening = {**screening, 'error': str(exc), 'previous_record_outcome': previous_outcome}
            if previous_outcome == 'identity_conflict' or 'identity' in str(exc) or 'alias' in str(exc):
                outcome = 'held_conflict'
                totals['held_conflicts'] += 1
            else:
                totals['invalid_cache_or_record'] += 1
        c = atlas.connect()
        enrichment_event(c, run_id, request_id, ordinal, pmid, paper, outcome, screening, changes)
        c.commit()
        c.close()
    atlas.resolve()
    report = {'version': VERSION, 'mode': 'enrich-cached', 'run': run_id, 'started': started,
              'finished': atlas.now(), 'cutoff': atlas.CUTOFF, 'requests_this_run': 0,
              'max_cached_records': max_records, 'totals': totals,
              'stopped': 'bounded cached MED snapshot processed', 'cooldown_until': '',
              'requires_before_export': ['stop all writers', 'atlas.rescreen', 'supplement.anchors', 'resolve/export/audit'],
              'limits': ['No network requests or new publication identities in cached enrichment.',
                         'Original requests, record screening, run reports and raw responses remain unchanged.',
                         'Current-gate changes are separate enrichment events with immutable prior canonical archives.'],
              **public_context(context)}
    write_report(report, report_path)
    c = atlas.connect()
    c.execute('UPDATE pmid_neighbor_runs SET finished=?,stopped=?,cooldown_until=?,report=? WHERE id=?',
              (report['finished'], report['stopped'], '', json.dumps(report), run_id))
    c.commit()
    c.close()
    return report


def run(client=None, batch_size=100, max_candidates=None, min_citers=2, report_path=None):
    client = client or Client()
    max_candidates = client.maximum*batch_size if max_candidates is None else max_candidates
    if not 1 <= batch_size <= MAX_BATCH_SIZE or not 0 <= max_candidates <= MAX_REQUESTS*MAX_BATCH_SIZE or min_citers < 2:
        raise ValueError('batch_size must be 1..100, max_candidates 0..10000 and min_citers at least 2')
    if atlas.CUTOFF != '2026-10-26':
        raise ValueError('pmid-neighbors-v1 is frozen to 2026-10-26')
    context = freeze_context()
    init()
    run_id, started = str(uuid.uuid4()), atlas.now()
    c = atlas.connect()
    cooldown = c.execute('SELECT max(cooldown_until) FROM pmid_neighbor_runs').fetchone()[0] or ''
    candidates = select_candidates(c, max_candidates, min_citers)
    c.execute('INSERT INTO pmid_neighbor_runs VALUES(?,?,NULL,?,?,?)',
              (run_id, started, '', '', json.dumps({'mode': 'network', **public_context(context)})))
    c.commit()
    c.close()
    totals = {'requested_id_occurrences': 0, 'returned_rows': 0, 'retrieved_exact': 0, 'accepted_metadata': 0,
              'rejected_metadata': 0, 'accepted_new_provisional': 0, 'new_candidates': 0,
              'reused_identities': 0, 'date_rejected': 0, 'invalid_records': 0, 'not_returned': 0,
              'invalid_batches': 0, 'promoted': 0, 'scope_changed': 0, 'activated_existing': 0,
              'removed_existing': 0, 'pmid_filled': 0, 'refs_reset': 0}
    stopped, ratefails, serverfails = '', 0, 0
    if cooldown > atlas.now():
        stopped = 'stored Europe PMC provider cooldown remains active'
    for offset in range(0, len(candidates), batch_size):
        if stopped:
            break
        batch = candidates[offset:offset+batch_size]
        pmids = [b['pmid'] for b in batch]
        by_id = {b['pmid']: b for b in batch}
        remember_origins(batch, run_id)
        while not stopped:
            c = atlas.connect()
            attempts = max(c.execute('SELECT attempts FROM pmid_neighbor_checkpoint WHERE pmid=?', (p,)).fetchone()[0] for p in pmids)
            c.close()
            if attempts >= MAX_ATTEMPTS:
                break
            if not client.available():
                stopped = 'request or elapsed-time budget reached'
                break
            request_id = begin_request(pmids, run_id)
            response = None
            try:
                totals['requested_id_occurrences'] += len(pmids)
                response = client.get(pmids)
                finish_request(request_id, 'received', response=response)
                status = response.status_code
                if status in {429, 500, 502, 503, 504}:
                    ratefails += int(status == 429)
                    serverfails += int(status != 429)
                    persistent = ratefails >= 2 or serverfails >= 3
                    delay = max(2, neighbors.retry_seconds(response.headers))
                    if persistent:
                        delay = max(3600, delay)
                    cooldown = max(cooldown, neighbors.after(delay))
                    finish_request(request_id, 'retryable', 'HTTP '+str(status))
                    for pmid in pmids:
                        checkpoint(pmid, 'retryable', 'HTTP '+str(status), cooldown)
                    if persistent:
                        stopped = 'persistent Europe PMC throttling or server failures'
                    elif delay > 60 or not client.available() or attempts+1 >= MAX_ATTEMPTS:
                        stopped = 'Europe PMC provider cooldown; resume later'
                    else:
                        time.sleep(delay)
                        cooldown = ''
                    continue
                if status != 200:
                    cooldown = neighbors.after(3600)
                    finish_request(request_id, 'retryable', 'unexpected HTTP '+str(status))
                    for pmid in pmids:
                        checkpoint(pmid, 'retryable', 'unexpected HTTP '+str(status), cooldown)
                    stopped = 'unexpected Europe PMC HTTP response; resume later'
                    break
                try:
                    rows = response_rows(response, pmids, request_id)
                except (ValueError, TypeError, AttributeError) as exc:
                    totals['invalid_batches'] += 1
                    finish_request(request_id, 'invalid_batch', str(exc))
                    for pmid in pmids:
                        checkpoint(pmid, 'retryable', str(exc), neighbors.after(3600))
                    stopped = 'invalid batch identity or coverage envelope; inspect audit before continuing'
                    break
                totals['returned_rows'] += len(rows)
                returned = set()
                for ordinal, row in enumerate(rows):
                    pmid = numeric_pmid(row['id'])
                    returned.add(pmid)
                    totals['retrieved_exact'] += 1
                    try:
                        screening = screen(row)
                    except (ValueError, TypeError, AttributeError) as exc:
                        totals['invalid_records'] += 1
                        finish_record(request_id, ordinal, 'invalid_record', {'error': str(exc)})
                        checkpoint(pmid, 'invalid_record', str(exc))
                        continue
                    if not screening['date_eligible']:
                        totals['date_rejected'] += 1
                        finish_record(request_id, ordinal, 'date_rejected', screening)
                        checkpoint(pmid, 'date_rejected', 'outside cutoff or date evidence unavailable')
                        continue
                    try:
                        paper, reused, accepted_new, screening, changes = ingest_record(
                            row, by_id[pmid], request_id, screening, context, run_id, ordinal)
                    except ValueError as exc:
                        totals['invalid_records'] += 1
                        finish_record(request_id, ordinal, 'identity_conflict', {**screening, 'error': str(exc)})
                        checkpoint(pmid, 'identity_conflict', str(exc))
                        continue
                    totals['reused_identities'] += int(reused)
                    totals['new_candidates'] += int(not reused)
                    totals['accepted_new_provisional'] += int(accepted_new)
                    if reused:
                        for key in ['promoted', 'scope_changed', 'activated_existing', 'removed_existing', 'pmid_filled', 'refs_reset']:
                            totals[key] += int(changes[key])
                    totals['accepted_metadata' if screening['accepted_metadata'] else 'rejected_metadata'] += 1
                    outcome = 'accepted' if screening['accepted_metadata'] else 'rejected'
                    finish_record(request_id, ordinal, outcome, {**screening, 'reused_identity': reused, 'canonical_changes': changes}, paper)
                    checkpoint(pmid, outcome, paper=paper)
                for pmid in set(pmids)-returned:
                    totals['not_returned'] += 1
                    checkpoint(pmid, 'not_returned', 'not returned by this frozen indexed MED batch; availability unknown')
                finish_request(request_id, 'complete')
                break
            except StopHarvest as exc:
                totals['requested_id_occurrences'] -= len(pmids)
                finish_request(request_id, 'budget_boundary', str(exc))
                c = atlas.connect()
                for pmid in pmids:
                    c.execute("UPDATE pmid_neighbor_checkpoint SET status='pending',attempts=attempts-1 WHERE pmid=?", (pmid,))
                c.commit()
                c.close()
                stopped = str(exc)
            except requests.RequestException as exc:
                cooldown = neighbors.after(3600)
                finish_request(request_id, 'retryable', str(exc), response=response)
                for pmid in pmids:
                    checkpoint(pmid, 'retryable', str(exc), cooldown)
                stopped = 'Europe PMC network failure; resume later'
        print(json.dumps({'stage': 'pmid_neighbor_batch', 'time': atlas.now(), 'requests': client.count, **totals}), flush=True)
    atlas.resolve()
    c = atlas.connect()
    requested_unique = set()
    for ids, in c.execute("SELECT requested_pmids FROM pmid_neighbor_requests WHERE run=? AND outcome!='budget_boundary'", (run_id,)):
        requested_unique.update(json.loads(ids))
    raw_returned = c.execute('''SELECT count(*) FROM pmid_neighbor_records r
                               JOIN pmid_neighbor_requests q ON q.id=r.request WHERE q.run=?''', (run_id,)).fetchone()[0]
    report = {'version': VERSION, 'mode': 'network', 'run': run_id, 'started': started, 'finished': atlas.now(),
              'cutoff': atlas.CUTOFF, 'endpoint': ENDPOINT, 'batch_size': batch_size,
              'max_candidates': max_candidates, 'max_requests': client.maximum,
              'requests_this_run': client.count, 'minimum_interval_seconds': getattr(client, 'interval', None),
              'unique_pmids_requested_this_run': len(requested_unique),
              'raw_response_rows_this_run': raw_returned,
              'selected_pmids': [{'pmid': b['pmid'], 'citing_papers': b['citing_papers'], 'title_signal': b['title_signal']} for b in candidates],
              'totals': totals, 'checkpoint_states': dict(c.execute('SELECT status,count(*) FROM pmid_neighbor_checkpoint GROUP BY status')),
              'stopped': stopped or 'selected PMID snapshot exhausted', 'cooldown_until': cooldown,
              'screening': 'automatic native metadata screening, not manual verification',
              'requires_before_export': ['stop all writers', 'atlas.rescreen', 'supplement.anchors', 'resolve/export/audit'],
              'limits': ['Indexed batch absence is unknown coverage, not a nonexistent PMID.',
                         'Accepted counts are provisional until final identity merging and rescreening.',
                         'No reference lists are fetched or inferred in this metadata stage.',
                         'Primary MED promotion is reported separately from new identities; every previous canonical version is archived.'],
              **public_context(context)}
    write_report(report, report_path)
    c.execute('UPDATE pmid_neighbor_runs SET finished=?,stopped=?,cooldown_until=?,report=? WHERE id=?',
              (report['finished'], report['stopped'], cooldown, json.dumps(report), run_id))
    c.commit()
    c.close()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-requests', type=int, default=20)
    parser.add_argument('--batch-size', type=int, default=100)
    parser.add_argument('--max-candidates', type=int)
    parser.add_argument('--min-citers', type=int, default=2)
    parser.add_argument('--interval', type=float, default=1.)
    parser.add_argument('--max-seconds', type=int, default=600)
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--enrich-cached', action='store_true', help='Use original validated cached MED responses; no network or new identities')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        client = Client(args.max_requests, args.interval, args.max_seconds)
        limit = args.max_candidates if args.max_candidates is not None else 10000 if args.enrich_cached else args.batch_size*args.max_requests
        if not 1 <= args.batch_size <= MAX_BATCH_SIZE or not 0 <= limit <= 10000 or args.min_citers < 2:
            raise ValueError('batch-size must be 1..100, max-candidates 0..10000 and min-citers at least 2')
        if args.plan_only:
            c = sqlite3.connect('file:'+quote(str(atlas.DB), safe='/')+'?mode=ro', uri=True)
            if args.enrich_cached:
                candidates = [{'request': r[0], 'ordinal': r[1], 'pmid': json.loads(r[2]).get('id'),
                               'previous_outcome': r[3]} for r in cached_records(c, limit)]
            else:
                candidates = select_candidates(c, limit, args.min_citers)
            c.close()
            print(json.dumps({'cutoff': atlas.CUTOFF, 'candidates': candidates}, indent=2))
        elif args.enrich_cached:
            report_path = args.report or ROOT/'research/pmid_neighbor_enrichment_report.json'
            print(json.dumps(enrich_cached(limit, report_path), indent=2))
        else:
            report_path = args.report or ROOT/'research/pmid_neighbor_report.json'
            print(json.dumps(run(client, args.batch_size, limit, args.min_citers, report_path), indent=2))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
