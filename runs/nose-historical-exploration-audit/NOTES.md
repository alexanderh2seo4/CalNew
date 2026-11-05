# Historical exploration recovery, 2026-10-02

Numerical recovery ran on `compute-host` through the SSH checkout wrapper. It recomputed metrics from existing prediction arrays; it did not fit models, replay old experiments or score reserved final rows. `summary.json` contains exact metrics and source hashes. `historical-input.tar.gz` preserves all selected sources and serialized research data. The server also holds the expanded `source-archives/` tree.

The scratch directory mapping is:

- S1: `1a20ddec-767a-4104-a71b-a01c6eead7ad/scratchpad/`
- S2: `2d34f5d3-d15d-4675-9fe1-59553eb3adc8/scratchpad/`
- S3: `5da5f4aa-ece6-464d-973c-7fa31560ce6c/scratchpad/`

All had the common original prefix `/path/to/historical-workspace/`.

## Recovered precursor selection scores

These are means over three five-fold prediction arrays on original split-42 training rows: Abraham 111, Keller pleasantness 260, Ravia 91. Target values and inferred training IDs agree exactly between the S1 and S3 context snapshots. They are historical exploratory scores, with the provenance and nesting limitations below.

| Historical candidate | Mean Pearson |
|---|---:|
| Abraham pipeline B1 | 0.659680083881299 |
| Abraham XGBoost RDKit/explicit/fingerprint | 0.700389492428367 |
| Abraham extra-trees RDKit/explicit/fingerprint | 0.698770199731618 |
| Abraham fingerprint ridge | 0.632979079213712 |
| Abraham equal average of these four | 0.717555260871746 |
| Abraham Uni-Mol2 ridge alone | 0.663636951633605 |
| Abraham four-member average plus Uni-Mol2 ridge | 0.735901034678555 |
| Keller pleasantness extra-trees RDKit/explicit/quality/direction | 0.706446175299702 |
| Keller pleasantness extra-trees RDKit/explicit/fingerprint | 0.689762281071011 |
| Keller pleasantness equal average of these two | 0.714167338602201 |
| Ravia pipeline B2 (Hill, fixed coordinate) | 0.347496940861945 |
| Ravia three XGBoost members | 0.569199973435813 |
| Ravia Uni-Mol2 extra-trees alone | 0.585128646627038 |
| Ravia three-member average plus Uni-Mol2 extra-trees | 0.585633542830917 |

The full audit preserves all individual ridge, SVR, MinMax count-fingerprint kernel, boosted-tree, extra-trees and Uni-Mol2 variants and their three repeat metrics. These values do not replace later fully nested, connectivity-grouped selection results.

## Recovered water training variants

The source `S2/li_joint.py` uses a medium indicator and excludes the main held molecules and each inner validation connectivity from Li source rows. The baseline equal ensemble includes B1, two air-only trees, fingerprint ridge and Uni-Mol2 ridge (0.735901034678555).

| Li water weight | Replace the two air-only tree members | Add both joint tree members |
|---|---:|---:|
| 1.0 | 0.754024999504009 | 0.748650154069156 |
| 0.5 | 0.750102760383760 | 0.745800846514182 |
| 0.25 | 0.745616909621906 | 0.743015531667298 |

The retained `S2/li_aux_train_oof.npy` water proxy correlates 0.376850285210840 with Abraham training targets. This is a transfer-feature diagnostic, not a downstream head's cross-validation score. The audit also reads the full saved proxy array but scores only the corresponding Abraham training rows.

## Evidence limits and missing results

The OOF pickles contain target values and named prediction matrices but no molecule IDs, fold membership, source hashes or execution manifest. Row correspondence is inferred from the matching context targets and retained code; correct executed fold alignment remains unverified. Source specifies ordinary KFold seeds 100, 101, 102 rather than connectivity-grouped folds. Stage-A features were computed once before downstream inner validation, so those features are not fully nested. Current controlled experiments use stronger selection evidence.

The pretrained OOF archives contain Uni-Mol2 members and **no MolFormer members**. The retained source supports a MolFormer experiment and writes to the same pretrained artifact naming pattern, but its reported scores cannot be recovered from the surviving arrays. Whether an earlier artifact was overwritten is unverified.

`stageA_keller_seeds.pkl` contains five sets of quality/direction/embedding feature arrays; its first set matches the context exactly. No final seed-averaging OOF predictions are saved, so the reported five-seed score and measured-profile oracle ceiling cannot be verified without fitting.

`val_weights.py` contains the NNLS and half-shrunk weighting procedure but saves neither fitted weights nor score results. This audit did not replay or fit those weights. Its reported comparisons remain narrative evidence only.

Water proxy-augmented heads, the S3 pooled-water variants, random tree searches, Keller/Ravia-to-threshold transfer, extra Ravia concentration rows and pleasantness stimulus-row variants have retained source but no corresponding final OOF results identified. Do not assign recovered numerical values to them.
