# Semantic Scholar supplemental coverage and availability

Tested 26–27 October 2026 (Europe/Berlin), no API key/account/signup/paid operations.

The [official API reference](https://api.semanticscholar.org/api-docs/) supports Boolean title/abstract queries through `/graph/v1/paper/search/bulk`, up to 1,000 records per response with token pagination. It explicitly excludes nested citation/reference data. The runtime rejected requested nested reference fields with HTTP 400. The correct date filter is `publicationDateOrYear=1800-01-01:2026-10-26`; the `year` parameter uses a hyphenated year range rather than colon syntax.

A valid query for `"aroma" | "fragrance" | "odorant" | "olfactophore"` returned HTTP 200, an estimated 135,605 candidate matches, and 1,000 metadata rows. That first response was cached and ingested, preserving existing DOI/PMID metadata. It yielded 627 new candidate records, of which 56 passed the current title/abstract screening rules. The estimate is neither a retrieved-paper count nor a relevant-paper count.

The next token page returned HTTP 429 twice, separated by a 10-second wait. The pipeline stopped after those two responses, as required for persistent public API throttling. No additional probes or reference batch requests were made. No references were returned; no citation edges were inferred; metadata-only discoveries retain unknown/pending reference coverage.

Artifacts:

- `pipeline/semantic.py`: resumable, bounded no-key pipeline with DOI/PMID matching and provider-specific provenance.
- `research/semantic_harvest_report.json`: actual coverage counts and saved query state.
- `research/semantic_bulk_probe_valid.json`: cached successful response, including returned metadata and continuation token.
- `logs/semantic_harvest.log`: successful ingestion and subsequent throttling evidence.
- SQLite tables `semantic_queries`, `semantic_ids`, `semantic_refs`: explicit source identity and query/reference state.

The implemented optional `/paper/batch` stage would ingest actual provider reference lists and mark coverage only after receiving them. It did not execute in this run because discovery throttling ended the run. Three isolated regression tests pass: metadata-only coverage remains pending; actual DOI references resolve with their correct provider while preserving Europe PMC metadata; repeated throttling stops after exactly two responses.

This source has been attempted successfully for one page but cannot currently provide sustained anonymous bulk coverage. Its result stream remains incomplete.
