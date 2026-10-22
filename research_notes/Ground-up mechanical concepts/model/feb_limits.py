"""FEB 21700G charge cap and temperature derating, as linear ramps that stay inside the cell's spec table, simulated in the
cup + P0 build (thermal_rundown.py). Estimates, not measurements. Run: python feb_limits.py -> table + feb_limits.png

FEB spec (diy500amp listing): charge 0.65 A at 0-5 C, 3.25 A at 5-15 C, 4.55 A at 15-45 C, none outside 0-45 C;
discharge 6.5 A at -20-0 C, 13 A at 0-35 C, 6.5 A at 35-45 C, 3.25 A at 45-60 C, none above 60 C.
The table is read as CELL temperature (the conservative reading); every ramp below sits on or under it."""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import thermal_rundown as TR, thermal_derate as TD

# ---------------- the limit curves (per series string = pack current) ----------------
# charge: (cell C, A). Ramps only ever reduce current inside a spec band, so no point exceeds the table.
CHG_T = [0.0, 1.0, 4.9, 5.0, 6.5, 15.0, 16.5, 40.0, 45.0]
CHG_I = [0.0, 0.65, 0.65, 0.65, 3.25, 3.25, 4.55, 4.55, 0.0]
# discharge: (cell C, A)
DIS_T = [-20.0, -19.0, 0.0, 1.5, 33.0, 35.0, 43.0, 45.0, 55.0, 60.0]
DIS_I = [0.0, 6.5, 6.5, 13.0, 13.0, 6.5, 6.5, 3.25, 3.25, 0.0]
BOARD = (60.0, 75.0)                    # board copper ramp, unchanged
def i_chg(t): return float(np.interp(t, CHG_T, CHG_I))
def i_dis(t): return float(np.interp(t, DIS_T, DIS_I))
# hardware ceilings: R_ICHG 9.1 k -> 11.5 k gives 48-52 A·kΩ / 11.5 kΩ = 4.17-4.52 A (bq25756 §5.5), under 4.55 A
ICHG_PIN_MAX = 52.0 / 11.5

FEB_R = lambda s: float(np.interp(s, [0.0, 0.10, 0.25, 1.0], [0.050, 0.043, 0.0315, 0.030]))
def sim(demand, mode='dis', v_usb=20.0, amb=25.0, soc0=None, hours=6.0, cap_wh=93.6, by='cell'):
    """by='cell': the FEB table read against the hottest cell (conservative); by='ambient': against ambient, with the generic
    cell ramp (45 -> 55 C, full -> zero) on top."""
    TR.r_cell = FEB_R; prm = TR.P0; d = TD.DESIGNS['Cup: coupled + PA12 webs']
    B = F = K = amb; soc = (1.0 if mode == 'dis' else 0.0) if soc0 is None else soc0
    rec = []
    for i in range(int(hours*3600)):
        v_pack = 4*TR.ocv(soc); hot = max(F, K)
        f_board = TD.ramp(B, BOARD)
        if mode == 'dis':
            if by == 'cell':
                p_cell = i_dis(hot) * v_pack * 0.90              # battery-current limit as output power (~90 % at heavy load)
            else:
                p_cell = min(i_dis(amb) * v_pack * 0.90, demand * TD.ramp(hot, (45.0, 55.0)))
            p = min(demand, demand*f_board, p_cell)
        else:
            i_lim = min(i_chg(hot), ICHG_PIN_MAX)
            p = min(demand, demand*f_board, i_lim * v_pack / 0.93)   # input power that puts i_lim into the pack
        pb, pc, ib = TR.losses(max(p, 0.01), v_usb, soc, prm, mode == 'chg')
        qbf = d['gbf']*(B - F); qfk = d['gfk']*(F - K)
        B += (pb - qbf - d['gba']*(B - amb)) / TD.CB
        F += (pc/2 + qbf - qfk - TD.G_SKIN*(F - amb)) / TD.CPAIR
        K += (pc/2 + qfk - TD.G_SKIN*(K - amb)) / TD.CPAIR
        soc += (-1 if mode == 'dis' else 1) * ib*v_pack/3600/cap_wh
        rec.append((i/60, p, B, F, K, soc, ib))
        if (mode == 'dis' and (soc <= 0.0 or v_pack < 4*3.0)) or (mode == 'chg' and soc >= 1.0) or (mode == 'chg' and p <= 0.01 and i > 600): break
    a = np.array(rec)
    return dict(t=a[:, 0], P=a[:, 1], B=a[:, 2], F=a[:, 3], K=a[:, 4], soc=a[:, 5], I=a[:, 6])

if __name__ == '__main__':
    print(f'ICHG pin ceiling with 11.5 kohm: {48/11.5:.2f}-{ICHG_PIN_MAX:.2f} A')
    print('Discharge, 100 W asked:')
    for amb, by in ((25.0, 'cell'), (35.0, 'cell'), (25.0, 'ambient'), (35.0, 'ambient')):
        r = sim(100, amb=amb, by=by)
        full = np.nonzero(r['P'] < 99)[0]; full = (full[0] if len(full) else len(r['P']))/60
        print(f"   ambient {amb:.0f} C, table by {by}: {full:.1f} min at 100 W, {r['P'][r['t'] < 20].sum()/3600:.1f} Wh in 20 min, {r['P'].sum()/3600:.1f} Wh total, "
              f"empty at {r['t'][-1]:.0f} min, peak cell {max(r['F'].max(), r['K'].max()):.0f} C, peak battery current {r['I'].max():.1f} A")
    for amb in (25.0, 35.0):
        r = sim(30, v_usb=15, amb=amb)
        print(f"   30 W at {amb:.0f} C: {r['t'][-1]/60:.2f} h, min power {r['P'].min():.1f} W, peak cell {max(r['F'].max(), r['K'].max()):.0f} C")
    print('Charging, 88 W offered:')
    for amb in (25.0, 10.0, 3.0):
        r = sim(88, mode='chg', amb=amb, hours=12)
        print(f"   ambient {amb:.0f} C: full at {r['t'][-1]:.0f} min ({r['t'][-1]/60:.1f} h), mean {np.mean(r['P']):.0f} W in, peak cell {max(r['F'].max(), r['K'].max()):.0f} C, "
              f"peak battery current {r['I'].max():.2f} A")
    if len(sys.argv) > 1 and sys.argv[1] == 'nochart': sys.exit()

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e6e5e1'
    plt.rcParams.update({'font.family': 'Segoe UI', 'font.size': 11, 'text.color': INK, 'axes.labelcolor': INK2, 'axes.edgecolor': GRID,
                         'xtick.color': INK2, 'ytick.color': INK2, 'axes.titlesize': 13, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
                         'figure.facecolor': SURF, 'axes.facecolor': SURF})
    def style(ax):
        ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
        for s in ('top', 'right'): ax.spines[s].set_visible(False)
    def spec_steps(ax, edges, vals, color):
        for (a, b), v in zip(zip(edges[:-1], edges[1:]), vals):
            ax.fill_between([a, b], 0, v, color=color, alpha=0.18, step=None, lw=0)
    fig = plt.figure(figsize=(18, 10.5), dpi=150)
    gs = fig.add_gridspec(2, 3, hspace=0.42, wspace=0.25, left=0.05, right=0.98, top=0.86, bottom=0.08)
    fig.text(0.02, 0.95, 'FEB 21700G: charge cap and temperature derating', fontsize=20, weight='bold')
    fig.text(0.02, 0.92, 'Shaded: the cell\'s spec table, read as cell temperature. Lines: the linear ramps firmware follows, which never exceed it. '
             'Simulated in the cup + P0 build; estimates, not measurements.', fontsize=12, color=INK2)
    ax = fig.add_subplot(gs[0, 0]); style(ax)
    spec_steps(ax, [0, 5, 15, 45], [0.65, 3.25, 4.55], '#6250d6')
    T = np.linspace(-5, 50, 600); ax.plot(T, [i_chg(t) for t in T], color='#6250d6', lw=2, label='firmware charge limit')
    ax.axhline(ICHG_PIN_MAX, color='#8a8984', lw=1.2, ls=(0, (4, 3))); ax.text(49, ICHG_PIN_MAX + 0.12, f'hardware ceiling, R_ICHG 11.5 kΩ: ≤ {ICHG_PIN_MAX:.2f} A', fontsize=10, color=INK2, ha='right')
    ax.set_xlim(-5, 50); ax.set_ylim(0, 5.5); ax.set_xlabel('hottest cell, °C'); ax.set_ylabel('charge current, A'); ax.legend(frameon=False, loc='lower center')
    ax.set_title('1  Charge current vs cell temperature')
    ax = fig.add_subplot(gs[0, 1]); style(ax)
    spec_steps(ax, [-20, 0, 35, 45, 60], [6.5, 13, 6.5, 3.25], '#eb6834')
    T = np.linspace(-25, 65, 900); ax.plot(T, [i_dis(t) for t in T], color='#eb6834', lw=2, label='firmware discharge limit')
    ax.axhline(10, color='#8a8984', lw=1.2, ls=(0, (4, 3))); ax.text(-24, 10.2, 'hardware ceiling: IBAT_REV 10 A', fontsize=10, color=INK2)
    ax2 = ax.twinx(); ax2.set_ylim(0, 14*14.4*0.9); ax2.set_ylabel('≈ output power at 14.4 V, W', color=INK2); ax2.spines['top'].set_visible(False)
    ax.set_xlim(-25, 65); ax.set_ylim(0, 14); ax.set_xlabel('hottest cell, °C'); ax.set_ylabel('battery current, A'); ax.legend(frameon=False, loc='upper left')
    ax.set_title('2  Discharge current vs cell temperature')
    ax = fig.add_subplot(gs[0, 2]); style(ax)
    for amb, c, by, ls in ((25.0, '#2a78d6', 'cell', '-'), (35.0, '#e34948', 'cell', '-'), (25.0, '#2a78d6', 'ambient', (0, (5, 3))), (35.0, '#e34948', 'ambient', (0, (5, 3)))):
        r = sim(100, amb=amb, by=by); ax.plot(r['t'], r['P'], color=c, lw=2, ls=ls, label=f'{amb:.0f} °C, table by {by}: {r["P"][r["t"] < 20].sum()/3600:.0f} Wh in 20 min')
    ax.set_xlim(0, 90); ax.set_ylim(0, 108); ax.set_xlabel('minutes, 100 W asked, from full'); ax.set_ylabel('power delivered, W'); ax.legend(frameon=False, loc='upper right', fontsize=9.5)
    ax.set_title('3  100 W asked: what the limits let out')
    ax = fig.add_subplot(gs[1, 0]); style(ax)
    for amb, c in ((25.0, '#2a78d6'), (35.0, '#e34948')):
        r = sim(100, amb=amb); ax.plot(r['t'], np.maximum(r['F'], r['K']), color=c, lw=2, label=f'{amb:.0f} °C: hottest cell')
        ax.plot(r['t'], r['B'], color=c, lw=1.6, ls=(0, (5, 3)), label=f'{amb:.0f} °C: board')
    ax.axhspan(35, 45, color='#fbe7dd', zorder=0); ax.text(89, 45.4, 'FEB 6.5 A band', ha='right', fontsize=10, color=INK2)
    ax.set_xlim(0, 90); ax.set_ylim(20, 75); ax.set_xlabel('minutes, 100 W asked'); ax.set_ylabel('°C'); ax.legend(frameon=False, fontsize=9.5, loc='lower right')
    ax.set_title('4  100 W asked: temperatures')
    ax = fig.add_subplot(gs[1, 1]); style(ax)
    for amb, c in ((25.0, '#2a78d6'), (10.0, '#1baf7a'), (3.0, '#6250d6')):
        r = sim(88, mode='chg', amb=amb, hours=12); ax.plot(r['t']/60, r['I'], color=c, lw=2, label=f'{amb:.0f} °C ambient: full at {r["t"][-1]/60:.1f} h')
    ax.set_xlim(0, 2.5); ax.set_ylim(0, 5); ax.set_xlabel('hours charging (no CC-CV taper)'); ax.set_ylabel('charge current, A'); ax.legend(frameon=False, loc='lower right')
    ax.set_title('5  Charging: warm, cool and near-freezing')
    ax = fig.add_subplot(gs[1, 2]); ax.axis('off'); ax.set_title('6  Where each limit lives', pad=10)
    rows = ['Hardware ceilings (no firmware needed)',
            '• R_ICHG 9.1 k → 11.5 k: charge ≤ 4.17–4.52 A even unconfigured',
            '• IBAT_REV = 10 A in the TPS25751 bundle (already planned)',
            '• Gauge: OTC 45 °C, UTC 0 °C (opens CHG); OTD 60 °C (opens DSG);',
            '   OCD1 ≈ 12 A; cell-temp sensors on the FRONT (board-heated) cells',
            'Gauge charge algorithm (BQ40Z50 temperature ranges)',
            '• T1 0 / T2 5 / T3 15 / T4 40 / T5 45 °C,',
            '   currents 650 / 3250 / 4550 / ramp to 0 mA',
            'Firmware, every second',
            '• Charge: ICHG_REG = min(gauge request, ramp 1, pin)',
            '• Discharge: re-advertise Source Caps with power = min(ramp 2 × V,',
            '   board ramp), in ~5 W steps with hysteresis; split across ports',
            '• Keep the low-pack-voltage PDO limit']
    for k, s in enumerate(rows):
        ax.text(0.0, 0.97 - k*0.074, s, transform=ax.transAxes, fontsize=11, va='top', weight='bold' if not s.startswith(('•', '   ')) else 'normal')
    fig.savefig(os.path.join(HERE, 'feb_limits.png'), facecolor=SURF)
    print('wrote feb_limits.png')
