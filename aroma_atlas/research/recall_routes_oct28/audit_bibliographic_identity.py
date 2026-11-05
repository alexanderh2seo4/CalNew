import sqlite3,pathlib,json,re,html,hashlib,datetime,difflib,collections
root=pathlib.Path(__file__).resolve().parents[2]
# SQL transaction keeps one consistent read snapshot while another process adds metadata.
c=sqlite3.connect('file:'+str(root/'data/atlas.sqlite')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;c.execute('BEGIN')
def n(s):
 return re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',html.unescape(s or ''))).strip().rstrip('.!?;: ,')
def ident(s):return n(s).casefold()
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
counts=[dict(x) for x in c.execute('select accepted,count(*) n from papers group by accepted')]
light=[dict(x) for x in c.execute("select id,source,title,authors,year,doi,pmid from papers where source in ('AGR','MED')")]
index=collections.defaultdict(list)
for r in light:
 if r['source']=='MED':index[(ident(r['title']),ident(r['authors']),r['year'])].append(r)
def full(pid):return dict(c.execute('select * from papers where id=?',(pid,)).fetchone())
def journal(r):
 raw=json.loads(r['raw']);ji=raw.get('journalInfo') or {};j=ji.get('journal') or {}
 return {'volume':n(str(ji.get('volume') or '')),'names':list(set(ident(x) for x in [r['journal'],j.get('title','')] if x)), 'issns':list(set(n(j.get(x,'')) for x in ['issn','essn'] if j.get(x))), 'page_info':raw.get('pageInfo'),'pub_date':ji.get('printPublicationDate')}
exact=[];unequal=[];blocked=[];nominated=0
for a in light:
 if a['source']!='AGR':continue
 for b in index.get((ident(a['title']),ident(a['authors']),a['year']),[]):
  # At least one absent DOI; never merge records with conflicting explicit IDs.
  if a['doi'] and b['doi']:continue
  nominated+=1;aa,bb=full(a['id']),full(b['id']);ja,jb=journal(aa),journal(bb)
  ab1,ab2=n(aa['abstract']),n(bb['abstract']);same_volume=bool(ja['volume'] and ja['volume']==jb['volume']);shared_issn=sorted(set(ja['issns'])&set(jb['issns']));shared_names=sorted(set(ja['names'])&set(jb['names']));same_journal=bool(shared_issn or shared_names)
  conflict=bool((a['doi'] and b['doi'] and ident(a['doi'])!=ident(b['doi'])) or (a['pmid'] and b['pmid'] and a['pmid']!=b['pmid']))
  proof={'normalized_full_title':ident(a['title']),'normalized_authorstring':ident(a['authors']),'year':a['year'],'journal_volume_equal':same_volume,'journal_left':ja,'journal_right':jb,'shared_issn':shared_issn,'shared_normalized_journal_names':shared_names,'conflicting_doi_or_pmid':conflict,'abstract_lengths':[len(ab1),len(ab2)],'abstract_equal':ab1==ab2,'abstract_sha256':[sha(ab1),sha(ab2)],'normalization':'HTML entity decode and tag removal, whitespace collapse, leading whitespace and trailing .!?;:, space removal; title/author/journal casefold; abstract case preserved; no Unicode, math, lexical, or fuzzy normalization'}
  rec={'left':aa,'right':bb,'matching_proof':proof}
  if not conflict and same_volume and same_journal and len(ab1)>=200 and ab1==ab2:
   rec['verdict']='very-high-confidence-cross-index-duplicate';exact.append(rec)
  elif not conflict and same_volume and len(ab1)>=200 and len(ab2)>=200 and ab1!=ab2:
   # Flag every exact-title/author/year/volume unequal abstract pair, not a fuzzy-match rule.
   rec['verdict']='flag-only-abstract-unequal-no-automatic-merge';sm=difflib.SequenceMatcher(None,ab1,ab2,autojunk=False);rec['abstract_difference_spans']=[{'operation':tag,'left_start':i,'left_end':j,'left':ab1[i:j],'right_start':k,'right_end':l,'right':ab2[k:l]} for tag,i,j,k,l in sm.get_opcodes() if tag!='equal'];unequal.append(rec)
  else:
   rec['verdict']='insufficient-proof-no-automatic-merge';blocked.append(rec)
c.rollback();c.close()
out={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'read_only':True,'snapshot':'SQLite mode=ro explicit BEGIN read transaction, all input rows from same snapshot','snapshot_counts':counts,'source_counts':dict(collections.Counter(r['source'] for r in light)),'rules':'AGR versus MED only; >=one missing DOI; exact normalized full title+author string+year+nonempty raw journal volume; journal corroboration by intersecting ISSN or exact normalized journal name; no conflicting DOI/PMID; abstracts exact after explicitly limited normalization and length>=200. No fuzzy matching, title-only merges, preprint/source version merging, DB or classifier mutations.','candidate_pairs':nominated,'exact_duplicate_pair_count':len(exact),'accepted_both_exact_duplicate_pairs':sum(r['left']['accepted']==r['right']['accepted']==1 for r in exact),'exact_duplicate_excess_accepted_records':len({r['left']['id'] for r in exact if r['left']['accepted']==r['right']['accepted']==1}),'flagged_unequal_abstract_pairs':len(unequal),'insufficient_proof_pairs':len(blocked),'very_high_confidence_duplicates':exact,'abstract_unequal_flags':unequal,'insufficient_proof_flags':blocked}
(root/'research/bibliographic_identity_audit_2026-10-28.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ['very_high_confidence_duplicates','abstract_unequal_flags','insufficient_proof_flags']},indent=2))
for r in exact:print('EXACT',r['left']['id'],r['right']['id'],r['left']['title'])
