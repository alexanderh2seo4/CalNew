# Automated extraction pipeline for odor potency data (thresholds, OAVs, FD factors, intensities) — technology, accuracy, cost

Research date: 2026-09-26. 20 tool calls. Prices were checked in September 2026 where noted. Several sources are aggregators or vendor blogs; they are flagged. Numbers marked **(uncertain)** are my assumptions or unverified estimates.

---

## 1. PDF/XML parsing and table extraction tools (2026), benchmarks, and threshold-table handling

### Takeaway
MinerU 2.5 has the best published table-structure scores in the open-source VLM class (OmniDocBench table TEDS 88.2). Marker v2 is the fastest parser in throughput. Docling is barely present on standardized leaderboards. I found no benchmark that scores the features typical of threshold tables: footnote markers, units in headers, and superscript reference letters. Use publisher XML/JATS wherever it exists. For PDF-only papers, a VLM parser plus an LLM that also sees the table page image is the practical design.

### Cited Findings
- OmniDocBench (CVPR 2025) is the reference composite benchmark for document parsing. It scores text edit distance, table TEDS, formula CDM and reading order — [OmniDocBench GitHub](https://github.com/opendatalab/OmniDocBench); [Nanonets IDP leaderboard v1.5](https://benchmarking.nanonets.com/benchmarks/omnidocbench)
- MinerU2.5 (a decoupled VLM, 2025) reports text edit 0.047, formula CDM 88.46, **table TEDS 88.22, TEDS-S (structure only) 92.38**, and reading-order edit 0.044. It leads its cohort on every axis — [MinerU2.5 arXiv 2509.22186](https://arxiv.org/pdf/2509.22186); summarized in [Medium comparison 2026](https://adityamangal98.medium.com/docling-vs-marker-vs-mineru-the-ultimate-open-source-pdf-parser-benchmark-2026-which-is-best-a36ecbb6c6b1)
- "No public leaderboard cleanly ranks MinerU, Docling and Marker on the same suite." MinerU appears on every board, Marker on some, and Docling is essentially absent from the standardized public leaderboards — [Medium comparison 2026](https://adityamangal98.medium.com/docling-vs-marker-vs-mineru-the-ultimate-open-source-pdf-parser-benchmark-2026-which-is-best-a36ecbb6c6b1) (secondary blog source)
- Marker 2 (Datalab, July 2026) scores 76.0 on olmOCR-bench. It claims 5× MinerU's throughput. Docling scores 50.3% on the same bench at 2.1 pages/s — [Lumien AI news](https://lumienai.com/news/marker-2-vs-mineru-docling-liteparse-olmocr-bench-benchmark); [MarkTechPost 2026-07-24](https://www.marktechpost.com/2026/07/24/datalab-marker-v2-vs-mineru-docling-and-liteparse-benchmark-breakdown/). **Caveat:** Datalab, Marker's own developer, produced this comparison.
- Summary of the same sources: "for raw high-volume batch, Marker on a big GPU is hard to beat; for accuracy-per-dollar, MinerU2.5; for CPU-only or mixed-format ingestion, Docling or MinerU-pipeline" — [Spheron self-hosting guide 2026](https://www.spheron.network/blog/self-host-document-intelligence-docling-marker-mineru-rag-guide/)
- Newer research parsers (2026) such as coarse-to-fine VLM parsers and LingDT-VL-OCR report results on OmniDocBench, so the field is still moving quickly — [arXiv 2603.24326](https://arxiv.org/pdf/2603.24326); [arXiv 2603.11044](https://arxiv.org/pdf/2603.11044)

### Inferences
- **Source priority.** Order the inputs as follows:
  1. Publisher XML/JATS, via Elsevier/ACS/Wiley TDM APIs or PMC OA. Tables arrive already structured, with `<table-wrap-foot>` footnotes, which removes the table-recognition error.
  2. Born-digital PDF, parsed with MinerU2.5 or Marker.
  3. Scanned PDF, which needs the OCR/VLM path.

  Older J. Agric. Food Chem., Z. Lebensm. Unters. Forsch. and Eur. Food Res. Technol. papers from the 1980s–90s, where many classic threshold tables live, are likely scan-quality PDFs.
- **Hard cases in threshold tables.** Units often sit in a header row ("OT (µg/L water)") or in a footnote. Superscript letters (a, b, c) link values to the method or reference. Values can be ranges ("0.1–0.5"), inequalities ("<0.01"), or given in scientific notation. Cells often merge compound name and RI. TEDS measures structure and cell text, but a 0.88 TEDS can still hide a mis-attached superscript that changes meaning. The recommended mitigation is to give the extraction LLM **both** the parsed Markdown/HTML table **and** the rendered page image of that table, so it can resolve superscripts and footnotes visually.
- GROBID is still the best tool for header, reference and section segmentation. It helps pre-filtering and reference linking, but it does not extract table content well. This is from prior knowledge and was not re-verified in this session.

### Gaps
- I found no benchmark that isolates footnote/superscript linkage or unit-in-header handling. PubTabNet and FinTabNet TEDS scores for table-transformer, Camelot and pdfplumber were not re-verified in this session.
- Nougat, Unstructured, PyMuPDF, Camelot, pdfplumber and table-transformer have no 2026 OmniDocBench numbers in the sources I found.
- I did not find a published head-to-head of direct frontier-LLM vision on page images against MinerU or Marker for scientific tables. OmniDocBench has historically included general VLMs (GPT-4o, Gemini, Qwen-VL); check the current leaderboard.

---

## 2. Chemical entity recognition and name → structure resolution

### Takeaway
Use a cascade. First take the CAS number if the paper prints it. Then look up the name in PubChem or CIR, which covers trivial and flavor names ("furaneol", "sotolon", "β-damascenone", "rotundone"). OPSIN handles systematic IUPAC names at about 99.8% precision. Put an LLM normalization step in front of the resolvers to fix spelling, Greek letters and stereo descriptors. Stereochemistry and enantiomers need their own field and manual rules.

### Cited Findings
- OPSIN is an open-source Java IUPAC-name → structure parser. It reports **precision ≥99.8% and recall 98.7–99.2%** on general organic nomenclature — [OPSIN, JCIM 2011](https://pubs.acs.org/doi/abs/10.1021/ci100384d); [PubMed 21384929](https://pubmed.ncbi.nlm.nih.gov/21384929/)
- CIR (the NCI/CADD Chemical Identifier Resolver) works by database lookup. It is less systematic than OPSIN because it only resolves names in its database. Its advantage is that it can resolve **trivial names** that follow no systematic nomenclature — [CACTUS blog](https://cactus.nci.nih.gov/blog/?tag=iupac-name); [LibreTexts Cheminformatics OLCC 2.6](https://chem.libretexts.org/Courses/Intercollegiate_Courses/Cheminformatics_OLCC_(2019)/2._Representing_Small_Molecules_on_Computers/2.6:_Chemical_Resolvers_Molecular_Editors_and_Visualization)
- Recent multi-agent chemical-literature extraction systems convert textual identifiers (IUPAC and trivial names) to SMILES by querying **CIR and PubChem via their public APIs** — [Multi-agent chemical IE, arXiv 2507.20230](https://arxiv.org/pdf/2507.20230)
- ChemDataExtractor has been used to auto-generate chemical property databases from literature — [LibreTexts / search summary](https://chem.libretexts.org/Courses/Intercollegiate_Courses/Cheminformatics_OLCC_(2019)/2._Representing_Small_Molecules_on_Computers/2.6:_Chemical_Resolvers_Molecular_Editors_and_Visualization) (weak source; see Gaps)

### Inferences
- **Suggested resolution cascade:**
  1. CAS number printed in the table → PubChem `compound/xref/RN/…/cids`.
  2. Exact name → PubChem PUG REST `compound/name/{name}/cids`.
  3. CIR `/{name}/smiles`.
  4. OPSIN for IUPAC-like names.
  5. LLM-proposed synonym (e.g., "4-hydroxy-2,5-dimethyl-3(2H)-furanone" for "furaneol"; "3-hydroxy-4,5-dimethyl-2(5H)-furanone" for "sotolon"; "(–)-rotundone"), re-resolved and checked by molecular formula or InChIKey consensus between two resolvers.
  6. Anything left over goes to a human queue.
- **Stereochemistry.** Threshold papers routinely report enantiomer-specific values, e.g., (R)- vs (S)-linalool or the 2-methylbutanoate enantiomers. Keep a separate `stereo_descriptor` field copied verbatim. Resolve to a stereo-specific InChIKey only when the name carries R/S, E/Z, (+)/(–) or cis/trans. Otherwise map to the flat (connectivity) InChIKey layer and flag it as "stereo-unspecified". PubChem often maps a trivial name to the racemate or an unspecified-stereo CID. Do not merge enantiomer-specific thresholds into those.
- Greek-letter damascenones and ionones (β-damascenone, α-/β-ionone), and names with typographic primes or dashes, are a common source of failed lookups. Normalizing Unicode (β → beta, ′ → ') before lookup is cheap and high-yield. This is prior knowledge, not measured here.

### Gaps
- I found no published accuracy figure for PubChem or CIR resolution specifically on flavor/fragrance trivial names. A small in-house test (e.g., 200 names from a Leffingwell or VCF list) would take a few hours and would give the real figure.
- ChemDataExtractor 2.x, OSCAR4 and ChemNER 2024–2026 F1 numbers were not re-verified in this session.

---

## 3. LLM-based structured data extraction from chemistry/materials literature: accuracy, errors, validation

### Takeaway
Published LLM pipelines for numeric property extraction reach about **85–92% precision and recall** on well-defined single properties when they use verification prompts, as ChatExtract does with GPT-4. F1 drops to roughly **0.65–0.85** for older and cheaper models, or for properties with messy reporting (the polymer Tg example). Plan for 5–15% record-level error before validation. The errors that dominate are wrong compound↔value pairing, unit and medium mistakes, and hallucinated or missed values. Cross-model agreement plus rule checks plus human adjudication of disagreements is the pattern the 2024–2026 literature converges on.

### Cited Findings
- **ChatExtract (Polak & Morgan, Nat Commun 2024, 15:1569).** An engineered-prompt workflow on a conversational LLM. It finds sentences containing data, extracts the data, and then asks follow-up "are you sure / is this value for this material" questions. With GPT-4 it reached **90.8% precision / 87.7% recall on bulk modulus** and **91.6% precision / 83.6% recall on critical cooling rates**. The follow-up questions "largely overcome known issues with LLMs providing factually inaccurate responses" — [Nat Commun](https://www.nature.com/articles/s41467-024-45914-8); [arXiv 2303.05352](https://arxiv.org/abs/2303.05352)
- **Polymer literature, Gupta et al., Communications Materials 2024.** They extracted **>1 million polymer-property records from 681,000 full-text articles**, covering 24 properties and >106,000 unique polymers. They used GPT-3.5 and LlaMa 2 together with the MaterialsBERT NER model. **F1: GPT-3.5 0.67 vs MaterialsBERT 0.63 for Tg; 0.85 vs 0.66 for bandgap.** They also discuss cost-optimization methods and in-context few-shot learning. The data is public at polymerscholar.org — [Commun Mater 2024](https://www.nature.com/articles/s43246-024-00708-9); [ADS abstract](https://ui.adsabs.harvard.edu/abs/2024CoMat...5..269G/abstract); [code: Ramprasad-Group/PromptDataExtraction](https://github.com/Ramprasad-Group/PromptDataExtraction)
- **Dagdelen et al. (Nat Commun 2024), "Structured information extraction from scientific text with LLMs".** They fine-tuned GPT-3 on **about 500 prompt/completion pairs**. Tasks were dopant–host linking, MOF cataloguing, and general chemistry/phase/morphology/application extraction. Output was JSON records — [arXiv 2212.05238](https://arxiv.org/abs/2212.05238). Per-task F1 values were not in the abstract I could access; see Gaps.
- **Self-prompting and cross-model consensus (arXiv 2608.19025, Aug 2026).** Experts specify the evidence standard, models cross-check repeated extractions, and researchers resolve disputed cases. LLM-authored prompts were "almost as effective as expert-written prompts". LLMs "can struggle with interpreting scientific context and nuance", autonomous agents "either missed or hallucinated references", and a human-in-the-loop is still required — [arXiv 2608.19025](https://arxiv.org/pdf/2608.19025)
- An evaluation study of LLM extraction of experimental materials data exists — [arXiv 2401.11052](https://arxiv.org/pdf/2401.11052). I did not fetch its numbers.
- Agentic extraction for other domains in 2026, e.g., targeted protein degradation databases — [arXiv 2605.11221](https://arxiv.org/pdf/2605.11221); alloy data — [arXiv 2602.04602](https://arxiv.org/html/2602.04602); concrete — [arXiv 2604.22938](https://arxiv.org/pdf/2604.22938). This confirms that the pattern is routine by 2026.

### Inferences
- **Error types expected for odor thresholds.** This is my taxonomy, informed by the sources above and the domain.
  1. **Pairing errors.** A value is attached to the wrong row, or a threshold is shifted a column (air vs water column).
  2. **Unit and scale errors.** µg/L vs ng/L vs mg/kg vs µg/m³ vs ppb (v/v vs w/w). Units stated only in the header or footnote are often lost.
  3. **Medium errors.** Air vs water vs oil vs a specific matrix (beer, wine model solution, 10% ethanol, starch). The medium is often in the Methods text, not in the table.
  4. **Detection vs recognition** thresholds confused. Orthonasal vs retronasal is not captured.
  5. **Cited vs measured.** Many papers copy thresholds from earlier literature, with a superscript reference. Without provenance this creates duplicates and false "independent" measurements. Extract `measured_here: bool` and `cited_ref`.
  6. **OAV and FD traps.** An OAV is a ratio that depends on the paper's own concentration and a threshold, often borrowed. FD factors are 2^n dilution steps (sometimes reported as log₃ or as "FD 1024"). Charm and OSME values are not FD factors.
  7. **Hallucinated values** for compounds named in the text but absent from the table.
  8. **Range and inequality handling** ("<0.1", "0.2–0.4", "n.d.").
- **Validation stack** (cheap to expensive):
  - (a) JSON-schema-constrained output.
  - (b) Rule checks: unit whitelist, conversion to a canonical unit (µg/L water; µg/m³ or ng/L air), log-threshold plausibility window, and an FD factor that is a power of 2 or 3.
  - (c) **Grounding check.** The numeric string must appear verbatim in the parsed source text or table. This is the most effective anti-hallucination rule, and it costs nothing.
  - (d) Dual-model agreement, e.g., a Claude-class and a Gemini-class model, or two prompts. Records that agree go through; disagreements go to review.
  - (e) Cross-source consistency: flag a value more than 2 log units away from the median for that compound and medium.
  - (f) Stratified human spot check (Section 6).
- ChatExtract-style follow-up questions are an alternative to dual-model agreement. Both roughly double the token cost, which at 2026 prices is small (Section 4).

### Gaps
- Per-task precision/recall for Dagdelen et al. was not retrieved: the Nature page is behind a redirect and only the arXiv abstract was accessible.
- SciDaSynth and LLaMP were not researched in this session. There are no numbers for them here.
- I found no extraction-accuracy benchmark on **tables** specifically (as opposed to sentences) for chemistry property values. The ChatExtract numbers are sentence-level.

---

## 4. Cost estimation: API LLMs and local parsing and inference

### Takeaway
At September 2026 list prices, extracting 10k papers of about 15k tokens each costs **roughly $30 (Gemini Flash-Lite batch) to about $540 (Claude Opus batch)**. A mid-tier model such as Claude Sonnet 5 or Gemini 3.1 Pro costs about $200–250 batched. At 50k papers the range is about **$150–$2,700**. A dual-model setup roughly doubles these figures. LLM API cost is not the bottleneck. PDF acquisition and licensing, parsing compute (tens of GPU-hours), and human QA hours dominate.

### Cited Findings — prices (per 1M tokens, input / output)
- **Anthropic (first-party API, table cached 2026-06-24, from the Claude API reference):** Claude Opus 5 $5/$25; Claude Opus 5.5 $4/$20; **Claude Sonnet 5 $2/$10**; Sonnet 4.6 $3/$15; **Claude Haiku 4.5 $1/$5**. The Batches API runs at **50% of cost**. Prompt-cache reads are about **0.1×** the input price and cache writes about 1.25× — Anthropic Claude API docs/skill reference; aggregator confirmation for Sonnet 4.6 and Haiku 4.5 prices and the 50% batch discount: [Finout Anthropic pricing 2026](https://www.finout.io/blog/anthropic-api-pricing); [BenchLM Claude pricing Sep 2026](https://benchlm.ai/anthropic/api-pricing)
- **Google Gemini (official pricing page, fetched Sep 2026):**
  - Gemini 3.1 Flash-Lite: $0.25/$1.50; batch $0.125/$0.75.
  - Gemini 3.5 Flash-Lite: $0.30/$2.50; batch $0.15/$1.25.
  - Gemini 2.5 Flash-Lite: $0.10/$0.40, with batch at half that. It retires 2026-10-16 per an aggregator.
  - Gemini 3.8/3.7/3.6 Flash: promotional $0.75/$3.75 through 2026-12-31, then $1.50/$7.50; batch is half.
  - Gemini 3.5 Flash: $1.50/$9.00.
  - Gemini 3.1 Pro Preview: $2.00/$12.00 (≤200k prompt); batch $1.00/$6.00.
  - Context caching costs about 10% of input.

  Sources: [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing); retirement date from [BenchLM Gemini pricing](https://benchlm.ai/google/api-pricing)
- **OpenAI (from aggregators; official page listed but not fetched, so uncertain):** gpt-5 $1.25/$10; gpt-5-mini $0.25/$2.00; gpt-5-nano $0.05 input; GPT-5.4 $2.50/$15 (mini $0.75/$4.50, nano $0.20/$1.25); gpt-5.6-sol $5/$30; gpt-5.6-terra $2/$12; gpt-5.6-luna $0.20/$1.20. Batch is 50% off — [OpenAI pricing page](https://developers.openai.com/api/docs/pricing); [Morph OpenAI pricing](https://www.morphllm.com/openai-api-pricing); [BenchLM OpenAI pricing](https://benchlm.ai/openai/api-pricing)

### Cited Findings — local parsing throughput
- **Marker 2.** Balanced mode runs at **2.9 pages/s** on one NVIDIA B200 and fast mode at **7.4 pages/s** (~134 ms/page). CPU with `--disable_ocr` runs at **23.7 pages/s** (born-digital text only) — [MarkTechPost](https://www.marktechpost.com/2026/07/24/datalab-marker-v2-vs-mineru-docling-and-liteparse-benchmark-breakdown/); [Lumien](https://lumienai.com/news/marker-2-vs-mineru-docling-liteparse-olmocr-bench-benchmark) (vendor-produced numbers)
- **MinerU2.5.** The VLM backend runs at about **2.1 pages/s on an A100-80G** and up to about 4.5 pages/s on an H200. The pipeline backend runs at about 0.54 pages/s. Expect roughly 1,600–2,000 pages/hr with 4–5 workers on an L40S for mixed native and scanned documents with equations — [Spheron guide](https://www.spheron.network/blog/self-host-document-intelligence-docling-marker-mineru-rag-guide/); [MinerU2.5 paper](https://arxiv.org/pdf/2509.22186)
- **Docling.** About 2.1 pages/s in the Marker benchmark, and about 2,400 pages/hr on an L40S — [Spheron guide](https://www.spheron.network/blog/self-host-document-intelligence-docling-marker-mineru-rag-guide/)

### Cost arithmetic (my calculations; assumptions marked)
**Assumptions (uncertain):**
- A 10-page food-chemistry paper is about 12k tokens of text (the brief's 10–15k range).
- A fixed prompt, schema and few-shot examples add about 2k tokens, so input is **14k tokens/paper**.
- Output is **1.5k tokens/paper** on average. A table of 30 compounds × ~50 tokens of JSON is about 1.5k; many papers have fewer rows. Thinking disabled or low effort; adaptive thinking could add 1–3k output tokens.
- Prompt caching of the 2k prefix is ignored because it saves under 10%.

Per-paper cost = 14,000 × p_in/1e6 + 1,500 × p_out/1e6

| Model (list price) | Standard $/paper | Batch $/paper | 10k papers (batch) | 50k papers (batch) |
|---|---|---|---|---|
| Gemini 3.1 Flash-Lite ($0.25/$1.50) | 0.0035+0.00225 = **$0.0058** | $0.0029 | **$29** | **$144** |
| GPT-5-mini ($0.25/$2.00, uncertain) | 0.0035+0.0030 = $0.0065 | $0.0033 | $33 | $163 |
| Gemini 3.8 Flash promo ($0.75/$3.75) | 0.0105+0.0056 = $0.0161 | $0.0081 | $81 | $403 |
| Claude Haiku 4.5 ($1/$5) | 0.014+0.0075 = $0.0215 | $0.0108 | $108 | $538 |
| Claude Sonnet 5 ($2/$10) | 0.028+0.015 = **$0.043** | $0.0215 | **$215** | **$1,075** |
| Gemini 3.1 Pro ($2/$12) | 0.028+0.018 = $0.046 | $0.023 | $230 | $1,150 |
| Claude Opus 5 ($5/$25) | 0.070+0.0375 = $0.1075 | $0.0538 | $538 | **$2,688** |

- **Standard (non-batch)** prices are 2× the batch column. For example, Sonnet 5 costs $430 for 10k papers and $2,150 for 50k.
- **Dual-model validation** (e.g., Sonnet 5 + Gemini 3.1 Pro, both batched) costs about $0.045/paper, which is about **$445 for 10k and $2,225 for 50k**.
- **Image input.** Anthropic's documented formula is image tokens ≈ width×height/750 px, so a page at about 1,000×1,400 px is about 1.9k tokens. This is from vendor docs; I did not re-fetch them, so treat it as uncertain. A full 10-page paper sent as images is about 15–20k tokens, which is similar to text. The cost-efficient hybrid is text/Markdown for the whole paper plus page images only for the 1–3 table pages, adding about 2–6k tokens (+15–40%).
- **Pre-filter savings.** If a cheap classifier (Flash-Lite over title, abstract and table captions, about 1k tokens, about $0.0003/paper) passes only 20–40% of papers to the expensive model, the Sonnet-class spend for 50k papers falls from about $1,075 to about **$215–430**.
- **Local parsing compute for 50k papers × 10 pages = 500k pages:**
  - MinerU2.5 VLM on an A100 at 2.1 p/s: 500,000/2.1 ≈ 238,000 s ≈ **66 GPU-hours**.
  - Marker 2 fast mode on a B200 at 7.4 p/s: ≈ 67,600 s ≈ **19 GPU-hours**.
  - Marker CPU no-OCR at 23.7 p/s: ≈ 5.9 h, for born-digital files only.
  - Docling at ~2,400 p/hr on an L40S: ≈ **208 GPU-hours**.
  - For 10k papers, divide by 5 (MinerU ≈ 13 A100-hours).
  - At an assumed **$1.5–3/GPU-hour** cloud rental (unsourced, uncertain), MinerU for 50k papers costs about **$100–200**.
- **Local open-weight LLM** (Qwen/Llama class). The total is 50k × 15.5k ≈ 775M tokens, mostly prefill. At an assumed ~2–5k tokens/s aggregate prefill+decode on one H100 with vLLM for a ~30B model (uncertain, unsourced), that is roughly **45–110 GPU-hours**, or about $100–300 at rental rates. This is comparable to Flash-class API cost, but with worse accuracy and more engineering. It is only attractive if data or licensing constraints forbid external APIs.

### Gaps
- I did not verify real token counts for food-chemistry PDFs. Measure on 50 sample papers with a token-count endpoint.
- The OpenAI numbers come from aggregators because the official page was not fetched.
- Local LLM throughput and GPU rental rates are unsourced assumptions.
- GROBID throughput was not verified. From prior knowledge it is CPU-fast (roughly seconds per paper), but that is unconfirmed here.

---

## 5. Pre-filtering: finding relevant papers and tables cheaply

### Takeaway
Cheap filtering happens in three stages: corpus metadata and keyword search, then a paragraph- or table-level heuristic or NER filter, then an optional tiny-LLM classifier. The polymer study (681k papers → >1M records) showed that NER- or heuristic-filtered paragraphs are the main cost lever. The same logic applies to threshold tables, which are highly lexically distinctive.

### Cited Findings
- Gupta et al. combined a MaterialsBERT NER step with GPT-3.5/LlaMa 2 extraction. They present methods to "optimize costs" and discuss in-context few-shot inference — [Commun Mater 2024](https://www.nature.com/articles/s43246-024-00708-9); [code](https://github.com/Ramprasad-Group/PromptDataExtraction)
- ChatExtract's first stage is a sentence classifier ("does this sentence contain the property data?") before extraction — [arXiv 2303.05352](https://arxiv.org/abs/2303.05352)

### Inferences
- **Stage 0: corpus discovery (free).** Query OpenAlex, Crossref or Semantic Scholar for "odor threshold", "odour threshold", "aroma extract dilution analysis", "AEDA", "FD factor", "odor activity value", "OAV", "GC-O", "GC-olfactometry", "CharmAnalysis", "OSME", "sensomics", "key odorants", "recombination". Journal-level priors help: J. Agric. Food Chem., Food Chem., Eur. Food Res. Technol., Flavour Fragr. J., J. Food Sci., Food Res. Int.
- **Stage 1: table-caption and header regex over parsed XML or Markdown (≈free).** Patterns: `threshold|OT|OTV|odou?r activity|OAV|FD|dilution factor|µg/L|ng/L|µg/kg|µg/m3|ppb` in captions or headers. This probably catches >90% of target tables (uncertain).
- **Stage 2: embedding or small-LLM classifier.** Run it on captions, headers and the first rows. Flash-Lite at about 1k tokens costs about $0.0003/paper, so $15 for 50k papers.
- **Section-level routing.** Send only Methods (for medium and method) plus the tables, table footnotes, and the paragraphs that cite them. This cuts per-paper input from about 12k tokens to about 4–6k.

### Gaps
- I found no published recall figure for keyword or regex filters on flavor-chemistry threshold tables. Estimate it by annotating 200–500 random candidate papers.

---

## 6. Human-in-the-loop verification workload and QA tooling

### Takeaway
Plan human effort around disagreement adjudication plus a stratified random audit, not a flat 5%. For about 100k–200k extracted records, a 5% audit takes about 40–170 person-hours, and adjudicating disagreements takes about the same again. Label Studio and Argilla are both suitable. No odor-specific QA figures exist in the literature I found.

### Cited Findings
- 2026 practice: "experts specify the evidence standard, models cross-check repeated extractions and researchers resolve disputed cases"; human-in-the-loop remains required — [arXiv 2608.19025](https://arxiv.org/pdf/2608.19025)
- ChatExtract-style verification prompts reduce, but do not eliminate, errors (about 90% precision/recall with GPT-4) — [Nat Commun 2024](https://www.nature.com/articles/s41467-024-45914-8)

### Inferences (workload arithmetic, all assumptions uncertain)
- **Volume assumption.** Of 50k candidate papers, perhaps 10–20% (5k–10k) contain threshold, OAV or FD tables, at about 20 records each. That gives **100k–200k records**.
- **5% flat audit** = 5k–10k records. At 30–60 s per record, checking against a highlighted PDF crop, that is **42–167 person-hours**.
- **Disagreement queue.** With dual-model disagreement at about 10–15% of records, that is 10k–30k records. At about 45 s each, that is **125–375 hours**. Group by table, not by record, because one table view resolves 20 rows in about 2–3 minutes. That brings the figure down to about **50–150 hours**.
- **Gold set for prompt development and evaluation.** Fully annotate 100–200 papers (about 2k–4k records) at about 20–30 min/paper, which is **35–100 hours**. This gives per-field precision and recall with confidence intervals and is non-negotiable before a scale-up.
- **Total human effort** is roughly **150–400 person-hours** for a 50k-paper run, and about a third of that for 10k.
- **Tooling:**
  - Label Studio supports PDF/image regions plus JSON field review.
  - Argilla is suited to record-level accept/reject/correct on LLM outputs, with suggestions pre-filled.
  - A lightweight custom Streamlit app showing the table crop and the extracted rows side by side is often fastest for table adjudication. That is prior knowledge; I did not research feature details of these tools this session.

### Gaps
- I found no empirical per-record verification time for scientific table extraction QA. The numbers above are estimates.
- I did not check current (2026) Label Studio or Argilla feature sets or licensing in this session.

---

## 7. Existing precedents specific to food, flavor and odor

### Takeaway
I found **no published work that used LLMs or text mining to extract odor thresholds, OAVs or FD factors from the literature at scale**. Existing threshold ML datasets are small (hundreds of compounds) and were aggregated manually from curated databases. An LLM-mined dataset would be novel, but it will run into the known problem of thresholds varying by orders of magnitude across sources.

### Cited Findings
- A 2025 study (PMC12654368) on predictive models of odor contribution and thresholds for crop aroma compounds compiled **odor thresholds for 716 compounds** and **odor-descriptor annotations for 31,459 volatiles**. They were aggregated from existing databases (FlavorNet, Lee et al. 2023, Pyrfume, Pred-O3), not mined with LLMs. Multiple measurements were combined by the **median** and harmonized to mg/L (as −log₁₀ mg/L). Thresholds "varied by several orders of magnitude" between sources. The ECFP4-GBDT threshold model reached **R² = 0.94, RMSE = 0.44** log units (RMSE 0.17 for low-threshold and 0.64 for high-threshold compounds). No explicit QC framework is described — [PMC12654368](https://pmc.ncbi.nlm.nih.gov/articles/PMC12654368/)
- The VCF online database covers **9,832 volatile substances** in foods, with odor descriptions and aroma thresholds. FEMA's Flavor Ingredient Library has 3,012 flavor substances. OlfactionBase has 5,109 odorants. Reviews name "data inaccessibility, untimely updates, and nonstandard flavor descriptions" as the main limitations, and note that most volatiles lack threshold data — [Data-Driven Elucidation of Flavor Chemistry, JAFC 2023](https://pubs.acs.org/doi/10.1021/acs.jafc.3c00909); [Flavor compounds identification and reporting, PMC12844016](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12844016/)
- LLM work in olfaction so far concerns descriptor semantics, not potency data. For example, "Odor maps from LLM-derived similarity scores" (2026) compared GPT-4o-mini and Gemma 3 descriptor similarities with the Dravnieks dataset of 180 odorants and 146 descriptors (Mantel r = 0.332) — [arXiv 2604.20310](https://arxiv.org/html/2604.20310v1)
- A 2026 critical review of food aroma extraction and analysis methods — [Food Res Int / ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0963996926020533). There is also a PMC review of sensory-guided (GC-O, AEDA) to flavoromics methods — [PMC11695657](https://pmc.ncbi.nlm.nih.gov/articles/PMC11695657/). These are useful for defining the method vocabulary (AEDA, CHARM, OSME, detection frequency) in the extraction schema.

### Inferences
- The key scientific value of a mined dataset is **provenance-rich multi-measurement records** (medium, method, detection vs recognition, panel size, year) rather than one median per compound. That would let a model learn or correct for the method effects that the existing median-aggregated datasets wash out.
- Mined thresholds will contain many **citation copies** of the same classic values: Rychlik/Schieberle/Grosch compilations, Van Gemert's compilation, Buttery's water thresholds. Deduplicating by (compound, value, medium, cited source) is essential, or the dataset will over-weight a few measurements.

### Gaps
- I did not find FlavorDB's construction method, or any "FlavorMiner" tool, in this session. Claims about them are unverified.
- Van Gemert's "Compilations of Odour Threshold Values" and Leffingwell/Burdock/Good Scents compilations are known threshold sources, but I did not retrieve their licensing or availability here.

---

## 8. Patents as a source (Google Patents BigQuery, USPTO, EPO, SureChEMBL)

### Takeaway
Fragrance patents (Givaudan, Firmenich/DSM-Firmenich, IFF, Symrise, Takasago) often report odor thresholds or "odour values" for novel molecules. That makes them a good complement for **novel, non-food fragrance chemistry** that journals rarely cover. Patent full text is freely available in bulk (Google Patents public data on BigQuery, USPTO bulk, EPO), and SureChEMBL already links chemical structures to patent text. The extra effort is mainly retrieval and filtering plus handling of patent-style "compound of Example 3" references. The LLM cost is similar per document.

### Cited Findings
- **SureChEMBL** is a public resource that extracts compounds from patent full text, images and attached MOL files with an automated text- and image-mining pipeline, updated daily. It supports combined structure and keyword search, plus data downloads — [SureChEMBL NAR 2016, PMC4702887](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4702887/); [surechembl.org](https://www.surechembl.org/)
- **SureChEMBL 2.0** (2025–2026) rebuilt the pipeline with "cleaner data and a more robust extraction pipeline" — [kiin.bio newsletter](https://newsletter.kiin.bio/p/surechembl-20-rebuilding-patent-chemistry) (secondary). SureChEMBL has also been deposited in PubChem as part of a patent-extracted chemistry "big bang" — [Zenodo 20492718](https://zenodo.org/records/20492718)
- **Google Patents public datasets on BigQuery** include patent publications and a "Google Patents Research Data" annotations table. The SureChEMBL mirror in BigQuery was **last updated in November 2018**, so it is stale — [google/patents-public-data issue #25](https://github.com/google/patents-public-data/issues/25)
- **PatCID** (Nat Commun 2024) is an open-access dataset of chemical structures recognized from patent document images — [PatCID](https://www.nature.com/articles/s41467-024-50779-y)
- An example fragrance patent in USPTO full text ("Organic compounds") shows the document class available through USPTO — [USPTO 12522786](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12522786)

### Inferences (effort estimate; uncertain)
- **Retrieval.** In BigQuery, filter publications by CPC **C11B 9/00** (essential oils/perfumes), **A61K 8/** + **A61Q 13/** (perfumery), and **A23L 27/20** (flavoring agents), together with full-text terms such as "odour threshold", "odor detection threshold", "ng/l air" or "odour value". This probably yields thousands to low tens of thousands of families (uncertain). Deduplicate to one publication per family (prefer EP/WO English full text).
- **Extraction differences from journals.** Thresholds are often in prose or in example tables ("the compound of Example 5 has an odour threshold of 0.3 ng/l air"). The compound identity must be resolved from the example's synthesis section, IUPAC name, or a structure image. OPSIN works well on patent IUPAC names; SureChEMBL or PatCID give structures for image-only compounds.
- **Cost.** Patent texts are long, often 20–60k tokens. Section routing (examples and claims with threshold keywords only) keeps input to about 5–10k tokens per patent. For 10k patents at Sonnet-5 batch rates that is about 10k × (8k×$1 + 1k×$5)/1e6 ≈ **$130**. Human QA is comparable per record to the journal case.
- **Bias.** Patent thresholds are self-reported by assignees, usually with in-house GC-O panels, and mostly in **air** (ng/L air). Tag `source_type = patent` so models can weight or ablate them.
- **Overall effort.** Adding a patent branch to an existing journal pipeline takes roughly **2–4 extra engineering weeks**: BigQuery query, section router, patent-specific prompts, and example-to-compound resolution. This is an inference, not sourced.

### Gaps
- I did not verify current BigQuery table names and schemas (e.g., `patents-public-data.patents.publications`), full-text language coverage, or query costs in this session.
- USPTO bulk data and EPO full-text data (EP full-text for text and data mining) access terms were not retrieved.
- I have no measured count of fragrance patents that report thresholds. Run the BigQuery keyword and CPC query to size it (likely under $5 of BigQuery scan cost, unverified).

---

## Appendix: suggested pipeline shape and effort (inference; for the report writer)

1. **Acquire:** OpenAlex query → DOIs → publisher TDM XML where licensed (Elsevier, ACS, Wiley, Springer) and PMC OA. PDF fallback. BigQuery for patents.
2. **Parse:** use XML directly. For PDFs, use MinerU2.5 (accuracy) or Marker 2 (speed). GROBID for sections and references. Render table pages to PNG.
3. **Filter:** caption/header regex, then a Flash-Lite classifier.
4. **Extract:** a Sonnet-class model, batched, with the JSON schema: compound_name_verbatim, CAS, stereo, value, value_qualifier, unit_verbatim, medium, matrix, threshold_type (detection/recognition/difference), orthonasal/retronasal, method (ASTM E679, 3-AFC, GC-O, …), panel_n, measured_here/cited_ref, OAV, FD, intensity_scale, table_id/row, and evidence_span. Input is table Markdown + table image + Methods.
5. **Resolve names:** CAS → PubChem → CIR → OPSIN → LLM synonym, then InChIKey consensus.
6. **Validate:** grounding check, unit normalization, plausibility window, second-model agreement, and outlier flags.
7. **Human QA:** gold set of 100–200 papers, disagreement queue, and a 5% stratified audit.
8. **Deduplicate** cited values and store full provenance.

- **LLM spend (50k papers):** about $200–2,700 depending on model and dual-check, and about $400–1,100 for a sensible Sonnet+Flash dual setup with pre-filtering.
- **Compute:** about 20–70 GPU-hours of parsing.
- **Engineering:** about 4–8 person-weeks for journals, plus 2–4 weeks for patents (uncertain).
- **Human QA:** about 150–400 hours at 50k papers.
- **Expected residual error after validation:** in the 2–5% record range, extrapolated from about 90% raw precision with verification and dual-model filtering. This is uncertain and must be measured on the gold set.
