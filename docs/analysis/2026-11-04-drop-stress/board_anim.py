"""Board-flex animation data: reruns the board plate (board_dyn.py) for the drops with an x part, records its shape
every 10 us, and writes it on a regular grid for the animated page (cache/board_anim_data.json, not committed) and the
page cache/board-flex.html from board_anim.tmpl.html.
Per frame: the board's deflection (um, + toward the board-face wall) and surface strain (10 ue) on a 1 mm grid, the
support forces, the front cans' travel, and the closest F.Cu / B.Cu parts.
Run after run_all.py: python board_anim.py [pose ...]   (default: board back)"""
import os, sys, json, base64, numpy as np
import matplotlib.tri as mtri
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'cache')
import board_dyn as BD, bodies
BF = BD.BF
STEP = 1.0                                    # mm grid
GROUP = {'spacer': 'Post spacers', 'lip': 'F.Cu lips', 'usb_f': 'USB-C housings (wall side)',
         'usb_b': 'USB-C housings (cell side)', 'rail': 'Rail blocks (core push)'}

def b64(a): return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()

def parts_geometry():
    """every part with its footprint and height off its board face, from the real board (B.Cu caps at their BOM height)"""
    RB = bodies.P.real_board(); xb0 = BF.X_F - BF.T; out = []
    for k, V in RB.items():
        if k.startswith('_') or k == 'PCB' or str(RB.get('_model_' + k, '')).startswith(('Peg_', 'SolderWire')): continue
        P = V.reshape(-1, 3); side = 'F' if P[:, 0].mean() > BF.X_F - 0.8 else 'B'
        h = P[:, 0].max() - BF.X_F if side == 'F' else xb0 - P[:, 0].min()
        if h <= 0.05: continue
        out.append(dict(ref=k, side=side, y0=round(float(P[:, 1].min()), 2), y1=round(float(P[:, 1].max()), 2),
                        z0=round(float(P[:, 2].min()), 2), z1=round(float(P[:, 2].max()), 2), h=round(float(h), 2)))
    return out

def main(poses):
    B = BD.setup(); P = B['P']; tri = B['m'].t
    T = mtri.Triangulation(P[0], P[1], tri.T); finder = T.get_trifinder()
    ys = np.arange(np.floor(P[0].min()), P[0].max() + 1e-6, STEP); zs = np.arange(np.floor(P[1].min()), P[1].max() + 1e-6, STEP)
    Y, Z = np.meshgrid(ys, zs); inside = finder(Y, Z) >= 0
    # element -> vertex averaging matrix for the strain
    nv = P.shape[1]; cnt = np.bincount(tri.ravel(), minlength=nv)
    parts = parts_geometry(); pmap = {p['ref']: p for p in parts}
    sup = []
    for i, (kind, n, k, gap, sgn) in enumerate(B['sup']):
        sup.append(dict(kind=kind.split(':')[0], ref=kind.split(':')[1] if kind.startswith('bcu:') else None,
                        y0=round(float(P[0, n].min()), 2), y1=round(float(P[0, n].max()), 2),
                        z0=round(float(P[1, n].min()), 2), z1=round(float(P[1, n].max()), 2), gap=float(gap)))
    out = dict(step=STEP, ny=len(ys), nz=len(zs), y0=float(ys[0]), z0=float(zs[0]), inside=b64(inside.astype(np.uint8)),
               geom=dict(X_F=BF.X_F, T=BF.T, X_IN=BF.X_IN, PR=bodies.K.PR, CR=bodies.K.CR,
                         z_cell=[bodies.S.sb_z_cell0, bodies.S.sb_z_cell1]),
               parts=parts, supports=sup, poses={})
    for pose in poses:
        rec = []
        r = BD.run(pose, B, record=rec, rec_every=200)                       # 200 x 0.05 us = 10 us
        if r is None: continue
        W, curv = B['W'], B['curv']
        wg, eg, frames = [], [], []
        for s in rec:
            w = W @ s['q']
            kxx, kyy, kxy = np.tensordot(s['q'], curv, axes=(0, 0)); rr = np.sqrt((0.5 * (kxx - kyy))**2 + kxy**2)
            kmax = np.maximum(np.abs(0.5 * (kxx + kyy) + rr), np.abs(0.5 * (kxx + kyy) - rr)); e_el = kmax * BF.T / 2 * 1e6
            ev = np.zeros(nv); np.add.at(ev, tri.ravel(), np.repeat(e_el, 3)); ev /= np.maximum(cnt, 1)
            wi = mtri.LinearTriInterpolator(T, w)(Y, Z).filled(0.0); ei = mtri.LinearTriInterpolator(T, ev)(Y, Z).filled(0.0)
            wg.append(np.clip(np.round(wi * 1000), -32000, 32000).astype(np.int16))
            eg.append(np.clip(np.round(ei / 10), 0, 65000).astype(np.uint16))
            # closest parts to the wall (F) and to the cans (B), at their footprint's highest / lowest point
            cf, cb = (9, None), (9, None)
            for p in parts:
                sel = inside & (Y >= p['y0']) & (Y <= p['y1']) & (Z >= p['z0']) & (Z <= p['z1'])
                if not sel.any():
                    j = np.argmin((Y - (p['y0'] + p['y1']) / 2)**2 + (Z - (p['z0'] + p['z1']) / 2)**2); sel = np.zeros_like(inside); sel.flat[j] = True
                if p['side'] == 'F':
                    c = BF.X_IN + BD.POCKET.get(p['ref'], 0) - (BF.X_F + p['h'] + wi[sel].max())   # L401 / L501 sit under wall pockets
                    if c < cf[0]: cf = (c, p['ref'])
            frames.append(dict(t=round(s['t'] * 1e6, 1), g=round(float(s['a_g'])), uc=round(max(s['uc'].values()), 3),
                               F=[round(float(f), 1) for f in s['F']], emax=round(float(np.percentile(e_el, 99))),
                               wmax=round(float(w.max()), 3), wmin=round(float(w.min()), 3),
                               cf=[round(cf[0], 3), cf[1]]))
        out['poses'][pose] = dict(frames=frames, w=b64(np.array(wg)), e=b64(np.array(eg)),
                                  summary=dict(strain_p99=round(r['strain_p99_ue']), bow_wall=round(r['w_toward_wall_max'], 2),
                                               bow_cells=round(r['w_toward_cells_max'], 2), closest=r['closest_parts'][:5],
                                               hot=r['highest_strain_parts'][:6], supports=r['support_groups_sum_of_peaks_N']))
        print(pose, len(frames), 'frames', flush=True)
    p = os.path.join(CACHE, 'board_anim_data.json'); txt = json.dumps(out); open(p, 'w').write(txt)
    print(p, round(os.path.getsize(p) / 1e6, 2), 'MB')
    # the page: board_anim.tmpl.html with the data inlined (cache/board-flex.html, not committed)
    page = open(os.path.join(HERE, 'board_anim.tmpl.html')).read().replace('@@DATA@@', txt.replace('</', '<\\/'))
    q = os.path.join(CACHE, 'board-flex.html'); open(q, 'w').write(page); print(q)

if __name__ == '__main__':
    main(sys.argv[1:] or ['board', 'back'])
