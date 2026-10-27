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

def bear(x, yb, s=1.0):
    """walking grizzly facing right, about 16 mm nose to tail at s = 1, feet on yb: shoulder hump, dished face,
    round ears, heavy legs with pale claws, grizzled tips on the hump"""
    g = f'<g transform="translate({x:.3f} {yb:.3f}) scale({s:.4f})">'
    w = lambda v: v / s                                            # stroke widths stay in mm
    body = ('M2.4 0 C2.2 -0.7 1.9 -1.5 1.3 -2.4 C0.5 -3.5 0.3 -5.1 1.0 -6.0 C1.6 -6.8 2.6 -6.9 3.6 -7.1 '
            'C5.0 -7.4 6.6 -8.6 8.4 -8.9 C9.7 -9.1 10.8 -8.6 11.4 -8.0 C12.0 -8.5 12.8 -8.7 13.5 -8.4 '
            'C14.2 -8.1 14.5 -7.4 15.0 -7.0 C15.6 -6.7 16.3 -6.6 16.6 -6.2 C16.9 -5.8 16.7 -5.2 16.1 -5.1 '
            'C15.3 -4.9 14.4 -4.7 13.6 -4.5 C12.9 -4.3 12.5 -3.8 12.6 -3.2 C12.7 -2.1 12.9 -1.1 13.3 -0.6 '
            'C13.8 -0.4 14.0 -0.2 13.8 0 L11.3 0 C11.3 -0.8 11.1 -1.8 10.7 -2.7 C9.4 -3.0 7.2 -2.8 5.8 -2.9 '
            'C5.1 -2.4 4.7 -1.4 4.5 -0.5 C4.7 -0.3 4.8 -0.1 4.6 0 Z')
    far = ('M9.3 -3.2 C9.5 -2.0 9.3 -1.0 9.0 -0.3 C9.0 -0.1 9.1 0 9.3 0 L10.9 0 C10.8 -1.0 11.0 -2.0 11.3 -3.3 Z '
           'M4.8 -3.3 C5.1 -2.1 5.2 -1.0 5.0 -0.3 C5.0 -0.1 5.1 0 5.3 0 L6.9 0 C6.6 -1.0 6.6 -2.1 6.9 -3.1 Z')
    add(g)
    add(f'<path d="{far}" fill="{C["bear_sh"]}" stroke="{INK}" stroke-width="{w(0.3):.3f}" stroke-linejoin="round"/>')
    add(f'<circle cx="12.6" cy="-8.55" r="0.72" fill="{C["bear"]}" stroke="{INK}" stroke-width="{w(0.3):.3f}"/>')   # ear
    add(f'<circle cx="12.65" cy="-8.5" r="0.36" fill="{C["bear_sh"]}"/>')
    _clip[0] += 1; cid = f'b{_clip[0]}'
    add(f'<clipPath id="{cid}"><path d="{body}"/></clipPath>')
    add(f'<path d="{body}" fill="{C["bear"]}"/>')
    add(f'<g clip-path="url(#{cid})">')
    # shadow under the belly and down the legs, then hatching
    sh = 'M0 -3.4 C3 -3.9 8 -4.0 13 -3.6 L16 -3.6 L16 1 L0 1 Z'
    add(f'<path d="{sh}" fill="{C["bear_sh"]}"/>')
    hl = ''.join(f'M{k:.2f} 0.5L{k + 2.2:.2f} -3.6' for k in np.arange(-2, 16, 0.55))
    add(f'<path d="{hl}" stroke="{INK}" stroke-width="{w(0.12):.3f}" fill="none"/>')
    add(f'<ellipse cx="15.8" cy="-5.8" rx="1.5" ry="0.95" fill="#b9814b"/>')                       # pale muzzle
    add(f'<path d="M5.2 -7.7 C7 -9.4 10 -9.6 11.6 -7.9 C10.2 -8.3 7.4 -8.2 5.2 -7.7Z" fill="#b9814b"/>')  # grizzled hump
    add('</g>')
    add(f'<path d="{body}" fill="none" stroke="{INK}" stroke-width="{w(0.4):.3f}" stroke-linejoin="round"/>')
    fur = 'M6.0 -7.9l0.5 0.5l0.3 -0.6l0.5 0.5l0.4 -0.7l0.5 0.5l0.4 -0.6M12.3 -3.6l-0.5 0.4M1.2 -4.6l0.5 0.3M4.6 -7.0l0.6 0.2M11.6 -7.6C12.4 -6.6 12.6 -5.6 12.9 -4.6'
    add(f'<path d="{fur}" fill="none" stroke="{INK}" stroke-width="{w(0.18):.3f}" stroke-linecap="round" stroke-linejoin="round"/>')
    add(f'<path d="M14.9 -5.15 C15.4 -5.3 15.8 -5.25 16.2 -5.15" fill="none" stroke="{INK}" stroke-width="{w(0.16):.3f}"/>')  # mouth
    add(f'<circle cx="14.45" cy="-7.0" r="0.3" fill="{INK}"/><circle cx="14.53" cy="-7.08" r="0.1" fill="{C["cream"]}"/>')
    add(f'<ellipse cx="16.5" cy="-5.95" rx="0.42" ry="0.34" fill="{INK}"/>')                     # nose
    claws = ''.join(f'M{cx + k * 0.42:.2f} -0.05 q0.3 -0.05 0.38 -0.4' for cx in (12.6, 3.7) for k in range(3))
    add(f'<path d="{claws}" fill="none" stroke="{C["cream"]}" stroke-width="{w(0.14):.3f}" stroke-linecap="round"/>')
    add('</g>')

def rock(x0, outline, holes, shade, cap_y, strata, talus_y):
    """sandstone formation (x relative to x0): flat fill, shadowed right side, pale cap rock, ledges, talus at the foot"""
    sh = lambda p: [(x0 + x, y) for x, y in p]
    ring = lambda p: 'M' + ' L'.join(f'{x:.3f} {y:.3f}' for x, y in sh(p)) + 'Z'
    d = ring(outline) + ''.join(ring(h) for h in holes)
    _clip[0] += 1; cid = f'r{_clip[0]}'
    add(f'<clipPath id="{cid}"><path d="{d}" clip-rule="evenodd"/></clipPath>')
    path(d, C['mesa'], 0, extra=' fill-rule="evenodd"')
    add(f'<g clip-path="url(#{cid})">')
    xs = [x0 + x for x, _ in outline]; xa, xb = min(xs) - 1, max(xs) + 1
    add(f'<rect x="{xa:.2f}" y="{talus_y:.2f}" width="{xb - xa:.2f}" height="20" fill="#c96a35"/>')
    poly(sh(shade), C['mesa_sh'], 0); hatch(sh(shade), step=0.75, ang=70, sw=0.15)
    add(f'<rect x="{xa:.2f}" y="0" width="{xb - xa:.2f}" height="{cap_y:.2f}" fill="{C["mesa_top"]}"/>')
    path(f'M{xa:.2f} {cap_y:.2f}' + ''.join(f'L{x:.2f} {cap_y + 0.25 * math.sin(x * 2.1):.2f}' for x in np.arange(xa, xb, 0.8)), sw=0.25)
    for y in strata:
        path(f'M{xa:.2f} {y:.2f}' + ''.join(f'L{x:.2f} {y + 0.3 * math.sin(x * 1.3 + y):.2f}' for x in np.arange(xa, xb, 0.8)), sw=0.2)
    path(f'M{xa:.2f} {talus_y:.2f}' + ''.join(f'L{x:.2f} {talus_y + 0.4 * math.sin(x * 1.7):.2f}' for x in np.arange(xa, xb, 0.8)), sw=0.3)
    for x in np.arange(xa + 1.5, xb - 1, 2.6):                     # boulders on the talus
        y = talus_y + 2.5 + 1.8 * (math.sin(x * 3.7) + 1)
        add(f'<ellipse cx="{x:.2f}" cy="{y:.2f}" rx="0.55" ry="0.4" fill="#e39258" stroke="{INK}" stroke-width="0.18"/>')
    add('</g>')
    path(d, 'none', 0.45)

# side B formations, x from the side B fold: (outline, holes, shadow, cap rock bottom, ledge lines, talus top)
CANYON = [
    ([(13.5, 62), (15.4, 57.5), (16.3, 52), (16.6, 47.5), (16.3, 44.4), (16.9, 42.9), (16.3, 42.0), (17.1, 40.8), (18.7, 40.5),
      (19.8, 41.4), (19.1, 42.8), (19.6, 44.4), (19.5, 48), (20.1, 53), (21.6, 58), (23.5, 62)], [],
     [(18.4, 40), (21, 40), (24, 62), (19.2, 62), (18.8, 52), (18.6, 44)], 42.2, [46.5, 50.5], 54.0),
    ([(-7.0, 62), (-3.6, 57.6), (-1.6, 53.8), (-0.6, 50.8), (-0.3, 45.5), (0.2, 40.5), (0.6, 36.6), (1.0, 34.9), (1.8, 34.3),
      (2.6, 34.9), (2.9, 37.2), (3.0, 40.6), (3.3, 41.8), (3.6, 40.8), (3.8, 36.0), (4.1, 32.6), (4.7, 31.7), (7.0, 31.4),
      (9.2, 31.9), (10.1, 32.4), (10.4, 36.0), (10.6, 41.5), (11.3, 45.6), (12.4, 46.3), (12.9, 49.8), (15.0, 54.4), (18.8, 58.6),
      (22.5, 62)], [],
     [(7.4, 31), (11, 31), (11.6, 46), (13.4, 47), (23, 62), (9.6, 62), (8.6, 48), (8.2, 38)], 33.6, [37.2, 40.9, 44.6], 50.2),
    ([(21.5, 62), (23.8, 57.2), (24.7, 52.0), (25.0, 46.2), (25.4, 41.2), (26.1, 39.7), (29.0, 39.1), (32.5, 39.5), (35.5, 38.9),
      (38.3, 39.6), (39.2, 41.2), (39.6, 46.2), (40.3, 51.2), (42.6, 57.0), (46.5, 62)],
     [[(29.3, 62), (29.4, 53.0), (30.4, 48.1), (32.2, 46.0), (34.2, 46.5), (35.4, 49.2), (35.9, 54.0), (36.1, 62)]],
     [(36.5, 38), (41, 38), (47, 62), (38.6, 62), (37.6, 50), (37.0, 43)], 41.0, [43.6, 46.3], 53.4),
]

MONO = (105.2, 60.2)                          # alien Monolith on the board face: front-left foot of the pack
GLOW, GLOW_PALE = '#56c94c', '#c6f3a4'

def sparkle(x, y, r, fill=GLOW_PALE):
    k = r * 0.28
    poly([(x, y - r), (x + k, y - k), (x + r, y), (x + k, y + k), (x, y + r), (x - k, y + k), (x - r, y), (x - k, y - k)], fill, 0.2)

def alien_monolith(x, yb, fw=5.2, fh=10.6, dx=1.8, dy=-1.3):
    """the pack as a black monolith in 3/4 view: bumpers, the two USB-C ports on top, a green bolt and an alien glow"""
    for g, op in ((1.1, 0.8),):
        add(f'<rect x="{x - g:.2f}" y="{yb - fh + dy - g:.2f}" width="{fw + dx + 2 * g:.2f}" height="{fh - dy + 2 * g:.2f}" rx="{g + 0.6:.2f}" '
            f'fill="none" stroke="{GLOW}" stroke-width="0.35" stroke-dasharray="1.2 0.8" opacity="{op}"/>')
    add(f'<ellipse cx="{x + (fw + dx) / 2:.2f}" cy="{yb + 0.2:.2f}" rx="{(fw + dx) / 2 + 1.5:.2f}" ry="0.8" fill="{C["hill_sh"]}"/>')
    side = [(x + fw, yb), (x + fw + dx, yb + dy), (x + fw + dx, yb - fh + dy), (x + fw, yb - fh)]
    top = [(x, yb - fh), (x + fw, yb - fh), (x + fw + dx, yb - fh + dy), (x + dx, yb - fh + dy)]
    poly(side, '#2a2a2f', 0.4)
    poly(top, '#55555c', 0.4)
    for t in (0.3, 0.7):                                       # the ports
        px, py = x + fw * t + dx * 0.5, yb - fh + dy * 0.5
        add(f'<rect x="{px - 0.75:.2f}" y="{py - 0.22:.2f}" width="1.5" height="0.44" rx="0.22" fill="#0b0b0c" stroke="{GLOW}" stroke-width="0.12"/>')
    poly([(x, yb), (x + fw, yb), (x + fw, yb - fh), (x, yb - fh)], '#1b1b1f', 0.45)
    for y0, h in ((yb - fh, 1.5), (yb - 1.4, 1.4)):            # TPU bumpers
        poly([(x, y0 + h), (x + fw, y0 + h), (x + fw, y0), (x, y0)], '#34343a', 0.3)
    poly([(x + fw, yb - 1.4), (x + fw + dx, yb - 1.4 + dy), (x + fw + dx, yb + dy), (x + fw, yb)], '#3a3a40', 0.3)
    poly([(x + fw, yb - fh + 1.5), (x + fw + dx, yb - fh + 1.5 + dy), (x + fw + dx, yb - fh + dy), (x + fw, yb - fh)], '#3a3a40', 0.3)
    cx, cy = x + fw / 2, yb - fh / 2 - 0.1
    add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="1.75" fill="none" stroke="{GLOW}" stroke-width="0.3"/>')
    poly([(cx + 0.35, cy - 1.3), (cx - 0.75, cy + 0.2), (cx - 0.05, cy + 0.2), (cx - 0.35, cy + 1.3), (cx + 0.75, cy - 0.2), (cx + 0.05, cy - 0.2)], GLOW, 0)
    path(f'M{x + 0.35:.2f} {yb - 1.8:.2f}V{yb - fh + 1.9:.2f}', stroke=GLOW, sw=0.25)
    for sx, sy, r in ((x - 3.2, yb - fh + 1.0, 0.9), (x + fw + dx + 2.6, yb - fh * 0.55, 0.75), (x - 2.4, yb - 3.2, 0.6)):
        sparkle(sx, sy, r)

def ufo(cx, cy, bx, by):
    """flying saucer with a little green pilot, tractor beam down to (bx, by)"""
    beam = [(cx - 1.9, cy + 1.6), (cx + 1.9, cy + 1.6), (bx + 4.3, by), (bx - 4.3, by)]
    poly(beam, GLOW_PALE, 0, extra=' opacity="0.7"')
    for a, b in ((beam[0], beam[3]), (beam[1], beam[2])):
        path(f'M{a[0]:.2f} {a[1]:.2f}L{b[0]:.2f} {b[1]:.2f}', stroke=GLOW, sw=0.3, extra=' stroke-dasharray="1 0.7"')
    for k in range(1, 4):
        t = k / 4; yy = cy + 1.6 + (by - cy - 1.6) * t; hw = 1.9 + (4.3 - 1.9) * t
        path(f'M{cx + (bx - cx) * t - hw * 0.8:.2f} {yy:.2f}h{hw * 1.6:.2f}', stroke=GLOW, sw=0.2, extra=' opacity="0.8"')
    add(f'<path d="M{cx - 2.7:.2f} {cy:.2f}A2.7 2.6 0 0 1 {cx + 2.7:.2f} {cy:.2f}Z" fill="#a8e3ea" stroke="{INK}" stroke-width="0.35"/>')
    add(f'<ellipse cx="{cx + 0.1:.2f}" cy="{cy - 1.0:.2f}" rx="0.9" ry="1.05" fill="{GLOW}" stroke="{INK}" stroke-width="0.2"/>')
    for ex in (-0.35, 0.45):
        add(f'<ellipse cx="{cx + ex:.2f}" cy="{cy - 1.1:.2f}" rx="0.28" ry="0.42" fill="{INK}" transform="rotate({-25 if ex < 0 else 25} {cx + ex:.2f} {cy - 1.1:.2f})"/>')
    path(f'M{cx - 1.3:.2f} {cy - 1.9:.2f}A1.4 1.6 0 0 1 {cx - 0.3:.2f} {cy - 2.35:.2f}', stroke='#ffffff', sw=0.3)
    add(f'<ellipse cx="{cx:.2f}" cy="{cy + 0.9:.2f}" rx="3.4" ry="1.0" fill="#6f7a86" stroke="{INK}" stroke-width="0.35"/>')
    add(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="6.4" ry="1.55" fill="#b9c2cb" stroke="{INK}" stroke-width="0.45"/>')
    path(f'M{cx - 5.6:.2f} {cy - 0.2:.2f}Q{cx:.2f} {cy - 1.3:.2f} {cx + 5.6:.2f} {cy - 0.2:.2f}', stroke='#e8edf1', sw=0.3)
    for k in range(-2, 3):
        add(f'<circle cx="{cx + k * 2.3:.2f}" cy="{cy + 0.45 - 0.08 * abs(k):.2f}" r="0.42" fill="{C["sun"]}" stroke="{INK}" stroke-width="0.18"/>')

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
    # far range, periodic, with snow on the high points; it falls away either side of the board face so the sun
    # rises in open sky
    terms = [(4.0, 3, 1.0), (2.5, 7, 2.0), (1.3, 13, 0.4), (0.7, 29, 1.3)]
    xs = np.arange(X0 - 1, X1 + 1.01, 0.5)
    sun_d = lambda x: min(abs(x - VX), abs(x - VX + PER), abs(x - VX - PER))
    ridge = [(x, wave(x, 33.5, terms) + (32 * (0.5 + 0.5 * math.cos(math.pi * sun_d(x) / 30)) if sun_d(x) < 30 else 0)) for x in xs]
    poly(ridge + [(X1 + 1, Y1 + 1), (X0 - 1, Y1 + 1)], C['far'], 0.35)
    ys = [y for _, y in ridge]
    for n in range(2, len(ridge) - 2):
        x, y = ridge[n]
        if y < 31.5 and y <= min(ys[n - 2:n + 3]):
            cap = [(x - 2.6, y + 2.2), (x - 1.3, y + 1.0), (x, y), (x + 1.4, y + 1.1), (x + 2.8, y + 2.4), (x + 1.6, y + 2.0),
                   (x + 0.9, y + 2.9), (x + 0.1, y + 2.0), (x - 0.9, y + 2.9), (x - 1.6, y + 2.0)]
            poly(cap, C['snow'], 0.3)
    hatch([(x, y + 3.5) for x, y in ridge] + [(X1 + 1, Y1 + 1), (X0 - 1, Y1 + 1)], step=1.3, ang=35, sw=0.12)
    # sun over the board face: the vent hole is its core
    for i in range(16):
        a0 = 2 * math.pi * i / 16; a1 = a0 + 2 * math.pi / 32
        r0, r1 = VENT_HOLE_D / 2 + 2.6, VENT_HOLE_D / 2 + (9.5 if i % 2 == 0 else 6.5)
        poly([(VX + r0 * math.cos(a0), VY + r0 * math.sin(a0)), (VX + r1 * math.cos((a0 + a1) / 2), VY + r1 * math.sin((a0 + a1) / 2)),
              (VX + r0 * math.cos(a1), VY + r0 * math.sin(a1))], C['sun_ray'], 0.3)
    add(f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2 + 2.6:.3f}" fill="{C["sun"]}" stroke="{INK}" stroke-width="0.45"/>')
    add(f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2 + 1.2:.3f}" fill="none" stroke="{INK}" stroke-width="0.2" stroke-dasharray="0.8 0.8"/>')
    b0, b1 = SIDE_B
    # canyon country on side B: a spire, a mitten butte and an arch, standing on talus slopes
    for outline, holes, shade, cap_y, strata, talus_y in CANYON: rock(b0, outline, holes, shade, cap_y, strata, talus_y)
    # desert floor under the rocks
    floor = [(b0 - 6, 60), (b0 + 6, 58.5), (b1 - 6, 59.5), (b1 + 4, 61), (b1 + 4, H + 2), (b0 - 6, H + 2)]
    poly(floor, C['sand'], 0.35)
    for x in np.arange(b0 - 2, b1 + 2, 4.7): scrub(x, 63.5 + 1.2 * math.sin(x), 0.55)
    # rolling green hills, periodic, dipping into the notch
    hterms = [(1.6, 5, 0.3), (1.0, 11, 1.7)]
    hills = []
    for x in xs:
        y = wave(x, 54.0, hterms)
        d = sun_d(x)
        if d < 22: y += (22 - d) / 22 * 13          # valley under the sun
        if b0 - 4 < x < b1 + 4: y = max(y, 63.5)    # stays below the desert floor
        hills.append((x, y))
    hill_poly = hills + [(X1 + 1, Y1 + 1), (X0 - 1, Y1 + 1)]
    poly(hill_poly, C['hill'], 0.4)
    hatch([(x, y + 4) for x, y in hills] + [(X1 + 1, Y1 + 1), (X0 - 1, Y1 + 1)], step=1.1, ang=25, sw=0.14)
    # the alien Monolith on the hill right of the sun, a saucer beaming it
    alien_monolith(*MONO)
    ufo(MONO[0] + 3.3, 33.5, MONO[0] + 3.3, MONO[1] - 12.2)
    # pine forest: tall at the back and seam, a treeline under side A, sparse on the board face, none in the desert
    rng = np.random.default_rng(7)
    trees = []
    for x in np.arange(0, PER, 2.4):
        if b0 - 3 < x < b1 + 1: continue
        d = abs(x - VX)
        if d < 7 or MONO[0] - 3 < x < MONO[0] + 9: continue
        back = x < SIDE_A[0] - 1 or x > b1 + 1
        h = (rng.uniform(17, 26) if back else rng.uniform(9, 14)) * (0.7 if d < 16 else 1.0)
        yb = rng.uniform(66.5, 70.5)
        trees.append((yb, x + rng.uniform(-0.7, 0.7), h, h * 0.42, rng.random() < 0.35))
    for yb, x, h, w, dk in sorted(trees): rep(pine, x, yb, h, w, dk)
    # grizzly on the arc between side B and the back, in front of the trees
    mound = [(b1 - 4 + t, 66.2 - 2.4 * math.sin(math.pi * t / 30)) for t in np.arange(0, 30.01, 1.0)]
    poly(mound + [(b1 + 26, H + 2), (b1 - 4, H + 2)], C['hill'], 0)
    path('M' + ' L'.join(f'{a:.2f} {b:.2f}' for a, b in mound[3:-3]), sw=0.35)
    bear(b1 + 2.0, 66.8, 1.1)
    # a few pines in front of the bear's meadow edge
    for x, h in ((b1 + 23.5, 15), (b1 + 26.0, 19)): rep(pine, x, 70.5, h, h * 0.42, False)

def panels():
    # board face: wordmark and tagline banner
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
    # side A: carry-on mark and the ratings caption
    a0, a1 = SIDE_A; x0, x1 = a0 + 2.0, a1 - 2.0
    caption(x0, VIS0 + 2.0, x1 - 0.8, 48.8)
    ix, iy, ir = x0 + 6.4, VIS0 + 8.6, 5.4
    plane_icon(ix, iy, ir)
    tx = ix + ir + 1.4
    text('CARRY-ON', XB, 3.0, tx, iy - 1.0, fit=x1 - 1.5 - tx)
    text('OK', XB, 3.0, tx, iy + 3.0, fill=C['check'])
    text('UNDER 100 Wh', BOLD, 1.9, tx + 5.0, iy + 3.0, fit=x1 - 1.6 - (tx + 5.0))
    path(f'M{x0 + 1.5:.2f} {iy + ir + 1.6:.2f}H{x1 - 2.3:.2f}', sw=0.3)
    cxA = (x0 + x1 - 0.8) / 2; wA = x1 - x0 - 3.6
    y = iy + ir + 5.0
    text('LITHIUM-ION BATTERY', XB, 2.2, cxA, y, 'c', fit=wA); y += 9.6
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
