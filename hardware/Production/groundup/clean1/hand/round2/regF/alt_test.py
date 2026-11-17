# NOT part of the spec: tests whether the three stair removals that exceed the 0.30 mm limit would be clearance-legal
import sys, json
S = '/tmp/clean1'
sys.path.insert(0, S + '/tools'); sys.path.insert(0, S + '/agents/regF')
from fixlib import Fix
import geolib as G
for name in ('srn_in2', 'c1n_in2', 'c4p_B'):
    f = Fix(S + '/r2/geo.json', region=(79, 120, 100, 137.5))
    if name == 'srn_in2':
        v = f.via(93.825, 121.5245, quiet=True); b = f.pt(92.875, 123.6245, 'In2')
        f.replace(['13c8f53b', '7c5759ae', 'ba9bde0f', 'ebe9a01b'], [v, (b[0], v[1] + (v[0] - b[0])), b])
    if name == 'c1n_in2':
        a = f.pt(97.925, 124.6745, 'In2'); v = f.via(94.425, 126.1745, quiet=True)
        f.replace(['62b547aa', '88640ee1', '3bb65879', 'bbbc8c19'], [a, (v[0] + (v[1] - a[1]), a[1]), v])
    if name == 'c4p_B':
        a = f.pt(91.325, 134.0245, 'B'); v = f.via(97.975, 136.1245, quiet=True)
        f.replace(['1960109a', 'b3bd53a2', 'bbbf5c24', 'b1f93268'], [a, (a[0] + (v[1] - a[1]), v[1]), v])
    spec = f.save(S + '/agents/regF/alt_%s.json' % name)
    res, g1 = G.check(f.g, spec, maxexc=None)
    print(name, 'ok', res['ok'], 'clearance', [(c['gap'], c['need'], c['to'], c['name'][:10], c['tonet']) for c in res['clearance']], 'exc', res['excursion_max_mm'])
