"""Quasi-static voxel finite-element model of the pack for the drop study (no bumpers, no label: their crush is in
contact.py). Every closed mesh of the assembly is voxelised on an H mm grid (2x2x2 sub-samples per voxel, parity test
along x); a voxel takes the material with the largest share and its modulus is scaled by the solid fraction.
Parts that touch are bonded (cell to cup, posts to the wall): the model is stiffer than the real pack, which makes the
peak g it gives conservative. Linear 8-node bricks, pyamg-preconditioned CG.
The floor is a bed of springs on the outer voxels in the contact footprint (normal direction), with a weak tangential
spring so the model can't slide; the load is a uniform acceleration (d'Alembert body force) toward the floor."""
import numpy as np, scipy.sparse as sp, pyamg, time
H = 1.0
# material: (E MPa, nu, density g/cm3 or None = from the part mass)
MATS = {'pa12': (1700.0, 0.38, 1.01), 'cell': (2000.0, 0.30, None), 'fr4': (20000.0, 0.15, None),
        'filler': (0.5, 0.45, 3.1), 'pad': (0.6, 0.30, 0.12), 'oring': (5.0, 0.48, 1.2)}
PART_MAT = {'cup': 'pa12', 'cap': 'pa12', 'carrier': 'pa12', 'rails': 'pa12', 'cell': 'cell', 'board': 'fr4',
            'filler': 'filler', 'pad': 'pad', 'oring': 'oring'}
MAT_ID = {k: i for i, k in enumerate(MATS)}

def voxelise(A, H=H, part_mass=None):
    """returns grid dict: origin, shape, mat (int, -1 empty), frac, part (index into names), names, rho"""
    use = [(k, V) for i, (k, V, _) in enumerate(A) if k in PART_MAT and not (k == 'board' and i != first_board(A))]
    P = np.vstack([V.reshape(-1, 3) for _, V in use])
    o = np.floor(P.min(0)) - H; n = (np.ceil((P.max(0) - o) / H) + 1).astype(int)
    sub = 2; hs = H / sub; ns = n * sub
    names = sorted({k for k, _ in use})
    frac = np.zeros((len(names),) + tuple(n), np.float32)
    for k, V in use:
        occ = np.zeros(tuple(ns), bool)
        cols = {}                                    # (j, k) -> list of x crossings
        y, z = V[:, :, 1], V[:, :, 2]
        for tri in V:
            x_, y_, z_ = tri[:, 0], tri[:, 1], tri[:, 2]
            j0, j1 = int(np.ceil((y_.min() - o[1]) / hs - 0.5)), int(np.floor((y_.max() - o[1]) / hs - 0.5))
            k0, k1 = int(np.ceil((z_.min() - o[2]) / hs - 0.5)), int(np.floor((z_.max() - o[2]) / hs - 0.5))
            if j1 < j0 or k1 < k0: continue
            den = (z_[1] - z_[2]) * (y_[0] - y_[2]) + (y_[2] - y_[1]) * (z_[0] - z_[2])
            if abs(den) < 1e-12: continue
            gj, gk = np.meshgrid(np.arange(j0, j1 + 1), np.arange(k0, k1 + 1), indexing='ij')
            py, pz = o[1] + (gj + 0.5) * hs + 1.3e-6, o[2] + (gk + 0.5) * hs + 1.7e-6
            a = ((z_[1] - z_[2]) * (py - y_[2]) + (y_[2] - y_[1]) * (pz - z_[2])) / den
            b = ((z_[2] - z_[0]) * (py - y_[2]) + (y_[0] - y_[2]) * (pz - z_[2])) / den
            m = (a >= 0) & (b >= 0) & (a + b <= 1)
            for jj, kk, xx in zip(gj[m], gk[m], (a * x_[0] + b * x_[1] + (1 - a - b) * x_[2])[m]):
                cols.setdefault((jj, kk), []).append(xx)
        xs = o[0] + (np.arange(ns[0]) + 0.5) * hs
        for (jj, kk), xl in cols.items():
            xl = np.sort(xl)
            for xa, xb in zip(xl[0::2], xl[1::2]): occ[(xs >= xa) & (xs < xb), jj, kk] ^= True
        f = occ.reshape(n[0], sub, n[1], sub, n[2], sub).mean((1, 3, 5))
        frac[names.index(k)] = np.maximum(frac[names.index(k)], f)
    tot = frac.sum(0); best = frac.argmax(0)
    mat = np.where(tot > 0.12, np.array([MAT_ID[PART_MAT[k]] for k in names])[best], -1)
    g = dict(origin=o, shape=tuple(n), H=H, names=names, part=np.where(mat >= 0, best, -1), frac=np.clip(tot, 0, 1), mat=mat)
    # densities: fixed for PA12 / filler / pad / oring, from the part mass for the cells and the board (with its parts)
    rho = np.zeros(tuple(n), np.float32)
    for i, k in enumerate(names):
        mm = (g['part'] == i); r = MATS[PART_MAT[k]][2]
        if r is None and part_mass is not None:
            vol = (g['frac'][mm]).sum() * H**3 / 1000.0
            r = part_mass[k] / vol
        rho[mm] = (r or 0) * g['frac'][mm]
    g['rho'] = rho
    return g

def first_board(A): return [i for i, (k, _, _) in enumerate(A) if k == 'board'][0]

def ke_hex(nu, h=H):
    """8-node brick stiffness for E = 1, cube of side h (2x2x2 Gauss)"""
    D = np.zeros((6, 6)); l = nu / ((1 + nu) * (1 - 2 * nu)); mu = 1 / (2 * (1 + nu))
    D[:3, :3] = l; D[np.arange(3), np.arange(3)] += 2 * mu; D[3:, 3:] = np.eye(3) * mu
    nodes = np.array([[i, j, k] for k in (0, 1) for j in (0, 1) for i in (0, 1)], float) * 2 - 1
    K = np.zeros((24, 24)); gp = np.array([-1, 1]) / np.sqrt(3)
    for xi in gp:
        for et in gp:
            for ze in gp:
                dN = np.array([nodes[:, 0] * (1 + nodes[:, 1] * et) * (1 + nodes[:, 2] * ze),
                               nodes[:, 1] * (1 + nodes[:, 0] * xi) * (1 + nodes[:, 2] * ze),
                               nodes[:, 2] * (1 + nodes[:, 0] * xi) * (1 + nodes[:, 1] * et)]) / 8 * (2 / h)
                B = np.zeros((6, 24))
                B[0, 0::3], B[1, 1::3], B[2, 2::3] = dN[0], dN[1], dN[2]
                B[3, 0::3], B[3, 1::3] = dN[1], dN[0]; B[4, 1::3], B[4, 2::3] = dN[2], dN[1]; B[5, 0::3], B[5, 2::3] = dN[2], dN[0]
                K += B.T @ D @ B * (h / 2)**3
    return K, D

def b_centre(h=H):
    nodes = np.array([[i, j, k] for k in (0, 1) for j in (0, 1) for i in (0, 1)], float) * 2 - 1
    dN = nodes.T / 8 * (2 / h)
    B = np.zeros((6, 24))
    B[0, 0::3], B[1, 1::3], B[2, 2::3] = dN[0], dN[1], dN[2]
    B[3, 0::3], B[3, 1::3] = dN[1], dN[0]; B[4, 1::3], B[4, 2::3] = dN[2], dN[1]; B[5, 0::3], B[5, 2::3] = dN[2], dN[0]
    return B

class Model:
    def __init__(self, g):
        self.g = g; n = np.array(g['shape']); H = g['H']
        el = np.argwhere(g['mat'] >= 0); self.el = el
        nn = n + 1; self.nn = nn
        off = np.array([[i, j, k] for k in (0, 1) for j in (0, 1) for i in (0, 1)])
        nid = ((el[:, None, :] + off[None]) * np.array([nn[1] * nn[2], nn[2], 1])).sum(-1)
        used, inv = np.unique(nid, return_inverse=True); self.used = used; self.conn = inv.reshape(nid.shape)
        self.nnode = len(used)
        ijk = np.stack(np.unravel_index(used, tuple(nn)), -1)
        self.X = g['origin'] + ijk * H
        mats = g['mat'][tuple(el.T)]; self.emat = mats
        self.E = np.array([list(MATS.values())[m][0] for m in mats]) * g['frac'][tuple(el.T)]
        self.rho = g['rho'][tuple(el.T)] * 1e-3              # g/mm3 -> kg... kept in g/cm3*1e-3 = g/mm3
        self.mass_g = self.rho.sum() * H**3                   # grams
        self.Ke = {}; self.D = {}
        for name, (E, nu, _) in MATS.items(): self.Ke[MAT_ID[name]], self.D[MAT_ID[name]] = ke_hex(nu, H)
        t = time.time()
        dof = (self.conn[:, :, None] * 3 + np.arange(3)).reshape(len(el), 24)
        self.dof = dof
        rows = np.repeat(dof, 24, axis=1).ravel(); cols = np.tile(dof, (1, 24)).ravel()
        vals = np.empty((len(el), 576))
        for m in np.unique(mats):
            s = mats == m; vals[s] = self.E[s, None] * self.Ke[m].ravel()[None]
        self.K = sp.csr_matrix((vals.ravel(), (rows.astype(np.int64), cols.astype(np.int64))), shape=(3 * self.nnode,) * 2)
        print(f'  FE: {len(el)} bricks, {self.nnode} nodes, mass {self.mass_g:.1f} g, assembled in {time.time() - t:.0f} s')

    def body_force(self, a_vec_g):
        """nodal forces (N) for a uniform acceleration a (in g, pack frame) applied as inertia (pushes toward +a)"""
        f = np.zeros((self.nnode, 3)); w = self.rho * self.g['H']**3 / 8 * 1e-3 * 9.81   # kg per node share * g
        for c in range(8): np.add.at(f, self.conn[:, c], w[:, None] * np.asarray(a_vec_g)[None])
        return f.ravel()

    def solve(self, f, springs):
        """springs: (node idx, k_normal N/mm, normal unit vector, k_tangential N/mm)"""
        idx, kn, nrm, kt = springs
        K = self.K.copy().tolil() if False else self.K.copy()
        r, c, v = [], [], []
        for i in range(3):
            for j in range(3):
                kij = kn * nrm[i] * nrm[j] + kt * ((i == j) - nrm[i] * nrm[j])
                r.append(3 * idx + i); c.append(3 * idx + j); v.append(np.full(len(idx), kij) if np.isscalar(kij) else kij)
        K = K + sp.csr_matrix((np.concatenate(v), (np.concatenate(r), np.concatenate(c))), shape=K.shape)
        B = np.zeros((3 * self.nnode, 6)); Xc = self.X - self.X.mean(0)
        B[0::3, 0] = 1; B[1::3, 1] = 1; B[2::3, 2] = 1
        B[0::3, 3], B[1::3, 3] = -Xc[:, 1], Xc[:, 0]; B[1::3, 4], B[2::3, 4] = -Xc[:, 2], Xc[:, 1]; B[0::3, 5], B[2::3, 5] = Xc[:, 2], -Xc[:, 0]
        t = time.time()
        ml = pyamg.smoothed_aggregation_solver(K, B=B, symmetry='hermitian', max_coarse=2000)
        res = []
        u = ml.solve(f, tol=1e-7, accel='cg', maxiter=400, residuals=res)
        print(f'  FE solve: {len(res)} its, rel res {res[-1] / res[0]:.1e}, {time.time() - t:.0f} s')
        return u.reshape(-1, 3)

    def stress(self, u):
        """element-centre stress (MPa) and von Mises"""
        B = b_centre(self.g['H']); ue = u[self.conn].reshape(len(self.el), 24)
        eps = ue @ B.T; sig = np.empty_like(eps)
        for m in np.unique(self.emat):
            s = self.emat == m; sig[s] = (eps[s] @ self.D[m].T) * self.E[s, None]
        sx, sy, sz, txy, tyz, txz = sig.T
        vm = np.sqrt(0.5 * ((sx - sy)**2 + (sy - sz)**2 + (sz - sx)**2) + 3 * (txy**2 + tyz**2 + txz**2))
        return sig, vm, eps
