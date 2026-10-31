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
import os, sys, struct, math, numpy as np
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
                                    # coupon), a rounded rectangle like the ring (USB_RING_R), not a stadium
# Housing pocket (real-board check, 2026-10-30): the connector's hard front housing (d 1.5-2.5 behind the face) reaches
# 0.35 into the top wall and is wider than the seal bore at its corners (~0.5 mm), so the wall's inside face is pocketed
# round it up to just under the ring (plus the board's z float), and the ring's lead-in starts there. USB_LEAD is now
# the peg-slot y float the old 45 deg lead-in had to cover; the pocket covers it.
HOUSING_CLR = 0.15                  # pocket round the housing, each side
POCKET_LEAD = 0.25                  # loft from the pocket up to the seal bore (the ring squeezes in over it)
BOARD_ZFLOAT = 0.1                  # board top edge to the top wall (it can rise this much before it stops)
FR_B0 = S.cup_fr_b0; FR_B1 = FR_B0 + 1.6                            # carrier bottom frame, under the bottom strips
FR_T0, FR_T1 = S.sb_z_cell1 + S.TAB_T, Z_TOP0                       # carrier top frame, bears on the top wall
# Cap end (#1, #2, #7). The skirt top stays SKIRT_GAP under the carrier frame, so no rigid contact crosses the groove;
# OT_POSTS on the cap plate are the overtravel stop instead. The O-ring sits higher, the M2 screws go in under it with a
# real ligament below, and the cup's mouth is thickened outward (MOUTH_T) so its flats don't bow off the O-ring.
SKIRT_GAP = 1.1                    # skirt top to the carrier frame underside
Z_SKIRT1 = FR_B0 - SKIRT_GAP       # cap skirt top
SKIRT_L = 7.5                      # skirt length = cup mouth to skirt top (was 7.0)
Z_MOUTH = Z_SKIRT1 - SKIRT_L       # open bottom end of the cup
CAP_T = 1.6                        # cap plate below the mouth (lands on the cup rim: hard stop)
SKIRT_T = 2.6                      # radial skirt wall: 1.2 mm root behind the groove (was 2.1, 0.7 root)
ORING_CS, GROOVE_D = 2.0, 1.4      # 2.0 mm cord, groove 2.6 wide x 1.4 deep (+0.1 bore gap) -> ~25 % squeeze
GROOVE_Z = (Z_MOUTH + 3.9, Z_MOUTH + 6.5)
SCREW_X, SCREW_Z = 16.0, Z_MOUTH + 2.4   # two M2 (thread-forming), radially through the thick mouth of the cup wall into blind
SCREW_HOLE_R, PILOT_R, PILOT_SOLID = 1.1, 0.8, 1.2   # pilots in the skirt bosses, below the O-ring; >= 1.2 solid behind
BOSS_DEPTH = 5.0                   # skirt boss depth (y)
MOUTH_T, MOUTH_H, MOUTH_TAPER = 2.4, SKIRT_L, 0.8   # cup wall at the mouth, thickened outward over the O-ring band, tapering
                                   # back to WALL at the top (2026-10-31: replaces the cap's 1.5 mm outer collar, which flexed
                                   # off the cap plate; plate model in docs/reviews/2026-10-31-mouth-band/)
MOUTH_LEAD = 0.8                   # lead-in at the cup mouth for the O-ring (0.3 deep over this height)
OT_POSTS = [(-(PR + CR) + 2.6, 0.0), (0.0, 0.0), (0.0, -(PR + CR) + 2.6), (0.0, PR + CR - 2.6)]   # overtravel posts (x, y)
OT_R, OT_GAP = 1.5, 0.6            # post radius; gap to the frame underside at nominal
PAD_PROUD = 1.2                    # TPU pad printed this much taller than drawn (10 % gyroid since 2026-10-31): roughly
                                   # 8-40 N of preload on the core (~15-80 N at 15 %); check the core can't rattle
PAD_RELIEF = 1.5                   # pad pocketed this deep under the C1 / C4 windows and the wire notches (PACK pads, wires)
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
KEY_RIB = (0.25, 0.5, 0.4)         # crush rib on each side face of a tongue (2026-10-28): height (0.15 into the slot wall past
                                   # the clearance), width (z), lead-in length at the tip. Holds the blocks in on the bench
                                   # until the board is soldered; the cup captures them after that
POST_GAP = 0.3                     # peg posts stop this far under the board-face wall at nominal
SLEEVE = (1.9, 0.85, 1.0)          # TPU retaining sleeve pushed down each post onto F.Cu: outer r, bore r, height (pushed
                                    # down to touch, not clamp, so the board can still float in the board's peg slots)
# Cells (#3, #6). An insulator ring on every + end (C1 / C3 top, C2 / C4 bottom) under the nickel, so a strip pushed
# into a frame window lands on paper, not on the cell's own - shoulder; a foam ring in a pocket in the bottom frame
# pushes each cell up onto the top frame, so the cells can't float on the welds.
INSUL = (10.6, 4.7, 0.2)           # fish-paper ring: outer r, inner r (measure the BAK + cap first), thickness
FOAM_R, FOAM_POCKET = (WIN_R + 0.3, CR - 1.2), 0.6   # foam ring radii, its pocket depth in the bottom frame (not under
                                    # the PACK pads: C1 / C4 keep only the half away from the board)
CH_W, CH_D = 1.0, 0.95              # CELL2 sense-wire channel in the bottom frame (y = 0), from under the strip to the edge
WEB_X, WEB_IN, WEB_CLR, WEB_LINK = 2.0, 4.5, 0.05, 0.6   # front-back webs (heat sharing), link out to the side spine
BUMP_T_TOP, BUMP_T_BOT, BUMP_BAND, BUMP_WALL = 6.0, 3.0, 7.0, 2.0   # mass trim 2026-10-31 (was 8 / 4 / 9): pick the
                                    # final slabs in the drop series
SLAB_FILL, PAD_FILL = 0.20, 0.10    # TPU gyroid infill: bumper slabs (was 30 %), cap pad (was 15 %), mass trim 2026-10-31
BUMP_WALL_BOT = 1.0                 # bottom band over the cup's thick mouth (the 2.4 mm PA12 under it is the edge's backbone)
# Wrap label (label plan 2026-10-27, art in hardware/label/): printed vinyl round the whole cup, its top and bottom edges
# TUCKed under the bumpers. The bottom bumper grows a lip over the label's lower edge; the top band is relieved over it.
LABEL_T, LABEL_TUCK, LABEL_GAP = 0.15, 3.0, 0.6   # vinyl + laminate; edge under each bumper; bottom edge over the mouth band
LABEL_RELIEF = 0.45                 # bumper inside over the label, off the cup (clears the two-layer seam with TPU tolerance)
LEAD_IN = (0.6, 30.0)               # chamfer where a bumper meets the label edge: depth, angle off the axis
RELIEF_UP = 1.5                     # top band relief runs this far past the label's top edge (label placed high)
LABEL_Z = (0.0, 0.0)                # set below, once the cup heights are known
LIP_WALL, LIP_FLOOR = 1.0, 0.8      # bottom-bumper lip over the label: wall, and the ledge joining it to the mouth band
PORT_DIGITS = ((S.SB_PORT_Y, '1'), (-S.SB_PORT_Y, '2'))   # raised on the top bumper beside each port (USB1 at +y, as in the
                                    # thermal model's port labels)
DIGIT_H, DIGIT_RAISE, BASE_TEXT, BASE_TEXT_H, BASE_TEXT_D = 4.0, 0.4, '91 Wh', 7.0, 0.6   # bottom: debossed rating
PORT_X, PORT_YS = S.sb_port_x, (-S.SB_PORT_Y, S.SB_PORT_Y)
LABEL_Z = (Z_MOUTH + MOUTH_H + LABEL_GAP, Z_TOP1 - BUMP_BAND + LABEL_TUCK)   # label edges on the cup
LIP_TOP, RELIEF_TOP = LABEL_Z[0] + LABEL_TUCK, LABEL_Z[1] + RELIEF_UP          # bottom lip top; top band relief top

# ---------------- manifold helpers ----------------
def rect(u0, u1, v0, v1): return CS.square((u1 - u0, v1 - v0)).translate((u0, v0))
def rrect(u0, u1, v0, v1, r): return rect(u0 + r, u1 - r, v0 + r, v1 - r).offset(r, ROUND)
def circ(u, v, r): return CS.circle(r).translate((u, v))
def stad(u, v, L, W): return rrect(u - L/2, u + L/2, v - W/2, v + W/2, min(L, W)/2 - 1e-3)
def hull(*cs): return CS.batch_hull(list(cs))
def text_cs(txt, h, x, y, mirror=False):
    """outlined text (DejaVu Sans Bold) as a cross-section, cap height h, centred on (x, y); mirror for a bottom face"""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    fp = FontProperties(family='DejaVu Sans', weight='bold')
    k = h / TextPath((0, 0), 'H', size=1.0, prop=fp).get_extents().height
    tp = TextPath((0, 0), txt, size=k, prop=fp); e = tp.get_extents()
    polys = [np.c_[(-1 if mirror else 1) * (p[:, 0] - (e.x0 + e.x1) / 2), p[:, 1] - (e.y0 + e.y1) / 2] for p in tp.to_polygons() if len(p) > 2]
    return CS(polys, M3.FillRule.EvenOdd).translate((x, y))
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
cs_mouth = hull(cs_out, cs_in.offset(MOUTH_T, ROUND))   # the cup's thick mouth band, outside
X_OUT = X_IN + WALL_BF

# ---------------- parts ----------------
Z_RING0 = Z_TOP1 - S.USB_RING_D[1]                                # ring's back edge, board at nominal (ports flush)
Z_HOUSING0 = Z_TOP1 - S.USB_HOUSING[3]                             # housing's back edge
Z_POCKET = Z_RING0 + BOARD_ZFLOAT + 0.02                           # top of the housing pocket in the top wall
def usb_bore(py, grow=0.0):
    """seal bore section: the A4 ring less USB_SQ each side, same rounded-rectangle shape (grow = offset outward)"""
    bw, bh, r = S.USB_RING_W - 2*USB_SQ + 2*grow, S.USB_RING_H - 2*USB_SQ + 2*grow, S.USB_RING_R - USB_SQ + grow
    return rrect(PORT_X - bh/2, PORT_X + bh/2, py - bw/2, py + bw/2, r)
def usb_housing(py, grow=0.0):
    w, h, r, _ = S.USB_HOUSING
    return rrect(PORT_X - h/2 - grow, PORT_X + h/2 + grow, py - w/2 - grow, py + w/2 + grow, r + grow)
def usb_pocket(py):
    """housing pocket section: clears the housing and lets the free ring through (convex, so the lead-in is a hull)"""
    return hull(usb_housing(py, HOUSING_CLR), usb_bore(py, USB_SQ))
def cup():
    zt = Z_MOUTH + MOUTH_H
    band = MF.batch_hull([pz(cs_mouth, Z_MOUTH, zt - MOUTH_TAPER), pz(cs_out, zt - 0.01, zt)])
    m = (pz(cs_out, Z_MOUTH, Z_TOP1) + band) - pz(cs_in, Z_MOUTH - 1, Z_TOP0)
    m = m - pz(cs_in.offset(0.3, ROUND), Z_MOUTH - 1, Z_MOUTH + MOUTH_LEAD)                     # mouth lead-in
    for py in PORT_YS:
        m = m - MF.extrude(usb_bore(py), 4).translate((0, 0, Z_TOP0 - 1))
        m = m - pz(usb_pocket(py), Z_TOP0 - 1, Z_POCKET)
        m = m - MF.batch_hull([pz(usb_pocket(py), Z_POCKET - 0.01, Z_POCKET), pz(usb_bore(py), Z_POCKET + POCKET_LEAD - 0.01, Z_POCKET + POCKET_LEAD)])
    return m - cyly(SCREW_X, SCREW_Z, SCREW_HOLE_R, -(YI + MOUTH_T + 0.5), YI + MOUTH_T + 0.5)
def cap():
    plate = pz(cs_mouth, Z_MOUTH - CAP_T, Z_MOUTH)
    skirt = pz(CS.batch_boolean([cs_in.offset(-0.1, ROUND), cs_in.offset(-0.1 - SKIRT_T, ROUND)], M3.OpType.Subtract), Z_MOUTH - 0.01, Z_SKIRT1)
    bosses = [cyly(SCREW_X, SCREW_Z, 2.6, -(YI - 0.1), -(YI - 0.1 - BOSS_DEPTH)), cyly(SCREW_X, SCREW_Z, 2.6, YI - 0.1 - BOSS_DEPTH, YI - 0.1)]
    posts = [pz(circ(x, y, OT_R), Z_MOUTH - 0.01, FR_B0 - OT_GAP) for x, y in OT_POSTS]
    m = U(plate, skirt, *bosses, *posts)
    m = m - pz(CS.batch_boolean([cs_in.offset(0.5, ROUND), cs_in.offset(-0.1 - GROOVE_D, ROUND)], M3.OpType.Subtract), *GROOVE_Z)
    d = YI - 0.1 - BOSS_DEPTH + PILOT_SOLID                                                       # blind pilots
    return m - cyly(SCREW_X, SCREW_Z, PILOT_R, -(YI + 1), -d) - cyly(SCREW_X, SCREW_Z, PILOT_R, d, YI + 1)
def oring(): return pz(CS.batch_boolean([cs_in, cs_in.offset(-0.1 - GROOVE_D, ROUND)], M3.OpType.Subtract), GROOVE_Z[0] + 0.3, GROOVE_Z[1] - 0.3)
def screws():
    e = YI + MOUTH_T; t = YI - 0.1 - BOSS_DEPTH + PILOT_SOLID   # head on the mouth band, tip short of the pilot end
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
def key_ribs():
    """the crush ribs on the rail blocks' tongues: one on each side face (y), along x, ramped up over KEY_RIB[2] from the
    tip so the tongue starts into its slot before the ribs bite"""
    out, xe = [], PR + CR; h, w, lead = KEY_RIB
    x0 = xe - KEY_DEPTH + 0.1
    for s in (-1, 1):
        for end, (z0, z1) in (('bottom', (FR_B0, FR_B1)), ('top', (FR_T0, FR_T1))):
            for yf, d in ((s*KEY_Y[end][0], -s), (s*KEY_Y[end][1], s)):   # inner and outer face, rib grows away from the tongue
                yb = yf - d*0.05                                                  # root 0.05 inside the tongue
                pts = [(x0, yb), (x0 + lead, yf + d*h), (xe, yf + d*h), (xe, yb)]
                if sum(xa*yb - xb*ya for (xa, ya), (xb, yb) in zip(pts, pts[1:] + pts[:1])) < 0: pts = pts[::-1]   # CCW
                zm = (z0 + z1) / 2
                out.append(pz(CS([pts]), zm - w/2, zm + w/2))
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
    return U(*m, *key_slots(0.0), *key_ribs()) - U(*rail_usb_relief())
def rail_usb_relief():
    """the USB-C front housings hang 0.32 below B.Cu in the board notches, over the top rail blocks (real-board check
    2026-10-30): notch the blocks' board-side corner there, 0.2 clear plus the board's z float"""
    w, h, _, _ = S.USB_HOUSING; out = []
    for py in PORT_YS:
        out.append(pz(rect(PORT_X - h/2 - 0.2, S.sb_xb0 + 0.1, py - w/2 - 0.25, py + w/2 + 0.25), Z_HOUSING0 - 0.2 - BOARD_ZFLOAT, FR_T1 + 1))
    return out
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
    ch = CS.batch_boolean([rect(-PR - 1.5, PR + CR + 0.1, -CH_W/2, CH_W/2), rect(-PR - 1.5, -PR + 1.5, -2.0, 2.0)], M3.OpType.Add)
    # (solder pocket +-2.0, was +-1.5: it now runs into the C2 / C3 foam pockets instead of leaving a 0.2 mm wall, 2026-10-30)
    return pz(ch, FR_B1 - CH_D, FR_B1 + 0.1)
def foam_rings(r0=None, r1=None, grow=0.0):
    """foam preload rings (one per cell, under its bottom end), as 2-D sections; other radii / grown for the pockets"""
    out = []; r0 = FOAM_R[0] if r0 is None else r0; r1 = FOAM_R[1] if r1 is None else r1
    for x, y in CELLS:
        r = CS.batch_boolean([circ(x, y, r1), circ(x, y, r0)], M3.OpType.Subtract)
        if x > 0: r = CS.batch_boolean([r, rect(x - CR - 1, x - 1.0 + grow, y - CR - 1, y + CR + 1)], M3.OpType.Intersect)   # C1 / C4: away from the PACK pads
        out.append(r)
    return CS.batch_boolean(out, M3.OpType.Add)
def foam_pockets():
    """pockets for the foam rings: open into the weld windows (an inner lip there would be 0.1 mm, too thin for MJF) and
    stopping 1.0 inside the frame's outer edge (polish pass 2026-10-30: the old ring left a 0.2 mm skin there)"""
    return [pz(foam_rings(WIN_R - 0.3, FOAM_R[1] + 0.2, 0.2), FR_B1 - FOAM_POCKET, FR_B1 + 0.1)]
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
    base = cs_out if top else cs_mouth                    # the bottom bumper goes over the cup's thick mouth
    out = base.offset(BUMP_WALL if top else BUMP_WALL_BOT, ROUND); ring = CS.batch_boolean([out, base], M3.OpType.Subtract)
    if top:
        zb = Z_TOP1 - BUMP_BAND                           # relieved over the label, with a lead-in at the bottom edge
        band = pz(ring, zb, Z_TOP1) - pz(cs_out.offset(LABEL_RELIEF, ROUND), zb - 1, RELIEF_TOP) - lead_in(zb, +1)
        slab = pz(out, Z_TOP1, Z_TOP1 + BUMP_T_TOP) - pz(rrect(PORT_X - 4.5, PORT_X + 4.5, -14.0, 14.0, 2.0), Z_TOP1 - 0.1, Z_TOP1 + BUMP_T_TOP + 1)
        zt = Z_TOP1 + BUMP_T_TOP                          # port numbers, raised beside the port well
        slab = slab + U(*[pz(text_cs(d, DIGIT_H, PORT_X - 4.5 - 3.6, py), zt - 0.01, zt + DIGIT_RAISE) for py, d in PORT_DIGITS])
    else:
        z0, zc = Z_MOUTH - CAP_T, Z_MOUTH + MOUTH_H
        band = pz(ring, z0, zc); slab = pz(out, z0 - BUMP_T_BOT, z0)
        e = YI + MOUTH_T                                  # pockets over the screw heads
        band = band - cyly(SCREW_X, SCREW_Z, 2.3, -(e + 3), -(e - 0.1)) - cyly(SCREW_X, SCREW_Z, 2.3, e - 0.1, e + 3)
        lip_in = cs_out.offset(LABEL_RELIEF, ROUND)       # the lip over the label's lower edge, lead-in at its top
        floor = pz(CS.batch_boolean([out, lip_in], M3.OpType.Subtract), zc - 0.01, zc + LIP_FLOOR)
        lip = pz(CS.batch_boolean([lip_in.offset(LIP_WALL, ROUND), lip_in], M3.OpType.Subtract), zc + LIP_FLOOR - 0.01, LIP_TOP) - lead_in(LIP_TOP, -1)
        band = U(band, floor, lip)
        zb = z0 - BUMP_T_BOT                              # rating debossed in the base, reads from below
        bx0, by0, bx1, by1 = out.bounds()
        slab = slab - pz(text_cs(BASE_TEXT, BASE_TEXT_H, (bx0 + bx1) / 2, (by0 + by1) / 2, mirror=True), zb - 1, zb + BASE_TEXT_D)
    return band, slab
def lead_in(z, sense):
    """conical chamfer on a bumper's inner edge at height z, opening downwards (sense +1) or upwards (-1); cs_out is convex,
    so the hull of the two end sections is the exact chamfer"""
    d, a = LEAD_IN; h = d / math.tan(math.radians(a))
    wide, narrow = cs_out.offset(LABEL_RELIEF + d, ROUND), cs_out.offset(LABEL_RELIEF, ROUND)
    return M3.Manifold.batch_hull([pz(wide, z - sense * 0.01 - 0.005, z - sense * 0.01 + 0.005), pz(narrow, z + sense * h - 0.005, z + sense * h + 0.005)])
def label():
    """the wrap label as fitted: a 0.15 mm shell on the cup between LABEL_Z"""
    return pz(CS.batch_boolean([cs_out.offset(LABEL_T, ROUND), cs_out], M3.OpType.Subtract), *LABEL_Z)

LABEL_ART = os.path.join(HERE, '..', 'label', 'out', 'monolith_label_bl_print.svg')   # the adopted art (2 mm bleed)
def label_tex(parts_keys, offset=(0, 0, 0), dpmm=12):
    """zrender tex hook that paints the printed label art on the label's pixels: each pixel is unprojected to the cup,
    its perimeter position measured from the seam (middle of the back flat, as hardware/label/monolith_label.py lays it
    out) and the art sampled there, keeping the renderer's shading. Plain label colour if the art or cairosvg is missing."""
    try:
        import cairosvg, io
        bleed = 2.0
        png = cairosvg.svg2png(url=LABEL_ART, scale=dpmm / (96 / 25.4), background_color='white')
        art = np.asarray(Image.open(io.BytesIO(png)).convert('RGB'), float)
    except Exception as e:
        print('label art not drawn:', e); return None
    Pl = np.array(cs_out.offset(LABEL_T / 2, ROUND, circular_segments=720).to_polygons()[0], float)
    Ql = np.roll(Pl, -1, 0); seg = np.linalg.norm(Ql - Pl, axis=1); s0 = np.concatenate([[0], np.cumsum(seg)[:-1]]); per = seg.sum()
    back = [i for i in range(len(Pl)) if seg[i] > 2 and abs(Pl[i, 0] - Ql[i, 0]) < 1e-4 and Pl[i, 0] < 0][0]
    seam = s0[back] + seg[back] / 2
    idx = [i for i, k in enumerate(parts_keys) if k == 'label']
    def tex(base, pid, zb, ox, oy, px, R):
        m = np.isin(pid, idx)
        if not m.any(): return
        iy, ix = np.nonzero(m)
        Q = np.stack([(ix + 0.5 - ox) / px, (oy - iy - 0.5) / px, zb[iy, ix]], -1)
        p = Q @ R - np.asarray(offset, float)
        d = Ql - Pl; u = np.empty(len(p))
        for a in range(0, len(p), 4000):                  # nearest perimeter segment, in chunks
            q = p[a:a + 4000, None, :2]
            t = np.clip(((q - Pl[None]) * d[None]).sum(-1) / (seg**2)[None], 0, 1)
            j = np.argmin(np.linalg.norm(q - (Pl[None] + t[..., None] * d[None]), axis=-1), axis=1)
            u[a:a + 4000] = (s0[j] + t[np.arange(len(j)), j] * seg[j] - seam) % per
        v = LABEL_Z[1] - p[:, 2]
        cx = np.clip(((u + bleed) * dpmm).astype(int), 0, art.shape[1] - 1)
        cy = np.clip(((v + bleed) * dpmm).astype(int), 0, art.shape[0] - 1)
        shade = (base[iy, ix] / np.array(C['label'], float)).mean(1, keepdims=True)
        base[iy, ix] = art[cy, cx] * np.clip(shade, 0.35, 1.15)
    return tex

# ---------------- assembly and masses ----------------
C = dict(RR.C, cup=(214, 214, 208), cap=(170, 186, 200), carrier=(196, 190, 150), filler=(232, 150, 200), oring=(200, 60, 60),
         screw=(110, 110, 116), pad=(236, 156, 80), bump=(118, 72, 50), bslab=(236, 156, 80),
         rails=(170, 160, 110), insul=(200, 40, 40), foam=(120, 120, 130), sleeve=(118, 72, 50), label=(96, 160, 196),
         parts=(64, 64, 70), usb=(150, 150, 156))
def assembly():
    A = [('cup', tris(cup()), C['cup'])]
    cell = P.cell_solid()
    for x, y in CELLS: A.append(('cell', mv(cell, (x, y, S.sb_z_cell0)), C['cell']))
    A += [('carrier', tris(carrier()), C['carrier']), ('rails', tris(rails()), C['rails']), ('filler', tris(filler()), C['filler']),
          ('nickel', P.nickel_strips('strips'), C['nickel']), ('tails', P.nickel_strips('tails'), C['tail']),
          ('tails_wire', P.pack_wires(), C['wire']), ('tails_sense', P.sense_wires(), C['wire']),
          ('insul', tris(insul_rings()), C['insul']), ('foam', tris(foam()), C['foam']), ('sleeve', tris(sleeves()), C['sleeve']),
          *board_parts(),
          ('pad', tris(pad()), C['pad']), ('oring', tris(oring()), C['oring']), ('cap', tris(cap()), C['cap']),
          ('screw', tris(screws()), C['screw']),
          ('label', tris(label()), C['label'])]
    for top in (False, True):
        b, s = bumper(top); k = 'bumpt' if top else 'bumpb'
        A += [(k + '_band', tris(b), C['bump']), (k + '_slab', tris(s), C['bslab'])]
    return A
def board_parts():
    """the real routed board (KiCad STEP via board/board_from_step.py): the PCB, its parts and the BLE module (U301, on
    F.Cu), or the old slab + USB-C envelopes and B.Cu BLE envelope if the board mesh hasn't been made"""
    B = P.real_board()
    if B is None: return [('board', P.side_board_dummy(), C['board']), ('ble', P.ble_module(), C['ble'])]
    refs = [k for k in B if not k.startswith('_') and k not in ('PCB', 'U301') + P.BENCH_ONLY]
    usb = [k for k in refs if k in ('J401', 'J501')]
    return [('board', B['PCB'], C['board']), ('board', np.vstack([B[k] for k in refs if k not in usb]), C['parts']),
            ('board', np.vstack([B[k] for k in usb]), C['usb']), ('ble', B['U301'], C['ble'])]
def group(k): return k.split('_')[0]
PARTS = [(1, 'Cell carrier: frames, spines, front-back webs', 'MJF PA12', 'carrier'),
         (2, 'Board rails (4, clip-on) with the peg posts', 'MJF PA12', 'rails'),
         (3, 'Cells C1-C4, welded 4S', 'BAK N21700CX-65E', 'cell'),
         (4, 'Insulator rings on the + ends (4)', 'fish paper 0.2', 'insul'), (5, 'Preload rings under the cells (4)', 'silicone foam', 'foam'),
         (6, 'Nickel series strips (3)', 'nickel 0.2 x 10', 'nickel'), (7, 'PACK pads, CELL1/3 tongues; 18 / 28 AWG wires', 'nickel; PTFE wire', 'tails'),
         (8, 'Gap filler, board to the front cells (dispensed)', 'GEL 30, 3.1 g/cm3', 'filler'),
         (9, 'Board 1.6 mm with its parts (routed P0, from KiCad)', 'FR4, 6 layers', 'board'),
         (10, 'Retaining sleeves on the posts (4)', 'TPU 95A', 'sleeve'),
         (11, 'Cup: 5 closed sides, USB-C seal bores in the top wall', 'MJF PA12, 1.2 / 1.8', 'cup'),
         (12, 'Pad on the cap: preloads the core', 'TPU 95A, 10 % gyroid', 'pad'),
         (13, 'O-ring, 2.0 mm cord (radial)', 'silicone 60A', 'oring'), (14, 'Bottom cap: plate, skirt, posts', 'MJF PA12', 'cap'),
         (15, 'Screws M2 (2), thread-forming, below the seal', 'stainless', 'screw'),
         (16, 'Bottom bumper, mouth band + label lip', 'TPU 95A', 'bumpb'), (17, 'Top bumper, port well, port numbers', 'TPU 95A', 'bumpt'),
         (18, 'Wrap label, edges under the bumpers', 'vinyl + laminate', 'label')]
NUM = {k: n for n, _, _, k in PARTS}
RHO = dict(cup=1.01, cap=1.01, carrier=1.01, rails=1.01, screw=7.9, oring=1.15, filler=3.1, nickel=8.9, tails=8.9,
           insul=1.1, foam=0.3, sleeve=1.2, label=1.35)
def masses(A):
    m = {}
    for k, V, _ in A:
        g = group(k)
        r = RHO.get(g, 1.2*PAD_FILL if g == 'pad' else 1.2*SLAB_FILL if k.endswith('_slab') else (1.2 if k.endswith('_band') else None))
        if r is None: continue
        m[g] = m.get(g, 0) + vol(V) * r
    m['board'] = board_g(S.sb_board_area, S.SB_PCB_T) + board_parts_g(); m['cell'] = 4 * CELL_G
    return m
PARTS_RHO = 3.0                     # g/cm3 over each part's convex hull: a rough mix of ferrite / metal-powder inductors,
                                    # USB-C shells, ceramic caps and moulded ICs (the real board's parts, 2026-10-30)
def board_parts_g():
    """estimated mass of the parts on the real board (0 without the board mesh)"""
    B = P.real_board()
    if B is None: return 0.0
    refs = [k for k in B if not k.startswith('_') and k != 'PCB' and k not in P.BENCH_ONLY
            and not str(B['_model_' + k]).startswith(('Peg_', 'SolderWire'))]
    return sum(MF.hull_points(B[k].reshape(-1, 3)).volume() for k in refs) / 1000 * PARTS_RHO
def size(A):
    V = np.vstack([V for _, V, _ in A]).reshape(-1, 3); return V.max(0) - V.min(0)
def wall_deflection(t, p_kpa, a=37.5, b=80.0):
    """centre deflection (mm) of a flat a x b wall panel of thickness t under p_kpa, simply supported (Roark, b/a ~2:
    alpha 0.1106), E 1700 MPa for MJF PA12: the upper bound the review used"""
    return 0.1106 * p_kpa * 1e-3 * a**4 / (1700 * t**3)
def sealed_pressure(p_kpa):
    """no vent (removed 2026-10-28): the cup keeps the air it was closed with, so at altitude it pushes out by p_kpa
    (~25 kPa in an airliner, ~40 kPa at 4300 m, ~50 kPa there with the pack warm). Flat walls simply supported (Roark,
    b/a ~2: beta 0.61, linear, so the deflection is an upper bound), and the cap's push carried by the two M2 screws
    shearing the ligament under their holes in the cup wall (two planes). PA12 MJF: ~48 MPa tensile, creeps above ~15."""
    q = p_kpa * 1e-3
    a_side = X_IN - R_FRONT + PR                        # side flat: the back cell's tangent to the board-face corner
    a_face = 2 * (YI - R_FRONT)
    F = cs_in.area() * q
    return {'side flat 1.2 mm: stress (MPa)': 0.61 * q * a_side**2 / WALL**2,
            'side flat 1.2 mm: centre bulge, linear bound (mm)': wall_deflection(WALL, p_kpa, a_side),
            'board face 2.0 mm: stress (MPa)': 0.61 * q * a_face**2 / WALL_BF**2,
            'cap push (N)': F,
            'screw ligament shear (MPa)': F / 2 / (2 * (SCREW_Z - SCREW_HOLE_R - Z_MOUTH) * MOUTH_T)}
def checks():
    """assembly checks (positive = clearance), in the style of monolith_shell. The 2026-10-24 review fixes add: one-piece
    parts, screw edge distance and blind pilots, the axial stack (skirt gap, overtravel posts, pad preload), the USB-C
    ring in the top wall, the posts under the board-face wall, and the CELL2 wire channel."""
    bw, bh = S.USB_RING_W - 2*USB_SQ, S.USB_RING_H - 2*USB_SQ
    pk_y = [abs(S.sb_pack_holes()[n][0]) for n in ('PACK-', 'PACK+')]
    return {
        'carrier is one body': 1 - len(carrier().decompose()) + 0.0,
        'board rails: four bodies (clip-on blocks)': 4 - len(rails().decompose()) + 0.0,
        'rail tongue crush ribs bite the slot walls (0.1-0.2 per side)': min(KEY_RIB[0] - KEY_CLR - 0.1, 0.2 - (KEY_RIB[0] - KEY_CLR)) + 1e-9,
        'crush ribs fit the thin top frame (z, >= 0.2 each side)': (FR_T1 - FR_T0 - KEY_RIB[1]) / 2 - 0.2 + 1e-9,
        'cap is one body': 1 - len(cap().decompose()) + 0.0,
        'board fits the bore (y, per side)': YI - S.sb_board_w/2 - 0.3,
        'tallest part under the board-face wall (x)': X_IN - (S.sb_xb1 + S.SB_OUT_H) - 0.3,
        'USB-C body under the board-face wall (x)': X_IN - (S.sb_port_x + S.USB_UP) - 0.3,
        'board-face wall at 25 kPa (simply supported bound) stays off the parts (x)': (X_IN - (S.sb_xb1 + S.SB_OUT_H)) - wall_deflection(WALL_BF, 25) - 0.05,
        'peg posts under the board-face wall (x, gap 0.1-0.5)': min(X_IN - POST_GAP - (S.sb_xb1 + 0.1), POST_GAP - 0.1, 0.5 - POST_GAP),
        'retaining sleeves under the board-face wall (x)': X_IN - (S.sb_xb1 + SLEEVE[2]) - 0.5,
        'peg-slot float lets the seal bores centre the ports (y, float >= the pocket over the bore)': (S.CUP_PEG_SLOT[0] - S.CUP_PEG_D)/2
                                                       - USB_LEAD + 1e-9,
        'seal band after the pocket lead-in, board at full rise (z, >= 0.6)': (Z_TOP1 - S.USB_RING_D[0] + BOARD_ZFLOAT)
                                                       - (Z_POCKET + POCKET_LEAD) - 0.6,
        'housing pocket clears the housing at full rise (z, >= 0)': Z_POCKET - (Z_RING0 + BOARD_ZFLOAT),
        'housing pocket clears the housing at full y float (y, >= 0)': HOUSING_CLR - 0.0 + 1e-9,
        'retaining sleeves cover the peg slots at full float (y, >= 0.3)': SLEEVE[0] - (S.CUP_PEG_SLOT[0] - S.CUP_PEG_D)/2 - S.CUP_PEG_SLOT[0]/2 - 0.3 + 1e-9,
        'board top edge is a backstop under the top wall (z, 0.05-0.2)': min(Z_TOP0 - S.sb_zb1 - 0.05, 0.2 - (Z_TOP0 - S.sb_zb1)),
        'USB-C seal squeeze per side (0.12-0.18)': min(USB_SQ - 0.12, 0.18 - USB_SQ),
        'seal bores fit the top wall beside the board (y)': (S.SB_STOP_Y0 - (S.SB_PORT_Y + bw/2 + USB_LEAD)),
        'housing pockets: wall left between the two ports (y, >= 1.5)': 2 * S.SB_PORT_Y - (S.USB_RING_W + 2 * HOUSING_CLR) - 1.5,
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
        'thick mouth band covers the O-ring band before its taper (z)': (Z_MOUTH + MOUTH_H - MOUTH_TAPER) - GROOVE_Z[1],
        'label: placement slack down to the mouth band top (z, >= 0.5)': LABEL_Z[0] - (Z_MOUTH + MOUTH_H) - 0.5,
        'label: placement slack up, inside the top band relief (z, >= 1.0)': RELIEF_TOP - LABEL_Z[1] - 1.0,
        'label: both edges covered >= 1.5 past the lead-ins (z)': min(LABEL_Z[1] - (Z_TOP1 - BUMP_BAND),
                                                       LIP_TOP - LABEL_Z[0]) - LEAD_IN[0] / math.tan(math.radians(LEAD_IN[1])) - 1.5,
        'label: bumpers clear the two-layer seam (radial, >= 0.1)': LABEL_RELIEF - 2 * LABEL_T - 0.1 + 1e-9,
        'label: top band wall left at the lead-in (radial, >= 0.8)': BUMP_WALL - LABEL_RELIEF - LEAD_IN[0] - 0.8 + 1e-9,
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
        'foam pockets: frame left outside them (r, >= 0.8)': CR - (FOAM_R[1] + 0.2) - 0.8,
        'insulator rings inside the can (r)': CR - INSUL[0] - 0.2,
        'board rails clear of the PACK pads (z, rail above the pads)': S.SB_BAR_Z0 - (S.sb_z_tail_b + 0.5),
        'webs: room between front and back cells (gap - 2 x clearance)': (2*PR - 2*CR) - 2*WEB_CLR,
        'bore corner radius >= 2 x O-ring cord': R_FRONT - 2*ORING_CS,
        **board_checks(),
    }
# ---------------- the real board against the enclosure ----------------
CLEAR = dict(cup=0.3, rails=0.2, sleeves=0.15, carrier=0.3, cells=0.3, cap=0.5, pad=0.5)   # minimum gap, part hull to each
SKIP = dict(cells=('J108', 'J112', 'J109', 'J110', 'J111', 'J115', 'J116', 'J117', 'J118', 'J119', 'J120'))   # wire stubs:
# the KiCad stand-ins are straight 28 / 18 AWG stubs off B.Cu; the real wires bend away along the rails (P.sense_wires)
def slice_pts(T, z):
    """points where the triangle soup T (n, 3, 3) crosses the plane z"""
    a = T[..., 2] - z; out = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        m = (a[:, i] * a[:, j]) < 0
        t = a[m, i] / (a[m, i] - a[m, j]); out.append(T[m, i] + t[:, None] * (T[m, j] - T[m, i]))
    return np.concatenate(out)
def penetration(T, m, zs):
    """deepest point of the mesh T inside the solid m (mm, 0 if none), over the planes zs"""
    import shapely
    deep = 0.0
    for z in zs:
        p = slice_pts(T, z)
        if not len(p): continue
        g = None
        for c in m.slice(z).to_polygons():
            if len(c) < 3: continue
            q = shapely.Polygon(c); g = q if g is None else g.symmetric_difference(q)
        if g is None: continue
        inside = shapely.contains_xy(g, p[:, 0], p[:, 1])
        if inside.any(): deep = max(deep, shapely.distance(g.boundary, shapely.points(p[inside, :2])).max())
    return float(deep)
def board_checks():
    """every part of the real board against the cup, rails, sleeves, carrier, cells and cap (convex hull of each part, so
    the gaps are lower bounds), the tallest part under the board-face wall, and the USB-C connectors in the seal bores
    (sliced: the ring's squeeze, and nothing hard in the wall or the rails)"""
    B = P.real_board()
    if B is None: return {'real board mesh present (board/board_from_step.py)': -1.0}
    cells = U(*[pz(circ(x, y, CR), S.sb_z_cell0, S.sb_z_cell1) for x, y in CELLS])
    mech = dict(cup=cup(), rails=rails(), sleeves=sleeves(), carrier=carrier(), cells=cells, cap=cap(), pad=pad())
    refs = [k for k in B if not k.startswith('_') and k != 'PCB' and k not in P.BENCH_ONLY and not str(B['_model_' + k]).startswith('Peg_')]
    hulls = {k: MF.hull_points(B[k].reshape(-1, 3)) for k in refs}
    out = {}
    for n, m in mech.items():
        g = {k: h.min_gap(m, 2.0) for k, h in hulls.items() if k not in ('J401', 'J501') + SKIP.get(n, ())}
        k = min(g, key=g.get)
        out[f'real board: every part clears the {n} (>= {CLEAR[n]}; worst {k})'] = g[k] - CLEAR[n]
    top = {k: B[k][..., 0].max() for k in refs if k not in ('J401', 'J501')}; k = max(top, key=top.get)
    out[f'real board: tallest part under the board-face wall at 25 kPa (x, >= 0.05; {k} {top[k] - S.sb_xb1:.2f} tall)'] = \
        X_IN - top[k] - wall_deflection(WALL_BF, 25) - 0.05
    cupm, railm = mech['cup'], mech['rails']
    zr = np.arange(Z_TOP1 - S.USB_RING_D[1] + 0.05, Z_TOP1 - S.USB_RING_D[0] - 0.04, 0.1)    # ring band
    zh = np.arange(Z_HOUSING0 + 0.02, Z_TOP1 - S.USB_RING_D[1] - 0.01, 0.05)                    # housing, under the ring
    zl = np.arange(Z_TOP1 - S.USB_RING_D[0] + 0.02, Z_TOP1 - 0.01, 0.1)                         # shell lip, in front of it
    for k in ('J401', 'J501'):
        sq = penetration(B[k], cupm, zr)
        out[f'real board: {k} ring squeeze in the seal bore (0.08-0.25 per side)'] = min(sq - 0.08, 0.25 - sq)
        for up in (0.0, BOARD_ZFLOAT):                                                           # nominal, and at full rise
            T = B[k] + np.array([0, 0, up])
            out[f'real board: {k} housing and lip clear the top wall (board +{up:.1f} z)'] = -penetration(T, cupm, np.r_[zh, zl] + up)
        out[f'real board: {k} housing clears the top rail block'] = -penetration(B[k], railm, zh)
    return out

# ---------------- sheets ----------------
SS, INK, MUTED, RULE, ACCENT = RR.SS, RR.INK, RR.MUTED, RR.RULE, RR.ACCENT
LEG = [('PA12 cup', C['cup']), ('PA12 cap', C['cap']), ('PA12 carrier', C['carrier']), ('cells', C['cell']), ('board', C['board']),
       ('BLE module', C['ble']), ('gap filler', C['filler']), ('O-ring', C['oring']), ('screw', C['screw']),
       ('TPU pad / bumper slab', C['pad']), ('TPU bumper band', C['bump']), ('nickel strip', C['nickel']), ('nickel tail / pad', C['tail']), ('PACK wire', C['wire']), ('vinyl label', C['label'])]
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
    keys = [k for k, _, _ in A]
    sh.render([(V, c) for _, V, c in A], R, o1, pxs, tex=label_tex(keys)); pj = RR.proj(R, o1, pxs)
    sh.callouts([(pj((PORT_X, 9, Z_TOP1 + BUMP_T_TOP)), 'Port well through the top bumper'),
                 (pj((X_OUT, -8, 50)), 'Board face: 2.0 mm PA12 under the\nwrap label (seam on the back)'),
                 (pj((X_OUT + 2, -YI, Z_MOUTH - CAP_T - BUMP_T_BOT + 1)), f'{BUMP_T_BOT:.0f} mm bottom bumper over the cap and the thick mouth\n(the pad inside adds the rest of the stroke)')],
                475, 'r', 150)
    sh.panel_title(780, 128, 'Exploded, in assembly order', 1180)
    EX = dict(cell=(0, 0, -75), carrier=(0, 0, -75), nickel=(0, 0, -75), tails=(0, 0, -75), board=(16, 0, -75), ble=(16, 0, -75),
              filler=(8, 0, -75), cup=(0, 0, 25), pad=(0, 0, -118), oring=(0, 0, -136), cap=(0, 0, -152), screw=(0, 0, -152),
              rails=(9, 0, -75), insul=(0, 0, -75), foam=(0, 0, -75), sleeve=(22, 0, -75), label=(0, 0, 25))
    ex, gid = [], []
    for k, V, c in A:
        g_ = group(k); dd = EX.get(g_, (0, 0, -182) if g_ == 'bumpb' else (0, 0, 50))
        ex.append((mv(V, dd), c)); gid.append(g_)
    R2 = camera((0.5, -1.25, 0.32)); o2 = (1180, 690); px2 = 3.0
    pid = sh.render(ex, R2, o2, px2, tex=label_tex(keys, EX['label']))
    balloons(sh, pid, gid, dict(cup=160, carrier=150, cell=200, nickel=330, tails=10, filler=20, board=0, pad=200, oring=0,
                                cap=200, screw=340, bumpb=200, bumpt=170, rails=30, insul=120, foam=230, sleeve=20))
    x0 = 2010; sh.panel_title(x0, 128, 'Parts', 650)
    rows = [[str(n), name, mat, f'{m.get(k, 0):.1f}' if m.get(k, 0) >= 0.05 else '<0.1'] for n, name, mat, k in PARTS]
    rows.append(['', 'Pack total', '', f'{total:.1f}'])
    y = sh.table(x0, 176, ['#', 'Part', 'Material', '>g'], rows, [36, 344, 200, 70], 13, bold_last=True, rh=26)
    for i, s in enumerate(('Board mass is estimated: FR4 + 6-layer copper, parts at 3 g/cm3 over their 3D models.',
                           f'TPU pad {PAD_FILL:.0%} and bumper slabs {SLAB_FILL:.0%} gyroid; bumper bands solid. Cells 75 g each (datasheet max).',
                           'Label drawn on the cup; board thermal vias not drawn. Pad drawn as installed (printed 1.2 mm taller).')):
        sh.text(x0, y + 14 + 24*i, s, 13, fill=MUTED)
    sh.line([(40, 1330), (2660, 1330)], RULE, 1.5); sh.legend(LEG, 40, 1350, 14)
    save(sh, 'monolith_cup_exploded.png')

def sheet_sections(A):
    core = [(k, V, c) for k, V, c in A if not k.startswith('bump')]
    sh = RR.Sheet(2700, 1300)
    sh.header('Monolith cup: sections', 'Cut from the same meshes as the STLs. The board and its parts are the routed P0 board from KiCad '
              '(board/board_from_step.py). The O-ring is drawn as squeezed.')
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
                 (td(YI + MOUTH_T + 0.6, SCREW_Z), 'M2 through the cup wall into a blind\nskirt boss, below the O-ring'),
                 (td(YI + MOUTH_T/2, Z_MOUTH + 5.0), f'Mouth {MOUTH_T} mm thick: the flats\nstay on the O-ring'),
                 (td(10, Z_MOUTH - CAP_T/2), 'Cap plate'),
                 (td(0, Z_MOUTH + 4.0), 'TPU pad'),
                 (td(-10, FR_B0 + 0.8), 'Carrier frame, cells above')], DX + dw + 40, 'r', DY, size=14)
    # D-D: the USB-C in the top wall, through the port centre and near the housing corner (real-board check 2026-10-30)
    pxu, (x0, x1, z0, z1) = 40.0, (21.8, 31.4, 76.9, 80.9); uw, uh = int((x1 - x0)*pxu), int((z1 - z0)*pxu)
    sh.panel_title(40, 960, 'D-D   USB-C in the top wall: port centre, and 0.3 mm in from the housing corner', 1380)
    for i, (dy, lab) in enumerate(((0.02, 'centre'), (S.USB_HOUSING[0]/2 - S.USB_HOUSING[2] - 0.3, 'corner'))):
        u = RR.Sheet(uw, uh); ou = (-x0*pxu, z1*pxu)
        u.section(core, 1, PORT_YS[1] + dy, 0, 2, ou, pxu)
        UX, UY = 60 + i*(uw + 330), 1000
        sh.img.paste(u.img, (UX*SS, UY*SS)); sh.rect(UX, UY, UX + uw, UY + uh, outline=RULE, width=1)
        tu = lambda x, z: (UX + ou[0] + pxu*x, UY + ou[1] - pxu*z)
        sh.text(UX + uw/2, UY + uh + 14, lab, 14, fill=MUTED, anchor='mm')
        sh.callouts([(tu(PORT_X + S.USB_RING_H/2 - 0.1, Z_TOP1 - 1.0), 'Seal ring in the bore'),
                     (tu(PORT_X + S.USB_HOUSING[1]/2 + HOUSING_CLR/2, Z_RING0 - 0.15), 'Housing pocket: clears\nthe hard front housing'),
                     (tu(S.sb_xb0 - 0.2, Z_HOUSING0 - 0.15), 'Rail block notched under\nthe housing (0.32 below B.Cu)')]
                    if i == 0 else [(tu(PORT_X + S.USB_HOUSING[1]/2 + HOUSING_CLR/2, Z_RING0 - 0.15), 'Housing corner in\nthe pocket, 0.15 clear')],
                    UX + uw + 30, 'r', UY, size=13)
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
              ('Seal + fasteners', ('unmodelled',), ('oring', 'screw')), ('Thermal interface', ('gappad',), ('filler',)),
              ('Insulation sheet + hold-downs', ('insul', 'rings', 'hold'), ())]
    rows = [[n, f'{cat(mt, a):.1f}', f'{cat(m, b):.1f}', f'{cat(m, b) - cat(mt, a):+.1f}'] for n, a, b in rows_w]
    rows.append(['Pack total', f'{tt:.1f}', f'{tc:.1f}', f'{tc - tt:+.1f}'])
    sh.panel_title(40, 760, 'Weight by function (g)', 1240)
    sh.table(40, 810, ['', '>Tray', '>Cup', '>Cup - tray'], rows, [440, 200, 200, 220], 15, bold_last=True, rh=36)
    rows2 = [['Outside (mm)', f'{wt:.1f} x {dt:.1f} x {Lt:.1f}', f'{su[0]:.1f} x {su[1]:.1f} x {su[2]:.1f}'],
             ['Seal joints', 'bead round the cover, 2 port rings, vent', '1 radial O-ring, 2 port rings, no vent'],
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
    for p_kpa in (25, 50):
        print(f'  sealed, +{p_kpa} kPa inside: ' + ', '.join(f'{k} {v:.1f}' for k, v in sealed_pressure(p_kpa).items()))
    print('total', round(sum(m.values()), 1), 'g   size (x, y, z)', np.round(size(A), 1))
    if which in ('all', 'stl'):
        for k in ('cup', 'cap', 'carrier', 'rails', 'sleeve', 'foam', 'pad', 'oring', 'filler', 'bumpb_band', 'bumpb_slab', 'bumpt_band', 'bumpt_slab'):
            write_stl(os.path.join(HERE, f'monolith_cup_{k}.stl'), np.vstack([V for kk, V, _ in A if kk == k]))
        print('wrote monolith_cup_*.stl')
    if which in ('all', 'exploded'): sheet_exploded(A, m)
    if which in ('all', 'sections'): sheet_sections(A)
    if which in ('all', 'compare'): sheet_compare(A, m)
