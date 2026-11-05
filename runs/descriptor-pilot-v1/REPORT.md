# CALNEW — catalogue_descriptor

**Status:** computational_pilot. Prospective validation: not_performed.

Source: `leffingwell`. 3522 rows; 2466 development, 528 calibration and 528 reserved test rows.

Selected by the declared one-standard-error rule: **organiser_mean**. This is a development selection.

| Candidate | Outer-fold mean score¹ | Standard error | Pooled development metric |
|---|---:|---:|---:|
| descriptor_linear | 0.2275 | 0.0215 | 0.1956 |
| fingerprint_rf | 0.2180 | 0.0163 | 0.1714 |
| fingerprint_xgb | 0.2118 | 0.0168 | 0.1808 |
| organiser_gating | 0.2402 | 0.0236 | 0.1957 |
| organiser_mean | 0.2548 | 0.0184 | 0.2176 |
| organiser_stacking | 0.2277 | 0.0178 | 0.1831 |
| stereo_dmpnn | 0.1740 | 0.0134 | 0.1348 |

¹ Higher is better: macro average precision for descriptors; negative log-threshold MAE for regression. Pooled metrics weight rows rather than folds.

## Interpretation

- No source-disjoint or prospective result is inferred from structural CV.
- Abraham processed duplicates are already aggregated.
- Pilot results do not establish the final architecture winner.

## Unavailable candidates

None in this run.

The machine-readable report includes per-label metrics, paired group-bootstrap comparisons, source caveats and configuration lineage.
Independent interval coverage must be measured on a subsequent evaluation set; calibration-set fit is not an independent coverage result.
