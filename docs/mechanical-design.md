# Mechanical design

_Moved from the root README on 2026-10-18; rewritten 2026-10-21 for **the cup**, the current enclosure; cleaned up 2026-10-24 for the BAK N21700CX-65E cells, with the retired side tray and top-cap tube moved to [`archive/side-tray-mechanical.md`](archive/side-tray-mechanical.md). The models and renders live in `hardware/mechanical/`. Decisions and open items are in [`spec.md`](spec.md) (Boards and enclosure)._

## Renders

<table>
<tr>
<td width="50%"><a href="../hardware/mechanical/monolith_cup_exploded.png"><img src="../hardware/mechanical/monolith_cup_exploded.png" alt="Cup: assembled and exploded views with the parts list"></a><br><b>Exploded view and parts list.</b> The bench-built core (cells, PA12 carrier, board) goes in from the bottom; the cap seals it with one radial O-ring.</td>
<td width="50%"><a href="../hardware/mechanical/monolith_cup_sections.png"><img src="../hardware/mechanical/monolith_cup_sections.png" alt="Cup sections"></a><br><b>Sections.</b> A-A through the gap filler and webs, B-B through a USB-C port, C-C through the cap screws and O-ring.</td>
</tr>
<tr>
<td width="50%"><a href="../hardware/mechanical/monolith_cup_vs_tray.png"><img src="../hardware/mechanical/monolith_cup_vs_tray.png" alt="Side tray against the cup"></a><br><b>Tray vs cup.</b> Weight by function and the differences.</td>
<td width="50%"></td>
</tr>
</table>

All of these come from the Python models in `hardware/mechanical/`. Re-run the scripts after changing a parameter (see below).

## The cup (2026-10-21, the current design)

`monolith_cup.py`; design study in `research_notes/Ground-up mechanical concepts/` and [`../reports/Ground-up mechanical design.md`](../reports/Ground-up%20mechanical%20design.md).

- **Shell:** an MJF PA12 cup closed on five sides, 1.2 mm walls, with the two USB-C seal bores in its closed top wall. No aluminium cover, no wedge, no fish paper, no standoffs.
- **Core:** the cells sit in a one-piece PA12 carrier (two frames, spines, split rails, board pegs, full-length front-back webs). The board rides on the pegs, so cells and board move together; the nickel tongues only take up tolerance.
- **Closing it:** the core goes in from the bottom, port end first, until the USB-C faces seat in the top wall. A PA12 bottom cap seals it with one 2.0 mm radial O-ring in its skirt (~25 % squeeze), lands on the rim as a hard stop, and is held by two radial M2 screws below the seal. A TPU pad on the cap preloads the core.
- **Heat:** no heat spreader. The power stage dumps its heat through thermal vias and a dispensed gap filler into the two front cells (~300 J/K of thermal mass), and the PA12 webs share it with the back pair. The gap filler is about 4.5 g of Parker Chomerics THERM-A-GAP GEL 30 (decided 2026-10-24). Thermal model: `research_notes/Pack thermal BAK 65E/`; derate policy: `docs/firmware/charge-and-thermal-policy.md`.
- **Drop:** TPU bumpers at both ends (8 mm slab over the port end with a port well, 4 mm over the cap, solid bands over the edges), plus the pad inside the cap.
- **Venting:** one ePTFE vent on the board-face wall; its bare hole is the leak-test port (+10–15 kPa) before the patch goes on.
- **Size and mass:** 59.8 × 51.9 × 97.2 mm, about 384–400 g modelled. The model is designed to a 21.85 mm cell diameter (cell pitch 23.25 mm), so measure each cell's diameter before assembly; the bottom tab slots still need a recheck against the 65E's length (spec, P0 board changes).
- **PACK tails (option C, 2026-10-24):** nickel pads welded to the C1 and C4 bottoms, with an 18 AWG PTFE power wire and a 28 AWG Kelvin wire soldered to each; they pass through notches in the carrier's bottom frame (`wire_notches()`) into two Ø1.5 mm plated holes and two slots on the board (`sb_pack_holes()`). Details: [`production/p0-assembly.md`](production/p0-assembly.md).
- **Board:** same outline, slots and cell taps as the tray. New: two peg holes, the gap-filler zone on B.Cu with thermal vias, the rails split at z 25–55 mm, the PACK wire holes; the cover standoffs are gone.
- **Open:** the label (emboss, or a small plate), an O-ring dunk coupon in MJF, the push-in force.

## Board geometry shared with the retired side tray

The cup kept the side-board layout's board, so these still apply. They are generated from the side-tray parameters in `monolith_shell.py`.

- **BLE antenna:** the CC2340R5MODA goes on B.Cu at the right board edge (+y, the C4 / PACK+ side), antenna end at the edge, centre 19.1 mm below the top edge (KiCad about 116.6, 81.9).
    - That leaves 10 mm of ground above it and 10 mm to the USB-C bodies, and it radiates out through the printed side wall.
    - To make room for it, the board sits 2.3 mm further from the cells (`SB_BCU_H`).
    - `monolith_side_pcb.dxf` shows it on `BLE_MODULE_BCU`.
- **Board:** 1.6 mm thick (for cost). The outline is on the production board as well (`hardware/Production/tools/make_board.py` imports it from `monolith_shell.py`).
- **Files:** the board outline is `monolith_side_pcb.dxf`, with the `TAB_SLOTS`, `TAB_SLOT_PADS`, `BCU_TAIL_RUNS` and frame-bar layers that `make_board.py` follows.
- **Running it:** parameters are `SB_*` in `monolith_shell.py`, which also prints the assembly clearance checks.

The side tray itself (aluminium cover, wedge, TPU cell cage, cover label), the original top-cap tube and the scripts that render them are described in [`archive/side-tray-mechanical.md`](archive/side-tray-mechanical.md).
