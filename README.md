# Monolith battery bank

An ultralight 100 W USB-C battery bank for backpacking: four EVE INR21700-58E cells (4S1P, about 82 Wh) in a printed tube, with two USB-C PD ports and Bluetooth.

**Status (2026-10-14):** nothing has been built, test-fitted or bench-tested yet.
- **Dev board** (`DevBoard/`): the active work, a bench version of the electronics.
    - **Schematic:** rev A7, three datasheet reviews. Rev A7 swapped the MCU to a TI CC2340R5MODA (cost-down) and the board NTCs to TMP1075 I2C sensors.
    - **Board:** 6-layer, all parts placed for rev A7, not routed.
    - **Firmware:** not started. It targets TI's LPF3 SDK (SysConfig, TI Arm Clang, XDS110 debugger).
- **Product top board** (`BatteryBank.kicad_*`): still the early draft from 2026-10-09.

## Contents

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
    - changes planned for rev 2.
- `docs/project/` holds project notes: next actions, cell datasheet notes, TPS25751 EEPROM programming.
- `docs/*.csv` holds the product net list and the port 1 parts list.
- `datasheets/` holds the datasheets and app notes the designs were checked against, indexed in `datasheets/sources.csv`.
- `BatteryBank.kicad_*`, `Monolith.kicad_sym`, `sym-lib-table` are the product top board.
    - Its schematic is a first draft connected by net labels.
    - Its PCB has only the outline and mechanical reference marks.
- `mechanical/` holds STL models for the shell, cap and test-print parts, the bottom board outline (DXF), and the Python scripts that generate them.
- `tools/` holds the scripts that generated the product schematic and fetched the datasheets.

## Dev board main parts

- **Gauge and protection:** BQ40Z50-R2 gauge with CHG/DSG FETs and a 1 mΩ shunt. A BQ294700 second-level protector drives a chemical fuse.
- **Each USB-C port:**
    - TPS25751D PD controller with EEPROM;
    - TPD4S201 CC/SBU protection and liquid detection;
    - BQ25756 buck-boost charger with four discrete PGQ04N070 FETs;
    - TPS62933 5 V source.
- **Supply and sleep current:** TPS62177 3.3 V rail, and INA190 amplifiers on a 10 Ω R_MEAS for measuring sleep current.
- **MCU:** TI CC2340R5MODA Bluetooth LE module (rev A7; was the STM32WB1MMC). Its 10 usable GPIOs are all assigned.
- **Board temperature:** TMP1075 I2C sensors at each charger stage and the USB-C connectors, plus two DNP spots. Their alerts share one IRQ_N line with the PD controllers and the gauge.

## Known open items

**Dev board:**
- silkscreen pass;
- routing;
- LCSC numbers, stock and price for the rev A7 parts (CC2340R5MODA, TMP1075, RF match);
- antenna match tuning (C314/C315) and a BLE range check on the real board;
- rewrite of the MCU pin-by-power-state plan for the CC2340;
- the U403/U503 footprint library warning;
- production board thickness.

Details are in `DevBoard/README.md`, and rev 2 changes in `docs/devboard/rev2-changes.md`.

**Product top board:** still has placeholder parts and no footprints. It will follow from the dev board results.
