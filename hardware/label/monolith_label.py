"""Monolith wrap label: one printed vinyl rectangle round the whole cup, top and bottom edges under the TPU bumpers.
Spec: the "Cup label plan" doc (2026-10-27). The layout comes from the cup model (hardware/mechanical/monolith_cup.py):
the cup's outside is a prism, so the label is a flat rectangle, cup perimeter + LAP long, seam in the middle of the
back face, art running unbroken across the seam (the overlap repeats the first LAP mm).
Run: python monolith_label.py      (numpy, fonttools, manifold3d, cairosvg, pypdf)
-> out/monolith_label_print.pdf    send this: artwork with 2 mm bleed, all text as outlines, page = art + bleed exactly,
                                   TrimBox = the cut size, die line as a CutContour spot-colour stroke (overprint)
   out/monolith_label_print.svg    the artwork alone
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
LAP, BLEED = 5.0, 2.0                # seam overlap, print bleed
TUCK = K.LABEL_TUCK                  # edge under each bumper; label heights and the vent hole come from monolith_cup
VENT_HOLE_D = 2 * K.VENT_HOLE_R

def wrap_layout():
    # the vinyl's mid-thickness, not the cup surface: wrapping the film round the corners and arcs adds pi * LABEL_T
    P = np.array(K.cs_out.offset(K.LABEL_T / 2, K.ROUND, circular_segments=720).to_polygons()[0], float)
    seg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    per = s[-1]
    back = [i for i in range(len(P)) if seg[i] > 2 and abs(P[i, 0] - P[(i + 1) % len(P), 0]) < 1e-4 and P[i, 0] < 0]
    i = back[0]; seam = s[i] + seg[i] / 2                          # middle of the back flat
    flats = []                                                    # (x0, x1) of each flat in label x
    for j in range(len(P)):
        if seg[j] > 2: flats.append((((s[j] - seam) % per), ((s[j] - seam) % per) + seg[j]))
    flats.sort()
    z_bot, z_top = K.LABEL_Z                                      # label edges on the cup
    # vent: board-face centre (y = VENT_Y) at VENT_Z
    jb = [j for j in range(len(P)) if seg[j] > 2 and abs(P[j, 0] - P[(j + 1) % len(P), 0]) < 1e-4 and P[j, 0] > 0][0]
    vx = (s[jb] + (K.VENT_Y - P[jb, 1]) - seam) % per
    return dict(per=per, seam=seam, flats=flats, z_bot=z_bot, z_top=z_top, H=z_top - z_bot, W=per + LAP,
                vent=(vx, z_top - K.VENT_Z), poly=P, s=s[:-1])

L = wrap_layout()
PER, W, H = L['per'], L['W'], L['H']
VX, VY = L['vent']
FLATS = [f for f in L['flats'] if f[1] - f[0] > 30 and f[1] < PER]   # side A, board face, side B (the back flat wraps)
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
def hatch(p, step=1.0, ang=45, sw=0.25):
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
    if stroke and sw:                                  # outline under the fill: a stroked copy first, then the fill
        add(f'<path d="{d}" fill="{stroke}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>')
    add(f'<path d="{d}" fill="{fill}"/>')
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
    """walking grizzly facing right, about 16.6 mm nose to tail at s = 1, feet on yb: shoulder hump, dished face,
    round ears, heavy legs with pale claws, a lit back and grizzled tips on the hump"""
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
    add(f'<path d="{far}" fill="{C["bear_sh"]}" stroke="{INK}" stroke-width="{w(0.4):.3f}" stroke-linejoin="round"/>')
    add(f'<circle cx="11.95" cy="-8.4" r="0.6" fill="{C["bear_sh"]}" stroke="{INK}" stroke-width="{w(0.35):.3f}"/>')   # far ear
    add(f'<circle cx="12.6" cy="-8.55" r="0.72" fill="{C["bear"]}" stroke="{INK}" stroke-width="{w(0.35):.3f}"/>')     # near ear
    add(f'<circle cx="12.65" cy="-8.5" r="0.36" fill="{C["bear_sh"]}"/>')
    _clip[0] += 1; cid = f'b{_clip[0]}'
    add(f'<clipPath id="{cid}"><path d="{body}"/></clipPath>')
    add(f'<path d="{body}" fill="{C["bear"]}"/>')
    add(f'<g clip-path="url(#{cid})">')
    # shadow under the belly and down the legs, then hatching
    add(f'<path d="M0 -3.4 C3 -3.9 8 -4.0 13 -3.6 L16 -3.6 L16 1 L0 1 Z" fill="{C["bear_sh"]}"/>')
    hl = ''.join(f'M{k:.2f} 0.5L{k + 2.2:.2f} -3.6' for k in np.arange(-2, 16, 0.95))
    add(f'<path d="{hl}" stroke="{INK}" stroke-width="{w(0.25):.3f}" fill="none"/>')
    add(f'<ellipse cx="15.8" cy="-5.8" rx="1.5" ry="0.95" fill="#b9814b"/>')                       # pale muzzle
    add(f'<path d="M3.4 -6.75 C5.0 -7.05 6.6 -8.25 8.4 -8.55 C9.7 -8.75 10.6 -8.35 11.1 -7.85" fill="none" stroke="#c58a52" '
        f'stroke-width="{w(0.5):.3f}" stroke-linecap="round"/>')                                       # light along the back
    add(f'<path d="M6.0 -8.0q0.5 0.6 1.1 0.4M7.5 -8.4q0.5 0.6 1.1 0.4M9.0 -8.5q0.5 0.6 1.1 0.4" fill="none" stroke="#d9a46c" '
        f'stroke-width="{w(0.3):.3f}" stroke-linecap="round"/>')                                       # grizzled hump
    add('</g>')
    add(f'<path d="{body}" fill="none" stroke="{INK}" stroke-width="{w(0.55):.3f}" stroke-linejoin="round"/>')
    fur = 'M12.3 -3.6l-0.5 0.4M1.2 -4.6l0.5 0.3M4.6 -7.0l0.6 0.2M11.6 -7.6C12.4 -6.6 12.6 -5.6 12.9 -4.6'
    add(f'<path d="{fur}" fill="none" stroke="{INK}" stroke-width="{w(0.25):.3f}" stroke-linecap="round" stroke-linejoin="round"/>')
    add(f'<path d="M14.9 -5.15 C15.4 -5.3 15.8 -5.25 16.2 -5.15" fill="none" stroke="{INK}" stroke-width="{w(0.25):.3f}"/>')  # mouth
    add(f'<circle cx="14.45" cy="-7.0" r="0.3" fill="{INK}"/><circle cx="14.53" cy="-7.08" r="0.1" fill="{C["cream"]}"/>')
    add(f'<ellipse cx="16.5" cy="-5.95" rx="0.42" ry="0.34" fill="{INK}"/>')                     # nose
    claws = ''.join(f'M{cx + k * 0.42:.2f} -0.05 q0.3 -0.05 0.38 -0.4' for cx in (12.6, 3.7) for k in range(3))
    add(f'<path d="{claws}" fill="none" stroke="{C["cream"]}" stroke-width="{w(0.25):.3f}" stroke-linecap="round"/>')
    add('</g>')

def blob(cx, cy, r, rng, n=7):
    """irregular round polygon (rocks, clods, moss)"""
    return [(cx + r * rng.uniform(0.7, 1.1) * math.cos(2 * math.pi * k / n), cy + r * rng.uniform(0.6, 0.95) * math.sin(2 * math.pi * k / n)) for k in range(n)]

def rock(x0, outline, holes, shade, cap_y, strata, talus_y, seed):
    """sandstone formation (x relative to x0): flat fill, shadowed right side, pale cap rock with varnish streaks hanging
    from it, broken ledges, talus at the foot with a few boulder clusters"""
    rng = np.random.default_rng(seed)
    sh = lambda p: [(x0 + x, y) for x, y in p]
    ring = lambda p: 'M' + ' L'.join(f'{x:.3f} {y:.3f}' for x, y in sh(p)) + 'Z'
    d = ring(outline) + ''.join(ring(h) for h in holes)
    _clip[0] += 1; cid = f'r{_clip[0]}'
    add(f'<clipPath id="{cid}"><path d="{d}" clip-rule="evenodd"/></clipPath>')
    path(d, C['mesa'], 0, extra=' fill-rule="evenodd"')
    add(f'<g clip-path="url(#{cid})">')
    xs = [x0 + x for x, _ in outline]; xa, xb = min(xs) - 1, max(xs) + 1
    add(f'<rect x="{xa:.2f}" y="{talus_y:.2f}" width="{xb - xa:.2f}" height="20" fill="#c96a35"/>')
    poly(sh(shade), C['mesa_sh'], 0); hatch(sh(shade), step=1.0, ang=70, sw=0.25)
    add(f'<rect x="{xa:.2f}" y="0" width="{xb - xa:.2f}" height="{cap_y:.2f}" fill="{C["mesa_top"]}"/>')
    for x in rng.uniform(xa + 1, xb - 1, int((xb - xa) / 1.6)):     # desert varnish down the cliff
        path(f'M{x:.2f} {cap_y + 0.2:.2f}l{rng.uniform(-0.2, 0.2):.2f} {rng.uniform(1.5, 4.0):.2f}', stroke='#8a3f24', sw=0.3)
    path(f'M{xa:.2f} {cap_y:.2f}' + ''.join(f'L{x:.2f} {cap_y + 0.25 * math.sin(x * 2.1):.2f}' for x in np.arange(xa, xb, 0.8)), sw=0.3)
    for y in strata:                                               # ledges: broken, uneven
        x = xa + rng.uniform(0, 1.5)
        while x < xb:
            run, amp = rng.uniform(2.5, 6.5), rng.uniform(0.12, 0.5)
            q = [(u, y + amp * math.sin(u * 1.3 + y) + rng.uniform(-0.06, 0.06)) for u in np.arange(x, min(x + run, xb), 0.6)]
            if len(q) > 1: path('M' + ' L'.join(f'{a:.2f} {b:.2f}' for a, b in q), sw=0.28)
            x += run + rng.uniform(0.6, 1.8)
    path(f'M{xa:.2f} {talus_y:.2f}' + ''.join(f'L{x:.2f} {talus_y + 0.4 * math.sin(x * 1.7):.2f}' for x in np.arange(xa, xb, 0.8)), sw=0.3)
    for cx in rng.uniform(xa + 2, xb - 2, max(2, int((xb - xa) / 7))):   # boulder clusters on the talus
        cy = talus_y + rng.uniform(2.5, 5.5)
        for _ in range(rng.integers(2, 4)):
            poly(blob(cx + rng.uniform(-1.2, 1.2), cy + rng.uniform(-0.5, 0.5), rng.uniform(0.3, 0.9), rng), '#e39258', 0.25)
    add('</g>')
    path(d, 'none', 0.55)

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
    ([(21.5, 62), (23.8, 57.2), (24.7, 52.0), (25.0, 46.2), (25.4, 41.2), (26.1, 39.7), (28.6, 38.9), (30.6, 38.2), (32.0, 37.6),
      (33.6, 38.3), (35.6, 38.7), (38.3, 39.6), (39.2, 41.2), (39.6, 46.2), (40.3, 51.2), (42.6, 57.0), (46.5, 62)],
     [[(29.3, 62), (29.3, 53.0), (29.9, 47.5), (31.4, 44.4), (33.2, 43.5), (35.0, 44.2), (36.3, 47.0), (36.9, 52.0), (37.0, 62)]],
     [(36.5, 38), (41, 38), (47, 62), (38.6, 62), (37.8, 50), (37.2, 43)], 40.6, [46.0, 49.6], 53.4),
]

MONO = (107.0, 60.4)                          # the ancient artifact on the board face: front-left foot of the pack, sunk in the hill
GLOW = '#56c94c'

def artifact(x, yb, fw=4.9, fh=11.5, dx=1.6, dy=-1.1, tilt=8.0):
    """the pack as an ancient alien artifact left in the earth: a weathered black slab leaning in the hillside, chipped,
    cracked and mossy, with alien glyphs and the two USB-C ports glowing green"""
    cx = x + fw / 2
    rng = np.random.default_rng(11)
    gx, gy = cx + fh * 0.45 * math.sin(math.radians(tilt)), yb - fh * 0.55        # glow: short strokes round the slab's middle
    for k, a in enumerate(np.linspace(-160, -20, 8)):
        r0, r1 = fh * 0.62, fh * 0.62 + (2.4 if k % 2 else 1.5)
        u, v = math.cos(math.radians(a)), math.sin(math.radians(a))
        path(f'M{gx + r0 * u:.2f} {gy + r0 * v:.2f}L{gx + r1 * u:.2f} {gy + r1 * v:.2f}', stroke=INK if k % 2 else GLOW, sw=0.35)
    add(f'<g transform="rotate({tilt:.1f} {cx:.2f} {yb:.2f})">')
    ch = 1.3                                                        # chipped top-left corner
    yt = yb - fh
    poly([(x + fw, yb + 3), (x + fw + dx, yb + 3 + dy), (x + fw + dx, yt + dy), (x + fw, yt)], '#2a2a2f', 0.45)        # side
    poly([(x + ch, yt), (x + fw, yt), (x + fw + dx, yt + dy), (x + ch + dx, yt + dy)], '#4b4b52', 0.45)                # top
    poly([(x, yt + ch), (x + ch, yt), (x + ch + dx, yt + dy), (x + dx, yt + ch + dy)], '#3b3b42', 0.4)                 # chip
    poly([(x, yb + 3), (x + fw, yb + 3), (x + fw, yt), (x + ch, yt), (x, yt + ch)], '#1d1d22', 0.5)                   # front
    for t in (0.42, 0.76):                                           # the ports, glowing
        px, py = x + ch + (fw - ch) * t + dx * 0.5 - 0.4, yt + dy * 0.5
        add(f'<rect x="{px - 0.7:.2f}" y="{py - 0.22:.2f}" width="1.4" height="0.44" rx="0.22" fill="{GLOW}" stroke="{INK}" stroke-width="0.25"/>')
    gl = cx + 0.1                                                    # alien glyphs down the face
    glyphs = [f'M{gl - 0.8:.2f} {yt + 2.4:.2f}a0.8 0.8 0 1 0 1.6 0a0.8 0.8 0 1 0 -1.6 0M{gl:.2f} {yt + 1.2:.2f}v2.4',
              f'M{gl - 0.9:.2f} {yt + 5.6:.2f}L{gl:.2f} {yt + 4.2:.2f}L{gl + 0.9:.2f} {yt + 5.6:.2f}ZM{gl:.2f} {yt + 5.0:.2f}v0.01',
              f'M{gl - 0.9:.2f} {yt + 6.9:.2f}h1.8M{gl - 0.6:.2f} {yt + 7.6:.2f}h1.2M{gl - 0.9:.2f} {yt + 8.3:.2f}h1.8',
              f'M{gl + 0.7:.2f} {yt + 9.3:.2f}a0.9 0.9 0 1 0 0 1.4M{gl - 0.2:.2f} {yt + 10.0:.2f}h0.6']
    for gd in glyphs: path(gd, stroke=GLOW, sw=0.35)
    path(f'M{x + 0.6:.2f} {yt + 3.4:.2f}l0.9 1.1l-0.4 1.0l0.8 1.3M{x + fw - 0.4:.2f} {yt + 6.5:.2f}l-0.8 0.9l0.3 1.2'
         f'M{x + fw + 0.5:.2f} {yt + 2.0 + dy:.2f}l0.4 1.6l-0.2 1.4', stroke='#5a5a62', sw=0.3)          # cracks
    for mx, my, mr in ((x + ch + 1.2, yt + dy * 0.6, 0.9), (x + fw + 0.2, yt + dy * 0.4, 0.7), (x + 0.4, yt + ch + 0.6, 0.6)):
        poly(blob(mx, my, mr, rng), '#6f8f3a', 0.3)                  # moss on the old stone
    path(f'M{x + fw + 0.8:.2f} {yt + dy + 0.3:.2f}c0.4 1.2 -0.3 2.0 0.2 3.2c0.3 0.8 -0.1 1.4 0.1 2.0', stroke='#4f7a2f', sw=0.35)  # vine
    add('</g>')
    # sunk in the earth: a turf mound with dirt clods over its foot
    x0m, x1m = x - 3.8, x + fw + dx + 4.4
    mound = [(x0m + t * (x1m - x0m), yb + 2.6 - 3.6 * math.sin(math.pi * t) ** 0.7) for t in np.linspace(0, 1, 25)]
    poly(mound + [(x1m, yb + 6), (x0m, yb + 6)], C['hill'], 0)
    path('M' + ' L'.join(f'{a:.2f} {b:.2f}' for a, b in mound[2:-2]), sw=0.5)
    for k in range(5):
        poly(blob(x - 1.6 + k * 2.2 + rng.uniform(-0.3, 0.3), yb + 0.4 + rng.uniform(-0.2, 0.6), rng.uniform(0.35, 0.6), rng), '#8a5a35', 0.25)

def birds(pts_):
    for bx, by, r in pts_:
        path(f'M{bx - r:.2f} {by - r * 0.35:.2f}q{r * 0.5:.2f} {-r * 0.45:.2f} {r:.2f} {r * 0.35:.2f}q{r * 0.5:.2f} {-r * 0.8:.2f} {r:.2f} {-r * 0.35:.2f}', sw=0.35)

def plane_icon(cx, cy, r, ring=True):
    """carry-on mark: airliner and a check, in a circle"""
    add(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="{C["cream"]}" stroke="{INK}" stroke-width="{max(0.3, r * 0.08):.3f}"/>')
    if ring: add(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r * 0.84:.3f}" fill="none" stroke="{INK}" stroke-width="{max(0.25, r * 0.03):.3f}"/>')
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
    add(f'<rect x="{X0}" y="{Y0}" width="{X1 - X0}" height="{28 - Y0}" fill="{C["sky1"]}"/>')
    add(f'<rect x="{X0}" y="{Y0}" width="{X1 - X0}" height="{10.5 - Y0}" fill="{C["sky0"]}"/>')
    # clouds over the forest
    for cx, cy, s in ((8, 9, 1.0), (176, 7.5, 0.8), (22, 15.5, 0.6)): rep(cloud, cx, cy, s)
    # far range, periodic, with snow on the high points; it falls away either side of the board face so the sun
    # rises in open sky
    terms = [(4.0, 3, 1.0), (2.5, 7, 2.0), (1.3, 13, 0.4), (0.7, 29, 1.3)]
    xs = np.arange(X0 - 1, X1 + 1.01, 0.5)
    sun_d = lambda x: min(abs(x - VX), abs(x - VX + PER), abs(x - VX - PER))
    ridge = [(x, wave(x, 33.5, terms) + (32 * (0.5 + 0.5 * math.cos(math.pi * sun_d(x) / 30)) if sun_d(x) < 30 else 0)) for x in xs]
    poly(ridge + [(X1 + 1, Y1 + 1), (X0 - 1, Y1 + 1)], C['far'], 0)
    # cel shadow on the slopes that fall away to the right (light from the left all round, so it repeats at the seam)
    run = []
    for n in range(len(ridge)):
        down = n + 1 < len(ridge) and ridge[n + 1][1] - ridge[n][1] > 0.05
        if down: run.append(ridge[n])
        elif run:
            run.append(ridge[n]); x0r, x1r = run[0][0], run[-1][0]
            if x1r - x0r > 1.0:                                     # a facet: down the slope, back up a slanted edge
                (xp, yp), (xv, yv) = run[0], run[-1]
                sp = run + [(xv + 0.2 * (Y1 + 1 - yv), Y1 + 1), (xp + 0.45 * (Y1 + 1 - yp), Y1 + 1)]
                poly(sp, C['far_sh'], 0); hatch(sp, step=1.4, ang=35, sw=0.25)
            run = []
    path('M' + ' L'.join(f'{x:.2f} {y:.2f}' for x, y in ridge), sw=0.3)
    ys = [y for _, y in ridge]
    for n in range(6, len(ridge) - 6):
        x, y = ridge[n]
        if y < 35 and y <= min(ys[n - 6:n + 7]):
            cap = [(x - 2.6, y + 2.2), (x - 1.3, y + 1.0), (x, y), (x + 1.4, y + 1.1), (x + 2.8, y + 2.4), (x + 1.6, y + 2.0),
                   (x + 0.9, y + 2.9), (x + 0.1, y + 2.0), (x - 0.9, y + 2.9), (x - 1.6, y + 2.0)]
            poly(cap, C['snow'], 0.3)
    # sun over the board face: the vent hole is its core
    for i in range(16):
        a0 = 2 * math.pi * i / 16; a1 = a0 + 2 * math.pi / 32
        if math.sin((a0 + a1) / 2) > 0.2: continue                 # under the hills anyway
        r0, r1 = VENT_HOLE_D / 2 + 2.6, VENT_HOLE_D / 2 + (7.0 if i % 2 == 0 else 4.5)
        poly([(VX + r0 * math.cos(a0), VY + r0 * math.sin(a0)), (VX + r1 * math.cos((a0 + a1) / 2), VY + r1 * math.sin((a0 + a1) / 2)),
              (VX + r0 * math.cos(a1), VY + r0 * math.sin(a1))], C['sun_ray'], 0.3)
    add(f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2 + 2.6:.3f}" fill="{C["sun"]}" stroke="{INK}" stroke-width="0.45"/>')
    add(f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2 + 1.2:.3f}" fill="none" stroke="{C["sun_ray"]}" stroke-width="0.4"/>')
    b0, b1 = SIDE_B
    # canyon country on side B: a spire, a mitten butte and an arch, standing on talus slopes
    for k, (outline, holes, shade, cap_y, strata, talus_y) in enumerate(CANYON): rock(b0, outline, holes, shade, cap_y, strata, talus_y, 20 + k)
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
        e = min(x - (b0 - 12), (b1 + 12) - x) / 8     # eases down under the desert floor
        if e > 0: y += (max(y, 63.5) - y) * min(1.0, e)
        hills.append((x, y))
    hill_poly = hills + [(X1 + 1, Y1 + 1), (X0 - 1, Y1 + 1)]
    poly(hill_poly, C['hill'], 0.5)
    hatch([(x, y + 4) for x, y in hills] + [(X1 + 1, Y1 + 1), (X0 - 1, Y1 + 1)], step=1.3, ang=25, sw=0.25)
    # the ancient alien artifact sunk in the hill right of the sun; birds in the open sky left of it
    artifact(*MONO)
    birds([(BOARD[0] + 5.5, 33.0, 1.1), (BOARD[0] + 9.6, 30.4, 0.9), (BOARD[0] + 8.0, 36.2, 0.75)])
    # pine forest: tall at the back and seam, a treeline under side A, sparse on the board face, none in the desert
    rng = np.random.default_rng(7)
    trees = []
    for x in np.arange(0, PER, 2.4):
        if b0 - 3 < x < b1 + 1: continue
        d = abs(x - VX)
        if d < 7 or MONO[0] - 5 < x < MONO[0] + 12: continue
        back = x < SIDE_A[0] - 1 or x > b1 + 1
        h = (rng.uniform(17, 26) if back else rng.uniform(9, 14)) * (0.7 if d < 16 else 1.0)
        yb = rng.uniform(66.5, 70.5)
        trees.append((yb, x + rng.uniform(-0.7, 0.7), h, h * 0.42, rng.random() < 0.35))
    for yb, x, h, w, dk in sorted(trees): rep(pine, x, yb, h, w, dk)
    # grizzly on the arc between side B and the back, in front of the trees
    mound = [(b1 - 4 + t, 64.9 - 2.6 * math.sin(math.pi * t / 32)) for t in np.arange(0, 32.01, 1.0)]
    poly(mound + [(b1 + 28, H + 2), (b1 - 4, H + 2)], C['hill'], 0)
    path('M' + ' L'.join(f'{a:.2f} {b:.2f}' for a, b in mound[3:-3]), sw=0.5)
    bear(b1 + 1.0, 65.3, 1.3)
    # a few pines in front of the bear's meadow edge
    for x, h in ((b1 + 27.5, 15), (b1 + 30.0, 19)): rep(pine, x, 70.5, h, h * 0.42, False)

def panels():
    # board face: wordmark and tagline banner
    xa, xb = BOARD; cx = (xa + xb) / 2; inner = xb - xa - 4.0
    wy = 14.6                                         # wordmark: stacked red shadow, heavy outline
    text('MONOLITH', BANG, 9.0, cx + 1.2, wy + 1.2, 'c', fill=C['word_sh'], track=0.1, fit=inner, stroke=INK, sw=1.4)
    for o in (0.9, 0.6, 0.3): text('MONOLITH', BANG, 9.0, cx + o, wy + o, 'c', fill=C['word_sh'], track=0.1, fit=inner)
    text('MONOLITH', BANG, 9.0, cx, wy, 'c', fill=C['word'], track=0.1, fit=inner, stroke=INK, sw=0.8)
    by0, by1 = 17.4, 26.6
    rib = [(xa + 2.0, by0), (xb - 2.0, by0 + 0.4), (xb - 2.4, by1), (xa + 2.3, by1 - 0.3)]
    poly([(xa + 0.6, by0 + 1.5), (xa + 2.0, by0 + 1.0), (xa + 2.3, by1 - 0.3), (xa + 0.6, by1 + 0.4), (xa + 1.5, (by0 + by1) / 2 + 0.8)], '#cdbb8e', 0.35)
    poly([(xb + 0.4, by0 + 1.9), (xb - 2.0, by0 + 1.4), (xb - 2.4, by1), (xb + 0.4, by1 + 0.6), (xb - 0.5, (by0 + by1) / 2 + 1.2)], '#cdbb8e', 0.35)
    poly(rib, C['banner'], 0.45)
    for i, s in enumerate(('ULTRALIGHT ENERGY', 'DESIGNED FOR BACKPACKERS', 'BY BACKPACKERS')):
        text(s, BOLD if i else XB, 1.75 if i else 2.0, cx, by0 + 2.85 + i * 2.8, 'c', track=0.08, fit=inner - 2)
    # side A: carry-on mark and the ratings caption
    a0, a1 = SIDE_A; x0, x1 = a0 + 2.0, a1 - 2.0
    caption(x0, VIS0 + 2.0, x1 - 0.8, 47.4)
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
    text('14.0 V ' + DC + ' 6.5 Ah  ·  4S1P', BOLD, 2.1, cxA, y, 'c', fit=wA); y += 3.1
    text('USB-C 1 / 2  ·  PD 5–20 V ' + DC + ' 5 A', SEMI, 2.0, cxA, y, 'c', fit=wA); y += 2.9
    text('100 W MAX PER PORT', SEMI, 2.0, cxA, y, 'c', fit=wA); y += 3.0
    text('MONOLITH Mk1 · 2026', BOLD, 1.8, cxA, y, 'c', fit=wA, fill='#5a4d3c')
    # side B: warning caption
    b0, b1 = SIDE_B; x0, x1 = b0 + 2.0, b1 - 2.0
    caption(x0, VIS0 + 2.0, x1 - 0.8, VIS0 + 23.4)
    cxB = (x0 + x1 - 0.8) / 2; wB = x1 - x0 - 3.6
    text('WARNING', XB, 2.6, cxB, VIS0 + 6.4, 'c', fill=C['red'], track=0.2)
    for i, ln in enumerate(('Do not crush, puncture or burn.', 'Keep below 60 °C.', 'Stop using if swollen,', 'hot or smelling.', "Recycle, don't bin.")):
        text(ln, SEMI, 2.1, cxB, VIS0 + 9.9 + i * 2.9, 'c', fit=wB)

# ---------------- files ----------------
def svg(body, w, h, x0=0.0, y0=0.0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}mm" height="{h:.3f}mm" viewBox="{x0:.3f} {y0:.3f} {w:.3f} {h:.3f}">\n'
            + '\n'.join(body) + '\n</svg>\n')
def cut_lines(stroke='#ec008c', sw=0.15):
    return [f'<rect x="0" y="0" width="{W:.3f}" height="{H:.3f}" rx="2" ry="2" fill="none" stroke="{stroke}" stroke-width="{sw}"/>',
            f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2:.3f}" fill="none" stroke="{stroke}" stroke-width="{sw}"/>']
def folds():
    xs = sorted({round(v % PER, 3) for f in L['flats'] for v in f} | {PER})
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
    """PNGs and the print PDF through cairosvg (exact page size: Chromium rounds PDF pages to 1/100 in)"""
    import cairosvg
    for name, w, h in (('monolith_label_proof', pw, ph), ('monolith_label_cut_art', W, H)):
        cairosvg.svg2png(url=os.path.join(OUT, name + '.svg'), write_to=os.path.join(OUT, name + '.png'),
                         output_width=round(w * dpmm), output_height=round(h * dpmm), background_color='white')
    pdf = os.path.join(OUT, 'monolith_label_print.pdf')
    cairosvg.svg2pdf(url=os.path.join(OUT, 'monolith_label_print.svg'), write_to=pdf)
    add_cut_contour(pdf, pw, ph)

def add_cut_contour(pdf, pw, ph, r=2.0):
    """put the die line in the print PDF as a stroke in the CutContour spot colour (100 % magenta alternate, overprint),
    and set TrimBox = cut size, BleedBox = page"""
    import pypdf
    from pypdf.generic import NameObject, ArrayObject, DictionaryObject, FloatObject, NumberObject, BooleanObject, DecodedStreamObject, RectangleObject
    pt = 72 / 25.4; rd = pypdf.PdfReader(pdf); wr = pypdf.PdfWriter(); pg = wr.add_page(rd.pages[0])
    mw, mh = float(pg.mediabox.width), float(pg.mediabox.height)
    assert abs(mw - pw * pt) < 0.05 and abs(mh - ph * pt) < 0.05, ('PDF page size', mw / pt, mh / pt, pw, ph)
    X = lambda x: (x + BLEED) * pt; Y = lambda y: mh - (y + BLEED) * pt          # label mm (y down) -> PDF pt
    k = 0.5523                                                                   # Bezier quarter-circle
    def arc(cx, cy, r, a0):                                                      # quarter arc from angle a0 (deg), y down
        p = lambda a: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
        (x0, y0), (x3, y3) = p(a0), p(a0 + 90)
        t0 = (-math.sin(math.radians(a0)), math.cos(math.radians(a0))); t3 = (-math.sin(math.radians(a0 + 90)), math.cos(math.radians(a0 + 90)))
        c1 = (x0 + k * r * t0[0], y0 + k * r * t0[1]); c2 = (x3 - k * r * t3[0], y3 - k * r * t3[1])
        return f'{X(c1[0]):.3f} {Y(c1[1]):.3f} {X(c2[0]):.3f} {Y(c2[1]):.3f} {X(x3):.3f} {Y(y3):.3f} c'
    outline = (f'{X(r):.3f} {Y(0):.3f} m {X(W - r):.3f} {Y(0):.3f} l {arc(W - r, r, r, -90)} {X(W):.3f} {Y(H - r):.3f} l {arc(W - r, H - r, r, 0)} '
               f'{X(r):.3f} {Y(H):.3f} l {arc(r, H - r, r, 90)} {X(0):.3f} {Y(r):.3f} l {arc(r, r, r, 180)} h')
    vr = VENT_HOLE_D / 2
    hole = f'{X(VX + vr):.3f} {Y(VY):.3f} m ' + ' '.join(arc(VX, VY, vr, a) for a in (0, 90, 180, 270)) + ' h'
    fn = DictionaryObject({NameObject('/FunctionType'): NumberObject(2), NameObject('/Domain'): ArrayObject([FloatObject(0), FloatObject(1)]),
                           NameObject('/C0'): ArrayObject([FloatObject(0)] * 4), NameObject('/N'): FloatObject(1),
                           NameObject('/C1'): ArrayObject([FloatObject(0), FloatObject(1), FloatObject(0), FloatObject(0)])})
    res = pg['/Resources']
    res.setdefault(NameObject('/ColorSpace'), DictionaryObject())[NameObject('/CSCut')] = \
        ArrayObject([NameObject('/Separation'), NameObject('/CutContour'), NameObject('/DeviceCMYK'), wr._add_object(fn)])
    res.setdefault(NameObject('/ExtGState'), DictionaryObject())[NameObject('/GSCut')] = DictionaryObject(
        {NameObject('/OP'): BooleanObject(True), NameObject('/op'): BooleanObject(True), NameObject('/OPM'): NumberObject(1)})
    pre, post = DecodedStreamObject(), DecodedStreamObject()
    pre.set_data(b'q\n'); post.set_data(f'Q\nq /GSCut gs /CSCut CS 1 SCN 0.5 w\n{outline} S\n{hole} S\nQ\n'.encode())
    old = pg['/Contents']; old = list(old) if isinstance(old, ArrayObject) else [old]
    pg[NameObject('/Contents')] = ArrayObject([wr._add_object(pre)] + [c.indirect_reference or wr._add_object(c) if hasattr(c, 'indirect_reference') else c for c in old] + [wr._add_object(post)])
    pg.trimbox = RectangleObject([X(0), Y(H), X(W), Y(0)]); pg.bleedbox = RectangleObject([0, 0, mw, mh])
    with open(pdf, 'wb') as f: wr.write(f)

if __name__ == '__main__':
    print(f'wrap {W:.2f} x {H:.2f} mm (perimeter {PER:.2f} + {LAP} lap), vent at ({VX:.2f}, {VY:.2f}), flats {[(round(a, 2), round(b, 2)) for a, b in L["flats"]]}')
    pw, ph = build(); rasterize(pw, ph)
