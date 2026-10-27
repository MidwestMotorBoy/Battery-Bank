"""Monolith wrap label: one printed vinyl rectangle round the whole cup, top and bottom edges under the TPU bumpers.
Spec: the "Cup label plan" doc (2026-10-27). The layout comes from the cup model (hardware/mechanical/monolith_cup.py):
the cup's outside is a prism, so the label is a flat rectangle, cup perimeter + LAP long, seam in the middle of the
back face, art running unbroken across the seam (the overlap repeats the first LAP mm).
Run: python monolith_label.py      (numpy, fonttools, manifold3d, cairosvg, pypdf)
-> out/monolith_label_print.pdf    send this: artwork with 2 mm bleed, all text as outlines, page = art + bleed exactly,
                                   TrimBox = the cut size, die line as a CutContour spot-colour stroke (overprint)
   out/monolith_label_stickerapp.pdf  the same for StickerApp: cut line = outer outline only, spot colour "die cut",
                                   1 pt, on its own layer (their custom-cutline rules)
   out/monolith_label_print.svg    the artwork alone
   out/monolith_label_trim.pdf     the artwork cut to size (R2 corners), no bleed or die line, for shops that make their
                                   own cut path from the artwork's outline (CarStickers)
   out/monolith_label_cut.svg      die line: outline (R2 corners) + vent hole, on the same page as the print file
   out/monolith_label_proof.png    art + die line + face folds, for checking
Run: python monolith_label.py --bl    the Borderlands-style version (brush inking, tapered hatching, cel tones, grit),
                                   written as out/monolith_label_bl_*  (also needs svgpathtools)
Label coordinates: mm, x along the wrap left to right as seen from outside with the ports up, y down from the label's
top edge. The fonts are OFL (fonts/)."""
import os, sys, math, zlib, numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
sys.path.insert(0, os.path.join(HERE, '..', 'mechanical'))

# ---------------- layout from the cup model ----------------
import monolith_cup as K
LAP, BLEED = 5.0, 2.0                # seam overlap, print bleed
BL = '--bl' in sys.argv              # Borderlands look: hand-inked brush outlines that swell and taper (heavier on the shadow
                                     # side), tapered hatching, lit edges and shadow faces (light from the upper left), ink grit
NAME = 'monolith_label_bl' if BL else 'monolith_label'
OW = 1.15 if BL else 1.0             # outer outline weight (the brush swells to about 1.45x at its fattest)
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
         word='#f6d061', word_sh='#b5372a', red='#b8322a', check='#3f8f4a',
         far_hi='#9fb2c3', hill_hi='#a2c462', pine_hi='#5d9a59', pine_hi_dk='#356640', mesa_hi='#f09d5c',
         sun_sh='#e6a234', ray_sh='#d0702c', word_hi='#fbeaa8', scrub_sh='#66763a')
if BL:                               # deeper, dustier shadows
    C.update(far_sh='#566a7c', hill_sh='#4d7231', pine_sh='#1f4429', mesa_sh='#8e3622', bear_sh='#4a2b14')

# ---------------- svg helpers ----------------
out = []
def add(s): out.append(s)
def pts(p): return ' '.join(f'{x:.3f},{y:.3f}' for x, y in p)
def poly(p, fill, sw=0.35, stroke=INK, extra=''):
    if BL and sw and stroke == INK and not _crisp[0]:
        if fill != 'none': add(f'<polygon points="{pts(p)}" fill="{fill}" stroke="none"{extra}/>')
        ink(list(p), sw, closed=True)
        return
    add(f'<polygon points="{pts(p)}" fill="{fill}" stroke="{stroke if sw else "none"}" stroke-width="{sw}" stroke-linejoin="round"{extra}/>')
def path(d, fill='none', sw=0.35, stroke=INK, extra=''):
    if BL and sw and stroke == INK and not _crisp[0]:
        if fill != 'none': add(f'<path d="{d}" fill="{fill}" stroke="none"{extra}/>')
        ink_d(d, sw)
        return
    add(f'<path d="{d}" fill="{fill}" stroke="{stroke if sw else "none"}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"{extra}/>')
_clip = [0]
_crisp = [False]                     # BL: draw plain strokes (text panels, icons)
def hatch(p, step=1.0, ang=45, sw=0.25):
    """ink hatching clipped to polygon p (the comic shadow)"""
    if BL: return hatch_ink(p, step, ang, sw)
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

# ---------------- brush inking (BL) ----------------
def _resample(q, step=0.2):
    q = np.asarray(q, float)
    s_ = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))])
    if s_[-1] < 1e-6: return q[:1]
    u = np.linspace(0, s_[-1], max(2, int(s_[-1] / step) + 1))
    return np.column_stack([np.interp(u, s_, q[:, 0]), np.interp(u, s_, q[:, 1])])
def _rng(*v):
    return np.random.default_rng(zlib.crc32(','.join(f'{x:.1f}' for x in v).encode()))
def _fmt(a): return ' '.join(f'{x:.2f},{y:.2f}' for x, y in a)
def _stroke(q, w, rng, t0=True, t1=True, wob=0.05, out=None, unit=1.0):
    """one brush stroke along polyline q: swells in the middle, tapers at the ends, wobbles a little, and (out = outward
    normal sign of a closed shape) gets heavier where it faces away from the light"""
    if len(q) < 2: return ''
    seg = np.linalg.norm(np.diff(q, axis=0), axis=1); s_ = np.concatenate([[0], np.cumsum(seg)]); L = s_[-1]
    if L < 1e-3: return ''
    tl = min(0.35 * L, 2.2 * unit)
    prof = np.ones(len(q))
    if t0: prof *= 0.12 + 0.88 * np.clip(s_ / tl, 0, 1) ** 0.7
    if t1: prof *= 0.12 + 0.88 * np.clip((L - s_) / tl, 0, 1) ** 0.7
    prof *= 1 + 0.22 * np.sin(2 * np.pi * s_ / (rng.uniform(3, 7) * unit) + rng.uniform(0, 6.3))
    tg = np.gradient(q, axis=0); tg /= np.maximum(np.linalg.norm(tg, axis=1), 1e-9)[:, None]
    n = np.column_stack([-tg[:, 1], tg[:, 0]])
    if out is not None:                                           # weight the shadow side (light from the upper left)
        prof *= 1 + 0.6 * np.clip(out * (n[:, 0] * 0.6 + n[:, 1] * 0.8), 0, 1)
    c = q + n * (wob * unit * np.sin(2 * np.pi * s_ / (rng.uniform(4, 9) * unit) + rng.uniform(0, 6.3)))[:, None]
    hw = (w * prof / 2)[:, None]
    return 'M' + _fmt(c + n * hw) + ' L' + _fmt((c - n * hw)[::-1]) + 'Z'
def ink(p, sw, closed=False, period=False, unit=1.0, raw=False):
    """hand-inked outline of polyline p (sw = the plain stroke width it replaces): broken into overlapping tapered strokes.
    period: a long line across the seam, broken at the same places every wrap period so both ends of the label match"""
    p = [tuple(map(float, v)) for v in p]
    if len(p) < 2: return ''
    w = sw * 1.45
    if closed: p = p + [p[0]]
    q = _resample(p, 0.2 * unit)
    if len(q) < 2: return ''
    rng = _rng(p[0][0] % PER, p[0][1], len(p), sw)
    d = ''
    if period:                                                    # break where x crosses fixed points of the period
        nb = 21; xb = lambda m: m * PER / nb + _rng(m % nb).uniform(-2, 2)
        m0 = math.floor(q[0][0] / (PER / nb)) - 1
        while xb(m0) < q[-1][0]:
            a, b = xb(m0) - 0.5, xb(m0 + 1) + 0.5
            sel = q[(q[:, 0] >= a) & (q[:, 0] <= b)]
            d += _stroke(sel, w, _rng(m0 % nb, 7), unit=unit); m0 += 1
    else:
        ss = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]); L = ss[-1]
        out = None
        if closed:
            A = sum(q[i][0] * q[i + 1][1] - q[i + 1][0] * q[i][1] for i in range(len(q) - 1))
            out = -1 if A > 0 else 1
        if L < 9 * unit and not closed:
            d = _stroke(q, w, rng, out=out, unit=unit)
        else:
            a = -rng.uniform(0, 3) * unit if closed else 0.0
            end = L + a if closed else L
            while a < end - 1e-6:
                b = a + rng.uniform(5, 11) * unit
                if b > end - 3 * unit: b = end
                lo, hi = a - 0.45 * unit, b + 0.45 * unit
                if closed:
                    u = np.arange(lo, hi, 0.2 * unit) % L
                    sel = np.column_stack([np.interp(u, ss, q[:, 0]), np.interp(u, ss, q[:, 1])])
                else:
                    sel = q[(ss >= max(lo, 0)) & (ss <= min(hi, L))]
                d += _stroke(sel, w, rng, t0=closed or a > 0, t1=closed or b < L, out=out, unit=unit)
                a = b
    if raw: return d
    if d: add(f'<path d="{d}" fill="{INK}"/>')
    return d
def _subpaths(d, step=0.2):
    from svgpathtools import parse_path
    res = []
    for sp in parse_path(d).continuous_subpaths():
        pts_ = []
        for seg in sp:
            n = max(2, int(seg.length(error=1e-3) / step) + 1)
            for t in np.linspace(0, 1, n)[(1 if pts_ else 0):]:
                z = seg.point(t); pts_.append((z.real, z.imag))
        res.append((pts_, sp.isclosed() and len(pts_) > 3))
    return res
def ink_d(d, sw, unit=1.0, raw=False):
    """hand-inked version of a stroked SVG path"""
    out_ = ''
    for p, closed in _subpaths(d, 0.2 * unit):
        if closed: p = p[:-1]
        out_ += ink(p, sw, closed=closed, unit=unit, raw=True)
    if raw: return out_
    if out_: add(f'<path d="{out_}" fill="{INK}"/>')
    return out_
def taper(a, b, w, rng, unit=1.0):
    """a single hatch stroke: full width at a, tapering to a point at b"""
    q = _resample([a, b], 0.2 * unit)
    return _stroke(q, w, rng, t0=False, t1=True, wob=0.02, unit=unit)
def hatch_ink(p, step=1.0, ang=45, sw=0.25, maxlen=5.0):
    """hand hatching: tapered strokes rising from the bottom of the shadow, of uneven length, clipped to polygon p"""
    _clip[0] += 1; cid = f'h{_clip[0]}'
    add(f'<clipPath id="{cid}"><polygon points="{pts(p)}"/></clipPath>')
    t = math.tan(math.radians(ang)); P = list(p) + [p[0]]
    cs = [x + y / t for x, y in p]
    d = ''
    for c in np.arange(math.floor(min(cs) / step) * step, max(cs), step):
        ys = []
        for (ax, ay), (bx, by) in zip(P[:-1], P[1:]):
            fa, fb = ax + ay / t - c, bx + by / t - c
            if (fa < 0) != (fb < 0):
                u = fa / (fa - fb); ys.append(ay + u * (by - ay))
        ys.sort()
        rng = _rng(c % PER, ang, step)
        for y0, y1 in zip(ys[::2], ys[1::2]):                     # inside intervals, y0 above y1
            if y1 - y0 < 0.3: continue
            k = rng.uniform(0.45, 1.0) if rng.random() < 0.7 else rng.uniform(0.2, 0.5)
            ya = y1 + 0.3; yt = y1 - min(k * (y1 - y0), maxlen * rng.uniform(0.6, 1.0) * math.sin(math.radians(ang)))
            d += taper((c - ya / t, ya), (c - yt / t + rng.uniform(-0.15, 0.15), yt), sw * 2.3, rng)
    if d: add(f'<g clip-path="url(#{cid})"><path d="{d}" fill="{INK}"/></g>')
def grit(p, n, rng, dash=(0.3, 1.0), w=0.22, ang=(15, 40), clip_d=None):
    """ink grit inside polygon p (or the path clip_d): specks and short tapered scratches"""
    _clip[0] += 1; cid = f'g{_clip[0]}'
    add(f'<clipPath id="{cid}">' + (f'<path d="{clip_d}"/>' if clip_d else f'<polygon points="{pts(p)}"/>') + '</clipPath>')
    xs, ys = [q[0] for q in p], [q[1] for q in p]
    d, dots = '', ''
    for _ in range(n):
        x, y = rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys))
        if rng.random() < 0.45:
            dots += f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{rng.uniform(0.07, 0.16):.2f}"/>'
        else:
            L, a = rng.uniform(*dash), math.radians(rng.uniform(*ang))
            d += taper((x, y), (x + L * math.cos(a), y + L * math.sin(a)), w, rng)
    add(f'<g clip-path="url(#{cid})" fill="{INK}"><path d="{d}"/>{dots}</g>')

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
def text(s, font, cap, x, y, anchor='l', fill=INK, track=0.0, stroke=None, sw=0.0, fit=None, hi=None):
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
    if hi:                                             # cel: a hard lit band across the tops of the letters
        _clip[0] += 1; cid = f't{_clip[0]}'
        add(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        add(f'<rect x="{x - w - 1:.3f}" y="{y - cap * 1.3:.3f}" width="{3 * w + 2:.3f}" height="{cap * 0.62:.3f}" fill="{hi}" clip-path="url(#{cid})"/>')
    return w

# ---------------- scene pieces ----------------
def cloud(x, y, s):
    lobes = [(-3.2, 0.6, 2.0), (-1.2, -0.6, 2.6), (1.4, -0.2, 2.3), (3.4, 0.7, 1.7)]
    if BL:                                          # one outline round the whole cloud, shadowed underside, lit tops
        _clip[0] += 1; cid = f'c{_clip[0]}'
        circ = lambda f, dx=0.0, dy=0.0, k=1.0, extra='': ''.join(
            f'<circle cx="{x + (a + dx) * s:.2f}" cy="{y + (b + dy) * s:.2f}" r="{r * k * s:.2f}" fill="{f}"{extra}/>' for a, b, r in lobes)
        bot = y + 2.3 * s
        from manifold3d import CrossSection as CS                 # the cloud's silhouette: lobes cut flat at the bottom
        u = CS.square((16 * s, bot - y + 6 * s)).translate((x - 8 * s, y - 6 * s))
        sil = sum((CS.circle(r * s, 48).translate((x + a * s, y + b * s)) for a, b, r in lobes[1:]),
                  CS.circle(lobes[0][2] * s, 48).translate((x + lobes[0][0] * s, y + lobes[0][1] * s))) ^ u
        rings = [[tuple(v) for v in r_] for r_ in sil.to_polygons()]
        add(f'<clipPath id="{cid}">' + ''.join(f'<polygon points="{pts(r_)}"/>' for r_ in rings) + '</clipPath>')
        add(f'<g clip-path="url(#{cid})">' + circ(C['cloud_sh']) + circ(C['cloud'], -0.35, -0.55, 0.92) + '</g>')
        for r_ in rings: ink(r_, 0.4, closed=True)
        return
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
        if BL:                                      # lit sliver down the left edge
            poly([(x, ytop), (x - hw, ybot), (x - hw * 0.62, ybot - h * 0.05), (x - hw * 0.12, ytop + (ybot - ytop) * 0.4)],
                 C['pine_hi_dk'] if dark else C['pine_hi'], 0)
        poly(tier, 'none', 0.2 if BL else 0.3)

def scrub(x, yb, s):
    for dx, r in ((-1.0, 1.1), (0.2, 1.5), (1.4, 1.0)):
        if BL:
            add(f'<circle cx="{x + dx * s:.2f}" cy="{yb - r * s * 0.8:.2f}" r="{r * s:.2f}" fill="{C["scrub_sh"]}" stroke="{INK}" stroke-width="0.32"/>')
            add(f'<circle cx="{x + (dx - 0.25 * r) * s:.2f}" cy="{yb - r * s * 1.05:.2f}" r="{r * s * 0.68:.2f}" fill="#8a9a52"/>')
            continue
        add(f'<circle cx="{x + dx * s:.2f}" cy="{yb - r * s * 0.8:.2f}" r="{r * s:.2f}" fill="#8a9a52" stroke="{INK}" stroke-width="0.28"/>')

def bear(x, yb, s=1.0):
    """walking grizzly facing right, about 17.1 mm rump to nose at s = 1, feet on yb: long body, high shoulder hump, head
    held low and forward with a long snout, shaggy fringe under the belly and down the legs, a lit back, grizzled hump"""
    g = f'<g transform="translate({x:.3f} {yb:.3f}) scale({s:.4f})">'
    w = lambda v: v / s                                            # stroke widths stay in mm
    fringe = lambda x0, x1, y, n: ''.join(f'L{x0 + (x1 - x0) * (k + 0.5) / n:.2f} {y + (0.45 if k % 2 == 0 else 0.0):.2f}'
                                          for k in range(n))      # shaggy belly: zigzag from x0 to x1 (right to left)
    body = ('M0.5 0 C0.1 -1.0 0.0 -2.6 0.2 -4.0 C0.35 -5.6 0.6 -7.1 1.2 -7.9 C1.8 -8.6 2.8 -8.9 3.9 -9.0 '      # rump
            'C5.3 -9.1 6.6 -9.15 7.8 -9.4 C8.9 -9.65 9.6 -10.6 10.6 -11.0 C11.3 -11.25 12.0 -11.0 12.5 -10.5 '    # back, hump
            'C12.8 -10.2 13.0 -9.95 13.4 -9.95 C14.0 -10.1 14.7 -9.95 15.1 -9.6 C15.4 -9.35 15.6 -9.1 15.9 -8.9 '  # neck, head
            'C16.4 -8.6 16.9 -8.0 17.25 -7.55 C17.45 -7.25 17.4 -6.95 17.1 -6.8 '                                  # snout, nose
            'C16.6 -6.6 16.0 -6.45 15.4 -6.35 C15.0 -6.25 14.6 -6.0 14.3 -5.7 '                                    # chin, jaw
            'L13.85 -5.3 L14.0 -5.0 L13.5 -4.75 L13.65 -4.4 L13.25 -4.1 '                                          # throat ruff
            'C13.2 -3.4 13.3 -2.6 13.4 -2.0 C13.5 -1.2 13.6 -0.6 13.8 -0.35 C14.3 -0.3 14.8 -0.2 14.8 0 L12.6 0 '  # near fore leg
            'C12.5 -0.7 12.4 -1.4 12.2 -2.0 L11.9 -1.75 L11.8 -2.3 '
            + fringe(11.8, 2.9, -2.75, 14) +
            'L2.9 -2.3 C2.75 -1.6 2.65 -0.9 2.75 -0.35 C3.1 -0.3 3.3 -0.15 3.2 0 Z')                               # near hind leg
    far = ('M4.3 -3.2 C4.6 -2.1 4.7 -1.0 4.5 -0.35 C4.6 -0.2 4.8 0 5.1 0 L6.4 0 C6.2 -1.0 6.2 -2.1 6.5 -3.1 Z '      # far hind leg
           'M9.7 -3.4 C9.9 -2.2 9.8 -1.0 9.6 -0.35 C9.7 -0.15 9.9 0 10.2 0 L11.6 0 C11.4 -1.0 11.4 -2.2 11.7 -3.4 Z')  # far fore leg
    add(g)
    add(f'<path d="{far}" fill="{C["bear_sh"]}" stroke="{INK if not BL else "none"}" stroke-width="{w(0.4):.3f}" stroke-linejoin="round"/>')
    if BL: ink_d(far, w(0.3), unit=1 / s)
    add(f'<circle cx="13.75" cy="-10.15" r="0.48" fill="{C["bear_sh"]}" stroke="{INK}" stroke-width="{w(0.35):.3f}"/>')   # far ear
    add(f'<circle cx="14.35" cy="-10.0" r="0.58" fill="{C["bear"]}" stroke="{INK}" stroke-width="{w(0.35):.3f}"/>')     # near ear
    add(f'<circle cx="14.4" cy="-9.95" r="0.29" fill="{C["bear_sh"]}"/>')
    _clip[0] += 1; cid = f'b{_clip[0]}'
    add(f'<clipPath id="{cid}"><path d="{body}"/></clipPath>')
    add(f'<path d="{body}" fill="{C["bear"]}"/>')
    add(f'<g clip-path="url(#{cid})">')
    # shadow under the belly and down the legs, then hatching
    add(f'<path d="M-1 -4.3 C3 -4.7 8 -4.8 12.6 -4.4 L14 -4.4 L14 1 L-1 1 Z" fill="{C["bear_sh"]}"/>')
    if BL:
        r = _rng(3, 3)
        hl = ''.join(taper((k, 0.5), (k + 2.4 * f, 0.5 - 4.9 * f), w(0.4), r, unit=1 / s)
                     for k in np.arange(-2.5, 15, 0.8) for f in [r.uniform(0.55, 1.0)])
        add(f'<path d="{hl}" fill="{INK}"/>')
    else:
        hl = ''.join(f'M{k:.2f} 0.5L{k + 2.4:.2f} -4.4' for k in np.arange(-2.5, 15, 0.95))
        add(f'<path d="{hl}" stroke="{INK}" stroke-width="{w(0.25):.3f}" fill="none"/>')
    add(f'<ellipse cx="16.6" cy="-7.45" rx="1.1" ry="0.6" transform="rotate(35 16.6 -7.45)" fill="#b9814b"/>')   # pale muzzle
    add(f'<path d="M2.1 -8.5 C3.3 -8.65 5.3 -8.7 7.8 -9.0 C8.9 -9.25 9.6 -10.15 10.6 -10.55 C11.2 -10.75 11.7 -10.65 12.0 -10.4" '
        f'fill="none" stroke="#c58a52" stroke-width="{w(0.5):.3f}" stroke-linecap="round"/>')         # light along the back
    add(f'<path d="M9.7 -9.9q0.4 0.6 1.0 0.5M10.8 -10.45q0.4 0.6 1.0 0.5M11.7 -10.1q0.3 0.6 0.9 0.6M10.4 -9.2q0.4 0.6 1.0 0.5" '
        f'fill="none" stroke="#d9a46c" stroke-width="{w(0.3):.3f}" stroke-linecap="round"/>')          # grizzled tips on the hump
    add('</g>')
    if BL: ink_d(body, w(0.42), unit=1 / s)
    else: add(f'<path d="{body}" fill="none" stroke="{INK}" stroke-width="{w(0.55 * OW):.3f}" stroke-linejoin="round"/>')
    fur = ('M11.9 -10.0C12.5 -8.2 12.6 -5.9 12.6 -3.6'          # shoulder under the hump
           'M13.3 -9.7C13.5 -8.5 13.7 -7.2 14.1 -6.1'         # neck ruff
           'M2.7 -7.6C3.4 -6.3 3.6 -4.6 3.25 -3.1'             # haunch
           'M1.0 -5.2l0.5 0.3M6.0 -8.6l0.6 0.2')
    if BL: ink_d(fur, w(0.2), unit=1 / s)
    else: add(f'<path d="{fur}" fill="none" stroke="{INK}" stroke-width="{w(0.25):.3f}" stroke-linecap="round" stroke-linejoin="round"/>')
    add(f'<path d="M16.8 -6.95 C16.4 -6.8 16.0 -6.75 15.7 -6.7" fill="none" stroke="{INK}" stroke-width="{w(0.25):.3f}" stroke-linecap="round"/>')  # mouth
    add(f'<circle cx="15.55" cy="-8.75" r="0.28" fill="{INK}"/><circle cx="15.62" cy="-8.82" r="0.09" fill="{C["cream"]}"/>')
    add(f'<ellipse cx="17.2" cy="-7.3" rx="0.36" ry="0.3" fill="{INK}"/>')                       # nose
    claws = ''.join(f'M{cx + k * 0.38:.2f} -0.05 q0.3 -0.05 0.36 -0.4' for cx in (13.95, 2.15) for k in range(3))
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
    area = lambda p: sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(p, p[1:] + p[:1]))
    holes = [h if area(h) * area(outline) < 0 else h[::-1] for h in holes]   # wound against the outline, so the hole
    d = ring(outline) + ''.join(ring(h) for h in holes)                      # stays open under nonzero clipping too
    _clip[0] += 1; cid = f'r{_clip[0]}'
    add(f'<clipPath id="{cid}"><path d="{d}" clip-rule="evenodd"/></clipPath>')
    path(d, C['mesa_hi'] if BL else C['mesa'], 0, extra=' fill-rule="evenodd"')
    add(f'<g clip-path="url(#{cid})">')
    if BL:                                          # the shape again, nudged down-right: leaves a lit edge on every face
        add(f'<g transform="translate(0.8 0.5)">'); path(d, C['mesa'], 0, extra=' fill-rule="evenodd"'); add('</g>')
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
    if BL:                                           # pits and scratches, thicker in the shadow
        grit(sh(outline), int((xb - xa) * 3.2), rng, dash=(0.3, 0.9), ang=(70, 100), clip_d=d)
        grit(sh(shade), int((xb - xa) * 2.0), rng, dash=(0.4, 1.4), ang=(60, 80), w=0.3)
    add('</g>')
    path(d, 'none', 0.55 * OW)

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

BEAR = [None]                                 # bear_options.py swaps in other bears here
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
    if BL:
        poly(mound[13:] + [(a + 0.8, b + 2.4) for a, b in reversed(mound[13:])], C['hill_sh'], 0)
        poly(mound[2:12] + [(a, b + 0.7 * math.sin(math.pi * k / 9)) for k, (a, b) in reversed(list(enumerate(mound[2:12])))], C['hill_hi'], 0)
    path('M' + ' L'.join(f'{a:.2f} {b:.2f}' for a, b in mound[2:-2]), sw=0.5 * OW)
    for k in range(5):
        poly(blob(x - 1.6 + k * 2.2 + rng.uniform(-0.3, 0.3), yb + 0.4 + rng.uniform(-0.2, 0.6), rng.uniform(0.35, 0.6), rng), '#8a5a35', 0.25)

def birds(pts_):
    for bx, by, r in pts_:
        path(f'M{bx - r:.2f} {by - r * 0.35:.2f}q{r * 0.5:.2f} {-r * 0.45:.2f} {r:.2f} {r * 0.35:.2f}q{r * 0.5:.2f} {-r * 0.8:.2f} {r:.2f} {-r * 0.35:.2f}', sw=0.35)

def bin_icon(cx, cy, h):
    """crossed-out wheelie bin (EN 50419: don't put in household waste), with the bar under it, h tall, centred on (cx, cy)"""
    k = h / 12.4; T = lambda u, v: (cx + u * k, cy + v * k)
    poly([T(-2.4, -4.0), T(2.4, -4.0), T(2.0, 3.4), T(-2.0, 3.4)], C['cream'], 0.32)                  # body
    poly([T(-3.1, -4.7), T(3.1, -4.7), T(3.1, -4.0), T(-3.1, -4.0)], INK, 0)                           # lid
    poly([T(-1.0, -5.3), T(1.0, -5.3), T(1.0, -4.7), T(-1.0, -4.7)], INK, 0)                           # handle
    wx, wy = T(1.7, 3.9); add(f'<circle cx="{wx:.3f}" cy="{wy:.3f}" r="{0.85 * k:.3f}" fill="{C["cream"]}" stroke="{INK}" stroke-width="0.3"/>')
    for a, b in ((T(-3.6, -5.8), T(3.6, 5.0)), (T(3.6, -5.8), T(-3.6, 5.0))):                          # the cross
        path(f'M{a[0]:.3f} {a[1]:.3f}L{b[0]:.3f} {b[1]:.3f}', sw=0.4)
    poly([T(-3.6, 5.7), T(3.6, 5.7), T(3.6, 6.9), T(-3.6, 6.9)], INK, 0)                               # bar

def recycle_icon(cx, cy, h):
    """three chasing arrows round a triangle (recycle), "Li-ion" under it; h = arrows height, centred on (cx, cy)"""
    r = h * 0.62                                                     # triangle corner radius
    cn = [(cx + r * math.cos(math.radians(a)), cy + 0.12 * h + r * math.sin(math.radians(a))) for a in (-90, 30, 150)]
    for i in range(3):
        (ax, ay), (bx, by) = cn[i], cn[(i + 1) % 3]
        ux, uy = bx - ax, by - ay; L = math.hypot(ux, uy); ux, uy = ux / L, uy / L
        s0, s1 = 0.2 * L, 0.72 * L                                   # band along the side, gap at each corner
        x0, y0, x1, y1 = ax + ux * s0, ay + uy * s0, ax + ux * s1, ay + uy * s1
        path(f'M{x0:.3f} {y0:.3f}L{x1:.3f} {y1:.3f}', sw=0.16 * h)
        hw, hl = 0.17 * h, 0.24 * h; nx, ny = -uy, ux                # arrowhead
        poly([(x1 + nx * hw, y1 + ny * hw), (x1 + ux * hl, y1 + uy * hl), (x1 - nx * hw, y1 - ny * hw)], INK, 0)

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
    _crisp[0] = False; poly(p, C['cream'], 0.35 if BL else 0.5); _crisp[0] = True

def facets(ridge, sh, ybot, hatched=None, hi=None, depth=None, hi_w=1.1, smooth=0):
    """cel shadow on the slopes of a ridge line that fall away to the right (light from the left all round, so it repeats
    at the seam); hi: a lit band under the slopes that face the light. depth: shadow band depth (None = down to ybot);
    smooth: half-window (samples) for finding the slopes, so small bumps don't break up a big facet"""
    ry = [y for _, y in ridge]
    sy = [sum(ry[max(0, n - smooth):n + smooth + 1]) / len(ry[max(0, n - smooth):n + smooth + 1]) for n in range(len(ry))]
    def flush(run, down):
        if len(run) < 2 or run[-1][0] - run[0][0] <= 1.0: return
        if down:                                                    # a facet: down the slope, back up a slanted edge
            if depth is None and BL:                               # a face: peak spine and valley edge meet at an apex
                (xp, yp), (xv, yv) = run[0], run[-1]
                ya = min(ybot, (xv - xp + 0.25 * yp - 0.05 * yv) / 0.2)
                sp = run + [(xv + 0.05 * (ya - yv), ya), (xp + 0.25 * (ya - yp), ya)]
            elif depth is None:
                (xp, yp), (xv, yv) = run[0], run[-1]
                sp = run + [(xv + 0.2 * (ybot - yv), ybot), (xp + 0.45 * (ybot - yp), ybot)]
            else:
                sp = run + [(a + 0.35 * depth, b + depth) for a, b in reversed(run)]
            poly(sp, sh, 0)
            if hatched: hatch(sp, step=hatched[0], ang=hatched[1], sw=0.25)
        elif hi:                                                    # lit band, pointed at both ends
            n = len(run)
            band = run + [(a, b + hi_w * min(1.0, 4 * min(k, n - 1 - k) / (n - 1))) for k, (a, b) in reversed(list(enumerate(run)))]
            poly(band, hi, 0)
    run, mode = [], None
    for n in range(len(ridge) - 1):
        dy = sy[n + 1] - sy[n]
        m = True if dy > 0.05 else False if dy < -0.05 else None
        if m != mode:
            if run: flush(run + [ridge[n]], mode)
            run, mode = [], m
        if m is not None: run.append(ridge[n])
    if run: flush(run + [ridge[-1]], mode)

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
    facets(ridge, C['far_sh'], Y1 + 1, hatched=(1.4, 35), hi=C['far_hi'] if BL else None, smooth=12 if BL else 0)
    if BL:
        ink(ridge, 0.4, period=True)
        for m in range(-3, int(PER / 2.9) + 3):                    # crags: tapered ink strokes down the faces
            xc = m * 2.9
            for xx in (xc - PER, xc, xc + PER):
                if not X0 - 3 < xx < X1 + 3: continue
                r = _rng(m % int(PER / 2.9), 31); yy = wave(xx, 33.5, terms) + (32 * (0.5 + 0.5 * math.cos(math.pi * sun_d(xx) / 30)) if sun_d(xx) < 30 else 0)
                if yy > 52 or r.random() < 0.35: continue
                L = r.uniform(2.0, 6.0); a = math.radians(r.uniform(60, 80))
                add(f'<path d="{taper((xx, yy + 0.3), (xx + L * math.cos(a), yy + 0.3 + L * math.sin(a)), 0.4, r)}" fill="{INK}"/>')
        far_poly = ridge + [(X1 + 1, 62), (X0 - 1, 62)]
        grit(far_poly, 260, _rng(41))
    else:
        path('M' + ' L'.join(f'{x:.2f} {y:.2f}' for x, y in ridge), sw=0.3 * OW)
    ys = [y for _, y in ridge]
    for n in range(6, len(ridge) - 6):
        x, y = ridge[n]
        if y < 35 and y <= min(ys[n - 6:n + 7]):
            cap = [(x - 2.6, y + 2.2), (x - 1.3, y + 1.0), (x, y), (x + 1.4, y + 1.1), (x + 2.8, y + 2.4), (x + 1.6, y + 2.0),
                   (x + 0.9, y + 2.9), (x + 0.1, y + 2.0), (x - 0.9, y + 2.9), (x - 1.6, y + 2.0)]
            poly(cap, C['snow'], 0.3)
            if BL:
                poly([(x, y), (x + 1.4, y + 1.1), (x + 2.8, y + 2.4), (x + 1.6, y + 2.0), (x + 0.9, y + 2.9), (x + 0.5, y + 1.4)], C['snow_sh'], 0)
                poly(cap, 'none', 0.3)
    # sun over the board face: the vent hole is its core
    for i in range(16):
        a0 = 2 * math.pi * i / 16; a1 = a0 + 2 * math.pi / 32
        if math.sin((a0 + a1) / 2) > 0.2: continue                 # under the hills anyway
        r0, r1 = VENT_HOLE_D / 2 + 2.6, VENT_HOLE_D / 2 + (7.0 if i % 2 == 0 else 4.5)
        poly([(VX + r0 * math.cos(a0), VY + r0 * math.sin(a0)), (VX + r1 * math.cos((a0 + a1) / 2), VY + r1 * math.sin((a0 + a1) / 2)),
              (VX + r0 * math.cos(a1), VY + r0 * math.sin(a1))], C['sun_ray'], 0.3)
        if BL:                                                    # shadow half of each ray
            am = (a0 + a1) / 2
            poly([(VX + r0 * math.cos(am), VY + r0 * math.sin(am)), (VX + r1 * math.cos(am), VY + r1 * math.sin(am)),
                  (VX + r0 * math.cos(a1), VY + r0 * math.sin(a1))], C['ray_sh'], 0)
            poly([(VX + r0 * math.cos(a0), VY + r0 * math.sin(a0)), (VX + r1 * math.cos(am), VY + r1 * math.sin(am)),
                  (VX + r0 * math.cos(a1), VY + r0 * math.sin(a1))], 'none', 0.3)
    rs = VENT_HOLE_D / 2 + 2.6
    add(f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{rs:.3f}" fill="{C["sun"]}" stroke="{INK if not BL else "none"}" stroke-width="{0.45 * OW:.2f}"/>')
    if BL:                                                        # shadowed lower right of the disc
        r = VENT_HOLE_D / 2 + 2.6 - 0.15 * OW; a0, a1 = math.radians(-30), math.radians(120)
        add(f'<path d="M{VX + r * math.cos(a0):.3f} {VY + r * math.sin(a0):.3f}A{r:.3f} {r:.3f} 0 0 1 {VX + r * math.cos(a1):.3f} {VY + r * math.sin(a1):.3f}'
            f'A{r * 1.35:.3f} {r * 1.35:.3f} 0 0 0 {VX + r * math.cos(a0):.3f} {VY + r * math.sin(a0):.3f}Z" fill="{C["sun_sh"]}"/>')
        ink([(VX + rs * math.cos(a), VY + rs * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 120, endpoint=False)], 0.45 * OW, closed=True)
    add(f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2 + 1.2:.3f}" fill="none" stroke="{C["sun_ray"]}" stroke-width="0.4"/>')
    b0, b1 = SIDE_B
    # canyon country on side B: a spire, a mitten butte and an arch, standing on talus slopes
    for k, (outline, holes, shade, cap_y, strata, talus_y) in enumerate(CANYON): rock(b0, outline, holes, shade, cap_y, strata, talus_y, 20 + k)
    # desert floor under the rocks
    floor = [(b0 - 6, 60), (b0 + 6, 58.5), (b1 - 6, 59.5), (b1 + 4, 61), (b1 + 4, H + 2), (b0 - 6, H + 2)]
    poly(floor, C['sand'], 0.35)
    if BL: grit(floor, 90, _rng(61), dash=(0.4, 1.2), ang=(-5, 5))
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
    poly(hill_poly, C['hill'], 0 if BL else 0.5 * OW)
    if BL:
        facets(hills, C['hill_sh'], Y1 + 1, hi=C['hill_hi'], depth=3.2, hi_w=0.9)
        ink(hills, 0.5 * OW, period=True)
        hy = dict((round(x, 1), y) for x, y in hills)
        tufts = ''
        for m in range(int(PER / 1.7)):                            # grass tufts
            r = _rng(m, 53)
            for xx in (m * 1.7 + r.uniform(-0.5, 0.5) + k * PER for k in (-1, 0, 1)):
                if not X0 < xx < X1: continue
                yb = wave(xx, 54.0, hterms) + r.uniform(1.6, 9.0)
                if sun_d(xx) < 22 or (b0 - 14 < xx < b1 + 14): continue
                for dx, a in ((-0.25, -115), (0.0, -92), (0.25, -68)):
                    L = r.uniform(0.6, 1.0)
                    tufts += taper((xx + dx, yb), (xx + dx + L * math.cos(math.radians(a)), yb + L * math.sin(math.radians(a))), 0.28, r)
        add(f'<path d="{tufts}" fill="{INK}"/>')
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
    if BL:
        poly(mound[17:] + [(a + 1.0, b + 3.0) for a, b in reversed(mound[17:])], C['hill_sh'], 0)
        poly(mound[2:16] + [(a, b + 0.8 * math.sin(math.pi * k / 13)) for k, (a, b) in reversed(list(enumerate(mound[2:16])))], C['hill_hi'], 0)
    path('M' + ' L'.join(f'{a:.2f} {b:.2f}' for a, b in mound[3:-3]), sw=0.5 * OW)
    if BL:                                                        # the bear's shadow on the grass
        add(f'<ellipse cx="{b1 + 1.0 + 8.6 * 1.26:.2f}" cy="65.4" rx="{8.8 * 1.26:.2f}" ry="0.75" fill="{C["hill_sh"]}"/>')
    (BEAR[0] or bear)(b1 + 1.0, 65.3, 1.26)
    # a few pines in front of the bear's meadow edge
    for x, h in ((b1 + 27.5, 15), (b1 + 30.0, 19)): rep(pine, x, 70.5, h, h * 0.42, False)

def panels():
    _crisp[0] = BL                                    # BL: brush only the caption boxes and banner; text and icons stay crisp
    # board face: wordmark and tagline banner
    xa, xb = BOARD; cx = (xa + xb) / 2; inner = xb - xa - 4.0
    wy = 14.6                                         # wordmark: stacked red shadow, heavy outline
    text('MONOLITH', BANG, 9.0, cx + 1.2, wy + 1.2, 'c', fill=C['word_sh'], track=0.1, fit=inner, stroke=INK, sw=1.4)
    for o in (0.9, 0.6, 0.3): text('MONOLITH', BANG, 9.0, cx + o, wy + o, 'c', fill=C['word_sh'], track=0.1, fit=inner)
    text('MONOLITH', BANG, 9.0, cx, wy, 'c', fill=C['word'], track=0.1, fit=inner, stroke=INK, sw=0.8, hi=C['word_hi'] if BL else None)
    by0, by1 = 17.4, 26.6
    rib = [(xa + 2.0, by0), (xb - 2.0, by0 + 0.4), (xb - 2.4, by1), (xa + 2.3, by1 - 0.3)]
    _crisp[0] = False
    poly([(xa + 0.6, by0 + 1.5), (xa + 2.0, by0 + 1.0), (xa + 2.3, by1 - 0.3), (xa + 0.6, by1 + 0.4), (xa + 1.5, (by0 + by1) / 2 + 0.8)], '#cdbb8e', 0.35)
    poly([(xb + 0.4, by0 + 1.9), (xb - 2.0, by0 + 1.4), (xb - 2.4, by1), (xb + 0.4, by1 + 0.6), (xb - 0.5, (by0 + by1) / 2 + 1.2)], '#cdbb8e', 0.35)
    _crisp[0] = False; poly(rib, C['banner'], 0.35 if BL else 0.45); _crisp[0] = BL
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
    caption(x0, VIS0 + 2.0, x1 - 0.8, VIS0 + 21.2)
    cxB = (x0 + x1 - 0.8) / 2; wB = x1 - x0 - 3.6
    text('WARNING', XB, 2.6, cxB, VIS0 + 6.4, 'c', fill=C['red'], track=0.2)
    for i, ln in enumerate(('Do not crush, puncture or burn.', 'Keep below 60 °C.')):
        text(ln, SEMI, 2.1, cxB, VIS0 + 9.9 + i * 2.9, 'c', fit=wB)
    iy = VIS0 + 16.2                                  # recycle it, don't bin it: the two marks instead of words
    bin_icon(cxB - 4.4, iy, 5.6)
    recycle_icon(cxB + 2.6, iy - 0.9, 3.6)
    text('Li-ion', BOLD, 1.6, cxB + 2.6, iy + 3.0, 'c')
    _crisp[0] = False

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
    with open(os.path.join(OUT, NAME + '_print.svg'), 'w') as f: f.write(svg(art, pw, ph, -BLEED, -BLEED))
    with open(os.path.join(OUT, NAME + '_cut.svg'), 'w') as f: f.write(svg(cut_lines(), pw, ph, -BLEED, -BLEED))
    hole = [f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2:.3f}" fill="#ffffff"/>']
    with open(os.path.join(OUT, NAME + '_proof.svg'), 'w') as f: f.write(svg(art + hole + cut_lines(sw=0.25) + folds(), pw, ph, -BLEED, -BLEED))
    # the cut-to-size art, hole knocked out, for the cup preview
    clip = (f'<clipPath id="cut"><rect x="0" y="0" width="{W:.3f}" height="{H:.3f}" rx="2"/></clipPath>')
    with open(os.path.join(OUT, NAME + '_cut_art.svg'), 'w') as f:
        f.write(svg([clip, '<g clip-path="url(#cut)">'] + art + ['</g>'] +
                    [f'<circle cx="{VX:.3f}" cy="{VY:.3f}" r="{VENT_HOLE_D / 2:.3f}" fill="#00ff00"/>'], W, H))
    with open(os.path.join(OUT, NAME + '_trim.svg'), 'w') as f:      # cut to size, transparent outside the R2 outline
        f.write(svg([clip, '<g clip-path="url(#cut)">'] + art + ['</g>'], W, H))
    return pw, ph

def rasterize(pw, ph, dpmm=24):
    """PNGs and the print PDF through cairosvg (exact page size: Chromium rounds PDF pages to 1/100 in)"""
    import cairosvg
    for name, w, h in ((NAME + '_proof', pw, ph), (NAME + '_cut_art', W, H)):
        cairosvg.svg2png(url=os.path.join(OUT, name + '.svg'), write_to=os.path.join(OUT, name + '.png'),
                         output_width=round(w * dpmm), output_height=round(h * dpmm), background_color='white')
    base = os.path.join(OUT, '_print_base.pdf')
    cairosvg.svg2pdf(url=os.path.join(OUT, NAME + '_print.svg'), write_to=base)
    add_cut_contour(base, os.path.join(OUT, NAME + '_print.pdf'), pw, ph)
    add_cut_contour(base, os.path.join(OUT, NAME + '_stickerapp.pdf'), pw, ph, spot='die cut', hole=False, width=1.0, layer='die cut')
    os.remove(base)
    cairosvg.svg2pdf(url=os.path.join(OUT, NAME + '_trim.svg'), write_to=os.path.join(OUT, NAME + '_trim.pdf'))

def add_cut_contour(src, dst, pw, ph, r=2.0, spot='CutContour', hole=True, width=0.5, layer=None):
    """copy the print PDF with the die line added as a stroke in a spot colour (100 % magenta alternate, overprint, width
    in pt), optionally on its own layer, and TrimBox = cut size, BleedBox = page"""
    import pypdf
    from pypdf.generic import (NameObject, ArrayObject, DictionaryObject, FloatObject, NumberObject, BooleanObject, DecodedStreamObject,
                               RectangleObject, TextStringObject)
    pt = 72 / 25.4; rd = pypdf.PdfReader(src); wr = pypdf.PdfWriter(); pg = wr.add_page(rd.pages[0])
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
    circle = f'{X(VX + vr):.3f} {Y(VY):.3f} m ' + ' '.join(arc(VX, VY, vr, a) for a in (0, 90, 180, 270)) + ' h'
    fn = DictionaryObject({NameObject('/FunctionType'): NumberObject(2), NameObject('/Domain'): ArrayObject([FloatObject(0), FloatObject(1)]),
                           NameObject('/C0'): ArrayObject([FloatObject(0)] * 4), NameObject('/N'): FloatObject(1),
                           NameObject('/C1'): ArrayObject([FloatObject(0), FloatObject(1), FloatObject(0), FloatObject(0)])})
    res = pg['/Resources']
    res.setdefault(NameObject('/ColorSpace'), DictionaryObject())[NameObject('/CSCut')] = \
        ArrayObject([NameObject('/Separation'), NameObject('/' + spot), NameObject('/DeviceCMYK'), wr._add_object(fn)])
    res.setdefault(NameObject('/ExtGState'), DictionaryObject())[NameObject('/GSCut')] = DictionaryObject(
        {NameObject('/OP'): BooleanObject(True), NameObject('/op'): BooleanObject(True), NameObject('/OPM'): NumberObject(1)})
    pre, post = DecodedStreamObject(), DecodedStreamObject()
    cut = f'q /GSCut gs /CSCut CS 1 SCN {width:g} w\n{outline} S\n' + (f'{circle} S\n' if hole else '') + 'Q\n'
    if layer:                                                       # optional content group = a layer in Illustrator / Acrobat
        ocg = wr._add_object(DictionaryObject({NameObject('/Type'): NameObject('/OCG'), NameObject('/Name'): TextStringObject(layer)}))
        res.setdefault(NameObject('/Properties'), DictionaryObject())[NameObject('/OCcut')] = ocg
        wr._root_object[NameObject('/OCProperties')] = DictionaryObject({NameObject('/OCGs'): ArrayObject([ocg]),
            NameObject('/D'): DictionaryObject({NameObject('/ON'): ArrayObject([ocg]), NameObject('/Order'): ArrayObject([ocg])})})
        cut = f'/OC /OCcut BDC\n{cut}EMC\n'
    pre.set_data(b'q\n'); post.set_data(f'Q\n{cut}'.encode())
    old = pg['/Contents']; old = list(old) if isinstance(old, ArrayObject) else [old]
    pg[NameObject('/Contents')] = ArrayObject([wr._add_object(pre)] + [c.indirect_reference or wr._add_object(c) if hasattr(c, 'indirect_reference') else c for c in old] + [wr._add_object(post)])
    pg.trimbox = RectangleObject([X(0), Y(H), X(W), Y(0)]); pg.bleedbox = RectangleObject([0, 0, mw, mh])
    with open(dst, 'wb') as f: wr.write(f)

if __name__ == '__main__':
    print(f'wrap {W:.2f} x {H:.2f} mm (perimeter {PER:.2f} + {LAP} lap), vent at ({VX:.2f}, {VY:.2f}), flats {[(round(a, 2), round(b, 2)) for a, b in L["flats"]]}')
    pw, ph = build(); rasterize(pw, ph)
