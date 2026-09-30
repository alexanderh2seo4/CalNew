# Modular pipeline: quality → potency → combiner

An example implementation of the modular architecture from [the pipeline research report](../reports/Modular%20odor%20pipeline%20architecture.md). Separate models predict *what a molecule smells like* (stage A) and *how strongly* (stage B). A small combiner then models the profile a panel perceives at a given dilution (stage C). The fusion encoder follows the block-fusion idea of NOSE ([arXiv:2604.10452](https://arxiv.org/html/2604.10452v2)), scaled down to run on a laptop CPU.

This is a runnable research prototype, not a validated sensory model. Results: [latest run](#results).

```mermaid
flowchart LR
  S[SMILES] --> F[Explicit structure blocks<br/>transport · H-bond · osmophore · chain/shape<br/>pharmacophore · fingerprint · optional Uni-Mol2]
  F --> A[Stage A: quality<br/>NOSE-lite fusion → 91 catalogue labels]
  F --> B1[Stage B1: air threshold<br/>ridge ablations + Gaussian fusion net]
  F --> B2[Stage B2: dose-response<br/>Hill parameters I_max, x50, slope]
  A -- out-of-fold logits --> B1
  A -- out-of-fold logits --> B2
  A -- out-of-fold logits --> C[Stage C: combiner<br/>profile = magnitude(I, dilution) × direction(quality)]
  B2 -- intensity at dilution --> C
  C --> P[Descriptor profile · intensity · pleasantness]
  C --> M[Mixture rule<br/>Primacy + vector average · unvalidated]
```

## Run it

```bash
.venv/bin/python -m calnew pipeline train --out runs/my-pipeline               # 5-fold, fingerprint anchor, ~2 min on CPU
.venv/bin/python -m calnew pipeline train --out runs/my-pipeline-unimol --anchor unimol2
.venv/bin/python -m calnew pipeline predict --run runs/modular-pipeline-fingerprint-v1 \
  --smiles 'CCCCCCCC=O' 'CC(C)(C)S' --dilution 1e-3
.venv/bin/python -m calnew pipeline predict --run runs/modular-pipeline-fingerprint-v1 \
  --smiles 'CCCCCCCC=O' 'COc1nccnc1C(C)C' --dilution 1e-3 --mixture
```

```bash
.venv/bin/python -m calnew pipeline paper-benchmark --out runs/my-benchmark \
  --robustness-splits 43 44 45 46 47 48 49 50 51            # NOSE protocol, ~23 min
```

`--fast` trains fewer seeds and epochs for a quick check. A run directory holds `REPORT.md`, `metrics.json`, `oof-predictions.npz`, the per-fold fusion gates (`gates.json`), `run.json` (data counts, settings, package and code identity) and `pipeline.joblib` (the trusted local artifact for `predict`).

## Data and leakage control

| Stage | Data | Unit of analysis |
|---|---|---|
| A quality | Leffingwell catalogue, labels with ≥20 positives | molecule × 91 binary labels |
| B1 threshold | Abraham 2012 via pyrfume; Li et al. 2025 water ODTs as flagged training-only rows | log10(ppbv) in air |
| B2 intensity, C profile | Keller & Vosshall 2016 (ingested for this pipeline) | stimulus = molecule × dilution, mean over raters |

- **Earlier holdouts stay closed.** Every molecule in the final-test partitions of `runs/basic-threshold-models` and `runs/basic-descriptor-models` is removed from every stage, together with its ring scaffold group.
- **A new pipeline test partition** (15% of structural groups containing Keller molecules) is reserved and written to `reserved-pipeline-test.json`. Training and evaluation never read it.
- **One global structural grouping** (Murcko scaffold, Butina clusters for acyclic molecules) covers the union of molecules. Groups are assigned to five folds by weighted greedy balancing. The benzene scaffold alone has 618 molecules, so that fold is larger.
- **Nested out-of-fold quality features.** For outer fold *k*, test rows get stage-A features from a model trained without fold *k*. Training rows in fold *j* get them from a model trained without folds {*k*, *j*}. That is 15 stage-A fits per run.
- **The combiner is teacher-forced.** It trains on measured intensity and is scored twice: with measured intensity (`oracle`) and with stage-B2 predictions (`predicted`). The gap is the error the potency stage propagates.

## Structure blocks (`pipeline/blocks.py`)

| Block | Contents |
|---|---|
| transport | MW, heavy atoms, Crippen logP, TPSA, rotatable bonds, rings, Labute ASA, MR, Fsp3, heteroatoms |
| hbond | RDKit donor/acceptor counts, NHOH/NO counts, PEOE_VSA1–14, SMARTS-typed donors (O–H, N–H, amide N–H, S–H) and acceptors (carbonyl, ether, ester, aromatic N, amine, nitrile), polar surface fraction |
| osmophore | 35 SMARTS counts: thiol, sulfide, disulfide, thioester, isothiocyanate, aldehyde, ketone, acid, ester, lactone, unsaturated ester, enal/enone, (alkoxy)pyrazine, furan, thiophene, thiazole, pyrrole, pyridine, phenol, alcohol and amine degree, etc. |
| chain | longest acyclic carbon chain (tree diameter), its square, acyclic carbons, tertiary/quaternary carbons, branch points, saturating `1 − exp(−k·n^1.4)` bases for several *k* (chain and heavy-atom count), Kappa/Chi, Balaban J, log Bertz, stereocentres |
| pharmacophore | Gobbi 2D pharmacophore bits folded to 1,024 counts |
| fingerprint | chiral Morgan r=2 (1,024) + MACCS |
| rdkit | the full RDKit 2D descriptor list (217 columns), clipped to ±1e6; tree members only |
| unimol2 (optional) | frozen Uni-Mol2 84M, 16-conformer mean + 256-bit chiral fingerprint (existing adapter) |

The chain features are deliberately not monotonic: thresholds fall with chain length, level off and then rise past a cut-off. Abraham A/B hydrogen-bond descriptors are not computed; UFZ-LSER lookup would be the next addition.

## NOSE-lite fusion (`pipeline/fusion.py`)

Each block gets its own two-layer projection. Every non-anchor projection has its component along the anchor projection removed (hard Gram–Schmidt). A soft penalty on pairwise cosine overlap and one softmax weight per block give the fused representation. The anchor is the fingerprint (default) or Uni-Mol2. Explicit blocks can therefore only contribute information the anchor lacks. `gates.json` records the learned block weights per fold. NOSE's Qwen3-8B descriptor encoder, ESM-2 receptor encoder and contrastive pretraining are not used.

## Stages (`pipeline/stages.py`)

- **A:** fusion net with positive-weighted masked BCE (2-seed ensemble). Compared with per-label balanced logistic regression on explicit + fingerprint blocks.
- **B1:** four grouped-CV ridge variants that isolate the blocks (fingerprint only; explicit only; explicit + fingerprint; explicit + quality), a 5-seed fusion net with a Gaussian head via the existing `censored_normal_nll` (it accepts left/right/interval-censored rows unchanged), and their ensemble.
- **B2:** fusion net emitting Hill parameters; intensity = I_max / (1 + exp(−slope·(x − x50))) on the log10 dilution axis. It is compared with flat ridge and extra-trees models.
- **C:** profile = 25·softplus(a·I + b·x + c) × normalise(softplus(W·q + d)) + residual(q). Pleasantness = f(q) + I·g(q). Biases start at the mean training profile, and the L2 penalty on all learned deviations is chosen by grouped inner CV.
- **Tabular heads (v2):** `TabularEnsemble` averages extra-trees / XGBoost / ridge members, each on its own block combination. It serves stage B1 (added to the fusion ensemble), the pleasantness head and the Ravia single-concentration task. Tree kinds ending in `+aux` additionally train on auxiliary rows carrying a medium flag, and always predict with the flag at 0.
- **Mixtures:** `combine_mixture` evaluates each component at 20% of its concentration (Primacy), averages intensities weighted by intensity, takes the normalised mean of quality directions and weights pleasantness by intensity. No mixture data is ingested, so this rule is **unvalidated** here.

## Results

Run `runs/modular-pipeline-fingerprint-v5`: 5-fold grouped CV, fingerprint anchor, 24 minutes on the alex-pc CPU (4.5 min on the Mac before the v2 heads were added). All numbers are out-of-fold on development molecules. The data: 2,589 quality molecules × 91 labels, 186 air thresholds, and 658 Keller stimuli from 326 molecules. 709 molecules were excluded for earlier holdouts, and 273 are reserved as the pipeline test. Full tables are in the run's `REPORT.md`.

**Stage A (quality):** fusion net macro AP **0.241** / AUROC **0.828**, vs 0.232 / 0.806 for per-label logistic regression. The second-vocabulary head predicts the Keller descriptor direction with held-out cosine 0.840. Predicting the mean direction scores 0.835, so cosine mostly measures the profile every odour shares.

**Stage B1 (air threshold, log10 ppbv):**

| Model | MAE | within 10× | Spearman |
|---|---:|---:|---:|
| NOSE-lite fusion (all blocks + quality) | **0.826** | 0.69 | 0.67 |
| v2 members (fusion+ridge ensemble, descriptor trees, fingerprint and Uni-Mol2 ridges) | 0.829 | 0.67 | **0.690** |
| ensemble (fusion + ridge explicit+quality) | 0.837 | 0.65 | 0.66 |
| ridge: explicit blocks + stage-A quality | 0.904 | 0.62 | 0.61 |
| ridge: explicit blocks only | 0.934 | 0.59 | 0.55 |
| ridge: explicit + fingerprint | 0.945 | 0.61 | 0.56 |
| ridge: fingerprint only | 1.027 | 0.58 | 0.45 |
| training mean | 1.214 | 0.49 | — |

- The explicit transport, H-bond, osmophore and chain blocks beat the Morgan/MACCS fingerprint alone by about 0.09 log units of MAE.
- Adding the out-of-fold stage-A quality logits improves the explicit ridge by a further 0.03. This is the pipeline link, measured.
- Fold standard errors are 0.05–0.10, so only the gap from fingerprint alone to fusion (0.20) is clearly larger than fold noise.
- The fusion net's Gaussian ±1.645 sd interval covers only 48% of held-out values: its uncertainty is too narrow. `predict` therefore reports a residual-quantile interval.

**Stage B2 (intensity, Keller 0–100):** the Hill-parameter model reaches Pearson **0.607** (RMSE 18.2), vs 0.582 for flat extra-trees and 0.539 for flat ridge. For every molecule with two dilutions, the predicted curve rises with concentration.

**Stage C (profile and pleasantness):**

| Model | mean descriptor r | pleasantness r |
|---|---:|---:|
| pipeline, measured intensity (oracle) | **0.325** | 0.491 |
| pipeline, predicted intensity | 0.266 | 0.383 |
| v2 hedonic head (descriptor trees on structure + stage-A outputs + dilution) | — | **0.499** |
| flat extra-trees (structure + dilution → all targets) | 0.325 | 0.481 |
| flat ridge | 0.249 | 0.350 |

- With measured intensity, the combiner ties the flat model on descriptors and slightly beats it on pleasantness.
- Feeding predicted intensity costs about 0.06 descriptor r and 0.11 pleasantness r. That is the error propagated from the potency stage.
- The first combiner version fed on catalogue logits alone and overfitted (descriptor r 0.19). Anchoring it at the mean profile, choosing its penalty by grouped CV and adding stage A's second-vocabulary direction head fixed that.
- The v2 hedonic head is a separate pleasantness model, not part of the profile combiner: it trades the combiner's `profile = magnitude × direction` structure for accuracy. `predict` serves it; the combiner still produces the descriptor profile.
- As expected from the research report, the modular design is **no more accurate** end to end than a flat model. What it adds is attribution per stage, a dose–response curve evaluable at any dilution, and a path to mixtures.

### Uni-Mol2 anchor vs fingerprint anchor

Run `runs/modular-pipeline-unimol2-v2` uses the same molecules, folds and settings, but anchors the fusion on the frozen Uni-Mol2 84M embedding and adds it as a block. The Uni-Mol2 embeddings took **5.2 h** of CPU on the Mac (32 ETKDG conformers per molecule dominate); the pipeline itself took 5 minutes. Three rigid bicyclic terpenoids (camphor/thujane-type cages) failed conformer embedding and are marked unavailable (`logs/unimol2-unavailable.json`).

| Metric | fingerprint anchor | Uni-Mol2 anchor | paired difference (95% CI, group bootstrap) |
|---|---:|---:|---|
| A macro AP / AUROC | 0.241 / 0.828 | 0.243 / 0.835 | AP +0.002 (−0.006 to +0.010) |
| B1 fusion MAE (log10) | 0.826 | 0.837 | −0.011 (−0.073 to +0.050) |
| B1 ensemble MAE | 0.837 | 0.836 | +0.002 (−0.041 to +0.049) |
| B2 intensity r / MAE | 0.607 | 0.609 | MAE −0.05 (−0.59 to +0.57) |
| C descriptor r (oracle / predicted) | 0.325 / 0.266 | 0.324 / 0.266 | — |

Every interval includes zero: at these data sizes the 3D pretrained view adds nothing measurable. This matches the earlier basic-model comparison, where frozen Uni-Mol2 also trailed a descriptor ridge on thresholds. The learned block weights say the same thing. Uni-Mol2 receives 0.11 of the stage-A fusion weight (fingerprint 0.27) and 0.14 in B1, about the same as each explicit block. Keep the fingerprint anchor as the default. Pay for Uni-Mol2 only once much larger labelled sets exist, or once it is fine-tuned rather than frozen.

**Example prediction** (`data/example-pipeline-predictions.json`):

- Out-of-domain molecules have low `nearest_tanimoto_*` values and should be read with caution.
- 2-isopropyl-3-methoxypyrazine (nearest threshold-training similarity 0.21) is predicted at about 1 ppb. That is the v2 heads' doing (v1 said 6 ppb), but still far weaker than its known sub-ppt potency.
- Calone (`Cc1ccc2c(c1)OCC(=O)CO2`, nearest similarity 0.31–0.34) is predicted as sweet/hay/phenolic. Its real marine-watermelon character has no vocabulary here: the Leffingwell label set has no `marine` or `ozone` label at all.

## NOSE downstream protocol (paper-style test)

Command: `calnew pipeline paper-benchmark --out runs/nose-protocol-v4 --robustness-splits 43 44 45 46 47 48 49 50 51` (23 min on the Mac CPU). The command reimplements the protocol of [NOSE](https://arxiv.org/html/2604.10452v2) (Tables 3, 4, 10):

- random molecule splits fixed with seed 42, with the paper's ratios and rounding (thresholds 60/20/20, Keller and Ravia 80/10/10);
- model seeds 42–44;
- test-set Pearson.

The pipeline's stages are trained per task on the train split. Stage-A quality features for train molecules are out-of-fold, and stage A never sees validation or test molecules. Nine extra random splits (seeds 43–51) show how much a single split moves the numbers; with 11–38 test molecules, that is the number to read.

| Task | n here / paper | Pipeline v1 | **Pipeline v2** | v2, 10 splits | NOSE (paper) | best paper baseline |
|---|---|---:|---:|---:|---:|---|
| Threshold (Abraham) | 186 / 268 | 0.80 | 0.77 | **0.79** (0.04) | 0.84 (0.03) | ChemBERTa 0.81 |
| Pleasantness (Keller) | 326 / 474 | 0.41 | 0.54 | **0.67** (0.07) | 0.71 (0.05) | Uni-Mol 0.68 |
| Intensity (Keller) | 326 / 474 | 0.66 | **0.66** | 0.57 (0.14) | 0.42 (0.01) | ChemBERTa 0.39 |
| Intensity (Ravia) | 114 / 248 | 0.02 | 0.45 | **0.54** (0.21) | 0.49 (0.03) | ChemBERTa 0.47 |
| Descriptor strength (Keller) | 326 / 474 | 0.41 | **0.41** | 0.42 (0.07) | 0.35 (0.06) | Uni-Mol 0.33 |

Where v2 differs from v1 (all member sets were chosen by repeated 5-fold inner CV **on the split-42 training portion only**, never on test molecules):

- **Threshold:** the v1 fusion+ridge ensemble is averaged with descriptor/fingerprint trees, a fingerprint ridge and a frozen Uni-Mol2 ridge. The trees also train on Li et al. 2025 water thresholds (see below).
- **Pleasantness:** a separate hedonic head (two extra-trees members on RDKit descriptors + explicit blocks + stage-A quality logits and direction, with the dilution as a column) replaces the combiner's pleasantness output. 0.41 → 0.54 on split 42, 0.56 → 0.67 over ten splits.
- **Ravia intensity:** three gradient-boosted members plus a Uni-Mol2 extra-trees member replace the Hill-curve stage, which cannot fit single-concentration data. 0.02 → 0.45, and 0.36 → 0.54 over ten splits.
- **Keller intensity and descriptors** keep the v1 dose–response and combiner stages, which already lead the paper.

### Where the remaining gap comes from

Three of five tasks are at or above the paper. Threshold (0.79 vs 0.84) and pleasantness (0.67 vs 0.71) remain short, both by less than one split-to-split standard deviation. The cause is data volume, not the architecture:

- **CALNEW's holdouts stay closed**, which removes 30% of the paper's molecules per task (Abraham 268 → 186, Keller 474 → 326, Ravia 248 → 114). Training splits are 111, 260 and 91 molecules.
- **Pleasantness is limited by stage A, not by the hedonic head.** Substituting the *measured* Keller descriptor profile for the predicted one lifts inner-CV pleasantness from 0.71 to 0.90. The head is close to what predicted quality supports; what it lacks is the quality model's missing 119 Keller molecules. Averaging more stage-A seeds does not help (5 seeds: 0.689 vs 0.706 for one).
- **Threshold has no comparable lever left.** MolFormer embeddings add nothing (inner CV 0.72 with, 0.72 without), and the auxiliary water thresholds help only marginally.

Closing the last 0.04–0.05 would mean opening the reserved holdouts. That is a deliberate trade this project does not make: the holdouts are worth more as clean final tests than the benchmark row is.

### Auxiliary water thresholds (training only)

The air-threshold trees also train on [Li et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12654368/) median water ODTs ([Zenodo 10.5281/zenodo.17559514](https://zenodo.org/records/17559514), CC BY 4.0), with a flag separating water from air rows. The file is not in the repository; `pipeline/auxiliary.py` pins its sha256 and prints the download URL if it is missing:

```bash
mkdir -p data/raw/li_2025/zenodo-17559514-v1
curl -L -o data/raw/li_2025/zenodo-17559514-v1/threshold_data_med.csv \
  'https://zenodo.org/records/17559514/files/threshold_data_med.csv?download=1'
```

716 of its 992 rows carry a numeric threshold; 567 survive the reserved-holdout exclusion, and each threshold fit drops the rows of its own validation and test molecules as well (0–542 rows used per fit). Of the 186 Abraham molecules, 70 also appear in Li; their water and air potencies correlate at r 0.64. The measurable effect is small: joint air+water trees reach inner-CV 0.71 against 0.70 air-only, and the v2 test score moves from 0.78 to 0.77 on split 42 and stays at 0.79 over ten splits. It is kept because it is honest extra evidence with a clean licence, not because it closed the gap.

### Other differences from the paper

- Keller targets use each molecule's higher-concentration stimulus with DREAM-style descriptor profiles (20 descriptors; the paper uses 21 dimensions).
- Ravia uses published group means at each molecule's most concentrated dilution (176 molecules in the public files, of which 114 survive exclusion, against the paper's 248 undiluted substances).
- The validation split is unused because nothing early-stops.
- NOSE's pretrained encoders (Qwen3-8B descriptors, ESM-2 receptors) and its GS-LF, Sagar and mixture tasks are not reproduced.
- Keller numbers are not directly comparable: our Morgan ridge scores 0.44 on intensity against the paper's 0.05, and our descriptor MAE is half of NOSE's, so the molecule-level target definitions differ.
- Random splits leak close analogues between train and test and are easier than CALNEW's structural splits; the structural numbers above are the honest generalisation estimate.

Earlier runs: `runs/nose-protocol-v1` (v1 only), `v2` (v2 heads, run on alex-pc), `v3` (adds Uni-Mol2 members), `v4` (adds the auxiliary water thresholds; the table above).

## Known limits

- The dilution axis is the Keller solution fraction in paraffin oil, not a gas-phase concentration. The transport block has to learn headspace effects implicitly.
- Keller descriptor profiles follow the DREAM convention: a descriptor a rater did not select counts as zero for that rater.
- Catalogue probabilities from stage A are positive-weighted rankings, not calibrated probabilities.
- The threshold set is small (186 development observations after exclusions). Differences below about 0.05 log units are within fold noise.
- The pipeline test partition has not been opened. All numbers are out-of-fold development estimates.
- Uni-Mol2 blocks mark molecules without conformers as unavailable (NaN + availability flag, imputed from training folds only).
