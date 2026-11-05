# Auto doser — folder overview

Updated 22 October 2026. The doser work from three parallel sessions is now merged into one set of files in this folder.

## Purpose and current state

This folder holds a perfume ingredient dosing machine. It belongs to the wider **CALNEW molecular odour research project**, which has three connected activities:

1. Predict molecular odour descriptors and airborne detection thresholds with a Python research pipeline.
2. Build a gravimetric dispenser that doses ingredients into a vial, targeting **±20 mg** per dose (this folder).
3. Measure odour thresholds with the sponsored olfactometer and feed the results back into the research.

**What exists for the doser:**
- feasibility analysis;
- 4-line parts list with a priced supplier workbook;
- numbered wiring and tubing diagrams;
- septum leak analysis;
- Blender concept scenes.

**What is still only planned:**
- doser firmware;
- the wireless control interface;
- a measured dosing-validation log.

The formula-to-doser connection is also future work: the CALNEW prediction endpoints do not generate perfume formulas.

## Where the files live

```text
Auto doser/
├── OVERVIEW.md                    this file
├── Perfume-Doser-Feasibility.md   concept, alternatives, risks, test plan
├── Doser-4-Line-BOM.md            parts list, rules, build order
├── Doser-4-Line-BOM.xlsx          shop links and prices, budget + lab-grade
├── Doser-4-Line-Wiring.md         every wire and tube, pin map, bring-up order
├── Septum-Leak-Analysis.md        cap sealing and evaporation analysis
├── doser-3d/                      Blender scene scripts, perfume_doser.blend, renders
├── doser-wiring/                  wiring + tubing SVGs and their generator script
```

The public repository contains the reviewed design files in this folder. The Python research software, reports and data configuration are at the repository root. Local worktrees and correspondence are excluded.

## Start here

| Interest | File or directory |
|---|---|
| Doser mechanism, alternatives, limitations and test plan | [Perfume-Doser-Feasibility.md](Perfume-Doser-Feasibility.md) |
| Phone/PC control over Wi-Fi and Bluetooth | [Perfume-Doser-Feasibility.md](Perfume-Doser-Feasibility.md), §2a |
| Bottle closure (septum in the bottle's own cap) | [Perfume-Doser-Feasibility.md](Perfume-Doser-Feasibility.md), §3, and [Septum-Leak-Analysis.md](Septum-Leak-Analysis.md) |
| Four-line rig parts, rules and build order | [Doser-4-Line-BOM.md](Doser-4-Line-BOM.md) |
| Shop links and prices | [Doser-4-Line-BOM.xlsx](Doser-4-Line-BOM.xlsx) |
| Wiring, tubing, ESP32 pin map, bring-up tests | [Doser-4-Line-Wiring.md](Doser-4-Line-Wiring.md) |
| Diagrams alone | [electrical](doser-wiring/doser_wiring_electrical.svg), [air and liquid](doser-wiring/doser_tubing.svg) |
| Visual concepts and scene generators | [doser-3d/](doser-3d) |
| Overall research project and installation | [CALNEW README](../README.md) |
| Sponsored odour measurement instrument | [Experimental measurements](../docs/ARCHITECTURE.md#experimental-measurements) |
| Original research map | [CALNEW.canvas](../CALNEW.canvas) (open in Obsidian) |
| Model results and architecture | [BASIC-MODELS.md](../docs/BASIC-MODELS.md), [ARCHITECTURE.md](../docs/ARCHITECTURE.md) |

## Doser concept

**Air and liquid path:**
- One central air pump and buffer bottle feed a separate normally-closed 3/2 air valve per ingredient bottle.
- Opening a valve pressurises that bottle's headspace, which pushes the liquid up a dedicated FEP tube to a fixed nozzle head above the vial.
- Unpowered, every valve vents its bottle.

**Feedback:** a balance under the vial reports to an ESP32 over RS232. The accuracy comes from the measured mass and from controlling after-drips, not from valve timing.

**Bottle closure:** each bottle keeps its own screw cap, with the liner replaced by a PTFE/silicone septum.
- Two Ø 2 mm holes 5 mm apart in the cap.
- The silicone is the seal; the PTFE face is a vapour shield.
- A printed saddle on the cap takes any pull on the tubes.
- The septum is replaced after terpene-rich materials.
- Each bottle gets a weekly idle-mass log.

The universal PTFE cone (option A) and the carousel/docking design remain documented alternatives.

**Wireless control:** the dosing loop stays on the ESP32. A phone or PC only submits jobs, sets things up and shows status over Wi-Fi (`doser.local`) or Bluetooth. This is a specification; no firmware exists yet.

**Stop button:** a latching mushroom button with two NC contacts.
- Contact 1 cuts the 12 V to all valves and the pump, in hardware.
- Contact 2 tells the ESP32 (GPIO 34). Pressed or wire broken both read as "stopped".
- The ESP32, balance link and sensor stay powered.

### Wiring and tubing

[Doser-4-Line-Wiring.md](Doser-4-Line-Wiring.md) numbers every connection: wires W01–W57, air tubes T01–T27 and liquid lines L1–L4. For each it gives the source, destination, material and length. It also has a step-by-step bring-up test.

Decisions recorded there:
- **Valve 4 is on GPIO 33**, not 14: GPIO 14 pulses at boot.
- **A Schottky diode (D6) sits in the ESP32's 5 V feed**, so USB and the 12 V supply can be connected at the same time.
- **I²C pull-ups** for the bare pressure sensor.
- **A silicone sleeve joint** links each FEP air tube to its valve. It is on the air side only, at least 30 cm from the bottle.

### Parts and estimated costs

| Version | Budget parts | Lab-grade parts |
|---|---:|---:|
| Merged 4-line rig (septum fixes + wiring + Wi-Fi/stop button) | ≈ €342 | ≈ €702 |

These are October 2026 listed prices including VAT. They exclude the balance, test liquids, shipping and tools. Earlier figures (≈ €322/682 and ≈ €339/699) were the separate branches before merging.

The workbook supersedes the rough tables in the notes. Its formulas and group totals were checked with a script; prices and stock were not re-checked for this overview. Rows whose price is not a confirmed listing are marked "estimate" in the workbook's status column. Examples:
- the silicone sleeve tube (eBay listing that would not load);
- lab-grade parts listed in other currencies.

### Validation still needed

**Go/no-go test:** four lines with contrasting liquids and bottles, 30 doses each at 50 mg and 500 mg targets.

**Acceptance criterion:** **95 % of doses within ±20 mg and zero unnoticed drips**.

**Also planned:**
- a four-week closure test with a terpene-rich material;
- after-drip monitoring;
- flow-drift checks.

No measured results exist yet.

## Open design points

- **Pressure limits disagree.**
  - The feasibility note asks for relief at **≤ 30 kPa**.
  - The parts list and wiring diagram use an adjustable relief valve whose minimum is **0.5 bar (50 kPa)** and quote "30–50 kPa".
  - The cheap valves are rated about 40–47 kPa.
  - Settle this before ordering, for example with a 0.3 bar pre-set valve.
- **Septum figures are calculations.** The seal life and permeation numbers in the leak analysis still need the four-week test.
- **Wireless control and firmware** are specifications only.
- **Totals in the septum analysis.** It still quotes the totals from its own branch (≈ €322/682); the parts list and workbook hold the current totals.

## CALNEW software and research

The research checkout in [`../`](..) contains the Python package `calnew` (version 0.1.0, Python ≥ 3.11; runs used 3.12). Next to it are its configs, docs, tests, scripts, reports, research notes and saved results.

The vault copy is a working installation:
- `.venv`, `runs/` and evidence snapshots are present.
- `data/current.json` points to snapshot `828751d0a24e8149`, which is present.

The git branches carry only the source; environments, runs and snapshots are ignored by `.gitignore`.

**Git state of the move:** the move of these files from the repository root into `Support/` is not yet committed. Git currently sees 140 deleted files: 131 moved unchanged, and 9 with newer edits from 1–3 October that exist only in `Support/`.

| Path (in `Support/`) | Role |
|---|---|
| `src/calnew/` | Evidence ingestion and storage, chemistry and units, features, models, benchmarking, calibration, prediction, modular pipeline |
| `configs/` | Source register, descriptor vocabulary, pilot/full experiment configurations |
| `data/` | Snapshot pointer, split definitions, quality audit, example predictions, snapshots |
| `docs/` | Architecture, data provenance, model results, pipeline, NOSE-parity reports, improvement programme |
| `tests/`, `scripts/` | Test suite; artifact verification, shuffle controls, candidate screening, macOS XGBoost repair |
| `results/`, `reports/`, `research_notes/` | Candidate screening, six research syntheses, topic notes |
| `src/calnew/panel.py` | Response bounds and analysis utilities for prospective panel measurements |

**Two endpoints:** catalogue descriptor annotations and airborne detection thresholds.

**Earlier recorded results** (basic models):
- **Thresholds:** outer-fold MAE **0.94 log10 ppbv** (268 records).
- **Descriptors:** macro average precision **0.25** across 90 labels.
- The final holdouts are unopened.

These figures were not re-checked for this update. The docs in `Support/` include newer pipeline and NOSE-parity reports.

## Practical next steps

1. Settle the relief-pressure value and update the feasibility note, parts list and workbook to match.
2. Build the electronics on the bench in the order given in [Doser-4-Line-Wiring.md](Doser-4-Line-Wiring.md):
   1. ESP32 reads the balance and the pressure sensor.
   2. Valves, pump and stop button.
3. Write the dosing firmware (closed loop on the balance), then the wireless interface.
4. Run the four-line dosing, drip, closure and idle-mass tests before scaling up.
5. Commit the vault's `Support/` reorganisation on `modular-pipeline` before merging `main` into it. That turns the 140 "deleted" files into recorded moves.

## About this overview

Rewritten after the three doser branches were merged. The doser sections reflect the merged files in this folder. The CALNEW section was updated only for file locations; its results come from the earlier analysis.
