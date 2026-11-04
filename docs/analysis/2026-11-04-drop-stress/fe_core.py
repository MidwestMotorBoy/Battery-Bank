"""Carrier and rail-block finite elements for one pose. (1) Compliance of the carrier where it pushes on the cup / cap
(held where the cells bear on it at that instant), which goes back into the drop model with the shell's. (2) Stress at
the instant of the largest total contact force on the part: every contact force at that instant on its patch, the
part's own inertia, and weak springs over the surface for the moment the no-rotation drop model leaves out.
Run: python fe_core.py compliance|stress H pose [pose ...]"""
import os, sys, json, time, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'cache'); OUT = os.path.join(HERE, 'out')
import bodies, fem, dyn
from fe_shell import geometry, F_MIN
K_HOLD = 2e4; K_WEAK = 2.0                      # N/mm per node: holding patches; weak surface springs

PARTS = {'carrier': ('carrier/frames', 'carrier/webs'), **{r: (f'{r}/ends', f'{r}/posts', f'{r}/blocks') for r in bodies.RAILS}}

def build_model(part, H):
    CP = geometry()['CP']; t = time.time()
    vg = fem.voxelise({k: CP[k][1] for k in PARTS[part]}, H); M = fem.Model(vg)
    print(f'  {part} FE H {H}: {len(M.el)} bricks, {M.nnode} nodes, {M.mass_g():.2f} g ({time.time() - t:.0f} s)', flush=True)
    return M

def part_contacts(T, S, part):
    """contacts touching this part: (a, b, sense, peak, side) with side +1 if the part is a (pushed back), -1 if b"""
    pk = {(c['a'], c['b'], c['sense']): c['peak_N'] for c in S['contacts']}; out = []
    for (a, b), tb in T['pairs'].items():
        for sense in ('+', '-'):
            if tb[sense] is None or pk.get((a, b, sense), 0) < F_MIN: continue
            if dyn.body_of(a) == part: out.append((a, b, sense, pk[(a, b, sense)], +1))
            elif dyn.body_of(b) == part: out.append((a, b, sense, pk[(a, b, sense)], -1))
    return out

def patch(M, a, b, sense, delta, d, part_is_a):
    CP = geometry()['CP']; dd = np.asarray(d, float) * (1 if sense == '+' else -1)
    pts = fem.overlap_points(CP[a][1], CP[b][1], dd, delta)
    if pts is None: pts = fem.overlap_points(CP[a][1], CP[b][1], dd, delta, extra=0.02)
    if pts is None: return None
    if part_is_a: pts = pts - dd * delta                    # the overlap sits where b is; part a is back by delta
    return M.patch_nodes(pts)

def deltas(R, i, a, b, sense):
    ia, ib = dyn.BODIES.index(dyn.body_of(a)), dyn.BODIES.index(dyn.body_of(b))
    return max((1 if sense == '+' else -1) * (R['x'][i, ia] - R['x'][i, ib]), 0.0)

def compliance(M, T, S, part='carrier'):
    """carrier patches on the shell: 1 N there, the carrier held at its cell patches at the same instant"""
    d = np.asarray(T['d'], float); pose = T['pose']
    R = np.load(os.path.join(CACHE, f'dyn_{pose}.npz')); names = list(R['names'])
    cs = part_contacts(T, S, part); out = {}
    for a, b, s, Fpk, side in cs:
        if not b.startswith('shell/') or b == 'shell/pad': continue
        j = names.index(f'{a}|{b}|{s}'); i = int(R['F'][:, j].argmax())
        nodes = patch(M, a, b, s, deltas(R, i, a, b, s), d, True)
        if nodes is None: continue
        hold = []
        for a2, b2, s2, F2, side2 in cs:
            if b2.startswith('shell/'): continue
            j2 = names.index(f'{a2}|{b2}|{s2}')
            if R['F'][i, j2] < 0.05 * Fpk: continue
            n2 = patch(M, a2, b2, s2, deltas(R, i, a2, b2, s2), d, side2 > 0)
            if n2 is not None: hold.append(n2)
        if not hold: continue
        hold = np.unique(np.concatenate(hold))
        springs = [(hold, K_HOLD, d), (hold, 0.1 * K_HOLD, None)]
        push = -d * (1 if s == '+' else -1)                # the shell pushes back on the carrier
        u, its, rr = M.solve(M.patch_force(nodes, push), springs, reuse=False)
        c = float((u[nodes] @ push).mean() - (u[hold] @ push).mean())
        out[f'{a}|{b}|{s}'] = dict(c_mm_per_N=c, k_N_per_mm=1 / max(c, 1e-9), nodes=len(nodes), hold=len(hold), peak_N=Fpk)
        print(f'    {a:16s} {s} {b:18s} k {1 / max(c, 1e-9):9.0f} N/mm  ({len(nodes)} nodes, held on {len(hold)}, {its} its)', flush=True)
    return out

def stress(M, T, S, part, tag=''):
    d = np.asarray(T['d'], float); pose = T['pose']
    R = np.load(os.path.join(CACHE, f'dyn_{pose}{tag}.npz')); names = list(R['names'])
    cs = part_contacts(T, S, part); cols = [names.index(f'{a}|{b}|{s}') for a, b, s, _, _ in cs]
    if not cs: return None
    tot = R['F'][:, cols].sum(1); idx = {int(tot.argmax()), int(R['F'][:, cols[int(np.argmax([R['F'][:, j].max() for j in cols]))]].argmax())}
    env = np.zeros(len(M.el)); snaps = []
    weak = [(M.surf, K_WEAK, None)]
    ip = dyn.BODIES.index(part)
    for i in sorted(idx):
        f = M.inertia(-R['a'][i, ip] * d); loads = []
        for (a, b, s, _, side), j in zip(cs, cols):
            F = R['F'][i, j]
            if F < 1.0: continue
            nodes = patch(M, a, b, s, deltas(R, i, a, b, s), d, side > 0)
            if nodes is None: continue
            f += M.patch_force(nodes, -side * F * d * (1 if s == '+' else -1)); loads.append((a, b, s, round(float(F), 1)))
        u, its, rr = M.solve(f, weak)
        sig, vm = M.stress(u); env = np.maximum(env, vm)
        snaps.append(dict(t_ms=round(float(R['t'][i] * 1e3), 4), loads=loads, its=its, rel_res=float(rr)))
    out = dict(pose=pose, part=part, H=M.g['H'], snapshots=snaps, regions={})
    for li, k in enumerate(M.g['labels']):
        s_ = env[M.elab == li]
        if len(s_) == 0: continue
        imax = np.flatnonzero(M.elab == li)[int(s_.argmax())]
        out['regions'][k] = dict(p99=float(np.percentile(s_, 99)), p999=float(np.percentile(s_, 99.9)), max=float(s_.max()),
                                 at=np.round(M.Xe[imax], 1).tolist())
    np.save(os.path.join(CACHE, f'{part}_vm_{pose}{tag}.npy'), env.astype(np.float32))
    return out

if __name__ == '__main__':
    mode, H, todo = sys.argv[1], float(sys.argv[2]), sys.argv[3:] or dyn.poses.ORDER
    if mode == 'compliance':
        M = build_model('carrier', H)
        for pose in todo:
            T = dyn.load(pose); S = json.load(open(os.path.join(OUT, f'dyn_{pose}.json')))
            print(pose, flush=True); C = compliance(M, T, S)
            json.dump(C, open(os.path.join(CACHE, f'corec_{pose}.json'), 'w'), indent=1)
    else:
        for part in PARTS:
            M = build_model(part, H if part == 'carrier' else H / 2)
            np.savez_compressed(os.path.join(CACHE, f'{part}_grid.npz'), Xe=M.Xe, elab=M.elab, labels=np.array(M.g['labels']))
            for pose in todo:
                T = dyn.load(pose); S = json.load(open(os.path.join(OUT, f'dyn_{pose}.json')))
                r = stress(M, T, S, part)
                if r: json.dump(r, open(os.path.join(OUT, f'{part}_{pose}.json'), 'w'), indent=1)
                print(pose, part, {k: round(v['p999'], 1) for k, v in (r or {}).get('regions', {}).items()}, flush=True)
