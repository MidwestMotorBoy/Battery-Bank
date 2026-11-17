#!/usr/bin/env python3
"""runwidth.py geo_in.json spec_out.json [--only=regex] [--skip=regex] [--log=file] [options]

Gives every run of track one width. It only ever changes widths: a width change is a delete plus an add of the
identical geometry (same end points, layer, net). No point is moved. The only new nodes are split points ON the centre
line of an existing piece (to shorten a neck), so the copper outline of the centre lines is identical.
Nothing depends on track ids or absolute coordinates; a second run on the result gives an empty spec.

Graph (rwgraph.py): per net and layer; a run is the chain of pieces between two fixed points (pad, via, junction of
three or more, free end). Micro-pieces inside a node blob follow the runs that meet there (the larger).

Policy per run
  Default, Kelvin   target = the net's standard width (most common width by length among widths >= 0.2 mm when the net
                    has any, else its most common width; Kelvin never above 0.2 mm). Whole run at the target if
                    clearance allows. If only the stretch next to a pad cannot take it (pin escape): ONE neck from the
                    pad to the first point where the target fits (at an existing node, or at a split point when that
                    saves --gain mm of neck). If a piece in the middle cannot take it: the whole run gets the widest
                    standard width that fits everywhere (reported).
                    On inner layers and for runs that cross a drawn pour (zone priority > 0) of another net on F/B the
                    target is never above the run's present widest width (a wider track is a wider slot in a plane).
  GateDrive         target = the run's present widest width; same procedure; widths 0.4, 0.3, 0.25, 0.2 (0.15 only
                    where the run has it now). Every changed run is listed for the gate-loop solver.
  HighCurrent, Power, GND
                    never narrowed. Each narrower piece is widened to the run's widest width where clearance allows;
                    a piece that is blocked only along part of its length is split so that the neck is as short as
                    clearance needs; the blocked part gets the widest intermediate width that fits. Every neck that
                    remains is reported with position, width, length and what blocks it.
  blob pieces       take the largest width of the run ends that meet in the blob (never-narrow classes: only made
                    narrower when the copper they lose is covered by the pad / via / pour / other pieces of the net,
                    or when the piece is a dot shorter than 0.1 mm).
Never touched: the RF nets and the USB data pairs (EXCLUDE below) and whatever --skip matches.

Options
  --only=regex --skip=regex   net filter (python re.search)
  --log=file                  text report; file + '.json' gets the same as data
  --neck=1.5                  longest pin-escape neck (mm) for Default/Kelvin; GateDrive uses --gneck=2.0
  --gain=0.5                  split a piece to shorten a signal neck only if that saves this much (mm); --pgain=0.3 power
  --minrun=0.6                a necked run keeps its neck only if the full-width part is this long (mm) and at least half
                              as long as the neck; else the run is one width
  --island=1.5                never-narrow classes: a stretch that touches no wider stretch is raised to the run's widest
                              width only if it is this long (mm) and three times as long as wide
  --vianeck                   also allow a neck at a via end of a run (default: pads only)
  --inner-widen               allow Default/Kelvin runs on inner layers / in pours to go up to the net standard
  --hold=L:x,y[:r];...        do not widen pieces of layer L that pass within r (default 0.3) mm of x,y (mm)
  --no-pour                   skip the pour-neck test
  --strict-nodes              refuse a widening that makes a wider piece swallow a nearby node of its own net that is not
                              on its centre line (the audit's end_off_track; such nodes are node blobs that the
                              junctions pass removes) or lie side by side on another piece of its net (body_ovl).
                              Default: only split points are kept clear of this; whole pieces are widened and counted.
  --keep-bulges               never-narrow classes, strictly literal: narrow nothing at all (default: a wide piece that
                              is shorter than its own width and sits between two narrower stretches comes down to the wider
                              of the two if the run does not end with more squares, and covered blob pieces / dots follow
                              their runs)
"""
import sys, os, json, math, re, collections
HERE = os.path.dirname(os.path.abspath(__file__))
for d in (os.environ.get('GEOLIB_DIR'), os.path.join(HERE, '..', '..', 'tools'), os.path.join(HERE, '..', 'tools'), HERE):
    if d and os.path.exists(os.path.join(d, 'geolib.py')): sys.path.insert(0, d); break
sys.path.insert(0, HERE)
import geolib as G
import rwgraph as R
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

MM = 1e-6
EXCLUDE_NETS = ('/MCU/RFIO', '/MCU/ANT_IN', 'Net-(C313-Pad2)')
EXCLUDE_RE = (r'/DPDN', r'/D[PN]$', r'USB_D')
NEVER_NARROW = ('HighCurrent', 'Power', 'GND')
ORDER = ['HighCurrent', 'Power', 'GND', 'GateDrive', 'Kelvin', 'Default']
STD = [800000, 600000, 500000, 400000, 300000, 250000, 200000, 150000]
GATE = [400000, 300000, 250000, 200000]
SIG = [250000, 200000, 150000]
INNER = ('In1', 'In2', 'In3', 'In4')
EPS = 0.5            # nm
MARG = 3000          # nm added to a blocked interval before snapping
SNAP = 10000         # nm grid for split points
MINNECK = 200000     # nm shortest neck part made by a split
DOT = 100000         # nm: a blob piece shorter than this is a dot; it follows the runs even in the never-narrow classes
MINWIDE = 300000     # nm shortest wide part made by a split (or its width, if larger)
def minneck(T): return max(MINNECK, T // 2 + 20000)      # the node behind a neck part must stay outside the round end of the wide part

def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])
def sgn(v): return (v > 0) - (v < 0)
def mm(v): return '%g' % round(v * MM, 4)
def pmm(p): return '(%.3f, %.3f)' % (p[0] * MM, p[1] * MM)

class Ob(G.Obst):
    """geolib.Obst with track radii that can be updated and with the blocking geometry returned"""
    def __init__(s, g):
        super().__init__(g); s.pos = {}
        for l in G.LN:
            for k, it in enumerate(s.items[l]):
                if it[3] == 'track': s.pos[it[4]] = (l, k)
    def setw(s, tid, w):
        l, k = s.pos[tid]; it = s.items[l][k]; s.items[l][k] = (it[0], w / 2) + it[2:]
    def hits(s, net, l, a, b, w, tid):
        """what a piece a-b of width w on layer l would violate: [(gap, need, kind, name, net, geom, radius)]"""
        gm = Point(a) if a == b else LineString([a, b]); r = w / 2; out = []
        if s.tree[l] is None: return out
        for k in s.tree[l].query(gm.buffer(r + G.CLR_HC + 1300000)):
            og, orr, onet, okind, oname, ohole = s.items[l][k]
            if onet is not None and onet == net: continue
            if okind == 'track' and oname == tid: continue
            need = s.need(net, okind, onet); gap = gm.distance(og) - r - orr
            if gap < need - EPS: out.append((gap, need, okind, oname, onet, og, orr))
        for pg, name in s.kos[l]:
            if pg.intersects(gm.buffer(r)): out.append((-1, 0, 'keepout', name, None, pg, 0))
        return out
    def blocked(s, net, l, a, b, w, tid):
        """stretches of the centre line a-b that cannot be w wide: merged [(u0, u1, {blockers})] in nm from a"""
        L = dist(a, b); hs = s.hits(net, l, a, b, w, tid)
        if not hs: return []
        if L == 0: return [(0, 0, {bname(h) for h in hs})]
        seg = LineString([a, b]); iv = []
        for h in hs:
            reg = h[5].buffer((w / 2 if h[2] == 'keepout' else h[1] + w / 2 + h[6]) + MARG, 32)
            x = seg.intersection(reg)
            parts = [x] if x.geom_type == 'LineString' else [q for q in getattr(x, 'geoms', []) if q.geom_type == 'LineString']
            if not parts or x.is_empty: iv.append((0, L, {bname(h)})); continue
            for q in parts:
                c = list(q.coords); u = sorted(seg.project(Point(p)) for p in (c[0], c[-1]))
                iv.append((max(0, u[0] - MARG), min(L, u[1] + MARG), {bname(h)}))
        iv.sort(key=lambda v: v[0]); out = []
        for u0, u1, b_ in iv:
            if out and u0 <= out[-1][1] + 1: out[-1] = (out[-1][0], max(out[-1][1], u1), out[-1][2] | b_)
            else: out.append((u0, u1, set(b_)))
        return out

def bname(h):
    kind, name, net = h[2], h[3], h[4]
    if kind == 'track': return 'track of %s' % net
    if kind == 'pad': return 'pad %s (%s)' % (name, net)
    if kind in ('via', 'viahole'): return '%s of %s' % ('via' if kind == 'via' else 'via hole', net)
    if kind == 'keepout': return 'rule area %s' % (name or '?')
    return kind

class El:
    """one piece of a run, seen in run direction (a -> b)"""
    def __init__(s, t, flip, s0):
        s.t = t; s.w = t['w']; s.flip = flip
        p, q = (t['x1'], t['y1']), (t['x2'], t['y2'])
        s.a, s.b = (q, p) if flip else (p, q); s.L = dist(p, q); s.s0 = s0
        s.parts = [(0.0, s.L, s.w)]                 # (u0, u1, width) from a
        dx, dy = abs(q[0] - p[0]), abs(q[1] - p[1]); s.on45 = (dx == 0 or dy == 0 or dx == dy) and s.L > 0
    def pt(s, u):
        """integer point at distance u from a (u must come from snap(), or be 0 / L)"""
        if u <= 0: return s.a
        if u >= s.L: return s.b
        dx, dy = s.b[0] - s.a[0], s.b[1] - s.a[1]; n = max(abs(dx), abs(dy)); k = int(round(u / (s.L / n)))
        return (s.a[0] + sgn(dx) * k, s.a[1] + sgn(dy) * k)
    def snap(s, u, up):
        """u moved (up: towards b) to the next point of the SNAP grid on the piece; clipped to [0, L]"""
        if not s.on45: return None
        dx, dy = s.b[0] - s.a[0], s.b[1] - s.a[1]; n = max(abs(dx), abs(dy)); step = s.L / n
        c0, sg = (s.a[0], sgn(dx)) if dx else (s.a[1], sgn(dy))
        c = c0 + sg * (u / step)
        cs = (math.ceil(c / SNAP - 1e-9) if (sg > 0) == up else math.floor(c / SNAP + 1e-9)) * SNAP
        k = (cs - c0) * sg
        return max(0.0, min(s.L, k * step))

class Tool:
    def __init__(s, g, opt, log):
        s.g = g; s.opt = opt; s.nc = g['netclass']; s.log = log
        s.neck = float(opt.get('neck', 1.5)) / MM; s.gneck = float(opt.get('gneck', 2.0)) / MM
        s.minrun = float(opt.get('minrun', 0.6)) / MM; s.island = float(opt.get('island', 1.5)) / MM
        s.gain = float(opt.get('gain', 0.5)) / MM; s.pgain = float(opt.get('pgain', 0.3)) / MM
        s.vianeck = 'vianeck' in opt; s.innerw = 'inner-widen' in opt; s.strict = 'strict-nodes' in opt; s.soft = 0; s.notes = []
        s.holds = []
        for h in opt.get('hold', '').split(';'):
            if h.strip():
                f = h.split(':'); x, y = f[1].split(','); s.holds.append((f[0], Point(float(x) / MM, float(y) / MM), (float(f[2]) if len(f) > 2 else 0.3) / MM))
        s.power_zones = collections.defaultdict(list)
        for z in g['zones']:
            if z.get('prio', 0) > 0:
                for outer, holes in z['outline']:
                    if len(outer) >= 3:
                        for l in z['layers']: s.power_zones[l].append((Polygon(outer, holes), z['net']))
    def cls(s, net): return s.nc.get(net, 'Default')
    def active(s, net):
        if net in EXCLUDE_NETS or any(re.search(p, net) for p in EXCLUDE_RE): return False
        if s.opt.get('only') and not re.search(s.opt['only'], net): return False
        if s.opt.get('skip') and re.search(s.opt['skip'], net): return False
        return True
    def netstd(s):
        by = collections.defaultdict(lambda: collections.defaultdict(float))
        for t in s.g['tracks']: by[t['net']][t['w']] += R.plen(t)
        std = {}
        for n, d in by.items():
            big = {w: L for w, L in d.items() if w >= 200000} or d
            std[n] = max(sorted(big), key=lambda w: big[w])
            if s.cls(n) == 'Kelvin': std[n] = min(std[n], max(200000, min(d)))
        return std
    def capped(s, run):
        """is this run a slot in a plane or a cut in a drawn pour of another net?"""
        if run.l in INNER: return 'inner layer'
        zs = s.power_zones.get(run.l, [])
        for t, _ in run.el:
            gm = G.tgeom(t)
            for pg, net in zs:
                if net != run.net and pg.intersects(gm): return 'inside the drawn pour of %s' % net
        return None
    def held(s, l, a, b):
        if not s.holds: return False
        gm = Point(a) if a == b else LineString([a, b])
        return any(hl == l and gm.distance(p) <= r for hl, p, r in s.holds)
    # ---------------------------------------------------------------- tests
    def fits(s, e, u0, u1, w, cur=None):
        """may the part u0..u1 of element e be w wide? (always yes when that is not wider than it is now)"""
        if w <= (e.w if cur is None else cur): return True
        a, b = e.pt(u0), e.pt(u1)
        if s.held(e.t['l'], a, b): return False
        if s.ob.hits(e.t['net'], e.t['l'], a, b, w, e.t['id']): return False
        part = not (u0 <= 0 and u1 >= e.L)
        if part or s.strict:
            if s.swallows(e.t['net'], e.t['l'], a, b, w, e.w if cur is None else cur): return False
            if s.strict and s.overlaps(e.t['net'], e.t['l'], a, b, w, e.w if cur is None else cur, e.t['id']): return False
            if part and any(s.inbody(e.t['net'], e.t['l'], p, e.t['id']) for p in (a, b) if p not in (e.a, e.b)): return False
        elif s.swallows(e.t['net'], e.t['l'], a, b, w, e.w if cur is None else cur): s.soft += 1
        return s.pour_ok(e, a, b, w)
    def swallows(s, net, l, a, b, w, cur):
        """would the piece a-b, made w wide, cover a free node of its net that is not on its centre line (and that it did
        not cover before)?"""
        ni = s.nodes.get((net, l))
        if ni is None: return False
        tree, pts = ni
        for k in tree.query(LineString([a, b]).buffer(w / 2 + 1) if a != b else Point(a).buffer(w / 2 + 1)):
            p = pts[k]
            if p == a or p == b: continue
            d = R.seg_dist(p, a, b)
            if 1000 < d <= w / 2 and d > cur / 2: return True
        return False
    def overlaps(s, net, l, a, b, w, cur, tid):
        """would the piece a-b, made w wide, lie side by side on another piece of its net (the audit's body_ovl) where it
        did not before?"""
        ti = s.segs.get((net, l))
        if ti is None or a == b: return False
        tree, ts = ti; li = LineString([a, b]); La = li.length
        for k in tree.query(li.buffer(w)):
            t = ts[k]
            if t['id'] == tid: continue
            c, d = (t['x1'], t['y1']), (t['x2'], t['y2'])
            if c == d: continue
            lj = LineString([c, d]); share = len({a, b} & {c, d})
            def flag(wi):
                near = lj.intersection(li.buffer((wi + t['w']) / 4, cap_style=2)); ln = near.length if not near.is_empty else 0
                if ln <= 200000: return False
                cr = abs((b[0] - a[0]) * (d[1] - c[1]) - (b[1] - a[1]) * (d[0] - c[0])) / La / lj.length
                if cr < 0.02: return share == 0 and lj.distance(li) >= 1000
                return share == 0 or ln > max(wi, t['w']) * 1.5
            if flag(w) and not flag(cur): return True
        return False
    def inbody(s, net, l, p, tid):
        """is point p inside the copper of another piece of the net without being on its centre line?"""
        ti = s.segs.get((net, l))
        if ti is None: return False
        tree, ts = ti
        for k in tree.query(Point(p).buffer(500000)):
            t = ts[k]
            if t['id'] == tid: continue
            d = R.seg_dist(p, (t['x1'], t['y1']), (t['x2'], t['y2']))
            if 1000 < d <= t['w'] / 2 + 100000: return True
        return False
    def blk(s, e, w):
        """blocked stretches of element e at width w, in element coordinates"""
        if w <= e.w: return []
        if s.held(e.t['l'], e.a, e.b): return [(0, e.L, {'--hold'})]
        return s.ob.blocked(e.t['net'], e.t['l'], e.a, e.b, w, e.t['id'])
    def pour_ok(s, e, a, b, w):
        """A wider track must not cut or pinch a pour of another net on its layer: the room a pour has (everything grown
        by the pour clearance plus half the minimum pour width, and once more by 0.1 mm) may not fall apart round the
        piece where it was one before. (After straighten_ref.py.)"""
        if 'no-pour' in s.opt: return True
        l = e.t['l']; pz = s.pours.get(l)
        if not pz: return True
        gm = Point(a) if a == b else LineString([a, b])
        x0, y0, x1, y1 = gm.bounds; m = 1500000
        W = box(x0 - m, y0 - m, x1 + m, y1 + m)
        for znet, zclr, zminw, zgeom in pz:
            if znet == e.t['net']: continue
            if not zgeom.intersects(W): continue
            for extra in (0, 100000):
                d = zclr + zminw / 2 + extra; polys = []
                for k in s.ob.tree[l].query(W.buffer(1000000)):
                    og, orr, onet, okind, oname, ohole = s.ob.items[l][k]
                    if onet == znet and not ohole: continue
                    if okind == 'track' and oname == e.t['id']: continue
                    polys.append(og.buffer(orr + d, 8))
                base = unary_union(polys) if polys else None
                old = LineString([e.a, e.b]).buffer(e.w / 2 + d, 8) if e.a != e.b else Point(e.a).buffer(e.w / 2 + d, 8)
                new = unary_union([old, gm.buffer(w / 2 + d, 8)])
                So = W.difference(unary_union([base, old]) if base is not None else old)
                Sn = W.difference(unary_union([base, new]) if base is not None else new)
                co = [q for q in getattr(So, 'geoms', [So]) if q.geom_type == 'Polygon' and q.area > 2e10]
                cn = [q for q in getattr(Sn, 'geoms', [Sn]) if q.geom_type == 'Polygon' and q.area > 2e10]
                if not co: continue
                wb = W.boundary
                for q in co:
                    hit = [c for c in cn if c.intersects(q) and c.intersection(q).area > 2e10]
                    big = [c for c in hit if c.area > 3e11 or c.distance(wb) < 1]
                    if len(big) > 1 or (not hit and (q.area > 3e11 or q.distance(wb) < 1)):
                        s.pourblocks += 1; return False
        return True
    # ---------------------------------------------------------------- policies
    def best(s, e, u0, u1, cands, lo, hi):
        """widest candidate c with lo < c < hi that the part fits, else lo"""
        for c in cands:
            if lo < c < hi and s.fits(e, u0, u1, c): return c
        return lo
    def plan_signal(s, run, els, T0, cands, neckmax):
        Lt = els[-1].s0 + els[-1].L; wmin = min(e.w for e in els)
        okA = bool(run.a.pad or (s.vianeck and run.a.via)); okB = bool(run.b.pad or (s.vianeck and run.b.via))
        if run.a is run.b and not run.a.fixed: okA = okB = False
        tries = [T0] + [c for c in cands if wmin <= c < T0]
        if wmin < T0 and wmin not in tries: tries.append(wmin)
        note = []
        for T in tries:
            B = []
            for e in els:
                for u0, u1, bl in s.blk(e, T): B.append((e.s0 + u0, e.s0 + u1, bl))
            nA, nB, mid, blA, blB = 0.0, Lt, None, set(), set()
            for s0, s1, bl in B:
                cA = okA and s1 <= neckmax; cB = okB and Lt - s0 <= neckmax
                if cA and cB: cA, cB = (True, False) if s1 <= Lt - s0 else (False, True)
                if cA: nA = max(nA, s1); blA |= bl
                elif cB: nB = min(nB, s0); blB |= bl
                else: mid = (s0, s1, bl); break
            if mid is None and nA > 0 and nB < Lt and nA >= nB - MINWIDE: mid = (nA, nB, blA | blB)
            if mid is not None:
                e = next(x for x in els if x.s0 + x.L >= mid[0] - 1)
                note.append('%s mm does not fit at %s (%s)' % (mm(T), pmm(e.pt(e.snap(mid[0] - e.s0, False) or 0) if e.on45 else e.a), ', '.join(sorted(mid[2]))))
                continue
            # place the necks: parts = (element, u0, u1, 'A'|'B'|'run')
            lay = []; mn = minneck(T)
            def cutA(e):
                if e.s0 + e.L <= nA + 1 or nA <= 0: return e.L if nA > 0 and e.s0 + e.L <= nA + 1 else 0.0
                if e.s0 >= nA - 1: return 0.0
                u = e.snap(max(nA - e.s0, mn), True)
                if u is None or e.L - u < max(s.gain, T, MINWIDE): return e.L
                return u
            def cutB(e):
                if e.s0 >= nB - 1 and nB < Lt: return 0.0
                if e.s0 + e.L <= nB + 1 or nB >= Lt: return e.L
                u = e.snap(min(nB - e.s0, e.L - mn), False)
                if u is None or u < max(s.gain, T, MINWIDE): return 0.0
                return u
            for e in els:
                ua, ub = cutA(e), cutB(e)
                if ua > ub: ua = ub = (e.L if e.s0 + e.L / 2 < Lt / 2 else 0.0)
                if ua > 0: lay.append((e, 0.0, ua, 'A'))
                if ub > ua: lay.append((e, ua, ub, 'run'))
                if ub < e.L: lay.append((e, ub, e.L, 'B'))
            ok = all(s.fits(e, u0, u1, T) for e, u0, u1, k in lay if k == 'run')
            if not ok: note.append('%s mm: a wide part failed the exact check' % mm(T)); continue
            wide = sum(u1 - u0 for e, u0, u1, k in lay if k == 'run'); nk = Lt - wide
            if nk > 0 and wide < max(s.minrun, 0.5 * nk):
                note.append('%s mm fits only on %.2f mm next to a %.2f mm neck (%s)' % (mm(T), wide * MM, nk * MM, ', '.join(sorted(blA | blB)))); continue
            wn = {}
            for k in 'AB':
                P = [(e, u0, u1) for e, u0, u1, kk in lay if kk == k]
                if not P: continue
                lo = min(e.w for e, _, _ in P); wn[k] = lo
                for c in cands:
                    if lo < c < T and all(s.fits(e, u0, u1, c) for e, u0, u1 in P): wn[k] = c; break
                if wn[k] >= T: wn[k] = T
            for e in els: e.parts = []
            for e, u0, u1, k in lay: e.parts.append((u0, u1, T if k == 'run' else wn[k]))
            if note: s.notes.append((run, T0, T, note))
            return dict(T=T, T0=T0, note=note, neckA=(wn.get('A'), sorted(blA)), neckB=(wn.get('B'), sorted(blB)))
        return dict(T=None, T0=T0, note=note)
    def plan_power(s, run, els, cands):
        """Never narrows, and never gives a run more width changes than it has. The run is seen as stretches of one width:
          1. a wider stretch grows into its narrower neighbour, at its own width, as far as clearance allows (the piece
             where it has to stop is split, so the neck that stays is as short as it can be);
          2. a stretch that still is narrower than a neighbour is raised as a whole to the widest standard width that fits
             all along it, but not above its widest neighbour (no new peaks);
          3. exception to "no more width changes": a free stretch of at least --island mm that touches nothing wide is
             raised to the run's widest width (wide - neck - wide)."""
        T = max(e.w for e in els)
        at = [[e, p[0], p[1], p[2]] for e in els for p in e.parts if p[1] > p[0]]
        if not at: return dict(T=T)
        def stretches():
            st = []
            for k, a in enumerate(at):
                if st and at[st[-1][1]][3] == a[3]: st[-1][1] = k
                else: st.append([k, k])
            return st
        def clipblk(a, w):
            e, u0, u1, cur = a
            return [(max(b0, u0), min(b1, u1)) for b0, b1, _ in s.blk(e, w) if b1 > u0 and b0 < u1]
        def setw(k, f0, f1, w):
            """atom k: the part f0..f1 becomes w wide (split as needed); returns the number of atoms inserted before k+1"""
            e, u0, u1, cur = at[k]; new = []
            if f0 > u0: new.append([e, u0, f0, cur])
            new.append([e, f0, f1, w])
            if f1 < u1: new.append([e, f1, u1, cur])
            at[k:k + 1] = new
        def grow(k0, k1, LN, left):
            """the neighbour of width LN on the left (or right) grows into the stretch k0..k1: list of (k, f0, f1) or None"""
            ops = []; tot = 0.0; full = True
            for k in (range(k0, k1 + 1) if left else range(k1, k0 - 1, -1)):
                e, u0, u1, cur = at[k]; B = clipblk(at[k], LN)
                if not B:
                    if not s.fits(e, u0, u1, LN, cur): full = False; break
                    ops.append((k, u0, u1)); tot += u1 - u0; continue
                full = False
                if not e.on45: break
                mn = minneck(LN)
                if left:
                    f = e.snap(B[0][0], False)
                    if u1 - f < mn: f = e.snap(u1 - mn, False)
                    for _ in range(8):                      # pull back if the split point or the wide end is not clean
                        if f - u0 < MINNECK or s.fits(e, u0, f, LN, cur): break
                        f = e.snap(f - 100000, False)
                    if f - u0 < MINNECK or not s.fits(e, u0, f, LN, cur): break
                    ops.append((k, u0, f)); tot += f - u0
                else:
                    f = e.snap(B[-1][1], True)
                    if f - u0 < mn: f = e.snap(u0 + mn, True)
                    for _ in range(8):
                        if u1 - f < MINNECK or s.fits(e, f, u1, LN, cur): break
                        f = e.snap(f + 100000, True)
                    if u1 - f < MINNECK or not s.fits(e, f, u1, LN, cur): break
                    ops.append((k, f, u1)); tot += u1 - f
                break
            if not ops or (tot < s.pgain and not full): return None
            return ops
        def islands():
            for k0, k1 in stretches():
                if at[k0][3] >= T: continue
                # blocked intervals in stretch coordinates
                off = []; pos = 0.0; B = []
                for k in range(k0, k1 + 1):
                    e, u0, u1, cur = at[k]; off.append(pos)
                    bl = clipblk(at[k], T) if e.on45 else [(u0, u1)]
                    for b0, b1 in bl: B.append((pos + b0 - u0, pos + b1 - u0))
                    pos += u1 - u0
                B.sort(); free = []; u = 0.0
                for b0, b1 in B + [(pos, pos)]:
                    if b0 - u >= max(3 * T, s.island): free.append((u, b0))
                    u = max(u, b1)
                for f0, f1 in free[::-1]:
                    ops = []; ok = True
                    for k in range(k1, k0 - 1, -1):
                        e, u0, u1, cur = at[k]; a0 = off[k - k0]; a1 = a0 + u1 - u0
                        if a1 <= f0 or a0 >= f1: continue
                        g0 = u0 if f0 <= a0 else e.snap(u0 + f0 - a0, True); g1 = u1 if f1 >= a1 else e.snap(u0 + f1 - a0, False)
                        mn = minneck(T)
                        if g0 > u0 and g0 - u0 < mn: g0 = e.snap(u0 + mn, True)
                        if g1 < u1 and u1 - g1 < mn: g1 = e.snap(u1 - mn, False)
                        if g1 - g0 < MINNECK: ok = False; break
                        if not s.fits(e, g0, g1, T, cur): ok = False; break
                        ops.append((k, g0, g1))
                    if ok and ops and sum(o[2] - o[1] for o in ops) >= max(3 * T, s.island):
                        for k, g0, g1 in ops: setw(k, g0, g1, T)          # descending k: indices stay valid
                        return True
            return False
        def step():
            st = stretches(); cand = []
            for si, (k0, k1) in enumerate(st):
                cur = at[k0][3]
                l = at[st[si - 1][0]][3] if si > 0 else 0; r = at[st[si + 1][0]][3] if si + 1 < len(st) else 0
                if l > cur: cand.append((l, 0, si, True))
                if r > cur: cand.append((r, 0, si, False))
                if max(l, r) > cur: cand.append((max(l, r), 1, si, None))
            for lev, kind, si, left in sorted(cand, key=lambda c: (-c[0], c[1], c[2])):
                k0, k1 = st[si]; cur = at[k0][3]
                if kind == 0:
                    ops = grow(k0, k1, lev, left)
                    if ops:
                        for k, f0, f1 in sorted(ops, reverse=True): setw(k, f0, f1, lev)
                        return True
                else:
                    for c in cands:
                        if cur < c <= lev and all(s.fits(at[k][0], at[k][1], at[k][2], c, at[k][3]) for k in range(k0, k1 + 1)):
                            for k in range(k0, k1 + 1): at[k][3] = c
                            return True
            return False
        def write():
            for e in els: e.parts = []
            for e, u0, u1, w in at:
                if e.parts and e.parts[-1][2] == w: e.parts[-1] = (e.parts[-1][0], u1, w)
                else: e.parts.append((u0, u1, w))
            for e in els:
                if not e.parts: e.parts = [(0.0, e.L, e.w)]
        for rnd in range(4):
            n = 0
            while n < 40 and islands(): n += 1
            while n < 300 and step(): n += 1
            write()
            before = [tuple(e.parts) for e in els]
            s.bulges(run, els)
            if before == [tuple(e.parts) for e in els]: break
            at = [[e, p[0], p[1], p[2]] for e in els for p in e.parts if p[1] > p[0]]
        return dict(T=T)
    def bulges(s, run, els):
        """A wide stretch between two narrower ones (or between a narrower one and the pad / via at the end of the run):
          - shorter than twice its width: widening that this tool has just done is taken back down to the wider neighbour
            (no blob is created);
          - shorter than its own width: it is a micro-piece of the corner or blob it is in, not a wide piece of the run,
            and takes the wider of its two neighbours even if it was wide before, as long as the run as a whole does not
            end with more squares than it had (at the end of a run: only when the copper it loses is covered by the pad,
            the via, the net's own pour or other pieces)."""
        if 'keep-bulges' in s.opt: return
        sq0 = sum(e.L / e.w for e in els if e.L)
        for _ in range(60):
            flat = [(e, k, p[2], p[1] - p[0]) for e in els for k, p in enumerate(e.parts)]
            grp = []
            for i, f in enumerate(flat):
                if grp and grp[-1][0] == f[2]: grp[-1][1].append(i)
                else: grp.append([f[2], [i]])
            sq = sum(f[3] / f[2] for f in flat if f[3]); best = None
            for gi, (w, idx) in enumerate(grp):
                L = sum(flat[i][3] for i in idx)
                if L >= 2 * w or len(grp) < 2: continue
                lw = grp[gi - 1][0] if gi > 0 else None; rw = grp[gi + 1][0] if gi + 1 < len(grp) else None
                if (lw is not None and lw >= w) or (rw is not None and rw >= w): continue
                nw = max(x for x in (lw, rw) if x is not None)
                micro = L < w and all(len(flat[i][0].parts) == 1 for i in idx)
                if micro and (lw is None or rw is None) and not all(s.hidden(flat[i][0].t, nw) for i in idx): micro = False
                new = [nw if micro else max(nw, flat[i][0].w) for i in idx]
                if all(n >= flat[i][2] for n, i in zip(new, idx)): continue
                cost = sum(flat[i][3] / n - flat[i][3] / flat[i][2] for n, i in zip(new, idx)) if (lw is not None and rw is not None) else 0.0
                if micro and sq + cost > sq0 + 1e-9:
                    new = [max(nw, flat[i][0].w) for i in idx]
                    if all(n >= flat[i][2] for n, i in zip(new, idx)):
                        s.notes.append((run, w, None, ['bulge %s mm, %.2f mm long at %s kept: the run would end with more squares' % (mm(w), L * MM, pmm(flat[idx[0]][0].a))])); continue
                    cost = 0.0
                if best is None or cost < best[0]: best = (cost, idx, new, w, L)
            if best is None: return
            for n, i in zip(best[2], best[1]):
                e, k = flat[i][0], flat[i][1]; p = e.parts[k]; e.parts[k] = (p[0], p[1], n)
            for e in {flat[i][0] for i in best[1]}:
                m = []
                for p in e.parts:
                    if m and m[-1][2] == p[2]: m[-1] = (m[-1][0], p[1], p[2])
                    else: m.append(p)
                e.parts = m
            if any(flat[i][0].w > n for n, i in zip(best[2], best[1])): s.debulged.append((run, best[3], min(best[2]), best[4], flat[best[1][0]][0].a))
    def hidden(s, t, w):
        """would making piece t only w wide take away copper that is not covered by a pad, a via or another piece of its net?"""
        gm = G.tgeom(t); lost = gm.buffer(t['w'] / 2, 16).difference(gm.buffer(w / 2, 16)); l = t['l']; cov = []
        for k in s.ob.tree[l].query(lost):
            og, orr, onet, okind, oname, ohole = s.ob.items[l][k]
            if onet != t['net'] or ohole or (okind == 'track' and oname == t['id']): continue
            cov.append(og.buffer(orr, 16) if orr else og)
        for znet, zc, zw, zg in s.pours.get(l, []):
            if znet == t['net']: cov.append(zg)
        if cov: lost = lost.difference(unary_union(cov))
        return lost.is_empty or lost.buffer(-15000).is_empty
    def index_nodes(s, nets):
        """free nodes (not in a pad or via, not already inside another piece) and the pieces, per net and layer"""
        from shapely.strtree import STRtree
        s.nodes = {}; s.segs = {}; grp = collections.defaultdict(list)
        for t in s.g['tracks']:
            if t['net'] in nets: grp[(t['net'], t['l'])].append(t)
        padpoly = collections.defaultdict(list); vias = collections.defaultdict(list)
        for p in s.g['pads']:
            for l, pts in p['L'].items():
                if len(pts) >= 3 and p['net'] in nets: padpoly[(p['net'], l)].append(Polygon(pts))
        for v in s.g['vias']:
            if v['net'] in nets:
                for l in G.LN[G.LN.index(v['top']):G.LN.index(v['bot']) + 1]: vias[(v['net'], l)].append(v)
        for key, ts in grp.items():
            lines = [G.tgeom(t) for t in ts]; tree = STRtree(lines); s.segs[key] = (tree, ts)
            pts = {(t['x1'], t['y1']) for t in ts} | {(t['x2'], t['y2']) for t in ts}; free = []
            for p in pts:
                P = Point(p)
                if any(math.hypot(v['x'] - p[0], v['y'] - p[1]) <= v['d'] / 2 for v in vias.get(key, [])): continue
                if any(pg.covers(P) for pg in padpoly.get(key, [])): continue
                mids = False
                for k in tree.query(P.buffer(500000)):
                    t = ts[k]
                    if (t['x1'], t['y1']) == p or (t['x2'], t['y2']) == p: continue
                    if lines[k].distance(P) <= t['w'] / 2: mids = True; break
                if not mids: free.append(p)
            if free: s.nodes[key] = (STRtree([Point(p) for p in free]), free)
    # ---------------------------------------------------------------- one pass
    def one_pass(s):
        g = s.g; s.ob = Ob(g); s.pourblocks = 0; s.debulged = []
        s.pours = collections.defaultdict(list)
        if 'no-pour' not in s.opt:
            fl = collections.defaultdict(list)
            for f in g['fills']:
                for outer, holes in f['polys']:
                    if len(outer) >= 3: fl[(f['net'], f['l'])].append(Polygon(outer, holes))
            zinfo = {}
            for z in g['zones']:
                for l in z['layers']:
                    k = (z['net'], l); c, w = zinfo.get(k, (0, 0)); zinfo[k] = (max(c, z.get('clearance', 200000)), max(w, z.get('minw', 250000)))
            for (net, l), ps in fl.items():
                c, w = zinfo.get((net, l), (200000, 250000))
                s.pours[l].append((net, c, w, unary_union([p if p.is_valid else p.buffer(0) for p in ps])))
        nets = {t['net'] for t in g['tracks'] if s.active(t['net'])}
        runs, clusters, blobs = R.build(g, nets); std = s.netstd()
        s.index_nodes(nets)
        plan = {}; info = []
        def commit(els):
            for e in els:
                parts = [p for p in e.parts if p[1] > p[0] or e.L == 0]
                m = []
                for u0, u1, w in parts:
                    if m and m[-1][2] == w: m[-1] = (m[-1][0], u1, w)
                    else: m.append((u0, u1, w))
                if len(m) == 1 and m[0][2] == e.w: continue
                pts = [(e.pt(u0), e.pt(u1), w) for u0, u1, w in m]
                if e.flip: pts = [(b, a, w) for a, b, w in pts[::-1]]
                plan[e.t['id']] = pts; s.ob.setw(e.t['id'], max(w for _, _, w in m))
        def endw(t, end):
            p = plan.get(t['id'])
            if p is None: return t['w']
            return p[0][2] if end == 0 else p[-1][2]
        for cname in ORDER:
            rs = [r for r in runs if s.cls(r.net) == cname]
            rs.sort(key=lambda r: (r.net, r.l, min(min(t['x1'], t['x2']) for t, _ in r.el), min(min(t['y1'], t['y2']) for t, _ in r.el), -r.length()))
            for r in rs:
                els = []; pos = 0.0
                for t, fl in r.el: e = El(t, fl, pos); pos += e.L; els.append(e)
                wmax = max(e.w for e in els); wmin = min(e.w for e in els)
                if cname in NEVER_NARROW:
                    if wmax == wmin: continue
                    res = s.plan_power(r, els, STD)
                else:
                    if cname == 'GateDrive': T0 = wmax; cands = GATE; nk = s.gneck
                    else:
                        T0 = std[r.net]; cands = SIG; nk = s.neck
                        cap = None if s.innerw else s.capped(r)
                        if cap and T0 > wmax: T0 = wmax
                    if wmax == wmin == T0: continue
                    res = s.plan_signal(r, els, T0, cands, nk)
                commit(els)
                # hangers follow the nearest piece of the run
                for h in r.hang:
                    hm = ((h['x1'] + h['x2']) / 2, (h['y1'] + h['y2']) / 2)
                    e = min(els, key=lambda e: R.seg_dist(hm, e.a, e.b)); tw = max(p[2] for p in e.parts)
                    s.blob(h, tw, plan)
            # blob pieces of fixed clusters
            for t, c in blobs:
                if s.cls(t['net']) != cname: continue
                if c.ext: tw = max(endw(x, e) for x, e in c.ext)
                elif cname in ('Default', 'Kelvin'):
                    tw = std[t['net']]; mx = max(x['w'] for x in c.blob)
                    if (t['l'] in INNER and not s.innerw) and tw > mx: tw = mx
                else: tw = max(x['w'] for x in c.blob)
                s.blob(t, tw, plan)
        return plan
    def blob(s, t, tw, plan):
        if tw == t['w']: return
        e = El(t, False, 0.0); cname = s.cls(t['net'])
        if tw < t['w']:
            if cname in NEVER_NARROW and ('keep-bulges' in s.opt or (e.L >= DOT and not s.hidden(t, tw))): return
            w = tw
        else:
            w = t['w']
            for c in STD:
                if t['w'] < c <= tw and s.fits(e, 0, e.L, c): w = c; break
            if w == t['w']: return
        plan[t['id']] = [(e.a, e.b, w)]; s.ob.setw(t['id'], w)
    def apply(s, plan):
        """-> new geometry with the plan applied; new pieces remember the piece of the input board they are part of"""
        out = dict(s.g); tr = []; n = 0
        for t in s.g['tracks']:
            p = plan.get(t['id'])
            if p is None: tr.append(t); continue
            for a, b, w in p:
                q = dict(t); q.update(id='rw%d-%05d' % (s.npass, n), x1=a[0], y1=a[1], x2=b[0], y2=b[1], w=w); n += 1; tr.append(q)
        out['tracks'] = tr
        return out

def tidy(g0, g1):
    """merge parts of one input piece that ended with the same width; a piece that is as it was gets its id back"""
    by = collections.defaultdict(list); keep = []
    ids0 = {t['id']: t for t in g0['tracks']}
    for t in g1['tracks']:
        if t['id'] in ids0: keep.append(t)
        else: by[t['_id0']].append(t)
    for i0, parts in by.items():
        o = ids0[i0]; a = (o['x1'], o['y1'])
        parts.sort(key=lambda t: min(dist(a, (t['x1'], t['y1'])), dist(a, (t['x2'], t['y2']))))
        m = []
        for t in parts:
            p, q = (t['x1'], t['y1']), (t['x2'], t['y2'])
            if dist(a, q) < dist(a, p): p, q = q, p
            if m and m[-1][2] == t['w']: m[-1] = (m[-1][0], q, t['w'])
            else: m.append((p, q, t['w']))
        if len(m) == 1 and m[0][2] == o['w']: keep.append(o); continue
        for k, (p, q, w) in enumerate(m):
            t = dict(o); t.update(id='rw-%s-%d' % (i0, k), x1=p[0], y1=p[1], x2=q[0], y2=q[1], w=w); keep.append(t)
    out = dict(g1); out['tracks'] = keep
    return out

def make_spec(g0, g1):
    ids0 = {t['id'] for t in g0['tracks']}; ids1 = {t['id'] for t in g1['tracks']}
    add = [t for t in g1['tracks'] if t['id'] not in ids0]
    add.sort(key=lambda t: (t['net'], t['l'], t['x1'], t['y1'], t['x2'], t['y2']))
    return {'tag': 'rw', 'del': sorted(ids0 - ids1), 'add': [dict(net=t['net'], l=t['l'], w=t['w'], x1=t['x1'], y1=t['y1'], x2=t['x2'], y2=t['y2']) for t in add]}, add

def run_tool(g0, opt, log=lambda *a: None):
    for t in g0['tracks']: t['_id0'] = t['id']; t['_w0'] = t['w']
    g = g0; npass = 0
    while npass < 8:
        tool = Tool(g, opt, log); tool.npass = npass; plan = tool.one_pass()
        log('pass %d: %d pieces change (%d widenings refused by the pour test; %d widened pieces now cover a blob node at their end)' % (npass + 1, len(plan), tool.pourblocks, tool.soft))
        for r, T0, T, note in (tool.notes if plan else []):
            t0 = r.el[0][0]
            log('   %-11s %-30s %-3s run from %s, %.2f mm: %s%s' % (tool.cls(r.net), r.net[-30:], r.l, pmm((t0['x1'], t0['y1'])), r.length() * MM, '; '.join(note), '' if T is None else '  => %s mm' % mm(T)))
        for r, w, nw, L, at in (tool.debulged if plan else []):
            log('   %-11s %-30s %-3s bulge %s mm, %.2f mm long at %s -> %s mm' % (tool.cls(r.net), r.net[-30:], r.l, mm(w), L * MM, pmm(at), mm(nw)))
        if not plan: break
        g = tidy(g0, tool.apply(plan)); npass += 1
    # final check with the shared clearance model; anything it finds is put back to the old width
    for rnd in range(5):
        spec, add = make_spec(g0, g)
        if not spec['del']: break
        g1 = G.apply_spec(g0, spec); bad = G.clearance(g0, g1, spec)
        if not bad: break
        idx = {'new-rw-%05d' % k: t for k, t in enumerate(add)}
        log('final clearance check: %d findings, the pieces go back to their old width' % len(bad))
        for b in bad:
            t = idx[b['id']]; log('   back to %s mm: %s %s at %s  (%s %s, gap %s)' % (mm(t['_w0']), t['net'], t['l'], pmm(((t['x1'] + t['x2']) / 2, (t['y1'] + t['y2']) / 2)), b['to'], b['name'], b['gap']))
            t['w'] = t['_w0']
        g = tidy(g0, g)
    spec, add = make_spec(g0, g); spec.pop('tag', None)
    return spec, g

# -------------------------------------------------------------------------------------------------- report
def seq(pairs):
    out = []
    for w, L in pairs:
        if out and out[-1][0] == w: out[-1][1] += L
        else: out.append([w, L])
    return ' '.join('%s/%.2f' % (mm(w), L * MM) for w, L in out)

def report(g0, g1, opt, log):
    tool = Tool(g1, opt, log); tool.npass = 99; tool.ob = Ob(g1); tool.pours = {}; tool.pourblocks = 0
    opt2 = dict(opt); opt2['no-pour'] = '1'; tool.opt = opt2
    nc = g1['netclass']; cls = lambda n: nc.get(n, 'Default'); std = tool.netstd()
    data = collections.OrderedDict()
    # width table
    tab = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0, 0, 0]))
    for k, gg in ((0, g0), (1, g1)):
        for t in gg['tracks']:
            c = tab[cls(t['net'])][t['w']]; c[k] += R.plen(t) * MM; c[2 + k] += 1
    log('\nTrack length (mm) and pieces per net class and width, before -> after')
    data['table'] = {}
    for c in ORDER:
        if c not in tab: continue
        log('  %s' % c); data['table'][c] = {}
        for w in sorted(tab[c]):
            v = tab[c][w]; log('     %-5s mm  %8.2f -> %8.2f mm   (%4d -> %4d pieces)' % (mm(w), v[0], v[1], v[2], v[3])); data['table'][c][mm(w)] = [round(v[0], 3), round(v[1], 3), v[2], v[3]]
    nets = {t['net'] for t in g1['tracks'] if tool.active(t['net'])}
    runs, clusters, blobs = R.build(g1, nets)
    def ends(r):
        t, fl = r.el[0]; a = (t['x2'], t['y2']) if fl else (t['x1'], t['y1'])
        t, fl = r.el[-1]; b = (t['x1'], t['y1']) if fl else (t['x2'], t['y2'])
        def nm(c): return ('pad %s.%s' % (c.pad['ref'], c.pad['n'])) if c.pad else c.kind
        return '%s %s -> %s %s' % (nm(r.a), pmm(a), nm(r.b), pmm(b))
    changed = []; necks = []; uniform_low = []
    for r in sorted(runs, key=lambda r: (ORDER.index(cls(r.net)), r.net, r.l)):
        c = cls(r.net); old = [(t['_w0'], R.plen(t)) for t, _ in r.el]; new = [(t['w'], R.plen(t)) for t, _ in r.el]
        sq0 = sum(L / w for w, L in old); sq1 = sum(L / w for w, L in new)
        if any(a[0] != b[0] for a, b in zip(old, new)):
            changed.append(dict(cls=c, net=r.net, l=r.l, where=ends(r), length=round(r.length() * MM, 3), old=seq(old), new=seq(new), sq0=round(sq0, 2), sq1=round(sq1, 2)))
        ws = [w for w, _ in new]; T = max(ws)
        els = []; pos = 0.0
        for t, fl in r.el: e = El(t, fl, pos); pos += e.L; els.append(e)
        if len(set(ws)) > 1:
            # stretches narrower than the run's widest
            i = 0
            while i < len(els):
                if els[i].w >= T: i += 1; continue
                j = i
                while j + 1 < len(els) and els[j + 1].w < T: j += 1
                bl = set()
                for e in els[i:j + 1]:
                    for h in tool.ob.hits(e.t['net'], e.t['l'], e.a, e.b, T, e.t['id']): bl.add(bname(h))
                    if tool.held(e.t['l'], e.a, e.b): bl.add('--hold')
                L = sum(e.L for e in els[i:j + 1]); atpad = (i == 0 and r.a.pad) or (j == len(els) - 1 and r.b.pad)
                kind = 'pin escape' if atpad and L <= (tool.gneck if c == 'GateDrive' else tool.neck) + 1 else ('at a pad' if atpad else 'mid-run')
                necks.append(dict(cls=c, net=r.net, l=r.l, a=pmm(els[i].a), b=pmm(els[j].b), w=seq([(e.w, e.L) for e in els[i:j + 1]]), length=round(L * MM, 3), full=mm(T), kind=kind,
                                  pad=(r.a.pad if i == 0 and r.a.pad else r.b.pad if atpad else None) and '%s.%s' % ((r.a.pad if i == 0 and r.a.pad else r.b.pad)['ref'], (r.a.pad if i == 0 and r.a.pad else r.b.pad)['n']),
                                  blocked=sorted(bl) or ['pour test / nothing at this width (see text)']))
                i = j + 1
        if c in ('Default', 'Kelvin'):
            wrun = collections.Counter()
            for w, L in new: wrun[w] += L
            main = max(wrun, key=lambda w: wrun[w])
            if main < std[r.net]:
                cap = tool.capped(r); bl = set(); fit = True
                for e in els:
                    hs = tool.ob.hits(e.t['net'], e.t['l'], e.a, e.b, std[r.net], e.t['id'])
                    if hs: fit = False
                    for h in hs: bl.add(bname(h))
                uniform_low.append(dict(cls=c, net=r.net, l=r.l, where=ends(r), length=round(r.length() * MM, 3), w=mm(main), std=mm(std[r.net]), cap=cap, clearance_would_allow=fit, blocked=sorted(bl)))
    data['changed_runs'] = changed; data['necks'] = necks; data['below_standard'] = uniform_low
    for c in ('HighCurrent', 'Power', 'GND', 'GateDrive'):
        rs = [x for x in changed if x['cls'] == c]
        log('\n%s: %d runs changed (old widths/lengths -> new; squares = sum of length/width)' % (c, len(rs)))
        for x in rs: log('   %-30s %-3s %-58s L=%5.2f  %s  ->  %s   squares %.1f -> %.1f%s' % (x['net'][-30:], x['l'], x['where'], x['length'], x['old'], x['new'], x['sq0'], x['sq1'], '   MORE SQUARES' if x['sq1'] > x['sq0'] + 1e-6 and c != 'GateDrive' else ''))
    rs = [x for x in changed if x['cls'] in ('Default', 'Kelvin')]
    log('\nDefault / Kelvin: %d runs changed' % len(rs))
    for x in rs: log('   %-30s %-3s %-58s L=%5.2f  %s  ->  %s' % (x['net'][-30:], x['l'], x['where'], x['length'], x['old'], x['new']))
    log('\nNecks that remain (a stretch narrower than the widest width of its run): %d' % len(necks))
    for k in ('pin escape', 'at a pad', 'mid-run'):
        ns = [n for n in necks if n['kind'] == k]
        log('  %s: %d' % (k, len(ns)))
        for n in ns: log('   %-11s %-30s %-3s %s .. %s  %s (run %s)  %s  blocked by: %s' % (n['cls'], n['net'][-30:], n['l'], n['a'], n['b'], n['w'], n['full'], n['pad'] or '', '; '.join(n['blocked'][:4])))
    log('\nDefault / Kelvin runs below the standard width of their net: %d' % len(uniform_low))
    for x in uniform_low:
        why = ('not widened: %s (clearance alone would %sallow %s)' % (x['cap'], '' if x['clearance_would_allow'] else 'NOT ', x['std'])) if x['cap'] and not tool.innerw else 'blocked by: ' + '; '.join(x['blocked'][:4])
        log('   %-30s %-3s %-58s L=%5.2f  %s mm (net standard %s)  %s' % (x['net'][-30:], x['l'], x['where'], x['length'], x['w'], x['std'], why))
    # blob pieces that changed
    bch = collections.Counter(); bl_nn = []
    for t, c in blobs:
        if t['w'] != t['_w0']:
            bch[(cls(t['net']), 'wider' if t['w'] > t['_w0'] else 'narrower')] += 1
            if t['w'] < t['_w0'] and cls(t['net']) in NEVER_NARROW: bl_nn.append(dict(cls=cls(t['net']), net=t['net'], l=t['l'], at=pmm((t['x1'], t['y1'])), w0=mm(t['_w0']), w=mm(t['w']), len=round(R.plen(t) * MM, 3)))
    data['blob_changes'] = {'%s %s' % k: v for k, v in sorted(bch.items())}; data['blob_narrowed_power'] = bl_nn
    log('\nBlob pieces (both ends in one node blob / pad / via) that changed: %s' % (', '.join('%s %s %d' % (k[0], k[1], v) for k, v in sorted(bch.items())) or 'none'))
    log('  of these, made narrower in a never-narrow class (only where the pad, via, pour or other pieces of the net cover the lost copper): %d' % len(bl_nn))
    for x in bl_nn: log('   %-11s %-30s %-3s %s  %s -> %s mm, %.2f long' % (x['cls'], x['net'][-30:], x['l'], x['at'], x['w0'], x['w'], x['len']))
    # blobs that still differ
    odd = []
    for t, c in blobs:
        ws = {x['w'] for x, _ in c.ext}
        if ws and t['w'] > max(ws): odd.append(dict(cls=cls(t['net']), net=t['net'], l=t['l'], at=pmm((t['x1'], t['y1'])), w=mm(t['w']), runs=[mm(w) for w in sorted(ws)], len=round(R.plen(t) * MM, 3)))
    data['wide_blob_pieces'] = odd
    log('\nShort pieces in a node blob that stay wider than every run that meets there (never-narrow classes, copper not covered): %d' % len(odd))
    for x in odd: log('   %-11s %-30s %-3s %s  %s mm, %.2f long; runs there: %s' % (x['cls'], x['net'][-30:], x['l'], x['at'], x['w'], x['len'], ', '.join(x['runs'])))
    return data

def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]; opt = dict((x[2:].split('=', 1) + ['1'])[:2] for x in sys.argv[1:] if x.startswith('--'))
    if len(a) < 2: print(__doc__); sys.exit(2)
    lines = []
    def log(*x):
        s = ' '.join(str(v) for v in x); lines.append(s)
        if 'quiet' not in opt: print(s)
    g0 = G.load(a[0]); spec, g1 = run_tool(g0, opt, log)
    json.dump(spec, open(a[1], 'w'))
    log('spec: %d deleted, %d added -> %s' % (len(spec['del']), len(spec['add']), a[1]))
    data = report(g0, g1, opt, log)
    if 'log' in opt:
        open(opt['log'], 'w').write('\n'.join(lines) + '\n'); json.dump(data, open(opt['log'] + '.json', 'w'), indent=1)

if __name__ == '__main__': main()
