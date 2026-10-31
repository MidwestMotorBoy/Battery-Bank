"""Both ports at once (Logan, 2026-10-31): USB1 25 W + USB2 20 W, start full at ambient, still air, run until empty.
Same rev7 setup as run.py / run_load.py: routed-copper losses (cu_losses_rev7.json), d44 policy, TH101/TH104 at out29.
Firmware split as in pack3d.run_case: USB2 keeps up to 20 W, USB1 is cut first when the derate lowers the total.
Cases (kind):
  std   - firmware derate on (the real product)
  nod   - firmware derate and board ramp OFF (what the hardware alone settles to; full discharge)
python run_dual.py [case,...] [kind,...] [amb,...]  -> results/p0f/<case>_<kind>_amb<amb>.npz"""
import os, sys, time
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('SMD_LAYOUT', 'p0f')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault('CU_JSON', os.path.join(HERE, 'cu_losses_rev7.json'))
import cu as C
P, S, N = C.P, C.S, C.N

DUAL = {   # name: (title, USB1 V, USB2 V)
    'dual15': ('USB1 25 W at 15 V + USB2 20 W at 9 V', 15.0, 9.0),
    'dual9':  ('USB1 25 W at 9 V + USB2 20 W at 9 V', 9.0, 9.0),
    'dual20': ('USB1 25 W at 20 V + USB2 20 W at 9 V', 20.0, 9.0),
}
for k, (title, v1, v2) in DUAL.items():
    P.CASES[k] = dict(title=title, ports={1: ('src', 25, v1), 2: ('src', 20, v2)}, soc0=1.0, hours=3.0, dt=10)

def job(spec):
    case, kind, amb = spec
    C.ON[0] = True
    P.DERATE, P.DERATE_HOT, P.CHG_HOT = S.POLICIES['d44']
    if kind == 'nod':
        P.DERATE, P.DERATE_HOT = (500.0, 501.0, 100.0), (600.0, 601.0); P.BOARD_RAMP = (500.0, 501.0)
    g = P.get_grid(); S.use_spot('out29')
    m = P.run_case(g, case, verbose=False, tag=f'_{kind}_amb{amb:.0f}', amb=amb, probes=S.spot_points(), ntc_front=N.SPOT)
    return spec, round(m['t_end'], 1)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cases = sys.argv[1].split(','); kinds = sys.argv[2].split(',') if len(sys.argv) > 2 else ['std']
        ambs = [float(a) for a in sys.argv[3].split(',')] if len(sys.argv) > 3 else [25.0, 35.0]
        specs = [(c, k, a) for c in cases for k in kinds for a in ambs]
    else:   # the default batch: baseline std + nod at 25 / 35 C, plus 40 C std, plus USB1 voltage sensitivity at 25 C
        specs = [('dual15', k, a) for k in ('std', 'nod') for a in (25.0, 35.0)] + [('dual15', 'std', 40.0)] + \
                [(c, 'std', 25.0) for c in ('dual9', 'dual20')]
    P.get_grid()
    import multiprocessing as mp
    with mp.get_context('spawn').Pool(int(os.environ.get('NPROC', '6')), maxtasksperchild=1) as pl:
        for r in pl.imap_unordered(job, specs): print(r, 'done', time.strftime('%H:%M:%S'), flush=True)
