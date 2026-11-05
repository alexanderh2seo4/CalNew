# Perfume auto-doser — feasibility analysis

Scope: a modular, low-cost machine that doses perfume raw materials (neat or diluted)
into one target vial to **±20 mg**, working with **whatever bottles the materials
come in**. One central air pump pressurises the headspace of each ingredient bottle
through its own solenoid; the liquid is pushed out through a dip tube and a dedicated
line to a nozzle above the vial. Arduino-class control. Natural consumer of
[CalNew](../README.md) formulas: the model proposes a formula, the doser makes it, a nose
or the [sponsored olfactometer](../docs/ARCHITECTURE.md#experimental-measurements) supports its sensory evaluation.

**Verdict: doable and cheap, in this form:**

1. **One line per ingredient, valves on the air side only.** Liquid never touches a valve.
2. **Closed-loop gravimetric dosing.** The ±20 mg comes from a balance under the vial,
   read over its data port, not from valve timing. With the balance, ±20 mg is easy
   (2-10 drops, not one).
3. **The bottle's own cap becomes the adapter.** Its liner is replaced by a PTFE/silicone
   septum and both FEP tubes are pushed through it — no special caps, no hold-down,
   works with any threaded bottle.
4. **No camera.** The balance and the pressure sensor cover the checks.
5. **Fully controllable from a phone or PC over Wi-Fi or Bluetooth** (§2a). The ESP32
   joins your home Wi-Fi and serves its own web page; Bluetooth is for first setup and
   for use without Wi-Fi. The dosing loop itself stays on the ESP32, and a stop button
   on the machine always overrides the app.

Rough cost: **~EUR 245-550 base + ~EUR 9-22 per ingredient line**, so ~EUR 315-730
for 8 lines and ~EUR 680-1,610 for 48. 3D concept: [doser-3d/](doser-3d)
(`build_doser_scene.py`, renders, `.blend`).

---

## 1. Does this already exist?

Yes in industry, not as an affordable or open-source machine.

| System | Type | Notes | Price |
|---|---|---|---|
| Accurate Dosing Systems **Veritas** (AU) | Gravimetric robot | "over 1,000 raw materials", sampling + production; also **Quanta** (volumetric, parallel). Built a dedicated robot for Firmenich | Not published; **leasing offered** |
| **Contexa** (CH) | Volumetric dosing | F&F sector specialist | Quote only |
| **Fricke Abfülltechnik** (DE) | Scale-based dosing | Production scale for perfume/aroma makers | Quote only |
| **Chemspeed** SWING XDOSE | Gravimetric liquids, viscous, solids | General formulation robot | Quote only (est. six figures) |
| Mettler Toledo **Quantos** liquid module | Gravimetric, drops < 1 mg | Needs an XPE analytical balance | Quote only (est. tens of k EUR) |
| IFF **Colibri** | In-house robot | Singapore plant: 200 sample batches in 8 h instead of 24 h | Not for sale |
| Givaudan **Carto** (2019) | AI formulation UI + sampling robot | Perfumer-facing; robot makes trials instantly | Not for sale |
| **Osmo** formulation robots | AI → robot compounding | New Jersey facility opened 2026 | Not for sale |
| Opentrons OT-2 / Flex | Generic pipetting robot | Could be adapted; volumetric, needs a balance anyway | from $15,950 / $24,950 (third-party price checks, mid-2026) |
| NINU | Consumer cartridge mixer | Mixes from a fixed set of base vials, no free formulation | Consumer price |
| Benchtop perfume sample fillers | Single-liquid filling | Fill one liquid into vials, not formulate | ~$300-1,200 |
| Perfumix (An-Najah Univ.), Indonesian solenoid+flow-sensor project | Student Arduino builds | ml-scale flow-sensor dosing, far too coarse for perfumery | — |

The South Australian government, announcing the Firmenich contract, said only five
companies worldwide supply this kind of dosing technology. "Est." prices above are my
order-of-magnitude estimates, not quotes.

**Prior art worth reading** (both relevant to the exact concept here):
- **US5898475A** (1997, expired) — precision fragrance dispenser controlled by gas
  pressure. Expired, so the principle is free to use.
- **EP1424129B1** — multi-channel dosing, one micro-valve per channel under a shared
  pressure, with automatic per-channel calibration.

**Gap:** I found no open-source or maker-grade gravimetric perfume doser. The cheapest
real option today is an adapted pipetting robot at ~$16k+.

---

## 2. Architecture

```
 diaphragm pump ─► reservoir (0.5 L) ─► pressure sensor ─► relief valve 30 kPa
                                                 │
                                       PRESSURE MANIFOLD (air only)
            ┌──────────────┬──────────────┬──────┴───────┐
         check valve    check valve    check valve      ...      one module = 8 lines
            │              │              │
         3/2 solenoid   3/2 solenoid   3/2 solenoid            exhaust port of each valve
            │  └─ vent     │  └─ vent     │  └─ vent             → own thin diffusion tube
            ▼              ▼              ▼
     [any bottle]    [any bottle]    [any bottle]   each bottle's own cap with a
     + septum cap    + septum cap    + septum cap   PTFE/silicone septum, 2 tubes through
            │              │              │
       one continuous FEP tube per line: dip tube → septum → nozzle head
            └──────────────┴──────┬───────┘
                         NOZZLE HEAD (all tips above the tallest bottle's max liquid level)
                              │   ← drip shutter (servo)
                           [vial]
                        [BALANCE 0.01 g] ── RS232 ──► ESP32      + draft shield
                                                        │  ▲
                                   Wi-Fi / Bluetooth LE ▼  │ STOP button (cuts valves + pump)
                                                  phone or PC browser
```

Why this shape:

- **Only air touches the valves.** Liquid-side valves are what kill cheap perfume
  dosers: terpenes, ketones and esters swell NBR/EPDM seals and cross-contaminate valve
  bodies. Here the wetted path is the bottle and one FEP tube; the vapour sees the septum's PTFE face.
- **3/2 valve per line** (pressurise ↔ vent). When it drops out, the headspace returns
  to ambient and flow stops within a fraction of a second.
- **Check valve per line** stops vapour from one bottle drifting into the shared
  pressure manifold.
- **Each valve vents through its own exhaust**, not a shared vent manifold — a shared
  vent connects all headspaces while idle. A 20-30 cm length of thin tube on each
  exhaust works as a diffusion barrier, so idle bottles barely evaporate or oxidise.
- **Nozzle tips above every bottle's liquid level.** Otherwise a full line siphons
  after venting and keeps dosing on its own. With mixed bottles this means: above the
  **tallest** bottle's shoulder. Taller bottles go on a lowered shelf or get decanted.
- **Fixed nozzle head, no moving parts.** 1/16" FEP lines bundle into a small head
  over the vial (§7 for 50+).

---

## 2a. Control from a phone or PC: Wi-Fi and Bluetooth

**Yes, the whole system can be run wirelessly, with no extra hardware.** The ESP32
(WROOM-32E) has 2.4 GHz Wi-Fi and Bluetooth LE on the chip.

### What runs where

| On the ESP32 (never over the radio) | On the phone or PC |
|---|---|
| Balance reading, valve timing, preact, the whole dosing loop | Choosing or uploading a formula |
| Pressure limits, pump cut-off, seal check, drip checks | Start, pause, abort |
| The complete current job (stored on the doser) | Live weight, pressure, progress |
| The dose log | Slot setup (material, dilution, fill level), log download |

Wi-Fi latency is 10-100+ ms and irregular. That is fine for watching, but it would ruin
the last-drop timing, so the dosing loop is never closed over the radio. Once a job has
started, the doser runs it to the end without the phone. If the phone disconnects, the
doser keeps going and the page catches up when it reconnects.

### Three ways to connect

| Way | How | Use for |
|---|---|---|
| **Home Wi-Fi** (normal) | The doser joins your Wi-Fi. Open `http://doser.local` (mDNS) in any browser | Daily use, from phone or PC, several viewers at once |
| **Bluetooth LE** | The phone connects directly, no network needed | First setup (sending your Wi-Fi name and password); control where there is no Wi-Fi |
| **Own hotspot** (fallback) | If the home Wi-Fi is not found for ~30 s, the doser opens a `Doser-xxxx` network; same page at `192.168.4.1` | No router nearby; works on every phone without an app |

**First setup:**
1. Power on. The doser has no Wi-Fi yet.
2. Connect from your phone, either:
   - over Bluetooth with Espressif's free "ESP BLE Provisioning" app (iOS/Android), or
   - by joining the doser's hotspot.
3. Pick your Wi-Fi and enter its password. The doser stores it and joins.
4. From then on, use `doser.local`. Holding the ESP32 board's BOOT button for 10 s
   forgets the Wi-Fi and starts setup again.

**Bluetooth on iPhone:** browsers can talk Bluetooth to a device only in Chrome/Edge
on Android, Windows and macOS (Web Bluetooth). Safari on iPhone cannot. So on an
iPhone, Bluetooth is used for setup through the Espressif app, and the hotspot covers
direct control without Wi-Fi. A native app is possible later but not needed.

### The interface

A web page stored in the ESP32's flash: nothing to install, no cloud account.

- **Live view:** weight, pressure, which line is open, progress per ingredient. A
  WebSocket sends ~10 updates/s.
- **Formula:** paste or upload a CSV/JSON list (slot, target mg), or send it straight
  from CalNew with `POST http://doser.local/api/jobs`. The same REST API returns the log.
- **Slots:** name, material, dilution, density and remaining fill per slot; a
  seal-check button per bottle.
- **Log:** actual mass per dose, downloadable as CSV.
- **Manual:** prime or flush a line, open a valve. These work only while the button is
  held, and the doser closes the valve after at most 2 s.
- **Alarms** (drip, blocked line, seal leak) show on the page. Push messages to the
  phone are optional, through a self-hosted service such as ntfy.
- **Firmware updates over Wi-Fi (OTA),** accepted only while idle with every bottle vented.

### Safety when controlled remotely

- **Stop button on the machine:** latching mushroom, 2 NC contacts, ~EUR 17.
  - Contact 1 cuts 12 V to the valves and the pump in hardware. The valves are
    normally closed, so every bottle vents.
  - Contact 2 tells the ESP32, which stays powered, so the page shows "stopped" and
    the log stays complete.
  - No command from the phone can override it.
- **A job starts only** with the stop button released, a stable vial on the balance and
  a passed pressure self-test.
- **Hardware watchdog:** if the firmware hangs, the ESP32 resets. The gate pull-downs
  then switch off every valve and the pump.
- **Access:**
  - PIN on the web page; Bluetooth pairing with a passkey.
  - Reachable only inside your home network; no port forwarding.
  - For control from outside, use a VPN into the home network (e.g. Tailscale on a home
    computer), never an open port.

### Hardware notes

- **Antenna:** the WROOM-32E has its antenna on the PCB. Mount the board outside the
  aluminium frame or metal housing, or use the WROOM-32**U**E variant with an external
  antenna.
- **2.4 GHz only.** Most routers provide it, but the network must not be 5 GHz-only.
- **Memory:** running Wi-Fi and Bluetooth at the same time is tight on the classic
  ESP32 (~320 KB RAM). The firmware runs Bluetooth only for setup and for the no-Wi-Fi
  mode. If both must stay on all the time, use an ESP32-S3 with 8 MB PSRAM
  (~EUR 10-15).
- **50+ lines:** only the main controller has the radio. The 8-line modules stay on the
  wired I²C/12 V bus (§7).

---

## 3. Bottle closure: septum in the bottle's own cap

Requirement: every bottle — 5 mL droppers, Boston rounds, supplier bottles, aluminium
flasks, GL45 lab bottles — gets two passages (liquid out, air in), chemically inert,
vapour-tight, and easy to integrate. Chosen: **keep each bottle's own screw cap and turn
it into a septum cap.** 3D section with a ×4 detail: `doser-3d/septum_render.png`
(`build_septum_scene.py`); all machine scenes use it.

### Design

```
 saddle clipped to cap ─┐   ║ FEP liquid line   ║ FEP air line (both 1/16", 5 mm apart)
                            └───╫───────────────────╫───
              ┌─────────────────╨───────────────────╨─────────┐  bottle's own cap, two Ø 2.0 mm holes 5 mm apart
              │   silicone (red): THE seal, grips each tube     │  PTFE/silicone septum replaces the liner
              │═══PTFE face (white): on the rim ════════════════│
              └──┬───────╲╥╱─────────────────╲╥╱───────────┬──┘  PTFE face drawn down and torn around each
                 │ neck   ║                   ║  air ends  │      tube (vapour shield only, not the seal)
                 │        ║ liquid line       ╨  5 mm below
                 │        ║ = dip tube           the septum
                          ╚═ ~3 mm above the bottle bottom
```

- **Parts per bottle:** its own cap, one PTFE/silicone septum (cents), two FEP tubes, a
  printed saddle. No machining beyond two Ø 2 mm holes, no hold-down, no posts or arms, no spring force on the glass; bottles can
  stand anywhere in a soft rack.
- **The seal on the rim** is the bottle maker's own: thread + liner geometry, with the
  septum's PTFE face where the liner was — the same design that keeps the bottle tight in
  storage. PTFE/silicone septa are made for keeping volatile samples (EPA VOA vials).
- **Sizes:** one septum diameter per thread family: 17.5 mm septa for DIN 18 / GL 18
  dropper caps, 22 mm for 24-400/24-410 caps, ready-made GL 25/32/45 caps with septum for
  lab bottles; trim a larger septum for odd caps (e.g. 28-410, aluminium flasks).
- **Limits:** bottles without a screw thread (stoppered flasks) need the cone adapter
  (alternative A below). Neck ID must take two tubes 5 mm apart (≥ ~7 mm). Remove
  dropper inserts and orifice reducers.

### Getting the tubes through the septum without leaks

The leak path that matters is along each tube, and the layer that seals it is the
**silicone**, which grips the tube elastically. The PTFE face is only a vapour shield:
it is 0.1-0.25 mm thick and stretches elastically by only a few %, so where a tube goes
through it, it is drawn down and torn, not sprung onto the tube. Vendors say the same:
once pierced, a PTFE/silicone septum has the chemical compatibility of silicone. Full
analysis of tubes left in for months: [Septum-Leak-Analysis](Septum-Leak-Analysis.md).

Procedure (per cap, ~3 minutes):

1. **Drill the cap top: two Ø 2.0 mm holes 5 mm apart**, not one big hole. Closer than
   5 mm the punctures can tear into one slot. The small holes leave almost no silicone
   open to the room air (permeation, below), guide the tubes straight and take side
   loads off the septum.
2. **Septum into the cap, the right way round:** PTFE face towards the bottle, silicone
   against the cap top.
3. **Pre-pierce through the two cap holes with a thin needle (Ø 0.9 mm, 20 G)**, much
   smaller than the 1.6 mm tube; the holes act as the jig. Don't punch or drill the
   septum: no material may be removed.
4. **Cut the FEP tube end at ~30° with a sharp blade** and push it through each hole with
   a slight twist. The puncture is a slit, and the tube spreads it to 1.6 mm: the silicone
   grips the tube at ~0.4-1.2 MPa, 18-60× the 20 kPa it has to hold. The PTFE face is
   drawn down around the tube.
5. **Set the depth now:** liquid line ~3 mm above the bottle bottom, air line ending
   ~5 mm below the septum. Re-cut the liquid line end square; check the tube for a burr
   or a scratch along it in the septum zone.
6. **Screw the cap onto the bottle.** Axial compression of the septum squeezes the
   silicone harder onto both tubes.
7. **Strain relief anchored to the cap:** a printed saddle clips onto the cap (two legs
   on the cap skirt) and clamps both tubes in its bar. A clip that only holds the tubes
   together is not enough: friction holds a tube in the septum with only ~1-3 N, so the
   saddle must carry any pull into the cap, not the septum.
8. **Seal check** (below) before first use.

Rules: never slide a tube once the cap is tight (it enlarges the puncture — re-septum
instead); no grease or silicone oil (contaminates and swells); to change the bottle,
hold the cap and **turn the bottle**, not the cap, so the tubes are not twisted.

At 20 kPa the demand is small: a still tube keeps an 18-60× margin, and stress
relaxation, temperature swings, FEP creep and pressure cycles don't wear it down to 1×.
If a puncture ever leaks, the septum costs cents — re-pierce a fresh one.

### Long-term tightness

What has to be tight, and how tight: the seal only carries pressure for the seconds of
a dose (2-20 kPa); between doses the bottle is vented through its valve's exhaust
diffusion tube anyway. Target: **leak < 1 mL/min at 20 kPa** — irrelevant for dosing
(the pump moves ~1 L/min), and it keeps the idle evaporation path no larger than the
exhaust diffusion tube.

| Risk over time | Why it matters | Fix |
|---|---|---|
| Tube pulled or bent (most likely) | friction holds it with only ~1-3 N; 1-2 mm of travel wipes the slit | saddle clipped to the cap clamps both tubes; never slide tubes after tightening |
| Silicone swells/absorbs fragrance (terpenes, hydrocarbons; up to ~1.3-1.4× linear) | the vapour reaches it at the punctures within days; confined it seals *tighter*, but swollen silicone tears easily and a dried-out one no longer seals | one septum per ingredient; neat terpene/hydrocarbon materials: new septum at every bottle change, never let a used septum dry out and reuse it; dilutions in ethanol/DPG are benign (~4 % swell) |
| Vapour permeates through silicone open to the room air | not a pressure leak: the seal check can't see it; with one Ø 8-10 mm hole up to ~5 mg/day ethanol, ~1 mg/day limonene, more than the exhaust tube; dilutions slowly get stronger | two Ø 2 mm cap holes (~28× less open silicone); weekly idle-mass log per bottle |
| Cap relaxes (PP creep, temperature cycles) | rim seal and tube grip drop | silicone layer acts as the spring; re-tighten at bottle change; prefer phenolic/PP caps with a flat top |
| Chipped rim, mould seam on the sealing surface | leak at the rim | seal check flags it; decant into another bottle |
| Puncture torn wide (silicone slit or PTFE flap) | the slit tips are where a leak starts; a big PTFE flap exposes more silicone to vapour | pierce small (0.9 mm) through the cap-hole jig, push slowly with a bevel; re-septum if torn |

**Built-in seal check (pressure decay).** With the pump stopped and one bottle valve
open, the pressure sensor watches the decay: leak ≈ V × (dP/dt) / P_atm. With ~0.6 L
(buffer + manifold + headspace), 1 mL/min shows as ~0.17 kPa/min, easily visible in a
60 s test. A baseline run with all bottle valves closed subtracts the buffer's own leak
(needs a check valve between pump and buffer so the pump cannot leak back). Run it at
every bottle change and daily: < 1 mL/min OK, 1-5 mL/min re-tighten, > 5 mL/min new
septum.

**Idle-mass log (permeation check).** Once a week the balance logs each idle bottle's
mass. Expected with the two small holes: ≤ ~0.5 mg/day for a dilution in ethanol, mostly
via the exhaust tube; anything well above points to the septum or the exhaust tube.

**Honest status:** a still tube in a septum has a large margin on paper (18-60×); the
real risks are tube movement, swelling in terpene-rich materials and permeation, all
with fixes above. The figures are first-principles estimates (swelling and permeation
deliberately pessimistic). The 4-line rig must confirm them: a 4-week pressure-decay
and idle-mass log per bottle with real materials (a neat citrus/terpene-rich one and
ester-rich ones), including temperature swings.

### Changing bottles

- **Same ingredient, new bottle:** hold the cap, turn the bottle off; turn the new bottle
  onto the cap if it has the same thread. Otherwise prepare a cap for the new bottle's
  thread (new septum, new punctures) and move the tubes over. The original cap goes
  back on the old bottle.
- **New ingredient in a slot:** replace the FEP lines and the septum (cleanest), or run
  the flush routine: lines into an ethanol bottle, dose ~2 mL into a waste vial, then
  blow the line dry with the tube out of the liquid. Always a new septum (it has absorbed
  the old material).
- **Bottle identity:** slot = ingredient. The software's refill dialog links the bottle
  to the slot; an optional USB barcode scanner (~EUR 20) reads the supplier label.

Cost per bottle: septum EUR 0.20-0.30 (packs of 100), nothing else.

### Alternative A: universal PTFE cone (bottles without a usable cap)

For stoppered or unthreaded bottles, or a fully thread-independent machine: one 60° PTFE
cone (Ø 42 → 6 mm, 31 mm tall, on a Ø 48 mm flange) seals on the inner rim of any neck from
~7.5 to 40 mm via a ~1 mm non-adhesive ePTFE skin, self-centring. Two bores near the axis
carry the FEP tubes, sealed by spring-loaded PTFE ferrules; a coaxial ~30 N stainless
spring (enough for the GL45 push-out force of ~18 N at 20 kPa) loads seal and ferrules at
constant force, so PTFE creep and the 19 °C PTFE transition do not open it. Needs a
lathe/CNC part and a hold-down per slot. 3D section: `doser-3d/adapter_render_cone.png`
(`build_adapter_scene_cone.py`); parts in the xlsx sheet "Adapter option A".

| | Septum in own cap (chosen) | A: universal cone |
|---|---|---|
| Fits | any threaded bottle with a cap | any neck ID 7.5-40 mm, threaded or not |
| Parts per bottle | one septum (cents) | none (adapter stays with the slot) |
| Build effort | pierce, push tubes, screw on | lathe/CNC cone, ferrules, spring hold-down, posts |
| Vapour-wetted | PTFE face + collars, FEP | PTFE, ePTFE, FEP only |
| Long-term force | thread + silicone (constant position) | spring (constant force) |
| Cost (4-line rig) | ~EUR 60 in septum packs | ~EUR 65-150 incl. hold-downs |

## 4. Can it hit ±20 mg?

### Numbers (Hagen–Poiseuille, 0.5 mm ID FEP line, 0.6 m long; Tate's law for drops)

| Material class | Viscosity (approx.) | Flow at 5 kPa | Flow at 20 kPa |
|---|---|---|---|
| Ethanol dilutions | ~1.2 mPa·s | ~8 mg/s | ~34 mg/s |
| IPM / DEP, most neat aroma chemicals | ~5-10 mPa·s | ~1.5-2 mg/s | ~6-7 mg/s |
| TEC | ~35 mPa·s | ~0.4 mg/s | ~1.7 mg/s |
| DPG | ~75 mPa·s | ~0.17 mg/s | ~0.7 mg/s |
| Resinoid / absolute, 50% | 500+ mPa·s | ~0.03 mg/s | ~0.1 mg/s |

- Drop mass from a 0.5-1.6 mm tip: **~2-10 mg** for perfume liquids (low surface
  tension; water drops would be 7-22 mg). So ±20 mg is ~2-10 drops.
- Valve switching ~10-20 ms → ~0.5 mg of ethanol, negligible.
- **The viscosity spread is ~500×.** Timed dosing cannot cover it; the balance can.
  Use a 1 mm ID line for slow classes (16× the flow), and pre-dilute anything thicker
  than ~TEC in ethanol or DEP — perfumers dilute those anyway. Solids (vanillin,
  crystalline musks) always as dilutions.
- Line dead volume (0.5 mm × 0.6 m) ≈ **120 µL ≈ 100 mg**. If the line drains back
  between doses, each dose starts with a priming phase — harmless with the balance.
- Headspace grows as a bottle empties, and bottles differ in size, so flow per second
  differs per slot and over time. Again only a problem without the balance.

### Dosing algorithm

1. Check the vial is stable (no drips) for ~3 s with all valves closed. Tare.
2. Open the line at full pressure until ~85% of target (rate learned per line).
3. Short pulses; use only settled readings (~1-2 s) for the last steps.
4. Close; wait until the reading settles (after-drip of the same line is counted
   correctly); close the shutter; log the **actual** mass.

Learn per line how much still arrives after the valve closes (liquid in flight plus
balance lag) and close that much early — industrial gravimetric dosers call this
in-flight compensation or "preact".

Expect ~10-30 s per ingredient, ~5-10 min for a 20-ingredient formula.

---

## 5. Balance interface

Read the balance's own data port; a camera reading the display is cheaper only for a
balance with no port at all.

- **Which port?** 9 pins in 2 rows = RS232 serial (usual). 15 pins in 3 rows = VGA
  (rare on balances). They look alike.
- **RS232:** MAX3232 level-converter board (~EUR 2) to the ESP32, or a USB-serial adapter
  (~EUR 8) to a PC. Readings arrive as text lines like `+  12.34 g` with a "stable" flag.
- **Real VGA:** a VGA-to-USB capture stick (~EUR 15-25) gives a clean digital image of the
  display; template-matching OCR on a fixed font is reliable. Second-best to serial.
- **Display-OCR with a camera** (~EUR 8 ESP32-CAM) only without any port: 2-5 updates/s,
  glare, and a misread digit is a 100 mg+ error, so every reading needs plausibility checks.

Balance settings:

- **Continuous output at the highest baud rate.**
- **Fastest filter / response setting.**
- **Auto-zero tracking OFF.** It silently zeroes slow changes near zero — right after
  taring that can swallow a slow viscous trickle or a drip.
- **0.01 g readability is enough for ±20 mg** (repeatability of cheap units 10-20 mg —
  test before trusting). 0.001 g units with RS232: ~$200 (US Solid) to ~EUR 455 incl. VAT
  (RS PRO 805-6682); Ohaus 0.001 g with USB+RS232 ~$1,500.
- **Draft shield** around the vial.

---

## 6. Monitoring without a camera

| Check | How |
|---|---|
| Dose correct | Balance (the control loop itself) |
| Drip into the vial | Mass must stay flat with all valves closed before every dose → alarm |
| Bottle empty / line blocked | Line pressurised, but mass does not rise → alarm |
| Adapter not seated / leaking | Manifold pressure sags or the pump runs on while that line is open |
| Wrong bottle on a cap | Refill dialog + optional barcode scan of the bottle |
| Low stock | Software subtracts every dose from the bottle's recorded fill |
| Cap / septum leaking | Pressure-decay seal check (§3) at every bottle change and daily |
| Septum permeation (vapour, no pressure) | Weekly idle-mass log per bottle (§3) |

**Blind spot:** all tips hang over the vial, so a drip from *another* line during a
dose is counted to the current ingredient. Mitigations: wait for each line's after-drip
to settle before the next opens, non-wetting FEP tips, shutter closed between doses,
optional suck-back (the pump's inlet side gives vacuum for one more valve per line).
If the test rig shows foreign drips anyway, a camera on the nozzle head is the add-on.

---

## 7. Scaling to 50+ lines without a tube mess

- **8-line modules.** Each module carries its own valve block, 8 bottle slots (soft
  rack, septum caps), a line comb, and one braided sleeve with its 8 FEP lines to the nozzle
  head. Modules daisy-chain the air bus and the I²C/12 V bus around the outside;
  nothing else crosses between them.
- **Octagon layout for 50 ingredients** (3D model: `doser-3d/build_doser_scene_50.py`,
  renders `doser_render_50.png`, `doser_top_50.png`): 7 modules × 8 slots on seven
  sides of an octagon around the balance = 56 slots, 50 used, 6 spare. The eighth side
  stays open as the access front for the vial, pump and electronics. With 52 mm slot
  pitch (bottles up to ~48 mm wide) the bottle row sits 0.53 m from the centre and the
  whole unit is **~1.4 m across**.
- **Lines are equal spokes of ~0.7 m** (septum → comb → sleeve → head). That is ~140 µL
  ≈ 120 mg dead volume and ~0.8× the flow of the 0.6 m figures in §4 — harmless with
  the balance, but use 1 mm ID lines for the slow materials. The nozzle head stays
  higher than the tallest bottle's liquid level, so bottles stand directly on the
  module plates.
- **One machined nozzle head plate** (PTFE/POM) with 56-64 numbered 1/16" bores in a
  hex pattern at ~2.4 mm pitch — fits in a ~22 mm circle over a wide-mouth vial
  (≥ 25 mm opening). The head hangs from one post between two sleeves.
- **Slot numbers on both ends of every line** and on each cap (M1-1 … M7-8).
- **Smaller footprint**, if needed: two concentric tiers (inner ring lower), at the
  cost of a higher nozzle head.

---

## 8. Bill of materials (budget parts, EUR, Oct 2026 estimates)

### Base unit (once)

| Item | ~EUR |
|---|---|
| Balance 0.01 g, RS232 (skip if you already have one) | 120-250 |
| 12 V diaphragm pump, oil-free | 10-20 |
| Air reservoir 0.5 L + pressure sensor (XGZP6847-class) + relief valve | 15-30 |
| Low-pressure regulator 0-0.2 bar (optional if the pump runs closed-loop on the sensor) | 0-60 |
| ESP32 (Wi-Fi + Bluetooth on board) + MAX3232 + 12 V 5 A supply | 30-55 |
| Stop button, latching, 2 NC (§2a) | 15-20 |
| Drip shutter servo, nozzle head (printed or PTFE), draft shield | 15-40 |
| Frame (2020 aluminium extrusion or printed) + wiring | 40-80 |
| **Total** | **~245-550** |

### Per ingredient line

| Item | ~EUR |
|---|---|
| 3/2 mini solenoid valve, 12 V (FKM-sealed: +5-30) | 3-8 |
| Inline check valve (FKM) | 1-3 |
| PTFE/silicone septum in the bottle's own cap (share of a 100-pack) | 0.2-0.3 |
| FEP tubing ~1 m (continuous dip tube + line) | 2-6 |
| Air line (PE/FEP near the bottle) + push fittings, exhaust diffusion tube | 1-2 |
| Nozzle tip (blunt stainless needle or cut FEP) | 0.3-1 |
| MOSFET channel on an 8-channel driver board | 1-2 |
| **Total** | **~9-22** |

| Lines | Budget build |
|---|---|
| 8 | ~EUR 315-730 |
| 16 | ~EUR 390-900 |
| 48 | ~EUR 680-1,610 |
| 64 | ~EUR 820-1,960 |

---

## 9. Risks, ranked

1. **After-drip / foreign drips** from idle nozzles over the vial. The main accuracy
   and contamination risk of a shared nozzle head. Mitigations in §6.
2. **Viscosity range.** Solved by the balance plus per-class line ID plus dilution
   rules; the software must account for the solvent carried by dilutions.
3. **Siphoning** with mixed bottle heights. Rule: tips above the tallest bottle's
   shoulder; enforce with a maximum bottle height for the rack.
4. **Septum and tube passages.** The silicone seals and has a large margin while the
   tube stays still; risks are tube movement (saddle clipped to the cap), swelling in
   terpene-rich vapour (new septum at bottle changes) and permeation (two Ø 2 mm cap
   holes) — 4-week pressure-decay and idle-mass log in the rig, seal check at every
   bottle change. Chipped rims and odd caps may not hold pressure (decant).
5. **Material compatibility.** Silicone, PVC, Tygon, NBR, PU must never be wetted
   (the septum's silicone sees only vapour, at the punctures). Valves see vapour during venting;
   NBR seals swell slowly — prefer FKM.
6. **Cross-contamination via air** — handled by check valves and separate exhausts.
7. **Changing ingredients in a slot** — flush routine or a new FEP line; a forgotten
   flush contaminates the next material.
8. **Evaporation / oxidation** of top notes in air-filled bottles. Diffusion tubes help;
   nitrogen instead of the air pump is the later upgrade.
9. **Pressurised unknown bottles.** Stay at 2-20 kPa, relief valve at ≤30 kPa.
10. **Ethanol vapour + brushed pump motor.** Keep the pump away from the exhaust outlets.

---

## 10. Alternatives considered

- **Carousel + docking head:** bottles on a turntable, one docking head pressurises the
  bottle at the dispensing spot; one valve for the whole machine and ~EUR 4-9 per
  ingredient, the tidiest plumbing. **Not chosen:** every bottle needs a special
  dispensing cap with a fixed nozzle geometry, and the ring fixes the bottle size, so it
  cannot take arbitrary bottles with a simple adapter. Concept kept in
  `doser-3d/build_doser_scene_carousel.py` and its renders.
- **Universal PTFE cone adapter** (§3, alternative A): fits unthreaded bottles too and
  touches only fluoropolymers, but needs a lathe/CNC part and a spring hold-down per slot.
  Kept for bottles without a usable cap.
- **Pipetting gantry** (adapted 3D printer + syringe/pipette + the same balance,
  disposable tips): ~EUR 500-900, no per-ingredient cost, zero carry-over, but slower
  and worse with viscous materials. Good for the long tail of rarely used materials.

---

## 11. Build path

1. **4-line test rig** (~EUR 340 with budget parts, excl. balance and tools; complete
   parts list in [Doser-4-Line-BOM](Doser-4-Line-BOM.md) with four very different bottle types
   (15 mL dropper to GL45), each closed by its own cap with a septum; ethanol, DEP, a 10%
   ethanol dilution, TEC. Measure per line: dose error over 30 doses at 50 mg and 500 mg
   targets, septum-cap leak at 20 kPa and idle mass loss (4-week log, incl. a neat
   citrus/terpene-rich material),
   after-drip events per hour, flow drift as the bottle empties.
   **Go criterion:** 95% of doses within ±20 mg, zero unnoticed drips.
2. Web page and REST API on the ESP32 (§2a): Wi-Fi setup over Bluetooth, live view,
   job upload; formula importer (CalNew output → dose list, per-bottle dilution and
   density table), refill/flush routines.
3. First 8-line module PCB + printed manifold; then replicate modules in the stadium layout.
4. Then: suck-back, nitrogen, cone adapters for unthreaded bottles.

---

## Sources

- [Accurate Dosing Systems — Perfumer & Flavorist directory](https://www.perfumerflavorist.com/directory-services/equipment-lab-manufacturing/company/21170630/accurate-dosing-systems)
- [ADS robot for Firmenich — Australian Manufacturing](https://www.australianmanufacturing.com.au/accurate-dosing-systems-set-to-provide-purpose-built-robot-for-belgium-giant-firmenich)
- [IFF smart dosing robot — MarketScreener](https://www.marketscreener.com/news/iff-introduces-smart-dosing-robot-to-transform-fragrance-production-ce7d5edcdb8cf420)
- [Givaudan Carto launch](https://www.givaudan.com/print/17256)
- [Osmo New Jersey facility — Manufacturing.net](https://www.manufacturing.net/software/news/22966744/ai-fragrance-company-opens-manufacturing-facility-in-new-jersey)
- [Chemspeed SWING XDOSE](https://www.chemspeed.com/example-solutions/swing-xdose)
- [Mettler Toledo Quantos liquid dosing datasheet](https://www.mt.com/content/dam/P5/labtec/Product_Datasheet/Quantos_Liquid_Dosing/30012924_DS_fr_Quantos_Liquid_Dosing_Module_LR_07_2015.pdf)
- [Opentrons price guide 2026](https://grabarobot.com/blog/opentrons-lab-automation-robot-price-guide-2026/)
- [US5898475A — precision fragrance dispenser](https://patents.google.com/patent/US5898475A/en)
- [EP1424129B1 — multichannel dispenser auto-adjustment](https://data.epo.org/gpi/EP1424129B1)
- [NINU — Yanko Design](https://www.yankodesign.com/2021/12/08/robots-perfumes-how-this-tiny-little-contraption-is-disrupting-the-massive-luxury-fragrance-industry/amp/)
- [Perfumix Machine — An-Najah](https://repository.najah.edu/items/6335497e-51aa-440d-842e-9a837ec9cd1e)
- [Sample perfume filler buying guide — Alibaba](https://smartbuy.alibaba.com/buyingguides/sample-perfume-filling-machine)
- Balances: [RS PRO 0.001 g RS232](https://es.rs-online.com/web/p/balanzas/8056682), [U.S. Solid 0.001 g RS232](https://www.walmart.com/ip/397429009), [Ohaus 0.001 g](https://solutionsdirectonline.com/ohaus-precision-balance-320gx0-001g-30429840)

Flow, drop-mass, dead-volume and hold-down figures are first-principles estimates
(Poiseuille, Tate's law with a 0.6 correction factor, F = ΔP·A); the test rig in §11
replaces them with measurements.
