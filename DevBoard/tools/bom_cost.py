"""Costed BOM for the dev board: exports the netlist with kicad-cli, prices every LCSC part from JLC's parts API at
the quantity JLC would actually buy (its minimum order and attrition), and writes ../bom_cost.csv.

Run: python tools/bom_cost.py [boards]   (from DevBoard/, default 5 boards; uses KiCad's python)

Parts bought elsewhere are priced from OUTSIDE below (update by hand). Parts with neither an LCSC number nor an
OUTSIDE price are listed with a blank price. kicad-cli rewrites MonolithDev.kicad_pro, so it is restored from git.
"""
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
KICAD_CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
URL = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
FEE = 3.0          # JLC loading fee per unique extended part per order (basic and preferred parts: none)
# Bought outside JLC: ref prefix -> (unit price USD, source). U301 is consigned to JLC for placement.
# Rev A7: U301 is the CC2340R5MODA. JLC lists it (C55046847) with 0 stock; TI.com prices it at $4.028 (1-99),
# $3.284 (100-249), $2.581 (250-999), $2.189 (1k+). In stock at TI.com (2026-10-15, seen logged in; a logged-out
# visitor sees "Not available").
OUTSIDE = {"U301": (4.028, "TI.com CC2340R5MODAN0MHAR, qty 1-99, in stock 2026-10-15")}
CONSIGNED = {"U301"}


def _ports(*refs):
    """Port-sheet refs are listed as 4xx; add the 5xx twin."""
    return set(refs) | {r[0:len(r) - 3] + "5" + r[-2:] for r in refs if re.match(r"[A-Z]+4\d\d$", r)}


# Planned for the production board? The dev board is the complete production circuit (circuit-description.md,
# "Purpose") plus test and measurement extras; this map is the dev-only / undecided part of it.
DEV_ONLY = {
    **{r: "21700 holders; production uses a welded pack" for r in ("BT101", "BT102", "BT103", "BT104")},
    **{r: "NTC wire header; production solders the NTC leads" for r in ("J102", "J105", "J106", "J107")},
    "J103": "EV2400 header", "J104": "bench PACK_P input", "D104": "bench input diode", "D105": "bench input clamp",
    **{r: "sleep-current measurement section" for r in ("R201", "R202", "R203", "R204", "R205", "R206", "U201", "U202",
                                                         "U203", "C202", "C203", "C204", "C205", "JP201", "JP202")},
    "R207": "0R measurement link", "R301": "0R measurement link", "R307": "0R LED link (sleep measurement)",
    "R312": "0R EV2400 helper link",
    "J301": "SWD header; production uses pogo pads", "SW301": "reset button; production uses a test pad",
    "J302": "UART header", "J303": "spare-GPIO header",
    **{r: "series resistor to the J303 header" for r in ("R317", "R318", "R319")},
    **{r: "I2Cc logic-analyzer header" for r in _ports("J402")},
}
MAYBE = {
    "SW101": "wake button (production wake method not decided)", "R118": "wake button resistor",
    **{r: "BTP_INT level shift (production may tie BTP_INT to VSS)" for r in ("Q103", "R114", "R117")},
    "D301": "status LED (production has its own LED set)", "R306": "status LED resistor",
    **{r: "0R gate/BTST tuning placeholder (keep if EMI needs it)" for r in
       _ports("R444", "R445", "R446", "R447", "R448", "R449")},
}


def production(ref):
    if ref.startswith("TP"):
        return "no", "test point"
    if ref in DEV_ONLY:
        return "no", DEV_ONLY[ref]
    if ref in MAYBE:
        return "maybe", MAYBE[ref]
    return "yes", ""


def parse(t):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', t)
    st = [[]]
    for k in toks:
        if k == "(":
            st.append([])
        elif k == ")":
            x = st.pop()
            st[-1].append(x)
        else:
            st[-1].append(k[1:-1] if k[0] == '"' else k)
    return st[0][0]


def find(n, key):
    return [c for c in n if isinstance(c, list) and c and c[0] == key]


def val(n, key):
    f = find(n, key)
    return f[0][1] if f and len(f[0]) > 1 else ""


def netlist_components():
    out = os.path.join(tempfile.mkdtemp(), "bom.net")
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out,
                    os.path.join(ROOT, "MonolithDev.kicad_sch")], check=True, capture_output=True)
    subprocess.run(["git", "checkout", "--", "MonolithDev.kicad_pro"], cwd=ROOT, capture_output=True)
    tree = parse(open(out, encoding="utf-8").read())
    comps = {}
    for c in find(find(tree, "components")[0], "comp"):
        fields = {val(f, "name"): (f[2] if len(f) > 2 else "") for fs in find(c, "fields") for f in find(fs, "field")}
        props = {val(p, "name") for p in find(c, "property")}
        comps[val(c, "ref")] = dict(value=val(c, "value"), fp=val(c, "footprint").split(":")[-1], fields=fields,
                                    dnp="dnp" in props, no_bom="exclude_from_bom" in props)
    return comps


def jlc(code, cache):
    if code not in cache:
        r = subprocess.run(["curl", "-s", "-m", "40", "-X", "POST", URL, "-H", "Content-Type: application/json", "-d",
                            json.dumps({"keyword": code, "currentPage": 1, "pageSize": 5})],
                           capture_output=True, text=True).stdout
        rec = None
        for x in (json.loads(r)["data"]["componentPageInfo"]["list"] or []):
            if x["componentCode"] == code:
                lib = x["componentLibraryType"]
                rec = dict(lib="basic" if lib == "base" else ("preferred" if x.get("preferredComponentFlag") else "extended"),
                           stock=x["stockCount"], prices=x["componentPrices"], least=x.get("leastPatchNumber") or 1,
                           loss=x.get("lossNumber") or 0, model=x["componentModelEn"])
        cache[code] = rec
    return cache[code]


def price_at(prices, q):
    p = prices[0]["productPrice"]
    for t in sorted(prices, key=lambda t: t["startNumber"]):
        if q >= t["startNumber"]:
            p = t["productPrice"]
    return p


def main():
    boards = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    comps = netlist_components()
    cache = {}
    groups = defaultdict(list)
    for ref, c in comps.items():
        if ref.startswith("#") or c["dnp"] or c["no_bom"]:
            continue
        f = c["fields"]
        lcsc = f.get("LCSC", "")
        hand = re.search(r"LCSC (C\d+)", f.get("Sourcing", ""))          # hand-fit parts bought from LCSC
        if hand and not lcsc:
            lcsc = "hand:" + hand.group(1)
        # one line per LCSC part (so its minimum buy and fee count once); unnumbered parts by MPN/value/footprint
        key = (lcsc, "", "", "") if lcsc else ("", f.get("MPN", ""), c["value"], c["fp"])
        groups[key].append(ref)

    def refkey(r):
        m = re.match(r"([A-Z]+)(\d+)", r)
        return (m.group(1), int(m.group(2))) if m else (r, 0)

    rows, tot, fees = [], 0.0, 0
    prod_tot = [0.0, 0.0]          # parts planned for production: "yes" only, and "yes" + "maybe"
    for (lcsc, mpn, value, fp), refs in sorted(groups.items(), key=lambda kv: refkey(min(kv[1], key=refkey))):
        refs = sorted(refs, key=refkey)
        n = len(refs)
        c0 = comps[refs[0]]
        value, fp, mpn = c0["value"], c0["fp"], c0["fields"].get("MPN", "")
        src, unit, buy, lib, stock = "", None, "", "", ""
        out = [OUTSIDE[r] for r in refs if r in OUTSIDE]
        hand = lcsc.startswith("hand:")
        lcsc = lcsc.replace("hand:", "")
        if out:
            unit, src = out[0]
            buy = n * boards
            lib = "consigned to JLC" if refs[0] in CONSIGNED else "hand-fit"
        elif lcsc:
            r = jlc(lcsc, cache)
            if r:
                if hand:                                                   # bought loose from LCSC, no JLC fee
                    buy = n * boards
                    unit = price_at(r["prices"], buy)
                    lib, stock, src = "hand-fit", r["stock"], "LCSC (hand-solder)"
                else:
                    buy = max(r["least"], n * boards + r["loss"])
                    unit = price_at(r["prices"], buy) * buy / (n * boards)    # minimum buy and attrition spread
                    lib, stock, src = r["lib"], r["stock"], "JLC"
                    fees += lib == "extended"
            else:
                src = "JLC: not found"
        else:
            src = comps[refs[0]]["fields"].get("Sourcing", "hand-fit")
        line = None if unit is None else unit * n
        tot += line or 0.0
        status = [(r, *production(r)) for r in refs]
        kinds = {s for _, s, _ in status}
        prod = kinds.pop() if len(kinds) == 1 else "partly"
        n_prod = sum(s == "yes" for _, s, _ in status)
        n_maybe = sum(s == "maybe" for _, s, _ in status)
        if unit is not None:
            prod_tot[0] += unit * n_prod
            prod_tot[1] += unit * (n_prod + n_maybe)
        why = defaultdict(list)
        for r, s, w in status:
            if s != "yes":
                why[f"{s}: {w}"].append(r)
        note = "; ".join(f"{','.join(rs)} {w}" if prod == "partly" else w for w, rs in why.items())
        rows.append([",".join(refs), n, value, mpn, lcsc, fp, lib, stock, buy,
                     "" if unit is None else f"{unit:.4f}", "" if line is None else f"{line:.2f}", src,
                     prod, n_prod, note])

    fee_board = FEE * fees / boards
    path = os.path.join(ROOT, "bom_cost.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([f"Monolith dev board costed BOM, {boards} boards, JLC prices fetched by tools/bom_cost.py"])
        w.writerow(["refs", "qty_per_board", "value", "mpn", "lcsc", "footprint", "library", "jlc_stock",
                    f"jlc_buy_qty_{boards}_boards", "unit_usd_incl_min_buy", "per_board_usd", "source",
                    "in_production", "production_qty_per_board", "production_note"])
        w.writerows(rows)
        w.writerow([])
        w.writerow(["parts per board", "", "", "", "", "", "", "", "", "", f"{tot:.2f}"])
        w.writerow(["production-intent parts at these dev-board prices: in_production = yes", "", "", "", "", "", "",
                    "", "", "", f"{prod_tot[0]:.2f}"])
        w.writerow(["production-intent parts at these dev-board prices: yes + maybe", "", "", "", "", "", "", "", "",
                    "", f"{prod_tot[1]:.2f}"])
        w.writerow([f"JLC extended-part fees: {fees} x ${FEE:.0f} per order / {boards} boards", "", "", "", "", "", "", "",
                    "", "", f"{fee_board:.2f}"])
        w.writerow(["total per board (excl. PCB, assembly, shipping, cells, blank-price parts)", "", "", "", "", "", "",
                    "", "", "", f"{tot + fee_board:.2f}"])
    blanks = [r[0] for r in rows if r[10] == ""]
    print(f"{boards} boards: parts ${tot:.2f}/board, {fees} extended fees -> ${fee_board:.2f}/board, "
          f"total ${tot + fee_board:.2f}/board. Unpriced: {', '.join(blanks)}. Wrote {path}")


if __name__ == "__main__":
    main()
