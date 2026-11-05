"""Shell (cup + cap) finite elements for one pose: (1) the compliance of every contact patch on the cup / cap, held at
the floor footprint, which goes back into the drop model as a series spring per contact, and (2) the stress at the
peak, from all the contact forces at that instant plus the shell's own inertia.
Run: python fe_shell.py H pose [pose ...] -> cache/shellc_<pose>.json (compliance), out/shell_<pose>.json (stress)"""
import os, sys, json, pickle, time, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'cache'); OUT = os.path.join(HERE, 'out')
import bodies, fem, dyn
sys.path.append(os.path.normpath(os.path.join(HERE, '..', '2026-10-31-drop-1m')))
import contact as FC
SHELL_PARTS = ('cup_walls', 'cradles', 'lands', 'lips', 'cap', 'ot_posts', 'feet')
K_FLOOR = 2e4                     # N/mm per footprint node (the floor through the crushed bumper: stiff next to the cup)
F_MIN = 20.0                      # N: contacts below this peak are left out
_G = {}

def geometry():
    if not _G:
        B, sub, m, prm, A = bodies.build(); _G.update(B=B, sub=sub, CP=bodies.contact_parts(B, sub), prm=prm)
    return _G

def build_model(H):
    g = geometry(); sub = g['sub']
    t = time.time(); vg = fem.voxelise({k: sub[k] for k in SHELL_PARTS}, H)
    M = fem.Model(vg)
    print(f'  shell FE H {H}: {len(M.el)} bricks, {M.nnode} nodes, {M.mass_g():.1f} g PA12 ({time.time() - t:.0f} s)', flush=True)
    return M

TILT = 1.0                        # mm: a bumper whose face is within this of the first touch carries too (see _rocked)
K_GAP_TPU = 0.05                  # fraction of K_FLOOR for a skin node that reaches the floor through a bumper

class Floor(list):
    """the footprint springs (a list for Model.solve) + the one-sided floor stops of the rest of the outer skin"""

def _rocked(rc):
    """A flat landing on bumpers whose faces differ by a few tenths (the cap-end bumper is 0.55 mm proud of the port-end
    one on the board face) rocks onto the second one within the same impact; the drop model has no rotation, so the FE
    lets every bumper within TILT of the first touch carry, as if both landed together."""
    g = rc['gap'].copy(); prt = rc['part']
    for grp in {k[:5] for k in rc['names'] if k.startswith('bump')}:
        m = np.isfinite(g) & np.isin(prt, [i for i, k in enumerate(rc['names']) if k.startswith(grp)])
        if m.any() and 0 < g[m].min() <= TILT: g[m] -= g[m].min()
    return dict(rc, gap=g)

def floor_springs(M, T, crush):
    """springs on the outermost shell node of each H x H column under the floor footprint at the deepest crush, and
    one-sided stops (gap = the column's standoff - crush) for every other outer-skin node within 3 mm of the floor"""
    rc = _rocked(T['rc']); d = np.asarray(T['d'], float)
    p, _ = FC.layer_pressure(rc, crush)
    R = rc['R']; u0, v0 = rc['origin']; res = rc['res']; H = M.g['H']
    Q = M.X[M.surf] @ R.T
    bu = np.floor(Q[:, 0] / H).astype(int); bv = np.floor(Q[:, 1] / H).astype(int)
    key = bu * 100003 + bv
    o = np.lexsort((-Q[:, 2], key)); first = np.r_[True, key[o][1:] != key[o][:-1]]; sel = o[first]
    front = {k: i for k, i in zip(key[sel], sel)}
    nu_, nv_ = rc['gap'].shape; IU, IV = np.meshgrid(np.arange(nu_), np.arange(nv_), indexing='ij')
    KK = np.floor((u0 + IU * res) / H).astype(int) * 100003 + np.floor((v0 + IV * res) / H).astype(int)
    nodes = {}
    for k_, w in zip(KK[p > 0], p[p > 0]):
        i = front.get(k_)
        if i is not None: nodes[i] = nodes.get(i, 0.0) + w
    idx = np.array(list(nodes)); w = np.array([nodes[i] for i in idx])
    # keep only nodes near the front along d (the bumper pushes the cup's outer skin, not something deep inside)
    s = Q[idx, 2]; keep = s >= s.max() - 6.0
    idx, w = idx[keep], w[keep]
    k = K_FLOOR * w / w.mean()
    F = Floor([(M.surf[idx], k, d), (M.surf[idx], 0.2 * k, None)])          # normal + weak tangential (friction)
    F.d, F.foot = d, M.surf[idx]
    # the rest of the skin: standoff per column (min over its rays), stiff through the label, soft through a bumper
    fin = np.isfinite(rc['gap']) & (p <= 0)
    gk = {}
    for k_, g_, pt in zip(KK[fin], rc['gap'][fin], rc['part'][fin]):
        if k_ not in gk or g_ < gk[k_][0]: gk[k_] = (g_, pt)
    foot = set(idx.tolist()); gi, gg, kg = [], [], []
    for k_, (g_, pt) in gk.items():
        i = front.get(k_)
        if i is None or i in foot or g_ - crush > 3.0: continue
        gi.append(i); gg.append(max(g_ - crush, 0.0))
        kg.append(K_FLOOR * (K_GAP_TPU if rc['names'][pt].startswith('bump') else 1.0))
    F.gidx = M.surf[np.array(gi, int)]; F.gap = np.array(gg); F.gk = np.array(kg)
    return F

def solve_floor(M, f, floor, maxit=14, tol=1e-7):
    """Model.solve with the one-sided skin stops: an active set on the skin nodes that reach the floor. The footprint-only
    AMG hierarchy preconditions CG on the system with the stops added (they only add to the diagonal blocks)."""
    import scipy.sparse as sp, scipy.sparse.linalg as sla
    d = floor.d; idx, g, k = floor.gidx, floor.gap, floor.gk
    u, its, rr = M.solve(f, floor)                                   # builds / reuses the hierarchy for this floor
    ml, Ks = M.ml[1], M.ml[2]; P = ml.aspreconditioner(cycle='V')
    act = np.zeros(len(idx), bool); nit = 1
    for it in range(maxit):
        pen = (u[idx] @ d) > g
        new = (act | pen) if it < maxit // 2 else pen                # grow first, then let go of the stops in tension
        if np.array_equal(new, act) and it > 0: break
        act = new
        if not act.any(): break
        ii = idx[act]; kk = k[act]
        r, c, v = [], [], []
        for a in range(3):
            for b in range(3): r.append(3 * ii + a); c.append(3 * ii + b); v.append(kk * d[a] * d[b])
        K2 = Ks + sp.csr_matrix((np.concatenate(v), (np.concatenate(r), np.concatenate(c))), shape=Ks.shape)
        f2 = f.reshape(-1, 3).copy(); np.add.at(f2, ii, (kk * g[act])[:, None] * d[None]); f2 = f2.ravel()
        n_ = [0]
        def cb(x): n_[0] += 1
        x, flag = sla.cg(K2, f2, x0=u.ravel(), rtol=tol, maxiter=800, M=P, callback=cb)
        u = x.reshape(-1, 3); its = n_[0]; nit += 1
        rr = float(np.linalg.norm(K2 @ x - f2) / max(np.linalg.norm(f2), 1e-30))
    return u, (its, rr, int(act.sum()), nit)

def shell_contacts(T, S):
    """the drop model's contacts that touch the shell, with their peak force"""
    pk = {(c['a'], c['b'], c['sense']): c['peak_N'] for c in S['contacts']}
    out = []
    for (a, b), tb in T['pairs'].items():
        if not b.startswith('shell/') or b == 'shell/pad': continue
        for sense in ('+', '-'):
            if tb[sense] is None or pk.get((a, b, sense), 0) < F_MIN: continue
            out.append((a, b, sense, pk[(a, b, sense)]))
    return out

def patch(M, a, b, sense, delta, d):
    """nodes of the shell part b where body a meets it at relative motion delta (sense '+': a moved +d into b)"""
    CP = geometry()['CP']; A, Bm = CP[a][1], CP[b][1]
    dd = np.asarray(d, float) * (1 if sense == '+' else -1)
    pts = fem.overlap_points(A, Bm, dd, delta, extra=0.0)
    if pts is None: pts = fem.overlap_points(A, Bm, dd, delta, extra=0.02)
    if pts is None: return None
    return M.patch_nodes(pts)

def load_case(M, T, R, sc, i, floor=None):
    """nodal forces at instant i: the shell's inertia + every shell contact force on its patch, with inertia relief of
    the moment about the floor footprint (fem.Model.relieve) when the floor is given"""
    d = np.asarray(T['d'], float); names = list(R['names'])
    f = M.inertia(-R['a'][i, 0] * d); loads, pt = [], {}
    for a, b, s, _ in sc:
        F = R['F'][i, names.index(f'{a}|{b}|{s}')]
        if F < 1.0: continue
        ia = dyn.BODIES.index(dyn.body_of(a))
        delta = (1 if s == '+' else -1) * (R['x'][i, ia] - R['x'][i, 0])
        nodes = patch(M, a, b, s, max(delta, 0.0), d)
        if nodes is None: continue
        f += M.patch_force(nodes, F * d * (1 if s == '+' else -1)); loads.append((a, b, s, round(float(F), 1))); pt[(a, b, s)] = (nodes, F)
    if floor is not None:
        kf = np.broadcast_to(np.asarray(floor[0][1], float), floor.foot.shape)          # the footprint's resultant point
        f, al, _ = M.relieve(f, about=(M.X[floor.foot] * kf[:, None]).sum(0) / kf.sum())
        pt['_alpha'] = al
    return f, loads, pt

def compliance(M, T, S, floor):
    """Secant compliance of every contact patch (mm/N): at the instant of that contact's peak in the run so far, all the
    shell's loads together (so the walls meet the floor where they would), the patch's mean push displacement relative
    to the footprint over its own force."""
    d = np.asarray(T['d'], float); out = {}
    R = np.load(os.path.join(CACHE, f"dyn_{T['pose']}.npz")); names = list(R['names'])
    sc = shell_contacts(T, S); by_i = {}
    for a, b, s, Fpk in sc: by_i.setdefault(int(R['F'][:, names.index(f'{a}|{b}|{s}')].argmax()), []).append((a, b, s, Fpk))
    for i, cs in sorted(by_i.items()):
        f, loads, pt = load_case(M, T, R, sc, i, floor)
        u, (its, rr, nact, nit) = solve_floor(M, f, floor)
        ref = float((u[floor.foot] @ d).mean())
        for a, b, s, Fpk in cs:
            if (a, b, s) not in pt: continue
            nodes, F = pt[(a, b, s)]; push = d * (1 if s == '+' else -1)
            c = max(float((u[nodes] @ push).mean() - ref * (push @ d)) / F, 2e-6)
            out[f'{a}|{b}|{s}'] = dict(c_mm_per_N=c, k_N_per_mm=1 / c, nodes=len(nodes), peak_N=Fpk, at_N=round(float(F), 1),
                                       skin_on_floor=nact)
            print(f'    {a:16s} {s} {b:18s} k {1 / c:9.0f} N/mm at {F:6.0f} N ({len(nodes)} nodes, {nact} skin nodes on the floor, {nit} sets)', flush=True)
    return out

REGIONS = SHELL_PARTS
def stress(M, T, S, floor, tag=''):
    """von Mises at the instants of the largest total shell contact force and of the largest single shell contact"""
    d = np.asarray(T['d'], float); pose = T['pose']
    R = np.load(os.path.join(CACHE, f'dyn_{pose}{tag}.npz')); names = list(R['names'])
    sc = shell_contacts(T, S)
    cols = [names.index(f'{a}|{b}|{s}') for a, b, s, _ in sc]
    tot = R['F'][:, cols].sum(1); t_idx = {int(tot.argmax())}
    t_idx.add(int(R['F'][:, cols[int(np.argmax([R['F'][:, j].max() for j in cols]))]].argmax()))
    env = np.zeros(len(M.el)); snaps = []; near = [floor.foot]
    for i in sorted(t_idx):
        f, loads, pt = load_case(M, T, R, sc, i, floor)
        u, (its, rr, nact, nit) = solve_floor(M, f, floor)
        sig, vm = M.stress(u); env = np.maximum(env, vm)
        near.extend([v[0] for k, v in pt.items() if k != '_alpha'])
        snaps.append(dict(t_ms=round(float(R['t'][i] * 1e3), 4), loads=loads, its=its, skin_on_floor=nact,
                          spin_rad_s2=np.round(pt['_alpha'], 0).tolist(),
                          max_push_mm=round(float((u[M.surf] @ d).max() - (u[floor.foot] @ d).mean()), 3)))
    out = dict(pose=pose, H=M.g['H'], snapshots=snaps, regions=fem.region_stats(M, env, near))
    np.save(os.path.join(CACHE, f'shell_vm_{pose}{tag}.npy'), env.astype(np.float32))
    return out

def main(H, todo):
    M = build_model(H)
    np.savez_compressed(os.path.join(CACHE, f'shell_grid_H{H}.npz'), Xe=M.Xe, elab=M.elab, labels=np.array(M.g['labels']))
    for pose in todo:
        t0 = time.time(); T = dyn.load(pose)
        S = json.load(open(os.path.join(OUT, f'dyn_{pose}.json')))
        springs = floor_springs(M, T, S['crush_mm'])
        print(f'{pose}: {len(springs[0][0])} floor nodes', flush=True)
        C = compliance(M, T, S, springs)
        json.dump(C, open(os.path.join(CACHE, f'shellc_{pose}.json'), 'w'), indent=1)
        print(f'  {pose} compliance done ({time.time() - t0:.0f} s)', flush=True)

if __name__ == '__main__':
    H = float(sys.argv[1]); main(H, sys.argv[2:] or dyn.poses.ORDER)
