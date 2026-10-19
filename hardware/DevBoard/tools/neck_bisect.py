"""Locate DRC connection_width necks in the GND planes by bisection on a board copy.

DRC reports a plane neck only at the zone's origin. This copies the board to a scratch folder, and for a region
removes every non-GND via inside it (as text), refills and runs DRC; if the connection_width count drops, a neck
is in that region, which is then split in four. Stops when the region is under 4 mm. Each DRC takes about a
minute, so expect 10-20 minutes; run it in the background.
    python tools/neck_bisect.py <scratch_dir>
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
CLI = r"C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
for f in ("MonolithDev.kicad_pcb", "MonolithDev.kicad_pro", "MonolithDev.kicad_dru", "fp-lib-table"):
    shutil.copy(os.path.join(ROOT, f), OUT)
if not os.path.isdir(os.path.join(OUT, "MonolithDev.pretty")):
    shutil.copytree(os.path.join(ROOT, "MonolithDev.pretty"), os.path.join(OUT, "MonolithDev.pretty"))
PCB = os.path.join(OUT, "MonolithDev.kicad_pcb")
PRO = os.path.join(OUT, "MonolithDev.kicad_pro")
base = open(PCB, encoding="utf-8").read()
pro = open(PRO, "rb").read()
VIA = re.compile(r"\n\t\(via\n(?:\t\t.*\n)*?\t\)")


def strip(text, rect):
    x0, y0, x1, y1 = rect
    def keep(m):
        blk = m.group(0)
        at = re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", blk)
        net = re.search(r'\(net "([^"]*)"\)', blk)
        x, y = float(at.group(1)), float(at.group(2))
        if net and net.group(1) != "GND" and x0 <= x < x1 and y0 <= y < y1:
            return ""
        return blk
    return VIA.sub(keep, text)


def necks(text):
    open(PCB, "w", encoding="utf-8", newline="\n").write(text)
    rpt = os.path.join(OUT, "drc.rpt")
    subprocess.run([CLI, "pcb", "drc", "--severity-all", "--refill-zones", "-o", rpt, PCB], capture_output=True)
    open(PRO, "wb").write(pro)
    return open(rpt, encoding="utf-8").read().count("[connection_width]")


full = necks(base)
print("baseline connection_width:", full, flush=True)
regions = [(50.0, 50.0, 246.0, 165.0)]
found = []
while regions:
    x0, y0, x1, y1 = regions.pop()
    if (x1 - x0) < 4.0 and (y1 - y0) < 4.0:
        found.append((x0, y0, x1, y1))
        print("NECK region", (x0, y0, x1, y1), flush=True)
        continue
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    quads = [(x0, y0, xm, ym), (xm, y0, x1, ym), (x0, ym, xm, y1), (xm, ym, x1, y1)]
    for q in quads:
        n = necks(strip(base, q))
        print(f"  region {tuple(round(v, 1) for v in q)} -> {n}", flush=True)
        if n < full:
            regions.append(q)
print("done; neck regions:", found)
