# Industry and startup teams building AI for olfaction, fragrance and flavor, with a focus on potency, intensity, threshold and performance (as of Sept 2026)

Scope note: these are research notes on industry and startup actors. Academic-only groups are mentioned only where they are directly tied to a company (for example Monell–Osmo) or give needed context. "Disclosed" means stated in a primary or trade-press source cited inline. "Inference" means my reasoning. Some fetches were blocked: Business Wire and Perfumer & Flavorist returned HTTP 403. For those items I relied on secondary coverage and have flagged it.

---

## 1. Osmo (Alex Wiltschko; spun out of Google Research/Brain): architecture, papers, data, compute, funding, patents, potency

### Takeaway
Osmo is the best-documented industry player. Its published core model, the Principal Odor Map (POM), is a message-passing GNN with a 256-d embedding. It was trained on about 5k molecules for odor *quality* (descriptors), not intensity. Osmo's direct intensity work is academic co-authorship with Monell: a 2025 intensity framework using a DNN on Dragon descriptors plus Hill curves, and a 2026 linear mixture-quality paper. By 2026 Osmo has become a vertically integrated "AI fragrance house" (Generation). It claims 5M human smell annotations, 250k physical samples and 3B molecules mapped, and it discloses almost nothing about architecture or compute beyond a 2023 Google Cloud case study.

### Cited Findings

**Corporate, funding and team**
- Founded as a Google Research/Brain spin-out by Alex Wiltschko, a former Google Brain researcher with a Harvard PhD in olfactory neuroscience. Google transferred "all relevant IP (data, code, models, patents)" to Osmo Labs, PBC. — [PMC: POM paper competing-interest statement](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/); [Osmo patent reassignment, US20220139504](https://patents.google.com/patent/US20220139504)
- Series A was $60M, led by Lux Capital and GV. Osmo's own site dates it to 2022; Contrary Research and Beauty Independent say it was announced in January 2023. Other participants listed by Contrary: Arena Holdings, Moore Strategic, Two Sigma Ventures, the Amazon Alexa Fund, Exor Ventures, and the Bill & Melinda Gates Foundation. — [Osmo About](https://www.osmo.ai/about); [Contrary Research](https://research.contrary.com/company/osmo); [Beauty Independent](https://www.beautyindependent.com/osmo-raises-70m-series-b-expand-ai-powered-fragrance-ingredient-design-manufacturing/)
- Series B was $70M (February 2026), led by Two Sigma Ventures. Also named: Valor, Atreides, Amplo, Alumni Ventures, Collab Fund, Lumina Partners and Patrick Collison. Beauty Independent gives total funding as "$130 million". Glossy and Business Wire coverage (via search snippet) says $133.5M. — [Beauty Independent](https://www.beautyindependent.com/osmo-raises-70m-series-b-expand-ai-powered-fragrance-ingredient-design-manufacturing/); [Glossy](https://www.glossy.co/beauty/ai-powered-fragrance-company-osmo-raises-70-million-in-series-b-funding/); [Business Wire (403 on fetch)](https://www.businesswire.com/news/home/20260204293785/en/Osmo-Digital-Scent-Design-Company-Announces-$70M-in-Series-B-Funding-and-Executive-Leadership-Team-to-Scale-AI-Powered-Olfaction-Technology)
- A Gates Foundation grant of $3.5M (November 2023) funds DEET-alternative mosquito-repellent discovery with Trop IQ. Contrary reports 10 candidate molecules that beat DEET out of a 317-compound test set, with 8 finalists. — [Contrary Research](https://research.contrary.com/company/osmo)
- Team: more than 100 employees across New Jersey and Boston. Executives include CTO Rich Whitcomb, COO Mateusz Brzuchacz (ex-Givaudan and IFF), CFO Nate Pearson (ex-Tesla) and CCO Mike Rytokoski (ex-Unilever and Amyris). Master perfumers include Christophe Laudamiel. — [Osmo About](https://www.osmo.ai/about); [Beauty Independent](https://www.beautyindependent.com/osmo-raises-70m-series-b-expand-ai-powered-fragrance-ingredient-design-manufacturing/)
- Scientific advisory board: Geoffrey Hinton, Ryan Adams (Princeton), John Cunningham (Columbia), Joel Mainland (Monell) and others. Rick Gerkin appears as an Osmo employee or SAB member in papers. — [Osmo About](https://www.osmo.ai/about); [PMC intensity paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)
- Facility: a manufacturing and R&D site in Elizabeth, NJ, described as "60,000 sq ft" in press and "58,000 sq ft" on Osmo's site. It replaces a 10,000 sq ft Manhattan lab and was targeted to be fully operational by March 2026. — [Beauty Independent](https://www.beautyindependent.com/osmo-raises-70m-series-b-expand-ai-powered-fragrance-ingredient-design-manufacturing/); [Osmo About](https://www.osmo.ai/about)

**Disclosed data scale (company claims, not independently verified)**
- "250K physical samples created, 3B molecules mapped, 5M human annotations of smell recorded, 8K molecules synthesized." — [Osmo About](https://www.osmo.ai/about)
- Osmo calls its platform "Olfactory Intelligence (OI)", "built on the world's largest interconnected scent dataset and the world's first olfactory world model". It says it screens billions of molecules "to predict how they will smell, perform and behave". — [Osmo home/About via search snippet](https://www.osmo.ai/); [Perfumer & Flavorist 2026 (403 on fetch; search snippet)](https://www.perfumerflavorist.com/fragrance/fine-fragrance/article/22965261/osmo-osmo-accelerates-fragrance-innovation-through-ai-molecular-discovery-and-scalable-olfactory-intelligence-platform)
- Osmo says it filed "more patents for new fragrance ingredients than the rest of the fragrance industry combined" in 2025. — [Osmo About](https://www.osmo.ai/about)
- Commercial ingredient library of about 900 synthetic, natural and proprietary ingredients. Output is "hundreds of scents per week", with fragrances delivered in "as little as 48 hours" and nearly 100 brand customers. — [Beauty Independent](https://www.beautyindependent.com/osmo-raises-70m-series-b-expand-ai-powered-fragrance-ingredient-design-manufacturing/)

**Principal Odor Map (Lee et al., Science 2023): disclosed architecture**
- Model: a message-passing neural network (MPNN). The penultimate layer is the 256-dimensional POM, and the final layer predicts odor labels.
  - Atom features: valence, degree, hydrogen count, hybridization, formal charge, atomic number.
  - Bond features: degree, aromaticity, ring membership.
  - Cross-validated AUROC is 0.89.
  - Source: [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- Training data: about 5,000 molecules from the GoodScents and Leffingwell databases, multi-label. The split is 80/20 train/test, with 5-fold cross-validation inside the training set. — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- Hyperparameter search: Bayesian optimization with Google Vizier over 1,000 trials. Training ran 150 epochs with Adam; the learning rate decayed from 5e-4 to 1e-5; batch size 128; the loss was weighted cross-entropy. — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- The paper states that "the code implementing and training the GNN model is not available to share". The fetched summary did not surface the layer count or ensemble size. — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- Human panel:
  - At least 15 trained panelists using a 55-word lexicon with RATA (rate-all-that-apply) scoring.
  - Prospective validation set: 323 novel odorants, rated twice per panelist; test-retest R=0.80 ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)).
  - Monell's press release says "400 odorants" were described and 15 panelists took part. The model "performed better than the average panelist for 53% of the molecules" ([Monell](https://monell.org/a-step-closer-to-digitizing-the-sense-of-smell-monell-center-osmo-model-describes-odors-better-than-human-panelists/)). The 400 vs 323 counts conflict; 323 is likely the count after filtering (unverified).
- **Potency relevance:** Monell's release says "we never trained it to learn odor strength, but it could nonetheless make accurate predictions". It also says odor properties were characterized for 500,000 potential scent molecules. In other words, POM embeddings transfer to odor strength, but the model was not trained on it. — [Monell](https://monell.org/a-step-closer-to-digitizing-the-sense-of-smell-monell-center-osmo-model-describes-odors-better-than-human-panelists/)

**Intensity and mixture papers with Osmo authors (2025–2026)**
- Pellegrino, Samoilova, Ihara, Andres, Singh, **Gerkin (Osmo Labs)**, Koulakov and Mainland, "A quantitative framework for predicting odor intensity across molecule and mixtures". bioRxiv, August 2025 ([PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/); [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.08.08.668954v1)).
  - Data: 62 odorants at 7 or more concentrations each (434 monomolecular points), rated by 36 panelists. Mixtures: 260 in total (216 binary, 20 ternary, 16 five-component, 8 ten-component), giving 7,623 mixture ratings. Odors were delivered by a closed gas-sampling-bag system with test-retest r=0.97.
  - Model: a 5-layer DNN on 127 Dragon physicochemical descriptors, not on POM. A 10-feature version built on transport parameters (MW, vapor pressure, boiling point, MLOGP, etc.) performed about as well. Training was augmented with 300 points per molecule sampled from Hill-curve fits, I = Imax·C^n/(C^n+EC50^n).
  - Single-molecule results: RMSE 7.1, r=0.87. The 10-feature model gave r=0.87 and RMSE 7.2.
  - Mixture results: the primacy model scored r=0.85 (RMSE 8.6) and the NN mixture model RMSE 7.5. Predictions correlated with GC-O intensity at r=0.62, and the model identified key odorants better than OAV (r=0.55 vs 0.45).
  - Funding: Ajinomoto and NIH.
- Pellegrino, Mayhew, Margolis, Andres, **Wiltschko**, **Gerkin** and Mainland, "Odors Smell Like Their Components: A Linear Framework for Predicting Olfactory Mixture Perception". bioRxiv, 8 July 2026, with Osmo Labs among the affiliations. It covers 432 mixtures of 144 components, rated by a trained panel. Its claim: "nearly all mixtures were explained by a linear average of their component quality profiles". This addresses quality; the abstract does not state whether intensity is modeled. — [bioRxiv](https://www.biorxiv.org/content/10.64898/2026.07.03.736426v1)
- Contrary Research (2025) lists "non-linearities in intensity prediction (concentration-dependent scent shifts) not reliably captured" and enantiomer discrimination as open limitations for Osmo. — [Contrary Research](https://research.contrary.com/company/osmo)

**Products and demos**
- Scent Teleportation (2024): a plum scent was captured by GC-MS, mapped through POM/AI, and re-created by a "refrigerator-sized" printer. — [Startups Magazine](https://startupsmagazine.co.uk/article-osmo-brings-scent-teleportation-and-ai-fragrances-life); [P&F](https://www.perfumerflavorist.com/fragrance/regulatory-research/news/22891453/osmo-in-early-stages-of-realizing-scent-teleportation)
- Generation, an "AI-powered fragrance house", launched in March 2025 with three captive AI-designed molecules: Glossine, Fractaline and Quasarine.
  - The molecules are "engineered to deliver specific olfactive functions such as radiance, texture and diffusion".
  - Performance claims: Glossine performs on dry fabric; Fractaline is long-lasting; Quasarine is long-lasting and "the most intense" of the three.
  - These are **performance claims in marketing**; no disclosed performance-prediction model is attached to them.
  - Sources: [Beauty Independent](https://www.beautyindependent.com/osmo-raises-70m-series-b-expand-ai-powered-fragrance-ingredient-design-manufacturing/); search summary of [P&F](https://www.perfumerflavorist.com/news/fragrance/news/22926387/osmo-launches-scent-molecules-through-proprietary-ai-technology) and [Business Wire](https://www.businesswire.com/news/home/20250305918665/en/Osmo-Launches-Generation-Worlds-First-AI-Powered-Fragrance-House)
- Contrary lists further products:
  - Inspire: a GPT-like scent-design interface, in closed beta as of May 2025.
  - Forge: a molecule-discovery engine, claimed to cut development from about 10 years to 1.75–2.5 years, with claims of "3x better than existing discovery methods" of the major houses.
  - Partnerships: a StockX counterfeit-detection pilot and the Museum of Pop Culture (MoPOP).
  - Source: [Contrary Research](https://research.contrary.com/company/osmo)

**Compute and infrastructure**
- Google Cloud case study (14 March 2023): Osmo uses Vertex AI for training, Dataflow to run models over large molecule libraries, BigQuery (a table of about 40 billion molecules at about 15 TB) and Bigtable for model outputs. **No GPU or TPU counts or model sizes are disclosed.** Osmo was named one of three foundation-model companies joining Google Cloud in March 2023. — [Google Cloud blog](https://cloud.google.com/blog/products/ai-machine-learning/how-osmo-is-bringing-ai-to-aromas); [Google Cloud partner blog](https://cloud.google.com/blog/products/ai-machine-learning/building-an-open-generative-ai-partner-ecosystem)

**Partnerships with the big houses**
- I found no announced Osmo partnership with Givaudan, dsm-firmenich, Symrise or IFF. Osmo competes with them and hires from them: its COO is ex-Givaudan/IFF, and a board member previously led dsm-firmenich operations. — [Trellis/search summary](https://trellis.net/article/ai-fragrance-tech-startup-osmo-hires-execs-raises/); [Beauty Independent](https://www.beautyindependent.com/osmo-raises-70m-series-b-expand-ai-powered-fragrance-ingredient-design-manufacturing/)

### Inferences
- Osmo's public, peer-reviewed potency work sits in academic collaborations led by Monell, where Osmo contributes staff (Gerkin, Wiltschko). Those papers use small, carefully controlled psychophysics datasets (62 molecules × 7+ concentrations) and descriptor-based DNNs, not large GNNs. That suggests even Osmo lacks large public intensity or threshold datasets. Its "5M annotations" are probably mostly quality or descriptor ratings (unverified).
- The "world model" and "billions of molecules" claims point to inference-heavy screening (cheap GNN forward passes over huge libraries, via Dataflow/BigQuery) rather than frontier-scale training. A GNN of POM's scale trains on modest hardware. The large items are the Vizier hyperparameter search (1,000 trials) and the library scoring.
- The Series B total discrepancy ($130M vs $133.5M) plausibly reflects whether the $3.5M Gates grant is counted.

### Gaps
- POM layer count, message-passing variant details, readout and ensemble size were not confirmed in the text I could fetch. Obtain them from the Science supplementary materials.
- No Osmo patent specifically on intensity, threshold or longevity prediction was found. Osmo's 2025 filings appear to be composition-of-matter claims on ingredients (per its own statement); none were enumerated.
- No GPU/TPU counts, cloud spend or model parameter counts are disclosed for Osmo's post-2023 "OI"/"world model".
- The 2026 Perfumer & Flavorist and Business Wire primary texts were blocked (403), so claims about screening "billions of molecules to predict how they will smell, perform and behave" rest on search snippets.

---

## 2. Google Research / DeepMind olfaction work

### Takeaway
Google's olfaction line has two key outputs. The first is the 2019 "Machine Learning for Scent" GNN (QSOR) paper. The second is the foundation for POM, built by the same people (Sanchez-Lengeling, Wei, Lee, Gerkin, Aspuru-Guzik, Wiltschko). Its IP, data, code and models were transferred to Osmo in 2022. I found no separate DeepMind olfaction program focused on potency.

### Cited Findings
- Sanchez-Lengeling, Wei, Lee, Gerkin, Aspuru-Guzik and Wiltschko, "Machine Learning for Scent: Learning Generalizable Perceptual Representations of Small Molecules" (arXiv:1910.10685, 2019). It uses GNNs for QSOR and "significantly out-perform[s] prior methods on a novel data set labeled by olfactory experts". The learned embeddings transfer to other tasks. — [arXiv](https://arxiv.org/abs/1910.10685)
- Google patent US20220139504A1, "Systems and Methods for Predicting the Olfactory Properties of Molecules Using Machine Learning". Inventors are Wiltschko and Sanchez-Lengeling. Priority date is 8 February 2019 and filing 10 February 2020. It was reassigned from Google LLC to Osmo Labs PBC on 25 October 2022 and is pending.
  - Architecture: GNN message-passing with reduce-sum aggregation, then fully connected layers, with one output node per descriptor. Examples extract a 63-d embedding from the penultimate layer.
  - Claims focus on categorical odor properties. Intensity descriptors or confidence values appear only as optional outputs.
  - Source: [Google Patents](https://patents.google.com/patent/US20220139504)
- Google patent US11009494B2, "Predicting human discriminability of odor mixtures". It describes an NN predicting mixture perceptual qualities and perceptual distance from structure. — [Google Patents](https://patents.google.com/patent/US11009494B2/en)

### Inferences
- The 2019 dataset (GoodScents plus Leffingwell, about 5k molecules) became the backbone of POM training. The step from Google to Osmo was mainly a change of owner, not a change of method.

### Gaps
- The exact 2019 descriptor count and GNN depth were not verified in this session (commonly cited as about 138 descriptors; unverified).
- The assignee of US11009494B2 was not captured in the fetch. I believe it is Google but have not verified this.
- No evidence of 2024–2026 Google DeepMind olfaction papers was found in these searches.

---

## 3. Fragrance houses: Givaudan, dsm-firmenich, IFF, Symrise, Kao, Takasago, Mane, Robertet

### Takeaway
The big houses publicly describe AI tools mostly for formulation generation, consumer and emotion prediction, and sustainability. Performance prediction appears only in vague terms: Givaudan's "Odour Value Map", IFF's "Science of Performance" with "decades of measured data", and Kao's dose-response database. **None of them discloses a model architecture for potency or intensity.** The most concrete industrial potency asset is Kao's dose-response database (314 perfumery raw materials, 18 expert panelists).

### Cited Findings

**Givaudan**
- Carto launched on 3 April 2019 from the Digital Factory in Paris (Computer Aided Creation programme, opened January 2019). It uses "the company's unique ingredients' Odour Value Map" to "maximise olfactive performance" and includes an instant-sampling robot. No model, data or algorithm details are disclosed. — [Givaudan press release 2019](https://www.givaudan.com/media/media-releases/2019/givaudan-fragrances-launches-carto-its-artificial-intelligence-powered-tool); [Givaudan Carto page](https://www.givaudan.com/fragrance-beauty/perfumery-school/carto-the-future-of-fragrance-formulations)
- Myrissi is an AI tool that predicts consumers' spontaneous emotional perception of a fragrance and maps it to colors and visuals. MoodScentz is described as predicting emotional impact. — [P&F on Myrissi](https://www.perfumerflavorist.com/news/fragrance/news/22684100/givaudan-givaudan-unveils-ai-technology-myrissi-to-predict-emotional-perception-of-fragrance); [search summary](https://cosmeticsbusiness.com/bringing-olfactory-knowledge-into-the-digital-age-givaudan-reinvents-how-perfumers-create--153468)
- A patent-related method described in search results: retrieve each ingredient's diffusion measure, group ingredients with similar diffusion, retrieve each one's olfactive contribution, and display total contribution ordered by diffusion to visualize the temporal fragrance profile. This is a **visualization and aggregation method, not ML**. The source was a PatSnap aggregator report, and I could not confirm the patent number, assignee or text (USPTO PDFs 12354713 and 12340876, "Method related to organic compositions", were image-only). — [PatSnap Eureka](https://eureka.patsnap.com/report-how-to-use-machine-olfaction-for-new-fragrance-development); [USPTO PDF](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12354713)

**dsm-firmenich**
- emotiOn™ (2025–2026): a "proprietary AI model" trained on 40,000+ tested fragrances and more than 1 million consumer responses, validated with the kronoscent™ neuroscience tool. "Social Connection" is one application. The target is emotion or wellbeing, not potency. — [dsm-firmenich trade news 2025](https://our-company.dsm-firmenich.com/en/our-company/news/trade-news/2025/dsm-firmenich-unveils-emotion-social-connection.html); [dsm-firmenich story 2026](https://our-company.dsm-firmenich.com/en/our-company/news/our-stories/2026/from-smell-to-smiles-the-future-of-feel-good-fragrances.html)
- Scentmate™ is a consumer/B2B scent-creation service (legacy Firmenich). EcoScent Compass is a digital eco-design tool. — [Firmenich press release](https://our-company.dsm-firmenich.com/en/our-company/news/press-releases/legacy-archive/firmenich/firmenich-launches-scentmatetm-new-way-scent.html); [P&F 2026 leaders piece (search summary)](https://www.perfumerflavorist.com/fragrance/trends/article/22965550/fragrance-leaders-newsmakers-2026-the-great-resetleadership-shifts-and-the-4-forces-driving-the-industrys-future)
- Firmenich supplied data for the "Learning to Smell" challenge (AIcrowd), which academic odor-prediction work has since used. — [search summary](https://pubs.rsc.org/en/content/articlehtml/2026/ra/d6ra01805j)

**IFF**
- Science of Performance (announced 2 April 2025) helps formulators "manage scent intensity and timing of fragrance release" and control malodor. It combines "decades of measured data" with "proprietary AI". Related platforms: IFF Scent+ (intensity at precise moments) and CTRL+D (malodor). **This is the most explicit big-house claim of AI for intensity and performance, but no architecture or data size is disclosed.** — [Personal Care Insights](https://www.personalcareinsights.com/news/iff-science-of-performance-fragrance-ai.html)
- ScentChat™ is a consumer-feedback app on WhatsApp and Messenger using "proprietary semantic and NLP AI algorithms". — [IFF news](https://www.iff.com/media/news/iff-adds-real-time-consumer-feedback-into-fragrance-creation-with-introduction-of-ai-powered-scentchat-app/)
- Correction to the brief: **Philyra is Symrise + IBM Research, not IFF.**

**Symrise (Philyra, with IBM Research)**
- The collaboration began in 2017. Symrise says a "first patent [was] granted for fragrance computational creativity" in 2019.
- Launches:
  - 2019: Boticário/Egeo launched "100% AI-generated" fragrances.
  - 2021: Belcorp/Ésika.
  - 2022: Philyra 2.0 added biodegradability and renewability scoring, and all Symrise fine-fragrance perfumers adopted it.
  - 2023: the tool won a Digital Beauty Award.
- Data: 3.5 million legacy formulas; "over 2,000 qualified raw materials evaluated across 20 dimensions" (older figure: about 1,500 materials). It generates up to 12 formulas in under a minute.
- Symrise publishes **no architecture** beyond a "continuous learning" description.
- Sources: [Symrise Philyra](https://www.symrise.com/scent-and-care/competence-platforms/philyra/); [Symrise newsroom](https://www.symrise.com/newsroom/article/breaking-new-fragrance-ground-with-artificial-intelligence-ai-ibm-research-and-symrise-are-workin/); [search summary incl. 2026 in-cosmetics](https://www.personalcareinsights.com/news/dawn-of-ai-perfumery-symrise-debuts-philyra-for-creative-green-transitions.html)

**Kao: an industrial potency dataset**
- Wakayama et al., "Method for Predicting Odor Intensity of Perfumery Raw Materials Using Dose–Response Curve Database", Ind. Eng. Chem. Res. 2019, 58(32):15036–44.
  - Data: dose-response data for 314 perfumery raw materials. Odor intensity was scored by "18 perfumers and experienced researchers" on samples from a fragrance diluter at different gas concentrations.
  - Model: dose-response curve fits, giving intensity from any gas concentration.
  - Accuracy: RMSE 6.22 for single components and 6.69 for mixtures.
  - Kao's stated use is control of "scent diffusion and longevity" and reduced raw-material use.
  - It is a curve-based model, not deep learning.
  - Sources: [ACS](https://pubs.acs.org/doi/10.1021/acs.iecr.9b01225); [Kao news release, 8 January 2020](https://www.kao.com/global/en/newsroom/news/release/2020/20200108-001/); [ResearchGate](https://www.researchgate.net/publication/334583081_Method_for_Predicting_Odor_Intensity_of_Perfumery_Raw_Materials_Using_Dose-Response_Curve_Database)
- The Pyrfume open-data project (Scientific Data 2024) references the Wakayama dataset. — [Pyrfume, Sci Data](https://www.nature.com/articles/s41597-024-04051-z)

**Mane, Takasago, Robertet**
- Contrary lists Mane's WELLMOTION as a competitor-side platform. I found no disclosed ML potency or performance model for Mane, Takasago or Robertet. — [Contrary Research](https://research.contrary.com/company/osmo)

### Inferences
- The big houses almost certainly hold the largest proprietary performance datasets (headspace, GC-O, evaluation-panel scores on blotter, skin and fabric over time). IFF's "decades of measured data" and Givaudan's "Odour Value Map" both imply per-ingredient odor-value (concentration/threshold) tables. Neither has published model details, so any claim that they run deep-learning potency models is **speculation**.
- The industry pattern is that performance knowledge lives in ingredient-level lookup tables such as odor value (concentration ÷ threshold) and diffusion measures. Ingredient-level lookup tables with rule-based aggregation, rather than end-to-end ML, match the Givaudan diffusion-visualization method and Kao's curve database.

### Gaps
- No verified patent from Givaudan, dsm-firmenich, IFF, Symrise, Takasago or Mane explicitly claims ML prediction of odor threshold, intensity, longevity or substantivity. Searches of Google Patents via web search returned only older composition patents on longevity and substantivity (e.g. WO1998047478A1, US20090176690A1), which are not ML.
- The architecture of Philyra, Carto, emotiOn and Science of Performance is undisclosed.
- No compute or cloud disclosures exist for any big house, beyond Philyra being built with IBM Research.

---

## 4. Flavor/food AI and sensor startups relevant to molecule→perception or potency

### Takeaway
Most flavor and food AI companies target formulation or consumer preference rather than molecule-level potency. NotCo discloses the most architecture (the "Generative Aroma Transformer", an encoder-decoder). Aromyx is the main receptor-assay play. None discloses a dedicated intensity or threshold model.

### Cited Findings
- **NotCo (Giuseppe; Generative Aroma Transformer).**
  - GAT is described as a dual-system encoder-decoder transformer trained on historical fragrance formulations and on molecular structures of volatiles. It predicts how molecules interact to create aroma profiles and is offered for flavor and fragrance formulation from text prompts.
  - Giuseppe crawls recipes, USDA data, and FTIR, GC, texturometer and physicochemical databases.
  - A $70M raise (December 2022) funded offering the platform to the wider industry.
  - Sources: [search summary of P&F](https://www.perfumerflavorist.com/flavor/dietary-supplements/news/22915358/how-notco-is-utilizing-artificial-intelligence-to-crack-plantbased-taste-formulations-completes-fragrance-formulations); [The Spoon](https://thespoon.tech/notco-has-created-a-generative-ai-for-flavor-and-fragrance-that-can-create-unique-formulations-with-text-prompts/); [GCI](https://www.gcimagazine.com/brands-products/fragrance-home/news/22924399/perfumegpt-notcos-generative-ai-fragrance-formulator-wants-to-disrupt-scent); [FoodNavigator-USA](https://www.foodnavigator-usa.com/Article/2022/12/12/NotCo-raises-70m-to-offer-AI-platform-to-wider-industry-and-exponentially-accelerate-the-transformation-of-the-plant-based-industry/)
- **Aromyx (EssenceChip).** A disposable biochip carries human olfactory and taste receptors, and an AI database analyzes the responses. At the time of reporting, 138 of about 400 receptors had been cloned, with robotic screening. Contrary puts funding raised at $18.8M. — [FoodNavigator 2017](https://www.foodnavigator.com/Article/2017/12/21/The-Google-Maps-for-taste-and-scent-Aromyx-s-bio-chip-sensor-could-fuel-future-reformulation-it-says/); [FI Global](https://insights.figlobal.com/colours-flavours/artificial-nose-real-results-are-biosensors-the-future-of-flavour-development-); [Contrary Research](https://research.contrary.com/company/osmo)
- **Analytical Flavor Systems (Gastrograph).** Uses "thousands of human testers" to model flavor, aroma and texture perception, i.e. consumer preference. No molecule-level potency model is disclosed. — [IFT Food Technology](https://www.ift.org/food-technology-magazine/4-next-generation-sensory-science)
- **Koniku** (bio-electric sensors; $37M raised) and **Moodify** (reformulation platform; $10.6M raised) are listed as competitors by Contrary. — [Contrary Research](https://research.contrary.com/company/osmo)
- **Givaudan Taste & Wellbeing** has AI tools to identify positive and negative flavor drivers. — [Green Queen](https://www.greenqueen.com.hk/givaudan-unveils-ai-tools-identify-positive-negative-flavour-drivers-for-future-product-development/); [Givaudan digital tools](https://www.givaudan.com/taste-wellbeing/imagine/tools/digital-tools)

### Inferences
- Receptor-assay startups (Aromyx) produce EC50-style dose-response data that could in principle anchor potency models. No public link between their assay data and perceptual threshold prediction was found.

### Gaps
- Ai Palette, Brightseed, Aryballe, Scentian Bio, Ainos, Stratuscent, Noze and Canaery: no potency-relevant disclosures surfaced within the search budget. I believe these are mostly e-nose, consumer-trend or bioactive-discovery companies, but this is unverified.
- NotCo GAT parameter count, dataset size and compute are undisclosed.

---

## 5. Patents on ML-based odor threshold, intensity and performance prediction

### Takeaway
The identifiable ML olfaction patents are Google-origin, now Osmo, and cover odor *quality* and mixture discriminability, with intensity only as an optional output. I found **no granted or published patent that specifically claims ML prediction of odor threshold, intensity, longevity or substantivity** from a major house. Potency-specific ML work surfaces in academic papers instead.

### Cited Findings
- US20220139504A1 (Google, reassigned to Osmo; priority 2019; pending): a GNN for olfactory properties, with optional intensity descriptors and confidence values. — [Google Patents](https://patents.google.com/patent/US20220139504)
- US11009494B2, "Predicting human discriminability of odor mixtures": an NN over structure for mixture perceptual distance. — [Google Patents](https://patents.google.com/patent/US11009494B2/en)
- Symrise/IBM: "first patent granted for fragrance computational creativity" in 2019. The patent number was not given. — [Symrise Philyra](https://www.symrise.com/scent-and-care/competence-platforms/philyra/)
- US 10,775,356, "System and method for scent perception measurements and for construction of a scent database". Surfaced in search; assignee and details not verified. — [USPTO PDF](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10775356)
- Academic potency ML for context (not patents):
  - A transfer-learning GCN→FFNN odor threshold model. — [Heliyon 2023, PMC10589844](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10589844/)
  - Fichtelmann & Westermayr, ordinal odor-strength prediction on more than 2,000 molecules (odorless/low/medium/high) from two public sources. SHAP identified size, polarity, rings and branching as the drivers. RSC Advances 2026, 16:25696. — [arXiv 2512.08683](https://arxiv.org/abs/2512.08683); [RSC Adv](https://pubs.rsc.org/en/content/articlehtml/2026/ra/d6ra01805j)

### Inferences
- The absence of potency-ML patents from the big houses probably reflects a preference for trade secrecy. Contrary notes that the industry's IP culture favors secrecy, and patent searches were limited.

### Gaps
- A proper Google Patents/Espacenet CPC search was not possible within budget. Useful targets: G16C 20/30 and 20/70 with "odor threshold" or "odour value", and G06N with "fragrance longevity". Assignees to check: Givaudan, Firmenich/DSM, IFF, Symrise, Kao, Takasago, P&G, Unilever and Henkel. P&G and Unilever are likely holders of substantivity-on-fabric work (speculative).
- The Givaudan "diffusion measure" patent number and assignee remain unconfirmed.

---

## 6. Compute budgets for industrial olfaction models

### Takeaway
Essentially nothing quantitative is disclosed. The only concrete infrastructure disclosure is Osmo on Google Cloud (Vertex AI, Dataflow, BigQuery with about 15 TB for a 40B-molecule table, and Bigtable). The POM training recipe (about 5k molecules, batch 128, 150 epochs, 1,000-trial Vizier search) implies a small compute footprint. Philyra is an IBM Research collaboration with no disclosed hardware.

### Cited Findings
- Osmo on Google Cloud: Vertex AI training, Dataflow batch inference over large libraries, a BigQuery table of 40B molecules (about 15 TB), Bigtable output. No accelerator counts. — [Google Cloud blog 2023](https://cloud.google.com/blog/products/ai-machine-learning/how-osmo-is-bringing-ai-to-aromas)
- POM training hyperparameters (as above), with a 1,000-trial Bayesian optimization. — [PMC11898014](https://pmc.ncbi.nlm.nih.gov/articles/PMC11898014/)
- Philyra was built by IBM Research with Symrise; no compute details are given. — [Symrise](https://www.symrise.com/newsroom/article/breaking-new-fragrance-ground-with-artificial-intelligence-ai-ibm-research-and-symrise-are-workin/)
- The 2025 intensity model is a 5-layer DNN on 127 features trained on a few thousand (augmented) points. That is trivially small compute. — [PMC12363845](https://pmc.ncbi.nlm.nih.gov/articles/PMC12363845/)

### Inferences
- The bottleneck for industrial potency and performance models is data (human psychophysics, dose-response, GC-O, time-course evaluations), not compute. A POM-scale MPNN on about 5k molecules trains in GPU-minutes to hours (**my estimate, not disclosed**). A 1,000-trial hyperparameter search multiplies that to perhaps hundreds of GPU-hours (estimate). Screening billions of molecules is embarrassingly parallel CPU/GPU inference, which matches Osmo's Dataflow/BigQuery design.
- If Osmo's "olfactory world model" is substantially larger (for example trained on 5M annotations plus GC-MS data), compute could be larger. **Nothing is disclosed**, so treat any figure as speculation.

### Gaps
- No GPU/TPU counts, cloud credits or spend for Osmo, Givaudan, dsm-firmenich, IFF, Symrise/IBM or NotCo.
- No disclosure of whether Osmo uses TPUs, despite its Google origins and cloud relationship.
