"""Monolith wrap label: one printed vinyl rectangle round the whole cup, top and bottom edges under the TPU bumpers.
Spec: the "Cup label plan" doc (2026-10-27). The layout comes from the cup model (hardware/mechanical/monolith_cup.py):
the cup's outside is a prism, so the label is a flat rectangle, cup perimeter + LAP long, seam in the middle of the
back face, art running unbroken across the seam (the overlap repeats the first LAP mm).
Run: python monolith_label.py      (numpy, fonttools, manifold3d; Chromium via playwright for the PNG / PDF)
-> out/monolith_label_print.svg    artwork with 1.5 mm bleed, all text as outlines (send this, or the PDF)
   out/monolith_label_print.pdf    the same, page = art + bleed
   out/monolith_label_cut.svg      die line: outline (R2 corners) + vent hole, on the same page as the print file
   out/monolith_label_proof.png    art + die line + face folds, for checking
Label coordinates: mm, x along the wrap left to right as seen from outside with the ports up, y down from the label's
top edge. The fonts are OFL (fonts/)."""
import os, sys, math, numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
sys.path.insert(0, os.path.join(HERE, '..', 'mechanical'))

# ---------------- layout from the cup model ----------------
import monolith_cup as K
LAP, BLEED = 5.0, 1.5                # seam overlap, print bleed
TUCK = K.LABEL_TUCK                  # edge under each bumper; label heights and the vent hole come from monolith_cup
VENT_HOLE_D = 2 * K.VENT_HOLE_R

def wrap_layout():
    P = np.array(K.cs_out.to_polygons()[0], float)
    seg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    per = s[-1]
    back = [i for i in range(len(P)) if seg[i] > 2 and abs(P[i, 0] - P[(i + 1) % len(P), 0]) < 1e-6 and P[i, 0] < 0]
    i = back[0]; seam = s[i] + seg[i] / 2                          # middle of the back flat
    flats = []                                                    # (x0, x1) of each flat in label x
    for j in range(len(P)):
        if seg[j] > 2: flats.append((((s[j] - seam) % per), ((s[j] - seam) % per) + seg[j]))
    flats.sort()
    z_bot, z_top = K.LABEL_Z                                      # label edges on the cup
    # vent: board-face centre (y = VENT_Y) at VENT_Z
    jb = [j for j in range(len(P)) if seg[j] > 2 and abs(P[j, 0] - P[(j + 1) % len(P), 0]) < 1e-6 and P[j, 0] > 0][0]
    vx = (s[jb] + (K.VENT_Y - P[jb, 1]) - seam) % per
    return dict(per=per, seam=seam, flats=flats, z_bot=z_bot, z_top=z_top, H=z_top - z_bot, W=per + LAP,
                vent=(vx, z_top - K.VENT_Z), poly=P, s=s[:-1])

L = wrap_layout()
PER, W, H = L['per'], L['W'], L['H']
VX, VY = L['vent']
FLATS = [f for f in L['flats'] if f[1] - f[0] > 30]               # side A, board face, side B (the back flat is split)
SIDE_A, BOARD, SIDE_B = FLATS
VIS0, VIS1 = TUCK, H - TUCK                                       # visible band between the bumpers (label y)

# ---------------- palette ----------------
INK = '#17120f'
C = dict(sky0='#5fa3c0', sky1='#93c9cf', sky2='#f2d39a', cloud='#fbf3df', cloud_sh='#d9d2c4',
         far='#7f93a6', far_sh='#647789', snow='#f8f6ef', snow_sh='#c9d3dc', rock='#a4a6a3', rock_sh='#6c6e6d',
         mesa='#dd7b3d', mesa_sh='#a2432a', mesa_top='#eda461', sand='#e2b06e', sand_sh='#c88c4f',
         hill='#7fa24c', hill_sh='#5b7f37', pine='#3e7343', pine_sh='#26502f', trunk='#5c3a22',
         bear='#80502a', bear_sh='#5a3519', sun='#f7c844', sun_ray='#f09a3a', cream='#f4ead0', banner='#efe2bf',
         word='#f6d061', word_sh='#b5372a', red='#b8322a', check='#3f8f4a')

# ---------------- svg helpers ----------------
out = []
def add(s): out.append(s)
def pts(p): return ' '.join(f'{x:.3f},{y:.3f}' for x, y in p)
def poly(p, fill, sw=0.35, stroke=INK, extra=''):
    add(f'<polygon points="{pts(p)}" fill="{fill}" stroke="{stroke if sw else "none"}" stroke-width="{sw}" stroke-linejoin="round"{extra}/>')
def path(d, fill='none', sw=0.35, stroke=INK, extra=''):
    add(f'<path d="{d}" fill="{fill}" stroke="{stroke if sw else "none"}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"{extra}/>')
_clip = [0]
def hatch(p, step=0.9, ang=45, sw=0.18):
    """ink hatching clipped to polygon p (the comic shadow)"""
    _clip[0] += 1; cid = f'h{_clip[0]}'
    add(f'<clipPath id="{cid}"><polygon points="{pts(p)}"/></clipPath>')
    xs, ys = [q[0] for q in p], [q[1] for q in p]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    span = (x1 - x0) + (y1 - y0); t = math.tan(math.radians(ang))
    d = ''.join(f'M{x0 + k:.2f} {y1:.2f}L{x0 + k + (y1 - y0) / t:.2f} {y0:.2f}' for k in np.arange(-span, span, step))
    add(f'<g clip-path="url(#{cid})"><path d="{d}" stroke="{INK}" stroke-width="{sw}" fill="none"/></g>')
def rep(fn, x, *a, **k):
    """draw an element at x and, near the ends, one wrap period away, so the seam overlap and the bleed match"""
    for dx in (-PER, 0, PER):
        if -BLEED - 25 < x + dx < W + BLEED + 25: fn(x + dx, *a, **k)
def wave(x, base, terms):
    return base + sum(a * math.sin(2 * math.pi * k * x / PER + ph) for a, k, ph in terms)   # periodic in PER

# ---------------- outlined text ----------------
class Font:
    def __init__(self, name):
        self.f = TTFont(os.path.join(HERE, 'fonts', name)); self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap(); self.hm = self.f['hmtx']; self.cap = self.f['OS/2'].sCapHeight
    def g(self, ch): return self.cmap.get(ord(ch), '.notdef')
    def width(self, s, cap, track=0.0): return sum(self.hm[self.g(c)][0] for c in s) * cap / self.cap + track * (len(s) - 1)
    def d(self, s, cap, x, y, track=0.0):
        k, cx, d = cap / self.cap, x, ''
        for ch in s:
            pen = SVGPathPen(self.gs); self.gs[self.g(ch)].draw(TransformPen(pen, (k, 0, 0, -k, cx, y)))
            d += pen.getCommands(); cx += self.hm[self.g(ch)][0] * k + track
        return d
BANG, XB, BOLD, SEMI = Font('Bangers-Regular.ttf'), Font('BarlowCondensed-ExtraBold.ttf'), Font('BarlowCondensed-Bold.ttf'), Font('BarlowCondensed-SemiBold.ttf')
DC = '⎓'
def text(s, font, cap, x, y, anchor='l', fill=INK, track=0.0, stroke=None, sw=0.0, fit=None):
    """text as outlines; '⎓' is drawn as the DC symbol; fit = max width (shrinks cap to fit)"""
    parts = s.split(DC); dcw = cap * 1.05
    wid = lambda c: sum(font.width(p, c, track) for p in parts) + (len(parts) - 1) * (c * 1.05 + 2 * c * 0.18)
    if fit and wid(cap) > fit: cap = cap * fit / wid(cap); dcw = cap * 1.05
    w = wid(cap); x = x - w / 2 if anchor == 'c' else x - w if anchor == 'r' else x
    d = ''
    for i, p in enumerate(parts):
        d += font.d(p, cap, x, y, track); x += font.width(p, cap, track)
        if i < len(parts) - 1:
            x += cap * 0.18; t = cap * 0.11
            d += f'M{x:.3f} {y - cap * 0.66:.3f}h{dcw:.3f}v{t:.3f}h{-dcw:.3f}z'
            for j in range(3):
                dx = x + j * dcw * 0.38
                d += f'M{dx:.3f} {y - cap * 0.30:.3f}h{dcw * 0.26:.3f}v{t:.3f}h{-dcw * 0.26:.3f}z'
            x += dcw + cap * 0.18
    st = f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" paint-order="stroke"' if stroke else ''
    add(f'<path d="{d}" fill="{fill}"{st}/>')
    return w

# ---------------- scene pieces ----------------
def cloud(x, y, s):
    lobes = [(-3.2, 0.6, 2.0), (-1.2, -0.6, 2.6), (1.4, -0.2, 2.3), (3.4, 0.7, 1.7)]
    for dx, dy, r in lobes:
        add(f'<circle cx="{x + dx * s:.2f}" cy="{y + dy * s:.2f}" r="{r * s:.2f}" fill="{C["cloud"]}" stroke="{INK}" stroke-width="0.35"/>')
    add(f'<rect x="{x - 3.6 * s:.2f}" y="{y + 0.4 * s:.2f}" width="{7.4 * s:.2f}" height="{1.9 * s:.2f}" fill="{C["cloud"]}"/>')
    path(f'M{x - 5.2 * s:.2f} {y + 2.3 * s:.2f}H{x + 5.1 * s:.2f}', sw=0.35)
    path(f'M{x - 2.5 * s:.2f} {y + 1.6 * s:.2f}H{x + 2.8 * s:.2f}', stroke=C['cloud_sh'], sw=0.5)

def pine(x, yb, h, w, dark=False):
    """comic pine: trunk + four tiers, shadow on the right half"""
    g, sh = (C['pine_sh'], '#1c3d24') if dark else (C['pine'], C['pine_sh'])
    poly([(x - w * 0.06, yb), (x - w * 0.06, yb - h * 0.16), (x + w * 0.06, yb - h * 0.16), (x + w * 0.06, yb)], C['trunk'], 0.25)
    n = 4
    for i in range(n):
        ytop = yb - h + i * h * 0.2; ybot = ytop + h * 0.36 + (0.1 * h if i == n - 1 else 0)
        hw = w / 2 * (0.42 + 0.58 * i / (n - 1))
        tier = [(x, ytop), (x + hw, ybot), (x + hw * 0.45, ybot - h * 0.04), (x, ybot + h * 0.01),
                (x - hw * 0.5, ybot - h * 0.04), (x - hw, ybot)]
        poly(tier, g, 0)
        poly([(x, ytop), (x + hw, ybot), (x + hw * 0.45, ybot - h * 0.04), (x + hw * 0.1, ybot)], sh, 0)
        poly(tier, 'none', 0.3)

def scrub(x, yb, s):
    for dx, r in ((-1.0, 1.1), (0.2, 1.5), (1.4, 1.0)):
        add(f'<circle cx="{x + dx * s:.2f}" cy="{yb - r * s * 0.8:.2f}" r="{r * s:.2f}" fill="#8a9a52" stroke="{INK}" stroke-width="0.28"/>')

def bear(x, yb, s=1.0, flip=False):
    """walking grizzly, 14 mm long at s = 1, feet on yb"""
    body = [(0.8, 0), (0.6, -2.4), (0.1, -4.2), (0.6, -5.9), (2.0, -6.9), (4.6, -7.3), (7.0, -8.1), (9.2, -7.5), (10.4, -6.7),
            (11.0, -7.0), (11.2, -7.7), (11.9, -7.2), (12.7, -6.7), (13.6, -5.8), (14.1, -5.1), (13.7, -4.6), (12.5, -4.4),
            (11.5, -4.6), (11.6, -3.0), (11.8, 0), (10.4, 0), (10.2, -2.2), (9.8, -2.4), (10.0, 0), (8.6, 0), (8.4, -2.6),
            (5.0, -2.8), (5.0, 0), (3.4, 0), (3.3, -2.6), (2.6, -2.7), (2.6, 0)]
    belly = [(0.6, -2.4), (0.1, -4.2), (0.8, -3.4), (3.0, -3.3), (8.6, -3.3), (11.5, -4.6), (11.6, -3.0), (11.8, 0), (10.4, 0),
             (10.2, -2.2), (9.8, -2.4), (10.0, 0), (8.6, 0), (8.4, -2.6), (5.0, -2.8), (5.0, 0), (3.4, 0), (3.3, -2.6),
             (2.6, -2.7), (2.6, 0), (0.8, 0)]
    T = (lambda p: (x + (14.1 - p[0] if flip else p[0]) * s, yb + p[1] * s))
    poly([T(p) for p in body], C['bear'], 0)
    poly([T(p) for p in belly], C['bear_sh'], 0)
    hatch([T(p) for p in belly], step=0.6, ang=60, sw=0.12)
    poly([T(p) for p in body], 'none', 0.38)
    path('M' + ' L'.join(f'{a:.2f} {b:.2f}' for a, b in map(T, [(5.6, -7.0), (7.0, -7.5), (8.6, -7.1)])), sw=0.2)   # hump fur
    ex, ey = T((12.6, -5.9)); add(f'<circle cx="{ex:.2f}" cy="{ey:.2f}" r="{0.28 * s:.2f}" fill="{INK}"/>')
    nx, ny = T((13.95, -5.05)); add(f'<circle cx="{nx:.2f}" cy="{ny:.2f}" r="{0.3 * s:.2f}" fill="{INK}"/>')
    for fx in (11.0, 9.3, 4.2, 1.7):
        cx, cy = T((fx, 0))
        path(f'M{cx - 0.4 * s:.2f} {cy:.2f}l{0.25 * s:.2f} {-0.35 * s:.2f}M{cx:.2f} {cy:.2f}l{0.25 * s:.2f} {-0.35 * s:.2f}M{cx + 0.4 * s:.2f} {cy:.2f}l{0.25 * s:.2f} {-0.35 * s:.2f}',
             stroke=C['cream'], sw=0.14)

def plane_icon(cx, cy, r, ring=True):
    """carry-on mark: airliner and a check, in a circle"""
    add(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="{C["cream"]}" stroke="{INK}" stroke-width="{max(0.3, r * 0.08):.3f}"/>')
    if ring: add(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r * 0.84:.3f}" fill="none" stroke="{INK}" stroke-width="{r * 0.03:.3f}"/>')
    pl = [(0, -1), (0.12, -0.78), (0.12, -0.2), (0.95, 0.25), (0.95, 0.42), (0.12, 0.17), (0.12, 0.6), (0.4, 0.8), (0.4, 0.95),
          (0, 0.86), (-0.4, 0.95), (-0.4, 0.8), (-0.12, 0.6), (-0.12, 0.17), (-0.95, 0.42), (-0.95, 0.25), (-0.12, -0.2), (-0.12, -0.78)]
    a, k, ox, oy = math.radians(45), r * 0.58, cx - r * 0.12, cy - r * 0.08
    poly([(ox + k * (u * math.cos(a) - v * math.sin(a)), oy + k * (u * math.sin(a) + v * math.cos(a))) for u, v in pl], INK, 0)
    bx, by, br = cx + r * 0.52, cy + r * 0.52, r * 0.36
    add(f'<circle cx="{bx:.3f}" cy="{by:.3f}" r="{br:.3f}" fill="{C["check"]}" stroke="{INK}" stroke-width="{max(0.25, r * 0.06):.3f}"/>')
    path(f'M{bx - br * 0.48:.3f} {by + br * 0.02:.3f}L{bx - br * 0.12:.3f} {by + br * 0.4:.3f}L{bx + br * 0.52:.3f} {by - br * 0.38:.3f}',
         stroke=C['cream'], sw=br * 0.26)

def caption(x0, y0, x1, y1, shadow=0.8):
    """comic caption box: cream, slightly skewed corners, hard drop shadow"""
    p = [(x0, y0 + 0.3), (x1 - 0.2, y0), (x1, y1 - 0.3), (x0 + 0.25, y1)]
    poly([(a + shadow, b + shadow) for a, b in p], INK, 0)
    poly(p, C['cream'], 0.5)

# ---------------- the scene ----------------
def scene():
    X0, X1, Y0, Y1 = -BLEED, W + BLEED, -BLEED, H + BLEED
    # sky in three flat bands
    add(f'<rect x="{X0}" y="{Y0}" width="{X1 - X0}" height="{Y1 - Y0}" fill="{C["sky2"]}"/>')
    add(f'<rect x="{X0}" y="{Y0}" width="{X1 - X0}" height="{24 - Y0}" fill="{C["sky1"]}"/>')
    add(f'<rect x="{X0}" y="{Y0}" width="{X1 - X0}" height="{13 - Y0}" fill="{C["sky0"]}"/>')
    for yb in (13, 24): path(f'M{X0} {yb}H{X1}', stroke='#ffffff', sw=0.25, extra=' stroke-dasharray="6 3 1.5 3" opacity="0.55"')
    # clouds over the forest
    for cx, cy, s in ((8, 9, 1.0), (176, 7.5, 0.8), (22, 15.5, 0.6)): rep(cloud, cx, cy, s)
    # far range, periodic, with snow on the high points
    terms = [(4.0, 3, 1.0), (2.5, 7, 2.0), (1.3, 13, 0.4), (0.7, 29, 1.3)]
    xs = np.arange(X0 - 1, X1 + 1.01, 0.5)
    ridge = [(x, wave(x, 33.5, terms)) for x in xs]
    poly(ridge + [(X1 + 1, Y1 + 1), (X0 - 1, Y1 + 1)], C['far'], 0.35)
    ys = [y for _, y in ridge]
    for n in range(2, len(ridge) - 2):
        x, y = ridge[n]
        if y < 31.5 and y <= min(ys[n - 2:n + 3]):
            cap = [(x - 2.6, y + 2.2), (x - 1.3, y + 1.0), (x, y), (x + 1.4, y + 1.1), (x + 2.8, y + 2.4), (x + 1.6, y + 2.0),
                   (x + 0.9, y + 2.9), (x + 0.1, y + 2.0), (x - 0.9, y + 2.9), (x - 1.6, y + 2.0)]
            poly(cap, C['snow'], 0.3)
    hatch([(x, y + 3.5) for x, y in ridge] + [(X1 + 1, Y1 + 1), (X0 - 1, Y1 + 1)], step=1.3, ang=35, sw=0.12)
    # sun in the board-face notch: the vent hole is its core
    for i in range(16):
        a0 = 2 * math.pi * i / 16; a1 = a0 + 2 * math.pi / 32
        r0, r1 = VENT_HOLE_D / 2 + 2.6, VENT_HOLE_D / 2 + (9.5 if i % 2 == 0 else 6.5)
        poly([(VX + r0 * math.cos(a0), VY + r0 * math.sin(a0)), (VX + r1 * math.cos((a0 + a1) / 2), VY + r1 * math.sin((a0 + a1) / 2)),
              (VX + r0 * math.cos(a1), VY + r0 * math.sin(a1))], C['sun_ray'], 0.3)
    add(f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2 + 2.6:.3f}" fill="{C["sun"]}" stroke="{INK}" stroke-width="0.45"/>')
    add(f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2 + 1.2:.3f}" fill="none" stroke="{INK}" stroke-width="0.2" stroke-dasharray="0.8 0.8"/>')
    # the two granite peaks either side of the board-face notch, snow-capped
    xa, xb = BOARD
    lpk, rpk = (xa - 6.0, 21.0), (xb + 5.0, 18.5)
    left = [(SIDE_A[0] - 6, 52), (SIDE_A[0] + 8, 41), (SIDE_A[1] - 14, 33), (lpk[0] - 4.5, 25.5), lpk, (lpk[0] + 3.0, 25.0),
            (xa + 4.0, 34.0), (xa + 8.5, 44.0), (VX - 10.5, 52.0), (VX - 9.0, H + 2), (SIDE_A[0] - 6, H + 2)]
    right = [(VX + 9.0, H + 2), (VX + 10.5, 51.5), (xb - 8.0, 41.0), (xb - 3.5, 30.0), (rpk[0] - 2.5, 22.0), rpk, (rpk[0] + 4.0, 24.0),
             (SIDE_B[0] + 9.0, 31.0), (SIDE_B[0] + 18.0, 38.0), (SIDE_B[1] + 2, 47), (SIDE_B[1] + 2, H + 2)]
    for pk, pg, shade in ((lpk, left, [lpk, (lpk[0] + 3.0, 25.0), (xa + 4.0, 34.0), (xa + 8.5, 44.0), (VX - 10.5, 52.0), (VX - 9.0, H + 2), (lpk[0] + 2.0, H + 2), (lpk[0] + 1.5, 44), (lpk[0] - 0.5, 31)]),
                          (rpk, right, [rpk, (rpk[0] + 4.0, 24.0), (SIDE_B[0] + 9.0, 31.0), (SIDE_B[0] + 18.0, 38.0), (SIDE_B[1] + 2, 47), (SIDE_B[1] + 2, H + 2), (rpk[0] + 1, H + 2), (rpk[0] - 0.5, 33)])):
        poly(pg, C['rock'], 0)
        poly(shade, C['rock_sh'], 0); hatch(shade, step=0.8, ang=50, sw=0.15)
        poly(pg, 'none', 0.45)
        sx, sy = pk
        snow = [(sx, sy), (sx + 3.4, sy + 3.8), (sx + 2.2, sy + 3.5), (sx + 1.6, sy + 5.2), (sx + 0.4, sy + 3.9), (sx - 0.8, sy + 5.6),
                (sx - 1.9, sy + 3.8), (sx - 3.0, sy + 4.6), (sx - 4.0, sy + 4.0)]
        poly(snow, C['snow'], 0.35)
        poly([(sx, sy), (sx + 3.4, sy + 3.8), (sx + 2.2, sy + 3.5), (sx + 1.6, sy + 5.2), (sx + 0.4, sy + 3.9)], C['snow_sh'], 0.25)
        for k in range(3): path(f'M{sx - 1.5 + k * 1.6:.2f} {sy + 8 + k * 2.5:.2f}l{1.2:.2f} {3.5:.2f}', sw=0.25)   # rock cracks
    # canyon mesas on side B, in front of the right peak
    b0, b1 = SIDE_B
    for (m0, m1, top, base) in ((b0 - 6, b0 + 17, 38.0, 62.0), (b1 - 15, b1 + 8, 40.5, 63.0), (b0 + 8, b0 + 31, 33.0, 64.0)):
        mesa = [(m0 - 2.5, base), (m0 + 1.0, base - 6), (m0 + 2.6, top + 7), (m0 + 3.0, top + 2.5), (m0 + 3.6, top + 1.2), (m0 + 4.2, top),
                (m0 + 9, top - 0.6), (m1 - 3.5, top), (m1 - 2.6, top + 1.5), (m1 - 2.0, top + 6), (m1 - 1.2, top + 8.5), (m1 + 1.5, base - 5), (m1 + 4.0, base)]
        poly(mesa, C['mesa'], 0)
        poly([(m1 - 6.5, top), (m1 - 3.5, top), (m1 - 2.6, top + 1.5), (m1 - 2.0, top + 6), (m1 - 1.2, top + 8.5), (m1 + 1.5, base - 5), (m1 + 4.0, base), (m1 - 5, base), (m1 - 6.8, top + 8)], C['mesa_sh'], 0)
        hatch([(m1 - 6.5, top), (m1 - 3.5, top), (m1 - 2.6, top + 1.5), (m1 - 2.0, top + 6), (m1 - 1.2, top + 8.5), (m1 + 1.5, base - 5), (m1 + 4.0, base), (m1 - 5, base), (m1 - 6.8, top + 8)], step=0.75, ang=70, sw=0.15)
        poly([(m0 + 4.2, top), (m0 + 9, top - 0.6), (m1 - 3.5, top), (m1 - 3.8, top + 1.1), (m0 + 4.0, top + 1.1)], C['mesa_top'], 0)
        poly([(m0 - 2.5, base), (m0 + 1.0, base - 6), (m0 + 4, base - 3.5), (m0 + 6, base)], '#c96a35', 0.3)
        for k, yy in enumerate(np.arange(top + 4, base - 2, 3.2)):
            path(f'M{m0 + 2.6 + k * 0.35:.2f} {yy:.2f}h{(m1 - m0) * (0.45 + 0.1 * (k % 2)):.2f}', sw=0.2)
        poly(mesa, 'none', 0.45)
    # desert floor under the mesas
    floor = [(b0 - 6, 60), (b0 + 6, 58.5), (b1 - 6, 59.5), (b1 + 4, 61), (b1 + 4, H + 2), (b0 - 6, H + 2)]
    poly(floor, C['sand'], 0.35)
    for x in np.arange(b0 - 2, b1 + 2, 4.7): scrub(x, 63.5 + 1.2 * math.sin(x), 0.55)
    # rolling green hills, periodic, dipping into the notch
    hterms = [(1.6, 5, 0.3), (1.0, 11, 1.7)]
    hills = []
    for x in xs:
        y = wave(x, 54.0, hterms)
        d = min(abs(x - VX), abs(x - VX + PER), abs(x - VX - PER))
        if d < 22: y += (22 - d) / 22 * 13          # valley under the sun
        if b0 - 4 < x < b1 + 4: y = max(y, 63.5)    # stays below the desert floor
        hills.append((x, y))
    hill_poly = hills + [(X1 + 1, Y1 + 1), (X0 - 1, Y1 + 1)]
    poly(hill_poly, C['hill'], 0.4)
    hatch([(x, y + 4) for x, y in hills] + [(X1 + 1, Y1 + 1), (X0 - 1, Y1 + 1)], step=1.1, ang=25, sw=0.14)
    # pine forest: tall at the back and seam, a treeline under side A, sparse on the board face, none in the desert
    rng = np.random.default_rng(7)
    trees = []
    for x in np.arange(0, PER, 2.4):
        if b0 - 3 < x < b1 + 1: continue
        d = abs(x - VX)
        if d < 7: continue
        back = x < SIDE_A[0] - 1 or x > b1 + 1
        h = (rng.uniform(17, 26) if back else rng.uniform(9, 14)) * (0.7 if d < 16 else 1.0)
        yb = rng.uniform(66.5, 70.5)
        trees.append((yb, x + rng.uniform(-0.7, 0.7), h, h * 0.42, rng.random() < 0.35))
    for yb, x, h, w, dk in sorted(trees): rep(pine, x, yb, h, w, dk)
    # grizzly on the arc between side B and the back, in front of the trees
    mound = [(b1 - 4 + t, 66.2 - 2.4 * math.sin(math.pi * t / 30)) for t in np.arange(0, 30.01, 1.0)]
    poly(mound + [(b1 + 26, H + 2), (b1 - 4, H + 2)], C['hill'], 0)
    path('M' + ' L'.join(f'{a:.2f} {b:.2f}' for a, b in mound[3:-3]), sw=0.35)
    bear(b1 + 5.0, 66.6, 1.0)
    # a few pines in front of the bear's meadow edge
    for x, h in ((b1 + 21.5, 15), (b1 + 24.5, 19)): rep(pine, x, 70.5, h, h * 0.42, False)

def panels():
    # board face: wordmark, tagline banner, small carry-on icon
    xa, xb = BOARD; cx = (xa + xb) / 2; inner = xb - xa - 4.0
    text('MONOLITH', BANG, 8.2, cx + 0.6, 14.0 + 0.6, 'c', fill=C['word_sh'], track=0.25, fit=inner, stroke=INK, sw=0.9)
    text('MONOLITH', BANG, 8.2, cx, 14.0, 'c', fill=C['word'], track=0.25, fit=inner, stroke=INK, sw=0.55)
    by0, by1 = 16.2, 25.4
    rib = [(xa + 2.0, by0), (xb - 2.0, by0 + 0.4), (xb - 2.4, by1), (xa + 2.3, by1 - 0.3)]
    poly([(xa + 0.6, by0 + 1.5), (xa + 2.0, by0 + 1.0), (xa + 2.3, by1 - 0.3), (xa + 0.6, by1 + 0.4), (xa + 1.5, (by0 + by1) / 2 + 0.8)], '#cdbb8e', 0.35)
    poly([(xb + 0.4, by0 + 1.9), (xb - 2.0, by0 + 1.4), (xb - 2.4, by1), (xb + 0.4, by1 + 0.6), (xb - 0.5, (by0 + by1) / 2 + 1.2)], '#cdbb8e', 0.35)
    poly(rib, C['banner'], 0.45)
    for i, s in enumerate(('ULTRALIGHT ENERGY', 'DESIGNED FOR BACKPACKERS', 'BY BACKPACKERS')):
        text(s, BOLD if i else XB, 1.75 if i else 2.0, cx, by0 + 2.85 + i * 2.8, 'c', track=0.08, fit=inner - 2)
    plane_icon(xa + 4.6, 47.0, 3.0, ring=False)
    # side A: carry-on mark and the ratings caption
    a0, a1 = SIDE_A; x0, x1 = a0 + 2.0, a1 - 2.0
    caption(x0, VIS0 + 2.0, x1 - 0.8, 50.0)
    ix, iy, ir = x0 + 6.4, VIS0 + 8.6, 5.4
    plane_icon(ix, iy, ir)
    tx = ix + ir + 1.4
    text('CARRY-ON', XB, 3.0, tx, iy - 1.0, fit=x1 - 1.5 - tx)
    text('OK', XB, 3.0, tx, iy + 3.0, fill=C['check'])
    text('UNDER 100 Wh', BOLD, 1.9, tx + 5.0, iy + 3.0, fit=x1 - 1.6 - (tx + 5.0))
    path(f'M{x0 + 1.5:.2f} {iy + ir + 1.6:.2f}H{x1 - 2.3:.2f}', sw=0.3)
    cxA = (x0 + x1 - 0.8) / 2; wA = x1 - x0 - 3.6
    y = iy + ir + 4.8
    text('SPARE LITHIUM-ION BATTERY', XB, 2.0, cxA, y, 'c', fit=wA); y += 2.9
    text('KEEP IN CABIN · NEVER IN CHECKED BAGS', BOLD, 1.6, cxA, y, 'c', fit=wA, fill=C['red']); y += 8.2
    text('91 Wh', XB, 7.0, cxA, y, 'c', stroke=INK, sw=0.0); y += 3.6
    text('Li-ion 14.0 V ' + DC + ' 6.5 Ah  ·  4S1P', BOLD, 2.1, cxA, y, 'c', fit=wA); y += 3.0
    text('USB-C 1 / 2  ·  PD 5–20 V ' + DC + ' 5 A', SEMI, 1.75, cxA, y, 'c', fit=wA); y += 2.5
    text('100 W MAX PER PORT', SEMI, 1.75, cxA, y, 'c', fit=wA); y += 2.9
    text('MONOLITH Mk1 · 2026', BOLD, 1.55, cxA, y, 'c', fit=wA, fill='#5a4d3c')
    # side B: warning caption
    b0, b1 = SIDE_B; x0, x1 = b0 + 2.0, b1 - 2.0
    caption(x0, VIS0 + 2.0, x1 - 0.8, VIS0 + 14.6)
    cxB = (x0 + x1 - 0.8) / 2; wB = x1 - x0 - 3.6
    text('WARNING', XB, 2.6, cxB, VIS0 + 6.4, 'c', fill=C['red'], track=0.2)
    text('Do not crush, puncture or burn.', SEMI, 1.75, cxB, VIS0 + 9.6, 'c', fit=wB)
    text('Keep below 60 °C.', SEMI, 1.75, cxB, VIS0 + 12.3, 'c', fit=wB)

# ---------------- files ----------------
def svg(body, w, h, x0=0.0, y0=0.0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}mm" height="{h:.3f}mm" viewBox="{x0:.3f} {y0:.3f} {w:.3f} {h:.3f}">\n'
            + '\n'.join(body) + '\n</svg>\n')
def cut_lines(stroke='#ec008c', sw=0.15):
    return [f'<rect x="0" y="0" width="{W:.3f}" height="{H:.3f}" rx="2" ry="2" fill="none" stroke="{stroke}" stroke-width="{sw}"/>',
            f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2:.3f}" fill="none" stroke="{stroke}" stroke-width="{sw}"/>']
def folds():
    xs = sorted({round(v, 3) for f in L['flats'] for v in f if 0 < v < PER} | {PER})
    return [f'<path d="M{x:.3f} 0V{H:.3f}" stroke="#00a0e0" stroke-width="0.12" stroke-dasharray="1 1"/>' for x in xs] + \
           [f'<path d="M0 {y:.3f}H{W:.3f}" stroke="#00a0e0" stroke-width="0.12" stroke-dasharray="2 1"/>' for y in (VIS0, VIS1)]

def build():
    out.clear(); scene(); panels()
    art = list(out)
    os.makedirs(OUT, exist_ok=True)
    pw, ph = W + 2 * BLEED, H + 2 * BLEED
    with open(os.path.join(OUT, 'monolith_label_print.svg'), 'w') as f: f.write(svg(art, pw, ph, -BLEED, -BLEED))
    with open(os.path.join(OUT, 'monolith_label_cut.svg'), 'w') as f: f.write(svg(cut_lines(), pw, ph, -BLEED, -BLEED))
    hole = [f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2:.3f}" fill="#ffffff"/>']
    with open(os.path.join(OUT, 'monolith_label_proof.svg'), 'w') as f: f.write(svg(art + hole + cut_lines(sw=0.25) + folds(), pw, ph, -BLEED, -BLEED))
    # the cut-to-size art, hole knocked out, for the cup preview
    clip = (f'<clipPath id="cut"><rect x="0" y="0" width="{W:.3f}" height="{H:.3f}" rx="2"/></clipPath>')
    with open(os.path.join(OUT, 'monolith_label_cut_art.svg'), 'w') as f:
        f.write(svg([clip, '<g clip-path="url(#cut)">'] + art + ['</g>'] +
                    [f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2:.3f}" fill="#00ff00"/>'], W, H))
    return pw, ph

def rasterize(pw, ph, dpmm=24):
    """PNGs and the PDF through headless Chromium (node playwright)"""
    import subprocess, json
    jobs = []
    for name, w, h in (('monolith_label_proof', pw, ph), ('monolith_label_cut_art', W, H)):
        jobs.append(dict(kind='png', svg=name + '.svg', out=name + '.png', w=int(w * dpmm), h=int(h * dpmm)))
    jobs.append(dict(kind='pdf', svg='monolith_label_print.svg', out='monolith_label_print.pdf', w=f'{pw:.3f}mm', h=f'{ph:.3f}mm'))
    js = """const {chromium} = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => { const jobs = JSON.parse(process.argv[2]); const dir = process.argv[3]; const b = await chromium.launch(); const pg = await b.newPage();
for (const j of jobs) { const st = j.kind === 'png' ? `width:${j.w}px;height:${j.h}px` : `width:${j.w};height:${j.h}`;
  const f = path.join(dir, '_' + j.out + '.html'); fs.writeFileSync(f, `<html><body style="margin:0"><img src="${j.svg}" style="${st};display:block"></body></html>`);
  if (j.kind === 'png') await pg.setViewportSize({width: j.w, height: j.h});
  await pg.goto('file://' + f); await pg.waitForTimeout(400);
  if (j.kind === 'png') await pg.screenshot({path: path.join(dir, j.out)});
  else await pg.pdf({path: path.join(dir, j.out), width: j.w, height: j.h, printBackground: true, margin: {top: 0, bottom: 0, left: 0, right: 0}, pageRanges: '1'});
  fs.unlinkSync(f); }
await b.close(); })();"""
    jf = os.path.join(OUT, '_raster.js')
    with open(jf, 'w') as f: f.write(js)
    subprocess.run(['node', jf, json.dumps(jobs), OUT], check=True)
    os.remove(jf)

if __name__ == '__main__':
    print(f'wrap {W:.2f} x {H:.2f} mm (perimeter {PER:.2f} + {LAP} lap), vent at ({VX:.2f}, {VY:.2f}), flats {[(round(a, 2), round(b, 2)) for a, b in L["flats"]]}')
    pw, ph = build(); rasterize(pw, ph)
