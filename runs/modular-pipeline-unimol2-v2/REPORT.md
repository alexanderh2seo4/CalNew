# Modular pipeline run (unimol2 anchor)

Snapshot `401a6b8f9d203429`; 5-fold grouped CV over one global structural grouping. Quality: 2589 molecules x 91 labels. Threshold: 186 air observations. Panel: 658 Keller stimuli from 326 molecules. 709 molecules excluded for earlier final tests; 273 reserved as the unopened pipeline test.

## Stage A: quality (catalogue descriptors)

| Model | macro AP | macro AUROC |
|---|---:|---:|
| pipeline_stage_A | 0.243 | 0.835 |
| logistic_explicit_fingerprint | 0.232 | 0.806 |

Panel-descriptor direction head (second vocabulary): held-out cosine 0.842 vs 0.835 for the mean training direction.

## Stage B1: air detection threshold, log10(ppbv)

| Model | MAE | RMSE | Spearman | within 3x | within 10x | fold MAE (SE) |
|---|---:|---:|---:|---:|---:|---:|
| ensemble | 0.836 | 1.084 | 0.637 | 0.366 | 0.672 | 0.824 (0.063) |
| fusion | 0.837 | 1.080 | 0.655 | 0.360 | 0.699 | 0.830 (0.050) |
| ridge_explicit_quality | 0.901 | 1.162 | 0.578 | 0.344 | 0.629 | 0.890 (0.062) |
| ridge_explicit | 0.934 | 1.167 | 0.549 | 0.323 | 0.586 | 0.920 (0.059) |
| ridge_explicit_fingerprint | 0.945 | 1.190 | 0.558 | 0.323 | 0.608 | 0.930 (0.101) |
| ridge_fingerprint | 1.027 | 1.327 | 0.453 | 0.344 | 0.581 | 1.010 (0.102) |
| null_mean | 1.214 | 1.564 | -0.129 | 0.280 | 0.489 | 1.200 (0.088) |

Ridge variants isolate the feature blocks: `ridge_fingerprint` = fingerprint; `ridge_explicit` = transport+hbond+osmophore+chain; `ridge_explicit_fingerprint` = transport+hbond+osmophore+chain+fingerprint; `ridge_explicit_quality` = transport+hbond+osmophore+chain+quality.

## Stage B2: perceived intensity (Keller, 0-100)

| Model | Pearson | RMSE |
|---|---:|---:|
| pipeline_stage_B2_hill | 0.609 | 18.324 |
| flat_ridge | 0.539 | 18.060 |
| flat_extra_trees | 0.582 | 17.205 |

## Stage C: combined descriptor profile and pleasantness

| Model | mean descriptor r | profile cosine | profile RMSE | pleasantness r |
|---|---:|---:|---:|---:|
| pipeline_oracle_intensity | 0.324 | 0.851 | 3.546 | 0.491 |
| pipeline_predicted_intensity | 0.266 | 0.849 | 3.625 | 0.365 |
| flat_ridge | 0.249 | 0.842 | 3.699 | 0.350 |
| flat_extra_trees | 0.325 | 0.859 | 3.499 | 0.481 |

`oracle` feeds measured intensity into the combiner; `predicted` feeds stage-B2 output. The gap is the error propagated from the potency stage.

## Limits

- Concentration axis: log10 solution dilution in paraffin oil (not gas-phase concentration).
- Profile targets: DREAM convention: per stimulus, sum of descriptor ratings divided by the number of participants who rated intensity; a descriptor a participant did not select counts as zero applicability for that participant.
- Mixture combination (`combine_mixture`) is an analytic literature rule and is not validated by this run.
- Out-of-fold metrics on development molecules only; the pipeline test partition was not read.
