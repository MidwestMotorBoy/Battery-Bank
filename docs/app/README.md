# Monolith iPhone app — plan and status

_Started 2026-10-16. No pack and no CC2340 dev board exist yet; the app is developed against a simulated pack running on the MacBook._

## What it is
A SwiftUI + CoreBluetooth iOS app that reads the pack's state and changes its stored settings over Bluetooth LE. The pack works fully without the app; the app never owns a safety limit. Everything it reads and writes is defined in [`ble-gatt-spec.md`](ble-gatt-spec.md), and `app/MonolithKit` is that spec as Swift.

## Machines
| Machine | Role |
|---|---|
| MacBook | All app work: Xcode, the iOS app, and **FakePack**, a small macOS app that advertises the Monolith GATT over the Mac's own Bluetooth radio (`CBPeripheralManager`) with sliders for SOC, temperatures, port states, faults, throttle. The iPhone app connects to it exactly as it will to the real pack |
| iPhone | Required from day one: Bluetooth does not work in the iOS Simulator. A free Apple ID installs the app from Xcode for 7 days at a time; the $99/yr Developer Program removes that limit and adds TestFlight (decide later) |
| Windows PC | Nothing for the app. Stays the BQStudio / TI tools machine |

## Repo layout
```
docs/app/ble-gatt-spec.md      the contract (firmware and app both build from it)
docs/app/firmware-interface.md brief for the firmware author: field sources, app behaviour, pitfalls, checklist
docs/app/README.md             this file
app/MonolithKit/               Swift package: UUIDs, enums, byte-exact record encode/decode, unit tests
app/Monolith/                  the iOS app (SwiftUI + CoreBluetooth); built-in demo pack for the iOS Simulator
app/FakePack/                  macOS simulator app
```
`MonolithKit` is a plain Swift package so both apps depend on it and a layout change has to be made in one place.

## Order of work
1. **GATT spec** — drafted, see the spec. Review it, then it's frozen as 1.0 except for appended fields.
2. **MonolithKit** — written; `swift test` on the Mac should pass (not yet run anywhere).
3. **FakePack (macOS)** — `CBPeripheralManager`, one window: SOC slider, charge stage picker, per-port state/contract/power, ten temperature sliders with "broken"/"not fitted" toggles, throttle and pairing-window toggles, a log of settings writes and commands received. Publishes the same Status/Ports/Temperatures notifications at the same rates as the spec.
4. **iOS app** — scan → connect → read Protocol Version → subscribe. Screens (tabs): Pack (SOC, time to full/empty, power flow with each port's voltage, current and power, battery V/A), Charging (stage, limit reason, cells), Temps (ten readings drawn on a placeholder pack model, faults, throttle points), Health (SOH, cycles, Pack Life from the gauge's Lifetime Data incl. time at temperature, spec §4.9), Settings (max SOC picker 60/70/80/90/95/100, fast charge, USB2 minimum, charge-to-100-once, trip mode; Developer inside: raw bytes, debug log, identify, reset, clear bonds, enter OTA).
5. **Bring-up on the CC2340 dev board** — port FakePack's GATT table to TI's BLE5-Stack (SysConfig), then the app connects to real hardware with no app changes.

## Design rules for the app
- Reconnect automatically to the bonded pack; when it's out of range, keep showing the last values with their timestamp, greyed.
- Writes are read-modify-write of the whole Settings record; never write a record the app couldn't parse.
- Treat a missing Command Result as a failure and say so.
- Show a banner for `THROTTLE`, `SENSORS_DEGRADED`, `GAUGE_FAULT`, `HARD_SHUTDOWN` and any sensor marked broken; these are the things a dead sensor in a potted pack would otherwise hide.
- Unknown enum values display as "Unknown (n)". Never crash on a short or long payload.
- Keep the radio quiet: subscribe only to what the visible screen needs; the pack's idle budget depends on it.

## Open questions
- Just Works pairing vs a printed passkey: v1 is Just Works; the pairing window (cable plugged in within the last 2 min) is what stops a stranger pairing.
- OTA: TI OAD on the CC2340 with MCUboot; images are ECDSA-signed, verified on every boot, with swap-and-revert fail-safe (spec §8). The app side (OAD profile UUIDs, sending an MCUboot image, showing version/hardware ID before sending) comes once firmware exists; v1 of the app stops at the `ENTER_OTA` command.
- Whether production keeps the LED (`led_mode` setting is reserved otherwise).
