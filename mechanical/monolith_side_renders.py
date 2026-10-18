"""Monolith side-tray drop-protection renders (numpy + scipy + PIL; builds the meshes from monolith_parts).
Run: python monolith_side_renders.py [v1_dir]
-> monolith_side_exploded.png  (assembled + exploded, every part named)
   monolith_side_sections.png  (A-A across the cells, B-B along C1/C2: the crush caps, pads, vents and board stops)
   monolith_side_parts.png     (cap zones, floor pad + rupture windows, mass and drop tables)
v1_dir (optional) holds the previous monolith_side_shell.stl and monolith_side_bumper.stl for the mass comparison.
Design basis: reports/Battery pack potting and drop protection.md (no potting; crush caps outside a stiff core)."""
import numpy as np, os, sys, struct
from PIL import Image, ImageDraw
import monolith_shell as S, monolith_parts as P
from monolith_render import camera, font, board_g, vol, CELL_G

HERE = os.path.dirname(os.path.abspath(__file__))
C = dict(shell=(205, 205, 200), cover=(200, 205, 222), board=(60, 150, 90), cell=(90, 140, 200), soft=(250, 205, 150),
         firm=(235, 150, 70), corner=(185, 85, 35), band=(125, 75, 50), poron=(225, 120, 170), wrap=(240, 170, 205),
         mica=(215, 185, 60), insul=(250, 230, 120), hold=(150, 110, 200), shim=(60, 170, 170))
INK, GREY = (25, 25, 25), (110, 110, 110)

def flipz(V, z0):
    V = V.copy(); V[..., 2] = z0 - V[..., 2]; return V[:, ::-1]
def mv(V, dx=0, dy=0, dz=0): return V + [dx, dy, dz]

# ---------------- the assembly, part by part: (key, label, mesh, colour) ----------------
def assembly():
    A = [('shell', 'printed tray', P.side_shell(), C['shell'])]
    cell = P.cell_solid()
    for k, (name, end) in S.SB_CELLS.items():
        x, y = S.sb_cell_xy[k]; A.append(('cell', name, mv(cell, x, y, S.sb_z_cell0), C['cell']))
    A += [('mica', 'mica cross', P.mica_cross(), C['mica']), ('wrap', 'side wrap', P.side_pad(), C['wrap']),
          ('pad_floor', 'floor pad', P.end_pad('bottom'), C['poron']), ('pad_top', 'top pad', P.end_pad('top'), C['poron']),
          ('insul', 'insulator', P.insulator(), C['insul']), ('board', 'board', P.side_board_dummy(), C['board']),
          ('shim', 'shim', P.board_shim(), C['shim']), ('hold', 'USB-C hold-down', P.hold_pads(), C['hold']),
          ('cover', 'Al cover', P.side_cover(), C['cover'])]
    for z in ('soft', 'firm', 'corner', 'band'):
        A.append(('capb_' + z, 'bottom cap', P.side_cap(z), C[z]))
        A.append(('capt_' + z, 'top cap', flipz(P.side_cap(z, True), S.SB_H), C[z]))
    return A

# ---------------- z-buffer renderer with outlines ----------------
LIGHT = np.array([0.35, -0.55, 0.75]); LIGHT = LIGHT / np.linalg.norm(LIGHT)
def render(img, parts, R, origin, px, outline=True):
    """parts: [(V, colour)]; R = camera rows (right, up, toward viewer); origin = screen position of the world origin"""
    W, H = img.size; ox, oy = origin
    zb = np.full((H, W), -np.inf); col = np.zeros((H, W, 3)); pid = np.full((H, W), -1)
    for ip, (V, c) in enumerate(parts):
        n = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
        sh = 0.42 + 0.58 * np.abs(n @ LIGHT)
        Q = V @ R.T; X = ox + px*Q[..., 0]; Y = oy - px*Q[..., 1]; Z = Q[..., 2]
        for t in range(len(V)):
            x, y, z = X[t], Y[t], Z[t]
            x0, x1 = max(int(np.floor(x.min())), 0), min(int(np.ceil(x.max())), W - 1)
            y0, y1 = max(int(np.floor(y.min())), 0), min(int(np.ceil(y.max())), H - 1)
            if x0 > x1 or y0 > y1: continue
            den = (y[1] - y[2])*(x[0] - x[2]) + (x[2] - x[1])*(y[0] - y[2])
            if abs(den) < 1e-9: continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            a = ((y[1] - y[2])*(gx - x[2]) + (x[2] - x[1])*(gy - y[2])) / den
            b = ((y[2] - y[0])*(gx - x[2]) + (x[0] - x[2])*(gy - y[2])) / den
            m = (a >= -1e-6) & (b >= -1e-6) & (a + b <= 1 + 1e-6)
            if not m.any(): continue
            d = a*z[0] + b*z[1] + (1 - a - b)*z[2]
            sub = zb[y0:y1 + 1, x0:x1 + 1]; w = m & (d > sub)
            sub[w] = d[w]
            col[y0:y1 + 1, x0:x1 + 1][w] = np.array(c) * sh[t]
            pid[y0:y1 + 1, x0:x1 + 1][w] = ip
    hit = pid >= 0
    base = np.asarray(img).astype(float); base[hit] = col[hit]
    if outline:   # dark where the part changes or the depth jumps
        e = np.zeros_like(hit)
        for dy, dx in ((0, 1), (1, 0)):
            p2 = np.roll(np.roll(pid, -dy, 0), -dx, 1); z2 = np.roll(np.roll(zb, -dy, 0), -dx, 1)
            with np.errstate(invalid='ignore'):
                e |= (pid != p2) | (np.abs(np.nan_to_num(zb - z2, posinf=99, neginf=99)) > 1.2)
        e &= hit | np.roll(hit, -1, 0) | np.roll(hit, -1, 1)
        base[e] = base[e] * 0.25
    img.paste(Image.fromarray(base.clip(0, 255).astype(np.uint8)))

def proj(R, origin, px):
    ox, oy = origin
    return lambda p: (ox + px*(np.asarray(p, float) @ R[0]), oy - px*(np.asarray(p, float) @ R[1]))

# ---------------- labels: a column (or row) of texts, pushed apart, leader to each anchor ----------------
def column(g, items, x, f, side='r', y_min=60, gap=6):
    """items: [(anchor_px, text)]; texts at x (left edge if side 'r', right edge if 'l'), y near each anchor"""
    y_prev = y_min
    for (ax, ay), s in sorted(items, key=lambda it: it[0][1]):
        n = s.count('\n') + 1; hgt = 17*n
        ty = max(ay - hgt/2, y_prev); y_prev = ty + hgt + gap
        w = max(g.textlength(l, font=f) for l in s.split('\n'))
        tx = x if side == 'r' else x - w
        ex = tx - 6 if side == 'r' else x + 6
        g.line([(ax, ay), (ex, ty + hgt/2 - 2)], fill=GREY, width=1)
        g.ellipse([ax - 3, ay - 3, ax + 3, ay + 3], fill=INK)
        g.multiline_text((tx, ty), s, fill=INK, font=f, spacing=3)

# ---------------- sections: slice the meshes, even-odd scanline fill ----------------
def slice_mesh(V, axis, c):
    d = V[..., axis] - c; m = (d.min(1) < 0) & (d.max(1) > 0); segs = []
    for T, D in zip(V[m], d[m]):
        pts = [T[i] + D[i] / (D[i] - D[(i+1) % 3]) * (T[(i+1) % 3] - T[i]) for i in range(3) if (D[i] < 0) != (D[(i+1) % 3] < 0)]
        if len(pts) == 2: segs.append(pts)
    return np.array(segs) if segs else np.zeros((0, 2, 3))
def section(img, A, axis, c, hu, hv, origin, px, skip=()):
    ox, oy = origin; g = ImageDraw.Draw(img)
    to_px = lambda u, v: (ox + px*u, oy - px*v)
    for key, _, V, colour in A:
        if key in skip: continue
        segs = slice_mesh(V, axis, c)
        if not len(segs): continue
        U, Vv = segs[..., hu], segs[..., hv]
        for py in range(int(oy - px*Vv.max()) - 1, int(oy - px*Vv.min()) + 2):
            v = (oy - py) / px; a, b = Vv[:, 0], Vv[:, 1]
            m = (np.minimum(a, b) <= v) & (np.maximum(a, b) > v)
            if not m.any(): continue
            xs = np.sort(U[m, 0] + (v - a[m]) / (b[m] - a[m]) * (U[m, 1] - U[m, 0]))
            for xa, xb in zip(xs[0::2], xs[1::2]): g.line([(ox + px*xa, py), (ox + px*xb, py)], fill=colour)
        for (ua, ub), (va, vb) in zip(U, Vv): g.line([to_px(ua, va), to_px(ub, vb)], fill=(45, 45, 45))
    return to_px

# ---------------- masses ----------------
def load_from(d, name):
    with open(os.path.join(d, name + '.stl'), 'rb') as f:
        f.read(80); n = struct.unpack('<I', f.read(4))[0]
        dt = np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')])
        return np.frombuffer(f.read(50*n), dtype=dt)['v'].reshape(-1, 3, 3).astype(float)
def masses(A, v1_dir):
    rho = dict(shell=1.18, cover=2.70, pad_floor=0.24, pad_top=0.24, wrap=0.24, mica=2.8, insul=1.4, hold=1.1, shim=1.21)
    m = {k: vol(V) * rho[k] for k, _, V, _ in A if k in rho}
    m['caps'] = P.cap_mass(False) + P.cap_mass(True)
    m['board'] = board_g(S.sb_board_area, S.SB_PCB_T); m['cells'] = 4 * CELL_G
    v1 = None
    if v1_dir:
        v1 = dict(shell=vol(load_from(v1_dir, 'monolith_side_shell'))*1.18, bumpers=2*vol(load_from(v1_dir, 'monolith_side_bumper'))*1.21,
                  cover=m['cover'], board=m['board'], cells=m['cells'])
    return m, v1

if __name__ == '__main__':
    v1_dir = sys.argv[1] if len(sys.argv) > 1 else None
    A = assembly(); f1, f2, f3 = font(26), font(18), font(15)
    pick = lambda pred: [(V, c) for k, _, V, c in A if pred(k)]
    centre = lambda parts: [(V - np.vstack([p[0].reshape(-1, 3) for p in parts]).mean(0), c) for V, c in parts]
    cx1, cy1 = S.sb_cell_xy[(1, -1)]; cx2 = S.sb_cell_xy[(-1, -1)][0]

    # ================= 1. assembled + exploded =================
    W, H = 2700, 1060; img = Image.new('RGB', (W, H), 'white')
    R = camera((1.0, -1.1, 0.65)); o1 = (300, 700); px = 5.6
    render(img, [(V, c) for _, _, V, c in A], R, o1, px)
    g = ImageDraw.Draw(img); pj = proj(R, o1, px)
    g.text((30, 20), 'Assembled', fill=INK, font=f1)
    column(g, [(pj((S.sb_port_x, 9, S.SB_H + S.SB_CAP_T)), 'port well through the top cap:\nboth plugs, overmolds up to 12.35 x 6.5 mm'),
               (pj((S.SB_CAP_OUT[1] - 2, -S.SB_CAP_OUT[2] + 2, S.SB_H + S.SB_CAP_T - 3)), 'dense corner noses (~60 % gyroid)\nfor corner drops'),
               (pj((S.sb_x_cv1, -8, 45)), '1 mm aluminium cover,\nalso the heat spreader'),
               (pj((S.sb_x_cv1, 0, S.SB_VENT_Z)), 'ePTFE pressure vent (unchanged)'),
               (pj((S.SB_CAP_OUT[1], -14, S.SB_CAP_BAND - 2)), 'cap band, 2 mm proud of the tray:\nflat side drops land on the bands'),
               (pj((S.SB_CAP_OUT[1] - 12, -10, -S.SB_CAP_T + 1)), '8 mm TPU lattice crush zone at both ends:\nsoft 15 % outside, firm 30 % behind')],
           560, f3)
    # exploded: everything goes in through the +x face, caps along z
    g.text((1080, 20), 'Exploded: parts go in through the open side, left to right; caps last', fill=INK, font=f1)
    EX = dict(shell=(0, 0, 0), wrap=(30, 0, 0), cell=(58, 0, 0), mica=(58, 0, 0), pad_floor=(58, 0, -16), pad_top=(58, 0, 16),
              insul=(88, 0, 0), board=(108, 0, 0), shim=(108, 0, -14), hold=(128, 0, 0), cover=(146, 0, 0))
    ex, anchor = [], {}
    for k, lab, V, c in A:
        d = EX.get(k, (0, 0, -40) if k.startswith('capb') else (0, 0, 40))
        ex.append((mv(V, *d), c)); anchor.setdefault(lab, V.reshape(-1, 3).mean(0) + d)
    R2 = camera((0.42, -1.25, 0.5)); o2 = (1380, 720); px2 = 4.3
    render(img, ex, R2, o2, px2)
    g = ImageDraw.Draw(img); pj2 = proj(R2, o2, px2)
    top = [('top cap', 'top crush cap'), ('top pad', 'PORON top pad 1.0 mm,\ncut-outs over the + caps'),
           ('USB-C hold-down', 'silicone hold-down pads\nover the USB-C bodies'), ('Al cover', 'aluminium cover, 2 x M2\ninto heat-set inserts'),
           ('board', '1.6 mm board: conformal coat,\nsoft staking, no potting')]
    bot = [('printed tray', 'one-piece printed tray: side guides,\nboard top stops, rupture windows'),
           ('side wrap', '1 mm PORON side wrap\n(gap pad if cells run hot)'), ('C1', 'cells (welded 4S) with the\nmica cross between them'),
           ('floor pad', 'PORON floor pad 4.8 mm,\ncut-outs over the + caps'), ('insulator', '0.3 mm insulator'),
           ('shim', 'TPU shim under the board'), ('bottom cap', 'bottom crush cap')]
    column(g, [(pj2(anchor[k]), s) for k, s in top if k in ('top cap', 'top pad')], 1080, f3, 'r', 90)
    left = ('printed tray', 'bottom cap', 'side wrap')
    column(g, [(pj2(anchor[k]), s) for k, s in top if k not in ('top cap', 'top pad')]
              + [(pj2(anchor[k]), s) for k, s in bot if k not in left], 2350, f3, 'r', 90)
    column(g, [(pj2(anchor[k]), s) for k, s in bot if k in left], 1050, f3, 'l', 820)
    g.text((30, H - 32), 'Caps by print zone: light orange = soft, orange = firm, dark = corner noses, brown = solid band. '
           'Pink: PORON. Gold: mica. Yellow: insulator. Purple: hold-down pads. Teal: shim. Board and USB-C are envelopes only.',
           fill=GREY, font=f3)
    img.save(os.path.join(HERE, 'monolith_side_exploded.png'))

    # ================= 2. sections =================
    W, H = 2600, 1300; img = Image.new('RGB', (W, H), 'white'); pxs = 9.0
    zc = (S.sb_z_cell0 + S.sb_z_cell1) / 2 + 0.03
    tp = section(img, A, 2, zc, 0, 1, (480, 600), pxs)
    g = ImageDraw.Draw(img)
    g.text((30, 20), f'A-A: across the pack at mid-cell (z = {zc:.0f} mm), seen from the port end', fill=INK, font=f1)
    aI, aC = S.a_in, S.a_cav
    column(g, [(tp(-aC + 0.5, 14), '1.0 mm PORON side wrap\n(silicone gap pad if the\ncells run hot)'),
               (tp(-aC - 0.6, 0), 'rib locates the cell block'),
               (tp(-aC - 0.6, -14), '1.2 mm printed wall')], 230, f3, 'l', 300)
    column(g, [(tp(aI + 0.6, aI - 1), 'board side guide (tray steps\nin to the board width)'),
               (tp(S.sb_xb0 + 0.8, 14), '1.6 mm board (coated, staked)'),
               (tp(S.sb_x_cv0 + 0.5, 4), 'Al cover; 0.5 mm gap pad from\nthe tall parts (not drawn)'),
               (tp(aI + 0.15, -8), '0.3 mm insulator'),
               (tp(0.6, -16), 'mica cross, 0.2 mm, in the 0.3 mm\ngaps between cells (propagation)'),
               (tp(S.sb_x_cv0 + 0.5, -aI - 0.25), 'cover rests in the rebates')], 800, f3, 'r', 300)
    for k, (name, end) in S.SB_CELLS.items():
        x, y = S.sb_cell_xy[k]; q = tp(x, y)
        g.text((q[0] - 10, q[1] - 22), name, fill='white', font=f2); g.text((q[0] - 26, q[1]), f'+ {end}', fill='white', font=f3)
    # B-B
    x0 = 1300
    g.text((x0, 20), f'B-B: along the pack through C1 (board side) and C2, y = {cy1:.1f} mm', fill=INK, font=f1)
    tpb = section(img, A, 1, cy1 - 0.03, 0, 2, (x0 + 560, 1180), pxs)
    g = ImageDraw.Draw(img)
    column(g, [(tpb(-12, S.SB_H + S.SB_CAP_T - 2), 'top crush cap: 4 mm soft\n+ 4 mm firm lattice'),
               (tpb(-S.SB_CAP_OUT[2] + 1, S.SB_H - 4), 'solid band over the tray end'),
               (tpb(cx1 - 3, S.sb_z_top_in - 0.5), 'top pad cut-out over the C1 + cap'),
               (tpb(cx2, 40), 'C2 (+ cap at the bottom)'),
               (tpb(-2, 55), 'mica between C1 and C2'),
               (tpb(cx2 + 9, S.SB_END_T + 2.4), 'PORON floor pad 4.8 mm: ~3 mm\nmore stroke for the cells in\nbottom-down drops'),
               (tpb(cx2 - 2, S.SB_END_T + 3.5), 'cut-out over the C2 + cap: the\nvent opens into a plenum'),
               (tpb(cx2 + 2, S.SB_END_T - S.SB_RUPT_T - 0.4), 'rupture window: wall thinned to\n0.6 mm, vents into the open lattice'),
               (tpb(-10, -S.SB_CAP_T + 2), 'bottom crush cap, band wraps\n9 mm up the sides')], x0 + 300, f3, 'l', 80)
    column(g, [(tpb(S.sb_port_x, S.SB_H + S.SB_CAP_T - 3), 'port well: the plug reaches the USB-C\nthrough the cap (USB-C at y = -6.5)'),
               (tpb(S.sb_xb0 + 0.8, S.sb_zb1 + 0.17), 'board top stop: drop loads go\nboard edge -> tray, not via the USB-C'),
               (tpb(S.sb_port_x + S.USB_UP + 0.8, S.SB_H - 4), 'USB-C hold-down pad'),
               (tpb(cx1, 40), 'C1 (+ cap at the top)'),
               (tpb(S.sb_xb0 + 0.8, 35), '1.6 mm board'),
               (tpb(S.sb_x_cv0 + 0.5, 30), 'aluminium cover'),
               (tpb(S.sb_xb0 + 0.8, S.SB_END_T + 1.2), 'TPU shim under the board'),
               (tpb(S.sb_x_cv1 - 2, S.sb_screw_z), 'M2 insert pillar (behind the cut)')], x0 + 860, f3, 'r', 80)
    g.text((30, H - 32), 'Cut from the same meshes that make the STLs. Board and USB-C are envelopes; nickel tabs, the gap pad '
           'and the parts on the board are not drawn.', fill=GREY, font=f3)
    img.save(os.path.join(HERE, 'monolith_side_sections.png'))

    # ================= 3. parts + numbers =================
    W, H = 2400, 1320; img = Image.new('RGB', (W, H), 'white')
    views = [(pick(lambda k: k.startswith('capb')), camera((0.8, -1.0, -0.9)), 'bottom cap from below: soft face (light),\ncorner noses (dark), solid band (brown)'),
             (pick(lambda k: k.startswith('capt')), camera((0.8, -1.0, 0.9)), 'top cap from above: one port well\nfor both plugs, near the cover side'),
             (pick(lambda k: k == 'shell'), camera((0.6, -0.8, -1.0)), 'tray from below: rupture windows under\nthe + caps of C2 and C4'),
             (pick(lambda k: k in ('pad_floor',)), camera((0.6, -0.9, 0.9)), 'floor pad: cut-outs over the C2 and C4\n+ caps, notch for the rib')]
    for i, (parts, Rv, cap) in enumerate(views):
        cxp = 300 + i*590; render(img, centre(parts), Rv, (cxp, 330), 3.6 if i == 2 else 5.0)
        ImageDraw.Draw(img).multiline_text((cxp - 230, 590), cap, fill=INK, font=f3, spacing=3)
    g = ImageDraw.Draw(img)
    g.text((30, 20), 'Crush caps, floor pad and rupture windows; mass and drop estimates', fill=INK, font=f1)
    m, v1 = masses(A, v1_dir); tot = sum(m.values())
    rows = [('tray (PETG)', m['shell']), ('aluminium cover', m['cover']), ('TPU crush caps (2, at print fill)', m['caps']),
            ('PORON floor + top pads', m['pad_floor'] + m['pad_top']), ('PORON side wrap', m['wrap']),
            ('mica cross', m['mica']), ('insulator', m['insul']), ('hold-down pads + shim', m['hold'] + m['shim']),
            ('board (1.6 mm, estimated)', m['board']), ('cells (4 x 71 g)', m['cells'])]
    y = 690; g.text((60, y), 'Mass (g)', fill=INK, font=f2); y += 32
    for k, v in rows:
        g.text((60, y), k, fill=INK, font=f3); g.text((420, y), f'{v:6.1f}', fill=INK, font=f3); y += 22
    g.text((60, y + 4), 'pack total', fill=INK, font=f2); g.text((410, y + 4), f'{tot:6.1f}', fill=INK, font=f2)
    lines = []
    if v1:
        t1 = sum(v1.values()); lines.append(f'previous side tray, thin bumpers: {t1:.1f} g -> {tot:.1f} g ({tot - t1:+.1f} g)')
    lines += [f'side wrap as a silicone gap pad (~2.2 g/cm3): +{m["wrap"]/0.24*2.2 - m["wrap"]:.1f} g',
              f'outside with caps {S.sb_x_out + S.a_sb + 2*S.SB_CAP_PROUD:.1f} x {2*(S.a_sb + S.SB_CAP_PROUD):.1f} x {S.sb_len:.1f} mm',
              '(was 54.4 x 49.0 x 83.0 mm)']
    for i, s in enumerate(lines): g.text((60, y + 44 + 22*i), s, fill=INK, font=f3)
    x0, y = 800, 690; st = 0.65 * S.SB_CAP_T
    g.text((x0, y), 'Drop estimate (first principles, to be measured)', fill=INK, font=f2); y += 32
    for s in (f'cap stroke ~{st:.1f} mm (65 % of {S.SB_CAP_T:g} mm), real-foam factor 1.3:',
              f'    1.0 m onto concrete ~{S.drop_g(1.0, st):.0f} g;   1.5 m ~{S.drop_g(1.5, st):.0f} g',
              f'    10 mm caps: ~{S.drop_g(1.0, 6.5):.0f} g / ~{S.drop_g(1.5, 6.5):.0f} g, pack 4 mm longer',
              'bottom-down: the cells also have ~3 mm of floor pad;',
              '    top-down only the 1 mm top pad (the board length sets it)',
              'benchmark: UN 38.3 T4 shock is 150 g for 6 ms;',
              '    the cells\' margin above that is not published',
              'corner drops: dense noses crush progressively,',
              '    soft foam alone would bottom out'):
        g.text((x0, y), s, fill=INK, font=f3); y += 22
    x0, y = 1560, 690
    g.text((x0, y), 'Materials and print settings (starting point)', fill=INK, font=f2); y += 32
    for s in ('caps: TPU 95A. Load *_mod_soft and *_mod_corner as modifiers:',
              '    soft 15 % gyroid, rest of the slab 30 %, corners 60 %,',
              '    band 100 %; no top/bottom skin on the outer face',
              'pads: PORON 4701-30 or XRD; floor 4.8 mm (2 x 2.4), top 1.0 mm',
              'side wrap: 1.0 mm PORON; a soft silicone gap pad',
              '    (1-1.5 W/m K, Shore 00 < 40) only if the 100 W run is hot',
              'mica: 0.2 mm muscovite, two pieces slotted into a cross',
              'board: acrylic or silicone conformal coat; soft silicone staking',
              '    on inductors, module, big MLCCs; BLE antenna end bare',
              'rupture windows: a concept, verify with a vent / burst test'):
        g.text((x0, y), s, fill=INK, font=f3); y += 22
    img.save(os.path.join(HERE, 'monolith_side_parts.png'))
    print(f"pack {tot:.1f} g; " + ", ".join(f"{k} {v:.1f}" for k, v in m.items()))
    if v1: print("v1: " + ", ".join(f"{k} {v:.1f}" for k, v in v1.items()) + f" -> {sum(v1.values()):.1f} g")
    print("wrote monolith_side_exploded.png, monolith_side_sections.png, monolith_side_parts.png")
