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

if __name__ == '__main__':
    write_stl('monolith_shell.stl'); write_dxf('monolith_bottom_pcb.dxf')
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
