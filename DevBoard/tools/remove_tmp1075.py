"""One-shot (2026-10-17): remove the TMP1075 board sensors U302-U306 and their caps C308-C312.

Board temperature now comes from the gauge (TS1-TS4 cell NTCs, FET and die temperature via DAStatus2, readable
sealed) and from each BQ25756's TS NTC (TH401/TH501), read through the TPS25751's 'I2Cr' pass-through (REG0x37 TS_ADC).
Deletes the parts, their power symbols, wires, labels, junctions and address notes from mcu.kicad_sch (everything
inside the two sensor areas), updates the heading and NOTES, drops the TMP1075 library symbol, and deletes the
footprints from the board (they were parked off-board, unrouted).

Run from DevBoard/: python tools/remove_tmp1075.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
REFS = ["U302", "U303", "U304", "U305", "U306", "C308", "C309", "C310", "C311", "C312"]
BOXES = [(40, 183, 182, 219), (105, 225, 196, 261)]


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


def top_blocks(s, head):
    out = []
    pat = "\n\t(" + head
    i = s.find(pat)
    while i >= 0:
        e = block_end(s, i + 2)
        out.append((i, e))
        i = s.find(pat, e)
    return out


def inb(x, y):
    return any(a <= x <= c and b <= y <= d for a, b, c, d in BOXES)


# ---------------------------------------------------------------- schematic
P = os.path.join(ROOT, "mcu.kicad_sch")
s = open(P, encoding="utf-8").read()
drop = []
for a, b in top_blocks(s, "symbol\n"):
    blk = s[a:b]
    m = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+)", blk)
    ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
    if ref in REFS or (ref.startswith("#") and inb(float(m.group(1)), float(m.group(2)))):
        drop.append((a, b))
for head in ("wire", "label", "global_label", "junction", "no_connect", "text "):
    for a, b in top_blocks(s, head):
        blk = s[a:b]
        pts = [(float(x), float(y)) for x, y in re.findall(r"\((?:xy|at) ([-\d.]+) ([-\d.]+)", blk)[:2]]
        if pts and all(inb(x, y) for x, y in pts):
            drop.append((a, b))
for a, b in sorted(drop, reverse=True):
    s = s[:a] + s[b:]
print("mcu.kicad_sch: removed", len(drop), "items")

# library symbol
i = s.find('\n\t\t(symbol "Sensor_Temperature:TMP1075DSG"')
if i >= 0:
    s = s[:i] + s[block_end(s, i + 3):]

old = "BOARD TEMPERATURE  (TMP1075 on I2C, 0x48-0x4C; ALERT wire-ORed onto IRQ_N)"
assert old in s
s = s.replace(old, "BOARD TEMPERATURE: no parts here (rev A8). Gauge TS1-TS4 + FET temp, charger NTCs via TPS25751 I2Cr")  # heading removed afterwards (overlapped)
reps = [
    ("6. IRQ_N = TPS25751 IRQ x2 + gauge BTP (Q103) + TMP1075 ALERTs, all open-drain.",
     "6. IRQ_N = TPS25751 IRQ x2 + gauge BTP (Q103), all open-drain."),
    ("14. FET over-temperature: gauge internal sensor (OTD/OTC); U306 is the fallback.",
     "14. Temperatures (rev A8, TMP1075s removed): cells and protection FETs from the gauge (DAStatus2, MAC 0x0072,\\n"
     "    readable sealed); each charger stage from its BQ25756 TS NTC, REG0x37 TS_ADC read through the TPS25751 'I2Cr'."),
]
for a, b in reps:
    assert a in s, a
    s = s.replace(a, b)
s = re.sub(r'\(comment 1 "[^"]*"\)', '(comment 1 "CC2340R5MODA, debug headers, status LED")', s, count=1)
open(P, "w", encoding="utf-8", newline="\n").write(s)

# ---------------------------------------------------------------- board
P = os.path.join(ROOT, "MonolithDev.kicad_pcb")
s = open(P, encoding="utf-8").read()
drop = []
for a, b in top_blocks(s, "footprint "):
    m = re.search(r'\(property "Reference" "([^"]+)"', s[a:b])
    if m and m.group(1) in REFS:
        drop.append((a, b))
for a, b in sorted(drop, reverse=True):
    s = s[:a] + s[b:]
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("MonolithDev.kicad_pcb: removed", len(drop), "footprints")
