"""Replace short label-to-label connections with real wires.

For every sheet-local label net, pins on the same sheet that are joined only through labels are
connected with orthogonal wires (A* on the 1.27 mm grid). Routes avoid symbol bodies, pin lines,
text, other nets' connection points and run along no other net's wire; perpendicular crossings of
other wires are allowed (KiCad does not connect them) but discouraged. Afterwards every fully
wired net keeps exactly one label so it keeps its name.

Usage (from DevBoard/): python tools/route_labels.py [--max 90] [sheet ...]
Verify afterwards: kicad-cli netlist diff, ERC, tools/check_overlaps.py.
"""
import heapq
import math
import os
import re
import subprocess
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sch_geom as G  # noqa: E402

CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
GRID = 1.27
SHEETS = ['gauge.kicad_sch', 'power.kicad_sch', 'mcu.kicad_sch', 'usb_port.kicad_sch', 'MonolithDev.kicad_sch']
MAX_SPAN = 45.0      # mm: nets spread wider than this stay on labels
TURN = 12.0
CROSS = 25.0

args = sys.argv[1:]
if '--max' in args:
    i = args.index('--max')
    MAX_SPAN = float(args[i + 1])
    del args[i:i + 2]
sheets = args or SHEETS


def g(v):
    return int(round(v / GRID))


def mm(n):
    return round(n * GRID, 2)


# ------------------------------------------------------------------ netlist (pin -> net name)
def netlist():
    out = os.path.join(tempfile.gettempdir(), 'route_net.xml')
    subprocess.run([CLI, 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', out, 'MonolithDev.kicad_sch'],
                   check=True, capture_output=True)
    r = ET.parse(out).getroot()
    pin_net = {}
    groups = set()
    for n in r.iter('net'):
        nodes = frozenset((x.get('ref'), x.get('pin')) for x in n.iter('node'))
        groups.add((n.get('name'), nodes))
        for ref, pin in nodes:
            pin_net[(ref, pin)] = n.get('name')
    return pin_net, groups


# ------------------------------------------------------------------ sheet model
def pin_points(root):
    """All pin connection points: list of (ref, pin_number, x, y)."""
    libs = {}
    for ls in G.kids(G.kid(root, 'lib_symbols') or [], 'symbol'):
        pins = []
        for sub in G.kids(ls, 'symbol'):
            for p in G.kids(sub, 'pin'):
                at = G.kid(p, 'at')
                pins.append((G.kid(p, 'number')[1], float(at[1]), float(at[2])))
        libs[ls[1]] = pins
    out = []
    for sym in G.kids(root, 'symbol'):
        lib = G.kid(sym, 'lib_id')[1]
        at = G.kid(sym, 'at')
        sx, sy, rot = float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0
        mir = G.kid(sym, 'mirror')
        ref = [p[2] for p in G.kids(sym, 'property') if p[1] == 'Reference'][0]
        for num, px, py in libs.get(lib, []):
            x, y = G.xform(px, py, sx, sy, rot, mir[1] if mir else None)
            out.append((ref, num, round(x, 2), round(y, 2), lib))
    return out


class UF:
    def __init__(self):
        self.p = {}

    def f(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def u(self, a, b):
        self.p[self.f(a)] = self.f(b)


def seg_cells(a, b):
    (x0, y0), (x1, y1) = a, b
    if x0 == x1:
        return [(x0, y) for y in range(min(y0, y1), max(y0, y1) + 1)]
    return [(x, y0) for x in range(min(x0, x1), max(x0, x1) + 1)]


def route_sheet(path, pin_net):
    s = open(path, encoding='utf-8').read()
    root, items, wires, syms = G.load(path)
    pins = pin_points(root)
    net_of_pin = {}
    for ref, num, x, y, lib in pins:
        n = pin_net.get((ref, num))
        if n:
            net_of_pin[(g(x), g(y))] = n
    # labels
    labels = []
    for kind in ('label', 'global_label', 'hierarchical_label'):
        for l in G.kids(root, kind):
            at = G.kid(l, 'at')
            labels.append((kind, l[1], g(float(at[1])), g(float(at[2]))))
    gw = [((g(a[0]), g(a[1])), (g(b[0]), g(b[1]))) for a, b in wires]

    # connectivity of points via wires (endpoints + endpoint-on-segment)
    uf = UF()
    pts = set(net_of_pin) | {p for w in gw for p in w} | {(x, y) for _, _, x, y in labels}
    for a, b in gw:
        uf.u(a, b)
        cells = set(seg_cells(a, b))
        for p in pts:
            if p in cells and p not in (a, b):
                # endpoint of something landing mid-segment connects (pins mid-segment do not)
                if p not in net_of_pin or any(p in w for w in gw):
                    uf.u(p, a)
    # net name of each wire group
    gnet = {}
    for p, n in net_of_pin.items():
        gnet.setdefault(uf.f(p), n)

    # which local-label nets are candidates
    local = {}
    for kind, txt, x, y in labels:
        if kind != 'label':
            continue
        grp = uf.f((x, y))
        n = gnet.get(grp)
        if n is None:
            continue
        local.setdefault(n, set()).add(grp)

    # obstacles
    W = max(g(b.x1) for b in items) + 10
    H = max(g(b.y1) for b in items) + 10
    hard = set()
    for b in items:
        if b.kind in ('body',):
            for x in range(g(b.x0 - 0.6), g(b.x1 + 0.6) + 1):
                for y in range(g(b.y0 - 0.6), g(b.y1 + 0.6) + 1):
                    hard.add((x, y))
        elif b.kind in ('note', 'glabel'):
            for x in range(g(b.x0) - 2, g(b.x1) + 3):
                for y in range(g(b.y0) - 2, g(b.y1) + 3):
                    hard.add((x, y))
    # pin lines (excluding the connection end itself)
    pin_line_cells = set()
    for b in items:
        if b.kind == 'pinline':
            for x in range(g(b.x0 + 0.15), g(b.x1 - 0.15) + 1):
                for y in range(g(b.y0 + 0.15 if b.y1 - b.y0 < 1 else b.y0 + 1.5), g(b.y1 - 0.15) + 1):
                    pin_line_cells.add((x, y))
    hwire, vwire, wpts = {}, {}, {}
    for a, b in gw:
        n = gnet.get(uf.f(a))
        for c in seg_cells(a, b):
            (hwire if a[1] == b[1] else vwire).setdefault(c, set()).add(n)
        for p in (a, b):
            wpts.setdefault(p, set()).add(n)
    conn_pts = {}
    for p, n in net_of_pin.items():
        conn_pts.setdefault(p, set()).add(n)
    for p, ns in wpts.items():
        conn_pts.setdefault(p, set()).update(ns)
    for kind, txt, x, y in labels:
        conn_pts.setdefault((x, y), set()).add(gnet.get(uf.f((x, y))))

    new_wires, routed_nets, junction_pts = [], [], set()

    def astar(net, sources, targets):
        # state: (cell, dir) ; dir 0 = horizontal, 1 = vertical, 2 = start
        openq = []
        best = {}
        tgt = targets
        tx = [t[0] for t in tgt]
        ty = [t[1] for t in tgt]

        def h(c):
            return min(abs(c[0] - a) + abs(c[1] - b) for a, b in tgt)

        for sc in sources:
            heapq.heappush(openq, (h(sc), 0.0, sc, 2, None))
            best[(sc, 2)] = 0.0
        came = {}
        limit = 0
        while openq:
            f, cost, c, d, prev = heapq.heappop(openq)
            if best.get((c, d), 1e9) < cost - 1e-9:
                continue
            if c in tgt and c not in sources:
                path = [c]
                k = (c, d)
                while k in came:
                    k = came[k]
                    path.append(k[0])
                return path[::-1]
            limit += 1
            if limit > 400000:
                return None
            for dx, dy, nd in ((1, 0, 0), (-1, 0, 0), (0, 1, 1), (0, -1, 1)):
                n = (c[0] + dx, c[1] + dy)
                if not (0 <= n[0] < W and 0 <= n[1] < H):
                    continue
                is_t = n in tgt
                if not is_t:
                    if n in hard or n in pin_line_cells:
                        continue
                    other = conn_pts.get(n)
                    if other and (other - {net}):
                        continue
                # running along another net's wire is never allowed
                along = hwire if nd == 0 else vwire
                if n in along and (along[n] - {net}):
                    continue
                if c in along and (along[c] - {net}) and c not in sources:
                    continue
                step = 1.0
                for nb in ((n[0] + 1, n[1]), (n[0] - 1, n[1]), (n[0], n[1] + 1), (n[0], n[1] - 1)):
                    if nb in tgt or nb in sources:
                        continue
                    o = conn_pts.get(nb)
                    if o and (o - {net}):
                        step += 15
                    par = hwire if nd == 0 else vwire
                    if nb[1 - nd] != n[1 - nd] and nb in par and (par[nb] - {net}):
                        step += 8
                cross = vwire if nd == 0 else hwire
                if n in cross and (cross[n] - {net}):
                    step += CROSS
                if d != 2 and nd != d:
                    # turning here creates a bend point: must not sit on another net's wire
                    if (c in hwire and (hwire[c] - {net})) or (c in vwire and (vwire[c] - {net})):
                        continue
                    step += TURN
                nc = cost + step
                key = (n, nd)
                if nc < best.get(key, 1e9) - 1e-9:
                    best[key] = nc
                    came[key] = (c, d)
                    heapq.heappush(openq, (nc + h(n), nc, n, nd, c))
        return None

    for net, grps in sorted(local.items()):
        # all pin/label points of this net on this sheet, grouped by wire connectivity
        members = {}
        for p, n in net_of_pin.items():
            if n == net:
                members.setdefault(uf.f(p), set()).add(p)
        for p in wpts:
            if gnet.get(uf.f(p)) == net:
                members.setdefault(uf.f(p), set()).add(p)
        if len(members) < 2:
            continue
        allp = [p for ps in members.values() for p in ps]
        span = max(mm(max(x for x, _ in allp) - min(x for x, _ in allp)),
                   mm(max(y for _, y in allp) - min(y for _, y in allp)))
        if span > MAX_SPAN:
            continue
        groups = list(members.values())
        tree = set(groups[0])
        # tree cells = group points plus cells of its existing wires
        for a, b in gw:
            if uf.f(a) in members and members[uf.f(a)] is groups[0]:
                tree.update(seg_cells(a, b))
        remaining = groups[1:]
        net_new = []
        ok = True
        while remaining:
            # connect the nearest remaining group
            remaining.sort(key=lambda gr: min(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a in gr for b in tree))
            gr = remaining.pop(0)
            tgt = set(gr)
            route = astar(net, set(tree), tgt)
            if route is None:
                ok = False
                break
            # compress to segments
            segs = []
            start = route[0]
            for i in range(1, len(route)):
                if i == len(route) - 1 or (route[i + 1][0] - route[i][0], route[i + 1][1] - route[i][1]) != \
                        (route[i][0] - route[i - 1][0], route[i][1] - route[i - 1][1]):
                    segs.append((start, route[i]))
                    start = route[i]
            for a, b in segs:
                if a != b:
                    net_new.append((a, b))
            junction_pts.add(route[0])
            for c in route:
                tree.add(c)
            tree.update(gr)
            # register as obstacles for other nets
            for a, b in segs:
                for c in seg_cells(a, b):
                    (hwire if a[1] == b[1] else vwire).setdefault(c, set()).add(net)
                for p in (a, b):
                    conn_pts.setdefault(p, set()).add(net)
        if ok:
            new_wires += net_new
            routed_nets.append(net)
        else:
            # roll back obstacle registration is unnecessary: failed partial routes are simply not written
            pass

    # write wires
    add = []
    for a, b in new_wires:
        add.append(f'\t(wire\n\t\t(pts\n\t\t\t(xy {mm(a[0])} {mm(a[1])}) (xy {mm(b[0])} {mm(b[1])})\n\t\t)\n'
                   f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n')
    # drop all but one local label of each routed net (keep the first, i.e. the one KiCad lists first)
    kept = set()
    out, last = [], 0
    for m in re.finditer(r'\t\(label "((?:[^"\\]|\\.)*)"\n', s):
        a = m.start()
        b = G_block_end(s, a + 1)
        name = m.group(1)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+)', s[a:b])
        p = (g(float(at.group(1))), g(float(at.group(2))))
        n = gnet.get(uf.f(p))
        if n in routed_nets:
            if n in kept:
                out.append(s[last:a])
                last = b + 2 if s[b + 1:b + 2] == '\n' else b + 1
                continue
            kept.add(n)
    out.append(s[last:])
    s = ''.join(out)
    # junctions: KiCad only joins a wire end to the middle of another wire if a junction sits there
    allw = gw + list(new_wires)
    have_j = {(g(float(x)), g(float(y))) for x, y in re.findall(r'\(junction\s*\(at ([-\d.]+) ([-\d.]+)', s)}
    need_j = set()
    for a, b in allw:
        for p in (a, b):
            for c, d in allw:
                if (c, d) == (a, b):
                    continue
                cells = seg_cells(c, d)
                if p in cells and p not in (c, d):
                    need_j.add(p)
    for p in sorted(need_j - have_j):
        add.append(f'\t(junction\n\t\t(at {mm(p[0])} {mm(p[1])})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n'
                   f'\t\t(uuid "{uuid.uuid4()}")\n\t)\n')
    i = s.rindex('\t(sheet_instances') if '\t(sheet_instances' in s else s.rstrip().rindex(')')
    s = s[:i] + ''.join(add) + s[i:]
    open(path, 'w', encoding='utf-8', newline='\n').write(s)
    print(f'{path}: routed {len(routed_nets)} nets with {len(new_wires)} wire segments')
    return routed_nets


def G_block_end(s, start):
    d, m = 0, start
    while True:
        ch = s[m]
        if ch == '"':
            m += 1
            while s[m] != '"':
                if s[m] == '\\':
                    m += 1
                m += 1
        elif ch == '(':
            d += 1
        elif ch == ')':
            d -= 1
            if d == 0:
                return m
        m += 1


pin_net, base = netlist()
for p in sheets:
    route_sheet(p, pin_net)
_, after = netlist()
print('netlist identical:', after == base)
if after != base:
    print('  only before:', sorted(n for n, _ in base - after)[:20])
    print('  only after :', sorted(n for n, _ in after - base)[:20])
