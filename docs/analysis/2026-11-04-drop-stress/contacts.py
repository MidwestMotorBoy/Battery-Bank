"""Contact tables between the bodies for a drop direction d (pack frame unit vector, pointing at the floor).

For each pair (a, b) the relative motion of a toward the floor past b is delta = x_a - x_b (mm, along d). Moving a
by delta * d, the overlap volume V(delta) = vol((a + delta d) ^ b) is a Winkler measure of the contact: with a bed of
springs of stiffness k_w (N/mm per mm2 of area per mm of penetration) on the surfaces, the contact force is k_w x V.
Each pair is tabulated both ways (a ahead of b, and b ahead of a), from the first touch (gap g0) to 1 mm past it.
b can be a shell sub-part (cup walls, cradles, lands, lips, cap, overtravel posts, board feet, pad)."""
import numpy as np
EPS = 1e-4                                      # mm3: overlap counted as contact (face-on-face sliding leaves ~2e-5 slivers)
DMAX = 1.5                                      # look this far for a first touch (mm)
STEPS = np.r_[0, np.geomspace(0.001, 0.05, 14), np.arange(0.06, 0.3, 0.02), np.arange(0.3, 1.01, 0.05)]

def vol(a, b, d, t):
    return (a.translate(tuple(np.asarray(d) * t)) ^ b).volume()

def first_gap(a, b, d, dmax=DMAX):
    """smallest t >= 0 with overlap (bisection after a coarse scan from the Euclidean lower bound); None if none <= dmax"""
    lo = max(0.0, a.min_gap(b, dmax + 0.5) - 1e-4)
    if lo > dmax: return None
    if vol(a, b, d, lo) > EPS: return lo
    t, step = lo, 0.02
    while t <= dmax:
        t2 = t + step
        if vol(a, b, d, t2) > EPS:
            lo_, hi = t, t2
            for _ in range(14):
                mid = 0.5 * (lo_ + hi)
                if vol(a, b, d, mid) > EPS: hi = mid
                else: lo_ = mid
            return hi
        t = t2
    return None

def table(a, b, d):
    """(g0, deltas, V) for a moving along +d into b, or None"""
    g0 = first_gap(a, b, d)
    if g0 is None: return None
    dl = g0 + STEPS
    V = np.array([vol(a, b, d, t) for t in dl])
    return g0, dl, np.maximum.accumulate(V)

def pair_tables(A, B, d):
    """both senses: '+' = A moves toward the floor past B (delta > 0), '-' = B moves toward the floor past A"""
    d = np.asarray(d, float)
    return {'+': table(A, B, d), '-': table(B, A, d)}
