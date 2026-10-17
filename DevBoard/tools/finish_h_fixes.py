"""Finish-routing stage H (2026-10-17): repairs after the user's hand-routing round.

- IRQ_N: the router's In2 vertical at x = 158.95 now runs through the user's GND via row at x = 159.131 (RS101's
  GND pad, four shorts): moved to x = 158.45 with a 0.5 mm jog to its via.
- Tracks on the In4 GND plane (SBU_FLT x2, SCL): each net's In4 path is re-layered as a whole to In2, In3 or
  B.Cu, the first layer where every segment is clear of other copper (segment intersection and clearance tested);
  a path with no clear layer stays and is reported for hand routing.
- Wedges: the LIQ_PU tracks end on their via's ring off centre (end -> centre).
- Dangling leftovers: short stubs with a free end (CC1, VBUS, SDA) and vias connected on F.Cu only inside a pad of
  an already-connected net are removed, then any track end left touching nothing is trimmed (two passes).
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
pads = [(q.GetNetCode(), q, f.GetReference()) for f in b.GetFootprints() for q in f.Pads()]
zones = [z for z in b.Zones() if not z.GetIsRuleArea()]
log, to_remove, to_add = [], [], []


def P(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def pt(v):
    return MM(v.x), MM(v.y)


def seg_pt(a, c, p):
    dx, dy = c[0] - a[0], c[1] - a[1]
    L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(a[0] + u * dx - p[0], a[1] + u * dy - p[1])


def cross(o, a, c):
    return (a[0] - o[0]) * (c[1] - o[1]) - (a[1] - o[1]) * (c[0] - o[0])


def seg_seg(a, c, d, e):
    """Distance between segments a-c and d-e (0 when they intersect)."""
    d1, d2 = cross(d, e, a), cross(d, e, c)
    d3, d4 = cross(a, c, d), cross(a, c, e)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and d1 != 0 and d2 != 0 and d3 != 0 and d4 != 0:
        return 0.0
    return min(seg_pt(a, c, d), seg_pt(a, c, e), seg_pt(d, e, a), seg_pt(d, e, c))


def clear_on(layer, a, c, net, hw, skip, clr=0.15):
    """Segment a-c (half width hw) on layer: clear of other nets' tracks, vias, pads and zone fills."""
    for s in segs:
        if s in to_remove or s in skip or s.GetNetCode() == net or s.GetLayer() != layer:
            continue
        if seg_seg(a, c, pt(s.GetStart()), pt(s.GetEnd())) < hw + MM(s.GetWidth()) / 2 + clr:
            return False
    for v in vias:
        if v in to_remove or v.GetNetCode() == net:
            continue
        if seg_pt(a, c, pt(v.GetPosition())) < hw + MM(v.GetWidth(pcbnew.F_Cu)) / 2 + clr:
            return False
    for n, q, ref in pads:
        if n == net or not (q.HasHole() or q.IsOnLayer(layer)):
            continue
        bq = q.GetBoundingBox()
        r = (MM(bq.GetLeft()) - hw - clr, MM(bq.GetTop()) - hw - clr, MM(bq.GetRight()) + hw + clr, MM(bq.GetBottom()) + hw + clr)
        for k in range(41):
            x, y = a[0] + (c[0] - a[0]) * k / 40, a[1] + (c[1] - a[1]) * k / 40
            if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
                return False
    for z in zones:
        if z.GetNetCode() == net or not z.IsOnLayer(layer):
            continue
        bz = z.GetBoundingBox()
        if MM(bz.GetLeft()) - 1 < max(a[0], c[0]) and MM(bz.GetRight()) + 1 > min(a[0], c[0]) and \
                MM(bz.GetTop()) - 1 < max(a[1], c[1]) and MM(bz.GetBottom()) + 1 > min(a[1], c[1]):
            fill = z.GetFilledPolysList(layer)
            for k in range(41):
                x, y = a[0] + (c[0] - a[0]) * k / 40, a[1] + (c[1] - a[1]) * k / 40
                if fill.Collide(P(x, y), mm(hw + clr)):
                    return False
    return True


# ---- 1. IRQ_N In2 vertical away from the GND via row
irq = b.FindNet("IRQ_N")
for s in segs:
    if s.GetNetname() == "IRQ_N" and s.GetLayer() == pcbnew.In2_Cu and abs(MM(s.GetStart().x) - 158.95) < 0.01 \
            and abs(MM(s.GetEnd().x) - 158.95) < 0.01:
        ys = sorted((MM(s.GetStart().y), MM(s.GetEnd().y)))
        s.SetStart(P(158.45, ys[0]))
        s.SetEnd(P(158.45, ys[1]))
        jog = pcbnew.PCB_TRACK(b)
        jog.SetStart(P(158.45, ys[1])); jog.SetEnd(P(158.95, ys[1]))
        jog.SetWidth(s.GetWidth()); jog.SetLayer(pcbnew.In2_Cu); jog.SetNet(irq)
        to_add.append(jog)
        log.append(f"IRQ_N In2 vertical moved to x 158.45 (y {ys[0]}-{ys[1]}), 0.5 mm jog to its via")

# ---- 2. tracks on the In4 plane: whole path per net
by_net = {}
for s in segs:
    if s.GetLayer() == pcbnew.In4_Cu:
        by_net.setdefault(s.GetNetCode(), []).append(s)
for net, group in by_net.items():
    moved = False
    for layer, name in ((pcbnew.In2_Cu, "In2"), (pcbnew.In3_Cu, "In3"), (pcbnew.B_Cu, "B.Cu")):
        if all(clear_on(layer, pt(s.GetStart()), pt(s.GetEnd()), net, MM(s.GetWidth()) / 2, group) for s in group):
            for s in group:
                s.SetLayer(layer)
            log.append(f"{group[0].GetNetname()}: {len(group)} In4 segments -> {name}")
            moved = True
            break
    if not moved:
        log.append(f"NOT MOVED: {group[0].GetNetname()} {len(group)} In4 segments near "
                   f"({MM(group[0].GetStart().x):.1f},{MM(group[0].GetStart().y):.1f}): no clear layer, hand-route")

# ---- 3. LIQ_PU wedges
for vx, vy in ((228.854, 68.394), (228.854, 104.394)):
    for s in segs:
        if s.GetNetname().endswith("/LIQ_PU") and s.GetLayer() == pcbnew.F_Cu:
            for which, p in (("start", s.GetStart()), ("end", s.GetEnd())):
                d = math.hypot(MM(p.x) - vx, MM(p.y) - vy)
                if 0.01 < d < 0.5:
                    (s.SetStart if which == "start" else s.SetEnd)(P(vx, vy))
                    log.append(f"LIQ_PU {which} -> via centre ({vx},{vy}) ({d:.3f} mm)")

# ---- 4. dangling leftovers
STUBS = [("/USB Port 1/CC1", pcbnew.F_Cu, 1.725), ("/USB Port 1/VBUS", pcbnew.B_Cu, 0.775), ("SDA", pcbnew.In2_Cu, 0.2694)]
for net, layer, L in STUBS:
    for s in segs:
        if s.GetNetname() == net and s.GetLayer() == layer and abs(MM(s.GetLength()) - L) < 0.02 and s not in to_remove:
            to_remove.append(s)
            log.append(f"removed dangling {net} stub {L} mm")
            break
DEAD_VIAS = [(164.842, 59.944), (199.5567, 54.4377), (179.578, 53.34), (169.672, 90.424), (162.0, 111.5),
             (158.066, 92.534), (157.861, 85.09), (203.1655, 57.712), (194.67, 96.342), (160.909, 62.738),
             (220.853, 83.888), (201.676, 96.342)]
for x, y in DEAD_VIAS:
    for v in vias:
        if math.hypot(MM(v.GetPosition().x) - x, MM(v.GetPosition().y) - y) < 0.02:
            to_remove.append(v)
            log.append(f"removed dangling via {v.GetNetname()} ({x},{y})")


def touches(p, net, skip):
    for v in vias:
        if v not in to_remove and v.GetNetCode() == net and math.hypot(*(MM(a) - MM(c) for a, c in zip((v.GetPosition().x, v.GetPosition().y), (p.x, p.y)))) < 0.05:
            return True
    for s in segs:
        if s is not skip and s not in to_remove and s.GetNetCode() == net and s.GetLayer() == skip.GetLayer() and (s.GetStart() == p or s.GetEnd() == p):
            return True
    for n, q, ref in pads:
        if n == net and (q.HasHole() or q.IsOnLayer(skip.GetLayer())) and q.HitTest(p):
            return True
    for z in zones:
        if z.GetNetCode() == net and z.IsOnLayer(skip.GetLayer()) and z.GetFilledPolysList(skip.GetLayer()).Collide(p, 0):
            return True
    return False


for _ in range(2):            # trim stubs left by the removed vias (and stubs of those stubs)
    for s in segs:
        if s in to_remove or s.GetNetCode() == gnd or MM(s.GetLength()) > 2.0:
            continue
        if not touches(s.GetStart(), s.GetNetCode(), s) or not touches(s.GetEnd(), s.GetNetCode(), s):
            to_remove.append(s)
            log.append(f"trimmed {s.GetNetname()} {s.GetLayerName()[:4]} stub {MM(s.GetLength()):.2f} mm at ({MM(s.GetStart().x):.2f},{MM(s.GetStart().y):.2f})")

for t in to_add:
    b.Add(t)
for item in to_remove:
    b.Remove(item)
b.Save(PCB)
open(PRO, "wb").write(pro)
print("\n".join(log))
