"""Summary numbers per case from results/*.npz (pack3d.py). Run: python summary.py -> prints a table, writes renders/summary.json"""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack3d as P

CELLN = [c[0] for c in P.CELLS]

def summarise(name):
    z = np.load(os.path.join(P.OUT_DIR, f'{name}.npz')); meta = json.load(open(os.path.join(P.OUT_DIR, f'{name}.json')))
    cs = P.CASES[name]
    if 'rec_ntc' not in z:
        th = z['snap_steady']
        return dict(name=name, title=cs['title'], steady=True, rise=float(th.max()))
    r = {k[4:]: z[k] for k in z.files if k.startswith('rec_')}
    t = r['t']; dt = (t[1] - t[0]) * 60
    surf = r['surf_max']; ntc = r['ntc']; cm = r['cell_mean']
    i_hot = np.unravel_index(surf.argmax(), surf.shape)
    within = (r['cell_max'] - r['cell_min'])
    spread = cm.max(1) - cm.min(1)
    src = any(v[0] == 'src' for v in cs['ports'].values()); snk = any(v[0] == 'snk' for v in cs['ports'].values())
    asked = sum(v[1] for v in cs['ports'].values() if v[0] == 'src')
    s = dict(name=name, title=cs['title'], t_end=float(t[-1]),
             q_cells_max=float(r['q_cells'].max()), q_board_max=float(r['q_board'].max()),
             q_cells_0=float(r['q_cells'][0]), q_board_0=float(r['q_board'][0]),
             surf_max=float(surf.max()), surf_cell=CELLN[i_hot[1]], t_surf=float(t[i_hot[0]]),
             ntc_max=float(ntc.max()), ntc_alt_max=float(r['ntc_alt'].max()),
             ntc_lag=float((surf.max(1) - ntc.max(1)).max()),
             core_max=float(r['cell_max'].max()), part_max=float(r['part_max'].max()), board_max=float(r['board_max'].max()),
             ts_max=float(max(r['ts1'].max(), r['ts2'].max())),
             skin_max=float(r['skin_max'].max()), spread_max=float(spread.max()), within_max=float(within.max()),
             within_cell=CELLN[int(np.unravel_index(within.argmax(), within.shape)[1])],
             front_back=float((cm[:, list(P.FRONT)].mean(1) - cm[:, [1, 2]].mean(1)).max()))
    if src:
        p = r['p_out']; full = np.nonzero(p < asked*0.99)[0]
        s.update(asked=asked, wh_out=float(p.sum()*dt/3600), min_full=float(t[full[0]] if len(full) else t[-1]),
                 p_end=float(p[-1]), p_mean_after=float(p[full[0]:].mean()) if len(full) else float(asked),
                 wh_20=float(p[t < 20].sum()*dt/3600))
    if snk:
        ic = r['i_chg']; s.update(t_full=float(t[-1]), soc_end=float(r['soc'][-1]), p_in_max=float(r['p_in'].max()),
                                  i_mean=float(ic.mean()), min_at_max=float((ic >= 4.5).sum()*dt/60),
                                  t_derate=float(t[np.nonzero(ic < 4.5)[0][0]]) if (ic < 4.5).any() else None)
    return s

if __name__ == '__main__':
    names = [n for n in P.CASES if os.path.exists(os.path.join(P.OUT_DIR, f'{n}.npz'))]
    out = {n: summarise(n) for n in names}
    os.makedirs(os.path.join(P.HERE, 'renders'), exist_ok=True)
    json.dump(out, open(os.path.join(P.HERE, 'renders', 'summary.json'), 'w'), indent=1)
    for n, s in out.items():
        print(n, json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in s.items()}))
