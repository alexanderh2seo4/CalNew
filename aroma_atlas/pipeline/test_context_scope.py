"""Scope boundaries: aroma chemicals versus incidental clinical/neural vocabulary."""
import unittest
import atlas


class ContextScope(unittest.TestCase):
    def accepted(self, title, abstract):
        return atlas.classify(title, abstract)[0]

    def test_clinical_odor_tests_do_not_become_chemical_intensity_research(self):
        self.assertFalse(self.accepted('Smell recovery in coronavirus disease: psychophysical olfactory thresholds',
                                       'Patients underwent olfactory threshold testing after COVID-19.'))
        self.assertTrue(self.accepted('Menthol suppresses inflammatory responses',
                                      'Menthol pharmacology and receptor activation were measured.'))
        self.assertTrue(self.accepted('Preventive effect of flavor/fragrance components on SARS-CoV-2 infections',
                                      'Fragrance compounds including cinnamyl alcohol were tested in binding and inhibition assays.'))

    def test_cell_expression_requires_ligand_chemistry(self):
        self.assertFalse(self.accepted('Membrane proteome of olfactory sensory cilia',
                                       'Olfactory receptor proteins and molecular expression were quantified.'))
        self.assertTrue(self.accepted('Odorant receptor antagonism by aroma mixtures',
                                      'Odorant molecules activated receptors; mixtures showed concentration-response antagonism.'))
        self.assertTrue(self.accepted('Discrete odors promote sensory neuron neurogenesis',
                                      'Exposure to discrete odorants and musk odors stimulated responsive neuron subtypes.'))

    def test_generic_gas_hardware_is_outside_molecular_odor_prediction(self):
        self.assertFalse(self.accepted('Artificial olfaction using semiconductor chemiresistors',
                                       'Gas sensors and molecular gas stimuli produce synaptic signals.'))
        self.assertTrue(self.accepted('Predicting fragrance intensity from molecular structure',
                                      'Aroma compounds were used to train molecular prediction models.'))

    def test_social_cues_do_not_replace_parent_aroma_pharmacology(self):
        self.assertFalse(self.accepted('Alcoholic drink odors and frontal fMRI responses',
                                       'Food odors and molecular processes in alcohol cue reward were studied.'))
        self.assertTrue(self.accepted('Linalool produces anxiolytic effects',
                                      'The established aroma compound linalool modulates receptor activity.'))


if __name__ == '__main__':
    unittest.main()
