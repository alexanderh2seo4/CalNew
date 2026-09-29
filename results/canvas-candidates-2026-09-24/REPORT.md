# Candidate molecules worth investigating with the current CALNEW models

## Recommendation

Invest first in **small, informative comparison series**, rather than choosing the molecule with the lowest predicted threshold. My first choices are **cyclamen aldehyde**, a **phenylacetaldehyde / 2-phenylethanol / phenethyl acetate series**, and **gamma-/delta-decalactone**. For the original marine project, investigate a **Calone alkyl-substitution series**, but do not claim that the model has found a more potent marine molecule.

I calculated predictions for **21 structures** using the saved threshold and descriptor models. Eighteen are PubChem-resolved reference structures; three are explicitly defined Calone analogues. All eight threshold experts and all four descriptor experts returned finite predictions. The screening does not add any observation to the training store.

## What the numbers mean

- Threshold point estimates come from the selected RDKit-descriptor regression, not the average of all eight experts. Units are **airborne ppbv**; lower means stronger predicted detection potency.
- The interval is the existing model's nominal 90% conformal interval. It is roughly a factor of **54 below/above** each point estimate. Coverage has not been independently demonstrated for these new chemical distributions.
- Descriptor outputs come from the calibrated average of the four basic descriptor experts. They predict catalogue annotations, not participant liking or assured perception.
- The retained vocabulary has **no marine, watery or ozonic head**. Refractory/recovery time and pleasantness are also unavailable. The model cannot optimise these canvas criteria directly.
- All candidates except 2-phenylethanol are outside the threshold development/calibration/test molecular groups. Many were present in descriptor training, so their odour profiles are not independent predictions of unseen chemistry. Each record states its partition membership.

## Prioritised research shortlist

| Candidate or comparison | Predicted threshold, ppbv | Nominal 90% interval, ppbv | Model's main descriptor annotations | Why it is worth investigating |
|---|---:|---:|---|---|
| **Cyclamen aldehyde** | **0.29** | **0.0054–16** | Floral, green, sweet | Best first generalisation candidate in this shortlist: outside both endpoint datasets, moderate structural size, one aromatic ring and a side chain that permits controlled changes. Test defined isomer composition. |
| **Phenylacetaldehyde** | **0.12** | **0.0022–6.4** | Floral, green, sweet | A small scaffold: nine heavy atoms. Pair with its alcohol and an ester to separate functional-group effects from a wholesale change in skeleton. The descriptor model has seen its group. |
| **2-Phenylethanol** | **6.0** | **0.11–320** | Floral, sweet, rose | A reference for the preceding series. Present in both development datasets; useful as an anchor, not an independent architecture-validation molecule. |
| **Phenethyl acetate** | **4.0** | **0.075–220** | Fruity, floral, sweet | Extends the same two-carbon aromatic side-chain series. Its predicted threshold differs too little from the alcohol to establish a reliable ordering. |
| **gamma-Decalactone / delta-Decalactone** | **37 / 34** | **0.68–2,000 / 0.64–1,900** | See full output; gamma is fatty, peach, creamy | A ring-size comparison with the same elemental composition. Useful for controlled structure–odour learning and a different fragrance direction. The model does not resolve a potency advantage. Both descriptor groups were seen in training. |
| **7-Ethyl Calone scaffold** | **1.5** | **0.029–83** | Sweet, floral, spicy | A small structural change from Calone, outside both endpoint datasets. An informative analogue, not a demonstrated marine or novelty hit. Material access/synthesis remains unverified. |
| **Floralozone reference structure** | **0.029** | **0.00054–1.6** | Floral, green, sweet | An exploratory potency candidate with a compact aromatic-aldehyde framework. The other experts mostly predict much higher thresholds, so validate before prioritising a derivative programme. Match the exact supplied structural/isomer composition. |

These are research priorities based on the combination of predicted behaviour, interpretability of a comparison and chemical structure. They are **not measured thresholds or procurement recommendations**. No current price, synthesis cost or supplier batch has been verified.

## The canvas criteria, applied explicitly

| Canvas factor | What can be concluded now | Consequence for selection |
|---|---|---|
| Potency | A central log-threshold prediction, broad interval and expert disagreement are available. Most shortlisted molecules have only moderate/low threshold-training similarity. | Use predictions to select informative tests; avoid treating small differences as real improvements. |
| Odour profile | Broad catalogue labels are predicted. Marine/watery/ozonic are absent from the current model. | Marine projects require separate evidence and measurements. |
| Positive smell | Floral/fruity/peach are descriptor categories, not a liking score. | Measure pleasantness at controlled delivered concentrations. |
| Refractory time | No current prediction or acquired matched data. | Keep recovery/adaptation testing separate from chemical persistence or fabric tenacity. |
| Complexity | Molecular size, ring count, rotatable bonds and a graph-complexity descriptor were calculated. | Prefer interpretable low-complexity series initially. These features do not establish synthesis difficulty. |
| Modifiability | Structural reasoning suggests side-chain, functional-group and ring-size comparisons. | Change one feature at a time, retain material/isomer identity and compare under the same method. |
| Novelty | The named reference compounds are known. Related Calone substitutions occur in prior art. | Treat the project as scaffold investigation first; novelty needs a separate structure/patent search. |
| Number of known derivatives | Existing primary work and patents establish that the Calone family has studied analogues, but an audited numerical inventory was not built here. | Curate actual structures and results; do not substitute patent family size for independent measurements. |
| Chance of a potent derivative | The current model does not provide a validated probability of successful analogue optimisation. | Combine uncertainty with a matched comparison series and new measurements. |

## Calone: useful as a scaffold, but the model cannot choose the winning derivative

| Defined structure | Predicted threshold, ppbv | Heavy atoms |
|---|---:|---:|
| Calone, 7-methyl | 2.11 | 13 |
| 7-Ethyl analogue | 1.54 | 14 |
| 7-n-Propyl analogue | 1.38 | 15 |
| 7-Isopropyl analogue | 11.25 | 15 |

The ethyl and n-propyl estimates are only approximately **1.4–1.5 times lower** than Calone. That is far below the uncertainty supported by the current model; it is not a credible potency improvement claim. The n-propyl/isopropyl pair is nevertheless informative because it changes branching at constant formula.

Published evidence also cautions against assuming that a small structural change preserves marine character. [EP0902024B1](https://patents.google.com/patent/EP0902024B1/en) describes the n-propyl compound as having an aldehydic character and distinguishes it from Calone's ozonic/marine character. The same source discusses other 7-position substitutions, so these examples are not presented as novel structures.

[dsm-firmenich's Calone page](https://studio.dsm-firmenich.com/product/caloner-pe-918970) supports its role as a marine/watery reference. Separately, [WO2018163800A1](https://patents.google.com/patent/WO2018163800A1/en) reports receptor assays involving Calone and related marine odorants, including OR10H5. This makes the family relevant to a future receptor experiment; it does not supply a human threshold or prove a universal marine receptor mechanism.

**Benchmark protection:** Calone belongs to the descriptor model's reserved test group. Its structure was scored here, but its stored test labels were not opened. Keep it as a literature reference and preserve the frozen evaluation; do not put it into model development before that evaluation is resolved.

## High-value diagnostics rather than leading bets

**Helional:** the selected model predicts 0.0053 ppbv, but the experts span approximately **0.00073–29 ppbv**. Threshold-training similarity is only 0.21. Its green/floral character has independent manufacturer support from [IFF](https://www.iff.com/scent/ingredients-compendium/helional/), but the extreme potency number should be treated as a diagnostic of extrapolation and expert disagreement. It is worth measuring to challenge the model, not worth promoting solely because it ranks first.

**Ambroxide and ionones:** the model gives high thresholds on structurally distant examples. Low similarity and uncertain transfer mean these should not be discarded as weak fragrance materials on that basis. They are useful tests of where the current model fails. The alpha/beta-ionone and some named commercial materials require explicit stereochemical/material definitions before a literature comparison.

**Melonal, cis-3-hexenol and methyl dihydrojasmonate:** their descriptor groups are reserved for calibration or final testing. Their computed outputs remain in the full table, but they are excluded from the proposed immediate measurement-development shortlist.

## Suggested first allocation

For a **general project**, start by assessing access to cyclamen aldehyde, phenylacetaldehyde, 2-phenylethanol, phenethyl acetate, gamma-decalactone and delta-decalactone. These cover an unseen candidate, a reference anchor, a functional-group series and a ring-size series. Obtain defined materials and use common verified delivery conditions before interpreting threshold comparisons.

For a **marine-focused follow-up**, assess access to 7-ethyl, 7-n-propyl and 7-isopropyl Calone analogues as a controlled series, with published Calone evidence as the initial anchor. Resolve novelty and synthesis feasibility before selecting a synthesis programme. Do not infer that the n-propyl analogue preserves marine character.

If the purpose is **improving the model**, add Helional as a high-disagreement challenge. If the purpose is **finding a commercially useful molecule**, measured odour quality, delivery, liking, stability, recovery and a novelty assessment must precede the investment decision.

## Files and reproducibility

- [All predictions and structural features](screening.json)
- [Candidate identity inputs](candidate-inputs.json)
- [All structures](candidate-structures.png)
- [Screening script](../../scripts/screen_canvas_candidates.py)

PubChem lookup responses are retained under `identities/`, including CID, SMILES, InChIKey and lookup URL. The three computational analogues have explicit SMILES and an identified prior-art reference. The script verifies resolved InChIKeys against RDKit identities. Every prediction records the fitted model ID, source membership and all expert outputs.

No model was retrained, no final-test sensory labels were read, and no predicted value was added as measured evidence.
