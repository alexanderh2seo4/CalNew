"""Data-integrity regressions for supplemental provider ingestion."""
import importlib.util,json,pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import atlas,supplement
from unittest.mock import patch
class SupplementIntegrity(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old_db=atlas.DB;atlas.DB=pathlib.Path(self.tmp.name)/'atlas.sqlite';supplement.init()
 def tearDown(self):atlas.DB=self.old_db;self.tmp.cleanup()
 def paper(self,doi='10.example/aroma',title='Predicting aroma intensity of fragrance molecules',**more):
  return {'DOI':doi,'title':[title],'type':'journal-article','published':{'date-parts':[[2020,1,2]]},'abstract':'Aroma molecules were assessed for odor intensity.',**more}
 def test_reuses_doi_and_preserves_enriched_epmc_metadata(self):
  atlas.ingest([{'id':'1234','source':'MED','pmid':'1234','doi':'10.example/aroma','title':'Predicting aroma intensity of fragrance molecules','abstractText':'Extensive enriched Europe PMC aroma molecule abstract','pubYear':'2020'}],'test')
  supplement.ingest([self.paper(reference=[{'DOI':'10.example/target'}])],'aroma')
  c=atlas.connect();rows=c.execute('SELECT id,abstract,source FROM papers').fetchall();self.assertEqual(rows,[('pmid:1234','Extensive enriched Europe PMC aroma molecule abstract','MED')]);self.assertEqual(c.execute('SELECT target_source,doi FROM raw_refs').fetchall(),[('Crossref','10.example/target')]);c.close()
 def test_provider_edges_have_real_deposited_doi_and_accepted_endpoints(self):
  supplement.ingest([self.paper('10.example/source',reference=[{'DOI':'10.example/target'},{'unstructured':'Unresolved reference'}]),self.paper('10.example/target')],'aroma');supplement.resolve()
  c=atlas.connect();edges=c.execute('SELECT * FROM edges').fetchall();self.assertEqual(edges,[('doi:10.example/source','doi:10.example/target','Crossref deposited reference list')]);c.close()
 def test_rejects_future_or_unrelated_aromatic_records(self):
  future=self.paper(published={'date-parts':[[2027,1,1]]});self.assertFalse(supplement.classify_record(future)[0])
  unrelated=self.paper(title='Prediction of aromatic molecules for cancer drugs',abstract='Aromatic compounds were used in molecular prediction software.');self.assertFalse(supplement.classify_record(unrelated)[0])
 def test_persistent_throttle_stops_after_two_responses(self):
  class Response:status_code=429;headers={}
  client=supplement.Client(30);client.session.get=lambda *a,**k:Response()
  with patch.object(supplement.time,'sleep'):
   with self.assertRaises(supplement.PersistentThrottle):client.get({})
  self.assertEqual(client.count,2)
 def test_parent_physical_title_without_abstract_preserves_scope_and_provider_gates(self):
  for title,expected in [('Identification of volatile flavor compounds in coffee',True),('Non-volatile flavor compounds causing bitterness',False),('Flavor physics of quark mixing',False),('Vapor pressure of linalool',True),('Solubility of caffeine in limonene',False),('Partitioning of linalool oxide derivatives',False),('Effect of menthol as solid cosolvent on the solubility enhancement of clozapine',False),('Linalool as precursor to synthesis epoxides as anti carcinogenic agents',False),('Toxicity of linalool against stored product insects',False),('Conjugated addition of thiols to citral: preparation of potential antimicrobial agents',False),('Fumigant toxicity of linalool on Tribolium confusum',False)]:
   p=self.paper(title=title,abstract='')
   self.assertEqual(supplement.classify_record(p)[0],expected,title)
  p=self.paper(title=title,abstract='')
  p['title']='Vapor pressure of linalool'
  p['type']='book';self.assertFalse(supplement.classify_record(p)[0]);p['type']='journal-article';p['published']={'date-parts':[[2027,1,1]]};self.assertFalse(supplement.classify_record(p)[0])
if __name__=='__main__':unittest.main()
