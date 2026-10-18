# Monolith production board

KiCad 10 project `Monolith`. **Status (2026-10-18): the dev board is skipped, so P0 is the first build** (gauge training and the dev board checks happen on P0: `docs/production/p0-bringup-and-training.md`). It is the dev board schematic (rev A8) with the dev-only parts removed. It has not been reviewed and there is no board yet.

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

`tools/layout_production.py` lays the sheets out: block moves through `DevBoard/tools/move_region.py`, then `place_fields.py` and `check_overlaps.py` (it should report 0 overlaps).

Run all four in order with KiCad's Python (make, tidy, layout, check):

```bash
"/c/Program Files/KiCad/10.0/bin/python.exe" Production/tools/make_production.py
```

```bash
"/c/Program Files/KiCad/10.0/bin/python.exe" Production/tools/tidy_production.py
```

```bash
"/c/Program Files/KiCad/10.0/bin/python.exe" Production/tools/layout_production.py
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

## Board: stack-up, outline and pour plan (2026-10-17)

`tools/make_board.py` writes the stack-up, layer table, thickness and outline into `Monolith.kicad_pcb`. It patches an existing board without touching footprints, and refuses once the board has copper. It also copies the dev board's custom DRC rules to `Monolith.kicad_dru`.

**Outline:** the board in the top cap, from `mechanical/monolith_parts.py`: **40.5 × 40.5 mm, R9.35 corners, about 1,565 mm² per side**, centred at (100, 100).

- `mechanical/monolith_bottom_pcb.dxf` is the 43.3 mm bottom end board with the 8 mm vent, not this board.
- The USB-C notches join the outline when J401/J501 are placed at the edge. Until then DRC reports 4 open-outline errors from their footprints.
- Courtyard area is 1,981 mm², so double-sided placement is required, and even then the board is tight.
- `monolith_parts.py` is out of date: it still models vertical Amphenol ports on the cap face, LEDs and a heat plate.

**Stack-up:** 6 layers, 0.8 mm, 2 oz outer / 0.5 oz inner, ENIG. Vias are filled and capped, JLC's default on 6+ layers, so via-in-pad is free. JLC publishes no 0.8 mm 6-layer stack and no net here needs controlled impedance, so the split below is a symmetric approximation. Replace it with JLC's stack at order time.

| Layer | Copper | Dielectric below | Role | Never |
|---|---|---|---|---|
| F.Cu | 70 µm | prepreg 0.10 | parts that make heat (power stages, inductors, BQ25756s), facing the gap pad and heatsink; one pour per power net in its block; GND fill elsewhere, stitched to In1 every 3–5 mm | sense pairs through power pours |
| In1.Cu | 17.5 µm | core 0.12 | **solid GND**: return for F.Cu and both hot loops | any trace, split or other-net island |
| In2.Cu | 17.5 µm | prepreg 0.15 | signals, vertical only: Kelvin pairs, cell taps, FB/ILIM, I2C; 3V3 as a local pour | high current, switch nodes |
| In3.Cu | 17.5 µm | core 0.12 | signals, horizontal only: cross-board nets, gate-drive pairs that must leave F.Cu; PP5V local pours | high current |
| In4.Cu | 17.5 µm | prepreg 0.10 | **solid GND**: return for B.Cu | any trace, split or other-net island |
| B.Cu | 70 µm | | cell side: small passives and logic (double-sided assembly); mirror of F.Cu high-current pours where no parts sit, stitched; GND fill | switch-node copper |

- **Second ground:** the gauge's VSS (CELL_N) is local fill on F.Cu/B.Cu around U101, joined to GND only through RS101. It never goes on In1/In4.
- **Antenna:** keep-out on every layer under the CC2340 antenna end, with solid ground either side at a board edge.
- **Board thickness:** 0.8 mm allows JLC's small vias (≤ 1 mm boards with ENIG), useful under the 0.4 mm-pitch TPS25751.
- **Via rules (`Monolith.kicad_pro`):**
    - default 0.45/0.3 mm, HighCurrent 0.8/0.4 mm;
    - minimum lowered to **0.35/0.2 mm** for fan-out (holes under 0.3 mm may carry a JLC surcharge: check the quote);
    - tracks 0.15/0.15 mm (JLC 2 oz multilayer); copper to edge 0.2 mm.
- **USB-C:** J401/J501 are now the **TYPE-C 16PCB0.8 IP68** (C55629727). Its land pattern is identical to the dev board's 1.6 mm version.

## Charger FETs: one Vishay SiZ240DT per leg (2026-10-17)

Each BQ25756 leg's two PGQ04N070s became one **SiZ240DT**, a 40 V dual-N half-bridge in a PowerPAIR 3×3S package with the switch node joined inside. That's two parts per port instead of four.

- **Schematic:** a new 2-unit symbol, `MonolithDev:SiZ240DT`. Unit A is Ch1 (high side: G1, D1, SW) and unit B is Ch2 (low side: G2, SW, S2). Pin 9 (SW, the S1/D2 paddle) appears in both units on one pad.
    - Q401 = leg A (old Q401 + Q407) and Q402 = leg B (old Q402 + Q408). Port 2 is the same parts as 5xx.
    - The units reuse the old symbol's pin geometry, so no wire moved.
    - `tools/siz240dt.py` holds the symbol, the footprint and the swap. `check_netlist.py` maps every old FET pin to its new unit pin and confirms the nets.
- **Footprint:** `MonolithDev:Vishay_PowerPAIR_3x3S`, from Vishay's recommended land pattern (doc 78115).
    - Pin rows: 0.65 mm pitch, 0.44 mm tall pads.
    - Paddles: D1 0.935 × 2.80 mm and SW 1.005 × 2.80 mm, 0.25 mm apart, with 2 × 3 paste windows each.
    - Smallest copper gap 0.20 mm; courtyard 4.37 × 3.8 mm.
    - Datasheet: `datasheets/siz240dt.pdf`.
- **Trade-offs against the PGQ04N070 (40 V, 10 mΩ max at 4.5 V, 14.7 nC):**
    - On-resistance is 12.25/13.30 mΩ max at 4.5 V, about 25–30 % more conduction loss.
    - Gate charge is 6.9/6.5 nC, so less load on REGN.
    - Both FETs of a leg now share one 3.3×3.3 package. Worst case (reverse 20 V 5 A from a 10 V pack), the fully-on high side dissipates ~1.8 W. That needs the paddle via arrays into the GND planes and the gap pad, and the thermal throttle limits it.
    - Measure FET temperature at bring-up. The dev board still has the old FETs.
- **Sourcing:** DigiKey/Mouser. JLC/LCSC (C3289403) has only a couple in stock, so supply them to JLC yourself, or check stock before ordering.
- **Area:** about 31 mm² less per port (one 16.6 mm² courtyard instead of two of 15.6 mm² each per leg).

## BQ25756 status pins (2026-10-17)

R421–R423 (R521–R523 on port 2), the 10 kΩ pull-ups on STAT1, STAT2 and PG, are removed.

- Those pins are open-drain status outputs. Nothing reads them on production, because the MCU gets the charger's status and faults over I2C through the TPS25751.
- U403/U503 pins 4–6 are now no-connects. An open-drain output may float.
- Set DIS_STAT_PINS = 1 in the BQ25756 configuration so they stay off.
- This also removes up to 0.33 mA per pin while the charger pulls it low.

## CC protection: TPD4S201 → TPD2S300 (2026-10-17)

U405/U505 changed from the TPD4S201 (CC + SBU, 3.5×3.5 mm QFN-20) to the **TPD2S300YFFR** (CC only, 1.4×1.4 mm WCSP-9, LCSC C2650411).

- **Why the CC lines still need a protector:** the TPS25751's CC pins survive a steady short to VBUS (26 V absolute maximum), but their ESD rating is only ±1 kV HBM / ±500 V CDM, with no IEC rating. TI's TPS25751 EVM protects them externally.
- **What the TPD2S300 provides:** CC short-to-VBUS overvoltage protection (24 V DC tolerant) and IEC 61000-4-2 ESD.
- **Why the SBU half can go:** with liquid detection gone, nothing uses SBU. The connector SBU pins are now no-connects.
- **Wiring:**
    - VPWR and VM go to LDO_3V3 (normal CC/PD mode). C452 stays on LDO_3V3.
    - VBIAS goes to C451 (0.1 µF 50 V; TI asks for ≥ 35 V).
    - FLT goes to GPIO3 through R441, as before.
- **CC capacitance:** 30–120 pF, the same as the TPD4S201, so C401/C402 (220 pF) still keep the total under the TPS25751's 480 pF.
- **Footprint:** the dev library's `TI_YFF0009_DSBGA-9_P0.4mm`. The 0.4 mm-pitch centre ball (GND) needs a via-in-pad (filled vias are free on 6 layers).
- **Code:** `tools/tpd2s300.py` holds the symbol; `make_production.py` places the part and labels its pins.
- **Totals:** 246 parts, courtyard area **1,884 mm²**.

## Board outline 45.5 mm, both USB-C ports on one side (2026-10-17)

Both ports exit the same face, for mechanical assembly: the seal flanges stick out ~1.95 mm past the board edge, so a board with ports on opposite faces can't drop into the cap.

- **Why the board grew:** one face of the 40.5 mm board had only 21.8 mm of straight edge, and each connector needs ~12.5 mm (10.2 mm notch plus shell tabs at ±5.8 mm).
- **New outline: 45.5 × 45.5 mm (+5 mm in x and y), corner radius kept at R9.35**, so each face has **26.8 mm** straight.
    - Growing the outline concentric with the tube would have kept the corner centres, and the straight edge would have stayed 21.8 mm.
    - **The cap and tube have to follow:** the board is now wider than the tube's 43.6 mm inner width, and `mechanical/monolith_parts.py` needs the new top-cap geometry.
- **Placement:** J501 (USB2) at y = 93.5 and **J401 (USB1)** at y = 106.5 on the right edge (x = 122.75), 13 mm apart, rotated 90°, locked.
    - The footprint origin is the board edge. The board outline leaves a 10.2 mm gap at each connector, and the footprint's own Edge.Cuts closes its 10.2 × 5.65 mm notch. DRC confirms the outline is closed.
    - A 2.8 mm board rib between the notches carries the neighbouring shell tabs. Those pads are 0.5 mm apart, both GND.
    - On the cap face, the two 10.25 mm seal flanges leave a ~2.75 mm wall rib between the openings.
- **Area:** about 2,000 mm² per side, up from 1,565.
- `tools/make_board.py` draws the outline (`PORTS_Y` sets the notch positions) and places the connectors.

**Found while checking DRC (not changed):**
- The via minimum in `Monolith.kicad_pro` is back at 0.45/0.3 mm. KiCad was open and rewrote the project file. Set 0.35/0.2 in Board Setup, or re-run the change with KiCad closed.
- The dev library's TPD2S300 footprint (`TI_YFF0009_DSBGA-9_P0.4mm`) puts a 0.15 mm-drill via in the centre ball pad (0.05 mm annular ring). That's inside JLC's ≤ 1 mm-board limits but trips the project rules. Decide at fan-out whether to keep it.

## P0 is the first build: training and test additions (2026-10-18)

The dev board won't be built, to save cost. P0 trains the gauge and carries the checks planned for the dev board, and a second spin follows only if needed. The procedure and the check list are in `docs/production/p0-bringup-and-training.md`.

**Gauge training access:**

- **J302: a second Tag-Connect TC2030-NL ("GAUGE") on the MCU sheet**, with no part fitted. Pinout: 1 SDA, 2 CHG_INH, 3 NRST, 4 nc, 5 GND, 6 SCL.
    - One TC2030-IDC-NL cable (+ clip) serves J301 and J302. Its 2×3 end takes the EV2400 and XDS110 jumper wires.
    - The pinout makes a wrong plug harmless: the SWD probe would drive only CHG_INH and NRST.
    - The gauge pogo pads TP110–TP112 are gone; J302 replaces them.
- **J113/J114:** PACK_P/GND 20 AWG wire pads for the learning-cycle load (~C/5 ≈ 1.2 A). The current runs through the protection FETs and RS101, so the gauge measures it.
- **WAKE:** R118 4.7 kΩ (0402, C25900) from CELL_P to TP113. Bridging TP113 to TP106 wakes the gauge, in case wake-on-USB fails.
- **With the MCU held in reset:** ground J302 pin 2 (CHG_INH) to keep charging enabled while BQStudio owns the bus.

**Hedges for the decisions that were waiting on the dev board:**

- **R444–R447** (and 5xx) are back as fitted **0 Ω 0402 gate links** (C17168). If SW1/SW2 ring, swap in 2.2–10 Ω without a respin.
- **R450/C454 and R451/C455** are back as **DNP 0402 RC snubbers** (3.3 Ω C270612, 33 pF C0G C1562).

**Probe pads (1.0 mm, `TestPoint_Pad_D1.0mm`):**

- Per port: TP401 VBUS, TP402 PPHV, TP403 PP5V, TP404 REGN, TP405 SW1, TP406 SW2, TP412 GND (5xx on port 2).
- Shared: TP301 3V3, TP106 PACK_P, TP109 GND.
- Every 1.5 mm pad is now 1.0 mm.

**Totals:** 276 parts, courtyard area 1,899 mm². The netlist check passes, with the new WAKE net and J302 checked. ERC shows only the known warnings.

## Next

1. **Review P0**, mainly gauge note 10. With no wake button, the gauge has to come out of SHUTDOWN when USB brings up PACK_P, through the TPS25751 dead-battery sink and the BQ25756 charging with 3V3 down. Confirm this on the dev board.
2. **Cap cut still on hold** (`docs/devboard/cap-reduction-sims-2026-10-17.md`):
    - C427/C527 (USB-side MLCC): only if dev board bring-up shows the polymer stays cool at 20 V 5 A reverse from a low pack (it reaches 85 % of its rating), or if firmware derates that case.
3. **Place the board**, double-sided, inside the 40.5 mm outline. Then update `mechanical/monolith_parts.py` to the real connector, port and board geometry.
