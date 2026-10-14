# Monolith dev board — circuit description

Draft 5, 2026-10-11 (gauge network, charger ACUV/ACOV, USB ESD and cell holders added). Written as the plain-English input for ProtoFlow's schematic drafting, and as the checklist to verify what it generates. Every symbol, pin number and footprint ProtoFlow produces must be checked against the datasheet before layout.

**Status: schematic drafted in KiCad (`DevBoard/`, 2026-10-11; see `DevBoard/README.md` for changes from this description). Not reviewed, laid out, built or tested.** Values marked *TBD* still need a datasheet calculation.

## Purpose

A roomy prototype of the complete Monolith production circuit, used for:
- BQ40Z50-R2 gauge chemistry ID, learning cycle and golden-image export
- STM32WB firmware, Bluetooth and iPhone app bring-up
- Testing both USB-C PD ports together (shared I2C bus, pass-through, dual-port charging, USB1/USB2 power sharing)
- Measuring sleep current on an oscilloscope

## Board

- 4 layers, **0.8 mm** thick (the production USB-C connector is a mid-mount part made for a 0.8 mm board), 2 oz outer / 1 oz inner, **196 × 115 mm** (the four holders need ~96 × 110 mm and their courtyards push the mid holes out; decided 2026-10-12), six M3 mounting holes (corners plus two between the holders and the electronics).
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

- **Four single-cell 21700 spring holders** in series: **MYOUNG BH-21700-B1BJ001** (JLC C20606791), placed by JLC with the rest of the board. Surface-mount, nickel-plated contacts, −25 to 85 °C; plenty in JLC stock (checked 2026-10-11). Since the solder joints take cell insertion force, use the manufacturer's full pad size, add stitching vias to the inner copper under each pad, and keep the holders away from board flex points (near mounting holes). Backup: Keystone 1121 (through-hole) / 1122 (SMT) from DigiKey or Farnell.
  - No published current rating; treat as a few amps (normal charging and modest loads only).
  - Open holders don't stop a cell going in backwards. Silkscreen + and − at both ends of every holder, orient all four the same way, and check each cell's voltage with a meter at the tap test points before closing the fuse/link. A reversed cell can push the gauge's VC pins below ground (the 100 Ω filter resistors limit the current).
- **Pack connector** in parallel with the holder stack (CELL_N, CELL1, CELL2, CELL3, CELL_P, plus thermistor pair), for running the final learning cycle on the real welded pack. Use one or the other, never both.
- **Fuse** in series with CELL_P: prosemi 1206FA-15A (C2838894), 15 A, 300 A interrupt at 24 Vdc, sized for 100 W out at the 12 V low end (rev A4; was 8 A for holder use). JLC-placed (rev A5; was DNP and hand-fitted). Check the cells before waking the gauge: the FETs stay off until FET_EN.
- **Kelvin cell taps:** CELL1–CELL3 and the stack ends for the gauge are taken from the cell end of each holder contact (separate small traces), not from the power traces, so spring resistance isn't measured as cell resistance.
- **Cell thermistors (rev A4: one per cell):** 10 kΩ NTC (103AT type) on two wires to each of the gauge's TS1–TS4 inputs (J102, J105, J106, J107), taped to BT101–BT104 at mid-height over the sleeve. Each can is that cell's negative terminal (up to about 12.6 V above VSS on BT104) and the TS pins are rated 2.1 V, so use insulated sensors.

## 2. Gauge and protection (BQ40Z50-R2, same as production)

Values from the BQ40Z50-R2 datasheet reference schematic (section 9).

- **U_GAUGE:** BQ40Z50RSMR-R2 (LCSC C2845123).
- **Cell inputs:** VC1–VC4 each through **100 Ω** in series from the Kelvin taps, with **0.1 µF** from each VC pin to the node below (VC4→VC3, VC3→VC2, VC2→VC1, VC1→VSS). The 100 Ω also sets internal balancing current (internal FETs ~200 Ω, up to ~10 mA); balancing settings in data flash.
- **BAT supply (rev A5: from the cell top before the fuse, TI fig. 9-12):** from CELL_P_RAW (the VC4 node, before F101) through a **30 V diode** and **100 Ω** to BAT, so the gauge stays powered with the FETs off and rides through load dips. VCC is fed internally (no external parts). REG18 needs no external capacitor (internal LDO, per the datasheet).
- **PBI:** 2.2 µF ceramic to VSS.
- **Sense resistor RS_GAUGE:** Yageo PA2512FKE7W0R001E, 1 mΩ 1% 2 W 2512, ±50 ppm/°C (LCSC C326570), low side between CELL_N and GND. **100 Ω** from each end of the sense resistor to SRP / SRN (Kelvin traces), **0.1 µF** across SRP–SRN at the pins.
- **Protection FETs:** AGM404AP1 ×2, back-to-back N-FETs in the high side between CELL_P (after the fuse) and PACK_P. CHG and DSG pins each drive their FET gate through **5.1 kΩ**, with **10 MΩ** gate-to-source on each FET to hold it off if the drive is open. The reversed-charger clamp FET from TI's schematic is not needed (no external charger connects to the pack terminals). Two **0.1 µF 50 V** ceramics in series from CELL_P to PACK_P, across the FET pair (TI fig. 9-2 C1/C2; C110/C111, added rev A4).
- **PCHG:** no precharge FET (the BQ25756 does precharge itself); leave PCHG unconnected or 20 kΩ to VSS, and set data flash so precharge uses the CHG FET.
- **PACK pin:** to PACK_P (10 kΩ input resistor is internal). Two 0.1 µF ceramics in series from PACK_P to GND at the gauge.
- **TS1–TS4:** one cell thermistor each (10 kΩ 103-type NTC; internal 18 kΩ pull-up), enabled in data flash.
- **PRES/SHUTDN:** to VSS (system always present). **FUSE:** to VSS. **DISP:** to VSS. **LEDCNTLA/B/C:** leave floating. **PTC and PTCEN:** both to VSS (PTC disabled).
- **BTP_INT:** to STM32WB **PA6** with a 100 kΩ pull-up to 3V3 and a test point (battery trip point interrupt, lets the gauge wake the MCU on SOC thresholds). On production this can tie to VSS if unused.
- **SMBus:** SMBC/SMBD through **100 Ω** series resistors to the shared SCL/SDA (address 0x0B). Internal ESD is enough on board (no external TVS).
- **EV2400 header:** 4-pin 2.54 mm in the EV2400 SMBus port order (rev A4): 1 VSS, 2 SMBC, 3 SMBD, 4 not used.

## 3. Power path split and sleep-current measurement

- PACK_P feeds the **high-current branch** directly: both BQ25756 power stages (battery side) and both TPS62933 inputs. No measurement resistor on these.
- PACK_P also feeds the **low-current branch** through **R_MEAS = 10 Ω** (R201, 1 %, 1206; the fitted 1206W4F100JT5E is 1/4 W: fine for the ~0.4 W start-up pulse and < 2 mW steady state, and it opens as a fuse if U204 fails short) to PACK_LP. PACK_LP feeds the TPS62177 3.3 V converter (→ STM32WB, both TPS25751s). Expected draw is a few mA at most (~80 mV drop at 8 mA).
- The gauge itself is **not** on this branch: TI requires its BAT supply straight from the cells so it stays alive with the protection FETs off. (Dropped 2026-10-13: a third INA190 on the gauge's BAT feed. Measure the gauge current as the drop across R105, 100 Ω in the BAT feed: 50–340 µA = 5–34 mV, with the pack on battery only.)
- **Two TI INA190 current-sense amplifiers** across R_MEAS (IN+ = PACK_P side, IN− = PACK_LP side; high-side, common mode ~12–17 V is within range):
  - **U_AMP_LO: INA190A5IDDFR** (gain 500, SOT-23-8 with ENABLE) → 5 mV per µA, ~0.99 mA full scale on a 5 V supply, 27 kHz bandwidth (sleep detail). If JLC doesn't stock the A5, use INA190A4 (gain 200 → 2 mV/µA, ~2.5 mA full scale; LCSC C2059766, SC-70-6, no ENABLE pin)
  - **U_AMP_HI: INA190A1IDDFR** (gain 25, JLC C1852068, SOT-23-8) → 0.25 V per mA, ~20 mA full scale, 45 kHz bandwidth (Bluetooth bursts)
  - INA190 (datasheet): offset ±15 µV max (≈ ±1.5 µA on 10 Ω; typically much less), input bias 0.5 nA typ, common mode −0.2 to 40 V, 48 µA supply, output swings to within 40 mV of VS and 3 mV of GND
  - REF pins to GND (unidirectional: charging current reads as zero). ENABLE pins to VS through a 2-pin jumper with a 100 kΩ pull-down, so pulling the jumper shuts both amps off
  - Input filter footprints: 100 Ω in each input lead + 22 nF across IN+/IN− (36 kHz corner, TI's example); fit 0 Ω / DNP to start
  - Outputs on test loops (OUT_LO TP201, OUT_HI TP202), each with a GND loop beside it (TP208, TP209) for a short probe ground; 49.9 Ω series resistor fitted at each output to keep cable capacitance from making the amp ring
  - **Amplifier supply: on-board TI TPS70950DBVR 5 V LDO** (LCSC C96028, SOT-23-5, 18k+ in stock, ~$0.57; 2.7–30 V in, ~1 µA quiescent, 150 mA), fed from PACK_P on the high-current side of R_MEAS, so the amps' ~100 µA never passes through the 10 Ω. No external supply or USB cable needed, which also avoids a ground loop between a PC-powered supply and the scope. 1 µF in/out, 0.1 µF at each amp. 2-pin jumper in the LDO input to switch the whole measurement section off
- Ground test point next to the scope connectors for the scope ground clip.

## 4. 3.3 V always-on rail

- **U_3V3:** TPS62177DQCR fixed 3.3 V buck (LCSC C91241), input from PACK_LP.
- Inductor: Bourns SRN4018TA-100M, 10 µH (LCSC C2044417). Output 22 µF, input 2.2 µF 50 V, per the TI datasheet.
- SNOOZE / sleep pin to an STM32WB GPIO (spare pin; *TBD*).
- 0 Ω link in the 3V3 output (to break the rail for debugging) and a test point.
- Loads: STM32WB, both TPS25751 VIN_3V3, I2C pull-ups, NTC dividers.

## 5. MCU and Bluetooth (STM32WB1MMC)

- **U_MCU:** STM32WB1MMC module, powered from 3V3 with the module datasheet's decoupling; antenna end at a board edge with the module's keep-out (no copper, no ground pour).
- Pin map (same as production; checked against DS13258 table 15 on 2026-10-11, see `DevBoard/README.md`):

| Pin | Net / use |
|---|---|
| PA0 | IRQ1 — TPS25751 port 1 I2Ct_IRQ (internal pull-up) |
| PA2 | IRQ2 — TPS25751 port 2 I2Ct_IRQ (internal pull-up) |
| PB6 / PB7 | SCL / SDA (I2C1), 4.7 kΩ pull-ups to 3V3, 100 kHz |
| PA1 | NTC TH1 (port 1 power stage) |
| PA3 | NTC TH2 (port 2 power stage) |
| PA4 | NTC TH3 (connectors) |
| PA5 | NTC TH4 (heatsink position) |
| PA8 | NTC_EN — supply for the four NTC dividers |
| PA11 | EN_5V1 — TPS62933 port 1 enable |
| PA12 | EN_5V2 — TPS62933 port 2 enable |
| PB0 / PB1 / PB2 | not connected (ST: RF-sensitive pins) |
| PB4 | 3V3_SLEEP — TPS62177 SLEEP (resets with a pull-up, so the rail boots in normal mode) |
| PA13 / PA14 / NRST | SWD |
| BOOT0 | 10 kΩ pull-down; TP306 pad to pull it high for the UART bootloader (reset button SW301 on NRST) |
| PA9 / PA10 | UART debug TX / RX (USART1) |
| PA6 | GAUGE_BTP — BQ40Z50-R2 BTP_INT through a 2N7002 (Q103), 100 kΩ pull-up: **active low** |
| PB5 | status LED |
| PB8 | CHG_INH (rev A4; polarity rev A5) — drive low to allow charging; high or hi-Z stops both chargers (1 k to each CE, 47 k pull-up to 3V3 at each CE) |
| PA7 | NTC_TH5 (rev A5): TH305 at the protection FETs, ADC1_IN2, same 10k/0.1 µF divider from NTC_EN; also on J303 pin 2 for probing |
| Spares | 2.54 mm header J303 (NTC_TH5, NTC_EN, EN_5V1, EN_5V2, CHG_INH through 1 k for probing) |

- **SWD header:** standard 10-pin 1.27 mm Cortex debug (or 5-pin 2.54 mm: 3V3, SWDIO, SWCLK, NRST, GND) for an ST-LINK.
- **UART header:** 3-pin (TX, RX, GND).
- One status LED on a spare GPIO (with a 0 Ω link so it can be removed for sleep measurements).

## 6. Board NTCs (STM32WB)

- Four 10 kΩ 1% NTCs (B ≈ 3380–3435, 0603): TH1 beside port 1 FETs/inductor, TH2 beside port 2, TH3 between the two USB-C connectors on VBUS/GND copper, TH4 on a bare copper pad where the heatsink plate would sit.
- Each NTC from its ADC pin to GND, with a 10 kΩ 1 % (UNI-ROYAL 0805W8F1002T5E, C17414; was 0.1 %, about 0.25 °C difference) from the ADC pin to NTC_EN (PA8). 100 nF at each ADC pin.

## 7. USB-C ports (×2, identical; port 2 mirrors port 1)

Pin-level connections for the TPS25751 and BQ25756 follow `docs/monolith_port1_netlist.csv` (checked against TI datasheets), with these updates.

### 7.1 Connector and protection
- **J1 / J2:** Shou Han TYPE-C 16PCB0.8 IP68 (LCSC C55629727), mid-mount: 10.2 × 4.7 mm notch at the board edge, four slotted plated shell holes, pads per the drawing (rev A5). Shell to GND.
- VBUS (A4/A9/B4/B9) → VBUSx; GND (A1/A12/B1/B12) → GND; CC1/CC2 → TPS25751 CC1/CC2; D+/D− (A6/B6, A7/B7) → TPS25751 USB_P/USB_N (BC1.2); SBU unconnected.
- **TVS:** Littelfuse SMAJ22A (C148220) VBUSx to GND, right at the connector.
- **ESD protection (rev A4: D± uses Nexperia PESD5V0S2BT, C49338, because D± go to TPS25751 GPIO4/5, rated 6 V; CC keeps the ESD2CAN24): originally 2 × TI ESD2CAN24DBZRQ1 per port** (LCSC C5736151, SOT-23, ~$0.30): one on CC1/CC2, one on D+/D−. Two-channel bidirectional, ±24 V working voltage, so it survives a CC or D± line shorted to 20 V VBUS by a bad cable (a 5 V ESD array would not). ±25 kV IEC 61000-4-2, ~2.5–4.2 pF per line. Place right at the connector pins, before the 330 pF CC caps.
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
  - USB side: 4 × Taiyo Yuden GMK325BJ226MM-P, 22 µF 35 V X5R 1210 (C778721) at the FETs + 0.1 µF, plus 1 × ChuangHui SV680M350E5R8R4Z00ZZ 68 µF 35 V solid polymer (C49435121) as bulk; about 100 µF effective at 20 V
  - Battery side: 3 × Taiyo Yuden TMK325ABJ476MM-P, 47 µF 25 V X5R 1210 (C90142) at the FETs + 0.1 µF, plus 1 × JIERR MA25V100M6x6 100 µF 25 V solid polymer (C46550465) as bulk; about 136 µF effective at 16.8 V
  - Polymer for the bulk because it has no DC-bias loss; MLCCs only where the switching-frequency ripple needs them (changed from 10 + 7 MLCCs on 2026-10-12, see the README change list)
- **Resistors** (rev A4: only the FB divider stays Yageo RT 0.1 %; the rest are UNI-ROYAL 1 %):
  - FSW_SYNC: 40.2 kΩ 1 % (C17678) → ~600 kHz
  - FB: 100 kΩ (C122537) from battery side to FB, 10.0 kΩ (C110775) FB to FBG (VFB_REG set to ~1.527 V in firmware for 16.8 V)
  - ICHG: 9.1 kΩ 1 % (C23260) → ~5.5 A hardware ceiling per port (rev A4; was 5.11 kΩ / 9.8 A). One port can charge at about 1C; with both ports charging, configuration/firmware hold each at 2.8 A (ICHG_REG).
  - ILIM_HIZ: 3.6 kΩ 1 % (C22980) → ~5.6 A hardware input ceiling (KILIM = 20 A·kΩ with 5 mΩ)
  - TS: RT1 1.8 kΩ 1 % (C4177) REGN→TS, RT2 5.6 kΩ 1 % (C23189) TS→GND (rev A4; was 1.74k/5.11k), with this port's own 10 kΩ NTC (TH5 / TH6) beside its FETs → ~−20 °C to ~95 °C window
  - ACUV / ACOV divider, three resistors in series from VAC to PGND: **RAC1 137 kΩ** 1 % 0603 (C22872; top, from VAC), **RAC2 40.2 kΩ** 1 % (C17678), **RAC3 10 kΩ** 1 % (C17414, bottom, to PGND). **ACUV** connects at the RAC1/RAC2 junction and **ACOV** at the RAC2/RAC3 junction (datasheet: VACOV = 1.2 V × total / RAC3; VACUV = 1.1 V × total / (RAC2 + RAC3)).
    - Overvoltage stop: 1.2 V × 187.2 / 10.0 = **22.5 V** (above PD's 21 V max, below the SMAJ22A's 24.4 V breakdown)
    - Undervoltage stop: 1.1 V × 187.2 / 50.2 = **4.1 V**
    - Hardware input-voltage regulation floor (ACUV reaching 1.21 V): **4.5 V**, so a weak 5 V source or panel is never pulled into collapse; firmware can raise it further via the input DPM / MPPT settings
    - Divider draws ~107 µA only while VAC is powered (cable attached)
    - All three are 1 % since rev A4: the thresholds move by about ±1.5 %, still between PD's 21 V and the SMAJ22A breakdown
    - Check in the full datasheet how ACUV/ACOV behave in reverse (sourcing) mode
- REGN and DRV_SUP 4.7 µF; bootstrap caps per datasheet plus a Schottky bootstrap diode from DRV_SUP to each BTST pin (TI BQ25756 schematic checklist D2/D3, required; LRB521S-40T1G, C135802; added rev A4); VAC feed and capacitor per `monolith_port1_netlist.csv`.
- STAT1, STAT2, PG to test points (pulled up to 3V3); CE pulled low (charge enabled).

### 7.4 5 V supply for PP5V (TPS62933)
- **U_5Vx:** TPS62933DRLR (LCSC C3200405), input from PACK_P (high-current branch), output PP5Vx.
- RT tied to GND → 1.2 MHz. Feedback 107 kΩ (C865130) top, 20.0 kΩ (C469660) bottom → 5.08 V (margin over the TPS25751's 4.9 V PP5V minimum).
- Inductor: Bourns SRP5030T-3R3M, 3.3 µH (LCSC C189931).
- Output 2 × 22 µF 35 V 1206 plus at least 10 µF right at the TPS25751 PP5V pin. Input 2 × 10 µF + 100 nF. Soft-start 33 nF.
- EN ← EN_5Vx (STM32WB) with a pull-down so it's off by default.

## 8. Test points and links

- Test points on: CELL_P, CELL_N, CELL1–3, PACK_P, PACK_LP, 3V3, each VBUSx, PPHVx, PP5Vx, REGNx, SW1x/SW2x (scope-probe friendly, with nearby GND), SDA, SCL, each I2CCx, IRQ1, IRQ2.
- 0 Ω links (0805) to isolate blocks: 3V3 to each TPS25751 VIN_3V3, 3V3 to the MCU, PACK_P to each TPS62933, PACK_P to each charger's battery side (use a wide copper link footprint rated for the full current).
- Mounting holes ×6 (M3) and rubber feet or standoffs.

## Open items before ProtoFlow

- INA190A5 / INA190A1: decided 2026-10-11 to buy from DigiKey/Mouser and hand-solder (JLC stock too low)
- Confirm the STM32WB1MMC pin map in CubeMX
