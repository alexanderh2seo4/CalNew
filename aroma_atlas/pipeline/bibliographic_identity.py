"""Validate a frozen, enumerated AGR/MED identity manifest without changing SQLite.

This is identity evidence only: it neither screens papers nor constructs citations.
No newly similar title can nominate a merge through this module.
"""
import hashlib
import html
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / 'research/verified_bibliographic_merges_2026-10-28.json'


class IdentityProofError(ValueError):
    pass


def digest(value):
    if isinstance(value, str):
        value = value.encode('utf-8')
    return hashlib.sha256(value).hexdigest()


def normalized(value):
    value = re.sub(r'<[^>]+>', ' ', html.unescape(value or ''))
    return re.sub(r'\s+', ' ', value).strip().rstrip('.!?;: ,')


def rendering(value):
    value = re.sub(r'<[^>]+>', ' ', html.unescape(value or ''))
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', value))


def _journal(row):
    raw = json.loads(row['raw'])
    info = raw.get('journalInfo') or {}
    journal = info.get('journal') or {}
    return {
        'volume': normalized(str(info.get('volume') or '')),
        'names': sorted({normalized(x).casefold() for x in
                         (row.get('journal'), journal.get('title')) if x}),
        'issns': sorted({normalized(journal[k]) for k in ('issn', 'essn')
                         if journal.get(k)}),
        'page_info': raw.get('pageInfo'),
    }


def _crossref_bridge(left, right, audit):
    """The one reviewed DOI bridge; never infer a general ISSN equivalence."""
    if (left['id'], right['id']) != ('AGR:IND609267307', 'pmid:40356132'):
        return None
    response = audit.get('known_pair_crossref_proof') or {}
    body = response.get('raw_body', '')
    if response.get('status') != 200 or digest(body) != response.get('body_sha256'):
        raise IdentityProofError('missing or changed known-pair Crossref response')
    if response.get('url') != 'https://api.crossref.org/works/10.1016%2Fj.foodres.2025.116467':
        raise IdentityProofError('unexpected Crossref proof origin')
    message = json.loads(body).get('message', {})
    a, b = _journal(left), _journal(right)
    valid = (
        message.get('DOI', '').lower() == right.get('doi', '').lower()
        and bool(set(a['issns']) & set(message.get('ISSN', [])))
        and bool(set(a['names']) & {normalized(x).casefold()
                                   for x in message.get('container-title', [])})
        and str(message.get('volume')) == a['volume'] == b['volume']
        and str(message.get('article-number') or message.get('page')) == str(b['page_info'])
        and normalized(' '.join(message.get('title', []))).casefold()
        == normalized(left['title']).casefold()
        and message.get('published', {}).get('date-parts', [[None]])[0][0] == left['year']
    )
    if not valid:
        raise IdentityProofError('known-pair Crossref bibliographic bridge differs')
    return {'kind': 'reviewed-record-specific-crossref-bridge',
            'response_sha256': digest(body), 'url': response['url'],
            'doi': message['DOI'], 'volume': message['volume'],
            'article_number': message.get('article-number') or message.get('page'),
            'note': 'Print ISSN and AGR journal match DOI deposit; MED DOI and article number match. No general print/electronic ISSN crosswalk.'}


def _proof(left, right, mode, audit):
    if left.get('source') != 'AGR' or right.get('source') != 'MED':
        raise IdentityProofError('only enumerated AGR/MED source identities qualify')
    if not left.get('source_id') or not right.get('source_id') or left['id'] == right['id']:
        raise IdentityProofError('missing or ambiguous source identity')
    if left.get('doi') and right.get('doi'):
        raise IdentityProofError('at least one DOI must be absent')
    if left.get('pmid') and right.get('pmid') and left['pmid'] != right['pmid']:
        raise IdentityProofError('conflicting PMID')
    for key in ('title', 'authors'):
        if not normalized(left.get(key)).casefold() or normalized(left.get(key)).casefold() != normalized(right.get(key)).casefold():
            raise IdentityProofError('different normalized ' + key)
    if not left.get('year') or left['year'] != right['year']:
        raise IdentityProofError('different publication year')
    a, b = _journal(left), _journal(right)
    if not a['volume'] or a['volume'] != b['volume']:
        raise IdentityProofError('different or missing journal volume')
    shared_issns = sorted(set(a['issns']) & set(b['issns']))
    shared_names = sorted(set(a['names']) & set(b['names']))
    bridge = None
    if not (shared_issns or shared_names):
        bridge = _crossref_bridge(left, right, audit)
        if bridge is None:
            raise IdentityProofError('journal identity lacks corroboration')
    if min(len(normalized(left.get('abstract'))), len(normalized(right.get('abstract')))) < 200:
        raise IdentityProofError('abstract too short for identity proof')
    if mode not in ('strict', 'standard-rendering'):
        raise IdentityProofError('unknown abstract normalization mode')
    ab = normalized if mode == 'strict' else rendering
    if ab(left.get('abstract')) != ab(right.get('abstract')):
        raise IdentityProofError('abstract fingerprints differ')
    return {'match_mode': mode, 'title_sha256': digest(normalized(left['title']).casefold()),
            'authors_sha256': digest(normalized(left['authors']).casefold()),
            'year': left['year'], 'volume': a['volume'],
            'abstract_sha256': digest(ab(left['abstract'])),
            'abstract_normalized_lengths': [len(normalized(left['abstract'])), len(normalized(right['abstract']))],
            'shared_journal_issns': shared_issns, 'shared_journal_names': shared_names,
            'record_specific_crossref_bridge': bridge}


def _record_fingerprint(row):
    """Only source metadata; acceptance, categories and evidence can be rescreened."""
    return {'id': row['id'], 'source': row['source'], 'source_id': row['source_id'],
            'doi': row.get('doi') or '', 'pmid': row.get('pmid') or '',
            'raw_sha256': digest(row['raw']),
            'source_metadata_sha256': digest(json.dumps({k: row.get(k) for k in
                ('title', 'authors', 'year', 'journal', 'abstract', 'doi', 'pmid', 'source', 'source_id')},
                sort_keys=True, ensure_ascii=False, separators=(',', ':')))}


def manifest_from_audit(audit, audit_name, audit_sha256):
    """Build only the already frozen union, never search the current database."""
    enumerated = {}
    for record in audit['very_high_confidence_duplicates']:
        enumerated[(record['left']['id'], record['right']['id'])] = (record, 'strict')
    for record in audit['standard_rendering_equivalence_cohort']['pairs']:
        enumerated.setdefault((record['left']['id'], record['right']['id']), (record, 'standard-rendering'))
    expected = audit['strict_or_standard_rendering_union']['pair_count']
    if len(enumerated) != expected:
        raise IdentityProofError('frozen audit union count differs')
    pairs = []
    removed = set()
    for (remove, keep), (record, mode) in sorted(enumerated.items()):
        if remove in removed:
            raise IdentityProofError('one AGR identity nominates multiple MED identities')
        removed.add(remove)
        left, right = record['left'], record['right']
        pairs.append({'remove_id': remove, 'keep_id': keep,
                      'remove_metadata': _record_fingerprint(left),
                      'keep_metadata': _record_fingerprint(right),
                      'proof': _proof(left, right, mode, audit)})
    return {'schema_version': 1, 'purpose': 'Frozen bibliographic identity only; no acceptance or edge overrides',
            'audit_file': audit_name, 'audit_sha256': audit_sha256,
            'pair_count': len(pairs), 'pairs': pairs}


def _row(connection, paper_id):
    cursor = connection.execute('SELECT * FROM papers WHERE id=?', (paper_id,))
    rows = cursor.fetchall()
    if len(rows) > 1:
        raise IdentityProofError('ambiguous current paper identity ' + paper_id)
    return dict(zip((x[0] for x in cursor.description), rows[0])) if rows else None


def _alias(connection, source, source_id):
    rows = connection.execute('SELECT paper FROM source_alias WHERE source=? AND source_id=?',
                              (source, source_id)).fetchall()
    if len(rows) > 1:
        raise IdentityProofError('ambiguous source alias')
    return rows[0][0] if rows else None


def validated_pairs(connection, manifest_path=None):
    """Return (remove_id, keep_id, proof) triples; raise on any stale proof.

    Caller owns transaction/snapshot and any subsequent merge. An absent AGR row
    is skipped only when its original source alias already names the verified MED.
    Validation is all-or-nothing: no partially validated list escapes on failure.
    """
    path = Path(manifest_path or DEFAULT_MANIFEST)
    manifest = json.loads(path.read_text())
    audit_path = path.parent / manifest['audit_file']
    audit_bytes = audit_path.read_bytes()
    if digest(audit_bytes) != manifest.get('audit_sha256'):
        raise IdentityProofError('frozen original audit hash differs')
    audit = json.loads(audit_bytes)
    expected = manifest_from_audit(audit, manifest['audit_file'], manifest['audit_sha256'])
    if manifest != expected:
        raise IdentityProofError('manifest differs from frozen enumerated audit proof')
    result = []
    for pair in manifest['pairs']:
        left = _row(connection, pair['remove_id'])
        right = _row(connection, pair['keep_id'])
        if right is None:
            raise IdentityProofError('missing MED metadata ' + pair['keep_id'])
        target_alias = _alias(connection, right['source'], right['source_id'])
        if target_alias not in (None, right['id']):
            raise IdentityProofError('MED source alias conflicts')
        old = pair['remove_metadata']
        alias = _alias(connection, old['source'], old['source_id'])
        if left is None:
            original = pair['keep_metadata']
            stable = all(right.get(k) == original[k] for k in ('id','source','source_id'))
            stable = stable and all(not original[k] or (right.get(k) or '') == original[k] for k in ('doi','pmid'))
            if alias == right['id'] and stable:
                continue
            raise IdentityProofError('absent AGR without verified retained alias ' + pair['remove_id'])
        if _record_fingerprint(right) != pair['keep_metadata']:
            raise IdentityProofError('stale MED metadata ' + pair['keep_id'])
        if alias not in (None, left['id']):
            raise IdentityProofError('present AGR source alias conflicts')
        if _record_fingerprint(left) != old:
            raise IdentityProofError('stale AGR metadata ' + pair['remove_id'])
        proof = _proof(left, right, pair['proof']['match_mode'], audit)
        if proof != pair['proof']:
            raise IdentityProofError('current identity proof differs')
        result.append((left['id'], right['id'], proof))
    return result
