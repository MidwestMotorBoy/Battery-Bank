#!/usr/bin/env python3
"""straighten.py geo.json spec_out.json [options]        (plain python 3 with shapely; no KiCad needed)

Takes needless kinks, jogs, staircases and small detours out of existing tracks, in place. It is a path shortener
that keeps the topology ("rubber band" on the 45 degree grid), not a router: nothing is ripped up and nothing new
is searched.

  geo.json    board dump from dumpgeo.py (integer nanometres, track ids)
  spec_out    {"del": [track ids], "add": [{net, l, w, x1, y1, x2, y2}], "runs": [...]} for straighten_apply.py

How it works
  1. Per net and layer the tracks are joined into a graph. Fixed points never move: pads, vias, T-junctions, track
     ends, places where the width changes and places where a track passes through a pad or via of its own net.
     A "run" is the chain of segments between two fixed points; it has one layer and one width.
  2. For a run with corners v0..vn every pair (vi, vj) gets up to three replacement paths between the SAME two
     points: one straight segment if they line up, the two "one straight + one diagonal" paths, and the corner
     where the lines of the first and last segment meet. All of them lie on the 45 degree grid.
  3. A replacement is taken only if all of this holds:
       - not longer, not more bends, not more total turning, no new acute corner, and strictly better in bends or
         length (at least 1 um);
       - clearance to every other net's track, pad, via, hole and to the board edge by the board's rules (0.15 mm,
         0.25 mm between HighCurrent copper and default-class copper, 0.2 mm to a hole, 0.25 mm to the edge); where
         the old path was already closer than this model allows, the new one may not be closer than the old one;
       - same channel: the area between the old and the new path holds no copper of any net, no pad, via or hole,
         so the track stays on the same side of everything and no net order changes;
       - the track's own net is not touched anywhere new, and the branches at a T-junction keep their order;
       - no rule area is entered that the old path did not cross;
       - power pours keep their copper: inside the outline of a drawn pour of another net (zone priority above 0:
         VBUS, PPHV, PACK_P at the sense resistors, the switch nodes ...) there may not be more track than before;
       - pours stay whole: around the change, the room a pour has on this layer (everything grown by the pour
         clearance and half the minimum pour width) must not fall apart where it was one piece, also not for necks
         of 0.55 mm and wider. A track on In2 or In3 is a slot in the PACK_P or 3V3 plane, and moving the slot can
         cut a neck that no rule check reports.
     Among the legal ones the largest saving (length + 0.3 mm per bend) is applied, and the search repeats until
     nothing is left. Runs are visited in sweeps until a sweep changes nothing, because one straightened track
     frees room for its neighbour.
  4. Vias, pads, zones and widths are never changed. Nets on the protected list are obstacles only.

Options
  --protect=file.json   {"nets": [exact names], "regex": [patterns], "classes": [net classes]}; default: built in (see PROTECT)
  --only=regex          work on matching nets only          --skip=regex   leave matching nets alone as well
  --maxmove=mm          largest distance a point of a run may move (default 0 = no limit)
  --maxmove-L=mm        the same for one layer, e.g. --maxmove-In2=0.6 (pour layers)
  --lam=mm              what one bend is worth in mm of length when ranking (default 0.3)
  --pour=0              switch the pour test off (never for a real pass)
  --sweeps=n            at most n sweeps (default 6)
  --log=file            per-run log
"""
import json, sys, math, collections, re, os, time
import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree

MM = 1e-6
TOL = 2e-6                      # mm, slack on a clearance compare (2 nm)
CLR, CLR_HC, CLR_HOLE, CLR_EDGE, GAP_SAME = 0.15, 0.25, 0.20, 0.25, 0.15
TIE = 50000.0                   # nm: savings within 0.05 mm of the best count as equal; the candidate that moves least wins
# Nets that are never altered (they are still obstacles). Classes cover PACK_P, the cell taps, VBUS, PPHV, the switch
# nodes, the 3V3 / 5 V rails, ground, every Kelvin tap and the gate drives; nets with a pour and nets with a track on
# In1 or In4 (the ground planes) are added automatically.
PROTECT = dict(classes=['HighCurrent', 'Power', 'GND', 'Kelvin', 'GateDrive'],
               nets=['EN_5V1',                                          # hand repair of fix pass 2 (solver-driven)
                     # the other nets that fix pass 2 moved because the coupling solver flagged them. Tried here on
                     # 2026-11-16: straightening port 1 I2CC_SCL took it from 4.0 to 17.5 mV per switch edge.
                     '/USB Port 1/I2CC_SCL', '/USB Port 2/SBU_FLT', '/Cells and Gauge/TS4', 'Net-(U403-FB)', 'Net-(U503-FB)',
                     '/MCU/RFIO', '/MCU/ANT_IN', 'Net-(C313-Pad2)'],    # RF path and its match node
               # last pattern: the gate-driver supply of each charger. It runs beside the switch nodes; straightening it
               # (tried 2026-11-16) raised its own pick-up from them by 0.3 to 3.5 fF and port 1 TS by 0.05 fF.
               regex=[r'/DPDN', r'/D[PN]$', r'USB_D', r'/(SRP|SRN|ACP|ACN)(_F)?$', r'/DRV_SUP$'])


# ---------------------------------------------------------------- small geometry helpers (integer nm points)
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])
def octi(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    return dx == 0 or dy == 0 or abs(dx) == abs(dy)
def sgn(v): return (v > 0) - (v < 0)
def turn(a, b, c):
    """turning angle at b in degrees, 0 = straight on, 180 = doubles back"""
    u, v = sub(b, a), sub(c, b)
    return abs(math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1])))
def clean(pts):
    """drop repeated points and points on a straight line (keeps points where the path doubles back)"""
    o = []
    for p in pts:
        if o and p == o[-1]: continue
        while len(o) >= 2:
            u, v = sub(o[-1], o[-2]), sub(p, o[-1])
            if u[0] * v[1] - u[1] * v[0] == 0 and u[0] * v[0] + u[1] * v[1] > 0: o.pop()
            else: break
        o.append(p)
    return o
def plen(pts): return sum(dist(a, b) for a, b in zip(pts, pts[1:]))
def metrics(pts):
    """length (nm), bends, total turning (units of 45 degrees), largest turn (degrees)"""
    p = clean(pts); T = 0.0; B = 0; mx = 0.0
    for a, b, c in zip(p, p[1:], p[2:]):
        t = turn(a, b, c)
        if t > 0.5: B += 1; T += t / 45.0; mx = max(mx, t)
    return plen(p), B, T, mx
def connect(a, b):
    """paths a -> b on the 45 degree grid with at most one corner"""
    if a == b: return []
    dx, dy = b[0] - a[0], b[1] - a[1]
    if dx == 0 or dy == 0 or abs(dx) == abs(dy): return [[a, b]]
    m = min(abs(dx), abs(dy)); dg = (sgn(dx) * m, sgn(dy) * m); st = (dx - dg[0], dy - dg[1])
    return [[a, (a[0] + dg[0], a[1] + dg[1]), b], [a, (a[0] + st[0], a[1] + st[1]), b]]
def meet(a, a2, b2, b):
    """corner X where the ray a -> a2 meets the ray arriving at b from b2 (both on the 45 degree grid), or None"""
    d1, d2 = sub(a2, a), sub(b, b2)
    if not (octi(a, a2) and octi(b2, b)) or d1 == (0, 0) or d2 == (0, 0): return None
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if den == 0: return None
    w = sub(b, a)                                                    # a + t*d1 = b - s*d2
    t = (w[0] * d2[1] - w[1] * d2[0]) / den; s = (d1[0] * w[1] - d1[1] * w[0]) / den
    if t <= 0 or s <= 0: return None
    x = a[0] + t * d1[0]; y = a[1] + t * d1[1]
    xi, yi = round(x), round(y)
    if abs(x - xi) > 1e-6 or abs(y - yi) > 1e-6: return None
    X = (xi, yi)
    if not (octi(a, X) and octi(X, b)): return None
    return X
def cross_point(a, b, c, d):
    """interior crossing point of segments a-b and c-d if it is a whole number of nm, else None"""
    r, q = sub(b, a), sub(d, c); den = r[0] * q[1] - r[1] * q[0]
    if den == 0: return None
    w = sub(c, a); tn = w[0] * q[1] - w[1] * q[0]; un = w[0] * r[1] - w[1] * r[0]
    if den < 0: den, tn, un = -den, -tn, -un
    if not (0 < tn < den and 0 < un < den): return None
    if (tn * r[0]) % den or (tn * r[1]) % den: return None
    return (a[0] + tn * r[0] // den, a[1] + tn * r[1] // den)
def mmpts(pts): return [(p[0] * MM, p[1] * MM) for p in pts]
def region(old, new):
    """area between two paths with common ends (every bounded face of the closed curve), or None"""
    ring = list(old) + list(new[-2:0:-1]) + [old[0]]
    if len(set(ring)) < 3: return None
    try:
        faces = list(polygonize(unary_union(LineString(mmpts(ring)))))
    except Exception:
        return None
    faces = [f for f in faces if f.area > 1e-10]
    if not faces: return None
    return unary_union(faces)


# ---------------------------------------------------------------- board model
class Item:
    __slots__ = ('kind', 'net', 'geom', 'r', 'cls', 'tid', 'alive', 'hole', 'rp', 'inf')
    def __init__(s, kind, net, geom, r, cls='', tid=None, hole=False, rp=None):
        s.kind, s.net, s.geom, s.r, s.cls, s.tid, s.alive, s.hole = kind, net, geom, r, cls, tid, True, hole
        s.rp = r if rp is None else rp                     # radius towards the item's own net (a via counts with its full pad)
        s.inf = {}                                         # inflated outline per distance (pour test)

class LayerIndex:
    """obstacles of one copper layer; items can die and new ones can be added"""
    def __init__(s, items):
        s.items = list(items); s.extra = []; s._build()
    def _build(s):
        s.items = [i for i in s.items + s.extra if i.alive]; s.extra = []
        s.tree = STRtree([i.geom for i in s.items]) if s.items else None
    def add(s, it):
        s.extra.append(it)
        if len(s.extra) > 48: s._build()
    def query(s, bx):
        out = []
        if s.tree is not None:
            for k in s.tree.query(bx):
                it = s.items[k]
                if it.alive: out.append(it)
        for it in s.extra:
            if it.alive and it.geom.intersects(bx): out.append(it)
        return out

class Run:
    __slots__ = ('net', 'l', 'w', 'pts', 'orig', 'ids', 'frozen', 'items', 'key', 'changed')

class Board:
    def __init__(s, geo, protect, opt):
        s.g = geo; s.opt = opt; s.nc = geo['netclass']; s.LN = ['F', 'In1', 'In2', 'In3', 'In4', 'B']
        zoned = {z['net'] for z in geo['zones'] if z['net']}
        plane = {t['net'] for t in geo['tracks'] if t['l'] in ('In1', 'In4')}
        rx = [re.compile(r) for r in protect.get('regex', [])]
        s.prot = {}
        for n in {t['net'] for t in geo['tracks']}:
            why = None
            if s.nc.get(n, 'Default') in protect.get('classes', []): why = 'class ' + s.nc.get(n)
            elif n in protect.get('nets', []): why = 'listed'
            elif any(r.search(n) for r in rx): why = 'pattern'
            elif n in zoned: why = 'has a pour'
            elif n in plane: why = 'track on a ground-plane layer'
            if why: s.prot[n] = why
        # obstacles
        per = {L: [] for L in s.LN}
        s.RMAX = 0.0
        for v in geo['vias']:
            pt = Point(v['x'] * MM, v['y'] * MM)
            for L in s.LN:
                if L in v['flash']: it = Item('via', v['net'], pt, v['d'] / 2 * MM, s.nc.get(v['net'], 'Default'))
                else: it = Item('via', v['net'], pt, v['drill'] / 2 * MM, s.nc.get(v['net'], 'Default'), hole=True, rp=v['d'] / 2 * MM)
                per[L].append(it); s.RMAX = max(s.RMAX, it.r)
        for p in geo['pads']:
            for L, poly in p['L'].items():
                if len(poly) >= 3:
                    per[L].append(Item('pad', p['net'], Polygon(mmpts(poly)), 0.0, s.nc.get(p['net'], 'Default'), tid=p['ref'] + '.' + p['n']))
            if p['hole'] and (p['npth'] or not p['L']):
                h = p['hole']; a, b = (h[0] * MM, h[1] * MM), (h[2] * MM, h[3] * MM)
                gm = Point(a) if a == b else LineString([a, b])
                for L in s.LN: per[L].append(Item('hole', None, gm, h[4] / 2 * MM, hole=True)); s.RMAX = max(s.RMAX, h[4] / 2 * MM)
        for outline, holes in geo['edge']:
            for ring in [outline] + holes:
                gm = LineString(mmpts(ring + [ring[0]]))
                for L in s.LN: per[L].append(Item('edge', None, gm, 0.0))
        s.kos = {L: [] for L in s.LN}
        for k in geo['keepouts']:
            for outline, holes in k['polys']:
                pg = Polygon(mmpts(outline), [mmpts(h) for h in holes])
                for L in k['layers']: s.kos[L].append(pg)
        for t in geo['tracks']:                              # tracks of protected nets; the others are added run by run
            a, b = (t['x1'], t['y1']), (t['x2'], t['y2'])
            s.RMAX = max(s.RMAX, t['w'] / 2 * MM)
            if a == b or not (t['net'] in s.prot or not t['net']): continue
            per[t['l']].append(Item('trk', t['net'], LineString(mmpts([a, b])), t['w'] / 2 * MM, s.nc.get(t['net'], 'Default'), tid=t['id']))
        s.idx = {L: LayerIndex(per[L]) for L in s.LN}
        s.pour_nets = {L: {z['net'] for z in geo['zones'] if L in z['layers']} for L in s.LN}
        s.shapes = {L: [] for L in s.LN}                     # drawn power pours (priority above 0), grown by the pour clearance
        for z in geo['zones']:
            if z['prio'] > 0:
                for outline, holes in z['outline']:
                    pg = Polygon(mmpts(outline), [mmpts(h) for h in holes]).buffer(max(z['clearance'] * MM, CLR_HC))
                    for L in z['layers']: s.shapes[L].append((z['net'], pg))
        s.pour_d = {L: (0.2 if L in ('F', 'B') else 0.25) + 0.125 for L in s.LN}    # pour clearance + half the minimum pour width
        s.frozen_log = []
        s.build_runs()

    # ------------------------------------------------------------ graph -> runs
    def build_runs(s):
        g = s.g; byNL = collections.defaultdict(list)
        for t in g['tracks']: byNL[(t['net'], t['l'])].append(t)
        viaAt = collections.defaultdict(set)
        for v in g['vias']: viaAt[v['net']].add((v['x'], v['y']))
        s.runs = []; s.zero = []; s.dup_ids = []; s.dup_log = []
        for (net, L), tt in sorted(byNL.items()):
            if net in s.prot or not net: continue
            segs = []                                            # [a, b, w, id]
            for t in tt:
                a, b = (t['x1'], t['y1']), (t['x2'], t['y2'])
                if a == b: s.zero.append(t); continue
                segs.append([a, b, t['w'], t['id']])
            bad = set(); extra_nodes = set()
            def dedupe():
                cnt = collections.Counter(q[3] for q in segs); seen = {}; out = []
                for sg in sorted(segs, key=lambda q: (-(cnt[q[3]] > 1), -q[2])):      # pieces of a split track first, then widest first
                    k = frozenset((sg[0], sg[1]))
                    if k in seen:
                        if cnt[sg[3]] == 1 and sg[2] <= seen[k][2]:                    # a whole track that lies on another: it can go
                            s.dup_ids.append(sg[3]); s.dup_log.append((net, L, sg[0], sg[1]))
                        else: bad.add(sg[3]); bad.add(seen[k][3])
                        continue
                    seen[k] = sg; out.append(sg)
                segs[:] = out
            dedupe()
            # an end that lands exactly on the middle of another track of the net: split that track there (T-junction)
            changed = True
            while changed:
                changed = False
                pts_all = {p for sg in segs for p in sg[:2]}
                for k, (a, b, w, i) in enumerate(segs):
                    u = sub(b, a); hit = None
                    for e in pts_all:
                        if e == a or e == b: continue
                        v = sub(e, a)
                        if u[0] * v[1] - u[1] * v[0] == 0 and 0 < u[0] * v[0] + u[1] * v[1] < u[0] * u[0] + u[1] * u[1]: hit = e; break
                    if hit is not None:
                        segs[k] = [a, hit, w, i]; segs.append([hit, b, w, i]); changed = True; break
                if not changed:                                              # two tracks that cross without a common point: split both there
                    for k, (a, b, w, i) in enumerate(segs):
                        for k2 in range(k + 1, len(segs)):
                            X = cross_point(a, b, segs[k2][0], segs[k2][1])
                            if X is not None:
                                c, d, w2, i2 = segs[k2]
                                segs[k] = [a, X, w, i]; segs.append([X, b, w, i]); segs[k2] = [c, X, w2, i2]; segs.append([X, d, w2, i2]); changed = True; break
                        if changed: break
                if changed: dedupe()
            ends = collections.Counter()
            for a, b, w, i in segs: ends[a] += 1; ends[b] += 1
            lines = [LineString(mmpts([a, b])) for a, b, w, i in segs]
            # a loose end that sits in the copper of another track of the net without a common point: hold both in place
            for k, (a, b, w, i) in enumerate(segs):
                for e in (a, b):
                    if ends[e] != 1: continue
                    pe = Point(e[0] * MM, e[1] * MM)
                    for k2, (c, d, w2, i2) in enumerate(segs):
                        if k2 == k: continue
                        lim = (w + w2) / 2 * MM - 1e-6
                        if lines[k2].distance(pe) >= lim: continue
                        P = min((c, d), key=lambda q: dist(q, e))
                        if dist(P, e) * MM < lim: extra_nodes.add(P)
                        else: bad.add(i); bad.add(i2)
            # true crossings (no common point)
            for k, (a, b, w, i) in enumerate(segs):
                for k2 in range(k + 1, len(segs)):
                    c, d, w2, i2 = segs[k2]
                    if len({a, b, c, d}) < 4: continue
                    if lines[k].distance(lines[k2]) < 1e-7: bad.add(i); bad.add(i2)
            adj = collections.defaultdict(list)
            for k, (a, b, w, i) in enumerate(segs): adj[a].append(k); adj[b].append(k)
            node = set()
            for p, ks in adj.items():
                if len(ks) != 2 or segs[ks[0]][2] != segs[ks[1]][2] or p in viaAt[net] or p in extra_nodes: node.add(p)
            used = set()
            def walk(k, start):
                pts = [start]; ids = []; cur = start
                while True:
                    used.add(k); a, b, w, i = segs[k]; nxt = b if a == cur else a
                    pts.append(nxt); ids.append(i); cur = nxt
                    if cur in node: break
                    k2 = [q for q in adj[cur] if q != k]
                    if not k2 or k2[0] in used: break
                    k = k2[0]
                return pts, ids
            for p in sorted(node):
                for k in adj[p]:
                    if k in used: continue
                    pts, ids = walk(k, p)
                    s._add_run(net, L, segs[k][2], pts, ids, bad, node)
            for k in range(len(segs)):                           # closed loops without any fixed point: leave alone
                if k not in used:
                    pts, ids = walk(k, segs[k][0])
                    s._add_run(net, L, segs[k][2], pts, ids, bad, node, frozen='closed loop without a fixed point')
        # a track id that is in two runs (it was split at a T): remember
        s.id_runs = collections.defaultdict(list)
        for r in s.runs:
            for i in set(r.ids): s.id_runs[i].append(r)

    def _add_run(s, net, L, w, pts, ids, bad, nodes=(), frozen=None):
        """split the run where it passes through a pad or via of its own net, then store"""
        if any(i in bad for i in ids): frozen = frozen or 'touches its own net away from a track end'
        cuts = set()
        if not frozen:
            ln = LineString(mmpts(pts)); half = w / 2 * MM
            for it in s.idx[L].query(box(*ln.buffer(half + s.RMAX + 0.01).bounds)):
                if it.net != net or it.kind not in ('pad', 'via'): continue
                rr = it.rp
                if ln.distance(it.geom) > half + rr - 1e-6: continue          # no copper contact
                ins = [k for k, p in enumerate(pts) if Point(p[0] * MM, p[1] * MM).distance(it.geom) <= rr + 1e-6]
                if 0 in ins or len(pts) - 1 in ins: continue                 # the run ends in it: the end point holds the contact
                if any(Point(q[0] * MM, q[1] * MM).distance(it.geom) <= rr + 1e-6 for q in nodes): continue    # another fixed point of the net holds it
                if not ins: frozen = 'passes a pad or via of its own net without a corner in it'; break
                c = it.geom.centroid
                cuts.add(min(ins, key=lambda k: math.hypot(pts[k][0] * MM - c.x, pts[k][1] * MM - c.y)))
        if frozen or not cuts:
            return s._store(net, L, w, pts, ids, frozen)
        cs = [0] + sorted(cuts) + [len(pts) - 1]
        for a, b in zip(cs, cs[1:]): s._store(net, L, w, pts[a:b + 1], ids[a:b], None)

    def _store(s, net, L, w, pts, ids, frozen):
        r = Run(); r.net, r.l, r.w, r.pts, r.orig, r.ids, r.frozen, r.changed = net, L, w, list(pts), list(pts), list(ids), frozen, False
        r.key = (net, L, pts[0], pts[-1], len(s.runs)); r.items = []
        for a, b in zip(pts, pts[1:]):
            it = Item('trk', net, LineString(mmpts([a, b])), w / 2 * MM, s.nc.get(net, 'Default')); r.items.append(it); s.idx[L].add(it)
        if frozen: s.frozen_log.append((net, L, frozen, pts[0], pts[-1]))
        s.runs.append(r); return r

    # ------------------------------------------------------------ legality of one replacement
    def clr(s, cls, it):
        if it.kind == 'edge': return CLR_EDGE
        if it.kind == 'hole': return CLR_EDGE
        c = CLR
        if it.kind != 'pad' and ((cls == 'HighCurrent' and it.cls == 'Default') or (it.cls == 'HighCurrent' and cls == 'Default')): c = CLR_HC
        return max(c, CLR_HOLE) if it.hole else c           # a via without a pad on this layer: its barrel counts as copper

    def legal(s, r, i, j, N, why=None):
        V = r.pts; old = V[i:j + 1]; n = len(V) - 1
        half = r.w / 2 * MM; cls = s.nc.get(r.net, 'Default')
        newL = LineString(mmpts(N)); oldL = LineString(mmpts(old))
        mv = s.opt['maxmove'].get(r.l, s.opt['maxmove'].get('*', 0))
        if mv and shapely.hausdorff_distance(newL, oldL, densify=0.2) > mv: return 'moves too far'
        R = region(old, N)
        reach = half + s.RMAX + CLR_HC + 0.02
        b0 = newL.bounds; b1 = oldL.bounds
        bx = box(min(b0[0], b1[0]) - reach, min(b0[1], b1[1]) - reach, max(b0[2], b1[2]) + reach, max(b0[3], b1[3]) + reach)
        for it in s.idx[r.l].query(bx):
            g = it.geom; dn = newL.distance(g)
            if it.net != r.net or it.kind in ('edge', 'hole'):
                req = half + it.r + s.clr(cls, it)
                if dn < req - TOL and dn < oldL.distance(g) - TOL: return 'clearance to %s %s' % (it.kind, it.net)
                if R is not None and R.intersects(g): return 'would pass %s %s' % (it.kind, it.net)
                continue
            # own net, not part of this run
            touch = half + it.rp; do = oldL.distance(g)
            if do <= touch + 1e-6:                                           # the old path touches it: something at a fixed end
                if it.kind == 'trk':
                    c = list(g.coords); c = [(round(c[0][0] / MM), round(c[0][1] / MM)), (round(c[1][0] / MM), round(c[1][1] / MM))]
                    P = None
                    for e in (old[0], old[-1]):
                        if e in c: P = e
                    if P is None:
                        if dn < do - TOL or (R is not None and R.intersects(g)): return 'own net nearby'
                        continue
                    Q = c[1] if c[0] == P else c[0]; bv = sub(Q, P); bl = math.hypot(*bv)
                    dn_ = sub(N[1], N[0]) if P == N[0] else sub(N[-2], N[-1]); do_ = sub(old[1], old[0]) if P == old[0] else sub(old[-2], old[-1])
                    cn = (bv[0] * dn_[0] + bv[1] * dn_[1]) / (bl * math.hypot(*dn_)); co = (bv[0] * do_[0] + bv[1] * do_[1]) / (bl * math.hypot(*do_))
                    if cn > max(co, 0.0) + 1e-9: return 'sharper angle to a branch'
                    if R is not None:
                        e = min(bl / 2, 5000.0) / bl; pr = Point((P[0] + bv[0] * e) * MM, (P[1] + bv[1] * e) * MM)
                        if R.contains(pr) and R.boundary.distance(pr) > 1e-6: return 'would swap sides with a branch'
                continue
            if dn < touch + GAP_SAME - TOL and dn < do - TOL: return 'own net too close'
            if R is not None and R.intersects(g): return 'would pass own net'
        # the rest of this run
        for part in (V[:i], V[j + 1:]):
            if len(part) >= 2:
                g = LineString(mmpts(part)); dn = newL.distance(g)
                if dn < r.w * MM + GAP_SAME - TOL and dn < oldL.distance(g) - TOL: return 'own run too close'
                if R is not None and R.intersects(g): return 'would pass own run'
        if R is not None:
            for a, b in ((i, i - 1), (j, j + 1)):
                if 0 <= b <= n:
                    P, Q = V[a], V[b]; bv = sub(Q, P); bl = math.hypot(*bv); e = min(bl / 2, 5000.0) / bl
                    pr = Point((P[0] + bv[0] * e) * MM, (P[1] + bv[1] * e) * MM)
                    if R.contains(pr) and R.boundary.distance(pr) > 1e-6: return 'folds over its own run'
        for ko in s.kos[r.l]:
            dn = newL.distance(ko)
            if dn < half - TOL and dn < oldL.distance(ko) - TOL: return 'enters a rule area'
        for znet, pg in s.shapes[r.l]:                       # no more track inside a drawn power pour of another net than before
            if znet == r.net: continue
            a = newL.intersection(pg.buffer(half)).length if newL.distance(pg) < half else 0.0
            if a > 1e-6 and a > oldL.intersection(pg.buffer(half)).length + 1e-6: return 'would cut into a power pour'
        if s.opt['pour'] and s.pour_nets[r.l] and not s.pour_ok(r, i, j, oldL, newL, half): return 'would cut or pinch a pour'
        return None

    def pour_ok(s, r, i, j, oldL, newL, half):
        """The copper pours of this layer must stay in one piece around the change. Free room for a pour is what is left
        of a window when every obstacle is grown by the pour clearance plus half the minimum pour width (and once more by
        0.15 mm, so a neck that is at least 0.55 mm wide is not squeezed below that either). No piece of free room that
        was one before may fall apart into two pieces that matter (reaching the window edge, or larger than 0.3 mm2)."""
        V = r.pts; b0 = newL.bounds; b1 = oldL.bounds; m = 1.2
        W = box(min(b0[0], b1[0]) - m, min(b0[1], b1[1]) - m, max(b0[2], b1[2]) + m, max(b0[3], b1[3]) + m)
        pn = s.pour_nets[r.l]; items = [it for it in s.idx[r.l].query(W.buffer(0.7)) if it.net not in pn or it.kind in ('edge', 'hole')]
        rest = [LineString(mmpts(p)) for p in (V[:i + 1], V[j:]) if len(p) >= 2]
        for d in (s.pour_d[r.l], s.pour_d[r.l] + 0.15):
            polys = []
            for it in items:
                g = it.inf.get(d)
                if g is None: g = it.inf[d] = it.geom.buffer(it.r + d, 8)
                polys.append(g)
            polys += [k for k in s.kos[r.l] if k.intersects(W)] + [g.buffer(half + d, 8) for g in rest]
            base = unary_union(polys) if polys else None
            So = W.difference(unary_union([base, oldL.buffer(half + d, 8)]) if base is not None else oldL.buffer(half + d, 8))
            Sn = W.difference(unary_union([base, newL.buffer(half + d, 8)]) if base is not None else newL.buffer(half + d, 8))
            co = [g for g in getattr(So, 'geoms', [So]) if g.geom_type == 'Polygon' and g.area > 0.02]
            cn = [g for g in getattr(Sn, 'geoms', [Sn]) if g.geom_type == 'Polygon' and g.area > 0.02]
            if not co or not cn: continue
            wb = W.boundary
            big = [k for k, g in enumerate(cn) if g.area > 0.3 or g.distance(wb) < 1e-9]
            for g in co:
                hit = 0
                for k in big:
                    if cn[k].intersects(g) and cn[k].intersection(g).area > 0.02: hit += 1
                if hit > 1: return False
        return True

    # ------------------------------------------------------------ one run
    def optimise(s, r, stats):
        if r.frozen or len(r.pts) < 3: return False
        lam = s.opt['lam'] * 1e6; SPAN = s.opt['span']
        for it in r.items: it.alive = False                                  # the run does not block itself
        r.pts = clean(r.pts)
        failed = set(); any_change = False
        while True:
            V = r.pts; n = len(V) - 1; cands = []
            if n < 2: break
            sl = [dist(V[k], V[k + 1]) for k in range(n)]; tv = [0.0] + [turn(V[k - 1], V[k], V[k + 1]) for k in range(1, n)] + [0.0]
            cl = [0.0]; cb = [0]; ct = [0.0]
            for k in range(n): cl.append(cl[-1] + sl[k])
            for k in range(n + 1): cb.append(cb[-1] + (1 if tv[k] > 0.5 else 0)); ct.append(ct[-1] + (tv[k] / 45.0 if tv[k] > 0.5 else 0.0))
            for i in range(0, n - 1):
                for j in range(i + 2, min(n, i + SPAN) + 1):
                    opts = connect(V[i], V[j])
                    if j - i >= 3:
                        X = meet(V[i], V[i + 1], V[j - 1], V[j])
                        if X is not None and X != V[i] and X != V[j]: opts.append([V[i], X, V[j]])
                    lo, hi = max(i - 1, 0), min(j + 1, n)
                    Lo = cl[hi] - cl[lo]; Bo = cb[hi] - cb[lo + 1]; To = ct[hi] - ct[lo + 1]; Mo = None       # corners lo+1 .. hi-1
                    for N in opts:
                        Ln, Bn, Tn, Mn = metrics(V[lo:i] + N + V[j + 1:hi + 1])
                        if Ln > Lo + 1e-3 or Bn > Bo or Tn > To + 1e-6: continue
                        if not (Bn < Bo or Ln < Lo - 1000.0): continue
                        if Mn > 90.5:
                            if Mo is None: Mo = max(tv[lo + 1:hi] or [0.0])
                            if Mn > Mo + 0.5: continue
                        key = (tuple(V[i:j + 1]), tuple(N))
                        if key in failed: continue
                        cands.append(((Lo - Ln) + lam * (Bo - Bn), i, j, N, key))
            cands.sort(key=lambda c: -c[0]); best = None; g0 = None
            for gain, i, j, N, key in cands:
                if g0 is not None and gain < g0 - TIE: break
                why = s.legal(r, i, j, N)
                if why is not None:
                    failed.add(key)
                    if stats is not None: stats[why[:40]] += 1
                    continue
                if g0 is None: g0 = gain
                mv = shapely.hausdorff_distance(LineString(mmpts(N)), LineString(mmpts(V[i:j + 1])), densify=0.1)
                if best is None or mv < best[0] - 1e-9: best = (mv, i, j, N)      # of near-equal savings take the one that moves least
            if best is None: break
            mv, i, j, N = best; r.pts = clean(V[:i] + N + V[j + 1:]); any_change = True
        new_segs = list(zip(r.pts, r.pts[1:])); old_segs = list(zip(r.orig, r.orig[1:]))
        r.changed = [tuple(sorted(x)) for x in new_segs] != [tuple(sorted(x)) for x in old_segs]
        if any_change or len(r.items) != len(new_segs):
            r.items = []
            for a, b in new_segs:
                it = Item('trk', r.net, LineString(mmpts([a, b])), r.w / 2 * MM, s.nc.get(r.net, 'Default')); r.items.append(it); s.idx[r.l].add(it)
        else:
            for it in r.items: it.alive = True
        return any_change


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]; O = dict((x[2:].split('=', 1) + ['1'])[:2] for x in sys.argv[1:] if x.startswith('--'))
    geo = json.load(open(a[0]))
    protect = json.load(open(O['protect'])) if 'protect' in O else PROTECT
    mv = {'*': float(O.get('maxmove', 0))}
    for k, v in O.items():
        if k.startswith('maxmove-'): mv[k[8:]] = float(v)
    opt = dict(maxmove=mv, lam=float(O.get('lam', 0.3)), span=int(O.get('span', 40)), pour=O.get('pour', '1') != '0')
    t0 = time.time(); B = Board(geo, protect, opt)
    only = re.compile(O['only']) if 'only' in O else None; skip = re.compile(O['skip']) if 'skip' in O else None
    runs = [r for r in B.runs if (only is None or only.search(r.net)) and not (skip and skip.search(r.net))]
    print('runs', len(B.runs), 'to work on', len(runs), 'frozen', sum(1 for r in B.runs if r.frozen), 'protected nets with tracks', len(B.prot), flush=True)
    stats = collections.Counter()
    for sweep in range(int(O.get('sweeps', 6))):
        nch = 0
        for r in runs:
            if B.optimise(r, stats): nch += 1
        print('sweep', sweep + 1, 'runs changed', nch, 'time %.0f s' % (time.time() - t0), flush=True)
        if nch == 0: break
    # ---- spec
    ch = [r for r in B.runs if r.changed]
    dele = set()
    for r in ch: dele.update(r.ids)
    grew = True
    while grew:                                                              # a split track drags its other run along
        grew = False
        for r in B.runs:
            if r not in ch and any(i in dele for i in r.ids): ch.append(r); dele.update(r.ids); grew = True
    add = []; rl = []
    for r in ch:
        for p, q in zip(r.pts, r.pts[1:]): add.append(dict(net=r.net, l=r.l, w=r.w, x1=p[0], y1=p[1], x2=q[0], y2=q[1]))
        Lo, Bo, To, Mo = metrics(r.orig); Ln, Bn, Tn, Mn = metrics(r.pts)
        rl.append(dict(net=r.net, l=r.l, w=r.w, a=r.orig[0], b=r.orig[-1], old=r.orig, new=r.pts, len0=Lo * MM, len1=Ln * MM, bends0=Bo, bends1=Bn, segs0=len(r.orig) - 1, segs1=len(r.pts) - 1))
    zero = [t['id'] for t in B.zero] + [i for i in B.dup_ids if i not in dele]
    spec = dict(**{'del': sorted(dele) + zero}, add=add, runs=rl, zero_or_duplicate_removed=len(zero), duplicates=[dict(net=n, l=l, a=p, b=q) for n, l, p, q in B.dup_log], frozen=[dict(net=n, l=l, why=w, a=p, b=q) for n, l, w, p, q in B.frozen_log],
                protected=B.prot, options=O)
    json.dump(spec, open(a[1], 'w'))
    nets = sorted({r['net'] for r in rl})
    print('rejected candidates by reason:', dict(stats.most_common(12)))
    print('changed runs', len(rl), 'in', len(nets), 'nets;  tracks removed', len(spec['del']), 'added', len(add), '(zero-length or duplicate removed %d)' % len(zero))
    print('length of the changed runs %.1f -> %.1f mm, bends %d -> %d' % (sum(x['len0'] for x in rl), sum(x['len1'] for x in rl), sum(x['bends0'] for x in rl), sum(x['bends1'] for x in rl)))
    if 'log' in O:
        with open(O['log'], 'w') as f:
            for n in nets:
                rr = [x for x in rl if x['net'] == n]
                f.write('%-34s runs %2d  %7.2f -> %7.2f mm  bends %3d -> %3d  segments %3d -> %3d\n' % (n[-34:], len(rr), sum(x['len0'] for x in rr), sum(x['len1'] for x in rr), sum(x['bends0'] for x in rr), sum(x['bends1'] for x in rr), sum(x['segs0'] for x in rr), sum(x['segs1'] for x in rr)))
            f.write('\nfrozen runs (left alone)\n')
            for n, l, w, p, q in B.frozen_log: f.write('  %s %s (%.3f, %.3f) to (%.3f, %.3f): %s\n' % (n, l, p[0] * MM, p[1] * MM, q[0] * MM, q[1] * MM, w))
            f.write('\nprotected nets (obstacles only)\n')
            for n, w in sorted(B.prot.items()): f.write('  %s: %s\n' % (n, w))

if __name__ == '__main__':
    main()
