import sqlite3
import unittest
import reference_coverage


class CoverageUnionTests(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(':memory:')
        self.c.executescript('''CREATE TABLE papers(id TEXT,doi TEXT);
        CREATE TABLE refs(paper TEXT,status TEXT,retrieved INTEGER,error TEXT);
        CREATE TABLE raw_refs(paper TEXT);
        CREATE TABLE source_alias(source TEXT,source_id TEXT,paper TEXT);
        CREATE TABLE crossref_responses(paper TEXT,doi TEXT,reference_count INTEGER,reference_rows INTEGER);
        CREATE TABLE openalex_ids(openalex_id TEXT,paper TEXT);
        CREATE TABLE openalex_refs(openalex_id TEXT,paper TEXT,total INTEGER);
        CREATE TABLE pmid_neighbor_records(paper TEXT,raw TEXT);
        ''')
        self.c.executemany('INSERT INTO papers VALUES(?,?)', [('a','10.1234/a'),('b','10.1234/b'),('c','10.1234/c')])

    def tearDown(self):
        self.c.close()

    def test_nonempty_secondary_provider_overrides_empty_primary_list(self):
        self.c.execute("INSERT INTO refs VALUES('a','complete',0,'')")
        self.c.execute("INSERT INTO crossref_responses VALUES('deleted-id','10.1234/a',30,30)")
        result = reference_coverage.collect(self.c)
        self.assertIn('a', result['available'])
        self.assertEqual(reference_coverage.status('a', result), 'complete')

    def test_exact_id_maps_survive_merges_and_metadata_is_not_a_list(self):
        self.c.execute("INSERT INTO openalex_ids VALUES('W1','b')")
        self.c.execute("INSERT INTO openalex_refs VALUES('W1','old-id',8)")
        self.c.execute("INSERT INTO pmid_neighbor_records VALUES('c','{\"hasReferences\":\"Y\"}')")
        self.c.execute("INSERT INTO crossref_responses VALUES('c','10.1234/c',500,0)")
        result = reference_coverage.collect(self.c)
        self.assertIn('b', result['available'])
        self.assertNotIn('c', result['available'])
        self.assertEqual(reference_coverage.status('c', result), 'no indexed references')

    def test_partial_rows_do_not_claim_complete_and_rejected_ids_stay_out(self):
        self.c.execute("INSERT INTO refs VALUES('a','error',0,'network')")
        self.c.executemany('INSERT INTO raw_refs VALUES(?)', [('a',),('b',)])
        result = reference_coverage.collect(self.c, {'a'})
        self.assertEqual(result['available'], {'a'})
        self.assertEqual(result['processed'], set())
        self.assertEqual(reference_coverage.status('a', result), 'error')


if __name__ == '__main__':
    unittest.main()
