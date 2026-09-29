# Fragrance Industry Data Access: Public Company Data and an Academic Approach Playbook

Scope: (1) odor-potency data that fragrance and flavor companies already publish openly and that can be lawfully collected; (2) how an LMU researcher in Munich can approach fragrance companies for data sharing or collaboration. Status: September 2026. The legal points below are factual background, not legal advice. Items marked **[BK]** come from the researcher's background knowledge and were not re-verified with a live source in this session. Treat them as leads to check.

---

## Q1. Which ingredient catalogs and compendia do companies publish, and what fields do they contain?

### Takeaway
Supplier-authored catalog data is openly readable, but it rarely contains true odor thresholds. The fields that exist at scale are **"tenacity on blotter"** (hours, days or weeks), **use level (%)**, qualitative **substantivity** (damp and dry, e.g. "Good"), **vapor pressure**, boiling point and MW. Givaudan also has a proprietary **"odour value"** (vapor pressure divided by detection threshold) behind its "olfactive impact" metric, but the underlying threshold numbers do not appear to be published per molecule. Expect roughly 100 to 300 captive molecules per major house, with tenacity as the main potency-related label. That label is noisy, ordinal-ish and blotter-specific.

### Cited Findings
- **Givaudan "odour value":** Givaudan defines its olfactive-impact metric as "Odour value as measured by Givaudan as a combination of Odour Detection Threshold and Vapour Pressure". It publishes this next to nine sustainability parameters (renewable carbon, biodegradability, ecotoxicity, etc.) and links a downloadable "sustainability profile catalogue" PDF. The page gives no molecule count and says nothing about tenacity, log P or access terms. — [Givaudan sustainability parameters page](https://www.givaudan.com/fragrance-beauty/fragrance-ingredients-business/fragrance-molecules/sustainability-parameters); [Givaudan Fragrance Ingredients Sustainability Profile catalogue (PDF)](https://www.givaudan.com/files/giv-fb-fragrance-ingredients-sustainability-profile-catalogue.pdf)
- **Givaudan "Carto":** Givaudan's AI-assisted formulation tool "Carto" uses the ingredients' "Odour Value Map" to maximise olfactive performance. This shows that Givaudan holds an internal threshold × vapor-pressure dataset across its palette. — [Givaudan Carto launch press release](https://www.givaudan.com/file/156296/download)
- **Reseller pages repeat Givaudan TDS fields.** Perfumer's Apprentice, Toscanol (Givaudan), CAS 16510-27-3: odor "Herbal, Aniseed, Green"; use level 0.1–5%; **tenacity on blotter 2 days**; burning effectiveness Good; substantivity damp Good; substantivity dry Good; **vapor pressure 0.0113 hPa at 20 °C**; bp 235 °C; MW 162.2. — [Perfumer's Apprentice – Toscanol](https://shop.perfumersapprentice.com/p-6232-toscanol-givaudan.aspx)
- More examples of the same field set: Givescone (Givaudan) tenacity on blotter **20 hours**; Ultrazur (Givaudan) **1 week**. — [Perfumer's Apprentice – Givescone](https://shop.perfumersapprentice.com/p-6095-givescone-givaudan.aspx); [Perfumer's Apprentice – Ultrazur](https://shop.perfumersapprentice.com/p-5976-ultrazur-givaudan.aspx). Perfumer's Apprentice also has an A–Z "All Fragrance Ingredients" listing that could be enumerated. — [PA all ingredients S–Z](https://shop.perfumersapprentice.com/c-244-all-fragrance-ingredients.aspx?pagerange=S-Z)
- **dsm-firmenich** runs an online "Ingredient Catalog" (studio.dsm-firmenich.com) with separate Perfumery and Flavor catalogs, plus Terms of Use at /company/terms-use. The fetched landing page is only a navigation shell: field content and login status could not be checked. — [dsm-firmenich Ingredient Catalog](https://studio.dsm-firmenich.com/ingredients/Ingredient-Catalog)
- dsm-firmenich product text uses tenacity in days on a smelling strip, e.g. **FLOROL: tenacity 3 days on smelling strip**, "very stable and substantive". — [SpecialChem – dsm-firmenich FLOROL TDS](https://www.specialchem.com/cosmetics/product/dsm-firmenich-florol)
- Legacy Firmenich PDF compendia are still online: "Firmenich Perfumery Ingredients 2020" catalogue leaflet and "Flavor Ingredients Catalogue 2016" compendium. Automated text extraction of the 2020 PDF failed; the file is image and font encoded, so OCR is needed. — [Firmenich Perfumery Ingredients 2020 (PDF)](https://www.firmenich.com/sites/default/files/Catalogue_leaflet_Perfumery_Ingredients_2020.pdf); [Firmenich Flavor Ingredients Compendium 2016 (PDF)](https://www.firmenich.com/sites/default/files/uploads/files/ingredients/Compendium_Flavors_Ingredients_2016.pdf)
- Aggregated open datasets already include some catalog-derived sources. Pyrfume unifies ten expert sources, including the **IFRA Fragrance Ingredient Glossary** and **Sigma's Fragrance & Flavor Catalog**, TGSC, Arctander and Leffingwell. Leffingwell = 3,523 molecules with descriptors. — [Pyrfume, Scientific Data 2024](https://www.nature.com/articles/s41597-024-04051-z); [Leffingwell Odor Dataset (Zenodo)](https://explore.openaire.eu/search/dataset?pid=10.5281%2Fzenodo.4085097)

### Inferences
- Tenacity on blotter is the only potency-adjacent label that is broadly published. Its units are heterogeneous ("20 hours", "2 days", "1 week", ">400 h"). It mostly reflects volatility and vapor pressure plus threshold, not threshold alone. It is useful as a weak or auxiliary target, for example in ordinal regression or multi-task learning with vapor pressure as a covariate.
- Expected yield, all estimates: Givaudan captives plus specialties ~150–250 with tenacity; dsm-firmenich ~150–300; IFF ~100–200; Symrise ~100–200; BASF Aroma Ingredients, Kao, Takasago, Privi and Vigon together another ~300–800. After deduplication by CAS, a scraped "tenacity + use level + VP" table could plausibly reach **~1,000–2,500 unique molecules**. Only a small fraction would have a numeric threshold. **[estimate]**
- **[BK]** Other reseller and educational sites with extra fields: The Good Scents Company (odor strength class "low/medium/high", "substantivity X hours at 100%", some thresholds with citations). PerfumersWorld (Odour Life/Impact numbers, proprietary scales). Scentree (odor strength, tenacity, log P). Fraterworks and Pell Wall (qualitative tenacity or impact notes). None of these field sets were verified live this session. TGSC's odor-strength and substantivity-hours fields are probably the densest free "potency" labels, but TGSC has explicit copyright notices.
- IFF, Symrise (Scent & Care), Takasago, Kao, BASF, Privi, Vigon, Moellhausen, Hekserij and Fraterworks pages could not be inspected within the tool budget. Their fields and terms remain unchecked (see Gaps).

### Gaps
- Numbers of molecules and exact field schemas for IFF, Symrise, Takasago, Kao, BASF, Privi, Vigon, Moellhausen, Hekserij, PerfumersWorld, Scentree, Fraterworks and Pell Wall were not verified.
- No evidence found that Givaudan publishes the numeric "odour value" or threshold per molecule. The sustainability PDF may list an "olfactive impact" class per molecule; this needs manual inspection.
- The Terms of Use of dsm-firmenich, Givaudan and Perfumer's Apprentice on reuse and scraping were not read.

---

## Q2. What is the realistic yield of odour thresholds from TDS and SDS documents (SDS Section 9)?

### Takeaway
Low. SDS Section 9 has an "odour threshold" field, but for fragrance materials it is overwhelmingly filled with "not determined" or "no data available" **[BK / estimate]**. TDS documents give tenacity and use level, not thresholds.

### Cited Findings
- TDS-type documents found in this session (Givaudan via reseller, dsm-firmenich via SpecialChem) list tenacity, substantivity, VP and bp. None of them list an odor-threshold value. — [Perfumer's Apprentice – Toscanol](https://shop.perfumersapprentice.com/p-6232-toscanol-givaudan.aspx); [SpecialChem – FLOROL](https://www.specialchem.com/cosmetics/product/dsm-firmenich-florol)

### Inferences
- **[BK / estimate]** The CLP/REACH SDS format (Annex II, Section 9.1) includes "odour threshold". In practice, fewer than about 5% of fragrance-ingredient SDSs give a number. Numbers that do appear are often copied from generic literature (e.g. the old van Gemert compilations) and are of mixed quality. SDS scraping is therefore a poor use of effort. Harvesting the logP, VP and water-solubility fields as features would be a better use of SDSs.
- ECHA REACH registration dossiers, which are public, contain physchem data (VP, log Kow), not odor thresholds. They are useful as features, not labels.

### Gaps
- No systematic survey of SDS Section 9 odour-threshold fill rates for fragrance materials was found.

---

## Q3. How many numeric thresholds can be extracted from company-authored papers and patents?

### Takeaway
This is the richest openly readable **numeric** source from industry. Givaudan's Philip Kraft group routinely reports GC-olfactometry odor thresholds in **ng/L air** for newly designed molecules and their analogs. Firmenich and Symrise authors publish fewer. Thresholds are facts, and extracting them from papers is lawful (see Q4). Yield is probably several hundred to about 1,000 molecule-threshold pairs, all measured with a fairly consistent in-house protocol. **[estimate]**

### Cited Findings
- Philip Kraft joined Givaudan's Fragrance Research in 1996 and became group leader for the discovery of new odorants in 2001. His field is rational odorant design, molecular modeling and structure–odor relationships. His ORCID lists his publication record. — [Philip Kraft ORCID](https://orcid.org/0000-0002-4801-5389)
- Kraft, "From Cassyrane to Cashmeran – The Molecular Parameters of Odorants", Chemistry & Biodiversity 2014: a review of odorant design with threshold-driven molecular parameters. — [Wiley](https://onlinelibrary.wiley.com/doi/10.1002/cbdv.201400071); [free copy](https://d.docksci.com/from-cassyrane-to-cashmeran-the-molecular-parameters-of-odorants_5a87bc28d64ab2c2a4aa1380.html)
- Example of the numeric threshold detail in this literature: (3E,5E)-5-(tert-butyl)octadeca-3,5-dien-2-one is reported as having the lowest odor threshold of the ionone family, **0.036 ng/L air**. Another study reports thresholds from **0.0032 ng/L air (1-hexen-3-one)** to **55 ng/L air (1-dodecen-3-one)**. — search-snippet results pointing to the Kraft and related literature; primary papers not opened, see [search context: Chem. Biodiversity / PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5741668/)
- Academic–industry SAR papers with thresholds also exist outside the big houses. Example: halogenated guaiacol odorants, with odor qualities and thresholds measured systematically (FAU Erlangen / Leibniz-LSB tradition). — [PMC5741668](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5741668/)
- Perfumer & Flavorist trade articles tell the story of a molecule's discovery, e.g. Nympheal (Givaudan muguet aldehyde), and sometimes quote thresholds. — [P&F – Discovery of Nympheal](https://www.perfumerflavorist.com/fragrance/ingredients/article/21856694/discovery-of-nympheal-the-definitive-muguet-aldehyde)
- Company patents contain odor evaluations of new molecules and sometimes threshold comparisons. Example: US 10443018 / RE49502 (Givaudan), "Phenyl based compounds substituted with aldehyde moieties and their use in perfumery". — [USPTO 10443018](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10443018); [USPTO RE49502](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/RE49502)
- The Leibniz-LSB@TUM Odorant Database, in Freising near Munich, compiles odor thresholds in different matrices. Version 1.2 (2022) covers **>1,700 odorants from >700 publications**. It is the most important curated threshold source for food odorants, and it is local. — [Leibniz-LSB@TUM Odorant Database](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-odorant-database/start/)

### Inferences
- **[estimate]** Kraft-group papers from roughly 1998 to 2026, in Helv. Chim. Acta, Eur. J. Org. Chem., Chem. Biodiversity, Angew. Chem. and Synthesis, plus reviews such as "Odds and Trends" (Angew. Chem. 2000) **[BK]**, likely hold **~400–1,000 threshold values**, many of them for close analog series. That is well suited to activity-cliff / SAR learning, but the chemical space is narrow (musks, ambers, woody, muguet aldehydes).
- Patents more often give qualitative comparisons ("stronger than", "more tenacious") than numeric thresholds. Estimated yield is a few hundred usable numeric thresholds across Givaudan, Firmenich, Symrise, IFF and Takasago patents, and they are hard to mine. **[estimate]**
- A single-protocol source (Givaudan GC-O in ng/L air) has less inter-lab noise than pooled literature. It should be kept as a separate "source" feature or domain in the model.

### Gaps
- No bibliometric count of threshold-bearing papers by Givaudan, Firmenich or Symrise authors was performed.
- Firmenich and Symrise authors with systematic threshold series were not identified in this session.

---

## Q4. Is it legal in Germany/EU to scrape public company websites, and are facts like "tenacity 48 h" protectable?

### Takeaway
Single facts (a threshold, "tenacity 2 days", a VP value) are not copyright-protected. The risks are (a) the **sui generis database right** (§§ 87a ff. UrhG) when extracting a *substantial part* of a catalog, and (b) contractual Terms of Use. For an LMU researcher, **§ 60d UrhG (TDM for scientific research)** is the stronger basis: unlike § 44b, it cannot be opted out of by rightholders **[BK]**. Givaudan's robots.txt currently contains no AI/TDM crawler blocks.

### Cited Findings
- § 44b UrhG permits text and data mining, but rightholders may reserve their rights. For content accessible online, the reservation is only effective if made in **machine-readable form** (§ 44b Abs. 3). — [§ 44b UrhG, gesetze-im-internet](https://www.gesetze-im-internet.de/urhg/__44b.html); [dejure § 44b](https://dejure.org/gesetze/UrhG/44b.html)
- **Kneschke v. LAION:** LAION e.V. extracted photos from a stock-photo site. The key dispute was whether a natural-language reservation in terms of use counts as "machine-readable". The **OLG Hamburg** found that a reservation declared only in natural-language text (2021) could not be assumed to be machine-readable. It left open whether natural language counts as machine-readable today (2025/26). — [LTO on LG Hamburg judgment](https://www.lto.de/recht/hintergruende/h/kuenstliche-intelligenz-ki-urheberrecht-text-data-mining-lg-hamburg-310o22723); [Initiative Urheberrecht on OLG Hamburg](https://urheber.info/diskurs/hamburger-olg-urteil-im-fall-laion); [IT-Kanzlei Lutz on OLG Hamburg](https://datenschutz-rv.de/text-und-data-mining-olg-hamburg-erkennt-schrankenprivileg-an-ki-darf-crawlen/); plaintiff's status post (Dec 2025): [Kneschke blog](https://www.alltageinesfotoproduzenten.de/2025/12/22/aktueller-stand-meiner-klage-gegen-laion-e-v/)
- Technical implementation of machine-readable TDM reservations (robots.txt, TDMRep, meta tags). — [LAUSEN – TDM-Vorbehalt technische Umsetzung](https://lausen.com/der-text-und-data-mining-vorbehalt-technische-umsetzung-der-maschinenlesbarkeit/)
- **Givaudan robots.txt** (checked 2026-09-26): only `User-agent: *` with standard Drupal disallows (/admin/, /user/*, /search/, /node/add/, /comment/reply/, /media/oembed, /core/, /profiles/). There are **no GPTBot/CCBot/AI or TDM-specific blocks**. — [givaudan.com/robots.txt](https://www.givaudan.com/robots.txt)

### Inferences
- **[BK]** § 60d UrhG allows research organisations (universities) to reproduce works for TDM for non-commercial scientific research. There is no opt-out, and copies may be shared with a defined circle of researchers for joint research. § 87c Abs. 1 Nr. 4/5 UrhG extends the § 44b / § 60d exceptions to the database right. LG Hamburg (Sept 2024) applied § 60d to LAION. So an LMU project that is non-commercial and has no company as a "decisive influence" partner has a stronger footing than a spin-off or startup would under § 44b alone. Once the project turns commercial (a spin-off, or an industry partner with privileged access to results), § 60d may no longer apply. Verify with LMU legal (Referat for research law).
- **[BK]** Single facts and numerical values have no copyright. The database right (§ 87b) protects against extracting a qualitatively or quantitatively substantial part, or repeated systematic extraction of insubstantial parts, of a database built with substantial investment. Supplier catalogs of 100–300 entries probably qualify as protected databases. Scraping a *whole* catalog into a dataset is therefore the sensitive case. Harvesting a few fields per molecule for research use under § 60d / § 87c is the defensible case.
- **[BK]** Under CJEU Ryanair v PR Aviation (C-30/14), where a database is *not* protected, website terms of use can contractually restrict use. In Germany, browsewrap terms that were never actively accepted are hard to enforce. Terms accepted at login (clickwrap) are enforceable.
- Practical rule: publish the trained model and a derived dataset of (SMILES, source ID, value) facts with citations. Do **not** redistribute copied catalog text or odor descriptions verbatim. Honor robots.txt and rate limits, and keep a log of each site's ToU and robots.txt on the crawl date.

### Gaps
- The current text of Givaudan, dsm-firmenich, IFF, Symrise and TGSC terms of use was not read. TDMRep/ai.txt status for sites other than Givaudan was not checked.
- The OLG Hamburg judgment (Dec 2025) reference and case number were not captured, and neither was any BGH appeal status as of September 2026.

---

## Q5. Which contract instruments exist, and how does LMU handle them?

### Takeaway
The standard ladder runs: **CDA/NDA → Data Use/Transfer Agreement (DUA/DTA) or MTA → Research Collaboration Agreement (Kooperationsvertrag) or Sponsored Research (Auftragsforschung) → industrial PhD or master's thesis in industry**. At LMU, the Drittmittelreferat (third-party funding office) handles costing and contracts, and LMU Transfer / Entrepreneurship handles industry matchmaking. The German template set is the **BMWK "Mustervereinbarungen für Forschungs- und Entwicklungskooperationen"**, the German counterpart to the UK Lambert toolkit.

### Cited Findings
- LMU "Kollaborationsmöglichkeiten mit der Industrie" page:
  - Named contact: **Dr. Barbara Blaurock, Ecosystem Manager Life Sciences**.
  - The **Drittmittelreferat** advises on cost calculation and research contracts. The LMU Klinikum Legal & Compliance unit covers hospital staff.
  - The **Pivot-RP** database lists funding calls.
  - Industry matchmaking platforms are **Inpart** (companies post "Campaigns") and **HALO Science** (RFPs, expert consultation, materials; short online application).
  - Bavaria's **ESF+ STEP programme** offers €9 M for knowledge transfer from universities to SMEs in strategic technologies, with a deadline of **31 Oct 2026**.
  - Expressions of interest usually need no cost calculation.
  - The page does **not** detail NDA/MTA/contract types.
  - [LMU – Kollaboration mit der Industrie](https://www.lmu.de/de/forschung/entrepreneurship-und-transfer/kollaboration-mit-der-industrie/)
- LMU Transfer contact page. — [LMU Transfer – Kontakt](https://www.lmu.de/de/forschung/transfer/kontakt.html); LMU cooperations overview: [LMU Kooperationen](https://www.lmu.de/de/die-lmu/struktur/kooperationen/)
- LMU Klinikum "Abteilung Recht und Compliance" organigram (Aug 2025): a unit handles research contracts and third-party-funded contracts (design and review). This is Klinikum-side. — [LMU Klinikum organigram (PDF)](https://cdn.lmu-klinikum.de/8b80224715d00107/c12fe60f1191/Organigramm-REC-08_2025_anonym.pdf)
- German model agreements for R&D cooperation (BMWK, 2022 edition). Covers cooperation, contract research, background/foreground IP, publication and access-rights options. — [BMWK Mustervereinbarungen 2022 (PDF)](https://www.bundeswirtschaftsministerium.de/Redaktion/DE/Publikationen/Technologie/mustervereinbarungen-fuer-forschungs-und-entwicklungskooperationen-2022.pdf?__blob=publicationFile&v=2); older 2010 guideline: [Leitfaden BMWi 2010](https://www.innovationsfoerderung-hessen.de/mm/Leitfaden_KV_des_BMWi_April_2010.pdf)
- Comparable university practice pages with templates: TUM ForTe "Forschungs- und Wirtschaftskooperationen" brochure (de/en); Heidelberg and Ulm contract templates for industry, cooperation and contract research. — [TUM FWK brochure (PDF)](https://www.forte.tum.de/fileadmin/w00bgt/www/Forschungsfoerderung_new/FWK/0083-12-2024_TUM-FWK-Broschuere_dt_engl.pdf); [Uni Heidelberg Mustervertäge](https://www.uni-heidelberg.de/de/forschung/forschungsservice/formulare-richtlinien-mustervertraege/industrie-kooperationen-auftragsforschung); [Uni Ulm Verträge](https://www.uni-ulm.de/einrichtungen/zuv/dez1/recht-und-organisation/forschung-und-entwicklung-vertraege-rechtsberatung/)

### Inferences
- **[BK]** Legal distinction: under the EU state-aid framework for R&D&I (2022 Framework), **Auftragsforschung** (contract research) must be priced at market rate or full cost plus a margin, and the company gets the results and IP. **Kooperationsforschung** (collaboration) requires genuine shared risk and effective collaboration. Universities must stick to this split, and it shapes which IP terms LMU can accept. It is why LMU will insist on full-cost pricing if a company wants to own everything.
- Recommended ladder for this project:
  1. **Mutual CDA** (LMU template; 1–4 weeks).
  2. **Data Use Agreement** where the company provides potency data for non-commercial research. The company keeps the data. LMU owns the model, with a license-back or option for the company, and publishes aggregates.
  3. Alternatively, a **"model-to-data" evaluation agreement**: LMU sends the model or its predictions, the company scores them on internal data and returns only metrics. This is the lightest contract, and data never leaves the company.
  4. Only then a **Research Collaboration Agreement** with funding (PhD or postdoc) or an **industrial PhD / Master's thesis** at the company site.
- Company-side research sites to target **[BK]**: Givaudan fragrance research in Dübendorf/Kemptthal near Zürich (ingredients research); dsm-firmenich in Geneva (Satigny); Symrise in Holzminden (Germany's largest; runs student theses and internships); IFF in Hilversum/Union NJ; Takasago Europe in Paris/Zülpich; Kao in Tokyo/Wakayama; BASF Aroma Ingredients in Ludwigshafen. Symrise and BASF are German, which makes contract law and travel simpler.

### Gaps
- The name of LMU's central research-contracts unit (e.g. "Referat Forschungsförderung/Drittmittel" or "Rechtsabteilung Verträge"), and whether LMU publishes its own CDA/MTA/DUA templates, were not confirmed on the LMU (non-Klinikum) side.
- LMU Spin-off Service and LMU Innovation & Entrepreneurship Center details were not fetched. They matter if the model is later commercialised.

---

## Q6. What IP and publication terms do companies demand, and what can academics negotiate?

### Takeaway
Typical industry asks are: prior review of publications (30–90 days), the right to delete their confidential information, a patent-filing delay, ownership of or an exclusive licence to results in their field, and a no-redistribution clause on their data. Academics can usually secure: the right to publish after review, no deletion of the *results*, and LMU ownership of models trained with LMU methods. The company gets a non-exclusive or option-to-exclusive licence. Its data stays confidential, and only aggregate metrics are released.

### Cited Findings
- The BMWK model agreements give standard options for ownership of results ("Arbeitsergebnisse"), access rights, publication clauses with review periods, and background/foreground IP. They are the German reference framework that LMU and company lawyers will recognise. — [BMWK Mustervereinbarungen 2022](https://www.bundeswirtschaftsministerium.de/Redaktion/DE/Publikationen/Technologie/mustervereinbarungen-fuer-forschungs-und-entwicklungskooperationen-2022.pdf?__blob=publicationFile&v=2)
- TUM's cooperation brochure (a Munich peer institution) sets out the contract-type choices and their IP consequences for industry partners. — [TUM FWK brochure](https://www.forte.tum.de/fileadmin/w00bgt/www/Forschungsfoerderung_new/FWK/0083-12-2024_TUM-FWK-Broschuere_dt_engl.pdf)

### Inferences (negotiation positions, **[BK]**; typical market practice, not verified per company)
- **Publication:** accept a 30–60-day review, and a further 60–90 days only for patent filing. Refuse any veto over scientific conclusions. Define "Confidential Information" narrowly as the raw data table, structures of non-commercial molecules, and internal methods.
- **Data:** the company's data remains the company's. LMU gets a non-exclusive, non-transferable research licence and deletes or returns the data at term end. Publications report only performance metrics, plus possibly binned or anonymised aggregates. Molecule identities are not released.
- **Model ownership:** the model architecture and code trained on combined data are the hardest point. Viable compromises:
  - (a) LMU owns code and architecture and publishes models trained on public data only. The company-data-trained weights stay with the company, or are jointly owned but unpublished.
  - (b) The company gets a royalty-free internal-use licence to the fine-tuned model.
  - (c) The company gets an option for an exclusive field-of-use licence (fragrance) at market terms.
- **Exclusivity:** resist exclusivity over the *method*. Accept a time-limited (e.g. 12–24 months) exclusivity on the company-data-derived model in fragrance use only.
- **DSGVO:** only relevant if human panel data with personal information is shared. Odor-threshold tables are not personal data.
- **Students:** for master's theses at a company, the thesis must remain gradable and publishable in the library. A "Sperrvermerk" (blocking notice, e.g. 5 years) is common in German industry theses. Confirm it is acceptable under the LMU examination rules.

### Gaps
- No published fragrance-company standard research agreement (e.g. Givaudan or Symrise academic templates) was found.

---

## Q7. What do companies value in return?

### Takeaway
F&F houses value: (1) **models they can use internally** (all big houses now run AI formulation tools: Givaudan's Carto, and Osmo-style startups are competitors); (2) **independent benchmarking** of their in-house models; (3) **talent pipeline** (PhD/MSc hires with ML + chemistry skills); (4) joint publications and scientific prestige; (5) **prospective validation** on new molecules. A "model-to-data" offer is the lowest-risk proposition for them.

### Cited Findings
- Givaudan already operationalises threshold/VP-based "odour value" maps in its AI tool Carto. The company therefore has internal potency data and a use case for better predictors. — [Givaudan Carto press release](https://www.givaudan.com/file/156296/download); [Givaudan odour value definition](https://www.givaudan.com/fragrance-beauty/fragrance-ingredients-business/fragrance-molecules/sustainability-parameters)
- Givaudan publicised an in-house scent-receptor breakthrough (2025), quoting its Global Head of Science & Technology Fragrances (Jeremy Compton) and its Head of Ingredients Research Fragrance S&T (Agnes Bombrun). No academic partner is named in the release, so these are the relevant R&D leadership names to know. — [Givaudan scent receptor research 2025](https://www.givaudan.com/media/trade-media/2025/scent-receptor-research)
- A competitive threat that motivates the incumbents: Osmo raised a **$70 M Series B (Feb 2026)** and scaled its "AI-powered olfaction technology" and executive team. — [BusinessWire – Osmo Series B](https://www.businesswire.com/news/home/20260204293785/en/Osmo-Digital-Scent-Design-Company-Announces-$70M-in-Series-B-Funding-and-Executive-Leadership-Team-to-Scale-AI-Powered-Olfaction-Technology); [Trellis](https://trellis.net/article/ai-fragrance-tech-startup-osmo-hires-execs-raises/)
- Osmo's COO brings more than 15 years of F&F experience from Phoenix, Givaudan and IFF, which shows people moving from the houses into AI startups. Osmo claims "the industry's largest structured scent data library". — [Contrary Research – Osmo](https://research.contrary.com/company/osmo) (secondary source)

### Inferences
- Pitch framing for the houses: "Independent, publishable benchmark of potency prediction. Your data never leaves your servers. You get an internal-use licence to the fine-tuned model, plus first access to students." Givaudan has Carto and its own receptor programme, so it is the least likely to need outside modelling. Symrise (German, Holzminden), BASF Aroma Ingredients (German), Takasago, Kao and mid-size houses (Robertet, Mane, CPL, Expressions Parfumées) may value an academic model more.
- Prospective validation is the strongest currency. The researcher predicts potency for the company's *unpublished* candidate molecules. The company measures them and reports only the hit rate. Both sides get a publishable result, and no data is transferred.

### Gaps
- No public statement found from any F&F house on its academic data-sharing policy.

---

## Q8. What precedents exist of academics getting fragrance or olfaction data from industry?

### Takeaway
Documented precedents of *fragrance houses handing potency data to academics* are scarce in public sources. The best-known ML olfaction datasets came from academic psychophysics (Keller/Vosshall), from expert or commercial compendia later released (Leffingwell to Zenodo/Pyrfume), or from startup–academic partnerships (Osmo–Monell). Locally, Leibniz-LSB@TUM in Freising is the strongest institutional partner: it holds a curated threshold database and has a long industry-project tradition.

### Cited Findings
- **Keller & Vosshall (Rockefeller):** 480 structurally diverse molecules, two concentrations, 55 subjects, rating intensity, pleasantness, familiarity and 19 semantic descriptors. This became the basis of the **DREAM Olfaction Prediction Challenge** (Keller et al., Science 2017), where models predicted intensity, pleasantness and 8 of 19 descriptors. Industry funding of this work could **not** be confirmed. — [PubMed 27502425 (BMC Neurosci 2016)](https://pubmed.ncbi.nlm.nih.gov/27502425/); [Science 2017](https://www.science.org/doi/10.1126/science.aal2014); [bioRxiv preprint](https://www.biorxiv.org/content/10.1101/049999v1.full.pdf)
- **Leffingwell PMP 2001 database** (a commercial perfumery-materials compendium by Leffingwell & Associates): 3,523 molecules with expert descriptors, released as a Zenodo dataset and integrated into Pyrfume. This is a precedent of a commercial dataset being opened for ML. — [Leffingwell Odor Dataset, Zenodo 4085097](https://explore.openaire.eu/search/dataset?pid=10.5281%2Fzenodo.4085097); [Pyrfume Sci Data 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11557823/)
- **Osmo–Monell:** Joel Mainland (Monell) is on Osmo's Scientific Advisory Board, and Monell is listed as Osmo's olfactory-psychophysics partner. The Principal Odor Map (Lee et al., Science 2023) came out of Google Research, later Osmo, with Monell panels. — [Contrary Research – Osmo](https://research.contrary.com/company/osmo); [Science 2023 – Principal Odor Map](https://www.science.org/doi/10.1126/science.ade4401); [Monell 2024 Annual Report](https://annualreport.2024.monell.org/)
- **Leibniz-LSB@TUM (Freising):** Odorant Database (>1,700 odorants, thresholds in matrices, >700 publications). It has a research-projects portal and "Research Networks and Collaborative Projects". A specific Symrise joint project was **not** confirmed in this session. — [Odorant Database](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-odorant-database/start/); [Leibniz-LSB projects](https://portal.fis.leibniz-lsb.tum.de/en/projects/); [Research networks](https://www.leibniz-lsb.de/en/research/research-networks-and-collaborative-projects); [Aroma Chemistry section](https://portal.fis.leibniz-lsb.tum.de/en/organisations/aroma-chemistry/)
- A recent open laymen dataset (74 mono-molecular odors) shows that academic groups keep generating their own data rather than obtaining industry data. — [Scientific Data 2025](https://www.nature.com/articles/s41597-025-04644-2)

### Inferences
- **[BK, unverified]** Other known relationships to check:
  - Firmenich and University of Geneva (long-standing chemistry and olfaction ties).
  - Givaudan and ETH Zürich / Univ. Zürich (Kraft teaches as Titularprofessor at ETH, or at least lectures; verify).
  - Kao and Japanese universities.
  - Symrise's funding of research at TU Munich / Hamburg, and Symrise's "Holzminden" student programmes.
  - Mainland-lab papers acknowledging industry reagents or data.

  Look in the acknowledgements and funding statements of relevant papers. That is the fastest way to find real precedents and the named industry scientists who approved data release.
- The weak public record suggests that direct data transfer from F&F houses to academics is rare. Collaboration usually takes the form of company scientists as co-authors publishing *their own* data (as Kraft does), or of funded PhD positions.

### Gaps
- No verified evidence was found of IFF funding Keller/Vosshall, a Givaudan–ETH/EPFL data deal, a Firmenich–UNIGE data deal, Kao–Wakayama, or a TUM/Weihenstephan–Symrise potency-data project. All of these remain unconfirmed.

---

## Q9. Realistic assessment: success probability, timelines, contacts and entry points

### Takeaway
The chance of a big house simply handing over a potency dataset is low (roughly 10–20%). A model-to-data or prospective-validation arrangement has a moderate chance (roughly 30–50%), especially with German or mid-size houses. Timelines: 1–3 months to a first meeting via a warm introduction, 2–6 months for a CDA plus DUA, and 6–12 months for a funded collaboration or industrial PhD. **[all estimates]** The best entry points are conferences where industry R&D scientists present, and the Freising cluster (Leibniz-LSB, TUM Weihenstephan, Fraunhofer IVV).

### Cited Findings
- **Weurman Flavour Research Symposium:** held every three years in Europe. The **18th edition is in 2027, in Copenhagen**. The 17th was hosted by WUR. — [Wonderful Copenhagen – 18th Weurman 2027](https://www.wonderfulcopenhagen.com/18th-weurman-flavour-research-symposium-2027-gdk1151813); [WUR – 17th Weurman](https://www.wur.nl/en/activity/17th-international-weurman-flavour-research-symposium.htm)
- **ECRO:** annual European chemoreception meeting. ECRO lists a **Paris 2026** meeting. **ISOT** takes place every 4 years and rotates between Europe, Japan and the USA. — [ECRO Paris 2026 meeting page](https://www.ecro.online/meetings/paris-2026/meeting/); [Tasting Science conference list](http://tastingscience.info/advanced/conferences/)
- Industry-posted research calls on **Inpart** and **HALO Science** are officially promoted by LMU as entry points. Companies post RFPs there, and researchers can apply directly. — [LMU Kollaboration mit der Industrie](https://www.lmu.de/de/forschung/entrepreneurship-und-transfer/kollaboration-mit-der-industrie/)
- The LMU Life-Sciences ecosystem manager (Dr. Barbara Blaurock) is the named internal first contact for initiating industry cooperation. — [LMU page](https://www.lmu.de/de/forschung/entrepreneurship-und-transfer/kollaboration-mit-der-industrie/)
- Leibniz-LSB@TUM runs public outreach events on odor and taste research ("Einblicke in die Geruchs- und Geschmacksforschung"). — [Leibniz-LSB activity](https://portal.fis.leibniz-lsb.tum.de/en/activities/einblicke-in-die-geruchs-und-geschmacksforschung/)

### Inferences (playbook)
1. **Build the public baseline first:** Pyrfume + Leibniz-LSB DB + Kraft/Givaudan GC-O thresholds + catalog tenacity. Publish a preprint with an honest noise analysis. A working model plus a clear gap statement is what makes companies take the meeting.
2. **Go warm, not cold:**
   - Ask LMU Transfer (Blaurock) and your supervisor for introductions.
   - Contact Leibniz-LSB (Freising) as a scientific partner. Its staff have industry links, and co-supervision adds credibility.
   - Contact the *scientists* who publish (e.g. Kraft at Givaudan; the Firmenich and Symrise authors of threshold papers) before business development.
3. **Offer model-to-data first:** a 1–2-page proposal stating the question, the offer (prospective predictions on their blinded molecules, and an internal-use licence) and the ask (evaluation metrics only, and co-authorship). Sign a CDA only once they are interested.
4. **Where to meet people:**
   - ECRO (annual), Weurman 2027 (Copenhagen), ISOT (next likely 2028 **[unverified]**).
   - AChemS (USA, annual) **[BK]**.
   - Wartburg Symposium on Flavor Chemistry & Biology (Eisenach, organised with Leibniz-LSB/DFA tradition; roughly every 3 years) **[BK]**.
   - GDCh Lebensmittelchemische Gesellschaft regional meetings **[BK]**.
   - IFEAT and World Perfumery Congress (industry-heavy) **[BK]**.
5. **Target list by likelihood:**
   - Symrise (German; Holzminden; strong thesis and internship culture) and BASF Aroma Ingredients (Ludwigshafen): high relevance, German contracts.
   - Mid-size houses (Mane, Robertet, CPL, Takasago Europe, Kao Chemicals Europe): may value external modelling most.
   - Givaudan / dsm-firmenich / IFF: prestigious, but they have the strongest internal AI and are the most protective.
6. **Funding levers that make the ask cheaper for companies:**
   - Bavarian or federal co-funding: ESF+ STEP (SMEs, deadline 31 Oct 2026), BMBF/BMFTR programmes, ZIM for SMEs **[BK]**, DFG transfer projects (Erkenntnistransfer) **[BK]**, and an industrial PhD co-funded by a company.
   - A company paying 30–50% of a PhD position is a common entry size **[BK / estimate]**.

### Gaps
- Exact 2026–2028 dates and venues for ISOT, AChemS, Wartburg and the next GDCh LChG meetings were not verified.
- Names of current open-innovation or academic-partnership managers at Symrise, dsm-firmenich and IFF were not found.
- No public success-rate statistics exist for academic data requests to F&F houses. The probabilities above are judgment estimates.
