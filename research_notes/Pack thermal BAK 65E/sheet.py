"""Graphite heat-spreader wrap round the four-cell bundle, to even out the cell temperatures (Panasonic PGS grades).
Run: python sheet.py VARIANT:CASE [...] -> results/<case>_sheet_<variant>.npz ; python sheet.py table -> renders/sheet.json"""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack3d as P

Z_SHEET = (P.Z_C0 + 3.0, P.Z_C1 - 3.0)          # 65 mm tall, clear of the + caps, the nickel and the carrier frames
VARIANTS = {
    'pgs70': dict(label='70 µm PGS wrap (850 W/m·K), PET-laminated', kt=850*70e-6, grams=1.2),
    'pgs25': dict(label='25 µm PGS wrap (1600 W/m·K), PET-laminated', kt=1600*25e-6, grams=0.8),
}
CASES = ('dis100', 'chg1', 'pass')

def run(v, case):
    P.SHEET = dict(kt=VARIANTS[v]['kt'], z=Z_SHEET)
    P.run_case(P.get_grid(), case, tag=f'_sheet_{v}', verbose=False)

def stats(f):
    z = np.load(f); t = z['rec_t']; dt = t[1] - t[0]
    win = (z['rec_cell_max'] - z['rec_cell_min']).max(1); cm = z['rec_cell_mean']; c2c = cm.max(1) - cm.min(1)
    on = (z['rec_p_out'] + z['rec_p_in']) > 1; p = z['rec_p_out']; full = np.nonzero(p < 99)[0]
    return dict(t_end=float(t[-1]), within_max=float(win.max()), within_avg=float(win[on].mean()), within_min5=float((win > 5).sum()*dt),
                c2c_max=float(c2c.max()), c2c_avg=float(c2c[on].mean()), c2c_min5=float((c2c > 5).sum()*dt),
                can=float(z['rec_surf_max'].max()), ntc=float(z['rec_ntc'].max()), part=float(z['rec_part_max'].max()),
                skin=float(z['rec_skin_max'].max()), min_full=float(t[full[0]]) if len(full) else float(t[-1]),
                soc_end=float(z['rec_soc'][-1]))

def table():
    rows = []
    for v, o in [('none', dict(label='No wrap (design as specified)', grams=0.0))] + list(VARIANTS.items()):
        for case in CASES:
            f = os.path.join(P.OUT_DIR, f'{case}.npz' if v == 'none' else f'{case}_sheet_{v}.npz')
            if os.path.exists(f): rows.append(dict(variant=v, label=o['label'], grams=o['grams'], case=case, **stats(f)))
    json.dump(rows, open(os.path.join(P.HERE, 'renders', 'sheet.json'), 'w'), indent=1)
    for r in rows: print(json.dumps({k: (round(x, 1) if isinstance(x, float) else x) for k, x in r.items()}))

if __name__ == '__main__':
    if sys.argv[1:] == ['table']: table()
    else:
        for a in sys.argv[1:]: run(*a.split(':'))
