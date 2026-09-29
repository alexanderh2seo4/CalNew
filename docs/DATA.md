# Evidence and reproducibility

## Frozen initial snapshot

`data/snapshots/955c3ab05ff9fb7d` contains the source tables used in the basic comparisons:

| Source | Resolved molecular examples | Imported observations | Interpretation |
|---|---:|---:|---|
| Leffingwell | 3,522 | 397,986 | 113 source-specific descriptor columns |
| Abraham 2012 processed table | 268 | 268 | Log airborne detection thresholds; 57 upstream aggregates |

There are 3,622 distinct molecular identities across both sources, reflecting overlap. The snapshot has 398,254 observations. These are not 398,254 independent molecular examples. Quality-audit counts are in `data/quality-audit.json`.

Pyrfume is pinned to commit `8054ea98ed675005ec10e67359902f500e4911b0`. Each downloaded file has a URL, size and SHA-256 hash in its `download.json`; ingestion checks these hashes. The raw Abraham spreadsheet and upstream processing code are retained to support reconstruction of original measurements. No upstream Python acquisition scripts are executed as part of ingestion.

The initial source register is `configs/sources.json`. It distinguishes immediately supported adapters from acquisition targets and sources needing licence/access review. GoodScents is excluded from ingestion until its permissions are resolved. Keller files have been acquired for the next participant/context stage; they are not part of the frozen initial snapshot or basic-model scores.

## Model lineage

| Encoder | Checkpoint/release used |
|---|---|
| Native graph | CALNEW source archived with each final basic run |
| Chemprop | Installed release 2.3.1 |
| MoLFormer | `ibm-research/MoLFormer-XL-both-10pct`, revision `361063d0ad524ef77cf39b08469f6be770dc550f` |
| Uni-Mol2 | `dptech/Uni-Mol2`, revision `bf37d253c0f5ac61f468137eb00059978a104ff0`, `modelzoo/84M/checkpoint.pt` |

Uni-Mol2 checkpoint hashes are recorded under its feature cache. MoLFormer code and weights are fetched at the immutable revision; the two remote Python model files were inspected before execution. Feature-cache records state whether the representation is deterministic or frozen pretrained. Learned imputers, scalers, heads and graph encoders are fitted within folds.

Only load locally trusted `model.joblib` files: Python model serialisation is executable and is not a safe interchange format for arbitrary external files. JSON/Parquet records are the evidence interchange.

## Reviewed literature/patent records

Use `calnew discover 'query' --out data/search.json` for Europe PMC discovery and `calnew retrieve PMC12345` for available full text. A retrieval does not itself establish licence permission or an accepted measurement.

`import-reviewed` accepts JSONL bundles with `smiles`, `evidence`, `stimulus` and `observation`. The strict models in `schema.py` define the required fields. Molecular IDs, source IDs and foreign keys must agree; evidence must be accepted and carry documented permitted use. Predicted/calculated records remain distinct and are excluded from the measured basic task loader.

Before import, resolve whether a repeated publication refers to the same original experiment. Preserve conflicting independent results. The audit flags duplicated original-experiment keys but does not silently decide that two different observations are independent or average them away.

The current parser handles JATS text/tables/figures as located text. Full PDF table reconstruction, MolScribe structure resolution, EPO credentialed retrieval, Markush handling and automatic patent-family deduplication remain future integration work. The register listing a source does not imply that its observations have already entered training.

## Tests and runtime caveats

The offline test suite covers unit conversion, matrix separation, stereo grouping, censored likelihoods and gradients, panel bounds, extraction gates, split separation, organiser lineage, conformal grouping, model persistence, unsupported prediction endpoints, conformer caching, acquisition protection, contextual models and a complete synthetic nested benchmark. Synthetic fixtures never enter the public evidence store.

The local NumPy 2.2.6/BLAS combination emits floating-point status warnings for some finite matrix multiplications. The Tanimoto implementation was checked against a non-BLAS boolean oracle, and model outputs are checked for finiteness. Warnings are retained in run logs rather than hidden. A separate runtime comparison on the target compute cluster should verify numerical agreement before the expanded study; a passing finite-value check is not proof that every numerical operation is unaffected.

The final holdout remains reserved. Computational pilot results, calibration fitting and future prospective measurements are separate evidence categories throughout the reports.
