#!/usr/bin/env python3
"""Resumable, rate-limited Crossref discovery plus exact verified aroma anchors.

No API key, signup, paid operation, full-text scraping, or invented citation edges.
Crossref search is ranked discovery, not an exact-match or exhaustive census.
"""
import argparse,datetime as dt,html,json,re,sqlite3,time
from pathlib import Path
import requests
import atlas
ROOT=Path(__file__).resolve().parents[1]
QUERIES={
 'aroma':'aroma', 'fragrance':'fragrance', 'perfume':'perfume',
 'odorant':'odorant', 'olfactophore':'olfactophore',
 'odor_prediction':'odor prediction', 'odor_threshold':'odor threshold',
 'structure_odor':'structure odor', 'pharmacophore_odor':'pharmacophore odor',
 'flavordb':'FlavorDB', 'olfactory_receptor_ligand':'olfactory receptor ligand',
 'aroma_intensity':'aroma intensity',
 'odor':'odor', 'odour':'odour', 'olfactory':'olfactory',
 'olfactometry':'olfactometry', 'flavour':'flavour', 'flavor_american_v1':'flavor', 'odourant_v1':'odourant', 'perfumery_v1':'perfumery', 'odorophore_v1':'odorophore', 'volatile':'volatile',
 'parent_linalool_v2':'linalool', 'parent_limonene_v2':'limonene',
 'parent_vanillin_v2':'vanillin', 'parent_geraniol_v2':'geraniol',
 'parent_menthol_v2':'menthol', 'parent_eugenol_v2':'eugenol',
 'parent_carvacrol_v2':'carvacrol', 'parent_thymol_v2':'thymol',
 'parent_caryophyllene_v2':'caryophyllene', 'parent_bisabolol_v2':'bisabolol',
 'parent_citral_v2':'citral', 'parent_camphor_v2':'camphor',
 'parent_anethole_v3':'anethole', 'parent_farnesol_v3':'farnesol',
 'parent_carvone_v3':'carvone', 'parent_terpineol_v3':'terpineol',
 'parent_citronellol_v3':'citronellol', 'parent_linalyl_acetate_v3':'linalyl acetate',
 'parent_cinnamaldehyde_v3':'cinnamaldehyde', 'parent_isoeugenol_v3':'isoeugenol',
 'parent_eucalyptol_v3':'eucalyptol', 'parent_borneol_v3':'borneol',
 'parent_nerolidol_v3':'nerolidol', 'parent_citronellal_v3':'citronellal',
 'parent_methyl_salicylate_v3':'methyl salicylate', 'parent_benzaldehyde_v3':'benzaldehyde',
 'parent_benzyl_acetate_v3':'benzyl acetate', 'parent_phenethyl_alcohol_v3':'phenethyl alcohol',
 'parent_ionone_v3':'ionone', 'parent_myrcene_v3':'myrcene',
 'parent_humulene_v3':'humulene', 'parent_isoborneol_v3':'isoborneol',
 'parent_fenchone_v3':'fenchone', 'parent_fenchol_v3':'fenchol',
 'parent_estragole_v3':'estragole', 'parent_methyl_eugenol_v3':'methyl eugenol',
 'parent_cuminaldehyde_v3':'cuminaldehyde', 'parent_methyl_anthranilate_v3':'methyl anthranilate',
 'parent_benzyl_salicylate_v3':'benzyl salicylate', 'parent_santalol_v3':'santalol',
 'parent_safrole_v3':'safrole', 'parent_cymene_v3':'cymene',
 'parent_decalactones_v5':'decalactone', 'parent_nonalactone_v5':'nonalactone',
 'parent_undecalactone_v5':'undecalactone', 'parent_hydroxycitronellal_v5':'hydroxycitronellal',
 'parent_cinnamyl_v5':'cinnamyl', 'parent_anisyl_v5':'anisyl',
 'parent_geranyl_v5':'geranyl', 'parent_eugenyl_v5':'eugenyl',
 'parent_terpinene_v5':'terpinene', 'parent_terpinolene_v5':'terpinolene',
 'parent_sclareol_v5':'sclareol', 'parent_hexadecanolactone_v5':'hexadecanolactone',
 'parent_hexylcinnamaldehyde_v5':'hexylcinnamaldehyde', 'parent_amyl_salicylate_v5':'amyl salicylate',
 'parent_coumarin_v4':'coumarin', 'parent_benzyl_alcohol_v4':'benzyl alcohol',
 'parent_benzyl_benzoate_v4':'benzyl benzoate', 'parent_methyl_benzoate_v4':'methyl benzoate',
 'parent_ethyl_butyrate_v4':'ethyl butyrate', 'parent_ethyl_hexanoate_v4':'ethyl hexanoate',
 'parent_hedione_v4':'methyl dihydrojasmonate', 'parent_galaxolide_v4':'galaxolide',
 'parent_tonalide_v4':'tonalide', 'parent_lilial_v4':'lilial',
 'musks_v2':'musks', 'fragrant_v2':'fragrant', 'olfactive_v2':'olfactive', 'olfactometric_v2':'olfactometric', 'scent_chemistry_v2':'scent',
 'parent_ethylvanillin_v6':'ethyl vanillin', 'parent_piperonal_v6':'piperonal',
 'parent_phenylacetate_v6':'phenylacetate', 'parent_benzylacetone_v6':'benzylacetone',
 'parent_octanal_v6':'octanal', 'parent_nonanal_v6':'nonanal', 'parent_decanal_v6':'decanal',
 'parent_hexylacetate_v6':'hexyl acetate', 'parent_phenethylacetate_v6':'phenethyl acetate',
 'parent_nerylacetate_v6':'neryl acetate', 'parent_citronellylacetate_v6':'citronellyl acetate',
 'parent_phenylacetaldehyde_v6':'phenylacetaldehyde', 'parent_anisaldehyde_v6':'p-anisaldehyde',
 'parent_muscone_v7':'muscone', 'parent_musk_ketone_v7':'musk ketone', 'parent_musk_xylene_v7':'musk xylene',
 'parent_pentadecalactone_v7':'pentadecalactone',
}
TYPES={'journal-article','proceedings-article','posted-content'}
def log(**d): print(json.dumps({'time':atlas.now(),**d}),flush=True)
def init():
 atlas.init();c=atlas.connect();c.executescript('''
 CREATE TABLE IF NOT EXISTS crossref_queries(name TEXT PRIMARY KEY,query TEXT,cursor TEXT,hits INTEGER,seen INTEGER,complete INTEGER,updated TEXT,error TEXT);
 CREATE TABLE IF NOT EXISTS crossref_responses(paper TEXT PRIMARY KEY,doi TEXT,reference_count INTEGER,reference_rows INTEGER,updated TEXT,query TEXT);
 ''');c.commit();c.close()
def text(s):return atlas.clean(s)
def normdoi(s):return re.sub(r'^https?://(?:dx\.)?doi\.org/','',s or '',flags=re.I).strip().lower()
def date_parts(p):
 for key in ['published','published-print','published-online','issued']:
  a=p.get(key,{}).get('date-parts',[])
  if a and a[0] and isinstance(a[0][0],int):
   v=(a[0]+[1,1])[:3]
   try:return dt.date(*v)
   except (ValueError,TypeError):continue
 return None

def classify_record(p):
 title=text(' '.join(p.get('title') or []));ab=text(p.get('abstract',''))
 ok,cat,tracks,evidence=atlas.classify(title,ab)
 # Avoid aromatic/aromatics and unrelated flavour-of-the-month records creating aroma matches.
 cleantext=re.sub(r'\baromatic\w*\b','',title+' '+ab,flags=re.I)
 central=bool(re.search(r'\b(aromas?|fragranc\w*|perfum\w*|odou?r\w*|olfact\w*|smell\w*|flavo[u]?r\w*|flavordb|superscent|pyrfume)\b',cleantext,re.I))
 if atlas.NAMED_RX.search(atlas.chemical_text(title)) and (atlas.PHARMA_RX.search(title+' '+ab) or re.search(r'\b(synthesis|production|biosynthesis|biotransformation)\b',title,re.I)):central=True
 if atlas.physical_parent_study(title) or atlas.parent_production(title):central=True
 if atlas.scent_chemistry(title,ab):central=True
 if not central:ok=False;evidence.append('supplement: no explicit aroma/odor context after aromatic-chemistry exclusion')
 if atlas.secondary_abstract(title,p.get('DOI',''),' '.join(p.get('container-title') or [])):ok=False;evidence.append('supplement: secondary abstracting record')
 when=date_parts(p)
 if p.get('type') not in TYPES:ok=False;evidence.append('supplement: excluded record type '+str(p.get('type')))
 if not when or when.isoformat()>atlas.CUTOFF:ok=False;evidence.append('supplement: missing or out-of-window publication date')
 if not ab and ok:
  # With no abstract, only accept a self-contained aroma-chemistry/intensity/model title.
  mt={k:bool(r.search(title)) for k,r in atlas.RX.items()}
  if not ((mt['aroma'] or mt['odor'] or mt['resource']) and (mt['chem'] or mt['potency'] or mt['prediction'] or mt['resource'])) and not atlas.self_contained_parent_title(title) and not atlas.self_contained_flavor_title(title) and not atlas.scent_chemistry(title):
   ok=False;evidence.append('supplement: missing abstract and ambiguous title')
 evidence.append('Crossref title/abstract automated screening')
 return ok,cat,tracks,evidence,title,ab,when

def ingest(rows,query):
 c=atlas.connect();counts={'returned':len(rows),'new':0,'accepted_new':0,'reused':0,'reference_rows':0}
 for p in rows:
  doi=normdoi(p.get('DOI'))
  if not doi:continue
  ok,cat,tracks,evidence,title,ab,when=classify_record(p)
  old=c.execute('SELECT id,source FROM papers WHERE doi=? ORDER BY accepted DESC LIMIT 1',(doi,)).fetchone()
  pid=old[0] if old else 'doi:'+doi
  if not old:
   authors='; '.join(' '.join(v for v in [a.get('given',''),a.get('family','') or a.get('name','')] if v) for a in p.get('author',[]))
   journal='; '.join(p.get('container-title') or [])
   c.execute('INSERT OR IGNORE INTO papers VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(pid,doi,title,when.year if when else 0,authors,journal,ab,p.get('is-referenced-by-count',0),'','','Crossref',doi,cat,json.dumps(tracks),json.dumps(evidence),int(ok),json.dumps(p,separators=(',',':'))))
   counts['new']+=1;counts['accepted_new']+=int(ok)
  else:counts['reused']+=1
  c.execute('INSERT OR IGNORE INTO provenance VALUES(?,?)',(pid,'crossref:'+query))
  refs=p.get('reference',[])
  n=0
  for r in refs:
   rd=normdoi(r.get('DOI'))
   if rd and rd!=doi:
    rt=text(r.get('article-title') or r.get('unstructured') or '')
    c.execute('INSERT OR IGNORE INTO raw_refs VALUES(?,?,?,?,?)',(pid,'Crossref',rd,rd,rt));n+=1
  counts['reference_rows']+=n
  c.execute('INSERT OR REPLACE INTO crossref_responses VALUES(?,?,?,?,?,?)',(pid,doi,p.get('reference-count',len(refs)),len(refs),atlas.now(),query))
  if not old or old[1]=='Crossref':
   # A complete response can have zero references; this does not mean the paper cited nothing.
   c.execute('INSERT OR REPLACE INTO refs VALUES(?,?,?,?,?,?)',(pid,'complete',p.get('reference-count',len(refs)),len(refs),atlas.now(),'Crossref metadata response; deposited reference coverage only'))
 c.commit();c.close();return counts

def resolve():
 c=atlas.connect();c.execute("INSERT OR IGNORE INTO edges SELECT r.paper,p.id,'Crossref deposited reference list' FROM raw_refs r JOIN papers p ON r.doi=p.doi JOIN papers s ON s.id=r.paper WHERE r.target_source='Crossref' AND r.doi!='' AND p.accepted=1 AND s.accepted=1 AND r.paper!=p.id")
 c.commit();c.close()

def anchors():
 """Import only deliberately selected verified anchors; preserve existing EPMC metadata."""
 path=ROOT/'research/verified_seeds.json'
 if not path.exists():return
 seeds=json.loads(path.read_text())['papers'];c=atlas.connect();new=updated=0
 for p in seeds:
  doi=normdoi(p.get('doi'))
  if not doi:continue
  old=c.execute('SELECT id,tracks,evidence,accepted FROM papers WHERE doi=? ORDER BY accepted DESC LIMIT 1',(doi,)).fetchone()
  tags=p.get('tags',[]);prediction=bool(set(tags)&{'prediction','pharmacophore','software'})
  tracks=['aroma']+(['prediction'] if prediction else [])
  title=p['title'];ok,cat,_,evidence=atlas.classify(title,'')
  if 'database' in tags:cat='Databases & benchmarks'
  elif 'pharmacophore' in tags:cat='Receptors & pharmacophores'
  elif 'prediction' in tags:cat='Molecular prediction'
  elif 'intensity' in tags or 'threshold' in tags:cat='Intensity & thresholds'
  evidence.append('API-verified curated aroma seed DOI/title; tags manually selected from source research')
  pid=old[0] if old else 'doi:'+doi
  if old:
   merged=list(dict.fromkeys(json.loads(old[1] or '[]')+tracks));ev=list(dict.fromkeys(json.loads(old[2] or '[]')+evidence))
   c.execute('UPDATE papers SET tracks=?,evidence=?,accepted=1 WHERE id=?',(json.dumps(merged),json.dumps(ev),pid));updated+=1
  else:
   c.execute('INSERT OR IGNORE INTO papers VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(pid,doi,title,int(p.get('year') or 0),p.get('authors',''),'','',p.get('cited_by_count_europepmc',p.get('cited_by_count_crossref',0)),p.get('pmid',''),p.get('pmcid',''),'Crossref',doi,cat,json.dumps(tracks),json.dumps(evidence),1,json.dumps(p)))
   new+=1
  c.execute('INSERT OR IGNORE INTO provenance VALUES(?,?)',(pid,'curated:verified_seed'))
 c.commit();c.close()
 # Previously retrieved exact Crossref metadata contains real reference lists.
 meta=ROOT/'research/industrial_seed_metadata.json'
 if meta.exists():
  c=atlas.connect()
  for p in json.loads(meta.read_text()):
   doi=normdoi(p['doi']);row=c.execute('SELECT id,source FROM papers WHERE doi=? ORDER BY accepted DESC LIMIT 1',(doi,)).fetchone()
   if not row:continue
   for r in p.get('references',[]):
    rd=normdoi(r.get('DOI'))
    if rd and rd!=doi:c.execute('INSERT OR IGNORE INTO raw_refs VALUES(?,?,?,?,?)',(row[0],'Crossref',rd,rd,text(r.get('article-title') or r.get('unstructured') or '')))
   refs=p.get('references',[])
   c.execute('INSERT OR REPLACE INTO crossref_responses VALUES(?,?,?,?,?,?)',(row[0],doi,p.get('reference_count',len(refs)),len(refs),atlas.now(),'curated:industrial_exact_doi'))
   if row[1]=='Crossref':c.execute('INSERT OR REPLACE INTO refs VALUES(?,?,?,?,?,?)',(row[0],'complete',p.get('reference_count',len(refs)),len(refs),atlas.now(),'Crossref metadata response; deposited reference coverage only'))
  c.commit();c.close()
 resolve();log(stage='curated_anchors',new=new,existing_enriched=updated)

class PersistentThrottle(RuntimeError):pass
class Client:
 def __init__(self,max_requests):
  self.session=requests.Session();self.session.headers['User-Agent']='AromaResearchAtlas/1.0 (public scholarly metadata research)';self.last=0;self.count=0;self.maximum=max_requests
 def get(self,params):
  ratefail=0
  for attempt in range(5):
   if self.count>=self.maximum:raise RuntimeError('request budget reached')
   time.sleep(max(0,1.15-(time.monotonic()-self.last)));self.last=time.monotonic();self.count+=1
   try:
    r=self.session.get('https://api.crossref.org/works',params=params,timeout=(20,150))
   except requests.RequestException as exc:
    if attempt==4:raise
    delay=min(60,2**(attempt+1));log(stage='retry',error=str(exc)[:200],delay=delay);time.sleep(delay);continue
   # Respect a stricter current server interval if supplied.
   interval=re.search(r'([0-9.]+)',r.headers.get('x-rate-limit-interval','1s'))
   if interval:
    limit=float(r.headers.get('x-rate-limit-limit','1'));time.sleep(max(0,float(interval[1])/max(1,limit)-.9))
   if r.status_code==429:
    ratefail+=1
    if ratefail>=2:raise PersistentThrottle('persistent Crossref throttling (two HTTP 429 responses); stop all query streams')
   if r.status_code in [429,500,502,503,504]:
    retry=r.headers.get('Retry-After','')
    try:delay=float(retry)
    except ValueError:delay=2**(attempt+1)
    log(stage='retry',http=r.status_code,delay=delay);time.sleep(min(60,max(2,delay)));continue
   r.raise_for_status();return r.json()['message']
  raise RuntimeError('Crossref retries exhausted')

def report(client=None):
 c=atlas.connect();c.row_factory=sqlite3.Row
 d={'retrieved_at':atlas.now(),'cutoff':atlas.CUTOFF,'provider':'Crossref REST API','endpoint':'https://api.crossref.org/works','query_parameter':'query.title','filter':'until-pub-date:'+atlas.CUTOFF,'types_accepted':sorted(TYPES),'screening':'atlas.classify plus explicit odor/aroma context, aromatic-word exclusion, publication-date/type checks, missing-abstract title checks','scope':'Ranked candidate discovery, not exhaustive field coverage. Existing Europe PMC metadata retained. Citation links are deposited DOI references only.','requests_this_run':getattr(client,'count',0),'query_states':[dict(r) for r in c.execute('SELECT * FROM crossref_queries')],'source_counts':[dict(r) for r in c.execute('SELECT source,accepted,count(*) n FROM papers GROUP BY source,accepted')],'crossref_reference_responses':c.execute('SELECT count(*) FROM crossref_responses').fetchone()[0],'crossref_raw_reference_rows':c.execute("SELECT count(*) FROM raw_refs WHERE target_source='Crossref'").fetchone()[0],'crossref_resolved_edges':c.execute("SELECT count(*) FROM edges WHERE provider='Crossref deposited reference list'").fetchone()[0]}
 c.close()
 for q in d['query_states']:q['coverage_state']='exhausted ranked query results' if q['complete'] else 'bounded candidate sample; additional pages remain'
 d['exhausted_queries']=[q['name'] for q in d['query_states'] if q['complete']]
 d['bounded_queries']=[q['name'] for q in d['query_states'] if not q['complete']]
 (ROOT/'research/crossref_harvest_report.json').write_text(json.dumps(d,indent=2));log(stage='summary',**{k:d[k] for k in ['requests_this_run','crossref_reference_responses','crossref_raw_reference_rows','crossref_resolved_edges']})

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--pages-per-query',type=int,default=3);ap.add_argument('--rows',type=int,default=1000);ap.add_argument('--max-requests',type=int,default=40);ap.add_argument('--anchors-only',action='store_true');ap.add_argument('--max-query-rows',type=int,default=0,help='Optional cumulative per-query candidate bound; zero leaves selected streams unbounded');ap.add_argument('--query-names',default='',help='Comma-separated keys from QUERIES; empty selects all');args=ap.parse_args();selected=[x.strip() for x in args.query_names.split(',') if x.strip()] or list(QUERIES);unknown=set(selected)-set(QUERIES)
 if unknown:ap.error('Unknown query names: '+','.join(sorted(unknown)))
 init();anchors();client=Client(args.max_requests)
 if not args.anchors_only:
  for name in selected:
   query=QUERIES[name]
   c=atlas.connect();old=c.execute('SELECT cursor,seen,complete FROM crossref_queries WHERE name=?',(name,)).fetchone();c.close()
   if old and old[2]:continue
   if old and args.max_query_rows and old[1]>=args.max_query_rows:
    log(stage='query_bound',query=name,seen=old[1],bound=args.max_query_rows);continue
   cursor=old[0] if old else '*';seen=old[1] if old else 0
   for page in range(args.pages_per_query):
    if args.max_query_rows and seen>=args.max_query_rows:break
    try:
     d=client.get({'query.title':query,'filter':'until-pub-date:'+atlas.CUTOFF,'rows':min(1000,args.rows),'cursor':cursor});rows=d.get('items',[]);counts=ingest(rows,name);seen+=len(rows);nxt=d.get('next-cursor');done=len(rows)<min(1000,args.rows) or not nxt
     c=atlas.connect();c.execute('INSERT OR REPLACE INTO crossref_queries VALUES(?,?,?,?,?,?,?,?)',(name,query,nxt or cursor,d.get('total-results',0),seen,int(done),atlas.now(),''));c.commit();c.close();resolve();log(stage='crossref_harvest',query=name,page_this_run=page+1,seen=seen,hits=d.get('total-results'),complete=done,requests=client.count,**counts)
     if done:break
     cursor=nxt
    except Exception as e:
     c=atlas.connect();c.execute('INSERT INTO crossref_queries VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET error=excluded.error,updated=excluded.updated',(name,query,cursor,0,seen,0,atlas.now(),str(e)[:500]));c.commit();c.close();log(stage='error',query=name,error=str(e))
     if isinstance(e,PersistentThrottle):resolve();report(client);return
     break
   if client.count>=client.maximum:break
 resolve();report(client)
if __name__=='__main__':main()
