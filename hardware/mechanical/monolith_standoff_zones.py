"""Where the cover standoffs (H101-H104) may go: a board-face map of the allowed zones, around the hard keep-outs and the
parts already placed on Production/Monolith.kicad_pcb.
Run: (1) KiCad's python dumps the placement:  "C:/Program Files/KiCad/10.0/bin/python.exe" -I monolith_standoff_zones.py --dump BOARD JSON
     (2) the mechanical venv draws the map:    python monolith_standoff_zones.py JSON
-> monolith_side_standoff_zones.png, plus suggested positions on stdout (KiCad mm).
Rules (from the mechanical model; positions are SB_STANDOFFS in monolith_shell.py):
- the standoff (Wurth WA-SMSI, 5.8 mm courtyard) sits on F.Cu, and its 3 mm hole goes through the board, so B.Cu parts
  must clear the hole too;
- it only helps under the free middle of the cover: the ends are held by the top lip, the screws and the cap bands;
- keep-outs: USB-C bodies, PACK lead holes, sense-tap holes, the vent, the BLE module (and 5 mm round it), board edges/notches;
- best over a TPU frame bar on the back, so the load goes straight on into the cells."""
import sys, json, os

def dump(board, out):
    import pcbnew
    b = pcbnew.LoadBoard(board); res = []
    for fp in b.GetFootprints():
        polys = []
        for lay in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            sp = fp.GetCourtyard(lay)
            for i in range(sp.OutlineCount()):
                o = sp.Outline(i)
                polys.append([(pcbnew.ToMM(o.CPoint(k).x), pcbnew.ToMM(o.CPoint(k).y)) for k in range(o.PointCount())])
        res.append(dict(ref=fp.GetReference(), layer='B' if fp.IsFlipped() else 'F',
                        x=pcbnew.ToMM(fp.GetPosition().x), y=pcbnew.ToMM(fp.GetPosition().y), crt=polys))
    json.dump(res, open(out, 'w'))

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--dump':
    dump(sys.argv[2], sys.argv[3]); sys.exit()

import numpy as np
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
import monolith_shell as S
from monolith_side_renders import Sheet, C, INK, MUTED, RULE, ACCENT, SS

R_STAND = 5.8 / 2 + 0.25          # courtyard radius + a little
R_HOLE = 1.5 + 0.4                # through hole + clearance, for B.Cu parts
def K(y, z): return S.kicad(y, z)                      # shell (y, z) -> KiCad (x, y)
def kpoly(rect):                                        # shell rect (y0, y1, z0, z1) -> KiCad polygon
    y0, y1, z0, z1 = rect; a, b = K(y0, z0), K(y1, z1)
    return box(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))

def zones(fps):
    w, z0, z1, ny, nz = S.sb_board_w / 2, S.sb_zb0, S.sb_zb1, S.sb_notch_y, S.sb_notch_z
    board = Polygon([K(*p) for p in [(-ny, z0), (ny, z0), (ny, nz), (w, nz), (w, z1), (-w, z1), (-w, nz), (-ny, nz)]])
    useful = kpoly((-w, w, S.SB_CAP_BAND + 4.0, S.SB_H - S.SB_CAP_BAND - 4.0))     # the cover's free middle
    keep = []
    for py in (-S.SB_PORT_Y, S.SB_PORT_Y):                                         # USB-C bodies + notches
        keep.append(kpoly((py - 5.6, py + 5.6, S.sb_zb1 + S.USB_FACE_OUT - S.USB_DEPTH - 0.5, S.sb_zb1 + 1)))
    for y, z, l in S.sb_slots().values():                                          # nickel tab slots and their pads
        a, b = l / 2 + S.SB_SLOT_RING + 0.3, S.SB_SLOT_W / 2 + S.SB_SLOT_RING + 0.3
        keep.append(kpoly((y - a, y + a, z - b, z + b)))
    keep.append(Point(*K(0, S.SB_VENT_Z)).buffer(S.SB_VENT_D / 2 + 2))           # vent keep-out
    s = S.SB_ANT_SIDE; ya, yb = sorted((s * S.sb_ant_y[0], s * S.sb_ant_y[1]))
    ble = kpoly((ya, yb, S.sb_ant_zc - S.SB_ANT_MOD[0] / 2, S.sb_ant_zc + S.SB_ANT_MOD[0] / 2))
    keep.append(ble.buffer(5.0 - R_STAND, join_style='mitre'))                      # 5 mm rule (edge to edge)
    hard = unary_union(keep)
    ownH = {f"H10{i}" for i in range(1, 5)}
    partsF, partsB = [], []
    for f in fps:
        if f['ref'] in ownH: continue
        for poly in f['crt']:
            if len(poly) < 3: continue
            p = Polygon(poly).buffer(0)
            if not p.intersects(board): continue
            (partsB if f['layer'] == 'B' else partsF).append(p)
    pF, pB = unary_union(partsF) if partsF else Polygon(), unary_union(partsB) if partsB else Polygon()
    inner = board.buffer(-R_STAND)
    centres = inner.intersection(useful).difference(hard.buffer(R_STAND)).difference(pF.buffer(R_STAND)).difference(pB.buffer(R_HOLE))
    lanes = unary_union([kpoly(l) for l in S.sb_lanes()])
    return dict(board=board, useful=useful, hard=hard, pF=pF, pB=pB, centres=centres, best=centres.intersection(lanes),
                lanes=lanes, ble=ble, fps=[f for f in fps if f['ref'] not in ownH and Point(f['x'], f['y']).within(board.buffer(2))])

def suggest(Z):
    """one standoff per quadrant of the free middle: on a lane if possible, near (+-11, lower/upper third)"""
    out = []
    zmid = (S.SB_CAP_BAND + S.SB_H - S.SB_CAP_BAND) / 2
    for zt in (zmid - 13, zmid + 13):
        for yt in (-S.pocket_r, S.pocket_r):
            tx, ty = K(yt, zt); best = None
            for pool, bonus in ((Z['best'], 0.0), (Z['centres'], 6.0)):
                if pool.is_empty: continue
                xs = np.arange(78, 122, 0.25); ys = np.arange(62, 138, 0.25)
                for X in xs:
                    for Y in ys:
                        if (X - 100) * (tx - 100) <= 0: continue          # stay on this side
                        d = np.hypot(X - tx, Y - ty) + bonus
                        if best is not None and d >= best[0]: continue
                        if pool.contains(Point(X, Y)): best = (d, X, Y, bonus == 0.0)
                if best: break
            out.append(best)
    return out

def draw(Z, cands, path):
    sh = Sheet(2200, 1040)
    sh.header('Cover standoffs: where they can go', 'Green: where a standoff centre may sit given the keep-outs and the parts placed so far. '
              'Dark green: also over a TPU frame bar on the back (best load path). Board seen from the cover side (F.Cu), KiCad coordinates.')
    ps, ox, oy = 11.0, 130, 160                      # screen = ox + ps*(X - 78), oy + ps*(Y - 62)
    T = lambda X, Y: (ox + ps * (X - 77.5), oy + ps * (Y - 62.0))
    def poly(g, fill=None, outline=None, width=1):
        for p in (g.geoms if hasattr(g, 'geoms') else [g]):
            if p.is_empty or not hasattr(p, 'exterior'): continue
            sh.g.polygon([(a * SS, b * SS) for a, b in (T(*c) for c in p.exterior.coords)], fill=fill, outline=outline, width=int(width * SS))
            for h in p.interiors:
                sh.g.polygon([(a * SS, b * SS) for a, b in (T(*c) for c in h.coords)], fill=(255, 255, 255) if fill else None, outline=outline)
    poly(Z['board'], fill=(236, 238, 232), outline=C['board'], width=2.5)
    poly(Z['board'].difference(Z['useful']), fill=(222, 222, 222))
    poly(Z['lanes'], outline=(222, 118, 168), width=1.5)
    poly(Z['centres'], fill=(170, 222, 160))
    poly(Z['best'], fill=(70, 160, 80))
    poly(Z['hard'].intersection(Z['board']), fill=(240, 160, 150), outline=(190, 70, 60))
    poly(Z['pF'].intersection(Z['board'].buffer(1)), outline=(40, 40, 46), width=1.2)
    poly(Z['pB'].intersection(Z['board'].buffer(1)), outline=(80, 110, 200), width=1.2)
    for (y, z), n in zip(S.SB_STANDOFFS, ('H101', 'H102', 'H103', 'H104')):     # where they are now
        X, Y = K(y, z); a = T(X, Y); r = 2.9 * ps
        sh.g.ellipse([(a[0] - r) * SS, (a[1] - r) * SS, (a[0] + r) * SS, (a[1] + r) * SS], outline=(120, 120, 120), width=int(2 * SS))
        sh.text(a[0], a[1], n, 12, True, fill=(110, 110, 110), anchor='mm')
    for i, c in enumerate(cands):
        if not c: continue
        a = T(c[1], c[2]); r = 2.9 * ps
        sh.g.ellipse([(a[0] - r) * SS, (a[1] - r) * SS, (a[0] + r) * SS, (a[1] + r) * SS], outline=ACCENT, width=int(3 * SS))
        sh.text(a[0], a[1], f'S{i + 1}', 13, True, fill=ACCENT, anchor='mm')
    for lab, (y, z) in (('USB-C', (0, S.sb_zb1 - 3)), ('vent', (0, S.SB_VENT_Z)), ('BLE (B.Cu)', (S.SB_ANT_SIDE * 16.6, S.sb_ant_zc))):
        a = T(*K(y, z)); sh.text(a[0], a[1], lab, 12, True, fill=(150, 50, 40), anchor='mm')
    x0 = 700; y = 170
    sh.text(x0, y, 'Rules', 20, True); y += 40
    for s in ['A standoff is a 4.35 mm steel tube, 3.5 mm tall, on F.Cu, with a 5.8 mm courtyard and a 3 mm hole',
              'through the board. So F.Cu parts clear its courtyard, and B.Cu parts clear the hole.',
              'Grey band at each end: the cover is already held there (top lip, screws, cap bands). A standoff only',
              'helps in the free middle.',
              'Red: keep-outs (USB-C bodies, PACK pads, sense-tap holes, the vent, and the BLE module plus 5 mm).',
              'Pink outline: the TPU frame bars on the back. A standoff over a bar passes its load straight into the cells.',
              'Spread them: one pair in the lower half and one in the upper half, one each side, so no part of the',
              'cover is more than about 15 mm from a support. Three can work; two is too few.',
              'Black outlines: F.Cu courtyards placed now. Blue: B.Cu. Grey rings: H101-H104 where they are today.']:
        sh.text(x0, y, s, 15); y += 26
    y += 20; sh.text(x0, y, 'Suggested positions with the current placement (blue rings)', 20, True); y += 40
    rows = []
    for i, c in enumerate(cands):
        if c: rows.append([f'S{i + 1}', f'{c[1]:.1f}', f'{c[2]:.1f}', 'yes' if c[3] else 'no'])
        else: rows.append([f'S{i + 1}', '-', '-', 'no room'])
    y = sh.table(x0, y, ['', '>KiCad x', '>KiCad y', 'over a bar'], rows, [60, 140, 140, 160], 15)
    y += 20
    for s in ['These follow your placement: re-run this after moving parts, or tell me the spots you want.',
              'Changing them is one edit: SB_STANDOFFS in mechanical/monolith_shell.py (shell y, z). The model, the checks,',
              'the renders and make_board.py --standoffs all read it.']:
        sh.text(x0, y, s, 15, fill=MUTED); y += 26
    sh.save(path)

if __name__ == '__main__':
    fps = json.load(open(sys.argv[1]))
    Z = zones(fps); cands = suggest(Z)
    for i, c in enumerate(cands):
        print(f"S{i + 1}: " + (f"KiCad ({c[1]:.2f}, {c[2]:.2f}), over a lane: {c[3]}" if c else "no room"))
    draw(Z, cands, os.path.join(S.RETIRED, 'monolith_side_standoff_zones.png'))
    print('wrote monolith_side_standoff_zones.png')
