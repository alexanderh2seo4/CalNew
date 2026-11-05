"""Reference-list coverage across actual returned provider lists.

Metadata-only PMID discovery and provider citation totals are not reference lists.
"""


def collect(connection, accepted_ids=None):
    identities = {pid: doi for pid, doi in connection.execute('SELECT id,doi FROM papers')}
    allowed = set(identities) if accepted_ids is None else set(accepted_ids)
    by_doi = {doi.lower(): pid for pid, doi in identities.items() if doi}
    tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    doi_aliases = dict(connection.execute("SELECT source_id,paper FROM source_alias WHERE source='DOI'")) if 'source_alias' in tables else {}
    processed, available, errors = set(), set(), set()
    providers = {}

    def add(provider, paper, complete, nonempty, failed=False):
        if paper not in allowed:
            return
        group = providers.setdefault(provider, {'processed': set(), 'available': set(), 'errors': set()})
        for enabled, total, per_source in [(complete, processed, group['processed']), (nonempty, available, group['available']), (failed, errors, group['errors'])]:
            if enabled:
                total.add(paper)
                per_source.add(paper)

    for pid, status, retrieved, note in connection.execute('SELECT paper,status,retrieved,error FROM refs'):
        provider = next((name for name in ['Crossref','OpenAlex','Semantic Scholar'] if (note or '').startswith(name)), 'Europe PMC')
        add(provider, pid, status == 'complete', retrieved > 0, status == 'error')
    if 'identity_reference_archive' in tables:
        import json
        for kept, source, sid, payload in connection.execute('SELECT kept_paper,source,source_id,refs_row FROM identity_reference_archive'):
            pid=kept
            if pid not in identities:
                alias=connection.execute('SELECT paper FROM source_alias WHERE source=? AND source_id=?',(source,sid)).fetchone()
                pid=alias[0] if alias else None
            row=json.loads(payload)
            provider=next((name for name in ['Crossref','OpenAlex','Semantic Scholar'] if str(row[5] or '').startswith(name)), 'Europe PMC')
            add(provider,pid,row[1]=='complete',row[3]>0,row[1]=='error')
    if 'crossref_responses' in tables:
        for old_pid, doi, returned in connection.execute('SELECT paper,doi,reference_rows FROM crossref_responses'):
            pid = old_pid if old_pid in identities else by_doi.get((doi or '').lower()) or doi_aliases.get((doi or '').lower())
            add('Crossref', pid, True, returned > 0)
    if 'openalex_refs' in tables:
        for pid, total in connection.execute('SELECT i.paper,r.total FROM openalex_refs r JOIN openalex_ids i ON r.openalex_id=i.openalex_id'):
            add('OpenAlex', pid, True, total > 0)
    if 'semantic_refs' in tables:
        for pid, status, retrieved in connection.execute('SELECT i.paper,r.status,r.retrieved FROM semantic_refs r JOIN semantic_ids i ON r.semantic_id=i.semantic_id'):
            add('Semantic Scholar', pid, status == 'complete', retrieved > 0, status == 'error')
    # A failed/paged lookup may still have supplied real reference rows. This
    # proves a nonempty list, but does not turn an incomplete lookup into complete.
    available.update(pid for pid, in connection.execute('SELECT DISTINCT paper FROM raw_refs') if pid in allowed)
    return {'processed': processed, 'available': available, 'errors': errors,
            'providers': {name: {k: len(v) for k, v in counts.items()} for name, counts in providers.items()},
            'definition': 'At least one supplied source-index response processed; nonempty evidence is the union of actual returned provider lists. Zero returned references leaves bibliography availability elsewhere unknown.'}


def status(paper, coverage):
    if paper in coverage['processed']:
        return 'complete' if paper in coverage['available'] else 'no indexed references'
    if paper in coverage['errors']:
        return 'error'
    return 'pending'
