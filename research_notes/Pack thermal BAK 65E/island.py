"""Local 3-D model of an SMD NTC on a thermally isolated B.Cu island under the gap filler (2026-10-28).
Board (1.6 mm) with the thermal-via zone smeared (k 38 in plane, 8 through) except under the island and its moat, where all
copper and vias are cleared (FR4, 0.3 W/mK); the island itself is 70 um of copper on B.Cu. Gel (3.5 W/mK) fills the gap to the
can. F.Cu is held at 1.24 and the can at 0, which puts the far-field B.Cu at about 1.0 (the via zone's own through-drop).
Prints f = (island - can) / (far-field B.Cu - can): 1 = reads the board, 0 = reads the can.
Run: python island.py"""
import numpy as np, scipy.sparse as sp, pyamg

def solve(isl=(2.0, 2.5), moat=0.4, gel=2.9, h=0.05, half=4.0, k_fr4=0.3, k_gel=3.5, fcu_clear=False):
    tb = 1.6; nx = int(round((tb + gel)/h)); ny = nz = int(round(2*half/h))
    x = (np.arange(nx) + 0.5)*h; y = (np.arange(ny) + 0.5)*h - half; z = y.copy()
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    foot = (np.abs(Y) <= isl[0]/2 + moat) & (np.abs(Z) <= isl[1]/2 + moat)
    cu = (np.abs(Y) <= isl[0]/2) & (np.abs(Z) <= isl[1]/2) & (X >= tb - 0.07) & (X < tb)
    brd = X < tb
    kx = np.where(brd, 8.0, k_gel); ky = np.where(brd, 38.0, k_gel)
    kx = np.where(brd & foot, k_fr4, kx); ky = np.where(brd & foot, k_fr4, ky)
    kx = np.where(cu, 390.0, kx); ky = np.where(cu, 390.0, ky)
    kz = ky
    n = nx*ny*nz; idx = np.arange(n).reshape(nx, ny, nz)
    rows, cols, vals = [], [], []; diag = np.zeros(n); b = np.zeros(n)
    for k, ax in ((kx, 0), (ky, 1), (kz, 2)):
        sl0 = [slice(None)]*3; sl1 = [slice(None)]*3; sl0[ax] = slice(0, -1); sl1[ax] = slice(1, None)
        g = 2.0/(1.0/k[tuple(sl0)] + 1.0/k[tuple(sl1)])*h   # W/K per face for h-cubes (times 1e-3 m scale cancels)
        i0 = idx[tuple(sl0)].ravel(); i1 = idx[tuple(sl1)].ravel(); g = g.ravel()
        rows += [i0, i1]; cols += [i1, i0]; vals += [-g, -g]
        np.add.at(diag, i0, g); np.add.at(diag, i1, g)
    # Dirichlet: F.Cu face (x=0) at 1.24 (or, if F.Cu is cleared over the footprint, adiabatic there), can face (x=end) at 0
    gf = 2*kx[0].ravel()*h; ff = np.ones(ny*nz, bool) if not fcu_clear else ~foot[0].ravel()
    diag[idx[0].ravel()[ff]] += gf[ff]; b[idx[0].ravel()[ff]] += 1.24*gf[ff]
    gc = 2*kx[-1].ravel()*h; diag[idx[-1].ravel()] += gc
    A = sp.coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr() + sp.diags(diag)
    T = pyamg.smoothed_aggregation_solver(A.tocsr(), symmetry='symmetric').solve(b, tol=1e-9, accel='cg', maxiter=400).reshape(nx, ny, nz)
    ib = int((tb - 0.035)/h)
    far = T[ib, 0, 0]; t_isl = T[ib, ny//2, nz//2]
    return t_isl/far, far

if __name__ == '__main__':
    print('plain SMD on the via zone (no island):  f = 1 by definition')
    for isl, moat, gel, fc in [((2.0, 2.5), 0.4, 2.9, False), ((2.0, 2.5), 0.8, 2.9, False), ((4.0, 4.0), 0.5, 2.9, False),
                               ((2.0, 2.5), 0.4, 2.9, True), ((4.0, 4.0), 0.5, 2.9, True), ((2.0, 2.5), 0.4, 1.5, True)]:
        f, far = solve(isl, moat, gel, fcu_clear=fc)
        print(f'island {isl[0]}x{isl[1]} mm, moat {moat}, gel {gel} mm, F.Cu {"cleared" if fc else "hot over it"}: f = {f:.2f} (far B.Cu {far:.2f})')
