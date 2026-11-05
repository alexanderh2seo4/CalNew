"""Resolve paper names with PubChem; cache responses and audit hand transcriptions."""
import csv, json, time, pathlib, requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
from rdkit import Chem
P = pathlib.Path(__file__).resolve().parent
rows = list(csv.DictReader((P/'ligands.tsv').open(), delimiter='\t'))
cache = P/'sources'/'pubchem'; cache.mkdir(exist_ok=True)
def resolve(r):
    path = cache/(r['id']+'.json')
    url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/'+quote(r['name'],safe='')+'/property/ConnectivitySMILES,IsomericSMILES,InChIKey/JSON'
    if not path.exists():
        response = requests.get(url, timeout=45)
        path.write_text(json.dumps({'url':url,'status':response.status_code,'response':response.json()},indent=2))
    d = json.loads(path.read_text())
    prop = d['response'].get('PropertyTable',{}).get('Properties',[])
    m=Chem.MolFromSmiles(r['smiles'])
    if prop:
        p=prop[0]; resolved=Chem.MolFromSmiles(p['SMILES'])
        same=Chem.MolToSmiles(m,isomericSmiles=False)==Chem.MolToSmiles(resolved,isomericSmiles=False)
        status='match' if same else 'MISMATCH'
        return {**r,'pubchem_cid':p['CID'],'pubchem_smiles':p['SMILES'],'pubchem_inchi_key':p['InChIKey'],'graph_audit':status,'pubchem_url':url}
    return {**r,'graph_audit':'name_not_resolved','pubchem_url':url}
with ThreadPoolExecutor(max_workers=4) as ex: audited=list(ex.map(resolve,rows))
(P/'structure_audit.json').write_text(json.dumps(audited,indent=2))
for r in audited:print(r['id'],r['graph_audit'],r.get('pubchem_smiles',''),flush=True)
