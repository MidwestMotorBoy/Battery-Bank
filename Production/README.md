# Monolith production board

KiCad 10 project `Monolith`. **Status (2026-10-17): schematic P0 only.** It is the dev board schematic (rev A8) with the dev-only parts removed. It has not been reviewed, there is no board yet, and the drawings still need a tidy pass.

## How P0 was made

`tools/make_production.py` (re-runnable) copies the dev board's sheets, libraries and project file from `DevBoard/` and edits them as follows:

- deletes parts by reference, then prunes the wires, labels, junctions, no-connects and power symbols left dangling;
- replaces 0 Ω links with wires;
- adds the production pads.

`tools/check_netlist.py` then compares the result with the dev board netlist. Every surviving pin must keep its dev net, with only the intended link merges, and every new pad must take the net of the pin it replaces. Result: 960 pins checked, no differences, and 424 parts down to 297. ERC shows the dev board's 8 pin-to-pin warnings plus 3 off-grid notes on the root sheet pins.

Don't hand-edit the sheets until the tidy pass has been done and you've decided to stop re-running the script. Re-running overwrites them.

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
| | R401, R431 → wires | links |
| | R440 → wire | D+/D− become one net, `DPDN_DCP` (rev 2 item 1c) |
| | R448, R449 → wires | BTST links |
| Root | R1–R4 straps | port 1 ADCIN1 is tied to its LDO_3V3; the other ADCIN pins to GND |

## Added or changed

- **Pack wires:**
    - J108 PACK− (CELL_N) and J112 PACK+ (CELL_P_RAW): 16 AWG pads (`SolderWire-1.5sqmm`, Ø1.7 mm hole);
    - J109–J111: CELL1–CELL3 tap pads (`SolderWire-0.15sqmm`);
    - J102, J105–J107: cell NTC wire pads.
- **Gauge access:** TP110 SMBC, TP111 SMBD, TP112 GND, 1.5 mm pogo pads (replace the EV2400 header J103).
- **SWD:** J301 is a Tag-Connect TC2030-NL footprint (VCC, SWDIO, NRST, SWCLK, GND; SWO not connected). Use an XDS110 with a TC2030-CTX cable.
- **Factory test pads (1.5 mm):** TP106 PACK_P, TP109 GND, TP301 3V3, TP401/TP501 VBUS.

## Next

1. **Tidy the drawings:**
    - spread the new pads;
    - move the TC2030 off R302/C304;
    - delete empty headings (Wake + bench supply, Debug headers, Status LED);
    - rewrite the sheet notes and the root sheet index.
2. **Cap cuts from the 2026-10-17 simulations** (`docs/devboard/cap-reduction-sims-2026-10-17.md`): C435/C535 out.
3. **Decide the production board's thickness and stack-up**, then start the layout from `mechanical/monolith_bottom_pcb.dxf`.
