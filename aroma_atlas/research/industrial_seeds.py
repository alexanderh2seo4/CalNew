import json,pathlib,urllib.request,urllib.parse,time
out=pathlib.Path(__file__).parent
entries=[
('10.1002/ejoc.200300174',['pharmacophore','intensity','marine']),
('10.2533/chimia.2020.247',['pharmacophore','rose']),
('10.1002/ejoc.201501338',['pharmacophore','musk']),
('10.1002/hlca.202300040',['pharmacophore','muguet']),
('10.1371/journal.pone.0182147',['pharmacophore','receptor','muguet']),
('10.1002/hlca.201800048',['pharmacophore','marine','muguet']),
('10.1002/anie.202005719',['fragrance','review']),
('10.1021/cr950068a',['pharmacophore','review']),
('10.1093/chemse/bjr094',['intensity','threshold','prediction']),
('10.1093/chemse/27.2.95',['intensity','threshold','prediction']),
('10.1111/1541-4337.70533',['intensity','threshold','review']),
('10.1055/s-0037-1610199',['pharmacophore','rose']),
('10.1016/j.compchemeng.2018.04.018',['prediction','software']),
('10.1093/gigascience/giaa011',['prediction']),
('10.1002/hlca.200790126',['pharmacophore','marine']),
('10.1002/cbdv.200890083',['pharmacophore','marine']),
('10.1002/ejoc.201403142',['pharmacophore','marine']),
]
records=[]
for doi,tags in entries:
 try:
  req=urllib.request.Request('https://api.crossref.org/works/'+urllib.parse.quote(doi,safe=''),headers={'User-Agent':'AromaLiteratureAtlas/1.0'})
  x=json.load(urllib.request.urlopen(req,timeout=40))['message']
  y=x.get('published',x.get('issued',{})).get('date-parts',[[None]])[0][0]
  records.append({'doi':doi,'title':x.get('title',[''])[0],'year':y,'tags':tags,'source_url':'https://doi.org/'+doi,'metadata_source':'Crossref REST exact DOI','reference_count':x.get('reference-count'),'cited_by_count_crossref':x.get('is-referenced-by-count'),'references':x.get('reference',[])})
  print(doi,records[-1]['title'][:100],flush=True)
 except Exception as e:print('ERROR',doi,str(e),flush=True)
 time.sleep(1.1)
(out/'industrial_seed_metadata.json').write_text(json.dumps(records,indent=2))
p=out/'verified_seeds.json';d=json.loads(p.read_text());seen={x.get('doi') for x in d['papers']}
for x in records:
 if x['doi'] not in seen:d['papers'].append({k:v for k,v in x.items() if k!='references'})
p.write_text(json.dumps(d,indent=2))
print('Saved',len(records),'industrial metadata records,',len(d['papers']),'total seeds')
