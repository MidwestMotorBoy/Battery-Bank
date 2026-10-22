"""Sheet for thermal_derate.py: the linear derate bands, 30 W continuous, 100 W asked for, and 88 W charging,
for the current tray, the hybrid and the cup. Run: python thermal_derate_visuals.py [OUT_DIR] -> thermal_derate.png"""
import os, sys, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import thermal_derate as TD
OUT = sys.argv[1] if len(sys.argv) > 1 else HERE

SURF, INK, INK2, MUTE, GRID, BANDC = '#fcfcfb', '#0b0b0b', '#52514e', '#8a8984', '#e6e5e1', '#f1f0ec'
COL = {'Current: 1 mm Al cover': '#2a78d6', 'Hybrid: 3 mm CNC lid': '#eb6834', 'Cup: coupled + PA12 webs': '#1baf7a'}   # same entities, same slots as thermal_visuals
plt.rcParams.update({'font.family': 'Segoe UI', 'font.size': 11, 'text.color': INK, 'axes.labelcolor': INK2,
                     'axes.edgecolor': GRID, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.titlesize': 13,
                     'axes.titleweight': 'bold', 'axes.titlelocation': 'left', 'figure.facecolor': SURF, 'axes.facecolor': SURF})
def style(ax):
    ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
def band(ax, lo, hi, text):
    ax.axhspan(lo, hi, color=BANDC, zorder=0); ax.text(ax.get_xlim()[1]*0.99, hi + 0.4, text, ha='right', va='bottom', fontsize=10, color=INK2)

R30 = {n: TD.run(n, 30.0) for n in TD.DESIGNS}
R100 = {n: TD.run(n, 100.0) for n in TD.DESIGNS}
RCH = {n: TD.run(n, 88.0, mode='chg') for n in TD.DESIGNS}
hot = lambda r: np.maximum(r['F'], r['K'])

fig = plt.figure(figsize=(18, 11.5), dpi=150)
gs = fig.add_gridspec(2, 3, hspace=0.45, wspace=0.26, left=0.05, right=0.97, top=0.87, bottom=0.08)
fig.text(0.02, 0.955, 'Linear thermal derate (FEB 21700G cells): 30 W continuous, 100 W asked for, and 88 W charging', fontsize=20, weight='bold')
fig.text(0.02, 0.925, 'Firmware lowers the power limit in a straight line from full to zero across a temperature band, on whichever sensor is worst. '
         'Lumped estimates at 25 °C ambient (thermal_derate.py); trust the ranking more than the absolute numbers.', fontsize=12, color=INK2)

# 1. the derate bands
ax = fig.add_subplot(gs[0, 0]); style(ax)
T = np.linspace(30, 85, 400)
for key, lab, c in (('cell_chg', 'Hottest cell, charging (40 → 45 °C)', '#6250d6'), ('cell_dis', 'Hottest cell, discharging (45 → 55 °C)', '#e87ba4'),
                    ('board', 'Board copper (60 → 75 °C)', '#eda100')):
    ax.plot(T, [100*TD.ramp(t, TD.BANDS[key]) for t in T], color=c, lw=2, label=lab)
ax.axvline(81, color=MUTE, lw=1.2, ls=(0, (4, 3))); ax.text(80.5, 50, 'TS hardware\nstop 81 °C', ha='right', fontsize=10, color=INK2)
ax.set_xlim(30, 85); ax.set_ylim(-3, 108); ax.set_xlabel('sensor temperature, °C'); ax.set_ylabel('allowed power, % of asked')
ax.legend(frameon=False, fontsize=10, loc='lower left'); ax.set_title('1  The three derate ramps (the lowest one wins)')

# 2. 30 W continuous
ax = fig.add_subplot(gs[0, 1]); style(ax)
for n, r in R30.items():
    ax.plot(r['t']/60, r['B'], color=COL[n], lw=2, label=f'{n}: board')
    ax.plot(r['t']/60, hot(r), color=COL[n], lw=2, ls=(0, (5, 3)), label=f'{n}: hottest cell')
ax.set_xlim(0, 3.1); ax.set_ylim(24, 66)
ax.axhspan(60, 66, color=BANDC, zorder=0); ax.text(3.05, 61, 'board derate starts at 60 °C', ha='right', fontsize=10, color=INK2)
ax.text(3.05, 45.4, 'cell derate starts at 45 °C', ha='right', fontsize=10, color=INK2)
ax.axhline(45, color=MUTE, lw=1.2, ls=(0, (4, 3)))
ax.set_xlabel('hours at 30 W (the pack runs empty at 2.6 h)'); ax.set_ylabel('°C')
ax.legend(frameon=False, fontsize=9.5, loc='upper left', ncol=1)
ax.set_title('2  30 W continuous: nothing derates, in any design')

# 3. 100 W asked for: delivered power
ax = fig.add_subplot(gs[0, 2]); style(ax)
for n, r in R100.items():
    ax.plot(r['t'], r['P'], color=COL[n], lw=2, label=f"{n} (empty at {r['t'][-1]:.0f} min)")
ax.set_xlim(0, 120); ax.set_ylim(0, 108); ax.set_xlabel('minutes, 100 W asked for'); ax.set_ylabel('power delivered, W')
ax.legend(frameon=False, fontsize=10, loc='lower left')
txt = '\n'.join(f"{n.split(':')[0]}: {TD.out_wh(r, 20):.1f} Wh in the first 20 min, {np.mean(r['P']):.0f} W average" for n, r in R100.items())
ax.text(79, 104, txt, ha='right', va='top', fontsize=10, color=INK2)
ax.set_title('3  100 W asked for: what the derate lets out')

# 4. 100 W asked for: temperatures
ax = fig.add_subplot(gs[1, 0]); style(ax)
for n, r in R100.items():
    ax.plot(r['t'], r['B'], color=COL[n], lw=2, label=f'{n}: board')
    ax.plot(r['t'], hot(r), color=COL[n], lw=2, ls=(0, (5, 3)), label=f'{n}: hottest cell')
ax.set_xlim(0, 120); ax.set_ylim(24, 80)
ax.axhspan(60, 75, color=BANDC, zorder=0); ax.axhspan(45, 55, color='#f6eef1', zorder=0)
ax.text(79, 75.5, 'board ramp 60–75 °C', ha='right', fontsize=10, color=INK2); ax.text(79, 55.5, 'cell ramp 45–55 °C', ha='right', fontsize=10, color=INK2)
ax.set_xlabel('minutes, 100 W asked for'); ax.set_ylabel('°C'); ax.legend(frameon=False, fontsize=9, loc='lower right', ncol=1)
ax.set_title('4  100 W asked for: what limits each design')

# 5. charging: power
ax = fig.add_subplot(gs[1, 1]); style(ax)
for n, r in RCH.items():
    ax.plot(r['t'], r['P'], color=COL[n], lw=2, label=f"{n} (full at {r['t'][-1]:.0f} min)")
ax.set_xlim(0, 150); ax.set_ylim(0, 95); ax.set_xlabel('minutes charging, 88 W asked for (empty to full, no CC-CV taper)'); ax.set_ylabel('charge power, W')
ax.legend(frameon=False, fontsize=10, loc='lower left'); ax.set_title('5  Charging: the cup derates first and finishes last')

# 6. charging: cells
ax = fig.add_subplot(gs[1, 2]); style(ax)
for n, r in RCH.items():
    ax.plot(r['t'], hot(r), color=COL[n], lw=2, label=f'{n}: hottest cell')
    ax.plot(r['t'], r['B'], color=COL[n], lw=1.6, ls=(0, (5, 3)), label=f'{n}: board')
ax.set_xlim(0, 150); ax.set_ylim(24, 66); ax.axhspan(40, 45, color='#efedf9', zorder=0)
ax.text(149, 45.4, 'charge ramp 40–45 °C', ha='right', fontsize=10, color=INK2)
ax.set_xlabel('minutes charging'); ax.set_ylabel('°C'); ax.legend(frameon=False, fontsize=9, loc='lower right', ncol=1)
ax.set_title('6  Charging: the cells pin at the ramp')

fig.text(0.02, 0.012, 'Losses: board 0.024·P + 3.1e-4·P² (≈1 W at 30 W, 5.5 W at 100 W), cells 4.8e-4·P² (4.8 W at 100 W); charging 2.6 W + 2.7 W at 88 W. '
         '\nAll three designs use the same four-node model (board, Al, front cells, back cells), so the figures differ slightly from thermal_visuals.png.',
         fontsize=10.5, color=INK2)
fig.savefig(os.path.join(OUT, 'thermal_derate.png'), facecolor=SURF)
print('wrote thermal_derate.png')
