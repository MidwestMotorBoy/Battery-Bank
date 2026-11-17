#!/usr/bin/env python3
"""rwgraph.py: the run graph used by runwidth.py (import only).

Per net and layer the track pieces are turned into a graph of CLUSTERS (nodes) and RUNS:
  cluster  one or more end points that are the same place electrically:
             - the same point,
             - the two ends of a micro-piece (a piece shorter than its own width),
             - an end that lies inside the round end of another piece (a "near miss", joined by copper only),
             - all ends inside one via, all ends inside one pad of the net.
           A cluster is FIXED when it is at a pad, at a via, has other than two run pieces leaving it, or lies on the
           body of another piece (a tee without a node on the through piece).
  blob     pieces with both ends in one cluster (micro-pieces of a node blob, pieces inside a pad or via)
  run      the chain of pieces from one fixed cluster to the next. Micro-pieces that sit in the chain (in a cluster
           that is not fixed) are members of the run, in order.
Nothing here depends on track ids or absolute coordinates."""
import math, collections
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

LN = ['F', 'In1', 'In2', 'In3', 'In4', 'B']
MICRO = 200000      # nm: a piece shorter than its own width AND shorter than this is a micro-piece

def plen(t): return math.hypot(t['x2'] - t['x1'], t['y2'] - t['y1'])
def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    if L2 == 0: return math.hypot(px - ax, py - ay)
    u = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - u * dx, py - ay - u * dy)

class UF:
    def __init__(s, n): s.p = list(range(n))
    def f(s, a):
        while s.p[a] != a: s.p[a] = s.p[s.p[a]]; a = s.p[a]
        return a
    def u(s, a, b):
        a, b = s.f(a), s.f(b)
        if a != b: s.p[max(a, b)] = min(a, b)

class Cluster:
    __slots__ = ('k', 'pts', 'pad', 'via', 'tee', 'ext', 'blob', 'fixed', 'kind')
    def __init__(s, k): s.k = k; s.pts = []; s.pad = None; s.via = None; s.tee = False; s.ext = []; s.blob = []; s.fixed = False; s.kind = ''

class Run:
    """el: ordered list of (piece, flipped) ; a, b: the clusters at its two ends; hang: blob pieces that sit in the chain
    but not on the path (they follow the run's width)"""
    __slots__ = ('net', 'l', 'el', 'a', 'b', 'hang', 'cls')
    def __init__(s, net, l): s.net = net; s.l = l; s.el = []; s.a = None; s.b = None; s.hang = []
    def length(s): return sum(plen(t) for t, _ in s.el)
    def widths(s): return [t['w'] for t, _ in s.el]

def build(g, nets=None):
    """-> (runs, clusters_by_group, blobs) where blobs = [(piece, cluster)] for blob pieces of FIXED clusters"""
    padpoly = collections.defaultdict(list); vias = collections.defaultdict(list)
    for p in g['pads']:
        for l, pts in p['L'].items():
            if len(pts) >= 3: padpoly[(p['net'], l)].append((Polygon(pts), p))
    for v in g['vias']:
        for l in LN[LN.index(v['top']):LN.index(v['bot']) + 1]: vias[(v['net'], l)].append(v)
    groups = collections.defaultdict(list)
    for t in g['tracks']:
        if nets is None or t['net'] in nets: groups[(t['net'], t['l'])].append(t)
    runs = []; blobs = []; allcl = {}
    for (net, l) in sorted(groups):
        ts = groups[(net, l)]
        pidx = {}; pts = []
        def nid(p):
            if p not in pidx: pidx[p] = len(pts); pts.append(p)
            return pidx[p]
        ends = [(nid((t['x1'], t['y1'])), nid((t['x2'], t['y2']))) for t in ts]
        uf = UF(len(pts))
        L = [plen(t) for t in ts]
        for i, t in enumerate(ts):
            if L[i] < min(t['w'], MICRO): uf.u(*ends[i])
        nbr = collections.defaultdict(set)
        for a, b in ends: nbr[a].add(b); nbr[b].add(a)
        # pads and vias
        pp = padpoly.get((net, l), []); vv = vias.get((net, l), [])
        npad = {}; nvia = {}
        first = {}
        for n, p in enumerate(pts):
            for v in vv:
                if math.hypot(v['x'] - p[0], v['y'] - p[1]) <= v['d'] / 2:
                    nvia[n] = v; key = ('v', v['id'])
                    if key in first: uf.u(n, first[key])
                    else: first[key] = n
                    break
            P = Point(p)
            for poly, pad in pp:
                if poly.covers(P):
                    npad[n] = pad; key = ('p', pad['ref'], pad['n'])
                    if key in first: uf.u(n, first[key])
                    else: first[key] = n
                    break
        # ends inside the copper of another piece
        lines = [LineString([pts[a], pts[b]]) if a != b else Point(pts[a]) for a, b in ends]
        tree = STRtree(lines); tee = set()
        for n, p in enumerate(pts):
            P = Point(p)
            for j in tree.query(P.buffer(1000000)):
                a, b = ends[j]
                if n == a or n == b or a in nbr[n] or b in nbr[n]: continue
                w2 = ts[j]['w'] / 2
                if seg_dist(p, pts[a], pts[b]) > w2 + 1: continue
                da = math.hypot(p[0] - pts[a][0], p[1] - pts[a][1]); db = math.hypot(p[0] - pts[b][0], p[1] - pts[b][1])
                if min(da, db) <= w2 + 1: uf.u(n, a if da <= db else b)
                else: tee.add(n)
        cl = {}
        for n, p in enumerate(pts):
            k = uf.f(n)
            c = cl.get(k)
            if c is None: c = cl[k] = Cluster((net, l, k))
            c.pts.append(n)
            if n in npad: c.pad = npad[n]
            if n in nvia: c.via = nvia[n]
            if n in tee: c.tee = True
        isblob = [uf.f(a) == uf.f(b) for a, b in ends]
        for i, t in enumerate(ts):
            a, b = ends[i]
            if isblob[i]: cl[uf.f(a)].blob.append(i)
            else: cl[uf.f(a)].ext.append((i, 0)); cl[uf.f(b)].ext.append((i, 1))
        for c in cl.values():
            c.fixed = bool(c.pad or c.via or c.tee or len(c.ext) != 2)
            c.kind = 'pad' if c.pad else 'via' if c.via else 'tee' if (c.tee or len(c.ext) > 2) else 'end' if len(c.ext) < 2 else 'mid'
        def chain_blobs(c, n_in, n_out):
            """micro-pieces of a chain cluster: (ordered path pieces from node n_in to n_out as (i, flipped), the others)"""
            if not c.blob: return [], []
            adj = collections.defaultdict(list)
            for i in c.blob:
                a, b = ends[i]; adj[a].append((i, b)); adj[b].append((i, a))
            prev = {n_in: None}; q = [n_in]
            while q:
                x = q.pop(0)
                if x == n_out: break
                for i, y in adj[x]:
                    if y not in prev: prev[y] = (x, i); q.append(y)
            path = []
            if n_out in prev:
                x = n_out
                while prev[x] is not None:
                    px, i = prev[x]; path.append((i, ends[i][0] != px)); x = px
                path.reverse()
            on = {i for i, _ in path}
            return path, [i for i in c.blob if i not in on]
        seen = set()
        def walk(c0, i, e):
            r = Run(net, l); r.a = c0; cur = (i, e)
            while True:
                i, e = cur; seen.add(i); r.el.append((ts[i], e == 1))
                far = ends[i][1 - e]; c = cl[uf.f(far)]
                if c.fixed or c is c0 and not c0.fixed: r.b = c; break
                nxt = [x for x in c.ext if x[0] != i]
                if len(nxt) != 1 or nxt[0][0] in seen: r.b = c; break
                path, rest = chain_blobs(c, far, ends[nxt[0][0]][nxt[0][1]])
                for j, fl in path: r.el.append((ts[j], fl)); seen.add(j)
                r.hang += [ts[j] for j in rest]
                cur = nxt[0]
            runs.append(r)
        for c in cl.values():
            if c.fixed:
                for i, e in c.ext:
                    if i not in seen: walk(c, i, e)
        for c in cl.values():                      # closed loops without a fixed point
            if not c.fixed:
                for i, e in c.ext:
                    if i not in seen: walk(c, i, e)
        for c in cl.values():
            if c.fixed:
                for i in c.blob: blobs.append((ts[i], c))
        allcl[(net, l)] = list(cl.values())
        # give the clusters real pieces instead of indices
        for c in cl.values():
            c.ext = [(ts[i], e) for i, e in c.ext]; c.blob = [ts[i] for i in c.blob]
            c.pts = [pts[n] for n in c.pts]
    return runs, allcl, blobs
