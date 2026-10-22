"""Thermal rundown with everything learned so far: the corrected loss model (Loss reduction/summary.md), cell resistance and
pack voltage that follow the state of charge, the four-node thermal model (thermal_derate.py) with its linear derates,
for three builds: the current tray, the cup with today's parts, and the cup with the four P0 loss cuts.
Lumped estimates, 25 C ambient, not measurements. Run: python thermal_rundown.py -> table + thermal_rundown.png"""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import thermal_derate as TD

# ---------------- losses ----------------
BASE = dict(prot=2*0.0057, fuse=0.0025, shunt=0.001, pack_cu=0.002, nickel=0.0085, rbat=0.005, rac=0.005,
            fet=0.013, fet_9v=None, ind=0.015, core=0.20, fsw=600e3, pphv=0.018, conn=0.010, gate=0.20, ldo=0.0)
P0 = dict(BASE, prot=2*0.0024, nickel=0.0041, fet_9v=0.0090, ind=0.012, core=0.15, fsw=500e3, ldo=0.09)
#   P0: XRS120N04D protection FETs; 0.2 x 10 Ni strips + Cu PACK tails; 9 V DRV_SUP (LDO, on above 45 W);
#       XGL7030-332 at 500 kHz. Fuse F102 2.5 mOhm and the warm inductor / gate-drive corrections apply to both.
T_EDGE, T_DEAD, V_BODY, C_OSS = 10e-9, 45e-9, 0.8, 600e-12
def ocv(soc):          # per cell, rough NMC curve
    return np.interp(soc, [0.0, 0.05, 0.10, 0.20, 0.50, 0.80, 1.0], [3.00, 3.25, 3.38, 3.50, 3.65, 3.92, 4.18])
def r_cell(soc):       # DC, new, 25 C: 22 mOhm mid-charge, ~33 near empty (Loss reduction D)
    return float(np.interp(soc, [0.0, 0.10, 0.25, 1.0], [0.036, 0.031, 0.022, 0.021]))
def losses(p, v_usb, soc, prm, charging=False):
    """returns (board W, cells+nickel W, battery current A)"""
    v_pack = 4*ocv(soc); rc = r_cell(soc)
    fet = prm['fet_9v'] if (prm['fet_9v'] and p >= 45) else prm['fet']
    ldo = prm['ldo'] if (prm['fet_9v'] and p >= 45) else 0.0
    i_usb = p / v_usb; i_bat = p / v_pack
    for _ in range(4):
        cells = 4*rc*i_bat**2; nickel = prm['nickel']*i_bat**2
        path = (prm['prot'] + prm['fuse'] + prm['shunt'] + prm['pack_cu'])*i_bat**2
        if charging or v_usb <= v_pack:
            v_hi = v_usb if charging else v_pack; i_l = i_bat if charging else i_usb
        else:
            v_hi = v_usb; i_l = i_bat
        cond = fet*i_l**2*2                                    # 100 %-on FET + the switching leg's two FETs (d + 1-d)
        sw = 0.5*v_hi*i_l*T_EDGE*prm['fsw'] + 0.5*C_OSS*v_hi**2*prm['fsw'] + 2*T_DEAD*prm['fsw']*V_BODY*i_l
        ind = prm['ind']*i_l**2 + prm['core']*min(1.0, v_hi/20)
        sense = prm['rbat']*i_bat**2 + prm['rac']*i_usb**2
        usb = (prm['pphv'] + prm['conn'])*i_usb**2
        board = path + cond + sw + ind + sense + usb + prm['gate'] + ldo
        tot = board + cells + nickel
        i_bat = ((p + tot) if not charging else (p - tot)) / v_pack
    return board, cells + nickel, i_bat

# ---------------- thermal run (four-node model from thermal_derate, SOC tracked) ----------------
BUILDS = {'Current tray (today\'s parts)': ('Current: 1 mm Al cover', BASE),
          'Cup (today\'s parts)': ('Cup: coupled + PA12 webs', BASE),
          'Cup + P0 loss cuts': ('Cup: coupled + PA12 webs', P0)}
CAP_WH = 82.0
def run(build, demand, v_usb=20.0, mode='dis', soc0=None, hours=6.0, derate=True, amb=TD.AMB):
    design, prm = BUILDS[build]; d = TD.DESIGNS[design]; CL = d['al']*0.90
    B = L = F = K = amb; soc = (1.0 if mode == 'dis' else 0.0) if soc0 is None else soc0
    rec = []
    for i in range(int(hours*3600)):
        f = 1.0
        if derate:
            f = min(TD.ramp(B, TD.BANDS['board']), TD.ramp(max(F, K), TD.BANDS['cell_dis' if mode == 'dis' else 'cell_chg']))
        p = demand*f
        pb, pc, ib = losses(p, v_usb, soc, prm, mode == 'chg')
        qbl = d['gbl']*(B - L) if CL else 0.0; qbf = d['gbf']*(B - F); qfk = d['gfk']*(F - K)
        B += (pb - qbl - qbf - d['gba']*(B - amb)) / TD.CB
        if CL: L += (qbl - d['gla']*(L - amb)) / CL
        F += (pc/2 + qbf - qfk - TD.G_SKIN*(F - amb)) / TD.CPAIR
        K += (pc/2 + qfk - TD.G_SKIN*(K - amb)) / TD.CPAIR
        v_pack = 4*ocv(soc)
        soc += (-1 if mode == 'dis' else 1) * ib*v_pack/3600/CAP_WH
        rec.append((i/60, p, B, F, K, soc, pb, pc))
        if (mode == 'dis' and (soc <= 0.0 or v_pack < 4*3.0)) or (mode == 'chg' and soc >= 1.0): break
    a = np.array(rec)
    return dict(t=a[:, 0], P=a[:, 1], B=a[:, 2], F=a[:, 3], K=a[:, 4], soc=a[:, 5], pb=a[:, 6], pc=a[:, 7])
def wh(r, minutes=None):
    m = r['t'] < (minutes if minutes is not None else 1e9); return r['P'][m].sum()/3600
def full_minutes(r, demand):
    below = np.nonzero(r['P'] < demand*0.99)[0]; return (below[0] if len(below) else len(r['P']))/60

if __name__ == '__main__':
    print('Losses (board / cells+nickel, W) at mid charge and near empty (10 %)')
    for name, prm in (('today', BASE), ('P0 cuts', P0)):
        row = []
        for lab, p, v, soc, ch in (('30 W', 30, 15, 0.5, False), ('100 W', 100, 20, 0.5, False), ('100 W @10 %', 100, 20, 0.10, False),
                                   ('88 W chg', 88, 20, 0.5, True)):
            b, c, _ = losses(p, v, soc, prm, ch); row.append(f'{lab}: {b:.1f} / {c:.1f} = {b+c:.1f}')
        print(f'   {name:8s} ' + '   '.join(row))
    res = {}
    for b in BUILDS:
        r30 = run(b, 30, v_usb=15); r100 = run(b, 100); rlo = run(b, 100, soc0=0.25); rch = run(b, 88, mode='chg')
        res[b] = (r30, r100, rlo, rch)
        print(f"\n{b}")
        print(f"   30 W: {r30['t'][-1]/60:.2f} h to empty, peak board {r30['B'].max():.0f} C, hottest cell {max(r30['F'].max(), r30['K'].max()):.0f} C, derated: {'yes' if r30['P'].min() < 29.9 else 'no'}")
        print(f"   100 W asked, full pack: {full_minutes(r100, 100):.1f} min at full power, {wh(r100, 20):.1f} Wh in 20 min, empty at {r100['t'][-1]:.0f} min, "
              f"{wh(r100):.1f} Wh delivered, peak board {r100['B'].max():.0f}, hottest cell {max(r100['F'].max(), r100['K'].max()):.0f}")
        print(f"   100 W asked from 25 % charge: {full_minutes(rlo, 100):.1f} min at full power, mean {np.mean(rlo['P']):.0f} W, empty at {rlo['t'][-1]:.0f} min")
        print(f"   88 W charging: full at {rch['t'][-1]:.0f} min, {full_minutes(rch, 88):.1f} min at full rate, hottest cell {max(rch['F'].max(), rch['K'].max()):.0f} C")
    if len(sys.argv) > 1 and sys.argv[1] == 'nochart': sys.exit()

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    SURF, INK, INK2, GRID, BANDC = '#fcfcfb', '#0b0b0b', '#52514e', '#e6e5e1', '#f1f0ec'
    COL = {'Current tray (today\'s parts)': '#2a78d6', 'Cup (today\'s parts)': '#1baf7a', 'Cup + P0 loss cuts': '#6250d6'}
    plt.rcParams.update({'font.family': 'Segoe UI', 'font.size': 11, 'text.color': INK, 'axes.labelcolor': INK2, 'axes.edgecolor': GRID,
                         'xtick.color': INK2, 'ytick.color': INK2, 'axes.titlesize': 13, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
                         'figure.facecolor': SURF, 'axes.facecolor': SURF})
    def style(ax):
        ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
        for s in ('top', 'right'): ax.spines[s].set_visible(False)
    hot = lambda r: np.maximum(r['F'], r['K'])
    fig = plt.figure(figsize=(18, 12), dpi=150)
    gs = fig.add_gridspec(2, 3, hspace=0.42, wspace=0.25, left=0.05, right=0.98, top=0.87, bottom=0.07)
    fig.text(0.02, 0.955, 'Thermal rundown: current tray vs the cup, before and after the P0 loss cuts', fontsize=20, weight='bold')
    fig.text(0.02, 0.925, 'Corrected losses, cell resistance and pack voltage following the charge, linear derates (board 60→75 °C, cells 45→55 °C discharging, '
             '40→45 °C charging), 25 °C ambient. Estimates, not measurements.', fontsize=12, color=INK2)
    # 1 losses
    ax = fig.add_subplot(gs[0, 0]); style(ax)
    pts = (('30 W', 30, 15, 0.5, False), ('100 W', 100, 20, 0.5, False), ('100 W\nnear empty', 100, 20, 0.10, False), ('88 W\ncharging', 88, 20, 0.5, True))
    x = np.arange(len(pts)); w = 0.36
    for k, (lab, prm, c1, c2) in enumerate((('today', BASE, '#1baf7a', '#9fdcc4'), ('P0 cuts', P0, '#6250d6', '#bdb5ef'))):
        vals = [losses(p, v, s, prm, ch) for _, p, v, s, ch in pts]
        bb = [v[0] for v in vals]; cc = [v[1] for v in vals]
        xs = x + (k - 0.5)*w
        ax.bar(xs, bb, w*0.92, color=c1, label=f'board ({lab})'); ax.bar(xs, cc, w*0.92, bottom=bb, color=c2, label=f'cells + nickel ({lab})')
        for xi, b1, c1v in zip(xs, bb, cc): ax.text(xi, b1 + c1v + 0.3, f'{b1+c1v:.1f}', ha='center', fontsize=10)
    ax.set_xticks(x); ax.set_xticklabels([p[0] for p in pts]); ax.set_ylabel('heat, W'); ax.legend(frameon=False, fontsize=9.5, loc='upper left')
    ax.set_title('1  Heat made, today vs with the P0 cuts')
    # 2 100 W power
    ax = fig.add_subplot(gs[0, 1]); style(ax)
    for b, (r30, r100, rlo, rch) in res.items():
        ax.plot(r100['t'], r100['P'], color=COL[b], lw=2, label=f"{b}: {wh(r100, 20):.0f} Wh in 20 min, empty at {r100['t'][-1]:.0f} min")
    ax.set_xlim(0, 85); ax.set_ylim(0, 108); ax.set_xlabel('minutes, 100 W asked, from full'); ax.set_ylabel('power delivered, W')
    ax.legend(frameon=False, fontsize=9.5, loc='lower left'); ax.set_title('2  100 W asked: what the derate lets out')
    # 3 100 W temps
    ax = fig.add_subplot(gs[0, 2]); style(ax)
    for b, (r30, r100, rlo, rch) in res.items():
        ax.plot(r100['t'], r100['B'], color=COL[b], lw=2, label=f'{b}: board'); ax.plot(r100['t'], hot(r100), color=COL[b], lw=2, ls=(0, (5, 3)), label=f'{b}: hottest cell')
    ax.axhspan(60, 75, color=BANDC, zorder=0); ax.axhspan(45, 55, color='#f6eef1', zorder=0)
    ax.text(84, 75.5, 'board ramp', ha='right', fontsize=10, color=INK2); ax.text(84, 55.5, 'cell ramp', ha='right', fontsize=10, color=INK2)
    ax.set_xlim(0, 85); ax.set_ylim(24, 80); ax.set_xlabel('minutes'); ax.set_ylabel('°C'); ax.legend(frameon=False, fontsize=8.5, loc='lower right')
    ax.set_title('3  100 W asked: temperatures')
    # 4 30 W
    ax = fig.add_subplot(gs[1, 0]); style(ax)
    for b, (r30, r100, rlo, rch) in res.items():
        ax.plot(r30['t']/60, r30['B'], color=COL[b], lw=2, label=f'{b}: board'); ax.plot(r30['t']/60, hot(r30), color=COL[b], lw=2, ls=(0, (5, 3)), label=f'{b}: hottest cell')
    ax.axhline(45, color='#8a8984', lw=1.2, ls=(0, (4, 3))); ax.text(2.6, 45.4, 'cell derate starts at 45 °C', ha='right', fontsize=10, color=INK2)
    ax.set_xlim(0, 2.75); ax.set_ylim(24, 50); ax.set_xlabel('hours at 30 W (15 V 2 A), full to empty'); ax.set_ylabel('°C')
    ax.legend(frameon=False, fontsize=8.5, loc='lower right'); ax.set_title('4  30 W continuous: no derate in any build')
    # 5 charging power
    ax = fig.add_subplot(gs[1, 1]); style(ax)
    for b, (r30, r100, rlo, rch) in res.items():
        ax.plot(rch['t'], rch['P'], color=COL[b], lw=2, label=f"{b}: full at {rch['t'][-1]:.0f} min")
    ax.set_xlim(0, 105); ax.set_ylim(0, 95); ax.set_xlabel('minutes charging, 88 W asked, empty to full (no CC-CV taper)'); ax.set_ylabel('charge power, W')
    ax.legend(frameon=False, fontsize=9.5, loc='lower left'); ax.set_title('5  Charging at 88 W')
    # 6 100 W from 25 %
    ax = fig.add_subplot(gs[1, 2]); style(ax)
    for b, (r30, r100, rlo, rch) in res.items():
        ax.plot(rlo['t'], rlo['P'], color=COL[b], lw=2, label=f"{b}: {full_minutes(rlo, 100):.0f} min at 100 W")
    ax.set_xlim(0, 25); ax.set_ylim(0, 108); ax.set_xlabel('minutes, 100 W asked from 25 % charge (cells start at 25 °C)'); ax.set_ylabel('power delivered, W')
    ax.legend(frameon=False, fontsize=9.5, loc='lower left'); ax.set_title('6  Late in the charge: higher resistance, less headroom')
    fig.text(0.02, 0.02, 'P0 cuts: XRS120N04D protection FETs, 9 V gate drive (LDO, on above 45 W), XGL7030-332 at 500 kHz, 0.2 x 10 Ni strips + Cu PACK tails. '
             'Both use F102 at 2.5 mΩ, inductor and gate-drive corrections, cells 21-36 mΩ by charge. The 5 V output path is not modelled.', fontsize=10.5, color=INK2)
    fig.savefig(os.path.join(HERE, 'thermal_rundown.png'), facecolor=SURF)
    print('wrote thermal_rundown.png')
