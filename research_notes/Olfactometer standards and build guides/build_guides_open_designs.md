# Olfactometer build guides and open-source designs (human psychophysics + transferable animal designs)

Research date: 2026-09-28. Method: Europe PMC API (full-text XML for open-access papers), bioRxiv full text, publisher/vendor pages, GitHub/Zenodo/Mendeley repositories. PubMed/PMC web pages were behind a captcha for the fetch tool, so PMC-hosted papers were read via Europe PMC full text (same content). "OA" = open access. Paywalled items are marked; where only the abstract was available this is stated.

---

## Q1. Which published human-olfactometer build guides are most detailed, and what does each specify?

### Takeaway
Two open-access papers give the most detailed, reproducible build instructions for humans: Lundström et al. 2010 (author manuscript on PMC, with part numbers, prices and PID/GC-MS validation) and Doyle et al. 2025 (bioRxiv, step-by-step Arduino build with PID validation, about €1,700). Johnson & Sobel 2007 is the key paywalled paper for *known output concentrations* (air dilution with a characterised saturator canister; its LabVIEW code is on Zenodo). For threshold work specifically, AutomOT (Surakka et al. 2025, OA) is the closest recent human design. It uses mass flow controllers (MFCs), a stainless-steel odor source and two inline PIDs, and gives a verified dilution scheme.

### Cited Findings

**A. Johnson BN & Sobel N (2007). "Methods for building an olfactometer with known concentration outcomes." J Neurosci Methods 160(2):231–245. doi:10.1016/j.jneumeth.2006.09.008. Paywalled (not OA in Europe PMC).**
- Five-channel **air-dilution** olfactometer. It generates neat odorants and binary mixtures "at a range of known concentrations" and comes with detailed instructions and part selections — [Europe PMC abstract / PubMed 17081618](https://doi.org/10.1016/j.jneumeth.2006.09.008)
- Core element is an **odorant canister** that is cheap, durable, has minimal odor adherence and produces a consistent end-vapor: "by flowing a given carrier gas at a given flowrate through a given odorant in this canister, the same end-vapor is achieved". Flow→concentration outcomes are tabulated for several common odorants so that known concentrations can be produced "without expensive analytical machinery" — [abstract](https://doi.org/10.1016/j.jneumeth.2006.09.008)
- Secondary sources describe it as having **controllable flow, humidity and temperature** — [search summary citing Hayes et al. 2013 / ResearchGate record](https://www.researchgate.net/publication/6714551_Methods_for_building_an_olfactometer_with_known_concentration_outcomes). (Uncertain: I could not verify from the full text the canister material, MFC models, or whether the delivery is by nasal mask.)
- **Code:** "LabVIEW code for olfactometer described in Johnson and Sobel", on Zenodo (Olfactometer.zip; main VI "OLFACTOMETER" plus sub-VIs and example experiments) — [Zenodo 3874197](https://zenodo.org/records/3874197)
- Lundström et al. (2010) point to Johnson and colleagues (2007) for how to add heating and humidity — [Lundström 2010 PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)

**B. Lundström JN, Gordon AR, Alden EC, Boesveldt S, Albrecht J (2010). "Methods for building an inexpensive computer-controlled olfactometer for temporally-precise experiments." Int J Psychophysiol 78(2):179–189. doi:10.1016/j.ijpsycho.2010.07.007. Journal version paywalled; free NIH author manuscript PMC2967213. Monell Chemical Senses Center.**
- Built almost entirely from off-the-shelf parts and controlled by E-Prime (or Presentation, SuperLab, PowerLab). Presents solid or liquid odor sources. The paper includes a parts list with prices (October 2009) and **PID onset/concentration curves plus GC/MS showing a 5.9% signal-intensity drop over longer use** — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)
- **Architecture:** compressor or house air → filtration (dry, odor-free) → pressure regulator with bleed → Cole-Parmer multitube flowmeter frames: eight 5.0 L/min tubes for odor channels plus one 1.15 L/min tube for the **continuous-flow (CF) line** → miniature manifold-mounted **3-way solenoid valves** (AutoMate Scientific; 1.5–4.0 ms lag, "nearly inaudible click"), driven by **ValveLink 8.2** controllers (up to 64 valves) → check valve → odor reservoir → check valve → PTFE nosepiece — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)
- **Tubing:** 1/8" ID polyurethane upstream of the odor. After the odor reservoirs, **1/16" ID fluoropolymer (PTFE/PFA/FEP)**. PTFE thread tape on all threads, because leakage is "a primary concern" — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)
- **Why 3-way and not 2-way valves:** with 2-way valves, pressure builds behind the closed valve and is released on opening as a felt **air puff** (a tactile cue). 3-way valves only redirect a continuous flow, and exhaust from unactuated valves flushes residual odor — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)
- **Check valves** (Smart Products 204204PB/214214PB) before and after each reservoir and at each nosepiece inlet. They prevent back-flow and cross-channel contamination and keep lines pressurised, which shortens stimulus onset — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)
- **Reservoirs:** Nalgene polycarbonate jars with a PTFE block in the lid for threaded fittings, or a custom glass reservoir for liquids. The authors warn that aerosol can form and contaminate downstream parts — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)
- **Flows:** 3 L/min total (1.5 L/min per nostril) with a CF line of 0.5–1 L/min that masks switching puffs. Keep flow **<5 L/min per nostril**. With a mask, up to 8 L/min before discomfort. At 3 L/min dry air, no build-up of irritation over 40 min (compared in the paper with 8 L/min heated, humidified air from the Burghart OM6b) — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)
- **Not heated or humidified** by design, to save cost and complexity — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)
- **Validation:** miniPID 200A (Aurora Scientific; 0.6 ms update) sampled at 2 kHz 10" downstream of the nosepiece. 20× 1 s and 3 s stimuli at 3 and 5 L/min, plus a 10-min stability run — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/). (I did not extract the exact onset and rise-time numbers.)
- **Cost items:** custom cabinet (Rankin Automation "LUNDSTROM-BHV-3") $1,000. ValveLinks are "the largest individual cost". The compressor is a WOB-L piston type (40–50 dB, so it needs acoustic isolation) — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)
- Related patent: "MRI compatible and air-actuated olfactometer" (Lundström & Gordon; US 8,899,095) — [USPTO](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8899095)

**C. Doyle C, Wang J, Galliano E, Guillaume C (2025). "A low-cost and open-source olfactometer to precisely deliver single odours and odour mixtures." bioRxiv doi:10.1101/2025.09.11.675563. OA preprint (peer-reviewed status unknown as of 2026-09).**
- **Design:** continuous carrier (1 L/min) plus **4 modules**. Each module has one solvent bottle and one odor bottle (0.3 L/min per module). Bottles are pressurised and sealed until the valve opens, then odorised air merges into the carrier. For mixtures, the solvent bottles of the other modules are opened, so the number of open bottles is constant and pressure stays matched — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.09.11.675563v1.full)
- **Named parts:** MGF medical compressor (S-OF100-003-MS2) or cylinder or house air. Two pressure regulators (carrier and odor paths). Key Instruments flowmeters 25102A13BVBN. SMC speed controllers AS1211F-M5-04. **Lee Company LHDB1262245D solenoid valves**. 40 mL **brown glass** bottles with silicone-septum caps and needle inlets/outlets. 4 mm/6 mm polyurethane or polyether push-fit tubing — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.09.11.675563v1.full)
- **Electronics:** Arduino-compatible board programmed in the Arduino IDE. Custom valve-driver boards (2 valves each) and power-converter boards (12 V → 2.8 V hold and 7 V open lines, i.e., spike-and-hold). Schematics and step-by-step assembly are in the paper — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.09.11.675563v1.full)
- **Cost:** about **£1,500 / €1,700 / $2,000**, excluding compressor and PC. The only specialised step is soldering — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.09.11.675563v1.full)
- **Validation (miniPID 200B):** 5% methyl tiglate in diethyl phthalate. Peak 83.86 ± 1.25 mV, plateau 25.48 ± 0.30 mV, latency 65.72 ± 1.81 ms over 10 trials. Pulses from 10 ms to 10 min. Concentration series of 0.2–20% (v/v in solvent) with stable latencies. Consistent across the four modules (latency 35–48 ms). The waveform is less square and the amplitude lower than a commercial CyNexo olfactometer — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.09.11.675563v1.full)
- **Tips from the paper:** keep tubing as short as possible and **equal in length across modules**. 40 mL is a deliberate compromise (larger bottles need more odorant; smaller ones fail under pressure). Brown glass protects light-sensitive odorants. Add vacuum extraction if the output is a mask or small enclosure. Suggested human interfaces are the Johnson & Sobel mask or the Lundström nosepiece — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.09.11.675563v1.full)

**D. Surakka V, Björkbacka M, Lylykangas J, Rantala J, Salpavaara T, Verho J, Špakov O et al. (2025). "A new method for automated olfactory threshold testing" (AutomOT). Chem Senses. doi:10.1093/chemse/bjaf029. OA (PMC12370629). Tampere.**
- An Alicat MC-series MFC (MFC0) supplies air that is split into a constant clean-air line to the mask and a carrier line. A second MFC (MFC1) sets the scented stream through the odor source. Concentration is set by the ratio of the two flows — [PMC12370629](https://doi.org/10.1093/chemse/bjaf029)
- **Odor source:** coaxial stainless-steel tube with **glass beads (5 mm) filling the dead space** to cut delays. Stainless-steel piping throughout the odorised path to limit contamination. The odor source is removed and stored separately when not in use — [PMC12370629](https://doi.org/10.1093/chemse/bjaf029)
- **Switching:** two fast 3-way Festo MHE2-M1H-3/2G-QS4 valves route clean or scented air to the mask or to exhaust, driven by a custom driver with ms timing. **Two PIDs** (Ion Science MiniPID 2 PPB, 5 Hz): PID0 checks that each dilution has stabilised before presentation, PID1 monitors the output pulses. An LM35 sensor monitors temperature. Replaceable polyurethane tubing to an Intersurgical EcoLite oxygen mask gives a fixed nose–source distance — [PMC12370629](https://doi.org/10.1093/chemse/bjaf029)
- Pulse duration and dilution are combined to widen the intensity range. **MFC inaccuracy at very low flow** caused higher relative SD for the faintest pulses; the authors suggest an extra low-range MFC — [PMC12370629](https://doi.org/10.1093/chemse/bjaf029)
- **Cue control:** pink-noise headphones, pre-tested so that valve clicks are inaudible — [PMC12370629](https://doi.org/10.1093/chemse/bjaf029)
- Validated on 50 participants (27 with olfactory dysfunction), including a comparison table of earlier computerised threshold systems — [PMC12370629](https://doi.org/10.1093/chemse/bjaf029)

**E. Hopper R, Popa D, Maggioni E, Patel D, Obrist M, Landis BN, Hsieh JW, Udrea F (2024). "Multi-channel portable odor delivery device for self-administered and rapid smell testing." Communications Engineering. doi:10.1038/s44172-024-00286-1. OA (PMC11470141).**
- **24 channels**, one odor or dilution per channel, so there is no shared mixing chamber and no cross-contamination. Filtered air → Parker BTX Connect diaphragm pump (max 6 L/min) → aluminium manifold → 24 Zanty SDF-0626L solenoid valves → odor reservoirs (sponge absorbers in a cleanable cartridge) → **individual Teflon outlet pipes**. 3D-printed case, CAD shown; shift registers → 12 V MOSFET drivers — [Commun Eng](https://doi.org/10.1038/s44172-024-00286-1)
- **Concentration** is set by **serially diluted liquid odorants in separate channels**, e.g., 16-step geometric series as in Sniffin' Sticks threshold tests. The authors avoid gas-phase dilution because proportional valves add cost — [Commun Eng](https://doi.org/10.1038/s44172-024-00286-1)
- **Cost $2,140**, plus a few dollars per odorant. Validated with an Ion Science MiniPID (10 repeats, 3 L/min outflow, spatial scans on a Thorlabs stage). Cartridges are cleaned with baking-soda solution plus oven bake-out — [Commun Eng](https://doi.org/10.1038/s44172-024-00286-1)

**F. Salama R, Rodríguez-Lázaro MA, … Otero J et al. (2025). "Low-cost, open-source device for applying controlled olfactory stimuli during fMRI." HardwareX e00708. doi:10.1016/j.ohx.2025.e00708. OA (PMC12549773). Barcelona.**
- Arduino Nano. A 12 V **blower** (voltage sets the flow) feeds 3 normally-closed L172 solenoid valves (air, odor 1, odor 2) through TIP122 drivers. Three ≈15 m non-collapsible tubes (5.5 mm ID) run into the scanner room to **100 mL glass bubblers** (about 3 cm liquid height), which join close to the nasal cannula so mixing volume is near zero. Flow up to 2.7 L/min (typically 2 L/min), dead-space delay about 0.75 s — [HardwareX](https://doi.org/10.1016/j.ohx.2025.e00708)
- **BOM €251.91 (June 2025)**, GPL v3. STL enclosure, Arduino .ino and PCB layout on **Mendeley Data** — [doi:10.17632/g896nz5gm6.1](https://doi.org/10.17632/g896nz5gm6.1)
- **Tips:** the upstream lines carry only clean air, so only the bubbler and its tubes are replaced when changing odor. **Disconnect the bubblers when idle**, because passive diffusion contaminates the lines. A 12 s purge runs at power-on. Measure the real flow with a soft bag plus syringe (ΔV/Δt), because an inline flowmeter's resistance changes the flow — [HardwareX](https://doi.org/10.1016/j.ohx.2025.e00708)
- Limitation for threshold work: there is no concentration control beyond the bubbler solution, and no PID validation was reported (inference from the extracted text).

**G. Gotow N, Hoshi A, Kobayakawa T (2019). "Expanded olfactometer for measuring reaction time to a target odor during background odor presentation." Heliyon 5:e01254. OA (PMC6383036). AIST Japan.**
- Parts list: MFC-controlled odorless air and N₂. Stainless-steel gas-wash-bottle deodoriser. **Teflon tubing (Flon Industry F-8011, 4.35 mm ID)** and Flowell Teflon connectors. CKD MYB2 2-way valves driven by an Arduino Uno through Panasonic PhotoMOS relays (5 V → 24 V). A 3-way switching valve with suction exhaust of the non-presented stream — [Heliyon](https://doi.org/10.1016/j.heliyon.2019.e01254)
- **About 40 °C water circulated around the Teflon line** to keep air and odor warm. Onset and rise time measured with a high-speed ultrasonic gas sensor: ms for the target odor, about 4 s for background-odor equilibrium. They note that humidified odorless air vs humidified odor may be discriminable depending on vapor pressure — [Heliyon](https://doi.org/10.1016/j.heliyon.2019.e01254)

**H. Older or paywalled human designs (abstract-level only)**
- **Lorig TS, Elmes DG, Zald DH, Pardo JV (1999).** "A computer-controlled olfactometer for fMRI and electrophysiological studies of olfaction." Behav Res Methods Instrum Comput. doi:10.3758/bf03207734. Paywalled. Built from **off-the-shelf chromatography parts**, with no ferrous parts near the subject, contamination-resistant, and **deliberately neither warmed nor humidified** so it cannot become a bacterial incubator — [abstract](https://doi.org/10.3758/bf03207734). Lundström 2010 describes the "Lorig design" as small reservoirs near the subject, valves at a distance and per-channel flowmeters: cheap, but onset timing is imprecise at low flow — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)
- **Sommer JU, Maboshe W, Griebe M, Heiser C, Hörmann K, Stuck BA, Hummel T (2012).** "A mobile olfactometer for fMRI-studies." J Neurosci Methods. doi:10.1016/j.jneumeth.2012.05.026. Paywalled. Built from standard industrial and laboratory parts with **open-source software**, in three sections (air inlet/control/distribution, odorant, delivery). Tested with d-limonene and terpinen-4-ol in 21 subjects — [abstract](https://doi.org/10.1016/j.jneumeth.2012.05.026)
- **Lowen SB & Lukas SE (2006)** "A low-cost, MR-compatible olfactometer" (BRM, doi:10.3758/bf03192782; PMC1602106) and **Lowen, Farmer & Lukas (2017)** "Improved low-cost, MR-compatible olfactometer to deliver tobacco smoke odor" (BRM, doi:10.3758/s13428-016-0709-1; PMC4991953) — [Europe PMC listing](https://doi.org/10.3758/s13428-016-0709-1). Full text not retrieved.
- **Bestgen AK et al. (2016)** "An extension of olfactometry methods: an expandable, fully automated, mobile, MRI-compatible olfactometer." J Neurosci Methods. doi:10.1016/j.jneumeth.2015.12.009. Paywalled — [DOI](https://doi.org/10.1016/j.jneumeth.2015.12.009)
- **Hosseini SF et al. (2020)** "A multimodal MR-compatible olfactometer with real-time controlling capability." J Med Eng Technol. doi:10.1080/03091902.2020.1791987. Paywalled — [DOI](https://doi.org/10.1080/03091902.2020.1791987)
- **Hayes JE, Jinks AL, Stevenson RJ (2013)** "A comparison of sniff bottle staircase and olfactometer-based threshold tests." Behav Res Methods. doi:10.3758/s13428-012-0220-2. Paywalled. Directly relevant for validating an olfactometer threshold procedure against bottles — [Springer](https://link.springer.com/article/10.3758/s13428-012-0220-2)
- **Neige C et al. (2024)** "Combining a breath-synchronized olfactometer with brain stimulation…" JoVE. doi:10.3791/65714. Video protocol, paywalled — [DOI](https://doi.org/10.3791/65714)

**I. Bag-based delivery (Monell, Mainland lab), which is the "Pellegrino" method**
- **Andres M*, Pellegrino R*, Song X, Ocampos F, Mainland JD (2026).** "Odor sampling bags enable reliable delivery of controlled odor concentrations." bioRxiv 10.64898/2026.01.12.698699 (OA, PMC12871223); peer-reviewed version in **Chem Senses** (doi:10.1093/chemse/bjag022) — [PMC12871223](https://pmc.ncbi.nlm.nih.gov/articles/PMC12871223/); [Chem Senses](https://academic.oup.com/chemse/article-abstract/doi/10.1093/chemse/bjag022/8746392). (The task brief said "Pellegrino 2025". The bag paper is dated 2026. Pellegrino and Mainland had other 2025 work, e.g., a bioRxiv on odor intensity, whose relation to this method I did not verify.)
- **Protocol:** Nalophan tube, sealed at one end around a septum (for injection) and at the other around an open/close valve. Evacuate it on vacuum, then fill with **dehumidified, carbon-filtered air at a known flow for a known time** (e.g., 2 L/min × 5 min = 10 L). **Inject neat liquid odorant by syringe** (0.5 µL–2 mL). Example: 30 µL in 10 L gives 3×10⁻⁶ v/v headspace (as reported). Equilibrate for minutes to hours — [PMC12871223](https://pmc.ncbi.nlm.nih.gov/articles/PMC12871223/)
- **Delivery:** the valve attaches to a soft **nose mask with a low-resistance one-way valve**. The bag collapses as the subject sniffs, so no ambient air dilutes the sample and air is the only "solvent". Bags were prepared the day before testing (7 concentrations plus a blank) — [PMC12871223](https://pmc.ncbi.nlm.nih.gov/articles/PMC12871223/)
- **Verification:** PID **calibrated daily with isobutylene**. A per-odorant multipoint calibration was made by air-diluting saturated headspace (concentration from vapor pressure), and bag concentrations were read off it in ppm. Concentration was stable over 4 days, comparable to Tedlar bags. PID accuracy was checked with 500 ppm isobutylene diluted to 250 and 100 ppm with MFCs — [PMC12871223](https://pmc.ncbi.nlm.nih.gov/articles/PMC12871223/)
- **Outcome:** compared with glass jars (propylene glycol diluent), bags gave higher maximum intensities and steeper curves, better test–retest reliability, and preserved differences in maximum intensity between odorants. Jars dilute with ambient air, and solvent choice alone can shift vapor concentration by at least 10× (water vs mineral oil) — [PMC12871223](https://pmc.ncbi.nlm.nih.gov/articles/PMC12871223/)
- Method lineage: Japanese **Triangle Odor Bag method** (Iwasaki 1972). Abraham et al. 2012 used bag delivery in a large threshold study — [PMC12871223](https://pmc.ncbi.nlm.nih.gov/articles/PMC12871223/)

**J. Commercial air-dilution unit used as a human threshold tool**
- **Cook GR et al. (2014)** "Quantitative measurement of odor detection thresholds using an air dilution olfactometer…" PeerJ. doi:10.7717/peerj.643. OA. Portable **Scentroid SM110C**. n-Butanol (20 ppm) was prepared daily in a **stainless-steel evaporation chamber** (0.5 µL aqueous butanol plus compressed air) and stored in a 1 L **Tedlar bag**, then air-diluted to **5.5–100 ppb** (15 steps, dilution ratios 200–3,600). Delivered from a metal cone at 20 L/min and 2.5 m/s for about 2 s per step. Mean threshold 22.5 ± 13.7 ppb, test–retest stable — [PeerJ](https://doi.org/10.7717/peerj.643)

### Inferences
- For an ML dataset of thresholds across many pure molecules, the most transferable blueprint is a hybrid: the Lundström switching and anti-cue scheme (3-way valves, check valves, continuous-flow line, PTFE after the odor), plus Johnson & Sobel or AutomOT MFC-ratio air dilution from a characterised saturator, plus the AutomOT or Monell practice of PID-verifying every step.
- Doyle 2025 and Hopper 2024 are the cheapest fully documented builds, but concentration is set in the liquid phase (solvent dilution) and verified only in relative PID units. They need absolute calibration (see Q4) before they can produce ppb-level threshold data.
- The Nalophan bag method is the lowest-hardware route to absolute gas-phase concentration at the nose. It is labor-intensive per concentration, but it removes solvent and dilution artefacts, which dominate threshold variance.

### Gaps
- I could not access the Johnson & Sobel 2007 full text: canister material and geometry, MFC models, humidifier/heater design, the concentration tables, and whether a mask is used remain unverified.
- Lundström 2010 onset and rise-time values and total cost were not extracted (the paper's Table 1 has the prices).
- Doyle 2025: no GitHub/OSF repository URL was found in the extracted text, and peer-review status is unknown.
- Keller & Vosshall (vial-based delivery with odorants diluted in solvent) was not retrieved in this session. From memory they used vials of solvent dilutions sniffed directly, not an olfactometer; this is unverified.
- Kobal's original design papers (1980s) and Burghart OM2 documentation were not retrieved. Only the "Kobal switching principle" is confirmed (see Q3).
- Gottfried-lab and Vigouroux olfactometer build descriptions were not found in this search.
- Schmidt & Cain 2010 "Making scents" (VDD8): only the abstract was retrieved. It is the key paper for solvent-free delivery below 1 ppt (see Q4).

---

## Q2. Which animal/neuroscience open designs have engineering that transfers to a human threshold olfactometer?

### Takeaway
Rodent flow-dilution olfactometers from the Rinberg lineage (Janelia → Aurora 206A/220A → Dewan lab protocol) are the best-documented MFC-based air-dilution architecture. Their features transfer directly: odor MFC 0–100 mL/min into a carrier MFC 0–1000 mL/min, a "final valve" diverting to exhaust until stabilised, pressure-balanced dummy vials, and Teflon manifolds. Open hardware repositories exist for ODORS (GitHub), Harp (GitHub), the Dewan lab (GitHub) and Janelia (Flintbox licence).

### Cited Findings
- **Dewan lab STAR Protocol:** Johnson CE, Williams E, Dewan A (2023). "Protocol for quantifying the odor detection threshold of mice." STAR Protoc. doi:10.1016/j.xpro.2023.102635. OA (PMC10579531).
  - Eight-channel olfactometer. Carrier MFC fed from an N₂ tank. A dilutor MFC and a clean-air line fed from house air through coalescing and ultra-high-capacity hydrocarbon filters.
  - A **final valve** sends odorised air to exhaust at rest and to the animal when actuated (clean air goes the other way).
  - A **pressure-balanced dummy vial** is used via normally-open valves, and an **electronic needle valve** (stepper-driven) balances per-vial pressure.
  - Manual needle valves equalise resistance, and an exhaust flowmeter diagnoses leaks and pressure mismatch. 1/8" Teflon tubing with ferrules. The distance from final valve to port is minimised.
  - 3D-printed parts are on [GitHub OlfactoryBehaviorLab](https://github.com/OlfactoryBehaviorLab/). The protocol notes that any liquid- or flow-dilution olfactometer with repeatable pulses can be used — [STAR Protoc](https://doi.org/10.1016/j.xpro.2023.102635)
- **Rinberg lab (Nakayama, Gerkin, Rinberg 2022, Cell Rep Methods, OA PMC9243525):** two-cassette air-dilution olfactometer. Each cassette has an Alicat clean-air MFC (0–1000 mL/min, MC-1SLPM) and an odor MFC (0–100 mL/min, MC-100SCCM), four inline **NResearch Teflon 4-valve manifolds (225T082)**, bypass valves, and a **final valve (NResearch SH360T042)**. Defaults are 400 + 100 mL/min per cassette, 1000 mL/min total to exhaust until delivery. Binary mixtures come from opening vials in both cassettes — [Cell Rep Methods](https://doi.org/10.1016/j.crmeth.2022.100233)
- **Janelia open-science olfactometer (Rinberg lab, Janelia ref. 2012-020):** cassettes with 2 MFCs each, 5-valve Teflon manifolds, vial valve pairs, a fast pressure gauge, vacuum and clean-air MFC lines, and thin Teflon tubing. Concentration stabilises in about 0.5–1 s. Designs are available via Flintbox, free for non-profit research, and also sold by Aurora Scientific — [Janelia](https://www.janelia.org/open-science/olfactometer)
- **Aurora Scientific 206A/220A:** 206A was based on Rinberg's design. It uses MFCs throughout, 4 vials expandable to 8 or 12, and opens only one vial set at a time for a "square" profile. The 220A adds a **third MFC to balance clean-air and odor-line pressures** — [Aurora 206A manual](http://bulletins.aurorascientific.com/manuals/206A.Manual.pdf); [Aurora 220A](https://aurorascientific.com/products/neuroscience/220a-olfactometer/)
- **Harp Olfactometer (harp-tech, open hardware):** 1 carrier line at 0–1000 mL/min, 4 odor lines at 0–100 mL/min with configurable flow, TTL-controllable odor and end valves, supports mixtures, USB, 24 V — [GitHub harp-tech/device.olfactometer](https://github.com/harp-tech/device.olfactometer)
- **ODORS:** Kosel F, Hartley MR, Franklin TB (2025). eNeuro doi:10.1523/ENEURO.0161-25.2025. OA (PMC12757508).
  - Aquarium-type pump (about 16 L/min, run below maximum to reduce noise) → carbon filter → two rotameters (1–10 L/min).
  - **NResearch pinch solenoid valves** (360P021-42 normally-open for clean air; double-tube pinch valves for odors), C-Flex tubing, 250 mL PET bottles with PP caps. Each bottle, cap and tube assembly is swapped as a unit per odor.
  - The clean-air valve starts the downstream line, so it is continuously flushed. Only one valve is open at a time to keep flow constant. An Arduino Uno reads tVOC sensors.
  - BOM on [GitHub FilipKosel/ODORS](https://github.com/FilipKosel/ODORS); licence CC BY-NC-SA 4.0 — [eNeuro](https://doi.org/10.1523/ENEURO.0161-25.2025)
- **Burton SD, Wipfel M, Guo M, Eiting TP, Wachowiak M (2019).** "A novel olfactometer for efficient and flexible odorant delivery." Chem Senses 44:173. doi:10.1093/chemse/bjz005. Paywalled, with a PMC author version (PMC6410398). Modular, "unlimited" number of odorants, **no detectable intertrial or interchannel contamination**, flexible mixtures and sequences. Delivery is turbulent but reliable, with precision equivalent to a flow-dilution olfactometer — [abstract](https://doi.org/10.1093/chemse/bjz005)
- **Tichy H et al. (2020).** "Developing and testing of an air dilution flow olfactometer with known rates of concentration change." J Neurosci Methods. doi:10.1016/j.jneumeth.2020.108794. OA (PMC7614200).
  - Two **proportional valves** (Kolvenbach KWS 3/4), each in series with an electronic flowmeter (Honeywell AWM 3000), mix saturated and clean air. A **PI feedback controller linearises** the valves' non-linear flow. Validated with a miniPID 200A.
  - Tips: valves overshoot on step opening, and **PID sensitivity drifts**. The lamp window needed periodic cleaning, so PID output was only used as relative concentration — [PMC7614200](https://doi.org/10.1016/j.jneumeth.2020.108794)
- **Arevalo N et al. (2025)** "Constructing an Olfactometer for Rodent Olfactory Behavior Studies." JoVE doi:10.3791/67049 (Restrepo lab; video protocol, paywalled) — [DOI](https://doi.org/10.3791/67049)
- **Ni J et al. (2022)** "Sniff Olfactometer (SO) Protocols," bioRxiv doi:10.1101/2022.07.08.499357 — [DOI](https://doi.org/10.1101/2022.07.08.499357). Not read in detail.
- **Bpod (Sanworks):** open-source Arduino-based state machine with a valve-driver module, widely used to time olfactometer valves. I found no Sanworks-specific open MFC olfactometer — [GitHub sanworks/Bpod](https://github.com/sanworks/Bpod); [Valve Driver Module](https://sanworks.io/shop/viewproduct?productID=1015)
- **Aviles-Rosa EO et al. (2024)** "Development of an automated human scent olfactometer…" PLoS One (canine detection; OA, PMC10906837) — [DOI](https://doi.org/10.1371/journal.pone.0299148). Not read in detail.

### Inferences
- The Rinberg/Dewan MFC-cassette design, scaled to human flows (e.g., carrier 2–8 L/min, odor MFC with a 10–100 mL/min or smaller range) and fed from saturators, is the proven architecture for stepping concentrations under software control. Dewan's protocol is designed for threshold measurement (in mice) and has explicit anti-contamination and pressure-balancing details.
- Pinch valves (ODORS) keep odor off the valve internals and make swapping cheap. Soft tubing (C-Flex) and PET/PP bottles, however, are more adsorptive than PTFE/glass. That is acceptable for strong odors, risky for trace thresholds.

### Gaps
- I did not verify whether OpenScent, a "Raspberry Pi olfactometer" or other named "olfactory display" repos exist as documented builds. GitHub search beyond harp-tech, ODORS and OlfactoryBehaviorLab was not done systematically.
- Knosys olfactometer specs were not retrieved.
- Burton 2019 full-text specifics (valve types, "odor stick" or cartridge concept) were not extracted.

---

## Q3. Commercial reference designs: what are their key specifications?

### Takeaway
Clinical and EEG instruments (Burghart OM6b, Kobal principle) run high flow, heated and humidified. EN 13725 instruments (Olfasense TO8, Scentroid SC300) cover 3–5 orders of magnitude of dilution with passivated stainless steel, orifice/jet-pump or venturi dilution, and 20 L/min-class presentation. These are the benchmarks a home-built device should be compared against.

### Cited Findings
- **Burghart OM-series (Kobal):** works on the **Kobal switching principle**. Air is heated to about 36–36.5 °C and humidified to about 80% RH (the vendor says >60% RH). Reported flows are 6–8 L/min. Studies describe it as 8-channel — [Burghart](https://www.burghart-mt.de/en/medical_product/olfactometer_and_gustometer/); [WUR equipment page](https://search.researchequipment.wur.nl/SearchDetail.aspx?deviceid=a6f4abd5-e484-4f00-8666-aeca14957f6c). Lundström 2010 used an OM6b at 8 L/min heated and humidified air as a comparison for irritation ratings — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/). (Flow varies by study, 6 vs 8 L/min, which suggests it is configurable. Uncertain.)
- **Olfasense TO8 evolution:** 4- or 6-station. **28 dilution steps from 1:3.5 to 1:65,000**. Dilution by gas jet pumps with fixed sapphire orifices. **Passivated stainless steel** with odorant recovery of 85–99%. Meets EN 13725:2022 — [Olfasense TO8](https://www.olfasense.com/odour-measurement-equipment/instruments/to8-evolution-olfactometer/)
- **Scentroid SC300 (portable):** dilution **8–131,072 (2³–2¹⁷)** with up to 1000 intermediate steps. Venturi eductor with MFCs on clean and sample air. Presentation at 5–30 L/min (0.25 m/s at 20 L/min). Uses 70 L/min of clean air at 80 psi. Response 0.2 s — [Scentroid SC300](https://scentroid.com/products/olfactometers/sc300-portable-olfactometer/). The SC300P "scientific" variant is marketed with EEG/fNIRS triggering — [SC300P](https://scentroid.com/products/olfactometers/sc300p-scientific-olfactometer/)
- **Recovery of odorants in dilution olfactometers:** papers exist that quantify losses by PTR-MS: Hansen, Adamsen & Feilberg 2013, Sensors (doi:10.3390/s130607860, OA), and "Effects of dilution systems in olfactometry on the recovery of typical livestock odorants determined by PTR-MS" (PMC5579735) — [Sensors 2013](https://doi.org/10.3390/s130607860); [PMC5579735](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5579735/). Only the titles were verified; I did not extract the findings.
- **Aurora Scientific 206A/220A** (rodent): see Q2.

### Inferences
- The EN 13725 instruments show that 4–5 decades of dilution come from one or two stages of calibrated orifice or venturi dilution plus a known-concentration source (bag or reference gas). A DIY build that wants ppt–ppm will need cascade dilution or a range of saturator sources, not a single MFC ratio (see Q4).
- EN 13725 presentation flows (about 20 L/min at a cone) are far above nasal-cannula flows (1.5–3 L/min per nostril). This affects whether the subject entrains room air, and so the effective concentration.

### Gaps
- Dravnieks forced-choice dynamic triangle olfactometer specs were not retrieved.
- In-house EN 13725 dynamic-dilution builds (theses) were not found in this session.
- OM6b exact channel count and flow specification were not verified from a Burghart datasheet.

---

## Q4. Which designs report precise, verified concentration control across many orders of magnitude (ppt–ppm)?

### Takeaway
Only a few approaches report *absolute*, verified gas-phase concentrations:
- MFC air dilution from a saturator, with tabulated outcomes (Johnson & Sobel 2007) or PID-verified ratios (AutomOT);
- solvent-free vapor delivery down to below 1 ppt (Schmidt & Cain VDD8);
- static gas-bag dilution with PID calibration (Monell Nalophan bags; Cook/Scentroid Tedlar bag plus air dilution, 5.5–100 ppb);
- model-based prediction from mineral-oil partition coefficients (Conchou 2026).

Most low-cost builds verify only relative PID signal.

### Cited Findings
- **Schmidt R & Cain WS (2010)** "Making scents: dynamic olfactometry for threshold measurement." Chem Senses 35:109. doi:10.1093/chemse/bjp088. Author version PMC2805809. The **vapor delivery device 8 (VDD8)** offers a flexible range of delivered concentrations and definable stability, "**accommodates solvent-free delivery below a part per trillion**", and has a realistic subject interface and replaceable components. It is designed for absolute sensitivity. The motivation is that reported human thresholds vary by orders of magnitude between studies — [abstract](https://doi.org/10.1093/chemse/bjp088)
- Thresholds for the same odorant in the literature differ by **4–5 orders of magnitude**, attributed to poor stimulus control — [Andres, Pellegrino et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC12871223/)
- **Johnson & Sobel 2007:** known concentrations from carrier flow through a standard canister, with outcome tables — [abstract](https://doi.org/10.1016/j.jneumeth.2006.09.008)
- **AutomOT:** flow-ratio dilution with two inline PIDs, stabilisation checked before each presentation. The faint end is limited by MFC low-flow accuracy — [Chem Senses 2025](https://doi.org/10.1093/chemse/bjaf029)
- **Cook 2014 (Scentroid):** 20 ppm n-butanol Tedlar-bag standard air-diluted to 5.5–100 ppb — [PeerJ](https://doi.org/10.7717/peerj.643)
- **Monell bags:** PID calibrated per odorant against saturated-headspace air dilution; concentration stable 4 days — [PMC12871223](https://pmc.ncbi.nlm.nih.gov/articles/PMC12871223/)
- **Conchou L, Trelea IC, Gévar J, Monsempès C, Peron AC, Renou M, Souchon I, Lucas P et al. (2026)** "A method to estimate absolute odorant concentration of olfactory stimuli." PLoS One e0337336. doi:10.1371/journal.pone.0337336. OA (PMC12758820).
  - A **mass-transfer model** predicts the concentration delivered from a vial of odorant in **mineral oil** as a function of airflow, source size and odorant properties.
  - It is calibrated with **air–mineral-oil partition coefficients measured by headspace GC-FID** and generalises to other compounds with known partition coefficients.
  - It warns that PID traces reflect the dynamic stimulus shape and must be interpreted carefully. Headspace is depleted by repeated or long puffs — [PLoS One](https://doi.org/10.1371/journal.pone.0337336)
- Flow-dilution systems give precise control, but adsorption on walls downstream of the odor source causes contamination — [Conchou 2026](https://doi.org/10.1371/journal.pone.0337336)
- **Liquid-phase serial dilution** (Hopper 2024, 16-step geometric series; Doyle 2025, 0.2–20% v/v) gives PID-consistent relative steps but no absolute gas-phase concentration — [Hopper](https://doi.org/10.1038/s44172-024-00286-1); [Doyle](https://www.biorxiv.org/content/10.1101/2025.09.11.675563v1.full)
- **Commercial EN 13725 dilution ranges:** TO8 1:3.5–1:65,000; SC300 8–131,072 — [Olfasense](https://www.olfasense.com/odour-measurement-equipment/instruments/to8-evolution-olfactometer/); [Scentroid](https://scentroid.com/products/olfactometers/sc300-portable-olfactometer/)
- **PID limits:** Lundström's miniPID 200A was quoted with a 100 ppm detection limit (as stated, likely range-dependent). Ion Science "MiniPID 2 PPB" sensors are designed for ppb. Tichy found PID sensitivity drift — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/); [AutomOT](https://doi.org/10.1093/chemse/bjaf029); [Tichy 2020](https://doi.org/10.1016/j.jneumeth.2020.108794)

### Inferences
- A single MFC ratio (e.g., 0–100 mL/min into 1–8 L/min) covers only about 2–3 decades at usable accuracy. MFCs are typically unreliable below about 2% of full scale, which AutomOT found in practice. Spanning ppt–ppm (6+ decades) needs several steps combined:
  1. saturator vapor, or vapor over a liquid dilution in low-volatility solvent, with a known or GC-measured partition coefficient;
  2. two cascaded MFC dilution stages, or several MFCs with different ranges;
  3. PID verification at the upper end, extrapolated through the calibrated dilution ratios at the lower end, because PIDs cannot read ppt.
  Static bag dilution (serial transfer between bags) is the low-cost alternative.
- For an ML dataset, per-molecule absolute concentration should come from gas-phase verification (PID with a compound-specific response factor, or GC/PTR-MS) at one or more anchor points, not only from liquid-dilution arithmetic. Solvent effects of 10× or more are documented.

### Gaps
- VDD8 construction details (saturator design, dilution stages, GC verification) are needed from the Schmidt & Cain full text. I found no open build files.
- I found no open-source design with documented cascade dilution over 6 decades and PID/GC verification. This looks like a real gap in the open literature (not exhaustively confirmed).
- Cometto-Muñiz & Abraham used the VDD in many threshold papers. I did not extract their delivery details.

---

## Q5. Which practical building tips recur across sources?

### Takeaway
The recurring rules:
- fluoropolymer (PTFE/PFA/FEP), glass or passivated stainless steel on every wetted path downstream of the odor source; cheap tubing is fine upstream;
- continuous clean-air flushing, with odors switched by 3-way valves or a final valve to exhaust;
- check valves or one-way paths, and a separate outlet per odor where possible;
- matched flow resistances, so switching produces no puff or noise cue;
- masking of valve sounds;
- 1.5–3 L/min per nostril (≤5 L/min per nostril, up to 8 L/min with a mask);
- disconnect or remove odor sources when idle;
- PID verification of every channel and concentration.

### Cited Findings
- **Materials:** fluoropolymer tubing after the odor reservoirs (Lundström) — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/). Stainless-steel piping in the odorised path (AutomOT) — [Chem Senses 2025](https://doi.org/10.1093/chemse/bjaf029). Teflon tubing and connectors throughout (Gotow) — [Heliyon](https://doi.org/10.1016/j.heliyon.2019.e01254). Teflon outlet pipes, one per channel (Hopper) — [Commun Eng](https://doi.org/10.1038/s44172-024-00286-1). Passivated stainless steel gives 85–99% recovery (TO8) — [Olfasense](https://www.olfasense.com/odour-measurement-equipment/instruments/to8-evolution-olfactometer/). Chromatography fittings (Lorig) — [abstract](https://doi.org/10.3758/bf03207734). Odorants adsorb to tubing, valves and walls (Doyle; Conchou) — [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.09.11.675563v1.full); [PLoS One](https://doi.org/10.1371/journal.pone.0337336)
- **Cross-contamination:** continuous carrier or clean-air flushing (Doyle, ODORS, Lundström CF line). Check valves (Lundström). Separate channels instead of a shared mixing chamber (Hopper). Swap the whole bottle, cap and tube per odor (ODORS). Replace only the bubbler and downstream tubing (Salama). Remove odor sources when idle (Salama; AutomOT) — sources above. Test low-to-high concentrations, or dedicate lines, so that residual high concentrations do not mask low ones (Dewan protocol) — [STAR Protoc](https://doi.org/10.1016/j.xpro.2023.102635)
- **Cleaning:** baking-soda solution plus oven bake-out of cartridges (Hopper) — [Commun Eng](https://doi.org/10.1038/s44172-024-00286-1). Power-on 12 s purge (Salama) — [HardwareX](https://doi.org/10.1016/j.ohx.2025.e00708). Regular tubing replacement (Lundström) — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)
- **Tactile and auditory cues:**
  - 3-way valves avoid pressure-release puffs, and a CF line of 0.5–1 L/min masks switching. Quiet valves are gasket-mounted inside the cabinet. The compressor is loud — [PMC2967213](https://pmc.ncbi.nlm.nih.gov/articles/PMC2967213/)
  - Pink-noise headphones (AutomOT) — [Chem Senses 2025](https://doi.org/10.1093/chemse/bjaf029)
  - Only one valve open at a time, for constant flow (ODORS). Solvent bottles opened to keep the number of open bottles constant (Doyle) — [eNeuro](https://doi.org/10.1523/ENEURO.0161-25.2025); [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.09.11.675563v1.full)
  - Pressure-balanced dummy vial, needle valves and a final valve to exhaust (Dewan; Rinberg) — [STAR Protoc](https://doi.org/10.1016/j.xpro.2023.102635); [Cell Rep Methods](https://doi.org/10.1016/j.crmeth.2022.100233)
- **Flow at the nose:** 3 L/min total (1.5 per nostril), ≤5 L/min per nostril, 8 L/min with a mask (Lundström). About 2 L/min by cannula (Salama). OM6b 6–8 L/min heated and humidified. Scentroid 20 L/min cone — sources above.
- **Temperature and humidity:** OM6b 36 °C / 80% RH. Gotow uses a 40 °C water jacket. Lundström and Lorig deliberately use dry, room-temperature air (cheaper, and no bacterial growth). Gotow warns that humidification can itself become a discriminable cue for low-vapor-pressure odorants — sources above.
- **Dead volume and timing:** glass beads to fill source dead space (AutomOT). Final valve placed close to the nose port (Dewan). Merge odor lines at the cannula (Salama, 0.75 s delay at 2 L/min). Equal tubing lengths across channels (Doyle). Check valves keep channels pressurised (Lundström) — sources above.
- **Flow measurement:** an inline meter's resistance changes the flow, so use a bag plus syringe, or put meters upstream (Salama). Proportional valves are non-linear and need closed-loop control (Tichy). The exhaust flowmeter doubles as a leak diagnostic (Dewan) — sources above.
- **Controllers used:**
  - Arduino Uno/Nano with TIP122 or MOSFET drivers or PhotoMOS relays: Salama, ODORS, Gotow, Doyle, Hopper;
  - AutoMate ValveLink driven from E-Prime or PowerLab: Lundström;
  - LabVIEW: Johnson & Sobel;
  - CED 1401 analog output: Tichy;
  - Bpod or Harp for behavior rigs — sources above.
- **PID practice:** calibrate daily with isobutylene and build odorant-specific curves (Monell). Clean the lamp window and expect drift (Tichy). Place the probe where the nose would be (Lundström). A PID's response time can be too slow for ms pulse shapes (AutomOT) — sources above.

### Inferences
- Budget: a PID (Ion Science MiniPID 2 PPB or Aurora miniPID) plus 2–3 Alicat-class MFCs will likely cost more than the rest of the build. The Doyle (about €1,700) and Salama (about €250) builds exclude these.
- For an LMU build, a practical starting point is:
  - the Doyle/Lundström valve and flush topology, rebuilt with PFA tubing, glass saturators and stainless or PTFE fittings;
  - Rinberg/Dewan-style MFC cassettes with a final valve to exhaust;
  - a nose mask or nosepiece at 3–6 L/min;
  - PID anchoring per odorant;
  - optional Nalophan-bag standards for absolute calibration.

### Gaps
- No source found gives quantitative carry-over (memory effect) numbers for PTFE vs PFA vs stainless steel at ppb levels for a human olfactometer. Burton 2019 claims "no detectable" contamination for its own design. The PTR-MS recovery papers listed in Q3 would be the place to look.
- Humidification designs with numbers (bubbler vs membrane, RH achieved) were not retrieved beyond the OM6b figures.
