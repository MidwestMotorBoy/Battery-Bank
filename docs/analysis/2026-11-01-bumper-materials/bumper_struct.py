"""Engineered bumper slabs (2026-11-05): gyroid (bending, plateau ~ rho^2) vs vertical-wall honeycomb (buckling, plateau
~ rho^3) vs an ideal flat plateau, in Flexible 50A and TPU 95A, through the 10-31 two-mass drop model (top + bottom poses).
Moduli are impact-rate: TPU 95A 40 MPa (the model's E_TPU), Flexible 50A 2.6 MPa static x1.5 = 3.9 MPa.
python bumper_struct.py -> out/bumper_struct.json (the printout is out/struct.log)"""
import os, sys, json, numpy as np
import resin as R, drop as D, contact as C
E_IMP = {'TPU 95A': 40.0, 'Flexible 50A': 3.9, 'Flexible 80A V2': 12.3}
RHO_M = {'TPU 95A': 1.20, 'Flexible 50A': 1.05, 'Flexible 80A V2': 1.09}
ETA = {'TPU 95A': 0.35, 'Flexible 50A': 0.5, 'Flexible 80A V2': 0.6}
CUR = {}
def solid(eps, E):             # neo-Hookean confined solid, as contact.solid_tpu
    lam = np.clip(1 - eps, 0.05, 1); return C.CONF * E / 3 * (1 / lam**2 - lam)
def law(eps, kind, rho, E):
    eps = np.asarray(eps, float); eD = 1 - 1.4 * rho
    if kind == 'gyroid':
        k = (rho / 0.20)**2 * E / 40.0; Eg, pl = 2.0 * k, 0.30 * k
        s = pl * (1 - np.exp(-Eg * eps / pl)) + 0.3 * pl * eps / eD
    elif kind == 'honeycomb':  # hex cells, walls along the crush: axial until they buckle, then a gently rising plateau
        sb = 3.4 * E * rho**3; eb = sb / (E * rho)
        s = np.where(eps < eb, E * rho * eps, sb * (1 + 0.3 * (eps - eb) / max(eD - eb, 1e-3)))
    elif kind == 'ideal':      # perfectly flat plateau at sigma_p = rho (MPa here), densifies at 0.75
        eD = 0.75; s = np.where(eps < 0.01, rho * eps / 0.01, rho)
        dens = np.clip((eps - eD) / (1 - eD), 0, None); return s + solid(np.minimum(dens, 0.9), 40.0) * (dens > 0)
    dens = np.clip((eps - eD) / (1 - eD), 0, None)
    return s + solid(np.minimum(dens, 0.9), E) * (dens > 0)
_s0 = R._s0
def stress(mat, eps, thick):
    if mat == 'slab': return law(eps, CUR['kind'], CUR['rho'], CUR['E'])
    if mat == 'tpu': return solid(eps, CUR['Eb'])
    return _s0(mat, eps, thick)
C.stress = stress
K = R.K; M_SHELL0, M_ALL0 = R.M_SHELL0, R.M_ALL0
G0 = 1.2 * (R.VB + 0.30 * R.VS + 0.15 * R.VP)
def run(name, kind, rho, mat, band_mat, h=1.0, tscale=1.0):
    CUR.update(kind=kind, rho=rho, E=E_IMP[mat], Eb=E_IMP[band_mat])
    rc = R.rc_case(name)
    if tscale != 1.0:
        rc = dict(rc); th = rc['thick'].copy(); m = np.isin(rc['part'], [rc['names'].index('bumpt_slab'), rc['names'].index('bumpb_slab')]); th[m] *= tscale; rc['thick'] = th
    C.MAT['bumpt_slab'] = C.MAT['bumpb_slab'] = 'slab'
    rho_eff = 0.15 if kind == 'ideal' else rho
    g_soft = RHO_M[band_mat] * R.VB + RHO_M[mat] * rho_eff * R.VS * tscale + 1.2 * 0.15 * R.VP
    dm = (g_soft - G0) / 1000; D.M_SHELL, D.M_ALL = M_SHELL0 + dm, M_ALL0 + dm
    D.V0 = np.sqrt(2 * D.G * h); D.PRM['PAD_FILL'] = 0.15
    dl, Fc = D.force_curve(rc, dmax=9.0, step=0.01)
    if name == 'bottom': Fp, _ = D.pad_curve(); tr = D.simulate(dl, Fc, None, F_sc=Fp, eta=ETA[mat], dt=2e-7)
    else: tr = D.simulate(dl, Fc, K[name]['k_struct_N_per_mm'] * 1e3, eta=ETA[mat], dt=2e-7)
    D.M_SHELL, D.M_ALL = M_SHELL0, M_ALL0; D.V0 = np.sqrt(2 * D.G)
    return dict(g=round(float(np.abs(tr[:, 8]).max())), crush=round(float(tr[:, 1].max() * 1e3), 2), F=round(float(tr[:, 5].max())),
                slab_g=round(RHO_M[mat] * rho_eff * R.VS * tscale, 2), soft_g=round(g_soft, 2))
if __name__ == '__main__':
    out = {}
    grid = {'gyroid': [0.2, 0.3, 0.4, 0.5, 0.6], 'honeycomb': [0.08, 0.1, 0.12, 0.14, 0.17, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55]}
    for name in ('top', 'bottom'):
        for mat in ('TPU 95A', 'Flexible 50A'):
            for kind, rhos in grid.items():
                for rho in rhos:
                    r1 = run(name, kind, rho, mat, mat); r15 = run(name, kind, rho, mat, mat, 1.5)
                    out[f'{name} | {mat} {kind} {rho:.2f}'] = dict(m1=r1, m15=r15)
                    print(name, mat, kind, rho, r1['g'], r15['g'], r1['crush'], r1['slab_g'], flush=True)
        for sp in (0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0):
            r1 = run(name, 'ideal', sp, 'TPU 95A', 'TPU 95A'); out[f'{name} | ideal {sp}'] = dict(m1=r1); print(name, 'ideal', sp, r1['g'], r1['crush'], flush=True)
    json.dump(out, open(os.path.join(R.OUT, 'bumper_struct.json'), 'w'), indent=1)
