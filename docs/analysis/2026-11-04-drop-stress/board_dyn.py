"""The board in a drop that has a component across it (board face, back face, and the edges and corners with an x part):
a Kirchhoff plate (the 10-31 study's Morley model of the routed P0 board, with its parts' masses) moving in the cup's
frame, pushed by the cup's deceleration from dyn.py, against one-sided supports with their gaps:
  toward the board-face wall (+x): the four PA12 post spacers (0.4 mm), the F.Cu lips on the long edges from z 27 up
  (0.5 mm), and the two USB-C housings in their top-wall pockets (0.2 mm, on the receptacles' solder tabs);
  toward the cells (-x): the rail blocks under B.Cu (they move with the core, from dyn.py) and the housings (0.17 mm).
Modal superposition (60 modes, 2 % damping), explicit in time. Gives the support forces, the board's bow, the surface
strain envelope and every F.Cu part's clearance to the wall.
Run: python board_dyn.py [pose ...] -> out/board_<pose>.json"""
import os, sys, json, numpy as np, scipy.sparse.linalg as sla, skfem as F
from skfem.helpers import dd, ddot, trace, eye
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'cache'); OUT = os.path.join(HERE, 'out')
sys.path.append(os.path.normpath(os.path.join(HERE, '..', '2026-10-31-drop-1m')))
import board_flex as BF
import dyn
G = 9.81
GAPS = dict(spacer=0.4, lip=0.5, usb_f=0.198, usb_b=0.168)      # from gapcheck (out/gaps.json)
K_SPACER = 4.5e3     # N/mm per spacer: PA12 tube, ~8.7 mm2 over 3.3 mm
K_LIP = 300.0        # N/mm per mm of edge: 1.8 mm PA12 ledge reaching 1.85 mm off the side wall
K_USB = 3.0e3        # N/mm per receptacle (shell tabs and pins)
K_RAIL = 2.0e4       # N/mm per rail block under B.Cu
K_PART = 3.0e3       # N/mm: a B.Cu part landing on a can or a cradle top (the part's body and joints)
RAIL_Y, RAIL_Z = (6.5, 11.3), ((7.3, 25.0), (55.0, 78.75))
LIP_Y, LIP_Z = 20.9, 27.0
N_MODES, ZETA, DT = 60, 0.02, 5e-8
POCKET = dict(L401=0.5, L501=0.5)

def setup():
    m, parts = BF.setup()
    # keep the largest edge-connected piece (the outline filter leaves triangles hanging on a corner: zero-energy modes)
    import scipy.sparse as sps, scipy.sparse.csgraph as csg
    t2f = m.t2f; nt = m.t.shape[1]
    rows = np.repeat(np.arange(nt), 3); A = sps.csr_matrix((np.ones(3 * nt), (rows, t2f.T.ravel())))
    adj = (A @ A.T) > 0; nc, lab = csg.connected_components(adj, directed=False)
    keep = lab == np.bincount(lab).argmax()
    m = F.MeshTri(m.p, m.t[:, keep])
    used = np.unique(m.t); remap = -np.ones(m.p.shape[1], int); remap[used] = np.arange(len(used))
    m = F.MeshTri(m.p[:, used], remap[m.t])                                 # drop the nodes outside the outline
    ib = F.Basis(m, F.ElementTriMorley())
    D = BF.E_FR4 * BF.T**3 / (12 * (1 - BF.NU**2))
    @F.BilinearForm
    def bil(u, v, w): return ddot(D * ((1 - BF.NU) * dd(u) + NU_ * eye(trace(dd(u)), 2)), dd(v))
    NU_ = BF.NU
    P = m.p; a_, b_, c_ = P[:, m.t[0]], P[:, m.t[1]], P[:, m.t[2]]
    A_board = 0.5 * np.abs((b_[0] - a_[0]) * (c_[1] - a_[1]) - (b_[1] - a_[1]) * (c_[0] - a_[0])).sum()
    pcb_g = 20.2 - sum(p['m'] for p in parts.values())
    rho_a = pcb_g / 1000 / A_board                                          # kg/mm2
    @F.BilinearForm
    def mass(u, v, w): return rho_a * u * v
    K = bil.assemble(ib).tocsc(); M = mass.assemble(ib).tolil()
    vdof = ib.nodal_dofs[0]
    for k, p in parts.items():
        sel = np.where((P[0] >= p['y0']) & (P[0] <= p['y1']) & (P[1] >= p['z0']) & (P[1] <= p['z1']))[0]
        if len(sel) == 0: sel = [np.argmin((P[0] - p['y'])**2 + (P[1] - p['z'])**2)]
        for s in sel: M[vdof[s], vdof[s]] += p['m'] / 1000 / len(sel)
    M = M.tocsc()
    # modes (K in N/mm, M in kg -> w in mm, omega^2 in N/(mm kg) = 1e3 / s^2)
    lam, Phi = sla.eigsh(K, k=N_MODES, M=M, sigma=-1.0, which='LM')
    o = np.argsort(lam); lam, Phi = np.maximum(lam[o], 0), Phi[:, o]
    W = Phi[vdof]                                                           # vertex w per mode
    # per-mode element curvature -> surface strain (linear in q: keep the three curvature components)
    curv = []
    for i in range(N_MODES):
        H = ib.interpolate(Phi[:, i]).hess
        curv.append(np.stack([H[0][0].mean(1), H[1][1].mean(1), H[0][1].mean(1)]))
    curv = np.array(curv)                                                   # (modes, 3, elements)
    mvert = np.asarray(M.diagonal())[vdof]                                  # lumped-ish vertex masses for the inertia load
    # inertia load of a unit acceleration: consistent, via M @ (w = 1 everywhere, slopes 0)
    ones = np.zeros(M.shape[0]); ones[vdof] = 1.0
    g_modal = Phi.T @ (M @ ones)                                            # modal force per (m/s2 -> N/kg)... see run()
    sup = supports(P, parts)
    return dict(m=m, parts=parts, P=P, lam=lam, W=W, curv=curv, g_modal=g_modal, sup=sup, mass_kg=float(ones @ (M @ ones)))

def bcu_gaps():
    """every B.Cu part within 3 mm of a can or a cradle top along -x at nominal: {ref: dict(y0, y1, z0, z1, gap, by)}
    with by = the cell it meets (moves with the core) or 'cradles' (the cup). Cached in cache/board_bcu.json."""
    p = os.path.join(CACHE, 'board_bcu.json')
    if os.path.exists(p): return json.load(open(p))
    import bodies, contacts as C
    MF = bodies.MF; B, sub, m, prm, A = bodies.build(); RB = bodies.P.real_board(); xb0 = BF.X_F - 1.6
    stops = {c: B[c]['m'] for c in ('C1', 'C2', 'C3', 'C4')}; stops['cradles'] = sub['cradles']; out = {}
    for k, V in RB.items():
        if k.startswith('_') or k == 'PCB' or str(RB.get('_model_' + k, '')).startswith(('Peg_', 'SolderWire')): continue
        P = V.reshape(-1, 3)
        if P[:, 0].mean() > xb0: continue                                    # F.Cu side
        h = MF.hull_points(P); best = None
        for nm, sm in stops.items():
            g = C.first_gap(h, sm, (-1.0, 0.0, 0.0), dmax=3.0)
            if g is not None and (best is None or g < best[0]): best = (g, nm)
        if best: out[k] = dict(y0=float(P[:, 1].min()), y1=float(P[:, 1].max()), z0=float(P[:, 2].min()), z1=float(P[:, 2].max()),
                               gap=round(best[0], 3), by=best[1])
    json.dump(out, open(p, 'w'), indent=1)
    return out

RAIL_BLOCK = {(-1, 0): 'rails_bn', (-1, 1): 'rails_tn', (1, 0): 'rails_bp', (1, 1): 'rails_tp'}   # (side of y, z band)

def flex(B=None):
    """The board's own give at each support group, relative to its rigid motion (inertia relief: the flexible modes
    only), mm/N along x for a force spread evenly over the group's nodes. dyn.py puts it in series with the board's
    contacts (times dx^2), since it carries the board as one rigid body. Cached in cache/board_flex.json."""
    p = os.path.join(CACHE, 'board_flex.json')
    if os.path.exists(p): return json.load(open(p))
    B = B or setup(); lam, W = B['lam'], B['W']
    fl = lam > 1.0                                                           # drop the three rigid-body modes
    groups = {}
    for kind, n, k, gap, sgn in B['sup']:
        g = {'spacer': 'spacers', 'lip': 'lips', 'usb_f': 'usb'}.get(kind)
        if g: groups.setdefault(g, []).append(n)
    ri = 0
    for s in (-1, 1):
        for zb in (0, 1): groups[RAIL_BLOCK[(s, zb)]] = [B['sup'][[i for i, x in enumerate(B['sup']) if x[0] == 'rail'][ri]][1]]; ri += 1
    out = {}
    for g, ns in groups.items():
        n = np.concatenate(ns); phi = W[n][:, fl].mean(0)
        out[g] = float((phi**2 / lam[fl]).sum())
    json.dump(out, open(p, 'w'), indent=1)
    return out

def supports(P, parts):
    y, z = P[0], P[1]; out = []
    for i, (py, pz) in enumerate(BF.PEGS):
        n = np.where(np.hypot(y - py, z - pz) <= 2.0)[0]; out.append(('spacer', n, K_SPACER / len(n), GAPS['spacer'], +1))
    # lips: nodes on the long edges (|y| >= 20.9), z >= 27; spread K_LIP over their length
    for s in (-1, 1):
        n = np.where((s * y >= LIP_Y) & (z >= LIP_Z))[0]
        L = z[n].max() - z[n].min(); out.append(('lip', n, K_LIP * L / len(n), GAPS['lip'], +1))
    for k in ('J401', 'J501'):
        p = parts[k]; n = np.where((y >= p['y0']) & (y <= p['y1']) & (z >= 76.5))[0]
        out.append(('usb_f', n, K_USB / len(n), GAPS['usb_f'], +1)); out.append(('usb_b', n, K_USB / len(n), GAPS['usb_b'], -1))
    for s in (-1, 1):
        for z0, z1 in RAIL_Z:
            n = np.where((s * y >= RAIL_Y[0]) & (s * y <= RAIL_Y[1]) & (z >= z0) & (z <= z1))[0]
            out.append(('rail', n, K_RAIL / len(n), 0.0, -1))
    for k, q in bcu_gaps().items():                                          # B.Cu parts onto the cans / cradle tops
        n = np.where((y >= q['y0']) & (y <= q['y1']) & (z >= q['z0']) & (z <= q['z1']))[0]
        if len(n) == 0: n = np.array([np.argmin((y - (q['y0'] + q['y1']) / 2)**2 + (z - (q['z0'] + q['z1']) / 2)**2)])
        out.append(('bcu:' + k + ':' + q['by'], n, K_PART / len(n), q['gap'], -1))
    return out

def run(pose, B=None, rails_body='rails_tp', record=None, rec_every=200):
    """record: a list to fill with snapshots every rec_every steps (t, modal q, support forces, cup acceleration)"""
    B = B or setup()
    T = dyn.load(pose); d = np.asarray(T['d'], float); dx = d[0]
    if abs(dx) < 0.05: return None
    R = np.load(os.path.join(CACHE, f'dyn_{pose}.npz'))
    t = R['t']; a_shell = R['a'][:, 0] * G * 1e3                    # mm/s2, along d (+ toward the floor)
    # the core's push on B.Cu through each rail block, from dyn.py (force on the board along +x, N)
    names = list(R['names']); Frail = {}
    for j, nm in enumerate(names):
        a, b, sn = nm.split('|')
        if dyn.body_of(a) == 'board' and dyn.body_of(b).startswith('rails_'):
            Frail[dyn.body_of(b)] = Frail.get(dyn.body_of(b), 0) + R['F'][:, j] * (-1 if sn == '+' else 1) * dx
    ri = [i for i, s_ in enumerate(B['sup']) if s_[0] == 'rail']; rail_of = {}
    for (s_, zb), i in zip([(s_, zb) for s_ in (-1, 1) for zb in (0, 1)], ri): rail_of[i] = RAIL_BLOCK[(s_, zb)]
    ux = {c: (R['x'][:, dyn.BODIES.index(c)] - R['x'][:, 0]) * dx for c in ('C1', 'C2', 'C3', 'C4')}   # cells along +x, mm
    lam, W, gm = B['lam'], B['W'], B['g_modal']
    om = np.sqrt(lam * 1e3)                                         # rad/s (lam in N/(mm kg))
    nm = len(lam); q = np.zeros(nm); qd = np.zeros(nm)
    ts = np.arange(0, t[-1], DT)
    env_curv = np.zeros(B['curv'].shape[2]); wmax_t = np.full(W.shape[0], -1e9); wmin_t = np.full(W.shape[0], 1e9)
    Fsup = {i: 0.0 for i in range(len(B['sup']))}; rec = []; Fnow = np.zeros(len(B['sup']))
    for k_, tt in enumerate(ts):
        a = np.interp(tt, t, a_shell) * dx                          # cup's acceleration across the board, mm/s2
        w = W @ q                                                   # mm
        f = np.zeros(W.shape[0])
        for i, (kind, n, k, gap, sgn) in enumerate(B['sup']):
            if kind == 'rail':                                       # the core's push, spread over the block's nodes
                Fr = np.interp(tt, t, Frail[rail_of[i]]) if rail_of[i] in Frail else 0.0
                fn = np.full(len(n), max(Fr, 0.0) / len(n)); f[n] += fn
            elif kind.startswith('bcu:'):                             # gap = nominal + bow toward the wall - the cell's own x
                uc = np.interp(tt, t, ux[kind.split(':')[2]]) if not kind.endswith(':cradles') else 0.0
                pen = np.maximum(uc - w[n] - gap, 0); fn = k * pen; f[n] += fn
            else:
                pen = np.maximum(sgn * w[n] - gap, 0); fn = k * pen; f[n] -= sgn * fn
            tot = fn.sum(); Fnow[i] = tot
            if tot > Fsup[i]: Fsup[i] = tot
        # modal forces: support forces (N) + the cup frame's pseudo-force -m a (kg * mm/s2 = 1e-3 N)
        Q = W.T @ f - gm * a * 1e-3
        qdd = Q * 1e3 - 2 * ZETA * om * qd - om**2 * q             # (N/kg = 1e3 mm/s2)
        qd += qdd * DT; q += qd * DT
        if record is not None and k_ % rec_every == 0:
            record.append(dict(t=tt, q=q.copy(), F=Fnow.copy(), a_g=a / dx / (G * 1e3) if dx else 0.0,
                               uc={c: float(np.interp(tt, t, ux[c])) for c in ux}))
        if k_ % 50 == 0:
            w = W @ q; wmax_t = np.maximum(wmax_t, w); wmin_t = np.minimum(wmin_t, w)
            c = np.tensordot(q, B['curv'], axes=(0, 0))             # (3, el)
            kxx, kyy, kxy = c; r = np.sqrt((0.5 * (kxx - kyy))**2 + kxy**2)
            kmax = np.maximum(np.abs(0.5 * (kxx + kyy) + r), np.abs(0.5 * (kxx + kyy) - r))
            env_curv = np.maximum(env_curv, kmax)
    strain = env_curv * BF.T / 2
    P = B['P']; mtri = B['m'].t; ce = P[:, mtri].mean(1)
    parts = {}
    for k, p in B['parts'].items():
        sel = (P[0] >= p['y0']) & (P[0] <= p['y1']) & (P[1] >= p['z0']) & (P[1] <= p['z1'])
        if not sel.any(): sel = np.zeros(P.shape[1], bool); sel[np.argmin((P[0] - p['y'])**2 + (P[1] - p['z'])**2)] = True
        es = (ce[0] >= p['y0'] - 0.5) & (ce[0] <= p['y1'] + 0.5) & (ce[1] >= p['z0'] - 0.5) & (ce[1] <= p['z1'] + 0.5)
        parts[k] = dict(side=p['side'], strain_ue=float(strain[es].max() * 1e6) if es.any() else 0.0,
                        w_max=float(wmax_t[sel].max()), clear_mm=float(BF.X_IN + POCKET.get(k, 0) - p['top'] - wmax_t[sel].max()) if p['side'] == 'F' else None)
    names = [f"{s[0]}{i}" for i, s in enumerate(B['sup']) if not s[0].startswith('bcu:')]
    groups = {}
    for i, s in enumerate(B['sup']):
        g = 'bcu' if s[0].startswith('bcu:') else s[0]; groups[g] = groups.get(g, 0) + Fsup[i]
    strikes = sorted([dict(ref=s[0].split(':')[1], on=s[0].split(':')[2], gap_mm=s[3], peak_N=round(Fsup[i], 1))
                      for i, s in enumerate(B['sup']) if s[0].startswith('bcu:') and Fsup[i] > 0.5], key=lambda r: -r['peak_N'])
    worst = sorted([(v['clear_mm'], k) for k, v in parts.items() if v['clear_mm'] is not None])[:5]
    out = dict(pose=pose, dx=dx, w_toward_wall_max=float(wmax_t.max()), w_toward_cells_max=float(-wmin_t.min()),
               strain_max_ue=float(strain.max() * 1e6), strain_p99_ue=float(np.percentile(strain, 99) * 1e6),
               support_peak_N={n: round(Fsup[i], 1) for i, n in enumerate(names)}, bcu_strikes=strikes, support_groups_sum_of_peaks_N={k: round(v, 1) for k, v in groups.items()},
               closest_parts=[dict(ref=k, clear_mm=round(c, 3), strain_ue=round(parts[k]['strain_ue'])) for c, k in worst],
               highest_strain_parts=sorted([dict(ref=k, strain_ue=round(v['strain_ue']), side=v['side']) for k, v in parts.items()], key=lambda r: -r['strain_ue'])[:8])
    np.save(os.path.join(CACHE, f'board_strain_{pose}.npy'), strain.astype(np.float32))
    np.savez_compressed(os.path.join(CACHE, 'board_mesh.npz'), p=B['P'], t=B['m'].t)          # for figs.py
    return out

if __name__ == '__main__':
    B = setup()
    print(f"board modes: {np.sqrt(B['lam'][3:8] * 1e3) / 2 / np.pi} Hz, mass {B['mass_kg'] * 1e3:.1f} g", flush=True)
    for p in sys.argv[1:] or dyn.poses.ORDER:
        if not os.path.exists(os.path.join(CACHE, f'dyn_{p}.npz')): continue
        r = run(p, B)
        if r is None: continue
        json.dump(r, open(os.path.join(OUT, f'board_{p}.json'), 'w'), indent=1)
        print(p, json.dumps({k: r[k] for k in ('w_toward_wall_max', 'w_toward_cells_max', 'strain_max_ue', 'strain_p99_ue', 'support_groups_sum_of_peaks_N')}), r['closest_parts'][:2], flush=True)
