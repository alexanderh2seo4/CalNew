#!/usr/bin/env python3
"""One-command checkpointed pipeline. Never pads the graph to meet a target."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(*args):
 subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,check=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--discover',action='store_true',help='Run bounded additional public-index discovery; consumes only public free quotas')
 p.add_argument('--retry-semantic',action='store_true',help='Explicitly retry Semantic Scholar after its persistent anonymous throttle barrier changes')
 p.add_argument('--workers',type=int,default=12);p.add_argument('--target',type=int,default=50000);p.add_argument('--skip-references',action='store_true');a=p.parse_args()
 run(ROOT/'pipeline/atlas.py','harvest','--workers',min(a.workers,5))
 if a.discover:
  import supplement
  focused=['aroma','fragrance','perfume','odorant','olfactophore','odor','odour','olfactometry','flavour']
  focused += [name for name in supplement.QUERIES if name.startswith('parent_')]
  run(ROOT/'pipeline/supplement.py','--query-names',','.join(focused),'--pages-per-query','2','--max-requests','30','--max-query-rows','5000')
  run(ROOT/'pipeline/neighbors.py','--max-candidates','100','--max-requests','80','--max-seconds','600')
  if a.retry_semantic:run(ROOT/'pipeline/semantic.py','--bulk-requests','10','--reference-batches','1','--max-requests','12')
  run(ROOT/'pipeline/openalex.py','--max-requests','20','--max-page','100','--reserve-usd','0.06')
 run(ROOT/'pipeline/atlas.py','rescreen')
 run(ROOT/'pipeline/supplement.py','--anchors-only')
 if not a.skip_references:run(ROOT/'pipeline/atlas.py','references','--workers',min(a.workers,24))
 run(ROOT/'pipeline/atlas.py','export')
 run(ROOT/'pipeline/validate_export.py')
 run(ROOT/'pipeline/audit_aliases.py')
 run('-m','unittest','discover','-s',ROOT/'pipeline','-p','test*.py')
 audit_result=subprocess.run([sys.executable,str(ROOT/'pipeline/test_atlas.py'),'--audit-db',str(ROOT/'data/atlas.sqlite'),'--sample-limit','5'],cwd=ROOT,check=True,capture_output=True,text=True)
 audit=json.loads(audit_result.stdout)
 (ROOT/'data/integrity_audit.json').write_text(json.dumps(audit,indent=2))
 bad_integrity={k:v for k,v in audit['integrity'].items() if k in {'dangling_edges','edges_outside_current_accepted_set','self_edges','duplicate_doi_groups','duplicate_pmid_groups'} and v}
 bad_scope={k:v for k,v in audit['screening_warnings'].items() if k in {'stored_scope_differs_from_current_classifier','provider_eligibility_audit_error','reviewed_exclusion_still_accepted','accepted_missing_valid_track','invalid_evidence_or_tracks_json'} and v}
 if bad_integrity or bad_scope:raise RuntimeError('Atlas audit failed: '+json.dumps({'integrity':bad_integrity,'scope':bad_scope}))
 run(ROOT/'pipeline/report.py')
 stats=json.loads((ROOT/'data/stats.json').read_text())
 review_files=__import__('atlas').review_paths()+__import__('atlas').identity_paths()
 hashes={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in list((ROOT/'pipeline').glob('*.py'))+list((ROOT/'research').glob('*allowlist*.json'))+list((ROOT/'research').glob('*seed*.json'))+[f for f in review_files if f.exists()]}
 report={'target_papers':a.target,'included_records':stats['accepted'],'target_met':stats['accepted']>=a.target,'scope':'Automated screen, not manual relevance verification; exact DOI/PMID and frozen full-bibliographic identity proofs; secondary abstracting records excluded; some publication versions remain distinct.','hashes':hashes,'stats':stats}
 (ROOT/'data/run_manifest.json').write_text(json.dumps(report,indent=2))
 print(json.dumps({'target':a.target,'included_records':stats['accepted'],'target_met':report['target_met'],'report':str(ROOT/'data/run_manifest.json')},indent=2))
 if not report['target_met']:print('The target remains unmet. No unrelated records were added to reach it.',file=sys.stderr)
if __name__=='__main__':main()
