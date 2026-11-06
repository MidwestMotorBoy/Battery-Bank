"""Animations of the 2026-11-04 check 1 (board parts striking the cup): the flat drop on the back (cell) face, where
the board's two B.Cu bulk caps C421 / C556 move toward the cell cradles. On the 11-04 geometry they closed a 0.88 mm gap
and took 2200 N; with the caps at the BOM part's 2.0 mm and the cradle relief (2026-11-05) they don't reach.
Reads cache/dyn_back.npz and cache/tables_back.pkl (run_all.py) and the master geometry (bodies.py). No new physics:
every body is drawn at the position dyn.py computed for it, at true scale.
  figs/anim_1_back_section<tag>.gif   section through the two caps (z 46.2): the whole pack, a zoom on C421, the force
  figs/anim_2_back_board<tag>.gif     the board's B.Cu face seen from the cells: where the caps sit over the cradles
Run: python anim.py [--tag _1105] [--label "11-05 geometry"]"""
import os, sys, json, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Polygon, Rectangle
from scipy.spatial import ConvexHull
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'cache'); OUT = os.path.join(HERE, 'out')
FIG = os.path.join(HERE, 'figs')
sys.path.insert(0, HERE)
import bodies as BD, dyn, contacts as CT
import argparse
_ap = argparse.ArgumentParser(); _ap.add_argument('--tag', default=''); _ap.add_argument('--label', default='')
ARGS, _ = _ap.parse_known_args()
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
BLUE, ORANGE, AQUA, YELLOW, GREEN, VIOLET, RED = '#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#008300', '#6250d6', '#c8102e'
GEL = '#f2b8dc'                                   # GEL 30 is pink
plt.rcParams.update({'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF, 'text.color': INK,
                     'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.edgecolor': GRID,
                     'axes.spines.top': False, 'axes.spines.right': False, 'font.size': 9, 'axes.titlesize': 10,
                     'axes.titleweight': 'bold', 'legend.frameon': False})
POSE, CAPS, Z_CUT = 'back', ('C421', 'C556'), 46.2
LIMIT_N = 100.0
FPS = 20

def polys(cs, rot=False):
    """CrossSection -> list of (n, 2) arrays; the screen frame is (y, x): y across, pack x up (the floor is at -x)"""
    out = []
    for p in cs.to_polygons():
        p = np.asarray(p)
        out.append(p[:, [1, 0]] if not rot else p)
    return out

def geometry():
    B, sub, m, prm, A = BD.build()
    RB = BD.P.real_board()
    caps = {k: BD.MF.hull_points(RB[k].reshape(-1, 3)) for k in CAPS}
    G = dict(shell={k: polys(sub[k].slice(Z_CUT)) for k in ('cup_walls', 'cradles', 'lands', 'lips')},
             cells={k: polys(B[k]['m'].slice(Z_CUT)) for k in ('C1', 'C2', 'C3', 'C4')},
             carrier=polys(B['carrier']['m'].slice(Z_CUT)),
             gel=polys(BD.K.filler().slice(Z_CUT)),
             pcb=polys(B['board']['pcb'].slice(Z_CUT)),
             parts=polys((B['board']['parts'] - BD.K.U(*caps.values())).slice(Z_CUT)),
             caps={k: polys(v.slice(Z_CUT)) for k, v in caps.items()})
    for kk, V, _ in A:
        if kk == 'bumpb_band': G['bumper'] = polys(BD.mesh_manifold(V).slice(0.0))
    # the board's B.Cu face from the cells (y-z): outline, B.Cu parts, the cradles' tops under it
    rot = lambda M_: M_.rotate((0, -90, 0))                                      # (x, y, z) -> (-z, y, x)
    face = lambda M_, x: [np.c_[p[:, 1], -p[:, 0]] for p in rot(M_).slice(x).to_polygons()]
    G['b_outline'] = face(B['board']['pcb'], 26.1)
    G['b_cradles'] = face(sub['cradles'], 21.4)
    G['b_gel'] = face(BD.K.filler(), BD.S.sb_xb0 - 0.3)
    bparts = {}
    for k in RB:
        if k.startswith('_') or k == 'PCB': continue
        V = RB[k].reshape(-1, 3)
        if V[:, 0].min() < BD.S.sb_xb0 - 0.05:
            yz = V[:, 1:3]; h = ConvexHull(yz); bparts[k] = yz[h.vertices]
    G['b_parts'] = bparts
    G['cap_xy'] = {k: (float(np.mean(RB[k].reshape(-1, 3)[:, 1])), float(np.mean(RB[k].reshape(-1, 3)[:, 2]))) for k in CAPS}
    d = np.array(dyn.load(POSE)['d'], float)
    G['cap_gap'] = min(CT.first_gap(c, sub['cradles'], d, dmax=4.0) or 9.9 for c in caps.values())   # first touch, mm
    G['cap_h'] = float(BD.S.sb_xb0 - min(RB[k].reshape(-1, 3)[:, 0].min() for k in CAPS))           # off B.Cu, mm
    G['cap_split'] = cap_split(B, sub, caps, G['cap_gap'])
    G['floor_x'] = min(p[:, 1].min() for p in G['bumper'])
    return G

def cap_split(B, sub, caps, g0):
    """how the board/parts-on-cradles force divides between the two caps: their overlap with the cradles against travel"""
    d = np.array(dyn.load(POSE)['d'], float); u = np.linspace(0, g0 + 1.2, 81)
    V = {k: np.array([(c.translate(tuple(d * t)) ^ sub['cradles']).volume() for t in u]) for k, c in caps.items()}
    return dict(u=u, **V)

def history(G):
    R = np.load(os.path.join(CACHE, f'dyn_{POSE}.npz')); names = list(R['names'])
    nm = 'board/parts|shell/cradles|+'                       # no such contact when the caps can't reach the cradles
    F = R['F'][:, names.index(nm)] if nm in names else np.zeros(len(R['t']))
    i = dyn.BODIES.index('board')
    return dict(t=R['t'] * 1e3, x=R['x'], F=F, ff=R['ff'], g0=G['cap_gap'], bodies=dyn.BODIES, travel=R['x'][:, i] - R['x'][:, 0])

def frames(H, v0=np.sqrt(2 * 9.81)):
    """frame times (ms): a short approach before touch-down, the hit, a hold at the peak"""
    tp = H['t'][np.argmax(H['F'])] if H['F'].max() > 0.5 else H['t'][np.argmax(H['travel'])]   # the hit, or the closest approach
    pre = np.linspace(-0.25, 0, 10, endpoint=False)
    main_ = np.r_[np.linspace(0, tp, 70, endpoint=False), np.full(int(1.2 * FPS), tp), np.linspace(tp, min(H['t'][-1], 1.0), 60)]
    return np.r_[pre, main_], tp

def disp(H, body, t, v0=np.sqrt(2 * 9.81)):
    """body travel along d (mm, + toward the floor) at time t (ms); before touch-down everything falls together"""
    if t < 0: return v0 * t                                   # m/s * ms = mm
    i = H['bodies'].index(body)
    return float(np.interp(t, H['t'], H['x'][:, i]))

def section_anim(G, H):
    T, tp = frames(H)
    fig = plt.figure(figsize=(12.8, 7.2))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1], height_ratios=[1.35, 1], hspace=0.35, wspace=0.18,
                          left=0.05, right=0.97, top=0.88, bottom=0.11)
    axA, axB, axC = fig.add_subplot(gs[:, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 1])
    fig.suptitle('Check 1: board parts striking the cup (1 m drop flat on the back face)', fontweight='bold', fontsize=13, x=0.05, ha='left')
    sub_ = fig.text(0.05, 0.905, 'Section through C421 and C556 (z = 46.2 mm). Every part at the position the impact model computed, true scale.',
                    fontsize=9, color=INK2, ha='left')
    style = dict(cup_walls=('#b9b6ae', INK2), cradles=('#8f8b82', INK), lands=('#b9b6ae', INK2), lips=('#b9b6ae', INK2))
    art, cap_art = [], []                                    # (patch, body, base polygon); the cap patches
    def add(ax, P, body, fc, ec, lw=0.6, z=2, alpha=1.0):
        for p in P:
            pa = Polygon(p, closed=True, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha); ax.add_patch(pa); art.append((pa, body, p))
    for ax in (axA, axB):
        add(ax, G['bumper'], 'shell', '#dad7cf', 'none', z=0.5)
        for k, (fc, ec) in style.items(): add(ax, G['shell'][k], 'shell', fc, ec, z=1)
        for k, P in G['cells'].items(): add(ax, P, k, '#cfe9de', AQUA, lw=0.8)
        add(ax, G['carrier'], 'carrier', '#dcd8f5', VIOLET)
        add(ax, G['gel'], 'gel', GEL, '#b8579a', lw=0.6, z=2.5)
        add(ax, G['pcb'], 'board', '#9fcf9f', GREEN)
        add(ax, G['parts'], 'board', '#6b6a66', INK, lw=0.4, z=3)
        for k, P in G['caps'].items():
            n0 = len(art); add(ax, P, 'board', ORANGE, INK, lw=0.8, z=4); cap_art.extend(a[0] for a in art[n0:])
        fx = G['floor_x']
        ax.add_patch(Rectangle((-60, fx - 20), 120, 20, fc='#d6d3cc', ec='none', hatch='////', zorder=6))
        ax.axhline(fx, color=INK, lw=1.2, zorder=7)
        ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_visible(False)
    axA.set_xlim(-31, 31); axA.set_ylim(G['floor_x'] - 4, 39)
    axA.text(0, G['floor_x'] - 2.2, 'concrete', ha='center', va='center', fontsize=8, color=INK2, zorder=8,
             bbox=dict(fc=SURF, ec='none', pad=1))
    lab = dict(fontsize=8, color=INK2, zorder=9)
    axA.annotate('cells', (-20, 2), (-30.5, 9), arrowprops=dict(arrowstyle='-', color=INK2, lw=0.6), **lab)
    axA.annotate('GEL 30 gap filler', (-10, 23.6), (-17, 35.5), color='#b8579a', fontsize=8, zorder=9,
                 arrowprops=dict(arrowstyle='-', color='#b8579a', lw=0.6))
    axA.annotate('board (PCB)', (0, 26.1), (6, 35), arrowprops=dict(arrowstyle='-', color=INK2, lw=0.6), **lab)
    axA.annotate('cell cradles\n(part of the cup)', (21, 17.5), (24.2, 5), arrowprops=dict(arrowstyle='-', color=INK2, lw=0.6), **lab)
    cy = {k: G['cap_xy'][k][0] for k in CAPS}
    for k in CAPS:
        axA.annotate(k, (cy[k], 22.9), (cy[k] + (6 if cy[k] > 0 else -12), 31), color=ORANGE, fontweight='bold', fontsize=9, zorder=9,
                     arrowprops=dict(arrowstyle='-', color=ORANGE, lw=0.9))
    axA.text(-30.5, G['floor_x'] + 1, 'bumper ring\n(at the cap end, behind)', fontsize=7, color=INK2, zorder=9, va='bottom')
    # zoom on C421
    yc = cy['C421']; axB.set_xlim(yc - 4.2, yc + 4.2); axB.set_ylim(19.6, 27.6)
    axB.set_title('Zoom on C421 over its cradle', loc='left', fontsize=10)
    gap_txt = axB.text(0.02, 0.96, '', transform=axB.transAxes, fontsize=10, fontweight='bold', color=INK, zorder=10, va='top',
                       bbox=dict(fc=SURF, ec=GRID, pad=3))
    axB.plot([yc + 3.4, yc + 3.4 + 1.0], [20.1, 20.1], color=INK, lw=2, zorder=10, solid_capstyle='butt')
    axB.text(yc + 3.9, 20.35, '1 mm', ha='center', fontsize=7, color=INK2, zorder=10)
    gap_ln, = axB.plot([], [], color=RED, lw=1.5, zorder=9)
    # force
    t, F = H['t'], H['F']
    axC.plot(t, F, color=ORANGE, lw=2.2, label='C421 + C556 on the cradles')
    axC.axhline(LIMIT_N, color=RED, lw=1, ls=':'); axC.text(1.0, LIMIT_N + 40, 'limit ~100 N (est.)', color=RED, fontsize=7.5, ha='right')
    axC.set_xlim(-0.25, 1.0); axC.set_ylim(0, max(F.max(), 2.5 * LIMIT_N) * 1.2)
    axC.set_xlabel('time from touch-down, ms'); axC.set_ylabel('force, N'); axC.grid(color=GRID, lw=0.5); axC.legend(fontsize=7.5, loc='upper right')
    axC.set_title('Contact force', loc='left', fontsize=10)
    cur = axC.axvline(0, color=INK, lw=0.8); dot, = axC.plot([], [], 'o', color=ORANGE, ms=6, zorder=5)
    peak_txt = axC.text(0.02, 0.88, '', transform=axC.transAxes, fontsize=9, fontweight='bold', color=RED)
    clock = axA.text(0.0, 1.0, '', transform=axA.transAxes, fontsize=10, fontweight='bold', va='top')
    fig.text(0.05, 0.035, 'GEL 30 is drawn between B.Cu and the front cells, squeezed by their motion; the impact model carries it as mass only (no load path).',
             fontsize=7.5, color=INK2)
    fig.text(0.05, 0.015, f'Impact model: rigid bodies, no rotation, board rigid. Caps as this model has them: {G["cap_h"]:.1f} mm off B.Cu '
             f'(the BOM part, KEMET T593V 7343-20, is 2.0 mm). First-touch gap to the cradles {G["cap_gap"]:.2f} mm.', fontsize=7.5, color=INK2)
    if ARGS.label: fig.text(0.97, 0.955, ARGS.label, fontsize=11, fontweight='bold', ha='right', color=BLUE)
    def g_of(t_):
        b = disp(H, 'board', t_) - disp(H, 'shell', t_)
        return H['g0'] - b
    def update(k):
        t_ = T[k]
        for pa, body, p in art:
            if body == 'gel':                                # B.Cu side rides with the board, can side with its cell
                on_b = p[:, 1] > BD.S.sb_xb0 - 0.05
                dc = np.where(p[:, 0] < 0, disp(H, 'C1', t_), disp(H, 'C4', t_))
                pa.set_xy(p - np.c_[np.zeros(len(p)), np.where(on_b, disp(H, 'board', t_), dc)]); continue
            dx = disp(H, body, t_)
            pa.set_xy(p - [0, dx])                          # travel toward the floor (-x) moves down on screen
        f = float(np.interp(t_, t, F)) if t_ >= 0 else 0.0
        gap = g_of(t_) if t_ >= 0 else H['g0']
        gap_txt.set_text(f'gap to the cradle {max(gap, 0):.2f} mm' if gap > 0 else f'contact: {f:,.0f} N on the two caps')
        gap_txt.set_color(RED if gap <= 0 else INK)
        # the gap marker: from the cap's lowest point to the cradle top under it
        cap_low = min(p[:, 1].min() for p in G['caps']['C421']) - disp(H, 'board', t_)
        cr_top = cap_low - max(gap, 0)
        gap_ln.set_data(*(([yc, yc], [cr_top, cap_low]) if gap > 0 else ([], [])))
        for pa in cap_art: pa.set_facecolor(RED if f > LIMIT_N else ORANGE)
        cur.set_xdata([t_]); dot.set_data([t_], [f])
        clock.set_text(f't = {t_:+.3f} ms' + ('   (falling at 4.43 m/s)' if t_ < 0 else ''))
        if F.max() > 0.5: peak_txt.set_text(f'peak {F.max():,.0f} N = {F.max() / LIMIT_N:.0f}x the limit' if t_ >= tp - 1e-9 else '')
        else: peak_txt.set_text(f'no contact: closest {H["g0"] - H["travel"].max():.2f} mm' if t_ >= tp - 1e-9 else ''); peak_txt.set_color(GREEN)
        return []
    an = FuncAnimation(fig, update, frames=len(T), interval=1000 / FPS)
    p = os.path.join(FIG, f'anim_1_back_section{ARGS.tag}.gif'); an.save(p, writer=PillowWriter(fps=FPS), dpi=90)
    update(int(np.argmax(T >= tp))); fig.savefig(os.path.join(FIG, f'anim_1_back_section{ARGS.tag}_peak.png'), dpi=130)
    plt.close(fig); print('  ', os.path.relpath(p, HERE))

def board_anim(G, H):
    T, tp = frames(H)
    fig, (ax, axg) = plt.subplots(1, 2, figsize=(10.5, 7.2), gridspec_kw=dict(width_ratios=[1.5, 1], wspace=0.25, left=0.04, right=0.96, top=0.86, bottom=0.08))
    fig.suptitle('Check 1: where it happens on the board (back-face drop)', fontweight='bold', fontsize=13, x=0.04, ha='left')
    fig.text(0.04, 0.895, "The board's B.Cu side, seen from the cells. Grey bands: the cup's cell cradles under the board. Pink: the GEL 30 zones.", fontsize=9, color=INK2)
    for p in G['b_cradles']: ax.add_patch(Polygon(p, fc='#cfccc4', ec='#8f8b82', lw=0.6, zorder=1))
    for p in G['b_outline']: ax.add_patch(Polygon(p, fc='#9fcf9f', ec=GREEN, lw=1, alpha=0.55, zorder=2))
    for p in G['b_gel']: ax.add_patch(Polygon(p, fc=GEL, ec='#b8579a', lw=0.6, alpha=0.9, zorder=2.5))
    ax.text(-11.5, 29, 'GEL 30', fontsize=7, color='#b8579a', ha='center', zorder=6)
    cap_patch = {}
    for k, p in G['b_parts'].items():
        hot = k in CAPS
        pa = Polygon(p, fc=ORANGE if hot else '#8a8984', ec=INK, lw=0.8 if hot else 0.4, zorder=4 if hot else 3); ax.add_patch(pa)
        if hot: cap_patch[k] = pa
        elif np.ptp(p[:, 0]) > 3 or np.ptp(p[:, 1]) > 3: ax.text(*p.mean(0), k, fontsize=5.5, ha='center', va='center', color='white', zorder=5)
    for k, (y, z) in G['cap_xy'].items():
        ax.annotate(k, (y, z), (y + (-9 if y > 0 else 9), z + 9), ha='center', fontweight='bold', color=ORANGE, fontsize=10, zorder=6,
                    arrowprops=dict(arrowstyle='-', color=ORANGE, lw=1))
    ax.annotate('USB-C ports', (0, 76), (0, 84), ha='center', fontsize=8, color=INK2)
    ax.set_xlim(-26, 26); ax.set_ylim(0, 88); ax.set_aspect('equal'); ax.set_xlabel('y, mm (across)'); ax.set_ylabel('z, mm (along the cells; port end up)')
    ax.invert_xaxis()                                          # seen from the cells (from -x): +y is on the left
    ax.grid(color=GRID, lw=0.4); ax.set_axisbelow(True)
    # per-cap gauges: gap left, then force
    sp = G['cap_split']; Fy = H['F']
    def split(t_):
        b = disp(H, 'board', t_) - disp(H, 'shell', t_)            # the split tables are on the board's travel itself
        v = {k: np.interp(max(b, 0), sp['u'], sp[k]) for k in CAPS}; s = sum(v.values())
        f = float(np.interp(t_, H['t'], Fy)) if t_ >= 0 else 0.0
        return {k: (f * v[k] / s if s > 0 else 0.0) for k in CAPS}, H['g0'] - b
    axg.set_xlim(0, 2); axg.set_ylim(0, max(1300 if H['F'].max() > 0.5 else 300, 1.15 * H['F'].max() / 2)); axg.set_xticks([0.5, 1.5], CAPS); axg.set_ylabel('force on the cap, N')
    axg.axhline(LIMIT_N, color=RED, lw=1, ls=':'); axg.text(1.0, LIMIT_N + 20, 'limit ~100 N (est.)', color=RED, fontsize=7.5, ha='center')
    axg.grid(axis='y', color=GRID, lw=0.5); axg.set_axisbelow(True)
    axg.set_title('Load on each cap', loc='left', fontsize=10)
    bars = axg.bar([0.5, 1.5], [0, 0], width=0.55, color=ORANGE)
    btxt = [axg.text(x, 0, '', ha='center', va='bottom', fontsize=9, fontweight='bold') for x in (0.5, 1.5)]
    gtxt = axg.text(0.5, 0.93, '', transform=axg.transAxes, ha='center', fontsize=10, fontweight='bold')
    clock = ax.text(0.98, 0.98, '', transform=ax.transAxes, fontsize=10, fontweight='bold', ha='right', va='top',
                    bbox=dict(fc=SURF, ec='none', pad=2))
    if ARGS.label: fig.text(0.96, 0.955, ARGS.label, fontsize=11, fontweight='bold', ha='right', color=BLUE)
    fig.text(0.04, 0.015, f'Force split between the caps by their overlap with the cradles. Impact model: board rigid, caps {G["cap_h"]:.1f} mm off B.Cu, first-touch gap {G["cap_gap"]:.2f} mm.',
             fontsize=7.5, color=INK2)
    def update(k):
        t_ = T[k]; f, gap = split(t_) if t_ >= 0 else ({c: 0.0 for c in CAPS}, H['g0'])
        for b, tx, c in zip(bars, btxt, CAPS):
            b.set_height(f[c]); b.set_color(RED if f[c] > LIMIT_N else ORANGE)
            tx.set_position((tx.get_position()[0], f[c] + 15)); tx.set_text(f'{f[c]:,.0f} N' if f[c] > 0.5 else '')
            cap_patch[c].set_facecolor(RED if f[c] > LIMIT_N else ORANGE)
        gtxt.set_text(f'gap left {gap:.2f} mm' if gap > 0 else 'caps on the cradles'); gtxt.set_color(INK if gap > 0 else RED)
        clock.set_text(f't = {t_:+.3f} ms')
        return []
    an = FuncAnimation(fig, update, frames=len(T), interval=1000 / FPS)
    p = os.path.join(FIG, f'anim_2_back_board{ARGS.tag}.gif'); an.save(p, writer=PillowWriter(fps=FPS), dpi=90)
    plt.close(fig); print('  ', os.path.relpath(p, HERE))

if __name__ == '__main__':
    os.makedirs(FIG, exist_ok=True)
    G = geometry(); H = history(G)
    section_anim(G, H); board_anim(G, H)
