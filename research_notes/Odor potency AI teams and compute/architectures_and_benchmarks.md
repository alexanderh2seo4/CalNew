# Model architectures for molecule→odor perception prediction, with emphasis on potency (threshold / intensity / strength), and small-data evidence

Research date: 2026-09-26. All metrics below are as reported by the cited source; nothing is
interpolated or estimated. Where a number I expected to find was not in the source, it is listed
under Gaps rather than guessed.

## Q1. Architecture families and their reported olfaction results

### Takeaway
Olfaction work clusters into five practically-used families: (a) descriptor/fingerprint + classical
ML or MLP, (b) Abraham LSER-style physicochemical linear models (the only family with a mechanistic
story for *thresholds* specifically), (c) 2D message-passing GNNs (POM / OpenPOM / Chemprop-style
D-MPNN), (d) graph transformers (GraphNOSE, 2026), and (e) pretrained sequence/graph foundation
models (ChemBERTa, MoLFormer, CheMeleon, MiniMol). On the *quality/descriptor* task, GNNs and graph
transformers lead; on the *potency* tasks (threshold, strength/intensity) the only head-to-head
evidence I found points the other way — RDKit-descriptor MLP/RF/XGBoost ensembles won on odor
strength, and POM's threshold result was a *linear head on frozen POM embeddings*, not an end-to-end
GNN.

### Cited Findings

**(c) 2D message-passing GNN — POM (Lee et al., Science 2023)**
- POM is an MPNN over molecular graphs; atoms featurized by valence, degree, hydrogen count,
  hybridization, formal charge, atomic number; bonds by degree, aromaticity, ring membership — [Science, POM](https://www.science.org/doi/10.1126/science.ade4401)
- The penultimate layer *is* the "principal odor map", **256 dimensions**; trained 150 epochs, Adam,
  LR decayed 5e-4 → 1e-5, batch size 128; hyperparameters tuned by Bayesian optimization over
  **1,000 trials**; cross-validated **AUROC = 0.89** on the odor-descriptor task — [PMC11898014 (POM full text)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- Rationale given for GNN over fingerprints: fingerprints "assign equal weight to all molecular
  fragments within a set bond radius", whereas a GNN can optimize fragment weights for the
  odor task — [Science, POM](https://www.science.org/doi/10.1126/science.ade4401)
- Human panel design: ~5,000 training molecules; 323 novel test molecules rated by ≥15 panelists;
  GNN beat the median panelist on 53% of molecules vs 41% for a count-fingerprint random forest;
  on "counterintuitive" structure-odor triplets the GNN was right 50% of the time while RF
  failed in 81% of cases — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- Per-chemical-class performance "relatively uniform" across esters, phenols, amines; strongest for
  sulfur-containing molecules (R = 0.52) — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)

**POM on potency specifically (the load-bearing datapoint for this project)**
- A **linear model on top of POM embeddings outperformed a chemoinformatic SVM baseline at predicting
  odor detection threshold**, using the Abraham et al. 2011 threshold dataset — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- The same transfer pattern held for odor applicability (Dravnieks, DREAM) and perceptual similarity
  (Snitz et al. 2013) — POM embeddings + simple head beat SVM baselines — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- Explicit limitation stated by the authors: "the concentration of an odor influences odor character,
  but is not explicitly included in the map" — i.e. POM is a *character* map, potency is bolted on — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)

**OpenPOM (the open reimplementation)**
- Multi-label classification over **138 odor descriptors** from SMILES; integrates with DeepChem — [openpom README](https://github.com/BioMachineLearning/openpom/blob/main/README.md)
- Custom featurizer: **134 node features** (hydrogen count, valence, formal charge, degree,
  hybridization, atomic number) and **6 edge features** (aromaticity, degree, in-ring) — [GraphNOSE, arXiv:2609.05694](https://arxiv.org/html/2609.05694)
- Uses a **10-model ensemble** trained on the POM/GS-LF dataset — [GraphNOSE, arXiv:2609.05694](https://arxiv.org/html/2609.05694)
- Two active forks exist: `ARY2260/openpom` (original replication) and `BioMachineLearning/openpom`
  (maintained; on PyPI as `openpom`) — [ARY2260/openpom](https://github.com/ARY2260/openpom), [PyPI openpom](https://pypi.org/project/openpom/)

**(d) Graph transformer — GraphNOSE (Sharma, Balaji, Parma, Kumar; arXiv:2609.05694v1, 4 Sep 2026)**
- Architecture: **4 GPS layers, hidden dim 64**; local pathway = GINE (GIN with edge features);
  global pathway = single-head attention; positional encodings from **GPSE** pretrained on molecular
  datasets; **~314K parameters total** — [arXiv:2609.05694](https://arxiv.org/html/2609.05694)
- Dataset: curated GoodScents–Leffingwell (GS-LF), **4,983 molecules**, up to 138 descriptors,
  heavily imbalanced (fruity = 1,902 molecules; garlic = 120) — [arXiv:2609.05694](https://arxiv.org/html/2609.05694)
- AUROC (%): GraphNOSE_trans **89.15 ± 0.08**; GraphNOSE_lin 89.02 ± 0.16; **OpenPOM 87.14 ± 0.57**
  (p = 0.003); LDM-GCN 86.91 ± 0.15; LDM-DMPNN 86.60 ± 0.25; **MoLFormer 84.97 ± 0.09**;
  **ChemBERTa 84.78 ± 0.04** — [arXiv:2609.05694](https://arxiv.org/html/2609.05694)
- Out-of-distribution (physicochemical-extreme split, 65:35): GraphNOSE 84.34% vs OpenPOM 80.84%
  (−3.50%, p < 0.001) — [arXiv:2609.05694](https://arxiv.org/html/2609.05694)
- **Low-data ablation**: GraphNOSE beat GNN baselines across 30–90% training-data fractions
  (p < 0.05 to p < 0.001), with the **largest margin at 30–50% of data** — [arXiv:2609.05694](https://arxiv.org/html/2609.05694)
- Binary mixtures, structure-disjoint 50:50 split: GraphNOSE_lin **77.96 ± 0.58%** AUROC (281K params)
  vs MPNN baseline 76.64 ± 0.06% (2M params), p = 0.008 — [arXiv:2609.05694](https://arxiv.org/html/2609.05694)
- Stated limitation: cannot distinguish enantiomers (non-isomeric SMILES) — relevant because
  enantiomer pairs differ in threshold by orders of magnitude — [arXiv:2609.05694](https://arxiv.org/html/2609.05694)

**(a) Descriptors/fingerprints + classical ML — and the key potency result**
- **Fichtelmann & Westermayr, RSC Advances 2026, DOI 10.1039/d6ra01805j** — ordinal *odor strength*
  (potency) of perfumery molecules: **2,393 molecules** (Good Scents 1,678 + PubChem 715), 4 ordinal
  classes (odorless / low / medium / high). Annotation reliability: Cohen's κ = 0.83,
  Krippendorff's α = 0.81 — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
- Encodings compared: RDKit descriptors (217), Morgan FP, MACCS keys, RDKit FP, topological torsion,
  atom pair, **ChemBERTa-2** (pretrained on 77M SMILES), **Chemprop** (D-MPNN), **CheMeleon**
  (pretrained Chemprop foundation model). Predictors: logistic regression, RF, XGBoost, MLP, and
  **CORAL** (ordinal-specific MLP head) — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
- **Winner: an ensemble of RDKit-descriptor MLP + Random Forest + XGBoost, 72% test accuracy**;
  primary metric macro-MSE; **no significant difference among the top four models**. Direct
  4-class prediction beat hierarchical two-step classification in 19 of 30
  descriptor×predictor combinations — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
- SHAP: molecular shape, size and polarity dominate — consistent with mass-transport/volatility
  limits on potency — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
- External validation on Keller et al. 2017 intensity ratings: predictions correlate with
  experimental intensity across dilutions 10⁻³ to 10⁻⁷ but **degrade at 10⁻¹ dilution** —
  concentration-dependent limitation — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
- Code/data: https://github.com/peter-fichtelmann/odor-strength and Zenodo
  10.5281/zenodo.17660448 — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
- **Wen, Cai & Li, Molecules 2025, 30, 4605** (GNN vs traditional QSAR, multi-label odor):
  GoodScent, **3,304 molecules**, 6 labels. Macro-F1: **GCN 0.5193**, GAT 0.5189, NNConv 0.4819,
  MLP 0.4766, GBDT 0.4732 → GCN +24.1% relative over best traditional (MLP). Compared RF, SVM,
  GBDT, MLP, XGBoost, LightGBM. Featurization: 25-d atom vectors, 6-d bond vectors; 64/16/20 split.
  Per-label **decision-threshold optimization was essential** (GAT gained 338.2% after threshold
  tuning; optimal thresholds consistently < 0.5) — [PMC12693603](https://pmc.ncbi.nlm.nih.gov/articles/PMC12693603/)
- Also in that paper: three feature-processing strategies for classical models — basic (2,692
  features), feature selection (12–33 features/label), PCA/kPCA. **Feature selection was best** for
  classical models — [PMC12693603](https://pmc.ncbi.nlm.nih.gov/articles/PMC12693603/)
- **Threshold regression with gradient boosting on fingerprints**: ECFP4–GBDT best for odor
  thresholds (**R² = 0.94, RMSE = 0.44**); ECFP6–GBDT best for aroma contribution (macro-F1 0.732,
  weighted-F1 0.912) — crop-aroma volatiles study — [PMC12654368](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12654368/) *(R²=0.94 is suspiciously high for threshold data; likely a random split on a narrow chemical space — treat as uncertain and do not use as a target)*
- **Sun, Jia & Xi (SSRN preprint)**: structure-based odor-detection-threshold model on **1,741
  compounds**, thresholds spanning 10⁻⁹ to 10⁸ mg/m³, **test R² ≥ 0.65**; a parallel MS²-spectrum-based
  threshold model on 932 compounds reached accuracy 0.81 — [SSRN 7070562](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7070562) *(preprint, not peer-reviewed — flag as uncertain)*

**(b) Abraham LSER / physicochemical linear models**
- Abraham's "A model for odour thresholds" (Chemical Senses 2002): odour detection thresholds
  analysed with a general selective-transport equation accounting for **~77% of the total effect**;
  the residual attributed to a specific size effect (possibly odorant-binding proteins) plus
  specific effects for aldehydes and carboxylic acids — [Chem Senses 27(2):95](https://academic.oup.com/chemse/article/27/2/95/351961)
- Descriptor set: air–water partition coefficient, dipolarity S, H-bond basicity B, and L
  (log air–hexadecane partition coefficient); the equations predict a **chemical cut-off** in odour
  detection along a homologous series and are intended to extrapolate to thousands of VOCs — [Chem Senses 27(2):95](https://academic.oup.com/chemse/article/27/2/95/351961)
- Companion work correlates/predicts nasal pungency, eye irritation and odour thresholds from the
  same solvation descriptors — [Abraham et al., Indoor Built Environ 2001](https://dx.doi.org/10.1177/1420326X0101000320)

**(f)/(i) Transfer learning onto thresholds**
- Heliyon 2023 "framework for predicting odor threshold values of perfumes by scientific ML and
  transfer learning": GCN trained on **273 molecules** for semantic descriptors, its embeddings fed to
  an FNN to predict thresholds for only **45 perfume molecules**. Average MSE: transfer learning
  **0.0179** vs generic-descriptor/ECFP4 benchmark 0.0220 vs arithmetic-mean dummy 0.0218 — [PMC10589844](https://pmc.ncbi.nlm.nih.gov/articles/PMC10589844/)
- That is the same architectural recipe as POM's threshold result: **freeze/reuse a
  descriptor-trained graph model, put a tiny head on it for potency.**

**(e) Pretrained foundation models**
- **CheMeleon** (Burns et al., arXiv:2506.15792): a ~10M-parameter foundation model that pretrains a
  **D-MPNN on classical molecular descriptors** (low-noise targets) instead of experimental or QM
  data. Follows Chemprop conventions: message-passing width **2048**, **6 message-passing
  iterations**, 8.7M params in the MP block, plus a 2-layer FFN → **12.9M total** — [arXiv:2506.15792](https://arxiv.org/abs/2506.15792), [github.com/JacksonBurns/chemeleon](https://github.com/JacksonBurns/chemeleon)
- **MiniMol** (arXiv:2404.14986): 10M params, pretrained on ~3,300 sparsely-defined graph- and
  node-level quantum + biological tasks — [arXiv:2404.14986](https://arxiv.org/abs/2404.14986)
- In GraphNOSE's olfaction benchmark, the two sequence foundation models were the **worst** entries
  (MoLFormer 84.97, ChemBERTa 84.78 vs OpenPOM 87.14) — [arXiv:2609.05694](https://arxiv.org/html/2609.05694)

**(g) Receptor-informed models**
- ~400 human ORs have been modelled with AlphaFold2 and docked against odorants; AlphaFold3 extends
  to ligands/cofactors — [Computational modelling of olfactory receptors (review)](https://www.sciencedirect.com/science/article/pii/S0304416525000704)
- Explicitly still an open problem: "the olfactory receptors linked to specific olfactory percepts
  are unknown, unlike in vision or taste" — [same review](https://www.sciencedirect.com/science/article/pii/S0304416525000704)
- Structure-based odor-*similarity* prediction via docking against human ORs has been demonstrated — [ACS Omega 2025, 10.1021/acsomega.5c04324](https://pubs.acs.org/doi/10.1021/acsomega.5c04324)
- A paper combining odorant structure **and** measured receptor activation profile to predict human
  perception exists (title: "Predicting human olfactory perception by odorant structure and receptor
  activation profile") — [ResearchGate record](https://www.researchgate.net/publication/388565768_Predicting_human_olfactory_perception_by_odorant_structure_and_receptor_activation_profile) *(only a metadata record retrieved; venue/metrics unverified)*

**(h) Mixtures**
- **POMMix**: extends POM to mixtures — GNN mono-molecular embeddings → **attention-based
  aggregation** across components → **cosine prediction head** encoding perceptual distance — [Tom et al., Mach. Learn.: Sci. Technol. (IOP) 2025](https://iopscience.iop.org/article/10.1088/2632-2153/adfffc); preprint [arXiv:2501.16271](https://awesomepapers.io/ai-for-science/papers/2501.16271)
- **2nd DREAM olfactory mixtures challenge**: 26 teams, 3 months, hidden test set of **46 mixture
  pairs**; ended in a **four-way tie**, so the organizers ensembled the **six** highest-scoring teams'
  predictions — the ensemble beat every individual submission and prior SOTA — [bioRxiv 2025.12.13.694160](https://www.biorxiv.org/content/10.64898/2025.12.13.694160.full.pdf)
- Blends/pairs work also exists in ACS Omega ("Deep Learning for Odor Prediction on Aroma-Chemical
  Blends") and arXiv:2312.16124 ("Olfactory Label Prediction on Aroma-Chemical Pairs") — [ACS Omega 4c07078](https://pubs.acs.org/doi/10.1021/acsomega.4c07078), [arXiv:2312.16124](https://arxiv.org/pdf/2312.16124)

### Inferences
- Every strong potency result I found is **embedding-plus-shallow-head**, not end-to-end deep
  regression: POM+linear on Abraham thresholds, GCN-embedding+FNN on 45 perfume thresholds,
  descriptor-MLP/RF/XGB ensemble on 2,393 strength labels. The graph model earns its keep as a
  *featurizer trained on the abundant descriptor labels*, then the potency head is deliberately
  low-capacity.
- Potency and quality are different problems: SHAP on the strength model surfaces size/shape/polarity
  (transport and volatility), which is exactly what Abraham's LSER equations encode. That argues
  for *concatenating* physicochemical/LSER-style features with learned embeddings rather than
  expecting a topological GNN to rediscover vapour pressure.
- GraphNOSE is currently the best-evidenced olfaction backbone (beats OpenPOM in-distribution, OOD,
  and in low-data ablations, at ~6× fewer parameters) but has only been evaluated on
  *multi-label descriptor* and *mixture* tasks — its potency performance is untested.
- The 3D/equivariant family (SchNet, DimeNet, PaiNN, Uni-Mol, POI-3DGCN) did not appear in any
  olfaction head-to-head I could retrieve; given the enantiomer-threshold problem this is a genuine
  open niche rather than a settled negative result.

### Gaps
- POM's exact number of message-passing layers, per-layer hidden dims, readout function, and
  ensemble size are in the Science supplementary material, which I could not retrieve; only the
  256-d embedding, 150 epochs, Adam schedule, batch 128, 1,000 HPO trials are confirmed. OpenPOM's
  concrete hyperparameter values are likewise not stated in retrievable docs.
- No retrievable quantitative metric for POM+linear vs SVM on Abraham thresholds — the source states
  "outperforms" without a number.
- Chemprop v2 D-MPNN default hyperparameters (depth, hidden size) were not directly verified in this
  session beyond what CheMeleon inherits (2048 width, 6 iterations).
- No head-to-head of 3D/equivariant GNNs (SchNet/DimeNet/PaiNN/Uni-Mol/POI-3DGCN) on any olfactory
  task was found.
- No LLM-fine-tuning or GPT-few-shot paper *on odor* was found; the only LLM-vs-classical evidence
  retrieved is on ADME/tox endpoints (see Q2).
- Could not access the Heliyon/ScienceDirect version (403) or the arXiv 2601.16426 paper named in the
  assignment — the latter did not surface in any search; I cannot confirm it exists.
- MolE, GROVER, MolCLR, Uni-Mol2, Graphormer: no olfaction-specific results found.

## Q2. Head-to-head evidence: classical ML vs GNN vs foundation models at small data

### Takeaway
The 2026 general-chemistry benchmarks are consistent and blunt: **RF/ExtraTrees on ECFP4 or RDKit
descriptors wins most endpoints at essentially all training sizes ≥1,000 compounds**, and the only
reliable way to beat them with a deep model is descriptor-pretraining (CheMeleon) rather than scale.
Olfaction is partly an exception — but only on the multi-label *quality* task, which has ~5,000
molecules and 138 correlated labels, i.e. an effectively multitask-rich regime that favours GNNs.

### Cited Findings
- **Guo et al., arXiv:2604.26498v2 (15 May 2026), "Do Larger Models Really Win in Drug Discovery?"**
  — 26 endpoints (6 ADME, 17 toxicity, 3 bioactivity), models: RF/ExtraTrees/GBDT on
  ECFP4/ECFP6/MACCS/RDKit; GCN, GAT, GIN, Ligandformer (10⁵–10⁶ params); ChemBERTa (77M),
  ChemBERTa2 (10M), MoLFormer (~47M); plus GPT5.5-SAR and Opus4.7-SAR rule libraries — [arXiv:2604.26498v2](https://arxiv.org/html/2604.26498v2)
  - "Across 156 fold mean comparisons, classical ML such as RF(ECFP4) and ExtraTrees(RDKit) win 116,
    GNNs such as GIN and Ligandformer win 25, pretrained sequence models such as MoLFormer and
    ChemBERTa2 win 12, and LLM based SAR baselines win three."
  - **Crossover size**: classical ML dominates at all training sizes ≥1,000 compounds; the *only*
    exception is at **500 compounds** on anti-TB activity where MoLFormer briefly leads
    (PR-AUC 0.291 vs 0.281 for RF), and the ordering reverses again by 1,000 compounds.
  - Split matters more than architecture: random CV → ML wins 48/52; **structure-separated CV →
    ML/GNN reach parity** on ADME and bioactivity. Median PR-AUC drop going to scaffold-style splits:
    ML −0.208 to −0.263, GNN −0.153 to −0.212 (i.e. **GNNs degrade less**).
  - Conclusion quoted: "Compact specialized models remain highly effective... Larger models add value
    for SAR interpretation and reasoning in low data settings, but predictive performance depends on
    the fit among model, task and validation scenario, not on scale alone."
- **CheMeleon (arXiv:2506.15792)** — Polaris (reported as 58 benchmarks in one place, 28 tasks in
  another; see Gaps): **CheMeleon 75% win rate, Random Forest 68%, fastprop 36%, vanilla Chemprop
  32%**; MiniMol 71%. MoleculeACE: **CheMeleon 97% win rate overall and 100% on activity-cliff
  subsets**, vs RF 50% and MiniMol 40% — [arXiv:2506.15792](https://arxiv.org/abs/2506.15792)
  - The authors frame the motivation explicitly as deep learning's "inability to outperform classical
    machine learning methods when tested on practical, real-world benchmarks with limited training
    data" — [arXiv:2506.15792](https://arxiv.org/abs/2506.15792)
  - Note the ordering: **vanilla Chemprop (32%) is far *worse* than RF (68%)**; the identical
    architecture with descriptor pretraining goes to 75%. Pretraining, not architecture, is the lever.
- **MolGraphBench (Gupta et al., arXiv:2602.20573v3, 18 Jun 2026)** — GCN/GAT/GraphSAGE/GIN plus
  fingerprint-fused variants (…-FP) vs Linear/SVM/RF/XGBoost on 1024-bit ECFP4. Datasets: FreeSolv
  642, ESOL 1,028, B3DB 1,058, RT 1,400, Lipophilicity 4,200 — i.e. **exactly the 0.6–4.2k range of
  interest** — [arXiv:2602.20573v3](https://arxiv.org/html/2602.20573v3)
  - Best RMSE: B3DB GCN 0.518; ESOL GraphSAGE 0.762; FreeSolv **GIN-FP 1.022**;
    Lipophilicity GraphSAGE 0.629; RT GIN (MAE 63.783).
  - Fingerprint fusion was **non-complementary overall** and helped **only on FreeSolv, the smallest
    dataset** — "fingerprints help only when training data is severely limited."
  - Recommendation for <5,000 molecules: **GraphSAGE and GCN best in absolute terms**; GCN and GIN
    better efficiency trade-off. No 3D/equivariant models included.
- Contradiction to flag: MolGraphBench favours simple GNNs at 0.6–4.2k, while Guo et al. favour
  RF/ExtraTrees above 1k on 26 mostly-classification endpoints. The datasets, task types
  (regression vs classification) and splits differ, so these are not strictly comparable — treat
  "GNN vs RF at ~1–5k" as **genuinely unsettled**, decided per-dataset. — [arXiv:2602.20573v3](https://arxiv.org/html/2602.20573v3); vs [arXiv:2604.26498v2](https://arxiv.org/html/2604.26498v2)
- Polymer graph pretraining study: RF beat a **pretrained wD-MPNN** when finetuning on 0.4% and 0.8%
  of the data, and the RF advantage **vanished as dataset size grew** — [arXiv:2506.18194](https://arxiv.org/pdf/2506.18194)
- On small sets such as CROW, "traditional machine learning methods such as Random Forest and FNN are
  quite competitive and even outperform modern GNN architectures such as ESAN and HM-GNN" — [Hierarchical Grammar-Induced Geometry, arXiv:2309.01788](https://arxiv.org/pdf/2309.01788)
- A hybrid concatenating a GNN graph-level embedding with a 1024-bit ECFP4 fingerprint is reported to
  consistently beat standalone GNNs with **RMSE improvements of 7–29%** — [Graph Neural Networks vs Random Forests (PatSnap Eureka report)](https://eureka.patsnap.com/report-graph-neural-networks-vs-random-forests-predictive-accuracy) *(commercial aggregator, not a primary source — low confidence, and it appears to conflict with MolGraphBench's "non-complementary" finding)*
- **Tabular foundation models for in-context prediction of molecular properties (arXiv:2604.16123)** —
  representation matters more than the tabular model: "CheMeleon-derived embeddings and 2D descriptor
  sets showed stronger results than Morgan fingerprint variants, suggesting that the gains of tabular
  foundation models are not representation-agnostic but depend strongly on sufficiently expressive
  molecular features." Reported MiniMol at 19/58 wins (32.8%), average rank 11.43 on combined
  Polaris+MoleculeACE — [arXiv:2604.16123](https://arxiv.org/html/2604.16123)
- Also surfaced but not fetched, potentially relevant to ~1–5k noisy labels with UQ:
  **Monroe: A Molecular Foundation Model for In-Context Probabilistic Inference** (arXiv:2608.18982) — [arXiv:2608.18982](https://arxiv.org/html/2608.18982)
- Olfaction-specific head-to-heads, collected in one place:
  - Quality/descriptor task, ~4,983 molecules: graph transformer 89.15 > OpenPOM MPNN 87.14 >
    GCN 86.91 > D-MPNN 86.60 > MoLFormer 84.97 > ChemBERTa 84.78 (AUROC %) — [arXiv:2609.05694](https://arxiv.org/html/2609.05694)
  - Quality task, 3,304 molecules / 6 labels: GCN 0.5193 > GAT 0.5189 > NNConv 0.4819 > MLP 0.4766
    > GBDT 0.4732 (macro-F1) — [PMC12693603](https://pmc.ncbi.nlm.nih.gov/articles/PMC12693603/)
  - **Potency/strength task, 2,393 molecules: RDKit-descriptor MLP + RF + XGBoost ensemble wins at
    72% accuracy, beating Chemprop D-MPNN, CheMeleon and ChemBERTa-2 — though the top four models
    were not significantly different** — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
  - Threshold task: POM embedding + linear head > chemoinformatic SVM (Abraham 2011 data) — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)

### Inferences
- The single most transferable pattern across Guo 2026, CheMeleon and the polymer study: at ~1–5k
  labels the *representation* decides the outcome, and a descriptor-pretrained or descriptor-fed
  model is the safe bet. Architecture novelty is second-order.
- The olfaction/general discrepancy is explained by label structure, not by chemistry: the winning
  GNN results are all **multi-label with 6–138 correlated targets** (implicit multitask
  regularization on ~3–5k molecules), whereas potency is a **single noisy scalar** — which is the
  regime where RF/descriptor models win in every general benchmark. This predicts descriptor+tree/MLP
  baselines will be very hard to beat on a single potency target at 1–5k, and that the way to win is
  to reintroduce multitask structure (train jointly with the 138 descriptor labels, or use frozen
  POM/CheMeleon embeddings).
- Fichtelmann's "no significant difference among the top four models" is the most honest signal in
  the whole literature for this project: at ~2.4k noisy potency labels the architecture choice is
  within noise, so effort is better spent on label curation, ordinal/censored loss design, and
  ensembling than on backbone selection.
- Guo et al.'s split finding (GNNs lose less under structure-separated CV) matters if the deployment
  goal is novel chemotypes rather than interpolation — it is an argument for keeping a GNN in the
  ensemble even if it loses on random-split CV.

### Gaps
- CheMeleon's Polaris benchmark count is reported inconsistently across retrieved summaries
  ("58 benchmarks" in one, "28 tasks" in another, and a combined Polaris+MoleculeACE "58 tasks"
  elsewhere). I could not reconcile these from the abstract alone — the win-rate numbers should be
  re-checked against the paper body before quoting.
- Deng et al. 2023 *Nat Commun*, "A systematic study of key elements underlying molecular property
  prediction", did not surface in my searches; I have **no verified findings** from it.
- No Polaris or TDC leaderboard page was fetched directly, so all leaderboard-style numbers here are
  second-hand from the CheMeleon/tabular-FM papers.
- No olfaction dataset appears in Polaris/TDC/MoleculeACE as far as I could determine, so none of the
  general benchmarks test potency-like olfactory endpoints.
- The "hybrid GNN+ECFP4 improves RMSE 7–29%" claim comes only from a commercial aggregator and
  directly conflicts with MolGraphBench; do not rely on it.

## Q3. Uncertainty quantification and censored-label support per architecture

### Takeaway
Chemprop-family D-MPNNs have the best off-the-shelf UQ menu (ensembles, MVE, evidential with
total/epistemic/aleatoric split, plus calibration), but **raw evidential and ensemble uncertainties
are documented to be systematically miscalibrated**, so post-hoc calibration is mandatory. Censored
labels (odor thresholds are routinely reported as ">" or "<" and as ranges) are **not** a first-class
Chemprop feature — the working implementation is the Tobit-loss family in the UQ4DD repo.

### Cited Findings
- Chemprop's documented UQ methods include **MVE, ensemble, and evidential (total / epistemic /
  aleatoric)** — [Chemprop UQ docs](https://chemprop.readthedocs.io/en/main/uncertainty.html)
- **Censored regression labels**: "Enhancing Uncertainty Quantification in Drug Discovery with
  Censored Regression Labels" adapts ensemble-based, Bayesian and Gaussian models to learn from
  censored labels using the **Tobit model from survival analysis**; five extended models plus two
  baselines — [arXiv:2409.04313](https://arxiv.org/abs/2409.04313); published version [Artificial Intelligence in the Life Sciences (S2667318525000042)](https://www.sciencedirect.com/science/article/pii/S2667318525000042)
- Reference implementation: **UQ4DD** handles temporal splitting, probabilistic labels, **and censored
  labels** — [github.com/MolecularAI/uq4dd](https://github.com/MolecularAI/uq4dd)
- Recommended decomposition from that work: a **Gaussian Ensemble** of k MVE models — mean of
  predictions as the point estimate, **variance across members = epistemic**, mean of predicted
  variances = **aleatoric**; epistemic is obtainable from both the Gaussian Ensemble and the
  evidential model — [arXiv:2409.04313](https://arxiv.org/abs/2409.04313)
- Calibration warning (2026): "Raw uncertainty estimates from deep evidential regression and deep
  ensembles are systematically miscalibrated" — DER conflates data noise with model uncertainty;
  ensembles are **sharper but underconfident** — [Garain et al., Chem. Eur. J. 2026, 10.1002/chem.202503299](https://chemistry-europe.onlinelibrary.wiley.com/doi/10.1002/chem.202503299?af=R)
- Distribution-shift behaviour of UQ methods has been evaluated temporally — [Temporal Evaluation of UQ Under Distribution Shift](https://link.springer.com/chapter/10.1007/978-3-031-72381-0_11)
- Architecture-specific UQ in the olfaction papers: OpenPOM's own answer is a **10-model ensemble** — [arXiv:2609.05694](https://arxiv.org/html/2609.05694); GraphNOSE reports ± standard deviations over seeds (e.g. 89.15 ± 0.08) rather than predictive UQ — [arXiv:2609.05694](https://arxiv.org/html/2609.05694)
- Ordinal-aware modelling as a partial substitute for censoring: the odor-strength paper used
  **CORAL** (ordinal MLP) and **macro-MSE** as the primary metric so that misclassifying by two
  ordinal steps is penalized more than one — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)

### Inferences
- For a potency model, the practical stack is: k-member **MVE ensemble with a Tobit/censored
  likelihood**, then post-hoc calibration on a held-out set. Nothing in the literature indicates a
  tree-based model gives comparable aleatoric/epistemic separation, so if censored-aware UQ is a
  requirement it argues for keeping a neural head (over descriptors or over frozen embeddings)
  rather than a pure RF/XGBoost solution — a descriptor-input MLP gets you Tobit + MVE while keeping
  the descriptor representation that wins on potency.
- Because odor thresholds are collated from heterogeneous sources spanning ~17 orders of magnitude
  (10⁻⁹–10⁸ mg/m³ in the Sun et al. set), aleatoric noise is label-source-dependent; an MVE/Gaussian
  head that can learn heteroscedastic variance is more defensible than a single RMSE objective.

### Gaps
- I found **no evidence of a Tobit / censored-regression loss in Chemprop itself** (v2 docs list MVE,
  ensemble, evidential only). Whether a community PR exists is unresolved — treat "Chemprop supports
  censored labels" as **unsupported**.
- No paper was found applying censored-regression losses to *odor threshold* data specifically.
- MC-dropout support in current Chemprop v2 was not confirmed in the retrieved docs.
- No calibration numbers (ECE, NLL, miscalibration area) were extracted for any olfaction model.

## Q4. Recommended architecture stack for ~1,000–5,000 noisy potency labels

### Takeaway
The evidence supports a **descriptor-first, embedding-augmented, shallow-head, ensembled** stack:
RDKit/Mordred descriptors plus Abraham-style physicochemical terms concatenated with frozen
pretrained embeddings (CheMeleon and/or a POM/OpenPOM-style olfaction model), fed to a small
MLP with an ordinal or Tobit-censored heteroscedastic head, ensembled ~10×, with an
RF/XGBoost-on-descriptors model kept in the ensemble and as the honesty baseline.

### Cited Findings (the specific results this recommendation rests on)
- The only direct potency head-to-head at this data scale chose **RDKit-descriptor MLP + RF +
  XGBoost ensemble** over Chemprop, CheMeleon and ChemBERTa-2 (2,393 molecules, 72% accuracy),
  with the caveat that the top four were statistically indistinguishable — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
- Both successful threshold-transfer results used a **frozen graph model + tiny head**:
  POM embeddings + linear model beat a chemoinformatic SVM on Abraham 2011 thresholds — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/); GCN-descriptor embeddings + FNN beat ECFP4 and a dummy regressor on 45 perfume thresholds (MSE 0.0179 vs 0.0220 vs 0.0218) — [PMC10589844](https://pmc.ncbi.nlm.nih.gov/articles/PMC10589844/)
- Descriptor pretraining is what makes a D-MPNN competitive at small data: vanilla Chemprop 32% →
  CheMeleon 75% Polaris win rate, vs RF 68% — [arXiv:2506.15792](https://arxiv.org/abs/2506.15792)
- Classical ML wins 116 of 156 fold-mean comparisons and dominates at ≥1,000 training compounds — so
  a descriptor/tree baseline is not a formality, it is the model to beat — [arXiv:2604.26498v2](https://arxiv.org/html/2604.26498v2)
- Keep a GNN in the ensemble for extrapolation: GNNs lose **less** accuracy than classical ML when
  moving from random to structure-separated splits (median PR-AUC drop −0.153/−0.212 vs
  −0.208/−0.263) — [arXiv:2604.26498v2](https://arxiv.org/html/2604.26498v2)
- If a GNN backbone is used on olfaction data, the current best-evidenced choice is a **GPS graph
  transformer with GINE local + attention global pathways, 4 layers, hidden 64, GPSE positional
  encodings (~314K params)**, which beat OpenPOM in-distribution, OOD, on mixtures, and by the
  largest margin at 30–50% training data — [arXiv:2609.05694](https://arxiv.org/html/2609.05694)
- At <5,000 molecules on regression, simple GNNs (GraphSAGE, GCN) were best in MolGraphBench, and
  fingerprint fusion helped only on the smallest set (642 molecules) — [arXiv:2602.20573v3](https://arxiv.org/html/2602.20573v3)
- UQ/censoring: Gaussian (MVE) ensemble for aleatoric/epistemic separation, Tobit likelihood for
  ">" / "<" thresholds, mandatory post-hoc calibration — [arXiv:2409.04313](https://arxiv.org/abs/2409.04313), [uq4dd](https://github.com/MolecularAI/uq4dd), [Chem. Eur. J. 2026](https://chemistry-europe.onlinelibrary.wiley.com/doi/10.1002/chem.202503299?af=R)
- Physicochemical prior worth encoding explicitly: Abraham's selective-transport equation already
  explains ~77% of odour-threshold variance from 4–6 solvation descriptors, and predicts the
  homologous-series cut-off — [Chem Senses 27(2):95](https://academic.oup.com/chemse/article/27/2/95/351961); independently, SHAP on the 2,393-molecule strength model surfaced size/shape/polarity as the dominant features — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)
- Multitask/auxiliary structure is what makes deep models shine in olfaction: the GNN wins are all on
  6–138-label tasks at 3–5k molecules — [PMC12693603](https://pmc.ncbi.nlm.nih.gov/articles/PMC12693603/), [arXiv:2609.05694](https://arxiv.org/html/2609.05694)
- For threshold/potency as an ordinal or interval target, ordinal-specific heads (CORAL) and
  macro-MSE metrics are already in use on olfactory potency — [PMC13182554](https://pmc.ncbi.nlm.nih.gov/articles/PMC13182554/)

### Inferences (the recommendation itself — reasoning, not sourced fact)
- **Tier 1 (must build, is the baseline to beat):** RDKit + Mordred descriptors, plus explicit
  Abraham/LSER-adjacent terms (log P, vapour pressure proxies, H-bond acidity/basicity, McGowan
  volume), into RF and XGBoost/LightGBM/CatBoost, with feature selection (the Molecules 2025 paper
  found selection beat PCA and raw for classical models). Report this honestly; in three of the four
  relevant benchmarks it is within noise of anything fancier.
- **Tier 2 (the actual model):** concatenate those descriptors with **frozen** embeddings — CheMeleon
  (descriptor-pretrained D-MPNN, the only deep model with a documented small-data win over RF) and a
  frozen olfaction embedding (256-d POM/OpenPOM, or a GraphNOSE-style GPS encoder trained on the
  ~5k GS-LF descriptor labels) — into a small MLP (≤2 hidden layers) with a heteroscedastic
  (MVE) output and a Tobit/interval-censored likelihood. Freeze rather than fine-tune at 1–5k labels;
  both successful threshold papers froze.
- **Tier 3 (squeeze):** multitask co-training — train the potency head jointly with the 138 GS-LF
  descriptor labels so the 1–5k potency labels are regularized by the ~5k quality labels. This is
  the mechanism that explains why GNNs win the quality task and lose the potency task, so it is the
  highest-expected-value experiment.
- **Ensemble ~10 members** (matching OpenPOM's own choice) across seeds *and* model families
  (descriptor-tree + descriptor-MLP + embedding-MLP). Stack with a simple average or a
  ridge meta-learner fitted with nested CV.
- **Validation discipline:** report both random-split and scaffold/structure-separated CV; the
  architecture ranking flips between them (Guo et al.), and a random-split-only result on 1–5k
  noisy potency labels is close to meaningless. Also hold out whole homologous series to test the
  Abraham cut-off behaviour.
- **Do not** start with: end-to-end fine-tuned SMILES transformers (worst entries in the olfaction
  benchmark), 3D/equivariant GNNs (no olfaction evidence, and conformer generation adds noise at
  this scale), or LLM few-shot (3/156 wins in the only benchmark that tested it). Revisit
  3D/stereo-aware models only if enantiomer-resolved threshold labels are a deliberate target —
  that is the one place where 2D graph and SMILES models provably cannot work (GraphNOSE's own
  stated limitation).
- **Label engineering probably beats architecture here.** Thresholds are censored, span ~17 orders of
  magnitude, and are pooled across incompatible measurement protocols; an ordinal/interval
  formulation with per-source noise terms is likely worth more than any backbone swap, given that
  the one careful potency study found its top four architectures statistically tied.

### Gaps
- No published study trains an odor-potency model on 1–5k labels with a censored-aware loss, so the
  Tier-2/Tier-3 recommendations are extrapolated from adjacent domains rather than demonstrated on
  odor thresholds.
- No source quantifies how much frozen-POM-embedding transfer helps vs descriptors *on the same
  threshold dataset* — POM vs SVM and Fichtelmann's descriptors vs CheMeleon are different datasets
  and different tasks, so they cannot be combined into a single ranking.
- Which public threshold corpus to train on is unresolved from these sources: Abraham 2011
  (hundreds of compounds, exact n unverified), Sun et al. 1,741 compounds (preprint), and
  vendor/GoodScents strength labels (2,393, ordinal) are not mutually calibrated.
- CatBoost specifically was not evaluated in any olfaction paper retrieved.
