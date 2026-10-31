"""Fit coupons for the Monolith cup: cheap MJF PA12 prints that test the risky fits before the full cup is ordered
(docs/production/p0-assembly.md, Open items: Fit). Geometry comes from monolith_cup.py, so a coupon is the real part's
feature, not a redraw.
  A  USB-C seal-bore ladder: a 1.85 mm top-wall plate with five bores at 0.05-0.25 mm squeeze a side, each over the
     housing pocket and lead-in, the squeeze debossed beside it, and a 1.2 mm skirt so the plate stays flat. Push a
     loose connector in from the pocket side; pick the bore that seals (1 m dunk) and still lets the board float.
  B  Cup mouth + cap: the bottom 14 mm of the cup, closed by a lid, with the real cap, O-ring and M2 screws. Squeeze in
     the middle of each flat (clay or feelers), dunk at 1 m / 30 min, pull-test the cap, -50 kPa jar test.
  C  Core: the real carrier, the four clip-on rail blocks and the four TPU sleeves (no coupon: the parts themselves).
Run: python monolith_coupons.py   -> coupons/*.stl, coupons/monolith_coupons.png"""
import os, numpy as np
import manifold3d as M3
import monolith_shell as S, monolith_cup as K, monolith_side_renders as RR
from monolith_render import camera
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'coupons')
MF, CS = M3.Manifold, M3.CrossSection
pz, rect, rrect, U = K.pz, K.rect, K.rrect, K.U

# ---------------- A: seal-bore ladder ----------------
LADDER_SQ = (0.05, 0.10, 0.15, 0.20, 0.25)   # squeeze a side; the cup uses K.USB_SQ (0.15)
LADDER_PITCH = 9.5                            # bore to bore along x (bores are 4.27 x 10.05, pockets ~4.6 x 10.5)
LADDER_Y = 9.5                                # plate half-width across the bores
SKIRT_H, SKIRT_T = 4.0, K.WALL                # stiffening skirt under the plate, like the cup's side walls
TEXT_H, TEXT_D = 2.4, 0.5                     # debossed squeeze labels on the outer face
def ladder():
    n = len(LADDER_SQ); x1 = n * LADDER_PITCH; z0, z1 = K.Z_TOP0, K.Z_TOP1
    out = rrect(0, x1, -LADDER_Y, LADDER_Y, 2.0)
    m = pz(out, z0, z1) + (pz(out, z0 - SKIRT_H, z0) - pz(out.offset(-SKIRT_T, M3.JoinType.Round), z0 - SKIRT_H - 1, z0 + 0.01))
    for i, sq in enumerate(LADDER_SQ):
        dx = (i + 0.5) * LADDER_PITCH - K.PORT_X      # the cup's port 1 section, moved to this slot (centred on y = 0)
        mv = lambda c: c.translate((dx, -K.PORT_YS[1]))
        bore = mv(K.usb_bore(K.PORT_YS[1], K.USB_SQ - sq)); pocket = mv(K.usb_pocket(K.PORT_YS[1]))
        m = m - MF.extrude(bore, 4).translate((0, 0, z0 - 1)) - pz(pocket, z0 - SKIRT_H - 1, K.Z_POCKET)
        m = m - MF.batch_hull([pz(pocket, K.Z_POCKET - 0.01, K.Z_POCKET), pz(bore, K.Z_POCKET + K.POCKET_LEAD - 0.01, K.Z_POCKET + K.POCKET_LEAD)])
        lab = K.text_cs(f'{round(sq * 100):02d}', TEXT_H, (i + 0.5) * LADDER_PITCH, LADDER_Y - 1.0 - TEXT_H / 2 - 0.3)
        m = m - pz(lab, z1 - TEXT_D, z1 + 1)
    return m

# ---------------- B: cup mouth + cap ----------------
MOUTH_H, LID_T = 14.0, 1.5                    # cup section above the mouth, lid on top
def mouth():
    z1 = K.Z_MOUTH + MOUTH_H
    sec = K.cup() ^ pz(K.cs_out.offset(1, M3.JoinType.Round), K.Z_MOUTH - 1, z1)
    return sec + pz(K.cs_out, z1 - 0.01, z1 + LID_T) - pz(K.text_cs('B', 5.0, 0, 0), z1 + LID_T - 0.5, z1 + LID_T + 1)

def coupons():
    """[(file stem, description, material, manifold)]"""
    return [('A_seal_bore_ladder', 'Seal-bore ladder: squeeze 05-25 (x 0.01 mm a side)', 'MJF PA12', ladder()),
            ('B1_cup_mouth', 'Cup mouth, bottom 14 mm, lidded', 'MJF PA12', mouth()),
            ('B2_cap', 'Bottom cap (the real part)', 'MJF PA12', K.cap()),
            ('C1_carrier', 'Cell carrier (the real part)', 'MJF PA12', K.carrier()),
            ('C2_rails', 'Clip-on rail blocks, 4 (the real parts)', 'MJF PA12', K.rails()),
            ('C3_sleeves', 'Post sleeves, 4', 'TPU 95A', K.sleeves())]

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    C = coupons(); rows = []
    for stem, desc, mat, m in C:
        K.write_stl(os.path.join(OUT, f'monolith_coupon_{stem}.stl'), K.tris(m))
        b = np.array(m.bounding_box()); sz = b[3:] - b[:3]
        g = m.volume() / 1000 * (1.2 if mat.startswith('TPU') else 1.01)
        rows.append([stem.split('_')[0], desc, mat, f'{sz[0]:.1f} x {sz[1]:.1f} x {sz[2]:.1f}', f'{g:.1f}'])
        print(f'{stem:22s} {desc:52s} {mat:9s} {sz[0]:5.1f} x {sz[1]:5.1f} x {sz[2]:5.1f} mm  {g:5.1f} g')
    # preview sheet
    sh = RR.Sheet(2700, 1100)
    sh.header('Monolith fit coupons', 'Print these before the full cup: the USB-C seal bores, the cap seal and the core fit. '
              'Same geometry as monolith_cup.py. Files: hardware/mechanical/coupons/.')
    col = dict(A=K.C['cup'], B1=K.C['cup'], B2=K.C['cap'], C1=K.C['carrier'], C2=K.C['rails'], C3=K.C['sleeve'])
    R = camera((0.9, -1.0, 0.8)); RB = camera((0.9, -1.0, -0.7))
    def ctr(m):
        b = np.array(m.bounding_box()); return -(b[:3] + b[3:]) / 2
    panels = [('A  seal-bore ladder: outer face, and from below (the pockets)', [('A', C[0][3])], None, 7.0),
              ('B  cup mouth + cap, O-ring, M2 screws', [('B1', C[1][3]), ('B2', C[2][3].translate((0, 0, -12)))], R, 4.5),
              ('C  carrier, rail blocks, sleeves', [('C1', C[3][3]), ('C2', C[4][3]), ('C3', C[5][3])], R, 3.2)]
    for i, (title, parts, cam, px) in enumerate(panels):
        x = 40 + i * 880; sh.panel_title(x, 128, title, 840)
        off = ctr(U(*[m for _, m in parts]))
        for c, o in (((R, (x + 420, 330)), (RB, (x + 420, 620))) if cam is None else ((cam, (x + 420, 470)),)):
            sh.render([(K.tris(m.translate(off)), col[k]) for k, m in parts], c, o, px)
    sh.table(40, 800, ['', 'Coupon', 'Material', 'Size (mm)', '>g'], rows, [80, 900, 200, 300, 100], 14, rh=30)
    K.save(sh, os.path.join('coupons', 'monolith_coupons.png'))
