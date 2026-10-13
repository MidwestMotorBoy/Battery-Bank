# Bring-up and configuration checklist (rev A5, 2026-10-13)

This is the order of work from a bare assembled board to a configured pack. It gathers every configuration item from both schematic reviews into one list:

- `schematic-review-2026-10-12.md`, "Firmware and configuration", items 1–14;
- `schematic-review-2-2026-10-12.md`, configuration items 1–17;
- `mcu-io-power-states.md`.

Where review 2 corrected review 1, the corrected value is used here, and the source is marked.

## 0. Hand-fit parts (not in the JLC BOM)

- [ ] U301 STM32WB1MMC (out of stock at LCSC).
- [ ] U201/U202 INA190 (DigiKey/Mouser).
- [ ] J301 Samtec FTSH-105-01-L-DV-K (keyed shroud).
- [ ] J201/J202 SMA.
- [ ] Two 2.54 mm shunts (JP201, JP202).
- [ ] Wired NTCs on J102, J105–J107, insulated, taped to BT101–BT104.

## 1. First power, no cells

1. [ ] Bench supply on J104: current-limited, about 12–16 V. It feeds PACK_P through D104, so expect about a 0.4 V drop.
2. [ ] Check 3V3 at TP301 and PG_3V3 at TP205. Do not plug in USB yet.
3. [ ] Flash the MCU over J301. Since rev A5, an unprogrammed MCU blocks USB charging (CHG_INH defaults to inhibit).
4. [ ] Set the MCU option bytes: IWDG_SW = 0, IWDG_STOP = 1, IWDG_STDBY = 1 (review 2, item 15).

## 2. Cells in, gauge woken and configured

Rule: fit the cells before USB (silkscreen). Never attach USB with no cells.

1. [ ] Insert BT101–BT104.
2. [ ] Check each cell at TP102–TP105 and the stack at TP108 (CELL_P_RAW). Every cell should be 2.5–4.25 V, and none reversed. Q101/Q102 stay off on a fresh gauge (`Manufacturing Status Init` = 0x0000, FET_EN off), so nothing loads the cells yet.
3. [ ] Wake the gauge: SW101 (hold about 0.5 s), J104, or USB.
4. [ ] Connect the EV2400 to J103: 1 VSS, 2 SCL, 3 SDA. Release the MCU's I2C or hold the MCU in reset (review 1 item 9). With 3V3 down, remove R312 and feed TP308.
5. [ ] Gauge data flash (TRM SLUUBK0B). **Set all of these before FET enable:**

| Setting | Value | Why / source |
|---|---|---|
| `DA Configuration` cell count | **4S** | factory default is 3S (0x12) |
| Chemistry | EVE INR21700-58E | review 1 item 4 |
| TS1–TS4 | all enabled; protections use the maximum | rev A4 per-cell NTCs |
| COV / CUV | COV ≤ 4.25 V; CUV and terminate voltage set so 100 W never runs below **2.8 V/cell under load** | F101 = 15 A (review 2, D3) |
| OCC1 | about 6 A, short delay | review 1 item 14 |
| OCD1 | about 10–11 A (welded pack); 2–3 A in holder mode | review 1 item 4 |
| **OCD2** | **about 12–13 A for 1–2 s** | the default of 8 A for 3 s trips a single 100 W port at low pack voltage (review 2, M-B1) |
| OLD (AOLD) | about 16–20 A | review 1 item 4 |
| SCD1 delay | short enough to clear a hard short before F101 melts (about 0.5 ms at 185 A) | review 2, A N-2 |
| **Precharge Start Voltage** | **2500 mV** (keep the default) | **replaces review 1's "0 mV"**: it is the only non-MCU block on charging a reversed or dead cell (review 2, A-3, major) |
| **Charging Voltage Low** | **≤ 2500 mV** | the default of 2900 mV would block USB recovery after a CUV trip (review 2, A-3) |
| `FET Options[PCHG_COMM]` | 0 | no precharge FET on this board; the 0-V charging circuit stays off |
| SUV permanent fail | consider enabling (2.2 V for 5 s) | review 2, A-3 |
| SOCD | keep disabled, or above the 100 W discharge current | review 2, A-3 |
| VIMR / VIMA | enabled | review 1 item 4 |
| Sleep current threshold | above the ±10 mA coulomb-counter offset | review 1 item 4 |
| `[IN_SYSTEM_SLEEP]` | 1 | the bus idles high, so without it the gauge never sleeps (336 µA instead of 75 µA) |
| `[BCAST]` | 0 | review 2, C-16 |
| OCD / OCC recovery delays | short | body-diode heating (review 1, decision Q1) |

6. [ ] Read the configuration back and compare it to this table.
7. [ ] Only then send **FET enable**. Check PACK_P at TP106.

## 3. PD controller EEPROMs (TPS25751, one bundle per port)

The two ports have separate EEPROMs, so use per-port bundles (review 2, M-B3). See also `docs/project/tps25751-eeprom-programming.md`.

- [ ] Default source PDOs: USB1 up to 100 W, USB2 20–30 W, so the "80 + 20 W" rule holds without the MCU. If a single bundle is used, 60 W or less per port (review 2, A-1).
- [ ] PPHV soft-start: setting 0 or 1 (port sheet note 9).
- [ ] `DIS_CE_PIN` = 0 (CHG_INH must keep control of CE).
- [ ] Charger set-up written by the bundle (BQ25756 over I2Cc):
  - [ ] VFB_REG = 0x0F (16.80 V).
  - [ ] ICHG_REG = 2.8 A at start.
  - [ ] EN_ICHG_PIN = 1.
  - [ ] EN_CHG_BIT_RESET_BEHAVIOR = 0.
  - [ ] IPRECHG ≈ 0.5 A.
  - [ ] ITERM = 0.25 A.
  - [ ] **EN_PFM = 0** (ITERM < 2 A).
  - [ ] **IBAT_REV = 10 A** (default 20 A).
  - [ ] **TS_T5 = 00b** (about 81 °C) and **BHOT = 00b**, so the X5R MLCCs stay within 85 °C (review 2, B-2).
  - [ ] EN_JEITA = 0, or set TS_T2/JEITA_ISETC to suit (review 1 item 2).
  - [ ] Watchdog: confirm something services it. Otherwise sourcing drops every 40 s and ICHG_REG returns to 20 A (review 2, B-11).
- [ ] After a start where VBUS arrived before 3V3, the MCU clears the dead-battery flag (DBfg).

## 4. MCU firmware

Pin states per power state are in `mcu-io-power-states.md`.

- [ ] **CHG_INH (PB8):** drive it low only while a port is charging and all checks pass; drive it high otherwise. Low costs 138 µA. Re-check after every reset before driving it low. Use Stop0–2, never Standby.
- [ ] **Supervision (review 1 item 12).** Inhibit charging when any of these happens:
  - [ ] the gauge stops answering for about 2 s;
  - [ ] the gauge's read-back configuration is wrong;
  - [ ] the gauge stack voltage, the sum of its cells and the chargers' VBAT disagree by more than 300 mV;
  - [ ] any cell is outside 2.5–4.25 V;
  - [ ] a FET is stuck on.
- [ ] **Charge sharing:** one port charging gets the full rate (5.5 A, "fast charge"); on the other port's attach it drops back to 2.8 A. While XDSG = 1, hold the precharge level.
- [ ] **Source sharing:** lower USB1's offer when USB2 attaches. Gate EN_5Vx on four valid cells and both FETs on.
- [ ] **IWDG:**
  - [ ] Timeout about 2 s while charging or sourcing, about 16 s in idle, with an RTC wake-up about every 8 s.
  - [ ] Refresh only from the supervision loop.
  - [ ] Freeze it in debug (DBGMCU).
  - [ ] Count resets.
- [ ] **Sleep:**
  - [ ] Stop2 only.
  - [ ] PB4 goes high first on every wake.
  - [ ] Enter TPS62177 sleep mode only with no cable attached.
  - [ ] NTC_EN high only while sampling; wait 5 ms or more after raising it.
- [ ] **Port-to-itself cable loop:** detect it and stop (review 2, B-12).

## 5. Bring-up measurements

- [ ] A phone attaching is detected with EN_5Vx low (idle). If not, keep EN_5Vx high in idle and raise R432/R532 to 1 MΩ.
- [ ] The 3V3 rail survives an attach while the TPS62177 is in sleep mode (15 mA limit).
- [ ] Capture J402 (I2Cc): does the bundle rewrite ICHG_REG on every attach?
- [ ] Bootstrap diodes D404/D405 and the protection FETs (about 1 W each at 100 W): measure their temperature.
- [ ] Holder contact resistance (accepted risk, 100 mΩ maximum per holder; review 1 #4): measure each holder. Holder mode stays at about 2 A (ICHG_REG, PDOs, OCD1 2–3 A). Run high-current tests and gauge learning on the welded pack via J101.
- [ ] Sleep current: R_MEAS for the 3V3 branch, the gauge's current reading for the pack. Budget about 150 µA.
- [ ] BLE range with the module at the board edge (antenna keep-out `ANT_KEEPOUT` on all copper layers).
