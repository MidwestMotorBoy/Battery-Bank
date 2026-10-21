"""Monolith home-print kit: the side-board pack as FDM parts, dummy cells and a dummy board, for fit checks,
assembly practice and the dummy-mass drop test. Imports the generators; needs numpy, scipy, trimesh, manifold3d, pillow.
Run: python monolith_print_kit.py  -> print_kit/*.stl (each one in its print orientation, on the bed at z = 0),
print_kit/kit_plate.png. Parts keep the production dimensions (MJF tolerances), so print the fit coupons first."""
import os, numpy as np, trimesh
from PIL import Image, ImageDraw, ImageFont
import monolith_shell as S, monolith_parts as P
from monolith_render import camera, CELL_G
import monolith_render as R

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'print_kit')

# ---------------- new-part parameters (mm) ----------------
CELL_WALL, CELL_FLOOR = 1.6, 1.6     # dummy cell: printed can
CELL_CAP_T, CELL_NUB_H, CELL_NUB_R = 2.0, 0.6, 3.5   # glued + end cap with a button nub
CELL_SPIGOT_L, CELL_SPIGOT_CLR = 3.0, 0.15
BLE_POCKET, BLE_CLR = 0.6, 0.15      # locating pocket in the dummy board's B.Cu face for the glued-on BLE block
LEAD_DRILL = 2.2                     # PACK lead holes in the dummy board (passes an insulated 18 AWG lead for the fit)
COVER_HOLE_D = 2.2                   # M2 clearance in the printed cover stand-in
COUPONS = {'coupon_bottom_end': (0.0, 10.0),            # floor, screw pillars and insert pilots
           'coupon_mid': (40.0, 48.0),                  # cell pockets, rib, crush ribs, cover rebates
           'coupon_top_end': (S.SB_H - 10.0, S.SB_H)}   # port holes, cover slot under the lip, board stops

def mesh(V):
    m = trimesh.Trimesh(vertices=V.reshape(-1, 3), faces=np.arange(len(V)*3).reshape(-1, 3), process=True)
    m.merge_vertices(); m.fix_normals(); return m
def box(x0, x1, y0, y1, z0, z1):
    return trimesh.creation.box(bounds=[[x0, y0, z0], [x1, y1, z1]])
def cyl(r, z0, z1, x=0.0, y=0.0, n=96):
    c = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=n); c.apply_translation([x, y, (z0 + z1)/2]); return c
def xcyl(r, x0, x1, y, z, n=48):        # cylinder along x
    c = cyl(r, x0, x1, n=n); c.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    c.apply_translation([0, y, z] - np.r_[0, c.centroid[1:]]); return c
def union(*ms): return trimesh.boolean.union(list(ms), engine='manifold')
def diff(a, *bs): return trimesh.boolean.difference([a, *bs], engine='manifold')
def inter(a, b): return trimesh.boolean.intersection([a, b], engine='manifold')

OPEN_UP = trimesh.transformations.rotation_matrix(-np.pi/2, [0, 1, 0])   # tray frame +x (open side) -> print +z
FLIP = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])          # upside down (top plate onto the bed)
def on_bed(m, T=None):
    m = m.copy()
    if T is not None: m.apply_transform(T)
    lo, hi = m.bounds; m.apply_translation([-(lo[0] + hi[0])/2, -(lo[1] + hi[1])/2, -lo[2]]); return m
def same_move(src, dst, T=None):
    """move dst exactly as on_bed moved src (slicer modifier volumes must stay registered to their body)"""
    a, b = src.copy(), dst.copy()
    if T is not None: a.apply_transform(T); b.apply_transform(T)
    lo, hi = a.bounds; b.apply_translation([-(lo[0] + hi[0])/2, -(lo[1] + hi[1])/2, -lo[2]]); return b

# ---------------- new parts ----------------
def cell_body():
    """printed can, open at the + end for ballast; length to the cap seat"""
    r = S.CELL_D/2; h = S.CELL_L - CELL_CAP_T - CELL_NUB_H
    return diff(cyl(r, 0, h), cyl(r - CELL_WALL, CELL_FLOOR, h + 1))
def cell_cap():
    """+ end: disc, button nub, spigot into the can. Printed spigot-down."""
    r = S.CELL_D/2; ri = r - CELL_WALL - CELL_SPIGOT_CLR
    return union(cyl(ri, -CELL_SPIGOT_L, 0.01), cyl(r, 0, CELL_CAP_T), cyl(CELL_NUB_R, CELL_CAP_T - 0.01, CELL_CAP_T + CELL_NUB_H))
def ble_span():
    y0, y1 = sorted((S.SB_ANT_SIDE*S.sb_ant_y[0], S.SB_ANT_SIDE*S.sb_ant_y[1]))
    return y0, y1, S.sb_ant_zc - S.SB_ANT_MOD[0]/2, S.sb_ant_zc + S.SB_ANT_MOD[0]/2
def board_dummy():
    """side_board_dummy (notched slab + USB-C envelopes) with the F.Cu cover standoffs, the two PACK lead holes and a
    pocket in B.Cu that locates the separate BLE block. Seated position; on_bed() lays it flat."""
    b = mesh(P.side_board_dummy()); xb0, xb1, h = S.sb_xb0, S.sb_xb1, S.SB_STANDOFF_D/2
    add = [box(xb1 - 0.01, xb1 + S.sb_standoff_h, y - h, y + h, z - h, z + h) for y, z in S.SB_STANDOFFS]
    y0, y1, z0, z1 = ble_span(); c = BLE_CLR
    cut = [box(xb0 - 1, xb0 + BLE_POCKET, y0 - c, y1 + 1, z0 - c, z1 + c)]
    cut += [xcyl(LEAD_DRILL/2, xb0 - 1, xb1 + 1, y, z) for y, z in S.SB_LEAD_HOLES.values()]
    return diff(union(b, *add), *cut, mesh(P.side_shell()))   # the tray cut trims the square USB-C corners to the round port holes
def ble_block():
    """CC2340R5MODA envelope, 7 x 10 x 2.3 mm, plus the part that sits in the pocket"""
    a, b = S.SB_ANT_MOD
    return box(0, b, 0, a, 0, S.SB_ANT_H + BLE_POCKET)
def cover_standin():
    """printed stand-in for the 1.0 mm aluminium cover (flat pattern as monolith_side_cover.dxf: u = y, v = z)"""
    w, z0, z1 = S.sb_cover_w, S.sb_cover_z0, S.sb_cover_z1
    m = box(-w/2, w/2, z0, z1, 0, S.SB_COVER_T)
    holes = [cyl(COVER_HOLE_D/2, -1, 2, sy*S.sb_pillar_y, S.sb_screw_z, 48) for sy in (-1, 1)]
    holes.append(cyl(S.SB_VENT_D/2, -1, 2, 0, S.SB_VENT_Z, 48))
    return diff(m, *holes)

# ---------------- the kit: (file, mesh in print pose, qty, material, notes) ----------------
def kit():
    tray = mesh(P.side_shell())
    K = [('01_tray', on_bed(tray, OPEN_UP), 1, 'PETG or PLA', 'open side up; no supports (port holes and the cover slot bridge)')]
    big = 200.0
    for i, (name, (z0, z1)) in enumerate(COUPONS.items()):
        K.append((f'00{"abc"[i]}_{name}', on_bed(inter(tray, box(-big, big, -big, big, z0, z1)), OPEN_UP), 1, 'same as the tray',
                  f'tray slice z {z0:.1f}-{z1:.1f}, printed like the tray'))
    K.append(('02_cover_standin', on_bed(cover_standin()), 1, 'PETG or PLA', 'stand-in for the aluminium cover; flat'))
    K.append(('03_cell_body', on_bed(cell_body()), 4, 'PLA', 'upright; fill with ballast, then glue the cap'))
    cap = cell_cap(); cap.apply_translation([0, 0, CELL_SPIGOT_L])
    K.append(('04_cell_cap', on_bed(cap), 4, 'PLA', 'spigot down, nub up'))
    K.append(('05_board_dummy', on_bed(board_dummy(), OPEN_UP), 1, 'PLA, green if you have it', 'B.Cu face down'))
    K.append(('06_ble_block', on_bed(ble_block()), 1, 'PLA', 'glue into the pocket on the board dummy B.Cu face'))
    for end, well in (('bottom', False), ('top', True)):
        body = mesh(P.side_cap('body', well)); n = '07' if end == 'bottom' else '08'
        K.append((f'{n}_cap_{end}', on_bed(body), 1, 'TPU 95A', 'crush slab down; load with its two modifiers'))
        for z in ('soft', 'corner'):
            K.append((f'{n}_cap_{end}_mod_{z}', same_move(body, mesh(P.side_cap(z, well))), 0, 'modifier',
                      f'infill {int(P.CAP_FILL[z]*100)} %'))
    K.append(('09_cell_holder_bottom', on_bed(mesh(P.bottom_holder(free=True))), 1, 'TPU 95A', 'rings up; printed 0.4 mm proud on purpose'))
    K.append(('10_board_shim', on_bed(mesh(P.board_shim())), 1, 'TPU 95A', ''))
    K.append(('11_cell_frame_top', on_bed(mesh(P.top_frame()), FLIP), 1, 'TPU 95A', 'plate on the bed, bars and web up'))
    K.append(('12_sense_strip_standin', on_bed(mesh(P.sense_strip())), 1, 'PLA', 'stand-in for the 0.6 mm ENIG strip; glue into the web pocket'))
    K.append(('13_usb_hold', on_bed(mesh(P.hold_pads()), OPEN_UP), 1, 'EVA template or TPU', '2 pads, 2 mm (2 x 1 mm EVA)'))
    return K

def font(sz):
    try: return R.font(sz)
    except ImportError:   # the freetype DLL can be blocked on Windows: fall back to the bitmap font
        try: return ImageFont.load_default(sz)
        except ImportError: return ImageFont.load_default()
def plate_png(K, path):
    W, H = 2000, 1150
    img = Image.new('RGB', (W, H), (255, 255, 255)); t = ImageDraw.Draw(img)
    def col(mat):
        for k, c in (('EVA', (225, 190, 120)), ('same', (170, 170, 166)), ('PETG', (170, 170, 166)),
                     ('TPU', (70, 70, 70)), ('PLA', (90, 150, 200))):
            if k in mat: return c
        return (150, 150, 150)
    shown = [k for k in K if k[2] > 0]
    iso = camera((0.9, -1.2, 1.1)); R.PX = 3.2
    rows = [[], [], []]
    for k in shown: rows[0 if k[0].startswith(('01', '02', '05', '06')) else 1 if k[0].startswith(('00', '07', '08')) else 2].append(k)
    f1, f2, f3 = font(26), font(15), font(13)
    t.text((30, 18), 'Monolith print kit: dummy cells, dummy board, tray, caps, fit coupons', fill=(20, 20, 20), font=f1)
    y = 110
    for row in rows:
        x = 40
        for name, m, q, mat, _ in row:
            V = m.triangles.copy(); V -= [0, 0, 0]
            P2 = (V.reshape(-1, 3) @ iso.T)
            w = (P2[:, 0].max() - P2[:, 0].min())*R.PX; h = (P2[:, 1].max() - P2[:, 1].min())*R.PX
            ox, oy = x - P2[:, 0].min()*R.PX, y + 30 + P2[:, 1].max()*R.PX
            R.draw(img, [(V, col(mat))], iso, (ox, oy))
            t.text((x, y), name.split("_", 1)[1] + (f"  x{q}" if q > 1 else ''), fill=(20, 20, 20), font=f2)
            t.text((x, y + 18 + h + 20), mat, fill=(110, 110, 110), font=f3)
            x += max(w, 150) + 40
        y += 360
    t.text((30, H - 30), 'Each STL is already in its print pose. Grey: tray and coupons. Blue: PLA dummies. Dark: TPU. Tan: EVA templates.',
           fill=(110, 110, 110), font=f2)
    img.save(path)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    K = kit(); rho = {'PLA': 1.24, 'PETG': 1.27, 'TPU': 1.21}
    print(f"{'file':32s}{'qty':>4s}  {'size x y z (mm)':>22s}  {'cm3':>6s}  watertight  material")
    for name, m, q, mat, note in K:
        m.export(os.path.join(OUT, name + '.stl'))
        e = m.extents
        print(f"{name:32s}{q:4d}  {e[0]:6.1f} {e[1]:6.1f} {e[2]:6.1f}  {m.volume/1000:6.2f}  {str(m.is_watertight):10s}  {mat}")
    body = next(m for n, m, *_ in K if n == '03_cell_body'); cap = next(m for n, m, *_ in K if n == '04_cell_cap')
    printed = (body.volume + cap.volume)/1000*1.24
    cav = np.pi*(S.CELL_D/2 - CELL_WALL)**2*(S.CELL_L - CELL_CAP_T - CELL_NUB_H - CELL_FLOOR)/1000
    print(f"dummy cell: printed ~{printed:.1f} g solid PLA; add ~{CELL_G - printed:.0f} g ballast to match {CELL_G:.0f} g; "
          f"cavity {cav:.1f} cm3 (steel BBs ~4.7 g/cm3 poured -> {cav*4.7:.0f} g max)")
    plate_png(K, os.path.join(OUT, 'kit_plate.png')); print('wrote print_kit/kit_plate.png')
