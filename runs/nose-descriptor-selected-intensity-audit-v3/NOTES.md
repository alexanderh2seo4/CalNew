# Paired descriptor evaluation with selected Keller intensity

Completed **2026-10-02**, on SSH host the authorized remote compute host, in the isolated `calnew-intensity-20261001` checkout. All fitting, predictions, metric calculation and verification ran on that server with two threads. Local work was editing and evidence transfer.

Twenty unchanged development cases were evaluated: the original train-only partitions and validation-refit partitions for split seeds 42–51. Each has 33 test molecules and twenty descriptor targets. Original training contains 260 molecules; validation-refit contains 293. Existing reserved final partitions and held-connectivity exclusions remain enforced.

For each partition, the original `CombinerStage` profile recipe was fitted once at model seed 42 with measured training intensities. The same fitted profile model then received either the frozen old intensity vector or the frozen selected Keller v3 vector. The profile definitions have identical ASTs to the original archived producer. Training retains 400 epochs and the original grouped, training-only penalty choice among 0.01/0.1/1/10/100. No new head, hyperparameter study or test-based selection was introduced. These are paired development results, not a new production-head promotion.

## Mean results across the ten unchanged test assignments

| Protocol / intensity input | Macro Pearson (split SD) | MAE | Macro R² | MSE |
|---|---:|---:|---:|---:|
| Original train-only / old | 0.419521403 (0.066111488) | 2.556208078 | 0.096719996 | 13.121764707 |
| Original train-only / selected Keller v3 | 0.426645044 (0.066333772) | 2.515651004 | 0.120279528 | 12.904100085 |
| Validation-refit / old | 0.419143814 (0.063947087) | 2.547636739 | 0.103628512 | 12.932754673 |
| Validation-refit / selected Keller v3 | 0.427571093 (0.064357696) | 2.509885599 | 0.125416860 | 12.737825209 |

Within each protocol, the selected intensity improves macro Pearson in **9/10** splits and MAE in **10/10**. Split sensitivity is not a confidence interval; the overlapping test assignments are not independent replications. Per-descriptor scores and a secondary flattened Pearson are preserved in `results.json`.

The fresh fixed-seed old-intensity baselines are distinct from the earlier saved v2 summary values **0.420007** and **0.419091**. The paired comparison directly validates substitution into this unchanged, freshly fitted profile recipe; it does not recreate every historical training seed or assert exact historical baseline replication. These local twenty-dimensional targets also differ from the paper's processed descriptor endpoint.

## Features and provenance

All twenty frozen intensity files passed exact test-ID/target, original assignment, selection-checksum, shape, finiteness and range checks. Nineteen Stage-A quality/direction caches exactly matched the current producer identity. Validation-refit split 46 required one fixed original seed-42 Stage-A refit: its previous producer hash could not be proved equivalent. That refit is isolated in this result directory under `stage-A-fixed-refits`; unknown historical caches were preserved. No migrated cache was used. `cache-inventory.json` and `resource-manifest.json` preserve the full evidence.

`verify_results.py` independently read every saved paired prediction file and verified all twenty sets of raw metrics, summary aggregates, test/training/validation IDs, frozen intensity arrays, feature-cache/model checksums, archived source hashes and installed dependency versions. It fitted no models. See `verification.json`; the primary computation finished successfully in SSH session 19749, with 338 seconds recorded for the twenty C fits and evaluations after preflight. The one Stage-A refit preceded that timed section.

Every case retains `.npz` predictions, IDs, descriptor targets, intensity inputs, doses, quality/direction features and descriptor names; `.joblib` fitted profile model; and `.json` metrics, training-only penalty-selection results and provenance. `source-code`, `protocol.json` and `resource-manifest.json` record the exact implementation and resources.

The earlier `nose-descriptor-selected-intensity-audit-v1`, `-v2` and `nose-descriptor-selected-intensity-preflight` directories are failed cache-identity preflight records. They produced no profile benchmarks. They are retained without being treated as completed evidence.
