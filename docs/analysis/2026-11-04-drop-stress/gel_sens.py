"""Sensitivity: the GEL 30 gap filler between B.Cu and the two front cells as a load path in the board plate model
(board_dyn.py), bracketed. The drop model itself carries the gel as mass only (half on the board, a quarter on each
front cell). GEL 30 data (Parker Chomerics GEL 8010 / GEL 30 sheet): 22 / 40 / 51 / 61 % deflection at 0.5 / 1 / 2 /
4 psi (modified ASTM C165, 1 cc, 1 in probe, 0.025 in/min), flow 20 g/min through a 0.100 in orifice at 90 psi
(~1200 Pa s at ~65 1/s, by Poiseuille over ~5 mm; shear thinning takes it lower at the ~2000 1/s of a drop).

Per plate node in the two fill zones (|y| 7-16, z 27-53; y < 0 -> C1, y > 0 -> C4), with the local bond line h(y)
(2.75 mm at the can tangent, 3.8 at the zone edges) and the node's share a of the zone area:
  elastic, compression only:  f = E a / h * squeeze            (E: datasheet ~0.14 MPa tangent at 50 %, x10 bracket)
  squeeze film, both ways:    f = -(eta w^2 / h^3) a * d(gap)/dt  (strip of width w = 9 mm, gel escapes across it)
  tension (gap opening) capped at P_TENS per area (suction / tack, ~1 atm).
Force on the board along +x. Everything else as board_dyn.run on the current cache (dyn_<pose>.npz).
Needs cache/dyn_<pose>.npz (run_all.py). Run: python gel_sens.py [pose ...] -> out/gel_sensitivity.json"""
import os, sys, json, time, numpy as np
STUDY = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, STUDY)
import board_dyn as BD, dyn
G = 9.81
FILL_Y, FILL_Z, W_STRIP = (7.0, 16.0), (27.0, 53.0), 9.0
XB0, CXY, CR = 25.3, 11.625, 10.925                      # B.Cu face; front-cell centre |x| = |y|; can radius (from the section)
P_TENS = 0.1                                              # MPa

def gel_nodes(B):
    P = B['P']; y, z = P[0], P[1]
    out = []
    for cell, s in (('C1', -1), ('C4', 1)):
        n = np.where((s * y >= FILL_Y[0]) & (s * y <= FILL_Y[1]) & (z >= FILL_Z[0]) & (z <= FILL_Z[1]))[0]
        h = XB0 - (CXY + np.sqrt(np.maximum(CR**2 - (np.abs(y[n]) - CXY)**2, 0)))
        a = (FILL_Y[1] - FILL_Y[0]) * (FILL_Z[1] - FILL_Z[0]) / len(n)
        out.append((cell, n, h, a))
    return out

def run(pose, B, E=0.0, eta=0.0):
    T = dyn.load(pose); d = np.asarray(T['d'], float); dx = d[0]
    R = np.load(os.path.join(BD.CACHE, f'dyn_{pose}.npz'))
    t = R['t']; a_shell = R['a'][:, 0] * G * 1e3
    names = list(R['names']); Frail = {}
    for j, nm in enumerate(names):
        a, b, sn = nm.split('|')
        if dyn.body_of(a) == 'board' and dyn.body_of(b).startswith('rails_'):
            Frail[dyn.body_of(b)] = Frail.get(dyn.body_of(b), 0) + R['F'][:, j] * (-1 if sn == '+' else 1) * dx
    ri = [i for i, s_ in enumerate(B['sup']) if s_[0] == 'rail']; rail_of = {}
    for (s_, zb), i in zip([(s_, zb) for s_ in (-1, 1) for zb in (0, 1)], ri): rail_of[i] = BD.RAIL_BLOCK[(s_, zb)]
    ux = {c: (R['x'][:, dyn.BODIES.index(c)] - R['x'][:, 0]) * dx for c in ('C1', 'C2', 'C3', 'C4')}
    vx = {c: np.gradient(ux[c], t) for c in ux}                                     # mm/s
    gel = gel_nodes(B)
    gk = [(c, n, E * a / h, eta * 1e-6 * W_STRIP**2 / h**3 * a, P_TENS * a) for c, n, h, a in gel]   # N/mm, N s/mm, N
    lam, W, gm = B['lam'], B['W'], B['g_modal']; om = np.sqrt(lam * 1e3)
    q = np.zeros(len(lam)); qd = np.zeros(len(lam))
    env = np.zeros(B['curv'].shape[2]); wmin = np.full(W.shape[0], 1e9); wmax = np.full(W.shape[0], -1e9)
    Fsup = np.zeros(len(B['sup'])); Fgel_pk = 0.0; Fgel_tens = 0.0
    for k_, tt in enumerate(np.arange(0, t[-1], BD.DT)):
        a = np.interp(tt, t, a_shell) * dx; w = W @ q; f = np.zeros(W.shape[0])
        for i, (kind, n, k, gap, sgn) in enumerate(B['sup']):
            if kind == 'rail':
                Fr = np.interp(tt, t, Frail[rail_of[i]]) if rail_of[i] in Frail else 0.0
                fn = np.full(len(n), max(Fr, 0.0) / len(n)); f[n] += fn
            elif kind.startswith('bcu:'):
                uc = np.interp(tt, t, ux[kind.split(':')[2]]) if not kind.endswith(':cradles') else 0.0
                pen = np.maximum(uc - w[n] - gap, 0); fn = k * pen; f[n] += fn
            else:
                pen = np.maximum(sgn * w[n] - gap, 0); fn = k * pen; f[n] -= sgn * fn
            Fsup[i] = max(Fsup[i], fn.sum())
        if E or eta:
            wd = W @ qd; Ftot = 0.0
            for c, n, ke, ce_, cap in gk:
                uc = np.interp(tt, t, ux[c]); vc = np.interp(tt, t, vx[c])
                sq = uc - w[n]                                               # squeeze of the gel past its rest (mm)
                fg = ke * np.maximum(sq, 0) + ce_ * (vc - wd[n])             # + pushes the board toward the wall
                fg = np.maximum(fg, -cap); f[n] += fg; Ftot += fg.sum()
            Fgel_pk = max(Fgel_pk, Ftot); Fgel_tens = min(Fgel_tens, Ftot)
        Q = W.T @ f - gm * a * 1e-3
        qdd = Q * 1e3 - 2 * BD.ZETA * om * qd - om**2 * q; qd += qdd * BD.DT; q += qd * BD.DT
        if k_ % 50 == 0:
            w = W @ q; wmin = np.minimum(wmin, w); wmax = np.maximum(wmax, w)
            cc = np.tensordot(q, B['curv'], axes=(0, 0)); kxx, kyy, kxy = cc; r = np.sqrt((0.5 * (kxx - kyy))**2 + kxy**2)
            env = np.maximum(env, np.maximum(np.abs(0.5 * (kxx + kyy) + r), np.abs(0.5 * (kxx + kyy) - r)))
    strain = env * BD.BF.T / 2 * 1e6
    P = B['P']; ce = P[:, B['m'].t].mean(1); parts = {}; clr = []
    for k, p in B['parts'].items():
        es = (ce[0] >= p['y0'] - 0.5) & (ce[0] <= p['y1'] + 0.5) & (ce[1] >= p['z0'] - 0.5) & (ce[1] <= p['z1'] + 0.5)
        parts[k] = float(strain[es].max()) if es.any() else 0.0
        if p['side'] == 'F':
            sel = (P[0] >= p['y0']) & (P[0] <= p['y1']) & (P[1] >= p['z0']) & (P[1] <= p['z1'])
            if not sel.any(): sel = np.zeros(P.shape[1], bool); sel[np.argmin((P[0] - p['y'])**2 + (P[1] - p['z'])**2)] = True
            clr.append((BD.BF.X_IN + BD.POCKET.get(k, 0) - p['top'] - wmax[sel].max(), k))
    grp = {}
    for i, s in enumerate(B['sup']):
        g = 'bcu' if s[0].startswith('bcu:') else s[0]; grp[g] = round(grp.get(g, 0) + Fsup[i], 1)
    top = sorted(parts.items(), key=lambda kv: -kv[1])[:4]
    return dict(pose=pose, E_MPa=E, eta_Pas=eta, p99_ue=round(float(np.percentile(strain, 99))), max_ue=round(float(strain.max())),
                bow_cells_mm=round(float(-wmin.min()), 3), bow_wall_mm=round(float(wmax.max()), 3),
                gel_push_N=round(Fgel_pk, 1), gel_pull_N=round(-Fgel_tens, 1), supports=grp,
                worst=[(k, round(v)) for k, v in top], wall_clear=[(k, round(c, 3)) for c, k in sorted(clr)[:3]], usb=(round(parts.get('J401', 0)), round(parts.get('J501', 0))))

if __name__ == '__main__':
    B = BD.setup(); poses = sys.argv[1:] or ['back', 'board']
    cases = [(0, 0), (0.14, 0), (0.14, 50), (0.14, 160), (1.4, 500), (1.4, 1220)]
    res = []
    for p in poses:
        for E, eta in cases:
            t0 = time.time(); r = run(p, B, E, eta); r['s'] = round(time.time() - t0); res.append(r)
            print(json.dumps(r), flush=True)
    json.dump(res, open(os.path.join(STUDY, 'out', 'gel_sensitivity.json'), 'w'), indent=1)
