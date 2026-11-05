# Bounded PMID citation-neighbor metadata lookup

Method version: `pmid-neighbors-v1`. Frozen literature cutoff: **2026-10-26**.
Implementation/API documentation checked on 2026-10-27. This is an automatically
screened follow-up of actual citations, not manual review, a keyword expansion,
or an exhaustive field census.

## Evidence and batch query

The official [Europe PMC Help](https://europepmc.org/help) identifies `EXT_ID`
plus `SRC:MED` as an exact publication lookup, documents uppercase Boolean
operators and parentheses, and identifies `FIRST_PDATE` as the first-publication
date field. The official [REST API documentation](https://europepmc.org/RestfulWebService)
describes the search module, JSON output and `resultType=core` metadata, including
abstracts. The [Europe PMC web-service reference](https://dev.europepmc.org/docs/EBI_Europe_PMC_Web_Service_Reference.pdf)
also defines the external-ID/source identity pair and inclusive publication-date
range syntax. Its first-publication field can include source-algorithm dates
when only a partial date is available; it is metadata evidence, not full-text
date verification.

The collector composes those documented operations into batches of up to 100
existing numeric cited endpoints:

```text
(EXT_ID:123 OR EXT_ID:456) AND SRC:MED AND FIRST_PDATE:[1800-01-01 TO 2026-10-26]
```

It sends a serial GET to the public Europe PMC REST `/search` endpoint with
`format=json`, `resultType=core`, `pageSize=<requested batch length>` and synonym
expansion disabled. IDs contain only exact positive decimal identifiers; titles
or DOI strings never supply a new PMID. There are no accounts, API keys or paid
operations.

## Candidate snapshot and priority

`pipeline/pmid_neighbors.py` reads actual `raw_refs` rows with target source
`MED` or `PMID`. The citing paper must currently be accepted and carry an
`aroma` or `prediction` track. Pharmacology-only/rejected citing papers cannot
nominate candidates. Existing paper PMIDs, existing native MED source IDs and
exact MED/PMID aliases with a present target paper are already known and skipped.
Invalid, zero-prefixed, nonnumeric, and embedded/free-text identifiers are not
repaired or inferred.

An eligible endpoint either has a supplied title passing the **current**
`neighbors.title_signal`, or is cited by at least two distinct accepted core
papers. Multiple providers for one citing paper count once. Title signals are
retrieval priorities, never substitutes for source metadata. A repeated methods
paper can be retrieved and then rejected. Ranking is deterministic: title signal
first, then descending distinct citers, then numeric PMID. Complete origin text
is loaded only for the bounded selected set; all other original references
remain in `raw_refs`.

The snapshot stays fixed within a run. No recursively discovered IDs, new query
terms, citation similarity or fabricated edges are introduced to increase the
paper count.

## Exact response and date validation

Before any row from a batch is ingested, every returned row must identify a
requested numeric ID with `source=MED`. A supplied `pmid` field must agree with
its MED `id`; duplicate IDs, foreign sources/IDs and incomplete/inconsistent
hit counts invalidate the entire response. Full responses and returned rows
remain auditable. A failed identity/coverage envelope stops the run; requested
PMIDs receive retryable checkpoints and are not counted as retrieved candidates
or missing records.

Each exact row must additionally satisfy first-publication eligibility. A
valid native `firstPublicationDate` must be from 1800-01-01 through 2026-10-26.
When no usable full first date exists, an explicit publication year from 1800
through **2025** supplies conservative known-past evidence. A 2026 year without
a usable date, a future date/year, or unavailable evidence does not establish
eligibility. Date-rejected rows are retained in the dedicated record audit and
checkpoint but never admitted to `papers`, because the general final rescreen
does not independently implement this stage's date gate.

A successful, internally consistent batch can return fewer IDs than requested.
Each unreturned ID receives `not_returned`, its exact batch request identity,
and an explicit unknown-availability reason. It adds no metadata candidate or
accepted paper. This is a terminal checkpoint for the frozen method version;
it means that this indexed batch did not return the record. It does **not**
establish that the PMID does not exist, that a bibliography is empty, or that
Europe PMC has complete coverage of the reference neighborhood. There is no
automatic unbounded single-ID fallback.

## Native screening and exact identity reuse

Date-eligible metadata uses `atlas.classify` and the same publication-type
exclusions as native `atlas.ingest` (patents, book reviews, retractions and
errata). The collector does not weaken aroma scope or borrow a supplied
reference title to pass the classifier. Newly stored accepted and rejected
candidates both go through `atlas.ingest`. A missing `pmid` field may be filled
only from the already verified exact numeric MED identity; a missing display
year may use the verified native first-publication date. The unchanged source
row remains separately retained in the record audit.

Before insertion, exact existing PMID/MED identity or exact normalized DOI can
reuse a canonical paper, including an independently proved DOI alias. It
registers `source_alias` for both `MED/<PMID>` and `PMID/<PMID>`. Conflicting or
dangling identities remain held. Two requested PMIDs returning the same exact
DOI can supply two metadata responses but only one publication identity.

A richer native MED abstract can replace a non-MED canonical representation;
an explicit excluded publication type can remove an earlier inclusion. Before
a change, the complete prior canonical row, raw payload and reference checkpoint
are archived immutably. The stable atlas paper ID and existing canonical DOI
remain intact; the unmodified native payload retains its own reported DOI.
No self DOI aliases or reverse aliases are manufactured. A richer existing
primary representation is retained otherwise. Current source/type/date/scope
rules and frozen diagnostic exclusions apply to promoted metadata. Changes in
acceptance are counted separately from genuinely new publication identities.

Exact aliases resolve actual original references, preserving their source and
direction. Old provider caches and raw reference rows remain available. This
metadata stage **does not import reference lists**. When a non-MED primary
becomes native MED, only its obsolete overall provider reference checkpoint is
cleared so the normal MED reference stage can perform an actual lookup. The
underlying deposited lists remain preserved and count toward provider-union
reference coverage.

`--enrich-cached` replays only complete, validated original MED batches with no
network calls or new identities. It preserves original request/record/run
history, appending enrichment events and prior-canonical archives. Context
hashes and diagnostic gates are frozen at each new run's start. The initial
27 October report predates this behavior; its original statements and results
are retained as historical evidence, not rewritten retroactively.

## Audit tables and counts

| Table | Retained evidence |
|---|---|
| `pmid_neighbor_origins` | Requested PMID, actual citing paper/DOI/PMID, original target source and ID, supplied DOI/title, citing paper's original query provenance, first run |
| `pmid_neighbor_checkpoint` | Per-PMID state, cumulative request attempts, retry time, error, exact ingested/reused paper, last request/run |
| `pmid_neighbor_requests` | Full requested ID batch, exact query/parameters/URL, HTTP response URL/status/headers/body, outcome and error |
| `pmid_neighbor_records` | Every returned source row, batch/ordinal, original source/ID, validation/screening evidence, outcome and canonical paper |
| `pmid_neighbor_runs` | Start/end, stop reason, provider cooldown and full JSON report |
| `pmid_neighbor_canonical_archive` | Immutable prior canonical row, raw response, reference checkpoint, reason and fingerprint |
| `pmid_neighbor_enrichments` | Separate replay/promotion decisions and acceptance changes linked to original source rows |

Responses are committed before metadata parsing/ingestion. Origins and existing
query provenance are retained alongside new paper provenance
`pmid-neighbors-v1:<PMID>` and
`pmid-neighbor:<citing paper>|pmid:<PMID>`. An interrupted request can resume
within its checkpoint attempt budget; existing exact identities prevent an
unnecessary replacement if metadata was committed before interruption.

The report separates actual HTTP requests; requested-ID occurrences including
retries; distinct requested PMIDs; all raw response rows; valid exact-batch
returned rows; exact retrieved candidates; accepted/rejected metadata; unknown
unreturned IDs; date/identity/field failures; new candidates; reused identities;
and **newly accepted provisional identities**. A raw or retrieved row is not an
accepted paper. Query hit counts, selected snapshot size and origin counts are
not admissions or field-coverage claims. Full response/origin details remain in
SQLite; the JSON report is a compact run summary.

## Public budgets, retries and CLI

Defaults are 100 PMIDs per batch, **20 HTTP requests per run**, at least one
second between serial request starts, and a ten-minute request-time budget.
Hard limits are 100 IDs per batch, 100 requests per run, 10,000 selected IDs,
and a one-hour time budget. Per-ID attempts are capped at three requests across
runs, including attempts in failed batches. A retry consumes an ordinary HTTP
request and a per-ID attempt for every requested PMID. In-flight requests use
15/45-second connect/read timeouts; a response/local processing can extend a
soft elapsed-time boundary.

Two HTTP 429 responses stop all subsequent batches. Three server-failure
responses also stop the run. Numeric/date `Retry-After` is honored without
shortening long waits; waits over sixty seconds are checkpointed for a later
run. Persistent throttling/server failures, network failures and unexpected
HTTP responses preserve a provider-wide cooldown of at least one hour where
applicable. No alternate endpoint/account/key is used to evade a stop. Completed
accepted/rejected/unknown checkpoints remain terminal for this method version.

Run only after other collection writers have stopped. From the atlas directory:

```sh
# Read-only snapshot; no network, schema changes, or checkpoint writes.
../.venv/bin/python pipeline/pmid_neighbors.py --plan-only --max-candidates 100

# Default bounded bulk pass: up to 20 requests of at most 100 PMIDs each.
../.venv/bin/python pipeline/pmid_neighbors.py --max-requests 20 --batch-size 100

# Reuse validated cached source metadata; no network or new identities.
../.venv/bin/python pipeline/pmid_neighbors.py --enrich-cached --max-candidates 10000

# Offline regression fixtures use only temporary SQLite databases.
../.venv/bin/python pipeline/test_pmid_neighbors.py
```

`--max-candidates`, `--min-citers`, `--interval`, `--max-seconds` and `--report`
provide additional bounded controls. The default report is
`research/pmid_neighbor_report.json`. Repeating the command resumes eligible
checkpoints; there is no force-reset option.

**Before any final count/export:** stop writers, run the normal exact-identity
merge/rescreen, restore the verified anchors, resolve citations, export and audit.
Counts from this stage remain provisional until that sequence finishes. No Site
or export is changed by this collector. All scope decisions remain automatic;
passing the current offline regressions is not an independent precision/recall
estimate or manual validation of the retrieved literature.
