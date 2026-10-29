"""Board-mounted SMD NTCs for TS1 / TS4 instead of the wired beads on the can (2026-10-28).
1. probes: run the main cases with today's policy (p42c, wired NTC on the stripe) and record the board's B.Cu temperature
   at candidate SMD spots over each front cell, next to the stripe spot and the hottest can point.
2. seq: 100 W to empty, then straight onto one 100 W charger (the cool-down case a board sensor could get wrong).
3. policy: rerun the cases with the front NTCs on the board at the best spot and shifted thresholds.
Run: python smd.py probes | seq | policy [pol=s46,s50] | table     -> results/smd_*.npz, renders/smd.json"""
import os, sys, json, time
os.environ.setdefault('OMP_NUM_THREADS', '1')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pack3d as P
import ntc as N

# SMD_LAYOUT=p0: the port-1 stage where it sits on the Production board today (2026-10-28, KiCad x = 100 + y, y = 141.47 - z):
# Q401 / Q402 SiZ240DT at (10.4, 50.3) / (10.3, 44.0), L401 at (4.3, 47.1), U403 BQ25756 at (17.4, 45.8), R424 (AC sense) at
# (11.2, 60.8). The battery-side sense resistor and port 2 aren't placed yet: RBAT is put beside the FETs, port 2 mirrored onto C1.
LAYOUT = os.environ.get('SMD_LAYOUT', '')
def p0_src_boxes():
    b = _orig_src_boxes()
    for p in (1, 2):
        s = 1 if p == 1 else -1
        def bx(y, z, hy, hz, x1=27.8): y = s*y; return (26.9, x1, y - hy, y + hy, z - hz, z + hz)
        b[f'fet{p}'] = [bx(10.4, 50.26, 1.65, 1.65), bx(10.32, 44.01, 1.65, 1.65)]
        b[f'ind{p}'] = [bx(4.27, 47.12, 3.5, 3.5, 30.0)]
        b[f'ic{p}'] = [bx(17.36, 45.83, 2.5, 3.0, 27.7)]
        b[f'sense{p}'] = [bx(11.23, 60.83, 2.5, 1.3, 27.5), bx(14.3, 54.5, 1.6, 0.8, 27.5)]
    return b
# SMD_LAYOUT=p0b: the same after Logan's 10-27 "Layout in progress" commit (ed56285): Q401 / Q402 at (9.6, 41.7) / (14.1, 41.6),
# L401 at (11.8, 48.9), U403 at (11.4, 31.0) turned 90 deg, RBAT R427 at (18.2, 36.5). R424 (AC sense) is still off the board:
# put beside L401 at (9.0, 54.5). Port 2 is still off the board and stays mirrored onto C1.
def p0b_src_boxes():
    b = _orig_src_boxes()
    for p in (1, 2):
        s = 1 if p == 1 else -1
        def bx(y, z, hy, hz, x1=27.8): y = s*y; return (26.9, x1, y - hy, y + hy, z - hz, z + hz)
        b[f'fet{p}'] = [bx(9.56, 41.66, 1.65, 1.65), bx(14.08, 41.62, 1.65, 1.65)]
        b[f'ind{p}'] = [bx(11.81, 48.86, 3.5, 3.5, 30.0)]
        b[f'ic{p}'] = [bx(11.44, 30.97, 3.0, 2.5, 27.7)]
        b[f'sense{p}'] = [bx(18.17, 36.48, 0.8, 1.6, 27.5), bx(9.0, 54.5, 1.0, 0.65, 27.5)]
    return b
_orig_src_boxes = P.src_boxes
if LAYOUT in ('p0', 'p0b'):
    P.src_boxes = p0_src_boxes if LAYOUT == 'p0' else p0b_src_boxes
    P.OUT_DIR = os.path.join(P.HERE, 'results', 'p0layout' if LAYOUT == 'p0' else 'p0b')

X_BCU, X_FCU = 25.8, 26.4                 # board voxels: the B.Cu half (board is x 25.3-26.9) and the F.Cu half
SPOTS = {                                  # name: (x, |y|, z) on the board, mirrored onto C1 (-y) and C4 (+y)
    'stripe':  (X_BCU, 12.9, 48.0),        # B.Cu straight over the wired bead's spot (under the stage FETs)
    'tangent': (X_BCU, 11.6, 44.0),        # B.Cu on the board-facing line, closest to the can
    'zone_lo': (X_BCU, 13.5, 30.0),        # B.Cu at the bottom of the filler zone, under the BQ25756
    'edge':    (X_BCU, 15.5, 40.0),        # B.Cu at the outer edge of the filler zone
    'below':   (X_BCU, 13.5, 24.0),        # B.Cu just below the filler zone (air gap to the can)
    'above':   (X_BCU, 12.9, 57.0),        # B.Cu just above the filler zone
    'pads':    (X_BCU, 14.7, 66.0),        # B.Cu where J102 / J107 are today
    'low28':   (X_BCU, 12.9, 28.5),        # B.Cu at the bottom end of the filler zone, on the stripe line
    'low33':   (X_BCU, 12.9, 33.0),
    'low38':   (X_BCU, 12.9, 38.0),
    'out29':   (X_BCU, 15.5, 29.0),        # filler zone bottom, outboard of U403 in the p0b layout
    'in29':    (X_BCU, 7.5, 29.0),         # filler zone bottom, inboard of U403
    'z26':     (X_BCU, 12.9, 26.0),        # just below the filler zone
    'z20':     (X_BCU, 13.5, 20.0),
    'stripe_f': (X_FCU, 12.9, 48.0),       # F.Cu side of the stripe spot
}
def spot_points():
    pts = []
    for k in P.FRONT:
        s = np.sign(P.CELLS[k][2])
        pts += [(x, s*y, z) for x, y, z in SPOTS.values()]
        pts.append(P.can_point(k, *N.SPOT))                       # the wired bead's spot (today's design)
    return pts
NAMES = list(SPOTS) + ['wired']
CASES = {'dis100': None, 'dis60': None, 'dis30': None, 'chg1': None, 'pass': None, 'dis100x2': None}

POLICIES = {    # name: (DERATE, DERATE_HOT, CHG_HOT) on the hottest TS reading, as ntc.POLICIES
    'p42c': N.POLICIES['p42c'],
    's46':  ((46.0, 50.0, 40.0), (54.0, 62.0), (46.0, 48.5)),   # +4 K
    's48':  ((48.0, 52.0, 40.0), (56.0, 62.0), (48.0, 50.5)),   # +6 K
    's50':  ((50.0, 54.0, 40.0), (58.0, 62.0), (50.0, 52.5)),   # +8 K
    's43':  ((43.0, 47.0, 40.0), (51.0, 59.0), (43.0, 45.5)),   # +1 K
    'd44':  ((44.0, 48.0, 40.0), (52.0, 59.0), (42.0, 44.5)),   # discharge ramp +2 K, charge ramp as p42c
}

def probe_job(case):
    P.DERATE, P.DERATE_HOT, P.CHG_HOT = N.POLICIES['p42c']
    g = P.get_grid()
    P.run_case(g, case, verbose=False, tag='_smdprobe', probes=spot_points(), ntc_front=N.SPOT)
    return case

def seq_job(spec):
    """100 W to empty, then one 100 W charger at once, with policy `pol` and the front NTCs `ntc` ('wired' or a spot)"""
    pol, ntc = spec
    P.DERATE, P.DERATE_HOT, P.CHG_HOT = POLICIES[pol]
    g = P.get_grid(); use_spot(ntc)
    a = f'_smdseq_{pol}_{ntc}'
    P.run_case(g, 'dis100', verbose=False, tag=a + '_a', probes=spot_points(), ntc_front=N.SPOT)
    z = np.load(os.path.join(P.OUT_DIR, 'dis100' + a + '_a.npz'))
    P.run_case(g, 'chg1', verbose=False, tag=a + '_b', probes=spot_points(), ntc_front=N.SPOT, hours=3.0,
               th0=z['snap_end'][...], soc0=float(z['rec_soc'][-1]))
    return spec

_orig_ntc_points = P.ntc_points
def use_spot(ntc):
    """front NTCs on the board at SPOTS[ntc] (or the wired spot for 'wired')"""
    if ntc == 'wired': P.ntc_points = _orig_ntc_points; return
    def pts(g, ntc_front=None):
        p, alt = _orig_ntc_points(g, ntc_front)
        for k in P.FRONT:
            x, y, z = SPOTS[ntc]; p[k] = P.vox(g, (x, np.sign(P.CELLS[k][2])*y, z))
        return p, alt
    P.ntc_points = pts

def policy_job(spec):
    case, pol, ntc, amb = spec
    P.DERATE, P.DERATE_HOT, P.CHG_HOT = POLICIES[pol]
    g = P.get_grid(); use_spot(ntc)
    P.run_case(g, case, verbose=False, tag=f'_smd_{pol}_{ntc}' + ('' if amb == 25 else f'_amb{amb:.0f}'), amb=amb,
               probes=spot_points(), ntc_front=N.SPOT)
    return spec

def lambda_free_job(spec):
    kind, a = spec
    return (policy_job if kind == 'policy' else seq_job)(a)

def load(name): return np.load(os.path.join(P.OUT_DIR, name + '.npz'))

def bias(z):
    """per spot: reading minus the hottest can point of the same front cell, (max, min, at the can peak), worst cell"""
    pr, sm, t = z['rec_probe'], z['rec_surf_max'], z['rec_t']
    hot = int(np.argmax(sm.max(1))); out = {}
    for j, n in enumerate(NAMES):
        d = np.stack([pr[:, i*len(NAMES) + j] - sm[:, k] for i, k in enumerate(P.FRONT)], 1)   # (t, 2)
        late = t > 3                                                    # skip the first minutes from a cold start
        out[n] = dict(max=float(d[late].max()), min=float(d[late].min()), at_peak=float(d[hot].max()),
                      c4_at_peak=float(d[hot, 1]), c1_at_peak=float(d[hot, 0]))
    return out

def run_row(z, case):
    t = z['rec_t']; dt = t[1] - t[0]; p = z['rec_p_out']; m40 = t <= 40; full = np.nonzero(p < 99)[0]
    r = dict(t_end=float(t[-1]), surf_max=float(z['rec_surf_max'].max()), ntc_max=float(z['rec_ntc'].max()),
             part_max=float(z['rec_part_max'].max()), skin_max=float(z['rec_skin_max'].max()))
    if case.startswith('dis'):
        r.update(min_full=float(t[full[0]]) if len(full) else float(t[-1]), wh_40=float(p[m40].sum()*dt/60), wh_total=float(p.sum()*dt/60))
    else:
        soc = z['rec_soc']; r.update(soc_end=float(soc[-1]))
        hit = np.nonzero(soc >= 0.95 - 1e-6)[0]; r.update(min_to_95=float(t[hit[0]]) if len(hit) else None)
        chg = z['rec_i_chg'] > 0.1                                       # hottest can while current flows
        r.update(surf_max_charging=float(z['rec_surf_max'][chg].max()) if chg.any() else None)
    return r

if __name__ == '__main__':
    what = sys.argv[1:] or ['table']
    P.get_grid()
    if 'probes' in what: N.pool_run(probe_job, list(CASES))
    if 'seq' in what:
        sq = [a.split('=')[1].split(':') for a in what if a.startswith('seq=')]
        N.pool_run(seq_job, [tuple(sq[0])] if sq else [('p42c', 'wired'), ('s48', 'stripe')])
    if 'policy' in what:
        pols = [a.split('=')[1].split(',') for a in what if a.startswith('pol=')]
        pols = pols[0] if pols else ['s46', 's48', 's50']
        spot = [a.split('=')[1] for a in what if a.startswith('spot=')] or ['stripe']
        N.pool_run(policy_job, [(c, p, spot[0], 25.0) for p in pols for c in ('dis100', 'chg1', 'pass')])
    if 'amb' in what:
        N.pool_run(policy_job, [('dis100', 'p42c', 'wired', 35.0), ('dis100', 's48', 'stripe', 35.0),
                                ('chg1', 'p42c', 'wired', 35.0), ('chg1', 's48', 'stripe', 35.0)])
    if 'p0' in what:          # SMD_LAYOUT=p0 python smd.py p0
        N.pool_run(probe_job, ['dis100', 'chg1', 'pass', 'dis30'])
        N.pool_run(policy_job, [(c, p, 'low28', 25.0) for p in ('p42c', 's43') for c in ('dis100', 'chg1', 'pass')])
        N.pool_run(seq_job, [('s43', 'low28')])
    if 'p0c' in what:         # the p0b layout's best spot, today's thresholds
        N.pool_run(lambda_free_job, [('policy', ('dis100', 'p42c', 'out29', 25.0)), ('policy', ('chg1', 'p42c', 'out29', 25.0)),
                                     ('policy', ('pass', 'p42c', 'out29', 25.0)), ('seq', ('p42c', 'out29'))])
    if 'p0d' in what:
        N.pool_run(lambda_free_job, [('policy', ('dis100', 'd44', 'out29', 25.0)), ('seq', ('d44', 'out29')),
                                     ('policy', ('dis60', 'd44', 'out29', 25.0)), ('policy', ('dis60', 'p42c', 'wired', 25.0))])
    if 'probes4' in what: N.pool_run(probe_job, ['dis100', 'chg1', 'pass', 'dis30'])
    if 'p0b' in what:         # the recommended spot (z 33) with today's thresholds
        N.pool_run(lambda_free_job, [('policy', ('dis100', 'p42c', 'low33', 25.0)), ('policy', ('chg1', 'p42c', 'low33', 25.0)),
                                     ('policy', ('pass', 'p42c', 'low33', 25.0)), ('seq', ('p42c', 'low33'))])
    if 'table' in what:
        res = dict(probes={}, policy=[], seq={})
        for c in CASES:
            f = c + '_smdprobe'
            if os.path.exists(os.path.join(P.OUT_DIR, f + '.npz')):
                z = load(f); res['probes'][c] = dict(bias=bias(z), **run_row(z, c))
        for fn in sorted(os.listdir(P.OUT_DIR)):
            if fn.endswith('.npz') and '_smd_' in fn:
                name = fn[:-4]; case = name.split('_smd_')[0]; z = load(name)
                res['policy'].append(dict(run=name, case=case, bias=bias(z)['stripe'], wired_bias=bias(z)['wired'], **run_row(z, case)))
            if fn.endswith('_b.npz') and '_smdseq_' in fn:
                name = fn[:-4]; z = load(name); a = load('dis100' + name[4:-2] + '_a')
                t = z['rec_t']; i = z['rec_i_chg']; sm = z['rec_surf_max'].max(1); nt = z['rec_ntc'].max(1)
                on = np.nonzero(i > 0.1)[0]
                res['seq'][name] = dict(dis=run_row(a, 'dis100'), chg=run_row(z, 'chg1'), bias=bias(z),
                                        t_first_current=float(t[on[0]]) if len(on) else None,
                                        can_at_first_current=float(sm[on[0]]) if len(on) else None,
                                        ntc_at_first_current=float(nt[on[0]]) if len(on) else None,
                                        can_max_while_charging=float(sm[i > 0.1].max()) if len(on) else None,
                                        can_max_at_full_current=float(sm[i > 4.4].max()) if (i > 4.4).any() else None)
        os.makedirs(os.path.join(P.HERE, 'renders'), exist_ok=True)
        json.dump(res, open(os.path.join(P.HERE, 'renders', f'smd{"_" + LAYOUT if LAYOUT else ""}.json'), 'w'), indent=1)
        for c, r in res['probes'].items():
            print(c, {k: round(v, 1) for k, v in r.items() if isinstance(v, float)})
            for n, b in r['bias'].items(): print(f'   {n:9s}', {k: round(v, 1) for k, v in b.items()})
        for r in res['policy']: print(json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items() if k not in ('bias', 'wired_bias')}),
                                      'bias', {k: round(v, 1) for k, v in r['bias'].items()})
        for n, r in res['seq'].items(): print(n, json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items() if k != 'bias'}))
