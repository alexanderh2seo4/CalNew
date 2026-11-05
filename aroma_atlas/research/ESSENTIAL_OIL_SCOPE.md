# Essential-oil composition studies as aroma-chemical source literature

A defined composition subset is relevant to an aroma-chemical graph when it measures known aroma-active parent molecules. This should be a separate botanical aroma-source chemistry category, rather than silently being called intensity/prediction research. Undifferentiated herbal-medicine efficacy reports, generic essential-oil activity without chemical composition, and insect-only ecological studies do not become relevant merely because an essential oil is mentioned.

The primary [AromaDb paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC6099104/) describes a resource connecting aroma-molecule identity, fragrance character, essential-oil constituents and GC–MS data. The primary [EssOilDB paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC4273207/) documents experimentally reported essential-oil profiles linked to individual source papers, including chemical identity and abundance. These establish the link between oil composition and aroma-chemical source literature. They do not certify every essential-oil publication as perfume research.

Suggested inclusion rule:

1. The title centrally concerns composition, chemical characterization or a volatile profile of an essential oil.
2. The abstract names a parent aroma molecule from the source-backed identity allowlist.
3. The record explicitly reports GC–MS, GC/MS, gas chromatography–mass spectrometry or a suitable validated composition method; pure undifferentiated oil assays are insufficient.
4. Existing exclusions for insect-only context, arbitrary drug derivatives and unrelated materials remain in force.
5. The evidence field should state which measured parent identity and method made the paper eligible.

Exact Europe PMC URLs, query syntax and sample abstracts are in `essential_oil_profile_scope_counts.json`. Results through 26 October 2026:

| Candidate definition | Hits |
|---|---:|
| Essential oil in title + chemical composition/characterization/profile title phrase + GC–MS evidence | 1,375 |
| Above + one of twenty named aroma parent compounds | 657 |
| Above + explicit aroma/fragrance/perfume/odor/flavor text | 20 |
| Expanded singular/plural oils + title composition/characterization/profile term + GC–MS evidence | 4,063 |
| Expanded rule + one of twenty named aroma parent compounds | 2,067 |

Counts are candidates, not approved records, and overlap the current corpus. Some sample results are insect-only and should be rejected. The likely contribution is below 2,000 additional strict papers after deduplication and screening, not tens of thousands.

EssOilDB's original publication describes more than 123,000 compound/profile measurements sourced from roughly 1,520 citations. Those measurement rows must never be reported as 123,000 research papers. Molecular observations, paper nodes and citation edges are different quantities.
