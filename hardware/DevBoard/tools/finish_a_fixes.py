"""Finish-routing stage A (2026-10-17): mechanical DRC fixes on the user's routed board.

- Edge.Cuts: drop the stray duplicate right-edge segment (246, 51.1)-(246, 76.9) that broke the outline.
- Vias: 0.6/0.3 -> 0.45/0.3 (the board standard); then drop near-duplicate vias (hole-to-hole < 0.25 mm, same net),
  keeping the one with more tracks attached.
- Zones: delete the exact duplicates (same net, layers, priority, outline) and port 1's B.Cu-only PP5V copy; PP5V
  pours connect pads solid (C507's thermal relief was starved); CELL1-3 pours drop islands.
- Planes: delete the SDA/SCL segments on In4 (re-routed later) and the CELL_N island on In4 (the gauge VSS is routed
  as a net; pack current never flows in it).
- Pack negative: a 4 mm wide F.Cu CELL_N pour from BT101 pad 2 into RS101 pad 1 (was a 0.2 mm track).
Run from DevBoard/ with KiCad's python. Restores MonolithDev.kicad_pro after saving.
KiCad-python note: every read happens before the first Remove(); a removed item poisons later board reads.
"""
import collections
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
log = []
to_remove = []

# ---- read everything first
vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
segs = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
zones = [z for z in b.Zones() if not z.GetIsRuleArea()]
drawings = list(b.GetDrawings())

# outline
for d in drawings:
    if d.GetLayer() == pcbnew.Edge_Cuts and d.GetClass() == "PCB_SHAPE":
        s, e = d.GetStart(), d.GetEnd()
        if (round(MM(s.x), 2), round(MM(s.y), 2), round(MM(e.x), 2), round(MM(e.y), 2)) == (246.0, 51.1, 246.0, 76.9):
            to_remove.append(d)
            log.append("outline: removed stray segment (246,51.1)-(246,76.9)")

# vias: resize, then near-duplicates
n = 0
for v in vias:
    if abs(MM(v.GetWidth(pcbnew.F_Cu)) - 0.6) < 0.01 and abs(MM(v.GetDrillValue()) - 0.3) < 0.01:
        v.SetWidth(mm(0.45))
        n += 1
log.append(f"vias: {n} resized 0.6 -> 0.45")


def attached(v):
    p = v.GetPosition()
    return sum(1 for s in segs if s.GetNetname() == v.GetNetname() and (s.GetStart() == p or s.GetEnd() == p))


dead = set()
for i, v in enumerate(vias):
    if id(v) in dead:
        continue
    for w in vias[i + 1:]:
        if id(w) in dead or w.GetNetname() != v.GetNetname():
            continue
        d = math.hypot(MM(v.GetPosition().x) - MM(w.GetPosition().x), MM(v.GetPosition().y) - MM(w.GetPosition().y))
        if d < 0.25:
            loser = w if attached(w) <= attached(v) else v
            dead.add(id(loser))
            to_remove.append(loser)
            log.append(f"vias: removed near-duplicate {loser.GetNetname()} at "
                       f"({MM(loser.GetPosition().x):.3f},{MM(loser.GetPosition().y):.3f}) ({d:.3f} mm from its twin)")
            if loser is v:
                break

# zones
groups = collections.defaultdict(list)
for z in zones:
    o = z.Outline().Outline(0)
    pts = tuple((o.CPoint(i).x, o.CPoint(i).y) for i in range(o.PointCount()))
    groups[(z.GetNetname(), tuple(z.GetLayerSet().Seq()), z.GetAssignedPriority(), pts)].append(z)
dup = set()
for key, zs in groups.items():
    for z in zs[1:]:
        to_remove.append(z)
        dup.add(id(z))
        log.append(f"zones: removed duplicate {key[0]} outline ({len(key[3])} pts)")
for z in zones:
    if id(z) in dup:
        continue
    layers = tuple(z.GetLayerSet().Seq())
    net = z.GetNetname()
    if net == "/USB Port 1/PP5V" and layers == (pcbnew.B_Cu,):
        to_remove.append(z)
        log.append("zones: removed port 1 PP5V B.Cu-only copy (the F+B pour covers it)")
    elif net == "CELL_N" and layers == (pcbnew.In4_Cu,):
        to_remove.append(z)
        log.append("zones: removed the CELL_N island on the In4 GND plane")
    elif net.endswith("/PP5V") and pcbnew.F_Cu in layers:
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        log.append(f"zones: {net} pour pads solid")
    elif net.startswith("/Cells and Gauge/CELL") and net[-1] in "123":
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)

# plane-layer tracks
n = 0
for t in segs:
    if t.GetLayer() == pcbnew.In4_Cu:
        to_remove.append(t)
        n += 1
log.append(f"planes: removed {n} track segments from In4")

# R123 / U102-VDD clearance: geometry for the follow-up
for t in segs:
    if t.GetNetname() == "Net-(U102-VDD)":
        s, e = t.GetStart(), t.GetEnd()
        log.append(f"  U102-VDD {t.GetLayerName()} ({MM(s.x):.3f},{MM(s.y):.3f})-({MM(e.x):.3f},{MM(e.y):.3f}) w {MM(t.GetWidth())}")

# ---- add the pack-negative pour, then remove, then save
cell_n = b.FindNet("CELL_N")
z = pcbnew.ZONE(b)
z.SetNet(cell_n)
z.SetLayer(pcbnew.F_Cu)
z.SetAssignedPriority(20)
z.SetZoneName("CELL_N_shunt")
z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
z.SetLocalClearance(mm(0.25))
z.SetMinThickness(mm(0.25))
poly = pcbnew.SHAPE_POLY_SET()
poly.NewOutline()
for x, y in ((150.0, 62.9), (153.6, 62.9), (153.6, 67.1), (150.0, 67.1)):
    poly.Append(mm(x), mm(y))
z.SetOutline(poly)
b.Add(z)
log.append("pack negative: added CELL_N F.Cu pour (150-153.6 x 62.9-67.1) BT101 pad 2 -> RS101 pad 1")

for item in to_remove:
    b.Remove(item)
b.Save(PCB)
open(PRO, "wb").write(pro)
print("\n".join(log))
print("removed", len(to_remove), "items")
