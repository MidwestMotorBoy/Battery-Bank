"""Finish-routing stage F (2026-10-17): clean up the router's leftovers DRC reported.

- 0.1 mm GND stubs the router left when start and goal were adjacent cells (track_dangling): removed.
- Tracks that end inside a same-net via ring but off its centre (connection_width wedges): end moved to the centre.
- A segment under 0.15 mm joined at an acute angle to a longer one (the LIQ_PU snap stubs): the tiny segment goes and
  the long one takes over its far end.
- The port 1 PP5V track along the pour's edge (web 0.09 mm): widened to 0.4 mm.
Run from DevBoard/ with KiCad's python; restores MonolithDev.kicad_pro after saving.
"""
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
gnd = b.FindNet("GND").GetNetCode()
vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
segs = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
log, to_remove = [], []


def ends(s):
    return s.GetStart(), s.GetEnd()


def touching(p, net, skip):
    """Other same-net items at point p: pads, vias, segment ends."""
    n = 0
    for v in vias:
        if v.GetNetCode() == net and v.GetPosition() == p:
            n += 1
    for s in segs:
        if s is not skip and s.GetNetCode() == net and p in ends(s):
            n += 1
    for f in b.GetFootprints():
        for q in f.Pads():
            if q.GetNetCode() == net and q.HitTest(p):
                n += 1
    return n


# 1. tiny GND stubs
for s in segs:
    if s.GetNetCode() == gnd and MM(s.GetLength()) <= 0.15 and s.GetLayer() == pcbnew.F_Cu:
        a, c = ends(s)
        if touching(a, gnd, s) == 0 or touching(c, gnd, s) == 0:
            to_remove.append(s)
            log.append(f"removed {MM(s.GetLength()):.2f} mm GND stub at ({MM(a.x):.2f},{MM(a.y):.2f})")

# 2. track ends inside a via ring but off centre -> centre, only at the two vias DRC named (moving every such end
#    on the board shifted hundreds of hand-routed track ends and broke clearances elsewhere)
WEDGE_VIAS = [(220.853, 82.872), (212.979, 52.07), (228.854, 68.394), (228.854, 104.394)]
for s in segs:
    if s in to_remove:
        continue
    for v in vias:
        if v.GetNetCode() != s.GetNetCode():
            continue
        if not any(math.hypot(MM(v.GetPosition().x) - wx, MM(v.GetPosition().y) - wy) < 0.02 for wx, wy in WEDGE_VIAS):
            continue
        c = v.GetPosition()
        r = MM(v.GetWidth(pcbnew.F_Cu)) / 2
        for which, p in (("start", s.GetStart()), ("end", s.GetEnd())):
            d = math.hypot(MM(p.x) - MM(c.x), MM(p.y) - MM(c.y))
            if 0.01 < d < r + 0.05:
                (s.SetStart if which == "start" else s.SetEnd)(c)
                log.append(f"{s.GetNetname()} {s.GetLayerName()[:4]} {which} ({MM(p.x):.3f},{MM(p.y):.3f}) -> via centre ({MM(c.x):.3f},{MM(c.y):.3f}) ({d:.3f} mm)")

# 3. tiny non-GND segments at an acute joint with a longer one: merge
for s in segs:
    if s in to_remove or not s.GetNetname().endswith("/LIQ_PU") or MM(s.GetLength()) >= 0.15:
        continue
    a, c = ends(s)
    for far, near in ((a, c), (c, a)):
        longer = [t for t in segs if t is not s and t not in to_remove and t.GetNetCode() == s.GetNetCode()
                  and t.GetLayer() == s.GetLayer() and near in ends(t) and MM(t.GetLength()) > 0.5]
        if longer and touching(far, s.GetNetCode(), s) > 0:
            t = longer[0]
            (t.SetStart if t.GetStart() == near else t.SetEnd)(far)
            to_remove.append(s)
            log.append(f"{s.GetNetname()}: merged {MM(s.GetLength()):.3f} mm segment at ({MM(near.x):.2f},{MM(near.y):.2f}) into its neighbour")
            break

# 4. PP5V track along the pour edge
for s in segs:
    if s.GetNetname() == "/USB Port 1/PP5V" and s.GetLayer() == pcbnew.F_Cu and abs(MM(s.GetLength()) - 2.9) < 0.05 \
            and abs(MM(s.GetStart().y) - 71.65) < 0.1:
        s.SetWidth(mm(0.3))
        log.append("PP5V edge track widened to 0.3 mm (0.4 came within 0.146 mm of C407's GND pad)")

for s in to_remove:
    b.Remove(s)
b.Save(PCB)
open(PRO, "wb").write(pro)
print("\n".join(log) or "nothing to do")
