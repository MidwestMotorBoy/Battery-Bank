"""Monolith cover standoffs explained: what the four steel spacers on F.Cu do, and how they differ from the two cover screws.
Run: python monolith_standoff_detail.py   (same venv as monolith_side_renders.py)
-> retired/monolith_side_standoffs.png   (the side tray and its cover standoffs are retired; the cup has none)
   1. 3D view, caps off, cover and screws lifted: the four standoffs (H101-H104) on the board, the two real screws
   2. section through the upper pair (z = 48): cover, 0.2 mm gap, standoff, board, EVA lane, cells, tray
   3. the squeeze: normal vs. cover bent onto the standoffs, and the load path, plus where H101-H104 sit on the board"""
import numpy as np, os
from PIL import Image
import monolith_shell as S, monolith_parts as P
from monolith_side_renders import Sheet, camera, proj, C, INK, MUTED, RULE, ACCENT, LEADER, SS, assembly

HERE = os.path.dirname(os.path.abspath(__file__))
STEEL, SCREW = (168, 170, 176), (90, 92, 98)

def cyl_x(y, z, x0, x1, r, r_in=0.0):
    """cylinder (or tube) along x from x0 to x1, centred at (y, z)"""
    cur = [P.circ_pts(0, 0, r, 0.15)] + ([P.circ_pts(0, 0, r_in, 0.15)] if r_in else [])
    V = P.build(cur, [x0, x1], lambda k, x, y_: P.circ_in(x, y_, 0, 0, r) & ~(P.circ_in(x, y_, 0, 0, r_in) if r_in else False))
    V = V[..., [2, 1, 0]][:, ::-1]                 # axis z -> x (swap flips the winding, so reverse it)
    return V + [0, y, z]
def standoffs():
    """Wuerth WA-SMSI 9774035243R: steel tube 3.5 mm tall, M2 internal thread (unused here), reflow-soldered to F.Cu"""
    return np.vstack([cyl_x(y, z, S.sb_xb1, S.sb_xb1 + S.sb_standoff_h, S.SB_STANDOFF_D / 2, 1.0) for y, z in S.SB_STANDOFFS])
def screws(dx=0.0):
    """the two real fasteners: M2 screws through the cover into heat-set inserts in the wedge's two corner bosses"""
    out = []
    for sy in (-1, 1):
        y, z = sy * S.sb_pillar_y, S.sb_screw_z
        out.append(cyl_x(y, z, S.sb_x_cv1 + dx, S.sb_x_cv1 + 1.3 + dx, 1.9))           # pan head
        out.append(cyl_x(y, z, S.sb_x_cv0 - S.SB_INSERT_L + dx, S.sb_x_cv1 + dx, 1.0))  # shank
    return np.vstack(out)

if __name__ == '__main__':
    A = assembly(); get = {k: (V, c) for k, V, c in A if k in ('shell', 'board', 'cover', 'frame', 'cell')}
    sh = Sheet(2700, 1500)
    sh.header('Cover standoffs: what the four "screw mounts" on the board do',
              'They are not screws, and nothing screws into them. Four steel spacers soldered to the cover side of the board stand '
              '0.2 mm under the aluminium cover. If the pack is squeezed or lands flat, the cover bends onto them instead of onto the parts.')

    # ---------- 1. 3D: caps off, cover and screws lifted ----------
    sh.panel_title(40, 128, '1.  Where they are (caps off, cover and its screws lifted)', 1240)
    SIDE = 56.0     # the cover is slid off to the right so the standoffs show; the screws only lift out of their bosses
    parts = [get['shell'], get['board'], (standoffs(), STEEL), (get['cover'][0] + [6.0, SIDE, 0], C['cover']),
             (screws(9.0), SCREW)]
    R1 = camera((1.0, -0.55, 0.42)); o1 = (500, 860); px1 = 5.6
    sh.render(parts, R1, o1, px1); pj = proj(R1, o1, px1)
    xs = S.sb_xb1 + S.sb_standoff_h
    names = {(-15.0, 28.0): 'H101', (15.0, 28.0): 'H102', (-15.0, 48.0): 'H103', (15.0, 48.0): 'H104'}
    items = []
    for (y, z), n in names.items():
        kx, ky = S.kicad(y, z)
        items.append((pj((xs, y, z)), f'{n} standoff  (KiCad {kx:.0f}, {ky:.1f})'))
    sh.callouts(items, 300, 'l', 330, size=14)
    sh.callouts([(pj((S.sb_x_cv1 + 6.0, SIDE, 45)), 'Aluminium cover, slid aside here.\nIn the pack it sits 0.2 mm above\nthe four standoff tops.'),
                 (pj((S.sb_x_cv1 + 9.0 + 1.3, S.sb_pillar_y, S.sb_screw_z)), 'The only screws: 2 x M2 through the\ncover into the wedge bosses, hidden\nunder the bottom cap. Not through\nthe board.'),
                 (pj((S.sb_xb1, 5, 66)), 'Board: held by the tray guides, the top\nstops and the shim. Not screwed down.')],
                1040, 'r', 300, size=14)

    # ---------- 2. section through the upper pair ----------
    zc = 48.0 + 0.03
    sh.panel_title(40, 1000, f'2.  Section through H103 / H104 (z = 48 mm), cover side up', 1240)
    tmp = Sheet(2700, 1500)
    pxs = 15.0; os_ = (690, 1330)                     # screen = (ox + px*y, oy - px*(x - X0))
    X0 = 17.0
    Asec = [(k, V - [X0, 0, 0], c) for k, V, c in A if k in ('shell', 'board', 'cover', 'frame', 'cell', 'insul', 'wrap')]
    Asec.append(('stand', standoffs() - [X0, 0, 0], STEEL))
    tp = tmp.section(Asec, 2, zc, 1, 0, os_, pxs)
    crop = (40 * SS, 1045 * SS, 1300 * SS, 1440 * SS)
    sh.img.paste(tmp.img.crop(crop), crop[:2])
    T = lambda y, x: tp(y, x - X0)
    # indicative tall part + gap pad between the standoffs
    a, b = T(-4.0, S.sb_xb1 + 3.1), T(4.0, S.sb_xb1)
    sh.rect(a[0], a[1], b[0], b[1], fill=(80, 80, 86), outline=INK, width=1)
    g0, g1 = T(-4.0, S.sb_x_cv0), T(4.0, S.sb_xb1 + 3.1)
    sh.rect(g0[0], g0[1], g1[0], g1[1], fill=(150, 200, 230), outline=INK, width=1)
    sh.callouts([(T(0, S.sb_xb1 + 1.5), 'A tall part (inductor, 3.1 mm),\nindicative only'),
                 (T(-2, S.sb_x_cv0 - 0.25), '0.5 mm gap pad: heat path\nto the cover (indicative)')], 300, 'l', 1060, size=13)
    sh.callouts([(T(15.0 + 1.3, S.sb_xb1 + 2.0), 'H104: steel spacer, 3.5 mm tall,\nsoldered to F.Cu (its M2 thread is unused)'),
                 (T(15.0, S.sb_xb1 + S.sb_standoff_h + 0.1), '0.2 mm gap to the cover'),
                 (T(19.0, S.sb_x_cv0 + 0.5), '1.0 mm aluminium cover'),
                 (T(19.5, S.sb_xb1 - 0.8), '1.6 mm board'),
                 (T(10.9, S.sb_xb0 - 1.2), 'TPU frame bar behind the board:\nthe load goes on into the cells'),
                 (T(5.0, S.sb_xb0 - 3.4), 'cells')], 1070, 'r', 1060, size=13)
    sh.dim(T(21.0, S.sb_xb1), T(21.0, S.sb_x_cv0), 22, f'{S.sb_x_cv0 - S.sb_xb1:.1f}', 13)

    # ---------- 3. the squeeze ----------
    x0 = 1360
    sh.panel_title(x0, 128, '3.  What they do when the pack is squeezed', 1300)
    def diagram(ox, oy, bent, title):
        sx, sz = 9.0, 26.0                      # schematic scale: wide, and tall to show 0.2 mm gaps (not to scale)
        Y = lambda y: ox + sx * y
        H = lambda x: oy - sz * x               # x measured up from the board's F.Cu
        sh.text(ox - 22 * sx, oy - 220, title, 16, True)
        sh.rect(Y(-22), H(0), Y(22), H(-1.6), fill=C['board'])                      # board
        for y in (-15, 15):                                                          # standoffs
            sh.rect(Y(y - 2.2), H(3.5), Y(y + 2.2), H(0), fill=STEEL, outline=INK)
        for y0, h in ((-5, 3.1), (4, 2.6), (-11, 1.2), (9, 0.9)):                   # parts
            sh.rect(Y(y0 - 2.5), H(h), Y(y0 + 2.5), H(0), fill=(80, 80, 86))
        sh.rect(Y(-7.5), H(3.7 if not bent else 3.45), Y(-2.5), H(3.1), fill=(150, 200, 230))   # gap pad on the tall part
        ys = np.linspace(-22.5, 22.5, 120)
        if bent:   # cover bent onto the standoffs: sag limited by the standoffs, worst in the middle
            sag = np.where(np.abs(ys) <= 15, 0.2 + 0.25 * (1 - (ys / 15) ** 2), 0.2 * (22.5 - np.abs(ys)) / 7.5)
        else:
            sag = np.zeros_like(ys)
        top = [(Y(y), H(3.7 - s)) for y, s in zip(ys, sag)]
        bot = [(Y(y), H(4.7 - s)) for y, s in zip(ys, sag)][::-1]
        sh.g.polygon([(a * SS, b * SS) for a, b in top + bot], fill=C['cover'], outline=(60, 60, 66))
        for y in (-10.9, 10.9):                                                      # EVA lanes + cells below
            sh.rect(Y(y - 3), H(-1.6), Y(y + 3), H(-2.6), fill=C['eva'])
            sh.g.ellipse([Y(y - 10.75) * SS, H(-2.6) * SS, Y(y + 10.75) * SS, (H(-2.6) + 70) * SS], fill=C['cell'])
        return Y, H
    Y1, H1 = diagram(x0 + 260, 520, False, 'Normal: nothing touches')
    sh.callouts([((Y1(15), H1(3.6)), '0.2 mm between each standoff and the cover'),
                 ((Y1(-5), H1(3.4)), 'gap pad only lightly touches the parts')], x0 + 520, 'r', 300, size=14)
    Y2, H2 = diagram(x0 + 260, 960, True, 'Squeezed (strap, sat on, flat drop): the cover bends')
    sh.callouts([((Y2(15), H2(3.5)), 'Cover lands on the standoffs after 0.2 mm'),
                 ((Y2(-5), H2(3.3)), 'between them it can sag only a little more,\nso the parts see a squeezed gap pad,\nnot the cover itself'),
                 ((Y2(10.9), H2(-2.1)), 'load path: cover -> standoffs -> board\n-> frame bars -> cells -> tray -> TPU')], x0 + 520, 'r', 760, size=14)
    sh.text(x0, 1130, 'Schematic, not to scale (heights exaggerated about 3x to show the 0.2 mm gaps).', 14, fill=MUTED)
    notes = ['Why they are needed: by rough plate maths a 200 N point load on the 1 mm cover bends it about 0.7 mm,',
             'which is more than the 0.5 mm gap pad and would push straight onto the inductors and USB-C bodies.',
             'The standoffs cap that travel at 0.2 mm and carry the load through solid steel into the board.',
             'They are on the BOM as H101-H104 (Wurth WA-SMSI 9774035243R, LCSC C5266183), placed and locked by',
             'Production/tools/make_board.py --standoffs. The upper pair keeps at least 5 mm from the BLE module.']
    for i, s in enumerate(notes): sh.text(x0, 1175 + 24 * i, s, 14, fill=INK)
    sh.line([(40, 1460), (2660, 1460)], RULE, 1.5)
    sh.legend([('tray', C['shell']), ('board', C['board']), ('standoff (steel)', STEEL), ('screw', SCREW), ('Al cover', C['cover']),
               ('TPU frame', C['frame']), ('cells', C['cell']), ('gap pad (indicative)', (150, 200, 230)), ('board parts (indicative)', (80, 80, 86))],
              40, 1470, 13)
    sh.save('monolith_side_standoffs.png')
    print('wrote monolith_side_standoffs.png')
