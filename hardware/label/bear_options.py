"""Bear options for the back of the label, in the --bl (Borderlands) style, each drawn in place on the label.
Each bear is built from overlapping shapes (ellipses, limbs = hulls of two circles, fur points) unioned into one
silhouette; the layer renderer gives it a lit upper-left rim, a hatched lower-right shadow and a hand-inked outline.
Run: python bear_options.py   -> out/bear_options.png  (numbered sheet, each option on the real label background)
                                  out/bear_options_angular.png  (variations of option 9, the angular bear)"""
import os, sys, math
sys.argv = [sys.argv[0], '--bl']
import numpy as np
import monolith_label as M
from manifold3d import CrossSection as CS, FillRule

INK = M.INK
BR, BR_SH, BR_HI, MUZ, CREAM = M.C['bear'], M.C['bear_sh'], '#a46c3a', '#c08a55', M.C['cream']

# ---------------- shapes (local mm, x right, y up = negative, feet on y = 0) ----------------
def E(cx, cy, rx, ry=None, rot=0.0):
    return CS.circle(1.0, 72).scale((rx, ry or rx)).rotate(rot).translate((cx, cy))
def LIMB(p, q, r1, r2):
    return CS.batch_hull([CS.circle(r1, 40).translate(p), CS.circle(r2, 40).translate(q)])
def P(pts):
    return CS([pts], FillRule.EvenOdd)
def U(*parts):
    r = parts[0]
    for q in parts[1:]: r = r + q
    return r
def fringe(x0, x1, y, n, h=0.6, lean=-0.25):
    """shaggy fur: n points hanging below y between x0 and x1"""
    w = (x1 - x0) / n
    return U(*[P([(x0 + k * w - 0.1, y - 0.7), (x0 + (k + 1) * w + 0.1, y - 0.7), (x0 + (k + 0.5) * w + lean, y + h)]) for k in range(n)])
def bz(p0, p1, p2, p3, n=14):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = map(np.array, (p0, p1, p2, p3))
    return [tuple(v) for v in (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3]

# ---------------- renderer ----------------
class Bear:
    def __init__(self, x, yb, k=1.0):
        self.x, self.yb, self.k = x, yb, k
    def T(self, pts): return [(self.x + u * self.k, self.yb + v * self.k) for u, v in pts]
    def rings(self, cs): return [self.T([tuple(p) for p in r]) for r in cs.to_polygons()]
    def d(self, cs): return ''.join('M' + ' L'.join(f'{a:.3f} {b:.3f}' for a, b in r) + 'Z' for r in self.rings(cs))
    def fill(self, cs, colour): M.add(f'<path d="{self.d(cs)}" fill="{colour}"/>')
    def layer(self, cs, fill=BR, shade=BR_SH, hi=BR_HI, sw=0.42, cel=(0.9, 1.0), rim=(0.45, 0.55), belly=None, hatch=True):
        """one inked, cel-shaded part: base colour, lit rim upper left, hatched shadow lower right, brush outline"""
        self.fill(cs, fill)
        if hi: self.fill(cs - cs.translate(rim), hi)
        if shade:
            sh = cs - cs.translate((-cel[0], -cel[1]))
            if belly is not None: sh = sh + (cs ^ CS.square((60, 20)).translate((-20, belly)))
            self.fill(sh, shade)
            if hatch:
                for r in self.rings(sh):
                    if abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(r, r[1:] + r[:1]))) > 0.6:
                        M.hatch_ink(r, step=0.7, ang=62, sw=0.17, maxlen=2.6)
        for r in self.rings(cs): M.ink(r, sw, closed=True)
    def line(self, pts, sw=0.22): M.ink(self.T(pts), sw)
    def blob(self, cs, colour=INK): self.fill(cs, colour)
    def eye(self, u, v, r=0.3, glint=CREAM):
        (a, b), = self.T([(u, v)])
        M.add(f'<circle cx="{a:.3f}" cy="{b:.3f}" r="{r * self.k:.3f}" fill="{INK}"/>'
              f'<circle cx="{a + 0.08 * self.k:.3f}" cy="{b - 0.08 * self.k:.3f}" r="{0.1 * self.k:.3f}" fill="{glint}"/>')
    def claws(self, u, v, n=3, dx=0.36, dir=(0.25, 0.32)):
        rng = M._rng(u, v, 9); d = ''
        for i in range(n):
            (a, b), (c, e) = self.T([(u + i * dx, v), (u + i * dx + dir[0], v + dir[1])])
            d += M.taper((a, b), (c, e), 0.22 * self.k, rng)
        M.add(f'<path d="{d}" fill="{CREAM}"/>')
    def grizzle(self, spots):
        """pale flicks on the hump"""
        rng = M._rng(len(spots), 5); d = ''
        for u, v in spots:
            (a, b), (c, e) = self.T([(u, v), (u + 0.7, v + 0.45)])
            d += M.taper((a, b), (c, e), 0.3 * self.k, rng)
        M.add(f'<path d="{d}" fill="#d9a66e"/>')

# ---------------- the options ----------------
def walker_geo(lift=False):
    far = U(LIMB((11.4, -4.2), (11.0, -1.0), 1.45, 1.1), E(11.5, -0.55, 1.35, 0.55),
            LIMB((6.4, -4.4), (6.9, -1.0), 1.6, 1.1), E(7.3, -0.55, 1.35, 0.55), E(16.0, -9.0, 0.75))
    fore = (U(LIMB((14.0, -5.6), (15.2, -2.8), 1.85, 1.25), E(15.9, -2.3, 1.35, 0.6, 35)) if lift else
            U(LIMB((14.0, -5.6), (14.7, -1.0), 1.85, 1.3), E(15.3, -0.6, 1.6, 0.6)))
    near = U(E(9.0, -6.4, 6.6, 3.4), E(4.2, -6.6, 3.5, 3.3), E(12.0, -8.6, 3.3, 2.6, -15),
             LIMB((13.8, -7.6), (16.4, -7.2), 2.5, 2.0), E(17.2, -7.2, 2.2, 1.95),
             LIMB((18.4, -6.7), (20.7, -6.2), 1.15, 0.75), E(16.8, -9.1, 0.8), fore,
             LIMB((4.3, -5.6), (3.8, -1.0), 2.3, 1.25), E(4.3, -0.6, 1.65, 0.6), fringe(5.6, 12.6, -3.0, 9))
    return far, near

def walker_face(b, lift=False):
    b.blob(E(19.7, -6.45, 1.35, 0.72, -10), MUZ)
    b.blob(E(21.25, -6.4, 0.42, 0.35))                                      # nose
    b.blob(E(16.85, -9.05, 0.38), BR_SH)                                    # inner ear
    b.eye(17.9, -7.85)
    b.line([(20.9, -5.8), (20.0, -5.6), (19.1, -5.65)], 0.2)                # mouth
    b.line(bz((17.2, -8.5), (17.6, -8.75), (18.1, -8.7), (18.5, -8.4)), 0.2)  # brow
    b.line(bz((12.6, -10.6), (13.5, -8.6), (13.7, -6.6), (13.5, -4.7)), 0.24)  # shoulder
    b.line(bz((5.4, -9.1), (6.5, -7.7), (6.8, -5.7), (6.2, -3.9)), 0.24)    # haunch
    b.grizzle([(10.4, -10.4), (11.6, -10.9), (12.6, -10.5), (11.0, -9.6), (9.6, -9.7)])
    if lift: b.claws(16.6, -2.1, dir=(0.35, 0.15))
    else: b.claws(15.9, -0.25)
    b.claws(4.9, -0.25)

def opt_walker(x, yb, s):
    b = Bear(x, yb); far, near = walker_geo()
    b.layer(far, fill=BR_SH, shade='#3a2210', hi=None, sw=0.32)
    b.layer(near, belly=-3.6); walker_face(b)

def rearing_geo():
    far = U(LIMB((9.6, -4.5), (10.2, -1.0), 1.6, 1.2), E(10.8, -0.55, 1.5, 0.6),
            LIMB((10.4, -12.6), (13.4, -14.4), 1.1, 0.9), E(13.9, -14.7, 1.0, 0.85), E(10.2, -18.3, 0.7))
    near = U(E(7.6, -5.0, 3.6, 3.2), E(8.4, -9.6, 3.3, 5.0, -12), E(9.2, -13.6, 2.9, 2.3, -20),
             LIMB((9.8, -14.6), (11.0, -16.0), 2.0, 1.8), E(11.4, -16.4, 2.1, 1.9, -15),
             LIMB((12.6, -17.1), (14.4, -17.9), 1.0, 0.7), LIMB((12.3, -15.6), (13.9, -15.6), 0.75, 0.45),
             E(10.9, -18.2, 0.8), LIMB((10.2, -12.0), (12.8, -10.4), 1.35, 1.0), E(13.4, -10.2, 1.05, 0.9),
             LIMB((6.8, -4.6), (6.2, -1.0), 2.0, 1.3), E(6.8, -0.6, 1.7, 0.6),
             fringe(10.4, 12.6, -10.3, 4, h=0.45))
    return far, near

def opt_rearing(x, yb, s):
    b = Bear(x + 2.0, yb)
    far, near = rearing_geo()
    b.layer(far, fill=BR_SH, shade='#3a2210', hi=None, sw=0.32)
    b.layer(near)
    b.blob(P([(12.5, -16.45), (14.5, -17.45), (14.0, -15.9), (12.6, -15.75)]))           # open mouth
    b.blob(E(13.1, -15.95, 0.55, 0.22, 10), '#a8443a')                                     # tongue
    for (u, v, du, dv) in ((14.05, -17.3, 0.12, 0.5), (13.65, -17.1, 0.1, 0.4), (13.75, -15.85, 0.08, -0.4)):
        b.blob(P([(u - 0.13, v), (u + 0.13, v), (u + du, v + dv)]), CREAM)               # fangs
    b.blob(E(14.85, -18.05, 0.38, 0.32))                                                   # nose
    b.blob(E(10.95, -18.15, 0.36), BR_SH)
    b.eye(12.05, -17.1, 0.26)
    b.line(bz((11.4, -17.8), (11.8, -17.95), (12.3, -17.8), (12.6, -17.5)), 0.2)
    b.line(bz((7.0, -11.8), (7.4, -9.6), (7.6, -7.6), (7.2, -6.2)), 0.24)
    b.grizzle([(8.4, -15.0), (9.4, -15.4), (8.0, -13.8), (9.0, -14.1)])
    b.claws(13.9, -10.2, dir=(0.35, 0.15)); b.claws(7.4, -0.25)

def opt_headon(x, yb, s):
    b = Bear(x + 1.0, yb)
    body = U(E(10, -7.2, 6.2, 4.0), E(10, -9.6, 4.6, 2.6),
             LIMB((6.4, -5.5), (5.8, -1.0), 2.0, 1.55), E(5.7, -0.7, 2.0, 0.75),
             LIMB((13.6, -5.5), (14.2, -1.0), 2.0, 1.55), E(14.3, -0.7, 2.0, 0.75), fringe(7.6, 12.4, -3.6, 6, lean=0))
    head = U(E(10, -7.0, 3.5, 3.0), E(7.0, -9.7, 1.15), E(13.0, -9.7, 1.15))
    b.layer(body, belly=-3.8)
    b.line(bz((7.6, -3.6), (7.8, -2.4), (7.7, -1.4), (7.4, -0.9)), 0.22)
    b.line(bz((12.4, -3.6), (12.2, -2.4), (12.3, -1.4), (12.6, -0.9)), 0.22)
    b.layer(head, cel=(0.6, 0.7))
    b.blob(E(7.05, -9.7, 0.55), BR_SH); b.blob(E(12.95, -9.7, 0.55), BR_SH)
    b.layer(E(10, -5.6, 1.85, 1.35), fill=MUZ, shade='#9a6a3c', hi=None, sw=0.28, cel=(0.4, 0.5), hatch=False)
    b.blob(E(10, -6.25, 0.8, 0.52))                                                        # nose
    b.line([(10, -5.8), (10, -5.0)], 0.2); b.line(bz((8.9, -4.75), (9.4, -4.55), (9.7, -4.8), (10, -5.0)), 0.2)
    b.line(bz((11.1, -4.75), (10.6, -4.55), (10.3, -4.8), (10, -5.0)), 0.2)
    b.eye(8.55, -7.9); b.eye(11.45, -7.9)
    b.line([(7.8, -8.75), (9.2, -8.35)], 0.24); b.line([(12.2, -8.75), (10.8, -8.35)], 0.24)    # brows
    b.grizzle([(6.6, -10.2), (13.0, -10.6), (8.4, -10.9), (11.6, -11.0)])
    for cx in (4.7, 13.3): b.claws(cx, -0.2, n=4, dx=0.45, dir=(0.0, 0.35))

def sitting_geo():
    far = U(LIMB((9.2, -7.5), (9.6, -1.0), 1.2, 1.0), E(10.1, -0.55, 1.2, 0.5), E(9.7, -14.4, 0.65))
    near = U(E(5.6, -3.6, 4.4, 3.4), E(8.0, -7.8, 3.1, 4.6, -18), LIMB((8.8, -11.0), (10.2, -12.6), 2.1, 1.8),
             E(10.6, -12.9, 2.15, 1.9), LIMB((11.8, -12.5), (13.8, -12.0), 1.05, 0.72), E(10.2, -14.75, 0.78),
             LIMB((10.0, -8.0), (10.9, -1.0), 1.35, 1.15), E(11.5, -0.55, 1.35, 0.55), E(7.4, -0.75, 2.3, 0.75))
    return far, near

def opt_sitting(x, yb, s):
    b = Bear(x + 3.0, yb)
    far, near = sitting_geo()
    b.layer(far, fill=BR_SH, shade='#3a2210', hi=None, sw=0.32)
    b.layer(near)
    b.blob(E(12.9, -12.25, 1.25, 0.7, -8), MUZ); b.blob(E(14.35, -12.15, 0.4, 0.34))
    b.blob(E(10.25, -14.7, 0.37), BR_SH); b.eye(11.35, -13.5)
    b.line([(14.1, -11.6), (13.3, -11.45), (12.6, -11.5)], 0.2)
    b.line(bz((2.6, -5.6), (4.4, -6.9), (7.4, -6.4), (8.6, -4.0)), 0.24)               # haunch
    b.line(bz((9.0, -10.2), (9.8, -9.0), (10.0, -8.0), (9.9, -7.0)), 0.22)
    b.grizzle([(8.0, -11.6), (8.8, -12.2), (7.4, -10.6)])
    b.claws(12.0, -0.25); b.claws(8.6, -0.3)

def forager_geo():
    far = U(LIMB((10.8, -4.0), (10.6, -1.0), 1.4, 1.1), E(11.1, -0.55, 1.3, 0.55),
            LIMB((6.0, -4.4), (6.5, -1.0), 1.6, 1.1), E(6.9, -0.55, 1.35, 0.55), E(15.7, -6.3, 0.65))
    near = U(E(3.8, -7.4, 3.6, 3.5), E(8.0, -6.8, 5.6, 3.4, 6), E(10.9, -8.5, 3.2, 2.7, -10),
             LIMB((12.8, -7.6), (15.8, -4.4), 2.4, 1.6), E(16.8, -3.9, 2.1, 1.75, 38),
             LIMB((17.6, -3.0), (19.0, -1.0), 1.0, 0.65), E(16.3, -5.9, 0.75),
             LIMB((12.6, -5.2), (12.9, -1.0), 1.8, 1.3), E(13.5, -0.6, 1.55, 0.6),
             LIMB((3.8, -6.0), (3.4, -1.0), 2.3, 1.25), E(3.9, -0.6, 1.65, 0.6), fringe(5.2, 11.6, -3.2, 7))
    return far, near

def opt_forager(x, yb, s):
    b = Bear(x, yb)
    far, near = forager_geo()
    b.layer(far, fill=BR_SH, shade='#3a2210', hi=None, sw=0.32)
    b.layer(near, belly=-3.8)
    b.blob(E(18.35, -1.9, 0.72, 1.15, 35), MUZ); b.blob(E(19.15, -0.75, 0.4, 0.33))
    b.blob(E(16.35, -5.85, 0.36), BR_SH); b.eye(17.35, -4.15, 0.27)
    b.line(bz((16.6, -4.9), (17.0, -5.05), (17.5, -4.9), (17.8, -4.6)), 0.2)
    b.line(bz((11.4, -10.6), (12.3, -8.8), (12.4, -6.8), (12.2, -5.0)), 0.24)
    b.line(bz((5.0, -10.0), (6.1, -8.6), (6.4, -6.4), (5.8, -4.2)), 0.24)
    b.line([(19.9, -1.4), (20.6, -1.75)], 0.18); b.line([(20.0, -0.6), (20.8, -0.6)], 0.18)   # sniffs
    b.grizzle([(9.4, -10.6), (10.6, -11.0), (11.7, -10.6), (10.0, -9.8)])
    b.claws(14.1, -0.25); b.claws(4.5, -0.25)

def roar_geo():
    far = U(LIMB((11.4, -4.2), (11.0, -1.0), 1.45, 1.1), E(11.5, -0.55, 1.35, 0.55),
            LIMB((6.4, -4.4), (6.9, -1.0), 1.6, 1.1), E(7.3, -0.55, 1.35, 0.55), E(15.2, -11.5, 0.7))
    near = U(E(9.0, -6.4, 6.6, 3.4), E(4.2, -6.6, 3.5, 3.3), E(11.8, -8.6, 3.3, 2.7, -15),
             LIMB((13.6, -8.0), (16.0, -9.6), 2.5, 2.0), E(16.8, -10.0, 2.1, 1.9, -20),
             LIMB((17.9, -10.8), (20.1, -11.6), 1.0, 0.68), LIMB((17.7, -9.2), (19.6, -9.0), 0.8, 0.45),
             E(16.0, -11.8, 0.8), LIMB((14.0, -5.6), (14.7, -1.0), 1.85, 1.3), E(15.3, -0.6, 1.6, 0.6),
             LIMB((4.3, -5.6), (3.8, -1.0), 2.3, 1.25), E(4.3, -0.6, 1.65, 0.6), fringe(5.6, 12.6, -3.0, 9))
    return far, near

def opt_roar(x, yb, s):
    b = Bear(x - 1.8, yb)
    far, near = roar_geo()
    b.layer(far, fill=BR_SH, shade='#3a2210', hi=None, sw=0.32)
    b.layer(near, belly=-3.6)
    b.blob(P([(17.9, -10.05), (20.4, -11.05), (19.9, -9.3), (18.0, -9.45)]))
    b.blob(E(18.8, -9.55, 0.6, 0.22), '#a8443a')
    for (u, v, du, dv) in ((19.85, -10.95, 0.1, 0.5), (19.2, -10.75, 0.08, 0.4), (19.45, -9.3, 0.08, -0.45)):
        b.blob(P([(u - 0.13, v), (u + 0.13, v), (u + du, v + dv)]), CREAM)
    b.blob(E(20.6, -11.75, 0.38, 0.32)); b.blob(E(16.05, -11.75, 0.36), BR_SH)
    b.eye(17.45, -10.95, 0.27)
    b.line(bz((16.8, -11.5), (17.2, -11.75), (17.7, -11.7), (18.0, -11.35)), 0.22)
    b.line(bz((12.4, -10.6), (13.4, -8.6), (13.7, -6.6), (13.5, -4.7)), 0.24)
    b.line(bz((5.4, -9.1), (6.5, -7.7), (6.8, -5.7), (6.2, -3.9)), 0.24)
    b.grizzle([(10.2, -10.4), (11.4, -10.9), (12.6, -10.6), (10.8, -9.6)])
    b.claws(15.9, -0.25); b.claws(4.9, -0.25)

def cub_geo():
    cfar = U(LIMB((4.4, -2.0), (4.5, -0.6), 0.65, 0.5), E(4.8, -0.35, 0.65, 0.32), LIMB((2.6, -2.0), (2.8, -0.6), 0.7, 0.5),
             E(3.1, -0.35, 0.65, 0.32), E(5.6, -5.5, 0.42))
    cnear = U(E(3.2, -3.1, 2.5, 1.8), E(5.9, -4.2, 1.35, 1.25), LIMB((6.4, -4.0), (7.6, -3.7), 0.6, 0.42),
              E(6.0, -5.45, 0.5), LIMB((5.0, -2.4), (5.3, -0.6), 0.75, 0.6), E(5.6, -0.35, 0.75, 0.35),
              LIMB((1.8, -2.4), (1.6, -0.6), 0.85, 0.6), E(1.9, -0.35, 0.75, 0.35))
    return cfar, cnear

def opt_mother_cub(x, yb, s):
    m = Bear(x + 6.0, yb, 0.82); far, near = walker_geo()
    m.layer(far, fill=BR_SH, shade='#3a2210', hi=None, sw=0.32); m.layer(near, belly=-3.6); walker_face(m)
    c = Bear(x - 2.0, yb, 1.0)
    cfar, cnear = cub_geo()
    c.layer(cfar, fill=BR_SH, shade='#3a2210', hi=None, sw=0.25)
    c.layer(cnear, sw=0.34, cel=(0.5, 0.6), rim=(0.3, 0.35))
    c.blob(E(7.0, -3.85, 0.75, 0.45), MUZ); c.blob(E(7.85, -3.75, 0.25, 0.21)); c.blob(E(6.0, -5.4, 0.24), BR_SH)
    c.eye(6.45, -4.55, 0.2)

def opt_shadow(x, yb, s):
    b = Bear(x, yb); far, near = walker_geo(lift=True)
    b.layer(far, fill='#140c07', shade=None, hi=None, sw=0.32)
    b.layer(near, fill='#22150c', shade=None, hi='#c4874a', rim=(0.55, 0.7), sw=0.42)
    b.blob(E(17.9, -7.85, 0.34), '#f0a83c'); b.blob(E(17.98, -7.93, 0.12), '#fff1c8')    # glowing eye
    b.blob(E(21.25, -6.4, 0.42, 0.35), '#0a0604')
    b.grizzle([(10.4, -10.4), (11.6, -10.9), (12.6, -10.5), (9.4, -10.0)])
    b.claws(16.6, -2.1, dir=(0.35, 0.15)); b.claws(4.9, -0.25)

def opt_angular(x, yb, s):
    b = Bear(x, yb)
    sil = [(0.6, 0), (0.4, -3.4), (0.8, -7.4), (2.4, -9.6), (6.0, -9.9), (9.4, -10.4), (11.6, -11.6), (13.4, -10.8),
           (14.6, -9.6), (16.4, -9.4), (17.4, -8.8), (19.2, -7.6), (21.0, -6.6), (20.9, -5.9), (18.6, -5.4), (16.4, -5.0),
           (15.4, -4.2), (15.2, -1.0), (16.6, -0.6), (16.6, 0), (13.4, 0), (13.0, -2.8), (12.2, -3.4), (11.0, -2.6),
           (10.2, -3.3), (9.0, -2.7), (8.0, -3.3), (6.8, -2.7), (5.6, -3.2), (5.0, -1.0), (5.6, -0.5), (5.4, 0)]
    far = U(P([(6.2, -3.4), (7.0, -0.7), (8.4, -0.5), (8.4, 0), (6.2, 0), (5.8, -3.0)]),
            P([(11.2, -3.0), (11.0, -0.7), (12.2, -0.5), (12.2, 0), (10.2, 0), (10.4, -3.0)]),
            P([(15.2, -9.3), (15.4, -10.5), (16.1, -10.4), (16.2, -9.3)]))
    body = U(P(sil), P([(15.8, -9.3), (16.1, -10.7), (17.0, -10.5), (17.2, -9.1)]))
    b.layer(far, fill=BR_SH, shade=None, hi=None, sw=0.3)
    b.fill(body, BR)
    lit = [[(0.8, -7.4), (2.4, -9.6), (6.0, -9.9), (4.4, -7.0)], [(9.4, -10.4), (11.6, -11.6), (11.4, -8.4), (8.4, -8.6)],
           [(17.4, -8.8), (19.2, -7.6), (18.2, -6.6), (16.6, -7.2)], [(14.6, -9.6), (16.4, -9.4), (16.6, -7.2), (14.4, -7.8)]]
    dark = [[(5.6, -3.2), (6.8, -2.7), (8.0, -3.3), (9.0, -2.7), (10.2, -3.3), (11.0, -2.6), (12.2, -3.4), (13.0, -2.8),
             (13.6, -5.2), (6.0, -5.4)], [(11.6, -11.6), (13.4, -10.8), (14.6, -9.6), (14.4, -7.8), (13.6, -5.2), (11.4, -8.4)],
            [(16.4, -5.0), (18.6, -5.4), (18.2, -6.6), (16.6, -7.2)], [(13.0, -2.8), (13.4, 0), (15.2, -1.0), (15.4, -4.2), (13.6, -5.2)],
            [(0.4, -3.4), (0.6, 0), (5.4, 0), (5.0, -1.0), (5.6, -3.2), (4.4, -7.0), (0.8, -7.4)]]
    for f in lit: b.blob(P(f), BR_HI)
    for f in dark:
        b.blob(P(f), BR_SH); M.hatch_ink(b.T(f), step=0.75, ang=62, sw=0.17, maxlen=2.4)
    for f in lit + dark: b.line(f + f[:1], 0.15)
    for r in b.rings(body): M.ink(r, 0.42, closed=True)
    b.blob(P([(20.4, -6.9), (21.1, -6.6), (21.0, -6.0), (20.5, -6.2)]))
    b.blob(P([(17.7, -8.3), (18.2, -8.2), (18.0, -7.85)]), INK)
    b.claws(15.8, -0.25); b.claws(4.4, -0.25)

def opt_peeker(x, yb, s):
    b = Bear(x + 1.0, yb + 0.6)
    body = U(E(10, -3.6, 7.2, 4.6), E(9.0, -6.6, 5.0, 2.8))
    head = U(E(10.6, -9.4, 3.4, 3.0), LIMB((11.8, -8.3), (13.6, -7.6), 1.65, 1.2), E(8.0, -11.9, 1.1), E(12.7, -12.3, 1.0))
    b.layer(body, belly=-2.0)
    b.layer(head, cel=(0.7, 0.8))
    b.blob(E(8.05, -11.85, 0.52), BR_SH); b.blob(E(12.7, -12.25, 0.48), BR_SH)
    b.layer(LIMB((12.2, -7.9), (13.6, -7.5), 1.15, 0.9), fill=MUZ, shade='#9a6a3c', hi=None, sw=0.26, cel=(0.4, 0.5), hatch=False)
    b.blob(E(14.15, -7.95, 0.6, 0.45)); b.eye(10.3, -9.8); b.eye(12.6, -9.7, 0.27)
    b.line(bz((12.4, -6.9), (13.0, -6.75), (13.6, -6.8), (14.1, -7.1)), 0.2)
    b.line([(9.5, -10.7), (10.9, -10.45)], 0.24); b.line([(12.0, -10.5), (13.1, -10.6)], 0.22)
    b.grizzle([(7.2, -8.6), (8.4, -8.9), (6.2, -7.6), (13.4, -11.1)])
    mound = [(-3 + t, -0.9 - 1.4 * math.sin(math.pi * t / 27) ** 0.6) for t in np.arange(0, 27.01, 0.9)]
    poly_ = b.T(mound + [(24, 3), (-3, 3)])
    M.poly(poly_, M.C['hill'], 0); M.ink(b.T(mound), 0.5)
    for cx, cy in ((5.0, -2.2), (15.2, -2.4)):                         # paws over the mound
        b.layer(E(cx, cy, 1.7, 0.95), cel=(0.4, 0.5), sw=0.36)
        b.claws(cx - 0.4, cy + 0.6, n=4, dx=0.38, dir=(0.05, 0.4))

# ---------------- angular (low-poly) bears ----------------
TONES = ('#b98048', '#8f5a2e', '#6b4020', '#45280f')             # lit to dark
TONES_FAR = ('#6b4020', '#56331a', '#45280f', '#2f1a0a')
LIGHT = np.array([-0.45, -0.6, 0.66]) / np.linalg.norm([-0.45, -0.6, 0.66])   # upper left, towards the viewer (y down)

def lowpoly(b, cs, spacing=2.4, simp=0.5, tones=TONES, seed=1, sw=0.42, zk=1.0, cuts=(0.86, 0.66, 0.4),
            hatch_dark=True, edges='tone', edge_w=0.13):
    """angular cel-shaded bear part: the silhouette simplified to straight edges, filled with triangles over a domed
    height field (higher away from the edge), each lit from the upper left and stepped to one of the tones"""
    from scipy.spatial import Delaunay
    cs = cs.simplify(simp)
    rings = [np.array(r, float) for r in cs.to_polygons()]
    segs = []
    bpts = []
    for r in rings:
        for a_, c_ in zip(r, np.roll(r, -1, 0)):
            n = max(1, int(np.linalg.norm(c_ - a_) / spacing + 0.5))
            for t in range(n): bpts.append(a_ + (c_ - a_) * t / n)
            segs.append((a_, c_))
    A = np.array([s_[0] for s_ in segs]); Bv = np.array([s_[1] for s_ in segs])
    def dist(q):
        d_ = Bv - A; t = np.clip(((q[:, None, :] - A) * d_).sum(2) / np.maximum((d_ ** 2).sum(1), 1e-9), 0, 1)
        return np.linalg.norm(q[:, None, :] - (A + t[..., None] * d_), axis=2).min(1)
    def inside(q):
        c = np.zeros(len(q), int)
        for r in rings:
            x_, y_ = r[:, 0], r[:, 1]; x2, y2 = np.roll(x_, -1), np.roll(y_, -1)
            cond = ((y_[None] > q[:, 1:2]) != (y2[None] > q[:, 1:2])) & \
                   (q[:, 0:1] < (x2 - x_)[None] * (q[:, 1:2] - y_[None]) / np.where(y2 - y_ == 0, 1e-9, y2 - y_)[None] + x_[None])
            c += cond.sum(1)
        return c % 2 == 1
    rng = np.random.default_rng(seed)
    lo, hi = np.min([r.min(0) for r in rings], 0), np.max([r.max(0) for r in rings], 0)
    gx, gy = np.meshgrid(np.arange(lo[0], hi[0], spacing), np.arange(lo[1], hi[1], spacing * 0.87))
    gx = gx + (np.arange(gx.shape[0])[:, None] % 2) * spacing / 2
    q = np.column_stack([gx.ravel(), gy.ravel()]) + rng.uniform(-0.3, 0.3, (gx.size, 2)) * spacing
    q = q[inside(q)]; q = q[dist(q) > 0.4 * spacing]
    bpts = np.array(bpts)
    P_ = np.vstack([bpts, q]); z = np.concatenate([np.zeros(len(bpts)), zk * dist(q) ** 0.75])
    tri = Delaunay(P_).simplices
    cen = P_[tri].mean(1); tri = tri[inside(cen)]
    shade = []
    for t in tri:
        v = np.column_stack([P_[t], z[t]])
        n = np.cross(v[1] - v[0], v[2] - v[0]); n = n / (np.linalg.norm(n) + 1e-12)
        if n[2] < 0: n = -n
        I = float(n @ LIGHT); shade.append(0 if I > cuts[0] else 1 if I > cuts[1] else 2 if I > cuts[2] else 3)
    for t, k in zip(tri, shade):
        r_ = b.T([tuple(P_[i]) for i in t])
        M.add(f'<polygon points="{M.pts(r_)}" fill="{tones[k]}" stroke="{tones[k]}" stroke-width="0.04" stroke-linejoin="round"/>')
    if hatch_dark:
        for t, k in zip(tri, shade):
            if k == 3: M.hatch_ink(b.T([tuple(P_[i]) for i in t]), step=0.7, ang=62, sw=0.15, maxlen=2.0)
    if edges:                                                     # ink between planes of different tone (or all planes)
        own = {}
        for t, k in zip(tri, shade):
            for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])): own.setdefault(tuple(sorted(e)), []).append(k)
        d = ''
        for (i, j), ks in own.items():
            if len(ks) == 2 and (edges == 'all' or ks[0] != ks[1]):
                (a1, b1_), (a2, b2) = b.T([tuple(P_[i]), tuple(P_[j])])
                d += f'M{a1:.2f} {b1_:.2f}L{a2:.2f} {b2:.2f}'
        if d: M.add(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{edge_w}" stroke-linecap="round"/>')
    for r in rings: M.ink([tuple(v) for v in b.T([tuple(p) for p in r])], sw, closed=True)

def angular(geo, face, dx=0.0, k=1.0, **kw):
    def draw(x, yb, s):
        b = Bear(x + dx, yb, k); far, near = geo()
        lowpoly(b, far, tones=TONES_FAR, sw=0.3, seed=2, hatch_dark=False, **{a: v for a, v in kw.items() if a in ('spacing', 'simp')})
        lowpoly(b, near, **kw)
        face(b)
    return draw

def face_walker(b):
    b.blob(P([(20.4, -6.9), (21.5, -6.7), (21.4, -6.0), (20.6, -6.1)]))                   # nose
    b.blob(P([(17.5, -8.25), (18.4, -8.1), (18.0, -7.55)])); b.blob(E(17.95, -8.0, 0.1), CREAM)   # eye
    b.line([(20.9, -5.75), (20.0, -5.55), (19.1, -5.6)], 0.2)
    b.claws(15.9, -0.25); b.claws(4.9, -0.25)
def face_roar(b):
    b.blob(P([(17.9, -10.05), (20.4, -11.05), (19.9, -9.3), (18.0, -9.45)]))
    for (u, v, du, dv) in ((19.85, -10.95, 0.1, 0.5), (19.2, -10.75, 0.08, 0.4), (19.45, -9.3, 0.08, -0.45)):
        b.blob(P([(u - 0.13, v), (u + 0.13, v), (u + du, v + dv)]), CREAM)
    b.blob(P([(20.3, -12.0), (21.0, -11.8), (20.8, -11.35), (20.3, -11.5)]))
    b.blob(P([(17.05, -11.3), (17.9, -11.15), (17.5, -10.6)])); b.blob(E(17.45, -11.05, 0.1), CREAM)
    b.claws(15.9, -0.25); b.claws(4.9, -0.25)
def face_rearing(b):
    b.blob(P([(12.5, -16.45), (14.5, -17.45), (14.0, -15.9), (12.6, -15.75)]))
    for (u, v, du, dv) in ((14.05, -17.3, 0.12, 0.5), (13.65, -17.1, 0.1, 0.4), (13.75, -15.85, 0.08, -0.4)):
        b.blob(P([(u - 0.13, v), (u + 0.13, v), (u + du, v + dv)]), CREAM)
    b.blob(P([(14.6, -18.3), (15.2, -18.1), (15.0, -17.7), (14.6, -17.85)]))
    b.blob(P([(11.65, -17.45), (12.5, -17.3), (12.1, -16.75)])); b.blob(E(12.05, -17.2, 0.1), CREAM)
    b.claws(13.9, -10.2, dir=(0.35, 0.15)); b.claws(7.4, -0.25)
def face_forager(b):
    b.blob(P([(18.9, -1.1), (19.5, -0.9), (19.4, -0.4), (18.9, -0.5)]))
    b.blob(P([(16.95, -4.5), (17.8, -4.3), (17.35, -3.75)])); b.blob(E(17.3, -4.25, 0.1), CREAM)
    b.line([(19.9, -1.4), (20.6, -1.75)], 0.18); b.line([(20.0, -0.6), (20.8, -0.6)], 0.18)
    b.claws(14.1, -0.25); b.claws(4.5, -0.25)
def face_sitting(b):
    b.blob(P([(14.0, -12.45), (14.7, -12.3), (14.6, -11.85), (14.0, -11.95)]))
    b.blob(P([(10.95, -13.85), (11.8, -13.7), (11.4, -13.15)])); b.blob(E(11.35, -13.6, 0.1), CREAM)
    b.claws(12.0, -0.25); b.claws(8.6, -0.3)

def opt_mother_cub_angular(x, yb, s):
    angular(walker_geo, face_walker, dx=6.0, k=0.82, spacing=2.2, simp=0.45)(x, yb, s)
    c = Bear(x - 2.0, yb, 1.0); cfar, cnear = cub_geo()
    lowpoly(c, cfar, tones=TONES_FAR, sw=0.25, spacing=1.3, simp=0.2, hatch_dark=False)
    lowpoly(c, cnear, sw=0.34, spacing=1.3, simp=0.2, zk=1.4)
    c.blob(P([(7.55, -4.0), (8.0, -3.85), (7.9, -3.5), (7.5, -3.6)]))
    c.blob(P([(6.3, -4.75), (6.75, -4.65), (6.5, -4.35)]))

ANGULAR = [('Bold planes', angular(walker_geo, face_walker, spacing=3.4, simp=0.8, cuts=(0.8, 0.5, 0.25))),
           ('Low-poly', angular(walker_geo, face_walker, spacing=1.5, simp=0.3)),
           ('Crystal, every edge inked', angular(walker_geo, face_walker, spacing=2.3, simp=0.5, zk=2.4, edges='all')),
           ('Two-tone graphic', angular(walker_geo, face_walker, spacing=2.6, simp=0.7, cuts=(0.7, 0.7, -1), hatch_dark=False)),
           ('Roar on all fours', angular(roar_geo, face_roar, dx=-1.8, spacing=2.2, simp=0.45)),
           ('Rearing roar', angular(rearing_geo, face_rearing, dx=2.0, spacing=2.0, simp=0.35)),
           ('Forager', angular(forager_geo, face_forager, spacing=2.2, simp=0.45)),
           ('Sitting', angular(sitting_geo, face_sitting, dx=3.0, spacing=2.0, simp=0.35)),
           ('Mother and cub', opt_mother_cub_angular)]

OPTIONS = [('Walker', opt_walker), ('Rearing roar', opt_rearing), ('Head-on', opt_headon), ('Sitting', opt_sitting),
           ('Forager', opt_forager), ('Roar on all fours', opt_roar), ('Mother and cub', opt_mother_cub),
           ('Shadow bear', opt_shadow), ('Angular', opt_angular), ('Peeking over the hill', opt_peeker)]

def sheet(dpmm=16, only=None, options=None, name='bear_options.png', prefix=''):
    import cairosvg, io
    from PIL import Image, ImageDraw, ImageFont
    b1 = M.SIDE_B[1]; x0, y0, cw, ch = b1 - 6.0, 41.0, 36.0, M.VIS1 - 41.0
    tiles = []
    for i, (label, fn) in enumerate(options or OPTIONS):
        if only and i + 1 not in only: continue
        M.out.clear(); M._clip[0] = 0; M.BEAR[0] = fn; M.scene(); M.panels()
        png = cairosvg.svg2png(bytestring=M.svg(list(M.out), cw, ch, x0, y0).encode(),
                               output_width=round(cw * dpmm), output_height=round(ch * dpmm), background_color='white')
        tiles.append((i + 1, label, Image.open(io.BytesIO(png)).convert('RGB')))
    M.BEAR[0] = None
    tw, th = tiles[0][2].size; cols = 2; rows = (len(tiles) + 1) // 2; pad, head = 16, 46
    img = Image.new('RGB', (cols * (tw + pad) + pad, rows * (th + head + pad) + pad), '#f4efe4')
    fp = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    font = ImageFont.truetype(fp, 30) if os.path.exists(fp) else ImageFont.load_default()
    dr = ImageDraw.Draw(img)
    for k, (n, lbl, t) in enumerate(tiles):
        cx, cy = pad + (k % cols) * (tw + pad), pad + (k // cols) * (th + head + pad)
        dr.text((cx, cy + 6), (f'{prefix}{"abcdefghij"[n - 1]}. ' if prefix else f'{n}. ') + lbl, fill='#17120f', font=font)
        img.paste(t, (cx, cy + head))
    img.save(os.path.join(M.OUT, name))
    return img

if __name__ == '__main__':
    sheet()
    sheet(options=ANGULAR, name='bear_options_angular.png', prefix='9')
