"""PEBA 85A (JLC3DP FDM) bumpers against the TPU 95A ones, through the same 1 m drop model: the six poses' contact maps
(cache/<case>.npz from drop.py) and FE structure stiffness (out/drop.json), re-run through drop.simulate with the
bumper material swapped. Only the bumpers change; the cap pad stays 10 % TPU.
PEBA 85A vs TPU 95A, all estimates (no PEBA compression data yet):
  stiffness   x0.45 nominal (FDM 85A ~12 MPa vs 95A ~26 MPa), range x0.3-0.6; the gyroid scales with the solid
  density     1.0 vs 1.2 g/cm3 (JLC3DP data): the bumpers get 17 % lighter at the same build
  rebound     unloading at 0.60 x the loading force (high-resilience PEBA) vs 0.35 for TPU
  cold        at -20 C: TPU 95A ~x2.5 stiffer, PEBA ~x1.3 (it stays flexible to about -40 C)
Run after drop.py: python peba.py -> out/peba.json"""
import os, json, numpy as np
import contact as C
import drop as D
from sens import rc_of
HERE = os.path.dirname(os.path.abspath(__file__))
RHO = dict(tpu=1.2, peba=1.0)
MAT = dict(tpu=dict(E=1.0, eta=0.35, cold=2.5), peba=dict(E=0.45, eta=0.60, cold=1.3))
_gyroid0 = C.gyroid
def gyroid(eps, rho):
    """the slab lattice: stiffness and plateau ~ solid x rho^2 (from the 20 % calibration); the 10 % pad is TPU, unscaled"""
    g20 = C.GYROID[0.20]; k = (rho / 0.20)**2
    E, pl = g20['E'] * k, g20['pl'] * k
    if abs(rho - 0.10) > 1e-9: E, pl = E * C.SCALE['gyroid'], pl * C.SCALE['gyroid']
    else: E, pl = C.GYROID[0.10]['E'], C.GYROID[0.10]['pl']
    eD = 1 - 1.4 * rho
    s = pl * (1 - np.exp(-E * eps / pl)) + 0.3 * pl * eps / eD
    dens = np.clip((eps - eD) / (1 - eD), 0, None)
    return s + C.solid_tpu(np.minimum(dens, 0.9)) * (dens > 0)
C.gyroid = gyroid
_stress0 = C.stress
def stress(mat, eps, thick):
    if mat.startswith('gyroid'): return gyroid(eps, int(mat[6:]) / 100)
    return _stress0(mat, eps, thick)
C.stress = stress

def bumper_g(mat, fill):
    """bumper mass: solid bands + slabs at `fill`, from the cup model's TPU masses"""
    import geom
    A, MASS, P = geom.load()
    vol = lambda k: sum(abs(np.einsum('ij,ij->i', V[:, 0], np.cross(V[:, 1], V[:, 2])).sum()) / 6 for kk, V, _ in A if kk == k) / 1000
    band = vol('bumpt_band') + vol('bumpb_band'); slab = vol('bumpt_slab') + vol('bumpb_slab')
    return float(RHO[mat] * (band + fill * slab))

def run_case(name, rc, k_struct, h, mat, fill, cold=False):
    m = MAT[mat]; s = m['E'] * (m['cold'] if cold else 1.0)
    C.SCALE['tpu'] = C.SCALE['gyroid'] = s
    C.MAT['bumpt_slab'] = C.MAT['bumpb_slab'] = f'gyroid{round(fill * 100)}'
    dm = (bumper_g(mat, fill) - BUMP0) / 1000
    D.M_SHELL, D.M_ALL = M_SHELL0 + dm, M_ALL0 + dm
    D.V0 = np.sqrt(2 * D.G * h)
    dl, Fc = D.force_curve(rc, dmax=9.0, step=0.01)
    if name == 'bottom': Fp, _ = D.pad_curve(); tr = D.simulate(dl, Fc, None, F_sc=Fp, eta=m['eta'], dt=2e-7)
    else: tr = D.simulate(dl, Fc, k_struct * 1e3, eta=m['eta'], dt=2e-7)
    C.SCALE['tpu'] = C.SCALE['gyroid'] = 1.0; D.V0 = np.sqrt(2 * D.G * 1.0); D.M_SHELL, D.M_ALL = M_SHELL0, M_ALL0
    reb = tr[-1, 3] if tr[-1, 3] < 0 else 0.0
    return dict(g_core=float(np.abs(tr[:, 8]).max()), crush=float(tr[:, 1].max() * 1e3), F=float(tr[:, 5].max()),
                rebound=float(-reb))

M_SHELL0, M_ALL0 = D.M_SHELL, D.M_ALL
BUMP0 = bumper_g('tpu', 0.20)
VARIANTS = [('tpu', 0.20), ('tpu', 0.30), ('peba', 0.20), ('peba', 0.30), ('peba', 0.40)]
if __name__ == '__main__':
    res = json.load(open(os.path.join(HERE, 'out', 'drop.json')))
    out = dict(bumper_g={f'{m} {f:.0%}': bumper_g(m, f) for m, f in VARIANTS}, runs={})
    print({k: round(v, 1) for k, v in out['bumper_g'].items()})
    for name, r in res['cases'].items():
        rc = rc_of(name); k = r['k_struct_N_per_mm']
        for mat, fill in VARIANTS:
            for h, cold in ((1.0, False), (1.5, False), (1.0, True)):
                key = f'{mat} {fill:.0%} | {h} m{" cold" if cold else ""}'
                out['runs'].setdefault(name, {})[key] = run_case(name, rc, k, h, mat, fill, cold)
        print(name, {k_: round(v['g_core']) for k_, v in out['runs'][name].items()}, flush=True)
    # PEBA stiffness range at 1 m, 30 % and 40 %
    for name, r in res['cases'].items():
        rc = rc_of(name)
        for e in (0.3, 0.6):
            MAT['peba']['E'] = e
            for fill in (0.30, 0.40):
                out['runs'][name][f'peba {fill:.0%} | 1.0 m, E x{e}'] = run_case(name, rc, r['k_struct_N_per_mm'], 1.0, 'peba', fill)
        MAT['peba']['E'] = 0.45
    json.dump(out, open(os.path.join(HERE, 'out', 'peba.json'), 'w'), indent=1)
