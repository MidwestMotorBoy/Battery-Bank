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

## Passive downsizing (2026-10-17)

Production may use JLC extended parts and 0201 parts. 0201 is used only where both of a part's nets stay at or below 5.5 V. The swaps are in `DOWNSIZE` in `tools/make_production.py`, and each part was checked for rating and JLC stock the same day.

Courtyard area went from **2,653 to 2,221 mm²** for all placed parts (−16 %). Passives alone went from about 1,570 to 1,170 mm² (−25 %).

| Change | Parts (port 1 shown, port 2 = 5xx) | Saved |
|---|---|---|
| Charger inductor 10×10 → Coilank APS0730M2R2F (7.8×7.6×3.1 mm) | L401/L501 | 162 mm² |
| 0603 resistors → 0402 | R110, R112, R117, R410, R413–R416, R420, R433, R444–R447 | ~60 mm² |
| Low-voltage R/C 0402 → 0201 | pull-ups and pull-downs, SMBus series R, FSW, MCU and LDO_3V3 decoupling | ~30 mm² |
| Sense resistors: RAC 2010 → 0805 0.5 W, RBAT 2010 → 1206 1 W, gauge shunt 2512 → 1206 1 W 75 ppm | R424, R427, RS101 | ~58 mm² |
| Cell filter resistors 1206 → 0402 (with a welded pack, no cell can be reversed in an open holder) | R101–R104 | 34 mm² |
| BAT54WS SOD-323 → Nexperia BAT54L SOD-882 | D101, D406–D409 | ~37 mm² |
| REGN/DRV_SUP, sense filter and soft-start caps 0603 → 0402 | C410, C411, C414, C417, C439 | ~13 mm² |
| NTC 0603 → 0402 (NCP15XH103F03RC: same 3380/3435 K curve, so the TS thresholds don't move) | TH401 | 3 mm² |

**Checked and kept:**

- **Bulk polymers C421/C432.** No smaller 100 µF 35 V polymer is stocked. The only smaller 25 V option is a polymer tantalum, rated for up to 250 µA leakage, which would wreck the sleep budget on PACK_P.
- **TPS25751 VIN_3V3, LDO_3V3 and PP5V caps.** Their datasheet minimums after derating don't fit a 0402.
- **50 V 1206s on 5V_IN and VBUS.** DC bias at 16.8–20 V would take them under the TPS62933 and TPS25751 needs.
- **C207**, the TPS62177 output cap.
- **The RF match parts**, kept at 0402 so they can be retuned.

**Inductor trade-off:** the APS0730 costs $0.56 against about $8.50 for the Coilcraft XAL7070-222. In return it runs hotter: about 1.6 W DCR loss at the worst case (reverse 20 V 5 A from a 10 V pack), against about 1.0 W for the old part. It also drops to about 1.7 µH at the 12 A peak. Measure its temperature on the dev board before committing to it. The XAL7070-222 fits the same space if it runs too hot.

## Gate drive and shared battery-side bulk (2026-10-17)

- **Gate resistors and diodes removed.** R444–R447 are now copper, and D406–D409 are gone (both ports): HIDRV/LODRV drive the FET gates directly. The dev board fits 10 Ω gate resistors, so measure SW1/SW2 ringing there with them bridged before relying on this.
- **One shared battery-side hybrid.** Both chargers' battery sides, both TPS62933 inputs and the pack all sit on one PACK_P bus, so `tools/pack_bus_sims.py` models them as one network. Each port's MLCCs sit behind its 5 mΩ RBAT, and the shared bulk sits between the two power stages. The model runs both chargers and both bucks together: single-port worst cases, both ports sourcing, pass-through, and a buck plus a charger.

| Option | Battery-side effective C (worst, 16.8 V) | Worst part | Ripple | Damping | Area |
|---|---|---|---|---|---|
| Before: 2 × 22 µF + hybrid + 2 × 10 µF 50 V, per port | 185 µF | 47 % | 80 mV | 20.3 dB | 217 mm² |
| One shared hybrid, rest unchanged | 105 µF | 28 % | 148 mV | 20.2 dB | 151 mm² |
| **Applied: one shared hybrid, 2 × 22 µF + 1 × 10 µF 50 V per port** | **99 µF** | **44 %** | **232 mV** | **20.2 dB** | **130 mm²** |
| As applied, but 1 × 22 µF per port | 92.5 µF | 55 % | 267 mV | 20.0 dB | 109 mm² |
| No hybrid at all | 25 µF (below the 80 µF minimum) | 27 % | 143 mV | 14.5 dB | 84 mm² |

The BQ25756 needs C_OUT ≥ 80 µF after derating (datasheet sec. 5.3). Each charger sees the whole bus through its RBAT, so one hybrid has to stay.

- **Removed:** C432/C532, the per-port hybrids, and C445/C545, the second TPS62933 input caps.
- **Added:** C208, a 100 µF 25 V hybrid (EEH-ZA1E101XP) on the 3V3 Rail sheet. Place it between the two power stages on PACK_P, next to both RBAT pads.
- **USB sides:** these can't share bulk, because each port has its own VBUS/PPHV, so C421/C521 stay. C427 is still on hold for bring-up.

**Totals:** 276 parts (262 placed), and courtyard area is now **2,104 mm²**, down from 2,653 mm² before any downsizing (−21 %).

## Liquid detection removed (2026-10-17)

The production ports have IP68 connectors and a potted board, so liquid detection is dropped. Port 1 is listed; port 2's 5xx parts are the same.

- **Removed:** Q403–Q406 (SBU pull FETs), R436–R439 and R442/R443.
- **TPS25751 GPIO4–GPIO7:** tied to GND, as its datasheet says for unused GPIOs. Configure them as unused in the TPS25751 configuration, never as outputs.
- **TPD4S201 system-side SBU pins:** left as no-connects. Grounding them would short a cable's SBU lines whenever the SBU switch is on.
- **Kept:** the TPD4S201 itself, for CC and SBU overvoltage and ESD protection, and its fault output R441 → GPIO3.
- **ERC:** shows 8 more of the expected "GPIO tied to GND" pin-to-pin warnings, 16 in total.

Parts: 256.

**Checked and not applied: dual FETs for the chargers (packaging option 4).**

- **40 V half-bridges at JLC** come only in 5×6 mm (Infineon IAUC60N04S6N050), the same area as two 3.3×3.3 singles.
- **3.3×3.3 half-bridges** are 30 V only (SiZ340). That's too little with 20 V VBUS, the 22.5 V OVP and the 28 V TVS clamp, now that there are no gate resistors.
- **3×3 duals with independent FETs** could pair only the two low sides, Q407 + Q408: their sources share GND, and the two never carry heavy current at the same time. The high sides can't share: about 2 W in one package at the worst case.
- **The dual parts on offer don't qualify:** the genuine Vishay SiSB46DN is out of stock and has 15.8 mΩ at 4.5 V (today's part: 10 mΩ). The stocked "SiSB46DN-HXY" clone lists specs the original doesn't have. Other duals are 13–22 mΩ.
- **Not worth it:** the gain would be only about 31 mm² for both ports, so the four singles per port stay.

## Next

1. **Review P0**, mainly gauge note 10. With no wake button, the gauge has to come out of SHUTDOWN when USB brings up PACK_P, through the TPS25751 dead-battery sink and the BQ25756 charging with 3V3 down. Confirm this on the dev board.
2. **Cap cut still on hold** (`docs/devboard/cap-reduction-sims-2026-10-17.md`):
    - C427/C527 (USB-side MLCC): only if dev board bring-up shows the polymer stays cool at 20 V 5 A reverse from a low pack (it reaches 85 % of its rating), or if firmware derates that case.
3. **Decide the production board's thickness and stack-up**, then start the layout from `mechanical/monolith_bottom_pcb.dxf`.
