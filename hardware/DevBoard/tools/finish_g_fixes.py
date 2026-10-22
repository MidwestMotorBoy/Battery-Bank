"""Finish-routing stage G (2026-10-17): last scripted DRC fixes before the hand-routing hand-over.

- Two GND reference vias landed 0.5 mm from U501's GND pads 7 and 11, leaving 0.04-0.08 mm webs: removed (the
  exposed-pad vias serve as references there).
- The NRST In2 track ends 0.32 mm from its via centre (web 0.076 mm): end moved onto the centre.
- Three footprint silk items print over neighbouring pads (U301's pin-1 circle over C315, the U404/U504 polygon
  over R432/R532): removed from the board instances.
Run from DevBoard/ with KiCad's python; restores MonolithDev.kicad_pro after saving.
"""
import math
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PCB = os.path.join(ROOT, "MonolithDev.kicad_pcb")
PRO = os.path.join(ROOT, "MonolithDev.kicad_pro")
IDS = os.path.join(HERE, "finish_d_gndvias.uuids")
mm, MM = pcbnew.FromMM, pcbnew.ToMM
pro = open(PRO, "rb").read()
b = pcbnew.LoadBoard(PCB)
log, to_remove = [], []
vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
segs = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
ids = set(open(IDS).read().split()) if os.path.exists(IDS) else set()

for x, y in ((223.105, 117.343), (223.171, 115.345)):
    for v in vias:
        if v.GetNetname() == "GND" and math.hypot(MM(v.GetPosition().x) - x, MM(v.GetPosition().y) - y) < 0.02:
            to_remove.append(v)
            ids.discard(v.m_Uuid.AsString())
            log.append(f"removed GND via at ({x},{y}) (web to a U501 GND pad)")

c = pcbnew.VECTOR2I(mm(212.979), mm(52.07))
for s in segs:
    if s.GetNetname() == "/MCU and Sensors/NRST" and s.GetLayer() == pcbnew.In2_Cu:
        for which, p in (("start", s.GetStart()), ("end", s.GetEnd())):
            if math.hypot(MM(p.x) - 212.75, MM(p.y) - 51.85) < 0.05:
                (s.SetStart if which == "start" else s.SetEnd)(c)
                log.append("NRST In2 track end moved onto its via centre")

# footprint silk items that clip a neighbouring pad: every F.SilkS item whose box meets the pad's box (+0.1 mm)
silk_pads = {"U301": ("C315", "2"), "U404": ("R432", "2"), "U504": ("R532", "2")}
for ref, (pref, pnum) in silk_pads.items():
    f = b.FindFootprintByReference(ref)
    pad = [q for q in b.FindFootprintByReference(pref).Pads() if q.GetNumber() == pnum][0]
    pb = pad.GetBoundingBox()
    px0, py0, px1, py1 = MM(pb.GetLeft()) - 0.1, MM(pb.GetTop()) - 0.1, MM(pb.GetRight()) + 0.1, MM(pb.GetBottom()) + 0.1
    for g in list(f.GraphicalItems()):
        if g.GetLayer() == pcbnew.F_SilkS:
            bx = g.GetBoundingBox()
            if MM(bx.GetLeft()) < px1 and px0 < MM(bx.GetRight()) and MM(bx.GetTop()) < py1 and py0 < MM(bx.GetBottom()):
                f.Remove(g)
                log.append(f"removed {ref} silk item over {pref} pad {pnum}")

for item in to_remove:
    b.Remove(item)
b.Save(PCB)
open(PRO, "wb").write(pro)
open(IDS, "w", newline="\n").write("\n".join(sorted(ids)) + "\n")
print("\n".join(log))
