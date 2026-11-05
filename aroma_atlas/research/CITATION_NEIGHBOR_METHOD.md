# Bounded citation-neighbor DOI discovery

Method version: `citation-neighbors-v1`. Literature cutoff: **2026-10-26**.
Implementation and API documentation checked on 2026-10-27. This method performs
automatic metadata screening; it is not manual or full-text verification. It
does not establish exhaustive citation or literature coverage.

## Candidate evidence and scope

`pipeline/neighbors.py` takes a fixed, per-run snapshot of actual `raw_refs` rows
whose citing paper is accepted and carries an `aroma` or `prediction` track.
Pharmacology-only records and rejected citing papers cannot nominate candidates.
Candidates require a syntactically plausible DOI that is not already present
in `papers`, whether accepted or rejected. DOI case and a supplied DOI resolver
prefix are normalized; suffix punctuation is not guessed or stripped.

A candidate is eligible if its supplied reference title passes the shared
title-only aroma/prediction classifier, **or** if at least two distinct accepted
core papers cite that DOI. The title is a retrieval priority signal, never the
retrieved record's title or proof of relevance. A repeated reference can be an
unrelated statistical method and still be rejected after retrieval. Multiple
providers reporting the same citing paper count once toward recurrence.

Title-signal candidates rank first, followed by descending distinct citing
papers and DOI for deterministic ties. The complete origin text is loaded only
for the bounded selected set; the unselected bibliography remains in `raw_refs`.
New references returned during a run can become candidates on a subsequent run,
but do not recursively expand the current run.

## Crossref API choice

The current official [Crossref filters documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/)
documents an exact DOI filter and comma-separated filters. It does not provide
an explicit current guarantee for OR-of-DOI batches. Crossref's official
[older REST API repository](https://github.com/Crossref/rest-api-doc) describes
OR semantics for repeated filters, but explicitly marks that documentation
deprecated after the Solr-to-Elasticsearch migration. The
[current API documentation](https://api.crossref.org/swagger-ui/index.html)
was also checked. This is insufficient evidence to depend on repeated DOI
filters as a current batching contract.

The implementation therefore uses **serial `GET /works/{encoded DOI}` requests**,
with the HTTP library's automatic redirects disabled. Crossref's
[current REST API tips](https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-for-using-the-crossref-rest-api/)
describe endpoint/filter selection and efficient retrieval. No title search,
fuzzy endpoint match, API key, account, or paid access is used. The full returned
metadata is retained rather than a reduced field projection, including actual
publisher-deposited references when supplied.

An HTTP 200 response must contain a successful Crossref envelope, a metadata
object, and the exact requested DOI after the same conservative normalization.
Malformed fields or a different DOI without a verified HTTP redirect are
retained as invalid retrieval evidence and are not ingested. HTTP 404 is a
terminal not-found result. The requested DOI is never replaced with a nearby
title match.

### Verified DOI endpoint redirects

Redirect policy: `same-origin-crossref-works-v1`. A live run on 2026-10-27 exposed
an HTTP 301 from `10.1111/j.1567-1364.2003.tb00138.x` to
`/works/10.1016/s1567-1356(02)00141-1`. Its original HTTP body, headers and run
record remain retained in SQLite; this is API endpoint evidence rather than a
title-based identity inference.

The collector explicitly handles HTTP 301, 302, 303, 307 and 308 only when
`Location` identifies a syntactically valid DOI at `/works/{DOI}` on the same
`https://api.crossref.org` origin. Root-relative paths or absolute same-origin
HTTPS URLs are allowed. External hosts, HTTP downgrade, user information,
arbitrary paths, query strings/fragments, traversal/control characters,
malformed DOIs, redirect loops, unknown redirect statuses and more than three
hops are invalid per-DOI retrievals. They do not create a provider-throttling
cooldown. Requests use reconstructed, encoded DOI endpoints after validation;
the supplied Location URL is never fetched directly.

Every redirect hop is a separate ordinary HTTP request, with the same serial
rate, timeout, elapsed-time and per-run request budgets. The database retains
every 301/200 (or other status) response separately under the original DOI,
with its actual requested target URL. Final metadata must exactly match the
last proven redirect target. Its screening evidence includes the full DOI
chain and preceding proof-attempt identifiers. Until that final response is
validated and ingested, no DOI alias is established. Verified metadata reuses
the existing canonical DOI identity; `source_alias` receives
`source='DOI', source_id=<original DOI>, paper=<canonical paper>` without
overwriting a conflicting alias. The original reference remains unchanged.
Accepted-endpoint resolution through that alias retains the reference's
original citation provider.

If a request budget ends partway through a verified chain, a later run resumes
its last proven target from the cached evidence. Original response/run rows are
not rewritten. This also recovers the original implementation's 301 stop. A
legacy one-hour cooldown is ignored only when that run's abnormal responses are
all HTTP 301, its last abnormal response proves a currently supported redirect,
and the original stop reason is the legacy unexpected-HTTP stop. Passive runs
that only inherited the identical stale cooldown may also be ignored. The
new run reports all ignored legacy evidence identifiers. Per-DOI retry time
is waived only for that same evidenced legacy 301 checkpoint. Actual 429,
server, network, or independent provider cooldowns remain effective, including
a legacy run with an earlier provider failure and a final 301.

## Screening, identity and citations

An exact response is screened with `supplement.classify_record`, preserving the
provider's publication-type, publication-date, aroma-context, missing-abstract,
and shared relevance gates. The cutoff is applied to retrieved metadata because
the exact DOI endpoint is not a date-filtered search. The collector refuses to
run if `atlas.CUTOFF` differs from `2026-10-26`; a future scope/version requires a
deliberate implementation/checkpoint decision.

`supplement.ingest` stores accepted and rejected metadata and reuses an existing
exact DOI identity, preserving enriched Europe PMC metadata. A rejected exact
record remains a rejected candidate; it does not add an accepted paper. Returned
references are retained through the existing ingestion path even for rejected
metadata, as elsewhere in this atlas. They are not counted as accepted papers.

`atlas.resolve` links only supplied identifier references with both endpoints
accepted, retaining their original provider label and direction. Similar titles,
shared keywords, recurrence, and layout proximity never create a citation edge.
An unresolved or rejected endpoint remains outside the accepted graph. This
stage does not run export or change the public/private website; the normal
rescreen/identity-resolution/export/audit sequence follows after collection
writers have stopped.

## Audit and checkpoint tables

The collector creates separate tables without altering the existing schema:

| Table | Retained evidence |
|---|---|
| `citation_neighbor_origins` | Requested DOI; actual citing paper and its DOI; provider/target identifier; original supplied DOI/title; citing paper's existing query provenance; first run |
| `citation_neighbor_checkpoint` | Per-DOI state, cumulative attempts, update time, retry time, error, ingested paper identity, last run |
| `citation_neighbor_attempts` | Each started request; request and response URLs; HTTP status; response headers and full body; outcome; screening evidence; exact ingestion counters; errors |
| `citation_neighbor_runs` | Run start/end, stop reason, provider cooldown, complete JSON report |

Every retrieved paper also receives `crossref:citation-neighbors-v1:<doi>` and
`citation-neighbor:<citing paper>|doi:<doi>` provenance through the existing
`provenance` table. Citation origins remain separate from the metadata provider:
retrieving a Europe PMC-supplied reference from Crossref does not relabel the
original citation as a Crossref citation.

Responses are cached before parsing/ingestion. A killed process can leave an
`in_progress` attempt; its DOI is eligible to resume within the cumulative
attempt ceiling if no paper has been ingested. An already ingested identity is
excluded from subsequent discovery, and the durable response remains available
for audit if interruption occurred before checkpoint finalization. No unverified
response is treated as an accepted paper merely because its checkpoint exists.

The report preserves selected DOI priorities, exact/new/reused/rejected/invalid
counts, all checkpoint state totals, request usage, stop reason, cutoff, and
SHA-256 hashes of the collector and both classifier/ingester modules. Full
responses and origin rows are in SQLite; a report is not a replacement for the
database. `accepted_metadata` means responses that passed the rules;
`accepted_new` is the ingester's actual newly accepted identity count. Neither
the candidate snapshot length nor raw-reference rows are an accepted count.

## Public budget and resumption

Defaults are 100 selected DOI candidates, 80 HTTP requests including retries,
at least 1.5 seconds between serial request starts, and a ten-minute elapsed
request budget. Hard CLI limits are 500 candidates, 200 requests, one hour, and
at least two distinct citers for recurrence without a title signal. A stricter
server-advertised request interval is respected. In-flight requests have
connect/read timeouts of 15/45 seconds, so elapsed time can exceed the soft run
budget by an in-flight request and local database processing.

At most three non-redirect request attempts plus at most three distinct verified
redirect hops are attempted per original DOI across all runs (at most six HTTP
requests; a DOI without redirects retains the three-request ceiling). Cached
proof permits resumption without spending another request on earlier hops.
Exact accepted,
rejected, malformed/mismatched, and not-found outcomes are terminal for this
version. Network failures and interrupted attempts can resume; the relevant
retry time and attempt ceiling remain in the checkpoint.

Two HTTP 429 responses stop the entire run. Three server failure responses also
stop the run. The collector honors numeric/date `Retry-After`, never shortens a
long wait, and saves a provider-wide cooldown before a later run can issue
requests. Persistent failures preserve at least a one-hour cooldown. A single
429 or transient server error may be retried within the same budgets after the
requested wait; waits longer than sixty seconds stop and resume later. Other
unexpected HTTP responses stop the run conservatively and preserve an hour
cooldown. No alternate endpoint/account/key is sought to evade a stop.

Run one collection writer at a time. From the atlas directory:

```sh
# Read-only preview: no network calls, schema changes, or checkpoint writes.
../.venv/bin/python pipeline/neighbors.py --plan-only --max-candidates 25

# Bounded exact-DOI pass after all other writers have stopped.
../.venv/bin/python pipeline/neighbors.py \
  --max-candidates 100 --max-requests 80 --max-seconds 600

# Offline fixtures only; each uses a temporary SQLite database.
../.venv/bin/python pipeline/test_neighbors.py
```

The default report is `research/citation_neighbor_report.json`; `--report PATH`
selects another report file. Repeating the bounded command resumes eligible
DOIs and preserves completed outcomes. There is no force-reset option. A
changed classifier, metadata-refresh study, retry ceiling, or DOI-alias policy
requires an explicit new version/review rather than silently reopening finished
rejections or changing the scope to meet the 50,000-paper target.

Twenty-one offline tests cover candidate scope and priority, true recurrence versus
provider duplicates, rejected citing papers, exact identity reuse, source/query
origins and real directed edges, raw response retention, rejected/invalid/not-found
retrievals, checkpoint resumption and attempt limits, persistent throttling,
long `Retry-After`, hard budgets, per-run snapshot behavior, canonical redirect
identity reuse, full proof retention, final-DOI mismatch, hop/rate/request bounds,
unsafe redirects, resumable chains and narrowly evidenced legacy cooldown
recovery with original records preserved. These are
implementation regressions, not an independent precision/recall assessment.
