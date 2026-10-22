"""Extract outline segments (display coordinates, points) of each view of the USB-C drawing."""
import sys, json
sys.path.insert(0, sys.argv[1])
import pymupdf

doc = pymupdf.open(sys.argv[2])
pg = doc[0]
M = pg.rotation_matrix
W, H = pg.rect.width, pg.rect.height
VIEWS = {   # display-page fractions (x0, y0, x1, y1), from the rendered crops
    'top': (0.05, 0.47, 0.25, 0.73),
    'side': (0.31, 0.40, 0.42, 0.73),
    'bottom': (0.48, 0.40, 0.68, 0.73),
    'front': (0.07, 0.73, 0.30, 0.93),
    'layout': (0.35, 0.04, 0.66, 0.35),
}
segs = {k: [] for k in VIEWS}
for d in pg.get_drawings():
    wdt = round(d.get('width') or 0, 2)
    for it in d['items']:
        kind = it[0]
        if kind == 'l':
            pts = [it[1], it[2]]
        elif kind == 'c':
            pts = [it[1], it[2], it[3], it[4]]
        elif kind == 're':
            r = it[1]
            pts = [pymupdf.Point(r.x0, r.y0), pymupdf.Point(r.x1, r.y0), pymupdf.Point(r.x1, r.y1), pymupdf.Point(r.x0, r.y1), pymupdf.Point(r.x0, r.y0)]
        else:
            continue
        P = [p * M for p in pts]
        cx, cy = sum(p.x for p in P) / len(P) / W, sum(p.y for p in P) / len(P) / H
        for k, (a, b, c, e) in VIEWS.items():
            if a <= cx <= c and b <= cy <= e:
                segs[k].append({'k': kind, 'w': wdt, 'p': [[round(p.x, 3), round(p.y, 3)] for p in P]})
json.dump(segs, open(sys.argv[3], 'w'))
for k, v in segs.items():
    print(k, len(v), {w: sum(1 for s in v if s['w'] == w) for w in sorted(set(s['w'] for s in v))})
