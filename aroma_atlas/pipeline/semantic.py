#!/usr/bin/env python3
"""Bounded/resumable no-key Semantic Scholar metadata discovery and optional real refs.
Bulk endpoint does NOT expose nested references; missing references remain unknown.
"""
import argparse,json,re,time
from pathlib import Path
import requests
import atlas
ROOT=Path(__file__).resolve().parents[1];BASE='https://api.semanticscholar.org/graph/v1'
QUERIES={'aroma_union':'"aroma" | "fragrance" | "odorant" | "olfactophore"'}
FIELDS='title,abstract,year,citationCount,referenceCount,externalIds,publicationDate,authors,venue,publicationTypes'
class LimitReached(RuntimeError):pass
def log(**d):print(json.dumps({'time':atlas.now(),**d}),flush=True)
def init():
 atlas.init();c=atlas.connect();c.executescript('''
 CREATE TABLE IF NOT EXISTS semantic_queries(name TEXT PRIMARY KEY,query TEXT,token TEXT,hits INTEGER,seen INTEGER,complete INTEGER,updated TEXT,error TEXT);
 CREATE TABLE IF NOT EXISTS semantic_ids(semantic_id TEXT PRIMARY KEY,paper TEXT);
 CREATE TABLE IF NOT EXISTS semantic_refs(semantic_id TEXT PRIMARY KEY,paper TEXT,status TEXT,total INTEGER,retrieved INTEGER,updated TEXT,error TEXT);
 ''');c.commit();c.close()
def doi(s):return re.sub(r'^https?://(?:dx\.)?doi\.org/','',s or '',flags=re.I).strip().lower()
def classify(p):
 title=atlas.clean(p.get('title'));ab=atlas.clean(p.get('abstract'));ok,cat,tracks,evidence=atlas.classify(title,ab)
 if atlas.secondary_abstract(title,(p.get('externalIds') or {}).get('DOI',''),p.get('venue','')):ok=False;evidence.append('secondary abstracting record')
 when=p.get('publicationDate') or (str(p.get('year'))+'-01-01' if p.get('year') else '')
 if not when or when>atlas.CUTOFF:ok=False;evidence.append('missing or out-of-window publication date')
 types=p.get('publicationTypes') or []
 if set(types)&{'Book','BookSection','News','Editorial','LettersAndComments','Dataset'} and not set(types)&{'JournalArticle','Conference','Review','Study'}:ok=False;evidence.append('excluded Semantic Scholar publication type')
 if not ab and ok:
  mt={k:bool(r.search(title)) for k,r in atlas.RX.items()}
  if not ((mt['aroma'] or mt['odor'] or mt['resource']) and (mt['chem'] or mt['potency'] or mt['prediction'] or mt['resource'])) and not atlas.self_contained_parent_title(title) and not atlas.self_contained_flavor_title(title) and not atlas.scent_chemistry(title):
   ok=False;evidence.append('missing abstract and ambiguous title')
 evidence.append('Semantic Scholar title/abstract automatic screening')
 return ok,cat,tracks,evidence,title,ab

def ingest(rows,name):
 c=atlas.connect();counts={'returned':len(rows),'new':0,'accepted_new':0,'reused':0}
 for p in rows:
  sid=p.get('paperId')
  if not sid:continue
  ext=p.get('externalIds') or {};pd=doi(ext.get('DOI'));pmid=str(ext.get('PubMed') or '')
  old=c.execute('SELECT id FROM papers WHERE doi=? AND doi!=? ORDER BY accepted DESC LIMIT 1',(pd,'')).fetchone() if pd else None
  if not old and pmid:old=c.execute('SELECT id FROM papers WHERE pmid=? ORDER BY accepted DESC LIMIT 1',(pmid,)).fetchone()
  if not old:old=c.execute('SELECT paper FROM semantic_ids WHERE semantic_id=?',(sid,)).fetchone()
  pid=old[0] if old else 'pmid:'+pmid if pmid else 'doi:'+pd if pd else 's2:'+sid
  if not old:
   ok,cat,tracks,evidence,title,ab=classify(p)
   c.execute('INSERT OR IGNORE INTO papers VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(pid,pd,title,int(p.get('year') or 0),'; '.join(a.get('name','') for a in p.get('authors') or []),p.get('venue') or '',ab,int(p.get('citationCount') or 0),pmid,ext.get('PubMedCentral',''),'SemanticScholar',sid,cat,json.dumps(tracks),json.dumps(evidence),int(ok),json.dumps(p,separators=(',',':'))))
   counts['new']+=1;counts['accepted_new']+=int(ok)
  else:counts['reused']+=1
  c.execute('INSERT OR REPLACE INTO semantic_ids VALUES(?,?)',(sid,pid));c.execute('INSERT OR IGNORE INTO provenance VALUES(?,?)',(pid,'semanticscholar:'+name))
 c.commit();c.close();return counts
class Client:
 def __init__(self,budget):self.budget=budget;self.used=0;self.last=0;self.session=requests.Session();self.session.headers['User-Agent']='AromaResearchAtlas/1.0 (public scholarly metadata research)'
 def request(self,path,params=None,payload=None):
  ratefail=0
  for attempt in range(4):
   if self.used>=self.budget:raise LimitReached('request budget reached')
   time.sleep(max(0,1.2-(time.monotonic()-self.last)));self.last=time.monotonic();self.used+=1
   try:
    r=self.session.get(BASE+path,params=params,timeout=(20,120)) if payload is None else self.session.post(BASE+path,params=params,json=payload,timeout=(20,120))
   except requests.RequestException as e:
    if attempt==3:raise
    log(stage='retry',error=str(e)[:200]);time.sleep(min(40,2**(attempt+1)));continue
   if r.status_code==429:
    ratefail+=1
    if ratefail>=2:raise LimitReached('persistent public API throttling (two HTTP 429 responses); stop without further probes')
    try:delay=float(r.headers.get('Retry-After','10'))
    except ValueError:delay=10
    log(stage='rate_limit',delay=delay);time.sleep(min(60,max(2,delay)));continue
   if r.status_code in [500,502,503,504]:time.sleep(min(40,2**(attempt+1)));continue
   r.raise_for_status();return r.json()
  raise RuntimeError('retry limit')
def resolve():
 c=atlas.connect()
 c.execute("INSERT OR IGNORE INTO edges SELECT r.paper,p.id,'Semantic Scholar reference list' FROM raw_refs r JOIN semantic_ids s ON s.semantic_id=r.target_id JOIN papers p ON p.id=s.paper JOIN papers q ON q.id=r.paper WHERE r.target_source='SemanticScholar' AND p.accepted=1 AND q.accepted=1 AND r.paper!=p.id")
 c.execute("INSERT OR IGNORE INTO edges SELECT r.paper,p.id,'Semantic Scholar reference list' FROM raw_refs r JOIN papers p ON r.doi=p.doi JOIN papers q ON q.id=r.paper WHERE r.target_source='SemanticScholar' AND r.doi!='' AND p.accepted=1 AND q.accepted=1 AND r.paper!=p.id")
 c.commit();c.close()
def save_refs(rows):
 c=atlas.connect();saved=0
 for p in rows:
  if not p or 'references' not in p:continue
  sid=p.get('paperId');old=c.execute('SELECT paper FROM semantic_ids WHERE semantic_id=?',(sid,)).fetchone()
  if not old:continue
  pid=old[0];refs=p.get('references') or [];n=0
  for r in refs:
   rid=r.get('paperId');rd=doi((r.get('externalIds') or {}).get('DOI'))
   if not rid and not rd:continue
   c.execute('INSERT OR IGNORE INTO raw_refs VALUES(?,?,?,?,?)',(pid,'SemanticScholar',rid or 'doi:'+rd,rd,atlas.clean(r.get('title'))));n+=1
  c.execute('INSERT OR REPLACE INTO semantic_refs VALUES(?,?,?,?,?,?,?)',(sid,pid,'complete',int(p.get('referenceCount') or len(refs)),len(refs),atlas.now(),''));saved+=n
  source=c.execute('SELECT source FROM papers WHERE id=?',(pid,)).fetchone()
  if source and source[0]=='SemanticScholar':c.execute('INSERT OR REPLACE INTO refs VALUES(?,?,?,?,?,?)',(pid,'complete',int(p.get('referenceCount') or len(refs)),len(refs),atlas.now(),'Semantic Scholar returned references; provider coverage only'))
 c.commit();c.close();resolve();return saved

def report(client):
 c=atlas.connect();c.row_factory=__import__('sqlite3').Row
 d={'retrieved_at':atlas.now(),'cutoff':atlas.CUTOFF,'provider':'Semantic Scholar Academic Graph API','endpoint':BASE+'/paper/search/bulk','official_docs':'https://api.semanticscholar.org/api-docs/','fields':FIELDS,'requests_this_run':client.used,'query_states':[dict(r) for r in c.execute('SELECT * FROM semantic_queries')],'source_counts':[dict(r) for r in c.execute('SELECT source,accepted,count(*) n FROM papers GROUP BY source,accepted')],'semantic_ids':c.execute('SELECT count(*) FROM semantic_ids').fetchone()[0],'real_reference_responses':c.execute("SELECT count(*) FROM semantic_refs WHERE status='complete'").fetchone()[0],'raw_reference_rows':c.execute("SELECT count(*) FROM raw_refs WHERE target_source='SemanticScholar'").fetchone()[0],'resolved_edges':c.execute("SELECT count(*) FROM edges WHERE provider='Semantic Scholar reference list'").fetchone()[0],'limitations':['Bulk search exposes no nested references. Metadata-only discoveries retain pending reference coverage.','Total hits are estimated candidate counts, not relevant paper counts.','Bounded token-paginated search is not an exhaustive census. Existing DOI/PMID metadata is preserved.','No API keys/accounts/charges used. Stop after persistent public API throttling.']};c.close();(ROOT/'research/semantic_harvest_report.json').write_text(json.dumps(d,indent=2));log(stage='summary',requests=client.used,source_counts=d['source_counts'],semantic_ids=d['semantic_ids'],real_reference_responses=d['real_reference_responses'],raw_reference_rows=d['raw_reference_rows'],resolved_edges=d['resolved_edges'])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--max-requests',type=int,default=37);ap.add_argument('--bulk-requests',type=int,default=36);ap.add_argument('--reference-batches',type=int,default=1);ap.add_argument('--reference-batch-size',type=int,default=100);ap.add_argument('--cached-probe',action='store_true');a=ap.parse_args();init();client=Client(a.max_requests)
 try:
  for name,query in QUERIES.items():
   c=atlas.connect();old=c.execute('SELECT token,hits,seen,complete FROM semantic_queries WHERE name=?',(name,)).fetchone();c.close()
   if old and old[3]:continue
   token=old[0] if old else None;seen=old[2] if old else 0
   for i in range(a.bulk_requests):
    cached=ROOT/'research/semantic_bulk_probe_valid.json'
    if not old and i==0 and a.cached_probe and cached.exists():d=json.loads(cached.read_text())['data']
    else:
     params={'query':query,'fields':FIELDS,'publicationDateOrYear':'1800-01-01:'+atlas.CUTOFF}
     if token:params['token']=token
     d=client.request('/paper/search/bulk',params)
    rows=d.get('data',[]);counts=ingest(rows,name);seen+=len(rows);nxt=d.get('token');done=not rows or not nxt;c=atlas.connect();c.execute('INSERT OR REPLACE INTO semantic_queries VALUES(?,?,?,?,?,?,?,?)',(name,query,nxt or token,d.get('total',0),seen,int(done),atlas.now(),''));c.commit();c.close();resolve();log(stage='semantic_bulk',query=name,seen=seen,hits=d.get('total'),complete=done,requests=client.used,**counts)
    if done:break
    token=nxt
  for i in range(a.reference_batches):
   c=atlas.connect();pending=c.execute("SELECT s.semantic_id FROM semantic_ids s JOIN papers p ON p.id=s.paper LEFT JOIN refs r ON r.paper=p.id LEFT JOIN semantic_refs sr ON sr.semantic_id=s.semantic_id WHERE p.accepted=1 AND (r.status IS NULL OR r.status!='complete') AND sr.status IS NULL ORDER BY p.citations DESC LIMIT ?",(min(500,a.reference_batch_size),)).fetchall();c.close()
   if not pending:break
   d=client.request('/paper/batch',{'fields':'referenceCount,references.paperId,references.externalIds,references.title'}, {'ids':[x[0] for x in pending]});n=save_refs(d);log(stage='semantic_real_references',papers=len(pending),saved_rows=n,requests=client.used)
 except Exception as e:log(stage='stopped',reason=str(e))
 finally:resolve();report(client)
if __name__=='__main__':main()
