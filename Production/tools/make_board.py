"""Create the production board file with its stack-up and outline (2026-10-17). Run once; refuses to overwrite.

Stack-up: 6 layers, 0.8 mm, 2 oz outer / 0.5 oz inner, ENIG, vias filled and capped (JLC default on 6+ layers).
The dielectric split is a symmetric approximation that sums to 0.8 mm; JLC publishes no 0.8 mm 6-layer stack and no
net here is impedance-controlled, so set it to JLC's stack at order time.

Outline: 45.5 x 45.5 mm rounded square, R9.35 corners, centred on (100, 100) (2026-10-17: the 40.5 mm top-cap board from
mechanical/monolith_parts.py plus 5 mm in x and y, so both USB-C ports fit on the right edge). The outline leaves gaps
for the connector notches (PORTS_Y), and place_ports() puts J401/J501 there.
(mechanical/monolith_bottom_pcb.dxf is the 43.3 mm bottom end board with the vent, not this board.)

Run: "C:/Program Files/KiCad/10.0/bin/python.exe" -I Production/tools/make_board.py [--force]
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
CX, CY, HALF, R = 100.0, 100.0, 22.75, 9.35  # 45.5 mm (2026-10-17: +5 mm in x and y for both ports on one side)
# USB-C notches on the right edge (x = CX + HALF): connector centres along y. The footprint's own Edge.Cuts draws the
# 10.2 x 5.65 notch (origin = board edge), so the board outline leaves a 10.2 mm gap at each. 13 mm apart: each
# connector needs ~12.5 mm (notch + shell tabs at +-5.8), all inside the 26.8 mm straight edge (R9.35 corners).
PORTS_Y = {"J501": CY - 6.5, "J401": CY + 6.5}
NOTCH_HALF = 5.1

COPPER = [("F.Cu", 0.07), ("In1.Cu", 0.0175), ("In2.Cu", 0.0175), ("In3.Cu", 0.0175), ("In4.Cu", 0.0175), ("B.Cu", 0.07)]
DIELECTRIC = [("prepreg", 0.10, 4.4), ("core", 0.12, 4.6), ("prepreg", 0.15, 4.4), ("core", 0.12, 4.6), ("prepreg", 0.10, 4.4)]
THICK = round(sum(t for _, t in COPPER) + sum(t for _, t, _ in DIELECTRIC), 4)


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


def arc(cx, cy, a0):
    pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))) for a in (a0, a0 + 45, a0 + 90)]
    return ('\t(gr_arc\n\t\t(start %.4f %.4f)\n\t\t(mid %.4f %.4f)\n\t\t(end %.4f %.4f)\n\t\t(stroke\n\t\t\t(width 0.05)\n'
            '\t\t\t(type default)\n\t\t)\n\t\t(layer "Edge.Cuts")\n\t\t(uuid "%s")\n\t)'
            % (pts[0][0], pts[0][1], pts[1][0], pts[1][1], pts[2][0], pts[2][1], u()))


def outline():
    k = HALF - R
    g = [line(CX - k, CY - HALF, CX + k, CY - HALF), line(CX + k, CY + HALF, CX - k, CY + HALF),
         line(CX - HALF, CY + k, CX - HALF, CY - k)]
    ys = [CY - k] + [y for c in sorted(PORTS_Y.values()) for y in (c - NOTCH_HALF, c + NOTCH_HALF)] + [CY + k]
    for y0, y1 in zip(ys[0::2], ys[1::2]):  # right edge, with gaps where the connector notches are
        g.append(line(CX + HALF, y0, CX + HALF, y1))
    for (sx, sy), a0 in (((1, 1), 0), ((-1, 1), 90), ((-1, -1), 180), ((1, -1), 270)):
        g.append(arc(CX + sx * k, CY + sy * k, a0))
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
    assert not __import__("re").search(r"\n\t\((segment|via|arc|zone)\b", s), "board has copper; patch it in KiCad instead"
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
    print("patched %s: %g mm, 6 layers, stack-up and outline; footprints untouched" % (path, THICK))


def place_ports(path):
    """Put J401/J501 on the right edge: footprint origin on the edge, notch pointing into the board (90 deg), locked."""
    import pcbnew
    b = pcbnew.LoadBoard(path)
    for ref, y in PORTS_Y.items():
        f = b.FindFootprintByReference(ref)
        if f is None:
            print("no %s on the board (run Update PCB from Schematic)" % ref)
            continue
        if f.IsFlipped():
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(90)
        f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(CX + HALF), pcbnew.FromMM(y)))
        f.SetLocked(True)
        print("%s at (%.2f, %.2f) 90 deg, locked" % (ref, CX + HALF, y))
    pcbnew.SaveBoard(path, b)


def main():
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
    print("wrote %s: %g mm, 6 layers; outline %.1f mm square R%.2f" % (OUT, THICK, 2 * HALF, R))


if __name__ == "__main__":
    main()
