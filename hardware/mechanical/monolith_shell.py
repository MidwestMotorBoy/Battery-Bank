"""Monolith 4S1P 21700 shell - parametric generator (numpy only).
Run: python3 monolith_shell.py   -> monolith_shell.stl, monolith_bottom_pcb.dxf
All dimensions in mm. Z = 0 is the bottom rim of the tube."""
import numpy as np, struct

# ---------------- parameters ----------------
CELL_D      = 21.85   # FEB 21700G (68E) 6500 mAh: 21.65 +-0.2 mm, so design to the 21.85 maximum (measure yours)
CELL_L      = 71.1    # 70.95 +-0.2 mm; Batemo measures 71.1. A 71.15 maximum cell squeezes the spring rings 0.05 more.
                      # Was the EVE 58E, 21.5 x 70.8, until 2026-10-21
CELL_D_58E  = 21.5    # the board outline is still derived from the 58E-era pocket (see pocket_r), so it doesn't change
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
pocket_r = (CELL_D_58E + CELL_CLEAR) / 2      # also the inner corner radius. Frozen at the 58E value: a_in is the side board's
                                              # guide line (43.2 mm board), which must not move with the cell
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
# Assembly: the cells, TPU frame and board are one power module, built and tested on the bench (see "Power module"
#   below) -> module in through the side, resting on its ring carrier (board ~2.1 mm low) -> lifted SB_SLIDE so both
#   USB-C mating faces pass into their holes in the top wall (the connector's own mating direction, so the seal rings
#   seat whole) -> PA12 wedge pushed in under it -> gap pad -> aluminium cover: top edge under the top-wall lip, then
#   two M2 screws into heat-set inserts in the bottom corner pillars (hidden under the bumper). Nothing is soldered
#   in the tray.
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
SB_PAD_T     = 4.3    # floor zone under the cells: the TPU bottom holder (base plate + spring rings). 4.6 -> 4.3 with the
                     # FEB cell (0.3 longer), so the tray and the board outline keep their length
SB_PIL_T     = 4.8    # screw-boss zone in the bottom corners (sets the board's corner notches and the screw height: unchanged)
SB_TOP_PAD   = 1.2    # TPU top plate of the cell frame (JLC TPU minimum wall 1.2); the floor zone gave up the 0.2
SB_SLIDE     = 2.5    # board slide that engages the ports (needs > SB_END_T - (USB_FACE_OUT - SB_END_T))
SB_PCB_CLEAR = 0.2    # board edge to wall, and board to the end zones
SB_PORT_Y    = 6.5    # ports at y = +-6.5 (13 mm apart, as on the production board)
SB_INSERT_D, SB_INSERT_L = 3.2, 4.0   # M2 heat-set insert pilot (e.g. M2 x 3 x 3.2): diameter, depth
SB_PILLAR_W  = 5.0    # screw-boss corner zone: width in y, from the board-guide line (a_in) inward
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
SB_SIDE_PAD  = 0.0    # (was a 0.2 mm fish-paper liner round the cells; dropped 2026-10-21: the TPU cage locates them)
SB_EVA_T     = 1.0    # EVA foam sheet: the cell-end pads (top, and over the TPU floor spacer) and, doubled, the USB-C hold-downs
SB_SEP_T     = 0.0    # (was a 0.2 mm mica cross between the cells; dropped 2026-10-21 for the TPU cage webs)
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
# vibration and trail durability (2026-10-18)
SB_AXIAL_PRELOAD = 0.4   # floor spacer printed this much taller than its gap: squeezes the cell stack ends (covers MJF +-0.3)
SB_CRUSH_W, SB_CRUSH_H = 1.0, 0.3   # crush ribs on the cell-zone walls (at each cell's tangent): 0.15 mm onto the cell wrap
SB_COVER_GAP = 0.3       # cover edge to tray, all round: nylon grows ~0.35 mm more than aluminium over 78 mm and 60 K;
                         # the joint is sealed with a bead of neutral-cure silicone (formed-in-place gasket)
SB_GROOVE_Z, SB_GROOVE_W, SB_GROOVE_D = 4.5, 1.2, 0.3   # cap retention: groove round the tray (-x, +-y faces) at each end
SB_BEAD_W = 0.9          # matching bead inside each cap band
SB_DRAIN_W, SB_DRAIN_H = 2.0, 1.5    # drain channel from the port well out through the top cap's +x wall
SB_STANDOFFS = [(-15.0, 28.0), (15.0, 28.0), (-15.0, 48.0), (15.0, 48.0)]   # (y, z) SMD standoffs on F.Cu for the cover
#   (upper pair was z 56: that sat on the port-1 BQ25756 and on the BLE module end, 2026-10-20)
SB_STANDOFF_D = 4.35     # Wuerth WA-SMSI 9774035243R body diameter (KiCad courtyard 5.8)
SB_WELL_W, SB_WELL_H = 28.0, 9.0     # one port well through the top cap for both plugs (USB-C overmold rec. max 12.35 x 6.5)
# BLE module (CC2340R5MODA, 7 x 10 x 2.3 mm max) on B.Cu at the right (+y, C4 / PACK+) board edge, antenna end at the
# edge: the board's ground plane sits between it and the aluminium cover, and it radiates out through the printed
# side wall. >= 10 mm of ground along the edge above it (TI SWRS349A fig. 9-2). The cover is whole (no notch).
SB_ANT_SIDE  = 1                     # +1 = right edge seen from the cover (+y), -1 = left
SB_ANT_BELOW = 19.1                  # module centre below the board's top edge (10 mm of ground above, 10 mm from the USB-C bodies)
SB_ANT_MOD   = (7.0, 10.0)           # module: along the edge, into the board
SB_ANT_H     = 2.3                   # module height on B.Cu
# Power module (2026-10-21): the cells, their TPU frame and the board are built into ONE module on the bench, every
# connection is a nickel tab through a plated slot in the board, soldered on F.Cu, and the module is tested (programmed,
# gauge trained, 100 W run) before it goes near the tray. In the tray the whole module makes the board's 2.5 mm slide:
#   drop in through the open side 2.5 mm low -> lift it 2.5 mm (USB-C faces into the top wall, board edge on the stops)
#   -> push the PA12 wedge in under it from the open side. The wedge fills SB_SLIDE under the cells and under the
#   board's bottom edge (it is the old shim too); its nose is chamfered so it takes up the last of the preload, and the
#   cover traps it.
# Cell frame: two printed TPU parts that ride with the module.
# - ring carrier (was the bottom holder): thin base + a slotted spring ring under each cell end, printed
#   SB_AXIAL_PRELOAD proud; the CELL2 tail runs in the channel between the rings.
# - top frame: top plate (cut-outs over the + caps) + two bars down the board side that hold the cells off B.Cu.
SB_FRAME_BASE = 0.8                  # ring carrier base plate (the floor zone is now wedge + carrier)
SB_RING_OD, SB_RING_ID, SB_RING_SLOT = 17.0, 14.4, 2.0   # spring rings (ID clears the + cap cut-out), 4 slots
SB_BAR_Y = (6.5, 11.3)               # bars: |y| span (to within 0.33 of the cell tangent at 11.625, clear of the BLE module at 11.6)
SB_BAR_Z0 = None                     # set below: bars start above the bottom tails
# TPU cell cage (2026-10-21, replaces the mica cross and the liner): a cross of SB_CAGE_WEB webs between the four cells in
# three bands (bottom, middle, top), joined by a round spine along the pack axis. The cells sit SB_CAGE_WEB + 2 x
# SB_CAGE_CLR apart, so they can't touch; the pack grows about 0.7 mm in y and 0.9 mm in x for it. The board outline is
# unchanged: the board stays 43.2 mm wide (a_in) and sits in a cavity that is now a little wider than it, located in y
# by the USB-C bodies in the port holes. The cells go into the cage first, then the strips are welded over it.
SB_CAGE_WEB, SB_CAGE_CLR = 1.2, 0.1  # web thickness (JLC TPU minimum wall), clearance each side
SB_CAGE_BAND = 10.0                  # height of each web band
SB_CAGE_END = 1.0                    # bands stop this far inside the cell ends (the strips pass over them)
SB_CAGE_SPINE_D = 5.0                # spine through the centre void, joins the bands
SB_CELL_WALL = 0.15                  # cell to cavity wall (the crush ribs take it up)
# The two cover screws go into M2 heat-set inserts in two bosses on the wedge (not in tray pillars any more: the module
# would sweep through those as it drops in). A ridge on the tray floor snaps the wedge in place.
SB_SNAP = (-10.0, 1.0, 0.3)          # floor ridge: x centre, width, height (|y| <= SB_SNAP_HALF); groove in the wedge
SB_SNAP_HALF = 8.0
SB_WEDGE_T = SB_SLIDE                # wedge under the ring carrier (z SB_END_T .. +SB_WEDGE_T); under the board it is
                                     # taller, up to the board's bottom edge
SB_WEDGE_HALF = None                 # set below: the wedge fills the floor zone wall to wall
SB_WEDGE_NOSE = (4.0, 1.0)           # chamfered nose at its -x end: length, height it rises by
SB_LANE_W, SB_LANE_LAYERS, SB_LANE_GAP = 6.0, 3, 2.0     # (legacy EVA lane values, kept for older scripts)
# cells seen from the port end: (sx, sy) of the centre -> (name, end that carries the positive cap).
# C1 and C4 face the board (PACK- on the C1 side, -y); series chain C1 -> C2 -> C3 -> C4 (Production/README.md).
SB_CELLS = {(1, -1): ('C1', 'top'), (-1, -1): ('C2', 'bottom'), (-1, 1): ('C3', 'top'), (1, 1): ('C4', 'bottom')}
# Pack connections: seven nickel tails through seven plated slots, all soldered on F.Cu (no wire, no connector).
# - PACK- (C1 bottom) / PACK+ (C4 bottom): a 0.2 x 7 mm tab, split near the board into a 4.2 mm power finger and a
#   1.2 mm Kelvin finger (1N / 4P for the gauge), each through its own slot. A 1 mm kink in the gap behind the board
#   gives the tab some give between the cells and the board.
# - CELL2 (C2+/C3- strip, bottom): a 3 mm tail off the strip, along the channel between the spring rings (kapton
#   wrapped: it passes under the C1 / C4 rims), kinked the same way, straight into its slot.
# - CELL1 (C1+/C2- strip, top) / CELL3 (C3+/C4- strip, top): the strip itself runs on as a 3 mm tail, out past the
#   cell (outside the frame bars, clear of the USB-C notches), down the gap behind the board and through its slot.
# The tails are cut long, welded with the strips, threaded through the slots as the board meets the frame, soldered,
# then trimmed on F.Cu.
SB_TAB_W, SB_TAB_T = 7.0, 0.15       # nickel strip (series strips, sense tails)
SB_PACK_T = 0.2                      # PACK tabs: 0.2 mm nickel (9.4 A)
SB_FINGER = (4.2, 1.6, 1.2)          # PACK tab split: power finger, gap, Kelvin finger (Kelvin on the inner side; the
                                     # gap keeps the two slot pads 0.4 apart, so the Kelvin pad stays a separate net)
SB_TAIL_W = 3.0                      # CELL1-3 tails
SB_TAIL_Y = 13.9                     # |y| of the CELL1 / CELL3 tails (outside the frame bars and the USB-C notches)
SB_TAIL_TOP_Z = 72.0                 # CELL1 / CELL3 slots (a 5 mm drop behind the board gives the tail some give)
SB_SLOT_W, SB_SLOT_CLR, SB_SLOT_RING = 0.6, 0.4, 0.4    # plated slot: width (z), length over the tail (y), annular ring
SB_KINK = (23.35, 24.55, 1.0)        # strain-relief kink in the bottom tails: x from, x to, depth (+0.35 with the FEB cell)
SB_WIRE_D = 0.8                      # (legacy)
# PACK wire tails (option C, 2026-10-24): each PACK power path is an 18 AWG PTFE wire, bench-soldered to a 0.2 x 7 nickel
# pad that is welded to the cell end inside the weld window. It runs through a notch in the carrier's bottom frame
# (monolith_cup.py), crosses the gap behind the board and is soldered into a plated hole. The Kelvin side (1N / 4P) is
# a 28 AWG PTFE wire from the same pad, through its own notch, into the existing Kelvin slot.
SB_PWIRE_OD, SB_KWIRE_OD = 1.45, 0.6  # 18 AWG thin-wall PTFE (M22759/11-18, 1.37 max) / 28 AWG PTFE, outside diameter
SB_PWIRE_HOLE, SB_PWIRE_RING = 1.5, 0.4   # PACK wire plated hole (finished; 19/30 strand ~1.22 mm) and its annular ring
SB_PWIRE_Z = 5.75                    # hole centre: as low as the ring allows over the board's bottom edge
# derived (x across the board, y along the board width, z along the cells)
sb_pr = (CELL_D + SB_CAGE_WEB + 2 * SB_CAGE_CLR) / 2   # cell centres at (+-sb_pr, +-sb_pr)
sb_ac = sb_pr + CELL_D / 2 + SB_CELL_WALL     # cell-zone half-width (cavity, -x and +-y walls), and the cells' +x face line
sb_xb0 = sb_ac + SB_INSUL + SB_BCU_H          # board inner face (B.Cu)
sb_xb1 = sb_xb0 + SB_PCB_T                    # board outer face
sb_x_cv0 = sb_xb1 + SB_OUT_H + SB_GAP         # cover inner face (rests on the rebates and pillars)
sb_x_cv1 = sb_x_cv0 + SB_COVER_T
sb_x_out = sb_x_cv1 + SB_LIP                  # rim of the tray
sb_z_pad1 = SB_END_T + SB_PAD_T               # top of the floor zone (bottom holder)
sb_z_pil = SB_END_T + SB_PIL_T                # top of the screw pillars
sb_z_cell0 = sb_z_pad1 + TAB_T                # cell bottoms
sb_z_cell1 = sb_z_cell0 + CELL_L              # cell tops
sb_z_top_in = sb_z_cell1 + TAB_T + SB_TOP_PAD # top wall, inside face
SB_H = sb_z_top_in + SB_END_T                 # overall shell length (outside of the top wall)
sb_zb1 = SB_H - USB_FACE_OUT                  # board top edge: mating faces flush with the top wall
sb_zb0 = SB_END_T + SB_SLIDE + SB_PCB_CLEAR   # board bottom edge (slid up; the shim fills SB_SLIDE)
sb_notch_y = a_in - SB_PILLAR_W - SB_PCB_CLEAR # bottom corners notched around the screw pillars:
sb_notch_z = sb_z_pil + SB_SLIDE + SB_PCB_CLEAR    #   |y| > sb_notch_y and z < sb_notch_z
sb_port_x = sb_xb1 + USB_ZC
sb_board_w = 2 * (a_in - SB_PCB_CLEAR)
sb_board_l = sb_zb1 - sb_zb0
sb_board_area = sb_board_w * sb_board_l - 2 * (sb_board_w/2 - sb_notch_y) * (sb_notch_z - sb_zb0)
a_cav, c_cav = sb_ac + SB_SIDE_PAD, sb_ac - sb_pr + SB_SIDE_PAD   # cavity half-width; -x corners concentric with C2 / C3
a_sb, c_sb = a_cav + WALL, c_cav + WALL                 # tray outside half-width and -x corner radius
sb_pillar_y = a_in - SB_PILLAR_W / 2          # insert axis at y = +-sb_pillar_y, z = sb_screw_z (bosses on the wedge, board zone)
sb_screw_z = SB_END_T + SB_PIL_T / 2
sb_cover_w = 2 * (a_cav + SB_REB) - 2 * SB_COVER_GAP
sb_cover_z0, sb_cover_z1 = SB_END_T + SB_COVER_GAP, sb_z_top_in + SB_SLOT - SB_COVER_GAP
sb_cell_xy = {k: (k[0] * sb_pr, k[1] * sb_pr) for k in SB_CELLS}
sb_pos_caps = {end: [sb_cell_xy[k] for k, (_, e) in SB_CELLS.items() if e == end] for end in ('top', 'bottom')}
# profiles: rounded rect x0..x1, |y| <= h, corner radius rl (-x side), rr (+x side)
SB_OUT = (-a_sb, sb_x_out, a_sb, c_sb, 0.0)
SB_CAV = (-a_cav, sb_ac, a_cav, c_cav, 0.0)   # cell zone; for x >= sb_ac the board zone keeps the same width
SB_CAP_OUT = (-a_sb - SB_CAP_PROUD, sb_x_out + SB_CAP_PROUD, a_sb + SB_CAP_PROUD, c_sb + SB_CAP_PROUD, SB_CAP_PROUD)
sb_len = SB_H + 2 * SB_CAP_T                  # overall length with the caps
SB_GROOVE = (SB_OUT[0] + SB_GROOVE_D, SB_OUT[1], SB_OUT[2] - SB_GROOVE_D, SB_OUT[3] - SB_GROOVE_D, 0.0)   # tray profile in the groove
sb_standoff_h = 3.5                           # Wuerth WA-SMSI 9774035243R (M2, 3.5 mm): 0.2 mm under the cover, so it only bears once the cover flexes
sb_ant_zc = sb_zb1 - SB_ANT_BELOW             # module centre (z)
sb_ant_y = (sb_board_w/2 - SB_ANT_MOD[1], sb_board_w/2)   # module |y| span (antenna end at the edge)
SB_BAR_Z0 = sb_z_cell0 + 1.0                  # bars start above the tails on the cell bottoms
SB_WEDGE_HALF = a_cav - 0.2
def sb_lanes():
    """what presses on B.Cu behind the board, as (y0, y1, z0, z1): now the cell frame's two bars (was the EVA lanes).
    Keep B.Cu parts out of these. (Name kept: Production/tools/make_board.py reads it.)"""
    return [(-SB_BAR_Y[1], -SB_BAR_Y[0], SB_BAR_Z0, sb_z_top_in), (SB_BAR_Y[0], SB_BAR_Y[1], SB_BAR_Z0, sb_z_top_in)]
sb_tab_y = {'PACK-': sb_cell_xy[(1, -1)][1], 'PACK+': sb_cell_xy[(1, 1)][1]}   # PACK tab centrelines (C1, C4)
sb_z_tail_b = sb_z_cell0 - 0.2                # bottom strips and tails: top face (under the cell bottoms)
sb_z_tail_t = sb_z_cell1 + 0.2                # top strips and tails: bottom face (over the + rings)
def sb_fingers(name):
    """PACK tab fingers as {slot name: (y0, y1)}: the power finger outside, the Kelvin finger inside"""
    yc = sb_tab_y[name]; s = 1 if yc > 0 else -1; hw = SB_TAB_W / 2; pw, g, kw = SB_FINGER
    inner, outer = yc - s * hw, yc + s * hw
    k = '4P' if s > 0 else '1N'
    return {name: tuple(sorted((outer, outer - s * pw))), k: tuple(sorted((inner, inner + s * kw)))}
def sb_slots():
    """the five plated slots, {name: (y centre, z centre, length along y)}: the two Kelvin leads and the three cell taps
    (the PACK power paths are wires in plated holes, sb_pack_holes)"""
    out = {}
    zb = sb_z_tail_b - SB_PACK_T / 2
    for n in ('PACK-', 'PACK+'):
        for k, (y0, y1) in sb_fingers(n).items():
            if k not in ('PACK-', 'PACK+'): out[k] = ((y0 + y1) / 2, zb, y1 - y0 + SB_SLOT_CLR)
    out['CELL2'] = (0.0, sb_z_tail_b - SB_TAB_T / 2, SB_TAIL_W + SB_SLOT_CLR)
    out['CELL1'] = (-SB_TAIL_Y, SB_TAIL_TOP_Z, SB_TAIL_W + SB_SLOT_CLR)
    out['CELL3'] = (SB_TAIL_Y, SB_TAIL_TOP_Z, SB_TAIL_W + SB_SLOT_CLR)
    return out
def sb_pack_holes():
    """the PACK wire holes, {name: (y centre, z centre, finished diameter)}, on the old power-finger centrelines"""
    return {n: (sum(sb_fingers(n)[n]) / 2, SB_PWIRE_Z, SB_PWIRE_HOLE) for n in ('PACK-', 'PACK+')}
def sb_wire_runs():
    """where the PACK and Kelvin wires cross the gap behind B.Cu, as (y0, y1, z0, z1) with 0.5 mm margin. No B.Cu parts
    here: the 1.2 mm power wire leaves no room even for the low parts the nickel tail runs allow."""
    m, out = 0.5, []
    for n, (y, z, _) in sb_pack_holes().items(): out.append((y - SB_PWIRE_OD/2 - m, y + SB_PWIRE_OD/2 + m, sb_zb0, z + SB_PWIRE_OD/2 + m))
    for k in ('1N', '4P'):
        y, z, _ = sb_slots()[k]; out.append((y - SB_KWIRE_OD/2 - m, y + SB_KWIRE_OD/2 + m, sb_zb0, z + SB_KWIRE_OD/2 + m))
    return out
def sb_tail_runs():
    """where nickel runs behind B.Cu, as (y0, y1, z0, z1) with 0.5 mm margin: the bottom tails and their kinks, and the
    CELL1 / CELL3 tails down the gap (about 1.1 mm from B.Cu). Only low B.Cu parts here (<= 0.6 mm)."""
    out, m = [], 0.5
    zlo = sb_z_tail_b - SB_PACK_T - SB_KINK[2] - m
    out.append((-SB_TAIL_W/2 - m, SB_TAIL_W/2 + m, zlo, sb_z_tail_b + m))
    for sy in (-1, 1): out.append((sy*SB_TAIL_Y - SB_TAIL_W/2 - m, sy*SB_TAIL_Y + SB_TAIL_W/2 + m, SB_TAIL_TOP_Z - m, sb_zb1))
    return out
# Front-cell NTCs (C1 on TS1, C4 on TS4), 2026-10-24: research_notes/Pack thermal BAK 65E/ntc-placement.md
SB_NTC_BEAD = (12.9, 48.0)           # bead centre (|y|, z): on the hot stripe, 7° outboard of the board-facing line, in the filler
SB_NTC_CAP_Z = 5.0                   # closed-cell foam cap over the bead (4 x 5 mm), its length along z
SB_NTC_LEAD_Y = (12.0, 14.5)         # leads taped up the can in this |y| band, beside the carrier rail
SB_NTC_PAD_Y, SB_NTC_PAD_Z, SB_NTC_PAD_D = 14.7, (64.0, 68.0), 1.7   # lead pads: |y| (13.4 in the note; 14.7 clears
                                     # port 1's C406 on F.Cu), z of pads 1 and 2 (4 mm pitch), pad size (0.7 drill)
def sb_ntc_pads():
    """the front-cell NTC lead pads, {cell: (y, z of pad 1, z of pad 2)}: C1 on the PACK- side, C4 on the PACK+ side"""
    return {c: (s * SB_NTC_PAD_Y,) + SB_NTC_PAD_Z for c, s in (('C1', -1), ('C4', 1))}
def sb_ntc_runs():
    """where the front-cell NTC bead, its foam cap and its leads sit behind B.Cu, up to the lead pads, as
    (y0, y1, z0, z1) with 0.5 mm margin, C1 then C4. No B.Cu parts here."""
    m, out = 0.5, []
    for s in (-1, 1):
        y0, y1 = SB_NTC_LEAD_Y[0] - m, SB_NTC_PAD_Y + SB_NTC_PAD_D / 2 + m
        out.append((min(s * y0, s * y1), max(s * y0, s * y1), SB_NTC_BEAD[1] - SB_NTC_CAP_Z / 2 - m,
                    max(SB_NTC_PAD_Z) + SB_NTC_PAD_D / 2 + m))
    return out
SB_TAP_HOLES = {n: (y, z) for n, (y, z, _) in sb_slots().items() if n.startswith('CELL')}   # (legacy name for make_board.py)
SB_TAB_PAD_H = 5.0                             # (legacy: the old PACK strip pads; Production/tools/make_board.py still reads it)
sb_z_mid = (sb_zb0 + sb_zb1) / 2
def kicad(y, z): return 100.0 + y, 100.0 - (z - sb_z_mid)   # board position in Production/Monolith.kicad_pcb
# The cup (monolith_cup.py, adopted 2026-10-21): its board-facing values live here so Production/tools/make_board.py
# can read them (KiCad's python can't import monolith_cup: manifold3d).
CUP_FILL_Y, CUP_FILL_Z = (7.0, 16.0), (27.0, 53.0)   # gap filler, B.Cu to the two front cells: |y| span, z span
CUP_RAIL_GAP = (25.0, 55.0)          # carrier rails (|y| SB_BAR_Y) stop here so the filler reaches the cell tangents
CUP_PEGS = [(s * 8.6, z) for s in (-1, 1) for z in (14.0, 68.0)]   # carrier pegs through the board, (y, z)
CUP_PEG_D, CUP_PEG_HOLE_D = 2.0, 2.2  # peg, and its NPTH hole in the board
CUP_PEG_PROUD = 0.6                  # peg tip above F.Cu
CUP_VENT = (0.0, 14.0)               # ePTFE vent in the cup's board-side wall, (y, z)
cup_fr_b0 = sb_z_tail_b - SB_PACK_T - 0.05 - 1.6     # carrier bottom frame, underside (monolith_cup.py FR_B0)
def cup_rails():
    """the carrier rails pressing on B.Cu, as (y0, y1, z0, z1): two per side, split at CUP_RAIL_GAP"""
    return [(y0, y1, z0, z1) for y0, y1 in ((-SB_BAR_Y[1], -SB_BAR_Y[0]), SB_BAR_Y)
            for z0, z1 in ((cup_fr_b0, CUP_RAIL_GAP[0]), (CUP_RAIL_GAP[1], sb_z_top_in))]

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
    for y in (-sb_pr, 0, sb_pr): _line(e, y, z0, y, z1, 'CELLS_REF')
    for z in (sb_z_cell0, sb_z_cell1): _line(e, -w, z, w, z, 'CELLS_REF')
    _circ(e, 0, SB_VENT_Z, SB_VENT_D/2 + 2, 'VENT_KEEPOUT')
    s, (ma, mi) = SB_ANT_SIDE, SB_ANT_MOD     # BLE module on B.Cu at the edge, and the frame bars (no B.Cu parts there)
    _rect(e, s*(w - mi/2), sb_ant_zc, mi, ma, 'BLE_MODULE_BCU')
    for y0, y1, z0, z1 in sb_lanes(): _rect(e, (y0 + y1)/2, (z0 + z1)/2, y1 - y0, z1 - z0, 'BCU_FRAME_BARS')
    for y, z, l in sb_slots().values():                                   # plated slots (finished size) and their pads
        _rect(e, y, z, l, SB_SLOT_W, 'TAB_SLOTS'); _rect(e, y, z, l + 2*SB_SLOT_RING, SB_SLOT_W + 2*SB_SLOT_RING, 'TAB_SLOT_PADS')
    for y0, y1, z0, z1 in sb_tail_runs(): _rect(e, (y0 + y1)/2, (z0 + z1)/2, y1 - y0, z1 - z0, 'BCU_TAIL_RUNS')   # nickel behind B.Cu
    for y, z, d in sb_pack_holes().values():                                # PACK wire holes (finished size) and their pads
        _circ(e, y, z, d/2, 'PACK_WIRE_HOLES'); _circ(e, y, z, d/2 + SB_PWIRE_RING, 'PACK_WIRE_PADS')
    for y0, y1, z0, z1 in sb_wire_runs(): _rect(e, (y0 + y1)/2, (z0 + z1)/2, y1 - y0, z1 - z0, 'BCU_WIRE_RUNS')   # wires behind B.Cu: no parts
    for y, z in SB_STANDOFFS: _rect(e, y, z, SB_STANDOFF_D, SB_STANDOFF_D, 'COVER_STANDOFFS')
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
    dy = np.abs(np.abs(y) - sb_pr)
    r = CELL_D / 2
    return np.where(dy < r, sb_xb0 - (sb_pr + np.sqrt(np.maximum(r*r - dy*dy, 0))), sb_xb0 - sb_pr)

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
    print("tab slots (KiCad x, y, length along x): " + ", ".join(f"{n} {kicad(y, z)[0]:.2f}, {kicad(y, z)[1]:.2f}, {l:.1f}"
          for n, (y, z, l) in sb_slots().items()) + f"; slot width {SB_SLOT_W}")
    print("PACK wire holes (KiCad x, y, finished dia): " + ", ".join(f"{n} {kicad(y, z)[0]:.2f}, {kicad(y, z)[1]:.2f}, {d}"
          for n, (y, z, d) in sb_pack_holes().items()) + f"; ring {SB_PWIRE_RING}")
    r = 6.99e-8 * 0.007 / (7 * SB_PACK_T * 1e-6) + 2.09e-2 * 0.015     # ~7 mm of 0.2 x 7 nickel pad + ~15 mm of 18 AWG
    print(f"PACK pad + 18 AWG wire: {r*1e3:.2f} mOhm, {9.4**2*r:.2f} W at 9.4 A per tab")
    ys = np.array([0, 2, 4, 6, 8, 15, 18, 21])
    print("inner-face free height vs y: " + ", ".join(f"{y:g}:{d:.1f}" for y, d in zip(ys, side_groove_depth(ys))))
    # assembly checks (positive = clearance)
    chk = {
        'port faces below the top wall while the board drops in': sb_z_top_in - (SB_H - SB_SLIDE),
        'board bottom above the floor while it drops in': sb_zb0 - SB_SLIDE - SB_END_T,
        'port hole to the cover slot (x)': sb_x_cv0 - (sb_port_x + (USB_SEAL_H + 0.2)/2),
        'USB-C body to the cover (x)': sb_x_cv0 - (sb_port_x + USB_UP),
        'seal ring (0.5-1.5 behind the face) inside the top wall': SB_END_T - 1.5,
        'cover top edge under the lip': sb_cover_z1 - sb_z_top_in,
        'wedge bosses clear of the cells (x: the bosses sit in the board zone)': (sb_x_cv0 - SB_INSERT_L - 1.5) - (sb_pr + CELL_D/2),
        'wedge bosses below the board notches (z, after the lift)': sb_notch_z - sb_z_pil - SB_PCB_CLEAR,
        'board fits the wider cavity (y, per side)': a_cav - sb_board_w/2 - 0.3,
        'cage: cells kept apart by the web (gap - web)': (2*sb_pr - CELL_D) - SB_CAGE_WEB - 2*SB_CAGE_CLR + 1e-9,
        'cage: spine fits the centre void': (sb_pr*np.sqrt(2) - CELL_D/2) - SB_CAGE_SPINE_D/2 - 0.3,
        'cage: three bands fit the cell length': CELL_L - 2*SB_CAGE_END - 3*SB_CAGE_BAND - 2*5.0,
        'snap ridge under the ring carrier, clear of the wedge nose (x)': (SB_SNAP[0] - SB_SNAP[1]/2) - (-(a_cav - RIB_DEPTH) + 0.2 + SB_WEDGE_NOSE[0]) - 1.0,
        'board top stops: board edge to the top wall (stop height)': sb_z_top_in - sb_zb1,
        'board stops clear of the port holes (y)': SB_STOP_Y0 - (SB_PORT_Y + (USB_SEAL_W + 0.2)/2),
        'hold-down pad compressed (pad - gap)': SB_HOLD_T - (sb_x_cv0 - (sb_port_x + USB_UP)),
        'port well clear of the seal holes (y)': SB_WELL_W/2 - (SB_PORT_Y + (USB_SEAL_W + 0.2)/2),
        'port well: cap wall to the +x edge beyond 2 mm (x)':SB_CAP_OUT[1] - (sb_port_x + SB_WELL_H/2) - 2.0,
        'cap band clear of the cover vent (z)': (SB_VENT_Z - SB_VENT_D/2) - SB_CAP_BAND,
        'crush ribs bear on the cells (rib - air gap)': SB_CRUSH_H - (a_cav - SB_SIDE_PAD - (sb_pr + CELL_D/2)),
        'cover thermal clearance, length (gaps - growth)': 2*SB_COVER_GAP - (sb_cover_z1 - sb_cover_z0) * (100e-6 - 23e-6) * 60,
        'cover thermal clearance, width (gaps - growth)': 2*SB_COVER_GAP - sb_cover_w * (100e-6 - 23e-6) * 60,
        'cover still under the top-wall lip (z)': sb_cover_z1 - sb_z_top_in - 0.5,
        'cap groove leaves wall (>= 0.8)': WALL - SB_GROOVE_D - 0.8,
        'cap groove clear of the insert pilots (y)': (a_sb - SB_GROOVE_D) - (sb_pillar_y + SB_INSERT_D/2) - 1.0,
        'drain channel: cap wall beside it (x)': SB_CAP_OUT[1] - (sb_port_x + SB_WELL_H/2) - 1.0,
        'standoffs: 0.1 below the cover': (sb_x_cv0 - sb_xb1) - sb_standoff_h - 0.1 + 0.1,
        'standoffs clear of the top slots (z)': min(abs(z - SB_TAIL_TOP_Z) for _, z in SB_STANDOFFS) - SB_STANDOFF_D/2 - 1.0,
        'standoffs clear of the vent keep-out': min(np.hypot(y, z - SB_VENT_Z) for y, z in SB_STANDOFFS) - (SB_VENT_D/2 + 2 + SB_STANDOFF_D/2),
        'frame bars clear of the BLE module (y)': sb_ant_y[0] - SB_BAR_Y[1] - 0.3,
        'frame bars bear on the cans (can surface at the bar end <= 0.05 below the tangent)':
            0.05 - (CELL_D/2 - float(np.sqrt((CELL_D/2)**2 - max(sb_pr - SB_BAR_Y[1], 0)**2))),
        'top plate meets the JLC TPU minimum wall': SB_TOP_PAD - 1.2,
        'module drop, resting on its ring carrier: port faces under the top wall': sb_z_top_in - (SB_H - (SB_WEDGE_T - SB_AXIAL_PRELOAD)),
        'wedge nose lifts more than the preload': SB_WEDGE_NOSE[1] - SB_AXIAL_PRELOAD - 0.3,
        'ring carrier: ring height >= 1.0 over the wedge': sb_z_pad1 - (SB_END_T + SB_WEDGE_T) - SB_FRAME_BASE - 1.0,
        'wedge under the board edge reaches it (shim job)': sb_zb0 - (SB_END_T + SB_WEDGE_T),
        'wedge trapped by the cover (cover reaches below the wedge top, z)': (SB_END_T + SB_WEDGE_T) - sb_cover_z0 - 1.0,
        'slots: pads above the board bottom edge (z)': min(z for _, z, _ in sb_slots().values()) - SB_SLOT_W/2 - SB_SLOT_RING - sb_zb0 - 0.5,
        'slots: pads clear of the corner notches (y)': sb_notch_y - max(abs(y) + l/2 + SB_SLOT_RING for y, _, l in sb_slots().values()) - 0.5,
        'slots: pads between each other (y, >= 0.4)': min(abs(a[0] - b[0]) - (a[2] + b[2])/2 - 2*SB_SLOT_RING
                                                       for i, a in enumerate(sb_slots().values()) for b in list(sb_slots().values())[i+1:] if abs(a[1] - b[1]) < 2) - 0.4,
        'PACK wire holes: pads above the board bottom edge (z, >= 0.1)': min(z - d/2 for _, z, d in sb_pack_holes().values()) - SB_PWIRE_RING - sb_zb0 - 0.1,
        'PACK wire holes: pads clear of the corner notches (y)': sb_notch_y - max(abs(y) + d/2 for y, _, d in sb_pack_holes().values()) - SB_PWIRE_RING - 0.5,
        'PACK wire holes: pads clear of the Kelvin slot pads (y, >= 0.4)': min(abs(abs(y) - abs(sb_slots()[k][0])) - d/2 - SB_PWIRE_RING - sb_slots()[k][2]/2 - SB_SLOT_RING
                                                       for y, _, d in sb_pack_holes().values() for k in ('1N', '4P')) - 0.4,
        'PACK wire holes below the frame bars (z)': SB_BAR_Z0 - (SB_PWIRE_Z + SB_PWIRE_HOLE/2 + SB_PWIRE_RING) - 0.3,
        'bottom slots below the frame bars (z)': SB_BAR_Z0 - (sb_z_tail_b + SB_SLOT_W/2 + SB_SLOT_RING) - 0.3,
        'bottom slots clear of the vent keep-out': min(np.hypot(y, z - SB_VENT_Z) for y, z, _ in sb_slots().values()) - SB_SLOT_W/2 - SB_SLOT_RING - (SB_VENT_D/2 + 2),
        'top tails outside the frame bars (y)': (SB_TAIL_Y - SB_TAIL_W/2) - SB_BAR_Y[1] - 0.5,
        'top tails clear of the USB-C notches (y)': (SB_TAIL_Y - SB_TAIL_W/2) - (SB_PORT_Y + 10.20/2) - 0.5,
        'top tails overlap their series strip by >= 2 mm (y)': (sb_pr + SB_TAB_W/2) - (SB_TAIL_Y - SB_TAIL_W/2) - 2.0,
        'top tails inside the board edge (y)': sb_board_w/2 - (SB_TAIL_Y + SB_TAIL_W/2 + SB_SLOT_CLR/2 + SB_SLOT_RING) - 1.0,
        'top slots clear of the BLE module (z)': (SB_TAIL_TOP_Z - SB_SLOT_W/2 - SB_SLOT_RING) - (sb_ant_zc + SB_ANT_MOD[0]/2) - 1.0,
        'top tails: room behind the board, past the cans (x)': (sb_xb0 - 1.3) - (sb_pr + float(np.sqrt((CELL_D/2)**2 - (SB_TAIL_Y - SB_TAIL_W/2 - sb_pr)**2))) - 0.5,
        'kink inside the gap behind the board (x)': min(SB_KINK[0] - (sb_ac + 0.2), sb_xb0 - SB_KINK[1]) - 0.2,
        'kink above the wedge (z)': (sb_z_tail_b - SB_PACK_T - SB_KINK[2]) - sb_zb0 - 0.3,
        'CELL2 tail in the channel between the rings (y)': 2*(sb_pr - SB_RING_OD/2) - SB_TAIL_W - 1.0,
        'Kelvin fingers clear of the CELL2 tail (y)': min(abs(y) - l/2 for n, (y, _, l) in sb_slots().items() if n in ('1N', '4P')) - (SB_TAIL_W/2 + SB_SLOT_CLR/2) - 2.0,
        'spring rings clear the + cap cut-out': SB_RING_ID - SB_VENT_CUT_D,
        'spring ring wall >= 1.2': (SB_RING_OD - SB_RING_ID)/2 - 1.2,
        'BLE module on B.Cu: room behind it to the fish paper (min over its span)':
            float(np.min(side_groove_depth(np.linspace(*sb_ant_y, 41)))) - SB_INSUL - SB_ANT_H,
        'standoffs clear of the BLE module (z, >= 5 mm)': min(abs(z - sb_ant_zc) - SB_ANT_MOD[0]/2 - SB_STANDOFF_D/2 for y, z in SB_STANDOFFS if y * SB_ANT_SIDE > 0) - 5.0,
        'BLE module: ground along the edge above it (>= 10)': sb_zb1 - (sb_ant_zc + SB_ANT_MOD[0]/2) - 10.0,
        'BLE module 10 mm below the USB-C bodies (z)': (sb_zb1 + USB_FACE_OUT - USB_DEPTH) - (sb_ant_zc + SB_ANT_MOD[0]/2) - 10.0,
    }
    for k, v in chk.items(): print(f"  {'ok ' if v >= 0 else 'BAD'} {v:6.2f}  {k}")
