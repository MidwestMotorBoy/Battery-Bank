"""Finish-routing stage C (2026-10-17): put the parts the user parked off-board back on it.

33 test points, J103 (EV2400 header) and C452/C552 (TPD4S201 VPWR 1 uF) sit outside the outline. Each gets the
nearest free spot to its intended place: free = its courtyard clear of every other courtyard (0.2 mm), its F.Cu pads
0.2 mm clear of other nets' F.Cu copper (pads, tracks, vias), its holes 0.35 mm clear of every track on any copper
layer and 0.6 mm from other holes, everything 0.5 mm inside the board edge, and no part of it on the module antenna.
Pours refill around whatever lands in them. Prints what went where and what found no spot (left off-board).

Run from DevBoard/ with KiCad's python. Restores MonolithDev.kicad_pro after saving.
"""
import math
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PCB = os.path.join(ROOT, "MonolithDev.kicad_pcb")
PRO = os.path.join(ROOT, "MonolithDev.kicad_pro")
mm, MM = pcbnew.FromMM, pcbnew.ToMM
O = 50.0                                      # board origin (top-left corner) in absolute mm
DY = 36.0                                     # port 2 below port 1

# ref -> list of (x, y, rot) candidates in absolute mm, tried in order; each is also searched around (spiral)
WANT = {
    # port 1 probe field (2 x 4, 3.15 mm pitch) and the small pads, where rev A8 placed them
    "TP407": [(O + 171.75, O + 44.25, 0)], "TP408": [(O + 174.9, O + 44.25, 0)],
    "TP409": [(O + 178.05, O + 44.25, 0)], "TP410": [(O + 181.2, O + 44.25, 0)],
    "TP411": [(O + 171.75, O + 47.25, 0)], "TP404": [(O + 174.9, O + 47.25, 0)],
    "TP403": [(O + 178.05, O + 47.25, 0)], "TP414": [(O + 181.2, O + 47.25, 0)],
    "TP413": [(O + 143.5, O + 19.8, 0)], "TP401": [(O + 194.3, O + 22.6, 0)],
    "TP416": [(O + 178.4, O + 27.05, 0), (234.5, 72.0, 0), (231.0, 75.0, 0), (237.5, 72.0, 0), (240.0, 70.0, 0)],
    "TP415": [(O + 180.95, O + 27.05, 0)],
    "TP417": [(O + 187.5, O + 26.55, 0), (228.0, 77.0, 0), (222.0, 77.5, 0), (230.0, 66.0, 0), (218.5, 66.0, 0)],
    "TP420": [(O + 174.7, O + 14.0, 0)], "TP421": [(O + 170.3, O + 23.4, 0)],
    "TP501": [(O + 194.3, O + 22.6 + DY, 0)], "TP517": [(O + 187.5, O + 26.55 + DY, 0)],
    "TP520": [(O + 174.7, O + 14.0 + DY, 0)], "TP521": [(O + 170.3, O + 23.4 + DY, 0)],
    # TPD4S201 VPWR caps: at the chip
    "C452": [(234.3 + dx, 83.5 + dy, r) for dx, dy, r in ((-3.0, 0, 90), (3.0, 0, 90), (0, -3.2, 0), (0, 3.2, 0))],
    "C552": [(234.3 + dx, 119.5 + dy, r) for dx, dy, r in ((-3.0, 0, 90), (3.0, 0, 90), (0, -3.2, 0), (0, 3.2, 0))],
    # MCU probe field: below the MCU block, right of SW301
    "TP302": [(190.0, 66.0, 0)], "TP301": [(190.0, 69.2, 0)], "TP309": [(193.2, 69.2, 0)],
    "TP303": [(193.2, 66.0, 0), (199.2, 74.5, 0), (199.2, 68.0, 0), (184.0, 74.5, 0), (205.0, 74.5, 0), (210.0, 66.0, 0)],
    "TP304": [(196.4, 66.0, 0), (202.4, 74.5, 0), (202.4, 68.0, 0), (184.0, 77.7, 0), (208.0, 74.5, 0), (213.0, 66.0, 0)],
    # pack probe field: under the NTC headers
    "TP101": [(156.0, 131.0, 0)], "TP106": [(159.2, 131.0, 0)], "TP107": [(162.4, 131.0, 0)], "TP109": [(165.6, 131.0, 0)],
    # sleep-section GND loops along the bottom edge
    "TP203": [(184.0, 161.5, 0)], "TP208": [(188.0, 161.5, 0)], "TP209": [(192.0, 161.5, 0)],
    # EV2400 SMBus header: bottom edge, right of the sleep section (pins along the edge)
    "J103": [(186.0, 158.0, 90), (186.0, 158.0, 0), (160.0, 135.0, 90)],
}
EDGE, CRT_CLR, CU_CLR, HOLE_TRK, HOLE_HOLE = 0.5, 0.2, 0.2, 0.35, 0.6

pro = open(PRO, "rb").read()
b = pcbnew.LoadBoard(PCB)
bb = b.GetBoardEdgesBoundingBox()
X0, Y0, X1, Y1 = MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())
fps = {f.GetReference(): f for f in b.GetFootprints()}


def on_board(f):
    q = f.GetPosition()
    return X0 < MM(q.x) < X1 and Y0 < MM(q.y) < Y1


moving = {r for r in WANT if not on_board(fps[r])}          # parts already placed count as obstacles


def rect(bx, m=0.0):
    return (MM(bx.GetLeft()) - m, MM(bx.GetTop()) - m, MM(bx.GetRight()) + m, MM(bx.GetBottom()) + m)


def overlap(a, c):
    return a[0] < c[2] and c[0] < a[2] and a[1] < c[3] and c[1] < a[3]


def seg_rect(a, c, r):
    """0 if segment a-c touches rect r, else the distance."""
    best = 1e9
    for k in range(25):
        x, y = a[0] + (c[0] - a[0]) * k / 24, a[1] + (c[1] - a[1]) * k / 24
        if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
            return 0.0
        best = min(best, math.hypot(max(r[0] - x, 0, x - r[2]), max(r[1] - y, 0, y - r[3])))
    return best


# static obstacles (parts that stay)
courts = []
for ref, f in fps.items():
    if ref in moving:
        continue
    cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    courts.append((ref, rect(cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False, False), 0.0)))
pads_f = [(p.GetNetCode(), rect(p.GetBoundingBox())) for ref, f in fps.items() if ref not in moving
          for p in f.Pads() if p.IsOnLayer(pcbnew.F_Cu) or p.HasHole()]
holes = [(MM(p.GetPosition().x), MM(p.GetPosition().y), max(MM(p.GetBoundingBox().GetWidth()), MM(p.GetBoundingBox().GetHeight())) / 2)
         for ref, f in fps.items() if ref not in moving for p in f.Pads() if p.HasHole()]
segs = []       # (net, layer, (x0,y0), (x1,y1), halfwidth)
vias = []       # (net, x, y, r)
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        q = t.GetPosition()
        vias.append((t.GetNetCode(), MM(q.x), MM(q.y), MM(t.GetWidth(pcbnew.F_Cu)) / 2))
    else:
        s, e = t.GetStart(), t.GetEnd()
        segs.append((t.GetNetCode(), t.GetLayer(), (MM(s.x), MM(s.y)), (MM(e.x), MM(e.y)), MM(t.GetWidth()) / 2))
keepouts = []
for f in fps.values():
    for z in f.Zones():
        if z.GetIsRuleArea():
            keepouts.append(rect(z.GetBoundingBox()))
for z in b.Zones():
    if z.GetIsRuleArea():
        keepouts.append(rect(z.GetBoundingBox()))


def placed_ok(f, cands_courts):
    cy = f.GetCourtyard(pcbnew.F_CrtYd)
    cr = rect(cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False, False), 0.0)
    if cr[0] < X0 + EDGE or cr[1] < Y0 + EDGE or cr[2] > X1 - EDGE or cr[3] > Y1 - EDGE:
        return False
    for k in keepouts:
        if overlap(cr, k):
            return False
    for ref, c in courts + cands_courts:
        if overlap((cr[0] - CRT_CLR, cr[1] - CRT_CLR, cr[2] + CRT_CLR, cr[3] + CRT_CLR), c):
            return False
    for p in f.Pads():
        n = p.GetNetCode()
        pr = rect(p.GetBoundingBox())
        prc = (pr[0] - CU_CLR, pr[1] - CU_CLR, pr[2] + CU_CLR, pr[3] + CU_CLR)
        for n2, r2 in pads_f:
            if n2 != n and overlap(prc, r2):
                return False
        hole = p.HasHole()
        for n2, lay, a, c, hw in segs:
            if n2 == n:
                continue
            if hole:
                if seg_rect(a, c, (pr[0] - HOLE_TRK, pr[1] - HOLE_TRK, pr[2] + HOLE_TRK, pr[3] + HOLE_TRK)) < hw:
                    return False
            elif lay == pcbnew.F_Cu and seg_rect(a, c, prc) < hw:
                return False
        for n2, x, y, r in vias:
            if hole:
                if math.hypot(x - MM(p.GetPosition().x), y - MM(p.GetPosition().y)) < HOLE_HOLE + max(MM(p.GetBoundingBox().GetWidth()), MM(p.GetBoundingBox().GetHeight())) / 2:
                    return False
            elif n2 != n and prc[0] - r < x < prc[2] + r and prc[1] - r < y < prc[3] + r:
                return False
        if hole:
            for x, y, r in holes:
                if math.hypot(x - MM(p.GetPosition().x), y - MM(p.GetPosition().y)) < HOLE_HOLE + r:
                    return False
    return True


def spiral(x, y, rmax, step=0.5):
    yield x, y
    r = step
    while r <= rmax:
        n = max(8, int(2 * math.pi * r / step))
        for i in range(n):
            a = 2 * math.pi * i / n
            yield x + r * math.cos(a), y + r * math.sin(a)
        r += step


placed, failed = [], []
new_courts = []
for ref, cands in WANT.items():
    f = fps[ref]
    if ref not in moving:
        continue                                                    # already on the board (earlier run)
    ok = False
    for cx, cy, rot in cands:
        rmax = 10.0 if ref.startswith("J") else 6.0
        f.SetOrientationDegrees(rot)
        for x, y in spiral(cx, cy, rmax):
            f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            if placed_ok(f, new_courts):
                ok = True
                break
        if ok:
            cyp = f.GetCourtyard(pcbnew.F_CrtYd)
            new_courts.append((ref, rect(cyp.BBox() if cyp.OutlineCount() else f.GetBoundingBox(False, False), 0.0)))
            for p in f.Pads():
                if p.HasHole():
                    holes.append((MM(p.GetPosition().x), MM(p.GetPosition().y), max(MM(p.GetBoundingBox().GetWidth()), MM(p.GetBoundingBox().GetHeight())) / 2))
                pads_f.append((p.GetNetCode(), rect(p.GetBoundingBox())))
            placed.append(f"{ref:6} -> ({x:.2f}, {y:.2f}) rot {rot}  (asked ({cx:.1f}, {cy:.1f}), moved {math.hypot(x - cx, y - cy):.1f} mm)")
            break
    if not ok:
        failed.append(ref)
        f.SetPosition(pcbnew.VECTOR2I(mm(cands[0][0]), mm(cands[0][1] - 120)))   # park above the board

b.Save(PCB)
open(PRO, "wb").write(pro)
print("\n".join(placed))
print("no spot found:", failed)
