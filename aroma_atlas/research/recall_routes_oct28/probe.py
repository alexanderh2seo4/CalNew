import requests,time,json,pathlib,datetime
p=pathlib.Path(__file__).parent
jobs=[('crossref_docs_retry','https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-for-using-the-crossref-rest-api/',None),('epmc_docs','https://europepmc.org/RestfulWebService',None),('crossref_scent','https://api.crossref.org/works',{'query.title':'scent','rows':50,'filter':'until-pub-date:2026-10-26,type:journal-article'}),('crossref_musk','https://api.crossref.org/works',{'query.title':'musks','rows':50,'filter':'until-pub-date:2026-10-26,type:journal-article'}),('epmc_floral','https://www.ebi.ac.uk/europepmc/webservices/rest/search',{'query':'(TITLE:"floral scent" OR TITLE:"flower scent") AND (TITLE_ABS:compound OR TITLE_ABS:composition OR TITLE_ABS:chemical OR TITLE_ABS:volatile) AND FIRST_PDATE:[1800-01-01 TO 2026-10-26]','format':'json','resultType':'core','pageSize':25}),('epmc_receptor','https://www.ebi.ac.uk/europepmc/webservices/rest/search',{'query':'TITLE:receptor AND (TITLE_ABS:muscone OR TITLE_ABS:galaxolide OR TITLE_ABS:ionone) AND (TITLE_ABS:anosmia OR TITLE_ABS:"olfactory bulb") AND FIRST_PDATE:[1800-01-01 TO 2026-10-26]','format':'json','resultType':'core','pageSize':25})]
log=json.loads((p/'requests.json').read_text());session=requests.Session();session.headers['User-Agent']='AromaResearchAtlas/1.0 read-only recall audit'
for name,url,params in jobs:
 if log:time.sleep(1.6)
 r=session.get(url,params=params,timeout=50)
 (p/(name+'.raw')).write_bytes(r.content)
 entry={'name':name,'url':r.url,'status':r.status_code,'headers':dict(r.headers),'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bytes':len(r.content)};log.append(entry);(p/'requests.json').write_text(json.dumps(log,indent=2))
 print(name,r.status_code,len(r.content),flush=True)
 if r.status_code==429 or r.status_code in [401,403,502,503,504]:break
 if name.endswith('docs') and r.status_code!=200:break
