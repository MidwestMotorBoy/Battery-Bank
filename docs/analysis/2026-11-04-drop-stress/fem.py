"""Voxel finite elements for the contact drop model: a part (or a set of labelled sub-parts) voxelised on an H mm grid
by slicing the manifold solids, linear 8-node bricks (the 10-31 study's element), pyamg-preconditioned CG.
Loads are nodal forces (contact patches, inertia); supports are springs (floor footprint, or weak springs to take
the out-of-balance moment of a free part, since the drop model has no rotation)."""
import os, sys, time, numpy as np, scipy.sparse as sp, pyamg
from matplotlib.path import Path
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.normpath(os.path.join(HERE, '..', '2026-10-31-drop-1m')))
import fe as FE0                                       # ke_hex, b_centre

def voxelise(parts, H, pad=1.0):
    """parts: {label: Manifold}. Returns dict(origin, shape, H, lab (int grid, -1 empty), labels)"""
    labels = list(parts)
    bb = np.array([parts[k].bounding_box() for k in labels])
    lo = bb[:, :3].min(0) - pad; hi = bb[:, 3:].max(0) + pad
    n = np.ceil((hi - lo) / H).astype(int)
    xc = lo[0] + (np.arange(n[0]) + 0.5) * H; yc = lo[1] + (np.arange(n[1]) + 0.5) * H
    XY = np.stack(np.meshgrid(xc, yc, indexing='ij'), -1).reshape(-1, 2)
    lab = np.full(tuple(n), -1, np.int16)
    for li, k in enumerate(labels):
        m = parts[k]; b = m.bounding_box()
        k0 = max(0, int((b[2] - lo[2]) / H) - 1); k1 = min(n[2], int((b[5] - lo[2]) / H) + 2)
        for kz in range(k0, k1):
            z = lo[2] + (kz + 0.5) * H
            polys = m.slice(z).to_polygons()
            if not polys: continue
            inside = np.zeros(len(XY), bool)
            for p in polys:
                p = np.asarray(p)
                if len(p) < 3: continue
                pb = (XY[:, 0] >= p[:, 0].min()) & (XY[:, 0] <= p[:, 0].max()) & (XY[:, 1] >= p[:, 1].min()) & (XY[:, 1] <= p[:, 1].max())
                if pb.any(): inside[pb] ^= Path(p).contains_points(XY[pb])
            sl = lab[:, :, kz].reshape(-1)
            sl[inside & (sl < 0)] = li
            lab[:, :, kz] = sl.reshape(n[0], n[1])
    return dict(origin=lo, shape=tuple(n), H=H, lab=lab, labels=labels)

class Model:
    def __init__(self, g, E=1700.0, nu=0.38, rho=1.01):
        self.g = g; H = g['H']; n = np.array(g['shape'])
        el = np.argwhere(g['lab'] >= 0); self.el = el; self.elab = g['lab'][tuple(el.T)]
        nn = n + 1
        off = np.array([[i, j, k] for k in (0, 1) for j in (0, 1) for i in (0, 1)])
        nid = ((el[:, None, :] + off[None]) * np.array([nn[1] * nn[2], nn[2], 1])).sum(-1)
        used, inv = np.unique(nid, return_inverse=True); self.conn = inv.reshape(nid.shape); self.nnode = len(used)
        ijk = np.stack(np.unravel_index(used, tuple(nn)), -1); self.X = g['origin'] + ijk * H
        self.Xe = g['origin'] + (el + 0.5) * H
        self.E, self.nu, self.rho = E, nu, rho
        Ke, self.D = FE0.ke_hex(nu, H)
        dof = (self.conn[:, :, None] * 3 + np.arange(3)).reshape(len(el), 24).astype(np.int32)
        K = None; ke = (E * Ke).ravel()
        for i0 in range(0, len(el), 40000):                     # chunked: the full COO arrays would need ~5 GB at H 0.5
            dc = dof[i0:i0 + 40000]
            Kc = sp.csr_matrix((np.tile(ke, len(dc)), (np.repeat(dc, 24, axis=1).ravel(), np.tile(dc, (1, 24)).ravel())),
                               shape=(3 * self.nnode,) * 2)
            K = Kc if K is None else K + Kc
        self.K = K
        self.surf = self._surface_nodes()
        self.tree = cKDTree(self.X[self.surf])
        self.ml = None

    def _surface_nodes(self):
        """nodes of elements with an empty face neighbour"""
        lab = self.g['lab'] >= 0; n = lab.shape
        P = np.pad(lab, 1)
        e = self.el + 1
        nb = [P[e[:, 0] + dx, e[:, 1] + dy, e[:, 2] + dz] for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
        outer = ~np.all(nb, axis=0)
        return np.unique(self.conn[outer])

    def mass_g(self): return len(self.el) * self.g['H']**3 * self.rho / 1000

    def inertia(self, a_vec_g, labels=None):
        """nodal forces (N) of a uniform acceleration a (g, pushes the part toward +a), optionally only some labels"""
        f = np.zeros((self.nnode, 3)); w = self.rho * self.g['H']**3 / 8 * 1e-6 * 9.81
        sel = np.ones(len(self.el), bool) if labels is None else np.isin(self.elab, [self.g['labels'].index(l) for l in labels])
        for c in range(8): np.add.at(f, self.conn[sel, c], w * np.asarray(a_vec_g, float)[None])
        return f.ravel()

    def node_mass(self):
        """lumped nodal masses (kg)"""
        if getattr(self, '_mn', None) is None:
            mn = np.zeros(self.nnode); np.add.at(mn, self.conn.ravel(), self.rho * self.g['H']**3 / 8 * 1e-6); self._mn = mn
        return self._mn

    def relieve(self, f, about=None):
        """Inertia relief. The drop model has no rotation, so its loads leave a moment on the part; in the drop that moment
        spins the part up instead. Adds the d'Alembert loads of the rotational (and, for a free part, translational)
        acceleration that balance it: about=None for a free part (net force and moment about its centre of mass go to
        zero), about=c for a part held at a small floor patch around c (the moment about c goes to zero; the patch keeps
        the net force). Returns (f, alpha in rad/s^2, linear a in mm/s^2)."""
        mn = self.node_mass(); X = self.X; F = f.reshape(-1, 3)
        xg = (mn[:, None] * X).sum(0) / mn.sum(); a = np.zeros(3)
        if about is None:
            a = F.sum(0) / mn.sum() * 1e3                                    # N/kg = 1e3 mm/s2
            F = F - mn[:, None] * a[None] * 1e-3
            c = xg
        else: c = np.asarray(about, float)
        M = np.cross(X - c, F).sum(0)
        r, s = X - xg, X - c                                                 # J alpha = sum m s x (alpha x r)
        J = np.zeros((3, 3))
        for k in range(3):
            e = np.zeros(3); e[k] = 1.0
            J[:, k] = (mn[:, None] * np.cross(s, np.cross(e[None], r))).sum(0) * 1e-3     # N mm per (rad/s2) / 1e3
        al = np.linalg.solve(J, M)
        F = F - mn[:, None] * np.cross(al[None], r) * 1e-3
        return F.ravel(), al, a

    def patch_nodes(self, pts, r=None):
        """surface nodes within r (default 0.75 H) of the points (a contact overlap's vertices and face centres)"""
        r = 0.75 * self.g['H'] if r is None else r
        hits = self.tree.query_ball_point(pts, r)
        s = np.unique(np.concatenate([np.asarray(h, int) for h in hits])) if len(hits) else np.array([], int)
        if len(s) == 0:
            _, i = self.tree.query(pts.mean(0)); s = np.array([i])
        return self.surf[s]

    def patch_force(self, nodes, F_vec):
        f = np.zeros((self.nnode, 3)); np.add.at(f, nodes, np.asarray(F_vec, float)[None] / len(nodes)); return f.ravel()

    def solve(self, f, springs, tol=1e-7, reuse=True):
        """springs: list of (node idx array, k N/mm per node, unit normal or None for isotropic)"""
        r, c, v = [], [], []
        for idx, k, nrm in springs:
            idx = np.asarray(idx); k = np.broadcast_to(np.asarray(k, float), idx.shape)
            for i in range(3):
                for j in range(3):
                    kij = k * (nrm[i] * nrm[j] if nrm is not None else float(i == j))
                    if np.all(kij == 0): continue
                    r.append(3 * idx + i); c.append(3 * idx + j); v.append(kij)
        Ks = self.K + sp.csr_matrix((np.concatenate(v), (np.concatenate(r), np.concatenate(c))), shape=self.K.shape)
        key = springs                                       # held (not id()): a freed list's id can be reused
        if not reuse or self.ml is None or self.ml[0] is not key:
            B = np.zeros((3 * self.nnode, 6)); Xc = self.X - self.X.mean(0)
            B[0::3, 0] = 1; B[1::3, 1] = 1; B[2::3, 2] = 1
            B[0::3, 3], B[1::3, 3] = -Xc[:, 1], Xc[:, 0]; B[1::3, 4], B[2::3, 4] = -Xc[:, 2], Xc[:, 1]; B[0::3, 5], B[2::3, 5] = Xc[:, 2], -Xc[:, 0]
            self.ml = (key, pyamg.smoothed_aggregation_solver(Ks, B=B, symmetry='hermitian', max_coarse=1500, coarse_solver='splu'), Ks)
        ml = self.ml[1]
        res = []
        u = ml.solve(f, tol=tol, accel='cg', maxiter=600, residuals=res)
        return u.reshape(-1, 3), len(res), res[-1] / max(res[0], 1e-30)

    def stress(self, u):
        B = FE0.b_centre(self.g['H']); ue = u[self.conn].reshape(len(self.el), 24)
        sig = (ue @ B.T) @ self.D.T * self.E
        sx, sy, sz, txy, tyz, txz = sig.T
        vm = np.sqrt(0.5 * ((sx - sy)**2 + (sy - sz)**2 + (sz - sx)**2) + 3 * (txy**2 + tyz**2 + txz**2))
        return sig, vm

R_NEAR = 1.5     # mm: elements this close to a loaded patch or a floor support are the contact's bearing zone

def region_stats(M, env, near_nodes):
    """per label: p99 / p99.9 / max of the von Mises envelope, over all elements and over the elements away from the
    contact patches and supports ('far': the part's own bending / shear, not the local bearing under a contact)"""
    from scipy.spatial import cKDTree as KD
    nn = np.unique(np.concatenate([np.asarray(n, int) for n in near_nodes])) if near_nodes else np.array([], int)
    far = np.ones(len(M.el), bool)
    if len(nn): far = KD(M.X[nn]).query(M.Xe, distance_upper_bound=R_NEAR)[0] > R_NEAR
    out = {}
    for li, k in enumerate(M.g['labels']):
        sel = M.elab == li; s = env[sel]
        if len(s) == 0: continue
        imax = np.flatnonzero(sel)[int(s.argmax())]
        r = dict(p99=float(np.percentile(s, 99)), p999=float(np.percentile(s, 99.9)), max=float(s.max()), at=np.round(M.Xe[imax], 1).tolist())
        sf = env[sel & far]
        if len(sf) > 20:
            jf = np.flatnonzero(sel & far)[int(sf.argmax())]
            r.update(p999_far=float(np.percentile(sf, 99.9)), max_far=float(sf.max()), at_far=np.round(M.Xe[jf], 1).tolist())
        out[k] = r
    return out

def overlap_points(a, b, d, delta, extra=0.0):
    """points on the contact overlap of a moved delta (+ extra, so a just-touching pair still gives a patch) along d into b"""
    o = a.translate(tuple(np.asarray(d) * (delta + extra))) ^ b
    if o.is_empty(): return None
    M = o.to_mesh(); V = np.asarray(M.vert_properties)[:, :3]; T = np.asarray(M.tri_verts)
    return np.vstack([V, V[T].mean(1)])
