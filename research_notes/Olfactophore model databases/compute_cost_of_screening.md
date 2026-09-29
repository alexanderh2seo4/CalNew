# Compute cost of evaluating novel molecules against olfactophore / pharmacophore models and related 3D methods

Scope note: almost no benchmark exists that is *specifically* olfactophore-flavoured. The
cost numbers below come from the generic cheminformatics / structure-based drug design
literature (the methods are identical — an olfactophore is just a pharmacophore fitted to
odorant SAR), and the *olfaction-specific* evidence is confined to the predictive-value
section. Every conversion from a published benchmark to "per molecule on 2026 hardware"
is my own arithmetic and is flagged **[my arithmetic]** or **[assumption]**.

Hardware-scaling assumption used throughout, stated once:
**[assumption, not sourced]** A 2026 Apple Silicon P-core (M4/M5 Max class) is ~3× the
single-thread throughput of the Intel Xeon E5-2630 v3 (Haswell, 2.4 GHz) used in the
CONFORGE benchmark, and ~1.5–2× a 2011-era Core i7-975 (Pharmer benchmark). I use 12
usable parallel cores for an M4 Max-class laptop (12 P-cores; E-cores add little for
FP-heavy cheminformatics). Treat every "per-molecule on a Mac" figure as ±2×.

---

## Q1. Conformer generation — the real cost floor for any 3D olfactophore test

### Takeaway
For a ligand-based olfactophore query, conformer generation dominates: the pharmacophore
match itself is microseconds, the 3D ensemble behind it is 0.1–6 seconds per molecule
(knowledge-based), minutes-to-hours (xTB/CREST), or hours-to-days (DFT). CONFORGE is
~60× faster than RDKit ETKDGv3 at equal-or-better accuracy on the same hardware, which
is the single largest practical lever in the whole funnel.

### Cited findings
- CONFORGE benchmark, Platinum Diverse dataset (2,859 molecules, max 50 conformers),
  hardware **Intel Xeon E5-2630 v3 (8 × 2.4 GHz), 64 GB DDR3, CentOS 8** — average time
  per molecule: CONFORGE systematic default **0.09 s**, CONFORGE systematic best
  **0.16 s**, iCon (Schrödinger ConfGen) fast **0.53 s** / best **0.65 s**, Conformator
  fast **3.58 s** / best **4.03 s**, **RDKit ETKDGv3 5.54–6.22 s**, Balloon GA **12.60 s**,
  Balloon DG **16.94 s** — [CONFORGE, JCIM 2023 (PMC10498443)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10498443/)
- Whole-dataset wall clock for the same 2,859 molecules: CONFORGE default **5 min 21 s**,
  CONFORGE best **8 min 56 s**, iCon fast **26 min 7 s**, Conformator fast **2 h 50 min** —
  [CONFORGE, JCIM 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10498443/)
- Accuracy at the same 50-conformer budget — % of experimental structures reproduced below
  0.5 Å RMSD: CONFORGE best **51.6%**, iCon fast **46.1%**, CONFORGE default **44.6%**,
  Conformator best **41.8%**, Balloon DG **32.4%**. Mean RMSD: CONFORGE best **0.67 Å**,
  Conformator best 0.68 Å, iCon best 0.70 Å, **RDKit ETKDGv3 0.71–0.74 Å**, Balloon GA
  0.99 Å — [CONFORGE, JCIM 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10498443/)
- Ensemble sizes actually produced: **29–39 conformers** per small drug-like molecule,
  **342** per macrocycle — [CONFORGE, JCIM 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10498443/)
- Macrocycles (Prime dataset), median time per molecule: iCon fast **24.91 s**,
  Conformator fast **111.53 s**, RDKit ETKDGv3 multi-fragment **178.30 s**, CONFORGE
  stochastic **426.73 s**; best mean ring-only RMSD CONFORGE stochastic 0.56 Å vs RDKit
  0.62 Å — [CONFORGE, JCIM 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10498443/)
- CONFORGE is shipped in CDPKit (LGPL) as the `confgen` CLI plus C++/Python API —
  [CDPKit confgen docs](https://cdpkit.org/applications/confgen.html)
- CONFORGE "clearly outperformed all other tested open-source conformer generators and
  performed at least equally well as the evaluated commercial generators in terms of both
  processing speed and accuracy" for small molecules —
  [CONFORGE, JCIM 2023 abstract](https://pubs.acs.org/doi/10.1021/acs.jcim.3c00563)
- Semiempirical GFN2-xTB conformational search on a flexible 65-atom organic molecule:
  **5–8 hours on 24 cores** — [TalTech HPC CREST guide](https://docs.hpc.taltech.ee/chemistry/crest.html)
- CREST on macrocyclic peptides, 14 cores: **2.3 h (4-mer), 5.8 h (5-mer), 13.9 h (6-mer)**
  average — [CREMP, arXiv 2305.08057](https://arxiv.org/pdf/2305.08057)
- 189 ps of xTB metadynamics on a 102-atom molecule: **24 h 48 min on one Xeon-P8 core**;
  ~31 min on 48 cores at perfect parallel efficiency —
  [azobenzene screening, arXiv 2207.11592](https://arxiv.org/pdf/2207.11592)
- ETKDG derives torsion preferences from CSD crystal structures and is "much more efficient
  than DFT, but at the cost of accuracy"; it also has non-zero embedding failure rates —
  [ETKDG small-rings/macrocycles paper, JCIM 2020](https://pubs.acs.org/doi/10.1021/acs.jcim.0c00025)

### Inferences (arithmetic)
- **[my arithmetic]** Per-core throughput from the CONFORGE table, Haswell baseline:
  CONFORGE default 1/0.09 = **11.1 mol/s/core**; RDKit ETKDGv3 1/5.5 = **0.18 mol/s/core**.
  Ratio ≈ **61×**.
- **[my arithmetic + assumption]** On an M4 Max-class laptop (3× per core, 12 cores):
  CONFORGE ≈ 11.1 × 3 × 12 ≈ **400 mol/s**; RDKit ETKDGv3 ≈ 0.18 × 3 × 12 ≈ **6.5 mol/s**.
  - 1,000 molecules: CONFORGE **~2.5 s**; RDKit **~2.6 min**
  - 100,000 molecules: CONFORGE **~4 min**; RDKit **~4.3 h**
  - 10,000,000 molecules: CONFORGE 10e6/400 = 25,000 s ≈ **7 h**; RDKit 10e6/6.5 =
    1.54e6 s ≈ **18 days** on one laptop → needs a cluster (e.g. 500 cores ≈ 9 h).
- **[my arithmetic]** Per-conformer cost: CONFORGE 0.09 s for ~34 conformers ≈ **2.6 ms
  per conformer**; RDKit 5.5 s for ≤50 ≈ **110 ms per conformer**. The 110 ms figure is
  high relative to the folklore "tens of ms" for bare ETKDG embedding — the CONFORGE
  protocol includes RMSD pruning and (for ETKDGv3 defaults) minimisation, so a stripped
  ETKDG-only run will be faster. Flagged as a possible apples-to-oranges comparison.
- **[my arithmetic]** A typical flexible odorant (muguet aldehyde, C12–C14, 4–6 rotatable
  bonds) sits at or below the Platinum-dataset average in flexibility, so 50–300
  conformers per odorant is achievable in **0.1–0.5 s (CONFORGE)** or **5–30 s (RDKit
  ETKDGv3 at 300 conformers)** per molecule on one core.
- **[my arithmetic]** xTB/CREST refinement is ~10^5× more expensive than ETKDG: 5–8 h ×
  24 cores = **120–190 core-hours per molecule** vs ~1.5e-3 core-hours for ETKDG. At 10k
  candidates that is 1.2–1.9 M core-hours — cluster-only, and only justified for a
  handful of molecules.

### Gaps
- **OMEGA (OpenEye) absolute timings were not recovered.** The CONFORGE paper states it
  matched commercial generators but the extracted table did not include an OMEGA row; I
  could not confirm OMEGA's seconds/molecule from a primary source.
- No source found for RDKit ETKDG throughput measured natively on Apple Silicon.
- No sourced per-molecule DFT conformer-optimisation timing; the "hours per molecule"
  figure in the brief is plausible but I found no citable benchmark in this pass.

---

## Q2. Pharmacophore matching / alignment and 3D shape overlay

### Takeaway
Pharmacophore *matching* against a pre-indexed database is effectively free per molecule
(Pharmer: ~10^5–10^6 conformers/s on 2009 hardware; Pharmit screens 10^8-conformer
libraries in seconds); the cost is entirely in (a) generating conformers for a *novel*
molecule and (b) the one-off index build, which runs into days for billion-conformer
libraries. Shape overlay is ~2–3 orders of magnitude more expensive per pair than
pharmacophore triangle matching but still ≥100 molecules/CPU-second.

### Cited findings
- Pharmer worst-case queries (query matching essentially the whole library), hardware
  **Intel Core i7-975 @ 3.33 GHz, 8 GB RAM, RAID-0 2 × 500 GB SATA-II 7200 rpm**:
  HSP90 library of **1,892,172 conformations** → **31.3 s total / 11.3 s compute**;
  FXIa library of **1,796,125 conformations** → **22.1 s total / 8.2 s compute** —
  [Pharmer, JCIM 2011 (PMC3124593)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3124593/)
- Same queries in MOE: **388.9 s total / 119.2 s compute** (HSP90) and **299.7 s / 110.5 s**
  (FXIa) — Pharmer "more than ten times faster"; at peak enrichment **38× faster than MOE
  for HSP90 and 24× for FXIa** — [Pharmer, JCIM 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3124593/)
- Pharmer index sizes: **34 GB (HSP90), 32 GB (FXIa)** for ~1.9M conformations —
  [Pharmer, JCIM 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3124593/)
- Pharmer "can search a library of hundreds of millions of conformations in just seconds"
  for precise queries — [Pharmer, JCIM 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3124593/)
- Pharmit hosted library scale: MolPort 7.3M compounds = **104,330,134 conformations
  occupying 2.5 TB**, of which the TripleData (triangle) index is **72%**; total hosted
  data **>28 TB** on **24 × 4 TB drives (JBOD)**; libraries include ZINC 13M, ChemSpace
  47M, PubChem 91M compounds —
  [Pharmit backend, JCIM 2021 (PMC8049614)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8049614/)
- Pharmit preprocessing "requires several days" for libraries such as PubChem with >1
  billion conformers; repeat queries get a **2–10× cache speedup**; typical queries take
  "a few seconds to a few minutes"; ~30,000 queries/year, 3,000+ users —
  [Pharmit backend, JCIM 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8049614/); query-time
  statement corroborated by [Pharmit help](https://pharmit.csb.pitt.edu/help.html)
- Align-it (formerly Pharao) models pharmacophore features as **Gaussian 3D volumes**
  rather than points/spheres, and scores+aligns pairs of small molecules; open source —
  [Pharao, J Mol Graph Model 2008](https://www.silicos-it.be/assets/papers/hdw-pharao-paper.pdf);
  [align-it repo](https://github.com/OliverBScott/align-it)
- ROCS: "able to process hundreds of molecules per CPU second"; FastROCS does "millions of
  compounds in seconds" on GPU — [OpenEye ROCS](https://www.eyesopen.com/rocs);
  [FastROCS](https://www.eyesopen.com/molecular-modeling-fastrocs)
- Reported industrial scale point: a Boehringer-Ingelheim 1-billion-compound ROCS search
  took **11 CPU-years (2 days on a 2,000-CPU cluster)**; the same search with FastROCS
  takes **<1 day on a 4-GPU cluster, or <30 min on AWS** —
  [FastROCS/NVIDIA slide deck](https://www.slideshare.net/CanOzdoruk/s3328-fast-rocs)
  *(vendor-sourced marketing figure — treat as an upper bound on achievable speed)*
- PAPER (open-source GPU Gaussian shape overlay) gives **1–2 orders of magnitude speedup
  over a reference CPU shape-overlay implementation and >1 order of magnitude over
  commercial ROCS** — [PAPER, J Comput Chem 2010](https://cs.stanford.edu/people/ihaque/papers/gpurocs.pdf)
- RDKit 2D pharmacophore fingerprints (Gobbi & Poppinger 1998 definition) use 8 feature
  types (HBA, HBD, basic, acidic, hydrophobic, halogen, aliphatic-ring attachment,
  aromatic-ring attachment); a 3D pharmacophore fingerprint can be built by feeding a 3D
  distance matrix into the same 2D machinery —
  [RDKit docs](http://www.rdkit.org/RDKit_Docs.2012_06_1.pdf);
  [Landrum, RDKit UGM 2012 fingerprints talk](https://www.rdkit.org/UGM/2012/Landrum_RDKit_UGM.Fingerprints.Final.pptx.pdf)
- Contra the "microseconds" assumption for Gobbi fingerprints: a user on rdkit-discuss
  reported `Gen2DFingerprint` running **>2 hours without completing** on a set of
  molecules — combinatorial explosion of feature triplets/quadruplets makes these
  fingerprints unusually slow for a 2D descriptor —
  [rdkit-discuss thread](https://www.mail-archive.com/rdkit-discuss@lists.sourceforge.net/msg10823.html)

### Inferences (arithmetic)
- **[my arithmetic]** Pharmer worst case: 1,892,172 conformers / 11.3 s compute ≈
  **167,000 conformers/s** on a single 2009 quad-core desktop; FXIa 1,796,125 / 8.2 ≈
  **219,000 conformers/s**. These are *worst-case* (query matches nearly everything);
  selective queries use the sub-linear triangle index and are far faster.
- **[my arithmetic + assumption]** Scaling to a 2026 workstation with NVMe (I/O was ~2/3
  of Pharmer's wall clock: 31.3 s total vs 11.3 s compute) plausibly gives **≥10^6
  conformers/s**, i.e. a 100M-conformer commercial library searched in **~100 s** —
  consistent with Pharmit's "seconds to a few minutes" claim.
- **[my arithmetic]** Per *novel* molecule, testing "does it fit the muguet olfactophore?"
  = conformers (~34 for a small odorant) × matching. At 167k conformers/s that is
  **~0.2 ms of matching**, i.e. **>99.9% of the cost is conformer generation**. This is
  the single most important cost fact for the report.
- **[my arithmetic]** Storage, not CPU, is the binding constraint for hosting your own
  olfactophore-searchable library: 2.5 TB / 104.3M conformers ≈ **24 kB per conformer**
  (index included), and 104.3M / 7.3M compounds ≈ **14.3 conformers per compound** as
  Pharmit's production setting. A 10M-molecule odorant-space library at 14 conf/mol ≈
  143M conformers ≈ **3.4 TB**.
- **[my arithmetic]** Shape overlay per molecule: at "hundreds of molecules per CPU
  second" (ROCS), 1k molecules ≈ 2–10 CPU-s, 100k ≈ 3–8 CPU-min, 10M ≈ 8–28 CPU-hours →
  trivially parallel, a laptop job at 1k–100k scale. On GPU (FastROCS/PAPER) 10M is
  minutes.
- **[inference]** Practical stack recommendation for a fully open Mac-runnable
  olfactophore pipeline: CDPKit/CONFORGE (conformers) → Pharmit/Pharmer indexing for
  large libraries, or Align-it for pairwise olfactophore fit of a handful of candidates,
  or RDKit Pharm3D `EmbedPharmacophore` for constrained embedding against a hand-built
  muguet/Calone feature set.

### Gaps
- **No absolute molecules/second figure for Align-it/Pharao** in any source found — the
  original paper reports alignment quality, not throughput. Same for **LigandScout**
  screening speed and **RDKit Pharm3D EmbedPharmacophore** timing; both are gaps.
- **ESPsim** and **RDKit O3A** timings: no benchmark found in this pass.
- Pharmit's per-second conformer throughput is nowhere stated numerically in its own
  papers; the 167k/s figure above is my derivation from the 2011 Pharmer paper on
  2009 hardware and should be presented as such.

---

## Q3. 3D-QSAR (CoMFA / CoMSIA / Open3DQSAR)

### Takeaway
I found **no citable benchmark numbers** for Open3DQSAR or CoMFA/CoMSIA per-molecule
compute cost in this research pass. On method grounds the cost is negligible per
molecule (grid-field evaluation + PLS projection) and the true cost is the alignment
step, which is the same shape/pharmacophore overlay cost as Q2.

### Cited findings
- (none recovered — see Gaps)

### Inferences
- **[inference, uncritically flagged]** A CoMFA/CoMSIA prediction for a new molecule is
  a steric/electrostatic field evaluation on a ~1,000–8,000-point grid followed by a dot
  product with PLS loadings: microseconds-to-milliseconds of arithmetic, dominated
  entirely by (a) conformer selection and (b) alignment to the training set. Budget the
  same 0.1–6 s/molecule as Q1 plus a shape overlay from Q2; the QSAR step itself should
  be treated as free.

### Gaps
- No primary-source timing for Open3DQSAR, SYBYL CoMFA, or any 3D-QSAR implementation.
  This should be presented in the report as "no benchmark located", not estimated as
  fact.

---

## Q4. Structure-based: docking into OR models, co-folding, MD, FEP

### Takeaway
Docking is the first genuinely expensive tier: **15–30 CPU-seconds per ligand** for
GNINA-class docking with CNN rescoring on 4 cores, dropping ~1–2 orders of magnitude on
GPU (Vina-GPU 2.x family). Co-folding (Boltz-2) is ~20–60 GPU-seconds per complex. MD of
a GPCR in a membrane runs at ~150–240 ns/day on one datacentre GPU, and FEP is ~10 GPU-
hours and ~$10+ of cloud per ligand — three to four orders of magnitude above docking.

### Cited findings — docking
- GNINA 1.3 benchmark: random 100-complex subset of PDBbind core set v2016, **GNINA
  limited to 4 CPU cores**. Time per complex: **Vina scoring ~15 s**, **fast CNN model
  16 s**, **1.3 Default Ensemble 23 s**, **1.0 Default Ensemble 30 s**, **1.0 Caffe
  implementation 129 s**. The fast model is only **~1.3 s slower than Vina scoring and
  <1 s slower on CPU than on GPU** —
  [GNINA 1.3, J Cheminform 2025 (PMC11874439)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11874439/)
- GNINA 1.3 accuracy: PoseBusters redocking top-1 ≤2 Å **67%** (1.3 ensemble), 69% (1.0),
  64% (fast); cross-docking top-1 **40%** (1.3), 37% (1.0), ~36% (fast); DUD-E virtual
  screening **median AUC 0.78** and **nEF1% 0.27** for 1.3 vs 0.75 / 0.25 for 1.0,
  improved on 68/102 targets —
  [GNINA 1.3, J Cheminform 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11874439/)
- Vina-GPU 2.0 achieves **65.6× average acceleration over original AutoDock Vina**, 1.4×
  over QuickVina 2 and 3.6× over QuickVina-W in virtual screening on kinase targets;
  QuickVina 2 alone is **20.39× faster than Vina** —
  [Vina-GPU 2.1, bioRxiv 2023](https://www.biorxiv.org/content/10.1101/2023.11.04.565429v1.full)
- Vina-GPU 2.1 over 2.0: **1.62× (Vina-GPU), 6.89× (QuickVina2-GPU), 3.56×
  (QuickVina-W-GPU)**; in screening, 2.91×/11.15×/4.23× on DrugBank (9,125 molecules) and
  1.44×/5.53×/4.60× on Selleck (5,148 molecules). Hardware: **i9-10900K + RTX 3090** and
  **i7-12700H + RTX 3060 Laptop** —
  [Vina-GPU 2.1, bioRxiv 2023](https://www.biorxiv.org/content/10.1101/2023.11.04.565429v1.full)
- DiffDock: "about 1–2 seconds to process one ligand on an A100" — [DiffDock, arXiv 2210.01776](https://arxiv.org/pdf/2210.01776).
  **Contradicted** by a later benchmark reporting DiffDock-L at **88.33 s for 5 samples on
  an NVIDIA 80 GB A100** (≈17.7 s/sample) —
  [LIT-PCBA docking benchmark, arXiv 2605.01681](https://arxiv.org/pdf/2605.01681).
  The discrepancy is most likely sample count + model size (DiffDock-L) + whether ESM
  embedding is amortised; flag both figures.
- Boltz-2 inference: reported variously as **~18 s on a single GPU** for FEP-class
  affinity — [drugdiscoverytrends on Boltz-2](https://www.drugdiscoverytrends.com/recursion%E2%80%91mit-boltz-2-tool-can-predicts-binding-affinity-in-about-20-seconds/);
  **27.8 s per complex on a single A6000** —
  [TerraBind, arXiv 2602.07735](https://arxiv.org/pdf/2602.07735); and **40–60 s per
  protein–ligand pair** in a production deployment guide —
  [Nebius Boltz-2 at scale](https://nebius.com/blog/posts/running-boltz-2-inference-at-scale).
  These are consistent once MSA/preprocessing and diffusion-sample count are accounted
  for; use **20–60 GPU-s per complex** as the honest range.

### Cited findings — MD and free energy
- GROMACS on a **membrane-protein benchmark of 80,289 atoms** (close to a GPCR in a
  lipid bilayer with water): **A100 241.2 ns/day, A40 238.8, RTX 3080 191.2,
  RTX 2080 Ti 169.3, V100 153.1**. Node config: 16 CPU cores per GPU on the A40/A100
  nodes, 8 cores per GPU for RTX 2080Ti/V100/RTX 3080; GROMACS 2021.x —
  [NHR@FAU GROMACS GPU benchmarks](https://hpc.fau.de/2022/02/10/gromacs-performance-on-different-gpu-types/)
- The standard GROMACS `benchMEM` system is **82k atoms**, a protein in a membrane
  surrounded by water; the MPI benchmark set spans 6k–12M atoms —
  [MPI-NAT GROMACS benchmark set](https://www.mpinat.mpg.de/grubmueller/bench)
- An RTX 4090 workstation gives GROMACS performance "comparable to the RTX 6000 Ada", and
  consumer GPUs with 8 OpenMP threads can match or surpass datacentre GPUs with 16
  threads on larger systems —
  [Exxact RTX 4090 GROMACS benchmark](https://www.exxactcorp.com/blog/Benchmark/GROMACS-Benchmark-NVIDIA-RTX-4090)
  *(vendor blog — directional, not peer-reviewed)*
- Relative binding free energy: Cresset estimates RBFE at **~10 hours per ligand** as of
  2025, consistent with AstraZeneca estimates; production protocols cost **single to tens
  of GPU-hours per perturbation edge**; "each computed binding affinity might cost **$10
  or more** in underlying cloud-compute costs" —
  [Rowan, How to predict binding affinity](https://www.rowansci.com/blog/how-to-predict-binding-affinity)
- Non-equilibrium switching as a cheaper alternative: **40 ligands in 2–3 h with FE-NES
  on Orion vs 24–36 h with FEP+** —
  [OpenEye RBFE](https://www.eyesopen.com/relative-binding-free-energy)
- OpenMM has no official Metal backend; a third-party Metal plugin exists for Apple GPUs
  on macOS Ventura+, and a native Metal platform is only a proposal, with FP64 absence
  cited as a concern — [OpenMM issue #5397](https://github.com/openmm/openmm/issues/5397);
  [openmm-metal](https://github.com/philipturner/openmm-metal)

### Inferences (arithmetic)
- **[my arithmetic]** GNINA 1.3 Default Ensemble at 23 s on 4 cores = **92 core-seconds
  per ligand**. On a 12-core M-series laptop at 3 concurrent 4-core jobs: 23/3 ≈
  **7.7 s/ligand wall clock** → 1,000 ligands ≈ **2.1 h**, 100,000 ≈ **9 days**,
  10M ≈ **2.4 years**. 100k+ is cluster-only.
  *(Caveat: GNINA's CNN scoring is CUDA-only; on Apple Silicon you get the CPU path, and
  I found no Apple-Silicon GNINA benchmark — treat this as an upper-bound estimate.)*
- **[my arithmetic]** GNINA fast model at 16 s × 4 cores = 64 core-s/ligand. A 128-core
  cluster node: 128/64 = **2 ligands/s** → 100k ligands ≈ **14 h on one node**;
  10M ≈ **58 node-days** ≈ 2 days on a 32-node allocation (e.g. LRZ CoolMUC/Linux Cluster).
- **[my arithmetic]** Vina-GPU 2.1 route: if plain Vina is ~15 s/ligand (GNINA's Vina
  scoring figure, 4 cores) and QuickVina2-GPU 2.1 is 20.39 × 65.6/1.4 … — the stacked
  speedup factors are not cleanly composable across papers. A defensible bound: Vina-GPU
  2.0 at 65.6× over Vina gives **~0.23 s/ligand-equivalent** on an RTX 3090.
  1k ligands ≈ **4 min**; 100k ≈ **6.4 h**; 10M ≈ **27 GPU-days** (≈ 1 day on 27 GPUs).
  Flag as a derived, not measured, number — **no source in this pass gave absolute
  seconds/ligand for any Vina-GPU variant**.
- **[my arithmetic]** MD: a 100 ns equilibrium run of one OR–odorant complex in a bilayer
  at 241 ns/day (A100) = **~10 h of GPU time**, ≈ 0.4 GPU-days. Ten candidate odorants ×
  3 replicas × 100 ns = 30 runs ≈ **12.5 GPU-days**, or ~1 day on 12 GPUs. This is the
  hard ceiling for "a few molecules", never a screening tier.
- **[my arithmetic]** FEP at ~10 GPU-h/ligand: 10 ligands = 100 GPU-h ≈ 4 GPU-days;
  100 ligands ≈ 6 GPU-weeks. At the quoted ~$10/affinity, 100 ligands ≈ **$1,000+**.
- **[inference]** OR model preparation cost is a *one-off per receptor*, not per molecule:
  ~400 human ORs × one AlphaFold2 prediction each. MSA search dominates and is CPU-bound;
  once the 400-model set exists (and it does — see Q5), the marginal cost of a new
  odorant is purely the docking cost × 400 receptors, i.e. **400 × 23 s ≈ 2.5 CPU-hours
  per odorant** for a full 409-dimensional GNINA docking-score vector **[my arithmetic]**.
  That single number is probably the most useful figure in this whole note for an
  olfaction application.

### Gaps
- No sourced absolute seconds/ligand for AutoDock-GPU, QuickVina, or any Vina-GPU version
  — every paper reports only acceleration ratios. This is a real hole; the report should
  say so rather than quote a derived number as measured.
- No AlphaFold3 / Chai-1 co-folding per-complex timing recovered.
- No OpenMM ns/day figure for a GPCR-in-membrane system on any specific GPU (the Metal
  plugin's published numbers top out at ~4,158 atoms, far below a membrane system).
- No sourced 2026 cloud GPU/CPU prices; **all cloud-cost statements below are marked
  assumption.**

---

## Q5. ML surrogates and the olfaction-specific predictive-value evidence

### Takeaway
GNN odour models (POM/OpenPOM) give human-panel-level odour-quality prediction at
essentially zero per-molecule cost, and are the only method in this list with a
*prospective* validation on novel odorants. Docking against OR models is by contrast
weak per-receptor (AUC ~0.67–0.68 for OR5K1, enrichment factors below 1) and only becomes
useful when aggregated into a multi-receptor score *vector*.

### Cited findings — ML surrogates
- The Principal Odor Map is a message-passing GNN mapping structure to 138 odour
  descriptors; on a **prospective validation set of 400 novel odorants** the model's odour
  profile "more closely matched the trained panel mean (n=15) than did the median
  panelist" — [POM, Science 2023](https://www.science.org/doi/10.1126/science.ade4401);
  [preprint PDF](https://www.biorxiv.org/content/10.1101/2022.09.01.504602.full.pdf)
- OpenPOM is the open reimplementation, integrated into DeepChem, trained on **4,983
  molecules** (GoodScents + Leffingwell PMP 2001) with **138 odour labels** —
  [DeepChem OpenPOM tutorial](https://github.com/deepchem/deepchem/blob/master/examples/tutorials/Predict_Multi_Label_Odor_Descriptors_using_OpenPOM.ipynb)
- Graph-transformer successors to POM exist as of 2026 —
  [GraphNOSE, arXiv 2609.05694](https://arxiv.org/html/2609.05694)

### Cited findings — predictive value of docking/pharmacophore for odour
- **M2OR** curates **75,050 bioassay experiments** covering **51,395 distinct OR–molecule
  pairs**, with receptor sequences and experimental detail — this is the ground-truth set
  any OR docking benchmark should be scored against —
  [M2OR, Nucleic Acids Res 2024](https://academic.oup.com/nar/article/52/D1/D1370/7327067)
- **OR5K1 modelling study**: ROC AUC in retrospective virtual screening was **0.67 for
  homology models and 0.68 for AlphaFold2 models**, with **enrichment factors in the top
  15% of only 0.11 and 0.24** respectively —
  [OR5K1 orthosteric site, bioRxiv 2022](https://www.biorxiv.org/content/10.1101/2022.06.01.494157v1.full).
  **An EF below 1 means the top-ranked fraction is *depleted* of actives relative to
  random** — this is the single most important caution in the whole note.
- **Structure-based odour-similarity study (2025)**: ~**400–409 human ORs** built with
  AlphaFold2, each odorant represented as a **409-dimensional docking-score vector**;
  odour similarity inferred by comparing vectors statistically, which "compensates for
  inaccuracies in individual docking poses and affinities"; the authors report the method
  enables *relative* prediction of odour similarity including for compounds outside the
  reference database —
  [ACS Omega 2025, 10.1021/acsomega.5c04324](https://pubs.acs.org/doi/10.1021/acsomega.5c04324)
  (full text 403-blocked; details from [PubMed record](https://pubmed.ncbi.nlm.nih.gov/40949280/)
  and search snippets — **quantitative accuracy numbers not recovered**)
- **Fully in silico OR–odorant protocol (2025)**: 217 molecules from M2OR, reduced by
  k-nearest-neighbour clustering to 78 representative molecules for docking; the pipeline
  "verified over 25 previously established odorant–OR relationships"; AlphaFold2 models
  with template selection from PDB; OR51E2 pocket estimated at 71.05 Å3 vs 433.11 Å3 for
  an OR52 holo structure —
  [ACS Omega 2025, 10.1021/acsomega.4c08181](https://pubs.acs.org/doi/10.1021/acsomega.4c08181)
  (full text 403-blocked; details from search snippets and
  [UH repository PDF](https://uhra.herts.ac.uk/id/eprint/25787/1/ao4c08181.pdf))
- **MORE-Q** is a published dataset of molecular olfactory-receptor docking (Sci Data
  2025) — [Nature Sci Data](https://www.nature.com/articles/s41597-025-04616-6.pdf)
  (paywalled/redirect; **compute details not recovered**)
- Experimental structural anchor: cryo-EM of active human **OR51E2 bound to propionate**
  shows odorant selectivity controlled by tight packing between odorant and receptor,
  and mutation of the pocket shifts the fatty-acid chain-length preference —
  [Billesbølle et al., bioRxiv 2022 / Nature](https://pmc.ncbi.nlm.nih.gov/articles/PMC10580732/)
- Ligand-based olfactophore evidence: the C/Si/Ge/Sn switch study on the Lilial/Bourgeonal
  muguet family argues for **shape-based recognition of odorants in vivo in the human
  nose**, with "odotopes" matching molecular surface shape + electrostatics — direct
  support for shape/pharmacophore methods in the muguet family specifically —
  [PMC5538716](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5538716/)
- Structure–odour work on muguet aldehydes (Nympheal and derivatives) and on
  aldehyde-free muguet odorants crossing into the marine/Calone space exists and is
  recent, but is synthesis/SAR, not computational validation —
  [Helv Chim Acta 2023](https://onlinelibrary.wiley.com/doi/10.1002/hlca.202300040);
  [Helv Chim Acta 2018, marine/muguet boundary](https://onlinelibrary.wiley.com/doi/abs/10.1002/hlca.201800048)
- Market weight of the target family: lily-of-the-valley odorants account for "over 20%
  of the total perfumery raw materials market" —
  [Perfumer & Flavorist, Muguet in Perfumery](https://img.perfumerflavorist.com/files/base/allured/all/document/2016/04/pf.8041.pdf)

### Inferences
- **[inference]** The OR5K1 numbers (AUC 0.67–0.68, EF@15% of 0.11–0.24) and the ACS
  Omega 2025 design choice (aggregate 409 docking scores rather than trust any one) point
  the same way: **single-receptor OR docking is near-useless as a ranker, and only the
  ensemble/vector representation carries signal.** Any cost model that budgets docking
  against one "the muguet receptor" is budgeting for a method that does not work; budget
  400 receptors per molecule instead (~2.5 CPU-h/odorant, per Q4).
- **[inference]** Cost–value ordering, cheapest first, with honest value labels:
  1. 2D fingerprint / GNN odour model (POM-class): ~**1 ms/molecule or less** on CPU,
     trivially millions/hour; *only method with prospective novel-odorant validation*.
  2. 2D pharmacophore fingerprint (Gobbi): nominally cheap but **empirically slow in
     RDKit** (see Q2); value as a coarse pre-filter only.
  3. Conformers + 3D pharmacophore/olfactophore match (CONFORGE + Pharmit/Align-it):
     **0.1–0.5 s/molecule**; interpretable, hypothesis-driven, directly answers "does it
     fit the muguet olfactophore"; validated only indirectly (shape-recognition evidence
     in the Lilial/Bourgeonal family).
  4. Shape overlay (ROCS/PAPER/shape-it): **~5–10 ms/molecule CPU**; good analogue
     retrieval, no mechanism.
  5. Docking × 400 OR models: **~2.5 CPU-h/molecule**; weak per-receptor (AUC ~0.68),
     usable as a vector.
  6. Co-folding (Boltz-2): **20–60 GPU-s per OR–odorant pair** → ×400 receptors = **2–7
     GPU-hours/odorant**; no published OR-specific validation found.
  7. MD: **~10 GPU-h per 100 ns per complex**; mechanism only, a handful of molecules.
  8. FEP: **~10 GPU-h and ~$10+/ligand per edge**; congeneric series only.
- **[my arithmetic, tiered funnel for 10,000 novel candidates]**
  - Tier 0, GNN odour model + property filters: 10k × ~1 ms ≈ **10 s**, laptop. Keep 2,000.
  - Tier 1, CONFORGE conformers + olfactophore fit: 2,000 × 0.09 s ≈ **3 min** single
    core, seconds on 12 cores; matching is free. Keep 300.
  - Tier 2, shape/electrostatic overlay against known muguet/Calone actives: 300 × ~10 ms
    ≈ **3 s**. Keep 300 (used for re-ranking, not cutting).
  - Tier 3, docking vs 409 AF2 OR models with GNINA fast model: 300 × 409 × 64 core-s ≈
    7.85e6 core-s ≈ **2,180 core-hours** ≈ **17 h on a 128-core node**, or ~2 h on 8
    nodes (LRZ Linux Cluster scale). This is the one tier that needs a cluster.
  - Tier 4, MD on the survivors: 10 complexes × 3 replicas × 100 ns at 241 ns/day ≈
    **12.5 GPU-days**.
  - Tier 5, FEP: only for a congeneric muguet series, ~10 h/ligand.
  - **Total**: everything through Tier 2 is a coffee break on an M-series MacBook;
    Tier 3 is ~2,200 core-hours; Tier 4 is ~12 GPU-days. The compute cliff is entirely
    between Tier 2 and Tier 3.
- **[assumption, not sourced — flag prominently in the report]** 2026 cloud cost
  sanity-check: at a nominal $0.02/vCPU-hour spot and $1.50/GPU-hour, Tier 3 ≈ 2,200 ×
  $0.02 ≈ **$45** and Tier 4 ≈ 12.5 × 24 × $1.50 ≈ **$450**. I found **no sourced 2026
  price list**; these are placeholders and must be labelled as such or dropped.
- **[inference] What runs well on a Mac**: CDPKit/CONFORGE, RDKit (ETKDG, O3A, Pharm3D,
  fingerprints), Align-it, shape-it, OpenPOM inference, AutoDock Vina / smina CPU docking
  at 1k–10k scale. **What does not**: anything CUDA-dependent — GNINA's CNN scoring,
  Vina-GPU, DiffDock, Boltz-2, AlphaFold, and GPU MD (OpenMM has only a third-party
  Metal plugin and no native Metal platform; GROMACS numbers above are all NVIDIA).

### Gaps
- **Quantitative accuracy of the ACS Omega 2025 docking-vector odour-similarity method
  was not recovered** (publisher 403 on both the ACS and ChemRxiv full texts). The report
  should cite the method and its design rationale but must not assert a correlation value.
- **No published validation of a muguet or musk olfactophore model with retrospective
  hit rates / enrichment.** I found the SAR and synthesis literature and the shape-
  recognition argument, but no paper reporting "our muguet pharmacophore gave X%
  precision on Y novel candidates". This is the biggest evidential hole for the brief.
- **Cong 2022** could not be uniquely identified from the search results; the OR
  structural-biology anchor I did find is Billesbølle et al. on OR51E2. If the brief
  means a specific Cong et al. paper, it needs a DOI.
- **No 2024–2026 systematic OR docking benchmark** (i.e. a DUD-E-style OR decoy set with
  reported AUC/EF across many receptors) was found. MORE-Q is the closest candidate but
  its contents were behind a redirect.
- No per-molecule cost figures for ML docking surrogates (e.g. DrugCLIP-class screening)
  beyond the observation that such methods exist —
  [DrugCLIP, arXiv 2310.06367](https://arxiv.org/pdf/2310.06367).
