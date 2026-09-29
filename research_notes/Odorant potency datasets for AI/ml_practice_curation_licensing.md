# ML prediction of odor potency (detection threshold and intensity): models, data curation, performance ceilings, and licensing (state as of Sept 2026)

Scope note: these notes cover published ML/QSPR models for odor detection thresholds (ODT) and odor intensity/strength from 2000 to 2026, how their training data were built and cleaned, what they achieved, the noise ceiling, and the licensing status of common aroma data sources. Where a figure comes only from a search-engine snippet or an abstract, rather than full text, it is marked as such. Units: "log units" means log10 unless stated otherwise.

---

## Q1. Which papers predicted odor detection thresholds and odor intensity with ML, and what data and performance did they report?

### Takeaway
Threshold modeling has moved from small QSPR/LSER equations (Abraham 2012: 353 ODTs, R² 0.76, SD 0.82 log units) to gradient-boosted trees and GNNs on curated sets of about 700 to 1,050 compounds. The strongest well-documented 2026 result is XGBoost on 1,003 aqueous ODTs: test R² 0.83, RMSE 0.83 log units, and 87% of 177 externally measured compounds within 10-fold. Scaffold-split GNN results are much weaker. For intensity, the reference points are DREAM (population-level r = 0.78) and the Monell/Osmo-affiliated concentration-controlled dataset (r = 0.87 against a panel test–retest of r = 0.97). No foundation model (MoLFormer, ChemBERTa, POM, LLMs) has shown a clear, published advantage over descriptor-plus-tree baselines for potency.

### Cited Findings

**Threshold (ODT) models, in chronological order**
- **Abraham, Sánchez-Moreno, Cometto-Muñiz & Cain 2012 (Chem Senses 37:207–218), "An Algorithm for 353 Odor Detection Thresholds in Humans".** A single linear equation fitted to 353 ODTs in air, with R² = 0.759 and SD = 0.819 log units. Indicator variables handle the extra potency of aldehydes, acids, unsaturated esters and mercaptans. The descriptors "can be calculated from structure". — [OUP](https://academic.oup.com/chemse/article/37/3/207/325917)
- Abraham 2012 combined four datasets: Nagata (193 ODTs, Japanese triangular bag method), Cometto-Muñiz & Cain, Cometto-Muñiz & Abraham, and Hellman & Small. It put them on the "Nagata scale" and estimated the self-consistency of Nagata's data at 0.66 log units. — [OUP abstract](https://academic.oup.com/chemse/article/37/3/207/325917)
- *Uncertain (not verified in the fetched text):* the descriptor set is presumably the Abraham solvation descriptors (E, S, A, B, L). The fetched abstract does not name them.
- **Toropov et al. 2016, "Odor threshold prediction by means of the Monte Carlo method"** (Ecotoxicol Environ Saf) exists. Its metrics were not retrieved. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0147651316303013)
- **Lee et al. 2023 (Science), Principal Odor Map (POM).** The supplement reports that "a linear model atop POM outperforms a chemoinformatic SVM baseline at predicting odor detection threshold using data from Abraham et al". No numeric metric was captured. The authors state that the map "cannot predict suprathreshold intensity". — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- **Oliveira et al. 2023 (Heliyon), "A framework for predicting odor threshold values of perfumes by scientific ML and transfer learning".**
  - Data: the AIHA book *Odor Thresholds for Chemicals with Established Occupational Health Standards* (2nd ed., 295 molecules), intersected with perfumery compounds, leaving only 45 molecules. Units were ppm, and the lowest ODT was used when a compound had several values.
  - Model: a GCN trained on odor descriptors for 273 molecules, whose 128-d embeddings feed a feed-forward network.
  - Result: average MSE was 0.0179, against 0.0220 for an ECFP4 network and 0.0218 for a dummy mean regressor.
  - — [PMC10589844](https://pmc.ncbi.nlm.nih.gov/articles/PMC10589844/)
- **Application paper, PLOS ONE 2023, "Utilisation of QSPR ODT modelling and odour vector modelling to predict Cannabis sativa odour"** exists. Its metrics were not retrieved. — [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0284842)
- **Cheng et al. 2024 (Sci Total Environ), swine-slurry odorants.** QSAR models for olfactory thresholds:
  - Ridge regression: R² = 0.77, RMSE = 0.93, MAE = 0.73.
  - Random forest: R² = 0.76, RMSE = 0.97, MAE = 0.69.
  - The authors preferred these over the "commonly used" PCR/PLSR. Training-set size is not in the abstract. — [DOI](https://doi.org/10.1016/j.scitotenv.2024.170428) (abstract via Europe PMC)
- **Huang, Bu, Huang, Zhang & Zhou 2024 (Environ Sci Technol).** Described as "the first ML model to predict odor perception/threshold aiming at odorants in water". Inputs are either molecular structure or MS² spectra, and MS²-based performance is "nearly as good as" structure-based. Numeric metrics were not retrieved (the ACS page returned 403). — [ACS](https://pubs.acs.org/doi/10.1021/acs.est.4c01763) (abstract via Europe PMC)
- **Huang, Bu, Zhu & Zhou 2024 (J Hazard Mater).** A threshold model used to prioritize surface-water VOCs reports "accuracy of 79%", which implies a classification framing. — [DOI](https://doi.org/10.1016/j.jhazmat.2024.134367)
- **Hassan et al. 2025 (J Hazard Mater), VOCs from air filters.** 874 VOCs × 240 properties. Random forest reached R² = 0.786 and RMSE = 0.657 (units presumably log). It beat bagging and gradient boosting. — [DOI](https://doi.org/10.1016/j.jhazmat.2025.139637)
- **Sun, Jia & Xi (SSRN preprint, ~2025), structure- and MS²-based framework for organic and inorganic odorants.** Per the search snippet only:
  - Structure-based threshold models: test R² ≥ 0.65.
  - MS²-based threshold models: "accuracy of 0.81" (metric type unclear).
  - Descriptor models: accuracy 0.69 and 0.70.
  - Full text returned 403. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7070562)
- **Li, Luo, Yuan et al. 2025 (Metabolites 15:747).**
  - Data: 716 volatiles with water thresholds, harmonized to mg/L and modeled as −log10(mg/L). The median was taken when a compound had several values. Names were converted to canonical SMILES and deduplicated by SMILES.
  - Split: Murcko scaffold-aware greedy 80/20.
  - Result: ECFP4 + GBDT reached R² = 0.94 and RMSE = 0.44 log units. This is unusually high compared with every other report here.
  - — [PMC12654368](https://pmc.ncbi.nlm.nih.gov/articles/PMC12654368/)
- **"Safe Multitask Molecular Graph Networks for Vapor Pressure and Odor Threshold Prediction" (arXiv 2601.16426, Jan 2026).**
  - Data: 1,042 molecules with thresholds (598 air, 444 water) scraped from "government reports, handbooks, database excerpts", plus 1,852 molecules with vapor pressure from the PUFFIN open dataset.
  - Split: Bemis–Murcko scaffold split, 80/10/10, three seeds. Median max-ECFP4 Tanimoto similarity of val/test molecules to train was 0.37–0.42.
  - Result: best single-task threshold MSE on standardized targets was 0.598 ± 0.020 (PNA) against 0.612 (GINE). The safe multitask model gave 0.605.
  - Huber loss plus winsorization improved threshold MSE from 0.658 to 0.612 (GINE).
  - — [arXiv](https://arxiv.org/html/2601.16426)
- **Hou, Zhou, … Zhang & Mao 2026 (npj Science of Food, published 3 Sept 2026), "ML reveals structural determinants of ODTs and identifies high-potency food odorants".** — [DOI](https://doi.org/10.1038/s41538-026-01125-7); [PMC13558726](https://pmc.ncbi.nlm.nih.gov/articles/PMC13558726/)
  - Data: 1,003 compounds with aqueous ODTs, taken mainly from van Gemert's *Odour Thresholds* (2011) plus post-2011 literature.
  - Split: random 80/20.
  - Test-set results for nine algorithms:

    | Model | Test R² | Test RMSE (pT) |
    |---|---|---|
    | XGBoost | 0.8268 | 0.8323 (MAE 0.6394) |
    | GBDT | 0.8145 | — |
    | LightGBM | 0.8084 | — |
    | RF | 0.8076 | — |
    | SVM | 0.8053 | — |
    | CatBoost | 0.7960 | — |
    | KNN | 0.7677 (train R² 0.9987) | — |
    | MLP | 0.7166 | — |
    | AdaBoost | 0.6769 | — |

  - Cross-validation MAE was 0.6045 ± 0.0448.
  - External validation: aqueous ODTs for 177 commercially available odorants were measured in the authors' lab. 87.0% of predictions fell within 10-fold and 97.7% within 100-fold. Sensory tests on 12 model-prioritized compounds gave "preliminary prospective support".
  - The authors characterize earlier QSPR models as typically reaching "test R² around 0.6–0.7".
- **Han, Wang, Mankodi, Yang & Tewari (arXiv 2608.25893, Aug 2026).** Fine-tuned Uni-Mol2 for olfactory tasks: descriptors, odorous vs odorless, enantiomers, mixture discriminability. The fetched excerpt shows no threshold or intensity task. — [arXiv](https://arxiv.org/abs/2608.25893)

**Odorous vs odorless (a potency-adjacent binary)**
- **Mayhew et al. 2022 (PNAS).**
  - Data: 1,924 molecules (84% odorous, 16% odorless). 128 were classified by 3-AFC human testing (75 trials per molecule) and 1,796 by literature and database searches.
  - Features and result: a model using only boiling point, vapor pressure and logP "reliably classifies" molecules.
  - Prior work: a previously published neural-network classifier scored AUROC 0.626 on the cleaned data.
  - — [PMC9169660](https://pmc.ncbi.nlm.nih.gov/articles/PMC9169660/)

**Intensity and strength models**
- **Keller et al. 2017 (Science), DREAM Olfaction Prediction Challenge.** Intensity predictions correlated with observed ratings at r = 0.56 for individuals and r = 0.78 for the population. — [Science](https://www.science.org/doi/10.1126/science.aal2014); [PubMed](https://pubmed.ncbi.nlm.nih.gov/28219971/)
  - Per a search summary (not verified in full text): the DREAM data are 476 molecules rated by 49 subjects on a 0–100 scale across 21 attributes.
- **Keller & Vosshall 2016 (BMC Neurosci), the source of the DREAM data.** 480 molecules at two concentrations, 55 subjects, rated for intensity, pleasantness, familiarity and 20 descriptors. — [Springer](https://link.springer.com/article/10.1186/s12868-016-0287-2); [bioRxiv PDF](https://www.biorxiv.org/content/10.1101/049999v1.full.pdf)
  - Stimuli were liquid dilutions in paraffin oil, and 437 of the 1,000 stimuli used the same 1/1,000 dilution. Concentrations were therefore nominal liquid dilutions, not matched vapor-phase or iso-intense concentrations.
- **POI-3DGCN (Expert Systems with Applications, 2022).** A 3D graph convolutional network for the odor intensity of "monomer flavors". Metrics were not retrieved. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S095741742200416X)
- **Pellegrino, Samoilova, Ihara, Andres, Singh, Gerkin, Koulakov & Mainland (bioRxiv, Aug 2025), "A quantitative framework for predicting odor intensity across molecule and mixtures".** Gerkin lists Osmo Labs as an affiliation, and Mainland sits on Osmo's scientific advisory board. — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
  - Data: 62 odorants, each at ≥7 concentrations, delivered in Nalophan bags and rated on the gLMS by 36 panelists. Also 260 mixtures (2–10 components) with 7,623 ratings.
  - Model: a 5-layer DNN on 127 Dragon descriptors (vapor pressure, MW, MLOGP, boiling point, etc.), with a Hill-equation fit.
  - Held-out results: RMSE = 7.1 (gLMS units) and r = 0.87, against a shuffled control of RMSE 20.4.
  - Mixtures: the primacy model reached r = 0.85.
  - Real-world transfer: GC-O intensities were predicted at r = 0.62. In omission tests the DNN reached r = 0.55 against 0.45 for an OAV baseline.
- **Fichtelmann & Westermayr (arXiv 2512.08683; RSC Advances 2026, 16:25696), ordinal odor strength.** — [arXiv HTML](https://arxiv.org/html/2512.08683); [RSC](https://pubs.rsc.org/ra/article/16/28/25696/1240457/Machine-learning-for-smell-ordinal-odor-strength)
  - Data: 2,056 molecules in four classes (odorless 383, low 244, medium 1,071, high 358). Labels come from The Good Scents Company "odor strength" field (web-scraped) plus PubChem odor descriptions mapped by keywords.
  - Split: molecules with Tanimoto ≥ 0.8 were kept in the same fold.
  - Methods compared: RDKit descriptors, several fingerprints, ChemBERTa-2, ChemProp and CheMeleon, each with LR, RF, XGBoost, MLP and CORAL.
  - Best result: MLP on RDKit descriptors, with macro-MSE 0.53 ± 0.03, R² 0.57 ± 0.02 and accuracy above 60%.
- **Makri et al. (arXiv 2604.00002, Mar 2026), LLM Olfactory Perception benchmark.**
  - Task: pairwise "which smells more intense", built from Keller 2017 ratings.
  - Best result: 74.9% (Claude Opus 4.6), with Pearson r ≈ 0.55 for numeric intensity.
  - Compound names beat SMILES by about 7 points on average. The authors conclude that LLMs rely on "lexical associations rather than structural molecular reasoning".
  - — [arXiv](https://arxiv.org/html/2604.00002v1)
- **Huang & Sun (arXiv 2607.24848, Jul 2026).** A reliability-aware audit on the Keller-Vosshall and Bierling rating sets (intensity, pleasantness, familiarity). MoLFormer showed "no clear incremental predictive value" over an RDKit + Morgan baseline, and alignment between model and human perceptual geometry was weak (RSA 0.019–0.158). — [arXiv](https://arxiv.org/abs/2607.24848)

### Inferences
- **Realistic baselines for an ODT pipeline.**
  - Random split: gradient-boosted trees on RDKit/Mordred-style descriptors or ECFP. Expect test R² of about 0.75–0.83 and RMSE of about 0.8–1.0 log units on about 1,000 compounds in a single medium (Hou 2026; Cheng 2024; Hassan 2025).
  - Scaffold split: expect markedly worse results. The arXiv 2601.16426 standardized MSE of about 0.6 corresponds to explaining only about 40% of variance, if test-target variance is close to 1.
  - Treat the Li 2025 result (R² 0.94, RMSE 0.44) as an outlier to replicate before relying on it.
- **Report more than one kind of metric.** Most papers report R² on random splits, which rewards the wide dynamic range of ODTs: Nagata spans about 9 orders of magnitude. Fold-error rates ("% within 10×") and scaffold-split RMSE are more decision-relevant.
- **Foundation models are unproven for potency.** Every published potency result that compared pretrained encoders (ChemBERTa-2, MoLFormer, POM linear probe) against descriptors either showed parity or the descriptors winning, or gave no number. Descriptor-plus-GBDT is the baseline to beat.
- **Physics features are consistently the top drivers.** Size, polarity, vapor pressure and logP lead in Fichtelmann, Mayhew, Pellegrino and Hou. This suggests multitask learning with vapor pressure (arXiv 2601.16426) or explicit transport features as cheap priors.

### Gaps
- The brief names "Zhu/Chen et al." as threshold-ML authors. No paper by those authors was found. The closest matches are the Chinese-group papers above (Cheng 2024, Huang 2024, Li 2025, Hou 2026).
- Numeric ODT metrics were not retrievable for the following, because of paywalls, 403s or abstract-only access:
  - Lee 2023 POM linear probe
  - Huang 2024 EST
  - POI-3DGCN
  - Toropov 2016
  - the Cannabis QSPR paper
- The size and source of Cheng 2024's training set are not in its abstract.
- The arXiv 2601.16426 paper says "0 records had multiple aggregated references". This conflicts with its own description of log-median aggregation, so its data description should be treated with caution.

---

## Q2. What accuracy ceiling does experimental noise allow?

### Takeaway
For compiled ODTs, the label noise itself is roughly 0.5–0.8 log units.
- Nagata's repeated measurements in a single lab vary by up to about 5× (~0.7 log).
- Abraham estimated Nagata's self-consistency at 0.66 log units.
- Between laboratories, values for the same compound differ by 2–3 orders of magnitude or more.

An RMSE of about 0.6–0.8 log units on an independent test set is therefore near the practical floor, and "87% within 10×" (Hou 2026) is about as good as the data allow. Intensity data measured under controlled headspace concentration are much cleaner: panel test–retest r ≈ 0.86–0.97, against about 0.65–0.81 for jar or earlier setups.

### Cited Findings
- **Nagata (Japan Environmental Sanitation Center).** 223 substances measured 1976–1988 with the triangle odor bag method by a 6-member trained panel. Thresholds were reported in ppm v/v and ranged from 0.77 ppt (isoamyl mercaptan) to 1,500 ppm (propane). For a substance measured repeatedly, the ratio of highest to lowest threshold "was about 5 at the maximum". — [MoE PDF](https://www.env.go.jp/en/air/odor/measure/02_3_2.pdf)
- Nagata also reports that thresholds can differ by about 10,000× between functional-group isomers and by more than 100× between positional isomers. — [MoE PDF](https://www.env.go.jp/en/air/odor/measure/02_3_2.pdf)
- **Abraham 2012.** Nagata self-consistency was 0.66 log units, and the SD of the combined 353-compound fit was 0.819 log units. — [OUP](https://academic.oup.com/chemse/article/37/3/207/325917)
- **Yang et al. 2026 review (Compr Rev Food Sci Food Saf).** — [PMC13420774](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)
  - Early measurements from different labs vary by "up to two to three orders of magnitude".
  - Method changes alone shift values: for butyric acid, 3-AFC gave 2,741 µg/L and TST gave 5,592 µg/L. For ethyl acetate, the Feller model gave 4,666 µg/L and BET gave 2,845 µg/L.
  - Panel type matters: for 2-phenylethanol, experts measured 871 µg/L and consumers 2,042 µg/L (p < 0.01).
- **n-butanol.** Reported air ODTs from 44 studies published 1892–2010 range from 0.01 to 162 mg/m³, about 4.2 orders of magnitude. The same summary says modern dynamic-dilution olfactometry narrows this to about 1–2 orders. — [ScienceDirect (Indoor air quality overview)](https://www.sciencedirect.com/science/article/abs/pii/S1569904823000964) (per search summary; full text not accessed)
- A 2025 Building & Environment variability analysis reportedly finds Western populations have thresholds "2.15-order higher" than Asian populations. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0360132325006031) (search-summary only; attribution and exact meaning unverified)
- **Recognition vs detection.** Odor recognition thresholds can exceed ODTs by "up to two orders of magnitude for certain compounds". — [Hou 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13558726/)
- **Impurities.**
  - Mayhew 2022 ran GC-MS and GC-O on 111 stimuli judged odorous. "22% of molecules classified as odorous were actually odorless compounds contaminated with odorous compounds, despite high nominal purity ratings from vendors". Because ODTs span many orders of magnitude, "even high purity (e.g., 99%) is insufficient". — [PMC9169660](https://pmc.ncbi.nlm.nih.gov/articles/PMC9169660/)
  - Paoli et al. 2017 (eNeuro) found that a 0.0006% impurity explained the full response of one receptor cell type. — [eNeuro](https://www.eneuro.org/content/4/3/ENEURO.0070-17.2017) (per search summary)
  - Keller & Vosshall 2016 stimuli were >97% pure (median 98%). The authors flag that "3% impurity can have an impact on the percept". — [bioRxiv PDF](https://www.biorxiv.org/content/10.1101/049999v1.full.pdf)
- **Chirality.** — search summaries; primary texts not fetched
  - The (+)/(−) α-ionone threshold ratio varied over 4 orders of magnitude across 63 subjects. — [PubMed 2914071](https://pubmed.ncbi.nlm.nih.gov/2914071/)
  - (R)- and (S)-2-pentanol thresholds were 163.30 and 78.58 mg/L in 46% ethanol. — [PMC9455680](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9455680/)
  - Geosmin: about 9.5 ppt for (−) against 78 ppt for (+). — [Wikipedia](https://en.wikipedia.org/wiki/Odor_detection_threshold)
- **Intensity reliability.**
  - Pellegrino 2025: panel test–retest r = 0.97, RMSE 3.0–3.62 (gLMS). Earlier work cited there reached r = 0.65–0.77. — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
  - Andres, Pellegrino et al. 2026 (Chem Senses): Nalophan bags gave test–retest r = 0.89 against 0.81 for glass jars (experiment 1), and 0.86 against 0.72 (experiment 2). — [DOI](https://doi.org/10.1093/chemse/bjag022)
  - POM (Lee 2023): panel-mean test–retest R = 0.80 for odor-descriptor ratings. — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
  - Huang & Sun 2026: agreement between human datasets on shared molecules was RSA 0.331 (95% CI 0.204–0.507), against within-dataset split-half values of 0.743 and 0.855. — [arXiv](https://arxiv.org/abs/2607.24848)
- **n-butanol panel calibration.** EN 13725 panels are screened on n-butanol, but assessor sensitivity to n-butanol "is not transferable to other odorants". — [Atmos Environ 2024](https://www.sciencedirect.com/science/article/pii/S1352231024001845); [Environ Sci Eur 2025](https://enveurope.springeropen.com/articles/10.1186/s12302-025-01179-6) (per search summary)

### Inferences
- **ODT ceiling.** If a consensus label carries about 0.5–0.7 log units of irreducible error from single-lab reproducibility, and inter-lab spread adds more, then scaffold-split RMSE below about 0.7 log units is suspicious. Check it for leakage: duplicates across stereoisomers or salts, or the same compound appearing in both air and water.
- **Report a label-noise-aware metric.** Examples are the fraction within 10× (1 log unit) and within 3× (0.5 log unit) of the consensus label. Also compare the model against the per-compound spread across sources: the SD of log values, as Hou records.
- **Intensity ceiling.** For intensity at a controlled concentration, a population-level r of about 0.85–0.9 is near the ceiling in the Pellegrino setup. For DREAM-style jar and paraffin-oil data the ceiling is lower, because concentrations are uncontrolled and reliability is lower.

### Gaps
- No published "noise-ceiling-normalized" ODT benchmark was found: that is, no model error compared with inter-lab variance on the same compounds.
- Devos et al. 1990 (*Standardized Human Olfactory Thresholds*, OUP) reportedly used weighting and averaging over more than 500 chemicals. Its exact standardization math (e.g., n-butanol-anchored correction) could not be verified online. — [OUP catalog](https://global.oup.com/academic/product/standardized-human-olfactory-thresholds-9780199631469)
- The exact EN 13725 reference values (the commonly quoted 123 µg/m³ n-butanol reference) were not verified in a fetched source.

---

## Q3. What concrete harmonization recipe is recommended (steps and tools)?

### Takeaway
Recent papers converge on one recipe:
1. Pick one endpoint and matrix: detection, not recognition, in air or water.
2. Resolve identifiers (CAS or name) through PubChem.
3. Standardize with RDKit.
4. Deduplicate by structure.
5. Convert to a single molar or mass unit and take logs.
6. Drop outliers relative to the modal order of magnitude.
7. Aggregate with the geometric mean or log-median, keeping spread metadata.
8. Split by scaffold or similarity cluster.

The biggest unresolved choices are:
- whether to keep stereoisomers as separate entities (InChIKey-14 dedup collapses them);
- whether to convert water thresholds to air, which is not recommended.

### Cited Findings
- **Hou 2026 curation (the most explicit recipe):** — [PMC13558726](https://pmc.ncbi.nlm.nih.gov/articles/PMC13558726/)
  1. Keep only ODTs measured in water or aqueous solution.
  2. Exclude recognition thresholds, air, oil and other matrices, ambiguous endpoints, mixtures, metal salts, and undefined structures.
  3. Retrieve canonical SMILES from PubChem, standardize them with RDKit, and merge duplicates by canonical SMILES.
  4. Convert all values to mg/L.
  5. Build a histogram of log10 magnitudes and keep "the most frequent order-of-magnitude bin and its two neighboring bins". Values far outside are "inconsistent reports".
  6. Take the geometric mean of retained values, and record n, min, max and SD of log10 values.
  7. Model target: pT = −log10(T × 10⁻³).
- **arXiv 2601.16426 curation:** — [arXiv](https://arxiv.org/html/2601.16426)
  - Units: ppb/ppm, mg/m³, µg/L and ng/L were converted to log concentrations "with density and molar-mass conversions".
  - Aggregation: log-space median per (molecule, medium), with IQR kept as uncertainty.
  - Outliers: winsorized at the 2–2.5% quantiles per medium, computed on the training fold only.
  - Structures: CAS→SMILES mapping; RDKit sanitize and canonicalize; dedup by the 14-character InChIKey skeleton; salts and solvents stripped; any record whose SMILES round-trip changed heavy-atom topology was dropped.
  - Split: all endpoints of one molecule go in the same fold. Report the maximum ECFP4 similarity of test molecules to train.
  - Modeling: Huber loss (δ ≈ 1.5) with optional uncertainty weighting.
- **Li 2025:** median of multiple values; water thresholds converted to mg/L; names converted to canonical SMILES and deduplicated; Murcko scaffold-aware split. — [PMC12654368](https://pmc.ncbi.nlm.nih.gov/articles/PMC12654368/)
- **Oliveira 2023 (contrasting choice):** takes the lowest reported ODT per compound, which the authors describe as the safest known value. This is a conservative, biased aggregator suited to safety use, not to central-tendency modeling. — [PMC10589844](https://pmc.ncbi.nlm.nih.gov/articles/PMC10589844/)
- **EPA 1992 Reference Guide (EPA/600/R-92/047):** published odor thresholds were "critically evaluated" against quality criteria, and "values of acceptable quality" were used to compute a geometric mean or best estimate. — [EPA Science Inventory](https://cfpub.epa.gov/si/si_public_record_report.cfm?Lab=NCEA&dirEntryId=40610)
- **Nagata:** thresholds were computed as the primary-sample concentration divided by the odor concentration (dilution factor at threshold), in ppm v/v. For odorants measured repeatedly, the geometric mean was used. Amines, fatty acids, skatole and indole were corrected for low bag recovery rates (e.g., indole 6.5%, skatole 13%). — [MoE PDF](https://www.env.go.jp/en/air/odor/measure/02_3_2.pdf)
- **Unit conversion (gases, 25 °C, 1 atm):** mg/m³ = ppm(v/v) × MW / 24.45. 24.45 L/mol is the molar volume at those conditions. — [Breeze Technologies](https://www.breeze-technologies.de/blog/air-pollution-how-to-convert-between-mgm3-%C2%B5gm3-ppm-ppb/); [AIHA calculator](https://www.aiha.org/ih-calculator-app/calcs/conversion-concentration.html)
- **Standards and matrices (Yang 2026):** — [PMC13420774](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)
  - Standards: ISO 13301:2018 (3-AFC), ASTM E679-19 (keeps the detection/recognition distinction), and GB/T 22366-2022.
  - Recommendation: prioritize studies with standardized procedures and transparent statistics, and treat detection and recognition separately.
  - Matrix effects are non-monotonic (e.g., esters in 9–12% ethanol).
  - Nasal and retronasal thresholds correlate at r = 0.932 across 50 compounds.
- **RDKit rdMolStandardize:** `Cleanup` runs RemoveHs, SanitizeMol, MetalDisconnector, Normalizer, Reionizer and AssignStereochemistry, equivalent to MolVS `standardize`. The module also provides `LargestFragmentChooser`, `Uncharger` and `TautomerEnumerator.canonicalize`. — [RDKit docs](https://www.rdkit.org/docs/source/rdkit.Chem.MolStandardize.rdMolStandardize.html)
- **PubChem PUG REST:** URL = prolog `https://pubchem.ncbi.nlm.nih.gov/rest/pug` + input + operation + output format. Isomeric SMILES containing "/" should be sent by POST or as a URL parameter. — [PUG REST docs](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest)
  - Tested live on 2026-09-25: a CAS number resolves through the `name` namespace, and the current property names are `SMILES` (isomeric) and `ConnectivitySMILES`. The call `/compound/name/78-93-3/property/SMILES,ConnectivitySMILES,InChIKey/JSON` returned CID 6569 and `CCC(=O)C`. — [live query](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/78-93-3/property/SMILES,ConnectivitySMILES,InChIKey/JSON)
- **Odor strength (Fichtelmann):**
  - Standardization: RDKit canonicalization, removal of duplicates and invalid SMILES, and splitting of disconnected fragments "when appropriate".
  - Leakage control: molecules with Tanimoto ≥ 0.8 go in the same CV fold.
  - Label harmonization: keyword mapping of PubChem text into classes ("very faint"→odorless, "faint/weak"→low, "very strong"→high), and "very high" merged into high.
  - — [arXiv HTML](https://arxiv.org/html/2512.08683)
- **Label QC (Mayhew):**
  - Molecules with ambiguous labels ("practically odorless") or labels that disagreed across sources were discarded.
  - Experimental boiling point and vapor pressure values were preferred over estimates. Estimated boiling points have a median absolute error of about 55 °C with the Burnop method.
  - GC-MS/GC-O quality control was run on the psychophysics stimuli.
  - — [PMC9169660](https://pmc.ncbi.nlm.nih.gov/articles/PMC9169660/)
- **Scale of the harmonization problem:** Yang 2026 compiled 848 compounds across 11 matrices from 146 publications (1952–2024). 712 had air or water values, 299 ethanol–water, 143 oil. — [PMC13420774](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)

### Inferences
Recommended pipeline, synthesized from the above. It is not taken from any single paper.
1. **Record-level schema.** Keep every raw observation, never only the aggregate. Fields: source ID, year, compound name, CAS, matrix (air / water / ethanol-water / oil), endpoint (detection / recognition / unknown), method (3-AFC, triangle bag, dynamic olfactometer, ASTM E679, EN 13725), panel size and type, raw value and unit, and flags for purity or chirality if known.
2. **Identifier resolution.** Use CAS first, through the PUG REST `name` namespace, falling back to the name. Store CID, isomeric SMILES and the full InChIKey. Flag any name that maps to several CIDs.
3. **Structure standardization.** Run RDKit `Cleanup` → `LargestFragmentChooser` (strip salts and counter-ions) → `Uncharger` → optionally a canonical tautomer. Keep two keys:
   - the full InChIKey, which preserves stereo;
   - the InChIKey-14 skeleton, for leakage-safe grouping.
   Aggregate by the full key, but split by the skeleton so that enantiomers and E/Z isomers never straddle train and test.
4. **Units.**
   - Air: convert to log10(mol/m³), or mg/m³ via MW/24.45 at 25 °C.
   - Water: convert to log10(mol/L).
   - Do not merge matrices into one target. Use separate heads or a matrix covariate.
   - Converting water ODTs to the gas phase with Henry's-law constants is physically motivated but unvalidated as a label transform. Use it as a feature or in multitask training, not as a replacement label. This recommendation is inferred and has no source.
5. **Within-compound aggregation.** Apply a Hou-style modal-bin filter, or a MAD filter in log space. Then take the geometric mean or log-median, and store n, SD and range as per-label uncertainty for weighted or Huber losses.
6. **Endpoint hygiene.** Drop recognition thresholds and "unknown" endpoints from the primary target, or model them as a separate task: they can be up to about 100× higher.
7. **Splits.** Report both random and scaffold or similarity-cluster splits, with all matrices of one molecule in the same fold. Add a small, externally measured prospective set where possible, as Hou did with 177 compounds.

### Gaps
- No paper has published a validated algorithm for combining Devos-standardized, Nagata and van Gemert values on a common scale, beyond Abraham's "Nagata scale" rescaling (details not retrieved).
- No source was found that quantifies how often CAS→PubChem resolution returns the wrong stereoisomer or a mixture record for aroma chemicals.

---

## Q4. Which datasets are safe for commercial model training, and which are research-only?

### Takeaway
The perfumery-descriptor sources that dominate olfaction ML (Good Scents, Leffingwell, and the pyrfume bundles built from them) are research-only or permission-required.
- Leffingwell is CC BY-NC.
- The Good Scents Company says "permission to reproduce is required".

Commercially usable threshold data do exist but are small:
- PubChem/HSDB (public domain);
- the US EPA 1992 odor-threshold guide (a US government work);
- Nagata's 223 thresholds, hosted by Japan's Ministry of the Environment (MoE site content is under PDL1.0, which permits commercial use and is CC BY 4.0-compatible; verify that it covers this third-party-authored PDF);
- original measurements.

The largest recent curated ODT set (Hou 2026, 1,003 compounds) sits in an MIT-licensed repo but was built mainly from van Gemert's copyrighted compilation, so its commercial status is doubtful. In the EU, database rights and the TDM opt-out add risk for commercial extraction.

### Cited Findings
- **The Good Scents Company.** The company "retains all exclusive copyrights". Its content is "protected under the U.S. and Foreign Copyright Laws", and "permission to reproduce is required". — [TGSC copyright page](http://www.thegoodscentscompany.com/misc/copyrigh.html)
  - Fichtelmann & Westermayr did not redistribute Good Scents data because it is copyright-protected. They released scraping code instead. — [arXiv HTML](https://arxiv.org/html/2512.08683)
- **Leffingwell (3,523 molecules, from the PMP 2001 database).** The Sanchez-Lengeling et al. release is "freely available for research use under the CC-BY-NC license". — [Zenodo 4085098](https://zenodo.org/records/4085098); readme in [pyrfume-data/leffingwell](https://github.com/pyrfume/pyrfume-data/tree/main/leffingwell)
  - The pyrfume manifest says: "Licensing information and use restrictions according to the terms of John Leffingwell and Google". — [manifest](https://github.com/pyrfume/pyrfume-data/blob/main/leffingwell/manifest.toml)
- **How pyrfume handles licenses.**
  - The pyrfume README says: "Data is provided as-is. Licensing information for individual datasets is available in the data repository. Takedown requests for datasets may be directed to admin at pyrfume dot org." — [pyrfume GitHub](https://github.com/pyrfume/pyrfume)
  - The pyrfume-data repo carries an MIT license at repo level (GitHub API, checked 2026-09-25). Individual manifests override it:
    - Goodscents: "use restrictions according to the terms of The Goodscents Company; Pyrfume developers make no claims concerning copyright". The data is a Contrebande Labs scrape dated Jan 17, 2022.
    - The `LICENSE` file that the Goodscents manifest refers to was absent from the folder listing on 2026-09-25.
    - Arctander 1960, digitized by the Mainland lab, says "see LICENSE for use restrictions".
    - Flavornet is marked "© Datu Inc., 2004".
    - Sigma 2014 is "Produced by the Sigma-Aldrich company".
    - — [pyrfume-data](https://github.com/pyrfume/pyrfume-data); [goodscents manifest](https://github.com/pyrfume/pyrfume-data/blob/main/goodscents/manifest.toml)
  - The pyrfume Scientific Data paper says the repository is "intended for non-commercial purposes under FAIR use principles, except where licenses permit commercial use". The article itself is CC BY-NC-ND 4.0. — [PMC11557823](https://pmc.ncbi.nlm.nih.gov/articles/PMC11557823/)
- **OpenPOM.** The code is MIT-licensed. The model is trained on a 4,983-molecule, 138-descriptor dataset merged from GoodScents and Leffingwell PMP 2001. — [BioMachineLearning/openpom](https://github.com/BioMachineLearning/openpom)
- **POM (Lee 2023).**
  - "The code implementing and training the GNN model is not available to share."
  - About 45% of validation-study structures could not be shared under legal agreements, and odorant identities were to be "released pending legal review".
  - — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- **FlavorDB.** Described as distributed under CC BY-NC (non-commercial reuse, with commercial reuse needing permission). FlavorDB2 (2024) is "freely accessible for non-commercial use". — [search summary citing NAR 2018](https://academic.oup.com/nar/article/46/D1/D1210/4559748); [FlavorDB2](https://ift.onlinelibrary.wiley.com/doi/10.1111/1750-3841.17298)
  - Unverified: the CC BY-NC statement may refer to the NAR article rather than to separate database terms.
- **PubChem and HSDB.** HSDB is listed as public domain on data.gov. HSDB content has been folded into PubChem, whose records carry odor and odor-threshold annotations. — [data.gov HSDB](https://catalog.data.gov/dataset/hazardous-substances-data-bank-hsdb-28053); [PubChem HSDB source](https://pubchem.ncbi.nlm.nih.gov/source/hsdb)
  - PubChem data are generally described as public domain and usable commercially. — [Wikipedia](https://en.wikipedia.org/wiki/PubChem) (secondary source)
- **EPA 1992 Reference Guide to Odor Thresholds for Hazardous Air Pollutants (EPA/600/R-92/047).** — [EPA](https://cfpub.epa.gov/si/si_public_record_report.cfm?Lab=NCEA&dirEntryId=40610)
- **Nagata / Japan MoE.**
  - The Nagata threshold paper is hosted on the MoE English site. — [MoE PDF](https://www.env.go.jp/en/air/odor/measure/02_3_2.pdf)
  - MoE website content is under the Public Data License 1.0 (PDL1.0). It requires the attribution "Source: Ministry of the Environment website (URL)", plus an edit statement if content is modified. — [MoE copyright](https://www.env.go.jp/en/utility/copyright.html)
  - PDL1.0 permits commercial use and is compatible with CC BY 4.0. — [Digital Agency PDL1.0](https://www.digital.go.jp/en/resources/open_data/public_data_license_v1.0)
- **Mayhew 2022 (Monell).** "There are no restrictions on the availability of these data" (1,924 odor classifications plus physicochemical features). The repo is Apache-2.0 (LICENSE file read 2026-09-25). The article is CC BY-NC-ND. Dragon-computed features for 107k GDB-17 molecules were withheld because of Dragon's terms of service. — [PMC9169660](https://pmc.ncbi.nlm.nih.gov/articles/PMC9169660/); [OlfactorySpace](https://github.com/emayhew/OlfactorySpace)
- **Keller & Vosshall 2016 (the DREAM source data).** The bioRxiv preprint is under CC-BY-NC 4.0 (stated in the PDF footer). The license of the BMC Neuroscience version and its supplementary data was not verified. — [bioRxiv PDF](https://www.biorxiv.org/content/10.1101/049999v1.full.pdf); [BMC](https://link.springer.com/article/10.1186/s12868-016-0287-2)
- **DREAM Olfaction Prediction Challenge on Synapse (syn2811262).** The Synapse REST API returned zero access requirements for the project on 2026-09-25. No license statement was retrievable, because the page is JavaScript-rendered. — [Synapse](https://www.synapse.org/Synapse:syn2811262); [API](https://repo-prod.prod.sagebase.org/repo/v1/entity/syn2811262/accessRequirement)
- **van Gemert, *Odour Thresholds: compilations of odour threshold values in air, water and other media* (Oliemans Punter & Partners, 2011).** A commercially published compilation. — [Google Books](https://books.google.com/books/about/Odour_thresholds_compilations_of_odour_t.html?id=ZfC6twAACAAJ)
  - Hou 2026 used it as the "primary data source" and published the curated 1,003-compound dataset in a GitHub repo licensed MIT (GitHub API). The article is CC BY-NC-ND 4.0. — [PMC13558726](https://pmc.ncbi.nlm.nih.gov/articles/PMC13558726/); [Hvard24/odt-prediction-ml](https://github.com/Hvard24/odt-prediction-ml)
- **arXiv 2601.16426:** "raw pages not redistributed where licenses unclear". Only numeric targets are released, with scripts to re-download from the original URLs where permitted. — [arXiv](https://arxiv.org/html/2601.16426)
- **EU database right (Directive 96/9/EC).**
  - Protects databases that required "a substantial investment in obtaining, verifying or presenting the contents", regardless of originality.
  - Lasts 15 years, and a substantial modification creates a new term.
  - Restricts extraction or re-use of all or a substantial part, including repeated extraction of insubstantial parts. Lawful users may extract insubstantial parts.
  - The US has no equivalent right (Feist: originality is required).
  - Post-Brexit, UK and EU rights created after 2020 are recognized only in the creator's jurisdiction.
  - — [Wikipedia: Database right](https://en.wikipedia.org/wiki/Database_right)
- **EU text-and-data-mining exceptions (DSM Directive 2019/790).** — [Kluwer Copyright Blog](https://legalblogs.wolterskluwer.com/copyright-blog/the-new-copyright-directive-text-and-data-mining-articles-3-and-4/)
  - Art. 3 covers reproduction and extraction for TDM by research organizations and cultural-heritage institutions for scientific research. It covers the database right, and contracts cannot override it.
  - Art. 4 covers TDM by anyone for any purpose, commercial included. Rightholders can opt out "in an appropriate manner, such as machine-readable means" for online content.
  - The AI Act (Reg. 2024/1689) requires general-purpose AI model providers to respect Art. 4(3) opt-outs. — [JIPLP](https://academic.oup.com/jiplp/article/19/5/453/7614898) (per search summary)

### Inferences
Not legal advice. Classification for training a commercial potency model:

| Class | Sources |
|---|---|
| **Likely commercial-OK** | PubChem/HSDB odor-threshold annotations (public domain); EPA 1992 guide (US federal work, generally public domain under 17 U.S.C. §105; not verified on the document itself); Nagata 223 (if PDL1.0 applies); Mayhew 2022 labels (Apache-2.0, "no restrictions"; many labels came from scraped databases, so check provenance for sensitive uses); your own measurements; thresholds re-extracted from primary papers as individual facts. |
| **Research-only / NC** | Leffingwell (CC BY-NC); FlavorDB (NC); pyrfume bundles unless the dataset-specific license allows otherwise; Keller 2016 preprint data (CC BY-NC) unless the BMC supplement is more permissive; POM-derived artifacts trained on GS-LF. |
| **Permission-required / high risk** | Good Scents (explicit reservation, and scraping likely breaches ToS); van Gemert, AIHA and Devos compilations (commercial books); derivative datasets built mainly from them (Hou 2026) despite MIT repo labels, because an MIT label on a repo does not relicense upstream data. |

Further implications:
- **US.** Individual threshold numbers are facts. What matters is selection and arrangement (thin compilation copyright) and contract or ToS terms. Extracting individual values from primary literature, rather than copying a compilation wholesale, is the lower-risk route.
- **EU/UK.** Extracting a substantial part of van Gemert or TGSC could implicate the database right. Art. 3 TDM protects only research organizations. Commercial actors rely on Art. 4, which is defeated by an opt-out; TGSC's reservation of rights may count as one.
- **Model weights.** Whether weights trained on NC data are themselves NC is unresolved. Conservative practice keeps NC-trained checkpoints out of commercial products.

### Gaps
- The DREAM/Synapse data license and the BMC supplement license for Keller 2016 could not be verified.
- The terms behind the Leffingwell website (leffingwell.com threshold tables) were not checked.
- Whether PDL1.0 covers the Nagata paper (authored by the Japan Environmental Sanitation Center, hosted by MoE) is uncertain.
- The PubChem depositor-level license exceptions for odor-threshold sections were not checked.
- The GitHub Goodscents manifest refers to a LICENSE file that does not exist in the folder, so the actual Goodscents terms applied by pyrfume are unclear.
- No machine-readable TDM opt-out (robots.txt, TDMRep) was checked for thegoodscentscompany.com.

---

## Q5. Did Osmo or Google release any potency or intensity data or models?

### Takeaway
No released Osmo or Google threshold or intensity dataset or model was found as of Sept 2026.
- The 2023 POM paper withheld GNN code and weights. It showed only a linear-probe advantage on the Abraham ODT data, and it explicitly cannot predict suprathreshold intensity.
- The closest thing is the Monell/CSHL intensity work with an Osmo-affiliated co-author (Pellegrino et al. 2025 bioRxiv; Andres et al. 2026 Chem Senses). It reports a controlled-concentration intensity dataset, but no explicit open-data license or repository was found.

### Cited Findings
- **POM data release.** POM deposited "human psychophysics data, model predictions, and model embeddings for tested odorants" to pyrfume. The GNN code and weights are "not available to share". POM + linear model beat an SVM on the Abraham ODT data, but the map "cannot predict suprathreshold intensity". — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- **Osmo's 2023 announcement.** Osmo publicized POM as a Google Research spin-out result trained on about 5,000 molecules. — [PR Newswire](https://www.prnewswire.com/news-releases/digital-olfaction-startup-osmo-introduces-scent-to-the-world-of-artificial-intelligence-in-breakthrough-science-paper-301915197.html)
- **POM limitations per Contrary Research.** An analyst report lists the earlier model's limitations, including enantiomers and non-linearities "such as scent intensity" across concentration. — [Contrary Research](https://research.contrary.com/company/osmo)
- **Pellegrino et al. 2025 (bioRxiv).**
  - Authorship: Gerkin lists an Osmo Labs, PBC affiliation, and Mainland is on Osmo's SAB.
  - Data: 62 odorants × ≥7 concentrations and 260 mixtures, in Nalophan bags.
  - The fetched text gives no explicit open-data repository or license; it refers only to "data analysis files ... in the Supplementary Materials".
  - — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/); [bioRxiv DOI](https://doi.org/10.1101/2025.08.08.668954)
- **Andres, Pellegrino, Song, Ocampos & Mainland 2026 (Chem Senses).** Describes the bag delivery method and its reliability (r = 0.86–0.89 for bags against 0.72–0.81 for jars). — [DOI](https://doi.org/10.1093/chemse/bjag022)
- **OpenPOM (community).** An MIT-licensed replication of the descriptor model only; it has no potency head. — [GitHub](https://github.com/BioMachineLearning/openpom)
- **Other 2025–2026 academic potency releases:**
  - Hou 2026: 1,003 aqueous ODTs on GitHub, provenance caveats in Q4. — [GitHub](https://github.com/Hvard24/odt-prediction-ml)
  - Fichtelmann 2026: PubChem part plus code on Zenodo, with Good Scents to be re-scraped by the user. — [arXiv](https://arxiv.org/html/2512.08683)
  - arXiv 2601.16426: numeric targets only. — [arXiv](https://arxiv.org/html/2601.16426)

### Inferences
- A practitioner cannot currently fine-tune an official POM for potency. Options are:
  - OpenPOM embeddings, which carry GS-LF license contamination risk;
  - a model pretrained on public-domain structures, such as ChemBERTa or MoLFormer-style models pretrained on PubChem/ZINC;
  - descriptor baselines.
- The Monell bag protocol together with the Pellegrino design (7-point concentration series, gLMS, Hill fit) is the best available template for generating new, license-clean intensity data.

### Gaps
- No Osmo or Google blog post, dataset card, or Hugging Face release covering threshold or intensity was found in searches up to Sept 2026. Absence in search results is not proof of absence.
- It is unknown whether the Pellegrino 2025 raw intensity data have since been deposited (e.g., in pyrfume) and under what license.

---

## Q6. (Objective item 4) What data are missing, and where are the opportunities?

### Takeaway
The field is data-limited, not model-limited.
- Only about 1,800 compounds have experimental thresholds at all.
- The largest open curated sets hold about 1,000 compounds, each limited to a single medium.
- Almost no intensity data exist at matched or controlled vapor concentrations beyond about 60 odorants.
- Purity- and chirality-controlled measurements are rare.

### Cited Findings
- **Thresholds are scarce.** "Only around 1800 compounds have experimentally determined odor threshold values" (citing van Gemert), against more than 500,000 odor-active molecules reported. — [Hou 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13558726/)
- **Current open or curated set sizes:**

  | Set | Size / medium | Source |
  |---|---|---|
  | Hou 2026 | 1,003 aqueous | [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13558726/) |
  | arXiv 2601.16426 | 1,042 (598 air, 444 water) | [arXiv](https://arxiv.org/html/2601.16426) |
  | Hassan 2025 | 874 VOCs | [DOI](https://doi.org/10.1016/j.jhazmat.2025.139637) |
  | Yang 2026 | 848 compounds across 11 matrices | [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/) |
  | Li 2025 | 716 water | [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12654368/) |
  | Abraham 2012 | 353 air | [OUP](https://academic.oup.com/chemse/article/37/3/207/325917) |
  | Nagata | 223, single lab, one method | [MoE](https://www.env.go.jp/en/air/odor/measure/02_3_2.pdf) |

- **Intensity at controlled concentration.**
  - Keller 2016 used nominal liquid dilutions in paraffin oil, mostly 1/1,000. — [bioRxiv](https://www.biorxiv.org/content/10.1101/049999v1.full.pdf)
  - Pellegrino 2025 controlled headspace concentration but covers only 62 odorants. — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- **Stereochemistry.** Hou's model "does not explicitly capture stereochemistry". — [PMC13558726](https://pmc.ncbi.nlm.nih.gov/articles/PMC13558726/)
- **Purity.** Odorous-label contamination affected 22% of molecules in the Mayhew QC set. — [PMC9169660](https://pmc.ncbi.nlm.nih.gov/articles/PMC9169660/)
- **Matrix and method heterogeneity** is documented, with calls for standardized protocols (ISO 13301, ASTM E679). — [PMC13420774](https://pmc.ncbi.nlm.nih.gov/articles/PMC13420774/)
- **Emerging modalities.**
  - MS²-spectrum-based threshold prediction for unidentified compounds. — [Huang 2024 EST](https://pubs.acs.org/doi/10.1021/acs.est.4c01763); [Sun SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7070562)
  - Vapor-pressure multitask learning. — [arXiv 2601.16426](https://arxiv.org/html/2601.16426)

### Inferences
Highest-value data opportunities:
1. A license-clean, public-domain-seeded threshold core, built by merging PubChem/HSDB, EPA 1992 and Nagata and adding values re-extracted from primary papers with full provenance.
2. Iso-concentration or dose–response intensity panels using Nalophan bags and a gLMS, with GC-O purity QC, on a chemically diverse and scaffold-balanced set of a few hundred odorants.
3. Enantiomer-pair threshold measurements, to give 3D or chiral-aware models a real target.
4. Per-compound inter-source variance, released alongside the labels so that noise-aware losses and noise-ceiling benchmarking become possible.

A shared scaffold-split benchmark (analogous to the MoleculeNet or TDC style) for air and water ODTs does not appear to exist. Creating one is a clear community gap.

### Gaps
- No announced 2024–2026 initiative was found (Osmo, Google, Monell, OpenPOM, or AI-olfaction startups) that commits to releasing a large, openly licensed threshold dataset.
- No benchmark leaderboard for ODT regression was found.
