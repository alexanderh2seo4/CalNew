# Modular pipeline under the NOSE downstream protocol

Development train+validation refit; original NOSE-style test assignments retained; split seed 42, model seeds [42, 43, 44]. Test-set Pearson, mean (sd) over model seeds.

| Task | n here / paper | test n | Pipeline v1 | Pipeline v2 | Morgan ridge (ours) | Extra-trees explicit+FP (ours) | NOSE (paper) | Morgan (paper) | best other paper baseline |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Threshold (Abraham) | 186 / 268 | 38 | 0.82 (0.01) | 0.81 (0.00) | 0.76 (0.00) | 0.80 (0.00) | 0.84 (0.03) | 0.60 (0.18) | ChemBERTa 0.81 (0.02) |
| Pleasantness (Keller) | 326 / 474 | 33 | 0.39 (0.02) | 0.52 (0.01) | 0.46 (0.00) | 0.52 (0.00) | 0.71 (0.05) | 0.51 (0.03) | Uni-Mol 0.68 (0.02) |
| Intensity (Keller) | 326 / 474 | 33 | 0.63 (0.02) | 0.63 (0.02) | 0.49 (0.00) | 0.47 (0.00) | 0.42 (0.01) | 0.05 (0.02) | ChemBERTa 0.39 (0.07) |
| Intensity (Ravia) | 114 / 248 | 12 | 0.04 (0.09) | 0.46 (0.01) | 0.01 (0.00) | 0.30 (0.00) | 0.49 (0.03) | 0.10 (0.19) | ChemBERTa 0.47 (0.06) |
| Descriptor strength (Keller) | 326 / 474 | 33 | 0.40 (0.01) | 0.40 (0.01) | 0.37 (0.00) | 0.45 (0.00) | 0.35 (0.06) | 0.24 (0.02) | Uni-Mol 0.33 (0.05) |

## Split robustness (split seeds [42, 43, 44, 45, 46, 47, 48, 49, 50, 51] with model seed 42)

Mean (sd) over random splits. With the reduced datasets, test sets hold 11-38 molecules, so a single split is noisy.

| Task | Pipeline v1 | Pipeline v2 | Morgan ridge (ours) | Extra-trees explicit+FP (ours) | NOSE (paper, split 42) |
|---|---:|---:|---:|---:|---:|
| Threshold (Abraham) | 0.81 (0.06) | 0.82 (0.03) | 0.73 (0.07) | 0.82 (0.03) | 0.84 (0.03) |
| Pleasantness (Keller) | 0.56 (0.11) | 0.69 (0.08) | 0.61 (0.10) | 0.66 (0.08) | 0.71 (0.05) |
| Intensity (Keller) | 0.58 (0.14) | 0.58 (0.14) | 0.29 (0.15) | 0.38 (0.15) | 0.42 (0.01) |
| Intensity (Ravia) | 0.33 (0.32) | 0.56 (0.17) | 0.27 (0.30) | 0.45 (0.24) | 0.49 (0.03) |
| Descriptor strength (Keller) | 0.42 (0.06) | 0.42 (0.06) | 0.43 (0.06) | 0.50 (0.05) | 0.35 (0.06) |

Descriptor strength: macro Pearson (the paper's stated aggregation), flattened diagnostic and MAE:

| Model | Pearson mean per descriptor | Pearson flattened | MAE |
|---|---:|---:|---:|
| explicit_fp_extra_trees | 0.45 (0.00) | 0.63 (0.00) | 2.60 |
| morgan_ridge | 0.37 (0.00) | 0.58 (0.00) | 2.73 |
| pipeline_C | 0.40 (0.01) | 0.61 (0.00) | 2.73 |
| pipeline_v2 | 0.40 (0.01) | 0.61 (0.00) | 2.73 |
| NOSE (paper) | 0.348 | — | 5.86 |

Threshold components: fusion 0.77 (0.01), ridge explicit+quality 0.81 (0.01).

## Differences from the paper

- CALNEW's reserved final tests and the pipeline test partition stay closed, so every dataset
  is smaller than in the paper (e.g. Abraham 186 vs 268).
- Keller molecule targets use each molecule's higher-concentration stimulus; descriptor
  strength covers the 20 semantic descriptors (the paper's 21-dim target is not specified).
- Ravia uses published group means at each molecule's most concentrated dilution
  (178 molecules in the public files vs 248 in the paper).
- Fixed v2 models are refitted on train+validation development molecules. Effective ratios are 80/0/20 for Abraham and 90/0/10 for Keller/Ravia; the original test assignments are retained. This is an expanded-training experiment, not the paper's training protocol.
- Threshold tree members also train on Li et al. 2025 water thresholds (CC BY 4.0) as flagged
  auxiliary rows; rows of the split's validation/test molecules and of reserved molecules are dropped.

The paper's standard deviations describe model seeds on a fixed split; the robustness table's standard deviations describe different, overlapping random splits. Comparing their size does not establish statistical equivalence or parity.

The Morgan-ridge column is our reimplementation of the paper's weakest-feature baseline on the same reduced splits: comparing it with the paper's Morgan row shows how much the smaller, different datasets shift the scale.

Random splits leak close analogues between train and test and are easier than CALNEW's structural splits; see docs/PIPELINE.md for the structural cross-validation results.
