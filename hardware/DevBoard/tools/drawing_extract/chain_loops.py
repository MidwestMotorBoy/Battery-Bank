"""Chain thick outline segments of a view into polylines/loops (mm, view origin given), print and save them."""
import sys, json, math

segs = json.load(open(sys.argv[1]))[sys.argv[2]]
S, cx, cy = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
TOL = 0.06 / S * 10      # mm


def mm(p):
    return (round((p[0] - cx) / S, 4), round((cy - p[1]) / S, 4))


edges = []
for s in segs:
    if s['w'] < 0.7:
        continue
    p = [mm(q) for q in s['p']]
    if s['k'] == 'c':
        a, b, c, e = p
        pts = []
        for i in range(9):
            t = i / 8
            pts.append(((1-t)**3*a[0] + 3*(1-t)**2*t*b[0] + 3*(1-t)*t*t*c[0] + t**3*e[0],
                        (1-t)**3*a[1] + 3*(1-t)**2*t*b[1] + 3*(1-t)*t*t*c[1] + t**3*e[1]))
        p = pts
    for a, b in zip(p, p[1:]):
        if math.dist(a, b) > 1e-4:
            edges.append([a, b])


def key(p):
    return (round(p[0] / TOL), round(p[1] / TOL))


# greedy chaining
unused = edges[:]
chains = []
while unused:
    ch = unused.pop()
    grown = True
    while grown:
        grown = False
        for i, e in enumerate(unused):
            for flip in (False, True):
                a, b = (e[1], e[0]) if flip else (e[0], e[1])
                if math.dist(a, ch[-1]) < TOL:
                    ch.append(b); unused.pop(i); grown = True; break
                if math.dist(b, ch[0]) < TOL:
                    ch.insert(0, a); unused.pop(i); grown = True; break
            if grown:
                break
    chains.append(ch)
out = []
for ch in chains:
    xs = [p[0] for p in ch]; ys = [p[1] for p in ch]
    closed = math.dist(ch[0], ch[-1]) < TOL and len(ch) > 3
    out.append({'closed': closed, 'n': len(ch), 'bbox': [min(xs), min(ys), max(xs), max(ys)], 'pts': ch})
out.sort(key=lambda c: -(c['bbox'][2] - c['bbox'][0]) * (c['bbox'][3] - c['bbox'][1]))
json.dump(out, open(sys.argv[6], 'w'))
for i, c in enumerate(out):
    b = c['bbox']
    if c['n'] >= 3 or b[2] - b[0] > 1:
        print(i, 'closed' if c['closed'] else 'open  ', c['n'], 'x %.3f..%.3f (w %.3f)  y %.3f..%.3f (h %.3f)' % (b[0], b[2], b[2] - b[0], b[1], b[3], b[3] - b[1]))
