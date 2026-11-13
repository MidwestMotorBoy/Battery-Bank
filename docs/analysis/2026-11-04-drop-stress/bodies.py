"""Separate bodies for the contact drop model (2026-11-04), as manifold3d solids in the pack frame (x toward the board
face, y across, z along the cells, port end up), built from hardware/mechanical/monolith_cup.py.

Moving bodies: the four cells (each with its nickel / fish paper stack as an axial extension), the carrier, the four
rail blocks with their posts (one body: the board's pegs tie them together), and the board (PCB, part hulls, BLE module,
and the four post spacers). The spacers are gripped on the posts by crush ribs and sit on F.Cu, so they ride with the
posts across the board (friction only against F.Cu) but go with the board toward the board-face wall: they belong to the
board only against the cup walls (m_wall). The shell is everything that
meets the floor: the cup, the cap, the screws and O-ring, the bumpers and the label. For contact attribution the shell
is split into sub-parts: cup walls, cradles, edge lands, F.Cu lips, the cap (plate + skirt), its overtravel posts,
its board feet, and the TPU pad (a soft law, not rigid).

The crush ribs (rail tongues, spacer bores) are left off: they are bench friction, they give way in a drop."""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
MECH = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'hardware', 'mechanical'))
_cwd = os.getcwd(); sys.path.insert(0, MECH); os.chdir(MECH)
import manifold3d as M3
import monolith_cup as K, monolith_shell as S, monolith_parts as P
# This study ran on the hand-routed board, whose part meshes are kept as board/monolith_board_handrouted.npz.
# board/monolith_board.npz is the script-built board since 2026-11-13: set BOARD_NPZ to it to run on that board.
P.BOARD_NPZ = os.environ.get('BOARD_NPZ', os.path.join(MECH, 'board', 'monolith_board_handrouted.npz'))
os.chdir(_cwd)
MF, CS = M3.Manifold, M3.CrossSection

def mesh_manifold(T, tol=1e-4):
    """triangle soup (n, 3, 3) -> Manifold (vertices merged)"""
    V = np.asarray(T, float).reshape(-1, 3); q = np.round(V / tol).astype(np.int64)
    _, idx, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    return MF(M3.Mesh(vert_properties=V[idx].astype(np.float32), tri_verts=inv.reshape(-1, 3).astype(np.uint32)))

def slab_hulls(T, dz=0.25):
    """a non-convex part (the USB-C receptacles: housing, shell, mid-mount tabs) as the union of the hulls of 0.25 mm
    slabs along z (its section is convex, its profile along the port axis is not)"""
    T = np.asarray(T, float).reshape(-1, 3, 3); V = T.reshape(-1, 3)
    out = []
    for z in np.arange(V[:, 2].min(), V[:, 2].max(), dz):
        z1 = min(z + dz, V[:, 2].max())
        pts = [V[(V[:, 2] >= z) & (V[:, 2] <= z1)]] + [K.slice_pts(T, zz) for zz in (z + 1e-4, z1 - 1e-4)]
        pts = np.vstack([p.reshape(-1, 3) for p in pts if len(p)])
        if len(pts) < 4: continue
        pts[:, 2] = np.clip(pts[:, 2], z, z1)
        out.append(MF.hull_points(np.vstack([pts, pts + [0, 0, 0]])))
    return K.U(*out)

USB_SHELL = (8.94, 3.26)            # USB-C receptacle metal shell, outside (spec); the seal ring sits on it
def usb_part(T, py):
    """receptacle as slab hulls, with the silicone seal ring's band (USB_RING_D from the face) cut back to the metal
    shell: the ring is squeezed 0.15 into its bore and is far softer than PA12, so it is not a rigid contact"""
    m = slab_hulls(T)
    z0, z1 = K.Z_TOP1 - S.USB_RING_D[1] - 0.06, K.Z_TOP1 - S.USB_RING_D[0] + 0.06   # (+ the slab overhang)
    band = MF.cube((20, 30, z1 - z0)).translate((15, py - 15, z0))
    w, h = USB_SHELL
    shell = K.pz(K.rrect(K.PORT_X - h/2, K.PORT_X + h/2, py - w/2, py + w/2, h/2 - 1e-3), z0, z1)
    return (m - band) + (m ^ shell)

def spacers_plain():
    """the post spacers without their crush ribs: a Ø4 tube, bore SPACER_CLR round the post"""
    out = []
    for y, z in S.CUP_PEGS:
        sec = CS.batch_boolean([K.circ(y, z, K.SPACER_R), K.post_cs(y, z, K.SPACER_CLR)], M3.OpType.Subtract)
        out.append(K.px_(sec, S.sb_xb1, S.sb_xb1 + K.SPACER_H))
    return K.U(*out)

def rails_plain():
    """rail blocks + posts + tongues, no crush ribs"""
    keep = K.key_ribs
    K.key_ribs = lambda: []
    try: return K.rails()
    finally: K.key_ribs = keep

RAILS = ('rails_tp', 'rails_tn', 'rails_bp', 'rails_bn')      # top / bottom block, +y / -y
def rail_blocks(mass):
    """the four clip-on blocks as separate bodies (only the board's pegs and the carrier's key slots tie them)"""
    out = {}
    for c in rails_plain().decompose():
        b = c.bounding_box(); zc, yc = (b[2] + b[5]) / 2, (b[1] + b[4]) / 2
        out['rails_' + ('t' if zc > 40 else 'b') + ('p' if yc > 0 else 'n')] = dict(m=c, mass=mass * c.volume() / 1131.4)
    assert sorted(out) == sorted(RAILS), out.keys()
    return out

def box(x0, x1, y0, y1, z0, z1): return MF.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))
def nickel_boxes():
    """the nickel as monolith_parts.nickel_strips(pack='wire') builds it: three series strips, the two PACK pads (in the
    C1 / C4 bottom weld windows) and the CELL1 / CELL3 top tongues"""
    t, hw, pr = S.SB_TAB_T, S.SB_TAB_W / 2, S.sb_pr; zt0, zb1 = S.sb_z_tail_t, S.sb_z_tail_b
    out = [box(-pr, pr, -pr - hw, -pr + hw, zt0, zt0 + t), box(-pr, pr, pr - hw, pr + hw, zt0, zt0 + t),
           box(-pr - hw, -pr + hw, -pr, pr, zb1 - t, zb1)]
    for n, yc in S.sb_tab_y.items():
        out.append(box(pr - S.SB_TAB_W / 2, pr - S.SB_TAB_W / 2 + P.PACK_PAD_L, yc - hw, yc + hw, zb1 - S.SB_PACK_T, zb1))
    for sy in (-1, 1):
        yc, w = sy * S.SB_TAIL_Y, S.SB_TAIL_W / 2
        out.append(box(S.sb_pr - 0.01, S.SB_TONGUE_X, yc - w, yc + w, zt0, zt0 + t))
    return K.U(*out)

def cup_parts():
    """the cup split for attribution: walls (everything but the 2026-11-03 ribs), cradles, edge lands, F.Cu lips"""
    cup = K.cup(); clip = K.pz(K.cs_in.offset(0.02, K.ROUND), K.Z_MOUTH - 1, K.Z_TOP0 + 0.02)
    cr = K.cradles() ^ clip
    ll = K.lands() ^ clip
    xlip0 = S.sb_xb1 + K.FCU_LIP[0] - 0.01
    lip = ll ^ MF.cube((5, 60, 120)).translate((xlip0, -30, -20))
    lip = lip ^ MF.cube((K.FCU_LIP[1] + 0.02, 60, 120)).translate((xlip0, -30, -20))
    land = ll - lip
    walls = cup - cr - ll
    return dict(cup_walls=walls, cradles=cr, lands=land, lips=lip)

def cap_parts():
    cap = K.cap()
    posts = K.U(*[K.pz(K.circ(x, y, K.OT_R), K.Z_MOUTH - 0.01, K.FR_B0 - K.OT_GAP) for x, y in K.OT_POSTS]) ^ cap
    feet = K.board_feet() ^ cap
    return dict(cap=cap - posts - feet, ot_posts=posts, feet=feet)

def build():
    """returns bodies {name: dict(m=Manifold or None, mass=g)}, shell sub-parts {name: Manifold}, masses, params"""
    # (as the 10-31 drop study: the vent grille spans its pocket and bends into it, so it is no floor column)
    K.vent_grille = lambda: K.circ(*K.VENT_XY, K.VENT_POCKET_R + 0.2) - K.circ(*K.VENT_XY, K.VENT_POCKET_R)
    A = K.assembly(); m = K.masses(A)
    cells = {}
    # each cell: its can plus the nickel on its own quadrant (a strip between two cells is split between them), so the
    # frames bear on the strips where they cross frame material and on the can rims 0.4-0.45 mm further on
    ni = nickel_boxes()
    names = {v[0]: k for k, v in S.SB_CELLS.items()}
    # cell mass: 75 g + a quarter of nickel, tails, wires, fish paper, foam, + half the gel filler on each front cell
    extra = (m['nickel'] + m['tails'] + m['insul'] + m['foam']) / 4
    for nm in ('C1', 'C2', 'C3', 'C4'):
        x, y = S.sb_cell_xy[names[nm]]
        sx, sy = np.sign(x), np.sign(y)             # (the split strip halves stop 1 mm short of the split: no fake can-to-can stop)
        quad = box(min(sx, 40 * sx), max(sx, 40 * sx), min(sy, 40 * sy), max(sy, 40 * sy), -20, 120)
        can = K.pz(K.circ(x, y, K.CR), S.sb_z_cell0, S.sb_z_cell1)
        cells[nm] = dict(m=can + (ni ^ quad), mass=K.CELL_G + extra + (m['filler'] / 4 if x > 0 else 0.0), xy=(x, y))
    B = P.real_board()
    refs = [k for k in B if not k.startswith('_') and k != 'PCB' and k not in P.BENCH_ONLY
            and not str(B['_model_' + k]).startswith(('Peg_', 'SolderWire'))]
    usb_y = dict(J401=K.PORT_YS[1], J501=K.PORT_YS[0])
    hulls = [usb_part(B[k], usb_y[k]) if k in usb_y else MF.hull_points(B[k].reshape(-1, 3)) for k in refs]
    pcb = mesh_manifold(B['PCB'])                # KiCad's board body is the 1.46 mm laminate; the parts sit on the
    pcb = pcb + pcb.translate((S.sb_xb1 - pcb.bounding_box()[3], 0, 0))   # finished 1.6 mm surface (26.9): fill it out
    # the receptacles' pins reach 0.03 under B.Cu over the top blocks: trim them to B.Cu there (not a contact)
    trim = K.U(*[MF.cube((2, 8.0, 23.1)).translate((S.sb_xb0 - 2, s * 5.0 - (8.0 if s < 0 else 0), 55.0)) for s in (-1, 1)])
    usb_m = K.U(*[h for k, h in zip(refs, hulls) if k in usb_y]) - trim
    parts_m = K.U(*[h for k, h in zip(refs, hulls) if k not in usb_y]) - trim
    board_m = K.U(pcb, usb_m, parts_m)
    sp = spacers_plain()
    bodies = dict(**cells,
                  carrier=dict(m=K.carrier(), mass=m['carrier']),
                  **rail_blocks(m['rails']),
                  board=dict(m=board_m, m_wall=board_m + sp, spacers=sp, usb=usb_m, parts=parts_m, mass=m['board'] + m['spacer'] + m['filler'] / 2, pcb=pcb))
    shell_keys = ('cup', 'cap', 'label', 'bumpb', 'bumpt', 'screw', 'oring', 'pad', 'vent')
    bodies['shell'] = dict(m=None, mass=sum(m[k] for k in shell_keys))
    sub = dict(**cup_parts(), **cap_parts(), pad=K.pad())
    prm = dict(X_IN=K.X_IN, YI=K.YI, Z_TOP0=K.Z_TOP0, Z_TOP1=K.Z_TOP1, Z_MOUTH=K.Z_MOUTH, FR_B0=K.FR_B0, FR_T1=K.FR_T1,
               OT_GAP=K.OT_GAP, OT_R=K.OT_R, OT_POSTS=K.OT_POSTS, PAD_FILL=K.PAD_FILL, PAD_PROUD=K.PAD_PROUD, CR=K.CR, PR=K.PR,
               sb_xb0=S.sb_xb0, sb_xb1=S.sb_xb1, sb_zb0=S.sb_zb0, sb_zb1=S.sb_zb1, PCB_T=S.SB_PCB_T, CELLS=K.CELLS,
               SPACER_R=K.SPACER_R, SPACER_H=K.SPACER_H, SPACER_GAP=K.SPACER_GAP, POST_W=K.POST_W, PEG_D=S.CUP_PEG_D,
               PEGS=S.CUP_PEGS, FOOT_Y=K.FOOT_Y, FOOT_GAP=K.FOOT_GAP, LAND_GAP=K.LAND_GAP, LAND_Z=K.LAND_Z, FCU_LIP=K.FCU_LIP,
               CRADLE_GAP=K.CRADLE_GAP, POST_GAP=K.POST_GAP, WALL=K.WALL, WALL_BF=K.WALL_BF, MOUTH_T=K.MOUTH_T, CAP_T=K.CAP_T,
               SCREW=dict(X=K.SCREW_X, Z=K.SCREW_Z, hole_r=K.SCREW_HOLE_R, pilot_r=K.PILOT_R, L=K.SCREW_L, head=K.SCREW_HEAD,
                          cbore=K.SCREW_CBORE, boss_depth=K.BOSS_DEPTH, pilot_solid=K.PILOT_SOLID),
               FR_T0=K.FR_T0, FR_B1=K.FR_B1, KEY_Y=K.KEY_Y, KEY_DEPTH=K.KEY_DEPTH, KEY_CLR=K.KEY_CLR, RAIL_X0=K.RAIL_X0,
               SKIRT_T=K.SKIRT_T, GROOVE_D=K.GROOVE_D, ORING_CS=K.ORING_CS, SLOT=S.CUP_PEG_SLOT, mass_total=sum(m.values()))
    return bodies, sub, m, prm, A

def contact_parts(B, sub):
    """labelled contact surfaces: name -> (body, solid). The carrier and the rail blocks are split into their frame-end
    zones (axial contacts with the cells: frames, tongues) and the rest; the board into the PCB, the USB-C receptacles,
    the other parts and the spacers (the spacers only meet the cup walls)"""
    ends = K.U(K.pz(K.rect(-40, 40, -40, 40), K.FR_B0 - 0.01, K.FR_B1 + 0.01), K.pz(K.rect(-40, 40, -40, 40), K.FR_T0 - 0.01, K.FR_T1 + 0.01))
    posts = MF.cube((10, 60, 120)).translate((S.sb_xb0 - 0.51, -30, -20))
    ca, bo = B['carrier']['m'], B['board']
    P = {k: (k, B[k]['m']) for k in ('C1', 'C2', 'C3', 'C4')}
    P.update({'carrier/frames': ('carrier', ca ^ ends), 'carrier/webs': ('carrier', ca - ends),
              'board/pcb': ('board', bo['pcb']), 'board/usb': ('board', bo['usb']), 'board/parts': ('board', bo['parts']),
              'board/spacers': ('board', bo['spacers'])})
    for r in RAILS:
        ra = B[r]['m']
        P.update({f'{r}/ends': (r, ra ^ ends), f'{r}/posts': (r, (ra - ends) ^ posts), f'{r}/blocks': (r, ra - ends - posts)})
    P.update({'shell/' + k: ('shell', v) for k, v in sub.items()})
    return {k: v for k, v in P.items() if not v[1].is_empty()}

if __name__ == '__main__':
    import time; t = time.time()
    bodies, sub, m, prm, A = build()
    for k, b in bodies.items():
        print(f"{k:8s} {b['mass']:7.2f} g", '' if b['m'] is None else f"vol {b['m'].volume():9.1f} mm3 status {b['m'].status()}")
    for k, s in sub.items(): print(f"  shell/{k:10s} vol {s.volume():9.1f}")
    print('total', round(sum(b['mass'] for b in bodies.values()), 1), 'g of', round(prm['mass_total'], 1), f'({time.time() - t:.1f} s)')
