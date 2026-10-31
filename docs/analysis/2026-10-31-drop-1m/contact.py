"""Floor contact for the 1 m drop study: for a drop direction d (unit vector in the pack frame, pointing at the floor),
cast rays from the floor up into the pack on a fine grid and record, per ray, the gap to the first surface, the part
it enters and that part's thickness along the ray. Force-crush curves then come from a Winkler (bed of springs) layer
per ray: each ray's first layer is crushed by (delta - gap) and pushes back with its material's stress-strain law."""
import numpy as np
OUTER = ('bumpt_slab', 'bumpt_band', 'bumpb_slab', 'bumpb_band', 'label', 'cup', 'cap', 'screw')
MAT = dict(bumpt_slab='gyroid20', bumpb_slab='gyroid20', bumpt_band='tpu', bumpb_band='tpu', label='pa12', cup='pa12',
           cap='pa12', screw='pa12')

def frame(d):
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    a = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
    e1 = np.cross(a, d); e1 /= np.linalg.norm(e1); e2 = np.cross(d, e1)
    return np.array([e1, e2, d])            # rows: u, v (floor plane), s (toward the floor)

def raycast(A, d, res=0.25, parts=OUTER):
    """returns dict(u, v grids, gap (mm, inf = no hit), part index into parts, thick (mm), s0 (lowest point along d))"""
    R = frame(d)
    T = {k: np.vstack([V for kk, V, _ in A if kk == k]) @ R.T for k in parts if any(kk == k for kk, _, _ in A)}
    allp = np.vstack([t.reshape(-1, 3) for t in T.values()])
    s0 = allp[:, 2].max()
    u0, v0 = allp[:, :2].min(0) - 1; u1, v1 = allp[:, :2].max(0) + 1
    nu, nv = int((u1 - u0) / res) + 1, int((v1 - v0) / res) + 1
    hits = {}                                 # part -> list of (pixel, s)
    for k, V in T.items():
        P_, S_ = [], []
        for tri in V:
            x, y, z = tri[:, 0], tri[:, 1], tri[:, 2]
            i0, i1 = int(np.floor((x.min() - u0) / res)), int(np.ceil((x.max() - u0) / res))
            j0, j1 = int(np.floor((y.min() - v0) / res)), int(np.ceil((y.max() - v0) / res))
            den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(den) < 1e-12: continue
            gi, gj = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1), indexing='ij')
            px, py = u0 + gi * res + 1e-7, v0 + gj * res + 2e-7
            a = ((y[1] - y[2]) * (px - x[2]) + (x[2] - x[1]) * (py - y[2])) / den
            b = ((y[2] - y[0]) * (px - x[2]) + (x[0] - x[2]) * (py - y[2])) / den
            m = (a >= 0) & (b >= 0) & (a + b <= 1)
            if not m.any(): continue
            P_.append((gi[m] * nv + gj[m])); S_.append(a[m] * z[0] + b[m] * z[1] + (1 - a[m] - b[m]) * z[2])
        if P_: hits[k] = (np.concatenate(P_), np.concatenate(S_))
    n = nu * nv
    gap = np.full(n, np.inf); part = np.full(n, -1); thick = np.zeros(n)
    names = list(T)
    for ip, k in enumerate(names):
        if k not in hits: continue
        pix, s = hits[k]
        o = np.lexsort((-s, pix)); pix, s = pix[o], s[o]
        first = np.r_[True, pix[1:] != pix[:-1]]
        idx = np.flatnonzero(first)
        cnt = np.diff(np.r_[idx, len(pix)])
        ok = cnt >= 2
        p_, s_in, s_out = pix[idx[ok]], s[idx[ok]], s[idx[ok] + 1]
        g = s0 - s_in
        better = g < gap[p_]
        gap[p_[better]] = g[better]; part[p_[better]] = ip; thick[p_[better]] = (s_in - s_out)[better]
    return dict(R=R, s0=s0, res=res, shape=(nu, nv), origin=(u0, v0), gap=gap.reshape(nu, nv), part=part.reshape(nu, nv),
                thick=thick.reshape(nu, nv), names=names)

# ---------------- materials: nominal compressive stress (MPa) vs strain ----------------
E_TPU = 40.0          # TPU 95A, impact-rate modulus (quasi-static ~26 MPa for FDM TPU 95A; rate stiffening ~1.5x)
CONF = 3.0            # apparent stiffening of a solid TPU band squeezed through its thickness (shape factor ~1.2-1.8)
E_PA12 = 1700.0       # MJF PA12
GYROID = {0.20: dict(E=2.0, pl=0.30), 0.10: dict(E=0.6, pl=0.10)}   # TPU gyroid: initial modulus, plateau stress (MPa)
GYROID[0.30] = dict(E=GYROID[0.20]['E'] * 1.5**2, pl=GYROID[0.20]['pl'] * 1.5**2)   # elastomer lattice ~ rho^2 (as sens.py)
GYROID[0.15] = dict(E=GYROID[0.10]['E'] * 1.5**2, pl=GYROID[0.10]['pl'] * 1.5**2)   # the cap pad since 2026-10-31
SCALE = dict(tpu=1.0, gyroid=1.0)     # sensitivity multipliers

def solid_tpu(eps):
    lam = np.clip(1 - eps, 0.05, 1)
    return SCALE['tpu'] * CONF * E_TPU / 3 * (1 / lam**2 - lam)     # neo-Hookean, uniaxial compression, nominal

def gyroid(eps, rho):
    g = GYROID[rho]; E, pl = g['E'] * SCALE['gyroid'], g['pl'] * SCALE['gyroid']; eD = 1 - 1.4 * rho
    s = pl * (1 - np.exp(-E * eps / pl)) + 0.3 * pl * eps / eD                  # elastic rise, gently climbing plateau
    dens = np.clip((eps - eD) / (1 - eD), 0, None)                              # cell walls in contact: the solid TPU left
    return s + solid_tpu(np.minimum(dens, 0.9)) * (dens > 0)                  # compacted: a solid TPU layer (1 - eD) t thick

def stress(mat, eps, thick):
    if mat == 'tpu': return solid_tpu(eps)
    if mat == 'gyroid20': return gyroid(eps, 0.20)
    if mat == 'gyroid10': return gyroid(eps, 0.10)
    if mat == 'gyroid30': return gyroid(eps, 0.30)
    return E_PA12 * eps                                                           # PA12 skin: through-thickness, local

def layer_pressure(rc, delta, t_pa=2.0):
    """pressure map (MPa) at crush delta (mm) and the total force (N)"""
    g, prt, th = rc['gap'], rc['part'], rc['thick']
    p = np.zeros_like(g)
    c = np.isfinite(g) & (delta > g)
    for ip, k in enumerate(rc['names']):
        m = c & (prt == ip)
        if not m.any(): continue
        mat = MAT[k]
        t = np.maximum(th[m], 0.3) if mat != 'pa12' else np.full(m.sum(), t_pa)
        p[m] = stress(mat, np.minimum((delta - g[m]) / t, 0.97 if mat != 'pa12' else 0.2), t)
    return p, p.sum() * rc['res']**2
