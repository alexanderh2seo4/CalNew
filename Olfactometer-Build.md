# Dynamic dilution olfactometer — build specification

Scope: a two-stage dynamic dilution olfactometer for determining odour detection
thresholds of pure aroma compounds, buildable for roughly EUR 700-1400.

It is **not** EN 13725 compliant. The gap is documented in the last section, and it
is mostly port flow rate. Everything else — traceability, panel handling, the maths —
follows the standard closely enough that results can be reported against it with a
stated deviation.

---

## 1. Architecture

```
 synthetic air cylinder (or pump + silica + carbon)
        |
        +---------------------------+
        |                           |
   carrier Q_c                 dilution air (humidified)
        |                           |
  syringe pump ---> heated evaporator|
        |                           |
     SOURCE C_0                     |
        |                           |
        +-----> stage 1 mix <-------+       ratio Z1 <= 100
                   |
                excess vent
                   |
        +-----> stage 2 mix <---- more dilution air    ratio Z2 <= 100
                   |
                excess vent
                   |
              3-way split, matched line lengths
             /            |            \
          port A       port B        port C      (odorant into ONE, after split)
```

Two cascaded stages, each at most 1:100. A single stage cannot span the four to five
decades a threshold series needs; chaining two verified stages can.

Everything after the evaporator is PTFE, FEP, glass or stainless. No silicone, no
Tygon, no PVC, no rubber septa.

---

## 2. Bill of materials

| Module | Item | ~EUR |
|---|---|---|
| Air | Synthetic air cylinder 10 L + regulator (rental) | 150/yr |
| Air | *or* oil-free diaphragm pump + silica gel + activated carbon + 2 L ballast | 120 |
| Air | Bubbler humidifier, glass, distilled water | 30 |
| Source | Syringe pump (lab used, or DIY stepper + NEMA17 + lead screw) | 60-350 |
| Source | Gastight glass syringe 100 uL and 1 mL, PTFE plunger | 90 |
| Source | Evaporator: 1/4" stainless tee + heating tape + PID controller + K-type | 110 |
| Flow | 3x mass flow controller, used Brooks/Bronkhorst 0-1 / 0-5 / 0-20 L/min | 450 |
| Flow | *or* 3x rotameter + needle valve (calibrate yourself) | 120 |
| Flow | Soap-film flowmeter: 100 mL burette + bulb + stopwatch | 30 |
| Plumbing | FEP tubing 4/6 mm, 10 m; PTFE ferrule fittings; glass mixing bulbs | 140 |
| Port | 3x glass funnel nosepiece, matched FEP lines, 3-way manifold | 60 |
| Verify | PID handheld VOC meter, used (ppb resolution preferred) | 300-1400 |
| Ref | n-butanol, reagent grade | 25 |

Minimum viable: pump air + rotameters + DIY syringe pump + no PID ~ EUR 700.
The PID is the single best marginal euro after that.

---

## 3. How the concentration is assured

Four independent layers. Each one can fail; they fail differently, which is the point.

### Layer 1 — Source, gravimetric

Concentration leaving the evaporator:

    C_0 [ug/L] = c_sol [ug/uL] * Q_syr [uL/min] / Q_c [L/min]

`ug/L` is numerically identical to `mg/m3`. Every term is weighable: the solution is
made up gravimetrically on a 0.1 mg balance, and the syringe rate is verified by
weighing delivered mass over 30 min (`Q_syr = m / (rho * t)`).

Alternative source for volatile compounds: a **permeation tube** in a thermostatted
block. Emission rate `E` from mass loss over 2-4 weeks, then `C_0 = E / Q_c`.
Permeation rate changes roughly 3-5 % per degree C, so hold the block to +/- 0.2 C
and record the temperature with every run.

#### Solvent selection

The test is not "is it odourless" but whether the solvent's odour activity value stays
far below 1 while the analyte reaches its own threshold:

    OAV = concentration / that compound's threshold
    require:  mass fraction of analyte  >>  T_analyte / T_solvent

The two regimes work by opposite mechanisms.

*Static jars* rely on the volatility gap. You smell headspace, not liquid, so a high
boiler is nearly absent from the gas phase even at 99.99 % of the liquid. Use DPG,
isopropyl myristate or triethyl citrate. Note the solvent's headspace contribution is
constant down the whole ladder while the analyte's falls, so its relative contribution
is worst at the threshold step.

*Dynamic flash evaporation* gets nothing from volatility — all of the solvent enters
the stream regardless of boiling point. DPG is the wrong choice here; it fogs instead
of evaporating. Use a volatile, high-threshold solvent and let the cascade do the
work. Worked example: 5 uL/min hexane into 1 L/min carrier is ~940 ppm at source;
after the 1:10^4 that brings the analyte to threshold it is ~94 ppb against a
threshold near 65000 ppb, so OAV ~ 0.001. Prefer n-pentane or cyclohexane over
n-hexane, which is neurotoxic on chronic exposure. Water when the analyte allows it.

**Purity beats identity.** Technical grades carry odorous impurities above the parent's
own contribution, and aged ethers form peroxides that decompose to aldehydes with
thresholds in the low ng/m3. HPLC grade, glass, under nitrogen, dated. Never
denatured ethanol.

**Acceptance test, per solvent lot:** run the solvent alone at the highest rate you
will ever use against clean air in a 3-AFC. The panel must be at chance. Published
solvent thresholds are as unreliable as every other threshold compilation; this test
is the only one that is about your rig. Target OAV below 0.1, not just below 1 —
sub-threshold components still cause mixture suppression.

**Fallback: matched blanks.** Feed the identical solvent stream to all three ports so
it is common-mode and the forced choice sees only the analyte. Second best: a
perceptible solvent background suppresses the analyte and inflates thresholds.

**Or no solvent at all.** A thermostatted saturator or permeation tube running neat
material has no vehicle, and gravimetric assurance is cleaner — weigh the vessel
before and after, divide by gas volume passed. Slow for low-volatility solids, but the
right source for lead compounds needing a defensible absolute number.

### Layer 2 — Dilution, primary flow calibration

    Z_stage = (Q_sample + Q_dilution) / Q_sample
    C_final = C_0 / (Z1 * Z2)

Do not trust the scale printed on a rotameter. Calibrate every flow path against a
soap-film flowmeter, which is a primary volumetric standard: time a soap film over a
known burette volume, `Q = V/t`, correct to reference conditions:

    Q_ref = Q_meas * (P_meas / P_ref) * (T_ref / T_meas)

Accuracy about 1 %, cost about EUR 30. Calibrate at five points across each range,
fit a curve, keep the table. Re-check quarterly.

**Verify each stage alone, never the product.** Measure Z1 with stage 2 bypassed and
Z2 with stage 1 bypassed. A compounded error in a cascade is invisible end-to-end.

### Layer 3 — Analytical verification, PID

The PID is not compound-specific and its absolute calibration does not matter here.
What matters is **linearity**: set the rig to nominal 1x, 2x, 5x, 10x, 20x dilution
and confirm the PID response tracks 1/Z. If a 2x dilution step does not halve the
signal, a flow is wrong, a line is leaking, or you are adsorbing.

The same instrument gives you the **equilibration time**. Step the concentration and
watch the rise and fall. At low ppb with cold lines this can be 20-30 minutes. That
number goes straight into the operating protocol — most home rigs fail here, not in
the arithmetic.

### Layer 4 — Biological anchor, n-butanol

Run n-butanol through the whole rig and have the panel find its threshold. It must
land near 40 ppb, i.e. 123 ug/m3. If the rig says 40 ppb and the panel says 300, you
are losing material to the walls somewhere between the evaporator and the nose.

Worked check of the unit definition, useful as a self-test of your own maths:

    123 ug / 74.12 g/mol         = 1.659 umol n-butanol
    1 m3 air / 24.45 L/mol       = 40.9 mol air
    1.659 umol / 40.9 mol        = 0.0406 umol/mol  = 40 ppb   OK

General conversion at 25 C, 1 atm:

    ppb = C [mg/m3] * 24450 / MW [g/mol]

---

## 4. Build notes per module

**Air supply.** A cylinder of synthetic air is cleaner and steadier than any pump and
removes a whole class of blank problems. If using a pump: oil-free diaphragm, then
silica gel (water), then activated carbon (VOC), then a 2 L glass ballast bottle to
damp pulsation, then a needle valve. Pulsation is audible at the port and panelists
detect rhythm, not odour.

**Humidify to 40-60 % RH.** Dry air stings — that is trigeminal, not olfactory, and it
will show up as false positives. Humidify the dilution air, not the odorant line, or
you will condense analyte in the bubbler.

**Evaporator.** Hold it 30-50 C above the boiling point of the solvent, with enough
residence volume for complete flash evaporation. Incomplete evaporation gives aerosol,
and aerosol gives you a concentration that is real but not the one you calculated.
Heat-trace the line from evaporator to stage 1.

**The three ports must be indistinguishable.** Identical funnel geometry, identical
FEP line lengths cut to the millimetre, identical flow. Split the total flow
symmetrically first, then inject odorant into one branch after the split. The classic
failure is that the sample port has a slightly higher flow and the panel detects the
draught. Test it: run all three ports blank and confirm the panel sits at chance.

**Port flow.** EN 13725 wants about 20 L/min per port so the panelist inhales without
resistance and without entraining room air. Three ports at 20 L/min is 60 L/min, which
is beyond a hobby pump. Two workarounds:
- funnel nosepiece at 5-10 L/min, accept the deviation, validate with n-butanol;
- **sequential single-port presentation** — one port, three timed intervals, the
  panelist names the interval that carried the odour. Same 3-AFC statistics, one third
  of the flow, one third of the plumbing. This is the better home design.

---

## 5. Operating protocol

1. Purge the whole train 30 min at the highest dilution before the first triad.
2. Always ascend. After each concentration change, wait the equilibration time you
   measured in Layer 3 before presenting.
3. Blank triads scattered through the session to measure false-positive rate.
4. One repeated concentration per session for within-person repeatability.
5. Stop at 30-40 min per panelist. Fatigue sets session length, not schedule.
6. Log for every triad: date, time, room temp, block temp, all flows, syringe rate,
   solution lot, panelist code, response. The log is the dataset.
7. Threshold per person = geometric mean of the last miss and the first sustained hit.
   Panel value = geometric mean across people. Everything in log10.

---

## 6. Known failure modes

| Symptom | Cause |
|---|---|
| Panel picks blanks above chance | port flows unmatched, or air not clean |
| Thresholds drift upward over a session | wall adsorption, lines too cold |
| Threshold 5-10x higher than literature | losses between evaporator and port |
| One panelist wildly insensitive | specific anosmia — screen before enrolling |
| Irreproducible between days | solution remade, or block temperature unlogged |
| PID nonlinear across dilution | leak at a fitting, or flow meter out of calibration |
| Everything smells faintly the same | silicone somewhere in the train |

---

## 7. Gap versus EN 13725

| Requirement | Standard | This rig |
|---|---|---|
| Port flow | ~20 L/min | 5-10 L/min, or sequential single port |
| Panel size | >= 4 qualified | recruit 5-8, screen on n-butanol |
| Panel qualification | ITE 20-80 ppb, antilog SD <= 2.3 | same criteria, self-administered |
| Reference | EROM, certified material | n-butanol, reagent grade |
| Dilution step | <= factor 2 | set to 2, or 3.16 for faster screening |
| Accreditation | ISO 17025 lab | none |

Report results as "determined by dynamic dilution forced choice following the
principles of EN 13725, with the deviations listed" — not as EN 13725 values. The
2022 revision's SROM procedure is the route to making a marine-note reference
traceable if this ever needs to be defensible.

---

## 8. What this rig is actually for

Absolute thresholds from a home rig will not beat the literature spread. Internal
consistency will. One rig, one protocol, one panel, forty analogs measured the same
week is a cleaner training signal than forty literature values from twenty labs — and
that consistency, not accuracy, is what a QSAR model needs.

Use rank-ordering at fixed dilution for the bulk of a series and full threshold
determinations only for a handful of anchor compounds. See the project canvas.
