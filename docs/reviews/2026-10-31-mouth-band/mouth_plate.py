"""Plate model of the cup's side flat at the mouth (2026-10-31): how far the O-ring and internal pressure push the
1.2 mm flat off the O-ring with no collar, with the cap's old 1.5 mm collar, and with a thicker mouth band.
Kirchhoff plate, Morley triangles (pip install scikit-fem). x along the flat (the back cell's tangent to the board-face
corner, 38.25 mm), z up from the mouth. Flat ends simply supported (corner R4 / cell arcs), top simply supported 60 mm up,
mouth edge free. The M2 screw (x = 16, z = 2.4) pins the wall. The collar is its own plate, clamped at the cap plate,
tied to the wall at its three crush ribs per flat. PA12 MJF E 1700 MPa (short term: creep makes every case worse).
Run: python mouth_plate.py   (~3 min)"""
import numpy as np, scipy.sparse as sp, skfem as F
from scipy.optimize import brentq
from skfem.models.poisson import unit_load
from skfem.helpers import dd, ddot, trace, eye
E, NU, N = 1700.0, 0.35, 0.25           # MPa, -, mesh step (mm)
A, H, Z_OR = 38.25, 60.0, 5.25          # flat length, wall height modelled, O-ring line above the mouth (groove 3.9-6.5)
X = lambda x: x + 11.6                  # cup x -> plate x
def plate(A, H, t_of_z):
    m = F.MeshTri.init_tensor(np.linspace(0, A, int(round(A/N))+1), np.linspace(0, H, int(round(H/N))+1))
    ib = F.Basis(m, F.ElementTriMorley())
    @F.BilinearForm
    def bil(u, v, w):
        D = E*t_of_z(w.x[1])**3/(12*(1-NU**2))
        return ddot(D*((1-NU)*dd(u) + NU*eye(trace(dd(u)), 2)), dd(v))
    return m.p, ib, bil.assemble(ib), unit_load.assemble(ib)
def screw(P, zo=0.0): return np.where((abs(P[0]-X(16)) <= 1.0) & (abs(P[1]-zo-2.4) <= 1.0))[0]
def run(q=1.0, p=0.0, band_t=1.2, band_h=7.5, collar_t=None, ribs=(-8.0, 6.0, 24.0), off=0.8, col_h=7.5):
    """(max, mean) outward deflection (mm) along the O-ring line for O-ring line load q (N/mm) and pressure p (MPa)"""
    P, bw, Kw, fw = plate(A, H, lambda z: np.where(z < band_h, band_t, 1.2)); vw = bw.nodal_dofs[0]
    f = p*fw; row = np.where(np.isclose(P[1], Z_OR))[0]; f[vw[row]] += q*N
    fix = list(vw[np.where(np.isclose(P[0], 0) | np.isclose(P[0], A) | np.isclose(P[1], H))[0]]) + list(vw[screw(P)])
    if collar_t is None:
        W = F.solve(*F.condense(Kw, f, D=np.unique(fix)))[vw]
        return W[row].max(), W[row].mean()
    Pc, bc, Kc, _ = plate(A, col_h + off, lambda z: collar_t + 0*z); vc = bc.nodal_dofs[0]; Nw = bw.N
    fc = list(vc[np.where(np.isclose(Pc[0], 0) | np.isclose(Pc[0], A) | np.isclose(Pc[1], 0))[0]])
    fc += list(bc.get_dofs(lambda x: np.isclose(x[1], 0)).all('u_n')) + list(vc[screw(Pc, off)])
    K = sp.block_diag([Kw, Kc]).tolil(); kp = 1e6
    for r in ribs:                       # crush ribs: stiff springs wall <-> collar
        for i in np.where((abs(P[0]-X(r)) <= 0.5) & (P[1] >= 1.0) & (P[1] <= col_h))[0]:
            j = np.where((abs(Pc[0]-P[0, i]) < 1e-6) & (abs(Pc[1]-(P[1, i]+off)) < 1e-6))[0]
            if len(j) != 1: continue
            a, b = vw[i], Nw + vc[j[0]]; K[a, a] += kp; K[b, b] += kp; K[a, b] -= kp; K[b, a] -= kp
    u = F.solve(*F.condense(K.tocsr(), np.r_[f, np.zeros(bc.N)], D=np.unique(np.r_[fix, Nw + np.array(fc)])))
    W = u[:Nw][vw]; return W[row].max(), W[row].mean()
def squeeze(c, s0=0.5, dp=0.0):
    """squeeze left (mm) where the wall's compliance is c (mm per N/mm): the O-ring pushes 1.1 N/mm at 0.5 mm (2.0 mm
    cord, 25 %, 70A, Parker-style curve ~ s^1.3), the wall gives, the push drops; dp = pressure's own deflection"""
    return 0.0 if s0 - dp <= 0 else brentq(lambda s: s + c*1.1*(s/0.5)**1.3 - (s0 - dp), 0, 0.5)
if __name__ == '__main__':
    cases = {'no collar': {}, 'cap collar 1.5 (to 2026-10-31)': dict(collar_t=1.5),
             'mouth band 2.0, no collar': dict(band_t=2.0), 'mouth band 2.4, no collar (adopted)': dict(band_t=2.4)}
    print(f"{'':38s} worst-spot squeeze % (25 nominal): nominal, low tol (0.35 mm), +25 kPa, +50 kPa")
    for k, kw in cases.items():
        cm = run(**kw)[0]; d50 = run(q=0, p=0.05, **kw)[0]
        r = [squeeze(cm), squeeze(cm, 0.35), squeeze(cm, 0.5, d50/2), squeeze(cm, 0.5, d50)]
        print(f'{k:38s} c {cm:.3f} mm/(N/mm), 50 kPa {d50:.3f} mm  ->  ' + '  '.join(f'{x/2*100:4.1f}' for x in r))
