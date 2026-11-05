# Septum caps with permanent FEP tubes: will they leak?

Companion to `Perfume-Doser-Feasibility.md` §3 (septum in the bottle's own cap). It
covers the case where the two 1/16" FEP tubes stay in the septum for months and are
never removed.

**Short answer:** the seal around a tube that doesn't move has a large margin and won't
start leaking by itself. Over months, the real losses come from three things:

- the tube being moved;
- silicone swelling in terpene-rich materials;
- vapour **permeating** through silicone that is open to the room air.

The third one is not a leak in the pressure sense, but with the cap drilled as first
planned (one Ø 8-10 mm hole) it can exceed the bottle's whole evaporation budget. All
three have cheap fixes, listed at the end, and now applied to the design.

All figures are first-principles estimates (sources at the end). The 4-week log on the
4-line rig replaces them with measurements.

---

## 1. Which layer actually seals

| Layer | What it does | Why |
|---|---|---|
| PTFE face, 0.1-0.25 mm | Vapour shield only, and only where it is intact | PTFE stays elastic for only a few % of stretch. The tube spreads the puncture by ~80 % or more, so the film is drawn and torn around the tube and does not spring back onto it. |
| Silicone, 1.5-3 mm | **The seal** | Rubber spread by the tube pushes back elastically, like a cable gland. |
| Cap + thread | Holds the septum's rim seal and adds axial squeeze | Fixed position, not fixed force. |

This corrects the earlier assumption in the feasibility note that the PTFE face forms a
pressure-energised lip collar. Vendors say the same thing outright: once pierced, a
PTFE/silicone septum has the chemical compatibility of silicone (Waters, Thermo). So
the headspace vapour **does** reach the silicone at the punctures. Diffusion in silicone
is fast (~10⁻⁶ cm²/s, so a 2 mm disc equilibrates in about half a day). Within days the
whole silicone disc will hold whatever the headspace contains.

## 2. Mechanical margin of a still tube

**How tight the seal has to be.** Leak target: < 1 mL/min of air at 20 kPa. That
corresponds to:

| Leak path through a 3 mm thick septum | Air leak at 20 kPa |
|---|---|
| Uniform gap all around the 1.6 mm tube | 4.8 µm gap gives 1 mL/min |
| One channel 100 × 10 µm, full thickness | 0.18 mL/min |
| One channel 100 × 20 µm | 1.5 mL/min |
| One tear 300 × 30 µm | 15 mL/min |

So to leak, the seal has to open a continuous channel through the whole silicone
thickness. A micro-scratch on the tube is not enough: rubber pressed at MPa level fills
it.

**How hard the silicone presses.** Modelled as a cavity expanded in rubber
(neo-Hookean, plane strain): p = G/2 · (ln λ² + 1 − 1/λ²). Septum silicone (Shore A
40-55) has a shear modulus G ≈ 0.4-0.8 MPa. A needle puncture is a slit, so the effective
stretch λ is 1.8-3.

| | Contact pressure on the tube | Margin over 20 kPa |
|---|---|---|
| Soft septum, λ 1.8 | 0.37 MPa | 18× |
| Hard septum, λ 3 | 1.2 MPa | 60× |

**What wears the margin down over time:**

| Effect | Size | Effect on margin |
|---|---|---|
| Stress relaxation of silicone at room temperature | Silicone reaches a near-steady pushback within hours, then changes very slowly; allow −20-30 % over years | Still ≥ 12× |
| Swelling while the bottle stays on (constrained) | The disc cannot expand outward, so swelling *raises* the pressure on the tube. The swollen rubber is softer (G × ~0.7) | Neutral to positive |
| Temperature ±10 K | Silicone expansion ~3 ‰ against an ~80 % stretch | Negligible |
| FEP tube creep under 2-3 MPa hoop stress (from the rubber pressure) | Some ‰ over months. FEP is well below its ~12 MPa yield, and the rubber follows the tube | Negligible |
| Pressure cycles (20 kPa for seconds, thousands of times) | Strain change ≪ 1 % | Negligible |
| Idle state | The bottle is vented through its valve exhaust, so there is ~0 pressure across the septum most of the time | Pressure leaks only matter during doses |

**Conclusion:** a tube that is not moved stays sealed against 20 kPa for years. Nothing
in the static case wears the 18-60× margin down to 1×.

## 3. The four ways it can really leak or lose material

### a) The tube moves (most likely)

- **Friction holds the tube in the septum with only ~0.6-2.8 N** (contact pressure ×
  friction 0.2-0.4 × ~2 mm grip length). FEP is non-stick, so there is no adhesion.
  Internal pressure pushes on the tube with only 0.04 N, so pressure is not the problem.
  A pull on the line is: moving a bottle, or catching a tube with a hand.
- **A movement of 1-2 mm wipes the slit** and can tear it at the slit ends. Bending the
  tubes sideways also opens the puncture on one side.
- **Fix:** strain relief **anchored to the cap**. The earlier plan was a clip that only
  holds the two tubes together, which does not stop the tube sliding through the septum.
  Use a printed saddle that clips onto the cap and clamps both tubes. Two Ø 2 mm holes
  in the cap top (point 3c) also take side loads off the septum.

### b) Swelling in terpene and hydrocarbon materials

PDMS swelling depends on the solvent (Lee/Whitesides). Measured linear swelling ratios:

| Solvent | Linear swelling ratio |
|---|---|
| Ethanol | 1.04 |
| Toluene | 1.31 |
| Xylenes / pentane | up to ~1.4 |

Limonene and pinene are hydrocarbons and belong to the high end; no direct value was
found. Linear 1.3-1.4 means 2.2-2.7× in volume.

- **While the bottle stays on:** the disc is confined, so the seal stays tight or gets
  tighter. The swollen silicone bulges into the cap holes, and its tear strength drops
  sharply.
- **The dangerous moments:**
  - handling a swollen septum at a bottle change, when the weakened slit tears;
  - letting it dry out (empty bottle, cap off for days). It shrinks back, loses
    extractables and does not fully recover, so the old puncture is now loose.
- **Contamination:** small amounts of cyclic siloxanes (D4/D5) and absorbed earlier
  materials can migrate into the headspace. This is a quality issue rather than a leak,
  and it is handled by the existing rule of one septum per ingredient.
- **Fix:**
  - Treat neat terpene/hydrocarbon materials (citrus oils, pinene, limonene, dipentene)
    as "replace septum at every bottle change, never re-dry".
  - Dilutions in ethanol or DPG are benign, because ethanol swells silicone ~4 %.
  - Keep the 4-week test with a neat citrus oil.

### c) Vapour permeation through silicone open to the room air (largest steady loss)

Saturated silicone is a very permeable membrane for organic vapours (thousands to tens
of thousands of Barrer). Whatever silicone the cap leaves open to the room air works as
a permanent evaporation window.

**Upper bound with today's cap (one Ø 9 mm hole, 2 mm silicone, ~20,000-40,000
Barrer):**

| Material | Loss through septum | Exhaust diffusion tube (2.5 mm ID × 30 cm) for comparison |
|---|---|---|
| Limonene (1.5 mmHg) | ~1 mg/day, ~0.4 g/year | ~0.1 mg/day |
| Ethanol (44 mmHg) | ~5 mg/day, ~1.8 g/year | ~1.9 mg/day |
| Ethyl acetate (73 mmHg) | ~30 mg/day | — |
| Heavy materials (Hedione, musks) | ~0 | ~0 |

So with a big hole the septum, not the exhaust tube, is the bottle's main evaporation
path, 3-10× larger for top notes and solvents.

**Why it matters for dosing:** the solvent evaporates faster than the material. A 30 g
10 % dilution in ethanol losing ~1.8 g/year goes from 10.0 % to ~10.6 % in a year. That
is a quiet concentration drift, not a dosing error the balance would catch.

**Fix: drill two Ø 2.0 mm holes 5 mm apart instead of one Ø 8-10 mm hole.**

- Open silicone drops from ~64 mm² to 2 × ~1.1 mm² (the ring between the tube and the
  hole wall), about **28× less**: ethanol ~0.2 mg/day, limonene ~0.04 mg/day. That is
  now below the exhaust tube.
- The holes also guide the tubes straight and serve as the drilling jig for the needle.
- Alternatively, use PTFE/silicone/PTFE sandwich septa, which have a PTFE face on both
  sides.

### d) Rim, cap and handling

- **Cap creep.** PP caps lose part of their tightening torque over days. The rim seal
  survives because the silicone acts as the spring. Re-tighten at the bottle change.
- **Chipped rims and mould seams** are found by the seal check.
- **Turning the cap instead of the bottle** twists both tubes. That is case a), so the
  rule stays: hold the cap, turn the bottle.

## 4. How the seal check sees each failure

The pressure-decay check sees 1 mL/min as ~0.17 kPa/min at 0.6 L, so it catches a), b)
and d) as soon as they start.

It **does not see c)**: permeation is vapour diffusion and needs no pressure difference.
c) has to be prevented by design (small holes), or measured by weighing an idle bottle:

- once a week, log the bottle mass from the balance;
- the expected loss is ≤ ~0.5 mg/day for a dilution in ethanol, with the small holes;
- anything well above that points to the septum or the exhaust tube.

## 5. Changes to the design

| # | Change | Replaces |
|---|---|---|
| 1 | Cap top: **two Ø 2.0 mm holes 5 mm apart** | One Ø 8-10 mm hole |
| 2 | Septum goes into the cap **first**, then pierce with 20 G through the holes, then push the tubes, then screw on | Tubes first, septum into the cap afterwards |
| 3 | Strain-relief saddle **clipped to the cap** that clamps both tubes | Clip that only holds the tubes together |
| 4 | The seal is the silicone; the PTFE face is a vapour shield only | The PTFE "lip collar" as the seal |
| 5 | Neat terpene/hydrocarbon materials: new septum at every bottle change; never let a used septum dry out and reuse it | One septum per ingredient only |
| 6 | Weekly idle-mass log per bottle (permeation check) in addition to the pressure decay | Pressure decay only |
| 7 | Inspect cut tube ends for burrs and the tube for axial scratches in the septum zone | — |

Extra parts: none. A 2.0 mm drill bit replaces the 8-10 mm step; the saddle is a
~1 g print.

**Applied in:** feasibility note §3 (procedure, long-term table, idle-mass log, risks,
build path), the BOM (section D, saddle row D5, cap procedure, tools, build order), the
xlsx (cap row + saddle row; totals unchanged at ≈ €322 / ≈ €682) and the Blender scenes
(`septum_render.png`: two cap holes, cap-anchored saddle, drawn PTFE face; the 8-line and
50-ingredient scenes show silicone only in the two holes).

## Sources

- Waters, PTFE/silicone septum ("chemical compatibility of silicone once pierced"):
  https://www.waters.com/nextgen/lv/en/shop/vials-containers--collection-plates/186002129-red-12-x-32-mm-screw-neck-cap-and-ptfe-silicone-septum-100-pk.html
- Thermo Fisher septa selection guide:
  https://documents.thermofisher.com/TFS-Assets/CMD/Flyers/fl-73838-cc-septa-selection-guide-fl73838-en.pdf
- Lee, Park, Whitesides, *Anal. Chem.* 2003, 75, 6544 (PDMS solvent compatibility, doi
  10.1021/ac0346712); toluene 1.31 via https://www.rsc.org/suppdata/lc/c0/c0lc00356e/c0lc00356e.pdf
- Ethanol swelling 1.04: https://rsc.org/suppdata/d2/ra/d2ra08109a/d2ra08109a1.pdf
- Terpene transport through swollen PDMS (limonene > p-cymene > α-pinene):
  https://research.monash.edu/en/publications/transport-of-terpenes-through-composite-pdmspan-solvent-resistant/
- Organic vapour permeability in rubbery membranes (toluene 22,000-40,000 Barrer):
  https://research.utwente.nl/en/publications/epdm-as-a-selective-membrane-material-in-pervaporation/
- Silicone stress relaxation vs compression set:
  https://silicone.co.uk/news/compression-set-cfd-stress-relaxation-explained/

Calculations: annular and slit gap flow (laminar, air µ = 1.81·10⁻⁵ Pa·s, 3 mm length);
cavity-expansion contact pressure; Fick diffusion for the exhaust tube (D_air ethanol
0.12, limonene 0.065 cm²/s, 20 °C); permeation J = P·A·Δp/L with the open silicone area
and saturated vapour pressure as the upper bound.
