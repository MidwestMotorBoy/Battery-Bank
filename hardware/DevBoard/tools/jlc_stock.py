"""JLC stock check for the assembly BOM: one query per LCSC number in fab/MonolithDev-bom.csv, prints the lines whose
part is out of stock, missing from JLC's catalogue or no longer basic/preferred as the BOM assumes.
usage: "C:/Program Files/KiCad/10.0/bin/python.exe" -I tools/jlc_stock.py [--all]
"""
import csv
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOM = os.path.join(HERE, "..", "fab", "MonolithDev-bom.csv")
URL = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"


def lookup(code):
    r = subprocess.run(["curl", "-s", "-m", "40", "-X", "POST", URL, "-H", "Content-Type: application/json", "-d",
                        json.dumps({"keyword": code, "currentPage": 1, "pageSize": 5})], capture_output=True, text=True).stdout
    try:
        lst = json.loads(r)["data"]["componentPageInfo"]["list"] or []
    except (ValueError, KeyError, TypeError):
        return None
    for x in lst:
        if x["componentCode"] == code:
            lib = x["componentLibraryType"]
            lib = "basic" if lib == "base" else ("preferred" if x.get("preferredComponentFlag") else "extended")
            p = x["componentPrices"]
            return {"stock": x["stockCount"], "lib": lib, "price": p[0]["productPrice"] if p else None,
                    "mpn": x["componentModelEn"]}
    return {}


rows = list(csv.DictReader(open(BOM, newline="")))
bad = []
for row in rows:
    code = row["LCSC Part #"]
    info = lookup(code)
    n = len(row["Designator"].split(","))
    line = f'{code:>10} x{n:<3} {row["Comment"][:22]:22s} {row["Designator"].split(",")[0]:6s}'
    if info is None:
        print(line, "API error"); bad.append(row); continue
    if not info:
        print(line, "NOT IN JLC CATALOGUE"); bad.append(row); continue
    flag = "OUT OF STOCK" if info["stock"] == 0 else ("low stock" if info["stock"] < 5 * n else "")
    if flag or "--all" in sys.argv:
        print(line, f'{info["lib"]:9s} stock {info["stock"]:>7} ${info["price"]} {info["mpn"]} {flag}')
    if flag == "OUT OF STOCK":
        bad.append(row)
print(f"\n{len(rows)} BOM lines checked, {len(bad)} need attention")
