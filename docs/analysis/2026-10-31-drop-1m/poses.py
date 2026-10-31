"""Renders of the pack in each drop pose, floor at the bottom (uses the cup renderer and the label art)."""
import os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
import geom
sys.path.insert(0, geom.MECH)
_cwd = os.getcwd(); os.chdir(geom.MECH)
import monolith_side_renders as RR, monolith_cup as K
os.chdir(_cwd)
SHOW = ('cup', 'cap', 'label', 'bumpb_band', 'bumpb_slab', 'bumpt_band', 'bumpt_slab', 'screw')

def pose(A, d, size=(700, 700), px=4.6, view=(0.55, -1.0, 0.30), floor_gap=6, mark=None):
    """image of the outer parts with the floor under them; d = drop direction (pack frame)"""
    d = np.asarray(d, float); d /= np.linalg.norm(d); up = -d
    w = np.asarray(view, float); w = w - (w @ d) * d; w /= np.linalg.norm(w)
    r = np.cross(up, w); R = np.array([r, up, w])
    parts = [(k, V) for k, V, _ in A if k in SHOW]
    P = np.vstack([V.reshape(-1, 3) for _, V in parts])
    s0 = (P @ d).max(); c = P.mean(0)
    W, H = size; S = RR.SS
    img = Image.new('RGB', (W * S, H * S), (252, 252, 250))
    ox = W / 2 - px * (c @ r)
    oy = (H - 70) - px * s0            # screen y = oy - px * (V @ up); the contact point (V @ up = -s0) lands on the floor line
    keys = [k for k, _ in parts]
    tex = K.label_tex(keys)
    RR.zrender(img, [(V, dict(K.C, bumpt_band=K.C['bump'], bumpb_band=K.C['bump'], bumpt_slab=K.C['bslab'],
                               bumpb_slab=K.C['bslab']).get(k, (200, 200, 200))) for k, V in parts], R, (ox * S, oy * S), px * S, tex=tex)
    g = ImageDraw.Draw(img); yf = (H - 70) * S
    g.rectangle([0, yf, W * S, yf + 14 * S], fill=(205, 203, 196))
    for x in range(-40, W + 40, 14): g.line([(x * S, (yf + 14 * S)), ((x + 14) * S, yf)], fill=(170, 168, 160), width=S)
    g.line([(0, yf), (W * S, yf)], fill=(90, 90, 90), width=2 * S)
    if mark is not None:            # arrow for the fall
        x0 = (ox + px * (np.asarray(mark) @ r)) * S
        g.line([(x0, 30 * S), (x0, 110 * S)], fill=(31, 78, 121), width=3 * S)
        g.polygon([(x0 - 9 * S, 100 * S), (x0 + 9 * S, 100 * S), (x0, 122 * S)], fill=(31, 78, 121))
    return img.resize((W, H), Image.LANCZOS)

if __name__ == '__main__':
    A, m, p = geom.load()
    im = pose(A, (1, 0, 0)); im.save('cache/pose_test.png')
