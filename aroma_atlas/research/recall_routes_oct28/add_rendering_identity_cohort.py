import pathlib,json,unicodedata,re,html,hashlib,urllib.request,datetime
root=pathlib.Path(__file__).resolve().parents[2];p=root/'research/bibliographic_identity_audit_2026-10-28.json';d=json.loads(p.read_text())
def norm(s):return re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',html.unescape(s or ''))).strip().rstrip('.!?;: ,')
def render(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',re.sub('<[^>]+>',' ',html.unescape(s or ''))))
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
url='https://api.crossref.org/works/10.1016%2Fj.foodres.2025.116467'
proof=d.get('known_pair_crossref_proof')
if not proof:
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'AromaResearchAtlas/1.0 read-only identity audit'})
  with urllib.request.urlopen(req,timeout=50) as r:
   raw=r.read().decode();proof={'url':url,'status':r.status,'headers':dict(r.headers),'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw_body':raw,'body_sha256':sha(raw)}
 except Exception as e:proof={'url':url,'error':str(e),'time':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 d['known_pair_crossref_proof']=proof;p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
metadata=json.loads(proof.get('raw_body','{}')).get('message',{})
issns=set(metadata.get('ISSN',[]));known_issn_support={'issns':sorted(issns),'crossref_container_title':metadata.get('container-title'),'crossref_volume':metadata.get('volume'),'crossref_article_number':metadata.get('article-number'),'doi':metadata.get('DOI')}
cohort=[];known=None
for original in d['very_high_confidence_duplicates']+d['abstract_unequal_flags']+d['insufficient_proof_flags']:
 a,b=original['left'],original['right'];mp=original['matching_proof'];aa,bb=render(a['abstract']),render(b['abstract'])
 samejournal=bool(mp['shared_issn'] or mp['shared_normalized_journal_names']);knownpair=a['id']=='AGR:IND609267307' and b['id']=='pmid:40356132'
 if knownpair:
  supported=bool(set(mp['journal_left']['issns'])&issns) and metadata.get('DOI','').lower()==b['doi'].lower() and str(metadata.get('volume'))==mp['journal_left']['volume']==mp['journal_right']['volume'] and norm(' '.join(metadata.get('title',[]))).casefold()==mp['normalized_full_title'] and str(metadata.get('article-number') or metadata.get('page'))==str(mp['journal_right']['page_info']) and bool(set(norm(x).casefold() for x in metadata.get('container-title',[]))&set(mp['journal_left']['names'])) and metadata.get('published',{}).get('date-parts',[[None]])[0][0]==a['year']
  known_issn_support['scope_note']='Record-specific bridge: AGR print ISSN+journal title match official exact DOI response; MED exact DOI+article number+volume/year match that response; both index records share full normalized title and authorstring. Crossref did NOT return electronic ISSN, so this is not a generalized print/electronic ISSN mapping.'
  samejournal=samejournal or supported
  known={'left_id':a['id'],'right_id':b['id'],'strict_abstract_equal':mp['abstract_equal'],'rendering_abstract_equal':aa==bb,'rendered_lengths':[len(aa),len(bb)],'same_journal_primary_corroboration':supported,'primary_source_proof':known_issn_support,'matching_proof':mp,'left':a,'right':b}
 if aa==bb and len(norm(a['abstract']))>=200 and len(norm(b['abstract']))>=200 and samejournal and mp['journal_volume_equal'] and not mp['conflicting_doi_or_pmid']:
  cohort.append({'left':a,'right':b,'original_strict_verdict':original['verdict'],'matching_proof':mp,'rendering_equivalence_proof':{'algorithm':'HTML entities decoded; tags stripped with whitespace separators; Unicode NFKC; delete all whitespace; preserve remaining letters/numbers/punctuation; no fuzzy matching or edit threshold','rendered_sha256':[sha(aa),sha(bb)],'rendered_lengths':[len(aa),len(bb)],'normalized_abstract_lengths':[len(norm(a['abstract'])),len(norm(b['abstract']))],'known_pair_primary_journal_support':known_issn_support if knownpair else None}})
additional=[x for x in cohort if x['original_strict_verdict']!='very-high-confidence-cross-index-duplicate']
def excess(rr):return len({r['left']['id'] for r in rr if r['left']['accepted']==r['right']['accepted']==1})
d['standard_rendering_equivalence_cohort']={'scope':'Same frozen SQL input snapshot as original strict cohort. A separately declared deterministic rendering comparison; does not replace or erase original strict judgments. No DB merge.','pair_count':len(cohort),'accepted_both_pairs':sum(x['left']['accepted']==x['right']['accepted']==1 for x in cohort),'excess_accepted_records':excess(cohort),'additional_over_strict_pairs':len(additional),'additional_over_strict_excess_accepted_records':excess(additional),'pairs':cohort}
d['known_pyrazine_pair_rendering_result']=known
combined=d['very_high_confidence_duplicates']+cohort
pairs={(x['left']['id'],x['right']['id']) for x in combined}
d['strict_or_standard_rendering_union']={'pair_count':len(pairs),'accepted_excess_records':excess(combined),'accepted_excess_ids':sorted({x['left']['id'] for x in combined if x['left']['accepted']==x['right']['accepted']==1}),'note':'Union avoids counting the same pair/AGR record twice; standard-rendering preserves punctuation and therefore need not contain every strict punctuation-trimmed match.'}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
print(json.dumps({'crossref_status':proof.get('status'),'crossref_issns':sorted(issns),'strict_pairs':d['exact_duplicate_pair_count'],'strict_excess_accepted':d['exact_duplicate_excess_accepted_records'],'rendering_pairs':len(cohort),'rendering_excess_accepted':excess(cohort),'additional_pairs':len(additional),'additional_excess_accepted':excess(additional),'known_pair':{k:v for k,v in (known or {}).items() if k in ['strict_abstract_equal','rendering_abstract_equal','rendered_lengths','same_journal_primary_corroboration']}},indent=2))
