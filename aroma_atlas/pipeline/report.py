#!/usr/bin/env python3
"""Regenerate descriptive reports from the reconciled export, without harvesting."""
import collections, datetime, json, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    graph = json.loads((ROOT / 'site/dist/graph.json').read_text())
    s, nodes = graph['stats'], graph['nodes']
    tracks = collections.Counter(t for n in nodes for t in n['tracks'])
    fmt = lambda x: f'{x:,}'
    date_label = datetime.date.fromisoformat(s['collectedAt'][:10]).strftime('%d %B %Y')
    text = f'''# Aroma Research Atlas — {date_label}

Private explorer and hosting details are excluded from this public export.

The reconciled export contains **{fmt(s['accepted'])} automatically included publication records** and **{fmt(s['edges'])} unique directed citation connections**, from {fmt(s['candidates'])} distinct retrieved candidates. The target of 50,000 in-scope records is **{'met numerically' if s['accepted'] >= 50000 else 'unmet'}**. These are publication records, not distinct experiments or manually verified papers. Discovery is checkpointed; completion and scheduling status are recorded in WORK_STATUS.md.

## Focal maps

- **Aroma and intensity:** {fmt(tracks['aroma'])} records. Aroma chemistry, volatile food aroma, intensity/thresholds, parent odorant production and relevant databases. The volatility/partitioning theme also contains physical-property calculations; it does not imply direct sensory intensity measurement.
- **Prediction and pharmacophores:** {fmt(tracks['prediction'])} records. Molecular odor prediction and olfactory models, overlapping the aroma map.
- **Separate pharmacology context:** {fmt(tracks['pharmacology'])} records. Unchanged parent aroma chemical pharmacology, fragrance safety and identified oil-mixture studies. Mixture effects do not establish constituent effects.

![Atlas overview](data/atlas-overview.png)

## Coverage and provenance

| Measure | Count |
|---|---:|
'''
    for label, key in [('Included publication records', 'accepted'), ('Unique directed citation pairs', 'edges'), ('Papers with a matched citation', 'connectedPapers'), ('Largest connected component', 'largestComponent'), ('Reference-indexing records processed', 'referenceListsProcessed'), ('Papers with nonempty indexed reference lists', 'referenceListsAvailable'), ('Raw reference rows attached to included records', 'rawReferencesAccepted'), ('Raw reference rows across all candidates', 'rawReferences')]:
        text += f"| {label} | {fmt(s[key])} |\n"
    text += f'''
Reference indexing is processed for {s['referenceCoverage']:.2%} of included records; {s['availableReferenceCoverage']:.2%} have a nonempty indexed list. Processed means at least one source response, with nonempty evidence combined across actual provider lists. A processed zero-result lookup does not establish absence of a bibliography. Limited Semantic Scholar records retain unknown availability after anonymous throttling.

Edges point from citing paper to cited paper. DOI, PMID or actual provider work IDs establish connections. Multiple provider observations count as one directed pair; the citation CSV retains provenance. Unresolved and rejected endpoints remain outside the visible graph.

## Themes

| Theme | Included records |
|---|---:|
'''
    for cat, count in sorted(s['categories'].items(), key=lambda x: -x[1]):
        text += f'| {cat} | {fmt(count)} |\n'
    text += '\n## Highly connected papers\n\nRanked by observed incoming plus outgoing citation connections within this atlas, rather than source-index citation totals.\n'
    for name, track in [('Aroma and intensity', 'aroma'), ('Prediction and pharmacophores', 'prediction')]:
        text += f'\n### {name}\n\n| Publication | Year | Atlas connections |\n|---|---:|---:|\n'
        for n in sorted((n for n in nodes if track in n['tracks']), key=lambda n: (-n['degree'], n['id']))[:10]:
            title = n['title'].replace('|', '\\|').replace('[', '').replace(']', '')
            text += f"| [{title}]({n['url']}) | {n['year']} | {fmt(n['degree'])} |\n"
    text += '''
## A software-paper neighborhood

Search the Principal Odor Map, DREAM challenge, Pyrfume or FlavorDB from the landmark shortcuts. Citation neighborhoods display all collected neighbors even if they fall outside the previous filter.

![Prediction-paper neighborhood](data/prediction-citation-neighborhood.png)

## Validation and limits

The full graph, metadata and edge shards, both CSVs and directed GEXF are reconciled against SQLite by `pipeline/validate_export.py`; mandatory integrity/scope audit failures prevent successful orchestration. Offline tests check representative scope errors, provider eligibility, exact identity reuse, real references and public-budget stops. Passing code and structural checks does not certify scientific relevance for every paper.

The original frozen AI diagnostic review (`research/scope_audit.json`: 50 stratified records, 32 in-scope, 12 out-of-scope, 6 uncertain) remains unchanged. The parent expansion diagnostic (`research/parent_expansion_diagnostic_2026-10-27.json`: 40 records, including 10 targeted failure examples) is also preserved. They use titles/available abstracts, not full-text or human adjudication. Selected failures and uncertain records are excluded; neither sample yields a corpus precision estimate. Additional Crossref completion, later-parent, flavor-title, DOI citation-neighbor and PMID-neighbor diagnostics are retained separately with frozen selection methods and original findings. These stratified/targeted AI samples are not population error-rate estimates. A dated primary-source readjudication can resolve an original uncertainty without overwriting it, and never overrides current provider or scope eligibility.

The additional parent allowlist records exact identities and primary source evidence. Historical flavor membership does not imply current authorization, safety or efficacy: estragole, methyl eugenol and safrole retain their source cautions. Derivatives, organometallic complexes, reagent-only/solvent-only use and pest-only studies do not qualify through parent membership. Coumarin drug-family ambiguity requires explicit parent identity evidence; benzyl-alcohol/coumarin production requires aroma purpose. Isomers and commercial-mixture caveats are retained. Versioned v5–v7 allowlists add source-verified lactone, terpene, alcohol, ester, aldehyde and musk identities, with exact isomer and unchanged-parent restrictions. Frozen full-bibliographic AGR/MED identity proofs remove verified cross-index duplicates; secondary ChemInform summaries are excluded as separate research publications. Known historical fragrance status is not a clinical or regulatory endorsement.

Source streams have different completion states. Europe PMC routes are cursor-paginated; some Crossref streams are exhausted while broader searches and new parent streams remain bounded. OpenAlex is limited by a conservative public budget reserve and Semantic Scholar by anonymous throttling. Provider hit estimates are not included counts. Absence from this atlas does not establish absence from the literature; no claim is made that fewer than 50,000 relevant papers exist. Some preprint/journal versions remain distinct.

Layout proximity is a navigational aid, not validated chemical similarity. The overview draws at most 30,000 actual citation lines; full collected neighborhoods and exports remain accessible. The atlas maps bibliographic references, without full-text quotation or potency extraction.

See [methods](pipeline/METHODOLOGY.md), [resume instructions](README.md), [statistics](data/stats.json), [export reconciliation](data/export_validation.json), [integrity audit](data/integrity_audit.json), and the source coverage reports in `research/`. The private Site deployment receipt is `data/publication.json`; the SQLite evidence/checkpoint store is `data/atlas.sqlite`.
'''
    (ROOT / 'REPORT.md').write_text(text)
    c = sqlite3.connect(f"file:{ROOT / 'data/atlas.sqlite'}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    queries = [dict(r) for r in c.execute("SELECT * FROM crossref_queries WHERE name LIKE 'parent_%' ORDER BY name")]
    epmc = [dict(r) for r in c.execute("SELECT name,hits,seen,complete FROM queries WHERE name LIKE 'parent_titles_v%' ORDER BY name")]
    c.close()
    coverage = {'exported_at': s['collectedAt'], 'cutoff': s['cutoff'], 'included_records': s['accepted'], 'candidate_records': s['candidates'], 'epmc_parent_query_states': epmc, 'crossref_parent_query_states': queries, 'interpretation': 'Provider result totals and overlapping returned rows are not accepted-paper counts. New queries retain versioned checkpoints; bounded streams are not exhausted.'}
    (ROOT / 'research/parent_expansion_coverage_2026-10-27.json').write_text(json.dumps(coverage, indent=2))
    rows = '\n'.join(f"| {q['name']} | {q['seen']:,} | {q['hits']:,} | {'exhausted' if q['complete'] else 'bounded; resumable'} |" for q in queries)
    appendix = '\n## Parent-title discovery continuation — 27 October 2026\n\nThe initial continuation advanced one page for each of twelve ranked parent-title streams (12 requests total). The table below reflects current cumulative checkpoints, including later versioned parent queries. Exact query/checkpoint states are also saved in `parent_expansion_coverage_2026-10-27.json`; title queries are candidate discovery, not a field census.\n\n| Query | Retrieved rows | Provider matches | State |\n|---|---:|---:|---|\n' + rows + '\n\nThe final acceptance count is the reconciled graph count above, not the sum of query hits or per-run provisional admissions. No account or paid access was used.\n'
    p = ROOT / 'research/CROSSREF_COVERAGE.md'
    previous=p.read_text()
    retained=previous[previous.index('\n## Strict vocabulary and American flavor continuation'): ] if '\n## Strict vocabulary and American flavor continuation' in previous else ''
    p.write_text(previous.split('\n## Parent-title discovery continuation — 27 October 2026')[0] + appendix + retained)
    print(json.dumps({'report': str(ROOT / 'REPORT.md'), 'included': s['accepted'], 'tracks': dict(tracks)}))


if __name__ == '__main__':
    main()
