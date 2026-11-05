"""Offline identity-proof checks; all database mutations are in-memory fixtures."""
import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import bibliographic_identity as identity


class BibliographicIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.c = sqlite3.connect(':memory:')
        self.c.executescript('''
        CREATE TABLE papers(id TEXT PRIMARY KEY, title TEXT, authors TEXT, year INTEGER,
          journal TEXT, abstract TEXT, doi TEXT, pmid TEXT, source TEXT, source_id TEXT,
          raw TEXT, accepted INTEGER, evidence TEXT);
        CREATE TABLE source_alias(source TEXT, source_id TEXT, paper TEXT,
          PRIMARY KEY(source,source_id));
        ''')
        abstract = 'A named aroma molecule was measured by chemical and sensory assays. ' * 6
        self.left = {'id': 'AGR:one', 'title': 'Chemical thresholds of a named odorant',
            'authors': 'Smith A, Jones B.', 'year': 2025, 'journal': 'Chemistry Journal.',
            'abstract': abstract, 'doi': '', 'pmid': '', 'source': 'AGR', 'source_id': 'one',
            'raw': json.dumps({'id': 'one', 'source': 'AGR', 'journalInfo':
                {'volume': '12', 'journal': {'title': 'Chemistry Journal', 'issn': '1234-5678'}}}),
            'accepted': 1, 'evidence': 'original screen'}
        self.right = dict(self.left, id='pmid:two', title=self.left['title']+'.',
            source='MED', source_id='two', pmid='two', doi='10.1234/odorant',
            raw=json.dumps({'id': 'two', 'source': 'MED', 'journalInfo':
                {'volume': '12', 'journal': {'title': 'Chemistry Journal', 'issn': '1234-5678'}}}))

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def prepare(self, mode='strict', left=None, right=None):
        left, right = copy.deepcopy(left or self.left), copy.deepcopy(right or self.right)
        audit = {'very_high_confidence_duplicates': [],
            'standard_rendering_equivalence_cohort': {'pairs': []},
            'strict_or_standard_rendering_union': {'pair_count': 1}}
        record = {'left': left, 'right': right}
        if mode == 'strict':
            audit['very_high_confidence_duplicates'].append(record)
        else:
            audit['standard_rendering_equivalence_cohort']['pairs'].append(record)
        payload = json.dumps(audit).encode()
        (self.path/'audit.json').write_bytes(payload)
        manifest = identity.manifest_from_audit(audit, 'audit.json', identity.digest(payload))
        (self.path/'manifest.json').write_text(json.dumps(manifest))
        for row in (left, right):
            self.c.execute('INSERT INTO papers ('+','.join(row)+') VALUES ('+
                           ','.join('?' for _ in row)+')', tuple(row.values()))
            self.c.execute('INSERT INTO source_alias VALUES (?,?,?)',
                           (row['source'], row['source_id'], row['id']))
        self.c.commit()
        return self.path/'manifest.json'

    def test_exact_pair_is_read_only_and_classification_independent(self):
        path = self.prepare()
        before = self.c.total_changes
        pairs = identity.validated_pairs(self.c, path)
        self.assertEqual([(a,b) for a,b,_ in pairs], [('AGR:one', 'pmid:two')])
        self.assertEqual(self.c.total_changes, before)
        self.c.execute("UPDATE papers SET accepted=0,evidence='rescreened'")
        self.assertEqual(len(identity.validated_pairs(self.c, path)), 1)

    def test_math_rendering_is_exact_but_scientific_changes_are_not(self):
        left, right = copy.deepcopy(self.left), copy.deepcopy(self.right)
        left['abstract'] += 'Prediction R²ₚ = 0.909.'
        right['abstract'] += 'Prediction R 2 p = 0.909.'
        with self.assertRaises(identity.IdentityProofError):
            identity._proof(left, right, 'strict', {})
        path = self.prepare('standard-rendering', left, right)
        self.assertEqual(identity.validated_pairs(self.c, path)[0][2]['match_mode'], 'standard-rendering')
        right['abstract'] = right['abstract'].replace('0.909', '0.908')
        with self.assertRaises(identity.IdentityProofError):
            identity._proof(left, right, 'standard-rendering', {})

    def test_conflicting_doi_or_pmid_fails(self):
        path = self.prepare()
        for field, value in [('doi', '10.1234/different'), ('pmid', 'different')]:
            with self.subTest(field=field):
                self.c.execute('UPDATE papers SET '+field+'=? WHERE id=?', (value, 'AGR:one'))
                with self.assertRaises(identity.IdentityProofError):
                    identity.validated_pairs(self.c, path)
                self.c.rollback()

    def test_raw_metadata_changes_fail_even_if_title_still_matches(self):
        path = self.prepare()
        self.c.execute("UPDATE papers SET raw=json_set(raw,'$.new_source_field','changed') WHERE id='AGR:one'")
        with self.assertRaisesRegex(identity.IdentityProofError, 'stale AGR'):
            identity.validated_pairs(self.c, path)

    def test_existing_merge_is_idempotent_only_with_unchanged_alias_and_keep(self):
        path = self.prepare()
        self.c.execute("DELETE FROM papers WHERE id='AGR:one'")
        self.c.execute("UPDATE source_alias SET paper='pmid:two' WHERE source='AGR'")
        self.assertEqual(identity.validated_pairs(self.c, path), [])
        self.c.execute("UPDATE source_alias SET paper='unrelated' WHERE source='AGR'")
        with self.assertRaises(identity.IdentityProofError):
            identity.validated_pairs(self.c, path)
        self.c.execute("UPDATE source_alias SET paper='pmid:two' WHERE source='AGR'")
        self.c.execute("UPDATE papers SET abstract='changed' WHERE id='pmid:two'")
        self.assertEqual(identity.validated_pairs(self.c, path), [])
        self.c.execute("UPDATE papers SET pmid='different' WHERE id='pmid:two'")
        with self.assertRaises(identity.IdentityProofError):
            identity.validated_pairs(self.c, path)

    def test_no_preprint_or_title_only_identity(self):
        for modification in ('preprint', 'short-abstract', 'different-volume', 'different-journal'):
            with self.subTest(modification=modification):
                left, right = copy.deepcopy(self.left), copy.deepcopy(self.right)
                if modification == 'preprint':
                    right['source'] = 'PPR'
                elif modification == 'short-abstract':
                    left['abstract'] = right['abstract'] = 'Identical title alone is insufficient.'
                else:
                    raw = json.loads(right['raw'])
                    if modification == 'different-volume':
                        raw['journalInfo']['volume'] = '13'
                    else:
                        raw['journalInfo']['journal'] = {'title': 'Different Journal', 'issn': '9999-9999'}
                        right['journal'] = 'Different Journal'
                    right['raw'] = json.dumps(raw)
                with self.assertRaises(identity.IdentityProofError):
                    identity._proof(left, right, 'strict', {})

    def test_unlisted_similar_record_cannot_create_another_pair(self):
        path = self.prepare()
        extra = dict(self.left, id='AGR:unlisted', source_id='unlisted')
        self.c.execute('INSERT INTO papers ('+','.join(extra)+') VALUES ('+
                       ','.join('?' for _ in extra)+')', tuple(extra.values()))
        self.assertEqual(len(identity.validated_pairs(self.c, path)), 1)

    def test_audit_or_manifest_tampering_fails(self):
        path = self.prepare()
        payload = json.loads(path.read_text())
        payload['pairs'][0]['keep_id'] = 'unlisted'
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(identity.IdentityProofError, 'frozen enumerated'):
            identity.validated_pairs(self.c, path)
        (self.path/'audit.json').write_text('{}')
        with self.assertRaisesRegex(identity.IdentityProofError, 'audit hash'):
            identity.validated_pairs(self.c, path)


if __name__ == '__main__':
    unittest.main()
