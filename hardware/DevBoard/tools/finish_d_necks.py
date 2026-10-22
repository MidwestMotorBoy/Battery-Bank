"""Finish-routing stage D (2026-10-17): widen the two GND-plane necks DRC reported (connection_width 0.128 / 0.120 mm).

neck_bisect.py located them at y ~ 119: the port 2 3V3 via (199.009, 118.872) against the TS via (198.22, 119.742),
and the port 2 LODRV1 via (210.058, 119.634) against its nearest non-GND hole. Each named via moves 0.15 mm
straight away from that neighbour (web 0.13 -> ~0.28 mm); the track ends on it follow. Run from DevBoard/ with
KiCad's python; restores MonolithDev.kicad_pro after saving.
"""
import math
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PCB = os.path.join(ROOT, "MonolithDev.kicad_pcb")
PRO = os.path.join(ROOT, "MonolithDev.kicad_pro")
mm, MM = pcbnew.FromMM, pcbnew.ToMM
MOVE = 0.15
TARGETS = [("3V3", 199.009, 118.872), ("/USB Port 2/LODRV1", 210.058, 119.634)]

pro = open(PRO, "rb").read()
b = pcbnew.LoadBoard(PCB)
gnd = b.FindNet("GND").GetNetCode()
vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
segs = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
holes = [(MM(v.GetPosition().x), MM(v.GetPosition().y), v) for v in vias if v.GetNetCode() != gnd]
for f in b.GetFootprints():
    for q in f.Pads():
        if q.HasHole() and q.GetNetCode() != gnd:
            holes.append((MM(q.GetPosition().x), MM(q.GetPosition().y), None))
for net, x, y in TARGETS:
    v = min((w for w in vias if w.GetNetname() == net), key=lambda w: math.hypot(MM(w.GetPosition().x) - x, MM(w.GetPosition().y) - y))
    p = v.GetPosition()
    if math.hypot(MM(p.x) - x, MM(p.y) - y) > 0.05:
        print("via not found at", net, x, y)
        continue
    others = [(hx, hy, math.hypot(hx - x, hy - y)) for hx, hy, w in holes if w is not v and math.hypot(hx - x, hy - y) > 0.01]
    hx, hy, d = min(others, key=lambda h: h[2])
    ux, uy = (x - hx) / d, (y - hy) / d
    nx, ny = round(x + ux * MOVE, 3), round(y + uy * MOVE, 3)
    newp = pcbnew.VECTOR2I(mm(nx), mm(ny))
    n = 0
    for s in segs:
        if s.GetNetCode() == v.GetNetCode():
            if s.GetStart() == p:
                s.SetStart(newp); n += 1
            if s.GetEnd() == p:
                s.SetEnd(newp); n += 1
    v.SetPosition(newp)
    print(f"{net} via ({x},{y}) -> ({nx},{ny}), away from hole at ({hx:.3f},{hy:.3f}) {d:.3f} mm; {n} track ends moved")
b.Save(PCB)
open(PRO, "wb").write(pro)
