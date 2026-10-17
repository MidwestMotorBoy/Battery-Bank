# Firmware ↔ app interface: brief for whoever writes the pack firmware

_Written 2026-10-16, after the iPhone app was tested end to end against FakePack on a real iPhone. Read this before writing any BLE or gauge code on the CC2340._

## What this is

The iPhone app is done for v1 and tested over a real radio. The firmware isn't started. This doc tells the firmware author what the app expects, where every byte should come from on this board, and what testing already turned up. It doesn't repeat the byte layouts.

**The contract is [`ble-gatt-spec.md`](ble-gatt-spec.md) (protocol 1.1).** If this doc and the spec disagree, the spec wins; fix this doc.

Read in this order:
1. `ble-gatt-spec.md`, all of it. §1 (rules), §4 (characteristics), §6 (pairing) and §7 (connection behaviour) are what the app depends on.
2. This doc.
3. `app/FakePack/PeripheralServer.swift` and `app/FakePack/PackModel.swift`: a working peripheral that the app has been tested against. **Treat it as the reference implementation** for the GATT table, permissions, notification rates, command handling and the derived fields (flags, time to full). It's about 480 lines of Swift; port its behavior, not its code.
4. `app/MonolithKit/Sources/MonolithKit/Records.swift`: `encode()` on each record is the byte-exact reference for what firmware must send. `swift test` in `app/MonolithKit` checks lengths and sentinels.

## Ground rules for changing the interface

- Don't move, resize or retype a field within protocol major 1. New fields go at the end of a record; new characteristics get the next UUID (`DDE7010B`…) and a minor bump (spec §1).
- Any change touches four places, in this order: `ble-gatt-spec.md` → `MonolithKit` (+ a test) → `FakePack` → the app. Firmware follows the spec, so a change that isn't in the spec doesn't exist.
- Set `proto_major`/`proto_minor` in Protocol Version to the spec version the firmware implements. The app refuses a major it doesn't know and accepts any minor.

## Hardware the GATT is fed from

All on the one I2C/SMBus (see `docs/devboard/cc2340-pin-budget.md`, `docs/project/tps25751-eeprom-programming.md`):

| Chip | Address | Feeds |
|---|---|---|
| BQ40Z50-R2 gauge | SMBus 0x0B | SOC, pack V/I, cells, remaining energy, times, Gauge Health, Pack Life, cell temps, gauge-die temp |
| TPS25751 USB1 / USB2 | 0x20 / 0x21 | Ports: state, PD contract, role, faults |
| TMP1075 T1–T5 | 0x48–0x4C | Board temperatures (T4, T5 DNP on the dev board → report "not fitted") |
| BQ25756 ×2 | (charger) | Charge stage/current, input power |

The MCU is the CC2340R5MODA on the LPF3 SDK with BLE5-Stack (`docs/project/monolith-next-actions.md`, Firmware section). The gauge's BTP alert and both TPS25751 interrupts share one line, IRQ_N; on a falling edge, read all three to find the source.

## The GATT table to build

Mirror `PeripheralServer.buildServices()`:

| Service / characteristic | UUID | Properties | Permission | Size | When it changes |
|---|---|---|---|---|---|
| Battery Service | `180F` | | | | |
| · Battery Level | `2A19` | read, notify | open | 1 | with Status |
| Device Information | `180A` | | | | |
| · Manufacturer / Model / FW rev / HW rev / Serial | `2A29` `2A24` `2A26` `2A27` `2A25` | read | open | strings | static |
| Monolith | `DDE70001-422D-4970-B281-8D5F2C2119C3` | | | | |
| · Protocol Version | `DDE70101` | read | open | 8 | static |
| · Status | `DDE70102` | read, notify | open | 36 | ≤ 1/s on change, ≥ every 10 s |
| · Ports | `DDE70103` | read, notify | open | 16 | on any port event + every Status heartbeat |
| · Temperatures | `DDE70104` | read, notify | open | 22 | ≤ 5 s attached / 60 s idle, immediately on fault change |
| · Settings | `DDE70105` | read, write | read open, **write encrypted + bonded** | 8 | on write |
| · Command | `DDE70106` | write | **encrypted + bonded** | 1–4 | |
| · Command Result | `DDE70107` | notify | open | 4 | ≤ 1 s after each Command |
| · Gauge Health | `DDE70108` | read | open | 16 | read on connect |
| · Pack Life | `DDE7010A` | read | open | 48 | read on connect, on demand |
| · Debug Log | `DDE70109` | notify | open | ≤ 48 | dev builds only |

The full 128-bit form of every short `DDE7xxxx` is `DDE7xxxx-422D-4970-B281-8D5F2C2119C3`.

**Include the GATT Service Changed characteristic and keep the table static within a firmware image.** iOS caches the GATT table of a *bonded* peripheral. If an OTA update adds a characteristic, the bonded phone won't see it unless firmware sends a Service Changed indication after the update. Testing already showed the app depends on service-change events (below).

## Where every field comes from

SBS commands are the BQ40Z50-R2's (TRM SLUUBK0, ch. 14). "MAC" means `ManufacturerBlockAccess()` (SBS `0x44`) with the given subcommand.

### Status (spec §4.2)

| Field | Source |
|---|---|
| `soc_pct` | SBS `0x0D` RelativeStateOfCharge. Also the Battery Level value |
| `charge_stage`, `limit_reason`, `charge_target_ma` | firmware's charge controller (charging plan in `monolith-next-actions.md`) |
| `flags` | assembled by firmware; see `PackModel.statusRecord()` for how each bit is derived |
| `pack_mv` | SBS `0x09` Voltage |
| `pack_ma` | SBS `0x0A` Current. The gauge's sign (+ = charging) is already the spec's |
| `remaining_dwh` | SBS `0x0F` RemainingCapacity is mAh by default; convert with pack voltage, or set BatteryMode[CAPM] for 10 mWh units. Pick one and note it in code |
| `time_to_empty_min` | SBS `0x12` AverageTimeToEmpty; its 65535 = n/a matches the spec's `0xFFFF` |
| `time_to_full_min` | **not** the gauge's AverageTimeToFull when `max_soc_pct` < 100: that's time to 100 %. Compute time to the active limit (`PackModel` does: missing Wh ÷ charge W) |
| `cell1..4_mv` | SBS `0x3F`, `0x3E`, `0x3D`, `0x3C` (CellVoltage1 is `0x3F`) |
| `output_dw`, `input_dw` | sum of the ports' measured power, split by sign |
| `power_state` | firmware power state (`docs/devboard/mcu-io-power-states.md`) |
| `sensors_ok_board` | count of working board sensors (fitted and not faulted) |
| `uptime_s` | seconds since MCU reset |

### Ports (§4.3)

`state`, `contract_mv`/`contract_ma` and role come from each TPS25751's PD status and active contract. `power_dw` is measured power, positive = out of the pack. The app computes current as power ÷ contract voltage, so `contract_mv` must be the actual VBUS level (5000 for a non-PD 5 V source), not 0, whenever power flows.

### Temperatures (§4.4)

Order and sentinels are fixed by the spec: cells 1–4 from the gauge's TS1–TS4, slot 4 the gauge die, slots 5–9 TMP1075 0x48–0x4C. Send `0x7FFE` for DNP sensors (T4 and T5 on the dev board) and `0x7FFF` + the fault-mask bit for a sensor firmware has stopped trusting. The app draws all ten on a pack diagram and highlights any within 5 °C of its throttle point, so the throttle constants in Gauge Health must be the ones the code really uses.

### Gauge Health (§4.7)

`full_charge_mah` SBS `0x10`, `design_mah` SBS `0x18`, `cycle_count` SBS `0x17`, `soh_pct` SBS `0x4F` (check the returned layout against TRM §14.41 on hardware). `gauge_status` bits (§5.8) come from OperationStatus/SafetyStatus. `cell_delta_mv` is tracked by firmware at each charge termination. The `throttle_*_dc` fields are firmware constants.

### Pack Life (§4.9): assembling 48 bytes from five gauge blocks

Read MAC `0x0060`–`0x0064` through `ManufacturerBlockAccess()`. **Don't use SBS `0x60`–`0x64`:** those are not readable once the gauge is sealed (TRM Table 14-1: the MAC route is "Available in SEALED: Yes"; the SBS commands are `—` for SE). Each block is little-endian:

| Block | Layout (byte offsets) |
|---|---|
| 1 `0x0060` | 0–7 Cell 1–4 Max V (u16 mV) · 8–15 Cell 1–4 Min V · 16 Max Delta Cell V · 18 Max Charge Current (mA) · 20 Max Discharge Current · 22 Max Avg Dsg Current · 24 Max Avg Dsg Power (cW) · 26 Max Temp Cell (i8 °C) · 27 Min Temp Cell · 28 Max Delta Cell Temp · 29 Max Temp Int · 30 Min Temp Int · 31 Max Temp FET |
| 2 `0x0061` | 0 Shutdowns · 1 Partial resets · 2 Full resets · 3 WDT resets · 4–7 CB Time Cell 1–4 (u8, 2 h units) |
| 3 `0x0062` | 0 Total FW Runtime · 2 UT · 4 LT · 6 STL · 8 RT · 10 STH · 12 HT · 14 OT (all u16, 2 h units) |
| 4 `0x0063` | (count u16, last-cycle u16) pairs: COV, CUV, OCD1, OCD2, OCC1, OCC2, AOLD, ASCD |
| 5 `0x0064` | pairs: ASCC, OTC, OTD, OTF, Valid Charge Term, Qmax Update, Ra Update, Ra Disable |

Then:
- `cell_max_mv` = max of the four Max V values, and `cell_min_mv` = min of the four Min V values. The gauge's defaults (0 and 32767) already match the spec's "never measured".
- The temperature fields copy straight across; −128/127 are the gauge's own "never measured" defaults.
- `safety_events` = saturating sum of the 12 safety counts (blocks 4 and 5, up to OTF). `last_safety_cycle` = the largest "last" value among events whose count is > 0, or `0xFFFF` if none.
- `full_charges` = Valid Charge Term count; `qmax_updates` = Qmax Update count; `max_balance_time_2h` = max of CB Time Cell 1–4.
- `manufacture_date` = SBS `0x1B` ManufacturerDate (readable sealed). Program it at production, or the app shows no age.
- `life_flags` bit 0 = ManufacturingStatus() (MAC `0x0057`) bit 5 `LF_EN`.
- `temp_t1_c…`: **the gauge's data flash isn't readable when sealed** (TRM §11.5.1, §14.1.67), so firmware can't read T1–T6 at runtime. Compile them in as constants that match the gauge configuration image (*Advanced Charge Algorithm › Temperature Ranges*), in the order T1, T2, T5, T6, T3, T4. The gauge defaults are 0, 12, 20, 25, 30, 55 °C; this pack's will differ (charging is 0–45 °C).

Rate-limit the five block reads to once a minute. The data changes slowly, and the gauge only flushes lifetime RAM to flash every 10 h.

**Gauge configuration prerequisite: set `LF_EN` before sealing**, either through MAC `0x0023` (Lifetime Data Collection) or in the configuration image. Without it the gauge records nothing and the app's Health tab says "not recorded". Add it to `docs/devboard/bringup-config-checklist.md` when the gauge configuration is written.

## Behavior the app relies on (tested against FakePack on an iPhone 15 Pro Max)

- **Connect sequence.** The app discovers services, reads Protocol Version, then subscribes to Status, Ports, Temperatures and Command Result, and reads Status, Ports, Temperatures, Settings, Gauge Health and Pack Life. Firmware should answer reads with current values, not wait for a notification cycle.
- **Status heartbeat ≤ 10 s, always.** The app treats 15 s without a Status notification as "No data". It greys the screen, then cancels and reconnects. Firmware that only notifies on change will look dead whenever the pack is idle.
- **Service Changed / services disappearing.** When the Monolith service disappears without the link dropping, the app rediscovers every 3 s until it's back, then reruns the connect sequence. This is what happens on a firmware reboot that keeps the link, and after OTA.
- **Disconnects are routine.** After `ENTER_OTA`, `RESET_MCU` and `CLEAR_BONDS` the app expects the link to drop and treats the drop as success. It keeps a pending connect to the remembered pack, so the pack only needs to start advertising again.
- **Idle drop.** Firmware may drop a connection with no subscriptions after 60 s (§7). The app subscribes immediately, so this only catches stray scanners.
- **Settings writes are whole-record.** The app reads, edits and writes all 8 bytes with reserved bytes 0. Range-check every field and reject the whole write with ATT error `0x80` if any is bad; the app shows "rejected as out of range, nothing changed". A rejected write must change nothing. After a successful write the app re-reads Settings.
- **Pairing.** Writes to Settings or Command on an unencrypted link make iOS run pairing (Just Works) on its own. Firmware only needs to accept pairing inside the window (§6) and return "insufficient encryption/authentication" outside it. The app then shows the ATT error.
- **Command Result within 1 s**, with the opcode echoed. The app waits 2 s, then reports "the pack didn't confirm the command".
- **Unknown values.** The app shows unknown enum values as "Unknown (n)" and parses records that are longer or shorter than expected (missing fields = "not available"). Firmware can add enum values and append fields without breaking v1 apps.

## Pitfalls already found

1. **Notification size vs ATT MTU.** A notification carries at most MTU − 3 bytes: 20 at the default MTU of 23, too small for Status (36) or Temperatures (22). iOS normally negotiates 185 or more, so in practice this is fine. But firmware must check the negotiated MTU before notifying. If it's still 23, send the first MTU − 3 bytes (the app parses a short record as "fields not available") rather than nothing, so the heartbeat continues. Reads aren't affected: long reads handle Pack Life (48) at any MTU.
2. **Sealed gauge.** Anything from data flash, and the SBS-mapped lifetime and status blocks, are off-limits once sealed. Use the MAC route and compile-time constants, as above. Seal the gauge last at production.
3. **iOS caches the GATT table of bonded packs.** See Service Changed above. After any change to the table during development, toggle Bluetooth on the phone or "Forget" the pack if you see stale characteristics.
4. **FakePack on a Mac isn't a perfect model of a real pack.** The Mac keeps a Continuity link to the phone, so "pack gone" showed up as services vanishing rather than a disconnect. Real hardware will mostly produce real disconnects; the app handles both.

## Testing firmware with what already exists

- **The app itself:** `app/README.md` and the Mac setup in this repo build and install it on an iPhone (free Apple ID, 7-day profile). Its Developer screen (Settings › Developer) shows raw bytes for every record, the firmware's Debug Log notifications, and the app's own BLE event log.
- **nRF Connect or LightBlue** on the phone for raw reads and writes; `app/README.md` has the FakePack checks, and the same expected bytes apply to firmware.
- **Byte vectors:** write a test in `app/MonolithKit/Tests` that encodes the record you're implementing with known values, print the hex, and compare it against what firmware produces.
- **The demo pack in the app** shows how each screen should look with sensible data, for comparison.

## Conformance checklist

- [ ] Advertises name `Monolith` with Battery Service `180F`, and the Monolith UUID in the scan response (§2)
- [ ] GATT table as above, including Service Changed; Settings and Command writes require an encrypted, bonded link
- [ ] Protocol Version reports 1.1 and real firmware semver, `hw_rev` and build
- [ ] Status notifies ≤ 1/s on change and ≥ every 10 s idle; Battery Level matches `soc_pct`
- [ ] Ports notify on every port event; `contract_mv` set whenever power flows
- [ ] Temperatures: sentinels for DNP and broken sensors, fault mask, notify on fault change
- [ ] Settings: whole-record range check, `0x80` on any bad field, nothing changes on rejection, persisted with CRC
- [ ] Commands: every opcode answered within 1 s; arg magic bytes checked; `ENTER_OTA` checks SOC ≥ 20 % and output ≤ 20 W and reports which check failed in `detail`
- [ ] Gauge Health throttle constants equal the ones the throttle code uses
- [ ] Pack Life from MAC `0x0060`–`0x0064` while sealed; `LF_EN` set; T1–T6 constants match the gauge configuration; ManufacturerDate programmed
- [ ] MTU checked before notifying; short notifications rather than none at MTU 23
- [ ] App test pass on a phone: connect, Pack tab live, pairing on first save, Identify OK, Health tab populated, pull power → app shows Reconnecting → pack returns → app reconnects on its own

## Open decisions for the firmware author

- `remaining_dwh` source: CAPM mode vs mAh × voltage.
- The exact TPS25751 registers for contract and role, and where measured port power comes from on this board (`docs/devboard/circuit-description.md`).
- `cell_delta_mv` in Gauge Health: tracked by firmware at charge termination, or taken from the lifetime Max Delta Cell V (which never goes down).
- The MCUboot options the LPF3 SDK actually exposes (spec §8 is the requirement).
