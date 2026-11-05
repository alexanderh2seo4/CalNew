"""Offline checks that a stored DOI alias has real, consistent redirect evidence."""
import json
import sqlite3
import unittest
import audit_aliases


class AliasEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(':memory:')
        self.c.executescript('''
        CREATE TABLE papers(id TEXT,doi TEXT);
        CREATE TABLE source_alias(source TEXT,source_id TEXT,paper TEXT);
        CREATE TABLE citation_neighbor_attempts(id INTEGER,doi TEXT,request_url TEXT,http_status INTEGER,response_headers TEXT,response_body TEXT,screening TEXT,outcome TEXT);
        ''')
        self.c.execute('INSERT INTO papers VALUES(?,?)', ('paper', '10.1234/new'))
        self.c.execute('INSERT INTO source_alias VALUES(?,?,?)', ('DOI', '10.1234/old', 'paper'))
        self.c.execute('INSERT INTO citation_neighbor_attempts VALUES(?,?,?,?,?,?,?,?)', (1,'10.1234/old','https://api.crossref.org/works/10.1234%2Fold',301,json.dumps({'Location':'/works/10.1234/new'}),'','{}','redirect'))
        self.c.execute('INSERT INTO citation_neighbor_attempts VALUES(?,?,?,?,?,?,?,?)', (2,'10.1234/old','https://api.crossref.org/works/10.1234%2Fnew',200,'{}',json.dumps({'status':'ok','message':{'DOI':'10.1234/new'}}),json.dumps({'redirect_chain':['10.1234/old','10.1234/new'],'redirect_proof_attempts':[1]}),'accepted'))
        self.c.commit()

    def tearDown(self):
        self.c.close()

    def test_complete_provider_chain_supports_alias(self):
        self.assertEqual(audit_aliases.audit(self.c)['verified_aliases'], 1)

    def test_missing_or_changed_redirect_proof_fails(self):
        for sql in ["DELETE FROM citation_neighbor_attempts WHERE id=1", "UPDATE citation_neighbor_attempts SET response_headers='{\"Location\":\"https://example.com/works/10.1234/new\"}' WHERE id=1", "UPDATE citation_neighbor_attempts SET request_url='https://api.crossref.org/works/10.1234/other' WHERE id=1"]:
            with self.subTest(sql=sql):
                self.c.execute(sql)
                self.assertEqual(audit_aliases.audit(self.c)['status'], 'failed')
                self.c.rollback()

    def test_final_metadata_must_match_canonical_paper(self):
        self.c.execute('UPDATE citation_neighbor_attempts SET response_body=? WHERE id=2', (json.dumps({'status':'ok','message':{'DOI':'10.1234/wrong'}}),))
        self.assertEqual(audit_aliases.audit(self.c)['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
