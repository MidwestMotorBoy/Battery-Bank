"""Per pose: the floor force-crush curve of the shell (the 10-31 study's ray-cast bumper model, contact.py) and the
contact tables of every body pair (contacts.py). Parallel over (pose, pair). Run: python tables.py [nproc] [pose ...]
-> cache/tables_<pose>.npz"""
import os, sys, time, pickle, numpy as np, multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'cache')
sys.path.append(os.path.normpath(os.path.join(HERE, '..', '2026-10-31-drop-1m')))   # its contact.py (floor)
import bodies, contacts as C, poses
_W = {}

def pair_list(CP):
    """contact-part pairs on different bodies that come within 1.2 mm (the spacers only against the cup walls)"""
    ks = list(CP); out = []
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            if CP[a][0] == CP[b][0]: continue
            if 'board/spacers' in (a, b) and 'shell/cup_walls' not in (a, b): continue
            if CP[a][1].min_gap(CP[b][1], 2.0) < 1.5: out.append((a, b))
    return out

def _init():
    B, sub, m, prm, A = bodies.build(); _W.update(CP=bodies.contact_parts(B, sub))

def _job(args):
    pose, d, a, b = args
    CP = _W['CP']
    return pose, a, b, C.pair_tables(CP[a][1], CP[b][1], d)

def cg_of(A, mass):
    num, den = np.zeros(3), 0.0
    groups = {}
    for k, V, _ in A: groups.setdefault(k.split('_')[0], []).append(V.reshape(-1, 3))
    for g, Vs in groups.items():
        if g not in mass: continue
        P = np.vstack(Vs); num += mass[g] * (P.min(0) + P.max(0)) / 2; den += mass[g]   # bbox centre per group
    return num / den

def floor_curve(A, d):
    import contact as FC
    FC.MAT['bumpt_slab'] = FC.MAT['bumpb_slab'] = 'gyroid30'
    rc = FC.raycast(A, d)
    dl = np.arange(0, 8.0 + 1e-9, 0.005); F = np.array([FC.layer_pressure(rc, x)[1] for x in dl])
    return dl, F, rc

def main(nproc=4, only=None):
    os.makedirs(CACHE, exist_ok=True)
    B, sub, m, prm, A = bodies.build()
    P_out = np.vstack([V.reshape(-1, 3) for k, V, _ in A if k in ('bumpt_slab', 'bumpt_band', 'bumpb_slab', 'bumpb_band', 'label', 'cup', 'cap', 'screw')])
    cg = cg_of(A, m); D = poses.directions(P_out, cg)
    todo = [p for p in poses.ORDER if not only or p in only]
    CP = bodies.contact_parts(B, sub); pairs = pair_list(CP)
    print(len(pairs), 'contact pairs')
    jobs = [(p, D[p], a, b) for p in todo for a, b in pairs]
    t = time.time(); res = {p: {} for p in todo}
    with mp.Pool(nproc, _init) as pool:
        for i, (p, a, b, tb) in enumerate(pool.imap_unordered(_job, jobs, chunksize=2)):
            res[p][(a, b)] = tb
            if i % 50 == 0: print(f'  {i}/{len(jobs)} pair tables, {time.time() - t:.0f} s', flush=True)
    for p in todo:
        t1 = time.time(); dl, F, rc = floor_curve(A, D[p])
        keep = {k: rc[k] for k in ('gap', 'part', 'thick', 'R', 'origin', 'res', 'shape', 'names', 's0')}
        pickle.dump(dict(pose=p, d=D[p], cg=cg, pairs=res[p], part_body={k: v[0] for k, v in CP.items()}, floor=(dl, F), rc=keep, masses={k: b['mass'] for k, b in B.items()},
                         prm=prm), open(os.path.join(CACHE, f'tables_{p}.pkl'), 'wb'))
        print(f'{p:18s} d {np.round(D[p], 3)}  floor F at 1 mm {np.interp(1.0, dl, F):7.0f} N  ({time.time() - t1:.0f} s)', flush=True)

if __name__ == '__main__':
    a = sys.argv[1:]; n = int(a[0]) if a and a[0].isdigit() else 4
    main(n, [x for x in a if not x.isdigit()] or None)
