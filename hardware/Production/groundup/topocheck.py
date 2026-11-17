#!/usr/bin/env python3
"""topocheck.py before_geo.json after_geo.json [out.json] [--protect=file.json]     (plain python 3 with shapely)
Proof that a straightening pass kept the board's structure. Both files are dumps from dumpgeo.py.

  1. pads, vias, zones (outline, net, layers, priority, clearance, minimum width), rule areas and the board outline
     are identical
  2. tracks: which ids went, how many came, which nets changed; no protected net among them
  3. every new segment is on the 45 degree grid; count of off-grid segments before and after
  4. per net, the reduced track graph is identical: fixed points (track ends, T-junctions, vias, width changes)
     and between them one edge per run with its layer and width
  5. per net, the same pads and vias are joined (geometric union-find over tracks, pads and vias; nets with a pour
     are skipped here, their tracks are not touched)
  6. set of track widths per net and layer unchanged
Exit code 1 if any of it fails."""
import json, sys, collections, math
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree
a = [x for x in sys.argv[1:] if not x.startswith('--')]; O = dict((x[2:].split('=', 1) + ['1'])[:2] for x in sys.argv[1:] if x.startswith('--'))
A, B = json.load(open(a[0])), json.load(open(a[1])); MM = 1e-6
res = collections.OrderedDict(); fail = []
def same(name, x, y):
    ok = x == y; res[name + ' identical'] = ok
    if not ok: fail.append(name)
    return ok
# 1
same('pads (%d)' % len(A['pads']), A['pads'], B['pads'])
vk = lambda d: sorted((v['id'], v['x'], v['y'], v['d'], v['drill'], v['net'], v['top'], v['bot'], v['rul']) for v in d['vias'])
same('vias (%d): id, position, size, drill, net, layers' % len(A['vias']), vk(A), vk(B))
res['vias: layers with a pad identical'] = sorted((v['id'], v['flash']) for v in A['vias']) == sorted((v['id'], v['flash']) for v in B['vias'])
same('zones (%d): outline, net, layers, priority, clearance, min width' % len(A['zones']), A['zones'], B['zones'])
same('rule areas (%d)' % len(A['keepouts']), A['keepouts'], B['keepouts'])
same('board outline', A['edge'], B['edge'])
same('net classes', A['netclass'], B['netclass'])
# 2
ta = {t['id']: t for t in A['tracks']}; tb = {t['id']: t for t in B['tracks']}
gone = [ta[i] for i in ta if i not in tb]; new = [tb[i] for i in tb if i not in ta]
moved = [i for i in ta if i in tb and ta[i] != tb[i]]
res['tracks before / after'] = [len(ta), len(tb)]; res['tracks removed / added / altered in place'] = [len(gone), len(new), len(moved)]
if moved: fail.append('tracks altered in place')
chg = sorted({t['net'] for t in gone + new}); res['nets changed'] = len(chg)
if 'protect' in O:
    prot = set(json.load(open(O['protect'])))
    bad = [n for n in chg if n in prot]; res['protected nets changed'] = bad
    if bad: fail.append('protected net changed')
ngone = collections.Counter(t['net'] for t in gone); nnew = collections.Counter(t['net'] for t in new)
# 3
def off(t):
    dx, dy = abs(t['x2'] - t['x1']), abs(t['y2'] - t['y1'])
    return not (dx == 0 or dy == 0 or dx == dy)
oldgeo = {(t['net'], t['l'], t['w'], frozenset(((t['x1'], t['y1']), (t['x2'], t['y2'])))) for t in gone}
offnew = [t for t in new if off(t)]
res['off-grid segments written again unchanged (part of a run that changed elsewhere)'] = sum(1 for t in offnew if (t['net'], t['l'], t['w'], frozenset(((t['x1'], t['y1']), (t['x2'], t['y2'])))) in oldgeo)
res['new segments off the 45 degree grid'] = sum(1 for t in offnew if (t['net'], t['l'], t['w'], frozenset(((t['x1'], t['y1']), (t['x2'], t['y2'])))) not in oldgeo)
if res['new segments off the 45 degree grid']: fail.append('off-grid segment added')
res['segments off the 45 degree grid, before / after (exact, any length)'] = [sum(1 for t in A['tracks'] if off(t)), sum(1 for t in B['tracks'] if off(t))]
res['zero-length tracks, before / after'] = [sum(1 for t in d['tracks'] if (t['x1'], t['y1']) == (t['x2'], t['y2'])) for d in (A, B)]
# 4
def graph(d, net):
    vias = {(v['x'], v['y']) for v in d['vias'] if v['net'] == net}; E = collections.Counter(); ndup = 0
    byL = collections.defaultdict(list)
    for t in d['tracks']:
        if t['net'] == net and (t['x1'], t['y1']) != (t['x2'], t['y2']): byL[t['l']].append(((t['x1'], t['y1']), (t['x2'], t['y2']), t['w']))
    for L, segs in byL.items():
        ch = True
        while ch:                                             # an end on the middle of another track: split there
            ch = False; pts = {p for s in segs for p in s[:2]}
            for k, (p, q, w) in enumerate(segs):
                u = (q[0] - p[0], q[1] - p[1])
                for e in pts:
                    if e == p or e == q: continue
                    v = (e[0] - p[0], e[1] - p[1])
                    if u[0] * v[1] - u[1] * v[0] == 0 and 0 < u[0] * v[0] + u[1] * v[1] < u[0] * u[0] + u[1] * u[1]:
                        segs[k] = (p, e, w); segs.append((e, q, w)); ch = True; break
                if ch: break
            if not ch:                                        # two tracks crossing without a common point: split both
                for k, (p, q, w) in enumerate(segs):
                    for k2 in range(k + 1, len(segs)):
                        c, d, w2 = segs[k2]; r = (q[0] - p[0], q[1] - p[1]); s_ = (d[0] - c[0], d[1] - c[1]); den = r[0] * s_[1] - r[1] * s_[0]
                        if den == 0: continue
                        ww = (c[0] - p[0], c[1] - p[1]); tn = ww[0] * s_[1] - ww[1] * s_[0]; un = ww[0] * r[1] - ww[1] * r[0]
                        if den < 0: den, tn, un = -den, -tn, -un
                        if 0 < tn < den and 0 < un < den and (tn * r[0]) % den == 0 and (tn * r[1]) % den == 0:
                            X = (p[0] + tn * r[0] // den, p[1] + tn * r[1] // den)
                            segs[k] = (p, X, w); segs.append((X, q, w)); segs[k2] = (c, X, w2); segs.append((X, d, w2)); ch = True; break
                    if ch: break
        seen = {}
        for p, q, w in segs:
            k = frozenset((p, q)); seen[k] = max(seen.get(k, 0), w)
        ndup += len(segs) - len(seen); segs = [(tuple(k)[0], tuple(k)[1], w) for k, w in seen.items()]
        adj = collections.defaultdict(list)
        for k, (p, q, w) in enumerate(segs): adj[p].append(k); adj[q].append(k)
        node = {p for p, ks in adj.items() if len(ks) != 2 or segs[ks[0]][2] != segs[ks[1]][2] or p in vias}
        used = set()
        def walk(k, st):
            cur = st
            while True:
                used.add(k); p, q, w = segs[k]; cur = q if p == cur else p
                if cur in node: return cur
                k2 = [x for x in adj[cur] if x != k]
                if not k2 or k2[0] in used: return cur
                k = k2[0]
        for p in sorted(node):
            for k in adj[p]:
                if k not in used: E[(L, segs[k][2], frozenset((p, walk(k, p))))] += 1
        for k in range(len(segs)):
            if k not in used: walk(k, segs[k][0]); E[(L, segs[k][2], 'loop')] += 1
    return E, ndup
nets = sorted({t['net'] for t in A['tracks']} | {t['net'] for t in B['tracks']})
gdiff = []; dups = [0, 0]
for n in nets:
    ga, da = graph(A, n); gb, db = graph(B, n); dups[0] += da; dups[1] += db
    if ga != gb: gdiff.append(n)
res['nets with tracks'] = len(nets); res['nets whose reduced track graph differs'] = gdiff
res['duplicate track pieces (same two ends), before / after'] = dups
if gdiff: fail.append('track graph differs')
# 5
zoned = {z['net'] for z in A['zones']}
def groups(d, net):
    items = []                                                # (kind, name, layer or None, geom, radius)
    for p in d['pads']:
        if p['net'] == net:
            for L, poly in p['L'].items():
                if len(poly) >= 3: items.append(('pad', p['ref'] + '.' + p['n'], L, Polygon([(x * MM, y * MM) for x, y in poly]), 0.0))
    for v in d['vias']:
        if v['net'] == net: items.append(('via', '%d,%d' % (v['x'], v['y']), None, Point(v['x'] * MM, v['y'] * MM), v['d'] / 2 * MM))
    for t in d['tracks']:
        if t['net'] == net and (t['x1'], t['y1']) != (t['x2'], t['y2']): items.append(('trk', '', t['l'], LineString([(t['x1'] * MM, t['y1'] * MM), (t['x2'] * MM, t['y2'] * MM)]), t['w'] / 2 * MM))
    par = list(range(len(items)))
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    name = {}
    for k, it in enumerate(items):
        if it[0] != 'trk':
            if it[1] in name: par[find(k)] = find(name[it[1]])      # one pad on several layers
            else: name[it[1]] = k
    tree = STRtree([it[3].buffer(it[4] + 1e-4) if it[4] else it[3] for it in items])
    for k, it in enumerate(items):
        if it[0] != 'trk': continue
        for j in tree.query(it[3].buffer(it[4] + 0.01)):
            o = items[j]
            if j == k or (o[2] is not None and o[2] != it[2]): continue
            if it[3].distance(o[3]) < it[4] + o[4] - 1e-7: par[find(k)] = find(j)
    g = collections.defaultdict(set)
    for k, it in enumerate(items):
        if it[0] != 'trk': g[find(k)].add(it[0] + ' ' + it[1])
    return sorted(sorted(x) for x in g.values())
cdiff = []; split = []
for n in nets:
    if n in zoned or not n: continue
    ga, gb = groups(A, n), groups(B, n)
    if ga != gb: cdiff.append(n)
    if len(gb) > 1: split.append('%s (%d before, %d after)' % (n, len(ga), len(gb)))
res['nets checked for joined pads and vias (no pour)'] = len([n for n in nets if n and n not in zoned])
res['nets whose joined pads / vias differ'] = cdiff; res['nets in more than one piece by tracks alone (joined through a pad-to-pad overlap or the like)'] = split
if cdiff: fail.append('connectivity differs')
# 6
wa = collections.defaultdict(set); wb = collections.defaultdict(set)
for t in A['tracks']: wa[(t['net'], t['l'])].add(t['w'])
for t in B['tracks']: wb[(t['net'], t['l'])].add(t['w'])
wd = sorted(str(k) for k in set(wa) | set(wb) if wa.get(k) != wb.get(k)); res['net/layer pairs whose set of widths differs'] = wd
if wd: fail.append('widths differ')
res['layers used per net identical'] = {n: sorted({t['l'] for t in A['tracks'] if t['net'] == n}) for n in nets} == {n: sorted({t['l'] for t in B['tracks'] if t['net'] == n}) for n in nets}
if not res['layers used per net identical']: fail.append('layers differ')
res['per net'] = {n: dict(removed=ngone[n], added=nnew[n]) for n in chg}
res['FAILED'] = fail
for k, v in res.items():
    if k != 'per net': print('%-78s %s' % (k, v))
if len(a) > 2: json.dump(res, open(a[2], 'w'), indent=1)
sys.exit(1 if fail else 0)
