# Monolith production board

KiCad 10 project `Monolith`. **Status (2026-10-17): schematic P0 only.** It is the dev board schematic (rev A8) with the dev-only parts removed. It has not been reviewed and there is no board yet.

## How P0 was made

`tools/make_production.py` (re-runnable) copies the dev board's sheets, libraries and project file from `DevBoard/` and edits them as follows:

- deletes parts by reference, then prunes the wires, labels, junctions, no-connects and power symbols left dangling;
- replaces 0 Ω links with wires;
- adds the production pads.

`tools/tidy_production.py` then tidies the drawings, with no electrical change:

- merges split wires and deletes the wires the link merges left between same-name labels;
- spreads the pogo pads into their own row;
- deletes the headings of removed blocks and renames the rest;
- rewrites every sheet's notes, the root index and the revision log;
- renames the sheets *3V3 Rail* and *MCU*.

`tools/check_netlist.py` then compares the result with the dev board netlist. Every surviving pin must keep its dev net, with only the intended link merges, and every new pad must take the net of the pin it replaces. Result: 956 pins checked, no differences, and 424 parts down to 295. ERC shows the dev board's 8 pin-to-pin warnings plus 3 off-grid notes on the root sheet pins.

Run all three in order with KiCad's Python:

```bash
"/c/Program Files/KiCad/10.0/bin/python.exe" Production/tools/make_production.py
```

```bash
"/c/Program Files/KiCad/10.0/bin/python.exe" Production/tools/tidy_production.py
```

```bash
"/c/Program Files/KiCad/10.0/bin/python.exe" Production/tools/check_netlist.py
```

Re-running overwrites the sheets. Once you start editing them by hand in KiCad, stop using the scripts.

## Removed (decided 2026-10-17)

| Sheet | Removed | Why |
|---|---|---|
| Gauge | BT101–BT104 | cell holders; the production pack is welded |
| | J104, D104, D105 | bench supply |
| | R127 | fuse bypass |
| | R114, C109, D102 | DNP options |
| | SW101, R118 | wake button |
| | TP101–TP105, TP107, TP108 | test points |
| Sleep current / 3V3 | U201–U203, JP201/JP202, R202–R206, R208, C201–C205, TP201–TP209 | the whole sleep-current measurement section |
| | R201 (R_MEAS) → wire | PACK_LP is PACK_P now |
| | R207 → wire | link |
| MCU | J302, J303 + their series resistors | UART and spare-GPIO headers |
| | SW301 | reset button |
| | D301, R306, R307 | status LED (none on the product) |
| | R315 (DNP) | unused pull-up |
| | R301, R312 → wires | links |
| | TP302–TP304, TP307–TP309 | test points |
| | | DIO12, DIO18 and DIO20 are now free (no-connect) |
| USB ×2 | J402 | logic-analyser header |
| | TP402–TP421 | test points |
| | R450/C454, R451/C455 | DNP snubbers; removed before bring-up, by choice |
| | C447 | DNP feed-forward cap |
| | C435 | battery-side bank down to 2 × 22 µF + hybrid: 87 µF effective, hybrid at 63 % of its ripple rating (cap sims 2026-10-17, B2) |
| | R401, R431 → wires | links |
| | R440 → wire | D+/D− become one net, `DPDN_DCP` (rev 2 item 1c) |
| | R448, R449 → wires | BTST links |
| Root | R1–R4 straps | port 1 ADCIN1 is tied to its LDO_3V3; the other ADCIN pins to GND |

## Added or changed

- **PP5V bulk:** C443/C543, the 100 µF polymer, is now a 22 µF 25 V 1206 (CL31A226KAHNNNE, LCSC C12891, the same part as C441). This leaves three 22 µF parts, about 33 µF effective, and saves about 43 mm² per port.
    - Each port's PP5V comes from its own TPS62933, so the USB PD cSrcBulk minimum (10 µF, dedicated supply) applies. The 120 µF cSrcBulkShared in the TPS25751 table is for a shared supply (checked 2026-10-17, `docs/devboard/cap-reduction-sims-2026-10-17.md`).
    - The estimated 0.5 → 3 A step undershoot is about 190 mV against a 250 mV budget. Measure it on the dev board with C443 removed.
- **Pack wires:**
    - J108 PACK− (CELL_N) and J112 PACK+ (CELL_P_RAW): 16 AWG pads (`SolderWire-1.5sqmm`, Ø1.7 mm hole);
    - J109–J111: CELL1–CELL3 tap pads (`SolderWire-0.15sqmm`);
    - J102, J105–J107: cell NTC wire pads.
- **Gauge access:** TP110 SMBC, TP111 SMBD, TP112 GND, 1.5 mm pogo pads in a row (replace the EV2400 header J103).
- **SWD:** J301 is a Tag-Connect TC2030-NL footprint (VCC, SWDIO, NRST, SWCLK, GND; SWO not connected). Use an XDS110 with a TC2030-CTX cable.
- **Factory test pads (1.5 mm):** TP106 PACK_P, TP109 GND, TP301 3V3, TP401/TP501 VBUS.

## Next

1. **Review P0**, mainly gauge note 10. With no wake button, the gauge has to come out of SHUTDOWN when USB brings up PACK_P, through the TPS25751 dead-battery sink and the BQ25756 charging with 3V3 down. Confirm this on the dev board.
2. **Cap cut still on hold** (`docs/devboard/cap-reduction-sims-2026-10-17.md`):
    - C427/C527 (USB-side MLCC): only if dev board bring-up shows the polymer stays cool at 20 V 5 A reverse from a low pack (it reaches 85 % of its rating), or if firmware derates that case.
3. **Decide the production board's thickness and stack-up**, then start the layout from `mechanical/monolith_bottom_pcb.dxf`.
