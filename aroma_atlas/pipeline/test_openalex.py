"""Provider-reference and budget-preservation regressions, no network calls."""
import pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import atlas,openalex
class OpenAlexIntegrity(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.old=atlas.DB;atlas.DB=pathlib.Path(self.tmp.name)/'atlas.sqlite';openalex.init()
 def tearDown(self):atlas.DB=self.old;self.tmp.cleanup()
 def paper(self,work,doi,refs=None):return {'id':'https://openalex.org/'+work,'doi':'https://doi.org/'+doi,'title':'Predicting aroma intensity of odorant molecules','publication_year':2020,'publication_date':'2020-02-01','type':'article','abstract_inverted_index':{'Aroma':[0],'chemical':[1],'intensity':[2]},'referenced_works':refs or []}
 def test_inverted_abstract_is_reconstructed(self):self.assertEqual(openalex.abstract(self.paper('W1','10.example/a')),'Aroma chemical intensity')
 def test_actual_work_ids_reuse_doi_and_resolve_provider_edges(self):
  atlas.ingest([{'id':'123','pmid':'123','source':'MED','doi':'10.example/a','title':'Predicting aroma intensity of odorant molecules','abstractText':'Preserve enriched aroma chemical abstract','pubYear':'2020'}],'test')
  openalex.ingest([self.paper('W1','10.example/a',['https://openalex.org/W2']),self.paper('W2','10.example/b')],'test');c=atlas.connect();self.assertEqual(c.execute("SELECT abstract,source FROM papers WHERE id='pmid:123'").fetchone(),('Preserve enriched aroma chemical abstract','MED'));self.assertEqual(c.execute('SELECT * FROM edges').fetchall(),[('pmid:123','doi:10.example/b','OpenAlex referenced_works')]);c.close()
 def test_budget_reserve_stops_before_network_request(self):
  client=openalex.Client(29,.06);client.remaining=.0605
  with self.assertRaises(openalex.StopHarvest):client.get({})
  self.assertEqual(client.used,0)
 def test_reserve_is_preserved_across_goal_turns_until_server_reset(self):
  c=atlas.connect();c.execute('INSERT INTO openalex_budget_checks VALUES(?,?,?,?)',(atlas.now(),.0605,.001,'{"X-RateLimit-Reset":"3600"}'));c.commit();c.close()
  client=openalex.Client(29,.06)
  with self.assertRaises(openalex.StopHarvest):client.get({})
  self.assertEqual(client.used,0)
 def test_source_type_and_cutoff_gates(self):
  p=self.paper('W1','10.example/a');p['type']='book';self.assertFalse(openalex.classify(p)[0]);p['type']='article';p['publication_date']='2027-01-01';self.assertFalse(openalex.classify(p)[0])
 def test_parent_physical_title_without_abstract_preserves_scope_and_provider_gates(self):
  for title,expected in [('Identification of volatile flavor compounds in coffee',True),('Non-volatile flavor compounds causing bitterness',False),('Flavor physics of quark mixing',False),('Vapor pressure of linalool',True),('Solubility of caffeine in limonene',False),('Partitioning of linalool oxide derivatives',False),('Effect of menthol as solid cosolvent on the solubility enhancement of clozapine',False),('Linalool as precursor to synthesis epoxides as anti carcinogenic agents',False),('Toxicity of linalool against stored product insects',False),('Conjugated addition of thiols to citral: preparation of potential antimicrobial agents',False),('Fumigant toxicity of linalool on Tribolium confusum',False)]:
   p=self.paper('W1','10.example/a');p.update(title=title,abstract_inverted_index=None)
   self.assertEqual(openalex.classify(p)[0],expected,title)
  p=self.paper('W1','10.example/a');p.update(title=title,abstract_inverted_index=None)
  p['title']='Vapor pressure of linalool'
  p['type']='book';self.assertFalse(openalex.classify(p)[0]);p['type']='article';p['publication_date']='2027-01-01';self.assertFalse(openalex.classify(p)[0])
if __name__=='__main__':unittest.main()
