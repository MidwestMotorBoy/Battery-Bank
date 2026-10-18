# Monolith battery bank

An ultralight 100 W USB-C battery bank for backpacking: four EVE INR21700-58E cells (4S1P, about 82 Wh) in a printed tube, with two USB-C PD ports and Bluetooth.

**Status (2026-10-14):** nothing has been built, test-fitted or bench-tested yet.
- **Dev board** (`DevBoard/`): the active work, a bench version of the electronics.
    - **Schematic:** rev A7, three datasheet reviews. Rev A7 swapped the MCU to a TI CC2340R5MODA (cost-down) Rev A8 removed the board temperature sensors: the gauge and the chargers' NTCs cover it.
    - **Board:** 6-layer, all parts placed for rev A7, not routed.
    - **Firmware** (`firmware/`): a bring-up skeleton for the LP-EM-CC2340R53 LaunchPad, not built yet. It targets TI's LPF3 SDK (SysConfig, TI Arm Clang, XDS110 debugger). Install steps are in [`firmware/README.md`](firmware/README.md), and the LaunchPad plan is `docs/devboard/launchpad-cc2340-plan.md`.
- **Product top board:** not started. It will be drawn from the dev board results. The 2026-10-09 draft was removed on 2026-10-14; it is kept in git as the tag `product-draft-2026-10-09`.

## Contents

- `firmware/` holds the MCU firmware (CC2340, LPF3 SDK, command-line build).
- `DevBoard/` is the dev board's KiCad 10 project.
    - It has its own library, its generator and placement scripts, and a costed BOM (`bom_cost.csv`).
    - Start with [`DevBoard/README.md`](DevBoard/README.md): files, board rules, status and the full change log.
- `docs/devboard/` holds the dev board documents:
    - the circuit description;
    - schematic reviews 1–3;
    - the cost-down list;
    - the power budget and the MCU pin-by-power-state plan (STM32-era, rewrite pending);
    - the CC2340R5MODA pin budget (`cc2340-pin-budget.md`);
    - the bring-up configuration checklist;
    - the LP-EM-CC2340R53 LaunchPad plan (`launchpad-cc2340-plan.md`);
    - changes planned for rev 2.
- `docs/project/` holds project notes: next actions, cell datasheet notes, TPS25751 EEPROM programming.
- `datasheets/` holds the datasheets and app notes the designs were checked against, indexed in `datasheets/sources.csv`.
- `mechanical/` holds STL models for the shell, cap and test-print parts, the bottom board outline (DXF), and the Python scripts that generate them.
    - Since 2026-10-18 the scripts also model a **side-board layout**, still under evaluation. The board runs along one face of the cells, inside a one-piece printed tray whose only opening is the board side.
        - **Closing it:** a recessed 1 mm aluminium cover (also the heat spreader). Its top edge tucks under a lip in the top wall, and two M2 screws go into heat-set inserts in the bottom corner pillars.
        - **Ports:** the board drops in, then slides 2.5 mm toward the top so the USB-C mating faces pass into their holes in the top wall.
        - **Venting:** no airflow vents; one ePTFE pressure vent over a hole in the cover.
        - **Drop protection (2026-10-18):** no potting. The basis is `reports/Battery pack potting and drop protection.md`. The tray, cells and board form one stiff core, and TPU end caps outside it are the crush zone.
            - **End caps:** 8 mm of TPU lattice, graded soft-outside and firm-behind. Corner noses are dense. A solid band, 2 mm proud of the tray, wraps 9 mm over each end, so flat side drops land on the bands. The top cap has one port well for both plugs.
            - **Inside (hobby build: the only sheet stock is 1 mm EVA foam, 0.2 mm mica and 0.2 mm fish paper):**
                - Cell-end pads of 1 mm EVA, with cut-outs over each positive cap so the vent stays open. The floor pad sits on a printed 3.8 mm TPU spacer (about 20 % gyroid).
                - Fish paper, 0.2 mm, in three places: a liner round the cells (the cans stay close to the walls for heat), a sheet on the cells' board-side face (it also covers the B.Cu parts), and rings on the four + ends (21 mm OD, about 10 mm hole).
                - EVA lanes (3 × 1 mm, about 20 % squeezed) between that sheet and B.Cu, along the two cell tangent lines. They hold the cells off the board now that there is a 2.3 mm gap behind it. Keep B.Cu parts out of the lanes (`BCU_EVA_LANES` on the board DXF) and under 2.3 mm tall elsewhere.
                - A 0.2 mm mica cross between the cells.
                - Board top stops, so drop loads reach the tray through the board edge rather than the USB-C.
                - A TPU shim under the board, and 2 x 1 mm EVA hold-downs over the USB-C bodies.
            - **No rupture windows:** removed 2026-10-18. No consumer power bank found has a designed burst point (UL 2056 has no venting requirement), and a printed tray splits anyway. The pad cut-outs stay so the cells' own vents aren't blocked.
            - **Cost of the protection:** the pack is now 58.7 × 50.4 × 96.6 mm, and about 364 g including the pads and mica (+26 g). The estimated peak is about 250 g at 1.0 m and about 375 g at 1.5 m. These are estimates, to be measured.
            - **Unchanged:** the board outline and ports (the tray only widens in the cell zone).
            - **Pack connections:** everything is soldered from the open side once the board is in, so it all lands on F.Cu (`monolith_side_tabs.png`).
                - **PACK- and PACK+:** 0.15 × 7 mm nickel strips from the C1 and C4 bottoms. Each drops down behind the board, wraps under its bottom edge and is soldered to an F.Cu pad, 8 × 5 mm at KiCad x 89.1 / 110.9, y 134.7. The shim is now one centre block between them.
                - **CELL1, CELL3 and CELL2:** sense taps only, so thin wires (about 28 AWG silicone) go through plated holes at KiCad (98.0, 71.5), (102.0, 71.5) and (102.0, 133.5).
                    - The top two run down the groove behind the board between C1 and C4, which has 5 mm free.
                    - CELL2 runs in a channel in the floor spacer.
                    - The top EVA has slots for the wires.
                - Holes and pads are on the board DXF's `TAB_PADS` layer.
                - Take the gauge's PACK-/PACK+ Kelvin sense from the pads.
            - **Vibration and trail durability (2026-10-18):**
                - **Cells are preloaded everywhere:**
                    - crush ribs on the cell-zone walls flatten 0.25 mm into the liner;
                    - the floor spacer prints 0.4 mm taller than its gap, which takes up MJF's ±0.3 mm;
                    - the EVA lanes are squeezed about 20 %.
                - **Cover:**
                    - It has a 0.3 mm joint all round, because nylon grows about 0.35 mm more than aluminium over 60 K.
                    - The joint is sealed with a bead of neutral-cure silicone, which acts as the gasket.
                    - Four SMD standoffs (about 3.6 mm, `COVER_STANDOFFS` on the board DXF) carry crush loads instead of the parts.
                    - Use M2 thread-forming screws with a nylon patch or a plastic-safe threadlocker.
                - **Caps:**
                    - A bead inside each cap band snaps into a 0.3 mm groove round the tray.
                    - The top cap has a drain channel from the port well.
                - **Assembly:**
                    - Give the PACK strips a small S-bend, and keep their solder joints away from the bend.
                    - Weld at the cells.
                    - Tack the sense wires in their slots with neutral-cure silicone.
                - **Open item for the board:** C421/C521 (100 µF 35 V polymer, about 7.7 mm tall) and C208 (hybrid, about 5.8 mm tall) don't fit the 3.2 mm F.Cu height or the B.Cu room. Pick lower-profile parts, or raise the cover.
            - **BLE antenna:** the CC2340R5MODA goes on B.Cu at the right board edge (+y, the C4 / PACK+ side), antenna end at the edge, centre 19.1 mm below the top edge (KiCad about 116.6, 81.9).
                - That leaves 10 mm of ground above it and 10 mm to the USB-C bodies.
                - The board's ground plane sits between it and the aluminium cover, and it radiates out through the printed side wall. The cover stays whole.
                - To make room for it, the board sits 2.3 mm further from the cells (`SB_BCU_H`); the outline and ports didn't change.
                - `monolith_side_pcb.dxf` shows it on `BLE_MODULE_BCU`.
        - **Board:** 1.6 mm thick (for cost; the pack is 0.8 mm wider than with a 0.8 mm board). The outline is on the production board as well (`Production/tools/make_board.py` imports it from `monolith_shell.py`).
        - **Files:** parts are `monolith_side_*.stl`; the board outline (with corner notches for the pillars) is `monolith_side_pcb.dxf`; the cover's flat pattern is `monolith_side_cover.dxf`.
        - **Running it:** parameters are `SB_*` in `monolith_shell.py`, which also prints the assembly clearance checks. `python monolith_parts.py side` builds only these parts.
    - `monolith_render.py` renders both layouts side by side to `monolith_layout_compare.png` and prints a size and mass table. It needs numpy, scipy and Pillow.
    - `monolith_side_renders.py` renders the side tray's drop design:
        - `monolith_side_exploded.png`: assembled and exploded views;
        - `monolith_side_sections.png`: sections A-A and B-B;
        - `monolith_side_parts.png`: the cap zones, the tray and the pads, plus mass, drop and print-setting tables;
        - `monolith_side_tabs.png`: the nickel strips and sense wires, and the board face with the pad and hole positions.
    - **Cover heatsink and label (prototype):** `monolith_cover_label.py` builds the aluminium cover for JLCCNC sheet metal: 1.0 mm 5052, black anodized, laser-marked.
        - It needs shapely and matplotlib as well, and KiCad 10's `kicad-cli` for the STEP.
        - **Outputs:**
            - `monolith_side_cover.step`: the plate (JLCCNC requires a STEP);
            - `monolith_side_cover_marking.dxf` / `.svg`: the marking as outlined shapes, every line at least 0.2 mm (JLCCNC asks for outlined, double-line text);
            - `monolith_side_cover_preview.png`.
        - **Label:** Li-ion 4S1P, 14.4 V, 5.7 Ah, 82 Wh (from `docs/project/eve-58e-datasheet-notes.md`), the USB-C PD ratings, warnings, the recycling and WEEE symbols, and our own carry-on badge (an airliner in a ring with a check disc, "CARRY-ON OK · < 100 Wh"). It carries no certification marks.
        - **Graphic:** a topo map with a dashed trail from the trailhead to a summit flag at "EL. 82 Wh".
        - The script checks the art stays between the cap bands, clear of the vent, and has no line under 0.2 mm. Ratings are prototype values, to confirm before the final.
    - **Cap print zones:** each cap prints as one TPU body. Load the `*_mod_soft` and `*_mod_corner` STLs as slicer modifiers.
- `tools/fetch_datasheets.sh` fetches the datasheets.

## Dev board main parts

- **Gauge and protection:** BQ40Z50-R2 gauge with CHG/DSG FETs and a 1 mΩ shunt. A BQ294700 second-level protector drives a chemical fuse.
- **Each USB-C port:**
    - TPS25751D PD controller with EEPROM;
    - TPD4S201 CC/SBU protection and liquid detection;
    - BQ25756 buck-boost charger with four discrete PGQ04N070 FETs;
    - TPS62933 5 V source.
- **Supply and sleep current:** TPS62177 3.3 V rail, and INA190 amplifiers on a 10 Ω R_MEAS for measuring sleep current.
- **MCU:** TI CC2340R5MODA Bluetooth LE module (rev A7; was the STM32WB1MMC). Its 10 usable GPIOs are all assigned.
- **Board temperature:** no dedicated sensors (rev A8). The gauge reports the four cell NTCs and the protection-FET temperature; each charger's NTC is read through its PD controller. The USB-C connectors are not monitored.

## Known open items

**Dev board:**
- silkscreen pass;
- routing;
- LCSC numbers, stock and price for the rev A7 parts (CC2340R5MODA, RF match);
- antenna match tuning (C314/C315) and a BLE range check on the real board;
- rewrite of the MCU pin-by-power-state plan for the CC2340;
- the U403/U503 footprint library warning;
- ~~production board thickness~~: decided 2026-10-18, 1.6 mm for cost (`Production/README.md`).

Details are in `DevBoard/README.md`, and rev 2 changes in `docs/devboard/rev2-changes.md`.

**Product top board:** not started; it will follow from the dev board results. The board outline is `mechanical/monolith_bottom_pcb.dxf`.
