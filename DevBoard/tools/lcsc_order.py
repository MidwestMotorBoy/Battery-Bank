"""LCSC order list for the parts JLC does not place: every hand-fit part on the board (excluded from the position
file) with its LCSC number, plus the loose items the board needs (jumper shunts), for N boards.

Writes fab/MonolithDev-lcsc-order.csv (the order), fab/MonolithDev-lcsc-quick-order.txt (paste into LCSC's
BOM tool / quick order: "C-number,qty" per line) and fab/MonolithDev-lcsc-optional-dnp.csv (the DNP options, not
ordered). Prices, stock and order minimums come from LCSC's product API on the day it runs.
usage: "C:/Program Files/KiCad/10.0/bin/python.exe" -I tools/lcsc_order.py [boards]   (default 3)
"""
import csv
import json
import math
import os
import re
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
FAB = os.path.join(ROOT, "fab")
BOARDS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
API = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode="

# hand-fit parts whose LCSC number is not on the board, and parts bought elsewhere
OVERRIDE = {
    "U201": ("C1852078", "INA190A5IDDFR; Sourcing field says DigiKey/Mouser, LCSC stocks it too"),
    "J301": ("C41376037", "unkeyed 2x5 1.27 mm SMD header (HANXIA PZ1.27-2x5P TP) replacing the Samtec: land "
                          "pattern 0.74 x 2.50 mm pads, rows 4.0 mm apart, fits the FTSH-105 footprint "
                          "(0.74 x 2.79 mm, 4.07 mm); unkeyed, so seat the cable by the silk"),
}
NOT_LCSC = {"U301": "CC2340R5MODAN0MHAR from TI.com, consigned to JLC for placement"}
EXTRAS = [  # (LCSC, per board, designators, what for)
    ("C100114", 2, ["JP201", "JP202"], "2.54 mm jumper shunts (closed top) for AMP_EN and the meas. section power"),
]
ELSEWHERE = [  # needed for bring-up, not from LCSC
    ("U301", "CC2340R5MODAN0MHAR from TI.com, consigned to JLC for placement (not on LCSC)"),
    ("NTCs for J102/J105-J107", "4 per board wired Semitec 103AT-2 10k NTCs: none in stock at LCSC (DigiKey/Mouser)"),
]
NOTES = {
    "C55121754": "SMT test loop on the 1.5 mm test pads (hand-solder)",
}


def lcsc(code):
    out = subprocess.run(["curl", "-s", "-m", "40", "-A", "Mozilla/5.0", API + code], capture_output=True,
                         text=True).stdout
    try:
        r = json.loads(out).get("result") or {}
    except ValueError:
        r = {}
    prices = [(p.get("ladder"), p.get("usdPrice")) for p in (r.get("productPriceList") or [])]
    return {"model": r.get("productModel", ""), "brand": r.get("brandNameEn", ""), "stock": r.get("stockNumber"),
            "min": r.get("minBuyNumber") or 1, "desc": r.get("productIntroEn", ""), "prices": prices}


def unit_price(prices, qty):
    best = None
    for ladder, price in sorted(prices):
        if ladder is not None and qty >= ladder:
            best = price
    return best if best is not None else (prices[0][1] if prices else None)


b = pcbnew.LoadBoard(os.path.join(ROOT, "MonolithDev.kicad_pcb"))
lines, optional, skipped = {}, {}, []
for f in b.GetFootprints():
    ref = f.GetReference()
    a = f.GetAttributes()
    if a & pcbnew.FP_BOARD_ONLY:
        continue
    field = str(f.GetFieldText("LCSC")).strip() if f.HasField("LCSC") else ""
    src = str(f.GetFieldText("Sourcing")) if f.HasField("Sourcing") else ""
    m = re.search(r"LCSC (C\d+)", src)
    code = OVERRIDE.get(ref, (field if field.startswith("C") else (m.group(1) if m else ""), ""))[0]
    if a & pcbnew.FP_DNP:
        if code:
            optional.setdefault(code, []).append(ref)
        continue
    if not a & pcbnew.FP_EXCLUDE_FROM_POS_FILES or a & pcbnew.FP_EXCLUDE_FROM_BOM:
        continue                                   # JLC places it, or it is a bare pad / solder jumper
    if ref in NOT_LCSC or not code:
        skipped.append((ref, NOT_LCSC.get(ref, "no LCSC number")))
        continue
    lines.setdefault(code, {"refs": [], "per": 0, "note": OVERRIDE.get(ref, ("", ""))[1] or NOTES.get(code, "")})
    lines[code]["refs"].append(ref)
    lines[code]["per"] += 1
for code, per, refs, what in EXTRAS:
    lines[code] = {"refs": refs, "per": per, "note": what}

rows, total = [], 0.0
for code, ln in sorted(lines.items(), key=lambda kv: sorted(kv[1]["refs"] or ["~"])[0]):
    info = lcsc(code)
    need = ln["per"] * BOARDS
    qty = max(need, info["min"])
    qty = int(math.ceil(qty / info["min"]) * info["min"])
    up = unit_price(info["prices"], qty)
    ext = round(up * qty, 2) if up is not None else None
    total += ext or 0
    flag = "" if info["stock"] and info["stock"] >= qty else "CHECK STOCK"
    rows.append([code, qty, need, ln["per"], info["model"], info["brand"], info["desc"],
                 ",".join(sorted(ln["refs"])), up, ext, info["stock"], flag, ln["note"]])

with open(os.path.join(FAB, "MonolithDev-lcsc-order.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["LCSC Part Number", "Order Qty", f"Needed ({BOARDS} boards)", "Per Board", "MPN", "Manufacturer",
                "Description", "Designators", "Unit Price (USD)", "Ext. Price (USD)", "LCSC Stock", "Flag", "Notes"])
    w.writerows(rows)
    w.writerow([])
    w.writerow(["", "", "", "", "", "", "", "Total (parts only)", "", round(total, 2)])
    for ref, why in skipped + ELSEWHERE:
        w.writerow([f"not ordered here: {ref}", "", "", "", "", "", "", "", "", "", "", "", why])
with open(os.path.join(FAB, "MonolithDev-lcsc-quick-order.txt"), "w", newline="\n") as fh:
    fh.write("".join(f"{r[0]},{r[1]}\n" for r in rows))
with open(os.path.join(FAB, "MonolithDev-lcsc-optional-dnp.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["LCSC Part Number", "Per Board", "Designators", "MPN", "Description"])
    for code, refs in sorted(optional.items(), key=lambda kv: sorted(kv[1])[0]):
        info = lcsc(code)
        w.writerow([code, len(refs), ",".join(sorted(refs)), info["model"], info["desc"]])

for r in rows:
    print(f"{r[0]:>10} x{r[1]:<4} (need {r[2]:>3}) {r[4][:24]:24s} {r[7][:46]:46s} ${r[9]} {r[11]}")
print(f"total ${total:.2f} for {BOARDS} boards; not ordered: {skipped}; optional DNP lines: {len(optional)}")
