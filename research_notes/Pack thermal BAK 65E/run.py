"""rev7 runs: 100 W out of USB1 / USB2 alone with routed-copper losses (cu_losses_rev7.json), d44 policy, TH101/TH104 at out29.
python run.py std|amb35|nod ...   -> results/p0f/<case>_rev7_<tag>.npz"""
import os, sys, time
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('SMD_LAYOUT', 'p0f')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('CU_JSON', os.path.join(HERE, 'cu_losses_rev7.json'))
import cu as C
P, S, N = C.P, C.S, C.N

def job(spec):
    case, kind = spec
    C.ON[0] = True
    P.DERATE, P.DERATE_HOT, P.CHG_HOT = S.POLICIES['d44']
    amb, hours = 25.0, None
    if kind == 'amb35': amb = 35.0
    if kind.startswith('nod'):                     # firmware derate failed: no cell derate, no board ramp, 10 min
        P.DERATE, P.DERATE_HOT = (500.0, 501.0, 100.0), (600.0, 601.0); P.BOARD_RAMP = (500.0, 501.0); hours = 10/60
        if kind == 'nod35': amb = 35.0
    g = P.get_grid(); S.use_spot('out29')
    P.run_case(g, case, verbose=False, tag=f'_rev7_{kind}', amb=amb, hours=hours, probes=S.spot_points(), ntc_front=N.SPOT)
    return spec

if __name__ == '__main__':
    kinds = sys.argv[1:] or ['std']
    P.get_grid()
    specs = [(c, k) for k in kinds for c in ('dis100', 'dis100u2')]
    import multiprocessing as mp
    with mp.get_context('spawn').Pool(int(os.environ.get('NPROC', '4')), maxtasksperchild=1) as pl:
        for r in pl.imap_unordered(job, specs): print(r, 'done', time.strftime('%H:%M:%S'), flush=True)
