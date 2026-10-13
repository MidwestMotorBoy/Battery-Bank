"""GND fanout: one via beside every SMD GND pad that is not already on GND copper, into the In1/In2 GND planes.

    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/fanout_gnd.py

Run after route_power.py and before tools/autoroute.py (Freerouting then sees those pins as connected through the
plane and only routes signals). Re-runnable: the UUIDs it adds are kept in tools/fanout_gnd.uuids and removed first.
For each pad it tries via spots just outside the pad (along the pad's long axis first, then the short axis, then
diagonals) and takes the first one that clears every other-net pad, track and via on every layer by 0.2 mm, together
with the short stub from the pad. Pads that sit in a GND zone already, pads that already have a GND via within 1 mm,
and Kelvin-sense pads (KEEP) are skipped; pads with no free spot are listed.
"""
import math
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "MonolithDev.kicad_pcb")
PRO = os.path.join(HERE, "..", "MonolithDev.kicad_pro")
IDS = os.path.join(HERE, "fanout_gnd.uuids")
KEEP = {("R108", "1"), ("R208", "1")}         # sense-resistor ends routed by hand (Kelvin); not fanned out
VIA_D, VIA_DRILL, STUB_W, CLR = 0.5, 0.3, 0.3, 0.2
mm, MM = pcbnew.FromMM, pcbnew.ToMM

pro_backup = open(PRO, encoding="utf-8").read()
board = pcbnew.LoadBoard(PCB)
old = set(open(IDS).read().split()) if os.path.exists(IDS) else set()
stale = [t for t in board.GetTracks() if t.m_Uuid.AsString() in old]
for t in stale:
    board.Remove(t)
gnd = board.FindNet("GND")
gcode = gnd.GetNetCode()

# obstacles (board mm): rectangles for pads, segments for tracks, circles for vias; per layer set
rects, segs, circs = [], [], []        # (net, layers, geometry)
for fp in board.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        lay = {l for l in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu) if p.IsOnLayer(l)}
        if p.HasHole():
            lay |= {pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu}
        rects.append((p.GetNetCode(), lay, (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))))
for t in board.GetTracks():
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        circs.append((t.GetNetCode(), "all", (MM(p.x), MM(p.y), MM(t.GetWidth(pcbnew.F_Cu)) / 2)))
    else:
        a, b = t.GetStart(), t.GetEnd()
        segs.append((t.GetNetCode(), {t.GetLayer()}, (MM(a.x), MM(a.y), MM(b.x), MM(b.y), MM(t.GetWidth()) / 2)))
gnd_zones_f = [z for z in board.Zones() if z.GetNetCode() == gcode and z.IsOnLayer(pcbnew.F_Cu) and not z.GetIsRuleArea()]
keepouts = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias()]
inside = pcbnew.SHAPE_POLY_SET()                     # board outline shrunk by the edge rule (0.25 mm) + via radius
board.GetBoardPolygonOutlines(inside, False)
inside.Deflate(mm(0.25 + VIA_D / 2 + 0.05), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, mm(0.01))


def seg_pt(ax, ay, bx, by, px, py):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(ax + t * dx - px, ay + t * dy - py)


def rect_pt(r, px, py):
    dx = max(r[0] - px, 0, px - r[2])
    dy = max(r[1] - py, 0, py - r[3])
    return math.hypot(dx, dy)


def seg_seg(a, b):
    return min(seg_pt(*a[:2], *a[2:4], *b[:2]), seg_pt(*a[:2], *a[2:4], *b[2:4]),
               seg_pt(*b[:2], *b[2:4], *a[:2]), seg_pt(*b[:2], *b[2:4], *a[2:4]))


def via_ok(x, y):
    r = VIA_D / 2 + CLR
    for n, lay, g in rects:
        if n != gcode and rect_pt(g, x, y) < r:
            return False
    for n, lay, g in segs:
        if n != gcode and seg_pt(*g[:4], x, y) < r + g[4]:
            return False
    for n, _, g in circs:
        if math.hypot(g[0] - x, g[1] - y) < (r + g[2] if n != gcode else VIA_D / 2 + g[2] + 0.25):
            return False
    pt = pcbnew.VECTOR2I(mm(x), mm(y))
    for z in keepouts:
        if z.Outline().Collide(pt, mm(VIA_D / 2 + 0.05)):
            return False
    return inside.Contains(pt)


def stub_ok(x0, y0, x1, y1, own):
    s = (x0, y0, x1, y1)
    for n, lay, g in rects:
        if n != gcode and pcbnew.F_Cu in lay:
            if min(rect_pt(g, x0, y0), rect_pt(g, x1, y1), rect_pt(g, (x0 + x1) / 2, (y0 + y1) / 2)) < CLR + STUB_W / 2:
                return False
    for n, lay, g in segs:
        if n != gcode and pcbnew.F_Cu in lay and seg_seg(s, g[:4]) < CLR + STUB_W / 2 + g[4]:
            return False
    return True


added, missing, n_skip = [], [], 0
for fp in board.GetFootprints():
    for p in fp.Pads():
        if p.GetNetCode() != gcode or p.HasHole() or not p.IsOnLayer(pcbnew.F_Cu):
            continue
        if (fp.GetReference(), p.GetNumber()) in KEEP:
            continue
        c = p.GetPosition()
        cx, cy = MM(c.x), MM(c.y)
        if any(z.HitTestFilledArea(pcbnew.F_Cu, c) for z in gnd_zones_f):
            n_skip += 1
            continue
        if any(n == gcode and math.hypot(g[0] - cx, g[1] - cy) < 1.0 for n, _, g in circs):
            n_skip += 1
            continue
        bb = p.GetBoundingBox()
        hw, hh = MM(bb.GetWidth()) / 2, MM(bb.GetHeight()) / 2
        off = VIA_D / 2 + 0.2
        long_x = hw >= hh
        cands = []
        for k in (0.0, 0.35, 0.7):
            ax = [(hw + off + k, 0), (-hw - off - k, 0)]
            ay = [(0, hh + off + k), (0, -hh - off - k)]
            cands += (ax + ay) if long_x else (ay + ax)
            cands += [(sx * (hw + off * 0.7 + k), sy * (hh + off * 0.7 + k)) for sx in (1, -1) for sy in (1, -1)]
        for dx, dy in cands:
            x, y = cx + dx, cy + dy
            ex = cx + max(-hw, min(hw, dx))                 # stub from the pad edge
            ey = cy + max(-hh, min(hh, dy))
            if via_ok(x, y) and stub_ok(ex, ey, x, y, p):
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                v.SetViaType(pcbnew.VIATYPE_THROUGH)
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL)); v.SetNet(gnd)
                board.Add(v)
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(mm(cx), mm(cy))); t.SetEnd(v.GetPosition())
                t.SetWidth(mm(STUB_W)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd)
                board.Add(t)
                added += [v.m_Uuid.AsString(), t.m_Uuid.AsString()]
                circs.append((gcode, "all", (x, y, VIA_D / 2)))
                segs.append((gcode, {pcbnew.F_Cu}, (cx, cy, x, y, STUB_W / 2)))
                break
        else:
            missing.append("%s.%s" % (fp.GetReference(), p.GetNumber()))

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(PCB)
open(PRO, "w", encoding="utf-8", newline="\n").write(pro_backup)
open(IDS, "w", newline="\n").write("\n".join(added) + "\n")
print("GND vias added: %d; already on GND copper: %d; no room: %d %s" % (len(added) // 2, n_skip, len(missing), missing))
