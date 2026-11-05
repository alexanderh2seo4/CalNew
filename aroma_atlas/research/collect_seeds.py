import concurrent.futures,json,urllib.request,urllib.parse,time,pathlib
out=pathlib.Path(__file__).parent
queries=[
 ('DREAM','TITLE:"Predicting human olfactory perception from chemical features of odor molecules"',['intensity','prediction']),
 ('POM','TITLE:"A principal odor map unifies diverse tasks"',['prediction','database']),
 ('Pyrfume','TITLE:"Pyrfume"',['database','prediction','intensity']),
 ('FlavorDB','TITLE:"FlavorDB: a database of flavor molecules"',['database']),
 ('AromaDb','TITLE:"AromaDb"',['database','pharmacology']),
 ('SuperScent','TITLE:"SuperScent"',['database']),
 ('OlfactionBase','TITLE:"OlfactionBase"',['database','receptor']),
 ('EssOilDB','TITLE:"EssOilDB"',['database']),
 ('PharmaGNN','TITLE:"PharmaGNN"',['prediction','pharmacophore']),
 ('DeepLearningBlends','TITLE:"Deep Learning for Odor Prediction on Aroma-Chemical Blends"',['prediction','mixtures']),
 ('ChemicalFeatureMining','TITLE:"Chemical features mining provides new descriptive structure-odor relationships"',['prediction','pharmacophore']),
 ('AIReceptors','TITLE:"Application of artificial intelligence to decode the relationships between smell"',['prediction','receptor']),
 ('StructureOdorSimilarity','TITLE:"Predicting odor perceptual similarity from odor structure"',['prediction']),
 ('OdorPleasantness','TITLE:"Predicting odor pleasantness from odorant structure"',['prediction']),
 ('OlfactorySpace','TITLE:"Olfactory perceptual space"',['intensity','prediction']),
 ('OdorIntensityAbraham','AUTH_LAST:Abraham AND ("odor" OR "odour") AND ("threshold" OR "intensity")',['intensity']),
 ('OdorReceptorStructure','TITLE:"Structural basis of odorant recognition by a human odorant receptor"',['receptor','pharmacophore']),
 ('OpenPOM','"OpenPOM"',['prediction','software']),
 ('OdorantReceptorDatabase','TITLE:"HORDE"',['database','receptor']),
 ('OdorDB','TITLE:"OdorDB"',['database','receptor']),
]
def get(q):
 label,query,tags=q
 url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode({'query':query,'format':'json','pageSize':6,'resultType':'core'})
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'AromaLiteratureAtlas/1.0'})
  d=json.load(urllib.request.urlopen(req,timeout=50)); records=[]
  for x in d.get('resultList',{}).get('result',[]):
   records.append({'seed_group':label,'title':x.get('title'),'doi':x.get('doi'),'pmid':x.get('pmid'),'pmcid':x.get('pmcid'),'year':x.get('pubYear'),'authors':x.get('authorString'),'europepmc_source':x.get('source'),'europepmc_id':x.get('id'),'cited_by_count_europepmc':x.get('citedByCount'),'tags':tags,'source_url':f"https://europepmc.org/article/{x.get('source')}/{x.get('id')}",'query_url':url,'abstract_available':bool(x.get('abstractText'))})
  return {'label':label,'query':query,'hits':d.get('hitCount'),'records':records}
 except Exception as e:return {'label':label,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(get,queries))
(out/'seed_search_results.json').write_text(json.dumps(results,indent=2))
seen=set();seeds=[]
for g in results:
 for x in g.get('records',[]):
  k=x.get('doi') or x['source_url']
  if k not in seen:seeds.append(x);seen.add(k)
(out/'verified_seeds.json').write_text(json.dumps({'retrieved_at':'2026-10-26','note':'API-verified metadata. Query results include secondary matches; tags are discovery hints, not manual relevance certification. Individual citation counts are Europe PMC counts, not total global counts.','papers':seeds},indent=2))
for g in results:print(g['label'],g.get('hits',g.get('error')),[(r['doi'],r['title'][:90]) for r in g.get('records',[])])
print('Saved',len(seeds),'unique papers')
