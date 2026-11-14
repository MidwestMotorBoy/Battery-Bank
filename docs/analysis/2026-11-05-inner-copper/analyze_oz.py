"""python analyze_oz.py [amb tag] -> prints and writes results/p0f/oz_metrics.json"""
import numpy as np, os, sys, json
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results', 'p0f'); sfx = sys.argv[1] if len(sys.argv) > 1 else ''
out = {}
for case in ('dis100', 'dis100u2'):
    for w in ('0.5', '1', '2'):
        f = os.path.join(D, f'{case}_oz{w}{sfx}.npz')
        if not os.path.exists(f): continue
        z = np.load(f); t = z['rec_t']; p = z['rec_p_out']
        full = t[p >= 0.99 * p.max()]; k = t <= 40
        r = dict(burst_min=float(full.max() + (t[1] - t[0])) if len(full) else 0.0,
                 Wh40=float(np.trapezoid(p[k], t[k]) / 60), can_max=float(z['rec_cell_max'].max()),
                 part_max=float(z['rec_part_max'].max()), t_end=float(t[-1]),
                 board_heat_W_first4min=float(z['rec_q_board'][t <= 4].mean()))
        out[f'{case}_oz{w}'] = {a: round(b, 2) for a, b in r.items()}; print(case, w, out[f'{case}_oz{w}'])
json.dump(out, open(os.path.join(D, f'oz_metrics{sfx}.json'), 'w'), indent=1)
