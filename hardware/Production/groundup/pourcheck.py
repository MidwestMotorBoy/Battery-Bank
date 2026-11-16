#!/usr/bin/env python3
"""pourcheck.py before_geo.json after_geo.json [out.json]      (plain python 3 with shapely)
What a track edit did to the pours, per pour net and layer (dumps from dumpgeo.py):
  area, number of separate pieces, and which vias / pads of the net sit on a common piece of copper once every neck
  narrower than 0.2 / 0.4 mm is taken away (the fill shrunk by 0.1 / 0.2 mm). A pair that shared a piece before and
  does not after is a neck that got thinner or was cut; the list gives where. It is a screen, not a proof: the
  resistance and loop solvers in compare/ are the measurement."""
import json, sys, collections, math
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
A, B = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])); MM = 1e-6
def fills(d):
    f = collections.defaultdict(list)
    for z in d['fills']:
        for o, hs in z['polys']:
            if len(o) >= 3: f[(z['net'], z['l'])].append(Polygon([(x * MM, y * MM) for x, y in o], [[(x * MM, y * MM) for x, y in h] for h in hs if len(h) >= 3]))
    return {k: unary_union([p if p.is_valid else p.buffer(0) for p in v]) for k, v in f.items()}
def anchors(d, net, L):
    a = [('via %.3f,%.3f' % (v['x'] * MM, v['y'] * MM), Point(v['x'] * MM, v['y'] * MM), v['d'] / 2 * MM) for v in d['vias'] if v['net'] == net and L in v['flash']]
    for p in d['pads']:
        if p['net'] == net and L in p['L'] and len(p['L'][L]) >= 3:
            pg = Polygon([(x * MM, y * MM) for x, y in p['L'][L]]); a.append(('pad %s.%s' % (p['ref'], p['n']), pg.centroid, math.sqrt(pg.area / math.pi)))
    return a
def parts(g): return list(g.geoms) if hasattr(g, 'geoms') else ([g] if not g.is_empty else [])
def label(geom, anc, r):
    ps = parts(geom.buffer(-r)) if r else parts(geom)
    if not ps: return {}
    tree = STRtree(ps); lab = {}
    for name, pt, rad in anc:
        best = None
        for k in tree.query(pt.buffer(rad + r + 0.05)):
            dd = ps[k].distance(pt)
            if dd < rad + r + 0.02 and (best is None or dd < best[0]): best = (dd, k)
        if best: lab[name] = best[1]
    return lab
FA, FB = fills(A), fills(B); out = []; bad = 0
print('%-28s %-4s %18s %12s   lost links at neck 0 / 0.2 / 0.4 mm' % ('pour net', 'lay', 'area mm2 (delta)', 'pieces'))
for k in sorted(set(FA) | set(FB)):
    ga, gb = FA.get(k), FB.get(k)
    if ga is None or gb is None: print(k, 'missing on one board'); bad += 1; continue
    anc = anchors(A, *k); row = dict(net=k[0], layer=k[1], area0=ga.area, area1=gb.area, pieces0=len(parts(ga)), pieces1=len(parts(gb)), lost={})
    for r in (0.0, 0.1, 0.2):
        la, lb = label(ga, anc, r), label(gb, anc, r); lost = []
        grp = collections.defaultdict(list)
        for n, c in la.items(): grp[c].append(n)
        for c, names in grp.items():
            sub = collections.Counter(lb.get(n, -1) for n in names)
            if len(sub) > 1 or -1 in sub:
                main = sub.most_common(1)[0][0]; lost += [n for n in names if lb.get(n, -1) != main or lb.get(n, -1) == -1]
        row['lost'][str(2 * r)] = lost
    n = [len(row['lost'][x]) for x in ('0.0', '0.2', '0.4')]; bad += n[0]
    if abs(row['area1'] - row['area0']) > 1e-4 or row['pieces0'] != row['pieces1'] or any(n):
        print('%-28s %-4s %9.2f (%+6.2f) %5d -> %-4d   %d / %d / %d  %s' % (k[0][-28:], k[1], row['area1'], row['area1'] - row['area0'], row['pieces0'], row['pieces1'], n[0], n[1], n[2], '; '.join((row['lost']['0.4'] or row['lost']['0.2'])[:4])))
    out.append(row)
print('pours unchanged:', sum(1 for r in out if abs(r['area1'] - r['area0']) <= 1e-4), 'of', len(out))
if len(sys.argv) > 3: json.dump(out, open(sys.argv[3], 'w'), indent=1)
