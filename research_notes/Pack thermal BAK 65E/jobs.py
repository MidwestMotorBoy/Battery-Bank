"""Run every model job on all cores: the main cases, the gap-filler options, then the sensitivity runs.
Run: python jobs.py [main|fill|sens ...]"""
import os, sys, time, multiprocessing as mp
os.environ.setdefault('OMP_NUM_THREADS', '1')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def job(spec):
    import pack3d as P, fill, sens
    kind, a = spec[0], spec[1:]
    t0 = time.time()
    if kind == 'main': g = P.get_grid(); P.run_case(g, a[0], verbose=False)
    elif kind == 'fill': fill.run(*a)
    elif kind == 'sens': sens.run(a[0])
    return f'{spec} done in {time.time() - t0:.0f} s'

if __name__ == '__main__':
    import pack3d as P, fill, sens
    P.get_grid()                                              # build the baseline cache once
    for v in fill.VARIANTS: fill.configure(v); P.get_grid()   # and each filler grid
    groups = sys.argv[1:] or ['main', 'fill', 'sens']
    specs = []
    if 'main' in groups: specs += [('main', n) for n in ('dis100', 'dis100x2', 'dis60', 'dis30', 'pass', 'chg1', 'chg2', 'idle')]
    if 'fill' in groups: specs += [('fill', v, w) for v in fill.VARIANTS if v != 'base' for w in ('dis', 'chg')]
    if 'sens' in groups: specs += [('sens', v) for v in sens.VARIANTS]
    with mp.get_context('spawn').Pool(4, maxtasksperchild=1) as pool:
        for r in pool.imap_unordered(job, specs): print(r, flush=True)
