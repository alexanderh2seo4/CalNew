# Aroma Research Atlas — 30 October 2026

Private explorer and hosting details are excluded from this public export.

The reconciled export contains **50,104 automatically included publication records** and **298,910 unique directed citation connections**, from 242,205 distinct retrieved candidates. The target of 50,000 in-scope records is **met numerically**. These are publication records, not distinct experiments or manually verified papers. Discovery is checkpointed; completion and scheduling status are recorded in WORK_STATUS.md.

## Focal maps

- **Aroma and intensity:** 33,464 records. Aroma chemistry, volatile food aroma, intensity/thresholds, parent odorant production and relevant databases. The volatility/partitioning theme also contains physical-property calculations; it does not imply direct sensory intensity measurement.
- **Prediction and pharmacophores:** 2,958 records. Molecular odor prediction and olfactory models, overlapping the aroma map.
- **Separate pharmacology context:** 16,640 records. Unchanged parent aroma chemical pharmacology, fragrance safety and identified oil-mixture studies. Mixture effects do not establish constituent effects.

!Atlas overview (local artifact omitted from the public snapshot)

## Coverage and provenance

| Measure | Count |
|---|---:|
| Included publication records | 50,104 |
| Unique directed citation pairs | 298,910 |
| Papers with a matched citation | 40,633 |
| Largest connected component | 40,352 |
| Reference-indexing records processed | 50,054 |
| Papers with nonempty indexed reference lists | 39,688 |
| Raw reference rows attached to included records | 2,131,739 |
| Raw reference rows across all candidates | 5,299,792 |

Reference indexing is processed for 99.90% of included records; 79.21% have a nonempty indexed list. Processed means at least one source response, with nonempty evidence combined across actual provider lists. A processed zero-result lookup does not establish absence of a bibliography. Limited Semantic Scholar records retain unknown availability after anonymous throttling.

Edges point from citing paper to cited paper. DOI, PMID or actual provider work IDs establish connections. Multiple provider observations count as one directed pair; the citation CSV retains provenance. Unresolved and rejected endpoints remain outside the visible graph.

## Themes

| Theme | Included records |
|---|---:|
| Aroma chemical pharmacology | 11,851 |
| Food & flavor chemistry | 11,837 |
| Fragrance & aroma chemistry | 8,959 |
| Intensity & thresholds | 7,886 |
| Characterized aroma oils | 2,442 |
| Fragrance safety & pharmacology | 2,347 |
| Molecular prediction | 2,064 |
| Odorant receptor chemistry | 1,591 |
| Receptors & pharmacophores | 735 |
| Volatility & partitioning | 212 |
| Databases & benchmarks | 180 |

## Highly connected papers

Ranked by observed incoming plus outgoing citation connections within this atlas, rather than source-index citation totals.

### Aroma and intensity

| Publication | Year | Atlas connections |
|---|---:|---:|
| [A novel multigene family may encode odorant receptors: a molecular basis for odor recognition.](https://doi.org/10.1016/0092-8674%2891%2990418-x) | 1991 | 803 |
| [Solvent assisted flavour evaporation--a new and versatile technique for the careful and direct isolation of aroma compounds from complex food matrices.](https://doi.org/10.1007/s002170050486) | 1999 | 578 |
| [Quantification and sensory studies of character impact odorants of different white wine varieties.](https://doi.org/10.1021/jf970280a) | 1997 | 484 |
| [Combinatorial receptor codes for odors.](https://doi.org/10.1016/s0092-8674%2800%2980581-4) | 1999 | 469 |
| [Quantitative determination of the odorants of young red wines from different grape varieties](https://doi.org/10.1002/1097-0010%2820000901%2980%3A11%3C1659%3A%3Aaid-jsfa693%3E3.0.co%3B2-6) | 2000 | 442 |
| [Re-investigation on odour thresholds of key food aroma compounds and development of an aroma language based on odour qualities of defined aqueous odorant solutions](https://doi.org/10.1007/s00217-008-0931-x) | 2008 | 419 |
| [Biosynthesis of plant-derived flavor compounds.](https://doi.org/10.1111/j.1365-313x.2008.03446.x) | 2008 | 413 |
| [Evaluation of the key odorants of foods by dilution experiments, aroma models and omission.](https://doi.org/10.1093/chemse/26.5.533) | 2001 | 353 |
| [Nature's chemical signatures in human olfaction: a foodborne perspective for future biotechnology.](https://doi.org/10.1002/anie.201309508) | 2014 | 333 |
| [Recent studies of the volatile compounds in tea](https://doi.org/10.1016/j.foodres.2013.02.011) | 2013 | 330 |

### Prediction and pharmacophores

| Publication | Year | Atlas connections |
|---|---:|---:|
| [Odor coding by a Mammalian receptor repertoire.](https://doi.org/10.1126/scisignal.2000016) | 2009 | 255 |
| [How the olfactory system makes sense of scents.](https://doi.org/10.1038/35093026) | 2001 | 220 |
| [Decoding Sulfur-Containing Aroma Compounds in Foods: From Key Odorant Mapping to Structure-Odor Mechanisms and Flavor Design.](https://doi.org/10.3390/foods15173003) | 2026 | 173 |
| [Structure−Odor Relationships](https://doi.org/10.1021/cr950068a) | 1996 | 159 |
| [Structural basis for a broad but selective ligand spectrum of a mouse olfactory receptor: mapping the odorant-binding site.](https://doi.org/10.1523/jneurosci.4723-04.2005) | 2005 | 158 |
| [The human olfactory receptor gene family.](https://doi.org/10.1073/pnas.0307882100) | 2004 | 146 |
| [Structure–odour relationships reviewed in the postgenomic era](https://doi.org/10.1002/ffj.3249) | 2015 | 145 |
| [Predicting human olfactory perception from chemical features of odor molecules.](https://doi.org/10.1126/science.aal2014) | 2017 | 132 |
| [Predicting odor pleasantness from odorant structure: pleasantness as a reflection of the physical world.](https://doi.org/10.1523/jneurosci.1158-07.2007) | 2007 | 125 |
| [Structural determinants of odorant recognition by the human olfactory receptors OR1A1 and OR1A2.](https://doi.org/10.1016/j.jsb.2007.04.013) | 2007 | 116 |

## A software-paper neighborhood

Search the Principal Odor Map, DREAM challenge, Pyrfume or FlavorDB from the landmark shortcuts. Citation neighborhoods display all collected neighbors even if they fall outside the previous filter.

!Prediction-paper neighborhood (local artifact omitted from the public snapshot)

## Validation and limits

The full graph, metadata and edge shards, both CSVs and directed GEXF are reconciled against SQLite by `pipeline/validate_export.py`; mandatory integrity/scope audit failures prevent successful orchestration. Offline tests check representative scope errors, provider eligibility, exact identity reuse, real references and public-budget stops. Passing code and structural checks does not certify scientific relevance for every paper.

The original frozen AI diagnostic review (`research/scope_audit.json`: 50 stratified records, 32 in-scope, 12 out-of-scope, 6 uncertain) remains unchanged. The parent expansion diagnostic (`research/parent_expansion_diagnostic_2026-10-27.json`: 40 records, including 10 targeted failure examples) is also preserved. They use titles/available abstracts, not full-text or human adjudication. Selected failures and uncertain records are excluded; neither sample yields a corpus precision estimate. Additional Crossref completion, later-parent, flavor-title, DOI citation-neighbor and PMID-neighbor diagnostics are retained separately with frozen selection methods and original findings. These stratified/targeted AI samples are not population error-rate estimates. A dated primary-source readjudication can resolve an original uncertainty without overwriting it, and never overrides current provider or scope eligibility.

The additional parent allowlist records exact identities and primary source evidence. Historical flavor membership does not imply current authorization, safety or efficacy: estragole, methyl eugenol and safrole retain their source cautions. Derivatives, organometallic complexes, reagent-only/solvent-only use and pest-only studies do not qualify through parent membership. Coumarin drug-family ambiguity requires explicit parent identity evidence; benzyl-alcohol/coumarin production requires aroma purpose. Isomers and commercial-mixture caveats are retained. Versioned v5–v7 allowlists add source-verified lactone, terpene, alcohol, ester, aldehyde and musk identities, with exact isomer and unchanged-parent restrictions. Frozen full-bibliographic AGR/MED identity proofs remove verified cross-index duplicates; secondary ChemInform summaries are excluded as separate research publications. Known historical fragrance status is not a clinical or regulatory endorsement.

Source streams have different completion states. Europe PMC routes are cursor-paginated; some Crossref streams are exhausted while broader searches and new parent streams remain bounded. OpenAlex is limited by a conservative public budget reserve and Semantic Scholar by anonymous throttling. Provider hit estimates are not included counts. Absence from this atlas does not establish absence from the literature; no claim is made that fewer than 50,000 relevant papers exist. Some preprint/journal versions remain distinct.

Layout proximity is a navigational aid, not validated chemical similarity. The overview draws at most 30,000 actual citation lines; full collected neighborhoods and exports remain accessible. The atlas maps bibliographic references, without full-text quotation or potency extraction.

See [methods](pipeline/METHODOLOGY.md), [resume instructions](README.md), [statistics](data/stats.json), [export reconciliation](data/export_validation.json), [integrity audit](data/integrity_audit.json), and the source coverage reports in `research/`. The private Site deployment receipt is `data/publication.json`; the SQLite evidence/checkpoint store is `data/atlas.sqlite`.
