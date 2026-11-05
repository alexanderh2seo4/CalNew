# Modular pipeline under the NOSE downstream protocol

NOSE arXiv:2604.10452 downstream: random split seed 42, model seeds [42, 43, 44]. Test-set Pearson, mean (sd) over model seeds.

| Task | n here / paper | test n | Pipeline | Morgan ridge (ours) | Extra-trees explicit+FP (ours) | NOSE (paper) | Morgan (paper) | best other paper baseline |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Threshold (Abraham) | 186 / 268 | 38 | 0.80 (0.02) | 0.64 (0.00) | 0.74 (0.00) | 0.84 (0.03) | 0.60 (0.18) | ChemBERTa 0.81 (0.02) |
| Pleasantness (Keller) | 326 / 474 | 33 | 0.41 (0.03) | 0.49 (0.00) | 0.55 (0.00) | 0.71 (0.05) | 0.51 (0.03) | Uni-Mol 0.68 (0.02) |
| Intensity (Keller) | 326 / 474 | 33 | 0.66 (0.02) | 0.44 (0.00) | 0.39 (0.00) | 0.42 (0.01) | 0.05 (0.02) | ChemBERTa 0.39 (0.07) |
| Intensity (Ravia) | 114 / 248 | 12 | 0.02 (0.08) | 0.07 (0.00) | 0.32 (0.00) | 0.49 (0.03) | 0.10 (0.19) | ChemBERTa 0.47 (0.06) |
| Descriptor strength (Keller) | 326 / 474 | 33 | 0.41 (0.03) | 0.36 (0.00) | 0.44 (0.00) | 0.35 (0.06) | 0.24 (0.02) | Uni-Mol 0.33 (0.05) |

## Split robustness (split seeds [42, 43, 44, 45, 46] with model seed 42)

Mean (sd) over random splits. With the reduced datasets, test sets hold 11-37 molecules, so a single split is noisy.

| Task | Pipeline | Morgan ridge (ours) | Extra-trees explicit+FP (ours) |
|---|---:|---:|---:|
| Threshold (Abraham) | 0.81 (0.06) | 0.66 (0.02) | 0.79 (0.03) |
| Pleasantness (Keller) | 0.56 (0.06) | 0.59 (0.08) | 0.65 (0.09) |
| Intensity (Keller) | 0.52 (0.15) | 0.23 (0.13) | 0.37 (0.04) |
| Intensity (Ravia) | 0.10 (0.18) | 0.24 (0.22) | 0.26 (0.16) |
| Descriptor strength (Keller) | 0.39 (0.05) | 0.40 (0.05) | 0.48 (0.04) |

Descriptor strength, other aggregations (the paper does not define how Pearson is pooled over 21 dimensions):

| Model | Pearson mean per descriptor | Pearson flattened | MAE |
|---|---:|---:|---:|
| pipeline_C | 0.41 (0.03) | 0.61 (0.01) | 2.74 |
| morgan_ridge | 0.36 (0.00) | 0.57 (0.00) | 2.75 |
| explicit_fp_extra_trees | 0.44 (0.00) | 0.62 (0.00) | 2.65 |
| NOSE (paper) | 0.348 | — | 5.86 |

Threshold components: fusion 0.75 (0.01), ridge explicit+quality 0.79 (0.03).

## Differences from the paper

- CALNEW's reserved final tests and the pipeline test partition stay closed, so every dataset
  is smaller than in the paper (e.g. Abraham 186 vs 268).
- Keller molecule targets use each molecule's higher-concentration stimulus; descriptor
  strength covers the 20 semantic descriptors (the paper's 21-dim target is not specified).
- Ravia uses published group means at each molecule's most concentrated dilution
  (178 molecules in the public files vs 248 in the paper).
- Models train on the train split only; the validation split is not used (no early stopping).

The Morgan-ridge column is our reimplementation of the paper's weakest-feature baseline on the same reduced splits: comparing it with the paper's Morgan row shows how much the smaller, different datasets shift the scale.

Random splits leak close analogues between train and test and are easier than CALNEW's structural splits; see docs/PIPELINE.md for the structural cross-validation results.
