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
        - **Board:** 1.6 mm thick (for cost; the pack is 0.8 mm wider than with a 0.8 mm board). The outline is on the production board as well (`Production/tools/make_board.py` imports it from `monolith_shell.py`).
        - **Files:** parts are `monolith_side_*.stl`; the board outline (with corner notches for the pillars) is `monolith_side_pcb.dxf`; the cover's flat pattern is `monolith_side_cover.dxf`.
        - **Running it:** parameters are `SB_*` in `monolith_shell.py`, which also prints the assembly clearance checks. `python monolith_parts.py side` builds only these parts.
    - `monolith_render.py` renders both layouts side by side to `monolith_layout_compare.png` and prints a size and mass table. It needs numpy, scipy and Pillow.
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
