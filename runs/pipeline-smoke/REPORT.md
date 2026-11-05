# Modular pipeline run (fingerprint anchor)

Snapshot `401a6b8f9d203429`; 3-fold grouped CV over one global structural grouping. Quality: 2589 molecules x 91 labels. Threshold: 186 air observations. Panel: 658 Keller stimuli from 326 molecules. 709 molecules excluded for earlier final tests; 273 reserved as the unopened pipeline test.

## Stage A: quality (catalogue descriptors)

| Model | macro AP | macro AUROC |
|---|---:|---:|
| pipeline_stage_A | 0.206 | 0.813 |
| logistic_explicit_fingerprint | 0.208 | 0.791 |

Panel-descriptor direction head (second vocabulary): held-out cosine 0.833 vs 0.835 for the mean training direction.

## Stage B1: air detection threshold, log10(ppbv)

| Model | MAE | RMSE | Spearman | within 3x | within 10x | fold MAE (SE) |
|---|---:|---:|---:|---:|---:|---:|
| fusion | 0.987 | 1.211 | 0.537 | 0.312 | 0.570 | 0.993 (0.035) |
| ridge_explicit | 1.002 | 1.291 | 0.523 | 0.301 | 0.575 | 1.004 (0.039) |
| ridge_fingerprint | 1.012 | 1.282 | 0.525 | 0.312 | 0.575 | 1.017 (0.031) |
| ensemble | 1.015 | 1.266 | 0.513 | 0.312 | 0.570 | 1.014 (0.006) |
| ridge_explicit_fingerprint | 1.049 | 1.410 | 0.513 | 0.339 | 0.581 | 1.053 (0.100) |
| ridge_explicit_quality | 1.210 | 1.476 | 0.457 | 0.226 | 0.462 | 1.199 (0.066) |
| null_mean | 1.216 | 1.565 | -0.079 | 0.290 | 0.495 | 1.211 (0.051) |

Ridge variants isolate the feature blocks: `ridge_fingerprint` = fingerprint; `ridge_explicit` = transport+hbond+osmophore+chain; `ridge_explicit_fingerprint` = transport+hbond+osmophore+chain+fingerprint; `ridge_explicit_quality` = transport+hbond+osmophore+chain+quality.

## Stage B2: perceived intensity (Keller, 0-100)

| Model | Pearson | RMSE |
|---|---:|---:|
| pipeline_stage_B2_hill | 0.648 | 16.910 |
| flat_ridge | 0.575 | 17.441 |
| flat_extra_trees | 0.617 | 16.698 |

## Stage C: combined descriptor profile and pleasantness

| Model | mean descriptor r | profile cosine | profile RMSE | pleasantness r |
|---|---:|---:|---:|---:|
| pipeline_oracle_intensity | 0.306 | 0.842 | 3.635 | 0.417 |
| pipeline_predicted_intensity | 0.262 | 0.841 | 3.701 | 0.305 |
| flat_ridge | 0.273 | 0.845 | 3.692 | 0.399 |
| flat_extra_trees | 0.330 | 0.855 | 3.565 | 0.492 |

`oracle` feeds measured intensity into the combiner; `predicted` feeds stage-B2 output. The gap is the error propagated from the potency stage.

## Limits

- Concentration axis: log10 solution dilution in paraffin oil (not gas-phase concentration).
- Profile targets: DREAM convention: per stimulus, sum of descriptor ratings divided by the number of participants who rated intensity; a descriptor a participant did not select counts as zero applicability for that participant.
- Mixture combination (`combine_mixture`) is an analytic literature rule and is not validated by this run.
- Out-of-fold metrics on development molecules only; the pipeline test partition was not read.
