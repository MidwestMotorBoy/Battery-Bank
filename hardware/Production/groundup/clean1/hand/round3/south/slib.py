import sys, json, math, collections, subprocess, os
S = '/tmp/clean1'
sys.path.insert(0, S + '/tools')
from fixlib import Fix
import geolib as G
from shapely.geometry import Point, Polygon
REGION = (79, 103, 121.5, 137.5)
RF = ('/MCU/RFIO', '/MCU/ANT_IN', 'Net-(C313-Pad2)')
HERE = S + '/agents/south'
LN = ['F', 'In1', 'In2', 'In3', 'In4', 'B']

def mk(): return Fix(S + '/r3/geo.json', region=REGION)

def own(t):
    x = (t['x1'] + t['x2']) / 2e6; y = (t['y1'] + t['y2']) / 2e6
    return REGION[0] <= x < REGION[2] and REGION[1] <= y < REGION[3]

def merged_spec(f, verbose=True):
    """spec of f plus: merge collinear same net/layer/width pieces meeting at a degree-2 node with no via/pad there."""
    g = f.g
    key = lambda t: (t['net'], t['l'], t['w'], t['x1'], t['y1'], t['x2'], t['y2'])
    cur = [dict(t) for t in g['tracks'] if t['id'] not in f.dele] + [dict(a, id=None) for a in f.adds]
    padpoly = collections.defaultdict(list); vias = collections.defaultdict(list)
    for p in g['pads']:
        for l, pts in p['L'].items():
            if len(pts) >= 3: padpoly[(p['net'], l)].append(Polygon(pts))
    for v in g['vias']:
        a, b = LN.index(v['top']), LN.index(v['bot'])
        for l in LN[a:b + 1]: vias[(v['net'], l)].append(v)
    def blocked(net, l, pt, oa, ob):
        # a node at a via / pad centre stays; a node elsewhere inside the via / pad may go if the merged piece still ends inside that same via / pad
        for v in vias.get((net, l), []):
            d = math.hypot(v['x'] - pt[0], v['y'] - pt[1])
            if d <= v['d'] / 2:
                if d <= 30000: return True
                if not any(math.hypot(v['x'] - o[0], v['y'] - o[1]) <= 30000 for o in (oa, ob)): return True
        P = Point(pt)
        for poly in padpoly.get((net, l), []):
            if poly.contains(P) or poly.distance(P) < 1000:
                c = poly.centroid
                if abs(c.x - pt[0]) <= 30000 and abs(c.y - pt[1]) <= 30000: return True
                if not any(poly.contains(Point(o)) for o in (oa, ob)): return True
        return False
    n = 0
    while True:
        nodes = collections.defaultdict(list)
        for i, t in enumerate(cur):
            if t is None: continue
            nodes[(t['net'], t['l'], t['x1'], t['y1'])].append(i); nodes[(t['net'], t['l'], t['x2'], t['y2'])].append(i)
        did = False
        for (net, l, x, y), ii in nodes.items():
            if len(ii) != 2 or ii[0] == ii[1] or net in RF: continue
            a, b = cur[ii[0]], cur[ii[1]]
            if a is None or b is None or a['w'] != b['w']: continue
            if not (own(a) and own(b)): continue
            oa = (a['x2'], a['y2']) if (a['x1'], a['y1']) == (x, y) else (a['x1'], a['y1'])
            ob = (b['x2'], b['y2']) if (b['x1'], b['y1']) == (x, y) else (b['x1'], b['y1'])
            ux, uy = oa[0] - x, oa[1] - y; vx, vy = ob[0] - x, ob[1] - y
            if ux * vy - uy * vx != 0 or ux * vx + uy * vy >= 0: continue      # not collinear or folded back
            if blocked(net, l, (x, y), oa, ob): continue
            cur[ii[0]] = dict(net=net, l=l, w=a['w'], x1=oa[0], y1=oa[1], x2=ob[0], y2=ob[1], id=None); cur[ii[1]] = None
            n += 1; did = True
            if verbose: print('  merge %-30s %-3s w %.2f at (%.4f, %.4f)' % (net[-30:], l, a['w'] / 1e6, x / 1e6, y / 1e6))
            break
        if not did: break
    cur = [t for t in cur if t is not None]
    keep = {t['id'] for t in cur if t['id']}
    dele = [t['id'] for t in g['tracks'] if t['id'] not in keep]
    add = [{k: t[k] for k in ('net', 'l', 'w', 'x1', 'y1', 'x2', 'y2')} for t in cur if t['id'] is None]
    # cancel identical delete+add
    byk = {}
    for t in g['tracks']:
        if t['id'] in dele:
            byk.setdefault(key(t), []).append(t['id']); byk.setdefault((t['net'], t['l'], t['w'], t['x2'], t['y2'], t['x1'], t['y1']), []).append(t['id'])
    add2 = []
    for a in add:
        k = key(a)
        if byk.get(k):
            i = byk[k].pop(); dele.remove(i)
            for kk in list(byk):
                if i in byk[kk]: byk[kk].remove(i)
        else: add2.append(a)
    print('merged %d collinear nodes; spec: del %d add %d' % (n, len(dele), len(add2)))
    return {'del': dele, 'add': add2}

def finish(f, name='spec.json', maxexc=0.8, verbose=False):
    spec = merged_spec(f, verbose); fn = HERE + '/' + name; json.dump(spec, open(fn, 'w'))
    r = subprocess.run([sys.executable, S + '/tools/chk.py', f.fn, fn, '--maxexc=%s' % maxexc, '--out=' + HERE + '/after_geo.json', '--json=' + HERE + '/res.json'], capture_output=True, text=True)
    print(r.stdout[-3500:], r.stderr[-2000:]); open(HERE + '/chk.txt', 'w').write(r.stdout)
    return r.returncode == 0

def chamfer(f, ia, ib, leg=0.3):
    """replace the corner between tracks ia and ib by a 45 degree piece; leg in mm along each track."""
    a = f.by[f._id(ia)]; b = f.by[f._id(ib)]
    pa = set(G.P(a)); pb = set(G.P(b)); c = (pa & pb)
    assert len(c) == 1, 'no single common point'
    c = c.pop(); oa = (pa - {c}).pop(); ob = (pb - {c}).pop(); n = int(round(leg * 1e6))
    def back(o):
        d = max(abs(o[0] - c[0]), abs(o[1] - c[1])); assert d > n, 'leg too long'
        return (c[0] + (o[0] - c[0]) // d * n, c[1] + (o[1] - c[1]) // d * n)
    qa = back(oa); qb = back(ob)
    f.replace([a['id']], [oa, qa]); f.replace([b['id']], [qa, qb, ob] if False else [qa, qb]) ; f.add(b['net'], b['l'], b['w'], [qb, ob])
    # note: the diagonal takes the width of b
