"""Placement for the Monolith dev board (run with KiCad's python: "C:/Program Files/KiCad/10.0/bin/python.exe").

1. Mechanical: board outline (with gaps for the USB-C notches), mounting holes, USB-C connectors (locked).
2. Hand placement of everything that matters electrically (FIXED, PORT): holders, gauge core, both charger power
   trains (port 2 is port 1 shifted down), regulators, connectors, MCU.
3. Auto placement of the remaining small parts: each goes to the nearest free spot (courtyards never overlap)
   to the pads it connects to, inside its block's region.

Coordinates are board mm from the top-left corner (KiCad adds ORIGIN). Re-running places everything again.

    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/place_parts.py
    python tools/setup_board.py        # always afterwards: pcbnew rewrites the .kicad_pro with default rules
"""
import math
import os
import re
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "MonolithDev.kicad_pcb")
ORIGIN = (50.0, 50.0)
W, H = 196.0, 115.0
USB_Y = (32.0, 68.0)
NOTCH_W = 10.2
HOLES = {"H1": (4, 4), "H2": (106, 4), "H3": (192, 4), "H4": (4, 111), "H5": (106, 111), "H6": (192, 111)}

# block regions (x0, y0, x1, y1) for auto placement
REGION = {
    "1": (110, 13, 136, 101),     # gauge column
    "2": (136, 88, 196, 115),     # sleep-current section along the bottom
    "3": (110, 0, 196, 13),       # MCU + headers along the top
    "4": (136, 13, 196, 50),      # port 1
    "5": (136, 50, 196, 88),      # port 2
    "0": (110, 0, 196, 115),
}

# ---- hand placement (board mm, rotation deg) ------------------------------------------------------------
FIXED = {
    # cells: + on the left; BT101 (CELL_N end) at the top
    "BT101": (55, 15, 0), "BT102": (55, 43, 0), "BT103": (55, 71, 0), "BT104": (55, 99, 0),
    # gauge core: shunt by BT101's - contact, protection FETs and fuse down the column
    "RS101": (115, 20, 90), "U101": (123, 42, 0), "Q101": (130, 24, 0), "Q102": (130, 32, 0),
    # BQ40Z50 cell-input filter ladder (TI fig. 9-1): 100R per tap in a column, 0.1u between adjacent VC
    # nodes staggered in two columns right at the VC pins; nodes VC4..VC1, CELL_N at 1.9 mm pitch
    "R104": (112.6, 38.6, 0), "R103": (112.6, 40.5, 0), "R102": (112.6, 42.4, 0), "R101": (112.6, 44.3, 0),
    "C101": (116.0, 39.55, 90), "C102": (117.8, 41.45, 90), "C103": (116.0, 43.35, 90), "C104": (117.8, 45.25, 90),
    "F101": (114, 96, 90), "J101": (113, 108, 0), "J102": (127, 95.5, 0), "J103": (132.5, 92.5, 0),
    # sleep-current section: R_MEAS, amplifiers, LDO, 3.3 V buck; SMAs on the bottom edge
    "R201": (150, 96, 0), "U201": (160, 95, 0), "U202": (160, 104, 0), "U203": (146, 105, 0),
    "U204": (180, 96, 0), "L201": (186, 96, 0), "JP201": (140, 103, 0),
    "J201": (162, 112.16, 270), "J202": (178, 112.16, 270),   # edge-mount: pad ends 0.3 mm inside the edge
    # MCU top band; antenna (pin-1 end) at the top edge
    "U301": (150, 5.8, 0), "J301": (120, 6, 90), "J302": (131, 6, 90), "J303": (168, 6, 90),
}

# one charger port in a local frame: Q401 left, L401 centre, Q402 right; input caps above Q401, output caps
# below Q402, BQ25756 below the inductor. The frame is turned 180 deg onto the board so the input side faces
# the USB-C edge and the output side faces the pack bus.
PORT = {
    "Q01": (-11, 0, 0), "L01": (0, 0, 0), "Q02": (11, 0, 180),
    "U03": (0, 9.6, 90), "C12": (-3.3, 5.3, 0), "C10": (0, 5.3, 0), "C13": (3.3, 5.3, 0),
    "R24": (-20.3, -9.0, 90), "R27": (20.3, 9.0, 90), "R30": (19.0, 16.3, 0),
}
for i, (x, y) in enumerate([(-11, -6.0), (-11, -9.35), (-11, -12.7), (-11, -16.05), (-15.6, -6.0), (-15.6, -9.35),
                            (-15.6, -12.7), (-6.4, -6.0), (-6.4, -9.35), (-6.4, -12.7)]):
    PORT[f"C{20 + i}"] = (x, y, 0)
for i, (x, y) in enumerate([(11, 6.0), (11, 9.35), (11, 12.7), (11, 16.05), (15.6, 6.0), (15.6, 9.35), (15.6, 12.7)]):
    PORT[f"C{31 + i}"] = (x, y, 180)
PORT_CENTRE = {"4": (158, 31.5), "5": (158, 68.5)}
PORT_EXTRA = {  # board offsets from the port centre for the PD controller side (not turned)
    "U01": (19, -8, 0), "D01": (28, 9, 0), "D02": (25, -4, 90), "D03": (25, 3.5, 90),
    "U04": (23, 15.5, 0), "L02": (30, 14.5, 0), "C43": (25.5, -14.5, 0), "U02": (8, -16, 0), "J02": (-18, 14, 90),
}


def k(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(ORIGIN[0] + x), pcbnew.FromMM(ORIGIN[1] + y))


PRO = os.path.join(HERE, "..", "MonolithDev.kicad_pro")
pro_backup = open(PRO, encoding="utf-8").read()      # pcbnew's save rewrites the project with default rules
board = pcbnew.LoadBoard(PCB)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

# ---- 1. mechanical --------------------------------------------------------------------------------------
for ref, (x, y) in HOLES.items():
    fps[ref].SetPosition(k(x, y))
for ref, yc in (("J401", USB_Y[0]), ("J501", USB_Y[1])):
    fps[ref].SetLocked(False)
    fps[ref].SetOrientationDegrees(90)
    fps[ref].SetPosition(k(W, yc))
    fps[ref].SetLocked(True)

# ---- 2. hand placement ----------------------------------------------------------------------------------
placed = {}


def put(ref, x, y, rot):
    fp = fps[ref]
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(k(x, y))
    placed[ref] = fp


for ref, (x, y, r) in FIXED.items():
    put(ref, x, y, r)
for blk, (cx, cy) in PORT_CENTRE.items():
    for suf, (x, y, r) in PORT.items():
        put(suf[0] + blk + suf[1:], cx - x, cy - y, (r + 180) % 360)
    for suf, (x, y, r) in PORT_EXTRA.items():
        put(suf[0] + blk + suf[1:], cx + x, cy + y, r)
for ref in list(HOLES) + ["J401", "J501"]:
    placed[ref] = fps[ref]


# ---- 3. auto placement ----------------------------------------------------------------------------------
def crt_tp(fp):
    """Test points reserve room for their net-name label above them (placed there in the silk pass)."""
    r = crt(fp)
    if fp.GetReference().startswith("TP"):
        r = (r[0] - pcbnew.FromMM(2.2), r[1] - pcbnew.FromMM(1.6), r[2] + pcbnew.FromMM(2.2), r[3])
    return r


def crt(fp, margin=0.25):
    """Courtyard bounding box (F.CrtYd graphics, else pads) in board units, grown by margin mm."""
    bbs = [g.GetBoundingBox() for g in fp.GraphicalItems() if g.GetLayer() == pcbnew.F_CrtYd]
    if not bbs:
        bbs = [p.GetBoundingBox() for p in fp.Pads()]
    m = pcbnew.FromMM(margin)
    return (min(b.GetLeft() for b in bbs) - m, min(b.GetTop() for b in bbs) - m,
            max(b.GetRight() for b in bbs) + m, max(b.GetBottom() for b in bbs) + m)


def hit(r, rects):
    return any(r[0] < q[2] and q[0] < r[2] and r[1] < q[3] and q[1] < r[3] for q in rects)


rects = [crt(fp) for ref, fp in placed.items()]
a, b = k(141, 0), k(159, 4.2)              # STM32WB1MMC antenna end (pin-1 end, top edge): nothing else here
rects.append((a.x, a.y, b.x, b.y))
for yc in USB_Y:                          # keep the "USB n" label spot (silk pass) free
    a, b = k(W - 7.2, yc - 9.4), k(W - 0.2, yc - 7.4)
    rects.append((a.x, a.y, b.x, b.y))
holder_keepout = [(pcbnew.FromMM(ORIGIN[0] + 0), pcbnew.FromMM(ORIGIN[1]), pcbnew.FromMM(ORIGIN[0] + 109.5),
                   pcbnew.FromMM(ORIGIN[1] + H))]
pads_by_net = {}
for ref, fp in placed.items():
    for p in fp.Pads():
        pads_by_net.setdefault(p.GetNetname(), []).append(p.GetPosition())


def target(fp):
    pts = []
    for p in fp.Pads():
        n = p.GetNetname()
        if n and n != "GND" and not n.startswith("unconnected") and n in pads_by_net:
            pts += pads_by_net[n]
    if not pts:
        return None
    return (sum(q.x for q in pts) / len(pts), sum(q.y for q in pts) / len(pts))


def block(ref):
    m = re.match(r"[A-Z]+(\d+)$", ref)
    d = m.group(1) if m else "0"
    return d[0] if len(d) == 3 else "0"


todo = [r for r in fps if r not in placed]
todo.sort(key=lambda r: -(lambda b: b[2] - b[0])(crt(fps[r], 0)) * (lambda b: b[3] - b[1])(crt(fps[r], 0)))
failed = []
for npass in range(3):                   # pass 2: parts whose neighbours were placed later; pass 3: any region
    for ref in [r for r in todo if r not in placed]:
        fp = fps[ref]
        t = target(fp)
        x0, y0, x1, y1 = REGION[block(ref) if npass < 2 else "0"]
        if t is None:
            t = (pcbnew.FromMM(ORIGIN[0] + (x0 + x1) / 2), pcbnew.FromMM(ORIGIN[1] + (y0 + y1) / 2))
        best = None
        step = pcbnew.FromMM(0.5)
        for rot in (0, 90):
            fp.SetOrientationDegrees(rot)
            for ring in range(0, 120):
                cands = []
                for i in range(-ring, ring + 1):
                    for j in (-ring, ring):
                        cands += [(i, j), (j, i)]
                found = None
                for i, j in sorted(set(cands), key=lambda c: math.hypot(*c)):
                    x, y = t[0] + i * step, t[1] + j * step
                    fp.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
                    r = crt_tp(fp)
                    if r[0] < pcbnew.FromMM(ORIGIN[0] + x0) or r[2] > pcbnew.FromMM(ORIGIN[0] + x1) or \
                       r[1] < pcbnew.FromMM(ORIGIN[1] + y0) or r[3] > pcbnew.FromMM(ORIGIN[1] + y1):
                        continue
                    if hit(r, rects) or hit(r, holder_keepout):
                        continue
                    found = (math.hypot(i, j), rot, x, y)
                    break
                if found:
                    break
            if found and (best is None or found[0] < best[0]):
                best = found
        if best is None:
            failed.append(ref)
            continue
        _, rot, x, y = best
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
        placed[ref] = fp
        rects.append(crt_tp(fp))
        for p in fp.Pads():
            pads_by_net.setdefault(p.GetNetname(), []).append(p.GetPosition())
    todo = [r for r in todo if r not in placed]

# ---- 4. silkscreen: labels only where the spec asks (test points by net name, connectors, jumpers, holders)
for ref, fp in fps.items():
    pre = re.match(r"[A-Z]+", ref).group(0)
    fp.Reference().SetVisible(pre in ("J", "JP", "BT") and ref not in ("J401", "J501"))
    if pre == "TP":
        v = fp.Value()
        v.SetLayer(pcbnew.F_SilkS)
        v.SetVisible(True)
        v.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
        v.SetTextThickness(pcbnew.FromMM(0.15))
        v.SetTextAngleDegrees(0)


def box(b, m=0.15):
    m = pcbnew.FromMM(m)
    return (b.GetLeft() - m, b.GetTop() - m, b.GetRight() + m, b.GetBottom() + m)


# test-point labels: first free spot around the pad, clear of pads, footprint silk and earlier labels
obst = []
for fp in fps.values():
    obst += [box(p.GetBoundingBox()) for p in fp.Pads()]
    obst += [box(g.GetBoundingBox(), 0.1) for g in fp.GraphicalItems() if g.GetLayer() == pcbnew.F_SilkS]
    if fp.Reference().IsVisible() and not re.match(r"JP?\d", fp.GetReference()):
        obst.append(box(fp.Reference().GetBoundingBox(), 0.1))
edge = (pcbnew.FromMM(ORIGIN[0] + 0.5), pcbnew.FromMM(ORIGIN[1] + 0.5),
        pcbnew.FromMM(ORIGIN[0] + W - 0.5), pcbnew.FromMM(ORIGIN[1] + H - 0.5))
unplaced_labels, port_labels = [], []
for ref, fp in sorted(fps.items(), key=lambda kv: not kv[0].startswith("J")):
    if not (ref.startswith("TP") or re.match(r"JP?\d", ref)):
        continue
    v, c = (fp.Value(), fp.GetPosition()) if ref.startswith("TP") else (fp.Reference(), fp.GetPosition())
    orig = v.GetText()
    port = re.match(r"TP([45])\d\d$", ref)
    if port:                              # both ports share net names: label them P1 / P2 on the board
        v.SetText(f"P{int(port.group(1)) - 3} {orig}")
    if not ref.startswith("TP"):          # connectors: start from the courtyard edges
        x0, y0, x1, y1 = crt(fp, 0)
        hw, hh = (x1 - x0) / 2e6, (y1 - y0) / 2e6
        cands = [(0, -hh - 0.8), (0, hh + 0.8), (-hw - 2.0, 0), (hw + 2.0, 0), (-hw - 3.5, 0), (hw + 3.5, 0),
                 (0, -hh - 1.8), (0, hh + 1.8), (-hw + 1, -hh - 0.8), (hw - 1, hh + 0.8)]
        c = pcbnew.VECTOR2I((x0 + x1) // 2, (y0 + y1) // 2)
        v.SetTextAngleDegrees(0)
    else:
        cands = None
    for dx, dy in cands or [(0, -2.3), (0, -2.0), (0, 2.0), (-3.2, 0), (3.2, 0), (0, -2.8), (0, 2.8), (-4.2, 0), (4.2, 0),
                   (-3, -2), (3, -2), (-3, 2), (3, 2), (0, -3.6), (0, 3.6), (-5.5, 0), (5.5, 0)]:
        v.SetPosition(pcbnew.VECTOR2I(c.x + pcbnew.FromMM(dx), c.y + pcbnew.FromMM(dy)))
        r = box(v.GetBoundingBox(), 0.05)
        if r[0] > edge[0] and r[1] > edge[1] and r[2] < edge[2] and r[3] < edge[3] and not hit(r, obst):
            obst.append(r)
            if port:
                port_labels.append((v.GetText(), v.GetPosition()))
                v.SetText(orig)
                v.SetVisible(False)
            break
    else:
        unplaced_labels.append(ref)
print("test-point labels without a free spot:", unplaced_labels)

# outline last: creating PCB_SHAPEs earlier breaks the SWIG wrappers of footprint graphics
for d in list(board.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts or (d.GetLayer() == pcbnew.F_SilkS and d.GetClass() == "PCB_TEXT"):
        board.Remove(d)
segs = [((0, 0), (W, 0)), ((0, H), (W, H)), ((0, 0), (0, H))]
y = 0.0
for yc in USB_Y:
    segs.append(((W, y), (W, yc - NOTCH_W / 2)))
    y = yc + NOTCH_W / 2
segs.append(((W, y), (W, H)))
for a, b in segs:
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(k(*a)); s.SetEnd(k(*b))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1))
    board.Add(s)
for txt, pos in port_labels:               # P1/P2 test-point labels as board text (values stay as in the schematic)
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8))); t.SetTextThickness(pcbnew.FromMM(0.15))
    t.SetPosition(pos)
    board.Add(t)
for txt, yc in (("USB 1", USB_Y[0]), ("USB 2", USB_Y[1])):     # port labels beside the connectors
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(1.2))); t.SetTextThickness(pcbnew.FromMM(0.2))
    t.SetPosition(k(W - 3.6, yc - 8.4))                       # just above the connector's courtyard
    board.Add(t)
board.Save(PCB)
open(PRO, "w", encoding="utf-8", newline="\n").write(pro_backup)
print(f"placed {len(placed)} / {len(fps)}; not placed: {sorted(set(failed) - set(placed))}")
