# Keller and Ravia intensity — 2026-10-01

The latest fixed recipes improve mean development Pearson correlation and absolute error for both datasets. Keller retains its selected dose/semantic blend. A further Ravia shared-study blend improves on the earlier proxy-ridge head: refit Pearson rises **0.589 → 0.607** and MAE falls **12.060 → 11.855**. All further training, evaluation, inference and tests ran on SSH. Reserved final-test molecules and their connectivity variants remain excluded from fitting and scoring.

## Paired development results

Ten existing split seeds, 42–51, with model seed 42. Test assignments and target values are unchanged. Each row compares the new head with a baseline fitted using the same training partition and meta-features. Standard deviations are across overlapping splits, not independent trials or confidence intervals.

**Latest Ravia refinement, compared with the already-improved proxy-ridge head:**

| Training | Pearson, previous → selected (SD) | MAE, previous → selected | RMSE, previous → selected | Pearson / MAE gains |
|---|---|---|---|---|
| Original 91 training molecules | 0.580 (0.192) → **0.597 (0.178)** | 11.851 → **11.748** | 14.475 → **14.285** | 8/10 / 6/10 splits |
| Train+validation: 102 molecules | 0.589 (0.180) → **0.607 (0.156)** | 12.060 → **11.855** | 14.510 → **14.310** | 6/10 / 8/10 splits |

The refitted baseline reproduces the previous selected prediction arrays within 1.43e-14 intensity units. The latest Ravia result also improves on the original paired baseline: Pearson 0.540 → 0.597 and MAE 11.930 → 11.748 under original training; Pearson 0.574 → 0.607 and MAE 11.937 → 11.855 after validation refit.

**First improvements, retained as the comparison history; Keller remains the current selection:**

| Dataset / training | Pearson, baseline → selected (SD) | MAE, baseline → selected | RMSE, baseline → selected | Pearson gains |
|---|---|---|---|---|
| Keller, original 260 training molecules | 0.569 (0.145) → **0.627 (0.111)** | 11.676 → **10.519** | 15.686 → **13.854** | 9/10 splits |
| Keller, train+validation: 293 molecules | 0.578 (0.141) → **0.639 (0.113)** | 11.581 → **10.385** | 15.623 → **13.673** | 10/10 splits |
| Ravia, original 91 training molecules | 0.540 (0.199) → **0.580 (0.192)** | 11.930 → **11.851** | 14.883 → **14.475** | 6/10 splits |
| Ravia, train+validation: 102 molecules | 0.574 (0.159) → **0.589 (0.180)** | 11.937 → 12.060 | 14.684 → **14.510** | 5/10 splits |

Original evaluation keeps 33 Keller validation and 33 test molecules, and 11 Ravia validation and 12 test molecules. The separate refit experiment admits validation molecules to training while retaining the original tests. It is not used to choose recipes or to attribute gains to a changed split ratio.

**Development-split limitation:** Ravia split 48 contains one primary training/held connectivity overlap, `NNWHUJCUHAELCL`, between two molecule variants. The original molecule assignments are retained for both the paired baseline and the candidate; these ten-split scores therefore do not establish fully connectivity-disjoint generalization. Auxiliary Keller training excludes every held connectivity, including that variant group. Training-only recipe selection uses connectivity-grouped folds, and reserved final connectivity exclusions remain enforced. The overlap is recorded in both benchmark results and the audit.

Keller's secondary score over both observed stimuli of the same held molecules also improves: mean Pearson 0.702 → 0.739 under original training and 0.708 → 0.747 after refit. All ten runs have zero decreases on the71-point dose grid. The new paired fixed-C descriptor benchmark, described under Serving below, also improves with selected intensity. Mixture predictions remain analytic and unvalidated against mixture observations.

These are local development targets, not an exact reproduction of [NOSE v2](https://arxiv.org/html/2604.10452v2). Eligible datasets contain 326 Keller and 114 Ravia molecules. Keller uses the higher-concentration stimulus as its primary target; Ravia uses published group means at the most concentrated presentation, rather than the paper's subject-normalized processing of 248 substances.

## Frozen recipes and selection

**Keller: `blend_dose_semantic`.** Equal average of the existing Hill head and monotone XGBoost trees trained on all observed dilutions of training molecules. The trees receive RDKit descriptors, explicit chemistry blocks, fingerprint, nominal log dilution and a 128-dimensional descriptor-transfer prediction. The latter is learned from the filtered 7,000-molecule augmented corpus and generic MiniLM descriptor-word vectors. Transfer fits exclude every main held connectivity; downstream training features are cross-fitted with their own connectivities excluded as well. No odor-trained released NOSE adapter is imported.

The original split-42 training-only comparison uses three repeats of grouped five-fold CV. Mean Pearson improves 0.500 → 0.552 and MAE 11.409 → 10.570, with correlation gains in every repeat. The selection was frozen before development evaluation.

**Ravia, previous head: `blend_proxy_ridge`.** Equal average of the existing four-member Ravia model and a standardized ridge head (alpha 10) on three Keller intensity proxies. These proxies use fixed Keller log10 reference dilutions −5, −3 and −1. They are latent structure features, not a Ravia dilution input or a validated Ravia dose curve.

During selection and development evaluation, source labels come only from Keller's original split-42 training cohort. Every held Ravia connectivity is excluded from source fits. Ravia training proxy values use an additional three-fold connectivity cross-fit, excluding each training feature's own connectivity from Keller source training. The source tree uses structure and fingerprint blocks, without quality meta-features. All parameter settings, reference doses and equal blend weights were registered before scoring.

The three original-training CV repeats improve mean Pearson 0.583 → 0.631 and MAE 10.575 → 10.489. A further confirmation with freshly fitted SSH baselines retains the frozen recipe, gives mean Pearson gain **+0.0461**, and MAE ratio **0.9955**, passing the same criterion. Selection requires mean Pearson gain ≥0.01, positive gains in at least two repeats and mean MAE no more than 1% above baseline. No alternative blend weight was chosen using test results.

Earlier Ravia trials are retained as negative evidence: original Uni-Mol1 representations, molecular SVR and semantic trees did not pass training selection. Smaller boosted trees passed training selection but gave refit Pearson 0.562 → 0.560 and worse MAE; that regularized head is not the recommended artifact. Direct dose-augmented trees failed selection.

**Ravia, latest head: `joint_0.25_current`.** Equal average of the previous proxy-ridge head and a shared Keller/Ravia XGBoost model. The shared model receives structure descriptors, explicit chemistry blocks and fingerprints, a study indicator and an internal dose coordinate. Keller source rows retain their nominal log dilution and weight 0.25; Ravia target rows receive weight 1, study indicator 1 and fixed coordinate 0. That coordinate represents the single highest-presentation endpoint, not a measured Ravia concentration. Trees use 400 estimators, depth 3, learning rate 0.03, minimum child weight 5, regularization 10 and a nondecreasing dose constraint. Final prediction weights are 0.25 legacy Ravia ensemble, 0.25 proxy ridge and 0.50 shared-study trees.

The source cohort during selection and both development protocols remains Keller's original split-42 training molecules, with every held Ravia connectivity excluded. The proxy component also retains its three-fold source cross-fit. The new shared model uses structure-derived inputs directly; its source rows exclude each outer validation connectivity during selection. No study weights, model parameters or blend weights were fitted to development-test errors.

All eleven refinement variants were compared inside the original split-42 training partition using three repeated connectivity-grouped five-fold evaluations (seeds 100–102). Promotion required mean Pearson gain ≥0.01 over the **current improved head**, gains in at least two repeats, and no increase in mean MAE. The winning shared-study blend passed all three repeats: mean Pearson **0.632 → 0.661**, MAE **10.488 → 10.252**. It was frozen before the ten-split development evaluation. The serving class reproduces its first frozen selection fold within 7.11e-15.

| Refinement family | Variants | Outcome on training-only selection |
|---|---|---|
| Keller dose trees plus quality/semantic features | 2 | Neither passed; current Keller retained |
| Ravia proxy Huber / median / SVR heads | 3 | None passed |
| Ravia proxy plus transport ridge, alpha 10 / 100 | 2 | Neither passed |
| Shared-study source weight 0.25 / 1, blended with legacy / current head | 4 | Two weight-0.25 variants passed; `joint_0.25_current` had the highest mean Pearson |

## Serving

The selected Keller intensity also improves the fixed descriptor combiner in a new **2026-10-02 SSH evaluation**. Across ten unchanged original assignments, descriptor macro Pearson rises **0.419521→0.426645**, MAE falls **2.556208→2.515651**, macro R² rises **0.096720→0.120280**, and MSE falls **13.121765→12.904100**. Separate validation-refit values improve **0.419144→0.427571** and **2.547637→2.509886**. Both intensity vectors feed the same fitted original C recipe per case, with no new recipe or test-based tuning. Pearson improves in9/10 splits and MAE in10/10 for both protocols. Nineteen exact Stage-A caches were reused and one fixed refit was isolated. [Notes](../runs/nose-descriptor-selected-intensity-audit-v3/NOTES.md) and [independent verification of all20 cases](../runs/nose-descriptor-selected-intensity-audit-v3/verification.json) retain raw predictions, targets and provenance. These fresh fixed-seed C baselines are separate from historical v2 descriptor summaries .420007/.419091; mixture performance is still unbenchmarked.

Saved artifacts, with hashes checked by the serving API:

- Keller: `runs/nose-intensity-keller-refit-v3/intensity-keller.joblib`, 326 eligible training molecules; SHA256 `2604aa815ad95e3311281cbb124caf73dc1eb7d3964d0c647688b10042733679`.
- Ravia, recommended: `runs/nose-intensity-ravia-joint-refit-v2/intensity-ravia.joblib`, 114 eligible Ravia training molecules and 326 eligible Keller source molecules; SHA256 `d02eadb6ecbb2043d7f96ea1e0421c3ea4cf9ce947264ff95c7102ff9090dc0c` (2,806,296 bytes).
- Previous Ravia proxy-ridge artifact retained: `runs/nose-intensity-ravia-dose-transfer-refit-v1/intensity-ravia.joblib`; SHA256 `9d570d8d379c19389123f764fe3e086ed625c72a46838d15ad21297edee905df`.

Final source training uses the complete eligible development cohort; original/refit benchmark fits retain the restricted source cohort and all test exclusions. Artifacts and detailed results are synced into the local `runs/` directory, which is ignored by Git.

Commands below run inside the isolated SSH checkout. Use its `scripts/ssh_compute.py` wrapper to select this checkout's source with the existing server Python environment.

```powershell
Set-Location 'C:\calnew'
$calnewPython = 'C:\calnew-compute\.venv\Scripts\python.exe'

# Keller alone, with the nominal paraffin-oil solution dilution
& $calnewPython scripts/ssh_compute.py -m calnew pipeline intensity-predict --dataset keller `
  --run runs/nose-intensity-keller-refit-v3 --smiles "S=C=NCCc1ccccc1" "CC(=O)c1ccccn1" --dilution 0.001

# Ravia's single highest-presentation endpoint; no dilution argument
& $calnewPython scripts/ssh_compute.py -m calnew pipeline intensity-predict --dataset ravia `
  --run runs/nose-intensity-ravia-joint-refit-v2 --smiles "S=C=NCCc1ccccc1" "CC(=O)c1ccccn1"

# Use the selected Keller head throughout the existing pipeline
& $calnewPython scripts/ssh_compute.py -m calnew pipeline predict --run runs/modular-pipeline-fingerprint-v5 `
  --intensity-run runs/nose-intensity-keller-refit-v3 --smiles "S=C=NCCc1ccccc1" "CC(=O)c1ccccn1" --dilution 0.001
```

`--out` writes JSON for either prediction command. `--semantic-run runs/nose-semantic-pleasantness-v3` can also select the earlier pleasantness head where that artifact is installed. The selected intensity enters the descriptor combiner before prediction, and mixture primacy uses the selected head at 20% concentration. Output reports the full selected Keller curve and its Hill component separately; uncertainty is unestimated for the blend. Default pipeline serving remains available when `--intensity-run` is omitted.

## SSH execution and verification

After the user's SSH-only instruction, all model fitting, numerical analysis, inference and tests ran on **authorized remote compute host**, in `C:\calnew`. Python is `C:\calnew-compute\.venv\Scripts\python.exe`; its current PyTorch wheel uses CPU. The existing checkout and unrelated user jobs were preserved.

The earlier Keller splits 42–50 were retained and verified against IDs, targets and saved metrics. Split 51 and the final Keller fit completed on SSH. Every new Ravia dose-transfer trial, ten-split evaluation, final fit and baseline confirmation ran on SSH. The frozen Keller selection copy was used to preserve its original checksum after the exploratory partial file had changed.

Fresh Windows legacy Ravia baseline predictions differ from the prior Mac fits, by up to 3.80 and 4.10 intensity units under original and refit training. The first-improvement table therefore uses its paired Windows baselines, not the earlier 0.538/0.562 means. The latest shared-study comparison reproduces the previous Windows proxy-ridge predictions within 1.43e-14. Original test IDs and targets match exactly. Transferred feature caches were reused only under their pinned code/data identities and verified checksums, with explicit path-separator migration provenance.

An unrelated change to `combine_mixture` changed the whole-file cache identity for `stages.py`. Cache migration first verified that every other source AST node, all pinned dependencies, data identities and training/held IDs were unchanged. It created verified aliases and retained existing valid numerical replicas instead of overwriting them. This proof is saved in `runs/intensity-cache-serving-migration.json`. The split-48 source check was narrowed to the auxiliary Keller cohort after detecting the pre-existing primary Ravia overlap; completed split checkpoints were verified before resuming, and both original and resumed source archives are retained.

**71 tests passed on SSH**, including shared-study serialization, monotonicity with missing geometry, connectivity exclusions, single-endpoint guards and selected-intensity pipeline/mixture integration. The prior Windows olfactometer test also passed in this isolated checkout. Actual saved-bundle smoke checks passed with the latest Ravia artifact for two eligible molecules: CLI JSON output, Ravia dilution rejection, unchanged thresholds, monotone Keller curves and selected mixture primacy intensities.

Latest evidence: `runs/intensity-ssh-audit.json`, `runs/intensity-refinement-summary.json`, `runs/intensity-refinement-smoke.json`, `runs/ssh-intensity-refinement-tests.xml`, and `runs/nose-intensity-ravia-joint-inner-v2/module-parity.json`. Each run retains its protocol, frozen selection, code archives and prediction arrays. Earlier smoke/test evidence remains in `runs/intensity-ssh-smoke.json` and `runs/ssh-intensity-tests.xml`; the previous baseline confirmation is `runs/nose-intensity-ravia-dose-transfer-inner-v1/ssh-baseline-verification.json`.

Reproduction scripts for the latest refinement: `nose_intensity_refine.py`, `nose_ravia_transport_refine.py`, `nose_ravia_joint_refine.py`, `nose_ravia_joint_benchmark.py` and `nose_ravia_joint_parity.py`. Earlier scripts remain: `nose_intensity_experiment.py`, `nose_intensity_benchmark.py`, `nose_ravia_regularization.py`, `nose_ravia_dose_transfer.py`, `nose_ravia_dose_benchmark.py` and `nose_ravia_dose_validate.py`. Choose fresh output directories for new evaluations; the benchmark `--resume` option verifies existing split checkpoints before computing missing splits. Do not reopen reserved partitions or tune either recipe using development-test errors. This development evaluation supports the fixed refinement, while fully connectivity-disjoint performance and exact NOSE parity remain unverified.
