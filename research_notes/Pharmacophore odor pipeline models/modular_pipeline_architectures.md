# Modular / cascaded / hierarchical ML architectures for olfactory property prediction

Scope note: research conducted September 2026. Where a claim comes from an automated
extraction of a PDF whose text layer was partly illegible, it is flagged **uncertain**.
No metric in this file is invented; anything I could not source sits in a Gaps list.

---

## Q1. Are odor thresholds systematically different across odor families / chemical classes, and do potency models improve when conditioned on class?

### Takeaway
Yes — functional-group class is one of the strongest single determinants of odor potency
(roughly 3.5 log units of spread in asymptotic potency between thiols and hydrocarbons),
and the best-known physicochemical threshold model (Abraham) only reaches acceptable fit
*after* adding class-specific indicator terms. That is direct, quantitative support for
conditioning a potency stage on chemical class; the evidence for conditioning on
*perceptual* odor family (as opposed to chemical class) is thinner and mostly indirect.

### Cited Findings
- Zarzo (2012, *Sensors*, 114 aliphatic compounds, model R² = 0.90) fits
  `pOL = [1 − exp(−k·n^1.4)] · pOL_max`, where `n` is the number of non-hydrogen atoms
  and **`pOL_max` is a per-homologous-series (per-functional-group) asymptote**. Reported
  asymptotes: thiols ≈ 9.5, aldehydes ≈ 8.5, carboxylic acids ≈ 8.5, thioethers ≈ 8.5,
  1-alcohols ≈ 7.7, 2-ketones ≈ 7.7, hydrocarbons ≈ 6.0 — i.e. ~3.5 log units between the
  most and least potent class at equal molecular size — [Zarzo, Sensors 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3355402/).
  *Caveat:* my extraction of that table also returned "esters ≈ 9.5", which is out of order
  with the stated potency ranking and with the ester literature; treat the ester value as an
  extraction artifact to be re-checked against the paper before use.
- The same work frames the class effect as an *interaction*: threshold improves with chain
  length but plateaus at a **functional-group-specific maximum**, so a single global
  size term cannot capture potency — [Zarzo, Sensors 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3355402/).
- Abraham's general solvation (LFER) equation
  `log VG0 = c + r·R2 + s·π2H + a·α2H + b·β2H + l·log L16` explains **93–95 %** of the
  variance for nasal pungency and eye irritation but **only ~77 %** for odour thresholds;
  the improved model adds **indicator factors for aliphatic aldehydes and carboxylic acids**
  plus a maximum-molecular-length term producing a potency cut-off for higher homologues —
  [Abraham et al., "A model for odour thresholds"](https://www.researchgate.net/publication/11520625_A_model_for_odour_thresholds);
  companion VOC paper: [Abraham, Gola, Cometto-Muñiz & Cain (2001), *Indoor + Built Environment*](https://dx.doi.org/10.1177/1420326X0101000320).
- Sulfur-bearing compounds are the potency outliers in classical panel data: of 53 odorant
  chemicals measured, sulfur compounds show thresholds "on the order of parts per billion"
  while most other classes sit far higher — [Odor Threshold Determinations of 53 Odorant Chemicals](https://www.tandfonline.com/doi/pdf/10.1080/00022470.1969.10466465).
- Within a single class the structure–potency surface is steep and non-monotonic: in
  homologous alkanethiols, thresholds are dominated by **steric effects**, with a potency
  minimum (i.e. threshold optimum) at **five to seven carbons**; the authors attempted
  3D-QSAR specifically because a global descriptor model did not capture this —
  [Structure–Odor Correlations in Homologous Series of Alkanethiols, *J. Agric. Food Chem.*](https://pubs.acs.org/doi/10.1021/jf506135c).
- Class-restricted ("local") threshold QSARs reach far higher fits than global ones:
  flavour-threshold QSARs reported R² = 0.978 for alcohols and R² = 0.987 for acids,
  versus the heterogeneous-set models below — [search synthesis over threshold-QSAR literature](https://link.springer.com/article/10.1007/s11030-017-9800-5).
  (The two R² values come from a search-engine synthesis of the alcohol/acid/ester QSAR
  literature rather than a paper I fetched directly — verify the primary source before
  citing the exact numbers.)
- Global, chemically heterogeneous threshold QSPR is the hard case: Monte-Carlo / CORAL-style
  QSPR has been built explicitly for "the large number of heterogenic chemicals", which the
  authors motivate by the failure of single-class models to generalise —
  [Molecular Diversity (2017)](https://link.springer.com/article/10.1007/s11030-017-9800-5);
  [Odor threshold prediction by Monte Carlo method, *Ecotox. Env. Safety*](https://www.sciencedirect.com/science/article/abs/pii/S0147651316303013).
- Descriptor-level potency structure also shows up in single-family QSAR work, e.g.
  sandalwood-odor α-campholenic derivatives modelled as a family in its own right —
  [J. Chem. Inf. Model.](https://pubs.acs.org/doi/abs/10.1021/ci020296n).
- Counterweight: in the only large ordinal-strength ML study, SHAP attributed strength
  mainly to **molecular weight, size and polarity** (mass-transport terms), and the authors
  did *not* find or use family-specific potency — 2,393 molecules, RDKit descriptors, 217
  features, no odor-family inputs — [Fichtelmann & Westermayr, *RSC Advances* 2026, DOI 10.1039/d6ra01805j](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/).

### Inferences
- The class effect is largely an **intercept/asymptote shift plus a class-specific size
  interaction**, not a wholesale change of mechanism. That is exactly the structure a
  conditional model captures cheaply: shared representation + class-conditioned offset and
  slope (a per-class bias/scale head, or class embedding concatenated before the regressor)
  rather than fully independent per-class regressors.
- Because Abraham needed indicator variables for *chemical* classes (aldehydes, acids) and
  Zarzo needed per-series asymptotes, a potency stage conditioned on **chemical class is
  better evidenced than one conditioned on perceptual odor family**. Perceptual family
  (musk, thiol-sulfurous, pyrazine-roasted, lactonic) correlates with chemical class, so an
  odor-quality conditioning signal is probably a noisy proxy for the chemical-class signal
  that actually carries the potency information — with the advantage that it is predictable
  from structure at ~0.89 AUROC and is continuous.
- The mass-transport SHAP result and the class-asymptote result are compatible: transport
  (MW, vapour pressure, logP) sets the *envelope*, receptor-class chemistry sets *where in
  the envelope* a series saturates. A potency model should therefore receive both
  transport features and a class/quality conditioning vector.

### Gaps
- I found **no paper that directly ablates "threshold model with class conditioning" vs
  "same model without"** on a common odor-threshold benchmark with scaffold splits. The
  Abraham indicator-term improvement (77 % → higher) is the closest thing, and I could not
  retrieve the exact post-indicator R² from a primary full text.
- No quantitative, citable ppt/ppb/ppb–ppm banding table for **musks, pyrazines and
  lactones** specifically. The ppb claim for sulfur compounds is sourced; the musk and
  pyrazine bands are widely repeated in flavour literature but I could not source them to a
  primary paper within this session, so they must not be stated as numbers in the report.

---

## Q2. Architecture options: hard cascade, soft cascade/stacking, MoE, hierarchical MTL, hurdle, conditional models

### Takeaway
The strongest *directly olfactory* evidence supports a **soft cascade / stacking design**:
take a quality-trained embedding and use it as the input to the potency model. Two
independent groups did this and both beat a structure-features-only baseline. The strongest
*general* molecular-ML evidence for learned modularity is TopExpert-style clustering MoE,
which improves exactly the metric that matters here (unseen-scaffold generalisation).

### Cited Findings
- **Soft cascade, olfaction, variant A (embedding → threshold FNN):** Oliveira et al.,
  *Heliyon* 9(10):e20813 (Oct 2023). A GCN is trained on semantic odor descriptors
  (273 molecules), its **128-dimensional embedding** is then the input to a feed-forward
  network that predicts odor detection thresholds (45 perfumery compounds, filtered from
  295). Transfer model average MSE **0.0179** vs Morgan/ECFP4 benchmark FNN **0.0220** and
  an arithmetic-mean baseline **0.0218**; 50/50 train/test with 60/40 train/val inside the
  training half — [Heliyon 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10589844/) /
  [publisher](https://www.cell.com/heliyon/fulltext/S2405-8440(23)08021-0).
  Note the mean baseline (0.0218) and the ECFP baseline (0.0220) are indistinguishable,
  so the ECFP baseline was effectively at chance: the transfer gain is real but the
  comparison is weak, and n = 45 makes the absolute numbers fragile.
- **Soft cascade, olfaction, variant B (POM → linear head):** in the Principal Odor Map
  paper, a **linear model on top of the POM embedding outperformed a chemoinformatic SVM
  baseline at predicting odor detection threshold**, evaluated on the Abraham et al. 2011
  threshold set (referenced as 353 thresholds). The paper does **not** report the numeric
  correlation for that comparison —
  [POM, *Science* 2023 / PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/);
  [Science](https://www.science.org/doi/10.1126/science.ade4401).
- **Geometric conditioning is explicit in POM:** the authors map tasks onto embedding
  geometry — vector length / projection magnitude ↔ **detectability (odor strength)**,
  vector distance ↔ similarity, projection onto a descriptor axis ↔ descriptor
  applicability — [POM/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/).
  This is the cleanest published statement that potency and quality live in one shared
  space and can be read off with different heads, i.e. an argument *for* joint
  representation + light task heads over disjoint per-stage models.
- **POM also uses a hard stage-1 gate:** the authors note they pre-screen molecules with
  no odor using "a separate, simpler model", but give **no metrics or training details**
  for that odorless screen — [POM/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/).
  So the canonical olfaction model already *is* a two-stage cascade (odorless gate →
  quality model), just an undocumented one.
- **Stage-1 physics is nearly separable from stage 2:** Mayhew et al. show three
  transport features — boiling point, vapour pressure and octanol/water logP — reliably
  classify molecules as odorous vs odorless, on the argument that a molecule must be
  volatile enough to reach air, hydrophilic enough to sorb into mucus, and hydrophobic
  enough to enter a receptor pocket — [Mayhew et al., *PNAS* 2022](https://www.pnas.org/doi/10.1073/pnas.2116576119).
  Their curated set has become a standard benchmark and later work builds "odorous
  background" datasets from their model — [review](https://www.sciencedirect.com/science/article/abs/pii/S0924224424003765).
- **MoE with learned clustering gate (TopExpert):** GNN + clustering-based gating module +
  multiple expert heads; the gate assigns molecules to topological groups via trainable
  centroids. Reported to win **35 of 40 cases** across 8 benchmark datasets and multiple
  GNN backbones, with the paper's headline claim being **better generalisation to
  molecules with unseen scaffolds** — [Kim et al., AAAI 2023](https://ojs.aaai.org/index.php/AAAI/article/view/26000),
  [arXiv:2302.13693](https://arxiv.org/pdf/2302.13693).
- **Other molecular MoE variants:** Mixture of Collaborative Experts
  ([arXiv:2312.03292](https://arxiv.org/pdf/2312.03292)) and ASE-Mol, an
  adaptive **substructure-aware** expert model ([arXiv:2504.05844](https://arxiv.org/pdf/2504.05844)).
  Substructure-aware gating is conceptually the closest match to "thiol expert / pyrazine
  expert / macrocyclic-musk expert" without hand-coding the classes.
- **Hurdle / zero-inflated framing is already implicit in the odor-strength labels:**
  Fichtelmann & Westermayr use a four-level ordinal scale whose lowest level **is
  "odorless"** (odorless / low / medium / high), 2,393 molecules, MLP + RF + XGBoost
  ensemble on 217 RDKit descriptors, **72 %** correct-class on the hold-out, macro-averaged
  MSE as the primary metric, best on "medium", worst on "low" (least prevalent), Cohen's
  κ = 0.83 / Krippendorff's α = 0.81 inter-annotator agreement, 80/20 split with repeated
  stratified 10-fold CV — [RSC Adv. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/).
- **Hurdle model mechanics (general statistics):** stage 1 is a binary
  presence/absence classifier, stage 2 models only the non-zero outcomes with a separate
  distribution; the two components **can be fit with completely different model classes**
  (e.g. GBDT classifier + gamma or neural regressor), and the explanatory variables are
  allowed different effects in each stage. Unlike Tobit, a hurdle model makes **no
  assumption about the outcome distribution below the detection limit**, which is the right
  choice when "odorless" is a true absence rather than a censored measurement —
  [Towards Data Science, Two-Stage Hurdle Models](https://towardsdatascience.com/two-stage-hurdle-models-predicting-zero-inflated-outcomes/);
  [pscl::hurdle docs](https://www.rdocumentation.org/packages/pscl/versions/1.5.9/topics/hurdle).
  A recent methods paper compares Tobit vs two-part hurdle for semicontinuous data and is a
  reasonable template for the "odorless vs censored threshold" decision —
  [arXiv:2608.09725](https://arxiv.org/pdf/2608.09725).
- **Unified end-to-end alternatives now exist in olfaction.** AROMMA (Kang, Kim, Park, Lee,
  Choi, So; arXiv:2601.19561, Jan 2026) claims one embedding space for single molecules
  *and* mixtures, trained jointly over Leffingwell/GoodScents-derived tasks, and explicitly
  positions itself as **avoiding separate specialised models** —
  [arXiv:2601.19561](https://arxiv.org/pdf/2601.19561). **Uncertain:** the PDF text layer
  extracted poorly; I could not recover its per-task metrics, exact task list, or whether
  thresholds/intensity were actually evaluated. Do not quote numbers from it.
- A general-purpose molecular **foundation model** is reported to transfer across diverse
  olfactory tasks with an encoder + task-specific heads, and the paper contains
  joint-multitask vs per-task comparison tables (Han, Wang, Mankodi, Yang, Tewari;
  arXiv:2608.25893, Aug 2026) — [arXiv:2608.25893](https://arxiv.org/pdf/2608.25893).
  **Uncertain:** same extraction problem; the direction and size of the multitask-vs-single-task
  result could not be read reliably and must be re-checked before the report relies on it.
- **Mixtures as a later stage (POMMix):** builds hierarchically — (1) GNN molecular
  embeddings, (2) attention to aggregate molecules into a mixture representation,
  (3) cosine prediction heads for perceptual distance — and reports state-of-the-art
  performance across multiple mixture datasets; explicitly leverages **mono-molecular**
  data to make mixture representations learnable despite scarce mixture labels —
  [OpenReview](https://openreview.net/forum?id=TYP85NdMtE);
  [Mach. Learn.: Sci. Technol.](https://iopscience.iop.org/article/10.1088/2632-2153/adfffc);
  [arXiv:2501.16271](https://arxiv.org/html/2501.16271v1).
- **Representation choice matters more than model family for quality:** GNNs beat
  traditional QSAR on multi-label odor prediction, best GCN macro-F1 **0.5193**, a **24 %**
  improvement over QSAR baselines — [Molecules 30(23):4605](https://www.mdpi.com/1420-3049/30/23/4605),
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/41375203/).

### Inferences
- The design space collapses to a practical ordering for this problem:
  **(1) hurdle stage-1 gate (odorous vs odorless) as a hard gate** — justified because the
  decision is nearly separable on transport features, the gate is the most accurate model
  in the stack, and "odorless" is a genuine absence, not censoring;
  **(2) shared quality encoder** trained on the 138-label set, kept as the backbone;
  **(3) potency as a conditioned head on that encoder** (soft cascade / stacking), fed
  quality logits or the embedding **plus** the transport descriptors, not a hard
  per-family regressor;
  **(4) MoE gating only if a monolithic conditioned head underfits** the known
  family-specific asymptotes.
- A hard cascade at stage 2→3 (predict family, then route to a family regressor) is the
  *worst* option on the available evidence: with ~1–2 k threshold labels, routing 138
  overlapping multi-label descriptors into disjoint regressors leaves each expert with tens
  of molecules — the regime where Oliveira's n = 45 fragility appears — while also
  importing hierarchical error propagation for no representational gain over a
  concatenated conditioning vector.
- POM's geometry result (length ↔ detectability) implies potency conditioning may need no
  extra parameters at all in the limit: a well-trained quality space already orders
  molecules by strength. A useful cheap ablation is therefore "‖POM vector‖ alone as a
  potency feature" as a baseline rung below the full conditioned head.
- Multi-label quality means a *soft* class vector, not a class id. Conditioning should be
  on the 138-dim probability vector (or a low-rank projection of it) so that a
  thiol-fruity molecule gets an interpolated, not an arbitrated, prior.

### Gaps
- No published head-to-head in olfaction of **hard cascade vs joint multitask vs MoE** on
  the same molecules and splits. Every comparison above is cross-paper and
  cross-dataset, so effect sizes are not commensurable.
- No MoE paper I found applies expert gating **to odor potency specifically**; TopExpert /
  ASE-Mol evidence is on general ADMET/QM-style benchmarks and must be transferred by
  analogy, with the caveat that those benchmarks are much larger than 1–2 k thresholds.

---

## Q3. Error propagation in cascades, and mitigation; evidence from other domains; local vs global QSAR

### Takeaway
Error propagation is the documented, named failure mode of top-down modular hierarchies,
and the literature's fixes are exactly the ones available here: don't commit to a single
path, pass soft scores rather than hard decisions, and hybridise with a flat/global model.
Independently, the local-vs-global QSAR literature is genuinely split, with a slight
overall tilt toward global models plus the warning that local models carry "pronounced
risk" — which argues against hard per-family experts as a default.

### Cited Findings
- In **Local Classifier per Parent Node (LCPN)** hierarchies, each internal node gets its
  own classifier trained only on examples in its subtree; during top-down prediction,
  "misclassifications at higher levels propagate errors affecting predictions at lower
  levels", and a parent-node mistake "can greatly affect the result" —
  [LCPN overview](https://www.emergentmind.com/topics/local-classifier-per-parent-node-lcpn-lcpc).
- Documented mitigations: **LCPN+** removes the constraint of predicting along a single
  hierarchy path, and **LCPN+F** harmonises local and **flat** classification to balance
  modularity against error propagation; in both, "error propagation, typically encountered
  in LCPN, is circumvented by not constraining test instances to follow a single path" —
  [Hierarchy Generation and Exploitation via Extended Local Classification Schemes, ACM](https://dl.acm.org/doi/fullHtml/10.1145/3651671.3651772).
- **Route/path confidence** is an established mitigation: evaluating the confidence of the
  whole route rather than each node independently for reliable hierarchical categorisation —
  [A Route Confidence Evaluation Method, arXiv:1206.0335](https://arxiv.org/pdf/1206.0335).
- Evaluation of hierarchical pipelines needs hierarchy-aware metrics, not flat accuracy —
  [Hierarchical confusion matrix for classification performance evaluation, arXiv:2306.09461](https://arxiv.org/pdf/2306.09461).
- **Local vs global QSAR — evidence against local:** a systematic evaluation of modelling
  strategies concluded that "a global modeling strategy is preferred over a local
  strategy", with local strategies showing "a pronounced risk and comparatively high
  computational cost" — [Evaluation of QSAR modeling strategies: local and global models, PubMed](https://pubmed.ncbi.nlm.nih.gov/20218538/).
- **Sheridan/Merck-style industrial comparison:** for off-target activities, global models
  calibrated on all tested compounds were compared against project-local models —
  [Global QSAR Models vs Selected Local Models as Predictors of Off-Target Activities, *J. Chem. Inf. Model.* 54(4):1083](https://pubs.acs.org/jcisd8/article-abstract/54/4/1083/939903/Global-Quantitative-Structure-Activity),
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/24628044/).
- **Evidence for local:** for bioconcentration factor, local models improved prediction
  quality in **97 %** of cases relative to comparable subsets of the global model —
  [SAR QSAR Environ. Res. 24(3)](https://www.tandfonline.com/doi/full/10.1080/1062936X.2012.762426).
- **Evidence for "it depends":** for ionic-liquid cytotoxicity, local and global predictive
  abilities were **similar**; local models were useful for mechanistic questions inside one
  group, global models recommended for newly designed compounds —
  [J. Mol. Liquids](https://www.sciencedirect.com/science/article/abs/pii/S0167732216328550).
- **Middle path already exists in QSAR:** hierarchies that combine global and local models
  automatically — [Automated QSAR with a Hierarchy of Global and Local Models](https://www.researchgate.net/publication/244483493_Automated_QSAR_with_a_Hierarchy_of_Global_and_Local_Models) —
  and local *lazy* regression, which builds a neighbourhood-specific model at prediction
  time instead of pre-partitioning chemical space —
  [Local Lazy Regression, *J. Chem. Inf. Model.*](https://pubs.acs.org/doi/10.1021/ci060064e).
  Local lazy regression is the closest QSAR analogue of a soft, per-query gate and avoids
  the brittle class boundaries of a hard cascade.

### Inferences
- Mapping the hierarchical-classification fixes onto this pipeline gives a concrete
  mitigation list: (a) never hard-argmax the family before the potency stage — pass the full
  soft vector (the "don't follow a single path" fix); (b) always keep a **flat/global
  potency model** in the ensemble and blend by confidence (the LCPN+F fix); (c) score the
  *route* — report calibrated joint confidence P(odorous) × P(family) × potency predictive
  interval rather than per-stage numbers (the route-confidence fix); (d) evaluate with
  hierarchy-aware, end-to-end metrics.
- The global-vs-local split is best read as a data-volume question: local wins where each
  subset still has enough labels (BCF), global wins where subsetting starves the model. With
  1–2 k noisy thresholds spread over many families, **the olfaction potency stage is in the
  regime where global-with-conditioning should beat local-per-family**.
- Stage-1 calibration matters asymmetrically. A false "odorless" permanently removes a
  molecule from the pipeline with no downstream chance of recovery, so the gate should be
  run at high recall for "odorous" with an explicit abstain band, and the gate's probability
  should be multiplied into downstream outputs rather than used as a filter during training.

### Gaps
- I found **no ADMET or tiered-toxicity paper quantifying end-to-end cascade error
  propagation** (e.g. "stage-1 AUROC 0.95 costs X in final RMSE") that I could cite
  directly; the propagation evidence is from hierarchical-classification methodology, not
  from a chemistry pipeline.
- I did not verify the *direction of the result* in the Sheridan 2014 J. Chem. Inf. Model.
  paper from its full text (abstract behind a wall in this session). The "global preferred"
  conclusion above is sourced to the separate 2010 strategy-evaluation paper, not to
  Sheridan; do not attribute it to Sheridan.

---

## Q4. Does multitask learning with odor-quality labels improve potency prediction? Negative-transfer risks

### Takeaway
Two olfaction studies show quality-label pretraining helps potency (POM linear head beating
an SVM baseline; Oliveira's descriptor-embedding transfer beating ECFP), but neither is a
strong experiment — one reports no numbers, the other has n = 45 and a chance-level
baseline. Meanwhile the general molecular-ML literature documents negative transfer
concretely enough that a joint model needs explicit safeguards.

### Cited Findings
- POM: a linear model on the quality-trained embedding **outperformed a chemoinformatic SVM
  baseline** on odor detection threshold (Abraham 2011 data, 353 thresholds referenced);
  **no correlation coefficients reported** for that comparison —
  [POM/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/).
- Oliveira et al.: descriptor-GCN embedding → threshold FNN, MSE **0.0179** vs ECFP4
  baseline **0.0220**; the authors' stated motivation is to "mitigate potential shortcomings
  brought on by the use of a relatively small dataset". They also flag the cascade's
  coverage limitation: the model can only predict thresholds for molecules for which odor
  descriptor information exists — [Heliyon 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10589844/).
- Fichtelmann & Westermayr's ordinal strength model (72 % accuracy, 2,393 molecules)
  used **RDKit descriptors only — no odor-family or descriptor labels as inputs** —
  [RSC Adv. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/). So the best current
  odor-strength model is an *unconditioned* baseline: the "does quality conditioning help
  strength?" ablation has, as far as I can tell, not been run on that dataset.
- Negative transfer mechanisms documented for molecular MTL: conflicting optimal
  representations forcing shared parameters into suboptimal compromises; **data imbalance**,
  where gradient updates are dominated by the large task and small tasks are starved; and
  gradient interference causing optimisation instability —
  [survey/synthesis of molecular MTL negative transfer](https://www.nature.com/articles/s42004-024-01169-4).
- Concrete negative-transfer instance: adding extra QM9 molecules that only have QM9
  properties available **hurt** performance, introducing noise that disrupted learning —
  [Exploring data augmentation: Multi-task methods for molecular property prediction, *Comput. Chem. Eng.*](https://www.sciencedirect.com/science/article/pii/S0098135425002571).
  This is the direct analogue of dumping ~5 k descriptor-only molecules into a joint model
  whose threshold head has ~1–2 k labels.
- Mitigations with published support: **adaptive checkpointing with specialisation (ACS)**
  for multi-task GNNs, to damp inter-task interference while keeping MTL benefits; **MoTSE**
  task-similarity estimation, reported to alleviate negative transfer on QM9 and PCBA —
  [transferability map, *Commun. Chem.* 2024](https://www.nature.com/articles/s42004-024-01169-4) /
  [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11024153/);
  [task-similarity-enhanced transfer, PubMed](https://pubmed.ncbi.nlm.nih.gov/36274947/).
- Task **hardness/relatedness can be quantified before committing** to joint training —
  [Quantifying the Hardness of Bioactivity Prediction Tasks for Transfer Learning, *J. Chem. Inf. Model.* 2024](https://pubs.acs.org/doi/10.1021/acs.jcim.4c00160) —
  and meta-learning frameworks exist specifically to mitigate negative transfer in drug
  design — [PubMed 41068285](https://pubmed.ncbi.nlm.nih.gov/41068285/).
- Ultra-low-data regimes have their own recommended practice, relevant to threshold and
  substantivity heads — [Molecular property prediction in the ultra-low data regime, *Commun. Chem.* 2025](https://www.nature.com/articles/s42004-025-01592-1).

### Inferences
- The safest reading of the olfaction evidence: **quality-label pretraining is a reliable
  win as a frozen-representation transfer (sequential/stacked), and an unproven win as
  simultaneous joint multitask training.** The two positive results are both of the frozen
  kind (train quality, then train a potency head on the embedding).
- The dataset shapes here (≈5 k quality, ≈1–2 k thresholds, 2,393 ordinal strength,
  ~few hundred with reliable Abraham-style thresholds) are precisely the imbalance profile
  the negative-transfer papers warn about. If joint training is attempted, it needs
  per-task loss weighting or gradient-conflict handling, and the ordering matters:
  pretrain on the big quality task, then fine-tune the potency head with the encoder mostly
  frozen or at a low learning rate.
- Because the ordinal-strength model (72 %) is a published, unconditioned baseline on a
  known dataset, the single most informative experiment available is to re-run it with
  predicted-quality conditioning added and report the delta under the same repeated-CV
  protocol. That is the missing ablation in the whole field, and it is cheap.

### Gaps
- **GraphNOSE / NOSE / OpenPOM:** I did not retrieve primary sources for these within this
  session, so I cannot confirm whether any of them trains threshold or intensity jointly
  with descriptors, nor their reported metrics. The AUROC ≈ 0.89 figures in the brief should
  be re-sourced before publication.
- No study I found reports a **negative** result for quality→potency transfer in olfaction,
  which given publication bias means the positive evidence should be discounted somewhat.

---

## Q5. Data-flow design: which datasets feed which stage, partial labels, and whole-pipeline evaluation

### Takeaway
Each stage has a different molecule set and a different label modality, so the pipeline is
inherently a partial-label problem; the workable pattern (used by POMMix) is to let the
data-rich mono-molecular tasks build the representation and let the scarce tasks attach
light heads, with one shared scaffold split defined once at the molecule level.

### Cited Findings
- Stage 1 (odorous/odorless): Mayhew et al.'s three transport features and their curated
  benchmark, now widely reused as the standard odorous/odorless set and as the source of
  "odorous background" datasets in later work —
  [PNAS 2022](https://www.pnas.org/doi/10.1073/pnas.2116576119);
  [review](https://www.sciencedirect.com/science/article/abs/pii/S0924224424003765).
- Stage 2 (quality): the GoodScents/Leffingwell union, ~5,000 molecules, single perceptual
  labelling task, is what POM was trained on; POM's prospective validation used **400 novel
  odorants** rated by a **15-person trained panel**, and the model's profile matched the
  panel mean better than the median panelist did —
  [POM/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/).
  Leffingwell is distributed via **pyrfume-data**, per AROMMA's data section —
  [arXiv:2601.19561](https://arxiv.org/pdf/2601.19561).
- Stage 3 (potency): the available threshold sets are small and heterogeneous —
  **Abraham et al. 2011 (353 thresholds** as referenced by POM)
  [POM/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/);
  Oliveira's perfumery subset **45 of 295 compounds**, taking the **lowest** reported
  threshold when several exist [Heliyon 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10589844/);
  Zarzo's **114** aliphatics [Sensors 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3355402/);
  Fichtelmann & Westermayr's **2,393**-molecule ordinal set drawn from Good Scents and
  PubChem, with κ = 0.83 agreement [RSC Adv. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/).
- Stage 4 (mixtures): POMMix's stated design premise is that **olfactory mixture data is
  limited**, so it leverages mono-molecular olfactory data to build mixture representations,
  aggregating molecule embeddings by attention —
  [MLST](https://iopscience.iop.org/article/10.1088/2632-2153/adfffc);
  [arXiv:2501.16271](https://arxiv.org/html/2501.16271v1).
- Scaffold generalisation is the metric that separates architectures: TopExpert's headline
  claim is better generalisation "for new molecules with unseen scaffolds" —
  [AAAI 2023](https://ojs.aaai.org/index.php/AAAI/article/view/26000).

### Inferences
- **Define one molecule-level scaffold assignment and reuse it across every stage.** Because
  the same molecule can appear in the odorless set, the quality set and the threshold set,
  per-stage independent splits leak: a molecule in stage-2 training can be in stage-3 test
  while the stage-2 model supplies its features. A single global scaffold→fold map,
  applied to all datasets, is the only way the reported end-to-end numbers mean anything.
- The "lowest reported threshold when several exist" convention (Oliveira) is a defensible
  but consequential choice; thresholds are the noisiest labels in the stack and the
  aggregation rule should be reported as a modelling decision, with a sensitivity check
  against using the median or a censored-likelihood treatment of inter-study spread.
- Partial labels are best handled by **masked multi-head losses** (each molecule
  contributes gradient only through the heads it has labels for) rather than by imputation;
  combined with per-head loss weights inversely proportional to label count, this is the
  standard countermeasure to the data-imbalance mechanism of negative transfer.
- End-to-end evaluation should report both the **oracle-conditioned** potency error (using
  true family/odorous labels) and the **pipeline** error (using predicted ones). The gap
  between them *is* the error-propagation cost, and reporting only the first is the most
  common way modular pipelines flatter themselves.
- GoodScents/Leffingwell licensing is research-only in practice; any downstream artefact
  that embeds those labels inherits that restriction. Worth stating explicitly in the
  pipeline's data card. (Licensing status asserted in the brief, not verified here.)

### Gaps
- **M2OR** (receptor-level mixture/odorant response data): not retrieved in this session;
  I cannot state its size, splits, or how it would attach to the pipeline.
- No source found for a published **end-to-end evaluation protocol** for a multi-stage
  olfactory pipeline — the field reports per-task metrics only, so the protocol above is
  my construction, not a citable standard.

---

## Q6. Later stages: longevity/substantivity, mixture perception, dose–response as the potency representation

### Takeaway
Stage 4+ is the least-served part of the pipeline: mixtures now have a credible
architecture (POMMix, hierarchical GNN→attention→cosine head) and 2026 work pushing toward
unified single-molecule/mixture embeddings, but I found **no sourced ML work on
substantivity/longevity prediction and none using Hill dose–response curves as the potency
output representation**.

### Cited Findings
- POMMix's three-level hierarchy — GNN molecular embeddings → attention aggregation into a
  mixture embedding → **cosine prediction heads** encoding perceptual distance — with
  state-of-the-art results across multiple mixture datasets, built on the explicit
  inductive biases (permutation invariance over components) of the problem —
  [OpenReview](https://openreview.net/forum?id=TYP85NdMtE);
  [MLST](https://iopscience.iop.org/article/10.1088/2632-2153/adfffc);
  [arXiv:2501.16271](https://arxiv.org/html/2501.16271v1).
- AROMMA (Jan 2026) targets one embedding space for molecules **and** mixtures, joint rather
  than modular — [arXiv:2601.19561](https://arxiv.org/pdf/2601.19561). **Uncertain**: task
  list and metrics not recoverable from the PDF.
- A general-purpose molecular foundation model reported to transfer across "diverse
  olfactory tasks" with encoder + task heads, Aug 2026 —
  [arXiv:2608.25893](https://arxiv.org/pdf/2608.25893). **Uncertain**: metrics not
  recoverable.
- The relevant physical anchor for longevity is the same transport axis that governs
  detectability: volatility/vapour pressure and logP appear in Mayhew's three-feature
  odorous/odorless model [PNAS 2022](https://www.pnas.org/doi/10.1073/pnas.2116576119),
  and molecular weight/size/polarity dominate SHAP for ordinal strength
  [RSC Adv. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/).
- Abraham's threshold model already contains a **cut-off effect** whereby potency falls off
  for higher homologues past a maximum molecular length —
  [A model for odour thresholds](https://www.researchgate.net/publication/11520625_A_model_for_odour_thresholds).

### Inferences
- Substantivity and detection threshold are partly the *same* physics read in opposite
  directions: high volatility helps detectability-in-air and hurts longevity. A joint head
  predicting both from a shared transport-aware representation is therefore a plausible
  place where multitask learning would genuinely help rather than interfere — the two tasks
  share features with opposite-signed coefficients, which is cooperative, not conflicting.
- Because thresholds are only the lower anchor of a dose–response curve, representing
  potency as **Hill parameters (EC50/threshold + slope + asymptote)** would let threshold
  data, ordinal strength data, and intensity dose–response data all attach to one
  parameterisation via different likelihoods — a principled way to pool the 353/114/2,393
  label sets instead of choosing one. I found no published instance of this in olfaction,
  so it is a design proposal, not a reported result.
- Mixture behaviour should sit *after* single-molecule potency in the pipeline and consume
  its outputs (per-component predicted threshold and quality) as inputs, which is
  structurally what POMMix's attention aggregation does over embeddings.

### Gaps
- **Good Scents substantivity hours as an ML target:** no paper found. I could not source
  any model trained on substantivity/longevity, nor any evaporation-model hybrid, so the
  report should state this as an open area rather than cite anything.
- **DREAM olfaction mixture challenge winners:** not retrieved in this session; no citable
  details on their architectures.
- **Hill / dose–response as a potency output head:** no olfactory ML paper found using it.

---

## Q7. Practical implementation: frameworks, compute, and concrete recommendations

### Takeaway
Nothing in this pipeline needs large compute — the binding constraint is label count, not
FLOPs — so the recommended build is a single shared GNN encoder with masked multi-head
losses plus a frozen-encoder stacked potency head, implemented with Chemprop/DeepChem-class
tooling and scikit-learn stacking for the tabular stages, with MoE reserved as a later
upgrade.

### Cited Findings
- Reference implementations for the quality stage are GNN-based and modest in scale: POM is
  a graph neural network trained on ~5 k molecules
  [POM/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/); the GNN-vs-QSAR comparison
  used standard GCNs and reported macro-F1 0.5193
  [Molecules 2025](https://www.mdpi.com/1420-3049/30/23/4605).
- The potency stage's best published performers are **tabular**: an MLP+RF+XGBoost ensemble
  on 217 RDKit descriptors reached 72 % on 4-class ordinal strength
  [RSC Adv. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/); Zarzo's R² = 0.90
  came from a 2-parameter nonlinear fit with a per-class asymptote
  [Sensors 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3355402/); Abraham's is a 6-term
  linear free-energy relationship
  [model for odour thresholds](https://www.researchgate.net/publication/11520625_A_model_for_odour_thresholds).
- Hurdle stages are explicitly framework-agnostic — "gradient boosting classifier for the
  first stage and gamma regression for the second, or logistic regression paired with a
  neural network, or any other combination" —
  [Two-Stage Hurdle Models](https://towardsdatascience.com/two-stage-hurdle-models-predicting-zero-inflated-outcomes/).
- TopExpert's cost is one gating module plus K expert heads on top of an existing GNN
  backbone, evaluated across multiple backbones and 8 datasets — i.e. an incremental add-on
  rather than a new training regime — [AAAI 2023](https://ojs.aaai.org/index.php/AAAI/article/view/26000),
  [arXiv:2302.13693](https://arxiv.org/pdf/2302.13693).
- Leffingwell data is available through **pyrfume-data** —
  [arXiv:2601.19561](https://arxiv.org/pdf/2601.19561).

### Inferences — concrete recommendation
1. **Stage 1 (odorous/odorless): hard gate, hurdle-style.** GBDT on transport features
   (boiling point, vapour pressure, logP) per Mayhew, plus a small descriptor set. Calibrate
   (isotonic/Platt), pick the operating point for high odorous-recall, add an abstain band,
   and propagate P(odorous) as a multiplicative factor into downstream outputs rather than
   deleting molecules.
2. **Stage 2 (quality): shared GNN encoder, 138 multi-label heads.** This is the
   data-richest task and therefore the representation owner. Train it first, alone.
3. **Stage 3 (potency): soft cascade, not hard routing.** Freeze (or low-LR fine-tune) the
   stage-2 encoder; concatenate [embedding ‖ 138-dim quality probabilities ‖ transport
   descriptors ‖ chemical-class indicators (thiol/sulfide, pyrazine/N-heterocycle, aldehyde,
   acid, lactone, macrocycle, nitro-musk, ester…)] and feed a GBDT **and** an MLP; blend.
   Include Zarzo-style structure as an inductive bias: a per-class asymptote term plus a
   size term, either as explicit features (class one-hot × size) or as a per-class
   bias/scale head. Rung-ladder of baselines to report: (a) transport descriptors only,
   (b) + chemical-class indicators, (c) + predicted-quality vector, (d) + POM-embedding,
   (e) ‖embedding‖ alone (the POM geometry baseline).
4. **Keep a flat global potency model always** and blend by route confidence (the LCPN+F
   lesson). Never let a family argmax gate the regressor.
5. **MoE later, not first.** Add a TopExpert/ASE-Mol-style gate only if the conditioned
   single head demonstrably underfits specific families in residual analysis; with ~1–2 k
   threshold labels, K experts each see far too little data to justify the default.
6. **Stage 4+:** mixtures via POMMix-style attention over stage-2/3 outputs;
   longevity/substantivity as a second head sharing the transport representation with
   potency (opposite-signed, cooperative); express potency as Hill parameters if intensity
   dose–response data is available, so all potency-like label types share one head.
7. **Tooling:** PyTorch Lightning for the encoder + masked multi-head losses (per-head
   masks for partial labels, per-head loss weights ∝ 1/√n_labels); Chemprop v2 multitask as
   the fastest path to a credible D-MPNN baseline; DeepChem for splitters and dataset
   plumbing; scikit-learn `StackingRegressor`/`Pipeline` for the tabular potency stage;
   pyrfume for data access; RDKit for the 217-descriptor block and scaffold assignment.
8. **Compute:** all published components here are ≤ ~5 k molecules with small GNNs and
   descriptor GBDTs — single-GPU or even CPU-feasible; budget effort for repeated
   scaffold-split CV and calibration, not for training throughput.
9. **Reporting discipline:** one global scaffold→fold map for every stage; report oracle-
   conditioned vs pipeline-conditioned potency error side by side; use hierarchy-aware
   metrics; report the threshold-aggregation rule (lowest vs median) and a sensitivity
   analysis.

### Gaps
- No source found benchmarking **Chemprop v2 multitask specifically on olfactory tasks**,
  so the framework recommendation is engineering judgement, not an evidenced ranking.
- No compute-cost figures (GPU-hours) are published for POM, POMMix, TopExpert or the
  ordinal-strength ensemble in what I retrieved; the "cheap" claim is inferred from model
  and dataset sizes, not measured.
- Two potentially decisive 2026 papers (AROMMA, arXiv:2601.19561; olfactory foundation
  model, arXiv:2608.25893) could not be read reliably — both would bear directly on
  "modular vs unified", and both should be re-fetched (HTML versions or published venues)
  before the report takes a position on end-to-end multitask superiority.
