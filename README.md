# Monolith battery bank

An ultralight 100 W USB-C battery bank for backpacking: four EVE INR21700-58E cells (4S1P, about 82 Wh) in a printed tube.

**Status: early draft. Nothing here has been built, test-fitted or bench-tested.**

## Contents

- `BatteryBank.kicad_*` - KiCad 10 project for the top board. The schematic is a first draft with connections made by net labels; the PCB has the outline and mechanical reference marks only.
- `Monolith.kicad_sym`, `sym-lib-table` - project symbol library.
- `docs/` - net list and early parts lists.
- `mechanical/` - STL models for the shell, cap and test-print parts, the bottom board outline (DXF), and the Python scripts that generate them.
- `tools/` - Python scripts that generate the schematic.

## Main parts

TPS25751D (USB-C PD), BQ25756 (charger and buck-boost), BQ77915 (cell protection), TPS25810 (5 V port), TPS62933 and TPS70933 (rails), STM32WB1MMC (Bluetooth).

## Known open items

Several parts are placeholders (FETs, inductors, EEPROM), no footprints are assigned, the port 1 ESD protection is not drawn, and a number of pin connections are marked for checking against the datasheets.
