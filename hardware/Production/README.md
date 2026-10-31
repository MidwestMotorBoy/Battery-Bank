# Monolith production board

KiCad 10 project `Monolith`: the P0 board, the design of record. Since 2026-10-30 the routed board is on `master` (the `Production` and `Layout-P0` branches were merged in).

**Status (2026-10-29):** the dev board was skipped on 2026-10-18, so P0 is the first build (gauge training and the dev board checks happen on P0: `docs/production/p0-bringup-and-training.md`). The schematic is the dev board's (rev A8) with the dev-only parts removed, plus the P0 changes below. Footprint placement was finished on 2026-10-28 and routing on 2026-10-30 (`8fd8b74`); the routed board is in review ([`docs/reviews/2026-10-30-routed-board/`](../../docs/reviews/2026-10-30-routed-board/README.md) lists what to fix before fab), and nothing has been ordered.

The current design is in `docs/spec.md`, which wins where this file disagrees; its *P0 board changes still to apply* list is the to-do list. The sections below are a dated design log. Sections that a later decision replaced say so and are kept as history. In short, as of 2026-10-29:

- **Cells:** four BAK N21700CX-65E (6500 mAh) in 4S1P, 14.0 V nominal, 91 Wh (since 2026-10-23; the FEB 21700G section below is history).
- **Enclosure:** the MJF PA12 cup, with no vent since 2026-10-28 (the side tray, its aluminium cover and the top-cap tube are retired; their outputs were removed on 2026-10-29 and are in git history at `5cf521e`).
- **Loss cuts:** Q101/Q102 BSC007N04LS6, a 9 V gate drive per port (U406/U506), L401/L501 XGL7030-332 at 500 kHz.
- **Front-cell NTCs:** SMD TH101 / TH104 on B.Cu (since 2026-10-28; they replace the J102 / J107 wire pads).
- **Charge ceiling:** R413/R513 are to become 0 Ω (decided 2026-10-23, register-only limit); the schematic still has 11.8k.

## Tools

All in `tools/`. Run them from the repo root as `hardware/Production/tools/<name>.py`, with KiCad's Python unless the script's docstring says any Python 3 will do.

| Script | What it does |
|---|---|
| `make_production.py` | Builds the production schematic from the dev board's (see below); holds the part swaps (`DOWNSIZE`, loss cuts, P0 pads). It overwrites the sheets, which have been edited in KiCad since (2026-10-28), so don't re-run it blindly |
| `tidy_production.py`, `layout_production.py` | Drawing tidy and block layout after `make_production.py` (no electrical change) |
| `check_netlist.py` | Compares the production netlist with the dev board's |
| `schlib.py` | Schematic text helpers used by the three above |
| `siz240dt.py`, `tpd6s300.py`, `tps7a4101.py` | Symbol, footprint and wiring for the SiZ240DT, TPD6S300 and TPS7A4101 (imported by `make_production.py`) |
| `make_board.py` | Board stack-up and outline; `--mech` places and locks the wire holes, peg holes and front-cell NTCs; `--keepouts` redraws the `KO_*` rule areas (board closed in KiCad) |
| `make_3d_models.py`, `step_mesh.py` | Writes the STEP models in `3dmodels/` (pure Python); the SiZ240DT and TPD6S300 models start from the EasyEDA meshes in `3dmodels/source/`, so keep those |
| `pack_bus_sims.py`, `low_profile_sims.py` | Bulk-capacitor studies (reuse `hardware/DevBoard/tools/cap_sims.py`) |
| `jlc.py`, `jlc_datasheet.py` | JLC part search, and a datasheet download through a part's JLC page |

## How P0 was made

`tools/make_production.py` (re-runnable) copies the dev board's sheets, libraries and project file from `hardware/DevBoard/` and edits them as follows:

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

`tools/layout_production.py` lays the sheets out: block moves through `hardware/DevBoard/tools/move_region.py`, then `place_fields.py` and `check_overlaps.py` (it should report 0 overlaps).

Run all four in order with KiCad's Python (make, tidy, layout, check):

```bash
"/c/Program Files/KiCad/10.0/bin/python.exe" hardware/Production/tools/make_production.py
```

```bash
"/c/Program Files/KiCad/10.0/bin/python.exe" hardware/Production/tools/tidy_production.py
```

```bash
"/c/Program Files/KiCad/10.0/bin/python.exe" hardware/Production/tools/layout_production.py
```

```bash
"/c/Program Files/KiCad/10.0/bin/python.exe" hardware/Production/tools/check_netlist.py
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
    - J108 PACK− (CELL_N) and J112 PACK+ (CELL_P_RAW): 18 AWG wires (TE 100G0111-1.00-0, up to 1.8 mm OD) in Ø1.5 mm plated holes (since 2026-10-24, *Pack wire holes* below);
    - J109–J111 (CELL1–CELL3) and J115 / J116 (1N / 4P Kelvin): 28 AWG sense wires (TE 55A0111-28-9) in Ø0.8 mm plated holes (since 2026-10-24, *Pack wire holes* below);
    - J105 / J106: back-cell (C2 / C3) NTC wire pads. The front cells' NTCs are SMD since 2026-10-28: TH101 (C1, TS1) and TH104 (C4, TS4), 0402s on B.Cu at |y| 15.5 mm, z 29 mm (KiCad (84.5, 112.48) / (115.5, 112.48), 90°, locked; `sb_ntc_smd()`), in a notch at the outer edge of each gap-filler keep-out, under the gel (`research_notes/Pack thermal BAK 65E/smd-ntc.md`). They replace J102 / J107 and the wired beads.
- **Gauge access:** TP110 SMBC, TP111 SMBD, TP112 GND, 1.5 mm pogo pads in a row (replace the EV2400 header J103). Later replaced by the J302 Tag-Connect (see below).
- **SWD:** J301 is a Tag-Connect TC2030-NL footprint (VCC, SWDIO, NRST, SWCLK, GND; SWO not connected). Use an XDS110 with a TC2030-CTX cable.
- **Factory test pads (1.5 mm):** TP106 PACK_P, TP109 GND, TP301 3V3, TP401/TP501 VBUS.

## Loss cuts 1–3 (adopted 2026-10-23, drawn 2026-10-28)

The board-side loss cuts from `docs/spec.md` (*Decided: the four loss cuts*). Port 1 references; port 2 is 5xx.

| Cut | Parts | Change |
|---|---|---|
| 1. Protection FETs | Q101, Q102 | AGM404AP1 (3.3 × 3.3) → Infineon BSC007N04LS6 (LCSC C534274), 0.70 mΩ, TDSON-8 FL 5 × 6. Footprint `Infineon_PG-TDSON-8_6.15x5.15mm_D5-8`: KiCad's PG-TDSON-8 with the drain leads numbered 5–8 to match the symbol (`tdson_footprint()`). Check it against the datasheet's footprint drawing before fab |
| 2. 9 V gate drive | U406, C457, C458, R452–R455, D410, D411, Q409 | See below |
| 3. Inductor + 500 kHz | L401, R412 | Coilcraft XGL7030-332MEC 3.3 µH on the APS0730 pads (consigned); R412 40.2k → 49.9k (598 → ~500 kHz). R412's LCSC code (0201WMF4992TEE) is still to look up |

**9 V gate drive, per port** (`add_gate_drive()`, symbol in `tools/tps7a4101.py`), in the free area right of the BQ25756 controller block:

- U406 TPS7A4101DGNR (LCSC C111739, HVSSOP-8 PowerPAD) runs from PACK_P. C457 1 µF 50 V in, C458 22 µF 25 V 0805 out (the LDO needs ≥ 4.7 µF; about 8 µF is left at 9.6 V). R452 40.2k / R453 5.6k set 1.173 × (1 + 40.2/5.6) ≈ 9.6 V.
- D411 (LRB520S-40) ORs it onto DRV_SUP at about 9.3 V. D410 (LRB520S-40) replaces R420 (10 Ω REGN → DRV_SUP), so with U406 off DRV_SUP is REGN − VF, TI's standard drive, and a dead pack still charges. The output diode is needed because the TPS7A41's OUT may not sit more than 0.3 V above IN.
- EN: R454 (100k) from REGN, pulled low by Q409 (AO3400A) unless TPS25751 GPIO6 (net DRV9_OFF) is low. R455 (100k) pulls Q409's gate up to the port's LDO_3V3, so GPIO6 Hi-Z (reset, no configuration) or high means 9 V off. GPIO6 leaves the unused-GPIO GND rail (`free_gpio6()`); its wire crosses the rail without a junction.
- Firmware: GPIO6 as an output with initial value high; `GPsl` turns the 9 V on, `GPsh` off. On only while that converter switches, for contracts ≥ 45 W and with PACK_P ≥ 10 V (the TPS7A41's EN may not sit more than 0.3 V above IN either). With REGN down, EN is low, so DRV_SUP is never driven while the BQ25756 is off (bq25756.pdf 6.3.3.2).
- C411 4.7 µF 10 V 0402 → 4.7 µF 25 V 0805 (CL21A475KAQNNNE, C1779).

The committed sheets were updated by calling these functions (`edit_symbols`, `add_gate_drive`, `tdson_footprint`, tidy's notes) on the existing files, because KiCad can't be installed in the cloud session that made the change; a full `make_production.py` run produces the same result. Connectivity was checked by a script that compares every pin's net before and after (only the intended changes); **ERC, check_netlist.py and Update PCB from Schematic are still to run in KiCad.**

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

- **Bulk polymers C421/C432.** No smaller 100 µF 35 V polymer is stocked. The only smaller 25 V option is a polymer tantalum, rated for up to 250 µA leakage, which would wreck the sleep budget on PACK_P. (Superseded on 2026-10-18 by *Low-profile bulk*.)
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
- **USB sides:** these can't share bulk, because each port has its own VBUS/PPHV, so C421/C521 stay. C427 is still on hold for bring-up. (Both superseded on 2026-10-18 by *Low-profile bulk*: C208 became six MLCCs, C421 became two polymer tantalums, and C427 is now required.)

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

`tools/make_board.py` writes the stack-up, layer table, thickness and outline into `Monolith.kicad_pcb`. It patches an existing board without touching footprints. Once the board has copper it refuses, unless `--keep-copper` is passed, which leaves every trace where it is. It also copies the dev board's custom DRC rules to `Monolith.kicad_dru`.

**Outline:** since 2026-10-18, the side board of the one-piece tray. The details are in *Side outline and 1.6 mm board* below. The 40.5 mm and then 45.5 mm top-cap outlines that came before it are kept below as history.

- `monolith_bottom_pcb.dxf` (removed 2026-10-29, in git at `5cf521e`) was the old 43.3 mm bottom end board with the 8 mm vent, not this board.

**Stack-up:** 6 layers, **1.6 mm** (2026-10-18, for cost; it was 0.8 mm), 2 oz outer / 0.5 oz inner, ENIG. Vias are filled and capped, JLC's default on 6+ layers, so via-in-pad is free. No net here needs controlled impedance, so the split below is a symmetric approximation. Replace it with JLC's stack at order time.

| Layer | Copper | Dielectric below | Role | Never |
|---|---|---|---|---|
| F.Cu | 70 µm | prepreg 0.20 | outer face: parts that make heat (power stages, inductors, BQ25756s), facing the gap pad and the aluminium cover; one pour per power net in its block; GND fill elsewhere, stitched to In1 every 3–5 mm | sense pairs through power pours |
| In1.Cu | 17.5 µm | core 0.30 | **solid GND**: return for F.Cu and both hot loops | any trace, split or other-net island |
| In2.Cu | 17.5 µm | prepreg 0.39 | signals, vertical only: Kelvin pairs, cell taps, FB/ILIM, I2C; 3V3 as a local pour | high current, switch nodes |
| In3.Cu | 17.5 µm | core 0.30 | signals, horizontal only: cross-board nets, gate-drive pairs that must leave F.Cu; PP5V local pours | high current |
| In4.Cu | 17.5 µm | prepreg 0.20 | **solid GND**: return for B.Cu | any trace, split or other-net island |
| B.Cu | 70 µm | | cell side, against the insulator: only low parts in the free strips (see the side outline section), ideally none; mirror of F.Cu high-current pours where no parts sit, stitched; GND fill | switch-node copper |

- **Second ground:** the gauge's VSS (CELL_N) is local fill on F.Cu/B.Cu around U101, joined to GND only through RS101. It never goes on In1/In4.
- **Antenna:** keep-out on every layer under the CC2340 antenna end, with solid ground either side at a board edge.
- **Board thickness:** 1.6 mm, for cost. JLC's multilayer minimum at 1.6 mm is a 0.15 mm hole on a 0.25 mm via, with a surcharge below a 0.2 mm hole or under a 0.45 mm via. The 0.1 mm / 0.2 mm via option needs a board of 1 mm or less, so it's gone. The project minimum (0.35/0.2 mm) is still inside JLC's limits (the TPD2S300's 0.15 mm via-in-pad is gone: U405/U505 are TPD6S300s since 2026-10-18) ([JLC capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), checked 2026-10-18).
- **Via rules (`Monolith.kicad_pro`):**
    - default 0.45/0.3 mm, HighCurrent 0.8/0.4 mm;
    - minimum lowered to **0.35/0.2 mm** for fan-out (holes under 0.3 mm may carry a JLC surcharge: check the quote);
    - tracks 0.15/0.15 mm (JLC 2 oz multilayer); copper to edge 0.2 mm.
- **USB-C:** J401/J501 are the **TYPE-C 16PCB1.6 IP68** (C55629729), the 1.6 mm board version, since 2026-10-18 (before that, the 16PCB0.8, C55629727). The land pattern is identical, so only the footprint name and part fields changed, in the schematic, on the board and in `tools/make_production.py`.

## Side outline and 1.6 mm board (2026-10-18)

The board moved from the top cap to one side of the cells, in a one-piece printed tray (`hardware/mechanical/`, see the root README). The tray was replaced by the cup on 2026-10-21 (*Enclosure: the cup* below); the outline stayed. The board thickness went to 1.6 mm, for cost.

- **Outline:** 43.2 × 74.35 mm, about 3,164 mm² per side.
    - The bottom corners are notched 5.0 × 4.8 mm around the cover-screw bosses (on the wedge since 2026-10-21; they were tray pillars).
    - The outline comes from `hardware/mechanical/monolith_shell.py` (`sb_*`), which `tools/make_board.py` imports, so the tray and the board can't drift apart. The same outline is in `hardware/mechanical/monolith_side_pcb.dxf`.
    - It is centred at (100, 100). KiCad x is across the pack (left = the C1 / PACK- side), and KiCad y runs down the pack, with the port end at the top.
- **Ports:** J501 (USB2) at x = 93.5 and J401 (USB1) at x = 106.5, on the top edge (y = 62.82), rotated 180°, locked. The outline leaves the two 10.2 mm notch gaps.
- **Faces:**
    - F.Cu faces the aluminium cover through a gap pad: up to 3.2 mm of part height (the APS0730 inductor is 3.1 mm).
    - B.Cu faces the cells through a 0.3 mm insulator. Along the two cell tangent lines (8–13 mm from centre) there is only 0.3–0.8 mm, which the insulator mostly fills. There are 3 mm or more within 4 mm of centre and beyond 18 mm from it.
- **Pack connections** become nickel-tab pads instead of the 16 AWG holes:
    - PACK- (C1 side) and PACK+ (C4 side) at the bottom edge, within 16 mm of centre, clear of the notches;
    - CELL2 at the bottom; CELL1 and CELL3 at the top.
    - The cell order and the assembly steps are in the assembly doc.
- **Vent:** keep a Ø7 mm circle free of tall parts and gap pad, centred 12 mm above the tray bottom (shown on the DXF's `VENT_KEEPOUT` layer). Gone since 2026-10-28: the cup has no vent.
- **Still to do:**
    - Placement: every part except J401/J501 still sits where it was.
    - Four hand-drawn VBUS traces near the old J401 position were kept as they were (`--keep-copper`). They now dangle (3 DRC warnings).
    - DRC otherwise shows only the known items: the pending Update PCB from Schematic for the P0 additions. (The TPD2S300 via-in-pad errors went with the TPD6S300 swap.) There are no outline errors.

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

## CC protection: TPD2S300 → TPD6S300 (2026-10-18)

U405/U505 changed from the TPD2S300YFFR (WCSP-9) to the **TPD6S300RUKR** (WQFN-20, 3 × 3 mm, 0.4 mm pitch, LCSC C2649810, $0.51, 17,307 in stock on 2026-10-18).

- **Why:** the TPD2S300's centre ball (GND) is boxed in by the other eight, so it needed a 0.15 mm via-in-pad. That's under JLC's no-surcharge hole size and failed the project's 0.3 mm minimum drill and 0.075 mm minimum annular ring (4 DRC errors). The TPD6S300 has perimeter pads plus an exposed pad, so it fans out with standard vias.
- **Same job on CC:** short-to-VBUS OVP (24 V DC tolerant), IEC 61000-4-2 ±8 kV contact, FLT open drain. It is the TPD4S201's sibling in TI's port-protector family (similar pinout).
- **Wiring** (`tools/tpd6s300.py`):
    - VPWR → LDO_3V3 with C452 (the part has no VM pin);
    - VBIAS → C451 (0.1 µF 50 V);
    - FLT → SBU_FLT, then R441 → GPIO3, as before;
    - RPD_G1 → C_CC1 and RPD_G2 → C_CC2. This gives the dead-battery Rd while unpowered, which the TPD2S300 had built in.
    - GND pins and the exposed pad go to GND. Pins 16/17 (N.C.) also go to GND, as the datasheet asks.
    - The SBU channels (C_SBU1/2, SBU1/2) and the USB2 ESD pins D1/D2 are no-connects.
- **CC capacitance:** 60–120 pF (TPD2S300: 30–120 pF). The maximum is the same, so C401/C402 (220 pF) still keep the total under the TPS25751's 480 pF.
- **Footprint:** `MonolithDev:TI_RUK0020B_WQFN-20-1EP_3x3mm_P0.4mm_EP1.7x1.7mm_Via0.3`. It is KiCad's RUK0020B land pattern with four 0.3 / 0.5 mm GND vias in the exposed pad (KiCad's own thermal-via version uses 0.2 mm drills). `make_production.py` writes it.
- **Board:** both footprints were swapped in place, keeping their position, rotation and schematic link. U405 moved 0.65 mm down (+y) to clear U401's courtyard. DRC shows nothing on U405/U505 except unrouted ratsnest.
- **Cost of the swap:**
    - **Quiescent current:** IVPWR is 90 µA typical / 135 µA maximum per part, against 3.2 µA for the TPD2S300. That's about +175 µA on the two LDO_3V3 rails, the same order as the TPD4S201's 224 µA.
    - **Area:** 3 × 3 mm instead of 1.4 × 1.4 mm.
- **Code:** `tools/tpd6s300.py` holds the symbol, the footprint and the pin nets; `make_production.py` places the part. `tools/tpd2s300.py` was removed (it is in git history).

## CC protection: TPD4S201 → TPD2S300 (2026-10-17)

_Superseded on 2026-10-18 by the TPD6S300 above (via-in-pad); kept as history._

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

_Superseded on 2026-10-18 by the side outline below; kept as history._

Both ports exit the same face, for mechanical assembly: the seal flanges stick out ~1.95 mm past the board edge, so a board with ports on opposite faces can't drop into the cap.

- **Why the board grew:** one face of the 40.5 mm board had only 21.8 mm of straight edge, and each connector needs ~12.5 mm (10.2 mm notch plus shell tabs at ±5.8 mm).
- **New outline: 45.5 × 45.5 mm (+5 mm in x and y), corner radius kept at R9.35**, so each face has **26.8 mm** straight.
    - Growing the outline concentric with the tube would have kept the corner centres, and the straight edge would have stayed 21.8 mm.
    - **The cap and tube have to follow:** the board is now wider than the tube's 43.6 mm inner width, and `hardware/mechanical/monolith_parts.py` needs the new top-cap geometry.
- **Placement:** J501 (USB2) at y = 93.5 and **J401 (USB1)** at y = 106.5 on the right edge (x = 122.75), 13 mm apart, rotated 90°, locked.
    - The footprint origin is the board edge. The board outline leaves a 10.2 mm gap at each connector, and the footprint's own Edge.Cuts closes its 10.2 × 5.65 mm notch. DRC confirms the outline is closed.
    - A 2.8 mm board rib between the notches carries the neighbouring shell tabs. Those pads are 0.5 mm apart, both GND.
    - On the cap face, the two 10.25 mm seal flanges leave a ~2.75 mm wall rib between the openings.
- **Area:** about 2,000 mm² per side, up from 1,565.
- `tools/make_board.py` draws the outline (`PORTS_Y` sets the notch positions) and places the connectors.

**Found while checking DRC (not changed):**
- The via minimum in `Monolith.kicad_pro` is back at 0.45/0.3 mm. KiCad was open and rewrote the project file. Set 0.35/0.2 in Board Setup, or re-run the change with KiCad closed.
- The dev library's TPD2S300 footprint (`TI_YFF0009_DSBGA-9_P0.4mm`) puts a 0.15 mm-drill via in the centre ball pad (0.05 mm annular ring). That's inside JLC's ≤ 1 mm-board limits but trips the project rules. Decide at fan-out whether to keep it. (Resolved 2026-10-18: U405/U505 are TPD6S300s.)

## P0 is the first build: training and test additions (2026-10-18)

The dev board won't be built, to save cost. P0 trains the gauge and carries the checks planned for the dev board, and a second spin follows only if needed. The procedure and the check list are in `docs/production/p0-bringup-and-training.md`.

**Gauge training access:**

- **J302: a second Tag-Connect TC2030-NL ("GAUGE") on the MCU sheet**, with no part fitted. Pinout: 1 SDA, 2 CHG_INH, 3 NRST, 4 nc, 5 GND, 6 SCL.
    - One TC2030-IDC-NL cable (+ clip) serves J301 and J302. Its 2×3 end takes the EV2400 and XDS110 jumper wires.
    - The pinout makes a wrong plug harmless: the SWD probe would drive only CHG_INH and NRST.
    - The gauge pogo pads TP110–TP112 are gone; J302 replaces them.
- **J113/J114:** PACK_P/GND 20 AWG wire pads for the learning-cycle load (~C/5 of 6.5 Ah ≈ 1.3 A). The current runs through the protection FETs and RS101, so the gauge measures it.
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

## Gauge choice: BQ40Z50-R2 kept, U102 kept (2026-10-18)

**BQ41Z50 considered and not adopted:**

- **Not a drop-in.** Its pinout and package differ (RSN WQFN-32), so it would need a new symbol and footprint and a gauge sheet redrawn and re-reviewed against TI's reference design.
- **Cost and stock.** $7.44 with 17 in stock at JLC, against $1.96 with ~9,700 for the BQ40Z50-R2.
- **Same training.** It still needs chemistry selection, calibration, a learning cycle and a golden image.
- **What it would gain:** better state of charge under dynamic load, max-power reporting, 25 mA balancing and 1 MHz SMBus. Worth looking at for a later spin.

**Second-level protection stays as it is.**

- Both gauges have the same "software 1st- and 2nd-level protection" plus a FUSE pin, running in the same chip. That gives no independent layer.
- TI's BQ41Z50 reference design still pairs it with an external protector (BQ296103).
- So U102 (BQ294700) stays as the independent hardware second level that blows F102 through Q104, as decided on 2026-10-13.

## Low-profile bulk (2026-10-18)

The 6.3 × 7.7 mm cans (C421/C521 polymer, C208 hybrid) stood 7.7 mm tall. Every bulk cap is now no taller than the inductors (APS0730M2R2F, 3.1 mm max). Checked with `tools/low_profile_sims.py`, which runs the same ripple, part-stress and damping models as `cap_sims.py` and `pack_bus_sims.py`.

**Why two different fixes.** Low-profile polymer chips (Panasonic SP-Cap, CDE MPD, KEMET T521, CCTC CA55) are rated for 0.1–0.3 CV of leakage: 165 µA for a CA55 47 µF 35 V and about 250 µA for a 33 µF 25 V SP-Cap. That doesn't matter on AC_SNS_N, which is dead in sleep. It rules them out on PACK_P, which is always live and has a ~150 µA sleep budget. So the USB side uses polymer tantalum and PACK_P uses MLCCs only.

**USB side, per port** (BQ25756 C_IN ≥ 80 µF after derating, at 20 V):

| Option | Effective C (worst, 20 V) | Typ. | Worst part | Ripple | Damping | Area | Height | Polymer cost |
|---|---|---|---|---|---|---|---|---|
| Before: 4 × 22 µF 1210 + 100 µF can | 104.5 µF | 134 µF | 65 % (can) | 162 mV | 19.7 dB | 125 mm² | 7.7 mm | |
| 4 × 22 µF + 2 × T521D 33 µF | 77.3 µF (low) | 100 µF | 40 % | 150 mV | 17.1 dB | 143 mm² | 3.1 mm | $6.40 |
| 5 × 22 µF + 2 × T521D (first pass) | 83.4 µF | 109 µF | 33 % | 123 mV | 17.8 dB | 158 mm² | 3.1 mm | $6.40 |
| 4 × 22 µF + 3 × T521D (second pass) | 103.7 µF | 133 µF | 38 % | 139 mV | 18.8 dB | 185 mm² | 3.1 mm | $9.60 |
| 4 × 22 µF + 3 × CA45 33 µF (MnO₂) | 103.7 µF | 133 µF | 43 % | 162 mV | 18.7 dB | 185 mm² | 2.8 mm | $2.14 |
| Applied 10-18 to 10-31: 4 × 22 µF + 2 × CA55 47 µF | 99.7 µF | 128 µF | 43 % | 160 mV | 20.0 dB | 143 mm² | 2.8 mm | $2.97 |
| 4 × 22 µF + 3 × CA55 47 µF | 137.3 µF | 175 µF | 42 % | 157 mV | 21.0 dB | 185 mm² | 2.8 mm | $4.46 |
| **Applied since 2026-10-31: 4 × 22 µF + 2 × T593V 68 µF** | **133.3 µF** | **170 µF** | **41 %** | **154 mV** | **20.9 dB** | **143 mm²** | **2.0 mm** | **$4.88** |

- **C421/C521 and C456/C556 (2026-10-31, Logan):** KEMET **T593V686M035APE070**. 68 µF 35 V polymer tantalum (T593, the high-humidity series: 85 °C / 85 % RH for 1000 h), 70 mΩ, 1.69 A rms at 85 °C (2.42 A at 45 °C), −55 to 105 °C, 238 µA leakage (0.1 CV, still harmless on AC_SNS_N). V case, 7343-20: 7.3 × 4.3 mm, 2.0 mm max, with the same terminals as the D case, so the footprint stays `CP_EIA-7343-31_Kemet-D` and nothing moves on the board. Being 2.0 mm tall, C456 now clears the 2.3 mm B.Cu height zone it used to stick into. `low_profile_sims.py` option C4: 133 µF worst case at 20 V (+34 %), 154 mV ripple, 20.9 dB damping, worst part still a 1210 at 41 %; PPHV inrush about 170 µF × 0.47 V/ms = 0.08 A. Mouser, $2.44 at 10+, 94 in stock on 2026-10-31 with a 52-week factory lead (not at LCSC). `tools/make_3d_models.py` now maps the D footprint to KiCad's 2.0 mm Kemet-V model; re-run it to update the board's 3D view.
- **Before 2026-10-31:** CCTC CA55-D035M476T (LCSC C2761440, 3,658 in stock, $1.49). 47 µF 35 V polymer tantalum, 150 mΩ, 1.225 A rms at 100 kHz. 7343-28 case, 2.8 mm max, on the standard 7343 D land pattern. Polymer tantalum needs only 20 % voltage derating; at 20 V on a 35 V part it runs at 57 %. C456 sits on AC_SNS_N next to C430.
- **Why not the CA45-D035K336T.** It's $0.71 and it simulates fine, but it is an MnO₂ solid tantalum. Those fail short and can ignite. Makers want ≥ 50 % voltage derating, more on a low-impedance input. This one would run at 57 % on a USB input that sees hot-plug surges from a 5 A charger, and in reverse mode the pack feeds it through the converter. The CA55 is the same maker's polymer series, which avoids both problems.
- **T521D history:** the first pass used two KEMET T521D336M035ATE065 plus a fifth 22 µF 1210 (C457). The second pass used three T521Ds. Both are replaced by the CA55 pair: about $6.60 cheaper per port, one part fewer, 42 mm² smaller, with better damping.
- **C427/C527** leaves the cut list: the bank is designed with it.
- **PPHV inrush** (sheet note 9): about 128 µF typical, against about 134 µF before. With soft-start at setting 0 that is still only about 0.06 A.
- **Fallback:** CDE MPD330M1VD28040R (33 µF 35 V polymer aluminium, 2.8 mm). It would need three per port and has low stock, or KEMET T521D as above.

**PACK_P bus** (≥ 80 µF at 16.8 V; each charger sees the whole bus through its RBAT):

| Option | Effective C (worst, 16.8 V) | Worst part | Ripple | Damping | Area | Height |
|---|---|---|---|---|---|---|
| Before: 2 × 22 µF 1206 + 10 µF 50 V per port, hybrid can shared | 99.2 µF | 44 % | 232 mV | 20.2 dB | 130 mm² | 7.7 mm |
| 47 µF 25 V 1210s (2 + 10 µF per port, 6 shared) | 66.5 µF (low) | 32 % | 121 mV | 19.8 dB | 167 mm² | 2.7 mm |
| 3 × 22 µF 35 V 1210 per port, 5 shared | 79.2 µF (low) | 26 % | 76 mV | 19.6 dB | 161 mm² | 2.7 mm |
| **Applied: 3 × 22 µF 35 V 1210 per port, 6 shared** | **86.4 µF** | **26 %** | **78 mV** | **19.9 dB** | **175 mm²** | **2.7 mm** |
| 4 × 22 µF 35 V 1210 per port, 4 shared | 86.4 µF | 17 % | 52 mV | 19.9 dB | 175 mm² | 2.7 mm |

- **Why 22 µF 35 V over 47 µF 25 V.** At 16.8 V a 22 µF 35 V 1210 keeps about 10 µF; a 47 µF 25 V 1210 keeps about 8 µF.
- **Per port:** C431/C434 (22 µF 25 V 1206) and C444 (TPS62933 input, 10 µF 50 V 1206) become GMK325BJ226MM-P 22 µF 35 V 1210s. That is the same part as the USB-side MLCCs. C444 now keeps about 10 µF at 16.8 V instead of about 4 µF.
- **Shared:** C208 (EEH-ZA1E101XP hybrid) becomes C208–C213, six GMK325BJ226MM-P on the 3V3 Rail sheet. Place them between the two power stages, beside both RBAT pads, as before.
- **Leakage:** effectively zero.
- **Damping:** still about 20 dB; the pack's own resistance damps the bus.

**Cost of the change:** about +81 mm² of courtyard (+18 mm² per USB side, +45 mm² on PACK_P) and 7 more parts (276 → 283 in the schematic). At JLC small-quantity prices it adds roughly +$8 per board: four CA55s at $1.49 and the extra 1210s. In return, no part rises above 3.1 mm.

**PCB:** run Update PCB from Schematic. The board needs new footprints for C421/C521 (7343 D), C431/C434/C444 and C531/C534/C544 (1210), and C208 (1210), plus seven new parts: C209–C213 and C456/C556 (7343 D).

## Board mounting: carrier pegs (2026-10-21; the cover standoffs are retired)

The board has **no screw holes**. In the cup it rides on the PA12 carrier (`hardware/mechanical/monolith_cup.py`):
- **four pegs** (Ø2.0 mm) on the carrier rails pass through four NPTH slots and stand 0.6 mm proud of F.Cu;
- the rails bear on B.Cu along the front cells' tangents;
- the top edge stops on the top wall, and the USB-C bodies sit in their seal bores.

- **Schematic:** H101–H104 on the 3V3 Rail sheet, now `Mechanical:MountingHole` (no pins, no net, not in the BOM) with the generated footprint `MonolithDev:Peg_NPTH_Slot2.6x2.2mm` (2.6 × 2.2 mm NPTH slot, long along KiCad x; courtyard 0.5 mm round it on both faces). Until 2026-10-24 these were Ø2.2 holes; the slot gives ±0.3 mm float across the board so the USB-C seal bores centre the ports, and keeps ±0.1 mm along it. Same references as the old Würth standoffs, so Update PCB swaps the footprints in place.
- **Positions:** `CUP_PEGS` in `hardware/mechanical/monolith_shell.py`. In KiCad, H101 (91.40, 127.48), H102 (91.40, 73.48), H103 (108.60, 127.48), H104 (108.60, 73.48).
    - H104 lands on U405 and C452 as placed today: move them.
- **Placing them:** run Update PCB from Schematic, save and close the board, then run `"C:/Program Files/KiCad/10.0/bin/python.exe" -I hardware/Production/tools/make_board.py --mech`. It moves only the peg holes, the seven pack wire holes and (since 2026-10-28) the front-cell NTCs TH101 / TH104 to their positions and locks them.

## Pack wire holes and the 1N / 4P Kelvin nets (2026-10-21; all wires 2026-10-24)

Every pack connection is a wire (Logan, 2026-10-24): **five 28 AWG sense wires** (TE 55A0111-28-9 since 2026-10-31) (CELL1–CELL3 and the 1N / 4P Kelvin leads) in Ø0.8 mm plated holes, and **two 18 AWG PACK power wires** (TE 100G0111-1.00-0 since 2026-10-31; the footprint names still say PTFE, from the earlier wire) in Ø1.5 mm plated holes (`docs/production/p0-assembly.md`). `tools/make_production.py` generates both from the model: the sense pads from `sb_slots()` as `MonolithDev:SolderWire-28AWG_PTFE_1x01_D0.8mm_Pad<L>x1.4mm` (a round Ø0.8 hole in the old slot's oval pad, so the routed copper is unchanged; no paste), the PACK holes from `sb_pack_holes()` as `MonolithDev:SolderWire-18AWG_PTFE_1x01_D1.5mm_OD2.3mm` (Ø1.5 mm finished, 0.4 mm ring, no paste). `make_board.py --mech` places and locks all seven. The five sense pads were plated slots for nickel tails until 2026-10-24; only their drills changed (oval 3.4 / 1.6 × 0.6 to round Ø0.8).

| Hole | Ref | Net | KiCad (x, y), pad length or Ø |
|---|---|---|---|
| PACK− power wire | J108 | CELL_N | (86.975, 135.726), Ø1.5 |
| 1N Kelvin wire | J115 | CELL_1N (new) | (91.275, 135.476), Ø0.8 in a 1.5 × 1.4 pad |
| CELL2 sense wire | J110 | CELL2 | (100.000, 135.451), Ø0.8 in a 1.5 × 1.4 pad |
| 4P Kelvin wire | J116 | CELL_4P (new) | (108.725, 135.476), Ø0.8 in a 1.5 × 1.4 pad |
| PACK+ power wire | J112 | CELL_P_RAW | (113.025, 135.726), Ø1.5 |
| CELL1 sense wire | J109 | CELL1 | (86.100, 69.475), Ø0.8 in a 1.5 × 1.4 pad |
| CELL3 sense wire | J111 | CELL3 | (113.900, 69.475), Ø0.8 in a 1.5 × 1.4 pad |

**Kelvin split** (BQ40Z50-R2 SLUSCS4C §9.2.2.1.3, SLUA660 §2.3–2.4):
- **CELL_1N** is the gauge's low-current ground: U101 VSS and its strapped pins (PRES, DISP, PTC, PTCEN), its decoupling (C104, C105, C115, C116, C118), U102 VSS and its CD cap C117, R117, and the NTC returns. It meets the pack only at the 1N tab, so route it as a star from J115 and keep it off CELL_N copper.
- **CELL_N** keeps the current: the PACK− power wire J108, the shunt RS101 (with SRP's R107 at its pad), and the fuse-heater FET Q104 with its gate resistor R125.
- **CELL_4P** is the sense top: VC4 (R104), the U102 V4 and VDD filters (R119, R123) and the BAT diode D101 (TI fig. 9-12). F102 stays on CELL_P_RAW with the PACK+ power wire J112.
- **Solder order** (gauge note 15): PACK−, then 1N and the taps bottom-up, then 4P, and PACK+ last.
- `check_netlist.py` lists these pins as deliberate moves (`KELVIN` / `NET_MOVES` in `make_production.py`).

## Mechanical keep-outs on the board (cup, 2026-10-21)

JLC assembles F.Cu only. B.Cu is hand-soldered and faces the cells. `tools/make_board.py --keepouts` draws these as named KiCad rule areas, so DRC flags any part placed on one. It takes every size from `hardware/mechanical/monolith_shell.py` (the cup's values are the `CUP_*` constants there), and re-running it replaces the old `KO_*` areas. It edits the board file as text (KiCad 10's python can't build zone outlines), so run it with the board closed in KiCad.

The cup has had no vent since 2026-10-28, so `KO_F_cup_vent` (a Ø7 mm F.Cu circle at 100, 127.5) is gone and parts may go there.

| Rule area | Layer | Not allowed | Why |
|---|---|---|---|
| ~~`KO_F_above_antenna`~~ (x 117.4–121.6, y 77.4–86.4) | F.Cu | parts | removed by Logan on 2026-10-23, and `make_board.py` no longer draws it. The module footprint keeps copper off every layer under the antenna end |
| `KO_top_stop_L` / `_R` (top edge, 1 mm, x ≤ 86 and ≥ 114) | F.Cu + B.Cu | parts | the top edge bears on the top wall's inside face |
| `KO_B_rail_L/R_top` (x 88.7–93.5 / 106.5–111.3, y to 86.48) and `_bottom` (from y 116.48) | B.Cu | parts | the carrier rails bear on B.Cu; they stop where the gap filler is |
| `KO_B_gap_filler_L` / `_R` (x 84–93 / 107–116, y 88.48–114.48, notched 1.1 × 2.2 mm at the outer edge round TH101 / TH104) | B.Cu | parts | gap filler to the front cells: solid copper and thermal vias to the power stages; the two front-cell NTCs sit in the notches, under the gel |
| `KO_B_tail_CELL1` / `_CELL2` / `_CELL3` (from `sb_tail_runs()`) | B.Cu | parts | CELL2 wire and the CELL1 / CELL3 tongues and wires behind the board (drawn as the old tail runs, which cover them) |
| `KO_B_wire_PACKN` / `_PACKP` / `_1N` / `_4P` (from `sb_wire_runs()`, bottom edge to y 134.3–134.6) | B.Cu | parts | the PACK power and Kelvin wires cross the gap to their holes; sized for a 1.8 mm power wire and a 0.75 mm Kelvin wire (2026-10-24), no room for any part |

There is no rule-area type for height, so a note on Cmts.User under the board holds those limits:
- **F.Cu:** parts up to 3.2 mm; the cup wall sits 0.5 mm above.
- **B.Cu:** parts up to 2.3 mm in most places. Up to about 5 mm only in the centre strip (x 96–104) or more than 18 mm from the centre line. No heat sources.

**Hand-soldered B.Cu parts (19):**
- **BLE module group:** U301 (hot air), with its decoupling C301/C302/C303, RF match C313/C314/C315/R321 and NRST cap C304. C302, C303 and C304 are 0201 today; make them 0402 before ordering.
- **Shared bulk:** C208–C213 (22 µF 1210) in the centre strip, between the two power stages.
- **USB-side tantalums:** C421, C456, C521 and C556 (T593V, 2.0 mm since 2026-10-31; CA55 2.8 mm before), in the centre strip near the ports. C421 is at (101.6, 88.0), behind C424 / C427 (2026-10-24); it was on the C4 NTC lead run.

Fit all 19 before the first power-up: the chargers need both bulk banks.

**DRC with the cup keep-outs (scratch run, 2026-10-22):**
- Port 1's stage sits over the antenna area: Q402, R446 and R447 are in `KO_F_above_antenna` (that keep-out was removed on 2026-10-23). The power stages belong over the gap-filler zones.

## FEB 21700G cells (2026-10-21)

_Superseded on 2026-10-23 by the BAK N21700CX-65E (91 Wh; `docs/spec.md`, Cells and pack); kept as history. R413/R513 are to become 0 Ω (spec, *Decided: the charge-ceiling resistor*)._

The pack's cell is now the **FEB 21700G (68E) 6500 mAh**: 93.6 Wh instead of 82 Wh. Why and how: `docs/archive/feb-21700g-datasheet-notes.md`, `research_notes/Loss reduction/G_feb_21700g.md`, `docs/firmware/charge-and-thermal-policy.md`.

- **R413/R513 (ICHG) 9.1k → 11.8k 1 %** (UNI-ROYAL 0402WGF1182TCE, LCSC C93752; `tools/make_production.py` updated). The hardware charge ceiling becomes 48–52 A·kΩ / 11.8 kΩ = 4.07–4.45 A per port, under the FEB's 4.55 A maximum (the 9.1k allowed up to 5.83 A). Check C93752 stock before ordering; 12k (C25752, 4.0–4.33 A) is the fallback.
- **Board outline unchanged** (43.20 × 74.35 mm). The mechanical model holds the board's guide line at the 58E-era value, and the extra 0.3 mm of cell length comes out of the floor zone.
- **Slots move:** the five bottom slots (PACK−, 1N, CELL2, 4P, PACK+) move 0.30 mm toward the board's bottom edge, and the PACK / Kelvin pairs 0.18 mm outward. New positions are in `docs/production/p0-assembly.md` and `monolith_side_pcb.dxf`. CELL1 / CELL3 are unchanged. On the board: Update PCB from Schematic, then `tools/make_board.py --mech` places all seven (see *Pack wire holes and the 1N / 4P Kelvin nets*).
- **Footprint values:** run Update PCB from Schematic so R413/R513 carry 11.8k.
- **Gauge:** design capacity 6,500 mAh, new temperature ranges and protections, and a new chemistry ID (`docs/production/p0-bringup-and-training.md`).
- **Heat:** about 12 W at 100 W out (cells ~6.5 W of it). Firmware keeps the 100 W offer but starts a linear derate at ~33 °C on the hottest cell, down to ~40 W.

## Enclosure: the cup (2026-10-21)

The side tray and its aluminium cover are retired; the enclosure is now **the cup** (`hardware/mechanical/monolith_cup.py`, `docs/production/p0-assembly.md`). Same board outline, slots and tails. Board changes it needs: the schematic side and the keep-outs are in the tools (2026-10-22); the board picks them up with Update PCB from Schematic, `make_board.py --mech` and `--keepouts`. Still by hand: the gap-filler copper and vias, and moving the power stages over it.
- **Gap-filler zone on B.Cu:** |y| 7–16 mm, z 27–53 mm (shell coordinates): no parts, solid copper, a dense thermal-via array from the power stages on F.Cu. This replaces the cover as the heat path.
- **Carrier rails split:** the B.Cu rail keep-outs stay at |y| 6.5–11.3 mm but stop between z 25 and 55 mm.
- **Four peg slots** (2.6 × 2.2 mm NPTH for Ø2.0 pegs: ±0.3 mm float in y, ±0.1 in z) at y ±8.6 mm, z 14 and 68 mm: H101–H104.
- **Cover standoffs are gone** (H101–H104 are the peg holes now), and the bottom corner notches no longer clear any bosses (harmless, left as they are).
- **F.Cu height:** the cup's board-face wall sits 0.5 mm over the tallest part (3.2 mm limit unchanged).

## Next

1. **Review P0**, mainly gauge note 10. With no wake button, the gauge has to come out of SHUTDOWN when USB brings up PACK_P, through the TPS25751 dead-battery sink and the BQ25756 charging with 3V3 down. Confirm this at P0 bring-up.
2. **No cap cuts on hold.** C427/C527 is part of the 100 µF USB-side bank since the low-profile change (2026-10-18), so it stays.
3. **Finish the board.** Placement is done (2026-10-28). Still to do (full list in `docs/spec.md`, *P0 board changes still to apply*): run ERC, `check_netlist.py` and DRC in KiCad (the 2026-10-28 schematic changes were checked by script only), change R413/R513 to 0 Ω, check the TDSON footprint against the BSC007N04LS6 drawing, look up R412/R512's LCSC code, make C302–C304 0402, remove the stranded VBUS traces, then route, with the gap-filler copper and thermal vias by hand.
