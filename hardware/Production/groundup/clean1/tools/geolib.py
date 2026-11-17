#!/usr/bin/env python3
"""geolib.py: shared helpers for track edits on a dumpgeo.py dump (integer nanometres). Plain python 3 + shapely.

  load(fn)                       -> geo dict
  apply_spec(geo, spec)          -> new geo dict with the spec applied to 'tracks' (everything else shared, fills are stale)
  connectivity(geo)              -> {net: partition of terminals}, orphans   (KiCad-like: a track joins what its END POINTS touch)
  clearance(geo_before, geo_after, spec) -> list of violations of the new tracks
  excursion(geo_before, spec)    -> how far new centre lines leave the old copper of their net+layer
  check(geo_before, spec, ...)   -> dict with everything, 'ok' True/False     (CLI: chk.py)

Spec format (same as straighten.py / straighten_apply.py):
  {"del": [track ids], "add": [{"net": str, "l": "F|In2|In3|In4|B", "w": nm, "x1": nm, "y1": nm, "x2": nm, "y2": nm}, ...]}
A width change is a del + add of the same geometry. Vias, pads, zones, parts are never edited.
"""
import json, math, collections, uuid
from shapely.geometry import LineString, Point, Polygon, box
from shapely.strtree import STRtree
from shapely.ops import unary_union

LN = ['F', 'In1', 'In2', 'In3', 'In4', 'B']
MM = 1e-6
CLR, CLR_HC, CLR_HOLE, CLR_EDGE, MINW = 150000, 250000, 200000, 250000, 150000
NOT_DEFAULT = ('HighCurrent', 'Power', 'GND', 'GateDrive', 'Kelvin')

def load(fn): return json.load(open(fn))
def P(t): return (t['x1'], t['y1']), (t['x2'], t['y2'])
def tlen(t): return math.hypot(t['x2'] - t['x1'], t['y2'] - t['y1'])
def on45(t):
    dx, dy = abs(t['x2'] - t['x1']), abs(t['y2'] - t['y1'])
    return dx == 0 or dy == 0 or dx == dy
def tgeom(t):
    a, b = P(t)
    return Point(a) if a == b else LineString([a, b])

def apply_spec(g, spec):
    dele = set(spec.get('del', [])); ids = {t['id'] for t in g['tracks']}
    missing = dele - ids
    if missing: raise ValueError('spec deletes unknown track ids: %s' % sorted(missing)[:5])
    out = dict(g); tr = [t for t in g['tracks'] if t['id'] not in dele]; n = 0
    for s in spec.get('add', []):
        for k in ('x1', 'y1', 'x2', 'y2', 'w'):
            if int(s[k]) != s[k]: raise ValueError('non-integer nm in add: %r' % s)
        if s['l'] not in LN: raise ValueError('bad layer %r' % s)
        t = dict(id=s.get('id') if s.get('id') and s.get('id') not in ids else str(uuid.uuid4()), x1=int(s['x1']), y1=int(s['y1']), x2=int(s['x2']), y2=int(s['y2']), w=int(s['w']), l=s['l'], net=s['net'], locked=False, new=True)
        n += 1; ids.add(t['id']); tr.append(t)
    out['tracks'] = tr
    return out

def merge_specs(specs):
    """several specs made against the SAME base board -> one; error if two of them delete the same track"""
    seen = {}; out = dict(**{'del': [], 'add': []})
    for name, s in specs:
        for i in s.get('del', []):
            if i in seen: raise ValueError('track %s deleted by both %s and %s' % (i, seen[i], name))
            seen[i] = name; out['del'].append(i)
        out['add'] += s.get('add', [])
    return out

# ------------------------------------------------------------------------------------------------ connectivity
class UF:
    def __init__(s): s.p = {}
    def f(s, a):
        s.p.setdefault(a, a)
        while s.p[a] != a: s.p[a] = s.p[s.p[a]]; a = s.p[a]
        return a
    def u(s, a, b): s.p[s.f(a)] = s.f(b)

def _index(g):
    pads = collections.defaultdict(list); vias = collections.defaultdict(list); fills = collections.defaultdict(list)
    for p in g['pads']:
        for l, pts in p['L'].items():
            if len(pts) >= 3: pads[(p['net'], l)].append((Polygon(pts), p))
    for v in g['vias']:
        for l in LN[LN.index(v['top']):LN.index(v['bot']) + 1]: vias[(v['net'], l)].append(v)
    for f in g['fills']:
        for k, (outer, holes) in enumerate(f['polys']):
            if len(outer) >= 3: fills[(f['net'], f['l'])].append((Polygon(outer, holes), '%s|%s|%s|%d' % (f['net'], f['l'], f['name'], k)))
    return pads, vias, fills

def connectivity(g, nets=None):
    """KiCad-like rule: a track is joined to an item when one of its END POINTS lies in that item's copper
    (other track body, pad outline, via pad, zone fill of the net as it was in the dump). Returns
    (part, orphans): part[net] = frozenset of frozensets of terminals ('pad:REF.N', 'via:ID'); orphans[net] = number
    of track groups that reach no pad or via."""
    pads, vias, fills = _index(g); by = collections.defaultdict(list)
    for t in g['tracks']: by[t['net']].append(t)
    allnets = set(by) | {k[0] for k in pads} | {k[0] for k in vias}
    part = {}; orph = {}
    for net in sorted(allnets):
        if nets is not None and net not in nets: continue
        uf = UF(); terms = set()
        for l in LN:
            ts = [t for t in by.get(net, []) if t['l'] == l]; pp = pads.get((net, l), []); vv = vias.get((net, l), []); ff = fills.get((net, l), [])
            for poly, p in pp: terms.add('pad:%s.%s' % (p['ref'], p['n'])); uf.f('pad:%s.%s' % (p['ref'], p['n']))
            for v in vv: terms.add('via:' + v['id']); uf.f('via:' + v['id'])
            geoms = [tgeom(t) for t in ts]; tree = STRtree(geoms) if ts else None
            for i, t in enumerate(ts):
                uf.f('t:' + t['id'])
                for e in P(t):
                    pe = Point(e)
                    for j in tree.query(pe.buffer(2500000)):
                        if j != i and geoms[j].distance(pe) <= ts[j]['w'] / 2 + 1: uf.u('t:' + t['id'], 't:' + ts[j]['id'])
                    for poly, p in pp:
                        if poly.covers(pe): uf.u('t:' + t['id'], 'pad:%s.%s' % (p['ref'], p['n']))
                    for v in vv:
                        if math.hypot(v['x'] - e[0], v['y'] - e[1]) <= v['d'] / 2 + 1: uf.u('t:' + t['id'], 'via:' + v['id'])
                    for poly, name in ff:
                        if poly.covers(pe): uf.u('t:' + t['id'], 'fill:' + name)
            for v in vv:
                pv = Point(v['x'], v['y'])
                for poly, p in pp:
                    if poly.covers(pv): uf.u('via:' + v['id'], 'pad:%s.%s' % (p['ref'], p['n']))
                for poly, name in ff:
                    if poly.covers(pv): uf.u('via:' + v['id'], 'fill:' + name)
                for v2 in vv:
                    if v2 is not v and math.hypot(v['x'] - v2['x'], v['y'] - v2['y']) <= (v['d'] + v2['d']) / 4: uf.u('via:' + v['id'], 'via:' + v2['id'])
            for poly, p in pp:
                for poly2, name in ff:
                    if poly.intersects(poly2): uf.u('pad:%s.%s' % (p['ref'], p['n']), 'fill:' + name)
        comp = collections.defaultdict(set)
        for k in list(uf.p): comp[uf.f(k)].add(k)
        part[net] = frozenset(frozenset(x for x in c if x in terms) for c in comp.values() if any(x in terms for x in c))
        orph[net] = sum(1 for c in comp.values() if not any(x in terms for x in c) and any(x.startswith('t:') for x in c))
    return part, orph

# ------------------------------------------------------------------------------------------------ clearance
class Obst:
    """everything a track must keep away from, per layer"""
    def __init__(s, g):
        s.g = g; s.nc = g['netclass']; s.items = {l: [] for l in LN}       # (geom, radius, net, kind, name, is_hole)
        for v in g['vias']:
            pt = Point(v['x'], v['y'])
            for l in LN:
                if l in v['flash']: s.items[l].append((pt, v['d'] / 2, v['net'], 'via', v['id'], False))
                else: s.items[l].append((pt, v['drill'] / 2, v['net'], 'viahole', v['id'], True))
        for p in g['pads']:
            for l, poly in p['L'].items():
                if len(poly) >= 3: s.items[l].append((Polygon(poly), 0, p['net'], 'pad', p['ref'] + '.' + p['n'], False))
            if p['hole'] and (p['npth'] or not p['L']):
                h = p['hole']; a, b = (h[0], h[1]), (h[2], h[3]); gm = Point(a) if a == b else LineString([a, b])
                for l in LN: s.items[l].append((gm, h[4] / 2, None, 'hole', p['ref'] + '.' + p['n'], True))
        for outline, holes in g['edge']:
            for ring in [outline] + holes:
                gm = LineString(ring + [ring[0]])
                for l in LN: s.items[l].append((gm, 0, None, 'edge', 'edge', False))
        s.kos = {l: [] for l in LN}
        for k in g['keepouts']:
            if not k.get('notracks'): continue
            for outline, holes in k['polys']:
                pg = Polygon(outline, holes)
                for l in k['layers']: s.kos[l].append((pg, k['name']))
        s.ntrk = len(g['tracks'])
        for t in g['tracks']: s.items[t['l']].append((tgeom(t), t['w'] / 2, t['net'], 'track', t['id'], False))
        s.tree = {l: STRtree([i[0] for i in s.items[l]]) if s.items[l] else None for l in LN}
    def need(s, net, okind, onet):
        if okind == 'hole': return CLR_HOLE
        if okind == 'viahole':                      # KiCad applies the 0.25 mm HighCurrent rule to the barrel of an unflashed via as well
            a, b = s.nc.get(net, 'Default'), s.nc.get(onet, 'Default')
            return CLR_HC if ((a == 'HighCurrent' and b not in NOT_DEFAULT) or (b == 'HighCurrent' and a not in NOT_DEFAULT)) else CLR_HOLE
        if okind == 'edge': return CLR_EDGE
        a, b = s.nc.get(net, 'Default'), s.nc.get(onet, 'Default')
        if okind != 'pad' and ((a == 'HighCurrent' and b not in NOT_DEFAULT) or (b == 'HighCurrent' and a not in NOT_DEFAULT)): return CLR_HC
        return CLR
    def near(s, t, slack=0):
        """[(gap_nm, need_nm, kind, name, net)] for every other-net item closer than its required clearance + slack"""
        gm = tgeom(t); r = t['w'] / 2; out = []; l = t['l']
        if s.tree[l] is None: return out
        for k in s.tree[l].query(gm.buffer(r + CLR_HC + slack + 1300000)):
            og, orr, onet, okind, oname, ohole = s.items[l][k]
            if onet == t['net'] and okind != 'viahole' and onet is not None: continue
            if okind == 'viahole' and onet == t['net']: continue
            if okind == 'track' and oname == t['id']: continue
            need = s.need(t['net'], okind, onet); gap = gm.distance(og) - r - orr
            if gap < need + slack: out.append((gap, need, okind, oname, onet))
        for pg, name in s.kos[l]:
            if pg.intersects(gm.buffer(r)): out.append((-1, 0, 'keepout', name, None))
        return out

def clearance(g0, g1, spec, tol=1000):
    """violations of the new tracks of g1 (those not in g0). A gap that is short of the rule is still accepted when the
    removed tracks of the same net and layer were at least as close to the same item (grandfathered)."""
    ids0 = {t['id'] for t in g0['tracks']}; new = [t for t in g1['tracks'] if t['id'] not in ids0]
    dele = set(spec.get('del', [])); old = collections.defaultdict(list)
    for t in g0['tracks']:
        if t['id'] in dele: old[(t['net'], t['l'])].append(t)
    ob1 = Obst(g1); ob0 = Obst(g0); bad = []
    oldgap = {}
    for t in new:
        for gap, need, kind, name, onet in ob1.near(t):
            if gap >= need - tol: continue
            key = (t['net'], t['l'], kind, name)
            if key not in oldgap:
                best = None
                for o in old.get((t['net'], t['l']), []):
                    for g_, n_, k_, nm_, on_ in ob0.near(o):
                        if k_ == kind and nm_ == name: best = g_ if best is None else min(best, g_)
                oldgap[key] = best
            if oldgap[key] is not None and gap >= oldgap[key] - tol: continue
            bad.append(dict(net=t['net'], l=t['l'], x=round((t['x1'] + t['x2']) / 2 * MM, 3), y=round((t['y1'] + t['y2']) / 2 * MM, 3), gap=round(gap * MM, 4), need=need * MM,
                            to=kind, name=name, tonet=onet, was=None if oldgap[key] is None else round(oldgap[key] * MM, 4), id=t['id']))
    return bad

def excursion(g0, g1, step=50000):
    """per net+layer: the largest distance of a point on a new centre line from the old centre lines of that net and layer"""
    ids0 = {t['id'] for t in g0['tracks']}; ids1 = {t['id'] for t in g1['tracks']}
    new = collections.defaultdict(list); oldall = collections.defaultdict(list)
    for t in g1['tracks']:
        if t['id'] not in ids0: new[(t['net'], t['l'])].append(t)
    for t in g0['tracks']: oldall[(t['net'], t['l'])].append(t)
    out = {}
    for k, ts in new.items():
        if not oldall.get(k): out[k] = (float('inf'), None); continue
        U = unary_union([tgeom(t) for t in oldall[k]]); worst = 0; where = None
        for t in ts:
            gm = tgeom(t); L = gm.length; n = max(1, int(L // step))
            for i in range(n + 1):
                q = gm.interpolate(L * i / n) if L else gm
                d = U.distance(q)
                if d > worst: worst = d; where = (round(q.x * MM, 3), round(q.y * MM, 3))
        out[k] = (worst * MM, where)
    return out

def check(g0, spec, maxexc=None, audit_fn=None, verbose=True):
    import audit as A
    g1 = apply_spec(g0, spec); res = collections.OrderedDict(); ok = True
    ids0 = {t['id'] for t in g0['tracks']}; new = [t for t in g1['tracks'] if t['id'] not in ids0]
    res['tracks'] = [len(g0['tracks']), len(g1['tracks'])]; res['deleted'] = len(spec.get('del', [])); res['added'] = len(new)
    res['nets_changed'] = sorted({t['net'] for t in new} | {t['net'] for t in g0['tracks'] if t['id'] in set(spec.get('del', []))})
    # form of the new tracks
    res['new_zero_length'] = [t['id'] for t in new if P(t)[0] == P(t)[1]]
    res['new_off45'] = [dict(net=t['net'], l=t['l'], x=t['x1'] * MM, y=t['y1'] * MM, len=round(tlen(t) * MM, 3)) for t in new if not on45(t)]
    res['new_below_min_width'] = [t['id'] for t in new if t['w'] < MINW]
    seen = collections.Counter((t['net'], t['l'], frozenset(P(t))) for t in g1['tracks'])
    seen0 = collections.Counter((t['net'], t['l'], frozenset(P(t))) for t in g0['tracks'])
    res['duplicates'] = [sum(1 for k, n in seen0.items() if n > 1), sum(1 for k, n in seen.items() if n > 1)]
    nets0 = {t['net'] for t in g0['tracks']}; res['unknown_nets'] = sorted({t['net'] for t in new} - nets0 - set(g0['netclass']))
    # connectivity
    c0, o0 = connectivity(g0); c1, o1 = connectivity(g1)
    def split(n):                                   # a group of pads/vias that was joined before must still be inside one group
        after = c1.get(n, frozenset())
        return any(not any(grp <= h for h in after) for grp in c0.get(n, frozenset()))
    res['connectivity_changed'] = sorted(n for n in set(c0) | set(c1) if split(n))
    res['connectivity_merged'] = sorted(n for n in set(c0) | set(c1) if not split(n) and c0.get(n) != c1.get(n))
    res['orphan_groups'] = {n: [o0.get(n, 0), o1.get(n, 0)] for n in set(o0) | set(o1) if o1.get(n, 0) > o0.get(n, 0)}
    # clearance
    res['clearance'] = clearance(g0, g1, spec)
    # excursion
    ex = excursion(g0, g1); res['excursion_max_mm'] = round(max([v[0] for v in ex.values()] + [0]), 3)
    res['excursion_over_limit'] = [] if maxexc is None else [dict(net=k[0], l=k[1], mm=round(v[0], 3), at=v[1]) for k, v in ex.items() if v[0] > maxexc]
    # audit
    a0 = collections.Counter(d['kind'] for d in A.audit(g0)); a1 = collections.Counter(d['kind'] for d in A.audit(g1))
    res['audit'] = {k: [a0.get(k, 0), a1.get(k, 0)] for k in sorted(set(a0) | set(a1))}
    res['audit_worse'] = [k for k in res['audit'] if res['audit'][k][1] > res['audit'][k][0]]
    hard = ['new_zero_length', 'new_below_min_width', 'unknown_nets', 'connectivity_changed', 'orphan_groups', 'clearance', 'excursion_over_limit']
    res['ok'] = not any(res[k] for k in hard) and res['duplicates'][1] <= res['duplicates'][0]
    return res, g1
