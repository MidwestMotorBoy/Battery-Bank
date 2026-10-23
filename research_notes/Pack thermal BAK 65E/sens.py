"""Sensitivity runs of the 100 W case (first 40 min): cell resistance, NTC placement, ambient and convection.
Run: python sens.py VARIANT [...]  (variants below) -> results/dis100_<variant>.npz; python sens.py table -> prints the comparison"""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack3d as P

VARIANTS = {
    'r12':   dict(label='Cell DC resistance 12 mΩ', r25=0.012),
    'r16':   dict(label='Cell DC resistance 16 mΩ', r25=0.016),
    'ntcb':  dict(label='Front-cell NTCs on the board-facing side', ntc_side='board'),
    'amb35': dict(label='35 °C ambient', amb=35.0),
    'h4':    dict(label='In a pack pocket (h = 4 W/m²K)', h_ext=4.0),
    'pol40': dict(label='Derate moved to 40 → 44 °C (sustain 40 W)', derate=(40.0, 44.0, 40.0)),
}
BASE = dict(label='Baseline (14 mΩ, NTC facing the centre, 25 °C, still air)')

def run(v):
    o = VARIANTS[v]; P.R25 = o.get('r25', 0.014); P.DERATE = o.get('derate', P.DERATE)
    g = P.get_grid()
    P.run_case(g, 'dis100', h_ext=o.get('h_ext', 10.0), amb=o.get('amb', 25.0), tag='_' + v,
               ntc_side=o.get('ntc_side', 'centre'), hours=40/60)

def row(path, label):
    z = np.load(path); t = z['rec_t']; p = z['rec_p_out']; m = t <= 40
    full = np.nonzero(p < 99)[0]
    return dict(label=label, min_full=float(t[full[0]] if len(full) else t[-1]), wh_20=float(p[t < 20].sum()*(t[1] - t[0])*60/3600),
                wh_40=float(p[m].sum()*(t[1] - t[0])*60/3600), surf=float(z['rec_surf_max'][m].max()), ntc=float(z['rec_ntc'][m].max()),
                part=float(z['rec_part_max'][m].max()), skin=float(z['rec_skin_max'][m].max()), p40=float(p[m][-1]))

if __name__ == '__main__':
    if sys.argv[1:] == ['table']:
        rows = [row(os.path.join(P.OUT_DIR, 'dis100.npz'), BASE['label'])]
        rows += [row(os.path.join(P.OUT_DIR, f'dis100_{v}.npz'), o['label']) for v, o in VARIANTS.items()
                 if os.path.exists(os.path.join(P.OUT_DIR, f'dis100_{v}.npz'))]
        json.dump(rows, open(os.path.join(P.HERE, 'renders', 'sensitivity.json'), 'w'), indent=1)
        for r in rows: print(json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()}))
    else:
        for v in sys.argv[1:]: run(v)
