"""Drawing and assembly helpers from the retired side-tray renders (numpy + scipy + PIL; meshes from monolith_parts).
monolith_cup.py and monolith_cup_assembly_steps.py import Sheet, proj, visible_anchor, assembly, masses, PARTS, SIZE
and the colours from here. The side-tray render script itself (monolith_side_*.png) was removed on 2026-10-29 with
the rest of the side-tray outputs; it is in git history (Production 5cf521e).
Everything is drawn at SS x size and downsampled, so edges and text are antialiased."""
import numpy as np, os, sys, struct
from PIL import Image, ImageDraw, ImageFont
import monolith_shell as S, monolith_parts as P
from monolith_render import camera, board_g, vol, CELL_G

HERE = os.path.dirname(os.path.abspath(__file__))
SS = 2
C = dict(shell=(214, 214, 208), cover=(196, 204, 222), board=(52, 140, 84), cell=(84, 132, 196), soft=(250, 210, 160),
         firm=(236, 156, 80), corner=(186, 88, 40), band=(118, 72, 50), eva=(222, 118, 168), paper=(176, 128, 98), spacer=(70, 180, 200), frame=(70, 180, 200), cage=(38, 132, 150), tail=(226, 120, 44), wedge=(150, 128, 206),
         mica=(212, 180, 56), shim=(54, 166, 166), ble=(150, 175, 225), nickel=(150, 150, 140), wire=(200, 50, 50))
INK, MUTED, RULE, PANEL, ACCENT = (34, 34, 38), (110, 112, 118), (222, 222, 226), (247, 247, 249), (31, 78, 121)
LEADER = (150, 152, 158)

def flipz(V, z0):
    V = V.copy(); V[..., 2] = z0 - V[..., 2]; return V[:, ::-1]
def mv(V, dx=0, dy=0, dz=0): return V + [dx, dy, dz]

# ---------------- the assembly: (key, part number, mesh, colour) ----------------
# part numbers follow the assembly order; the caps are four print-zone meshes each
PARTS = [(1, 'Printed tray', 'MJF PA12 nylon', 'shell'), (2, 'Cell frame: ring carrier', 'TPU 95A', 'holder'),
         (3, 'Cells C1-C4, welded 4S', 'FEB 21700G 6500 mAh', 'cell'), (4, 'Cell cage: 1.2 mm webs, spine', 'TPU 95A', 'cage'),
         (5, 'Insulator rings on + ends (4)', 'fish paper 0.2', 'rings'),
         (6, 'Nickel series strips (3)', 'nickel 0.15 x 7', 'nickel'),
         (7, 'Nickel tails: PACK+/- (split), CELL1-3', 'nickel 0.2 / 0.15', 'tails'),
         (8, 'Cell frame: top plate, bars', 'TPU 95A', 'frame'), (9, 'Board insulator 0.2 mm', 'fish paper', 'insul'),
         (10, 'Board 1.6 mm, coated + staked', 'FR4, 6 layers', 'board'), (11, 'Cover standoffs (4), SMD 3.5 mm', 'steel', 'stand'),
         (12, 'Wedge, with the 2 cover-screw bosses', 'MJF PA12 nylon', 'wedge'), (13, 'USB-C hold-downs, 2 x 1 mm', 'EVA foam', 'hold'),
         (14, 'Cover 1.0 mm, 2 x M2', 'aluminium', 'cover'),
         (15, 'Bottom crush cap', 'TPU 95A lattice', 'capb'), (16, 'Top crush cap', 'TPU 95A lattice', 'capt')]
MODULE = ('holder', 'cell', 'cage', 'nickel', 'tails', 'frame', 'insul', 'board', 'ble', 'stand')   # built on the bench
PARTS.sort(key=lambda r: r[0])
NUM = {k: n for n, _, _, k in PARTS}
def assembly():
    A = [('shell', P.side_shell(), C['shell'])]
    cell = P.cell_solid()
    for k in S.SB_CELLS:
        x, y = S.sb_cell_xy[k]; A.append(('cell', mv(cell, x, y, S.sb_z_cell0), C['cell']))
    A += [('nickel', P.nickel_strips('strips'), C['nickel']), ('tails', P.nickel_strips('tails'), C['tail']),
          ('cage', P.cell_cage(), C['cage']),
          ('holder', P.ring_carrier(), C['frame']), ('frame', P.top_frame(), C['frame']),
          ('insul', P.insulator(), C['paper']), ('board', P.side_board_dummy(), C['board']),
          ('wedge', P.wedge(), C['wedge']), ('hold', P.hold_pads(), C['eva']), ('cover', P.side_cover(), C['cover']),
          ('ble', P.ble_module(), C['ble']), ('stand', P.cover_standoffs(), C['nickel'])]
    for z in ('soft', 'firm', 'corner', 'band'):
        A.append(('capb_' + z, P.side_cap(z), C[z]))
        A.append(('capt_' + z, flipz(P.side_cap(z, True), S.SB_H), C[z]))
    return A
def group(key): return key.split('_')[0] if key.startswith('cap') else key

# ---------------- z-buffer renderer with outlines ----------------
LIGHT = np.array([0.35, -0.55, 0.75]); LIGHT = LIGHT / np.linalg.norm(LIGHT)
def zrender(img, parts, R, origin, px, edge_px=2, tex=None):
    """parts: [(V, colour)]; R = camera rows (right, up, toward viewer); returns the part-index buffer"""
    W, H = img.size; ox, oy = origin
    zb = np.full((H, W), -np.inf); col = np.zeros((H, W, 3)); pid = np.full((H, W), -1)
    for ip, (V, c) in enumerate(parts):
        n = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
        sh = 0.50 + 0.50 * np.abs(n @ LIGHT)
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
    if tex is not None: tex(base, pid, zb, ox, oy, px, R)     # e.g. the laser-marked label on the cover
    e = np.zeros_like(hit)          # outline where the part changes or the depth jumps
    for dy, dx in ((0, 1), (1, 0)):
        p2 = np.roll(np.roll(pid, -dy, 0), -dx, 1); z2 = np.roll(np.roll(zb, -dy, 0), -dx, 1)
        with np.errstate(invalid='ignore'):
            e |= (pid != p2) | (np.abs(np.nan_to_num(zb - z2, posinf=99, neginf=99)) > 1.0)
    e &= hit | np.roll(hit, -1, 0) | np.roll(hit, -1, 1)
    for _ in range(edge_px - 1): e |= np.roll(e, 1, 0) | np.roll(e, 1, 1)
    base[e] = base[e] * 0.35 + np.array(INK) * 0.4
    img.paste(Image.fromarray(base.clip(0, 255).astype(np.uint8)))
    return pid

# ---------------- sections: slice the meshes, even-odd scanline fill ----------------
def slice_mesh(V, axis, c):
    d = V[..., axis] - c; m = (d.min(1) < 0) & (d.max(1) > 0); segs = []
    for T, D in zip(V[m], d[m]):
        pts = [T[i] + D[i] / (D[i] - D[(i+1) % 3]) * (T[(i+1) % 3] - T[i]) for i in range(3) if (D[i] < 0) != (D[(i+1) % 3] < 0)]
        if len(pts) == 2: segs.append(pts)
    return np.array(segs) if segs else np.zeros((0, 2, 3))

# ---------------- a drawing sheet: final-pixel coordinates, drawn at SS x ----------------
def _font(size, bold=False):
    for f in (('seguisb.ttf', 'segoeuib.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf') if bold else ('segoeui.ttf', 'arial.ttf', 'DejaVuSans.ttf')):
        try: return ImageFont.truetype(f, int(size*SS))
        except OSError: pass
    return ImageFont.load_default()
class Sheet:
    def __init__(self, W, H):
        self.W, self.H = W, H; self.img = Image.new('RGB', (W*SS, H*SS), 'white'); self.g = ImageDraw.Draw(self.img)
        self._f = {}
    def f(self, size, bold=False):
        return self._f.setdefault((size, bold), _font(size, bold))
    def tw(self, s, size=15, bold=False): return max(self.g.textlength(l, font=self.f(size, bold)) for l in s.split('\n')) / SS
    def text(self, x, y, s, size=15, bold=False, fill=INK, anchor='la', spacing=4):
        self.g.multiline_text((x*SS, y*SS), s, font=self.f(size, bold), fill=fill, anchor=anchor, spacing=spacing*SS)
    def line(self, pts, fill=LEADER, width=1):
        self.g.line([(x*SS, y*SS) for x, y in pts], fill=fill, width=max(1, int(width*SS)))
    def rect(self, x0, y0, x1, y1, fill=None, outline=None, r=0, width=1):
        self.g.rounded_rectangle([x0*SS, y0*SS, x1*SS, y1*SS], radius=r*SS, fill=fill, outline=outline, width=int(width*SS))
    def dot(self, x, y, r=3, fill=INK): self.g.ellipse([(x-r)*SS, (y-r)*SS, (x+r)*SS, (y+r)*SS], fill=fill)
    def header(self, title, sub):
        self.text(40, 26, title, 30, True); self.text(40, 70, sub, 16, fill=MUTED)
        self.line([(40, 104), (self.W - 40, 104)], RULE, 1.5)
    def panel_title(self, x, y, s, w=None):
        self.text(x, y, s, 19, True)
        if w: self.line([(x, y + 32), (x + w, y + 32)], RULE, 1)
    def render(self, parts, R, origin, px, tex=None):
        pid = zrender(self.img, parts, R, (origin[0]*SS, origin[1]*SS), px*SS, tex=tex)
        self.g = ImageDraw.Draw(self.img); return pid
    def section(self, A, axis, c, hu, hv, origin, px):
        ox, oy = origin; g = self.g
        to_px = lambda u, v: (ox + px*u, oy - px*v)
        for key, V, colour in A:
            segs = slice_mesh(V, axis, c)
            if not len(segs): continue
            U, Vv = segs[..., hu], segs[..., hv]
            for py in range(int((oy - px*Vv.max())*SS) - 1, int((oy - px*Vv.min())*SS) + 2):
                v = (oy - py/SS) / px; a, b = Vv[:, 0], Vv[:, 1]
                m = (np.minimum(a, b) <= v) & (np.maximum(a, b) > v)
                if not m.any(): continue
                xs = np.sort(U[m, 0] + (v - a[m]) / (b[m] - a[m]) * (U[m, 1] - U[m, 0]))
                for xa, xb in zip(xs[0::2], xs[1::2]): g.line([((ox + px*xa)*SS, py), ((ox + px*xb)*SS, py)], fill=colour)
            for (ua, ub), (va, vb) in zip(U, Vv):
                g.line([(to_px(ua, va)[0]*SS, to_px(ua, va)[1]*SS), (to_px(ub, vb)[0]*SS, to_px(ub, vb)[1]*SS)], fill=(70, 70, 74), width=2)
        return to_px
    def callouts(self, items, x, side='r', y_min=120, y_max=None, size=14, gap=10):
        """items: [((ax, ay), text)]; text column at x (left edge if side 'r', right edge if 'l'); elbow leaders"""
        lh = size * 1.45; y_prev = y_min
        for (ax, ay), s in sorted(items, key=lambda it: it[0][1]):
            h = lh * (s.count('\n') + 1)
            ty = max(ay - h/2, y_prev); y_prev = ty + h + gap
            w = self.tw(s, size); ym = ty + lh/2
            ex = x - 10 if side == 'r' else x + 10          # end of the leader, beside the first line
            kx = ex - 18 if side == 'r' else ex + 18         # elbow
            self.line([(ax, ay), (kx, ym), (ex, ym)], LEADER, 1.2); self.dot(ax, ay, 3.2)
            self.text(x if side == 'r' else x - w, ty, s, size, spacing=3)
    def dim(self, p0, p1, off, text, size=14):
        """dimension between screen points p0, p1 (horizontal or vertical), offset off px to the side"""
        (x0, y0), (x1, y1) = p0, p1
        if abs(y1 - y0) < abs(x1 - x0):      # horizontal
            y = min(y0, y1) + off if off > 0 else min(y0, y1) + off
            self.line([(x0, y0), (x0, y + np.sign(off)*6)], MUTED, 1); self.line([(x1, y1), (x1, y + np.sign(off)*6)], MUTED, 1)
            self.line([(x0, y), (x1, y)], INK, 1.2); self._arrow(x0, y, 1, 0); self._arrow(x1, y, -1, 0)
            tw = self.tw(text, size); self.rect((x0+x1)/2 - tw/2 - 4, y - 11, (x0+x1)/2 + tw/2 + 4, y + 11, fill='white')
            self.text((x0+x1)/2, y, text, size, anchor='mm')
        else:                                 # vertical
            x = max(x0, x1) + off if off > 0 else min(x0, x1) + off
            self.line([(x0, y0), (x + np.sign(off)*6, y0)], MUTED, 1); self.line([(x1, y1), (x + np.sign(off)*6, y1)], MUTED, 1)
            self.line([(x, y0), (x, y1)], INK, 1.2); self._arrow(x, y0, 0, np.sign(y1 - y0)); self._arrow(x, y1, 0, -np.sign(y1 - y0))
            tw = self.tw(text, size); self.rect(x - tw/2 - 4, (y0+y1)/2 - 11, x + tw/2 + 4, (y0+y1)/2 + 11, fill='white')
            self.text(x, (y0+y1)/2, text, size, anchor='mm')
    def _arrow(self, x, y, dx, dy, L=8, w=3.5):
        px_, py_ = -dy, dx
        pts = [(x, y), (x + dx*L + px_*w, y + dy*L + py_*w), (x + dx*L - px_*w, y + dy*L - py_*w)]
        self.g.polygon([(a*SS, b*SS) for a, b in pts], fill=INK)
    def legend(self, items, x, y, size=14, step=None):
        for name, c in items:
            self.rect(x, y + 2, x + 18, y + 18, fill=c, outline=(90, 90, 90), r=3, width=1)
            self.text(x + 26, y, name, size, fill=INK); x += step or (self.tw(name, size) + 56)
    def table(self, x, y, cols, rows, widths, size=14, head=True, bold_last=False, rh=27):
        """cols: header strings; rows: lists of strings; widths: column widths; numbers right-aligned"""
        W = sum(widths)
        if head:
            self.rect(x, y, x + W, y + rh, fill=(236, 238, 242), r=4)
            cx = x
            for c, w in zip(cols, widths):
                self.text(cx + 10 if not c.startswith('>') else cx + w - 10, y + rh/2, c.lstrip('>'), size, True,
                          anchor='lm' if not c.startswith('>') else 'rm'); cx += w
            y += rh
        for i, r in enumerate(rows):
            last = bold_last and i == len(rows) - 1
            if last: self.line([(x, y + 2), (x + W, y + 2)], INK, 1.2)
            elif i % 2: self.rect(x, y, x + W, y + rh, fill=PANEL)
            cx = x
            for j, (c, w) in enumerate(zip(r, widths)):
                right = cols[j].startswith('>')
                self.text(cx + w - 10 if right else cx + 10, y + rh/2, c, size, last, anchor='rm' if right else 'lm'); cx += w
            y += rh
        return y
    def balloon(self, x, y, n, r=13):
        self.g.ellipse([(x-r)*SS, (y-r)*SS, (x+r)*SS, (y+r)*SS], fill='white', outline=ACCENT, width=int(2*SS))
        self.text(x, y + 0.5, str(n), 14, True, fill=ACCENT, anchor='mm')
    def save(self, name):
        self.img.resize((self.W, self.H), Image.LANCZOS).save(os.path.join(S.RETIRED, name))

def proj(R, origin, px):
    ox, oy = origin
    return lambda p: (ox + px*(np.asarray(p, float) @ R[0]), oy - px*(np.asarray(p, float) @ R[1]))
def visible_anchor(pid, idx):
    """a visible pixel of the parts idx (final-pixel coords): the one nearest the middle of what is visible"""
    m = np.isin(pid, list(idx))
    if not m.any(): return None
    ys, xs = np.nonzero(m); cy, cx = ys.mean(), xs.mean()
    k = np.argmin((ys - cy)**2 + (xs - cx)**2)
    return xs[k] / SS, ys[k] / SS

# ---------------- masses ----------------
def load_from(d, name):
    with open(os.path.join(d, name + '.stl'), 'rb') as f:
        f.read(80); n = struct.unpack('<I', f.read(4))[0]
        dt = np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')])
        return np.frombuffer(f.read(50*n), dtype=dt)['v'].reshape(-1, 3, 3).astype(float)
RHO = dict(nickel=8.9, tails=8.9, holder=1.0, frame=1.0, stand=7.8, shell=1.01, cover=2.70, cage=1.0, insul=1.2, hold=0.20, wedge=1.01)
def masses(A, v1_dir):
    m = {}
    for k, V, _ in A:
        if k in RHO: m[k] = m.get(k, 0) + vol(V) * RHO[k]
    m['capb'], m['capt'] = P.cap_mass(False), P.cap_mass(True)
    m['board'] = board_g(S.sb_board_area, S.SB_PCB_T); m['cell'] = 4 * CELL_G
    m['rings'] = 4 * np.pi/4 * (21.0**2 - 10.0**2) * 0.2 / 1000 * 1.2   # 21 x 10 mm rings, not modelled
    v1 = None
    if v1_dir:
        v1 = dict(shell=vol(load_from(v1_dir, 'monolith_side_shell'))*1.18, bumpers=2*vol(load_from(v1_dir, 'monolith_side_bumper'))*1.21,
                  cover=m['cover'], board=m['board'], cell=m['cell'])
    return m, v1

SIZE = lambda: (S.sb_x_out + S.a_sb + 2*S.SB_CAP_PROUD, 2*(S.a_sb + S.SB_CAP_PROUD), S.sb_len)
