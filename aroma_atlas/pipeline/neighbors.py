#!/usr/bin/env python3
"""Bounded exact-DOI retrieval from actual references of accepted core papers.

This is discovery, not an acceptance override or a recursive citation crawler.
Run as the sole database writer. No credentials or accounts are used.
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
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import requests

import atlas
import supplement

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'citation-neighbors-v1'
ENDPOINT = 'https://api.crossref.org/works/'
TERMINAL = {'accepted', 'rejected', 'invalid', 'not_found'}
MAX_REQUESTS = 200
MAX_CANDIDATES = 500
MAX_ATTEMPTS = 3
MAX_REDIRECT_HOPS = 3
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
REDIRECT_POLICY = 'same-origin-crossref-works-v1'


def canonical_doi(value):
    """Normalize resolver prefix/case only; never guess truncated DOI suffixes."""
    if not isinstance(value, str):
        return ''
    value = supplement.normdoi(value)
    return value if re.fullmatch(r'10\.\d{4,9}/[^\s<>\x00-\x1f]+', value) else ''


def redirect_target(location):
    """Accept only an exact DOI endpoint on Crossref's same HTTPS origin."""
    if not isinstance(location, str) or re.search(r'[\s\\\x00-\x1f]', location):
        raise ValueError('missing or malformed Crossref DOI redirect Location')
    parsed = urlsplit(location)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme.lower() != 'https' or parsed.netloc.lower() not in {'api.crossref.org', 'api.crossref.org:443'}:
            raise ValueError('redirect leaves the Crossref HTTPS origin')
    elif not location.startswith('/works/'):
        raise ValueError('redirect is not a root-relative Crossref DOI endpoint')
    if parsed.query or parsed.fragment or not parsed.path.startswith('/works/'):
        raise ValueError('redirect has an unsupported path, query or fragment')
    decoded = unquote(parsed.path[len('/works/'):], errors='strict')
    doi = canonical_doi(decoded)
    if not doi or '\\' in decoded or any(piece in {'.', '..'} for piece in doi.split('/')):
        raise ValueError('redirect does not identify a syntactically valid DOI')
    return doi


def header(headers, name):
    return next((v for k, v in headers.items() if k.lower() == name.lower()), '')


def redirect_chain(c, doi):
    """Reconstruct only cached, validated HTTP redirect proof; never rewrite it."""
    chain = [doi]
    proofs = []
    for attempt_id, request_url, status, headers in c.execute('''SELECT id,request_url,http_status,response_headers
        FROM citation_neighbor_attempts WHERE doi=? AND http_status IN (301,302,303,307,308) ORDER BY id''', (doi,)):
        try:
            if redirect_target(request_url) != chain[-1]:
                continue
            target = redirect_target(header(json.loads(headers), 'Location'))
            if target in chain or len(proofs) >= MAX_REDIRECT_HOPS:
                continue
        except (ValueError, TypeError, AttributeError):
            continue
        chain.append(target)
        proofs.append(attempt_id)
    return chain, proofs


def stored_cooldown(c):
    """Ignore only proved legacy 301 cooldowns; retain their original audit rows."""
    rows = c.execute('SELECT id,stopped,cooldown_until FROM citation_neighbor_runs').fetchall()
    ignored, stale_values = {}, set()
    for run_id, stopped, cooldown in rows:
        if stopped != 'unexpected public-provider HTTP response; resume later':
            continue
        attempts = c.execute('''SELECT id,doi,request_url,http_status,response_headers,outcome
            FROM citation_neighbor_attempts WHERE run=? ORDER BY id''', (run_id,)).fetchall()
        abnormal = [a for a in attempts if a[3] not in (200, 404)]
        # An actual network/rate/server failure is never waived by a later redirect.
        if not abnormal or abnormal[-1][3] != 301 or any(a[3] != 301 for a in abnormal):
            continue
        latest = abnormal[-1]
        try:
            source = redirect_target(latest[2])
            target = redirect_target(header(json.loads(latest[4]), 'Location'))
            chain, proofs = redirect_chain(c, latest[1])
            if source == target or latest[0] not in proofs:
                continue
        except (ValueError, TypeError, AttributeError):
            continue
        ignored[run_id] = {'attempt': latest[0], 'doi': latest[1], 'from_doi': source,
                           'to_doi': target, 'legacy_cooldown_until': cooldown}
        stale_values.add(cooldown)
    # A previous invocation may merely have copied the same stale cooldown.
    for run_id, stopped, cooldown in rows:
        if stopped == 'stored public-provider cooldown remains active' and cooldown in stale_values:
            if not c.execute('SELECT 1 FROM citation_neighbor_attempts WHERE run=? LIMIT 1', (run_id,)).fetchone():
                ignored[run_id] = {'inherited_legacy_cooldown_until': cooldown}
    effective = max((r[2] or '' for r in rows if r[0] not in ignored), default='')
    return effective, ignored


def init():
    supplement.init()
    c = atlas.connect()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS citation_neighbor_checkpoint(
      doi TEXT PRIMARY KEY, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
      updated TEXT NOT NULL, retry_after TEXT NOT NULL DEFAULT '', error TEXT NOT NULL DEFAULT '',
      paper TEXT NOT NULL DEFAULT '', last_run TEXT NOT NULL DEFAULT '');
    CREATE TABLE IF NOT EXISTS citation_neighbor_origins(
      doi TEXT, citing_paper TEXT, citing_doi TEXT, target_source TEXT, target_id TEXT,
      raw_doi TEXT, supplied_title TEXT, citing_queries TEXT, first_run TEXT,
      PRIMARY KEY(doi,citing_paper,target_source,target_id));
    CREATE TABLE IF NOT EXISTS citation_neighbor_attempts(
      id INTEGER PRIMARY KEY, run TEXT, doi TEXT, started TEXT, finished TEXT,
      request_url TEXT, response_url TEXT, http_status INTEGER, response_headers TEXT,
      response_body TEXT, outcome TEXT, screening TEXT, ingestion TEXT, error TEXT);
    CREATE TABLE IF NOT EXISTS citation_neighbor_runs(
      id TEXT PRIMARY KEY, started TEXT, finished TEXT, stopped TEXT,
      cooldown_until TEXT, report TEXT);
    ''')
    c.commit()
    c.close()


def core_tracks(value):
    try:
        tracks = json.loads(value or '[]')
    except (TypeError, ValueError):
        return False
    return isinstance(tracks, list) and bool(set(tracks) & {'aroma', 'prediction'})


def title_signal(title):
    """A prioritization signal only; never substitute a reference title for metadata."""
    if not title:
        return False
    ok, _, tracks, _ = atlas.classify(atlas.clean(title), '')
    return bool(ok and set(tracks) & {'aroma', 'prediction'})


def select_candidates(c, limit=100, min_citers=2, at=None):
    """Snapshot unresolved DOI references with a title signal or repeated core origin.

    Distinct citing papers count once even if multiple providers report the reference.
    Existing rejected endpoints are not unresolved and are never reintroduced here.
    """
    at = at or atlas.now()
    known = {canonical_doi(r[0]) for r in c.execute('SELECT doi FROM papers WHERE doi!=""')}
    known.update(canonical_doi(r[0]) for r in c.execute('''SELECT a.source_id FROM source_alias a
        JOIN papers p ON p.id=a.paper WHERE a.source='DOI' '''))
    tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    checkpoints = {}
    ignored_runs = {}
    if 'citation_neighbor_checkpoint' in tables:
        checkpoints = {r[0]: r[1:] for r in c.execute(
            'SELECT doi,status,attempts,retry_after,last_run,error FROM citation_neighbor_checkpoint')}
        _, ignored_runs = stored_cooldown(c)
    candidates = {}
    query = '''SELECT r.paper,p.doi,p.tracks,r.target_source,r.target_id,r.doi,r.title
               FROM raw_refs r JOIN papers p ON r.paper=p.id
               WHERE p.accepted=1 AND r.doi!=''
               ORDER BY r.paper,r.target_source,r.target_id'''
    rows = c.execute(query)
    for pid, citing_doi, tracks, source, target_id, raw_doi, title in rows:
        if not core_tracks(tracks):
            continue
        doi = canonical_doi(raw_doi)
        if not doi or doi in known or doi == canonical_doi(citing_doi):
            continue
        state = checkpoints.get(doi)
        if state:
            chain, _ = redirect_chain(c, doi)
            legacy_redirect = state[3] in ignored_runs and state[4] == 'unexpected HTTP 301'
            if (state[0] in TERMINAL or state[1] >= MAX_ATTEMPTS + len(chain)-1 or
                    (state[2] > at and not legacy_redirect)):
                continue
        entry = candidates.setdefault(doi, {'doi': doi, 'origins': [], 'citers': set(),
                                             'title_signal': False})
        entry['citers'].add(pid)
        if not entry['title_signal']:
            entry['title_signal'] = title_signal(title)
    chosen = [v for v in candidates.values() if v['title_signal'] or len(v['citers']) >= min_citers]
    chosen.sort(key=lambda v: (-int(v['title_signal']), -len(v['citers']), v['doi']))
    chosen = chosen[:limit]
    selected = {entry['doi']: entry for entry in chosen}
    # Retain full origin text only for the bounded selected set, not the entire
    # unresolved bibliography. All unselected original rows remain in raw_refs.
    for pid, citing_doi, tracks, source, target_id, raw_doi, title in c.execute(query):
        doi = canonical_doi(raw_doi)
        if doi in selected and core_tracks(tracks):
            selected[doi]['origins'].append({'citing_paper': pid, 'citing_doi': citing_doi,
                                             'target_source': source, 'target_id': target_id,
                                             'raw_doi': raw_doi, 'supplied_title': title or ''})
    for entry in chosen:
        entry['citing_papers'] = len(entry.pop('citers'))
        for origin in entry['origins']:
            origin['citing_queries'] = [r[0] for r in c.execute(
                'SELECT query FROM provenance WHERE paper=? ORDER BY query',
                (origin['citing_paper'],))]
    return chosen


class StopHarvest(RuntimeError):
    pass


class Client:
    """One serial request per call; every retry is controlled/audited by run()."""
    def __init__(self, max_requests=80, interval=1.5, max_seconds=600):
        if not 0 <= max_requests <= MAX_REQUESTS:
            raise ValueError('max_requests must be between 0 and 200')
        if not math.isfinite(interval) or interval < 1.5:
            raise ValueError('interval must be at least 1.5 seconds')
        if not 1 <= max_seconds <= 3600:
            raise ValueError('max_seconds must be between 1 and 3600')
        self.maximum, self.interval, self.max_seconds = max_requests, interval, max_seconds
        self.count = 0
        self.last = 0
        self.started = time.monotonic()
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'AromaResearchAtlas/1.0 (public citation metadata research)'

    def available(self):
        return self.count < self.maximum and time.monotonic() - self.started < self.max_seconds

    def get(self, doi):
        delay = max(0, self.interval - (time.monotonic() - self.last))
        if not self.available() or delay > 60 or time.monotonic() - self.started + delay >= self.max_seconds:
            raise StopHarvest('request or elapsed-time budget reached')
        time.sleep(delay)
        self.last = time.monotonic()
        self.count += 1
        response = self.session.get(ENDPOINT + quote(doi, safe=''), timeout=(15, 45), allow_redirects=False)
        # A stricter server-advertised interval always takes priority over our floor.
        interval = re.search(r'([0-9.]+)', response.headers.get('X-Rate-Limit-Interval', ''))
        try:
            if interval:
                self.interval = max(self.interval, float(interval[1]) /
                                    max(.001, float(response.headers.get('X-Rate-Limit-Limit', '1'))))
        except ValueError:
            pass
        return response


def retry_seconds(headers):
    value = headers.get('Retry-After', '')
    try:
        seconds = float(value)
        return max(0, seconds) if math.isfinite(seconds) else 60
    except (TypeError, ValueError):
        try:
            when = parsedate_to_datetime(value)
            return max(0, (when - dt.datetime.now(dt.timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return 60


def after(seconds):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=seconds)).isoformat()


def remember_origins(candidate, run_id):
    c = atlas.connect()
    for o in candidate['origins']:
        c.execute('INSERT OR IGNORE INTO citation_neighbor_origins VALUES(?,?,?,?,?,?,?,?,?)',
                  (candidate['doi'], o['citing_paper'], o['citing_doi'], o['target_source'],
                   o['target_id'], o['raw_doi'], o['supplied_title'],
                   json.dumps(o['citing_queries']), run_id))
    c.execute('''INSERT OR IGNORE INTO citation_neighbor_checkpoint(doi,status,updated,last_run)
                 VALUES(?,'pending',?,?)''', (candidate['doi'], atlas.now(), run_id))
    c.commit()
    c.close()


def begin_attempt(doi, run_id, request_doi=None):
    c = atlas.connect()
    cur = c.execute('''INSERT INTO citation_neighbor_attempts
        (run,doi,started,request_url,outcome) VALUES(?,?,?,?, 'in_progress')''',
        (run_id, doi, atlas.now(), ENDPOINT + quote(request_doi or doi, safe='')))
    c.execute('''UPDATE citation_neighbor_checkpoint SET status='in_progress',
        attempts=attempts+1,updated=?,last_run=? WHERE doi=?''', (atlas.now(), run_id, doi))
    c.commit()
    result = cur.lastrowid
    c.close()
    return result


def finish_attempt(attempt_id, doi, outcome, response=None, error='', screening=None,
                   ingestion=None, retry_after='', paper=''):
    c = atlas.connect()
    c.execute('''UPDATE citation_neighbor_attempts SET finished=?,response_url=?,http_status=?,
        response_headers=?,response_body=?,outcome=?,screening=?,ingestion=?,error=? WHERE id=?''',
        (atlas.now(), getattr(response, 'url', ''), getattr(response, 'status_code', None),
         json.dumps(dict(response.headers)) if response is not None else '{}',
         response.text if response is not None else '', outcome,
         json.dumps(screening or {}), json.dumps(ingestion or {}), error, attempt_id))
    c.execute('''UPDATE citation_neighbor_checkpoint SET status=?,updated=?,retry_after=?,
        error=?,paper=? WHERE doi=?''', (outcome, atlas.now(), retry_after, error, paper, doi))
    c.commit()
    c.close()


def validated_message(response, doi):
    payload = response.json()
    if not isinstance(payload, dict) or payload.get('status') != 'ok':
        raise ValueError('missing successful Crossref envelope')
    message = payload.get('message')
    if not isinstance(message, dict) or canonical_doi(message.get('DOI')) != doi:
        raise ValueError('missing or mismatched exact DOI; response not ingested')
    if not isinstance(message.get('title'), list) or not all(isinstance(x, str) for x in message['title']):
        raise ValueError('malformed title field')
    if 'reference' in message and (not isinstance(message['reference'], list) or
                                  not all(isinstance(x, dict) for x in message['reference'])):
        raise ValueError('malformed deposited references')
    for reference in message.get('reference', []):
        for key in ['DOI', 'article-title', 'unstructured']:
            if key in reference and not isinstance(reference[key], str):
                raise ValueError('malformed deposited reference '+key)
    if 'abstract' in message and not isinstance(message['abstract'], str):
        raise ValueError('malformed abstract')
    if 'container-title' in message and (not isinstance(message['container-title'], list) or
                                         not all(isinstance(x, str) for x in message['container-title'])):
        raise ValueError('malformed container-title')
    if 'author' in message:
        if not isinstance(message['author'], list) or not all(isinstance(x, dict) for x in message['author']):
            raise ValueError('malformed authors')
        for author in message['author']:
            if any(key in author and not isinstance(author[key], str) for key in ['given', 'family', 'name']):
                raise ValueError('malformed author name')
    # Normalize only the matched metadata identity; the unmodified envelope is retained.
    message = dict(message)
    message['DOI'] = doi
    return message


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(client=None, max_candidates=100, min_citers=2, report_path=None):
    if not 0 <= max_candidates <= MAX_CANDIDATES or min_citers < 2:
        raise ValueError('max_candidates must be 0..500 and min_citers at least 2')
    if atlas.CUTOFF != '2026-10-26':
        raise ValueError('citation-neighbors-v1 is frozen to cutoff 2026-10-26')
    init()
    client = client or Client()
    run_id, started = str(uuid.uuid4()), atlas.now()
    c = atlas.connect()
    cooldown, ignored_cooldowns = stored_cooldown(c)
    candidates = select_candidates(c, max_candidates, min_citers)
    c.execute('INSERT INTO citation_neighbor_runs VALUES(?,?,NULL,?,?,?)',
              (run_id, started, '', '', '{}'))
    c.commit()
    c.close()
    totals = {'retrieved_exact': 0, 'accepted_metadata': 0, 'rejected_metadata': 0,
              'accepted_new': 0, 'new': 0, 'reused': 0, 'invalid': 0, 'not_found': 0,
              'retryable': 0, 'redirect_responses': 0, 'doi_aliases_added': 0}
    stopped, throttle_count, server_failures = '', 0, 0
    if cooldown > atlas.now():
        stopped = 'stored public-provider cooldown remains active'
    for candidate in candidates:
        if stopped:
            break
        doi = candidate['doi']
        remember_origins(candidate, run_id)
        c = atlas.connect()
        chain, proof_ids = redirect_chain(c, doi)
        c.close()
        while True:
            c = atlas.connect()
            attempts = c.execute('SELECT attempts FROM citation_neighbor_checkpoint WHERE doi=?',
                                 (doi,)).fetchone()[0]
            c.close()
            if attempts >= MAX_ATTEMPTS + len(proof_ids):
                break
            if not client.available():
                stopped = 'request or elapsed-time budget reached'
                break
            request_doi = chain[-1]
            attempt_id = begin_attempt(doi, run_id, request_doi)
            response = None
            try:
                response = client.get(request_doi)
                # Cache before parsing/ingestion so an interrupted write can be audited.
                c = atlas.connect()
                c.execute('''UPDATE citation_neighbor_attempts SET response_url=?,http_status=?,
                             response_headers=?,response_body=? WHERE id=?''',
                          (response.url, response.status_code, json.dumps(dict(response.headers)),
                           response.text, attempt_id))
                c.commit()
                c.close()
                status = response.status_code
                if 300 <= status < 400:
                    try:
                        if status not in REDIRECT_STATUSES:
                            raise ValueError('unsupported Crossref redirect HTTP '+str(status))
                        target = redirect_target(header(response.headers, 'Location'))
                        if target in chain:
                            raise ValueError('Crossref DOI redirect loop')
                        if len(proof_ids) >= MAX_REDIRECT_HOPS:
                            raise ValueError('Crossref DOI redirect hop limit reached')
                    except (ValueError, TypeError, AttributeError) as exc:
                        totals['invalid'] += 1
                        finish_attempt(attempt_id, doi, 'invalid', response, error=str(exc))
                        break
                    finish_attempt(attempt_id, doi, 'redirect', response,
                                   screening={'redirect_policy': REDIRECT_POLICY,
                                              'from_doi': request_doi, 'to_doi': target,
                                              'hop': len(proof_ids)+1})
                    chain.append(target)
                    proof_ids.append(attempt_id)
                    totals['redirect_responses'] += 1
                    continue
                if status == 429 or status in {500, 502, 503, 504}:
                    throttle_count += int(status == 429)
                    server_failures += int(status != 429)
                    delay = max(2, retry_seconds(response.headers))
                    persistent = throttle_count >= 2 or server_failures >= 3
                    if persistent:
                        delay = max(delay, 3600)
                    cooldown = max(cooldown, after(delay))
                    finish_attempt(attempt_id, doi, 'retryable', response,
                                   error='HTTP '+str(status), retry_after=cooldown)
                    totals['retryable'] += 1
                    if persistent:
                        stopped = 'persistent public-provider throttling or server failure'
                        break
                    # Never shorten Retry-After. Long waits resume on a later run.
                    if delay > 60 or not client.available() or attempts + 1 >= MAX_ATTEMPTS:
                        stopped = 'public-provider cooldown; resume later'
                        break
                    time.sleep(delay)
                    cooldown = ''
                    continue
                if status == 404:
                    totals['not_found'] += 1
                    finish_attempt(attempt_id, doi, 'not_found', response)
                    break
                if status != 200:
                    totals['retryable'] += 1
                    cooldown = after(3600)
                    finish_attempt(attempt_id, doi, 'retryable', response,
                                   error='unexpected HTTP '+str(status), retry_after=cooldown)
                    stopped = 'unexpected public-provider HTTP response; resume later'
                    break
                try:
                    message = validated_message(response, request_doi)
                    ok, category, tracks, evidence, _, _, when = supplement.classify_record(message)
                    if proof_ids:
                        c = atlas.connect()
                        alias = c.execute('''SELECT p.doi FROM source_alias a JOIN papers p ON p.id=a.paper
                                             WHERE a.source='DOI' AND a.source_id=?''', (doi,)).fetchone()
                        c.close()
                        if alias and canonical_doi(alias[0]) != request_doi:
                            raise ValueError('existing DOI alias conflicts with verified redirect target')
                except (ValueError, TypeError, AttributeError, KeyError) as exc:
                    totals['invalid'] += 1
                    finish_attempt(attempt_id, doi, 'invalid', response, error=str(exc))
                    break
                screening = {'accepted': bool(ok), 'category': category, 'tracks': tracks,
                             'evidence': evidence, 'publication_date': when.isoformat() if when else None,
                             'classifier': 'supplement.classify_record', 'cutoff': atlas.CUTOFF,
                             'requested_doi': doi, 'canonical_doi': request_doi,
                             'redirect_chain': chain, 'redirect_proof_attempts': proof_ids}
                counts = supplement.ingest([message], VERSION+':'+doi)
                c = atlas.connect()
                paper = c.execute('SELECT id FROM papers WHERE doi=? ORDER BY accepted DESC LIMIT 1',
                                  (request_doi,)).fetchone()[0]
                if proof_ids:
                    inserted = c.execute('INSERT OR IGNORE INTO source_alias VALUES(?,?,?)',
                                         ('DOI', doi, paper)).rowcount
                    totals['doi_aliases_added'] += inserted
                for origin in candidate['origins']:
                    c.execute('INSERT OR IGNORE INTO provenance VALUES(?,?)',
                              (paper, 'citation-neighbor:'+origin['citing_paper']+'|doi:'+doi))
                c.commit()
                c.close()
                totals['retrieved_exact'] += 1
                totals['accepted_metadata' if ok else 'rejected_metadata'] += 1
                for key in ['accepted_new', 'new', 'reused']:
                    totals[key] += counts[key]
                finish_attempt(attempt_id, doi, 'accepted' if ok else 'rejected', response,
                               screening=screening, ingestion=counts, paper=paper)
                break
            except StopHarvest as exc:
                # No request was sent if the client detected a time boundary before sleep.
                finish_attempt(attempt_id, doi, 'retryable', error=str(exc))
                c = atlas.connect()
                c.execute('UPDATE citation_neighbor_checkpoint SET attempts=attempts-1 WHERE doi=?', (doi,))
                c.commit()
                c.close()
                stopped = str(exc)
                break
            except requests.RequestException as exc:
                totals['retryable'] += 1
                finish_attempt(attempt_id, doi, 'retryable', response, error=str(exc),
                               retry_after=after(3600))
                stopped = 'network failure; resume later'
                break
        supplement.log(stage='citation_neighbor', doi=doi, requests=client.count, **totals)
    # Uses only supplied references with accepted endpoints; no title-similarity edges.
    atlas.resolve()
    # Persist a stricter advertised interval across process restarts as well.
    if getattr(client, 'interval', 1.5) > 1.5:
        remaining = client.interval - (time.monotonic() - client.last)
        if remaining > 0:
            cooldown = max(cooldown, after(remaining))
    c = atlas.connect()
    states = dict(c.execute('SELECT status,count(*) FROM citation_neighbor_checkpoint GROUP BY status'))
    report = {'version': VERSION, 'run': run_id, 'started': started, 'finished': atlas.now(),
              'cutoff': atlas.CUTOFF, 'endpoint': ENDPOINT+'{exact DOI}',
              'redirect_policy': REDIRECT_POLICY, 'max_redirect_hops': MAX_REDIRECT_HOPS,
              'ignored_legacy_301_cooldowns': ignored_cooldowns,
              'screening': 'automatic title/abstract rules; not manual verification',
              'candidate_policy': 'unresolved DOI from accepted aroma/prediction raw_refs; title signal or repeated distinct core citing papers',
              'selected_candidates': [{'doi': x['doi'], 'citing_papers': x['citing_papers'],
                                       'title_signal': x['title_signal']} for x in candidates],
              'max_candidates': max_candidates, 'min_citers': min_citers,
              'max_requests': client.maximum, 'requests_this_run': client.count,
              'minimum_interval_seconds': getattr(client, 'interval', None),
              'max_seconds': getattr(client, 'max_seconds', None),
              'totals': totals, 'checkpoint_states': states,
              'stopped': stopped or 'selected snapshot exhausted', 'cooldown_until': cooldown,
              'hashes': {'neighbors.py': file_hash(__file__), 'supplement.py': file_hash(supplement.__file__),
                         'atlas.py': file_hash(atlas.__file__)}}
    c.execute('UPDATE citation_neighbor_runs SET finished=?,stopped=?,cooldown_until=?,report=? WHERE id=?',
              (report['finished'], report['stopped'], cooldown, json.dumps(report), run_id))
    c.commit()
    c.close()
    if report_path:
        Path(report_path).write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-candidates', type=int, default=100)
    parser.add_argument('--max-requests', type=int, default=80)
    parser.add_argument('--min-citers', type=int, default=2)
    parser.add_argument('--interval', type=float, default=1.5)
    parser.add_argument('--max-seconds', type=int, default=600)
    parser.add_argument('--plan-only', action='store_true', help='Read-only candidate preview; no network or checkpoint writes')
    parser.add_argument('--report', type=Path, default=ROOT/'research/citation_neighbor_report.json')
    args = parser.parse_args()
    try:
        client = Client(args.max_requests, args.interval, args.max_seconds)
        if not 0 <= args.max_candidates <= MAX_CANDIDATES or args.min_citers < 2:
            raise ValueError('max-candidates must be 0..500 and min-citers at least 2')
        if args.plan_only:
            c = sqlite3.connect('file:'+quote(str(atlas.DB), safe='/')+'?mode=ro', uri=True)
            result = select_candidates(c, args.max_candidates, args.min_citers)
            c.close()
            print(json.dumps({'cutoff': atlas.CUTOFF, 'candidates': result}, indent=2))
        else:
            print(json.dumps(run(client, args.max_candidates, args.min_citers, args.report), indent=2))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
