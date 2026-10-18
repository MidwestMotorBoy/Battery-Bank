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
                - Fish paper, 0.2 mm, in three places: a liner round the cells (the cans stay close to the walls for heat), the insulator on the board's back, and rings on the four + ends (21 mm OD, about 10 mm hole).
                - A 0.2 mm mica cross between the cells.
                - Board top stops, so drop loads reach the tray through the board edge rather than the USB-C.
                - A TPU shim under the board, and 2 x 1 mm EVA hold-downs over the USB-C bodies.
            - **Rupture windows:** the floor is thinned to 0.6 mm under the bottom positive caps (C2, C4). This is a concept, still to be tested.
            - **Cost of the protection:** the pack is now 56.4 × 50.4 × 96.6 mm, and about 361 g including the pads and mica (+23 g). The estimated peak is about 250 g at 1.0 m and about 375 g at 1.5 m. These are estimates, to be measured.
            - **Unchanged:** the board outline and ports (the tray only widens in the cell zone).
            - **Open item:** the aluminium cover sits over the BLE antenna. `monolith_side_cover.dxf` has an `ANT_WINDOW_OPTION` layer for a possible window.
        - **Board:** 1.6 mm thick (for cost; the pack is 0.8 mm wider than with a 0.8 mm board). The outline is on the production board as well (`Production/tools/make_board.py` imports it from `monolith_shell.py`).
        - **Files:** parts are `monolith_side_*.stl`; the board outline (with corner notches for the pillars) is `monolith_side_pcb.dxf`; the cover's flat pattern is `monolith_side_cover.dxf`.
        - **Running it:** parameters are `SB_*` in `monolith_shell.py`, which also prints the assembly clearance checks. `python monolith_parts.py side` builds only these parts.
    - `monolith_render.py` renders both layouts side by side to `monolith_layout_compare.png` and prints a size and mass table. It needs numpy, scipy and Pillow.
    - `monolith_side_renders.py` renders the side tray's drop design:
        - `monolith_side_exploded.png`: assembled and exploded views;
        - `monolith_side_sections.png`: sections A-A and B-B;
        - `monolith_side_parts.png`: the cap zones, the floor pad and rupture windows, plus mass, drop and print-setting tables.
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
