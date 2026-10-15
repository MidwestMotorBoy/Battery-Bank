"""One-shot migration (rev A7): U301 STM32WB1MMC -> TI CC2340R5MODA, board NTCs -> TMP1075 I2C sensors,
IRQ1 / IRQ2 / GAUGE_BTP wire-ORed onto one open-drain net IRQ_N.

Plan: docs/devboard/cc2340-pin-budget.md. Sources: datasheets/cc2340r5moda.pdf (SWRS349A table 6-1, fig. 9-1),
datasheets/tmp1075.pdf (SBOS854F tables 5-1, 7-2), datasheets/tps62177.pdf (SLEEP pull-down).

Edits mcu.kicad_sch, gauge.kicad_sch and MonolithDev.kicad_sch in place. Run once from DevBoard/:
    python tools/mcu_cc2340.py
then tools/junctions.py mcu.kicad_sch, tools/place_fields.py mcu.kicad_sch, ERC.
"""
import math
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import sch_geom as G  # noqa: E402

STOCK = r"C:/Program Files/KiCad/10.0/share/kicad/symbols/"
TI = "https://www.ti.com/lit/ds/symlink/"


def U():
    return str(uuid.uuid4())


def g(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def block_end(s, start):
    """Index just past the S-expression that opens at s[start] == '('."""
    d = 0
    k = start
    n = len(s)
    while k < n:
        c = s[k]
        if c == '"':
            k += 1
            while s[k] != '"':
                k += 2 if s[k] == "\\" else 1
        elif c == "(":
            d += 1
        elif c == ")":
            d -= 1
            if d == 0:
                return k + 1
        k += 1
    raise ValueError("unbalanced")


def top_blocks(s, head):
    """(start, end) of top-level '\\n\\t(head' blocks; start points at the newline."""
    out = []
    pat = "\n\t(" + head
    i = s.find(pat)
    while i >= 0:
        e = block_end(s, i + 2)
        out.append((i, e))
        i = s.find(pat, e)
    return out


def sym_spans(s):
    out = {}
    for a, b in top_blocks(s, "symbol\n"):
        m = re.search(r'\(property "Reference" "([^"]+)"', s[a:b])
        out[m.group(1)] = (a, b)
    return out


def remove_spans(s, spans):
    for a, b in sorted(set(spans), reverse=True):
        s = s[:a] + s[b:]
    return s


def insert_before_sheet_instances(s, text):
    k = s.rindex("\n\t(sheet_instances")
    return s[:k] + text + s[k:]


# ------------------------------------------------------------------ item builders
def wire(x0, y0, x1, y1):
    return (f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {g(x0)} {g(y0)}) (xy {g(x1)} {g(y1)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n'
            f'\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')


def label(name, x, y, ang=0):
    just = "left bottom" if ang in (0, 90) else "right bottom"
    return (f'\n\t(label "{name}"\n\t\t(at {g(x)} {g(y)} {ang})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n\t)')


def glabel(name, x, y, ang=0, shape="bidirectional"):
    just = "left" if ang in (0, 90) else "right"
    return (f'\n\t(global_label "{name}"\n\t\t(shape {shape})\n\t\t(at {g(x)} {g(y)} {ang})\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n'
            f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n\t\t\t(at {g(x)} {g(y)} 0)\n\t\t\t(hide yes)\n'
            f'\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n'
            f'\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')


def junction(x, y):
    return f'\n\t(junction\n\t\t(at {g(x)} {g(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)'


def no_connect(x, y):
    return f'\n\t(no_connect\n\t\t(at {g(x)} {g(y)})\n\t\t(uuid "{U()}")\n\t)'


def text(t, x, y, size=1.27, bold=False):
    t = t.replace("\n", "\\n")
    b = "\n\t\t\t\t(bold yes)" if bold else ""
    return (f'\n\t(text "{t}"\n\t\t(exclude_from_sim no)\n\t\t(at {g(x)} {g(y)} 0)\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size {g(size)} {g(size)}){b}\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')


def prop(name, val, x, y, hide):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return (f'\n\t\t(property "{name}" "{val}"\n\t\t\t(at {g(x)} {g(y)} 0){h}\n\t\t\t(show_name no)\n'
            f'\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)')


def new_symbol(lib_id, ref, value, x, y, pins, path, props, rot=0, dnp=False):
    body = (f'\n\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {g(x)} {g(y)} {rot})\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            f'\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            f'\t\t(dnp {"yes" if dnp else "no"})\n\t\t(uuid "{U()}")')
    body += prop("Reference", ref, x, y - 3, False) + prop("Value", value, x, y + 3, False)
    for k, v in props:
        body += prop(k, v, x, y, True)
    for p in pins:
        body += f'\n\t\t(pin "{p}"\n\t\t\t(uuid "{U()}")\n\t\t)'
    body += (f'\n\t\t(instances\n\t\t\t(project "MonolithDev"\n\t\t\t\t(path "{path}"\n\t\t\t\t\t(reference "{ref}")\n'
             f'\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
    return body


def set_prop(blk, name, val):
    new, n = re.subn(r'(\(property "' + re.escape(name) + r'" )"[^"]*"', lambda m: m.group(1) + '"' + val + '"', blk, count=1)
    assert n == 1, (name, blk[:200])
    return new


def clone(s, spans, tref, nref, x, y, rot=0, value=None, props=(), dnp=None):
    """Copy symbol tref to a new ref at (x, y, rot). Fields move with the body (place_fields tidies them later)."""
    a, b = spans[tref]
    blk = s[a:b]
    at = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+) (\d+)\)", blk)
    ox, oy = float(at.group(1)), float(at.group(2))

    def shift(m):
        return f"(at {g(float(m.group(1)) - ox + x)} {g(float(m.group(2)) - oy + y)} {m.group(3)})"
    blk = re.sub(r"\(at ([-\d.]+) ([-\d.]+) (\d+)\)", shift, blk)            # body and every field
    at = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+) (\d+)\)", blk)
    blk = blk[:at.start()] + f"\n\t\t(at {g(x)} {g(y)} {rot})" + blk[at.end():]
    blk = re.sub(r'\(uuid "[^"]+"\)', lambda m: f'(uuid "{U()}")', blk)
    blk = set_prop(blk, "Reference", nref)
    blk = re.sub(r'\(reference "[^"]+"\)', f'(reference "{nref}")', blk)
    if value is not None:
        blk = set_prop(blk, "Value", value)
    for k, v in props:
        blk = set_prop(blk, k, v)
    if dnp is not None:
        blk = re.sub(r"\(dnp (yes|no)\)", f"(dnp {'yes' if dnp else 'no'})", blk, count=1)
    return blk


def lib_block(text_, name):
    i = text_.index(f'(symbol "{name}"')
    return text_[i:block_end(text_, i)]


def lib_pins(blk):
    """{number: (x, y)} in library coordinates (y up)."""
    out = {}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) [-\d.]+\).*?\(number "([^"]+)"', blk, re.S):
        out[m.group(3)] = (float(m.group(1)), float(m.group(2)))
    return out


def pin_at(libpins, num, x, y, rot=0):
    px, py = libpins[num]
    sx, sy = G.xform(px, py, x, y, rot, None)
    return round(sx, 2), round(sy, 2)


# ================================================================== mcu.kicad_sch
P = os.path.join(ROOT, "mcu.kicad_sch")
s = open(P, encoding="utf-8").read()
spans = sym_spans(s)
PATH = re.search(r'\(path "(/[^"]+)"\s*\(reference "C302"\)', s).group(1)

# ---- library symbols: CC2340R5MODA in, TMP1075DSG in, STM32WB1MMC and the NTC out
mono = open(os.path.join(ROOT, "MonolithDev.kicad_sym"), encoding="utf-8").read()
cc = lib_block(mono, "CC2340R5MODA")
CC_PINS = lib_pins(cc)
cc = cc.replace('(symbol "CC2340R5MODA"', '(symbol "MonolithDev:CC2340R5MODA"', 1)
tmp = lib_block(open(STOCK + "Sensor_Temperature.kicad_sym", encoding="utf-8").read(), "TMP1075DSG")
TMP_PINS = lib_pins(tmp)
tmp = tmp.replace('(symbol "TMP1075DSG"', '(symbol "Sensor_Temperature:TMP1075DSG"', 1)
la = s.index("\n\t(lib_symbols")
lb = block_end(s, la + 2)
libsec = s[la:lb]
for name in ("MonolithDev:STM32WB1MMC", "Device:Thermistor_NTC"):
    i = libsec.index(f'\n\t\t(symbol "{name}"')
    libsec = libsec[:i] + libsec[block_end(libsec, i + 3):]
k = libsec.rindex(")")
libsec = libsec[:k] + "\t" + cc + "\n\t" + tmp + "\n\t" + libsec[k:]
s = s[:la] + libsec + s[lb:]

# Library pin geometry for the parts placed below
devlib = open(STOCK + "Device.kicad_sym", encoding="utf-8").read()
R_PINS = lib_pins(lib_block(devlib, "R"))
C_PINS = lib_pins(lib_block(devlib, "C"))

# ---- new symbols are built from templates before anything is deleted
spans = sym_spans(s)
add = []
pwr_n = [max(int(m) for m in re.findall(r'\(property "Reference" "#PWR(\d+)"', s)) + 1]


def pwr(kind, x, y, rot=0):
    ref = f"#PWR{pwr_n[0]}"
    pwr_n[0] += 1
    add.append(clone(s, spans, "#PWR302" if kind == "GND" else "#PWR301", ref, x, y, rot))


# U301: CC2340R5MODA. Left pins end at x 173.99, right pins at x 207.01 (lib +-16.51).
UX, UY = 190.5, 139.7
add.append(new_symbol("MonolithDev:CC2340R5MODA", "U301", "CC2340R5MODA", UX, UY, [str(n) for n in range(1, 25)], PATH,
                      [("Footprint", "MonolithDev:TI_MHA0024A_CC2340R5MODA_7x10mm"), ("Datasheet", TI + "cc2340r5moda.pdf"),
                       ("Description", "CC2340R5 Bluetooth LE module, Cortex-M0+, 512 kB flash, integrated antenna"),
                       ("LCSC", ""), ("MPN", "CC2340R5MODAN0MHAR")]))


def upin(n):
    return pin_at(CC_PINS, str(n), UX, UY)


assert upin(6) == (173.99, 124.46) and upin(9) == (207.01, 124.46) and upin(21) == (207.01, 154.94), (upin(6), upin(9), upin(21))
right = [(9, "SCL", True), (10, "SDA", True), (16, "UART_TX", False), (17, "UART_RX", False), (11, "CHG_INH", True),
         (18, "LED_DRV", False), (12, "EN_5V1", True), (13, "EN_5V2", True), (15, "3V3_SLEEP", True), (21, "IRQ_N", True)]
for n, net, glob in right:
    x, y = upin(n)
    add.append(wire(x, y, x + 5.08, y))
    add.append(glabel(net, x + 5.08, y) if glob else label(net, x + 5.08, y))
for n, net in ((6, "3V3_MCU"), (14, "NRST"), (3, "ANT_IN"), (4, "RFIO")):
    x, y = upin(n)
    add.append(label(net, x, y, 180))
# SWD straight to J301 (pin 2 SWDIO at 163.83/139.7, pin 4 SWCLK at 163.83/142.24)
x, y = upin(20)
add += [wire(163.83, 139.7, 170.18, 139.7), wire(170.18, 139.7, 170.18, y), wire(170.18, y, x, y)]
x, y = upin(19)
add += [wire(163.83, 142.24, 167.64, 142.24), wire(167.64, 142.24, 167.64, y), wire(167.64, y, x, y)]
x, y = upin(1)
add += [wire(x, y, x - 2.54, y), wire(x - 2.54, y, x - 2.54, y + 2.54)]
pwr("GND", x - 2.54, y + 2.54)
add += [no_connect(163.83, 144.78), no_connect(163.83, 147.32), label("NRST", 163.83, 149.86, 0)]

# RSTN: 100k pull-up R302 + C304 (fig. 9-1 R1 / C92). C304 stays at 144.78-152.4 / 124.46.
add.append(clone(s, spans, "R314", "R302", 152.4, 120.65))
assert pin_at(R_PINS, "1", 152.4, 120.65) == (152.4, 116.84)
add += [label("3V3_MCU", 152.4, 116.84, 0), label("NRST", 152.4, 124.46, 0)]

# RF: RFIO - C313 (CA1 15 pF) - R321 (Z61 0R) - ANT_IN, shunts C314 (Z60, DNP) and C315 (Z62 1 pF). Fig. 9-1.
RY = 106.68
add.append(clone(s, spans, "C302", "C313", 180.34, RY, 90, "15p C0G", [("LCSC", ""), ("MPN", "GRM1555C1H150JA01D")]))
assert pin_at(C_PINS, "1", 180.34, RY, 90) == (176.53, RY), pin_at(C_PINS, "1", 180.34, RY, 90)
add.append(clone(s, spans, "R301", "R321", 187.96, RY, 90, props=[("Footprint", "Resistor_SMD:R_0402_1005Metric"), ("LCSC", ""), ("MPN", "0402WGF0000TCE")]))
add.append(clone(s, spans, "C302", "C314", 184.15, RY + 3.81, 0, "TBD", [("LCSC", ""), ("MPN", "")], dnp=True))
add.append(clone(s, spans, "C302", "C315", 191.77, RY + 3.81, 0, "1p C0G", [("LCSC", ""), ("MPN", "GRM1555C1H1R0BA01D")]))
pwr("GND", 184.15, RY + 7.62)
pwr("GND", 191.77, RY + 7.62)
add += [label("RFIO", 176.53, RY, 180), wire(191.77, RY, 196.85, RY), label("ANT_IN", 196.85, RY, 0)]

# ---- TMP1075 sensors (U302-U306) with bypass caps C308-C312 (refs reused from the NTC filter caps)
SENS = [  # ref, cap, x, y, (A2, A1, A0), dnp, note
    ("U302", "C308", 60.96, 200.66, (0, 0, 0), False, "0x48: port 1 stage (TH301)"),
    ("U303", "C309", 101.6, 200.66, (0, 0, 1), False, "0x49: port 2 stage (TH302)"),
    ("U304", "C310", 142.24, 200.66, (0, 1, 0), False, "0x4A: USB-C connectors (TH303)"),
    ("U305", "C311", 124.46, 241.3, (0, 1, 1), True, "0x4B: DNP, heatsink (TH304)"),
    ("U306", "C312", 165.1, 241.3, (1, 0, 0), True, "0x4C: DNP, prot. FETs (TH305)"),
]
for ref, cref, x, y, (a2, a1, a0), dnp, note in SENS:
    add.append(new_symbol("Sensor_Temperature:TMP1075DSG", ref, "TMP1075", x, y, [str(n) for n in range(1, 10)], PATH,
                          [("Footprint", "MonolithDev:TI_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm_Vias0.3mm"),
                           ("Datasheet", TI + "tmp1075.pdf"),
                           ("Description", "I2C temperature sensor, +-1 C, open-drain ALERT"),
                           ("LCSC", ""), ("MPN", "TMP1075DSGR")], dnp=dnp))
    tp = {n: pin_at(TMP_PINS, n, x, y) for n in TMP_PINS}
    assert tp["8"] == (x, round(y - 7.62, 2)) and tp["1"] == (round(x + 10.16, 2), round(y - 2.54, 2)), tp
    vx, vy = tp["8"]
    add += [wire(vx, vy, vx, vy - 2.54)]
    pwr("3V3", vx, vy - 2.54)
    add.append(clone(s, spans, "C302", cref, vx + 3.81, vy - 2.54, 90, dnp=dnp))
    pwr("GND", vx + 7.62, vy - 2.54)
    gx, gy = tp["4"]
    ex, ey = tp["9"]
    add += [wire(gx, gy, gx, gy + 2.54), wire(ex, ey, ex, ey + 2.54), wire(ex, ey + 2.54, gx, gy + 2.54)]
    pwr("GND", gx, gy + 2.54)
    for pin, lvl in (("7", a0), ("6", a1), ("5", a2)):
        px, py = tp[pin]
        pwr("3V3" if lvl else "GND", px, py, 90 if lvl else 270)
    add += [glabel("SDA", *tp["1"]), glabel("SCL", *tp["2"]), glabel("IRQ_N", *tp["3"])]
    add.append(text(note, x - 10.16, y + 15.24, 1.0))

# ---- deletions
DEL_REFS = ["U301", "R302", "R303", "TP306", "TH301", "TH302", "TH303", "TH304", "TH305", "R308", "R309", "R310",
            "R311", "R320", "C308", "C309", "C310", "C311", "C312", "R316", "TP305",
            "#PWR306", "#PWR307", "#PWR308", "#PWR309", "#PWR310", "#PWR311", "#PWR312", "#PWR313", "#PWR314",
            "#PWR315", "#PWR327", "#PWR328"]
dels = [spans[r] for r in DEL_REFS]

MCU_BOX = (152.0, 104.0, 240.0, 178.0)
NTC_BOX = (40.0, 178.0, 175.0, 218.0)


def inbox(x, y, b):
    return b[0] <= x <= b[2] and b[1] <= y <= b[3]


def pts_of(blk):
    return [(float(a), float(b)) for a, b in re.findall(r"\(xy ([-\d.]+) ([-\d.]+)\)", blk)]


for a, b in top_blocks(s, "wire"):
    p = pts_of(s[a:b])
    if any(inbox(x, y, MCU_BOX) or inbox(x, y, NTC_BOX) for x, y in p):
        dels.append((a, b))
    elif p == [(160.02, 101.6), (171.45, 101.6)]:          # old 3V3_MCU run to U301's VDD pins
        dels.append((a, b))
for head in ("label", "global_label", "junction", "no_connect"):
    for a, b in top_blocks(s, head):
        m = re.search(r"\(at ([-\d.]+) ([-\d.]+)", s[a:b])
        x, y = float(m.group(1)), float(m.group(2))
        name = re.match(r'\n\t\(\w+ "([^"]*)"', s[a:b])
        name = name.group(1) if name else ""
        if inbox(x, y, MCU_BOX) or inbox(x, y, NTC_BOX):
            dels.append((a, b))
        elif head == "junction" and (x, y) == (160.02, 101.6):
            dels.append((a, b))
        elif name in ("NTC_EN", "J303_NTC_EN", "NTC_TH5"):        # R316 ends and J303 pins 2/3
            dels.append((a, b))
            if x > 280:
                add.append(no_connect(x, y) if name == "J303_NTC_EN" else glabel("IRQ_N", x, y, 180))
        elif name == "IRQ2" and abs(x - 287.02) < 0.01:          # TP305's label
            dels.append((a, b))
# wires that only fed R316
r316 = spans["R316"]
for a, b in top_blocks(s, "wire"):
    p = pts_of(s[a:b])
    if any(abs(y - 39.37) < 0.01 or abs(y - 40.64) < 0.01 for x, y in p) and all(100 < x < 140 for x, y in p):
        dels.append((a, b))

s = remove_spans(s, dels)
s = insert_before_sheet_instances(s, "".join(add))

# ---- renames and part changes
s = s.replace('(global_label "IRQ1"', '(global_label "IRQ_N"').replace('(global_label "IRQ2"', '(global_label "IRQ_N"')
spans = sym_spans(s)
for ref, fn in (("R315", lambda b: re.sub(r"\(dnp no\)", "(dnp yes)", b, count=1)),
                ("R313", lambda b: set_prop(set_prop(set_prop(re.sub(r"\(dnp yes\)", "(dnp no)", b, count=1),
                                                              "Value", "470k"), "LCSC", ""), "MPN", "")),
                ("TP304", lambda b: set_prop(b, "Value", "IRQ_N"))):
    a, b = spans[ref]
    s = s[:a] + fn(s[a:b]) + s[b:]

# ---- texts
s = s.replace("BLUETOOTH MCU  STM32WB1MMC  (per ST DS14096 fig. 5)", "BLUETOOTH MCU  CC2340R5MODA  (per TI SWRS349A fig. 9-1)")
s = s.replace("BOARD NTCs  (TH1-TH4, divider powered only while sampling)",
              "BOARD TEMPERATURE  (TMP1075 on I2C, 0x48-0x4C; ALERT wire-ORed onto IRQ_N)")
NOTES = """NOTES
1. U301 antenna end at a board edge, ground 10-20 mm each side; keep-out in the footprint (fig. 9-2).
2. C301-C303 at the VDDS pads. R302 + C304 = power-on reset (SWRS349A fig. 9-1 R1/C92).
3. C313 = CA1. R321/C314/C315 = Z61/Z60/Z62 pi match (TI: 0R, DNP, 1 pF); retune on the board.
4. No 32 kHz crystal: LFOSC calibrated against the 48 MHz crystal. DIO3/DIO4 are GPIOs.
5. Pins: DIO6 SCL, DIO8 SDA, DIO18 TX, DIO20 RX, DIO12 LED, DIO24 CHG_INH, DIO3/4 EN_5V1/2,
   DIO21 3V3_SLEEP, DIO11 IRQ_N; no spares (docs/devboard/cc2340-pin-budget.md).
6. IRQ_N = TPS25751 IRQ x2 + gauge BTP (Q103) + TMP1075 ALERTs, all open-drain.
   One pull-up: R314 (R315, R114 DNP). Firmware polls each source to find which.
7. Diamonds are PWR_FLAGs (ERC only, no part) where a rail is sourced through a passive part.
8. SW301 resets the MCU. Bootloader: ROM bootloader on a blank part or the CCFG backdoor pin.
9. R313 470k (fitted) holds 3V3_SLEEP high in reset (pins float; TPS62177 pulls down 1.4 uA).
   Costs 7 uA while driven low in S2. TP307 probes it.
10. R312 feeds the SMBus pull-ups: remove it and supply TP308 for EV2400 work.
11. R317-R319: J303 overrides EN_5V1/EN_5V2/CHG_INH without shorting the MCU; pin 2 = IRQ_N.
12. DIO24 = CHG_INH (rev A5): LOW allows charging. High or hi-Z stops both chargers
    (R417/R517 pull CE up), so reset/hang/unprogrammed stops charging.
13. Watchdog: CC2340 WDT runs in active, idle and standby and can't be stopped once enabled.
    GPIOs latch in standby; IRQ_N wakes it on an edge (SWRS349A 8.6, 8.11).
14. FET over-temperature: gauge internal sensor (OTD/OTC); U306 is the fallback."""
s = re.sub(r'\(text "NOTES\\n(?:[^"\\]|\\.)*"', lambda m: '(text "' + NOTES.replace("\n", "\\n") + '"', s, count=1)
s = s.replace('(title "MCU and board NTCs")', '(title "MCU and board temperature")')
s = s.replace('(rev "A6")', '(rev "A7")')
s = re.sub(r'\(comment 1 "[^"]*"\)', '(comment 1 "CC2340R5MODA, debug headers, TMP1075 x3 (+2 DNP)")', s, count=1)
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("mcu.kicad_sch: added", len(add), "items, removed", len(set(dels)))

# ================================================================== gauge.kicad_sch: BTP onto IRQ_N, R114 DNP
P = os.path.join(ROOT, "gauge.kicad_sch")
s = open(P, encoding="utf-8").read()
n = s.count('(global_label "GAUGE_BTP"')
s = s.replace('(global_label "GAUGE_BTP"', '(global_label "IRQ_N"')
a, b = sym_spans(s)["R114"]
s = s[:a] + re.sub(r"\(dnp no\)", "(dnp yes)", s[a:b], count=1) + s[b:]
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("gauge.kicad_sch: renamed", n, "GAUGE_BTP labels, R114 DNP")

# ================================================================== root: IRQ1 / IRQ2 -> IRQ_N
P = os.path.join(ROOT, "MonolithDev.kicad_sch")
s = open(P, encoding="utf-8").read()
n = s.count('(global_label "IRQ1"') + s.count('(global_label "IRQ2"')
s = s.replace('(global_label "IRQ1"', '(global_label "IRQ_N"').replace('(global_label "IRQ2"', '(global_label "IRQ_N"')
old = "4.  MCU and NTCs:  STM32WB1MMC, debug headers, board NTCs TH1-TH5, status LED"
assert old in s
s = s.replace(old, "4.  MCU and NTCs:  CC2340R5MODA, debug headers, TMP1075 board temperature sensors, status LED")
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("MonolithDev.kicad_sch: renamed", n, "IRQ labels")
