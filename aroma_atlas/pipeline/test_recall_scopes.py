"""Frozen metadata challenge cases and chemical-identity scope boundaries."""
import json
from pathlib import Path
import unittest
import atlas
import supplement


class RecallScopes(unittest.TestCase):
    def test_frozen_metadata_scope_challenges(self):
        path = Path(__file__).resolve().parents[1]/'research/recall_routes_oct28/frozen_metadata_review.json'
        for row in json.loads(path.read_text())['records']:
            with self.subTest(doi=row['doi'], title=row['title']):
                expected = row['verdict'].startswith('in-scope')
                self.assertEqual(atlas.classify(row['title'], row['abstract'])[0], expected)
                payload = {'title': [row['title']], 'abstract': row['abstract'],
                           'type': 'journal-article', 'published': {'date-parts': [[2020, 1, 1]]}}
                self.assertEqual(supplement.classify_record(payload)[0], expected)

    def test_v6_unchanged_parent_not_arbitrary_drug_hybrid(self):
        self.assertTrue(atlas.classify('Ethyl vanillin reduces inflammatory responses',
                                        'Receptor pharmacology and anti-inflammatory activity of ethyl vanillin were assessed.')[0])
        self.assertFalse(atlas.classify('Ethyl vanillin derived quinazoline hybrids against cancer',
                                         'New substituted drug scaffolds were assessed for cytotoxic activity.')[0])

    def test_v6_production_requires_aroma_purpose(self):
        self.assertFalse(atlas.classify('Synthesis of piperonal', 'A drug intermediate was prepared.')[0])
        self.assertTrue(atlas.classify('Synthesis of piperonal', 'The fragrance ingredient was produced by biocatalysis.')[0])

    def test_oxidized_aerosol_products_do_not_inherit_parent_physical_properties(self):
        self.assertFalse(atlas.classify('Explicit modelling of SOA formation from alpha-pinene photooxidation: sensitivity to vapour pressure estimation',
                                         'Vapour pressures of atmospheric oxidation products were predicted.')[0])
        self.assertTrue(atlas.classify('Vapour pressure of alpha-pinene',
                                        'Measurements of the unchanged compound.')[0])

    def test_musk_parent_identity_does_not_admit_musk_mixtures_or_derivatives(self):
        self.assertTrue(atlas.classify('Muscone attenuates inflammatory responses',
                                        'Pharmacological activity of muscone was measured.')[0])
        self.assertFalse(atlas.classify('Muscone derivatives as anticancer scaffolds',
                                         'Substituted drug hybrids were assessed.')[0])
        self.assertFalse(atlas.classify('Ambrettolide inhibits inflammation',
                                         'Pharmacological activity was measured; connectivity is unspecified.')[0])
        self.assertFalse(atlas.classify('MuSK antibodies in myasthenia gravis',
                                         'The muscle-specific receptor controls neural molecular signaling.')[0])

    def test_substituted_constituent_is_not_the_registered_unchanged_parent(self):
        self.assertFalse(atlas.identified_parent('GC-MS identified the major component 2-hydroxy-4-methoxybenzaldehyde (78%).'))
        self.assertTrue(atlas.identified_parent('GC-MS identified the major component 4-methoxybenzaldehyde (78%).'))

    def test_polymerized_lactone_is_not_the_free_parent(self):
        self.assertFalse(atlas.parent_in_title('Protein release from poly(glycerol adipate-co-omega-pentadecalactone)'))
        self.assertTrue(atlas.parent_in_title('Vapour pressure of omega-pentadecalactone'))
        self.assertFalse(atlas.classify('Ethyl vanillin incorporated chitosan/poly(vinyl alcohol) active films for food packaging applications',
                                         'The antibacterial films showed Schiff base formation and increased tensile strength.')[0])

    def test_parent_as_drug_detection_reagent_or_scaffold_is_outside_parent_pharmacology(self):
        self.assertFalse(atlas.classify('Fluorescent probing for Mirabegron determination through condensation with phenylacetaldehyde',
                                         'The receptor agonist was measured using a condensation reagent.')[0])
        self.assertFalse(atlas.classify('Chalcones derived from piperonal as antimicrobial agents',
                                         'The substituted new compounds had antimicrobial activity.')[0])


if __name__ == '__main__':
    unittest.main()
