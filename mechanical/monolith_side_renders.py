"""Monolith side-tray drop-protection renders (numpy + scipy + PIL; builds the meshes from monolith_parts).
Run: python monolith_side_renders.py [v1_dir]
-> monolith_side_exploded.png  (assembled view, exploded view with numbered balloons, parts list)
   monolith_side_sections.png  (A-A across the cells, B-B along C1/C2, with dimensions)
   monolith_side_parts.png     (cap zones, tray floor, pads; mass, drop and print-setting tables)
v1_dir (optional) holds the previous monolith_side_shell.stl and monolith_side_bumper.stl for the mass comparison.
Design basis: reports/Battery pack potting and drop protection.md (no potting; crush caps outside a stiff core).
Everything is drawn at SS x size and downsampled, so edges and text are antialiased."""
import numpy as np, os, sys, struct
from PIL import Image, ImageDraw, ImageFont
import monolith_shell as S, monolith_parts as P
from monolith_render import camera, board_g, vol, CELL_G

HERE = os.path.dirname(os.path.abspath(__file__))
SS = 2
C = dict(shell=(214, 214, 208), cover=(196, 204, 222), board=(52, 140, 84), cell=(84, 132, 196), soft=(250, 210, 160),
         firm=(236, 156, 80), corner=(186, 88, 40), band=(118, 72, 50), eva=(222, 118, 168), paper=(176, 128, 98), spacer=(70, 180, 200),
         mica=(212, 180, 56), shim=(54, 166, 166), antp=(120, 120, 128))
INK, MUTED, RULE, PANEL, ACCENT = (34, 34, 38), (110, 112, 118), (222, 222, 226), (247, 247, 249), (31, 78, 121)
LEADER = (150, 152, 158)

def flipz(V, z0):
    V = V.copy(); V[..., 2] = z0 - V[..., 2]; return V[:, ::-1]
def mv(V, dx=0, dy=0, dz=0): return V + [dx, dy, dz]

# ---------------- the assembly: (key, part number, mesh, colour) ----------------
# part numbers follow the assembly order; the caps are four print-zone meshes each
PARTS = [(1, 'Printed tray', 'PETG', 'shell'), (2, 'Side liner 0.2 mm', 'fish paper', 'wrap'),
         (3, 'Floor spacer 3.8 mm', 'TPU 95A, ~20 % gyroid', 'pad_floor'), (4, 'Floor pad 1.0 mm', 'EVA foam', 'eva_floor'),
         (5, 'Cells C1-C4, welded 4S', 'EVE INR21700-58E', 'cell'), (6, 'Insulator rings on + ends (4)', 'fish paper 0.2', 'rings'),
         (7, 'Mica cross 0.2 mm', 'mica', 'mica'), (8, 'Top pad 1.0 mm', 'EVA foam', 'pad_top'),
         (9, 'Board insulator 0.2 mm', 'fish paper', 'insul'), (10, 'Board 1.6 mm, coated + staked', 'FR4, 6 layers', 'board'),
         (11, 'Board shim', 'TPU 95A', 'shim'), (12, 'USB-C hold-downs, 2 x 1 mm', 'EVA foam', 'hold'),
         (13, 'Cover 1.0 mm, 2 x M2, antenna notch', 'aluminium', 'cover'),
         (14, 'Antenna window plate', 'PETG, silicone-sealed', 'antp'),
         (15, 'Bottom crush cap', 'TPU 95A lattice', 'capb'), (16, 'Top crush cap', 'TPU 95A lattice', 'capt')]
NUM = {k: n for n, _, _, k in PARTS}
def assembly():
    A = [('shell', P.side_shell(), C['shell'])]
    cell = P.cell_solid()
    for k in S.SB_CELLS:
        x, y = S.sb_cell_xy[k]; A.append(('cell', mv(cell, x, y, S.sb_z_cell0), C['cell']))
    A += [('mica', P.mica_cross(), C['mica']), ('wrap', P.side_pad(), C['paper']),
          ('pad_floor', P.end_pad('bottom', 'spacer'), C['spacer']), ('eva_floor', P.end_pad('bottom'), C['eva']),
          ('pad_top', P.end_pad('top'), C['eva']),
          ('insul', P.insulator(), C['paper']), ('board', P.side_board_dummy(), C['board']),
          ('shim', P.board_shim(), C['shim']), ('hold', P.hold_pads(), C['eva']), ('cover', P.side_cover(), C['cover']),
          ('antp', P.ant_plate(), C['antp'])]
    for z in ('soft', 'firm', 'corner', 'band'):
        A.append(('capb_' + z, P.side_cap(z), C[z]))
        A.append(('capt_' + z, flipz(P.side_cap(z, True), S.SB_H), C[z]))
    return A
def group(key): return key.split('_')[0] if key.startswith('cap') else key

# ---------------- z-buffer renderer with outlines ----------------
LIGHT = np.array([0.35, -0.55, 0.75]); LIGHT = LIGHT / np.linalg.norm(LIGHT)
def zrender(img, parts, R, origin, px, edge_px=2):
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
    def render(self, parts, R, origin, px):
        pid = zrender(self.img, parts, R, (origin[0]*SS, origin[1]*SS), px*SS)
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
        self.img.resize((self.W, self.H), Image.LANCZOS).save(os.path.join(HERE, name))

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
RHO = dict(antp=1.27, shell=1.18, cover=2.70, pad_floor=0.30, eva_floor=0.20, pad_top=0.20, wrap=1.2, mica=2.8, insul=1.2, hold=0.20, shim=1.21)
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

if __name__ == '__main__':
    v1_dir = sys.argv[1] if len(sys.argv) > 1 else None
    A = assembly(); m, v1 = masses(A, v1_dir); total = sum(m.values())
    cx1, cy1 = S.sb_cell_xy[(1, -1)]; cx2 = S.sb_cell_xy[(-1, -1)][0]
    LEG = [('tray', C['shell']), ('cells', C['cell']), ('board', C['board']), ('Al cover', C['cover']), ('EVA foam', C['eva']),
           ('mica', C['mica']), ('fish paper', C['paper']), ('TPU soft 15 %', C['soft']), ('TPU firm 30 %', C['firm']),
           ('TPU corners 60 %', C['corner']), ('TPU band, solid', C['band']), ('TPU floor spacer', C['spacer']), ('TPU shim', C['shim']), ('antenna plate', C['antp'])]
    w, d, L = SIZE()

    # ================= 1. assembled + exploded + parts list =================
    sh = Sheet(2700, 1100)
    sh.header('Monolith side tray: drop protection without potting',
              'Nothing is potted. The tray, cells and board form one stiff core; the TPU end caps outside it are the crush zone. '
              f'Pack {w:.1f} x {d:.1f} x {L:.1f} mm, about {total:.0f} g.')
    sh.panel_title(40, 128, 'Assembled', 640)
    R = camera((1.0, -1.1, 0.65)); o1 = (250, 640); px = 5.0
    sh.render([(V, c) for _, V, c in A], R, o1, px); pj = proj(R, o1, px)
    sh.callouts([(pj((S.sb_port_x, 9, S.SB_H + S.SB_CAP_T)), 'Port well through the top cap,\nboth plugs (overmolds to 12.35 x 6.5)'),
                 (pj((S.SB_CAP_OUT[1] - 2, -S.SB_CAP_OUT[2] + 2, S.SB_H + S.SB_CAP_T - 3)), 'Dense corner noses for corner drops'),
                 (pj((S.sb_x_cv1, -8, 45)), 'Aluminium cover, also the heat spreader'),
                 (pj((S.sb_x_cv1, 0, S.SB_VENT_Z)), 'ePTFE pressure vent'),
                 (pj((S.sb_x_cv1, S.SB_ANT_SIDE*(S.sb_ant_y0 + S.sb_ant_y1)/2, S.sb_ant_zc)), 'Antenna window: printed plate in a\ncover notch over the BLE module'),
                 (pj((S.SB_CAP_OUT[1], -14, S.SB_CAP_BAND - 2)), 'Solid band 2 mm proud of the tray:\nflat side drops land here'),
                 (pj((S.SB_CAP_OUT[1] - 12, -10, -S.SB_CAP_T + 1)), '8 mm graded TPU lattice at each end')],
                475, 'r', 150)
    # exploded
    sh.panel_title(780, 128, 'Exploded, in assembly order', 1180)
    EX = dict(shell=(0, 0, 0), wrap=(30, 0, 0), cell=(58, 0, 0), mica=(58, 0, 0), pad_floor=(58, 0, -24), eva_floor=(58, 0, -12), pad_top=(58, 0, 16),
              insul=(88, 0, 0), board=(108, 0, 0), shim=(108, 0, -14), hold=(128, 0, 0), cover=(146, 0, 0), antp=(146, 0, 0))
    ex, gid = [], []
    for k, V, c in A:
        dd = EX.get(k, (0, 0, -40) if k.startswith('capb') else (0, 0, 40))
        ex.append((mv(V, *dd), c)); gid.append(group(k))
    R2 = camera((0.42, -1.25, 0.5)); o2 = (1130, 690); px2 = 4.2
    pid = sh.render(ex, R2, o2, px2)
    anchors = {}
    for g_ in dict.fromkeys(gid):
        a = visible_anchor(pid, [i for i, x in enumerate(gid) if x == g_])
        if a is not None: anchors[g_] = a
    # balloon direction per part (screen degrees, 0 = right, 90 = up), chosen to land in clear space
    BAL = dict(shell=180, wrap=240, pad_floor=250, eva_floor=330, cell=65, mica=300, pad_top=95, insul=125, board=75, shim=300,
               hold=60, cover=0, antp=20, capb=180, capt=180)
    DIST = dict(capb=150, capt=150)
    balloons = {g_: np.array([ax + DIST.get(g_, 80)*np.cos(np.radians(BAL[g_])), ay - DIST.get(g_, 80)*np.sin(np.radians(BAL[g_]))])
                for g_, (ax, ay) in anchors.items()}
    for g_, (bx, by) in balloons.items():
        ax, ay = anchors[g_]; v = np.array([bx - ax, by - ay]); v = v / (np.linalg.norm(v) + 1e-9)
        sh.line([(ax, ay), (bx - v[0]*13, by - v[1]*13)], ACCENT, 1.2); sh.dot(ax, ay, 3, ACCENT); sh.balloon(bx, by, NUM[g_])
    # parts list
    x0 = 2010; sh.panel_title(x0, 128, 'Parts', 650)
    rows = [[str(n), name, mat, f'{m[k]:.1f}' if m[k] >= 0.05 else '<0.1'] for n, name, mat, k in PARTS]
    rows.append(['', 'Pack total', '', f'{total:.1f}'])
    y = sh.table(x0, 176, ['#', 'Part', 'Material', '>g'], rows, [40, 300, 210, 90], 14, bold_last=True)
    if v1:
        t1 = sum(v1.values())
        sh.text(x0, y + 14, f'Previous tray with thin bumpers: {t1:.1f} g, so {total - t1:+.1f} g for the drop protection.', 14, fill=MUTED)
    sh.text(x0, y + 40, 'Board mass is estimated (FR4 + 6-layer copper); parts on it are not included.', 14, fill=MUTED)
    sh.text(x0, y + 66, 'Cap mass is at print fill: 15 / 30 / 60 % gyroid, solid band.', 14, fill=MUTED)
    sh.line([(40, 1030), (2660, 1030)], RULE, 1.5)
    sh.legend(LEG, 40, 1050, 14)
    sh.save('monolith_side_exploded.png')

    # ================= 2. sections =================
    sh = Sheet(2700, 1270)
    sh.header('Sections', 'Cut from the same meshes that make the STLs. Board and USB-C are envelopes; nickel tabs, the 0.5 mm gap pad '
              'to the cover and the parts on the board are not drawn.')
    zc = (S.sb_z_cell0 + S.sb_z_cell1) / 2 + 0.03; aI, aC = S.a_in, S.a_cav; pxa = 11.0
    sh.panel_title(40, 128, f'A-A   across the pack at mid-cell (z = {zc:.0f} mm), seen from the port end', 1180)
    oa = (620, 560)
    tp = sh.section(A, 2, zc, 0, 1, oa, pxa)
    for k, (name, end) in S.SB_CELLS.items():
        x, y = S.sb_cell_xy[k]; q = tp(x, y)
        sh.text(q[0], q[1] - 12, name, 22, True, fill='white', anchor='mm'); sh.text(q[0], q[1] + 16, f'+ cap {end}', 14, fill='white', anchor='mm')
    sh.callouts([(tp(-aC + 0.5, 14), '0.2 mm fish paper liner: the\ncans stay close to the walls\nfor heat'),
                 (tp(-aC - 0.6, 0), 'Rib locates the cell block'),
                 (tp(-aC - 0.6, -15), '1.2 mm printed wall')], 330, 'l', 250)
    sh.callouts([(tp(aI + 0.6, aI - 1), 'Board side guide: the tray\nsteps in to the board width'),
                 (tp(S.sb_xb0 + 0.8, 12), '1.6 mm board, coated and staked'),
                 (tp(S.sb_x_cv0 + 0.5, 3), 'Aluminium cover'),
                 (tp(aI + 0.15, -6), '0.2 mm fish paper insulator'),
                 (tp(0.6, -16), 'Mica cross 0.2 mm in the 0.3 mm\ngaps between the cells'),
                 (tp(S.sb_x_cv0 + 0.5, -aI - 0.25), 'Cover rests in the rebates')], 1070, 'r', 250)
    sh.dim(tp(-S.a_sb, -S.a_sb), tp(S.sb_x_out, -S.a_sb), 70, f'{S.sb_x_out + S.a_sb:.1f} tray')
    sh.dim(tp(S.sb_x_out, -S.a_sb), tp(S.sb_x_out, S.a_sb), 45, f'{2*S.a_sb:.1f}')
    sh.text(oa[0] - 260, 1000, f'Caps add {S.SB_CAP_PROUD:g} mm per side at the ends: {w:.1f} x {d:.1f} mm overall.', 14, fill=MUTED)
    # B-B
    x0 = 1400; pxb = 9.0
    sh.panel_title(x0, 128, f'B-B   along the pack through C1 (board side) and C2, y = {cy1:.1f} mm', 1260)
    ob = (x0 + 640, 1010)
    tb = sh.section(A, 1, cy1 - 0.03, 0, 2, ob, pxb)
    sh.text(*tb(cx2, 40), 'C2', 22, True, fill='white', anchor='mm'); sh.text(*tb(cx1, 40), 'C1', 22, True, fill='white', anchor='mm')
    sh.callouts([(tb(-12, S.SB_H + S.SB_CAP_T - 2), 'Top crush cap: 4 mm soft\n+ 4 mm firm lattice'),
                 (tb(-S.SB_CAP_OUT[2] + 1, S.SB_H - 4), 'Solid band over the tray end'),
                 (tb(cx1 - 6, S.sb_z_top_in - 0.5), 'Top pad cut-out over the C1 + cap'),
                 (tb(-2, 55), 'Mica between C1 and C2'),
                 (tb(cx2 + 9, S.SB_END_T + 2.4), '3.8 mm TPU spacer + 1 mm EVA:\n~3 mm more stroke for the cells\nin bottom-down drops'),
                 (tb(cx2 - 2, S.SB_END_T + 3.5), 'Cut-out over the C2 + cap:\nthe cell vent is not blocked'),
                 (tb(-10, -S.SB_CAP_T + 2), 'Bottom crush cap, band wraps\n9 mm up the sides')], x0 + 300, 'l', 170)
    sh.callouts([(tb(S.sb_port_x, S.SB_H + S.SB_CAP_T - 3), 'Port well: the plug reaches the\nUSB-C through the cap'),
                 (tb(S.sb_xb0 + 0.8, S.sb_zb1 + 0.17), 'Board top stop: drop loads go\nboard edge -> tray, not via USB-C'),
                 (tb(S.sb_port_x + S.USB_UP + 0.8, S.SB_H - 4), 'USB-C hold-down, 2 x 1 mm EVA'),
                 (tb(S.sb_xb0 + 0.8, 35), '1.6 mm board'),
                 (tb(S.sb_x_cv0 + 0.5, 30), 'Aluminium cover'),
                 (tb(S.sb_xb0 + 0.8, S.SB_END_T + 1.2), 'TPU shim under the board'),
                 (tb(S.sb_x_cv1 - 2, S.sb_screw_z), 'M2 insert pillar (behind the cut)')], x0 + 1000, 'r', 170)
    xl = -S.a_sb - S.SB_CAP_PROUD
    sh.dim(tb(xl, -S.SB_CAP_T), tb(xl, S.SB_H + S.SB_CAP_T), -40, f'{L:.1f}')
    xr = S.SB_CAP_OUT[1]
    sh.dim(tb(xr, S.SB_H), tb(xr, S.SB_H + S.SB_CAP_T), 28, f'{S.SB_CAP_T:g}')
    sh.dim(tb(xr, -S.SB_CAP_T), tb(xr, 0), 28, f'{S.SB_CAP_T:g}')
    sh.line([(40, 1200), (2660, 1200)], RULE, 1.5)
    sh.legend(LEG, 40, 1220, 14)
    sh.save('monolith_side_sections.png')

    # ================= 3. parts + numbers =================
    sh = Sheet(2700, 1080)
    sh.header('Crush caps, tray and pads', 'The new parts, with the mass, drop and print numbers behind them. '
              'Drop figures are first-principles estimates, to be measured with a dummy-mass drop test.')
    pick = lambda pred: [(V, c) for k, V, c in A if pred(k)]
    centre = lambda parts: [(V - np.vstack([p[0].reshape(-1, 3) for p in parts]).mean(0), c) for V, c in parts]
    cards = [(pick(lambda k: k.startswith('capb')), camera((0.8, -1.0, -0.9)), 5.0, 'Bottom cap, from below',
              'Soft face, dense corner noses,\nsolid band that wraps the tray'),
             (pick(lambda k: k.startswith('capt')), camera((0.8, -1.0, 0.9)), 5.0, 'Top cap, from above',
              'One port well for both plugs,\non the cover side'),
             (pick(lambda k: k == 'shell'), camera((1.0, -0.55, 0.45)), 3.5, 'Tray',
              'Open on the board side only;\nM2 insert pillars in the corners'),
             (pick(lambda k: k in ('pad_floor', 'eva_floor', 'pad_top')), camera((0.6, -0.9, 0.9)), 4.6, 'Floor spacer and EVA pads',
              'Cut-outs over the + caps,\nnotch for the rib')]
    cw = 640
    for i, (parts, Rv, pxv, t, s) in enumerate(cards):
        x = 40 + i*(cw + 20)
        sh.rect(x, 128, x + cw, 640, fill=PANEL, r=10)
        if i == 3:   # floor pad in front, top pad behind it
            parts = [(mv(V, 0, 0, -(S.sb_z_cell1 - S.SB_END_T) + 40) if V[..., 2].mean() > 40 else V, c) for V, c in parts]
        sh.render(centre(parts), Rv, (x + cw/2, 390), pxv)
        sh.text(x + 24, 560, t, 18, True); sh.text(x + 24, 590, s, 14, fill=MUTED, spacing=3)
    # mass table
    y0 = 680; x = 40
    sh.panel_title(x, y0, 'Mass', 820)
    rows = [['Tray (PETG)', f"{m['shell']:.1f}"], ['Aluminium cover', f"{m['cover']:.1f}"],
            ['TPU crush caps, 2, at print fill', f"{m['capb'] + m['capt']:.1f}"],
            ['TPU floor spacer, EVA pads', f"{m['pad_floor'] + m['eva_floor'] + m['pad_top']:.1f}"],
            ['Fish paper: liner, insulator, rings', f"{m['wrap'] + m['insul'] + m['rings']:.1f}"],
            ['Mica cross', f"{m['mica']:.1f}"], ['EVA hold-downs and TPU shim', f"{m['hold'] + m['shim']:.1f}"],
            ['Board, 1.6 mm (estimate)', f"{m['board']:.1f}"], ['Cells, 4 x 71 g', f"{m['cell']:.1f}"], ['Pack total', f'{total:.1f}']]
    y = sh.table(x, y0 + 46, ['Part', '>g'], rows, [400, 110], 14, bold_last=True)
    notes = []
    if v1: notes.append(f'Previous tray with thin bumpers: {sum(v1.values()):.1f} g ({total - sum(v1.values()):+.1f} g now).')
    notes += [f'Outside {w:.1f} x {d:.1f} x {L:.1f} mm (was 54.4 x 49.0 x 83.0).']
    for i, s in enumerate(notes): sh.text(x + 540, y0 + 60 + 26*i, s, 14, fill=MUTED)
    # drop table
    x = 940; sh.panel_title(x, y0, 'Drop estimate (peak deceleration at the core)', 820)
    st8, st10 = 0.65*S.SB_CAP_T, 0.65*10
    rows = [['1.0 m onto concrete', f'~{S.drop_g(1.0, st8):.0f} g', f'~{S.drop_g(1.0, st10):.0f} g'],
            ['1.5 m onto concrete', f'~{S.drop_g(1.5, st8):.0f} g', f'~{S.drop_g(1.5, st10):.0f} g'],
            ['Pack length', f'{L:.1f} mm', f'{L + 4:.1f} mm']]
    y = sh.table(x, y0 + 46, ['', f'>{S.SB_CAP_T:g} mm caps (model)', '>10 mm caps'], rows, [250, 230, 200], 14)
    for i, s in enumerate((f'Stroke is 65 % of the cap thickness, with a 1.3 factor for a real foam curve.',
                           'Benchmark: the UN 38.3 T4 shock is 150 g for 6 ms. The cells\' margin above that is not published.',
                           'Bottom-down drops add ~3 mm of floor pad for the cells; top-down only the 1 mm top pad.',
                           'Corner drops: the dense noses crush progressively, where soft foam would bottom out.')):
        sh.text(x, y + 18 + 26*i, s, 14, fill=MUTED)
    # materials table
    x = 1840; sh.panel_title(x, y0, 'Materials and print settings (starting point)', 820)
    rows = [['Caps', 'TPU 95A; modifier STLs: soft 15 %,'], ['', 'slab 30 %, corners 60 %, band solid'],
            ['Cell-end pads', '1 mm EVA, cut-outs over the + caps;'], ['', 'floor: on a 3.8 mm TPU spacer (20 % gyroid)'],
            ['Fish paper', '0.2 mm: wall liner, board insulator,'], ['', '+ end rings (21 x ~10 mm, vents open)'],
            ['Mica', '0.2 mm sheet, two slotted pieces'],
            ['Board', 'conformal coat; soft silicone staking'], ['', 'BLE antenna end left bare'],
            ['Mica (buy)', '0.2 mm sheet: McMaster 85825K42, RS PRO']]
    sh.table(x, y0 + 46, ['Part', 'Material / setting'], rows, [170, 650], 14)
    sh.save('monolith_side_parts.png')
    print(f"pack {total:.1f} g; " + ", ".join(f"{k} {v:.1f}" for k, v in m.items()))
    if v1: print(f"v1 {sum(v1.values()):.1f} g")
    print("wrote monolith_side_exploded.png, monolith_side_sections.png, monolith_side_parts.png")
