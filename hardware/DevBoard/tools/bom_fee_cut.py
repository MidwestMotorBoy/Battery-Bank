"""One-shot (2026-10-15): cut JLC extended-part fees for a 2-board build. JLC charges $3 per unique extended part
per order, so at 2 boards each one costs $1.50 per board. Run once from DevBoard/:
    python tools/bom_fee_cut.py
then ERC, tools/netlist_to_board.py (values/fields only; no footprint changes) and tools/bom_cost.py 2.

Swaps to JLC basic/preferred parts (checked against JLC's parts API on 2026-10-15):
    C313 15p C0G   GRM1555C1H150JA01D (ext)  -> 0402CG150J500NT C1548 (basic, C0G)
    C315 1p C0G    GRM1555C1H1R0BA01D (ext)  -> 0402CG1R0C500NT C1550 (preferred, C0G); C314 (DNP) likewise
    C401/C402 220p CL05C221JB5NNNC C0G (ext) -> 0402B221K500NT C1530 (basic, X7R; fine on CC)
    R433/R434 107k/20.0k 0.1 % (ext x2)      -> 120k C17436 (preferred) / 22k C17560 (basic), 1 %: PP5V 5.16 V
    C443 220u 16V ChuangHui polymer (ext)    -> 100u 35V Honor HV1V107M0607PZ C5246554, the part C421 already uses
Hand-fit (bought loose from LCSC, soldered by hand; no JLC fee, out of the position file):
    BT101-BT104 holders, the 13 Harwin test loops, U202 INA190A1, D105 SMAJ18A
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sch_edit as F  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def rd(name):
    return open(os.path.join(ROOT, name), encoding="utf-8").read()


def wr(name, s):
    open(os.path.join(ROOT, name), "w", encoding="utf-8", newline="\n").write(s)


def setp(s, ref, **kv):
    a, b = F.sym_span(s, ref)
    blk = s[a:b]
    at = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+) \d+\)", blk)
    for k, v in kv.items():
        if f'(property "{k}"' in blk:
            blk = F.set_prop(blk, k, v)
        else:
            i = blk.index("\n\t\t(pin ") if "\n\t\t(pin " in blk else blk.index("\n\t\t(instances")
            blk = blk[:i] + F.prop(k, v, float(at.group(1)), float(at.group(2)), True) + blk[i:]
    return s[:a] + blk + s[b:]


def hand_fit(s, ref, why):
    """Move the LCSC number into Sourcing, clear LCSC, drop the part from the position file."""
    a, b = F.sym_span(s, ref)
    blk = s[a:b]
    p = dict(re.findall(r'\(property "([^"]+)" "([^"]*)"', blk))
    src = f"Hand-solder, not JLC assembled ({why}; LCSC {p['LCSC']} {p.get('MPN', '')})"
    s = setp(s, ref, LCSC="", Sourcing=src)
    a, b = F.sym_span(s, ref)
    blk, n = re.subn(r"\(in_pos_files yes\)", "(in_pos_files no)", s[a:b], count=1)
    assert n == 1, ref
    return s[:a] + blk + s[b:]


LOOP = "test loop, dev only; saves a JLC extended-part fee"

# ---------------------------------------------------------------- mcu
s = rd("mcu.kicad_sch")
s = setp(s, "C313", MPN="0402CG150J500NT", LCSC="C1548")
for r in ("C314", "C315"):
    s = setp(s, r, MPN="0402CG1R0C500NT", LCSC="C1550")
s = hand_fit(s, "TP309", LOOP)
wr("mcu.kicad_sch", s)

# ---------------------------------------------------------------- usb_port (shared: also C501/C502, R533/R534, C543, TP5xx)
s = rd("usb_port.kicad_sch")
for r in ("C401", "C402"):
    s = setp(s, r, MPN="0402B221K500NT", LCSC="C1530",
             Notes="50V X7R (JLC basic). 220 pF: with the TPD4S201's 40-120 pF the CC total stays under the TPS25751's "
                   "480 pF (TI EVM value with this protector; review 4 C-3)")
s = setp(s, "R433", Value="120k", MPN="0805W8F1203T5E", LCSC="C17436",
         Notes="PP5V = 0.8 x (1 + 120/22) = 5.16 V (1 % basic parts since 2026-10-15; was 107k/20.0k 0.1 % for 5.08 V): "
               "inside the TPS25751's 4.9-5.5 V PP5V range and USB vSafe5V")
s = setp(s, "R434", Value="22k", MPN="0805W8F2202T5E", LCSC="C17560")
s = setp(s, "C443", Value="100u 35V", MPN="Honor Elec HV1V107M0607PZ (polymer)", LCSC="C5246554",
         Notes="PP5V bulk: USB PD cSrcBulkShared needs 120 uF: 100 uF polymer (no DC-bias loss) + C441/C442 2 x 22 uF. Same "
               "part as C421 since 2026-10-15 (was a 220 uF 16 V polymer) to save a JLC extended-part fee")
for r in ("TP405", "TP406", "TP412"):
    s = hand_fit(s, r, LOOP)
wr("usb_port.kicad_sch", s)

# ---------------------------------------------------------------- gauge
s = rd("gauge.kicad_sch")
for r in ("BT101", "BT102", "BT103", "BT104"):
    s = hand_fit(s, r, "dev-only 21700 holder; saves a JLC extended-part fee")
s = hand_fit(s, "TP109", LOOP)
s = hand_fit(s, "D105", "dev-only bench-input clamp; saves a JLC extended-part fee")
wr("gauge.kicad_sch", s)

# ---------------------------------------------------------------- power
s = rd("power.kicad_sch")
for r in ("TP201", "TP202", "TP203", "TP208", "TP209"):
    s = hand_fit(s, r, LOOP)
s = setp(s, "U202", Sourcing="")                       # hand_fit rewrites it from the LCSC field
s = hand_fit(s, "U202", "dev-only sleep-current amplifier; saves a JLC extended-part fee")
s = F.note_replace(s, r"8. U201 is hand-soldered (DigiKey/Mouser; not in the JLC BOM/CPL). U202 (INA190A1) is JLC-placed.",
                   r"8. U201 (DigiKey/Mouser) and U202 (LCSC) are hand-soldered: not in the JLC BOM/CPL.")
wr("power.kicad_sch", s)
print("done")
