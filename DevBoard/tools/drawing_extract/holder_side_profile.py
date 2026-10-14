"""Upper side-view silhouette of the MYOUNG holder (thin outline strokes) as an (x, z) polyline in mm:
x from the holder centre, z above the seating plane. For each x, the highest outline point."""
import sys, json, math
segs = json.load(open(sys.argv[1]))['side']
S, XC, ZB = 2.513, 185.58, 276.64
pts = []
for s in segs:
    if s['w'] > 0.3:
        continue                                   # outlines are the thin strokes in this drawing
    p = s['p']
    if s['k'] == 'c':
        a, b, c, e = p
        p = [((1-t)**3*a[0]+3*(1-t)**2*t*b[0]+3*(1-t)*t*t*c[0]+t**3*e[0], (1-t)**3*a[1]+3*(1-t)**2*t*b[1]+3*(1-t)*t*t*c[1]+t**3*e[1]) for t in [i/10 for i in range(11)]]
    for a, b in zip(p, p[1:]):
        n = max(1, int(math.dist(a, b) / 0.2))
        for i in range(n + 1):
            x = a[0] + (b[0] - a[0]) * i / n; y = a[1] + (b[1] - a[1]) * i / n
            pts.append(((x - XC) / S, (ZB - y) / S))
pts = [p for p in pts if -41.4 <= p[0] <= 41.4 and -0.1 <= p[1] <= 16]
# upper envelope on a 0.1 mm grid
env = {}
for x, z in pts:
    k = round(x, 1)
    env[k] = max(env.get(k, -9), z)
xs = sorted(env)
prof = [(x, round(env[x], 3)) for x in xs]
# simplify: keep points where the slope changes
out = [prof[0]]
for i in range(1, len(prof) - 1):
    (x0, z0), (x1, z1), (x2, z2) = out[-1], prof[i], prof[i + 1]
    if abs((z1 - z0) * (x2 - x1) - (z2 - z1) * (x1 - x0)) > 0.02:
        out.append(prof[i])
out.append(prof[-1])
json.dump(out, open(sys.argv[2], 'w'))
print(len(prof), '->', len(out))
for p in out:
    print('  ', p)
