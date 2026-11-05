# Open aggregator platforms and food/flavor/fragrance databases with odor-potency fields (status: 25 Sep 2026)

Method note: every URL's live status was checked by HTTP request on 2026-09-25 (curl, following redirects). "200" means it answered, "403" means it refused automated requests (the site may still work in a browser), and "000" means no response or timeout. Where a count below comes from my own tally of a downloaded file, the text says so. Other counts are quoted from the cited page. Uncertain figures are marked **(uncertain)**.

---

## 1. Pyrfume / pyrfume-data: which archived datasets relate to potency?

### Takeaway
Pyrfume-data (MIT-licensed repository, 55 dataset folders) has only a few truly potency-relevant sets:
- **abraham_2012**: 268 CID-indexed log(1/ODT) values.
- **keller_2016**: 480 molecules with intensity ratings at 2 concentrations.
- **wakayama_2019**: 314 supra-threshold dose-response curves.
- **mayhew_2022**: 1,924 molecules labelled odorous or odorless.
- **ma_2021**: intensity of 72 key food odorants and 222 binary mixtures.
- Smaller sets: keller_2012 (3 thresholds × 391 subjects), arshamian_2022 (intensity ranks of 10 odorants) and snitz_2019 (intensity).
- Sparse categorical "strength" fields hidden in the raw GoodScents dump (739 records) and in OlfactionBase (19 molecules).

The MIT licence covers the repository. The data licences vary per dataset, and several say "Pyrfume developers make no claims concerning copyright."

### Cited Findings
**Platform facts**
- pyrfume.org is online (HTTP 200). It describes Pyrfume as making "odorant-linked datasets" FAIR. Its components are the `pyrfume` Python package, `pyrfume-data` ("Curated and standardized datasets for research and model benchmarking"), `Rfume` (R) and `pyRESTfume` (REST API). — [pyrfume.org](https://pyrfume.org/)
- The pyrfume-data repository licence is MIT ("Copyright (c) 2020 The Pyrfume Project"). The last push/commit was 2025-09-25 ("Merge pull request #203 from CastroLab/aromadb"), so there were no commits in the 12 months before this check. — [GitHub API: pyrfume/pyrfume-data](https://github.com/pyrfume/pyrfume-data); [LICENSE](https://github.com/pyrfume/pyrfume-data/blob/main/LICENSE)
- Data loads with `pyrfume.load_data('<dataset>/<file>.csv')`. Each folder has a `manifest.toml` listing source DOI, tags, raw/processed files and, sometimes, a LICENSE note. — [pyrfume-data README](https://github.com/pyrfume/pyrfume-data)
- The top-level folders (my count) are 55 dataset/utility folders: abraham_2012, ahmed_2018, arctander_1960, aromadb, arshamian_2022, bolding_2018, burton_2022, bushdid_2014, chae_2019, dravnieks_1985, flavordb, flavornet, foodb, foodcomex, fragrancedb, freesolve, goodscents, gras, haddad_2008, ifra_2019, iurilli_2017, jones_2019, keller_2012, keller_2016, knapsack, leffingwell, leon, ma_2012, ma_2021, mainland_2015, manoel_2021, mayhew_2022, nagappan_2021, nakayama_2022, nat_geo_1986, nhanes_2014, optical_rotation, prediction_targets, prestwick, qian_2022, ravia_2020, scott_2014, sharma_2021a, sharma_2021b, sigma_2014, sisson_2024, slone_2017, snitz_2013, snitz_2019, soh_2013, superscent, t3db, wakayama_2019, weiss_2012, yu_2015. There are also feature folders: embedding, molecules, mordred, morgan, tools. — [GitHub API contents](https://github.com/pyrfume/pyrfume-data)

**Potency-relevant datasets in pyrfume-data (manifests read and files tallied by me)**
- **abraham_2012** (tags `human;threshold;academic`)
  - Source: "An Algorithm for 353 Odor Detection Thresholds in Humans", Chem Senses, doi 10.1093/chemse/bjr094.
  - `behavior.csv` = "Compiled odor thresholds and threshold algorithm parameters, indexed by CID". It has **268 rows** with columns `Log (1/ODT)` plus Abraham solvation descriptors (E, S, A, B, L, V…). Pyrfume ships `benchmarks.csv` for "modeling Log(1/ODT)".
  - `prediction_targets/abraham_2012.csv` = "CID, Log(1/ODT) threshold".
  - No licence line in the manifest. — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/abraham_2012/manifest.toml); [behavior.csv](https://github.com/pyrfume/pyrfume-data/blob/main/abraham_2012/behavior.csv)
  - From the source paper: 193 ODTs by Nagata (Japanese triangular bag method), put on one scale with data from Cometto-Muñiz & Cain, Cometto-Muñiz & Abraham and Hellman & Small, for **353 ODTs** in total (R² = 0.759, SD 0.819 log units). Nagata's own self-consistency is about 0.66 log units. — [Europe PMC abstract, PMC3278675](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1093/chemse/bjr094%22)
  - The paper is free on PMC, but Europe PMC flags it as not open access (no CC licence). — [Europe PMC](https://europepmc.org/article/PMC/PMC3278675)
- **keller_2016** (tags `human;intensity;pleasantness;familiarity;odorCharacter;academic`)
  - Raw xlsx = "Raw ratings for all odorants, subjects, descriptors, and replicates". `behavior.csv` is 68 MB and `molecules.csv` has 480 molecules. There is also `prediction_targets/keller_2016.csv` (CID, Descriptor, Ave Rating). — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/keller_2016/manifest.toml)
  - Study design: 480 molecules at two concentrations, 55 subjects, rating perceived **intensity**, pleasantness, familiarity and 20 descriptors. The paper (BMC Neurosci) is **CC BY**. — [Europe PMC PMC4977894](https://europepmc.org/article/PMC/PMC4977894)
- **wakayama_2019** (tags `human;intensity`)
  - Source: "Method for Predicting Odor Intensity of Perfumery Raw Materials Using Dose–Response Curve Database" (Ind. Eng. Chem. Res. 2019, doi 10.1021/acs.iecr.9b01225).
  - `behavior.csv` = "Supratheshold intensity curve parameters", with columns `I_max, C, D` for **314 rows**. Data were "scraped from supplemental pdf". There are benchmarks for I_max, C and D. No licence stated. — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/wakayama_2019/manifest.toml); [Crossref record](https://api.crossref.org/works/10.1021/acs.iecr.9b01225)
- **mayhew_2022** ("Drawing the Borders of Olfactory Space", PNAS)
  - `behavior_1.csv` has **1,924 molecules**: 1,615 "Odor" and 309 "Odorless".
  - Label sources: PubChem 1,156; van Gemert 2011 387; lab-tested 128; Abraham 2012 126; Wikipedia 17; blank 107. It includes boiling points and transport-model odor probabilities.
  - Manifest says "Copyright 2021 Emily Mayhew, Rick Gerkin, Brian Lee, Joel Mainland". — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/mayhew_2022/manifest.toml)
  - The PNAS article is **CC BY-NC-ND**. — [Europe PMC PMC9169660](https://europepmc.org/article/PMC/PMC9169660)
- **keller_2012** (tags include `threshold;intensity`)
  - `behavior_1.csv` = "Detection thresholds for 3 odorants": 1,173 rows, i.e. 391 subjects × T1–T3. This is individual-variation data, not a structure-potency set.
  - Benchmarks exist "for predicting odor intensity (target 1), and pleasantness (target 2)". — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/keller_2012/manifest.toml)
- **ma_2021** (tags `human;intensity;pleasantness;mixtures`)
  - 222 binary mixtures of **72 key food odorants** (molecules.csv has 72 rows), rated by 30 trained assessors for intensity and pleasantness. — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/ma_2021/manifest.toml)
  - The data include the single-component intensities (IA, IB), the mixture intensity and the in-mixture component intensities. The Data in Brief article is CC BY. — [Europe PMC PMC8144660](https://europepmc.org/article/PMC/PMC8144660)
  - The underlying dataset (doi 10.15454/51OVY6, released 2021-05-05) is under the **Etalab 2.0** open licence. — [Recherche Data Gouv API](https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi:10.15454/51OVY6)
- **arshamian_2022**: `behavior_2.csv` = "All intensity data. Rank 1 is most intenst odor (by CID), Rank 10 is the least intense". That is 125 participant rows ranking 10 odorants. — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/arshamian_2022/manifest.toml)
  - Europe PMC lists the Current Biology paper with license "cc by", but its open-access flag reads "N" (inconsistent metadata). — [Europe PMC PMC11672226](https://europepmc.org/article/PMC/PMC11672226)
- **snitz_2019** (SmellSpace; tags `human;intensity;odorCharacter`): descriptor ratings from participants. Manifest licence: "Creative Commons Attribution Non-Commercial License (CC BY-NC 4.0)… For commercial re-use, please contact [contact omitted]". — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/snitz_2019/manifest.toml)
- **sharma_2021b** (OlfactionBase scrape)
  - `behavior_1.csv` = "Odor descriptors and strength for each molecule (odorants and odorless chemicals)", plus `odorless.csv`.
  - My tally: 54,237 rows across 5,090 unique stimuli. Only **344 rows (19 unique molecules)** have a non-empty `Strength` (high 230, medium 108, very high 3, low 3).
  - Manifest LICENSE = "2022 Copyright OlfactionBase. All Rights Reserved." — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/sharma_2021b/manifest.toml)
- **goodscents** (web scrape of The Good Scents Company, 17 Jan 2022, by Contrebande Labs)
  - The processed `behavior.csv` has descriptors only (4,626 rows). `stimuli.csv` maps to "Concentration %, Solvent".
  - The raw `data_rw_odor.csv` (6,161 records) has potency-type columns (my tally):
    - `Strength`: 739 filled (medium 378, high 342, very high 12, low 7)
    - `Recommended Max Concentration %`: 739
    - `Substantivity (Hours)`: 1,305
    - `Concentration %`: 5,013
  - The manifest says "see LICENSE for use restrictions; Pyrfume developers make no claims concerning copyright". **No LICENSE file is present in the folder** (per the GitHub API listing). — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/goodscents/manifest.toml); [README](https://github.com/pyrfume/pyrfume-data/blob/main/goodscents/README.md)

**Descriptor-only or non-potency aggregations mirrored in pyrfume (useful for joins, no potency)**
- **flavordb**: 25,595 rows with "Odor Percepts, Odor Modifiers" (e.g. "slight"). LICENSE = CC BY-NC-SA 3.0 Unported. — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/flavordb/manifest.toml)
- **flavornet**: 716 rows of descriptors, "© Datu Inc., 2004". — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/flavornet/manifest.toml)
- **aromadb**: 869 rows, "Pyrfume developers make no claims concerning copyright". — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/aromadb/manifest.toml)
- **superscent**: 1,589 CIDs, molecules only. — [folder](https://github.com/pyrfume/pyrfume-data/tree/main/superscent)
- **leffingwell**: 3,523 molecules. The README PDF says "freely available for research use under the CC-BY-NC license". — [leffingwell_readme.pdf](https://github.com/pyrfume/pyrfume-data/blob/main/leffingwell/leffingwell_readme.pdf)
- **arctander_1960**: LICENSE = CC BY-NC 4.0. — [LICENSE](https://github.com/pyrfume/pyrfume-data/blob/main/arctander_1960/LICENSE)
- **foodb**: physicochemical properties only. My tally found no odor, flavor or threshold columns in `properties.csv` (70,926 rows). Manifest licence: "Use and re-distribution … for commercial purposes requires explicit permission". — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/foodb/manifest.toml)
- **Receptor-level "thresholds"**:
  - mainland_2015: "Computed activation thresholds" for human ORs in vitro. — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/mainland_2015/manifest.toml)
  - jones_2019: tagged `threshold`, rodent receptor data. — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/jones_2019/manifest.toml)
- **Leibniz-LSB@TUM Odorant Database**: requested for inclusion in pyrfume in issue #50 (opened 2020-12-01). The issue is **still open** and the data is not archived. — [pyrfume-data issue #50](https://github.com/pyrfume/pyrfume-data/issues/50)

### Inferences
- The only pyrfume sets that give a continuous, cross-molecule, **perceptual** potency target are:
  - abraham_2012: about 268 ODTs, air, log scale.
  - wakayama_2019: 314 dose-response curves, Kao perfumery materials.
  - keller_2016: intensity at 2 fixed dilutions for 480 molecules. This is a psychophysical proxy, not an absolute threshold.
- mayhew_2022 is the best open binary "odorous vs odorless" set. It could serve as a potency-zero class or a pre-filter.
- GoodScents "Strength" (4 ordinal levels, 739 records) and "Recommended Max Concentration %" are weak but large perfumery potency proxies. Their copyright status is the problem (see §6).

### Gaps
- I could not confirm why pyrfume's abraham_2012 has 268 CID rows rather than 353. Likely causes are CID mapping or de-duplication **(uncertain)**.
- Castro et al. 2022 (the Pyrfume paper) was not fetched. The repo was used as the primary source.
- nat_geo_1986 (National Geographic Smell Survey, 6 odorants) likely includes intensity ratings, but this was not verified. Its data files in the repo are only 127-byte stubs, and the data sit on Kaggle (jmainland).
- qian_2022 has an empty manifest (14 bytes), so its content is unknown.

---

## 2. OpenPOM / Principal Odor Map (Lee et al. 2023) GoodScents+Leffingwell dataset: any potency information? Licence?

### Takeaway
The curated GS-LF file (`curated_GS_LF_merged_4983.csv`) has **4,983 molecules × 138 binary odor labels**. Its only potency-adjacent field is an "odorless" label. It has no thresholds, intensity or strength. The OpenPOM code is MIT. The underlying data inherit Leffingwell's **CC-BY-NC (research use)** terms and GoodScents' "all rights reserved" copyright, so it is **not cleanly usable commercially**.

### Cited Findings
- OpenPOM (BioMachineLearning/openpom, fork of ARY2260/openpom) replicates the POM paper in DeepChem. Its benchmark is MPNNPOMModel on `curated_GS_LF_merged_4983.csv`, ROC-AUC 0.8872 (5-fold CV, 10-model ensembles). — [OpenPOM README](https://github.com/BioMachineLearning/openpom)
- Repo licence is **MIT**. Last push was 2025-10-17 for both the BioMachineLearning and ARY2260 repos. — [GitHub API](https://github.com/BioMachineLearning/openpom)
- Data files are `curated_GS_LF_merged_4983.csv` (1.65 MB), `curated_goodcents.csv` and `curated_leffingwell.csv`, with curation notebooks. — [repo tree](https://github.com/BioMachineLearning/openpom/tree/main/openpom/data/curated_datasets)
- My inspection of `curated_GS_LF_merged_4983.csv`:
  - 4,983 rows and 140 columns: `nonStereoSMILES`, `descriptors` and 138 label columns.
  - The only column matching threshold/strength/intensity/odorless/concentration keywords is **`odorless`**. — [CSV](https://github.com/BioMachineLearning/openpom/blob/main/openpom/data/curated_datasets/curated_GS_LF_merged_4983.csv)
- The GraphNOSE paper (arXiv, Sept 2026) confirms GS-LF has 4,983 molecules with up to 138 descriptors and a highly imbalanced label distribution. It states it uses **no** threshold, intensity or strength datasets. — [arXiv 2609.05694](https://arxiv.org/html/2609.05694)
- The same data are mirrored on Kaggle as "Multi-Labelled SMILES Odors dataset". — [Kaggle](https://www.kaggle.com/datasets/aryanamitbarsainyan/multi-labelled-smiles-odors-dataset)
- Leffingwell source data:
  - "The dataset, and all associated features, is freely available for research use under the CC-BY-NC license" (3,523 molecules from Leffingwell PMP 2001). — [leffingwell_readme.pdf](https://github.com/pyrfume/pyrfume-data/blob/main/leffingwell/leffingwell_readme.pdf)
  - The Zenodo record 4085098 is "restricted" access. — [Zenodo 4085098](https://zenodo.org/records/4085098)
  - The commercial PMP 2001 product costs "U.S. $2775.00" for a non-exclusive two-workstation licence. — [Leffingwell PMP 2001](http://www.leffingwell.com/bacispmp.htm)
- GoodScents source data: "The Good Scents Company retains all exclusive copyrights… Permission to reproduce is required." — [TGSC copyright page](https://www.thegoodscentscompany.com/misc/copyright.html)
- Lee et al. 2023 (Science, doi 10.1126/science.ade4401) is not open access. Europe PMC lists an author manuscript, PMC11898014. — [Europe PMC](https://europepmc.org/article/PMC/PMC11898014)

### Inferences
- For potency modelling, GS-LF is useful only for (a) the odorless label and (b) pretraining or representation learning with a quality-map embedding. The potency head needs other data.
- GoodScents web pages themselves do show "Odor Strength" and substantivity (see §3). A commercial user would have to license or re-derive them rather than scrape them.

### Gaps
- I did not verify the exact data-availability wording in the Science paper's supplementary materials.

---

## 3. General flavor/fragrance/food chemistry databases: potency fields, size, access, licence, status

### Takeaway
Among the free web databases, **none offers bulk-downloadable, numeric odor thresholds under a permissive licence**:
- **FlavorDB2** (25,595 molecules) adds a free-text "aroma/taste threshold" field, but it is CC BY-NC-SA.
- **PubChem** has ~819 "Odor Threshold" annotations (511 CIDs, from HSDB and Haz-Map), mostly industrial-hygiene air values.
- **GoodScents** pages show ordinal "Odor Strength" but are fully copyrighted.
- **VCF** holds the largest threshold compilation (~5,890 compounds, ~26,490 values) but is subscription-only.
- **Flavornet** (738 GC-O odorants) implies odor-activity but has no numeric potency.
- **OlfactionBase** (3,985 odorants + 1,124 odorless) supplies odorous/odorless labels.
- Several named resources are dead or could not be found: SuperScent, ScentBase, OdorDB, "OlfactomeDB".

### Cited Findings

**FlavorDB / FlavorDB2 (IIIT-Delhi, Bagler lab)**
- Live (HTTP 200). "FlavorDB comprises of 25595 flavor molecules… Among these 2254 molecules are associated with 936 natural ingredients belonging to 34 categories." — [FlavorDB2 home](https://cosylab.iiitd.edu.in/flavordb2/)
- The site footer links to **CC BY-NC-SA 3.0**. — [FlavorDB2 home (license link)](https://cosylab.iiitd.edu.in/flavordb2/)
- The original NAR 2018 paper is CC BY-NC. — [Europe PMC PMC5753196](https://europepmc.org/article/PMC/PMC5753196)
- FlavorDB2 paper: Goel et al., J Food Sci 2024, 89:7076–7082; arXiv 2205.05451.
  - It adds "(iv) taste/aroma threshold values". Example: allyl hexanoate reads "'Taste attributes at 10 ppm; sweet, juicy, fresh, pineapple, and fruity'". So this is free text, not a numeric ODT.
  - Sources are "FooDB, Flavornet, SuperSweet, BitterDB, and Fenaroli's Handbook". Compound and ingredient counts are unchanged from FlavorDB. — [arXiv 2205.05451 PDF](https://arxiv.org/pdf/2205.05451); [Wiley record](https://ift.onlinelibrary.wiley.com/doi/10.1111/1750-3841.17298)
- A JSON endpoint works: `…/flavordb2/molecules_json?id=<PubChem CID>`.
  - For vanillin (CID 1183) it returns SMILES, CAS, FEMA number, `fema_flavor_profile`, `odor`, `taste`, `fooddb_flavor_profile`, `flavornet_id`, `fenoroli_and_os`, `natural` and physicochemical fields.
  - It returned **no threshold key** for vanillin. — [molecules_json?id=1183](https://cosylab.iiitd.edu.in/flavordb2/molecules_json?id=1183)

**FooDB (Wishart lab, U Alberta)**
- foodb.ca returned **HTTP 403** to automated requests (curl and WebFetch) on 2026-09-25. Its online status for browsers could not be verified here.
- Licence: "All data and metadata in FooDB are released under… CC Attribution-NonCommercial 4.0". "Use and re-distribution … for commercial purposes requires explicit permission." — [search summary of foodb.ca/about](https://foodb.ca/about); [pyrfume foodb manifest](https://github.com/pyrfume/pyrfume-data/blob/main/foodb/manifest.toml)
- The search-indexed "about" text says FooDB covers "~28,000 food components". A 2025 MethodsX paper reports the downloaded files held 9,461 food items and 10,898 compounds with quantitative `orig_content` values **(sizes inconsistent across sources; uncertain)**. — [MethodsX 2025 "Cleaning and using FooDB"](https://www.sciencedirect.com/science/article/pii/S2215016125005357)
- FooDB provides **food concentrations** (orig_content) and flavor descriptors. No odor-threshold field was found. The pyrfume scrape of FooDB properties has no odor/flavor/threshold columns (my tally). — [pyrfume foodb](https://github.com/pyrfume/pyrfume-data/tree/main/foodb)

**Flavornet (Acree & Arn, Cornell / DATU Inc.)**
- Online (HTTP 200), but static: "There are 738 odorants listed as of 6.25.04".
- Inclusion criterion: "detected in a natural product or real environment by some form of quantitative GCO method e.g. dilution analysis". It lists only "odorants… found in a human odor space at supra-threshold levels".
- Data: retention indices (Kovats and ethyl-ester) on 4 phases, descriptors and links. — [flavornet.org](https://www.flavornet.org/)
- There are no per-compound FD factors or thresholds in the pyrfume scrape (descriptors only). Rights: "© Datu Inc., 2004". — [pyrfume flavornet manifest](https://github.com/pyrfume/pyrfume-data/blob/main/flavornet/manifest.toml)

**SuperScent (Charité Berlin; Dunkel et al., NAR 2009)**
- About 2,100 volatiles and ~9,200 synonyms, with 2D/3D structures, physicochemical properties, commercial availability and references. — [NAR 2009](https://academic.oup.com/nar/article/37/suppl_1/D291/1005806)
- Status: bioinformatics.charite.de/superscent now only redirects to bioinf-applied.charite.de/superscent, which **did not respond** (HTTP 000, 45 s timeout), so it is effectively **offline**. — [redirect page](https://bioinformatics.charite.de/superscent/)
- Pyrfume keeps 1,589 SuperScent CIDs (structures only). — [pyrfume superscent](https://github.com/pyrfume/pyrfume-data/tree/main/superscent)

**AromaDb (CSIR-CIMAP, Lucknow; Kumar et al., Front Plant Sci 2018)**
- 1,321 aroma chemical structures, 357 fragrance types, 166 plants and 148 varieties/chemotypes, plus essential-oil GC-MS profiles and bioactivity. — [Frontiers 2018](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2018.01081/full)
- The old URLs fail: bioinfo.cimap.res.in/aromadb gave 403/timeout and aromadb.cimap.res.in gave 000. A **new domain, aromadb.cimapbioinfo.in, is live (HTTP 200)**. — [aromadb.cimapbioinfo.in](https://aromadb.cimapbioinfo.in/)
- No potency fields. Pyrfume's scrape is 869 descriptor rows. — [pyrfume aromadb](https://github.com/pyrfume/pyrfume-data/tree/main/aromadb)

**OlfactionBase (IIIT-Allahabad; Sharma et al., NAR 2022)**
- 3,985 odorants, **1,124 odorless compounds**, 106 primary odors, 572 sub-odors, 2,067 ORs and 874 OR-odorant interactions. The NAR article is CC BY. — [NAR 2022](https://academic.oup.com/nar/article/50/D1/D678/6362078); [Europe PMC PMC8728123](https://europepmc.org/article/PMC/PMC8728123)
- The article describes no odor thresholds or intensity. — [NAR 2022](https://academic.oup.com/nar/article/50/D1/D678/6362078)
- The site is online at olfactionbase.com (HTTP 200). The older olfab.iiita.ac.in/olfactionbase returned HTTP 500. — [olfactionbase.com](https://olfactionbase.com/)
- Pyrfume's scrape found a sparse "Strength" field (19 molecules) and records the data as "All Rights Reserved". — [pyrfume sharma_2021b](https://github.com/pyrfume/pyrfume-data/blob/main/sharma_2021b/manifest.toml)

**ODORactor (SJTU; Liu et al., Bioinformatics 2011)**
- 3,038 odorants and 1,608 ORs, used for odorant verification and OR prediction. — [Bioinformatics 2011](https://academic.oup.com/bioinformatics/article/27/16/2302/255357)
- The page is still up (HTTP 200) but static ("Copyright © 2009-2011 … All Rights Reserved"). No potency fields. — [ODORactor](https://mdl.shsmu.edu.cn/ODORactor/)

**M2OR (chemosim-lab, Univ. Côte d'Azur; Lalis et al., NAR 2024)**
- Receptor-level potency: 75,050 bioassays for 51,395 OR–molecule pairs. — [NAR 2024](https://academic.oup.com/nar/article/52/D1/D1370/7327067)
- Dose-response rows carry **EC50** in `Value`/`Unit`, with screening concentrations for non-agonists. — [M2OR GitHub README](https://github.com/chemosim-lab/M2OR)
- GitHub is **Apache-2.0** (last push 2024-06-05). The NAR article is CC BY. — [GitHub API](https://github.com/chemosim-lab/M2OR); [Europe PMC PMC10767820](https://europepmc.org/article/PMC/PMC10767820)
- m2or.chemsensim.fr returned HTTP 403 to curl (bot-blocking; browser status unverified). — [m2or.chemsensim.fr](https://m2or.chemsensim.fr/)

**OdoriFy (JBC 2021)**: a curated set of 4,201 compounds (odorant vs non-odorant), split 3,781 train / 420 test. — [ResearchGate record](https://www.researchgate.net/publication/353188333_OdoriFy_A_conglomerate_of_Artificial_Intelligence-driven_prediction_engines_for_olfactory_decoding)

**Odor Pair (Sisson et al., arXiv 2312.16124)**
- More than 160k molecule-pair data points with labels for 109 notes, taken from GoodScents "suggested blends". Code is MIT (repo pushed 2025-10-01). — [odor-pair README](https://github.com/odor-pair/odor-pair)
- Mirrored as pyrfume sisson_2024. No potency. — [pyrfume sisson_2024](https://github.com/pyrfume/pyrfume-data/blob/main/sisson_2024/manifest.toml)

**VCF – Volatile Compounds in Food (BeWiDo BV / formerly TNO; version 16.10)**
- "VCF Online can only be consulted on basis of subscription" (**paywalled**). — [VCF home](https://www.vcf-online.nl/VcfHome.cfm)
- Threshold module (OFTV), compound counts:

  | Code | Threshold type | Compounds |
  |---|---|---|
  | OA | odour, air (mg/m³) | 1,789 |
  | OW | odour, water (mg/L) | 1,881 |
  | OV | odour, other media | 788 |
  | FW | flavour, water | 2,163 |
  | FV | flavour, other media | 1,002 |
  | FP | peptides | 633 |

  — [VCF OFTV](https://www.vcf-online.nl/OFTVCompounds.cfm)
- A search summary of the VCF site gives "over 26,490 threshold values … for 5,890 compounds from 3180 literature references", ~13,300 volatiles and 1,445 food products **(from search snippet; not re-read on page)**. — [VCF](https://www.vcf-online.nl/)
- Copyright "© 1992—2026 BeWiDo BV" (active in 2026). — [VCF OFTV](https://www.vcf-online.nl/OFTVCompounds.cfm)

**van Gemert "Compilations of Odour Threshold Values" (2011, Oliemans Punter & Partners)**
- "About 22,000 threshold values": ~1,790 compounds in air, ~1,860 in water, ~760 in other media, ~2,160 flavour-in-water, ~1,010 flavour-other, ~680 peptides.
- "Available only from Oliemans Punter & Partners" (**paid**). — [Leffingwell page](http://www.leffingwell.com/bacis2.htm)

**Leffingwell & Associates**
- leffingwell.com has HTTPS failures, but http:// works.
- Free web table "Odor Detection Thresholds of GRAS Flavor Chemicals" (copyrighted page). — [Leffingwell odorback](http://www.leffingwell.com/odorback.htm)
- "Flavor-Base 10th Edition" is a **commercial** regulatory/flavor database (GRAS/FEMA to 2016, EC register, JECFA). — [Flavor-Base 10](http://www.leffingwell.com/flavbase.htm)

**ChemFOnt (Wishart lab)**
- Functional ontology covering 341,627 compounds. No odor-potency fields (ontology of functions/actions). — [ChemFOnt stats](https://chemfont.ca/simple/stats)
- Licence **CC BY-NC 4.0** ("derivative works may not be used for commercial purposes"). — [ChemFOnt license](https://chemfont.ca/simple/license)

**PubChem odor annotations (my query of the PUG-View annotations API)**
- Heading "Odor Threshold":
  - **819 annotations**: HSDB 433 and Haz-Map 386, covering **511 unique CIDs**.
  - Values are free-text strings with references (e.g. Ruth 1986 AIHA J; USCG CHRIS; Fenaroli's Handbook), not normalised numbers.
  - Haz-Map entries carry "Copyright (c) 2026 Haz-Map(R). All rights reserved…". HSDB points to NLM web policies. — [PUG-View Odor Threshold](https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/annotations/heading/JSON?heading=Odor%20Threshold&heading_type=Compound&page=1)
- Heading "Odor": about **2,359 annotations** (3 pages: 1,000 + 1,000 + 359), all from HSDB. — [PUG-View Odor](https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/annotations/heading/JSON?heading=Odor&heading_type=Compound&page=1)

**The Good Scents Company (W. Luebke)**
- Pages show "Odor Strength: medium; Substantivity: 251 hour(s) at 10.00 % in dipropylene glycol", odor description at a stated dilution, and FEMA/JECFA data. — [TGSC example page](https://www.thegoodscentscompany.com/data/rw1000111.html)
- "Permission to reproduce is required". — [TGSC copyright](https://www.thegoodscentscompany.com/misc/copyright.html)

**Fragrantica**
- Its terms prohibit "Automated Means, including scraping, crawling, harvesting…" except as expressly permitted in writing. Fragrantica has stated that no information may be used except for private reading in a browser. — [Fragrantica Terms of Service](https://www.fragrantica.com/terms-of-service.phtml)
- The terms page returned HTTP 403 to curl. Fragrantica has perfume-level data only, no molecule potency.

**Not found or dead**
- **OdorDB**: odordb.org does not resolve (HTTP 000). No published "OdorDB" database was found.
- **"OlfactomeDB"**: no such resource found. Search returns **OlfactionDB**, which covers about 400 odorant-receptor interactions. — [OlfactionDB record](https://www.researchgate.net/publication/271102554_OlfactionDB_A_Database_of_Olfactory_Receptors_and_Their_Ligands)
- **ScentBase / SCENTbase** (floral-scent compilation, Univ. Gothenburg): www2.dpes.gu.se/SCENTbase.html gives no response (HTTP 000), so it is **dead**. — [search reference](https://www.perfume.com/article-smell-database)
- **"Aroma Chemical Database"**: no distinct resource by this name was found.
- **SweGen**: no aroma-related resource by this name was found. It appears unrelated.
- **"BitterDB-like aroma analogues"**: none found. BitterDB and SuperSweet are integrated into FlavorDB2 for taste, not odor. — [FlavorDB2 arXiv](https://arxiv.org/pdf/2205.05451)

### Inferences
- For a potency model, the free web databases supply mainly:
  - **Negatives and odor-active flags**: OlfactionBase odorless (1,124), mayhew_2022 odorless (309), Flavornet "supra-threshold in real foods" (738).
  - **Descriptors and identifiers** for joins.
- Numeric ODTs in bulk sit behind VCF or van Gemert paywalls, or in Leibniz-LSB (see §4).
- PubChem/HSDB is the only large-ish free, government-sourced ODT text corpus (~433 HSDB annotations). It is skewed toward industrial chemicals and air ppm, and it needs text parsing and unit harmonisation.

### Gaps
- FooDB could not be accessed directly (403). Its current version, compound count and the exact licence page wording come from search snippets and the pyrfume manifest.
- The number of FlavorDB2 molecules with a filled "aroma/taste threshold" field is unknown. No bulk download or API documentation was found beyond the per-CID JSON endpoint.
- The Flavornet per-compound pages were not examined for any FD/Charm values.

---

## 4. Food sensomics datasets with OAVs / FD factors / thresholds (Dunkel 2014, Leibniz-LSB@TUM, Czerny 2008, etc.)

### Takeaway
The **Leibniz-LSB@TUM Odorant Database** (v1.2, 2022: >1,700 odorants from >700 publications) is the richest free-to-browse source:
- It contains **odor thresholds in several matrices** (Czerny 2008 method), RIs on 3 phases, and the foods where each compound is odor-active.
- It is query-only (max 20 hits per search), and **systematic download or reuse "in similar products" requires written permission**.

Other sources:
- Dunkel et al. 2014 (~230 key food odorants, >220 foods) and Czerny et al. 2008 (84 + 10 re-measured ODTs) are paywalled papers, not open datasets.
- The Nagata 223-compound air-ODT table is freely readable as a Japanese Ministry of Environment PDF.

### Cited Findings
**Leibniz-LSB@TUM Odorant Database**
- Authors: Kreissl J, Mall V, Steinhaus P, Steinhaus M. "The 2022 version 1.2 currently includes data on more than 1700 odorants extracted from more than 700 publications".
- Contents: "retention indices and odor qualities, but also odor threshold values in different matrices and a list of foods and raw materials in which the substances have been detected in odor-active amounts." — [Leibniz-LSB Start](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-odorant-database/start/)
- Structure:
  - A basic table gives name, CAS, odor quality, RI on DB-5/DB-1701/DB-FFAP, MW and structure. Searches return "maximum 20 hits with best fit".
  - Per-substance detail tables give Reference, Year, Food, Odor quality and "Odor threshold … determined according to Eur. Food Res. Technol. 2008, 228, 265". Searching "OT" returns references with threshold values. — [User guide](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-odorant-database/user-guide)
- History: it was used in-house for more than 20 years (DFA, then Leibniz-LSB). "In 2019, we decided to make this data collection available to the scientific community free of charge". — [Preface](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-odorant-database/preface)
- **Terms**: "Copyright © 2019-2025… The use and dissemination of data… for scientific purposes is encouraged provided that full acknowledgement… However, **systematic download** of the… contents, **use… in similar products**, and reproduction of the database or parts thereof in any form… **requires prior written permission**." — [Copyright and Citation](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-odorant-database/copyright-and-citation)
- The disclaimer says there is no warranty of accuracy and the data are "updated on an ongoing basis". — [Disclaimer](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-odorant-database/disclaimer)
- Online status: pages return HTTP 200 (Sept 2026). The version is still labelled 1.2 (2022). — [Leibniz-LSB Start](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-odorant-database/start/)

**Dunkel et al. 2014, Angew Chem Int Ed, doi 10.1002/anie.201309508**
- A meta-analysis: each food has "about 3 to 40 genuine key odorants, from a group of about 230 out of circa 10,000 food volatiles". It covers the chemical odor codes of "more than 220 food samples". — [PubMed 24939725](https://pubmed.ncbi.nlm.nih.gov/24939725/); [TUM press release](https://www.tum.de/en/news-and-events/all-news/press-releases/details/31635)
- Not open access (Europe PMC: isOpenAccess = N, no PMCID). The Wiley page returned HTTP 403, so free availability of the Supporting Information **could not be verified**. — [Europe PMC search](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1002/anie.201309508%22)

**Czerny et al. 2008, Eur Food Res Technol 228:265–273**
- "Re-evaluated the odour thresholds of eighty-four compounds previously characterised as key food odorants", plus 10 odorants reported for the first time. Thresholds were measured in air/water with an aroma-language descriptor set.
- Not open access (Europe PMC: N). — [Springer](https://link.springer.com/article/10.1007/s00217-008-0931-x); [Europe PMC search](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1007/s00217-008-0931-x%22)

**Nagata (1990/2003), triangle odor bag thresholds**
- 223 substances measured 1976–1988. The lowest is isoamyl mercaptan (0.77 ppt) and the highest propane (1,500 ppm).
- The PDF is hosted by the Japanese Ministry of the Environment (HTTP 200, 339 kB). — [env.go.jp PDF](https://www.env.go.jp/en/air/odor/measure/02_3_2.pdf)
- It is the backbone of Abraham 2012. — [Abraham 2012 abstract](https://pubmed.ncbi.nlm.nih.gov/?term=10.1093/chemse/bjr094)

**US EPA 1992, "Reference Guide to Odor Thresholds for Hazardous Air Pollutants Listed in the Clean Air Act Amendments of 1990"** (EPA/600/R-92/047): listed in the EPA Science Inventory and on OSTI. — [EPA Science Inventory](https://cfpub.epa.gov/si/si_public_record_report.cfm?Lab=NCEA&dirEntryId=40610); [OSTI](https://www.osti.gov/biblio/7008820)

**Ma et al. 2021 (INRAE)**: open benchmark with intensity for 72 key food odorants, alone and in 222 binary mixtures. Etalab 2.0 licence (see §1). — [Recherche Data Gouv](https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi:10.15454/51OVY6)

### Inferences
- There is no open, machine-readable KFO × food table with concentrations, thresholds and OAVs, the "sensomics matrix" Dunkel 2014 implies. The Leibniz-LSB DB is the closest, but its terms bar systematic scraping and "similar products". A commercial ML project should ask Leibniz-LSB for a licence.
- OAVs and FD factors remain scattered across individual J Agric Food Chem / Food Chem / EFRT papers. The 2025 Metabolites crop-aroma study built its 716-compound ODT set from PubChem, Flavornet and literature rather than from a sensomics database (§5).

### Gaps
- Whether the Dunkel 2014 SI (KFO tables with thresholds and concentrations) is freely downloadable remains **unverified** (Wiley blocked automated access).
- The number of Leibniz-LSB entries with ≥1 threshold value is not published on the site pages read.
- No open compilation of AEDA FD factors was found.

---

## 5. Newer (2022–2026) open databases/benchmarks on GitHub, Zenodo, Hugging Face, Kaggle that include potency

### Takeaway
Few new open datasets carry potency:
- The notable one is the **Metabolites 2025 ODT set** (716 compounds in the paper; 992 SMILES in the GitHub CSV; CC BY 4.0 on Zenodo), which is water-matrix thresholds.
- Also relevant: the **Sci Data 2025 laymen dataset** (74 odors, 1,227 participants, evaluative ratings plus an intensity pilot, CC BY 4.0) and **M2OR** (receptor EC50, Apache-2.0).

Most HF and Kaggle olfaction sets (GS-LF mirrors, SmellNet sensor data, odor-image sets) have no molecular potency. No "OlfactionBench" was found.

### Cited Findings
- **Yuan et al., Metabolites 2025, 15(11):747, "Predictive Models of Odor Contribution and Thresholds…"** (CC BY):
  - "Odor thresholds for 716 volatile compounds", harmonised to mg/L in a **distilled-water matrix** and modelled as −log10.
  - Sources: PubChem, Flavornet and literature, taking the median when there were several values.
  - Contribution labels are rule-based from descriptors, **not OAV/FD**. — [PMC12654368](https://pmc.ncbi.nlm.nih.gov/articles/PMC12654368/)
  - GitHub `data/threshold_data.csv` has **992 rows** (SMILES, threshold) by my count, which differs from the 716 in the paper **(discrepancy; uncertain)**. The repo has **no LICENSE file**; its README says "Choose a permissive license (MIT/Apache-2.0)". Last push 2025-11-14. — [yuanhonglun/odor_prediction_models](https://github.com/yuanhonglun/odor_prediction_models)
  - Zenodo 17605258 ("Odor Prediction Models", 2025-11-14) is **CC-BY-4.0, open**, with `odor_models_data_v3.zip`. — [Zenodo 17605258](https://zenodo.org/records/17605258)
- **OpenSmell/Smellability** (GitHub, last push 2026-03-27): an ODT regressor trained on Abraham 2012 via Pyrfume, with R² ≈ 0.575. It says it is "not intended for production use". No licence. — [Smellability](https://github.com/OpenSmell/Smellability)
- **Sci Data 2025, "A dataset of laymen olfactory perception for 74 mono-molecular odors"**:
  - 1,227 participants gave free descriptions, evaluative ratings and labels.
  - Zenodo 15657278 (2025-06-13) is **CC-BY-4.0**. Files include `intensity_piloting.csv`, `data.csv` and `odors.csv`. — [Zenodo 15657278](https://zenodo.org/records/15657278); [Europe PMC PMC11865284](https://europepmc.org/article/PMC/PMC11865284)
- **M2OR** (2024): receptor EC50 data, Apache-2.0 (see §3). — [GitHub](https://github.com/chemosim-lab/M2OR)
- **Olfactory Perception (OP) benchmark for LLMs** (arXiv 2604.00002): 1,010 questions in eight task categories, including "intensity and pleasantness judgments". — [arXiv 2604.00002](https://arxiv.org/html/2604.00002)
- **GraphNOSE** (arXiv 2609.05694, Sept 2026): uses only GS-LF and Sisson pairs, with no threshold or intensity data. — [arXiv 2609.05694](https://arxiv.org/html/2609.05694)
- Hugging Face results for olfaction datasets:
  - SmellNet: MOX gas-sensor recordings. — [HF SmellNet](https://huggingface.co/datasets/DeweiFeng/SmellNet)
  - An olfaction-vision-language dataset and odor OVLA robotics demos.
  - None carried molecular ODT/intensity in the search results. — [HF search result](https://huggingface.co/datasets/christina040807/odor_ovla_physical_raw_v3)
- Kaggle: the main olfaction dataset is the OpenPOM GS-LF mirror (no potency). — [Kaggle](https://www.kaggle.com/datasets/aryanamitbarsainyan/multi-labelled-smiles-odors-dataset)
- "OdorGrapher" dataset (Zenodo 18183116) targets multi-label odor prediction, not potency. — [Zenodo 18183116](https://zenodo.org/records/18183116)

### Inferences
- In 2026, the open potency-specific training pool is still roughly:
  - Abraham ~268–353 air ODTs
  - Metabolites 2025 716–992 water ODTs (overlapping sources)
  - Wakayama 314 dose-response curves
  - Keller 2016 intensity for 480 molecules
  - Mayhew 1,924 odorous/odorless labels
  - plus parsed PubChem/HSDB text (~511 CIDs)
- Merging these requires matrix separation (air vs water), unit harmonisation and de-duplication. Several share Nagata or van Gemert as the upstream source.

### Gaps
- No "OlfactionBench", TDC olfaction task or Hugging Face dataset with ODT/OAV was found. I cannot rule out small unindexed repos.
- The upstream licences of the 716/992-compound ODT set's sources (e.g. PubChem/Haz-Map or copyrighted literature tables) are not documented.
- arXiv 2607.24848 ("reliability-aware audit of molecular representations for human olfaction") was not read. It may list threshold datasets.

---

## 6. Which resources can legally train a (potentially commercial) ML model?

### Takeaway
Only a small set is **clearly permissive for commercial training**:
- Keller 2016 (CC BY)
- Ma 2021 (Etalab 2.0)
- The Sci Data 2025 laymen set (CC BY 4.0)
- The Metabolites 2025 Zenodo ODT data (CC BY 4.0, but with upstream-source caveats)
- M2OR (Apache-2.0)
- Probably US-government sources: HSDB via PubChem and EPA 1992

Explicitly **non-commercial**: Leffingwell/GS-LF (CC-BY-NC), FlavorDB (CC BY-NC-SA 3.0), FooDB (commercial use needs permission), ChemFOnt (CC BY-NC 4.0), Arctander (CC BY-NC 4.0), SmellSpace (CC BY-NC 4.0), and the Mayhew PNAS article (CC BY-NC-ND).

**All-rights-reserved or permission required**: GoodScents, OlfactionBase data, Flavornet, Leibniz-LSB (systematic download), Haz-Map, Fragrantica (scraping prohibited), VCF and van Gemert (paid).

### Cited Findings
- **Permissive**
  - Keller 2016: CC BY. — [Europe PMC](https://europepmc.org/article/PMC/PMC4977894)
  - Ma 2021 dataset: Etalab 2.0. — [Recherche Data Gouv](https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi:10.15454/51OVY6)
  - Laymen 74-odor dataset: CC-BY-4.0. — [Zenodo 15657278](https://zenodo.org/records/15657278)
  - Metabolites 2025 models and data: CC-BY-4.0. — [Zenodo 17605258](https://zenodo.org/records/17605258)
  - M2OR code/data repo: Apache-2.0. — [GitHub](https://github.com/chemosim-lab/M2OR)
  - pyrfume-data repo: MIT. — [LICENSE](https://github.com/pyrfume/pyrfume-data/blob/main/LICENSE)
  - OpenPOM code: MIT. — [GitHub](https://github.com/BioMachineLearning/openpom)
- **Non-commercial**
  - Leffingwell dataset: "freely available for research use under the CC-BY-NC license". — [pyrfume leffingwell README](https://github.com/pyrfume/pyrfume-data/blob/main/leffingwell/leffingwell_readme.pdf)
  - FlavorDB: CC BY-NC-SA 3.0. — [pyrfume flavordb manifest](https://github.com/pyrfume/pyrfume-data/blob/main/flavordb/manifest.toml)
  - FooDB: "commercial purposes requires explicit permission". — [pyrfume foodb manifest](https://github.com/pyrfume/pyrfume-data/blob/main/foodb/manifest.toml)
  - ChemFOnt: CC BY-NC 4.0. — [ChemFOnt license](https://chemfont.ca/simple/license)
  - Arctander: CC BY-NC 4.0. — [LICENSE](https://github.com/pyrfume/pyrfume-data/blob/main/arctander_1960/LICENSE)
  - SmellSpace: CC BY-NC 4.0. — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/snitz_2019/manifest.toml)
  - Mayhew 2022 article: CC BY-NC-ND. — [Europe PMC](https://europepmc.org/article/PMC/PMC9169660)
- **Restricted**
  - GoodScents: "Permission to reproduce is required". — [TGSC](https://www.thegoodscentscompany.com/misc/copyright.html)
  - OlfactionBase: "All Rights Reserved". — [pyrfume manifest](https://github.com/pyrfume/pyrfume-data/blob/main/sharma_2021b/manifest.toml)
  - Leibniz-LSB: systematic download or use in similar products needs written permission. — [Copyright](https://www.leibniz-lsb.de/en/databases/leibniz-lsbtum-odorant-database/copyright-and-citation)
  - Fragrantica: automated access prohibited. — [ToS](https://www.fragrantica.com/terms-of-service.phtml)
  - Haz-Map (in PubChem): "All rights reserved". — [PubChem PUG-View](https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/annotations/heading/JSON?heading=Odor%20Threshold&heading_type=Compound&page=1)
  - VCF: subscription. — [VCF](https://www.vcf-online.nl/VcfHome.cfm)
  - van Gemert: sold only by Oliemans Punter. — [Leffingwell page](http://www.leffingwell.com/bacis2.htm)
  - Flavornet: "© Datu Inc., 2004". — [pyrfume manifest](https://github.com/pyrfume/pyrfume-data/blob/main/flavornet/manifest.toml)
- **Unclear**
  - Abraham 2012: free on PMC but no OA licence. — [Europe PMC](https://europepmc.org/article/PMC/PMC3278675)
  - Wakayama 2019: ACS supplementary data, no licence stated in pyrfume. — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/wakayama_2019/manifest.toml)
  - Pyrfume's AromaDb, GoodScents, OlfactionBase and SmellSpace manifests say "Pyrfume developers make no claims concerning copyright". — [aromadb manifest](https://github.com/pyrfume/pyrfume-data/blob/main/aromadb/manifest.toml)

### Summary catalogue (potency focus)

| Resource | Maintainer | Status Sep 2026 | Molecules | Potency field (n) | Access | Licence / commercial ML |
|---|---|---|---|---|---|---|
| pyrfume abraham_2012 | Pyrfume / Abraham et al. | GitHub live | 268 rows (353 in paper) | log(1/ODT), air (268) | CSV via pyrfume | Unclear (paper not CC) |
| pyrfume wakayama_2019 | Pyrfume / Kao (Wakayama) | live | 314 | Dose-response I_max, C, D (314) | CSV | Unclear (ACS SI) |
| pyrfume keller_2016 | Pyrfume / Rockefeller | live | 480 | Intensity at 2 concentrations, 55 subjects | CSV/XLSX | CC BY: yes |
| pyrfume mayhew_2022 | Pyrfume / Monell | live | 1,924 | Odorous/odorless (1,615/309) | CSV | Article CC BY-NC-ND: non-commercial |
| pyrfume ma_2021 | INRAE | live | 72 (+222 mixtures) | Intensity | XLSX/CSV | Etalab 2.0: yes |
| pyrfume goodscents (raw) | Contrebande Labs scrape of TGSC | live | ~4,600 CIDs / 6,161 records | Strength ordinal (739), max-use % (739), substantivity (1,305) | CSV | TGSC © all rights: no |
| OpenPOM GS-LF | OpenPOM | live | 4,983 | "odorless" label only | CSV | Code MIT; data NC/©: no |
| OlfactionBase | IIIT-Allahabad | olfactionbase.com live | 3,985 + 1,124 odorless | Odorless flag; Strength (19) | Web, xlsx per odor | "All Rights Reserved": no |
| FlavorDB2 | IIIT-Delhi | live | 25,595 | Free-text aroma/taste threshold (n unknown) | Web, JSON per CID | CC BY-NC-SA 3.0: no |
| FooDB | U Alberta | 403 to bots | ~28k (uncertain) | None; food concentrations yes | Downloads page | CC BY-NC 4.0; commercial needs permission |
| Flavornet | Acree/Arn, DATU | live, frozen 2004 | 738 | GC-O odor-active flag | Web | © Datu: no |
| PubChem "Odor Threshold" | NLM (HSDB) + Haz-Map | live | 511 CIDs | 819 text annotations | PUG-View API | HSDB NLM policy (likely OK); Haz-Map ©: no |
| Leibniz-LSB@TUM Odorant DB | Leibniz-LSB | live, v1.2 (2022) | >1,700 | ODTs in several matrices (count unknown) | Web query only | Science use OK; bulk/"similar products" need permission |
| VCF 16.10 | BeWiDo BV | live, paid | 13,300 volatiles | Thresholds for ~5,890 compounds (~26,490 values) | Subscription | Paid |
| van Gemert 2011 | Oliemans Punter | book, paid | ~1,790 air / ~1,860 water | ~22,000 values | Purchase | Paid |
| M2OR | chemosim-lab | GitHub live; site 403 to bots | 51,395 pairs | OR EC50 | CSV (GitHub) | Apache-2.0 / CC BY: yes |
| Metabolites 2025 ODT | Yuan et al. | GitHub/Zenodo live | 716 (paper) / 992 (CSV) | ODT water mg/L | CSV, Zenodo zip | Zenodo CC BY 4.0 (upstream unclear) |
| Nagata table | Japan MoE | PDF live | 223 | Air ODT | PDF | Government publication; licence not stated |
| SuperScent | Charité | **offline** | ~2,100 | none | – | – |
| AromaDb | CSIR-CIMAP | moved to aromadb.cimapbioinfo.in | 1,321 | none | Web | not stated |
| ODORactor | SJTU | live, frozen 2011 | 3,038 | none | Web | All rights reserved |

(Sources for each row are cited in §§1–5 above.)

### Inferences
- Legal background, **not verified in this research; consult counsel**:
  - Bare numeric facts such as a threshold value are generally weakly protected by copyright in the US.
  - In the EU, a substantial extraction from a database can trigger sui generis database rights. Explicit contractual terms (Leibniz-LSB, Fragrantica, TGSC, VCF) add contractual risk regardless of copyright.
  - The EU DSM-Directive text-and-data-mining exception (Art. 4) may allow commercial TDM unless the rights holder has opted out.
- A defensible commercial pipeline would:
  - train its core potency head on CC BY/Etalab/Apache/US-gov data (Keller 2016, Ma 2021, laymen 2025, the Metabolites ODT set after auditing its upstream sources, HSDB-only PubChem annotations, EPA 1992, M2OR for receptor-level auxiliary tasks);
  - license GoodScents, Leibniz-LSB or VCF data rather than scrape them;
  - keep NC data (GS-LF, FlavorDB, FooDB) to internal research and benchmarking unless permission is obtained.

### Gaps
- The copyright status of the Abraham 2012 and Wakayama 2019 numeric tables (journal SI) was not resolved.
- I did not check whether HSDB text in PubChem is formally public domain; it is governed by NLM web policies.
- The status of EPA 1992 as a US-government work (and therefore public domain) is an inference, not confirmed on the document.
