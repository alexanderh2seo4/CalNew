"""Document discovery, immutable retrieval, and an audited extraction acceptance gate."""
from pathlib import Path
import json
import requests

from .ingest import download
from .io import digest, read_json, write_json

CRITICAL=('molecule_id','raw_value','raw_unit','endpoint','matrix')


def discover(query,limit=50):
    r=requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',
                   params={'query':query,'format':'json','pageSize':min(limit,1000),'resultType':'core'},timeout=60)
    r.raise_for_status()
    return {'query':query,'provider':'Europe PMC','results':r.json().get('resultList',{}).get('result',[])}


def retrieve_open_article(pmcid,root):
    if not pmcid.startswith('PMC') or not pmcid[3:].isdigit(): raise ValueError('Expected PMC identifier')
    info=download(f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML',Path(root)/f'{pmcid}.xml')
    # API access is not a licence: preserve terms for review before training ingestion.
    write_json(Path(root)/f'{pmcid}.json',{**info,'permitted_use':'unverified','training_acceptance':'pending_review'})
    return info


def parse_jats(path):
    import xml.etree.ElementTree as ET
    root=ET.parse(path).getroot()
    records=[]
    for i,element in enumerate(root.iter()):
        if element.tag in ('p','table-wrap','fig'):
            records.append({'location':element.attrib.get('id',f'xml-element-{i}'),'type':element.tag,
                            'text':' '.join(element.itertext()).strip()})
    return records


def extraction_audit(gold,predicted):
    """Each gold observation must be manually checked, never extractor consensus."""
    truth={r['observation_id']:r for r in gold}
    pred={r['observation_id']:r for r in predicted}
    if len(truth)!=len(gold) or len(pred)!=len(predicted): raise ValueError('Duplicate audit IDs')
    if any(r.get('review_status')!='manually_verified' for r in truth.values()):
        raise ValueError('Audit gold must be manually verified')
    classes={}
    for document_class in sorted({r['document_class'] for r in gold}):
        records=[r for r in gold if r['document_class']==document_class]
        fields={field:sum(pred.get(r['observation_id'],{}).get(field)==r.get(field) for r in records)/len(records) for field in CRITICAL+('provenance_location','duplicate_of')}
        exact=sum(all(field in r and pred.get(r['observation_id'],{}).get(field)==r[field] for field in CRITICAL) for r in records)/len(records)
        classes[document_class]={'n':len(records),'critical_exact_agreement':exact,'fields':fields,
                                 'automatic_acceptance':len(records)>=200 and exact>=.98}
    return {'classes':classes,'rule':'At least 200 manually verified examples per automatically accepted document class and >=98% joint critical agreement'}


def queue_record(record,root):
    required=('source_url','location','supporting_text','document_class')
    if any(not record.get(k) for k in required): raise ValueError('Extraction needs source, location, supporting text and class')
    key=digest(record)
    write_json(Path(root)/f'{key}.json',{'status':'pending','extraction':record})
    return key


def quality_audit(snapshot):
    import pandas as pd
    obs=pd.read_parquet(Path(snapshot)/'observations.parquet')
    evidence=pd.read_parquet(Path(snapshot)/'evidence.parquet')
    molecules=pd.read_parquet(Path(snapshot)/'molecules.parquet')
    merged=obs.merge(evidence[['evidence_id','original_experiment_id','review_status']],on='evidence_id',validate='many_to_one')
    keys=['original_experiment_id','molecule_id','endpoint','descriptor','subject_id','replicate']
    duplicate=merged.duplicated(keys,keep=False)
    return {'observations':len(obs),'molecules':len(molecules),'endpoints':obs.endpoint.value_counts().to_dict(),
            'censoring':obs.censoring.value_counts().to_dict(),'origins':obs.value_origin.value_counts().to_dict(),
            'stereochemistry':molecules.stereo_status.value_counts().to_dict(),'review_status':evidence.review_status.value_counts().to_dict(),
            'candidate_duplicate_observations':int(duplicate.sum()),'duplicate_ids':merged.loc[duplicate,'observation_id'].head(100).tolist(),
            'missing_methods':int((obs.method=='unknown').sum()),'missing_source_hashes':int(evidence.source_sha256.isna().sum()),
            'interpretation':'Counts are audit flags, not inferred reliability scores; copied experiments require review.'}
