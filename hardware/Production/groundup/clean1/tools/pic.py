#!/usr/bin/env python3
"""pic.py geo.json out.png x0 y0 x1 y1 [--layers=F,In2,In3,B] [--audit=audit.json] [--fills] [--px=40] [--title=..] [--hl=id,id]
KiCad-like picture of a window of the board from a dumpgeo.py dump: tracks at true width (round ends, see-through so
overlaps show darker), pads, vias, optional zone fills, optional audit markers."""
import json, sys, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Circle
from matplotlib.collections import PatchCollection, LineCollection
from shapely.geometry import LineString, box

MM = 1e-6
COL = dict(F='#c83434', In1='#7fc87f', In2='#ce7d2c', In3='#4fcbcb', In4='#db628b', B='#4d7fc4')
KCOL = dict(width_step='#ffff00', width_tee='#ffff00', end_off_pad='#ff00ff', end_off_via='#ff00ff', end_off_track='#00ff00', near_miss='#00ff00',
            dangling='#ffffff', acute='#ff8800', collinear_ovl='#00ffff', body_ovl='#00ffff', tiny='#ffffff', through_pad='#aaaaaa', cross='#ff0000', off45='#8888ff')

def draw(ax, g, win, layers, fills=False, alpha=0.62, hl=(), dim=None, centre=True):
    x0, y0, x1, y1 = win; B = box(x0 / MM, y0 / MM, x1 / MM, y1 / MM)
    ax.set_facecolor('#001023')
    if fills:
        for f in g['fills']:
            if f['l'] not in layers: continue
            for outer, holes in f['polys']:
                xs = [p[0] * MM for p in outer]; ys = [p[1] * MM for p in outer]
                if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1: continue
                ax.add_patch(MPoly(list(zip(xs, ys)), closed=True, fc=COL[f['l']], ec='none', alpha=0.13, zorder=1))
    for li, l in enumerate(layers[::-1]):
        for t in g['tracks']:
            if t['l'] != l: continue
            if max(t['x1'], t['x2']) * MM < x0 - 1 or min(t['x1'], t['x2']) * MM > x1 + 1 or max(t['y1'], t['y2']) * MM < y0 - 1 or min(t['y1'], t['y2']) * MM > y1 + 1: continue
            if (t['x1'], t['y1']) == (t['x2'], t['y2']): poly = LineString([(t['x1'], t['y1']), (t['x2'] + 1, t['y2'])]).buffer(t['w'] / 2)
            else: poly = LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w'] / 2, 12)
            a = alpha if (dim is None or t['net'] in dim) else 0.15
            ax.add_patch(MPoly([(p[0] * MM, p[1] * MM) for p in poly.exterior.coords], closed=True, fc=COL[l], ec='#000000' if t['id'] not in hl else '#ffffff', lw=0.25 if t['id'] not in hl else 1.2, alpha=a, zorder=3 + li))
            if centre: ax.plot([t['x1'] * MM, t['x2'] * MM], [t['y1'] * MM, t['y2'] * MM], color='#ffffff', lw=0.3, alpha=0.5, zorder=20, marker='o', ms=1.2, mew=0)
    for p in g['pads']:
        if not (x0 - 3 < p['x'] * MM < x1 + 3 and y0 - 3 < p['y'] * MM < y1 + 3): continue
        for l, pts in p['L'].items():
            if l in layers and len(pts) >= 3 and l in ('F', 'B'):
                ax.add_patch(MPoly([(q[0] * MM, q[1] * MM) for q in pts], closed=True, fc='#b0a060' if l == 'F' else '#6080b0', ec='#ffffff', lw=0.3, alpha=0.45, zorder=12))
                ax.plot([p['x'] * MM], [p['y'] * MM], '+', color='#ffffff', ms=3, mew=0.4, zorder=21)
    for v in g['vias']:
        if not (x0 - 1 < v['x'] * MM < x1 + 1 and y0 - 1 < v['y'] * MM < y1 + 1): continue
        ax.add_patch(Circle((v['x'] * MM, v['y'] * MM), v['d'] / 2 * MM, fc='#d0d0d0', ec='#000000', lw=0.3, alpha=0.6, zorder=14))
        ax.add_patch(Circle((v['x'] * MM, v['y'] * MM), v['drill'] / 2 * MM, fc='#202020', ec='none', zorder=15))
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect('equal')

def main():
    a = [s for s in sys.argv[1:] if not s.startswith('--')]; o = dict(s[2:].split('=', 1) if '=' in s else (s[2:], '1') for s in sys.argv[1:] if s.startswith('--'))
    g = json.load(open(a[0])); win = tuple(float(v) for v in a[2:6]); layers = o.get('layers', 'F,In2,In3,In4,B').split(',')
    px = float(o.get('px', 40)); W = (win[2] - win[0]) * px / 100; H = (win[3] - win[1]) * px / 100
    fig, ax = plt.subplots(figsize=(W, H), dpi=100)
    draw(ax, g, win, layers, fills='fills' in o, hl=set(o.get('hl', '').split(',')))
    if 'audit' in o:
        kinds = set(o.get('kinds', 'width_step,width_tee,end_off_pad,end_off_via,end_off_track,near_miss,dangling,acute,collinear_ovl,body_ovl,tiny,cross').split(','))
        for d in json.load(open(o['audit'])):
            if d['kind'] in kinds and d['l'] in layers and win[0] < d['x'] < win[2] and win[1] < d['y'] < win[3]:
                ax.plot([d['x']], [d['y']], 'o', mfc='none', mec=KCOL.get(d['kind'], '#fff'), ms=9, mew=0.9, zorder=30)
    ax.tick_params(labelsize=6, colors='#888888'); ax.set_title(o.get('title', ''), fontsize=8)
    fig.tight_layout(pad=0.3); fig.savefig(a[1], dpi=100); print('wrote', a[1])
if __name__ == '__main__': main()
