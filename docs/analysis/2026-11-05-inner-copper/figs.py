"""Figures of the inner copper study: python3 figs.py -> img/path-resistance.png, img/thermal.png
Reads paths_oz*.txt (solver printout per path) and thermal_pc.json. Needs matplotlib."""
import os, re, json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
W = ['0.5', '1', '2']
SEG = [('cub', 'PACK_P', 'PACK_P to RBAT', '#9aa3ad'), ('cub', 'BAT_SNS_P', 'BAT_SNS_P to leg B', '#c9cdd2'),
       ('cub', 'GND', 'GND return', '#2f6db5'), ('cuu', 'VBUS', 'VBUS to TPS25751', '#d8b46a'),
       ('cuu', 'PPHV', 'PPHV', '#efdcae'), ('cuu', 'AC_SNS_N', 'AC_SNS_N to leg A', '#c4481b')]
def paths(w):
    out = {}
    for line in open(os.path.join(HERE, f'paths_oz{w}.txt')):
        m = re.match(r'(cu[bu])(\d) (.+?) [A-Z]+\d+ [A-Z]+\d+ R ([\d.]+) mOhm', line)
        if m and 'total' not in line: out[(m[1], int(m[2]), m[3].split('/')[-1])] = float(m[4])
    return out
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9})
fig, axs = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
for ax, port in zip(axs, (1, 2)):
    bottom = [0.0] * 3
    for kind, net, lab, col in SEG:
        v = [paths(w)[(kind, port, net)] for w in W]
        ax.bar(range(3), v, bottom=bottom, color=col, label=lab, edgecolor='white', lw=0.6)
        bottom = [a + b for a, b in zip(bottom, v)]
    for i, (t, w) in enumerate(zip(bottom, W)):           # label: unrounded total from cu_oz<w>.json
        cu = json.load(open(os.path.join(HERE, f'cu_oz{w}.json')))
        ax.text(i, t + 0.1, f"{(cu[f'cub{port}']['R'] + cu[f'cuu{port}']['R']) * 1e3:.2f}", ha='center', fontsize=8.5, weight='bold')
    ax.set_xticks(range(3), [f'{w} oz inner' for w in W]); ax.set_title(f'Port {port}', loc='left', weight='bold')
    ax.spines[['top', 'right']].set_visible(False)
axs[0].set_ylabel('Path resistance (mΩ)')
axs[1].legend(fontsize=7.5, frameon=False, loc='upper right')
fig.suptitle('Battery-side plus USB-side copper per port, hand-routed board (8081416), outer layers 2 oz', x=0.01, ha='left', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, 'img', 'path-resistance.png'), dpi=130); plt.close(fig)

T = json.load(open(os.path.join(HERE, 'thermal_pc.json')))['per_port']
fig, axs = plt.subplots(1, 2, figsize=(9, 3.2))
for case, lab, mk in (('dis100', 'Port 1 (USB1)', 'o'), ('dis100u2', 'Port 2 (USB2)', 's')):
    axs[0].plot([0.5, 1, 2], [T[f'{case}_oz{w}']['burst_min'] for w in W], marker=mk, label=lab)
    axs[1].plot([0.5, 1, 2], [T[f'{case}_oz{w}']['part_max'] for w in W], marker=mk, label=lab)
axs[0].set_ylabel('Minutes at 100 W before the derate'); axs[1].set_ylabel('Hottest board part (°C)')
for ax in axs:
    ax.set_xticks([0.5, 1, 2], ['0.5 oz', '1 oz', '2 oz']); ax.set_xlabel('Inner copper weight')
    ax.spines[['top', 'right']].set_visible(False); ax.grid(alpha=0.3)
axs[0].legend(frameon=False, fontsize=8)
fig.suptitle('100 W burst at 25 °C, d44 policy (model values)', x=0.01, ha='left', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, 'img', 'thermal.png'), dpi=130); plt.close(fig)
print('img/path-resistance.png img/thermal.png')
