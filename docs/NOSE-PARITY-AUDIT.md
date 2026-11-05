# NOSE parity audit — updated 2026-10-02

**Parity is incomplete.** The new [methods and differences report](NOSE-PARITY-AND-METHODS-REPORT.md) uses full-precision appendix references and verifies the current retained arrays on SSH. Original train-only threshold is **0.785935 versus 0.836**, and pleasantness is **0.692984 versus 0.715**. Pleasantness refit **0.708851** remains below 0.715 despite rounding to 0.71. The earlier mixed-protocol completion claim is withdrawn. The [complete technique ledger](NOSE-TECHNIQUE-LEDGER.md) includes unsuccessful and unverified explorations. New grouped training-only studies are continuing without scoring reserved partitions.

Later intensity work improves Keller's paired refit Pearson to **0.639** and Ravia's to **0.607**, with all resumed compute on SSH and 71 passing tests. The latest Ravia head improves on its previous proxy-ridge head in both Pearson (0.589 → 0.607) and MAE (12.060 → 11.855). See [INTENSITY-IMPROVEMENT.md](INTENSITY-IMPROVEMENT.md) for original-training results, frozen recipes, saved serving artifacts and the pre-existing Ravia split-48 connectivity overlap. The table below records the earlier parity goal's outcome; exact paper parity and fully connectivity-disjoint development performance remain unverified.

The existing v2 pipeline remains available; the improved pleasantness head is saved and can be selected with `--semantic-run`. Reserved final-test molecules have not been scored or admitted to training in these experiments. Changed-protocol scores are useful development evidence but do not establish the original-protocol performance target, exact NOSE reproduction or statistical equivalence.

The goal currently follows the five tasks in `CONTINUATION.md`. This is not reproduction of all eleven NOSE tasks or its retrieval experiments.

## Historical mixed-protocol comparison

| Task | Local Pearson | NOSE reference | Local evaluation |
|---|---:|---:|---|
| Abraham threshold | **0.843** | 0.840 | Ten-fold connectivity CV, 166–168 training rows, three model seeds |
| Keller pleasantness | **0.709** | 0.710 | Fixed v3 blend; ten development splits, train+validation refit |
| Keller intensity | **0.578** | 0.420 | Fixed v2; ten development splits, train+validation refit |
| Ravia intensity | **0.562** | 0.490 | Fixed v2; ten development splits, train+validation refit |
| Keller descriptor strength | **0.419** | 0.348 | Fixed v2; ten development splits, train+validation refit |

Pleasantness is 0.708851, which rounds to the main table's 0.71 but remains below the appendix's 0.715. This is a **local development comparison**, not a shared-data leaderboard comparison. Threshold's pooled CV metric and the other tasks' mean over development splits differ from the paper's fixed-test metric. Sample sizes, processed targets and descriptor dimensions also differ. The original train-only benchmark gaps remain visible below; changing evaluation training counts does not demonstrate a new threshold architecture improvement.

The serving artifact is `runs/nose-semantic-pleasantness-v3/semantic-pleasantness.joblib`. It is fitted on all 326 eligible Keller development molecules. API/CLI integration was checked on an eligible molecule: the optional head changes pleasantness, while threshold, intensity, dose parameters and descriptor profiles retain their prior predictions. The head is validated for Keller higher-concentration stimuli. **58 tests pass.**

```bash
.venv/bin/python -m calnew pipeline predict \
  --run runs/modular-pipeline-fingerprint-v5 \
  --semantic-run runs/nose-semantic-pleasantness-v3 \
  --smiles "CC(C)CCO" --dilution 1e-3
```

## Existing benchmark

Run `runs/nose-protocol-v4`, Pearson means over ten development splits:

| Task | CALNEW v2 | Published NOSE reference | Difference |
|---|---:|---:|---:|
| Abraham threshold | 0.786 | 0.840 | −0.054 |
| Keller pleasantness | 0.673 | 0.710 | −0.037 |
| Keller intensity | 0.569 | 0.420 | +0.149 |
| Ravia intensity | 0.539 | 0.490 | +0.049 |
| Keller descriptor strength | 0.420 | 0.348 | +0.072 |

These are descriptive comparisons. CALNEW uses fewer molecules, different Keller/Ravia targets, and different splits. The paper reports variability across model seeds on a fixed split; CALNEW's robustness table measures variability across overlapping splits. Their standard deviations cannot be used to establish statistical equivalence. The paper explicitly specifies macro averaging for multi-label regression.

Primary reference: [NOSE v2, Tables 3, 4 and Appendix A.3.2](https://arxiv.org/html/2604.10452v2).

## New training data

The [authors' released descriptor corpus](https://github.com/Xianyusyy/NOSE/blob/main/data/README.md) was downloaded and its pinned SHA256 verified:

`858e482f407a3577870a87a61f8f16b488412ed06922dd35dd8d4fe4cf5e6ff2`

After canonicalization, removal of invalid/salt/mixture structures, and the existing reserved connectivity/scaffold exclusions, it contains **7,000 usable molecules, 1,086 descriptor terms and 1,098,957 unique associations**. The archive contains no source identifiers or strong/weak-positive labels. These are augmented research associations, not measured panel responses; source-code licensing does not replace the underlying dataset terms.

The released molecular NOSE weights are not used. Transfer learners are fitted locally on filtered corpus rows, excluding each main validation/test molecule and every inner validation molecule by connectivity. Downstream training features are cross-fitted as well. This preserves the final-test exclusion rules instead of importing an odor checkpoint whose pretraining overlap cannot be removed.

## Completed exploratory checks

All scores below are **inner cross-validation**, inside the split-42 training portion only. They are not new paper-benchmark test results.

| Experiment | Abraham threshold | Keller pleasantness |
|---|---:|---:|
| Structure trees, three repeats | 0.697 | 0.688 |
| Structure + linear descriptor transfer, three repeats | 0.695 | 0.697 |
| Structure + nonlinear descriptor transfer, first repeat | 0.739 | 0.700 |
| Structure + measured Abraham properties, three repeats | 0.693 | 0.687 |

Linear transfer offers no threshold gain and only a small pleasantness gain. Independently measured E/S/A/B/L/V descriptors add no gain; the loader explicitly excludes odor targets and assay/source indicators. Neither route is promoted.

The nonlinear candidate was compared with the **full v2 model**, with stage A nested anew inside each validation fold. Three threshold repeats give v2 **0.751** and the equal blend **0.756**; pleasantness gives **0.695 → 0.703**. These gains are below the subsequent text-candidate promotion rule.

A second transfer target uses generic text embeddings of descriptor words. The [MiniLM encoder](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) is pinned to revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; it receives descriptor words only. Its local vector artifact is checked for shape, finiteness, vocabulary order and checksum before molecular transfer training. The completed three repeats use a fixed promotion rule: mean gain of at least 0.01 over the nested v2 baseline, positive gain in at least two repeats. **Pleasantness passes: 0.695 → 0.711 for the equal v2/text blend, with gains in all three repeats.** Structure+text alone gives 0.706 and also passes. No threshold candidate passes. Exact ID/target alignment was verified before reusing the nested v2 predictions. No paper-benchmark test result was used for this choice. The selected equal pleasantness blend completed the separately registered ten-split train-only evaluation: **v2 0.6732 → v3 0.6930**, with gains in all ten splits. NOSE’s reference mean is 0.710. The separate development-validation refit gives **0.6872 → 0.7089**, with gains in nine of ten splits. Mean split MAE also improves: 7.709 → 7.622 in train-only evaluation and 7.532 → 7.422 after refit. The default model remains unchanged; the optional serving head has been fitted on all eligible development molecules and checked in the full prediction API. Saving initially encountered an empty-held-set edge case after evaluation had completed; the tested fix reran only the final fit, preserving the benchmark scores.

## Original Uni-Mol check

The original Uni-Mol1 molecular checkpoint used by NOSE is now cached separately from the previously tried Uni-Mol2 encoder. Generic unlabeled weights from `dptech/Uni-Mol-Models` are pinned to revision `9f19c45c718192888a1c8a1c905f69f0755ea502`. No odor-trained NOSE adapters are imported. One optimized ETKDGv3 conformer produces each frozen 512-dimensional vector plus an availability flag. Of 7,216 corpus/development molecules, 7,129 have valid geometry/embeddings; missing geometry stays unavailable, without a flat substitute.

A registered three-repeat training-only experiment compares direct molecular features and text-descriptor transfer using these features. A separate fixed 256/128 neural adapter, trained for 40 epochs on descriptor vectors, tests whether trees were limiting use of the dense embeddings. Both use mean gain ≥0.01 over fully nested v2, positive in at least two repeats; no endpoint test score enters selection. Threshold checks are complete and neither passes. The best 3D tree blend gives 0.747 versus v2 0.751; the neural structure/semantic blend gives 0.735. A separate nested kernel check (descriptor SVRs and fingerprint Tanimoto GP) also fails; its best fixed v2 blend gives 0.730. These candidates are not promoted. Pleasantness 3D checks also fail: their best fixed blend gives 0.702 versus v2 0.695, below the 0.01 promotion threshold. The generic-text blend remains selected.

## Separate development-validation refit

The fixed v2 recipes were also evaluated after refitting on the unused development-validation molecules. Original test assignments and every reserved exclusion are retained. Training counts become 148 Abraham molecules, 293 Keller molecules and 102 Ravia molecules. This changes the ratios to approximately 80/0/20 and 90/0/10; results must be reported separately from the train-only experiment.

`runs/nose-development-refit-v1/protocol.json` records this protocol before fitting, and `source-code/` archives the executing package. The registered evaluation uses model seeds 42–44 and ten split seeds 42–51. The experiment is complete and does not change semantic-transfer selection criteria. Results over the ten splits:

| Task | Train-only v2 | Train+validation v2 | Published NOSE reference |
|---|---:|---:|---:|
| Abraham threshold | 0.786 | **0.824** | 0.840 |
| Keller pleasantness | 0.673 | **0.687** | 0.710 |
| Keller intensity | 0.569 | 0.578 | 0.420 |
| Ravia intensity | 0.539 | 0.562 | 0.490 |
| Keller descriptor strength | 0.420 | 0.419 | 0.348 |

Threshold and pleasantness still fall short of the reference means. Effective training ratios and target definitions differ from NOSE, so these improvements do not establish paper reproduction or statistical equivalence.

## Larger threshold training count

The unchanged v2 threshold recipe completed ten-fold connectivity CV, fold seed 42 and model seeds 42–44. Each fit uses 166–168 development rows, close to NOSE’s 160, and every eligible row receives an out-of-fold prediction. Two stereoisomer pairs sharing connectivity stay in one fold. This protocol is separate from both the original train-only split and the validation refit; pooled CV Pearson is not its fixed-test Pearson. No model is selected or retuned using these scores. Pooled Pearson is **0.842974**, with per-seed results 0.844377, 0.844626 and 0.839918 (seed SD 0.002163). The initial setup requiring unique connectivity stopped before fitting; the grouped run corrects that requirement. The sequential run was checkpointed and completed in per-seed workers. Checkpoint values were verified bitwise unchanged, all final predictions finite, and every held connectivity group disjoint from training. The protocol, original and worker source archives, final predictions and execution checks are retained in `runs/nose-threshold-grouped-tenfold-v2/`.

## Reproduce

Install the project's normal dependencies and download the pinned descriptor archive into `data/raw/nose/v1.0.0/`. Use a fresh output directory per run.

```bash
.venv/bin/python scripts/nose_semantic_experiment.py \
  --out runs/my-linear-transfer --repeats 3

.venv/bin/python scripts/nose_semantic_experiment.py \
  --out runs/my-nonlinear-transfer --encoder extra_trees --include-v2 --repeats 3

.venv/bin/python scripts/abraham_properties_experiment.py \
  --out runs/my-physical-properties --repeats 3

.venv/bin/python scripts/build_descriptor_word_vectors.py
.venv/bin/python scripts/nose_semantic_experiment.py \
  --out runs/my-text-transfer --encoder extra_trees \
  --word-vectors data/features/nose-descriptor-minilm.npz --repeats 3

.venv/bin/python scripts/build_unimol1_vectors.py
.venv/bin/python scripts/nose_semantic_experiment.py \
  --out runs/my-unimol1-transfer --encoder extra_trees \
  --word-vectors data/features/nose-descriptor-minilm.npz \
  --molecular-vectors data/features/unimol1-research/vectors.npz --repeats 3

.venv/bin/python scripts/nose_semantic_benchmark.py \
  --out runs/my-selected-pleasantness --fit-final

.venv/bin/python -m calnew pipeline paper-benchmark \
  --out runs/my-development-refit --refit-validation \
  --robustness-splits 43 44 45 46 47 48 49 50 51

.venv/bin/python scripts/nose_threshold_cv.py \
  --out runs/my-threshold-connectivity-cv

.venv/bin/python -m calnew pipeline predict \
  --run runs/modular-pipeline-fingerprint-v5 \
  --semantic-run runs/my-selected-pleasantness --smiles "CC(C)CCO"
```

Run directories contain source manifests, inner-fold predictions and results. `runs/` and `data/` remain ignored; this document records the durable conclusions. **58 automated tests pass**, including connectivity exclusion, cross-fitting, target-column separation and preservation of test assignments during validation refit. A candidate must improve the fully nested development comparison before a fixed benchmark evaluation or production integration. Final production fits already use all eligible development data, so the validation-refit experiment increases evaluation training counts rather than changing the deployed v2 recipe. Increasing training data does not guarantee the paper's scores, and consuming reserved holdouts remains disallowed without a new user decision.
