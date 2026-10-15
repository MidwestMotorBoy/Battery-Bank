"""One-shot (rev A8): the pre-routing hardware fixes from schematic review 4
(docs/devboard/schematic-review-4-2026-10-14.md). Edits mcu.kicad_sch and usb_port.kicad_sch in place.

    A-1b  R313 470k -> 220k          3V3_SLEEP pull-up margin against the TPS62177 SLEEP pull-down
    A-5   R314 100k -> 47k           IRQ_N leakage / noise margin
    A-6   R304/R305 4.7k -> 3.3k     SCL/SDA rise time
    A-7   R324 1k in series with J303 pin 2 (IRQ_N probe)
    A-9   R322/R323 1k in series with J302 TX/RX
    A-10  C314 placeholder value and MPN (still DNP)
    B-3   R450/R451 snubber resistors 0805 -> 1206 0.66 W anti-surge (still DNP; a 2010 or 0612 doesn't fit the row)
    C-3   C401/C402 330p -> 220p
    C-4   D401 SMAJ22A -> TVS2200DRVR (flat clamp, TI's pick for the TPS25751)
    C-8   TP415-TP421 (and 5xx): CC1, CC2, SBU_FLT, SBU1_SNS, SBU2_SNS, LIQ_PU, LIQ_PD

Part numbers checked against JLC's parts API on 2026-10-14. Run once from DevBoard/:
    python tools/review4_fixes.py
then tools/place_fields.py on both sheets, ERC, and the board flow (reset_board.py, netlist_to_board.py, place_blocks.py).
"""
import os
import re
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
STOCK = r"C:/Program Files/KiCad/10.0/share/kicad/symbols/"


def U():
    return str(uuid.uuid4())


def g(v):
    return f"{v:.4f}".rstrip("0").rstrip(".")


def block_end(s, start):
    d = 0
    k = start
    while True:
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


def sym_span(s, ref):
    i = s.index(f'(property "Reference" "{ref}"')
    a = s.rindex("\n\t(symbol\n", 0, i)
    return a, block_end(s, a + 2)


def set_prop(blk, name, val):
    new, n = re.subn(r'(\(property "' + re.escape(name) + r'" )"[^"]*"', lambda m: m.group(1) + '"' + val + '"', blk,
                     count=1)
    assert n == 1, (name, blk[:120])
    return new


def edit(s, ref, **kv):
    a, b = sym_span(s, ref)
    blk = s[a:b]
    for k, v in kv.items():
        blk = set_prop(blk, k, v)
    return s[:a] + blk + s[b:]


def move_item(s, kind, name, x, y, nx, ny):
    """Move a label / global label / power symbol whose anchor is at (x, y)."""
    if kind == "symbol":
        pat = re.compile(r'(\n\t\(symbol\n\t\t\(lib_id "[^"]+"\)\n\t\t\(at )' + re.escape(g(x)) + " " + re.escape(g(y))
                         + r"( \d+\))")
    else:
        pat = re.compile(r'(\n\t\(' + kind + ' "' + re.escape(name) + r'"(?:\n\t\t\(shape \w+\))?\n\t\t\(at )'
                         + re.escape(g(x)) + " " + re.escape(g(y)) + r"( \d+\))")
    m = pat.search(s)
    assert m, (kind, name, x, y)
    a = m.start()
    b = block_end(s, a + 2)
    blk = s[a:b]
    dx, dy = nx - x, ny - y
    blk = re.sub(r"\(at ([-\d.]+) ([-\d.]+)( \d+)?\)",
                 lambda q: f"(at {g(float(q.group(1)) + dx)} {g(float(q.group(2)) + dy)}{q.group(3) or ''})", blk)
    return s[:a] + blk + s[b:]


def prop(name, val, x, y, hide):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return (f'\n\t\t(property "{name}" "{val}"\n\t\t\t(at {g(x)} {g(y)} 0){h}\n\t\t\t(show_name no)\n'
            f'\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)')


def new_symbol(lib_id, refs, value, x, y, pins, props, rot=0, dnp=False):
    """refs: [(sheet path, reference), ...] - one entry per instance of the sheet."""
    body = (f'\n\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {g(x)} {g(y)} {rot})\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            f'\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            f'\t\t(dnp {"yes" if dnp else "no"})\n\t\t(uuid "{U()}")')
    body += prop("Reference", refs[-1][1], x, y - 3, False) + prop("Value", value, x, y + 3, False)
    for k, v in props:
        body += prop(k, v, x, y, True)
    for p in pins:
        body += f'\n\t\t(pin "{p}"\n\t\t\t(uuid "{U()}")\n\t\t)'
    body += '\n\t\t(instances\n\t\t\t(project "MonolithDev"'
    for path, ref in refs:
        body += f'\n\t\t\t\t(path "{path}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)'
    return body + "\n\t\t\t)\n\t\t)\n\t)"


def clone(s, tref, refs, x, y, rot, props):
    """Copy symbol tref (same lib symbol) to (x, y, rot) with new references and properties."""
    a, b = sym_span(s, tref)
    blk = s[a:b]
    at = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+) (\d+)\)", blk)
    ox, oy = float(at.group(1)), float(at.group(2))
    blk = re.sub(r"\(at ([-\d.]+) ([-\d.]+) (\d+)\)",
                 lambda m: f"(at {g(float(m.group(1)) - ox + x)} {g(float(m.group(2)) - oy + y)} {m.group(3)})", blk)
    at = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+) (\d+)\)", blk)
    blk = blk[:at.start()] + f"\n\t\t(at {g(x)} {g(y)} {rot})" + blk[at.end():]
    blk = re.sub(r'\(uuid "[^"]+"\)', lambda m: f'(uuid "{U()}")', blk)
    blk = set_prop(blk, "Reference", refs[-1][1])
    for path, ref in refs:
        blk, n = re.subn(r'(\(path "' + re.escape(path) + r'"\s*\(reference )"[^"]+"', lambda m: m.group(1) + f'"{ref}"', blk)
        assert n == 1, (tref, path)
    for k, v in props:
        blk = set_prop(blk, k, v)
    return blk


def label(name, x, y, ang):
    just = "left bottom" if ang in (0, 90) else "right bottom"
    return (f'\n\t(label "{name}"\n\t\t(at {g(x)} {g(y)} {ang})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n\t)')


def wire(x0, y0, x1, y1):
    return (f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {g(x0)} {g(y0)}) (xy {g(x1)} {g(y1)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n'
            f'\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')


def junction(x, y):
    return f'\n\t(junction\n\t\t(at {g(x)} {g(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)'


def drop(s, pattern):
    """Delete the one top-level item whose text starts with the regex pattern."""
    m = list(re.finditer(pattern, s))
    assert len(m) == 1, (pattern, len(m))
    a = m[0].start()
    return s[:a] + s[block_end(s, a + 2):]


def insert_items(s, text):
    k = s.rindex("\n\t(sheet_instances")
    return s[:k] + text + s[k:]


def paths_of(s, ref):
    a, b = sym_span(s, ref)
    return re.findall(r'\(path "([^"]+)"\s*\(reference "([^"]+)"\)', s[a:b])


def note_replace(s, old, new):
    assert s.count(old) == 1, old
    return s.replace(old, new)


# ================================================================== mcu.kicad_sch
P = os.path.join(ROOT, "mcu.kicad_sch")
s = open(P, encoding="utf-8").read()

s = edit(s, "R313", Value="220k", MPN="0603WAF2203T5E", LCSC="C22961",
         Notes="3V3_SLEEP pull-up: holds the TPS62177 in normal mode while U301 is in reset or unprogrammed (pins float; "
               "SLEEP pull-down 1.4 uA typ, no max). 220k gives about 0.92 x VDDS typ against VIH 0.8 x VDDS "
               "(review 4 A-1b); 15 uA while firmware drives SLEEP low in S2")
s = edit(s, "R314", Value="47k", MPN="0603WAF4702T5E", LCSC="C25819",
         Notes="The one IRQ_N pull-up (TPS25751 I2Ct_IRQ x2, gauge BTP via Q103, TMP1075 ALERTs; all open drain). 47k for "
               "leakage and noise margin on a long net (review 4 A-5); 70 uA only while asserted")
for r in ("R304", "R305"):
    s = edit(s, r, Value="3.3k", MPN="0603WAF3301T5E", LCSC="C22978")
s = edit(s, "C314", Value="1p C0G", MPN="GRM1555C1H1R0BA01D", LCSC="C76952")
a, b = sym_span(s, "C314")
blk = s[a:b]
if '(property "Notes"' not in blk:
    k = blk.index('\n\t\t(property "LCSC"')
    blk = blk[:k] + prop("Notes", "Z60 shunt, DNP as on TI's LaunchPad. Placeholder value: TI characterised the match on "
                                  "0201 parts, so retune Z60/Z61/Z62 on this board (review 4 A-10)", 184.15, 110.49, True) + blk[k:]
    s = s[:a] + blk + s[b:]

# A-9: R322/R323 in series with J302 TX (pin 1) and RX (pin 2). The pins end at x 299.72; each resistor spans
# 292.1-299.72 and the UART labels move to its far end.
MCU_PATH = paths_of(s, "R317")[0][0]
add = ""
for ref, y, name in (("R322", 134.62, "UART_TX"), ("R323", 137.16, "UART_RX")):
    s = move_item(s, "label", name, 299.72, y, 292.1, y)
    add += clone(s, "R317", [(MCU_PATH, ref)], 295.91, y, 90,
                 [("Notes", "Series resistor at J302: limits current from a USB-UART adapter into an unpowered U301 "
                            "(review 4 A-9). Connect the adapter only with 3V3 up; recovery is SWD (J301)")])
# A-7: R324 in series with J303 pin 2 (IRQ_N).
s = move_item(s, "global_label", "IRQ_N", 299.72, 160.02, 292.1, 160.02)
add += clone(s, "R317", [(MCU_PATH, "R324")], 295.91, 160.02, 90,
             [("Notes", "Series resistor at J303 pin 2 (IRQ_N probe): a shunt on pins 1-2 can't short 3V3 through the "
                        "open-drain sinks (review 4 A-7)")])
s = insert_items(s, add)

s = note_replace(s, r"One pull-up: R314 (R315, R114 DNP).", r"One pull-up: R314 47k (R315, R114 DNP).")
s = note_replace(s, r"9. R313 470k (fitted) holds 3V3_SLEEP high in reset (pins float; TPS62177 pulls down 1.4 uA).\n"
                    r"   Costs 7 uA while driven low in S2. TP307 probes it.",
                 r"9. R313 220k holds 3V3_SLEEP high in reset (pins float; TPS62177 pulls down 1.4 uA typ).\n"
                 r"   Costs 15 uA while driven low in S2. TP307 probes it. DIO21 is also the default ROM-bootloader pin:\n"
                 r"   disable or move that trigger in the CCFG before the first flash (review 4 A-1).")
s = note_replace(s, r"11. R317-R319: J303 overrides EN_5V1/EN_5V2/CHG_INH without shorting the MCU; pin 2 = IRQ_N.",
                 r"11. R317-R319: J303 overrides EN_5V1/EN_5V2/CHG_INH without shorting the MCU; pin 2 = IRQ_N via R324.\n"
                 r"    R322/R323: 1k in the UART lines; connect a USB-UART adapter only with 3V3 up.")
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("mcu.kicad_sch: R313, R314, R304, R305, C314 edited; R322, R323, R324 added")

# ================================================================== usb_port.kicad_sch
P = os.path.join(ROOT, "usb_port.kicad_sch")
s = open(P, encoding="utf-8").read()
PORT = {r[1][-3]: r[0] for r in paths_of(s, "TP413")}          # '4' -> port 1 path, '5' -> port 2 path


def refs(n):
    return [(PORT["5"], f"{n[:-3]}5{n[-2:]}"), (PORT["4"], n)]


for r in ("C401", "C402"):
    s = edit(s, r, Value="220p 50V", MPN="CL05C221JB5NNNC", LCSC="C307445",
             Notes="50V C0G. 220 pF: with the TPD4S201's 40-120 pF the CC total stays under the TPS25751's 480 pF "
                   "(TI EVM value with this protector; review 4 C-3)")
for r, node in (("R450", "SW1"), ("R451", "SW2")):
    s = edit(s, r, Footprint="Resistor_SMD:R_1206_3216Metric", MPN="ERJ-P08J3R3V", LCSC="C3998398",
             Notes=f"DNP RC snubber on {node} (EVM R14/R15 placeholder). 1206 anti-surge 0.66 W: R loss is about C x V^2 x fsw, "
                   "0.3-0.55 W at the sizes the ring may need (review 4 B-3). Size R and C from the measured ring")

# C-4: D401 (Device:D_Zener at 73.66, 88.9, hanging off the VBUS wire at y 81.28) -> TVS2200DRV. The new symbol is
# much wider and would cover J401's pin labels, so it moves right into the gap between C450 and C401 (x 93.98):
# a drop from the VBUS wire to its IN pins (y 85.09), GND pins at y 100.33 where #PWR403 moves to.
pp = open(STOCK + "Power_Protection.kicad_sym", encoding="utf-8").read()
i = pp.index('(symbol "TVS0500DRV"')
base = pp[i:block_end(pp, i)]
i = pp.index('(symbol "TVS2200DRV"')
der = pp[i:block_end(pp, i)]
tvs = base.replace('(symbol "TVS0500DRV"', '(symbol "Power_Protection:TVS2200DRV"', 1)
tvs = tvs.replace('"TVS0500DRV_', '"TVS2200DRV_')
for name, val in re.findall(r'\(property "([^"]+)" "([^"]*)"', der):
    if name != "Reference":
        tvs = set_prop(tvs, name, val)
la = s.index("\n\t(lib_symbols")
lb = block_end(s, la + 2)
lib = s[la:lb]
if '"Power_Protection:TVS2200DRV"' not in lib:
    k = lib.rindex(")")
    lib = lib[:k] + "\t" + tvs + "\n\t" + lib[k:]
s = s[:la] + lib + s[lb:]

a, b = sym_span(s, "D401")
assert '(lib_id "Device:D_Zener")' in s[a:b]
s = s[:a] + s[b:]
TX = 93.98
s = drop(s, r"\n\t\(wire\n\t\t\(pts\n\t\t\t\(xy 73\.66 81\.28\) \(xy 73\.66 85\.09\)")
s = drop(s, r"\n\t\(junction\n\t\t\(at 73\.66 81\.28\)")
s = move_item(s, "symbol", None, 73.66, 92.71, TX, 100.33)
TI_TVS = "https://www.ti.com/lit/ds/symlink/tvs2200.pdf"
add = wire(TX, 81.28, TX, 85.09) + junction(TX, 81.28)
add += new_symbol("Power_Protection:TVS2200DRV", refs("D401"), "TVS2200DRVR", TX, 92.71, [str(n) for n in range(1, 8)],
                 [("Footprint", "Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm"), ("Datasheet", TI_TVS),
                  ("Description", "Flat-clamp surge protection, 22 V standoff, WSON-6 2x2"),
                  ("LCSC", "C523793"), ("MPN", "TVS2200DRVR"),
                  ("Notes", "VBUS flat-clamp TVS (TI's recommendation for the TPS25751; on its EVM): 22 V standoff, "
                            "24.6 V breakdown min, 28 V clamp at 40 A 8/20 us, 105 pF. Replaces the SMAJ22A (35.5 V clamp; "
                            "review 4 C-4). Pins 1-3 + EP to GND, 4-6 to VBUS")])

# C-8: test pads on the CC (controller side), SBU-fault, SBU-sense and liquid-detect gate nets, in a second row
# under the existing test points (y 289.56, 15.24 pitch; their labels hang down to about y 301), same label style.
X0, Y = 121.92, 312.42
for n, (ref, net) in enumerate((("TP415", "CC1"), ("TP416", "CC2"), ("TP417", "SBU_FLT"), ("TP418", "SBU1_SNS"),
                                ("TP419", "SBU2_SNS"), ("TP420", "LIQ_PU"), ("TP421", "LIQ_PD"))):
    x = X0 + 15.24 * n
    add += clone(s, "TP413", refs(ref), x, Y, 0, [("Value", net), ("Footprint", "TestPoint:TestPoint_Pad_D1.0mm")])
    add += label(net, x, Y, 270)
s = insert_items(s, add)

s = note_replace(s, r"C401/C402 on the controller side.", r"C401/C402 (220 pF) on the controller side.")
s = note_replace(s, r"   R442/R443 hold the liquid-detect FETs off while GPIO6/7 are Hi-Z.",
                 r"   R442/R443 hold the liquid-detect FETs off while GPIO6/7 are Hi-Z. TP415-TP421: CC, SBU and liquid-detect probes.\n"
                 r"   D401 = TVS2200 flat clamp on VBUS (28 V at 40 A 8/20 us; TI's pick for the TPS25751).")
s = note_replace(s, r"R450/C454 and R451/C455 DNP snubbers.", r"R450/C454 and R451/C455 DNP snubbers (R 1206 0.66 W).")
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("usb_port.kicad_sch: C401, C402, R450, R451 edited; D401 -> TVS2200DRV; TP415-TP421 added")
