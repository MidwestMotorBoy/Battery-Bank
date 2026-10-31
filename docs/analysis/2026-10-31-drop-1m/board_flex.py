"""Board flex in a drop: the P0 board as a Kirchhoff plate (Morley triangles, scikit-fem) carrying its own mass and
its parts' masses at their places, held at the four carrier pegs (|y| 8.6, z 14 / 68) and at the two USB-C
receptacles (in the top wall's seal bores; their housings sit 0.15 mm off the pocket). Loaded by the acceleration
normal to the board (the board-face drop and the corners). Gives the deflection map, the surface strain under each
part, and each F.Cu part's clearance to the board-face wall minus the deflection.
Part masses: hull volume x 3 g/cm3, as monolith_cup.board_parts_g()."""
import os, sys, numpy as np, skfem as F
from skfem.helpers import dd, ddot, trace, eye
from scipy.spatial import ConvexHull
HERE = os.path.dirname(os.path.abspath(__file__))
MECH = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'hardware', 'mechanical'))
E_FR4, NU, T, RHO_PARTS, N = 20000.0, 0.15, 1.6, 3.0, 0.5
PEGS = [(s * 8.6, z) for s in (-1, 1) for z in (14.0, 68.0)]
X_F, X_IN = 26.9, 30.6                       # F.Cu face, board-face wall inside (monolith_cup.X_IN)
BENCH = ('J113', 'J114')

def board():
    z = np.load(os.path.join(MECH, 'board', 'monolith_board.npz'))
    B = {k: z[k].astype(float) for k in z.files if not k.startswith('_')}
    models = {k[7:]: str(z[k]) for k in z.files if k.startswith('_model_')}
    return B, models

def setup():
    B, models = board()
    pcb = B['PCB']
    yz = pcb.reshape(-1, 3)[:, 1:]
    m = F.MeshTri.init_tensor(np.arange(yz[:, 0].min(), yz[:, 0].max() + 1e-6, N), np.arange(yz[:, 1].min(), yz[:, 1].max() + 1e-6, N))
    # keep elements inside the PCB outline: centroid inside any F.Cu-face triangle of the PCB mesh
    tri = pcb[np.abs(pcb[:, :, 0] - pcb[:, :, 0].max()).max(1) < 1e-3][:, :, 1:]
    c = m.p[:, m.t].mean(1).T
    inside = np.zeros(len(c), bool)
    for t in tri:
        (y0, z0), (y1, z1), (y2, z2) = t; den = (z1 - z2) * (y0 - y2) + (y2 - y1) * (z0 - z2)
        if abs(den) < 1e-12: continue
        a = ((z1 - z2) * (c[:, 0] - y2) + (y2 - y1) * (c[:, 1] - z2)) / den
        b = ((z2 - z0) * (c[:, 0] - y2) + (y0 - y2) * (c[:, 1] - z2)) / den
        inside |= (a >= -1e-9) & (b >= -1e-9) & (a + b <= 1 + 1e-9)
    m = F.MeshTri(m.p, m.t[:, inside]).remove_unused_nodes() if hasattr(F.MeshTri, 'remove_unused_nodes') else F.MeshTri(m.p, m.t[:, inside])
    parts = {}
    for k, V in B.items():
        if k == 'PCB' or k in BENCH or models.get(k, '').startswith(('Peg_', 'SolderWire')): continue
        P = V.reshape(-1, 3)
        try: vol = ConvexHull(P).volume
        except Exception: continue
        side = 'F' if P[:, 0].mean() > X_F - 0.8 else 'B'
        parts[k] = dict(m=vol / 1000 * RHO_PARTS, y=P[:, 1].mean(), z=P[:, 2].mean(), side=side,
                        top=P[:, 0].max(), y0=P[:, 1].min(), y1=P[:, 1].max(), z0=P[:, 2].min(), z1=P[:, 2].max())
    return m, parts

def solve(a_g, m=None, parts=None, usb_fixed=True):
    """deflection w (mm, toward the F.Cu side = toward the wall for a +x deceleration) for a_g normal to the board"""
    if m is None: m, parts = setup()
    ib = F.Basis(m, F.ElementTriMorley())
    D = E_FR4 * T**3 / (12 * (1 - NU**2))
    @F.BilinearForm
    def bil(u, v, w): return ddot(D * ((1 - NU) * dd(u) + NU * eye(trace(dd(u)), 2)), dd(v))
    @F.LinearForm
    def lin(v, w): return 1.0 * v
    K = bil.assemble(ib); f1 = lin.assemble(ib)
    vdof = ib.nodal_dofs[0]; P = m.p
    pcb_g = 20.2 - sum(p['m'] for p in parts.values())          # monolith_cup: board 20.2 g with its parts
    a_, b_, c_ = P[:, m.t[0]], P[:, m.t[1]], P[:, m.t[2]]
    A_board = 0.5 * np.abs((b_[0] - a_[0]) * (c_[1] - a_[1]) - (b_[1] - a_[1]) * (c_[0] - a_[0])).sum()
    q = pcb_g / 1000 / A_board * 9.81 * a_g                         # N/mm2
    f = q * f1
    for k, p in parts.items():                                       # each part's weight spread over its footprint nodes
        sel = np.where((P[0] >= p['y0']) & (P[0] <= p['y1']) & (P[1] >= p['z0']) & (P[1] <= p['z1']))[0]
        if len(sel) == 0: sel = [np.argmin((P[0] - p['y'])**2 + (P[1] - p['z'])**2)]
        f[vdof[sel]] += p['m'] / 1000 * 9.81 * a_g / len(sel)
    fix = []
    for y, z in PEGS: fix += list(vdof[np.where(np.hypot(P[0] - y, P[1] - z) <= 1.9)[0]])
    if usb_fixed:
        for k in ('J401', 'J501'):
            p = parts[k]; fix += list(vdof[np.where((P[0] >= p['y0']) & (P[0] <= p['y1']) & (P[1] >= p['z0']))[0]])
    w = F.solve(*F.condense(K, f, D=np.unique(fix)))
    # curvature -> surface strain at the nodes (project the element-wise Hessian)
    ib0 = F.Basis(m, F.ElementTriP0())
    H = ib.interpolate(w).hess
    kxx, kyy, kxy = H[0][0].mean(1), H[1][1].mean(1), H[0][1].mean(1)
    kmax = np.maximum(np.abs(0.5 * (kxx + kyy) + np.sqrt((0.5 * (kxx - kyy))**2 + kxy**2)),
                      np.abs(0.5 * (kxx + kyy) - np.sqrt((0.5 * (kxx - kyy))**2 + kxy**2)))
    strain = kmax * T / 2                                             # per element
    return m, parts, w[vdof], strain

def part_report(m, parts, wn, strain):
    P = m.p; c = m.p[:, m.t].mean(1)
    out = {}
    for k, p in parts.items():
        sel = (P[0] >= p['y0']) & (P[0] <= p['y1']) & (P[1] >= p['z0']) & (P[1] <= p['z1'])
        ce = (c[0] >= p['y0'] - 0.5) & (c[0] <= p['y1'] + 0.5) & (c[1] >= p['z0'] - 0.5) & (c[1] <= p['z1'] + 0.5)
        w = wn[sel].max() if sel.any() else wn[np.argmin((P[0] - p['y'])**2 + (P[1] - p['z'])**2)]
        out[k] = dict(w_mm=float(w), strain_ue=float(strain[ce].max() * 1e6) if ce.any() else 0.0, side=p['side'],
                      clear_mm=float(X_IN - p['top']) if p['side'] == 'F' else None, m_g=p['m'])
    return out

if __name__ == '__main__':
    m, parts = setup()
    print(len(parts), 'parts', round(sum(p['m'] for p in parts.values()), 2), 'g of parts', m.t.shape[1], 'triangles')
    for usb in (True, False):
        m_, _, wn, st = solve(1000.0, m, parts, usb)
        print('usb fixed' if usb else 'usb free ', 'at 1000 g: w max %.3f mm, strain max %.0f ue' % (np.abs(wn).max(), st.max() * 1e6))
