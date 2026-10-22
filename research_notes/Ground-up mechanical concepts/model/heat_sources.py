"""Where the heat comes from: part-by-part loss estimates at 30 W, 60 W, 100 W out and 88 W charging.
Estimates from datasheet resistances at a warm-but-not-hot temperature; switching from a simple edge model. Not measured.
Run: python heat_sources.py  -> prints the tables; writes heat_sources.png next to this file."""
import os, sys

V_PACK = 14.4                  # nominal 4S
F_SW = 600e3                   # BQ25756 switching frequency (598 kHz, schematic review 4)
# resistances (ohm), warm. Sources: datasheets/ and docs/devboard reviews
R = dict(
    cell=0.030,                # each of 4: FEB 21700G (68E), <= 25 mOhm spec; ~30 mOhm DC mid-charge is an estimate
                               # (the cell adopted 2026-10-21; the EVE 58E it replaced was ~22 mOhm DC)
    nickel=0.005,              # strips + tongues, whole path (estimate)
    fuse=0.005,                # F101 hot (review 2, A-findings)
    shunt=0.001,               # RS101 gauge shunt (pa2512-1mohm)
    prot=2 * 0.0057,           # Q101 + Q102 AGM404AP1: 4.4 mOhm typ at 10 V, x1.3 warm
    pack_cu=0.002,             # board copper, pack input to the chargers (estimate)
    rbat=0.005, rac=0.005,     # charger sense resistors (pa2010-5mohm)
    fet=0.013,                 # SiZ240DT channel at 4.5 V gate: 12.25 / 13.3 mOhm max, warm typical ~13
    ind=0.012,                 # APS0730M2R2F DCR (~11-14 mOhm max in aps0730.pdf; the table is misaligned)
    pphv=0.018,                # TPS25751 internal PPHV switch, fig 6-5: 14-26 mOhm over -20..150 C
    conn=0.010,                # USB-C: 4 VBUS + 4 GND contacts, 40 mOhm max each mated -> 20 mOhm loop max; ~10 typical
)
T_EDGE, T_DEAD, V_BODY, C_OSS = 10e-9, 45e-9, 0.8, 600e-12     # rise+fall total, dead time per edge, body diode, switch node C
P_CORE, P_GATE_IC, P_HOUSE = 0.20, 0.10, 0.05                  # inductor core (at full ripple), gate drive + BQ IC, MCU/BLE/3V3/PD controller logic

GROUPS = ['Cells (internal resistance)', 'Pack path: nickel, fuse, shunt, protection FETs', 'Charger FETs (conduction)',
          'Charger FETs (switching + dead time)', 'Inductor (DCR + core)', 'Charger sense resistors',
          'USB side: PD-controller switch + connector', 'Gate drive, ICs, MCU/BLE']
WHERE = ['spread through the 4 cans', 'cells to board, pack input corner', 'charger zone', 'charger zone', 'charger zone',
         'charger zone', 'port end of the board', 'spread over the board']

def losses(p_out, v_usb, charging=False, v_pack=V_PACK):
    """returns dict group -> W, plus currents. Discharge: battery -> USB. Charging: USB in at p_out -> battery."""
    i_usb = p_out / v_usb
    i_bat = p_out / v_pack
    for _ in range(4):                                         # iterate: losses raise the battery current (discharge) / lower it (charge)
        g = dict.fromkeys(GROUPS, 0.0)
        g[GROUPS[0]] = 4 * R['cell'] * i_bat**2
        g[GROUPS[1]] = (R['nickel'] + R['fuse'] + R['shunt'] + R['prot'] + R['pack_cu']) * i_bat**2
        boost = (v_usb > v_pack) if not charging else False    # discharge to a higher USB voltage = boost
        if charging or not boost:
            # buck: the source-side leg switches; inductor carries the low-voltage-side current
            v_hi, v_lo = (v_usb, v_pack) if charging else (v_pack, v_usb)
            i_l = i_bat if charging else i_usb
            d = v_lo / v_hi
            cond = R['fet'] * i_l**2 * (1 + d + (1 - d))      # through-FET on the other leg (100 %) + HS (d) + LS sync (1-d)
            v_sw = v_hi
        else:
            # boost (discharge 14.4 -> 20 V): battery-side HS on, USB-side LS switches, USB-side HS is the sync rectifier
            i_l = i_bat; d = 1 - v_pack / v_usb
            cond = R['fet'] * i_l**2 * (1 + d + (1 - d))
            v_sw = v_usb
        g[GROUPS[2]] = cond
        g[GROUPS[3]] = 0.5 * v_sw * i_l * T_EDGE * F_SW + 0.5 * C_OSS * v_sw**2 * F_SW + 2 * T_DEAD * F_SW * V_BODY * i_l
        g[GROUPS[4]] = R['ind'] * i_l**2 + P_CORE * min(1.0, v_sw / 20.0)
        g[GROUPS[5]] = R['rbat'] * i_bat**2 + R['rac'] * i_usb**2
        g[GROUPS[6]] = (R['pphv'] + R['conn']) * i_usb**2
        g[GROUPS[7]] = P_GATE_IC + P_HOUSE
        tot = sum(g.values())
        i_bat = ((p_out + tot) if not charging else (p_out - tot)) / v_pack
    return g, i_bat, i_usb

SCEN = [('30 W out (9 V 3.3 A, phone)', 30.0, 9.0, False, V_PACK), ('60 W out (20 V 3 A, laptop)', 60.0, 20.0, False, V_PACK),
        ('100 W out (20 V 5 A)', 100.0, 20.0, False, V_PACK), ('100 W out, near-empty pack (12 V)', 100.0, 20.0, False, 12.0),
        ('88 W charging (20 V in)', 88.0, 20.0, True, V_PACK)]
MODEL_BOARD = {'30 W': 1.0, '60 W': 2.5, '100 W': 5.5, '88 W': 2.6}   # what the thermal models assumed for the board

if __name__ == '__main__':
    res = []
    for name, p, v, ch, vp in SCEN:
        g, ib, iu = losses(p, v, ch, vp); res.append((name, g, ib, iu))
        tot = sum(g.values()); board = tot - g[GROUPS[0]] - 0.4 * g[GROUPS[1]]     # nickel share (~40 % of the pack path) stays off-board
        print(f'{name}: battery {ib:.1f} A, USB {iu:.1f} A, total {tot:.1f} W, on the board ~{board:.1f} W, efficiency {p/(p+tot) if not ch else (p-tot)/p:.1%}')
        for k, w in zip(GROUPS, WHERE): print(f'   {k:50s} {g[k]:5.2f} W   ({w})')
    if len(sys.argv) > 1 and sys.argv[1] == 'nochart': sys.exit()

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e6e5e1'
    COLS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']   # slots 1-8, fixed order
    plt.rcParams.update({'font.family': 'Segoe UI', 'font.size': 11, 'text.color': INK, 'axes.labelcolor': INK2, 'axes.edgecolor': GRID,
                         'xtick.color': INK2, 'ytick.color': INK2, 'axes.titlesize': 13, 'axes.titleweight': 'bold',
                         'axes.titlelocation': 'left', 'figure.facecolor': SURF, 'axes.facecolor': SURF})
    fig = plt.figure(figsize=(18, 10.5), dpi=150)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.15], width_ratios=[1.25, 1], hspace=0.62, wspace=0.10, left=0.17, right=0.98, top=0.86, bottom=0.05)
    fig.text(0.02, 0.95, 'Where the heat comes from', fontsize=20, weight='bold')
    fig.text(0.02, 0.92, 'Part-by-part estimates from datasheet resistances (warm) and a simple switching model, nominal 14.4 V pack. '
             'Not measured: the dev-board 100 W run should replace these.', fontsize=12, color=INK2)
    ax = fig.add_subplot(gs[0, :])
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.grid(True, axis='x', color=GRID); ax.set_axisbelow(True)
    names = [r[0] for r in res]
    for i, (name, g, ib, iu) in enumerate(res):
        left = 0.0
        for j, k in enumerate(GROUPS):
            w = g[k]
            ax.barh(i, w, left=left, color=COLS[j], height=0.6, edgecolor=SURF, linewidth=2, label=k if i == 0 else None)
            if w >= 0.55: ax.text(left + w/2, i, f'{w:.1f}', ha='center', va='center', fontsize=10, color='white' if j in (0, 2, 5, 6, 7) else INK)
            left += w
        ax.text(left + 0.15, i, f'{left:.1f} W total', va='center', fontsize=11, weight='bold')
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names); ax.invert_yaxis(); ax.set_xlim(0, 19); ax.set_xlabel('heat, W')
    ax.legend(loc='upper center', bbox_to_anchor=(0.45, -0.2), frameon=False, fontsize=10, ncol=4)
    ax.set_title('1  Heat by source at five operating points')
    # 100 W detail table
    ax = fig.add_subplot(gs[1, 0]); ax.axis('off'); ax.set_title('2  100 W out, part by part', pad=10)
    g, ib, iu = res[2][1], res[2][2], res[2][3]
    rows = [('Cells: 4 × ~30 mΩ (FEB 21700G)', f'{ib:.1f} A', 4*R['cell']*ib**2, 'inside the cans'),
            ('Protection FETs Q101/Q102: 2 × ~5.7 mΩ', f'{ib:.1f} A', R['prot']*ib**2, 'pack input'),
            ('Nickel strips + tongues: ~5 mΩ', f'{ib:.1f} A', R['nickel']*ib**2, 'cell ends'),
            ('Fuse F101 ~5 mΩ, shunt 1 mΩ, copper ~2 mΩ', f'{ib:.1f} A', (R['fuse'] + R['shunt'] + R['pack_cu'])*ib**2, 'pack input'),
            ('Charger FETs, conduction: SiZ240DT ~13 mΩ', f'{ib:.1f} A', g[GROUPS[2]], 'charger'),
            ('Charger FETs, switching + dead time (600 kHz)', '', g[GROUPS[3]], 'charger'),
            ('Inductor APS0730: ~12 mΩ DCR + core', f'{ib:.1f} A', g[GROUPS[4]], 'charger'),
            ('Sense resistors RBAT + RAC: 5 mΩ each', f'{ib:.1f} / {iu:.1f} A', g[GROUPS[5]], 'charger'),
            ('TPS25751 PPHV switch: ~18 mΩ', f'{iu:.1f} A', R['pphv']*iu**2, 'port end'),
            ('USB-C contacts: ~10 mΩ loop', f'{iu:.1f} A', R['conn']*iu**2, 'port end'),
            ('Gate drive, ICs, MCU/BLE', '', g[GROUPS[7]], 'spread')]
    y = 0.95
    for hdr, x in (('Part', 0.0), ('Current', 0.55), ('Heat', 0.70), ('Where', 0.80)): ax.text(x, y, hdr, transform=ax.transAxes, weight='bold', fontsize=11)
    for k, (a, b, c, d) in enumerate(rows):
        y = 0.87 - k*0.075
        if k % 2: ax.add_patch(plt.Rectangle((-0.01, y - 0.035), 1.0, 0.07, transform=ax.transAxes, color='#f4f4f1', zorder=0))
        ax.text(0.0, y, a, transform=ax.transAxes, va='center', fontsize=11); ax.text(0.55, y, b, transform=ax.transAxes, va='center', fontsize=11)
        ax.text(0.76, y, f'{c:.2f} W', transform=ax.transAxes, va='center', ha='right', fontsize=11); ax.text(0.80, y, d, transform=ax.transAxes, va='center', fontsize=11, color=INK2)
    # notes
    ax = fig.add_subplot(gs[1, 1]); ax.axis('off'); ax.set_title('3  What it means', pad=10)
    tot100 = sum(g.values()); board100 = tot100 - g[GROUPS[0]] - 0.4*g[GROUPS[1]]
    gc = res[4][1]; totc = sum(gc.values()); boardc = totc - gc[GROUPS[0]] - 0.4*gc[GROUPS[1]]
    gl = res[3][1]; totl = sum(gl.values()); boardl = totl - gl[GROUPS[0]] - 0.4*gl[GROUPS[1]]
    notes = [f'• At 100 W the cells make {g[GROUPS[0]]:.1f} of the {tot100:.1f} W: the biggest single source, heating',
             '   the cans from the inside. No heatsink helps with that; only lower-resistance cells do.',
             f'• Near empty (12 V pack) the same 100 W costs {totl:.1f} W: the battery current rises ~26 %,',
             '   and heat goes with I². The board makes ~{:.1f} W then, against the 5.5 W the'.format(boardl),
             '   thermal models used, so late-discharge bursts run hotter.',
             f'• Charging puts ~{boardc:.1f} W on the board, not the 2.6 W the thermal models assumed,',
             '   so the cup charges a little slower than the derate sheet shows.',
             '• The charger zone (FETs, inductor, sense resistors) is about two-thirds of the board heat.',
             f'   The rest is the protection FETs at the pack input and ~{g[GROUPS[6]]:.1f} W at the port end',
             '   (PD-controller switch + USB-C contacts), right against the closed top wall.',
             f'• At 30 W the whole pack makes ~{sum(res[0][1].values()):.1f} W; a third is fixed (gate drive, ICs, inductor core).',
             '• Levers: lower-resistance cells, a lower charger frequency (switching scales with f),',
             '   lower-RDS(on) FETs, and fewer milliohms in the pack path (fuse, protection FETs).']
    for k, s in enumerate(notes): ax.text(-0.02, 0.97 - k*0.068, s, transform=ax.transAxes, fontsize=11, va='top')
    fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'heat_sources.png'), facecolor=SURF)
    print('wrote heat_sources.png')
