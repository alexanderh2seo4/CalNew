# Crossref supplemental harvest coverage

Search cutoff: 26 October 2026. Harvest completed during the night of 26–27 October (Europe/Berlin).

The API parameter used was `query.title`. Crossref performs ranked candidate retrieval; a keyword query is not an exact title filter and the total result count is not a relevant-paper count. All returned rows were screened and deduplicated by DOI against the working corpus. Existing enriched Europe PMC metadata was retained. Deposited DOI references supplied real citation evidence.

## Exhausted query result streams

| Query | Retrieved candidate rows | API reported results | State |
|---|---:|---:|---|
| aroma | 13,492 | 13,492 | exhausted |
| fragrance | 5,362 | 5,362 | exhausted |
| perfume | 1,536 | 1,536 | exhausted |
| odorant | 3,514 | 3,514 | exhausted |
| olfactophore | 1 | 1 | exhausted |
| FlavorDB | 1 | 1 | exhausted |

These queries overlap. Exhaustion refers only to that API result stream at harvest time, not to exhaustive field coverage.

## Bounded ranked discovery searches

The six multiword searches below were each limited to their first 3,000 candidate rows, because Crossref's ranked search broadens them dramatically. They are explicitly incomplete and their cursors remain saved for optional continuation:

- odor prediction
- odor threshold
- structure odor
- pharmacophore odor
- olfactory receptor ligand
- aroma intensity

## Retrieval totals and artifacts

The initial pass used 31 requests. Completing the single-term streams used 15 additional requests and returned 13,368 additional rows, of which 7,071 were new DOI candidates and 3,112 passed the screening rules loaded for that run. These per-run acceptance counts precede the main pipeline's final deduplication/reclassification audit.

At completion, the supplemental response table held 40,978 distinct DOI metadata responses. The raw-reference table held 817,590 Crossref DOI-reference rows, including references from rejected candidates; only edges with accepted endpoints belong in the visible graph. These are raw data counts, not paper or graph-edge counts.

- Pipeline: `pipeline/supplement.py`
- Resume/provenance tables: `crossref_queries`, `crossref_responses`, and main `provenance`
- Machine report: `research/crossref_harvest_report.json`
- Initial log: `logs/crossref_supplement.log`
- Completion log: `logs/crossref_single_terms_completion.log`

Resume selected streams with the project Python environment, for example:

```sh
Support/.venv/bin/python Support/aroma_atlas_2026-10-26/pipeline/supplement.py --query-names aroma,fragrance,perfume,odorant,olfactophore --pages-per-query 30 --max-requests 40
```

The request budget includes retries. A single synchronous worker waits at least 1.15 seconds between requests and respects HTTP retry guidance. No API key or paid operation was used. Three isolated ingestion regression tests pass, covering DOI reuse/metadata preservation, real provider-tagged DOI citation resolution, and future/unrelated aromatic-record rejection.


## Extended single-term discovery pass

A subsequent pass used 44 requests and returned 42866 candidate rows, adding 32659 previously unseen DOI candidates. 2081 of the new candidates passed the classifier loaded for that run; the final main-pipeline audit can change this count. No inclusion rule was relaxed merely to increase the count.

| Query | Retrieved | Reported matches | State |
|---|---:|---:|---|
| odor | 10000 | 14584 | bounded at ten pages |
| odour | 4276 | 4276 | exhausted |
| olfactory | 10000 | 38560 | bounded at ten pages |
| olfactometry | 754 | 754 | exhausted |
| flavour | 7836 | 7836 | exhausted |
| volatile | 10000 | 70828 | bounded at ten pages |

The `volatile` stream yielded very few accepted papers per thousand rows because most volatile-compound research falls outside perfume/aroma chemistry. Further broad paging is therefore a low-yield route. Details are in `crossref_extended_report.json` and `logs/crossref_extended_discovery.log`.

## Parent-title discovery continuation — 27 October 2026

The initial continuation advanced one page for each of twelve ranked parent-title streams (12 requests total). The table below reflects current cumulative checkpoints, including later versioned parent queries. Exact query/checkpoint states are also saved in `parent_expansion_coverage_2026-10-27.json`; title queries are candidate discovery, not a field census.

| Query | Retrieved rows | Provider matches | State |
|---|---:|---:|---|
| parent_amyl_salicylate_v5 | 1,000 | 7,827 | bounded; resumable |
| parent_anethole_v3 | 627 | 627 | exhausted |
| parent_anisaldehyde_v6 | 269 | 269 | exhausted |
| parent_anisyl_v5 | 326 | 326 | exhausted |
| parent_benzaldehyde_v3 | 4,967 | 4,967 | exhausted |
| parent_benzyl_acetate_v3 | 1,000 | 98,933 | bounded; resumable |
| parent_benzyl_alcohol_v4 | 1,000 | 247,291 | bounded; resumable |
| parent_benzyl_benzoate_v4 | 1,000 | 33,623 | bounded; resumable |
| parent_benzyl_salicylate_v3 | 1,000 | 32,253 | bounded; resumable |
| parent_benzylacetone_v6 | 17 | 17 | exhausted |
| parent_bisabolol_v2 | 389 | 389 | exhausted |
| parent_borneol_v3 | 782 | 782 | exhausted |
| parent_camphor_v2 | 3,538 | 3,538 | exhausted |
| parent_carvacrol_v2 | 2,723 | 2,723 | exhausted |
| parent_carvone_v3 | 1,025 | 1,025 | exhausted |
| parent_caryophyllene_v2 | 1,115 | 1,115 | exhausted |
| parent_cinnamaldehyde_v3 | 3,439 | 3,439 | exhausted |
| parent_cinnamyl_v5 | 1,205 | 1,205 | exhausted |
| parent_citral_v2 | 1,501 | 1,501 | exhausted |
| parent_citronellal_v3 | 513 | 513 | exhausted |
| parent_citronellol_v3 | 384 | 384 | exhausted |
| parent_citronellylacetate_v6 | 1,000 | 73,396 | bounded; resumable |
| parent_coumarin_v4 | 1,000 | 12,967 | bounded; resumable |
| parent_cuminaldehyde_v3 | 126 | 126 | exhausted |
| parent_cymene_v3 | 1,182 | 1,182 | exhausted |
| parent_decalactones_v5 | 204 | 204 | exhausted |
| parent_decanal_v6 | 79 | 79 | exhausted |
| parent_estragole_v3 | 202 | 202 | exhausted |
| parent_ethyl_butyrate_v4 | 1,000 | 72,502 | bounded; resumable |
| parent_ethyl_hexanoate_v4 | 1,000 | 64,647 | bounded; resumable |
| parent_ethylvanillin_v6 | 1,000 | 68,604 | bounded; resumable |
| parent_eucalyptol_v3 | 343 | 343 | exhausted |
| parent_eugenol_v2 | 4,858 | 4,858 | exhausted |
| parent_eugenyl_v5 | 58 | 58 | exhausted |
| parent_farnesol_v3 | 809 | 809 | exhausted |
| parent_fenchol_v3 | 52 | 52 | exhausted |
| parent_fenchone_v3 | 222 | 222 | exhausted |
| parent_galaxolide_v4 | 77 | 77 | exhausted |
| parent_geraniol_v2 | 1,232 | 1,232 | exhausted |
| parent_geranyl_v5 | 733 | 733 | exhausted |
| parent_hedione_v4 | 1,000 | 214,384 | bounded; resumable |
| parent_hexadecanolactone_v5 | 4 | 4 | exhausted |
| parent_hexylacetate_v6 | 1,000 | 76,073 | bounded; resumable |
| parent_hexylcinnamaldehyde_v5 | 5 | 5 | exhausted |
| parent_humulene_v3 | 285 | 285 | exhausted |
| parent_hydroxycitronellal_v5 | 43 | 43 | exhausted |
| parent_ionone_v3 | 813 | 813 | exhausted |
| parent_isoborneol_v3 | 141 | 141 | exhausted |
| parent_isoeugenol_v3 | 523 | 523 | exhausted |
| parent_lilial_v4 | 32 | 32 | exhausted |
| parent_limonene_v2 | 3,255 | 3,255 | exhausted |
| parent_linalool_v2 | 1,461 | 1,461 | exhausted |
| parent_linalyl_acetate_v3 | 1,000 | 73,425 | bounded; resumable |
| parent_menthol_v2 | 3,457 | 3,457 | exhausted |
| parent_methyl_anthranilate_v3 | 1,000 | 215,020 | bounded; resumable |
| parent_methyl_benzoate_v4 | 1,000 | 221,553 | bounded; resumable |
| parent_methyl_eugenol_v3 | 1,000 | 218,911 | bounded; resumable |
| parent_methyl_salicylate_v3 | 1,000 | 219,968 | bounded; resumable |
| parent_muscone_v7 | 302 | 302 | exhausted |
| parent_musk_ketone_v7 | 1,000 | 24,567 | bounded; resumable |
| parent_musk_xylene_v7 | 1,000 | 10,029 | bounded; resumable |
| parent_myrcene_v3 | 498 | 498 | exhausted |
| parent_nerolidol_v3 | 335 | 335 | exhausted |
| parent_nerylacetate_v6 | 1,000 | 73,361 | bounded; resumable |
| parent_nonalactone_v5 | 33 | 33 | exhausted |
| parent_nonanal_v6 | 103 | 103 | exhausted |
| parent_octanal_v6 | 97 | 97 | exhausted |
| parent_pentadecalactone_v7 | 101 | 101 | exhausted |
| parent_phenethyl_alcohol_v3 | 1,000 | 227,253 | bounded; resumable |
| parent_phenethylacetate_v6 | 1,000 | 75,804 | bounded; resumable |
| parent_phenylacetaldehyde_v6 | 224 | 224 | exhausted |
| parent_phenylacetate_v6 | 606 | 606 | exhausted |
| parent_piperonal_v6 | 164 | 164 | exhausted |
| parent_safrole_v3 | 330 | 330 | exhausted |
| parent_santalol_v3 | 178 | 178 | exhausted |
| parent_sclareol_v5 | 284 | 284 | exhausted |
| parent_terpinene_v5 | 213 | 213 | exhausted |
| parent_terpineol_v3 | 456 | 456 | exhausted |
| parent_terpinolene_v5 | 130 | 130 | exhausted |
| parent_thymol_v2 | 3,316 | 3,316 | exhausted |
| parent_tonalide_v4 | 44 | 44 | exhausted |
| parent_undecalactone_v5 | 18 | 18 | exhausted |
| parent_vanillin_v2 | 4,318 | 4,318 | exhausted |

The final acceptance count is the reconciled graph count above, not the sum of query hits or per-run provisional admissions. No account or paid access was used.

## Strict vocabulary and American flavor continuation, 28–30 October

Versioned fragrant, scent, olfactive, olfactometric and musk discovery streams
completed at their recorded SQLite checkpoints. They nominate candidates;
chemical-context rules, provider eligibility, frozen diagnostic exclusions,
secondary-abstract exclusions and exact identities determine final admission.
The American `flavor_american_v1` stream advanced from 10,000 to **26,392**
returned rows in **17** additional requests and is now exhausted at that
saved provider stream. Its new acceptances were provisional until rescreening.
The earlier parent table remains a historical snapshot: cinnamyl now completed
1,205 rows, and versioned v6/v7 parent-title streams have their own saved states.
Broad multiword acetate searches remain bounded with low marginal yield;
their provider hit totals do not indicate relevant field size. Consult SQLite
and dated logs for each stream, rather than summing overlapping query totals.
