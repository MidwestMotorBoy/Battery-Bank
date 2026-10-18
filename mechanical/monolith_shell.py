"""Monolith 4S1P 21700 shell - parametric generator (numpy only).
Run: python3 monolith_shell.py   -> monolith_shell.stl, monolith_bottom_pcb.dxf
All dimensions in mm. Z = 0 is the bottom rim of the tube."""
import numpy as np, struct

# ---------------- parameters ----------------
CELL_D      = 21.5    # EVE INR21700-58E listed diameter (measure yours)
CELL_L      = 70.8    # listed length
CELL_CLEAR  = 0.30    # diametral clearance per cell pocket
WALL        = 1.20
PCB_RECESS  = 2.0     # bottom PCB sits this far inside the rim
PCB_T       = 1.6
PCB_CLEAR   = 0.15    # gap between PCB edge and tube wall
TAB_T       = 0.4     # nickel + insulator allowance, each end
FOAM_T      = 1.0     # foam pad on top of the cells
SKIRT_DEPTH = 6.0     # how far the top cap skirt slides in
RIB_W       = 2.0     # mid-wall rib width (0 disables ribs)
RIB_DEPTH   = 2.5
VENT_D      = 8.0     # placeholder vent hole in the PCB outline
N_ANGLES    = 720
# ---------------- derived ----------------
pocket_r = (CELL_D + CELL_CLEAR) / 2          # also the inner corner radius
a_in  = 2 * pocket_r                          # inner half-width
a_out = a_in + WALL
c_in, c_out = pocket_r, pocket_r + WALL
z_rib0 = PCB_RECESS + PCB_T                   # PCB seats against rib ends here
z_rib1 = z_rib0 + TAB_T + CELL_L + TAB_T      # top of the cell stack
H      = z_rib1 + FOAM_T + SKIRT_DEPTH

def rsq(th, a, c):
    """radius of a rounded square (half-width a, corner radius c) along angle th"""
    t = np.abs(np.arctan2(np.sin(th), np.cos(th)))
    t = np.where(t > np.pi/2, np.pi - t, t)
    dx, dy = np.cos(t), np.sin(t)
    q = a - c
    with np.errstate(divide='ignore', invalid='ignore'):
        rx = np.where(dx > 1e-12, a/np.maximum(dx,1e-12), np.inf)
        ry = np.where(dy > 1e-12, a/np.maximum(dy,1e-12), np.inf)
    dq = (dx+dy)*q
    rc = dq + np.sqrt(np.maximum(dq*dq - 2*q*q + c*c, 0))
    return np.where(rx*dy <= q, rx, np.where(ry*dx <= q, ry, rc))

# angle columns: uniform + flat/arc transitions + rib edges (duplicated)
th = list(np.linspace(0, 2*np.pi, N_ANGLES, endpoint=False))
for a in (a_in, a_out):
    b = np.arctan2(a - (a - (c_in if a == a_in else c_out)), a)
    b = np.arctan2(a_in - c_in, a)
    for k in range(4):
        th += [k*np.pi/2 + b, k*np.pi/2 - b, k*np.pi/2 + np.pi/2 - b]
ribs = RIB_W > 0 and RIB_DEPTH > 0
tip = a_in - RIB_DEPTH
ts = np.arctan2(RIB_W/2, tip) if ribs else 0.0
th = np.unique(np.round(np.mod(th, 2*np.pi), 12))
cols = [(t, 0) for t in th]
if ribs:
    for k in range(4):
        for s in (-1, 1):
            t = np.mod(k*np.pi/2 + s*ts, 2*np.pi)
            cols += [(t, -s), (t, s)]      # -s side = on the rib, +s side = on the wall
cols.sort(key=lambda c: (c[0], c[1] if True else 0))
# order duplicates so that going CCW we meet the correct side first
def keyf(c):
    t, flag = c
    k = np.round(t/(np.pi/2)); off = t - k*np.pi/2
    return (t, flag*np.sign(off) if flag else 0)
cols.sort(key=lambda c: (round(c[0], 12), -keyf(c)[1]))
T = np.array([c[0] for c in cols]); F = np.array([c[1] for c in cols])
n = len(T)

r_out  = rsq(T, a_out, c_out)
r_wall = rsq(T, a_in, c_in)
r_rib  = r_wall.copy()
if ribs:
    off = T - np.round(T/(np.pi/2))*np.pi/2
    on = (np.abs(off) < ts - 1e-9) | ((np.abs(np.abs(off) - ts) < 1e-9) & (F*np.sign(off) < 0))
    r_rib[on] = tip/np.cos(off[on])

def ring(r, z): return np.c_[r*np.cos(T), r*np.sin(T), np.full(n, z)]
tris = []
def strip(A, B):           # quads A[i],A[i+1],B[i+1],B[i]
    for i in range(n):
        j = (i+1) % n
        tris.append((A[i], A[j], B[j])); tris.append((A[i], B[j], B[i]))
O0, O1 = ring(r_out, 0), ring(r_out, H)
W0, W1, W2, W3 = [ring(r_wall, z) for z in (0, z_rib0, z_rib1, H)]
R1, R2 = ring(r_rib, z_rib0), ring(r_rib, z_rib1)
strip(O0, O1)              # outer wall
strip(W0, O0)              # bottom rim
strip(O1, W3)              # top rim
strip(W1, W0)              # PCB pocket wall
strip(R2, R1)              # cell zone wall with ribs
strip(W3, W2)              # cap socket wall
strip(R1, W1)              # rib ends, bottom (PCB stop)
strip(W2, R2)              # rib ends, top
V = np.round(np.array(tris), 6)
nrm = np.cross(V[:,1]-V[:,0], V[:,2]-V[:,0])
keep = np.linalg.norm(nrm, axis=1) > 1e-9
V, nrm = V[keep], nrm[keep]

def write_stl(path):
    with open(path, 'wb') as f:
        f.write(b'Monolith shell'.ljust(80, b' ')); f.write(struct.pack('<I', len(V)))
        for t, nn in zip(V, nrm):
            nn = nn/np.linalg.norm(nn)
            f.write(struct.pack('<12fH', *nn, *t.ravel(), 0))

def write_dxf(path):
    a, c, q = a_in - PCB_CLEAR, c_in - PCB_CLEAR, a_in - c_in
    e = []
    def line(x1,y1,x2,y2,l='OUTLINE'): e.append(f"0\nLINE\n8\n{l}\n10\n{x1:.4f}\n20\n{y1:.4f}\n11\n{x2:.4f}\n21\n{y2:.4f}\n")
    def arc(x,y,r,a0,a1,l='OUTLINE'): e.append(f"0\nARC\n8\n{l}\n10\n{x:.4f}\n20\n{y:.4f}\n40\n{r:.4f}\n50\n{a0}\n51\n{a1}\n")
    def circ(x,y,r,l): e.append(f"0\nCIRCLE\n8\n{l}\n10\n{x:.4f}\n20\n{y:.4f}\n40\n{r:.4f}\n")
    line(-q, a, q, a); line(-q, -a, q, -a); line(a, -q, a, q); line(-a, -q, -a, q)
    arc(q, q, c, 0, 90); arc(-q, q, c, 90, 180); arc(-q, -q, c, 180, 270); arc(q, -q, c, 270, 360)
    circ(0, 0, VENT_D/2, 'VENT')
    for sx in (-1, 1):
        for sy in (-1, 1): circ(sx*pocket_r, sy*pocket_r, CELL_D/2, 'CELLS_REF')
    if ribs:
        for k in range(4):
            cs, sn = np.cos(k*np.pi/2), np.sin(k*np.pi/2)
            p = [(tip, -RIB_W/2), (a_in, -RIB_W/2), (a_in, RIB_W/2), (tip, RIB_W/2)]
            p = [(x*cs - y*sn, x*sn + y*cs) for x, y in p]
            for i in range(4): line(*p[i], *p[(i+1) % 4], l='RIB_STOPS_REF')
    open(path, 'w').write("0\nSECTION\n2\nENTITIES\n" + "".join(e) + "0\nENDSEC\n0\nEOF\n")

# ---------------- side-board layout (board along the +x face of the cells) ----------------
# A one-piece printed tray, closed on five sides; the +x face is the only opening.
# Assembly: foam pad on the floor -> cell module in through the side -> board in through the side,
#   then slid +z by SB_SLIDE so both USB-C mating faces pass into their holes in the top wall
#   (the connector's own mating direction, so the seal rings seat whole) -> shim under the board ->
#   solder the nickel tabs -> gap pad -> aluminium cover: top edge under the top-wall lip, then
#   two M2 screws into heat-set inserts in the bottom corner pillars (hidden under the bumper).
# The cover is recessed SB_LIP into a frame in the walls and doubles as the heat spreader.
# No airflow vents; one adhesive ePTFE pressure vent over a hole in the cover (altitude).
SB_INSUL     = 0.3    # 0.2 mm fish paper on the cells' board-side face, plus 0.1
SB_BCU_H     = 2.3    # extra room behind the board for B.Cu parts (the BLE module is 2.3 mm max), 2026-10-18
SB_PCB_T     = 1.6    # production board thickness (1.6 mm for cost, 2026-10-18; was 0.8)
SB_OUT_H     = 3.2    # tallest outer part (APS0730 inductor 3.1; the USB-C body is 1.97 above a 1.6 mm board)
SB_GAP       = 0.5    # compressed gap pad between those parts and the cover
SB_COVER_T   = 1.0    # aluminium cover
SB_LIP       = 0.8    # frame lip outside the cover (cover sits this far below the rim)
SB_REB       = 0.5    # rebate into the +-y walls that the cover edges rest in (wall left 0.7)
SB_SLOT      = 1.0    # cover top edge tucks this far under the top-wall lip
SB_END_T     = 1.6    # bottom and top walls
SB_PAD_T     = 4.8    # floor zone under the cells: printed TPU spacer + 1 mm EVA, and the two screw pillars beside it
SB_TOP_PAD   = 1.0    # 1 mm EVA between the cell tops and the top wall
SB_SLIDE     = 2.5    # board slide that engages the ports (needs > SB_END_T - (USB_FACE_OUT - SB_END_T))
SB_PCB_CLEAR = 0.2    # board edge to wall, and board to the end zones
SB_PORT_Y    = 6.5    # ports at y = +-6.5 (13 mm apart, as on the production board)
SB_INSERT_D, SB_INSERT_L = 3.2, 4.0   # M2 heat-set insert pilot (e.g. M2 x 3 x 3.2): diameter, depth
SB_PILLAR_W  = 5.0    # pillar width in y, from the wall inward
SB_VENT_D, SB_VENT_Z = 3.0, 12.0      # ePTFE vent hole in the cover (above the bottom bumper band)
# ShouHan TYPE-C 16PCB<t> IP68 (DevBoard/tools/make_3d_usbc.py), the variant for the board thickness:
# mid-mount, body bottom flush with the board bottom, centreline 1.627 above the board bottom
# (0.027 above the top of a 1.6 mm board), mating face 1.949 past the board edge
USB_FACE_OUT, USB_ZC, USB_DEPTH = 1.949, 1.632 - SB_PCB_T - 0.005, 7.45
USB_SHELL_W, USB_SHELL_H, USB_UP, USB_DN = 9.64, 3.87, 1.939, 1.632
USB_SEAL_W, USB_SEAL_H = 10.25, 4.45  # seal ring, sits in the top-wall hole
# drop protection, cooling and venting (2026-10-18, reports/Battery pack potting and drop protection.md).
# Hobby build, sheet stock limited to 1 mm EVA foam, 0.2 mm mica and 0.2 mm fish paper; everything else is printed.
# nothing is potted. The tray, cells and board form one stiff core; TPU end caps outside it are the crush zone.
SB_SIDE_PAD  = 0.2    # fish paper liner round the -x and +-y faces of the cells (wrap abrasion); thin, so the cans stay close to the walls
SB_EVA_T     = 1.0    # EVA foam sheet: the cell-end pads (top, and over the TPU floor spacer) and, doubled, the USB-C hold-downs
SB_SEP_T     = 0.2    # mica sheets in the cross-shaped gap between the cells (propagation barrier)
SB_VENT_CUT_D = 14.0  # end-pad cut-out over each positive cap: button and vent holes stay open, the pad bears on the crimp rim
SB_RUPT_D, SB_RUPT_T = 0.0, 0.0      # rupture windows (bottom wall thinned under the bottom + caps): off, 2026-10-18 -
                                     # consumer power banks don't have them; set e.g. 10.0, 0.6 to bring them back
SB_STOP_Y0   = 14.0   # board top stops on the top-wall inside face, |y| from here to the wall (clear of the port holes)
SB_HOLD_T    = 2.0    # 2 x 1 mm EVA hold-down between each USB-C body and the cover (compresses to the gap)
SB_CAP_T     = 8.0    # TPU lattice crush zone beyond each end wall
SB_CAP_SOFT  = 4.0    # outer part of it printed softer (graded: soft at the face, firmer behind)
SB_CAP_BAND  = 9.0    # how far each cap's band wraps over the sides (bottom band stays clear of the cover vent)
SB_CAP_PROUD = 2.0    # band wall: stands this proud of the shell faces, so flat side drops land on the bands
SB_CAP_CORNER = 9.0   # dense corner noses: this far in from each corner of the cap, in x and y
SB_CAP_SQUEEZE = 0.1  # band stretch fit over the tray
SB_WELL_W, SB_WELL_H = 28.0, 9.0     # one port well through the top cap for both plugs (USB-C overmold rec. max 12.35 x 6.5)
# BLE module (CC2340R5MODA, 7 x 10 x 2.3 mm max) on B.Cu at the right (+y, C4 / PACK+) board edge, antenna end at the
# edge: the board's ground plane sits between it and the aluminium cover, and it radiates out through the printed
# side wall. >= 10 mm of ground along the edge above it (TI SWRS349A fig. 9-2). The cover is whole (no notch).
SB_ANT_SIDE  = 1                     # +1 = right edge seen from the cover (+y), -1 = left
SB_ANT_BELOW = 19.1                  # module centre below the board's top edge (10 mm of ground above, 10 mm from the USB-C bodies)
SB_ANT_MOD   = (7.0, 10.0)           # module: along the edge, into the board
SB_ANT_H     = 2.3                   # module height on B.Cu
# EVA lanes (3 x 1 mm EVA, compressed) between the insulated cells and B.Cu along the two cell tangent lines: they hold
# the cells off the board now that there is a gap for B.Cu parts. The +y lane stops either side of the BLE module.
SB_LANE_W, SB_LANE_LAYERS = 6.0, 3
SB_LANE_GAP = 2.0                    # lane end to the module (z)
# cells seen from the port end: (sx, sy) of the centre -> (name, end that carries the positive cap).
# C1 and C4 face the board (PACK- on the C1 side, -y); series chain C1 -> C2 -> C3 -> C4 (Production/README.md).
SB_CELLS = {(1, -1): ('C1', 'top'), (-1, -1): ('C2', 'bottom'), (-1, 1): ('C3', 'top'), (1, 1): ('C4', 'bottom')}
# Pack connections. The tabs are soldered from the open side after the board is in, so everything lands on F.Cu.
# - PACK- (C1 bottom) and PACK+ (C4 bottom): nickel strips that wrap under the board's bottom edge onto F.Cu pads.
#   The shim under the board is one centre block between them; the floor spacer and EVA get reliefs beside the board.
# - CELL1 (C1+/C2- strip, top), CELL3 (C3+/C4- strip, top), CELL2 (C2+/C3- strip, bottom): sense taps only, so thin
#   wires through plated holes. They run in the deep groove behind the board between C1 and C4 (5 mm free at |y| = 2),
#   in slots in the top EVA, and for CELL2 in a channel in the floor spacer.
SB_TAB_W, SB_TAB_T = 7.0, 0.15       # nickel strip (all strips)
SB_TAB_PAD_H = 5.0                   # PACK+/- F.Cu pads: from the bottom edge up
SB_SHIM_HALF = 6.0                   # centre shim block |y| (the PACK strips pass either side)
SB_WIRE_D = 0.8                      # sense wire, e.g. 28 AWG silicone
SB_TAP_HOLES = {'CELL1': (-2.0, 70.0), 'CELL3': (2.0, 70.0), 'CELL2': (2.0, 8.0)}   # (y, z) plated holes, ~1.0 mm drill
SB_TAP_PAD_D = 2.0                   # tap hole pad diameter
# derived (x across the board, y along the board width, z along the cells)
sb_xb0 = a_in + SB_INSUL + SB_BCU_H           # board inner face (B.Cu)
sb_xb1 = sb_xb0 + SB_PCB_T                    # board outer face
sb_x_cv0 = sb_xb1 + SB_OUT_H + SB_GAP         # cover inner face (rests on the rebates and pillars)
sb_x_cv1 = sb_x_cv0 + SB_COVER_T
sb_x_out = sb_x_cv1 + SB_LIP                  # rim of the tray
sb_z_pad1 = SB_END_T + SB_PAD_T               # top of the floor zone
sb_z_cell0 = sb_z_pad1 + TAB_T                # cell bottoms
sb_z_cell1 = sb_z_cell0 + CELL_L              # cell tops
sb_z_top_in = sb_z_cell1 + TAB_T + SB_TOP_PAD # top wall, inside face
SB_H = sb_z_top_in + SB_END_T                 # overall shell length (outside of the top wall)
sb_zb1 = SB_H - USB_FACE_OUT                  # board top edge: mating faces flush with the top wall
sb_zb0 = SB_END_T + SB_SLIDE + SB_PCB_CLEAR   # board bottom edge (slid up; the shim fills SB_SLIDE)
sb_notch_y = a_in - SB_PILLAR_W - SB_PCB_CLEAR # bottom corners notched around the screw pillars:
sb_notch_z = sb_z_pad1 + SB_SLIDE + SB_PCB_CLEAR   #   |y| > sb_notch_y and z < sb_notch_z
sb_port_x = sb_xb1 + USB_ZC
sb_board_w = 2 * (a_in - SB_PCB_CLEAR)
sb_board_l = sb_zb1 - sb_zb0
sb_board_area = sb_board_w * sb_board_l - 2 * (sb_board_w/2 - sb_notch_y) * (sb_notch_z - sb_zb0)
assert SB_SEP_T < 2 * pocket_r - CELL_D, "mica does not fit the cell-to-cell gap"
a_cav, c_cav = a_in + SB_SIDE_PAD, c_in + SB_SIDE_PAD   # cell-zone cavity (x < a_in): grown by the side pad
a_sb, c_sb = a_cav + WALL, c_cav + WALL                 # tray outside half-width and -x corner radius
sb_pillar_y = a_in - SB_PILLAR_W / 2          # insert axis at y = +-sb_pillar_y, z = sb_screw_z (pillars sit in the board zone)
sb_screw_z = SB_END_T + SB_PAD_T / 2
sb_cover_w = 2 * (a_in + SB_REB) - 0.2
sb_cover_z0, sb_cover_z1 = SB_END_T + 0.1, sb_z_top_in + SB_SLOT - 0.1
sb_cell_xy = {k: (k[0] * pocket_r, k[1] * pocket_r) for k in SB_CELLS}
sb_pos_caps = {end: [sb_cell_xy[k] for k, (_, e) in SB_CELLS.items() if e == end] for end in ('top', 'bottom')}
# profiles: rounded rect x0..x1, |y| <= h, corner radius rl (-x side), rr (+x side)
SB_OUT = (-a_sb, sb_x_out, a_sb, c_sb, 0.0)
SB_CAV = (-a_cav, a_in, a_cav, c_cav, 0.0)    # cell zone; for x >= a_in the cavity narrows to the board width (guides)
SB_CAP_OUT = (-a_sb - SB_CAP_PROUD, sb_x_out + SB_CAP_PROUD, a_sb + SB_CAP_PROUD, c_sb + SB_CAP_PROUD, SB_CAP_PROUD)
sb_len = SB_H + 2 * SB_CAP_T                  # overall length with the caps
sb_ant_zc = sb_zb1 - SB_ANT_BELOW             # module centre (z)
sb_ant_y = (sb_board_w/2 - SB_ANT_MOD[1], sb_board_w/2)   # module |y| span (antenna end at the edge)
def sb_lanes():
    """EVA lanes as (y0, y1, z0, z1)"""
    z0, z1 = sb_z_cell0 + 2.0, sb_z_cell1 - 2.0; out = []
    for s in (-1, 1):
        y0, y1 = s*pocket_r - SB_LANE_W/2, s*pocket_r + SB_LANE_W/2
        if s == SB_ANT_SIDE:
            g0, g1 = sb_ant_zc - SB_ANT_MOD[0]/2 - SB_LANE_GAP, sb_ant_zc + SB_ANT_MOD[0]/2 + SB_LANE_GAP
            out += [(y0, y1, z0, g0), (y0, y1, g1, z1)]
        else: out.append((y0, y1, z0, z1))
    return out
sb_tab_y = {'PACK-': sb_cell_xy[(1, -1)][1], 'PACK+': sb_cell_xy[(1, 1)][1]}   # PACK strip centrelines (C1, C4)
sb_z_mid = (sb_zb0 + sb_zb1) / 2
def kicad(y, z): return 100.0 + y, 100.0 - (z - sb_z_mid)   # board position in Production/Monolith.kicad_pcb

def _dxf(path, ents):
    open(path, 'w').write("0\nSECTION\n2\nENTITIES\n" + "".join(ents) + "0\nENDSEC\n0\nEOF\n")
def _line(e, x1, y1, x2, y2, l): e.append(f"0\nLINE\n8\n{l}\n10\n{x1:.4f}\n20\n{y1:.4f}\n11\n{x2:.4f}\n21\n{y2:.4f}\n")
def _circ(e, x, y, r, l): e.append(f"0\nCIRCLE\n8\n{l}\n10\n{x:.4f}\n20\n{y:.4f}\n40\n{r:.4f}\n")
def _rect(e, cx, cy, w, h, l):
    p = [(cx-w/2, cy-h/2), (cx+w/2, cy-h/2), (cx+w/2, cy+h/2), (cx-w/2, cy+h/2)]
    for i in range(4): _line(e, *p[i], *p[(i+1) % 4], l)

def write_side_dxf(path):
    """Side board outline in the board plane: DXF x = shell y, DXF y = shell z (shell bottom at 0).
    Layers: OUTLINE, USB_NOTCH (10.20 x 5.65 footprint notches), CELLS_REF (cell tangent lines,
    groove centreline, cell ends), VENT_KEEPOUT (no gap pad or tall parts under the cover vent)."""
    e = []; w, z0, z1, ny, nz = sb_board_w / 2, sb_zb0, sb_zb1, sb_notch_y, sb_notch_z
    p = [(-ny, z0), (ny, z0), (ny, nz), (w, nz), (w, z1), (-w, z1), (-w, nz), (-ny, nz)]
    for i in range(len(p)): _line(e, *p[i], *p[(i+1) % len(p)], 'OUTLINE')
    for py in (-SB_PORT_Y, SB_PORT_Y): _rect(e, py, z1 - 5.65/2, 10.20, 5.65, 'USB_NOTCH')
    for y in (-pocket_r, 0, pocket_r): _line(e, y, z0, y, z1, 'CELLS_REF')
    for z in (sb_z_cell0, sb_z_cell1): _line(e, -w, z, w, z, 'CELLS_REF')
    _circ(e, 0, SB_VENT_Z, SB_VENT_D/2 + 2, 'VENT_KEEPOUT')
    s, (ma, mi) = SB_ANT_SIDE, SB_ANT_MOD     # BLE module on B.Cu at the edge, and the EVA lanes (no B.Cu parts there)
    _rect(e, s*(w - mi/2), sb_ant_zc, mi, ma, 'BLE_MODULE_BCU')
    for y0, y1, z0, z1 in sb_lanes(): _rect(e, (y0 + y1)/2, (z0 + z1)/2, y1 - y0, z1 - z0, 'BCU_EVA_LANES')
    for yc in sb_tab_y.values():              # PACK strip pads on F.Cu, and the sense-wire holes
        _rect(e, yc, sb_zb0 + SB_TAB_PAD_H/2, SB_TAB_W + 1.0, SB_TAB_PAD_H, 'TAB_PADS')
    for y, z in SB_TAP_HOLES.values(): _circ(e, y, z, SB_TAP_PAD_D/2, 'TAB_PADS')
    _dxf(path, e)

def write_cover_dxf(path):
    """Aluminium cover flat pattern: DXF x = shell y, DXF y = shell z. OUTLINE, HOLES (M2 clearance,
    use low-head screws: the bottom bumper covers them), VENT (ePTFE patch on the inside)."""
    e = []
    _rect(e, 0, (sb_cover_z0 + sb_cover_z1)/2, sb_cover_w, sb_cover_z1 - sb_cover_z0, 'OUTLINE')
    for sy in (-1, 1): _circ(e, sy*sb_pillar_y, sb_screw_z, 1.1, 'HOLES')
    _circ(e, 0, SB_VENT_Z, SB_VENT_D/2, 'VENT')
    _dxf(path, e)

def drop_g(h_m, stroke_mm, shape=1.3):
    """peak deceleration (g) for a free fall of h_m stopped over stroke_mm; shape > 1 for a real (non-flat) foam curve"""
    return shape * h_m * 1000 / stroke_mm

def side_groove_depth(y):
    """Free height between the board's inner face and the cells at board position y (mm)."""
    dy = np.abs(np.abs(y) - pocket_r)
    r = CELL_D / 2
    return np.where(dy < r, sb_xb0 - (pocket_r + np.sqrt(np.maximum(r*r - dy*dy, 0))), sb_xb0 - pocket_r)

if __name__ == '__main__':
    write_stl('monolith_shell.stl'); write_dxf('monolith_bottom_pcb.dxf')
    write_side_dxf('monolith_side_pcb.dxf'); write_cover_dxf('monolith_side_cover.dxf')
    # checks
    from collections import Counter
    key = lambda p: tuple(p)
    ed = Counter()
    for t in V:
        for i in range(3): ed[(key(t[i]), key(t[(i+1) % 3]))] += 1
    bad = sum(1 for (a, b), c in ed.items() if c != 1 or ed.get((b, a), 0) != 1)
    vol = np.einsum('ij,ij->i', V[:,0], np.cross(V[:,1], V[:,2])).sum()/6
    print(f"triangles {len(V)}  non-manifold edges {bad}")
    print(f"outside {2*a_out:.2f} sq, corner R {c_out:.2f}; inside {2*a_in:.2f}, corner R {c_in:.2f}; length {H:.2f}")
    print(f"rib zone z {z_rib0:.2f}..{z_rib1:.2f}; volume {vol/1000:.2f} cm3; mass @1.18 g/cc {vol/1000*1.18:.1f} g")
    print(f"min wall {np.min(r_out - r_wall):.3f}")
    print(f"PCB outline {2*(a_in-PCB_CLEAR):.2f} sq, corner R {c_in-PCB_CLEAR:.2f}")
    print(f"side layout: tray {sb_x_out + a_sb:.2f} x {2*a_sb:.2f} x {SB_H:.2f}; with caps "
          f"{sb_x_out + a_sb + 2*SB_CAP_PROUD:.2f} x {2*(a_sb + SB_CAP_PROUD):.2f} x {sb_len:.2f}; "
          f"cover {sb_cover_w:.2f} x {sb_cover_z1 - sb_cover_z0:.2f} x {SB_COVER_T}")
    st = 0.65 * SB_CAP_T
    print(f"end-cap stroke ~{st:.1f} mm (65 % of {SB_CAP_T}): est. peak "
          + ", ".join(f"{h} m -> {drop_g(h, st):.0f} g" for h in (1.0, 1.5))
          + f"; bottom-down drops add {0.65*SB_PAD_T:.1f} mm of floor pad between the cells and the tray")
    print(f"side board {sb_board_w:.2f} x {sb_board_l:.2f} mm, corner notches -> {sb_board_area:.0f} mm2 per side, "
          f"x {sb_xb0:.2f}..{sb_xb1:.2f}; ports at x {sb_port_x:.2f}, y +-{SB_PORT_Y}")
    print("pack connections (KiCad x, y): " + ", ".join(f"{n} {kicad(y, sb_zb0 + SB_TAB_PAD_H/2)[0]:.1f}, {kicad(y, sb_zb0 + SB_TAB_PAD_H/2)[1]:.1f} pad"
          for n, y in sb_tab_y.items()) + "; " + ", ".join(f"{n} {kicad(y, z)[0]:.1f}, {kicad(y, z)[1]:.1f} hole" for n, (y, z) in SB_TAP_HOLES.items()))
    ys = np.array([0, 2, 4, 6, 8, 15, 18, 21])
    print("inner-face free height vs y: " + ", ".join(f"{y:g}:{d:.1f}" for y, d in zip(ys, side_groove_depth(ys))))
    # assembly checks (positive = clearance)
    chk = {
        'port faces below the top wall while the board drops in': sb_z_top_in - (SB_H - SB_SLIDE),
        'board bottom above the floor while it drops in': sb_zb0 - SB_SLIDE - SB_END_T,
        'board notches above the pillars while it drops in': sb_notch_z - SB_SLIDE - sb_z_pad1,
        'port hole to the cover slot (x)': sb_x_cv0 - (sb_port_x + (USB_SEAL_H + 0.2)/2),
        'USB-C body to the cover (x)': sb_x_cv0 - (sb_port_x + USB_UP),
        'seal ring (0.5-1.5 behind the face) inside the top wall': SB_END_T - 1.5,
        'cover top edge under the lip': sb_cover_z1 - sb_z_top_in,
        'pillars below the cells (z)': sb_z_cell0 - TAB_T - sb_z_pad1,
        'board top stops: board edge to the top wall (stop height)': sb_z_top_in - sb_zb1,
        'board stops clear of the port holes (y)': SB_STOP_Y0 - (SB_PORT_Y + (USB_SEAL_W + 0.2)/2),
        'hold-down pad compressed (pad - gap)': SB_HOLD_T - (sb_x_cv0 - (sb_port_x + USB_UP)),
        'port well clear of the seal holes (y)': SB_WELL_W/2 - (SB_PORT_Y + (USB_SEAL_W + 0.2)/2),
        'port well: cap wall to the +x edge beyond 2 mm (x)':SB_CAP_OUT[1] - (sb_port_x + SB_WELL_H/2) - 2.0,
        'cap band clear of the cover vent (z)': (SB_VENT_Z - SB_VENT_D/2) - SB_CAP_BAND,
        'mica fits the cell-to-cell gap': 2*pocket_r - CELL_D - SB_SEP_T,
        'PACK strip between the floor spacer and the board (x)': (sb_xb0 - a_in) - SB_TAB_T,
        'PACK strips clear of the centre shim (y)': (min(abs(v) for v in sb_tab_y.values()) - SB_TAB_W/2) - SB_SHIM_HALF,
        'PACK strips clear of the board corner notches (y)': sb_notch_y - (max(abs(v) for v in sb_tab_y.values()) + SB_TAB_W/2),
        'room under the board edge for the strip wrap (z)': (sb_zb0 - SB_TAB_T) - SB_END_T - 1.0,
        'PACK pads clear of the vent keep-out (y)': (min(abs(v) for v in sb_tab_y.values()) - SB_TAB_W/2 - 0.5) - (SB_VENT_D/2 + 2),
        'top tap holes below the USB-C bodies (z)': (sb_zb1 + USB_FACE_OUT - USB_DEPTH) - (max(SB_TAP_HOLES['CELL1'][1], SB_TAP_HOLES['CELL3'][1]) + SB_TAP_PAD_D/2) - 1.0,
        'tap wires in the groove behind the board (free height - wire)': float(side_groove_depth(abs(SB_TAP_HOLES['CELL1'][0]))) - SB_WIRE_D,
        'tap wires beside the mica (y)': abs(SB_TAP_HOLES['CELL1'][0]) - SB_WIRE_D/2 - SB_SEP_T/2 - 0.5,
        'CELL2 hole clear of the PACK pads (y)': (min(abs(v) for v in sb_tab_y.values()) - SB_TAB_W/2 - 0.5) - (abs(SB_TAP_HOLES['CELL2'][0]) + SB_TAP_PAD_D/2),
        'BLE module on B.Cu: room behind it to the fish paper (min over its span)':
            float(np.min(side_groove_depth(np.linspace(*sb_ant_y, 41)))) - SB_INSUL - SB_ANT_H,
        'EVA lanes: 3 x 1 mm squeezed into the gap (compression)': SB_LANE_LAYERS*1.0 - (sb_xb0 - (a_in + 0.2)),
        'EVA lanes not over-squeezed (< 40 %)': 0.4*SB_LANE_LAYERS - (SB_LANE_LAYERS*1.0 - (sb_xb0 - (a_in + 0.2))),
        'BLE module: ground along the edge above it (>= 10)': sb_zb1 - (sb_ant_zc + SB_ANT_MOD[0]/2) - 10.0,
        'BLE module 10 mm below the USB-C bodies (z)': (sb_zb1 + USB_FACE_OUT - USB_DEPTH) - (sb_ant_zc + SB_ANT_MOD[0]/2) - 10.0,
    }
    for k, v in chk.items(): print(f"  {'ok ' if v >= 0 else 'BAD'} {v:6.2f}  {k}")
