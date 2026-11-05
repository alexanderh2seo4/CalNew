#!/usr/bin/env python3
"""Resumable public-metadata harvest; explicit, auditable aroma scope, real citations only."""
import argparse, concurrent.futures as cf, collections, csv, datetime as dt, gzip, hashlib, html, json, math, os, random, re, sqlite3, threading, time
from pathlib import Path
from urllib.parse import quote
import requests

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data/atlas.sqlite'
BASE='https://www.ebi.ac.uk/europepmc/webservices/rest'
def review_paths():
 return [ROOT/'research'/name for name in ['scope_audit.json','parent_expansion_diagnostic_2026-10-27.json','crossref_parent_diagnostic_2026-10-27.json','display_year_diagnostic_2026-10-27.json','crossref_completion_diagnostic_2026-10-27.json','later_parent_diagnostic_2026-10-27.json','flavor_title_diagnostic_2026-10-27.json','citation_neighbor_scope_diagnostic_2026-10-27.json','pmid_neighbor_scope_diagnostic_2026-10-28.json','doi_growth_scope_diagnostic_2026-10-28.json','recall_parent_scope_diagnostic_2026-10-28.json','recall_routes_oct28/frozen_metadata_review.json','flavor_completion_scope_diagnostic_2026-10-30.json','product_consumer_scope_diagnostic_2026-10-30.json','pom_neighborhood_scope_diagnostic_2026-10-30.json','scope_readjudications_2026-10-27.json']]
CUTOFF='2026-10-26'
NAMED_AROMA=['linalool','limonene','eugenol','menthol','vanillin','anethole','camphor','geraniol','citral','farnesol','carvone','terpineol','pinene','citronellol','linalyl acetate','carvacrol','thymol','cinnamaldehyde','isoeugenol']
ALLOWLIST=ROOT/'research/named_aroma_allowlist_expanded.json'
EXPANDED_NAMES=[]
if ALLOWLIST.exists():
 EXPANDED_NAMES=list(dict.fromkeys(n for p in json.loads(ALLOWLIST.read_text())['chemicals'] for n in p['exact_parent_synonyms']))
 NAMED_AROMA=list(dict.fromkeys(NAMED_AROMA+EXPANDED_NAMES))
LEGACY_NAMED_NAMES=NAMED_AROMA.copy()
ADDITIONAL_ALLOWLIST=ROOT/'research/named_aroma_allowlist_2026-10-27_v2.json'
ADDITIONAL_NAMES=[]
if ADDITIONAL_ALLOWLIST.exists():
 ADDITIONAL_NAMES=list(dict.fromkeys(n for p in json.loads(ADDITIONAL_ALLOWLIST.read_text())['chemicals'] for n in p['exact_parent_synonyms']))
 NAMED_AROMA=list(dict.fromkeys(NAMED_AROMA+ADDITIONAL_NAMES))
V2_NAMES=NAMED_AROMA.copy()
LATEST_ALLOWLIST=ROOT/'research/named_aroma_allowlist_2026-10-27_v4.json'
LATEST_NAMES=[]
COUMARIN_ALIASES=set()
AMBIGUOUS_PRODUCTION_ALIASES=set()
if LATEST_ALLOWLIST.exists():
 _latest=json.loads(LATEST_ALLOWLIST.read_text())['chemicals']
 LATEST_NAMES=list(dict.fromkeys(n for p in _latest for n in p['exact_parent_synonyms']))
 COUMARIN_ALIASES={n.casefold() for p in _latest if p['name']=='coumarin' for n in p['exact_parent_synonyms']}
 AMBIGUOUS_PRODUCTION_ALIASES={n.casefold() for p in _latest if p['name'] in ('coumarin','benzyl alcohol') for n in p['exact_parent_synonyms']}
 NAMED_AROMA=list(dict.fromkeys(NAMED_AROMA+LATEST_NAMES))
FURTHER_ALLOWLIST=ROOT/'research/named_aroma_allowlist_2026-10-27_v5.json'
_further=json.loads(FURTHER_ALLOWLIST.read_text())['chemicals'] if FURTHER_ALLOWLIST.exists() else []
FURTHER_NAMES=list(dict.fromkeys(n for p in _further for n in p['exact_parent_synonyms']))
NAMED_AROMA=list(dict.fromkeys(NAMED_AROMA+FURTHER_NAMES))
V6_ALLOWLIST=ROOT/'research/named_aroma_allowlist_2026-10-28_v6.json'
_v6=json.loads(V6_ALLOWLIST.read_text())['chemicals'] if V6_ALLOWLIST.exists() else []
V7_ALLOWLIST=ROOT/'research/named_aroma_allowlist_2026-10-28_v7_musks.json'
_v7=json.loads(V7_ALLOWLIST.read_text())['chemicals'] if V7_ALLOWLIST.exists() else []
_new_parents=_v6+_v7
V6_NAMES=list(dict.fromkeys(n for p in _new_parents for n in p['exact_parent_synonyms']))
NAMED_AROMA=list(dict.fromkeys(NAMED_AROMA+V6_NAMES))
AMBIGUOUS_PRODUCTION_ALIASES.update(n.casefold() for n in V6_NAMES)
NAMED_RX=re.compile(r'(?<!\w)(?:'+ '|'.join(re.escape(x) for x in sorted(NAMED_AROMA,key=lambda x:(-len(x),x)))+r')(?!\w)',re.I)
PHARMA_RX=re.compile(r'\b(pharmacolog\w*|pharmacokinet\w*|pharmacodynam\w*|bioavailability|agonist\w*|antagonist\w*|receptor\w*|antimicrob\w*|antifung\w*|antibacter\w*|anti.inflamm\w*|neuroinflamm\w*|anticancer|anti.cancer|anti.tumou?r|antitumou?r|apoptosis|analges\w*|antinocicep\w*|anxiolytic\w*|neuroprotect\w*|cytotoxic\w*|therapeut\w*|anti.oxidant|antioxidant|bioactiv\w*|anti.viral|antiviral|anti.diabet\w*|antidiabet\w*|toxicolog\w*|toxicity|genotox\w*|mutagen\w*|carcinogen\w*|hepatotox\w*|nephrotox\w*|neurotox\w*|DNA.adduct\w*)\b',re.I)
PHYSICAL_RX=re.compile(r'\b(vapou?r.pressures?|volatility|vapou?r.liquid.equilibri\w*|liquid.liquid.equilibri\w*|partition.coefficient\w*|Henry.?s?\s+(?:law|constant\w*)|air.water.partition\w*|gas.liquid.partition\w*|activity.coefficient\w*|enthalp\w*\s+of\s+vapori[sz]ation|solubilit\w*|diffusion.coefficient\w*)\b',re.I)
QUERIES={
 'aroma':'TITLE_ABS:aroma OR TITLE_ABS:aromas',
 'fragrance':'TITLE_ABS:fragrance OR TITLE_ABS:fragrances OR TITLE_ABS:perfume OR TITLE_ABS:perfumery',
 'odorants':'TITLE_ABS:odorant OR TITLE_ABS:odorants OR TITLE_ABS:odourant OR TITLE_ABS:odourants OR TITLE_ABS:olfactophore OR TITLE_ABS:olfactophores',
 'odor_chemistry':'(TITLE_ABS:odor OR TITLE_ABS:odour OR TITLE_ABS:odors OR TITLE_ABS:odours) AND (TITLE_ABS:chemical OR TITLE_ABS:chemicals OR TITLE_ABS:molecule OR TITLE_ABS:molecules OR TITLE_ABS:compound OR TITLE_ABS:compounds OR TITLE_ABS:intensity OR TITLE_ABS:threshold OR TITLE_ABS:prediction)',
 'receptor_models':'TITLE_ABS:olfactory AND (TITLE_ABS:ligand OR TITLE_ABS:pharmacophore OR TITLE_ABS:binding OR TITLE_ABS:agonist OR TITLE_ABS:docking OR TITLE_ABS:structure OR TITLE_ABS:prediction)',
 'flavor_volatiles':'(TITLE_ABS:flavor OR TITLE_ABS:flavour) AND (TITLE_ABS:volatile OR TITLE_ABS:volatiles OR TITLE_ABS:olfactometry OR TITLE_ABS:odor OR TITLE_ABS:odour)',
 'odor_threshold':'(TITLE_ABS:olfactory OR TITLE_ABS:olfaction) AND (TITLE_ABS:threshold OR TITLE_ABS:concentration OR TITLE_ABS:intensity OR TITLE_ABS:QSAR OR TITLE_ABS:prediction)',
 'named_resources':'TITLE_ABS:DreamOlF OR TITLE_ABS:Pyrfume OR TITLE_ABS:GoodScents OR TITLE_ABS:FlavorDB OR TITLE_ABS:Flavornet OR TITLE_ABS:Leffingwell OR TITLE_ABS:OdorDB OR TITLE_ABS:OlfactionBase OR TITLE_ABS:OlfactoryDB OR TITLE_ABS:ODORactor OR TITLE_ABS:OlfactionBase',
 'scent_chemistry':'(TITLE_ABS:scent OR TITLE_ABS:scents OR TITLE_ABS:fragrant OR TITLE_ABS:smell) AND (TITLE_ABS:chemical OR TITLE_ABS:molecule OR TITLE_ABS:compound OR TITLE_ABS:intensity OR TITLE_ABS:threshold OR TITLE_ABS:prediction OR TITLE_ABS:volatile)',
 'named_aroma_pharmacology':'('+' OR '.join('TITLE:"'+x+'"' for x in LEGACY_NAMED_NAMES)+') AND (pharmacology OR pharmacological OR agonist OR receptor OR antimicrobial OR antifungal OR antibacterial OR anti-inflammatory OR anticancer OR antitumor OR apoptosis OR analgesic OR anxiolytic OR neuroprotective OR cytotoxic OR therapeutic OR antioxidant OR bioactivity OR antiviral OR antidiabetic)',
 'named_pharmacology_extension':'(TITLE:carvacrol OR TITLE:thymol OR TITLE:cinnamaldehyde OR TITLE:isoeugenol) AND (pharmacology OR pharmacological OR agonist OR receptor OR antimicrobial OR antifungal OR antibacterial OR anti-inflammatory OR anticancer OR antitumor OR apoptosis OR analgesic OR anxiolytic OR neuroprotective OR cytotoxic OR therapeutic OR antioxidant OR bioactivity OR antiviral OR antidiabetic)',
 'named_parent_pharmacology_expanded':'('+' OR '.join('TITLE:"'+x+'"' for x in EXPANDED_NAMES)+') AND (pharmacology OR pharmacological OR agonist OR receptor OR antimicrobial OR antifungal OR antibacterial OR anti-inflammatory OR anticancer OR antitumor OR apoptosis OR analgesic OR anxiolytic OR neuroprotective OR cytotoxic OR therapeutic OR antioxidant OR bioactivity OR antiviral OR antidiabetic)',
 'named_parent_production':'('+' OR '.join('TITLE:"'+x+'"' for x in LEGACY_NAMED_NAMES)+') AND (TITLE:synthesis OR TITLE:production OR TITLE:biosynthesis OR TITLE:biotransformation OR TITLE:fermentation)',
 'characterized_aroma_oils':'TITLE:"essential oil" AND ('+' OR '.join('TITLE_ABS:"'+x+'"' for x in LEGACY_NAMED_NAMES)+') AND (TITLE_ABS:"GC-MS" OR TITLE_ABS:chromatography OR TITLE_ABS:composition OR TITLE_ABS:constituents) AND (TITLE_ABS:pharmacological OR TITLE_ABS:antimicrobial OR TITLE_ABS:antifungal OR TITLE_ABS:antibacterial OR TITLE_ABS:anti-inflammatory OR TITLE_ABS:anticancer OR TITLE_ABS:antioxidant OR TITLE_ABS:fragrance OR TITLE_ABS:perfumery OR TITLE_ABS:aroma)',
}
# Versioned, bounded-size title routes retain old completed query evidence.
_vocab_hash=hashlib.sha256(json.dumps(V2_NAMES,ensure_ascii=False).encode()).hexdigest()[:10]
for _start in range(0,len(V2_NAMES),22):
 QUERIES[f'parent_titles_v2_{_vocab_hash}_{_start//22}']='('+' OR '.join('TITLE:"'+x+'"' for x in V2_NAMES[_start:_start+22])+')'
# Ambiguous multi-role parents use narrower discovery routes instead of a generic
# coumarin drug-family or benzyl-alcohol reagent crawl. Checkpoint by query text.
for _parent in (_latest if LATEST_ALLOWLIST.exists() else []):
 _query='('+' OR '.join('TITLE:"'+x+'"' for x in _parent['exact_parent_synonyms'])+')'
 _aroma='(TITLE_ABS:aroma OR TITLE_ABS:fragrance OR TITLE_ABS:perfume OR TITLE_ABS:odorant OR TITLE_ABS:flavor OR TITLE_ABS:flavour)'
 _physical='(TITLE:"vapor pressure" OR TITLE:"vapour pressure" OR TITLE:"vapor-liquid" OR TITLE:"liquid-liquid" OR TITLE:partition OR TITLE:solubility OR TITLE:volatility OR TITLE:Henry OR TITLE:"activity coefficient")'
 if _parent['name']=='coumarin':_query+=' AND (TITLE_ABS:"91-64-5" OR TITLE_ABS:"1,2-benzopyrone" OR '+_aroma+' OR '+_physical+')'
 elif _parent['name']=='benzyl alcohol':_query+=' AND (TITLE_ABS:pharmacology OR TITLE_ABS:toxicity OR TITLE_ABS:toxicology OR TITLE_ABS:pharmacokinetics OR TITLE_ABS:antimicrobial OR TITLE_ABS:antibacterial OR TITLE_ABS:receptor OR '+_aroma+' OR '+_physical+')'
 _hash=hashlib.sha256(_query.encode()).hexdigest()[:10]
 QUERIES['parent_titles_v4_'+_hash+'_'+re.sub(r'[^a-z0-9]+','_',_parent['name'])]=_query
for _parent in _further:
 _query='('+' OR '.join('TITLE:"'+x+'"' for x in _parent['exact_parent_synonyms'])+')'
 _hash=hashlib.sha256(_query.encode()).hexdigest()[:10]
 QUERIES['parent_titles_v5_'+_hash+'_'+re.sub(r'[^a-z0-9]+','_',_parent['name'])]=_query
for _parent in _new_parents:
 _query='('+' OR '.join('TITLE:"'+x+'"' for x in _parent['exact_parent_synonyms'])+')'
 _hash=hashlib.sha256(_query.encode()).hexdigest()[:10]
 QUERIES['parent_titles_v6_'+_hash+'_'+re.sub(r'[^a-z0-9]+','_',_parent['name'])]=_query
RX={
 'aroma':re.compile(r'\b(aroma|aromas|fragranc\w*|perfum\w*|olfactophor\w*|odorophor\w*)\b',re.I),
 'odor':re.compile(r'\b(odou?r(?:s|ants?|ous|iferous|i[sz]\w*|ogen\w*)?|olfactor\w*|olfaction|olfactive\w*|olfactometr\w*|smell\w*)\b',re.I),
 'chem':re.compile(r'\b(chemi\w*|molecul\w*|compound\w*|volatile\w*|ligand\w*|agonist\w*|antagonist\w*|binding|ingredient\w*|GC.MS|GC.O|terpen\w*|sesquiterpen\w*|monoterpen\w*|diterpen\w*|pyrazin\w*|alkylpyrazin\w*|ester\w*|aldehyde\w*|ketone\w*|alcohol\w*|lactone\w*|musk\w*|vanillin|eugenol|linalool|limonene|citral)\b',re.I),
 'potency':re.compile(r'\b(intensit\w*|threshold\w*|potency|potencies|dose.response|concentration.response|odor.activity|odour.activity|suprathreshold|psychophysic\w*|dilution|olfactometr\w*)\b',re.I),
 'prediction':re.compile(r'\b(predict\w*|QSAR|QSPR|machine.learning|deep.learning|neural.network|graph.neural|software|algorithm\w*|pharmacophor\w*|olfactophor\w*|odorophor\w*|docking|virtual.screen\w*|structure.activity|structure.odor|structure.odour|generative|computational|chemoinformat\w*|cheminformat\w*|modeling|modelling)\b',re.I),
 'resource':re.compile(r'\b(database\w*|dataset\w*|data.set\w*|benchmark\w*|pyrfume|flavornet|flavordb|leffingwell|good.?scents|odoractor|olfactionbase|odordb|dreamolf)\b',re.I),
 'receptor':re.compile(r'\b(receptor\w*|ligand\w*|agonist\w*|binding|pharmacolog\w*|pharmacophor\w*)\b',re.I),
 'flavor':re.compile(r'\b(flavo[u]?r\w*|taste\w*|food\w*|wine\w*|coffee|tea|fruit\w*|ferment\w*|beverage\w*)\b',re.I),
 'insect':re.compile(r'\b(insect\w*|mosquito\w*|drosophila|moth\w*|pheromon\w*|antenna\w*|bombyx|aedes|anopheles|pest\w*|lepidopter\w*|wasp\w*|herbivor\w*|parasitoid\w*|apis|honey.?bee\w*)\b',re.I),
 'outscope':re.compile(r'\b(olfactory.bulb|anosmia|parkinson\w*|alzheimer\w*|covid|sars.cov|olfactory.dysfunction|olfactory.ensheathing)\b',re.I),
}
LOCAL=threading.local()
def connect():
 c=sqlite3.connect(DB,timeout=90);c.execute('PRAGMA journal_mode=WAL');return c
def init():
 DB.parent.mkdir(exist_ok=True,parents=True)
 c=connect();c.executescript('''
 CREATE TABLE IF NOT EXISTS papers(id TEXT PRIMARY KEY,doi TEXT,title TEXT,year INTEGER,authors TEXT,journal TEXT,abstract TEXT,citations INTEGER,pmid TEXT,pmcid TEXT,source TEXT,source_id TEXT,category TEXT,tracks TEXT,evidence TEXT,accepted INTEGER,raw TEXT);
 CREATE INDEX IF NOT EXISTS paper_doi ON papers(doi);
 CREATE INDEX IF NOT EXISTS paper_pmid ON papers(pmid);
 CREATE INDEX IF NOT EXISTS paper_source_identity ON papers(source,source_id);
 CREATE TABLE IF NOT EXISTS provenance(paper TEXT,query TEXT,PRIMARY KEY(paper,query));
 CREATE TABLE IF NOT EXISTS queries(name TEXT PRIMARY KEY,query TEXT,cursor TEXT,hits INTEGER,seen INTEGER,complete INTEGER,updated TEXT);
 CREATE TABLE IF NOT EXISTS edges(source TEXT,target TEXT,provider TEXT,PRIMARY KEY(source,target,provider));
 CREATE TABLE IF NOT EXISTS refs(paper TEXT PRIMARY KEY,status TEXT,total INTEGER,retrieved INTEGER,updated TEXT,error TEXT);
 CREATE TABLE IF NOT EXISTS raw_refs(paper TEXT,target_source TEXT,target_id TEXT,doi TEXT,title TEXT,PRIMARY KEY(paper,target_source,target_id));
 CREATE TABLE IF NOT EXISTS source_alias(source TEXT,source_id TEXT,paper TEXT,PRIMARY KEY(source,source_id));
 CREATE TABLE IF NOT EXISTS identity_reference_archive(removed_paper TEXT PRIMARY KEY,kept_paper TEXT,source TEXT,source_id TEXT,refs_row TEXT,created TEXT);
 ''');c.commit();c.close()
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def clean(s):return re.sub('<[^>]+>',' ',html.unescape(s or '')).strip()
def secondary_abstract(title='',doi='',journal=''):
 doi=re.sub(r'^https?://(?:dx\.)?doi\.org/','',doi or '',flags=re.I).strip().lower()
 return bool(re.match(r'^\s*ChemInform\s+Abstract\s*:',title,re.I) or doi.startswith('10.1002/chin.') or (journal or '').strip().casefold()=='cheminform')
def chemical_text(s):
 """Normalize typography for identity guards while retaining original metadata."""
 s=s.translate(str.maketrans({x:'-' for x in '\u2010\u2011\u2012\u2013\u2014\u2212'}))
 return re.sub(r'\.(alpha|beta|gamma|delta|epsilon)\.',lambda m:m[1],s,flags=re.I)
def identified_parent(text):
 """Conservative constituent evidence; avoid named derivatives, absence and background."""
 text=chemical_text(text)
 for clause in re.split(r'[.;]',text):
  for match in NAMED_RX.finditer(clause):
   before=clause[max(0,match.start()-100):match.start()];after=clause[match.end():match.end()+70]
   if re.search(r'\b((?:(?:mono|di|tri|tetra)?(?:methyl|ethyl|propyl|butyl|pentyl|hexyl|phenyl|benzyl|acetyl|amino|methoxy|ethoxy|hydroxy|chloro|bromo|nitro))|o|m|p|epi|ent)[- ]$',before,re.I):continue
   if re.search(r'\b(?:co)?poly\s*[(\[][^)\]]*$',before,re.I):continue
   if re.match(r'\s*(?:[- ]?(?:oxide|glucoside|glycoside|derivative|hybrid|conjugate|schiff|polymer))\b',after,re.I):continue
   if re.search(r'\b(no|not|without|absence.of|undetectable|absent)\b(?:\W+\w+){0,4}\W*$',before,re.I):continue
   if re.search(r'\b(earlier|previously|previous.stud\w*|background|literature|other.oils)\b',clause[:match.start()],re.I):continue
   if re.search(r'\b(major|main|identified|detected|contained|contain|constituent\w*|component\w*|composed|rich)\b|\d\s*%',before+after,re.I):return True
 return False
def parent_in_title(text,exclude=None):
 text=chemical_text(text)
 for match in NAMED_RX.finditer(text):
  if exclude and match.group().casefold() in exclude:continue
  after=text[match.end():]
  if re.match(r'\s*[-–]\s*\d',after):continue
  if re.match(r'\s*(?:[- ]?(?:oxide|glucoside|glycoside|derivative|derived|based|hybrid|conjugate|schiff|polymer|compounds|esters?|citrate|blue|dyes?|lactone|glycol|metabolit\w*|rich|chemotype\w*|analog\w*|thiosemicarbazon\w*|hydrazon\w*|semicarbazon\w*))\b',after,re.I):continue
  before=text[:match.start()]
  if re.search(r'\b(?:co)?poly\s*[(\[][^)\]]*$',before,re.I):continue
  if match.group().casefold()=='humulene' and re.search(r'\b(?:beta|gamma|delta|β|γ|δ)-\s*$',before,re.I):continue
  if match.group().casefold()=='benzyl alcohol' and re.search(r'\ba\s+$',before,re.I):continue
  if re.search(r'\b((?:(?:mono|di|tri|tetra)?(?:methyl|ethyl|propyl|butyl|pentyl|hexyl|phenyl|benzyl|acetyl|amino|methoxy|ethoxy|hydroxy|chloro|bromo|nitro))|o|m|p|epi|ent)[- ]$',before,re.I):continue
  if re.search(r'[\])](?:\s*-\s*)?$',before) and not re.search(r'\(\s*(?:R|S|E|Z|cis|trans|rac|\+|-|±|[0-9,]*[RS])\s*\)\s*-?\s*$',before,re.I):continue
  if re.search(r'\bpoly\s*[([]\s*$',before,re.I):continue
  return True
 return False
def parent_production(title,abstract=''):
 title,abstract=chemical_text(title),chemical_text(abstract)
 if re.search(r'\b(labelled|labeled|deuter\w*|isotop\w*|radiolabel\w*)\b',title,re.I):return False
 if parent_in_title(title) and not parent_in_title(title,exclude=AMBIGUOUS_PRODUCTION_ALIASES) and not re.search(r'\b(aroma\w*|fragranc\w*|perfum\w*|odou?rants?|flavo[u]?r\w*)\b',title+' '+abstract,re.I):return False
 if re.search(r'\b(deriv\w*|based|ligands?|scaffold\w*|hybrid\w*|(?:co)?polymer\w*|polybenzoxazin\w*|polylimonen\w*|resins?|glucoside\w*|glycoside\w*|thiosemicarbazon\w*|hydrazon\w*)\b',title,re.I):return False
 for match in NAMED_RX.finditer(title):
  if not parent_in_title(match.group()+title[match.end():]):continue
  before=title[:match.start()];after=title[match.end():]
  if re.search(r'\b(?:synthesis|biosynthesis|production|bioproduction)(?:\s+and\s+characterization)?\s+of\s*(?:(?:optically|enantiomerically)\s+pure\s+)?[-+(),\sDLRSE0-9]*$',before,re.I):return True
  if re.match(r'\s*(biosynthesis|production|synthesis|fermentation)\b',after,re.I):return True
  if re.search(r'\b(biotransformation|bioconversion|conversion)\b',title,re.I) and re.search(r'\b(into|to)\s*(?:(?:optically|enantiomerically)\s+pure\s+)?[-+(),\sDLRSE0-9]*$',before,re.I):return True
 return False
def physical_parent_study(title):
 """A known unchanged odorant must be the physical-property target, not a solvent."""
 title=chemical_text(title)
 if not PHYSICAL_RX.search(title) or not parent_in_title(title):return False
 if re.search(r'\b(substitut\w*|deriv\w*|based|hydrazon\w*|thiosemicarbazon\w*|(?:co)?polymer\w*|polybenzoxazin\w*|polylimonen\w*|hydrogel\w*|nanoparticl\w*|deep.eutectic|DES|extract\w*|catalys\w*|scaffold\w*|cements?|adhesiv\w*|resins?|ozonolys\w*|photooxidat\w*|SOA|secondary.organic.aerosol\w*|oxidation.products?|reaction.products?|degradation.products?)\b',title,re.I):return False
 if re.search(r'\b(as\s+(?:(?:a|solid|liquid)\s+)*(?:co.?solvent|solvent)|(?:co.?solvent|solvent)\s+for)\b',title,re.I):return False
 # Solubility/diffusion of another compound in an odorant solvent is out of scope.
 if re.search(r'\b(solubilit\w*|diffusion.coefficient\w*)\b',title,re.I):
  subject=re.split(r'\b(in|using)\b',title,maxsplit=1,flags=re.I)[0]
  if not parent_in_title(subject):return False
  target=re.search(r'\bsolubilit\w*\s+of\s+(.+)',subject,re.I)
  if target and not parent_in_title(target[1]):return False
  if re.search(r'\b(modifier\w*|co.?solvent\w*|dissolv\w*|sealers?|sealants?|gutta.percha)\b',title,re.I) and not (target and parent_in_title(target[1])):return False
 return True
def self_contained_parent_title(title):
 return physical_parent_study(title) or parent_production(title) or (parent_in_title(title) and bool(PHARMA_RX.search(title)))
def self_contained_flavor_title(title):
 """Explicit volatile flavor chemistry can be unambiguous without an abstract."""
 title=chemical_text(title)
 volatile_text=re.sub(r'\bnon[-\s]*volatil\w*\b','',title,flags=re.I)
 return bool(re.search(r'\bflavo[u]?r\w*\b',title,re.I) and re.search(r'\bvolatil\w*\b',volatile_text,re.I) and re.search(r'\b(compounds?|molecul\w*|chemi\w*|profil\w*|composi\w*|chromatograph\w*|constituen\w*)\b|GC.MS',title,re.I))
def scent_chemistry(title,abstract=''):
 """Central scent chemistry, without granting scent the clinical/insect exceptions."""
 if re.search(r'\b(macrocyclic|polycyclic|synthetic|nitro)[- ]musks?\b',title,re.I) and re.search(r'\b(synthesis|syntheses|chemistry|structure\w*|olfact\w*|percept\w*|threshold\w*|intensit\w*|model\w*)\b',title,re.I):return True
 if not re.search(r'\b(scents?|scented|fragrant)\b',title,re.I):return False
 chemical_title=bool(re.search(r'\b(compounds?|molecul\w*|chemi\w*|volatil\w*|composi\w*|biosynth\w*|biochem\w*|terpen\w*|esters?|aldehydes?|ketones?|olfactometr\w*)\b',title,re.I))
 chemical_measurement=bool(re.search(r'GC.MS|GC.O|chromatograph\w*|mass.spectrom\w*|\bvolatile.compounds?\b',abstract,re.I) and RX['chem'].search(abstract))
 if re.search(r'\b(memory|emotions?|social|diagnos\w*|consumer\w*|navigat\w*|scent.mark\w*|scent.trail\w*)\b',title,re.I) and not chemical_title:return False
 return chemical_title or chemical_measurement

def direct_odor_ligand(title,abstract):
 """Chemical ligand/perception work can mention specific anosmia as background."""
 central=bool(re.search(r'\b(musks?|muscone|odou?rant.receptor\w*|olfactory.receptor\w*)\b',title,re.I))
 chemical=parent_in_title(abstract) or bool(re.search(r'\b(muscone|musks?|bourgeonal)\b',abstract,re.I))
 assay=bool(re.search(r'\b(activat\w*|agonis\w*|antagonis\w*|binding|in.vitro|detection.threshold|perceived.intensit\w*)\b',abstract,re.I))
 return central and chemical and assay

def chemical_olfactometry(title,abstract):
 """Auxiliary electronic-nose methods do not erase actual chemical GC-O studies."""
 return bool(re.search(r'olfactometr|GC.O',title+' '+abstract,re.I) and re.search(r'\b(volatile\w*|odorants?|odourants?|sesquiterpen\w*|terpen\w*)\b',abstract,re.I) and re.search(r'\b(compounds?|identified|chromatograph\w*|mass.spectrom\w*|intensit\w*|threshold\w*|docking)\b',abstract,re.I))
def classify(title,abstract):
 title,abstract=chemical_text(title),chemical_text(abstract)
 t=title+' '+abstract;m={k:bool(r.search(t)) for k,r in RX.items()};strong={k:bool(r.search(title)) for k,r in RX.items()}
 reasons=[]
 scent_core=scent_chemistry(title,abstract)
 ligand_core=direct_odor_ligand(title,abstract)
 # Require odor chemistry/perception. Generic drug pharmacology, smell disease,
 # neural circuit and insect-only chemosensation are excluded from the strict set.
 accepted=(m['aroma'] and (m['chem'] or m['potency'] or m['resource'])) or (m['odor'] and (m['chem'] or m['potency']))
 if scent_core:accepted=True;reasons.append('central scent/fragrant chemical composition or molecular study')
 flavor_volatile=bool(re.search(r'\bflavo[u]?r\w*\b',t,re.I) and re.search(r'\b(volatile\w*|olfactometr\w*)\b',re.sub(r'\bnon[-\s]*volatil\w*\b','',t,flags=re.I),re.I) and (strong['chem'] or re.search(r'\bflavo[u]?r\w*\b',title,re.I)))
 if flavor_volatile:accepted=True;reasons.append('flavor + volatile chemical characterization')
 if m['insect'] and not m['aroma'] and not re.search(r'\b(perfum\w*|fragranc\w*|food.aroma)\b',t,re.I) and not re.search(r'\bhuman\b.*\b(odorant|olfactory.receptor)',title,re.I): accepted=False;reasons.append('insect/pheromone-only context')
 if m['outscope'] and not strong['aroma'] and not ligand_core and not (strong['chem'] and bool(re.search(r'\bodou?rants?\b',title,re.I))) and not (strong['potency'] and strong['odor']):accepted=False;reasons.append('clinical/neural smell context without central aroma chemistry')
 clinical=bool(re.search(r'\b(cancer\w*|carcinoma\w*|tumou?r\w*|biomarker\w*|COPD|diagnos\w*|dementia|parkinson\w*|alzheimer\w*|anosmia|hyposmia|olfactory.dysfunction|surgery|polyposis|sinusitis|rhinosinusitis|schizophren\w*|autism)\b',title,re.I))
 if clinical and not strong['aroma'] and not (strong['chem'] and bool(re.search(r'\bodou?rants?\b',title,re.I))):accepted=False;reasons.append('clinical paper without central aroma molecule')
 if not (strong['aroma'] or strong['odor'] or scent_core or (strong['flavor'] and strong['chem'])) and not (len(RX['aroma'].findall(t))>=2 and m['chem']):accepted=False;reasons.append('incidental aroma mention')
 if re.search(r'\b(electronic.nose|e.nose|bioelectronic.nose|gas.sensor)\b',title,re.I) and not chemical_olfactometry(title,abstract) and not re.search(r'\b(aroma|fragranc\w*|perfum\w*|odorants?|odourants?|olfactophor\w*)\b',title,re.I):accepted=False;reasons.append('generic sensing hardware')
 if re.search(r'\b(neuroimag\w*|odou?r.memory|odou?r.evoked.memory|episodic.memory|emotional.potency)\b',title,re.I) and not strong['aroma'] and not NAMED_RX.search(title):accepted=False;reasons.append('general memory/neuroimaging without specific aroma molecule')
 if re.search(r'\b(promoter\w*|transcription.factor\w*|gene.regulat\w*|axon\w*|neuronal.adhesion|cell.adhesion|olfactory.cortex|cortical.slices?)\b',title,re.I) and not strong['aroma'] and not parent_in_title(title) and not strong['potency']:accepted=False;reasons.append('generic neural/gene regulation without central aroma ligand or intensity endpoint')
 if not m['odor'] and not m['aroma'] and not flavor_volatile and not scent_core:accepted=False
 named=parent_in_title(title)
 coumarin_proof=bool(re.search(r'91-64-5|\b1,2.benzopyrone\b|\b2H-1-benzopyran-2-one\b',t,re.I))
 named_pharma=parent_in_title(title,exclude=None if coumarin_proof else COUMARIN_ALIASES) and bool(PHARMA_RX.search(t))
 if re.search(r'\b(as\s+(?:(?:a|solid|liquid)\s+)*(?:co.?solvent|solvent|reagent|vehicle)|(?:co.?solvent|solvent|vehicle)\s+for)\b',title,re.I):named_pharma=False
 if re.search(r'\b(dissolut\w*|dissolv\w*|sealers?|sealants?|gutta.percha|root.canal.filling)\b',title,re.I) and not PHARMA_RX.search(title):named_pharma=False
 if re.search(r'\b(catalys\w*|benzylation|esterification|transesterification|hydrogenation)\b',title,re.I) and not PHARMA_RX.search(title):named_pharma=False
 if re.search(r'\b(aggregation|unfolding|stability|formulation)\b',title,re.I) and re.search(r'\b(recombinant|antibod\w*|therapeutic.protein)\b',title,re.I):named_pharma=False
 if re.search(r'\b\w*hydrazon\w*\b',title,re.I):named_pharma=False
 if re.search(r'\b(derived.from|derivatives?.of)\b',title,re.I):named_pharma=False
 if re.search(r'\b(determination|quantif\w*|fluorescen\w*|spectrofluor\w*)\b',title,re.I) and re.search(r'\b(derivati[sz]\w*|condensation.with|fluorescen\w*.prob\w*|reagents?)\b',t,re.I):named_pharma=False
 if named_pharma and not re.search(r'\b(cigarette\w*|smoking|smoker\w*|tobacco|(?:co)?polymer\w*|polybenzoxazin\w*|polylimonen\w*|polyurethane\w*|scaffold\w*|hybrid\w*|derivative\w*|derivati[sz]\w*|reagents?|precursor\w*|conjugated.addition|michael.addition|addition.of.thiols|substitut\w*|analog(?:ue)?s?|thiosemicarbazon\w*|semicarbazon\w*|hydrazon\w*|extract\w*|ruthenium\w*|rhodium\w*|palladium\w*|platinum\w*|organometallic\w*|cements?|PCR|barcod\w*|phylogenet\w*|genetic.diversity)\b',title,re.I):
  accepted=True;reasons.append('established parent aroma chemical in title + pharmacological activity')
 else:named_pharma=False
 named_production=named and parent_production(title,abstract)
 if named_production:accepted=True;reasons.append('established parent aroma molecule production in title')
 if re.search(r'\b(wastewater|sewage|sewer\w*|landfill\w*|manure|compost\w*|paddy|activated.sludge|algal.bloom|soil.remediat\w*|protective.distance|swine|pig.slurr\w*|piggery\w*|poultry.litter|livestock|animal.housing|dairy.farm\w*|industrial.odou?r\w*|urban.odou?r\w*|drinking.water|surface.water|water.treatment|water.suppl\w*|water.quality|lakes?|reservoir\w*|rivers?|ponds?|dissolved.organic.matter)\b',title,re.I) and not strong['aroma'] and not named_production and not (named_pharma and PHARMA_RX.search(title)):accepted=False;reasons.append('environmental occurrence/engineering context without central aroma ingredient purpose')
 if re.search(r'\b(herbicid\w*|biofilter\w*|animal.rendering|seabird\w*|crosslink\w*|cross.link\w*|polyvinyl|polyurethane\w*|schiff.base|(?:co)?polymer\w*|polybenzoxazin\w*|polylimonen\w*)\b',title,re.I) and not strong['aroma']:accepted=False;reasons.append('environmental/materials context outside aroma chemical purpose')
 if re.search(r'\b(bitterness|astringen\w*|umami|nonvolatile|non.volatile)\b',title+' '+abstract,re.I) and not strong['aroma'] and not re.search(r'\bvolatile\w*\b',re.sub(r'\bnon[-\s]*volatil\w*\b','',title,flags=re.I),re.I) and not named_pharma and not named_production:accepted=False;reasons.append('nonvolatile taste chemistry without central aroma characterization')
 if re.search(r'\b(crossmodal|language|metaphor\w*|attribution.circle)\b',title,re.I) and not strong['chem'] and not NAMED_RX.search(title):accepted=False;reasons.append('conceptual crossmodal scent design without molecular research')
 if re.search(r'\b(robot\w*|swarm\w*|source.locali[sz]ation|odor.source.tracking|odour.source.tracking|piriform.cortex|synaptic.transmission)\b',title,re.I) and not strong['aroma'] and not named_pharma:accepted=False;reasons.append('robotic navigation or generic neural physiology')
 if re.search(r'\b(recommend\w*|shopping|purchase\w*|structural.equation|consumer.preference\w*)\b',title,re.I) and not m['chem']:accepted=False;reasons.append('consumer preference/model without molecular evidence')
 if re.search(r'\b(structural.equation|shopping|purchase\w*|recommend\w*)\b',title,re.I) and not (NAMED_RX.search(abstract) or re.search(r'\b(molecul\w*|compounds?|volatiles?|SMILES|GC.MS)\b',abstract,re.I)):accepted=False;reasons.append('product-level consumer/sensory model lacks identified chemical evidence')
 oil_profile=bool(re.search(r'\bessential.oils?\b',title,re.I) and identified_parent(abstract) and re.search(r'GC.MS|chromatograph|composi\w*|constituen\w*',abstract,re.I) and (PHARMA_RX.search(t) or m['aroma']))
 if oil_profile and not strong['insect'] and not re.search(r'\b(insecticid\w*|spodoptera|(?:co)?polymer\w*|polybenzoxazin\w*|polylimonen\w*|packaging|films?|crosslink\w*)\b',title,re.I):accepted=True;reasons.append('essential oil chemical profile identifies established parent aroma molecule + bioactivity/aroma purpose')
 else:oil_profile=False
 if named and re.search(r'\b(removal|sorption|adsorpt\w*|degrad\w*|photocatal\w*|Fenton)\b',title,re.I) and not strong['aroma'] and not PHARMA_RX.search(title) and not named_production:accepted=False;reasons.append('parent odorant removal/reaction engineering without central pharmacology or aroma purpose')
 physical=physical_parent_study(title)
 if physical:accepted=True;reasons.append('verified parent odorant is the explicitly named volatility/partition-property target')
 if (strong['insect'] or re.search(r'\b(aphicid\w*|Musca.domestica|Bactrocera|Phthorimaea|insects?|fumigant|coleopter\w*|tribolium|insect.repellent|insecticid\w*|insectistatic|spodoptera|aedes|anopheles|fleas?|ticks?|acaricid\w*|larvicid\w*|nematicid\w*|pesticid\w*|housefl\w*|storage.insects?|stored.product.insects?)\b',title,re.I)) and not strong['aroma'] and not re.search(r'\bhuman\b.*\b(odorant|olfactory.receptor)',title,re.I):accepted=False;oil_profile=False;reasons.append('pest-control bioactivity outside perfume/aroma pharmacology')
 if re.search(r'\bISBN(?:[- ](?:10|13))?\b',title,re.I):accepted=False;reasons.append('bibliographic book-review title rather than qualifying research record')
 if strong['odor'] and re.search(r'\b(squid|octopus|cuttlefish|cephalopod\w*|lobster\w*|crayfish|crustacean\w*|sea.urchin\w*)\b',title,re.I) and not (strong['aroma'] or strong['flavor'] or named_pharma or re.search(r'\bhuman\b.*\b(odorant|olfactory.receptor)',title,re.I)):accepted=False;reasons.append('non-mammalian ecological chemosensation without aroma ligand or purpose')
 if re.match(r'^\s*(retract\w*|correction\b|corrigendum\b|erratum\b|author.correction\b)',title,re.I):accepted=False;reasons.append('non-research publication notice')
 # Final contextual gates prevent generic molecular/psychophysical vocabulary
 # from admitting disease tests, neural anatomy, gas hardware or social cues.
 # Verified parent chemistry/pharmacology and characterized oils keep their
 # independent routes; an odor-detection test alone is not aroma chemistry.
 clinical_context=bool(re.search(r'\b(covid\w*|coronavirus|sars.cov\w*|neuroblastoma|esthesioneuroblastoma|bulbectom\w*|ESRD|uremi\w*|renal.disease|neuropathic.pain|multiple.chemical.sensitivity|antidepressant\w*|smell.and.taste.recovery|olfactory.dysfunction|olfactory.impairment|impaired.olfactory|olfactory.function\w*)\b',title,re.I))
 fragrance_ligand_pharma=bool(strong['aroma'] and parent_in_title(abstract) and re.search(r'\b(inhibit\w*|binding|antivir\w*|antimicrob\w*|receptor\w*|pharmacolog\w*)\b',abstract,re.I))
 if clinical_context and not (named_pharma or oil_profile or physical or fragrance_ligand_pharma):accepted=False;reasons.append('clinical function/recovery or disease model without central established aroma chemical')
 generic_hardware=bool(re.search(r'\b(artificial.olfact\w*|chemi.memrist\w*|chemiresistor\w*|neuromorphic\w*)\b',title,re.I) and re.search(r'\b(gas.sens\w*|semiconductor\w*|memrist\w*|chemiresistor\w*|synaptic\w*)\b',t,re.I))
 if generic_hardware and not chemical_olfactometry(title,abstract) and not (strong['aroma'] or named or re.search(r'\bodou?rants?\b',title,re.I)):accepted=False;reasons.append('generic artificial-olfaction gas hardware without aroma chemical target')
 if re.search(r'\b(sensor\w*|electronic.nose)\b',title,re.I) and re.search(r'\bartificial.olfact\w*\b',title,re.I) and not (chemical_olfactometry(title,abstract) or named or strong['aroma']):accepted=False;reasons.append('generic artificial-olfactory sensor review without central aroma chemistry')
 generic_biology=bool(strong['odor'] and re.search(r'\b(neurogenes\w*|proteom\w*|immunocytochem\w*|cell.and.molecular.biology|chloride.channel\w*|olfactory.signaling.molecules|olfactory.signalling.molecules)\b',title,re.I))
 odor_ligand_experiment=bool(re.search(r'\b(discrete.odou?rants?|odou?r.blends?|musk.odou?rs?|aroma.compounds?)\b',abstract,re.I) and re.search(r'\b(agonis\w*|antagonis\w*|binding|expos\w*|stimulat\w*|concentration.response)\b',abstract,re.I))
 if generic_biology and not (strong['aroma'] or named or re.search(r'\bodou?rants?\b',title,re.I) or odor_ligand_experiment):accepted=False;reasons.append('generic olfactory cellular biology without aroma ligand chemistry')
 behavior_context=bool(re.search(r'\b(social.preferences?|assessment.of.people|socialization|alcoholism|alcoholic.drink\w*|body.weight|preschool\w*|fMRI|PET.CT|cortical.activity)\b',title,re.I))
 if behavior_context and not (named_pharma or oil_profile or physical or (named and strong['potency'])):accepted=False;reasons.append('social/clinical odor-cue study without central aroma chemical endpoint')
 if re.search(r'\b(forensic\w*|hand.scent|conspecific.odou?rs?)\b',title,re.I) and not (strong['aroma'] or named_pharma):accepted=False;reasons.append('forensic/social odor signatures without central perfume chemical endpoint')
 if re.search(r'\b(packaging|films?|poly\s*[(\[]|CS/PVA)\b',title,re.I) and re.search(r'\b(schiff.base|crosslink\w*|cross.link\w*|covalent\w*|structural.modif\w*)\b',abstract,re.I) and not strong['aroma']:accepted=False;reasons.append('structurally modified polymer/material rather than unchanged parent aroma chemical')
 if strong['odor'] and re.search(r'\b(monoclonal.antibod\w*|globose.basal.cells?|carbon.monoxide)\b',title,re.I) and not ligand_core:accepted=False;reasons.append('generic neural messenger/cell-marker biology without aroma ligand')
 if re.search(r'\b(occurrence|fate|monitor\w*|residues?)\b',title,re.I) and re.search(r'\b(aquatic|environment\w*|sediment\w*|sewage|surface.water|marine)\b',title,re.I) and not (named_pharma and PHARMA_RX.search(title)):accepted=False;reasons.append('environmental occurrence/fate of residues rather than central aroma chemical endpoint')
 if secondary_abstract(title):accepted=False;reasons.append('secondary abstracting record, not the original research publication')
 tracks=['aroma'] if accepted else []
 if accepted and m['prediction']:tracks.append('prediction')
 fragrance_safety=bool(re.search(r'\b(safety.assessment|safety.evaluation|skin.sensiti\w*|skin.absorption|contact.allerg\w*|sensitization|sensitisation|risk.assessment|exposure|dermal|genotox\w*|toxicity|toxicolog\w*)\b',title,re.I)) and m['aroma']
 if physical:
  cat='Volatility & partitioning'
  tracks=['aroma']+(['prediction'] if strong['prediction'] else []) if accepted else []
 elif oil_profile and not strong['aroma'] and not strong['odor']:
  cat='Characterized aroma oils'
  tracks=['pharmacology'] if accepted else []
 elif named_production and not named_pharma:
  cat='Fragrance & aroma chemistry'
  tracks=['aroma'] if accepted else []
 elif fragrance_safety:
  tracks=['pharmacology'] if accepted else []
  cat='Fragrance safety & pharmacology'
 elif named_pharma and not (strong['aroma'] or strong['odor']):cat='Aroma chemical pharmacology';tracks=['pharmacology'] if accepted else []
 elif strong['resource'] or (m['resource'] and strong['prediction']):cat='Databases & benchmarks'
 elif m['prediction'] and m['receptor']:cat='Receptors & pharmacophores'
 elif m['prediction']:cat='Molecular prediction'
 elif m['potency']:cat='Intensity & thresholds'
 elif m['flavor']:cat='Food & flavor chemistry'
 elif m['receptor']:cat='Odorant receptor chemistry'
 else:cat='Fragrance & aroma chemistry'
 reasons += [k+' term in title/abstract' for k in ['aroma','odor','chem','potency','prediction','resource'] if m[k]]
 return accepted,cat,tracks,reasons

def review_exclusions():
 review={}
 for audit_path in review_paths():
  if audit_path.exists():
   for r in json.loads(audit_path.read_text()).get('records',[]):
    if r.get('verdict') in ('out-of-scope','uncertain'):
     # An explicit negative takes precedence over uncertainty across samples.
     if r['id'] not in review or r['verdict']=='out-of-scope':review[r['id']]=r
 resolution=ROOT/'research/scope_readjudications_2026-10-27.json'
 if resolution.exists():
  for r in json.loads(resolution.read_text()).get('resolutions',[]):
   old=review.get(r.get('id'))
   if old and old['verdict']=='uncertain' and r.get('verdict')=='in-scope' and r.get('reason') and r.get('sources') and r.get('date'):
    review.pop(r['id'])
 return review

def merge_identity(c,old,keep,merges):
 """Move actual references/aliases to a proved existing identity, preserving checkpoints."""
 if old==keep:return
 old_source,old_sid=c.execute('SELECT source,source_id FROM papers WHERE id=?',(old,)).fetchone()
 keep_source=c.execute('SELECT source FROM papers WHERE id=?',(keep,)).fetchone()[0]
 prior=c.execute('SELECT * FROM refs WHERE paper=?',(old,)).fetchone()
 if prior:
  c.execute('INSERT OR IGNORE INTO identity_reference_archive VALUES(?,?,?,?,?,?)',(old,keep,old_source,old_sid,json.dumps(prior),now()))
  # Another provider's no-reference flag cannot complete a new native MED lookup.
  if old_source==keep_source:c.execute('INSERT OR IGNORE INTO refs SELECT ?,status,total,retrieved,updated,error FROM refs WHERE paper=?',(keep,old))
 c.execute('INSERT OR IGNORE INTO provenance SELECT ?,query FROM provenance WHERE paper=?',(keep,old));c.execute('DELETE FROM provenance WHERE paper=?',(old,))
 c.execute('INSERT OR IGNORE INTO raw_refs SELECT ?,target_source,target_id,doi,title FROM raw_refs WHERE paper=?',(keep,old));c.execute('DELETE FROM raw_refs WHERE paper=?',(old,))
 c.execute('DELETE FROM refs WHERE paper=?',(old,))
 c.execute('INSERT OR IGNORE INTO edges SELECT ?,target,provider FROM edges WHERE source=?',(keep,old));c.execute('INSERT OR IGNORE INTO edges SELECT source,?,provider FROM edges WHERE target=?',(keep,old));c.execute('DELETE FROM edges WHERE source=? OR target=?',(old,old))
 c.execute('DELETE FROM papers WHERE id=?',(old,));merges[old]=keep
 c.execute('UPDATE source_alias SET paper=? WHERE paper=?',(keep,old))
 tables={x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
 for table in ['semantic_ids','openalex_ids']:
  if table in tables:c.execute(f'UPDATE {table} SET paper=? WHERE paper=?',(keep,old))

def identity_paths():
 return [ROOT/'research'/n for n in ['verified_bibliographic_merges_2026-10-28.json','bibliographic_identity_audit_2026-10-28.json','secondary_abstract_eligibility_2026-10-28.json','bibliographic_merges_applied_2026-10-30.json']]

def rescreen():
 """Run after writers finish: exact identifiers and frozen full-bibliographic proofs."""
 c=connect();merges={};review=review_exclusions()
 manifest=identity_paths()[0]
 if manifest.exists():
  import bibliographic_identity
  proven=bibliographic_identity.validated_pairs(c,manifest)
 else:proven=[]
 c.execute('INSERT OR IGNORE INTO source_alias SELECT source,source_id,id FROM papers')
 for old,keep,proof in proven:merge_identity(c,old,keep,merges)
 for field in ['doi','pmid']:
  for value, in c.execute(f"SELECT {field} FROM papers WHERE {field}!='' GROUP BY {field} HAVING count(*)>1").fetchall():
   group=c.execute(f"SELECT id,source,length(abstract) FROM papers WHERE {field}=? ORDER BY CASE WHEN source='MED' THEN 0 WHEN source='Crossref' THEN 2 ELSE 1 END,length(abstract) DESC",(value,)).fetchall();keep=group[0][0]
   for old,*_ in group[1:]:merge_identity(c,old,keep,merges)
 counts=collections.Counter()
 for pid,title,abstract,raw,source,doi,journal in c.execute('SELECT id,title,abstract,raw,source,doi,journal FROM papers').fetchall():
  accepted,cat,tracks,evidence=classify(title,abstract)
  try:
   p=json.loads(raw);types=p.get('pubTypeList',{}).get('pubType',[])
   if any(v in ' '.join(types).lower() for v in ['patent','book review','retract','erratum']):accepted=False;evidence.append('excluded publication type')
   if source=='Crossref' and 'DOI' in p:
    import supplement
    accepted,cat,tracks,evidence,*_=supplement.classify_record(p)
   if source=='SemanticScholar':
    import semantic
    accepted,cat,tracks,evidence,*_=semantic.classify(p)
   if source=='OpenAlex':
    import openalex
    accepted,cat,tracks,evidence,*_=openalex.classify(p)
  except Exception as exc:accepted=False;evidence.append('source eligibility parse failed: '+str(exc)[:160])
  if secondary_abstract(title,doi,journal):accepted=False;tracks=[];evidence.append('secondary abstracting record, not original research')
  if pid in review:accepted=False;tracks=[];evidence.append('AI diagnostic review exclusion ('+review[pid]['verdict']+'): '+review[pid]['reason'])
  c.execute('UPDATE papers SET accepted=?,category=?,tracks=?,evidence=? WHERE id=?',(int(accepted),cat,json.dumps(tracks),json.dumps(evidence),pid));counts[int(accepted)]+=1
 c.execute('DELETE FROM edges WHERE source=target OR source NOT IN (SELECT id FROM papers WHERE accepted=1) OR target NOT IN (SELECT id FROM papers WHERE accepted=1)');c.commit();c.close()
 (ROOT/'data/identity_merges.json').write_text(json.dumps(merges,indent=2));print({'rescreen':dict(counts),'merged':len(merges)},flush=True)
def get(url,params=None):
 if not hasattr(LOCAL,'session'):
  LOCAL.session=requests.Session();LOCAL.session.headers['User-Agent']='AromaResearchAtlas/1.0 (public scholarly metadata research)'
 for attempt in range(7):
  try:
   r=LOCAL.session.get(url,params=params,timeout=(20,120))
   if r.status_code in (429,500,502,503,504):
    time.sleep(min(60,float(r.headers.get('Retry-After',2**attempt))+random.random()));continue
   r.raise_for_status();d=r.json()
   if isinstance(d,dict) and d.get('errCode'):raise ValueError(str(d))
   return d
  except (requests.RequestException,ValueError):
   if attempt==6:raise
   time.sleep(min(30,2**attempt))
 raise RuntimeError('retry limit')
def ingest(rows,name):
 c=connect()
 for p in rows:
  title=clean(p.get('title'));ab=clean(p.get('abstractText'));doi=(p.get('doi') or '').lower();pmid=str(p.get('pmid') or '');source=p.get('source','');sid=str(p.get('id',''))
  alias=c.execute('SELECT a.paper,p.source FROM source_alias a JOIN papers p ON p.id=a.paper WHERE a.source=? AND a.source_id=?',(source,sid)).fetchone()
  if source=='AGR' and alias and alias[1]=='MED':
   c.execute('INSERT OR IGNORE INTO provenance VALUES(?,?)',(alias[0],name));continue
  # Prefer stable PMID, otherwise DOI, then source identifier.
  pid='pmid:'+pmid if pmid else 'doi:'+doi if doi else source+':'+sid
  accepted,cat,tracks,evidence=classify(title,ab)
  typ=' '.join(p.get('pubTypeList',{}).get('pubType',[])).lower()
  if any(v in typ for v in ['patent','book review','retract','erratum']):accepted=False;evidence.append('excluded publication type')
  ji=p.get('journalInfo') or {};j=(ji.get('journal') or {}).get('title') or p.get('journalTitle','')
  if secondary_abstract(title,doi,j):accepted=False;evidence.append('secondary abstracting record')
  c.execute('INSERT OR REPLACE INTO papers VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(pid,doi,title,int(p.get('pubYear') or 0),p.get('authorString',''),j,ab,p.get('citedByCount',0),pmid,p.get('pmcid',''),source,sid,cat,json.dumps(tracks),json.dumps(evidence),int(accepted),json.dumps(p,separators=(',',':'))))
  c.execute('INSERT OR IGNORE INTO provenance VALUES(?,?)',(pid,name))
 c.commit();c.close()
def harvest_one(item):
 name,query=item;query='('+query+') AND FIRST_PDATE:[1800-01-01 TO '+CUTOFF+'] AND (SRC:MED OR SRC:PMC OR SRC:PPR OR SRC:AGR)'
 c=connect();old=c.execute('SELECT cursor,hits,seen,complete FROM queries WHERE name=?',(name,)).fetchone();c.close()
 if old and old[3]:return name,old[2]
 cursor=old[0] if old else '*';seen=old[2] if old else 0
 while True:
  d=get(BASE+'/search',{'query':query,'format':'json','resultType':'core','pageSize':1000,'cursorMark':cursor})
  if 'resultList' not in d:raise ValueError('missing resultList '+str(d)[:200])
  rows=d['resultList'].get('result',[]);ingest(rows,name);seen+=len(rows);nxt=d.get('nextCursorMark');done=not rows or not nxt or nxt==cursor
  c=connect();c.execute('INSERT OR REPLACE INTO queries VALUES(?,?,?,?,?,?,?)',(name,query,nxt or cursor,d['hitCount'],seen,int(done),now()));c.commit();c.close()
  print(json.dumps({'stage':'harvest','query':name,'seen':seen,'hits':d['hitCount'],'complete':done}),flush=True)
  if done:return name,seen
  cursor=nxt
def harvest(workers):
 with cf.ThreadPoolExecutor(max_workers=workers) as ex:
  for f in cf.as_completed([ex.submit(harvest_one,x) for x in QUERIES.items()]):print({'finished':f.result()},flush=True)
def reference_one(p):
 pid,src,sid=p;c=connect();old=c.execute('SELECT status FROM refs WHERE paper=?',(pid,)).fetchone();c.close()
 if old and old[0]=='complete':return
 try:
  page=1;count=0;total=0
  while True:
   d=get(f'{BASE}/{src}/{sid}/references',{'format':'json','pageSize':1000,'page':page})
   total=int(d.get('hitCount',0));rows=d.get('referenceList',{}).get('reference',[])
   c=connect()
   for r in rows:
    rs=r.get('source','');ri=str(r.get('id') or '');doi=(r.get('doi') or '').lower()
    if not ri:rs='DOI' if doi else 'unresolved';ri=doi or hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()
    c.execute('INSERT OR REPLACE INTO raw_refs VALUES(?,?,?,?,?)',(pid,rs,ri,doi,clean(r.get('title'))))
   c.commit();c.close();count+=len(rows)
   if not rows or count>=total:break
   page+=1
  c=connect();c.execute('INSERT OR REPLACE INTO refs VALUES(?,?,?,?,?,?)',(pid,'complete',total,count,now(),''));c.commit();c.close()
 except Exception as e:
  c=connect();c.execute('INSERT OR REPLACE INTO refs VALUES(?,?,?,?,?,?)',(pid,'error',0,0,now(),str(e)[:500]));c.commit();c.close()
def references(workers,limit):
 c=connect();unavailable=0
 for pid,raw in c.execute("SELECT p.id,p.raw FROM papers p LEFT JOIN refs r ON p.id=r.paper WHERE p.accepted=1 AND p.source IN ('MED','PMC','PPR','AGR') AND r.paper IS NULL").fetchall():
  if json.loads(raw).get('hasReferences')=='N':
   c.execute('INSERT OR IGNORE INTO refs VALUES(?,?,?,?,?,?)',(pid,'complete',0,0,now(),'Europe PMC metadata: hasReferences=N; bibliography availability unknown beyond source'));unavailable+=1
 c.commit();print({'stage':'references','source_flag_no_indexed_references':unavailable},flush=True)
 q='''SELECT p.id,p.source,p.source_id FROM papers p LEFT JOIN refs r ON p.id=r.paper WHERE p.accepted=1 AND p.source IN ('MED','PMC','PPR','AGR') AND (r.status IS NULL OR r.status!='complete') ORDER BY CASE WHEN p.category IN ('Databases & benchmarks','Molecular prediction','Receptors & pharmacophores') THEN 0 ELSE 1 END,p.citations DESC'''
 rows=c.execute(q).fetchall();c.close()
 if limit:rows=rows[:limit]
 print({'stage':'references','pending':len(rows)},flush=True)
 with cf.ThreadPoolExecutor(max_workers=workers) as ex:
  for i,_ in enumerate(ex.map(reference_one,rows),1):
   if i%100==0:print(json.dumps({'stage':'references','processed':i,'planned':len(rows),'time':now()}),flush=True)
 resolve()
def resolve():
 c=connect()
 provider="CASE WHEN r.target_source='Crossref' THEN 'Crossref deposited reference list' WHEN r.target_source='SemanticScholar' THEN 'Semantic Scholar reference list' WHEN r.target_source='OpenAlex' THEN 'OpenAlex referenced_works' ELSE 'Europe PMC reference list' END"
 c.execute(f"INSERT OR IGNORE INTO edges SELECT r.paper,p.id,{provider} FROM raw_refs r JOIN papers p ON (r.target_source=p.source AND r.target_id=p.source_id) JOIN papers s ON s.id=r.paper WHERE p.accepted=1 AND s.accepted=1 AND r.paper!=p.id")
 c.execute("INSERT OR IGNORE INTO edges SELECT r.paper,p.id,'Europe PMC reference list' FROM raw_refs r JOIN papers p ON r.target_source='MED' AND r.target_id=p.pmid JOIN papers s ON s.id=r.paper WHERE p.accepted=1 AND s.accepted=1 AND r.paper!=p.id")
 c.execute(f"INSERT OR IGNORE INTO edges SELECT r.paper,p.id,{provider} FROM raw_refs r JOIN papers p ON r.doi=p.doi JOIN papers s ON s.id=r.paper WHERE r.doi!='' AND p.accepted=1 AND s.accepted=1 AND r.paper!=p.id")
 c.execute(f"INSERT OR IGNORE INTO edges SELECT r.paper,p.id,{provider} FROM raw_refs r JOIN source_alias a ON a.source=r.target_source AND a.source_id=r.target_id JOIN papers p ON p.id=a.paper JOIN papers s ON s.id=r.paper WHERE p.accepted=1 AND s.accepted=1 AND r.paper!=p.id")
 # An explicitly proved provider DOI redirect is an identity alias. Citation
 # provenance still comes from the actual original reference, not the redirect.
 c.execute(f"INSERT OR IGNORE INTO edges SELECT r.paper,p.id,{provider} FROM raw_refs r JOIN source_alias a ON a.source='DOI' AND a.source_id=r.doi JOIN papers p ON p.id=a.paper JOIN papers s ON s.id=r.paper WHERE r.doi!='' AND p.accepted=1 AND s.accepted=1 AND r.paper!=p.id")
 tables={x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
 for table,col,source in [('openalex_ids','openalex_id','OpenAlex'),('semantic_ids','semantic_id','SemanticScholar')]:
  if table in tables:c.execute(f"INSERT OR IGNORE INTO edges SELECT r.paper,p.id,{provider} FROM raw_refs r JOIN {table} a ON a.{col}=r.target_id JOIN papers p ON p.id=a.paper JOIN papers s ON s.id=r.paper WHERE r.target_source=? AND p.accepted=1 AND s.accepted=1 AND r.paper!=p.id",(source,))
 c.execute("INSERT OR IGNORE INTO edges SELECT source,target,'Crossref deposited reference list' FROM edges WHERE provider='Crossref deposited references'");c.execute("DELETE FROM edges WHERE provider='Crossref deposited references'")
 c.execute('DELETE FROM edges WHERE source=target OR source NOT IN (SELECT id FROM papers WHERE accepted=1) OR target NOT IN (SELECT id FROM papers WHERE accepted=1)')
 c.commit();c.close()
def export():
 import networkx as nx
 import numpy as np
 from reference_coverage import collect as collect_reference_coverage,status as reference_status
 resolve();c=connect();c.row_factory=sqlite3.Row
 papers=[dict(x) for x in c.execute('SELECT * FROM papers WHERE accepted=1 ORDER BY id')];ids={p['id'] for p in papers}
 ref_coverage=collect_reference_coverage(c,ids)
 edges=sorted({(s,t) for s,t in c.execute('SELECT source,target FROM edges') if s in ids and t in ids})
 G=nx.Graph();G.add_nodes_from(sorted(ids));G.add_edges_from(edges);ind=collections.Counter(t for s,t in edges);out=collections.Counter(s for s,t in edges)
 counts=collections.Counter(p['category'] for p in papers);cats=sorted(counts);rng=np.random.default_rng(42)
 # Topology-derived communities/layout for connected core; category rings for isolates.
 components=sorted(nx.connected_components(G),key=len,reverse=True)
 active=[n for n in G if G.degree(n)>0];H=G.subgraph(active)
 groups=nx.community.louvain_communities(H,seed=42) if len(H) else []
 groups=sorted(groups,key=lambda g:(-len(g),min(g)));membership={n:i for i,g in enumerate(groups) for n in g}
 pos={};centers={};ng=max(1,len(groups))
 for i,g in enumerate(groups):
  a=2.3999632297*i;r=(5+2*math.sqrt((i-18)/max(1,ng-18))) if i>=18 else (3.5 if ng>1 else 0)
  centers[i]=(r*math.cos(a),r*math.sin(a));sub=H.subgraph(g)
  if len(g)<=1200:lp=nx.spring_layout(sub,seed=42,iterations=35,scale=max(.4,math.sqrt(len(g))/22))
  else:
   # A force layout of real citation landmarks, with neighbors around their
   # barycenters, avoids collapsed eigenvectors and an n^2 full-graph simulation.
   scale=max(1.2,math.sqrt(len(g))/24)
   landmarks=sorted(sub,key=lambda n:(-sub.degree(n),n))[:350]
   lp=dict(nx.spring_layout(sub.subgraph(landmarks),seed=42,iterations=55,scale=scale))
   for n in sorted(g,key=lambda n:(-sub.degree(n),n)):
    if n in lp:continue
    neighbors=[lp[v] for v in sub.neighbors(n) if v in lp]
    center=np.mean(neighbors,axis=0) if neighbors else np.zeros(2)
    lp[n]=center+rng.normal(0,scale*.28,2)
  cx,cy=centers[i]
  for n,v in lp.items():pos[n]=(cx+float(v[0]),cy+float(v[1]))
 for p in papers:
  if p['id'] not in pos:
   k=cats.index(p['category']);a=2*math.pi*k/len(cats)+rng.normal(0,.16);r=8.5+rng.uniform(0,2.5)
   pos[p['id']]=(r*math.cos(a),r*math.sin(a))
 nodes=[];details={}
 for idx,p in enumerate(papers):
  pid=p['id'];x,y=pos[pid];url='https://doi.org/'+quote(p['doi'],safe='/') if p['doi'] else f'https://europepmc.org/article/{p["source"]}/{p["source_id"]}'
  source_url=('https://api.crossref.org/works/'+quote(p['doi'],safe='/') if p['source']=='Crossref' else p['source_id'] if p['source']=='OpenAlex' else 'https://www.semanticscholar.org/paper/'+p['source_id'] if p['source']=='SemanticScholar' else f'https://europepmc.org/article/{p["source"]}/{p["source_id"]}')
  if not p['doi']:url=source_url
  node={k:p[k] for k in ['id','title','year','doi','citations','category']} | {'url':url,'sourceUrl':source_url,'degree':ind[pid]+out[pid],'inDegree':ind[pid],'outDegree':out[pid],'tracks':json.loads(p['tracks']),'x':round(x,5),'y':round(y,5),'community':membership.get(pid,-1),'detailShard':idx//500,'referenceStatus':reference_status(pid,ref_coverage)}
  nodes.append(node);details.setdefault(idx//500,{})[pid]={'authors':p['authors'],'journal':p['journal'],'abstract':p['abstract'],'evidence':json.loads(p['evidence'])}
 processed=len(ref_coverage['processed']);available=len(ref_coverage['available'])
 stats={'candidates':c.execute('SELECT count(*) FROM papers').fetchone()[0],'accepted':len(nodes),'papers':len(nodes),'edges':len(edges),'connectedPapers':len(active),'isolates':len(nodes)-len(active),'components':len(components),'largestComponent':len(components[0]) if components else 0,'predictionPapers':sum('prediction' in n['tracks'] for n in nodes),'referenceRequests':c.execute("SELECT count(*) FROM refs r JOIN papers p ON p.id=r.paper WHERE r.status='complete' AND p.source IN ('MED','PMC','PPR','AGR')").fetchone()[0],'referenceListsProcessed':processed,'referenceListsAvailable':available,'referenceErrors':len(ref_coverage['errors']),'rawReferences':c.execute('SELECT count(*) FROM raw_refs').fetchone()[0],'referenceCoverage':round(processed/max(1,len(nodes)),4),'availableReferenceCoverage':round(available/max(1,len(nodes)),4),'collectedAt':now(),'cutoff':CUTOFF,'source':'Europe PMC and Crossref','categories':dict(counts),'queries':[dict(x) for x in c.execute('SELECT name,query,hits,seen,complete FROM queries')],'scopeNote':'Automated title/abstract screening, not manual verification. Food aroma and pharmacology/production of listed parent aroma molecules included. Generic pharmacology, smell disease, insect-only pheromones, nonvolatile taste and environmental odor engineering excluded by rules. Literature indexed through 2026-10-26. Real directed citations from Europe PMC and Crossref deposited reference lists. Missing references are unknown; no exhaustive coverage claim. Preprints may coexist with journal versions when no exact identity link is available.'}
 stats['referenceCoverageDefinition']=ref_coverage['definition']
 stats['referenceCoverageByProvider']=ref_coverage['providers']
 stats['sources']=[dict(x) for x in c.execute('SELECT source,accepted,count(*) count FROM papers GROUP BY source,accepted')]
 stats['citationProviders']=[dict(x) for x in c.execute('SELECT provider,count(*) count FROM edges GROUP BY provider')]
 stats['source']='Europe PMC, Crossref, OpenAlex; limited Semantic Scholar metadata'
 stats['scopeNote']='Automated title/abstract screening; not manual verification or exhaustive coverage. Food aroma, named parent aroma chemical pharmacology/production and volatility/partition properties, and identified aroma-oil profiles included as separate themes. Generic drugs, smell disease, insect-only pheromones, taste-only and environmental odor engineering excluded by rules. Literature cutoff 26 Oct 2026. Real citations from Europe PMC, Crossref and OpenAlex. Missing references are unknown. Some preprint/journal versions remain distinct.'
 stats['referenceRequests']=c.execute("SELECT count(*) FROM refs r JOIN papers p ON p.id=r.paper WHERE r.status='complete' AND p.source IN ('MED','PMC','PPR','AGR') AND r.error NOT LIKE 'Crossref%' AND r.error NOT LIKE 'Europe PMC metadata%'").fetchone()[0]
 stats['rawReferencesAccepted']=c.execute('SELECT count(*) FROM raw_refs r JOIN papers p ON p.id=r.paper WHERE p.accepted=1').fetchone()[0]
 stats['queryCompletion']={}
 tables={x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
 for table in ['queries','crossref_queries','semantic_queries','openalex_queries']:
  if table in tables:stats['queryCompletion'][table]=[dict(x) for x in c.execute('SELECT * FROM '+table)]
 data={'nodes':nodes,'edges':edges,'stats':stats,'communities':[{'id':i,'size':len(g)} for i,g in enumerate(groups)]}
 outdir=ROOT/'site/dist';outdir.mkdir(exist_ok=True,parents=True)
 (outdir/'details').mkdir(exist_ok=True)
 for shard,values in details.items():(outdir/'details'/f'{shard:05d}.json').write_text(json.dumps(values,separators=(',',':'),ensure_ascii=False))
 for old in (outdir/'details').glob('[0-9][0-9][0-9][0-9][0-9].json'):
  if int(old.stem) not in details:old.unlink()
 (outdir/'edges').mkdir(exist_ok=True);shards=[]
 for start in range(0,len(edges),50000):
  path=f'edges/{start//50000:05d}.json';(outdir/path).write_text(json.dumps(edges[start:start+50000],separators=(',',':')));shards.append(path)
 data['edges']=[];data['edgeShards']=shards
 for old in (outdir/'edges').glob('[0-9][0-9][0-9][0-9][0-9].json'):
  if str(old.relative_to(outdir)) not in shards:old.unlink()
 tmp=outdir/'graph.json.tmp';tmp.write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False));tmp.replace(outdir/'graph.json')
 with gzip.open(ROOT/'data/graph.json.gz','wt',encoding='utf8') as f:json.dump(data,f,separators=(',',':'),ensure_ascii=False)
 (ROOT/'data/stats.json').write_text(json.dumps(stats,indent=2))
 with open(ROOT/'data/papers.csv','w',newline='') as f:
  fields=['id','title','year','doi','url','authors','journal','category','degree','inDegree','outDegree','citations'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(n|details[n['detailShard']][n['id']] for n in nodes)
 with open(ROOT/'data/citations.csv','w',newline='') as f:
  w=csv.writer(f);w.writerow(['citing_paper','cited_paper','provider']);w.writerows((s,t,p) for s,t,p in c.execute('SELECT source,target,provider FROM edges') if s in ids and t in ids)
 DG=nx.DiGraph();DG.add_nodes_from((n['id'],{k:n[k] for k in ['title','year','doi','category']}|{'label':n['title']}) for n in nodes);DG.add_edges_from(edges)
 nx.write_gexf(DG,ROOT/'data/aroma-citations.gexf')
 print(json.dumps(stats,indent=2),flush=True);c.close()
def main():
 a=argparse.ArgumentParser();a.add_argument('command',choices=['harvest','references','export','all','status','rescreen']);a.add_argument('--workers',type=int,default=5);a.add_argument('--limit',type=int,default=0);args=a.parse_args();init()
 if args.command in ['harvest','all']:harvest(args.workers)
 if args.command=='all':
  rescreen()
  import supplement
  supplement.anchors()
 if args.command in ['references','all']:references(args.workers,args.limit)
 if args.command in ['export','all']:export()
 if args.command=='rescreen':rescreen()
 if args.command=='status':
  c=connect()
  for label,q in [('papers','SELECT accepted,count(*) FROM papers GROUP BY accepted'),('queries','SELECT name,hits,seen,complete FROM queries'),('references','SELECT status,count(*) FROM refs GROUP BY status'),('edges','SELECT count(*) FROM edges')]:print(label,c.execute(q).fetchall())
if __name__=='__main__':main()
