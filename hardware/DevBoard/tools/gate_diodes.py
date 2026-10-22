"""One-shot (2026-10-17): charger gate resistors R444-R447 (R544-R547) 0R -> 10R, with a BAT54WS turn-off diode across
each (D406-D409 / D506-D509), anode at the FET gate, cathode at the BQ25756 driver pin. Turn-on goes through the 10R
(slower edges); turn-off bypasses it through the diode, so the 45 ns dead time is kept. Fixes the gate-resistor Notes,
which named the wrong drivers.

Edits usb_port.kicad_sch (shared by both ports). Run from DevBoard/: python tools/gate_diodes.py
"""
import os
import re
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "..", "usb_port.kicad_sch")
s = open(P, encoding="utf-8").read()


def U():
    return str(uuid.uuid4())


def block_end(t, i):
    d = 0
    k = i
    while True:
        c = t[k]
        if c == '"':
            k += 1
            while t[k] != '"':
                k += 2 if t[k] == "\\" else 1
        elif c == "(":
            d += 1
        elif c == ")":
            d -= 1
            if d == 0:
                return k + 1
        k += 1


def sym_span(ref):
    i = s.index(f'(reference "{ref}")')
    a = s.rfind("\n\t(symbol\n", 0, i)
    return a, block_end(s, a + 2)


def set_prop(blk, name, val):
    new, n = re.subn(r'(\(property "' + re.escape(name) + r'" )"(?:[^"\\]|\\.)*"', lambda m: m.group(1) + '"' + val + '"',
                     blk, count=1)
    assert n == 1, name
    return new


def shift_block(blk, dy):
    def f(m):
        return f"(at {m.group(1)} {float(m.group(2)) + dy:.2f} {m.group(3)})"
    return re.sub(r"\(at ([-\d.]+) ([-\d.]+) (\d+)\)", f, blk)


def g(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


X0 = 309.88
XL, XR = X0 - 3.81, X0 + 3.81                     # resistor (rot 90) pin ends: driver side left, gate side right
OLD_Y = {"R444": 271.78, "R445": 279.4, "R446": 287.02, "R447": 294.64}
NEW_Y = {"R444": 271.78, "R445": 283.21, "R446": 294.64, "R447": 306.07}   # 11.43 mm rows: diode + next row's text fit
GATE = {"R444": ("HIDRV1", "HG1", "Q401 / Q501 high side (SW1 leg)", "D406", "D506"),
        "R445": ("LODRV1", "LG1", "Q407 / Q507 low side (SW1 leg)", "D407", "D507"),
        "R446": ("HIDRV2", "HG2", "Q402 / Q502 high side (SW2 leg)", "D408", "D508"),
        "R447": ("LODRV2", "LG2", "Q408 / Q508 low side (SW2 leg)", "D409", "D509")}

# ---- 1. resistors: value, part, notes, new row positions; move their pin labels with them
for ref, (drv, gate, fet, d1, d2) in GATE.items():
    a, b = sym_span(ref)
    blk = s[a:b]
    blk = set_prop(blk, "Value", "10R")
    blk = set_prop(blk, "LCSC", "C22859")
    blk = set_prop(blk, "MPN", "0603WAF100JT5E")
    blk = set_prop(blk, "Notes", f"Gate resistor {drv} -> {gate}, {fet}. 10 Ohm slows turn-on; {d1}/{d2} (BAT54WS, "
                                 f"anode at the gate) bypasses it at turn-off so the 45 ns dead time is kept")
    dy = NEW_Y[ref] - OLD_Y[ref]
    if dy:
        blk = shift_block(blk, dy)
    s = s[:a] + blk + s[b:]
    if dy:
        for name, x in ((drv, XL), (gate, XR)):
            pat = r'(\(label "' + name + r'"\n\t\t\(at ' + re.escape(g(x)) + r" )" + re.escape(g(OLD_Y[ref])) + r"( \d+\))"
            s, n = re.subn(pat, lambda m: m.group(1) + g(NEW_Y[ref]) + m.group(2), s)
            assert n == 1, (name, x, OLD_Y[ref])

# ---- 2. diodes: clone D404 (Device:D_Schottky, rot 0: K pin 1 left, A pin 2 right), one row below each resistor
ta, tb = sym_span("D404")
tmpl = s[ta:tb]
tat = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+) (\d+)\)", tmpl)
tx, ty = float(tat.group(1)), float(tat.group(2))
assert tat.group(3) == "0"
add = []
for ref, (drv, gate, fet, d1, d2) in GATE.items():
    y = NEW_Y[ref] + 3.81
    blk = tmpl

    def mv(m):
        return f"(at {g(float(m.group(1)) - tx + X0)} {g(float(m.group(2)) - ty + y)} {m.group(3)})"
    blk = re.sub(r"\(at ([-\d.]+) ([-\d.]+) (\d+)\)", mv, blk)
    blk = re.sub(r'\(uuid "[^"]+"\)', lambda m: f'(uuid "{U()}")', blk)
    blk = blk.replace('(reference "D404")', f'(reference "{d1}")').replace('(reference "D504")', f'(reference "{d2}")')
    blk = set_prop(blk, "Reference", d1)
    blk = set_prop(blk, "Value", "BAT54WS")
    blk = set_prop(blk, "Footprint", "Diode_SMD:D_SOD-323")
    blk = set_prop(blk, "LCSC", "C7502694")
    blk = set_prop(blk, "MPN", "BAT54WS (R+O)")
    blk = set_prop(blk, "Notes", f"Turn-off diode across {ref[:1]}{ref[1:]}: cathode {drv}, anode {gate} ({fet})")
    # reference / value to the right of the diode, clear of the resistor text above and below
    for name, fy in (("Reference", y - 0.635), ("Value", y + 1.27)):
        blk, n = re.subn(r'(\(property "' + name + r'" "[^"]*"\n\t\t\t\(at )[-\d.]+ [-\d.]+ \d+\)',
                         lambda m: m.group(1) + f"{g(X0 + 9.525)} {g(fy)} 0)", blk, count=1)
        assert n == 1, name
    add.append(blk)
    # wires from the resistor pins down to the diode pins, junction dots at the resistor pins
    for x in (XL, XR):
        add.append(f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {g(x)} {g(NEW_Y[ref])}) (xy {g(x)} {g(y)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)'
                   f'\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
        add.append(f'\n\t(junction\n\t\t(at {g(x)} {g(NEW_Y[ref])})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)')
k = s.rindex("\n\t(sheet_instances")
s = s[:k] + "".join(add) + s[k:]
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("usb_port.kicad_sch: 4 gate resistors -> 10R, 4 diodes (x2 instances) added")
