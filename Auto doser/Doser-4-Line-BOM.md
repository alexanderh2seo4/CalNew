# 4-ingredient doser — complete parts list

Everything needed to build the 4-line test rig from
[Perfume-Doser-Feasibility](Perfume-Doser-Feasibility.md) §11: per-line air
pressurisation, septum in each bottle's own cap, closed-loop dosing on the balance, no camera,
controlled from a phone or PC over Wi-Fi or Bluetooth (feasibility note §2a).

**Total ≈ EUR 342 with budget parts, ≈ EUR 702 lab-grade** (listed prices, see the
xlsx), not counting the balance, the test liquids (you have both), shipping and tools. Prices are Oct 2026
estimates incl. VAT; check before ordering.

**Shop links and listed prices:** [Doser-4-Line-BOM.xlsx](Doser-4-Line-BOM.xlsx) — budget
version (mostly AliExpress + Reichelt/BerryBase) ≈ EUR 342, lab-grade ≈ EUR 702, with
septum caps. As listed on 22.10.2026, shipping excluded. The cone adapter (option A) is
costed in its own sheet. The spreadsheet supersedes the estimates below.

**Measure before ordering:**
1. **Bottle caps:** note each bottle's thread (DIN 18 / GL 18, 24-410, GL 45 …) to pick
   the septum sizes; neck ID must take two tubes 5 mm apart (≥ ~7 mm); remove dropper inserts.
2. **Balance port:** count the pins (9 in 2 rows = RS232), note the connector gender, and
   find the interface settings in the manual (baud rate, continuous-output mode, command
   for "send weight"). This decides whether you need the null-modem adapter (§A).

---

## Pneumatics and wiring at a glance

Every wire and tube, numbered, with pin map and test order: [Doser-4-Line-Wiring](Doser-4-Line-Wiring.md).

```
PNEUMATICS (air only — no liquid ever reaches these parts)

 pump ──► PET buffer bottle ──┬──► pressure sensor
 (12 V)       0.5 L           ├──► relief: check valve 0.3-0.5 bar, outlet open to air
                              └──► 1→4 manifold
                                      │  (×4)
                                   check valve (low cracking)
                                      │
                                   3/2 valve NC  P ─► A ──► FEP air tube through septum ──► bottle headspace
                                                  R ──► 30 cm thin exhaust tube (diffusion barrier)

LIQUID (per line)
 bottle bottom ── FEP 1/16" × 0.5 mm, one piece ──► through septum ──► nozzle head ──► vial on balance

ELECTRICS
 12 V PSU ── fuse 3 A ──┬── STOP contact NC1 ──┬── valves V1-V4 (+) ── low side: MOSFET modules ← ESP32 GPIO 25/26/27/33
                        │                      └── pump (+) ───────── low side: MOSFET module  ← ESP32 GPIO 32 (PWM)
                        │      Schottky diode across every coil and the pump (cathode to +12 V)
                        └── buck 12→5 V ──┬── 1N5819 ── ESP32 5V pin   (stays powered when STOP is pressed)
                                          └── servo V+   ← ESP32 GPIO 13 (signal)
 ESP32 GPIO 21/22 (I²C) ── pressure sensor (3.3 V)
 ESP32 GPIO 16/17 (UART2) ── MAX3232 TTL side ── DB9 ── balance RS232
 ESP32 GPIO 34 ── STOP contact NC2 ── GND; 10 kΩ pull-up to 3.3 V (reads HIGH = stopped)
 ESP32 radio: Wi-Fi 2.4 GHz + Bluetooth LE ⇄ phone / PC browser
 all grounds common
```

Rules that matter:
- **Valves normally closed + 10 kΩ pull-down on every MOSFET gate.** At power-up, reset or
  crash, every bottle is vented and the pump is off. Don't use ESP32 strapping pins
  (GPIO 0, 2, 12, 15) or pins that pulse at boot (GPIO 1, 3, 5, 14) for loads.
- **Stop button cuts the load power in hardware**, not through the ESP32. The firmware
  only reads its second contact, so no app command and no firmware bug can override it.
- **The radio only sends jobs and shows status.** The dosing loop never waits on Wi-Fi;
  manual valve commands from the app time out after 2 s.
- **Keep the ESP32's PCB antenna clear of the aluminium frame** (or use a WROOM-32UE
  with an external antenna).
- **Pressure limits:** software target 2-20 kPa, pump cut-off at 25 kPa, hardware relief at
  30-50 kPa. The cheap mini valves are rated ~40-47 kPa (300-350 mmHg).
- **Nozzle tips higher than the tallest bottle's shoulder** (no siphon).
- **Never in the liquid path:** silicone, PVC, Tygon, PU, NBR, 3D-print plastics.

Power budget: valves ~0.1-0.2 A each (normally one open at a time), pump 0.3-0.6 A
(~1 A stall), ESP32 ~0.25 A and servo up to ~0.6 A on 5 V → under 2 A at 12 V. A 3 A
supply is enough.

---

## Parts

### A. Weighing

| # | Part | Spec / what to look for | Qty | Budget ~EUR | Upgrade ~EUR |
|---|---|---|---|---|---|
| A1 | Balance | **You have one.** Needs a data port; 0.01 g readability is enough. If buying: KERN PCB 350-3 (350 g, 0.001 g, RS232) | 1 | 0 | ~305-400 |
| A2 | RS232 ↔ TTL module | MAX3232 with DB9, runs on 3.3 V | 1 | 3 | — |
| A3 | DB9 null-modem adapter + gender changer | Only if TX/RX or connector gender don't match (check with the manual) | 1 | 5 | — |
| A4 | Draft shield | Acrylic tube Ø 90-100 mm × ~120 mm + acrylic lid with a 30 mm hole for the nozzles | 1 | 10 | — |
| A5 | Target vials | 20 mL glass vials with caps, opening ≥ 20 mm | 20 | 12 | — |

### B. Air supply and valves

| # | Part | Spec / what to look for | Qty | Budget ~EUR | Upgrade ~EUR |
|---|---|---|---|---|---|
| B1 | Diaphragm air pump | 12 V, oil-free, ≥ 1 L/min, max pressure ≥ 40 kPa (370-size pump) | 1 | 8 | BODENFLO BD-02A1L (1 bar, 1 L/min) 25 |
| B2 | Buffer reservoir | 0.5 L PET bottle + 2 bulkhead push-in fittings 4 mm in the cap (PET holds bar, not kPa) | 1 | 6 | small aluminium air tank 15 |
| B3 | Pressure sensor | XGZP6847D040KPG: 0-40 kPa gauge, I²C, 3 mm port (check the supply voltage in its datasheet) | 1 | 6 | Adafruit MPRLS breakout (Honeywell, 3.3 V, Arduino library) 17 |
| B4 | Overpressure relief | Adjustable relief valve set to its 0.5 bar minimum + 4 mm push-in fitting, outlet open to air (exact parts in the xlsx) | 1 | 12 | Brass safety valve 0.5-1 bar G 1/8" + push-in fitting, both FKM-sealed 26 |
| B5 | Manifold | Push-in distributor 1→4 for 4 mm tube + 2 push-in tees | 1 set | 10 | — |
| B6 | 3/2 solenoid valves | Mini 3/2, 12 V DC, **normally closed**, ≥ 300 mmHg, 3 mm barbs (0520E/FA0520-type) | 4 | 16 | FKM-sealed mini 3/2 (SMC/Clippard class) 120-200 |
| B7 | Check valves | 4 mm in-line, cracking pressure ≤ 2 kPa; one per line + one after the pump (so the pressure-decay seal check can run with the pump off) | 5 | 17 | SMC AKH04 55 |
| B8 | Air tube | PU 4 mm OD × 2.5 mm ID, 5 m (air side only; also fits the 3 mm barbs) | 1 | 5 | PE near the bottles |
| B9 | Exhaust diffusion tubes | 4 × 30 cm thin tube on each valve's R port (PU 2.5 mm ID offcuts) | 4 | 0 | — |
| B10 | Silicone tube 1 × 3 mm, 1 m | Sleeve joints FEP 1/16" air tube ↔ PU stub at each valve's A port (air side only) | 1 | 3 | — |

### C. Liquid path, nozzle head, shutter

| # | Part | Spec / what to look for | Qty | Budget ~EUR | Upgrade ~EUR |
|---|---|---|---|---|---|
| C1 | FEP tubing, standard | 1/16" OD × 0.5 mm (0.020") ID, ≥ 5 m (4 lines × ~0.8 m + spare) | 1 roll | 15 (generic, 10 m) | VICI TFEP120-25M / Upchurch 1548 (lab-grade) 100 |
| C2 | FEP tubing, viscous | 1/16" OD × 1.0 mm ID, for TEC/DPG-like materials | optional | 0 | JR-T-6806-M10 (10 m) 45 |
| C3 | Nozzle head | Block with 4 bores of 1.65 mm on ~5 mm spacing; tubes protrude 5 mm | 1 | 2 (PETG print) | PTFE block, drilled 15 |
| C4 | Drip shutter | SG90/MG90S servo + 1 mm PP or PTFE sheet offcut as flap | 1 | 6 | — |

### D. Bottle closure: septum in each bottle's own cap

Design, leak-free tube passage and long-term tightness: [feasibility note §3](Perfume-Doser-Feasibility.md)
and [Septum-Leak-Analysis](Septum-Leak-Analysis.md); 3D section with ×4 detail:
`doser-3d/septum_render.png`. No machining beyond two Ø 2 mm holes per cap, no hold-down.

| # | Part | Spec / what to look for | Qty | Budget ~EUR | Upgrade ~EUR |
|---|---|---|---|---|---|
| D1 | PTFE/silicone septa 17.5 mm, 100 pcs | DIN 18 / GL 18 dropper-bottle caps | 1 | 22 | — |
| D2 | PTFE/silicone septa 22 mm, 3 mm, 100 pcs | 24-400 / 24-410 caps (Boston rounds); trim for odd caps | 1 | 28 | — |
| D3 | Open GL 45 cap with PTFE/silicone septum | lab bottles | 1 | 11 | — |
| D4 | Sharp needles 20 G (0.9 mm) | pre-pierce the septum before pushing the 1.6 mm tube | 1 pack | 1 | — |
| D5 | Strain-relief saddles | printed (PETG, see F3), one per cap: clips onto the cap skirt and clamps both tubes, so a pull goes into the cap, not the septum | 4 | 0 | — |
| D6 | Test bottles | only if you don't have them: amber droppers 30/100 mL (+ 100 mL GL 45 lab bottle) | — | 14 | 24 |

Preparing a cap (~3 min): remove the liner; drill **two Ø 2.0 mm holes 5 mm apart** in the
cap top (not one big hole: it would leave silicone open to the air, and vapour permeates
through it); septum into the cap, PTFE face towards the bottle; pre-pierce through both cap
holes with the 20 G needle; push the bevel-cut FEP tubes through (the silicone is the seal,
the PTFE face is only drawn down around the tube as a vapour shield); set the depth (liquid
~3 mm above the bottom, air ~5 mm below the septum); screw the cap onto the bottle; clip the
saddle onto the cap and clamp both tubes; run the seal check. Neat terpene-rich materials
(citrus oils): new septum at every bottle change.

Option A — universal PTFE cone with spring hold-down, for bottles without a usable cap:
parts in the xlsx sheet "Adapter option A" (~EUR 72 for four, plus hold-down posts).

### E. Electronics

| # | Part | Spec / what to look for | Qty | Budget ~EUR | Upgrade ~EUR |
|---|---|---|---|---|---|
| E1 | Microcontroller | ESP32 DevKitC V4 (or any ESP32 dev board with UART2 + I²C); Wi-Fi + Bluetooth LE on the chip | 1 | 10 | ESP32-S3 N8R8 (Wi-Fi and Bluetooth both on all the time) ~15 |
| E2 | MOSFET switch modules | Logic-level (AOD4184/D4184 "MOSFET trigger" modules), switch at 3.3 V, ≥ 2 A; 4 valves + 1 pump | 5 | 7 | — |
| E3 | Schottky diodes | 1N5819: D1-D5 flyback across each valve and the pump, D6 in the ESP32 5 V feed (lets USB and 12 V be connected together) | 6 | 1 | — |
| E4 | Pull-downs / pull-up | 10 kΩ resistors: R3-R7 gate pull-downs (if the modules don't have them) + R8 stop-button pull-up on GPIO 34 | 6 | 0.5 | — |
| E4b | I²C pull-ups | 4.7 kΩ resistors, SDA/SCL to 3.3 V (bare XGZP6847D only) | 2 | 0.1 | — |
| E5 | 12 V supply | 12 V 3 A desktop adapter + DC jack (no mains wiring) | 1 | 14 | Mean Well LRS-50-12 25 |
| E6 | 5 V supply | Buck converter 12 → 5 V, ≥ 2 A (LM2596 module) | 1 | 3 | Pololu D24V22F5 12 |
| E7 | Fuse | Inline fuse holder + 3 A fuse on the 12 V line | 1 | 3 | — |
| E8 | Wiring | Perfboard, screw terminals, JST-XH connectors, Dupont wires, 0.5 mm² wire | 1 set | 15 | — |
| E9 | Stop button | Latching mushroom, twist to release, **2 NC** contacts, 22.3 mm panel hole (Schlegel FRVKPOO); NC1 in the 12 V load line, NC2 to the ESP32 | 1 | 17 | — |

### F. Mechanics

| # | Part | Spec / what to look for | Qty | Budget ~EUR | Upgrade ~EUR |
|---|---|---|---|---|---|
| F1 | 2020 aluminium profile kit | 2 × 400 mm uprights, 2 × 500 mm crossbars (valve rail + nozzle-head rail), 1 × 300 mm nozzle arm, 8 corner brackets, ~30 M5 T-nuts + screws | 1 | 35 | — |
| F2 | Base plate | ~500 × 350 mm, 10-12 mm HDPE or plywood | 1 | 18 | — |
| F3 | 3D-printed parts (PETG) | Bottle locator pockets, cap saddles, nozzle-head holder, valve bracket, sensor bracket, shutter arm, front panel for the stop button (not wetted) | 1 set | 5 (filament) | print service 30 |
| F4 | Small stuff | Cable ties, spiral wrap, slot labels 1-4 on both ends of every line | 1 | 8 | — |

### G. Test materials (go/no-go run)

Already on hand, not in the totals: ethanol, DEP, TEC, DPG (plus gloves, pipettes and a
waste vial). One of the four lines gets a 10 % dilution made from these, as in the test plan.

---

## Totals

| Group (listed prices, from the xlsx) | Budget EUR | Lab-grade EUR |
|---|---|---|
| A Weighing (without the balance) | 31 | 31 |
| B Air supply and valves | 81 | 235 |
| C Liquid path, head, shutter | 38 | 203 |
| D Bottle closure (septum caps) | 75 | 85 |
| E Electronics | 58 | 71 |
| F Mechanics | 58 | 76 |
| **Total** | **≈ 342** | **≈ 702** |

The biggest upgrade jumps are FKM-sealed valves (B6, +~150) and lab-grade FEP (C1,
+~85). Neither is needed to answer the go/no-go question; buy them once the rig works.

## Tools (if not at hand)

Digital caliper · drill stand + HSS bits 1.6 / 2.0 / 2.9 / 3.2 mm · razor or ceramic tube cutter
for square FEP cuts · soldering iron + multimeter · access to a 3D printer (or a print
service) · USB cable for the ESP32.

## Software

- **Firmware:** Arduino-ESP32 core (Arduino IDE or PlatformIO); `HardwareSerial` (UART2)
  for the balance, `Wire` + the sensor's library (Adafruit MPRLS or XGZP6847D example
  code), `ESP32Servo`, LEDC PWM for the pump.
- **Wireless (all in the Arduino-ESP32 core or common libraries):** `WiFi` + `ESPmDNS`
  (`doser.local`), `WiFiProv` (Wi-Fi setup over Bluetooth with Espressif's "ESP BLE
  Provisioning" app), soft-AP fallback hotspot, `ESPAsyncWebServer` + WebSocket for the
  page and live data, `LittleFS` for the page files, `ArduinoJson` for the REST API,
  `ArduinoOTA` for updates over Wi-Fi.
- **Phone / PC:** just a browser. From the Mac, a formula can also be sent with Python
  `requests` (`POST http://doser.local/api/jobs`); the log comes back as CSV.

## Build order

1. Electronics on the bench: ESP32 reads the balance over RS232 and the pressure sensor
   over I²C; switches the valves and the pump; the stop button kills valves and pump.
   Then Wi-Fi setup over Bluetooth and the live page on `doser.local`.
2. Air side: pump → buffer → sensor/relief → manifold → check valves → valves. Leak-test
   at 20 kPa with the valve outlets plugged.
3. Bottle closures: prepare a septum cap per bottle (two Ø 2 mm holes), push the FEP lines
   through, clip the saddle onto the cap, seal-check.
4. Frame, nozzle head over the vial, shutter, draft shield. Check that the tips are above
   the tallest bottle's shoulder.
5. Run the test plan from the feasibility note §11: 30 doses at 50 mg and 500 mg per
   line, septum-cap leak at 20 kPa, weekly idle-mass log per bottle, after-drips per hour.

---

## Sources

- Mini 3/2 valves: [Makeblock 0520E (12 V, 2-position 3-way, >300 mmHg)](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/314/59001_Web.pdf), [FA0520F 12 V](https://zbotic.in/product/fa0520f-12v-dc-2-position-3-way-small-mini-electric-solenoid-valve-for-air-gas/), [0520D NC, 0-350 mmHg](https://sigmanortec.ro/en/miniature-solenoid-valve-air-nc-0520d-6v)
- Pumps: [BODENFLO BD-02A1L (1 bar, 1 L/min)](https://evelta.com/12v-micro-diaphragm-air-pump-for-medical-devices-max-flow-1l-min/), [370 DC air pump](https://aws.robu.in/?p=890172)
- Pressure sensors: [XGZP6847D040KPG at DigiKey](https://www.digikey.lt/en/products/detail/cfsensor/XGZP6847D040KPG/22530787), [Honeywell ABP2 5 psi at RS](https://befr.rs-online.com/web/p/pressure-sensor-ics/2362674)
- Relief / check valves: [Tameson pre-set 0.3 bar brass safety valve](https://tameson.com/products/sfl-b-8-0p3-038-g-3-8-inch-brass-pre-set-safety-valve-0p3-bar-dn-8), [Tameson G 1/8" adjustable 0.5-1 bar](https://tameson.com/products/sfl-b-1-018-m-g-1-8-inch-brass-adjustable-safety-valve-0p5-1-bar-m), [SMC AKH check valve, 4 mm](https://uk.rs-online.com/web/p/pneumatic-non-return-valves/2328617)
- FEP tubing: [VICI TFEP120-25M, 1/16" × 0.5 mm, 25 m](https://www.mz-at.de/en/tfep120-25m-tubing-1-16-od-020-5mm-id-fep-25m-pkg.html), [Upchurch 1/16" × 0.020", 15 m](https://www.analytics-shop.com/gb/up1548l), [FEP 1/16" × 1.0 mm, 10 m](https://www.mz-at.de/en/jr-t-6806-m10-tubing-fep-1-16-x-10-mm-id-10m-pkg.html)
- Stop button: [Schlegel FRVKPOO, 2 NC, at Reichelt](https://www.reichelt.de/de/de/shop/produkt/not-aus-taster_-_2_hygiene-168198)
- RS232 module: [MAX3232 DB9 module (Electrokit)](https://www.electrokit.com/en/rs232-db9-till-ttl-omvandlare-max3232), [Bits&Parts](https://www.bitsandparts.nl/en/converter-serial-ttl-max3232-rs232-db9-p122414)
- Balance: [KERN PCB 350-3 specs and prices](https://www.oconchemicals.ie/products/precision-balance-pcb-kern-model-pcb-sl00pcb350-3.html), [older catalogue price](https://static.mercateo.com/5e/46120173547f4560a0f07fe7c8fbf31a/pdf/pcba02.pdf)
