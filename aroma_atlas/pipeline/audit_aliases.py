#!/usr/bin/env python3
"""Independently check every DOI alias against retained HTTP redirect evidence."""
import json
import sqlite3
from pathlib import Path
import atlas
from neighbors import canonical_doi, redirect_target, header


def audit(connection):
    aliases = connection.execute("SELECT a.source_id,a.paper,p.doi FROM source_alias a LEFT JOIN papers p ON p.id=a.paper WHERE a.source='DOI'").fetchall()
    tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    bad = []
    for alias, paper, target in aliases:
        supported = False
        if target and 'citation_neighbor_attempts' in tables:
            finals = connection.execute("SELECT request_url,response_body,screening FROM citation_neighbor_attempts WHERE doi=? AND http_status=200 AND outcome IN ('accepted','rejected')", (alias,)).fetchall()
            for url, body, screening in finals:
                try:
                    s = json.loads(screening)
                    chain, proofs = s['redirect_chain'], s['redirect_proof_attempts']
                    if not (2 <= len(chain) <= 4 and len(proofs) == len(chain)-1 and chain[0] == alias and chain[-1] == target):
                        continue
                    payload = json.loads(body)
                    if payload.get('status') != 'ok' or canonical_doi(payload.get('message', {}).get('DOI')) != target or redirect_target(url) != target:
                        continue
                    for index, proof in enumerate(proofs):
                        row = connection.execute("SELECT doi,request_url,http_status,response_headers FROM citation_neighbor_attempts WHERE id=?", (proof,)).fetchone()
                        if not row or row[0] != alias or row[2] not in (301,302,303,307,308):
                            raise ValueError('missing redirect response')
                        if redirect_target(row[1]) != chain[index] or redirect_target(header(json.loads(row[3]), 'Location')) != chain[index+1]:
                            raise ValueError('redirect identity chain differs')
                    supported = True
                    break
                except (ValueError, TypeError, KeyError, AttributeError):
                    continue
        if not supported:
            bad.append({'alias': alias, 'paper': paper, 'canonical_doi': target})
    return {'status': 'passed' if not bad else 'failed', 'doi_aliases': len(aliases), 'verified_aliases': len(aliases)-len(bad), 'unsupported_aliases': bad, 'interpretation': 'Identity proof only. An actual supplied reference and two accepted endpoints are still required for a graph edge.'}


def main():
    c = sqlite3.connect(atlas.DB.as_uri()+'?mode=ro', uri=True)
    c.execute('BEGIN')
    result = audit(c)
    c.close()
    (atlas.ROOT/'data/doi_alias_audit.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
    if result['status'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
