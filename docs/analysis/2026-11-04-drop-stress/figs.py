"""Figures for the contact drop study (run after run_all.py; reads out/*.json and cache/*):
  fig_margins.png    every check against its limit, worst first
  fig_heatmap.png    pose x part: stress / limit
  fig_stress_<part>_<pose>.png   von Mises of the cup + cap / carrier at the worst pose, three views
  fig_board_<pose>.png           board surface strain envelope
  fig_forces_<pose>.png          the largest contact forces against time
Run: python figs.py [--h 0.5]"""
import os, sys, json, glob, argparse, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out'); CACHE = os.path.join(HERE, 'cache')
FIG = os.path.join(HERE, 'figs')
import poses
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET = '#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6'
CAT = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET]
SEQ = LinearSegmentedColormap.from_list('seq', ['#e8f1fc', '#9cc3f0', '#2a78d6', '#164a8c', '#0b2547'])
plt.rcParams.update({'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF, 'text.color': INK,
                     'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.edgecolor': GRID,
                     'axes.spines.top': False, 'axes.spines.right': False, 'font.size': 9, 'axes.titlesize': 10,
                     'axes.titleweight': 'bold', 'legend.frameon': False})

def L(p):
    try: return json.load(open(p))
    except Exception: return None

def save(fig, name):
    os.makedirs(FIG, exist_ok=True); fig.savefig(os.path.join(FIG, name), dpi=160, bbox_inches='tight'); plt.close(fig)
    print('  ', name)

def margins():
    C = L(os.path.join(OUT, 'checks.json'))
    if not C: return
    rows = [r for r in C['rows'] if r['margin'] is not None and r['limit'] < 1e8][:28][::-1]
    u = np.array([r['value'] / r['limit'] for r in rows])
    fig, ax = plt.subplots(figsize=(8, 0.28 * len(rows) + 1))
    col = [ORANGE if x >= 1 else (YELLOW if x >= 0.67 else BLUE) for x in u]
    ax.barh(range(len(rows)), u, height=0.62, color=col)
    ax.axvline(1, color=INK, lw=1); ax.axvline(0.67, color=INK2, lw=0.7, ls=':')
    ax.set_yticks(range(len(rows)), [f"{r['part']}  ({r['title']})" for r in rows], fontsize=7.5)
    for i, (r, x) in enumerate(zip(rows, u)):
        ax.text(x + 0.02, i, f"{r['value']:.0f} {r['unit']} / {r['limit']:g}", va='center', fontsize=7, color=INK2)
    ax.set_xlabel('demand / limit  (1 = at the limit; dotted = 1.5x margin)')
    ax.set_xlim(0, max(1.2, u.max() * 1.25)); ax.grid(axis='x', color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.set_title('1 m drop: every check against its limit, worst at the top')
    save(fig, 'fig_margins.png')

def heatmap():
    ps = [p for p in poses.ORDER if os.path.exists(os.path.join(OUT, f'dyn_{p}.json'))]
    cols = {}
    for p in ps:
        for f, pre in ((f'shell_{p}.json', ''), (f'carrier_{p}.json', ''), *[(os.path.basename(g), 'rail ') for g in glob.glob(os.path.join(OUT, f'rails_??_{p}.json'))]):
            r = L(os.path.join(OUT, f))
            if not r: continue
            for k, v in r['regions'].items():
                k2 = pre + k.split('/')[-1] if pre else k.replace('carrier/', 'carrier ')
                cols.setdefault(k2, {})[p] = max(cols.get(k2, {}).get(p, 0), v['p999'] / 48.0)
        b = L(os.path.join(OUT, f'board_{p}.json'))
        if b: cols.setdefault('board strain p99', {})[p] = b['strain_p99_ue'] / 2000.0
    if not cols: return
    names = sorted(cols, key=lambda k: -max(cols[k].values()))
    A = np.array([[cols[k].get(p, np.nan) for k in names] for p in ps])
    fig, ax = plt.subplots(figsize=(0.55 * len(names) + 3, 0.34 * len(ps) + 1.6))
    im = ax.imshow(np.minimum(A, 2), cmap=SEQ, vmin=0, vmax=2, aspect='auto')
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            if np.isfinite(A[i, j]) and A[i, j] >= 0.5:
                ax.text(j, i, f'{A[i, j]:.1f}', ha='center', va='center', fontsize=6.5, color='white' if A[i, j] > 1.0 else INK)
    ax.set_xticks(range(len(names)), names, rotation=50, ha='right', fontsize=7.5)
    ax.set_yticks(range(len(ps)), [poses.TITLES.get(p, p) for p in ps], fontsize=7.5)
    ax.spines[:].set_visible(False); ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, shrink=0.8); cb.set_label('stress / 48 MPa  (board: strain / 2000 ue)'); cb.outline.set_visible(False)
    ax.set_title('Where each pose loads the parts (99.9th percentile; numbers shown from 0.5)')
    save(fig, 'fig_heatmap.png')

def stress_views(part, pose, H):
    g = os.path.join(CACHE, f'{part}_grid_H{H}.npz'); v = os.path.join(CACHE, f'{part}_vm_{pose}.npy')
    if not (os.path.exists(g) and os.path.exists(v)): return
    G = np.load(g); vm = np.load(v); X = G['Xe']
    if len(vm) != len(X): return
    o = np.argsort(vm)
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.6))
    for ax, (i, j, lab) in zip(axs, ((1, 2, 'y-z (from +x, board side)'), (0, 2, 'x-z (from +y)'), (0, 1, 'x-y (from +z, port end)'))):
        # draw low first so the hot elements sit on top: a "max through the thickness" view
        sc = ax.scatter(X[o, i], X[o, j], c=vm[o], s=1.2, cmap=SEQ, vmin=0, vmax=48, linewidths=0, rasterized=True)
        ax.set_aspect('equal'); ax.set_title(lab, fontsize=8.5, fontweight='normal', color=INK2)
        ax.set_xlabel('mm'); ax.grid(color=GRID, lw=0.4)
    cb = fig.colorbar(sc, ax=axs, shrink=0.8, extend='max'); cb.set_label('von Mises, MPa (48 = PA12 tensile)'); cb.outline.set_visible(False)
    fig.suptitle(f'{part}: {poses.TITLES.get(pose, pose)}, stress envelope', fontweight='bold')
    save(fig, f'fig_stress_{part}_{pose}.png')

def board_map(pose):
    m = os.path.join(CACHE, 'board_mesh.npz'); s = os.path.join(CACHE, f'board_strain_{pose}.npy'); r = L(os.path.join(OUT, f'board_{pose}.json'))
    if not (os.path.exists(m) and os.path.exists(s) and r): return
    M = np.load(m); e = np.load(s) * 1e6
    if len(e) != M['t'].shape[1]: return
    fig, ax = plt.subplots(figsize=(5.2, 7))
    tp = ax.tripcolor(M['p'][0], M['p'][1], M['t'].T, facecolors=np.minimum(e, 4000), cmap=SEQ, vmin=0, vmax=4000)
    ax.set_aspect('equal'); ax.set_xlabel('y, mm'); ax.set_ylabel('z, mm')
    cb = fig.colorbar(tp, ax=ax, shrink=0.7, extend='max'); cb.set_label('surface strain envelope, ue (2000 = bad)'); cb.outline.set_visible(False)
    ax.set_title(f'Board: {poses.TITLES.get(pose, pose)}\nbow {r["w_toward_wall_max"]:.2f} mm toward the wall, p99 {r["strain_p99_ue"]:.0f} ue')
    save(fig, f'fig_board_{pose}.png')

def forces(pose, n=7):
    p = os.path.join(CACHE, f'dyn_{pose}.npz')
    if not os.path.exists(p): return
    R = np.load(p); F = R['F']; names = list(R['names']); t = R['t'] * 1e3
    top = np.argsort(-F.max(0))[:n]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(t, R['ff'] / 1e3, color=INK2, lw=1.2, ls='--', label='floor on the bumpers')
    for c, j in zip(CAT, top):
        a, b, s = names[j].split('|')
        ax.plot(t, F[:, j] / 1e3, color=c, lw=2, label=f'{a} on {b}')
    ax.set_xlabel('time from touch-down, ms'); ax.set_ylabel('contact force, kN'); ax.grid(color=GRID, lw=0.5)
    ax.set_xlim(0, t[-1]); ax.legend(fontsize=7, loc='upper right')
    ax.set_title(f'{poses.TITLES.get(pose, pose)}: the largest internal contact forces')
    save(fig, f'fig_forces_{pose}.png')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--h', type=float, default=None); a = ap.parse_args()
    H = a.h if a.h is not None else (L(os.path.join(OUT, 'run_all.json')) or {}).get('h', 0.5)
    margins(); heatmap()
    for part, pre in (('shell', 'shell'), ('carrier', 'carrier')):
        best = {}
        for f in glob.glob(os.path.join(OUT, f'{pre}_*.json')):
            r = L(f)
            if r and r.get('regions'): best[r['pose']] = max(v['p999'] for v in r['regions'].values())
        for pose in sorted(best, key=lambda k: -best[k])[:3]: stress_views(part, pose, H)
    bs = {}
    for f in glob.glob(os.path.join(OUT, 'board_*.json')):
        r = L(f); bs[r['pose']] = r['strain_p99_ue']
    for pose in sorted(bs, key=lambda k: -bs[k])[:2]: board_map(pose)
    for pose in ('bottom', 'board', 'side', 'top_board'): forces(pose)

if __name__ == '__main__': main()
