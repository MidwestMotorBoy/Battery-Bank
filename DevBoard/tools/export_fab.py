"""Fab outputs for JLCPCB: gerbers + drill (zipped), assembly BOM and pick-and-place (CPL) CSVs, into DevBoard/fab/.

Steps: refill zones and save the board (JLC: plot with fresh fills; MonolithDev.kicad_pro is restored after the
save), plot gerbers with JLC's recommended KiCad settings (Protel extensions, soldermask subtracted from silk, no X2,
no netlist attributes), Excellon drill files (mm, decimal, PTH and NPTH separate, absolute origin, Gerber X2 map),
zip them, then write:
  fab/MonolithDev-bom.csv   Comment, Designator, Footprint, LCSC Part #   (JLC-placed parts only)
  fab/MonolithDev-cpl.csv   Designator, Mid X, Mid Y, Layer, Rotation      (same parts)
  fab/MonolithDev-hand-fit.csv  parts left out of the JLC files: DNP, hand-fit (exclude from position files) or no LCSC number
Run from anywhere with KiCad's python: "C:/Program Files/KiCad/10.0/bin/python.exe" -I tools/export_fab.py
"""
import csv
import os
import shutil
import subprocess
import zipfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PCB = os.path.join(ROOT, "MonolithDev.kicad_pcb")
PRO = os.path.join(ROOT, "MonolithDev.kicad_pro")
FAB = os.path.join(ROOT, "fab")
GERB = os.path.join(FAB, "gerbers")
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
MM = pcbnew.ToMM
LAYERS = "F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"

# 1. fresh zone fills, saved
pro = open(PRO, "rb").read()
b = pcbnew.LoadBoard(PCB)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(PCB)
open(PRO, "wb").write(pro)

# 2. gerbers + drill
os.makedirs(GERB, exist_ok=True)
for name in os.listdir(GERB):
    os.remove(os.path.join(GERB, name))
subprocess.run([CLI, "pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask", "--no-x2", "--no-netlist",
                "--precision", "6", "-o", GERB + os.sep, PCB], check=True)
subprocess.run([CLI, "pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
                "--excellon-zeros-format", "decimal", "--excellon-separate-th", "--drill-origin", "absolute",
                "--generate-map", "--map-format", "gerberx2", "-o", GERB + os.sep, PCB], check=True)
open(PRO, "wb").write(pro)                        # kicad-cli rewrites the project file too
zpath = os.path.join(FAB, "MonolithDev-gerbers.zip")
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for name in sorted(os.listdir(GERB)):
        z.write(os.path.join(GERB, name), name)
print("gerbers:", sorted(os.listdir(GERB)))

# 3. BOM / CPL
rows_bom, rows_cpl, left_out = {}, [], []
for f in sorted(b.GetFootprints(), key=lambda f: (f.GetReference().rstrip("0123456789"), int("".join(c for c in f.GetReference() if c.isdigit()) or 0))):
    ref = f.GetReference()
    attr = f.GetAttributes()
    if attr & pcbnew.FP_EXCLUDE_FROM_BOM or attr & pcbnew.FP_BOARD_ONLY:
        continue
    value = str(f.GetValue())
    fpname = str(f.GetFPID().GetLibItemName())
    lcsc = str(f.GetFieldText("LCSC")).strip() if f.HasField("LCSC") else ""
    why = None
    if attr & pcbnew.FP_DNP:
        why = "DNP"
    elif attr & pcbnew.FP_EXCLUDE_FROM_POS_FILES:
        why = "hand-fit (excluded from position files)"
    elif not lcsc.startswith("C"):
        why = "no LCSC number"
    if why:
        left_out.append([ref, value, fpname, lcsc, why])
        continue
    rows_bom.setdefault((value, fpname, lcsc), []).append(ref)
    p = f.GetPosition()
    rows_cpl.append([ref, f"{MM(p.x):.4f}", f"{-MM(p.y):.4f}", "Bottom" if f.IsFlipped() else "Top", f"{f.GetOrientationDegrees():.1f}"])

with open(os.path.join(FAB, "MonolithDev-bom.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for (value, fpname, lcsc), refs in rows_bom.items():
        w.writerow([value, ",".join(refs), fpname, lcsc])
with open(os.path.join(FAB, "MonolithDev-cpl.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    w.writerows(rows_cpl)
with open(os.path.join(FAB, "MonolithDev-hand-fit.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["Designator", "Value", "Footprint", "LCSC", "Why not in the JLC files"])
    w.writerows(left_out)
print(f"BOM lines {len(rows_bom)}, placed parts {len(rows_cpl)}, left out {len(left_out)}")
for r in left_out:
    print("  ", *r)
