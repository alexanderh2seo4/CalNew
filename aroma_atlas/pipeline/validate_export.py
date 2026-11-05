#!/usr/bin/env python3
"""Independently reconcile published graph shards, CSV and GEXF with frozen SQLite.

Structural checks do not establish the scientific relevance of every record.
"""
import collections,csv,hashlib,json,math,sqlite3,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate():
 dist=ROOT/'site/dist';g=json.loads((dist/'graph.json').read_text());nodes=g['nodes'];byid={n['id']:n for n in nodes}
 assert len(byid)==len(nodes),'duplicate graph node IDs'
 c=sqlite3.connect(ROOT/'data/atlas.sqlite');c.row_factory=sqlite3.Row;c.execute('BEGIN')
 papers={p['id']:dict(p) for p in c.execute('SELECT id,title,doi,category,tracks,authors,journal,abstract,evidence FROM papers WHERE accepted=1')}
 assert set(byid)==set(papers),'graph node IDs differ from accepted SQLite IDs'
 edges=[tuple(e) for shard in g['edgeShards'] for e in json.loads((dist/shard).read_text())]
 eset=set(edges);assert len(eset)==len(edges),'duplicate graph citation pairs'
 assert all(a!=b and a in byid and b in byid for a,b in edges),'self/dangling graph citation'
 dbedges={(s,t) for s,t in c.execute('SELECT source,target FROM edges') if s in byid and t in byid}
 assert eset==dbedges,'graph citations differ from SQLite directed citation pairs'
 incoming=collections.Counter(b for a,b in edges);outgoing=collections.Counter(a for a,b in edges)
 details={}
 for n in nodes:
  p=papers[n['id']]
  assert n['title']==p['title'] and n['doi']==p['doi'] and n['category']==p['category'],'stale graph metadata'
  assert n['tracks']==json.loads(p['tracks']),'stale graph track'
  assert n['inDegree']==incoming[n['id']] and n['outDegree']==outgoing[n['id']] and n['degree']==incoming[n['id']]+outgoing[n['id']],'incorrect graph degree'
  assert math.isfinite(n['x']) and math.isfinite(n['y']),'non-finite graph layout'
  shard=n['detailShard']
  if shard not in details:details[shard]=json.loads((dist/'details'/f'{shard:05d}.json').read_text())
  d=details[shard][n['id']]
  for field in ['authors','journal','abstract']:assert d[field]==p[field],'stale or missing extended metadata'
  assert d['evidence']==json.loads(p['evidence']),'stale inclusion evidence'
 csvrows=list(csv.DictReader((ROOT/'data/papers.csv').open()))
 assert len(csvrows)==len(nodes) and {r['id'] for r in csvrows}==set(byid),'paper CSV differs from graph'
 with (ROOT/'data/citations.csv').open() as f:csv_edges={tuple(r[k] for k in ['citing_paper','cited_paper','provider']) for r in csv.DictReader(f)}
 db_provenance={(s,t,p) for s,t,p in c.execute('SELECT source,target,provider FROM edges') if s in byid and t in byid}
 assert csv_edges==db_provenance,'citation CSV provenance differs from SQLite'
 gx_nodes=set();gx_edges=set();directed=False
 for event,el in ET.iterparse(ROOT/'data/aroma-citations.gexf',events=['start','end']):
  tag=el.tag.rsplit('}',1)[-1]
  if event=='start' and tag=='graph':directed=el.get('defaultedgetype')=='directed'
  if event=='end' and tag=='node':gx_nodes.add(el.get('id'));el.clear()
  if event=='end' and tag=='edge':gx_edges.add((el.get('source'),el.get('target')));el.clear()
 assert directed and gx_nodes==set(byid) and gx_edges==eset,'directed GEXF differs from graph'
 assert g['stats']['accepted']==len(nodes) and g['stats']['edges']==len(eset),'headline counts differ from graph'
 assets=[p for p in dist.rglob('*') if p.is_file()];largest=max(assets,key=lambda p:p.stat().st_size)
 assert largest.stat().st_size<=25*1024*1024,'static asset exceeds 25 MiB'
 c.close()
 result={'status':'passed','nodes':len(nodes),'directed_citation_pairs':len(eset),'citation_provenance_rows':len(csv_edges),'metadata_shards':len(details),'edge_shards':len(g['edgeShards']),'largest_asset':str(largest.relative_to(dist)),'largest_asset_bytes':largest.stat().st_size,'graph_manifest_sha256':hashlib.sha256((dist/'graph.json').read_bytes()).hexdigest(),'scope_limit':'Reconciles exact accepted identifiers and all directed edges across SQLite/JSON/CSV/GEXF. It does not manually verify scientific relevance or exhaustive literature coverage.'}
 (ROOT/'data/export_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':validate()
