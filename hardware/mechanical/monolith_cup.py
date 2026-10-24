"""Monolith heatsink-free cup: THE CURRENT ENCLOSURE (adopted 2026-10-21; replaces the side tray + aluminium cover).
An MJF PA12 cup closed on five sides holds the bench-built core (cells, PA12 carrier, board, nickel tongues): the core
goes in from the bottom until the USB-C faces seat in the closed top wall, and a bottom cap seals it with one radial
O-ring, held by two radial M2 screws below the seal. No aluminium: the power stage dumps its heat into the cells
through thermal vias and a dispensed gap filler, and full-length PA12 webs share it with the back pair.
Design study and thermal models: research_notes/Ground-up mechanical concepts/ (monolith_cup.py there, thermal_*.py).

Geometry comes from monolith_shell.py (cells, board, nickel, slots, ports), so the board outline and slot positions
are the same as the side tray's: the tray-only parts (wedge, ring carrier, TPU cage and frame, cover, standoffs,
fish paper, EVA hold-downs, crush caps) are not used.
Needs numpy, pillow, manifold3d (the mechanical venv).
Run: python monolith_cup.py [all|stl|exploded|sections|compare]
-> monolith_cup_*.stl, monolith_cup_exploded.png, monolith_cup_sections.png, monolith_cup_vs_tray.png"""
import os, sys, struct, numpy as np
import manifold3d as M3
from PIL import Image
import monolith_shell as S, monolith_parts as P, monolith_side_renders as RR
from monolith_render import camera, board_g, vol, CELL_G
HERE = os.path.dirname(os.path.abspath(__file__))
M3.set_circular_segments(48)
CS, MF, ROUND = M3.CrossSection, M3.Manifold, M3.JoinType.Round

# ---------------- parameters (mm); frame as monolith_shell: z along the cells, +x toward the board, y across ----------------
PR, CR = S.sb_pr, S.CELL_D / 2
CELLS = [S.sb_cell_xy[k] for k in S.SB_CELLS]
WALL = S.WALL                       # cup wall, MJF PA12
WALL_BF = 2.0                       # board-face (+x) wall, thickened outward (review 2026-10-24 #4: 1.2 mm deflected onto the
                                    # parts under thumb load or dunk underpressure; 2.0 mm is ~4.6x stiffer)
YI = PR + CR + 0.2                  # inside half-width (cells + 0.2)
X_IN = S.sb_xb1 + S.SB_OUT_H + 0.5  # inside face over the board: tallest part + 0.5
R_FRONT = 4.0                       # bore corner radius on the board side (radial O-ring: >= 2 x cord)
TOP_T = 1.85                        # top wall, thickened inward (#8): the USB-C seal ring ends 0.35 inside it, and the board's
Z_TOP1 = S.SB_H                     # top edge is a 0.1 mm backstop under it
Z_TOP0 = Z_TOP1 - TOP_T
USB_SQ, USB_LEAD = 0.15, 0.3        # seal bore = ring (rev A4) - 2 x USB_SQ (0.12-0.18 radial target: pick from the bore-ladder
                                    # coupon); USB_LEAD x 45 deg lead-in on the inside face for the blind push-in
FR_B0 = S.cup_fr_b0; FR_B1 = FR_B0 + 1.6                            # carrier bottom frame, under the bottom strips
FR_T0, FR_T1 = S.sb_z_cell1 + S.TAB_T, Z_TOP0                       # carrier top frame, bears on the top wall
# Cap end (#1, #2, #7). The skirt top stays SKIRT_GAP under the carrier frame, so no rigid contact crosses the groove;
# OT_POSTS on the cap plate are the overtravel stop instead. The O-ring sits higher, the M2 screws go in under it with a
# real ligament below, and an outer collar on the cap holds the cup mouth's flats against the O-ring's push.
SKIRT_GAP = 1.1                    # skirt top to the carrier frame underside
Z_SKIRT1 = FR_B0 - SKIRT_GAP       # cap skirt top
SKIRT_L = 7.5                      # skirt length = cup mouth to skirt top (was 7.0)
Z_MOUTH = Z_SKIRT1 - SKIRT_L       # open bottom end of the cup
CAP_T = 1.6                        # cap plate below the mouth (lands on the cup rim: hard stop)
SKIRT_T = 2.6                      # radial skirt wall: 1.2 mm root behind the groove (was 2.1, 0.7 root)
ORING_CS, GROOVE_D = 2.0, 1.4      # 2.0 mm cord, groove 2.6 wide x 1.4 deep (+0.1 bore gap) -> ~25 % squeeze
GROOVE_Z = (Z_MOUTH + 3.9, Z_MOUTH + 6.5)
SCREW_X, SCREW_Z = 16.0, Z_MOUTH + 2.4   # two M2 (thread-forming), radially through the collar and the cup wall into blind
SCREW_HOLE_R, PILOT_R, PILOT_SOLID = 1.1, 0.8, 1.2   # pilots in the skirt bosses, below the O-ring; >= 1.2 solid behind
BOSS_DEPTH = 5.0                   # skirt boss depth (y)
COLLAR_T, COLLAR_CLR, COLLAR_H = 1.5, 0.15, SKIRT_L   # outer collar on the cap: wall, clearance to the cup, height above the rim
CRUSH_W, CRUSH = 1.0, 0.15         # crush ribs inside the collar (3 per flat): width, interference with the cup
MOUTH_LEAD = 0.8                   # lead-in at the cup mouth for the O-ring (0.3 deep over this height)
OT_POSTS = [(-(PR + CR) + 2.6, 0.0), (0.0, 0.0), (0.0, -(PR + CR) + 2.6), (0.0, PR + CR - 2.6)]   # overtravel posts (x, y)
OT_R, OT_GAP = 1.5, 0.6            # post radius; gap to the frame underside at nominal
PAD_PROUD = 1.2                    # TPU pad printed this much taller than drawn (15 % gyroid): ~15-80 N of preload on the core
PAD_RELIEF = 1.5                   # pad pocketed this deep under the C1 / C4 windows and the wire notches (PACK pads, wires)
VENT_Y, VENT_Z = S.CUP_VENT          # ePTFE vent on the board-side face (its bare hole is the leak-test port)
WIN_R = 7.0                        # weld / + cap windows in the frames
FILL_Z = S.CUP_FILL_Z              # gap filler, board B.Cu to the two front cells, over the power stages
RAIL_GAP = S.CUP_RAIL_GAP          # board rails stop here so the filler reaches the cell tangents
WIRE_NOTCH_CLR = 0.2               # PACK / Kelvin wire notch through the bottom frame: clearance each side of the wires
RAIL_RELIEF_Y = 7.6                # below SB_BAR_Z0 the rails keep only |y| <= this, so the PACK and Kelvin wires pass
RAIL_X0 = PR + CR + 0.15           # rails stand 0.15 off the front cans (they keep the cells off the board)
# Board rails (#5): four clip-on PA12 blocks (bottom and top, each side), not part of the carrier, so the front cells can
# go into the carrier from the board side. Each has a tongue that slides into a key slot in the frame's board-side face;
# the board's pegs then hold them, and the peg posts run on to the board-face wall (#4).
KEY_Y = {'bottom': (5.4, 7.4), 'top': (7.5, 10.5)}   # |y| span of each block's tongue
KEY_DEPTH, KEY_CLR = 2.0, 0.1      # tongue length into the frame (-x), clearance all round in the key slot
POST_GAP = 0.3                     # peg posts stop this far under the board-face wall at nominal
SLEEVE = (2.0, 0.85, 1.0)          # TPU retaining sleeve pushed down each post onto F.Cu: outer r, bore r, height (pushed
                                    # down to touch, not clamp, so the board can still float in the board's peg slots)
# Cells (#3, #6). An insulator ring on every + end (C1 / C3 top, C2 / C4 bottom) under the nickel, so a strip pushed
# into a frame window lands on paper, not on the cell's own - shoulder; a foam ring in a pocket in the bottom frame
# pushes each cell up onto the top frame, so the cells can't float on the welds.
INSUL = (10.6, 4.7, 0.2)           # fish-paper ring: outer r, inner r (measure the BAK + cap first), thickness
FOAM_R, FOAM_POCKET = (WIN_R + 0.3, CR - 0.4), 0.6   # foam ring radii, its pocket depth in the bottom frame (not under
                                    # the PACK pads: C1 / C4 keep only the half away from the board)
CH_W, CH_D = 1.0, 0.95              # CELL2 sense-wire channel in the bottom frame (y = 0), from under the strip to the edge
WEB_X, WEB_IN, WEB_CLR, WEB_LINK = 2.0, 4.5, 0.05, 0.6   # front-back webs (heat sharing), link out to the side spine
BUMP_T_TOP, BUMP_T_BOT, BUMP_BAND, BUMP_WALL = 8.0, 4.0, 9.0, 2.0
BUMP_WALL_BOT = 1.0                 # bottom band over the cap's collar (the PA12 collar under it is the edge protection's backbone)
PORT_X, PORT_YS = S.sb_port_x, (-S.SB_PORT_Y, S.SB_PORT_Y)

# ---------------- manifold helpers ----------------
def rect(u0, u1, v0, v1): return CS.square((u1 - u0, v1 - v0)).translate((u0, v0))
def rrect(u0, u1, v0, v1, r): return rect(u0 + r, u1 - r, v0 + r, v1 - r).offset(r, ROUND)
def circ(u, v, r): return CS.circle(r).translate((u, v))
def stad(u, v, L, W): return rrect(u - L/2, u + L/2, v - W/2, v + W/2, min(L, W)/2 - 1e-3)
def hull(*cs): return CS.batch_hull(list(cs))
def pz(cs, z0, z1): return MF.extrude(cs, z1 - z0).translate((0, 0, z0))                                   # section (x, y)
def px_(cs, x0, x1): return MF.extrude(cs, x1 - x0).transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])  # section (y, z)
def cylx(y, z, r, x0, x1): return px_(circ(y, z, r), x0, x1)
def cyly(x, z, r, y0, y1): return MF.extrude(circ(z, x, r), y1 - y0).transform([[0, 1, 0, 0], [0, 0, 1, y0], [1, 0, 0, 0]])
def U(*ms): return MF.batch_boolean(list(ms), M3.OpType.Add)
def tris(m):
    me = m.to_mesh(); v = np.asarray(me.vert_properties)[:, :3]; return v[np.asarray(me.tri_verts)].astype(float)
def write_stl(path, V):
    n = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    with open(path, 'wb') as f:
        f.write(b'monolith cup'.ljust(80, b' ')); f.write(struct.pack('<I', len(V)))
        rec = np.zeros(len(V), np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')])); rec['n'] = n; rec['v'] = V.reshape(-1, 9)
        f.write(rec.tobytes())
def mv(V, d): return V + np.asarray(d, float)

cs_cells = hull(*[circ(x, y, CR) for x, y in CELLS])
cs_in = hull(*[circ(x, y, CR + 0.2) for x, y in CELLS], rrect(-1, X_IN, -YI, YI, R_FRONT))
cs_out = hull(cs_in.offset(WALL, ROUND), rrect(-1, X_IN + WALL_BF, -YI - WALL, YI + WALL, R_FRONT + WALL))
cs_col0 = cs_out.offset(COLLAR_CLR, ROUND); cs_col1 = cs_col0.offset(COLLAR_T, ROUND)   # collar inside, outside
X_OUT = X_IN + WALL_BF

# ---------------- parts ----------------
def cup():
    m = pz(cs_out, Z_MOUTH, Z_TOP1) - pz(cs_in, Z_MOUTH - 1, Z_TOP0)
    m = m - pz(cs_in.offset(0.3, ROUND), Z_MOUTH - 1, Z_MOUTH + MOUTH_LEAD)                     # mouth lead-in
    for py in PORT_YS:
        bw, bh = S.USB_RING_W - 2*USB_SQ, S.USB_RING_H - 2*USB_SQ
        m = m - MF.extrude(stad(PORT_X, py, bh, bw), 4).translate((0, 0, Z_TOP0 - 1))
        m = m - pz(stad(PORT_X, py, bh + 2*USB_LEAD, bw + 2*USB_LEAD), Z_TOP0 - 1, Z_TOP0 + USB_LEAD)
    m = m - cylx(VENT_Y, VENT_Z, 1.5, X_IN - 0.5, X_OUT + 0.5)
    return m - cyly(SCREW_X, SCREW_Z, SCREW_HOLE_R, -(YI + WALL + 0.5), YI + WALL + 0.5)
def crush_ribs():
    """crush ribs on the collar's inside, three per flat, CRUSH into the cup's outside"""
    xo, yo = X_OUT, YI + WALL; r, w, out = COLLAR_CLR + CRUSH, CRUSH_W / 2, []
    for x in (-8.0, 6.0, 24.0):                          # clear of the screws at SCREW_X
        for s in (-1, 1): out.append(rect(x - w, x + w, *sorted((s*(yo + COLLAR_CLR + 0.01), s*(yo + COLLAR_CLR - CRUSH)))))
    for y in (-12.0, 0.0, 12.0): out.append(rect(xo + COLLAR_CLR - CRUSH, xo + COLLAR_CLR + 0.01, y - w, y + w))
    xb = -(PR + CR + 0.2 + WALL)                          # back face (between the C2 / C3 arcs)
    for y in (-6.0, 6.0): out.append(rect(xb - COLLAR_CLR - 0.01, xb - COLLAR_CLR + CRUSH, y - w, y + w))
    return CS.batch_boolean(out, M3.OpType.Add)
def cap():
    plate = pz(cs_col1, Z_MOUTH - CAP_T, Z_MOUTH)
    collar = pz(CS.batch_boolean([cs_col1, cs_col0], M3.OpType.Subtract), Z_MOUTH - 0.01, Z_MOUTH + COLLAR_H)
    ribs = pz(crush_ribs(), Z_MOUTH + 1.0, Z_MOUTH + COLLAR_H)
    skirt = pz(CS.batch_boolean([cs_in.offset(-0.1, ROUND), cs_in.offset(-0.1 - SKIRT_T, ROUND)], M3.OpType.Subtract), Z_MOUTH - 0.01, Z_SKIRT1)
    bosses = [cyly(SCREW_X, SCREW_Z, 2.6, -(YI - 0.1), -(YI - 0.1 - BOSS_DEPTH)), cyly(SCREW_X, SCREW_Z, 2.6, YI - 0.1 - BOSS_DEPTH, YI - 0.1)]
    posts = [pz(circ(x, y, OT_R), Z_MOUTH - 0.01, FR_B0 - OT_GAP) for x, y in OT_POSTS]
    m = U(plate, collar, ribs, skirt, *bosses, *posts)
    m = m - pz(CS.batch_boolean([cs_in.offset(0.5, ROUND), cs_in.offset(-0.1 - GROOVE_D, ROUND)], M3.OpType.Subtract), *GROOVE_Z)
    e = YI + WALL + COLLAR_CLR + COLLAR_T
    m = m - cyly(SCREW_X, SCREW_Z, SCREW_HOLE_R, -(e + 1), -(YI + WALL)) - cyly(SCREW_X, SCREW_Z, SCREW_HOLE_R, YI + WALL, e + 1)   # collar
    d = YI - 0.1 - BOSS_DEPTH + PILOT_SOLID                                                       # blind pilots
    return m - cyly(SCREW_X, SCREW_Z, PILOT_R, -(YI + 1), -d) - cyly(SCREW_X, SCREW_Z, PILOT_R, d, YI + 1)
def oring(): return pz(CS.batch_boolean([cs_in, cs_in.offset(-0.1 - GROOVE_D, ROUND)], M3.OpType.Subtract), GROOVE_Z[0] + 0.3, GROOVE_Z[1] - 0.3)
def screws():
    e = YI + WALL + COLLAR_CLR + COLLAR_T; t = YI - 0.1 - BOSS_DEPTH + PILOT_SOLID   # head on the collar, tip short of the pilot end
    return U(cyly(SCREW_X, SCREW_Z, 1.0, -e, -(t + 0.2)), cyly(SCREW_X, SCREW_Z, 1.9, -(e + 1.3), -e),
             cyly(SCREW_X, SCREW_Z, 1.0, t + 0.2, e), cyly(SCREW_X, SCREW_Z, 1.9, e, e + 1.3))
def pad():
    """TPU pad on the cap plate, drawn as installed (it is printed PAD_PROUD taller): pockets for the overtravel posts,
    the screw bosses, and PAD_RELIEF under the C1 / C4 windows and the wire notches so it never bears on the PACK pads"""
    m = pz(CS.batch_boolean([cs_cells.offset(-0.4, ROUND), cs_in.offset(-0.1 - SKIRT_T - 0.3, ROUND)], M3.OpType.Intersect), Z_MOUTH, FR_B0)
    m = m - U(cyly(SCREW_X, SCREW_Z, 3.0, -YI, -(YI - BOSS_DEPTH - 0.5)), cyly(SCREW_X, SCREW_Z, 3.0, YI - BOSS_DEPTH - 0.5, YI))
    m = m - U(*[pz(circ(x, y, OT_R + 0.4), Z_MOUTH - 1, FR_B0 + 1) for x, y in OT_POSTS])
    rel = [circ(x, y, WIN_R + 1.0) for (x, y) in CELLS if x > 0] + [rect(PR, PR + CR + 1, 7.5, 16.0), rect(PR, PR + CR + 1, -16.0, -7.5)]
    return m - pz(CS.batch_boolean(rel, M3.OpType.Add), FR_B0 - PAD_RELIEF, FR_B0 + 1)
def webs():
    """full-length PA12 webs in the front-back gaps (C1-C2, C4-C3): they share the board-heated front pair's heat
    with the back pair. Cells load sideways: the front pair from the board side, the back pair from the back."""
    cells = U(*[pz(circ(x, y, CR + WEB_CLR), S.sb_z_cell0 - 1, S.sb_z_cell1 + 1) for x, y in CELLS])
    w = [pz(rect(-WEB_X, WEB_X, *sorted((s*(PR - WEB_IN), s*(PR + WEB_IN)))), S.sb_z_cell0, S.sb_z_cell1) for s in (-1, 1)]
    w += [pz(rect(-WEB_LINK, WEB_LINK, *sorted((s*(PR + WEB_IN - 0.5), s*(PR + CR)))), S.sb_z_cell0, S.sb_z_cell1) for s in (-1, 1)]
    return U(*w) - cells
def key_slots(clr=KEY_CLR):
    """the rail blocks' tongues (clr=0) or their key slots in the frames' board-side faces (clr=KEY_CLR)"""
    out, xe = [], PR + CR
    for s in (-1, 1):
        for end, (z0, z1) in (('bottom', (FR_B0, FR_B1)), ('top', (FR_T0, FR_T1))):
            y0, y1 = KEY_Y[end]
            out.append(pz(rect(xe - KEY_DEPTH - clr, RAIL_X0 + 0.01, *sorted((s*(y0 - clr), s*(y1 + clr)))), z0 - (1 if clr else 0), z1 + (1 if clr else 0)))
    return out
def carrier():
    """one-piece PA12 cell carrier: the two frames, the spines and the front-back webs. The board rails are separate
    clip-on blocks (rails()) so the front cells can go in from the board side."""
    frame = CS.batch_boolean([cs_cells] + [circ(x, y, WIN_R) for x, y in CELLS], M3.OpType.Subtract)
    m = [pz(frame, FR_B0, FR_B1), pz(frame, FR_T0, FR_T1),
         pz(rect(-PR - CR, -PR - CR + 5.2, -1.5, 1.5), FR_B0, FR_T1),
         pz(rect(-1.5, 1.5, PR + CR - 5.2, PR + CR), FR_B0, FR_T1), pz(rect(-1.5, 1.5, -PR - CR, -PR - CR + 5.2), FR_B0, FR_T1)]
    return U(*m, webs()) - U(*wire_notches(), *key_slots(), *foam_pockets(), sense_channel())
def rails():
    """the four clip-on board-rail blocks with their tongues and the board peg posts (#4, #5): the posts pass through the
    board's peg holes and stop POST_GAP under the board-face wall, so a board-face hit goes post -> rail -> cells, not
    through the parts"""
    m = []
    for s in (-1, 1):
        r = rect(RAIL_X0, S.sb_xb0, *sorted((s*S.SB_BAR_Y[0], s*S.SB_BAR_Y[1])))
        keep = rect(RAIL_X0, S.sb_xb0, *sorted((s*S.SB_BAR_Y[0], s*RAIL_RELIEF_Y)))
        m += [pz(keep, FR_B0, RAIL_GAP[0]), pz(r, S.SB_BAR_Z0, RAIL_GAP[0]), pz(r, RAIL_GAP[1], FR_T1)]
    m += [cylx(y, z, S.CUP_PEG_D / 2, S.sb_xb0 - 0.5, X_IN - POST_GAP) for y, z in S.CUP_PEGS]
    return U(*m, *key_slots(0.0))
def sleeves():
    return U(*[cylx(y, z, SLEEVE[0], S.sb_xb1, S.sb_xb1 + SLEEVE[2]) - cylx(y, z, SLEEVE[1], S.sb_xb1 - 1, S.sb_xb1 + SLEEVE[2] + 1)
               for y, z in S.CUP_PEGS])
def wire_notches():
    """PACK wire tails: one notch right through the bottom frame per side for the power and Kelvin wires together, from
    inside the C1 / C4 weld window out past the frame, since no wire fits the gap between the frame and the cell end
    (one notch, not two: two left a loose chip of frame between them)"""
    out = []
    for n in ('PACK-', 'PACK+'):
        yc = S.sb_pack_holes()[n][0]; k = '4P' if yc > 0 else '1N'; yk = S.sb_slots()[k][0]; s = 1 if yc > 0 else -1
        ya, yb = yk - s*(S.SB_KWIRE_OD/2 + WIRE_NOTCH_CLR), yc + s*(S.SB_PWIRE_OD/2 + WIRE_NOTCH_CLR)
        out.append(pz(rect(PR + 3.0, S.sb_xb0, min(ya, yb), max(ya, yb)), FR_B0 - 0.1, FR_B1 + 0.1))
    return out
def sense_channel():
    """CELL2 sense wire (#9): a channel along y = 0 in the bottom frame's cell-side face, from under the middle of the
    C2-C3 strip (with a wider pocket there for the solder joint) out past the frame's board-side edge"""
    ch = CS.batch_boolean([rect(-PR - 1.5, PR + CR + 0.1, -CH_W/2, CH_W/2), rect(-PR - 1.5, -PR + 1.5, -1.5, 1.5)], M3.OpType.Add)
    return pz(ch, FR_B1 - CH_D, FR_B1 + 0.1)
def foam_rings():
    """foam preload rings (one per cell, under its bottom end), as 2-D sections"""
    out = []
    for x, y in CELLS:
        r = CS.batch_boolean([circ(x, y, FOAM_R[1]), circ(x, y, FOAM_R[0])], M3.OpType.Subtract)
        if x > 0: r = CS.batch_boolean([r, rect(x - CR - 1, x - 1.0, y - CR - 1, y + CR + 1)], M3.OpType.Intersect)   # C1 / C4: away from the PACK pads
        out.append(r)
    return CS.batch_boolean(out, M3.OpType.Add)
def foam_pockets(): return [pz(foam_rings().offset(0.2, ROUND), FR_B1 - FOAM_POCKET, FR_B1 + 0.1)]
def foam():
    """silicone foam rings, drawn as installed: pocket floor up to the strips / cell bottoms"""
    return pz(foam_rings(), FR_B1 - FOAM_POCKET, S.sb_z_tail_b - S.SB_TAB_T) - pz(rect(-PR - 1.5, PR + CR + 1, -CH_W, CH_W), FR_B0, FR_B1 + 1)
def insul_rings():
    """fish-paper rings on the four + ends, on the shoulder under the nickel"""
    r0, r1, t = INSUL; out = []
    for k, (x, y) in zip(S.SB_CELLS, CELLS):
        ring = pz(CS.batch_boolean([circ(x, y, r0), circ(x, y, r1)], M3.OpType.Subtract), 0, t)
        z = S.sb_z_cell1 - 0.45 if S.SB_CELLS[k][1] == 'top' else S.sb_z_cell0 + 0.45 - t
        out.append(ring.translate((0, 0, z)))
    return U(*out)
def filler():
    blk = MF.cube((S.sb_xb0 - 19.0, 37.0, FILL_Z[1] - FILL_Z[0])).translate((19.0, -18.5, FILL_Z[0]))
    cells = U(*[pz(circ(x, y, CR), FILL_Z[0] - 1, FILL_Z[1] + 1) for x, y in CELLS])
    fy0, fy1 = S.CUP_FILL_Y
    keep = pz(CS.batch_boolean([rect(19.0, S.sb_xb0, -fy1, -fy0), rect(19.0, S.sb_xb0, fy0, fy1)], M3.OpType.Add), *FILL_Z)
    return (blk ^ keep) - cells
def bumper(top):
    base = cs_out if top else cs_col1                     # the bottom bumper goes over the cap's collar
    out = base.offset(BUMP_WALL if top else BUMP_WALL_BOT, ROUND); ring = CS.batch_boolean([out, base], M3.OpType.Subtract)
    if top:
        band = pz(ring, Z_TOP1 - BUMP_BAND, Z_TOP1)
        slab = pz(out, Z_TOP1, Z_TOP1 + BUMP_T_TOP) - pz(rrect(PORT_X - 4.5, PORT_X + 4.5, -14.0, 14.0, 2.0), Z_TOP1 - 0.1, Z_TOP1 + BUMP_T_TOP + 1)
    else:
        z0 = Z_MOUTH - CAP_T
        band = pz(ring, z0, z0 + BUMP_BAND); slab = pz(out, z0 - BUMP_T_BOT, z0)
        e = YI + WALL + COLLAR_CLR + COLLAR_T             # pockets over the screw heads
        band = band - cyly(SCREW_X, SCREW_Z, 2.3, -(e + 3), -(e - 0.1)) - cyly(SCREW_X, SCREW_Z, 2.3, e - 0.1, e + 3)
    return band, slab

# ---------------- assembly and masses ----------------
C = dict(RR.C, cup=(214, 214, 208), cap=(170, 186, 200), carrier=(196, 190, 150), filler=(232, 150, 200), oring=(200, 60, 60),
         screw=(110, 110, 116), pad=(236, 156, 80), bump=(118, 72, 50), bslab=(236, 156, 80), vent=(240, 240, 240),
         rails=(170, 160, 110), insul=(200, 40, 40), foam=(120, 120, 130), sleeve=(118, 72, 50))
def assembly():
    A = [('cup', tris(cup()), C['cup'])]
    cell = P.cell_solid()
    for x, y in CELLS: A.append(('cell', mv(cell, (x, y, S.sb_z_cell0)), C['cell']))
    A += [('carrier', tris(carrier()), C['carrier']), ('rails', tris(rails()), C['rails']), ('filler', tris(filler()), C['filler']),
          ('nickel', P.nickel_strips('strips'), C['nickel']), ('tails', P.nickel_strips('tails'), C['tail']),
          ('tails_wire', P.pack_wires(), C['wire']), ('tails_sense', P.sense_wires(), C['wire']),
          ('insul', tris(insul_rings()), C['insul']), ('foam', tris(foam()), C['foam']), ('sleeve', tris(sleeves()), C['sleeve']),
          ('board', P.side_board_dummy(), C['board']), ('ble', P.ble_module(), C['ble']),
          ('pad', tris(pad()), C['pad']), ('oring', tris(oring()), C['oring']), ('cap', tris(cap()), C['cap']),
          ('screw', tris(screws()), C['screw']), ('vent', tris(cylx(VENT_Y, VENT_Z, 5.5, X_OUT, X_OUT + 0.3)), C['vent'])]
    for top in (False, True):
        b, s = bumper(top); k = 'bumpt' if top else 'bumpb'
        A += [(k + '_band', tris(b), C['bump']), (k + '_slab', tris(s), C['bslab'])]
    return A
def group(k): return k.split('_')[0]
PARTS = [(1, 'Cell carrier: frames, spines, front-back webs', 'MJF PA12', 'carrier'),
         (2, 'Board rails (4, clip-on) with the peg posts', 'MJF PA12', 'rails'),
         (3, 'Cells C1-C4, welded 4S', 'BAK N21700CX-65E', 'cell'),
         (4, 'Insulator rings on the + ends (4)', 'fish paper 0.2', 'insul'), (5, 'Preload rings under the cells (4)', 'silicone foam', 'foam'),
         (6, 'Nickel series strips (3)', 'nickel 0.2 x 10', 'nickel'), (7, 'PACK pads, CELL1/3 tongues; 18 / 28 AWG wires', 'nickel; PTFE wire', 'tails'),
         (8, 'Gap filler, board to the front cells (dispensed)', 'GEL 30, 3.1 g/cm3', 'filler'),
         (9, 'Board 1.6 mm, thermal vias under the power stages', 'FR4, 6 layers', 'board'),
         (10, 'Retaining sleeves on the posts (4)', 'TPU 95A', 'sleeve'),
         (11, 'Cup: 5 closed sides, USB-C seal bores in the top wall', 'MJF PA12, 1.2 / 1.8', 'cup'),
         (12, 'Pad on the cap: preloads the core', 'TPU 95A, 15 % gyroid', 'pad'),
         (13, 'O-ring, 2.0 mm cord (radial)', 'silicone 60A', 'oring'), (14, 'Bottom cap: plate, collar, skirt, posts', 'MJF PA12', 'cap'),
         (15, 'Screws M2 (2), thread-forming, below the seal', 'stainless', 'screw'), (16, 'Pressure vent (after the leak test)', 'ePTFE', 'vent'),
         (17, 'Bottom bumper, 4 mm, over the collar', 'TPU 95A', 'bumpb'), (18, 'Top bumper, port well', 'TPU 95A', 'bumpt')]
NUM = {k: n for n, _, _, k in PARTS}
RHO = dict(cup=1.01, cap=1.01, carrier=1.01, rails=1.01, screw=7.9, oring=1.15, filler=3.1, nickel=8.9, tails=8.9, vent=1.0,
           insul=1.1, foam=0.3, sleeve=1.2)
def masses(A):
    m = {}
    for k, V, _ in A:
        g = group(k)
        r = RHO.get(g, 1.2*0.15 if g == 'pad' else 1.2*0.30 if k.endswith('_slab') else (1.2 if k.endswith('_band') else None))
        if r is None: continue
        m[g] = m.get(g, 0) + vol(V) * r
    m['board'] = board_g(S.sb_board_area, S.SB_PCB_T); m['cell'] = 4 * CELL_G
    return m
def size(A):
    V = np.vstack([V for _, V, _ in A]).reshape(-1, 3); return V.max(0) - V.min(0)
def wall_deflection(t, p_kpa, a=37.5, b=80.0):
    """centre deflection (mm) of a flat a x b wall panel of thickness t under p_kpa, simply supported (Roark, b/a ~2:
    alpha 0.1106), E 1700 MPa for MJF PA12: the upper bound the review used"""
    return 0.1106 * p_kpa * 1e-3 * a**4 / (1700 * t**3)
def checks():
    """assembly checks (positive = clearance), in the style of monolith_shell. The 2026-10-24 review fixes add: one-piece
    parts, screw edge distance and blind pilots, the axial stack (skirt gap, overtravel posts, pad preload), the USB-C
    ring in the top wall, the posts under the board-face wall, and the CELL2 wire channel."""
    bw, bh = S.USB_RING_W - 2*USB_SQ, S.USB_RING_H - 2*USB_SQ
    pk_y = [abs(S.sb_pack_holes()[n][0]) for n in ('PACK-', 'PACK+')]
    return {
        'carrier is one body': 1 - len(carrier().decompose()) + 0.0,
        'board rails: four bodies (clip-on blocks)': 4 - len(rails().decompose()) + 0.0,
        'cap is one body': 1 - len(cap().decompose()) + 0.0,
        'board fits the bore (y, per side)': YI - S.sb_board_w/2 - 0.3,
        'tallest part under the board-face wall (x)': X_IN - (S.sb_xb1 + S.SB_OUT_H) - 0.3,
        'USB-C body under the board-face wall (x)': X_IN - (S.sb_port_x + S.USB_UP) - 0.3,
        'board-face wall at 25 kPa (simply supported bound) stays off the parts (x)': (X_IN - (S.sb_xb1 + S.SB_OUT_H)) - wall_deflection(WALL_BF, 25) - 0.05,
        'peg posts under the board-face wall (x, gap 0.1-0.5)': min(X_IN - POST_GAP - (S.sb_xb1 + 0.1), POST_GAP - 0.1, 0.5 - POST_GAP),
        'retaining sleeves under the board-face wall (x)': X_IN - (S.sb_xb1 + SLEEVE[2]) - 0.5,
        'peg-slot float lets the seal bores centre the ports (y, float >= bore lead-in)': (S.CUP_PEG_SLOT[0] - S.CUP_PEG_D)/2 - USB_LEAD + 1e-9,
        'peg slots keep the seal rings in the top wall (z, ring 0.35 in - float >= 0.2)': (TOP_T - 1.5) - (S.CUP_PEG_SLOT[1] - S.CUP_PEG_D)/2 - 0.2 + 1e-9,
        'retaining sleeves cover the peg slots at full float (y, >= 0.3)': SLEEVE[0] - (S.CUP_PEG_SLOT[0] - S.CUP_PEG_D)/2 - S.CUP_PEG_SLOT[0]/2 - 0.3 + 1e-9,
        'USB-C ring ends inside the top wall (z, ring band 1.5, >= 0.3)': TOP_T - 1.5 - 0.3 + 1e-9,
        'board top edge is a backstop under the top wall (z, 0.05-0.2)': min(Z_TOP0 - S.sb_zb1 - 0.05, 0.2 - (Z_TOP0 - S.sb_zb1)),
        'USB-C seal squeeze per side (0.12-0.18)': min(USB_SQ - 0.12, 0.18 - USB_SQ),
        'seal bores fit the top wall beside the board (y)': (S.SB_STOP_Y0 - (S.SB_PORT_Y + bw/2 + USB_LEAD)),
        'carrier top frame >= 0.9 thick (z)': (FR_T1 - FR_T0) - 0.9,
        'cap skirt top under the carrier frame (z, >= 0.5 at -3 sigma)': (FR_B0 - Z_SKIRT1) - 0.5 - 0.5,
        'overtravel posts stop before the skirt touches (z)': (FR_B0 - Z_SKIRT1) - OT_GAP - 0.3,
        'overtravel posts under frame material, not a window or notch': min(
            min(np.hypot(x - cx, y - cy) for cx, cy in CELLS) - WIN_R - OT_R for x, y in OT_POSTS),
        'pad preload: printed proud 1.0-1.5': min(PAD_PROUD - 1.0, 1.5 - PAD_PROUD),
        'pad relief under the PACK pads deeper than the proud (z)': PAD_RELIEF - PAD_PROUD - 0.2,
        'skirt root behind the groove >= 1.2': SKIRT_T - GROOVE_D - 1.2 + 1e-9,
        'carrier bottom frame below the bottom strips (z)': (S.sb_z_tail_b - S.SB_PACK_T) - FR_B1,
        'carrier top frame bears on the top wall (z)': 0.0 if abs(FR_T1 - Z_TOP0) < 1e-9 else -1.0,
        'O-ring groove inside the skirt (z)': min(GROOVE_Z[0] - Z_MOUTH, Z_SKIRT1 - GROOVE_Z[1]) - 1.0 + 1e-9,
        'screws below the O-ring (outside the seal, z)': (GROOVE_Z[0] - 0.3) - (SCREW_Z + SCREW_HOLE_R),
        'screw holes: ligament under them in the cup wall (z, >= 1.2)': (SCREW_Z - SCREW_HOLE_R - Z_MOUTH) - 1.2,
        'screw holes clear of the mouth lead-in (z)': (SCREW_Z - SCREW_HOLE_R) - (Z_MOUTH + MOUTH_LEAD),
        'blind pilots: solid behind them in the bosses (>= 1.2)': PILOT_SOLID - 1.2 + 1e-9,
        'collar covers the O-ring band (z)': (Z_MOUTH + COLLAR_H) - (GROOVE_Z[1] + 0.5),
        'board rails clear of the BLE module (y)': S.sb_ant_y[0] - S.SB_BAR_Y[1] - 0.3,
        'board rails clear of the PACK pads (y, rail stub to the pad edge)': min(abs(y0) for n in ('PACK-', 'PACK+')
                                                       for y0, y1 in S.sb_fingers(n).values() for y0 in (y0, y1)) - RAIL_RELIEF_Y - 0.5,
        'bottom key slots clear of the wire notch (y, web >= 0.6)': (abs(S.sb_slots()['4P'][0]) - S.SB_KWIRE_OD/2 - WIRE_NOTCH_CLR)
                                                       - (KEY_Y['bottom'][1] + KEY_CLR) - 0.6,
        'key slots clear of the weld windows (frame left >= 1.0)': min(np.hypot(PR + CR - KEY_DEPTH - KEY_CLR - PR, max(PR - (y1 + KEY_CLR), 0))
                                                       for y0, y1 in KEY_Y.values()) - WIN_R - 1.0,
        'wire notch: power wire inside the frame edge (y)': (PR + CR) - (max(pk_y) + S.SB_PWIRE_OD/2 + WIRE_NOTCH_CLR),
        'CELL2 channel: wire sits below the frame face (z)': CH_D - S.SB_KWIRE_OD - 0.2 + 1e-9,
        'wire notch: power wire under the PACK pad clears the pad relief (z, >= 0.5)':
            (S.sb_z_tail_b - S.SB_PACK_T - S.SB_PWIRE_OD) - (FR_B0 - PAD_RELIEF) - 0.5,
        'CELL2 channel clear of the C1 / C4 rims (y)': (PR - CR) - CH_W/2,
        'CELL2 channel: frame left under it (z, >= 0.6)': (FR_B1 - FR_B0) - CH_D - 0.6,
        'foam pockets: frame left under them (z, >= 0.8)': (FR_B1 - FR_B0) - FOAM_POCKET - 0.8,
        'insulator rings inside the can (r)': CR - INSUL[0] - 0.2,
        'board rails clear of the PACK pads (z, rail above the pads)': S.SB_BAR_Z0 - (S.sb_z_tail_b + 0.5),
        'gap filler below the BLE module (z)': (S.sb_ant_zc - S.SB_ANT_MOD[0]/2) - FILL_Z[1] - 1.0,
        'webs: room between front and back cells (gap - 2 x clearance)': (2*PR - 2*CR) - 2*WEB_CLR,
        'bore corner radius >= 2 x O-ring cord': R_FRONT - 2*ORING_CS,
    }

# ---------------- sheets ----------------
SS, INK, MUTED, RULE, ACCENT = RR.SS, RR.INK, RR.MUTED, RR.RULE, RR.ACCENT
LEG = [('PA12 cup', C['cup']), ('PA12 cap', C['cap']), ('PA12 carrier', C['carrier']), ('cells', C['cell']), ('board', C['board']),
       ('BLE module', C['ble']), ('gap filler', C['filler']), ('O-ring', C['oring']), ('screw', C['screw']),
       ('TPU pad / bumper slab', C['pad']), ('TPU bumper band', C['bump']), ('nickel strip', C['nickel']), ('nickel tail / pad', C['tail']), ('PACK wire', C['wire'])]
def save(sh, name): sh.img.resize((sh.W, sh.H), Image.LANCZOS).save(os.path.join(HERE, name)); print('wrote', name)
def balloons(sh, pid, gid, BAL, dist=70):
    for g_ in dict.fromkeys(gid):
        a = RR.visible_anchor(pid, [i for i, x in enumerate(gid) if x == g_])
        if a is None or g_ not in NUM: continue
        ax, ay = a; ang = np.radians(BAL.get(g_, 0)); d = dist + (60 if g_.startswith('bump') else 0)
        bx, by = ax + d*np.cos(ang), ay - d*np.sin(ang); v = np.array([bx - ax, by - ay]); v /= np.linalg.norm(v)
        sh.line([(ax, ay), (bx - v[0]*13, by - v[1]*13)], ACCENT, 1.2); sh.dot(ax, ay, 3, ACCENT); sh.balloon(bx, by, NUM[g_])

def sheet_exploded(A, m):
    total = sum(m.values()); w, d, L = size(A)
    sh = RR.Sheet(2700, 1400)
    sh.header('Monolith cup: one radial O-ring, no aluminium',
              'The bench-built core goes in from the bottom until the USB-C faces seat in the closed top wall; a bottom cap seals it. '
              f'The power stage dumps its heat into the cells. BAK N21700CX-65E cells, about 91 Wh. Pack {w:.1f} x {d:.1f} x {L:.1f} mm, about {total:.0f} g.')
    sh.panel_title(40, 128, 'Assembled', 640)
    R = camera((1.0, -1.1, 0.65)); o1 = (250, 660); pxs = 5.0
    sh.render([(V, c) for _, V, c in A], R, o1, pxs); pj = RR.proj(R, o1, pxs)
    sh.callouts([(pj((PORT_X, 9, Z_TOP1 + BUMP_T_TOP)), 'Port well through the top bumper'),
                 (pj((X_OUT, -8, 50)), 'Board face: plain 2.0 mm PA12,\nno cover, no seam'),
                 (pj((X_OUT, 0, VENT_Z)), 'ePTFE vent, fitted last:\nits hole is the leak-test port'),
                 (pj((X_OUT + 2, -YI, Z_MOUTH - CAP_T - BUMP_T_BOT + 1)), '4 mm bottom bumper over the cap and its collar\n(the pad inside adds the rest of the stroke)')],
                475, 'r', 150)
    sh.panel_title(780, 128, 'Exploded, in assembly order', 1180)
    EX = dict(cell=(0, 0, -75), carrier=(0, 0, -75), nickel=(0, 0, -75), tails=(0, 0, -75), board=(16, 0, -75), ble=(16, 0, -75),
              filler=(8, 0, -75), cup=(0, 0, 25), pad=(0, 0, -118), oring=(0, 0, -136), cap=(0, 0, -152), screw=(0, 0, -152), vent=(14, 0, 25),
              rails=(9, 0, -75), insul=(0, 0, -75), foam=(0, 0, -75), sleeve=(22, 0, -75))
    ex, gid = [], []
    for k, V, c in A:
        g_ = group(k); dd = EX.get(g_, (0, 0, -182) if g_ == 'bumpb' else (0, 0, 50))
        ex.append((mv(V, dd), c)); gid.append(g_)
    R2 = camera((0.5, -1.25, 0.32)); o2 = (1180, 690); px2 = 3.0
    pid = sh.render(ex, R2, o2, px2)
    balloons(sh, pid, gid, dict(cup=160, carrier=150, cell=200, nickel=330, tails=10, filler=20, board=0, pad=200, oring=0,
                                cap=200, screw=340, vent=0, bumpb=200, bumpt=170, rails=30, insul=120, foam=230, sleeve=20))
    x0 = 2010; sh.panel_title(x0, 128, 'Parts', 650)
    rows = [[str(n), name, mat, f'{m.get(k, 0):.1f}' if m.get(k, 0) >= 0.05 else '<0.1'] for n, name, mat, k in PARTS]
    rows.append(['', 'Pack total', '', f'{total:.1f}'])
    y = sh.table(x0, 176, ['#', 'Part', 'Material', '>g'], rows, [36, 344, 200, 70], 13, bold_last=True, rh=26)
    for i, s in enumerate(('Board mass is estimated (FR4 + 6-layer copper); parts on it are not included.',
                           'TPU pad 15 % and bumper slabs 30 % gyroid; bumper bands solid. Cells 75 g each (datasheet max).',
                           'Not drawn: the label (open item), thermal vias in the board. Pad drawn as installed (printed 1.2 mm taller).')):
        sh.text(x0, y + 14 + 24*i, s, 13, fill=MUTED)
    sh.line([(40, 1330), (2660, 1330)], RULE, 1.5); sh.legend(LEG, 40, 1350, 14)
    save(sh, 'monolith_cup_exploded.png')

def sheet_sections(A):
    core = [(k, V, c) for k, V, c in A if not k.startswith('bump')]
    sh = RR.Sheet(2700, 1300)
    sh.header('Monolith cup: sections', 'Cut from the same meshes as the STLs. Board and USB-C are envelopes; parts on the board are not drawn. '
              'The O-ring is drawn as squeezed.')
    z_a = 40.0; pxa = 10.0
    sh.panel_title(40, 128, f'A-A   across the pack through the gap filler (z = {z_a:.0f} mm), from the port end', 1380)
    oa = (600, 600); tp = sh.section(core, 2, z_a, 0, 1, oa, pxa)
    for (x, y), nm in zip(CELLS, [S.SB_CELLS[k][0] for k in S.SB_CELLS]):
        q = tp(x, y); sh.text(q[0], q[1], nm, 22, True, fill='white', anchor='mm')
    sh.callouts([(tp(-YI - WALL/2, 6), '1.2 mm MJF PA12 cup wall,\nclosed all round'),
                 (tp(-PR - CR + 2.5, 0), 'Carrier spine (the core is rigid)'),
                 (tp(0, PR + CR - 2), 'Side spine'),
                 (tp(0, -PR), 'PA12 web, full length: carries heat\nfrom the front pair to the back pair')], 300, 'l', 230)
    sh.callouts([(tp(X_IN + WALL_BF/2, 0), 'Board face: 2.0 mm cup wall,\n0.5 mm over the tallest part'),
                 (tp(S.sb_xb0 + 0.8, -2), 'Board on the clip-on rails;\nthermal vias under the power stages'),
                 (tp(PR + CR + 1.0, -PR), 'Gap filler: B.Cu to the two front cells.\nThe cells are the heat sink'),
                 (tp(PR + CR + 1.0, PR), 'Rails stop over the filler zone\n(they carry the board above and below it)'),
                 (tp(X_IN - 1, -YI + 1), 'Bore corners r 4 for the O-ring')], 1010, 'r', 200)
    sh.dim((tp(-YI - WALL, 0)[0], tp(0, -YI - WALL - 4)[1]), (tp(X_OUT, 0)[0], tp(0, -YI - WALL - 4)[1]), 30, f'{X_OUT + YI + WALL:.1f}')
    sh.dim(tp(X_OUT, -YI - WALL), tp(X_OUT, YI + WALL), 40, f'{2*(YI + WALL):.1f}')
    pxb = 6.4; ob = (1700, 430)
    sh.panel_title(1480, 128, f'B-B   along the pack through a USB-C port (y = {PORT_YS[1]:.1f} mm)', 1180)
    tq = sh.section(core, 1, PORT_YS[1] + 0.02, 2, 0, ob, pxb)
    sh.text(ob[0] + pxb*(Z_MOUTH - CAP_T), 640, 'bottom (cap)', 15, fill=MUTED, anchor='mm'); sh.text(ob[0] + pxb*Z_TOP1, 640, 'port end', 15, fill=MUTED, anchor='mm')
    sh.callouts([(tq(Z_TOP1 - 0.5, PORT_X), 'Ports seat in the closed\ntop wall as the core is\npushed home: no seam here'),
                 (tq(FR_T0 + 0.6, -6), 'Carrier top frame\non the top wall')], 2320, 'r', 200, size=14)
    sh.callouts([(tq(Z_MOUTH - CAP_T/2, 0), 'Cap plate on the rim (hard stop);\nposts stop the core 0.6 short of the skirt'),
                 (tq((Z_MOUTH + FR_B0)/2, -8), 'TPU pad: preloads the core\n(printed 1.2 proud)'),
                 (tq(sum(GROOVE_Z)/2, X_IN - 0.6), 'O-ring in the skirt\n(radial, ~25 %)')], 1660, 'l', 200, size=14)
    pxd, (y0, y1, z0, z1) = 15.0, (-27.5, 27.5, Z_MOUTH - 3.0, Z_MOUTH + 12.0); dw, dh = int((y1 - y0)*pxd), int((z1 - z0)*pxd)
    det = RR.Sheet(dw, dh); od = (-y0*pxd, z1*pxd)
    det.section(core, 0, SCREW_X + 0.02, 1, 2, od, pxd)
    DX, DY = 1560, 760
    sh.panel_title(1480, 700, f'C-C   the cap end, cut at x = {SCREW_X:.0f} mm through both screws', 1180)
    sh.img.paste(det.img, (DX*SS, DY*SS)); sh.rect(DX, DY, DX + dw, DY + dh, outline=RULE, width=1)
    td = lambda y, z: (DX + od[0] + pxd*y, DY + od[1] - pxd*z)
    sh.callouts([(td(YI + WALL/2, Z_MOUTH + 9), 'Cup wall'),
                 (td(YI - 0.1 - GROOVE_D/2 - 0.2, sum(GROOVE_Z)/2), 'O-ring between skirt and bore'),
                 (td(YI + WALL + COLLAR_CLR + COLLAR_T + 0.6, SCREW_Z), 'M2 through the collar and the wall into\na blind skirt boss, below the O-ring'),
                 (td(YI + WALL + COLLAR_CLR + COLLAR_T/2, Z_MOUTH + 6.5), 'Collar holds the mouth\nagainst the O-ring'),
                 (td(10, Z_MOUTH - CAP_T/2), 'Cap plate'),
                 (td(0, Z_MOUTH + 4.0), 'TPU pad'),
                 (td(-10, FR_B0 + 0.8), 'Carrier frame, cells above')], DX + dw + 40, 'r', DY, size=14)
    sh.line([(40, 1240), (2660, 1240)], RULE, 1.5); sh.legend(LEG, 40, 1256, 14)
    save(sh, 'monolith_cup_sections.png')

def sheet_compare(A, m):
    At = RR.assembly(); mt, _ = RR.masses(At, None)
    for k in ('cage', 'frame', 'holder'): mt[k] *= 1.2          # TPU at 1.2 g/cm3 (the tray script uses 1.0)
    mt['gappad'] = 1.0; mt['unmodelled'] = 0.65
    tt, tc = sum(mt.values()), sum(m.values())
    wt, dt, Lt = RR.SIZE(); su = size(A)
    sh = RR.Sheet(2700, 1300)
    sh.header('Side tray (retired) vs the cup (current)', 'Same FEB 21700G cells, board outline, slots, nickel tongues and BLE position. '
              'The cup drops the aluminium cover, the wedge, the TPU cage and frame, the fish paper and the standoffs.')
    R = camera((1.0, -1.1, 0.65)); pxs = 3.9
    for title, asm, cx in (('Side tray (retired)', At, 330), ('Cup (current)', A, 900)):
        sh.panel_title(cx - 260, 128, title, 520); sh.render([(V, c) for _, V, c in asm], R, (cx - 50, 580), pxs)
    zc = 40.35; pxa = 6.0
    sh.panel_title(1480, 128, f'A-A at z = {zc:.0f} mm, same scale', 1180)
    sh.section([(k, V, c) for k, V, c in At if not k.startswith('cap')], 2, zc, 0, 1, (1780, 430), pxa); sh.text(1780, 650, 'tray', 16, True, anchor='mm')
    sh.section([(k, V, c) for k, V, c in A if not k.startswith('bump')], 2, zc, 0, 1, (2330, 430), pxa); sh.text(2330, 650, 'cup', 16, True, anchor='mm')
    cat = lambda mm, keys: sum(mm.get(k, 0) for k in keys)
    rows_w = [('Cells, board, nickel', ('cell', 'board', 'nickel', 'tails'), ('cell', 'board', 'nickel', 'tails')),
              ('Tray / cup (+ wedge)', ('shell', 'wedge'), ('cup',)), ('Cover / cap (+ standoffs)', ('cover', 'stand'), ('cap',)),
              ('Cell holder (+ pad)', ('cage', 'frame', 'holder'), ('carrier', 'pad')), ('Bumpers / crush caps', ('capb', 'capt'), ('bumpb', 'bumpt')),
              ('Seal + fasteners', ('unmodelled',), ('oring', 'screw', 'vent')), ('Thermal interface', ('gappad',), ('filler',)),
              ('Insulation sheet + hold-downs', ('insul', 'rings', 'hold'), ())]
    rows = [[n, f'{cat(mt, a):.1f}', f'{cat(m, b):.1f}', f'{cat(m, b) - cat(mt, a):+.1f}'] for n, a, b in rows_w]
    rows.append(['Pack total', f'{tt:.1f}', f'{tc:.1f}', f'{tc - tt:+.1f}'])
    sh.panel_title(40, 760, 'Weight by function (g)', 1240)
    sh.table(40, 810, ['', '>Tray', '>Cup', '>Cup - tray'], rows, [440, 200, 200, 220], 15, bold_last=True, rh=36)
    rows2 = [['Outside (mm)', f'{wt:.1f} x {dt:.1f} x {Lt:.1f}', f'{su[0]:.1f} x {su[1]:.1f} x {su[2]:.1f}'],
             ['Seal joints', 'bead round the cover, 2 port rings, vent', '1 radial O-ring, 2 port rings, vent'],
             ['Core install', 'drop in, lift 2.5 mm, wedge', 'push in from the bottom, cap on'],
             ['Heat path for bursts', 'board -> 1 mm Al cover', 'board -> vias + filler -> cells, webs'],
             ['100 W from full (model)', '~5 min at 100 W', '~9 min (~10 with the P0 loss cuts)'],
             ['88 W charge, empty to full', '~108 min', '~127 min (~120 with the P0 cuts)'],
             ['BLE antenna', 'Al cover over the board', 'no metal at all'],
             ['Label', 'laser-marked on the Al cover', 'open: emboss, or a small plate']]
    sh.panel_title(1320, 760, 'Side by side', 1340)
    y2 = sh.table(1320, 810, ['', 'Tray', 'Cup'], rows2, [330, 500, 510], 14, rh=36)
    sh.text(1320, y2 + 14, 'Thermal rows: research_notes/.../model/thermal_rundown.py (FEB cells, 25 C ambient, estimates).', 13, fill=MUTED)
    save(sh, 'monolith_cup_vs_tray.png')

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    A = assembly(); m = masses(A)
    for k, v in checks().items(): print(f"  {'ok ' if v >= 0 else 'BAD'} {v:6.2f}  {k}")
    for n, name, mat, k in PARTS: print(f'{n:3d} {name:58s} {m.get(k, 0):7.1f} g')
    print('total', round(sum(m.values()), 1), 'g   size (x, y, z)', np.round(size(A), 1))
    if which in ('all', 'stl'):
        for k in ('cup', 'cap', 'carrier', 'rails', 'sleeve', 'foam', 'pad', 'oring', 'filler', 'bumpb_band', 'bumpb_slab', 'bumpt_band', 'bumpt_slab'):
            write_stl(os.path.join(HERE, f'monolith_cup_{k}.stl'), np.vstack([V for kk, V, _ in A if kk == k]))
        print('wrote monolith_cup_*.stl')
    if which in ('all', 'exploded'): sheet_exploded(A, m)
    if which in ('all', 'sections'): sheet_sections(A)
    if which in ('all', 'compare'): sheet_compare(A, m)
