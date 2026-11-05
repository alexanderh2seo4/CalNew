import requests,time,json,pathlib,datetime
p=pathlib.Path(__file__).parent;log=json.loads((p/'requests.json').read_text());session=requests.Session();session.headers['User-Agent']='AromaResearchAtlas/1.0 read-only recall audit'
for name,term in [('crossref_scent','scent'),('crossref_musk','musks')]:
 time.sleep(1.6)
 r=session.get('https://api.crossref.org/works',params={'query.title':term,'rows':50,'filter':'until-pub-date:2026-10-26,type:journal-article'},timeout=50)
 (p/(name+'.raw')).write_bytes(r.content)
 log.append({'name':name,'url':r.url,'status':r.status_code,'headers':dict(r.headers),'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bytes':len(r.content)});(p/'requests.json').write_text(json.dumps(log,indent=2));print(name,r.status_code,len(r.content),flush=True)
 if r.status_code!=200:break
