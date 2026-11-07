"""The 17 drop poses: 5 faces, 8 edges, 4 corners (the pack is near mirror-symmetric in y, so only the +y side, USB1,
is run where a pose has a y component). Edges and corners land with the centre of mass straight over the edge or
corner: the hardest way to land on them (no rotation during the hit)."""
import numpy as np

FACES = {'top': (0, 0, 1), 'bottom': (0, 0, -1), 'board': (1, 0, 0), 'back': (-1, 0, 0), 'side': (0, 1, 0)}
EDGES = {'top_board': ((0, 0, 1), (1, 0, 0)), 'top_back': ((0, 0, 1), (-1, 0, 0)), 'bottom_board': ((0, 0, -1), (1, 0, 0)),
         'bottom_back': ((0, 0, -1), (-1, 0, 0)), 'top_side': ((0, 0, 1), (0, 1, 0)), 'bottom_side': ((0, 0, -1), (0, 1, 0)),
         'board_side': ((1, 0, 0), (0, 1, 0)), 'back_side': ((-1, 0, 0), (0, 1, 0))}
CORNERS = {'top_board_side': (1, 1, 1), 'top_back_side': (-1, 1, 1), 'bottom_board_side': (1, 1, -1), 'bottom_back_side': (-1, 1, -1)}
TITLES = {'top': 'Flat on the port end', 'bottom': 'Flat on the cap end', 'board': 'Flat on the board face',
          'back': 'Flat on the back (cell) face', 'side': 'Flat on a narrow side (USB1, +y)',
          'top_board': 'Edge: port end / board face', 'top_back': 'Edge: port end / back face',
          'bottom_board': 'Edge: cap end / board face', 'bottom_back': 'Edge: cap end / back face',
          'top_side': 'Edge: port end / narrow side', 'bottom_side': 'Edge: cap end / narrow side',
          'board_side': 'Edge: board face / narrow side (long edge)', 'back_side': 'Edge: back face / narrow side (long edge)',
          'top_board_side': 'Corner: port end, board face, narrow side', 'top_back_side': 'Corner: port end, back face, narrow side',
          'bottom_board_side': 'Corner: cap end, board face, narrow side', 'bottom_back_side': 'Corner: cap end, back face, narrow side'}
ORDER = list(FACES) + list(EDGES) + list(CORNERS)

def over(P, cg, d, span=None):
    """iterate d until the outer point lowest along d is straight under the CG (d restricted to span if given)"""
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    for _ in range(100):
        p = P[np.argmax(P @ d)]
        dn = p - cg
        if span is not None:                    # keep d in the plane of the two face normals (edge landing)
            S = np.asarray(span, float).T; dn = S @ np.linalg.lstsq(S, dn, rcond=None)[0]
        dn /= np.linalg.norm(dn)
        if np.linalg.norm(dn - d) < 1e-7: break
        d = 0.5 * d + 0.5 * dn; d /= np.linalg.norm(d)
    return d, p

def directions(P, cg):
    out = {}
    for k, v in FACES.items(): out[k] = np.asarray(v, float)
    for k, (a, b) in EDGES.items(): out[k] = over(P, cg, np.add(a, b), span=(a, b))[0]
    for k, v in CORNERS.items(): out[k] = over(P, cg, v)[0]
    return out
