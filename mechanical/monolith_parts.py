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
def build(curves, zs, solid):
    """curves: list of closed polylines; zs: ascending z levels; solid(k, x, y) -> bool for slab k"""
    curves = [np.round(c, 6) for c in curves]
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

PARTS = [('monolith_top_cap', top_cap, 1.20, 1), ('monolith_top_board_dummy', board_dummy, 1.2, 1),
         ('monolith_bottom_pcb_dummy', pcb_dummy, 1.2, 1), ('monolith_cell_dummy', cell_dummy, 1.2, 4),
         ('monolith_fit_ring', fit_ring, 1.2, 1), ('monolith_end_bumper', bumper, 1.21, 2)]
if __name__ == '__main__':
    for name, fn, rho, qty in PARTS:
        V = fn(); bad, vol = check(V); write_stl(name + '.stl', V)
        lo, hi = V.reshape(-1, 3).min(0), V.reshape(-1, 3).max(0)
        print(f"{name:28s} x{qty} tris {len(V):6d} open-edges {bad} size {np.round(hi-lo,2)} vol {vol/1000:5.2f} cm3 ~{vol/1000*rho:4.1f} g")
    print(f"cap: skirt bottom z {z_sk}, board {z_bb}..{z_bt}, face {z_face_bot}..{z_face_top} (z=0 is the tube rim)")
    print(f"skirt outer {2*SK_O[0]:.2f} R{SK_O[1]:.2f}; board outline {2*BOARD[0]:.2f} R{BOARD[1]:.2f}")
