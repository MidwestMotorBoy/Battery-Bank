# MCU I/O versus power states (rev A8, 2026-10-14)

This document sets the state of every CC2340R5MODA (U301) pin in every power state. U301 replaced the STM32WB1MMC in rev A7 (`cc2340-pin-budget.md`, `hardware/DevBoard/README.md` items 40–41). It is reconciled against:

- the sleep plan in `power-budget.md`: about 240 µA idle at the pack, the MCU in Standby between BLE advertising events, and the TPS62177 in sleep mode with no cable attached;
- the CHG_INH and watchdog decisions (`schematic-review-2-2026-10-12.md`, D1);
- schematic review 4 (`schematic-review-4-2026-10-14.md`): A-1, A-3, A-4, A-8, C-6, D-4 and S-1.

Loads come from the netlist and are given at 3.3 V. The firmware steps that go with this plan are in `bringup-config-checklist.md` §4.

## Power states

| State | When | MCU mode | 3V3 (TPS62177) |
|---|---|---|---|
| **S0 Charging** | At least one port has a sink contract and the supervision checks pass | Active, or Standby between checks with an RTC wake (≤ 1 s) | Normal (DIO21 high) |
| **S1 Sourcing** | At least one port supplies a device and none is charging | Active, or Standby between checks with an RTC wake (≤ 1 s) | Normal |
| **S2 Idle** | No cable | **Standby**, BLE advertising | **Sleep mode** (DIO21 low), 15 mA max |
| **S3 Reset** | Power-on, SW301, WDT, brown-out; also the ROM bootloader and an unprogrammed part | Reset: pins hi-Z, no pulls | Normal (R313 220k holds SLEEP high) |
| **S4 MCU unpowered** | Dead pack (CUV), gauge FETs off | — | Off |
| **S5 Ship (storage)** | App command, two weeks with no cable or button, or RSOC ≤ 5 %; never with a cable attached (review 4 S-1) | Unpowered: the MCU sends the gauge MAC 0x0010 SHUTDOWN, then the rail collapses | Off. Pack drain about 3–4 µA. Wakes on a USB charger or SW101, not on a phone |

**CC2340 Standby is the BLE sleep mode, and its GPIOs latch** (SWRS349A §8.11): every output keeps its level, and a pin edge (IRQ_N) or the RTC wakes it. This is the opposite of the STM32's Standby, where outputs went hi-Z. Shutdown (the CC2340's lowest mode, RTC off) is not used; S5 powers the MCU down instead.

## Pin plan

| DIO (pin) | Net | External load (3.3 V) | S0 Charging | S1 Sourcing | S2 Idle | S3 Reset (hi-Z) | Cost if wrong in S2 |
|---|---|---|---|---|---|---|---|
| DIO24 | CHG_INH | Two CE pull-ups, 47k + 1k each to 3V3 (R417/R435, R517/R535) | **Low** (2 × 69 µA = 138 µA) | High | **High** (0 µA) | High via the pull-ups → charging inhibited | **138 µA** if left low |
| DIO3 / DIO4 | EN_5V1 / EN_5V2 | 100k pull-down (R432/R532) → TPS62933 EN | Low unless that port needs VCONN | High for a port that is sourcing (any voltage: vSafe5V, Rp and VCONN come from PP5V) | **Low** | Low → PP5V off. Restore from retained state first thing after reset (review 4 C-6) | 33 µA + Iq per port |
| DIO21 | 3V3_SLEEP | TPS62177 SLEEP (1.4 µA typ internal pull-down); R313 220k pull-up to 3V3 | High | High | **Low** (sleep mode; 15 µA through R313) | High (R313) → normal mode | — |
| DIO12 | LED_DRV | R306 330 Ω + red LED (R307 removes it) | Optional, high drive (about 3.6 mA) | Optional | **Off** | Hi-Z → off | about 3.6 mA, and it eats the 15 mA sleep-mode limit (D-4) |
| DIO11 | IRQ_N | R314 47k pull-up; open-drain sources: 2 × TPS25751 I2Ct_IRQ, gauge BTP via Q103 | Input, falling-edge wake, internal pull **off** | Same | Same (Standby wake source) | — | 70 µA while any source holds it low: clear every source (rule 3) |
| DIO6 / DIO8 | SCL / SDA | 3.3k pull-ups to 3V3 via R312; gauge internal 1 MΩ pull-downs | I2C0, 100 kHz | Same | Bus idle high; never enter Standby mid-transfer | Hi-Z, pulled high | 6.6 µA (gauge pull-downs, unavoidable) |
| DIO18 / DIO20 | UART TX / RX (J302, via R322/R323 1k) | Header only | UART | UART | UART idle (TX high); RX internal pull-up on | Hi-Z | A powered USB-UART adapter on an unpowered board back-feeds through RX (R323 limits it); connect only with 3V3 up |
| DIO16 / DIO17 | SWDIO / SWCLK | J301 | SWD | SWD | SWD (an attached debugger raises sleep current; unplug it to measure) | SWD | — |

**MCU pin loads in S2 with this plan: about 22 µA** at 3.3 V: the gauge's SMBus pull-downs (6.6 µA) and R313 while SLEEP is held low (15 µA). The rest of the 3V3 idle load (about 400 µA in total) is the TPD4S201s and the TPS25751s (`power-budget.md`).

## Rules that reconcile the I/O plan with the sleep plan

1. **CHG_INH is low only in S0.** Holding DIO24 low costs 138 µA. In S1 and S2, drive it high: that costs 0 µA, and charging is blocked anyway. Because Standby keeps the pin low, the supervision checks keep running in S0 Standby on an RTC wake.
2. **On every wake from S2 that may need current, DIO21 goes high first.** In sleep mode the TPS62177 supplies 15 mA at most. After a cable attaches, the two TPS25751s draw 3–6 mA each, and the radio at +8 dBm draws about 11 mA. In sleep mode keep the LED off and TX at ≤ +4 dBm, and leave sleep mode on any IRQ_N edge (review 4 D-4).
3. **IRQ_N is one wire-OR of three latched sources** (review 4 A-3; TMP1075s removed in rev A8):
   - at boot, clear INT_EVENT1 on both TPS25751s and the gauge BTP;
   - the handler reads and clears every source and loops until DIO11 reads high;
   - never enter Standby with DIO11 low; if a source is stuck, fall back to RTC polling and log it.
4. **Temperatures (rev A8):** S0/S1: poll the gauge `DAStatus2` and each charger's `TS_ADC` (through the TPS25751 `I2Cr`) about once a second. If firmware stalls, the chargers' own TS limits and the gauge's OTD/OTC still act. S2: nothing to poll.
5. **Enter S2 only when:**
   - no port has a contract;
   - EN_5Vx are low;
   - CHG_INH is high;
   - IRQ_N is high (no TPS25751 or gauge event pending);
   - the I2C bus is idle.
6. **The WDT runs in Active, Idle and Standby and can't be stopped once enabled** (SWRS349A §8.6). A firmware fault that leaves no wake source armed is therefore still caught. About 2 s in S0/S1, serviced by the ≤ 1 s supervision loop; longer in S2, serviced from an RTC wake that also runs the slow gauge check.
7. **After any reset (S3), outputs come up safe:**
   - charging is inhibited (CHG_INH pulled high);
   - PP5V is off (EN_5Vx pulled low);
   - the 3V3 rail is in normal mode (R313).

   Firmware restores EN_5Vx from retained state first, then runs the supervision checks before it drives CHG_INH low. The PP5V bulk keeps the attached Rp up for about 16 ms at 5 mA, so a 20 V contract can ride through a WDT reset if EN_5Vx comes back in time; a stuck or unprogrammed MCU drops every sourced contract (review 4 C-6).
8. **Bootloader pin (review 4 A-1):** DIO21 is the ROM bootloader's default trigger pin (active low). Configure the CCFG without that trigger before the first flash, and drive DIO21 high before Shutdown or a deliberate reset.
9. **Gauge sleep:** the bus idles high in S2. The gauge's [IN_SYSTEM_SLEEP] must therefore be 1 (or the MCU sends MAC 0x0011 SLEEP), or it never sleeps and draws about 336 µA instead of about 75 µA (review 2, A N-1 / C-8). The gauge opens the CHG FET in sleep; that is fine in S2.
10. **EN_5V in S2 (open, verify at bring-up):** the plan keeps the TPS62933s off in idle. The TPS25751 must still detect a sink attaching without PP5V, raise IRQ_N, and wait for the MCU to enable PP5V within its source timing. If bring-up shows it cannot, keep EN_5Vx high in S2. That costs about 33 µA (R432 pull-down) plus the TPS62933 Iq per port, so raise R432/R532 to 1 MΩ then.

## Supersedes

- The rev A5 version of this document (STM32WB1MMC: PB8/PB4/PA6 pins, Stop2, IWDG option bytes, NTC_EN).
- `monolith-next-actions.md`: "TPS25751 interrupts … using the STM32's internal pull-up (no resistor)". IRQ_N has an external pull-up (R314); keep the internal pull off.
- First review, firmware item 12: "otherwise drive it low". Replaced by rule 1.
- Review 2, firmware item 12: "use Stop2, not Standby, while inhibiting". Replaced by rule 1 and the S-state table (CC2340 Standby keeps GPIO states).
