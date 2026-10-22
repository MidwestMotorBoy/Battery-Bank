"""Create the production board file with its stack-up and outline (2026-10-17; side outline and 1.6 mm 2026-10-18).
Run once; later runs patch an existing board that has no copper yet.

Stack-up: 6 layers, 1.6 mm (chosen 2026-10-18 for cost; was 0.8 mm), 2 oz outer / 0.5 oz inner, ENIG, vias filled
and capped (JLC default on 6+ layers). The dielectric split is a symmetric approximation that sums to 1.6 mm; no net
here is impedance-controlled, so set it to JLC's stack at order time. JLC multilayer vias at 1.6 mm: 0.15 mm hole /
0.25 mm via minimum (surcharge below 0.2 mm or under a 0.45 mm via); the 0.1 mm hole option needs a board <= 1 mm.

Outline: the side board of the one-piece tray, from mechanical/monolith_shell.py (sb_* values, also written to
mechanical/monolith_side_pcb.dxf): 43.2 mm wide, its bottom corners notched around the tray's screw pillars, centred on
(100, 100). KiCad x = the tray's y (left = the C1 / PACK- side), KiCad y = down the pack (top edge = the port end).
F.Cu faces the aluminium cover (outer face), B.Cu faces the cells. The outline leaves gaps for the connector notches
(PORTS_X), and place_ports() puts J401/J501 there.
(History: 40.5 mm then 45.5 mm top-cap boards, 2026-10-17. mechanical/monolith_bottom_pcb.dxf is the old bottom end
board with the vent, not this board.)

Run: "C:/Program Files/KiCad/10.0/bin/python.exe" -I Production/tools/make_board.py [--force] [--keep-copper]
     ... make_board.py --standoffs   (only places the cover standoffs H101-H104, after Update PCB from Schematic)
     ... make_board.py --keepouts    (redraws the KO_* mechanical keep-out rule areas from mechanical/monolith_shell.py)
"""
import math
import os
import shutil
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.normpath(os.path.join(HERE, ".."))
DEV = os.path.normpath(os.path.join(PROD, "..", "DevBoard"))
OUT = os.path.join(PROD, "Monolith.kicad_pcb")
sys.path.insert(0, os.path.normpath(os.path.join(PROD, "..", "mechanical")))
import monolith_shell as M  # noqa: E402  (side-board geometry: one source for the tray and the board)

CX, CY = 100.0, 100.0
HALF_W = M.sb_board_w / 2                     # 21.6
Z_MID = (M.sb_zb0 + M.sb_zb1) / 2             # tray z of the board centre
def Y(z):                                     # tray z -> KiCad y (port end at the top)
    return CY - (z - Z_MID)
Y_TOP, Y_BOT, Y_NOTCH = Y(M.sb_zb1), Y(M.sb_zb0), Y(M.sb_notch_z)
NOTCH_X = M.sb_notch_y                        # bottom corners cut away for |x - CX| > NOTCH_X, below Y_NOTCH
# USB-C notches on the top edge: connector centres along x, 13 mm apart. The footprint's own Edge.Cuts draws the
# 10.2 x 5.65 notch (origin = board edge), so the board outline leaves a 10.2 mm gap at each.
PORTS_X = {"J501": CX - M.SB_PORT_Y, "J401": CX + M.SB_PORT_Y}
NOTCH_HALF = 5.1

COPPER = [("F.Cu", 0.07), ("In1.Cu", 0.0175), ("In2.Cu", 0.0175), ("In3.Cu", 0.0175), ("In4.Cu", 0.0175), ("B.Cu", 0.07)]
DIELECTRIC = [("prepreg", 0.20, 4.4), ("core", 0.30, 4.6), ("prepreg", 0.39, 4.4), ("core", 0.30, 4.6), ("prepreg", 0.20, 4.4)]
THICK = round(sum(t for _, t in COPPER) + sum(t for _, t, _ in DIELECTRIC), 4)
assert abs(THICK - M.SB_PCB_T) < 1e-6, "stack-up %g mm != mechanical SB_PCB_T %g mm" % (THICK, M.SB_PCB_T)


LAYERS = """\t(layers
\t\t(0 "F.Cu" signal)
\t\t(4 "In1.Cu" power "In1.Cu (GND)")
\t\t(6 "In2.Cu" signal "In2.Cu (signal V + 3V3)")
\t\t(8 "In3.Cu" signal "In3.Cu (signal H + 5V)")
\t\t(10 "In4.Cu" power "In4.Cu (GND)")
\t\t(2 "B.Cu" signal)
\t\t(9 "F.Adhes" user "F.Adhesive")
\t\t(11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(17 "Dwgs.User" user "User.Drawings")
\t\t(19 "Cmts.User" user "User.Comments")
\t\t(21 "Eco1.User" user "User.Eco1")
\t\t(23 "Eco2.User" user "User.Eco2")
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t)"""


def u():
    return str(uuid.uuid4())


def stackup():
    s = ['\t\t(stackup',
         '\t\t\t(layer "F.SilkS"\n\t\t\t\t(type "Top Silk Screen")\n\t\t\t)',
         '\t\t\t(layer "F.Paste"\n\t\t\t\t(type "Top Solder Paste")\n\t\t\t)',
         '\t\t\t(layer "F.Mask"\n\t\t\t\t(type "Top Solder Mask")\n\t\t\t\t(thickness 0.01)\n\t\t\t)']
    for i, (name, t) in enumerate(COPPER):
        s.append('\t\t\t(layer "%s"\n\t\t\t\t(type "copper")\n\t\t\t\t(thickness %g)\n\t\t\t)' % (name, t))
        if i < len(DIELECTRIC):
            kind, dt, er = DIELECTRIC[i]
            s.append('\t\t\t(layer "dielectric %d"\n\t\t\t\t(type "%s")\n\t\t\t\t(thickness %g)\n\t\t\t\t(material "FR4")\n'
                     '\t\t\t\t(epsilon_r %g)\n\t\t\t\t(loss_tangent 0.02)\n\t\t\t)' % (i + 1, kind, dt, er))
    s += ['\t\t\t(layer "B.Mask"\n\t\t\t\t(type "Bottom Solder Mask")\n\t\t\t\t(thickness 0.01)\n\t\t\t)',
          '\t\t\t(layer "B.Paste"\n\t\t\t\t(type "Bottom Solder Paste")\n\t\t\t)',
          '\t\t\t(layer "B.SilkS"\n\t\t\t\t(type "Bottom Silk Screen")\n\t\t\t)',
          '\t\t\t(copper_finish "ENIG")\n\t\t\t(dielectric_constraints no)', '\t\t)']
    return "\n".join(s)


def line(x0, y0, x1, y1):
    return ('\t(gr_line\n\t\t(start %g %g)\n\t\t(end %g %g)\n\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n'
            '\t\t)\n\t\t(layer "Edge.Cuts")\n\t\t(uuid "%s")\n\t)' % (x0, y0, x1, y1, u()))


def outline():
    """Top edge with the two connector gaps, straight sides, bottom corners notched around the screw pillars."""
    xl, xr = CX - HALF_W, CX + HALF_W
    xs = [xl] + [x for c in sorted(PORTS_X.values()) for x in (c - NOTCH_HALF, c + NOTCH_HALF)] + [xr]
    g = [line(x0, Y_TOP, x1, Y_TOP) for x0, x1 in zip(xs[0::2], xs[1::2])]
    pts = [(xr, Y_TOP), (xr, Y_NOTCH), (CX + NOTCH_X, Y_NOTCH), (CX + NOTCH_X, Y_BOT),
           (CX - NOTCH_X, Y_BOT), (CX - NOTCH_X, Y_NOTCH), (xl, Y_NOTCH), (xl, Y_TOP)]
    g += [line(*p, *q) for p, q in zip(pts[:-1], pts[1:])]
    return "\n".join(g)


def block_end(s, i):
    d = 0
    while True:
        c = s[i]
        if c == '"':
            i += 1
            while s[i] != '"':
                i += 2 if s[i] == "\\" else 1
        elif c == "(":
            d += 1
        elif c == ")":
            d -= 1
            if d == 0:
                return i + 1
        i += 1


def patch(path, layers):
    """Put the stack-up, 6-layer table, thickness and outline into an existing board, leaving footprints alone."""
    s = open(path, encoding="utf-8").read()
    copper = __import__("re").findall(r"\n\t\((segment|via|arc|zone)\b", s)
    assert not copper or "--keep-copper" in sys.argv, \
        "board has %d copper items; patch it in KiCad, or pass --keep-copper to leave them where they are" % len(copper)
    if copper:
        print("kept %d copper items as they are (not moved with the outline or the ports)" % len(copper))
    s = __import__("re").sub(r"\(general\n\t\t\(thickness [\d.]+\)", "(general\n\t\t(thickness %g)" % THICK, s, count=1)
    a = s.index("\n\t(layers") + 1
    s = s[:a] + layers.lstrip("\n") + s[block_end(s, a + 1):]
    a = s.index("\n\t(setup") + 1
    st = s.find("\n\t\t(stackup", a, block_end(s, a + 1))
    if st >= 0:
        s = s[:st + 1] + stackup().lstrip("\n") + s[block_end(s, st + 3):]
    else:
        s = s[:a] + "\t(setup\n" + stackup() + s[a + len("\t(setup"):]
    # redraw the outline: drop top-level Edge.Cuts lines/arcs (footprint notches stay with their footprints)
    re = __import__("re")
    spans = []
    for m in re.finditer(r"\n\t\((gr_line|gr_arc)\b", s):
        a = m.start() + 2
        b = block_end(s, a)
        if '(layer "Edge.Cuts")' in s[a:b]:
            spans.append((m.start(), b))
    for a, b in reversed(spans):
        s = s[:a] + s[b:]
    s = s.rstrip()[:-1].rstrip() + "\n" + outline() + "\n)\n"
    open(path, "w", encoding="utf-8", newline="\n").write(s)
    print("patched %s: %g mm, 6 layers, stack-up and side outline %.1f x %.2f mm; footprints untouched"
          % (path, THICK, 2 * HALF_W, Y_BOT - Y_TOP))


def place_ports(path):
    """Put J401/J501 on the top edge: footprint origin on the edge, notch pointing into the board (180 deg), locked."""
    import pcbnew
    b = pcbnew.LoadBoard(path)
    for ref, x in PORTS_X.items():
        f = b.FindFootprintByReference(ref)
        if f is None:
            print("no %s on the board (run Update PCB from Schematic)" % ref)
            continue
        if f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(180)
        f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(Y_TOP)))
        f.SetLocked(True)
        print("%s at (%.2f, %.2f) 180 deg, locked" % (ref, x, Y_TOP))
    pcbnew.SaveBoard(path, b)


STANDOFFS = {"H101": 0, "H102": 1, "H103": 2, "H104": 3}  # ref -> index into M.SB_STANDOFFS


def place_standoffs(path):
    """Put the cover standoffs H101-H104 (Wuerth WA-SMSI M2 x 3.5 mm) where mechanical/monolith_shell.py
    SB_STANDOFFS has them: F.Cu, locked. Only moves those four footprints; run after Update PCB from Schematic,
    with the board closed in KiCad (or reload it afterwards)."""
    import pcbnew
    lock = os.path.join(os.path.dirname(path), "~" + os.path.basename(path) + ".lck")
    if os.path.exists(lock):
        sys.exit("%s is open in KiCad (lock file %s): save and close the PCB editor first" % (path, lock))
    b = pcbnew.LoadBoard(path)
    missing = [r for r in STANDOFFS if b.FindFootprintByReference(r) is None]
    if missing:
        sys.exit("not on the board: %s. In the PCB editor run Tools > Update PCB from Schematic (F8), drop the new "
                 "footprints anywhere, save, close the PCB editor, then run this again. Board not written." % ", ".join(missing))
    for ref, k in STANDOFFS.items():
        f = b.FindFootprintByReference(ref)
        if f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        y, z = M.SB_STANDOFFS[k]
        x, yk = CX + y, Y(z)
        f.SetOrientationDegrees(0)
        f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(yk)))
        f.SetLocked(True)
        print("%s at (%.2f, %.2f), F.Cu, locked" % (ref, x, yk))
    pcbnew.SaveBoard(path, b)


def keepout_list():
    """Mechanical keep-outs as (name, layers, polygon, rules), all from mechanical/monolith_shell.py.
    rules: subset of footprints / tracks / vias / pour (each one is 'not allowed' inside)."""
    k = M.kicad

    def rect(x0, y0, x1, y1):
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    out = []
    # F.Cu: no tall parts and no gap pad under the cover's ePTFE vent
    cx, cy = k(0, M.SB_VENT_Z)
    r = M.SB_VENT_D / 2 + 2
    out.append(("KO_F_cover_vent", ["F.Cu"], [(cx + r * math.cos(a * math.pi / 16), cy + r * math.sin(a * math.pi / 16))
                                              for a in range(32)], {"footprints"}))
    # F.Cu: nothing above the module's antenna end (the module footprint already clears copper on every layer)
    s = M.SB_ANT_SIDE
    xa = sorted((CX + s * (HALF_W - 3.2 - 1.0), CX + s * HALF_W))
    ya = (k(0, M.sb_ant_zc + M.SB_ANT_MOD[0] / 2)[1] - 1.0, k(0, M.sb_ant_zc - M.SB_ANT_MOD[0] / 2)[1] + 1.0)
    out.append(("KO_F_above_antenna", ["F.Cu"], rect(xa[0], ya[0], xa[1], ya[1]), {"footprints"}))
    # both faces: the top edge bears on the top wall's inside face beyond |x| = SB_STOP_Y0
    for side, (x0, x1) in (("L", (CX - HALF_W, CX - M.SB_STOP_Y0)), ("R", (CX + M.SB_STOP_Y0, CX + HALF_W))):
        out.append(("KO_top_stop_" + side, ["F.Cu", "B.Cu"], rect(x0, Y_TOP, x1, Y_TOP + 1.0), {"footprints"}))
    # B.Cu: EVA lanes pressed onto the board along the cell tangents
    for i, (y0, y1, z0, z1) in enumerate(M.sb_lanes()):
        out.append(("KO_B_EVA_lane_%d" % (i + 1), ["B.Cu"], rect(CX + y0, Y(z1), CX + y1, Y(z0)), {"footprints"}))
    # B.Cu: the PACK nickel strips run behind the board and wrap the bottom edge onto the F.Cu pads
    for name, yc in M.sb_tab_y.items():
        w = M.SB_TAB_W / 2 + 0.5
        out.append(("KO_B_%s_strip" % name.replace("+", "P").replace("-", "N"), ["B.Cu"],
                    rect(CX + yc - w, Y(M.sb_zb0 + M.SB_TAB_PAD_H), CX + yc + w, Y_BOT), {"footprints", "tracks"}))
    # B.Cu: cell sense wires behind the board, from the tap holes to the top EVA slots / the floor channel
    (x1, y1), (x3, y3), (x2, y2) = (k(*M.SB_TAP_HOLES[n]) for n in ("CELL1", "CELL3", "CELL2"))
    out.append(("KO_B_tap_wires_top", ["B.Cu"], rect(min(x1, x3) - 1.5, Y_TOP, max(x1, x3) + 1.5, y1 + 1.5), {"footprints"}))
    out.append(("KO_B_tap_wire_CELL2", ["B.Cu"], rect(x2 - 1.5, y2 - 1.5, x2 + 1.5, Y_BOT), {"footprints"}))
    return out


def add_keepouts(path):
    """Draw keepout_list() as named rule areas (replacing earlier KO_* areas) plus a B.Cu height note on
    Cmts.User, so DRC flags parts that land on them. Board must be closed in KiCad."""
    import pcbnew
    lock = os.path.join(os.path.dirname(path), "~" + os.path.basename(path) + ".lck")
    if os.path.exists(lock):
        sys.exit("%s is open in KiCad (lock file %s): save and close the PCB editor first" % (path, lock))
    b = pcbnew.LoadBoard(path)
    for z in [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith("KO_")]:
        b.Remove(z)
    for d in [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Cmts_User and "KO_NOTE" in str(getattr(d, "GetText", lambda: "")())]:
        b.Remove(d)
    for name, layers, poly, rules in keepout_list():
        z = pcbnew.ZONE(b)
        z.SetIsRuleArea(True)
        z.SetZoneName(name)
        ls = pcbnew.LSET()
        for l in layers:
            ls.AddLayer(b.GetLayerID(l))
        z.SetLayerSet(ls)
        z.SetDoNotAllowFootprints("footprints" in rules)
        z.SetDoNotAllowTracks("tracks" in rules)
        z.SetDoNotAllowVias("vias" in rules)
        z.SetDoNotAllowZoneFills("pour" in rules)
        z.SetDoNotAllowPads(False)
        o = z.Outline()
        o.NewOutline()
        for x, y in poly:
            o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        b.Add(z)
        print("%-22s %-14s %s" % (name, "+".join(layers), ", ".join(sorted(rules)) + " not allowed"))
    t = pcbnew.PCB_TEXT(b)
    t.SetLayer(pcbnew.Cmts_User)
    t.SetText("KO_NOTE B.Cu (faces the cells, hand-soldered): parts <= 2.3 mm tall; up to ~5 mm only in the centre "
              "strip x 96-104 or beyond 18 mm from centre. No heat sources on B.Cu. F.Cu: parts <= 3.2 mm (cover gap pad).")
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
    t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(CX), pcbnew.FromMM(Y_BOT + 4)))
    b.Add(t)
    pcbnew.SaveBoard(path, b)


def main():
    if "--standoffs" in sys.argv:
        place_standoffs(OUT)
        return
    if "--keepouts" in sys.argv:
        add_keepouts(OUT)
        return
    if os.path.exists(OUT) and "--force" not in sys.argv:
        patch(OUT, LAYERS)
        place_ports(OUT)
        if not os.path.exists(os.path.join(PROD, "Monolith.kicad_dru")):
            shutil.copy2(os.path.join(DEV, "MonolithDev.kicad_dru"), os.path.join(PROD, "Monolith.kicad_dru"))
        return
    dev = open(os.path.join(DEV, "MonolithDev.kicad_pcb"), encoding="utf-8").read()
    a = dev.index("\t(pad_to_mask_clearance")  # the setup block after the stack-up, up to its end
    b = dev.index("\n\t(footprint")
    rest_of_setup = dev[a:b].rstrip()
    rest_of_setup = rest_of_setup[:rest_of_setup.rfind(")")].rstrip()  # drop the closing ')' of (setup
    layers = LAYERS
    text = "\n".join([
        "(kicad_pcb", "\t(version 20260206)", '\t(generator "pcbnew")', '\t(generator_version "10.0")',
        "\t(general\n\t\t(thickness %g)\n\t\t(legacy_teardrops no)\n\t)" % THICK, '\t(paper "A4")',
        '\t(title_block\n\t\t(title "Monolith production board")\n\t\t(date "2026-10-17")\n\t\t(rev "P0")\n'
        '\t\t(company "Monolith 100 W battery bank")\n\t)',
        layers, "\t(setup", stackup(), rest_of_setup, "\t)", '\t(net 0 "")', outline(), ")", ""])
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    shutil.copy2(os.path.join(DEV, "MonolithDev.kicad_dru"), os.path.join(PROD, "Monolith.kicad_dru"))
    print("wrote %s: %g mm, 6 layers; side outline %.1f x %.2f mm" % (OUT, THICK, 2 * HALF_W, Y_BOT - Y_TOP))


if __name__ == "__main__":
    main()
