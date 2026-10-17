# Monolith BLE GATT specification

**Protocol version 1.0** · draft 2026-10-16

This is the contract between the pack firmware (CC2340R5MODA, TI LPF3 SDK) and the iPhone app (SwiftUI + CoreBluetooth). Both are built from this file. `app/MonolithKit` is the Swift encoding of it; the firmware's GATT table must match it byte for byte.

## 1. Rules that never change

- **Byte order:** little-endian, always.
- **Fixed layouts, append-only.** Within a major version, fields are never moved, resized or re-typed. New fields are appended at the end. A reader must accept a value *longer* than it expects (ignore the tail) and must treat a value *shorter* than the fields it needs as "field not available", not as an error.
- **Versioning:** `protocol_version` is `major.minor`. Minor bumps only append fields, add characteristics or add enum values. A major bump may change anything; the app refuses to show live data from a major it doesn't know.
- **Unknown enum values** are shown as "Unknown (n)", never crash, never hide the rest of the record.
- **Invalid sentinel:** `0x7FFF` for a signed 16-bit field means "no reading / sensor broken". `0xFFFF` for an unsigned 16-bit field means "not available / not applicable".
- **ATT MTU:** firmware requests a 128-byte MTU on connect (iOS normally grants 185). No characteristic is longer than 48 bytes. A notification carries at most MTU − 3 bytes, so at the default 23-byte MTU (20-byte payload) Status and Temperatures don't fit; if the exchange fails, firmware notifies the first MTU − 3 bytes, which readers treat as a shorter record (fields not available). Reads use long reads and are unaffected.
- **Units are in the field name** (`_mv`, `_ma`, `_dc` = deci-°C, `_dw` = deci-watt, `_dwh` = deci-Wh, `_min`).
- **Security:** LE Secure Connections pairing. Bonding required for every write and for the Command characteristic. Reads and notifications of status are allowed unbonded so a quick check works with any phone. See §6.

## 2. Advertising

| Field | Value |
|---|---|
| Local name | `Monolith` (complete name in the scan response; shortened `Mono` if space is short) |
| Advertised 16-bit services | `0x180F` Battery Service |
| Scan response 128-bit service | Monolith Service UUID (§3) |
| Manufacturer data | none in v1 (reserved: company ID `0xFFFF` dev ID, then `u8 soc_pct`, `u8 flags` for a future no-connect glance) |
| Interval, idle (S2) | 1000–1250 ms, TX ≤ +4 dBm (TPS62177 sleep-mode current limit, see `docs/devboard/mcu-io-power-states.md`) |
| Interval, cable attached (S0/S1) | 200–300 ms |
| Connectable | always; pairing accepted only inside the pairing window (§6) |

App-side filter: scan for `0x180F`, then match on local name `Monolith` or on the Monolith Service UUID in the scan response.

## 3. UUIDs

Base UUID: `DDE7xxxx-422D-4970-B281-8D5F2C2119C3`. The `xxxx` slot is the short ID below.

| Short | Name | Props | Len | Section |
|---|---|---|---|---|
| **Standard** | | | | |
| `0x180F` | Battery Service | | | |
| `0x2A19` | Battery Level (`u8` SOC %) | R, N | 1 | |
| `0x180A` | Device Information Service | | | |
| `0x2A29` | Manufacturer Name String | R | | `"Monolith"` |
| `0x2A24` | Model Number String | R | | e.g. `"MONO-4S-100"` |
| `0x2A26` | Firmware Revision String | R | | e.g. `"0.1.0+42"` |
| `0x2A27` | Hardware Revision String | R | | e.g. `"devboard-A7"` |
| `0x2A25` | Serial Number String | R | | pack serial, from gauge or flash |
| **Monolith service** `DDE70001` | | | | |
| `DDE70101` | Protocol Version | R | 8 | §4.1 |
| `DDE70102` | Status | R, N | 36 | §4.2 |
| `DDE70103` | Ports | R, N | 16 | §4.3 |
| `DDE70104` | Temperatures | R, N | 22 | §4.4 |
| `DDE70105` | Settings | R, W (bonded) | 8 | §4.5 |
| `DDE70106` | Command | W (bonded) | 1–4 | §4.6 |
| `DDE70107` | Command Result | N | 4 | §4.6 |
| `DDE70108` | Gauge Health | R | 16 | §4.7 |
| `DDE70109` | Debug Log | N | ≤ 48 | §4.8, dev builds only |
| `DDE7010A` | Pack Life | R | 48 | §4.9, added in 1.1 |

Type abbreviations: `u8/u16/u32` unsigned, `s16/s32` signed two's complement.

## 4. Characteristics

### 4.1 Protocol Version — `DDE70101`, read, 8 bytes

| Off | Type | Field | Notes |
|---|---|---|---|
| 0 | u8 | `proto_major` | 1 |
| 1 | u8 | `proto_minor` | 1 (1.1) |
| 2 | u8 | `fw_major` | firmware semver |
| 3 | u8 | `fw_minor` | |
| 4 | u8 | `fw_patch` | |
| 5 | u8 | `hw_rev` | 0 = unknown, 1 = dev board, 2 = production |
| 6 | u16 | `fw_build` | CI build number or git short count; 0 if none |

The app reads this first, before subscribing to anything.

### 4.2 Status — `DDE70102`, read + notify, 36 bytes

Notified on change, rate-limited to one per second while connected; at least one every 10 s as a heartbeat.

| Off | Type | Field | Notes |
|---|---|---|---|
| 0 | u8 | `soc_pct` | 0–100, gauge RelativeStateOfCharge; same value as Battery Level |
| 1 | u8 | `charge_stage` | enum §5.1 |
| 2 | u8 | `limit_reason` | enum §5.2, why the pack isn't doing more |
| 3 | u8 | `reserved` | 0 |
| 4 | u16 | `flags` | bitfield §5.3 |
| 6 | u16 | `pack_mv` | pack voltage |
| 8 | s16 | `pack_ma` | pack current; **positive = into the cells (charging), negative = out (discharging)**, gauge convention |
| 10 | u16 | `remaining_dwh` | remaining energy, 0.1 Wh |
| 12 | u16 | `time_to_empty_min` | `0xFFFF` = not discharging / unknown |
| 14 | u16 | `time_to_full_min` | `0xFFFF` = not charging / unknown |
| 16 | u16 | `cell1_mv` | |
| 18 | u16 | `cell2_mv` | |
| 20 | u16 | `cell3_mv` | |
| 22 | u16 | `cell4_mv` | |
| 24 | s16 | `charge_target_ma` | current the charge controller is asking for; 0 if not charging |
| 26 | u16 | `output_dw` | total power delivered out of both ports, 0.1 W |
| 28 | u16 | `input_dw` | total power taken in from both ports, 0.1 W |
| 30 | u8 | `power_state` | enum §5.4 (S0 charging … S5 ship) |
| 31 | u8 | `sensors_ok_board` | number of working board temperature sensors (0–5) |
| 32 | u32 | `uptime_s` | seconds since last MCU reset |

### 4.3 Ports — `DDE70103`, read + notify, 16 bytes

Two 8-byte records, USB1 (priority port) first, USB2 second. Notified on any port event (attach, detach, new contract, role swap, fault) and with every Status heartbeat.

| Off | Type | Field | Notes |
|---|---|---|---|
| 0 | u8 | `state` | enum §5.5 |
| 1 | u8 | `flags` | bitfield §5.6 |
| 2 | u16 | `contract_mv` | negotiated VBUS, 0 if none (5000 for a non-PD 5 V source) |
| 4 | u16 | `contract_ma` | negotiated current limit, 0 if none |
| 6 | s16 | `power_dw` | measured power, 0.1 W; **positive = out of the pack (sourcing), negative = into the pack (sinking)** |

### 4.4 Temperatures — `DDE70104`, read + notify, 22 bytes

Ten `s16` deci-°C readings in a fixed order, then a fault mask. `0x7FFF` = broken (firmware's sensor-fault rule tripped) and `0x7FFE` = not fitted (DNP footprint). Notified at most every 5 s while a cable is attached, every 60 s idle, and immediately when a sensor changes fault state or the throttle state changes.

| Off | Index | Source | Notes |
|---|---|---|---|
| 0 | 0 | Cell 1, gauge TS1 | wired NTC on the cell |
| 2 | 1 | Cell 2, gauge TS2 | |
| 4 | 2 | Cell 3, gauge TS3 | |
| 6 | 3 | Cell 4, gauge TS4 | |
| 8 | 4 | Gauge die (BQ40Z50-R2 internal) | stands in for the protection FETs |
| 10 | 5 | T1, USB1 power stage (TMP1075 0x48) | |
| 12 | 6 | T2, USB2 power stage (TMP1075 0x49) | |
| 14 | 7 | T3, between the USB-C connectors (TMP1075 0x4A) | |
| 16 | 8 | T4, heatsink plate (TMP1075 0x4B, DNP) | `0x7FFE` when not fitted |
| 18 | 9 | T5, protection FETs (TMP1075 0x4C, DNP) | `0x7FFE` when not fitted |
| 20 | — | u16 `fault_mask` | bit *i* set = sensor *i* is marked broken by firmware |

The 20 W thermal throttle state itself is `flags.THROTTLE` in Status (§5.3); the sensor that tripped it is `limit_reason` = `TOO_HOT` plus whichever index is nearest its limit — the app shows all ten and highlights any within 5 °C of its throttle point. Throttle points are firmware constants reported in Gauge Health (§4.7) so the app never hard-codes them.

### 4.5 Settings — `DDE70105`, read + write (bonded), 8 bytes

Persisted in MCU flash with a CRC; firmware falls back to defaults on a bad record. Writes are **whole-record**: the app reads, modifies, writes all 8 bytes. Firmware range-checks every field and rejects the whole write with `0x80` (Application Error, "value out of range") if any field is bad; a rejected write changes nothing.

| Off | Type | Field | Range / default |
|---|---|---|---|
| 0 | u8 | `max_soc_pct` | 60–100, **default 95** |
| 1 | u8 | `fast_charge` | 0 off (default) / 1 on; 1C between 20–80 % when the source and temperatures allow |
| 2 | u8 | `usb2_min_w` | 10–30, default 20. Guaranteed USB2 budget while both ports source |
| 3 | u8 | `led_mode` | 0 off, 1 normal (default), 2 dim/night. Reserved on production if there's no LED |
| 4 | u8 | `auto_full_charge_days` | 0 = never, else do a 100 % balancing charge if none in this many days; default 30 |
| 5 | u8 | `reserved5` | write 0 |
| 6 | u8 | `reserved6` | write 0 |
| 7 | u8 | `reserved7` | write 0 |

Trip mode and "charge to 100 % once" are not settings; they are commands (§4.6), because they expire on their own.

### 4.6 Command — `DDE70106`, write (bonded), 1–4 bytes; Command Result — `DDE70107`, notify, 4 bytes

Write `u8 opcode` followed by up to 3 bytes of argument. Firmware answers with a Command Result notification within 1 s: `u8 opcode, u8 result (§5.7), u16 detail`. The app treats a missing result as a failure.

| Opcode | Name | Args | Effect |
|---|---|---|---|
| `0x01` | `CHARGE_TO_100_ONCE` | — | Next charge ignores `max_soc_pct` and runs a full balancing charge, then reverts |
| `0x02` | `TRIP_MODE` | u8 enable, u8 hours (default 48 if 0) | Charge to 100 % for the next *hours*, then revert to `max_soc_pct` |
| `0x03` | `CLEAR_BONDS` | u8 `0xA5` | Forget all bonded phones, then drop this connection. Arg must be `0xA5` |
| `0x04` | `ENTER_OTA` | u8 `0x5A` | Reboot into OAD (MCUboot update mode, §8). Arg must be `0x5A`; refused unless SOC ≥ 20 % and output ≤ 20 W; `detail` says which check failed |
| `0x05` | `SHIP_MODE` | u8 `0x3C` | Enter S5 ship/storage: gauge SHUTDOWN, pack unpowered until a charger or the button wakes it. Refused while any cable is attached |
| `0x06` | `IDENTIFY` | — | Blink the LED for 5 s so you know which pack you're connected to |
| `0x07` | `RESET_MCU` | u8 `0x99` | Warm reset of the MCU only; ports and gauge keep running |
| `0x08` | `OPEN_PAIRING` | — | Open the pairing window for 2 min (only accepted from an already-bonded phone, to add a second phone) |
| `0x09` | `CLEAR_SENSOR_FAULTS` | — | Re-test all board sensors now instead of waiting for the periodic retry |

### 4.7 Gauge Health — `DDE70108`, read, 16 bytes

Slow-changing numbers from the BQ40Z50-R2 plus firmware's throttle constants. Read on connect; no notify.

| Off | Type | Field | Notes |
|---|---|---|---|
| 0 | u16 | `full_charge_mah` | gauge FullChargeCapacity |
| 2 | u16 | `design_mah` | 5600 |
| 4 | u16 | `cycle_count` | |
| 6 | u8 | `soh_pct` | gauge StateOfHealth |
| 7 | u8 | `gauge_status` | bitfield §5.8 |
| 8 | u16 | `cell_delta_mv` | max − min cell at last full charge, a balance indicator |
| 10 | s16 | `throttle_cell_dc` | cell temperature that triggers the 20 W throttle, deci-°C |
| 12 | s16 | `throttle_board_dc` | board (T1–T5) temperature that triggers it |
| 14 | s16 | `throttle_conn_dc` | connector (T3) temperature that triggers it |

### 4.8 Debug Log — `DDE70109`, notify, up to 48 bytes

UTF-8 text, one line per notification, no terminator. Only compiled into dev firmware. The app shows it in a hidden developer screen.

### 4.9 Pack Life — `DDE7010A`, read, 48 bytes (added in 1.1)

The BQ40Z50-R2's Lifetime Data (TRM SLUUBK0 ch. 10; MAC 0x0060–0x0064 read through `ManufacturerBlockAccess()`, which works sealed, unlike SBS 0x60–0x64) condensed into one record, plus the pack's manufacture date. Firmware reads the five blocks on connect and when the app reads this characteristic, at most once a minute. Read on demand; no notify.

The gauge only collects lifetime data while `ManufacturingStatus()[LF_EN]` = 1 and writes RAM to flash every 10 h, so a value can be up to 10 h behind and is lost on a full reset before a flush. Bit 0 of `life_flags` says whether collection is on. If it's off, the app says "not recorded" rather than showing zeros.

| Off | Type | Field | Source / notes |
|---|---|---|---|
| 0 | u16 | `manufacture_date` | SBS `ManufacturerDate()` 0x1B: day + month·32 + (year − 1980)·512. 0 = not set |
| 2 | u16 | `runtime_2h` | Block 3 Total FW Runtime, 2 h units |
| 4 | u16 | `time_ut_2h` | Block 3 time below T1, 2 h units |
| 6 | u16 | `time_lt_2h` | T1–T2 |
| 8 | u16 | `time_stl_2h` | T2–T5 |
| 10 | u16 | `time_rt_2h` | T5–T6 |
| 12 | u16 | `time_sth_2h` | T6–T3 |
| 14 | u16 | `time_ht_2h` | T3–T4 |
| 16 | u16 | `time_ot_2h` | above T4 |
| 18 | s8 × 6 | `temp_t1_c` … | the gauge's T1, T2, T5, T6, T3, T4 in that (ascending) order, °C, as configured in data flash *Advanced Charge Algorithm › Temperature Ranges*, so the app labels the buckets without hard-coding them. Data flash isn't readable once the gauge is sealed, so firmware sends compile-time constants that match the gauge configuration image |
| 24 | u16 | `cell_max_mv` | highest of Block 1 Cell 1–4 Max Voltage |
| 26 | u16 | `cell_min_mv` | lowest of Block 1 Cell 1–4 Min Voltage; 0x7FFF (gauge default) = never measured |
| 28 | u16 | `max_delta_cell_mv` | Block 1 Max Delta Cell Voltage (worst imbalance ever seen) |
| 30 | s16 | `max_charge_ma` | Block 1 Max Charge Current |
| 32 | s16 | `max_discharge_ma` | Block 1 Max Discharge Current, ≤ 0 |
| 34 | s8 | `max_temp_cell_c` | Block 1 Max Temp Cell, °C. −128 = never measured |
| 35 | s8 | `min_temp_cell_c` | Block 1 Min Temp Cell, °C. 127 = never measured |
| 36 | s8 | `max_temp_fet_c` | Block 1 Max Temp FET, °C |
| 37 | u8 | `shutdowns` | Block 2 No. of Shutdowns |
| 38 | u16 | `full_charges` | Block 5 No. Valid Charge Term (charge terminations, i.e. reached full) |
| 40 | u16 | `safety_events` | sum of the 12 safety event counters in Blocks 4–5 (COV, CUV, OCD1/2, OCC1/2, AOLD, ASCD, ASCC, OTC, OTD, OTF), saturating at 0xFFFF |
| 42 | u16 | `last_safety_cycle` | cycle count at the most recent of those events. 0xFFFF = none |
| 44 | u16 | `qmax_updates` | Block 5 No. of Qmax Updates (capacity re-learned) |
| 46 | u8 | `max_balance_time_2h` | highest of Block 2 CB Time Cell 1–4, 2 h units (saturates at 255 = 510 h) |
| 47 | u8 | `life_flags` | bit 0 `COLLECTING` (LF_EN); bits 1–7 reserved |

The per-event-type counters stay on the gauge; read them with BQStudio when a pack comes back with a non-zero `safety_events`.

## 5. Enums and bitfields

### 5.1 `charge_stage`
| Value | Name | Meaning |
|---|---|---|
| 0 | `IDLE` | no charger attached or charging finished and above the recharge point |
| 1 | `PRECHARGE` | a cell below ~3.0 V, C/10 |
| 2 | `NORMAL` | 0.5C constant current |
| 3 | `FAST` | 1C constant current (fast mode, 20–80 %) |
| 4 | `CONSTANT_VOLTAGE` | 16.8 V, current tapering |
| 5 | `HOLD` | at `max_soc_pct` (or full), charger holds the pack and feeds pass-through |
| 6 | `INHIBITED` | charger attached but charging stopped: see `limit_reason` |
| 7 | `FAULT` | gauge or charger fault, see Gauge Health |

### 5.2 `limit_reason`
| Value | Name |
|---|---|
| 0 | `NONE` |
| 1 | `SOURCE_TOO_SMALL` (input contract limits the rate) |
| 2 | `TOO_COLD` |
| 3 | `TOO_HOT` |
| 4 | `MAX_SOC_REACHED` |
| 5 | `SOLAR_LIMITED` (MPPT / VINDPM holding back) |
| 6 | `THERMAL_THROTTLE` (20 W mode) |
| 7 | `PACK_FAULT` |
| 8 | `INPUT_UNDERVOLTAGE` (weak source, VINDPM active) |
| 9 | `SENSORS_DEGRADED` (fewer than 3 board sensors working) |
| 10 | `CABLE_LIMITED` (no e-marked cable, 3 A cap) |

### 5.3 Status `flags` (u16)
| Bit | Name |
|---|---|
| 0 | `CHARGING` |
| 1 | `DISCHARGING` |
| 2 | `THROTTLE` — 20 W thermal throttle active |
| 3 | `SENSORS_DEGRADED` — fewer than 3 board sensors working |
| 4 | `FAST_ACTIVE` — currently charging at 1C |
| 5 | `TRIP_MODE` — trip mode armed |
| 6 | `FULL_ONCE_PENDING` — charge-to-100-once armed |
| 7 | `BALANCING` — gauge cell balancing active |
| 8 | `GAUGE_FAULT` |
| 9 | `PAIRING_WINDOW` — pairing accepted right now |
| 10 | `HARD_SHUTDOWN` — outputs off on over-temperature |
| 11 | `PASS_THROUGH` — one port sinking while the other sources |
| 12 | `SOLAR` — at least one port on a solar-like source |
| 13 | `LOW_SOC` — SOC ≤ 10 % |
| 14 | `OTA_PENDING` |
| 15 | reserved |

### 5.4 `power_state`
0 `S0_CHARGING`, 1 `S1_SOURCING`, 2 `S2_IDLE`, 3 `S3_RESET`, 4 `S4_PASS_THROUGH`, 5 `S5_SHIP` (never actually seen over BLE; reserved).

### 5.5 Port `state`
| Value | Name |
|---|---|
| 0 | `DETACHED` |
| 1 | `ATTACHED` — cable present, no contract yet |
| 2 | `SOURCING` |
| 3 | `SINKING` |
| 4 | `ATTACHED_NO_POWER` — attached but held off (e.g. loop detected, budget exhausted) |
| 5 | `FAULT` — OVP/OCP/TSD, see flags |

### 5.6 Port `flags` (u8)
| Bit | Name |
|---|---|
| 0 | `PD_CONTRACT` (else plain USB-C 5 V) |
| 1 | `EMARKED_5A` |
| 2 | `SOLAR_SOURCE` |
| 3 | `THROTTLED` — this port capped at 20 W |
| 4 | `PRIORITY` — set on USB1 |
| 5 | `LOOP_DETECTED` — cable between the pack's own ports |
| 6 | `SOURCE_ONLY` — dual-role disabled (pass-through partner) |
| 7 | `OVERCURRENT` |

### 5.7 Command `result`
0 `OK`, 1 `UNKNOWN_OPCODE`, 2 `BAD_ARG`, 3 `REFUSED_STATE` (e.g. ship mode with a cable attached), 4 `NOT_BONDED`, 5 `BUSY`.

### 5.8 `gauge_status` (u8)
bit 0 `FET_CHG_OFF`, bit 1 `FET_DSG_OFF`, bit 2 `OVERTEMP`, bit 3 `UNDERTEMP`, bit 4 `CELL_OV`, bit 5 `CELL_UV`, bit 6 `OVERCURRENT`, bit 7 `IMPEDANCE_TRACK_NOT_LEARNED`.

## 6. Pairing and security

- LE Secure Connections, Just Works in v1 (no display on the pack). An optional printed 6-digit passkey can be enabled by firmware build flag later; the app already handles the iOS passkey prompt either way.
- **Pairing window:** firmware accepts a pairing request only (a) while it has no bonds at all, (b) for 2 min after a USB cable is plugged into either port (the TPS25751 attach interrupt opens it), or (c) for 2 min after `OPEN_PAIRING` from a bonded phone. Outside the window a pairing request is rejected with "Pairing Not Supported"; bonded phones reconnect normally. `flags.PAIRING_WINDOW` tells the app when a new phone can be added.
- Up to 4 bonds. `CLEAR_BONDS` from the app, or without the app: plug and unplug a cable 5 times within 15 s.
- Writes to Settings and Command require an encrypted link with a bond; reads and notifications don't.
- Firmware updates go through TI's OAD service after `ENTER_OTA`; that service has its own UUIDs and is documented by TI, not here. Signing, rollback and fail-safe rules are in §8.

## 7. Connection behaviour the app relies on

- Connection parameters: firmware requests 50–100 ms interval, latency 4, timeout 4 s while connected; the app doesn't care if iOS picks something else.
- Firmware drops a connection that stays idle (no subscriptions) for 60 s to save power; the app subscribes to Status, Ports and Temperatures right after reading Protocol Version.
- One connection at a time. A second phone sees the pack as not connectable until the first disconnects.
- After `ENTER_OTA`, `RESET_MCU` or `CLEAR_BONDS` the link drops; the app must expect it and not show an error.

## 8. Firmware update (OTA) security

The pack is potted; a bad or hostile update is the one fault that can't be fixed with a screwdriver. The CC2340's OAD uses **MCUboot** as the bootloader (TI LPF3 SDK), which gives most of this for free; the rest is our policy.

**Image authenticity — mandatory.**
- Every application image is **signed with ECDSA P-256** (MCUboot `imgtool`) by a private key that lives only on Logan's MacBook (and an offline backup). The matching public key is compiled into MCUboot and flashed once over SWD before potting. After potting it cannot be changed, so losing the private key means no more updates for that pack: back it up.
- MCUboot verifies the signature (and SHA-256) of an image **before swapping to it, and again on every boot**. An unsigned or tampered image is never run. The app cannot bypass this; it only transfers bytes.
- Image header carries a **version** (semver + build) and a **hardware ID** (dev board = 1, production = 2, matching `hw_rev` in §4.1). MCUboot's anti-rollback (`MCUBOOT_HW_ROLLBACK_PROT` / security counter) is enabled on production so a known-bad older image can't be reinstalled; dev boards leave it off so bisecting is possible.

**Image confidentiality — optional, decide at firmware time.**
- MCUboot can also **encrypt** images (AES-128-CTR, key wrapped with ECIES-P256). It stops someone reading the firmware out of a BLE capture or a distributed `.bin`. For a hobby pack that's mostly about not leaking the gauge golden image and the PD config; enable it if the update files will ever be posted publicly, otherwise skip it (it costs flash and boot time).

**Who may start an update — our policy, in the GATT.**
- `ENTER_OTA` (§4.6) is accepted only from a **bonded, encrypted** link, only when SOC ≥ 20 %, and never while the pack is sourcing more than 20 W (so the reboot can't drop a laptop at full load). The command result reports which check failed.
- The TI OAD service is **not advertised and not present** in the normal application; it only exists in OAD mode after `ENTER_OTA`. An attacker can't even see the update service without a bond.
- OAD mode times out: if no transfer starts within 2 min, or stalls for 30 s, the pack reboots into the existing application. The old image stays valid until the new one is verified (MCUboot swap or overwrite-after-verify), so a dropped connection mid-update can't brick it.
- The app shows the image version, hardware ID and signature status (from the file's MCUboot header/TLV) **before** it offers to send, and refuses a file whose hardware ID doesn't match `hw_rev`.

**Fail-safe boot — the potted-pack rule.**
- Firmware feeds the WDT from the supervision loop; a new image that hangs is reset by the WDT. MCUboot is configured in **swap-with-revert** mode: a new image boots as "test" and must mark itself **confirmed** after passing self-checks (gauge responds, both PD controllers respond, settings CRC OK, one successful BLE connection). If it doesn't confirm before the next reset, MCUboot **reverts to the previous image** automatically.
- The app's update flow is therefore: send → pack reboots → app reconnects → app reads Protocol Version and sees the new `fw_*` → firmware confirms itself. If the app sees the *old* version after the reboot, the update was reverted and the app says so.

**Rejected alternatives.**
- Plain CRC-only OAD (TI's default example): anyone within radio range could, after pairing in the window, load arbitrary code into a 82 Wh lithium pack. Not acceptable for a potted product even as a hobby.
- Password or token in the app instead of signing: the token leaks the moment the app binary is shared; signing keeps the secret off the phone entirely.
- TI's "secure OAD" naming on older CC13xx/CC26xx parts doesn't apply here; on the CC2340 it is MCUboot's own signing. Confirm the exact MCUboot options the LPF3 SDK exposes (signature type, encryption, swap mode, rollback counter) when firmware starts; this section is the requirement, the SDK release decides the mechanism.

## 9. Change log

- 1.0 (2026-10-16): first draft; §8 OTA security added the same day.
- 1.1 (2026-10-16): Pack Life characteristic `DDE7010A` (§4.9) from the gauge's Lifetime Data. §1 MTU rule corrected (notifications carry MTU − 3 bytes). Firmware-side notes in `firmware-interface.md`.
