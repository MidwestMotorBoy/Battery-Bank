"""Sensitivity of the flat top drop (the 6 mm, 20 % gyroid slab over the port end) and the other cases to the TPU
properties, the drop height and the slab build. Re-runs only the two-mass impact (drop.simulate) on the cached
contact maps (cache/<case>.npz from drop.py), with the FE structure stiffness from out/drop.json.
Run after drop.py: python sens.py -> out/sens.json"""
import os, json, numpy as np
import contact as C
import drop as D
HERE = os.path.dirname(os.path.abspath(__file__))
C.GYROID[0.30] = dict(E=C.GYROID[0.20]['E'] * 1.5**2, pl=C.GYROID[0.20]['pl'] * 1.5**2)     # elastomer lattice ~ rho^2

def rc_of(name):
    z = np.load(os.path.join(HERE, 'cache', f'{name}.npz'))
    return dict(gap=z['gap'], part=z['part'], thick=z['thick'], names=list(z['names']), res=float(z['res']), R=z['R'],
                origin=z['origin'], shape=z['gap'].shape)

def peak(name, rc, k_struct, h=1.0):
    D.V0 = np.sqrt(2 * D.G * h)
    dl, Fc = D.force_curve(rc, dmax=9.0, step=0.01)
    if name == 'bottom': Fp, _ = D.pad_curve(); tr = D.simulate(dl, Fc, None, F_sc=Fp, dt=2e-7)
    else: tr = D.simulate(dl, Fc, k_struct * 1e3, dt=2e-7)
    D.V0 = np.sqrt(2 * D.G * 1.0)
    return dict(g_core=float(np.abs(tr[:, 8]).max()), g_shell=float(np.abs(tr[:, 7]).max()), F=float(tr[:, 5].max()),
                crush=float(tr[:, 1].max() * 1e3))

if __name__ == '__main__':
    res = json.load(open(os.path.join(HERE, 'out', 'drop.json')))
    out = {}
    hs = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
    for name, r in res['cases'].items():                      # peak g vs drop height, nominal properties
        rc = rc_of(name); out.setdefault('height', {})[name] = [peak(name, rc, r['k_struct_N_per_mm'], h) for h in hs]
        print(name, [round(x['g_core']) for x in out['height'][name]], flush=True)
    out['heights'] = hs
    # TPU properties x0.5 .. x1.5 at 1 m
    for name, r in res['cases'].items():
        rc = rc_of(name); row = {}
        for key in ('gyroid', 'tpu'):
            for s in (0.5, 0.75, 1.25, 1.5):
                C.SCALE[key] = s; row[f'{key} x{s}'] = peak(name, rc, r['k_struct_N_per_mm']); C.SCALE[key] = 1.0
        out.setdefault('props', {})[name] = row
        print(name, {k: round(v['g_core']) for k, v in row.items()}, flush=True)
    # slab builds for the top drop: thickness and infill
    rc0 = rc_of('top'); k = res['cases']['top']['k_struct_N_per_mm']; slab = rc0['names'].index('bumpt_slab')
    builds = {}
    for t in (6.0, 7.0, 8.0, 10.0):
        for rho in (0.20, 0.30):
            rc = dict(rc0); th = rc0['thick'].copy(); m = rc0['part'] == slab; th[m] = th[m] * t / 6.0; rc['thick'] = th
            C.MAT['bumpt_slab'] = f'gyroid{int(rho * 100)}'
            builds[f'{t:.0f} mm {rho:.0%}'] = {f'{h} m': peak('top', rc, k, h) for h in (0.5, 1.0, 1.5)}
    C.MAT['bumpt_slab'] = 'gyroid20'
    out['top_builds'] = builds
    for b, v in builds.items(): print(b, {h: round(x['g_core']) for h, x in v.items()})
    json.dump(out, open(os.path.join(HERE, 'out', 'sens.json'), 'w'), indent=1)
