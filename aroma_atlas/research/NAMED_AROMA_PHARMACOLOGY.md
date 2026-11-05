# Named aroma compounds and pharmacology: scope recommendation

The user's scope permits pharmacology **of aroma chemicals**. An additional track can therefore include studies whose central experimental agent is a documented fragrance/flavor compound, even where their abstracts do not discuss odor perception. This is a different category from odor intensity and should be labeled accordingly.

## Primary evidence for membership

Health Canada's [cosmetic industry guide, Appendix 1](https://www.canada.ca/en/health-canada/services/consumer-product-safety/reports-publications/industry-professionals/labelling-cosmetics.html) identifies fragrance ingredients including linalool, limonene, eugenol, menthol, vanillin, anethole, camphor, geraniol, citral, farnesol, carvone, pinene and terpineol. The list establishes fragrance use; it does not establish therapeutic efficacy or safety of a use.

Individual government ingredient records also explicitly identify fragrance/flavour roles:

- [Linalool, CAS 78-70-6](https://webprod.hc-sc.gc.ca/nhpid-bdipsn/ingredReq?id=2349)
- [d-Limonene, CAS 5989-27-5](https://webprod.hc-sc.gc.ca/nhpid-bdipsn/ingredReq?id=2346)
- [Eugenol, CAS 97-53-0](https://webprod.hc-sc.gc.ca/nhpid-bdipsn/ingredReq?id=2191)
- [Vanillin, CAS 121-33-5](https://webprod.hc-sc.gc.ca/nhpid-bdipsn/ingredReq?id=3061&wbdisable=true)
- [FDA menthol flavoring record](https://hfpappexternal.fda.gov/Scripts/Fdcc/index.cfm?id=MENTHOL&set=FoodSubstances)

Additional chemical identities can be checked against the [FDA food substance inventory](https://www.hfpappexternal.fda.gov/scripts/fdcc/index.cfm?order=ASC&set=FoodSubstances&showAll=true&sort=Sortterm_ID) or the underlying molecule datasets documented by the Pyrfume/FlavorDB papers. Registry identity should be retained. Generic compound-family names are insufficient.

## Reproducible candidate counts

`named_chemical_pharmacology_counts.json` stores exact Europe PMC URLs for 15 exploratory chemical queries. The query requires the chemical name in the **title**, at least one pharmacological activity/mechanism term in title/abstract, and a publication date through 26 October 2026. Their counts sum to 6,039 before deduplication; they are not 6,039 verified inclusions.

Counts for the five originally suggested compounds: linalool 307; limonene 309; eugenol 1,025; menthol 527; vanillin 364. Broadening names to abstract mentions will increase recall and incidental mentions together.

## Inclusion design

1. Curate a finite identity-based allowlist of established parent fragrance/flavor molecules, with CAS/PubChem identity and source per chemical.
2. Require the exact parent name in title, or stronger abstract evidence that the parent compound is administered, assayed, bound, or mechanistically studied.
3. Require a pharmacology or toxicology outcome/mechanism. Add the category `Aroma compound pharmacology` so users can filter it independently.
4. Do not include every synthetic derivative, hybrid, Schiff-base, scaffold library or generic aromatic compound just because its name contains the parent name. Parent fragrance membership does not transfer to arbitrary derivatives.
5. Exclude menthol-cigarette marketing/epidemiology without compound mechanisms, vanillin polymers/materials chemistry without aroma or pharmacology, and solvent-only uses.
6. Avoid broad coumarin or salicylate-family expansion unless the unchanged parent fragrance agent itself is central. These families include much unrelated medicinal chemistry.
7. Flag this as automated screening and retain evidence in every record; do not claim manual review or clinical efficacy.

This approach is a legitimate scope expansion but is unlikely by itself to yield an additional 20,000 rigorously relevant papers under title-central screening. Do not relax criteria to reach a number.


## Additional verified parent compounds (27 October 2026)

The following individual FDA records explicitly classify each named parent as a flavoring agent or adjuvant. Identity and eligibility provenance are also stored in `named_aroma_allowlist_additions.json`.

| Parent compound | CAS | Primary identity/use evidence |
|---|---|---|
| Carvacrol | 499-75-2 | [FDA carvacrol record](https://hfpappexternal.fda.gov/scripts/fdcc/index.cfm?id=CARVACROL&set=FoodSubstances) |
| Thymol | 89-83-8 | [FDA thymol record](https://hfpappexternal.fda.gov/scripts/fdcc/index.cfm?id=THYMOL&set=FoodSubstances) |
| Cinnamaldehyde (cinnamic aldehyde; cinnamal) | 104-55-2 | [FDA cinnamaldehyde record](https://hfpappexternal.fda.gov/scripts/fdcc/index.cfm?id=CINNAMALDEHYDE&set=FoodSubstances) |
| Isoeugenol | 97-54-1 | [FDA isoeugenol record](https://hfpappexternal.fda.gov/scripts/fdcc/index.cfm?id=ISOEUGENOL&set=FoodSubstances) |

Cinnamal and isoeugenol are additionally named in Health Canada's fragrance-ingredient list. These source records establish ingredient membership, not the relevance of every paper mentioning a name or the clinical efficacy of a compound.


## Expanded identity allowlist

`named_aroma_allowlist_expanded.json` now records 19 source-verified parent identities spanning all requested additional candidates. Each has a browsed individual FDA or Health Canada record, CAS as reported, exact-name variants, and inclusion restrictions. Eucalyptol/1,8-cineole is one identity. Generic ionone is split into alpha- and beta-ionone; use exact isomer names rather than allowing every ionone-derived scaffold. Phenethyl alcohol and benzaldehyde are established odorants that also have other industrial functions: retain pharmacology of the unchanged parent and exclude solvent-only use.
