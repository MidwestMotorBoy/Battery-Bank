# Monolith — Next Actions
_Rewritten 2026-10-16 to match the repo (dev board rev A8). The 2026-10-09/10/11 history this replaced is in git; the dev-board detail lives in `DevBoard/README.md` (change log items 1–43) and `docs/devboard/`._

## Where things stand (2026-10-16)
- **Nothing has been built, test-fitted or bench-tested yet.**
- **Dev board (`DevBoard/`):** the active work. Schematic rev A8 after four reviews, 429 parts, 6-layer 196 × 115 mm board, every part placed, **not routed**. Cost about $79 per board at 5 boards. Order checklist: `docs/devboard/bringup-config-checklist.md`.
- **Production top board:** not started; it will be drawn from the dev board results. The 2026-10-09 draft is kept only as git tag `product-draft-2026-10-09`.
- **Firmware:** not started. Target is TI's SimpleLink Low Power F3 SDK (CC2340), SysConfig, TI Arm Clang, XDS110 debugger — **not** STM32CubeWB/ST-LINK any more.
- **iPhone app:** started 2026-10-16 on branch `app`: BLE GATT spec v1.0 draft (`docs/app/ble-gatt-spec.md`), `app/MonolithKit` Swift package, plan in `docs/app/README.md`.

## What changed since the 2026-10-11 version of this doc
These supersede the older decisions. Reasons and datasheet checks are in `DevBoard/README.md` (item numbers in brackets).
- **MCU: TI CC2340R5MODA Bluetooth LE module, not the STM32WB1MMC** [40]. Cost-down ($4 vs $20) and JLC had no STM32 module stock. Bought from TI.com and consigned to JLC. 10 usable GPIOs, all assigned, no spares; no 32 kHz crystal (LFOSC). SWD via a 1.27 mm header (J301) on the dev board, pogo pads on production. Bluetooth OTA is TI OAD with MCUboot.
- **Board temperature: three TMP1075 I2C sensors, not five NTCs** [40]: T1 USB1 power stage (0x48), T2 USB2 power stage (0x49), T3 between the connectors (0x4A); DNP footprints T4 heatsink (0x4B) and T5 protection FETs (0x4C). The gauge's internal die sensor stands in for the protection FETs. NTC_EN, the dividers and all analog pins are gone.
- **Cell temperature: one wired 10k NTC per cell on gauge TS1–TS4** [21], not a single mid-pack thermistor. The welded pack's four thermistors plug into the same dev-board headers (J102, J105–J107). Enable TS2–TS4 in gauge data flash.
- **One interrupt line, IRQ_N** [40]: both TPS25751 IRQs, the gauge BTP and the TMP1075 ALERTs are wire-ORed (47k pull-up). Firmware reads all sources on a falling edge.
- **Second-level protection added back in hardware** [33]: BQ294700 per-cell OVP plus the gauge FUSE pin blow a TLC WSFB1514 chemical fuse (F102, 15 A) at the cell top. The MCU's software cross-checks stay as a third layer. This reverses the 2026-10-12 "software only" decision.
- **CHG_INH fails safe** [23]: 47k pull-up on each BQ25756 CE; the MCU drives it low to allow charging, so reset, hang, WDT or an unprogrammed MCU all stop charging. The CC2340 WDT can't be stopped once enabled.
- **Charger FETs: discrete JinYu PGQ04N070** (×8 per board), not the Infineon half-bridges [38]. Cheaper, in stock, every gate can face the BQ25756.
- **Charger bulk capacitors: one polymer (battery side now hybrid polymer, review 4 B-4) plus the HF MLCCs at the FETs** [16, 43], not the 17-MLCC-per-port all-ceramic bank. The MLCC bank lost most of its value to DC bias.
- **Port protection: TPD4S201 CC/SBU protector with liquid detection** [35, 39] replaces the ESD2CAN24 on CC; **TVS2200** flat clamp on VBUS replaces the SMAJ22A [41 C-4]. Liquid detection matters because the receptacle cavity still gets wet in a sealed product.
- **Dev board stack-up: 6 layers, 1.6 mm, 2 oz outer / 0.5 oz inner, ENIG, filled and capped vias** [39]; USB-C connector variant is therefore the 1.6 mm **C55629729**. (Production is still expected to be the 0.8 mm C55629727 on 4 layers; decide when the production board is drawn.)
- **Precision resistors: only the two voltage-setting dividers stay 0.1 %** (BQ25756 charge voltage, PP5V); everything else is 1 % [19]. ICHG 9.1k (5.5 A), ILIM 3.6k (5.6 A), TS network 1.8k/5.6k (hot 94.5 °C, cold −7 °C).
- **Bootstrap diodes added** to each BQ25756 BTST node [20]; the old production BOM was missing them.
- **Sleep budget is now about 230 µA idle (~3 %/month), not 150 µA** (`docs/devboard/power-budget.md`). The two TPD4S201s (~70 µA at the pack) and the gauge (75 µA) dominate. **Ship mode now exists** (reverses the 2026-10-11 "no storage mode"): gauge SHUTDOWN, pack drains 3–4 µA, entered from the app, after two weeks idle, or at RSOC ≤ 5 %, never with a cable attached; wakes on a charger or the button. Gauge Shutdown Voltage 2700 mV.
- **Fuse F101 → F102**: the 1206 fuse was replaced by the chemical fuse as the pack fuse [25, 33].
- **PP5V bulk: 220 µF polymer per port** [8]; **PPHV sink bulk above 100 µF is fine** with soft-start setting 0 or 1 [15].
- **Schematic/PCB tool: KiCad 10 with scripts**, not ProtoFlow. The ProtoFlow section is gone.
- **Datasheets:** 50-odd PDFs in `datasheets/`, indexed in `datasheets/sources.csv`, all on `master` (there is no `dev-board` branch any more).
- **Open inconsistency to settle:** the bring-up checklist (§4, charge sharing) says "one port charging gets the full 5.5 A ('fast charge'); on the other port's attach it drops to 2.8 A", while the charging plan below and the app spec make 1C an **app-enabled option, off by default, 20–80 % only**. Decide which; the GATT spec currently assumes the opt-in version.

## Decisions locked in (current)
- **Pack:** 4S1P, 2×2 bundle of EVE INR21700-58E bare flat-tops, 82 Wh nominal (label 82 Wh, under the 100 Wh carry-on limit). (The Amprius SA112 6.5 Ah was floated on 2026-10-14; the repo and dev board still assume the EVE 58E; if the Amprius goes ahead, redo the gauge data flash, 1C = 6.5 A, and the fast-charge current.)
- **Cell source:** 18650batterystore.com (verify domain; ~$5.99/cell), all four from one batch.
- **Connections:** spot-welded 0.15 mm pure nickel (double layer or wider strip for ~10 A); kWeld + kCap from keenlab; never solder to a cell.
- **Housing:** 0.8 mm blank FR4 wall panels with finger joints, printed Tough 2000 end caps with sealant grooves, ~44.5–45 mm inner cavity (> 1 mm between 21.7 mm cells), IP65 via bonded seams.
- **Ports:** two identical USB-C PD ports, bidirectional, 5–20 V, 5 A each with an e-marked cable, **100 W total**, thermally limited. USB1 has priority; USB2 guaranteed 20 W while both source (app-settable 10–30 W). Thermal throttle: every active port drops to 20 W, restores with hysteresis.
- **Connector:** Shou Han TYPE-C 16PCB IP68, right-angle, 5 A / 20 V; thickness variant to match the board.
- **Per port:** TPS25751D (EEPROM M24512 on its private bus, SafeMode straps, 0x20 / 0x21), TPD4S201, BQ25756 (600 kHz, XAL7030-222 2.2 µH, 5 mΩ sense resistors, 4 × PGQ04N070), TPS62933 PP5V 5 V buck, TVS2200 on VBUS.
- **Gauge / protection:** BQ40Z50-R2 (SMBus 0x0B), AGM404AP1 CHG/DSG FETs, 1 mΩ 2512 Yageo shunt, BQ294700 + chemical fuse second level, software cross-checks third.
- **3.3 V rail:** TPS62177 buck, sleep mode controlled by the MCU (3V3_SLEEP).
- **MCU:** CC2340R5MODA; pins in `docs/devboard/cc2340-pin-budget.md`.
- **Temperature sensing:** 4 cell NTCs (gauge), gauge die, TMP1075 T1–T3 (+ DNP T4/T5), BQ25756 TS NTCs as the hardware charge cutoff. Broken sensors are ignored; full power stays available while ≥ 3 board sensors work.
- **Charging:** gauge is the authority; MCU relays to the charging BQ25756(s). 0.5C default, optional 1C 20–80 % (see the inconsistency above), stop at max SOC (default 95 %, user-settable 60–100 % over BLE), JEITA 0–45 °C, either or both ports, solar MPPT, pass-through.
- **Solar:** Dark Energy 15 W USB-C panel as the reference source; must work from plain 5 V non-PD.
- **Sleep:** ~230 µA idle; ship mode for storage.
- **Bluetooth / app:** custom iOS app (SwiftUI + CoreBluetooth); GATT per `docs/app/ble-gatt-spec.md`; buttonless pairing window (2 min after a cable attaches, or no bonds yet); bonded writes only; signed MCUboot OTA with revert (spec §8).
- **Tools:** KiCad 10 + repo scripts; BQStudio with the EV2400 clone (ordered 2026-10-10); Xcode on the MacBook for the app; Windows PC for TI tools only.

## Charging plan (unchanged in substance)
Stages for 4S EVE 58E (1C = 5.6 A): precharge C/10 below ~3.0 V/cell → 0.5C (2.8 A) normal → optional 1C (5.6 A) between 20–80 % when enabled, the source can supply it and temperatures allow → CV at 16.8 V (only when max SOC = 100 %) → stop at max SOC or 0.02C taper → recharge a few percent below the stop point. Dual-port charging splits the target current by what each source can supply; only one charger regulates CV. Pass-through raises the charge setpoint by the output load, closed on the gauge's net current. Solar: VINDPM + MPPT, ride through panel dropouts, report "solar limited". Temperature: no charging below 0 °C or above 45 °C, JEITA via the gauge, 1C only in a comfortable cell band. Max SOC below 100 % needs a periodic full balancing charge (app setting, default every 30 days) and a "charge to 100 % once" / trip-mode command. Details and the stage table are in the 2026-10-11 version of this doc in git; the firmware-facing encoding is the GATT spec.

## iPhone app (see `docs/app/README.md`)
- Order of work: GATT spec (drafted) → `MonolithKit` (written, run `swift test` on the Mac) → **FakePack** macOS simulator (next) → iOS app → bring-up on the CC2340 dev board.
- FakePack lets the whole app be built before any hardware exists: the MacBook advertises the Monolith GATT with sliders for every value.
- Free Apple ID installs for 7 days; decide on the $99 Developer Program later.

## To order
- [x] EV2400-compatible clone adapter (Amazon) — ordered 2026-10-10
- [ ] 4× EVE INR21700-58E bare flat-top, one batch (18650batterystore.com — confirm domain) — or decide on the Amprius SA112 first
- [ ] kWeld complete kit + kCap (keenlab); 6 V/12 V charger for the kCap; 0.15 mm pure nickel strip
- [ ] CC2340R5MODA module(s) from TI.com (CC2340R5MODAN0MHAR) to consign to JLC, plus one for a bench LaunchPad-style setup if wanted; **a TI LP-EM-CC2340R5 LaunchPad** for firmware/app work before the dev board exists (replaces the STM32WB dev board)
- [ ] XDS110 debugger (on the LaunchPad) — the ST-LINK is no longer needed
- [ ] Dev board hand-fit parts: U201 INA190A5 (DigiKey/Mouser), J301 1.27 mm SWD header, 2.54 mm shunts, pin headers, four wired 10k 103AT NTCs (checklist §0)
- [ ] 100 W USB-C PD charger and a 5 A e-marked cable; 65 W and 30 W chargers for charging validation
- [ ] USB-C inline power meter, to measure the Dark Energy panel
- [ ] Thermal gap pad and fish paper/Kapton (production)
- [ ] Apple Developer Program decision (~$99/year)

## Gauge adapter checks (when it arrives)
- [ ] Install TI BQStudio on the Windows PC and confirm it sees the adapter as an EV2400 (inside the Amazon return window)
- [ ] Confirm SMBus connection (clock, data, ground; the pack powers the gauge)
- [ ] Before writing anything to a gauge, read and save its full data flash
- [ ] No hubs or loose cables during writes

## Dev board: order and bring-up
Follow `docs/devboard/bringup-config-checklist.md` (rev A8). Headline items:
- [ ] Finish routing (hand-route the power stages per README item 32, then the rest); silkscreen pass; DRC clean; fix the U403/U503 library-mismatch warning
- [ ] Resolve the review 4 leftovers: EV2400 procedure (A-2), 28 parts without an MPN, U301/J301 sourcing, stale STM32 text in `circuit-description.md`
- [ ] Order: JLC 6-layer 1.6 mm, consign U301, hand-fit list in checklist §0
- [ ] First power with no cells (§1), then cells in and gauge configured (§2), TPS25751 EEPROM bundles (§3), MCU firmware (§4), measurements (§5)
- [ ] Gauge learning cycle per TI SLUA903 on the real welded pack; export the golden image to the repo

## Firmware (CC2340, LPF3 SDK) — not started
- [ ] Project skeleton: BLE5-Stack peripheral with the Monolith GATT from the spec, MCUboot with signed images, WDT, RTC-wake supervision loop
- [ ] Drivers: SMBus gauge, TPS25751 4CC commands and IRQ_N decode, TMP1075 one-shot/continuous modes, CHG_INH / EN_5Vx / 3V3_SLEEP per `mcu-io-power-states.md`
- [ ] Charge policy per the charging plan; power sharing (USB1 priority, 100 W cap, never exceed it even briefly); pass-through; loop detection; thermal throttle and sensor-fault rules; ship mode
- [ ] Settings in flash with CRC and safe defaults (95 %, fast off, USB2 20 W, auto full charge 30 days)
- [ ] Pairing window, bonding, 4 bonds max, cable-plug gesture to clear bonds
- [ ] Measure the real idle current (BLE advertising rate is the biggest unknown) against the 230 µA budget

## Production board (after dev-board results)
- [ ] Redraw from the dev board: same power stages, double-sided 44 × 44 mm-class board, top side JLC-assembled facing the heatsink plate, bottom side hand-solder only (small-buck inductors, bulk caps, shunt, pads, pogo pads for SWD and SMBus)
- [ ] Decide layer count/thickness and the matching connector variant; 2 oz outer copper if JLC offers it at that thickness
- [ ] Top cap: port openings sealing on the connectors' 10.25 × 4.45 mm flange, board edge ~2.9 mm behind the cap face, seat for the aluminum plate, antenna window clear of cells and plate
- [ ] Heatsink: JLC aluminum-core plate over the top side, stepped gap pad (inductors ~3.1 mm vs FETs ~1 mm), notched clear of the module antenna, T4 TMP1075 fitted under it
- [ ] Thermal and charging validation runs (100 W full-to-empty logging every sensor, one sensor disabled at a time, charge from 100/65/30 W, dual-port, solar in sun and shade)
- [ ] Update the `master` README's remaining old-design references once the production schematic exists

## Open decisions
- [ ] 1C fast charge: app opt-in 20–80 % (this doc, GATT spec) vs single-port default (bring-up checklist §4)
- [ ] EVE 58E vs Amprius SA112
- [ ] Production: keep the LED? (`led_mode` in the app settings is reserved otherwise)
- [ ] OTA image encryption on top of signing (spec §8): only needed if update files are ever posted publicly
- [ ] Just Works pairing vs a printed passkey
