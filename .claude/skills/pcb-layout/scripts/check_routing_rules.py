"""Check a KiCad board against the routing discipline in references/routing-discipline.md.

    python check_routing_rules.py board.kicad_pcb [--vertical In2.Cu] [--horizontal In3.Cu]
        [--planes In1.Cu,In4.Cu] [--outer-max 15] [--ref-via 1.0] [--fanout 3.0] [--web 0.3]
        [--allow-classes Power,GateDrive,Kelvin] [--allow-nets REGEX] [--ic-prefix U] [--max-list 15]

Checks, each printed as a section with a count and the first few offenders (mm, relative to the outline's top-left):
  1. direction    - segments on the vertical layer that aren't vertical, on the horizontal layer that aren't
                    horizontal; arcs on either.
  2. planes       - tracks on a plane layer; zones on a plane layer whose net isn't GND; rows of non-GND vias
                    whose plane antipads leave less than --web of copper between them (a slot), 3+ in a chain.
  3. outer runs   - signal nets whose connected track run on F.Cu/B.Cu is longer than --outer-max (power,
                    gate-drive, Kelvin classes and GND are exempt; extend with --allow-classes / --allow-nets).
  4. ref vias     - non-GND vias with no GND via or GND through-hole pad within --ref-via.
  5. fan-out room - ICs (refs starting with --ic-prefix, default U) with >20 pins or pitch < 0.8 mm whose courtyard has another part's courtyard within
                    --fanout, except caps that share a net with the IC and have a GND pad (decoupling).
Exit code 0 always; read the counts. Run with KiCad's bundled python (needs pcbnew).
"""
import collections
import math
import re
import sys

import pcbnew

argv = sys.argv[1:]


def opt(name, default):
    if name in argv:
        i = argv.index(name)
        v = argv[i + 1]
        del argv[i:i + 2]
        return v
    return default


VERT = opt("--vertical", "In2.Cu")
HORZ = opt("--horizontal", "In3.Cu")
PLANES = opt("--planes", "In1.Cu,In4.Cu").split(",")
OUTER_MAX = float(opt("--outer-max", "15"))
REF_VIA = float(opt("--ref-via", "1.0"))
FANOUT = float(opt("--fanout", "3.0"))
WEB = float(opt("--web", "0.3"))
ALLOW_CLASSES = set(opt("--allow-classes", "Power,HighCurrent,Pack,GateDrive,Kelvin,SW").split(","))
ALLOW_NETS = re.compile(opt("--allow-nets", r"^$"), re.I)
MAX_LIST = int(opt("--max-list", "15"))
IC_PREFIX = tuple(opt("--ic-prefix", "U").split(","))
TOL = 0.001  # mm

board = pcbnew.LoadBoard(argv[0])
bb = board.GetBoardEdgesBoundingBox()
OX, OY = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
lid = {board.GetStandardLayerName(l): l for l in board.GetEnabledLayers().CuStack()}
for name in [VERT, HORZ] + PLANES:
    if name not in lid:
        sys.exit(f"layer {name} not on this board (copper layers: {', '.join(lid)})")
V, H, P = lid[VERT], lid[HORZ], {lid[n] for n in PLANES}
mm = pcbnew.ToMM


def xy(p):
    return (round(mm(p.x) - OX, 2), round(mm(p.y) - OY, 2))


def is_gnd(net):
    return net == "GND" or net.endswith("/GND")


def report(title, items, fmt):
    print(f"\n== {title}: {len(items)}")
    for it in items[:MAX_LIST]:
        print("   " + fmt(it))
    if len(items) > MAX_LIST:
        print(f"   ... {len(items) - MAX_LIST} more")


tracks = list(board.GetTracks())
vias = [t for t in tracks if t.GetClass() == "PCB_VIA"]
segs = [t for t in tracks if t.GetClass() in ("PCB_TRACK", "PCB_ARC")]

# 1. direction
bad_dir = []
for t in segs:
    L = t.GetLayer()
    if L not in (V, H):
        continue
    s, e = t.GetStart(), t.GetEnd()
    dx, dy = abs(mm(e.x - s.x)), abs(mm(e.y - s.y))
    if t.GetClass() == "PCB_ARC":
        bad_dir.append((t, "arc"))
    elif L == V and dx > TOL:
        bad_dir.append((t, "not vertical"))
    elif L == H and dy > TOL:
        bad_dir.append((t, "not horizontal"))
report(f"direction ({VERT} vertical, {HORZ} horizontal)", bad_dir,
       lambda it: f"{board.GetStandardLayerName(it[0].GetLayer())} {it[0].GetNetname()} {xy(it[0].GetStart())}->"
                  f"{xy(it[0].GetEnd())} {it[1]}")

# 2. planes
on_plane = [t for t in segs if t.GetLayer() in P]
report("tracks on plane layers", on_plane,
       lambda t: f"{board.GetStandardLayerName(t.GetLayer())} {t.GetNetname()} {xy(t.GetStart())}->{xy(t.GetEnd())}")
bad_zones = [(z, board.GetStandardLayerName(L)) for z in board.Zones() if not z.GetIsRuleArea()
             for L in P if z.IsOnLayer(L) and not is_gnd(z.GetNetname())]
report("non-GND zones on plane layers", bad_zones,
       lambda it: f"{it[1]} net '{it[0].GetNetname()}' bbox {xy(it[0].GetBoundingBox().GetOrigin())}"
                  f"-{xy(it[0].GetBoundingBox().GetEnd())}")
# antipad rows: approximate each non-GND via's plane antipad as pad radius + zone clearance
zclr = max([mm(z.GetLocalClearance() or 0) for z in board.Zones() if not z.GetIsRuleArea()
            and any(z.IsOnLayer(L) for L in P)] + [0.2])
ap = [(v, mm(v.GetWidth(pcbnew.F_Cu)) / 2 + zclr) for v in vias if not is_gnd(v.GetNetname())]
parent = list(range(len(ap)))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


grid = collections.defaultdict(list)
for i, (v, r) in enumerate(ap):
    p = v.GetPosition()
    grid[(int(mm(p.x) // 2), int(mm(p.y) // 2))].append(i)
for i, (v, r) in enumerate(ap):
    p = v.GetPosition()
    gx, gy = int(mm(p.x) // 2), int(mm(p.y) // 2)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for j in grid[(gx + dx, gy + dy)]:
                if j <= i:
                    continue
                q, rj = ap[j][0].GetPosition(), ap[j][1]
                if math.hypot(mm(p.x - q.x), mm(p.y - q.y)) - r - rj < WEB:
                    parent[find(i)] = find(j)
chains = collections.defaultdict(list)
for i in range(len(ap)):
    chains[find(i)].append(ap[i][0])
slots = [c for c in chains.values() if len(c) >= 3]
report(f"via rows slotting the planes (antipad web < {WEB} mm, 3+ vias)", slots,
       lambda c: f"{len(c)} vias, nets {sorted({v.GetNetname() for v in c})[:3]}, from {xy(c[0].GetPosition())}")

# 3. outer runs
def exempt(net):
    if not net or is_gnd(net) or ALLOW_NETS.search(net):
        return True
    ni = board.FindNet(net)
    return ni is not None and ni.GetNetClassName() in ALLOW_CLASSES


runs = []
for L in (pcbnew.F_Cu, pcbnew.B_Cu):
    by_net = collections.defaultdict(list)
    for t in segs:
        if t.GetLayer() == L and not exempt(t.GetNetname()):
            by_net[t.GetNetname()].append(t)
    for net, ts in by_net.items():
        idx = {}
        par = list(range(len(ts)))

        def f(i):
            while par[i] != i:
                par[i] = par[par[i]]
                i = par[i]
            return i

        for i, t in enumerate(ts):
            for p in (t.GetStart(), t.GetEnd()):
                k = (p.x // 1000, p.y // 1000)
                if k in idx:
                    par[f(i)] = f(idx[k])
                else:
                    idx[k] = i
        tot = collections.Counter()
        for i, t in enumerate(ts):
            tot[f(i)] += mm(t.GetLength())
        for root, length in tot.items():
            if length > OUTER_MAX:
                runs.append((net, board.GetStandardLayerName(L), length, ts[root]))
runs.sort(key=lambda r: -r[2])
report(f"long signal runs on outer layers (> {OUTER_MAX} mm)", runs,
       lambda r: f"{r[1]} {r[0]} {r[2]:.1f} mm near {xy(r[3].GetStart())}")

# 4. reference vias
gnd_pts = [v.GetPosition() for v in vias if is_gnd(v.GetNetname())]
gnd_pts += [p.GetPosition() for fp in board.GetFootprints() for p in fp.Pads()
            if p.HasHole() and is_gnd(p.GetNetname())]
gg = collections.defaultdict(list)
for q in gnd_pts:
    gg[(int(mm(q.x) // 2), int(mm(q.y) // 2))].append(q)
lonely = []
for v in vias:
    if is_gnd(v.GetNetname()):
        continue
    p = v.GetPosition()
    gx, gy = int(mm(p.x) // 2), int(mm(p.y) // 2)
    near = any(math.hypot(mm(p.x - q.x), mm(p.y - q.y)) <= REF_VIA
               for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in gg[(gx + dx, gy + dy)])
    if not near:
        lonely.append(v)
report(f"signal vias without a GND via within {REF_VIA} mm", lonely,
       lambda v: f"{v.GetNetname()} at {xy(v.GetPosition())}")

# 5. fan-out room
def courtyard_box(fp):
    c = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
    return c.BBox() if c.OutlineCount() else fp.GetBoundingBox(False)


def dense(fp):
    pads = [p for p in fp.Pads() if p.GetNumber()]
    nums = {p.GetNumber() for p in pads}
    if len(nums) > 20:
        return True
    pts = [(mm(p.GetPosition().x), mm(p.GetPosition().y)) for p in pads]
    pitch = min((math.hypot(a[0] - b[0], a[1] - b[1]) for i, a in enumerate(pts) for b in pts[i + 1:]),
                default=99)
    return len(nums) >= 6 and pitch < 0.8


fps = list(board.GetFootprints())
crowd = []
for ic in fps:
    if not ic.GetReference().startswith(IC_PREFIX) or not dense(ic) or ic.IsDNP():
        continue
    box = courtyard_box(ic)
    zone = pcbnew.BOX2I(box.GetOrigin(), box.GetSize())
    zone.Inflate(pcbnew.FromMM(FANOUT))
    ic_nets = {p.GetNetname() for p in ic.Pads() if p.GetNetname()}
    for o in fps:
        if o is ic or o.IsFlipped() != ic.IsFlipped():
            continue
        ob = courtyard_box(o)
        if not zone.Intersects(ob):
            continue
        onets = {p.GetNetname() for p in o.Pads()}
        decoup = o.GetReference().startswith("C") and (onets & ic_nets) and any(is_gnd(n) for n in onets)
        if not decoup:
            gap = max(mm(max(box.GetLeft() - ob.GetRight(), ob.GetLeft() - box.GetRight(), 0)),
                      mm(max(box.GetTop() - ob.GetBottom(), ob.GetTop() - box.GetBottom(), 0)))
            crowd.append((ic.GetReference(), o.GetReference(), gap))
crowd.sort(key=lambda c: (c[0], c[2]))
report(f"parts inside the {FANOUT} mm fan-out area of dense ICs", crowd,
       lambda c: f"{c[0]}: {c[1]} at {c[2]:.2f} mm")

print("\nsummary: direction %d, plane tracks %d, plane zones %d, plane slots %d, outer runs %d, ref vias %d, "
      "fan-out %d" % (len(bad_dir), len(on_plane), len(bad_zones), len(slots), len(runs), len(lonely), len(crowd)))
