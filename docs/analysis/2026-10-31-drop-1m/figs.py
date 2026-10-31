"""Figures for the 1 m drop study (run drop.py, then sens.py, then this): img/*.png, out/checks.json"""
import os, sys, json, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, LogNorm
from PIL import Image
import geom, contact as C, fe, board_flex as BF
HERE = os.path.dirname(os.path.abspath(__file__)); IMG = os.path.join(HERE, 'img'); OUT = os.path.join(HERE, 'out')
SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#d9d8d3'
BLUE, ORANGE, RED, GREEN, GREY, BROWN = '#1f4e79', '#e07b22', '#b3261e', '#3a7d44', '#8c8c8c', '#7a4a1c'
CMAP = LinearSegmentedColormap.from_list('warm', ['#fff6ee', '#fbd5b8', '#f4a77c', '#eb6834', '#c4481b', '#8f2f0e', '#4e1704'])
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': INK, 'axes.labelcolor': INK2,
                     'axes.edgecolor': GRID, 'xtick.color': INK2, 'ytick.color': INK2, 'figure.facecolor': SURF,
                     'axes.facecolor': SURF, 'axes.titlesize': 11, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left'})
RES = json.load(open(os.path.join(OUT, 'drop.json'))); CASES = RES['cases']
ORDER = ['top', 'bottom', 'board', 'side', 'corner_top', 'corner_bottom']
SHORT = dict(top='Flat on the port end', bottom='Flat on the cap end', board='Flat on the board face', side='Flat on a narrow side',
             corner_top='Corner, port end', corner_bottom='Corner, cap end')
COL = dict(top=BLUE, bottom='#6aa6d6', board=RED, side=ORANGE, corner_top=GREEN, corner_bottom=BROWN)
PA12_UTS = 48.0                     # MJF PA12 tensile strength, MPa (HP data sheet, XY); at impact rates it is higher
def style(ax):
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
def cache(name): return np.load(os.path.join(HERE, 'cache', f'{name}.npz'), allow_pickle=True)

def poses():
    import poses as PS
    A, _, _ = geom.load()
    fig, axs = plt.subplots(2, 3, figsize=(14, 10.5), dpi=110, gridspec_kw=dict(wspace=0.02, hspace=0.12))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.91, bottom=0.01)
    for ax, n in zip(axs.ravel(), ORDER):
        im = PS.pose(A, CASES[n]['d'], size=(560, 640), px=4.0)
        ax.imshow(im); ax.set_axis_off()
        r = CASES[n]
        ax.set_title(f"{SHORT[n]}\n{r['g_core']:.0f} g on the core, {r['crush_mm']:.1f} mm crush", fontsize=10.5)
    fig.suptitle('The six 1 m drops onto concrete (4.43 m/s, 3.84 J): pose at first touch, peak deceleration of the cells and board',
                 x=0.01, ha='left', fontsize=13.5, weight='bold')
    fig.savefig(os.path.join(IMG, 'drop-poses.png'), facecolor=SURF, bbox_inches='tight'); plt.close(fig)

def pulses():
    fig, axs = plt.subplots(1, 2, figsize=(16, 5.2), dpi=110, gridspec_kw=dict(wspace=0.18))
    for n in ORDER:
        z = cache(n); tr = z['tr']; t = tr[:, 0] * 1e3
        axs[0].plot(t, np.abs(tr[:, 8]) * (tr[:, 8] <= 0) + 0 * t, color=COL[n], lw=1.7, label=f"{SHORT[n]} ({CASES[n]['g_core']:.0f} g)")
        axs[1].plot(z['dl'], z['Fc'] / 1e3, color=COL[n], lw=1.7)
        d = CASES[n]['crush_mm']; axs[1].plot([d], [np.interp(d, z['dl'], z['Fc']) / 1e3], 'o', color=COL[n], ms=6)
    ax = axs[0]; style(ax); ax.set_xlim(0, 4); ax.set_xlabel('ms from first touch'); ax.set_ylabel('deceleration of the cells and board (g)')
    ax.set_yscale('symlog', linthresh=100); ax.set_ylim(0, 2e4); ax.legend(frameon=False, fontsize=9)
    ax.set_title('Deceleration pulse of the core (cells, carrier, board)')
    ax = axs[1]; style(ax); ax.set_xlim(0, 6); ax.set_yscale('log'); ax.set_ylim(0.05, 200)
    ax.set_xlabel('crush into the floor (mm)'); ax.set_ylabel('floor force (kN)')
    ax.set_title('Force against crush for each pose (dot = where the 3.84 J runs out)')
    ax.axhline(RES['m_all_g'] / 1000 * 9.81 * 1000 / 1e3, color=GREY, lw=0.8, ls=(0, (3, 3)))
    ax.text(5.9, RES['m_all_g'] / 1000 * 9.81 * 1000 / 1e3 * 1.1, '1000 g on the pack', ha='right', fontsize=8, color=INK2)
    fig.savefig(os.path.join(IMG, 'drop-pulses.png'), facecolor=SURF, bbox_inches='tight'); plt.close(fig)

def footprints():
    fig, axs = plt.subplots(2, 3, figsize=(16, 10), dpi=110, gridspec_kw=dict(wspace=0.15, hspace=0.25))
    for ax, n in zip(axs.ravel(), ORDER):
        z = cache(n); p = z['p_pk']; gap = z['gap']; res = float(z['res']); u0, v0 = z['origin']
        nu, nv = gap.shape; ext = (u0, u0 + nu * res, v0, v0 + nv * res)
        sil = np.isfinite(gap)
        base = np.where(sil, 0.92, 1.0)
        ax.imshow(base.T, origin='lower', extent=ext, cmap='gray', vmin=0, vmax=1)
        pm = np.ma.masked_where(p <= 0, p)
        im = ax.imshow(pm.T, origin='lower', extent=ext, cmap=CMAP, norm=LogNorm(0.05, 100), interpolation='nearest')
        names = list(z['names']); prt = z['part']
        for i, nm in enumerate(names):
            m = (prt == i) & (p > 0)
            if m.sum() * res**2 > 15:
                iu, iv = np.argwhere(m).mean(0)
        ax.contour(np.arange(nu) * res + u0, np.arange(nv) * res + v0, sil.T.astype(float), levels=[0.5], colors=INK2, linewidths=0.6)
        ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_visible(False)
        r = CASES[n]; pc = r['parts_in_contact']
        lab = {'bumpt_slab': 'top slab', 'bumpb_slab': 'bottom slab', 'bumpt_band': 'top band', 'bumpb_band': 'bottom band',
               'label': 'label / cup wall', 'cup': 'cup', 'cap': 'cap', 'screw': 'screw head'}
        txt = ', '.join(f"{lab.get(k, k)} {v:.0f}" for k, v in sorted(pc.items(), key=lambda kv: -kv[1]) if v >= 1)
        ax.set_title(f"{SHORT[n]}: {r['contact_area_mm2']:.0f} mm² in contact\n{txt} mm²", fontsize=10)
    cb = fig.colorbar(im, ax=axs, fraction=0.02, pad=0.01); cb.set_label('contact pressure at full crush (MPa, log scale)'); cb.outline.set_visible(False)
    fig.suptitle('Where the floor pushes: contact pressure at the deepest point of each drop (grey = the pack seen from the floor)',
                 x=0.01, ha='left', fontsize=13.5, weight='bold')
    fig.savefig(os.path.join(IMG, 'drop-footprints.png'), facecolor=SURF, bbox_inches='tight'); plt.close(fig)

def stress():
    A, MASS, _ = geom.load()
    g = fe.voxelise(A, part_mass=MASS); M = fe.Model(g)
    sig1 = {}
    names = g['names']; epart = g['part'][tuple(M.el.T)]
    out = {}
    for n in ORDER:
        z = cache(n); u = z['u1g']; _, vm, _ = M.stress(u)
        a = CASES[n]['g_core']; vm = vm * a
        sig1[n] = vm
        out[n] = {}
        for k in ('cup', 'cap', 'carrier', 'rails'):
            s = vm[epart == names.index(k)]
            out[n][k] = dict(p99=float(np.percentile(s, 99)), p999=float(np.percentile(s, 99.9)), max=float(s.max()))
    # 3-D views: cup + cap + carrier cut open on the viewer's side, coloured by stress at the peak
    sys.path.insert(0, geom.MECH); cwd = os.getcwd(); os.chdir(geom.MECH)
    import monolith_side_renders as RR, monolith_render as MR
    os.chdir(cwd)
    keep = np.isin(epart, [names.index(k) for k in ('cup', 'cap', 'carrier', 'rails')])
    norm = LogNorm(0.3, 60)
    fig, axs = plt.subplots(2, 3, figsize=(16, 13), dpi=110, gridspec_kw=dict(wspace=0.02, hspace=0.1))
    fig.subplots_adjust(left=0.01, right=0.92, top=0.93, bottom=0.01)
    for ax, n in zip(axs.ravel(), ORDER):
        tris, cols = voxel_faces(M, keep, sig1[n], norm)
        d = np.asarray(CASES[n]['d']); view = np.array([0.9, -1.0, 0.55])
        R = MR.camera(view, up=(0, 0, 1))
        W, H = 680, 860; S = RR.SS; K = 7.2
        img = Image.new('RGB', (W * S, H * S), (252, 252, 250))
        c = M.X.mean(0)
        ox = W / 2 - K * (c @ R[0]); oy = H / 2 + K * (c @ R[1])
        bins = np.digitize(cols, np.linspace(0, 1, 33)[1:-1])
        parts = [(tris[bins == b], tuple(int(255 * x) for x in CMAP(b / 31)[:3])) for b in range(32) if (bins == b).any()]
        RR.zrender(img, parts, R, (ox * S, oy * S), K * S, edge_px=1)
        img = img.resize((W, H), Image.LANCZOS)
        ax.imshow(img); ax.set_axis_off()
        q = (np.asarray(d) @ R[0], np.asarray(d) @ R[1])
        L = 90; cx, cy = W / 2, H / 2
        ax.annotate('', xy=(cx + L * q[0] * 3, cy - L * q[1] * 3), xytext=(cx + L * q[0] * 1.6, cy - L * q[1] * 1.6),
                    arrowprops=dict(arrowstyle='-|>', color=BLUE, lw=2.2))
        o = out[n]
        ax.set_title(f"{SHORT[n]} ({CASES[n]['g_core']:.0f} g): cup {o['cup']['p999']:.0f}, cap {o['cap']['p999']:.0f},\n"
                     f"carrier {o['carrier']['p999']:.0f} MPa (99.9th percentile von Mises)", fontsize=10)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=CMAP), ax=axs, fraction=0.02, pad=0.01)
    cb.set_label('von Mises stress at the peak (MPa, log); MJF PA12 breaks at ~48 MPa'); cb.outline.set_visible(False)
    fig.suptitle('Stress in the PA12 parts at the peak of each drop (cup, cap, carrier, rails; cut open on the near side, blue arrow = toward the floor)',
                 x=0.01, ha='left', fontsize=13, weight='bold')
    fig.savefig(os.path.join(IMG, 'drop-stress.png'), facecolor=SURF, bbox_inches='tight'); plt.close(fig)
    return out

def voxel_faces(M, keep, vm, norm):
    """exposed faces of the kept voxels (minus the near half in -y, so the inside shows), coloured by element stress"""
    g = M.g; o, H = g['origin'], g['H']; el = M.el[keep]; s = vm[keep]
    cut = (o[1] + (el[:, 1] + 0.5) * H) < -2.0
    cut &= (o[0] + (el[:, 0] + 0.5) * H) > -40
    el, s = el[~cut], s[~cut]
    occ = np.zeros(g['shape'], bool); occ[tuple(el.T)] = True
    tris, cols = [], []
    corners = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], float)
    faces = {(-1, 0, 0): [0, 3, 7, 4], (1, 0, 0): [1, 2, 6, 5], (0, -1, 0): [0, 1, 5, 4], (0, 1, 0): [3, 2, 6, 7],
             (0, 0, -1): [0, 1, 2, 3], (0, 0, 1): [4, 5, 6, 7]}
    n = np.array(g['shape'])
    for dvec, idx in faces.items():
        nb = el + np.array(dvec); inside = np.all((nb >= 0) & (nb < n), 1)
        exposed = ~inside; exposed[inside] = ~occ[tuple(nb[inside].T)]
        e = el[exposed]; ss = s[exposed]
        P = o + (e[:, None, :] + corners[idx][None]) * H
        tris += [P[:, [0, 1, 2]], P[:, [0, 2, 3]]]; c = norm(np.clip(ss, norm.vmin, norm.vmax)); cols += [c, c]
    return np.vstack(tris), np.concatenate(cols)

def board():
    m, parts = BF.setup(); out = {}
    fig, axs = plt.subplots(1, 3, figsize=(18, 7.2), dpi=110, gridspec_kw=dict(wspace=0.42, width_ratios=[1, 1, 1.05]))
    n = 'board'; a = CASES[n]['g_core']
    _, _, w, st = BF.solve(a, m, parts)
    rep = BF.part_report(m, parts, w, st)
    P = m.p
    ax = axs[0]; tc = ax.tricontourf(P[0], P[1], m.t.T, w, levels=20, cmap=CMAP); ax.set_aspect('equal')
    fig.colorbar(tc, ax=ax, fraction=0.05).set_label('deflection toward the board-face wall (mm)')
    for y, z in BF.PEGS: ax.plot(y, z, 'o', mfc='white', mec=INK, ms=7)
    ax.set_title(f'Board deflection, board-face drop ({a:.0f} g)\nheld at the 4 pegs (o) and the 2 USB-C receptacles')
    ax.set_xlabel('y (mm)'); ax.set_ylabel('z (mm)')
    ax = axs[1]; c = P[:, m.t].mean(1)
    sc = ax.tripcolor(P[0], P[1], m.t.T, facecolors=np.clip(st * 1e6, 1, None), cmap=CMAP, norm=LogNorm(50, 5000)); ax.set_aspect('equal')
    fig.colorbar(sc, ax=ax, fraction=0.05).set_label('surface strain (µε, log)')
    ax.set_title('Board surface strain (bending)'); ax.set_xlabel('y (mm)')
    for y, z in BF.PEGS: ax.plot(y, z, 'o', mfc='white', mec=INK, ms=7)
    ax = axs[2]; style(ax)
    fparts = sorted([(k, r) for k, r in rep.items() if r['side'] == 'F' and r['clear_mm'] is not None], key=lambda kv: kv[1]['clear_mm'] - kv[1]['w_mm'])[:12]
    y = np.arange(len(fparts))
    ax.barh(y, [r['clear_mm'] for _, r in fparts], color='#c9d8e6', label='gap to the wall, at rest')
    ax.barh(y, [r['clear_mm'] - max(r['w_mm'], 0) for _, r in fparts], color=BLUE, label='gap left at the peak')
    ax.set_yticks(y); ax.set_yticklabels([k for k, _ in fparts]); ax.invert_yaxis(); ax.set_xlabel('mm')
    ax.set_xlim(0, 2.1); ax.legend(frameon=False, loc='upper right', fontsize=9); ax.set_title('Tallest F.Cu parts: gap to the wall')
    fig.suptitle('Board flex in the worst drop for the board (flat on the board face)', x=0.01, ha='left', fontsize=13.5, weight='bold')
    fig.savefig(os.path.join(IMG, 'drop-board.png'), facecolor=SURF, bbox_inches='tight'); plt.close(fig)
    for nn in ORDER:
        an = CASES[nn]['g_core'] * abs(CASES[nn]['d'][0])
        if an < 1: out[nn] = dict(a_normal_g=0.0); continue
        _, _, w, st = BF.solve(an, m, parts); rp = BF.part_report(m, parts, w, st)
        fp = [r for r in rp.values() if r['side'] == 'F' and r['clear_mm'] is not None]
        heavy = sorted(parts.items(), key=lambda kv: -kv[1]['m'])[:6]
        c = m.p[:, m.t].mean(1); away = np.min([np.hypot(c[0] - y, c[1] - z) for y, z in BF.PEGS], 0) > 3.0
        out[nn] = dict(a_normal_g=an, w_max_mm=float(np.abs(w).max()), strain_p50_ue=float(np.percentile(st[away], 50) * 1e6),
                       strain_p99_ue=float(np.percentile(st[away], 99) * 1e6),
                       
                       min_gap_left_mm=float(min(r['clear_mm'] - max(r['w_mm'], 0) for r in fp)),
                       heavy_parts={k: dict(m_g=round(v['m'], 2), N=round(v['m'] / 1000 * 9.81 * CASES[nn]['g_core'], 1)) for k, v in heavy})
    return out

def sensitivity():
    S = json.load(open(os.path.join(OUT, 'sens.json')))
    fig, axs = plt.subplots(1, 2, figsize=(16, 5.4), dpi=110, gridspec_kw=dict(wspace=0.2))
    ax = axs[0]; style(ax)
    for n in ORDER:
        ax.plot(S['heights'], [x['g_core'] for x in S['height'][n]], 'o-', color=COL[n], lw=1.6, ms=4, label=SHORT[n])
    ax.axvline(1.0, color=GREY, lw=0.8, ls=(0, (3, 3))); ax.set_yscale('log'); ax.set_xlabel('drop height (m)'); ax.set_ylabel('peak g on the core')
    ax.legend(frameon=False, fontsize=9); ax.set_title('Peak g against drop height (nominal TPU)')
    ax = axs[1]; style(ax)
    B = S['top_builds']; keys = list(B); x = np.arange(len(keys)); w = 0.27
    for i, h in enumerate(('0.5 m', '1.0 m', '1.5 m')):
        ax.bar(x + (i - 1) * w, [B[k][h]['g_core'] for k in keys], w, color=[ '#9cc3e4', BLUE, '#0f2a44'][i], label=h)
    ax.set_xticks(x); ax.set_xticklabels([k.replace(' mm ', ' mm\n') for k in keys]); ax.set_yscale('log')
    ax.set_ylabel('peak g on the core'); ax.legend(frameon=False, title='drop height'); ax.set_title('Port-end slab: thickness and gyroid infill (flat port-end drop)')
    ax.axvline(-0.5 + 0.0, color=GREY)
    fig.suptitle('Sensitivity: where the bumpers bottom out', x=0.01, ha='left', fontsize=13.5, weight='bold')
    fig.savefig(os.path.join(IMG, 'drop-sensitivity.png'), facecolor=SURF, bbox_inches='tight'); plt.close(fig)

if __name__ == '__main__':
    os.makedirs(IMG, exist_ok=True)
    what = sys.argv[1:] or ['poses', 'pulses', 'footprints', 'stress', 'board', 'sens']
    chk = json.load(open(os.path.join(OUT, 'checks.json'))) if os.path.exists(os.path.join(OUT, 'checks.json')) else {}
    if 'poses' in what: poses()
    if 'pulses' in what: pulses()
    if 'footprints' in what: footprints()
    if 'stress' in what: chk['stress'] = stress()
    if 'board' in what: chk['board'] = board()
    if 'sens' in what and os.path.exists(os.path.join(OUT, 'sens.json')): sensitivity()
    json.dump(chk, open(os.path.join(OUT, 'checks.json'), 'w'), indent=1)
    print(json.dumps(chk, indent=1)[:3000])
