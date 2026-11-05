# NOSE data and model improvement, 28 October 2026

The official paper and dataset have been acquired and checked. A cleaned, independently audited transfer corpus is available. The previously selected threshold direction/confidence recipe improves a fresh paired comparator on the ten unchanged original development splits. This is a modest improvement on local proxy targets; it does not establish NOSE reproduction or prospective sensory accuracy.

## Downloaded and curated material

- Published ACL paper, 33 pages (local artifact omitted from the public snapshot), arXiv reference PDF (local artifact omitted from the public snapshot), and [acquisition record](../data/documents/nose-20261028/SOURCES.md).
- Original released dataset (local artifact omitted from the public snapshot). Its SHA256 matches the official sidecar: `858e482f407a3577870a87a61f8f16b488412ed06922dd35dd8d4fe4cf5e6ff2`.
- Cleaned dataset ZIP (local artifact omitted from the public snapshot), [manifest](../data/curated/nose-20261028-v1/manifest.json), and [format guide](../data/curated/nose-20261028-v1/README.md).

The release has 2,567,558 rows, including 1,054,030 repeated rows. Curation canonicalizes molecular identities, preserves stereochemistry, removes repeated canonical associations, and quarantines 474 invalid/disconnected SMILES. The initial reserved-group filtering leaves 7,000 molecules and 1,098,957 pairs. An additional conservative exclusion of all 489 Abraham/Keller/Ravia development connectivities leaves **6,445 molecules and 934,458 unique binary associations**, with a 1,086-term vocabulary. File checksums, foreign-key joins, unique pairs, sparse-matrix alignment and endpoint disjointness were checked on SSH.

These improvements concern identity, duplication, reproducibility and evaluation integrity. They do not validate the descriptor associations as human sensory measurements. The release omits per-pair strong/weak-positive annotations and upstream provenance. Curation preserves that limitation and does not invent confidence labels. Underlying dataset terms remain applicable.

## Verified original threshold evaluation

The frozen recipe was selected inside the original 111-molecule training portion by three repetitions of connectivity-grouped five-fold evaluation. It passed the existing gate: mean Pearson gain at least 0.01, improvement in at least two repeats, and no mean MAE increase. Training Pearson was 0.732907 to 0.744156 and MAE 0.737901 to 0.712893. This selection preceded the development benchmark.

The fixed prediction is half the current threshold ensemble and half an ExtraTrees head using explicit molecular features plus a predicted descriptor-vector direction and its original norm. The descriptor source excludes every Abraham development connectivity and all earlier reserved groups. No source model was refitted during benchmark scoring.

| Ten original development splits, seeds 42-51 | Fresh current comparator | Fixed selected blend |
|---|---:|---:|
| Mean Pearson | 0.783838 | **0.792823** |
| Mean MAE, log10 units | 0.795823 | **0.762767** |
| Mean R2 | 0.579922 | **0.606760** |
| Mean MSE | 1.092746 | **1.033683** |

Pearson improves in 8/10 splits and MAE in 9/10. These are overlapping development splits, not ten independent experiments. Five original Abraham splits retain the previously documented primary connectivity overlap. No reserved final target was fitted or scored. The historical comparator 0.785935 differs from this freshly fitted comparator and is not substituted into the paired comparison.

The published ACL paper retains the full-precision references **0.836** for threshold and **0.715** for Keller pleasantness (Tables 24/25, printed pages 19640/19641). The original threshold gap remains. Local target processing, cohort sizes and split assignments differ from NOSE; attaining a reference point estimate would still not prove reproduction.

Evidence: [original benchmark](../runs/nose-threshold-direction-original-v1/results.json), [independent reconstruction](../runs/nose-research-independent-audit-20261028.json), and [benchmark script](../scripts/nose_threshold_direction_benchmark.py).

The separate [validation-refit benchmark](../runs/nose-threshold-direction-refit-v1/results.json) is complete with 148 training molecules rather than 111 and the original test assignments fixed. Fresh paired Pearson is **0.822570 to 0.828785**, MAE **0.723185 to 0.705304**, R2 **0.658213 to 0.671192**. Mean Pearson increases, but only 4/10 individual splits improve; MAE improves in 8/10. This protocol remains separate from the original train-only result and does not close its reference gap.

## New training-only experiments

Both new studies retained the original training cohorts and independently verified all fifteen comparator folds before fitting. Main validation/test labels and reserved targets were not scored. The same unchanged promotion gate was used.

1. **Compact CatBoost heads:** fixed depth-four, 700-iteration RMSE/MAE heads on compact chemistry or the broader fingerprint feature set, and their half/current blends. No candidate passes for threshold or pleasantness. [Results](../runs/nose-compact-heads-inner-20261028-v1/results.json).
2. **Descriptor co-occurrence transfer:** the new globally endpoint-disjoint curated corpus supplies source-only TF-IDF/SVD64 targets, then a 150-tree molecular transfer model. Fixed raw/direction representations feed tree or Ridge100 heads, standalone and half/current. No candidate passes for either endpoint. The fitted source model and all negative results are retained. [Results](../runs/nose-cooccurrence-inner-20261028-v1/results.json).

These studies do not replace the existing pleasantness or intensity models. The official NOSE adapters were not imported: their pretraining overlap with the reserved molecules cannot be audited from the release.

## Usable threshold bundle and checks

The frozen direction recipe has been fitted on all 186 eligible development molecules for serving. A separate serialization fit recreates the evaluated descriptor source: predictions match its pinned arrays exactly (maximum error zero). Cross-fitted quality features fit endpoint heads; the final quality source model serves new molecules.

The saved model (local artifact omitted from the public snapshot), [serving manifest](../runs/nose-threshold-direction-serving-20261028-v1/serving.json) and [real-model smoke result](../runs/nose-threshold-direction-serving-20261028-v1/smoke.json) are available locally and on SSH. Serialized and public-API predictions agree with the fitted feature matrices within 2.23e-16. A missing SSH Uni-Mol dependency caught by the initial smoke check was installed; the matching cached molecular features were transferred and checksummed. A further [uncached-molecule check](../runs/nose-threshold-direction-serving-20261028-v1/novel-molecule-smoke.json) successfully generated new Uni-Mol2 conformer features and served predictions on SSH.

Inference entry point: [predict_threshold_direction.py](../scripts/predict_threshold_direction.py). It returns airborne detection threshold in log10(ppbv) and ppbv; the internal reciprocal-ppm target is converted as `log10(ppbv) = 3 - prediction`. From the SSH checkout:

```powershell
C:\calnew-compute\.venv\Scripts\python.exe scripts\ssh_compute.py scripts\predict_threshold_direction.py --smiles CCO
```

For the combined selected model, [predict_olfaction_selected.py](../scripts/predict_olfaction_selected.py) combines the new threshold head, the retained Keller intensity refinement, the existing pleasantness semantic head and the profile pipeline. It verifies molecular alignment and replaces the complete old threshold object, removing the old model's interval. The [combined real-model smoke output](../runs/nose-threshold-direction-serving-20261028-v1/all-endpoint-smoke.json) checks two molecules through all heads, including the previously uncached molecule.

```powershell
C:\calnew-compute\.venv\Scripts\python.exe scripts\ssh_compute.py scripts\predict_olfaction_selected.py --smiles CCO --dilution 0.001
```

All fitting, prediction, dataset analysis and tests run on the authorized remote compute host, in `C:\calnew`, using the existing Python environment and `scripts/ssh_compute.py`. The full suite passes **79/79**, including serialization, immutable source preprocessing, target-unit conversion, checksum checks, molecular identity alignment, removal of the old interval and measured-source connectivity exclusions. Package versions are retained in the serving directory's `ssh-packages.json`; CatBoost 1.2.8 was installed for the rejected new trials, while Uni-Mol Tools 0.1.6 and Transformers 5.17.0 support inference.

## Connectivity-disjoint development sensitivity

A separate ten-fold connectivity check uses 166-168 training molecules per fold and retained baseline OOF arrays for model seeds 42/43/44. The historical source archive, IDs, targets, fold assignments and baseline score reconstruction were checked before evaluating the unchanged blend. The selected branch source excludes all 186 primary connectivities. Mean pooled Pearson is **0.842974 to 0.841964** (slightly lower); MAE is **0.692024 to 0.673389** (lower in all three model seeds), and R2 is **0.689162 to 0.697131**. [Saved results](../runs/nose-threshold-direction-structural-20261028-v2/results.json).

This is a development sensitivity analysis, not a new independent nested-selection result: the recipe was selected earlier using part of this development cohort. It supports lower development absolute error under connectivity separation, without showing a correlation improvement or establishing paper parity. The first structural setup stopped before fitting because the old SSH source archive was absent; the exact local archive was transferred and verified, and the completed analysis uses a fresh directory.

No calibrated prospective prediction interval is claimed for the new bundle. Reserved final evaluation remains a separate future decision. The broad “good model” goal is not marked complete merely because a development score improved.

## Additional measured-source continuation

The [Sagar2023 author deposit](https://github.com/viveksgr/NEMO_scripts), pinned at `6c4169b7d92b063d9ce011afe8cb4790a4ffe8aa`, supplies three small behavioral MAT files and identity/concentration spreadsheets. Only these behavioral files and interpretation code were downloaded. Their union has195 CIDs, despite each participant having160 rows. Nine conflicting stereochemical mappings are quarantined;186 CIDs resolve unambiguously, and115 remain after the existing reserved-group exclusions. [Identity and scale audit](../runs/sagar-source-audit-20261028-v2/report.json). Allowed endpoint values lie in the supplied [-1,1] scale; they are not converted into Keller observations.

A new registered trial learned fifteen common measured perceptual dimensions from the allowed source. Three explicitly recorded name aliases align flowery/floral, bakery-like/bakery and spicey/spicy. Every source fit excluded main-held, outer-held and its own crossfit feature-fold connectivities; source target standardization was fitted after those exclusions. Two fixed endpoint heads and two half/current blends were evaluated only inside the original Keller training260 cohort. **None passes**. The strongest blend gives Pearson0.697971 and MAE8.105557 versus current0.702819 and8.018147. Existing pleasantness serving remains unchanged. [Registered script](../scripts/nose_sagar_refine.py), [results](../runs/nose-sagar-measured-profile-inner-20261028-v1/results.json), [independent gate reconstruction](../runs/nose-research-independent-audit-20261028.json). Two additional source-exclusion tests confirm that perturbing forbidden source labels cannot affect the fitted source and that each feature fold excludes its own connectivity.

The next research step should add a different biological or measurement signal, rather than rerunning these failed source/head variants. Original threshold and pleasantness reference-score gaps remain, and no prospective validation has been performed.
