"""Finish-routing stage D (2026-10-17): a GND reference via next to every signal via that has none within 1 mm.

routing-discipline.md section 5: a signal that changes layers changes its reference plane (F/In2 reference In1,
In3/B reference In4); the return current needs a GND via within 1 mm of the signal via. For every non-GND via
without one, this drops a 0.45/0.3 GND via at the nearest free spot within 1 mm: 0.65 mm from any other hole
(hole-to-hole 0.25 plus the rings), ring 0.2 mm clear of other nets' copper on F/B/In2/In3 (pads, tracks, vias;
pours refill around it), 0.5 mm inside the board edge, outside rule areas. Re-runnable: the vias it adds are
listed in finish_d_gndvias.uuids and removed first. Prints how many vias got one and which could not.
Run from DevBoard/ with KiCad's python; restores MonolithDev.kicad_pro after saving.
"""
import math
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcb_text import strip_items  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PCB = os.path.join(ROOT, "MonolithDev.kicad_pcb")
PRO = os.path.join(ROOT, "MonolithDev.kicad_pro")
IDS = os.path.join(HERE, "finish_d_gndvias.uuids")
mm, MM = pcbnew.FromMM, pcbnew.ToMM
VIA_D, DRILL, REACH, HOLE_GAP, CU_GAP, EDGE = 0.45, 0.3, 1.0, 0.65, 0.2, 0.5
SIG_LAYERS = (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.B_Cu)
ONLY_BOTH_SIDES = "--both-sides-only" in sys.argv       # only vias whose tracks reference both planes

old = set(open(IDS).read().split()) if os.path.exists(IDS) else set()
print("removed old GND vias:", strip_items(PCB, old))
pro = open(PRO, "rb").read()
b = pcbnew.LoadBoard(PCB)
gnd = b.FindNet("GND")
gcode = gnd.GetNetCode()
bb = b.GetBoardEdgesBoundingBox()
X0, Y0, X1, Y1 = MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())

vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
segs = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
holes = []                     # (x, y, r_extra) every hole; r_extra = pad radius beyond a via's own
for v in vias:
    p = v.GetPosition()
    holes.append((MM(p.x), MM(p.y), 0.0))
pads = []                      # (net, layer-set flags, rect)
for f in b.GetFootprints():
    for q in f.Pads():
        bq = q.GetBoundingBox()
        r = (MM(bq.GetLeft()), MM(bq.GetTop()), MM(bq.GetRight()), MM(bq.GetBottom()))
        if q.HasHole():
            c = q.GetPosition()
            holes.append((MM(c.x), MM(c.y), max(r[2] - r[0], r[3] - r[1]) / 2 - VIA_D / 2))
        pads.append((q.GetNetCode(), q.HasHole(), [q.IsOnLayer(l) for l in SIG_LAYERS], r))
tracks = [(t.GetNetCode(), t.GetLayer(), (MM(t.GetStart().x), MM(t.GetStart().y)), (MM(t.GetEnd().x), MM(t.GetEnd().y)), MM(t.GetWidth()) / 2) for t in segs]
keep = []
for z in list(b.Zones()) + [z for f in b.GetFootprints() for z in f.Zones()]:
    if z.GetIsRuleArea() and z.GetDoNotAllowVias():
        bz = z.GetBoundingBox()
        keep.append((MM(bz.GetLeft()), MM(bz.GetTop()), MM(bz.GetRight()), MM(bz.GetBottom())))
gnd_vias = [(MM(v.GetPosition().x), MM(v.GetPosition().y)) for v in vias if v.GetNetCode() == gcode]
# bucket holes and tracks for speed
HB, TB = {}, {}
for h in holes:
    HB.setdefault((int(h[0]), int(h[1])), []).append(h)
for t in tracks:
    for ix in range(int(min(t[2][0], t[3][0])) - 1, int(max(t[2][0], t[3][0])) + 2):
        for iy in range(int(min(t[2][1], t[3][1])) - 1, int(max(t[2][1], t[3][1])) + 2):
            TB.setdefault((ix, iy), []).append(t)


def seg_pt(a, c, p):
    dx, dy = c[0] - a[0], c[1] - a[1]
    L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(a[0] + u * dx - p[0], a[1] + u * dy - p[1])


def free(x, y):
    if not (X0 + EDGE < x < X1 - EDGE and Y0 + EDGE < y < Y1 - EDGE):
        return False
    for k in keep:
        if k[0] - VIA_D / 2 < x < k[2] + VIA_D / 2 and k[1] - VIA_D / 2 < y < k[3] + VIA_D / 2:
            return False
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for hx, hy, re_ in HB.get((int(x) + i, int(y) + j), ()):
                if math.hypot(hx - x, hy - y) < HOLE_GAP + re_:
                    return False
    r = VIA_D / 2 + CU_GAP
    for n, lay, a, c, hw in TB.get((int(x), int(y)), ()):
        if n != gcode and lay in SIG_LAYERS and seg_pt(a, c, (x, y)) < r + hw:
            return False
    for n, hole, lays, pr in pads:
        if n == gcode:
            continue
        if hole or any(lays):
            if pr[0] - r < x < pr[2] + r and pr[1] - r < y < pr[3] + r:
                return False
    return True


def layer_sides(v):
    p = v.GetPosition()
    a = b_ = False
    for t in segs:
        if t.GetNetCode() == v.GetNetCode() and (t.GetStart() == p or t.GetEnd() == p):
            if t.GetLayer() in (pcbnew.F_Cu, pcbnew.In2_Cu):
                a = True
            elif t.GetLayer() in (pcbnew.In3_Cu, pcbnew.B_Cu):
                b_ = True
    return a and b_


added, done, nospot, skipped = [], 0, [], 0
for v in vias:
    if v.GetNetCode() == gcode:
        continue
    if ONLY_BOTH_SIDES and not layer_sides(v):
        skipped += 1
        continue
    p = v.GetPosition()
    x, y = MM(p.x), MM(p.y)
    if any(math.hypot(gx - x, gy - y) <= REACH for gx, gy in gnd_vias):
        continue
    best = None
    for rr in (0.65, 0.75, 0.85, 1.0):
        for k in range(16):
            a = 2 * math.pi * k / 16
            cx, cy = round(x + rr * math.cos(a), 3), round(y + rr * math.sin(a), 3)
            if free(cx, cy):
                best = (cx, cy)
                break
        if best:
            break
    if not best:
        nospot.append(f"{v.GetNetname()} ({x:.2f},{y:.2f})")
        continue
    nv = pcbnew.PCB_VIA(b)
    nv.SetPosition(pcbnew.VECTOR2I(mm(best[0]), mm(best[1])))
    nv.SetViaType(pcbnew.VIATYPE_THROUGH)
    nv.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    nv.SetWidth(mm(VIA_D))
    nv.SetDrill(mm(DRILL))
    nv.SetNet(gnd)
    b.Add(nv)
    added.append(nv.m_Uuid.AsString())
    gnd_vias.append(best)
    HB.setdefault((int(best[0]), int(best[1])), []).append((best[0], best[1], 0.0))
    done += 1
b.Save(PCB)
open(PRO, "wb").write(pro)
open(IDS, "w", newline="\n").write("\n".join(added) + "\n")
print(f"GND reference vias added: {done}; skipped (one-side vias): {skipped}; no spot: {len(nospot)}")
for s in nospot:
    print("   ", s)
