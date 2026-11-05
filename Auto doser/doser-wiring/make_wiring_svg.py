"""Draws the 4-line doser wiring diagrams: electrical (W-numbers) and pneumatic/liquid (T/L-numbers).

Writes doser_wiring_electrical.svg and doser_tubing.svg next to this script.
Wire and tube numbers match the tables in Doser-4-Line-Wiring.md.
"""
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).parent

COL = {
    "12v": "#d62728", "5v": "#f28e0e", "3v3": "#c2185b", "gnd": "#222222",
    "gpio": "#1f5fbf", "i2c": "#2e8b3a", "uart": "#7b3fb0", "rs232": "#777777",
    "usb": "#777777", "load": "#8c564b",
    "air": "#2a7fbf", "fep_air": "#00a0a0", "liquid": "#c47a00", "exhaust": "#9aa7b0",
}


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.body = w, h, []

    def add(self, s):
        self.body.append(s)

    def text(self, x, y, s, size=13, anchor="start", weight="normal", fill="#222", italic=False):
        style = ' font-style="italic"' if italic else ""
        for i, line in enumerate(s.split("\n")):
            self.add(f'<text x="{x}" y="{y + i * (size + 3)}" font-size="{size}" text-anchor="{anchor}" '
                     f'font-weight="{weight}" fill="{fill}"{style}>{escape(line)}</text>')

    def box(self, x, y, w, h, title, sub=None, fill="#f4f6f8", stroke="#445", dash=False):
        d = ' stroke-dasharray="6 4"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{d}/>')
        self.text(x + w / 2, y + 18, title, 13, "middle", "bold")
        if sub:
            self.text(x + w / 2, y + 34, sub, 11, "middle", fill="#555")

    def pin(self, x, y, label, side):
        """Pin square on a box edge; label inside the box."""
        self.add(f'<rect x="{x - 3}" y="{y - 3}" width="6" height="6" fill="#fff" stroke="#333"/>')
        dx, anchor = {"l": (8, "start"), "r": (-8, "end"), "t": (0, "middle"), "b": (0, "middle")}[side]
        dy = {"l": 4, "r": 4, "t": 16, "b": -8}[side]
        self.text(x + dx, y + dy, label, 11, anchor, fill="#333")

    def wire(self, pts, color, wid=None, at=None, width=2.6, dash=False):
        path = " ".join(f"{x},{y}" for x, y in pts)
        d = ' stroke-dasharray="7 5"' if dash else ""
        self.add(f'<polyline points="{path}" fill="none" stroke="#fff" stroke-width="{width + 4}" stroke-linejoin="round"/>')
        self.add(f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{d}/>')
        if wid:
            if at is None:
                (x1, y1), (x2, y2) = pts[0], pts[1]
                at = ((x1 + x2) / 2, (y1 + y2) / 2)
            self.badge(at[0], at[1], wid, color)

    def badge(self, x, y, s, color):
        w = 7 * len(s) + 8
        self.add(f'<rect x="{x - w / 2}" y="{y - 9}" width="{w}" height="17" rx="8" fill="#fff" stroke="{color}" stroke-width="1.4"/>')
        self.text(x, y + 4, s, 11, "middle", "bold", fill=color)

    def dot(self, x, y, color="#222"):
        self.add(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')

    def tag(self, x, y, s, color, anchor="l"):
        """Bus reference tag; (x, y) is the attachment point, the tag extends away from it."""
        w = 6.6 * len(s) + 12
        x0 = {"l": x - w, "r": x, "c": x - w / 2}[anchor]
        self.add(f'<rect x="{x0}" y="{y - 10}" width="{w}" height="20" rx="3" fill="{color}"/>')
        self.text(x0 + w / 2, y + 4, s, 11, "middle", "bold", fill="#fff")

    def diode(self, x, y1, y2, color="#222", label=None):
        """Vertical diode between y1 (cathode, top) and y2 (anode, bottom)."""
        m = (y1 + y2) / 2
        self.add(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{color}" stroke-width="2"/>')
        self.add(f'<polygon points="{x - 9},{m + 7} {x + 9},{m + 7} {x},{m - 7}" fill="{color}"/>')
        self.add(f'<line x1="{x - 10}" y1="{m - 8}" x2="{x + 10}" y2="{m - 8}" stroke="{color}" stroke-width="3"/>')
        if label:
            self.text(x + 14, m + 4, label, 11, fill="#333")

    def diode_h(self, x1, x2, y, color="#222", label=None):
        """Horizontal diode, anode at x1, cathode at x2."""
        m = (x1 + x2) / 2
        self.add(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="2.6"/>')
        self.add(f'<polygon points="{m - 7},{y - 9} {m - 7},{y + 9} {m + 7},{y}" fill="{color}"/>')
        self.add(f'<line x1="{m + 8}" y1="{y - 10}" x2="{m + 8}" y2="{y + 10}" stroke="{color}" stroke-width="3"/>')
        if label:
            self.text(m, y - 14, label, 11, "middle", fill="#333")

    def resistor(self, x, y1, y2, label=None, color="#222"):
        m = (y1 + y2) / 2
        self.add(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{color}" stroke-width="2"/>')
        self.add(f'<rect x="{x - 6}" y="{m - 13}" width="12" height="26" fill="#fff" stroke="{color}" stroke-width="2"/>')
        if label:
            self.text(x + 10, m + 4, label, 11, fill="#333")

    def save(self, name, title):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" font-family="Helvetica, Arial, sans-serif">'
                f'<title>{escape(title)}</title><rect width="100%" height="100%" fill="#ffffff"/>')
        (HERE / name).write_text(head + "\n".join(self.body) + "</svg>\n")


# ---------------------------------------------------------------- electrical
def electrical():
    s = Svg(1840, 1290)
    s.text(40, 42, "4-line doser — electrical wiring", 24, weight="bold")
    s.text(40, 66, "W-numbers = one physical wire each (table in Doser-4-Line-Wiring.md). Coloured tags = screw terminal "
                   "on a bus strip, e.g. 12V·3 = terminal 3 of the +12 V strip. Pins drawn by function, not board position.",
           13, fill="#555")

    # power entry
    s.box(40, 110, 150, 80, "12 V / 3 A adapter", "plug-in PSU")
    s.pin(190, 135, "+", "r"); s.pin(190, 170, "−", "r")
    s.box(250, 110, 90, 80, "J1", "DC jack")
    s.pin(250, 135, "+", "l"); s.pin(250, 170, "−", "l"); s.pin(340, 135, "+", "r"); s.pin(340, 170, "−", "r")
    s.wire([(190, 135), (250, 135)], COL["12v"], "W01", (220, 120))
    s.wire([(190, 170), (250, 170)], COL["gnd"], "W01", (220, 186))
    s.text(220, 212, "barrel plug 5.5/2.1, centre +", 10, "middle", fill="#777")
    s.wire([(340, 135), (385, 135)], COL["12v"], "W02", (362, 118))
    s.add('<rect x="385" y="125" width="50" height="20" rx="3" fill="#fff" stroke="#222" stroke-width="2"/>'
          '<line x1="385" y1="135" x2="435" y2="135" stroke="#222" stroke-width="1.5"/>')
    s.text(410, 162, "F1 3.15 A T", 11, "middle")
    s.wire([(435, 135), (520, 135)], COL["12v"], "W03", (470, 118))
    s.wire([(340, 170), (370, 170), (370, 215)], COL["gnd"], "W04", (370, 192))
    s.tag(370, 225, "GND·1", COL["gnd"], "c")

    # +12 V strip TB1
    s.add(f'<rect x="500" y="117" width="130" height="36" rx="4" fill="#fdecec" stroke="{COL["12v"]}" stroke-width="2"/>')
    s.text(565, 106, "+12 V bus strip", 12, "middle", "bold", fill=COL["12v"])
    for i in range(3):
        x = 520 + 40 * i
        s.add(f'<circle cx="{x}" cy="135" r="7" fill="#fff" stroke="{COL["12v"]}" stroke-width="2"/>')
        s.text(x + 13, 168, str(i + 1), 11, "middle", "bold", fill=COL["12v"])
    s.text(640, 140, "3 → S1 NC1 (W54)", 11, fill=COL["12v"])

    # stop button S1: NC1 switches the load supply, NC2 tells the ESP32 (GPIO34)
    s.add(f'<rect x="110" y="480" width="180" height="36" rx="4" fill="#fdecec" stroke="{COL["12v"]}" stroke-width="2"/>')
    s.text(110, 456, "+12 V load strip (live only while STOP is released)", 12, weight="bold", fill=COL["12v"])
    for i in range(6):
        x = 125 + 30 * i
        s.add(f'<circle cx="{x}" cy="498" r="7" fill="#fff" stroke="{COL["12v"]}" stroke-width="2"/>')
        s.text(x, 474, str(i + 1), 11, "middle", "bold", fill=COL["12v"])
    s.text(300, 502, "2–6 → M1–M5 VIN+", 11, fill=COL["12v"])
    s.box(110, 560, 180, 120, "S1 STOP button", "latching, 2 × NC")
    s.pin(125, 560, "", "t")
    s.pin(110, 595, "NC1", "l"); s.pin(110, 650, "NC2", "l"); s.pin(290, 635, "NC2", "r")
    s.text(200, 612, "NC1 ↑ to strip 1", 10, "middle", fill="#555")
    s.wire([(125, 560), (125, 498)], COL["12v"], "W55", (125, 535))
    s.wire([(110, 595), (85, 595)], COL["12v"])
    s.tag(85, 595, "12V·3", COL["12v"], "l"); s.badge(55, 573, "W54", COL["12v"])
    s.wire([(110, 650), (85, 650)], COL["gnd"])
    s.tag(85, 650, "GND·18", COL["gnd"], "l"); s.badge(55, 672, "W57", COL["gnd"])
    s.wire([(290, 635), (900, 635)], COL["gpio"], "W56", (380, 635))
    s.resistor(850, 595, 635, None, "#444"); s.dot(850, 635, COL["gpio"])
    s.tag(850, 585, "U1 3V3", COL["3v3"], "c")
    s.text(862, 622, "R8", 10, fill="#333")
    s.text(200, 700, "pressed → valves + pump dead,\nGPIO34 HIGH; ESP32 stays on", 10, "middle", fill="#555")

    # buck U2
    s.box(500, 205, 170, 95, "U2 buck 12→5 V", "LM2596 · set 5.0 V first!")
    s.pin(560, 205, "", "t")
    s.pin(500, 270, "IN−", "l"); s.pin(670, 255, "OUT+", "r"); s.pin(670, 285, "OUT−", "r")
    s.text(560, 262, "IN+", 11, "middle", fill="#333")
    s.wire([(560, 135), (560, 205)], COL["12v"], "W05", (560, 188))
    s.wire([(500, 270), (465, 270), (465, 305)], COL["gnd"], "W06", (465, 287))
    s.tag(465, 315, "GND·2", COL["gnd"], "c")
    s.wire([(670, 285), (690, 285), (690, 315)], COL["gnd"], "W08", (690, 300))
    s.tag(690, 325, "GND·3", COL["gnd"], "c")

    # +5 V strip TB3
    s.add(f'<rect x="705" y="237" width="130" height="36" rx="4" fill="#fff3e3" stroke="{COL["5v"]}" stroke-width="2"/>')
    s.text(770, 229, "+5 V bus strip", 12, "middle", "bold", fill=COL["5v"])
    for i in range(3):
        x = 725 + 45 * i
        s.add(f'<circle cx="{x}" cy="255" r="7" fill="#fff" stroke="{COL["5v"]}" stroke-width="2"/>')
    s.text(738, 289, "1", 11, "middle", "bold", fill=COL["5v"]); s.text(783, 289, "2", 11, "middle", "bold", fill=COL["5v"])
    s.text(815, 289, "3 → servo", 11, "start", "bold", fill=COL["5v"])
    s.wire([(670, 255), (725, 255)], COL["5v"], "W07", (697, 239))

    # ESP32 U1
    ex, ey, ew, eh = 900, 95, 230, 845
    s.box(ex, ey, ew, eh, "U1 ESP32 dev board", "ESP32-WROOM-32(E) · UART2 + I²C", fill="#eef3fb")
    left = {"5V": 320, "GND": 370, "GPIO21 SDA": 470, "3V3": 510, "GPIO22 SCL": 550, "GPIO34 STOP": 635, "GPIO16 RX2": 700, "GPIO17 TX2": 740}
    for name, y in left.items():
        s.pin(ex, y, name, "l")
    rights = [("GPIO25", 150), ("GPIO26", 335), ("GPIO27", 520), ("GPIO33", 705), ("GPIO32 PWM", 890)]
    for name, y in rights:
        s.pin(ex + ew, y, name, "r")
    s.pin(950, ey + eh, "USB", "b"); s.pin(1080, ey + eh, "GPIO13", "b")
    s.text(ex + ew / 2, 800, "Do not use for loads:\nGPIO 0, 2, 12, 15 (strapping)\nGPIO 1, 3, 5, 14 (pulse at boot)\n"
                             "GPIO 6–11 (flash)", 11, "middle", fill="#777")

    # 5 V into U1 through D6 (OR-ing so USB and the buck never fight)
    s.wire([(770, 255), (770, 320), (820, 320)], COL["5v"], "W09", (770, 300))
    s.diode_h(820, 870, 320, COL["5v"], "D6 1N5819")
    s.wire([(870, 320), (ex, 320)], COL["5v"])
    s.wire([(ex, 370), (865, 370), (865, 405)], COL["gnd"], "W10", (865, 388))
    s.tag(865, 415, "GND·4", COL["gnd"], "c")

    # pressure sensor U3 (I²C)
    s.box(470, 410, 200, 185, "U3 pressure sensor", "XGZP6847D040KPG · 0–40 kPa\n2.5–5.5 V · I²C (0x6D?)")
    s.pin(670, 470, "SDA", "r"); s.pin(670, 510, "VDD", "r"); s.pin(670, 550, "SCL", "r"); s.pin(670, 578, "GND", "r")
    s.wire([(670, 470), (ex, 470)], COL["i2c"], "W46", (720, 470))
    s.wire([(670, 510), (ex, 510)], COL["3v3"], "W44", (720, 510))
    s.wire([(670, 550), (ex, 550)], COL["i2c"], "W47", (720, 550))
    s.resistor(790, 470, 510, None, COL["i2c"]); s.dot(790, 470, COL["i2c"]); s.dot(790, 510, COL["3v3"])
    s.resistor(840, 510, 550, None, COL["i2c"]); s.dot(840, 510, COL["3v3"]); s.dot(840, 550, COL["i2c"])
    s.text(815, 440, "R1, R2 4.7 kΩ", 11, "middle", fill="#333")
    s.text(815, 454, "(bare sensor only)", 10, "middle", fill="#777")
    s.wire([(670, 578), (700, 578), (700, 605)], COL["gnd"], "W45", (730, 590))
    s.tag(700, 615, "GND·16", COL["gnd"], "c")

    # MAX3232 U4 + balance
    s.box(470, 650, 200, 155, "U4 MAX3232 module", "RS232 ↔ 3.3 V TTL")
    s.pin(670, 700, "RXD (out)", "r"); s.pin(670, 740, "TXD (in)", "r")
    s.pin(470, 700, "VCC", "l"); s.pin(470, 745, "GND", "l"); s.pin(570, 805, "DB9", "b")
    s.wire([(670, 700), (ex, 700)], COL["uart"], "W51", (720, 700))
    s.wire([(ex, 740), (670, 740)], COL["uart"], "W50", (720, 740))
    s.add(f'<polygon points="{ex - 120},694 {ex - 120},706 {ex - 108},700" fill="{COL["uart"]}"/>')
    s.add(f'<polygon points="{ex - 120},734 {ex - 120},746 {ex - 132},740" fill="{COL["uart"]}"/>')
    s.wire([(470, 700), (440, 700)], COL["3v3"], "W48", (452, 684))
    s.tag(440, 700, "U1 3V3", COL["3v3"], "l")
    s.wire([(470, 745), (440, 745)], COL["gnd"], "W49", (452, 761))
    s.tag(440, 745, "GND·17", COL["gnd"], "l")
    s.box(500, 860, 140, 50, "A3 null-modem", "only if needed", fill="#fff", dash=True)
    s.wire([(570, 805), (570, 860)], COL["rs232"], "W52", (570, 833), width=4)
    s.wire([(570, 910), (570, 940)], COL["rs232"], width=4)
    s.box(450, 940, 240, 90, "Balance (RS232, DB9)", "pin 2 TxD · 3 RxD · 5 GND\nsee its manual: baud, 8N1,\ncontinuous output")

    # loads
    loads = ["V1 3/2 valve NC", "V2 3/2 valve NC", "V3 3/2 valve NC", "V4 3/2 valve NC", "Pump 12 V"]
    mx, mw = 1320, 190
    for k in range(5):
        y = 110 + 185 * k
        trig = y + 40
        name = f"M{k + 1}"
        s.add(f'<rect x="{mx}" y="{y}" width="{mw}" height="130" rx="6" fill="#f4f6f8" stroke="#445" stroke-width="1.6"/>')
        s.text(mx + 10, y + 20, f"{name} MOSFET", 13, weight="bold")
        s.text(mx + mw / 2, y + 124, "D4184 module", 11, "middle", fill="#555")
        s.pin(mx, trig, "TRIG", "l"); s.pin(mx, y + 95, "GND", "l")
        s.pin(mx + 120, y, "VIN+", "t"); s.pin(mx + 165, y, "VIN−", "t")
        s.pin(mx + mw, y + 50, "OUT+", "r"); s.pin(mx + mw, y + 105, "OUT−", "r")
        gpio = rights[k][1]
        s.wire([(ex + ew, gpio), (mx, trig)], COL["gpio"], f"W{31 + k}", (1185, trig))
        s.wire([(mx, y + 95), (1230, y + 95)], COL["gnd"], f"W{36 + k}", (1290, y + 95))
        s.tag(1230, y + 95, f"GND·{10 + k}", COL["gnd"], "l")
        s.resistor(1260, trig, y + 95, None, "#444"); s.dot(1260, trig, COL["gpio"]); s.dot(1260, y + 95, COL["gnd"])
        s.text(1244, y + 72, f"R{3 + k}", 10, "end", fill="#333")
        s.wire([(mx + 120, y), (mx + 120, y - 14)], COL["12v"])
        s.tag(mx + 120, y - 22, f"12VL·{2 + k}", COL["12v"], "c")
        s.badge(mx + 70, y - 22, f"W{11 + k}", COL["12v"])
        s.wire([(mx + 165, y), (mx + 165, y - 14)], COL["gnd"])
        s.tag(mx + 160, y - 22, f"GND·{5 + k}", COL["gnd"], "r")
        s.badge(mx + 232, y - 22, f"W{16 + k}", COL["gnd"])
        lx = 1640
        s.wire([(mx + mw, y + 50), (lx, y + 50)], COL["load"], f"W{21 + k}", (1595, y + 50))
        s.wire([(mx + mw, y + 105), (lx, y + 105)], COL["load"], f"W{26 + k}", (1595, y + 105))
        s.diode(1545, y + 50, y + 105, "#222")
        s.dot(1545, y + 50); s.dot(1545, y + 105)
        s.text(1562, y + 82, f"D{k + 1}", 11, weight="bold")
        s.box(lx, y + 30, 160, 95, loads[k], "+ to OUT+, − to OUT−" if k == 4 else "coil, either lead", fill="#fbf3ef")
        s.text(lx + 80, y + 80, "red / black" if k == 4 else "12 V, ~0.1–0.2 A", 11, "middle", fill="#555")
        s.text(lx + 80, y + 98, "PWM 1–5 kHz" if k == 4 else "off = bottle vented", 11, "middle", fill="#555")
    s.text(1390, 1028, "D1–D5 1N5819 flyback: under the OUT screws, band (cathode) → OUT+\n"
                       "R3–R7 10 kΩ TRIG→GND: fit only if the module has none\n(measure TRIG–GND with power off)\n"
                       "Never plug in USB and 12 V without D6 fitted", 11, fill="#333")

    # USB + servo
    s.wire([(950, ey + eh), (950, 1010)], COL["usb"], "W53", (950, 980), width=4)
    s.box(880, 1010, 140, 66, "Mac (USB)", "flash + host link")
    s.wire([(1080, ey + eh), (1080, 1010)], COL["gpio"], "W43", (1080, 980))
    s.box(1050, 1010, 170, 90, "Servo SG90/MG90S", "drip shutter")
    s.pin(1080, 1010, "", "t")
    s.text(1060, 1092, "orange = signal", 10, fill="#555")
    s.pin(1220, 1040, "red", "r"); s.pin(1220, 1075, "brown", "r")
    s.wire([(1220, 1040), (1290, 1040)], COL["5v"], "W41", (1255, 1040))
    s.tag(1290, 1040, "5V·3", COL["5v"], "r")
    s.wire([(1220, 1075), (1290, 1075)], COL["gnd"], "W42", (1255, 1075))
    s.tag(1290, 1075, "GND·15", COL["gnd"], "r")

    # GND strip TB2
    gy = 1185
    s.add(f'<rect x="40" y="{gy - 18}" width="{18 * 56 + 20}" height="36" rx="4" fill="#ececec" stroke="#222" stroke-width="2"/>')
    s.text(40, gy - 28, "GND bus strip (18 terminals) — the single star point; every GND tag above is a wire to it",
           12, weight="bold")
    gnd_names = ["J1 −", "U2 IN−", "U2 OUT−", "U1 GND", "M1 VIN−", "M2 VIN−", "M3 VIN−", "M4 VIN−", "M5 VIN−",
                 "M1 sig", "M2 sig", "M3 sig", "M4 sig", "M5 sig", "servo", "U3", "U4", "S1 NC2"]
    for i, n in enumerate(gnd_names):
        x = 60 + 56 * i
        s.add(f'<circle cx="{x}" cy="{gy}" r="7" fill="#fff" stroke="#222" stroke-width="2"/>')
        s.text(x, gy + 34, str(i + 1), 11, "middle", "bold")
        s.text(x, gy + 50, n, 10, "middle", fill="#444")

    # legend
    lx, ly = 1110, 1150
    s.text(lx, ly - 4, "Wire colours", 13, weight="bold")
    legend = [("12v", "+12 V, 0.5 mm²"), ("5v", "+5 V"), ("3v3", "+3.3 V from U1"), ("gnd", "GND"),
              ("gpio", "GPIO → MOSFET / servo"), ("i2c", "I²C"), ("uart", "UART2 (3.3 V TTL)"),
              ("rs232", "RS232 / USB cable"), ("load", "12 V switched load")]
    for i, (c, t) in enumerate(legend):
        x = lx + (i // 5) * 260; y = ly + 16 + (i % 5) * 22
        s.add(f'<line x1="{x}" y1="{y}" x2="{x + 34}" y2="{y}" stroke="{COL[c]}" stroke-width="4"/>')
        s.text(x + 42, y + 4, t, 12)
    s.save("doser_wiring_electrical.svg", "Doser electrical wiring")


# ---------------------------------------------------------------- pneumatic + liquid
def check_valve(s, x, y, color):
    """Check valve, flow to the right."""
    s.add(f'<polyline points="{x + 12},{y - 13} {x - 8},{y} {x + 12},{y + 13}" fill="none" stroke="{color}" stroke-width="2.4"/>'
          f'<circle cx="{x + 6}" cy="{y}" r="6" fill="#fff" stroke="{color}" stroke-width="2"/>'
          f'<rect x="{x - 20}" y="{y - 16}" width="40" height="32" fill="none" stroke="#888" stroke-dasharray="3 3"/>')


def tubing():
    s = Svg(1840, 1010)
    s.text(40, 42, "4-line doser — air and liquid tubing", 24, weight="bold")
    s.text(40, 66, "T-numbers = air tube pieces, L-numbers = liquid lines (table in Doser-4-Line-Wiring.md). "
                   "Air never touches liquid; liquid only touches FEP, the PTFE septum face and glass.", 13, fill="#555")
    rows = [170 + 190 * k for k in range(4)]
    mid = 455

    # pump
    s.add(f'<circle cx="110" cy="{mid}" r="34" fill="#fff" stroke="#333" stroke-width="2"/>'
          f'<polygon points="94,{mid + 16} 126,{mid + 16} 110,{mid - 18}" fill="#333"/>')
    s.text(110, mid + 58, "Pump 12 V\n(M5, PWM)", 12, "middle", "bold")
    s.wire([(30, mid), (76, mid)], COL["exhaust"], dash=True)
    s.text(30, mid - 50, "inlet open,\naway from bottles", 10, fill="#666")
    s.wire([(144, mid), (205, mid)], COL["air"], "T01", (172, mid - 20))
    check_valve(s, 225, mid, COL["air"])
    s.text(225, mid + 34, "CV0", 12, "middle", "bold")
    s.wire([(245, mid), (300, mid)], COL["air"], "T02", (272, mid - 20))
    s.add(f'<rect x="300" y="{mid - 60}" width="80" height="130" rx="14" fill="#f2f7fb" stroke="#333" stroke-width="2"/>')
    s.text(340, mid + 20, "Buffer\n0.5 L\nPET", 12, "middle", "bold")
    s.text(340, mid - 86, "2 bulkhead\npush-ins in cap", 10, "middle", fill="#666")
    s.wire([(380, mid), (450, mid)], COL["air"], "T03", (415, mid - 20))
    s.dot(450, mid, COL["air"])
    s.wire([(450, mid), (450, 330)], COL["air"], "T04", (450, 395))
    s.box(395, 270, 110, 60, "PS sensor", "U3 · 3 mm port")
    s.wire([(450, mid), (560, mid)], COL["air"], "T05", (505, mid - 20))
    s.dot(560, mid, COL["air"])
    s.text(450, mid + 28, "TE1", 11, "middle", "bold"); s.text(560, mid + 28, "TE2", 11, "middle", "bold")
    s.wire([(560, mid), (560, 330)], COL["air"], "T06", (560, 395))
    s.box(505, 270, 110, 60, "RV relief", "0.5 bar · vents")
    s.wire([(560, 270), (560, 240)], COL["exhaust"], dash=True)
    s.text(560, 232, "to air", 10, "middle", fill="#666")
    s.wire([(560, mid), (660, mid)], COL["air"], "T07", (610, mid - 20))

    # manifold
    s.add(f'<rect x="660" y="{rows[0] - 20}" width="26" height="{rows[3] - rows[0] + 40}" rx="4" fill="#dde6ee" stroke="#333" stroke-width="2"/>')
    s.text(673, rows[0] - 30, "MF 1→4", 12, "middle", "bold")

    for k, y in enumerate(rows):
        n = k + 1
        s.wire([(686, y), (745, y)], COL["air"], f"T{8 + k:02d}", (715, y - 20))
        check_valve(s, 765, y, COL["air"])
        s.text(765, y + 32, f"CV{n}", 12, "middle", "bold")
        s.wire([(785, y), (860, y)], COL["air"], f"T{12 + k:02d}", (822, y - 20))
        # 3/2 valve
        s.add(f'<rect x="860" y="{y - 30}" width="130" height="60" rx="4" fill="#fff" stroke="#333" stroke-width="2"/>'
              f'<line x1="925" y1="{y - 30}" x2="925" y2="{y + 30}" stroke="#333" stroke-width="1.5"/>')
        s.text(892, y - 8, "on", 10, "middle", fill="#555"); s.text(892, y + 10, "P → A", 12, "middle", "bold")
        s.text(957, y - 8, "off", 10, "middle", fill="#555"); s.text(957, y + 10, "A → R", 12, "middle", "bold")
        s.text(925, y - 38, f"V{n} 3/2 NC (M{n})", 12, "middle", "bold")
        s.text(866, y + 4, "P", 11, fill="#c00", weight="bold")
        s.text(984, y + 4, "A", 11, "end", fill="#c00", weight="bold")
        s.text(925, y + 46, "R", 11, "middle", fill="#c00", weight="bold")
        s.wire([(925, y + 30), (925, y + 70), (1010, y + 70)], COL["exhaust"], f"T{16 + k:02d}", (962, y + 70))
        s.text(1016, y + 74, "30 cm, open end away from balance", 10, fill="#666")
        # A -> sleeve joint -> FEP air tube
        s.wire([(990, y), (1050, y)], COL["air"], f"T{20 + k:02d}", (1020, y - 20))
        s.add(f'<rect x="1050" y="{y - 8}" width="28" height="16" rx="3" fill="#f6c6c6" stroke="#a33"/>')
        s.text(1064, y + 26, f"SJ{n}", 11, "middle", "bold")
        top = y - 60
        s.wire([(1078, y), (1150, y), (1150, top - 30), (1215, top - 30), (1215, top + 18)], COL["fep_air"],
               f"T{24 + k:02d}", (1150, y - 40))
        # bottle with septum cap
        s.add(f'<rect x="1190" y="{top + 10}" width="70" height="120" rx="12" fill="#f3e3c8" stroke="#6b4a1e" stroke-width="2"/>'
              f'<rect x="1196" y="{top - 6}" width="58" height="18" rx="2" fill="#333"/>'
              f'<rect x="1205" y="{top - 9}" width="40" height="5" fill="#d33"/>')
        s.add(f'<rect x="1190" y="{top + 70}" width="70" height="60" rx="10" fill="#e8c27a" opacity="0.8"/>')
        s.text(1225, top + 62, f"B{n}", 14, "middle", "bold", fill="#6b4a1e")
        s.wire([(1240, top + 124), (1240, top - 50), (1290, top - 50)], COL["liquid"], width=2.2)
    s.text(1290, rows[3] + 10, "septum cap: tubes 5 mm apart\nair tip 5 mm below septum\nliquid tip 3 mm above bottom",
           11, fill="#555")

    # liquid lines to the nozzle head (outer verticals for the upper bottles, so nothing crosses)
    hx = [1625, 1605, 1585, 1565]
    hy0 = 770
    for k, y in enumerate(rows):
        ly = y - 110
        s.wire([(1290, ly), (hx[k], ly), (hx[k], hy0 + 52)], COL["liquid"], f"L{k + 1}", (1340, ly), width=2.2)
    s.add(f'<rect x="1545" y="{hy0}" width="100" height="40" rx="4" fill="#e9eef2" fill-opacity="0.85" stroke="#333" stroke-width="2"/>')
    s.text(1535, hy0 + 25, "Nozzle head", 12, "end", "bold")
    s.text(1692, hy0 + 8, "4 bores 1.65 mm,\n5 mm apart; tips\nprotrude 5 mm", 11, fill="#555")
    s.add(f'<line x1="1540" y1="{hy0 + 64}" x2="1610" y2="{hy0 + 58}" stroke="#555" stroke-width="4"/>')
    s.text(1692, hy0 + 66, "shutter flap\n(servo), swings\naway to dose", 11, fill="#555")
    s.add(f'<rect x="1555" y="{hy0 + 80}" width="80" height="70" rx="4" fill="#fff" stroke="#333" stroke-width="2"/>'
          f'<rect x="1520" y="{hy0 + 150}" width="150" height="20" rx="3" fill="#ccc" stroke="#333"/>')
    s.text(1595, hy0 + 120, "vial", 11, "middle")
    s.add(f'<rect x="1515" y="{hy0 + 30}" width="165" height="120" rx="6" fill="none" stroke="#5a8" stroke-dasharray="6 4"/>')
    s.text(1510, hy0 + 140, "draft\nshield", 10, "end", fill="#5a8")
    s.text(1595, hy0 + 190, "Balance (RS232 → U4)", 12, "middle", "bold")
    s.text(1820, 995, "Not to height scale. Real rig: every nozzle tip ABOVE the tallest bottle's shoulder (no siphon).",
           11, "end", fill="#c00")

    # sleeve joint detail
    dx, dy = 40, 820
    s.add(f'<rect x="{dx}" y="{dy - 30}" width="700" height="170" rx="8" fill="#fafafa" stroke="#999"/>')
    s.text(dx + 12, dy - 10, "SJ sleeve joint (air side only): FEP 1/16\" × 1.0 mm  ↔  PU 4 × 2.5 mm", 13, weight="bold")
    s.add(f'<rect x="{dx + 40}" y="{dy + 30}" width="300" height="10" fill="{COL["fep_air"]}"/>'
          f'<rect x="{dx + 250}" y="{dy + 24}" width="140" height="22" rx="3" fill="#f6c6c6" stroke="#a33"/>'
          f'<rect x="{dx + 330}" y="{dy + 16}" width="260" height="38" rx="4" fill="none" stroke="{COL["air"]}" stroke-width="3"/>'
          f'<rect x="{dx + 590}" y="{dy + 22}" width="40" height="26" fill="#bbb" stroke="#333"/>')
    s.text(dx + 120, dy + 66, "FEP 1.6 mm OD", 11, "middle")
    s.text(dx + 300, dy + 82, "silicone 1 × 3 mm, 20 mm:\n10 mm over the FEP,\n10 mm pushed into the PU", 11, "middle")
    s.text(dx + 480, dy + 76, "PU 4 × 2.5 mm stub (T20–T23)\ncable tie over the overlap", 11, "middle")
    s.text(dx + 640, dy + 66, "valve A\nbarb 3 mm", 11, "middle")
    s.text(dx + 12, dy + 128, "Mount SJ on the valve rail, ≥ 30 cm from the bottle: silicone only sees diluted headspace air.",
           11, fill="#555")

    # legend
    lx, ly = 800, 840
    s.text(lx, ly - 4, "Tube types", 13, weight="bold")
    legend = [("air", "PU 4 × 2.5 mm, push-in / 3 mm barbs"), ("fep_air", "FEP 1/16\" × 1.0 mm (air, through septum)"),
              ("liquid", "FEP 1/16\" × 0.5 mm (liquid, one piece)"), ("exhaust", "vent / open end")]
    for i, (c, t) in enumerate(legend):
        y = ly + 18 + i * 24
        s.add(f'<line x1="{lx}" y1="{y}" x2="{lx + 34}" y2="{y}" stroke="{COL[c]}" stroke-width="4"/>')
        s.text(lx + 42, y + 4, t, 12)
    s.text(lx + 330, ly + 22, "CV = check valve (flow →), cracking ≤ 2 kPa\nTE = push-in tee, MF = 1→4 distributor\n"
                              "V = 3/2 NC valve: P supply, A bottle, R exhaust\n(unpowered: A↔R, so the bottle vents)",
           12, fill="#333")
    s.save("doser_tubing.svg", "Doser air and liquid tubing")


if __name__ == "__main__":
    electrical()
    tubing()
