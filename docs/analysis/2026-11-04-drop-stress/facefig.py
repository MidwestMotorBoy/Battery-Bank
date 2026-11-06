"""Figure for the flat-face drops (the poses where the no-rotation impact model is exact): per part, the FE stress away
from the contact patches (99.9th percentile) over the PA12 limit. Run after run_all.py on the face poses."""
import os, json, numpy as np
import figs as Fg, poses
import matplotlib.pyplot as plt
OUT = Fg.OUT
FACES = ['bottom', 'top', 'board', 'back', 'side']
COLS = [('cup walls', 'shell', 'cup_walls'), ('cradles', 'shell', 'cradles'), ('edge lands', 'shell', 'lands'),
        ('F.Cu lips', 'shell', 'lips'), ('cap plate', 'shell', 'cap'), ('cap OT posts', 'shell', 'ot_posts'),
        ('cap board feet', 'shell', 'feet'), ('carrier frames', 'carrier', 'carrier/frames'), ('carrier webs', 'carrier', 'carrier/webs'),
        ('rail tongues*', 'rails', 'ends'), ('rail posts', 'rails', 'posts'), ('rail blocks', 'rails', 'blocks')]

def val(pose, src, key):
    if src == 'rails':
        v = 0.0
        for r in ('rails_tp', 'rails_tn', 'rails_bp', 'rails_bn'):
            R = Fg.L(os.path.join(OUT, f'{r}_{pose}.json'))
            if not R: continue
            g = R['regions'].get(f'{r}/{key}')
            if g: v = max(v, g['p999'] if key == 'ends' else g.get('p999_far', g['p999']))
        return v
    R = Fg.L(os.path.join(OUT, f'{src}_{pose}.json'))
    g = R['regions'].get(key) if R else None
    return (g.get('p999_far', g['p999'])) if g else np.nan

if __name__ == '__main__':
    A = np.array([[val(p, s, k) for _, s, k in COLS] for p in FACES])
    json.dump(dict(poses=FACES, parts=[c[0] for c in COLS], MPa=np.round(A, 1).tolist()), open(os.path.join(OUT, 'faces_stress.json'), 'w'), indent=1)
    U = A / 48.0
    fig, ax = plt.subplots(figsize=(9.5, 3.4))
    im = ax.imshow(np.minimum(U, 4), cmap=Fg.SEQ, vmin=0, vmax=4, aspect='auto')
    for i in range(U.shape[0]):
        for j in range(U.shape[1]):
            if np.isfinite(A[i, j]): ax.text(j, i, f'{A[i, j]:.0f}', ha='center', va='center', fontsize=7.5, color='white' if U[i, j] > 2 else Fg.INK)
    ax.set_xticks(range(len(COLS)), [c[0] for c in COLS], rotation=40, ha='right', fontsize=8)
    ax.set_yticks(range(len(FACES)), [poses.TITLES[p] for p in FACES], fontsize=8)
    ax.spines[:].set_visible(False); ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, shrink=0.85, extend='max'); cb.set_label('stress / 48 MPa'); cb.outline.set_visible(False)
    ax.set_title('Flat drops from 1 m: PA12 stress away from the contacts, MPa (99.9th pct; * tongues: at the contact)')
    Fg.save(fig, 'fig_faces.png')
