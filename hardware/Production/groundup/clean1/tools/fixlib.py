#!/usr/bin/env python3
"""fixlib.py: small helper for hand-written track fixes against a dumpgeo.py dump. Coordinates in mm for you, integer nm inside.

    import sys; sys.path.insert(0, SCRATCH + '/tools'); from fixlib import Fix
    f = Fix(SCRATCH + '/r2/geo.json', region=(79, 69, 100, 86))        # x0, y0, x1, y1 in mm: tracks you own
    f.near(97.9, 122.5, 'F', r=0.5)           -> prints the tracks within r mm: short id, net, width, both ends (mm), length
    f.net('/USB Port 2/CC1', 'F')             -> prints every track of a net on a layer, in chain order where possible
    v = f.via(97.92, 122.3)                   -> exact (x, y) in nm of the nearest via centre (also prints net, size)
    p = f.pad('U101.9')                       -> exact (x, y) in nm of a pad centre; f.padbox('U101.9', 'F') -> its outline box in mm
    q = f.pt(98.3, 124.0)                     -> the nearest existing track END point (nm) within 0.1 mm, so joins stay exact
    f.replace(['3f2a', '9c1e'], [p, (97.9, 122.6), v])      # delete these tracks (ids or unique id prefixes) and draw one
                                                             # polyline through the points with the net, layer and width of
                                                             # the first deleted track (override: net=, l=, w= in mm)
    f.delete(['ab12'])                        # only for copper that is truly redundant
    f.add(net, 'F', 0.2, [a, b, c])           # a new polyline without deleting anything
    f.split('ab12', (x, y))                   # cut a track in two at a point on its centre line (makes a T node)
    f.L(a, b, first='straight')               -> [a, corner, b]: the two-piece 0/45/90 path from a to b ('straight' or 'diag' piece first)
    f.setw(['ab12'], 0.2)                     # same geometry, new width
    f.save('spec.json')                       -> writes the spec (against the dump you loaded) and returns it
    f.check('spec.json', maxexc=0.8)          -> runs chk.py, prints its output, returns True/False

Points may be given in mm as floats (rounded to the nearest nm) or as exact nm tuples of ints (what via(), pad(), pt() return).
A float is taken as mm, an int as nm. Every piece of a polyline must be exactly 0/45/90 degrees: replace()/add() raise if not,
so build corners with L() or compute them from exact points. Use pt()/via()/pad() for every point that must coincide
with something that exists.
"""
import json, math, os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geolib as G
MM = 1e-6

def _nm(p):
    return tuple(int(round(c * 1e6)) if isinstance(c, float) else int(c) for c in p)

class Fix:
    def __init__(s, geo_fn, region=None):
        s.fn = geo_fn; s.g = G.load(geo_fn); s.region = region
        s.by = {t['id']: t for t in s.g['tracks']}; s.dele = []; s.adds = []
    # ---- lookups
    def _id(s, i):
        if i in s.by: return i
        m = [k for k in s.by if k.startswith(i)]
        if len(m) != 1: raise ValueError('id prefix %r matches %d tracks' % (i, len(m)))
        return m[0]
    def _own(s, t):
        if s.region is None: return True
        x = (t['x1'] + t['x2']) / 2 * MM; y = (t['y1'] + t['y2']) / 2 * MM
        return s.region[0] <= x < s.region[2] and s.region[1] <= y < s.region[3]
    def _show(s, t):
        print('  %s  %-28s %-3s w %.3f  (%.4f, %.4f) -> (%.4f, %.4f)  len %.3f%s%s' % (t['id'][:8], t['net'][-28:], t['l'], t['w'] * MM, t['x1'] * MM, t['y1'] * MM, t['x2'] * MM, t['y2'] * MM,
              G.tlen(t) * MM, '' if G.on45(t) else '  OFF-ANGLE', '' if s._own(t) else '  (not yours)'))
    def near(s, x, y, l=None, r=0.5):
        from shapely.geometry import Point
        P = Point(x * 1e6, y * 1e6); out = []
        for t in s.g['tracks']:
            if t['id'] in s.dele or (l and t['l'] != l): continue
            if G.tgeom(t).distance(P) <= r * 1e6 + t['w'] / 2: out.append(t)
        for t in sorted(out, key=lambda t: (t['l'], t['net'])): s._show(t)
        for v in s.g['vias']:
            if math.hypot(v['x'] * MM - x, v['y'] * MM - y) <= r + 0.3: print('  via %s  %-28s (%.4f, %.4f) d %.2f drill %.2f %s-%s' % (v['id'][:8], v['net'][-28:], v['x'] * MM, v['y'] * MM, v['d'] * MM, v['drill'] * MM, v['top'], v['bot']))
        for p in s.g['pads']:
            if math.hypot(p['x'] * MM - x, p['y'] * MM - y) <= r + 0.6 and (l is None or l in p['L']): print('  pad %s.%s  %-28s (%.4f, %.4f) layers %s' % (p['ref'], p['n'], p['net'][-28:], p['x'] * MM, p['y'] * MM, ','.join(p['L'])))
        return out
    def net(s, name, l=None):
        ts = [t for t in s.g['tracks'] if t['net'] == name and (l is None or t['l'] == l) and t['id'] not in s.dele]
        for t in sorted(ts, key=lambda t: (t['l'], min(t['y1'], t['y2']), min(t['x1'], t['x2']))): s._show(t)
        return ts
    def via(s, x, y, quiet=False):
        v = min(s.g['vias'], key=lambda v: math.hypot(v['x'] * MM - x, v['y'] * MM - y))
        if math.hypot(v['x'] * MM - x, v['y'] * MM - y) > 0.4: raise ValueError('no via within 0.4 mm of (%s, %s)' % (x, y))
        if not quiet: print('  via %s (%.4f, %.4f) d %.2f' % (v['net'], v['x'] * MM, v['y'] * MM, v['d'] * MM))
        return (v['x'], v['y'])
    def pad(s, name):
        ref, n = name.rsplit('.', 1)
        p = [p for p in s.g['pads'] if p['ref'] == ref and p['n'] == n]
        if not p: raise ValueError('no pad ' + name)
        return (p[0]['x'], p[0]['y'])
    def padbox(s, name, l='F'):
        ref, n = name.rsplit('.', 1)
        p = [p for p in s.g['pads'] if p['ref'] == ref and p['n'] == n and l in p['L']][0]; pts = p['L'][l]
        return (min(q[0] for q in pts) * MM, min(q[1] for q in pts) * MM, max(q[0] for q in pts) * MM, max(q[1] for q in pts) * MM)
    def pt(s, x, y, l=None, r=0.1):
        best = None
        for t in s.g['tracks'] + [dict(a, id='+') for a in s.adds]:
            if t.get('id') in s.dele or (l and t['l'] != l): continue
            for e in G.P(t):
                d = math.hypot(e[0] * MM - x, e[1] * MM - y)
                if d <= r and (best is None or d < best[0]): best = (d, e)
        if best is None: raise ValueError('no track end within %s mm of (%s, %s)' % (r, x, y))
        return best[1]
    @staticmethod
    def L(a, b, first='straight'):
        a = _nm(a); b = _nm(b); dx = b[0] - a[0]; dy = b[1] - a[1]; m = min(abs(dx), abs(dy))
        sx = (dx > 0) - (dx < 0); sy = (dy > 0) - (dy < 0)
        if m == 0 or abs(dx) == abs(dy): return [a, b]
        if first == 'diag': c = (a[0] + sx * m, a[1] + sy * m)
        else: c = (b[0] - sx * m, b[1] - sy * m)
        return [a, c, b]
    # ---- edits
    def _poly(s, net, l, w, pts):
        pts = [_nm(p) for p in pts]; w = int(round(w * 1e6)) if isinstance(w, float) else int(w)
        for a, b in zip(pts, pts[1:]):
            if a == b: continue
            dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
            if not (dx == 0 or dy == 0 or dx == dy): raise ValueError('piece (%.4f, %.4f) -> (%.4f, %.4f) is not 0/45/90 (dx %d nm, dy %d nm)' % (a[0] * MM, a[1] * MM, b[0] * MM, b[1] * MM, dx, dy))
            s.adds.append(dict(net=net, l=l, w=w, x1=a[0], y1=a[1], x2=b[0], y2=b[1]))
    def delete(s, ids):
        for i in ids:
            i = s._id(i); t = s.by[i]
            if not s._own(t): raise ValueError('track %s is outside your region' % i[:8])
            if i not in s.dele: s.dele.append(i)
    def replace(s, ids, pts, net=None, l=None, w=None):
        ids = [s._id(i) for i in ids]; t0 = s.by[ids[0]]
        s.delete(ids); s._poly(net or t0['net'], l or t0['l'], w if w is not None else t0['w'], pts)
    def add(s, net, l, w, pts): s._poly(net, l, w, pts)
    def split(s, i, p):
        i = s._id(i); t = s.by[i]; p = _nm(p); a, b = G.P(t)
        cr = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        if cr != 0: raise ValueError('point is not exactly on the centre line of %s (cross %d)' % (i[:8], cr))
        s.delete([i]); s._poly(t['net'], t['l'], t['w'], [a, p, b])
    def setw(s, ids, w):
        for i in ids:
            i = s._id(i); t = s.by[i]; s.delete([i]); s._poly(t['net'], t['l'], w, [G.P(t)[0], G.P(t)[1]])
    def save(s, fn):
        spec = {'del': list(s.dele), 'add': list(s.adds)}; json.dump(spec, open(fn, 'w')); return spec
    def check(s, fn, maxexc=0.8, out=None):
        s.save(fn); cmd = [sys.executable, os.path.join(HERE, 'chk.py'), s.fn, fn, '--maxexc=%s' % maxexc] + (['--out=' + out] if out else [])
        r = subprocess.run(cmd, capture_output=True, text=True); print(r.stdout[-3500:]); return r.returncode == 0
