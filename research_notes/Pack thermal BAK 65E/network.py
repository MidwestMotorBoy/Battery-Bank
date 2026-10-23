"""Lumped thermal circuit extracted from the 3-D model: nodes for the four cells, the two power stages, the pack path
(protection FETs, fuse, shunt) and the enclosure skin, with ambient as ground. Each node is a weighted group of voxels
(the cells' jelly rolls, the parts by their share of the 100 W losses, the skin by its exterior conductance). Injecting
1 W into each group and solving the steady state gives the transfer matrix Z (K/W); its inverse is the conductance
network. Heat capacities split the voxel capacity by nearest node. Then a transient check against the full model.
Run: python network.py -> renders/network.json"""
import os, sys, json
import numpy as np, scipy.sparse as sp, pyamg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack3d as P
import sheet

NODES = ['C1', 'C2', 'C3', 'C4', 'S1', 'S2', 'PP', 'SK']
LABELS = dict(C1='Cell C1 (front, under USB2)', C2='Cell C2 (back)', C3='Cell C3 (back)', C4='Cell C4 (front, under USB1)',
              S1='USB1 power stage', S2='USB2 power stage', PP='Pack path (protection FETs, fuse, shunt)', SK='Enclosure skin')

def weights(g):
    dom = g.dom; boxes = P.src_boxes()
    W = {n: g.box_weights(b)[dom] for n, b in boxes.items()}
    L, _ = P.port_loss(100.0, 20.0, 14.4, False)
    out = {}
    cw = g.cellw[dom]; cw = cw / cw.sum(0)
    for k in range(4): out[f'C{k+1}'] = cw[:, k]
    for p in (1, 2):
        w = sum(W[f'{part}{p}']*L[part] for part in ('fet', 'ind', 'ic', 'sense')); out[f'S{p}'] = w / w.sum()
    w = sum(W[n]*P.P0[n] for n in ('prot', 'fuse', 'shunt', 'pack_cu')); out['PP'] = w / w.sum()
    return out, L

def extract(sheet_kt=None):
    P.SHEET = dict(kt=sheet_kt, z=sheet.Z_SHEET) if sheet_kt else None
    g = P.get_grid(); K, ge = g.assemble(10.0)
    w, _ = weights(g); w['SK'] = ge / ge.sum()
    ml = pyamg.smoothed_aggregation_solver(K, symmetry='symmetric')
    th = {n: ml.solve(w[n], tol=1e-10, accel='cg', maxiter=400) for n in NODES}
    Z = np.array([[w[i] @ th[j] for j in NODES] for i in NODES])
    Z = 0.5*(Z + Z.T)
    G = np.linalg.inv(Z)
    # heat capacity: each active voxel to the node it is warmest for per watt (the node that "owns" it)
    own = np.argmax(np.stack([th[n] / Z[k, k] for k, n in enumerate(NODES)], 1), 1)
    Cv = g.C[g.dom]
    Cn = np.array([Cv[own == k].sum() for k in range(len(NODES))])
    return g, Z, G, Cn, ge

_Q = {}
def node_heat(case, tag=''):
    """per-node heat (W) over time from the full model's record: cells share the cell and nickel heat equally,
    each stage gets its port's losses, the pack path its I^2 R"""
    key = case + tag
    if key in _Q: return _Q[key]
    z = np.load(os.path.join(P.OUT_DIR, f'{case}{tag}.npz')); t = z['rec_t']
    Q = np.zeros((len(t), len(NODES)))
    for i in range(len(t)):
        q = Q[i]; q[:4] = z['rec_q_cells'][i]/4
        vb = z['rec_v_bus'][i]; ib = z['rec_i_bat'][i]
        for p, key, node in ((1, 'rec_p1', 4), (2, 'rec_p2', 5)):
            pw = z[key][i]
            if pw > 0: q[node] += sum(P.port_loss(pw, 20.0 if p == 1 else 15.0, vb, False)[0].values())
            elif pw < 0: q[node] += sum(P.port_loss(-pw, 20.0, vb, True)[0].values())
        q[6] = (P.P0['prot'] + P.P0['fuse'] + P.P0['shunt'] + P.P0['pack_cu'])*ib**2
        q[:4] += z['rec_q_ni'][i]/4
    _Q[key] = (t, Q, z['rec_cell_mean']); return _Q[key]

def transient(G, Cn, case='dis100', tag=''):
    """drive the lumped network with the full model's recorded powers and compare the cell means"""
    t, Q, full = node_heat(case, tag); dt = (t[1] - t[0])*60
    n = len(NODES); th = np.zeros(n); A = np.diag(Cn/dt) + G; Ainv = np.linalg.inv(A); out = []
    for q in Q:
        out.append(th.copy())
        th = Ainv @ (Cn/dt*th + q)
    lump = np.array(out)[:, :4] + 25.0
    return dict(max_err=float(np.abs(lump - full).max()), peak_full=full.max(0).round(1).tolist(), peak_lump=lump.max(0).round(1).tolist(),
                c2c_full=float((full.max(1) - full.min(1)).max()), c2c_lump=float((lump.max(1) - lump.min(1)).max()))

# steady operating points (heat in W: all four cells incl. nickel, each stage, pack path), from the case records
OPS = {'40 W out, sustained': dict(cells=0.45, S1=1.17, S2=0.0, PP=0.06),
       '100 W out, if it were held': dict(cells=2.45, S1=3.55, S2=0.0, PP=0.29),
       'Charging at 4.55 A, if it were held': dict(cells=1.69, S1=2.01, S2=0.0, PP=0.15),
       'Pass-through (100 W in, 30 W out)': dict(cells=1.31, S1=3.76, S2=0.86, PP=0.15)}
C_CELL = 68.0                                   # J/K per cell (72 g x 0.95 J/g K), fixed; the rest are fitted
def fit_capacities(Gs):
    """stage, pack-path and skin capacities (J/K), one set for both variants, fitted so the lumped circuit's cell means
    track the full model through dis100, chg1 and pass"""
    from scipy.optimize import minimize
    def err(x):
        cs, cp, ck = np.exp(x); Cn = np.array([C_CELL]*4 + [cs, cs, cp, ck]); e = 0.0
        for G, tag in Gs:
            for c in ('dis100', 'chg1', 'pass'): e += transient(G, Cn, c, tag)['max_err']**2
        return e
    r = minimize(err, np.log([5.0, 2.0, 150.0]), method='Nelder-Mead', options=dict(maxiter=400, xatol=1e-3, fatol=1e-4))
    cs, cp, ck = np.exp(r.x); return np.array([C_CELL]*4 + [cs, cs, cp, ck])

if __name__ == '__main__':
    res = {}; ext = {}
    for name, kt, tag in (('base', None, ''), ('wrap', sheet.VARIANTS['pgs70']['kt'], '_sheet_pgs70')):
        ext[name] = extract(kt) + (tag,)
    Cn = fit_capacities([(e[2], e[5]) for e in ext.values()])
    for name, (g, Z, G, _, ge, tag) in ext.items():
        n = len(NODES)
        edges = [dict(a=NODES[i], b=NODES[j], g=float(-G[i, j]), r=float(-1/G[i, j]) if G[i, j] != 0 else None)
                 for i in range(n) for j in range(i + 1, n) if abs(G[i, j]) > 1e-4]
        amb = [dict(a=NODES[i], g=float(G[i].sum()), r=float(1/G[i].sum())) for i in range(n) if abs(G[i].sum()) > 1e-4]
        chk = {c: transient(G, Cn, c, tag) for c in ('dis100', 'chg1', 'pass')}
        ops = {}
        for op, q in OPS.items():
            ops[op] = (np.linalg.solve(G, np.array([q['cells']/4]*4 + [q['S1'], q['S2'], q['PP'], 0.0])) + 25.0).round(1).tolist()
        res[name] = dict(G=G.tolist(), ops=ops, Z=Z.round(3).tolist(), edges=edges, amb=amb, C=dict(zip(NODES, Cn.round(1).tolist())), check=chk,
                         g_ext_total=float(ge.sum()))
        print(name, 'C', dict(zip(NODES, Cn.round(1))), '\n check', chk)
        for e in sorted(edges, key=lambda e: -abs(e['g'])): print(f"  {e['a']}-{e['b']}: G {e['g']:.4f} W/K  R {e['r']:.1f} K/W")
        for a in amb: print(f"  {a['a']}-amb: G {a['g']:.4f}  R {a['r']:.1f}")
    res['labels'] = LABELS; res['nodes'] = NODES; res['ops_q'] = OPS
    json.dump(res, open(os.path.join(P.HERE, 'renders', 'network.json'), 'w'), indent=1)
