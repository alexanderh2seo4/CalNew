# Olfactometer build: components, calibration and validation, safety and ethics (Germany)

Scope note: a builder's reference for a research-grade olfactometer that measures human detection thresholds of pure odorants (ppt to ppm). Research ran in September 2026. Some pages could not be retrieved: PMC and bioRxiv returned CAPTCHA/429 errors, and the EN 13725/ISO full texts are paywalled. Items without a source are marked **[unverified]** or **[estimate]** and sit in Inferences or Gaps. Treat every price as an estimate unless a source is cited.

---

## 1. Concentration generation methods and accuracy (incl. ISO 6145 parts)

### Takeaway
The only generation methods with standardized, documented uncertainty are those in the ISO 6145 series. Permeation (Part 10) reaches about ±2.5% expanded uncertainty at 10⁻⁹–10⁻⁶ mol/mol (ppb–ppm). Diffusion (Part 8) reaches ≤±2% at 10⁻⁹–10⁻³. Both are traceable by weighing. For the ppt range they have to be followed by an MFC dilution stage (Part 7), and each cascade stage multiplies the uncertainty. Bags, syringes and liquid-dilution headspace are cheaper but less accurate, because of adsorption and permeation losses.

### Cited Findings
- The ISO 6145 series covers dynamic preparation of calibration gas mixtures. The parts are: 1 (methods of calibration), 2 (volumetric/piston pumps), 4 (continuous injection), 5 (capillary calibration devices), 6 (critical orifices), 7 (thermal mass-flow controllers), 8 (diffusion), 9 (saturation method) and 10 (permeation). — [ISO 6145-10 via search summary / ISO](https://www.iso.org/standard/25916.html); [ISO 6145-1 preview](https://webstore.ansi.org/preview-pages/ISO/preview_ISO+6145-1-2003.pdf)
- **ISO 6145-10 (permeation):** mole fractions 10⁻⁹ to 10⁻⁶, "relative expanded uncertainty of ± 2.5 %". — [ISO 6145-10:2002](https://www.iso.org/standard/25916.html); [iTeh sample PDF](https://cdn.standards.iteh.ai/samples/25916/9abbcba785e943a9b5e2ec13ed3c630d/ISO-6145-10-2002.pdf)
- **ISO 6145-8 (diffusion):** mole fractions 10⁻⁹ to 10⁻³, relative expanded uncertainty "not greater than ± 2 %". — [ISO 6145-8:2005](https://www.iso.org/standard/36480.html)
- The largest uncertainty contributors for permeation are the permeation-rate determination (by weighing), the carrier and diluent gas flows, and the pressure, temperature and humidity measurements. — [ISO 6145-10 (iTeh sample)](https://cdn.standards.iteh.ai/samples/25916/9abbcba785e943a9b5e2ec13ed3c630d/ISO-6145-10-2002.pdf); [IPQ-LCM Eurachem presentation](https://www.eurachem.org/images/stories/workshops/2011_06_MU/presentations/P23-FDias.pdf)
- **ISO 6145-7 (thermal MFCs):** the standard exists (ed. 2, 2009). I could not read its stated uncertainty range. — [ISO OBP 6145-7](https://www.iso.org/obp/ui/#iso:std:iso:6145:-7:ed-2:en)
- **ISO 6145-2** (piston pumps) was revised in 2014. — [ISO 6145-2:2014](https://www.iso.org/standard/45866.html)
- Some research olfactometers use bubblers as the odor source, meaning air passed through the liquid odorant. Examples are the open-source fMRI olfactometer in HardwareX (blower + valves + bubblers) and a 2025 bioRxiv low-cost olfactometer for single odours and mixtures. — [HardwareX 2025 fMRI olfactometer](https://www.hardware-x.com/article/S2468-0672(25)00086-0/fulltext); [bioRxiv 2025.09.11.675563](https://www.biorxiv.org/content/10.1101/2025.09.11.675563v1.full)
- A classic low-cost, computer-controlled olfactometer design for temporally precise experiments was published by Lundström et al. in Int J Psychophysiol (2010). — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167876010006665); [PubMed 20688109](https://pubmed.ncbi.nlm.nih.gov/20688109/)
- Bag-based dosing: recovery in bags is ordered PTFE > Tedlar > Nalophan. PTFE losses are adsorption-controlled. Nalophan and Tedlar lose by adsorption plus diffusion through the film (details in §3). — [Kasper et al. 2018, J Environ Qual](https://pubmed.ncbi.nlm.nih.gov/29634807/)

### Inferences
- **Getting to ppt:** most odorants have saturated vapour concentrations of 10²–10⁵ ppm. Reaching ppt therefore takes about 10⁶–10¹⁰ total dilution. A single MFC pair gives only about 1:100–1:1000 per stage, so plan for 2–3 cascaded stages. Alternatively, pre-dilute the liquid in an odorless solvent (e.g. 1,2-propanediol, diethyl phthalate, mineral oil) and then apply dynamic dilution. Each stage adds MFC uncertainty (see §2), so a 3-stage cascade of ±1% MFCs gives roughly ±3–5% combined before adsorption losses. **[inference]**
- **Saturator/bubbler + vapour pressure (ISO 6145-9):** accuracy depends on complete saturation (use two saturators in series or a condenser at controlled T) and on the accuracy of the Antoine-equation data. A ±1 °C temperature error changes vapour pressure by several percent, so temperature control is the key spec. **[inference; general physical chemistry]**
- **Liquid dilution + static headspace (bottle/Sniffin'-Stick style):** the cheapest option and easy to cascade (1:2 or 1:3 steps in solvent). The headspace concentration depends on Raoult/Henry non-ideality in the solvent, so it must be measured (GC or PID), not calculated. It is fine for relative thresholds, weak for absolute ppt claims. **[inference]**
- **For an ML dataset,** the recommended architecture is: permeation tube or diffusion vial (gravimetric traceability, ISO 6145-8/-10), then 2-stage MFC dilution (ISO 6145-7), then a sniff port, with a PID/GC check of every stock concentration. Use saturators only for compounds where permeation tubes are unavailable. **[inference]**

### Gaps
- Numerical uncertainty ranges for ISO 6145-7 (MFC) and ISO 6145-9 (saturation) are not in accessible previews.
- ASTM E679 and ISO 13301 method details (forced-choice ascending series; ISO 13301 describes a 3-AFC ascending concentration series with a gas-dilution apparatus) could not be retrieved in this pass. Check the full texts.

---

## 2. Components: specs, vendors, prices (EU/DE where possible)

### Takeaway
MFCs are the dominant cost. New thermal MFCs cost roughly €1.2k–3k each [estimate]. Used Bronkhorst EL-FLOW Select units sell for about $470–520 on the secondary market. Alicat MC controllers list at about $1,400+, with ±0.5% of reading accuracy and about 30 ms response. Low-cost open-source olfactometers replace MFCs with blowers or bubblers plus Arduino-driven solenoid valves.

### Cited Findings
- **Bronkhorst EL-FLOW Select** (NL): digital thermal MFM/MFC, modular, with digital diagnostics and fieldbus. There is also a cheaper **EL-FLOW Base** line for gas. — [Bronkhorst EL-FLOW Select datasheet](https://products.bronkhorst.com/media/cp3lfvo1/el-flow-select_en.pdf); [EL-FLOW Base](https://www.bronkhorst.com/products/gas-flow/el-flow-base/)
- Used Bronkhorst EL-FLOW Select F-201CV (100–500 sccm) sell for about $467–519 on eBay, and are also stocked by the German reseller Lagerwerk GmbH. — [eBay listing](https://www.ebay.com/itm/356063312250); [Lagerwerk](https://www.lagerwerk.com/en/test-lab-metrology-equipment/measuring-tools/24478/bronkhorst-el-flow-select-f-201cv-mass-flow-controller-300sccm/sih4/v1.22i)
- **Alicat MC series:** ±0.5% of reading or ±0.05% of full scale, control response as fast as 30 ms. An Alicat Standard MFC price was seen at about $1,424.50 (configuration dependent). Alicat runs an online store. — [Alicat MFC](https://www.alicat.com/products/gas-flow/mass-flow-controller/); [Alicat store](https://store.alicat.com/products/flow-controller); [Cole-Parmer MC series](https://www.coleparmer.com/p/alicat-mc-series-mass-flow-controllers-sccm/89851)
- Arduino control of MFCs is documented: a low-cost microcontroller unit drives two MFCs at once. — [ResearchGate: Low cost MFC control unit](https://www.researchgate.net/publication/336138329_Low_cost_MFC_control_unit_using_microcontoller)
- The open-source fMRI olfactometer (HardwareX 2025) uses an Arduino-compatible microcontroller, a 12 V supply with a converter board for valve voltages, a blower-based airflow generator, multichannel air valves, long delivery tubing and bubbler odour sources. Up to 5 more lines can be added "only adding more electrovalves and rewriting a few lines" of code. — [HardwareX](https://www.hardware-x.com/article/S2468-0672(25)00086-0/fulltext)
- Janelia's older Arduino olfactometer firmware is archived on GitHub ("Obsolete. For historical reference only"). — [GitHub janelia-idf/arduino_olfactometer](https://github.com/janelia-idf/arduino_olfactometer)
- Research olfactometer example: Burghart OL023 provides birhinal stimulation with up to 12 odorants (max 6 per nostril side). Burghart (Wedel, DE) also sells Sniffin' Sticks. — [Burghart Olfaktometer/Gustometer](https://www.burghart-mt.de/medizintechnik/olfaktometer_gustometer/)

### Inferences (component shortlist; prices are **[estimate]**, 2026 list-price ballpark, excl. VAT)
- **MFCs:** use a 0–10 or 0–20 L/min carrier/diluent MFC plus 0–100 sccm or 0–1 L/min odour-line MFCs.
  - Bronkhorst EL-FLOW Select or Prestige: ~€1.5–3k new.
  - Vögtlin red-y smart (CH): ~€0.8–1.5k.
  - Alicat MC: ~€1.4–2.5k.
  - Sierra SmartTrak, MKS GE50A: ~€1.5–3k.
  - Used Bronkhorst: ~€400–600.
  - Choose models with stainless-steel wetted parts and FKM/Kalrez seals. FKM (Viton) can sorb odorants, so specify FFKM or PTFE-sealed versions where available.
- **Valves:**
  - NResearch PTFE isolation/pinch valves (~€150–300 each).
  - Takasago PTFE-diaphragm valves (~€50–150).
  - Bürkert Type 6724/6712 or 0127 rocker valves with PTFE/FFKM wetted parts (~€100–300; DE vendor).
  - Parker Series 3/9; SMC LVM.
  - For odour lines, prefer media-separated rocker or pinch valves so that odorant never contacts the plunger or elastomer.
- **Tubing/fittings:**
  - PFA or FEP tubing, 1/8"–1/4" OD (~€5–15/m).
  - Bola (Bohlender, DE) PTFE/PFA fittings and stopcocks.
  - Swagelok 316L, preferably electropolished, or SilcoNert/Sulfinert-coated for sulphur compounds (see §3). Budget ~€20–60 per fitting.
- **Odourless air:**
  - Option A: oil-free compressor (e.g. Jun-Air/Bambi silent) → coalescing filter → activated carbon (plus optional Purafil/KMnO₄ media) → HEPA → MFC.
  - Option B: zero-air generator (Parker, Peak, LNI; ~€3–8k).
  - Option C: synthetic air cylinders (~€50–150 per 50 L bottle refill).
- **Humidification:** a bubbler in the carrier line or a Nafion/Perma Pure humidifier. Target 40–60% RH to avoid nasal drying.
- **Sniff port:** a glass (borosilicate) or PTFE nose cone/funnel, with a 1:1 or 2-port layout to prevent the panelist from judging by flow cues.
- **Control and software:**
  - Teensy 4.x or Arduino (~€30–50) plus MOSFET/ULN2803 valve drivers.
  - An NI USB-6001/6002 DAQ (~€300–700) if analog MFC control is needed. Digital RS232/Modbus/Profibus MFC control via Python (pyserial, propar for Bronkhorst, alicat package) avoids the DAQ.
  - PsychoPy for staircase or 3-AFC procedures (QUEST/up-down), synchronized to valve switching.

### Gaps
- No verified 2026 new-list prices for Bronkhorst, Vögtlin, Sierra, MKS, Bürkert, NResearch or Takasago. These vendors quote on request, so ask for academic quotes.
- The bioRxiv 2025 low-cost olfactometer BOM and cost could not be fetched (HTTP 429). Retry: https://www.biorxiv.org/content/10.1101/2025.09.11.675563v1.full

---

## 3. Validation instruments and methods (PID, GC, tracer gas; rise time, stability, accuracy, carry-over)

### Takeaway
EN 13725:2022 calibration checks every dilution step with a traceable tracer gas: CO measured by a calibrated IR analyser, or propane measured by FID. The acceptance limits are **accuracy A_d < 0.20** and **instability I_d < 5%**, reference uncertainty below 3%, and calibration at least annually. For temporal dynamics and carry-over, the de facto tool is a fast miniPID (Aurora 200B/200C, 0.6–1 ms rise time). Low-cost ppb PIDs (Ion Science MiniPID 2 PPB, Alphasense PID-AH2) cover concentration checks down to about 1–20 ppb isobutylene-equivalent. GC-MS or GC-FID is needed for absolute verification at sub-ppb levels.

### Cited Findings
- **EN 13725:2022 calibration (section 5.4.2 / 6.5.5 / Annex C):**
  - Calibration at least once a year.
  - Tracer, e.g. carbon monoxide reference mixtures with expanded uncertainty < 3%, measured by a continuous IR analyser that is also < 3%.
  - Accuracy and instability determined for every dilution the device offers.
  - Pass criteria: A_d < 0.20 (accuracy) and I_d < 5% (instability).
  - Procedure: fill bags with CO reference mixtures, dilute with air in the olfactometer, and read the output with a calibrated CO analyser. The example device covers dilution ratios up to 1:100,000.
  - Source: [Trescal CIM2023 poster](https://www.trescal.com/wp-content/uploads/2023/06/CIM2023-Trescal-POSTER-REF-190-Calibration-of-Olfactometers-1.pdf)
- Propane-in-N₂ CRM with FID is also used to check the individual dilution settings against the EN 13725 accuracy and instability requirements. — [search summary of EN 13725 calibration practice; Olfasense/LOD sources](https://www.lodsrl.it/en/news/uni-en-13725-2022-how-did-the-standard-change)
- n-Butanol (CAS 71-36-3) is the EN 13725 reference odorant. The 2022 revision adds provision for a second reference odorant (SROM). — [LOD Srl: UNI EN 13725:2022 changes](https://www.lodsrl.it/en/news/uni-en-13725-2022-how-did-the-standard-change); [Update on revised EN 13725:2021 (ResearchGate)](https://www.researchgate.net/publication/351942376_Update_on_the_revised_EN_137252021)
- EN 13725:2021/2022 panel monitoring:
  - ITE data used for panel qualification must be no older than 12 months.
  - The number of ITE values for monitoring is fixed at n = 12.
  - Source: [olores.org](https://www.olores.org/en/techniques/dynamic-olfactometry/1210-what-is-new-in-the-revised-en13725-2021-standard)
- A statistical analysis of EN 13725 variance components is available for estimating inter-lab and inter-panel spread. — [Atmos Environ, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1352231013009771)
- **Aurora Scientific miniPID:** the 200B has a true frequency response of 330 Hz and a 0.6 ms rise time. The 200C has a 1 ms rise time. — [Aurora 200B](https://aurorascientific.com/products/neuroscience/200b-minipid/); [Aurora 200C](https://aurorascientific.com/products/neuroscience/200c-minipid/)
- **Ion Science MiniPID 2 PPB:** 0–40 ppm range, 1 ppb sensitivity (10.6 eV lamp). — [Ion Science MiniPID 2 PPB](https://www.ionscience.com/products/minipid-2-pid-ppb/)
- **Alphasense PID-AH2:** about 20 ppb isobutylene detection level (from a partial datasheet excerpt; verify against the full datasheet). — [DirectIndustry PID-AH2 datasheet](https://pdf.directindustry.com/pdf/alphasense/pid-ah2/16860-1025987.html); [Alphasense PID sensors](https://www.alphasense.com/products/view-by-target-gas/pid-sensors)
- **Chemical Senses 2019, "Novel Olfactometer for Efficient and Flexible Odorant Delivery":**
  - Characterized with an Aurora 200B miniPID placed 8–10 cm from the outlet, with 30 kPa channel pressure and an 8 L/min carrier stream.
  - GC-MS over a longer period of use showed a 5.9% drop in signal intensity.
  - Source: [Chem Senses 44(3):173](https://academic.oup.com/chemse/article/44/3/173/5292343)
- Another olfactometer showed "negligible memory effect" and a 10–90% rise time of about 300 ms, measured with a PID. — [search result summary; see Lundström 2010 / ResearchGate PID figure](https://www.researchgate.net/figure/Odor-Delivery-Controlled-by-the-Olfactometer-A-Sample-traces-of-PID-measurement-of-AA_fig5_261372949)

### Inferences (validation protocol for a self-build)
1. **Dilution accuracy:**
   - Run propane (FID) or CO (IR) through every dilution step, following EN 13725 Annex C.
   - Compute A_d and I_d, and require A_d < 0.20 and I_d < 5%, the same criteria as commercial EN 13725 devices.
   - Accredited labs (e.g. Trescal, DAkkS labs in DE) can do this as a service.
2. **Odorant-specific recovery:**
   - Tracer gases do not adsorb, but real odorants do.
   - For each odorant, verify the output concentration at 2–3 dilution levels with PID (ppb range) or with sorbent-tube sampling (Tenax TA) plus TD-GC-MS/FID for sub-ppb levels.
   - Report recovery as a percentage of nominal.
3. **Rise time and stability:**
   - Measure 10–90% rise and fall times with a miniPID at the sniff port using a high-concentration surrogate such as ethyl acetate or isoamyl acetate.
   - Measure steady-state CV over 30–60 s. Targets **[inference]**: < 300 ms rise, < 5% CV.
4. **Carry-over:**
   - Present high → blank → low sequences.
   - The PID blank after the high concentration should return to baseline (< LOD) within the planned inter-stimulus interval.
   - For sticky compounds, GC-MS on blank-air sorbent tubes after purge.

### Gaps
- The exact EN 13725 definitions and formulas for A_d and I_d, the sniff-port flow requirement (commonly cited as ≥ 20 L/min per port **[unverified]**) and the n-butanol panel acceptance window (commonly 20–80 ppb / 62–123 µg/m³ **[unverified]**) were not confirmed from the standard text.
- No miniPID or Ion Science price was found. Aurora quotes on request.

---

## 4. Material odour-neutrality, adsorption and carry-over

### Takeaway
Fluoropolymers (PTFE/PFA/FEP) and passivated or coated stainless steel are the accepted wetted materials. EN 13725:2022 explicitly requires stainless steel with properties that avoid poor recovery (e.g. passivated), especially for H₂S and reduced sulphur compounds. Nalophan and Tedlar bags lose odorants through both adsorption and permeation, and PTFE loses only through adsorption. Keep sticky odorants (thiols, amines, acids, phenols, musks) in dedicated lines, and use heat and long purges.

### Cited Findings
- Kasper et al. (2018, J Environ Qual) studied Nalophan, Tedlar and PTFE bags with acetic, propanoic, butanoic and 3-methylbutanoic acid, H₂S, methanethiol, dimethyl sulfide, trimethylamine and 4-methylphenol. Findings:
  - Recovery was PTFE > Tedlar > Nalophan.
  - PTFE losses were adsorption-controlled.
  - Nalophan and Tedlar losses combined adsorption and diffusion.
  - Heating PTFE bags to 57 °C during evacuation improved recovery to 71.6–98.8% after 48 h in 5 L bags.
  - Sources: [PubMed 29634807](https://pubmed.ncbi.nlm.nih.gov/29634807/); [Wiley JEQ](https://acsess.onlinelibrary.wiley.com/doi/10.2134/jeq2017.07.0289)
- Comparative study of PTFE vs Nalophan vs Tedlar with wastewater samples:
  - Sulphur compounds lost less than 5% in PTFE after 24 h.
  - Odour losses reached 60% in Nalophan and 35% in Tedlar after 24 h.
  - Sources: [olores.org](https://olores.org/index.php?option=com_content&view=article&id=382:reducing-odour-sample-degradation-a-comparative-study-of-nalophan-tedlar-and-ptfe-sample-bags&catid=80&Itemid=422&lang=en); [ResearchGate](https://www.researchgate.net/publication/276204854_Reducing_Odour_Sample_Degradation_A_Comparative_Study_of_Nalophan_TedlarR_and_PTFE_Sample_Bags)
- Volatile sulphur compounds in Nalophan bags show permeability and adsorption effects that depend on storage time. — [Biosystems Engineering, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1537511019308700)
- A 2025 study measured how storage conditions affect odorant recovery in Nalophan bags. — [Appl Sci 15(17):9258](https://www.mdpi.com/2076-3417/15/17/9258)
- EN 13725:2021/2022 materials changes:
  - The list of permitted materials now includes titanium and aluminium, for sampling hoods and wind tunnels only.
  - Stainless steel must have technical properties that avoid inadequate recovery (e.g. passivated), "in particular of H₂S and reduced sulphur compounds".
  - Source: [olores.org](https://www.olores.org/en/techniques/dynamic-olfactometry/1210-what-is-new-in-the-revised-en13725-2021-standard)
- A Chem Senses 2019 olfactometer showed a 5.9% signal drop over long use (GC-MS). — [Chem Senses 44(3):173](https://academic.oup.com/chemse/article/44/3/173/5292343)

### Inferences
- **Material ranking** **[inference, consistent with the cited bag studies and EN 13725]**:
  - Best: PFA ≈ FEP ≈ PTFE, and glass. PFA is smoother and less porous than PTFE, which helps for tubing.
  - Next: electropolished, passivated or Silco-coated 316L.
  - Avoid: silicone, PVC, polyurethane, Tygon, FKM elastomers and nylon in odour paths. Silicone strongly absorbs hydrophobic odorants such as musks and terpenes and acts as a reservoir that releases them later.
- **Carry-over mitigation** **[inference]**:
  - Use one line and one valve per concentration step, or at least per odorant.
  - Mix into the diluent as close to the nose cone as possible so that the shared path is short.
  - Run a continuous clean-air purge through the port between trials, and use a heated manifold (40–60 °C) for semi-volatiles.
  - Give each odorant its own sniff funnel or cone and bake glassware between compounds.
  - Leave inter-stimulus intervals ≥ 30 s for adaptation and purge.
  - For sticky compounds (thiols, amines, musks, vanillin-type phenolics), dedicate complete sub-assemblies and verify blanks by PID or GC before each session.

### Gaps
- I found no systematic study of adsorption in PFA/FEP tubing specifically for musks or thiols. Look for Chem Senses and Flavour Fragr J papers, and consider building a small recovery test.

---

## 5. Odour-neutral environment (room, booth, CO₂)

### Takeaway
EN 13725:2022 sets a minimum room temperature set-point of 21 °C, adds upper and lower RH limits, and has dropped the old recommended 25 °C maximum. Panel quality is tracked with n-butanol ITE data (at most 12 months old, n = 12 for monitoring). A 2024 study shows that uncomfortable room conditions shift n-butanol thresholds. The standard's exact CO₂ limit was not confirmed here.

### Cited Findings
- EN 13725:2021/2022 room changes: minimum set-point of 21 °C, upper and lower RH limits introduced, recommended 25 °C maximum removed. — [olores.org](https://www.olores.org/en/techniques/dynamic-olfactometry/1210-what-is-new-in-the-revised-en13725-2021-standard)
- A study of uncomfortable environmental conditions and n-butanol detection thresholds (dynamic olfactometer vs room air) used a baseline of 22–23 °C, 2800 K warm light, 45 dB fan noise, 415 ppm CO₂ and 34–42% RH. Its 20 non-smoking assessors were trained to EN 13725:2022. — [ScienceDirect 2024, S2950362024000328](https://www.sciencedirect.com/science/article/pii/S2950362024000328)
- The EN 13725 update overview is available on ResearchGate. — [Update on revised EN 13725:2021](https://www.researchgate.net/publication/351942376_Update_on_the_revised_EN_137252021)

### Inferences
- Practical room spec **[inference; aligns with EN 13725 and ISO 8589 intent]**:
  - Separate, well-ventilated room at slight positive pressure, supplied with carbon-filtered air.
  - Keep CO₂ < 1000–1500 ppm. Check with a cheap NDIR CO₂ logger (€100–200).
  - 21–25 °C, 40–60% RH.
  - Odourless surfaces: stainless steel, glass, melamine; no carpets or fresh paint.
  - Local exhaust at the sniff port to extract exhaled and presented odour.
  - Panelists: no perfume, no smoking or eating for 30 min before sessions.
- ISO 8589 (sensory booth design) could not be retrieved. It generally specifies individual booths, controlled lighting and odour-free ventilation. **[unverified detail]**

### Gaps
- The EN 13725 room CO₂ limit and ISO 8589 numerical requirements were not confirmed (paywalled).

---

## 6. Safety and regulation in Germany (AGW/MAK, GefStoffV, MDR, ethics at LMU)

### Takeaway
For healthy-volunteer threshold research, the LMU Medical Faculty ethics committee requires an application via **ethikPool** (online since 15 April 2024). Non-AMG/MPDG studies can obtain a "no advisory obligation" certificate, or a full opinion under Berufs-/Fakultätsrecht. Published fees (€100–3,500) apply only to AMG/CTR and MDR/MPDG clinical trials. A self-built research olfactometer used for psychophysics, not diagnosis, is likely outside the MDR. For comparison, commercial Sniffin' Sticks for clinical smell testing are class I medical devices.

### Cited Findings
- The LMU Medical Faculty Ethikkommission:
  - Since 15 April 2024, applications under Berufs-/Fakultätsrecht are submitted only through the ethikPool portal (www.ethikpool-lmu.de).
  - Required documents: full study protocol (templates for prospective and interventional studies), participant information and consent in German, a data-protection clause, written approval from the heads of the involved institutions, a signed cover letter, and all study materials.
  - From 1 July 2025, the "One Study – One Opinion" standardized procedures are mandatory for first opinions.
  - Sources: [LMU Nicht AMG/MPDG](https://www.med.lmu.de/de/fakultaet/wer-wir-sind/gremien-kommissionen/ethikkommission/nicht-amg-mpdg/); [LMU Ethikkommission](https://www.med.lmu.de/de/fakultaet/wer-wir-sind/gremien-kommissionen/ethikkommission/); [Umstellung Antragstellung](https://www.med.lmu.de/de/fakultaet/wer-wir-sind/gremien-kommissionen/ethikkommission/umstellung-antragstellung/)
- A "no advisory obligation" (keine Beratungspflicht) certificate is also requested via ethikPool before the project starts. — [LMU Wissenswertes](https://www.med.lmu.de/de/fakultaet/wer-wir-sind/gremien-kommissionen/ethikkommission/wissenswertes/)
- Fees apply to AMG/CTR and MPG/MDR/MPDG clinical trials:
  - AMG monocentric €100–3,500; AMG multicentric €200–3,500; MDR/MPDG/IVDR €100–3,500; biobank add-on €500.
  - A fee-reduction request must be submitted with the first application.
  - No fee is listed for non-AMG/MPDG studies.
  - Source: [LMU Gebühren](https://www.med.lmu.de/de/fakultaet/wer-wir-sind/gremien-kommissionen/ethikkommission/gebuehren/)
- Ethics office contact: 089-4400 55191, ethikkommission@med.uni-muenchen.de. — [LMU Ethikkommission](https://www.med.lmu.de/de/fakultaet/wer-wir-sind/gremien-kommissionen/ethikkommission/)
- Other LMU faculties have their own ethics committees, e.g. Economics. Psychology (Fakultät 11) also has one **[unverified]**. — [LMU Econ Ethikkommission](https://www.econ.lmu.de/de/forschung/ethikkommission/)
- Sniffin' Sticks and Taste Strips (Burghart) are medical devices of risk class I under the MDD. — [Burghart Sniffin' Sticks](https://www.burghart-mt.de/medizintechnik/sniffin_sticks_und_taste_strips/)
- If a device study falls under the MDR/MPDG, LMU has a separate route (klinische Prüfung nach MPDG/MDR). — [LMU MPDG/MDR](https://www.med.lmu.de/de/fakultaet/wer-wir-sind/gremien-kommissionen/ethikkommission/klinische-pruefung-nach-mpdg-mdr/)

### Inferences
- **MDR:** a device is a medical device when its manufacturer-assigned intended purpose (Zweckbestimmung) is medical, such as diagnosing smell disorders. An olfactometer built and used only to measure population odour thresholds for a dataset has no medical purpose, so it is most likely **not** an MDR device. Document this intended purpose in the protocol. If clinical diagnosis of hyposmia is ever added, MDR/MPDG applies. **[inference; confirm with the ethics office]**
- **Electrical safety:**
  - Use low-voltage DC (12–24 V) valves and a CE-marked mains power supply.
  - Keep mains wiring out of the self-built parts.
  - Have the device checked by LMU electrical safety (DGUV V3 inspection) before use with participants. **[inference]**
- **Exposure limits (AGW/MAK):**
  - Threshold testing exposes panelists to ppt–ppb levels for seconds. Most AGW values (TRGS 900) are in the ppm range, so they will usually not be approached.
  - Check the stock and saturated-headspace concentrations of each odorant against TRGS 900 AGW / DFG MAK. This matters especially for high-toxicity odorants: H₂S (AGW 5 ppm **[unverified]**), thiols, amines, and aldehydes such as acrolein or formaldehyde.
  - Also check CMR classification. Avoid carcinogens (e.g. some aldehydes) or justify them in the ethics application.
  - Add hardware interlocks or flow limits so that a valve failure cannot deliver undiluted headspace. **[inference]**
- **GefStoffV:** the handling lab needs:
  - a Gefährdungsbeurteilung (risk assessment, §6 GefStoffV),
  - an up-to-date Gefahrstoffverzeichnis (hazardous substances register),
  - Betriebsanweisungen (operating instructions) with staff instruction,
  - fume-hood work for neat odorants and waste disposal via the LMU route.
  - **[inference; standard German lab practice]**
- **Panelist compensation:** typical German university rates are about €10–15/h **[estimate]**. Participant payments may be tax-relevant, so check LMU finance rules.

### Gaps
- TRGS 900 AGW values for specific candidate odorants were not retrieved. Look them up at baua.de/TRGS-900 and in the GESTIS database.
- I did not confirm which LMU ethics committee has jurisdiction for a non-medical-faculty researcher (Medical Faculty vs Psychology/other faculty committee).
- I found no authoritative German source that explicitly classifies research olfactometers under the MDR.

---

## 7. Build cost tiers vs commercial instruments

### Takeaway
Commercial EN 13725 olfactometers (Olfasense TO8 evolution in 4- or 6-station versions, Scentroid SC300/SC300P) are quote-only, and no public price was found. A self-build ranges from a few hundred euros (bottles or bags) to roughly €10–25k for an MFC cascade with PID validation **[estimate]**. External EN 13725 calibration (CO/propane tracer) is available as an accredited service.

### Cited Findings
- The Olfasense TO8 evolution comes in 4- or 6-station versions and meets EN 13725:2022. No price is published. — [Olfasense TO8 evolution](https://www.olfasense.com/odour-measurement-equipment/instruments/to8-evolution-olfactometer/); [St. Croix Sensory listing](https://www.fivesenses.com/equipment/olfasense/olfasense-to-8-evolution-olfactometer/)
- The Scentroid SC300 is a portable olfactometer. The SC300P is a scientific version with EEG/fNIRS capability. No prices are published. — [Scentroid SC300](https://scentroid.com/products/olfactometers/sc300-portable-olfactometer/); [Scentroid SC300P](https://scentroid.com/products/olfactometers/sc300p-scientific-olfactometer/)
- Burghart (DE) sells research and clinical olfactometers (e.g. OL023) and Sniffin' Sticks. No prices are online. — [Burghart](https://www.burghart-mt.de/medizintechnik/olfaktometer_gustometer/)
- Accredited olfactometer calibration against EN 13725:2022 §5.4.2 is offered as a lab and on-site service (e.g. Trescal Spain, ENAC-accredited). — [Trescal poster](https://www.trescal.com/wp-content/uploads/2023/06/CIM2023-Trescal-POSTER-REF-190-Calibration-of-Olfactometers-1.pdf)
- Used MFCs cost about $470–520 each, and a new Alicat MFC about $1,400+. — see §2 sources.

### Inferences (cost tiers — all **[estimate]**, excl. VAT, 2026)

| Tier | Concept | Main items | Est. cost |
|---|---|---|---|
| Minimal | Liquid dilution series in odourless solvent, in glass sniff bottles or PTFE squeeze bottles (Sniffin'-Stick style), or PTFE/Nalophan bags filled by gas-tight syringe | Amber glass bottles, Hamilton gas-tight syringes (~€100–200 each), PTFE bags (~€30–80 each), analytical balance access, pipettes, 1 low-cost PID (Alphasense/Ion Science ~€300–800 plus electronics) | €0.5–2.5k |
| Mid | 2–4 channel dynamic olfactometer: zero-air, 1 carrier MFC plus 2–4 odour MFCs (used or low-cost), saturators or permeation vials in a thermostated block, PTFE valves, PFA tubing, glass nose cone, Teensy plus Python/PsychoPy, ppb-PID for QC | MFCs €2–8k; valves €0.5–1.5k; fittings/tubing €0.5–1.5k; air supply/filters €0.5–3k; thermostat/oven €0.5–2k; PID €0.5–3k | €5–20k |
| High | EN 13725-style: cascade dilution to ≥ 1:10⁵–10⁶, multi-port, electropolished SS/PFA, heated manifold, miniPID, annual tracer-gas calibration, booths and odour-free room | Above ×2–3, plus Aurora miniPID (~€5–10k), external calibration (~€1–3k/yr), TD-GC-MS access (core facility), room HVAC/carbon filtration | €25–60k+ |
| Commercial | Olfasense TO8, Scentroid SC300, Burghart OL-series | Quote only | Typically €40–100k+ **[unverified; commonly reported range, no source found]** |

### Gaps
- No public price was found for the TO8, SC300 or Burghart olfactometers. Request quotes (Olfasense is in Kiel, DE; Burghart is in Wedel, DE).
- The "Burghart OM6b" model name was not found. The current Burghart research model found is the OL023.
