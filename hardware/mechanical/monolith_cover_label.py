"""Monolith side cover: laser-cut 1.0 mm 5052 aluminium, black anodized, laser-marked label (JLCCNC sheet metal).
PROTOTYPE artwork, built from the data we have now (cells: docs/project/feb-21700g-datasheet-notes.md).
Run: python monolith_cover_label.py   (numpy, shapely, matplotlib, Pillow; KiCad 10 for the STEP)
-> monolith_side_cover.step            plate with holes, the 3D file JLCCNC requires (made by kicad-cli from a
                                        throw-away board file, since the plate is just a 1.0 mm outline with holes)
   monolith_side_cover_marking.dxf     2D marking file: OUTLINE + HOLES for registration, MARKING as closed outlines
                                        (JLCCNC: text as "double-line" outlines, lines at least 0.2 mm wide)
   monolith_side_cover_marking.svg     the same artwork, for checking and for the quote upload if they prefer it
   monolith_side_cover_preview.png     flat plate as anodized + marked, and the plate in the pack with the caps on
Plate coordinates: X = shell y (to the right seen from outside, toward the C4 / PACK+ side), Y = shell z (port end up).
The outer face is drawn as seen from outside, so the artwork reads the right way round."""
import numpy as np, os, subprocess, shutil
from shapely.geometry import Polygon, LineString, Point, box, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import contourpy
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import monolith_shell as S

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = 'C:/Windows/Fonts/'
F_BOLD, F_SEMI, F_REG = FONTS + 'segoeuib.ttf', FONTS + 'seguisb.ttf', FONTS + 'segoeui.ttf'
MIN_LINE = 0.2            # JLCCNC: marking lines at least 0.2 mm
STROKE = 0.3              # line art width used here

# ---------------- label data (PROTOTYPE: confirm before the final) ----------------
PACK = dict(chem='Li-ion', config='4S1P', v_nom=14.4, ah=6.5, wh=93.6)   # FEB 21700G: 4 x 3.60 V x 6.5 Ah = 93.6 Wh
                                                                        # (was 82 Wh with the EVE 58E)
PORTS = 'USB-C PD in/out  5-20 V  ·  100 W max'

# ---------------- plate geometry, all from monolith_shell ----------------
W2 = S.sb_cover_w / 2
Y0, Y1 = S.sb_cover_z0, S.sb_cover_z1
HOLES = [(sy * S.sb_pillar_y, S.sb_screw_z, 1.1) for sy in (-1, 1)] + [(0.0, S.SB_VENT_Z, S.SB_VENT_D / 2)]
VIS = (-S.a_in, S.SB_CAP_BAND, S.a_in, S.SB_H - S.SB_CAP_BAND)       # what shows between the cap bands
MARGIN = 1.2
ART = (VIS[0] + MARGIN, VIS[1] + MARGIN, VIS[2] - MARGIN, VIS[3] - MARGIN)
VENT_KEEP = 2.6           # no marking within this radius of the vent hole centre (1.1 mm round the 3 mm hole)

# ---------------- helpers ----------------
def ring_xor(rings):
    g = Polygon()
    for r in rings:
        if len(r) >= 3:
            p = Polygon(r).buffer(0)
            if not p.is_empty: g = g.symmetric_difference(p)
    return g
_cap = {}
def text(s, font, cap_h, x, y, anchor='c', track=0.0):
    """outlined text: cap height cap_h (mm), baseline y, anchored left/centre/right at x; track = extra gap per letter"""
    prop = FontProperties(fname=font)
    if font not in _cap:
        _cap[font] = TextPath((0, 0), 'H', size=1.0, prop=prop).get_extents().height
    k = cap_h / _cap[font]
    if track:
        parts, cx = [], 0.0
        for ch in s:
            if ch == ' ': cx += 0.33 / k * cap_h * 1.0; continue
            tp = TextPath((0, 0), ch, size=1.0, prop=prop); ext = tp.get_extents()
            g = ring_xor(tp.to_polygons(closed_only=True))
            parts.append(affinity.translate(g, cx - ext.x0, 0)); cx += ext.width + track / k
        g = unary_union(parts)
    else:
        g = ring_xor(TextPath((0, 0), s, size=1.0, prop=prop).to_polygons(closed_only=True))
    g = affinity.scale(g, k, k, origin=(0, 0))
    if cap_h < 2.5: g = g.buffer(0.06, join_style='mitre')   # small text: thicken the strokes so none is under 0.2 mm
    x0, _, x1, _ = g.bounds
    dx = {'l': x - x0, 'c': x - (x0 + x1) / 2, 'r': x - x1}[anchor]
    return affinity.translate(g, dx, y)
def fit(g, maxw=None, cx=0.0):
    """scale g down (about its centre line) so it fits maxw, the art width by default"""
    maxw = maxw or (ART[2] - ART[0]); x0, y0, x1, y1 = g.bounds
    if x1 - x0 > maxw: g = affinity.scale(g, maxw / (x1 - x0), maxw / (x1 - x0), origin=((x0 + x1) / 2, y0))
    x0, _, x1, _ = g.bounds
    return affinity.translate(g, cx - (x0 + x1) / 2, 0)
def stroke(pts, w=STROKE, closed=False):
    pts = list(pts) + ([pts[0]] if closed else [])
    return LineString(pts).buffer(w / 2, cap_style='round', join_style='round')
def rrect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=12)

# ---------------- artwork ----------------
def wordmark():
    t = fit(text('MONOLITH', F_BOLD, 5.4, 0, 64.0, 'c', track=0.9))
    rule = stroke([(ART[0] + 2, 61.6), (ART[2] - 2, 61.6)], 0.3)
    sub = text(f'{PACK["wh"]} Wh  ·  100 W  ·  USB-C PD', F_SEMI, 1.7, 0, 58.8, 'c')
    return unary_union([t, rule, sub])

def topo():
    """the fun bit: a contour map of a peak, a dashed trail to the summit, a flag, and the elevation in Wh"""
    x0, y0, x1, y1 = ART[0], 36.2, ART[2], 56.8
    sh = (y1 - y0) / 24.6; oy = y0 - 31.0 * sh     # peaks were laid out for a 31..55.6 panel
    frame = rrect(x0, y0, x1, y1, 2.0)
    xs = np.linspace(x0 - 2, x1 + 2, 240); ys = np.linspace(y0 - 2, y1 + 2, 160); X, Y = np.meshgrid(xs, ys)
    def peak(cx, cy, sx, sy, a): return a * np.exp(-(((X - cx) / sx) ** 2 + ((Y - (oy + cy * sh)) / (sy * sh)) ** 2))
    Z = (peak(5, 47, 9.5, 6.5, 1.0) + peak(-9, 42, 7.5, 5.5, 0.62) + peak(13, 37, 5.5, 4.2, 0.38)
         + peak(-17, 50, 5, 4, 0.25) + 0.012 * (Y - y0) + 0.05 * np.sin(X / 3.1) * np.cos(Y / 4.3))
    gen = contourpy.contour_generator(xs, ys, Z)
    levels = np.linspace(Z.min() + 0.06, Z.max() - 0.03, 14)
    lines = []
    for i, lv in enumerate(levels):
        w = 0.46 if i % 4 == 3 else 0.28       # index contours heavier, like a real topo map
        for seg in gen.lines(lv):
            if len(seg) > 3: lines.append(LineString(seg).buffer(w / 2, cap_style='round', join_style='round'))
    contours = unary_union(lines)
    iy, ix = np.unravel_index(np.argmax(Z), Z.shape); sx_, sy_ = xs[ix], ys[iy]
    # trail: a winding dashed path from the lower left to the summit
    way = np.array([(x0 + 2.5, y0 + 2.0)] + [(x, oy + y * sh) for x, y in [(-11, 34.5), (-4.5, 36.0), (-8.0, 40.5), (-2.0, 43.2), (1.0, 45.5)]] + [(sx_ - 0.6, sy_ - 0.9)])
    t = np.linspace(0, 1, len(way)); tt = np.linspace(0, 1, 400)
    path = np.c_[np.interp(tt, t, way[:, 0]), np.interp(tt, t, way[:, 1])]
    for _ in range(25): path[1:-1] = 0.25 * path[:-2] + 0.5 * path[1:-1] + 0.25 * path[2:]   # smooth
    L = LineString(path); dashes = []
    d = 0.0
    while d < L.length:
        a, b = L.interpolate(d), L.interpolate(min(d + 1.1, L.length))
        dashes.append(LineString([a, b]).buffer(0.21, cap_style='round')); d += 1.9
    trail = unary_union(dashes)
    # summit: flag on a pole, with a ring round the top
    pole = stroke([(sx_, sy_), (sx_, sy_ + 3.6)], 0.32)
    flag = Polygon([(sx_ + 0.15, sy_ + 3.6), (sx_ + 2.6, sy_ + 2.95), (sx_ + 0.15, sy_ + 2.3)])
    ring = Point(sx_, sy_).buffer(0.75).difference(Point(sx_, sy_).buffer(0.42))
    elev = text(f'EL. {PACK["wh"]} Wh', F_BOLD, 1.6, sx_ + 1.6, sy_ - 3.2, 'l')
    start = text('TRAILHEAD', F_BOLD, 1.5, x0 + 2.0, y0 + 3.3, 'l')
    knock = unary_union([elev.buffer(0.55), flag.buffer(0.5), pole.buffer(0.4), ring.buffer(0.45),
                         start.buffer(0.5), trail.buffer(0.25)])
    inner = frame.buffer(-0.9)
    art = unary_union([contours.difference(knock), trail, pole, flag, ring, elev, start]).intersection(inner)
    art = art.buffer(-0.1).buffer(0.1)        # drop slivers left by the knock-outs (keeps every line >= 0.2 mm)
    border = frame.difference(frame.buffer(-0.32))
    north = unary_union([Polygon([(x1 - 3.7, y1 - 6.0), (x1 - 2.7, y1 - 3.3), (x1 - 1.7, y1 - 6.0), (x1 - 2.7, y1 - 5.2)]).buffer(0.08),
                         text('N', F_BOLD, 1.5, x1 - 2.7, y1 - 2.8, 'c')])
    return unary_union([art.difference(north.buffer(0.5)).buffer(-0.1).buffer(0.1), border, north])

def specs():
    g = []
    g.append(fit(text(f'{PACK["chem"]} battery pack  ·  {PACK["config"]}', F_SEMI, 1.75, 0, 32.4, 'c')))
    big = text(f'{PACK["v_nom"]:.1f} V DC  ·  {PACK["ah"]:.1f} Ah  ·', F_SEMI, 2.3, 0, 28.3, 'l')
    wh = text(f'{PACK["wh"]} Wh', F_BOLD, 2.9, 0, 28.3, 'l')
    wh = affinity.translate(wh, big.bounds[2] + 1.3 - wh.bounds[0], 0)
    g.append(fit(unary_union([big, wh])))
    g.append(fit(text(PORTS, F_BOLD, 1.6, 0, 24.8, 'c')))
    g.append(fit(text('Do not crush, puncture or burn  ·  max 60 °C', F_BOLD, 1.5, 0, 21.9, 'c')))
    g.append(flight_badge(19.0))
    return unary_union(g)

def flight_badge(yc):
    """our own carry-on mark: an airliner in a ring with a check disc, then CARRY-ON OK / < 100 Wh.
    Spare lithium batteries go in the cabin, and under 100 Wh needs no airline approval (FAA / IATA)."""
    fus = LineString([(-1.05, 0), (1.05, 0)]).buffer(0.2, cap_style='round')
    wing = Polygon([(0.25, 0.1), (-0.35, 1.05), (-0.62, 1.05), (-0.2, 0.1), (-0.2, -0.1), (-0.62, -1.05), (-0.35, -1.05), (0.25, -0.1)])
    tail = Polygon([(-0.75, 0.05), (-1.05, 0.48), (-1.25, 0.48), (-1.0, 0.05), (-1.0, -0.05), (-1.25, -0.48), (-1.05, -0.48), (-0.75, -0.05)])
    plane = affinity.rotate(unary_union([fus, wing, tail]).buffer(0.08), 40, origin=(0, 0))
    r0 = 1.75; cx = 0.0
    ring = Point(0, 0).buffer(r0).difference(Point(0, 0).buffer(r0 - 0.32))
    disc_c = (r0 * 0.72, -r0 * 0.72)
    disc = Point(disc_c).buffer(0.82)
    tick = LineString([(disc_c[0] - 0.42, disc_c[1] + 0.02), (disc_c[0] - 0.1, disc_c[1] - 0.3), (disc_c[0] + 0.42, disc_c[1] + 0.32)]).buffer(0.16, cap_style='round', join_style='round')
    icon = unary_union([ring.difference(disc.buffer(0.3)), plane.difference(disc.buffer(0.3)), disc.difference(tick)])
    icon = icon.buffer(-0.11).buffer(0.11)     # no sliver under 0.2 mm where the plane meets the disc gap
    label = text('CARRY-ON OK  ·  < 100 Wh', F_BOLD, 1.75, 0, -0.85, 'l')
    label = affinity.translate(label, r0 + 1.0 - label.bounds[0], 0)
    g = unary_union([icon, label])
    x0, y0, x1, y1 = g.bounds
    return affinity.translate(g, cx - (x0 + x1) / 2, yc - (y0 + y1) / 2)

def symbols():
    """recycling arrows with 'Li-ion' (left of the vent) and the crossed-out wheelie bin (right)"""
    out = []
    cx, cy, r = -15.0, 13.8, 2.4                       # three chasing arrows round a triangle
    corners = [(cx + r * np.cos(a), cy + r * np.sin(a)) for a in np.radians([90, 210, 330])]
    for i in range(3):
        a, b = np.array(corners[i]), np.array(corners[(i + 1) % 3]); d = (b - a) / np.linalg.norm(b - a)
        p0, p1 = a + d * 0.9, b - d * 1.35
        out.append(stroke([p0, p1], 0.42))
        n = np.array([-d[1], d[0]])
        out.append(Polygon([p1 + d * 0.95, p1 + n * 0.62, p1 - n * 0.62]))
    out.append(text('Li-ion', F_BOLD, 1.6, cx + 3.4, cy - 0.8, 'l'))
    bx, by = 14.0, 11.8                                 # WEEE bin: body, lid, wheel, cross, bar
    body = stroke([(bx - 1.5, by + 4.0), (bx - 1.15, by + 0.6), (bx + 1.15, by + 0.6), (bx + 1.5, by + 4.0)], 0.32)
    lid = stroke([(bx - 1.9, by + 4.25), (bx + 1.9, by + 4.25)], 0.36)
    handle = stroke([(bx - 0.5, by + 4.25), (bx - 0.5, by + 4.75), (bx + 0.5, by + 4.75), (bx + 0.5, by + 4.25)], 0.26)
    wheel = Point(bx - 1.15, by + 0.35).buffer(0.42).difference(Point(bx - 1.15, by + 0.35).buffer(0.16))
    cross = unary_union([stroke([(bx - 2.3, by + 5.2), (bx + 2.3, by - 0.1)], 0.34), stroke([(bx + 2.3, by + 5.2), (bx - 2.3, by - 0.1)], 0.34)])
    bar = box(bx - 2.0, by - 1.35, bx + 2.0, by - 0.75)
    out += [body, lid, handle, wheel, cross, bar]
    return unary_union(out)

def artwork():
    g = unary_union([wordmark(), topo(), specs(), symbols()])
    vent = Point(0, S.SB_VENT_Z).buffer(VENT_KEEP)
    return g.difference(vent)

# ---------------- outputs ----------------
def polys(g): return list(g.geoms) if isinstance(g, MultiPolygon) else ([g] if not g.is_empty else [])
def plate_outline(): return [(-W2, Y0), (W2, Y0), (W2, Y1), (-W2, Y1)]

def write_dxf(path, g):
    e = []
    def pline(pts, layer):
        e.append(f"0\nPOLYLINE\n8\n{layer}\n66\n1\n70\n1\n")
        for x, y in pts: e.append(f"0\nVERTEX\n8\n{layer}\n10\n{x:.4f}\n20\n{y:.4f}\n")
        e.append("0\nSEQEND\n")
    pline(plate_outline(), 'OUTLINE')
    for x, y, r in HOLES: e.append(f"0\nCIRCLE\n8\nHOLES\n10\n{x:.4f}\n20\n{y:.4f}\n40\n{r:.4f}\n")
    pline([(VIS[0], VIS[1]), (VIS[2], VIS[1]), (VIS[2], VIS[3]), (VIS[0], VIS[3])], 'VISIBLE_REF')
    for p in polys(g):
        pline(list(p.exterior.coords)[:-1], 'MARKING')
        for h in p.interiors: pline(list(h.coords)[:-1], 'MARKING')
    open(path, 'w').write("0\nSECTION\n2\nENTITIES\n" + "".join(e) + "0\nENDSEC\n0\nEOF\n")

def write_svg(path, g):
    def d(ring): return 'M' + ' L'.join(f'{x:.3f},{-y:.3f}' for x, y in ring) + ' Z'
    parts = []
    for p in polys(g):
        parts.append('<path d="' + ' '.join([d(p.exterior.coords)] + [d(h.coords) for h in p.interiors]) + '"/>')
    holes = ''.join(f'<circle cx="{x:.3f}" cy="{-y:.3f}" r="{r:.3f}" fill="white" stroke="#888" stroke-width="0.05"/>' for x, y, r in HOLES)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{2*W2}mm" height="{Y1-Y0}mm" viewBox="{-W2} {-Y1} {2*W2} {Y1-Y0}">'
           f'<rect x="{-W2}" y="{-Y1}" width="{2*W2}" height="{Y1-Y0}" fill="none" stroke="#888" stroke-width="0.05"/>'
           f'<g fill="black" fill-rule="evenodd">{"".join(parts)}</g>{holes}</svg>')
    open(path, 'w').write(svg)

def write_step(path):
    """plate as a 1.0 mm 'board' (outline + holes on Edge.Cuts) -> kicad-cli STEP"""
    cli = shutil.which('kicad-cli') or r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
    if not os.path.exists(cli): print('kicad-cli not found: STEP skipped'); return False
    ox, oy = 100.0, 100.0          # KiCad y points down
    pts = plate_outline()
    segs = ''.join(f'(gr_line (start {ox + a[0]:.4f} {oy - a[1]:.4f}) (end {ox + b[0]:.4f} {oy - b[1]:.4f}) (layer "Edge.Cuts") (width 0.05))\n'
                   for a, b in zip(pts, pts[1:] + pts[:1]))
    circ = ''.join(f'(gr_circle (center {ox + x:.4f} {oy - y:.4f}) (end {ox + x + r:.4f} {oy - y:.4f}) (layer "Edge.Cuts") (width 0.05))\n' for x, y, r in HOLES)
    brd = ('(kicad_pcb (version 20240108) (generator "monolith_cover_label")\n(general (thickness %.2f))\n(paper "A4")\n'
           '(layers (0 "F.Cu" signal) (31 "B.Cu" signal) (44 "Edge.Cuts" user))\n' % S.SB_COVER_T) + segs + circ + ')\n'
    tmp = os.path.join(HERE, '_cover_tmp.kicad_pcb'); open(tmp, 'w').write(brd)
    r = subprocess.run([cli, 'pcb', 'export', 'step', '--board-only', '--force', '-o', path, tmp], capture_output=True, text=True)
    os.remove(tmp)
    if r.returncode != 0: print('STEP export failed:', r.stdout[-400:], r.stderr[-400:]); return False
    return True

def preview(path, g):
    SS, px = 3, 9.0
    Wf, Hf = 1700, 980
    img = Image.new('RGB', (Wf * SS, Hf * SS), 'white'); d = ImageDraw.Draw(img)
    def fnt(sz, b=False):
        try: return ImageFont.truetype(F_SEMI if b else F_REG, int(sz * SS))
        except OSError: return ImageFont.load_default()
    ANOD, MARK = (34, 35, 39), (206, 208, 212)
    def plate(ox, oy, k, hidden_shade=True):
        T = lambda x, y: ((ox + k * x) * SS, (oy - k * y) * SS)
        d.rectangle([*T(-W2, Y1), *T(W2, Y0)], fill=ANOD)
        # faint brushed texture
        rng = np.random.default_rng(3)
        for _ in range(int(450 * k / 9)):
            yy = rng.uniform(Y0, Y1); c = 34 + int(rng.integers(-3, 5))
            d.line([T(-W2, yy), T(W2, yy)], fill=(c, c + 1, c + 5), width=1)
        for p in polys(g):
            d.polygon([T(x, y) for x, y in p.exterior.coords], fill=MARK)
            for h in p.interiors: d.polygon([T(x, y) for x, y in h.coords], fill=ANOD)
        for x, y, r in HOLES:
            a, b = T(x - r, y + r), T(x + r, y - r); d.ellipse([*a, *b], fill='white', outline=(120, 120, 120), width=SS)
        if hidden_shade:
            for ya, yb, lab in ((Y0, VIS[1], 'under the bottom cap band'), (VIS[3], Y1, 'under the top cap band / lip')):
                over = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(over)
                od.rectangle([*T(-W2, yb), *T(W2, ya)], fill=(240, 150, 60, 110))
                img.paste(Image.alpha_composite(img.convert('RGBA'), over).convert('RGB'))
                tx, ty = T(W2 + 1.0, (ya + yb) / 2)
                ImageDraw.Draw(img).text((tx, ty), lab, font=fnt(14), fill=(110, 110, 110), anchor='lm')
    d.text((30 * SS, 22 * SS), 'Monolith cover: 1.0 mm 5052 aluminium, black anodized, laser-marked (prototype)', font=fnt(26, True), fill=(30, 30, 34))
    d.text((30 * SS, 62 * SS), 'JLCCNC sheet metal: STEP for the plate, DXF for the marking (outlined text and lines, all at least 0.2 mm). '
           'Orange: hidden by the TPU cap bands.', font=fnt(15), fill=(110, 110, 110))
    plate(260, 860, px)
    d = ImageDraw.Draw(img)
    # in the pack: front view (from the cover side) with the tray rim and the TPU caps
    ox, oy, k = 1030, 880, 8.0
    T = lambda x, y: ((ox + k * x) * SS, (oy - k * y) * SS)
    capc, band = (236, 156, 80), (118, 72, 50)
    a_out = S.a_sb + S.SB_CAP_PROUD
    d.rounded_rectangle([*T(-S.a_sb, S.SB_H), *T(S.a_sb, 0)], radius=6 * SS, fill=(205, 205, 200))
    sub_img = Image.new('RGB', img.size, 'white')
    plate(ox, oy, k, hidden_shade=False); d = ImageDraw.Draw(img)
    for ya, yb in ((-S.SB_CAP_T, S.SB_CAP_BAND), (S.SB_H - S.SB_CAP_BAND, S.SB_H + S.SB_CAP_T)):
        d.rounded_rectangle([*T(-a_out, yb), *T(a_out, ya)], radius=5 * SS, fill=capc, outline=band, width=3 * SS)
    d.text(((ox) * SS, (oy - k * (S.SB_H + S.SB_CAP_T) - 26) * SS), 'In the pack, caps on', font=fnt(18, True), fill=(30, 30, 34), anchor='mm')
    # notes
    nx, ny = 1430, 150
    notes = ['Plate', f'  {2*W2:.1f} x {Y1-Y0:.1f} x {S.SB_COVER_T:.1f} mm, 5052-H32',
             '  2 x Ø2.2 screw holes, Ø3.0 vent hole', '  (holes ≥ 1 mm and ≥ ½ t: OK)', '',
             'Finish', '  black anodize, laser marking', '  (mask the vent patch area inside', '   if JLC can; optional)', '',
             'Label', f'  {PACK["chem"]} {PACK["config"]}, {PACK["v_nom"]:.1f} V, {PACK["ah"]:.1f} Ah, {PACK["wh"]} Wh',
             '  carry-on badge: our own plane +', '  check mark; under 100 Wh, so no', '  airline approval needed', '  no certification marks', '', 'Art', '  topo map of a peak, a trail from',
             '  the trailhead, the summit flag at', f'  "EL. {PACK["wh"]} Wh"']
    for i, s in enumerate(notes):
        d.text((nx * SS, (ny + 24 * i) * SS), s, font=fnt(15, not s.startswith(' ') and s != ''), fill=(30, 30, 34))
    img.resize((Wf, Hf), Image.LANCZOS).save(path)

if __name__ == '__main__':
    g = artwork()
    # checks: inside the visible window, clear of the vent, no feature thinner than MIN_LINE
    x0, y0, x1, y1 = g.bounds
    thin = g.difference(g.buffer(-MIN_LINE / 2 + 0.005).buffer(MIN_LINE / 2 - 0.005))
    thin = [p for p in (thin.geoms if hasattr(thin, 'geoms') else [thin]) if p.area > 0.01]   # ignore sharp-corner rounding
    print(f"marking bounds X {x0:.2f}..{x1:.2f}, Y {y0:.2f}..{y1:.2f}; art window X {ART[0]:.1f}..{ART[2]:.1f}, Y {ART[1]:.1f}..{ART[3]:.1f}")
    print(f"  {'ok ' if x0 >= ART[0] - 0.01 and x1 <= ART[2] + 0.01 and y0 >= ART[1] - 0.01 and y1 <= ART[3] + 0.01 else 'BAD'} inside the visible window")
    vd = min(Point(0, S.SB_VENT_Z).distance(p) for p in polys(g))
    print(f"  {'ok ' if vd >= VENT_KEEP - 0.01 else 'BAD'} vent keep-out: nearest mark {vd:.2f} mm from the vent centre")
    print(f"  {'ok ' if not thin else 'CHECK'} features under {MIN_LINE} mm: {len(thin)}" + (f" (at {[tuple(round(c, 1) for c in p.centroid.coords[0]) for p in thin[:6]]})" if thin else ''))
    write_dxf(os.path.join(HERE, 'monolith_side_cover_marking.dxf'), g)
    write_svg(os.path.join(HERE, 'monolith_side_cover_marking.svg'), g)
    ok = write_step(os.path.join(HERE, 'monolith_side_cover.step'))
    preview(os.path.join(HERE, 'monolith_side_cover_preview.png'), g)
    print("wrote monolith_side_cover_marking.dxf/.svg, monolith_side_cover_preview.png" + (", monolith_side_cover.step" if ok else ""))
