# Untapped odor-potency data sources and statistical/ML methods for improving noisy, small threshold/intensity data

Scope note (researcher, 2026-09-26): ~24 tool calls. Several publisher and registry pages (PubMed, ChemRxiv, SSRN, HathiTrust, ECHA IUCLID) returned HTTP 403/reCAPTCHA, so some numbers could not be verified in this session. Anything marked **[background, not re-verified]** comes from prior knowledge and must be checked before it is cited in a final report. Every yield marked **(estimate)** is a guess, not a count.

---

## Q1. Grey literature: regulatory, government and occupational-safety sources (ECHA/IUCLID, eChemPortal, SDS, NIOSH/AIHA, national agencies)

### Takeaway
ECHA's "REACH Study Results" bulk download (about 23,000 substances in IUCLID .i6z format) is the only large regulatory corpus that can be downloaded in bulk. Odour threshold is **not** a standard REACH endpoint, though, so the expected yield of numeric thresholds from it is low and they are mostly copied from secondary sources. SDS section 9 "odour threshold" fields are overwhelmingly "no data available" or copied from AIHA/3M-type compilations. The richer regulatory leads are odour-based air guideline programs, such as the Texas TCEQ odor-threshold evaluation, and the AIHA odor-threshold compilation, which is copyrighted.

### Cited Findings
- ECHA publishes **REACH Study Results**: non-confidential study results from REACH registrations, released as a zip/7z archive of IUCLID 6.6 (.i6z) dossiers covering **about 23,000 substances**. It includes physical-chemical properties, environmental fate, ecotox and tox results "in a reduced form". The website shows one substance at a time, while the dump allows bulk reading. You import it into a local IUCLID installation. — [ECHA IUCLID: REACH Study Results](https://iuclid6.echa.europa.eu/es/reach-study-results); [Get IUCLID data](https://iuclid6.echa.europa.eu/get-iuclid-data)
- REACH Study Results was refreshed from ECHA CHEM. ECHA CHEM paused processing of registration dossiers during the IUCLID 9.0.1 adaptation and planned to resume by mid-September 2025. — [ECHA IUCLID news](https://iuclid6.echa.europa.eu/view-article/-/journal_content/title/reach-study-results-have-been-updated); [ECHA CHEM](https://echa.europa.eu/echa-chem)
- Texas TCEQ keeps an odor-threshold source hierarchy ("Appendix B: Sources of Information for Odor Thresholds") in its toxicity-factor development documents. This shows the agency curates odor thresholds as part of setting air guideline values. — [TCEQ Butadiene appendix (via TERA)](https://tera.org/Peer/TCEQ/TCEQ%201,3%20Butadiene/TCEQ%20Butadiene%20CD%20files/Updated%20Odor%20Ref%20Appendix%20BC_June2007.doc)
- The Chinese national standard **GB/T 22366-2022** (odor threshold determination), ISO 13301:2002/2018 and ASTM E679 are the methodological standards now used for thresholds in water/food matrices. — [Yang et al. 2026, Compr Rev Food Sci Food Saf (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)
- Studies found on SDS information extraction treat SDSs as heterogeneous documents in which "placement of information is sometimes spread" across sections and pages. No open bulk SDS corpus turned up. — [ML-driven SDS field extraction, Heliyon 2025](https://www.sciencedirect.com/science/article/pii/S240584402500595X); commercial free-lookup SDS databases exist but offer no bulk access, e.g. [ChemicalSafety SDS search](https://chemicalsafety.com/sds-search/)

### Inferences
- **IUCLID yield (estimate):** In IUCLID the odour information sits mainly in the "Appearance/physical state/colour" endpoint as a free-text odour *description*, not as a threshold **[background, not re-verified]**. A text search of the ~23k dossiers for "odour threshold/Geruchsschwelle/ppm" would probably return **low hundreds** of numeric values (estimate), mostly for industrial chemicals already covered by EPA 1992, Nagata and AIHA. It would add few new fragrance or flavour molecules. **Effort:** medium to high: install IUCLID 6, import the i6z files, then parse XML. **Licence:** ECHA's legal notice lets you reuse disseminated data, but you have to respect third-party (registrant) study ownership. Facts such as a threshold value are low risk; do not redistribute the dossier text. Verify the ECHA legal notice, which could not be fetched this session.
- **eChemPortal** federates ECHA, the OECD HPV programme, Japan's J-CHECK and others. It offers a property search, but in my recollection odour threshold is not a searchable property **[background, not re-verified]**. Expect little beyond IUCLID.
- **SDS section 9:** OSHA HCS 2012 Appendix D lists "odor threshold" as a required section 9 item. The EU revision of REACH Annex II (Reg. 2020/878) dropped "odour threshold" from the section 9 list **[background, not re-verified; check OSHA 1910.1200 App D and Reg. (EU) 2020/878]**. Even where the field exists, supplier SDSs usually say "not determined" or copy an AIHA/literature value. So SDS mining adds **mostly duplicates of secondary values with no provenance**. Low value per unit of effort, unless the aim is deliberately to model "secondary-source noise".
- **NIOSH Pocket Guide:** gives odour *descriptions* in "Physical Description". To my knowledge it does not list numeric thresholds systematically **[background, not re-verified]**. Yield ≈ 0 numeric values.
- **AIHA "Odor Thresholds for Chemicals with Established Health Standards"** (2nd ed. 2013; 1st ed. 1989 about 180 chemicals **[background, not re-verified]**) is a critically reviewed, quality-screened compilation. It is copyrighted and paid. It is best used as a *quality-rated reference layer*: facts can be extracted, but the book cannot be redistributed.
- **TCEQ (Texas)** odor-based ESL documents and the Development Support Documents contain critically reviewed odor thresholds with source ratings. As US state-government work they are generally free to access. Estimated yield: **~100–300 chemicals** (estimate), mostly HAP/industrial overlap with EPA 1992.
- **Other national agencies** (German UBA/VDI, Dutch RIVM, Australian NSW EPA, Chinese GB 14554) regulate a few malodorous compounds (GB 14554 covers about 8) or odour units, not per-compound thresholds. Yield is **negligible** (estimate).

### Gaps
- Could not open the ECHA IUCLID pages (HTTP 403). The exact endpoint list in REACH Study Results, whether odour text is included, and the reuse licence are **unverified**.
- No count found of IUCLID records that contain numeric odour thresholds. It would have to be measured by downloading the dump.
- The current wording of OSHA App D and EU 2020/878 on "odour threshold" was not re-verified.

---

## Q2. Theses, dissertations and institutional open databases (mediaTUM, Leibniz-LSB, DNB, HAL, ProQuest OA)

### Takeaway
The single most valuable under-used source found is the **Leibniz-LSB@TUM Odorant Database**: over 1,700 odorants from over 700 publications, with odor thresholds in several matrices (v1.2, 2022). It already distils much of the TUM/Leibniz dissertation corpus (Schieberle/Hofmann/Steinhaus groups). TUM dissertations on mediaTUM are open-access PDFs with GC-O air thresholds (ng/L air) and 3-AFC water thresholds, so they can fill in details, but mining them one by one is slow.

### Cited Findings
- The Leibniz-LSB@TUM Odorant Database "currently includes data on more than 1700 odorants extracted from more than 700 publications", including "odor threshold values in different matrices". The current version is 1.2 (2022). Copyright/citation and disclaimer terms are on separate pages. — [Leibniz-LSB@TUM Odorant Database](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-odorant-database/start/)
- mediaTUM hosts TUM natural-science dissertations as open PDFs. Examples found deal with odor threshold concentrations in air and were done with Leibniz-LSB colleagues. — [mediaTUM doc 1766468](https://mediatum.ub.tum.de/doc/1766468/1766468.pdf); [mediaTUM doc 648009](https://mediatum.ub.tum.de/doc/648009/648009.pdf); [mediaTUM doc 1710885](https://mediatum.ub.tum.de/doc/1710885/1710885.pdf)
- The commercial van Gemert *Odour Thresholds* compilation (2011 edition) contains thresholds for **~1,700 compounds in air, ~1,860 in water and ~760 in other media**. It sets the upper bound of what the literature holds. — [Academia.edu listing "Odour Thresholds Edition"](https://www.academia.edu/117947016/ODOUR_THRESHOLDS_EDITION)
- The Yang et al. 2026 review compiled OT data for **848 flavor compounds in 11 matrices from 146 studies since 1952**: water+air 712, ethanol–water 299, oil 143, starch/cellulose 32, real foods 54. It is in the Wiley Open Access collection. — [Yang et al. 2026 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)
- Sun, Jia & Xi (SSRN preprint) trained structure- and MS²-based models on **1,741 compounds** with air ODTs spanning 10⁻⁹ to 10⁸ mg/m³, including inorganic odorants. — [SSRN 7070562](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7070562) (abstract page returned 403; figures from the search snippet)

### Inferences
- **Leibniz-LSB DB yield (estimate):** ~1,700 odorants. Probably **several hundred structures not in Li 2025/Hou 2026**, particularly potent trace odorants (thiols, pyrazines, lactones) and **matrix-specific thresholds** (oil, starch). Effort: web scraping, or asking the institute for an export. **Licence: unverified.** Read the "Copyright and Citation" page. An academic database of this kind usually allows citation-based research use and may forbid bulk redistribution. Contacting the curators (Steinhaus group) for a data-sharing agreement is the cleanest route.
- **Yang et al. 2026:** if the 848-compound table is in the supplement, it is a directly usable, multi-matrix, multi-study compilation with per-study method metadata. That makes it ideal for fitting *method random effects*. Licence depends on the CC variant of the article; check it. Yield overlaps heavily with Li/Hou (estimate: 60–80% overlap), but the method annotations are the new value.
- **Sun/Jia/Xi 1,741-compound air set:** probably built from van Gemert plus Nagata plus Chinese literature. Check whether the data are released. If so, it is the largest structure-resolved air ODT set seen.
- **Dissertation mining (mediaTUM, DNB, HAL/theses.fr, ProQuest OA, EThOS):** each flavour-chemistry dissertation typically reports 20–80 odorants with GC-O/AEDA and orthonasal thresholds (estimate). The Leibniz-LSB DB already contains many of these. Marginal yield from TUM theses is therefore modest, but *non-TUM* theses add different panels: Wageningen, Ghent, Chinese universities via CNKI (paywalled), French HAL. Effort is high (PDF table extraction, unit harmonisation). Licence: theses are usually open access for reading. Facts are extractable, and redistributing the tables needs care.
- **EThOS (British Library)** was badly disrupted after the 2023 BL cyberattack **[background, not re-verified]**. Do not rely on it.

### Gaps
- The Leibniz-LSB DB licence, the number of threshold *values* versus odorants, and whether bulk export exists were not retrieved.
- Overlap of the Leibniz-LSB DB and Yang 2026 with Li 2025/Hou 2026 has not been measured.
- Whether the Yang 2026 supplement contains the raw per-study table is unverified.

---

## Q3. Old compilations: ASTM DS 48 / DS 48A, van Gemert & Nettenbreijer 1977, Devos 1990, USDA (Buttery, Guadagni) papers; public-domain status

### Takeaway
The classic compilations are **not public domain**. ASTM DS 48 (1973) and DS 48A (1978) remain under US copyright because of the 1976 Act and automatic renewal for 1964–1977 works. HathiTrust holds DS 48A, but access is almost certainly search-only. The *numeric facts* can still be extracted and reused: facts are not copyrightable in the US, and the EU sui generis database right for 1970s–1990 databases has expired. The papers do not need to be redistributed. USDA-authored papers (Buttery, Guadagni, Teranishi at WRRC Albany) are US government works, but most of their values are already in van Gemert and later compilations.

### Cited Findings
- ASTM DS 48A, *Compilation of Odor and Taste Threshold Values Data* (ed. F. A. Fazzalari, ASTM E-18, Philadelphia 1978), expands DS 48. For each entry it gives type, modality, medium, purity, threshold value, units, MW, Wiswesser Line Notation and literature source. — [HathiTrust catalog record 000176905](https://catalog.hathitrust.org/Record/000176905); [ASTM DS48A page](https://www.astm.org/DIGITAL_LIBRARY/MNL/SOURCE_PAGES/DS48A.htm); [ASTM Books Gateway](https://dl.astm.org/books/book/1798/Compilation-of-Odor-and-Taste-Threshold-Values)
- DS 48A is sold digitally through ASTM Books Gateway and the ASME Digital Collection. A Scribd copy circulates, which is of doubtful legality and should not be used. — [ASME Digital Collection](https://asmedigitalcollection.asme.org/astm-ebooks/book/551/Compilation-of-Odor-and-Taste-Threshold-Values); [Scribd](https://www.scribd.com/document/427900946/DS48A-1978-Compilation-of-Odor-and-Taste-Threshold-Values-Data)
- Devos, Patte, Rouault, Laffort & van Gemert, *Standardized Human Olfactory Thresholds* (IRL Press/OUP 1990) is "the first homogeneous inventory of weighted and averaged human olfactory thresholds for **over 500 chemicals**". A copy can be borrowed through Internet Archive controlled digital lending. — [OUP](https://global.oup.com/academic/product/standardized-human-olfactory-thresholds-9780199631469); [Internet Archive](https://archive.org/details/standardizedhuma0000unse); [Google Books](https://books.google.de/books/about/Standardized_human_olfactory_thresholds.html?id=qH9OAQAAIAAJ)
- Buttery and Guadagni (USDA) published volatility and odor-threshold work in water, oil and oil–water systems that underlies flavour-chemistry threshold practice. — [Springer chapter "Flavor Chemistry and Odor Thresholds"](https://link.springer.com/chapter/10.1007/978-1-4615-4693-1_30)
- Works of the US Government are not eligible for US copyright (17 U.S.C. §105). — [17 U.S.C. §105 (Cornell LII)](https://www.law.cornell.edu/uscode/text/17/105)
- Facts are not copyrightable; only original selection/arrangement is (Feist v. Rural, 1991). — [Feist, 499 U.S. 340](https://supreme.justia.com/cases/federal/us/499/340/)

### Inferences
- **Copyright status:** DS 48 (1973) and DS 48A (1978) are corporate works with 95-year terms, so in copyright until about 2068 and 2073. Van Gemert & Nettenbreijer 1977 (TNO/CIVO, Zeist) is in copyright. The EU database right, 15 years from completion or substantial update, has **expired** for all of them. So extracting individual values into a new, differently structured dataset is defensible. Publishing scans or verbatim tables is not.
- **Yield (estimate):**
  - DS 48A: ~1,000+ compounds with multiple values each. Old records (1930s–1970s, many using static sniff methods) carry huge method noise and have no structures (WLN only).
  - Van Gemert 1977 is the predecessor of the 2003/2011 editions.
  - Devos 1990: ~500 standardized air thresholds, **already harmonised**, so it is a valuable calibration anchor.
  
  Most compounds already appear in Li/Hou. The **new value is the multiple independent measurements per compound**, which is exactly what a random-effects model needs to estimate study/method variance.
- **USDA ARS papers (Buttery et al., J Agric Food Chem 1960s–1990s):** the authors are federal employees, so the text is PD under §105 even though journals printed them. Yield of water ODTs is perhaps 300–500 values (estimate), largely already in van Gemert. The main use is **high-quality single-lab water ODTs with measured air–water partition coefficients from the same lab**, which directly tests air↔water conversion (Q10).
- **Effort:** DS 48A plus Devos means OCR/manual transcription of ~200–400 pages. WLN-to-structure conversion needs name-based lookup (PubChem) because WLN parsers are rare. Budget several person-weeks, or use LLM-assisted table extraction with double-entry verification.

### Gaps
- HathiTrust access status (full view vs search-only) could not be confirmed (HTTP 403). Presumed search-only.
- Availability of van Gemert & Nettenbreijer 1977 on HathiTrust or Internet Archive was not checked.
- The exact number of compounds and values in DS 48A was not verified.

---

## Q4. Patents (Firmenich, Givaudan, IFF, Symrise, Takasago, P&G)

### Takeaway
Fragrance patents do report odour thresholds, and some report very potent novel molecules (e.g. 29 pg/L air). They come in two useful forms: (a) odorant-invention patents (Givaudan/Firmenich) with GC-olfactometry thresholds in ng/L air for novel structures, and (b) consumer-product patents (P&G) that define ODT classes and list perfume raw materials by ODT. Patent text is freely accessible and the facts are reusable. Yield is probably a few hundred to low thousands of values, much of it for **novel, non-commercial analogues**. That is valuable because they are close structural neighbours with SAR information.

### Cited Findings
- Givaudan-style GC-olfactometry protocol described in patents: solutions go to the sniff port at back-calculated concentrations, panelists report when odor is noticed, and the panel average is the odor threshold. — [WO2006133592A1 (Google Patents)](https://patents.google.com/patent/WO2006133592A1/en); [WO2008090396A1](https://patents.google.com/patent/WO2008090396A1/en)
- A vetiver odorant had a threshold of **29 pg/L air**, an example of the ultra-potent structures in fragrance R&D. — [PubMed 33315304](https://pubmed.ncbi.nlm.nih.gov/33315304/)
- P&G patents define ODT as the lowest concentration in air perceivable by humans, measured by GC. They class perfume raw materials by ODT cut-offs (e.g. ≤50 ppb "Class 1 HIA"; preferred ODT ≤100/10/1 ppb). — [US5919752A](https://patents.google.com/patent/US5919752A/en); [US20050003975A1](https://patents.google.com/patent/US20050003975A1/en); [US10351796B2](https://patents.google.com/patent/US10351796B2/en); [US20160367713A1](https://patents.google.com/patent/US20160367713A1/en)
- Leffingwell keeps index pages of Givaudan patents (e.g. 1976–1980), useful for enumerating assignee patent families. — [Leffingwell Givaudan patents](http://leffingwell.com/patents/giv_other_patents.htm)

### Inferences
- **Yield (estimate):**
  - Givaudan (Kraft group) and Firmenich odorant patents from ~1995–2025 typically give thresholds for 1–20 molecules each. With a few hundred relevant families, that is **~300–1,500 values**, mostly novel analogues (musks, ambergris, woody, marine).
  - P&G/Henkel/Unilever product patents often reproduce *ODT class lists* (binary ≤ or > cut-off). These are **censored/interval labels** for **~100–400 common PRMs** (estimate), many duplicated across patents.
  - IFF/Takasago/Symrise patents report thresholds less consistently (estimate).
- **Access:**
  - Google Patents full text can be searched ("odor threshold" OR "odour threshold" OR "Geruchsschwelle" OR "seuil olfactif" with ng/l, pg/l, ppb). Google's patents public dataset on BigQuery allows bulk full-text queries **[background, not re-verified]**.
  - USPTO bulk XML and EPO full-text data can also be downloaded in bulk **[background, not re-verified]**.
  - SureChEMBL-style chemical annotation can map patent compound names to structures **[background, not re-verified]**.
- **Licence:** patent documents are published for public disclosure. In the US, patent text is generally treated as not copyright-restricted **[background, not re-verified: USPTO considers patent text largely free of copyright restrictions]**. Threshold values are facts. Low legal risk.
- **Caveats:**
  - Values come from *assignee labs*, with a single method per company (GC-O). That is a consistent source effect, well suited to a lab random effect.
  - Patents select favourable results: they tend to report potent examples, which biases the distribution toward low thresholds.
  - Many compounds lack CAS numbers, and structures must be taken from the claims or examples.
  - Pipeline effort is medium to high: full-text search, table/sentence extraction with an LLM, name-to-structure (OPSIN), manual QA.

### Gaps
- No systematic count of patents containing numeric odor thresholds exists. The yields above are estimates.
- USPTO's copyright position on patent text and the BigQuery dataset were not re-verified this session.

---

## Q5. Supplier catalogs and technical data sheets (Sigma-Aldrich FCC, Givaudan/Symrise/IFF ingredient pages, Perfumer's Apprentice, Scentree, Fraterworks, Pell Wall)

### Takeaway
Supplier pages give mostly **qualitative or ordinal** potency ("odour strength: high", "odour life on blotter", "substantivity"). They rarely give numeric thresholds. The Givaudan ingredient compendium PDF and similar house catalogues are public, but their terms of use restrict reuse. Their best use is as **ordinal strength and tenacity labels** (research use only), not as ODTs.

### Cited Findings
- Givaudan publishes a public "Fragrance Ingredients Sustainability Profile" catalogue PDF describing its ingredients. — [Givaudan catalogue PDF](https://www.givaudan.com/files/giv-fb-fragrance-ingredients-sustainability-profile-catalogue.pdf)
- A 2026 study built an ordinal odor-strength dataset (odorless/low/medium/high) of **2,393 molecules**: **1,678 from The Good Scents Company** and **715 from PubChem**, where PubChem intensity text was mapped by keyword. Good Scents data were **not redistributed because of copyright**; only code to fetch them was released. — [Fichtelmann & Westermayr, RSC Adv 2026 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/); [RSC HTML](https://pubs.rsc.org/en/content/articlehtml/2026/ra/d6ra01805j)

### Inferences
- **Yield (estimate):**
  - Givaudan/Firmenich/Symrise/IFF online ingredient pages: ~1,000–2,000 materials in total, many of them mixtures or naturals. Perhaps 500–1,000 single molecules carry an ordinal "impact/strength/tenacity" rating.
  - Perfumer's Apprentice, Fraterworks and Pell Wall have a few hundred to a thousand products, with free-text strength and "recommended dilution" hints (a weak potency proxy).
  - Scentree.co has ~1,500 ingredients, with an odour-strength/"tenacity" style field in places.
- **Licence:** all are copyrighted websites whose ToS generally forbid scraping. Facts are extractable in the US, but **systematic scraping carries ToS or contract risk**, and EU database rights may apply to recent collections. Use them only for internal research labels and do not redistribute (same approach as Fichtelmann & Westermayr).
- **Sigma-Aldrich FCC/flavor catalogue:** gives organoleptic descriptions, and to my knowledge no thresholds **[background, not re-verified]**. Yield ≈ 0 numeric values.
- "Recommended usage level" (e.g. IFRA/typical % in concentrate) and "odour life on blotter (hours)" are weakly linked to potency. They are more useful as auxiliary tasks (Q9) than as threshold substitutes.

### Gaps
- Terms of use for Scentree, Fraterworks, Pell Wall and Perfumer's Apprentice were not fetched. Record counts are estimates.

---

## Q6. Crowdsourced / community data (Wikidata, Wikipedia, Fragrantica, Basenotes, OpenAlex)

### Takeaway
I ran live SPARQL queries on Wikidata (2026-09-26). **Wikidata has no odor-threshold property.** The only odour-related property is P5872 "smells of" (770 items, 1,932 statements). It is used mostly for grape varieties and aroma concepts, and **only 32 items with a SMILES string** carry it. Wikidata is therefore useless for potency today, though it is a CC0 venue for publishing a harmonised set. Fragrantica/Basenotes are about perfumes (mixtures), not molecules, and their ToS forbid scraping.

### Cited Findings (queries run by me against https://query.wikidata.org/sparql on 2026-09-26)
- A search of all English property labels containing "threshold", "smell", "odor", "odour", "olfact", "vapor pressure" or "henry" returned only **P5872 "smells of"**, **P2119 "vapor pressure"**, and two unrelated income-threshold properties. **No odor/odour threshold property and no Henry's-law-constant property exists.** — [Wikidata Query Service](https://query.wikidata.org/)
- P5872 "smells of": **770 distinct items, 1,932 statements**. The most common objects are "foxiness" (77), "Muscat flavor" (59), "scent of vanilla" (47), "smell of jasmine" (42), "scent of bergamot" (41) and "smell of musk" (41). These are mostly grape cultivars and perfume materials, not molecules. Only **32** items with P5872 also have canonical or isomeric SMILES (P233/P2017). — [Wikidata Query Service](https://query.wikidata.org/)
- P2119 "vapor pressure" is present on **639 items**, a potential auxiliary-feature source. — [Wikidata Query Service](https://query.wikidata.org/)
- Wikidata structured data is CC0. — [Wikidata:Licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)

### Inferences
- **Wikidata yield: ≈0 numeric thresholds.** The strategic option is the reverse: propose an "odor detection threshold" property with medium and method qualifiers, and deposit the harmonised CC-BY/CC0 subset (e.g. Li 2025, which is CC BY) there to raise visibility. Effort: a property proposal takes weeks of community discussion.
- **Wikipedia chemboxes** have an "Odor" field (descriptor text) and sometimes "odor threshold" mentions in article text **[background, not re-verified]**. They add perhaps tens of values, all secondary. CC BY-SA.
- **Fragrantica/Basenotes:** perfume-level (mixture) crowd ratings of "sillage/longevity". Fragrantica also has ingredient notes pages with no quantitative potency. ToS prohibit scraping **[background, not re-verified]**. Low value for molecule potency.
- **OpenAlex (CC0):** not a data source itself, but a good tool for *finding* papers, theses and patents that mention "odor threshold". Its full-text-indexed works and the Crossref/Unpaywall OA flags let you prioritise open PDFs for LLM table extraction. Effort: low to medium.

### Gaps
- Pyrfume (the open olfaction data aggregator, GitHub pyrfume-data) was not checked in this session for newly added threshold sets.

---

## Q7. Negative/censored data and new 2025–2026 compilations: "odorless" labels, ordinal strength, ODT class lists

### Takeaway
"Odorless" labels, ordinal strength classes and patent ODT cut-off lists can be handled as **censored or interval-valued potency labels**. They are far more plentiful than numeric ODTs: thousands of molecules versus about 1,500. New open resources from 2025–2026 are the PubChem-derived ordinal strength labels (715 molecules, released with code on GitHub/Zenodo) and the Yang 2026 848-compound multi-matrix compilation.

### Cited Findings
- Ordinal strength dataset: 2,393 molecules in 4 classes (odorless/low/medium/high). Agreement between Good Scents and PubChem on overlapping molecules: quadratic-weighted **Cohen's κ = 0.83**, **Krippendorff's α = 0.81**. The best ensemble reaches **72% accuracy**. Predictions correlate with Keller et al. intensity ratings but get worse at the 10⁻¹ dilution. PubChem-derived data and code are at github.com/peter-fichtelmann/odor-strength (Zenodo 10.5281/zenodo.17660448). The article is CC BY 3.0. — [Fichtelmann & Westermayr 2026 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
- Structural subtlety makes negative data informative: "small structural changes can render a molecule odorless". — [Search summary of olfaction ML literature; see PLOS One perceptual metrics](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0291767)

### Inferences
- **"Odorless" → right-censored threshold:** "odorless" means ODT > the saturated vapour concentration at room temperature, i.e. log ODT > log C_sat(T). Vapour pressure turns this label into a *compound-specific censoring bound*, which works directly in a Tobit loss (Q9).
- Mayhew et al. 2022 (PNAS, "Transport features predict if a molecule is odorous") curated **~1,900 odorous/odorless labels** **[background, not re-verified; doi 10.1073/pnas.2116576119]**. This is the key open negative set to combine with the approach above.
- **Ordinal strength (Good Scents "high/medium/low")** can be treated as interval-censored log-ODT with learned cut-points (an ordinal-probit or cumulative-link head sharing the latent potency). This adds ~2,000 molecules of weak supervision.
- **Patent ODT classes** (≤50 ppb, >50 ppb, etc.) are exact interval labels in known units. They are cleaner than Good Scents ordinal labels because the cut-off is numeric.
- The Leibniz-LSB DB and Yang 2026 compilations likely contain "<x" or ranges. Keep them as censored or interval labels rather than taking midpoints.

#### Yield summary for Part 1 (all counts are estimates unless marked verified)
| Source | New structure-resolved molecules beyond Li/Hou/Abraham/Nagata/EPA/HSDB | Values | Effort | Licence |
|---|---|---|---|---|
| Leibniz-LSB@TUM Odorant DB | hundreds (of >1,700 odorants, **verified count**) | >1,700+ multi-matrix | low–med (scrape/ask) | unverified; check "Copyright and Citation" |
| Yang 2026 review compilation | tens–low hundreds (848 compounds, **verified**) | multi-study, method-annotated | low if supplementary | Wiley OA (check CC variant) |
| Sun/Jia/Xi 1,741 air ODT set | possibly hundreds (incl. inorganics) | 1,741 (**verified from snippet**) | low if released | unknown |
| Devos 1990 (standardized) | few new; ~500 harmonised anchors | ~500 | med (OCR) | copyrighted book; facts extractable |
| ASTM DS 48A / van Gemert 1977 | few new; many replicate values | thousands | high (OCR, WLN) | copyrighted; facts extractable |
| USDA ARS papers | few new | ~300–500 | med | US gov work (PD) |
| Fragrance patents | ~300–1,500 novel analogues | similar | med–high | patent text, low risk |
| P&G-type ODT class lists | ~100–400 (interval labels) | – | med | low risk |
| ECHA IUCLID bulk | tens–low hundreds | – | high | ECHA legal notice (unverified) |
| SDS section 9 | ~0 independent | – | high | per-supplier |
| Supplier catalogues (ordinal) | ~500–1,000 ordinal | – | med | ToS restrictions |
| Wikidata | 0 (**verified**) | 0 | – | CC0 |
| Odorless labels (Mayhew 2022, Good Scents) | ~1,000–2,000 censored | – | low | mixed |

### Gaps
- The Mayhew 2022 dataset size and licence were not re-verified this session.
- Whether Hou 2026 or Li 2025 already absorbed the Leibniz-LSB DB is unknown. It is the biggest uncertainty in the "new molecules" column.

---

## Q8. Multi-source aggregation under noise: hierarchical/mixed-effects models, inter-source calibration (Abraham, Devos), weighting, outliers

### Takeaway
The evidence supports a **hierarchical model**:

log ODT_obs = θ_compound + δ_study/lab + β·method + ε, with Student-t errors and censoring.

Measured *systematic* method and panel effects in the flavour literature are only about **0.2–0.5 log10 units**, while reported inter-study spreads reach 2–3+ orders of magnitude. Most of the dispersion therefore comes from study-specific errors (purity, delivery, units, old static methods) and outliers, not from a single method offset. Abraham 2012 showed that a per-source rescaling onto Nagata works: 353 compounds fit with the same residual SD (~0.82 log) as Nagata alone.

### Cited Findings
- **Abraham et al. 2012 (Chem Senses 37:207):**
  - 193 Nagata triangle-bag ODTs fit with a linear free-energy equation: **R² = 0.748, SD = 0.830 log units**, with indicator variables for aldehydes, acids, unsaturated esters and mercaptans.
  - ODTs from Cometto-Muñiz & Cain, Cometto-Muñiz & Abraham, and Hellman & Small "could be put on the same scale as those of Nagata", giving **353 ODTs, R² = 0.759, SD = 0.819**.
  
  — [Oxford Academic](https://academic.oup.com/chemse/article-abstract/37/3/207/325917); [eScholarship full text](https://escholarship.org/uc/item/9b72q2v9); [ResearchGate table of Nagata values](https://www.researchgate.net/figure/Nagata-values-of-odor-detection-thresholds-ppm-used-to-obtain-eq-5_tbl2_51696432)
- **Devos et al. 1990** produced "weighted and averaged" standardized thresholds for >500 chemicals. It was the first systematic standardization of scattered literature values. — [OUP](https://global.oup.com/academic/product/standardized-human-olfactory-thresholds-9780199631469); [Yang 2026 review](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)
- **Size of method and panel effects** (Yang et al. 2026, Tables 2 and 4), all p < 0.01:
  - 3-AFC + curve fitting vs 3-AFC + BET: ethyl hexanoate **861 vs 507 µg/L**; butyric acid **2,741 vs 967 µg/L**.
  - Expert vs consumer panels: 2-phenylethanol **871 vs 2,042 µg/L**; vanillin **26 vs 79 µg/L**.
  - Overall inter-laboratory variation is "up to two to three orders of magnitude".
  - Nasal vs retronasal thresholds: Spearman **0.932** (N = 50).
  
  — [Yang et al. 2026 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)
- The same review recommends prioritising studies with ISO/ASTM procedures, defined conditions, adequate panels and transparent statistics. It also flags specific anosmias (receptor polymorphisms) as a bias source. — [Yang et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)
- **Reference odorant anchoring:** EN 13725 defines 1 ou_E/m³ ≡ 123 µg/m³ n-butanol, and panelists are screened on n-butanol sensitivity. A shared reference compound lets lab effects be calibrated. — [search summary citing standard practice; see Yang 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)
- **Analogous QSAR evidence:** Landrum & Riniker (JCIM 2024, 64:1560–1567) showed that combining IC50/Ki from different ChEMBL assays, even for the same target, is "a source of significant noise". Maximal curation (matching assay metadata) reduces it. Code and ChEMBL32 datasets are MIT-licensed. — [JCIM](https://pubs.acs.org/doi/10.1021/acs.jcim.4c00049); [ChemRxiv](https://chemrxiv.org/engage/chemrxiv/article-details/659d25b2e9ebbb4db9c21d61); [GitHub rinikerlab/overlapping_assays](https://github.com/rinikerlab/overlapping_assays)
- A follow-up perspective argues for "assay-aware" bioactivity models that encode biological or assay context rather than pooling. — [Toward Assay-Aware Bioactivity Models (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12264928/)

### Inferences
- **Recommended model:** a Bayesian mixed-effects meta-analysis (brms/Stan or NumPyro).
  - **Fixed effects:** method class (triangle bag, dynamic olfactometry ASTM E679/EN 13725, static squeeze bottle, GC-O, 3-AFC in water), data-processing rule (BET vs curve fit), panel type (expert/consumer), medium, and decade (a proxy for method generation).
  - **Random effects:** study/lab intercepts.
  - **Likelihood:** Student-t for robustness, with interval/censored terms for "<x", ">x" and ranges.
  - **Outputs:** (1) a consensus θ with a posterior SD per compound, used as the training target or as per-sample weights (1/σ²); (2) lab bias estimates; (3) automatic outlier flags wherever the posterior predictive p-value is extreme.
- **Priors:** from the Yang figures, method and processing offsets are ≈ log10(861/507) = 0.23 to log10(2741/967) = 0.45, and panel offsets ≈ 0.37–0.48 log10 units. So fixed-effect priors of N(0, 0.5) are reasonable. The residual after these effects will still be large (roughly 0.5–1 log unit), in line with Abraham's SD ≈ 0.82 for a physicochemical LFER.
- **Abraham-style rescaling** is the special case of lab intercepts estimated on overlapping compounds. The hierarchical model generalises it and propagates the uncertainty.
- **Devos standardization** (as I recall it, not verified): values were converted to common units, then each literature source was adjusted by a correction derived from its values for compounds shared with a reference set, and a weighted mean was taken. That is an iterative reference-based rescaling, i.e. an early fixed-effects form of the same idea. Worth reading the Internet Archive copy's method chapter to reuse its reference compounds and weights.
- **Quality weighting (EPA 1992's criteria, AIHA's ratings):** encode them as a covariate on the error variance (heteroscedastic σ_study = f(quality score)), not as hard filters. That keeps sparse compounds in the data while down-weighting weak sources.
- **Anchor compounds** (n-butanol, H₂S, etc.) measured across many studies identify lab offsets best. Include them even if they are uninteresting as prediction targets.

### Gaps
- Could not retrieve the quantitative Landrum & Riniker results (pairwise agreement fractions, R² under minimal vs maximal curation) because PubMed and ChemRxiv returned 403. Kalliokoski et al. 2013 (PLoS One) on mixed IC50 variance is another relevant benchmark **[background, not re-verified]**.
- The exact Devos 1990 standardization algorithm (reference set, weighting formula) is **not verified**. It needs the book.
- EPA 1992's 13 quality criteria were not re-fetched here, since the user already has the document.
- No published hierarchical Bayesian meta-analysis of odor thresholds with lab random effects was found. It looks like an **open niche**.

---

## Q9. Using correlated auxiliary targets: multitask, censored (Tobit) losses, ordinal heads, pretraining/POM, receptor data, learning-to-rank

### Takeaway
The strongest quantified evidence comes from drug-discovery QSAR. Adding censored labels through Tobit likelihoods improved NLL and calibration, especially when more than 35% of labels were censored (Svensson et al. 2024/2025). For odor, physicochemical transport properties alone explain about 77% of log-ODT variance in one set (Rodríguez 2011) and about 75% in the Abraham LFER. Vapour pressure, solubility and Henry's constant are therefore the most valuable auxiliary inputs or tasks. Odorless and ordinal-strength labels supply thousands of weakly supervised molecules.

### Cited Findings
- **Censored regression in QSAR:** Svensson, Friesacher, Winiwarter, Mervin, Arany & Engkvist adapted ensemble NNs, MC-Dropout, Bayes-by-Backprop and Gaussian mean-variance estimators with the **Tobit** likelihood across 15 AstraZeneca assays, with 0–63% censoring (target assays average 19%). Models trained with censored labels "performed better" on most assays in NLL and calibration, with MSE comparable or better. The gain was largest for datasets with more than **35% censoring**. — [arXiv 2409.04313](https://arxiv.org/html/2409.04313); [published version, AI in the Life Sciences 2025](https://www.sciencedirect.com/science/article/pii/S2667318525000042)
- **Censored NN losses compared:** Tobit likelihood, censored MSE and censored MAE. Tobit performed best, and the other two are simpler to implement. — [Pattern Analysis & Applications 2024](https://link.springer.com/article/10.1007/s10044-024-01216-9)
- **Physicochemical auxiliary signal:** a linear regression of ODT on vapour pressure, water solubility and log Kow gives **r² = 0.769**. It cannot handle water-immiscible odorants or enantiomers. — [Rodríguez et al. 2011, Flavour Fragr J](https://onlinelibrary.wiley.com/doi/abs/10.1002/ffj.2076); [ICBAS record](https://sigarra.up.pt/icbas/en/pub_geral.pub_view?pi_pub_base_id=62546)
- **Transfer learning for perfume ODT:** a "scientific ML + transfer learning" framework for predicting odor threshold values of perfumes exists (Heliyon 2023). — [ScienceDirect S2405844023080210](https://www.sciencedirect.com/science/article/pii/S2405844023080210)
- **Receptor-profile auxiliary features:** mapping odorants to predicted receptor activation profiles improved percept prediction. — [bioRxiv 2024.09.16.613334](https://www.biorxiv.org/content/10.1101/2024.09.16.613334.full.pdf)
- **Pairwise comparisons:** relative-similarity judgments ("does A smell more like B or C?") from non-experts give usable perceptual metrics. The same triplet/pairwise logic applies to "which is stronger" potency ranking. — [PLOS One 2023](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0291767)
- **Intensity as a dose-response target:** Pellegrino … Gerkin, Koulakov, Mainland (bioRxiv Aug 2025, CC BY 4.0):
  - 62 odorants at ≥7 concentrations, 7,623 gLMS ratings, 36 trained panelists, test-retest r = 0.97.
  - A **Hill equation** (I_max, EC50, n) beat Stevens, Beidler and Fechner.
  - A 5-layer DNN on 127 physicochemical features predicted intensity with **r = 0.87 (RMSE 7.1)**.
  - They argue OAV (C/ODT) poorly predicts perceptual dominance.
  
  — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)

### Inferences
- **Architecture sketch:**
  - A shared molecular encoder (GNN, or a POM/OpenPOM embedding pretrained on ~5k GoodScents+Leffingwell descriptor labels).
  - A **latent potency** head feeding several observation models:
    - (a) a Gaussian/Student-t head for numeric ODTs, with medium- and method-specific offsets;
    - (b) a Tobit head for "<x", ">x" and odorless (bound = log C_sat from vapour pressure);
    - (c) a cumulative-link ordinal head for Good Scents/PubChem strength classes and patent ODT classes;
    - (d) a Hill-EC50 head for Keller 2016 and Pellegrino intensity curves;
    - (e) auxiliary regression heads for log VP, log K_aw and log Kow.
  - Optionally, M2OR-derived receptor-response features as inputs or as an auxiliary classification task.
- **Expected gain:** no odor-specific ablation was found. By analogy with Svensson et al., censored and ordinal labels should help most with calibration and with coverage of chemical space (odorless boundary, weak odorants) rather than cutting RMSE on well-measured compounds. Treat any claimed RMSE gains as hypotheses until tested.
- **Learning-to-rank:** within a single study, the *ranking* of compounds is more reliable than absolute values, because lab offsets cancel. A pairwise ranking loss over within-study pairs (RankNet/ListNet), combined with absolute regression on the consensus θ, is a cheap way to remove lab bias without an explicit random-effects model.
- **Physics-informed baseline:** use a transport-property model (Abraham LFER, or Rodríguez VP/solubility/Kow) as the prior mean and train the ML model on the residual. With about 1,500 labels this is typically more sample-efficient than end-to-end learning.

### Gaps
- No 2015–2026 odor-threshold paper was found that quantifies gains from Tobit, multitask or ordinal-auxiliary training. This is a clear research gap.
- The SSRN Sun/Jia/Xi performance metrics could not be retrieved (403).
- The M2OR-to-threshold correlation (receptor EC50 vs ODT) was not quantified in any source found.

---

## Q10. Air ↔ water threshold conversion via Henry's law: validity for merging datasets

### Takeaway
Physically, the conversion is ODT_air ≈ ODT_water × K_aw, with K_aw the dimensionless air/water partition coefficient. It assumes the headspace above the water sample is at equilibrium when sniffed. Flavour chemistry has long used it (Buttery/Guadagni-era work), and transport-property regressions reach r² ≈ 0.77. However, no 2015–2026 paper found here quantifies how well water-derived air ODTs match directly measured air ODTs across many compounds. Treat conversion as a **modelled medium offset with its own uncertainty**, not as an exact identity.

### Cited Findings
- "Relatively simple methods are available for calculating thresholds in air from thresholds determined in water". Water-solution thresholds were an early standard approach in flavour research. — [Wikipedia: Odor detection threshold](https://en.wikipedia.org/wiki/Odor_detection_threshold); [Springer "Flavor Chemistry and Odor Thresholds"](https://link.springer.com/chapter/10.1007/978-1-4615-4693-1_30)
- ODT regression on vapour pressure, water solubility and Kow gives r² = 0.769. It fails for water-immiscible odorants. — [Rodríguez et al. 2011](https://onlinelibrary.wiley.com/doi/abs/10.1002/ffj.2076)
- Matrix effects are non-monotonic: ethyl acetate thresholds in 9–12% ethanol–water "did not gradually increase". Oil, starch and real-food thresholds differ systematically. This shows simple equilibrium partitioning is not the whole story. — [Yang et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)
- Nasal vs retronasal thresholds correlate at Spearman 0.932 (N = 50). Delivery route preserves rank but not absolute values. — [Yang et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)

### Inferences
- **Practical recommendation:**
  1. Convert water ODTs to air-equivalent values using experimental K_aw where available (EPI Suite HENRYWIN/Sander compilation), or predicted K_aw otherwise.
  2. Carry σ(K_aw) into the observation noise.
  3. Add a **medium fixed effect** (water-converted vs direct air) plus a per-method effect, so the model learns any systematic non-equilibrium bias. Sniffing from a squeeze bottle or sniff flask often does not reach headspace equilibrium; air ODTs derived this way would come out higher than true values.
  4. Check on the overlap of compounds with both direct air and water thresholds (Li/Hou vs Nagata/Abraham/Devos). The regression slope (ideal 1) and residual SD are the empirical validity check, and they are cheap to compute on the user's existing data.
- Expect larger conversion errors for (a) very hydrophobic compounds (low solubility, K_aw uncertain, adsorption to glass) and (b) ionisable acids and amines, where pH affects the partitioning.

### Gaps
- No quantitative validation was retrieved (slope, SD of converted vs measured air ODT across N compounds). The classic evidence (Buttery et al. 1969–1971; Guadagni et al.) was not fetched. This needs an in-house overlap analysis.

---

## Q11. Active learning: which molecules to measure next

### Takeaway
No olfaction-specific active-learning study for thresholds was found. Standard Bayesian optimal-design logic applies: prioritise molecules where the model's **epistemic** uncertainty is high **and** that cover under-represented chemical space. Also re-measure **bridging/anchor** compounds with contradictory literature values; these pay off twice, by reducing label noise and by identifying lab offsets.

### Cited Findings
- Perceptual datasets remain small: 476–480 molecules in the largest psychophysics sets (Keller-type, 49–55 subjects). This motivates careful choice of which molecules to test. — [PLOS One 2023](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0291767)
- Structure–odor relationships are discontinuous ("activity cliffs"): small changes can make a molecule odorless. Density-based coverage sampling alone will therefore miss cliffs. — [PLOS One 2023](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0291767)
- Bayes-by-Backprop gave the best-calibrated uncertainties in 34/45 dataset instances, and ensembles gave the best accuracy. These are the uncertainty estimators an acquisition function needs. — [Svensson et al. 2024](https://arxiv.org/html/2409.04313)
- Large-scale screening of millions of compounds with human-olfaction ML models has been done (insect repellents). The infrastructure for scoring candidate pools exists. — [eLife reviewed preprint 95532](https://elifesciences.org/reviewed-preprints/95532v1)

### Inferences
- **Acquisition recipe:**
  - Pool: commercially available, food/fragrance-safe molecules (e.g. FEMA GRAS/JECFA flavour list, ~2,500+ **[background]**, plus IFRA transparency list ingredients).
  - Score: expected reduction in integrated predictive variance (or BALD/ensemble disagreement), multiplied by a diversity term (k-center greedy on the embedding), times a feasibility/cost filter (purity available, safe to sniff, volatility within olfactometer range).
- **Three buckets of roughly equal budget:**
  1. **High-disagreement literature compounds** (spread > 1.5 log units across sources). Re-measuring them with a standardized protocol (EN 13725 or ASTM E679 with n-butanol reference) resolves label noise.
  2. **Model-uncertain unexplored scaffolds.**
  3. **Anchor compounds** in every panel session, to calibrate lab and session effects.
- **Cheaper proxy measurements:** GC-O with dilution to threshold (AEDA-style), measuring many compounds per run, gives noisier but much higher-throughput potency data. It can be modelled as a separate "method" in the hierarchical model. Intensity ratings at fixed concentrations (Keller style) are also cheaper than full threshold staircases, and the Hill/EC50 link connects them to thresholds.

### Gaps
- No quantified active-learning gains for olfactory potency were found. Gains would have to be estimated by retrospective simulation on the pooled data (hold out compounds, simulate acquisition).

---

## Q12. Quantified improvements from these methods (odor thresholds/intensity) and analogous noisy multi-source QSAR cases

### Takeaway
Published quantifications for odor are sparse. The main reference points are:
- Abraham's cross-source rescaling: 353 compounds fit with SD 0.819 vs 0.830 for Nagata-only, so no loss in quality while adding 160 compounds.
- The physicochemical ceiling of r² ≈ 0.75–0.77.
- Ordinal strength classification at 72% accuracy with κ ≈ 0.83 inter-source agreement.
- Intensity dose-response DNN at r = 0.87.

From QSAR, the transferable lessons are that pooling across assays adds significant noise (Landrum & Riniker 2024), and that censored labels help most when abundant (Svensson 2024).

### Cited Findings
- Abraham 2012: Nagata-only 193 ODTs, R² 0.748 / SD 0.830. After rescaling three other sources onto Nagata, 353 ODTs, R² 0.759 / SD 0.819. — [eScholarship](https://escholarship.org/uc/item/9b72q2v9)
- Rodríguez 2011: r² = 0.769 from VP, solubility and Kow. — [Wiley FFJ](https://onlinelibrary.wiley.com/doi/abs/10.1002/ffj.2076)
- Fichtelmann & Westermayr 2026: 4-class odor strength, 72% accuracy; inter-source κ_w 0.83. — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
- Pellegrino et al. 2025: single-molecule intensity DNN r = 0.87, RMSE 7.1 (gLMS). A mixture primacy-coding model reached RMSE 8.6. Leakage from overlapping components was worth about 1.0 RMSE unit. — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- Landrum & Riniker 2024: combining IC50/Ki from different sources is "a source of significant noise". — [JCIM](https://pubs.acs.org/doi/10.1021/acs.jcim.4c00049)
- Svensson et al. 2024: censored labels improve NLL and calibration, most at >35% censoring. — [arXiv](https://arxiv.org/html/2409.04313)
- Yang 2026: no ML/QSAR in the review. The authors call the lack of large, reliable OT data the limiting factor for predictive models. — [PMC13420774](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)

### Inferences
- **Noise ceiling:** if inter-source SD for the same compound is ~0.5–1.0 log units (typical after removing gross outliers), then no model can show test RMSE much below that on single-source labels. Published odor-ODT models with RMSE ≈ 0.8 log units (Abraham) may already be near the label-noise floor. Aggregation into consensus labels with a posterior SD is the prerequisite for measuring real model gains. Evaluate on **consensus labels of multiply-measured compounds** and report the noise ceiling, following Landrum/Riniker-style analysis.
- **Priority order by expected return per effort:**
  1. Hierarchical consensus plus censoring on existing data: low cost, directly attacks the 2–4-order noise.
  2. Add the Leibniz-LSB DB and Yang 2026 compilations: low to medium cost, more molecules and method metadata.
  3. Add odorless and ordinal labels as censored/ordinal heads: low cost, thousands of molecules.
  4. Patent mining: medium to high cost, novel potent analogues.
  5. OCR of DS 48A/Devos for replicate values: high cost, mostly helps variance estimation.
  6. New measurements via active learning, with anchors: highest cost, highest information per molecule.

### Gaps
- No odor-specific ablation of hierarchical aggregation, Tobit or multitask methods was found. The exact Landrum/Riniker agreement statistics were not retrieved (403). A retrospective benchmark on the user's own pooled data is the only way to quantify gains.
