# CALNEW

A runnable research system for comparing molecular odour models. The initial implementation predicts **catalogue descriptor annotations** and **airborne detection thresholds** as separate tasks. It trains actual models on public observations, saves calibrated prediction artifacts, and reserves the final holdout.

**Current stage: basic models and computational pilots.** This is not yet a prospectively validated human odour system. Water thresholds, participant-specific predictions, receptor transfer and molecule generation are not trained endpoints in the supplied artifacts.

Verification: **44 automated tests passed** (21 original + 23 pipeline), dependency checks passed, saved prediction artifacts were exercised, and both final holdouts remain unopened. See [artifact verification](docs/verification.json).

## Start here

- [Modular quality → potency → combiner pipeline](docs/PIPELINE.md) (example model; `calnew pipeline train/predict`, plus the NOSE paper benchmark)
- [Basic-model results and interpretation](docs/BASIC-MODELS.md)
- [Architecture and implementation status](docs/ARCHITECTURE.md)
- [Improvements with substantial computing capacity](docs/IMPROVEMENTS.md)
- [Evidence acquisition and reproducibility](docs/DATA.md)
- [Original project canvas](CALNEW.canvas) and [olfactometer notes](Olfactometer-Build.md)

## Run the installed system

Run commands from this directory. The local `.venv` is already installed.

```bash
.venv/bin/python -m calnew doctor
.venv/bin/python -m pytest -q

.venv/bin/python -m calnew predict \
  --run runs/basic-threshold-models \
  --smiles 'CCO' 'CC(=O)c1ccccc1' \
  --out data/example-threshold-predictions.json

.venv/bin/python -m calnew predict \
  --run runs/basic-descriptor-models \
  --smiles 'CCO' 'CC(=O)c1ccccc1' \
  --out data/example-descriptor-predictions.json
```

Predictions report the endpoint, training semantics, selected model, expert outputs, model disagreement, training similarity and data/model versions. Threshold intervals target 90% coverage under the calibration assumptions. Unsupported endpoints and invalid structures return `unavailable` with a reason. A catalogue probability means the source would record that descriptor; it is not automatically a human-panel endorsement probability.

## Reproduce the basic comparisons

```bash
.venv/bin/python -m calnew benchmark \
  --snapshot data/snapshots/955c3ab05ff9fb7d \
  --endpoint catalogue_descriptor --source leffingwell \
  --config configs/pilot.yaml --out runs/my-descriptor-pilot

.venv/bin/python -m calnew benchmark \
  --snapshot data/snapshots/955c3ab05ff9fb7d \
  --endpoint air_detection_threshold --source abraham_2012 \
  --config configs/four-family-pilot.yaml --out runs/my-threshold-pilot
```

Use a new output directory when changing source code, data or configuration. A run contains its manifest, split, selected configurations, nested-fold predictions, fitted models, calibration object and report. Current runs also archive the Python source used to execute them.

`configs/pilot.yaml` compares descriptors, fingerprints, XGBoost and a native stereochemistry-aware directed graph network. `configs/four-family-pilot.yaml` adds Chemprop, the Tanimoto Gaussian process, frozen MoLFormer and frozen Uni-Mol2. The 3D branch uses up to 16 optimised diverse conformers from 32 initial conformers; it appends an explicit chirality-aware fingerprint.

## Fresh installation

Python 3.12 was used for the completed runs. Core dependencies are in `pyproject.toml`; exact local versions are in `requirements-lock.txt`.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[models,pretrained,dev]'
.venv/bin/python -m calnew doctor
```

The lock file includes an editable local-project entry: install the project from this directory when recreating the environment. Hardware-specific packages may need platform-specific wheels. On this Mac, the XGBoost wheel needed its OpenMP search path repaired; `scripts/fix_macos_xgboost.py` reproduces the local environment repair when the sklearn runtime exists. The current environment exposes CPU only.

## Data commands

```bash
.venv/bin/python -m calnew sources
.venv/bin/python -m calnew fetch leffingwell
.venv/bin/python -m calnew ingest leffingwell
.venv/bin/python -m calnew fetch abraham_2012
.venv/bin/python -m calnew ingest abraham_2012
.venv/bin/python -m calnew snapshot
.venv/bin/python -m calnew quality-audit data/snapshots/955c3ab05ff9fb7d
```

Acquisition is explicit. The source register records rights separately from accessibility; unverified sources cannot be ingested through the public-data adapter. Raw downloads retain checksums and original values. Research-only inputs do not acquire commercial permission by being processed.

The final test set is not used in the supplied pilot reports. `audit-holdout` refuses pilot runs. A subsequent preregistered full comparison can use `configs/full.yaml`, but that configuration currently expands only implemented model routes—it does not implement every future experiment described in the research plan.
