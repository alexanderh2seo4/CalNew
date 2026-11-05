#!/usr/bin/env python3
"""Offline scope regressions and read-only audits for the Aroma Research Atlas.

    python3 pipeline/test_atlas.py
    python3 pipeline/test_atlas.py --audit-db data/atlas.sqlite

Fixtures are synthetic challenge cases, not claims of manual review of the corpus.
Audit warnings are screening leads; they do not establish false inclusion alone.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

_PIPELINE_DIR = str(Path(__file__).resolve().parent)
if _PIPELINE_DIR not in sys.path:
    sys.path.insert(0, _PIPELINE_DIR)

_SPEC = importlib.util.spec_from_file_location("aroma_atlas_pipeline", Path(__file__).with_name("atlas.py"))
atlas = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(atlas)

# name, title, abstract, expected inclusion. Cases deliberately combine positive
# keywords with a contrary central research question to catch keyword leakage.
SCOPE_CASES = [
    ("new_parent_beta_caryophyllene", "Beta-caryophyllene is a receptor agonist", "The unchanged parent activated CB2 receptors in pharmacological assays.", True),
    ("new_parent_methyl_eugenol", "Genotoxicity of eugenol methyl ether", "The unchanged parent was tested for DNA adduct formation and toxicity.", True),
    ("parent_vapor_pressure", "Vapor pressure measurements of linalool", "Temperature-dependent saturation pressures were measured using gas chromatography.", True),
    ("parent_vle_calculation", "Vapor-liquid equilibrium of d-limonene calculated by molecular simulation", "The phase equilibria and partial pressures of the unchanged parent were predicted.", True),
    ("parent_partition_measurement", "Air-water partition coefficients of geraniol and linalool", "Henry constants of the named molecules were measured at several temperatures.", True),
    ("unrelated_drug_solubility", "Solubility of caffeine in limonene solvents", "Limonene was the solvent used to measure the caffeine saturation concentration.", False),
    ("menthol_des_extraction", "Liquid-liquid equilibria of menthol-based deep eutectic solvents extracting tert-butanol", "Menthol served as a solvent component. The measured target was tert-butanol extraction.", False),
    ("parent_oxide_vapor", "Vapor pressure of linalool oxide", "Saturation pressures were measured for the oxide derivative.", False),
    ("substituted_parent_partition_library", "Prediction of partition coefficient and toxicity for benzaldehyde compounds by their capacity factors and various molecular descriptors", "Fourteen substituted benzaldehyde compounds were studied as a derivative library. The unchanged parent was not established.", False),
    ("p_cymene_metal_drug", "Anticancer activity of ruthenium p-cymene complexes", "An organometallic drug library induces apoptosis. The unchanged p-cymene parent was not administered.", False),
    ("molecular_prediction", "Predicting odor quality from molecular structure", "A graph neural network predicts fragrance descriptors for odorant molecules.", True),
    ("food_identified_volatiles", "Identification of key aroma compounds in coffee", "GC-MS and gas chromatography-olfactometry identify volatile compounds. Odor activity values were measured.", True),
    ("perfumery_intensity", "Odor intensity of perfumery raw materials", "Concentration-response curves describe perceived intensity for 314 fragrance chemicals.", True),
    ("olfactophore", "A marine olfactophore for Calone derivatives", "Pharmacophore screening predicts the odor thresholds of these marine fragrance molecules.", True),
    ("ligand_receptor", "Recognition of eugenol by an olfactory receptor", "Binding and agonist activation of the odorant eugenol were measured using concentration-response assays.", True),
    ("rifm_safety_cas", "RIFM fragrance ingredient safety assessment, methyl dihydrojasmonate, CAS Registry Number 24851-98-7", "The safety assessment includes genotoxicity, repeated dose toxicity and skin sensitization.", True),
    ("rifm_material_review", "Fragrance material review on ethyl vanillin", "CAS No. 121-32-4. A toxicological assessment of this perfumery ingredient.", True),
    ("dataset", "Pyrfume: a database of odorant-linked datasets", "The resource standardizes chemical identities, perceptual labels and odor intensity measurements.", True),
    ("ligand_pharmacology", "Sandalore activates an ectopic olfactory receptor", "The sandalwood fragrance chemical activates OR2AT4 and changes human keratinocyte proliferation.", True),
    ("odor_stereochemistry", "Stereochemistry and odor of carvone", "The enantiomers of this aroma compound have different perceived odor qualities.", True),
    ("parent_linalool_pharmacology", "Anti-inflammatory activity of linalool in macrophages", "The parent compound linalool inhibits inflammatory signaling and cytokine release.", True),
    ("parent_carvacrol_pharmacology", "Antibacterial activity of carvacrol against bacterial biofilms", "Carvacrol disrupts the bacterial membrane and reduces biofilm formation.", True),
    ("parent_eugenol_pharmacology", "Analgesic and antinociceptive effects of eugenol", "Eugenol acts on sensory ion channels and reduces pain responses in a concentration-dependent manner.", True),
    ("coumarin_drug_scaffold", "Coumarin scaffolds for kinase inhibitor discovery", "A library of synthetic coumarin hybrids was evaluated for anticancer activity and molecular docking.", False),
    ("vanillin_drug_derivatives", "Synthesis of vanillin derivatives as anticancer agents", "A drug library derived from the fragrance chemical vanillin was screened for kinase binding and cytotoxicity.", False),
    ("menthol_cigarettes", "Menthol cigarettes alter nicotine receptor activation", "Menthol exposure and cigarette smoking were studied through receptor pharmacology and nicotine dependence.", False),
    ("generic_odor_memory", "Molecular mechanisms of odor memory consolidation", "Odor stimuli alter hippocampal synapses and molecular signaling. Chemical stimuli are used to study memory rather than their aroma properties.", False),
    ("parasitoid_wasp", "Parasitic wasps exploit host odor for host location", "The wasp responds to volatile compounds and olfactory cues from its insect host.", False),
    ("honeybee_neural_learning", "Differential brain expression patterns of microRNAs related to olfactory performance in honey bees", "Apis mellifera brain microRNAs regulate olfactory learning and memory through neuroactive ligand-receptor pathways.", False),
    ("clinical_bariatric_surgery", "Does bariatric surgery change olfactory perception?", "Sniffin Sticks threshold and odor identification scores were compared before and after surgery in obese patients.", False),
    ("herbicide_olfactory_toxicity", "Metabolic activation of the herbicide dichlobenil in the olfactory mucosa of mice and rats", "Protein binding and metabolic activation of this herbicide were measured in olfactory mucosa tissue.", False),
    ("environmental_biofilters", "A pilot-scale study on biofilters for controlling animal rendering process odours", "Odorous compounds from animal tissue processing were removed by wood bark biofilters. Olfactometry measured removal efficiency.", False),
    ("taste_only_jasmine", "Effect of scenting process on the taste profile of jasmine green tea and the potent bitterness-enhancing compound in jasmine flowers", "Floral aroma motivates tea scenting. A nonvolatile quercetin glycoside was identified by LC-MS as the compound causing bitterness and astringency.", False),
    ("vanillin_structural_crosslinker", "Preparation and improved properties of vanillin-crosslinked polyvinyl alcohol/chitosan active packaging films", "Vanillin forms Schiff-base crosslinks. The resulting films have antioxidant activity and improved physical packaging properties.", False),
    ("conceptual_multisensory_design", "Olfactory attribution circle: designing crossmodal congruence between scent, color, and language", "A conceptual tool combines interviews, AI-generated maps of essences and intensity calibration in algorithmic perfumery for multisensory atmosphere design.", False),
    ("cognitive_effect_on_chemical_intensity", "Effects of cognitive factors on perceived odor intensity in adaptation processes", "Human participants rated the perceived intensity of the aroma chemical anethole delivered by an olfactometer at a controlled concentration.", True),
    ("characterized_essential_oil", "Chemical composition and antimicrobial activity of lavender essential oil", "GC-MS analysis identified linalool as a major constituent of the oil. The chemically characterized essential oil showed antibacterial activity against two bacterial strains.", True),
    ("uncharacterized_herbal_oil_trial", "Essential oil treatment for anxiety in a randomized herbal medicine trial", "Patients received an unspecified herbal preparation. Clinical anxiety scores were compared with placebo after four weeks.", False),
    ("insect_pheromone_oil_profile", "Essential oil composition and pheromone responses of insect odorant receptors", "GC-MS identified linalool among the constituents. Antimicrobial activity was measured, and moth pheromone responses were the central application.", False),
    ("packaging_essential_oil_film", "Antibacterial essential oil packaging films for food preservation", "GC-MS composition analysis identified linalool as a constituent. The oil was incorporated into packaging films and the resulting film antibacterial properties were evaluated.", False),
    ("generic_aromatic_chemistry", "Synthesis of aromatic compounds by palladium catalysis", "A molecular mechanism for carbon-carbon bond formation and aromatic ring functionalization is proposed.", False),
    ("aromatase", "Molecular docking of aromatase inhibitors", "A computational pharmacophore predicts binding of anticancer compounds.", False),
    ("ectopic_tumor_no_ligand", "An ectopic olfactory receptor drives prostate cancer progression", "We identify a receptor binding partner and study molecular signaling and tumor cell proliferation.", False),
    ("ectopic_biomarker", "Olfactory receptor expression as a biomarker of colorectal cancer", "Molecular profiling predicts survival using receptor expression and ligand binding pathways.", False),
    ("generic_pharmacology", "Pharmacophore prediction of kinase inhibitors", "Drug-like molecules bind a kinase receptor in cancer cells.", False),
    ("insect_pheromone", "Molecular recognition of sex pheromones by moth odorant receptors", "Ligand binding and olfactory receptor activation control antenna responses.", False),
    ("insect_with_human_aside", "Pheromone recognition by an insect odorant receptor", "Moth pheromone binding was measured. Human activities threaten moth populations.", False),
    ("electronic_nose_hardware", "An electronic nose for odor detection", "A chemical sensor array and neural network classify gases. Hardware sensitivity and sensor resistance were optimized.", False),
    ("enose_clinical", "Electronic nose prediction of lung cancer", "Volatile biomarkers in breath are classified by a chemical sensor array and machine learning algorithm.", False),
    ("clinical_odor_threshold", "Olfactory threshold predicts Parkinson disease progression", "Odor intensity and detection threshold tests measure clinical smell dysfunction in patients.", False),
    ("clinical_identification", "Odor identification in COVID-19 anosmia", "Chemical odor stimuli were used in an olfactory diagnostic test of patient recovery.", False),
    ("olfactory_bulb", "Molecular control of olfactory bulb development", "Neural progenitor signaling controls receptor expression and cortical migration.", False),
    ("generic_food", "Fermentation improves bread quality", "Taste and texture were measured after optimization of a fermentation model.", False),
    ("empty", "", "", False),
]


class ScopeRegressionTests(unittest.TestCase):
    def test_new_parent_identities_do_not_admit_drug_classes_or_reagents(self):
        cases = [
            ('Coumarin anticoagulants and warfarin toxicity', '', False),
            ('Toxicology of coumarin', 'The administered parent coumarin was CAS 91-64-5.', True),
            ('Vapor pressure of coumarin', '', True),
            ('Antibacterial drug assays using benzyl alcohol as solvent', '', False),
            ('Toxicology of benzyl alcohol', 'Benzyl alcohol was administered and evaluated.', True),
            ('Vapor pressure of ethyl hexanoate', '', True),
            ('Non-volatile flavor compounds causing bitterness', 'Aroma matters but aroma volatiles were not analyzed; nonvolatile taste compounds were measured.', False),
            ('Volatile and non-volatile flavor compounds in coffee', 'Volatile aroma compounds were measured by chromatography.', True),
            ('Pharmacology of methyl jasmonate', '', False),
            ('Receptor activation by Hedione', 'Methyl dihydrojasmonate was evaluated.', True),
            ('Toxicity of HHCB lactone', '', False),
            ('Flavor and fragrance volatiles by Author, Publisher, 472pp, ISBN 0-12-384250-6', '', False),
            ('Electrical responses to chemical stimulation of squid olfactory receptor cells', 'Quaternary ammonium ions, aminopyridines, squid ink and L-Dopa control escape jetting.', False),
            ('Volatile flavor compounds of squid meat', 'Aroma compounds were analyzed.', True),
            ('Molecular regulation in Odoribacter and Sporobolomyces odorus', 'Chemical cell signaling was studied.', False),
            ('Olf-1 promoter motifs regulate olfactory neuronal gene expression', 'Molecular DNA binding was measured.', False),
            ('Muscarinic antagonists in olfactory cortex slices', 'Molecular binding in neural tissue was studied.', False),
            ('Intensity and chemical profiles of swine odours', 'Volatile compounds in pig slurry were studied.', False),
            ('Identification of off-odor compounds in a lake bloom', 'Gas chromatography identified odorants in water quality monitoring.', False),
            ('Toxicity of galaxolide in aquatic organisms', 'Parent dose-response endpoints were measured.', True),
            ('Solubility of coumarin-3-carboxylate derivatives', '', False),
            ('Synthesis of benzyl alcohol as an organic intermediate', '', False),
            ('Production of benzyl alcohol as a fragrance ingredient', '', True),
            ('Vapor pressure of benzyl alcohol', '', True),
            ('Adsorption removal of galaxolide in wastewater', 'Toxicity motivates its environmental removal.', False),
            ('Antioxidant thymol blue indicator', '', False),
            ('Anticancer activity of limonene copolymers', '', False),
            ('Antioxidant 2-methoxy-carvacrol', '', False),
            ('Antimicrobial o-vanillin metal complexes', '', False),
            ('Isolation of humulene‐glucoside with antioxidant and antidiabetic activity', '', False),
            ('2-[(1H-benzimidazol-2-ylmethyl)-amino]-benzoic acid methyl ester: antibacterial activity', '', False),
            ('DFT and drug-target profiling of (R)-2-(2-(1,3-Dioxoisoindolin-2-yl)propanamido)benzoic acid methyl ester', '', False),
            ('Eucalyptol solubility on three endodontic sealants', '', False),
            ('Effect of benzyl alcohol on alkane solubility of phosphatidylcholine membranes', '', False),
            ('Pharmacology of (R)-linalool', '', True),
            ('Induction of apoptosis by γ-humulene', '', False),
            ('Coumarin (2H-1-benzopyran-2-one): a novel aphicide', '', False),
            ('Benzyl alcohol synergy with deltamethrin against Musca domestica', 'Toxicity and receptor docking in houseflies.', False),
            ('Recognition of linalool by a human olfactory receptor expressed in insect cells', 'Human odorant receptor ligand responses were measured.', True),
            ('Antibacterial bivalent metal complexes of cuminaldehyde acetoylhydrazone', '', False),
            ('Synthesis of estragole labelled with deuterium', '', False),
            ('Assay of drug receptor antagonist metabolites: simultaneous analysis of a benzyl alcohol and alkene', '', False),
            ('Benzyl alcohol-induced aggregation of recombinant human interleukin-1 receptor antagonist', 'Benzyl alcohol is an antimicrobial preservative.', False),
            ('Zeolite catalysts for benzylation of anisole with benzyl alcohol', 'Catalyst toxicity motivates optimization.', False),
            ('Synthesis and olfactory characteristics of methyl eugenol derivatives', 'Novel fragrance molecules were tested for odor properties.', True),
        ]
        for title, abstract, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(atlas.classify(title, abstract)[0], expected)

    def test_parent_production_uses_chemistry_category(self):
        result = atlas.classify('Synthesis of vanillin for a urea chemosensor', 'The synthesized vanillin was evaluated using detection thresholds.')
        self.assertTrue(result[0])
        self.assertEqual(result[1], 'Fragrance & aroma chemistry')
        self.assertEqual(result[2], ['aroma'])

    def test_new_fragrance_identity_and_historical_greek_typography(self):
        title = 'Conversion of hydroxy fatty acids into optically pure (R)-.delta.-decalactone'
        self.assertTrue(atlas.classify(title, '')[0])
        self.assertFalse(atlas.classify('Anticancer activity of epi-sclareol', '')[0])
        self.assertFalse(atlas.classify('Antimicrobial effects of sclareol glycol', '')[0])
        self.assertTrue(atlas.classify('Antioxidant activity of gamma-terpinene', '')[0])

    def test_inclusion_challenge_cases(self):
        for name, title, abstract, expected in SCOPE_CASES:
            with self.subTest(case=name):
                result = atlas.classify(title, abstract)
                self.assertEqual(bool(result[0]), expected, f"{name}: {result}")

    def test_rejected_papers_have_no_tracks(self):
        for name, title, abstract, _ in SCOPE_CASES:
            with self.subTest(case=name):
                accepted, _, tracks, _ = atlas.classify(title, abstract)
                if not accepted:
                    self.assertEqual(tracks, [])

    def test_prediction_and_aroma_tracks_are_explicit(self):
        accepted, category, tracks, reasons = atlas.classify(
            "Predicting odor quality from molecular structure",
            "A graph neural network predicts perceptual fragrance descriptors for odorant molecules.",
        )
        self.assertTrue(accepted)
        self.assertIn("aroma", tracks)
        self.assertIn("prediction", tracks)
        self.assertEqual(category, "Molecular prediction")
        self.assertTrue(reasons)

    def test_intensity_track_does_not_imply_prediction(self):
        accepted, category, tracks, _ = atlas.classify(
            "Odor intensity of perfumery raw materials",
            "Perceived intensity was measured for fragrance chemicals at serial dilutions.",
        )
        self.assertTrue(accepted)
        self.assertEqual(category, "Intensity & thresholds")
        self.assertNotIn("prediction", tracks)

    def test_characterized_oils_are_labeled_separately(self):
        accepted, category, tracks, reasons = atlas.classify(
            "Chemical composition and antimicrobial activity of lavender essential oil",
            "GC-MS analysis identified linalool as a major constituent. The oil showed antibacterial activity.",
        )
        self.assertTrue(accepted)
        self.assertEqual(category, "Characterized aroma oils")
        self.assertNotIn("prediction", tracks)
        self.assertTrue(any("essential oil chemical profile" in reason for reason in reasons))


class LocalDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.patches = contextlib.ExitStack()
        self.patches.enter_context(patch.object(atlas, "ROOT", self.root))
        self.patches.enter_context(patch.object(atlas, "DB", self.root / "data" / "atlas.sqlite"))
        self.patches.enter_context(patch.object(atlas, "get", side_effect=AssertionError("Offline tests must not access the network")))
        atlas.init()

    def tearDown(self):
        self.patches.close()
        self.directory.cleanup()

    @staticmethod
    def record(identifier, title="Odor intensity of fragrance molecules", **changes):
        row = {"id": str(identifier), "pmid": str(identifier), "source": "MED", "title": title,
               "abstractText": "Perceived odor intensity of aroma chemicals was measured.",
               "pubYear": "2020", "doi": f"10.1234/atlas.fixture{identifier}", "citedByCount": 4}
        row.update(changes)
        return row

    def test_ingest_is_idempotent_and_preserves_query_provenance(self):
        record = self.record(1)
        atlas.ingest([record], "aroma")
        atlas.ingest([record], "intensity")
        atlas.ingest([record], "intensity")
        with atlas.connect() as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM papers").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM provenance").fetchone()[0], 2)
            self.assertEqual(connection.execute("SELECT accepted FROM papers").fetchone()[0], 1)

    def test_primary_evidence_can_resolve_uncertainty_without_clearing_negatives(self):
        research = self.root / 'research'
        research.mkdir()
        (research / 'scope_audit.json').write_text(json.dumps({'records': [
            {'id':'uncertain','verdict':'uncertain','reason':'Identity not established'},
            {'id':'negative','verdict':'out-of-scope','reason':'Wrong study purpose'}]}))
        resolutions = [{'id':pid,'date':'2026-10-27','verdict':'in-scope','reason':'New primary identity evidence','sources':['https://www.femaflavor.org/']} for pid in ['uncertain','negative']]
        (research / 'scope_readjudications_2026-10-27.json').write_text(json.dumps({'resolutions':resolutions}))
        self.assertNotIn('uncertain', atlas.review_exclusions())
        self.assertIn('negative', atlas.review_exclusions())
        self.assertEqual(json.loads((research/'scope_audit.json').read_text())['records'][0]['verdict'], 'uncertain')

    def test_excluded_publication_type_overrides_scope(self):
        atlas.ingest([self.record(1, pubTypeList={"pubType": ["Patent"]})], "fixture")
        with atlas.connect() as connection:
            accepted, evidence = connection.execute("SELECT accepted,evidence FROM papers").fetchone()
        self.assertEqual(accepted, 0)
        self.assertIn("excluded publication type", json.loads(evidence))

    def test_clean_removes_markup_and_unescapes_metadata(self):
        self.assertEqual(atlas.clean("<i>Aroma</i> &amp; odor"), "Aroma  & odor")

    def test_resolve_adds_only_actual_references_and_is_idempotent(self):
        atlas.ingest([self.record(1), self.record(2), self.record(3)], "fixture")
        with atlas.connect() as connection:
            connection.executemany("INSERT INTO raw_refs VALUES(?,?,?,?,?)", [
                ("pmid:1", "MED", "2", "10.1234/atlas.fixture2", "Cited paper"),
                ("pmid:1", "MED", "1", "10.1234/atlas.fixture1", "Self reference"),
                ("pmid:1", "MED", "999", "", "Unresolved paper"),
            ])
        atlas.resolve()
        atlas.resolve()
        with atlas.connect() as connection:
            edges = connection.execute("SELECT source,target FROM edges").fetchall()
        self.assertEqual(edges, [("pmid:1", "pmid:2")])

    def test_rejected_targets_are_not_resolved_into_graph(self):
        atlas.ingest([self.record(1), self.record(2, title="Kinase inhibitors", abstractText="Drug screening.")], "fixture")
        with atlas.connect() as connection:
            connection.execute("INSERT INTO raw_refs VALUES(?,?,?,?,?)", ("pmid:1", "MED", "2", "", "Off-scope"))
        atlas.resolve()
        with atlas.connect() as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM edges").fetchone()[0], 0)

    def test_doi_alias_resolves_only_supplied_citation_and_preserves_provider(self):
        atlas.ingest([self.record(1), self.record(2)], "fixture")
        with atlas.connect() as connection:
            connection.execute("INSERT INTO source_alias VALUES(?,?,?)", ("DOI", "10.1234/old", "pmid:2"))
        atlas.resolve()
        with atlas.connect() as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM edges").fetchone()[0], 0)
            connection.execute("INSERT INTO raw_refs VALUES(?,?,?,?,?)", ("pmid:1", "Crossref", "10.1234/old", "10.1234/old", "Actual supplied reference"))
        atlas.resolve()
        with atlas.connect() as connection:
            self.assertEqual(connection.execute("SELECT source,target,provider FROM edges").fetchall(), [("pmid:1", "pmid:2", "Crossref deposited reference list")])

    def test_no_title_similarity_edges_are_invented(self):
        atlas.ingest([self.record(1), self.record(2)], "fixture")
        atlas.resolve()
        with atlas.connect() as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM edges").fetchone()[0], 0)

    def test_audit_accepts_explicit_pharmacology_track(self):
        atlas.ingest([self.record(1, title="Antibacterial activity of carvacrol", abstractText="Carvacrol inhibits bacterial growth.")], "fixture")
        result = audit_database(atlas.DB)
        self.assertNotIn("accepted_missing_valid_track", result["screening_warnings"])
        self.assertNotIn("accepted_missing_aroma_track", result["screening_warnings"])

    def test_audit_reports_curated_override_separately(self):
        atlas.ingest([self.record(1, title="Ambiguous historical reference", abstractText="")], "fixture")
        with atlas.connect() as connection:
            connection.execute("UPDATE papers SET accepted=1,tracks='[\"aroma\"]' WHERE id='pmid:1'")
            connection.execute("INSERT INTO provenance VALUES('pmid:1','curated:verified_seed')")
        result = audit_database(atlas.DB)
        self.assertEqual(result["screening_warnings"].get("curated_seed_override_of_automatic_eligibility"), 1)
        self.assertNotIn("stored_scope_differs_from_current_classifier", result["screening_warnings"])

    def test_audit_uses_native_publication_type_without_an_evidence_message(self):
        atlas.ingest([self.record(1, pubTypeList={"pubType": ["Retraction of Publication"]})], "fixture")
        with atlas.connect() as connection:
            connection.execute("UPDATE papers SET evidence='[]' WHERE id='pmid:1'")
        result = audit_database(atlas.DB)
        self.assertNotIn("stored_scope_differs_from_current_classifier", result["screening_warnings"])


def audit_database(path, sample_limit=12):
    """Return reproducible integrity/relevance warnings without changing the DB."""
    path = Path(path).resolve()
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    # One consistent WAL snapshot while an independent harvest may be writing.
    connection.execute("BEGIN")
    try:
        rows = [dict(row) for row in connection.execute("SELECT id,doi,pmid,title,abstract,source,accepted,tracks,evidence FROM papers")]
        curated_ids = {row[0] for row in connection.execute("SELECT paper FROM provenance WHERE query='curated:verified_seed'")}
        reviewed_exclusions = set(atlas.review_exclusions())
        provider_classifiers = {}
        for source, module, function in [("Crossref", "supplement", "classify_record"), ("SemanticScholar", "semantic", "classify"), ("OpenAlex", "openalex", "classify")]:
            if any(row["source"] == source for row in rows):
                provider_classifiers[source] = getattr(importlib.import_module(module), function)
        accepted = {row["id"] for row in rows if row["accepted"]}
        ids = {row["id"] for row in rows}
        reasons = collections.Counter()
        examples = collections.defaultdict(list)
        def flag(key, row):
            reasons[key] += 1
            if len(examples[key]) < sample_limit:
                examples[key].append({"id": row["id"], "title": row["title"]})
        duplicate_doi = collections.defaultdict(list)
        duplicate_pmid = collections.defaultdict(list)
        for row in rows:
            if row["doi"]:
                duplicate_doi[row["doi"].lower().removeprefix("https://doi.org/")].append(row["id"])
            if row["pmid"]:
                duplicate_pmid[row["pmid"]].append(row["id"])
            current, _, tracks, _ = atlas.classify(row["title"] or "", row["abstract"] or "")
            excluded_publication = "excluded publication type" in (row["evidence"] or "")
            if row["source"] in {"MED", "PMC", "PPR", "AGR"}:
                native = json.loads(connection.execute("SELECT raw FROM papers WHERE id=?", (row["id"],)).fetchone()[0])
                publication_types = " ".join(native.get("pubTypeList", {}).get("pubType", [])).lower()
                excluded_publication = excluded_publication or any(v in publication_types for v in ["patent", "book review", "retract", "erratum"])
            expected = bool(current and not excluded_publication)
            if row["source"] in provider_classifiers:
                try:
                    raw = json.loads(connection.execute("SELECT raw FROM papers WHERE id=?", (row["id"],)).fetchone()[0])
                    # Curated seed payloads have normalized lower-case DOI rather
                    # than a native Crossref record; their override is explicit.
                    if not (row["source"] == "Crossref" and "DOI" not in raw):
                        expected = bool(provider_classifiers[row["source"]](raw)[0])
                except Exception:
                    expected = False
                    flag("provider_eligibility_audit_error", row)
            if row["id"] in reviewed_exclusions:
                if row["accepted"]:
                    flag("reviewed_exclusion_still_accepted", row)
                elif expected:
                    flag("diagnostic_review_exclusion_override_of_automatic_eligibility", row)
                expected = False
            if bool(row["accepted"]) != expected:
                if row["accepted"] and row["id"] in curated_ids:
                    flag("curated_seed_override_of_automatic_eligibility", row)
                else:
                    flag("stored_scope_differs_from_current_classifier", row)
            if not row["accepted"]:
                continue
            text = (row["title"] or "") + " " + (row["abstract"] or "")
            if re.search(r"\baromat(?:ic|ase|ization|isation)\w*\b", text, re.I) and not re.search(r"\b(?:aromas?|fragrance\w*|perfum\w*|odou?r\w*|olfactor\w*|smell\w*)\b", text, re.I):
                flag("aromatic_or_aromatase_only", row)
            if re.search(r"\b(?:ectopic|cancer|tumou?r|biomarker)\b", text, re.I) and re.search(r"olfactory receptor", text, re.I):
                flag("review_ectopic_receptor_context", row)
            if re.search(r"electronic nose|e-nose|chemical sensor array", text, re.I):
                flag("review_sensor_hardware_context", row)
            if re.search(r"\b(?:pheromone|insect|moth|mosquito)\w*\b", text, re.I):
                flag("review_insect_context", row)
            try:
                stored_tracks = json.loads(row["tracks"] or "[]")
                json.loads(row["evidence"] or "[]")
            except (ValueError, TypeError):
                flag("invalid_evidence_or_tracks_json", row)
                continue
            if not set(stored_tracks) & {"aroma", "prediction", "pharmacology"}:
                flag("accepted_missing_valid_track", row)
            if set(stored_tracks) - {"aroma", "prediction", "pharmacology"}:
                flag("unrecognized_track", row)
        edges = [tuple(row) for row in connection.execute("SELECT source,target FROM edges")]
        ref_totals = dict(connection.execute("SELECT status,count(*) FROM refs GROUP BY status"))
        query_rows = [dict(row) for row in connection.execute("SELECT name,hits,seen,complete FROM queries")]
        result = {
            "database": str(path),
            "counts": {"candidates": len(rows), "accepted": len(accepted), "rejected": len(rows)-len(accepted), "unique_directed_edges": len(set(edges)), "raw_edge_rows": len(edges)},
            "query_completion": query_rows,
            "reference_status": ref_totals,
            "reference_retention": {
                "returned_reference_rows": connection.execute("SELECT coalesce(sum(retrieved),0) FROM refs").fetchone()[0],
                "retained_unique_raw_reference_rows": connection.execute("SELECT count(*) FROM raw_refs").fetchone()[0],
                "complete_requests_returning_zero_references": connection.execute("SELECT count(*) FROM refs WHERE status='complete' AND total=0").fetchone()[0],
                "note": "Returned request counts and retained rows may cover different providers; additional imports, deduplication and missing identifiers make these counts non-comparable. A successful zero-result request does not establish a paper has no references.",
            },
            "integrity": {
                "dangling_edges": sum(s not in ids or t not in ids for s,t in edges),
                "edges_outside_current_accepted_set": sum(s not in accepted or t not in accepted for s,t in edges),
                "self_edges": sum(s == t for s,t in edges),
                "duplicate_doi_groups": sum(len(v)>1 for v in duplicate_doi.values()),
                "duplicate_pmid_groups": sum(len(v)>1 for v in duplicate_pmid.values()),
                "completed_reference_rows_retrieved_less_than_total": connection.execute("SELECT count(*) FROM refs WHERE status='complete' AND retrieved<total").fetchone()[0],
            },
            "screening_warnings": dict(reasons),
            "examples": dict(examples),
            "duplicate_doi_examples": [{"doi": key, "ids": value} for key,value in duplicate_doi.items() if len(value)>1][:sample_limit],
            "limitations": "Synthetic fixture checks and automatic audits do not establish precision/recall or manual relevance. Warning contexts require inspection. Metadata coverage and citation availability are incomplete.",
        }
        return result
    finally:
        connection.close()


if __name__ == "__main__":
    if "--audit-db" in sys.argv:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--audit-db", required=True, type=Path)
        parser.add_argument("--sample-limit", default=12, type=int)
        args = parser.parse_args()
        print(json.dumps(audit_database(args.audit_db, args.sample_limit), indent=2))
    else:
        unittest.main()
