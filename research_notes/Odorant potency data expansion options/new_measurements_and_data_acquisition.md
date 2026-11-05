# Generating new odor potency data vs. acquiring proprietary data (options, costs, difficulty)

Scope note: researched 2026-09-26. About 40 tool calls. Most vendors and contract labs do **not** publish prices. Every price below is either quoted from a primary page (marked "quoted") or is an explicitly labelled **ESTIMATE** with its assumptions shown. The estimates come from general domain knowledge and were not verified in this session, so the report writer should keep the ESTIMATE label.

---

## 1. Human sensory threshold measurement: methods, panel, throughput, cost per compound

### Takeaway
The workhorse is ASTM E679-19: a 3-alternative forced-choice (3-AFC) test run up an ascending geometric concentration series, with each panellist's best-estimate threshold (BET) combined as a geometric mean. Panels should have at least 15 assessors, and they should be screened for sensitivity and repeatability (EN 13725 uses n-butanol). A small lab using sniffing bottles or a dynamic olfactometer could realistically measure about 3–8 compounds per week, at roughly €300–800 per compound (ESTIMATE) excluding equipment. The dominant hidden costs are chemical purity (odour-active trace impurities) and headspace/vapour calibration, not panel pay.

### Cited Findings
- ASTM E679-19 prescribes 3-AFC with an ascending concentration series. Each presentation holds 1 target and 2 blanks, and target concentration increases in a geometric progression. A judge's BET is the geometric mean of the last-missed concentration and the next higher step. The individual BET is the geometric mean over replications, and the group BET is the geometric mean over individuals — [ASTM E679-19](https://www.astm.org/Standards/E679.htm); [iTeh ASTM E679-19 summary](https://standards.iteh.ai/catalog/standards/astm/eead58ea-6fc2-4ed3-bfa1-fb91ffc86e4f/astm-e679-19)
- ASTM has an open revision work item, WK90516 ("Revision of E679-19"), so the standard may change — [ASTM WK90516](https://www.astm.org/workitem-wk90516)
- Known weaknesses of E679 BET and proposed fixes: Chemical Senses proposes fitting psychometric functions with a fixed-slope parameter to E679 data. Food Quality & Preference proposes a method-independent threshold definition within E679 — [Chem Senses 39(3):229](https://academic.oup.com/chemse/article/39/3/229/503441); [FQP 2012](https://www.sciencedirect.com/science/article/abs/pii/S0950329312000286)
- A 2026 data-driven review (PMC13420774) makes several points relevant to design:
  - It calls 3-AFC "the most widely used and internationally recognized psychophysical technique for determining OTs".
  - It calls dynamic olfactometry the gas-phase "gold standard", limited by "high equipment costs, complex operation and maintenance requirements".
  - It says GC-O with dynamic dilution for thresholds "has so far been rarely applied".
  - Early inter-laboratory results differ by "two to three orders of magnitude".
  - BET validity needs at least 15 assessors.
  — [Odor Thresholds in Flavor Science: A Data-Driven Review (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)
- The same review shows that the analysis choice alone moves thresholds. For ethyl hexanoate from the same 3-AFC data, the CF method gives 861 µg/L and BET gives 507 µg/L (p = 1.7e-10). Panel type also matters: 2-phenylethanol is 871 µg/L for experts vs 2042 µg/L for consumers (p < 0.01). The review compiled thresholds for 848 compounds across 11 matrices from 146 studies (712 in water/air). Implication: method and panel metadata must be recorded as model covariates — [PMC13420774](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)
- EN 13725 panel screening: assessors qualify if the geometric mean of at least 12 individual threshold estimates for n-butanol lies between 20 and 80 ppb (0.02–0.08 µmol/mol) and the antilog of the SD of log ITEs is below 2.3 — [Gostelow/Sensors review, PMC3231359](https://pmc.ncbi.nlm.nih.gov/articles/PMC3231359/); [WST 2010 panel selection](https://doi.org/10.2166/wst.2010.023); [Scentroid wiki "Assessor"](https://scentroid.com/wikiodour/assessor/)
- EN 13725 was revised as EN 13725:2022 (scope: odour concentration and emission rate by dynamic olfactometry) — [iTeh EN 13725:2022](https://standards.iteh.ai/catalog/standards/cen/67f31e88-f81d-4e78-bbf6-ce1dcb766eeb/en-13725-2022); [Update on revised EN 13725:2021 (ResearchGate)](https://www.researchgate.net/publication/351942376_Update_on_the_revised_EN_137252021)
- Even with n-butanol reference calibration, large inter-laboratory variability persists in EN 13725-type measurement. A 2024 Atmospheric Environment paper examines n-butanol's role as the reference and the origins of that variability — [Atmos Environ 2024](https://www.sciencedirect.com/science/article/pii/S1352231024001845)
- The triangle odor bag method (Japan) and dynamic olfactometry give systematically different odour concentrations for the same samples — [ResearchGate: triangle bag vs dynamic olfactometry](https://www.researchgate.net/publication/24311851_Difference_in_the_odor_concentrations_measured_by_the_triangle_odor_bag_method_and_dynamic_olfactometry)
- Individual assessor response behaviour at threshold (McGinley, IWA 2017) and the differences between European and US odour standards are documented by St. Croix Sensory — [McGinley IWA2017 PDF](https://www.fivesenses.com/wp-content/uploads/2024/05/McGinley-IWA2017.pdf); [Euro vs US odor standards](https://www.fivesenses.com/Documents/Library/21%20%20Euro%20vs%20US%20Odor%20Std.pdf)
- Dynamic olfactometers are commercially available from Olfasense (TO8 evolution, TO9 evolution) and Scentroid (SS600 6-station lab olfactometer). No public price was found — [Olfasense TO8](https://www.olfasense.com/odour-measurement-equipment/instruments/to8-evolution-olfactometer/); [Olfasense TO9](https://www.olfasense.com/odour-measurement-equipment/instruments/to9-evolution-olfactometer/); [Scentroid SS600](https://scentroid.com/products/olfactometers/ss600-laboratory-olfactometer/)
- Off-the-shelf olfactometers are described as expensive and in need of customisation, and some groups build low-cost lab olfactometers instead — [IEEE low-cost olfactometer](https://ieeexplore.ieee.org/document/8216486/); [Olfactometer (Wikipedia)](https://en.wikipedia.org/wiki/Olfactometer)
- A route for pure compounds via olfactometry is the "secondary reference odour mass" (SROM). The odour threshold mass of individual odorants (four odorants) is measured experimentally by EN 13725-style olfactometry. This is a published template for measuring single-compound air thresholds on an accredited olfactometer — [Environ Sci Eur 2025, SROM for four odorants](https://link.springer.com/article/10.1186/s12302-025-01179-6)
- Test–retest in large-scale intensity work: Keller & Vosshall (55 subjects, 480 molecules, 2 concentrations) included 40 repeated stimuli to assess reliability and excluded the 6 least-replicable subjects — [BMC Neurosci 2016](https://link.springer.com/article/10.1186/s12868-016-0287-2); [PubMed 27502425](https://pubmed.ncbi.nlm.nih.gov/27502425/)

### Inferences
- **ESTIMATE, in-house cost per compound (3-AFC sniffing bottles, E679).** Assumptions:
  - Panel: 16–20 screened panellists, 1–2 replicate ascending series each, 6–8 dilution steps.
  - Time: about 15–25 min of panellist time per compound per replicate.
  - Compensation: €12–15/h, a typical German university participant rate; this rate is not verified.
  - Totals:
    - Panel pay: 20 × 0.5 h × €15 ≈ **€150**.
    - Technician (dilution series, bottle prep, cleaning; 3–5 h at about €35–45/h): **€100–220**.
    - Consumables (odourless solvent or water, PTFE-lidded bottles/Teflon squeeze bottles, glassware): **€20–60**.
    - Purity check by GC-MS and ideally GC-O, run in-house or at a core facility: **€50–200**.
  - **Total about €300–650 per compound per matrix**, excluding PI time, chemical purchase, and one-off costs. One-off costs include the panel screening campaign (n-butanol, about 12 ITEs per candidate) and ethics.
- **ESTIMATE, throughput.** Fatigue and adaptation limit a session to about 3–4 compounds. With 2–3 sessions per week that gives about **3–8 compounds/week**, or about **150–300 per year** allowing for holidays and panel churn. Dynamic olfactometry in air is slower per compound because of calibration, but more reproducible.
- **ESTIMATE, equipment.** Commercial multi-station dynamic olfactometers (Olfasense TO8/TO9, Scentroid SS600) are likely in the **€40k–150k** range, plus an odour-neutral room with filtered air (roughly €10k–50k to fit out). Both figures are unverified and should be confirmed by quote. Sniffing-bottle 3-AFC needs only an odour-free room, glassware, and a balance, at under €5k.
- **Purity and trace impurities** are the biggest validity threat for low-potency compounds. A 0.1% impurity that is 10,000× more potent dominates the measured threshold. GC-O of the neat sample, or of its headspace at the threshold dilution, is the standard safeguard. Enantiomers can differ in threshold by orders of magnitude, so stereochemistry must be recorded.
- **Headspace vs liquid concentration.** Thresholds in water or oil bottles are liquid-phase concentrations. Air thresholds need a vapour-phase concentration (partition coefficients, or headspace GC calibration). Mixing the two phases is a known noise source in the free data.
- **Achievable reproducibility.** Given the reported 2–3 order-of-magnitude historic spread and roughly 2× method or panel effects even within one lab (review above), a well-run single-lab protocol could plausibly reach about ±0.3–0.5 log units within-lab replicate agreement. That is an inference, not a cited figure.

### Gaps
- No published per-compound cost or throughput benchmark was found for an academic E679 threshold lab.
- ISO 13301 (flavour/odour thresholds, 3-AFC) details were not retrieved; it is known to exist but was not verified here.
- Burghart (OM4/OM6 olfactometers for clinical/fMRI) pricing and suitability were not retrieved.
- Olfasense and Scentroid prices were not published anywhere found. Request quotes.
- No quantitative test–retest correlation for thresholds (as opposed to intensity) was retrieved in this session.

---

## 2. Commercial contract labs (EN 13725 odour labs, sensory CROs)

### Takeaway
Germany has many accredited EN 13725 olfactometry providers (TÜV SÜD, DEKRA, ODOCON, BUB, SFI, AltraSens, Olfasense/Odournet), and several operate in or near Bavaria. None publishes per-sample prices. These labs are built for emission samples (ou_E/m³), not pure-compound thresholds. They can measure a gravimetrically prepared bag of a pure odorant, from which threshold = concentration / odour concentration (the SROM approach), but you must supply and verify the concentration and purity yourself.

### Cited Findings
- Providers offering olfactometry or EN 13725 odour measurement in Germany: TÜV SÜD (Geruchsgutachten/Olfaktometrie), DEKRA (Geruchsmessung), ODOCON Hamburg, BUB Braunschweig (Geruchslabor), SFI (Sachverständige für Immissionsschutz), AltraSens, and Olfasense (Kiel; also sells TO8/TO9 olfactometers). TÜV Austria and Silsoe Odours (UK) also appear — [TÜV SÜD](https://www.tuvsud.com/de-de/branchen/produzierende-industrie/anlagenbau-betrieb/umwelt-klimaschutz/geruchsgutachten-olfaktometrie); [DEKRA](https://www.dekra.de/de/geruchsmessung/); [ODOCON](https://www.odocon.de/umweltanalytik/olfaktometrie); [BUB](https://www.bub-umwelt.de/leistungen/geruchslabor/); [SFI](https://www.sfimm.de/content/olfaktometrie); [AltraSens](http://www.altrasens.com/olfaktometrie.html); [Olfasense olfactometry](https://www.olfasense.com/olfactometry/); [TÜV Austria](https://www.tuv.at/geruchsmessung/); [Silsoe Odours](https://silsoeodours.com/olfactometry/)
- Odournet runs "Sensory and Molecular Odour Testing" labs combining GC-MS and GC-sniffing, a possible outsourcing route for purity and GC-O checks — [Odournet laboratories](https://www.odournet.com/laboratories/)
- TÜV lists "Geruchsprüfung" (odour testing) as a certificate type — [Certipedia](https://www.certipedia.com/certificate_types/343?locale=de)
- Olfactometric odour concentration is expressed in European odour units, and assessors judge dilutions presented by the olfactometer — [Olfaktometrie (de.wikipedia)](https://de.wikipedia.org/wiki/Olfaktometrie); [OST factsheet Olfaktometrie](https://www.ost.ch/fileadmin/dateiliste/3_forschung_dienstleistung/3.2_interdisziplinaere_themen/3.2.6_kmn_kompetenzzentrum_mathematik_und_naturwissenschaften/angewandte_chemie/pdf_angewandtechemie/230414_ost_kmn_factsheet_olfaktometrie.pdf)

### Inferences
- **ESTIMATE, EN 13725 lab analysis price:** likely about **€150–400 per olfactometric sample analysis** (lab-only, sample delivered in a Nalophan/PET bag), with discounts for bulk series. Field sampling and reporting add substantially. For a pure-compound threshold you would want at least 2–3 replicate bags, so about **€500–1,200 per compound** plus in-house bag preparation and concentration verification (GC). This is unverified; get 2–3 quotes (TÜV SÜD Munich, Olfasense, a Bavarian Messstelle nach §29b BImSchG).
- **Suitability caveat:** EN 13725 panels are 4+ screened assessors per measurement. That is fine for odour units but thinner than the ≥15 recommended for BET thresholds. Treat contract olfactometry as a *consistent single-protocol* source, not a population estimate.
- Sensory CROs for intensity ratings (dose–response, labelled magnitude scales) exist in Germany (for example food and consumer sensory institutes), but none was researched with prices in this session.

### Gaps
- No public price list or tender unit price for olfactometric analysis was found; German, English, and tender-oriented searches all returned nothing.
- Eurofins, Müller-BBM, and ODOURnet pricing and any "pure substance threshold" service were not verified.
- Sensory CRO (intensity panel) pricing: not found.

---

## 3. Ethics & regulation in Germany (LMU), GDPR

### Takeaway
An LMU member doing research on humans must apply to the LMU ethics committee (Medical Faculty) through the ethikPool-LMU portal, which has been mandatory since 15 Apr 2024. A smell-panel study is a non-AMG/MPDG study, and published fees apply only to AMG/MDR clinical trials (€3,500+). A healthy-volunteer sensory study is therefore probably fee-free for LMU members, but that is unverified. It still needs a protocol, German-language consent, data-protection consent, and institutional sign-off.

### Cited Findings
- "Every conducting member of the LMU" researching on humans, or with identifiable biomaterials or data, is entitled and obliged to apply. Applications have gone only through the ethikPool-LMU portal (www.ethikpool-lmu.de) since 15.04.2024 — [LMU Ethikkommission](https://www.med.lmu.de/de/fakultaet/wer-wir-sind/gremien-kommissionen/ethikkommission/); [Umstellung Antragstellung](https://www.med.lmu.de/de/fakultaet/wer-wir-sind/gremien-kommissionen/ethikkommission/umstellung-antragstellung/); [Wissenswertes](https://www.med.lmu.de/de/fakultaet/wer-wir-sind/gremien-kommissionen/ethikkommission/wissenswertes/)
- Non-AMG/MPDG applications need:
  - a study protocol (templates for prospective, interventional, and other designs)
  - German participant information and consent
  - data-protection consent documentation
  - written approval from institutional leadership
  - all study materials such as questionnaires
  New procedural standards have been mandatory since 01.07.2025 — [LMU Nicht AMG/MPDG](https://www.med.lmu.de/de/fakultaet/wer-wir-sind/gremien-kommissionen/ethikkommission/nicht-amg-mpdg/)
- Fee schedule (quoted): AMG mono- or multicentric review €3,500, MDR/MPDG lead €3,500, locally involved €800, amendments €200–1,500, accessory biobank €500. The page lists fees only for AMG/CTR and MPG/MDR/MPDG trials; fees are harmonised across Bavarian university committees — [LMU Gebühren](https://www.med.lmu.de/de/fakultaet/wer-wir-sind/gremien-kommissionen/ethikkommission/gebuehren/)
- LMU Munich School of Management runs its own ethics committee, relevant if the study sits outside medicine — [SOM Ethikkommission](https://www.som.lmu.de/de/forschung/ethikkommission/)
- Rules of procedure: [EK LMU Geschäfts- und Verfahrensordnung 2.0 (PDF)](https://cms-cdn.lmu.de/media/07-medizin/fakultaet-medizin/downloads/ethikkommission/g_vo_2022.pdf)

### Inferences
- Plan for about 1–3 months from submission to vote (ESTIMATE). Safety arguments should cite the following, keeping exposures far below occupational exposure limits, which threshold work does intrinsically:
  - use of food-grade or FEMA-GRAS or IFRA-compliant odorants
  - exclusion of CMR substances, strong sensitisers, and irritants such as isothiocyanates and aldehydes at high concentrations
  - screening for asthma, allergy, and pregnancy
- Under GDPR (Art. 9), health-related data (smell loss, allergies) is special-category data. Pseudonymise panellist IDs, keep consent forms separate, and write a data-management plan allowing open release of aggregated or per-panellist pseudonymous thresholds (consent must explicitly cover open data publication).
- Non-LMU (private/commercial) generation would need an independent ethics committee such as the Bavarian Landesärztekammer, which charges fees. Not verified.

### Gaps
- Whether non-AMG studies by LMU members are fee-free, and typical turnaround times, are not stated on the pages retrieved. Email [contact omitted] to confirm.

---

## 4. Crowdsourced / at-home approaches

### Takeaway
Large lay-panel datasets exist for quality, pleasantness, and intensity at 1–2 fixed concentrations: Keller & Vosshall (55 subjects × 480 molecules) and the Sci Data 2025 set (1,227 participants × 74 odorants). None measures thresholds. At-home threshold testing is limited by uncontrolled dilution, headspace, cross-contamination, and ambient odour. It is suited to *relative intensity* or *perceived strength at fixed dose* rather than absolute ODTs.

### Cited Findings
- Keller & Vosshall 2016 tested 480 structurally diverse molecules at two concentrations on 55 healthy subjects. They rated intensity, pleasantness, familiarity, and 20 semantic descriptors, with 40 repeated stimuli for reliability. This dataset underlies the DREAM Olfaction Prediction Challenge — [BMC Neuroscience](https://link.springer.com/article/10.1186/s12868-016-0287-2); [Keller et al., Science 2017 (DREAM)](https://www.science.org/doi/10.1126/science.aal2014)
- Bierling et al., Sci Data (Feb 2025): 1,227 lay participants described and rated 74 chemically diverse mono-molecular odorants (free descriptions, evaluative ratings, qualitative labels) plus demographics and personality. The data is on Zenodo — [Sci Data 2025](https://www.nature.com/articles/s41597-025-04644-2); [PMC11865284](https://pmc.ncbi.nlm.nih.gov/articles/PMC11865284/); [Springer Nature Community post](https://communities.springernature.com/posts/olfactory-research-needs-more-data-a-dataset-of-laymen-olfactory-perception-for-74-mono-molecular-odors)
- Olfactory sensitivity varies across geographical locations (Sci Rep 2026), a population-sampling caveat for crowdsourced thresholds — [Sci Rep 2026](https://www.nature.com/articles/s41598-026-38727-w)
- An ordinal odour-strength ML dataset of more than 2,000 molecules (odourless, low, medium, high) was built from two public sources. This shows coarse "strength" labels can be scaled cheaply — [arXiv 2512.08683](https://arxiv.org/abs/2512.08683)

### Inferences
- A mailed kit (pre-diluted sealed vials, 3-AFC triplets per step) is feasible for about 10–20 compounds per kit. At a plausible €15–40 per kit including postage and chemicals (ESTIMATE), plus participant incentives, it yields population-level *relative* thresholds with large per-person noise. Chemical stability in transit (oxidation, adsorption to caps) and headspace equilibration at unknown temperatures limit absolute accuracy to perhaps ±0.5–1 log unit (inference).
- Better use of crowdsourcing: rank-order or "which is stronger" comparisons at matched vapour concentrations, which feed pairwise or ranking models of potency.

### Gaps
- SmellSpace and other online platforms were not researched in this session.
- No validation study was found comparing at-home thresholds with lab ASTM E679 thresholds.

---

## 5. Instrumental / biological proxies (GC-O, e-nose, OR HTS assays, animal models)

### Takeaway
Human OR cell assays (Hana3A with CRE-luciferase) give dose–response EC50s at medium throughput. Within narrow chemotypes (musks) receptor potency tracked human thresholds closely (r ≈ 0.87), and EC20 of OR5A2 relates to sensory thresholds. Across all chemistry, however, the relevant receptor(s) are usually unknown, so OR data is best used as auxiliary features or multitask targets, not as threshold substitutes. E-noses do not measure human thresholds. GC-O/AEDA gives relative potency (FD factors) useful for ranking.

### Cited Findings
- The Hana3A protocol (JoVE/PMC4163990) expresses most of the OR repertoire in Hana3A cells with a CRE-luciferase readout. It screens odorant panels × OR panels and runs dose–response confirmation. Example: 328 ORs × 26 odorants. Up to about 4 h of odorant stimulation may be needed with standard plate readers — [PMC4163990](https://pmc.ncbi.nlm.nih.gov/articles/PMC4163990/); [JoVE 51640](https://www.jove.com/t/51640/high-throughput-analysis-mammalian-olfactory-receptors-measurement); [PubMed 24961834](https://pubmed.ncbi.nlm.nih.gov/24961834/)
- A real-time live-cell cAMP assay (GloSensor-type) is an alternative readout — [PMC5752358](https://pmc.ncbi.nlm.nih.gov/articles/PMC5752358/)
- State of deorphanization, including luciferase and Ca-imaging methods: [Peterlin et al., JGP 2014 "report from the orphanage"](https://rupress.org/jgp/article/143/5/527/43283/The-state-of-the-art-of-odorant-receptor); [ResearchGate: Deorphanization by luciferase and Ca-imaging](https://www.researchgate.net/publication/236181751_Deorphanization_of_Human_Olfactory_Receptors_by_Luciferase_and_Ca-Imaging_Methods)
- Human OR expression plasmids (pCI vector, Rho-tag) contributed by Hiroaki Matsunami are distributed individually by Addgene (e.g., pCI-OR2W1 #21686, pCI-OR51E2 #22324, pCI-OR2J2 #22321, pCI-OR2C1 #22320), from Science Signaling 2009 — [Addgene 21686](https://www.addgene.org/21686/); [Addgene 22324](https://www.addgene.org/22324/); [Addgene 22321](https://www.addgene.org/22321/)
- Search snippets (not full-text-verified, and the exact source paper among the linked Current Biology articles is uncertain) report:
  - musk detection thresholds vs receptor EC50: Pearson r = 0.87, with thresholds inversely related to receptor potency and efficacy
  - EC20 of OR5A2 correlates with sensory detection thresholds
  - median EC50 of about 1.6 µM for the best ligand across tested ORs, from high-expression heterologous systems
  — [Current Biology 2025 "Decoding human olfaction by high heterologous expression…"](https://www.cell.com/current-biology/fulltext/S0960-9822(25)01211-4); [Current Biology 2023 "Allosteric modulation of a human odorant receptor"](https://www.sciencedirect.com/science/article/pii/S0960982223003044); [phys.org summary Oct 2025](https://phys.org/news/2025-10-lab-boosted-olfactory-receptor-reveals.html)
- Leibniz-LSB@TUM also maintains a Receptor Database (odorant–receptor pairs), a partnership target — [Leibniz-LSB@TUM Receptor Database](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-receptor-database/)
- Validating sensor arrays against human-nose detection ability is itself patented as a method, a signal that e-nose-to-human mapping is non-trivial — [US 6844197](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6844197)

### Inferences
- **ESTIMATE, OR HTS cost.** A 384-well plate of dual-luciferase (for example Dual-Glo) with transfection reagents, plasticware, and cells probably costs about €150–400 in consumables. A full dose–response (8 concentrations × triplicate) for 1 odorant × 1 OR uses about 24–48 wells. Screening 400 human ORs × 1 odorant at 1–2 concentrations is about 1–3 plates, so roughly €300–1,000 in consumables per odorant for a repertoire-wide screen (cell culture, luminometer, and staff are extra). Plasmid libraries: Addgene charges per plasmid, roughly $100 academic; the full ~400-OR set via Addgene would be costly, and the Matsunami lab or MTA route is more realistic. Unverified.
- Use OR responses as auxiliary tasks or features, not labels. Threshold is governed by the most sensitive receptor plus air/mucus partitioning and transport, so a missing receptor gives a false "weak".
- GC-O/AEDA flavour dilution factors are matrix- and extract-dependent. Convert to thresholds only with quantitation and internal standards.
- Insect or mouse behavioural and electrophysiological proxies were not researched. Species receptor repertoires differ, so they are expected to correlate poorly with human ODTs.

### Gaps
- Not verified: actual Addgene per-plasmid price in 2026, availability of a complete human OR library (Matsunami lab / Duke), and commercial OR screening CRO prices (e.g., ChemCom, Givaudan in-house).
- No cross-chemotype correlation between OR EC50 and human ODT (beyond musks) was retrieved.

---

## 6. Purchasing odorants

### Takeaway
No catalogue prices were retrieved in this session. By ESTIMATE, 500 diverse pure aroma chemicals would cost about €25k–75k (median about €50–150 per compound at 5–25 g). Rare sulfur compounds, pyrazines, lactone enantiomers, and single stereoisomers cost €300–2,000+ each and push the upper tail. Purity (≥98–99% GC) must be re-verified by GC-MS/GC-O regardless of supplier.

### Cited Findings
- No sourced price data was obtained for Sigma-Aldrich/Merck FCC, TCI, Vigon, or Perfumer's Apprentice in this session. See Gaps.

### Inferences
- ESTIMATE assumptions: Sigma/Merck FCC-Kosher grade and TCI catalogue items for common aroma chemicals typically cost €30–150 for 5–100 g. Specialty items (thiols, methoxypyrazines, enantiopure lactones or ionones) often cost €200–1,500 for 100 mg–1 g. Perfumer's Apprentice, Vigon, and similar suppliers are cheap but give weaker purity documentation, which is fine for pilot work but not for benchmark thresholds.
- Enantiomers: buy or order both where they are chiral, or record "racemate". Thresholds of enantiomers can differ by more than 100×. The Leffingwell "Chirality & Odour" pages list many examples, but these were not fetched.

### Gaps
- Real catalogue prices for a representative 500-compound list were not collected. That needs a scripted catalogue query by CAS, or quotes.

---

## 7. Buying/licensing existing proprietary data (VCF, van Gemert, Leffingwell/BACIS, Leibniz-LSB, Good Scents)

### Takeaway
The largest curated threshold compilations are van Gemert (about 22,000 threshold values; about 1,790 compounds in air and 1,860 in water) and VCF. Their prices are modest: VCF online is €1,485/yr, and BACIS VCF 2000 is a US$2,775 one-PC licence. Both are licensed for *consultation*: the standard licences are per-user or per-site, non-exclusive, and do not grant rights to systematic extraction or model redistribution. For ML you need an explicit written data-licence or TDM clause. Leibniz-LSB@TUM (about 1,700 odorants) encourages scientific use with attribution but forbids systematic downloading without permission. It is 20 km from Munich, which makes it the most natural partner.

### Cited Findings
- **VCF online (Volatile Compounds in Food, vcf-online.nl):** subscription only, **€1,485 per year**. All staff at one company location may access it without extra cost, each user gets a personal login, and IP-based access is available on request. It holds 2,112 products and more than 13,300 volatile compounds across 18 chemical classes — [VCF Home](https://www.vcf-online.nl/); [VCF promotion page](https://www.vcf-online.nl/VcfPromo.cfm); [VCF compounds](https://www.vcf-online.nl/VcfCompounds.cfm); [VCF Guide](https://www.vcf-online.nl/VcfGuide.cfm?title=What+information)
- **BACIS VCF 2000 (offline, distributed by Leffingwell):** "PRICE: U.S. $2775.00". It is a "non-exclusive license granting rights to use the … Database and product files on one (1)" computer, with a separate licence and fee for each PC and US$350 per additional user at the same location — [Leffingwell VCF 2000](http://www.leffingwell.com/bacis1.htm)
- **BACIS PMP 2001 (Perfumery Materials & Performance):** more than 4,100 perfumery materials. US$2,775 for a non-exclusive licence plus US$250 per additional user — [Leffingwell PMP 2001](http://www.leffingwell.com/bacispmp.htm)
- **van Gemert, "Compilations of Odour/Flavour Threshold Values in Air, Water & Other Media" (2011 eds., two books):**
  - about 22,000 threshold values from about 2,930 references up to 2010
  - about 1,790 compounds with odour thresholds in air, about 1,860 in water, and about 760 in other media
  - about 2,160 with flavour thresholds in water, about 1,010 in other media, and 680 peptides
  - units normalised to mg/m³ (air) and mg/kg
  - "Available only from Oliemans Punter & Partners" (Utrecht), ordered by writing or calling; no price listed
  — [Leffingwell bacis2 page](http://www.leffingwell.com/bacis2.htm); [Google Books record](https://books.google.com/books/about/Odour_Thresholds.html?id=5LnPGAAACAAJ)
- The order website listed for van Gemert, thresholdcompilation.com, currently returns a Dutch parked-domain page ("Er is geen webhostingpakket actief"). The ordering channel may be defunct, so contact Oliemans Punter by post or phone (checked 2026-09-26 via curl) — [thresholdcompilation.com](http://www.thresholdcompilation.com/)
- Unlicensed PDF copies of van Gemert circulate on docplayer, silo.tips, and academia.edu. Using them for ML would be a copyright and database-right problem, not a solution — [docplayer listing](https://docplayer.net/21077515-Odour-thresholds-compilations-of-odour-threshold-values-in-air-water-and-other-media-edition.html)
- **Leffingwell Flavor-Base 10th ed.** includes an "Odor Thresholds" file giving threshold ranges in various media with references (price not extracted). The site's terms state that copying, redistribution, or use of materials requires permission and that no licence is implied — [Flavor-Base](http://www.leffingwell.com/flavbase.htm); [Leffingwell terms](http://www.leffingwell.com/terms_of_service.htm)
- **Leibniz-LSB@TUM Odorant Database v1.2 (2022):**
  - more than 1,700 odorants from more than 700 publications
  - retention indices, odour qualities, odour thresholds in different matrices, and foods where the odorants are odour-active
  - Terms: "use and dissemination of data … for scientific purposes is encouraged provided that full acknowledgement of the source is given". Systematic downloading, use in competing products, and reproduction of the database are prohibited without permission.
  - Contact: contact.leibniz-lsb(at)tum.de, +49 8161 71-2928, Lise-Meitner-Str. 34, 85354 Freising.
  - Citation: Kreissl, Mall, Steinhaus, Steinhaus 2022.
  — [Start page](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-odorant-database/start/); [Copyright & citation](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-odorant-database/copyright-and-citation); [ACS Spring 2025 talk](https://acs.digitellinc.com/p/s/valuable-tool-for-flavor-scientists-the-leibniz-lsb-at-tum-odorant-database-571376)

### Inferences
- **Terms that typically restrict ML**, as seen here:
  - (a) per-seat or per-PC licences that bar bulk export or systematic download (Leibniz-LSB, BACIS)
  - (b) "no reproduction of the database in any format", which covers derivative datasets
  - (c) EU sui generis database right (Directive 96/9/EC): extracting a substantial part is infringing even when individual facts are not copyrightable
  - (d) German UrhG §60d (TDM for scientific research) permits text and data mining by research organisations on lawfully accessed content, but does not permit redistributing the extracted corpus. A trained model or a derived *aggregated* statistic can be published, but the raw extracted table cannot. Verify with LMU legal.
- **Cost comparison:** purchasing access (under €3k) is trivial next to generation (€300–1,000 per compound), but it yields data that is largely *already in* the free 1,000–1,500-compound pool. van Gemert is the upstream source of many free compilations. The marginal new unique compounds are therefore probably hundreds, not thousands (inference), and the noise stays at 2–4 orders of magnitude because it comes from the primary literature.
- **Good Scents Company, AIHA (Odor Thresholds for Chemicals with Established Occupational Health Standards), and Devos et al. 1990 (Standardized Human Olfactory Thresholds, IRL Press):** not researched in this session. Devos 1990 is notable because it already applies a *standardisation* (panel-sensitivity correction) to about 500 compounds.

### Gaps
- van Gemert current price and whether a digital or licensable version exists: not found, and the order domain appears defunct.
- VCF: whether the licence permits TDM or ML, and whether threshold fields are included in the online version, was not verified.
- Flavor-Base 10 price not extracted.
- Good Scents permission policy, AIHA price, and Devos 1990 availability: not researched.

---

## 8. Partnerships and consortium models

### Takeaway
The most practical partner is Leibniz-LSB@TUM (Freising; Steinhaus group). It holds the odorant and receptor databases and has in-house GC-O/AEDA and OR-assay capabilities. The ask should be a data-sharing or collaboration agreement with co-authorship, not a purchase. Open-consortium precedents (DREAM Olfaction challenge built on Keller & Vosshall; Zenodo-released Sci Data sets) show that releasing new data openly in exchange for community models is accepted practice.

### Cited Findings
- Leibniz-LSB@TUM lists its databases (Odorant DB, Receptor DB) under Technology Facilities, and the database authors present it at ACS as a tool for flavour scientists — [Leibniz-LSB databases](https://www.leibniz-lsb.de/en/research/technology-facilities/databases); [FIS activity entry](https://portal.fis.leibniz-lsb.tum.de/en/activities/the-leibniz-lsbtum-odorant-database-a-valuable-tool-for-flavor-sc/)
- The DREAM Olfaction Prediction Challenge used the Keller & Vosshall 480-molecule set and showed crowd-sourced model development on released perceptual data — [Science 2017](https://www.science.org/doi/10.1126/science.aal2014)
- Recent olfaction ML preprints (GraphNOSE graph transformer; a reliability-aware audit of molecular representations for human olfaction) emphasise out-of-distribution generalisation, data efficiency, and label reliability, which are arguments for new *clean* data rather than more aggregated noisy data — [GraphNOSE arXiv 2609.05694](https://arxiv.org/pdf/2609.05694); [Reliability-aware audit arXiv 2607.24848](https://arxiv.org/pdf/2607.24848)

### Inferences
- Approach Leibniz-LSB with a concrete proposal: (1) a harmonised re-measurement of about 100–200 anchor compounds under one protocol, run jointly, to calibrate the inter-study offsets in their database (a latent "lab/method effect" model); (2) a formal data-use agreement for their v1.2 threshold table for model training, with a no-redistribution clause if needed.
- Fraunhofer IVV (Freising) has sensory-analytics groups and is a paid-contract rather than free-collaboration model. Not researched here.
- Monell and Osmo hold large proprietary perceptual datasets. Osmo's data is commercial and unlikely to be licensable for independent academic ML. Not researched.

### Gaps
- Contact persons and sensory service offerings at Fraunhofer IVV, Monell, and Osmo were not researched in this session.

---

## 9. Active learning / experimental design: how many new measurements matter?

### Takeaway
There is no olfaction-specific active-learning threshold study, but analogous physicochemical QSAR work shows that one round of targeted acquisition cut RMSE by up to about 0.3 log units. With a 2–4-log noise floor in the literature data, a few hundred *consistently measured, diversity- and uncertainty-selected* compounds is plausibly worth more than doubling the aggregated literature set.

### Cited Findings
- Active learning for LC/HRMS ionisation-efficiency prediction (a log-scale chemical property, structurally analogous to log ODT): a single active-learning iteration dropped RMSE by up to 0.3 log units — [PMC12224155](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12224155/)
- In enzyme-function prediction, active learning reached near-maximum performance with substantially less data (48% reduction) — [arXiv 2602.23269](https://arxiv.org/pdf/2602.23269)
- General ML-QSAR reviews discuss applicability domain, data curation, and noise as primary limits — [JCIM 2023](https://pubs.acs.org/doi/10.1021/acs.jcim.2c01422); [iScience 2021 / PMC8441174](https://pmc.ncbi.nlm.nih.gov/articles/PMC8441174/)

### Inferences
- Recommended design, which is inference:
  - **Batch 0 (about 50–100 anchors):** re-measure well-known compounds spanning 6+ log units to fit a lab-offset or measurement-model correction to the literature data.
  - **Batches 1…n (about 50 each):** select by model uncertainty × chemical-space diversity (for example BADGE/core-set on learned embeddings), excluding compounds with purity risk.
- At about 5 compounds/week in-house (ESTIMATE), 300 new compounds takes about 1–1.5 years and costs about €100k–200k all-in including staff (ESTIMATE). A contract-olfactometry route runs €150k–350k for the same count (ESTIMATE, depending on the unknown per-sample price).
- Expect diminishing returns if the model's error is dominated by label noise in the literature training set. Quantify with learning curves on the existing set before committing to generation.

### Gaps
- No published learning-curve or active-learning study was found specifically for odour thresholds or intensity.
