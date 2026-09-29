# Odor intensity / odor strength / dose-response / tenacity datasets for training odor-potency models

Research notes, verified 2026-09-25. Where I inspected files directly (GitHub raw files, the GitHub API, the Europe PMC full-text API), the counts below are my own tallies of the downloaded files and are labelled "(counted)". Numbers taken from papers are cited to those papers. Figures I could not verify are marked "uncertain".

---

## Q0. Which datasets exist overall, and what are their key attributes? (consolidated catalogue)

### Takeaway
Only a handful of free datasets give per-molecule, concentration-annotated, rated intensity. The core set is Keller & Vosshall 2016 / DREAM (480 molecules, 2 dilutions, 55 raters, CC BY 4.0), Lee et al. 2023 POM Data S3 (398 odorants, 18 raters, intensity 0–10, Apache-2.0 repo, but public structures for only about 208), Wakayama 2019 (314 perfumery materials with fitted dose-response curve parameters, license unclear), Ravia 2020 (181 molecules; 72 stimuli at 3 dilutions) and Keller 2012 (66 odors × 2 concentrations, 391 raters, CC BY). Ordinal "odor strength" at scale comes only from The Good Scents Company (copyrighted; "permission to reproduce is required"), either scraped directly or through the Fichtelmann et al. 2025/2026 pipeline (2,056 molecules; MIT code, raw Good Scents data not redistributed).

### Cited Findings
Catalogue (one row per dataset; details and sources are in the sections below):

| Dataset | Molecules | Raters | Conc./dilutions | Intensity scale | Per-subject raw | IDs | Format | License | Key quality issues |
|---|---|---|---|---|---|---|---|---|---|
| Keller & Vosshall 2016 (BMC Neurosci) | 480 | 55 analysed (61 completed) | 2 per molecule; 437 molecules at 1/1,000 and 1/100,000; others 1/10 vs 1/1,000 or 1/100,000 vs 1/10^7; paraffin oil | 0–100 slider ("How strong is the smell?") | Yes | CID, CAS, name | xlsx (Additional file 1); Pyrfume CSV | CC BY 4.0 | dilutions not intensity-matched across molecules; purity >97% (median 98%); impurities can dominate weak odorants |
| DREAM Olfaction Prediction Challenge (Keller et al. 2017 Science) | 476 (338 train CIDs in TrainSet.txt) | 49 | same as Keller 2016 ("high"/"low" dilution) | 0–100 | Yes | CID | TSV (GitHub), Synapse | GitHub repo MIT; underlying data from the CC BY Keller 2016 paper | subset of Keller 2016; intensity scoring used the "high" dilution |
| Keller et al. 2012 (BMC Neurosci) | 66 odors (Pyrfume manifest says "134 odorants", which conflicts) | 391 | 2 per odor (high/low; mostly paraffin oil, some PG/water) | discrete category scale (0–7 in the Pyrfume file) | Yes (107,916 rows, counted) | CID, CAS | xlsx; Pyrfume CSV | CC BY | category scale; some stimuli are mixtures/oils |
| Lee et al. 2023 POM (Science) Data S3 | 398 samples | 18 (15–18 per molecule) | one concentration per molecule, varied (e.g., 1.0, 0.1, 0.01 of "Final [ ]"; PG, neat, mineral oil) | 0–10 (as stored) + "NoOdor" flag | Yes, 2 reps (13,282 rows, counted) | RedJade codes; SMILES public for about 208 (Data S7) | CSV (Git LFS) | Apache-2.0 repo | concentrations not matched; GC-O found some samples contaminated/mixed; about half of structures not public |
| Wakayama et al. 2019 (Kao; I&EC Res) | 314 perfumery raw materials | uncertain | full dose-response per material (gas conc.) | LMS 0–100 | No (fitted parameters I_max, C, D only) | CAS → CID (Pyrfume) | Pyrfume CSV/TXT (scraped from SI) | paper paywalled (ACS); no license file in Pyrfume, so treat as copyrighted | only curve parameters; functional form must be taken from the paper |
| Ravia et al. 2020 (Nature) | 181 mono-molecule CIDs (257 stimuli with intensity) + mixtures | uncertain | 72 stimuli at 3 dilutions | about 0–100 (group means) | No (means in Pyrfume) | CID | Pyrfume CSV | not stated in Pyrfume | mono-molecules diluted toward iso-intensity |
| Ma et al. 2021 (Data in Brief) | 72 food odorants + 222 binary mixtures | 30 trained (1 removed) | one "iso-intense" conc. per odorant (mg/mL, PG or water) | anchored VAS (2 reference standards; ratio-like) | Yes | CID (Pyrfume) | xlsx on INRAE Data portal | article CC BY; dataset license not verified | concentrations deliberately equalised in intensity, so potency is encoded in the concentration, not the rating |
| Snitz et al. 2019 SmellSpace (Chem Senses) | 24 CIDs / 35 stimulus codes (incl. mixtures) | 983 online + 26 lab | scratch-and-sniff in isopropyl myristate | "WeakStrong" 1–101 (counted) | Yes | CID | xlsx; Pyrfume CSV | CC BY-NC 4.0 | microencapsulated delivery; uncontrolled home conditions |
| Arshamian et al. 2022 | 10 | 125 intensity rankers (counted) | fixed | rank 1–10 | Yes | CID | TXT/CSV (Pyrfume) | not stated | ranks only; 10 molecules |
| Mayhew et al. 2022 (PNAS) | 1,924 odor/odorless labels; 128 lab-tested | 3-AFC, 75 trials/molecule | 1 g in jar | binary + p-value, confidence | Trial counts per molecule | SMILES, CID | CSV (GitHub, Pyrfume) | article CC BY-NC-ND; repo license "NOASSERTION" | 22% of "odorous" molecules were actually contaminated odorless compounds |
| Fichtelmann & Westermayr 2025/2026 (RSC Adv.) | 2,056 (1,684 Good Scents + 372 PubChem) | n/a (literature) | n/a | ordinal: odorless/low/medium/high | n/a | SMILES, CAS | code MIT; Zenodo | Good Scents raw data not redistributed (copyright) | "medium" dominates (1,071); PubChem labels regex-derived |
| Good Scents Company (web) | about 42,234 entries scraped | n/a | "recommend smelling in X% solution" + substantivity "hours at 100%" | low/medium/high/very high | n/a | CAS, some SMILES | HTML | copyright; "Permission to reproduce is required" | SMILES sometimes wrong; only 13 "very high" |
| OlfactionBase (Sharma 2021b) | 19 CIDs with a "Strength" value (counted) | n/a | n/a | low/medium/high/very high | n/a | CID | Pyrfume CSV | "All Rights Reserved" | tiny |
| Dravnieks 1985 Atlas | 160 samples (139 unique CIDs, counted); 6 at a second "low" concentration | about 120–150 | samples presented at "similar odor intensity" | no intensity ratings (applicability/use only) | No | CID, CAS | Pyrfume CSV; book (ASTM DS61) | ASTM copyright; no license in Pyrfume | not a potency dataset |
| Patte, Etcheto & Laffort 1975 (Chem Senses) | 110 slopes / 124 thresholds / 78 biological limits / 110 physical limits | literature compilation | n/a | Stevens log-log slopes | No | names | PDF only | paywalled | not machine-readable |

### Inferences
- For a regression target of "intensity at a known concentration", combine Keller 2016 (plus DREAM), Lee 2023 S3 (for molecules with public SMILES), Keller 2012, and Ravia 2020 mono-molecules. Condition every rating on log-dilution and solvent.
- For a "potency" target that does not depend on concentration, the best free option is to fit a curve (e.g., I = f(log c)) per molecule where ≥2 concentrations exist (Keller 2016: 2 points; Ravia: up to 3 points; Wakayama: fitted curves already).
- Ordinal perfumery "odor strength" (Good Scents) is the only large-N potency proxy, but it is copyrighted. Commercial ML training on scraped Good Scents data carries legal risk.

### Gaps
- Exact rater counts for Wakayama 2019 and Ravia 2020 intensity experiments were not verified (papers paywalled or not read in full).
- The license of the INRAE dataset (Ma 2021) was not verified on the portal page.

---

## Q1. Keller & Vosshall 2016 / DREAM Olfaction Prediction Challenge: where to download, license, how intensity was measured

### Takeaway
The full Keller & Vosshall 2016 dataset (480 molecules × 2 concentrations, 55 analysed subjects, per-subject 0–100 intensity ratings) is free under CC BY 4.0 as Additional file 1 of the BMC Neuroscience paper. Pyrfume (`keller_2016`) and the DREAM GitHub repo (MIT) mirror it. The DREAM subset covers 476 molecules and 49 subjects.

### Cited Findings
- Keller & Vosshall 2016 tested "480 structurally and perceptually diverse molecules at two concentrations using a panel of 55 healthy human subjects". 61 subjects completed all ten visits, and the 6 with the lowest intensity-rating replicability/acuity were excluded. — [Keller & Vosshall 2016, PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC4977894/)
- Intensity, pleasantness, familiarity and 20 descriptors were rated with a slider whose final position "was translated into a scale from 0 to 100". — [Keller & Vosshall 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4977894/)
- Stimuli: 1 mL of diluted molecule in paraffin oil in vials. Chemicals were ">97 % pure with a median purity of 98 %". The authors call this a limitation because a 3% impurity can dominate the percept of an odorless molecule. — [Keller & Vosshall 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4977894/)
- 437 of the 1,000 stimuli were at 1/1,000 dilution. Water was rated 14.44 on average. 61 molecules at 1/1,000 were rated below water, and the authors estimate that about 126 molecules are undetectable at 1/1,000. — [Keller & Vosshall 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4977894/)
- The authors state that two dilutions "are not sufficient to determine the parameters of the concentration–response functions". Crossovers occur: methyl salicylate > methyl caprylate at 1/1,000 but the reverse at 1/100,000. — [Keller & Vosshall 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4977894/)
- Three molecules (2-methyl-1-butanol, isopropyl acetate, thiophene) had substantially different ratings between the two presentations of their high concentration. — [Keller & Vosshall 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4977894/)
- License: "distributed under the terms of the Creative Commons Attribution 4.0 International License". The authors are "making the entire dataset freely available (Additional file 1)". — [Keller & Vosshall 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4977894/); the Europe PMC REST API also returns license "cc by" for this DOI — [Europe PMC search API](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1186/s12868-016-0287-2%22&format=json&resultType=core)
- Pyrfume `keller_2016` holds the raw `12868_2016_287_MOESM1_ESM.xlsx` and a processed long-format `behavior.csv` that includes the field "HOW STRONG IS THE SMELL?". The processed data have 1,430,000 rows, 960 stimuli, 480 unique CIDs, dilutions {1/10, 1/1,000, 1/100,000, 1/10^7}, paraffin oil only, and 55 subjects (counted). — [pyrfume-data keller_2016 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/keller_2016/manifest.toml)
- Pyrfume's `prediction_targets/keller_2016.csv` averages ratings "across all concentrations, replicates, and subjects". This is unsuitable for a concentration-aware potency target. — [pyrfume-data prediction_targets manifest](https://github.com/pyrfume/pyrfume-data/blob/main/prediction_targets/manifest.toml)
- The pyrfume-data repository itself is MIT-licensed. Individual datasets carry their own terms. — [pyrfume-data repo](https://github.com/pyrfume/pyrfume-data)
- DREAM: the challenge asked participants to predict intensity, pleasantness and 19 descriptors for each of 49 individuals and for population mean and SD. Data and code are in the GitHub repo. — [dream-olfaction/olfaction-prediction](https://github.com/dream-olfaction/olfaction-prediction); [Keller et al. 2017 Science (PubMed)](https://pubmed.ncbi.nlm.nih.gov/28219971/)
- Snitz et al. describe the DREAM data as "49 participants who rated 476 odorants across 19 descriptors", posted for download. — [Snitz et al. 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6462760/)
- GitHub repo `dream-olfaction/olfaction-prediction` is MIT-licensed (last push 2019-08-09). `data/` contains TrainSet.txt, leaderboard_set.txt, LBs1/LBs2, TestSet.txt, CID_testset/leaderboard, dilution_testset/leaderboard, molecular_descriptors_data.txt (Dragon), and "0869 final data Pablo.xlsx" (counted via GitHub API). — [GitHub repo data folder](https://github.com/dream-olfaction/olfaction-prediction/tree/master/data)
- TrainSet.txt (TSV) columns: Compound Identifier (CID), Odor, Replicate, Intensity ("high"/"low"), Dilution, subject #, INTENSITY/STRENGTH, VALENCE/PLEASANTNESS, then 19 descriptors. It has 35,084 rows, 338 unique CIDs and 49 subjects, with intensity values 0–100 (counted). — [TrainSet.txt](https://github.com/dream-olfaction/olfaction-prediction/blob/master/data/TrainSet.txt)
- Synapse ID syn2811262 resolves to the "DREAM Olfaction Prediction Challenge" page. It is JavaScript-rendered, so its data-use terms could not be read in this session. — [Synapse syn2811262](https://www.synapse.org/Synapse:syn2811262/wiki/78368)
- Osmo's Lee et al. 2023 reproduction repo also re-hosts `DREAMTrainSet.txt` (Apache-2.0 repo). — [osmoai/publications lee_et_al_2023](https://github.com/osmoai/publications/tree/main/lee_et_al_2023)
- Fichtelmann & Westermayr used Keller 2016 as an external hold-out test set for ordinal odor-strength prediction. — [odor-strength GitHub README](https://github.com/peter-fichtelmann/odor-strength)

### Inferences
- The Keller 2016 xlsx under CC BY 4.0 is the cleanest-licensed intensity source: it permits commercial use and ML training with attribution. Prefer it over Synapse copies, whose terms are unverified.
- Within one molecule, the high-vs-low difference over a known 100-fold dilution gives a crude 2-point slope. Across molecules, only the 437 molecules at 1/1,000 are directly comparable at equal liquid dilution. Vapor-phase concentration still differs with volatility and solvent partitioning.

### Gaps
- Could not render Synapse to confirm whether the DREAM data require a data-use agreement or registered account.
- The official DREAM train/leaderboard/test split (338/69/69) is consistent with the 338 CIDs I counted, but I did not confirm the 69/69 split from a primary source.

---

## Q2. Dravnieks Atlas of Odor Character Profiles (1985): does it include intensity, and what free versions exist?

### Takeaway
No. Dravnieks gives percent applicability and use of 146 descriptors for 160 samples that were deliberately presented at a similar odor intensity. There are no intensity ratings. Pyrfume's `dravnieks_1985` is a free digitisation, but it has no license file and the book is ASTM-copyrighted.

### Cited Findings
- 160 chemicals and mixtures, about 120 panelists (over 100 panelists at 12 labs), 146 descriptors scored 0–5. Samples "were assessed at a similar odor intensity". Outputs are percent applicability (0–100). — [ASTM DS61 store page](https://store.astm.org/ds61-eb.html); [MDPI Sensors 2011 summary](https://www.mdpi.com/1424-8220/11/4/3667)
- Snitz et al. summarise Dravnieks as "average ratings from ~150 participants who rated 138 monomolecules and 16 mixtures/oils across 146 verbal descriptors". — [Snitz et al. 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6462760/)
- Pyrfume `dravnieks_1985` is tagged "human;odorCharacter" (not "intensity"). Its processed files are `behavior_1.csv` (applicability) and `behavior_2.csv` (use). It was digitised by the Bensafi and Sobel labs, with mixtures removed. — [pyrfume dravnieks_1985 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/dravnieks_1985/manifest.toml)
- Pyrfume `stimuli.csv` has 160 stimuli and 139 unique CIDs, with a "Conc" field of "high" (154) or "low" (6) (counted). One example is Aldehyde C-16 at both high and low. — [pyrfume dravnieks_1985 stimuli.csv](https://github.com/pyrfume/pyrfume-data/blob/main/dravnieks_1985/stimuli.csv)

### Inferences
- Because Dravnieks equated intensity, its concentrations (in the book) could in principle serve as an "iso-intensity concentration", which is an inverse-potency proxy. However, the concentrations are not in the Pyrfume files beyond high/low labels.

### Gaps
- Whether the printed atlas lists the exact presentation concentration for each sample was not verified.

---

## Q3. Other psychophysics datasets: which contain intensity or odor/no-odor labels?

### Takeaway
Intensity is present in Keller 2012, Snitz 2019 (SmellSpace), Ravia 2020, Ma 2021, Arshamian 2022 and Lee 2023 (POM Data S3). Odor/no-odor labels are in Mayhew 2022 and in Lee 2023 (per-trial "NoOdor"). Snitz 2013, Bushdid 2014 and Weiss 2012 in Pyrfume contain similarity, discrimination or descriptor data only, with no usable intensity.

### Cited Findings
**Lee et al. 2023 (Principal Odor Map, Science)**
- 15–18 panelists "rated intensity and pleasantness" and gave RATA ratings on a 55-word lexicon for each of about 400 molecules. — [Lee et al. bioRxiv v2](https://www.biorxiv.org/content/10.1101/2022.09.01.504602v2.full)
- The Osmo repo `osmoai/publications/lee_et_al_2023` (Apache-2.0) has Data S1–S7 as Git-LFS CSVs (counted after LFS download):
  - Data S3 has columns StartTime, SubjectCode, Rep, SampleIdentifier, Intensity, Pleasantness, NoOdor and 55 descriptors, with 13,282 rows, 18 subjects, 398 samples, reps 1–2 and Intensity 0–10.
  - Data S1 lists solvent (PG, neat, MO, ddH2O), "Final [ ]" concentration and GC-O purity results ("clean", "mixed", "contaminated").
  - Data S7 gives SMILES for 208 of the 398 codes.
  - Source: [osmoai/publications lee_et_al_2023/data](https://github.com/osmoai/publications/tree/main/lee_et_al_2023/data); [Osmo repo license (Apache-2.0)](https://github.com/osmoai/publications)
- Europe PMC lists the POM paper (PMC11898014) as not open access. — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- The GNN training set (about 5,000 molecules) is GoodScents + Leffingwell ("GS-LF"), which is licence-restricted. It has no intensity. — [Lee et al. bioRxiv](https://www.biorxiv.org/content/10.1101/2022.09.01.504602v2.full)

**Mayhew et al. 2022 (PNAS, "Drawing the borders of olfactory space")**
- 1,924 unique molecules labelled odorous (84%) or odorless (16%). 128 were lab-classified via 3-AFC with 75 trials per molecule plus GC analysis. "22% of molecules classified as odorous were actually odorless compounds contaminated with odorous compounds". Data are on GitHub. — [Mayhew et al. 2022, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9169660/)
- The article license is CC BY-NC-ND (per Europe PMC). The GitHub repo `emayhew/OlfactorySpace` shows license "NOASSERTION". — [GitHub emayhew/OlfactorySpace](https://github.com/emayhew/OlfactorySpace); [Europe PMC search API](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1073/pnas.2116576119%22&format=json&resultType=core)
- Pyrfume `mayhew_2022/behavior_2.csv` columns: compound, amount.in.jar (1 g), number.trials, number.correct.trials, p.value, mean.confidence.in.choice, initial/final odor class, QC reclassification reason. — [pyrfume mayhew_2022 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/mayhew_2022/manifest.toml)

**Keller et al. 2012 (olfactory demography)**
- 391 subjects rated the intensity and pleasantness of 66 odours at two concentrations. The dataset is "made available here in its entirety" (Additional file 1). The rating scale is categorical, with steps such as "very weak" to "extremely weak". — [Keller et al. 2012, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3493268/) (CC BY per Europe PMC)
- Pyrfume `keller_2012/behavior_3.csv` has stimulus, subject, rep and intensity, with 107,916 rows, 391 subjects and values 0–7 (counted). The manifest describes it as "Intensity for 134 odorants", which conflicts with the paper's 66 odours × 2 concentrations. Pyrfume provides intensity ML benchmarks. — [pyrfume keller_2012 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/keller_2012/manifest.toml)

**Snitz et al. 2019 (SmellSpace, Chem Senses)**
- 985 participants completed the task (983 adults retained), plus 26 lab controls. Descriptors included "Intensity". Odorants were diluted in isopropyl myristate and delivered in scratch-and-sniff booklets. The complete raw data are posted. — [Snitz et al. 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6462760/)
- License is CC BY-NC 4.0; commercial re-use needs OUP permission. — [pyrfume snitz_2019 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/snitz_2019/manifest.toml)
- Pyrfume `behavior_1.csv` has a "WeakStrong" column (1–101), 11,796 rows, 983 subjects, 35 stimulus codes and 24 CIDs mapped (counted). — [pyrfume snitz_2019](https://github.com/pyrfume/pyrfume-data/tree/main/snitz_2019)

**Ravia et al. 2020 (Nature, olfactory metamers)**
- Pyrfume `ravia_2020/behavior_1.csv` is "Intensity of mixtures used". Stimuli are 261 mono-molecule, 230 mixture. 257 mono-molecule stimuli (181 unique CIDs) have intensity at dilution #1, and 72 also have dilutions #2 and #3. Values are about 0–100 group means (counted). The manifest has no license file. — [pyrfume ravia_2020 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/ravia_2020/manifest.toml)

**Ma et al. 2021 (Data in Brief; binary mixtures)**
- 72 food odorants and 222 binary mixtures (198 unique + 24 duplicates), rated by 30 trained assessors (subject 47 removed). The data include per-subject intensity of components alone (IA, IB), within the mixture (IAmix, IBmix) and of the mixture (IAB), plus pleasantness. Intensity was rated on a VAS anchored by two standards (ethyl 2-methylbutyrate 1.8 g/L; linalool 10.7 g/L) using ratio instructions ("twice as strong → twice the distance"). Odorants were pre-diluted to rough iso-intensity. Data are at Portail Data INRAE, doi:10.15454/51OVY6. The article is CC BY. — [Ma et al. 2021, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8144660/); [dataset DOI](https://doi.org/10.15454/51OVY6)
- Pyrfume `ma_2021/stimuli.csv` gives concentration (mg/mL), solvent (water / 1,2-propanediol) and purity per CID. — [pyrfume ma_2021 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/ma_2021/manifest.toml)

**Arshamian et al. 2022 (cross-cultural)**
- Pyrfume `arshamian_2022/behavior_2.csv` is "All intensity data. Rank 1 is most intense… Rank 10 is the least intense". It covers 125 participants (counted) and 10 CIDs (379, 1183, 3314, 6054, 6549, 7762, 8077, 10430, 18827, 32594), with benchmarks for intensity. — [pyrfume arshamian_2022 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/arshamian_2022/manifest.toml)

**No usable intensity in Pyrfume copies**
- Snitz 2013: similarity ratings only. — [pyrfume snitz_2013 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/snitz_2013/manifest.toml)
- Bushdid 2014: triangle-test results only; tags "odorCharacter". — [pyrfume bushdid_2014 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/bushdid_2014/manifest.toml)
- Weiss 2012: descriptors for "olfactory white" only. — [pyrfume weiss_2012 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/weiss_2012/manifest.toml)

**Other**
- Sagar et al. 2023 (Nature Neuroscience) collected fMRI responses to 160 odors in 3 subjects. — [Sagar et al. 2023](https://www.nature.com/articles/s41593-023-01414-4)
- National Geographic Smell Survey: about 1.4 million people gave detection, identification, intensity and pleasantness ratings for 6 odorants. — [Snitz et al. 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6462760/). Pyrfume has a `nat_geo_1986` folder tagged "odorCharacter". — [pyrfume-data](https://github.com/pyrfume/pyrfume-data/tree/main/nat_geo_1986)

### Inferences
- Lee 2023 Data S3 is arguably the second-most valuable single-molecule intensity set after Keller 2016. It is per-subject and replicated, has a "NoOdor" flag and comes with GC-O purity QC. It is limited by one concentration per molecule and by about 190 codes without public structures.
- Ravia's 72 three-dilution stimuli and Keller 2016's two-dilution pairs are the only free multi-point human intensity functions for dozens to hundreds of molecules.
- Iso-intensity designs (Ma 2021, Ravia, Weiss, Bushdid, Dravnieks) put potency information into the chosen concentration rather than the rating. For those designs, model the concentration that yields a fixed intensity.

### Gaps
- Sagar 2023: full text via Europe PMC was not retrievable. It is unverified whether per-odor intensity ratings are publicly released.
- Lötsch/Hummel: no molecule-level intensity dataset was identified. Their work mostly concerns Sniffin' Sticks threshold/discrimination/identification norms.
- The Arshamian 2022 license and final publication venue were not verified.

---

## Q4. Stevens power-law exponents and concentration–intensity functions: any tabulated and free?

### Takeaway
The classic compilation (Patte, Etcheto & Laffort 1975: 110 Stevens slopes, 124 thresholds) exists only as a paywalled PDF. The only free machine-readable concentration–intensity functions I found at scale are Wakayama 2019 (314 perfumery materials; fitted I_max/C/D parameters via Pyrfume, copyright status unclear) plus the 2- and 3-point data in Keller 2016 and Ravia 2020.

### Cited Findings
- Patte, Etcheto & Laffort 1975, "Selected and standardized values of suprathreshold odor intensities for 110 substances", Chem. Senses 1(3):283–305. It models intensity via detection threshold, log-log slope and a ceiling. It compiled 110 slopes, 124 thresholds, 78 biological limits and 110 physical limits. It is paywalled ("only available as a PDF"; 24-h access about €53). — [Oxford Academic abstract](https://academic.oup.com/chemse/article-abstract/1/3/283/401623)
- Laffort 1987 derived power-law exponents from olfactory thresholds (NYAS Annals; paywalled). — [Wiley](https://nyaspubs.onlinelibrary.wiley.com/doi/10.1111/j.1749-6632.1987.tb43582.x)
- Wakayama, Sakasai, Yoshikawa & Inoue (Kao) 2019, I&EC Research. They built a database of odor-intensity standard curves (intensity vs gas concentration) for 314 perfumery raw materials using the Labeled Magnitude Scale (0–100, "barely detectable" … "strongest imaginable"). Prediction RMSE was 6.22 for single components and 6.69 for mixtures. — [ACS DOI page](https://pubs.acs.org/doi/10.1021/acs.iecr.9b01225); [Kao R&D news](https://kao.com/global/en/news/rd/2020/20200108-001)
- Pyrfume `wakayama_2019` has behavior.csv with columns I_max, C, D for 314 CIDs ("Supratheshold intensity curve parameters"), scraped from the supplemental PDF, with ML benchmarks for I_max, C and D. The raw TXT lists CAS, name, I_max, C, D (e.g., 1,8-cineole 58.98, 1.41, 0.86). No LICENSE file is present in the folder. — [pyrfume wakayama_2019 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/wakayama_2019/manifest.toml); [raw TXT](https://github.com/pyrfume/pyrfume-data/blob/main/wakayama_2019/wakayama-intensity.txt)
- Kao also published a model for the odor intensity of fragrance mixtures (I&EC Research, 2013). — [ACS](https://pubs.acs.org/doi/abs/10.1021/ie302538c)
- Cometto-Muñiz & Cain, "Thresholds for odor and nasal pungency" (Physiol. Behav. 1990) is freely available on eScholarship. It covers thresholds, not suprathreshold slopes. — [eScholarship PDF](https://escholarship.org/content/qt0mv466n9/qt0mv466n9_noSplash_cb7e6e486e48c10e334c6a201aa8eedf.pdf)
- Kamadia et al. 2006 studied relationships between odorant concentration and aroma intensity (J. Food Sci.; paywalled). — [Wiley](https://ift.onlinelibrary.wiley.com/doi/10.1111/j.1365-2621.2006.tb15640.x)

### Inferences
- The Wakayama parameters are the single best dose-response training target: 314 materials, all from one lab and one method. However, the ACS supplement is copyrighted. Treat the Pyrfume copy as research-use only unless Kao or ACS permission is obtained.
- A threshold dataset (another researcher's scope) combined with Patte-style slopes would let one reconstruct Stevens functions, but no free tabulated slope set was found.

### Gaps
- The functional form linking I_max, C and D (e.g., Hill or logistic in log-concentration) and the panel size were not verified from the Wakayama full text.
- No free, tabulated Wise/Olsson or Dalton intensity-function dataset was found. These appear only as figures or tables in paywalled papers (not verified individually).

---

## Q5. Perfumery data (Good Scents, Leffingwell PMP, Arctander, Sigma, Perfumer's Apprentice / Pell Wall, odour value): which are free or scrapeable, and on what terms?

### Takeaway
The Good Scents Company is the only large source of ordinal "odor strength" (low/medium/high/very high, with a recommended smelling dilution) and "substantivity (hours at 100%)". It is copyrighted ("Permission to reproduce is required"). Pyrfume's Good Scents and Leffingwell folders contain odor descriptors only, not strength. Their manifests reference LICENSE files that are missing from the repo. Leffingwell PMP 2001 is a paid commercial database. Arctander (Pyrfume) is CC BY-NC and has no strength field.

### Cited Findings
**Good Scents Company**
- Example page (benzaldehyde):
  - Odor strength: "high, recommend smelling in a 10.00 % solution or less".
  - Substantivity: "4 hour(s) at 100.00 %".
  - Odor description given at 10% in dipropylene glycol.
  - Source: [TGSC benzaldehyde page](http://www.thegoodscentscompany.com/data/rw1001491.html)
- Copyright notice, verbatim: "The Good Scents Company retains all exclusive copyrights. All information available from The Good Scents Company World Wide Web Pages are protected under the U.S. and Foreign Copyright Laws. Permission to reproduce is required." It says nothing specific about scraping or ML. — [TGSC copyright page](http://www.thegoodscentscompany.com/misc/copyrigh.html)
- Pyrfume `goodscents` is a CSV dump of a web scrape from January 17, 2022, by Contrebande Labs. The manifest says "see LICENSE for use restrictions; Pyrfume developers make no claims concerning copyright". — [pyrfume goodscents README](https://github.com/pyrfume/pyrfume-data/blob/main/goodscents/README.md); [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/goodscents/manifest.toml)
- The LICENSE files referenced by the `goodscents` and `leffingwell` manifests return 404 in pyrfume-data main (checked via the GitHub API tree on 2026-09-25). Only root, `arctander_1960` and `sisson_2024` LICENSE files exist. — [pyrfume-data repo tree](https://github.com/pyrfume/pyrfume-data)
- Pyrfume `goodscents/stimuli.csv` has 4,626 stimuli with "Concentration %" and "Solvent", i.e., the dilution at which the odor was described (100%: 2,225; 10%: 704; 0.1%: 537; 1%: 523; blank: 489; counted). It has no strength or substantivity columns. — [pyrfume goodscents stimuli.csv](https://github.com/pyrfume/pyrfume-data/blob/main/goodscents/stimuli.csv)
- Fichtelmann & Westermayr's crawler extracted odor strength, SMILES and CAS for "all 42,234 entries". Only 13 compounds were "very high", and these were merged into "high". Some Good Scents SMILES were incorrect, so CAS was resolved via the CAS Common Chemistry API. They state "The raw Good Scents data set is protected under the U.S. [copyright]" and did not redistribute it; users re-run the scraper. — [Fichtelmann & Westermayr, arXiv HTML](https://arxiv.org/html/2512.08683)

**Leffingwell**
- Pyrfume `leffingwell` (Sanchez-Lengeling et al., about 3.5k molecules) has descriptors only. The manifest says "see LICENSE for use restrictions" (the file is missing). The Zenodo record 10.5281/zenodo.4085098 has access_right "restricted" (checked via Zenodo API). — [pyrfume leffingwell manifest](https://github.com/pyrfume/pyrfume-data/blob/main/leffingwell/manifest.toml); [Zenodo 4085098](https://zenodo.org/records/4085098)
- PMP 2001 (BACIS, distributed by Leffingwell & Associates) covers >4,100 perfumery materials with "Odour Descriptions, Performance, Application", plus stability in 21 end-products. It costs US$2,775 for a non-exclusive 2-workstation license. — [Leffingwell PMP 2001](http://www.leffingwell.com/bacispmp.htm)

**Arctander, Sigma, OlfactionBase, FlavorDB, AromaDB**
- Arctander 1960 (Pyrfume) is CC BY-NC 4.0, with descriptors only. — [pyrfume arctander_1960 LICENSE](https://github.com/pyrfume/pyrfume-data/blob/main/arctander_1960/LICENSE)
- Sigma-Aldrich F&F catalog 2014 (Pyrfume) has descriptors only. The source PDF is kept in a "[private]" section. — [pyrfume sigma_2014 manifest](https://github.com/pyrfume/pyrfume-data/blob/main/sigma_2014/manifest.toml)
- OlfactionBase (Pyrfume `sharma_2021b`) `behavior_1.csv` has a "Strength" column. Only 19 of 5,090 CIDs have a value (high 230 rows, medium 108, very high 3, low 3; counted). License: "2022 Copyright OlfactionBase. All Rights Reserved." — [pyrfume sharma_2021b manifest](https://github.com/pyrfume/pyrfume-data/blob/main/sharma_2021b/manifest.toml)
- FlavorDB (Pyrfume) is CC BY-NC-SA 3.0. AromaDB is restricted to CSIR-CIMAP terms. Both have descriptors only. — [pyrfume flavordb manifest](https://github.com/pyrfume/pyrfume-data/blob/main/flavordb/manifest.toml); [pyrfume aromadb manifest](https://github.com/pyrfume/pyrfume-data/blob/main/aromadb/manifest.toml)

**Tenacity / odor life**
- Perfumer's Apprentice lists fragrance ingredients online, some with tenacity in hours. — [Perfumer's Apprentice ingredient list](https://shop.perfumersapprentice.com/c-244-all-fragrance-ingredients.aspx)
- A Perfumer & Flavorist article, "Odor tenacity of perfumery materials", exists but returned HTTP 403. — [P&F](https://www.perfumerflavorist.com/fragrance/ingredients/article/21855887/odor-tenacity-of-perfumery-materials)

### Inferences
- The Good Scents "recommend smelling in X% solution or less" string is itself a semi-quantitative potency label (≈ an iso-intensity dilution). It is arguably more informative than the 4-level class. It is available only by scraping copyrighted pages.
- For any commercial model, Good Scents, Leffingwell, OlfactionBase, AromaDB and Sigma-derived labels should be treated as not cleared. Arctander and FlavorDB are explicitly non-commercial.

### Gaps
- No free, bulk, machine-readable Perfumer's Apprentice or Pell Wall "odor life" dataset was verified. Their terms of use were not checked.
- "Odour value" (concentration/threshold, i.e., OAV) and "odour intensity" figures from IFF or Givaudan literature were not located as free tabulated datasets in this session. The concept definition was also not verified from a primary source here.

---

## Q6. Environmental odor science (EN 13725, VDI 3882, n-butanol scale): any open molecule-level datasets?

### Takeaway
I found no open molecule-level intensity dataset built on EN 13725 or VDI 3882. EN 13725 measures odor concentration (ouE/m³) of samples, not per-molecule intensity functions, and the standards themselves are paywalled. The closest public molecule-level anchors are Japan's Offensive Odor Control Law standards for 22 substances. Their ppm ranges correspond to intensity 2.5–3.5 on the Japanese six-level scale.

### Cited Findings
- Japan's MoE: the regulation standard range is set equivalent to odor intensity 2.5–3.5, and 22 specified substances are regulated at site boundaries. — [MoE Japan, Offensive Odor Control Law overview PDF](https://www.env.go.jp/content/900452838.pdf); [MoE law page](https://www.env.go.jp/en/laws/air/odor/ch.html)
- The MoE's English "Application and Quality Control of Odor Measurement" PDF tabulates ppm standards, for example:
  - ammonia 1–5 ppm
  - methyl mercaptan 0.002–0.01 ppm
  - hydrogen sulfide 0.02–0.2 ppm
  - methyl sulfide 0.01–0.2 ppm
  - dimethyl (di)sulfide 0.009–0.1 ppm
  - trimethylamine 0.005–0.07 ppm
  - acetaldehyde 0.05–0.5 ppm
  - styrene 0.4–2 ppm

  It also lists the 22 regulated substances (aldehydes, i-butanol, ethyl acetate, MIBK, toluene, xylene, C3–C5 fatty acids). The PDF text was extracted programmatically, so the column assignments (residential vs industrial) are uncertain. — [MoE Japan 02_2.pdf](https://www.env.go.jp/en/air/odor/measure/02_2.pdf)

### Inferences
- The Japanese standards give about 22 "concentration at intensity 2.5/3.0/3.5" triplets for industrial odorants. That is useful only as a small external calibration set in air (ppm), not as training data.

### Gaps
- VDI 3882 / EN 13725 / ASTM E544 (n-butanol reference) standards are paywalled, and I found no open per-molecule dataset derived from them.
- The exact Japanese per-substance intensity-2.5/3.0/3.5 concentration table (and underlying Weber–Fechner coefficients) was not cleanly extracted.

---

## Q7. 2020–2026 ML papers predicting odor intensity/strength with released data

### Takeaway
The main recent work with released code and data is Fichtelmann & Westermayr (arXiv Dec 2025; RSC Advances 2026). It covers ordinal odor strength for 2,056 molecules, with MIT code and Zenodo, but the Good Scents part must be re-scraped. Other intensity-ML resources reuse Keller 2016/DREAM or the Pyrfume benchmarks (Keller 2012, Arshamian, Wakayama). The DREAM mixture challenges (2024–2025) target perceptual distance, not intensity.

### Cited Findings
- Fichtelmann & Westermayr, "Machine learning for smell: ordinal odor strength prediction of molecular perfumery components":
  - Posted to arXiv on 9 Dec 2025 and published in RSC Advances 2026 (doi:10.1039/d6ra01805j, CC BY).
  - Classes: odorless / low / medium / high. Data: 1,684 Good Scents + 372 PubChem = 2,056. Class counts: odorless 383, low 244, medium 1,071, high 358.
  - PubChem labels come from keyword matching of odor descriptions, and PubChem compounds below 20% Tanimoto to any Good Scents compound were removed.
  - Keller 2016 was used as an independent hold-out test set.
  - Sources: [arXiv abstract](https://arxiv.org/abs/2512.08683); [arXiv HTML](https://arxiv.org/html/2512.08683); [PMC (RSC Adv.)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
- Code: GitHub `peter-fichtelmann/odor-strength` (MIT; last push 2026-04-22). It includes the Good Scents/PubChem scrapers, cleaned Keller 2016 and Mayhew 2022 copies, PubChem odor-description/threshold CSVs and pre-trained ensemble models. It is archived at Zenodo 10.5281/zenodo.17828661 (v1.0.4, MIT, open). — [GitHub](https://github.com/peter-fichtelmann/odor-strength); [Zenodo](https://doi.org/10.5281/zenodo.17828661)
- Pyrfume ships ML benchmark files (`benchmarks.csv/.pkl`) for Keller 2012 intensity, Arshamian 2022 intensity and Wakayama 2019 curve parameters. — [pyrfume keller_2012](https://github.com/pyrfume/pyrfume-data/blob/main/keller_2012/manifest.toml); [pyrfume arshamian_2022](https://github.com/pyrfume/pyrfume-data/blob/main/arshamian_2022/manifest.toml); [pyrfume wakayama_2019](https://github.com/pyrfume/pyrfume-data/blob/main/wakayama_2019/manifest.toml)
- Earlier DREAM-based intensity modelling includes personalized intensity/pleasantness prediction (GigaScience 2018) and Sci Rep 2020, "Data based predictive models for odor perception". — [GigaScience 2018](https://academic.oup.com/gigascience/article/7/2/gix127/4750780); [Sci Rep 2020](https://www.nature.com/articles/s41598-020-73978-1)
- DREAM Olfactory Mixtures Prediction Challenge (2024, 2025; Synapse syn64743570): 26 teams predicted perceptual distances between mixtures. Infrastructure repo: Sage-Bionetworks-Challenges. — [Synapse syn64743570](https://www.synapse.org/Synapse:syn64743570); [Sage GitHub](https://github.com/Sage-Bionetworks-Challenges/olfactory-mixtures-prediction); [bioRxiv 2025](https://www.biorxiv.org/content/10.64898/2025.12.13.694160.full.pdf)
- OpenSmell/Smellability predicts odor detection thresholds (no license declared on GitHub). — [GitHub OpenSmell/Smellability](https://github.com/OpenSmell/Smellability)
- OpenPOM (MIT) replicates Lee et al. 2023. Osmo's `osmoai/publications` is Apache-2.0. — [openpom](https://github.com/ARY2260/openpom); [osmoai/publications](https://github.com/osmoai/publications)
- A Hugging Face dataset search for "odor/olfaction/odour/smell/scent" (API, 2026-09-25) returned no dataset clearly providing molecule-level intensity. Results were mostly descriptor, e-nose, vision-language or unrelated "code smell" sets. — [Hugging Face datasets search](https://huggingface.co/datasets?search=odor)

### Inferences
- A 2026 state-of-the-art potency training corpus would combine several sources:
  - Keller 2016 (continuous, CC BY)
  - Lee 2023 S3 (continuous, Apache-2.0 repo, partial structures)
  - Wakayama curves (dose-response, license unclear)
  - Fichtelmann-style ordinal labels (Good Scents, re-scraped, copyright risk)
  - Mayhew odor/odorless (CC BY-NC-ND article; repo unlicensed)
- Only Keller 2016/2012 and the Lee 2023 repo files carry clearly permissive licenses.

### Gaps
- Kaggle was not searched through its API (it needs authentication). No Kaggle intensity dataset was verified.
- Whether the GigaScience 2018 and Sci Rep 2020 papers released new intensity data (vs reusing DREAM) was not checked in full text.
