#!/usr/bin/env python3
"""Concentration, flow and threshold maths for the dynamic dilution olfactometer.

Standard library only; runs on the system Python 3.9.

Subcommands
    conc      source and delivered concentration for a syringe-pump rig
    perm      same, for a permeation-tube source
    flow      reduce soap-film flowmeter readings to reference conditions
    series    generate a coded, randomised ascending triad series
    bet       best estimate thresholds from a response log
"""

import argparse
import csv
import math
import random
import sys

MOLAR_VOLUME_25C = 24.45  # L/mol at 25 C, 101.325 kPa


def ppb_from_mass(c_mg_m3, mw):
    """mg/m3 -> ppb (nmol/mol) at 25 C, 1 atm."""
    return c_mg_m3 * (MOLAR_VOLUME_25C * 1000.0) / mw


def mass_from_ppb(ppb, mw):
    """ppb -> mg/m3 at 25 C, 1 atm."""
    return ppb * mw / (MOLAR_VOLUME_25C * 1000.0)


def stage_ratio(q_sample, q_dilution):
    if q_sample <= 0:
        raise ValueError("sample flow must be positive")
    return (q_sample + q_dilution) / q_sample


def cascade(ratios):
    total = 1.0
    for r in ratios:
        total *= r
    return total


def soap_film(volume_ml, seconds, t_meas_c, p_meas_kpa,
              t_ref_c=25.0, p_ref_kpa=101.325):
    """Soap-film reading -> L/min at reference conditions."""
    q = (volume_ml / 1000.0) / (seconds / 60.0)
    return q * (p_meas_kpa / p_ref_kpa) * ((t_ref_c + 273.15) / (t_meas_c + 273.15))


def cmd_conc(a):
    # ug/uL * uL/min / (L/min) -> ug/L == mg/m3
    c0 = a.solution * a.syringe / a.carrier
    ratios = []
    if a.stage1:
        ratios.append(stage_ratio(*a.stage1))
    if a.stage2:
        ratios.append(stage_ratio(*a.stage2))
    z = cascade(ratios) if ratios else 1.0
    c = c0 / z

    print("source concentration   %12.4g mg/m3" % c0)
    for i, r in enumerate(ratios, 1):
        print("stage %d ratio          %12.2f :1" % (i, r))
    print("total dilution         %12.4g :1" % z)
    print("delivered              %12.4g mg/m3  = %.4g ug/m3" % (c, c * 1000.0))
    if a.mw:
        print("                       %12.4g ppb" % ppb_from_mass(c, a.mw))
    if a.threshold:
        print("odour units            %12.4g ou/m3" % (c * 1000.0 / a.threshold))
    _sanity(a.mw)


def cmd_perm(a):
    # ng/min / (L/min) -> ng/L == ug/m3
    c0_ug_m3 = a.rate / a.carrier
    ratios = []
    if a.stage1:
        ratios.append(stage_ratio(*a.stage1))
    if a.stage2:
        ratios.append(stage_ratio(*a.stage2))
    z = cascade(ratios) if ratios else 1.0
    c = c0_ug_m3 / z

    print("emission rate          %12.4g ng/min" % a.rate)
    print("source concentration   %12.4g ug/m3" % c0_ug_m3)
    print("total dilution         %12.4g :1" % z)
    print("delivered              %12.4g ug/m3" % c)
    if a.mw:
        print("                       %12.4g ppb" % ppb_from_mass(c / 1000.0, a.mw))
    if a.drift:
        f = a.drift * a.dt / 100.0
        print("temperature band       %12.4g to %.4g ug/m3  (+/- %.2f C)"
              % (c * (1 - f), c * (1 + f), a.dt))
    _sanity(a.mw)


def _sanity(mw):
    if mw:
        return
    print("\nself-test: EROM should be 123 ug/m3 n-butanol = 40 ppb")
    print("           %.1f ug/m3 -> %.3f ppb"
          % (123.0, ppb_from_mass(0.123, 74.12)))


def cmd_flow(a):
    q = soap_film(a.volume, a.seconds, a.temp, a.pressure)
    print("%.4f L/min at 25 C, 101.325 kPa" % q)
    if a.nominal:
        err = 100.0 * (q - a.nominal) / a.nominal
        print("nominal %.4f L/min, error %+.1f %%" % (a.nominal, err))


def cmd_series(a):
    rnd = random.Random(a.seed)
    steps = [a.top / (a.factor ** i) for i in range(a.steps)]
    steps.reverse()  # ascending: weakest first
    w = csv.writer(sys.stdout)
    w.writerow(["order", "nominal_mg_m3", "code_A", "code_B", "code_C", "spiked"])
    used = set()

    def code():
        while True:
            c = "%03d" % rnd.randint(100, 999)
            if c not in used:
                used.add(c)
                return c

    order = 0
    for i, conc in enumerate(steps):
        for _ in range(a.replicates):
            order += 1
            codes = [code(), code(), code()]
            spiked = rnd.choice("ABC")
            w.writerow([order, "%.5g" % conc] + codes + [spiked])
        if a.blanks and (i + 1) % a.blanks == 0:
            order += 1
            codes = [code(), code(), code()]
            w.writerow([order, "0", codes[0], codes[1], codes[2], "NONE"])


def cmd_bet(a):
    """Response log: panelist,nominal_mg_m3,correct(1/0). Ascending order assumed."""
    by_person = {}
    with open(a.log) as fh:
        for row in csv.DictReader(fh):
            p = row["panelist"].strip()
            c = float(row["nominal_mg_m3"])
            ok = int(row["correct"])
            if not math.isfinite(c) or c < 0 or ok not in (0, 1):
                raise ValueError("Response log requires nonnegative finite concentrations and binary correctness")
            by_person.setdefault(p, []).append((c, ok))

    logs = []
    print("%-12s %14s %14s" % ("panelist", "BET mg/m3", "log10"))
    for p in sorted(by_person):
        pts = sorted((c, ok) for c, ok in by_person[p] if c > 0)
        if not pts:
            print("%-12s %14s %14s" % (p, "blanks only", "-"))
            continue
        first_hit = None
        for i, (c, ok) in enumerate(pts):
            if ok and all(o for _, o in pts[i:]):
                first_hit = i
                break
        if first_hit is None:
            print("%-12s %14s %14s" % (p, "> %.5g" % pts[-1][0], "right-censored"))
            continue
        if first_hit == 0:
            print("%-12s %14s %14s" % (p, "< %.5g" % pts[0][0], "left-censored"))
            continue
        else:
            if pts[first_hit - 1][0] == pts[first_hit][0]:
                print("%-12s %14s %14s" % (p, "mixed repeats", "fit raw trials"))
                continue
            bet = math.sqrt(pts[first_hit - 1][0] * pts[first_hit][0])
        logs.append(math.log10(bet))
        print("%-12s %14.5g %14.3f" % (p, bet, math.log10(bet)))

    if logs:
        gm = 10 ** (sum(logs) / len(logs))
        if len(logs) > 1:
            mean = sum(logs) / len(logs)
            var = sum((x - mean) ** 2 for x in logs) / (len(logs) - 1)
            sd = math.sqrt(var)
        else:
            sd = 0.0
        print("\ngeometric mean of interior BET estimates only   %.5g mg/m3" % gm)
        print("BET values are derived midpoints; preserve bracket bounds and raw responses for modelling.")
        print("antilog sd             %.2f   (EN 13725 wants <= 2.3)" % (10 ** sd))


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("conc", help="syringe-pump source")
    c.add_argument("--solution", type=float, required=True, help="ug per uL")
    c.add_argument("--syringe", type=float, required=True, help="uL per min")
    c.add_argument("--carrier", type=float, required=True, help="L per min")
    c.add_argument("--stage1", type=float, nargs=2, metavar=("QSAMP", "QDIL"))
    c.add_argument("--stage2", type=float, nargs=2, metavar=("QSAMP", "QDIL"))
    c.add_argument("--mw", type=float, help="g/mol, for ppb")
    c.add_argument("--threshold", type=float, help="ug/m3, for odour units")
    c.set_defaults(func=cmd_conc)

    m = sub.add_parser("perm", help="permeation-tube source")
    m.add_argument("--rate", type=float, required=True, help="ng per min")
    m.add_argument("--carrier", type=float, required=True, help="L per min")
    m.add_argument("--stage1", type=float, nargs=2, metavar=("QSAMP", "QDIL"))
    m.add_argument("--stage2", type=float, nargs=2, metavar=("QSAMP", "QDIL"))
    m.add_argument("--mw", type=float)
    m.add_argument("--drift", type=float, help="percent per degree C, e.g. 4")
    m.add_argument("--dt", type=float, default=0.2, help="block temp uncertainty, C")
    m.set_defaults(func=cmd_perm)

    f = sub.add_parser("flow", help="soap-film reduction")
    f.add_argument("--volume", type=float, required=True, help="mL")
    f.add_argument("--seconds", type=float, required=True)
    f.add_argument("--temp", type=float, default=22.0, help="deg C")
    f.add_argument("--pressure", type=float, default=101.325, help="kPa")
    f.add_argument("--nominal", type=float, help="meter reading, L/min")
    f.set_defaults(func=cmd_flow)

    s = sub.add_parser("series", help="coded randomised triad series")
    s.add_argument("--top", type=float, required=True, help="highest mg/m3")
    s.add_argument("--factor", type=float, default=2.0)
    s.add_argument("--steps", type=int, default=10)
    s.add_argument("--replicates", type=int, default=1)
    s.add_argument("--blanks", type=int, default=3, help="blank triad every N steps")
    s.add_argument("--seed", type=int, default=None)
    s.set_defaults(func=cmd_series)

    b = sub.add_parser("bet", help="best estimate thresholds")
    b.add_argument("log", help="csv: panelist,nominal_mg_m3,correct")
    b.add_argument("--factor", type=float, default=2.0)
    b.set_defaults(func=cmd_bet)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
