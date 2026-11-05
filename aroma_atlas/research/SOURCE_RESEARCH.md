# Aroma citation atlas: verified source research

Retrieval date: 26 October 2026. This report concerns metadata and citation harvesting; it does not certify full-text relevance of each harvested record.

## API availability actually tested

All five services returned HTTP 200 without credentials from this machine on a small request.

| Service | Role | Tested request | Current practical constraints |
|---|---|---|---|
| Europe PMC | Primary biomedical/life-science candidate harvest, abstracts, references and citing papers | `search?query=olfactophore&format=json&resultType=core&pageSize=1` | No key needed. Use cursorMark and cache results. Coverage is not all chemistry literature. `/{source}/{id}/references` and `/citations` are available. Citation counts describe the Europe PMC citation network. |
| Crossref | Resolve exact DOI metadata and publisher-deposited reference lists | `/works?query=olfactophore&rows=1` | Runtime header for this anonymous request was 1 request / 1 second. Read headers rather than assuming a historic fixed rate. Reference lists are publisher-deposited and can be absent or contain unresolved strings. Use cursor paging for search. |
| OpenAlex | Broad scholarly metadata, `referenced_works`, citation expansion | `/works?search=olfactophore&per_page=1` | Runtime shared-IP daily budget $0.10; this list request cost $0.001 (10 credits), leaving 990/1000 credits. Official current docs say keyless 10 requests/s, free key 30/s, max per_page 100, basic paging up to 10,000, and cursor paging past first page needs a verified free API key. A free key raises daily budget to $1. Do not trigger signup without the user's actual email and activation. |
| OpenCitations Index v2 | Independent DOI citation edge evidence | `/index/v2/references/doi:10.1126/science.aal2014` | Current official docs: 180 requests/minute/IP; optional access token encouraged for frequent use. Large pulls should use public dumps. Returns OCI plus citing/cited identifier strings; strings can contain multiple identifiers. |
| Semantic Scholar | Supplemental references/citations and discovery | `/graph/v1/paper/DOI:10.1126/science.aal2014?fields=title,citationCount,references.title` | Public requests share throttling with other anonymous clients. Official default authenticated introductory quota is 1 request/s. Public availability is not a guarantee of sustained bulk access. Dataset endpoints require key. |

The API policy landscape changed during 2026. Prefer the current OpenAlex Help Center over old OpenAlex GitBook/GitHub pages; older pages still state incompatible keyless limits.

Official sources:

- [OpenAlex authentication and current limits](https://help.openalex.org/api/authentication/)
- [OpenAlex pricing](https://help.openalex.org/access/pricing/)
- [Europe PMC REST documentation](https://europepmc.org/RestfulWebService)
- [Europe PMC citation network coverage](https://europepmc.org/help)
- [Crossref paging and bulk guidance](https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-for-using-the-crossref-rest-api/)
- [OpenCitations Index API v2](https://api.opencitations.net/index/v2)
- [Semantic Scholar API tutorial](https://webflow.semanticscholar.org/product/api/tutorial)
- [Semantic Scholar API access overview](https://webflow.semanticscholar.org/product/api)

## Scale and scope checks

The saved `scope_counts.json` contains exact Europe PMC search URLs and returned counts. Counts are candidates, not accepted papers, and overlap across queries.

- Any-field odor/aroma/perfume/olfactory terms: 398,171 candidates.
- Any-field odor/aroma terms AND chemistry words: 216,479 candidates.
- The same combination restricted to title/abstract: 38,917 candidates.
- Perfume/perfumery/fragrance/aroma in title/abstract: 46,788 candidates.
- `olfactophore OR olfactophores`: 18 candidates.

The very large any-field counts are affected by full-text mentions, including incidental references. They cannot honestly be presented as a strictly relevant 50,000-paper corpus. A count target must not lower the inclusion standard. Adding Crossref and OpenAlex can extend coverage, particularly synthetic fragrance chemistry missed by PubMed, but requires record-level screening and deduplication.

Recommended inclusion evidence:

1. Explicit aroma, odorant, perfume or fragrance relevance plus chemical structure, molecule, intensity, threshold, concentration, mixture, or sensory descriptors.
2. Prediction papers must predict odor/perceived aroma or odorant-receptor activity; generic molecular prediction or drug discovery alone is insufficient.
3. Pharmacology papers must explicitly concern aroma compounds or olfactory receptor ligands. Generic aromatics, arbitrary essential-oil bioactivity without aroma-compound evidence, neurological olfactory deficits, and receptor-expression papers without relevant ligands should not inflate the core graph.
4. Citation-neighbor status alone is not inclusion evidence. Keep unscreened neighbors separate from included papers and candidate count separate from core count.
5. Books, database records, preprints, journal articles and software nodes should have separate entity types. Merge a preprint and final article only with evidence and retain both identifiers.

Avoid matching `aromatic` as `aroma`: aromatic chemistry is much broader than aroma chemistry. `volatile` alone is also insufficient.

## Seed files

`verified_seeds.json` contains API-verified dedicated seed metadata. `seed_search_results.json` is a raw audit trail and includes deliberately rejected ambiguous author/name hits; do not import that raw file wholesale. `industrial_seed_metadata.json` adds synthetic fragrance and olfactophore seeds with publisher-deposited reference lists from Crossref. No citation edges in those files are invented.

Representative seeds:

- Keller et al. 2017, DREAM odor intensity/pleasantness challenge: DOI [10.1126/science.aal2014](https://doi.org/10.1126/science.aal2014).
- Lee et al. 2023, principal odor map: DOI [10.1126/science.ade4401](https://doi.org/10.1126/science.ade4401).
- Pyrfume data integration: DOI [10.1038/s41597-024-04051-z](https://doi.org/10.1038/s41597-024-04051-z).
- FlavorDB: DOI [10.1093/nar/gkx957](https://doi.org/10.1093/nar/gkx957).
- AromaDb, aroma chemistry and therapeutic properties: DOI [10.3389/fpls.2018.01081](https://doi.org/10.3389/fpls.2018.01081).
- SuperScent: DOI [10.1093/nar/gkn695](https://doi.org/10.1093/nar/gkn695).
- OlfactionBase receptor/odorant resource: DOI [10.1093/nar/gkab763](https://doi.org/10.1093/nar/gkab763).
- Aroma blend prediction: DOI [10.1021/acsomega.4c07078](https://doi.org/10.1021/acsomega.4c07078).
- PharmaGNN 2026: DOI [10.1002/jsfa.70826](https://doi.org/10.1002/jsfa.70826).
- Human odorant receptor structure: DOI [10.1038/s41586-023-05798-y](https://doi.org/10.1038/s41586-023-05798-y).
- Marine olfactophore/threshold chemistry: DOI [10.1002/ejoc.200300174](https://doi.org/10.1002/ejoc.200300174).
- Rose odorant olfactophore: DOI [10.2533/chimia.2020.247](https://doi.org/10.2533/chimia.2020.247).
- Linear musk olfactophore: DOI [10.1002/ejoc.201501338](https://doi.org/10.1002/ejoc.201501338).
- Muguet olfactophore: DOI [10.1002/hlca.202300040](https://doi.org/10.1002/hlca.202300040).
- Abraham's 353 human detection thresholds: DOI [10.1093/chemse/bjr094](https://doi.org/10.1093/chemse/bjr094).
- Current threshold review (2026): DOI [10.1111/1541-4337.70533](https://doi.org/10.1111/1541-4337.70533).

## Software and database entity nodes

These should connect to papers by typed `describes`, `uses_dataset` or `implements` links, distinct from paper citation links.

- [Pyrfume software](https://github.com/pyrfume/pyrfume) and [public data archive](https://github.com/pyrfume/pyrfume-data).
- [OpenPOM](https://github.com/BioMachineLearning/openpom), a replication implementation of the Principal Odor Map integrated with DeepChem. The GitHub repository currently redirects/appears also as ARY2260/openpom. Record the canonical resolved URL when ingesting.
- [Leffingwell curated dataset](https://doi.org/10.5281/zenodo.4085098): research dataset has CC-BY-NC licensing; molecule rows are not papers.
- [AromaDb](https://aromadb.cimapbioinfo.in/): public website copyright restricts redistribution. Use the published paper's bibliography/metadata rather than republishing the whole database.
- [Pyrfume paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11557823/) documents dataset-specific licensing: public access does not imply every original dataset permits commercial reuse.

For node sizes, label whether size represents in-corpus degree, global provider citation count, or another metric. Database importance should emerge from actual graph evidence; do not add synthetic citation edges or manufacture giant database nodes to match an aesthetic.
