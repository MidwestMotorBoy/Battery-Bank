"""Port-end slab thickness 6-12 mm in each material (1 m): python thick.py -> out/thick_top.json"""
import os, json, sys, numpy as np
import resin as R
rc0 = R.rc_case('top'); slab = rc0['names'].index('bumpt_slab'); out = {}
for m, fills in (('TPU 95A (FDM)', (0.30,)), ('Flexible 80A V2', (0.30, 0.40, 0.50)), ('Rebound (86A)', (0.30, 0.40)), ('Flexible 50A', (0.40, 0.55, 1.0))):
    for t in (6.0, 8.0, 10.0, 12.0):
        for f in fills:
            rc = dict(rc0); th = rc0['thick'].copy(); msk = rc0['part'] == slab; th[msk] *= t / 6.0; rc['thick'] = th
            r = R.run('top', rc, m, f, 0.3)
            dm = R.MATS[m]['rho'] * f * R.vol('bumpt_slab') * (t / 6 - 1)
            out[f'{m} | {t:.0f} mm {f:.0%}'] = dict(g=r['g'], crush=r['crush'], extra_g=dm)
            print(m, t, f, round(r['g']), round(r['crush'], 2), f'+{dm:.1f} g', flush=True)
json.dump(out, open(os.path.join(R.OUT, 'thick_top.json'), 'w'), indent=1)
