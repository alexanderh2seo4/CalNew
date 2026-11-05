#!/usr/bin/env python3
"""Bounded keyless OpenAlex title discovery with free-budget reserve and real references.
No key signup, cursor pagination, prepaid budget, or invented references.
"""
import argparse,datetime as dt,json,re,sqlite3,time
from pathlib import Path
import requests
import atlas
ROOT=Path(__file__).resolve().parents[1];BASE='https://api.openalex.org/works'
QUERIES={'aroma':'aroma','fragrance':'fragrance','odorant':'odorant'}
FIELDS='id,doi,title,publication_year,abstract_inverted_index,referenced_works,authorships,primary_location,type,cited_by_count,ids,publication_date'
TYPES={'article','review','preprint','proceedings-article'}
class StopHarvest(RuntimeError):pass
def log(**d):print(json.dumps({'time':atlas.now(),**d}),flush=True)
def oid(s):return s if (s or '').startswith('https://openalex.org/') else 'https://openalex.org/'+(s or '').rsplit('/',1)[-1]
def doi(s):return re.sub(r'^https?://(?:dx\.)?doi\.org/','',s or '',flags=re.I).strip().lower()
def abstract(p):
 inv=p.get('abstract_inverted_index') or {};words={}
 for word,positions in inv.items():
  for n in positions:
   if isinstance(n,int) and 0<=n<100000:words[n]=word
 return atlas.clean(' '.join(words[i] for i in sorted(words)))
def init():
 atlas.init();c=atlas.connect();c.executescript('''
 CREATE TABLE IF NOT EXISTS openalex_queries(name TEXT PRIMARY KEY,query TEXT,next_page INTEGER,hits INTEGER,seen INTEGER,complete INTEGER,updated TEXT,error TEXT);
 CREATE TABLE IF NOT EXISTS openalex_ids(openalex_id TEXT PRIMARY KEY,paper TEXT);
 CREATE TABLE IF NOT EXISTS openalex_refs(openalex_id TEXT PRIMARY KEY,paper TEXT,total INTEGER,updated TEXT);
 CREATE TABLE IF NOT EXISTS openalex_budget_checks(time TEXT,remaining_usd REAL,cost_usd REAL,headers TEXT);
 ''');c.commit();c.close()
def classify(p):
 title=atlas.clean(p.get('title'));ab=abstract(p);ok,cat,tracks,ev=atlas.classify(title,ab)
 if atlas.secondary_abstract(title,p.get('doi','')):ok=False;ev.append('secondary abstracting record')
 if p.get('type') not in TYPES:ok=False;ev.append('excluded OpenAlex type '+str(p.get('type')))
 when=p.get('publication_date') or ''
 if not when or when>atlas.CUTOFF:ok=False;ev.append('missing or out-of-window OpenAlex publication date')
 if not ab and ok:
  mt={k:bool(r.search(title)) for k,r in atlas.RX.items()}
  if not ((mt['aroma'] or mt['odor'] or mt['resource']) and (mt['chem'] or mt['potency'] or mt['prediction'] or mt['resource'])) and not atlas.self_contained_parent_title(title) and not atlas.self_contained_flavor_title(title) and not atlas.scent_chemistry(title):
   ok=False;ev.append('missing abstract and ambiguous title')
 ev.append('OpenAlex title/abstract automatic screening')
 return ok,cat,tracks,ev,title,ab

def ingest(rows,name):
 c=atlas.connect();stats={'returned':len(rows),'new':0,'accepted_new':0,'reused':0,'reference_rows':0}
 for p in rows:
  if not p.get('id'):continue
  sid=oid(p['id']);pd=doi(p.get('doi'));ids=p.get('ids') or {};pmid=(ids.get('pmid') or '').rstrip('/').rsplit('/',1)[-1]
  old=c.execute("SELECT id FROM papers WHERE doi=? AND doi!='' ORDER BY accepted DESC LIMIT 1",(pd,)).fetchone() if pd else None
  if not old and pmid:old=c.execute('SELECT id FROM papers WHERE pmid=? ORDER BY accepted DESC LIMIT 1',(pmid,)).fetchone()
  if not old:old=c.execute('SELECT paper FROM openalex_ids WHERE openalex_id=?',(sid,)).fetchone()
  pid=old[0] if old else 'pmid:'+pmid if pmid else 'doi:'+pd if pd else 'openalex:'+sid.rsplit('/',1)[-1]
  if not old:
   ok,cat,tracks,ev,title,ab=classify(p);authors='; '.join((x.get('author') or {}).get('display_name','') for x in p.get('authorships') or []);journal=((p.get('primary_location') or {}).get('source') or {}).get('display_name','')
   c.execute('INSERT OR IGNORE INTO papers VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(pid,pd,title,int(p.get('publication_year') or 0),authors,journal,ab,int(p.get('cited_by_count') or 0),pmid,ids.get('pmcid',''),'OpenAlex',sid,cat,json.dumps(tracks),json.dumps(ev),int(ok),json.dumps(p,separators=(',',':'))));stats['new']+=1;stats['accepted_new']+=int(ok)
  else:stats['reused']+=1
  c.execute('INSERT OR REPLACE INTO openalex_ids VALUES(?,?)',(sid,pid));c.execute('INSERT OR IGNORE INTO provenance VALUES(?,?)',(pid,'openalex:title.search:'+name))
  # referenced_works are actual OpenAlex IDs; no content-based or inferred citation links.
  refs=p.get('referenced_works')
  if isinstance(refs,list):
   for target in refs:
    if target and oid(target)!=sid:c.execute('INSERT OR IGNORE INTO raw_refs VALUES(?,?,?,?,?)',(pid,'OpenAlex',oid(target),'',''));stats['reference_rows']+=1
   c.execute('INSERT OR REPLACE INTO openalex_refs VALUES(?,?,?,?)',(sid,pid,len(refs),atlas.now()))
   source=c.execute('SELECT source FROM papers WHERE id=?',(pid,)).fetchone()
   if source and source[0]=='OpenAlex':c.execute('INSERT OR REPLACE INTO refs VALUES(?,?,?,?,?,?)',(pid,'complete',len(refs),len(refs),atlas.now(),'OpenAlex referenced_works returned; indexed provider coverage only'))
 c.commit();c.close();resolve();return stats

def resolve():
 c=atlas.connect();c.execute("INSERT OR IGNORE INTO edges SELECT r.paper,p.id,'OpenAlex referenced_works' FROM raw_refs r JOIN openalex_ids oi ON oi.openalex_id=r.target_id JOIN papers p ON p.id=oi.paper JOIN papers s ON s.id=r.paper WHERE r.target_source='OpenAlex' AND p.accepted=1 AND s.accepted=1 AND r.paper!=p.id");c.commit();c.close()
class Client:
 def __init__(self,maximum,reserve):
  self.maximum=maximum;self.used=0;self.reserve=reserve;self.remaining=None;self.last=0;self.session=requests.Session();self.session.headers['User-Agent']='AromaResearchAtlas/1.0 (public scholarly metadata research)'
  # A new goal turn must not spend a probe merely to rediscover an exhausted
  # daily reserve. Reuse the last server budget only until its recorded reset.
  c=atlas.connect()
  try:previous=c.execute('SELECT time,remaining_usd,headers FROM openalex_budget_checks ORDER BY rowid DESC LIMIT 1').fetchone()
  except sqlite3.OperationalError:previous=None
  finally:c.close()
  if previous:
   try:
    headers={k.lower():v for k,v in json.loads(previous[2]).items()}
    age=max(0,(dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(previous[0])).total_seconds())
    if age<float(headers.get('x-ratelimit-reset',0)):self.remaining=float(previous[1])
   except (ValueError,TypeError,KeyError):pass
 def budget(self,headers):
  h={k:v for k,v in headers.items() if 'ratelimit' in k.lower() or k.lower()=='retry-after'}
  low={k.lower():v for k,v in h.items()};remaining=low.get('x-ratelimit-remaining-usd');cost=low.get('x-ratelimit-cost-usd')
  self.remaining=float(remaining) if remaining is not None else None
  if self.remaining is None:raise StopHarvest('missing public USD budget header; stop conservatively')
  c=atlas.connect();c.execute('INSERT INTO openalex_budget_checks VALUES(?,?,?,?)',(atlas.now(),self.remaining,float(cost or 0),json.dumps(h)));c.commit();c.close();return h
 def get(self,params):
  if self.used>=self.maximum:raise StopHarvest('bounded request limit reached')
  if self.remaining is not None and self.remaining-.001<self.reserve:raise StopHarvest('shared free budget reserve would be crossed')
  time.sleep(max(0,1.2-(time.monotonic()-self.last)));self.last=time.monotonic();self.used+=1
  r=self.session.get(BASE,params=params,timeout=(20,120));h=self.budget(r.headers);log(stage='budget',http_status=r.status_code,requests=self.used,headers=h)
  if r.status_code in [401,403,429]:raise StopHarvest('public API blocked/throttled HTTP '+str(r.status_code)+'; no retries')
  r.raise_for_status();return r.json()
def report(client):
 c=atlas.connect();c.row_factory=__import__('sqlite3').Row
 d={'retrieved_at':atlas.now(),'cutoff':atlas.CUTOFF,'provider':'OpenAlex','endpoint':BASE,'fields':FIELDS,'requests_this_run':client.used,'budget_reserve_usd':client.reserve,'remaining_shared_budget_usd':client.remaining,'queries':[dict(r) for r in c.execute('SELECT * FROM openalex_queries')],'source_counts':[dict(r) for r in c.execute('SELECT source,accepted,count(*) n FROM papers GROUP BY source,accepted')],'mapped_work_ids':c.execute('SELECT count(*) FROM openalex_ids').fetchone()[0],'reference_responses':c.execute('SELECT count(*) FROM openalex_refs').fetchone()[0],'raw_reference_rows':c.execute("SELECT count(*) FROM raw_refs WHERE target_source='OpenAlex'").fetchone()[0],'resolved_edges':c.execute("SELECT count(*) FROM edges WHERE provider='OpenAlex referenced_works'").fetchone()[0],'limitations':['Basic pagination only (at most 100 pages / 10,000 works per query); actual bounds and resumable page state are recorded. Not exhaustive field coverage.','Candidate totals are provider counts, not included papers. DOI/PMID metadata from existing providers is preserved.','Real referenced_works only; unmatched reference IDs remain unresolved.','Keyless shared free-budget use only; no signup/authentication/prepaid operations.']};c.close();(ROOT/'research/openalex_harvest_report.json').write_text(json.dumps(d,indent=2));log(stage='summary',requests=client.used,remaining_shared_budget_usd=client.remaining,mapped_work_ids=d['mapped_work_ids'],raw_reference_rows=d['raw_reference_rows'],resolved_edges=d['resolved_edges'])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--max-requests',type=int,default=29);ap.add_argument('--max-page',type=int,default=10);ap.add_argument('--reserve-usd',type=float,default=.06);ap.add_argument('--cached-probe',action='store_true');a=ap.parse_args();init();client=Client(a.max_requests,a.reserve_usd)
 try:
  for name,query in QUERIES.items():
   c=atlas.connect();old=c.execute('SELECT next_page,seen,complete FROM openalex_queries WHERE name=?',(name,)).fetchone();c.close()
   if old and old[2]:continue
   page=old[0] if old else 1;seen=old[1] if old else 0
   while page<=min(100,a.max_page):
    cached=ROOT/'research/openalex_probe.json'
    if not old and page==1 and name=='aroma' and a.cached_probe and cached.exists():
     probe=json.loads(cached.read_text());client.budget(probe['budget_headers']);d=probe['data']
    else:d=client.get({'filter':'title.search:'+query+',from_publication_date:1800-01-01,to_publication_date:'+atlas.CUTOFF,'per_page':100,'page':page,'select':FIELDS})
    rows=d.get('results',[]);stats=ingest(rows,name);seen+=len(rows);hits=int(d.get('meta',{}).get('count') or 0);done=not rows or page*100>=hits;c=atlas.connect();c.execute('INSERT OR REPLACE INTO openalex_queries VALUES(?,?,?,?,?,?,?,?)',(name,query,page+1,hits,seen,int(done),atlas.now(),''));c.commit();c.close();log(stage='openalex_title',query=name,page=page,seen=seen,hits=hits,complete=done,**stats)
    if done:break
    page+=1
 except Exception as e:log(stage='stopped',reason=str(e))
 finally:resolve();report(client)
if __name__=='__main__':main()
