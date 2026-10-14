# Schematic review 3: hand-review branch (2026-10-14)

Third review of the MonolithDev schematic. It covers everything changed since rev A5 (review 2):

- Second-level protection: U102 BQ294700 and F102 WSFB1514.
- F101 deleted; D103 fitted; U202 swapped to INA190A1.
- R405–R408 removed.
- USB-C liquid detection: U405 TPD2S300, Q403–Q406, the R440 DCP short, and D403 removed.

It also re-checks the gauge and both USB ports against documents added to `datasheets/` today:

- The BQ40Z50-R2 technical reference manual (SLUUBK0) and circuit-design note (SLUA660).
- The BQ25756 EVM guide (SLUUCT7) and the TPS25751 EVM guide (SLVUCP9), both with reference schematics.
- The BQ2947, TPD2S300 and WSFB1514 datasheets.
- Datasheets for the discretes (AO3400A, AO3401A, BSS138, BZT52C15, BAT54WS, SS34, 1N4148WS, LRB520S-40, NCP18XH103, TS-1187A, the test loop, the C406 capacitor).

The MCU sheet, the 3V3 rail, the TPS62933 bucks and the sleep-current section were not changed since review 2 passed them, so they were not re-done.

Method: every pin of U101, U102, U401/U501, U403/U503 and U405/U505 was checked from the KiCad netlist against the datasheet pin table and the TI reference schematic. ERC was run, the power budget re-totalled, and stock checked on JLC today.

## Result

| Critical | Major | Minor (hardware) | Configuration / procedure | Documentation |
|---|---|---|---|---|
| 0 | 0 | 4 | 6 | 7 |

The new blocks match TI's references. U102's filter components and the fuse-ignition network are exactly TI's values. Nothing is wired wrongly.

The findings are:
- One gap against TI's EVM in liquid detection: the TPD2S300 fault output is unused.
- Two gauge data-flash settings that the new fuse makes necessary.
- One handling rule specific to a board with cell holders.

## Minor: hardware changes (proposed, not made)

| # | Item | Proposed change | Source |
|---|---|---|---|
| H1 | **U405/U505 FLT is unconnected.** When liquid bridges VBUS to SBU (SBU1 sits between D− and VBUS on the receptacle), the TPD2S300 opens its switch. The TPS25751 ADC then sees only its own Rup/Rdown and reads "dry", so the port keeps VBUS on. That is the case that corrodes the VBUS pin. TI's EVM wires the protector's FLT to GPIO2, configured as Fault_Input_Event (33), so an OVP forces Type-C error recovery and VBUS turns off. | FLT → GPIO2 (pin 7). Remove GPIO2 from the GND tie bar. Add a 100 kΩ pull-up to LDO_3V3 (FLT is open drain; datasheet allows 1.7–300 kΩ to 2.7–5.5 V). Configure GPIO2 = Fault_Input_Event. | SLVUCP9 §4.4, tables 4-5 and 4-6; TPD2S300 §6.3 |
| H2 | **Liquid-detect FET gates float at reset.** The TPS25751 GPIOs reset to Hi-Z (table 5-1) and stay that way until the configuration loads, or forever if liquid detection is not configured. LIQ_PU and LIQ_PD have no pull resistor. The AO3401A threshold can be as low as −0.5 V. TI's EVM adds a gate pull resistor on each (R105 100k PFET gate to LDO_3V3, R110 100k NFET gate to GND). | 100 kΩ LIQ_PU → LDO_3V3 and 100 kΩ LIQ_PD → GND, one pair per port (the gates are shared). C25803, JLC basic. | SLVUCP9 fig. 5-6 |
| H3 | **No tuning footprints on the BQ25756 power stage.** The EVM puts a 0 Ω in series with every gate (R8, R20, R3, R17) and every BTST line (R13, R23), plus DNP RC snubbers on SW1 and SW2 (R14/C14, R15/C15). On a dev board these are the knobs for edge-rate and EMI tuning. Since the layout is being redone, they cost almost nothing now. | Optional: 0402/0603 0 Ω on HG1/LG1/HG2/LG2 and BTST1/BTST2, plus DNP 3.3 Ω + 330 pF (or the EVM's 33 pF) snubber pads from each SW node to PGND. Both ports. | SLUUCT7 fig. 3-1 |
| H4 | **GPIO11 pin type.** The `TPS25751` symbol types GPIO11 as Output. The datasheet says GPIO, so it should be bidirectional. This is the source of ERC's two errors (Output–Output and Output–Power output on the GND tie). | Change the pin type in `tools/make_symbols.py` and update the symbol. No netlist change. | TPS25751 table 5-1 |

## Configuration, firmware and procedure

| # | Item | Setting / rule | Source |
|---|---|---|---|
| C1 | **Min Blow Fuse Voltage.** The default is 3500 mV, but the WSFB1514 heater's operating range is 10.5–19.6 V. Below 10.5 V the gauge would assert FUSE for 30 s and the fuse may not open. | Min Blow Fuse Voltage = **10500 mV**. [PACK_FUSE] = 0 (fuse on the battery side, so the stack voltage is checked). Note: CHG/DSG FET-failure permanent fails bypass this threshold (TRM §15.2.2.5), so a FET failure at a low stack voltage may heat F102 without opening it. | TRM §2 (PF actions, item 8), §15.2.2.5; WSFB1514 table |
| C2 | **COV delay versus U102.** The gauge's COV delay defaults to 2 s; U102's delay is 1–2 s (C117 0.1 µF). On a slow overcharge the gauge always acts first, because 4.25–4.3 V comes before 4.35 V. On a *step* overvoltage both see it at once and U102 can win, permanently blowing F102 for something the gauge would have fixed by opening CHG. One step case is an empty holder slot while USB or J104 drives PACK_P (see P1). | COV Delay = **1 s** (0 s is allowed). Keep COV ≤ 4.25 V (checklist). | TRM COV data flash (default 2 s); BQ2947 tCD |
| C3 | **TPS25751 GPIOs tied to GND.** GPIO0–3 and GPIO11 are strapped to GND as the datasheet asks for unused pins. Configuring any of them as an output that drives high would short it. | Leave GPIO0, 1, 3 and 11 as inputs in the configuration. GPIO2 likewise, unless H1 is done (then it is Fault_Input_Event). | TPS25751 table 5-1 |
| C4 | **Liquid-detect GPIO mapping.** TI's EVM guide contradicts itself. Table 4-5 says GPIO6 drives the NFETs and GPIO7 the PFETs. Table 4-6 sets GPIO6 = LIQUID_PMOS_CONTROL (155) and GPIO7 = LIQUID_NMOS_CONTROL (156). | Follow the event names, which match our wiring: GPIO6 (LIQ_PU) → PFETs = 155; GPIO7 (LIQ_PD) → NFETs = 156. At bring-up, confirm with a scope that LIQ_PU goes low when the pull-up should be on. | SLVUCP9 tables 4-5, 4-6 |
| C5 | **Liquid-detect thresholds.** Our Rup/Rdown (100 k / 1 M) follow the datasheet's table 9-3. TI's EVM fits 249 k for Rup. The thresholds in register 0x98 must suit the resistors actually fitted. | Keep 100 k / 1 M (datasheet). Start from the Application Customization Tool defaults. Verify with a wet-receptacle test (salt water across SBU–GND and SBU–VBUS) at bring-up. | TPS25751 table 9-3; SLVUCP9 fig. 5-6 |
| P1 | **Hot-swapping cells with power applied blows F102.** With USB charging or a bench supply on J104, PACK_P is driven at up to 16.8 V. If the CHG FET is on and one holder is empty, the empty slot sees PACK_P minus the other three cells (about 5–6 V). U102 trips after 1–2 s and the fuse opens permanently. TI's references assume a welded pack, so they don't cover this. The same thing can happen while inserting cells into a powered board. | **Rule:** unplug USB and J104 before inserting or removing any cell; insert cells with the board unpowered. Add it to `bringup-config-checklist.md` and a gauge sheet note. C2 shortens the race but should not be relied on. For deliberate bench work, fit R127 knowingly or remove R124. | Analysis; BQ2947 fig. 8-1 |
| P2 | **Sleep budget.** New loads: U102 1–2 µA from the cells (IDD, BQ2947 §6.5); 2 × TPD2S300 about 4.2 µA typical / 8 µA maximum each at 3.3 V (IVPWR + IVM). Idle total from the pack goes from about 157 µA to **about 160–163 µA**. Liquid-detection sampling adds an unknown average current. | Measure LDO_3V3 / R201 current with liquid detection on and off at bring-up. | TPD2S300 §6.5 |

## Documentation

| # | Where | Fix |
|---|---|---|
| D1 | Top-sheet revision log | Has no entry after A5. Add **A6 (2026-10-13/14, hand-review)**: second-level protection (U102 + F102), F101 deleted, D103 fitted, U202 INA190A1 JLC-placed, R405–R408 removed, liquid detection (U405/U505, Q403–Q406, R440/R540), D403/D503 removed. |
| D2 | `bringup-config-checklist.md` lines 41 and 46 | F101 → F102. SCD1 criterion: the gauge must open the FETs before F102's element is asked to break more than its 50 A rating, so keep the SCD1 delay at the minimum that avoids nuisance trips. Add C1, C2 and P1. |
| D3 | `power-budget.md` lines 61–62 | F101 → F102. Add the U102 and TPD2S300 rows (P2). |
| D4 | `circuit-description.md` line 54 and line 132 | Line 54: "before F101" → F102. Line 132 says D+/D− go to the TPS25751 for BC1.2 and SBU is unconnected. Now D+/D− are shorted by R440/R540 (passive DCP) and SBU feeds liquid detection through U405/U505. |
| D5 | README item 34 | "the Zener's 13.8 V minimum": the BZT52C15 datasheet now in the folder gives **14.25 V** minimum (15.75 V maximum) at 5 mA. The conclusion stands; the margin is larger. |
| D6 | README item 16 | Still lists C421 as 68 µF. Rev A5 made it 100 µF 35 V (C5246554); item 24 and the schematic agree. |
| D7 | `datasheets/` | ST AN5290 (minimal BOM, STM32WB) and AN5165 (STM32WB RF hardware), and the Everlight 19-217 LED datasheet, could not be fetched: st.com times out for scripted downloads, and LCSC has no PDF link for C72043. Download them by hand. Everything else is in `sources.csv`. |

## Checked and correct

**U102 BQ294700** (BQ2947 table 8-1, fig. 8-1; BQ40Z50-R2 fig. 9-11)
- RIN 1 kΩ (the calibration value), CIN 0.1 µF ladder between adjacent inputs, RVD 100 Ω, CVD 0.1 µF, CCD 0.1 µF (tCD 1–2 s). All are inside the table 8-1 ranges.
- Taps are in order: V4 = CELL_P_RAW, V3 = CELL3, V2 = CELL2, V1 = CELL1. VSS and the exposed pad go to CELL_N.
- VDD maximum is 20 V against a 17.4 V worst case.
- OUT is guaranteed ≥ 6 V at 100 µA. R124 + R125 load it with about 0.12 mA, against 4.5 mA source capability.

**Ignition network** (BQ40Z50-R2 §9.2.2.2.5, SLUA660 fig. 10)
- R124/R126 5.1 kΩ, R125 51 kΩ and C118 0.1 µF are TI's values.
- Q104 gate voltage: about 6.4 V from U102 (7 V × 51/56.1), and at most 7.9 V from the gauge (FUSE VOH maximum 8.65 V). The AO3400A is rated ±12 V.
- When U102 trips, the FUSE pin sees about 6.4 V through R126, above its 2.5 V maximum VIH, so the gauge detects the second-level trip.
- TI's Q5 is a Si1406DH (SC-70, 3.6 A). The AO3400A (5.7 A, 30 A pulsed, 30 V) is a larger part.
- The heater current returns straight to CELL_N, not through the sense shunt.
- After both fuse elements open, the heater is disconnected, so Q104 does not keep dissipating.

**F102 WSFB1514**
- 4-cell part, 15 A at 40 °C, 36 V, 50 A break.
- Pin 1 faces the cells. VC4, BAT (D101) and U102 VDD/V4 are all on CELL_P_RAW, so after a blow the gauge stays powered, keeps logging, and U102 keeps monitoring.
- Operating temperature is −10 to +65 °C. Keep it away from the Q101/Q102 heat (layout).
- The README's 0.5–1.5 A heater estimate stands; TLC's table gives no heater resistance (the 1–3 figure is Rfuse in mΩ).

**U101 BQ40Z50-R2**: all 33 pins against table 6-1.
- NC pins left open (allowed).
- PTC and PTCEN to VSS, the documented disable.
- PRES and DISP to VSS. LEDCNTLA–C and PCHG floating (allowed).
- SRP via R107 from CELL_N and SRN via R108 from GND, so charge current reads positive.
- PACK through 10 kΩ (§9.2.2.3.3).
- VC1–VC4 with 100 Ω / 0.1 µF, in the 100–300 Ω range for balancing.
- PBI 2.2 µF; SMBus 100 Ω series.
- C107/C108 and C110/C111 series pairs as in fig. 9-2.
- TI's reverse-charger FET (Q4, fig. 9-13) is not needed: PACK_P is internal to the board and J104 has the D104 series diode.
- BTP_INT (VOH 3.5 V, 1.8 V at 10 µA) drives the BSS138 (Vth 0.8–1.5 V, Fairchild datasheet) with margin.

**D103 BZT52C15**
- 14.25–15.75 V at 5 mA. It clamps Q102's gate-source below the AGM404AP1's ±20 V, and sits above the 10.5–12 V on-state DSG drive.

**TPS25751 U401/U501** (table 5-1, §6.4; EVM fig. 5-4)
- The netlist has no pins 21, 22, 24, 25, 33 or 35. This is correct: the REF0038A land pattern merges 20–22 (PPHV), 23–25 (VBUS_IN), 32–33 (VBUS) and 34–35 (PP5V) into single pads.
- Capacitors:
  - LDO_3V3: about 12 µF nominal including the new TPD2S300 caps, inside 5–25 µF.
  - CC: 330 pF, inside 200–480 pF.
  - VBUS 4.7 µF; PP5V more than 120 µF.
- I2Cc_IRQ is pulled up (it must never be grounded). The DRAIN pins connect only to each other.
- ADCIN straps (0x20 and 0x21 SafeMode) and the EEPROM at 0x50 are as in review 2.

**Liquid detection** (TPS25751 §9.2.2.2, fig. 9-8, table 9-3)
- TPD2S300 is on SBU1/SBU2, connector side on C_CCx and system side on CCx to GPIO4/5.
- Rup 100 kΩ and Rdown 1 MΩ, as table 9-3.
- FETs equivalent to TI's: AO3401A (Vth −0.5 to −1.3 V) for CSD25480F3 (−0.95 V); AO3400A (0.65–1.45 V) for CSD15380F3 (1.1 V).
- TPD2S300 supply and protection:
  - VPWR/VM on LDO_3V3, inside the 2.7–4.5 V range for low-voltage mode.
  - 1 µF 50 V 0603 on each (C15849, about 0.8 µF at 3.3 V; recommended range 0.3–1 µF).
  - VBIAS 0.1 µF 50 V.
  - OVP 5.55–6.18 V keeps GPIO4/5 under their 6 V limit.
- When unpowered, the TPD2S300's 5.1 kΩ dead-battery pull-downs appear on SBU at the connector. This is harmless.

**R440/R540**
- They short D+ to D−: a valid BC1.2 DCP signature (≤ 200 Ω).
- Nothing else hangs on D+/D−, so there is nothing for ESD to damage now that D403 is gone.

**BQ25756 U403/U503** against the EVM schematic (SLUUCT7 fig. 3-1)
- ACP/ACN and SRP/SRN: 10 Ω series, 100 nF to GND on each, 470 nF across. Ours match.
- VAC 1 µF + 100 nF. REGN and DRV_SUP 4.7 µF each.
- Pins 15 and 16 floating (the datasheet says do not ground them). Pin 17 to PGND.
- FB divider 0.1 %. VFB_REG = 0x0F gives 16.80 V (review 1).
- Only differences: H3 (tuning footprints).

**U202 INA190A1**: same pinout and enable as U201. Gain 25 gives about 18 mA full scale on the 10 Ω R_MEAS.

**ERC**: 2 errors and 8 warnings, all from the TPS25751 GPIO-to-GND ties that the datasheet requires. The errors go away with H4.

**Stock (JLC, 2026-10-14)**

| Part | LCSC | Stock | Library |
|---|---|---|---|
| BQ294700DSGR | C414622 | 1,403 | extended |
| TPD2S300YFFR | C2650411 | **200** | extended |
| WSFB1514 | C42463217 | 3,871 | extended |
| INA190A1IDDFR | C1852068 | **598** (was 1,700 on 10-13) | extended |
| BZT52C15 | C173427 | 216,935 | extended |
| AO3400A | C20917 | 771,597 | basic |
| AO3401A | C15127 | 605,521 | basic |

The dev-board build is fine. The TPD2S300 is low for production; find a second source before the production BOM.

## Status (2026-10-14): all items done

Approved in full and applied the same day.

| Item | Done |
|---|---|
| H1 | U405/U505 FLT → TPS25751 **GPIO3**, not GPIO2: GPIO3 is the end of the GPIO0–3 GND tie bar, so freeing it leaves the bar intact. Any GPIO can be Fault_Input_Event. Net SBU_FLT, R441/R541 100k to LDO_3V3 (C25803). |
| H2 | R442/R542 (LIQ_PU → LDO_3V3) and R443/R543 (LIQ_PD → GND), 100k. |
| H3 | Gate 0R R444–R447 / R544–R547: controller-side nets renamed HIDRV1/LODRV1/HIDRV2/LODRV2, FET-side nets keep HG1/LG1/HG2/LG2. BTST 0R R448/R449 / R548/R549 (nets BTSTx → BTSTx_C). DNP snubbers R450/C454, R451/C455 (and 5xx): 3.3 Ω 0805 (C16257) + 33 pF C0G (C91368). All in a new "GATE / BOOTSTRAP TUNING" block. |
| H4 | `tools/make_symbols.py` now copies KiCad's stock TPS25751D into `MonolithDev.kicad_sym` with GPIO11 bidirectional; U401/U501 use `MonolithDev:TPS25751D`. ERC: 0 errors, 8 warnings (the GPIO-to-GND ties). |
| C1–C5, P1 | `bringup-config-checklist.md` (gauge table, TPS25751 section, rules, bring-up measurements); gauge sheet note 15; port sheet notes 2, 3 and 12. |
| P2 | `power-budget.md`: U102 and TPD2S300 rows; idle about 161 µA. |
| D1 | Top-sheet revision log: A6 entry. The log was moved down so it clears the sheet index. |
| D2–D6 | Checklist, power budget, circuit description (§2 fuse and FUSE pin, §7.1 connector), README items 16 and 34. Port sheet bulk caption: 100u. |
| D7 | `datasheets/README.md` lists the documents that must be downloaded by hand. |

Also on the port sheet: the NOTES block moved under the tuning block, because its bottom anchor had pushed it into the battery-side cap row. C413's fields moved clear of the LODRV2 label.

Verified from the netlist: every new part on both ports. Layout is not done: the new parts are not placed yet (board redo).
