# Compute and data requirements for molecule → odor-potency models

Scope: how much compute (and data) is needed to train a molecule→odor-potency model
(odor detection threshold / perceived intensity) to "reasonable" accuracy, grounded in
disclosed training costs, plus concrete hardware/cost budgets. Current as of
September 2026. All arithmetic is shown; every estimate I derived myself is marked
**[my estimate]**, and figures I could not verify against a primary source are marked
**[uncertain]**.

Headline framing for the report writer: **on 1,000–5,000 molecules with ~0.6–0.8 log
label noise, this problem is data-limited and noise-limited, not compute-limited.**
Every model class in scope except large-scale pretraining fits in single-GPU-hours to
single-GPU-days. The only genuinely expensive items are (a) pretraining a foundation
model from scratch — which you should not do, because open checkpoints exist — and
(b) physics-based 3D/vapour-pressure features and LLM-based literature extraction,
both of which are data-building costs, not model-training costs.

---

## Q1. Disclosed training compute per approach

### Takeaway
Disclosed compute for the actual odor models is close to zero by modern standards
(single GPU, minutes to hours); the large numbers all sit in *pretraining* of
general-purpose molecular foundation models (MoLFormer-XL ≈ 1,920 V100-GPU-hours;
ChemBERTa-2 ≈ 480 T4-GPU-hours; Uni-Mol2 on a 64×A100-80GB cluster), and in
hyperparameter search (Lee et al.'s POM used 1,000 Bayesian-optimization trials ×
5 CV folds). Fine-tuning any of these checkpoints on 1–5k molecules is a
minutes-to-low-hours job on one consumer GPU.

### Cited findings

**Lee et al. 2023 POM (Google Research / Osmo, Science)**
- Training set: "approximately 5,000 molecules with multiple odor labels each," curated
  from GoodScents and Leffingwell — [Lee et al. 2023, PMC copy](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- Hyperparameter search: "tuning over 1,000 trials" with Vizier (Google's Bayesian
  optimizer); the 80% training set was "further subdivided into 5 cross-validation
  splits" — [Lee et al. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- Training protocol: Adam, LR decaying 5e-4 → 1e-5, **150 epochs, batch size 128**,
  weighted cross-entropy; best architecture selected by mean CV AUROC = 0.89 —
  [Lee et al. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- **No hardware, wall-clock time, or compute cost is disclosed anywhere in the paper or
  the supplement I could reach** — [Lee et al. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- Prospective validation: model beat the median panelist on 53% of 323 test molecules
  vs 41% for a random-forest baseline — [Lee et al. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- (Note: this is the *odor-quality/descriptor* model, not a potency/threshold
  regressor. It is the best-documented compute reference point in olfaction ML, but
  the target is multi-label classification over 138 descriptors.)

**OpenPOM (open replication)**
- 4,983 molecules, curated by merging GoodScents and Leffingwell PMP 2001; predicts
  138 odor descriptors with a D-MPNN; ships as a **10-model ensemble**; training runs
  for **30 epochs** in the reference script; explicitly supports CPU-only inference
  ("If you do not have GPU support (CUDA), ensure the models are set to load on CPU") —
  [OpenPOM README](https://github.com/BioMachineLearning/openpom/blob/main/README.md)

**Chemprop / D-MPNN**
- Chemprop v2 is "about a factor of 2" faster in execution time and uses "a factor of
  3" less memory than v1; it scales to multiple GPUs — [Chemprop v2, JCIM 2025](https://pubs.acs.org/doi/10.1021/acs.jcim.5c02332)
- Official guidance: "for small datasets (~1000 molecules), it is possible to train
  models within a few minutes on a standard laptop with CPUs only" — [Chemprop v2 paper/preprint](https://chemrxiv.org/doi/pdf/10.26434/chemrxiv-2025-4p1nr)
- Hardware guidance: on GPU, train *without* caching (build graphs on the fly in
  parallel); on CPU, caching is preferable for medium datasets with few cores —
  [Chemprop docs](https://chemprop.readthedocs.io/en/latest/tutorial/cli/train.html)
- Hard measured numbers (fastprop paper, all on **one Dell Precision laptop with an
  NVIDIA Quadro RTX 4000 GPU + Intel Xeon E-2286M CPU**) — [Burns & Green, fastprop, arXiv:2404.02058](https://arxiv.org/html/2404.02058v3):
  | Dataset | Size | Chemprop | fastprop (descriptors + MLP) |
  |---|---|---|---|
  | ARA | ~0.8k | **16 min 55 s** | 1 min 54 s (of which 1 min 39 s = descriptor calc) |
  | Flash | ~0.6k | **5 min 44 s** | 30 s (13 s descriptors) |
  | YSI | ~0.4k | **7 min 02 s** | 42 s |
  | PAH | ~0.06k | **1 min 16 s** | 1 min 43 s (1 min 31 s descriptors) |
  | Fubrain | ~0.3k | — | 39 s (31 s descriptors) |
- fastprop is "typically ten times quicker on smaller datasets" than Chemprop on GPU,
  but "this advantage disappears on CPU due to the larger network size" —
  [fastprop](https://arxiv.org/html/2404.02058v3)

**Descriptor-based models (XGBoost / RF / Mordred / RDKit)**
- Mordred computes **1,613 descriptors per molecule** in the CheMeleon setup —
  [CheMeleon, arXiv:2506.15792](https://arxiv.org/abs/2506.15792)
- Measured Mordred cost (from the fastprop table above): ~1 min 39 s for ~800
  molecules → **≈0.12 s/molecule single-process**. → 10,000 molecules ≈ 1,240 s ≈
  **21 min on one core-bound laptop process**, and it parallelizes trivially across
  cores. **[my estimate, derived from the fastprop timings; strongly dependent on
  molecule size — aroma chemicals are small, so this is a conservative upper bound]**
- CheMeleon authors describe descriptors as "deterministic, low-noise, and
  computationally inexpensive to generate for any valid molecular structure" but give
  no timing — [CheMeleon](https://arxiv.org/abs/2506.15792)
- Best published odor-threshold regressors are tree ensembles on fingerprints:
  ECFP4–GBDT reached R² = 0.94, RMSE = 0.44 on −log10[mg/L] thresholds —
  [Predictive Models of Odor Contribution and Thresholds, PMC12654368](https://pmc.ncbi.nlm.nih.gov/articles/PMC12654368/)
  (flagged: this R² is far above the 0.77–0.83 range in the brief and above my
  noise-ceiling estimate below — likely a different target definition, unit
  transformation, or a non-independent split; treat with suspicion, see Q3)
- A second ODT study reports Extra Trees / RF / Bagging external R² = 0.814 / 0.802 /
  0.784 with RMSE = 0.816 / 0.841 / 0.878 — [same source](https://pmc.ncbi.nlm.nih.gov/articles/PMC12654368/).
  These are consistent with the brief's 0.66–0.93 RMSE band.

**Foundation-model pretraining costs (the expensive tier)**
- **MoLFormer-XL**: pretrained on 1.1 billion SMILES using "up to 16 V100 GPUs"; IBM
  reports algorithmic optimizations (linear-attention + length-bucketed SMILES) raised
  per-GPU throughput from 50 to 1,600 molecules, letting them use 16 GPUs "instead of
  1,000," consuming "61 times less energy," with "a trained model in five days" —
  [IBM Research blog](https://research.ibm.com/blog/molecular-transformer-discovery), [IBM/molformer repo](https://github.com/IBM/molformer)
  - Arithmetic: 16 GPUs × 5 days × 24 h = **1,920 V100-GPU-hours**. At a V100-class
    rental of ~$0.80–1.50/h that is **≈$1,500–2,900**. **[my arithmetic; rental rate
    is an assumption — V100s are largely off current price cards]**
- **ChemBERTa-2**: "Pretraining with 77M compounds requires multi-GPU resources,
  converging in approximately 5 days on 4×T4 nodes" — [ChemBERTa-2, arXiv:2209.01712](https://arxiv.org/abs/2209.01712)
  - Arithmetic: 4 × 5 × 24 = **480 T4-GPU-hours**; at ~$0.30–0.50/h for T4-class that
    is **≈$145–240**. **[my arithmetic; rate assumed]**
- **Uni-Mol2**: scaled to **1.1B parameters** pretrained on **800M conformations**;
  trained on "a computational cluster comprising **64 NVIDIA A100 GPUs**, each with
  80 GB HBM2, interconnected via Nvidia InfiniBand at 400 Gbps"; model sizes swept
  84M → 1.1B params; +27% average improvement on QM9, +14% on COMPAS-1D —
  [Uni-Mol2, arXiv:2406.14969](https://arxiv.org/abs/2406.14969), [NeurIPS 2024 proceedings PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/53923bb44655a7defb31c7744c01b62b-Paper-Conference.pdf)
  - Wall-clock is not in the abstract/summaries I retrieved (see Gaps). *If* the 1.1B
    run took one week: 64 × 168 = **10,752 A100-hours** → at RunPod A100-PCIe $1.39/h =
    **≈$14,900**. **[speculative: the one-week duration is my assumption, not a
    disclosed figure]**
- **CheMeleon**: D-MPNN pretrained on **1 million PubChem molecules** to regress 1,613
  Mordred descriptors; **12.9M total parameters** (8.7M in the message-passing net),
  hidden dim 2048, 6 message-passing steps. **GPU type, GPU count and wall-clock
  pretraining time are not stated in the paper** — [CheMeleon, arXiv:2506.15792](https://arxiv.org/abs/2506.15792), [repo](https://github.com/JacksonBurns/chemeleon)
  - Usable as a one-flag fine-tune: install Chemprop ≥2.2.0 and pass
    `--from-foundation CheMeleon` — [CheMeleon repo](https://github.com/JacksonBurns/chemeleon)
  - **[my estimate]** A 12.9M-param D-MPNN over 1M molecules for a handful of epochs is
    in the **low tens of GPU-hours** on one A100 — i.e. this entire foundation model is
    reproducible for ~$30–100, in sharp contrast to MoLFormer/Uni-Mol2. That makes it
    the only foundation model in scope whose *pretraining* is within a single-GPU budget.
- **MiniMol**: 10M parameters, pretrained on ~3,300 graph- and node-level tasks over
  ~6M molecules and ~500M quantum and biological labels — [MiniMol repo](https://github.com/graphcore-research/minimol), [ICML 2024 listing](https://icml.cc/virtual/2024/35909).
  No compute disclosure found (see Gaps).

**Fine-tuning and LLM fine-tuning costs**
- LoRA/QLoRA on a 7–8B model, single A100: reported real runs include Llama 3.1 8B on
  15,000 instruction-response pairs for a **total of $8.32** on a rented A100 80GB, and
  guidance that a 10k-sample instruction tune finishes "in under 2 hours" on an A100
  40GB at $1.20/h (**$2.40**) — [io.net fine-tuning budget guide](https://io.net/blog/llm-fine-tuning-budget-guide-gpu-costs-timelines-and-what-to-spend), [RunPod QLoRA guide](https://www.runpod.io/articles/guides/how-to-fine-tune-large-language-models-on-a-budget)
  **[uncertain: these are vendor/blog figures, not peer-reviewed; but multiple
  independent sources agree on the $2–20 order of magnitude]**
  - Arithmetic for our case: 5,000 molecules × ~300 tokens/example ≈ 1.5M tokens per
    epoch; 3–5 epochs ≈ 5–8M tokens. At 8B params and ~2,000 training tok/s on one
    A100 for LoRA, that is ~40–65 min → **<$3 per run**. **[my estimate]**
- Fine-tuning MoLFormer / ChemBERTa / CheMeleon / Uni-Mol on 1–5k labels: no paper in
  my search disclosed fine-tuning wall-clock. **[my estimate]** These are
  ≤100M-parameter encoders over ≤5k short sequences; a full fine-tune is **1–15 minutes
  per run on one consumer GPU**, so the dominant cost is the *number* of runs (see Q4's
  hyperparameter-search arithmetic), not any single run.

**3D / conformers / physics features**
- GFN2-xTB single-point geometry optimization: "approximately 1 second" for a
  representative molecule; full conformational search 20–27 minutes per molecule; a
  flexible 65-atom organic took "about 5–8 hours" on 24 cores —
  [xTB TADF benchmark, arXiv:2511.00922](https://arxiv.org/html/2511.00922v1)
- CREST (metadynamics + GFN2-xTB) is the expensive regime: "metadynamics remains
  expensive, requiring thousands of CPU hours per molecule" for hard cases; measured
  macrocyclic-peptide CREST runs on 14 cores averaged 2.3 h (4-mers), 5.8 h (5-mers),
  13.9 h (6-mers) — [CREMP, arXiv:2305.08057](https://arxiv.org/pdf/2305.08057)
- A hybrid xTB-based workflow is "a computational cost reduction of over 99% compared
  to conventional TD-DFT" — [arXiv:2511.00922](https://arxiv.org/html/2511.00922v1)
- Arithmetic for 5,000 aroma chemicals: xTB optimization only (1 s/molecule) ≈
  **1.4 core-hours total — free**. Full CREST-style conformer searching at 25 min each
  = 125,000 min ≈ **2,080 core-hours ≈ 87 days serial, ≈2.7 days on 32 cores**.
  **[my arithmetic; aroma chemicals are far smaller/less flexible than the peptides in
  the CREMP benchmark, so the true cost is likely at the low end or below]**

### Inferences
- The *published* odor models were all trainable on a single GPU. The expensive part of
  Lee et al. was search, not training: 1,000 Vizier trials × 5 CV folds = **5,000 model
  fits**. At ~5,000 molecules / batch 128 ≈ 39 steps/epoch × 150 epochs ≈ **5,850 steps
  per fit**, i.e. a few minutes on a modern accelerator → **≈250–400 GPU-hours for the
  whole search** (5,000 fits × 3–5 min). **[my estimate — this is the single most useful
  reconstructed number in these notes: the flagship olfaction paper's total compute is
  roughly one A100-fortnight, i.e. ~$350–800 at 2026 spot rates.]**
- Replicating OpenPOM end-to-end (10-model ensemble × 30 epochs × 4,983 molecules) is
  **well under 1 GPU-hour** by the fastprop-measured Chemprop rates (~17 min for ~800
  molecules includes repeated folds; per-model-per-epoch cost here is seconds).
  **[my estimate]**
- For a potency regressor on 1–5k molecules, **descriptor + GBDT is the compute-optimal
  baseline by a wide margin**: descriptors for 5k molecules ≈ 10 min on CPU, and an
  XGBoost/RF fit on a 5k × ~2,000 matrix is seconds; a 200-trial Optuna sweep with
  5-fold CV = 1,000 fits × ~2 s ≈ **35 min on a laptop**. **[my estimate]**

### Gaps
- Lee et al. 2023 disclose no hardware or wall-clock. Google/Osmo used internal TPU/GPU
  infrastructure; there is no public figure to cite.
- Uni-Mol2's wall-clock pretraining duration (and therefore total A100-hours) was not in
  the abstract, blog post, or proceedings summary I could retrieve; only the 64×A100-80GB
  cluster spec is disclosed.
- CheMeleon and MiniMol disclose no pretraining hardware or time at all.
- No source found for DFT/COSMO-RS vapour-pressure cost per molecule. Order-of-magnitude
  expectation (COSMO-RS requires a BP86/TZVP COSMO single point per conformer, typically
  ~minutes to ~1 h of CPU per small molecule) is **unverified in this session** and should
  not be reported as sourced.
- No source found for RDKit ETKDG conformer-generation throughput per molecule.
- Chemprop v2's paper reports relative speedups but I found no absolute
  molecules/second or per-epoch throughput table.

---

## Q2. Scaling evidence: is this data-limited or compute-limited?

### Takeaway
Molecular-property error follows a power law in *training-set size* with exponents
around −0.5 (occasionally toward −1), so cutting RMSE meaningfully requires
multiplying the dataset, not the FLOPs; and the 2025–2026 literature repeatedly finds
that pretraining *scale* transfers weakly or inconsistently to small downstream tasks,
with random forests still winning in the lowest-data regimes. For 1–5k noisy odor
labels the binding constraint is data (and label quality), not compute.

### Cited findings
- Generalization error follows ε(m) ∝ α·m^β with **β = −0.5 or −1** across domains, and
  "most works show power-law generalization error scaling with exponent βg = −0.5 or −1"
  — [Hestness et al., Deep Learning Scaling is Predictable, arXiv:1712.00409](https://arxiv.org/pdf/1712.00409); [The Shape of Learning Curves: a Review, arXiv:2103.10948](https://arxiv.org/pdf/2103.10948)
- Learning curves have "three primary learning regions: small-data, power law, and
  **irreducible error**"; the power-law exponent is "an indicator of the difficulty for
  models to represent the data generating function" — [Learning Curves for Drug Response Prediction, arXiv:2011.12466](https://arxiv.org/pdf/2011.12466)
- In chemistry specifically, "errors for most molecular property models decay with
  roughly the same slopes," and the power law is "confirmed for both neural networks and
  kernel models on molecular datasets spanning 6 orders of magnitude" —
  [Ab initio machine learning in chemical compound space, arXiv:2012.07502](https://arxiv.org/pdf/2012.07502)
- **Frey et al. 2023, "Neural scaling of deep chemical models" (Nat Mach Intell)**: varied
  model and dataset size over many orders of magnitude, up to >1B parameters and 10M
  datapoints; for chemistry language models the scaling exponent relating pretraining loss
  to model size was **≈0.17** at the largest dataset size, i.e. **each doubling of model
  size cuts pretraining loss by only ~11%**; loss improved monotonically with no plateau —
  [Nature Machine Intelligence](https://www.nature.com/articles/s42256-023-00740-3), [ChemRxiv preprint](https://chemrxiv.org/doi/10.26434/chemrxiv-2022-3s512)
- Uni-Mol2 characterized "power-law correlations between validation loss and model size,
  dataset size, and computational resources" from 84M to 1.1B params, with gains on QM9
  (+27%) and COMPAS-1D (+14%) — [arXiv:2406.14969](https://arxiv.org/abs/2406.14969).
  Note both are *large, low-noise, computed-label* datasets — the opposite of our regime.
- Counter-evidence on transfer to small data: molecular foundation models "often fail to
  consistently outperform strong classical baselines such as random forests or gradient
  boosting tree models trained on fixed molecular fingerprints," being "prone to
  overfitting and sensitive to hyperparameter choices" —
  [Benchmarking Robust Fine-Tuning with Molecular Graph Foundation Models, arXiv:2509.00614](https://arxiv.org/pdf/2509.00614)
- "In very low labeled data regimes, random forest models have been observed to
  outperform pretrained deep learning models... However, the advantage of the random
  forest model vanishes as the dataset size increases" — [arXiv:2509.00614](https://arxiv.org/pdf/2509.00614)
- Reported in 2026 surveys of molecular language-model scaling: "increasing model size
  beyond 15 million parameters was detrimental to property prediction performance on
  average," and scaling 32M → 300M gave only "modest improvements on average"; Lourie et
  al. (2025) caution that "scaling laws are unreliable for downstream tasks" —
  [Unveiling Scaling Behaviors in Molecular Language Models, arXiv:2601.22757](https://arxiv.org/html/2601.22757v1)
- Data *diversity* beats data *size* for chemical language models —
  [Diversity Beats Size Scaling for Chemical Language Models, PMC13439062](https://pmc.ncbi.nlm.nih.gov/articles/PMC13439062/)
- The one clear positive: CheMeleon (1M molecules, 12.9M params, descriptor targets)
  beats Random Forest, fastprop and vanilla Chemprop on 58 Polaris tasks (75% win rate
  vs RF 68%, fastprop 36%, Chemprop 32%) and wins 29/30 MoleculeACE assays (100% on
  activity-cliff subsets vs RF 67%) — [CheMeleon, arXiv:2506.15792](https://arxiv.org/abs/2506.15792).
  Its stated mechanism is that descriptor targets are "free from the confounding effects
  of label noise," i.e. the win comes from *pretraining-target design*, not scale.

### Inferences
- **Arithmetic on the data requirement.** Assume the power-law regime with β = −0.5 (the
  common chemistry value). To halve RMSE you need 4× the data; to go from RMSE 0.8 → 0.6
  (a 25% cut) you need (0.8/0.6)² ≈ **1.8× the data**, i.e. ~2,000 → ~3,600 molecules;
  0.8 → 0.5 needs 2.56× ≈ 5,100 molecules. Compute for any of those fits is unchanged
  (minutes). **This is the core quantitative argument that the project is data-limited.**
  **[my arithmetic on a sourced exponent]**
- Frey's 0.17 model-size exponent means that even in the pretraining-loss regime where
  scale *does* help, going 10× bigger buys ~30% lower loss — and none of that is
  guaranteed to survive the transfer to a 2,000-molecule noisy regression head. Combined
  with arXiv:2601.22757's "beyond 15M parameters was detrimental," **the expected value of
  spending compute on bigger models here is close to zero**.
- Practical corollary: the highest-leverage "compute" spend is **not** model scale but
  (i) LLM/literature extraction to grow the labelled set, and (ii) many cheap
  fits — ensembling, repeated scaffold splits, and uncertainty estimation — which are
  embarrassingly parallel and individually seconds-to-minutes.

### Gaps
- I found no published learning curve *specifically for odor detection threshold or
  odor intensity* (error vs N molecules). This would be the single most decision-relevant
  missing experiment, and it is cheap to run in-house (subsample 200/400/800/1600/3200,
  10 repeats, GBDT + Chemprop — hours on a laptop).
- I did not verify a 2024–2026 paper titled "Scaling laws for molecular foundation
  models" as a distinct work; the closest verified items are Frey 2023, Uni-Mol2 (2024),
  ChemFM (Nature Comm Chem 2025, 3B params / 178M molecules), the GNN-scalability
  NeurIPS 2024 paper, and arXiv:2601.22757 (2026).
- MolE: no source retrieved in this session; do not cite it as evidence.

---

## Q3. Accuracy ceiling under label noise, and definition of "reasonable"

### Takeaway
With experimental noise SD σ ≈ 0.6–0.8 log10 and a target spread of roughly 1.5–2 log10
SD, the irreducible RMSE is ≈σ and the maximum achievable R² is ≈0.8–0.9 — which means
the published random-split numbers in the brief (RMSE 0.66–0.93, R² 0.77–0.83) are
**already at or near the noise ceiling**, and no amount of compute can improve them on
random splits. The only headroom is in generalization (scaffold-split R² 0.4–0.6) and in
label quality, not in model capacity.

### Cited findings
- Learning curves saturate at an "irreducible error" region set by the data, independent
  of model or compute — [arXiv:2011.12466](https://arxiv.org/pdf/2011.12466), [arXiv:2103.10948](https://arxiv.org/pdf/2103.10948)
- Published ODT regression performance: Extra Trees R² = 0.814 / RMSE = 0.816;
  RF 0.802 / 0.841; Bagging 0.784 / 0.878 on external test — and ECFP4–GBDT R² = 0.94 /
  RMSE = 0.44 on −log10[mg/L] — [PMC12654368](https://pmc.ncbi.nlm.nih.gov/articles/PMC12654368/)
- The CheMeleon rationale explicitly frames noisy labels as the confound that limits
  learned representations, and uses noise-free computed descriptors as targets instead —
  [arXiv:2506.15792](https://arxiv.org/abs/2506.15792)

### Inferences (with arithmetic)
- **Ceiling formula.** If a label y = f(x) + ε with ε ~ N(0, σ²) and the model recovers
  f perfectly, then test RMSE → σ and R²_max = 1 − σ²/Var(y).
  - σ = 0.7, SD(y) = 1.8 log → R²_max = 1 − 0.49/3.24 = **0.85**
  - σ = 0.8, SD(y) = 1.8 → 1 − 0.64/3.24 = **0.80**
  - σ = 0.6, SD(y) = 2.0 → 1 − 0.36/4.00 = **0.91**
  → The brief's reported R² 0.77–0.83 sits inside this band. **Random-split performance
  is effectively solved; further compute buys nothing there.** **[my arithmetic]**
- **Corollary on the R² = 0.94 / RMSE = 0.44 result**: 0.44 log is *below* the stated
  experimental noise of 0.6–0.8 log. Either that dataset's labels are much less noisy
  (single-source, single-panel), or the split leaks (duplicates/analogues across
  train/test), or the target is a transformed quantity with different variance. Flag it
  as an outlier rather than a target to beat.
- **How to estimate the ceiling empirically** (cheap, CPU-only, do this first):
  1. **Replicate agreement**: for molecules with ≥2 independent literature thresholds,
     compute the SD of pairwise differences d; σ = SD(d)/√2. This directly measures σ.
  2. **Source-level split**: train on source A, test on source B; the residual RMSE floor
     approximates inter-lab σ plus systematic offsets.
  3. **Bayes-error bracket**: fit increasingly flexible models until test RMSE stops
     falling; the asymptote is the empirical ceiling.
  4. **Noise injection**: add known-variance noise to a clean computed property
     (e.g. logP), refit, and confirm the RMSE-vs-σ relationship holds for your pipeline.
- **Proposed accuracy tiers for odor potency** (log10 units; factor-of-X in
  concentration = 10^RMSE):
  | Tier | RMSE (log10) | Factor | R² (random split) | R² (scaffold) | Verdict |
  |---|---|---|---|---|---|
  | T0 "screening" | ≤1.3 | ~20× | ≥0.5 | ≥0.25 | Rank-orders strong vs weak odorants; already achievable with GBDT on descriptors in minutes |
  | T1 "useful" | ≤1.0 | **10×** | ≥0.65 | ≥0.4 | Matches the low end of published work; adequate for triage/prioritization |
  | T2 "good" | ≤0.8 | ~6× | ≥0.75 | ≥0.5 | Matches published random-split SOTA; at the noise ceiling for σ=0.8 |
  | T3 "at noise floor" | ≤0.65 | ~4.5× | ≥0.83 | ≥0.6 | Equal to a single replicate measurement; the practical maximum |
  | T4 "within 3×" | ≤0.48 | **3×** | ≥0.90 | ≥0.75 | **Below the label noise — not achievable on single-measurement labels.** Only reachable by averaging replicates (σ_eff = σ/√k) or restricting to a single high-quality source |
  **[my construction; the RMSE↔factor conversion is exact, the R² columns assume
  SD(y) ≈ 1.8 log]**
- "Within a factor of 3" should therefore be reframed: it is a **data-curation goal**
  (collect k≈3 replicates per molecule → σ_eff = 0.8/√3 = 0.46), not a modelling goal.
  This is the cleanest possible statement of the data-vs-compute conclusion.

### Gaps
- I did not find a published replicate-agreement / inter-laboratory σ estimate for odor
  detection thresholds in this session; the 0.6–0.8 figure comes from the brief, not from
  a source I verified. SD(y) for the candidate dataset is also assumed (1.8 log), not
  measured — both should be computed from the actual assembled dataset before the tiers
  above are quoted as firm.

---

## Q4. Concrete compute budgets by hardware tier

### Takeaway
Tiers (a) laptop/CPU and (b) single consumer GPU cover **everything needed to reach
T2/T3 accuracy**, at a hardware cost of €0–2,500 or a cloud cost of a few dollars per
full experimental campaign. Tier (c) single A100/H100 is only needed for LLM fine-tuning
and local literature extraction; tier (d) cluster is needed only to *pretrain* a
foundation model, which is unnecessary given open checkpoints — and which LMU
researchers can get free at LRZ anyway.

### Cited findings — 2026 prices
- **RunPod** (per-second billing, no egress fees): RTX 4090 from **$0.34/h** Community,
  **$0.69/h** Secure; RTX 5090 32 GB **$0.99/h**; A100 PCIe **$1.39/h**; A100 SXM
  **$1.49/h**; H100 PCIe from **$1.99/h**; H100 SXM **$2.69/h** —
  [RunPod pricing](https://www.runpod.io/pricing); corroborated by
  [computeprices.com/providers/runpod](https://computeprices.com/providers/runpod) and
  [gpuperhour.com/providers/runpod](https://gpuperhour.com/providers/runpod)
- **Lambda**: A100 40 GB **$1.99/h**; H100 PCIe **$3.29/h**; H100 SXM **$4.29/h**
  (as of September 2026) — [SynpixCloud Lambda pricing 2026](https://www.synpixcloud.com/blog/lambda-labs-gpu-pricing-2026) **[uncertain: secondary aggregator, not Lambda's own page]**
- Market-wide H100 range **$1.49/h (Vast.ai) to $6.98/h (Azure)**; "H100 pricing cannot
  be expressed as one universal on-demand rate" — [IntuitionLabs H100 comparison](https://intuitionlabs.ai/articles/h100-rental-prices-cloud-comparison) **[uncertain: aggregator]**
- **Hetzner (EU/Germany, dedicated, monthly)**: GEX44 with NVIDIA RTX 4000 SFF Ada
  (20 GB), i5-13500, 64 GB RAM at **€184/month**; GEX130 with RTX 6000 Ada (48 GB ECC),
  Xeon Gold 5412U at **€838/month**; a newer RTX PRO 6000 96 GB tier at **€1,199/month** —
  [Hetzner GPU matrix](https://www.hetzner.com/dedicated-rootserver/matrix-gpu/), [Hetzner GEX130 press release](https://www.hetzner.com/pressroom/gpu-server-gex130/), [gpuhosted.com review](https://gpuhosted.com/en/hetzner-gpu-review/) **[the €838 GEX130 may be discontinued per the last source — verify before quoting]**
- **LRZ (Leibniz Supercomputing Centre, Garching — available to LMU)**: the LRZ AI Systems
  provide HGX H100 nodes (**4× H100, 94 GB each**) and DGX A100 nodes (**8× A100, 80 GB
  each**), "primarily funded through the BayernKI initiative"; the BayernKI Gen-3 LRZ
  partition adds **120× NVIDIA H100 (92 GB HBM)** across 30 Lenovo SD665-N systems —
  [LRZ AI Systems docs](https://doku.lrz.de/lrz-ai-systems-11484278.html), [LRZ AI intro slides](https://doku.lrz.de/files/10333405/1131348032/7/1745833429023/IntroductionToLrzAiSystems.pdf), [BayernKI slides](https://hpc.fau.de/files/2024/05/2024-06-11-HPC-Cafe-BayernKI_LRZslides.pdf)
- LRZ access path: obtain a **Linux Cluster account**, then file a Servicedesk request
  choosing "AI topics" → "LRZ AI Systems – Request for Access," including the cluster
  username and a description of intended usage — [LRZ AI Systems docs](https://doku.lrz.de/lrz-ai-systems-11484278.html)
- LMU already co-uses H100s on the LRZ BayernKI AI cluster in published collaborations —
  [BayernKI/LRZ material](https://hpc.fau.de/files/2024/05/2024-06-11-HPC-Cafe-BayernKI_LRZslides.pdf)

### Inferences — the four budgets

**(a) Laptop / CPU tier — MacBook, €0 marginal cost.** Feasible: full Mordred/RDKit
featurization of 10k molecules (~21 min, parallelizable); XGBoost/RF/SVR with 200-trial
Optuna × 5-fold CV (~35 min); Chemprop D-MPNN on 1–5k molecules ("a few minutes on a
standard laptop with CPUs only" per [Chemprop](https://chemrxiv.org/doi/pdf/10.26434/chemrxiv-2025-4p1nr));
full learning-curve study and repeated scaffold splits overnight; frozen-embedding
fine-tuning (extract MoLFormer/ChemBERTa/CheMeleon embeddings once, then fit a linear or
GBDT head). **This tier alone reaches T2 accuracy.** **[my estimate, built on the
sourced Chemprop and fastprop timings]**

**(b) Single consumer GPU — RTX 4090/5090 24–32 GB.** Feasible: everything in (a) at
10–30× speed; full fine-tuning of MoLFormer/ChemBERTa/Uni-Mol/CheMeleon (minutes per
run, so a 100-run hyperparameter sweep is an afternoon); 10–30 model ensembles;
reproducing OpenPOM (<1 GPU-hour); QLoRA on a 7–8B LLM (24 GB is tight but workable at
4-bit). Cloud arithmetic: a realistic **50-GPU-hour** full campaign (all model classes,
sweeps, ensembles, ablations) costs 50 × $0.34 = **$17** on RunPod Community 4090, or
50 × $0.99 = **$50** on a 5090. Owned hardware: a 4090/5090 workstation ≈ €2,000–3,500
one-off; Hetzner GEX44 at €184/month is break-even against ~540 h/month of 4090 rental.
**[my arithmetic on sourced rates]**

**(c) Single datacenter GPU — A100 80 GB / H100.** Needed only for: full (non-LoRA)
fine-tuning of a 7–8B LLM; local open-weight LLM extraction at volume; 3D models with
large conformer batches; pretraining a CheMeleon-class descriptor model from scratch.
Arithmetic: a 20-hour job = 20 × $1.39 = **$28** (A100 PCIe, RunPod) or 20 × $2.69 =
**$54** (H100 SXM). Even a generous 200-hour month is **$278–538**. For LMU, the same
work is **free** on LRZ's HGX H100 / DGX A100 partitions after the access request.
**[my arithmetic on sourced rates]**

**(d) Cluster / pretraining tier.** Only justified to reproduce or extend a foundation
model. Reference points: MoLFormer-XL 1,920 V100-h (**≈$1.5–3k** at assumed V100 rates);
ChemBERTa-2 480 T4-h (**≈$150–240**); Uni-Mol2 on 64× A100-80GB — at 1 week that is
10,752 A100-h ≈ **$15k** at $1.39/h, or ~$21k at Lambda's $1.99/h. **Recommendation: do
not enter this tier.** The evidence in Q2 says scale transfers weakly to 2k noisy labels,
and CheMeleon shows the useful pretraining signal (descriptor targets on 1M molecules,
12.9M params) is obtainable in the (c) tier for tens of dollars. If a domain-specific
pretrain is wanted, pretrain *CheMeleon-style on odor-relevant chemical space*, not
MoLFormer-style at scale.

**Apple Silicon feasibility.** PyTorch's MPS backend runs on M1–M4 GPU cores, requires
macOS ≥12.3, keeps tensors in unified memory (no host↔device copy), and does not cover
all operators — `PYTORCH_ENABLE_MPS_FALLBACK=1` falls back to CPU kernels for the
missing ones — [PyTorch blog](https://pytorch.org/blog/introducing-accelerated-pytorch-training-on-mac/), [Apple developer page](https://developer.apple.com/metal/pytorch), [HF Accelerate MPS guide](https://huggingface.co/docs/accelerate/usage_guides/mps).
**[my assessment]** For this project MPS is a convenience, not a requirement:
- XGBoost / RF / Mordred / RDKit: **CPU only, unaffected — the M-series CPU is excellent
  here and this is the recommended primary workflow.**
- Chemprop: officially documented as CPU-viable at our dataset size; scatter/gather
  message-passing ops are exactly the class most likely to hit MPS operator gaps, so
  expect to need the CPU-fallback env var and expect little or no speedup. **Run it on
  CPU on the Mac; don't fight MPS.**
- Transformer encoder fine-tunes (ChemBERTa/MoLFormer, ≤100M params): MPS works and
  helps; a 5k-molecule fine-tune is minutes.
- 7–8B LLM LoRA: possible on 64 GB+ unified memory via MLX rather than PyTorch/MPS, but
  bitsandbytes/QLoRA CUDA kernels are unavailable — rent a GPU instead ($3/run).
- **No source found for Chemprop-on-MPS being officially supported or benchmarked** — the
  Chemprop docs discuss CPU vs GPU (CUDA) only.

### Gaps
- Lambda's and Hetzner's own price pages were not fetched directly in this session; the
  quoted figures come from secondary trackers and a press release. Verify before
  publishing exact numbers.
- LRZ publishes no €/GPU-hour or core-hour quota figure that I retrieved; the access
  model is application-based (Linux Cluster account + AI Systems request), and I found no
  statement of how many GPU-hours an LMU project is typically granted.
- Spot/preemptible discounts (typically 50–70%) were not verified for any provider.

---

## Q5. Data-building compute: LLM extraction and PDF parsing

### Takeaway
Parsing and extracting odor-threshold data from 10k–50k papers is a **tens-to-low-hundreds
of GPU-hours, sub-$500** job if done with open-weight models on rented GPUs, and it is
almost certainly the highest-return compute spend in the whole project — because Q2/Q3
say data, not model capacity, is the binding constraint.

### Cited findings
- **MinerU**: MinerU 2.5's VLM backend runs at **~2.1 pages/s on an A100-80G**, up to
  **~4.5 pages/s on an H200**; for 30+ pages/s an L40S (48 GB) or H100 (80 GB) is
  recommended, and an L40S hosts 4–5 concurrent MinerU workers without swapping —
  [Spheron self-hosting guide](https://www.spheron.network/blog/self-host-document-intelligence-docling-marker-mineru-rag-guide/), [MinerU throughput discussion](https://github.com/opendatalab/MinerU/discussions/3738) **[uncertain: vendor blog + GitHub discussion, not a paper]**
- **Marker**: "Marker projects up to ~122 pages/s on an H100 in batch mode"; separately
  "Marker v2 sustains 2.9 pages per second on a single NVIDIA B200," described as "more
  than five times the speed of MinerU's pipeline backend," scoring 76.0 on olmOCR-bench —
  [zal-group benchmark](https://www.zal-group.com/news/product-model-releases/marker-v2-vs-mineru-docling-liteparse-benchmark), [lumienai summary](https://lumienai.com/news/marker-2-vs-mineru-docling-liteparse-olmocr-bench-benchmark) **[these two Marker figures — 122 pages/s and 2.9 pages/s — differ by ~40×; they cannot both describe the same configuration. Treat the low figure (2.9 pages/s) as the safe planning number and the 122 figure as an unvalidated marketing claim.]**
- Local LLM serving throughput: vLLM reached **2,352 tok/s with Qwen3-32B on an H100**;
  a 7B-class dense model reached **~7,300 tokens/s (input+output) in offline batch mode
  on an H100** — [GPUStack Qwen3-32B H100 lab](https://docs.gpustack.ai/2.0/performance-lab/qwen3-32b/h100/), [Markaicode H100 benchmarks](https://markaicode.com/benchmarks/cuda-qwen-3-h100-latency-benchmark/) **[uncertain: vendor/blog benchmarks]**

### Inferences — arithmetic

**PDF parsing, 50,000 papers × 12 pages = 600,000 pages** **[12 pages/paper assumed]**:
- MinerU on A100 at 2.1 pages/s: 600,000 / 2.1 = 285,714 s = **79 h** → 79 × $1.39 =
  **$110** (RunPod A100 PCIe).
- MinerU on H200 at 4.5 pages/s: **37 h**; on an L40S with 4 workers, comparable.
- Marker v2 at 2.9 pages/s: **57 h** → ~$80–150 depending on GPU.
- For 10,000 papers (120,000 pages) divide by 5: **≈16 h, ≈$22** on an A100.
→ **PDF parsing is not a budget item.** It is a 1–3 day single-GPU job.

**LLM extraction, local open-weight model.** Assume 15,000 input tokens per paper
(parsed text of the relevant sections) + 1,000 output tokens:
- 50,000 papers × 16,000 tokens = **800M tokens**.
- At 7,300 tok/s (7B-class, H100, offline batch): 800e6 / 7300 = 109,589 s = **30.4 h**
  → 30.4 × $2.69 = **$82** (H100 SXM, RunPod), or × $1.99 = **$61** (H100 PCIe).
- At 2,352 tok/s (32B-class, H100): 800e6 / 2352 = 340,136 s = **94.5 h** → **$254**
  (H100 SXM) — i.e. **a much stronger extraction model costs ~$250 for the whole corpus.**
- For 10,000 papers: divide by 5 → **6 h / $17** (7B) or **19 h / $51** (32B).
**[my arithmetic on sourced throughputs; token counts are assumptions]**

**API alternative.** The comparison is cost = 800M input tokens × $/Mtok. At a
hypothetical $0.25/Mtok input and $1.25/Mtok output for a small frontier-tier model:
800M×0.25/1e6 = **$200** + 50M×1.25/1e6 = **$63** → **≈$263**; at a large-model
$3/$15 rate it is **$2,400 + $750 ≈ $3,150**. **[illustrative arithmetic only — I did
not verify any 2026 API price card in this session; the report must look these up before
quoting.]** Practical read: a small/cheap API model and a local 32B model land in the
same ~$100–300 band for 50k papers, so the decision should be made on extraction quality
and data-governance, not cost. Two-stage triage (cheap classifier decides which papers
contain threshold data; expensive model extracts only those, typically 2–10% of hits)
cuts either number by ~10×.

### Gaps
- No verified 2026 API price card (Anthropic/OpenAI/Google) in this session — all API
  cost figures above are parametric illustrations, not sourced.
- No source on extraction *accuracy* for numeric odor-threshold values from tables, which
  is the real risk: mis-extracted units (ppb vs µg/L vs µg/m³ vs ppm in air vs water) add
  systematic error far larger than the 0.6–0.8 log experimental noise and would lower the
  achievable ceiling rather than raise it. Unit normalization and a human-audited
  validation subset should be budgeted as human, not GPU, time.
- MinerU/Marker throughput figures all come from vendor blogs; the two Marker numbers
  are mutually inconsistent (see above).

---

## Cross-cutting recommendation (inference, for the report writer)

Ordered by expected return per unit compute:
1. **Measure the ceiling first** (replicate agreement → σ; source-split → systematic
   offsets). CPU-only, hours. Without this, every accuracy target is guesswork.
2. **Run the learning curve** (200 → 3,200 molecules, GBDT + Chemprop, 10 repeats).
   Laptop-overnight. This converts "should we get more data?" into a slope and an
   extrapolated N for each accuracy tier.
3. **Baseline hard**: Mordred/RDKit + XGBoost, with scaffold-split CV and ensembling.
   Minutes. Q2's evidence says this is the model to beat in the low-data regime.
4. **Fine-tune CheMeleon via Chemprop `--from-foundation CheMeleon`** — the one
   foundation model with published wins over RF on small data, and a one-flag change.
   Minutes per run on a consumer GPU.
5. **Spend the real compute budget on data**: PDF parsing + LLM extraction of the
   literature (≈$100–400, 1–4 GPU-days).
6. **Do not pretrain** a MoLFormer/Uni-Mol2-scale model (≈$1.5k–21k) — the scaling
   evidence does not support it at this label count and noise level.
7. Total defensible compute budget for the modelling side: **under $100 of rented GPU,
   or zero on an LMU LRZ allocation.** The project's cost is data curation and human
   validation, not FLOPs.
