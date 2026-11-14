"""img/engineered-bumper-2026-11-05.png: the force-crush laws and the port-end results (the bar values are typed in from
out/struct.log and the thick50.py printout)"""
import os, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import bumper_struct as S
BL, OR, INK, INK2, MUT, SURF = '#2a78d6', '#eb6834', '#0b0b0b', '#52514e', '#8a8984', '#fcfcfb'
plt.rcParams.update({'font.size': 10, 'axes.edgecolor': MUT, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2})
fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 4.8), gridspec_kw=dict(width_ratios=[1, 1.25]), facecolor=SURF)
e = np.linspace(0, 0.85, 400)
curves = [('TPU 95A gyroid 30 % (today)', 'gyroid', 0.30, 40.0, BL, '--'), ('TPU 95A honeycomb 15 %', 'honeycomb', 0.15, 40.0, BL, '-'),
          ('50A honeycomb 35 %', 'honeycomb', 0.35, 3.9, OR, '-'), ('50A gyroid 60 %', 'gyroid', 0.60, 3.9, OR, '--')]
for lab, k, r, E, c, ls in curves:
    s = S.law(e, k, r, E); a.plot(e, s, color=c, ls=ls, lw=2, label=lab)
a.set_ylim(0, 1.6); a.set_xlim(0, 0.85); a.set_xlabel('crush (fraction of slab thickness)'); a.set_ylabel('crush stress (MPa, impact rate)')
a.set_title('Force-crush law of each build', loc='left', color=INK, fontsize=11); a.legend(frameon=False, fontsize=9, loc='lower right')
a.grid(axis='y', color='#e4e3df', lw=0.8); [a.spines[s].set_visible(False) for s in ('top', 'right')]
rows = [('TPU gyroid 30 % (today)', 572, 624, 9.3, BL), ('TPU honeycomb 17 %', 557, 583, 5.3, BL), ('TPU honeycomb 15 %', 397, 425, 4.6, BL),
        ('50A honeycomb 35 %', 1334, 2354, 9.5, OR), ('50A gyroid 60 %', 2014, 2598, 16.2, OR), ('50A honeycomb 35 %, 9 mm slab', 485, 1316, 14.2, OR)]
y = np.arange(len(rows))[::-1]
for yi, (lab, g1, g15, m, c) in zip(y, rows):
    b.barh(yi, g1, height=0.55, color=c, edgecolor=SURF, lw=2)
    b.plot([g15], [yi], marker='o', ms=8, mfc=SURF, mec=c, mew=2, ls='none')
    b.text(max(g1, g15) + 60, yi, f'{g1} g (1.5 m: {g15})  ·  slab {m:.1f} g', va='center', color=INK, fontsize=9)
b.set_yticks(y); b.set_yticklabels([r[0] for r in rows], color=INK); b.set_xlim(0, 4300)
b.set_xlabel('peak deceleration on the cells and board (g)'); b.grid(axis='x', color='#e4e3df', lw=0.8); b.set_axisbelow(True)
b.set_title('Port-end drop: bar = 1 m, ring = 1.5 m (6 mm slab unless noted)', loc='left', color=INK, fontsize=11)
[b.spines[s].set_visible(False) for s in ('top', 'right', 'left')]; b.tick_params(axis='y', length=0)
for ax in (a, b): ax.set_facecolor(SURF)
fig.tight_layout(); fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'engineered-bumper-2026-11-05.png'), dpi=150, facecolor=SURF)
