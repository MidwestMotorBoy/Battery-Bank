# CC2340R5MODA pin budget (2026-10-14; in the schematic as rev A7)

> **Update 2026-10-17 (rev A8):** the TMP1075 sensors below were removed again. The gauge reports cell and FET temperatures, and the MCU reads each charger's NTC through the TPS25751 `I2Cr` pass-through (`circuit-description.md` §6). The pin map is unchanged.

This document checks whether the CC2340R5MODA module can replace the STM32WB1MMC (U301) as a cost-down. The plan below is in the schematic as rev A7 (`hardware/DevBoard/README.md` item 40). Its source is the module datasheet (`datasheets/cc2340r5moda.pdf`, SWRS349A, July 2026). The signal list comes from `mcu-io-power-states.md`.

## The problem: 12 GPIOs for 20 signals

The module brings out **12 DIOs**: DIO3, 4, 6, 8, 11, 12, 16, 17, 18, 20, 21 and 24. Of these:

- Two are SWD (DIO16 and DIO17). That leaves **10 for the board**.
- Only **4 are analog** (DIO6, DIO20, DIO21 and DIO24), and the board has **5 NTCs**.
- I2C SCL can go on pin 9 (DIO6) or pin 11 (DIO24), or pin 19 (DIO17, but that is SWDCK). Both usable ones are analog pins, so the I2C bus costs one of the four ADC inputs.
- DIO3 and DIO4 double as the 32 kHz crystal pins. We don't fit a 32 kHz crystal. The internal LFOSC, calibrated against the 48 MHz crystal, is fine for BLE, so both stay GPIOs.

The current design uses **18 signals plus SWD**:

| Group | Signals | Count |
|---|---|---|
| I2C | SCL, SDA | 2 |
| Interrupts | IRQ1, IRQ2, GAUGE_BTP | 3 |
| Outputs | CHG_INH, EN_5V1, EN_5V2, NTC_EN, 3V3_SLEEP, LED_DRV | 6 |
| Analog | NTC_TH1 to TH5 | 5 |
| UART | TX, RX | 2 |

That is 8 signals short. No rearrangement fixes this without circuit changes.

## Proposed fix: two changes, no extra ADC

1. **Replace the five NTCs with three TMP1075 I2C temperature sensors** (WSON-8 2 × 2 mm with exposed pad, or VSSOP-8). The NTCs need five ADC pins; on I2C, temperature sensing needs no MCU pins at all.

   **What already watches temperature without the MCU:**
   - **Cells:** the gauge's TS1 to TS4, one NTC per cell. The gauge opens its FETs itself on over-temperature.
   - **Each charger power stage:** the BQ25756 TS pin, with its own NTC beside that port's FETs. Charging stops at about 95 °C in hardware. This is a hard stop, though, not a reading the MCU can use to throttle.
   - **Gauge die:** the BQ40Z50 internal sensor. It can trip OTD and is readable over SMBus.

   **What the MCU still has to measure.** These are the gaps:

   | Sensor | Replaces | Where | Why it's kept |
   |---|---|---|---|
   | T1 | TH301 | Port 1 power stage (Q402/L401), pad on PGND copper | Firmware needs a reading to throttle to 20 W well before the BQ25756's 95 °C hard stop |
   | T2 | TH302 | Port 2 power stage (Q502/L501) | Same, for port 2. The stages are 36 mm apart, too far for one shared sensor |
   | T3 | TH303 | Between the USB-C connectors, pad on GND copper (TH303 sat on VBUS) | Nothing else watches the connectors. A worn or dirty plug at 5 A is the classic power-bank failure |

   **Dropped:**
   - **TH304, heatsink position:** this repeats T1 and T2. On production, the plate sits over the same stages they measure.
   - **TH305, protection FETs (Q101/Q102):** use the gauge's internal sensor and enable OTD. A-findings already named this as the fallback.
     - Today U101 sits 11 to 19 mm from Q101/Q102. Move it closer if layout allows.
     - **This reverses review 2 item H8.** The user approved it on 2026-10-14. If bring-up shows the gauge die lags the FETs badly, fit the DNP T5 footprint (below).

   **Details:**
   - **Keep DNP footprints for T4 and T5** at the old TH304/TH305 spots. On I2C they cost no MCU pins, so the dev board can still measure there if bring-up calls for it.
   - **Addresses:** T1 to T5 strap to 0x48 to 0x4C (A0, A1 and A2 tied to GND or 3V3). They don't clash with the gauge (0x0B) or the TPS25751s (0x20, 0x21).
   - **What gets removed:** NTC_EN, five 10k dividers, five 100 nF caps and all five analog pins.
   - **Idle current:** firmware keeps the sensors in shutdown and wakes them for one-shot readings. That's 0.37 µA typical each, about 1 µA for three in S2.
   - **Accuracy:** ±1 °C max from −40 to 75 °C and ±2 °C max up to 125 °C (DSG package, §6.5), so ±2 °C in the 80–95 °C derating band: enough for derating limits.
   - **Optional:** each TMP1075 has an open-drain ALERT output with a programmable trip point. Wire-ORing them onto IRQ_N (below) gives a hardware over-temperature interrupt that works even while firmware sleeps.
2. **Wire-OR the three interrupts onto one pin.** IRQ1, IRQ2 and GAUGE_BTP are all open-drain, active-low and pulled up by 100k, so they can share one net, IRQ_N. Keep R314 as the only 100k pull-up; R315 and the gauge's R114 become DNP.
   - On a falling edge, firmware reads both TPS25751 INT_EVENT registers and the gauge status to find the source.
   - The cost is one extra I2C read per interrupt, which is negligible.

With both changes, the board needs exactly 10 MCU pins:

| Module pin | DIO | Signal | Why this pin |
|---|---|---|---|
| 9 | DIO6 | SCL | One of only two SCL options (I2C0) |
| 10 | DIO8 | SDA | SDA option that isn't SWD |
| 16 | DIO18 | UART TX (J302) | UART0 TX option |
| 17 | DIO20 | UART RX (J302) | UART0 RX option |
| 11 | DIO24 | CHG_INH | High-drive; safe at reset via the existing pull-ups |
| 18 | DIO12 | LED_DRV | High-drive |
| 12 | DIO3 | EN_5V1 | 100k pull-down keeps it off at reset |
| 13 | DIO4 | EN_5V2 | 100k pull-down keeps it off at reset |
| 15 | DIO21 | 3V3_SLEEP | Comparator-capable pin, otherwise unused |
| 21 | DIO11 | IRQ_N | Wake-from-standby interrupt |
| 19 / 20 | DIO17 / DIO16 | SWDCLK / SWDIO | Fixed |
| 14 | RSTN | Reset (SW301, J301) | Fixed |

**This leaves no spare pins.** To free one, drop UART RX and keep TX for logs; commands can come over BLE instead.

## Other findings

- **TPS25751 boot configuration is not a firmware job.** Each TPS25751 loads its configuration from its own M24512 EEPROM on its private bus (I2CC1/I2CC2). The MCU only talks to them on the shared bus. This clears the risk raised earlier.
- **Low-power behaviour checked in SWRS349A (8.6, 8.11):**
  - GPIOs are latched in Standby.
  - A pin edge (IRQ_N) wakes the chip from Standby.
  - The watchdog runs in active, idle and Standby, and can't be stopped once enabled.
  - `mcu-io-power-states.md` still needs its rewrite for the CC2340: Stop2 becomes Standby, the IWDG becomes the WDT, and PB4's NJTRST pull-up becomes R313.
- **Reset-safe outputs still work.** The CC2340 pins are hi-Z in reset, as on the STM32. The existing pull-ups and pull-downs on CHG_INH and EN_5Vx still set the safe state.
- **Reset state of 3V3_SLEEP:** the STM32's PB4 reset with a pull-up, but CC2340 pins float in reset, and the TPS62177 pulls SLEEP down with 1.4 µA. R313 is therefore fitted at 470k: it holds about 2.8 V in reset and costs 7 µA while firmware drives it low in S2.
- **Footprint and antenna keep-out:** done from the datasheet (p.63-64, fig. 9-2): `TI_MHA0024A_CC2340R5MODA_7x10mm`.
- **Not checked yet:**
  - JLC/LCSC stock and price for the CC2340R5MODA. The datasheet is dated June 2026, so stock may be thin.
  - JLC/LCSC stock and price for the TMP1075 (WSON-8 DSG is in the schematic).
