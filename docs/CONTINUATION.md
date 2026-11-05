# Continuation report — NOSE parity work

> **Verified update, 2026-10-28:** the original frozen direction/confidence threshold benchmark is now complete. Fresh paired ten-split Pearson improves **0.783838 to 0.792823**, MAE **0.795823 to 0.762767**, with Pearson wins in 8/10 and MAE wins in 9/10. A usable bundle is saved at `runs/nose-threshold-direction-serving-20261028-v1`; its source predictions reproduce the evaluated source arrays exactly, serialization/public serving match within 2.23e-16, and uncached-molecule inference works on SSH. The combined entry point is `scripts/predict_olfaction_selected.py`. The new CatBoost and cleaned-corpus TF-IDF/SVD transfer trials pass no promotion gates for threshold or pleasantness. A separate connectivity-disjoint development check lowers MAE 0.692024 to 0.673389 while Pearson stays essentially unchanged, 0.842974 to 0.841964. The separate validation-refit benchmark also improves Pearson **0.822570 to 0.828785** and MAE **0.723185 to 0.705304**. The subsequent Sagar measured-profile transfer trial passes no pleasantness gate. The final SSH suite passes **79/79** tests. The NOSE original-protocol reference gaps remain; the goal is not declared complete. See [the new report](NOSE-RESEARCH-2026-10-28.md) for downloaded papers, the audited 6,445-molecule/934,458-pair dataset, tests, evidence and commands. All numerical work remains on SSH and final holdouts remain closed.

> **Parity correction, 2026-10-02:** the goal remains active. Full-precision appendix references are threshold **0.836** and pleasantness **0.715**; original train-only means remain **0.785935** and **0.692984**. The mixed-protocol rounded-precision completion claim below is superseded. The new SSH audit verifies retained test IDs/targets, recomputes available regression metrics, and finds Abraham training/test connectivity overlap in splits42/44/46/50/51 in addition to Ravia split48. See [NOSE-PARITY-AND-METHODS-REPORT.md](NOSE-PARITY-AND-METHODS-REPORT.md) and the complete [technique ledger](NOSE-TECHNIQUE-LEDGER.md) for the latest completed studies and pending frozen evaluations. Preserve SSH-only compute, original development assignments and reserved final exclusions.

> **Further verified progress, 2026-10-02:** the water-calibration and restricted spline studies completed without a passing variant. A disjoint semantic direction/confidence threshold blend passes the original111 training-only gate (Pearson **0.732907→0.744156**, MAE **0.737901→0.712893**, positive in3/3 repeats); its frozen ten-split original and separate refit benchmark is next, so test parity is still unproven. The all-stimulus pleasantness study completed with no passing variant; balanced semantic results are retained and being audited before a separate direction/confidence continuation. The selected Keller intensity now has a completed paired descriptor-C evaluation: original macro Pearson **0.419521→0.426645**, refit **0.419144→0.427571**, with lower MAE in every split under both protocols. These fresh fixed-C baselines differ from the historical v2 summaries below. All numerical work and verification ran onSSH.

> **Latest intensity update, 2026-10-01:** Keller retains paired ten-split Pearson **0.627** under original training and **0.639** after validation refit. A further Ravia shared-study blend improves the previous proxy-ridge head **0.580 → 0.597** and **0.589 → 0.607**, respectively; refit MAE improves **12.060 → 11.855**. The new Ravia artifact is `runs/nose-intensity-ravia-joint-refit-v2`. All eleven refinement trials, both ten-split evaluations, final fitting, serving checks and **71 passing tests** ran on compute-host. Reserved final exclusions remain enforced. Original Ravia split 48 has a primary training/held connectivity overlap; source exclusions remain strict, and this development limitation is documented in [INTENSITY-IMPROVEMENT.md](INTENSITY-IMPROVEMENT.md). Models and evidence are synced locally. Keep the SSH-only compute restriction for further work. The historical v2 table below remains unchanged.

> **Historical 2026-10-01 comparison, superseded as a completion claim:** threshold 0.843 (ten-fold connectivity CV), pleasantness 0.709, Keller intensity 0.578, Ravia intensity 0.562 and descriptor strength 0.419 (the latter four used expanded development training). Those changed protocols and rounded reference values did not prove original-protocol parity. Reserved final partitions remain excluded. The improved pleasantness artifact is `runs/nose-semantic-pleasantness-v3`; use `pipeline predict --semantic-run` to select it. See [NOSE-PARITY-AUDIT.md](NOSE-PARITY-AUDIT.md) for the original-protocol gaps, completed experiments and commands.

Initial handoff: **2026-10-01**, branch `modular-pipeline`, model commit `383094e` (pushed), 44 tests passed. The goal has since resumed; see [the parity audit](NOSE-PARITY-AUDIT.md) for new filtered-data experiments and the current conclusions. The historical modelling results below remain valid.

This report exists so the next session does not repeat work that has already been done and measured. Three of the five reported means exceed the paper's reference values; two remain lower. These are descriptive comparisons on different datasets and targets, not established benchmark parity. Smaller training sets plausibly contribute to the gap, but the measurements do not establish that training-set size is its sole cause. Previously tested modelling changes are below, including the ones that failed.

## Where the numbers stand

Test-set Pearson under the NOSE protocol (`arXiv:2604.10452`). The column to trust is the ten-split mean: single-split test sets hold only 11–38 molecules.

| Task | v1 (before) | v2 (now), split 42 | v2, 10 splits | NOSE (paper) | verdict |
|---|---:|---:|---:|---:|---|
| Intensity (Ravia) | 0.02 | 0.45 | **0.54** (0.21) | 0.49 (0.03) | above |
| Intensity (Keller) | 0.66 | 0.66 | **0.57** (0.14) | 0.42 (0.01) | above |
| Descriptor strength (Keller) | 0.41 | 0.41 | **0.42** (0.07) | 0.35 (0.06) | above |
| Threshold (Abraham) | 0.80 | 0.77 | **0.79** (0.04) | 0.84 (0.03) | **short by 0.05** |
| Pleasantness (Keller) | 0.41 | 0.54 | **0.67** (0.07) | 0.71 (0.05) | **short by 0.04** |

The threshold shortfall is about 1.3 of our split-to-split standard deviations; the pleasantness shortfall is about 0.5. The paper's deviations are instead across model seeds on a fixed split. Those different quantities and the different targets cannot support a statistical-equivalence claim.

Full tables, per-seed values and the run manifest: `runs/nose-protocol-v4/` (`REPORT.md`, `results.json`). Structural-CV results for the same model: `runs/modular-pipeline-fingerprint-v5/`.

## Evidence about the remaining 0.04–0.05

**The usable datasets are smaller.** Reserved exclusions reduce Abraham 268 → 186 and Keller 474 → 326. Ravia additionally differs from the paper's source processing/count: its usable public table is smaller than the paper's 248 molecules before reserved exclusions leave 114. Actual training splits are 111, 260 and 91 molecules against the paper's 160, 379 and 198.

**The oracle measurement for pleasantness:** substituting the *measured* Keller descriptor profile for the model's predicted one lifts inner-CV pleasantness from 0.71 to **0.90**. Better quality predictions could help. This measurement does not distinguish insufficient training data from limitations of the quality learner.

**For threshold the previously tested additions did not close the gap.** The failure list below records those tests, without ruling out new evidence or learners.

Opening the reserved holdouts would enlarge the datasets but would not guarantee parity. **The user decided on 2026-10-01 to keep them closed**, on the grounds that clean final tests are worth more than the benchmark row. Do not reverse that decision without asking. Independently sourced, filtered training data remains an allowed improvement route.

## What produced the gains (v2 heads)

All member sets were chosen by **repeated 5-fold inner CV on the split-42 training portion only**. Test molecules were never used for selection. Keep that discipline for any further changes.

- **Pleasantness 0.56 → 0.67:** a separate hedonic head (`HEDONIC_MEMBERS`, two extra-trees members on RDKit descriptors + explicit blocks + stage-A quality logits and direction, dilution as a column) replaces the profile combiner's pleasantness output. The combiner still produces the descriptor profile.
- **Ravia 0.36 → 0.54:** the Hill dose–response stage cannot fit single-concentration data at all. Three gradient-boosted members plus a Uni-Mol2 extra-trees member (`RAVIA_MEMBERS`) replace it.
- **Threshold:** `THRESHOLD_MEMBERS` averages the v1 fusion+ridge ensemble with descriptor/fingerprint trees, a fingerprint ridge and a frozen Uni-Mol2 ridge. Net effect over ten splits is +0.01.
- **Keller intensity and descriptors** keep the v1 dose–response and combiner stages, which already lead the paper.

Machinery: `TabularEnsemble` in `src/calnew/pipeline/stages.py`. Tree kinds ending in `+aux` also train on flagged auxiliary rows and always predict with the flag at 0.

## Things that were tried and did not work

Do not spend time on these again without a new reason.

| Idea | Result |
|---|---|
| **MolFormer embeddings** (frozen, all tasks) | Nothing anywhere. Inner CV 0.72 with and without, on threshold. |
| **Averaging more stage-A seeds** | Actively worse: 5 seeds 0.689 vs 1 seed 0.706 on pleasantness. |
| **Li et al. 2025 water thresholds as auxiliary rows** | +0.01 inner CV at most. Test score moved 0.78 → 0.77 on split 42, unchanged at 0.79 over ten splits. Kept anyway: cleanly licensed evidence, honestly reported. |
| **Extra Ravia dilution rows** (other concentrations of training molecules) | 0.573 vs 0.570 inner CV. Noise. |
| **Uni-Mol2 as fusion anchor** | No measurable effect (earlier finding, `runs/modular-pipeline-unimol2-v2`). Only useful as a ridge/extra-trees *member*. |
| **Validation-split ensemble weights** (the last untried lever, measured 2026-10-01) | **Worse than equal weights.** Simulated at the paper's val:train ratio inside the training portion: threshold 0.712 fitted vs 0.732 equal; pleasantness 0.706 vs 0.713; Ravia 0.569 vs 0.583. Half-shrunk weights also lose. 11–37 validation molecules are too few to fit weights on. Equal weighting stays. |

## Auxiliary data (training only, not in the repo)

Li et al. 2025 median water ODTs, [Zenodo 10.5281/zenodo.17559514](https://zenodo.org/records/17559514), CC BY 4.0. `src/calnew/pipeline/auxiliary.py` pins the sha256 and prints the download URL if the file is missing:

```bash
mkdir -p data/raw/li_2025/zenodo-17559514-v1
curl -L -o data/raw/li_2025/zenodo-17559514-v1/threshold_data_med.csv \
  'https://zenodo.org/records/17559514/files/threshold_data_med.csv?download=1'
```

716 of 992 rows carry a numeric threshold; 567 survive the reserved-holdout exclusion; each fit additionally drops rows of its own validation and test molecules. Registered in `configs/sources.json` as `li_2025` with `adapter: auxiliary_only` — it is deliberately **not** ingested into the evidence store, because it is never an evaluation target.

## How to reproduce

```bash
.venv/bin/python -m calnew pipeline paper-benchmark --out runs/my-benchmark \
  --robustness-splits 43 44 45 46 47 48 49 50 51      # ~23 min, Mac CPU
```

```bash
.venv/bin/python -m calnew pipeline train --out runs/my-run                # ~24 min with v2 heads
```

Note that `runs/` and `data/raw/` are git-ignored, so the numbers live in `docs/PIPELINE.md`, not in the repository as data. If those directories are lost, the benchmark has to be re-run to recover them.

## Compute setup

- **Current intensity checkout:** `C:\calnew`, using `C:\calnew-compute\.venv\Scripts\python.exe` and the `scripts/ssh_compute.py` wrapper. The user requires training, evaluation, inference and tests on SSH only. All current intensity jobs finished; models/results are synced locally. Keep this restriction for further compute unless the user changes it. The full suite passed here, including the historically failing Windows olfactometer test.
- **compute-host** (`ssh compute-host`, Tailscale) is the heavy-compute box: RTX 3060 Laptop 6 GB, 12-thread i5. A working copy lives at `C:\calnew-compute` with its own venv; sync with `tar czf - src | ssh compute-host 'tar xzf - -C C:\calnew-compute'`. Its CPU is roughly 5× slower per benchmark step than the Mac, so for CPU work the Mac is faster; compute-host is useful for running jobs in parallel.
- Long jobs must be launched detached (`wmic process call create "cmd /c ...\run.cmd"`) or they hang the SSH session.

## Open threads

1. Original train-only threshold and pleasantness reference-score gaps remain open; the parity goal is active. Exact NOSE reproduction additionally needs shared processed targets/splits and matching evaluation procedures. The latest evidence and every identified technique are recorded in the new report and ledger linked above.
2. If the user later explicitly authorizes using reserved molecules for training, this would consume their value as clean final tests. It would not guarantee the paper's scores.
3. Better-quality training data would help more than any model change — specifically a descriptor vocabulary with marine/ozonic terms (Good Scents, Arctander), which the current Leffingwell label set lacks entirely. This is also why Calone is predicted as sweet/hay rather than marine.
4. `docs/PIPELINE.md` is the canonical write-up; this file is only the handoff.
