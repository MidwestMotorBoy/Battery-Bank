#!/usr/bin/env python3
"""ba.py before_geo.json after_geo.json out.png x0 y0 x1 y1 [--px=130] [--layers=F] [--title=..] [--fills]
Before (left) and after (right) of the same window, same scale."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pic
a = [s for s in sys.argv[1:] if not s.startswith('--')]; o = dict(s[2:].split('=', 1) if '=' in s else (s[2:], '1') for s in sys.argv[1:] if s.startswith('--'))
A = json.load(open(a[0])); B = json.load(open(a[1])); win = tuple(float(v) for v in a[3:7]); layers = o.get('layers', 'F').split(',')
px = float(o.get('px', 130)); W = (win[2] - win[0]) * px / 100; H = (win[3] - win[1]) * px / 100
fig, ax = plt.subplots(1, 2, figsize=(2 * W + 0.3, H + 0.35), dpi=100)
for x, g, name in ((ax[0], A, 'before'), (ax[1], B, 'after')):
    pic.draw(x, g, win, layers, fills='fills' in o, centre='nocentre' not in o); x.tick_params(labelsize=6, colors='#888888')
    x.set_title('%s  %s  %s' % (o.get('title', ''), '+'.join(layers), name), fontsize=9)
fig.tight_layout(pad=0.4); fig.savefig(a[2], dpi=100); print('wrote', a[2])
