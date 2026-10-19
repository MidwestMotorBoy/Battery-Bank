"""One-shot (2026-10-17): add the gate turn-off diodes D406-D409 / D506-D509 (BAT54WS, SOD-323) to the board, each
beside its gate resistor (R444-R447 / R544-R547), same axis, cathode pad (1) next to the resistor's driver-side pad (1).
Picks the side of the resistor whose spot has no courtyard collision; otherwise reports it for hand placement.
Nets, values and symbol links come afterwards from netlist_to_board.py. Restores MonolithDev.kicad_pro after saving.

Run from DevBoard/ with KiCad's python: python tools/add_gate_diodes_board.py
"""
import math
import os

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
BOARD = os.path.join(ROOT, "MonolithDev.kicad_pcb")
PRO = os.path.join(ROOT, "MonolithDev.kicad_pro")
LIB = r"C:/Program Files/KiCad/10.0/share/kicad/footprints/Diode_SMD.pretty"
PAIRS = {"R444": "D406", "R445": "D407", "R446": "D408", "R447": "D409",
         "R544": "D506", "R545": "D507", "R546": "D508", "R547": "D509"}
GAP = 1.45            # mm, resistor centre to diode centre, across the resistor axis

pro = open(PRO, "rb").read()
b = pcbnew.LoadBoard(BOARD)


def courtyard(fp):
    s = fp.GetCourtyard(pcbnew.F_CrtYd if not fp.IsFlipped() else pcbnew.B_CrtYd)
    return s


report = []
for rref, dref in PAIRS.items():
    if b.FindFootprintByReference(dref):
        report.append(f"{dref}: already on the board, left alone")
        continue
    r = b.FindFootprintByReference(rref)
    d = pcbnew.FootprintLoad(LIB, "D_SOD-323")
    d.SetReference(dref)
    d.SetValue("BAT54WS")
    if r.IsFlipped():
        d.Flip(d.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    d.SetOrientation(r.GetOrientation())
    ang = math.radians(r.GetOrientationDegrees())
    # unit vector across the resistor axis (KiCad y is down, positive angles turn counter-clockwise on screen)
    nx, ny = -math.sin(ang), -math.cos(ang)
    placed = None
    for side in (1, -1, 2, -2):
        off = side * GAP
        pos = r.GetPosition() + pcbnew.VECTOR2I(pcbnew.FromMM(nx * off), pcbnew.FromMM(ny * off))
        d.SetPosition(pos)
        b.Add(d)
        cy = d.GetCourtyard(pcbnew.F_CrtYd if not d.IsFlipped() else pcbnew.B_CrtYd)
        hit = []
        for other in b.GetFootprints():
            if other is d or other.GetReference() == dref:
                continue
            if other.IsFlipped() != d.IsFlipped():
                continue
            oc = other.GetCourtyard(pcbnew.F_CrtYd if not other.IsFlipped() else pcbnew.B_CrtYd)
            if oc.OutlineCount() and cy.OutlineCount() and oc.Collide(cy):
                hit.append(other.GetReference())
        if not hit:
            placed = (side, pos)
            break
        b.Remove(d)
    if placed is None:
        d.SetPosition(r.GetPosition() + pcbnew.VECTOR2I(pcbnew.FromMM(nx * GAP), pcbnew.FromMM(ny * GAP)))
        b.Add(d)
        report.append(f"{dref}: no free spot beside {rref}; placed overlapping, move it by hand")
    else:
        p = placed[1]
        report.append(f"{dref}: beside {rref} at ({pcbnew.ToMM(p.x):.2f}, {pcbnew.ToMM(p.y):.2f}), side {placed[0]:+d}")

b.Save(BOARD)
open(PRO, "wb").write(pro)
print("\n".join(report))
