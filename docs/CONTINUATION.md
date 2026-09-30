# Continuation report — NOSE parity work

Status as of **2026-10-01**, branch `modular-pipeline`, commit `383094e` (pushed). Working tree clean, 44 tests pass, no jobs running on the Mac or on alex-pc.

This report exists so the next session does not repeat work that has already been done and measured. The short version: **three of the five NOSE benchmark tasks now beat the paper, two remain about one split-to-split standard deviation short, and the remaining gap is training-set size, not architecture.** Every modelling lever I could find has been tried and measured; the results are below, including the ones that failed.

## Where the numbers stand

Test-set Pearson under the NOSE protocol (`arXiv:2604.10452`). The column to trust is the ten-split mean: single-split test sets hold only 11–38 molecules.

| Task | v1 (before) | v2 (now), split 42 | v2, 10 splits | NOSE (paper) | verdict |
|---|---:|---:|---:|---:|---|
| Intensity (Ravia) | 0.02 | 0.45 | **0.54** (0.21) | 0.49 (0.03) | above |
| Intensity (Keller) | 0.66 | 0.66 | **0.57** (0.14) | 0.42 (0.01) | above |
| Descriptor strength (Keller) | 0.41 | 0.41 | **0.42** (0.07) | 0.35 (0.06) | above |
| Threshold (Abraham) | 0.80 | 0.77 | **0.79** (0.04) | 0.84 (0.03) | **short by 0.05** |
| Pleasantness (Keller) | 0.41 | 0.54 | **0.67** (0.07) | 0.71 (0.05) | **short by 0.04** |

Both shortfalls are smaller than one split-to-split standard deviation, so they are not statistically distinguishable from the paper's values — but they are not parity either, and should not be described as such.

Full tables, per-seed values and the run manifest: `runs/nose-protocol-v4/` (`REPORT.md`, `results.json`). Structural-CV results for the same model: `runs/modular-pipeline-fingerprint-v5/`.

## Why the last 0.04–0.05 is not a modelling problem

**The holdouts remove about 30% of each dataset.** Abraham 268 → 186, Keller 474 → 326, Ravia 248 → 114. Actual training splits are 111, 260 and 91 molecules against the paper's 160, 379 and 198.

**The decisive measurement for pleasantness:** substituting the *measured* Keller descriptor profile for the model's predicted one lifts inner-CV pleasantness from 0.71 to **0.90**. The hedonic head is already close to what predicted quality supports. The binding constraint is stage A learning quality from 260 instead of 379 molecules — not the head on top of it, and not the head's hyperparameters.

**For threshold there is no equivalent lever left.** Everything tried is in the failure list below.

The only remaining way to close both gaps is to open the reserved holdouts and run the paper-sized datasets. **The user decided on 2026-10-01 to keep them closed**, on the grounds that clean final tests are worth more than the benchmark row. Do not reverse that decision without asking.

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

- **alex-pc** (`ssh alex-pc`, Tailscale) is the heavy-compute box: RTX 3060 Laptop 6 GB, 12-thread i5. A working copy lives at `C:\Users\Alex.K\calnew-compute` with its own venv; sync with `tar czf - src | ssh alex-pc 'tar xzf - -C C:\Users\Alex.K\calnew-compute'`. Its CPU is roughly 5× slower per benchmark step than the Mac, so for CPU work the Mac is faster; alex-pc is useful for running jobs in parallel.
- Long jobs must be launched detached (`wmic process call create "cmd /c ...\run.cmd"`) or they hang the SSH session.
- One unrelated test, `test_olfactometer.py::test_bet_cli_preserves_censoring`, fails on Windows only (subprocess path issue). It passes on the Mac. Not investigated.
- **The user's CrisperWhisper training on alex-pc was stopped on 2026-09-30** at their request, during epoch 3. Best checkpoint kept at `Z:\aa JAR\ems-voice-v4\runs\crisper_large_v4\20260929_fix_e08\epoch_01`. It has not been restarted.

## Open threads

1. **Nothing is blocking.** The parity goal cannot be closed further without opening the holdouts, which is a decision already made against.
2. If parity ever becomes the priority over holdout integrity, the one-line change is to run the benchmark on the full datasets; expect threshold and pleasantness to land near the paper, and expect to lose the clean final tests permanently.
3. Better-quality training data would help more than any model change — specifically a descriptor vocabulary with marine/ozonic terms (Good Scents, Arctander), which the current Leffingwell label set lacks entirely. This is also why Calone is predicted as sweet/hay rather than marine.
4. `docs/PIPELINE.md` is the canonical write-up; this file is only the handoff.
