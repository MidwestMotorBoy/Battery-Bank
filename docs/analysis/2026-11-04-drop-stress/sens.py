"""How much the impact results move with the estimated inputs: the contact stiffness K_W (x0.5, x2), the cells' own
stiffness (x0.5, x2), the contact damping (5 %, 20 %), and a 1.5 m drop. Impact model only (dyn.py), with the
structure's springs from the last run_all.py if they are in cache/. -> out/sensitivity.json
Run: python sens.py [pose ...]   (default: the four poses that load the parts most)"""
import os, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out')
import dyn

KEYS = {   # quantity: contacts whose peaks are summed
    'OT posts (N)': lambda a, b: b == 'shell/ot_posts',
    'cradles (N)': lambda a, b: b == 'shell/cradles',
    'lips (N)': lambda a, b: b == 'shell/lips',
    'board parts on the wall (N)': lambda a, b: a == 'board/parts',
    'rail tongues (ends) (N)': lambda a, b: a.startswith('C') and b.endswith('/ends'),
    'carrier frames on cap skirt (N)': lambda a, b: a == 'carrier/frames' and b == 'shell/cap',
}

def one(pose, k_w=dyn.K_W, k_series=None, **kw):
    T = dyn.load(pose); cs, u = dyn.build_contacts(T, k_w, k_series, True)
    R = dyn.simulate(T, cs, u, **kw); S = dyn.summary(T, cs, R)
    out = dict(floor_kN=round(S['floor_peak_N'] / 1e3, 2), shell_g=round(S['bodies']['shell']['peak_g']),
               cell_g=round(max(S['bodies'][c]['peak_g'] for c in dyn.CELLS)),
               max_cell_contact_N=round(max([c['peak_N'] for c in S['contacts'] if c['a'] in dyn.CELLS] or [0])))
    for k, f in KEYS.items(): out[k] = round(sum(c['peak_N'] for c in S['contacts'] if f(c['a'], c['b'])))
    return out

VARIANTS = {
    'base': {},
    'K_W x0.5': dict(k_w=dyn.K_W / 2), 'K_W x2': dict(k_w=dyn.K_W * 2),
    'cells x0.5': dict(k_series=dict(cell_radial=dyn.K_SERIES['cell_radial'] / 2, cell_axial=dyn.K_SERIES['cell_axial'] / 2)),
    'cells x2': dict(k_series=dict(cell_radial=dyn.K_SERIES['cell_radial'] * 2, cell_axial=dyn.K_SERIES['cell_axial'] * 2)),
    'damping 5 %': dict(zeta=0.05), 'damping 20 %': dict(zeta=0.20),
    '1.5 m': dict(v0=float(np.sqrt(2 * 9.81 * 1.5))),
}

if __name__ == '__main__':
    todo = sys.argv[1:] or ['board', 'bottom', 'side', 'top_board']
    res = {}
    for p in todo:
        res[p] = {}
        for name, kw in VARIANTS.items():
            res[p][name] = one(p, **kw); print(p, name, res[p][name], flush=True)
    json.dump(res, open(os.path.join(OUT, 'sensitivity.json'), 'w'), indent=1)
