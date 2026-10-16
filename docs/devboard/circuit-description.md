# Monolith dev board — circuit description

Draft 5, 2026-10-11 (gauge network, charger ACUV/ACOV, USB ESD and cell holders added). Written as the plain-English input for ProtoFlow's schematic drafting, and as the checklist to verify what it generates. Every symbol, pin number and footprint ProtoFlow produces must be checked against the datasheet before layout.

**Status: schematic drafted in KiCad (`DevBoard/`, 2026-10-11; see `DevBoard/README.md` for changes from this description). Not reviewed, laid out, built or tested.** Values marked *TBD* still need a datasheet calculation.

## Purpose

A roomy prototype of the complete Monolith production circuit, used for:
- BQ40Z50-R2 gauge chemistry ID, learning cycle and golden-image export
- CC2340 firmware (TI LPF3 SDK), Bluetooth and iPhone app bring-up
- Testing both USB-C PD ports together (shared I2C bus, pass-through, dual-port charging, USB1/USB2 power sharing)
- Measuring sleep current on an oscilloscope

## Board

- **6 layers, 1.6 mm** thick, 2 oz outer / 0.5 oz inner, vias epoxy-filled and capped (2026-10-14; was 4 layers, 0.8 mm, 2 oz / 1 oz, chosen to match production's 0.8 mm mid-mount USB-C; production thickness is open), **196 × 115 mm** (the four holders need ~96 × 110 mm and their courtyards push the mid holes out; decided 2026-10-12), six M3 mounting holes (corners plus two between the holders and the electronics).
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
| SDA / SCL | MCU I2C bus (gauge, both PD controllers, TMP1075 sensors) |
| I2CC1_SDA/SCL, I2CC2_SDA/SCL | Each TPS25751's private controller bus (its BQ25756 + its EEPROM) |

## 1. Cell inputs

- **Four single-cell 21700 spring holders** in series: **MYOUNG BH-21700-B1BJ001** (JLC C20606791), placed by JLC with the rest of the board. Surface-mount, nickel-plated contacts, −25 to 85 °C; plenty in JLC stock (checked 2026-10-11). Since the solder joints take cell insertion force, use the manufacturer's full pad size, add stitching vias to the inner copper under each pad, and keep the holders away from board flex points (near mounting holes). Backup: Keystone 1121 (through-hole) / 1122 (SMT) from DigiKey or Farnell.
  - No published current rating; treat as a few amps (normal charging and modest loads only).
  - Open holders don't stop a cell going in backwards. Silkscreen + and − at both ends of every holder, orient all four the same way, and check each cell's voltage with a meter at the tap test points before closing the fuse/link. A reversed cell can push the gauge's VC pins below ground (the 100 Ω filter resistors limit the current).
- **Pack connector** in parallel with the holder stack (CELL_N, CELL1, CELL2, CELL3, CELL_P, plus thermistor pair), for running the final learning cycle on the real welded pack. Use one or the other, never both.
- **Fuse (rev A6):** F102, TLC WSFB1514 (C42463217), a 3-terminal self-control fuse between CELL_P_RAW and CELL_P. Its 15 A element (50 A interrupt, 36 V) is the pack's only fuse, and its heater lets U102 (BQ294700, 4.35 V/cell) or the gauge FUSE pin blow it through Q104 (TI BQ40Z50-R2 fig. 9-11). Until rev A5 the fuse was F101, prosemi 1206FA-15A (300 A interrupt). See DevBoard README items 33 and 36. Check the cells before waking the gauge: the FETs stay off until FET_EN.
- **Kelvin cell taps:** CELL1–CELL3 and the stack ends for the gauge are taken from the cell end of each holder contact (separate small traces), not from the power traces, so spring resistance isn't measured as cell resistance.
- **Cell thermistors (rev A4: one per cell):** 10 kΩ NTC (103AT type) on two wires to each of the gauge's TS1–TS4 inputs (J102, J105, J106, J107), taped to BT101–BT104 at mid-height over the sleeve. Each can is that cell's negative terminal (up to about 12.6 V above VSS on BT104) and the TS pins are rated 2.1 V, so use insulated sensors.

## 2. Gauge and protection (BQ40Z50-R2, same as production)

Values from the BQ40Z50-R2 datasheet reference schematic (section 9).

- **U_GAUGE:** BQ40Z50RSMR-R2 (LCSC C2845123).
- **Cell inputs:** VC1–VC4 each through **100 Ω** in series from the Kelvin taps, with **0.1 µF** from each VC pin to the node below (VC4→VC3, VC3→VC2, VC2→VC1, VC1→VSS). The 100 Ω also sets internal balancing current (internal FETs ~200 Ω, up to ~10 mA); balancing settings in data flash.
- **BAT supply (rev A5: from the cell top before the fuse, TI fig. 9-12):** from CELL_P_RAW (the VC4 node, before the fuse: F101 until rev A5, F102 since rev A6) through a **30 V diode** and **100 Ω** to BAT, so the gauge stays powered with the FETs off and rides through load dips. VCC is fed internally (no external parts). REG18 needs no external capacitor (internal LDO, per the datasheet).
- **PBI:** 2.2 µF ceramic to VSS.
- **Sense resistor RS_GAUGE:** Yageo PA2512FKE7W0R001E, 1 mΩ 1% 2 W 2512, ±50 ppm/°C (LCSC C326570), low side between CELL_N and GND. **100 Ω** from each end of the sense resistor to SRP / SRN (Kelvin traces), **0.1 µF** across SRP–SRN at the pins.
- **Protection FETs:** AGM404AP1 ×2, back-to-back N-FETs in the high side between CELL_P (after the fuse) and PACK_P. CHG and DSG pins each drive their FET gate through **5.1 kΩ**, with **10 MΩ** gate-to-source on each FET to hold it off if the drive is open. The reversed-charger clamp FET from TI's schematic is not needed (no external charger connects to the pack terminals). Two **0.1 µF 50 V** ceramics in series from CELL_P to PACK_P, across the FET pair (TI fig. 9-2 C1/C2; C110/C111, added rev A4).
- **PCHG:** no precharge FET (the BQ25756 does precharge itself); leave PCHG unconnected or 20 kΩ to VSS, and set data flash so precharge uses the CHG FET.
- **PACK pin:** to PACK_P (10 kΩ input resistor is internal). Two 0.1 µF ceramics in series from PACK_P to GND at the gauge.
- **TS1–TS4:** one cell thermistor each (10 kΩ 103-type NTC; internal 18 kΩ pull-up), enabled in data flash.
- **PRES/SHUTDN:** to VSS (system always present). **FUSE (rev A6):** to Q104's gate through R126 5.1 kΩ (net GAUGE_FUSE); it drives the F102 heater and reads U102's trip. **DISP:** to VSS. **LEDCNTLA/B/C:** leave floating. **PTC and PTCEN:** both to VSS (PTC disabled).
- **BTP_INT:** through Q103 onto the shared IRQ_N line (rev A7; R114 now DNP, pull-up R314 on the MCU sheet) and a test point (battery trip point interrupt, lets the gauge wake the MCU on SOC thresholds). On production this can tie to VSS if unused.
- **SMBus:** SMBC/SMBD through **100 Ω** series resistors to the shared SCL/SDA (address 0x0B). Internal ESD is enough on board (no external TVS).
- **EV2400 header:** 4-pin 2.54 mm in the EV2400 SMBus port order (rev A4): 1 VSS, 2 SMBC, 3 SMBD, 4 not used.

## 3. Power path split and sleep-current measurement

- PACK_P feeds the **high-current branch** directly: both BQ25756 power stages (battery side) and both TPS62933 inputs. No measurement resistor on these.
- PACK_P also feeds the **low-current branch** through **R_MEAS = 10 Ω** (R201, 1 %, 1206; the fitted 1206W4F100JT5E is 1/4 W: fine for the ~0.4 W start-up pulse and < 2 mW steady state, and it opens as a fuse if U204 fails short) to PACK_LP. PACK_LP feeds the TPS62177 3.3 V converter (→ CC2340R5MODA, both TPS25751s). Expected draw is a few mA at most (~80 mV drop at 8 mA).
- The gauge itself is **not** on this branch: TI requires its BAT supply straight from the cells so it stays alive with the protection FETs off. (Dropped 2026-10-13: a third INA190 on the gauge's BAT feed. Measure the gauge current as the drop across R105, 100 Ω in the BAT feed: 50–340 µA = 5–34 mV, with the pack on battery only.)
- **Two TI INA190 current-sense amplifiers** across R_MEAS (IN+ = PACK_P side, IN− = PACK_LP side; high-side, common mode ~12–17 V is within range):
  - **U_AMP_LO: INA190A5IDDFR** (gain 500, SOT-23-8 with ENABLE) → 5 mV per µA, ~0.99 mA full scale on a 5 V supply, 27 kHz bandwidth (sleep detail). If JLC doesn't stock the A5, use INA190A4 (gain 200 → 2 mV/µA, ~2.5 mA full scale; LCSC C2059766, SC-70-6, no ENABLE pin)
  - **U_AMP_HI: INA190A1IDDFR** (gain 25, JLC C1852068, SOT-23-8) → 0.25 V per mA, ~20 mA full scale, 45 kHz bandwidth (Bluetooth bursts)
  - INA190 (datasheet): offset ±15 µV max (≈ ±1.5 µA on 10 Ω; typically much less), input bias 0.5 nA typ, common mode −0.2 to 40 V, 48 µA supply, output swings to within 40 mV of VS and 3 mV of GND
  - REF pins to GND (unidirectional: charging current reads as zero). ENABLE pins to VS through a 2-pin jumper with a 100 kΩ pull-down, so pulling the jumper shuts both amps off
  - Input filter footprints: 100 Ω in each input lead + 22 nF across IN+/IN− (36 kHz corner, TI's example); fit 0 Ω / DNP to start
  - Outputs on test loops (OUT_LO TP201, OUT_HI TP202), each with a GND loop beside it (TP208, TP209) for a short probe ground; 49.9 Ω series resistor fitted at each output to keep cable capacitance from making the amp ring
  - **Amplifier supply: on-board Holtek HT7550-1 5 V LDO** (LCSC C16106, SOT-89, JLC preferred, ~$0.13; 30 V in, 2.5 µA quiescent, ±3 %, 100 mA; was the TPS70950DBVR until the cost-down 2026-10-14, `cost-down-2026-10-14.md`), fed from PACK_P on the high-current side of R_MEAS, so the amps' ~100 µA never passes through the 10 Ω. No external supply or USB cable needed, which also avoids a ground loop between a PC-powered supply and the scope. 10 µF 50 V in and 10 µF out (Holtek basic circuit), 0.1 µF at each amp. 2-pin jumper in the LDO input to switch the whole measurement section off
- Ground test point next to the scope connectors for the scope ground clip.

## 4. 3.3 V always-on rail

- **U_3V3:** TPS62177DQCR fixed 3.3 V buck (LCSC C91241), input from PACK_LP.
- Inductor: Changjiang FNR4030S100MT, 10 µH, 130 mΩ (LCSC C167879; was Bourns SRN4018TA-100M until the cost-down 2026-10-14, `cost-down-2026-10-14.md`). Output 22 µF, input 2.2 µF 50 V, per the TI datasheet.
- SLEEP pin to CC2340 DIO21 (3V3_SLEEP), with R313 470 kΩ to 3V3 to hold normal mode while the MCU is in reset.
- 0 Ω link in the 3V3 output (to break the rail for debugging) and a test point.
- Loads: CC2340R5MODA, both TPS25751 VIN_3V3, I2C pull-ups, TMP1075 sensors.

## 5. MCU and Bluetooth (CC2340R5MODA, rev A7)

- **U301:** TI CC2340R5MODA module (BLE only; Cortex-M0+, 512 kB flash, 64 kB RAM; on-chip OTA updates), wired per SWRS349A fig. 9-1. It replaced the STM32WB1MMC in rev A7 (`cc2340-pin-budget.md`, `DevBoard/README.md` item 40).
- **Supply:** VDDS from 3V3 through R301 (0 Ω) as 3V3_MCU, with C301–C303.
- **Reset:** R302 100k pull-up and C304 100 nF on RSTN (fig. 9-1 R1/C92); reset button SW301.
- **Antenna:** integrated, at a board edge with ground 10–20 mm either side. A 7.0 × 3.2 mm keep-out on all layers is drawn in the footprint (fig. 9-2).
    - RFIO → C313 15 pF (CA1) → R321 0 Ω (Z61) → ANT_IN.
    - Shunts: C314 (Z60) DNP, C315 1 pF (Z62). These are the LaunchPad values; retune them on the real board.
- **Clock:** no 32 kHz crystal. LFOSC, calibrated against the module's 48 MHz crystal, is fine for BLE.
- **Pin map:** 12 DIOs, two of them SWD, so 10 for the board. All 10 are used:

| DIO (pad) | Net / use |
|---|---|
| DIO6 (9) / DIO8 (10) | SCL / SDA (I2C0; SCL can only use DIO6 or DIO24), 4.7 kΩ pull-ups to 3V3, 100 kHz |
| DIO18 (16) / DIO20 (17) | UART debug TX / RX (UART0) |
| DIO12 (18) | Status LED (high-drive) |
| DIO24 (11) | CHG_INH: drive low to allow charging; high or hi-Z stops both chargers (1 k to each CE, 47 k pull-up to 3V3 at each CE) |
| DIO3 (12) / DIO4 (13) | EN_5V1 / EN_5V2: TPS62933 enables, 100 kΩ pull-downs |
| DIO21 (15) | 3V3_SLEEP: TPS62177 SLEEP. R313 470 kΩ holds the rail in normal mode while the MCU is in reset |
| DIO11 (21) | IRQ_N: TPS25751 I2Ct_IRQ ×2, gauge BTP (via Q103) and the TMP1075 ALERTs, all open-drain, wire-ORed; one 100 kΩ pull-up (R314). Active low; wakes the MCU from standby |
| DIO16 (20) / DIO17 (19) / RSTN (14) | SWD |
| Spares | 2.54 mm header J303: 3V3, IRQ_N probe, EN_5V1, EN_5V2, CHG_INH (the last three through 1 k for probing/override) |

- **SWD header:** J301, 10-pin 1.27 mm Cortex debug, for a TI XDS110.
- **UART header:** 3-pin (TX, RX, GND).
- **Status LED:** one, with a 0 Ω link (R307) so it can be removed for sleep measurements.
- **Bootloader:** the ROM serial bootloader runs on a blank part; later, a CCFG backdoor pin set in firmware.
- **Watchdog:** the WDT runs in active, idle and standby, and can't be stopped once enabled. GPIOs are latched in standby.

## 6. Board temperature sensors (TMP1075, rev A7)

- **TMP1075DSGR (WSON-8 2 × 2 mm) on the shared I2C bus.** Each exposed pad sits on the copper it measures, tied to GND with thermal vias. 0.1 µF bypass at each (C308–C312).

| Ref | Address | Where | Fitted |
|---|---|---|---|
| U302 | 0x48 | Port 1 power stage (FETs/inductor PGND copper; was TH301) | Yes |
| U303 | 0x49 | Port 2 power stage (was TH302) | Yes |
| U304 | 0x4A | Between the USB-C connectors, on GND copper (TH303 sat on VBUS) | Yes |
| U305 | 0x4B | Heatsink-plate spot (was TH304) | DNP |
| U306 | 0x4C | Protection FETs Q101/Q102 (was TH305) | DNP: FET over-temperature comes from the gauge's internal sensor (OTD/OTC); fit this if the gauge die lags the FETs |

- **Address straps:** A0/A1/A2 tied to GND or 3V3 (SBOS854F table 7-2).
- **ALERT:** open-drain, comparator mode, active low; power-up default trip is 80 °C. All ALERTs share IRQ_N, so an over-temperature wakes the MCU.
- **What other parts already sense:** cells on gauge TS1–TS4; each charger stage on its BQ25756 TS NTC (hardware stop at about 95 °C). The MCU sensors drive the 20 W throttle before that hard stop.

## 7. USB-C ports (×2, identical; port 2 mirrors port 1)

Pin-level connections for the TPS25751 and BQ25756 follow `docs/monolith_port1_netlist.csv` (git tag `product-draft-2026-10-09`; checked against TI datasheets), with these updates.

### 7.1 Connector and protection
- **J1 / J2:** Shou Han TYPE-C 16PCB1.6 IP68 (LCSC C55629729; the 1.6 mm board version of the 16PCB0.8, same land pattern), mid-mount: 10.2 × 4.7 mm notch at the board edge, four slotted plated shell holes, pads per the drawing (rev A5). Shell to GND.
- VBUS (A4/A9/B4/B9) → VBUSx; GND (A1/A12/B1/B12) → GND; CC1/CC2 → U405 C_CC1/C_CC2 → CC1/CC2 → TPS25751 CC1/CC2.
- **Rev A6:** D+/D− (A6/B6, A7/B7) are shorted by R440/R540 (0 Ω, a passive BC1.2 DCP signature); the TPS25751 no longer does BC1.2. SBU1/SBU2 feed liquid detection: TPD4S201 (U405/U505, item 39) → GPIO4/5, with switched 100 kΩ pull-up / 1 MΩ pull-down (GPIO6/7) and the TPD4S201 FLT on GPIO3. Before rev A6, D+/D− went to TPS25751 USB_P/USB_N and SBU was unconnected. See DevBoard README items 35–36.
- **TVS (rev A8):** TI TVS2200DRVR (LCSC C523793; flat clamp, 22 V standoff, 24.6 V breakdown min, 28 V clamp at 40 A 8/20 µs) VBUSx to GND, right at the connector. It replaced the SMAJ22A (35.5 V clamp), which let a live 20 V hot-plug reach the 28 V abs max of the TPS25751 and TPD4S201 (review 4 C-4).
- **ESD protection:** CC and SBU: TPD4S201 port protector U405/U505 (IEC ±8 kV contact, ±35 V surge, 28 V short-to-VBUS tolerance). D±: none, as they only meet each other through R440/R540. History: rev A4 used ESD2CAN24 on CC and PESD5V0S2BT on D±; rev A6 had a TPD2S300 on SBU; both were replaced by the TPD4S201 (README item 39).
- 220 pF on each CC line (rev A8; was 330 pF): with the TPD4S201's 40–120 pF the total stays under the TPS25751's 480 pF maximum; TI's EVM value with this protector (review 4 C-3).

### 7.2 PD controller (TPS25751D)
- **U_PDx:** TPS25751DREFR (LCSC C30169739). VIN_3V3 from 3V3; LDO_3V3, LDO_1V5, VBUS, PP5V capacitors per datasheet.
- **I2C address / dead-battery straps (SafeMode):** port 1: ADCIN1 → LDO_3V3, ADCIN2 → GND (address 0x20). Port 2: ADCIN1 → GND, ADCIN2 → GND (0x21). The straps are single 0 Ω parts (R1–R4) on the root sheet. To try another option, change which rail each 0 Ω goes to; moving port 1's R1 to GND gives decoded 0, and SafeMode #2 then collides with port 2's 0x21.
- I2Ct (target) SDA/SCL → shared SDA/SCL. I2Ct_IRQ → IRQ_N (shared with the other port, the gauge BTP and the TMP1075 ALERTs, rev A7).
- I2Cc (controller) → this port's private bus I2CCx_SDA/SCL with pull-ups to this TPS25751's **LDO_3V3** (TI guidance); I2Cc_IRQ ← its BQ25756 INT.
- PPHV → PPHVx (to the charger's input side). PP5V ← PP5Vx.
- **EEPROM:** ST M24512-DFMC6TG, 512 Kbit, DFN8 2 × 3 mm (LCSC C222237) on I2CCx at address 0x50, powered from this TPS25751's LDO_3V3. WC (write control) to GND. Add a 3-pin header on each I2CCx bus (SDA, SCL, GND) for a logic analyzer.

### 7.3 Charger and power stage (BQ25756) — copy of production layout
- **U_CHGx:** BQ25756RRVR (LCSC C19272232).
- **FETs (rev A6 cost-down, 2026-10-14):** four discrete JinYu PGQ04N070 per port (JLC C49384056, PDFN3333; 40 V, 7 mΩ max at 10 V, 10 mΩ max at 4.5 V, Qg 14.7 nC). Leg A (USB side): Q401 high side (HIDRV1), Q407 low side (LODRV1), SW1. Leg B (battery side): Q402 high side (HIDRV2), Q408 low side (LODRV2), SW2. This matches the production BOM's plan of four discrete 40 V logic-level 3.3 × 3.3 mm FETs. Until then the legs were Infineon IAUC45N04S6L063H half-bridges (C3288896, 8.5 mΩ max at 4.5 V, $1.16, 62 at JLC).
- **Inductor:** SXN SMMS1040-2R2M, 2.2 µH, Isat 18 A and Irms 12 A (typical values; soft saturation, −17 % at 15 A), 9 mΩ max, 11.5 × 10 mm (LCSC C149591), between SW1 and SW2. It was Coilcraft XAL7030-222MEC until the cost-down 2026-10-14, `cost-down-2026-10-14.md`.
- **Sense resistors:** Yageo PA2010FKE470R005Z, 5 mΩ 2 W 2010 (C7256567) for both RAC (ACP/ACN, USB side) and RBAT (SRP/SRN, battery side).
- **Capacitors (≥ 80 µF effective each side after DC-bias derating):**
  - USB side: 4 × Taiyo Yuden GMK325BJ226MM-P, 22 µF 35 V X5R 1210 (C778721) at the FETs + 0.1 µF, plus 1 × Honor HV1V107M0607PZ 100 µF 35 V solid polymer (C5246554) as bulk; ≥ 80 µF effective at 20 V
  - Battery side: 3 × Samsung CL31A226KAHNNNE, 22 µF 25 V X5R 1206 (C12891, JLC basic) at the FETs + 0.1 µF, plus 1 × Panasonic EEH-ZA1E101XP 100 µF 25 V hybrid polymer (C264047, 30 mΩ, 2 A, leakage ≤ 25 µA; was the JIERR MA25V100M6x6 solid polymer with a 500 µA limit until 2026-10-15) as bulk; about 114 µF effective at 16.8 V (≥ 80 µF). They were 47 µF 1210s until the cost-down 2026-10-14, `cost-down-2026-10-14.md`
  - Polymer for the bulk because it has no DC-bias loss; MLCCs only where the switching-frequency ripple needs them (changed from 10 + 7 MLCCs on 2026-10-12, see the README change list)
- **Resistors** (rev A4: only the FB divider stays Yageo RT 0.1 %; the rest are UNI-ROYAL 1 %):
  - FSW_SYNC: 40.2 kΩ 1 % 0603 (C12447) → about 598 kHz
  - FB: 100 kΩ (C122537) from battery side to FB, 10.0 kΩ (C110775) FB to FBG (VFB_REG = 0x0F, 1.534 V, written by the bundle for 16.8 V; the power-on value gives 16.70–16.96 V)
  - ICHG: 9.1 kΩ 1 % (C23260) → ~5.5 A hardware ceiling per port (rev A4; was 5.11 kΩ / 9.8 A). One port can charge at about 1C; with both ports charging, configuration/firmware hold each at 2.8 A (ICHG_REG).
  - ILIM_HIZ: 3.6 kΩ 1 % (C22980) → ~5.6 A hardware input ceiling (KILIM = 20 A·kΩ with 5 mΩ)
  - TS: RT1 1.8 kΩ 1 % (C4177) REGN→TS, RT2 5.6 kΩ 1 % (C23189) TS→GND (rev A4; was 1.74k/5.11k), with this port's own 10 kΩ NTC (TH401 / TH501) on its FET copper → about −7.6 °C to 94.5 °C window (TS_T5 = 81 °C configured)
  - ACUV / ACOV divider, three resistors in series from VAC to PGND: **RAC1 137 kΩ** 1 % 0603 (C22872; top, from VAC), **RAC2 40.2 kΩ** 1 % 0603 (C12447), **RAC3 10 kΩ** 1 % (C17414, bottom, to PGND). **ACUV** connects at the RAC1/RAC2 junction and **ACOV** at the RAC2/RAC3 junction (datasheet: VACOV = 1.2 V × total / RAC3; VACUV = 1.1 V × total / (RAC2 + RAC3)).
    - Overvoltage stop: 1.2 V × 187.2 / 10.0 = **22.5 V** (above PD's 21 V max, below the TVS2200's 24.6 V minimum breakdown)
    - Undervoltage stop: 1.1 V × 187.2 / 50.2 = **4.1 V**
    - Hardware input-voltage regulation floor (ACUV reaching 1.21 V): **4.5 V**, so a weak 5 V source or panel is never pulled into collapse; firmware can raise it further via the input DPM / MPPT settings
    - Divider draws ~107 µA only while VAC is powered (cable attached)
    - All three are 1 % since rev A4: the thresholds move by about ±1.5 %, still between PD's 21 V and the TVS breakdown
    - Reverse (sourcing) mode: the converter stops on its own reverse-mode undervoltage (review 4 C-7); how ACUV/ACOV act there is still to confirm at bring-up
- REGN and DRV_SUP 4.7 µF; bootstrap caps per datasheet plus a Schottky bootstrap diode from DRV_SUP to each BTST pin (TI BQ25756 schematic checklist D2/D3, required; LRB520S-40T1G, C132124; added rev A4); VAC feed and capacitor per `monolith_port1_netlist.csv` (git tag `product-draft-2026-10-09`).
- STAT1, STAT2, PG to test points (pulled up to 3V3). CE: R417/R517 47k pull-up to 3V3, so charging needs the MCU to drive CHG_INH (DIO24) low through R435/R535 (rev A5; fails safe in reset).
- High-side gate drive: at 100 % duty (Q402 in reverse boost and forward buck, Q401 in forward boost) the BQ25756 holds the gate up with an internal charge pump (TI E2E; not in the datasheet). Keep the high-side gates free of pull-down resistors; verify the gate voltage at bring-up (review 4 B-1).

### 7.4 5 V supply for PP5V (TPS62933)
- **U_5Vx:** TPS62933DRLR (LCSC C3200405), input from PACK_P (high-current branch), output PP5Vx.
- RT tied to GND → 1.2 MHz. Feedback 107 kΩ (C865130) top, 20.0 kΩ (C469660) bottom → 5.08 V (margin over the TPS25751's 4.9 V PP5V minimum).
- Inductor: Coilank APS0530M3R3H, 3.3 µH, 38 mΩ, Irms 5 A, Isat 8 A (LCSC C49073587; was Bourns SRP5030T-3R3M until the cost-down 2026-10-14, `cost-down-2026-10-14.md`).
- Output 2 × 22 µF 25 V 1206 (CL31A226KAHNNNE) plus a 220 µF 16 V polymer (C443/C543) and at least 10 µF right at the TPS25751 PP5V pin. Input 2 × 10 µF + 100 nF. Soft-start 33 nF.
- EN ← EN_5Vx (MCU) with a pull-down so it's off by default.

## 8. Test points and links

- Test points on: CELL_P, CELL_N, CELL1–3, PACK_P, PACK_LP, 3V3, each VBUSx, PPHVx, PP5Vx, REGNx, SW1x/SW2x (scope-probe friendly, with nearby GND), SDA, SCL, each I2CCx, IRQ_N.
- Links to isolate blocks: 0 Ω (0805) from 3V3 to each TPS25751 VIN_3V3 and to the MCU (R301); solder jumper R431/R531 from PACK_P to each TPS62933; a 10 A net-tie copper link (R430/R530) from PACK_P to each charger's battery side.
- Mounting holes ×6 (M3) and rubber feet or standoffs.

## Open items before ProtoFlow

- INA190A5 / INA190A1: decided 2026-10-11 to buy from DigiKey/Mouser and hand-solder (JLC stock too low)
- Confirm the CC2340R5MODA pin map in SysConfig when the firmware project is set up
