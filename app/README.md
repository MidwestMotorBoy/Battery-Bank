# Monolith app workspace

| Folder | What |
|---|---|
| `MonolithKit/` | Swift package: the BLE protocol (`docs/app/ble-gatt-spec.md`) as code. `swift test` runs its unit tests |
| `FakePack/` | macOS app: advertises the Monolith GATT from the Mac's radio with sliders for every value, so the iPhone app can be built with no hardware |
| `Monolith/` | (next) the iOS app |
| `project.yml` | XcodeGen spec that builds all of the above into one `Monolith.xcodeproj` (not committed) |

## First time on the Mac
```sh
brew install xcodegen
cd app/MonolithKit && swift test        # protocol round-trip tests
cd .. && xcodegen generate && open Monolith.xcodeproj
```
In Xcode pick your team under Signing (free Apple ID is fine), select the **FakePack** scheme, run. macOS asks for Bluetooth permission once. The window shows "Bluetooth on" and starts advertising as `Monolith`.

## Checking FakePack before the iOS app exists
Use a generic BLE scanner on the iPhone (e.g. nRF Connect or LightBlue):
1. Scan: `Monolith` should appear with the Battery Service in the advertisement.
2. Connect, open the Monolith service (`DDE70001-…`), read Protocol Version (`DDE70101`): expect `01 00 00 01 00 01 01 00`.
3. Subscribe to Status (`DDE70102`): a 36-byte value arrives once a second while SOC moves (drag the slider).
4. Write Settings (`DDE70105`) with `5F 00 14 01 1E 00 00 00` (max SOC 95, fast off): iOS prompts to pair because the characteristic needs encryption; the FakePack log shows the write. Write `3B …` (59 %) and the write is rejected.
5. Write Command (`DDE70106`) `06` (identify): a Command Result notification `06 00 00 00` follows, and the log shows "LED blink".

## Notes
- Settings and Command require an encrypted link; macOS handles the pairing prompt on its side. Forget the pairing in System Settings > Bluetooth when testing the pairing flow again.
- The simulated pack moves SOC by the net power you set on the ports (positive = out of the pack), picks the charge stage from the inputs, and respects the written max SOC / fast-charge settings, so most app states can be reproduced from the sliders alone.
- `.xcodeproj`, `Info.plist` and entitlements are generated; edit `project.yml` instead.
