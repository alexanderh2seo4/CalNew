# Mechanistic, Staged Models of Odor Potency (molecule → headspace → nasal transport → receptor → percept) and Mechanistic+ML Hybrids

Research notes, compiled 2026-09-27. Scope: physics- and biology-informed stage models of odor potency and hybrids that combine them with ML. Every factual claim carries an inline source. Standard textbook forms of equations (Raoult/Henry, Hill, Stevens) appear only where a cited paper uses them. Interpretations are kept in the "Inferences" sections.

---

## Q1. Headspace/release stage: Raoult/Henry, activity coefficients, matrix effects, fragrance evaporation models, odour value, datasets

### Takeaway
The best-developed mechanistic release models come from "Perfume Engineering" (Rodrigues/Teixeira/Mata group, AIChE J, Chem Eng Sci, Ind Eng Chem Res) and from Kao (Wakayama 2019). Both use modified Raoult's law with UNIFAC activity coefficients to get headspace concentrations. The Rodrigues/Teixeira group converts these into odour value (OV = headspace concentration / threshold) or a power-law intensity, then adds Fickian diffusion, skin permeation and matrix models. Kao feeds the same UNIFAC headspace into measured per-material dose-response curves. Its reported error is RMSE 6.22 (single materials) and 6.69 (mixtures) on a 0–100 LMS scale.

### Cited Findings
- **Perfumery Ternary Diagrams (PTD®).** PTDs give a fast theoretical estimate of headspace odour value for every composition of three fragrant components plus one solvent, which removes trial-and-error headspace analysis — [Mata et al. 2005, Flavour Fragr J](https://onlinelibrary.wiley.com/doi/abs/10.1002/ffj.1590); [Mata 2005 "Engineering perfumes", AIChE J](https://ui.adsabs.harvard.edu/abs/2005AIChE..51.2834M/abstract)
- **PTD validation.** Measured OVs were compared with PTD predictions under two cases: ideal (no molecular interactions) and non-ideal (UNIFAC activity coefficients). The test mixture was limonene / geraniol / vanillin / ethanol, and both thresholds and headspace concentrations were measured — [Gomes et al. 2008, AIChE J](https://ui.adsabs.harvard.edu/abs/2008AIChE..54..310G/abstract)
- **Extensions.** The method was extended to quaternary and quinary systems with tetrahedral diagrams — [Teixeira et al. 2009, AIChE J](https://aiche.onlinelibrary.wiley.com/doi/10.1002/aic.11811). The group also published a method for defining odour zones in PTDs — [Mata et al. 2006, AIChE J](https://ui.adsabs.harvard.edu/abs/2006AIChE..52.2938M/abstract)
- **Evaporation/diffusion model.** A Fick's-law model simulates how small volumes of perfume mixtures evaporate and diffuse over time and distance, with UNIFAC for the non-ideal vapour–liquid equilibrium. Ethanol is released fast first, followed by diffusion of the fragrant components. The OV model and a power-law intensity model were compared: they differ in initial impact but converge over time, and the power-law model predicts higher ethanol intensity — [Teixeira et al. 2009, Chem Eng Sci "The diffusion of perfume mixtures and the odor performance"](https://www.sciencedirect.com/science/article/abs/pii/S0009250909000700); [Teixeira et al. 2013, AIChE J "Diffusion and performance of fragranced products: prediction and validation"](https://aiche.onlinelibrary.wiley.com/doi/10.1002/aic.14106); [Almeida et al. 2021, AIChE J, radial diffusion model](https://aiche.onlinelibrary.wiley.com/doi/abs/10.1002/aic.17351)
- **Mixture intensity models compared.** [Teixeira et al. 2010, AIChE J, "The perception of fragrance mixtures: a comparison of odor intensity models"](https://aiche.onlinelibrary.wiley.com/doi/10.1002/aic.12043) compares intensity models for fragrance mixtures. The details were not retrieved.
- **Skin matrix.** A differential mass-balance model predicts evaporation and permeation profiles of fragrance applied to skin, validated with a Franz diffusion cell and porcine skin — [Evaporation and Permeation of Fragrance Applied to the Skin, Ind Eng Chem Res 2019](https://pubs.acs.org/doi/abs/10.1021/acs.iecr.9b01004)
- **Product/emulsion matrices.** Release of fragrance components from a simplified matrix used in toiletries and household products has been modelled — [Ind Eng Chem Res 2015/16](https://pubs.acs.org/doi/abs/10.1021/acs.iecr.5b03852). Fragrance in dermocosmetic emulsions is reviewed from microstructure to skin application — [Dallay 2024, Int J Cosmet Sci](https://onlinelibrary.wiley.com/doi/10.1111/ics.12896). A 2025 review summarises the PTD approach — [ScienceDirect 2025](https://www.sciencedirect.com/science/article/pii/S2772508125000079)
- **Kao/Wakayama 2019.**
  - The dataset has 314 perfumery raw materials (PRMs), each with an "odor intensity standard curve" (intensity vs gas-phase concentration) on the Labeled Magnitude Scale (0–100).
  - The prediction pipeline combines UNIFAC, modified Raoult's law, Stevens' power law and a strongest-component rule to predict perceived intensity and character.
  - Validation RMSE is 6.22 for single components and 6.69 for mixtures.
  - Sources: [Wakayama, Sakasai, Yoshikawa, Inoue 2019, Ind Eng Chem Res](https://pubs.acs.org/doi/10.1021/acs.iecr.9b01225); [Semantic Scholar record](https://www.semanticscholar.org/paper/Method-for-Predicting-Odor-Intensity-of-Perfumery-Wakayama-Sakasai/988a3e364a6918ec709a3e26fea10991f215e491)
- **Earlier fragrance-mixture intensity model** for perfumed product design: [Ind Eng Chem Res 2013 (ie302538c)](https://pubs.acs.org/doi/abs/10.1021/ie302538c). Details were not retrieved.
- **Dosing in the air phase, not the liquid phase.** Pellegrino et al. delivered measured air-phase (headspace) concentrations in Nalophan gas-sampling bags to avoid solvent-interaction artefacts of liquid dilutions. This improved replicate reliability to r(60) = 0.97 (RMSE 3.0), versus r ≈ 0.65 in earlier studies — [Pellegrino et al. 2025, bioRxiv/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)

### Inferences
- The release stage is the most mature and "solved" part of the pipeline. With y_i·P = x_i·γ_i·P_i^sat (γ from UNIFAC, or COSMO-RS as a drop-in alternative), headspace concentration can be computed for any formulation. The main needs are good P_sat (vapour pressure) values and a good activity-coefficient model.
- The Pellegrino result (solvent artefacts degrade reliability) implies that any potency model trained on liquid-dilution labels mixes release-stage error into the "potency" label. A staged pipeline should use gas-phase concentration as the internal currency.
- Kao's architecture is already a staged model: UNIFAC/Raoult for release, then a per-material psychophysical curve for perception. Its weak point is that each material needs a measured curve. ML can replace that measured-curve lookup (see VIANA in Q4).

### Gaps
- No retrieved paper directly benchmarks COSMO-RS against UNIFAC for fragrance headspace. COSMO-RS use in fragrance is plausible but unverified here.
- Firmenich/Givaudan proprietary headspace models: no public technical source found.
- Fabric matrix and quantitative ethanol/oil partitioning: no specific model retrieved.
- Specific datasets for vapour pressure and air/water partitioning (e.g., EPI Suite, NIST, Kao's 314-PRM curves) were not verified for public availability. It is unclear whether Wakayama's curve data are public; VIANA reports using 209 molecules from it (Q4).

---

## Q2. Transport/sorption stage: nasal mucus partitioning, sorption models, CFD, Abraham solvation equations, "transport vs receptor"

### Takeaway
Transport explains much of detectability and potency:
- For odour thresholds, the transport-based Abraham solvation equations reach R² ≈ 0.75–0.77, and Rodríguez's three-property model (vapour pressure, water solubility, logKow) reaches r² = 0.769.
- The same framework explains 93–95% of variance for nasal pungency and eye irritation (trigeminal, receptor-nonspecific) but only about 77% for odour. That gap is the classic evidence that odour has a receptor-specific component.
- Nasal CFD work (Keyhani/Scherer/Mozell; Zhao/Scherer/Dalton) shows that the limit on uptake is on the mucosal side (solubility and diffusion in mucus), not the air-side flow regime.
- Mucosa solubility is odorant-specific and higher than water solubility predicts for hydrophobic odorants.

### Cited Findings
- **Abraham general solvation equation for sensory thresholds.** It accounts for 93–95% of variance for VOC nasal pungency and eye irritation thresholds, but only 77% for odour thresholds — [Abraham, Gola, Cometto-Muñiz, Cain 2001, Indoor Built Environ](https://dx.doi.org/10.1177/1420326X0101000320) (figures as reported in search-indexed abstract text).
- **Modified Abraham equation for odour.** A modified equation adds a factor for aliphatic aldehydes and carboxylic acids plus a size term that depends on the VOC's maximum length. The size term produces a cut-off that sharply reduces the potency of higher homologues — [Abraham et al., "A model for odour thresholds", Chem Senses 2002 (ResearchGate)](https://www.researchgate.net/publication/11520625_A_model_for_odour_thresholds)
- **Abraham et al. 2012, "An Algorithm for 353 Odor Detection Thresholds in Humans"** (Chem Senses 37:207–218):
  - The dependent variable is log(1/ODT), regressed on Abraham descriptors (E, S, A, B, L).
  - 193 ODTs from Nagata's triangle-bag method give R² = 0.748, SD = 0.830 log units.
  - 353 combined ODTs (Nagata; Cometto-Muñiz & Cain; Cometto-Muñiz & Abraham; Hellman & Small), rescaled to the Nagata scale, give R² = 0.759, SD = 0.819 log units.
  - Indicator variables capture extra potency for **aldehydes, carboxylic acids, unsaturated esters and mercaptans**.
  - Descriptors are available or calculable for thousands of compounds.
  - Sources: [Oxford Academic abstract](https://academic.oup.com/chemse/article-abstract/37/3/207/325917); [pyrfume-data issue #37](https://github.com/pyrfume/pyrfume-data/issues/37)
- **Rodríguez et al. 2011.** A linear regression of ODT on vapour pressure, water solubility and octanol/water partition coefficient gives r² = 0.769 across 121 chemicals, with thresholds pooled from several authors. It is motivated by air-to-olfactory-neuron transport — [Rodríguez et al. 2011, Flavour Fragr J](https://onlinelibrary.wiley.com/doi/abs/10.1002/ffj.2076)
- **Mayhew et al. 2022, PNAS.** Transport features alone reliably classify molecules as odorous or odorless. An odorant must be:
  - volatile enough to enter the air phase;
  - non-volatile and hydrophilic enough to sorb into the mucus;
  - hydrophobic enough to enter a receptor binding pocket.
  
  Features were boiling point, vapour pressure, hydrophilicity and lipophilicity. The authors conclude that reaching the receptors is the dominant barrier — [Mayhew et al. 2022, PNAS](https://www.pnas.org/doi/full/10.1073/pnas.2116576119); [code: joelmainland/odor-prediction](https://github.com/joelmainland/odor-prediction). (Exact accuracy figures were not retrieved; see Gaps.)
- **Keyhani, Scherer & Mozell 1997** (J Theor Biol). This anatomically correct 3-D finite-element model of the human nose solves steady laminar flow at quiet-breathing rates.
  - The wall boundary condition includes odorant solubility (the mucus/air partition coefficient), diffusivity in mucus and mucus-layer thickness.
  - About 10% of volumetric flow passes through the olfactory airway, roughly constant across flow rates.
  - At constant inlet concentration, higher flow increases total olfactory uptake for all odorants.
  - Source: [PubMed 9219668](https://pubmed.ncbi.nlm.nih.gov/9219668/)
- **Zhao, Dalton, Yang & Scherer 2006** (Chem Senses 31:107). Predicted olfactory flux barely differs between turbulent and laminar flow at 300–1000 ml/s, for odorants of very different mucosal solubility. The reason is that lateral mass-transport resistance is much higher in the mucosal wall than in the air phase. Sniffing raises uptake flux but can lower cumulative olfactory uptake when inspired volume is held fixed — [PubMed 16354744](https://pubmed.ncbi.nlm.nih.gov/16354744/)
- **Zhao et al. 2004** (Chem Senses 29:763). The fraction of odorant absorbed by the nasal mucosa was measured with a photoionisation detector (in one nostril, out the other, with the velopharynx closed) and matched to 3-D CFD, giving estimates of mucosal solubility and effective diffusive resistance for each odorant.
  - Mucosa solubility is odorant-specific. Odorants with lower water solubility were more soluble in mucosa than water solubility alone predicts.
  - The mucosal layer's extra diffusive resistance over a thin water layer appeared general and not odorant-specific.
  - Source: [Chem Senses 29(9):763](https://academic.oup.com/chemse/article/29/9/763/271736)
- **Scott, Sherrill, Jiang & Zhao 2014** (J Neurosci 34:2025). A rat-nose CFD model simulated sorption patterns for many odorants and was compared with spatial EOG responses under matched flow. Both sorption and neural response are tuned to a narrow range of mucosal solubility, and flow rate and direction modulate that range — [J Neurosci 2014](https://www.jneurosci.org/content/34/6/2025). Related: rat odorant-uptake modelling ([PubMed 17220517](https://pubmed.ncbi.nlm.nih.gov/17220517/)); a mouse EOG study of receptor zones vs sorptiveness ([J Neurophysiol 2013](https://journals.physiology.org/doi/full/10.1152/jn.00769.2012)); and a review of the sorption/chromatography hypothesis ([Coppola 2022, BioEssays](https://onlinelibrary.wiley.com/doi/10.1002/bies.202100263))
- **In-nose concentration timing.** The primacy mixture model assumes mixture intensity is set early in inhalation, when odour concentration in the nose is about 20% of ambient — [Pellegrino et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- **Environmental application.** A pilot CFD study examined odorant transport to the olfactory region during ISO 16000-28 sensory evaluations — [Building & Environment 2023](https://www.sciencedirect.com/science/article/abs/pii/S0360132323008958)

### Inferences
- The transport stage can be written as an effective delivered dose: C_mucus,olf ≈ K_m/a · f_olf(Q, geometry, K_m/a, D_m) · C_air. K_m/a is the mucus/air partition coefficient, roughly K_water/air adjusted upward for hydrophobic odorants, per Zhao 2004. CFD work suggests a lumped one-parameter mucosal-resistance model is adequate for population-level potency, because air-side detail matters little (Zhao 2006).
- Abraham descriptors are a compact, physically interpretable interface for this stage. The E, S, A, B, L coefficients map onto dispersion, polarity and H-bond terms of gas → mucus/biophase transfer. They also transfer to pungency, which gives a "no receptor specificity" control.
- The Abraham indicator variables (mercaptans, aldehydes, acids, unsaturated esters) are, in effect, hand-coded receptor-specificity corrections. A hybrid model can learn these as an ML residual rather than as hand-picked flags.

### Gaps
- Hahn, Scherer & Mozell (1993–94) nasal sorption papers: original equations and values were not retrieved.
- A public, curated table of measured human mucus/air partition coefficients: not found. Zhao 2004 gives estimates for a limited set, and the exact odorants and values were not extracted.
- Mayhew 2022 exact classification metrics and the size of the "odorous chemical space" estimate were not retrieved (PNAS and PubMed returned 403 or a captcha).

---

## Q3. Receptor and perceptual stage: Hill/Stevens/Beidler, EC50 vs thresholds, single-receptor threshold setting, Laffort/Patte, intensity models

### Takeaway
- **Psychophysics.** Pellegrino/Mainland 2025 found the Hill equation fits concentration–intensity curves better than Stevens, Beidler or Fechner. A 10-feature model predicted held-out-molecule intensity nearly as well as a 127-feature DNN (r = 0.87). Vapour pressure was the most important feature, but half the 10 features are not transport descriptors.
- **Receptors.** Human OR EC50s cluster around roughly 100 µM (range about 1 µM–5 mM), orders of magnitude above perceptual thresholds. The strongest mechanistic finding on thresholds is Dewan et al. 2018: in mice, behavioural thresholds are set by the single most sensitive receptor.

### Cited Findings
- **Pellegrino, Samoilova, Ihara, Andres, Singh, Gerkin, Koulakov & Mainland 2025**, "A quantitative framework for predicting odor intensity across molecule and mixtures" (bioRxiv 10.1101/2025.08.08.668954; PMC12363845). Sources: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/); [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.08.08.668954v1)
  - **Data.** 62 odorants at 7 or more concentrations each; 434 monomolecular points; 260 mixture intensity ratings (7,623 ratings including replicates); 36 panellists, with at least 15 per session.
  - **Curve form.** I = I_max·C^n/(C^n + EC50^n). The Hill equation gave the lowest error of the four tested forms (Stevens power law, Beidler, Fechner log, Hill).
  - **Full DNN.** 127 physicochemical features, 5 layers of 300 units, 10-fold CV stratified by molecule. Held-out molecules: RMSE 7.1, r = 0.87, versus shuffled control RMSE 20.4.
  - **10-feature model.** RMSE 7.2, r = 0.87. The features are:
    - transport: MW, vapour pressure, boiling point, MLOGP;
    - geometric: alpha-area;
    - five Dragon-type chemoinformatic descriptors: CATS2D_03_LL, SpMax8_Bh(p), MPC07, MATS7i, H2s.
  
    Permuting vapour pressure produced the largest significant RMSE increase (p < 10⁻⁵).
  - **Mixtures.** A biophysical primacy-coding model scored RMSE 8.6, r = 0.85. An end-to-end mixture DNN scored RMSE 7.5 (shuffled control 15.8). Competitive-binding, Euclidean and strongest-component models were also tested; Euclidean and strongest-component overestimated.
  - **External validation.** Single-molecule predictions correlated with GC-olfactometry ratings, r(60) = 0.62. For identifying key odorants in 5 natural aromas (95 odorants), the mixture DNN reached r(65) = 0.55 versus 0.45 for the single-molecule model, outperforming classic OAV approaches.
  - **Residuals.** Errors were consistent across chemical classes and largest at maximum intensities. No detailed per-molecule outlier analysis was reported.
- **Kao/Wakayama 2019.** Stevens' power law and a strongest-component rule on top of 314 measured per-material curves (LMS 0–100) give RMSE 6.22 (single) and 6.69 (mixtures) — [Ind Eng Chem Res 2019](https://pubs.acs.org/doi/10.1021/acs.iecr.9b01225). VIANA describes the Wakayama curves as reparameterisable in a logistic (Hill-in-log-concentration) form, Ψ = I_max / (1 + e^(−(X − C)/D)) with X = log concentration — [VIANA arXiv 2604.01365](https://arxiv.org/html/2604.01365)
- **OR EC50 statistics** (Bak, Jang & Hyeon 2018, PLOS Comput Biol):
  - The data cover 89 odorants × 304 human ORs, with 317 reliable pairs out of 535.
  - Mean log10 EC50 is −3.6 for activating pairs (SD 1.1) and −4.0 over all pairs (SD 1.8). The range corresponds to about 1 µM < K½ < 5 mM.
  - OR responses appear optimised around about 100 µM, unlike non-olfactory GPCRs, which sit in the nM range.
  - Source: [PMC5983876](https://pmc.ncbi.nlm.nih.gov/articles/PMC5983876/)
- **The gap.** Most measured OR EC50s are in the µM–mM range, while 2-isobutyl-3-methoxypyrazine is detectable at about 0.01 nM, several orders of magnitude lower. Psychophysical detection thresholds nevertheless correlate directly with EC50, and even more strongly with efficacy, per a study indexed in the same search. That study was not individually verified; see Gaps — [search-indexed summary; PLOS CB 2018](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1006175)
- **Dewan, Cichy, Zhang, Miguel, Feinstein, Rinberg & Bozza 2018** (Nat Commun). In mice, deleting all TAARs, or even a single TAAR, causes significant amine-detection deficits.
  - The behavioural threshold is set solely by the most sensitive receptor, with no contribution from other highly sensitive receptors.
  - Increasing the number of neurons expressing the threshold-setting receptor did not improve sensitivity.
  - Sources: [bioRxiv 341099](https://www.biorxiv.org/content/10.1101/341099v1); [Nat Commun](https://www.nature.com/articles/s41467-018-05129-0)
- **Receptor-specific super-potency (thiols).** Human OR2T11 responds to low-MW thiols (C1–C4 straight and branched, C5 branched) and needs ionic copper for robust activation; copper and silver enhance its response — [Li et al. 2016, JACS](https://pubs.acs.org/doi/10.1021/jacs.6b06983). OR2M3 is narrowly tuned to the onion odorant 3-mercapto-2-methylpentan-1-ol ([Chem Senses 2017](https://academic.oup.com/chemse/article/42/3/195/2549461)), with copper-mediated thiol potentiation ([CMLS 2019](https://link.springer.com/article/10.1007/s00018-019-03279-y)).
- **Sulfur odorants as extreme potency.** Sulfur-containing compounds typically make up the lowest-threshold group among key food odorants — [JACS 2016 / search summary](https://pubs.acs.org/doi/10.1021/jacs.6b06983)
- **Other receptor-stage datasets.** OR5K1 is a specialised receptor for pyrazine key food odorants ([JCIM 2022](https://pubs.acs.org/doi/10.1021/acs.jcim.2c00752)). A status report on human ORs and their agonists appeared in [Chem Senses 2024](https://academic.oup.com/chemse/article/doi/10.1093/chemse/bjae037/7821270). A 2025 high-expression OR screen for signature odorants appeared in [Current Biology 2025](https://www.cell.com/current-biology/fulltext/S0960-9822(25)01211-4). Human perception predicted from OR activities: [PMC7393469](https://pmc.ncbi.nlm.nih.gov/articles/PMC7393469/)
- **Laffort/Patte/Dravnieks.** The power-law exponent of the psychophysical function depends on physicochemical properties, and a Dravnieks–Laffort model combining three basic properties was reported as quite successful. Patte and Laffort extended the "U model" for mixtures using power-law exponents, and it performed best on magnitude-estimation literature data — [Attention, Perception & Psychophysics reply](https://link.springer.com/article/10.3758/BF03208957); [Chem Senses 1982, suprathreshold interaction models](https://academic.oup.com/chemse/article-abstract/7/2/153/482173). Solvation models predict a length-driven cut-off in potency along homologous series — [MDPI Sensors 2012](https://www.mdpi.com/1424-8220/12/4/4105)
- **Review.** For an integrative intensity perspective, see [Mainland et al. 2014, Trends Neurosci "From molecule to mind"](https://www.cell.com/trends/neurosciences/abstract/S0166-2236(14)00080-0)

### Inferences
- The perceptual stage should output Hill parameters (EC50_perc, n, I_max), not a single number. The threshold is then derived as the concentration at which I crosses the detection criterion. This unifies threshold and suprathreshold intensity, as Pellegrino, Kao and VIANA all do in different ways.
- Two findings suggest threshold potency is governed by the receptor with the highest affinity for the odorant, not by population coding: Dewan 2018 (the most sensitive receptor sets the threshold) and the EC50/efficacy correlation. The receptor stage should therefore feed min over receptors of EC50_OR into the threshold, after conversion from gas-phase to mucus concentration by the transport stage.
- The µM/ppb gap is partly bridged by air→mucus partitioning (K_m/a can be large for hydrophobic odorants) and partly by the fact that heterologous assays likely underestimate in vivo sensitivity. Neither factor was quantified in retrieved sources, so any stated amplification factor is speculative.

### Gaps
- No retrieved paper gives a quantitative end-to-end mapping from EC50_OR (µM, aqueous) × K_m/a to human ODT (ppb, gas) across many odorants.
- Beidler-equation fits for human olfaction: only the Pellegrino comparison was retrieved, which rated Beidler worse than Hill.
- The claim "psychophysical thresholds correlate directly with EC50, more strongly with efficacy" comes from a search summary. Its primary source was not pinned down and should be verified before citing.

---

## Q4. Hybrid mechanistic–ML models (ML predicts parameters of a mechanistic equation; grey-box; olfaction/fragrance examples)

### Takeaway
Hybrids of this kind exist but are few and have small data:
- **VIANA (2026).** A GCN plus Principal Odor Map embeddings predicts Hill-law parameters, and the Hill law is hard-coded as the output layer. Hill-constrained models greatly outperformed a black-box GCN (R² 0.991–0.996 vs 0.010). This evaluation is on reconstructed curves from 209 Kao molecules, so the numbers overstate real-world accuracy.
- **Property-level hybrids.** GRAPPA (vapour pressure), group-contribution-assisted GNNs, GNN/kNN/group-contribution predictors of Abraham descriptors, and a safe multitask VP+ODT GNN all exist and could supply stage parameters.
- **Missing.** No olfaction-specific Gaussian-process residual ("grey-box") correction on top of Abraham/Raoult was found.

### Cited Findings
- **VIANA** (Queiroz, Bernardes, Ribeiro, Aguilera-Mercado, Nogueira; arXiv 2604.01365, 2026; also SSRN and a ScienceDirect journal version).
  - **Architecture.** Three GCN layers with mean/max pooling, concatenated with PCA-reduced POM embeddings (256-d reduced to 93 components at 95% variance) and physicochemical scalars (vapour pressure, log concentration). An MLP head with softplus outputs I_max, C (log concentration at half-max) and D (slope). Intensity is Ψ = I_max/(1 + e^(−(X − C)/D)).
  - **Data.** 209 molecules from the Wakayama 2019 Kao database. Synthetic dose-response curves (100 points per molecule) span threshold to saturation. The split is 80/10/10 by molecule.
  - **Results.**

    | Model | R² | Test MSE |
    |---|---|---|
    | VIANA (Hill + POM) | 0.996 | 0.19 |
    | Domain-informed Hill-only | 0.991 | 0.46 |
    | Character GCN (black-box + POM) | 0.881 | 23.47 |
    | Baseline GCN | 0.010 | 195.44 |

  - **Caveat.** The authors acknowledge that validation is bounded by the existing experimental landscape.
  - Sources: [arXiv HTML](https://arxiv.org/html/2604.01365); [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2666821126002243); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6545771)
- **Oliveira, Santana, Rodrigues, Ribeiro & Nogueira 2023** (Heliyon), "A framework for predicting odor threshold values of perfumes by scientific ML and transfer learning". Despite the "SciML" label, it embeds no mechanistic equation. A GCN trained on odour descriptors (273 molecules) provides 128-d embeddings to an FNN predicting ODT for 45 perfumery molecules.
  - Average MSE: 0.0179 (transfer), 0.0220 (Morgan fingerprints), 0.0218 (mean baseline).
  - The authors note that gains could come from the change of inputs, and that the approach was designed for limited data.
  - Source: [PMC10589844](https://pmc.ncbi.nlm.nih.gov/articles/PMC10589844/)
- **Wu, Wang & Yu 2026, "Safe Multitask Molecular Graph Networks for Vapor Pressure and Odor Threshold Prediction"** (arXiv 2601.16426).
  - **Data.** VP: 1,852 molecules, 9,260 temperature-dependent records. ODT: 1,042 molecule–medium records (598 air, 444 water).
  - **Model.** GINE/PNA backbones with temperature late-fusion and separate heads. The paper motivates the pairing causally: VP sets airborne concentration and ODT sets detectability.
  - **Scaffold-split results.**

    | Model | VP MSE | VP R² | ODT MSE |
    |---|---|---|---|
    | FP+MLP | 0.263 | 0.862 | — |
    | Single-task PNA | 0.210 | 0.901 | 0.598 |
    | Safe multitask | 0.208 | 0.904 | 0.605 |

  - **Conclusion.** Naive multitask training causes negative transfer.
  - Source: [arXiv 2601.16426](https://arxiv.org/html/2601.16426v1)
- **Physics-parameter predictors (release stage).**
  - GRAPPA is described as a hybrid GNN for pure-component vapour pressures — [ScienceDirect 2025](https://www.sciencedirect.com/science/article/pii/S266682112500047X). (Uncertain: whether it outputs Antoine-type parameters was not verified.)
  - GC²NN is a group-contribution-assisted graph convolutional network for vapour pressure — [GMD 18:7357 (2025)](https://gmd.copernicus.org/articles/18/7357/2025/)
  - A D-MPNN predicts vapour pressure — [ScienceDirect 2024](https://www.sciencedirect.com/science/article/abs/pii/S1876107024005844)
- **Physics-parameter predictors (transport stage, Abraham descriptors).**
  - kNN, group contributions and graph-convolutional networks were trained on Abraham's Absolv database — [ACS Environ Au 2026](https://pubs.acs.org/aeacc4/article/doi/10.1021/acsenvironau.6c00063/5232381/Prediction-of-Solute-Descriptors-for-Linear)
  - AbraLlama is an LLM-based predictor of Abraham descriptors — [Liquids 4(3):29](https://doi.org/10.3390/liquids4030029)
- **Pellegrino 2025 as a partial hybrid.** The primacy-coding mixture model (biophysical, RMSE 8.6) was nearly as good as the end-to-end DNN (RMSE 7.5). Mechanism-constrained mixture rules lose little accuracy — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- **Kao 2019 as a mechanistic backbone.** UNIFAC/Raoult for release and Stevens plus strongest-component for perception make a fully mechanistic staged chain — [Ind Eng Chem Res 2019](https://pubs.acs.org/doi/10.1021/acs.iecr.9b01225)

### Inferences
- Putting the mechanistic law in the output layer (VIANA) is the most clearly supported hybrid pattern. It makes curves monotonic and saturating by construction, and the reported gap to black-box models is large on small data. The reported R² is still an optimistic estimate: the targets are smooth synthetic curves from a fitted model, and the test set is about 21 molecules.
- ML-predicted physics parameters (P_sat, Abraham E/S/A/B/L, γ via UNIFAC groups) → mechanistic equation → residual learner is a natural grey-box stack. Its components exist individually, but no end-to-end olfaction implementation was found.

### Gaps
- No published Gaussian-process or neural residual correction of an Abraham or Raoult potency model in olfaction was found.
- No physics-informed neural network (PDE-constrained PINN) for nasal odorant uptake was found. CFD remains the tool used there.
- POM + Hill evidence is limited to VIANA. No independent replication was found.

---

## Q5. Variance explained by transport/volatility vs "receptor-specific" potency; outliers

### Takeaway
Transport and volatility properties account for about 75–77% of log-threshold variance (Abraham 2012; Rodríguez 2011). Much of the remaining about 23–25% is not measurement noise: the same framework explains 93–95% for trigeminal pungency. Structured residuals appear as super-potency in specific chemical classes: mercaptans/thiols, aldehydes, acids, unsaturated esters, and (by general knowledge) pyrazines. The strongest mechanistic evidence for receptor-set thresholds is Dewan 2018. No retrieved study reports a formal per-molecule residual analysis naming rotundone, β-damascenone or geosmin.

### Cited Findings
- **Odour vs pungency.** Transport-type solvation equations explain 77% for odour vs 93–95% for nasal pungency and eye irritation — [Abraham et al. 2001](https://dx.doi.org/10.1177/1420326X0101000320)
- **Threshold models.**
  - 353 ODTs: R² = 0.759, SD 0.819 log units. This required indicator variables for aldehydes, carboxylic acids, unsaturated esters and mercaptans (structured residuals) — [Abraham et al. 2012](https://academic.oup.com/chemse/article-abstract/37/3/207/325917)
  - Rodríguez 2011 (vapour pressure, water solubility, logKow): r² = 0.769 over 121 chemicals — [FFJ 2011](https://onlinelibrary.wiley.com/doi/abs/10.1002/ffj.2076)
- **Suprathreshold intensity.** Vapour pressure was the single most important feature (permutation p < 10⁻⁵). The 10-feature model also needed five non-transport chemoinformatic descriptors and a shape descriptor to reach r = 0.87 — [Pellegrino 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- **Odorous vs odorless.** Transport alone suffices, so reaching the receptors is the dominant barrier — [Mayhew 2022](https://www.pnas.org/doi/full/10.1073/pnas.2116576119)
- **Receptor-specific potency mechanisms.**
  - Copper-dependent thiol detection by OR2T11 — [JACS 2016](https://pubs.acs.org/doi/10.1021/jacs.6b06983)
  - Narrowly tuned OR2M3 for an onion thiol — [Chem Senses 2017](https://academic.oup.com/chemse/article/42/3/195/2549461)
  - Sulfur compounds as the lowest-threshold class of key food odorants — [JACS 2016](https://pubs.acs.org/doi/10.1021/jacs.6b06983)
  - The single most sensitive receptor sets the behavioural threshold — [Dewan 2018](https://www.biorxiv.org/content/10.1101/341099v1)
- **Specific ODT counter-example.** 2-Isobutyl-3-methoxypyrazine is detectable at about 0.01 nM despite typical OR EC50s in µM–mM — [search-indexed; PLOS CB 2018](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1006175)

### Inferences
- A useful decomposition: log(1/ODT) = [transport term, ~75% of variance] + [receptor-affinity residual] + [noise]. Inter-study ODT variability is commonly an order of magnitude or more. That is general knowledge, not quantified in retrieved sources here (see Gaps), so part of the 23% is surely noise.
- The residual is chemically clustered (thiols, pyrazines, specific aldehydes and esters), which argues for a receptor-aware or class-aware ML residual on top of a transport backbone.
- Rotundone, β-damascenone and geosmin are candidate test cases for large positive residuals, but their residuals under the Abraham or Rodríguez models were not retrieved. A pipeline should compute them explicitly and not assume them.

### Gaps
- No retrieved study computes residuals of a transport-only model for named super-potent odorants (rotundone, β-damascenone, geosmin, thiols) and attributes them quantitatively.
- The measurement-noise ceiling for ODT (between-lab SD) was not retrieved. Abraham's SD of 0.82 log units is the residual SD, not the noise floor.

---

## Q6. Recommended staged design (interfaces, data per stage, evaluation)

### Takeaway
Build a four-stage grey-box pipeline:
- **Release:** mechanistic, with ML supplying P_sat and γ.
- **Transport:** mechanistic, via Abraham descriptors and K_m/a.
- **Receptor/threshold:** an ML residual for receptor-specific affinity, optionally OR-informed.
- **Perception:** a Hill layer with ML-predicted EC50, n and I_max; primacy or strongest-component for mixtures.

Each stage outputs physically meaningful, unit-bearing quantities and is supervised by its own dataset. The design synthesises the cited sources; the component choices are inferences, not published results.

### Cited Findings (supporting the design choices)
- **Release (UNIFAC + modified Raoult) is validated** for perfume headspace and time-dependent diffusion — [Gomes 2008](https://ui.adsabs.harvard.edu/abs/2008AIChE..54..310G/abstract); [Teixeira 2013](https://aiche.onlinelibrary.wiley.com/doi/10.1002/aic.14106); [Wakayama 2019](https://pubs.acs.org/doi/10.1021/acs.iecr.9b01225)
- **GNN predictors exist for release and transport parameters.** VP on a scaffold split reaches R² ≈ 0.90 — [Wu et al. 2026](https://arxiv.org/html/2601.16426v1); [GC²NN](https://gmd.copernicus.org/articles/18/7357/2025/); [GRAPPA](https://www.sciencedirect.com/science/article/pii/S266682112500047X). Abraham descriptors — [ACS Environ Au 2026](https://pubs.acs.org/aeacc4/article/doi/10.1021/acsenvironau.6c00063/5232381/Prediction-of-Solute-Descriptors-for-Linear)
- **Transport-stage labels.** Abraham-equation ODT baseline — [Abraham 2012](https://academic.oup.com/chemse/article-abstract/37/3/207/325917). Mucosal solubility/uptake calibration — [Zhao 2004](https://academic.oup.com/chemse/article/29/9/763/271736)
- **Perception-stage labels.** Hill fits best — [Pellegrino 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/). Kao's 314 curves — [Wakayama 2019](https://pubs.acs.org/doi/10.1021/acs.iecr.9b01225). Hill-in-output-layer — [VIANA](https://arxiv.org/html/2604.01365)
- **Mixture rule.** Primacy model RMSE 8.6 vs DNN 7.5 — [Pellegrino 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/). Strongest-component rule — [Wakayama 2019](https://pubs.acs.org/doi/10.1021/acs.iecr.9b01225)
- **Receptor stage.** Threshold set by the most sensitive receptor — [Dewan 2018](https://www.biorxiv.org/content/10.1101/341099v1). OR EC50 distribution — [Bak 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC5983876/)

### Inferences (proposed design; not a published system)

**Stage 0: molecule to physics parameters (ML).**
- Outputs log P_sat(T), UNIFAC groups (deterministic) or a γ∞ estimate, Abraham descriptors {E, S, A, B, V, L}, logKow and water solubility, each with uncertainty.
- Data: VP sets (e.g., the 1,852-molecule set in Wu 2026), Absolv/Abraham descriptors.

**Stage 1: release (mechanistic).**
- C_gas,i = x_i·γ_i·P_i^sat/(RT), from UNIFAC plus modified Raoult. Add the Fick/diffusion or skin mass-balance model for time and distance profiles.
- Output: C_gas,i(t) in µg/L or ppb.
- Calibrate against measured headspace (GC-HS) where available.

**Stage 2: transport (mechanistic plus fitted coefficients).**
- log K_m/a from Abraham gas→water/biophase equations, with the Zhao 2004 correction that hydrophobics are more soluble than water predicts.
- Delivered dose at olfactory mucosa: C_eff = C_gas·g(K_m/a, D_m, flow).
- g can be a lumped 1–2-parameter uptake function fitted to CFD tables (Keyhani/Zhao). Pellegrino's "about 20% of ambient early in inhalation" can serve as a timing prior for mixtures.
- Output: C_eff (log M in mucus).

**Stage 3: receptor/threshold (hybrid).**
- log ODT_gas = log EC50_eff − log K_m/a − log g + δ_receptor.
- The transport part alone reproduces the Abraham/Rodríguez baseline (R² ≈ 0.76).
- δ_receptor is an ML residual, e.g. from a GNN/POM embedding or predicted min-EC50 over OR panels. It is trained on ODT residuals and regularised toward 0, so it activates only for structured outliers such as thiols and pyrazines.
- Data: Abraham 353 ODTs, Nagata, the 1,042 ODT records in Wu 2026, and OR EC50 panels.

**Stage 4: perception (Hill layer).**
- I(C) = I_max·C_eff^n/(C_eff^n + EC50_perc^n), with ML-predicted (EC50_perc, n, I_max) as in VIANA. Tie EC50_perc to ODT from Stage 3 through a shared latent, so that threshold and intensity stay consistent.
- Data: Pellegrino 62 odorants/434 points, Kao 314 curves (if accessible).
- Mixtures: primacy or strongest-component as the mechanistic default, with an optional DNN residual.

**Evaluation.**
- **Per-stage metrics against stage-specific labels:** VP R², headspace vs GC-HS, ODT SD in log units vs Abraham's 0.82 baseline, intensity RMSE vs Pellegrino's 7.1–7.2 LMS points.
- **Splits:** molecule- and scaffold-level, not point-level. VIANA's 80/10/10 over 209 molecules is small.
- **Ablations:** transport-only vs transport + δ_receptor. This directly measures "receptor-specific variance".
- **Residual audit** on named super-potent odorants (thiols, rotundone, β-damascenone, geosmin, IBMP).
- **External test** on GC-O / natural-aroma key-odorant identification; Pellegrino's benchmark is r = 0.55.
- **Consistency checks:** monotonicity, saturation, and the relation threshold ≤ EC50_perc.

### Gaps
- No published end-to-end system implements all four stages with learned parameters, so expected overall accuracy is unknown.
- Availability and licensing of the Kao 314-PRM curve data, the Nagata threshold tables, and machine-readable Abraham descriptors (Absolv is commercial/limited) were not verified.
- Individual variability (OR genotype) is outside this design. Dewan 2018 and the OR-genetics literature imply a per-person receptor stage would be needed for individual-level prediction; this was not researched here.
