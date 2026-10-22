"""Monolith heatsink-free cup: an MJF PA12 cup closed on five sides (the USB-C bores in its top wall), the bench-built core
pushed in from the bottom until the ports seat, and a bottom cap that seals radially with one O-ring. No aluminium:
the power stage dumps its heat into the cells through thermal vias and a dispensed gap filler.
Reuses monolith_hybrid.py's helpers and the current side-tray model's cells, board, nickel and BLE envelopes.
Run: python monolith_cup.py CURRENT_MECH_DIR [OUT_DIR] [all|exploded|sections|compare|none]
-> OUT_DIR/stl/cup_*.stl, cup_exploded.png, cup_sections.png, cup_vs_current.png"""
import os, sys, numpy as np
CUR = os.path.abspath(sys.argv[1]); OUT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.getcwd())
WHICH = sys.argv[3] if len(sys.argv) > 3 else 'all'
sys.argv = [sys.argv[0], CUR, OUT, 'none']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import monolith_hybrid as H
import monolith_shell as S, monolith_parts as P, monolith_side_renders as RR
from monolith_render import camera, board_g, vol, CELL_G
from PIL import Image
M3, CS, MF = H.M3, H.CS, H.MF
rect, rrect, circ, stad, hull, pz, U, tris, write_stl = H.rect, H.rrect, H.circ, H.stad, H.hull, H.pz, H.U, H.tris, H.write_stl
ROUND = M3.JoinType.Round

# ---------------- parameters (mm); same frame as the side tray ----------------
PR, CR, CELLS = H.PR, H.CR, H.CELLS
WALL = 1.2                         # cup wall, as the current tray
YI = PR + CR + 0.2                 # inside half-width (cells + 0.2)
X_IN = S.sb_xb1 + S.SB_OUT_H + 0.5 # inside face over the board: tallest part + 0.5
R_FRONT = 4.0                      # bore corner radius on the board side (radial O-ring: >= 2 x cord)
Z_TOP0, Z_TOP1 = S.SB_H - S.SB_END_T, S.SB_H          # closed top wall with the port bores (as the current tray)
Z_MOUTH = -3.0                     # open bottom end of the cup
Z_SKIRT1 = S.sb_zb0 - 0.3          # cap skirt top: just under the board's bottom edge
CAP_T = 1.6                        # cap plate below the mouth (lands on the cup rim: hard stop)
SKIRT_T = 2.1                      # radial skirt wall
ORING_CS, GROOVE_D, GROOVE_Z = 2.0, 1.4, (-0.4, 2.2)  # 2.0 cord, groove 2.6 wide x 1.4 deep (+0.1 gap) -> 25 % squeeze
SCREW_X, SCREW_Z = 16.0, -2.0      # two M2 radially through the side walls into skirt bosses, below the seal
VENT_Y, VENT_Z = 0.0, 14.0         # ePTFE vent on the board-side face (the leak-test port before it goes on)
FR_B0, FR_B1, FR_T0, FR_T1 = 4.6, 6.2, 77.8, Z_TOP0   # carrier frames
FILL_Z = (27.0, 53.0)              # gap filler, board B.Cu to the two front cells, over the power stages
RAIL_GAP = (23.0, 56.0)            # board rails stop here so the filler reaches the cell tangents
BUMP_T_TOP, BUMP_T_BOT, BUMP_BAND, BUMP_WALL = 8.0, 4.0, 9.0, 2.0
PORT_X, PORT_YS = H.PORT_X, H.PORT_YS

cs_in = hull(*[circ(x, y, CR + 0.2) for x, y in CELLS], rrect(-1, X_IN, -YI, YI, R_FRONT))
cs_out = cs_in.offset(WALL, ROUND)
def cyly(x, z, r, y0, y1):
    return MF.extrude(circ(z, x, r), y1 - y0).transform([[0, 1, 0, 0], [0, 0, 1, y0], [1, 0, 0, 0]])   # section (z, x), along y

# ---------------- parts ----------------
def cup():
    m = pz(cs_out, Z_MOUTH, Z_TOP1) - pz(cs_in, Z_MOUTH - 1, Z_TOP0)
    for py in PORT_YS:
        m = m - MF.extrude(stad(PORT_X, py, H.BORE_H, H.BORE_W), 4).translate((0, 0, Z_TOP0 - 1))
    m = m - H.cylx(VENT_Y, VENT_Z, 1.5, X_IN - 0.5, X_IN + WALL + 0.5)
    m = m - cyly(SCREW_X, SCREW_Z, 1.1, -(YI + WALL + 0.5), YI + WALL + 0.5)
    return m
def cap():
    plate = pz(cs_out, Z_MOUTH - CAP_T, Z_MOUTH)
    skirt = pz(CS.batch_boolean([cs_in.offset(-0.1, ROUND), cs_in.offset(-0.1 - SKIRT_T, ROUND)], M3.OpType.Subtract), Z_MOUTH - 0.01, Z_SKIRT1)
    bosses = [cyly(SCREW_X, SCREW_Z, 2.6, -(YI - 0.1), -(YI - 5.1)), cyly(SCREW_X, SCREW_Z, 2.6, YI - 5.1, YI - 0.1)]
    m = U(plate, skirt, *bosses)
    m = m - pz(CS.batch_boolean([cs_in.offset(0.5, ROUND), cs_in.offset(-0.1 - GROOVE_D, ROUND)], M3.OpType.Subtract), *GROOVE_Z)
    for s in (-1, 1): m = m - cyly(SCREW_X, SCREW_Z, 0.8, -(YI + 1), YI + 1)    # M2 pilots
    return m
def oring(): return pz(CS.batch_boolean([cs_in, cs_in.offset(-0.1 - GROOVE_D, ROUND)], M3.OpType.Subtract), GROOVE_Z[0] + 0.3, GROOVE_Z[1] - 0.3)
def screws():
    e = YI + WALL
    return U(cyly(SCREW_X, SCREW_Z, 1.0, -e, -(YI - 4.0)), cyly(SCREW_X, SCREW_Z, 1.9, -(e + 1.3), -e),
             cyly(SCREW_X, SCREW_Z, 1.0, YI - 4.0, e), cyly(SCREW_X, SCREW_Z, 1.9, e, e + 1.3))
def pad():
    m = pz(CS.batch_boolean([H.cs_cells.offset(-0.4, ROUND), cs_in.offset(-0.1 - SKIRT_T - 0.3, ROUND)], M3.OpType.Intersect), Z_MOUTH, FR_B0)
    return m - U(*[cyly(SCREW_X, SCREW_Z, 3.0, -YI, -(YI - 5.6)), cyly(SCREW_X, SCREW_Z, 3.0, YI - 5.6, YI)])
def carrier():
    frame = CS.batch_boolean([H.cs_cells] + [circ(x, y, H.WIN_R) for x, y in CELLS], M3.OpType.Subtract)
    m = [pz(frame, FR_B0, FR_B1), pz(frame, FR_T0, FR_T1),
         pz(rect(-PR - CR, -PR - CR + 5.2, -1.5, 1.5), FR_B0, FR_T1),
         pz(rect(-1.5, 1.5, PR + CR - 5.2, PR + CR), FR_B0, FR_T1), pz(rect(-1.5, 1.5, -PR - CR, -PR - CR + 5.2), FR_B0, FR_T1)]
    for s in (-1, 1):
        r = rect(PR + CR + 0.15, S.sb_xb0, *sorted((s*S.SB_BAR_Y[0], s*S.SB_BAR_Y[1])))
        m += [pz(r, FR_B0, RAIL_GAP[0]), pz(r, RAIL_GAP[1], FR_T1)]
    m += [H.cylx(s*8.6, z, 1.0, S.sb_xb0 - 0.5, S.sb_xb1 + 0.6) for s in (-1, 1) for z in (14.0, 68.0)]
    return U(*m)
def filler():
    blk = MF.cube((S.sb_xb0 - 19.0, 2*18.5, FILL_Z[1] - FILL_Z[0])).translate((19.0, -18.5, FILL_Z[0]))
    cells = U(*[pz(circ(x, y, CR), FILL_Z[0] - 1, FILL_Z[1] + 1) for x, y in CELLS])
    keep = pz(CS.batch_boolean([rect(19.0, S.sb_xb0, -16.0, -7.0), rect(19.0, S.sb_xb0, 7.0, 16.0)], M3.OpType.Add), FILL_Z[0], FILL_Z[1])
    return (blk ^ keep) - cells
cs_pack = cs_out
def bumper(top):
    out = cs_pack.offset(BUMP_WALL, ROUND)
    ring = CS.batch_boolean([out, cs_pack], M3.OpType.Subtract)
    if top:
        band = pz(ring, Z_TOP1 - BUMP_BAND, Z_TOP1)
        slab = pz(out, Z_TOP1, Z_TOP1 + BUMP_T_TOP) - pz(rrect(PORT_X - 4.5, PORT_X + 4.5, -14.0, 14.0, 2.0), Z_TOP1 - 0.1, Z_TOP1 + BUMP_T_TOP + 1)
    else:
        z0 = Z_MOUTH - CAP_T
        band = pz(ring, z0, z0 + BUMP_BAND)
        slab = pz(out, z0 - BUMP_T_BOT, z0)
    return band, slab

# ---------------- assembly ----------------
C = dict(H.C, cup=(214, 214, 208), cap=(170, 186, 200), filler=(232, 150, 200), oring=(200, 60, 60))
def assembly():
    A = [('cup', tris(cup()), C['cup'])]
    cell = P.cell_solid()
    for x, y in CELLS: A.append(('cell', H.mv(cell, (x, y, S.sb_z_cell0)), C['cell']))
    A += [('carrier', tris(carrier()), C['carrier']), ('filler', tris(filler()), C['filler']),
          ('nickel', P.nickel_strips('strips'), C['nickel']), ('tails', P.nickel_strips('tails'), C['tail']),
          ('board', P.side_board_dummy(), C['board']), ('ble', P.ble_module(), C['ble']),
          ('pad', tris(pad()), C['pad']), ('oring', tris(oring()), C['oring']), ('cap', tris(cap()), C['cap']),
          ('screw', tris(screws()), C['screw']), ('vent', tris(H.cylx(VENT_Y, VENT_Z, 5.5, X_IN + WALL, X_IN + WALL + 0.3)), C['vent'])]
    for top in (False, True):
        b, s = bumper(top); k = 'bumpt' if top else 'bumpb'
        A += [(k + '_band', tris(b), C['bump']), (k + '_slab', tris(s), C['bslab'])]
    return A
group = H.group
PARTS = [(1, 'Cell carrier: frames, spines, split rails, pegs', 'MJF PA12', 'carrier'), (2, 'Cells C1-C4, welded 4S', 'EVE INR21700-58E', 'cell'),
         (3, 'Nickel series strips (3)', 'nickel 0.15', 'nickel'), (4, 'Nickel tongues: PACK+/- (power + Kelvin), CELL1-3', 'nickel 0.15 / 0.2', 'tails'),
         (5, 'Gap filler, board to the front cells (dispensed)', '~3 W/mK, 2.6 g/cm3', 'filler'),
         (6, 'Board 1.6 mm, thermal vias under the power stages', 'FR4, 6 layers', 'board'),
         (7, 'Cup: 5 closed sides, port bores in the top wall', 'MJF PA12, 1.2 mm', 'cup'),
         (8, 'Pad on the cap: preloads the core, inner crush zone', 'TPU 95A, 30 % gyroid', 'pad'),
         (9, 'O-ring, 2.0 mm cord (radial)', 'silicone 60A', 'oring'), (10, 'Bottom cap: plate + skirt, groove, screw bosses', 'MJF PA12', 'cap'),
         (11, 'Screws M2 (2), radial, below the seal', 'stainless', 'screw'), (12, 'Pressure vent (after the leak test)', 'ePTFE', 'vent'),
         (13, 'Bottom bumper, 4 mm', 'TPU 95A', 'bumpb'), (14, 'Top bumper, port well', 'TPU 95A', 'bumpt')]
NUM = {k: n for n, _, _, k in PARTS}
RHO = dict(cup=1.01, cap=1.01, carrier=1.01, screw=7.9, oring=1.15, filler=2.6, nickel=8.9, tails=8.9, vent=1.0)
def masses(A):
    m = {}
    for k, V, _ in A:
        g = group(k)
        r = RHO.get(g, 1.2*0.30 if (g == 'pad' or k.endswith('_slab')) else (1.2 if k.endswith('_band') else None))
        if r is None: continue
        m[g] = m.get(g, 0) + vol(V) * r
    m['board'] = board_g(S.sb_board_area, S.SB_PCB_T); m['cell'] = 4 * CELL_G
    return m
def current_masses():
    """the side tray, corrected: TPU parts at 1.2 g/cm3 (the model uses 1.0), plus what it doesn't model"""
    m, _ = RR.masses(RR.assembly(), None)
    for k in ('cage', 'frame', 'holder'): m[k] *= 1.2
    m['gappad'] = 1.0                       # 0.5 mm gap pad under the cover
    m['unmodelled'] = 0.5 + 0.15            # 2 x M2 + 2 inserts; silicone bead
    return m

# ---------------- sheets ----------------
SS, INK, MUTED, RULE, ACCENT = RR.SS, RR.INK, RR.MUTED, RR.RULE, RR.ACCENT
LEG = [('PA12 cup', C['cup']), ('PA12 cap', C['cap']), ('PA12 carrier', C['carrier']), ('cells', C['cell']), ('board', C['board']),
       ('BLE module', C['ble']), ('gap filler', C['filler']), ('O-ring', C['oring']), ('screw', C['screw']),
       ('TPU pad / bumper slab', C['pad']), ('TPU bumper band', C['bump']), ('nickel strip', C['nickel']), ('nickel tongue', C['tail'])]
def save(sh, name): sh.img.resize((sh.W, sh.H), Image.LANCZOS).save(os.path.join(OUT, name)); print('wrote', name)
def size(A):
    V = np.vstack([V for _, V, _ in A]).reshape(-1, 3); return V.max(0) - V.min(0)
def balloons(sh, pid, gid, BAL, dist=80):
    for g_ in dict.fromkeys(gid):
        a = RR.visible_anchor(pid, [i for i, x in enumerate(gid) if x == g_])
        if a is None or g_ not in NUM: continue
        ax, ay = a; ang = np.radians(BAL.get(g_, 0)); d = dist + (60 if g_.startswith('bump') else 0)
        bx, by = ax + d*np.cos(ang), ay - d*np.sin(ang); v = np.array([bx - ax, by - ay]); v /= np.linalg.norm(v)
        sh.line([(ax, ay), (bx - v[0]*13, by - v[1]*13)], ACCENT, 1.2); sh.dot(ax, ay, 3, ACCENT); sh.balloon(bx, by, NUM[g_])

def sheet_exploded(A, m):
    total = sum(m.values()); w, d, L = size(A)
    sh = RR.Sheet(2700, 1400)
    sh.header('Heatsink-free cup: one radial O-ring, no aluminium',
              'The bench-built core goes in from the bottom until the USB-C faces seat in the closed top wall; a bottom cap seals it. '
              f'The power stage dumps its heat into the cells. Pack {w:.1f} x {d:.1f} x {L:.1f} mm, about {total:.0f} g.')
    sh.panel_title(40, 128, 'Assembled', 640)
    R = camera((1.0, -1.1, 0.65)); o1 = (250, 660); pxs = 5.0
    sh.render([(V, c) for _, V, c in A], R, o1, pxs); pj = RR.proj(R, o1, pxs)
    sh.callouts([(pj((PORT_X, 9, Z_TOP1 + BUMP_T_TOP)), 'Port well through the top bumper'),
                 (pj((X_IN + WALL, -8, 50)), 'Board face: plain 1.2 mm PA12,\nno cover, no seam'),
                 (pj((X_IN + WALL, 0, VENT_Z)), 'ePTFE vent, fitted last:\nits hole is the leak-test port'),
                 (pj((X_IN + WALL + 2, -YI, Z_MOUTH - CAP_T - BUMP_T_BOT + 1)), '4 mm bottom bumper over the cap\n(the pad inside adds the rest of the stroke)')],
                475, 'r', 150)
    sh.panel_title(780, 128, 'Exploded, in assembly order', 1180)
    EX = dict(cell=(0, 0, -75), carrier=(0, 0, -75), nickel=(0, 0, -75), tails=(0, 0, -75), board=(16, 0, -75), ble=(16, 0, -75),
              filler=(8, 0, -75), cup=(0, 0, 25), pad=(0, 0, -118), oring=(0, 0, -136), cap=(0, 0, -152), screw=(0, 0, -152), vent=(14, 0, 25))
    ex, gid = [], []
    for k, V, c in A:
        g_ = group(k); dd = EX.get(g_, (0, 0, -182) if g_ == 'bumpb' else (0, 0, 50))
        ex.append((H.mv(V, dd), c)); gid.append(g_)
    R2 = camera((0.5, -1.25, 0.32)); o2 = (1180, 690); px2 = 3.0
    pid = sh.render(ex, R2, o2, px2)
    balloons(sh, pid, gid, dict(cup=160, carrier=150, cell=200, nickel=330, tails=10, filler=20, board=0, pad=200, oring=0,
                                cap=200, screw=340, vent=0, bumpb=200, bumpt=170), 70)
    x0 = 2010; sh.panel_title(x0, 128, 'Parts', 650)
    rows = [[str(n), name, mat, f'{m.get(k, 0):.1f}' if m.get(k, 0) >= 0.05 else '<0.1'] for n, name, mat, k in PARTS]
    rows.append(['', 'Pack total', '', f'{total:.1f}'])
    y = sh.table(x0, 176, ['#', 'Part', 'Material', '>g'], rows, [36, 344, 200, 70], 13, bold_last=True, rh=26)
    for i, s in enumerate(('Board mass is estimated (FR4 + 6-layer copper); parts on it are not included.',
                           'TPU pad and bumper slabs at 30 % gyroid; bumper bands solid.',
                           'Not drawn: the label (embossed, or a small plate), RTV-free port bores as today.')):
        sh.text(x0, y + 14 + 24*i, s, 13, fill=MUTED)
    sh.line([(40, 1330), (2660, 1330)], RULE, 1.5); sh.legend(LEG, 40, 1350, 14)
    save(sh, 'cup_exploded.png')

def sheet_sections(A):
    core = [(k, V, c) for k, V, c in A if not k.startswith('bump')]
    sh = RR.Sheet(2700, 1300)
    sh.header('Cup sections', 'Cut from the same meshes as the STLs. Board and USB-C are envelopes; parts on the board are not drawn. '
              'The O-ring is drawn as squeezed.')
    z_a = 40.0; pxa = 10.0
    sh.panel_title(40, 128, f'A-A   across the pack through the gap filler (z = {z_a:.0f} mm), from the port end', 1380)
    oa = (600, 600); tp = sh.section(core, 2, z_a, 0, 1, oa, pxa)
    for (x, y), nm in zip(CELLS, [S.SB_CELLS[k][0] for k in S.SB_CELLS]):
        q = tp(x, y); sh.text(q[0], q[1], nm, 22, True, fill='white', anchor='mm')
    sh.callouts([(tp(-YI - WALL/2, 6), '1.2 mm MJF PA12 cup wall,\nclosed all round'),
                 (tp(-PR - CR + 2.5, 0), 'Carrier spine (the core is rigid)'),
                 (tp(0, PR + CR - 2), 'Side spine')], 300, 'l', 230)
    sh.callouts([(tp(X_IN + WALL/2, 0), 'Board face: just the cup wall,\n0.5 mm over the tallest part'),
                 (tp(S.sb_xb0 + 0.8, -2), 'Board, fixed to the carrier;\nthermal vias under the power stages'),
                 (tp(23.6, -11.45), 'Gap filler: B.Cu to the two front cells.\nThe cells (~270 J/K) are the heat sink'),
                 (tp(23.6, 11.45), 'Rails stop over the filler zone\n(they carry the board above and below it)'),
                 (tp(X_IN - 1, -YI + 1), 'Bore corners r 4 for the O-ring')], 1010, 'r', 200)
    sh.dim((tp(-YI - WALL, 0)[0], tp(0, -YI - WALL - 4)[1]), (tp(X_IN + WALL, 0)[0], tp(0, -YI - WALL - 4)[1]), 30, f'{X_IN + WALL + YI + WALL:.1f}')
    sh.dim(tp(X_IN + WALL, -YI - WALL), tp(X_IN + WALL, YI + WALL), 40, f'{2*(YI + WALL):.1f}')
    # B-B along the pack through a port
    pxb = 6.4; ob = (1700, 430)
    sh.panel_title(1480, 128, f'B-B   along the pack through a USB-C port (y = {PORT_YS[1]:.1f} mm)', 1180)
    tq = sh.section(core, 1, PORT_YS[1] + 0.02, 2, 0, ob, pxb)
    sh.text(ob[0] + pxb*(Z_MOUTH - CAP_T), 640, 'bottom (cap)', 15, fill=MUTED, anchor='mm'); sh.text(ob[0] + pxb*Z_TOP1, 640, 'port end', 15, fill=MUTED, anchor='mm')
    sh.callouts([(tq(Z_TOP1 - 0.5, PORT_X), 'Ports seat in the closed\ntop wall as the core is\npushed home: no seam here'),
                 (tq(FR_T0 + 0.6, -6), 'Carrier top frame\non the top wall')], 2320, 'r', 200, size=14)
    sh.callouts([(tq(Z_MOUTH - CAP_T/2, 0), 'Cap plate on the rim\n(hard stop)'),
                 (tq((Z_MOUTH + FR_B0)/2, -8), 'TPU pad: preloads the\ncore, inner crush zone'),
                 (tq(sum(GROOVE_Z)/2, X_IN - 0.6), 'O-ring in the skirt\n(radial, 25 %)')], 1660, 'l', 200, size=14)
    # detail: bottom end cut at x = SCREW_X, through both screws
    pxd, (y0, y1, z0, z1) = 15.0, (-27.5, 27.5, -6.0, 9.0); dw, dh = int((y1 - y0)*pxd), int((z1 - z0)*pxd)
    det = RR.Sheet(dw, dh); od = (-y0*pxd, z1*pxd)
    det.section(core, 0, SCREW_X + 0.02, 1, 2, od, pxd)
    DX, DY = 1560, 760
    sh.panel_title(1480, 700, f'C-C   the cap end, cut at x = {SCREW_X:.0f} mm through both screws', 1180)
    sh.img.paste(det.img, (DX*SS, DY*SS)); sh.rect(DX, DY, DX + dw, DY + dh, outline=RULE, width=1)
    td = lambda y, z: (DX + od[0] + pxd*y, DY + od[1] - pxd*z)
    sh.callouts([(td(YI + WALL/2, 6), 'Cup wall'),
                 (td(YI - 0.1 - GROOVE_D/2 - 0.2, sum(GROOVE_Z)/2), 'O-ring between skirt and bore'),
                 (td(YI + WALL + 0.6, SCREW_Z), 'M2 through the wall into a skirt boss,\nbelow the O-ring (outside the seal)'),
                 (td(10, Z_MOUTH - CAP_T/2), 'Cap plate'),
                 (td(0, 1.0), 'TPU pad'),
                 (td(-10, FR_B0 + 0.8), 'Carrier frame, cells above')], DX + dw + 40, 'r', DY, size=14)
    sh.line([(40, 1240), (2660, 1240)], RULE, 1.5); sh.legend(LEG, 40, 1256, 14)
    save(sh, 'cup_sections.png')

def sheet_compare(A, m):
    Acur = RR.assembly(); mcur = current_masses()
    Ahy = H.assembly(); mhy = H.masses(Ahy); mhy['filler'] = 26*30*0.5/1000*2.5; mhy['rtv'] = 0.2
    tc, th, tu = sum(mcur.values()), sum(mhy.values()), sum(m.values())
    wc, dc, Lc = RR.SIZE(); sh_, su = H.size(Ahy), size(A)
    sh = RR.Sheet(2700, 1300)
    sh.header('Current side tray vs heatsink-free cup (and the hybrid)',
              'Same cells, board outline, nickel tongues and BLE position in all three. Masses corrected the same way for all three (notes below the table).')
    R = camera((1.0, -1.1, 0.65)); pxs = 3.7
    for title, asm, cx in (('Current side tray (d994c3a)', Acur, 290), ('Heatsink-free cup', A, 780), ('Hybrid (for reference)', Ahy, 1270)):
        sh.panel_title(cx - 230, 128, title, 440)
        sh.render([(V, c) for _, V, c in asm], R, (cx - 50, 560), pxs)
    zc = 40.35; pxa = 6.0
    sh.panel_title(1560, 128, f'A-A at z = {zc:.0f} mm, same scale', 1100)
    sh.section([(k, V, c) for k, V, c in Acur if not k.startswith('cap')], 2, zc, 0, 1, (1800, 430), pxa); sh.text(1800, 640, 'current', 16, True, anchor='mm')
    sh.section([(k, V, c) for k, V, c in A if not k.startswith('bump')], 2, zc, 0, 1, (2330, 430), pxa); sh.text(2330, 640, 'cup', 16, True, anchor='mm')
    # weight table by function
    cat = lambda mm, keys: sum(mm.get(k, 0) for k in keys)
    rows_w = [('Cells, board, nickel', ('cell', 'board', 'nickel', 'tails'), ('cell', 'board', 'nickel', 'tails'), ('cell', 'board', 'nickel', 'tails')),
              ('Tray / cup / tub (+ wedge)', ('shell', 'wedge'), ('cup',), ('tub',)),
              ('Cover / lid / cap (+ standoffs)', ('cover', 'stand'), ('cap',), ('lid',)),
              ('Cell holder (+ pad)', ('cage', 'frame', 'holder'), ('carrier', 'pad'), ('carrier', 'pad')),
              ('Bumpers / crush caps', ('capb', 'capt'), ('bumpb', 'bumpt'), ('bumpb', 'bumpt')),
              ('Seal + fasteners', ('unmodelled',), ('oring', 'screw', 'vent'), ('oring', 'screw', 'lim', 'vent', 'rtv')),
              ('Thermal interface', ('gappad',), ('filler',), ('filler',)),
              ('Insulation sheet + hold-downs', ('insul', 'rings', 'hold'), (), ())]
    rows = []
    for name, kc, ku, kh in rows_w:
        a, b, c = cat(mcur, kc), cat(m, ku), cat(mhy, kh)
        rows.append([name, f'{a:.1f}', f'{b:.1f}', f'{b - a:+.1f}', f'{c:.1f}'])
    rows.append(['Pack total', f'{tc:.1f}', f'{tu:.1f}', f'{tu - tc:+.1f}', f'{th:.1f}'])
    sh.panel_title(40, 700, 'Weight by function (g)', 1240)
    y = sh.table(40, 750, ['', '>Current', '>Cup', '>Cup - current', '>Hybrid'], rows, [420, 200, 200, 220, 200], 15, bold_last=True, rh=36)
    for i, s in enumerate(('Current: TPU cage, frame and carrier recomputed at 1.2 g/cm3 (the model uses 1.0); +1.65 g for the gap pad,',
                           '2 x M2 + inserts and the silicone bead, which it doesn\'t model. Hybrid: gap filler at 0.5 mm, +0.2 g RTV.',
                           'Cup gap filler: 3.8 g modelled over both front cells, 26 mm of the length.')):
        sh.text(40, y + 14 + 24*i, s, 13, fill=MUTED)
    rows2 = [
        ['Outside (mm)', f'{wc:.1f} x {dc:.1f} x {Lc:.1f}', f'{su[0]:.1f} x {su[1]:.1f} x {su[2]:.1f}', f'{sh_[0]:.1f} x {sh_[1]:.1f} x {sh_[2]:.1f}'],
        ['Line items', f'{len(RR.PARTS)}', f'{len(PARTS)}', f'{len(H.PARTS)}'],
        ['Metal parts', 'Al cover, 4 steel standoffs, 2 M2', '2 M2 screws', 'CNC lid, 6 M2.5, 6 limiters'],
        ['Seal joints', 'bead round the cover, 2 port rings, vent', '1 radial O-ring, 2 port rings, vent', '1 face O-ring, 2 port rings + moats, vent'],
        ['What sets the squeeze', 'bead fill (hand-applied)', 'cap skirt vs cup bore (dimensions)', 'groove depth vs hard stop'],
        ['Core install', 'drop in, lift 2.5 mm, wedge', 'push in from the bottom, cap on', 'tilt in, rotate down, pad'],
        ['Heat path for bursts', 'board -> 1 mm Al cover (8.5 J/K)', 'board -> vias + filler -> cells (~270 J/K)', 'board -> 3 mm lid (32 J/K)'],
        ['100 W until a limit (model)', '~5 min', '~16 min', '~9 min'],
        ['Cells after 10 min 100 W + 30 W', '~37 C', '~42 C', '~36 C'],
        ['Charging 88 W, 1 h (cells)', '~48 C', '~54 C', '~46 C'],
        ['BLE antenna', 'Al cover 1 board-thickness away', 'no metal at all', 'CNC lid over the board'],
        ['Label', 'laser-marked on the Al cover', 'embossed PA12 or a small plate', 'laser-marked on the lid']]
    sh.panel_title(1320, 700, 'Side by side', 1340)
    y2 = sh.table(1320, 750, ['', 'Current', 'Cup', 'Hybrid'], rows2, [300, 340, 360, 340], 14, rh=36)
    sh.text(1320, y2 + 14, 'Thermal rows: research_notes/.../model/thermal_burst.py, a lumped estimate, 25 C ambient. The dev-board 100 W run should replace it.', 13, fill=MUTED)
    save(sh, 'cup_vs_current.png')

if __name__ == '__main__':
    os.makedirs(os.path.join(OUT, 'stl'), exist_ok=True)
    A = assembly()
    for k in ('cup', 'cap', 'carrier', 'pad', 'oring', 'filler', 'bumpb_band', 'bumpb_slab', 'bumpt_band', 'bumpt_slab'):
        write_stl(os.path.join(OUT, 'stl', f'cup_{k}.stl'), np.vstack([V for kk, V, _ in A if kk == k]))
    m = masses(A)
    for n, name, mat, k in PARTS: print(f'{n:3d} {name:52s} {m.get(k, 0):7.1f} g')
    print('total', round(sum(m.values()), 1), 'g   size (x, y, z)', np.round(size(A), 1))
    print('current corrected', round(sum(current_masses().values()), 1))
    if WHICH in ('all', 'exploded'): sheet_exploded(A, m)
    if WHICH in ('all', 'sections'): sheet_sections(A)
    if WHICH in ('all', 'compare'): sheet_compare(A, m)
