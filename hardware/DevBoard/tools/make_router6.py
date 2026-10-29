"""Derive tools/route_signals6.py from route_signals.py: the 6-layer, Manhattan-pair version of the A* router.

Changes (routing-discipline.md): layers F / In2 / In3 / B (In1 and In4 are the untouchable GND planes); In2 takes
vertical moves only and In3 horizontal moves only, so a direction change costs a via; outer layers cost more than the
inner pair so only escapes and short local links stay outside; 0.45/0.3 vias; the In2-GND-fill allowances of the
4-layer board are gone; zone end-points are searched in a wider window; own uuid sidecar.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "route_signals.py"), encoding="utf-8").read()


def rep(a, b, count=1):
    global src
    assert src.count(a) >= 1, a[:70]
    src = src.replace(a, b, count)


rep('"""Signal router: A* maze routing on a 0.1 mm grid for the connections DRC still reports as missing.',
    '"""Signal router (6-layer, Manhattan pair): A* maze routing on a 0.1 mm grid for the connections DRC still reports\n'
    'as missing. Generated from route_signals.py by make_router6.py; see routing-discipline.md.\n'
    'Layers F.Cu (cost 1.6), In2 (1.0, vertical moves only), In3 (1.0, horizontal moves only), B.Cu (1.8); In1/In4\n'
    'are the GND planes and are never used. A GND reference via next to each In2/In3 or B via is added afterwards by\n'
    'finish_d_gndvias.py.')
rep('IDS = os.path.join(HERE, "route_signals.uuids")', 'IDS = os.path.join(HERE, "route_signals6.uuids")')
rep("from pcb_text import strip_items",
    "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # runs under python -I too\n"
    "from pcb_text import strip_items  # noqa: E402")
rep("VIA_D, VIA_DRILL = 0.5, 0.3", "VIA_D, VIA_DRILL = 0.45, 0.3")
rep("LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]\nLCOST = [1.0, 1.4, 1.8]",
    "LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.B_Cu]\nLCOST = [1.6, 1.0, 1.0, 1.8]\n"
    "VERT, HORZ = 1, 2                         # Manhattan pair: In2 vertical only, In3 horizontal only")
rep("        if q.HasHole() and q.GetNetCode() == gnd:\n            c, bq = q.GetPosition(), q.GetBoundingBox()",
    "        if False:\n            c, bq = q.GetPosition(), q.GetBoundingBox()")
rep('    elif " on B.Cu" in desc:\n        lays = [2]\n    elif "In2" in desc:\n        lays = [1]\n    for li in lays:\n'
    '        for dx in range(-2, 3):\n            for dy in range(-2, 3):',
    '    elif " on B.Cu" in desc:\n        lays = [3]\n    elif "In2" in desc:\n        lays = [1]\n    elif "In3" in desc:\n'
    '        lays = [2]\n    R = 15 if desc.startswith("Zone") else 2\n    for li in lays:\n'
    '        for dx in range(-R, R + 1):\n            for dy in range(-R, R + 1):')
rep("        for k, (dx, dy, c) in enumerate(dirs):\n            X, Y = x + dx, y + dy\n",
    "        for k, (dx, dy, c) in enumerate(dirs):\n"
    "            if (li == VERT and dx) or (li == HORZ and dy):\n                continue\n"
    "            X, Y = x + dx, y + dy\n")
# pass-specific uuid sidecar (argv[3]) and relaxed mode (argv[4] == "--relaxed": off-direction moves on In2/In3
# allowed at triple cost, for the leftovers of a strict pass; such routes are listed so the deviation is known)
rep('MAX_EDGES = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 6',
    'MAX_EDGES = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 6\n'
    'if len(sys.argv) > 3:\n    IDS = sys.argv[3]\nRELAXED = "--relaxed" in sys.argv')
rep("            if (li == VERT and dx) or (li == HORZ and dy):\n                continue\n",
    "            if (li == VERT and dx) or (li == HORZ and dy):\n"
    "                if not RELAXED:\n                    continue\n                c = c * 3.0\n")
# bigger search budget and window for long edges
rep("    pad = 6.0 if dist < 10 else (12.0 if dist < 30 else 20.0)",
    "    pad = 6.0 if dist < 10 else (12.0 if dist < 30 else 30.0)")
rep("    WH, CAP = (1.0, NODE_CAP) if dist < 15 else (1.25, 3 * NODE_CAP)",
    "    WH, CAP = (1.0, NODE_CAP) if dist < 15 else ((1.25, 3 * NODE_CAP) if dist < 30 else (1.4, 12 * NODE_CAP))")
# a through-hole pad (the exposed-pad via) counts as F.Cu for the neighbouring-pin bridge
rep('    if ma and mb and ma.group(1) == mb.group(1) and dist < 1.0 and "on F.Cu" in ad and "on F.Cu" in bd \\',
    '    if ma and mb and ma.group(1) == mb.group(1) and dist < 1.2 and ("on F.Cu" in ad or "PTH" in ad) '
    'and ("on F.Cu" in bd or "PTH" in bd) \\')
# route ends: snap to the centre of a pad OR of an existing via; a short snap replaces the end point instead of
# adding a tiny segment (which left acute wedges DRC reported as narrow connections)
rep('''def snap(pt, n):
    """Centre of the convex F.Cu pad of net n that contains a path end, or None (a route that stops at a pad's
    corner leaves a thin neck; one that stops off the pad must not be extended)."""
    if pt[2] != 0:
        return None
    v = pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1]))
    for q in PADS_BY_NET.get(n, ()):
        if q.HitTest(v, mm(G * 1.2)):                     # grid cells at a rounded corner sit just outside
            c = q.GetPosition()
            return MM(c.x), MM(c.y)
    return None''',
    '''VIAS_BY_NET = {}
for _t in board.GetTracks():
    if _t.GetClass() == "PCB_VIA":
        _c = _t.GetPosition()
        VIAS_BY_NET.setdefault(_t.GetNetCode(), []).append((MM(_c.x), MM(_c.y), MM(_t.GetWidth(pcbnew.F_Cu)) / 2))


def snap(pt, n):
    """Centre of the convex F.Cu pad, or of the existing via, of net n that contains a path end, or None (a route
    that stops inside a pad or via ring but off its centre leaves a thin wedge)."""
    for x, y, r in VIAS_BY_NET.get(n, ()):
        if math.hypot(x - pt[0], y - pt[1]) < r + G * 1.2:
            return x, y
    if pt[2] != 0:
        return None
    v = pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1]))
    for q in PADS_BY_NET.get(n, ()):
        if q.HitTest(v, mm(G * 1.2)):                     # grid cells at a rounded corner sit just outside
            c = q.GetPosition()
            return MM(c.x), MM(c.y)
    return None''')
rep('''    if ca and math.hypot(ca[0] - pts[0][0], ca[1] - pts[0][1]) > 0.02:
        pts.insert(0, (ca[0], ca[1], 0))
    if cb and math.hypot(cb[0] - pts[-1][0], cb[1] - pts[-1][1]) > 0.02:
        pts.append((cb[0], cb[1], 0))''',
    '''    if ca:
        d0 = math.hypot(ca[0] - pts[0][0], ca[1] - pts[0][1])
        if d0 > 0.35:
            pts.insert(0, (ca[0], ca[1], pts[0][2]))
        elif d0 > 0.02 and len(pts) > 1:
            pts[0] = (ca[0], ca[1], pts[0][2])
    if cb:
        d1 = math.hypot(cb[0] - pts[-1][0], cb[1] - pts[-1][1])
        if d1 > 0.35:
            pts.append((cb[0], cb[1], pts[-1][2]))
        elif d1 > 0.02 and len(pts) > 1:
            pts[-1] = (cb[0], cb[1], pts[-1][2])''')
open(os.path.join(HERE, "route_signals6.py"), "w", encoding="utf-8", newline="\n").write(src)
print("wrote route_signals6.py")
