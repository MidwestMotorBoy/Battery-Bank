"""Board setup for the Monolith dev board.

Writes into MonolithDev.kicad_pcb (only while the board is still empty apart from the mounting holes):
4-layer 0.8 mm stack-up (2 oz outer / 1 oz inner, ENIG), the 175 x 115 mm outline with gaps for the two
mid-mount USB-C notches (the notches themselves come from the connector footprint's Edge.Cuts), and six M3
board-only mounting holes. Always (re)writes the JLC design rules and net classes in MonolithDev.kicad_pro
and the custom rules in MonolithDev.kicad_dru.

Board coordinates in the plan are mm from the board's top-left corner; KiCad coordinates add ORIGIN.

    python tools/setup_board.py
"""
import json
import os
import re
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "MonolithDev.kicad_pcb")
PRO = os.path.join(HERE, "..", "MonolithDev.kicad_pro")
DRU = os.path.join(HERE, "..", "MonolithDev.kicad_dru")
MH = r"C:/Program Files/KiCad/10.0/share/kicad/footprints/MountingHole.pretty/MountingHole_3.2mm_M3.kicad_mod"

ORIGIN = (50.0, 50.0)
W, H = 175.0, 115.0
USB_Y = (35.0, 78.0)              # notch centres on the right edge (J401, J501)
NOTCH_W = 10.2                     # Shou Han TYPE-C 16PCB0.8 recommended layout
HOLES = [(4, 4), (101, 4), (171, 4), (4, 111), (101, 111), (171, 111)]


def k(x, y):
    return ORIGIN[0] + x, ORIGIN[1] + y


def u():
    return str(uuid.uuid4())


def gr_line(a, b):
    (x0, y0), (x1, y1) = k(*a), k(*b)
    return (f'\t(gr_line\n\t\t(start {x0:g} {y0:g})\n\t\t(end {x1:g} {y1:g})\n\t\t(stroke\n\t\t\t(width 0.1)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{u()}")\n\t)\n')


def outline():
    segs = [((0, 0), (W, 0)), ((0, H), (W, H)), ((0, 0), (0, H))]
    y = 0.0
    for yc in USB_Y:                                   # right edge, broken at each notch
        segs.append(((W, y), (W, yc - NOTCH_W / 2)))
        y = yc + NOTCH_W / 2
    segs.append(((W, y), (W, H)))
    return "".join(gr_line(a, b) for a, b in segs)


def holes():
    src = open(MH, encoding="utf-8").read()
    body = src[src.find("\t(property"):src.rfind("\t(embedded_fonts")]
    out = ""
    for i, (x, y) in enumerate(HOLES, 1):
        kx, ky = k(x, y)
        b = body.replace('"Reference" "REF**"', f'"Reference" "H{i}"')
        b = b.replace("(attr exclude_from_pos_files exclude_from_bom)", "(attr board_only exclude_from_pos_files exclude_from_bom)")
        b = re.sub(r"\(property \"(Reference|Value|KiLib_Generator)\" (\"[^\"]*\")\n\t\t\(at ([-\d.]+) ([-\d.]+) 0\)",
                   lambda m: f'(property "{m.group(1)}" {m.group(2)}\n\t\t(at {kx + float(m.group(3)):g} {ky + float(m.group(4)):g} 0)', b)
        b = "\n".join("\t" + l if l else l for l in b.split("\n"))
        out += (f'\t(footprint "MountingHole:MountingHole_3.2mm_M3"\n\t\t(layer "F.Cu")\n\t\t(uuid "{u()}")\n'
                f'\t\t(at {kx:g} {ky:g})\n{b}\t)\n')
    return out


STACKUP = """		(stackup
			(layer "F.SilkS" (type "Top Silk Screen"))
			(layer "F.Paste" (type "Top Solder Paste"))
			(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
			(layer "F.Cu" (type "copper") (thickness 0.07))
			(layer "dielectric 1" (type "prepreg") (thickness 0.1) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
			(layer "In1.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 2" (type "core") (thickness 0.37) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
			(layer "In2.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 3" (type "prepreg") (thickness 0.1) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
			(layer "B.Cu" (type "copper") (thickness 0.07))
			(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
			(layer "B.Paste" (type "Bottom Solder Paste"))
			(layer "B.SilkS" (type "Bottom Silk Screen"))
			(copper_finish "ENIG")
			(dielectric_constraints no)
		)
"""


def write_board():
    s = open(PCB, encoding="utf-8").read()
    fps = re.findall(r'\(footprint "([^"]+)"', s)
    if any(f != "MountingHole:MountingHole_3.2mm_M3" for f in fps) or "(segment" in s:
        print("board already populated: outline, stack-up and holes left alone")
        return
    s = re.sub(r"\n\t\(footprint .*?\n\t\)(?=\n)", "", s, flags=re.S)
    s = re.sub(r"\n\t\(gr_line.*?\n\t\)(?=\n)", "", s, flags=re.S)
    s = re.sub(r"\(thickness [\d.]+\)\n\t\t\(legacy_teardrops", "(thickness 0.8)\n\t\t(legacy_teardrops", s, count=1)
    if '"In1.Cu"' not in s:
        s = s.replace('\t\t(2 "B.Cu" signal)\n',
                      '\t\t(4 "In1.Cu" signal "In1.Cu (GND)")\n\t\t(6 "In2.Cu" signal "In2.Cu (power)")\n\t\t(2 "B.Cu" signal)\n', 1)
    s = re.sub(r"\t\t\(stackup\n.*?\n\t\t\)\n", "", s, flags=re.S)
    s = s.replace("\t(setup\n", "\t(setup\n" + STACKUP, 1)
    k_end = s.rfind("\t(embedded_fonts")
    s = s[:k_end] + holes() + outline() + s[k_end:]
    open(PCB, "w", encoding="utf-8", newline="\n").write(s)
    print("board: outline, stack-up, 6 holes")


def cls(name, track, clear, via_d, via_dr, prio):
    return {"name": name, "track_width": track, "clearance": clear, "via_diameter": via_d, "via_drill": via_dr,
            "priority": prio, "bus_width": 12, "wire_width": 6, "line_style": 0, "diff_pair_gap": 0.25,
            "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "tuning_profile": ""}


def write_rules():
    p = json.load(open(PRO, encoding="utf-8"))
    ds = p.setdefault("board", {}).setdefault("design_settings", {})
    ds["rules"] = {
        # JLC 4-layer, 2 oz outer: 0.15/0.15 mm track/gap. Vias: 0.2-0.25 mm drills are standard price only
        # with a >= 0.45 mm pad. Copper >= 0.2 mm from routed edges (JLC floor; 0.25 by custom rule except at the USB-C notches). Legend text >= 0.8 mm.
        "min_clearance": 0.15, "min_track_width": 0.15, "min_connection": 0.15,
        "min_via_diameter": 0.45, "min_via_annular_width": 0.1, "min_through_hole_diameter": 0.2,
        "min_hole_to_hole": 0.25, "min_hole_clearance": 0.2, "min_copper_edge_clearance": 0.2,
        "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1, "allow_microvias": False, "allow_blind_buried_vias": False,
        "min_silk_clearance": 0.0, "min_text_height": 0.8, "min_text_thickness": 0.15,
        "solder_mask_to_copper_clearance": 0.0, "min_groove_width": 0.0, "min_resolved_spokes": 2,
        "max_error": 0.005, "use_height_for_length_calcs": True,
    }
    ds["track_widths"] = [0.0, 0.2, 0.3, 0.5, 0.8, 1.0, 1.5, 2.5, 4.0]
    ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.45, "drill": 0.25},
                            {"diameter": 0.6, "drill": 0.3}, {"diameter": 0.8, "drill": 0.4}]
    ns = p.setdefault("net_settings", {})
    ns["classes"] = [
        cls("Default", 0.2, 0.15, 0.6, 0.3, 2147483647),
        cls("HighCurrent", 2.5, 0.25, 0.8, 0.4, 0),     # pack/cell path, chargers' power stage (up to ~10 A)
        cls("Power", 0.8, 0.2, 0.6, 0.3, 1),             # 5 V / 3.3 V rails, regulator I/O
        cls("GND", 0.5, 0.15, 0.6, 0.3, 2),
        cls("GateDrive", 0.4, 0.15, 0.6, 0.3, 3),
    ]
    ns["netclass_patterns"] = (
        [{"netclass": "HighCurrent", "pattern": pt} for pt in
         ["PACK_P", "CELL_N", "/Cells and Gauge/CELL*", "/Cells and Gauge/FET_MID", "*/VBAT_SYS", "*/PPHV", "*/VBUS",
          "*/SW1", "*/SW2", "*/AC_SNS_N", "*/BAT_SNS_P"]] +
        [{"netclass": "Power", "pattern": pt} for pt in
         ["3V3", "*/3V3_MCU", "*/3V3_BUCK", "*/SW_3V3", "*/PACK_LP", "*/LDO_IN", "*/PP5V", "*/5V_IN", "*/SW_5V",
          "*/REGN", "*/LDO_3V3", "/P1_LDO_3V3", "*/3V3_PD", "*/5V_AMP"]] +
        [{"netclass": "GND", "pattern": "GND"}] +
        [{"netclass": "GateDrive", "pattern": pt} for pt in ["*/HG1", "*/HG2", "*/LG1", "*/LG2", "/Cells and Gauge/*_G"]])
    json.dump(p, open(PRO, "w", encoding="utf-8", newline="\n"), indent=2)
    print("project: rules, presets, 5 net classes")

    open(DRU, "w", encoding="utf-8", newline="\n").write("""(version 1)

# JLC multilayer: component-hole annular ring >= 0.254 mm on 2 oz outer copper. Holes under 0.5 mm are vias
# (including the thermal vias inside exposed pads) and follow the via rules. The Shou Han USB-C shell slots
# (0.5 x 1.0 drill in 0.9 x 1.4 pads) follow the maker's layout instead.
(rule "PTH annular ring (2 oz)"
	(constraint annular_width (min 0.25))
	(condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole' && A.Hole_Size_X >= 0.5mm && A.Parent.Reference != 'J401' && A.Parent.Reference != 'J501'"))

# 0.25 mm copper-to-edge margin everywhere except the USB-C signal pads, which sit 0.2 mm (JLC's minimum)
# behind their notch.
(rule "Edge margin"
	(constraint edge_clearance (min 0.25))
	(condition "A.Parent.Reference != 'J401' && A.Parent.Reference != 'J501'"))

# JLC: non-plated holes >= 0.5 mm.
(rule "NPTH minimum"
	(constraint hole_size (min 0.5))
	(condition "A.Type == 'Pad' && A.Pad_Type == 'NPTH, mechanical'"))

# Keep switch nodes and the pack bus a little further from small signals.
(rule "HighCurrent to small signals"
	(constraint clearance (min 0.25))
	(condition "A.NetClass == 'HighCurrent' && B.NetClass == 'Default'"))
""")
    print("rules file written")


write_board()
write_rules()
