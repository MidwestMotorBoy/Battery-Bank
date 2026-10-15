"""Block placement for the Monolith dev board (rev A7, 6-layer): every part inside its subsystem's zone.

Zones (board mm from the top-left corner; the cells' holders take x < 103):
    gauge column   x 104-134   Cells and Gauge sheet (BQ40Z50, BQ294700 second protector, pack connector)
    MCU band       y 0-13      MCU and NTCs sheet (module at the top edge, headers, sensor pull-ups)
    port 1 / 2     x 134-196   USB Port sheet, one 36 mm band per USB-C connector (port 2 = port 1 moved 36 mm down)
    sleep band     y 88-115    Sleep Current and 3V3 sheet

The gauge, MCU and sleep blocks keep the positions they already have (tools/place_parts.py placed them before the
layout reset); this script adds the parts that are not placed yet and lays the port block out again around the
discrete half-bridges and the 10 x 11.5 mm inductor. Rev A7 (CC2340R5MODA, TMP1075 sensors) re-places the U301
corner of the MCU band (MCU_LAYOUT) and puts the sensors on the copper they measure (SENSOR_LAYOUT).

Port power stage (port 1, centred on the inductor at (157, 32), the connector's centre line):
  output bank | Q402/Q408 | L401 | Q407/Q401 | input bank
  Each half-bridge is a vertical pair turned so both switch-node sides face the inductor pad. The pair's other side
  carries the high-side drain over the low-side source, and the 0603 HF cap (C430 / C438) stands across that joint:
  the smallest loop on the board. The 22u MLCCs continue the same row (same two copper strips), the polymer bulk
  sits one step further out. Gate resistors sit at each FET's gate pin, the BQ25756 sits above the inductor with
  its gate-drive pins facing down, the bootstrap / DRV_SUP / REGN parts in one row between them.

    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/place_blocks.py
Only footprint positions change (no tracks, silkscreen text or outline). The .kicad_pro is restored after the save.
"""
import math
import os
import re
import sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "MonolithDev.kicad_pcb")
PRO = os.path.join(HERE, "..", "MonolithDev.kicad_pro")
ORIGIN = (50.0, 50.0)
W, H = 196.0, 115.0
PORT_DY = 36.0                       # J501 sits 36 mm below J401

# ("fix", ref, x, y, rot)  courtyard centred on (x, y), exact rotation
# ("at",  ref, x, y, rot)  same, but rot or rot+180, whichever puts the pads nearer their nets (2-pin parts)
# ("best", ref, x, y)      the rotation (0/90/180/270) that puts the pads nearest their nets (ICs)
# ("col", refs, x, top, rot, gap) / ("row", refs, left, y, rot, gap): stacked courtyards
PORT_LAYOUT = [
    # ---- power stage ----
    ("fix", "L401", 157.0, 32.0, 180),                        # pad 1 (SW1) right, pad 2 (SW2) left
    ("fix", "Q407", 166.45, 30.15, 90), ("fix", "Q401", 166.45, 33.85, 270),   # input bridge: LS over HS
    ("fix", "Q402", 147.55, 30.15, 90), ("fix", "Q408", 147.55, 33.85, 270),   # output bridge: HS over LS
    ("fix", "C430", 169.5, 32.0, 90),                         # AC_SNS_N pad down on Q401's drain, GND up on Q407's source
    ("fix", "C423", 172.0, 32.0, 90), ("fix", "C420", 175.4, 32.0, 90),
    ("fix", "C424", 178.8, 32.0, 90), ("fix", "C427", 182.2, 32.0, 90),
    ("fix", "C438", 144.5, 32.0, 270),                        # BAT_SNS_P pad up on Q402's drain, GND down on Q408's source
    ("fix", "C431", 142.45, 32.0, 270), ("fix", "C434", 139.95, 32.0, 270), ("fix", "C435", 137.45, 32.0, 270),
    ("fix", "C421", 174.85, 38.95, 0),                        # input polymer under the AC_SNS_N strip, + pad left
    ("fix", "C432", 143.05, 24.7, 0),                         # output polymer over the BAT_SNS_P strip, + pad left
    ("fix", "R427", 136.25, 26.0, 90),                        # RBAT: BAT_SNS_P pad down at the output strip
    ("fix", "R430", 136.4, 18.9, 90),                         # 10 A link: VBAT_SYS down, PACK_P up to the pack bus
    ("fix", "R424", 184.75, 36.6, 180),                       # RAC: AC_SNS_N pad left under C427, PPHV right
    # gate resistors at each gate pin; DNP RC snubbers from each switch node, under the bridges
    ("at", "R445", 168.0, 26.6, 90), ("at", "R446", 149.1, 26.6, 90),
    ("at", "R444", 164.95, 37.6, 90), ("at", "R447", 146.05, 37.6, 90),
    ("at", "R450", 167.1, 37.6, 90), ("at", "C454", 169.1, 37.6, 90),
    ("at", "R451", 148.0, 37.6, 90), ("at", "C455", 144.1, 37.6, 90),
    # ---- BQ25756 above the inductor, gate-drive pins down ----
    ("fix", "U403", 157.0, 19.5, 270),
    ("row", ["C413", "D405", "R449", "C411", "R420", "C410", "R448", "D404", "C412"], 150.1, 24.6, 90, 0.2),
    ("row", ["R414", "R413", "R416", "R415", "TH401", "R417", "R435"], 150.2, 14.85, 90, 0.2),   # ILIM .. CE pins
    ("col", ["C417", "C418", "C419"], 151.5, 16.55, 0, 0.15),         # SRP/SRN filter at the SRP/SRN pins
    ("col", ["R428", "R429"], 148.0, 16.55, 0, 0.15),                 # SRP/SRN series resistors
    ("col", ["R418", "R419"], 143.6, 14.2, 0, 0.15),                  # FB divider
    ("col", ["R412", "R410", "R409"], 162.6, 16.55, 0, 0.15),         # FSW, ACUV/ACOV divider
    ("col", ["C414", "C415", "C416"], 166.0, 16.55, 0, 0.15),         # ACP/ACN filter
    ("col", ["R425", "R426", "R411"], 169.6, 16.55, 0, 0.15),
    # ---- TPS25751 right of the controller, EEPROM and supply caps around it ----
    ("fix", "U401", 178.5, 23.0, 0),
    ("col", ["C403", "R401", "C404", "C408", "C405", "R1", "R2"], 173.2, 15.5, 0, 0.1),
    ("at", "C407", 177.2, 18.9, 0),
    ("at", "C401", 179.6, 18.9, 90), ("at", "C402", 180.8, 18.9, 90),
    ("best", "U402", 177.5, 15.9),
    ("col", ["R404", "R402", "R403"], 181.6, 12.6, 0, 0.1),
    ("at", "C450", 183.2, 21.5, 90), ("at", "C449", 183.2, 24.6, 90), ("at", "C406", 185.6, 22.5, 90),
    ("at", "C409", 164.2, 15.4, 0),                           # VAC cap by the PPHV pins
    ("row", ["R421", "R422", "R423"], 166.0, 14.55, 90, 0.2),  # STAT1 / STAT2 / PG pull-ups
    # ---- TPD4S201 above the connector: connector-side pins down ----
    ("fix", "U405", 189.4, 22.8, 90),
    ("at", "C451", 188.0, 18.9, 0), ("at", "C452", 191.2, 18.9, 0), ("at", "R441", 194.3, 18.9, 0),
    ("at", "R440", 184.6, 27.0, 0),
    ("fix", "D401", 188.0, 41.0, 0),
    # liquid detection (TPS25751 fig. 9-8) in the corner above the connector: pull-up FETs, pull-down FETs,
    # their resistors in a column along the board edge
    ("fix", "Q403", 185.2, 10.0, 0), ("fix", "Q404", 189.6, 10.0, 0),           # drains (pin 3) toward the resistors
    ("fix", "Q405", 185.2, 15.6, 0), ("fix", "Q406", 189.6, 15.6, 0),
    ("col", ["R442", "R436", "R437", "R438", "R439", "R443"], 194.2, 8.1, 0, 0.1),
    # ---- PP5V buck along the bottom: input caps, IC, inductor, output caps; EN/SS/FB parts in a row under it ----
    ("at", "R431", 136.3, 38.5, 0),                           # PACK_P -> 5V_IN solder jumper
    ("at", "C444", 137.5, 43.6, 90), ("at", "C445", 140.1, 43.6, 90), ("at", "C446", 142.3, 44.1, 90),
    ("best", "U404", 144.8, 43.6),
    ("at", "C440", 147.2, 44.1, 90),
    ("fix", "L402", 151.7, 43.6, 0),
    ("at", "C441", 156.4, 43.6, 90), ("at", "C442", 158.9, 43.6, 90),
    ("fix", "C443", 165.25, 45.35, 0),
    ("row", ["R432", "C439", "R434", "R433", "C447"], 136.0, 47.55, 0, 0.2),
    # ---- test points: SW/GND probe loops under the inductor, logic and rail pads in a 2 x 4 field under the
    # input polymer, VBUS / PPHV beside the connector; I2CC logic-analyzer header in the top-left corner ----
    ("fix", "TP406", 152.0, 39.0, 0), ("fix", "TP412", 155.4, 39.0, 0), ("fix", "TP405", 162.3, 39.0, 0),
    ("fix", "TP407", 171.75, 44.25, 0), ("fix", "TP408", 174.9, 44.25, 0),
    ("fix", "TP409", 178.05, 44.25, 0), ("fix", "TP410", 181.2, 44.25, 0),
    ("fix", "TP411", 171.75, 47.25, 0), ("fix", "TP404", 174.9, 47.25, 0),
    ("fix", "TP403", 178.05, 47.25, 0), ("fix", "TP414", 181.2, 47.25, 0),
    ("fix", "TP413", 143.5, 19.8, 0),
    ("fix", "TP401", 194.3, 22.6, 0), ("fix", "TP402", 193.8, 39.85, 0),
    ("fix", "J402", 140.05, 16.7, 0),
]

# parts placed by the nearest-free-spot pass inside the port zone (both copies must fit)
PORT_AUTO = []

# CC2340R5MODA (SWRS349A fig. 9-1 / 9-2): antenna (pin-1) end at the top edge, courtyard on the edge. The RF match
# sits in the corner left of RFIO (pin 4) / ANT_IN (pin 3): C313 (CA1) and R321 (Z61) in series, pads facing their
# pins, joined on the left where C314 (Z60, DNP) shunts the node to GND; C315 (Z62) stands on ANT_IN with its GND
# pad up beside the module's GND pin 1. Below the match one column by the 3V3_MCU pins 6/7: the two 0.1u, the 4.7u,
# then the RSTN pull-up and cap. The pins left of the 7.0 x 3.2 mm keep-out stay clear; the keep-out itself is in
# the footprint.
MCU_LAYOUT = [
    ("fix", "U301", 150.0, 5.45, 0),
    ("at", "C315", 145.33, 1.36, 90),
    ("at", "R321", 144.85, 2.88, 0), ("at", "C313", 144.85, 3.91, 0),
    ("at", "C314", 142.9, 3.395, 0),
    ("at", "C302", 144.85, 5.9, 0), ("at", "C303", 144.85, 6.92, 0),
    ("at", "C301", 144.35, 8.25, 0), ("at", "R302", 144.35, 9.85, 0), ("at", "C304", 144.85, 11.2, 0),
]

# TMP1075 board sensors (MCU sheet, placed after the ports), exposed pad (GND) on the copper being measured with
# its thermal vias into the GND planes, the 0.1u at the V+ pin: U302/U303 under each output bank's PGND strip
# beside the output bridge, U304 between the connectors, U305 (DNP) under port 1's inductor, U306 (DNP) between
# the protection FETs with C110/C111 (the cap across the FETs) moved into the gap beside it, CELL_P cap up at Q101.
SENSOR_LAYOUT = [
    ("fix", "U302", 140.4, 36.4, 0), ("at", "C308", 142.6, 36.4, 90),
    ("fix", "U303", 140.4, 36.4 + PORT_DY, 0), ("at", "C309", 142.6, 36.4 + PORT_DY, 90),
    ("fix", "U304", 193.15, 42.62, 0), ("at", "C310", 195.25, 42.62, 90),
    ("fix", "U305", 158.85, 38.85, 0), ("at", "C311", 158.85, 40.7, 0),
    ("fix", "U306", 130.0, 28.0, 90), ("at", "C312", 127.9, 28.0, 90),
    ("at", "C110", 132.95, 27.2, 0), ("at", "C111", 132.95, 28.8, 0),
]

# second-level protector (BQ294700) under the gauge, beside the fuse it blows: tap resistors in a column at the
# cell-tap side, caps between adjacent taps right at the V pins, the heater FET by the fuse's heater pin
GAUGE_LAYOUT = [
    ("fix", "F102", 113.5, 96.0, 0),
    ("at", "R127", 113.5, 90.0, 0),                           # DNP fuse bypass (2512) above the fuse
    ("best", "Q104", 120.8, 96.0),
    ("col", ["R125", "R124", "R126", "C118"], 125.3, 93.0, 0, 0.15),
    ("best", "U102", 119.5, 82.5),
    ("col", ["R119", "R120", "R121", "R122"], 111.0, 79.0, 0, 0.15),
    ("col", ["C112", "C113", "C114", "C115"], 115.0, 79.0, 0, 0.15),
    ("col", ["R123", "C116", "C117"], 124.0, 79.5, 0, 0.15),
    ("at", "C105", 118.75, 37.2, 90),                         # 1206 now: clear of R105
]
# HT7550-1 (SOT-89) LDO for the amplifiers: input cap left, output cap right, probe pads above
SLEEP_LAYOUT = [
    ("at", "C204", 143.4, 107.0, 90), ("best", "U203", 147.3, 107.0), ("at", "C205", 151.1, 107.0, 90),
    ("fix", "TP206", 145.5, 101.4, 0), ("fix", "TP207", 149.0, 101.6, 0),
]
GAUGE_ZONE = (104.0, 13.0, 134.4, 102.4)
PORT_ZONE = (134.4, 7.6, 196.0, 49.2)


def k(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(ORIGIN[0] + x), pcbnew.FromMM(ORIGIN[1] + y))


pro_backup = open(PRO, encoding="utf-8").read()
board = pcbnew.LoadBoard(PCB)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}


def crt(fp, margin=0.0):
    """Courtyard bounding box (board units), grown by margin mm."""
    c = fp.GetCourtyard(pcbnew.F_CrtYd)
    if c.OutlineCount():
        bb = c.BBox()
        r = (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())
    else:
        bbs = [p.GetBoundingBox() for p in fp.Pads()]
        r = (min(b.GetLeft() for b in bbs), min(b.GetTop() for b in bbs),
             max(b.GetRight() for b in bbs), max(b.GetBottom() for b in bbs))
    m = pcbnew.FromMM(margin)
    return (r[0] - m, r[1] - m, r[2] + m, r[3] + m)


def hit(r, rects):
    return any(r[0] < q[2] and q[0] < r[2] and r[1] < q[3] and q[1] < r[3] for q in rects)


def box_at(fp, rot, cx, cy):
    """Turn fp to rot and move it so its courtyard centre lands on board mm (cx, cy)."""
    fp.SetOrientationDegrees(rot % 360)
    fp.SetPosition(k(cx, cy))
    r = crt(fp)
    p = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(p.x - ((r[0] + r[2]) // 2 - p.x), p.y - ((r[1] + r[3]) // 2 - p.y)))


placed = {}


def pad_score(fp):
    """Summed distance from each signal pad to the nearest placed pad on the same net (GND ignored)."""
    s = 0
    for p in fp.Pads():
        n = p.GetNetname()
        if not n or n == "GND" or n.startswith("unconnected"):
            continue
        pts = [q.GetPosition() for f in placed.values() if f is not fp for q in f.Pads() if q.GetNetname() == n]
        if pts:
            s += min(math.hypot(p.GetPosition().x - q.x, p.GetPosition().y - q.y) for q in pts)
    return s


def put_best(ref, cx, cy, rots):
    fp = fps[ref]
    best = None
    for r in rots:
        box_at(fp, r, cx, cy)
        sc = pad_score(fp)
        if best is None or sc < best[0] - 1:
            best = (sc, r)
    box_at(fp, best[1], cx, cy)
    placed[ref] = fp


def size(ref, rot):
    fp = fps[ref]
    fp.SetOrientationDegrees(rot % 360)
    r = crt(fp)
    return pcbnew.ToMM(r[2] - r[0]), pcbnew.ToMM(r[3] - r[1])


def run_layout(items):
    done = []
    for it in items:
        kind = it[0]
        if kind == "fix":
            _, ref, x, y, rot = it
            box_at(fps[ref], rot, x, y)
            placed[ref] = fps[ref]
            done.append(ref)
        elif kind == "at":
            _, ref, x, y, rot = it
            put_best(ref, x, y, (rot, rot + 180))
            done.append(ref)
        elif kind == "best":
            _, ref, x, y = it
            put_best(ref, x, y, (0, 90, 180, 270))
            done.append(ref)
        elif kind == "col":
            _, refs, x, y, rot, gap = it
            for ref in refs:
                h = size(ref, rot)[1]
                put_best(ref, x, y + h / 2, (rot, rot + 180))
                y += h + gap
                done.append(ref)
        elif kind == "row":
            _, refs, x, y, rot, gap = it
            for ref in refs:
                w = size(ref, rot)[0]
                put_best(ref, x + w / 2, y, (rot, rot + 180))
                x += w + gap
                done.append(ref)
    return done


def port2(ref):
    return {"R1": "R3", "R2": "R4"}.get(ref) or re.sub(r"^([A-Z]+)4(\d\d)$", r"\g<1>5\2", ref)


def copy_to_port2(ref):
    a, b = fps[ref], fps[port2(ref)]
    b.SetOrientationDegrees(a.GetOrientationDegrees())
    b.SetPosition(pcbnew.VECTOR2I(a.GetPosition().x, a.GetPosition().y + pcbnew.FromMM(PORT_DY)))
    placed[port2(ref)] = b


DY = pcbnew.FromMM(PORT_DY)
port_refs = set()
missing = sorted(f.GetReference() for f in fps.values() if f.GetSheetname() == "USB Port 1"
                 and f.GetReference() not in {it[1] for it in PORT_LAYOUT if isinstance(it[1], str)}
                 | {r for it in PORT_LAYOUT if isinstance(it[1], list) for r in it[1]} | set(PORT_AUTO))
print("port 1 parts with no place in the layout:", missing)
for ref in run_layout(PORT_LAYOUT):
    copy_to_port2(ref)
    port_refs.add(ref)

# everything that is not re-placed here keeps its position and is an obstacle
redo = set(port_refs) | {port2(r) for r in port_refs} | set(PORT_AUTO) | {port2(r) for r in PORT_AUTO}
redo |= {it[1] for it in MCU_LAYOUT + SENSOR_LAYOUT + GAUGE_LAYOUT + SLEEP_LAYOUT if isinstance(it[1], str)}
redo |= {r for it in GAUGE_LAYOUT if isinstance(it[1], list) for r in it[1]}
for ref, fp in fps.items():
    if ref not in redo:
        placed[ref] = fp
run_layout(GAUGE_LAYOUT)
run_layout(SLEEP_LAYOUT)
run_layout(MCU_LAYOUT)
run_layout(SENSOR_LAYOUT)

# ---- nearest-free-spot pass for the remaining port parts (port 1 and its port 2 copy must both be free) --------
MARGIN = 0.15


def zone_ok(r, zone):
    x0, y0, x1, y1 = (pcbnew.FromMM(v + o) for v, o in zip(zone, (ORIGIN[0], ORIGIN[1], ORIGIN[0], ORIGIN[1])))
    return r[0] >= x0 and r[1] >= y0 and r[2] <= x1 and r[3] <= y1


def obstacles():
    return [crt(f, MARGIN) for f in placed.values()]


def shift(r, d):
    return (r[0], r[1] + d, r[2], r[3] + d)


def target(fp):
    pts = []
    for p in fp.Pads():
        n = p.GetNetname()
        if not n or n == "GND" or n.startswith("unconnected"):
            continue
        for f in placed.values():
            if f is fp:
                continue
            pts += [q.GetPosition() for q in f.Pads() if q.GetNetname() == n]
    if not pts:
        return None
    return (sum(q.x for q in pts) / len(pts), sum(q.y for q in pts) / len(pts))


failed = []
step = pcbnew.FromMM(0.25)
for ref in PORT_AUTO:
    fp = fps[ref]
    t = target(fp) or (k(165, 40).x, k(165, 40).y)
    obs = obstacles()
    best = None
    for rot in (0, 90):
        fp.SetOrientationDegrees(rot)
        found = None
        for ring in range(0, 160):
            cands = set()
            for i in range(-ring, ring + 1):
                for j in (-ring, ring):
                    cands.add((i, j)); cands.add((j, i))
            for i, j in sorted(cands, key=lambda c: math.hypot(*c)):
                fp.SetPosition(pcbnew.VECTOR2I(int(t[0] + i * step), int(t[1] + j * step)))
                r = crt(fp, MARGIN)
                if not zone_ok(r, PORT_ZONE) or not zone_ok(shift(r, DY), (0, 0, W, H)):
                    continue
                if hit(r, obs) or hit(shift(r, DY), obs):
                    continue
                found = (math.hypot(i, j), rot, fp.GetPosition())
                break
            if found:
                break
        if found and (best is None or found[0] < best[0]):
            best = found
    if best is None:
        failed.append(ref)
        continue
    fp.SetOrientationDegrees(best[1])
    fp.SetPosition(best[2])
    placed[ref] = fp
    copy_to_port2(ref)

# ---- checks ---------------------------------------------------------------------------------------------
boxes = {ref: crt(fp) for ref, fp in fps.items() if not ref.startswith("H")}
refs = sorted(boxes)
clash = [(a, b) for i, a in enumerate(refs) for b in refs[i + 1:] if hit(boxes[a], [boxes[b]])]
outside = [r for r, b in boxes.items() if not zone_ok(b, (-0.01, -0.01, W + 7.0, H + 0.01))]
print("courtyard overlaps:", clash)
print("outside the board:", outside)
print("auto pass failed:", failed)
if "--dry" not in sys.argv:
    board.Save(PCB)
    open(PRO, "w", encoding="utf-8", newline="\n").write(pro_backup)
    print("saved")
