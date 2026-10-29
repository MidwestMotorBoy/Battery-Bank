"""Mesh and mass helpers (numpy + PIL): camera, draw, vol, board_g, CELL_G, used by monolith_cup.py,
monolith_cup_assembly_steps.py and monolith_side_renders.py. The top-cap vs side-tray comparison render that used to
run from here (retired/monolith_layout_compare.png) was removed on 2026-10-29; it is in git history (Production 5cf521e).
Masses: printed parts from STL volume x density; cells 75 g each (FEB 21700G listing; Batemo measures 73.4 g);
boards estimated at the production thickness (SB_PCB_T) as FR4 + 6-layer copper (2 oz outer, 0.5 oz inner) at 70 % fill."""
import numpy as np, struct, os
from PIL import Image, ImageDraw, ImageFont
import monolith_shell as S, monolith_parts as P

HERE = os.path.dirname(os.path.abspath(__file__))
CELL_G = 75.0          # BAK N21700CX-65E, <= 75 g per the spec (same as the FEB 21700G; EVE 58E was 71 g)
FR4_RHO, CU_RHO, CU_T, CU_FILL = 1.85, 8.96, 2*0.070 + 4*0.0175, 0.70
PX = 5.0                        # pixels per mm, same for every view

def board_g(area_mm2, t=0.8):
    cu = area_mm2 * CU_T * CU_FILL
    return (area_mm2 * t - cu) / 1000 * FR4_RHO + cu / 1000 * CU_RHO

def load(name):
    with open(os.path.join(S.RETIRED, name + '.stl'), 'rb') as f:
        f.read(80); n = struct.unpack('<I', f.read(4))[0]
        d = np.frombuffer(f.read(50*n), dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    return d['v'].reshape(-1, 3, 3).astype(float)
def vol(V): return abs(np.einsum('ij,ij->i', V[:,0], np.cross(V[:,1], V[:,2])).sum()) / 6000
def moved(V, dx=0, dy=0, dz=0, flip_z=None):
    V = V.copy()
    if flip_z is not None: V[..., 2] = flip_z - V[..., 2]
    return V + [dx, dy, dz]

# ---------------- assemblies: (name, triangles, colour, cut-away in the iso view, shown in end view) ----------------
SHELL, CAP, CELL, BOARD, BUMP, PLATE = (200, 200, 196), (150, 150, 146), (90, 150, 200), (60, 150, 90), (70, 70, 70), (215, 215, 225)
def top_assembly():
    cell = load('monolith_cell_dummy'); a = []
    a.append(('shell', load('monolith_shell'), SHELL, True, True))
    for sx in (-1, 1):
        for sy in (-1, 1): a.append(('cell', moved(cell, sx*S.pocket_r, sy*S.pocket_r, S.z_rib0 + S.TAB_T), CELL, False, True))
    a.append(('bottom pcb', moved(load('monolith_bottom_pcb_dummy'), dz=S.PCB_RECESS), BOARD, False, False))
    a.append(('top board', moved(load('monolith_top_board_dummy'), dz=S.H + P.z_bb), BOARD, False, True))
    a.append(('top cap', moved(load('monolith_top_cap'), dz=S.H), CAP, True, False))
    bump = load('monolith_end_bumper'); top = S.H + P.z_face_top + P.BUMP_LIP_T
    a.append(('bumper', moved(bump, dz=-P.BUMP_LIP_T), BUMP, True, False))
    a.append(('bumper', moved(bump, flip_z=top), BUMP, True, False))
    return a, (-P.BUMP_LIP_T, top)
def side_assembly():
    cell = load('monolith_cell_dummy'); a = []
    a.append(('shell', load('monolith_side_shell'), SHELL, True, True))
    for sx in (-1, 1):
        for sy in (-1, 1): a.append(('cell', moved(cell, sx*S.pocket_r, sy*S.pocket_r, S.sb_z_cell0), CELL, False, True))
    a.append(('side board', load('monolith_side_board_dummy'), BOARD, False, True))
    a.append(('cover', load('monolith_side_cover'), PLATE, True, True))
    a.append(('bumper', load('monolith_side_cap_bottom'), BUMP, True, False))
    a.append(('bumper', moved(load('monolith_side_cap_top'), flip_z=S.SB_H), BUMP, True, False))
    return a, (-S.SB_CAP_T, S.SB_H + S.SB_CAP_T)

# ---------------- flat-shaded painter's renderer ----------------
def camera(d, up=(0, 0, 1)):
    d = np.array(d, float); d /= np.linalg.norm(d)
    r = np.cross(up, d); r /= np.linalg.norm(r); u = np.cross(d, r)
    return np.array([r, u, d])
def draw(img, parts, R, origin, light=(0.4, -0.5, 0.75)):
    L = np.array(light) / np.linalg.norm(light); tris, cols = [], []
    for V, c in parts:
        n = np.cross(V[:,1]-V[:,0], V[:,2]-V[:,0]); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:,None]
        k = 0.45 + 0.55*np.abs(n @ L)
        tris.append(V @ R.T); cols.append((np.array(c)[None,:]*k[:,None]).astype(int))
    T = np.vstack(tris); C = np.vstack(cols)
    order = np.argsort(T[:,:,2].mean(1))
    g = ImageDraw.Draw(img); ox, oy = origin
    for i in order:
        p = T[i]; g.polygon([(ox + PX*x, oy - PX*y) for x, y in p[:, :2]], fill=tuple(C[i]))

def panel_parts(asm, iso, z_top=None):
    out = []
    for name, V, c, cut, end in asm:
        if iso:
            if cut: V = V[V[:,:,1].mean(1) > 0]       # cut away the -y half of the shell, caps and bumpers
        elif not end: continue
        elif z_top is not None and name == 'shell':
            V = V[V[:,:,2].min(1) < z_top - 0.01]     # drop the closed top wall so the end view sees inside
        out.append((V, c))
    return out

def font(sz):
    for f in ('arial.ttf', 'DejaVuSans.ttf'):
        try: return ImageFont.truetype(f, sz)
        except OSError: pass
    return ImageFont.load_default()
