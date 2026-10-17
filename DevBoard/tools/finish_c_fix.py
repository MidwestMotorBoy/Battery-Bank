"""Finish-routing stage C, small fixes (2026-10-17): the R123 / U102-VDD clearance (move the track's first vertex
0.2 mm right, away from R123 pad 2; it still passes between C116's pads with 0.17 mm to the CELL_N pad) and the last
near-duplicate GND via pair at (230.632, 82) / (231.0, 82). Run from DevBoard/ with KiCad's python."""
import math
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PCB = os.path.join(ROOT, "MonolithDev.kicad_pcb")
PRO = os.path.join(ROOT, "MonolithDev.kicad_pro")
mm, MM = pcbnew.FromMM, pcbnew.ToMM
pro = open(PRO, "rb").read()
b = pcbnew.LoadBoard(PCB)
old = pcbnew.VECTOR2I(mm(156.464), mm(87.122))
new = pcbnew.VECTOR2I(mm(156.67), mm(87.122))
n = 0
segs = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
for t in segs:
    if t.GetNetname() == "Net-(U102-VDD)":
        if t.GetStart() == old:
            t.SetStart(new); n += 1
        if t.GetEnd() == old:
            t.SetEnd(new); n += 1
print("R123: moved", n, "segment ends")
pair = [v for v in vias if v.GetNetname() == "GND" and abs(MM(v.GetPosition().y) - 82.0) < 0.01
        and 230.5 < MM(v.GetPosition().x) < 231.1]
if len(pair) == 2:
    def att(v):
        return sum(1 for s in segs if s.GetNetname() == "GND" and (s.GetStart() == v.GetPosition() or s.GetEnd() == v.GetPosition()))
    loser = min(pair, key=att)
    print("GND via pair: removing", MM(loser.GetPosition().x), MM(loser.GetPosition().y), "attached", att(loser))
    b.Remove(loser)
b.Save(PCB)
open(PRO, "wb").write(pro)
