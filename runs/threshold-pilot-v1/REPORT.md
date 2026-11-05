# CALNEW — air_detection_threshold

**Status:** computational_pilot. Prospective validation: not_performed.

Source: `abraham_2012`. 268 rows; 188 development, 40 calibration and 40 reserved test rows.

Selected by the declared one-standard-error rule: **descriptor_linear**. This is a development selection.

| Candidate | Outer-fold mean score¹ | Standard error | Pooled development metric |
|---|---:|---:|---:|
| descriptor_linear | -0.9403 | 0.0523 | 0.9262 |
| fingerprint_rf | -1.2133 | 0.0844 | 1.2153 |
| fingerprint_xgb | -1.0526 | 0.1328 | 1.1017 |
| organiser_gating | -0.9749 | 0.0441 | 0.9904 |
| organiser_mean | -1.0342 | 0.0676 | 1.0598 |
| organiser_stacking | -1.0948 | 0.0807 | 1.0704 |
| stereo_dmpnn | -1.2993 | 0.1093 | 1.3322 |
| tanimoto_gp | -1.1323 | 0.0903 | 1.1660 |

¹ Higher is better: macro average precision for descriptors; negative log-threshold MAE for regression. Pooled metrics weight rows rather than folds.

## Interpretation

- No source-disjoint or prospective result is inferred from structural CV.
- Abraham processed duplicates are already aggregated.
- Pilot results do not establish the final architecture winner.

## Unavailable candidates

None in this run.

The machine-readable report includes per-label metrics, paired group-bootstrap comparisons, source caveats and configuration lineage.
Independent interval coverage must be measured on a subsequent evaluation set; calibration-set fit is not an independent coverage result.
