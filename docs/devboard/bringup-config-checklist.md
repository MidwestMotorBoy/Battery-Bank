# Bring-up and configuration checklist (rev A8, 2026-10-14)

This is the order of work from a bare assembled board to a configured pack. It gathers every configuration item from the four schematic reviews into one list:

- `schematic-review-2026-10-12.md`, "Firmware and configuration", items 1–14;
- `schematic-review-2-2026-10-12.md`, configuration items 1–17;
- `schematic-review-3-2026-10-14.md`, items C1–C5 and P1–P2;
- `schematic-review-4-2026-10-14.md`, the CONFIG items, A-2, S-1 and the B-1 gate-drive test;
- `mcu-io-power-states.md` (pin states per power state).

Where a later review corrected an earlier one, the corrected value is used here, and the source is marked. Rev A7 replaced the STM32WB1MMC with the TI CC2340R5MODA, so every MCU item below is for the CC2340.

## Board order (JLC)

- [ ] 6 layers, 1.6 mm, 2 oz outer / 0.5 oz inner, ENIG; set the real JLC 6-layer stack-up.
- [ ] Via covering: epoxy filled and capped (free on 6+ layers), for the via-in-pad under exposed pads.
- [ ] Minimum via 0.3 mm / (0.4/0.45 mm): JLC's standard; nothing on the board needs smaller.

## 0. Hand-fit and consigned parts (not in the JLC BOM)

- [ ] **U301 CC2340R5MODA:** buy from TI.com (CC2340R5MODAN0MHAR) and consign it to JLC for placement. JLC (C55046847) had no stock on 2026-10-14; check TI stock before ordering.
- [ ] U201 INA190A5 (DigiKey/Mouser). U202 INA190A1 is JLC-assembled.
- [ ] J301, the 2 × 5 1.27 mm SWD header: hand-fit. The Samtec FTSH-105 is to be replaced by an unkeyed header JLC stocks; the silkscreen then shows pin 1 and the cable-key side.
- [ ] Two 2.54 mm shunts (JP201, JP202).
- [ ] Pin headers, hand-soldered since the 2026-10-14 cost-down: J102–J107, J302, J303, J402, J502, JP201, JP202 (PZ254V-11, part numbers in each part's `Sourcing` property).
- [ ] Wired NTCs on J102, J105–J107, insulated, taped to BT101–BT104.

## 1. First power, no cells

1. [ ] Bench supply on J104: **current-limited (≤ 0.5 A), 12–16 V**. It feeds PACK_P through D104, so expect about a 0.4 V drop. D105 (SMAJ18A) clamps a supply left above about 22 V; it is a crowbar, so a high current limit will cook it (review 4 D-5).
2. [ ] Check 3V3 at TP301 and PG_3V3 at TP205. 3V3_SLEEP (TP307) should read about 3 V (R313 220k holds the TPS62177 in normal mode while U301 is unprogrammed). Do not plug in USB yet.
3. [ ] **Debug probe:** the onboard XDS110 of an LP-MSPM0G3519 LaunchPad. Pull the NRST/SWDIO/SWCLK (and TXD/RXD) jumpers on its J101, then run a 10-pin 1.27 mm cable from its J102 (XDS110 side) to our J301. Check whether its J102 pin 1 drives XDS 3.3 V onto 3V3_MCU before plugging in. UART logs: jumper wires from the LaunchPad's XDS-side TXD/RXD to J302, only with our 3V3 up (R322/R323 limit back-power, but don't rely on them).
4. [ ] **CCFG before the first flash (review 4 A-1, blocking).** DIO21 (3V3_SLEEP) is the default ROM-bootloader trigger pin, active low, in the SDK's default CCFG ("Default FCFG bootloader"). Firmware drives it low in S2, so with the default a reset from S2 can strand the MCU in the bootloader. In SysConfig, choose a bootloader setting without the DIO21 pin trigger (or move the trigger to a pin that is high in every state), then flash over J301. Since rev A5, an unprogrammed MCU blocks USB charging (CHG_INH defaults to inhibit).
5. [ ] **WDT:** the CC2340 watchdog can't be stopped once enabled and runs in active, idle and Standby. Confirm how it behaves with the debugger halted (a halted target gets reset).

## 2. Cells in, gauge woken and configured

Rules:
- Fit the cells before USB (silkscreen). Never attach USB with no cells.
- **Never insert or remove a cell with USB or J104 power on.** An empty holder slot sees PACK_P minus the other cells (more than 4.35 V), U102 trips after 1–2 s and F102 blows for good (review 3, P1; gauge sheet note 15).
- **EV2400 work only with 3V3 up (review 4 A-2).** An unpowered CC2340 can't take bus voltage on SCL/SDA (VDDS + 0.3 V abs max): with 3V3 down, even the EV2400's own 20k pull-ups would push current into it and half-power the 3V3 rail during a data-flash write. Keep R312 fitted, never feed TP308 with 3V3 down, and never remove R301 with 3V3 up.

1. [ ] Turn J104 off, then insert BT101–BT104.
2. [ ] Check each cell at TP102–TP105 and the stack at TP108 (CELL_P_RAW). Every cell should be 2.5–4.25 V, and none reversed. Q101/Q102 stay off on a fresh gauge (`Manufacturing Status Init` = 0x0000, FET_EN off), so nothing loads the cells yet.
3. [ ] Wake the gauge with SW101 (hold about 0.5 s).
4. [ ] **Power 3V3 from J104** (current-limited, 12–16 V): the FETs are still off, so J104 is the only way to get 3V3 up. Hold U301 in reset (SW301 held, or the J301 nRESET line low from the probe) for the whole EV2400 session, so the MCU stays off the bus. Then connect the EV2400 to J103: 1 VSS, 2 SCL, 3 SDA.
5. [ ] Gauge data flash (TRM SLUUBK0B). **Set all of these before FET enable:**

| Setting | Value | Why / source |
|---|---|---|
| `DA Configuration` cell count | **4S** | factory default is 3S (0x12) |
| **`DA Configuration[NR]`** | **1** (non-removable / embedded pack) | PRES is tied to VSS, so with the default [NR] = 0 a latched protection could only clear on a PRES transition that never happens (review 4 D-1) |
| **Latch Limits** (COV, OCD, AOLD, ASCC, ASCD) | **explicit, non-zero** (for example 2–3) | the defaults are 0, and the TRM doesn't say whether 0 means "disabled" or "latch on the first trip" (review 4 D-1) |
| Chemistry | EVE INR21700-58E | review 1 item 4 |
| TS1–TS4 | all enabled; protections use the maximum | rev A4 per-cell NTCs |
| Internal temperature sensor | enabled, with OTD/OTC protection | FET over-temperature (U306 is the DNP fallback) |
| COV / CUV | COV ≤ 4.25 V; CUV and terminate voltage set so 100 W never runs below **2.8 V/cell under load** | F102's 15 A element is the only fuse (review 2, D3; F101 deleted) |
| **COV Delay** | **1 s** (default 2 s) | U102 trips after 1–2 s; on a step overvoltage the gauge must open CHG first (review 3, C2) |
| OCC1 | about 6 A, short delay | review 1 item 14 |
| OCD1 | about 10–11 A (welded pack); 2–3 A in holder mode | review 1 item 4 |
| **OCD2** | **about 12–13 A for 1–2 s** | the default of 8 A for 3 s trips a single 100 W port at low pack voltage (review 2, M-B1) |
| OLD (AOLD) | about 16–20 A | review 1 item 4 |
| SCD1 delay | the shortest that does not nuisance-trip: the FETs must open a hard short before F102 has to break it (F102 interrupts only 50 A; a short can reach about 185 A) | review 2, A N-2; review 3, D2 |
| **Min Blow Fuse Voltage** | **10500 mV** (default 3500 mV) | WSFB1514 heater works only from 10.5–19.6 V (review 3, C1) |
| `FET Options[PACK_FUSE]` | 0 | F102 is on the battery side, so the stack voltage is checked |
| Fuse / permanent fail | enable the FUSE pin action ([FUSE_EN]), the second-level protector input (2LVL) and the chosen permanent fails | README item 33 |
| **Precharge Start Voltage** | **2500 mV** (keep the default) | **replaces review 1's "0 mV"**: it is the only non-MCU block on charging a reversed or dead cell (review 2, A-3, major) |
| **Charging Voltage Low** | **≤ 2500 mV** | the default of 2900 mV would block USB recovery after a CUV trip (review 2, A-3) |
| `FET Options[PCHG_COMM]` | 0 | no precharge FET on this board; the 0-V charging circuit stays off |
| SUV permanent fail | consider enabling (2.2 V for 5 s) | review 2, A-3 |
| SOCD | keep disabled, or above the 100 W discharge current | review 2, A-3 |
| VIMR / VIMA | enabled | review 1 item 4 |
| Sleep current threshold | above the ±10 mA coulomb-counter offset | review 1 item 4 |
| **Shutdown Voltage** | **2700 mV** (default 1750 mV); keep Shutdown Time at 10 s | after a CUV trip the gauge and U102 keep drawing 75–336 µA from the cells. With the default it shuts down only at 1.75 V/cell, deep in over-discharge. 2700 mV stays below CUV so CUV still trips first (review 4 follow-up, S-1) |
| `[IN_SYSTEM_SLEEP]` | 1 | the bus idles high, so without it the gauge never sleeps (336 µA instead of 75 µA). With [NR] = 1 its effect is not stated in the TRM: confirm the gauge sleeps at bring-up, or have the MCU send MAC 0x0011 SLEEP |
| **`[XL]`** | **0** (SMBus 100 kHz, the default) | the shared bus runs at 100 kHz: its rise time (3.3k, about 100 pF) rules out 400 kHz (review 4 A-6, D-7) |
| **BTP** | **BTP_EN = 0**, or **BTP_POL = 1** whenever BTP_EN = 1 | with the default polarity BTP_INT idles high, Q103 holds the shared IRQ_N low and masks every other interrupt; BTP also stays latched until the host clears it (review 4 D-2) |
| `[BCAST]` | 0 | review 2, C-16 |
| OCD / OCC recovery delays | short | body-diode heating (review 1, decision Q1) |

6. [ ] Read the configuration back and compare it to this table.
7. [ ] Only then send **FET enable**. Check PACK_P at TP106. Release U301's reset.
8. [ ] **Latch recovery test:** with a current-limited supply, short PACK_P briefly and confirm the gauge recovers after its reset time ([NR] = 1). If a latch does set, firmware sends DeviceReset (MAC 0x0041) at boot when it finds one.

## 3. PD controller EEPROMs (TPS25751, one bundle per port)

The two ports have separate EEPROMs, so use per-port bundles (review 2, M-B3). See also `docs/project/tps25751-eeprom-programming.md`.

- [ ] **Default source PDOs:** USB1 up to 100 W, USB2 20–30 W, so the "80 + 20 W" rule holds without the MCU. If a single bundle is used, 60 W or less per port (review 2, A-1). **Until the B-1 gate-drive test passes, cap 20 V PDOs at 2.5 A** (reverse output is limited to about 57 W by IBAT_REV = 5 A).
- [ ] PPHV soft-start: setting 0 or 1 (port sheet note 9).
- [ ] `DIS_CE_PIN` = 0 (CHG_INH must keep control of CE).
- [ ] Charger set-up written by the bundle (BQ25756 over I2Cc):
  - [ ] VFB_REG = 0x0F (16.80 V; the power-on value regulates 16.70–16.96 V, so it must be written). Consider 0x0E if samples measure high (review 4 B-9).
  - [ ] ICHG_REG = 2.8 A at start.
  - [ ] EN_ICHG_PIN = 1.
  - [ ] EN_CHG_BIT_RESET_BEHAVIOR = 0.
  - [ ] IPRECHG ≈ 0.5 A.
  - [ ] ITERM = 0.25 A.
  - [ ] **EN_PFM = 0** (ITERM < 2 A).
  - [ ] **IBAT_REV = 5 A (11b) until the B-1 gate-drive test passes**, then 10 A (default 20 A).
  - [ ] **TS_T5 = 00b** (about 81 °C) and **BHOT = 00b**, so the X5R MLCCs stay within 85 °C (review 2, B-2). TH401/TH501 must sit on the Q402/Q407 copper for this to protect the FETs (review 4 B-2).
  - [ ] **EN_JEITA = 0 (mandatory).** The NTC is on the FETs, not the cells: with JEITA on, the charger drops to 20 % current below about 19 °C board temperature and needs about 24 °C to leave (review 4 B-8). T1/T5 stay active.
  - [ ] **Q12: INDPM margin 0–5 %** (IAC_DPM tracks the contract current) and **Q13: VINDPM 5 % below the contract voltage**. Without them the only input limit is ILIM_HIZ (5.3–5.8 A), which overloads a 9 V 3 A source (review 4 C-11). Read registers 0x06/0x08 back over J402 after a 9 V 3 A contract.
  - [ ] Watchdog: confirm something services it. Otherwise sourcing drops every 40 s and ICHG_REG returns to 20 A (review 2, B-11).
- [ ] **Interrupts (review 4 C-10):** unmask PlugInsertOrRemoval, LiquidDetection [60] and the fault events in INT_MASK1 in each bundle. INT_EVENT1 resets to 0x08, so IRQ_N can be low straight after boot.
- [ ] After a start where VBUS arrived before 3V3, the MCU clears the dead-battery flag (DBfg).
- [ ] Liquid detection and GPIOs (README items 35–36; review 3, C3–C5):
  - [ ] GPIO6 = LIQUID_PMOS_CONTROL (155), GPIO7 = LIQUID_NMOS_CONTROL (156). TI's EVM guide contradicts itself on this mapping; go by the event names.
  - [ ] GPIO3 = Fault_Input_Event (33), from the TPD4S201 FLT (SBU_FLT).
  - [ ] GPIO4/5 multiplexed to the ADC. BC1.2 off.
  - [ ] **Liquid Detection Configuration (0x98):** liquid detection and corrosion mitigation on. **Compute the thresholds for our Rup 100 kΩ / Rdown 1 MΩ** (14 mV/LSB), with ≥ 0.5 V margin below the worst-case dry reading of 2.87 V. That reading allows for the TPD4S201 SBU leakage (≤ 3.2 µA), GPIO leakage (1 µA) and LDO_3V3 sag during an attach. The tool's defaults come from TI's EVM (Rup 249 kΩ), so check them before flashing (review 4 C-9).
  - [ ] Unmask the Liquid Detection event.
  - [ ] GPIO0–2 and GPIO11 stay inputs: they are tied to GND.

## 4. MCU firmware (CC2340R5MODA)

Pin states per power state are in `mcu-io-power-states.md`. Pins: DIO6 SCL, DIO8 SDA, DIO18 UART TX, DIO20 UART RX, DIO12 LED, DIO24 CHG_INH, DIO3 EN_5V1, DIO4 EN_5V2, DIO21 3V3_SLEEP, DIO11 IRQ_N, DIO16/DIO17 SWD. No spares.

- [ ] **Boot order:**
  1. Restore EN_5V1/EN_5V2 from retained state as the very first action after any reset, before the BLE stack starts. The PP5V bulk holds the attached Rp for only about 16 ms at 5 mA, so a 20 V contract can then ride through a watchdog reset (review 4 C-6, A-8).
  2. Drive DIO21 (3V3_SLEEP) high.
  3. I2C0 on DIO6 (mux 2) / DIO8 (mux 4), **100 kHz**, internal pulls off. Clock 9 SCL pulses first (bus clear: the TPS25751s saw SCL/SDA low while 3V3 was down). Allow gauge clock stretching (SMBus, up to 25 ms).
  4. Configure every TMP1075 (0x48–0x4C): TM = 1 (interrupt mode), the wanted THIGH/TLOW, unused limits at the rails (TLOW −128 °C, THIGH +127.9375 °C). Their power-up default is comparator mode at 80 °C, which would hold IRQ_N low while a stage is hot (review 4 A-3).
  5. Read and clear INT_EVENT1 on 0x20 and 0x21 (write INT_CLEAR1); clear the gauge BTP if it is used (review 4 C-10).
  6. Check CHG_INH conditions (supervision below) before ever driving DIO24 low.
- [ ] **IRQ_N (DIO11) rules (review 4 A-3):** input, internal pull **off** (the internal pull-up would draw about 200 µA while IRQ_N is asserted); falling-edge wake.
  - [ ] The interrupt handler reads and clears all seven sources (2 × TPS25751, gauge BTP, TMP1075s; the TMP1075s answer the SMBus Alert Response Address 0x0C) and loops until DIO11 reads high, then re-checks the level.
  - [ ] Never enter Standby with DIO11 low. If a source can't be cleared, fall back to RTC polling and log which source is stuck.
- [ ] **TMP1075 modes per state (review 4 A-4):** S2 idle: shutdown (SD = 1), no hardware alert, as the stages are cool with no cable. S0/S1: continuous at R = 11 (220 ms) with TM = 1 and the derating THIGH, so ALERT still protects if firmware stalls.
- [ ] **CHG_INH (DIO24):** drive it low only while a port is charging and all checks pass; drive it high otherwise. Low costs 138 µA. CC2340 Standby **keeps** GPIO states, so a low CHG_INH keeps charging in Standby: only enter Standby while charging if the supervision keeps running (RTC wake). Reset, WDT reset, the ROM bootloader and an unprogrammed MCU all inhibit (pins float, R417/R517 pull CE up).
- [ ] **Supervision (review 1 item 12).** Inhibit charging when any of these happens:
  - [ ] the gauge stops answering for about 2 s;
  - [ ] the gauge's read-back configuration is wrong;
  - [ ] the gauge stack voltage, the sum of its cells and the chargers' VBAT disagree by more than 300 mV;
  - [ ] any cell is outside 2.5–4.25 V;
  - [ ] a FET is stuck on.
- [ ] **Charge sharing:** one port charging gets the full rate (5.5 A, "fast charge"); on the other port's attach it drops back to 2.8 A. While XDSG = 1, hold the precharge level.
- [ ] **Source sharing:** lower USB1's offer when USB2 attaches. Gate EN_5Vx on four valid cells and both FETs on. EN_5Vx gates PP5V, and every new source attach needs PP5V (vSafe5V, attached Rp, VCONN), so sourcing at any voltage depends on the MCU (review 4 C-6).
- [ ] **WDT:** about 2 s while charging or sourcing, longer in idle with an RTC wake to service it. Service it only from the supervision loop. It can't be stopped once enabled. Count resets.
- [ ] **Sleep (S2):**
  - [ ] Standby with BLE advertising; GPIOs latch.
  - [ ] Enter TPS62177 sleep mode (DIO21 low) only with no cable attached. In sleep mode keep the LED off and TX power at ≤ +4 dBm, and leave sleep mode on any IRQ_N edge: the sleep-mode limit is 15 mA (review 4 D-4).
  - [ ] Drive DIO21 high before Shutdown or a deliberate reset (it latches).
- [ ] **Pins:** DIO12 LED with high drive (about 3.6 mA); DIO20 UART RX with the internal pull-up; DIO3/DIO4 stay GPIO, never enable LFXT; LFCLK from LFOSC with the Power driver's compensation on (review 4 A-8).
- [ ] **FET temperature:** include the gauge internal sensor's reading in the firmware over-temperature limits. At 100 W (about 1 W per protection FET), compare it with a thermocouple on Q101/Q102. If it lags badly, fit U306 (DNP TMP1075 between them).
- [ ] **Port-to-itself cable loop:** detect it and stop (review 2, B-12).
- [ ] **Ship mode (storage, review 4 follow-up S-1, decided 2026-10-14).** Ship mode opens the gauge FETs and puts the gauge in SHUTDOWN, so the pack drains about 3–4 µA instead of about 240 µA in idle.
  - [ ] **Entry triggers:**
    - [ ] an app command over BLE;
    - [ ] two weeks with no cable attached and no button press;
    - [ ] low state of charge. The RSOC threshold is still to be chosen (about 5 % suggested); it must sit above the CUV point.
  - [ ] **How:** send the gauge SHUTDOWN command (MAC 0x0010), then let the rail collapse. Before sending it, release CHG_INH and drop EN_5Vx.
  - [ ] **Refuse with a cable attached:** while USB holds PACK_P up, the gauge never completes SHUTDOWN. Make the app command report "unplug first", and restart the 2-week timer on every attach.
  - [ ] **Wake:** a USB charger plug-in or SW101. A phone plugged into a sleeping board does not wake it; that is expected for a power bank, so say so in the app and docs.

## 5. Bring-up measurements

- [ ] A phone attaching is detected with EN_5Vx low (idle). If not, keep EN_5Vx high in idle and raise R432/R532 to 1 MΩ.
- [ ] The 3V3 rail survives an attach while the TPS62177 is in sleep mode (15 mA limit): scope 3V3 during an attach. It may dip to about 2.87 V (PG fallback) and recover; decide then whether to stay in normal mode while a cable could attach (about +5 µA).
- [ ] Capture J402 (I2Cc): does the bundle rewrite ICHG_REG, IAC_DPM and VAC_DPM on every attach?
- [ ] Bootstrap diodes D404/D405, the protection FETs (about 1 W each at 100 W) and the discrete charger FETs Q401/Q402/Q407/Q408 (and 5xx; about 1–1.6 W each at 100 W reverse from a 12 V pack, review 4 B-2): measure their temperature.
- [ ] Battery-side MLCCs C431/C434/C435 (and 5xx): temperature at the worst ripple point, reverse buck to 9 V 3 A (about 1.5 A rms).
- [ ] Polymer leakage: C432/C532 sit on PACK_P permanently, with a datasheet limit of 500 µA each; measure the pack drain with the FETs on (review 4 B-4).
- [ ] Holder contact resistance (accepted risk, 100 mΩ maximum per holder; review 1 #4): measure each holder. Holder mode stays at about 2 A (ICHG_REG, PDOs, OCD1 2–3 A). Run high-current tests and gauge learning on the welded pack via J101.
- [ ] Sleep current: R_MEAS for the 3V3 branch, the gauge's current reading for the pack. Expect about 400 µA on 3V3 in idle and about 240 µA from the pack (`power-budget.md`).
- [ ] **Ship mode:**
  - [ ] Send the app command (or MAC 0x0010 from the EV2400) with no cable attached. PACK_P (TP106) falls and the board goes dark.
  - [ ] Pack drain is about 3–4 µA: R105 reads about 0.2 mV or less, and the gauge current is 1.6 µA plus U102 at 1–2 µA.
  - [ ] It wakes on a USB charger and on SW101, and does not wake on a phone.
- [ ] **Storage:** store boards at 40–60 % charge, in ship mode. EVE rates 1 year at −20 to 25 °C at shipping charge (3.4–3.6 V per cell).
- [ ] Gauge supply current: with the pack on battery only (no USB, no J104), measure across R105 (100 Ω): 50–340 µA = 5–34 mV. Expect about 75 µA once the gauge sleeps; about 336 µA means it is not sleeping. Budget about 150 µA.
- [ ] BLE range with the module at the board edge (the CC2340 footprint carries TI's 7.0 × 3.2 mm antenna keep-out; keep the GND planes solid along the top edge either side). Retune the match (C313–C315, R321) if needed.
- [ ] F102 intact: TP108 (CELL_P_RAW) and TP101 (CELL_P) within a few mV.
- [ ] Liquid detection: scope LIQ_PU/LIQ_PD (TP420/TP421) to confirm the GPIO6/7 mapping. Then put salt water across SBU–GND and SBU–VBUS in the receptacle: the port must report liquid and turn VBUS off (SBU–VBUS goes through the FLT path, TP417). Then dry it and confirm recovery.
- [ ] Liquid-detection current: R201 current with liquid detection on and off (review 3, P2).
- [ ] **High-side gate drive at 100 % duty (review 4 B-1, follow-up).** The BQ25756 holds one high side fully on in each direction and keeps its gate up with an undocumented internal charge pump. TI E2E documents the pump; its voltage and current are unpublished.
  - [ ] **Q402/Q502 (HIDRV2–SW2):** reverse boost, pack to 20 V at full load (start at the interim IBAT_REV = 5 A, then the final limit), with the board hot (70–80 °C at the FETs).
  - [ ] **Q401/Q501 (HIDRV1–SW1):** forward boost from a 5 V and a 9 V source at full charge current.
  - [ ] **How:** differential or isolated probe across gate and source (SW). Record the minimum gate voltage over several seconds, and whether it sawtooths down to the 2.7–3.9 V refresh threshold.
  - [ ] **Pass:** the gate stays at 4.5 V or more, and the FET case temperature agrees with the B-2 loss estimate (about 1–1.6 W per FET at 100 W).
  - [ ] **Fail:** swap that position to the review's fallback part (AON7520 for Q402/Q502, SiS488DN for Q401/Q501; same footprint). Keep IBAT_REV at 5 A until then.
  - [ ] Keep the high-side gates free of pull-down resistors (TI: the pump can't drive them).
- [ ] **VBUS short while sourcing (review 4 C-7):** current-limited short at 20 V; the PPHV switch has no current clamp, so confirm VBUS-UVLO and the BQ25756 reverse undervoltage stop it, and that ACP−ACN stays within ±0.3 V.
- [ ] **PP5V headroom (review 4 C-5):** 3 A resistive load on a 5 V contract plus a VCONN load on CC; the TPS62933 valley limit allows about 3.2–3.5 A.
- [ ] **VBUS clamp:** a live 20 V hot-plug on each port with a scope on VBUS (TVS2200 clamps at 28 V max at 40 A).
- [ ] Switching edges: probe SW1/SW2 ringing at full load. If needed, put a few ohms (≤ 4.7 Ω) in R444–R449 or fit the R450/C454 and R451/C455 snubbers (R is 1206 0.66 W; size C from the measured ring).
