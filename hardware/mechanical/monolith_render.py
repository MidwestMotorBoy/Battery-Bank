"""Monolith layout comparison: top-cap board vs side board (numpy + PIL; imports the generators).
Run after monolith_shell.py and monolith_parts.py:  python3 monolith_render.py
-> monolith_layout_compare.png, plus a size / mass table on stdout.
Masses: printed parts from STL volume x density; cells 75 g each (FEB 21700G listing; Batemo measures 73.4 g);
boards estimated at the production thickness (SB_PCB_T) as FR4 + 6-layer copper (2 oz outer, 0.5 oz inner) at 70 % fill."""
import numpy as np, struct, os
from PIL import Image, ImageDraw, ImageFont
import monolith_shell as S, monolith_parts as P

HERE = os.path.dirname(os.path.abspath(__file__))
CELL_G = 75.0          # FEB 21700G (was 71 g, EVE 58E)
FR4_RHO, CU_RHO, CU_T, CU_FILL = 1.85, 8.96, 2*0.070 + 4*0.0175, 0.70
PX = 5.0                        # pixels per mm, same for every view

def board_g(area_mm2, t=0.8):
    cu = area_mm2 * CU_T * CU_FILL
    return (area_mm2 * t - cu) / 1000 * FR4_RHO + cu / 1000 * CU_RHO

def load(name):
    with open(os.path.join(HERE, name + '.stl'), 'rb') as f:
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

if __name__ == '__main__':
    top, (tz0, tz1) = top_assembly(); side, (sz0, sz1) = side_assembly()
    rho = dict(shell=1.18, cap=1.20, bump=1.21, plate=2.70)
    def g(asm, key, r): return sum(vol(V) for n, V, *_ in asm if n == key) * r
    top_board_a = 45.5**2 - (4 - np.pi)*9.35**2          # production outline, Production/README.md
    rows = {
        'top cap (today)': dict(
            w=2*S.a_out + 2*(P.BUMP_WALL - P.BUMP_SQUEEZE), d=2*S.a_out + 2*(P.BUMP_WALL - P.BUMP_SQUEEZE), l=tz1 - tz0,
            shell=g(top, 'shell', rho['shell']), cap=g(top, 'top cap', rho['cap']), bump=g(top, 'bumper', rho['bump']),
            board=board_g(top_board_a, S.SB_PCB_T), extra=g(top, 'bottom pcb', FR4_RHO),
            plate=P.PLATE_L*P.PLATE_W*P.PLATE_T/1000*rho['plate'], area=top_board_a),
        'side board': dict(
            w=S.sb_x_out + S.a_sb + 2*S.SB_CAP_PROUD, d=2*(S.a_sb + S.SB_CAP_PROUD), l=sz1 - sz0,
            shell=g(side, 'shell', rho['shell']), cap=0.0, bump=P.cap_mass(False) + P.cap_mass(True),
            board=board_g(S.sb_board_area, S.SB_PCB_T), extra=0.0,
            plate=g(side, 'cover', rho['plate']), area=S.sb_board_area)}
    lines = []
    hdr = f"{'':18s}{'outside (mm)':>22s}{'box cm3':>9s}{'board mm2/side':>16s}{'shell':>7s}{'cap/lid':>8s}{'bumpers':>8s}{'end pcb':>8s}{'Al':>9s}{'board':>7s}{'cells':>7s}{'total g':>9s}"
    print(hdr); lines.append(hdr)
    for k, r in rows.items():
        tot = r['shell'] + r['cap'] + r['bump'] + r['extra'] + r['plate'] + r['board'] + 4*CELL_G
        r['tot'] = tot; r['box'] = r['w']*r['d']*r['l']/1000
        s = (f"{k:18s}{r['w']:7.1f} x{r['d']:5.1f} x{r['l']:6.1f}{r['box']:9.0f}{r['area']:16.0f}{r['shell']:7.1f}{r['cap']:8.1f}"
             f"{r['bump']:8.1f}{r['extra']:8.1f}{r['plate']:9.1f}{r['board']:7.1f}{4*CELL_G:7.0f}{tot:9.1f}")
        print(s); lines.append(s)

    # ---------------- picture: iso cutaway + end view for each layout ----------------
    W, Hh = 2040, 1060
    img = Image.new('RGB', (W, Hh), (255, 255, 255)); t = ImageDraw.Draw(img)
    f1, f2 = font(22), font(15)
    iso = camera((1.0, -1.25, 0.85)); end = camera((0, 0, 1), up=(0, 1, 0))
    for col, (title, asm, z0, z1, key, zt) in enumerate((('Top-cap board (today\'s model, 40.5 mm board)', top, tz0, tz1, 'top cap (today)', None),
                                                        ('Side board, one-piece tray, TPU crush caps', side, sz0, sz1, 'side board', S.sb_z_top_in))):
        x0 = 30 + col*700; r = rows[key]
        t.text((x0, 18), title, fill=(20, 20, 20), font=f1)
        draw(img, panel_parts(asm, True), iso, (x0 + 260, 560))
        draw(img, panel_parts(asm, False, zt), end, (x0 + 470, 760))
        t.text((x0 + 380, 900), "end view from the port end, top removed", fill=(90, 90, 90), font=f2)
        for i, s in enumerate((f"outside {r['w']:.1f} x {r['d']:.1f} x {r['l']:.1f} mm (with bumpers), box {r['box']:.0f} cm3",
                               f"board area {r['area']:.0f} mm2 per side",
                               f"enclosure + board {r['tot'] - 4*CELL_G:.1f} g, pack {r['tot']:.0f} g")):
            t.text((x0, 940 + 22*i), s, fill=(20, 20, 20), font=f2)
    x0 = 1430
    t.text((x0, 18), 'Tray with the cover off', fill=(20, 20, 20), font=f1)
    tray = [(V, c) for n, V, c, *_ in side if n in ('shell', 'side board')]
    draw(img, tray, camera((1.0, -0.55, 0.45)), (x0 + 230, 520))
    for i, s_ in enumerate(("Opening on the board side only. Top-wall lip holds",
                            "the cover's top edge; two M2 inserts in the bottom",
                            "corner pillars. Board slides +z to seat the ports.")):
        t.text((x0, 940 + 22*i), s_, fill=(20, 20, 20), font=f2)
    t.text((30, Hh - 28), "Blue: cells. Green: boards and USB-C envelopes. Light grey: shell (front half cut away). "
           "Dark: TPU bumpers / crush caps (lattice, mass at print fill). Silver: aluminium cover (Al plate on the top-cap layout is not drawn).", fill=(90, 90, 90), font=f2)
    img.save(os.path.join(HERE, 'monolith_layout_compare.png'))
    print("wrote monolith_layout_compare.png")
