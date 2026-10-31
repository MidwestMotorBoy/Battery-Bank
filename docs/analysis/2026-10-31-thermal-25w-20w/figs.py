"""Figures and numbers for the 25 W + 20 W thermal runs (run_dual.py results). Needs the rev7 model folder
(research_notes/Pack thermal BAK 65E + the rev7 files: cu.py, smd.py, ntc.py, cu_losses_rev7.json, render.py) with
results/p0f/dual*.npz and grid.npz in it:  MODEL=<that folder> python figs.py  -> img/*.png, summary.json"""
import os, sys, json, numpy as np
os.environ.setdefault('SMD_LAYOUT', 'p0f')
HERE = os.path.dirname(os.path.abspath(__file__)); IMG = os.path.join(HERE, 'img')
MODEL = os.environ['MODEL']; sys.path.insert(0, MODEL); os.chdir(MODEL)
os.environ.setdefault('CU_JSON', os.path.join(MODEL, 'cu_losses_rev7.json'))
import cu as CU
import render as RD
P, S = CU.P, CU.S
RD.P = P
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
INK, INK2, GRID, SURF = RD.INK, RD.INK2, RD.GRID, RD.SURF
BLUE, ORANGE, RED, GREEN, GREY = '#1f4e79', '#e07b22', '#b3261e', '#3a7d44', '#8c8c8c'
RUNS = {'std25': 'dual15_std_amb25', 'std35': 'dual15_std_amb35', 'std40': 'dual15_std_amb40',
        'nod25': 'dual15_nod_amb25', 'nod35': 'dual15_nod_amb35', 'v9': 'dual9_std_amb25', 'v20': 'dual20_std_amb25'}
def load(k):
    z = np.load(os.path.join(P.OUT_DIR, RUNS[k] + '.npz')); m = json.load(open(os.path.join(P.OUT_DIR, RUNS[k] + '.json')))
    return z, m
def style(ax):
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)

def summary():
    out = {}
    for k in RUNS:
        z, m = load(k); t = z['rec_t']; p = z['rec_p1'] + z['rec_p2']; cut = (p < 44.9) & (t < t[-1] - 0.5)
        parts = dict(zip(m['part_names'], z['rec_parts'].max(0).round(1).tolist()))
        out[k] = dict(run=RUNS[k], title=m['title'], amb=m['amb'], t_end_min=float(t[-1]), wh_out=float(z['rec_p_out'].sum() * m['dt'] / 3600),
                      first_cut_min=float(t[np.argmax(cut)]) if cut.any() else None, p_min=float(p.min()),
                      p1_end=float(z['rec_p1'][-1]), p2_end=float(z['rec_p2'][-1]),
                      ntc_max=float(z['rec_ntc'].max()), cell_max=float(z['rec_cell_max'].max()), cell_spread_max=float((z['rec_cell_max'].max(1) - z['rec_cell_min'].min(1)).max()),
                      board_max=float(z['rec_board_max'].max()), part_max=float(z['rec_part_max'].max()), skin_max=float(z['rec_skin_max'].max()),
                      ts_max=float(max(z['rec_ts1'].max(), z['rec_ts2'].max())), q_board_W=float(z['rec_q_board'][3]), q_cells_W=float(z['rec_q_cells'][3]),
                      parts_max=parts, hit_3h_limit=bool(t[-1] >= 179.5))
    json.dump(out, open(os.path.join(HERE, 'summary.json'), 'w'), indent=1)
    return out

def timeline():
    fig, axs = plt.subplots(2, 3, figsize=(17, 8.6), dpi=110, sharex='col', gridspec_kw=dict(height_ratios=[1, 1.5], hspace=0.08, wspace=0.18))
    for j, (k, kn) in enumerate((('std25', 'nod25'), ('std35', 'nod35'), ('std40', None))):
        z, m = load(k); t = z['rec_t']
        ax = axs[0, j]; style(ax)
        ax.stackplot(t, z['rec_p2'], z['rec_p1'], colors=['#9cc3e4', BLUE], alpha=0.9, labels=['USB2 (phone, 9 V)', 'USB1 (15 V)'])
        ax.axhline(45, color=INK2, lw=0.8, ls=(0, (4, 3))); ax.text(2, 46.5, 'asked: 25 + 20 = 45 W', fontsize=8.5, color=INK2)
        ax.set_ylim(0, 55); ax.set_title(f"{m['amb']:.0f} °C still air", fontsize=12)
        if j == 0: ax.set_ylabel('Delivered (W)'); ax.legend(loc='lower left', fontsize=8.5, frameon=False)
        ax = axs[1, j]; style(ax)
        for key, lab, c in (('rec_part_max', 'hottest board part', RED), ('rec_ntc', 'hottest cell NTC (what firmware reads)', ORANGE),
                            ('rec_cell_max', 'hottest point in any cell', '#7a4a1c'), ('rec_skin_max', 'hottest outside skin', GREEN)):
            y = z[key].max(1) if z[key].ndim > 1 else z[key]
            ax.plot(t, y, color=c, lw=1.8, label=lab)
            if kn:
                z2, _ = load(kn); y2 = z2[key].max(1) if z2[key].ndim > 1 else z2[key]
                ax.plot(z2['rec_t'], y2, color=c, lw=1.0, ls=(0, (2, 2)), alpha=0.8)
        ax.axhspan(44, 48, color='#f6e2c8', alpha=0.6, lw=0); ax.text(t[-1] * 0.02, 44.4, 'derate ramp 44 → 48 °C (NTC)', fontsize=8, color='#8a5a20')
        ax.axhline(60, color=RED, lw=0.8, ls=(0, (1, 2))); ax.text(t[-1] * 0.02, 60.5, '60 °C: cell discharge limit', fontsize=8, color=RED)
        ax.set_ylim(m['amb'] - 2, 66); ax.set_xlabel('minutes from full')
        if j == 0: ax.set_ylabel('°C'); ax.legend(loc='lower right', fontsize=8.5, frameon=False)
        if kn: ax.text(0.99, 0.02 if j else 0.30, 'dashed: firmware derate off', transform=ax.transAxes, ha='right', fontsize=8, color=INK2)
        if t[-1] >= 179.5: axs[0, j].text(178, 30, 'run stopped at 3 h\n(not empty)', ha='right', fontsize=8, color=INK2)
    fig.suptitle('USB1 25 W + USB2 20 W at the same time, from full until empty', x=0.01, ha='left', fontsize=14, weight='bold')
    fig.savefig(os.path.join(IMG, 'thermal-timeline.png'), facecolor=SURF, bbox_inches='tight'); plt.close(fig)

def parts_bar(S_):
    names = {'fetA1': 'USB1 FETs (bat side)', 'fetB1': 'USB1 FETs (USB side)', 'ind1': 'USB1 inductor', 'ic1': 'USB1 BQ25756',
             'rbat1': 'USB1 sense R', 'buck51': 'USB1 5 V buck', 'fetA2': 'USB2 FETs (bat side)', 'fetB2': 'USB2 FETs (USB side)',
             'ind2': 'USB2 inductor', 'ic2': 'USB2 BQ25756', 'rbat2': 'USB2 sense R', 'buck52': 'USB2 5 V buck',
             'prot': 'protection FETs', 'shunt': 'gauge shunt', 'fuse': 'chem. fuse', 'conn1': 'USB1 receptacle', 'conn2': 'USB2 receptacle'}
    keys = [k for k in names if k in S_['std25']['parts_max']]
    keys.sort(key=lambda k: -S_['nod35']['parts_max'][k])
    fig, ax = plt.subplots(figsize=(12, 6.4), dpi=110); style(ax)
    y = np.arange(len(keys)); w = 0.26
    for i, (run, lab, c) in enumerate((('std25', '25 °C', BLUE), ('std35', '35 °C (derate on)', ORANGE), ('nod35', '35 °C, derate off', RED))):
        ax.barh(y + (i - 1) * w, [S_[run]['parts_max'][k] for k in keys], w, color=c, label=lab)
    ax.set_yticks(y); ax.set_yticklabels([names[k] for k in keys]); ax.invert_yaxis()
    ax.set_xlim(20, 70)
    for i, run in enumerate(('std25', 'std35', 'nod35')):
        for j, k in enumerate(keys[:1]): ax.text(S_[run]['parts_max'][k] + 0.4, j + (i - 1) * w, f"{S_[run]['parts_max'][k]:.1f}", va='center', fontsize=7.5, color=INK2); ax.set_xlabel('hottest temperature during the run (°C)')
    ax.legend(loc='lower right', frameon=True, facecolor=SURF, edgecolor=GRID)
    ax.set_title('Board parts: hottest temperature over the whole run (USB1 25 W at 15 V + USB2 20 W at 9 V)', fontsize=12)
    fig.savefig(os.path.join(IMG, 'thermal-board-parts.png'), facecolor=SURF, bbox_inches='tight'); plt.close(fig)

def losses():
    z, m = load('std25'); i = np.searchsorted(z['rec_t'], 30.0)
    L = dict(zip(m['part_names'], z['rec_loss'][i])); qc = float(z['rec_q_cells'][i]); qn = float(z['rec_q_ni'][i])
    groups = {'USB1 stage (25 W, 15 V)': [k for k in L if k.endswith('1') and k not in ('prot',)],
              'USB2 stage (20 W, 9 V)': [k for k in L if k.endswith('2')],
              'protection, shunt, fuse': ['prot', 'shunt', 'fuse']}
    vals = {g: sum(L[k] for k in ks) for g, ks in groups.items()}
    cu = float(z['rec_q_board'][i]) - sum(L.values())
    vals['copper, other'] = max(cu, 0.0); vals['cells (I²R)'] = qc; vals['nickel strips'] = qn
    fig, ax = plt.subplots(figsize=(10, 2.4), dpi=110); style(ax)
    cols = [BLUE, '#9cc3e4', '#6b6b6b', '#c8a24a', ORANGE, '#b0b0b0']; left = 0
    for (k, v), c in zip(vals.items(), cols):
        ax.barh(0, v, left=left, color=c, edgecolor='white'); 
        if v > 0.12: ax.text(left + v / 2, 0, f'{v:.2f} W', ha='center', va='center', color='white' if c in (BLUE, '#6b6b6b', ORANGE) else INK, fontsize=9)
        left += v
    ax.set_yticks([]); ax.set_xlabel('heat (W)'); ax.set_xlim(0, left * 1.02)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=k) for k, c in zip(vals, cols)], loc='upper center', bbox_to_anchor=(0.5, -0.45), ncol=3, frameon=False, fontsize=8.5)
    ax.set_title(f'Where the heat comes from at 45 W out (30 min in, 25 °C): {left:.2f} W in total, {100 * left / 45:.1f} % of the output', fontsize=11)
    fig.savefig(os.path.join(IMG, 'thermal-heat-sources.png'), facecolor=SURF, bbox_inches='tight'); plt.close(fig)
    return vals

def maps():
    for k, snap in (('std25', 'peak_board'), ('std35', 'peak_cell'), ('nod35', 'peak_board')):
        name = RUNS[k]
        RD.RD = os.path.join(MODEL, 'renders_dual')
        P.CASES[name] = dict(title={'std25': 'USB1 25 W + USB2 20 W, 25 °C', 'std35': 'USB1 25 W + USB2 20 W, 35 °C (derate on)',
                                    'nod35': 'USB1 25 W + USB2 20 W, 35 °C, derate OFF'}[k])
        F = RD.case_maps(name, snap)
        for suf in ('pack', 'cells'):
            src = os.path.join(RD.RD, f'{name}_{snap}_{suf}.png')
            os.replace(src, os.path.join(IMG, f'thermal-{k}-{suf}.png'))

RENDER = os.environ.get('RENDER', '')      # KiCad top render of the board (kicad-cli pcb render, USB-C on the right)
BOX = (94, 2871, 77, 1690)                  # board edges in that image (px): left = z 4.3, right = z 78.65, top = y -21.6

def board_overlay():
    """the board's temperature laid over the KiCad render, at the moment the board is hottest"""
    from PIL import Image
    im = Image.open(RENDER).convert('RGBA'); bg = Image.new('RGBA', im.size, (252, 252, 251, 255)); bg.alpha_composite(im)
    rgb = np.asarray(bg.convert('RGB')).astype(float) / 255
    sc = 0.5; W, H = int(rgb.shape[1] * sc), int(rgb.shape[0] * sc)
    rgb = np.asarray(Image.fromarray((rgb * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)).astype(float) / 255
    x0, x1, y0, y1 = [v * sc for v in BOX]
    u, v = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
    z = P.BOARD_Z[0] + (u - x0) / (x1 - x0) * (P.BOARD_Z[1] - P.BOARD_Z[0])
    y = -P.BOARD_HW + (v - y0) / (y1 - y0) * (2 * P.BOARD_HW)
    box = (u >= x0) & (u <= x1) & (v >= y0) & (v <= y1)
    g = P.get_grid()
    fig, axs = plt.subplots(1, 2, figsize=(17, 5.6), dpi=120, gridspec_kw=dict(wspace=0.10))
    for ax, (k, snap, ttl) in zip(axs, (('std25', 'peak_board', '25 °C, derate on'), ('nod35', 'peak_board', '35 °C, derate OFF'))):
        zf, m = load(k); F = RD.Field(g, zf[f'snap_{snap}'].astype(float), m['amb'])
        T = F.at(np.full_like(y, 0.5 * sum(P.BOARD_X)), y, z)
        ix = np.clip(np.searchsorted(g.edges[0], 0.5 * sum(P.BOARD_X)) - 1, 0, g.n[0] - 1)
        iy = np.clip(np.searchsorted(g.edges[1], y) - 1, 0, g.n[1] - 1); iz = np.clip(np.searchsorted(g.edges[2], z) - 1, 0, g.n[2] - 1)
        inb = box & np.isin(g.mat[ix][iy, iz], (P.BOARD, P.VIAS))
        lo, hi = np.floor(T[inb].min() * 2) / 2, np.ceil(T[inb].max() * 2) / 2
        nrm = Normalize(lo, hi); col = RD.CMAP(nrm(T))[..., :3]
        gray = rgb.mean(-1, keepdims=True) * 0.55 + rgb * 0.45
        out = np.where(inb[..., None], gray * 0.42 + col * 0.58, rgb)
        ax.imshow(out); ax.set_axis_off()
        cs = ax.contour(u[0], v[:, 0], np.where(inb, T, np.nan), levels=np.arange(lo, hi + 0.01, 0.5), colors='white', linewidths=0.6, alpha=0.8)
        ax.clabel(cs, fmt='%g', fontsize=7)
        t_at = m['t_peak_board']
        ax.set_title(f'{ttl}: {T[inb].min():.1f} to {T[inb].max():.1f} °C at {t_at:.0f} min', fontsize=11.5, loc='left')
        cb = fig.colorbar(plt.cm.ScalarMappable(norm=nrm, cmap=RD.CMAP), ax=ax, fraction=0.03, pad=0.01); cb.outline.set_visible(False); cb.set_label('°C')
        ax.text(W * 0.98, H * 0.5, 'USB-C', rotation=90, ha='right', va='center', fontsize=9, color=INK2)
    fig.suptitle('Board temperature on the routed P0 board (KiCad render): USB1 25 W + USB2 20 W', x=0.01, ha='left', fontsize=13.5, weight='bold')
    fig.savefig(os.path.join(IMG, 'thermal-board-on-render.png'), facecolor=SURF, bbox_inches='tight'); plt.close(fig)

if __name__ == '__main__':
    os.makedirs(IMG, exist_ok=True)
    S_ = summary(); timeline(); parts_bar(S_); v = losses()
    if 'nomaps' not in sys.argv: maps()
    if RENDER: board_overlay()
    for k, r in S_.items(): print(k, {a: (round(b, 1) if isinstance(b, float) else b) for a, b in r.items() if a != 'parts_max'})
    print(v)
