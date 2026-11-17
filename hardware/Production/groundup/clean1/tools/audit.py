#!/usr/bin/env python3
"""audit.py geo.json out.json [--quiet]
Junction / overlap / width audit of the tracks in a dumpgeo.py dump. Lists every defect with a position (mm).

Defect kinds
  width_step     two track pieces of different width meet end to end away from any pad or via (degree-2 node)
  width_tee      a branch of another width at a junction away from pads/vias (informational; only counted)
  end_off_pad    a track ends inside a pad of its net more than 0.03 mm off BOTH centre lines of the pad (x and y through the pad centre)
  end_off_via    a track ends inside a via of its net more than 0.03 mm from the via centre
  end_off_track  a track ends on the body of another track of its net but not on its centre line (joined only by copper overlap)
  hidden_jog     (not a fault, listed for information) a single bend whose copper lies inside the via or pad, with the next piece ending on the centre
  near_miss      two track ends of a net are closer than their copper but are not the same point
  dangling       a track end that touches nothing (stub)
  acute          two pieces meet at a node at less than 90 degrees (not counted: a 45 degree branch off a straight-through track)
  tee_unsplit    a track ends exactly on the centre line of another piece of its net that has no node there (the through piece should be split)
  collinear_ovl  two collinear pieces of a net lie on top of each other
  body_ovl       two pieces of a net run side by side with their copper overlapping (not collinear, not just meeting at a node)
  tiny           a piece shorter than 0.05 mm
  through_pad    a track passes over a pad/via of its net without a node at the centre (informational)
  cross          two tracks of a net cross without a node
  off45          a piece longer than 0.3 mm that is not at 0/45/90 degrees
"""
import json, sys, math, collections
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

MM = 1e-6
END_TOL = 30000          # nm: a track end this close to a via centre / a pad centre line counts as centred
def load(fn): return json.load(open(fn))

def audit(g):
    T = g['tracks']; out = []
    def add(kind, x, y, net, layer, **kw): out.append(dict(kind=kind, x=round(x * MM, 4), y=round(y * MM, 4), net=net, l=layer, **kw))
    # pads / vias by net+layer
    padpoly = collections.defaultdict(list); vias = collections.defaultdict(list)
    for p in g['pads']:
        for l, pts in p['L'].items():
            if len(pts) >= 3: padpoly[(p['net'], l)].append((Polygon(pts), p))
    LN = ['F', 'In1', 'In2', 'In3', 'In4', 'B']
    for v in g['vias']:
        a, b = LN.index(v['top']), LN.index(v['bot'])
        for l in LN[a:b + 1]: vias[(v['net'], l)].append(v)
    groups = collections.defaultdict(list)
    for t in T: groups[(t['net'], t['l'])].append(t)
    for (net, l), ts in groups.items():
        nodes = collections.defaultdict(list)          # point -> [(track, other end)]
        for t in ts:
            a = (t['x1'], t['y1']); b = (t['x2'], t['y2'])
            nodes[a].append((t, b)); nodes[b].append((t, a))
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 50000: add('tiny', (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, net, l, len=round(L * MM, 4), id=t['id'])
            dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
            if L > 300000 and not (dx < 1000 or dy < 1000 or abs(dx - dy) < 1000):
                add('off45', (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, net, l, len=round(L * MM, 3), id=t['id'])
        pp = padpoly.get((net, l), []); vv = vias.get((net, l), [])
        lines = [LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]) if (t['x1'], t['y1']) != (t['x2'], t['y2']) else Point(t['x1'], t['y1']).buffer(1) for t in ts]
        tree = STRtree(lines)
        def at_pad(pt):
            P = Point(pt)
            for poly, p in pp:
                if poly.covers(P): return p
            return None
        def at_via(pt):
            for v in vv:
                if math.hypot(v['x'] - pt[0], v['y'] - pt[1]) <= v['d'] / 2: return v
            return None
        for pt, lst in nodes.items():
            p = at_pad(pt); v = at_via(pt)
            ws = sorted(set(t['w'] for t, _ in lst))
            # other tracks whose body covers this point without having a node here
            P = Point(pt); mids = []
            for i in tree.query(P.buffer(500000)):
                t2 = ts[i]
                if (t2['x1'], t2['y1']) == pt or (t2['x2'], t2['y2']) == pt: continue
                d = lines[i].distance(P)
                if d <= t2['w'] / 2: mids.append((t2, d))
            # a bend that the via or pad copper hides: two pieces, the bend's copper inside the via/pad, one piece going on to the centre
            def hidden_bend(cx, cy, inside):
                if len(lst) != 2 or mids: return False
                if not inside(max(t['w'] for t, _ in lst) / 2): return False
                return any(math.hypot(o[0] - cx, o[1] - cy) <= END_TOL for _, o in lst)
            pad_ok = False
            if p is not None:
                dx, dy = abs(p['x'] - pt[0]), abs(p['y'] - pt[1]); pad_ok = dx <= END_TOL or dy <= END_TOL
            if v is not None and not (p is not None and pad_ok and v is not None and math.hypot(p['x'] - pt[0], p['y'] - pt[1]) <= END_TOL):
                d = math.hypot(v['x'] - pt[0], v['y'] - pt[1])
                if d > END_TOL:
                    if hidden_bend(v['x'], v['y'], lambda r: d + r <= v['d'] / 2 + 1000): add('hidden_jog', pt[0], pt[1], net, l, off=round(d * MM, 4))
                    else: add('end_off_via', pt[0], pt[1], net, l, off=round(d * MM, 4), ids=[t['id'] for t, _ in lst])
            elif p is not None and not pad_ok:
                poly = [q for q, pp_ in pp if pp_ is p][0]
                if hidden_bend(p['x'], p['y'], lambda r: poly.contains(Point(pt).buffer(r - 1000))): add('hidden_jog', pt[0], pt[1], net, l, off=round(math.hypot(dx, dy) * MM, 4))
                else: add('end_off_pad', pt[0], pt[1], net, l, off=round(math.hypot(dx, dy) * MM, 4), pad=p['ref'] + '.' + p['n'], ids=[t['id'] for t, _ in lst])
            if len(ws) > 1 and p is None and v is None:
                add('width_step' if len(lst) == 2 and not mids else 'width_tee', pt[0], pt[1], net, l, w=[w * MM for w in ws], ids=[t['id'] for t, _ in lst])
            # ends on a track body
            if mids and p is None and v is None:
                on = [m for m in mids if m[1] <= 1000]
                if on:
                    add('tee_unsplit', pt[0], pt[1], net, l, ids=[t['id'] for t, _ in lst], other=[m[0]['id'] for m in on])
                else:
                    add('end_off_track', pt[0], pt[1], net, l, off=round(min(m[1] for m in mids) * MM, 4), ids=[t['id'] for t, _ in lst], other=[m[0]['id'] for m in mids])
            if len(lst) == 1 and not mids and p is None and v is None:
                add('dangling', pt[0], pt[1], net, l, id=lst[0][0]['id'], len=round(math.hypot(lst[0][1][0] - pt[0], lst[0][1][1] - pt[1]) * MM, 3))
            # acute angles between pieces at this node (a 45 degree branch off a straight-through track is a proper T, not a fault)
            def straight_partner(k):
                a = lst[k][1]; ax, ay = a[0] - pt[0], a[1] - pt[1]
                for m in range(len(lst)):
                    if m == k: continue
                    b = lst[m][1]; bx, by = b[0] - pt[0], b[1] - pt[1]
                    if abs(ax * by - ay * bx) <= 2 * max(abs(ax), abs(ay), abs(bx), abs(by)) and ax * bx + ay * by < 0: return True
                return False
            for i in range(len(lst)):
                for j in range(i + 1, len(lst)):
                    a = lst[i][1]; b = lst[j][1]
                    ax, ay = a[0] - pt[0], a[1] - pt[1]; bx, by = b[0] - pt[0], b[1] - pt[1]
                    la, lb = math.hypot(ax, ay), math.hypot(bx, by)
                    if la < 1 or lb < 1: continue
                    c = (ax * bx + ay * by) / la / lb; ang = math.degrees(math.acos(max(-1, min(1, c))))
                    if ang < 1:
                        add('collinear_ovl', pt[0], pt[1], net, l, ids=[lst[i][0]['id'], lst[j][0]['id']], len=round(min(la, lb) * MM, 3))
                    elif ang < 89:
                        if len(lst) >= 3 and abs(ang - 45) < 0.5 and (straight_partner(i) or straight_partner(j)): continue
                        add('acute', pt[0], pt[1], net, l, ang=round(ang, 1), ids=[lst[i][0]['id'], lst[j][0]['id']], inpad=bool(p or v))
        # near-miss node pairs
        pts = list(nodes.keys())
        ptree = STRtree([Point(q) for q in pts])
        for i, q in enumerate(pts):
            wi = max(t['w'] for t, _ in nodes[q])
            for j in ptree.query(Point(q).buffer(wi)):
                if j <= i: continue
                r = pts[j]; d = math.hypot(q[0] - r[0], q[1] - r[1]); wj = max(t['w'] for t, _ in nodes[r])
                if d < (wi + wj) / 2 * 0.6:
                    # joined by a piece between them? then it is just a short piece
                    joined = any(o == r for _, o in nodes[q])
                    if not joined: add('near_miss', (q[0] + r[0]) / 2, (q[1] + r[1]) / 2, net, l, d=round(d * MM, 4), inpad=bool(at_pad(q) or at_via(q)))
        # pairwise body relations
        for i, t in enumerate(ts):
            a = (t['x1'], t['y1']); b = (t['x2'], t['y2'])
            La = lines[i].length
            if La < 1: continue
            for j in tree.query(lines[i].buffer(t['w'])):
                if j <= i: continue
                u = ts[j]; c = (u['x1'], u['y1']); d = (u['x2'], u['y2'])
                if lines[j].length < 1: continue
                share = len({a, b} & {c, d})
                # crossing
                if share == 0 and lines[i].crosses(lines[j]):
                    X = lines[i].intersection(lines[j])
                    if X.geom_type == 'Point' and min(X.distance(Point(q)) for q in (a, b, c, d)) > 1000:
                        add('cross', X.x, X.y, net, l, ids=[t['id'], u['id']])
                # overlap of copper along a length: part of j within (wi+wj)/2*0.5 of i
                near = lines[j].intersection(lines[i].buffer((t['w'] + u['w']) / 4, cap_style=2))
                ln = near.length if not near.is_empty else 0
                if ln > 200000:
                    # direction
                    ux, uy = b[0] - a[0], b[1] - a[1]; vx, vy = d[0] - c[0], d[1] - c[1]
                    cr = abs(ux * vy - uy * vx) / La / lines[j].length
                    cx, cy = near.centroid.x, near.centroid.y
                    if cr < 0.02:
                        if lines[j].distance(lines[i]) < 1000 and share == 0 or (share and ln > 1000 and lines[i].intersection(lines[j]).length > 1000):
                            add('collinear_ovl', cx, cy, net, l, ids=[t['id'], u['id']], len=round(ln * MM, 3))
                        elif share == 0:
                            add('body_ovl', cx, cy, net, l, ids=[t['id'], u['id']], len=round(ln * MM, 3), par=True)
                    elif share == 0 or ln > max(t['w'], u['w']) * 1.5:
                        add('body_ovl', cx, cy, net, l, ids=[t['id'], u['id']], len=round(ln * MM, 3), par=False, share=share)
        # through pad/via without node
        for i, t in enumerate(ts):
            for v in vv:
                P = Point(v['x'], v['y'])
                if lines[i].distance(P) < v['d'] / 2 and (v['x'], v['y']) not in ((t['x1'], t['y1']), (t['x2'], t['y2'])):
                    e = min(math.hypot(v['x'] - t['x1'], v['y'] - t['y1']), math.hypot(v['x'] - t['x2'], v['y'] - t['y2']))
                    if e > v['d'] / 2: add('through_pad', v['x'], v['y'], net, l, what='via', id=t['id'])
    return out

if __name__ == '__main__':
    g = load(sys.argv[1]); o = audit(g)
    json.dump(o, open(sys.argv[2], 'w'))
    c = collections.Counter(d['kind'] for d in o)
    for k, n in sorted(c.items(), key=lambda kv: -kv[1]): print('%-14s %5d' % (k, n))
    if '--quiet' not in sys.argv:
        cls = g['netclass']
        cc = collections.Counter((d['kind'], cls.get(d['net'], '?')) for d in o)
        for (k, c2), n in sorted(cc.items()): print('   %-14s %-12s %4d' % (k, c2, n))
