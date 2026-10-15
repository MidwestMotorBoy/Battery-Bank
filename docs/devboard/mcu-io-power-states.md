# MCU I/O versus power states (rev A5, 2026-10-13)

> **Out of date since rev A7 (2026-10-14).** U301 is now a CC2340R5MODA (`cc2340-pin-budget.md`, `DevBoard/README.md` item 40), so the STM32 pin names, Stop2/IWDG rules and the NTC_EN rows below no longer match the schematic. What carries over: the power states S0–S4, the CHG_INH / EN_5Vx / 3V3_SLEEP / LED policies, the S2 entry conditions and the gauge-sleep rule. The changes: IRQ1/IRQ2/GAUGE_BTP become one IRQ_N; NTC_EN is gone (I2C sensors); 3V3_SLEEP's reset state comes from R313 (470k), not PB4's pull-up; Stop2 becomes CC2340 Standby; the IWDG becomes the CC2340 WDT. A full rewrite is pending.

This document sets the state of every STM32WB1MMC (U301) pin in every power state. It is reconciled against two things:

- The sleep plan: about 150 µA idle at the pack, the MCU asleep between slow BLE advertising events, the TPS62177 in sleep mode with no cable attached, and the NTC dividers powered only while sampling (`docs/project/monolith-next-actions.md`).
- The rev A5 CHG_INH and watchdog decisions (`schematic-review-2-2026-10-12.md`, D1).

Loads come from the netlist and are given at 3.3 V.

## Power states

| State | When | MCU mode | 3V3 (TPS62177) |
|---|---|---|---|
| **S0 Charging** | At least one port has a sink contract and the supervision checks pass | Run, or Stop0–2 between checks (wakes ≤ 1 s) | Normal (PB4 high) |
| **S1 Sourcing** | At least one port supplies a device and none is charging | Run, or Stop0–2 between checks (wakes ≤ 1 s) | Normal |
| **S2 Idle** | No cable | **Stop2**, BLE slow advertising | **Sleep mode** (PB4 low), 15 mA max |
| **S3 Reset** | Power-on, SW301, IWDG, brown-out | Reset (pins analog/hi-Z) | Normal (PB4 has its NJTRST pull-up) |
| **S4 MCU unpowered** | Dead pack, gauge FETs off | — | Off |

**Standby and Shutdown are not used.**
- BLE needs Stop2.
- PA6 (BTP) is not a WKUP pin.
- In Standby, every output goes hi-Z. That inhibits charging, switches PP5V off and puts the 3V3 rail into sleep mode, all without supervision.

Stop2 keeps GPIO output states, and EXTI wakes it.

## Pin plan

| Pin | Net | External load (3.3 V) | S0 Charging | S1 Sourcing | S2 Idle | S3 Reset (hi-Z) | Cost if wrong in S2 |
|---|---|---|---|---|---|---|---|
| PB8 | CHG_INH | Two CE pull-ups, 47k + 1k each to 3V3 (R417/R435, R517/R535) | **Low** (2 × 69 µA = 138 µA) | High | **High** (0 µA) | High via the pull-ups → charging inhibited | **138 µA** if left low |
| PA11 / PA12 | EN_5V1 / EN_5V2 | 100k pull-down (R432/R532) → TPS62933 EN | Low unless that port needs VCONN | High for a port sourcing 5 V or needing VCONN (33 µA + TPS62933 Iq) | **Low** | Low → PP5V off: a 5 V-sourced device sees VBUS drop during a reset | 33 µA + Iq per port |
| PA8 | NTC_EN | 5 × (10k + NTC) to GND (TH301–TH305) | High only while sampling (~1 ms) | Same | **Low** | Hi-Z → 0 µA | ~825 µA at 25 °C |
| PB4 | 3V3_SLEEP | TPS62177 SLEEP (1.4 µA internal pull-down); R313 DNP | High | High | **Low** (sleep mode, 4.8 µA Iq) | High (NJTRST pull-up) → normal mode | 17 µA more Iq if left high |
| PB5 | LED_DRV | 1k + LED (R307 removes it) | Optional | Optional | **Low** | Hi-Z (C-14: may glow faintly) | ~0.5 mA |
| PA6 | GAUGE_BTP | 100k pull-up (R114); Q103 pulls it low when the gauge asserts BTP | Input, EXTI falling, internal pulls **off** | Same | Same (Stop2 EXTI wake; not WKUP) | — | 33 µA while BTP is asserted: re-arm or clear BTP after handling it |
| PA0 / PA2 | IRQ1 / IRQ2 | 100k pull-ups (R314/R315), TPS25751 open drain | Input, EXTI falling, internal pulls **off** | Same | Same (EXTI, also WKUP1/WKUP4) | — | 33 µA per pending IRQ: clear TPS25751 events promptly. An internal pull-up left on adds about 80 µA while asserted |
| PB6 / PB7 | SCL / SDA | 4.7k pull-ups to 3V3 via R312; gauge internal 1 MΩ pull-downs | I2C1 AF open-drain | Same | Bus idle high; never enter Stop2 mid-transfer | Hi-Z, pulled high | 6.6 µA (gauge pull-downs, unavoidable) |
| PA1 / PA3 / PA4 / PA5 / PA7 | NTC_TH1–TH5 | NTC dividers (TH5 = protection FETs, also on J303 pin 2) | Analog | Analog | Analog | Analog | — |
| PA9 / PA10 | UART TX / RX (J302) | Header only | USART | USART | USART idle (TX high), or analog when no adapter | Hi-Z | An unpowered USB-UART adapter is fed through TX |
| PA13 / PA14 | SWDIO / SWCLK | J301 | SWD | SWD | SWD (an attached debugger raises sleep current: unplug it to measure) | SWD pulls | — |
| PB0–PB2, other unused | — | None | Analog | Analog | Analog | Analog | Leakage if left as floating inputs |

**MCU pin loads in S2 with this plan: about 7 µA**, almost all of it the gauge's SMBus pull-downs. The rest of the 150 µA budget goes to the gauge, the chargers, the two TPS25751s and BLE.

## Rules that reconcile the I/O plan with the sleep plan

1. **CHG_INH is low only in S0.** Since rev A5, holding PB8 low costs 138 µA, nearly the whole idle budget. In S1 and S2, drive it high: that costs 0 µA, and charging is blocked anyway. This replaces the earlier wording "otherwise drive it low".
2. **On every wake from S2, PB4 goes high first, before anything else.** In sleep mode the TPS62177 supplies 15 mA at most. After a cable attaches, the two TPS25751s draw 3–6 mA each, and the MCU in Run plus the radio (4.5 mA RX, 5.2 mA TX at 0 dBm) can push the total past 15 mA. A slow switch-over risks a 3V3 droop and a brown-out reset (first review, firmware item 7).
3. **Enter S2 only when:**
   - no port has a contract;
   - EN_5Vx are low;
   - CHG_INH is high;
   - NTC_EN is low;
   - no TPS25751 event is pending (IRQ lines high);
   - BTP is not asserted;
   - the I2C bus is idle.
4. **The IWDG counts in Stop2** (option byte IWDG_STOP = 1). A firmware fault that leaves no wake source armed is therefore still caught. The timeout depends on the state:
   - **S0/S1: about 2 s,** refreshed by the ≤ 1 s supervision loop.
   - **S2: about 16 s** (up to 32.8 s with the LSI at prescaler /256 and reload 0xFFF). An RTC wake-up about every 8 s refreshes it and runs the slow gauge check.

   Change the prescaler and reload at runtime with the KR unlock sequence (0x5555), and wait for PVU/RVU before entering Stop2. IWDG_STDBY is unimportant, because Standby is not used. Keep IWDG_SW = 0.
5. **After any reset (S3), outputs come up safe:**
   - Charging is inhibited.
   - PP5V is off.
   - NTC dividers are off.
   - The 3V3 rail is in normal mode.

   Firmware runs the supervision checks before it drives CHG_INH low. A port sourcing 5 V from PP5V drops VBUS during an IWDG reset, so the device re-attaches; that is accepted. PPHV sourcing at 9–20 V (BQ25756 reverse mode) does not depend on the MCU.
6. **Gauge sleep:** the bus idles high in S2. The gauge's [IN_SYSTEM_SLEEP] must therefore be 1, or it never sleeps and draws about 336 µA instead of about 75 µA, which breaks the budget (review 2, A N-1 / C-8). The gauge opens the CHG FET in sleep; that is fine in S2.
7. **EN_5V in S2 (open, verify at bring-up):** the plan keeps the TPS62933s off in idle. The TPS25751 must still detect a sink attaching without PP5V, raise IRQ, and wait for the MCU to enable PP5V within its source timing. If bring-up shows it cannot, keep EN_5Vx high in S2. That costs about 33 µA (R432 pull-down) plus the TPS62933 Iq per port, so raise R432/R532 to 1 MΩ then.

## Supersedes

- `monolith-next-actions.md`: "TPS25751 interrupts … using the STM32's internal pull-up (no resistor)". Rev A4 has external 100k pull-ups (R314/R315); keep the internal pulls off.
- First review, firmware item 12: "otherwise drive it low". Replaced by rule 1.
- Review 2, firmware item 12: "use Stop2, not Standby, while inhibiting". This was the old CHG_INH polarity; replaced by rule 1 and the S-state table.
