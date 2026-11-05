# CALNEW

CALNEW is a molecular odour research project combining prediction software, receptor/pharmacophore research and experimental instrument designs.

**Status:** computational research and hardware designs. Reported retrospective results do not establish prospective human sensory performance. Receptor-to-perception transfer, learned mixture prediction and automatic formula-to-doser control remain research work.

## Start here

- [Anonymized research notes and next steps](docs/research-notes/README.md) — German summary of the late-October / early-November discussions, with no personal names, contacts or schedules.
- [Project architecture and performance](CALNEW%20Project%20Architecture%20and%20Performance.md) — system map, endpoint definitions, results and limitations.
- [Current model/data report](docs/NOSE-RESEARCH-2026-10-28.md), [methods and comparison limits](docs/NOSE-PARITY-AND-METHODS-REPORT.md), and [pipeline documentation](docs/PIPELINE.md).
- [Basic models](docs/BASIC-MODELS.md), [evidence acquisition](docs/DATA.md), and [architecture](docs/ARCHITECTURE.md).
- [Four-line ingredient doser](Auto%20doser/OVERVIEW.md) — parts workbook, wiring/tubing, sealing analysis and Blender concepts. Firmware and measured accuracy remain pending.
- [Five-output olfactometer](Olfactometer-Five-Output-Design.md) and [build notes](Olfactometer-Build.md).
- [Receptor/docking research](reports/AlphaFold%20Docking%20und%20Pharmakophore%20f%C3%BCr%20CALNEW.md), [ligand-based prototype](research_notes/olfactory_pharmacophore_2026-10-09/local_model/README.md), and [literature atlas code](aroma_atlas/README.md).
- [Public export scope and verification](docs/PUBLICATION.md).

## Install the research software

The Python project is at the repository root. Python 3.12 was used for the recorded runs; the package declares Python 3.11 or newer.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[models,pretrained,dev]'
.venv/bin/python -m calnew doctor
.venv/bin/python -m calnew --help
```

Core requirements and optional model packages are defined in [pyproject.toml](pyproject.toml). [requirements-lock.txt](requirements-lock.txt) records the previous environment; platform-specific packages can require different wheels. Research scripts retain their compute-host guards. On the authorized remote machine, set `CALNEW_COMPUTE_HOST` to that machine's actual hostname before using guarded scripts; the variable is unset by default. Configure an authorized compute environment before numerical experiments.

## Data and reproducibility

This public snapshot contains code, configuration, reviewed research reports, example outputs, hardware assets and selected lightweight benchmark evidence. It excludes raw/downloaded datasets, trained model files, credentials, correspondence, contact lists, calendars, company/legal documents and private hosting receipts.

Published `runs/` directories contain selected reports, metrics and protocol records. They are **not complete inference bundles**. Historical commands in the methods reports require the corresponding model/data artifacts or a newly reproduced run. Original artifact hashes identify historical calculations; public copies may have account paths and host identities removed.

Fetch and ingest data explicitly through the source register, checking each source's permissions. Processing a research-only source does not grant commercial rights. Preserve the reserved final holdouts and keep development results separate from final evaluation.

The new discussion notes are proposals, not evidence of an agreed collaboration or completed validation. Public literature citations retain their scholarly attribution.
