"""Monolith ground-up hybrid (reports/Ground-up mechanical design.md): a rigid PA12 core (cells + board) in an MJF PA12
tub, closed by a CNC aluminium heatsink lid with a silicone O-ring on a hard stop, TPU end bumpers outside.
Needs numpy, pillow, manifold3d and the current side-tray model (monolith_shell / monolith_parts / monolith_side_renders),
whose cells, board, nickel and BLE envelopes it reuses so both designs carry the same electrical core.
Run: python monolith_hybrid.py CURRENT_MECH_DIR [OUT_DIR] [all|exploded|sections|compare]
     CURRENT_MECH_DIR is hardware/mechanical as of d994c3a (the TPU cell cage); built with the mechanical venv.
-> OUT_DIR/stl/hybrid_*.stl, hybrid_exploded.png, hybrid_sections.png, hybrid_vs_current.png"""
import os, sys, struct, numpy as np
import manifold3d as M3
from PIL import Image

CUR = os.path.abspath(sys.argv[1]); OUT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.getcwd())
sys.path.insert(0, CUR); os.chdir(CUR)
import monolith_shell as S, monolith_parts as P, monolith_side_renders as RR
from monolith_render import camera, board_g, vol, CELL_G
M3.set_circular_segments(48)

# ---------------- parameters (mm); same frame as the side tray: z along the cells, +x toward the board, y across ----------------
PR, CR = S.sb_pr, S.CELL_D / 2          # cell pitch half and radius (unchanged, so the board outline is unchanged)
TW = 1.6                                # tub wall (MJF PA12)
YI = PR + CR + 0.2                      # tub inside half-width (cells + 0.2)
XB = -YI                                # tub inside back face
X_FL0, X_RIM = 26.0, 30.0               # flange underside and the sealing land (lid underside, hard stop)
X_LAND = 27.0                           # land blocks at the ends start here (board F.Cu is at 26.55)
Y_FL = 29.9                             # flange / lid half-width
Z_END = 1.6                             # end walls
Z_LAND0, Z_LAND1 = 5.0, S.SB_H - 5.0    # 5 mm sealing land at each end, x >= X_LAND
H = S.SB_H                              # tub length, the same 80.6 mm as the side tray
LID_T = 3.0                             # CNC 6061 lid base
ORING_CS, GROOVE_W, GROOVE_D = 2.0, 3.0, 1.5     # 25 % squeeze, ~70 % gland fill
Y_GROOVE, Z_GROOVE0, Z_GROOVE1, R_GROOVE = 24.4, 3.0, H - 2.5, 7.0   # O-ring centreline loop
SCREW_Y, SCREW_Z = 27.6, (8.0, H / 2, H - 8.0)   # six M2.5 from below into threads tapped in the lid
LIM_OD, LIM_ID = 4.0, 2.9               # brass compression limiters in the flange
PAD_Z0, PAD_Z1 = Z_END, 4.6             # TPU pad under the carrier (fills the tilt-in clearance, 0.5 preload)
FR_B0, FR_B1 = 4.6, 6.2                 # carrier frames
FR_T0, FR_T1 = 77.8, H - Z_END
WIN_R = 7.0                             # weld / + cap windows in the frames
VENT_Z, VENT_R = 14.0, 1.5
BUMP_T, BUMP_BAND, BUMP_WALL = 8.0, 9.0, 2.0
PORT_X, PORT_YS = S.sb_port_x, (-S.SB_PORT_Y, S.SB_PORT_Y)
BORE_W, BORE_H = S.USB_SEAL_W, S.USB_SEAL_H      # receptacle seal ring sits in this bore
MOAT_W, MOAT_H, MOAT_D = BORE_W + 3.0, BORE_H + 3.0, 1.0

# ---------------- manifold helpers ----------------
CS, MF = M3.CrossSection, M3.Manifold
ROUND = M3.JoinType.Round
def rect(u0, u1, v0, v1): return CS.square((u1 - u0, v1 - v0)).translate((u0, v0))
def rrect(u0, u1, v0, v1, r): return rect(u0 + r, u1 - r, v0 + r, v1 - r).offset(r, ROUND)
def circ(u, v, r): return CS.circle(r).translate((u, v))
def stad(u, v, L, W): return rrect(u - L/2, u + L/2, v - W/2, v + W/2, min(L, W)/2 - 1e-3)
def hull(*cs): return CS.batch_hull(list(cs))
def pz(cs, z0, z1): return MF.extrude(cs, z1 - z0).translate((0, 0, z0))                 # section (x, y)
def px_(cs, x0, x1): return MF.extrude(cs, x1 - x0).transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])   # section (y, z)
def cylx(y, z, r, x0, x1): return px_(circ(y, z, r), x0, x1)
def U(*ms): return MF.batch_boolean(list(ms), M3.OpType.Add)
def tris(m):
    me = m.to_mesh(); v = np.asarray(me.vert_properties)[:, :3]; return v[np.asarray(me.tri_verts)].astype(float)
def write_stl(path, V):
    n = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    with open(path, 'wb') as f:
        f.write(b'monolith hybrid'.ljust(80, b' ')); f.write(struct.pack('<I', len(V)))
        rec = np.zeros(len(V), np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')])); rec['n'] = n; rec['v'] = V.reshape(-1, 9)
        f.write(rec.tobytes())

# ---------------- sections ----------------
CELLS = [S.sb_cell_xy[k] for k in S.SB_CELLS]
cs_cells = hull(*[circ(x, y, CR) for x, y in CELLS])                         # the 2x2 envelope
cs_in = hull(*[circ(x, y, CR + 0.2) for x, y in CELLS], rect(0, X_LAND, -YI, YI))   # tub inside, cell + board zone
cs_body = hull(*[circ(x, y, CR + 0.2 + TW) for x, y in CELLS], rect(0, X_FL0 + 0.01, -YI - TW, YI + TW))
cs_flange = rrect(X_FL0 - 1.5, X_RIM, -Y_FL, Y_FL, 2.0)
cs_pack = CS.batch_boolean([cs_body, cs_flange, rrect(X_FL0, X_RIM + LID_T, -Y_FL, Y_FL, 2.0)], M3.OpType.Add)
def groove_loop(d): return rrect(-Y_GROOVE - d, Y_GROOVE + d, Z_GROOVE0 - d, Z_GROOVE1 + d, R_GROOVE + d)   # (y, z)

# ---------------- parts ----------------
def tub():
    body = U(pz(cs_body, 0, H), px_(rrect(-Y_FL, Y_FL, 0, H, 2.0), X_FL0 - 1.5, X_RIM))
    cav = U(pz(cs_in, Z_END, H - Z_END),                                                 # full-length cavity below the lands
            px_(rect(-YI, YI, Z_LAND0, Z_LAND1), X_LAND - 0.01, X_RIM + 1))              # opening through the land
    body = body - cav
    for py in PORT_YS:
        bore = MF.extrude(stad(PORT_X, py, BORE_H, BORE_W), H + 1 - (Z_LAND1 - 2)).translate((0, 0, Z_LAND1 - 2))
        moat = MF.extrude(stad(PORT_X, py, MOAT_H, MOAT_W), MOAT_D + 1).translate((0, 0, H - MOAT_D))
        body = body - bore - moat
    for sy in (-1, 1):
        for z in SCREW_Z:
            body = body - cylx(sy*SCREW_Y, z, LIM_OD/2, X_FL0 - 2, X_RIM + 0.1)
    return body
def limiters():
    return U(*[cylx(sy*SCREW_Y, z, LIM_OD/2, X_FL0 - 1.5, X_RIM) - cylx(sy*SCREW_Y, z, LIM_ID/2, X_FL0 - 2, X_RIM + 1)
               for sy in (-1, 1) for z in SCREW_Z])
def screws():
    return U(*[U(cylx(sy*SCREW_Y, z, 1.25, X_FL0 - 1.5, X_RIM + 2.5), cylx(sy*SCREW_Y, z, 2.25, X_FL0 - 3.2, X_FL0 - 1.5))
               for sy in (-1, 1) for z in SCREW_Z])
def lid():
    m = px_(rrect(-Y_FL, Y_FL, 0, H, 2.0), X_RIM, X_RIM + LID_T)
    m = m - px_(groove_loop(GROOVE_W/2) - groove_loop(-GROOVE_W/2), X_RIM - 0.1, X_RIM + GROOVE_D)
    for sy in (-1, 1):
        for z in SCREW_Z: m = m - cylx(sy*SCREW_Y, z, 1.05, X_RIM - 0.1, X_RIM + 2.5)
    m = m - cylx(0, VENT_Z, VENT_R, X_RIM - 0.1, X_RIM + LID_T + 0.1) - cylx(0, VENT_Z, 6.0, X_RIM + LID_T - 0.6, X_RIM + LID_T + 0.1)
    return m
def oring(): return px_(groove_loop(ORING_CS/2) - groove_loop(-ORING_CS/2), X_RIM, X_RIM + GROOVE_D)   # as squeezed: 1.5 tall
def vent(): return cylx(0, VENT_Z, 5.5, X_RIM + LID_T - 0.6, X_RIM + LID_T - 0.3)
def carrier():
    frame = CS.batch_boolean([cs_cells] + [circ(x, y, WIN_R) for x, y in CELLS], M3.OpType.Subtract)
    m = [pz(frame, FR_B0, FR_B1), pz(frame, FR_T0, FR_T1)]
    m += [pz(rect(-PR - CR, -PR - CR + 5.2, -1.5, 1.5), FR_B0, FR_T1)]                     # back spine in the C2/C3 valley
    m += [pz(rect(-1.5, 1.5, s*(PR + CR - 5.2), s*(PR + CR)) if s > 0 else rect(-1.5, 1.5, -PR - CR, -PR - CR + 5.2), FR_B0, FR_T1)
          for s in (-1, 1)]                                                              # side spines
    m += [pz(rect(PR + CR + 0.15, S.sb_xb0, *(sorted((s*S.SB_BAR_Y[0], s*S.SB_BAR_Y[1])))), FR_B0, FR_T1) for s in (-1, 1)]   # board rails
    m += [cylx(s*8.6, z, 1.0, S.sb_xb0 - 0.5, S.sb_xb1 + 0.6) for s in (-1, 1) for z in (14.0, 68.0)]                        # board pegs
    return U(*m)
def pad(): return pz(cs_cells.offset(-0.2, ROUND), PAD_Z0, PAD_Z1)
def gap_filler(): return MF.cube((X_RIM - 28.2, 26.0, 30.0)).translate((28.2, -13.0, 26.0))
def bumper(top):
    out = cs_pack.offset(BUMP_WALL, ROUND)
    band = pz(CS.batch_boolean([out, cs_pack], M3.OpType.Subtract), 0, BUMP_BAND)
    slab = pz(out, -BUMP_T, 0)
    if top:
        slab = slab - pz(rrect(PORT_X - 4.5, PORT_X + 4.5, -14.0, 14.0, 2.0), -BUMP_T - 1, 0.1)   # port well, both plugs
        flip = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, H]]                                     # mirror z about H/2 (and y to keep it solid)
        return band.transform(flip), slab.transform(flip)
    return band, slab

# ---------------- assembly ----------------
C = dict(RR.C, tub=(214, 214, 208), lid=(150, 156, 168), oring=(200, 60, 60), lim=(214, 172, 60), screw=(110, 110, 116),
         carrier=(196, 190, 150), pad=(236, 156, 80), filler=(232, 150, 200), bump=(118, 72, 50), bslab=(236, 156, 80), vent=(240, 240, 240))
def mv(V, d): return V + np.asarray(d, float)
def assembly():
    A = [('tub', tris(tub()), C['tub']), ('lim', tris(limiters()), C['lim'])]
    cell = P.cell_solid()
    for x, y in CELLS: A.append(('cell', mv(cell, (x, y, S.sb_z_cell0)), C['cell']))
    A += [('carrier', tris(carrier()), C['carrier']), ('pad', tris(pad()), C['pad']),
          ('nickel', P.nickel_strips('strips'), C['nickel']), ('tails', P.nickel_strips('tails'), C['tail']),
          ('board', P.side_board_dummy(), C['board']), ('ble', P.ble_module(), C['ble']),
          ('filler', tris(gap_filler()), C['filler']), ('oring', tris(oring()), C['oring']), ('lid', tris(lid()), C['lid']),
          ('screw', tris(screws()), C['screw']), ('vent', tris(vent()), C['vent'])]
    for top in (False, True):
        b, s = bumper(top); k = 'bumpt' if top else 'bumpb'
        A += [(k + '_band', tris(b), C['bump']), (k + '_slab', tris(s), C['bslab'])]
    return A
def group(k): return k.split('_')[0]

PARTS = [(1, 'Cell carrier: end frames, spines, rails, pegs', 'MJF PA12', 'carrier'), (2, 'Cells C1-C4, welded 4S', 'EVE INR21700-58E', 'cell'),
         (3, 'Nickel series strips (3)', 'nickel 0.15', 'nickel'), (4, 'Nickel tongues: PACK+/- (power + Kelvin), CELL1-3', 'nickel 0.15 / 0.2', 'tails'),
         (5, 'Board 1.6 mm on the carrier pegs, tongues soldered', 'FR4, 6 layers', 'board'),
         (6, 'Pad under the carrier (fills the tilt-in gap)', 'TPU 95A, 30 % gyroid', 'pad'),
         (7, 'Tub: sealing land, port bores + moats, screw flange', 'MJF PA12', 'tub'), (8, 'Compression limiters (6)', 'brass', 'lim'),
         (9, 'Gap filler over the hot parts', 'dispensed, ~3 W/mK', 'filler'), (10, 'O-ring, 2.0 mm cord', 'silicone 60A', 'oring'),
         (11, 'Lid / heatsink: groove, tapped holes, vent recess', 'CNC 6061, black anodised', 'lid'),
         (12, 'Screws M2.5 (6), from below', 'stainless', 'screw'), (13, 'Pressure vent (fitted after the leak test)', 'ePTFE', 'vent'),
         (14, 'Bottom bumper', 'TPU 95A', 'bumpb'), (15, 'Top bumper, port well', 'TPU 95A', 'bumpt')]
NUM = {k: n for n, _, _, k in PARTS}
RHO = dict(tub=1.01, carrier=1.01, lim=8.5, screw=7.9, lid=2.70, oring=1.15, filler=2.5, nickel=8.9, tails=8.9, vent=1.0)
def masses(A):
    m = {}
    for k, V, _ in A:
        g = group(k)
        if g in RHO: r = RHO[g]
        elif g == 'pad': r = 1.2 * 0.30
        elif k.endswith('_band'): r = 1.2
        elif k.endswith('_slab'): r = 1.2 * 0.30
        else: continue
        m[g] = m.get(g, 0) + vol(V) * r
    m['board'] = board_g(S.sb_board_area, S.SB_PCB_T); m['cell'] = 4 * CELL_G; m['ble'] = 0
    return m
def size(A):
    V = np.vstack([V for _, V, _ in A]); lo, hi = V.reshape(-1, 3).min(0), V.reshape(-1, 3).max(0); return hi - lo

# ---------------- sheets ----------------
SS, INK, MUTED, RULE, ACCENT, LEADER = RR.SS, RR.INK, RR.MUTED, RR.RULE, RR.ACCENT, RR.LEADER
def save(sh, name): sh.img.resize((sh.W, sh.H), Image.LANCZOS).save(os.path.join(OUT, name)); print('wrote', name)
def balloons(sh, pid, gid, BAL, dist=80):
    for g_ in dict.fromkeys(gid):
        a = RR.visible_anchor(pid, [i for i, x in enumerate(gid) if x == g_])
        if a is None or g_ not in NUM: continue
        ax, ay = a; ang = np.radians(BAL.get(g_, 0)); d = dist + (70 if g_.startswith('bump') else 0)
        bx, by = ax + d*np.cos(ang), ay - d*np.sin(ang); v = np.array([bx - ax, by - ay]); v /= np.linalg.norm(v)
        sh.line([(ax, ay), (bx - v[0]*13, by - v[1]*13)], ACCENT, 1.2); sh.dot(ax, ay, 3, ACCENT); sh.balloon(bx, by, NUM[g_])

LEG = [('PA12 tub', C['tub']), ('PA12 carrier', C['carrier']), ('cells', C['cell']), ('board', C['board']), ('BLE module', C['ble']),
       ('Al lid (CNC)', C['lid']), ('O-ring', C['oring']), ('brass limiter', C['lim']), ('screw', C['screw']), ('gap filler', C['filler']),
       ('TPU pad / bumper slab', C['pad']), ('TPU bumper band', C['bump']), ('nickel strip', C['nickel']), ('nickel tongue', C['tail'])]

def sheet_exploded(A, m):
    total = sum(m.values()); w, d, L = size(A)
    sh = RR.Sheet(2700, 1100)
    sh.header('Ground-up hybrid: rigid core, PA12 tub, O-ring heatsink lid',
              'The cells, carrier and board are one core, built and tested on the bench. One O-ring joint, two port seals and a vent keep the water out. '
              f'Pack {w:.1f} x {d:.1f} x {L:.1f} mm, about {total:.0f} g.')
    sh.panel_title(40, 128, 'Assembled', 640)
    R = camera((1.0, -1.1, 0.65)); o1 = (250, 640); pxs = 5.0
    sh.render([(V, c) for _, V, c in A], R, o1, pxs); pj = RR.proj(R, o1, pxs)
    sh.callouts([(pj((PORT_X, 9, H + BUMP_T)), 'Port well through the top bumper'),
                 (pj((X_RIM + LID_T, -8, 50)), 'CNC aluminium lid = heatsink;\nO-ring groove on its underside'),
                 (pj((X_RIM + LID_T, 0, VENT_Z)), 'ePTFE vent, fitted last:\nits hole is the leak-test port'),
                 (pj((X_RIM - 1, -Y_FL, 40)), 'Screw flange: six M2.5 from below,\noutside the seal line'),
                 (pj((X_RIM + LID_T + 2, -Y_FL, -BUMP_T + 2)), 'TPU end bumpers (8 mm slab,\nsolid band over the lid edges)')],
                475, 'r', 150)
    sh.panel_title(780, 128, 'Exploded, in assembly order', 1180)
    EX = dict(cell=(70, 0, 0), carrier=(70, 0, 0), nickel=(70, 0, 0), tails=(70, 0, 0), board=(86, 0, 0), ble=(86, 0, 0), pad=(70, 0, -22),
              tub=(0, 0, 0), lim=(-10, 0, 0), filler=(118, 0, 0), oring=(130, 0, 0), lid=(145, 0, 0), screw=(-34, 0, 0), vent=(160, 0, 0))
    ex, gid = [], []
    for k, V, c in A:
        g_ = group(k); dd = EX.get(g_, (0, 0, -38) if g_ == 'bumpb' else (0, 0, 38))
        ex.append((mv(V, dd), c)); gid.append(g_)
    R2 = camera((0.42, -1.25, 0.5)); o2 = (1150, 690); px2 = 4.0
    pid = sh.render(ex, R2, o2, px2)
    balloons(sh, pid, gid, dict(tub=200, lim=250, screw=230, pad=250, carrier=110, cell=235, nickel=40, tails=290, board=80, filler=40,
                                oring=330, lid=10, vent=40, bumpb=180, bumpt=180))
    x0 = 2010; sh.panel_title(x0, 128, 'Parts', 650)
    rows = [[str(n), name, mat, f'{m.get(k, 0):.1f}' if m.get(k, 0) >= 0.05 else '<0.1'] for n, name, mat, k in PARTS]
    rows.append(['', 'Pack total', '', f'{total:.1f}'])
    y = sh.table(x0, 176, ['#', 'Part', 'Material', '>g'], rows, [36, 344, 200, 70], 13, bold_last=True, rh=26)
    for i, s in enumerate(('Board mass is estimated (FR4 + 6-layer copper); parts on it are not included.',
                           'TPU pad and bumper slabs at 30 % gyroid; bumper bands solid.',
                           'Not drawn: RTV in the port moats (~0.2 g), the 0.5 mm + lips on the carrier.')):
        sh.text(x0, y + 14 + 24*i, s, 13, fill=MUTED)
    sh.line([(40, 1030), (2660, 1030)], RULE, 1.5); sh.legend(LEG, 40, 1050, 14)
    save(sh, 'hybrid_exploded.png')

def sheet_sections(A):
    core = [(k, V, c) for k, V, c in A if not k.startswith('bump')]
    sh = RR.Sheet(2700, 1240)
    sh.header('Hybrid sections', 'Cut from the same meshes as the STLs. Board and USB-C are envelopes; parts on the board are not drawn '
              '(the gap filler stands in for them). The O-ring is drawn as squeezed.')
    z_a = SCREW_Z[1] + 0.05; pxa = 10.0
    sh.panel_title(40, 128, f'A-A   across the pack through the middle screws (z = {z_a:.0f} mm), from the port end', 1380)
    oa = (600, 620); tp = sh.section(core, 2, z_a, 0, 1, oa, pxa)
    for (x, y), nm in zip(CELLS, [S.SB_CELLS[k][0] for k in S.SB_CELLS]):
        q = tp(x, y); sh.text(q[0], q[1], nm, 22, True, fill='white', anchor='mm')
    sh.callouts([(tp(XB - TW/2, 6), '1.6 mm MJF PA12 tub wall'),
                 (tp(-PR - CR + 2.5, 0), 'Carrier spine in the valley\n(the core is rigid)'),
                 (tp(0, PR + CR - 2), 'Side spine'),
                 (tp(X_FL0 - 2.4, -SCREW_Y), 'M2.5 from below, head\nunder the flange'),
                 (tp(XB + 8, YI + TW/2), 'BLE module (B.Cu, higher up)\nradiates through this PA12\nside wall, as today')], 300, 'l', 230)
    sh.callouts([(tp(X_RIM + 0.75, Y_GROOVE), 'O-ring in the lid groove, 25 % squeeze:\nthe lid lands on the PA12 land (hard stop),\nso the screws don\'t set the squeeze'),
                 (tp(X_FL0 + 2, SCREW_Y + 1.6), 'Brass limiter: the screw clamps metal to metal,\nso PA12 creep can\'t unload it'),
                 (tp(X_RIM + LID_T - 0.5, 0), '3 mm CNC 6061 lid = heatsink'),
                 (tp(29.0, 5), 'Gap filler: hot parts to lid'),
                 (tp(S.sb_xb0 + 0.8, -14), 'Board, fixed to the carrier'),
                 (tp(PR + CR + 1.2, -S.SB_BAR_Y[0] - 2), 'Carrier rail: holds the cells\noff B.Cu, carries the pegs')], 1010, 'r', 200)
    p0, p1 = tp(XB - TW, -Y_FL - 3), tp(X_RIM + LID_T, -Y_FL - 3)
    sh.dim((p0[0], tp(0, -Y_FL)[1]), (p1[0], tp(0, -Y_FL)[1]), 40, f'{X_RIM + LID_T - XB + TW:.1f}')
    q0, q1 = tp(X_RIM + LID_T, -Y_FL), tp(X_RIM + LID_T, Y_FL)
    sh.dim(q0, q1, 40, f'{2*Y_FL:.1f}')
    # B-B: along the pack through the +y port
    pxb = 7.0; ob = (1800, 420)
    sh.panel_title(1480, 128, f'B-B   along the pack through a USB-C port (y = {PORT_YS[1]:.1f} mm)', 1180)
    tq = sh.section(core, 1, PORT_YS[1] + 0.02, 2, 0, ob, pxb)
    sh.text(1800, 620, 'bottom end', 15, fill=MUTED, anchor='mm'); sh.text(1800 + pxb*H, 620, 'port end', 15, fill=MUTED, anchor='mm')
    # detail of the port end, same cut, drawn on its own sheet and pasted in (section() doesn't clip)
    pxd, (z0, z1, x0, x1) = 24.0, (63.0, 82.5, 15.0, 34.5); dw, dh = int((z1 - z0)*pxd), int((x1 - x0)*pxd)
    det = RR.Sheet(dw, dh); od = (-z0*pxd, x1*pxd)
    det.section(core, 1, PORT_YS[1] + 0.02, 2, 0, od, pxd)
    DX, DY = 1560, 680
    sh.panel_title(1480, 646, 'Detail: the port end of B-B', 1180)
    sh.img.paste(det.img, (DX*SS, DY*SS)); sh.rect(DX, DY, DX + dw, DY + dh, outline=RULE, width=1)
    td = lambda z, x: (DX + od[0] + pxd*z, DY + od[1] - pxd*x)
    sh.callouts([(td(80.1, PORT_X), 'Receptacle seal ring in the 1.6 mm wall bore'),
                 (td(80.3, PORT_X + 3.2), 'RTV moat: second barrier\non the printed bore'),
                 (td(Z_GROOVE1, X_RIM + 0.75), 'O-ring, 25 % squeeze, crossing\nthe top end above the ports'),
                 (td(77.0, X_RIM - 0.4), 'PA12 sealing land: lid lands here'),
                 (td(70.0, X_RIM + 1.8), 'CNC lid'),
                 (td(74.0, PORT_X), 'USB-C receptacle (envelope)'),
                 (td(70.0, S.sb_xb0 + 0.8), 'Board'),
                 (td(78.4, 18.0), 'Carrier top frame on the top wall')], DX + dw + 40, 'r', DY, size=14)
    sh.callouts([(tq(H - 3, X_RIM - 0.6), '5 mm land above the\nports: the core goes in\nUSB end first, tilted,\nthen rotates down'),
                 (tq(FR_T0 + 0.6, -6), 'Carrier top frame\non the top wall')], 2400, 'r', 200, size=14)
    sh.callouts([(tq(3.0, X_RIM + 0.75), 'O-ring crosses the\nbottom end'),
                 (tq((PAD_Z0 + PAD_Z1)/2, -8), 'TPU pad: last in, fills\nthe tilt clearance,\npreloads the core'),
                 (tq(FR_B0 + 0.8, -15), 'Carrier bottom frame:\ndatum for cells + board'),
                 (tq(S.sb_zb0 + 0.3, S.sb_xb0 + 0.8), 'Bottom 0.7 mm of the\nboard runs under the\nland: no tall parts')], 1760, 'l', 200, size=14)
    sh.line([(40, 1180), (2660, 1180)], RULE, 1.5); sh.legend(LEG, 40, 1196, 14)
    save(sh, 'hybrid_sections.png')

def sheet_compare(A, m):
    Acur = RR.assembly(); mcur, _ = RR.masses(Acur, None)
    tot_h, tot_c = sum(m.values()), sum(mcur.values())
    wc, dc, Lc = RR.SIZE(); sz = size(A)
    sh = RR.Sheet(2700, 1500)
    sh.header('Current side tray vs ground-up hybrid',
              'Same cells, board outline, nickel tongues and BLE position in both. What changes is how the core is held and how the box is sealed.')
    R = camera((1.0, -1.1, 0.65)); pxs = 4.0
    cols = (('Current side tray (origin/Production d994c3a)', Acur, 360), ('Ground-up hybrid', A, 1060))
    for title, asm, cx in cols:
        sh.panel_title(cx - 300, 128, title, 600)
        sh.render([(V, c) for _, V, c in asm], R, (cx - 60, 600), pxs)
    # A-A of each at the same scale
    zc = 40.35; pxa = 6.5
    sh.panel_title(1480, 128, f'A-A at z = {zc:.0f} mm, same scale', 1180)
    core_c = [(k, V, c) for k, V, c in Acur if not k.startswith('cap')]
    core_h = [(k, V, c) for k, V, c in A if not k.startswith('bump')]
    sh.section(core_c, 2, zc, 0, 1, (1760, 460), pxa); sh.text(1760, 680, 'current', 16, True, anchor='mm')
    sh.section(core_h, 2, zc, 0, 1, (2330, 460), pxa); sh.text(2330, 680, 'hybrid', 16, True, anchor='mm')
    n_c = len(RR.PARTS); n_h = len(PARTS)
    rows = [
        ['Outside, with caps/bumpers (mm)', f'{wc:.1f} x {dc:.1f} x {Lc:.1f}', f'{sz[0]:.1f} x {sz[1]:.1f} x {sz[2]:.1f}', f'{sz[1] - dc:+.1f} mm wide: the screw flange outside the O-ring land'],
        ['Mass (g)', f'{tot_c:.0f}', f'{tot_h:.0f}', f'{tot_h - tot_c:+.0f} g: lid {m["lid"]:.0f} vs cover {mcur["cover"]:.0f}, tub {m["tub"]:.0f} vs tray {mcur["shell"]:.0f}'],
        ['Line items in the parts list', f'{n_c}', f'{n_h}', ''],
        ['Lid / cover joint', '0.3 mm gap, formed-in-place silicone bead', '2.0 mm O-ring in a CNC groove, hard stop', 'squeeze set by the groove, not by torque or a bead'],
        ['Cover / lid retention', '2 x M2 into inserts on the PA12 wedge', '6 x M2.5 into the Al, brass limiters', 'mid-span screws stop the lid bowing'],
        ['Cover / lid part', 'JLC sheet metal, flat 1.0 mm', 'JLC CNC 6061, 3 mm, ~$15-25', 'heavier, stiffer, better spreading'],
        ['USB-C seal', 'receptacle ring in the tray hole', 'ring in the bore + RTV moat outside', 'second barrier on a printed bore'],
        ['Core', 'TPU frame + cage + PA12 wedge', 'one PA12 carrier, TPU pad', 'rigid: board and cells move together'],
        ['Sheet stock', 'fish paper: board insulator, + rings', 'none (printed + lips)', 'your no-fish-paper rule'],
        ['Board install', 'drop in, slide 2.5 mm, wedge', 'tilt in USB end first, rotate down, pad', 'the O-ring land sits above the ports'],
        ['Thermal at 100 W', 'burst, derate', 'burst, derate', 'lid sheds ~1-2 W at +40 K in both'],
        ['Leak test', 'none in p0-assembly.md (vent fitted before closing)', '+10-15 kPa through the vent hole, then the vent', 'could be added to the current one too']]
    sh.panel_title(40, 830, 'Side by side', 2620)
    sh.table(40, 880, ['', 'Current', 'Hybrid', 'Note'], rows, [430, 640, 640, 900], 15, rh=40)
    save(sh, 'hybrid_vs_current.png')

if __name__ == '__main__':
    os.makedirs(os.path.join(OUT, 'stl'), exist_ok=True)
    A = assembly()
    for k in ('tub', 'carrier', 'lid', 'pad', 'oring', 'lim', 'bumpb_band', 'bumpb_slab', 'bumpt_band', 'bumpt_slab'):
        write_stl(os.path.join(OUT, 'stl', f'hybrid_{k}.stl'), np.vstack([V for kk, V, _ in A if kk == k]))
    m = masses(A)
    for n, name, mat, k in PARTS: print(f'{n:3d} {name:52s} {m.get(k, 0):7.1f} g')
    print('total', round(sum(m.values()), 1), 'g   size (x, y, z)', np.round(size(A), 1))
    which = sys.argv[3] if len(sys.argv) > 3 else 'all'
    if which in ('all', 'exploded'): sheet_exploded(A, m)
    if which in ('all', 'sections'): sheet_sections(A)
    if which in ('all', 'compare'): sheet_compare(A, m)
