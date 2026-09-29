# How to improve the basic models with ample computing capacity

The next priority is to determine **why** the basic models fail, then spend compute on experiments that can distinguish competing explanations. The present results do not justify making the system larger everywhere.

These are proposed research experiments. Unless a route is marked implemented in [ARCHITECTURE.md](ARCHITECTURE.md), it requires additional code before a configuration can run it.

## 1. Complete the comparison before redesigning the model

Preserve the current descriptor regression and averaged descriptor predictor as controls. Run the expanded development protocol, retaining the unopened final holdout:

- Five outer folds and three inner folds, with structural and fingerprint-cluster evaluations.
- Fifty distinct initial hyperparameter configurations per main family where the search space supports them.
- Five seeds for every selected configuration **within each outer fold**, not only final refits. The current runner averages seeds only for the final fitted artifact; extend it before claiming a multi-seed architecture-selection result.
- Separate grouped-random results for literature comparison. Do not replace structural results with the easier score.
- Extend the search only when training curves and configuration sensitivity indicate unresolved optimisation. Predeclare the extra allowance and avoid opening the final test set after every change.

With many accelerators, distribute independent configurations/folds/seeds as separate jobs. Each job needs the immutable dataset ID, split ID, code hash, checkpoint revision, seed and output location. Share only deterministic feature caches. Fold-learned representations, source corrections and ligand templates must remain isolated.

The present `full.yaml` is a starting configuration for the implemented routes. It is not a scheduler, a multi-node training system, or evidence that the full experiment has run.

## 2. Optimise the basic representations

### Fingerprints and descriptors

Test fingerprints alone, descriptors alone and their combination at Morgan radii 2 and 3. Compare linear/logistic, RF, XGBoost and GP results using matched folds. For thresholds, add an intercept-only control and group-nearest-neighbour prediction so gains over simple priors are visible.

Expand GP comparisons to uncertainty-aware kernel combinations and robust observation noise. Keep training-set-only preprocessing. Test measured transport features separately from predictions available for a new molecule; giving the benchmark measured properties that will be unavailable at deployment creates an unfair comparison.

### Graph models

The initial native graph and Chemprop models were trained from scratch for 15 epochs. Their weak pilot performance is a reason to inspect learning curves and data efficiency, not a reason to discard graphs.

Test depths 3/5/7, widths 256/512/1024, dropout 0/0.1/0.3 and learning-rate schedules. Add physical descriptors after molecular pooling. Compare a purely shared encoder with endpoint-specific upper layers. Use the published [Chemprop implementation](https://github.com/chemprop/chemprop) as a separately identified candidate, and reproduce [OpenPOM](https://github.com/BioMachineLearning/openpom) in an isolated compatible environment.

The highest-value transfer experiment is broad odour-descriptor training followed by threshold adaptation. Every broad-odour training stage must exclude the outer validation, calibration and test molecules for a strict label-clean evaluation—even when their threshold labels are absent from pretraining.

### Chemical language

For [the pinned MoLFormer checkpoint](https://huggingface.co/ibm-research/MoLFormer-XL-both-10pct), compare:

1. Frozen encoder with regularised linear heads: already implemented.
2. Frozen encoder with a small nonlinear head.
3. Upper-layer adaptation or low-rank adapters.
4. Full fine-tuning, with the smallest learning rates applied to lower layers.

Inspect the tokenizer's handling of stereochemistry, charged species and unusual atoms. Test equivalent SMILES strings and stereochemical pairs separately. If a representation is insensitive to an important distinction, do not assume that larger endpoint heads will recover information it discarded.

Large unlabelled chemical pretraining can improve representation coverage. It does not create evidence for human odour descriptors or thresholds. Record unlabelled-structure exposure separately from sensory-label exposure.

## 3. Test what 3D information actually contributes

The implemented [Uni-Mol2](https://github.com/deepmodeling/Uni-Mol) route uses an 84M checkpoint and mean conformer pooling with appended chirality-aware fingerprints. Compare a controlled ladder:

| Experiment | Question it answers |
|---|---|
| Fingerprint head alone | How much of the combined result comes from the 2D stereo features? |
| Single 3D conformer, no appended fingerprint | Is the 3D embedding useful independently? |
| Mean of diverse conformers | Does conformational coverage improve generalisation? |
| Learned conformer attention | Can the model learn useful conformer weighting without overfitting? |
| Frozen versus adapted encoder | Is the general chemistry representation aligned with odour tasks? |
| 84M versus 164M versus larger released configurations | Does scaling improve the endpoint after adequate tuning? |

For attention, let the endpoint head attend over a variable number of conformers with an explicit validity mask. Compare learned weights with uniform weights; force-field energies are auxiliary inputs, not automatically the receptor-bound conformer distribution.

Use additional compute for conformer-search convergence experiments, not merely a larger fixed conformer count. Compare 16/32/64/128 generated conformers on a chemically diverse subset; track retained diversity, optimisation failures and score stability. Then choose the smallest configuration whose results have stabilised.

Check invariance under translation and proper rotation. Check whether a reflection is distinguished when stereochemistry is specified. Then test **correctness** on measured enantiomer pairs: merely producing different predictions for two enantiomers proves neither correct recognition nor correct human perception.

An independent 3D challenger such as [DeepNose](https://arxiv.org/abs/2412.08747) is useful only when compared on the same molecules and folds. Architectural diversity is more informative than many copies of one model making the same errors.

## 4. Strengthen threshold modelling before adding a large shared head

Threshold prediction currently has only 268 processed records, some already averaged upstream. Reconstruct original observations, study methods and censoring before treating them as interchangeable exact targets.

A proposed observation model is:

`observed log threshold = molecular effect + study/method effect + panel effect + residual`

Use a robust likelihood, retain bounds, and shrink source effects. Overlap among studies is required to separate source differences from chemical differences. The included `ThresholdObservationModel` implements a small study-level version over cross-fitted predictions; extending it to crossed methods and participant effects requires a richer design matrix and identifiability checks.

Do not force threshold and descriptor tasks to share every parameter. Compare separate encoders, shared lower layers and a shared encoder with separate upper layers. If descriptor pretraining helps but joint training hurts, a sequential transfer route may be better than adding loss-weighting complexity.

Retain threshold ranking as a derived task with its own evaluation. Do not count comparisons generated from one measured threshold table as new independent evidence. Suprathreshold intensity comparisons need a separate concentration-conditioned model.

## 5. Add physical and biological branches one at a time

### Transport properties

Prioritise vapour pressure, partitioning, solubility and flexibility because they connect molecular properties to delivered stimulus. Obtain provenance-aware data from [NIST](https://webbook.nist.gov/) and the [Henry's-law database](https://www.henrys-law.org/henry/download.html). Maintain each Henry convention explicitly.

Train or validate property predictors separately, then compare:

- A structure-only sensory predictor.
- Structure plus measured physical properties, as an upper-information research comparison.
- Structure plus predicted properties, reflecting a new-molecule workflow.
- Predictions with propagated property uncertainty.

Quantum calculations can add electrostatic potential, dipole-related and conformational descriptors. Their acceptance criterion is held-out sensory improvement beyond the cheaper descriptors; they must not be converted into artificial sensory labels.

### Pharmacophores

Start with generic donor/acceptor/hydrophobic/aromatic/charged spatial features. Compare these against the existing 2D pharmacophore fingerprints. Build target-specific templates only from training-fold experimental ligands. Test receptor-specific shape/feature alignment where the receptor evidence supports it; a universal “marine pharmacophore” should remain a hypothesis until validated.

### Receptors

Acquire and audit [M2OR](https://doi.org/10.1093/nar/gkad886), then reproduce [LORAX](https://github.com/depasquale-lab/lorax) before substantially enlarging the receptor network. Keep species, construct, cell system, concentration and assay context. Untested receptor–molecule pairs are missing observations, not negatives.

Compare direct perception prediction, receptor-task pretraining, optional predicted receptor profiles and joint receptor/perception learning. Retain the direct molecular path in every integrated model. Report held-out ligand, receptor and human-only results separately.

Only keep the receptor branch in the human predictor if it improves human endpoint performance and calibration. A scientifically useful receptor model can still be an unhelpful sensory feature generator.

## 6. Improve the organiser only after measuring complementary errors

The descriptor pilot favours simple averaging; threshold stacking does not beat the descriptor regression. Start by plotting per-molecule residual correlations and errors by chemical family. A larger gate is justified when experts have predictable, complementary strengths.

Then add expert uncertainty, training-domain similarity and protocol context to the gate. Learn endpoint-specific weights. Use missing-branch training and evaluate real branch failures before calling the system robust to missing 3D input.

Separate uncertainty quantities. Ensemble disagreement is a model diagnostic; it is not automatically measurement noise or participant variability. Evaluate probability calibration, interval coverage/width and risk-versus-coverage curves on held-out molecules. Recalibration needs its own partition. Reserve any neural gate's tuning for development folds.

## 7. Spend compute on finding better evidence

Extend the source programme beyond the initial catalogue and threshold compilation: Pyrfume collections, participant-level Keller data, primary threshold studies, aqueous-threshold data, concentration curves, receptor data, papers and patents.

A useful extraction system preserves document locations, chemical example identifiers, structure images, matrix, units, methods and original experiment lineage. Add structure recognition and patent-family resolution, then evaluate them on manually verified examples. Parallel extraction can increase throughput; it cannot replace the acceptance audit.

The first new human study should sample diverse chemistry, not a preselected Calone scaffold. Use the proposed 24-compound pilot to estimate repeatability and variance, then determine the larger study size. Keep descriptor/intensity and threshold endpoints separate and preserve raw responses.

After validation, compare the implemented mixed acquisition policy with random and diversity-only controls. Its initial allocation is 40% reducible uncertainty, 30% coverage, 20% discriminating analogues and 10% repeated anchors. Unreliable identity or delivery triggers curation rather than an acquisition-score reward.

## Promotion rule

Accept a modification only when it improves the declared endpoint on paired structural evaluations, remains consistent on independent sources, and does not materially worsen calibration. Use the simplest candidate within the predeclared uncertainty band. Reserve the final holdout for the frozen decision, then validate with genuinely new measurements.

Unlimited computing capacity is most valuable here for **better controlled comparisons, wider pretraining, uncertainty estimates and targeted evidence acquisition**. It does not make a component useful merely because the component is expensive.
