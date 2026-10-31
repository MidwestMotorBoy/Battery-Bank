"""1 m drop of the Monolith pack onto concrete: flat on the port end (top), flat on the cap end (bottom), flat on the
board face, flat on a narrow side, and on a corner at each end with the centre of mass straight over the corner.
Two masses: the shell (cup, cap, bumpers, label: the parts that meet the floor) and the core (cells, carrier, board,
everything inside), joined by the structure's stiffness from the voxel FE model (fe.py). The floor pushes on the shell
through contact.py's bed of springs (TPU gyroid slabs, solid TPU bands, PA12 where it touches).
Run: python drop.py -> out/drop.json (+ cache/) ; figures: python figs.py"""
import os, sys, json, time, numpy as np
import geom, contact as C, fe
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out')
H_DROP, G = 1.0, 9.81
V0 = np.sqrt(2 * G * H_DROP)                    # 4.43 m/s at impact
SHELL = ('cup', 'cap', 'label', 'bumpb', 'bumpt', 'screw', 'oring')
A, MASS, PRM = geom.load()
C.MAT['bumpt_slab'] = C.MAT['bumpb_slab'] = f"gyroid{round(PRM.get('SLAB_FILL', 0.2) * 100)}"   # the slabs as built in the model
M_ALL = sum(MASS.values()) / 1000; M_SHELL = sum(MASS[k] for k in SHELL) / 1000; M_CORE = M_ALL - M_SHELL

def cg():
    num = np.zeros(3); den = 0.0
    for k, V, _ in A:
        if k.startswith('board') and k != 'board': continue
        c = V.reshape(-1, 3).mean(0); w = MASS.get(k.split('_')[0], 0) / max(1, sum(1 for kk, _, _ in A if kk.split('_')[0] == k.split('_')[0]))
        num += w * c; den += w
    return num / den
CG = cg()
OUTER_PTS = np.vstack([V.reshape(-1, 3) for k, V, _ in A if k in C.OUTER])

def corner_dir(sx, sy, sz):
    """drop direction with the CG straight above the corner (the outer point that is lowest along it)"""
    d = np.array([sx, sy, sz], float)
    for _ in range(50):
        p = OUTER_PTS[np.argmax(OUTER_PTS @ (d / np.linalg.norm(d)))]
        dn = p - CG
        if np.linalg.norm(dn / np.linalg.norm(dn) - d / np.linalg.norm(d)) < 1e-6: break
        d = dn
    return d / np.linalg.norm(d), p

CASES = {
    'top':           dict(title='Flat on the port end (top bumper)', d=(0, 0, 1)),
    'bottom':        dict(title='Flat on the cap end (bottom bumper)', d=(0, 0, -1)),
    'board':         dict(title='Flat on the board face (+x)', d=(1, 0, 0)),
    'side':          dict(title='Flat on a narrow side (USB1 side, +y)', d=(0, 1, 0)),
    'corner_top':    dict(title='Corner, port end, board side (CG over the corner)', corner=(1, 1, 1)),
    'corner_bottom': dict(title='Corner, cap end, board side (CG over the corner)', corner=(1, 1, -1)),
}

def force_curve(rc, dmax=8.0, step=0.005):
    dl = np.arange(0, dmax + step, step); F = np.array([C.layer_pressure(rc, x)[1] for x in dl])
    return dl, F

def pad_curve():
    """bottom drop only: the core sits on the 10 % gyroid TPU pad on the cap, then the overtravel posts (0.6 mm gap)
    land on the carrier frame. Pad: its area at the frame, PAD thickness from the mesh."""
    V = [V for k, V, _ in A if k == 'pad'][0].reshape(-1, 3)
    t_pad = V[:, 2].max() - V[:, 2].min(); area = 0.55 * (np.ptp(V[:, 0]) * np.ptp(V[:, 1]))     # pocketed pad
    pre = 0.0                                                    # drawn as installed (pre-squeezed by PAD_PROUD)
    k_post = 4 * fe.MATS['pa12'][0] * np.pi * 1.5**2 / 6.0      # four r 1.5 PA12 posts ~6 mm long, N/mm
    def F(x_mm):
        x = np.maximum(x_mm, 0)
        return C.gyroid(np.minimum(x / t_pad, 0.97), 0.10) * area + k_post * np.maximum(x - 0.6, 0)
    return F, dict(t_pad=float(t_pad), area=float(area), k_post=float(k_post))

def simulate(dl, Fc, k_sc, eta=0.35, F_sc=None, t_end=6e-3, dt=1e-7, zeta=0.03):
    """shell (x_s) and core (x_c), m, positive toward the floor. Contact unloads at eta x the loading force
    (TPU hysteresis). k_sc N/m linear (or F_sc(x_mm) N, compression only, for the pad)."""
    xs = xc = 0.0; vs = vc = V0; out = []; xmax = 0.0; t = 0.0
    c_sc = 2 * zeta * np.sqrt((k_sc or 1e6) * M_CORE)
    while t < t_end:
        dmm = xs * 1e3
        if dmm > 0:
            fl = np.interp(dmm, dl, Fc)
            fc = fl if vs >= 0 and dmm >= xmax * 1e3 - 1e-9 else fl * eta
            xmax = max(xmax, xs)
        else: fc = 0.0
        rel = xc - xs
        if F_sc is not None: fsc = F_sc(rel * 1e3) if rel > 0 else 2e6 * rel
        else: fsc = k_sc * rel
        fsc += c_sc * (vc - vs)
        a_s = (-fc + fsc) / M_SHELL + 0.0; a_c = -fsc / M_CORE
        vs += a_s * dt; vc += a_c * dt; xs += vs * dt; xc += vc * dt; t += dt
        if len(out) == 0 or t - out[-1][0] >= 2e-6: out.append((t, xs, xc, vs, vc, fc, fsc, a_s / G, a_c / G))
        if t > 2e-4 and xs < -0.5e-3 and xc < -0.5e-3: break
    return np.array(out)

def run():
    os.makedirs(OUT, exist_ok=True)
    g = fe.voxelise(A, part_mass=MASS); M = fe.Model(g)
    res = {'v0': V0, 'm_all_g': M_ALL * 1e3, 'm_shell_g': M_SHELL * 1e3, 'm_core_g': M_CORE * 1e3, 'cg': CG.tolist(), 'cases': {}}
    for name, cs in CASES.items():
        t0 = time.time()
        if 'corner' in cs: d, p = corner_dir(*cs['corner']); cs['d'] = d
        d = np.asarray(cs['d'], float); d /= np.linalg.norm(d)
        rc = C.raycast(A, d)
        dl, Fc = force_curve(rc)
        # structure: FE with the footprint (first ~1.5 mm of contact) held by stiff springs, 1 g toward the floor
        sp, fp = springs_for(M, rc, d, delta=footprint_delta(dl, Fc))
        u = M.solve(M.body_force(d), sp)
        core = np.isin(M.emat, [fe.MAT_ID['cell'], fe.MAT_ID['fr4']])
        uc = (u[M.conn[core]].mean(1) @ d * M.rho[core]).sum() / M.rho[core].sum()   # core mean motion toward the floor, mm
        k_sc = M_ALL * G / (uc * 1e-3)
        if name == 'bottom':
            Fp, pinfo = pad_curve(); tr = simulate(dl, Fc, None, F_sc=Fp)
        else: pinfo = None; tr = simulate(dl, Fc, k_sc)
        i_pk = np.argmax(tr[:, 5]); a_shell = np.abs(tr[:, 7]).max()
        a_core = np.abs(tr[:, 8]).max()
        dmax = tr[:, 1].max() * 1e3
        p_pk, F_pk = C.layer_pressure(rc, dmax)
        np.savez_compressed(os.path.join(HERE, 'cache', f'{name}.npz'), tr=tr, dl=dl, Fc=Fc, p_pk=p_pk, gap=rc['gap'], part=rc['part'],
                            thick=rc['thick'], R=rc['R'], origin=rc['origin'], res=rc['res'], u1g=u, names=np.array(rc['names']))
        pulse = tr[tr[:, 5] > 0.05 * tr[:, 5].max(), 0]
        reb = tr[-1, 3] if tr[-1, 3] < 0 else 0.0
        r = dict(title=cs['title'], d=d.tolist(), k_struct_N_per_mm=k_sc / 1e3, crush_mm=dmax, F_peak_N=float(tr[:, 5].max()),
                 g_shell=a_shell, g_core=a_core, pulse_ms=float((pulse.max() - pulse.min()) * 1e3) if len(pulse) else 0,
                 t_peak_ms=float(tr[i_pk, 0] * 1e3), rebound_m_s=float(-reb), contact_area_mm2=float((p_pk > 0).sum() * rc['res']**2),
                 p_max_MPa=float(p_pk.max()), parts_in_contact={n: float(((rc['part'] == i) & (p_pk > 0)).sum() * rc['res']**2)
                                                                for i, n in enumerate(rc['names']) if ((rc['part'] == i) & (p_pk > 0)).any()},
                 u_core_1g_um=uc * 1e3, pad=pinfo)
        res['cases'][name] = r
        print(f"{name:14s} crush {dmax:5.2f} mm  F {r['F_peak_N']:7.0f} N  shell {a_shell:6.0f} g  core {a_core:6.0f} g  "
              f"pulse {r['pulse_ms']:.2f} ms  k_struct {k_sc/1e3:6.0f} N/mm  ({time.time() - t0:.0f} s)", flush=True)
    json.dump(res, open(os.path.join(OUT, 'drop.json'), 'w'), indent=1)
    return res, M

def footprint_delta(dl, Fc):
    """crush at which the floor carries the full static-equivalent load: used only to pick the FE footprint"""
    E = np.concatenate([[0], np.cumsum(0.5 * (Fc[1:] + Fc[:-1]) * np.diff(dl) * 1e-3)])
    return float(np.interp(0.5 * M_ALL * V0**2, E, dl))

def front_nodes(M, R):
    """the outermost FE node in each H x H column along the drop direction"""
    Q = M.X @ R.T; H = M.g['H']
    bu = np.floor(Q[:, 0] / H).astype(int); bv = np.floor(Q[:, 1] / H).astype(int)
    key = (bu - bu.min()) * 100000 + (bv - bv.min())
    o = np.lexsort((-Q[:, 2], key)); first = np.r_[True, key[o][1:] != key[o][:-1]]
    sel = o[first]
    return sel, Q, (bu.min(), bv.min())

def springs_for(M, rc, d, delta, k_rigid=2e4, p=None):
    """springs on the shell's outer FE nodes under the footprint: stiff (k_rigid N/mm per mm2, i.e. the floor through
    a crushed layer) where the layer is in contact at `delta`, or proportional to the pressure map p if given"""
    R = rc['R']; sel, Q, (b0u, b0v) = front_nodes(M, R)
    shell_mat = np.zeros(M.nnode, bool)
    shell_nodes = np.unique(M.conn[np.isin(M.g['part'][tuple(M.el.T)], [M.g['names'].index(k) for k in ('cup', 'cap')])])
    shell_mat[shell_nodes] = True
    sel = sel[shell_mat[sel]]
    if p is None: w = (rc['gap'] < max(delta, 1.0)).astype(float) * k_rigid       # everything within 1 mm of the floor at least
    else: w = p
    nu, nv = rc['shape']; u0, v0 = rc['origin']; res = rc['res']
    iu, iv = np.meshgrid(np.arange(nu), np.arange(nv), indexing='ij')
    pu, pv = u0 + iu * res, v0 + iv * res
    H = M.g['H']
    bu = np.floor(pu / H).astype(int) - b0u; bv = np.floor(pv / H).astype(int) - b0v
    nkey = {}
    for n in sel: nkey[(int(np.floor(Q[n, 0] / H)) - b0u, int(np.floor(Q[n, 1] / H)) - b0v)] = n
    acc = {}
    m = w > 0
    for a, b, ww in zip(bu[m], bv[m], w[m]):
        n = nkey.get((a, b))
        if n is None:
            for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                n = nkey.get((a + da, b + db))
                if n is not None: break
        if n is None: continue
        acc[n] = acc.get(n, 0.0) + ww * res**2
    idx = np.array(list(acc)); kn = np.array([acc[i] for i in idx])
    return (idx, kn, d, 0.5 * kn), dict(nodes=idx, k=kn)          # tangential: floor friction

if __name__ == '__main__': run()
