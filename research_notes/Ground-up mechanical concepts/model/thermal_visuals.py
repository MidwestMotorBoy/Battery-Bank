"""Thermal sheet for the mechanical study: heat soak, 100 W burst traces, the cup's front/back cell spread, charging.
Uses thermal_burst.py (current, hybrid, no-Al) and thermal_cell_spread.py (the cup's front and back cell pairs).
Lumped estimates, 25 C ambient. Run: python thermal_visuals.py [OUT_DIR] -> thermal_visuals.png"""
import os, sys, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import thermal_burst as TB, thermal_cell_spread as SP
OUT = sys.argv[1] if len(sys.argv) > 1 else HERE

SURF, INK, INK2, MUTE, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#8a8984', '#e6e5e1'
S1, S2, S3, S4, S5, S7 = '#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#6250d6'   # categorical slots 1-5 and 7, one per entity
plt.rcParams.update({'font.family': 'Segoe UI', 'font.size': 11, 'text.color': INK, 'axes.labelcolor': INK2,
                     'axes.edgecolor': GRID, 'xtick.color': INK2, 'ytick.color': INK2, 'axes.titlesize': 13,
                     'axes.titleweight': 'bold', 'axes.titlelocation': 'left', 'figure.facecolor': SURF, 'axes.facecolor': SURF})
def style(ax):
    ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
def limit(ax, y, text, x):
    ax.axhline(y, color=MUTE, lw=1.2, ls=(0, (4, 3))); ax.text(x, y + 0.6, text, color=INK2, fontsize=10, va='bottom')
def label_end(ax, t, y, s, dy=0):
    ax.annotate(s, (t[-1], y[-1]), xytext=(6, dy), textcoords='offset points', va='center', fontsize=10, color=INK)

fig = plt.figure(figsize=(18, 11), dpi=150)
gs = fig.add_gridspec(2, 3, hspace=0.42, wspace=0.28, left=0.12, right=0.94, top=0.87, bottom=0.09)
fig.text(0.02, 0.955, 'Where the heat goes: aluminium cover vs CNC lid vs coupling the board to the cells', fontsize=20, weight='bold')
fig.text(0.02, 0.925, 'Lumped estimates at 25 °C ambient with hand-set conductances (thermal_burst.py, thermal_cell_spread.py). '
         'The dev-board 100 W run should replace them; trust the ranking more than the absolute numbers.', fontsize=12, color=INK2)

# 1. heat soak
ax = fig.add_subplot(gs[0, 0]); style(ax)
names = ['1.0 mm Al cover (current)', 'Board + parts', '3 mm CNC lid (hybrid)', 'Four cells']
vals = [9.5*0.90, TB.CB, 35.8*0.90, TB.CK]
ax.barh(names, vals, color=S1, height=0.55)
for i, v in enumerate(vals): ax.text(v + 4, i, f'{v:.0f} J/K', va='center', fontsize=11)
ax.set_xlim(0, 320); ax.invert_yaxis(); ax.set_xlabel('heat it can soak per kelvin (J/K)')
ax.set_title('1  The cells are the big heat sink')

# 2. board temperature, 10 min at 100 W then 30 W
ax = fig.add_subplot(gs[0, 1:]); style(ax)
steps = [(100, 600), (30, 3000)]
series = [('Current: 1 mm Al cover', TB.sim('current: 1.0 mm cover, gap pad, air gap to cells', steps)[:, 1], S1),
          ('Hybrid: 3 mm CNC lid', TB.sim('hybrid: 3 mm CNC lid', steps)[:, 1], S2),
          ('No aluminium, board in air', TB.sim('no Al, board in air (no coupling)', steps)[:, 1], S4),
          ('Cup: board coupled to the cells + PA12 webs', SP.sim(0.11, steps)[:, 0], S3)]
t = np.arange(1, len(series[0][1]) + 1) / 60
for (n, y, c), dy in zip(series, (2, 7, 0, -7)):
    ax.plot(t, y, color=c, lw=2, label=n)
ax.axvspan(0, 10, color='#f1f0ec', zorder=0); ax.text(0.3, 103, '100 W', color=INK2, fontsize=10)
ax.text(10.3, 103, '30 W', color=INK2, fontsize=10)
limit(ax, 65, 'board limit used (65 °C, room for the FETs below the 81 °C TS stop)', 22); limit(ax, 81, 'TS stop 81 °C', 40)
ax.set_xlim(0, 60); ax.set_ylim(20, 110); ax.set_xlabel('minutes'); ax.set_ylabel('board copper, °C')
ax.legend(loc='upper right', frameon=False, fontsize=10)
ax.set_title('2  Board temperature: 10 minutes at 100 W, then 30 W')

# 3. minutes of 100 W
ax = fig.add_subplot(gs[1, 0]); style(ax)
def t100_tb(d): return len(TB.sim(d, [(100, 4*3600)], stop=lambda B, K: B >= TB.BOARD_LIM or K >= TB.CELL_LIM)) / 60
bars = [('No Al, board in air', t100_tb('no Al, board in air (no coupling)')), ('Current: 1 mm cover', t100_tb('current: 1.0 mm cover, gap pad, air gap to cells')),
        ('Hybrid: CNC lid', t100_tb('hybrid: 3 mm CNC lid')), ('Cup, no webs', SP.summary(0.032)['t100']),
        ('Cup + PA12 webs', SP.summary(0.11)['t100']), ('Cup + filler bead', SP.summary(2.0)['t100'])]
ax.barh([b[0] for b in bars], [b[1] for b in bars], color=[S4, S1, S2, S5, S3, S7], height=0.55)
for i, (_, v) in enumerate(bars): ax.text(v + 0.3, i, f'{v:.1f} min', va='center', fontsize=11)
ax.set_xlim(0, 20); ax.invert_yaxis(); ax.set_xlabel('minutes at 100 W from 25 °C until a limit')
ax.set_title('3  How long a 100 W burst lasts')

# 4. cup front vs back cells
ax = fig.add_subplot(gs[1, 1]); style(ax)
steps = [(100, 600), (30, 3000)]; t = np.arange(1, 3601) / 60
for (n, g, c) in (('air in the gaps', 0.032, S5), ('PA12 webs', 0.11, S3), ('gap-filler bead', 2.0, S7)):
    r = SP.sim(g, steps)
    ax.plot(t, r[:, 1], color=c, lw=2, label=f'{n}: front pair')
    ax.plot(t, r[:, 2], color=c, lw=2, ls=(0, (5, 3)), label=f'{n}: back pair')
ax.axvspan(0, 10, color='#f1f0ec', zorder=0)
ax.set_xlim(0, 60); ax.set_ylim(24, 52); ax.set_xlabel('minutes (10 min at 100 W, then 30 W)'); ax.set_ylabel('cell pair, °C')
ax.legend(frameon=False, fontsize=9.5, loc='upper right', ncol=1)
ax.set_title('4  Cup: front cells (board-heated) vs back cells')

# 5. charging
ax = fig.add_subplot(gs[1, 2]); style(ax)
steps = [('charge88', 3600)]; t = np.arange(1, 3601) / 60
cur = TB.sim('current: 1.0 mm cover, gap pad, air gap to cells', steps)[:, 3]
hyb = TB.sim('hybrid: 3 mm CNC lid', steps)[:, 3]
cw = SP.sim(0.11, steps); cb = SP.sim(2.0, steps)
for n, y, c, ls in (('Current', cur, S1, '-'), ('Hybrid', hyb, S2, '-'), ('Cup + webs, front pair', cw[:, 1], S3, '-'),
                    ('Cup + webs, back pair', cw[:, 2], S3, (0, (5, 3))), ('Cup + filler bead', cb[:, 1], S7, '-')):
    ax.plot(t, y, color=c, lw=2, ls=ls, label=n); label_end(ax, t, y, f'{y[-1]:.0f}')
limit(ax, 45, 'charge limit 45 °C: firmware slows the charge here', 1)
ax.set_xlim(0, 60); ax.set_ylim(24, 62); ax.set_xlabel('minutes charging at 88 W'); ax.set_ylabel('cells, °C')
ax.legend(frameon=False, fontsize=9.5, loc='upper left', bbox_to_anchor=(0, 0.93))
ax.set_title('5  Charging at 88 W for an hour')

fig.text(0.02, 0.03, 'Losses at 100 W: ~5.5 W in the power stage (FETs 3.6-4.1 W + inductor 1.0-1.8 W, schematic review 4) and ~4.8 W of cell I²R (4 x 7.4 A² x ~22 mΩ). '
         'Current and hybrid treat the four cells as one node; the cup splits them into front and back pairs.', fontsize=10.5, color=INK2)
fig.savefig(os.path.join(OUT, 'thermal_visuals.png'), facecolor=SURF)
print('wrote thermal_visuals.png')
