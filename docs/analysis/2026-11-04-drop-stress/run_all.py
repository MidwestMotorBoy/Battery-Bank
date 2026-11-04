"""The whole contact drop study, pose by pose, in parallel:
  1. contact tables (tables.py) if missing
  2. impact with rigid shell / carrier (dyn.py) -> out/dyn_<pose>_rigid.json
  3. FE compliance of every cup / cap patch (fe_shell.py) and of the carrier where it meets the shell (fe_core.py)
  4. impact again with those springs (dyn.py) -> out/dyn_<pose>.json
  5. FE stress at the peak: cup + cap, carrier, each rail block -> out/{shell,carrier,rails_xx}_<pose>.json
  6. the board as a plate against its stops (board_dyn.py) -> out/board_<pose>.json; then checks.py -> out/checks.json
Run: python run_all.py [--nproc N] [--h 0.75] [pose ...]   (H = shell mesh, carrier H, rail blocks H / 2)
About 2 GB of memory per worker at H 0.75, 3-4 GB at H 0.5."""
import os, sys, json, time, argparse, numpy as np, multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'cache'); OUT = os.path.join(HERE, 'out')
_M = {}

def models(H):
    import fe_shell, fe_core
    if 'shell' not in _M:
        _M['shell'] = fe_shell.build_model(H)
        _M['carrier'] = fe_core.build_model('carrier', H)
        for r in fe_core.PARTS:
            if r != 'carrier': _M[r] = fe_core.build_model(r, H / 2)
        for k in ['shell', 'carrier'] + [r for r in fe_core.PARTS if r != 'carrier']:          # element centres for figs.py
            p = os.path.join(CACHE, f'{k}_grid_H{H}.npz')
            if not os.path.exists(p): np.savez_compressed(p, Xe=_M[k].Xe, elab=_M[k].elab, labels=np.array(_M[k].g['labels']))
    return _M

def one(args):
    pose, H = args
    import dyn, fe_shell, fe_core
    t0 = time.time(); M = models(H); log = []
    dyn.run(pose, use_structure=False, tag='_rigid')
    for f in (f'shellc_{pose}.json', f'corec_{pose}.json'):
        p = os.path.join(CACHE, f)
        if os.path.exists(p): os.remove(p)
    # the compliance passes read cache/dyn_<pose>.npz: start from the rigid run
    dyn.run(pose, use_structure=False)
    T = dyn.load(pose); S = json.load(open(os.path.join(OUT, f'dyn_{pose}.json')))
    springs = fe_shell.floor_springs(M['shell'], T, S['crush_mm'])
    C = fe_shell.compliance(M['shell'], T, S, springs)
    json.dump(C, open(os.path.join(CACHE, f'shellc_{pose}.json'), 'w'), indent=1)
    C2 = fe_core.compliance(M['carrier'], T, S)
    json.dump(C2, open(os.path.join(CACHE, f'corec_{pose}.json'), 'w'), indent=1)
    S, R, c = dyn.run(pose)
    springs = fe_shell.floor_springs(M['shell'], T, S['crush_mm'])
    r = fe_shell.stress(M['shell'], T, S, springs); json.dump(r, open(os.path.join(OUT, f'shell_{pose}.json'), 'w'), indent=1)
    for part in fe_core.PARTS:
        r = fe_core.stress(M[part], T, S, part)
        if r: json.dump(r, open(os.path.join(OUT, f'{part}_{pose}.json'), 'w'), indent=1)
    import board_dyn
    if 'board' not in _M: _M['board'] = board_dyn.setup()
    r = board_dyn.run(pose, _M['board'])
    if r: json.dump(r, open(os.path.join(OUT, f'board_{pose}.json'), 'w'), indent=1)
    return pose, round(time.time() - t0)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--nproc', type=int, default=4); ap.add_argument('--h', type=float, default=0.75)
    ap.add_argument('poses', nargs='*'); a = ap.parse_args()
    import dyn, tables
    todo = a.poses or dyn.poses.ORDER
    missing = [p for p in todo if not os.path.exists(os.path.join(CACHE, f'tables_{p}.pkl'))]
    if missing: tables.main(min(a.nproc, 8), missing)
    import board_dyn; board_dyn.flex()                  # cache/board_flex.json once, before the workers read it
    t = time.time()
    with mp.Pool(min(a.nproc, len(todo)), maxtasksperchild=None) as pool:
        for pose, dt in pool.imap_unordered(one, [(p, a.h) for p in todo]):
            print(f'=== {pose} done in {dt} s ({time.time() - t:.0f} s total)', flush=True)
    json.dump(dict(h=a.h, poses=todo, finished=time.strftime('%Y-%m-%d %H:%M:%S')), open(os.path.join(OUT, 'run_all.json'), 'w'))
    import checks; checks.main()

if __name__ == '__main__': main()
