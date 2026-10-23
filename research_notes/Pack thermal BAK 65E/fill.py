"""Gap-filler options: where it goes, how conductive, what it weighs, and what it does to the 100 W burst and to charging.
Run: python fill.py VARIANT [...] -> results/{dis100,chg1}_fill_<variant>.npz ; python fill.py table -> renders/fill.json"""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack3d as P

BASE_ZONE = (18.0, 25.3, 7.0, 16.0, 27.0, 53.0)
VARIANTS = {
    'none':  dict(label='No filler (air gap, board to cells)', zones=[], k=3.0),
    'base':  dict(label='Baseline: 3 W/mK, board to front cells over the stages', zones=[BASE_ZONE], k=3.0),
    'k15':   dict(label='Same place, 1.5 W/mK (budget filler or soft pad)', zones=[BASE_ZONE], k=1.5),
    'k6':    dict(label='Same place, 6 W/mK', zones=[BASE_ZONE], k=6.0),
    'wide':  dict(label='Wider: 3 W/mK over |y| 2–20, z 23–56 (the whole rail gap)', zones=[(18.0, 25.3, 2.0, 20.0, 23.0, 56.0)], k=3.0),
    'beads': dict(label='Baseline + front-to-back beads in place of the carrier webs', zones=[BASE_ZONE],
                  over=[(-2.0, 2.0, P.PR - 3.0, P.PR + 3.0, 10.0, 74.0)], k=3.0),
    'lid':   dict(label='Baseline + parts side of the stages to the cup wall', zones=[BASE_ZONE, (26.9, 30.6, 4.0, 19.0, 27.0, 53.0)], k=3.0),
}
DENSITY = 3.1                                   # g/cc, typical 3-4 W/mK alumina-filled silicone (GEL 30 3.1, TGF 3600 3.0)

def configure(v):
    o = VARIANTS[v]; P.FILL_ZONES = o['zones']; P.FILL_OVER_PA12 = o.get('over', []); P.K_ISO[P.FILL] = o['k']
    P.GRID_TAG = '_fill_' + v

def run(v, which):
    configure(v); g = P.get_grid()
    if which == 'dis': P.run_case(g, 'dis100', tag=f'_fill_{v}', hours=40/60, verbose=False)
    else:
        P.CASES['chg1']['dt'] = 30; P.run_case(g, 'chg1', tag=f'_fill_{v}', hours=1.5, verbose=False)

def table():
    rows = []
    for v, o in VARIANTS.items():
        configure(v); g = P.get_grid()
        r = dict(variant=v, label=o['label'], k=o['k'], cc=g.fill_cc, grams=g.fill_cc*DENSITY)
        for which, case in (('dis', 'dis100'), ('chg', 'chg1')):
            f = os.path.join(P.OUT_DIR, f'{case}_fill_{v}.npz')
            if not os.path.exists(f) and v == 'base': f = os.path.join(P.OUT_DIR, f'{case}.npz')   # the main run is the baseline
            if not os.path.exists(f): continue
            z0 = np.load(f); t = z0['rec_t']; keep = t <= (40 if which == 'dis' else 90)
            z = {k: z0[k][keep] for k in z0.files if k.startswith('rec_')}; t = z['rec_t']; dt = (t[1] - t[0])*60
            if which == 'dis':
                p = z['rec_p_out']; full = np.nonzero(p < 99)[0]
                r.update(min_full=float(t[full[0]] if len(full) else t[-1]), wh_40=float(p.sum()*dt/3600),
                         surf=float(z['rec_surf_max'].max()), ntc=float(z['rec_ntc'].max()), part=float(z['rec_part_max'].max()),
                         spread=float((z['rec_cell_mean'].max(1) - z['rec_cell_mean'].min(1)).max()),
                         within=float((z['rec_cell_max'] - z['rec_cell_min']).max()))
            else:
                ic = z['rec_i_chg']; soc = z['rec_soc']
                r.update(chg_soc_60=float(soc[t <= 60][-1]), chg_ah_90=float(ic.sum()*dt/3600), chg_surf=float(z['rec_surf_max'].max()),
                         chg_part=float(z['rec_part_max'].max()), chg_i_min=float(ic[t > 5].min()))
        rows.append(r)
    os.makedirs(os.path.join(P.HERE, 'renders'), exist_ok=True)
    json.dump(rows, open(os.path.join(P.HERE, 'renders', 'fill.json'), 'w'), indent=1)
    for r in rows: print(json.dumps({k: (round(x, 2) if isinstance(x, float) else x) for k, x in r.items()}))

if __name__ == '__main__':
    if sys.argv[1:] == ['table']: table()
    else:
        for a in sys.argv[1:]:
            v, which = a.split(':'); run(v, which)
