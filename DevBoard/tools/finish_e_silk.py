"""Finish-routing stage E (2026-10-17): the silkscreen pass (port of the rev A5 pass in place_parts.py).

Labels only where the spec asks: reference designators stay visible on connectors, jumpers and holders only (the
USB-C receptacles get "USB 1" / "USB 2"); test points carry their net name; headers get pin labels; switches and
jumpers get their purpose; block titles, the board name / revision and the cell warning go in free spots. Every
label is placed at the first spot that is clear of pads, footprint silk, other labels, other parts' courtyards and
the board edge; a label with no clear spot is hidden rather than printed over something. Existing board-level
silkscreen texts are replaced (re-runnable).
Run from DevBoard/ with KiCad's python; restores MonolithDev.kicad_pro after saving.
"""
import os
import re

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
PCB = os.path.join(ROOT, "MonolithDev.kicad_pcb")
PRO = os.path.join(ROOT, "MonolithDev.kicad_pro")
mm, MM = pcbnew.FromMM, pcbnew.ToMM
TXT_H = 0.8
REV, DATE = "A8", "2026-10-17"

PIN_LABELS = {
    "J102": {"1": "TS1", "2": "-"}, "J105": {"1": "TS2", "2": "-"},
    "J106": {"1": "TS3", "2": "-"}, "J107": {"1": "TS4", "2": "-"},
    "J103": {"1": "GND", "2": "SCL", "3": "SDA", "4": "NC"},
    "J104": {"1": "+", "2": "-"},
    "J303": {"1": "3V3", "2": "IRQ", "3": "NC", "4": "5V1", "5": "5V2", "6": "INH", "7": "G"},
    "J402": {"1": "SDA", "2": "SCL", "3": "G"}, "J502": {"1": "SDA", "2": "SCL", "3": "G"},
    "J302": {"1": "TX", "2": "RX", "3": "G"},
    "J301": {"1": "1"},
}
PART_LABELS = {"SW101": "WAKE", "SW301": "RESET", "JP201": "AMP EN", "JP202": "MEAS PWR", "J301": "SWD"}
# titles: text, size, candidates (x, y, rot) in absolute mm
TITLES = [
    ("PORT 1", 1.2, [(184.0, 72.0, 90), (186.0, 66.0, 90), (190.0, 60.0, 0), (212.0, 101.0, 0), (182.5, 100.5, 0),
                     (236.0, 62.0, 0), (210.0, 71.0, 90)]),
    ("PORT 2", 1.2, [(184.0, 108.0, 90), (186.0, 102.0, 90), (190.0, 96.0, 0), (212.0, 137.0, 0), (236.0, 98.0, 0)]),
    ("GAUGE", 1.2, [(172.0, 62.0, 0), (164.0, 77.0, 0), (157.0, 58.0, 0), (152.0, 119.0, 90), (169.0, 128.0, 0),
                    (152.5, 78.0, 90), (152.5, 100.0, 90), (165.0, 140.0, 0), (148.0, 85.0, 90)]),
    ("MCU", 1.2, [(165.0, 63.5, 0), (158.0, 55.0, 0), (182.0, 58.0, 0), (190.0, 53.0, 0), (177.0, 75.0, 0)]),
    ("SLEEP CURRENT", 1.2, [(205.0, 160.5, 0), (210.0, 156.0, 0), (170.0, 160.5, 0), (225.0, 160.5, 0)]),
    ("FIT CELLS BEFORE USB", 1.2, [(100.0, 162.6, 0), (100.0, 52.4, 0), (100.0, 161.0, 0), (100.0, 79.0, 0),
                                   (100.0, 107.0, 0), (100.0, 135.0, 0), (100.0, 157.5, 0)]),
    (f"MONOLITH DEV BOARD  rev {REV}  {DATE}", 1.2, [(100.0, 52.4, 0), (100.0, 162.6, 0), (100.0, 79.0, 0),
                                                     (100.0, 107.0, 0), (100.0, 135.0, 0), (100.0, 56.0, 0)]),
    ("USB 1", 1.2, [(241.0, 92.0, 0), (241.0, 71.5, 0)]),
    ("USB 2", 1.2, [(241.0, 128.0, 0), (241.0, 107.5, 0)]),
    ("not GND", 0.8, [(154.0, 59.3, 0), (154.0, 63.8, 0)]),                    # TP102: CELL_N, not the scope ground
]

pro = open(PRO, "rb").read()


def strip_silk_texts(path):
    """Remove the board-level F.SilkS gr_text blocks as text, before LoadBoard (removing them through the API
    poisons the footprint wrappers used later)."""
    s = open(path, encoding="utf-8").read()
    out, i, n = [], 0, 0
    while True:
        k = s.find("\n\t(gr_text ", i)
        if k < 0:
            out.append(s[i:])
            break
        d, j = 0, k + 1
        while True:
            c = s[j]
            if c == '"':
                j += 1
                while s[j] != '"':
                    j += 2 if s[j] == "\\" else 1
            elif c == "(":
                d += 1
            elif c == ")":
                d -= 1
                if d == 0:
                    break
            j += 1
        blk = s[k:j + 1]
        out.append(s[i:k])
        if '(layer "F.SilkS")' in blk:
            n += 1
        else:
            out.append(blk)
        i = j + 1
    open(path, "w", encoding="utf-8", newline="\n").write("".join(out))
    return n


print("old silk texts stripped:", strip_silk_texts(PCB))
b = pcbnew.LoadBoard(PCB)
fps = {f.GetReference(): f for f in b.GetFootprints()}
bb = b.GetBoardEdgesBoundingBox()
edge = (MM(bb.GetLeft()) + 0.5, MM(bb.GetTop()) + 0.5, MM(bb.GetRight()) - 0.5, MM(bb.GetBottom()) - 0.5)

# ---- 1. reference / value visibility
for ref, fp in fps.items():
    pre = re.match(r"[A-Z]+", ref).group(0)
    fp.Reference().SetVisible(pre in ("J", "JP", "BT") and ref not in ("J401", "J501"))
    if fp.Reference().IsVisible():
        fp.Reference().SetLayer(pcbnew.B_SilkS if fp.IsFlipped() else pcbnew.F_SilkS)
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        fp.Reference().SetTextThickness(mm(0.15))
    fp.Value().SetVisible(False)          # test points get a separate (abbreviated) label text below

# test-point labels: the net name, shortened to fit the 3.15 mm probe-field pitch at the 0.8 mm legend minimum
ABBREV = {"I2CC_SDA": "CSDA", "I2CC_SCL": "CSCL", "SBU_FLT": "SBUF", "LIQ_PU": "LQPU", "LIQ_PD": "LQPD",
          "SBU1_SNS": "SBU1", "SBU2_SNS": "SBU2", "LDO_3V3": "LDO33", "3V3_SLEEP": "SLEEP", "IRQ_N": "IRQ",
          "CELL_P": "CELL+", "CELL_N": "CELL-", "PACK_P": "PACK+", "PACK_LP": "PKLP", "AMP_EN": "AMPEN",
          "MEAS_P": "MEAS+", "MEAS_N": "MEAS-", "CHG_INT": "CHINT", "OUT_LO": "OUTLO", "OUT_HI": "OUTHI",
          "SMB_PU": "SMBPU", "LDO_IN": "LDOIN", "5V_AMP": "5VAMP", "BOOT0": "BOOT", "3V3_MCU": "3V3M",
          "GAUGE_FUSE": "FUSE", "GAUGE_BTP": "BTP", "FET_MID": "FMID", "PPHV": "PPHV", "VBUS": "VBUS"}


def tp_label(fp):
    t = fp.Value().GetText()
    t = ABBREV.get(t, t)
    return t if len(t) <= 5 else t.replace("_", "")[:5]


def rect(bx, m=0.0):
    return (MM(bx.GetLeft()) - m, MM(bx.GetTop()) - m, MM(bx.GetRight()) + m, MM(bx.GetBottom()) + m)


def hit(r, rects):
    return any(r[0] < c[2] and c[0] < r[2] and r[1] < c[3] and c[1] < r[3] for c in rects)


def crt(fp, m=0.0):
    cy = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
    return rect(cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False, False), m)


# ---- 2. obstacles: pads, footprint silk, visible references, courtyards (per owner)
obst = []
for ref, fp in fps.items():
    obst += [rect(p.GetBoundingBox(), 0.15) for p in fp.Pads()]
    obst += [rect(g.GetBoundingBox(), 0.1) for g in fp.GraphicalItems() if g.GetLayer() == pcbnew.F_SilkS]
    if fp.Reference().IsVisible() and not re.match(r"JP?\d", ref):
        obst.append(rect(fp.Reference().GetBoundingBox(), 0.1))
crts = {ref: crt(fp, 0.05) for ref, fp in fps.items()}
EXTRA = []                     # (text, x, y, angle, size)


def text_box(txt, x, y, ang=0, h=TXT_H):
    L = 0.85 * h * max(len(txt), 1) + 0.2          # KiCad's stroke font is wider than 0.72 h (labels overlapped)
    w, hh = (L, h + 0.2) if ang == 0 else (h + 0.2, L)
    return (x - w / 2, y - hh / 2, x + w / 2, y + hh / 2)


def free_spot(txt, x, y, owner=None, ang=0, h=TXT_H, over_holders=False):
    r = text_box(txt, x, y, ang, h)
    if not (r[0] > edge[0] and r[1] > edge[1] and r[2] < edge[2] and r[3] < edge[3]):
        return None
    courts = [c for o, c in crts.items() if o != owner and not (over_holders and o.startswith("BT"))]
    if hit(r, obst) or hit(r, courts):
        return None
    return r


# ---- 3. header pin labels
missing = []
for ref, labels in PIN_LABELS.items():
    fp = fps.get(ref)
    if fp is None:
        continue
    pads = {p.GetNumber(): p for p in fp.Pads()}
    pts = {n: (MM(p.GetPosition().x), MM(p.GetPosition().y)) for n, p in pads.items() if n in labels}
    if not pts:
        continue
    cx = sum(q[0] for q in pts.values()) / len(pts)
    cy = sum(q[1] for q in pts.values()) / len(pts)
    xs, ys = [q[0] for q in pts.values()], [q[1] for q in pts.values()]
    vertical = (max(ys) - min(ys)) >= (max(xs) - min(xs))
    cx0, cy0, cx1, cy1 = crts[ref]
    ang = 90 if vertical and ref != "J301" else 0

    def tang(txt):
        return 0 if txt in "+-" else ang

    def spot(n, txt, sgn):
        px, py = pts[n]
        L = 0.72 * TXT_H * len(txt) + 0.2
        if ref == "J301":
            sgn2 = 1 if px > cx else -1
            return px + sgn2 * ((cx1 - cx0) / 2 - abs(px - cx) + 0.25 + L / 2), py
        if vertical:
            half = TXT_H / 2 if tang(txt) else L / 2
            return ((cx1 + 0.25 + half) if sgn > 0 else (cx0 - 0.25 - half)), py
        return px, ((cy1 + 0.2 + TXT_H / 2) if sgn > 0 else (cy0 - 0.2 - TXT_H / 2))

    def fit(n, t, sgn, taken):
        x, y = spot(n, t, sgn)
        for d in (0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5):
            xx, yy = (x, y + d) if vertical else (x + d, y)
            bx = free_spot(t, xx, yy, ref, tang(t))
            if bx and not hit(bx, taken):
                return (t, xx, yy, tang(t), TXT_H), bx
        return None

    placed_all = False
    for sgn in (+1, -1):
        got = []
        for n, t in labels.items():
            if n not in pts:
                continue
            f = fit(n, t, sgn, [bx for _, bx in got])
            if not f:
                break
            got.append(f)
        else:
            for lab, bx in got:
                EXTRA.append(lab)
                obst.append(bx)
            placed_all = True
            break
    if not placed_all:
        for n, t in labels.items():
            if n not in pts:
                continue
            for sgn in (+1, -1):
                f = fit(n, t, sgn, [])
                if f:
                    EXTRA.append(f[0])
                    obst.append(f[1])
                    break
            else:
                missing.append(f"{ref}.{n}")

# ---- 4. part-purpose labels
for ref, txt in PART_LABELS.items():
    if ref not in fps:
        continue
    x0, y0, x1, y1 = crts[ref]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w = 0.72 * TXT_H * len(txt) + 0.2
    for x, y in ((cx, y0 - 0.65), (cx, y1 + 0.65), (x0 - w / 2 - 0.3, cy), (x1 + w / 2 + 0.3, cy),
                 (cx, y0 - 1.6), (cx, y1 + 1.6), (x0 - w / 2 - 1.2, cy), (x1 + w / 2 + 1.2, cy)):
        bx = free_spot(txt, x, y, ref)
        if bx:
            EXTRA.append((txt, x, y, 0, TXT_H))
            obst.append(bx)
            break
    else:
        missing.append(ref)
print("pin/part labels without room:", missing)

# ---- 5. test-point net labels and the visible connector references
hidden = []
for ref, fp in sorted(fps.items(), key=lambda kv: (not kv[0].startswith("TP"), kv[0])):
    is_tp = ref.startswith("TP")
    if not (is_tp or fp.Reference().IsVisible()):
        continue
    c = fp.GetPosition()
    if is_tp:
        txt = tp_label(fp)
        cx, cy = MM(c.x), MM(c.y)
        others = [cc for o, cc in crts.items() if o != ref and not o.startswith("TP")]
        for dx, dy, ang in [(0, -1.5, 0), (0, 1.5, 0), (-1.55, 0, 90), (1.55, 0, 90), (0, -2.3, 0), (0, 2.3, 0),
                            (-2.4, 0, 0), (2.4, 0, 0), (-2.3, 0, 90), (2.3, 0, 90), (-3.4, 0, 0), (3.4, 0, 0),
                            (-1.8, -1.4, 0), (1.8, -1.4, 0), (-1.8, 1.4, 0), (1.8, 1.4, 0), (0, -3.1, 0), (0, 3.1, 0)]:
            r = text_box(txt, cx + dx, cy + dy, ang)
            if r[0] > edge[0] and r[1] > edge[1] and r[2] < edge[2] and r[3] < edge[3] and not hit(r, obst) \
                    and not hit(r, others):
                EXTRA.append((txt, cx + dx, cy + dy, ang, TXT_H))
                obst.append(r)
                break
        else:
            hidden.append(ref)
        continue
    v = fp.Reference()
    if True:
        x0, y0, x1, y1 = crt(fp, 0)
        hw, hh = (x1 - x0) / 2, (y1 - y0) / 2
        cands = [(0, -hh - 0.8, 0), (0, hh + 0.8, 0), (-hw - 2.0, 0, 0), (hw + 2.0, 0, 0), (-hw - 3.5, 0, 0),
                 (hw + 3.5, 0, 0), (0, -hh - 1.8, 0), (0, hh + 1.8, 0), (-hw + 1, -hh - 0.8, 0), (hw - 1, hh + 0.8, 0),
                 (-hw - 0.8, 0, 90), (hw + 0.8, 0, 90), (-hw - 1.9, 0, 90), (hw + 1.9, 0, 90),
                 (-hw - 2.6, 0, 90), (hw + 2.6, 0, 90)]
        c = pcbnew.VECTOR2I(mm((x0 + x1) / 2), mm((y0 + y1) / 2))
        sizes = [(1.0, 0.15), (0.8, 0.15)]
    found = False
    for sz in sizes:
        v.SetTextSize(pcbnew.VECTOR2I(mm(sz[0]), mm(sz[0])))
        v.SetTextThickness(mm(sz[1]))
        for dx, dy, ang in cands:
            v.SetTextAngleDegrees(ang)
            v.SetPosition(pcbnew.VECTOR2I(c.x + mm(dx), c.y + mm(dy)))
            r = rect(v.GetBoundingBox(), 0.05)
            # a test-point label may sit over a neighbouring test point's courtyard (its pad is still an obstacle)
            others = [cc for o, cc in crts.items() if o != ref and not (is_tp and o.startswith("TP"))]
            if r[0] > edge[0] and r[1] > edge[1] and r[2] < edge[2] and r[3] < edge[3] and not hit(r, obst) \
                    and not hit(r, others):
                obst.append(r)
                found = True
                break
        if found:
            break
    if not found:
        v.SetVisible(False)
        hidden.append(ref)
print("labels hidden (no free spot):", hidden)

# ---- 6. titles, board name, warnings
for txt, h, cands in TITLES:
    # the board name and the cell warning may sit over a holder's (empty) courtyard, between its pads
    holders_ok = txt.startswith("MONOLITH") or txt.startswith("FIT CELLS")
    for x, y, ang in cands:
        done = False
        for d in (0, 1.0, -1.0, 2.0, -2.0, 3.0, -3.0):
            xx, yy = (x + d, y) if ang == 0 else (x, y + d)
            bx = free_spot(txt, xx, yy, None, ang, h, holders_ok)
            if bx:
                EXTRA.append((txt, xx, yy, ang, h))
                obst.append(bx)
                done = True
                break
        if done:
            break
    else:
        print("title without room:", txt)

for txt, x, y, ang, h in EXTRA:
    t = pcbnew.PCB_TEXT(b)
    t.SetText(txt)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h)))
    t.SetTextThickness(mm(0.2 if h >= 1.2 else 0.15))
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetTextAngleDegrees(ang)
    b.Add(t)
b.Save(PCB)
open(PRO, "wb").write(pro)
print("silk texts written:", len(EXTRA))
