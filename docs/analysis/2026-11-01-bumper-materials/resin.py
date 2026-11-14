"""Formlabs flexible resins vs FDM TPU 95A through the 2026-10-31 1 m drop model (contact.py / drop.py):
bumper bands + slabs + cap pad swapped to each material, stiffness scaled from the solid modulus, lattice ~ rho^2.
The drop model meshes the geometry that hardware/mechanical/monolith_cup.py holds now (its cache/assembly.npz); the results
in out/ were run on the 2026-11-01 geometry (master a4ac02e to ece80e6), see the README.
python resin.py [pose ...] -> out/resin_<poses>.json"""
import os, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
AD = os.path.normpath(os.path.join(HERE, '..', '2026-10-31-drop-1m')); sys.path.insert(0, AD)
OUT = os.path.join(HERE, 'out'); CACHE = os.path.join(HERE, 'cache')
import contact as C, drop as D
K = json.load(open(os.path.join(AD, 'out', 'drop-pad15.json')))['cases']
# small-strain modulus estimates (MPa) from the data sheets' stress at 50 % elongation (neo-Hookean), vs 26 MPa FDM TPU 95A
MATS = {'TPU 95A (FDM)':      dict(E=1.00, eta=0.35, rho=1.20),
        'Flexible 80A V2':    dict(E=0.32, eta=0.60, rho=1.09),
        'Rebound (86A)':      dict(E=0.38, eta=0.60, rho=1.10),
        'Flexible 50A':       dict(E=0.10, eta=0.50, rho=1.05)}
def gy(eps, rho):
    k = (rho / 0.20)**2; E, pl = 2.0 * k * C.SCALE['gyroid'], 0.30 * k * C.SCALE['gyroid']
    eD = 1 - 1.4 * rho
    s = pl * (1 - np.exp(-E * eps / pl)) + 0.3 * pl * eps / eD
    dens = np.clip((eps - eD) / (1 - eD), 0, None)
    return s + C.solid_tpu(np.minimum(dens, 0.9)) * (dens > 0)
C.gyroid = gy
_s0 = C.stress
def stress(mat, eps, thick):
    if mat.startswith('gyroid'): return gy(eps, int(mat[6:]) / 100)
    if mat == 'solid_slab': return C.solid_tpu(eps)
    return _s0(mat, eps, thick)
C.stress = stress
def rc_case(name):
    os.makedirs(CACHE, exist_ok=True); f = os.path.join(CACHE, f'rc_{name}.npz')
    if os.path.exists(f):
        z = np.load(f); return dict(gap=z['gap'], part=z['part'], thick=z['thick'], names=list(z['names']), res=float(z['res']))
    cs = D.CASES[name]
    d = D.corner_dir(*cs['corner'])[0] if 'corner' in cs else np.asarray(cs['d'], float)
    rc = C.raycast(D.A, d / np.linalg.norm(d))
    np.savez_compressed(f, gap=rc['gap'], part=rc['part'], thick=rc['thick'], names=np.array(rc['names']), res=rc['res'])
    return rc
def vol(k): return float(sum(abs(np.einsum('ij,ij->i', V[:, 0], np.cross(V[:, 1], V[:, 2])).sum()) / 6 for kk, V, _ in D.A if kk == k) / 1000)
VB = vol('bumpt_band') + vol('bumpb_band'); VS = vol('bumpt_slab') + vol('bumpb_slab'); VP = [vol(k) for k, _, _ in D.A if k == 'pad'][0] if False else vol('pad')
def soft_g(m, slab, pad): return float(MATS[m]['rho'] * (VB + slab * VS + pad * VP))
G0 = soft_g('TPU 95A (FDM)', 0.30, 0.15)
M_SHELL0, M_ALL0 = D.M_SHELL, D.M_ALL
def run(name, rc, m, slab, pad, h=1.0):
    p = MATS[m]; C.SCALE['tpu'] = C.SCALE['gyroid'] = p['E']
    C.MAT['bumpt_slab'] = C.MAT['bumpb_slab'] = 'solid_slab' if slab >= 0.99 else f'gyroid{round(slab*100)}'
    D.PRM['PAD_FILL'] = pad
    dm = (soft_g(m, slab, pad) - G0) / 1000; D.M_SHELL, D.M_ALL = M_SHELL0 + dm, M_ALL0 + dm
    D.V0 = np.sqrt(2 * D.G * h)
    dl, Fc = D.force_curve(rc, dmax=9.0, step=0.01)
    if name == 'bottom': Fp, _ = D.pad_curve(); tr = D.simulate(dl, Fc, None, F_sc=Fp, eta=p['eta'], dt=2e-7)
    else: tr = D.simulate(dl, Fc, K[name]['k_struct_N_per_mm'] * 1e3, eta=p['eta'], dt=2e-7)
    C.SCALE['tpu'] = C.SCALE['gyroid'] = 1.0; D.M_SHELL, D.M_ALL = M_SHELL0, M_ALL0; D.V0 = np.sqrt(2 * D.G)
    return dict(g=float(np.abs(tr[:, 8]).max()), crush=float(tr[:, 1].max() * 1e3))
def pad_preload(m, fill, proud=1.2):
    """static preload of the cap pad squeezed PAD_PROUD (no rate stiffening: /1.5 off the impact modulus)"""
    V = [V for k, V, _ in D.A if k == 'pad'][0].reshape(-1, 3)
    t = np.ptp(V[:, 2]); area = 0.55 * np.ptp(V[:, 0]) * np.ptp(V[:, 1])
    C.SCALE['tpu'] = C.SCALE['gyroid'] = MATS[m]['E'] / 1.5
    F = (gy(proud / (t + proud), fill) if fill < 0.99 else C.solid_tpu(proud / (t + proud))) * area
    C.SCALE['tpu'] = C.SCALE['gyroid'] = 1.0
    return float(F), float(t), float(area)
if __name__ == '__main__':
    cases = sys.argv[1:] or list(D.CASES)
    VARS = [('TPU 95A (FDM)', 0.30, 0.15)] + [(m, s, p) for m, sp in (('Flexible 80A V2', ((0.30, 0.30), (0.45, 0.30), (0.55, 0.30), (0.65, 0.30))),
            ('Rebound (86A)', ((0.30, 0.25), (0.50, 0.25))), ('Flexible 50A', ((0.50, 0.45), (0.70, 0.45), (1.0, 0.45)))) for s, p in sp]
    res = dict(vol_cc=dict(bands=VB, slabs=VS, pad=VP), mass_g={f'{m} slab {s:.0%} pad {p:.0%}': soft_g(m, s, p) for m, s, p in VARS},
               preload_N={f'{m} {f:.0%}': pad_preload(m, f)[0] for m in MATS for f in (0.15, 0.25, 0.30, 0.45, 0.5, 1.0)}, runs={})
    print(json.dumps({k: round(v, 1) for k, v in res['mass_g'].items()}, indent=0)); print({k: round(v) for k, v in res['preload_N'].items()}, pad_preload('TPU 95A (FDM)', 0.15)[1:])
    for name in cases:
        rc = rc_case(name)
        for m, s, p in VARS:
            for h in (1.0, 1.5):
                res['runs'].setdefault(name, {})[f'{m} slab {s:.0%} pad {p:.0%} | {h} m'] = run(name, rc, m, s, p, h)
        print(name, {k: round(v['g']) for k, v in res['runs'][name].items()}, flush=True)
    json.dump(res, open(os.path.join(OUT, 'resin_' + '_'.join(cases) + '.json'), 'w'), indent=1)
