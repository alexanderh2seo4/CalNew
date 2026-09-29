# Open databases of olfactophore/pharmacophore models for odor families, and the open toolchain to build them

*Research current as of 28 September 2026. URL reachability was tested from a macOS shell on that date; codes noted below. "000" = connection failed from this test host and may reflect local network restriction rather than a dead service — treat those as unverified, not confirmed dead.*

---

## Q1. Do odor-specific resources (M2OR, OlfactionBase, ODORactor, OdorDB/ORDB, Pyrfume, GoodScents, Leffingwell, FlavorDB, AromaDb, HORDE, OdoriFy) contain pharmacophore/olfactophore models or 3D binding-site information? Any GitHub/Zenodo repos of olfactophore models?

### Takeaway

**No. There is no open (or closed) database of olfactophore models.** Every open olfaction database found is a 2D/activity resource — molecule ↔ odor-descriptor labels, or molecule ↔ receptor activity — with no 3D feature-point models and essentially no binding-site geometry. The single closest thing on the open internet is the `bin/olfactophore` command-line tool inside the GPL-3.0 **AROMA / primaryodors** repository, which *generates* olfactophores on demand from odorant sets rather than distributing a curated library of them.

### Cited Findings

- **M2OR** (the current reference OR–odorant activity database) holds 51,395 distinct OR–molecule pairs from 75,050 bioassay experiments, covering 1,246 unique OR protein sequences across 11 mammalian species and 768 molecules; the stored fields are receptor response (responsive/non-responsive), screening concentration or EC50, bioassay metadata (cell line, G-protein, assay, tags), stereochemistry and experimental procedure. **No 3D structures, docking data, binding sites or pharmacophores are included.** License CC-BY 4.0; code/data at GitHub — [M2OR, NAR Database Issue 2024 (PMC10767820)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10767820/); [github.com/chemosim-lab/M2OR](https://github.com/chemosim-lab/M2OR) (HTTP 200). The web front-end `https://m2or.chemsensim.fr/` returned HTTP 403 to automated fetches on 2026-09-28 (likely bot-blocking, not down).
- A later review (Oct 2025) cites M2OR as "51,483 unique pairs across 11 mammalian species and receptor variants", i.e. the database has grown slightly since the 2024 paper — [Nicoli et al., *Chemical Senses* 50, bjaf038 (2025)](https://academic.oup.com/chemse/article/doi/10.1093/chemse/bjaf038/8306567).
- **OlfactionBase** is a manually curated repository of 106 primary odors, 572 sub-odor types, 3,985 odorant molecules, 1,124 odorless compounds and 2,067 ORs — a descriptor/sequence resource, with no pharmacophore content described — [OlfactionBase, *NAR* 50:D678 (2022)](https://academic.oup.com/nar/article/50/D1/D678/6362078). Host `olfactionbase.amritaolfactionlab.com` did not respond from this test host (code 000; unverified).
- **ORDB / OdorDB (Yale SenseLab), HORDE (Weizmann) and ODORactor** are surveyed together as "on-line knowledge resources of olfactory receptor–odorant interactions" — sequence, gene and interaction resources, not structural/pharmacophore ones — [Database (Oxford) baw132 (2016)](https://academic.oup.com/database/article/doi/10.1093/database/baw132/2630523). On 2026-09-28 `senselab.med.yale.edu/OdorDB`, `senselab.med.yale.edu/ordb`, `genome.weizmann.ac.il/horde` and `mdl.shsmu.edu.cn/ODORactor` all failed to connect (code 000; unverified — but ODORactor has been reported unmaintained for years).
- **OdoriFy** (`odorify.ahujalab.iiitd.edu.in`) also failed to connect from this host (code 000; unverified). It is a deep-learning OR–odorant prediction server, not a pharmacophore store.
- **Pyrfume** is the broadest open olfaction archive: >40 odorant-linked datasets spanning human psychophysics, animal behaviour, imaging, physiology and pharmacology, with information on **more than 20,000 identified odorants**, including web-scraped **GoodScents (TGSC)** and **Leffingwell** perceptual compendia. Fetchable via the `pyrfume` Python/R packages or as GitHub zips. The authors explicitly note "licensing issues stand in the way of some datasets" — [Pyrfume, *Scientific Data* (2024)](https://www.nature.com/articles/s41597-024-04051-z); [pyrfume.org](https://pyrfume.org/) (200); [github.com/pyrfume/pyrfume-data](https://github.com/pyrfume/pyrfume-data) (200); [Zenodo record 13820408](https://zenodo.org/records/13820408). Pyrfume contains no 3D pharmacophore models.
- **AROMA (primaryodors)** — GPL-3.0, C++/Python/PHP — ships `bin/olfactophore`, described as "a tool for superimposing odorant molecules in space in order to identify the spatial and electrostatic features of collections of odorants, such as those with a common aroma note or the agonists of a given receptor." It also ships a `pdbs/` folder with homology/predicted models of roughly 400 olfactory receptors in **both active and inactive states**, an SDF odorant database with perceptual notes, receptor-prevalence data from Verbeurgt et al. (2014), and an automated docking pipeline (OpenBabel, RDKit, Modeller) — [github.com/primaryodors/aroma](https://github.com/primaryodors/aroma) (200); [primaryodors.org](https://www.primaryodors.org/) (200).
- A GitHub repository search for the term **"olfactophore" returns zero repositories** (GitHub search API, 2026-09-28). The AROMA tool is a file inside a repo, not a repo in its own right, and no Zenodo deposit of olfactophore models surfaced in any search.
- Published olfactophore models exist only as **figures in the fragrance-chemistry literature**, not as machine-readable files: e.g. a green/galbanum olfactophore for substituted hepta-1,6-dien-3-ones — [PubMed 12788363](https://pubmed.ncbi.nlm.nih.gov/12788363/); a three-dimensional sandalwood olfactophore whose spheres represent H-bond-acceptor and hydrophobic features — [figure record](https://www.researchgate.net/figure/a-three-dimensional-model-of-the-sandalwood-olfactophore-The-spheres-represent-the_fig1_291986200); and the older French "santalophore hypermotif" interaction model — [Tetrahedron/ScienceDirect 022352349090007P](https://www.sciencedirect.com/science/article/abs/pii/022352349090007P).

### Inferences

- The olfactophore concept is well established in fragrance chemistry (it is explicitly "the pharmacophore approach under a different name" for odor notes), but it was developed pre-genomically inside industrial perfumery houses (Firmenich, Givaudan, Symrise). That is the most likely reason no open repository exists: the models are trade secrets and/or were only ever published as journal figures.
- A researcher wanting muguet/marine/musk olfactophores today must **build them**, not download them. The two viable inputs are (a) ligand-based, from odor-family molecule sets (Q5), or (b) structure-based, from the handful of OR structures plus predicted models (Q3).

### Gaps

- Could not verify current live status of ORDB/OdorDB, HORDE, ODORactor, OlfactionBase and OdoriFy — all failed to connect from this host, which cannot distinguish "dead" from "blocked".
- FlavorDB / FlavorDB2 and AromaDb were not individually fetched in this pass; based on their published scope (flavor-molecule ↔ food/receptor association) they are 2D molecule/descriptor databases, but this was **not directly verified** here.
- No search was run against Zenodo's API specifically; the "no Zenodo olfactophore deposit" conclusion rests on web search only.

---

## Q2. Do general pharmacophore databases (PharmMapper/PharmTargetDB, Pharmit, ZINCPharmer, Pharmer, PharmaDB/Inte:Ligand, ChEMBL-derived sets) include olfactory receptors? Licenses.

### Takeaway

General-purpose pharmacophore databases are built from **druggable** targets (BindingDB, DrugBank, PDTD, TargetBank, PDB complexes) and there is no evidence any of them contain olfactory receptors. Pharmit/Pharmer are genuinely open-source and can *build* an OR pharmacophore from a user-supplied complex, but ship no OR content.

### Cited Findings

- **PharmMapper / PharmTargetDB**: "Over 7000 receptor-based pharmacophore models (covering 1627 drug target information, 459 of which are human protein targets) are stored and accessed by PharmMapper", annotated from **BindingDB, TargetBank, DrugBank and PDTD**; the server is open-access and free of charge — [PharmMapper, *NAR* 38:W609 (2010)](https://academic.oup.com/nar/article/38/suppl_2/W609/1095921); expanded in the [2017 update, *NAR* 45:W356](https://academic.oup.com/nar/article/45/W1/W356/3791213). Free to use ≠ open-source; the model set itself is not distributed under an open license. Host `www.lilab-ecust.cn/pharmmapper/` did not respond from this test host (code 000; unverified).
- **Pharmit** is "available under a dual BSD/GPL open-source license" and is designed for interactive structure-based pharmacophore search over large chemical libraries — [Pharmit (Sunseri & Koes)](https://www.researchgate.net/publication/301539748_Pharmit_Interactive_Exploration_of_Chemical_Space); [pharmit.csb.pitt.edu](https://pharmit.csb.pitt.edu/) (200).
- **ZINCPharmer** (`zincpharmer.csb.pitt.edu`) did not respond from this test host (code 000; unverified). It is the older Pharmer-based ZINC front-end, largely superseded by Pharmit.
- **Pharmer**: the canonical `github.com/dkoes/pharmer` path returns 404 (2026-09-28); a Python wrapper exists at [uibcdf/PyPharmer](https://github.com/uibcdf/PyPharmer) (no declared license).
- **Inte:Ligand's** pharmacophore collections ship with **LigandScout**, a commercial product; no open license. *(Commercial status is from general knowledge — not independently verified in this pass.)*

### Inferences

- ORs are almost certainly absent from PharmTargetDB: the source databases (DrugBank, BindingDB, PDTD) are drug-target-centric, ORs have essentially no approved drugs, and the first OR structure only appeared in 2023 — after the last PharmMapper update (2017).
- Consequence: **no general pharmacophore database can be mined for an odor-family model.** The general tools are useful only as engines applied to odor-specific data you supply.

### Gaps

- Did not directly query PharmMapper's target list for "olfactory" (server unreachable), so "ORs absent" is an inference, not a verified fact.
- "PharmacoDB" is a pharmacogenomics/cell-line resource, not a pharmacophore database — the name collision was noted but not investigated further.
- No ChEMBL-derived public pharmacophore set covering ORs was found; ChEMBL's OR coverage itself was not quantified here.

---

## Q3. Olfactory receptor structures enabling structure-based pharmacophores (cryo-EM, AlphaFold, GPCRdb). Which receptors map to muguet, marine/Calone, musk?

### Takeaway

The experimental OR structure set has grown from 1 (2023) to roughly a dozen mammalian entries by September 2026 — but almost all are **consensus/engineered receptors or class I (fatty-acid) receptors**, and none is a native human muguet, marine or musk receptor. Structure-based olfactophores for those specific families must therefore rest on AlphaFold/GPCRdb models, not experiment.

### Cited Findings — experimental structures (direct RCSB PDB query, 2026-09-28)

Entries whose title contains "olfactory receptor" / "odorant receptor" / consOR / Olfr, with initial release dates:

| PDB | Release | Content |
|---|---|---|
| 8F76 | 2023-03-22 | Human OR51E2 bound to **propionate**, miniGs399 (Billesbølle et al.) |
| 8J46 / 8W77 | 2023-12-20 | Human consensus OR **OR52c**, apo (bRIL and receptor-only) |
| 8HTI | 2023-12-20 | Human consensus **OR52c + octanoic acid** + G protein |
| 8UXY | 2024-10-30 | Consensus **consOR1 + L-menthol** + mini-Gs |
| 8UY0 | 2024-10-30 | Consensus **consOR2 + S-carvone** + mini-Gs |
| 8UYQ | 2024-10-30 | Consensus **consOR4 + 2-methylthiazoline** + mini-Gs |
| 8UXV | 2024-10-30 | Consensus **consOR51** + mini-Gs |
| 9LDW | 2026-01-28 | Consensus **consOR6 + α-hexyl cinnamaldehyde** + mini-Golf |
| 9LDV / 9LDX / 9LDZ | 2026-01-28 | consOR6 + mini-Golf / Gs |
| 9LE0 / 9LE1 / 9LE2 | 2026-01-28 | Consensus **bmOR6A2** + mini-Golf |
| 9WPM | 2026-01-28 | apo **consOR5**–Gs complex |
| 9LKB / 9LKD | 2026-01-21 | **Olfr110** + PL45 (unsaturated fatty-acid metabolite) + Gs |
| 9W45 | 2026-03-04 | **Mouse class II OR (Olfr412) + methyl-*trans*-cinnamate** + miniGs |
| 9WG4 | 2026-06-17 | Pocket-**engineered OR52cs**, active state |
| 7LIC / 7LID / 7LIG | 2021-08-11 | Insect MhOR5 (apo / **eugenol** / **DEET**) |
| 6C70 | 2018-08-22 | Insect **Orco** |
| 8Z9A / 8Z9Z | 2024-06-19 | Aphid ApisOR5–Orco ± **geranyl acetate** |
| 8V00 / 8V02 / 8V3C / 8V3D | 2024-06-19 | Mosquito **AaegOR10** ± o-cresol; **AgamOR28** ± 2,4,5-trimethylthiazole |
| 9VQO–9VQV | 2026-07 | *Drosophila*/*D. busckii* **OR67d–Orco** ± cVA, VUAA1 |
| 9WPE / 9WPF / 9WPG | 2026-08/09 | Aphid **ApisOR22–Orco + nepetalactone**, closed & open states |

Source: RCSB PDB search + data API, queried directly 2026-09-28 (`search.rcsb.org/rcsbsearch/v2/query`, `data.rcsb.org/rest/v1/core/entry/<ID>`).

- **9W45 is the single most relevant entry for muguet.** It is mouse **Olfr412, the ortholog of human OR1D2** (the bourgeonal / lily-of-the-valley receptor), bound to methyl-*trans*-cinnamate. Pocket residues: Y259(6x55), Y277(7x40), F207(5x47), L255(6x51), L199(5x39), L260(6x56), Y155(4x56), E180(45x51 in ECL2). The ligand's benzene ring packs against hydrophobic residues (van der Waals) while the ester oxygens form polar contacts with tyrosines — i.e. an explicit **aromatic + hydrophobic + H-bond-acceptor** arrangement, exactly a structure-based olfactophore in all but name. Published *Science Advances*, 27 March 2026; Gil, Choi & Choi — [PMC13025043](https://pmc.ncbi.nlm.nih.gov/articles/PMC13025043/).
- OR51E2/propionate (8F76) was the first OR cryo-EM structure and triggered the series — [Structural basis of odorant recognition by a human odorant receptor, PMC10580732](https://pmc.ncbi.nlm.nih.gov/articles/PMC10580732/).
- Human **OR52 family** mechanism paper (consensus design) — [*Nature Communications* 14 (2023)](https://www.nature.com/articles/s41467-023-43983-9).
- Class II OR **Olfr110** with PL45 and 12(S)-HEPE, revealing "an unusually large hydrophobic pocket" — [*Cell* (2025/26)](https://www.cell.com/cell/abstract/S0092-8674(25)01431-X).
- A review dated 30 Oct 2025 tabulates only **7 unique OR structures** plus 35+ TAAR structures; the PDB query above shows the mammalian count has roughly doubled since — [Nicoli et al., *Chemical Senses* bjaf038](https://academic.oup.com/chemse/article/doi/10.1093/chemse/bjaf038/8306567). Sources conflict on the total only because of date: a June 2026 preprint still cites five (OR51E2, consOR1/2/4/51) — [PMC13278317](https://pmc.ncbi.nlm.nih.gov/articles/PMC13278317/).

### Cited Findings — predicted models

- **GPCRdb 2025** added odorant receptors: "all ~400 human odorant receptors and their orthologs in major model organisms can now be studied across the various data and tool resources in GPCRdb", with state-specific structure models of all human GPCRs built with AlphaFold, RoseTTAFold and AlphaFold-Multistate, plus models of physiological ligand complexes — [GPCRdb in 2025, *NAR* 53:D425](https://academic.oup.com/nar/article/53/D1/D425/7903362); [gpcrdb.org](https://gpcrdb.org/) (200).
- The **AlphaFold Protein Structure Database** covers all annotated human proteins including the entire human OR repertoire — [alphafold.ebi.ac.uk](https://alphafold.ebi.ac.uk/) (200); context in [Nicoli et al. 2025](https://academic.oup.com/chemse/article/doi/10.1093/chemse/bjaf038/8306567).
- AlphaFold3 has been applied to ORs directly, including water-soluble QTY variants and an **OR1A2–octanoate** complex — [PMC11811853](https://pmc.ncbi.nlm.nih.gov/articles/PMC11811853/).
- AROMA ships ~400 OR PDB models in active *and* inactive states, which is a ready-made alternative to GPCRdb/AlphaFold downloads — [github.com/primaryodors/aroma](https://github.com/primaryodors/aroma).
- Caveat repeatedly stated: "~88% of ORs and most of TAARs remain orphans, lacking identified ligands", and ECL2 "could not be properly modelled" in AlphaFold predictions, with medium-to-low pLDDT confidence in extracellular regions — [Nicoli et al. 2025](https://academic.oup.com/chemse/article/doi/10.1093/chemse/bjaf038/8306567). ECL2 forms part of the OR binding cavity lid, so this directly degrades structure-based pharmacophore reliability.

### Cited Findings — odor family ↔ receptor mapping

- **Muguet / lily of the valley**: **OR1D2** is the bourgeonal receptor; bourgeonal activation of OR1D2 raises sperm calcium and drives chemotaxis, and OR1D2 was the first ectopic OR deorphanized — [bioRxiv 757880](https://www.biorxiv.org/content/10.1101/757880v1.full). A homology-model binding mode of bourgeonal in human OR1D2 has been published as a figure — [record](https://www.researchgate.net/figure/Binding-mode-of-bourgeonal-to-human-OR1D2-Bourgeonal-is-known-to-be-the-most-potent_fig15_280587080). Its mouse ortholog Olfr412 now has an experimental structure (9W45, above).
- **OR10J5** (mouse ortholog Olfr16) is reported as a receptor for floral muguet agonists — surfaced via a patent document, [US 11,921,105](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11921105). *Patent-sourced; treat as lower-confidence than a peer-reviewed deorphanization.*
- **Musk**: human **OR5AN1** and **OR1A1** are the characterized musk receptors; OR5AN1 responds at nanomolar concentrations to musk ketone and robustly to macrocyclic sulfoxides and fluorine-substituted macrocyclic ketones — [Block et al., *PNAS* (2018)](https://www.pnas.org/doi/10.1073/pnas.1713026115). Further musk-receptor claims appear in patents — [US 12,461,089](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12461089), [US 11,867,685](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11867685).
- **Marine / Calone**: Calone is 8-methyl-1,5-benzodioxepin-3-one, discovered at Pfizer in 1966, marine-ozonic with watermelon nuances — [Wikipedia: Calone](https://en.wikipedia.org/wiki/Calone); fragrance-chemistry context in [Hügel, *Chemistry & Biodiversity* 5 (2008)](https://onlinelibrary.wiley.com/doi/10.1002/cbdv.200890083). **No specific olfactory receptor for Calone or the marine/ozonic note has been identified in the published literature** as of this search.
- **Ambergris / sandalwood**: no deorphanized human receptor was found for either family in this pass.

### Inferences

- Structure-based olfactophores are realistic today only for: OR51E2 (short-chain acids), the OR52 class I family (medium-chain fatty acids), the consensus ORs (menthol, carvone, 2-methylthiazoline, α-hexyl cinnamaldehyde), and the OR1D2/Olfr412 aldehyde–ester pocket. **α-Hexyl cinnamaldehyde (consOR6, 9LDW) and methyl-trans-cinnamate (9W45) are the two structurally characterized ligands closest to the floral/muguet space** — 9W45 especially, given the OR1D2 orthology.
- Because consOR1/2/4/5/6/51 and OR52cs are **engineered consensus sequences**, a pharmacophore derived from them describes a family-average pocket, not any real human receptor — an important caveat for anyone screening against them.
- For musk, marine and ambergris the only tractable route is **ligand-based** (Q5) or docking into AlphaFold/GPCRdb models of OR5AN1 / OR1A1, with the ECL2 confidence caveat.

### Gaps

- The PDB title-based query will miss any OR entry whose title omits "olfactory"/"odorant"/consOR/Olfr; the table above should be treated as near-complete but not provably exhaustive.
- No experimental structure of OR5AN1, OR1A1, OR1D2 (human), OR2W1, OR10G4 or OR7D4 was found. OR7D4/androstenone and OR2W1 were not separately searched in depth.
- The **OR5K1** work (Nicoli et al.) is homology/binding-site modelling with mutagenesis, not an experimental structure — [bioRxiv 2022.06.01.494157](https://www.biorxiv.org/content/10.1101/2022.06.01.494157.full.pdf) / [PMC10091413](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10091413/). Whether it specifically concerns pyrazines was not re-verified here.
- Ambergris and sandalwood receptor identity: no source found; likely genuinely unknown.

---

## Q4. Open-source pharmacophore toolchain — what can derive a ligand-based olfactophore from e.g. 20 muguet odorants?

### Takeaway

The open toolchain is complete and mature: **RDKit + CDPKit** cover feature typing, conformer generation, ligand-based model derivation and screening; **Align-it** does pharmacophore-based flexible alignment of a molecule set; **Pharmit** does structure-based search; **PLIP/OpenPharmaco/PharmacoNet** derive receptor-based models from a complex. Nothing in the chain is odor-aware — you supply the molecules.

### Cited Findings

| Tool | What it does | License | URL / status |
|---|---|---|---|
| **RDKit** (`Chem.Pharm2D`, `Chem.Pharm3D`) | Feature definitions (HBA/HBD/hydrophobic/aromatic/charge), 2D pharmacophore fingerprints, 3D alignment to feature sets, embedding molecules into a pharmacophore | BSD-3 | [rdkit.Chem.Pharm3D.Pharmacophore docs](https://www.rdkit.org/docs/source/rdkit.Chem.Pharm3D.Pharmacophore.html); worked example in [rdkit/UGM_2016 Stiefl Ph4 notebook](https://github.com/rdkit/UGM_2016/blob/master/Notebooks/Stiefl_RDKitPh4FullPublication.ipynb) |
| **CDPKit / CDPL** | C++ toolkit with Python bindings; molecule **and pharmacophore** generation, pharmacophore fingerprints, alignment, screening | LGPL v2.1-or-later | [cdpkit.org](https://cdpkit.org/introduction.html) (200); [github.com/molinfo-vienna/CDPKit](https://github.com/molinfo-vienna/CDPKit) (200) |
| **Align-it** (ex-Silicos-it "Pharao") | Aligns molecules by their pharmacophores — the canonical way to superimpose a set of actives and extract the common feature arrangement | GPL-3.0 / LGPL-3.0 forks | Original Silicos-it repo is gone (404). Maintained forks: [OliverBScott/align-it](https://github.com/OliverBScott/align-it) (GPL-3.0), [leonard-lenny-lee/align-it](https://github.com/leonard-lenny-lee/align-it) (GPL-3.0), [UnixJunkie/align-it](https://github.com/UnixJunkie/align-it) (LGPL-3.0 backup of 1.0.4) |
| **Pharmit** | Interactive structure-based pharmacophore + shape search over large libraries | dual BSD/GPL | [pharmit.csb.pitt.edu](https://pharmit.csb.pitt.edu/) (200) |
| **OpenPharmacophore** | Python library for pharmacophoric points and pharmacophores; derives models from **ligand-based, ligand–receptor and receptor-based** routes, plus virtual screening | MIT | [uibcdf/OpenPharmacophore](https://github.com/uibcdf/OpenPharmacophore) (200); fork [Daniel-Ibarrola/OpenPharmacophore](https://github.com/Daniel-Ibarrola/OpenPharmacophore) |
| **OpenPharmaco** | Fully automated protein-based pharmacophore modelling + HTVS, GUI | MIT | [SeonghwanSeo/OpenPharmaco](https://github.com/SeonghwanSeo/OpenPharmaco) (200) |
| **PharmacoNet** | Deep-learning protein-based pharmacophore modelling via image instance segmentation + coarse-grained graph matching, for ultra-large-scale VS (*Chemical Science*) | see repo | [SeonghwanSeo/PharmacoNet](https://github.com/SeonghwanSeo/PharmacoNet) (200) |
| **PharMD** | Extracts pharmacophore models from MD trajectories of protein–ligand complexes, dedupes them, screens with multi-model scoring | see repo | [ci-lab-cz/pharmd](https://github.com/ci-lab-cz/pharmd) |
| **PMapper / PSearch** (ci-lab-cz) | 3D pharmacophore signatures & fingerprints; ligand-based model generation + VS | see repos | referenced via [CADD Vault: Pharmacophore](https://drugbud-suite.github.io/CADD_Vault/Pharmacophore/Pharmacophore/) |
| **PharmacoForge** | Diffusion model that generates pharmacophores conditioned on a protein pocket | see repo | [eflynn8/pharmacophore-diffusion](https://github.com/eflynn8/pharmacophore-diffusion) (found via GitHub API; the name "PharmacoForge" appears only in the repo description) |
| **PharmacoMatch** | Neural subgraph matching for efficient 3D pharmacophore screening | preprint | [arXiv 2409.06316](https://arxiv.org/pdf/2409.06316) |
| **pharmacophore-toolkit** | "Generate Simple Pharmacophore Models with RDKit" — thin convenience wrapper | see repo | [tlint101/pharmacophore-toolkit](https://github.com/tlint101/pharmacophore-toolkit) |
| **Apo2ph4** | Published workflow for receptor-based pharmacophore models from *apo* structures — relevant since most OR models are ligand-free | *JCIM* 2022 | [pubs.acs.org/doi/10.1021/acs.jcim.2c00814](https://pubs.acs.org/doi/10.1021/acs.jcim.2c00814) |

- **PharmaGist** (Tel Aviv webserver, ligand-based common-feature detection) could not be verified: `bioinfo3d.cs.tau.ac.il/PharmaGist/php.php` returned 404 on 2026-09-28.
- **LigandScout / MOE / Phase** remain commercial; not verified in this pass.

### Inferences

- **Recommended minimal recipe for a "muguet olfactophore"**: take the odor-family molecule set (Q5) → RDKit `EmbedMultipleConfs` for conformers → **Align-it** or CDPKit to superimpose and extract the common HBA / aromatic / hydrophobic arrangement → encode as an RDKit `Pharm3D.Pharmacophore` with distance bounds → screen a fragrance-chemical library with CDPKit or Pharmit. This is entirely BSD/LGPL/GPL and needs no commercial software.
- **Structure-based cross-check** is now possible for the muguet case specifically: run OpenPharmaco / PharmacoNet / PLIP on PDB **9W45** (Olfr412 + methyl-trans-cinnamate) to get a receptor-based feature map, and compare it against the ligand-based model. That combination did not exist before March 2026.
- No tool in this landscape has any olfaction-specific feature definition; standard medicinal-chemistry feature types (HBA, HBD, hydrophobic, aromatic, positive/negative ionizable) are what all published olfactophores use anyway, so this is not a blocker.

### Gaps

- PLIP was not separately verified in this pass (it is GPL-licensed protein–ligand interaction profiling; widely used, but no URL check run).
- "ELIXIR-A", "ShaPE" and "Open3DALIGN" from the brief did not surface in searches; Open3DALIGN is a real GPL tool but its current maintenance status was not confirmed.
- LigandScout free-academic-license availability was not checked.

---

## Q5. Curated odor-family molecule sets usable for ligand-based models — how many molecules per odor family?

### Takeaway

The **OpenPOM curated GS-LF dataset is the single best open starting point**, and it has enough molecules per family to build ligand-based olfactophores for muguet, musk, sandalwood and amber — but it has **no "marine", "watery" or "ambergris" label at all**, which makes the marine/Calone family the hardest of the requested set.

### Cited Findings

- Direct count from the dataset file `curated_GS_LF_merged_4983.csv` ([BioMachineLearning/openpom](https://github.com/BioMachineLearning/openpom), downloaded and counted 2026-09-28): **4,983 molecules × 138 odor labels** (140 columns = `nonStereoSMILES`, `descriptors`, + 138 binary labels). Per-label molecule counts relevant to this brief:

| Label | Molecules |
|---|---|
| **muguet** | **56** |
| lily | 71 |
| **musk** | **98** |
| **sandalwood** | **36** |
| amber | 101 |
| ozone | 39 |
| aldehydic | 144 |
| powdery | 167 |
| animal | 124 |
| melon | 132 |
| floral | 1,100 |
| woody | 679 |
| green | 1,446 |

  Labels **absent** from the 138-label vocabulary: `marine`, `watery`, `ambergris`. Top labels overall: fruity 1,902; green 1,446; sweet 1,429; floral 1,100; herbal 756; woody 679; fatty 598; fresh 533; waxy 488; spicy 464.
- The dataset provenance: "4,983 molecules annotated with 135 [reported elsewhere as 138] odour descriptors, curated by combining the GoodScents and Leffingwell PMP 2001 odour databases as distributed in the OpenPOM `curated_GS_LF_merged_4983` dataset" — [Foundation Models for Discovery and Exploration in Chemical Space, arXiv 2510.18900](https://arxiv.org/pdf/2510.18900). *(The 135 vs 138 discrepancy is a counting convention; the file itself has 138 label columns, verified directly.)*
- OpenPOM is reachable through DeepChem with a documented tutorial — [DeepChem: Predict Multi-Label Odor Descriptors using OpenPOM](https://deepchem.io/tutorials/predict-multi-label-odor-descriptors-using-openpom/); [notebook in deepchem repo](https://github.com/deepchem/deepchem/blob/master/examples/tutorials/Predict_Multi_Label_Odor_Descriptors_using_OpenPOM.ipynb).
- **Pyrfume** provides the underlying GoodScents and Leffingwell archives separately (>20,000 identified odorants across >40 datasets), fetchable by package or zip — [Pyrfume, *Scientific Data* (2024)](https://www.nature.com/articles/s41597-024-04051-z); [pyrfume-data/goodscents](https://github.com/pyrfume/pyrfume-data/tree/main/goodscents). Licensing on some component datasets is unresolved per the authors.
- Mixture-level and newer olfactory datasets exist for context: [chemcognition-lab/pom-mix](https://github.com/chemcognition-lab/pom-mix), [AROMMA (arXiv 2601.19561)](https://arxiv.org/pdf/2601.19561), [GraphNOSE (arXiv 2609.05694)](https://arxiv.org/html/2609.05694).
- AROMA/primaryodors ships its own SDF odorant database with perceptual notes (citrus, dairy, acrid, …), GPL-3.0 — [github.com/primaryodors/aroma](https://github.com/primaryodors/aroma).

### Inferences

- **56 muguet molecules, 98 musk and 36 sandalwood** are comfortably enough for a common-feature ligand-based olfactophore (classical published olfactophores used 10–30 actives). Pairing `muguet` with `lily` would give ~100+ candidate actives for the lily-of-the-valley family, at the cost of label noise.
- For **marine/Calone**, the open route is to build the set by hand: `ozone` (39) is the nearest proxy label in GS-LF, and `melon` (132) captures the watermelon facet, but neither is the marine note. Full GoodScents via Pyrfume (raw scraped descriptors, not the 138-label reduction) will contain "marine" and "aquatic" strings and is the better source.
- **Ambergris** must likewise be assembled from the `amber` label (101) plus manual curation; note that perfumery "amber" (labdanum/vanillin accord) and "ambergris"/ambrox are not the same thing, so the 101 is an over-count for the ambergris olfactophore.
- GS-LF labels are **binary perceptual descriptors from expert catalogues**, not receptor activities — a ligand-based olfactophore built from them models the *percept*, which is exactly what a classical olfactophore is, and is legitimately different from an OR-specific pharmacophore built from M2OR actives.

### Gaps

- The raw GoodScents/Leffingwell descriptor vocabularies in Pyrfume were not counted for "marine"/"aquatic"/"ambergris" occurrences — this would be a quick, high-value follow-up (`pyrfume.load_data('goodscents/behavior.csv')`).
- M2OR agonist counts per odor family were not computed (M2OR is receptor-indexed, not odor-descriptor-indexed, and the web front-end returned 403).
- Exact license terms on the OpenPOM curated CSV were not read; OpenPOM's own code license was not verified in this pass.

---

## Bottom line for the report writer

1. **There is no open database of olfactophore models — this can be stated definitively.** No odor database holds them, no general pharmacophore database covers ORs, and GitHub has zero repositories matching "olfactophore".
2. **The closest existing artifact** is the GPL-3.0 `bin/olfactophore` tool plus ~400 active/inactive OR models in [primaryodors/aroma](https://github.com/primaryodors/aroma).
3. **The closest structural data** is a small but rapidly growing PDB set (table in Q3), of which **9W45 (Olfr412/OR1D2 ortholog + methyl-trans-cinnamate, March 2026)** is the one genuinely relevant to the muguet family, plus GPCRdb's 2025 addition of all ~400 human ORs as state-specific AlphaFold models.
4. **The closest ligand data** is OpenPOM's GS-LF set: muguet 56, musk 98, sandalwood 36, amber 101 molecules — but no marine label.
5. **The toolchain to build your own is fully open**: RDKit + CDPKit + Align-it (ligand-based), Pharmit/OpenPharmaco/PharmacoNet (structure-based), all BSD/MIT/LGPL/GPL.
