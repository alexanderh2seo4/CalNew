# Calculated Olfr73 ligand pharmacophore reconstruction

This complete local calculation reproduces the **type of pharmacophore experiment**, not the unavailable original Phase/CoMFA/receptor workflow. It uses the mouse eugenol receptor Olfr73 and published measured ligands. No coordinates in the molecular figures were hand placed. Every atom position, feature center, fit score and overlay comes from the supplied calculation.

Open **viewer.html** directly in a WebGL-capable browser for offline use, or visit the local server:

<http://127.0.0.1:8766/viewer.html>

The viewer displays the top five held-out candidates, donor/acceptor/hydrophobic/aromatic spheres, individual calculated molecules, all rankings including failed assay compounds, downloads and evaluation plots. Drag to rotate, scroll to zoom. The browser renders included calculated data; it does not recalculate molecules.

## Reproduce the calculation

The Mac's existing `Support/.venv` has all dependencies. From the CalNew workspace:

```sh
Support/.venv/bin/python Support/research_notes/olfactory_pharmacophore_2026-10-09/local_model/run_model.py
Support/.venv/bin/python -m http.server 8766 --bind 127.0.0.1 --directory Support/research_notes/olfactory_pharmacophore_2026-10-09/local_model
```

For an isolated environment on another computer, run these from this folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_model.py
.venv/bin/python -m http.server 8766 --bind 127.0.0.1
```

RDKit, NumPy, SciPy, Matplotlib and 3Dmol.js are free software. Recalculation is offline and deterministic within the recorded library/platform environment. The optional `audit_structures.py` performs online PubChem named resolution and writes cached responses; it is not needed to run the model. Its raw first-pass cache includes some unresolved or overloaded requests; the final `structure_audit.json` incorporates subsequent named alias resolutions.

## Data and provenance

The authoritative assay data are Yuan et al. (2019), *Computational modeling of the olfactory receptor Olfr73 suggests a molecular basis for low potency of olfactory receptor-activating compounds*, Communications Biology, DOI [10.1038/s42003-019-0384-8](https://www.nature.com/articles/s42003-019-0384-8).

- `sources/MOESM2.pdf`: original supplementary information downloaded directly from Springer Nature; Table 2 supplies A1–A25 names, EC50 values for A1–A17 and eight explicit “no active response” compounds (A18–A25). Table 3 supplies B1–B25 previously known agonist names.
- `ligands.tsv`: chemical graph transcriptions from those names and their labels/assays. The source table's “cydohexyl” and “terbutyl” spelling is normalized. No B EC50 values were guessed from figures. Reported uncertainty after ± is transcribed without assuming its statistical meaning.
- `structure_audit.json` and `sources/pubchem/`: 45/50 chemical graphs match independently named PubChem records. B25, A2, A11, A12 and A13 remain explicit manual name transcriptions. B25's two bridgehead CIP labels are verified R/S; A17's source-specified rose oxide stereo is verified R/R. A11's source does not specify E/Z; both stereoisomers are calculated and the best geometric fit is retained, an optimistic bound.
- `outputs/run_manifest.json`: source/script/feature-definition hashes, platform, exact versions, settings, converged conformer counts and rigid optimizer diagnostics.
- `sources/source_manifest.json`: download URLs and SHA-256 hashes for downloaded sources and vendored renderer.

The downloaded M2OR CSV was inspected, but contains no records under this study's DOI; it is not used as assay or structure input here.

## Method

1. RDKit enumerates unspecified stereochemistry, generates up to 48 ETKDGv3 conformers per stereoisomer with a fixed seed and 0.25 Å RMS pruning, and relaxes them with MMFF94s. Only converged structures within 6 kcal/mol of each stereoisomer's lowest MMFF energy are retained. Absolute MMFF energies from different molecules are never used as a ranking.
2. The lowest-energy conformer of B3, source-specified E-isoeugenol, seeds a common reference frame. RDKit MMFF O3A rigidly aligns each B training conformer. The best O3A alignment per training molecule defines its feature contribution.
3. Standard RDKit `BaseFeatures.fdef` supplies donor, acceptor, aromatic and hydrophobic features. Lumped hydrophobic features replace redundant contained single-atom hydrophobes. B3's calculated features seed consensus sites; five iterations of family-wise one-to-one matching within 1.8 Å calculate their training mean coordinates. Sites supported by at least 40% of the 25 B ligands are retained.
4. Each site's support is the number of **distinct training molecules**, not the number of conformers. RMS spatial dispersion is calculated. Gaussian tolerance σ = max(0.75 Å, 1.5 × RMS dispersion). The floor, cutoff and multiplier are explicit model settings, not original paper constants or physical electron cloud sizes.
5. Each retained A conformer first receives O3A alignment, then bounded 6D rigid L-BFGS-B refinement against the consensus. This changes only translation/rotation, preserving the calculated MMFF internal geometry. One-to-one same-family assignments maximize support-weighted Gaussian fit. The score is the sum of assigned support-weighted `exp(-distance²/(2σ²))` divided by the sum of all model-site supports. Missing sites contribute zero. There is no compulsory donor requirement, no clash/exclusion-volume penalty and no potency regression.
6. The best fit across conformers/stereoisomers determines the displayed alignment and score. No A activity label or EC50 is used in construction, alignment, selection or score parameters. All A assays are used only after calculation for retrospective evaluation.

Consensus coordinates and radii are exported without display adjustments. The viewer's consensus spheres have radius σ. Individual ligand feature markers have a **0.45 Å display-only radius** centered at calculated feature positions. Molecules without donor features receive no donor markers. The static publication figure uses shared physical coordinate scales and orthographic projection so spheres retain their geometric meaning.

Input names are interpreted as their neutral chemical forms; no assay-pH protonation or tautomer ensemble is inferred. Aromatic and hydrophobic feature roles can share a ring center, so those score terms are correlated. The six sites are chemically typed geometric constraints, not six independently validated receptor interactions. Rigid optimization reached its convergence criterion for every one of the 328 retained conformers (300-iteration cap); numerical convergence does not establish a global optimum or a correct biological binding pose.

This run generated **378 conformers** and retained **328 converged low-energy conformers**. Six consensus sites survived: one donor, two acceptors, one aromatic site and two hydrophobic sites. The donor is supported by 13/25 training molecules (52%); it is a support-weighted site rather than a universal obligatory feature.

## Results and limits

The held-out 25-compound panel has 17 published positives and eight explicit nonresponses. The top five geometric fits are A4, A5, A8, A11 and A12; all five are experimentally active in the source. Eight of the top ten are active, with the nonresponses A19 and A20 ranked highly. This is evidence of both usable resemblance matching and the inability of a ligand-only pharmacophore to establish activation.

Retrospective ROC AUC is **0.691**. Pairwise AUC gives a tied positive/negative score half credit. A deterministic 5,000-replicate stratified percentile bootstrap gives a broad **95% interval approximately 0.471–0.890**. This interval samples the same biased panel and does not account for model-choice or dataset-selection uncertainty.

Among the 17 active compounds, feature fit has only a weak association with measured pEC50 (Spearman ρ approximately 0.228, p approximately 0.379). The scoring model is **not a potency predictor**. The original paper's 17/25 success rate belongs to its complete homology/MD/PH4/QSAR/docking/experimental workflow, not to this reconstruction.

All 25 A candidates were previously selected by the original multistage virtual screen. This is a small retrospective, preselected holdout, not a random library or prospective validation. Feature overlap does not prove receptor engagement or activation. Scores are not activation probabilities, odor labels or human smell predictions. A ligand pharmacophore may miss a valid nonaromatic class, as seen for the low-ranked active A6 and A17. It may assign high scores to a known nonhit, as seen for A19 and A20.

The original Olfr73 receptor model, Phase pharmacophore file, CoMFA model and original exact aligned conformer set were not publicly obtained. This reconstruction performs **no receptor homology modelling, receptor docking, molecular dynamics, exclusion-volume search, electrostatic potential or quantum electron-density calculation**. Displayed spheres are chemically defined interaction features/tolerances. A modern structure-based reproduction would be a different calculation.

## Exported results

- `outputs/results.json` / `results.js`: full calculated coordinates, bonds, chemical features, scores, source labels and settings.
- `outputs/aligned_ranked.sdf`: all 50 selected aligned conformers with hydrogens, score and assay metadata.
- `outputs/ranked_candidates.csv`: full ranking, experimental EC50 values, source split and selected conformer/MMFF metadata.
- `outputs/pharmacophore.json`: training consensus coordinates, tolerance radii, measured dispersion, support counts and contributing training IDs.
- `outputs/pharmacophore_panel.png`: publication-style computed molecular/feature figure.
- `outputs/holdout_validation.png`: ROC, full positive/negative scores and weak potency association.
- `outputs_calculation.log`: actual execution output.

The browser viewer, scientific PNGs, JSON coordinates and SDF files all use the same calculated coordinate frame.
