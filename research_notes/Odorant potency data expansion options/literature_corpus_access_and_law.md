# Literature corpus access and law: mining the primary literature for odor potency data (thresholds, OAV, FD factors)

Status: research notes, compiled 2026-09-26. Not legal advice. The law is presented factually. Numbers from live API queries are marked "(live query 2026-09-26)" and can be reproduced with the URLs given.

Method note for the live queries: OpenAlex `https://api.openalex.org/works?filter=title_and_abstract.search:<terms>&group_by=<field>` and `filter=fulltext.search:<terms>`; Europe PMC `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=<q>&format=json` (hitCount). The union query was: "odor threshold" | "odour threshold" | "odor activity value" | "odour activity value" | "aroma extract dilution analysis" | "flavor dilution factor" | "flavour dilution factor" | "olfactometry" | "odor detection threshold" | "odour detection threshold" | "aroma activity value". The scripts are in the session scratchpad (oa.py, oa2.py, oa3.py, ep.py); they are not saved in the vault.

---

## 1. How big is the relevant literature, and where is it published?

### Takeaway
About 10,000 works name an odor-potency term in the title or abstract, and about 27,000 name one somewhere in the full text. The corpus is concentrated in a few food-chemistry journals. The core journals are overwhelmingly paywalled: J Agric Food Chem is ~93% closed and Food Chemistry is ~86% closed. Among publishers, Elsevier, ACS and Wiley dominate the closed part. The relevant flavor-chemistry set is probably 5,000–8,000 papers once noise is removed (estimate). It is growing quickly, at ~850 papers per year in 2025–2026.

### Cited Findings
- **Per-term counts in OpenAlex, title + abstract** (live query 2026-09-26; total / OA / closed) — [OpenAlex API](https://api.openalex.org/works?filter=title_and_abstract.search:%22odor%20activity%20value%22&group_by=open_access.is_oa):
  - "odor threshold": 1,954 / 618 / 1,336
  - "odour threshold": 593 / 207 / 386
  - "odor activity value": 2,748 / 1,404 / 1,344
  - "odour activity value": 426 / 183 / 243
  - "aroma extract dilution analysis": 1,050 / 306 / 744
  - "flavor dilution factor": 182 / 64 / 118
  - "flavour dilution factor": 56 / 8 / 48
  - "GC-olfactometry": 470 / 146 / 324
  - "gas chromatography-olfactometry": 1,917 / 697 / 1,220
  - "odor detection threshold": 369 / 177 / 192
  - "odor intensity": 1,810 / 784 / 1,026
- **Per-term counts in OpenAlex, full text** (`fulltext.search`; the plain `search=` parameter returned the same numbers, live query 2026-09-26; total / OA / closed) — [OpenAlex API](https://api.openalex.org/works?filter=fulltext.search:%22odor%20threshold%22&group_by=open_access.is_oa):
  - "odor threshold": 8,739 / 7,300 / 1,439
  - "odour threshold": 3,657
  - "odor activity value": 5,408 / 4,039 / 1,369
  - "aroma extract dilution analysis": 3,219 / 2,460 / 759
  - "flavor dilution": 1,049
  - "olfactometry": 13,823
  - "odor detection threshold": 1,631
- **Union, title + abstract: 9,945 works.** 4,120 are OA (41%) and 5,825 closed. By OA type: closed 5,825, gold 1,636, green 1,203, bronze 524, hybrid 445, diamond 312. Restricted to journal articles from 2000 on, the union has 7,504 works, of which 3,267 (44%) are OA (live query) — [OpenAlex API](https://api.openalex.org/works?filter=title_and_abstract.search:%22odor%20threshold%22%7C%22odor%20activity%20value%22&group_by=open_access.oa_status).
- **Union, full-text search: 27,033 works**, of which 20,927 are OA and 6,106 closed (live query). This number is heavily biased toward OA, because OpenAlex can only full-text search works whose text it holds. In the title/abstract union only 2,447 of 9,945 had `has_fulltext = true` — [OpenAlex API](https://api.openalex.org/works?filter=fulltext.search:%22odor%20threshold%22&group_by=open_access.is_oa).
- **Top journals, title/abstract union** (live query; count, then OA / closed where queried):
  - J Agric Food Chem: 704 (OA 46 / closed 658)
  - Food Chemistry: 539 (OA 77 / closed 462)
  - SSRN (preprints of Elsevier submissions): 300
  - Food Research International: 295 (OA 45 / closed 250)
  - Foods (MDPI): 263, all OA
  - LWT: 216 (OA 142 / closed 74)
  - Flavour and Fragrance Journal: 173 (closed 149)
  - Food Chemistry X: 142, all OA
  - J Food Science: 135
  - Eur Food Res Technol: 134 (closed 121)
  - Molecules: 127, all OA
  - ACS Symposium Series: 122
  - J Food Compos Anal: 110
  - Food Bioscience: 103
  - J Sci Food Agric: 99
  - Water Sci Technol: 88
  - Chemical Senses: 85
  - J Chromatogr A: 84
  - Chem Eng Transactions: 71
  - Eur Arch Oto-Rhino-Laryngology: 54

  Source: [OpenAlex API](https://api.openalex.org/works?filter=title_and_abstract.search:%22odor%20threshold%22&group_by=primary_location.source.id).
- **By publisher, title/abstract union** (live query; total, then OA / closed):
  - Elsevier: 2,726 (812 / 1,914), plus the "RELX" SSRN entry with 300 more
  - Wiley: 966 (284 / 682)
  - ACS: 905 (66 / 839)
  - MDPI: 638, all OA
  - Springer: 574 (145 / 429)
  - Taylor & Francis: 207
  - Oxford UP: 168 (65 / 103)
  - Frontiers: 89
  - Nature Portfolio: 49

  Source: [OpenAlex API](https://api.openalex.org/works?filter=title_and_abstract.search:%22odor%20threshold%22&group_by=primary_location.source.host_organization).
- **By publisher, full-text union** (live query): Elsevier 4,667, MDPI 3,583, Wiley 2,166, Springer 1,167, ACS 1,043, Frontiers 687, OUP 455, T&F 422, Nature Portfolio 387.
- **By year, title/abstract union** (live query): 2026: 871, 2025: 843, 2024: 645, 2023: 531, 2022: 518, 2021: 424, 2020: 418, 2019: 360; about 150–350 per year across 2001–2018. The 2026 figure is already above 2025 in September, so some indexing or date artefacts are possible.
- **Europe PMC, same union query** (live query 2026-09-26) — [Europe PMC REST API](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22odor%20activity%20value%22&format=json):
  - any field: 9,718 hits
  - title/abstract: 4,576
  - with full text in Europe PMC (IN_EPMC:y): 5,808
  - OPEN_ACCESS:y: 5,130
  - METHODS section only: 2,315
  - preprints: 84
- **Europe PMC per journal** (live query): JAFC 701 hits, only 36 with full text in Europe PMC. Food Chem 467, only 4 OA. Foods 1,001. Molecules 442. Chem Senses 91, of which 52 have full text in Europe PMC.

### Inferences
- A realistic target corpus is **~8,000–12,000 candidate papers**. That covers the title/abstract union plus full-text-only mentions in food-chemistry journals. Of these, perhaps **5,000–8,000** would contain quantitative odor-potency tables (a rough estimate, not measured).
- The union contains noise. "Olfactometry" also covers dynamic olfactometry for environmental odour emissions (Water Sci Technol, Chem Eng Transactions). "Odor intensity" also covers clinical smell testing (Eur Arch ORL). Filter by OpenAlex topic/concept or by journal.
- **Many papers reuse thresholds rather than measure them.** Most OAV papers divide measured concentrations by thresholds cited from the literature: van Gemert, Rychlik et al., and Grosch/Schieberle-group determinations. Mining OAV papers will mostly re-surface the same few thousand literature thresholds, often with the citation chain available. Papers with newly measured thresholds are a much smaller subset: the Munich/Freising (Leibniz-LSB@TUM) group, Chemical Senses psychophysics, and synthetic-odorant structure-odor studies. FD factors and OAVs are matrix- and study-specific. They are useful for "potency in context" labels, not as intrinsic molecular properties.
- The most valuable journals (JAFC, Food Chemistry, Flavour Fragr J, Eur Food Res Technol, J Food Sci) are almost entirely closed. OA full text alone gives broad but shallow coverage: MDPI Foods/Molecules, Food Chem X, LWT, and Frontiers. It misses much of the high-quality German flavor-chemistry literature in JAFC and EFRT.

### Gaps
- There is no direct count of papers that contain *numeric tables* of thresholds, OAVs or FD factors. That needs sampling, for example by pulling 200 random hits and annotating them.
- OpenAlex full-text coverage for closed papers is incomplete, so the true number of full-text mentions in paywalled papers is unknown and probably much higher than 6,106.
- Unpaywall was not queried separately. OpenAlex's `open_access` fields are derived from Unpaywall data, so the numbers should be comparable.

---

## 2. How much is open-access full text, and which corpora offer bulk access?

### Takeaway
Roughly 40–45% of the title/abstract-matched literature is OA in some form. Only about a third of it has a clean reuse licence: CC BY is 1,500 of 9,945 works as the best OA location. The best machine-readable OA routes are:
- the Europe PMC and PMC OA subsets (JATS XML, bulk FTP/S3, about 5,100 OA hits for this topic);
- MDPI;
- S2ORC through the Semantic Scholar Datasets API.

Together these would cover roughly 4,000–6,000 relevant OA papers. Very few of them are in JAFC or Food Chemistry.

### Cited Findings
- **Licence of the best OA location, title/abstract union** (live query): CC BY 1,500, CC BY-NC-ND 621, CC BY-NC 175, CC BY-SA 161, "other OA" 152, CC BY-NC-SA 35, CC0 17, CC BY-ND 5. The rest are bronze or green with no licence, or closed — [OpenAlex API](https://api.openalex.org/works?filter=title_and_abstract.search:%22odor%20threshold%22&group_by=best_oa_location.license).
- **Europe PMC licences, union query** (live query): OA and CC BY 3,760, CC BY-NC 416, CC BY-NC-ND 874, CC0 15.
- **Europe PMC**:
  - A REST API (XML/JSON) covers search, metadata, and full text, figures and supplementary files for OA articles.
  - The OA full-text XML set can be bulk-downloaded from the Europe PMC FTP site, and a bulk PDF download for the OA subset was added.
  - Content is updated daily.

  Sources: [Europe PMC bulk downloads](https://europepmc.org/downloads); [Europe PMC in 2023, NAR](https://pmc.ncbi.nlm.nih.gov/articles/PMC10767826/).
- **Europe PMC rate limit**: no numeric limit is officially published. Third-party tooling reports ~10 requests/s per IP and describes throttling after bursts. Treat this as uncertain — [Europe PMC webservices group](https://groups.google.com/a/ebi.ac.uk/g/epmc-webservices/c/cZLnV1JhCj8); [GitHub issue on throttling](https://github.com/hherb/bmlibrarian_lite/issues/341).
- **PMC OA subset (NCBI)**:
  - It contains articles and preprints under CC or similar licences, with terms that vary by article.
  - Bulk retrieval is allowed only through the Cloud (AWS) service, OAI-PMH, E-utilities and the BioC API. Other systematic or automated bulk retrieval is prohibited, and users are responsible for licence compliance.

  Source: [PMC OA subset page](https://pmc.ncbi.nlm.nih.gov/tools/openftlist/).
- **S2ORC (Semantic Scholar)**: available as a continuously rebuilt "Bulk Dataset" through the Semantic Scholar Datasets API. It comes as monthly snapshots of gzipped JSON with parsed sections, paragraphs and table/figure references, under ODC-By 1.0. Users must check that the underlying content permits their use — [allenai/s2orc README](https://github.com/allenai/s2orc/blob/master/README.md); [Semantic Scholar Open Data Platform paper](https://arxiv.org/pdf/2301.10140).
- **OpenAlex itself** holds full text for only a minority of these works (2,447 of 9,945 have `has_fulltext`). It is a discovery and OA-location index, not a full-text source (live query).
- Preprints are marginal: Europe PMC shows 84 preprint hits for the union query. SSRN's 300 works are mostly Elsevier-submitted preprints (live queries).

### Inferences
- **Practical OA pipeline:**
  1. Use OpenAlex to find DOIs, `best_oa_location`, `pdf_url` and licence.
  2. Use Europe PMC `fullTextXML` (JATS) for anything with a PMCID.
  3. Use MDPI, Frontiers and Food Chem X/LWT OA HTML or PDF directly from the publisher.
  4. Use PDFs from repositories for green OA.

  Tables in JATS XML are structured (`<table-wrap>`). That matters because threshold, OAV and FD data sit almost entirely in tables. PDFs need table extraction (GROBID, or a vision/LLM parser) and will be noticeably noisier.
- The CC BY-NC(-ND) share (~25–30% of licensed OA) does not block mining. Mining is a reproduction covered by statute in the EU (section 4), and the extracted numbers are facts. It matters only if you want to redistribute article text itself.
- CORE (core.ac.uk) mostly aggregates repository copies, adding green-OA PDFs. It overlaps heavily with OpenAlex/Unpaywall locations.

### Gaps
- CORE bulk-dataset terms and size were not verified in this session. Nor were the MDPI and Frontiers bulk/JATS access terms, or the arXiv/ChemRxiv/bioRxiv bulk buckets.
- There is no exact count of how many OA hits actually have JATS XML rather than PDF only.

---

## 3. Routes and costs for bulk full text of paywalled content (publisher TDM)

### Takeaway
For a German university researcher, bulk access to the paywalled core is feasible at little or no cost through Elsevier, Wiley and Springer Nature. All three have self-service academic TDM for subscribed content: an API key or token plus a click-through licence. ACS publishes about 90% of the key JAFC content. It does not allow platform crawling and delivers TDM content per project or for a fee, so JAFC is the bottleneck. Commercial TDM costs extra with every publisher.

### Cited Findings
- **Elsevier (ScienceDirect)**:
  - Researchers at subscribing academic institutions can text-mine full text for non-commercial research, through an API key from the Elsevier developer portal (self-registration). Full text is delivered as XML.
  - Non-subscribers can request access case by case. Corporate use goes through account managers.

  Source: [Elsevier TDM policy](https://www.elsevier.com/about/policies-and-standards/text-and-data-mining).

  Elsevier states there is no hard download cap but a "reasonable and customary" rate limit, and it can deactivate abusive keys. One library guide cites a 20,000 records/week limit, which may vary by agreement — [Elsevier TDM FAQ](https://www.elsevier.com/about/policies-and-standards/text-and-data-mining/faq); [NYU TDM guide](https://guides.nyu.edu/tdm/elsevier). Treat the 20k/week figure as uncertain.
- **Wiley**:
  - Academic subscribers use their ORCID to get an API token after accepting Wiley's click-through TDM licence. They then download subscribed articles, historically routed via the Crossref Text and Data Mining links.

  Source: [University of Minnesota guide](https://libguides.umn.edu/text-mining); [Cranfield publisher TDM policies](https://library.cranfield.ac.uk/text-and-data-mining/publisher-policies).

  The Wiley librarian TDM page returned 403 to automated fetch, so this is not verified first-hand.
- **Springer Nature**:
  - Researchers may download subscription and OA content for TDM directly from the platform.
  - An API key is needed only for the TDM APIs, which allow up to 150 requests/min.
  - The TDM API "incurs additional costs", and commercial TDM through it is paid.

  Source: [University of Minnesota guide](https://libguides.umn.edu/text-mining).

  The Springer Nature Data Solutions full-text API (JSON/XML/plain text) is sold as subscription plans: usage-based for startups, custom enterprise plans, and "premium" for academia and government. Prices are on request — [Springer Nature TDM API](https://datasolutions.springernature.com/products/tdm/).
- **ACS (JAFC, J Nat Prod, ACS Symposium Series)**:
  - ACS handles TDM "on a project by project basis". Instead of allowing TDM on its platform, it delivers the content for each project to the PI (contact [contact omitted]) — [Cranfield publisher TDM policies](https://library.cranfield.ac.uk/text-and-data-mining/publisher-policies).
  - The commercial ACS TDM product delivers JATS XML for journals and BITS XML for books, for a fee that depends on breadth, duration, frequency and delivery. It can be combined with "ACS All Access" — [ACS Solutions: Text & Data Mining](https://solutions.acs.org/solutions/text-and-data-mining/).
  - ACS Terms of Use restrict TDM without permission — [ACS Terms of Use](https://pubs.acs.org/page/policy/termsofuse.html).
- **DEAL (Germany)**:
  - Wiley contract from 2019, Springer Nature from 2020, Elsevier signed 2023 and running to end-2028, with ~900 eligible German institutions — [DEAL contracts](https://deal-konsortium.de/vertraege); [DEAL Elsevier](https://deal-konsortium.de/vertraege/elsevier); [MPG on DEAL-Elsevier](https://openaccess.mpg.de/deal-elsevier-vertrag).
  - The Springer Nature DEAL agreement allows a member institution to add a TDM amendment for non-commercial TDM by authorised users, based on the publisher's TDM conditions. These conditions are designed not to restrict users' non-waivable statutory rights — [Editorial on DEAL contracts, PFG](https://link.springer.com/article/10.1007/s41064-020-00125-w).
  - As a consequence, DEAL makes new articles by German corresponding authors in Wiley, Springer Nature and Elsevier journals OA, often CC BY.
- **LMU library (UB LMU)**: its general e-media terms allow saving full texts for personal, teaching and research use. They prohibit systematic downloading, especially by robots, and direct researchers to contact the library about the legal situation and specific TDM licence terms — [UB LMU e-media](https://www.ub.uni-muenchen.de/ausleihe-online/e-medien-login/index.html).
- **Comparison: another German library's reading of §60d.** UB Leipzig states that its licensed resources may be used for TDM under §60d regardless of conflicting contract clauses if the contracts date from after 28 Feb 2018. Use must be research, not commercial — [UB Leipzig TDM](https://www.ub.uni-leipzig.de/recherche/text-und-data-mining).

### Inferences
- **Cost for an academic user (LMU):**
  - Elsevier, Wiley and Springer Nature platform/API: likely €0 beyond existing subscriptions and DEAL.
  - Springer Nature's premium TDM API and any ACS TDM delivery: likely a fee or a negotiated agreement. Price unknown.
  - Commercial reuse or a spin-off: paid licences from all publishers.
- **Order of work for the paywalled ~5,800 title/abstract hits:**
  1. Elsevier API: Food Chem, Food Res Int, LWT, JFCA, Food Biosci, ~1,900 closed.
  2. Wiley token: Flavour Fragr J, J Food Sci, JSFA, ~680 closed.
  3. Springer: EFRT, ~430 closed.
  4. ACS project request for JAFC plus ACS Symposium Series, ~840 closed. Start early, because it is a human process.
  5. OUP for Chemical Senses and T&F: case by case.
- Even where a contract says "no robots", §60d + §60g UrhG (section 4) mean contract terms cannot bar research TDM on lawfully accessible content. §60d(6), however, lets publishers apply technical measures such as throttling or blocking to protect their systems. In practice the cooperative API route is far more reliable than asserting the exception against a blocking platform.
- LLM-based table extraction costs are now likely larger than access costs for ~10k papers. An estimate is not included here.

### Gaps
- Not confirmed whether LMU has opted into the Springer Nature DEAL TDM amendment. Also unconfirmed: the exact TDM clauses in the Wiley and Elsevier DEAL contracts, and whether LMU subscribes to the full ACS journal package. Ask UB LMU (e-media/licensing team) directly.
- Not verified first-hand: current Elsevier API quotas, the Wiley TDM API rate limits, and the RSC, Taylor & Francis and OUP TDM terms (fetches blocked or not attempted).

---

## 4. Legal framework: Germany/EU, and the US briefly

### Takeaway
**Research TDM.** In Germany, §60d UrhG (implementing Art. 3 of the EU DSM Directive) lets research organisations and individual non-commercial researchers make copies of lawfully accessible works for TDM. Contracts cannot override this (§60g), and rightsholders cannot opt out, though they may take security measures.

**General TDM.** §44b (Art. 4) allows TDM by anyone, including commercial users, unless a machine-readable opt-out exists. The mining copies must be deleted when no longer needed.

**Extracted facts.** Numeric facts such as thresholds are not protected by copyright. Wholesale extraction from a compiled database such as van Gemert or the LSB@TUM Odorant Database can infringe the sui generis database right outside the TDM exceptions.

**Status of the model.** A model or dataset built by mining is a separate question from the mining copies. Commercial exploitation is less clearly covered, and litigation (Kneschke v LAION) is still ongoing.

### Cited Findings
- **§44b UrhG**:
  - (1) Defines TDM as automated analysis of digital works to extract information "in particular about patterns, trends and correlations".
  - (2) Reproductions of lawfully accessible works for TDM are permitted but must be deleted when no longer required.
  - (3) Use is allowed only if the rightsholder has not reserved it. For online works the reservation is effective only in machine-readable form.

  Source: [§44b UrhG](https://www.gesetze-im-internet.de/urhg/__44b.html).
- **§60d UrhG**:
  - Reproductions for TDM for scientific research are permitted.
  - Beneficiaries are non-commercial research organisations. Organisations under controlling influence of a private company that has preferential access to results are excluded. Libraries, museums and archives are also covered, as are individual researchers pursuing non-commercial aims.
  - Copies may be shared with a defined group for joint research and with third parties for quality verification.
  - Copies may be stored with adequate security for as long as needed for research or verification.
  - (6) Rightsholders may take measures to protect network and database security.

  Source: [§60d UrhG](https://www.gesetze-im-internet.de/urhg/__60d.html).
- **§60g(1) UrhG**: rightsholders cannot rely on agreements that restrict or prohibit permitted uses under §§60a–60f to the users' detriment — [§60g UrhG](https://www.gesetze-im-internet.de/urhg/__60g.html).
- **§87c UrhG (database makers' right)**:
  - Reproduction of substantial parts of a database is permitted for TDM under §44b.
  - It is also permitted for research under §60c and for research TDM under §60d.
  - §60g(1) applies accordingly for the research cases, so contracts cannot override those either.

  Source: [§87c UrhG](https://www.gesetze-im-internet.de/urhg/__87c.html).
- **EU DSM Directive 2019/790**:
  - Art. 3 is the research TDM exception.
  - Art. 4 is the general TDM exception with rightsholder reservation.
  - Art. 7(1) makes contractual provisions contrary to Art. 3 unenforceable.

  Source: [EUR-Lex 32019L0790](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L0790). The EUR-Lex text could not be fetched in this session; the German implementing provisions above are the verified sources.
- **Kneschke v LAION**:
  - LG Hamburg (Sept 2024) held that LAION's copying for an AI training dataset was covered by §60d — [EUIPO case summary](https://www.euipo.europa.eu/en/law/recent-case-law/germany-hamburg-district-court-310-o-22723-laion-v-robert-kneschke).
  - OLG Hamburg (5 U 104/24, 10 Dec 2025) dismissed the appeal, relying on §60d primarily and on §44b. It confirmed a broad reading of "scientific research" under §60d / Art. 3. It held that a natural-language opt-out in website terms was not machine-readable.
  - A further appeal to the BGH was allowed.

  Sources: [DLA Piper](https://www.dlapiper.com/en/insights/blogs/mse-today/2025/robert-kneschke-v-laion); [Harte-Bavendamm](https://www.harte-bavendamm.de/en/ip-blog/hamburg-higher-court-specifies-text-and-data-mining-restrictions-for-ai-training); [Norton Rose Fulbright](https://www.insidetechlaw.com/blog/2025/12/machine-readable-opt-outs-and-ai-training-hamburg-court-clarifies-copyright-exceptions).
- **Precedent for the legal/contract setup:** Ceder-group synthesis recipes (section 5). The team obtained explicit TDM agreements with each publisher and credited a university librarian for arranging them — [Kononova et al. 2019, Sci Data](https://ceder.berkeley.edu/publications/2019_olga_text-mining_dataset.pdf).

### Inferences
- **Facts vs expression.** Individual numbers are generally not protected by copyright in the EU or US: a threshold of 0.1 µg/kg for compound X in water. Protection attaches to text, table layout or selection, and figures. A dataset of (compound, SMILES, value, unit, medium, method, DOI) triples extracted from papers is generally not a reproduction of the papers.
  - **Risks:**
    - copying substantial parts of a protected database (sui generis right, 15 years from creation or substantial update);
    - reproducing large verbatim text snippets.
  - **Mitigations:** store DOIs plus short provenance pointers rather than quotations.
- **Compilations such as van Gemert, VCF and the LSB@TUM Odorant Database are the riskiest source.** Systematically re-extracting them is exactly what the database right targets. Research TDM (§87c with §60d) permits the mining reproduction. It does not clearly permit *publishing* a re-assembled substantial part of that database.
  - **The legally robust path:** mine the *primary papers* and record which paper each value came from. Where a paper cites van Gemert for a threshold, trace it back to the original source rather than copying van Gemert's table. This is also scientifically better.
- **Commercial use.**
  - §60d covers the copying only for non-commercial research. A commercial project, or an LMU project under controlling influence of an industry partner with preferential access, falls back to §44b: honour machine-readable opt-outs, and expect publisher contracts to exclude commercial TDM.
  - Whether a *trained model* or a factual dataset created under §60d may later be commercialised is legally less clear. The mining copies must be deleted or secured, but factual outputs are generally not infringing. Get LMU legal or tech-transfer advice before any commercial use.
- **Redistribution.** Publishing the extracted factual dataset (open licence, e.g. CC BY 4.0 or CC0 for the facts) with DOIs is the standard practice in precedents. Do not redistribute full texts: under §60d(4) they may be shared only with a defined research group or with reviewers for verification.
- **EU AI Act.** General-purpose AI model providers must respect Art. 4 opt-outs and publish training-data summaries. This concerns GPAI model providers, not a narrow odor-potency regressor. It is noted for completeness and was not researched in depth here.
- **US fair use** (context only). US courts have treated non-expressive mining (Authors Guild v. Google/HathiTrust) as fair use, and facts are unprotectable under Feist. The US has no sui generis database right. None of this was verified in this session, and it is secondary for an EU-based project.
- **Shadow libraries (Sci-Hub, Anna's Archive, LibGen).** They distribute copyrighted papers without authorisation. Downloading from them is not "lawful access" under §44b/§60d, so the TDM exceptions do not cover it. Sci-Hub has lost infringement cases (US, India) and is blocked by ISPs in several EU countries. Using them would taint the dataset's provenance and could expose the researcher and university to liability. **Not recommended**, and not needed given DEAL/API access.

### Gaps
- The Directive's exact wording was not fetched (EUR-Lex returned empty).
- No authoritative source was found in this session on whether models trained under §60d can be commercialised, or on the German case law applying the database right to scientific-data compilations.
- The BGH decision in Kneschke v LAION was not checked. Its status as of Sept 2026 is unknown.

---

## 5. Precedents: literature mining at scale for chemistry datasets

### Takeaway
Large chemistry text-mining projects have mined up to about 4 million papers. They relied on **explicit publisher TDM permissions/APIs** (Elsevier, Wiley, Springer, RSC, ACS, ECS), restricted themselves to post-2000 HTML/XML, and published only the extracted facts with DOIs. That model fits the odor-potency project well, at a scale 100–400 times smaller.

### Cited Findings
- **Kononova et al. 2019 (Ceder group), "Text-mined dataset of inorganic materials synthesis recipes"**:
  - Articles came from Springer, Wiley, Elsevier, RSC, the Electrochemical Society and ACS, "from which we received permissions to download large amounts of web-content".
  - The team built a scrapy crawler per publisher for materials-science journals.
  - They processed only HTML/XML papers published after 2000, because older papers are mostly PDF.
  - They scraped **4,204,170 papers** containing 6,218,136 experimental-section paragraphs, stored in MongoDB.
  - They acknowledge a UC Berkeley librarian for obtaining TDM agreements.
  - The published dataset has 19,488 recipes, later extended to 30,031 reactions from 95,283 paragraphs.

  Sources: [Kononova et al., Sci Data 6:203 (2019), PDF](https://ceder.berkeley.edu/publications/2019_olga_text-mining_dataset.pdf); [CederGroupHub GitHub](https://github.com/CederGroupHub/text-mined-synthesis_public).
- **Huang & Cole 2020, battery materials database (ChemDataExtractor)**: 292,313 records and 214,617 unique chemical–property relations for 17,354 chemicals. Properties are capacity, conductivity, Coulombic efficiency, energy density and voltage. The data is on Figshare — [Huang & Cole, Sci Data 2020](https://www.nature.com/articles/s41597-020-00602-2); [Figshare dataset](https://figshare.com/articles/dataset/A_database_of_battery_materials_auto-generated_using_ChemDataExtractor/11888115/2); [GitHub](https://github.com/ShuHuang/batterydatabase). The paper count and publisher list (Elsevier/RSC/Springer, as in other Cole-group work) were not verified in this session: the full text was not retrievable.
- Band-gap extraction with LLMs from literature is a recent example of the same approach with LLM extractors — [arXiv 2311.13778](https://arxiv.org/pdf/2311.13778).

### Inferences
- Standard practice copied from these projects:
  1. Get TDM permission or API access per publisher through the library.
  2. Harvest XML/HTML rather than PDF where possible.
  3. Extract with a domain parser (ChemDataExtractor-style) or an LLM.
  4. Publish only facts plus DOIs under an open licence.
- For odor potency, the harder technical problems will be:
  - normalising units and media (µg/L water vs air, ppb v/v vs µg/kg oil);
  - resolving compound names to structures (many trivial and flavor names);
  - de-duplicating values cited from the same original source.

  Access is not the hard problem.

### Gaps
- Not checked in this session: the Open Reaction Database's text-mining provenance, polymer property extraction (PolyBERT, Polymer Scholar), and the Olivetti-group sourcing details.
