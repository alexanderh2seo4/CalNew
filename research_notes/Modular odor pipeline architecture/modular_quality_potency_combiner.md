# Modular odor-prediction pipelines: quality model (A) + potency model (B) + combiner (C)

Scope: existing modular/multi-stage designs, the science of how quality and intensity combine, ML design patterns (modular vs end-to-end/multitask), and evaluation. Current as of 2026-09-27. Items marked [UNVERIFIED] come from search snippets only or from memory without a fetched primary source.

## 1. Existing modular or pipeline olfaction models

### Takeaway
The leading 2025–2026 work is already modular. Pellegrino/Mainland (2025) use a single-molecule network whose outputs are Hill-curve parameters, followed by a separate mixture combination rule ("Primacy"). POMMix stacks a pretrained POM GNN, an attention aggregator and a cosine head. The DREAM 2025 winners paired pretrained per-molecule embeddings with a pooling step and gradient boosting. The July 2026 Monell/Osmo paper finds that mixture *quality* is close to an unweighted average of component descriptor vectors. None of these systems joins a quality model and a potency model into one concentration-aware "perceived profile" output. That joint model is the open gap the proposed A/B/C pipeline would fill.

### Cited Findings
**Pellegrino et al. 2025, intensity framework (bioRxiv 10.1101/2025.08.08.668954; Pellegrino, Samoilova, Ihara, Andres, Singh, Gerkin, Koulakov, Mainland)**
- Single-molecule stage: a 5-layer DNN takes 127 physicochemical descriptors plus log concentration and predicts the Hill parameters Imax, EC50 and n, with I = Imax·C^n/(C^n+EC50^n). Cross-validated RMSE = 7.1, r = 0.87, against a shuffled control at RMSE 20.4. A reduced 10-feature model (vapor pressure, alpha-area and others) scores RMSE 7.2, r = 0.87 — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- Transport and volatility descriptors (MW, vapor pressure, boiling point, MLOGP) carry much of the signal. Stimuli were gas-phase concentrations delivered in gas-sampling bags: 62 molecules × ≥7 concentrations = 434 points. Panel reliability r = 0.97 — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- Mixture stage: the paper compared these combination rules: linear addition, strongest component, Euclidean, vector, U-model, competitive binding, and a new "Primacy" model. Primacy computes a weighted average of component intensities evaluated at about 20% of ambient concentration, on the assumption that intensity is fixed early in the sniff. It was best, at r(258) = 0.85 and RMSE 8.6 on 260 mixtures (binary up to 10 components; 7,623 ratings; panel r = 0.97) — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- End-to-end alternative: one DNN trained jointly on single molecules and mixtures reached RMSE 7.5 on mixtures (shuffled control 15.8) — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/). The modular Primacy rule (RMSE 8.6) and the direct DNN (RMSE 7.5) are therefore reported side by side. The fetched summary does not say whether the evaluation splits were identical, so the gap should not be treated as a clean head-to-head.
- Use case versus OAV: the intensity models predicted omission-test outcomes (which components matter in a natural aroma) better than OAV. Single-molecule model r(65) = 0.45; DNN mixture model r(65) = 0.55. At OAV = 100, odorants span a wide range of intensities — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)

**Pellegrino et al. 2026, "Odors Smell Like Their Components: A Linear Framework…" (bioRxiv, 8 Jul 2026; Pellegrino, Mayhew, Margolis, Andres, Wiltschko, Gerkin, Mainland)**
- Mixture quality is predicted as the *unweighted* average of the components' 51-descriptor RATA vectors. Data: 144 component stimuli (115 monomolecular, some at several dilutions) and 432 mixtures of 2–10 components; panel of ≥15 people with 2 replicates — [PMC13371102](https://pmc.ncbi.nlm.nih.gov/articles/PMC13371102/)
- Performance: per-mixture r ≈ 0.71, which is not significantly different from the test–retest ceiling (t = 0.72, p = 0.51). It beats the Ravia 2020 model (p < 0.001). Eight literature "emergent/suppressive" mixtures still fit at r = 0.84 — [PMC13371102](https://pmc.ncbi.nlm.nih.gov/articles/PMC13371102/)
- Geometry: descriptor-vector length tracks perceived intensity (r = 0.77 for single odorants, 0.69 for mixtures), and vector direction encodes quality. Pleasantness follows the intensity-*weighted* average of component pleasantness (r = 0.78) — [PMC13371102](https://pmc.ncbi.nlm.nih.gov/articles/PMC13371102/)
- The authors argue that apparent emergence or suppression is mostly panel drift. Deviation from linearity shrinks significantly when components and mixture are rated in the same session (p < 0.003). They explain "masking" as dilution of relative salience inside the average — [PMC13371102](https://pmc.ncbi.nlm.nih.gov/articles/PMC13371102/)
- This paper does not use POM embeddings; it relies on measured component profiles — [PMC13371102](https://pmc.ncbi.nlm.nih.gov/articles/PMC13371102/)
- Commentary and dispute: a Doty 2025 critique and the replies "Response to Doty 2025, predicting odor from structure is useful" / "Response to Comments of Pellegrino et al." exist in Chemical Senses — [PubMed 41705585](https://pubmed.ncbi.nlm.nih.gov/41705585/), [PubMed 41709413](https://pubmed.ncbi.nlm.nih.gov/41709413/). The content was not fetched.

**POMMix (Tom et al., IOP Machine Learning: Science & Technology 2025; arXiv 2501.16271)**
- Three stages. (1) A POM GraphNets GNN produces 196-d embeddings and is pretrained on GS-LF (4,814 molecules, validation AUROC 0.884). (2) CheMix, a self-attention aggregator with PNA pooling, makes the mixture embedding permutation-invariant. (3) A scaled cosine-distance head has a 2-parameter linear noise layer and a HardTanh output — [arXiv 2501.16271](https://arxiv.org/html/2501.16271v1); [IOP](https://iopscience.iop.org/article/10.1088/2632-2153/adfffc)
- Training was staged: pretrain the POM, train CheMix on frozen embeddings, then fine-tune end-to-end with a lower learning rate on the POM weights. End-to-end fine-tuning helped Kendall τ more than Pearson ρ — [arXiv](https://arxiv.org/html/2501.16271v1)
- 5-fold CV on 743 mixtures / 865 pairs (Snitz + Ravia + Bushdid):
  - Snitz baseline: ρ 0.399
  - XGBoost + RDKit: ρ 0.485
  - CheMix + frozen POM: ρ 0.746
  - POMMix: ρ 0.779 ± 0.028, RMSE 0.118
  — [arXiv](https://arxiv.org/html/2501.16271v1)
- Explicit limitation: POMMix "does not explicitly account for intensity or concentration" and would likely underperform on mixtures that are not intensity-balanced — [arXiv](https://arxiv.org/html/2501.16271v1)

**DREAM Olfactory Mixtures Prediction Challenge (2024, 2025)**
- The 2025 edition had 26 teams, 19 of which submitted test-set predictions. It ended in a four-way tie. A post-hoc ensemble of the top six teams reached median RMSE ≈ 0.08 and Pearson ≈ 0.57, reported as about 33% lower RMSE and 53% higher r than the prior state of the art — [bioRxiv community paper](https://www.biorxiv.org/content/10.64898/2025.12.13.694160.full.pdf); [Synapse](https://www.synapse.org/Synapse:syn64743570). The figures come from the search summary; the PDF text could not be extracted.
- Winning patterns: GIN-GNN blend-level embeddings fed XGBoost. Another approach used pretrained single-molecule embeddings with an exponential-transform aggregation, then boosting to predict mixture distance — [UMich news](https://lsa.umich.edu/stats/news-events/all-news/search-news/olfactory-mixtures-prediction-challenge-winners.html); [GitHub apalania](https://github.com/apalania/DREAM-Olfactory-Mixtures-Prediction-Challenge-2025)
- A PNAS paper, "A semantic-based community model for high-fidelity tuning of olfactory mixture distances" (10.1073/pnas.2611057123), appears to be the published version. It returned 403, so its content was not verified — [PNAS](https://www.pnas.org/doi/10.1073/pnas.2611057123)

**Ravia et al. 2020 (Nature 588:118–123) and Snitz et al. 2013 (PLoS Comput Biol)**
- Ravia 2020 represents a mixture as a combination of its components in a continuous metric space and uses that representation to build olfactory metamers — per search summary via [PMC13371102](https://pmc.ncbi.nlm.nih.gov/articles/PMC13371102/). Ravia's model relies on supplementary intensity ratings from panelists, which limits how well it generalizes — per search summary; [UNVERIFIED wording].
- Snitz 2013: mixtures are represented by summing or averaging component physicochemical descriptor vectors, and similarity is the angle distance — [PLoS CB](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1003184). The listing was seen; details are from memory [UNVERIFIED]. Its baseline scores ρ 0.399 in the POMMix benchmark — [arXiv](https://arxiv.org/html/2501.16271v1)

**Kao / Wakayama 2019 (Ind. Eng. Chem. Res., 10.1021/acs.iecr.9b01225)**
- Dose–response database for 314 perfumery raw materials, rated by 18 perfumers and experienced researchers on a fragrance diluter across gas concentrations. The model predicts intensity at an arbitrary gas concentration. RMSE is 6.22 for single components and 6.69 for mixtures — [ACS](https://pubs.acs.org/doi/10.1021/acs.iecr.9b01225); [ResearchGate](https://www.researchgate.net/publication/334583081_Method_for_Predicting_Odor_Intensity_of_Perfumery_Raw_Materials_Using_Dose-Response_Curve_Database); [Kao release 2020](https://www.kao.com/global/en/newsroom/news/release/2020/20200108-001/)
- The mixture combination rule Kao used was not found in the accessible abstract (GAP).

**Perfumery engineering (Teixeira, Rodríguez, Rodrigues, LSRE Porto)**
- "Perfumery Radar" is an explicit three-stage pipeline:
  1. Liquid-phase thermodynamics, i.e. activity coefficients / non-ideal mixtures, give headspace concentration.
  2. Headspace concentration becomes intensity via the Odor Value (OV = concentration/threshold) or Stevens' power law.
  3. Olfactive-family quality is combined from component intensities, using the stronger-component model for quality.
  — [Perfumery Radar, I&EC Res 2010](https://pubs.acs.org/doi/abs/10.1021/ie101161v); [Teixeira et al. AIChE J 2010, comparison of intensity models](https://aiche.onlinelibrary.wiley.com/doi/10.1002/aic.12043)
- A follow-on, "Perfumery Radar 2.0", extends this to predicting the odour space — [Semantic Scholar](https://www.semanticscholar.org/paper/On-the-design-of-new-fragrances-with-perfumery-2-.-Teixeira-Costa/10f6930dc7698f5f55c4f2ccc7419b6e3b855548)
- A related model covers fragrance-mixture intensity for product design — [I&EC Res ie302538c](https://pubs.acs.org/doi/abs/10.1021/ie302538c)

**Classical psychophysical mixture models**
- Vector model: Berglund 1973, with an interaction coefficient between components. U-model: Patte & Laffort 1979, with an experimentally determined interaction coefficient. Olsson 1994: an integrated model that predicts both mixture intensity *and* quality from component intensities, as an extension of vector summation — [Sensors 2015, modified vector model](https://pmc.ncbi.nlm.nih.gov/articles/PMC4435142/); [Olsson 1998, integrated model, Ann NY Acad Sci](https://nyaspubs.onlinelibrary.wiley.com/doi/10.1111/j.1749-6632.1998.tb10672.x); [Olsson 1994, "An interaction model for odor quality and intensity", Percept Psychophys](https://link.springer.com/article/10.3758/BF03205294)
- The Olsson equations themselves could not be fetched (paywall). From memory [UNVERIFIED]: mixture quality is judged by the relative perceived intensities of the components, so the stronger component dominates the quality judgement.
- Cain, Schiet, Olsson & de Wijk (1995) compared these interaction models. Mixtures of wine odorants showed hypoadditivity — per search summary, [PMC6720763](https://pmc.ncbi.nlm.nih.gov/articles/PMC6720763/)

**Other**
- AROMMA (arXiv 2601.19561, Jan 2026) builds unified embeddings for single molecules and mixtures. It was seen in search results only; details are [UNVERIFIED] — [arXiv](https://arxiv.org/html/2601.19561v1)
- NOSE (arXiv 2604.10452) is a tri-modal contrastive olfactory embedding. Seen in results only — [arXiv](https://arxiv.org/pdf/2604.10452)

### Inferences
- The field has converged on a *de facto* A/B/C decomposition:
  - Per-molecule representation. POM does quality; the Pellegrino DNN does the dose–response.
  - Permutation-invariant aggregation. Averaging, attention or Primacy.
  - A task head.
- What is missing is linking the two per-molecule models. POMMix and DREAM ignore concentration. Pellegrino 2025 ignores quality. Pellegrino 2026 uses measured component profiles and no structure-based quality model.
- The natural architecture would chain three pieces:
  - B (structure → Hill parameters, with vapor pressure) gives each component's intensity at its headspace concentration.
  - A (structure → quality direction, e.g. POM on the unit sphere) gives each component's descriptor direction.
  - C takes the sum or average of component vectors weighted by Primacy-style intensity, with vector length set by predicted mixture intensity.
- The 2026 finding that "vector length ≈ intensity, direction ≈ quality" is direct empirical support for that factorization.
- On weighting, Pellegrino 2026 used an *unweighted* average for quality and an intensity-weighted one for pleasantness. Their stimuli were probably intensity-matched, though that is not confirmed. In formulations with very unequal intensities, the weighting in C must be learned or tested, not assumed.

### Gaps
- Kao/Wakayama's mixture rule, and whether they model quality at all.
- The PNAS 2026 DREAM paper was inaccessible. It is unclear whether concentration/intensity features helped in DREAM 2025.
- The "Osmo mixture paper July 2026" in the brief most likely *is* the Pellegrino/Wiltschko/Gerkin/Mainland 2026 linear-framework preprint (Wiltschko is Osmo's founder). A separate Osmo-only paper was not found.
- Full Olsson 1994 equations; Snitz 2013 details (both from memory).

## 2. How perceived quality depends on concentration; should model A take concentration as input?

### Takeaway
For most molecules quality is roughly constant across dilution, but a minority change character markedly at higher concentration. Intensity also drives pleasantness and the "decayed/chemical" axes. The lowest-risk design gives model A concentration (or model B's predicted intensity) as an input, or gives C a learned concentration-dependent correction. Pure POM-style concentration-agnostic labels cannot represent this effect.

### Cited Findings
- Keller & Vosshall 2016 (BMC Neurosci): 480 molecules at two concentrations, 55 subjects, 20 descriptors plus intensity, pleasantness and familiarity. Of molecules perceived as stronger than water, 98% were rated more intense at the higher concentration. The median intensity difference was 33.2 points on a 0–100 scale — [PMC4977894](https://pmc.ncbi.nlm.nih.gov/articles/PMC4977894/)
- In the same study, descriptor usage was "in general … consistent" between presentations. Notable exceptions were 2-methyl-1-butanol, isopropyl acetate and thiophene, which "differed substantially" at high concentration. The paper gives no count of quality-changing molecules and no cross-concentration profile correlation — [PMC4977894](https://pmc.ncbi.nlm.nih.gov/articles/PMC4977894/). This is weaker than the brief's framing ("Keller 2016 shows quality ratings change with concentration quantitatively"). As fetched, the paper shows mostly consistency with a few strong exceptions.
- Also from Keller 2016: very unpleasant stimuli tended to be very intense, and weak stimuli were neither very pleasant nor very unpleasant, so pleasantness is intensity-coupled — [PMC4977894](https://pmc.ncbi.nlm.nih.gov/articles/PMC4977894/)
- Gross-Isseroff & Lancet 1988 (Chem Senses 13:191–204), "Concentration-dependent changes of perceived odor quality" in 21 subjects, is the classic demonstration — [Chem Senses](https://academic.oup.com/chemse/article-abstract/13/2/191/455578)
- A review exists on constancy vs change of odor quality with concentration ("process dissociation") — [ResearchGate](https://www.researchgate.net/publication/285110698_The_perception_of_odor_quality_as_stimulus_concentration_changes_Constancy_and_process_dissociation_in_olfaction)
- The Pellegrino 2025 introduction says intensity alters the perceived quality of monomolecular odors and of complex mixtures, and "perceived intensity fundamentally shapes stimulus identity" — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- Indole is given as an example that shifts from floral to fecal with concentration, in a 2026 ML paper or survey context — surfaced in search summary ([RSC Adv 2026](https://pubs.rsc.org/en/content/articlehtml/2026/ra/d6ra01805j) / [NOSE](https://arxiv.org/pdf/2604.10452)); exact attribution [UNVERIFIED]. The skatole and thiol examples are perfumery lore; no primary source was fetched (GAP).
- Fichtelmann & Westermayr 2026 (RSC Advances): an ordinal odor-strength classifier (odorless/low/medium/high) on 2,393 molecules with 72% accuracy. It correlates with dilution-series intensity ratings from 10⁻³ to 10⁻⁷ but degrades at 10⁻¹. The authors describe it as "concentration-agnostic" and call for concentration and solvent as explicit covariates — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
- Most public quality datasets lack concentration annotations, which is why current frameworks do not model concentration — search summary of [RSC Adv 2026](https://pubs.rsc.org/en/content/articlehtml/2026/ra/d6ra01805j)
- Mechanistic basis: in the competitive-binding receptor model, each receptor's dose–response differs, so the pattern of active receptors, and hence the quality code, shifts with concentration. The model explains receptor mixture responses with median RMSE < 0.1 for 12 of 15 receptors, and for 12-component mixtures with RMSE 0.16 vs 1.91 for summation — [PNAS 2019 / PMC6511041](https://pmc.ncbi.nlm.nih.gov/articles/PMC6511041/)

### Inferences
- Design options for A:
  - (i) Concentration-agnostic A with the "intrinsic" quality direction, plus a small residual head in C that takes (A-embedding, predicted intensity) and outputs a quality correction.
  - (ii) Concentration-conditioned A via FiLM on log-concentration or predicted intensity.
- Option (i) fits the data reality better: large label sets such as GS-LF have no concentration, while dilution-resolved quality data (Keller 2016 at 2 levels; the Pellegrino 2026 set with some dilutions) is small. So pretrain A without concentration and learn the correction only where data exist.
- Hedonic and "trigeminal/chemical/decayed" dimensions should be modeled as intensity-dependent even if the other descriptors are not.

### Gaps
- No quantitative per-descriptor estimate of how much of quality variance is explained by concentration across a large molecule set.
- No primary sources fetched for the indole, skatole or thiol concentration-dependence claims.

## 3. Combining rules: OAV weighting, masking/suppression/synergy, hypo-/hyperadditivity, ML mixture-intensity models

### Takeaway
Two regimes apply. For *intensity*, mixtures are hypoadditive. A Primacy-weighted average of component intensities beats addition, strongest-component, vector and U-models (r = 0.85). For *quality*, an average of component vectors is near the noise ceiling, and much of the apparent masking or emergence is measurement drift. OAV is a poor proxy for intensity because Hill slopes and maxima differ.

### Cited Findings
- Rule comparison for mixture intensity (Pellegrino 2025):
  - Candidates were ADD, SC, EUC, VEC, U, CB and Primacy; Primacy was best (r 0.85, RMSE 8.6).
  - A direct DNN reached RMSE 7.5.
  - OAV fails because at OAV = 100 intensities vary widely.
  — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- Quality mixing is linear (averaging), and pleasantness is intensity-weighted (Pellegrino 2026) — [PMC13371102](https://pmc.ncbi.nlm.nih.gov/articles/PMC13371102/)
- Receptor-level competitive binding produces overshadowing, suppression and (with facilitation extensions) synergy or inhibition from single-odorant dose–response data alone — [PMC6511041](https://pmc.ncbi.nlm.nih.gov/articles/PMC6511041/)
- Classical models: the vector model (Berglund), the U-model (Patte & Laffort), Olsson's integrated intensity + quality model, and a modified vector model for sensors — [PMC4435142](https://pmc.ncbi.nlm.nih.gov/articles/PMC4435142/); [Olsson 1998](https://nyaspubs.onlinelibrary.wiley.com/doi/10.1111/j.1749-6632.1998.tb10672.x). A hypoadditive total was observed for wine odorants — [PMC6720763](https://pmc.ncbi.nlm.nih.gov/articles/PMC6720763/)
- Perfumery: the OV or Stevens' power law gives intensity, and the stronger-component model gives quality or family classification — [Teixeira AIChE J 2010](https://aiche.onlinelibrary.wiley.com/doi/10.1002/aic.12043); [Perfumery Radar](https://pubs.acs.org/doi/abs/10.1021/ie101161v)
- Pleasantness of binary mixtures has its own prediction models (Lapid et al. 2008, Chem Senses) — [Chem Senses 33(7):599](https://academic.oup.com/chemse/article/33/7/599/330603). Listing only; details were not fetched.

### Inferences
- A defensible default for C:
  - I_mix = Primacy(Hill_i(0.2·C_i)).
  - Quality direction q_mix = normalize(Σ w_i·q_i), with w_i uniform or a learned function of I_i.
  - Output profile = I_mix · q_mix.
  - Pleasantness uses intensity-weighted averaging.
- Then learn a residual on top to capture any true interactions. This is physics/psychophysics-informed and has few parameters, which matters because mixture data are small (hundreds of mixtures).
- Replace OAV (C/threshold) with Hill-predicted intensity. Keep the threshold only as a derived quantity, e.g. the concentration at which I crosses the detection criterion.

### Gaps
- There is no public benchmark jointly scoring mixture intensity *and* quality profile at varied concentrations.
- Hyperadditivity/synergy evidence at the perceptual level was not surveyed in depth.

## 4. ML design patterns: modular vs end-to-end/multitask; physics-informed layers; evidence from analogous chemistry

### Takeaway
Olfaction evidence favors a hybrid: pretrained or modular components with structured, mechanistically shaped interfaces (Hill parameters, permutation-invariant aggregation), plus optional end-to-end fine-tuning at low learning rate. POMMix gains from end-to-end fine-tuning after staged training. Pellegrino's direct DNN slightly beats the modular Primacy rule on RMSE but gives up interpretability. PK/PBPK work shows ML-predicted parameters feeding a mechanistic model beat less-informed inputs and generalize better. Multitask sharing risks negative transfer when tasks want conflicting representations.

### Cited Findings
- **Staged then end-to-end** (POMMix): pretrain the GNN, train the aggregator on frozen embeddings, then fine-tune end-to-end at a lower learning rate for the encoder. This gave ρ 0.746 → 0.779 over frozen-POM CheMix. The end-to-end step mostly improved rank metrics — [arXiv 2501.16271](https://arxiv.org/html/2501.16271v1)
- **Bad auxiliary pretraining can hurt**: pretraining with GS-LF Jaccard similarities lowered ρ from 0.746 to 0.628 — [arXiv](https://arxiv.org/html/2501.16271v1). Negative transfer occurs in olfaction too.
- **Structured output layer**: the Pellegrino DNN outputs Hill parameters (Imax, EC50, n), a physics-informed differentiable layer, with r 0.87. Vapor pressure is among the top features — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- **Modular vs direct for mixture intensity**: Primacy rule on model-predicted component intensities gives RMSE 8.6. The direct DNN trained on single + mixture data gives RMSE 7.5 — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- **Embeddings + boosting (stacking)**: DREAM 2025 winners fed pretrained molecule embeddings into mixture aggregation and then XGBoost. A post-hoc ensemble of the top six teams beat every single team — [UMich](https://lsa.umich.edu/stats/news-events/all-news/search-news/olfactory-mixtures-prediction-challenge-winners.html); [bioRxiv](https://www.biorxiv.org/content/10.64898/2025.12.13.694160.full.pdf)
- **Multitask negative transfer**: conflicting task gradients mean joint training of related tasks can underperform single-task models — [arXiv 2303.14582](https://arxiv.org/html/2303.14582). In ADMET, multitask learning helps low-label endpoints, but task synergy is not guaranteed. This motivates adaptive auxiliary-task selection — [PMC10654589](https://pmc.ncbi.nlm.nih.gov/articles/PMC10654589/)
- **Hybrid ML + mechanistic (PK analog)**:
  - Structure → ML-predicted parameters (fu, Caco-2, CL) → PBPK model predicted AUC within 2-fold for 65.0% of compounds, vs 47.5% using in-vitro inputs — [Pharm Res 2024, PubMed 38918309](https://pubmed.ncbi.nlm.nih.gov/38918309)
  - A DNN–mechanistic hybrid split "physiology" parameters (fixed) from "molecule" parameters (learned). The authors claim this reduces data needs and improves generalization — [arXiv 2310.09167](https://arxiv.org/pdf/2310.09167)
  - Further hybrids combine ML with mechanistic modeling to predict IV PK profiles — [J Med Chem 2025](https://pubs.acs.org/doi/10.1021/acs.jmedchem.5c00340); [PMC12342024](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12342024/)
- **Explicit liquid → headspace step** in perfumery: thermodynamic activity models give headspace concentration before OV/Stevens — [Perfumery Radar](https://pubs.acs.org/doi/abs/10.1021/ie101161v); [Teixeira 2013 diffusion/performance](https://aiche.onlinelibrary.wiley.com/doi/10.1002/aic.14106)

### Inferences
- The PK analogy maps directly onto odor:
  - Molecule-specific parameters: Hill EC50/n/Imax, quality direction, vapor pressure or activity coefficient.
  - Fixed "physiology": the sniff/Primacy fraction, receptor competition, human noise.
  - The hybrid lets each module train on its own dataset, e.g. GS-LF for A and dose–response sets for B (Pellegrino 434 points, Kao 314 materials). This is the main practical argument for modularity: **the label sources are disjoint**, and almost no dataset has quality × concentration × mixture jointly.
- The recommended pattern is a shared pretrained molecular encoder (POM-like) with separate heads for A and B, i.e. multitask with a shared trunk. Watch for negative transfer, for example by comparing each head against single-task training. C is a differentiable psychophysics layer (Hill, Primacy, vector averaging) with a small learned residual. Optionally, fine-tune end-to-end at low learning rate once joint mixture data exist, as POMMix did.
- Mixture of experts or cascades are only warranted if molecule classes (thiols, amines, musks) show distinct dose–response or quality-shift behavior. No olfaction evidence was found either way.
- Neural ODEs for temporal (sniff-cycle) dynamics are not supported by any olfaction ML paper found. Primacy's "20% of ambient concentration" is a static approximation of that dynamic.

### Gaps
- No olfaction paper directly compares a shared-encoder multitask (quality + intensity) model against separate models.
- No mixture-of-experts or neural-ODE olfaction perception model was found.
- The Pellegrino DNN's single-task vs multitask ablations were not checked.

## 5. Evaluation: per-stage and whole-pipeline, error/uncertainty propagation

### Takeaway
Evaluate each stage against its own human-reliability ceiling, and evaluate the pipeline end-to-end on held-out mixtures and concentrations. Human noise ceilings (test–retest) are the key reference: r ≈ 0.97 for intensity panels, r ≈ 0.71–0.74 for mixture quality profiles, and a ceiling for similarity judgments noted by POMMix. No paper found propagates uncertainty through odor pipeline stages; that must be designed in.

### Cited Findings
- Ceilings:
  - Intensity panel reliability r = 0.97 for single molecules and r = 0.97 for mixtures, vs model r 0.87 / 0.85 — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
  - Quality-profile replicate r = 0.74 (consensus 0.84), and the model's r ≈ 0.71 is at ceiling — [PMC13371102](https://pmc.ncbi.nlm.nih.gov/articles/PMC13371102/)
  - POMMix notes human noise sets a ceiling: 60 of 63 identical-mixture pairs were rated with non-zero dissimilarity — [arXiv](https://arxiv.org/html/2501.16271v1)
- Stage metrics in use:
  - Intensity: RMSE on a 0–100 scale plus Pearson r — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/); Kao RMSE 6.22 / 6.69 — [ACS](https://pubs.acs.org/doi/10.1021/acs.iecr.9b01225)
  - Mixture distance: Pearson, RMSE and Kendall τ with 5-fold CV — [arXiv](https://arxiv.org/html/2501.16271v1)
  - Quality: AUROC (POM on GS-LF, validation 0.884) — [arXiv](https://arxiv.org/html/2501.16271v1)
- Downstream task validation: Pellegrino used omission tests on natural aromas (r 0.45–0.55) as an application-level check against OAV — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- Session effects matter: deviation from linearity shrank when components and mixture were rated in the same session (p < 0.003). Test design can create spurious "interaction" signal — [PMC13371102](https://pmc.ncbi.nlm.nih.gov/articles/PMC13371102/)
- Split design: scaffold, temporal and cluster splits with aligned multitask partitions prevent leakage — [Multitask ADMET splits](https://www.emergentmind.com/topics/multitask-admet-data-splits)

### Inferences
- Suggested protocol:
  - (a) Evaluate A on held-out *molecules* (scaffold split).
  - (b) Evaluate B on held-out molecules *and* held-out concentrations (extrapolation above and below the fitted range).
  - (c) Evaluate C with *oracle* inputs (measured component profiles and intensities) vs *predicted* inputs. The gap quantifies error propagation, mirroring Pellegrino's "model-predicted vs measured components" setup.
  - (d) Evaluate end-to-end on mixture splits where no component molecule was seen in training.
- Report everything relative to test–retest ceilings.
- Uncertainty: B's Hill parameters make parametric propagation natural (sample EC50, n, Imax from a posterior or deep ensemble, then push the samples through Primacy and the vector mix). A's direction uncertainty can come from ensemble spread on the embedding. Monte Carlo propagation through C is cheap because C is closed-form.
- Since EC50 errors enter on a log-concentration scale, errors are largest near threshold, where the Hill curve is steepest. That is exactly where OAV-style decisions are made.

### Gaps
- No published olfaction work on formal uncertainty propagation across stages, or on calibration of intensity predictions.
- No shared benchmark covers quality at multiple concentrations for mixtures; one would need to be assembled, e.g. from Pellegrino 2026 dilution data and Keller 2016's two levels.
