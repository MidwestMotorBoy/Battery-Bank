"""Inner copper weight study (Logan, 2026-11-05): 0.5 oz (as ordered) vs 1 oz vs 2 oz inner layers, outer 2 oz.
Each weight changes (a) routed-copper I2R (cu_oz<w>.json, DC grid solver on master 8081416) and
(b) board in-plane conductivity K_BOARD_IN = 38 W/mK * (2*70 + 4*t_inner) / 210 um.
Same rev7 setup as run.py (d44 policy, TH101/TH104 at out29, 25 C).
python run_oz.py [cases] [weights] [amb]  -> results/p0f/<case>_oz<w>[_amb35].npz ; then python analyze_oz.py"""
import os, sys, time, json
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('SMD_LAYOUT', 'p0f')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('CU_JSON', os.path.join(HERE, 'cu_oz0.5.json'))
import cu as C
P, S, N = C.P, C.S, C.N
K0 = 38.0
def kin(w): return K0 * (2*70 + 4*35*w) / 210.0

def setup(w):
    C.CU = json.load(open(os.path.join(HERE, f'cu_oz{w:g}.json')))
    C.RB = 0.5 * (C.CU['cub1']['R'] + C.CU['cub2']['R']); C.RU = 0.5 * (C.CU['cuu1']['R'] + C.CU['cuu2']['R'])
    P.K_BOARD_IN = kin(w); P.GRID_TAG = '' if w == 0.5 else f'_kin{kin(w):.1f}'

def job(spec):
    case, w, amb, hours = spec
    setup(w); C.ON[0] = True
    P.DERATE, P.DERATE_HOT, P.CHG_HOT = S.POLICIES['d44']
    g = P.get_grid(); S.use_spot('out29')
    tag = f'_oz{w:g}' + ('' if amb == 25 else f'_amb{amb:.0f}')
    P.run_case(g, case, verbose=False, tag=tag, amb=amb, hours=hours, probes=S.spot_points(), ntc_front=N.SPOT)
    return spec

if __name__ == '__main__':
    cases = sys.argv[1].split(',') if len(sys.argv) > 1 else ['dis100', 'dis100u2']
    ws = [float(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else [0.5, 1.0, 2.0]
    amb = float(sys.argv[3]) if len(sys.argv) > 3 else 25.0
    hours = float(os.environ['HOURS']) if 'HOURS' in os.environ else None
    for w in ws:                         # build each grid once, before the pool (K_BOARD_IN lives in the cached grid)
        setup(w); t0 = time.time(); P.get_grid(); print(f'grid oz{w:g} K_in {kin(w):.1f} ready {time.time()-t0:.0f} s', flush=True)
    specs = [(c, w, amb, hours) for w in ws for c in cases]
    import multiprocessing as mp
    with mp.get_context('spawn').Pool(int(os.environ.get('NPROC', '6')), maxtasksperchild=1) as pl:
        for r in pl.imap_unordered(job, specs): print(r, 'done', time.strftime('%H:%M:%S'), flush=True)
