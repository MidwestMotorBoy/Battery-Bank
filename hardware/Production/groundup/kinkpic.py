"""kinkpic.py out.png before_cu.json after_cu.json spec.json "x0,y0,x1,y1[=title];..." [--map] [--w=inches] [--dpi=n]
Before / after pictures of a straightening pass. The copper dumps come from dumpcu.py, the spec from straighten.py.
Default: one row per box, before on the left and after on the right at the same scale; the runs that changed are in
full colour by layer (white edge), everything else is dimmed.
--map: one box only, the after board with every change drawn over it: the parts of the old paths that are gone in
red, the new parts in green, and a ring around each changed spot (needs shapely)."""
import json, sys, math
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import Circle
a = [x for x in sys.argv[1:] if not x.startswith('--')]; OPT = dict((x[2:].split('=', 1) + ['1'])[:2] for x in sys.argv[1:] if x.startswith('--'))
out = a[0]; D = [json.load(open(a[1])), json.load(open(a[2]))]; spec = json.load(open(a[3]))
boxes = []
for b in a[4].split(';'):
    c, _, t = b.partition('='); boxes.append(([float(v) for v in c.split(',')], t))
COL = dict(F='#e25555', In1='#9aa3ad', In2='#f0b43c', In3='#4fc27a', In4='#b98ae6', B='#4f8fe8'); ORD = ['B', 'In4', 'In3', 'In2', 'In1', 'F']
MM = 1e-6
RUNS = [dict(net=r['net'], l=r['l'], w=r['w'] * MM, old=[(p[0] * MM, p[1] * MM) for p in r['old']], new=[(p[0] * MM, p[1] * MM) for p in r['new']],
             txt='%s  %.2f to %.2f mm, %d to %d bends' % (r['net'].split('/')[-1], r['len0'], r['len1'], r['bends0'], r['bends1'])) for r in spec['runs']
        if [tuple(p) for p in r['old']] != [tuple(p) for p in r['new']]]
def base(ax, d, x0, y0, x1, y1, ppmm, dim=0.30):
    ax.set_facecolor('#10151c'); ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect('equal')
    inb = lambda x, y, m=1.0: x0 - m < x < x1 + m and y0 - m < y < y1 + m
    pads = [p for p in d['pads'] if inb(p['x'], p['y'], 4)]
    for L in ('B', 'F'):
        ax.add_collection(PolyCollection([p['L'][L] for p in pads if p['L'].get(L)], facecolors='#7c8794' if L == 'F' else '#56606c', alpha=0.32, edgecolors='none'))
    tr = [s for s in d['tracks'] if inb(s['x1'], s['y1']) or inb(s['x2'], s['y2']) or inb((s['x1'] + s['x2']) / 2, (s['y1'] + s['y2']) / 2)]
    for L in ORD:
        o = [s for s in tr if s['l'] == L]
        ax.add_collection(LineCollection([[(s['x1'], s['y1']), (s['x2'], s['y2'])] for s in o], linewidths=[max(s['w'] * ppmm, 0.5) for s in o], colors=COL[L], alpha=dim, capstyle='round'))
    for v in d['vias']:
        if inb(v['x'], v['y']): ax.add_patch(Circle((v['x'], v['y']), v['d'] / 2, fc='#aeb4bb', ec='none', alpha=0.75, zorder=6)); ax.add_patch(Circle((v['x'], v['y']), v['drill'] / 2, fc='#10151c', ec='none', zorder=7))
    ax.tick_params(colors='#666', labelsize=7)
def hit(r, x0, y0, x1, y1):
    return any(x0 < x < x1 and y0 < y < y1 for x, y in r['old'] + r['new'])
Wd = float(OPT.get('w', 13.0))
if 'map' in OPT:
    (x0, y0, x1, y1), title = boxes[0]; H = Wd * (y1 - y0) / (x1 - x0)
    fig, ax = plt.subplots(1, 1, figsize=(Wd + 0.4, H + 0.9)); ppmm = 0.9 * Wd * 72 / (x1 - x0)
    base(ax, D[1], x0, y0, x1, y1, ppmm, dim=0.22)
    from shapely.geometry import LineString
    def lines(g):
        if g.is_empty: return []
        if g.geom_type == 'LineString': return [list(g.coords)]
        return [list(x.coords) for x in getattr(g, 'geoms', []) if x.geom_type == 'LineString']
    from shapely.ops import unary_union
    red = []; grn = []; blobs = []
    for r in RUNS:
        o, n = LineString(r['old']), LineString(r['new'])
        go, gn = o.difference(n.buffer(0.02)), n.difference(o.buffer(0.02))                   # only where the two paths differ
        red += lines(go); grn += lines(gn)
        if not go.is_empty: blobs.append(go.buffer(0.4))
        if not gn.is_empty: blobs.append(gn.buffer(0.4))
    u = unary_union(blobs); spots = list(getattr(u, 'geoms', [u]))
    for g in spots:                                                                           # one ring per changed spot
        x0_, y0_, x1_, y1_ = g.bounds
        ax.add_patch(Circle(((x0_ + x1_) / 2, (y0_ + y1_) / 2), math.hypot(x1_ - x0_, y1_ - y0_) / 2 + 0.2, fc='none', ec='#ffffff', lw=0.7, alpha=0.6, zorder=10))
    ax.add_collection(LineCollection(red, linewidths=max(0.2 * ppmm, 1.0), colors='#ff4d4d', alpha=0.95, capstyle='round', zorder=8))
    ax.add_collection(LineCollection(grn, linewidths=max(0.2 * ppmm, 1.0), colors='#5dff8a', alpha=0.95, capstyle='round', zorder=9))
    ax.set_title(title or 'every change: %d runs in %d spots (rings). Red = track taken away, green = track put in its place' % (len(RUNS), len(spots)), fontsize=11, loc='left')
    fig.tight_layout(); fig.savefig(out, dpi=int(OPT.get('dpi', 100))); sys.exit()
hr = [(b[3] - b[1]) / (b[2] - b[0]) for b, _ in boxes]; pw = Wd / 2
fig, axs = plt.subplots(len(boxes), 2, figsize=(Wd + 0.3, sum(pw * h for h in hr) + 0.55 * len(boxes) + 0.5), squeeze=False, gridspec_kw=dict(height_ratios=hr))
for row, ((x0, y0, x1, y1), title) in enumerate(boxes):
    ppmm = 0.88 * pw * 72 / (x1 - x0); rr = [r for r in RUNS if hit(r, x0, y0, x1, y1)]
    for c, (d, k) in enumerate(zip(D, ('old', 'new'))):
        ax = axs[row][c]; base(ax, d, x0, y0, x1, y1, ppmm)
        for r in rr:
            ax.add_collection(LineCollection([r[k]], linewidths=r['w'] * ppmm + 2.2, colors='white', alpha=0.9, capstyle='round', joinstyle='round', zorder=4))
            ax.add_collection(LineCollection([r[k]], linewidths=r['w'] * ppmm, colors=COL[r['l']], alpha=1.0, capstyle='round', joinstyle='round', zorder=5))
        ln = sum(sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(r[k], r[k][1:])) for r in rr); nb = sum(len(r[k]) - 1 for r in rr)
        ax.set_title(('%s   ' % title if title and c == 0 else '') + ('before' if c == 0 else 'after') + ': highlighted runs %.1f mm in %d segments' % (ln, nb), fontsize=10, loc='left')
h = [plt.Line2D([], [], color=COL[L], lw=5, label=L + '.Cu') for L in ('F', 'In2', 'In3', 'In4', 'B')]
fig.legend(handles=h, loc='lower center', ncol=5, frameon=False, fontsize=9)
fig.tight_layout(rect=(0, 0.02, 1, 1)); fig.savefig(out, dpi=int(OPT.get('dpi', 100)))
