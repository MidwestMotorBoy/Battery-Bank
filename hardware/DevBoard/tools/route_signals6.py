"""Signal router (6-layer, Manhattan pair): A* maze routing on a 0.1 mm grid for the connections DRC still reports
as missing. Generated from route_signals.py by make_router6.py; see routing-discipline.md.
Layers F.Cu (cost 1.6), In2 (1.0, vertical moves only), In3 (1.0, horizontal moves only), B.Cu (1.8); In1/In4
are the GND planes and are never used. A GND reference via next to each In2/In3 or B via is added afterwards by
finish_d_gndvias.py.

    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/route_signals.py <drc_report.rpt> [max_edges]

Why not Freerouting: on this board it stalled at a third unrouted, broke DRC and ran signals across the power stages
(README item 32). This router is deliberately simple and conservative:
  - Obstacles: every other net's copper (pads, tracks, vias, filled zones) grown by clearance + half the track width
    (plus 0.05 mm for the grid). Copper of the HighCurrent class is grown by 0.25 mm clearance (board rule).
  - Layers: F.Cu (cost 1.0), In2 (1.4), B.Cu (1.8); In1 is the solid GND plane and is never used. Vias cost 2.5 mm
    of track and need room on every layer. Bends cost a little, so routes come out straight and tidy.
  - Every route ends on the other item of the missing connection DRC reported, or (GND) on any GND copper.
  - Nets in HAND are skipped (sense pairs, antenna feed): they are routed deliberately elsewhere.
  - Re-runnable: what it adds is listed in tools/route_signals.uuids and removed first.
Edges are routed shortest first; each new track becomes an obstacle for the rest. Unroutable edges are listed.
"""
import heapq
import math
import os
import re
import sys

import numpy as np
import pcbnew
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # runs under python -I too
from pcb_text import strip_items  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "MonolithDev.kicad_pcb")
PRO = os.path.join(HERE, "..", "MonolithDev.kicad_pro")
IDS = os.path.join(HERE, "route_signals6.uuids")
RPT = sys.argv[1]
MAX_EDGES = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 6
if len(sys.argv) > 3:
    IDS = sys.argv[3]
RELAXED = "--relaxed" in sys.argv

G = 0.1                                   # grid, mm
W, CLR, TOL = 0.2, 0.15, 0.08             # track width, clearance, raster tolerance (discs rasterise a cell small)
VIA_D, VIA_DRILL = 0.45, 0.3
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.B_Cu]
LCOST = [1.6, 1.0, 1.0, 1.8]
VERT, HORZ = 1, 2                         # Manhattan pair: In2 vertical only, In3 horizontal only
VIA_COST = 40.0                           # in grid steps
VIA_GAP_PATH = 8                          # cells between two vias of one route (no via-hop-via-back)
VIA_MIN_SAME, VIA_MIN_OTHER = 0.9, 1.1    # mm to existing via centres (hole-to-hole; other nets: plane antipads)
BEND = 0.4
HAND = re.compile(r"(MEAS_[PN]|ACP_F|ACN_F|SRP_F|SRN_F|/Cells and Gauge/SR[PN]$|ANT_|U301-ANT)")

mm = pcbnew.FromMM
MM = pcbnew.ToMM
pro_backup = open(PRO, encoding="utf-8").read()


old = set(open(IDS).read().split()) if os.path.exists(IDS) else set()
print("removed old router items:", strip_items(PCB, old))
board = pcbnew.LoadBoard(PCB)
bb = board.GetBoardEdgesBoundingBox()
X0, Y0 = MM(bb.GetLeft()), MM(bb.GetTop())
NX, NY = int(MM(bb.GetWidth()) / G) + 2, int(MM(bb.GetHeight()) / G) + 2
EMPTY, MULTI = -1, -2
grid = [np.full((NY, NX), EMPTY, dtype=np.int32) for _ in LAYERS]      # copper grown by clearance (obstacles)
copper = [np.full((NY, NX), EMPTY, dtype=np.int32) for _ in LAYERS]    # true copper (route ends)
DEST = [grid]
HC = re.compile(r"(^PACK_P$|^CELL_N$|/CELL\d$|/CELL_P|/FET_MID|/VBAT_SYS|/PPHV|/VBUS$|/SW[12]$|/AC_SNS_N|/BAT_SNS_P)")
hc = {board.FindNet(str(nm)).GetNetCode() for nm in board.GetNetsByName().keys() if HC.search(str(nm))}


def cell(x, y):
    return int(round((x - X0) / G)), int(round((y - Y0) / G))


def mark(li, net, draw_fn, x0, y0, x1, y1):
    """Rasterise one shape (drawn by draw_fn on a local PIL canvas) into layer li as net."""
    cx0, cy0 = cell(x0, y0)
    cx1, cy1 = cell(x1, y1)
    cx0, cy0, cx1, cy1 = max(cx0 - 1, 0), max(cy0 - 1, 0), min(cx1 + 2, NX), min(cy1 + 2, NY)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    im = Image.new("1", (cx1 - cx0, cy1 - cy0), 0)
    draw_fn(ImageDraw.Draw(im), lambda x, y: ((x - X0) / G - cx0, (y - Y0) / G - cy0))
    m = np.array(im, dtype=bool)
    if DEST[0] is copper:
        copper[li][cy0:cy1, cx0:cx1][m] = net
        return
    reg = grid[li][cy0:cy1, cx0:cx1]
    free = m & (reg == EMPTY)
    clash = m & (reg != EMPTY) & (reg != net)
    reg[free] = net
    reg[clash] = MULTI


def grow(net):
    return CLR + W / 2 + TOL + (0.1 if net in hc else 0.0)


def mark_poly(li, net, poly, g):
    ps = pcbnew.SHAPE_POLY_SET(poly)
    if g > 0:
        ps.Inflate(mm(g), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, mm(0.01))
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [(MM(o.CPoint(j).x), MM(o.CPoint(j).y)) for j in range(o.PointCount())]
        if len(pts) < 3:
            continue
        holes = []
        for h in range(ps.HoleCount(i)):
            hh = ps.Hole(i, h)
            holes.append([(MM(hh.CPoint(j).x), MM(hh.CPoint(j).y)) for j in range(hh.PointCount())])
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]

        def draw(d, T, pts=pts, holes=holes):
            d.polygon([T(*p) for p in pts], fill=1)
            for h in holes:
                if len(h) >= 3:
                    d.polygon([T(*p) for p in h], fill=0)
        mark(li, net, draw, min(xs), min(ys), max(xs), max(ys))


def mark_seg(li, net, a, b, half):
    def draw(d, T):
        d.line([T(*a), T(*b)], fill=1, width=max(1, int(round(2 * half / G))))
        r = half / G
        for p in (a, b):
            q = T(*p)
            d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=1)
    mark(li, net, draw, min(a[0], b[0]) - half, min(a[1], b[1]) - half, max(a[0], b[0]) + half, max(a[1], b[1]) + half)


def mark_disc(li, net, c, r):
    def draw(d, T):
        q = T(*c)
        d.ellipse([q[0] - r / G, q[1] - r / G, q[0] + r / G, q[1] + r / G], fill=1)
    mark(li, net, draw, c[0] - r, c[1] - r, c[0] + r, c[1] + r)


# ---- obstacles (grown) and true copper ----------------------------------------------------------------------------
def pad_layers(p):
    return [li for li, lay in enumerate(LAYERS) if p.IsOnLayer(lay) or p.HasHole()]


for dest, k in ((grid, 1.0), (copper, 0.0)):
    DEST[0] = dest
    for fp in board.GetFootprints():
        for p in fp.Pads():
            n = p.GetNetCode()
            for li in pad_layers(p):
                mark_poly(li, n, p.GetEffectivePolygon(LAYERS[li], pcbnew.ERROR_INSIDE), k * grow(n))
    for t in board.GetTracks():
        n = t.GetNetCode()
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition()
            for li in range(len(LAYERS)):
                mark_disc(li, n, (MM(c.x), MM(c.y)), MM(t.GetWidth(pcbnew.F_Cu)) / 2 + k * grow(n))
        elif t.GetLayer() in LAYERS:
            li = LAYERS.index(t.GetLayer())
            a, b = t.GetStart(), t.GetEnd()
            mark_seg(li, n, (MM(a.x), MM(a.y)), (MM(b.x), MM(b.y)), MM(t.GetWidth()) / 2 + k * grow(n))
    if dest is copper:
        for z in board.Zones():
            if z.GetIsRuleArea():
                continue
            for li, lay in enumerate(LAYERS):
                if z.IsOnLayer(lay):
                    mark_poly(li, z.GetNetCode(), z.GetFilledPolysList(lay), 0.0)
DEST[0] = grid
gnd = board.FindNet("GND").GetNetCode()
for z in board.Zones():
    if z.GetIsRuleArea():
        for li, lay in enumerate(LAYERS):
            if z.IsOnLayer(lay) and (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()):
                mark_poly(li, MULTI, z.Outline(), grow(0))
        continue
    n = z.GetNetCode()
    for li, lay in enumerate(LAYERS):
        if not z.IsOnLayer(lay):
            continue
        if lay == pcbnew.In2_Cu and n == gnd and z.GetZoneName().startswith("GND_PLANE"):
            continue                       # In2 GND fill: signals may cut it (refill carves around them)
        mark_poly(li, n, z.GetFilledPolysList(lay), grow(n))
# room for the In2 GND fill's thermal spokes round GND through-hole pads (a signal hugging the pad starves them)
for fp in board.GetFootprints():
    for q in fp.Pads():
        if False:
            c, bq = q.GetPosition(), q.GetBoundingBox()
            mark_disc(1, gnd, (MM(c.x), MM(c.y)), max(MM(bq.GetWidth()), MM(bq.GetHeight())) / 2 + 0.6)
# outside the board (edge rule 0.25 mm)
outline = pcbnew.SHAPE_POLY_SET()
board.GetBoardPolygonOutlines(outline, False)
inside = pcbnew.SHAPE_POLY_SET(outline)
inside.Deflate(mm(0.25 + W / 2 + TOL), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, mm(0.01))
inmask = Image.new("1", (NX, NY), 0)
dr = ImageDraw.Draw(inmask)
for i in range(inside.OutlineCount()):
    o = inside.Outline(i)
    dr.polygon([((MM(o.CPoint(j).x) - X0) / G, (MM(o.CPoint(j).y) - Y0) / G) for j in range(o.PointCount())], fill=1)
outside = ~np.array(inmask, dtype=bool)
for li in range(len(LAYERS)):
    grid[li][outside] = MULTI
VIA_EXTRA = int(math.ceil((VIA_D / 2 - W / 2) / G))   # a via needs this much more room than a track centre line

HOLES, BIG_HOLES = {}, []                 # 1 mm buckets of (x, y, r_extra, net); large PTH pads kept apart
HOLE_CACHE = {}


def add_hole(x, y, r, n):
    if r > 1.0:
        BIG_HOLES.append((x, y, r, n))
    else:
        HOLES.setdefault((int(x), int(y)), []).append((x, y, r, n))
    HOLE_CACHE.clear()


for t in board.GetTracks():
    if t.GetClass() == "PCB_VIA":
        v = t.GetPosition()
        add_hole(MM(v.x), MM(v.y), 0.0, t.GetNetCode())
for fp in board.GetFootprints():
    for q in fp.Pads():
        if q.HasHole():
            c = q.GetPosition()
            r = max(MM(q.GetBoundingBox().GetWidth()), MM(q.GetBoundingBox().GetHeight())) / 2 - VIA_D / 2
            add_hole(MM(c.x), MM(c.y), max(r, 0.0), q.GetNetCode())


def via_spacing_ok(x, y, net):
    key = (round(x, 2), round(y, 2), net)
    if key in HOLE_CACHE:
        return HOLE_CACHE[key]
    near = [h for i in range(int(x) - 3, int(x) + 4) for j in range(int(y) - 3, int(y) + 4) for h in HOLES.get((i, j), ())]
    ok = True
    for hx, hy, r, hn in near + BIG_HOLES:
        if math.hypot(hx - x, hy - y) - r < (VIA_MIN_SAME if hn == net else VIA_MIN_OTHER):
            ok = False
            break
    HOLE_CACHE[key] = ok
    return ok


# ---- edges from the DRC report ----------------------------------------------------------------------------------
txt = open(RPT, encoding="utf-8").read()
edges = []
for blk in txt.split("[unconnected_items]")[1:]:
    items = re.findall(r"@\(([\d.\-]+) mm, ([\d.\-]+) mm\): (.*)", blk)[:2]
    if len(items) < 2:
        continue
    (ax, ay, ad), (bx, by, bd) = items
    netm = re.search(r"\[(.*?)\]", ad)
    if not netm:
        continue
    name = netm.group(1)
    if HAND.search(name) or HAND.search(ad):
        continue
    edges.append((math.hypot(float(ax) - float(bx), float(ay) - float(by)), name,
                  (float(ax), float(ay), ad), (float(bx), float(by), bd)))
edges.sort()
print("edges to route:", len(edges))


TRK_BY_NET = {}                           # pre-existing tracks / vias (route_power fanouts) per net
for _t in board.GetTracks():
    TRK_BY_NET.setdefault(_t.GetNetCode(), []).append(_t)


def island_cells(pad, net, seeds=None):
    """Cells of the hand-placed stubs and vias hanging off a pad (fanned-out fine-pitch pins: the pad itself is boxed
    in, the route starts / ends on its via). With seeds (tracks / vias) instead of a pad, flood from those."""
    items, frontier, seen = [], [], set()
    for t in (seeds if seeds is not None else TRK_BY_NET.get(net, ())):
        if seeds is not None or (t.GetClass() != "PCB_VIA" and (pad.HitTest(t.GetStart()) or pad.HitTest(t.GetEnd()))):
            ends = [t.GetPosition()] if t.GetClass() == "PCB_VIA" else [t.GetStart(), t.GetEnd()]
            items.append(t); seen.add(t.m_Uuid.AsString()); frontier += ends
    for _ in range(6):
        nxt = []
        for t in TRK_BY_NET.get(net, ()):
            if t.m_Uuid.AsString() in seen:
                continue
            ends = [t.GetPosition()] if t.GetClass() == "PCB_VIA" else [t.GetStart(), t.GetEnd()]
            if any(abs(e.x - f.x) + abs(e.y - f.y) < mm(0.05) for e in ends for f in frontier):
                items.append(t); seen.add(t.m_Uuid.AsString()); nxt += ends
        if not nxt:
            break
        frontier = nxt
    out = []
    for t in items:
        if t.GetClass() == "PCB_VIA":
            c, r = t.GetPosition(), MM(t.GetWidth(pcbnew.F_Cu)) / 2
            cx, cy = cell(MM(c.x), MM(c.y))
            k = int(r / G)
            cand = [(li, cx + dx, cy + dy) for li in range(len(LAYERS)) for dx in range(-k, k + 1) for dy in range(-k, k + 1)]
        elif t.GetLayer() in LAYERS:
            li = LAYERS.index(t.GetLayer())
            a, b = t.GetStart(), t.GetEnd()
            ax, ay, bx, by = MM(a.x), MM(a.y), MM(b.x), MM(b.y)
            n = max(1, int(math.hypot(bx - ax, by - ay) / (G / 2)))
            cand = [(li,) + cell(ax + (bx - ax) * i / n, ay + (by - ay) * i / n) for i in range(n + 1)]
        else:
            continue
        out += [c for c in cand if 0 <= c[1] < NX and 0 <= c[2] < NY
                and copper[c[0]][c[2], c[1]] == net and grid[c[0]][c[2], c[1]] == net]
    return out


def item_cells(desc, x, y, net):
    """True-copper cells (li, cx, cy) of the item DRC reported: the exact pad, or the track / via end at (x, y)."""
    m = re.match(r"(?:PTH )?[Pp]ad (\S+) \[.*?\] of (\S+)", desc)
    out = []
    if m:
        fp = board.FindFootprintByReference(m.group(2))
        pads = [p for p in fp.Pads() if p.GetNumber() == m.group(1)]
        pads.sort(key=lambda p: math.hypot(MM(p.GetPosition().x) - x, MM(p.GetPosition().y) - y))
        p = pads[0]
        bbp = p.GetBoundingBox()
        cx0, cy0 = cell(MM(bbp.GetLeft()), MM(bbp.GetTop()))
        cx1, cy1 = cell(MM(bbp.GetRight()), MM(bbp.GetBottom()))
        for li in pad_layers(p):
            poly = p.GetEffectivePolygon(LAYERS[li], pcbnew.ERROR_INSIDE)
            for X in range(cx0, cx1 + 1):
                for Y in range(cy0, cy1 + 1):
                    if poly.Contains(pcbnew.VECTOR2I(mm(X0 + X * G), mm(Y0 + Y * G))) and grid[li][Y, X] == net:
                        out.append((li, X, Y))
        return out + island_cells(p, net)
    seeds = []
    for t in TRK_BY_NET.get(net, ()):                    # the reported track / via itself, if it is pre-existing
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition()
            if math.hypot(MM(c.x) - x, MM(c.y) - y) < MM(t.GetWidth(pcbnew.F_Cu)) / 2 + 0.05:
                seeds.append(t)
        else:
            a, b = t.GetStart(), t.GetEnd()
            if _seg_pt(MM(a.x), MM(a.y), MM(b.x), MM(b.y), x, y) < MM(t.GetWidth()) / 2 + 0.05:
                seeds.append(t)
    if seeds:
        found = island_cells(None, net, seeds)
        if found:
            return found
    cx, cy = cell(x, y)
    lays = range(len(LAYERS))
    if " on F.Cu" in desc:
        lays = [0]
    elif " on B.Cu" in desc:
        lays = [3]
    elif "In2" in desc:
        lays = [1]
    elif "In3" in desc:
        lays = [2]
    R = 15 if desc.startswith("Zone") else 2
    for li in lays:
        for dx in range(-R, R + 1):
            for dy in range(-R, R + 1):
                X, Y = cx + dx, cy + dy
                if 0 <= X < NX and 0 <= Y < NY and copper[li][Y, X] == net and grid[li][Y, X] == net:
                    out.append((li, X, Y))
    return out


def net_cells(net, x0, y0, x1, y1):
    """True-copper cells of this net inside a window."""
    out = set()
    for li in range(len(LAYERS)):
        sub = (copper[li][y0:y1, x0:x1] == net) & (grid[li][y0:y1, x0:x1] == net)
        ys, xs = np.nonzero(sub)
        out.update((li, x0 + int(a), y0 + int(b)) for a, b in zip(xs, ys))
    return out


def astar(net, starts, goals, win, wh=1.0, cap=None):
    cap = cap or NODE_CAP
    x0, y0, x1, y1 = win
    gset = set(goals)
    if not gset or not starts:
        return None
    gl = list(gset)
    if len(gl) > 48:
        gl = gl[:: max(1, len(gl) // 48)]
    gxy = [(g[1], g[2]) for g in gl]

    def h(x, y):                                          # octile distance (diagonal steps cost 1.414)
        best = 1e18
        for gx, gy in gxy:
            a, b = abs(gx - x), abs(gy - y)
            v = a + b - 0.586 * min(a, b)
            if v < best:
                best = v
        return best

    def free(li, x, y):
        if not (x0 <= x < x1 and y0 <= y < y1):
            return False
        v = grid[li][y, x]
        return v == EMPTY or v == net

    def via_ok(x, y):
        for li in range(len(LAYERS)):
            sub = grid[li][max(y - VIA_EXTRA, 0):y + VIA_EXTRA + 1, max(x - VIA_EXTRA, 0):x + VIA_EXTRA + 1]
            if np.any((sub != EMPTY) & (sub != net)):
                return False
        return True

    dirs = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
            (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    openq, came, gs = [], {}, {}
    for s in starts:
        st = (s[0], s[1], s[2], -1)
        gs[st] = 0.0
        heapq.heappush(openq, (wh * h(s[1], s[2]), 0.0, st))
    seen = 0
    while openq:
        f, gcost, st = heapq.heappop(openq)
        if gs.get(st, 1e18) < gcost - 1e-9:
            continue
        li, x, y, d = st
        if (li, x, y) in gset and gcost > 0:
            path = [st]
            while st in came:
                st = came[st]
                path.append(st)
            return path[::-1]
        seen += 1
        if seen > cap:
            return None
        for k, (dx, dy, c) in enumerate(dirs):
            if (li == VERT and dx) or (li == HORZ and dy):
                if not RELAXED:
                    continue
                c = c * 3.0
            X, Y = x + dx, y + dy
            if not free(li, X, Y):
                continue
            if dx and dy and not (free(li, x + dx, y) or free(li, x, y + dy)):
                continue
            nc = gcost + c * LCOST[li] + (BEND if d not in (-1, k) else 0.0)
            ns = (li, X, Y, k)
            if nc < gs.get(ns, 1e18):
                gs[ns] = nc
                came[ns] = st
                heapq.heappush(openq, (nc + wh * h(X, Y), nc, ns))
        recent = False
        q = st
        for _ in range(VIA_GAP_PATH):
            pq = came.get(q)
            if pq is None:
                break
            if pq[0] != q[0]:
                recent = True
                break
            q = pq
        if not recent and via_ok(x, y) and via_spacing_ok(X0 + x * G, Y0 + y * G, net):
            for lj in range(len(LAYERS)):
                if lj != li and free(lj, x, y):
                    nc = gcost + VIA_COST
                    ns = (lj, x, y, -1)
                    if nc < gs.get(ns, 1e18):
                        gs[ns] = nc
                        came[ns] = st
                        heapq.heappush(openq, (nc + wh * h(x, y), nc, ns))
    return None


PADS_BY_NET = {}
for _fp in board.GetFootprints():
    for _q in _fp.Pads():
        if _q.IsOnLayer(pcbnew.F_Cu) and _q.GetShape(pcbnew.F_Cu) in (
                pcbnew.PAD_SHAPE_RECTANGLE, pcbnew.PAD_SHAPE_ROUNDRECT, pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_OVAL):
            PADS_BY_NET.setdefault(_q.GetNetCode(), []).append(_q)


VIAS_BY_NET = {}
for _t in board.GetTracks():
    if _t.GetClass() == "PCB_VIA":
        _c = _t.GetPosition()
        VIAS_BY_NET.setdefault(_t.GetNetCode(), []).append((MM(_c.x), MM(_c.y), MM(_t.GetWidth(pcbnew.F_Cu)) / 2))


def snap(pt, n):
    """Centre of the convex F.Cu pad, or of the existing via, of net n that contains a path end, or None (a route
    that stops inside a pad or via ring but off its centre leaves a thin wedge)."""
    for x, y, r in VIAS_BY_NET.get(n, ()):
        if math.hypot(x - pt[0], y - pt[1]) < r + G * 1.2:
            return x, y
    if pt[2] != 0:
        return None
    v = pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1]))
    for q in PADS_BY_NET.get(n, ()):
        if q.HitTest(v, mm(G * 1.2)):                     # grid cells at a rounded corner sit just outside
            c = q.GetPosition()
            return MM(c.x), MM(c.y)
    return None


def emit(net_obj, path, added):
    """Turn a cell path into tracks (merged straight runs) and vias; mark them in the grid. ca / cb: pad centres the
    route finishes on when it ends inside a pad (snap)."""
    n = net_obj.GetNetCode()
    pts = [(X0 + p[1] * G, Y0 + p[2] * G, p[0]) for p in path]
    ca, cb = snap(pts[0], n), snap(pts[-1], n)
    if ca:
        d0 = math.hypot(ca[0] - pts[0][0], ca[1] - pts[0][1])
        if d0 > 0.35:
            pts.insert(0, (ca[0], ca[1], pts[0][2]))
        elif d0 > 0.02 and len(pts) > 1:
            pts[0] = (ca[0], ca[1], pts[0][2])
    if cb:
        d1 = math.hypot(cb[0] - pts[-1][0], cb[1] - pts[-1][1])
        if d1 > 0.35:
            pts.append((cb[0], cb[1], pts[-1][2]))
        elif d1 > 0.02 and len(pts) > 1:
            pts[-1] = (cb[0], cb[1], pts[-1][2])
    i = 0
    while i < len(pts) - 1:
        j = i + 1
        if pts[j][2] != pts[i][2]:                          # layer change: via
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(pts[i][0]), mm(pts[i][1])))
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL)); v.SetNet(net_obj)
            board.Add(v)
            added.append(v.m_Uuid.AsString())
            add_hole(pts[i][0], pts[i][1], 0.0, n)
            for li in range(len(LAYERS)):
                mark_disc(li, n, pts[i][:2], VIA_D / 2 + grow(n))
                copper[li][cell(*pts[i][:2])[1], cell(*pts[i][:2])[0]] = n
            i = j
            continue
        dx, dy = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
        while j + 1 < len(pts) and pts[j + 1][2] == pts[i][2] and \
                abs((pts[j + 1][0] - pts[j][0]) - dx) < 1e-6 and abs((pts[j + 1][1] - pts[j][1]) - dy) < 1e-6:
            j += 1
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(pts[i][0]), mm(pts[i][1])))
        t.SetEnd(pcbnew.VECTOR2I(mm(pts[j][0]), mm(pts[j][1])))
        t.SetWidth(mm(W)); t.SetLayer(LAYERS[pts[i][2]]); t.SetNet(net_obj)
        board.Add(t)
        added.append(t.m_Uuid.AsString())
        mark_seg(pts[i][2], n, pts[i][:2], pts[j][:2], W / 2 + grow(n))
        DEST[0] = copper
        mark_seg(pts[i][2], n, pts[i][:2], pts[j][:2], W / 2)
        DEST[0] = grid
        i = j


# ---- fine-pitch pin escapes ---------------------------------------------------------------------------------------
# A pin on a 0.4/0.5 mm-pitch package is boxed in on the grid by its neighbours' clearance halos. Before searching,
# lay a 0.15 mm stub straight out of the package from the pin, checked exactly (pad rectangles, track segments, vias)
# against other nets with 0.15 mm clearance; the search then starts / ends at the open end of the stub.
FINE = re.compile(r"^(U101|U301|U401|U501|U403|U503|U402|U502|U201|U202|U204)$")
ESC_W, ESC_LEN = 0.15, 0.7
NODE_CAP = 600000


def _seg_pt(ax, ay, bx, by, px, py):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(ax + t * dx - px, ay + t * dy - py)


def _seg_rect(a, b, r):
    """Distance from segment a-b to rectangle r (x0, y0, x1, y1); 0 if they touch."""
    for k in range(21):
        x, y = a[0] + (b[0] - a[0]) * k / 20, a[1] + (b[1] - a[1]) * k / 20
        if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
            return 0.0
    best = 1e9
    for k in range(21):
        x, y = a[0] + (b[0] - a[0]) * k / 20, a[1] + (b[1] - a[1]) * k / 20
        dx = max(r[0] - x, 0, x - r[2])
        dy = max(r[1] - y, 0, y - r[3])
        best = min(best, math.hypot(dx, dy))
    return best


PADRECTS = []
for fp in board.GetFootprints():
    for q in fp.Pads():
        bq = q.GetBoundingBox()
        PADRECTS.append((q.GetNetCode(), pad_layers(q), (MM(bq.GetLeft()), MM(bq.GetTop()), MM(bq.GetRight()),
                                                        MM(bq.GetBottom()))))


def escape(desc, x, y, net, added):
    """Lay an escape stub from a fine-pitch pad; return the stub-end cells, or None."""
    m = re.match(r"(?:PTH )?[Pp]ad (\S+) \[.*?\] of (\S+)", desc)
    if not m or not FINE.match(m.group(2)) or " on F.Cu" not in desc:
        return None
    fp = board.FindFootprintByReference(m.group(2))
    pads = [q for q in fp.Pads() if q.GetNumber() == m.group(1)]
    pads.sort(key=lambda q: math.hypot(MM(q.GetPosition().x) - x, MM(q.GetPosition().y) - y))
    q = pads[0]
    c, f = q.GetPosition(), fp.GetPosition()
    px, py = MM(c.x), MM(c.y)
    vx, vy = px - MM(f.x), py - MM(f.y)
    bq = q.GetBoundingBox()
    hw, hh = MM(bq.GetWidth()) / 2, MM(bq.GetHeight()) / 2
    if abs(vx) >= abs(vy):
        d = (1.0 if vx > 0 else -1.0, 0.0)
        L = hw + ESC_LEN
    else:
        d = (0.0, 1.0 if vy > 0 else -1.0)
        L = hh + ESC_LEN
    a, b = (px, py), (px + d[0] * L, py + d[1] * L)
    need = CLR + ESC_W / 2
    for n2, lays, r in PADRECTS:
        if n2 != net and 0 in lays and _seg_rect(a, b, r) < need:
            return None
    for t in board.GetTracks():
        if t.GetNetCode() == net:
            continue
        if t.GetClass() == "PCB_VIA":
            v = t.GetPosition()
            if _seg_pt(*a, *b, MM(v.x), MM(v.y)) < need + MM(t.GetWidth(pcbnew.F_Cu)) / 2:
                return None
        elif t.GetLayer() == pcbnew.F_Cu:
            s0, s1 = t.GetStart(), t.GetEnd()
            w2 = MM(t.GetWidth()) / 2
            for pt in ((MM(s0.x), MM(s0.y)), (MM(s1.x), MM(s1.y))):
                if _seg_pt(*a, *b, *pt) < need + w2:
                    return None
            if min(_seg_pt(MM(s0.x), MM(s0.y), MM(s1.x), MM(s1.y), *a),
                   _seg_pt(MM(s0.x), MM(s0.y), MM(s1.x), MM(s1.y), *b)) < need + w2:
                return None
    ex, ey = cell(*b)
    if grid[0][ey, ex] not in (net, EMPTY):
        return None
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
    t.SetWidth(mm(ESC_W)); t.SetLayer(pcbnew.F_Cu); t.SetNet(board.FindNet(desc.split("[")[1].split("]")[0]))
    board.Add(t)
    added.append(t.m_Uuid.AsString())
    STUBS.append(t)
    mark_seg(0, net, a, b, ESC_W / 2 + grow(net))
    DEST[0] = copper
    mark_seg(0, net, a, b, ESC_W / 2)
    DEST[0] = grid
    return [(0, ex, ey)]


added, failed, done = [], [], 0
for dist, name, A, B in edges[:MAX_EDGES]:
    net_obj = board.FindNet(name)
    if net_obj is None:
        continue
    n = net_obj.GetNetCode()
    ax, ay, ad = A
    bx, by, bd = B
    # report coordinates are absolute board mm, the same frame as the grid
    pad = 6.0 if dist < 10 else (12.0 if dist < 30 else 30.0)
    wx0, wy0 = cell(min(A[0], B[0]) - pad, min(A[1], B[1]) - pad)
    wx1, wy1 = cell(max(A[0], B[0]) + pad, max(A[1], B[1]) + pad)
    win = (max(wx0, 0), max(wy0, 0), min(wx1, NX), min(wy1, NY))
    starts = item_cells(ad, A[0], A[1], n)
    goals = item_cells(bd, B[0], B[1], n)
    ma, mb = re.match(r"(?:PTH )?[Pp]ad \S+ \[.*?\] of (\S+)", ad), re.match(r"(?:PTH )?[Pp]ad \S+ \[.*?\] of (\S+)", bd)
    def straight_clear(a, b):
        k = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / (G / 2)))
        for i in range(k + 1):
            X, Y = cell(a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k)
            if grid[0][Y, X] not in (n, EMPTY):
                return False
        return True
    if ma and mb and ma.group(1) == mb.group(1) and dist < 1.2 and ("on F.Cu" in ad or "PTH" in ad) and ("on F.Cu" in bd or "PTH" in bd) \
            and straight_clear(A, B):
        # neighbouring pins of one part on the same net: one straight pad-width bridge
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(A[0]), mm(A[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(B[0]), mm(B[1])))
        t.SetWidth(mm(0.25)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net_obj)
        board.Add(t)
        added.append(t.m_Uuid.AsString())
        mark_seg(0, n, (A[0], A[1]), (B[0], B[1]), 0.125 + grow(n))
        done += 1
        continue
    if name == "GND" or bd.startswith("Zone"):
        own = {(c[1], c[2]) for c in starts}
        sx, sy = cell(A[0], A[1])
        goals = [c for c in net_cells(n, *win) if (c[1], c[2]) not in own and max(abs(c[1] - sx), abs(c[2] - sy)) > 6]
    WH, CAP = (1.0, NODE_CAP) if dist < 15 else ((1.25, 3 * NODE_CAP) if dist < 30 else (1.4, 12 * NODE_CAP))
    path = astar(n, starts, goals, win, WH, CAP)
    STUBS = []
    if path is None:                                      # retry from / to escape stubs on fine-pitch pins
        ea = escape(ad, A[0], A[1], n, added)
        eb = None if (name == "GND" or bd.startswith("Zone")) else escape(bd, B[0], B[1], n, added)
        if ea or eb:
            path = astar(n, ea or starts, eb or goals, win, WH, CAP)
    if path is None:
        for t in STUBS:                                   # no dangling escape stubs (their grid marks stay: harmless)
            added.remove(t.m_Uuid.AsString())
            board.Remove(t)
        failed.append("%s %.1f,%.1f -> %.1f,%.1f" % (name, A[0] - 50, A[1] - 50, B[0] - 50, B[1] - 50))
        continue
    emit(net_obj, path, added)
    done += 1

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(PCB)
open(PRO, "w", encoding="utf-8", newline="\n").write(pro_backup)
open(IDS, "w", newline="\n").write("\n".join(added) + "\n")
print("routed %d edges, %d failed" % (done, len(failed)))
for f in failed:
    print("  FAILED", f)
