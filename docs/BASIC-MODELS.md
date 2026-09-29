# Basic models: completed comparisons

The useful starting result is **two endpoint-specific predictors**, not one universal winning architecture. The initial threshold comparison favours a regularised physical/topological descriptor model. The descriptor comparison favours averaging complementary predictions.

The numerical results below are from the completed basic-model runs. The linked run reports retain full precision, per-label metrics, configuration lineage and paired bootstrap comparisons.

- [Threshold report](../runs/basic-threshold-models/REPORT.md)
- [Descriptor report](../runs/basic-descriptor-models/REPORT.md)
- [Threshold configurations](../configs/four-family-pilot.yaml)
- [Descriptor configurations](../configs/pilot.yaml)

## Airborne threshold pilot

268 processed Abraham records; 188 development, 40 calibration, 40 reserved final-test rows. The endpoint is `log10(threshold / 1 ppbv)`. Lower threshold means greater potency. Three outer structural folds and two inner tuning folds were used. This pilot uses one fixed configuration and one seed per candidate.

| Candidate | Mean outer-fold MAE | Standard error across folds |
|---|---:|---:|
| RDKit descriptors + regularised linear regression | **0.9403** | 0.0523 |
| Equal-weight ensemble | 0.9897 | 0.0541 |
| Gating ensemble | 1.0195 | 0.0852 |
| Morgan fingerprints + XGBoost | 1.0526 | 0.1328 |
| Frozen Uni-Mol2 + chirality features + linear head | 1.0651 | 0.0726 |
| Regularised stacking | 1.0900 | 0.0357 |
| Tanimoto Gaussian process | 1.1323 | 0.0903 |
| Frozen MoLFormer + linear head | 1.1466 | 0.0737 |
| Morgan fingerprints + random forest | 1.2133 | 0.0844 |
| Chemprop D-MPNN | 1.2723 | 0.0964 |
| Native CALNEW D-MPNN | 1.2993 | 0.1093 |

MAE of approximately 0.94 log units is substantial: `10^0.94 ≈ 8.7` gives the multiplicative error factor associated with that mean absolute log error. The model is a research prioritisation tool, not a precise threshold measurement substitute.

The frozen models use real published checkpoints. Uni-Mol2 here is a combined 3D-plus-chirality representation; its score does not isolate the contribution of 3D geometry. The later ablation must remove the appended fingerprints and compare single versus multiple conformers.

## Catalogue descriptor pilot

3,522 Leffingwell molecules and 113 original descriptor columns. **90 labels** meet the development-support requirement and are scored. Labels with insufficient development support are excluded from scoring and recorded in `label-selection.json`; no test-label information determines that filtering. There are 2,466 development, 528 calibration and 528 reserved final-test molecules.

| Candidate | Mean outer-fold macro average precision | Standard error |
|---|---:|---:|
| Equal-weight ensemble | **0.2548** | 0.0184 |
| Gating ensemble | 0.2401 | 0.0235 |
| Regularised stacking | 0.2277 | 0.0177 |
| RDKit descriptors + logistic regression | 0.2275 | 0.0215 |
| Morgan fingerprints + random forest | 0.2180 | 0.0163 |
| Morgan fingerprints + XGBoost | 0.2118 | 0.0168 |
| Native CALNEW D-MPNN | 0.1740 | 0.0134 |

These are source-annotation predictions. A zero is recorded as “not reported by the catalogue,” not “a person assessed and could not perceive it.” Scores are specific to the retained label vocabulary and strict split design; they are not directly comparable with papers using different molecules, labels or random splits.

The table averages the outer-fold scores, as used for selection. Pooled out-of-fold macro average precision for the selected average is **0.2176**; it differs because pooling changes label prevalence and combines predictions from differently fitted models. Both values are retained in the report rather than treated as interchangeable metrics.

## What these results justify

Keep the descriptor regression as the threshold baseline and the simple average as the descriptor baseline. Larger models must demonstrate an improvement against them on the same held-out chemistry. Different task winners support keeping quality and potency heads separate.

The neural models received only 15 epochs in these pilots. The result establishes working baselines, not that a graph architecture is intrinsically inferior. Frozen general chemistry embeddings are also only one transfer route.

## What remains unproven

- Independent 90% interval coverage: calibration objects are fitted, but the final test set has not been opened.
- Source-generalisation performance: these runs use one source per endpoint. The strict source-holdout utility needs additional independent sources.
- Prospective performance on newly measured molecules.
- Correct descriptor differences between enantiomers, despite explicit stereo representation.
- Participant variability, water thresholds, concentration-conditioned human profiles and receptor-assisted perceptual improvement.
- Adequate large-model optimisation: one pilot configuration per model cannot settle architecture selection.

The processed threshold table has 57 records marked as upstream aggregates. Original repeated experiments need reconstruction before estimating study effects credibly. The stored counts represent what was actually imported, not the larger molecule/observation counts in the source publication.

A grouped label-shuffle diagnostic of the fixed descriptor regression increased pooled development MAE to **1.6818, 1.8110 and 1.6786** across three shuffle seeds. The unshuffled pooled MAE was **0.9262** (the fold-averaged score is 0.9403). This is consistent with useful molecular information, but it is not proof that all leakage routes have been excluded. See `shuffle-control-descriptor_linear.json` in the threshold run.
