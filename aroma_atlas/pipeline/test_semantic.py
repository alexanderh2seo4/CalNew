"""Semantic Scholar metadata/reference provenance integrity regressions."""
import pathlib,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import atlas,semantic
class SemanticIntegrity(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.old=atlas.DB;atlas.DB=pathlib.Path(self.tmp.name)/'atlas.sqlite';semantic.init()
 def tearDown(self):atlas.DB=self.old;self.tmp.cleanup()
 def p(self,sid,doi):return {'paperId':sid,'externalIds':{'DOI':doi},'title':'Predicting odor intensity of aroma molecules','abstract':'Aroma chemical intensity is predicted.','year':2020,'publicationDate':'2020-02-02','publicationTypes':['JournalArticle']}
 def test_metadata_without_refs_stays_pending(self):
  semantic.ingest([self.p('abc','10.example/a')],'test');c=atlas.connect();self.assertEqual(c.execute('SELECT count(*) FROM refs').fetchone()[0],0);self.assertEqual(c.execute('SELECT count(*) FROM edges').fetchone()[0],0);c.close()
 def test_real_refs_resolve_provider_and_preserve_epmc_record(self):
  atlas.ingest([{'id':'123','pmid':'123','source':'MED','doi':'10.example/a','title':'Predicting odor intensity of aroma molecules','abstractText':'Enriched Europe PMC aroma molecule intensity abstract','pubYear':'2020'}],'test')
  semantic.ingest([self.p('abc','10.example/a'),self.p('def','10.example/b')],'test');semantic.save_refs([{'paperId':'abc','referenceCount':1,'references':[{'paperId':'def','externalIds':{'DOI':'10.example/b'},'title':'Predicting odor intensity of aroma molecules'}]}])
  c=atlas.connect();self.assertEqual(c.execute("SELECT source,abstract FROM papers WHERE id='pmid:123'").fetchone(),('MED','Enriched Europe PMC aroma molecule intensity abstract'));self.assertEqual(c.execute('SELECT source,target,provider FROM edges').fetchall(),[('pmid:123','doi:10.example/b','Semantic Scholar reference list')]);c.close()
 def test_persistent_throttle_stops_after_two_responses(self):
  class Response:status_code=429;headers={}
  client=semantic.Client(40);client.session.get=lambda *a,**k:Response()
  with patch.object(semantic.time,'sleep'):
   with self.assertRaises(semantic.LimitReached):client.request('/paper/search/bulk')
  self.assertEqual(client.used,2)
 def test_parent_physical_title_without_abstract_preserves_scope_and_provider_gates(self):
  for title,expected in [('Identification of volatile flavor compounds in coffee',True),('Non-volatile flavor compounds causing bitterness',False),('Flavor physics of quark mixing',False),('Vapor pressure of linalool',True),('Solubility of caffeine in limonene',False),('Partitioning of linalool oxide derivatives',False),('Effect of menthol as solid cosolvent on the solubility enhancement of clozapine',False),('Linalool as precursor to synthesis epoxides as anti carcinogenic agents',False),('Toxicity of linalool against stored product insects',False),('Conjugated addition of thiols to citral: preparation of potential antimicrobial agents',False),('Fumigant toxicity of linalool on Tribolium confusum',False)]:
   p=self.p('abc','10.example/a');p.update(title=title,abstract=None)
   self.assertEqual(semantic.classify(p)[0],expected,title)
  p=self.p('abc','10.example/a');p.update(title=title,abstract=None)
  p['title']='Vapor pressure of linalool'
  p['publicationTypes']=['Book'];self.assertFalse(semantic.classify(p)[0]);p['publicationTypes']=['JournalArticle'];p['publicationDate']='2027-01-01';self.assertFalse(semantic.classify(p)[0])
if __name__=='__main__':unittest.main()
