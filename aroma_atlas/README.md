# Aroma Research Atlas — code and methods

This directory contains reusable bibliographic collection, citation-resolution, scope-screening and audit code for the CALNEW literature atlas. The historical collection used a literature cutoff of 26 October 2026; later collection checkpoints retained that cutoff.

The public export includes the [methodology](pipeline/METHODOLOGY.md), pipeline tests, research methods and chemical scope allowlists. The local multi-gigabyte database, raw provider responses, full metadata/abstract exports, private explorer and hosting receipts are excluded. Historical counts in the accompanying report describe that local snapshot and cannot be checked against a database supplied here.

Install [requirements.txt](requirements.txt) in a suitable environment. Collection scripts create local data/checkpoints; use bounded public API requests and the documented rate-limit handling. Metadata and abstract rights vary by provider and publisher. Citation proximity is a navigation aid, not a validated molecular similarity or sensory measurement.

See [pipeline/METHODOLOGY.md](pipeline/METHODOLOGY.md) before starting a new collection. The public pipeline can be used to build a new local corpus; it does not resume the omitted private snapshot automatically.
