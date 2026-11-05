"""Verified identity merging preserves citations without skipping native lookup."""
import json
from pathlib import Path
import tempfile
import unittest
import atlas


class MergeIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=atlas.DB
        atlas.DB=Path(self.tmp.name)/'atlas.sqlite';atlas.init()
        self.native={'id':'100','source':'MED','pmid':'100','doi':'10.1234/odor',
                     'title':'Aroma molecule intensity','abstractText':'Odor compounds were measured.',
                     'pubYear':'2020','hasReferences':'Y'}
        self.agricultural={**self.native,'id':'one','source':'AGR','pmid':'','doi':'','hasReferences':'N'}
        atlas.ingest([self.native,self.agricultural],'original')
        self.c=atlas.connect()
        self.c.execute('INSERT INTO source_alias SELECT source,source_id,id FROM papers')
        self.c.execute("INSERT INTO refs VALUES('AGR:one','complete',0,0,'original','Europe PMC metadata: hasReferences=N')")
        self.c.execute("INSERT INTO raw_refs VALUES('AGR:one','MED','200','','Actual cited title')")
        self.c.commit()

    def tearDown(self):
        self.c.close();atlas.DB=self.old;self.tmp.cleanup()

    def test_cross_index_no_reference_flag_does_not_complete_med_lookup(self):
        merges={};atlas.merge_identity(self.c,'AGR:one','pmid:100',merges);self.c.commit()
        self.assertIsNone(self.c.execute("SELECT status FROM refs WHERE paper='pmid:100'").fetchone())
        self.assertEqual(self.c.execute("SELECT target_id FROM raw_refs WHERE paper='pmid:100'").fetchone()[0],'200')
        self.assertEqual(self.c.execute("SELECT paper FROM source_alias WHERE source='AGR' AND source_id='one'").fetchone()[0],'pmid:100')
        archived=json.loads(self.c.execute('SELECT refs_row FROM identity_reference_archive').fetchone()[0])
        self.assertEqual(archived[:4],['AGR:one','complete',0,0])

    def test_existing_native_checkpoint_is_preserved_and_old_alias_not_reinserted(self):
        self.c.execute("INSERT INTO refs VALUES('pmid:100','complete',5,5,'native','')")
        atlas.merge_identity(self.c,'AGR:one','pmid:100',{});self.c.commit()
        atlas.ingest([self.agricultural],'later-exact-alias-query')
        self.assertEqual(self.c.execute('SELECT count(*) FROM papers').fetchone()[0],1)
        self.assertEqual(self.c.execute("SELECT retrieved FROM refs WHERE paper='pmid:100'").fetchone()[0],5)
        self.assertEqual(self.c.execute("SELECT paper FROM provenance WHERE query='later-exact-alias-query'").fetchone()[0],'pmid:100')


    def test_native_rescreen_keeps_secondary_doi_and_journal_exclusions(self):
        from unittest.mock import patch
        records=[{**self.native,'pmid':'300','id':'300','doi':'10.1002/chin.example'},
                 {**self.native,'pmid':'301','id':'301','doi':'10.1234/secondary',
                  'journalInfo':{'journal':{'title':'ChemInform'}}}]
        atlas.ingest(records,'secondary-fixture')
        self.c.execute("UPDATE papers SET accepted=1 WHERE pmid IN ('300','301')")
        self.c.commit()
        root=Path(self.tmp.name);(root/'data').mkdir(exist_ok=True)
        with patch.object(atlas,'ROOT',root), patch.object(atlas,'identity_paths',return_value=[root/'absent.json']):
            atlas.rescreen()
        self.assertEqual(self.c.execute("SELECT sum(accepted) FROM papers WHERE pmid IN ('300','301')").fetchone()[0],0)
        self.assertEqual(self.c.execute("SELECT accepted FROM papers WHERE pmid='100'").fetchone()[0],1)


if __name__=='__main__':unittest.main()
