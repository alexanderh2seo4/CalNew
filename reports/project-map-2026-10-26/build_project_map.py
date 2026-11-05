"""Build a documentation canvas from saved artifacts; never imports model code."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REPORT = ROOT / "CALNEW Project Architecture and Performance.md"
CANVAS = ROOT / "CALNEW Detailed Project Map.canvas"


def read_json(relative):
    return json.loads((ROOT / relative).read_text())


def digest(relative):
    path = ROOT / relative
    return {"path": relative, "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    metrics = read_json("runs/modular-pipeline-fingerprint-v5/metrics.json")
    run = read_json("runs/modular-pipeline-fingerprint-v5/run.json")
    audit = read_json("runs/nose-parity-current-audit-20261002.json")
    descriptors = read_json("runs/nose-descriptor-selected-intensity-audit-v3/results.json")
    verification = read_json("runs/nose-descriptor-selected-intensity-audit-v3/verification.json")
    gate = read_json("runs/nose-threshold-disjoint-semantic-direction-inner-v1/gate-summary.json")
    ph4 = read_json("research_notes/olfactory_pharmacophore_2026-10-09/local_model/outputs/results.json")
    source_paths = [
        "README.md", "docs/ARCHITECTURE.md", "docs/DATA.md",
        "docs/BASIC-MODELS.md", "docs/PIPELINE.md", "docs/CONTINUATION.md",
        "docs/NOSE-PARITY-AND-METHODS-REPORT.md", "docs/INTENSITY-IMPROVEMENT.md",
        "runs/modular-pipeline-fingerprint-v5/metrics.json",
        "runs/modular-pipeline-fingerprint-v5/run.json",
        "runs/modular-pipeline-fingerprint-v5/REPORT.md",
        "runs/nose-parity-current-audit-20261002.json",
        "runs/nose-descriptor-selected-intensity-audit-v3/results.json",
        "runs/nose-descriptor-selected-intensity-audit-v3/verification.json",
        "runs/nose-threshold-disjoint-semantic-direction-inner-v1/gate-summary.json",
        "runs/basic-threshold-models/REPORT.md",
        "runs/basic-descriptor-models/REPORT.md",
        "src/calnew/pipeline/run.py", "src/calnew/pipeline/blocks.py",
        "src/calnew/pipeline/fusion.py", "src/calnew/pipeline/stages.py",
        "src/calnew/pipeline/semantic.py", "src/calnew/pipeline/intensity.py",
        "src/calnew/pipeline/dose_transfer.py", "src/calnew/pipeline/joint_intensity.py",
        "Auto doser/OVERVIEW.md", "Auto doser/Doser-4-Line-Wiring.md",
        "research_notes/olfactory_pharmacophore_2026-10-09/local_model/README.md",
        "research_notes/olfactory_pharmacophore_2026-10-09/local_model/outputs/results.json",
        "research_notes/olfactory_pharmacophore_2026-10-09/local_model/outputs/run_manifest.json",
    ]
    evidence = {
        "compiled": "2026-11-05",
        "method": "Read and format saved local artifacts; no new model computation or final-test target access.",
        "structural_cv": {"run": "modular-pipeline-fingerprint-v5", "manifest": run, "metrics": metrics},
        "repeated_development": {
            protocol: {task: {k: row[k] for k in ["metrics", "source", "retained_evidence",
                                                  "predictions_verified", "original_test_ids_and_targets_verified"]
                              if k in row}
                       for task, row in audit[protocol].items()}
            for protocol in ["original_train_only", "validation_refit"]
        },
        "development_connectivity_overlaps": audit["development_connectivity_overlaps"],
        "latest_paired_descriptors": descriptors["summary"],
        "descriptor_verification": {k: v for k, v in verification.items() if k != "cases"},
        "threshold_training_only_candidate": gate,
        "pharmacophore": {"training_n": ph4["training_n"], "metrics": ph4["metrics"]},
        "sources": [digest(p) for p in source_paths],
    }
    (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")

    nodes, edges = [], []

    def group(id_, label, x, y, width, height):
        nodes.append(dict(id=id_, type="group", label=label, x=x, y=y, width=width, height=height))

    def node(id_, text, x, y, width=620, height=320, color=None):
        value = dict(id=id_, type="text", text=text, x=x, y=y, width=width, height=height)
        if color:
            value["color"] = color
        nodes.append(value)

    def edge(a, b, label=None, from_side="bottom", to_side="top", color=None, arrow=True):
        value = dict(id=f"edge-{len(edges):03d}", fromNode=a, toNode=b,
                     fromSide=from_side, toSide=to_side, fromEnd="none", toEnd="arrow" if arrow else "none")
        if label:
            value["label"] = label
        if color:
            value["color"] = color
        edges.append(value)

    def mean(task, protocol="original_train_only"):
        return audit[protocol][task]["metrics"]["pearson"]["mean"]

    group("group-data", "1 · EVIDENCE AND PROTECTED DATA", 0, 0, 630, 1830)
    group("group-chemistry", "2 · MOLECULAR INPUT AND QUALITY", 760, 0, 720, 1830)
    group("group-models", "3 · MODULAR HEADS, METRICS AND SERVING", 1620, 0, 2080, 2600)
    group("group-validity", "4 · EVALUATION BOUNDARIES", 3860, 0, 700, 2600)
    group("group-basic", "5 · SEPARATE BASIC BENCHMARK ROUTE", 0, 2000, 1480, 1600)
    group("group-lab", "6 · CANDIDATES AND PROPOSED LABORATORY LOOP", 1620, 2750, 2940, 1600)
    group("group-ph4", "7 · SEPARATE Olfr73 PHARMACOPHORE", 0, 3750, 1480, 1500)
    group("group-index", "8 · NEXT GATES AND SOURCE INDEX", 1620, 4500, 2940, 750)

    node("title", "# CALNEW — detailed project map\n\nMolecular odour models, their saved performance, and the planned laboratory feedback loop.\n\n**Start with the companion report:** [[CALNEW Project Architecture and Performance]]\n\nCompiled 26 October 2026. Sensory results: saved 1–2 October; receptor prototype: 9 October; doser overview: 22 October. No model evaluation or final-test target access was performed for this map.", 0, -650, 3700, 350)
    node("legend", "## Reading this map\n\n**Uncoloured:** implemented model/data path.\n\n**Cyan:** saved numerical evidence.\n\n**Orange:** planned, unvalidated or awaiting evaluation.\n\n**Purple:** evaluation boundary.\n\nArrows labelled **planned** describe future work. Metrics are side branches from models, not inputs to inference.\n\nSource notes open through the links in each node.", 3860, -650, 700, 350)

    node("sources", "## Public observations and associations\n\n- Leffingwell catalogue descriptors\n- Abraham airborne thresholds\n- Keller intensity, profile and pleasantness\n- Ravia highest-presentation intensity\n- Flagged training-only water/descriptor auxiliaries\n\nSources have different semantics and are not one interchangeable target.\n\n[[docs/DATA|Data and provenance]]", 40, 120, 550, 320)
    node("curation", "## Identity, context and evidence review\n\nIsomeric SMILES, connectivity, material, endpoint, medium, units, censoring, original experiment and permitted-use provenance.\n\nAir and water thresholds stay separate. Predicted records stay distinct from measurements.\n\n[[src/calnew/schema.py|schema.py]] · [[src/calnew/chemistry.py|chemistry.py]] · [[src/calnew/units.py|units.py]]", 40, 530, 550, 320)
    node("store", "## SQLite → immutable Parquet\n\nForeign keys and immutable evidence IDs; content-addressed snapshots.\n\nInitial snapshot: 3,622 molecular identities and 398,254 observations. Observation count is not independent molecule count.\n\n[[src/calnew/store.py|store.py]] · [[docs/DATA|Snapshot lineage]]", 40, 940, 550, 290)
    node("split", "## Protected chemistry and development folds\n\n**Basic:** ~70/15/15 development/calibration/final test; nested structural folds.\n\n**Modular:** 709 molecules excluded for earlier tests; another 273 pipeline-test molecules reserved. Five global structural development folds.\n\n**Nested A features:** outer test excludes k; training fold j excludes both k and j.\n\n[[src/calnew/splits.py|splits.py]] · [[runs/modular-pipeline-fingerprint-v5/run.json|Saved manifest]]", 40, 1320, 550, 380, "6")

    node("smiles", "## Molecular input\n\nCanonical isomeric SMILES. Stereo variants retain identity, with shared connectivity kept together by the structural split route.\n\nOptional Keller input: nominal solution dilution in paraffin oil.\n\n[[src/calnew/chemistry.py|Identity implementation]]", 800, 120, 640, 240)
    node("blocks", "## Explicit molecular blocks\n\n- Transport: MW, logP, TPSA, flexibility, rings\n- Hydrogen bonding: typed donors/acceptors, VSA\n- Osmophores: 35 SMARTS functional-group counts\n- Chain/shape: length, branching, topology, stereo\n- Generic 2D pharmacophore: 1,024 folded counts\n- Chiral Morgan r2 + MACCS fingerprints\n- Full RDKit descriptors for tabular members\n- Optional frozen Uni-Mol2 conformer embedding\n\n[[src/calnew/pipeline/blocks.py|blocks.py]]", 800, 450, 640, 420)
    node("fusion", "## Task-specific NOSE-lite fusion\n\nTrain-only imputation/scaling → separate two-layer projections → project non-anchor blocks off the fingerprint anchor → softmax-weighted sum and LayerNorm. Soft pairwise overlap penalty.\n\nSeparate networks are fitted per task; this is not one shared trained encoder or a complete NOSE reproduction.\n\n[[src/calnew/pipeline/fusion.py|fusion.py]]", 800, 970, 640, 300)
    qa = metrics["quality"]["pipeline_stage_A"]
    node("quality", f"## Stage A · quality\n\nPositive-weighted masked BCE, two-seed fusion ensemble.\n\n91 catalogue labels and a second head for Keller descriptor direction.\n\n**Structural CV:** macro AP **{qa['macro_average_precision']:.4f}**, AUROC **{qa['macro_auroc']:.4f}**. Logistic baseline AP 0.2318 / AUROC 0.8056.\n\nCatalogue scores are uncalibrated association rankings.\n\n[[src/calnew/pipeline/stages.py|QualityStage]]", 800, 1370, 640, 330)

    node("threshold", "## B1 · airborne threshold\n\nFusion Gaussian head + grouped ridge ablations + extra-trees/XGBoost and frozen-embedding members.\n\nServed v2 ensemble predicts **log10 ppbv** and ppbv. Lower threshold means greater potency.\n\nThis branch does not calibrate the Keller dilution axis.\n\n[[src/calnew/pipeline/stages.py|ThresholdStage / tabular members]]", 1660, 120, 620, 340)
    node("keller", "## B2 · Keller concentration response\n\nBaseline: fusion predicts Hill Imax, x50 and positive slope.\n\n**Selected head:** 0.5 Hill + 0.5 monotone semantic dose trees.\n\nInput dose is nominal paraffin-oil solution dilution, not measured vapour concentration. Selected head is enabled with `--intensity-run`.\n\n[[src/calnew/pipeline/intensity.py|Intensity recipes]]", 2350, 120, 620, 340)
    node("pleasant", "## Separate pleasantness head\n\n0.5 legacy hedonic tree ensemble + 0.5 structure/descriptor-transfer trees. Includes dilution.\n\nReplaces the older C pleasantness output when selected with `--semantic-run`.\n\nImproved pleasantness is not inferred from a floral/fruity label alone.\n\n[[src/calnew/pipeline/semantic.py|Semantic head]]", 3040, 120, 620, 340)

    tm = metrics["threshold"]
    node("threshold-score", f"## Threshold · keep protocols separate\n\n**5-fold structural CV, 186 rows:**\n- Fusion pooled MAE **{tm['fusion']['mae']:.4f}** log10 ppbv\n- Served v2 pooled MAE **{tm['v2']['mae']:.4f}**\n- Served v2 Spearman **{tm['v2']['spearman']:.4f}**\n\n**10 development assignments:**\n- Original training r **{mean('threshold_abraham'):.6f}**\n- Separate validation-refit r **{mean('threshold_abraham', 'validation_refit'):.6f}**\n\n[[runs/modular-pipeline-fingerprint-v5/metrics.json|Structural metrics]] · [[runs/nose-parity-current-audit-20261002.json|Development audit]]", 1660, 580, 620, 340, "5")
    node("keller-score", f"## Keller intensity · saved performance\n\n**10 development assignments, selected head:**\n- Original-training r **{mean('intensity_keller'):.6f}**\n- MAE **10.519**, RMSE **13.854**\n- Separate refit r **{mean('intensity_keller', 'validation_refit'):.6f}**\n\nPaired original baseline r 0.569402.\n\n**Different protocol:** structural-CV baseline Hill r 0.6067 / RMSE 18.241.\n\n[[docs/INTENSITY-IMPROVEMENT|Paired results and selection]]", 2350, 580, 620, 340, "5")
    node("pleasant-score", f"## Pleasantness · saved performance\n\n**10 development assignments:**\n- Original-training r **{mean('pleasantness_keller'):.6f}**\n- Original MAE **7.622**\n- Separate validation-refit r **{mean('pleasantness_keller', 'validation_refit'):.6f}**\n\n**Different protocol:** baseline structural-CV v2 hedonic r 0.4985.\n\nOriginal-protocol reference-score gap remains open.\n\n[[docs/NOSE-PARITY-AND-METHODS-REPORT|Methods and limits]]", 3040, 580, 620, 340, "5")
    node("semantic", "## Auxiliary semantic transfer\n\n7,000 molecules; 1,098,957 descriptor associations. Generic MiniLM word vectors define descriptor-derived targets; molecular models predict 128-dimensional transfer features.\n\nHeld connectivities are excluded from source fits. Training meta-features use additional cross-fitting.\n\nResearch associations are not measured human sensory responses.\n\n[[src/calnew/pipeline/semantic.py|Transfer implementation]]", 1660, 1050, 620, 330)
    node("combiner", "## C · descriptor-profile combiner\n\nQuality direction + predicted intensity + dilution → 20 descriptor strengths.\n\nA learned magnitude scales the quality direction with a regularised residual. Training uses measured intensity; oracle/predicted evaluation exposes propagated intensity error.\n\nThe selected Keller input enters before C prediction.\n\n[[src/calnew/pipeline/stages.py|Combiner implementation]]", 2350, 1050, 620, 330)
    node("ravia", "## Separate Ravia intensity endpoint\n\n**Selected blend:**\n- 0.25 legacy Ravia ensemble\n- 0.25 ridge on cross-fitted Keller proxies\n- 0.50 shared Keller/Ravia trees\n\nHighest-presentation endpoint; no arbitrary dilution input. Keller proxy doses −5, −3, −1 are latent source features.\n\n[[src/calnew/pipeline/dose_transfer.py|Proxies]] · [[src/calnew/pipeline/joint_intensity.py|Shared-study trees]]", 3040, 1050, 620, 330)
    cand = gate["candidates"][gate["selected"]]
    node("threshold-candidate", f"## Threshold continuation · not serving-ready\n\nDirection/confidence blend passed original-training-only selection:\n\nPearson **{gate['candidates']['current']['mean_pearson']:.6f} → {cand['mean_pearson']:.6f}**\nMAE **{gate['candidates']['current']['mean_mae']:.6f} → {cand['mean_mae']:.6f}**\nPositive Pearson gain in 3/3 repeats.\n\nFrozen ten-split benchmark remains pending. This is not a new held-development score.\n\n[[runs/nose-threshold-disjoint-semantic-direction-inner-v1/gate-summary.json|Selection gate]]", 1660, 1490, 620, 300, "2")
    ds = descriptors["summary"]
    node("profile-score", f"## Descriptor profile · paired evaluation\n\n**10 original assignments, fixed C:**\nMacro r **{ds['original']['old_intensity']['pearson_macro']['mean']:.6f} → {ds['original']['selected_intensity']['pearson_macro']['mean']:.6f}** with selected intensity.\nMAE **{ds['original']['selected_intensity']['mae']['mean']:.3f}**. All 20 original/refit cases verified.\n\n**Different protocol:** structural CV r 0.3247 with measured intensity; 0.2655 with predicted baseline intensity.\n\n[[runs/nose-descriptor-selected-intensity-audit-v3/results.json|Paired results]]", 2350, 1490, 620, 300, "5")
    node("ravia-score", f"## Ravia intensity · saved performance\n\n**10 development assignments:**\n- Original-training r **{mean('intensity_ravia'):.6f}**\n- Original MAE **11.748**\n- Separate validation-refit r **{mean('intensity_ravia', 'validation_refit'):.6f}**\n\nOne training/test connectivity overlap in seed 48; auxiliary source exclusions remain enforced.\n\n[[runs/nose-intensity-ravia-joint-v2/results.json|Original results]]", 3040, 1490, 620, 300, "5")
    node("outputs", "## Structured outputs and optional head selection\n\n**Pipeline JSON:** catalogue rankings; air threshold; approximate interval; dose response; intensity, descriptor profile and pleasantness at the requested dilution; nearest-training similarity; provenance. Ravia has a separate intensity API.\n\n`pipeline predict --run runs/modular-pipeline-fingerprint-v5` uses that bundle's baseline heads.\n`--intensity-run runs/nose-intensity-keller-refit-v3` enables selected Keller intensity before C.\n`--semantic-run runs/nose-semantic-pleasantness-v3` enables improved pleasantness.\nRecommended Ravia bundle: `runs/nose-intensity-ravia-joint-refit-v2`.\n\n**Mixtures:** analytic primacy/vector rule only; no mixture validation observations. No automatic formula generation or formula-to-doser integration.\n\n[[src/calnew/pipeline/run.py|Serving implementation]]", 1660, 1930, 2000, 430)

    node("final-tests", "## Final tests stay reserved\n\nBasic threshold: 40 rows.\nBasic descriptors: 528 molecules.\nAdditional pipeline test: 273 molecules / 42 structural groups.\n\nEarlier holdout exclusions apply across stages. The inspected modular manifest records `pipeline_test_accessed: false`.\n\nDevelopment-test scores are not scores on these final tests.\n\n[[runs/modular-pipeline-fingerprint-v5/run.json|Reservation manifest]]", 3900, 120, 620, 350, "6")
    node("protocols", "## Three evaluation protocols\n\n1. Basic nested structural CV, with separate calibration.\n2. Modular 5-fold structural CV, using nested A features.\n3. Ten retained development assignments; original training and separate train+validation refit.\n\nDo not mix them into one leaderboard. Labels, cohorts and target processing also differ. Correlation is not percentage accuracy.\n\n[[CALNEW Project Architecture and Performance#5. Model performance, kept separate by protocol|Performance tables]]", 3900, 580, 620, 350, "6")
    node("overlap", "## Known connectivity overlap\n\nRetained development assignments include primary training/test connectivity overlap:\n\n- Abraham seeds **42, 44, 46, 50, 51**\n- Ravia seed **48**\n- Keller: none in the saved audit\n\nPaired assignments were preserved. Their scores do not establish fully connectivity-disjoint performance.\n\n[[runs/nose-parity-current-audit-20261002.json|Saved overlap audit]]", 3900, 1050, 620, 350, "6")
    node("uncertainty", f"## Uncertainty is endpoint-specific\n\nBasic regression: reserved-calibration group conformal. Basic classification: temperature scaling. Independent final coverage remains unmeasured.\n\nModular fusion's nominal Gaussian 90% interval covers only **{100*tm['fusion']['coverage_of_1.645sd']:.1f}%** in structural CV. Serving uses approximate OOF residual quantiles instead.\n\nSelected Keller blend uncertainty is unestimated. Similarity is an applicability diagnostic.\n\n[[src/calnew/calibration.py|Calibration]]", 3900, 1520, 620, 350, "6")
    node("parity", "## Claims and verification boundary\n\nReference-score parity is incomplete; exact shared-data reproduction is unestablished. Different targets/splits prevent equivalence claims.\n\n71 passing SSH tests are documented for earlier intensity integration. They were not rerun for this map. Later audits verify specific saved predictions and IDs.\n\nNumerical model work remains SSH-only in the saved continuation instructions.\n\n[[docs/NOSE-PARITY-AND-METHODS-REPORT|Current methods report]]", 3900, 1990, 620, 350, "6")

    node("experts", "## Basic expert families\n\nRDKit linear/logistic; Morgan RF/XGBoost; Tanimoto GP; native CALNEW D-MPNN; published Chemprop; frozen MoLFormer; frozen Uni-Mol2 conformer mean plus chirality.\n\nThese are separately compared model families, not all branches of the modular fusion net.\n\nOpenPOM adapter is unavailable locally; no completed receptor-assisted sensory route.\n\n[[docs/ARCHITECTURE|Implemented expert scope]]", 40, 2140, 650, 370)
    node("organiser", "## Nested expert/organiser selection\n\nOuter structural folds evaluate generalisation. Inner folds choose expert settings and generate organiser-training predictions. Refit experts on outer training before scoring outer validation.\n\nCompare equal averaging, regularised stacking and a small gate. Select the simplest declared model within one standard error.\n\n[[src/calnew/benchmark.py|benchmark.py]] · [[src/calnew/ensemble.py|ensemble.py]]", 790, 2140, 650, 370)
    node("basic-scores", "## Basic pilot winners\n\n**Threshold:** RDKit regularised linear.\nOuter-fold MAE **0.9403 ± 0.0523 SE** log10 ppbv; 188 development rows.\n\n**Descriptors:** equal average.\nOuter-fold macro AP **0.2548 ± 0.0184 SE**; 2,466 development molecules / 90 labels. Pooled OOF AP is **0.2176**.\n\n[[docs/BASIC-MODELS|Complete model comparisons]]", 40, 2640, 650, 290, "5")
    node("calibration", "## Calibrate on reserved calibration data\n\nThreshold: group-conformal residual quantile.\nDescriptors: regularised temperature.\n\nCalibration groups are separate from model selection and the untouched final test.\n\n40 threshold calibration rows; 528 descriptor calibration molecules.\n\n[[src/calnew/calibration.py|calibration.py]]", 790, 2640, 650, 290)
    node("basic-output", "## Saved basic predictors\n\nEndpoint-specific estimates, expert predictions/disagreement, provenance, nearest-training similarity and calibration information. Invalid inputs or unsupported endpoints return unavailable with a reason.\n\nThese are the calibrated basic artifacts; modular Stage-A rankings and residual intervals have different semantics. A catalogue association is not a panel endorsement probability.\n\n[[src/calnew/predict.py|predict.py]] · [[README|Commands and installation]]", 40, 3070, 1400, 340)

    node("priorities", "## Screening and measurement priorities\n\nCombine model uncertainty, diversity, analogue comparisons and anchors. Preserve protected evaluation groups.\n\nExisting candidate-screening outputs demonstrate prioritisation, not new experimental validation or a validated probability of a potent derivative.\n\n[[src/calnew/active.py|active.py]] · [[results/canvas-candidates-2026-09-24/REPORT|Candidate report]]", 1660, 2890, 620, 300)
    node("materials", "## Material acquisition and chemistry\n\nPurchase defined references or synthesise matched analogues; verify chemical identity, stereochemistry and purity.\n\nA planned experimental route. The model does not implement a validated molecule or perfume-formula generator.\n\n[[CALNEW|Original research canvas]]", 2350, 2890, 620, 300, "2")
    node("doser", "## Gravimetric ingredient doser · design\n\nPump/buffer → bottle-specific normally-closed 3/2 air valves → dedicated FEP lines → fixed four-line nozzle. Balance feedback over RS232 to ESP32.\n\n**±20 mg is a target, not a measured result.**\n\nParts, wiring/tubing, cap/septum analysis and Blender concepts exist.\n\n[[Auto doser/OVERVIEW|Doser overview]]", 3040, 2890, 620, 300, "2")
    node("olfactometer", "## Sponsored olfactometer · secured\n\nA sponsored instrument has been secured for CALNEW. Use it for controlled odour presentation and prospective panel measurements.\n\nRecord instrument settings, delivered concentration, protocol and assessor responses with each measurement.\n\n[[docs/ARCHITECTURE#Experimental measurements|Experimental measurement context]]", 3730, 2890, 790, 300, "2")
    node("lab-separation", "## Two instruments, two different functions\n\nThe doser measures **ingredient mass into a vial**. The olfactometer controls **odour presentation in air**. They are not an implemented continuous automatic chain.\n\nThe Keller solution-dilution model does not establish the delivered airborne dose. Prospective measurements must retain material, protocol, concentration and assessor context.\n\n[[Auto doser/OVERVIEW|System status]] · [[docs/ARCHITECTURE|Observation model]]", 1660, 3340, 1310, 320)
    node("doser-pending", "## Doser work still pending\n\nFirmware; wireless control implementation; dosing-validation log.\n\nWi-Fi/Bluetooth control is a specification. Formula-to-doser execution is future work.\n\nAccuracy depends on balance feedback and after-drip control, not valve timing alone.\n\n[[Auto doser/Doser-4-Line-Wiring|Bring-up plan]]", 3040, 3340, 620, 320, "2")
    node("panel", "## New panel observations · planned\n\nRecord each assessor's responses, delivered concentration and stimulus context.\n\nExisting panel code handles response bounds and censored BET estimates; software does not certify physical delivery or sensory validity.\n\nProspective thresholds, profiles, intensity, liking and recovery measurements would test the model.\n\n[[src/calnew/panel.py|Panel utilities]]", 3730, 3340, 790, 320, "2")
    node("new-evidence", "## Proposed feedback to the evidence store\n\nReview new measurements with lineage, units, medium, material identity and experiment IDs. Feed accepted independent observations into a new snapshot and a preregistered evaluation.\n\nNo prospective end-to-end validation series was identified in the inspected artifacts.\n\n[[src/calnew/review.py|Review gates]]", 2350, 3820, 900, 320, "2")

    node("ph4-train", "## Receptor-specific training ligands\n\n25 published B-series agonists of mouse Olfr73.\n\nThis is a separate ligand-geometry calculation, not a trained human olfactory-receptor network.\n\n[[research_notes/olfactory_pharmacophore_2026-10-09/local_model/README|Prototype method]]", 40, 3900, 650, 300)
    node("ph4-model", "## Calculated six-site consensus\n\nETKDGv3 conformers → MMFF94s relaxation/filtering → O3A rigid alignment → support-weighted feature consensus.\n\n1 donor, 2 acceptors, 1 aromatic and 2 hydrophobic sites. 378 conformers generated; 328 retained.\n\n[[research_notes/olfactory_pharmacophore_2026-10-09/local_model/outputs/pharmacophore.json|Consensus coordinates]]", 790, 3900, 650, 300)
    node("ph4-held", "## Retrospective A-series panel\n\n25 previously preselected compounds: 17 published active responses and 8 nonresponses.\n\nActivity/EC50 labels are used after model construction for evaluation. This is not a prospective random-library test.\n\n[[research_notes/olfactory_pharmacophore_2026-10-09/local_model/README|Source and selection limits]]", 40, 4320, 650, 300)
    node("ph4-fit", "## Held-ligand fit and viewer\n\nConformer alignment + bounded rigid refinement; best one-to-one same-family fit.\n\nOffline 3D viewer, calculated feature spheres, ranked CSV/SDF and scientific plots.\n\nNo docking, MD, quantum electron density or receptor-to-human model integration.\n\n[[research_notes/olfactory_pharmacophore_2026-10-09/local_model/viewer.html|Offline viewer]]", 790, 4320, 650, 300)
    pm = ph4["metrics"]
    node("ph4-score", f"## Pharmacophore performance and boundary\n\nRetrospective ROC AUC **{pm['ROC_AUC']:.4f}**; 95% bootstrap interval **{pm['ROC_AUC_stratified_bootstrap95_percentile_CI'][0]:.4f}–{pm['ROC_AUC_stratified_bootstrap95_percentile_CI'][1]:.4f}**. Top 5: 5 actives; top 10: 8 actives.\n\nActive-only fit versus pEC50: Spearman **{pm['positive_only_score_vs_pEC50_Spearman_rho']:.4f}**, p **{pm['positive_only_score_vs_pEC50_Spearman_p']:.4f}**. It is not a potency predictor.\n\nSeparate from the generic **2D pharmacophore block** used by the sensory pipeline; no validated human odour predictions follow from this receptor fit.\n\n[[research_notes/olfactory_pharmacophore_2026-10-09/local_model/outputs/results.json|Computed results]]", 40, 4740, 1400, 360, "5")

    node("next-gates", "## Remaining research gates\n\n1. Run the frozen threshold candidate on all unchanged development assignments; report original/refit protocols separately.\n2. Resolve remaining threshold/pleasantness reference-score gaps without treating altered targets as a reproduction.\n3. Preserve reserved final tests until an explicitly approved final evaluation.\n4. Implement/validate physical rigs and acquire prospective panel measurements.\n\nMixture learning, participant-specific predictions, receptor-to-human transfer, validated water prediction and molecule/formula generation remain unvalidated or unimplemented.\n\n[[docs/NOSE-PARITY-AND-METHODS-REPORT|Current completion gates]]", 1660, 4640, 1390, 440, "2")
    node("index", "## Source and artifact index\n\n**Detailed diagrams and complete performance tables:**\n[[CALNEW Project Architecture and Performance]]\n\n**Architecture/code:** [[docs/ARCHITECTURE]] · [[docs/PIPELINE]]\n**Initial models:** [[docs/BASIC-MODELS]]\n**Latest evidence:** [[docs/NOSE-PARITY-AND-METHODS-REPORT]]\n**Intensity refinements:** [[docs/INTENSITY-IMPROVEMENT]]\n**Hardware:** [[Auto doser/OVERVIEW]]\n\nExact extracted metrics and source hashes:\n[[reports/project-map-2026-10-26/evidence.json]]\n\nReporting only: saved artifacts were inspected; no model training, inference or tests were run locally.", 3150, 4640, 1370, 440)

    for a, b in [("sources", "curation"), ("curation", "store"), ("store", "split"),
                 ("smiles", "blocks"), ("blocks", "fusion"), ("fusion", "quality")]:
        edge(a, b)
    edge("split", "quality", "training targets / nested folds", "right", "left")
    edge("split", "experts", "separate basic route")
    for target in ["threshold", "keller"]:
        edge("fusion", target, "task-specific fusion", "right", "left")
        edge("quality", target, "quality meta-features", "right", "bottom")
    for target in ["pleasant", "ravia"]:
        edge("blocks", target, "tabular structure features", "right", "top")
    edge("quality", "pleasant", "quality / direction", "right", "left")
    edge("quality", "combiner", "quality direction", "right", "left")
    edge("keller", "combiner", "predicted intensity; selected head optional", "right", "top")
    edge("semantic", "keller", "semantic features", "top", "bottom")
    edge("semantic", "pleasant", "semantic features", "top", "bottom")
    for a, b in [("threshold", "threshold-score"), ("keller", "keller-score"),
                 ("pleasant", "pleasant-score"), ("combiner", "profile-score"), ("ravia", "ravia-score")]:
        edge(a, b, "saved evaluation", arrow=False)
    edge("threshold", "threshold-candidate", "separate training-only continuation", "left", "left", "2")
    for source in ["threshold", "combiner", "pleasant", "ravia"]:
        edge(source, "outputs", "prediction" if source != "ravia" else "separate intensity API", "right", "right")
    edge("outputs", "priorities", "research screening")
    edge("experts", "organiser", "expert predictions", "right", "left")
    edge("organiser", "calibration", "selected predictor")
    edge("organiser", "basic-scores", "outer-fold evaluation", "left", "top", arrow=False)
    edge("calibration", "basic-output", "calibrated serving", "bottom", "right")
    edge("basic-output", "priorities", "basic endpoint screening", "right", "left")
    for a, b, label in [("priorities", "materials", "planned acquisition / synthesis"),
                        ("materials", "doser", "planned mass preparation"),
                        ("materials", "olfactometer", "planned defined test material")]:
        edge(a, b, label, "right", "left", "2")
    edge("doser", "doser-pending", "implementation / validation pending", color="2", arrow=False)
    edge("olfactometer", "panel", "planned measured presentation", color="2")
    edge("panel", "new-evidence", "planned reviewed observations", "bottom", "right", "2")
    edge("new-evidence", "curation", "planned prospective feedback", "left", "left", "2")
    edge("ph4-train", "ph4-model", "training ligands", "right", "left")
    edge("ph4-model", "ph4-fit", "consensus")
    edge("ph4-held", "ph4-fit", "held-out structures", "right", "left")
    edge("ph4-fit", "ph4-score", "retrospective evaluation")

    canvas = {"nodes": nodes, "edges": edges}
    CANVAS.write_text(json.dumps(canvas, indent=2, ensure_ascii=False) + "\n")
    diagrams = re.findall(r"```mermaid\s*\n(.*?)\n```", REPORT.read_text(), re.S)
    for i, diagram in enumerate(diagrams, 1):
        (OUT / f"diagram-{i:02d}.mmd").write_text(diagram + "\n")
    print(json.dumps({"canvas": str(CANVAS), "text_nodes": sum(n["type"] == "text" for n in nodes),
                      "groups": sum(n["type"] == "group" for n in nodes), "edges": len(edges),
                      "mermaid_diagrams": len(diagrams), "hashed_sources": len(source_paths)}))


if __name__ == "__main__":
    main()
