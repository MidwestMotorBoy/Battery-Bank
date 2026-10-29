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

- **Shell:** an MJF PA12 cup closed on five sides, 1.2 mm walls (2.0 mm on the board face, 1.85 mm top wall), with the two USB-C seal bores in its closed top wall. The bores are the connector's rev A4 ring (10.35 × 4.57 mm) minus 0.15 mm a side, with a 0.3 mm lead-in. No aluminium cover, no wedge, no standoffs.
- **Core:** the cells sit in a one-piece PA12 carrier (two frames, spines, full-length front-back webs). The four board rails are separate clip-on blocks that key into the frames after the cells are in, so the front cells can be loaded. The board rides on the rails' peg posts, which run on to 0.3 mm under the board-face wall with TPU sleeves, so a drop on that face loads the carrier and not the inductors. Fish-paper rings insulate each + end from its own crimp shoulder, and foam rings under the cells take up the axial play.
- **Closing it:** the core goes in from the bottom, port end first, until the USB-C faces seat in the top wall. A PA12 bottom cap seals it with one 2.0 mm radial O-ring in its skirt (~25 % squeeze, skirt 2.6 mm thick). An outer 1.5 mm collar with crush ribs holds the cup's mouth round so the flats can't bow off the O-ring. Two radial M2 thread-forming screws go through the collar into blind pilots below the seal (no through-path into the pack). Four overtravel posts land on the frame as the hard stop, and a TPU pad printed 1.2 mm proud on the cap preloads the core.
- **Heat:** no heat spreader. The power stage dumps its heat through thermal vias and a dispensed gap filler into the two front cells (~300 J/K of thermal mass), and the PA12 webs share it with the back pair. The gap filler is about 4.5 g of Parker Chomerics THERM-A-GAP GEL 30 (decided 2026-10-24). Thermal model: `research_notes/Pack thermal BAK 65E/`; derate policy: `docs/firmware/charge-and-thermal-policy.md`.
- **Drop:** TPU bumpers at both ends (8 mm slab over the port end with a port well, 4 mm over the cap, solid bands over the edges), plus the pad inside the cap.
- **No vent (2026-10-28):** Logan removed the ePTFE vent, so the cup keeps the air it was closed with. At altitude it pushes out: about +25 kPa in an airliner, +40 kPa at 4300 m and about +50 kPa there with the pack warm. At +50 kPa the 1.2 mm side flats see about 25–31 MPa (half to two-thirds of PA12's tensile strength; nylon creeps above about 15) and bulge 1–2 mm, and the cap pushes out with about 120 N, which the two M2 screws take as about 19 MPa of shear in the 1.3 mm ligament under their holes (`sealed_pressure()` in `monolith_cup.py`). Cooling after closing pulls it the other way, about −10 kPa, which the 2.0 mm board face and the peg posts already cover. Close the cap in dry indoor air. The leak test is a vacuum-jar bubble test on the closed pack (`production/p0-assembly.md`, step 6).
- **Size and mass:** 61.9 × 53.8 × 98.5 mm, about 389 g modelled (after the 2026-10-24 review fixes; `python3 monolith_cup.py none` prints the part table). The model is designed to a 21.85 mm cell diameter (cell pitch 23.25 mm), so measure each cell's diameter before assembly.
- **PACK tails (option C, 2026-10-24):** nickel pads welded to the C1 and C4 bottoms, with an 18 AWG PTFE power wire and a 28 AWG Kelvin wire soldered to each; they pass through one notch per side in the carrier's bottom frame (`wire_notches()`) into two Ø1.5 mm plated holes and two Ø0.8 mm holes on the board (`sb_pack_holes()`).
- **Sense wires (2026-10-24):** the three cell taps are 28 AWG PTFE wires too, into Ø0.8 mm plated holes in 1.5 × 1.4 mm pads (`sb_slots()`). CELL1 and CELL3 solder to a flat tongue on their top strip (`_top_tongue()`); CELL2 solders to the middle of the bottom strip and runs in a 1.0 × 0.95 mm channel in the bottom frame (`sense_channel()`). Details: [`production/p0-assembly.md`](production/p0-assembly.md).
- **Board:** same outline and cell-tap positions as the tray. New: sense-wire holes in place of the tab slots, four peg slots (H101–H104, the former cover-standoff references), the gap-filler zone on B.Cu with thermal vias, the rails split at z 25–55 mm, the PACK wire holes; the cover standoffs are gone.
- **Label:** a printed vinyl wrap label (Borderlands bear art, 2026-10-28) in the cup's label relief; art and order files in [`hardware/label/`](../hardware/label/README.md).
- **Open:** the three coupons (cap collar on a mouth section, a clip-on rail block, a USB-C bore), the drop series, the push-in force.

## Board geometry shared with the retired side tray

The cup kept the side-board layout's board, so these still apply. They are generated from the side-tray parameters in `monolith_shell.py`.

- **BLE antenna:** the CC2340R5MODA goes on B.Cu at the right board edge (+y, the C4 / PACK+ side), antenna end at the edge, centre 19.1 mm below the top edge (KiCad about 116.6, 81.9).
    - That leaves 10 mm of ground above it and 10 mm to the USB-C bodies, and it radiates out through the printed side wall.
    - To make room for it, the board sits 2.3 mm further from the cells (`SB_BCU_H`).
    - `monolith_side_pcb.dxf` shows it on `BLE_MODULE_BCU`.
- **Board:** 1.6 mm thick (for cost). The outline is on the production board as well (`hardware/Production/tools/make_board.py` imports it from `monolith_shell.py`).
- **Files:** the board outline is `monolith_side_pcb.dxf`, with the `SENSE_WIRE_HOLES`, `SENSE_WIRE_PADS`, `BCU_TAIL_RUNS`, `BCU_WIRE_RUNS` and frame-bar layers that `make_board.py` follows.
- **Running it:** parameters are `SB_*` in `monolith_shell.py`, which also prints the assembly clearance checks.

The side tray itself (aluminium cover, wedge, TPU cell cage, cover label), the original top-cap tube and the scripts that render them are described in [`archive/side-tray-mechanical.md`](archive/side-tray-mechanical.md).
