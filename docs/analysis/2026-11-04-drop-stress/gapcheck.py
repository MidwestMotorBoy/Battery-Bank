"""First-touch gaps (mm) between every pair of bodies along the six axis directions: the model's check of the design gaps."""
import json, time, numpy as np, bodies, contacts as C
def pairs(B, sub):
    mov = [k for k in B if k != 'shell']; out = []
    for i, a in enumerate(mov):
        for b in mov[i + 1:]:
            if B[a]['m'].min_gap(B[b]['m'], 2.0) < 1.2: out.append((a, b))
        for s in sub:
            if B[a]['m'].min_gap(sub[s], 2.0) < 1.2: out.append((a, 'shell/' + s))
    return out
def solid(B, sub, k, other=None):
    if k == 'board' and other == 'shell/cup_walls': return B[k]['m_wall']
    return sub[k[6:]] if k.startswith('shell/') else B[k]['m']
if __name__ == '__main__':
    B, sub, m, prm, A = bodies.build(); P = pairs(B, sub); t = time.time()
    dirs = {'+x': (1, 0, 0), '-x': (-1, 0, 0), '+y': (0, 1, 0), '-y': (0, -1, 0), '+z': (0, 0, 1), '-z': (0, 0, -1)}
    res = {}
    for a, b in P:
        row = {}
        for n, d in dirs.items():
            g = C.first_gap(solid(B, sub, a, b), solid(B, sub, b, a), d)
            row[n] = None if g is None else round(g, 3)
        res[f'{a} -> {b}'] = row
        print(f'{a:8s} -> {b:16s}', '  '.join(f"{n} {'  -  ' if v is None else f'{v:5.3f}'}" for n, v in row.items()), flush=True)
    json.dump(res, open('out/gaps.json', 'w'), indent=1); print(f'{time.time() - t:.0f} s')
