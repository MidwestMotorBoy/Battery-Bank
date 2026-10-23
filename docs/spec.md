# Monolith Battery Bank: Current Design Spec

Last updated 2026-10-23. This file is the single source of truth for the Monolith design; it replaces `docs/project/monolith-next-actions.md`. Update it when a decision changes.

## Overview

Monolith is an ultralight 93.6 Wh backpacking power bank: four FEB 21700G cells in 4S1P, two identical bidirectional USB-C PD ports (100 W burst, about 40 W sustained), a BQ40Z50-R2 gauge, and a TI CC2340 Bluetooth LE MCU that talks to an iPhone app. The design of record is the production P0 board inside the MJF nylon "cup" enclosure. Nothing has been built or bench-tested yet, so every number here is a design value.

This spec reflects the repo's `master` at commit a490f98 (2026-10-21). Where sources disagree, the newest one wins and the conflict is listed under Contradictions. In order of authority: the repo README and `hardware/Production/README.md` (10-21), `docs/firmware/charge-and-thermal-policy.md` (10-21), the `app` branch GATT spec (10-16), the project's `monolith-next-actions.md` (10-16), then older notes and memory.

| Item | Current design |
| --- | --- |
| Energy | 93.6 Wh nominal (91.4 Wh minimum), under the 100 Wh carry-on limit |
| Pack voltage | 14.4 V nominal, 16.8 V full, 11.2 V floor (2.8 V per cell) |
| Ports | 2 × USB-C PD, each bidirectional, 5–20 V, up to 5 A |
| Output | 100 W while the hottest cell is at or below 33 °C, then a linear derate to about 40 W sustained |
| Charging | Up to 4.55 A into the pack, following a temperature ramp. About 2 h empty to full from an 88 W source at 25 °C |
| Wireless | Bluetooth LE (CC2340R5MODA), custom GATT service, signed OTA updates |
| Board | One 43.2 × 74.35 mm 6-layer board along one face of the cells |
| Enclosure | MJF PA12 cup with an O-ring bottom cap and TPU bumpers. No metal, no potting |
| Size and mass | 59.8 × 51.9 × 97.2 mm, about 384–400 g (modelled) |
| Cost (estimate) | About $105 per board at 5 boards, about $155–160 per finished pack |

## System architecture

![Monolith P0 system architecture](spec-architecture.png)

The gauge sits between the cells and a shared pack bus; each port's BQ25756 can charge from or source to its USB-C connector, and the MCU sets policy over one I2C bus without carrying power itself.

## Cells and pack

The pack is four FEB 21700G (68E) 6500 mAh cells in 4S1P, chosen on 2026-10-21 over the EVE 58E and Tenpower 60XG for energy at trail loads. The cell figures come from a reseller listing ([diy500amp](https://diy500amp.com/products/feb-21700-battery-cell-6500mah-13a-ultra-high-capacity-energy-cell?variant=42624877330503)), not the maker's datasheet, so they need confirming before P0.

| Item | Value |
| --- | --- |
| Capacity | 6500 mAh nominal, 6350 mAh minimum, 23.4 Wh per cell |
| Charge | 4.20 V. Max 4.55 A at 15–45 °C, 3.25 A at 5–15 °C, 0.65 A at 0–5 °C, none outside 0–45 °C |
| Discharge | 13 A at 0–35 °C, 6.5 A at −20–0 and 35–45 °C, 3.25 A at 45–60 °C. Floor used: 2.8 V per cell |
| Resistance | ≤ 25 mΩ spec; about 30 mΩ DC mid-charge and 50 mΩ near empty (estimate) |
| Size and mass | 21.65 × 70.95 mm, 75 g (300 g for four) |
| Cycle life | 500 cycles to ≥ 70 % at 0.5C charge / 1C discharge |
| Price | $7.49 each, bare, no protection |

- **Interconnect:** spot-welded pure nickel, kWeld plus kCap. Series strips 0.15 × 7 mm; PACK tabs 0.2 × 7 mm split into a power finger and a Kelvin finger. Every connection is a nickel tail through a plated slot in the board, soldered on F.Cu. No wires, springs or connectors.
- **Matching:** all four from one batch, within 10 mV and 1 mΩ (AC 1 kHz). Measure each diameter; the cup is designed to 21.85 mm.
- **Carrier:** an MJF PA12 carrier holds the cells at 23.25 mm pitch, with webs between the front and back pairs. The board's heat goes into the two front cells, so those run hottest.
- **Short circuit:** about 150–170 A available, less than the 58E, so the protection FETs and fuse have margin.
- **Future trial:** the carrier should accept a Molicel P60B/P60C later (lower resistance, but about 300 A short-circuit current would force new FETs and fuse).

## Battery management and protection

A TI BQ40Z50-R2 gauge is the pack's authority on cell voltage, current, temperature and state of charge, with three independent protection layers behind it.

| Layer | What | Trips on |
| --- | --- | --- |
| 1. Gauge | BQ40Z50-R2 (SMBus 0x0B), AGM404AP1 CHG/DSG FETs, 1 mΩ 1206 shunt | OTC 45 °C, UTC 0 °C, OTD 60 °C, OCD1 ≈ 12 A, OCD2 ≈ 14 A, CUV at ≥ 2.8 V per cell |
| 2. Hardware | BQ294700 per-cell OVP firing a TLC WSFB1514 15 A chemical fuse (F102) through Q104 | Cell overvoltage, independent of the gauge |
| 3. Firmware | MCU cross-checks and the charge/thermal policy | Everything above, with smoother limits |

- **Temperature inputs:** four wired 10k NTCs, one per cell, on TS1–TS4, plus the gauge's FET temperature and die. The policy acts on the hottest cell, which in the cup is a front cell.
- **JEITA ranges in data flash:** T1 0 / T2 5 / T3 15 / T4 40 / T5 45 °C with 650 / 3250 / 4550 / 2275 mA.
- **Ship mode:** gauge SHUTDOWN, pack drains 3–4 µA. Entered from the app, after two weeks idle, or at RSOC ≤ 5 %, never with a cable attached. Wakes when a charger is plugged in (wake-on-USB is unproven; TP113 to TP106 is the manual wake).
- **Training on P0:** there is no separate training board. BQStudio and the EV2400 clone connect through the J302 "GAUGE" Tag-Connect, with J113/J114 wire pads for the learning-cycle load. The FEB cell needs a new chemistry ID (likely a GPCCHEM run), then a learning cycle per TI SLUA903, and the golden image goes in the repo.
- **Considered and not adopted:** BQ41Z50 (not a drop-in, $7.44 vs $1.96, and still needs an external second-level protector). Worth a look for a later spin.
- **Loss cut (adopted 2026-10-23):** replace the AGM404AP1 with the XNRUSEMI XRS120N04D (2.8 mΩ vs 6.0 mΩ, same footprint), about −0.45 W at 100 W.

## Ports, charging and power policy

Each USB-C port is an identical, self-contained power stage, so either port can charge the pack or source up to 20 V / 5 A. Both stages share one pack bus (PACK\_P) behind the gauge shunt, so the gauge sees net current during pass-through and dual-port charging.

**Per port (P0 part numbers):**

| Function | Part | Notes |
| --- | --- | --- |
| PD controller | TPS25751D | I2C 0x20 (USB1) / 0x21 (USB2), SafeMode dead-battery strap, own 512 Kbit EEPROM. It is the I2C master for its charger; the MCU reaches the BQ25756 through `I2Cr`/`I2Cw` |
| Buck-boost charger | BQ25756 | 600 kHz, R\_ICHG 11.8 kΩ (hardware ceiling 4.07–4.45 A), DIS\_STAT\_PINS = 1, own TS NTC on the FET copper |
| Power FETs | 2 × Vishay SiZ240DT | 40 V half-bridge per leg. LCSC had only 2 in stock on 10-19; supply them to JLC yourself |
| Inductor | Coilank APS0730M2R2F, 2.2 µH | 3.1 mm tall. Runs hotter than the Coilcraft option; measure it |
| Sense resistors | 5 mΩ RAC (0805) and RBAT (1206) | TI fixes RBAT at 5 mΩ |
| 5 V source rail | TPS62933 | Feeds PP5V and VCONN; enabled per port (EN\_5V1/2) |
| Port protection | TPD6S300 on CC, TVS2200 on VBUS | No liquid detection on P0 |
| Connector | Shou Han TYPE-C 16PCB1.6 IP68 (C55629729) | Right angle, 5 A / 20 V, seals in the cup's top wall |
| Bulk caps | USB side 4 × 22 µF + 2 × CA55 47 µF polymer tantalum; PACK\_P 3 × 22 µF per port + 6 shared | All parts ≤ 3.1 mm tall |

The 3.3 V rail is a TPS62177 buck with a sleep pin the MCU controls (3V3\_SLEEP).

**Charging (decided 2026-10-21).** Firmware writes `ICHG = min(gauge ChargingCurrent, ramp(hottest cell), 4.55 A)` once a second, split across both chargers if both ports are sinking.

| Hottest cell | Charge current |
| --- | --- |
| ≤ 0 °C | 0 |
| 1–5 °C | 0.65 A |
| 5 → 6.5 °C | ramp to 3.25 A |
| 6.5–15 °C | 3.25 A |
| 15 → 16.5 °C | ramp to 4.55 A |
| 16.5–40 °C | 4.55 A |
| 40 → 45 °C | ramp to 0 |

- Stop at the max SOC setting (default 95 %, 60–100 % from the app), with a periodic 100 % balancing charge, a "charge to 100 % once" command and trip mode. An optional "longevity" charge to 4.10 V is proposed.
- Solar: the Dark Energy 15 W panel is the reference source, including plain 5 V with no PD. BQ25756 VINDPM and MPPT, riding through panel dropouts.
- Dual-port charging, pass-through (charge setpoint raised by the output load), and loop detection when a cable joins the pack's own two ports.

**Discharge: burst, then sustain.** The PD offer stays at 100 W until the hottest cell reaches 33 °C, then ramps down to 40 W at 39 °C.

| Hottest cell | Allowed output |
| --- | --- |
| ≤ 33 °C | 100 W |
| 33 → 39 °C | ramp 100 → 40 W |
| 39–45 °C | 40 W |
| 45 → 55 °C | ramp to 0 |
| ≥ 60 °C | 0 (gauge OTD) |

- `P_allow` also takes the board ramp (55 → 70 °C on the charger TS) and a low-pack-voltage limit. It changes the offer by re-advertising Source Capabilities in 5 W steps: down at once, up only after 2 K of cooling and 10 s.
- Model results at 25 °C: about 4 min of full 100 W from a full pack; at 30 W nothing derates and the pack lasts about 3 h.
- Heat at 100 W out is about 12 W in total, about 6.5 W of it in the cells.

**Port sharing (decided 2026-10-23): a user setting.** Both ports share `P_allow`. In **USB1 priority** mode (the default), USB2 keeps a guaranteed minimum (10–30 W, default 20 W) and USB1 gets the rest. In **Balanced** mode, the port with the larger contract gives way first. Either way, the two contracts never add up to more than `P_allow`, even briefly: lower one contract before raising the other.

**Loss cuts (adopted 2026-10-23; see Decided: the four loss cuts)** (about −1.6 W at 100 W; the gate drive is fitted but off by default): XRS120N04D protection FETs; a 9 V gate-drive LDO (TPS7A4101) per port, enabled by TPS25751 GPIO6 via `GPsl`/`GPsh` and ANDed with REGN; Coilcraft XGL7030-332 at 500 kHz; thicker nickel (0.2 × 10 mm).

## MCU, sensing and Bluetooth

The MCU is a TI CC2340R5MODA Bluetooth LE module (Cortex-M0+, 512 KB flash / 64 KB RAM, integrated antenna), bought from TI.com at about $4 and consigned to JLC. It replaced the STM32WB1MMC on 2026-10-14 for cost and stock.

| Signal | Pin | Notes |
| --- | --- | --- |
| I2C0 SCL / SDA | DIO6 / DIO8 | One bus: gauge 0x0B, TPS25751 0x20 and 0x21 |
| IRQ\_N | DIO11 | Wire-OR of both TPS25751 IRQs and the gauge BTP |
| CHG\_INH | DIO24 | 47k pull-up, so reset, hang or a blank MCU stops charging. MCU drives it low to allow charging |
| EN\_5V1 / EN\_5V2 | DIO3 / DIO4 | Per-port TPS62933 enables |
| 3V3\_SLEEP | DIO21 | TPS62177 sleep mode. CCFG bootloader trigger on DIO21 is off |
| Free on P0 | DIO12, DIO18, DIO20 | LED, reset button and UART headers were dev-board only |

- **Debug:** SWD over a Tag-Connect TC2030 (J301) with the XDS110 on an LP-MSPM0G3519 LaunchPad. Use a `.ccxml` set to "Target supplied power"; the default drives 3.3 V into the board's rail (measured 2026-10-20).
- **Toolchain:** LPF3 SDK 9.23, TI Arm Clang, SysConfig and gmake from CCS 21, UniFlash. Board files exist for the LaunchPad and the dev board; there is no P0 board file yet.
- **Board temperatures:** the TMP1075 sensors were removed in dev board rev A8 (2026-10-17). Temperatures now come from the gauge (`DAStatus2`: TS1–TS4, FET temperature, die) and each BQ25756's TS NTC (`TS_ADC`, read through the TPS25751). The USB-C receptacles have no sensor.
- **Bluetooth:** custom GATT service per the `app` branch spec v1.1, LE Secure Connections, Just Works in v1. Writes need a bond. Buttonless pairing window: 2 min after a cable attaches, or whenever no phone is bonded yet. Up to 4 bonds.
- **OTA:** TI OAD with MCUboot, ECDSA P-256 signed images, swap-with-revert, anti-rollback on production. The signing key lives on Logan's MacBook plus an offline backup.
- **Idle current:** about 230 µA on the dev board estimate, plus about 175 µA for P0's two TPD6S300s, so roughly 400 µA (about 4–5 % per month). Bluetooth advertising rate is the biggest unknown.

## Boards and enclosure

The production P0 board is the design of record and the first board planned to be built; it is mid-placement, not routed and not reviewed.

| Board | State (repo, 2026-10-21) | Key facts |
| --- | --- | --- |
| Production P0 (`hardware/Production/`) | Schematic generated and netlist-checked; placement in progress; USB-C ports placed and locked | 283 parts, 43.2 × 74.35 mm, 6 layers, 1.6 mm, 2 oz outer / 0.5 oz inner, ENIG, filled vias. JLC assembles F.Cu; 19 B.Cu parts are hand-fitted, including the CC2340 module by hot air |
| Dev board MonolithDev rev A8 (`hardware/DevBoard/`) | Routed, DRC clean, fab files generated. Repo says it was skipped on 10-18 and never ordered (see Contradictions) | 196 × 115 mm, about 430 parts, cell holders, test points, sleep-current section |

**P0 board changes still to apply:**

- [ ] Move the five bottom tab slots 0.30 mm for the FEB cells; run Update PCB from Schematic (R413/R513 = 11.8k)
- [ ] Cup changes: B.Cu gap-filler zone with a dense thermal-via array, split carrier rails, two Ø2.0 mm peg holes, remove the cover standoffs H101–H104, rerun `make_board.py --keepouts` for the cup
- [ ] Fix DRC: port 1's stage (U403, Q402, C434, R446, R447) sits in the antenna keep-out; L401 is on B.Cu and belongs on F.Cu
- [ ] Make C302–C304 0402 instead of 0201; remove the four stranded VBUS traces
- [ ] Check JLC's minimum plated slot width (0.6 mm slots) and SiZ240DT stock

**Enclosure: the cup (adopted 2026-10-21).** The cells, carrier and board are built and tested on the bench as one power module, which slides into the cup from the bottom until the USB-C faces seat in the top wall.

- MJF PA12 cup closed on five sides, with two USB-C seal bores in the top wall.
- MJF PA12 bottom cap with one 2.0 mm silicone O-ring (60A, about 25 % squeeze), held by two radial M2 screws below the seal.
- TPU 95A bumpers at both ends and a TPU pad inside the cap; an ePTFE vent patch.
- No metal and no potting: the power stage's heat goes into the front cells through thermal vias and about 4 g of 3 W/m·K gap filler. The board gets conformal coat.
- Outside size 59.8 × 51.9 × 97.2 mm, about 384–400 g. The design came from a five-concept study (`reports/Ground-up mechanical design.md`) and replaced the side tray with its aluminium cover.

## Contradictions between sources

Twenty conflicts turned up. The first eight changed what gets built or coded; Logan settled them on 10-23 except the resistor, which is laid out under Your call. The rest are stale text to clean up. "Project notes" means `/mnt/project-files/knowledge/claude/monolith-next-actions.md` (10-16); "repo checklist" means `docs/project/monolith-next-actions.md` as it stood on `master` at a490f98 (now retired).

| # | Topic | Older source says | Newer source says | Spec uses |
| --- | --- | --- | --- | --- |
| 1 | Dev board built? | Chat 10-20 and memory: dev board in hand, LEDs lit, probe measured 3.3 V back-feed | README and P0 docs: dev board skipped 10-18, never ordered | **Skipped (decided 10-23)** |
| 2 | Port sharing | Project notes, GATT `usb2_min_w`: USB1 priority, USB2 guaranteed 20 W (10–30 W setting) | Thermal policy: the port with the higher contract gives way first | **User setting, both modes (10-23)** |
| 3 | Charge rate and fast mode | Project notes, GATT `fast_charge`: 0.5C default, opt-in 1C at 20–80 %. Bring-up checklist: single port 5.5 A by default | Thermal policy: temperature ramp to 4.55 A, no fast mode mentioned | Ramp; fast toggle **kept, clamped to the cell table (10-23)** |
| 4 | Charge ceiling resistor | Thermal policy: R\_ICHG 11.5 kΩ | README, P0 README, FEB notes: 11.8 kΩ | 11.8 kΩ; **see Your call** |
| 5 | Output and throttle | Project notes, GATT: 100 W thermally limited; when hot every port drops to 20 W; full power while 3 of 4 board sensors work | Thermal policy: 100 W burst, linear ramp to \~40 W sustained on the hottest cell | Ramp |
| 6 | Board temperature sensors | Project notes, GATT Temperatures 5–9: TMP1075 T1–T3 (+T4/T5 DNP) | Dev board rev A8 (10-17): TMP1075s removed; gauge and charger TS only; USB-C receptacles unmonitored | Rev A8 |
| 7 | LED and button | GATT: `led_mode`, `IDENTIFY`, ship mode woken "by a charger or the button" | P0: LED, reset and wake buttons all removed | P0 |
| 8 | IP rating | Memory: IP65 (FR4 era). Mechanical brief: IP67 if possible | Cup docs state no target | **IP67 (decided 10-23)** |
| 9 | Cells | Project notes, GATT `design_mah` 5600, EEPROM notes: EVE 58E, 82 Wh. Memory 10-14: switch to Amprius SA112 | Repo 10-21: FEB 21700G, 93.6 Wh | FEB |
| 10 | Enclosure | Memory, project notes: FR4 walls with printed end caps, top-cap board, aluminium heatsink plate | 10-18 side tray + aluminium cover; 10-21 the cup | Cup |
| 11 | Potting | GATT §8, EEPROM notes, repo checklist: potted pack | Mechanical design 10-18: no potting | No potting |
| 12 | Port protection | Project notes: TPD4S201 with liquid detection | P0 10-18: TPD6S300, liquid detection removed | TPD6S300 |
| 13 | Charger FETs and inductor | Project notes, dev board: 4 × PGQ04N070, XAL7030-222 | P0: 2 × SiZ240DT, APS0730M2R2F; loss study proposes XGL7030-332 at 500 kHz | P0 parts |
| 14 | Idle current | Project notes: \~230 µA. P0 low-profile section: "\~150 µA budget" | P0 README: TPD6S300s add \~175 µA | \~400 µA |
| 15 | Pack wiring on P0 | `p0-bringup-and-training.md`: 16 AWG wire pads J108/J112 | `p0-assembly.md`: nickel tails through plated slots | Slots |
| 16 | Production board size | Project notes, repo checklist: \~44 × 44 mm double-sided board at the top cap, 0.8 mm, 4 layers | P0: 43.2 × 74.35 mm side board, 1.6 mm, 6 layers | P0 |
| 17 | Checklist docs | Repo checklist: 10-11 base with STM32WB pin map, ProtoFlow, 10-18 header | Project notes: 10-16 rewrite for the CC2340. Both predate the FEB cells and the cup | This spec |
| 18 | MCU in older notes | EEPROM programming notes: STM32WB, separate IRQ pins | CC2340, one IRQ\_N line | CC2340 (method unchanged) |
| 19 | Mass | Early plan: \~345 g | FEB notes: \~384 g; README: \~400 g with the board | 384–400 g |
| 20 | Learning-cycle load | P0 README: "\~C/5 ≈ 1.2 A" (58E math) | FEB C/5 = 1.3 A | 1.3 A |

## To do: areas not yet specified or built

Firmware is a bring-up skeleton, the GATT spec predates the 10-21 policy, the app exists only on the unmerged `app` branch, and no enclosure part has been printed.

### Firmware (CC2340, LPF3 SDK)

Today: a NoRTOS skeleton (banner, reset reason, heartbeat, IRQ\_N logging) with LaunchPad and dev-board targets, about 10 KB, not yet confirmed running on hardware.

- [ ] P0 board file (`boards/p0.syscfg`): pin map, safe initial states, CCFG
- [ ] Move to FreeRTOS with the BLE5 stack; supervision loop on an RTC wake, watchdog that can't be stopped
- [ ] Gauge driver: SBS reads, `DAStatus2`, Lifetime Data via `ManufacturerBlockAccess()`
- [ ] TPS25751 driver: 4CC commands, `I2Cr`/`I2Cw` passthrough to the BQ25756, `GPsh`/`GPsl`, IRQ\_N decode and event masks
- [ ] TPS25751 patch bundle from TI's Application Customization Tool (4S, bidirectional, 5–20 V / 5 A, BQ25756 ICHG\_REG default 3.25 A with EN\_ICHG\_PIN = 1, GPIO6 output for the gate-drive LDO if GPIO6 is the chosen enable); EEPROM self-programming and repair on every boot
- [ ] Charge loop per the 10-21 policy; dual-port split; solar MPPT and dropout ride-through; pass-through; max SOC hold and recharge point; balancing charge; loop detection
- [ ] Discharge `P_allow` with Source Capability re-advertising, hysteresis, and both port-sharing modes (USB1 priority, Balanced)
- [ ] Gate-drive LDO sequencing (if adopted): enable converter, then `GPsl`; `GPsh` before disable or on charge-done/fault
- [ ] Ship mode entry and exit rules; settings in flash with CRC and safe defaults
- [ ] MCUboot: signed images, swap-with-revert, self-confirm checks, key generation and backup
- [ ] Measure idle current against the \~400 µA estimate and tune advertising

### BLE protocol (GATT)

The spec is v1.1 from 10-16 (`docs/app/ble-gatt-spec.md` on `app`). It needs a revision for the FEB cells, P0 hardware and the 10-21 policy.

- [ ] `design_mah` 6500; product name and hardware revision strings for P0 (`hw_rev` 2)
- [ ] Settings: keep, as a future field clamped to the cell table, `fast_charge`; add a port-sharing mode (USB1 priority / Balanced) beside `usb2_min_w` (the guaranteed USB2 minimum); reserve `led_mode`; consider a `longevity_4v10` flag
- [ ] Charge stages and limit reasons for a ramp model (e.g. `DERATED` with the active limit), replacing `FAST` and the 20 W `THROTTLE`
- [ ] Temperatures record: remove TMP1075 indices, add the two charger TS readings and the gauge FET temperature
- [ ] Gauge Health: replace the three throttle constants with the derate start/end temperatures and sustain power
- [ ] Commands: `IDENTIFY` has no LED on P0; ship-mode wake is charger only
- [ ] Decide Just Works vs a printed passkey, and whether OTA images are encrypted

### iPhone app

Today on `app` (10-16): SwiftUI + CoreBluetooth app with dashboard, charging, temperatures, pack life, settings and developer views, the `MonolithKit` codec package with round-trip tests, a built-in demo pack and the FakePack macOS simulator. Not merged to `master`.

- [ ] Update MonolithKit and the views to the revised GATT spec
- [ ] OTA flow: TI OAD client, MCUboot header and signature check, revert detection
- [ ] First connection to real hardware (LaunchPad, then P0)
- [ ] Decide on the $99/year Apple Developer Program vs 7-day free installs

### Enclosure

- [ ] Fit print of the cup, cap and carrier (JLC3DP MJF) and check the board and cells fit
- [ ] O-ring dunk coupon and hand-pump leak test (vent fitted after the leak test)
- [ ] IP67: a 1 m / 30 min dunk of the sealed pack, plus an IP67-rated vent
- [ ] Bending jig for the nickel tails; gap-filler dispense pattern
- [ ] Outside label: 93.6 Wh, 14.4 V, USB1 / USB2, ratings

### Mass reduction (400 g accepted; keep working on it)

The four cells are 300 g of the \~387 g modelled pack, so the housing and board have about 87 g between them to work on.

- [ ] Get a part-by-part mass table from the cup model (cup, cap, carrier, bumpers, gap filler, board, nickel)
- [ ] Trim the TPU bumpers and carrier webs against the 1 m drop requirement once the first drop test gives real numbers
- [ ] Check cup and cap wall thickness against the IP67 dunk and drop results
- [ ] Weigh the P0 board populated and replace the modelled figure
- [ ] Revisit cells when a higher Wh/kg 21700 is buyable from a real distributor (the cells are the biggest lever)

### Testing and certification

- [ ] Bring-up per `docs/production/p0-bringup-and-training.md`: rails, flash, PD EEPROM load, gauge training
- [ ] Thermal: 100 W full-to-empty logging every sensor, at 10, 25 and 35 °C ambient; tune the derate start and sustain power
- [ ] Charging: 100, 65 and 30 W chargers, dual-port, solar in sun and shade; measure the FEB resistance curve
- [ ] Switching: SW1/SW2 ringing with 0 Ω gate links, inductor and SiZ240DT temperatures
- [ ] Drop: 1 m onto rock on the bumpers, then a leak test
- [ ] PD interoperability with a set of phones, laptops and chargers (a PD analyzer if one is available)
- [ ] No formal certification (personal use and gifts). Write down a per-pack safety test set (cell match, protection trips, 100 W thermal run, dunk test) and run it before gifting; hand-deliver gifts rather than ship them

## Decisions (2026-10-23)

Logan answered the open questions on 2026-10-23. He approved all four loss cuts the same day. The charge-ceiling resistor is the one call still open, laid out in the next section.

| Question | Decision | What it changes |
| --- | --- | --- |
| Dev board | Skipped for good; P0 is the Mk 1 build | `hardware/DevBoard/` stays in the repo as the reviewed reference only |
| Port sharing | A user setting in the app | Two modes: **USB1 priority** (USB2 keeps a guaranteed minimum, 10–30 W, default 20 W) and **Balanced** (the port with the larger contract gives way first). Default: USB1 priority, to match the port labels. Needs a GATT setting and firmware support for both |
| Fast-charge toggle | Kept in the app and GATT for future packs | Firmware always clamps to the cell's datasheet table. On the FEB pack the temperature ramp already reaches the 4.55 A maximum, so the toggle has no headroom today |
| Max SOC default | 95 %, settable 60–100 % | No change |
| Waterproofing | **IP67**: dust-tight, 1 m immersion for 30 min | The O-ring, both USB-C seals and the vent must pass a 1 m / 30 min dunk. The ePTFE vent must be an IP67-rated part |
| Scope | Personal use and gifts to friends | No formal UL, IEC or FCC certification. Hand-deliver gifts: shipping a lithium pack by carrier needs UN38.3. Run a documented safety test set on each pack before gifting it |
| Mass | About 400 g is fine; keep reducing | Mass reduction added to the to-do list |
| Cell data | Treat the FEB table as cell temperature until FEB confirms; get the maker's datasheet before ordering | No design change |
| Source of truth | This spec goes in the repo as `docs/spec.md` and replaces both next-actions files | Repo PR opened |

## Your call: the charge-ceiling resistor (R413 / R513)

Recommendation: keep **11.8 kΩ**. It is the only value of the two that stays under the cell's 4.55 A limit at every tolerance corner, and it costs well under a minute of charge time.

**What the resistor does.** Each BQ25756 has an ICHG pin. The resistor on it sets a hardware charge-current ceiling for that charger: I = K\_ICHG / R, with K\_ICHG = 48–52 A·kΩ for the 5 mΩ RBAT (BQ25756 datasheet §5.5). Firmware normally writes a lower limit over I2C. The resistor is the backstop that still holds if the TPS25751 configuration never loads, the MCU is blank, or firmware writes a wrong value. Software cannot raise the current above the pin: with EN\_ICHG\_PIN = 1 the charger uses the lower of the pin limit and the ICHG register, and the only way past the pin is to clear EN\_ICHG\_PIN, which removes the backstop. So the conservative-default scheme works the other way round: the resistor sits at the cell maximum, the TPS25751 configuration loads a conservative register default (3.25 A, the 5–15 °C cell limit), and the MCU raises the register toward the pin limit once it is running and reading cell temperatures. The dev board used the same scheme (EN\_ICHG\_PIN = 1, EN\_CHG\_BIT\_RESET\_BEHAVIOR = 0, so a watchdog expiry stops charging instead of falling back to the pin).

|  | 11.5 kΩ (policy doc, 10-21 plan) | 11.8 kΩ (applied in the P0 schematic) |
| --- | --- | --- |
| Ceiling, nominal resistor | 4.17–4.52 A | 4.07–4.45 A |
| Worst case with a 1 % resistor at its low end | **4.57 A, above the cell's 4.55 A** | 4.49 A, under |
| Worst-case unit's charging at the top of the ramp | 4.17 A | 4.07 A |
| Effect on charge time | The constant-current stretch is about 2 % faster | Baseline |
| Part | Needs an 11.5 kΩ 0402 1 % part picked and stock-checked | UNI-ROYAL 0402WGF1182TCE (C93752), already in the schematic; 12 kΩ (C25752) is the fallback |

The ceiling is per charger. With both ports charging, two chargers could together push past 4.55 A in hardware, and only firmware and the gauge stop that. So whichever value you pick, set the gauge's charge overcurrent (OCC) just above 4.55 A, around 5 A, as the pack-level backstop.

## Decided: the four loss cuts for P0

Decision (2026-10-23): take all four, with the 9 V gate drive fitted but switchable (default off) so P0 can A/B test it. Together they cut about 1.6 W of the \~12 W the pack makes at 100 W (about 13 %), which buys longer 100 W bursts before the derate starts. Only the inductor change helps much at trail loads.

The numbers come from the 2026-10-21 loss study (`research_notes/Loss reduction/`), which modelled the EVE cells. The FEB pack carries nearly the same currents, so the savings carry over. All are estimates, not measurements.

| Change | 30 W | 100 W | 100 W near empty | 88 W charging | Cost per board | Board impact |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Protection FETs → XRS120N04D | 0.03 W | 0.45 W | 0.77 W | 0.18 W | +$0.14 | Part fields only |
| 2. 9 V gate drive per port | 0 | 0.38–0.43 W | 0.72 W | 0.22 W | +$2–4 | \~25 mm² per port, new parts |
| 3. XGL7030-332 inductor + 500 kHz | 0.16 W | 0.49 W | 0.76 W | 0.26 W | +$3.2 | Same footprint; one resistor change |
| 4. Thicker nickel, copper PACK tails | 0.02 W | 0.26 W | 0.47 W | 0.14 W | \~$3 | None |
| **Total** | **\~0.2 W** | **\~1.6 W** | **\~2.7 W** | **\~0.8 W** |  |  |

### 1. Protection FETs: AGM404AP1 → XNRUSEMI XRS120N04D

- **What:** Q101/Q102 are the gauge's back-to-back main switches; every amp in or out passes through both. The XRS120N04D (LCSC C50314144) has 2.8 mΩ max at the gauge's \~10 V gate drive, against 6.0 mΩ for today's part. Same package and pinout, so only the part fields change.
- **Extra benefits:** about a third of the heat per FET during a short-circuit delay (about 104 W against 300 W), a softer inrush into the bus capacitors because it turns on more slowly, and 5,010 in stock at JLC against 477.
- **Risks:** an obscure vendor with a sloppy datasheet; turn-off at a short is about 3× slower (about 13 µs), still inside its rating; the gauge's short-circuit delay must stay at ≤ \~120 µs. Fallback on the same footprint: Infineon BSZ018N04LS6 ($1.10, fully characterised, only \~200 in stock).
- **Check on P0:** measure the FET pair's resistance with a Kelvin probe at 5 A and 10 A, scope the gate and a controlled short-circuit trip.
- **Verdict:** yes. Cheapest and lowest-risk of the four.

### 2. 9 V gate drive (DRV\_SUP) per port

- **What:** the BQ25756 drives its FET gates from its internal \~5 V REGN rail, and the SiZ240DTs have noticeably higher resistance at 5 V than at 9–10 V. A TPS7A4101 LDO per port, fed from the pack bus, supplies 9 V instead. A Schottky from REGN keeps the old \~5 V drive whenever the LDO is off, so dead-battery wake-up still works. C411/C511 move to 25 V 0805 parts.
- **The rule that shapes it:** TI requires DRV\_SUP to be off whenever the converter is off, and REGN alone isn't proof of that because the ADC can wake REGN. So the LDO enable is an AND of REGN and a control signal, and firmware only turns it on for contracts of 45 W or more.
- **Which control signal:** the study used each TPS25751's GPIO6 (commands `GPsl`/`GPsh`) because the CC2340 had no spare pins. P0 has since freed DIO12, DIO18 and DIO20, so two MCU pins could drive it directly, which is simpler to sequence. Either way, GPIO6 is tied to GND on P0 today and would need freeing if used.
- **Risks:** faster switching edges mean more ringing (the 0 Ω gate links can become 2.2–4.7 Ω without a respin); a short window after the charger stops on its own where 9 V stays on until firmware reacts (worth asking TI); more parts on a crowded board; firmware sequencing to get right.
- **Check on P0:** a free A/B test: toggle the enable at 100 W and read the efficiency change directly.
- **Verdict:** fit it, default off. If firmware isn't ready, the board behaves exactly as today.

### 3. Inductor: Coilcraft XGL7030-332MEC, switching at 500 kHz

- **What:** today's Coilank APS0730M2R2F (2.2 µH, $0.56) sags to about 1.6–1.7 µH under load, which is below the BQ25756's 2.2 µH minimum. The 3.3 µH XGL7030-332 stays at or above 2.2 µH up to 13 A and has lower losses. R412/R512 change from 40.2 kΩ to 49.9 kΩ to move switching from 598 kHz (the chip's maximum) to about 500 kHz.
- **Fit:** today's pads fully cover the Coilcraft terminals, same 3.1 mm height, about +0.3 g each. Coilcraft isn't stocked at JLC, so it is consigned like the SiZ240DT, at about $1.6 more per part in small quantities.
- **Risks:** at the 117 W worst case it runs about 2.2 W, close to its current rating; single source. The 2.2 µH version at 600 kHz saves about the same but keeps the below-minimum problem.
- **Check on P0:** fit the APS0730 on one port and the XGL on the other; compare temperatures and scope the inductor current at the worst case.
- **Verdict:** yes. It is the only cut that helps at 30 W, and it fixes an existing datasheet violation.

### 4. Thicker nickel and copper PACK tails

- **What:** series strips go from 0.15 × 7 mm to 0.2 × 10 mm pure nickel. The PACK tails become 0.2 mm copper with a small nickel pad welded at the cell end. The interconnect drops from about 8.5 mΩ to 4.1 mΩ. Copper also solders into the plated slots better than nickel.
- **Cost:** about $3 of strip, under 1 g, no board change.
- **Risks:** the welder has to weld 0.2 mm reliably (the kWeld is specced for it); buy from a source that sells real nickel, since nickel-plated steel is 2–3× worse.
- **Check:** 4-wire joint resistance on a test coupon before welding the real pack.
- **Verdict:** yes. It can be decided any time before welding.
