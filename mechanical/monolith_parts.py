"""Monolith test-print parts (numpy + scipy only).
Run: python3 monolith_parts.py  -> STL files next to this script.
Every part is a stack of flat layers; each layer is described by a 2D inside-test."""
import numpy as np, struct
from scipy.spatial import Delaunay, cKDTree
import monolith_shell as S

# ---------------- parameters (mm) ----------------
CAP_CLEAR    = 0.15   # skirt to tube wall, per side
SKIRT_WALL   = 1.2
BOARD_T      = 1.6
BOARD_CLEAR  = 0.20
BOARD_UP     = 1.0    # board underside above skirt bottom edge
LEDGE        = 1.0    # board stop ledge width and height
CONN_H       = 7.5    # connector height above board (Amphenol lists 7.5 length) - CONFIRM
PORT_L, PORT_W = 9.6, 3.9   # port opening, stadium - PLACEHOLDER, confirm from drawing
CONN_L, CONN_W = 8.94, 3.26 # stand-in connector shell on the dummy board
PORT_X, PORT_Y = 9.5, 11.0  # ports at (+-PORT_X, PORT_Y)
FACE_T       = 1.6
BEZEL_H, BEZEL_W = 0.4, 1.2   # set BEZEL_H = 0 for a flat face
PLATE_L, PLATE_W, PLATE_T = 20.0, 12.0, 1.0   # aluminium heat plate
PLATE_Y      = -3.0
PLATE_LIP    = 1.2
LED_D, LED_SKIN = 2.0, 0.4
LED_XY       = [(-6, -14), (-2, -14), (2, -14), (6, -14)]
BUMP_WALL, BUMP_BAND, BUMP_LIP_T, BUMP_LIP_IN, BUMP_SQUEEZE = 1.6, 8.0, 1.2, 1.5, 0.1
RING_H       = 10.0
# ---------------- derived ----------------
aI, cI, aO, cO = S.a_in, S.c_in, S.a_out, S.c_out
q = aI - cI                                   # corner centre offset, shared by every profile
def prof(a): return (a, a - q)                # rounded square concentric with the tube
SK_O = prof(aI - CAP_CLEAR); SK_I = prof(aI - CAP_CLEAR - SKIRT_WALL)
LEDG = prof(SK_I[0] - LEDGE); BOARD = prof(SK_I[0] - BOARD_CLEAR)
z_sk  = -S.SKIRT_DEPTH
z_bb  = z_sk + BOARD_UP; z_bt = z_bb + BOARD_T
z_face_top = z_bt + CONN_H; z_face_bot = z_face_top - FACE_T

# ---------------- 2D primitives ----------------
def rsq_in(x, y, a, c):
    ax, ay = np.abs(x), np.abs(y); k = a - c
    return (ax <= a) & (ay <= a) & ~((ax > k) & (ay > k) & ((ax-k)**2 + (ay-k)**2 > c*c))
def rsq_pts(a, c, step=0.25):
    k = a - c; P = []
    for i in range(4):
        cs, sn = np.cos(i*np.pi/2), np.sin(i*np.pi/2)
        n = max(2, int(np.ceil(2*k/step))); t = np.linspace(-k, k, n, endpoint=False)
        seg = np.c_[np.full(n, a), t]
        m = max(4, int(np.ceil(c*np.pi/2/step))); u = np.linspace(0, np.pi/2, m, endpoint=False)
        arc = np.c_[k + c*np.cos(u), k + c*np.sin(u)]
        for blk in (seg, arc): P.append(np.c_[blk[:,0]*cs - blk[:,1]*sn, blk[:,0]*sn + blk[:,1]*cs])
    return np.vstack(P)
def circ_in(x, y, cx, cy, r): return (x-cx)**2 + (y-cy)**2 <= r*r
def circ_pts(cx, cy, r, step=0.2):
    n = max(16, int(np.ceil(2*np.pi*r/step))); u = np.linspace(0, 2*np.pi, n, endpoint=False)
    return np.c_[cx + r*np.cos(u), cy + r*np.sin(u)]
def rect_in(x, y, cx, cy, L, W): return (np.abs(x-cx) <= L/2) & (np.abs(y-cy) <= W/2)
def rect_pts(cx, cy, L, W, step=0.25):
    c = [(-L/2,-W/2),(L/2,-W/2),(L/2,W/2),(-L/2,W/2)]; P = []
    for i in range(4):
        a, b = np.array(c[i]), np.array(c[(i+1)%4]); n = max(2, int(np.ceil(np.linalg.norm(b-a)/step)))
        P.append(a + np.linspace(0, 1, n, endpoint=False)[:,None]*(b-a))
    return np.vstack(P) + [cx, cy]
def stad_in(x, y, cx, cy, L, W):
    r = W/2; h = L/2 - r; dx = np.clip(x-cx, -h, h)
    return (x-cx-dx)**2 + (y-cy)**2 <= r*r
def stad_pts(cx, cy, L, W, step=0.2):
    r = W/2; h = L/2 - r; n = max(2, int(np.ceil(2*h/step))); m = max(8, int(np.ceil(np.pi*r/step)))
    t = np.linspace(-h, h, n, endpoint=False); u = np.linspace(-np.pi/2, np.pi/2, m, endpoint=False)
    P = np.vstack([np.c_[t, np.full(n,-r)], np.c_[h + r*np.cos(u), r*np.sin(u)],
                   np.c_[-t, np.full(n, r)], np.c_[-h - r*np.cos(u), -r*np.sin(u)]])
    return P + [cx, cy]

# ---------------- layered mesher ----------------
def _crossings(curves):
    """points where segments of two different curves cross (not at a shared vertex)"""
    X = []
    for i in range(len(curves)):
        for j in range(i + 1, len(curves)):
            P, Q = curves[i], curves[j]
            if (P.min(0) > Q.max(0)).any() or (Q.min(0) > P.max(0)).any(): continue
            a, r = P[:, None, :], (np.roll(P, -1, 0) - P)[:, None, :]
            c, s = Q[None, :, :], (np.roll(Q, -1, 0) - Q)[None, :, :]
            cr = lambda u, v: u[..., 0]*v[..., 1] - u[..., 1]*v[..., 0]
            den = cr(r, s); ok = np.abs(den) > 1e-12
            with np.errstate(divide='ignore', invalid='ignore'):
                t = cr(c - a, s) / den; u = cr(c - a, r) / den
            ok &= (t > 1e-9) & (t < 1 - 1e-9) & (u > 1e-9) & (u < 1 - 1e-9)
            ia, ib = np.nonzero(ok)
            if len(ia): X.append(P[ia] + t[ia, ib][:, None] * (np.roll(P, -1, 0) - P)[ia])
    return np.round(np.vstack(X), 6) if X else np.zeros((0, 2))
def _split_at(c, X, tol=1e-5):
    out = []
    for a, b in zip(c, np.roll(c, -1, axis=0)):
        out.append(a); d = b - a; L2 = d @ d
        if L2 < 1e-18: continue
        s_ = (X - a) @ d / L2; off = np.abs((X[:,0]-a[0])*d[1] - (X[:,1]-a[1])*d[0]) / np.sqrt(L2)
        ok = (off < tol) & (s_ > 1e-7) & (s_ < 1 - 1e-7)
        for i in np.argsort(s_[ok]): out.append(X[ok][i])
    return np.array(out)

def build(curves, zs, solid):
    """curves: list of closed polylines; zs: ascending z levels; solid(k, x, y) -> bool for slab k"""
    curves = [np.round(c, 6) for c in curves]
    X = _crossings(curves)                 # curves may cross: split both at the crossing
    if len(X): curves = [_split_at(c, X) for c in curves]
    for _ in range(6):
        pts = np.unique(np.vstack(curves), axis=0)
        kd = cKDTree(pts); split = []      # split segments at any point lying on them
        for c in curves:
            out = []
            for a, b in zip(c, np.roll(c, -1, axis=0)):
                out.append(a); d = b - a; L = np.linalg.norm(d)
                if L < 1e-9: continue
                cand = pts[kd.query_ball_point((a+b)/2, L/2 + 1e-6)]
                s_ = (cand - a) @ d / (L*L); off = np.abs((cand[:,0]-a[0])*d[1] - (cand[:,1]-a[1])*d[0])/L
                ok = (off < 1e-6) & (s_ > 1e-6) & (s_ < 1 - 1e-6)
                for i in np.argsort(s_[ok]): out.append(cand[ok][i])
            split.append(np.array(out))
        curves = split
        tri = Delaunay(pts)
        idx = {tuple(p): i for i, p in enumerate(pts)}
        E = set()
        for s in tri.simplices:
            for i in range(3): E.add((min(s[i], s[(i+1)%3]), max(s[i], s[(i+1)%3])))
        missing = 0; new = []
        for c in curves:
            nxt = np.roll(c, -1, axis=0); add = []
            for a, b in zip(c, nxt):
                add.append(a)
                ia, ib = idx[tuple(a)], idx[tuple(b)]
                if ia != ib and (min(ia, ib), max(ia, ib)) not in E:
                    add.append(np.round((a+b)/2, 6)); missing += 1
            new.append(np.array(add))
        if not missing: break
        curves = new
    assert missing == 0, f"boundary not conforming ({missing})"
    T = tri.simplices.copy(); P = pts
    a, b, c = P[T[:,0]], P[T[:,1]], P[T[:,2]]
    area = 0.5*((b[:,0]-a[:,0])*(c[:,1]-a[:,1]) - (b[:,1]-a[:,1])*(c[:,0]-a[:,0]))
    cen = (a+b+c)/3
    nsl = len(zs) - 1
    M = np.array([solid(k, cen[:,0], cen[:,1]) for k in range(nsl)]) & (np.abs(area) > 1e-10)
    faces = []
    def p3(i, z): return (P[i,0], P[i,1], z)
    for t in range(len(T)):
        v = T[t] if area[t] > 0 else T[t][::-1]
        col = M[:, t]
        if not col.any(): continue
        for j in range(nsl + 1):
            below = col[j-1] if j > 0 else False; above = col[j] if j < nsl else False
            if below and not above: faces.append((p3(v[0], zs[j]), p3(v[1], zs[j]), p3(v[2], zs[j])))
            if above and not below: faces.append((p3(v[0], zs[j]), p3(v[2], zs[j]), p3(v[1], zs[j])))
        for j in range(3):
            nb = tri.neighbors[t][j]
            e = [T[t][(j+1)%3], T[t][(j+2)%3]]
            if area[t] < 0: e = e[::-1]
            for k in range(nsl):
                if col[k] and not (nb >= 0 and M[k, nb]):
                    A0, B0, B1, A1 = p3(e[0], zs[k]), p3(e[1], zs[k]), p3(e[1], zs[k+1]), p3(e[0], zs[k+1])
                    faces.append((A0, B0, B1)); faces.append((A0, B1, A1))
    return np.round(np.array(faces), 6)

def check(V):
    from collections import Counter
    ed = Counter()
    for t in V:
        k = [tuple(p) for p in t]
        for i in range(3): ed[(k[i], k[(i+1)%3])] += 1
    bad = sum(1 for (a, b), c in ed.items() if c != ed.get((b, a), 0))
    vol = np.einsum('ij,ij->i', V[:,0], np.cross(V[:,1], V[:,2])).sum()/6
    return bad, vol
def write_stl(path, V):
    n = np.cross(V[:,1]-V[:,0], V[:,2]-V[:,0]); n /= np.linalg.norm(n, axis=1)[:,None]
    with open(path, 'wb') as f:
        f.write(path.encode()[:80].ljust(80, b' ')); f.write(struct.pack('<I', len(V)))
        for t, nn in zip(V, n): f.write(struct.pack('<12fH', *nn, *t.ravel(), 0))

# ---------------- parts ----------------
PORTS = [(-PORT_X, PORT_Y), (PORT_X, PORT_Y)]
def top_cap():
    win = (PLATE_L - 2*PLATE_LIP, PLATE_W - 2*PLATE_LIP); pk = (PLATE_L + 0.4, PLATE_W + 0.4)
    zs = [z_sk, z_bt, z_bt + LEDGE, 0.0, z_face_bot, z_face_top - PLATE_T, z_face_top - LED_SKIN, z_face_top]
    if BEZEL_H > 0: zs.append(z_face_top + BEZEL_H)
    cur = [rsq_pts(*p) for p in (prof(aO), SK_O, SK_I, LEDG)]
    cur += [stad_pts(x, y, PORT_L, PORT_W) for x, y in PORTS]
    cur += [stad_pts(x, y, PORT_L + 2*BEZEL_W, PORT_W + 2*BEZEL_W) for x, y in PORTS]
    cur += [rect_pts(0, PLATE_Y, *win), rect_pts(0, PLATE_Y, *pk)] + [circ_pts(x, y, LED_D/2) for x, y in LED_XY]
    def solid(k, x, y):
        port = sum(stad_in(x, y, px, py, PORT_L, PORT_W) for px, py in PORTS) > 0
        if k == 0: return rsq_in(x, y, *SK_O) & ~rsq_in(x, y, *SK_I)
        if k == 1: return rsq_in(x, y, *SK_O) & ~rsq_in(x, y, *LEDG)
        if k == 2: return rsq_in(x, y, *SK_O) & ~rsq_in(x, y, *SK_I)
        if k == 3: return rsq_in(x, y, *prof(aO)) & ~rsq_in(x, y, *SK_I)
        if k in (4, 5, 6):
            s = rsq_in(x, y, *prof(aO)) & ~port
            s &= ~rect_in(x, y, 0, PLATE_Y, *(win if k == 4 else pk))
            if k < 6: s &= ~(sum(circ_in(x, y, lx, ly, LED_D/2) for lx, ly in LED_XY) > 0)
            return s
        return (sum(stad_in(x, y, px, py, PORT_L + 2*BEZEL_W, PORT_W + 2*BEZEL_W) for px, py in PORTS) > 0) & ~port
    return build(cur, zs, solid)

def board_dummy():
    cur = [rsq_pts(*BOARD)] + [stad_pts(x, y, CONN_L, CONN_W) for x, y in PORTS]
    def solid(k, x, y):
        if k == 0: return rsq_in(x, y, *BOARD)
        return sum(stad_in(x, y, px, py, CONN_L, CONN_W) for px, py in PORTS) > 0
    return build(cur, [0, BOARD_T, BOARD_T + CONN_H], solid)

def pcb_dummy():
    p = prof(aI - S.PCB_CLEAR)
    return build([rsq_pts(*p), circ_pts(0, 0, S.VENT_D/2)], [0, S.PCB_T],
                 lambda k, x, y: rsq_in(x, y, *p) & ~circ_in(x, y, 0, 0, S.VENT_D/2))

def cell_dummy(wall=1.2):
    r = S.CELL_D/2
    return build([circ_pts(0, 0, r), circ_pts(0, 0, r - wall)], [0, S.CELL_L],
                 lambda k, x, y: circ_in(x, y, 0, 0, r) & ~circ_in(x, y, 0, 0, r - wall))

def rib_in(x, y):
    t = aI - S.RIB_DEPTH; h = S.RIB_W/2
    return ((np.abs(y) <= h) & (np.abs(x) >= t)) | ((np.abs(x) <= h) & (np.abs(y) >= t))
def fit_ring():
    t = aI - S.RIB_DEPTH; L = S.RIB_DEPTH; cur = [rsq_pts(*prof(aO)), rsq_pts(aI, cI)]
    for sx in (-1, 1):
        cur += [rect_pts(sx*(t + L/2), 0, L, S.RIB_W), rect_pts(0, sx*(t + L/2), S.RIB_W, L)]
    def solid(k, x, y):
        s = rsq_in(x, y, *prof(aO)) & ~rsq_in(x, y, aI, cI)
        return s | (rib_in(x, y) & rsq_in(x, y, aI, cI)) if k == 1 else s
    return build(cur, [0, S.z_rib0, RING_H], solid)

def bumper():
    bi = prof(aO - BUMP_SQUEEZE); bo = prof(aO - BUMP_SQUEEZE + BUMP_WALL); lip = prof(aO - BUMP_LIP_IN)
    def solid(k, x, y):
        return rsq_in(x, y, *bo) & ~rsq_in(x, y, *(lip if k == 0 else bi))
    return build([rsq_pts(*p) for p in (bi, bo, lip)], [0, BUMP_LIP_T, BUMP_LIP_T + BUMP_BAND], solid)

# ---------------- side-board layout (parameters in monolith_shell.py, SB_*) ----------------
def rr_in(x, y, x0, x1, h, rl, rr):
    """rounded rect x0..x1, |y| <= h, corner radius rl on the -x side and rr on the +x side"""
    s = (x >= x0) & (x <= x1) & (np.abs(y) <= h); ay = np.abs(y)
    if rl > 0: s &= ~((x < x0 + rl) & (ay > h - rl) & ((x - x0 - rl)**2 + (ay - h + rl)**2 > rl*rl))
    if rr > 0: s &= ~((x > x1 - rr) & (ay > h - rr) & ((x - x1 + rr)**2 + (ay - h + rr)**2 > rr*rr))
    return s
def rr_pts(x0, x1, h, rl, rr, step=0.25):
    def seg(a, b):
        a, b = np.array(a, float), np.array(b, float); n = max(2, int(np.ceil(np.linalg.norm(b-a)/step)))
        return a + np.linspace(0, 1, n, endpoint=False)[:,None]*(b-a)
    def arc(cx, cy, r, u0):
        if r <= 0: return np.array([[cx, cy]])
        m = max(4, int(np.ceil(r*np.pi/2/step))); u = u0 + np.linspace(0, np.pi/2, m, endpoint=False)
        return np.c_[cx + r*np.cos(u), cy + r*np.sin(u)]
    return np.vstack([seg((x0+rl, -h), (x1-rr, -h)), arc(x1-rr, -h+rr, rr, -np.pi/2),
                      seg((x1, -h+rr), (x1, h-rr)), arc(x1-rr, h-rr, rr, 0),
                      seg((x1-rr, h), (x0+rl, h)), arc(x0+rl, h-rl, rl, np.pi/2),
                      seg((x0, h-rl), (x0, -h+rl)), arc(x0+rl, -h+rl, rl, np.pi)])
def rr_off(p, d):
    """profile grown by d on every side (d < 0 shrinks)"""
    x0, x1, h, rl, rr = p
    return (x0 - d, x1 + d, h + d, max(rl + d, 0), max(rr + d, 0))
def xrect_pts(xa, xb, ya, yb): return rect_pts((xa+xb)/2, (ya+yb)/2, xb-xa, yb-ya)
def xrect_in(x, y, xa, xb, ya, yb): return (x >= xa) & (x <= xb) & (y >= ya) & (y <= yb)

def poly_pts(P, step=0.25):
    """closed polyline through the vertices P, resampled at about step"""
    out = []
    for a, b in zip(P, P[1:] + P[:1]):
        a, b = np.array(a, float), np.array(b, float); n = max(1, int(np.ceil(np.linalg.norm(b-a)/step)))
        out.append(a + np.linspace(0, 1, n, endpoint=False)[:,None]*(b-a))
    return np.vstack(out)

# tray cavity: the cell zone (x < a_in, rounded on -x, grown by the side pad), the board zone (x >= a_in, board width:
# the step is the board's side guide) and the rebates the cover rests in
SB_X, SB_XC, SB_R = S.sb_x_out, S.sb_x_cv0, S.SB_REB
aC, cC = S.a_cav, S.c_cav
def cav_in(x, y):
    return (rr_in(x, y, *S.SB_CAV) | xrect_in(x, y, aI, SB_X, -aI, aI)
            | xrect_in(x, y, SB_XC, SB_X, -(aI + SB_R), aI + SB_R))
def cav_pts(step=0.25):
    m = max(4, int(np.ceil(cC*np.pi/2/step)))
    def arc(cx, cy, u0):
        u = u0 - np.linspace(0, np.pi/2, m, endpoint=False)
        return [tuple(p) for p in np.c_[cx + cC*np.cos(u), cy + cC*np.sin(u)]]
    P = [(SB_X, -(aI + SB_R)), (SB_XC, -(aI + SB_R)), (SB_XC, -aI), (aI, -aI), (aI, -aC)]
    P += arc(-aC + cC, -aC + cC, -np.pi/2) + [(-aC, -aC + cC)] + arc(-aC + cC, aC - cC, np.pi)
    P += [(-aC + cC, aC), (aI, aC), (aI, aI), (SB_XC, aI), (SB_XC, aI + SB_R), (SB_X, aI + SB_R)]
    return poly_pts(P, step)

SB_RIB_T = aI - S.RIB_DEPTH
def rib1_in(x, y): return (np.abs(y) <= S.RIB_W/2) & (x <= -SB_RIB_T)   # -x face only: side insertion
def rib1_pts(): return xrect_pts(-aC, -SB_RIB_T, -S.RIB_W/2, S.RIB_W/2)

# screw pillars in the bottom corners, beside the floor pad, with stepped insert pilots along x
SB_PIL = [(SB_XC - S.SB_INSERT_L - 1.5, SB_XC, sy*aI - (sy > 0)*S.SB_PILLAR_W, sy*aI + (sy < 0)*S.SB_PILLAR_W) for sy in (-1, 1)]
SB_HOLE_N = 16
def hole_slabs():
    r = S.SB_INSERT_D/2; z = S.sb_screw_z - r + np.arange(SB_HOLE_N + 1)*(2*r/SB_HOLE_N)
    zm = (z[:-1] + z[1:])/2; w = np.sqrt(np.maximum(r*r - (zm - S.sb_screw_z)**2, 0))
    return list(z), list(w)
SB_SLOT = (SB_XC, S.sb_x_cv1 + 0.1, -(aI + SB_R), aI + SB_R)    # cover top edge under the lip
def stady_in(x, y, cx, cy, L, W): return stad_in(y, x, cy, cx, L, W)     # long axis along y
def stady_pts(cx, cy, L, W): return stad_pts(cy, cx, L, W)[:, ::-1]
SB_PORTS = [(S.sb_port_x, -S.SB_PORT_Y), (S.sb_port_x, S.SB_PORT_Y)]
SB_PORT_L, SB_PORT_W = S.USB_SEAL_W + 0.2, S.USB_SEAL_H + 0.2
# board top stops: the board's top edge bears on these, so drop loads reach the tray through the board edge, not the USB-C
SB_STOPS = [(aI, SB_XC, S.SB_STOP_Y0, aI), (aI, SB_XC, -aI, -S.SB_STOP_Y0)]   # x to SB_XC: shares edges with the pillars
SB_RUPT = S.sb_pos_caps['bottom']

def side_shell():
    """one-piece tray, open on +x only"""
    hz, hw = hole_slabs()
    zr = S.SB_END_T - S.SB_RUPT_T
    zs = sorted({0.0, zr, S.SB_END_T, S.sb_z_pad1, S.sb_zb1, S.sb_z_top_in, S.sb_z_top_in + S.SB_SLOT, S.SB_H,
                 *[round(z, 6) for z in hz]})
    cur = [rr_pts(*S.SB_OUT), cav_pts(), rib1_pts(), xrect_pts(*SB_SLOT)] + [xrect_pts(*p) for p in SB_PIL + SB_STOPS]
    cur += [stady_pts(x, y, SB_PORT_L, SB_PORT_W) for x, y in SB_PORTS] + [circ_pts(x, y, S.SB_RUPT_D/2) for x, y in SB_RUPT]
    for w in set(np.round(hw, 6)):
        for sy in (-1, 1): cur.append(xrect_pts(SB_XC - S.SB_INSERT_L, SB_XC, sy*S.sb_pillar_y - w, sy*S.sb_pillar_y + w))
    def solid(k, x, y):
        zm = (zs[k] + zs[k+1]) / 2
        out = rr_in(x, y, *S.SB_OUT)
        if zm < zr: return out & ~(sum(circ_in(x, y, cx, cy, S.SB_RUPT_D/2) for cx, cy in SB_RUPT) > 0)
        if zm < S.SB_END_T: return out
        if zm > S.sb_z_top_in:
            s = out & ~(sum(stady_in(x, y, px, py, SB_PORT_L, SB_PORT_W) for px, py in SB_PORTS) > 0)
            return s & ~xrect_in(x, y, *SB_SLOT) if zm < S.sb_z_top_in + S.SB_SLOT else s
        s = (out & ~cav_in(x, y)) | (rib1_in(x, y) & cav_in(x, y))
        if zm > S.sb_zb1: s |= sum(xrect_in(x, y, *p) for p in SB_STOPS) > 0
        if zm < S.sb_z_pad1:
            s |= sum(xrect_in(x, y, *p) for p in SB_PIL) > 0
            for z0, z1, w in zip(hz[:-1], hz[1:], hw):
                if z0 < zm < z1:
                    for sy in (-1, 1): s &= ~xrect_in(x, y, SB_XC - S.SB_INSERT_L, SB_XC, sy*S.sb_pillar_y - w, sy*S.sb_pillar_y + w)
        return s
    return build(cur, zs, solid)

def side_cover():
    """1.0 mm aluminium; screw and vent holes are in monolith_side_cover.dxf, not in this model"""
    p = (S.sb_x_cv0, S.sb_x_cv1, -S.sb_cover_w/2, S.sb_cover_w/2)
    return build([xrect_pts(*p)], [S.sb_cover_z0, S.sb_cover_z1], lambda k, x, y: xrect_in(x, y, *p))

def side_board_dummy():
    """board slab (bottom corners notched) plus the two USB-C envelopes (bottom flush with the board bottom)"""
    xb0, xb1, h, ny = S.sb_xb0, S.sb_xb1, S.sb_board_w/2, S.sb_notch_y
    cx1 = S.sb_port_x + S.USB_UP
    zc0, zc1 = S.sb_zb1 + S.USB_FACE_OUT - S.USB_DEPTH, S.sb_zb1 + S.USB_FACE_OUT
    cur = [xrect_pts(xb0, xb1, -h, h), xrect_pts(xb0, xb1, -ny, ny)]
    for _, py in SB_PORTS:
        ya, yb = py - S.USB_SHELL_W/2, py + S.USB_SHELL_W/2
        cur += [xrect_pts(xb0, xb1, ya, yb), xrect_pts(xb1, cx1, ya, yb)]
    zs = [S.sb_zb0, S.sb_notch_z, zc0, S.sb_zb1, zc1]
    def solid(k, x, y):
        conn = sum(xrect_in(x, y, xb0, cx1, py - S.USB_SHELL_W/2, py + S.USB_SHELL_W/2) for _, py in SB_PORTS) > 0
        board = xrect_in(x, y, xb0, xb1, -h, h)
        return [xrect_in(x, y, xb0, xb1, -ny, ny), board, board | conn, conn][k]
    return build(cur, zs, solid)

# ---- end caps: TPU 95A, the crush zone. One body to print; the zones are slicer modifier volumes ----
# soft: outer SB_CAP_SOFT of the end slab, gyroid ~15 %; firm: the rest of the slab, ~30 %;
# corner noses: ~60 %, they meet corner drops; band: solid walls, it wraps the tray and takes flat side drops.
CAP_FILL = dict(soft=0.15, firm=0.30, corner=0.60, band=1.0)
CAP_BAND_IN = rr_off(S.SB_OUT, -S.SB_CAP_SQUEEZE)
def cap_corner_in(x, y):
    x0, x1, h = S.SB_CAP_OUT[0], S.SB_CAP_OUT[1], S.SB_CAP_OUT[2]; c = S.SB_CAP_CORNER
    return ((x < x0 + c) | (x > x1 - c)) & (np.abs(y) > h - c)
SB_WELL = (S.sb_port_x - S.SB_WELL_H/2, S.sb_port_x + S.SB_WELL_H/2, -S.SB_WELL_W/2, S.SB_WELL_W/2)
def side_cap(zone='body', well=False):
    """bottom cap in place (z < 0 is the crush slab); the top cap is the same part mirrored, with the port well"""
    T, So, B = S.SB_CAP_T, S.SB_CAP_SOFT, S.SB_CAP_BAND
    x0, x1, h = S.SB_CAP_OUT[0], S.SB_CAP_OUT[1], S.SB_CAP_OUT[2]; c = S.SB_CAP_CORNER
    cur = [rr_pts(*S.SB_CAP_OUT), rr_pts(*CAP_BAND_IN)]
    for xa, xb in ((x0, x0 + c), (x1 - c, x1)):
        for ya, yb in ((-h, -h + c), (h - c, h)): cur.append(xrect_pts(xa, xb, ya, yb))
    if well: cur.append(xrect_pts(*SB_WELL))
    def solid(k, x, y):
        s = rr_in(x, y, *S.SB_CAP_OUT)
        if well: s &= ~xrect_in(x, y, *SB_WELL)
        if k == 2: s &= ~rr_in(x, y, *CAP_BAND_IN)
        cn = cap_corner_in(x, y)
        if zone == 'body': return s
        if zone == 'corner': return s & cn
        return s & ~cn & ({'soft': k == 0, 'firm': k == 1, 'band': k == 2}[zone])
    return build(cur, [-T, -T + So, 0.0, B], solid)

def cap_mass(well):
    return sum(abs(check(side_cap(z, well))[1])/1000 * 1.21 * f for z, f in CAP_FILL.items())

# ---- inside parts (no potting) ----
def _cellzone_in(x, y): return rr_in(x, y, *S.SB_CAV) & ~rib1_in(x, y)
def _cellzone_pts(): return [rr_pts(*S.SB_CAV), rib1_pts()]
def end_pad(end, layer='eva'):
    """pads between the cell ends and an end wall: 'eva' (1 mm EVA, top or bottom) or the bottom 'spacer' (printed TPU,
    fills the rest of the floor zone under the EVA); cut-outs over the positive caps leave the button and vent holes
    open into a plenum"""
    caps = S.sb_pos_caps[end]; r = S.SB_VENT_CUT_D/2
    if end == 'top': zs = [S.sb_z_cell1 + S.TAB_T, S.sb_z_top_in]
    elif layer == 'eva': zs = [S.sb_z_pad1 - S.SB_EVA_T, S.sb_z_pad1]
    else: zs = [S.SB_END_T, S.sb_z_pad1 - S.SB_EVA_T]
    cur = _cellzone_pts() + [circ_pts(x, y, r) for x, y in caps]
    return build(cur, zs, lambda k, x, y: _cellzone_in(x, y) & ~(sum(circ_in(x, y, cx, cy, r) for cx, cy in caps) > 0))
CELL_ENV = (-aI, aI + 1.0, aI, cI, 0.0)      # cell block envelope (square on the board side)
def side_pad():
    """SB_SIDE_PAD fish paper liner round the -x and +-y faces of the cells, slotted for the rib"""
    cur = _cellzone_pts() + [rr_pts(*CELL_ENV)]
    return build(cur, [S.sb_z_cell0, S.sb_z_cell1], lambda k, x, y: _cellzone_in(x, y) & ~rr_in(x, y, *CELL_ENV))
def mica_cross():
    t = S.SB_SEP_T/2; a = (-SB_RIB_T + 0.2, aI - 0.2, -t, t); b = (-t, t, -(aI - 0.2), aI - 0.2)
    return build([xrect_pts(*a), xrect_pts(*b)], [S.sb_z_cell0 + 1.0, S.sb_z_cell1 - 1.0],
                 lambda k, x, y: xrect_in(x, y, *a) | xrect_in(x, y, *b))
def insulator():
    p = (S.sb_xb0 - 0.2, S.sb_xb0, -(aI - 0.2), aI - 0.2)   # 0.2 mm fish paper on the board's back
    return build([xrect_pts(*p)], [S.sb_z_cell0 - S.TAB_T, S.sb_z_cell1 + S.TAB_T], lambda k, x, y: xrect_in(x, y, *p))
def hold_pads():
    ps = [(S.sb_port_x + S.USB_UP, SB_XC, py - 4.5, py + 4.5) for _, py in SB_PORTS]
    return build([xrect_pts(*p) for p in ps], [S.SB_H - S.USB_DEPTH + 0.5, S.sb_z_top_in],
                 lambda k, x, y: sum(xrect_in(x, y, *p) for p in ps) > 0)
def board_shim():
    p = (S.sb_xb0, S.sb_xb1, -(S.sb_notch_y - 0.2), S.sb_notch_y - 0.2)
    return build([xrect_pts(*p)], [S.SB_END_T, S.sb_zb0], lambda k, x, y: xrect_in(x, y, *p))
def cell_solid():
    r = S.CELL_D/2
    return build([circ_pts(0, 0, r, 0.4)], [0, S.CELL_L], lambda k, x, y: circ_in(x, y, 0, 0, r))

PARTS = [('monolith_top_cap', top_cap, 1.20, 1), ('monolith_top_board_dummy', board_dummy, 1.2, 1),
         ('monolith_bottom_pcb_dummy', pcb_dummy, 1.2, 1), ('monolith_cell_dummy', cell_dummy, 1.2, 4),
         ('monolith_fit_ring', fit_ring, 1.2, 1), ('monolith_end_bumper', bumper, 1.21, 2)]
# (file, mesh, density g/cm3 as built, qty). Caps: the print body (mass from its zone fills); mod_*: slicer modifiers.
SIDE_PARTS = [('monolith_side_shell', side_shell, 1.18, 1), ('monolith_side_cover', side_cover, 2.70, 1),
              ('monolith_side_board_dummy', side_board_dummy, 1.2, 1),
              ('monolith_side_cap_bottom', lambda: side_cap('body'), None, 1),
              ('monolith_side_cap_top', lambda: side_cap('body', True), None, 1),
              ('monolith_side_cap_bottom_mod_soft', lambda: side_cap('soft'), 0, 1),
              ('monolith_side_cap_bottom_mod_corner', lambda: side_cap('corner'), 0, 1),
              ('monolith_side_cap_top_mod_soft', lambda: side_cap('soft', True), 0, 1),
              ('monolith_side_cap_top_mod_corner', lambda: side_cap('corner', True), 0, 1),
              ('monolith_side_floor_spacer', lambda: end_pad('bottom', 'spacer'), 0.30, 1),
              ('monolith_side_eva_floor', lambda: end_pad('bottom'), 0.20, 1),
              ('monolith_side_eva_top', lambda: end_pad('top'), 0.20, 1),
              ('monolith_side_liner', side_pad, 1.2, 1), ('monolith_side_mica', mica_cross, 2.8, 1),
              ('monolith_side_insulator', insulator, 1.2, 1), ('monolith_side_usb_hold', hold_pads, 0.20, 1),
              ('monolith_side_shim', board_shim, 1.21, 1)]
if __name__ == '__main__':
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'     # top | side | all
    todo = (PARTS if which in ('top', 'all') else []) + (SIDE_PARTS if which in ('side', 'all') else [])
    for name, fn, rho, qty in todo:
        V = fn(); bad, vol = check(V); write_stl(name + '.stl', V)
        lo, hi = V.reshape(-1, 3).min(0), V.reshape(-1, 3).max(0)
        g = cap_mass(name.endswith('top')) if rho is None else vol/1000*rho
        print(f"{name:30s} x{qty} tris {len(V):6d} open-edges {bad} size {np.round(hi-lo,2)} vol {vol/1000:5.2f} cm3 ~{g:4.1f} g")
    print(f"cap: skirt bottom z {z_sk}, board {z_bb}..{z_bt}, face {z_face_bot}..{z_face_top} (z=0 is the tube rim)")
    print(f"skirt outer {2*SK_O[0]:.2f} R{SK_O[1]:.2f}; board outline {2*BOARD[0]:.2f} R{BOARD[1]:.2f}")
