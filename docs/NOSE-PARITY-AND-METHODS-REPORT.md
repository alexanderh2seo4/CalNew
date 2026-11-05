# NOSE parity, methods and differences

> **28 October 2026 continuation:** the new [data and model report](NOSE-RESEARCH-2026-10-28.md) supersedes the threshold row and the pending-benchmark status below. The original fixed direction blend improves a freshly fitted comparator **0.783838 to 0.792823**, with lower MAE **0.795823 to 0.762767**. The saved serving bundle and combined-model entry point pass real inference checks. The original threshold reference 0.836 and pleasantness reference 0.715 remain unmet. The historical tables below are retained with their original evidence and protocols.

Working report, **2026-10-02**. The parity goal remains active. This report replaces the earlier conclusion that mixing larger-training experiments established parity. The complete method inventory, including unsuccessful trials and source-only proposals, is in [NOSE-TECHNIQUE-LEDGER.md](NOSE-TECHNIQUE-LEDGER.md).

## What has and has not been achieved

The five-task scope comes from [CONTINUATION.md](CONTINUATION.md): Abraham air threshold, Keller pleasantness, Keller intensity, Ravia intensity and Keller descriptor strength. Under the original training partitions, both selected intensity heads and the paired descriptor evaluation exceed their paper references descriptively. Threshold and pleasantness still fall short. A new threshold recipe passed training-only selection; its frozen development benchmark is next. The earlier threshold connectivity-CV result and pleasantness validation-refit result are separate experiments; neither closes the original-protocol gap.

The full-precision references below are from [NOSE v2 Appendix A.9, Tables 24, 25, 27, 29 and 31](https://arxiv.org/html/2604.10452v2#A9), rather than the rounded main-table values. Local results are means over the ten existing development splits, seeds 42–51. This comparison measures reference-score attainment on local proxy targets, not shared-data reproduction or statistical equivalence.

| Task | Current original train-only Pearson | NOSE appendix Pearson | Current validation-refit Pearson | Original-protocol gap |
|---|---:|---:|---:|---|
| Abraham threshold | 0.785935 | 0.836 | 0.824471 | Remains below |
| Keller pleasantness | 0.692984 | 0.715 | 0.708851 | Remains below |
| Keller intensity | 0.626745 | 0.418 | 0.639398 | Above, different targets |
| Ravia intensity | 0.597362 | 0.485 | 0.607009 | Above, different targets |
| Keller descriptor strength, selected intensity into fixed C | 0.426645 | 0.348 | 0.427571 | Above, different vocabulary |

The unchanged threshold recipe's separate ten-fold connectivity CV gives pooled Pearson **0.842974**, using 166–168 training molecules. It is useful evidence for larger-training performance, not the fixed-test result of the original 111-molecule training cohort. Pleasantness **0.708851** rounds to 0.71, but remains below the appendix's **0.715**. The old rounded-precision completion claim is therefore withdrawn.

Numerical evidence was recomputed on **authorized remote compute host** by [nose_parity_evidence.py](../scripts/nose_parity_evidence.py) and saved in [nose-parity-current-audit-20261002.json](../runs/nose-parity-current-audit-20261002.json). For pleasantness and both intensity tasks, the audit checks each saved test ID and target against the current original assignment before recomputing scores. The older threshold and descriptor benchmarks retain metric summaries rather than raw task prediction arrays. The new paired descriptor audit now retains and independently verifies all twenty sets of predictions, targets and inputs.

The descriptor row comes from a [completed paired evaluation](../runs/nose-descriptor-selected-intensity-audit-v3/NOTES.md). Each unchanged original C recipe was fitted once at seed42, then received the frozen old or selected Keller intensity vector. Original macro Pearson improves **0.419521 → 0.426645** and refit **0.419144 → 0.427571**; Pearson improves in nine of ten splits and MAE in all ten, under both protocols. Nineteen exact Stage-A caches were reused; refit46 required one isolated fixed refit. [Independent verification](../runs/nose-descriptor-selected-intensity-audit-v3/verification.json) passed all20 cases. These fresh fixed-seed baselines are distinct from historical v2 summaries **0.420007 / 0.419091**; the new result directly checks the selected intensity/C combination.

## Other metrics and uncertainty

Pearson alone does not establish parity across all regression metrics. Here are the current original-training values where prediction arrays are retained. Missing values remain missing rather than being inferred from a correlation.

| Task | Local MAE / paper MAE | Local R² / paper R² | Local MSE / paper MSE |
|---|---|---|---|
| Abraham threshold | Unverified / 0.711 | Unverified / 0.652 | Unverified / 0.778 |
| Keller pleasantness | 7.622 / 6.911 | 0.441 / 0.488 | 94.303 / 89.280 |
| Keller intensity | 10.519 / 12.932 | 0.354 / 0.156 | 193.234 / 269.902 |
| Ravia intensity | 11.748 / 11.078 | 0.277 / 0.220 | 214.573 / 216.326 |
| Keller descriptor strength | 2.516 / 5.862 | 0.120 / 0.075 | 12.904 / 67.161 |

Paper metrics are from the [same appendix tables](https://arxiv.org/html/2604.10452v2#A9). In particular, the current Ravia correlation is higher while its MAE is higher too. The lower local descriptor MAE is not proof of a better shared-target model: local targets use a different vocabulary and processing.

Local standard deviations across overlapping development splits measure split sensitivity. NOSE reports three model seeds on one fixed split. Those quantities cannot be compared as confidence intervals or used to establish statistical equivalence. NOSE also uses validation for tuning/early stopping; the original local experiment fits only the training partition. [Evaluation setup](https://arxiv.org/html/2604.10452v2#A3.SS2).

## Data and evaluation differences

| Boundary | Current local work | Consequence |
|---|---|---|
| Eligible cohorts | Abraham 186; Keller 326; Ravia 114 | Smaller, filtered cohorts; original training counts 111 / 260 / 91. |
| Reserved final tests | Existing molecule, connectivity and structural exclusions stay enforced | No reserved target is admitted to fitting or scoring. Snapshot tables are parsed before filtering. |
| Original development splits | Existing molecule assignments and targets are retained | Matching a seed and ratio cannot prove matching the authors' actual rows or split IDs. |
| Validation refit | Expands training to 148 / 293 / 102 while preserving the test assignments | Reported separately; gains from larger training counts do not establish an architectural gain. |
| Threshold ten-fold CV | Connectivity-grouped out-of-fold predictions over eligible development molecules | Different training count, test aggregation and holdout protocol. |
| Keller endpoint | Each molecule's higher-concentration stimulus is the primary target; intensity models can train on both observed training-molecule stimuli | Nominal paraffin-oil dilution is not vapor concentration. |
| Descriptor targets | Twenty local semantic descriptors, macro Pearson | Their dimensions and preprocessing differ from the reference target. |
| Ravia endpoint | Published group mean at each molecule's most concentrated presentation | No subject-normalized target or validated arbitrary-dose curve. |
| Auxiliary labels | Filtered Li2025 water thresholds; filtered augmented descriptor associations | Additional supervised sources differ from the reference representation-training route. |

The paper's descriptor target has 21 dimensions and its Ravia target averages subject-normalized ratings. [Dataset processing](https://arxiv.org/html/2604.10452v2#A1). Its exact processed task tables and split IDs are absent from the inspected release; [the model card](https://github.com/Xianyusyy/NOSE/blob/5fa2d5c6846908bf37c6d4464b42dbd5d8dc759a/model/README.md) explicitly excludes training data, splits and logs. Exact scientific reproduction remains unverified.

The new audit also finds original Abraham train/test connectivity overlap `XMGQYMWWDOXHJM` in splits **42, 44, 46, 50 and 51**, plus training/validation overlaps in other splits. Ravia split **48** separates variants of `NNWHUJCUHAELCL` across training and test. Keller has no such overlap in these ten splits. Original molecule assignments are retained for paired comparisons, so those Abraham/Ravia scores do not establish fully connectivity-disjoint generalization. Auxiliary and transfer fits exclude all held connectivity variants. New selection folds use connectivity grouping.

## Architecture differences

The inspected official repository is pinned to commit `5fa2d5c6846908bf37c6d4464b42dbd5d8dc759a` for this audit. It is an inference release; no downstream training implementation or processed downstream task tables were found.

| Component | Official released implementation | Current local implementation |
|---|---|---|
| Molecular representation | Original no-hydrogen Uni-Mol wrapper, 512 dimensions | Explicit chemistry, RDKit and fingerprints are central; frozen Uni-Mol2 is used by selected tabular members; original Uni-Mol1 was separately tested. |
| Adapter layout | Separate descriptor and receptor residual adapter branches | Shallow projections of named structure blocks; no receptor-sequence branch. |
| Semantic representation | Qwen3-Embedding-8B with LoRA and ESM-2 650M receptor features, followed by multimodal adapters | Generic MiniLM descriptor-word vectors; supervised molecular prediction of 128-dimensional descriptor-derived targets. |
| Orthogonalization | Hard adapter projections in branch extraction; fused path combines raw adapter outputs with supplied normalized weights | Per-block projection off a fingerprint anchor, soft cosine penalty and learned softmax gates. |
| Training evidence | Released weights, without optimizer state, task heads or training logs | Locally fitted endpoint heads, source archives, selection plans, fold predictions and paired benchmark results. |

Official sources: [model.py](https://github.com/Xianyusyy/NOSE/blob/5fa2d5c6846908bf37c6d4464b42dbd5d8dc759a/nose/model.py), [projection.py](https://github.com/Xianyusyy/NOSE/blob/5fa2d5c6846908bf37c6d4464b42dbd5d8dc759a/nose/projection.py), [encoders.py](https://github.com/Xianyusyy/NOSE/blob/5fa2d5c6846908bf37c6d4464b42dbd5d8dc759a/nose/encoders.py), and [model card](https://github.com/Xianyusyy/NOSE/blob/5fa2d5c6846908bf37c6d4464b42dbd5d8dc759a/model/README.md). Local sources: [fusion.py](../src/calnew/pipeline/fusion.py), [stages.py](../src/calnew/pipeline/stages.py), [semantic.py](../src/calnew/pipeline/semantic.py) and [joint_intensity.py](../src/calnew/pipeline/joint_intensity.py).

No odor-trained NOSE adapter was imported. The generic pretrained molecular/text features and filtered supervised descriptor transfer do not constitute the paper's receptor/text contrastive pretraining. The released [descriptor dataset card](https://github.com/Xianyusyy/NOSE/blob/5fa2d5c6846908bf37c6d4464b42dbd5d8dc759a/data/README.md) describes augmented pairs without the original-source and strong/weak-positive metadata needed to reconstruct that training supervision. The local filtered corpus contains 7,000 molecules and 1,098,957 unique associations; these are research associations, not measured sensory responses.

## Techniques and retained outcomes

The [complete technique ledger](NOSE-TECHNIQUE-LEDGER.md) records every identified executed method and distinguishes source-only code. It includes precursor linear/tree/graph/kernel predictors; explicit feature and fusion ablations; quality/direction heads; threshold, Hill and profile heads; frozen molecular representations; flagged water auxiliaries; descriptor/text transfer; physical properties; nested kernels; regularization; robust proxy heads; transport calibration; shared-study trees; ensemble weighting; expanded-training evaluations; and serving integration.

The latest selected serving recipes remain:

- Keller intensity: half Hill, half semantic monotone dose trees; saved artifact (local artifact omitted from the public snapshot).
- Ravia intensity: 0.25 legacy ensemble + 0.25 cross-fitted Keller-proxy ridge + 0.50 shared-study trees; saved artifact (local artifact omitted from the public snapshot).
- Pleasantness: half legacy hedonic ensemble, half structure/text descriptor-transfer trees; saved artifact (local artifact omitted from the public snapshot).
- Descriptors: the unchanged C recipe benefits from the selected Keller intensity input in the new paired evaluation.
- Threshold: existing v2 remains available; the new direction/confidence blend is selected by original-training CV and awaits its frozen development benchmark.

Historical exploratory arrays have been inspected on SSH and archived in [nose-historical-exploration-audit](../runs/nose-historical-exploration-audit/NOTES.md). Recovered labels match two independent retained context snapshots. The old prediction files omit IDs, fold IDs and source hashes, so complete fold alignment remains unverified. Early downstream KFold screens reused Stage-A features computed before the downstream folds; their scores are weaker evidence than later fully nested studies. Missing final results for some seed-averaging, weighting, proxy, concentration and extra-stimulus explorations remain explicitly unverified.

## Current continuation and completion gate

Two new controlled studies were registered and executed only on SSH by [nose_parity_refine.py](../scripts/nose_parity_refine.py):

1. Separate ET/XGBoost water-source models; three-fold connectivity cross-fitted source predictions; Ridge10/100 or shallow boosted air calibration on explicit chemistry plus proxies; each standalone and fixed half/current blend.
2. Pleasantness semantic/quality boosting, standardized Ridge100, and a classical cross-fitted descriptor-direction learner; each standalone and fixed half/current-v3 blend.

Both use three repeated grouped five-fold evaluations inside original split-42 training only, with freshly refitted current comparators. The promotion gate requires mean Pearson gain at least 0.01, gains in at least two repeats and no increase in mean MAE. New water and direction source folds are grouped; the unchanged legacy semantic generator retains its own KFold crossfit with connectivity exclusions. Its method is preserved for comparator fairness.

Both studies completed and promoted **none** of their six pleasantness or eight water-calibration variants. [The final threshold audit](../runs/nose-parity-threshold-final-audit-20261002.json) independently checks all15 folds, source exclusions/counts, feature-cache identities, prediction checksums, reconstructed metrics and the unchanged gate. These are training-only results, not new test scores.

Balanced descriptor transfer computes frequencies after all fold-specific source exclusions and tests IDF-weighted average or unit-normalized targets, each standalone or fixed half/current. Its source-normalization and held-connectivity checks passed onSSH. The server now retains all15 endpoint folds,120 source fits and final results; independent reconstruction is underway. A separate zero-source-refit direction/confidence follow-up is registered.

The compact threshold spline study completed: degree-two, four-knot transforms of six physical properties, osmophore counts and optional chain/logP interactions, Ridge10/100, standalone and half/current. All15 candidate and comparator folds verified. Every variant loses all three repeats and increases MAE; **none passes**. Deterministic training transforms, held-input perturbation and missing-input checks pass.

Globally disjoint threshold semantic transfer excludes **all186** Abraham development molecule connectivities before its two balanced source fits, leaving6859 source molecules. Four fixed ET/Ridge100 endpoints and their half/current blends completed. The best IDF-unit tree blend gives mean Pearson **0.742062** against **0.732907**, with lower MAE in all repeats, but gain **0.009155** misses the unchanged0.01 gate: **none passes**.

The distinct [direction/confidence refinement](../runs/nose-threshold-disjoint-semantic-direction-inner-v1/gate-summary.json) reuses these two pinned128-dimensional arrays, normalizes each predicted vector independently and appends its original length. No source model is refitted. Its fixed half-current/IDF-unit ET blend is the only passing variant: mean Pearson **0.744156**, gain **0.011249**, mean MAE **0.712893** against **0.737901**, positive gains in all three repeats. All eight variants are retained. Its recipe is frozen before the ten-split original and separate validation-refit development evaluations; those results remain pending. Selection success does not establish test parity or serving readiness.

The pleasantness all-stimulus trial completed on260 training molecules/524 finite stimuli, using the existing hedonic and semantic trees and their equal ensemble, each standalone or half/current. Held molecules' stimuli stay excluded; evaluation uses original higher-concentration training-fold targets. Equal weight per stimulus gives molecules with more valid presentations more fitting weight. All15 nested feature caches were verified before fitting; no source model was retrained. **None of six variants passes.** The strongest blend has mean Pearson **0.705007** versus **0.702819**, but MAE **8.046297** versus **8.018147**. [Independent reconstruction](../runs/nose-pleasantness-trials-audit-20261002.json) confirms saved predictions, IDs/targets, stimuli boundaries and the failed gate.

Completion requires closing the original-train-only reference-score gaps with a recipe selected inside training, then evaluating that fixed recipe on all ten unchanged test assignments and updating this report and ledger with the full evidence. A scientific reproduction claim additionally needs shared processed targets/splits and matching training/evaluation procedures; these have not been established. The six further paper tasks—Sagar pleasantness, intensity and descriptor strength; GS–LF classification; and Ma mixture pleasantness and intensity—plus retrieval studies remain unevaluated rather than being treated as completed.

## Reproduction and compute boundary

All current numerical work uses `compute-host`, checkout `C:\calnew`, existing Python `C:\calnew-compute\.venv\Scripts\python.exe`, and [ssh_compute.py](../scripts/ssh_compute.py). Earlier local results remain historical; all work after the SSH-only instruction stays on the server. Unrelated jobs and the old checkout are preserved. Local operations are file editing, inspection, transfer and formatting checks.

```powershell
Set-Location 'C:\calnew'
$calnewPython = 'C:\calnew-compute\.venv\Scripts\python.exe'
& $calnewPython scripts/ssh_compute.py scripts/nose_parity_evidence.py
& $calnewPython scripts/ssh_compute.py scripts/nose_parity_refine.py `
  --datasets abraham --out runs/my-fresh-threshold-study
& $calnewPython scripts/ssh_compute.py scripts/nose_parity_refine.py `
  --datasets keller --out runs/my-fresh-pleasantness-study
```

Use fresh output directories. Do not reuse a fold checkpoint after changing source data, features, dependencies or code. Earlier intensity integration has **71 passing SSH tests** and saved-bundle CLI/API checks, with detailed commands in [INTENSITY-IMPROVEMENT.md](INTENSITY-IMPROVEMENT.md). Those tests do not establish the statistical validity or superiority of a new research recipe; the registered selection and frozen benchmark are separate requirements.
