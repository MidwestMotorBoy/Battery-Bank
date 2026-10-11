# Monolith dev board — circuit description

Draft 2, 2026-10-11 (gauge network values added). Written as the plain-English input for ProtoFlow's schematic drafting, and as the checklist to verify what it generates. Every symbol, pin number and footprint ProtoFlow produces must be checked against the datasheet before layout.

**Status: specification only. Nothing here has been drawn, built or tested.** Values marked *TBD* still need a datasheet calculation.

## Purpose

A roomy prototype of the complete Monolith production circuit, used for:
- BQ40Z50-R2 gauge chemistry ID, learning cycle and golden-image export
- STM32WB firmware, Bluetooth and iPhone app bring-up
- Testing both USB-C PD ports together (shared I2C bus, pass-through, dual-port charging, USB1/USB2 power sharing)
- Measuring sleep current on an oscilloscope

## Board

- 4 layers, **0.8 mm** thick (the production USB-C connector is a mid-mount part made for a 0.8 mm board), about 100 × 80 mm, mounting holes in the corners.
- Everything assembled by JLC except the cell holders and connectors you choose to hand-fit.
- Each charger power stage (BQ25756, two FET pairs, inductor, sense resistors, capacitor bank) is laid out as an **exact copy of the production power stage**, so switching and thermal results carry over. Everything else can be spread out.
- Silkscreen: label every test point, jumper, header pin and cell polarity.

## Net names

| Net | Meaning |
|---|---|
| CELL_P / CELL_N | Top and bottom of the 4S cell stack |
| CELL1, CELL2, CELL3 | Cell junctions (taps) |
| PACK_P | Pack bus after the gauge shunt and protection FETs (feeds everything) |
| PACK_LP | Low-current branch after the 10 Ω measurement resistor |
| GND | Ground (= pack negative after the gauge shunt) |
| 3V3 | Always-on 3.3 V rail |
| VBUS1 / VBUS2 | USB-C port 1 / port 2 VBUS |
| PPHV1 / PPHV2 | Each TPS25751's high-voltage power path node to its charger |
| PP5V1 / PP5V2 | Each port's 5 V supply into its TPS25751 PP5V pin |
| SDA / SCL | STM32WB I2C bus (gauge + both PD controllers) |
| I2CC1_SDA/SCL, I2CC2_SDA/SCL | Each TPS25751's private controller bus (its BQ25756 + its EEPROM) |

## 1. Cell inputs

- **Four single-cell 21700 spring holders** in series (polarized, one-way insertion; part *TBD*, rated for at least ~3–5 A). Mark polarity on silkscreen next to each.
- **Pack connector** in parallel with the holder stack (CELL_N, CELL1, CELL2, CELL3, CELL_P, plus thermistor pair), for running the final learning cycle on the real welded pack. Use one or the other, never both.
- **Fuse** in series with CELL_P, sized for holder use (*TBD*, ~5–7 A).
- **Kelvin cell taps:** CELL1–CELL3 and the stack ends for the gauge are taken from the cell end of each holder contact (separate small traces), not from the power traces, so spring resistance isn't measured as cell resistance.
- **Cell thermistor:** 10 kΩ NTC (103AT type) on two wires to the gauge's TS1 input, taped to a cell at mid-height.

## 2. Gauge and protection (BQ40Z50-R2, same as production)

Values from the BQ40Z50-R2 datasheet reference schematic (section 9).

- **U_GAUGE:** BQ40Z50RSMR-R2 (LCSC C2845123).
- **Cell inputs:** VC1–VC4 each through **100 Ω** in series from the Kelvin taps, with **0.1 µF** from each VC pin to the node below (VC4→VC3, VC3→VC2, VC2→VC1, VC1→VSS). The 100 Ω also sets internal balancing current (internal FETs ~200 Ω, up to ~10 mA); balancing settings in data flash.
- **BAT supply:** from CELL_P (after the fuse, before the protection FETs) through a **30 V diode** and **100 Ω** to BAT, so the gauge stays powered with the FETs off and rides through load dips. VCC is fed internally (no external parts). REG18 needs no external capacitor (internal LDO, per the datasheet).
- **PBI:** 2.2 µF ceramic to VSS.
- **Sense resistor RS_GAUGE:** Yageo PA2512FKE7W0R001E, 1 mΩ 1% 2 W 2512, ±50 ppm/°C (LCSC C326570), low side between CELL_N and GND. **100 Ω** from each end of the sense resistor to SRP / SRN (Kelvin traces), **0.1 µF** across SRP–SRN at the pins.
- **Protection FETs:** AGM404AP1 ×2, back-to-back N-FETs in the high side between CELL_P (after the fuse) and PACK_P. CHG and DSG pins each drive their FET gate through **5.1 kΩ**, with **10 MΩ** gate-to-source on each FET to hold it off if the drive is open. The reversed-charger clamp FET from TI's schematic is not needed (no external charger connects to the pack terminals).
- **PCHG:** no precharge FET (the BQ25756 does precharge itself); leave PCHG unconnected or 20 kΩ to VSS, and set data flash so precharge uses the CHG FET.
- **PACK pin:** to PACK_P (10 kΩ input resistor is internal). Two 0.1 µF ceramics in series from PACK_P to GND at the gauge.
- **TS1:** cell thermistor (10 kΩ 103-type NTC; internal 18 kΩ pull-up). **TS2–TS4:** tie to VSS and disable in data flash.
- **PRES/SHUTDN:** to VSS (system always present). **FUSE:** to VSS. **DISP:** to VSS. **LEDCNTLA/B/C:** leave floating. **PTC and PTCEN:** both to VSS (PTC disabled).
- **BTP_INT:** to STM32WB **PA6** with a 100 kΩ pull-up to 3V3 and a test point (battery trip point interrupt, lets the gauge wake the MCU on SOC thresholds). On production this can tie to VSS if unused.
- **SMBus:** SMBC/SMBD through **100 Ω** series resistors to the shared SCL/SDA (address 0x0B). Internal ESD is enough on board (no external TVS).
- **EV2400 header:** 3-pin 2.54 mm (SMBC, SMBD, GND).

## 3. Power path split and sleep-current measurement

- PACK_P feeds the **high-current branch** directly: both BQ25756 power stages (battery side) and both TPS62933 inputs. No measurement resistor on these.
- PACK_P also feeds the **low-current branch** through **R_MEAS = 10 Ω** (1%, 0.5 W, 1206 or larger) to PACK_LP. PACK_LP feeds the TPS62177 3.3 V converter (→ STM32WB, both TPS25751s). Expected draw is a few mA at most (~80 mV drop at 8 mA).
- The gauge itself is **not** on this branch: TI requires its BAT supply straight from the cells so it stays alive with the protection FETs off. Optional (low-current, no bypass needed): a 10 Ω in series with the gauge's BAT feed plus a third INA190 footprint (DNP) to see the gauge's ~50–340 µA on the scope.
- **Two TI INA190 current-sense amplifiers** across R_MEAS (IN+ = PACK_P side, IN− = PACK_LP side; high-side, common mode ~12–17 V is within range):
  - U_AMP_LO: INA190A5 (gain 500) → 5 mV per µA, ~1 mA full scale (sleep detail). If A5 isn't stocked, INA190A4 (gain 200 → 2 mV/µA, ~2.4 mA full scale; LCSC C2059766, SC-70-6)
  - U_AMP_HI: INA190A1 (gain 25) → 0.25 V per mA, ~20 mA full scale (Bluetooth bursts); JLC C1852068 (INA190A1IDDFR, TSOT-23-8)
  - INA190: zero-drift, ~2 µV typical offset, common mode −0.2 to 40 V, 1.7–5.5 V supply
  - REF pins to GND (unidirectional: charging current reads as zero)
  - Outputs to two BNC or SMA connectors (OUT_LO, OUT_HI) plus test points; optional RC footprint on each output
  - **Amplifier supply from a separate 5 V input** (2-pin header or USB-C/micro-USB used for power only), not from 3V3, so the amplifiers' ~50 µA isn't measured. Local 0.1 µF bypass each.
  - Confirm INA190 stock at JLC when ordering (stock wasn't visible from here)
- Ground test point next to the scope connectors for the scope ground clip.

## 4. 3.3 V always-on rail

- **U_3V3:** TPS62177DQCR fixed 3.3 V buck (LCSC C91241), input from PACK_LP.
- Inductor: Bourns SRN4018TA-100M, 10 µH (LCSC C2044417). Output 22 µF, input 2.2 µF 50 V, per the TI datasheet.
- SNOOZE / sleep pin to an STM32WB GPIO (spare pin; *TBD*).
- 0 Ω link in the 3V3 output (to break the rail for debugging) and a test point.
- Loads: STM32WB, both TPS25751 VIN_3V3, I2C pull-ups, NTC dividers.

## 5. MCU and Bluetooth (STM32WB1MMC)

- **U_MCU:** STM32WB1MMC module, powered from 3V3 with the module datasheet's decoupling; antenna end at a board edge with the module's keep-out (no copper, no ground pour).
- Pin map (same as production; confirm in STM32CubeMX):

| Pin | Net / use |
|---|---|
| PA0 | IRQ1 — TPS25751 port 1 I2Ct_IRQ (internal pull-up) |
| PA2 | IRQ2 — TPS25751 port 2 I2Ct_IRQ (internal pull-up) |
| PB6 / PB7 | SCL / SDA (I2C1), 4.7 kΩ pull-ups to 3V3, 100 kHz |
| PA1 | NTC TH1 (port 1 power stage) |
| PA3 | NTC TH2 (port 2 power stage) |
| PA4 | NTC TH3 (connectors) |
| PA5 | NTC TH4 (heatsink position) |
| PB0 | NTC_EN — supply for the four NTC dividers |
| PB1 | EN_5V1 — TPS62933 port 1 enable |
| PB2 | EN_5V2 — TPS62933 port 2 enable |
| PA13 / PA14 / NRST | SWD |
| BOOT0 | 10 kΩ pull-down |
| PA9 / PA10 | UART debug TX / RX (if CubeMX confirms USART1 there) |
| PA6 | GAUGE_BTP — BQ40Z50-R2 BTP_INT (100 kΩ pull-up) |
| Spares | PA7, PA8, PA11, PA12, PB4, PB5, PB8 → bring all to a 2.54 mm header |

- **SWD header:** standard 10-pin 1.27 mm Cortex debug (or 5-pin 2.54 mm: 3V3, SWDIO, SWCLK, NRST, GND) for an ST-LINK.
- **UART header:** 3-pin (TX, RX, GND).
- One status LED on a spare GPIO (with a 0 Ω link so it can be removed for sleep measurements).

## 6. Board NTCs (STM32WB)

- Four 10 kΩ 1% NTCs (B ≈ 3380–3435, 0603): TH1 beside port 1 FETs/inductor, TH2 beside port 2, TH3 between the two USB-C connectors on VBUS/GND copper, TH4 on a bare copper pad where the heatsink plate would sit.
- Each NTC from its ADC pin to GND, with a 10.0 kΩ 0.1% (Yageo RT0805BRD0710KL, C110775) from the ADC pin to NTC_EN (PB0). 100 nF at each ADC pin.

## 7. USB-C ports (×2, identical; port 2 mirrors port 1)

Pin-level connections for the TPS25751 and BQ25756 follow `docs/monolith_port1_netlist.csv` (checked against TI datasheets), with these updates.

### 7.1 Connector and protection
- **J1 / J2:** Shou Han TYPE-C 16PCB0.8 IP68 (LCSC C55629727), mid-mount: 10.2 × 4.7 mm notch at the board edge, four slotted plated shell holes, pads per the drawing (rev A5). Shell to GND.
- VBUS (A4/A9/B4/B9) → VBUSx; GND (A1/A12/B1/B12) → GND; CC1/CC2 → TPS25751 CC1/CC2; D+/D− (A6/B6, A7/B7) → TPS25751 USB_P/USB_N (BC1.2); SBU unconnected.
- **TVS:** Littelfuse SMAJ22A (C148220) VBUSx to GND, right at the connector.
- **ESD array** on CC1/CC2/D+/D−, 24 V-tolerant on CC (part *TBD*).
- 330 pF on each CC line (TPS25751 datasheet).

### 7.2 PD controller (TPS25751D)
- **U_PDx:** TPS25751DREFR (LCSC C30169739). VIN_3V3 from 3V3; LDO_3V3, LDO_1V5, VBUS, PP5V capacitors per datasheet.
- **I2C address / dead-battery straps (SafeMode):** port 1: ADCIN1 → LDO_3V3, ADCIN2 → GND (address 0x20). Port 2: ADCIN1 → GND, ADCIN2 → GND (0x21). Add unpopulated divider footprints on each ADCIN so other strap options can be tried.
- I2Ct (target) SDA/SCL → shared SDA/SCL. I2Ct_IRQ → IRQ1 / IRQ2.
- I2Cc (controller) → this port's private bus I2CCx_SDA/SCL with pull-ups to this TPS25751's **LDO_3V3** (TI guidance); I2Cc_IRQ ← its BQ25756 INT.
- PPHV → PPHVx (to the charger's input side). PP5V ← PP5Vx.
- **EEPROM:** ST M24512-DFMC6TG, 512 Kbit, DFN8 2 × 3 mm (LCSC C222237) on I2CCx at address 0x50, powered from this TPS25751's LDO_3V3. WC (write control) to GND. Add a 3-pin header on each I2CCx bus (SDA, SCL, GND) for a logic analyzer.

### 7.3 Charger and power stage (BQ25756) — copy of production layout
- **U_CHGx:** BQ25756RRVR (LCSC C19272232).
- **FETs:** two Infineon IAUC45N04S6L063H half-bridges (JLC C3288896): leg A (USB side: HIDRV1/LODRV1, SW1), leg B (battery side: HIDRV2/LODRV2, SW2).
- **Inductor:** Coilcraft XAL7030-222MEC, 2.2 µH (JLC C19191686) between SW1 and SW2.
- **Sense resistors:** Yageo PA2010FKE470R005Z, 5 mΩ 2 W 2010 (C7256567) for both RAC (ACP/ACN, USB side) and RBAT (SRP/SRN, battery side).
- **Capacitors (≥ 80 µF effective each side after DC-bias derating):**
  - USB side: 10 × Taiyo Yuden GMK325BJ226MM-P, 22 µF 35 V X5R 1210 (C778721); 2 at the FETs + 0.1 µF, 8 as bulk
  - Battery side: 7 × Taiyo Yuden TMK325ABJ476MM-P, 47 µF 25 V X5R 1210 (C90142); 2 at the FETs + 0.1 µF, 5 as bulk
- **Resistors (Yageo RT 0.1%):**
  - FSW_SYNC: 40.2 kΩ (C865475) → ~600 kHz
  - FB: 100 kΩ (C122537) from battery side to FB, 10.0 kΩ (C110775) FB to FBG (VFB_REG set to ~1.527 V in firmware for 16.8 V)
  - ICHG: 5.11 kΩ (C705788) → ~9.8 A hardware ceiling
  - ILIM_HIZ: 3.65 kΩ (C705773) → ~5.5 A hardware input ceiling (KILIM = 20 A·kΩ with 5 mΩ)
  - TS: RT1 1.74 kΩ (C784581) REGN→TS, RT2 5.11 kΩ (C705788) TS→GND, with this port's own 10 kΩ NTC (TH5 / TH6) beside its FETs → ~−20 °C to ~95 °C window
  - ACUV / ACOV divider: *TBD* from the datasheet (target: undervoltage below 4.5 V, overvoltage just above 21 V)
- REGN and DRV_SUP 4.7 µF; bootstrap caps per datasheet; VAC feed and capacitor per `monolith_port1_netlist.csv`.
- STAT1, STAT2, PG to test points (pulled up to 3V3); CE pulled low (charge enabled).

### 7.4 5 V supply for PP5V (TPS62933)
- **U_5Vx:** TPS62933DRLR (LCSC C3200405), input from PACK_P (high-current branch), output PP5Vx.
- RT tied to GND → 1.2 MHz. Feedback 105 kΩ (C865128) top, 20.0 kΩ (C469660) bottom → 5.00 V.
- Inductor: Bourns SRP5030T-3R3M, 3.3 µH (LCSC C189931).
- Output 2 × 22 µF 35 V 1206 plus at least 10 µF right at the TPS25751 PP5V pin. Input 2 × 10 µF + 100 nF. Soft-start 33 nF.
- EN ← EN_5Vx (STM32WB) with a pull-down so it's off by default.

## 8. Test points and links

- Test points on: CELL_P, CELL_N, CELL1–3, PACK_P, PACK_LP, 3V3, each VBUSx, PPHVx, PP5Vx, REGNx, SW1x/SW2x (scope-probe friendly, with nearby GND), SDA, SCL, each I2CCx, IRQ1, IRQ2.
- 0 Ω links (0805) to isolate blocks: 3V3 to each TPS25751 VIN_3V3, 3V3 to the MCU, PACK_P to each TPS62933, PACK_P to each charger's battery side (use a wide copper link footprint rated for the full current).
- Mounting holes ×4 and rubber feet.

## Open items before ProtoFlow

- 21700 holder part number (polarized, 3–5 A)
- INA190 JLC stock at order time; amplifier 5 V input connector
- ESD array for CC/D+/D−
- BQ25756 ACUV/ACOV divider values
- Confirm the STM32WB1MMC pin map in CubeMX
