# Aroma Research Atlas: methods and interpretation

This atlas collects public scholarly metadata and actual citation references for perfume, aroma chemicals, perceived odor intensity, molecular odor prediction, and aroma-related pharmacology. It is an automatically screened literature map, not a systematic review or a manually verified catalogue of every relevant paper. The current publication cutoff is **26 October 2026**; collection continued through 30 October. Indexing delay, incomplete abstracts, source coverage, language, and query vocabulary limit recall.

## Scope

The central chemistry/perception set includes fragrance ingredients, odorants, chemically characterized food aroma volatiles, intensity and detection-threshold measurements, olfactophores, molecular prediction methods, and odorant receptor–ligand work. Food studies qualify through aroma/volatile chemical evidence; taste-only nonvolatile constituents do not establish aroma relevance.

Additional scopes remain visible as separate categories:

- **Volatility and partitioning:** measured or calculated physical properties of explicitly named, source-verified parent odorants, including vapor pressure, phase equilibria and partition coefficients. These support odor delivery and availability; they are not necessarily direct sensory intensity measurements. Parent-as-solvent/cosolvent, unrelated solutes, substituted libraries, atmospheric oxidation products and bulk materials do not qualify through this route.
- **Aroma chemical pharmacology:** studies centrally investigating an unchanged parent compound with independently documented fragrance/flavor use. Registry identity and the source for ingredient membership are maintained in the research allowlists. Generic drug scaffolds, arbitrary derivatives, solvent-only applications, cigarette epidemiology, and structural polymer crosslinkers are not included merely because a parent name appears.
- **Characterized aroma oils:** an essential-oil title, abstract-level chemical profiling/composition evidence, an identified established aroma parent, and pharmacological activity or an aroma purpose are required. General herbal clinical studies without identified constituents, insect/pheromone applications, and packaging-oil films do not qualify through this extension. These are **mixture studies**: an oil assay does not establish the activity, dose, threshold, or mechanism of an individual constituent.

General smell disorders, clinical diagnostic smell testing, generic odor memory/neural development, ectopic receptor biomarkers without an aroma ligand, insect-only pheromone biology, general sensing hardware, environmental odor-removal engineering, and conceptual multisensory design without molecule research are outside the intended strict set. Screening rules are heuristic and can still make inclusion and exclusion errors.

Primary ingredient listings establish fragrance/flavor membership; they do not establish therapeutic efficacy, clinical safety, or approval for the application in a paper. See `research/NAMED_AROMA_PHARMACOLOGY.md` and the identity allowlist JSON files for source-specific evidence.

## Source-specific discovery and citation evidence

| Source | What was collected | Important interpretation |
|---|---|---|
| **Europe PMC** | Cursor-paginated query results, titles, abstracts when supplied, identifiers, publication types, and reference lists for accessible records | Candidate hit counts overlap between queries. MED, PMC, PPR, and AGR are distinct source identifiers. Biomedical/agricultural coverage is not comprehensive chemistry coverage. A completed request returning zero references does not establish that a paper has no bibliography. |
| **Crossref** | Ranked title-query DOI metadata and publisher-deposited DOI references | `query.title` is ranked candidate discovery, not an exact title restriction. Single-term streams and bounded multiword searches have different completion states. Deposits may omit abstracts or references. Missing fields are unknown. See `research/CROSSREF_COVERAGE.md` for actual per-query bounds. |
| **Semantic Scholar** | One successfully cached bulk metadata page and source identity mappings | Subsequent anonymous requests were persistently throttled. This source is incomplete. Bulk metadata does not contain nested references, and no reference coverage may be inferred from a metadata response. See `research/SEMANTIC_COVERAGE.md` for the actual attempted run. |
| **OpenAlex** | A bounded set of title-search metadata pages, inverted-index abstracts when supplied, work IDs, and actual `referenced_works` lists | Retrieval used the anonymous free daily allowance with a retained reserve. Basic pagination of three title-query families is deliberately bounded, not complete result streams. The initial pass retrieved ten pages per family; continuation passes and their exact checkpoints are recorded in the current report and logs. Work-ID references can remain unresolved. See `research/OPENALEX_COVERAGE.md` for exact coverage and budget evidence. |
| **Curated seeds** | A small collection of API-checked papers/databases with explicit research relevance | These improve discovery of important hubs; they do not establish complete coverage or manual review of the surrounding corpus. |

Discovery estimates, returned candidate rows, distinct stored candidates, accepted records, raw references, resolved citation edges, and connected papers are different quantities. The saved source reports describe retrieval at their respective run times; acceptance totals can change after final identity merging and rescreening. Source-specific citation counts cannot be assumed to describe the same citation universe.

Citation edges represent an actual supplied reference and point **from the citing paper to the cited paper**. Both endpoints must be accepted before an edge enters the displayed strict graph. DOI/PMID/source identifiers resolve references; title similarity, keyword overlap, and visual proximity must not manufacture citation edges. The same directed pair reported by several providers is one connection with multiple provenance records, rather than several independent citations. References to unresolved or rejected papers remain outside the visible strict graph.

Layout and category assignment are display aids. Graph communities describe the observed citation topology under incomplete coverage; categories come from screening rules. Neither is a validated scientific taxonomy. A disconnected paper or small node may have extensive citations outside the collected/resolved graph. Global provider citation totals and connections within this atlas should be labeled separately.

## Identity, reproducibility, and audits

The SQLite database retains metadata, query provenance, acceptance evidence, provider reference rows, and query/reference progress. Exact DOI and PMID matches support identity merging; preprint and journal versions with different identifiers may remain distinct. They should not be claimed to be distinct underlying experiments. Final rescreening must happen after collection writers stop, followed by resolution/export, so stale inclusions and edges are removed.

Rescreening applies the shared relevance rules and the Crossref, Semantic Scholar, and OpenAlex provider-specific eligibility functions, preserving their publication date/type/missing-abstract restrictions. Explicit curated seed overrides are reported separately from automatic-rule drift. A shared relevance classifier alone cannot replace provider eligibility checks. Frozen reports should retain the collection cutoff, source/query completion states, classifier version or file hash, allowlist version or file hash, identity merge record, and final counts.

Run the offline suite from the workspace:

```sh
Support/.venv/bin/python Support/aroma_atlas_2026-10-26/pipeline/test_atlas.py
```

Run a read-only consistent-snapshot database audit:

```sh
Support/.venv/bin/python Support/aroma_atlas_2026-10-26/pipeline/test_atlas.py \
  --audit-db Support/aroma_atlas_2026-10-26/data/atlas.sqlite --sample-limit 5
```

The scope challenge fixtures are synthetic regression cases, including four essential-oil cases and additional parent-identity, physical-property and derivative exclusions. The current offline unittest suite also check provider-specific title-only eligibility, type/date gates, identity reuse, real references and public-budget enforcement. These deliberately selected implementation cases are **not an independent precision/recall estimate**. Passing tests does not certify corpus relevance or completeness. An independent randomly selected, frozen, manually adjudicated sample would be needed for that purpose.

The subsequent `research/scope_audit.json` retains a reproducible frozen metadata sample: up to five accepted records per category, random seed 20261026, source metadata, classifier/allowlist hashes, and per-paper judgments by an **AI agent**. Those judgments use titles and available abstracts, not full-text verification or human adjudication. The stratified sample overrepresents small categories; its raw verdict proportions are not a population precision estimate. Retain the originally sampled records and findings even if later screening revisions remove them, rather than replacing failed cases with new accepted examples.

The audit reports duplicate identities, stale scope decisions against source-specific eligibility, deliberate curated overrides, dangling/self/out-of-scope edges, malformed evidence, query completion, and suspicious context patterns. Valid accepted tracks include aroma, prediction, and pharmacology; a separate pharmacology track does not require an aroma-track tag. Context warnings are inspection leads and may include legitimate records. Returned-reference totals and retained raw-reference rows can concern different providers and are not a retention-rate denominator pair.

## Known identity-screening limits

Exact-name regular expressions are not chemical structure recognition. The current guards reject common oxide/glucoside/derivative suffixes, some chemical-name prefixes, nearby absence statements, and previous-study/background mentions when identifying oil constituents. For example, identifying **linalool oxide** is not evidence of identifying unchanged **linalool**, and **vanillin glucoside** is not unchanged vanillin. An independent mention of GC–MS elsewhere in the abstract does not prove that a matched parent was measured in the oil. These guards do not cover every derivative or grammatical construction. The diagnostic sample found more difficult compound-name and substrate-only cases requiring further review. A source-verified parent allowlist does not resolve these identity questions by itself. Compound-level identities should ultimately be linked to registry identifiers and the actual composition statements rather than inferred solely from token matches.

The atlas does not imply full-text review, extraction of all quantitative measurements, verification of individual pharmacology findings, or causal interpretation of citations. Search expansion must preserve this declared scope. **A 50,000-paper target is not a reason to add unrelated papers or count unexamined references as relevant papers.** If source access or the available strict literature cannot support the target, report the observed accepted count and the unmet target plainly.


## Parent-title continuation on 27 October 2026

The adopted `research/named_aroma_allowlist_2026-10-27_v2.json` adds 16 documented parent identities with primary source links, exact synonyms and historical authorization cautions. Generic caryophyllene and unspecified santalol do not automatically identify the verified beta-caryophyllene and alpha-santalol parents. Historical flavor membership for estragole, methyl eugenol and safrole is not a current authorization or therapeutic endorsement. The original proposal and earlier allowlists remain preserved.

Versioned Europe PMC title routes include all established aliases and preserve the old completed query cursors. Twelve new bounded Crossref parent-title streams advance one page each. Actual query states are in `research/parent_expansion_coverage_2026-10-27.json`. Their overlapping hits cannot be added together or counted as relevant records.

The frozen parent expansion diagnostic in `research/parent_expansion_diagnostic_2026-10-27.json` reviewed 40 new admissions: 10 targeted failure examples and 30 seeded category-stratified records (25 in-scope, 14 out-of-scope, 1 uncertain). It exposed metal complexes, drug esters, analytical reagents, aerosol reaction products and pest-control leaks. The Crossref continuation diagnostic is retained separately. Explicit reviewed negatives/uncertain records are excluded alongside improved pattern guards. Both are AI title/abstract diagnostics, not human adjudication or population precision estimates. Preserve the original evidence, including failures, rather than resampling after corrections.

A targeted browser QA check of eleven 2027 issue-year records found first-publication dates within the frozen 2026 cutoff. Issue year and first online publication differ. The original metadata is retained; the header states the first-publication cutoff rather than implying that collection extended into 2027. Two incidental/generic scope failures noticed during that check are frozen separately in `research/display_year_diagnostic_2026-10-27.json` and excluded. This targeted check is not population validation.

The Crossref parent diagnostic retains a seeded sample of 25 records (23 in-scope, 2 uncertain) plus seven separately marked targeted negatives. These strata must remain distinguishable; their combined verdict fraction is not a corpus error rate.

## Further citation and identity discovery

`pipeline/neighbors.py` freezes bounded candidate snapshots from actual DOI references of accepted aroma/prediction papers. A title signal or repeated distinct citing origin prioritizes retrieval; it never grants inclusion. Each exact DOI metadata response passes the current Crossref date/type/title/abstract gates. Original request/response bodies, origins, query provenance and per-DOI attempts remain in SQLite. See `research/CITATION_NEIGHBOR_METHOD.md`.

Crossref-confirmed DOI redirects are followed only on the same HTTPS provider origin, through a bounded proof chain. Each response consumes ordinary request/time limits. Final metadata must match the proved canonical DOI. `pipeline/audit_aliases.py` independently checks every active DOI alias against retained redirects and final metadata. An identity alias does not itself make a citation: an actual supplied reference and two accepted endpoints remain necessary.

The versioned v4/v5 primary-source aroma-parent allowlists preserve CAS, exact aliases, isomer/mixture caveats and historical restrictions. Coumarin's drug-class ambiguity requires explicit unchanged-parent proof for its pharmacology route; generic coumarin scaffolds and anticoagulant classes do not qualify. Coumarin and benzyl alcohol require an explicit aroma purpose for production-only admission. Their solvent, catalyst/substrate, unrelated-protein formulation and other-solute roles are excluded. Sixteen further fragrance parents include separately identified lactone ring sizes and terpene isomers; hexadecanolactone is not Exaltolide.

Explicit volatile flavor chemistry titles can qualify without a deposited abstract when they name volatile flavor/flavour compounds and chemical/profile/composition evidence. Missing abstracts remain missing; no content is invented. Nonvolatile-only taste, quark/flavor terminology, bibliographic book reviews and herbicidal uses are excluded. This corrects a missing-abstract gate, not the declared scientific scope. A separate frozen flavor-title diagnostic records 32 seeded in-scope findings and two targeted failures; that fraction is not corpus precision.

The later-parent diagnostic retains 40 seeded records (33 in-scope, 4 out-of-scope, 3 uncertain) and 10 targeted leads (9 out-of-scope, 1 uncertain). The citation-neighbor diagnostic retains 40 seeded records (27 in-scope, 9 out-of-scope, 4 uncertain) and five targeted leads (4 out-of-scope, 1 uncertain). Environmental occurrence/removal/emission studies and generic neural gene regulation exposed by these samples were removed from the strict screen. Genuine central unchanged-parent toxicology is distinct from auxiliary pesticide-development safety screens. Original samples, raw metadata, timing, hashes and provisional review history are preserved.

`research/scope_readjudications_2026-10-27.json` separately records new primary evidence resolving the previously uncertain delta-decalactone production paper. Its original judgment remains frozen. A resolution clears only an uncertainty exclusion; it cannot clear an explicit negative or bypass current scope/provider eligibility. Historical Greek-letter typography and hyphens are normalized for screening only; original source metadata stays unchanged.

A finite `pipeline/grow_neighbors.py` job can advance repeated bounded DOI snapshots from a fully validated, unchanged policy/data snapshot. It enforces global request/time caps, stops on real provider failures and writes durable job/run reports. It does not publish or mark the research goal complete. After growth, the full rescreen/reference/export/reconciliation/audit sequence is required again.

Reference coverage is the union of actual returned lists across providers, not only the canonical record's original source. A nonempty deposited Crossref list remains available even when Europe PMC returns zero; provider citation totals and a metadata hasReferences flag do not prove a fetched list. Exact source-ID mappings follow identity merges. The exported processed fraction means at least one source-index response was processed, not that every provider's bibliography is complete. Errors and provider coverage are reported separately. PMID alias discovery initially supplies metadata only; additional native reference indexing is scheduled when its metadata becomes the canonical MED representation.

## PMID-neighbor review and coverage — 28 October 2026

A first exact PMID-neighbor pass retrieved 1,999 native metadata rows in 20
requests, initially adding 148 provisional accepted identities. These are
pre-final-screen results. The frozen diagnostic
`research/pmid_neighbor_scope_diagnostic_2026-10-28.json` retains 30 stratified
records: 7 in scope, 21 out of scope and 2 uncertain. This deliberately
stratified AI metadata sample is not a population precision estimate. It exposed
COVID smell recovery, generic olfactory cellular biology, gas hardware,
industrial biofiltration and social/clinical odor-cue studies. Context gates and
explicit diagnostic exclusions apply across the corpus before final counts;
the old sample and first-pass counts remain preserved. Genuine odor ligand/
mixture assays, chemical flavor profiles and established aroma parent
pharmacology retain their independent routes.

Cached native MED enrichment archives the full previous canonical representation
before a richer abstract or explicit excluded publication type changes it.
Exact IDs remain stable; no new paper is counted for a metadata promotion.
The original response and screening/run history remain unchanged. Actual MED
reference indexing follows separately when a primary source is promoted.
See `research/PMID_NEIGHBOR_METHOD.md` and the dated enrichment report.

## Strict recall correction and fragrance parents — 28 October 2026, evening

The completed finite DOI job made 4,000 requests and moved the provisional
record count from 48,306 to 48,677. Its last batches had low yield; it was not
restarted with the same priorities. The frozen growth diagnostic retains 40
seeded records (34 in scope, 4 outside, 2 uncertain) and six separate targeted
cases (1 in scope, 4 outside, 1 uncertain). The source metadata and negative
findings remain preserved, with explicit exclusions applied before export.

A separate read-only audit found 761 distinct cached rejected scent/fragrant/
olfactive/olfactometry leads. This is a nomination count, not an admission
estimate. The frozen 25-case metadata challenge includes genuine perfumery
synthesis, floral GC-MS profiles, human musk receptor/intensity studies and
GC-olfactometry methods, as well as clinical, insect, forensic, environmental
and drug-derivative negatives. See `research/recall_routes_oct28/REPORT.md`.

Scent/fragrant titles now require chemical composition/molecular evidence.
They do not acquire the broad exceptions given to explicit perfume/aroma
titles. Olfactive and olfactometry terminology, and relevant pyrazine/terpene
class vocabulary, are recognized across providers. Direct named aroma/musk
ligand assays can survive an incidental abstract mention of specific anosmia;
clinical smell-function diagnoses retain their exclusions. Actual GC-O chemical
profiles can coexist with an auxiliary electronic-nose method; generic gas
hardware and environmental biofilters remain outside scope. Pure SOA or
photooxidation-product vapor pressure does not inherit unchanged-parent scope.

Twenty additional discrete fragrance parent identities are source-verified in
allowlists v6/v7, with the original proposals preserved. Official IFRA
fragrance-ingredient listings establish fragrance membership; FEMA, government
and NIST identity sources supply additional evidence. New parent production
requires explicit aroma/flavor/fragrance intent. Arbitrary drug scaffolds,
complexes, derivatives, polymers, reagent/substrate roles and incidental
mentions do not inherit parent membership. Muscone's generic identity does not
prove an enantiopure sample. Exaltolide 106-02-5 differs from the already listed
hexadecanolactone 109-29-5. Bare commercial ambrettolide remains conditional;
7779-50-2 and 28645-51-4 must not be conflated. Historical musk-xylene membership
is distinct from current permission or safety.

All source-specific date/type/abstract gates, frozen publication cutoff and
real-reference-only graph construction remain in force. These corrections are
regression-tested against deliberately selected metadata; they do not certify
manual relevance or systematic-review completeness for the whole collection.


## Bibliographic identity and secondary abstracting records — 30 October 2026

A frozen, independently retained AGR/MED identity audit nominates 366 exact
cross-index pairs. The merge validator checks their complete title, author,
year, journal/volume and full available abstract evidence against recorded
hashes before merging; normalized math typography is documented explicitly.
One pair also has a record-specific publisher-deposited Crossref bridge. No
new title-similarity matches are admitted by this manifest. The original audit
and lean manifest are retained and hashed with the final screening policy.
The premerge snapshot had 170 pairs with both records accepted; that is an
excess-identity count, not a general corpus duplicate-rate estimate.

Source aliases, original metadata, query provenance, actual raw references and
reference checkpoints remain traceable after canonicalization. An AGR response
with no indexed references does not complete a distinct MED reference lookup.
Archived provider reference responses contribute to the coverage union only
through their actual preserved result, rather than inferred bibliography
presence. Later metadata enrichment does not rewrite the frozen merge proof.

Secondary ChemInform abstracting records are excluded by explicit title prefix,
ChemInform journal identity or DOI prefix 10.1002/chin. Wiley's official service
overview describes summaries derived from original publications. These entries
remain candidates with original metadata; they do not count as additional
research papers. Recovering an original article requires its own real source
identity and eligibility evidence. The frozen 290-entry pre-exclusion snapshot
and official service sources are in
`research/secondary_abstract_eligibility_2026-10-28.json`.

The American flavor title-query continuation finished its saved result stream
at 26,392 returned candidate rows, using 17 additional requests. This stream
completion does not establish field exhaustion. OpenAlex advanced to 30 pages
per title family (9,000 overlapping returned rows across aroma, fragrance and
odorant), with the last response retaining a shared free balance of $0.07.
The $0.06 reserve and stop-on-throttle rules remain in force. Final admission
counts follow the complete scope/identity/reference/export audit sequence.


The final American-flavor diagnostic freezes 30 uniformly seeded new-cohort
records (27 in scope, one outside, two uncertain) and five targeted negatives.
A separate full 537-record evidence frame retains the original response timing,
canonical/raw metadata and source provenance. Negative and uncertain examples
are held through the existing review-exclusion mechanism. This is an AI
metadata diagnostic, not full-text verification, human adjudication or an
estimate of whole-corpus precision. Original diagnostic findings remain frozen.


A separate targeted consumer/product diagnostic excludes 26 individually
adjudicated nonchemical product-acceptability records, retaining original raw
metadata and provenance. Eight ambiguous or chemical-positive leads were
preserved. The frozen nomination chain contains 288 accepted consumer/hedonic
or acceptability titles, 105 food contexts and 34 refined leads; these
purposefully selected groups do not estimate population error rates. No broad
consumer-word ban was applied: genuine chemical profiles and named-odorant
sensory studies remain eligible under their independent evidence routes.


A final bounded Principal Odor Map neighborhood diagnostic retains four exact
records and their real directed citation evidence. An NLP commercial-perfume
note recommender without molecule research and generic transistor gas coding
are excluded. Two broad conceptual substitution/electronic-nose reviews are
held uncertain pending evidence of central molecular aroma research. These
four targeted AI metadata verdicts do not estimate corpus precision and do not
ban genuine molecular odor models or chemically specific detection studies.
