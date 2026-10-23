"""Thermal maps from pack3d.py results: a 3-D view of the cells and board, two sections through the pack, the board,
and each cell's can surface unrolled. Run after pack3d.py: python render.py [case ...] -> renders/<case>_*.png, renders/series.json"""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from scipy.ndimage import map_coordinates
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack3d as P

HERE = os.path.dirname(os.path.abspath(__file__)); RD = os.path.join(HERE, 'renders')
SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#d9d8d3'
# one warm hue, light -> dark (monotonic lightness), so hotter always reads darker
CMAP = LinearSegmentedColormap.from_list('warm', ['#fff6ee', '#fbd5b8', '#f4a77c', '#eb6834', '#c4481b', '#8f2f0e', '#4e1704'])
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': INK, 'axes.labelcolor': INK2,
                     'axes.edgecolor': GRID, 'xtick.color': INK2, 'ytick.color': INK2, 'figure.facecolor': SURF,
                     'axes.facecolor': SURF, 'axes.titlesize': 11, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left'})

class Field:
    def __init__(self, g, th, amb):
        self.g = g; T = np.full(g.n, np.nan); T[g.dom] = th + amb; self.T = T
        self.Tf = np.where(np.isnan(T), amb, T)                 # for interpolation
    def at(self, x, y, z, order=1):
        g = self.g
        ix = [(np.asarray(v) - c[0]) / h for v, c, h in zip((x, y, z), g.c, g.h)]
        return map_coordinates(self.Tf, ix, order=order, mode='nearest')
    def plane(self, d, v):
        g = self.g; i = int(np.clip(np.searchsorted(g.edges[d], v) - 1, 0, g.n[d] - 1))
        sl = [slice(None)]*3; sl[d] = i
        return self.T[tuple(sl)], g.mat[tuple(sl)]

def cyl_unwrap(F, k, nphi=180, nz=120, r=None):
    _, cx, cy, _ = P.CELLS[k]; r = r or P.R_CAN_IN + 0.1
    phi = np.linspace(-np.pi, np.pi, nphi); z = np.linspace(P.Z_C0 + 0.5, P.Z_C1 - 0.5, nz)
    PH, Z = np.meshgrid(phi, z)
    return phi, z, F.at(cx + r*np.cos(PH), cy + r*np.sin(PH), Z)

def outlines(ax, d):
    """draw cell, board and cup outlines on a section; d = the plane's normal (2 for xy, 1 for xz)"""
    kw = dict(color=INK, lw=0.6, alpha=0.55)
    if d == 2:
        t = np.linspace(0, 2*np.pi, 200)
        for _, cx, cy, _ in P.CELLS: ax.plot(cx + P.R_CELL*np.cos(t), cy + P.R_CELL*np.sin(t), **kw)
        ax.add_patch(plt.Rectangle((P.BOARD_X[0], -P.BOARD_HW), P.BOARD_X[1] - P.BOARD_X[0], 2*P.BOARD_HW, fill=False, **kw))
    else:
        for _, cx, cy, _ in P.CELLS:
            if cy > 0: ax.add_patch(plt.Rectangle((cx - P.R_CELL, P.Z_C0), 2*P.R_CELL, P.Z_C1 - P.Z_C0, fill=False, **kw))
        ax.add_patch(plt.Rectangle((P.BOARD_X[0], P.BOARD_Z[0]), P.BOARD_X[1] - P.BOARD_X[0], P.BOARD_Z[1] - P.BOARD_Z[0], fill=False, **kw))

def section(ax, F, d, v, norm, title, contour_step):
    T, m = F.plane(d, v); g = F.g
    a, b = [i for i in range(3) if i != d]
    ext = (g.edges[a][0], g.edges[a][-1], g.edges[b][0], g.edges[b][-1])
    img = np.ma.masked_invalid(T.T)
    ax.imshow(img, origin='lower', extent=ext, cmap=CMAP, norm=norm, interpolation='bilinear')
    lv = np.arange(np.floor(norm.vmin/contour_step)*contour_step, norm.vmax + 1e-6, contour_step)
    cs = ax.contour(g.c[a], g.c[b], np.ma.masked_invalid(T.T), levels=lv, colors=INK2, linewidths=0.5, alpha=0.8)
    ax.clabel(cs, fmt='%d', fontsize=7, inline_spacing=2)
    outlines(ax, d)
    ax.set_aspect('equal'); ax.set_title(title)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_xlabel('xyz'[a] + ' (mm)'); ax.set_ylabel('xyz'[b] + ' (mm)')

def render3d(ax, F, norm):
    """the four cans and an exploded board (moved 14 mm off the cells), coloured by temperature"""
    for k, (name, cx, cy, _) in enumerate(P.CELLS):
        phi, z, T = cyl_unwrap(F, k, 90, 60, r=P.R_CAN_IN + 0.1)
        PH, Z = np.meshgrid(phi, z)
        X, Y = cx + P.R_CELL*np.cos(PH), cy + P.R_CELL*np.sin(PH)
        ax.plot_surface(X, Y, Z, facecolors=CMAP(norm(T)), rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)
        tt = np.linspace(0, 2*np.pi, 60)
        for zz in (P.Z_C0, P.Z_C1): ax.plot(cx + P.R_CELL*np.cos(tt), cy + P.R_CELL*np.sin(tt), zz, color=INK2, lw=0.4)
        ax.text(cx, cy, P.Z_C1 + 5, name, ha='center', fontsize=9, color=INK, zorder=10)
    g = F.g; xb = 0.5*sum(P.BOARD_X)
    y = np.linspace(-P.BOARD_HW, P.BOARD_HW, 70); z = np.linspace(P.BOARD_Z[0], P.BOARD_Z[1], 110)
    Yb, Zb = np.meshgrid(y, z)
    Tb = F.at(np.full_like(Yb, xb), Yb, Zb)
    inb = np.isin(g.mat[np.clip(np.searchsorted(g.edges[0], xb) - 1, 0, None)], (P.BOARD, P.VIAS))
    iy = np.clip(((Yb - g.c[1][0])/g.h[1]).round().astype(int), 0, g.n[1] - 1); iz = np.clip(((Zb - g.c[2][0])/g.h[2]).round().astype(int), 0, g.n[2] - 1)
    fc = CMAP(norm(Tb)); fc[~inb[iy, iz]] = (0, 0, 0, 0)
    EX = 34.0
    ax.plot_surface(np.full_like(Yb, xb + EX), Yb, Zb, facecolors=fc, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)
    ax.text(xb + EX, 0, P.BOARD_Z[1] + 6, f'board, pulled out {EX:.0f} mm', ha='center', fontsize=8, color=INK2)
    ax.view_init(elev=18, azim=-62); ax.set_box_aspect((96, 52, 75))
    ax.set_xlim(-24, 62); ax.set_ylim(-24, 24); ax.set_zlim(0, 84)
    ax.set_axis_off()

def case_maps(name, snap='peak_cell'):
    z = np.load(os.path.join(P.OUT_DIR, f'{name}.npz')); meta = json.load(open(os.path.join(P.OUT_DIR, f'{name}.json')))
    g = P.get_grid(); g.assemble(10.0)
    if 'snap_steady' in z: snap = 'steady'
    key = f'snap_{snap}'
    F = Field(g, z[key].astype(float), meta['amb'])
    when = {'steady': 'steady state', 'peak_cell': f"at {meta.get('t_peak_cell', 0):.0f} min, when the cells are hottest",
            'peak_board': f"at {meta.get('t_peak_board', 0):.0f} min, when the board is hottest"}[snap]
    tag = '' if snap == 'steady' else '_' + snap
    os.makedirs(RD, exist_ok=True)
    norm = Normalize(25, 60)
    # 1 overview: 3-D, xy section through the power stages, xz section through USB1's stage and C4/C3
    fig = plt.figure(figsize=(17, 6.6), dpi=110)
    gs0 = fig.add_gridspec(1, 4, width_ratios=[1.35, 1.05, 0.9, 0.04], wspace=0.25)
    ax = fig.add_subplot(gs0[0, 0], projection='3d'); render3d(ax, F, norm); ax.set_title('Cans and board', loc='left')
    ax = fig.add_subplot(gs0[0, 1]); section(ax, F, 2, 40.0, norm, 'Across the pack at z = 40 mm\n(through both power stages)', 2)
    ax.text(29, -24.5, 'board', fontsize=8, color=INK2, ha='center'); ax.text(-11.6, -11.6, 'C2', ha='center', va='center', fontsize=9)
    ax.text(11.6, -11.6, 'C1', ha='center', va='center', fontsize=9); ax.text(-11.6, 11.6, 'C3', ha='center', va='center', fontsize=9)
    ax.text(11.6, 11.6, 'C4', ha='center', va='center', fontsize=9)
    ax = fig.add_subplot(gs0[0, 2]); section(ax, F, 1, P.PR, norm, 'Lengthwise at y = +11.6 mm\n(C3, C4 and the USB1 stage)', 2)
    ax.text(-11.6, 42, 'C3', ha='center', fontsize=9); ax.text(11.6, 42, 'C4', ha='center', fontsize=9)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=CMAP)
    cb = fig.colorbar(sm, cax=fig.add_subplot(gs0[0, 3])); cb.set_label('°C (same scale for every case)'); cb.outline.set_visible(False)
    fig.suptitle(f"{meta['title']}: {when}", x=0.01, ha='left', fontsize=14, weight='bold')
    fig.savefig(os.path.join(RD, f'{name}{tag}_pack.png'), facecolor=SURF, bbox_inches='tight'); plt.close(fig)
    # 2 board and cells: each with its own scale so the gradients show
    Tb, mb = F.plane(0, 0.5*sum(P.BOARD_X))
    Tb = np.where(np.isin(mb, (P.BOARD, P.VIAS)), Tb, np.nan)
    unw = [cyl_unwrap(F, k) for k in range(4)]
    lo = np.floor(min(np.nanmin(u[2]) for u in unw)); hi = np.ceil(max(np.nanmax(u[2]) for u in unw))
    if hi - lo < 1: hi = lo + 1
    blo, bhi = np.floor(np.nanmin(Tb)), np.ceil(np.nanmax(Tb))
    if bhi - blo < 1: bhi = blo + 1
    fig = plt.figure(figsize=(17, 6.2), dpi=110)
    gs = fig.add_gridspec(1, 8, width_ratios=[1.25, 0.05, 0.22, 1, 1, 1, 1, 0.05], wspace=0.28)
    ax = fig.add_subplot(gs[0, 0]); bn = Normalize(blo, bhi)
    ax.imshow(np.ma.masked_invalid(Tb.T), origin='lower', extent=(g.edges[1][0], g.edges[1][-1], g.edges[2][0], g.edges[2][-1]),
              cmap=CMAP, norm=bn, interpolation='bilinear')
    step = max(1, int((bhi - blo)/8))
    cs = ax.contour(g.c[1], g.c[2], np.ma.masked_invalid(Tb.T), levels=np.arange(blo, bhi + 0.1, step), colors=INK2, linewidths=0.5)
    ax.clabel(cs, fmt='%d', fontsize=7)
    for nm, bx in P.src_boxes().items():
        if nm.startswith(('fet', 'ind', 'ic', 'pphv', 'conn', 'prot', 'fuse', 'shunt')):
            for x0, x1, y0, y1, z0, z1 in bx:
                ax.add_patch(plt.Rectangle((y0, z0), y1 - y0, z1 - z0, fill=False, lw=0.6, color=INK, alpha=0.6))
    for lab, (y, zz) in {'USB1 stage': (11.6, 54.5), 'USB2 stage': (-11.6, 54.5), 'protection FETs': (0, 15.5),
                         'USB1': (6.5, 68), 'USB2': (-6.5, 68)}.items():
        ax.text(y, zz, lab, ha='center', fontsize=7.5, color=INK)
    ax.set_xlim(-23, 23); ax.set_ylim(2, 81); ax.set_aspect('equal'); ax.set_xlabel('y (mm)'); ax.set_ylabel('z (mm)')
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_title(f'Board\n({blo:.0f}–{bhi:.0f} °C scale)')
    cax = fig.add_subplot(gs[0, 1]); cb = fig.colorbar(plt.cm.ScalarMappable(norm=bn, cmap=CMAP), cax=cax); cb.outline.set_visible(False)
    cn = Normalize(lo, hi)
    for k in range(4):
        ax = fig.add_subplot(gs[0, 3 + k]); phi, zz, T = unw[k]
        ax.imshow(T, origin='lower', extent=(-180, 180, zz[0], zz[-1]), aspect='auto', cmap=CMAP, norm=cn, interpolation='bilinear')
        st = 0.5 if hi - lo <= 4 else 1 if hi - lo <= 10 else 2
        cs = ax.contour(np.degrees(phi), zz, T, levels=np.arange(lo, hi + 1e-6, st), colors=INK2, linewidths=0.5)
        ax.clabel(cs, fmt='%g', fontsize=7)
        name_, cx, cy, _ = P.CELLS[k]
        bdir = np.degrees(np.arctan2(0, 1))                    # +x (board) is phi = 0
        cdir = np.degrees(np.arctan2(-cy, -cx))
        ax.axvline(bdir, color=INK2, lw=0.6, ls=(0, (3, 3))); ax.axvline(cdir, color=INK2, lw=0.6, ls=(0, (1, 2)))
        ax.set_xticks([-180, -90, 0, 90, 180]); ax.set_xlabel('° round the can')
        if k == 0: ax.set_ylabel('z (mm)')
        role = 'front' if k in P.FRONT else 'back'
        ax.set_title(f'{name_} ({role})\n{np.nanmin(T):.1f}–{np.nanmax(T):.1f} °C')
        for s in ax.spines.values(): s.set_visible(False)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=cn, cmap=CMAP), cax=fig.add_subplot(gs[0, 7])); cb.outline.set_visible(False)
    cb.set_label('°C')
    fig.suptitle(f"{meta['title']}: the board and each can surface unrolled, {when}\n0° faces the board (dashed); dotted = faces the pack centre (assumed NTC side)",
                 x=0.01, ha='left', fontsize=12.5, weight='bold')
    fig.subplots_adjust(top=0.80)
    fig.savefig(os.path.join(RD, f'{name}{tag}_cells.png'), facecolor=SURF, bbox_inches='tight'); plt.close(fig)
    # radial profile through the hottest front cell at its hottest z: core vs surface
    return F

def series(names):
    out = {}
    for n in names:
        z = np.load(os.path.join(P.OUT_DIR, f'{n}.npz')); meta = json.load(open(os.path.join(P.OUT_DIR, f'{n}.json')))
        if 'rec_ntc' not in z: out[n] = dict(meta=meta); continue
        t = z['rec_t']; step = max(1, int(round(0.5/(t[1] - t[0])))) if len(t) > 1 else 1      # ~30 s points
        s = slice(None, None, step)
        r = lambda k: np.round(z[f'rec_{k}'][s], 2).tolist()
        out[n] = dict(meta=meta, t=np.round(t[s], 2).tolist(), p_out=r('p_out'), p_in=r('p_in'), soc=r('soc'), i_bat=r('i_bat'),
                      q_cells=r('q_cells'), q_board=r('q_board'), ntc=r('ntc'), ntc_alt=r('ntc_alt'), cell_max=r('cell_max'),
                      cell_min=r('cell_min'), cell_mean=r('cell_mean'), surf_max=r('surf_max'), surf_min=r('surf_min'),
                      board_max=r('board_max'), part_max=r('part_max'), skin_max=r('skin_max'), ts1=r('ts1'), ts2=r('ts2'))
    os.makedirs(RD, exist_ok=True)
    json.dump(out, open(os.path.join(RD, 'series.json'), 'w'))
    return out

if __name__ == '__main__':
    names = sys.argv[1:] or [n for n in P.CASES if os.path.exists(os.path.join(P.OUT_DIR, f'{n}.npz'))]
    for n in names:
        for sn in (('steady',) if n == 'idle' else ('peak_board', 'peak_cell')): case_maps(n, sn)
        print('rendered', n)
    series([n for n in P.CASES if os.path.exists(os.path.join(P.OUT_DIR, f'{n}.npz'))])
