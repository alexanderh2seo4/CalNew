# OpenAlex bounded discovery coverage

Public keyless API access was verified on 26–27 October 2026 (Europe/Berlin). The first list response showed a shared anonymous free daily budget of $0.10, $0.098 remaining after the probe, and a $0.001 cost per list call. No API key, account signup, prepaid balance, or paid operation was used.

The run fetched the first ten basic pages of each `title.search` family, 100 records/page. It reused the initial cached probe and made 29 further HTTP calls: 30 list calls total, $0.03 consumed from the free shared budget. The final response reported $0.069 remaining. The pipeline enforces a $0.06 reserve and stops without retrying a blocked/throttled response.

| Title family | Retrieved rows | Provider candidate total | Coverage |
|---|---:|---:|---|
| aroma | 1000 | 21388 | first ten pages; incomplete |
| fragrance | 1000 | 8096 | first ten pages; incomplete |
| odorant | 1000 | 6435 | first ten pages; incomplete |

These overlapping pages returned 3000 metadata rows, adding 680 previously unseen DOI/PMID candidates. 113 new records passed the source/date/type/title/abstract gates at ingestion; this is before final rescreening and deduplication.

Every retrieved work ID is retained in `openalex_ids`. The actual `referenced_works` lists contributed 91180 raw reference rows and 3156 accepted-endpoint provider-tagged citation edges at the snapshot. Unmatched work IDs remain unresolved. Reference presence is not inferred from title similarity. Metadata from existing DOI/PMID records is preserved.

Artifacts: `pipeline/openalex.py`, `research/openalex_harvest_report.json`, `logs/openalex_harvest.log`, and the `openalex_queries`, `openalex_ids`, `openalex_refs`, `openalex_budget_checks` SQLite tables. Four isolated regression tests pass for abstract reconstruction, DOI preservation/reference-ID resolution, conservative budget enforcement, and source/type/date gates.

This intentionally bounded retrieval is an additional coverage sample, not an exhaustive field census. Provider hit totals are candidates and must not be counted as included papers.


## Later checkpoint correction, 28 October 2026 audit

The preceding narrative describes the original first-ten-page pass. The actual
SQLite checkpoints subsequently advanced to **20 pages/2,000 rows per family**,
6,000 cumulative overlapping returned rows, with next_page=21 for aroma,
fragrance and odorant. All three remain incomplete. The later saved report is
`openalex_harvest_report.json` (27 October 09:40 UTC): 5,979 mapped work IDs,
162,947 raw work-reference rows and a last observed $0.07 shared free balance.
These historical request/row counts are not current accepted-paper counts or a
promise of today's shared quota. The collector still preserves its $0.06
reserve, persisted reset checks and stop-on-throttle behavior. Exact query
states were independently frozen in `recall_routes_oct28/sqlite_states.json`.


## Continuation through 28 October, reconciled 30 October

The actual checkpoints advanced to **30 pages / 3,000 rows per family**,
9,000 cumulative overlapping metadata rows, next_page=31 for aroma, fragrance
and odorant. All three streams remain bounded and incomplete. The final two
continuations used 20 and 10 requests; the last response retained $0.07 above
the $0.06 reserve. The report records 8,907 mapped work IDs and 227,783 raw
work-reference rows before final identity reconciliation; these are not final
accepted-paper or citation-pair counts. Logs:
`openalex-recall-continuation-2026-10-28.log` and
`openalex-odorant-continuation-2026-10-28.log`.
