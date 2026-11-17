#!/usr/bin/env python3
"""rethread.py geo_in.json spec_out.json [--only=regex] [--skip=regex] [--maxexc-sensitive=0.30] [--maxexc=0.80] [--log=file] [--passes=6] [--exc-from=geo.json]

Junction / entry / angle pass: brings the tracks of every net into the "clean form" a to d of the brief
(ends meet exactly, tracks end on via and pad centres, no micro-pieces, only 0/45/90 degree pieces), in place.

How it works (per net and layer, per connected group of tracks):
  1. graph      zero-length and exact duplicate pieces go; a piece is split where another end lies exactly on it;
                a loose end that only touches the copper of another piece gets a link to it (a real T-junction is
                formed); micro spurs that lie inside other copper go.
  2. anchors    every node inside a via -> the via centre; nodes inside a pad that the track runs to the centre of
                (or that are close to it) -> the pad centre; nodes where three or more arms meet (welded when they are
                within a track width of each other) -> one junction point, chosen among the cluster nodes and the
                crossing points of the arms' long lines; loose ends, width changes and pad taps far from the pad
                centre stay exactly where they are.
  3. chains     the run between two anchors is a chain. Its dirty spots (end not on the anchor, piece off the 45 degree
                grid, piece shorter than its width, corner sharper than 90 degrees, corner inside a via or pad) are
                re-drawn one zone at a time: the zone reaches from the far end of the clean piece before the spot to
                the far end of the clean piece after it, so long clean stretches keep their line and only their ends
                slide. The new path is a shortest path (length + bends + penalties) in the graph of crossing points of
                candidate lines (the lines of the old pieces, the four lines through the anchor and through the old
                nodes, corner chamfers), restricted to a corridor of growing half-width round the old path, with the
                clearance of the board rules (old shortfalls grandfathered) and the same-channel test.
  4. accept     per connected group: every new piece on the 45 degree grid, same pads/vias/pours touched, group still
                in one piece, clearance, excursion limit; per net: geolib.connectivity before == after; at the end
                geolib.clearance on everything. Whatever fails is reverted and logged.
Widths: a re-drawn piece takes the width of the old piece it replaces (nearest old piece of its zone).
RF nets are never touched; sensitive nets (brief) get --maxexc-sensitive.
The passes repeat on their own result until nothing changes (at most --passes), so the output is a fixed point: running
the tool on its own result gives an empty spec. The excursion limit counts from the tracks of the board given with
--exc-from; default: base/geo.json beside tools/ (the committed board) when that file exists, otherwise the board that
came in (--exc-from=input forces that). So the limit holds for all the moves of a pipeline together, and a second run
cannot creep further.
"""
import json, sys, math, collections, re, os, time, heapq
import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box, MultiLineString
from shapely.strtree import STRtree
from shapely.ops import polygonize, unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
for cand in (os.environ.get('RETHREAD_TOOLS', ''), os.path.join(HERE, '..', '..', 'tools'), HERE):
    if cand and os.path.exists(os.path.join(cand, 'geolib.py')): sys.path.insert(0, cand); break
import geolib as G

LN = G.LN
MM = 1e-6
END_TOL = 30000
RF = ('/MCU/RFIO', '/MCU/ANT_IN', 'Net-(C313-Pad2)')
SENS_CLASSES = ('HighCurrent', 'Power', 'GND', 'Kelvin', 'GateDrive')
SENS_NETS = ('EN_5V1', '/USB Port 1/I2CC_SCL', '/USB Port 2/SBU_FLT', '/Cells and Gauge/TS4', 'Net-(U403-FB)', 'Net-(U503-FB)') + RF
SENS_RX = [re.compile(r) for r in (r'/DPDN', r'/D[PN]$', r'USB_D', r'/(SRP|SRN|ACP|ACN)(_F)?$', r'/DRV_SUP$')]
# cost model (unit: mm of track length)
C45, C90 = 0.2, 1.2
P_SHORT, P_SHORT_HID, P_TINY = 2.5, 1.0, 6.0
P_INVIA, P_INPAD = 4.0, 2.0
P_ACUTE, P_OVER = 0.5, 0.8
P_TOL, P_OFFC, P_BADEND = 0.1, 0.3, 0.9
KAREA = 6.0            # per mm2 of area between the old and the new path
P_STICK = 0.6          # a 90 degree corner on a pad centre line whose leaving track hangs over the side of the pad
P_JOG = 0.8            # a corner inside the via or pad the path ends in (hidden jog)
MAXLEN = 1.10          # a re-drawn zone may not be longer than this times the old one (+ 0.05 mm)
FREE_R = 150000        # a loose end inside a pour of its net may move this far when its blob is re-drawn
HID_MIN = 50000       # a piece inside pad/via copper is not 'short' from this length on
INF = float('inf')
DEBUG = bool(os.environ.get('RT_DEBUG'))
DIRS8 = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
D8 = {d: i for i, d in enumerate(DIRS8)}


# ------------------------------------------------------------------------------------------ small geometry
def sgn(v): return (v > 0) - (v < 0)
def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])
def on45(a, b):
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    return dx == 0 or dy == 0 or dx == dy
def dir8(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    if (dx == 0 and dy == 0) or not (dx == 0 or dy == 0 or abs(dx) == abs(dy)): return None
    return D8[(sgn(dx), sgn(dy))]
def turn8(d1, d2):
    t = (d2 - d1) % 8
    return min(t, 8 - t)
def lines_through(p): return [(0, p[1]), (1, p[0] - p[1]), (2, p[0]), (3, p[0] + p[1])]
def line_of(a, b):
    d = dir8(a, b)
    return None if d is None else lines_through(a)[d % 4]
def isect(l1, l2):
    (k1, c1), (k2, c2) = l1, l2
    if k1 == k2: return None
    if k1 > k2: k1, c1, k2, c2 = k2, c2, k1, c1
    if k1 == 0:
        if k2 == 1: return (c2 + c1, c1)
        if k2 == 2: return (c2, c1)
        return (c2 - c1, c1)
    if k1 == 1:
        if k2 == 2: return (c2, c2 - c1)
        if (c2 + c1) % 2: return None
        return ((c2 + c1) // 2, (c2 - c1) // 2)
    return (c1, c2 - c1)
def lparam(l, p): return p[1] if l[0] == 2 else p[0]
def seg_pt(p, a, b):
    """distance of p from segment a-b and the parameter of the foot"""
    dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
    if L2 == 0: return dist(p, a), 0.0
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2; t = max(0.0, min(1.0, t))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy)), t
def interior_exact(p, a, b):
    """p lies exactly on the open segment a-b"""
    ux, uy = b[0] - a[0], b[1] - a[1]; vx, vy = p[0] - a[0], p[1] - a[1]
    return ux * vy - uy * vx == 0 and 0 < ux * vx + uy * vy < ux * ux + uy * uy
def clean(pts):
    o = []
    for p in pts:
        if o and p == o[-1]: continue
        while len(o) >= 2:
            ux, uy = o[-1][0] - o[-2][0], o[-1][1] - o[-2][1]; vx, vy = p[0] - o[-1][0], p[1] - o[-1][1]
            if ux * vy - uy * vx == 0 and ux * vx + uy * vy > 0: o.pop()
            else: break
        o.append(p)
    return o
def plen(pts): return sum(dist(a, b) for a, b in zip(pts, pts[1:]))
def region(old, new):
    ring = list(old) + list(new[-2:0:-1]) + [old[0]]
    if len(set(ring)) < 3: return None
    try: faces = list(polygonize(unary_union(LineString(ring))))
    except Exception: return None
    faces = [f for f in faces if f.area > 100.0]
    return unary_union(faces) if faces else None


# ------------------------------------------------------------------------------------------ board model
class Item:
    __slots__ = ('geom', 'r', 'net', 'kind', 'name', 'alive')
    def __init__(s, geom, r, net, kind, name): s.geom, s.r, s.net, s.kind, s.name, s.alive = geom, r, net, kind, name, True

class Board:
    def __init__(s, g):
        s.g = g; s.nc = g['netclass']
        s.static = {l: [] for l in LN}; s.trk = {l: [] for l in LN}; s.extra = {l: [] for l in LN}; s.byid = {}
        s.pads = collections.defaultdict(list); s.vias = collections.defaultdict(list); s.fills = collections.defaultdict(list)
        for v in g['vias']:
            pt = Point(v['x'], v['y'])
            for l in LN:
                if l in v['flash']: s.static[l].append(Item(pt, v['d'] / 2, v['net'], 'via', v['id']))
                else: s.static[l].append(Item(pt, v['drill'] / 2, v['net'], 'viahole', v['id']))
            for l in LN[LN.index(v['top']):LN.index(v['bot']) + 1]: s.vias[(v['net'], l)].append(v)
        for p in g['pads']:
            for l, poly in p['L'].items():
                if len(poly) >= 3:
                    pg = Polygon(poly); s.static[l].append(Item(pg, 0, p['net'], 'pad', p['ref'] + '.' + p['n'])); s.pads[(p['net'], l)].append((pg, p))
            if p['hole'] and (p['npth'] or not p['L']):
                h = p['hole']; a, b = (h[0], h[1]), (h[2], h[3]); gm = Point(a) if a == b else LineString([a, b])
                for l in LN: s.static[l].append(Item(gm, h[4] / 2, None, 'hole', p['ref'] + '.' + p['n']))
        for outline, holes in g['edge']:
            for ring in [outline] + holes:
                gm = LineString(ring + [ring[0]])
                for l in LN: s.static[l].append(Item(gm, 0, None, 'edge', 'edge'))
        s.kos = {l: [] for l in LN}
        for k in g['keepouts']:
            if not k.get('notracks'): continue
            for outline, holes in k['polys']:
                pg = Polygon(outline, holes)
                for l in k['layers']: s.kos[l].append((pg, k['name']))
        for f in g['fills']:
            for k, (outer, holes) in enumerate(f['polys']):
                if len(outer) >= 3: s.fills[(f['net'], f['l'])].append((Polygon(outer, holes), '%s|%s|%s|%d' % (f['net'], f['l'], f['name'], k)))
        zc = {}
        for z in g['zones']:
            for l in z['layers']: zc[(z['net'], l)] = min(zc.get((z['net'], l), 10 ** 9), z.get('clearance') or 250000)
        s.fill_l = {l: [] for l in LN}
        for (net, l), lst in s.fills.items():
            for pg, nm in lst: s.fill_l[l].append((pg if pg.is_valid else pg.buffer(0), net, zc.get((net, l), 250000)))
        s.stree = {l: STRtree([i.geom for i in s.static[l]]) if s.static[l] else None for l in LN}
        s.rmax = {l: max([i.r for i in s.static[l]] + [0]) for l in LN}
        for t in g['tracks']: s.add_track(t)
        s.ttree = {}
        for l in LN: s.rebuild(l)
        s.nnew = 0
    def add_track(s, t):
        it = Item(G.tgeom(t), t['w'] / 2, t['net'], 'track', t['id']); s.byid[t['id']] = it; s.extra[t['l']].append(it)
    def kill(s, tid):
        it = s.byid.pop(tid, None)
        if it is not None: it.alive = False
    def rebuild(s, l):
        s.trk[l] = [i for i in s.trk[l] + s.extra[l] if i.alive]; s.extra[l] = []
        s.ttree[l] = STRtree([i.geom for i in s.trk[l]]) if s.trk[l] else None
    def query(s, l, gm, reach):
        b = gm.bounds; bx = box(b[0] - reach, b[1] - reach, b[2] + reach, b[3] + reach); out = []
        if s.stree[l] is not None:
            for k in s.stree[l].query(bx): out.append(s.static[l][k])
        if len(s.extra[l]) > 64: s.rebuild(l)
        if s.ttree[l] is not None:
            for k in s.ttree[l].query(bx):
                it = s.trk[l][k]
                if it.alive: out.append(it)
        b = bx.bounds
        for it in s.extra[l]:
            if it.alive:
                c = it.geom.bounds
                if c[0] <= b[2] and c[2] >= b[0] and c[1] <= b[3] and c[3] >= b[1]: out.append(it)
        return out
    def need(s, net, okind, onet):
        if okind == 'hole': return G.CLR_HOLE
        if okind == 'edge': return G.CLR_EDGE
        a, b = s.nc.get(net, 'Default'), s.nc.get(onet, 'Default')
        if okind == 'viahole':                              # KiCad applies the HighCurrent rule to the hole of an unflashed via too
            hc = (a == 'HighCurrent' and b not in G.NOT_DEFAULT) or (b == 'HighCurrent' and a not in G.NOT_DEFAULT)
            return max(G.CLR_HOLE, G.CLR_HC) if hc else G.CLR_HOLE
        if okind != 'pad' and ((a == 'HighCurrent' and b not in G.NOT_DEFAULT) or (b == 'HighCurrent' and a not in G.NOT_DEFAULT)): return G.CLR_HC
        return G.CLR
    def viol(s, l, net, a, b, w, slack=500):
        """[(item, gap, need)] of everything of another net closer to the piece a-b than the rule (same model as geolib.Obst.near)"""
        gm = LineString([a, b]) if a != b else Point(a); r = w / 2; out = []
        for it in s.query(l, gm, r + G.CLR_HC + s.rmax[l] + 2000):
            if it.net == net and it.net is not None: continue
            need = s.need(net, it.kind, it.net); gap = gm.distance(it.geom) - r - it.r
            if gap < need - slack: out.append((it, gap, need))
        for pg, name in s.kos[l]:
            if pg.intersects(gm.buffer(r)): out.append((('keepout', name), -1, 0))
        return out


class Retry(Exception):
    def __init__(s, key, why): s.key, s.why = key, why

class Group:
    def __init__(s, kind, nodes):
        s.kind, s.nodes = kind, set(nodes); s.T = None; s.centre = None; s.pad = None; s.bigpad = None; s.infill = None; s.arms = []; s.iadj = collections.defaultdict(list); s.iw = {}
        s.key = (kind, frozenset(nodes))
    def path_to_T(s, att, T):
        """old nodes from the attach node (excluded) through the group to T (included)"""
        if att == T: return []
        tgt = min(s.nodes, key=lambda n: (dist(n, T), n))
        if tgt == att: return [T]
        pq = [(0, att, None)]; seen = {}
        while pq:
            d, n, pr = heapq.heappop(pq)
            if n in seen: continue
            seen[n] = pr
            if n == tgt: break
            for m in s.iadj.get(n, []):
                if m not in seen: heapq.heappush(pq, (d + dist(n, m), m, n))
        if tgt not in seen: return [T]
        p = []; n = tgt
        while n != att: p.append(n); n = seen[n]
        p.reverse()
        if p[-1] != T: p.append(T)
        return p

class Chain:
    def __init__(s, core, cws, creal, ga, gb):
        s.core, s.cws, s.creal, s.g = core, cws, creal, [ga, gb]; s.pts = None; s.ws = None; s.real = None; s.frozen = False; s.dead = False
        s.core_len = plen(core); s.excl = set(core)
    def build(s):
        pts = list(s.core); ws = list(s.cws); real = list(s.creal)
        for end in (0, 1):
            g = s.g[end]; att = s.core[0] if end == 0 else s.core[-1]
            T = g.T if g.T is not None else att
            path = g.path_to_T(att, T)
            if not path: continue
            # a piece inside the group that is wider than the arm and not a micro-piece (a wide pad entry) is kept as a
            # real piece with its own width; everything else inside the group is only the way to the anchor point
            we = ws[0] if end == 0 else ws[-1]; pw = []; pr = []; prev = att
            for cur in path:
                wi = g.iw.get(frozenset((prev, cur)))
                if wi is not None and wi > we and dist(prev, cur) >= 300000: pw.append(wi); pr.append(True)
                else: pw.append(pw[-1] if pw and pr[-1] else we); pr.append(False)
                prev = cur
            if end == 0: pts = path[::-1] + pts; ws = pw[::-1] + ws; real = pr[::-1] + real
            else: pts = pts + path; ws = ws + pw; real = real + pr
        o = [pts[0]]; ow = []; orl = []
        for k in range(1, len(pts)):
            if pts[k] == o[-1]: continue
            o.append(pts[k]); ow.append(ws[k - 1]); orl.append(real[k - 1])
        if len(o) >= 2 and o[0] == o[-1] and plen(o) <= 4 * max(ow): o = [o[0]]; ow = []; orl = []
        s.pts, s.ws, s.real = o, ow, orl
    def snap(s): return (s.pts, s.ws, s.real)
    def restore(s, sn): s.pts, s.ws, s.real = sn


class Ctx:
    """one connected group of tracks of a net on a layer"""
    def __init__(s, B, net, l, tracks, others, opt):
        s.B, s.net, s.l, s.opt = B, net, l, opt; s.tracks = tracks
        xs = [t[k] for t in tracks for k in ('x1', 'x2')]; ys = [t[k] for t in tracks for k in ('y1', 'y2')]; m = 1500000
        bb = box(min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m)
        s.vias = [v for v in B.vias.get((net, l), []) if bb.covers(Point(v['x'], v['y']))]
        s.pads = [(pg, pd) for pg, pd in B.pads.get((net, l), []) if pg.intersects(bb)]; s.fills = [(pg, nm) for pg, nm in B.fills.get((net, l), []) if pg.intersects(bb)]
        s.npcache = {}
        s.sens = opt['sens'](net); s.maxexc = int((opt['maxexc_s'] if s.sens else opt['maxexc']) * 1e6)
        sched = [30000, 60000, 100000, 150000, 220000, 270000] if s.sens else [30000, 60000, 100000, 150000, 220000, 300000, 400000]
        s.sched = [e for e in sched if e <= s.maxexc - 30000]
        s.soft = 100000 if (s.sens or l not in ('F', 'B')) else 150000     # look for a nicer path up to this corridor even when a legal one exists
        s.old = [((t['x1'], t['y1']), (t['x2'], t['y2']), t['w']) for t in tracks]
        s.others = others                                   # [(a, b, w)] other tracks of the net on this layer
        s.ccache = {}; s.gcache = {}; s.zcache = {}; s.log = []
        s.own = None; s.owntree = None; s.nojog = False
        s.nojog_max = 100000 if l not in ('F', 'B') else 220000    # a piece may be shifted this far to avoid a jog inside a via or pad
    # ---- own terminals
    def via_at(s, p):
        r = None
        for v in s.vias:
            d = dist(p, (v['x'], v['y']))
            if d <= END_TOL: return v
            if d <= v['d'] / 2 + 1: r = v
        if r is not None:                                   # a pad centre that lies inside the via copper belongs to the pad
            q = s.pad_at(p)
            if q is not None and dist(p, (q[1]['x'], q[1]['y'])) <= END_TOL: return None
        return r
    def pad_at(s, p):
        P = Point(p)
        for pg, pd in s.pads:
            if pg.covers(P): return (pg, pd)
        return None
    def nodepen(s, p):
        r = s.npcache.get(p)
        if r is None: r = s.npcache[p] = s._nodepen(p)
        return r
    def _nodepen(s, p):
        v = s.via_at(p)
        if v is not None: return 0.0 if dist(p, (v['x'], v['y'])) <= END_TOL else P_INVIA
        q = s.pad_at(p)
        if q is not None:
            pd = q[1]
            return 0.0 if (abs(p[0] - pd['x']) <= END_TOL or abs(p[1] - pd['y']) <= END_TOL) else P_INPAD
        return 0.0
    def bendpen(s, p, e1, e2):
        """penalty of a corner at p; e1, e2: path end points next to p (or None). A corner inside the via or pad whose
        centre the path ends on, one piece away, is a hidden jog."""
        pn = s.nodepen(p)
        if pn:
            for e in (e1, e2):
                if e is None or s.nodepen(e) or s.nojog: continue
                v = s.via_at(p)
                if v is not None:
                    if dist(e, (v['x'], v['y'])) <= END_TOL: return P_JOG
                else:
                    q = s.pad_at(p)
                    if q is not None and dist(e, (q[1]['x'], q[1]['y'])) <= END_TOL: return P_JOG
        return pn
    def stick(s, p, q, w):
        """p: corner inside a pad of the net on one of its centre lines (not the centre), q: next point away from the pad
        centre. True if the track p-q hangs over the side of the pad."""
        pq = s.pad_at(p)
        if pq is None: return False
        pg, pd = pq; C = (pd['x'], pd['y'])
        if dist(p, C) <= END_TOL: return False
        b = pg.bounds
        if q[0] == p[0]: return p[0] - w / 2 < b[0] - 5000 or p[0] + w / 2 > b[2] + 5000
        if q[1] == p[1]: return p[1] - w / 2 < b[1] - 5000 or p[1] + w / 2 > b[3] + 5000
        return False
    def hidden(s, a, b):
        for v in s.vias:
            c = (v['x'], v['y'])
            if dist(a, c) <= v['d'] / 2 and dist(b, c) <= v['d'] / 2: return True
        A, Bp = Point(a), Point(b)
        for pg, pd in s.pads:
            if pg.covers(A) and pg.covers(Bp): return True
        return False
    # ---- clearance of one candidate piece
    def clear(s, a, b, w):
        key = (a, b, w) if a < b else (b, a, w)
        r = s.ccache.get(key)
        if r is None:
            r = True
            for it, gap, need in s.B.viol(s.l, s.net, a, b, w):
                k = it if isinstance(it, tuple) else id(it)
                og = s.gcache.get(k, s)
                if og is s:
                    if isinstance(it, tuple):
                        og = None
                        for pg, name in s.B.kos[s.l]:
                            if name == it[1] and any(pg.intersects((LineString([p, q]) if p != q else Point(p)).buffer(ww / 2)) for p, q, ww in s.old): og = -1
                    else:
                        og = None
                        for p, q, ww in s.old:
                            gp = (LineString([p, q]) if p != q else Point(p)).distance(it.geom) - ww / 2 - it.r
                            if gp < need and (og is None or gp < og): og = gp
                    s.gcache[k] = og
                if og is None or gap < og - 500: r = False; break
            s.ccache[key] = r
        return r


# ------------------------------------------------------------------------------------------ path cost
def end_pen(ctx, p, sp):
    for q, pen in sp['pts']:
        if q == p: return pen
    if sp.get('tol') is not None and dist(p, sp['tol']) <= END_TOL: return P_TOL
    if sp.get('padc') is not None:
        C, inset = sp['padc']
        if (p[0] == C[0] or p[1] == C[1]) and inset.covers(Point(p)): return P_OFFC if p != C else 0.0
    if sp.get('free') is not None:
        q, poly = sp['free']
        if dist(p, q) <= FREE_R and poly.covers(Point(p)): return 0.15 + 2.0 * dist(p, q) * MM
    return INF

def run_lengths(pts, ws):
    """per piece: the length of the straight run it belongs to (collinear neighbours of another width count in)"""
    n = len(pts) - 1; L = [dist(pts[k], pts[k + 1]) for k in range(n)]; out = list(L); k = 0
    while k < n:
        j = k; d = dir8(pts[k], pts[k + 1])
        while d is not None and j + 1 < n and dir8(pts[j + 1], pts[j + 2]) == d: j += 1
        tot = sum(L[k:j + 1])
        for i in range(k, j + 1): out[i] = tot
        k = j + 1
    return out

def short_pen(ctx, a, b, L, w):
    if L >= w - 1: return 0.0
    if L < 50000 - 1: return INF
    if ctx.hidden(a, b): return 0.0 if L >= HID_MIN else P_SHORT_HID
    return P_SHORT

def area_dev(gl, pts):
    """integral of the distance from the path pts to the line gl (nm2)"""
    tot = 0.0
    for a, b in zip(pts, pts[1:]):
        L = dist(a, b); n = max(1, int(math.ceil(L / 25000))); ts = (np.arange(n) + 0.5) / n
        tot += float(shapely.distance(gl, shapely.points(a[0] + (b[0] - a[0]) * ts, a[1] + (b[1] - a[1]) * ts)).mean()) * L
    return tot

def path_eval(ctx, pts, ws, sS, sE):
    """(cost, number of penalty items, number of 90 degree corners); cost is inf if the path is not legal"""
    if len(pts) < 2: return (0.0, 0, 0)
    c = end_pen(ctx, pts[0], sS); npen = 0; n90 = 0
    if c == INF: return (INF, 0, 0)
    if c >= P_BADEND: npen += 1
    e = end_pen(ctx, pts[-1], sE)
    if e == INF: return (INF, 0, 0)
    if e >= P_BADEND: npen += 1
    c += e; dprev = None; RL = run_lengths(pts, ws) if isinstance(ws, list) else None
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        d = dir8(a, b)
        if d is None: return (INF, 0, 0)
        L = dist(a, b); w = ws[k] if isinstance(ws, list) else ws; c += L * MM
        sp_ = short_pen(ctx, a, b, RL[k] if RL else L, w)
        if sp_ == INF: return (INF, 0, 0)
        if sp_: npen += 1; c += sp_
        if dprev is None:
            if sS.get('req') is not None and d != sS['req']: return (INF, 0, 0)
            f = sS['forbid'].get(d, 0.0)
            if f: c += f; npen += 1
        else:
            t = turn8(dprev, d)
            if t >= 3 or (t == 0 and not (RL and ws[k] != ws[k - 1])): return (INF, 0, 0)
            c += 0.0 if t == 0 else C45 if t == 1 else C90; n90 += (t == 2)
            pn = ctx.bendpen(a, pts[0] if k == 1 else None, pts[-1] if k == len(pts) - 2 else None) if t else 0.0
            if t == 2 and not pn and (ctx.stick(a, b, w) or ctx.stick(a, pts[k - 1], w)): pn = P_STICK
            if pn: c += pn; npen += 1
        dprev = d
    if sE.get('req') is not None and dprev != sE['req']: return (INF, 0, 0)
    f = sE['forbid'].get((dprev + 4) % 8, 0.0)
    if f: c += f; npen += 1
    return (c, npen, n90)


# ------------------------------------------------------------------------------------------ the search
def chamfer_lines(guide, w):
    out = set(); n = len(guide) - 1; c = max(w, 200000)
    for i in range(n):
        a, b = guide[i], guide[i + 1]; d1 = dir8(a, b)
        if d1 is None or dist(a, b) < 49000: continue
        acc = 0
        for j in range(i + 1, min(n, i + 6)):
            p, q = guide[j], guide[j + 1]; d2 = dir8(p, q)
            if d2 is not None and dist(p, q) >= 49000 and (d2 - d1) % 8 in (2, 6):
                X = isect(line_of(a, b), line_of(p, q))
                if X is not None:
                    u = DIRS8[(d1 + 4) % 8]; v = DIRS8[d2]
                    for f in (1.0, 2.0):
                        k = int(math.ceil(f * c / math.sqrt(2) / 50000 - 1e-9)) * 50000 if d1 % 2 == 0 else int(math.ceil(f * c / 2 / 50000 - 1e-9)) * 50000
                        P1 = (X[0] + k * u[0], X[1] + k * u[1]); P2 = (X[0] + k * v[0], X[1] + k * v[1])
                        ln = line_of(P1, P2)
                        if ln is not None: out.add(ln)
            acc += dist(p, q)
            if acc > 2 * w: break
    return out

def dp_solve(ctx, guide, w, sS, sE, eps, wsegs=None):
    """cheapest legal 45-degree path from the start set to the end set inside the corridor of half-width eps round guide"""
    gl = LineString(guide); lines = set()
    for a, b in zip(guide, guide[1:]):
        ln = line_of(a, b)
        if ln is not None: lines.add(ln)
    for sp in (sS, sE):
        for p, pen in sp['pts']:
            if sp.get('req') is not None: lines.add(lines_through(p)[sp['req'] % 4])
            else: lines.update(lines_through(p))
        if sp.get('tol') is not None: lines.update(lines_through(sp['tol']))
        if sp.get('padc') is not None: C = sp['padc'][0]; lines.add((0, C[1])); lines.add((2, C[0]))
    if sS.get('tol') is not None and sE.get('tol') is not None:      # both ends may sit 0.03 mm off their centre: a line half-way
        for (k, c1), (k2, c2) in zip(lines_through(sS['tol']), lines_through(sE['tol'])):
            if 0 < abs(c1 - c2) <= (60000 if k in (0, 2) else 84000): lines.add((k, (c1 + c2) // 2)); lines.add((k, (c1 + c2) // 2 + 1))
    if len(guide) <= 18:
        for p in guide[1:-1]: lines.update(lines_through(p))
    lines |= chamfer_lines(guide, w)
    L = sorted(lines); cand = set()
    for i in range(len(L)):
        for j in range(i + 1, len(L)):
            X = isect(L[i], L[j])
            if X is not None: cand.add(X)
    for sp in (sS, sE):
        for p, pen in sp['pts']: cand.add(p)
    cand = sorted(cand)
    arr = np.array(cand, dtype=float); P = shapely.points(arr[:, 0], arr[:, 1])
    dd = shapely.distance(gl, P); keep = dd <= eps + 1
    spts = {p for p, pen in sS['pts']}; epts = {p: pen for p, pen in sE['pts']}
    nodes = [c for c, k in zip(cand, keep) if k or c in spts or c in epts]
    if not nodes: return None
    arr = np.array(nodes, dtype=float); P = shapely.points(arr[:, 0], arr[:, 1]); gpar = shapely.line_locate_point(gl, P)
    idx = {p: i for i, p in enumerate(nodes)}
    # start / end sets
    starts = {}; ends = {}
    for which, sp, dst in ((0, sS, starts), (1, sE, ends)):
        for p, pen in sp['pts']: dst[idx[p]] = pen
        if sp.get('tol') is not None:
            for i, p in enumerate(nodes):
                if i not in dst and dist(p, sp['tol']) <= END_TOL: dst[i] = P_TOL
        if sp.get('padc') is not None:
            C, inset = sp['padc']
            for i, p in enumerate(nodes):
                if i not in dst and (p[0] == C[0] or p[1] == C[1]) and inset.covers(Point(p)): dst[i] = 0.0 if p == C else P_OFFC
        if sp.get('free') is not None:
            q, poly = sp['free']
            for i, p in enumerate(nodes):
                if i not in dst and dist(p, q) <= FREE_R and poly.covers(Point(p)): dst[i] = 0.15 + 2.0 * dist(p, q) * MM
    npn = [ctx.nodepen(p) for p in nodes]
    # edges along every line
    adj = collections.defaultdict(list)
    byline = collections.defaultdict(list)
    for i, p in enumerate(nodes):
        for ln in lines_through(p):
            if ln in lines: byline[ln].append(i)
    for ln, li in byline.items():
        if len(li) < 2: continue
        li.sort(key=lambda i: lparam(ln, nodes[i])); m = len(li)
        okv = []; dev = []
        for a, b in zip(li, li[1:]):
            pa, pb = nodes[a], nodes[b]; Ls = dist(pa, pb); n = max(1, int(math.ceil(Ls / 25000)))
            ts = np.linspace(0, 1, n + 1)
            sp_ = shapely.points(pa[0] + (pb[0] - pa[0]) * ts, pa[1] + (pb[1] - pa[1]) * ts)
            dv = shapely.distance(gl, sp_); okv.append(float(dv.max()) <= eps + 1); dev.append(float((dv[:-1] + dv[1:]).sum()) / 2 / n * Ls)
            if wsegs is not None and okv[-1]:                 # mixed widths: this stretch with the width of the nearest old piece
                mpt = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2); wi = min(wsegs, key=lambda s_: seg_pt(mpt, s_[0], s_[1])[0])[2]
                if not ctx.clear(pa, pb, wi): okv[-1] = False
        for a in range(m):
            mx = 0.0
            for b in range(a + 1, m):
                if not okv[b - 1]: break
                mx += dev[b - 1]; u, v = li[a], li[b]; pu, pv = nodes[u], nodes[v]; Ls = dist(pu, pv)
                if Ls < 1: continue
                dg = gpar[v] - gpar[u]; lim = 3 * Ls + 4 * eps + 200000
                d = dir8(pu, pv)
                we = w
                if wsegs is not None:
                    mpt = ((pu[0] + pv[0]) / 2, (pu[1] + pv[1]) / 2); we = min(wsegs, key=lambda s_: seg_pt(mpt, s_[0], s_[1])[0])[2]
                pen = short_pen(ctx, pu, pv, Ls, we)
                if pen == INF: continue
                ce = Ls * MM + pen + KAREA * mx * MM * MM
                if -2 * eps - 1000 <= dg <= lim: adj[u].append((v, d, ce))
                if -2 * eps - 1000 <= -dg <= lim: adj[v].append((u, (d + 4) % 8, ce))
    # Dijkstra over (node, direction of arrival)
    pq = []; best = {}; par = {}; cnt = 0
    for i, pen in starts.items():
        heapq.heappush(pq, (pen, cnt, i, -1, None)); cnt += 1
    fin = None
    while pq:
        c, _, u, din, pr = heapq.heappop(pq)
        if fin is not None and c >= fin[0]: break
        if (u, din) in best: continue
        best[(u, din)] = c; par[(u, din)] = pr
        if u in ends and din != -1:
            if sE.get('req') is None or din == sE['req']:
                tot = c + ends[u] + sE['forbid'].get((din + 4) % 8, 0.0)
                if fin is None or tot < fin[0]: fin = (tot, (u, din))
        for v, d, ce in adj.get(u, ()):
            if (v, d) in best: continue
            if din == -1:
                if sS.get('req') is not None and d != sS['req']: continue
                c2 = c + sS['forbid'].get(d, 0.0)
            else:
                t = turn8(din, d)
                if t == 0 or t >= 3: continue
                pn = npn[u]
                if pn: pn = ctx.bendpen(nodes[u], nodes[pr[0]] if pr[1] == -1 else None, nodes[v] if v in ends else None)
                elif t == 2 and (ctx.stick(nodes[u], nodes[v], w) or ctx.stick(nodes[u], nodes[pr[0]], w)): pn = P_STICK
                c2 = c + pn + (C45 if t == 1 else C90)
            if wsegs is None and not ctx.clear(nodes[u], nodes[v], w): continue
            heapq.heappush(pq, (c2 + ce, cnt, v, d, (u, din))); cnt += 1
    if fin is None: return None
    path = []; st = fin[1]
    while st is not None: path.append(nodes[st[0]]); st = par[st]
    path.reverse()
    return path


# ------------------------------------------------------------------------------------------ zones of a chain
def sib_forbid(g, ch, end):
    f = {}
    if g is None: return f
    me = ch.pts[0] if end == 0 else ch.pts[-1]
    for c2, e2 in g.arms:
        if (c2 is ch and e2 == end) or c2.pts is None or c2.dead or len(c2.pts) < 2: continue
        p = c2.pts[0] if e2 == 0 else c2.pts[-1]; q = c2.pts[1] if e2 == 0 else c2.pts[-2]; rl = c2.real[0] if e2 == 0 else c2.real[-1]
        if p != me or not rl: continue
        d = dir8(p, q)
        if d is None: continue
        for o in range(8):
            t = turn8(o, d)
            if t == 0: f[o] = max(f.get(o, 0), P_OVER)
            elif t == 1: f[o] = max(f.get(o, 0), P_ACUTE)
    return f

def end_spec(ctx, ch, end):
    g = ch.g[end]; pt = ch.pts[0] if end == 0 else ch.pts[-1]
    sp = dict(pts=[(pt, 0.0)], req=None, forbid=sib_forbid(g, ch, end), tol=None, padc=None, free=None)
    if g.infill is not None: sp['free'] = (g.T, g.infill)
    if g.kind in ('via', 'pad') and len(g.arms) == 1: sp['tol'] = g.centre
    if g.bigpad is not None:
        C, inset = g.bigpad
        good = (abs(pt[0] - C[0]) <= END_TOL or abs(pt[1] - C[1]) <= END_TOL) and inset.covers(Point(pt))
        sp['pts'] = [(pt, 0.0 if good else P_BADEND)]
        if not good: sp['padc'] = g.bigpad
    return sp

def dirty_runs(ctx, ch):
    pts, ws, real = ch.pts, ch.ws, ch.real; n = len(pts) - 1; bad = [False] * n; RL = run_lengths(pts, ws)
    for k in range(n):
        a, b = pts[k], pts[k + 1]
        if not real[k] or not on45(a, b) or short_pen(ctx, a, b, RL[k], ws[k]): bad[k] = True
    for k in range(1, n):
        d1, d2 = dir8(pts[k - 1], pts[k]), dir8(pts[k], pts[k + 1])
        if d1 is not None and d2 is not None and (turn8(d1, d2) >= 3 or turn8(d1, d2) == 0 and ws[k - 1] == ws[k]): bad[k - 1] = bad[k] = True
        if ctx.nodepen(pts[k]) and not (d1 is not None and d1 == d2): bad[k - 1] = bad[k] = True
    for end in (0, 1):
        g = ch.g[end]
        if g.bigpad is not None and end_spec(ctx, ch, end)['pts'][0][1] > 0: bad[0 if end == 0 else n - 1] = True
        f = sib_forbid(g, ch, end); d = dir8(pts[0], pts[1]) if end == 0 else dir8(pts[-1], pts[-2])
        if d is not None and f.get(d, 0): bad[0 if end == 0 else n - 1] = True
    runs = []; k = 0
    while k < n:
        if bad[k]:
            j = k
            while j + 1 < n and (bad[j + 1] or (j + 2 < n and bad[j + 2])): j += 1
            runs.append((k, j)); k = j + 1
        else: k += 1
    return runs

def validate(ctx, ch, old, new, w):
    """same channel and own-net test for a replacement of the sub-path old by new"""
    R = region(old, new)
    newL = LineString(new); oldL = LineString(old) if len(old) >= 2 and len(set(old)) > 1 else Point(old[0])
    if R is not None:
        for it in ctx.B.query(ctx.l, R, 1000):
            if it.net == ctx.net and it.net is not None: continue
            if R.intersects(it.geom): return 'would pass %s %s' % (it.kind, it.name)
    excl = ch.excl | ch.g[0].nodes | ch.g[1].nodes
    for a, b, w2 in ctx.own:
        if a in excl or b in excl: continue
        gm = LineString([a, b]); dn = newL.distance(gm)
        if dn < (w + w2) / 2 + 150000 - 500 and dn < oldL.distance(gm) - 500: return 'own net too close'
        if R is not None and R.intersects(gm): return 'would pass own net'
    return None

def solve_zone(ctx, ch, a, b):
    pts, ws = ch.pts, ch.ws; n = len(pts) - 1; best = None; why = 'no path'
    for grow in range(3):
        i0 = max(0, a - 1 - grow); i1 = min(n - 1, b + 1 + grow)
        if grow and (i0, i1) == last: break
        last = (i0, i1)
        guide = pts[i0:i1 + 2]; w = max(ws[i0:i1 + 1])
        sS = end_spec(ctx, ch, 0) if i0 == 0 else dict(pts=[(pts[i0], 0.0)], req=dir8(pts[i0], pts[i0 + 1]), forbid={})
        sE = end_spec(ctx, ch, 1) if i1 == n - 1 else dict(pts=[(pts[i1 + 1], 0.0)], req=dir8(pts[i1], pts[i1 + 1]), forbid={})
        if (i0 > 0 and sS['req'] is None) or (i1 < n - 1 and sE['req'] is None): continue
        allreal = all(ch.real[i0:i1 + 1])
        oc = path_eval(ctx, guide, ws[i0:i1 + 1], sS, sE) if allreal else (INF, 0, 0)
        zw = ws[i0:i1 + 1]; wsegs = None
        if len(set(zw)) > 1: wsegs = [(p_, q_, w_) for p_, q_, w_, r_ in zip(guide, guide[1:], zw, ch.real[i0:i1 + 1]) if r_] or None
        key = (tuple(guide), tuple(zw), repr(sS), repr(sE))
        if key in ctx.zcache: res = ctx.zcache[key]
        else:
            res = None; lastp = None
            for eps, nj in [(e_, m_) for e_ in ctx.sched for m_ in (False, True)]:
                if nj and (res is None or res[0] == 0 or eps > ctx.nojog_max or lastp is None): continue
                ctx.nojog = nj
                try: p = dp_solve(ctx, guide, w, sS, sE, eps, wsegs)
                finally: ctx.nojog = False
                if not nj: lastp = p
                if p is None or (nj and p == lastp): continue
                p = clean(p)
                wl = w
                if wsegs is not None: wl = [min(wsegs, key=lambda s_: seg_pt(((x[0] + y[0]) / 2, (x[1] + y[1]) / 2), s_[0], s_[1])[0])[2] for x, y in zip(p, p[1:])]
                cst, npen, n90 = path_eval(ctx, p, wl, sS, sE)
                if cst == INF: continue
                if p == clean(guide): cand = (npen, cst, p, n90)
                elif plen(p) > MAXLEN * plen(guide) + 50000: why = 'only a detour possible'; continue
                else:
                    v = validate(ctx, ch, guide if guide[-1] == p[-1] and guide[0] == p[0] else [p[0]] + guide + [p[-1]], p, w)
                    if v is not None: why = v; continue
                    gl = LineString(guide)
                    cand = (npen, cst + KAREA * area_dev(gl, p) * MM * MM, p, n90)
                if DEBUG: print('   ZONE eps', eps, 'grow', grow, 'npen', cand[0], 'cost %.3f' % cand[1], [(x * MM, y * MM) for x, y in p])
                if res is None or cand[:2] < res[:2]: res = cand
                if cand[0] == 0 and eps >= ctx.soft and cand[3] == 0: break
            ctx.zcache[key] = res
        if res is None: continue
        if oc[0] != INF and (oc[1], oc[0]) <= (res[0], res[1] + 1e-9):
            if oc[1] == 0: return None, 'already best'
            why = 'no better path'; continue
        c = (res[0], grow, res[1], i0, i1, res[2])
        if best is None or c[:3] < best[:3]: best = c
        if res[0] == 0: break
    if best is None: return None, why
    return best, None

def new_widths(ctx, old_pts, old_ws, old_real, new_pts):
    """widths of the new pieces (each takes the width of the nearest old piece); a width change that was hidden in a
    pad or via stays there: the new piece is split at that place. Returns (points, widths)."""
    if len(set(old_ws)) == 1: return list(new_pts), [old_ws[0]] * (len(new_pts) - 1)
    npts = list(new_pts)
    for k in range(1, len(old_pts) - 1):
        if old_ws[k - 1] == old_ws[k] or not (old_real[k - 1] and old_real[k]): continue
        c = old_pts[k]
        ex = [i for i, (a, b) in enumerate(zip(npts, npts[1:])) if interior_exact(c, a, b)]
        if ex:
            if min(dist(c, npts[ex[0]]), dist(c, npts[ex[0] + 1])) >= 100000: npts.insert(ex[0] + 1, c)
            continue
        if ctx.via_at(c) is None and ctx.pad_at(c) is None: continue
        best = None
        for i, (a, b) in enumerate(zip(npts, npts[1:])):
            d, t = seg_pt(c, a, b)
            if best is None or d < best[0]: best = (d, t, i)
        d, t, i = best
        if d > 150000: continue
        a, b = npts[i], npts[i + 1]; n = max(abs(b[0] - a[0]), abs(b[1] - a[1])); m = int(round(t * n))
        if m <= 0 or m >= n: continue
        q = (a[0] + sgn(b[0] - a[0]) * m, a[1] + sgn(b[1] - a[1]) * m)
        if not ctx.hidden(q, c) or min(dist(q, a), dist(q, b)) < 50000: continue
        npts.insert(i + 1, q)
    segs = [(a, b, w) for a, b, w, r in zip(old_pts, old_pts[1:], old_ws, old_real) if r] or [(a, b, w) for a, b, w in zip(old_pts, old_pts[1:], old_ws)]
    out = []
    for a, b in zip(npts, npts[1:]):
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        out.append(min(segs, key=lambda s_: seg_pt(m, s_[0], s_[1])[0])[2])
    oc = sum(1 for x, y in zip(old_ws, old_ws[1:]) if x != y)
    while sum(1 for x, y in zip(out, out[1:]) if x != y) > oc:
        for k in range(1, len(out)):
            if out[k] != out[k - 1]: out[k] = max(out[k], out[k - 1]); out[k - 1] = out[k]; break
    return npts, out

def fix_chain(ctx, ch):
    if ch.frozen or ch.dead or len(ch.pts) < 2: return False
    failed = {}; changed = False
    for it in range(60):
        runs = dirty_runs(ctx, ch); todo = None
        for a, b in runs:
            k = tuple(ch.pts[max(0, a - 1):b + 3])
            if k not in failed: todo = (a, b, k); break
        if todo is None: break
        a, b, k = todo
        best, why = solve_zone(ctx, ch, a, b)
        if best is None: failed[k] = why; continue
        npen, grow, cst, i0, i1, p = best
        p, nw = new_widths(ctx, ch.pts[i0:i1 + 2], ch.ws[i0:i1 + 1], ch.real[i0:i1 + 1], p)
        if len(set(nw)) > 1 and ctx.B.nc.get(ctx.net, 'Default') in ('HighCurrent', 'Power', 'GND', 'GateDrive'):   # never lengthen a neck
            wm = max(ch.ws[i0:i1 + 1])
            n0 = sum(dist(x, y) for x, y, w_, r_ in zip(ch.pts[i0:i1 + 2], ch.pts[i0 + 1:i1 + 2], ch.ws[i0:i1 + 1], ch.real[i0:i1 + 1]) if w_ < wm and r_)
            n1 = sum(dist(x, y) for x, y, w_ in zip(p, p[1:], nw) if w_ < wm)
            if n1 > n0 + 100000:
                if all(ctx.clear(x, y, wm) for x, y in zip(p, p[1:])): nw = [wm] * len(nw)
                else: failed[k] = 'would lengthen a neck'; continue
        ch.pts = ch.pts[:i0] + p + ch.pts[i1 + 2:]; ch.ws = ch.ws[:i0] + nw + ch.ws[i1 + 1:]; ch.real = ch.real[:i0] + [True] * len(nw) + ch.real[i1 + 1:]
        # merge collinear neighbours of equal width
        k2 = 1
        while k2 < len(ch.pts) - 1:
            d1, d2 = dir8(ch.pts[k2 - 1], ch.pts[k2]), dir8(ch.pts[k2], ch.pts[k2 + 1])
            if d1 is not None and d1 == d2 and ch.ws[k2 - 1] == ch.ws[k2] and ch.real[k2 - 1] and ch.real[k2]:
                del ch.pts[k2]; del ch.ws[k2]; del ch.real[k2]
            else: k2 += 1
        changed = True
        if len(ch.pts) < 2: break
    ch.failed = failed
    return changed

def chain_cost(ctx, ch):
    if ch.dead or len(ch.pts) < 2: return 0.0
    for k, (a, b) in enumerate(zip(ch.pts, ch.pts[1:])):
        if not ch.real[k] and not on45(a, b): return 1e6
    c = 0.0; dprev = None
    for k, (a, b) in enumerate(zip(ch.pts, ch.pts[1:])):
        d = dir8(a, b); L = dist(a, b); c += L * MM
        if d is None: c += 5.0; dprev = None; continue
        c += min(short_pen(ctx, a, b, L, ch.ws[k]), 8.0)
        if dprev is not None:
            t = turn8(dprev, d); c += (0 if t == 0 else C45 if t == 1 else C90 if t == 2 else 5.0) + ctx.bendpen(a, ch.pts[0] if k == 1 else None, ch.pts[-1] if k == len(ch.pts) - 2 else None)
        dprev = d
    for end in (0, 1):
        f = sib_forbid(ch.g[end], ch, end); d = dir8(ch.pts[0], ch.pts[1]) if end == 0 else dir8(ch.pts[-1], ch.pts[-2])
        if d is not None: c += f.get(d, 0.0)
    return c


# ------------------------------------------------------------------------------------------ one connected group
def junction_candidates(ctx, g):
    arms = []
    for ch, end in g.arms:
        core = ch.core if end == 0 else ch.core[::-1]; cw = ch.cws if end == 0 else ch.cws[::-1]; ln = []; acc = 0
        for k, (a, b) in enumerate(zip(core, core[1:])):
            l_ = line_of(a, b)
            if l_ is not None and dist(a, b) >= cw[k] - 1 and l_ not in ln: ln.append(l_)
            acc += dist(a, b)
            if len(ln) >= 3 or acc > 2500000: break
        far = ch.g[1 - end]
        if not ln and far.T is not None and ch.core_len < 1500000: ln = lines_through(far.T)
        arms.append(ln)
    wmax = max(max(ch.cws) for ch, e in g.arms); R = 0.6 * wmax + 50000
    cand = set(g.nodes)
    for i in range(len(arms)):
        for j in range(i + 1, len(arms)):
            for l1 in arms[i]:
                for l2 in arms[j]:
                    X = isect(l1, l2)
                    if X is not None and min(dist(X, n) for n in g.nodes) <= R: cand.add(X)
    cx = sum(n[0] for n in g.nodes) / len(g.nodes); cy = sum(n[1] for n in g.nodes) / len(g.nodes)
    def score(T):
        k = sum(1 for ln in arms if any(l_ in ln for l_ in lines_through(T)))
        return (-k, dist(T, (cx, cy)), T)
    return sorted(cand, key=score)[:5]

def attempt(ctx, frozen):
    B, net, l = ctx.B, ctx.net, ctx.l; log = ctx.log
    # ---- A: pieces
    pieces = []; seen = {}
    for t in ctx.tracks:
        a, b = (t['x1'], t['y1']), (t['x2'], t['y2'])
        if a == b: continue
        k = frozenset((a, b))
        if k in seen:
            if t['w'] > seen[k][2]: seen[k][2] = t['w']
            continue
        seen[k] = [a, b, t['w'], True]; pieces.append(seen[k])
    # ---- B: split where another end lies exactly on a piece
    def split_exact(pieces):
        ch_ = True
        while ch_:
            ch_ = False; nodes = {p for s in pieces for p in s[:2]}
            for s in pieces:
                a, b = s[0], s[1]; x0, x1 = min(a[0], b[0]), max(a[0], b[0]); y0, y1 = min(a[1], b[1]), max(a[1], b[1])
                hit = [p for p in nodes if x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and interior_exact(p, a, b)]
                if hit:
                    hit.sort(key=lambda p: dist(p, a)); seq = [a] + hit + [b]; pieces.remove(s)
                    for p, q in zip(seq, seq[1:]): pieces.append([p, q, s[2], s[3]])
                    ch_ = True; break
            if ch_:
                sn = {}; out = []
                for s in pieces:
                    k = frozenset(s[:2])
                    if k in sn: sn[k][2] = max(sn[k][2], s[2]); continue
                    sn[k] = s; out.append(s)
                pieces[:] = out
    split_exact(pieces)
    # ---- C: loose ends that only touch copper
    def adjacency():
        adj = collections.defaultdict(list)
        for s in pieces: adj[s[0]].append((s[1], s)); adj[s[1]].append((s[0], s))
        return adj
    def terminal(p):
        v = ctx.via_at(p)
        if v is not None: return ('v', v['id'])
        q = ctx.pad_at(p)
        return ('p', id(q[1])) if q is not None else None
    def gdist(adj, p, targets, lim, skip=None):
        pq = [(0, p)]; seen_ = set()
        while pq:
            d, q = heapq.heappop(pq)
            if q in seen_: continue
            seen_.add(q)
            if q in targets: return d
            if d > lim: return None
            for r, s in adj[q]:
                if s is skip or r in seen_: continue
                heapq.heappush(pq, (d + dist(q, r), r))
        return None
    fixed_nodes = set(); frozen_pieces = []; vlinks = {}; frozen_by = {}
    done = set()
    tc_ = {}
    def tcache(p):
        if p not in tc_: tc_[p] = terminal(p)
        return tc_[p]
    def near_own(p, r):
        P_ = Point(p)
        return any(pg.distance(P_) <= r for pg, nm in ctx.fills) or any(pg.distance(P_) <= r for pg, pd in ctx.pads) or any(dist(p, (v['x'], v['y'])) <= v['d'] / 2 + r for v in ctx.vias)
    for rnd in range(400):
        adj = adjacency(); act = None
        for p in sorted(adj, key=lambda p_: (tcache(p_) is not None, p_)):      # loose ends first, then the nodes inside pads and vias
            if p in done: continue
            tp = tcache(p); cons = []
            for s in pieces:
                if s[0] == p or s[1] == p: continue
                d, t = seg_pt(p, s[0], s[1])
                if d <= s[2] / 2 and not (tp is not None and (terminal(s[0]) == tp or terminal(s[1]) == tp)): cons.append((d, s))
            deg = len(adj[p])
            if not cons:
                # a short overhang past a junction that ends nowhere (KiCad calls it dangling once the junction has a node)
                if deg == 1 and tp is None:
                    q, s0 = adj[p][0]
                    if s0[3] and dist(p, q) <= 500000 and len(adj[q]) >= 3 and not near_own(p, s0[2] / 2 + 100000):
                        act = ('dead', s0, p); break
                done.add(p); continue
            cons.sort(key=lambda c: c[0]); ess = None
            for d, s in cons:
                if gdist(adj, p, {s[0], s[1]}, 1000000) is None: ess = (d, s); break
            if ess is None:
                realp = [(q_, s_) for q_, s_ in adj[p] if s_[3]]
                if len(realp) == 1 and tp is None:               # micro spur inside other copper
                    q, s0 = realp[0]; lone = deg == 1
                    qok = len(adj[q]) >= 3 or (tcache(q) is not None and len(adj[q]) >= 2)      # q does not become a new loose end
                    def covered(rr):
                        gm0 = LineString([p, q]); near = [LineString([x[0], x[1]]).buffer(x[2] / 2) for x in pieces if x is not s0 and x[0] != x[1] and LineString([x[0], x[1]]).distance(gm0) <= x[2] / 2 + s0[2]]
                        near += [pg for pg, pd in ctx.pads] + [Point(v['x'], v['y']).buffer(v['d'] / 2) for v in ctx.vias]
                        if rr is None:                           # copper that would go: at most 0.02 mm2
                            return bool(near) and gm0.buffer(s0[2] / 2).difference(unary_union(near)).area <= 2e10
                        return bool(near) and unary_union(near).covers(gm0.buffer(rr))
                    nofill = not any(pg.distance(Point(p)) <= s0[2] / 2 + 100000 for pg, nm in ctx.fills)
                    # (not wider than the copper it lies in, and next to no copper outside it: no wide copper is taken away)
                    if lone and s0[3] and nofill and s0[2] <= max(c_[1][2] for c_ in cons) + 1000 and dist(p, q) <= 1.5 * max(s0[2], cons[0][1][2]) and (qok or (len(adj[q]) >= 2 and any(q in (c_[1][0], c_[1][1]) for c_ in cons))) and covered(None):
                        act = ('spur', s0); break
                    # a longer piece that lies wholly in the copper of the other pieces (a near-duplicate): same
                    # ... or q is a plain corner that itself lies in the copper of another piece: the piece p-q runs beside
                    # that copper (two arms on top of each other before a junction); q then joins it with a proper T
                    qcont = len(adj[q]) == 2 and tcache(q) is None and any(x is not s0 and x[3] and q not in (x[0], x[1]) and seg_pt(q, x[0], x[1])[0] <= x[2] / 2 for x in pieces)
                    if s0[3] and ((qok and lone) or qcont) and nofill:
                        if covered(max(s0[2] / 2 - 10000, 1000) if (qok and lone) else s0[2] / 4):
                            act = ('spur', s0, p, q); break
                done.add(p); continue
            d, s = ess
            real_ = [s_ for q_, s_ in adj[p] if s_[3]]       # links made here do not count: the end of one real piece is still a loose end
            if (len(real_) >= 2 and tp is None) or ('link', frozenset([p])) in frozen: fixed_nodes.add(p); frozen_pieces.append(s); frozen_by.setdefault(p, []).append(s); done.add(p); continue
            wp = (real_ or [adj[p][0][1]])[0][2]; e = min((s[0], s[1]), key=lambda q: dist(p, q))
            if dist(p, e) <= 0.75 * max(s[2], wp): act = ('link', p, e, wp); break
            dx, dy = s[1][0] - s[0][0], s[1][1] - s[0][1]; t = ((p[0] - s[0][0]) * dx + (p[1] - s[0][1]) * dy) / (dx * dx + dy * dy)
            f = (int(round(s[0][0] + t * dx)), int(round(s[0][1] + t * dy)))
            if f == s[0] or f == s[1]: act = ('link', p, f, wp); break
            act = ('foot', p, f, s, wp); break
        if act is None: break
        if act[0] == 'spur':
            pieces.remove(act[1]); log.append('spur removed (%.4f, %.4f)' % (act[1][0][0] * MM, act[1][0][1] * MM))
            if len(act) == 4:                               # the links of the end that went, and q is looked at again as a loose end
                p_, q_ = act[2], act[3]
                for x in [x for x in pieces if not x[3] and p_ in (x[0], x[1])]:
                    pieces.remove(x); vlinks.pop(frozenset((x[0], x[1])), None); done.discard(x[0]); done.discard(x[1])
                done.discard(q_)
                if q_ in fixed_nodes:
                    fixed_nodes.discard(q_)
                    for fp in frozen_by.pop(q_, []):
                        if fp in frozen_pieces: frozen_pieces.remove(fp)
        elif act[0] == 'dead': pieces.remove(act[1]); log.append('dead overhang removed, %.3f mm, free end was at (%.4f, %.4f)' % (dist(act[1][0], act[1][1]) * MM, act[2][0] * MM, act[2][1] * MM))
        elif act[0] == 'link':
            if act[1] != act[2]: pieces.append([act[1], act[2], act[3], False]); vlinks[frozenset((act[1], act[2]))] = act[1]
            done.add(act[1])
        else:
            _, p, f, s, wp = act; pieces.remove(s); pieces.append([s[0], f, s[2], s[3]]); pieces.append([f, s[1], s[2], s[3]])
            if p != f: pieces.append([p, f, wp, False]); vlinks[frozenset((p, f))] = p
            done.add(p)
    adj = adjacency()
    ctx.own = ctx.others + [(s[0], s[1], s[2]) for s in pieces if s[3]]
    # ---- D: anchors
    grp = {}; groups = []
    def mk(kind, nodes):
        g = Group(kind, nodes); groups.append(g)
        for n in nodes: grp[n] = g
        return g
    def fixed(n):
        if n not in grp:
            g = mk('fixed', [n]); g.T = n
        return grp[n]
    lock = set()
    for k_ in frozen:
        if k_[0] == 'chainlock': lock |= k_[1]
    for p in lock:
        if p in adj: fixed(p)
    viag = collections.defaultdict(list); padn = {}
    for p in adj:
        if p in lock: continue
        v = ctx.via_at(p)
        if v is not None: viag[v['id']].append((p, v)); continue
        q = ctx.pad_at(p)
        if q is not None: padn[p] = q; continue
        if len(adj[p]) == 1 and adj[p][0][1][3]:           # a loose end whose copper only touches a via or pad of the net
            r = adj[p][0][1][2] / 2 - 10000; P_ = Point(p); q_ = adj[p][0][0]; vq = ctx.via_at(q_); pq = ctx.pad_at(q_)
            for v in ctx.vias:                             # (not a stub that starts in that same via or pad)
                if dist(p, (v['x'], v['y'])) <= v['d'] / 2 + r and v is not vq: viag[v['id']].append((p, v)); break
            else:
                for pg, pd in ctx.pads:
                    if pg.distance(P_) <= r and not (pq is not None and pq[1] is pd): padn[p] = (pg, pd); break
    for vid, lst in viag.items():
        v = lst[0][1]; C = (v['x'], v['y']); nodes = [p for p, _ in lst]
        if ('via', frozenset(nodes)) in frozen:
            for n in nodes: fixed(n)
            continue
        g = mk('via', nodes); g.centre = C
        near = min(nodes, key=lambda n: dist(n, C)); g.T = near if dist(near, C) <= END_TOL else C
    # pad groups: nodes inside one pad joined by pieces that stay inside it
    par = {p: p for p in padn}
    def find(p):
        while par[p] != p: par[p] = par[par[p]]; p = par[p]
        return p
    for s in pieces:
        if s[0] in padn and s[1] in padn and padn[s[0]][1] is padn[s[1]][1]: par[find(s[0])] = find(s[1])
    pg_ = collections.defaultdict(list)
    for p in padn: pg_[find(p)].append(p)
    D1 = min(500000, ctx.maxexc - 20000); ppt = collections.defaultdict(list)
    for root, nodes in list(pg_.items()):                  # all the parts of one pad that go to its centre are one anchor
        pgon, pd = padn[root]; C = (pd['x'], pd['y'])
        if min(dist(n, C) for n in nodes) <= D1: ppt[id(pd)].append(root)
    for lst in ppt.values():
        for r_ in lst[1:]: pg_[lst[0]] += pg_.pop(r_)
    for root, nodes in pg_.items():
        pgon, pd = padn[root]; C = (pd['x'], pd['y']); dmin = min(dist(n, C) for n in nodes)
        if dmin <= D1 and ('pad', frozenset(nodes)) not in frozen:
            g = mk('pad', nodes); g.centre = C; g.pad = pd
            near = min(nodes, key=lambda n: dist(n, C)); g.T = near if dist(near, C) <= END_TOL else C
        else:
            for n in nodes:
                g = fixed(n)
                if len(adj[n]) == 1 and ('big', frozenset([n])) not in frozen:
                    w = adj[n][0][1][2]; inset = pgon.buffer(-w / 2)
                    if not inset.is_empty: g.bigpad = (C, inset); g.pad = pd
    for p in fixed_nodes: fixed(p)
    for s in frozen_pieces:
        for p in s[:2]:
            if p in adj: fixed(p)
    # junctions
    raw = [p for p in adj if p not in grp and len(adj[p]) >= 3]
    jpar = {p: p for p in raw}; jextra = collections.defaultdict(set)
    def jfind(p):
        while jpar[p] != p: jpar[p] = jpar[jpar[p]]; p = jpar[p]
        return p
    rawset = set(raw); into_term = {}
    for p in raw:
        wmax = max(s[2] for q, s in adj[p])
        for q, s in adj[p]:
            path = [p, q]; acc = dist(p, q)
            while acc <= 1.25 * wmax:
                c = path[-1]
                if c in rawset:
                    if c != p: jpar[jfind(c)] = jfind(p); jextra[p].update(path[1:-1])
                    break
                if c in grp:
                    if grp[c].kind in ('via', 'pad') and acc <= 0.6 * wmax: into_term[p] = (grp[c], path[1:-1])
                    break
                if len(adj[c]) != 2: break
                nx = [r for r, s2 in adj[c] if r != path[-2]]
                if not nx: break
                path.append(nx[0]); acc += dist(c, nx[0])
    jg = collections.defaultdict(set)
    for p in raw: jg[jfind(p)].add(p); jg[jfind(p)].update(jextra[p])
    for root, nodes in jg.items():
        nodes = {n for n in nodes if n not in grp}
        tg = [into_term[p] for p in nodes if p in into_term]
        if tg and ('junc', frozenset(nodes)) not in frozen:
            g = tg[0][0]
            for n in list(nodes) + [x for x in tg[0][1] if x not in grp]: g.nodes.add(n); grp[n] = g
            continue
        if ('junc', frozenset(nodes)) in frozen:
            for n in nodes: fixed(n)
        else: mk('junc', nodes)
    for p in adj:
        if p in grp: continue
        if len(adj[p]) == 1:
            g = fixed(p); P_ = Point(p)
            for pg, nm in ctx.fills:                        # well inside a pour of the net: the end may move a little, staying well inside
                if pg.covers(P_):
                    ins = pg.buffer(-120000)
                    if ins.covers(P_): g.infill = ins
                    break
    # ---- E: chains
    used = set(); chains = []
    fz = {id(s) for s in frozen_pieces}
    for g in groups:
        for n in sorted(g.nodes):
            for m, s in adj[n]:
                if id(s) in used: continue
                if grp.get(m) is g:
                    used.add(id(s)); g.iadj[n].append(m); g.iadj[m].append(n)
                    if s[3]: g.iw[frozenset((n, m))] = s[2]
                    if g.kind == 'fixed': raise Retry(g.key, 'loop on a fixed node')
                    continue
                core = [n, m]; cws = [s[2]]; creal = [s[3]]; used.add(id(s)); isf = id(s) in fz
                while core[-1] not in grp:
                    c = core[-1]; nx = [(r, s2) for r, s2 in adj[c] if id(s2) not in used]
                    if len(nx) != 1: break
                    r, s2 = nx[0]; used.add(id(s2)); core.append(r); cws.append(s2[2]); creal.append(s2[3]); isf = isf or id(s2) in fz
                if core[-1] not in grp: raise Retry(g.key, 'chain ends nowhere')
                ch = Chain(core, cws, creal, g, grp[core[-1]]); ch.frozen = isf or (core[0] in lock and core[-1] in lock); chains.append(ch)
                g.arms.append((ch, 0)); grp[core[-1]].arms.append((ch, 1))
    loose = [s for s in pieces if id(s) not in used]             # closed loops without an anchor: keep as they are
    for g in groups:
        if g.kind in ('via', 'pad', 'junc'):
            for ch, e in g.arms:
                if ch.g[0] is ch.g[1]:
                    if ch.core_len <= 4 * max(ch.cws): ch.dead = True
                    else: raise Retry(g.key, 'loop through one anchor')
            g.arms = [(c, e) for c, e in g.arms if not c.dead]
    # two arms between the same two anchors whose copper lies on each other all the way: the shorter one stays
    pairs = collections.defaultdict(list)
    for ch in chains:
        if not ch.dead and ch.g[0] is not ch.g[1]: pairs[frozenset((id(ch.g[0]), id(ch.g[1])))].append(ch)
    for lst in pairs.values():
        if len(lst) < 2: continue
        lst.sort(key=lambda c: (-min(c.cws), c.core_len, c.core)); k0 = lst[0]; kl = LineString(k0.core)
        for c in lst[1:]:
            if max(c.cws) > min(k0.cws) + 1: continue       # never drop copper that is wider than what stays
            lim = 0.75 * (max(c.cws) + max(k0.cws)) / 2; smp = []
            for p_, q_ in zip(c.core, c.core[1:]):
                n_ = max(1, int(dist(p_, q_) // 50000))
                smp += [(p_[0] + (q_[0] - p_[0]) * i / n_, p_[1] + (q_[1] - p_[1]) * i / n_) for i in range(n_ + 1)]
            if max(kl.distance(Point(x)) for x in smp) <= lim and not c.frozen:
                c.dead = True; log.append('duplicate arm removed (%.4f, %.4f) to (%.4f, %.4f)' % (c.core[0][0] * MM, c.core[0][1] * MM, c.core[-1][0] * MM, c.core[-1][1] * MM))
    for g in groups: g.arms = [(c, e) for c, e in g.arms if not c.dead]
    for g in groups:
        if g.kind == 'junc' and len(g.arms) < 2: raise Retry(g.key, 'junction with fewer than two arms')
    # ---- F: junction points
    order = lambda g: sorted(g.arms, key=lambda ce: -ce[0].core_len)
    for g in groups:
        if g.kind != 'junc': continue
        best = None
        for T in junction_candidates(ctx, g):
            g.T = T; tot = 0.0
            for ch, e in g.arms: ch.build()
            for rep in range(2):
                for ch, e in order(g): fix_chain(ctx, ch)
            for ch, e in g.arms:
                tot += chain_cost(ctx, ch)
                if len(ch.pts) >= 2: tot += KAREA * area_dev(LineString(ch.core), ch.pts) * MM * MM
            if DEBUG:
                print('  JUNC T (%.4f,%.4f) total %.3f' % (T[0] * MM, T[1] * MM, tot))
                for ch, e in g.arms: print('     arm cost %.3f' % chain_cost(ctx, ch), [(x * MM, y * MM) for x, y in ch.pts], getattr(ch, 'failed', None) and list(ch.failed.values()))
            for ch, e in g.arms: ch.pts = None
            if best is None or tot < best[0] - 1e-9: best = (tot, T)
        g.T = None
        if best is None or best[0] >= 1e6: raise Retry(g.key, 'no junction point works')
        g.T = best[1]
    # ---- G: all chains
    for ch in chains: ch.build()
    todo = sorted([c for c in chains if not c.dead], key=lambda c: -c.core_len)
    for sweep in range(4):
        any_ = False
        for ch in todo:
            if fix_chain(ctx, ch): any_ = True
        if not any_: break
    for ch in todo:
        if len(ch.pts) < 2: continue
        for k, (a, b) in enumerate(zip(ch.pts, ch.pts[1:])):
            if not ch.real[k] and (not on45(a, b) or ch.frozen):
                if frozenset((a, b)) in vlinks: raise Retry(('link', frozenset([vlinks[frozenset((a, b))]])), 'loose end cannot be joined: %s' % (list(getattr(ch, 'failed', {}).values())[:1] or ['?'])[0])
                end = 0 if k < len(ch.pts) / 2 - 0.5 else 1; g = ch.g[end]
                if g.kind == 'fixed': g = ch.g[1 - end]
                raise Retry(g.key, 'arm cannot reach the anchor: %s' % (list(getattr(ch, 'failed', {}).values())[:1] or ['?'])[0])
    if os.environ.get('RT_DEBUG'):
        f = lambda p: '(%.4f,%.4f)' % (p[0] * MM, p[1] * MM)
        for g in groups: print('GROUP', g.kind, 'T', f(g.T) if g.T else None, 'nodes', [f(n) for n in sorted(g.nodes)], 'arms', len(g.arms), 'big' if g.bigpad else '')
        for ch in chains: print('CHAIN', 'dead' if ch.dead else '', 'frozen' if ch.frozen else '', ch.g[0].kind, ch.g[1].kind, 'core', [f(p) for p in ch.core], '->', [f(p) for p in (ch.pts or [])], [w_ * MM for w_ in (ch.ws or [])], getattr(ch, 'failed', None) and list(ch.failed.values()))
    # ---- emit
    final = []
    for ch in todo:
        for k, (a, b) in enumerate(zip(ch.pts, ch.pts[1:])):
            if a != b: final.append([a, b, ch.ws[k], True])
    for s in loose: final.append(list(s))
    for g in groups:                                       # internal pieces of held groups do not exist (fixed groups are single nodes)
        pass
    split_exact(final)
    resid = []
    for ch in todo:
        for k, why in getattr(ch, 'failed', {}).items():
            if why not in ('already best',): resid.append((k[len(k) // 2], why))
    return final, resid, groups, chains

def partition(ctx, pieces):
    """terminals (pads, vias, pours of the net) joined by the pieces, KiCad-like: an END POINT in copper joins"""
    uf = G.UF(); n = len(pieces)
    geoms = [LineString([a, b]) for a, b, w in pieces]
    tree = STRtree(geoms) if geoms else None
    for i, (a, b, w) in enumerate(pieces):
        uf.f(('t', i))
        for e in (a, b):
            pe = Point(e)
            for j in tree.query(pe.buffer(1300000)):
                if j != i and geoms[j].distance(pe) <= pieces[j][2] / 2 + 1: uf.u(('t', i), ('t', int(j)))
            for pg, pd in ctx.pads:
                if pg.covers(pe): uf.u(('t', i), 'pad:%s.%s' % (pd['ref'], pd['n']))
            for v in ctx.vias:
                if dist(e, (v['x'], v['y'])) <= v['d'] / 2 + 1: uf.u(('t', i), 'via:' + v['id'])
            for pg, name in ctx.fills:
                if pg.covers(pe): uf.u(('t', i), 'fill:' + name)
    for pg, pd in ctx.pads: uf.f('pad:%s.%s' % (pd['ref'], pd['n']))
    for v in ctx.vias:                                     # links that need no track (as in geolib.connectivity)
        pv = Point(v['x'], v['y']); uf.f('via:' + v['id'])
        for pg, pd in ctx.pads:
            if pg.covers(pv): uf.u('via:' + v['id'], 'pad:%s.%s' % (pd['ref'], pd['n']))
        for pg, name in ctx.fills:
            if pg.covers(pv): uf.u('via:' + v['id'], 'fill:' + name)
        for v2 in ctx.vias:
            if v2 is not v and dist((v['x'], v['y']), (v2['x'], v2['y'])) <= (v['d'] + v2['d']) / 4: uf.u('via:' + v['id'], 'via:' + v2['id'])
    for pg, pd in ctx.pads:
        for pg2, name in ctx.fills:
            if pg.intersects(pg2): uf.u('pad:%s.%s' % (pd['ref'], pd['n']), 'fill:' + name)
    comp = collections.defaultdict(set)
    for k in list(uf.p): comp[uf.f(k)].add(k)
    terms = [frozenset(x for x in c if isinstance(x, str)) for c in comp.values()]
    return [t for t in terms if t], sum(1 for t in terms if not t)

def process_component(ctx):
    frozen = set(); why = 'too many retries'
    for att in range(30):
        ctx.zcache.clear()
        try:
            res = attempt(ctx, frozen)
        except Retry as r:
            ctx.log.append('held as it is: %s group at (%.4f, %.4f): %s' % (r.key[0], min(r.key[1])[0] * MM, min(r.key[1])[1] * MM, r.why))
            if r.key in frozen: return None, 'retry loop'
            frozen.add(r.key)
            if r.key[0] in ('fixed',): frozen.add(('big', r.key[1]))
            continue
        out, why, bad = check_component(ctx, res)
        if out is not None: return out, None
        # the chains that hold the offending pieces or terminals stay as they are; try again
        chains = res[3]; hit = []
        for ch in chains:
            if ch.dead or ch.frozen or not ch.pts or len(ch.pts) < 2: continue
            for a, b in bad:
                if b is None:
                    if any(a(n) for n in ch.core): hit.append(ch); break
                else:
                    on = lambda x: any(x == p or x == q or interior_exact(x, p, q) for p, q in zip(ch.pts, ch.pts[1:]))
                    if on(a) and on(b): hit.append(ch); break
        new = [('chainlock', frozenset(ch.core)) for ch in hit if ('chainlock', frozenset(ch.core)) not in frozen]
        if not new: return None, why
        for k in new: frozen.add(k)
        ctx.log.append('chain(s) at %s kept as they are: %s' % (', '.join('(%.4f, %.4f)' % (min(k[1])[0] * MM, min(k[1])[1] * MM) for k in new), why))
    return None, why

def check_component(ctx, res):
    """(result, None, None) or (None, reason, [(a, b) offending new piece | (test, None) for a lost terminal])"""
    final, resid, groups, chains = res
    oldk = collections.defaultdict(list)
    for t in ctx.tracks: oldk[(frozenset(((t['x1'], t['y1']), (t['x2'], t['y2']))), t['w'])].append(t['id'])
    keep = set(); add = []
    for a, b, w, _ in final:
        k = (frozenset((a, b)), w)
        if oldk.get(k): keep.add(oldk[k].pop())
        else: add.append((a, b, w))
    dele = [t['id'] for t in ctx.tracks if t['id'] not in keep]
    if not dele and not add: return ([], [], resid), None, None
    for a, b, w in add:
        if not on45(a, b) or a == b: return None, 'off-grid piece left (%.4f, %.4f)' % (a[0] * MM, a[1] * MM), [(a, b)]
    # same terminals, still one piece
    t0, o0 = partition(ctx, ctx.old); newp = [(a, b, w) for a, b, w, _ in final]; t1, o1 = partition(ctx, newp)
    for grp_ in t0:
        if not any(grp_ <= h for h in t1):
            miss = grp_ - max(t1, key=lambda h: len(h & grp_), default=frozenset()); tests = []
            for m in miss:
                if m.startswith('via:'):
                    v = [v for v in ctx.vias if v['id'] == m[4:]][0]; tests.append((lambda n, v=v: dist(n, (v['x'], v['y'])) <= v['d'] / 2 + 150000, None))
                elif m.startswith('pad:'):
                    pg = [pg for pg, pd in ctx.pads if pd['ref'] + '.' + pd['n'] == m[4:]][0]; tests.append((lambda n, pg=pg: pg.distance(Point(n)) <= 150000, None))
                else:
                    pg = [pg for pg, nm in ctx.fills if nm == m[5:]][0]; tests.append((lambda n, pg=pg: pg.covers(Point(n)), None))
            return None, 'connectivity: %s' % sorted(miss)[:3], tests
    if o1 > o0: return None, 'group falls apart', []
    # excursion
    U = ctx.oldU
    for a, b, w in add:
        L = dist(a, b); n = max(1, int(L // 40000)); ts = np.linspace(0, 1, n + 1)
        d = float(shapely.distance(U, shapely.points(a[0] + (b[0] - a[0]) * ts, a[1] + (b[1] - a[1]) * ts)).max())
        if d > ctx.maxexc - 2000: return None, 'excursion %.3f mm at (%.3f, %.3f)' % (d * MM, a[0] * MM, a[1] * MM), [(a, b)]
    # clearance with the final widths, grandfathered by the deleted tracks only (as geolib does)
    delset = set(dele); oldp = [((t['x1'], t['y1']), (t['x2'], t['y2']), t['w']) for t in ctx.tracks if t['id'] in delset]
    for a, b, w in add:
        for it, gap, need in ctx.B.viol(ctx.l, ctx.net, a, b, w):
            if isinstance(it, tuple):
                ok = any(pg.intersects((LineString([p, q]) if p != q else Point(p)).buffer(ww / 2)) for pg, name in ctx.B.kos[ctx.l] if name == it[1] for p, q, ww in oldp)
            else:
                og = min([(LineString([p, q]) if p != q else Point(p)).distance(it.geom) - ww / 2 - it.r for p, q, ww in oldp] + [INF])
                ok = og < need and gap >= og - 500
            if not ok: return None, 'clearance to %s at (%.3f, %.3f)' % (it[0] if isinstance(it, tuple) else it.kind + ' ' + str(it.net), (a[0] + b[0]) / 2 * MM, (a[1] + b[1]) / 2 * MM), [(a, b)]
    pb = pour_guard(ctx, oldp, add)
    if pb is not None: return None, pb[0], pb[1]
    return (dele, add, resid), None, None

def _parts(gm): return [p for p in getattr(gm, 'geoms', [gm]) if p.geom_type == 'Polygon' and not p.is_empty]

def pour_guard(ctx, oldp, add):
    """The pours of other nets on this layer are cut by the tracks. Model of the new fill: the old fill minus the room
    the new pieces need. Taken with every neck narrower than 0 / 0.2 / 0.4 mm removed (as pourcheck.py does), no via or
    pad of the pour may lose the piece of copper it shared with another one, and no piece may fall apart into two
    that matter. Returns (reason, [offending new pieces]) or None."""
    B = ctx.B; l = ctx.l
    if not B.fill_l[l] or not add: return None
    seg = lambda a, b: LineString([a, b]) if a != b else Point(a)
    xs = [p[0] for a, b, w in add + oldp for p in (a, b)]; ys = [p[1] for a, b, w in add + oldp for p in (a, b)]; m = 1500000
    W = box(min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m); wb = W.boundary
    for pg, net, zclr in B.fill_l[l]:
        if net == ctx.net or not pg.intersects(W): continue
        clr = max(zclr, B.need(ctx.net, 'track', net))
        nk = unary_union([seg(a, b).buffer(w / 2 + clr, 8) for a, b, w in add])
        ok_ = unary_union([seg(a, b).buffer(w / 2 + clr - 2000, 8) for a, b, w in oldp]) if oldp else None
        extra = nk.difference(ok_) if ok_ is not None else nk
        if extra.is_empty: continue
        F0 = pg.intersection(W)
        if F0.is_empty or F0.intersection(extra).area < 1e6: continue
        F1 = F0.difference(nk)
        anc = [(Point(v['x'], v['y']), v['d'] / 2) for v in B.vias.get((net, l), []) if l in v['flash'] and W.covers(Point(v['x'], v['y']))]
        for q, pd in B.pads.get((net, l), []):
            if q.intersects(W): anc.append((q.centroid, math.sqrt(q.area / math.pi)))
        for r in (0, 100000, 200000):
            P0 = _parts(F0.buffer(-r) if r else F0); P1 = _parts(F1.buffer(-r) if r else F1)
            if not P0: continue
            def lab(P):
                out = []
                for pt, rad in anc:
                    best = None
                    for k, h in enumerate(P):
                        dd = h.distance(pt)
                        if dd < rad + r + 20000 and (best is None or dd < best[0]): best = (dd, k)
                    out.append(best[1] if best else -1)
                return out
            l0, l1 = lab(P0), lab(P1); bad = None
            byp = collections.defaultdict(list)
            for i, c in enumerate(l0):
                if c >= 0: byp[c].append(i)
            for c, idx in byp.items():
                if len({l1[i] for i in idx}) > 1 or any(l1[i] == -1 for i in idx): bad = P0[c]; break
            if bad is None:
                for g0 in P0:
                    if g0.area < 2e10: continue
                    big = [h for h in P1 if (h.area > 3e11 or h.distance(wb) < 1) and h.intersects(g0) and h.intersection(g0).area > 2e10]
                    if len(big) > 1: bad = g0; break
            if bad is not None:
                off = [(a, b) for a, b, w in add if seg(a, b).buffer(w / 2 + clr + r + 50000, 8).intersects(bad) and (ok_ is None or not ok_.covers(seg(a, b).buffer(w / 2 + clr - 3000, 8)))]
                c_ = bad.representative_point()
                return ('would pinch the %s pour (neck %.1f mm) near (%.2f, %.2f)' % (net, 2 * r * MM, c_.x * MM, c_.y * MM), off or [(a, b) for a, b, w in add])
    return None


# ------------------------------------------------------------------------------------------ main
def components(tracks):
    """connected groups of the tracks of one net on one layer: shared end points or an end in the copper of another"""
    n = len(tracks); par = list(range(n))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    geoms = [G.tgeom(t) for t in tracks]; tree = STRtree(geoms)
    for i, t in enumerate(tracks):
        for e in G.P(t):
            pe = Point(e)
            for j in tree.query(pe.buffer(1300000)):
                if j != i and geoms[j].distance(pe) <= tracks[j]['w'] / 2 + 1: par[f(i)] = f(int(j))
    out = collections.defaultdict(list)
    for i, t in enumerate(tracks): out[f(i)].append(t)
    return list(out.values())

def run_pass(geo, nc, opt, only, skip, U0, npass):
    B = Board(geo)
    by = collections.defaultdict(list)
    for t in geo['tracks']: by[(t['net'], t['l'])].append(t)
    nets = sorted({k[0] for k in by})
    LOG = []; dele_all = []; add_all = []; stats = collections.Counter(); resid_all = []
    tracks_now = {t['id']: t for t in geo['tracks']}; nn = [0]
    part0 = {}
    for net in nets:
        if not net or net in RF or (only and not only.search(net)) or (skip and skip.search(net)):
            if net in RF or (skip and skip.search(net)) : LOG.append('%s: skipped' % net)
            continue
        units = []
        for l in LN:
            ts = by.get((net, l))
            if not ts: continue
            U = U0.get((net, l))
            if U is None: U = unary_union([G.tgeom(t) for t in ts])
            for comp in components(ts):
                ids = {t['id'] for t in comp}
                others = [((t['x1'], t['y1']), (t['x2'], t['y2']), t['w']) for t in ts if t['id'] not in ids and (t['x1'], t['y1']) != (t['x2'], t['y2'])]
                ctx = Ctx(B, net, l, comp, others, opt); ctx.oldU = U
                ctx.own = others                               # same-net copper outside this group (inside it: see validate)
                try:
                    res, why = process_component(ctx)
                except Exception as e:
                    import traceback; res, why = None, 'error %r' % (e,); LOG.append(traceback.format_exc())
                x, y = comp[0]['x1'] * MM, comp[0]['y1'] * MM
                for m in ctx.log: LOG.append('%s %s group at (%.3f, %.3f): %s' % (net, l, x, y, m))
                if res is None:
                    stats['groups reverted'] += 1; LOG.append('%s %s group at (%.3f, %.3f) LEFT AS IT IS: %s' % (net, l, x, y, why)); continue
                dele, add, resid = res
                for p, w_ in resid: resid_all.append((net, l, p, w_))
                if not dele and not add: stats['groups clean'] += 1; continue
                units.append((l, dele, add, comp))
        if not units: continue
        # per net: geolib connectivity before == after; revert group by group if not
        def apply(us):
            dl = {i for u in us for i in u[1]}
            tr = [t for t in geo['tracks'] if t['net'] == net and t['id'] not in dl]
            for u in us:
                for a_, b_, w_ in u[2]: tr.append(dict(id='x%d' % len(tr), x1=a_[0], y1=a_[1], x2=b_[0], y2=b_[1], w=w_, l=u[0], net=net))
            return dict(geo, tracks=tr)
        g0n = dict(geo, tracks=[t for t in geo['tracks'] if t['net'] == net])
        c0, o0 = G.connectivity(g0n, nets={net})
        def same(us):
            c1, o1 = G.connectivity(apply(us), nets={net})
            return not any(not any(grp <= h for h in c1[net]) for grp in c0[net]) and o1[net] <= o0[net]
        if not same(units):
            good = []
            for u in units:
                if same(good + [u]): good.append(u)
                else:
                    stats['groups reverted'] += 1
                    LOG.append('%s %s group at (%.3f, %.3f) LEFT AS IT IS: geolib connectivity' % (net, u[0], u[3][0]['x1'] * MM, u[3][0]['y1'] * MM))
            units = good
        for l, dele, add, comp in units:
            stats['groups changed'] += 1
            for i in dele: B.kill(i); dele_all.append(i)
            for a_, b_, w_ in add:
                nn[0] += 1; t = dict(id='rt%d_%05d' % (npass, nn[0]), x1=a_[0], y1=a_[1], x2=b_[0], y2=b_[1], w=w_, l=l, net=net)
                B.add_track(t); add_all.append(t)
    # ---- final check of everything with geolib; revert the groups of anything that fails
    for rnd in range(4):
        spec = {'del': list(dele_all), 'add': [dict(net=t['net'], l=t['l'], w=t['w'], x1=t['x1'], y1=t['y1'], x2=t['x2'], y2=t['y2'], id=t['id']) for t in add_all], 'tag': 'rt'}
        g1 = G.apply_spec(geo, spec); bad = G.clearance(geo, g1, spec)
        if not bad: break
        badnl = {(v['net'], v['l']) for v in bad}
        for v in bad: LOG.append('%s %s: final clearance check failed at (%.3f, %.3f) to %s %s, net and layer reverted' % (v['net'], v['l'], v['x'], v['y'], v['to'], v['tonet']))
        stats['net-layers reverted by the final clearance check'] += len(badnl)
        ids0 = {t['id']: t for t in geo['tracks']}
        dele_all = [i for i in dele_all if (ids0[i]['net'], ids0[i]['l']) not in badnl]; add_all = [t for t in add_all if (t['net'], t['l']) not in badnl]
    spec = {'del': sorted(dele_all), 'add': [dict(net=t['net'], l=t['l'], w=t['w'], x1=t['x1'], y1=t['y1'], x2=t['x2'], y2=t['y2'], id=t['id']) for t in add_all], 'tag': 'rt'}
    return spec, stats, LOG, resid_all

def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]; O = dict((x[2:].split('=', 1) + ['1'])[:2] for x in sys.argv[1:] if x.startswith('--'))
    t0 = time.time(); geo = json.load(open(a[0])); nc = geo['netclass']
    zoned = {z['net'] for z in geo['zones'] if z['net']}; plane = {t['net'] for t in geo['tracks'] if t['l'] in ('In1', 'In4')}
    def sens(n): return nc.get(n, 'Default') in SENS_CLASSES or n in zoned or n in plane or n in SENS_NETS or any(r.search(n) for r in SENS_RX)
    opt = dict(sens=sens, maxexc_s=float(O.get('maxexc-sensitive', 0.30)), maxexc=float(O.get('maxexc', 0.80)))
    only = re.compile(O['only']) if 'only' in O else None; skip = re.compile(O['skip']) if 'skip' in O else None
    cached = G._index(geo); G._index = lambda g: cached
    # the copper of every net and layer as it came in: the excursion limit counts from there in every pass
    by0 = collections.defaultdict(list)
    # reference copper for the excursion limit: --exc-from=file, else the committed board base/geo.json next to tools/
    # when it is there, else (or with --exc-from=input) the board that came in
    rf = O.get('exc-from') or os.path.join(HERE, '..', '..', 'base', 'geo.json')
    ref = geo if rf == 'input' or not os.path.exists(rf) or os.path.abspath(rf) == os.path.abspath(a[0]) else json.load(open(rf))
    print('rethread: excursion counted from', 'the incoming board' if ref is geo else os.path.abspath(rf))
    for t in ref['tracks']: by0[(t['net'], t['l'])].append(G.tgeom(t))
    if ref is not geo:
        for t in geo['tracks']:
            if (t['net'], t['l']) not in by0: by0[(t['net'], t['l'])].append(G.tgeom(t))
    del ref
    U0 = {k: unary_union(v) for k, v in by0.items()}
    # passes until nothing changes (a re-drawn group can open the way for its neighbour); the result is a fixed point
    cur = geo; LOG = []; stats = collections.Counter(); resid_all = []; npass = 0; maxpass = int(O.get('passes', 6))
    while npass < maxpass:
        npass += 1
        sp, st, lg, resid_all = run_pass(cur, nc, opt, only, skip, U0, npass)
        if npass == 1: LOG += lg; stats.update(st)
        else:
            LOG += ['pass %d: %s' % (npass, m) for m in lg if m not in LOG]
            if st.get('groups changed'): stats['groups changed in pass %d' % npass] = st['groups changed']
        if not sp['del'] and not sp['add']: break
        cur = G.apply_spec(cur, sp)
    stats['passes'] = npass
    # the spec against the board that came in
    key = lambda t: (t['net'], t['l'], t['w'], min((t['x1'], t['y1']), (t['x2'], t['y2'])), max((t['x1'], t['y1']), (t['x2'], t['y2'])))
    ids0 = {t['id']: t for t in geo['tracks']}; ids1 = {t['id'] for t in cur['tracks']}
    dele = [i for i in ids0 if i not in ids1]; add = [t for t in cur['tracks'] if t['id'] not in ids0]
    back = collections.defaultdict(list)
    for i in dele: back[key(ids0[i])].append(i)
    keep = set(); add2 = []
    for t in add:                                           # a later pass put a piece back exactly as it was: not a change
        b = back.get(key(t))
        if b: keep.add(b.pop())
        else: add2.append(t)
    spec = {'del': sorted(i for i in dele if i not in keep), 'add': [dict(net=t['net'], l=t['l'], w=t['w'], x1=t['x1'], y1=t['y1'], x2=t['x2'], y2=t['y2']) for t in add2], 'tag': 'rt'}
    if npass > 1 and G.clearance(geo, G.apply_spec(geo, spec), spec):
        LOG.append('clearance of the passes together failed against the incoming board: result of pass 1 only')
        spec, st, lg, resid_all = run_pass(geo, nc, opt, only, skip, U0, 1)
        spec = {'del': spec['del'], 'add': [{k: v for k, v in t.items() if k != 'id'} for t in spec['add']], 'tag': 'rt'}
    json.dump(spec, open(a[1], 'w'))
    print('rethread: %d tracks deleted, %d added; %s; residual zones %d; %.0f s' % (len(spec['del']), len(spec['add']), dict(stats), len(resid_all), time.time() - t0))
    if 'log' in O:
        with open(O['log'], 'w') as f:
            for m in dict.fromkeys(LOG): f.write(m + '\n')
            f.write('\nzones left as they are\n')
            for net, l, p, w_ in resid_all: f.write('  %s %s (%.4f, %.4f): %s\n' % (net, l, p[0] * MM, p[1] * MM, w_))

if __name__ == '__main__':
    main()
