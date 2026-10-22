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
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
STOCK = r"C:/Program Files/KiCad/10.0/share/kicad/symbols/"
sys.path.insert(0, HERE)
from sch_edit import (U, g, block_end, sym_span, set_prop, edit, move_item, prop, new_symbol,  # noqa: E402,F401
                      clone, label, wire, junction, drop, insert_items, paths_of, note_replace)



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
