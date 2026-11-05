# CALNEW — air_detection_threshold

**Status:** computational_pilot. Prospective validation: not_performed.

Source: `abraham_2012`. 268 rows; 188 development, 40 calibration and 40 reserved test rows.

Selected by the declared one-standard-error rule: **descriptor_linear**. This is a development selection.

| Candidate | Outer-fold mean score¹ | Standard error | Pooled development metric |
|---|---:|---:|---:|
| chemprop | -1.2723 | 0.0964 | 1.2883 |
| descriptor_linear | -0.9403 | 0.0523 | 0.9262 |
| fingerprint_rf | -1.2133 | 0.0844 | 1.2153 |
| fingerprint_xgb | -1.0526 | 0.1328 | 1.1017 |
| molformer | -1.1466 | 0.0737 | 1.1751 |
| organiser_gating | -1.0195 | 0.0852 | 1.0492 |
| organiser_mean | -0.9897 | 0.0541 | 1.0107 |
| organiser_stacking | -1.0900 | 0.0357 | 1.0848 |
| stereo_dmpnn | -1.2993 | 0.1093 | 1.3322 |
| tanimoto_gp | -1.1323 | 0.0903 | 1.1660 |
| unimol2 | -1.0651 | 0.0726 | 1.0564 |

¹ Higher is better: macro average precision for descriptors; negative log-threshold MAE for regression. Pooled metrics weight rows rather than folds.

## Interpretation

- No source-disjoint or prospective result is inferred from structural CV.
- Abraham processed duplicates are already aggregated.
- Pilot results do not establish the final architecture winner.

## Unavailable candidates

None in this run.

The machine-readable report includes per-label metrics, paired group-bootstrap comparisons, source caveats and configuration lineage.
Independent interval coverage must be measured on a subsequent evaluation set; calibration-set fit is not an independent coverage result.
