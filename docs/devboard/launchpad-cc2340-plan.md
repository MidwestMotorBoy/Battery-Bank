# LP-EM-CC2340R53 LaunchPad plan (2026-10-15)

What we do with TI's LP-EM-CC2340R53 before the dev board exists: prove the toolchain and probe, then test every CC2340 risk in `bringup-config-checklist.md` §1 and §4 on a known-good board. When the dev board arrives, the firmware should only need its pin map changed.

Firmware lives in [`../../firmware/`](../../firmware/README.md). Claude writes the code and the step-by-step instructions; Logan plugs things in, flashes, and reports numbers, scope shots and logs.

## Facts that shape the plan

- **The LaunchPad has no onboard debugger.** It takes an external probe on its 20-pin LP-EM edge connector or its 10-pin header P4 (SWRU637). We use the **LP-MSPM0G3519's XDS110**: J102 (XDS110 side) → the kit's 10-pin cable → P4, and the kit's 2-wire cable for 3V3/GND. This is the same J102 → cable → target hookup as J301 on the dev board, so day 1 rehearses it.
- **Same memory as the module.** The CC2340R53 on the LaunchPad and the CC2340R5MODA both have 512 KB flash / 64 KB RAM (SDK linker `cc23x0r53.cmd`, TI product page). The plain CC2340R5 is the 36 KB part. No RAM cap is needed.
- **The LaunchPad pins differ from ours.** Its LEDs, buttons and back-channel UART come from TI's board file. Dev-board signals are tested on spare LaunchPad DIOs; the real map (DIO6 SCL, DIO8 SDA, ...) goes in the dev-board SysConfig file later.
- **The LaunchPad has a 32 kHz crystal; the dev board doesn't.** The firmware selects LF RCOSC anyway, so the LaunchPad runs the way the dev board will.
- **NoRTOS first, FreeRTOS for BLE.** The bring-up tests (CCFG, WDT, GPIO timing, Standby, I2C) build on NoRTOS with TI drivers. The BLE5 stack on CC23xx runs on FreeRTOS, so the BLE step moves the app to FreeRTOS; the drivers and logic carry over.

## 0. Before it arrives

- [ ] **Order the LP-MSPM0G3519** if it isn't ordered yet: without it the LaunchPad can't be flashed.
- [x] (2026-10-15: CCS 21.0.1, SDK 9.23.00.27, UniFlash 9.7.0) Install the tools (`firmware/README.md`, "Install"): Code Composer Studio (brings TI Arm Clang, SysConfig, gmake and the XDS110 drivers), the LPF3 SDK, UniFlash.
- [x] `gmake` in `firmware/` builds `batterybank_launchpad.out` (2026-10-15: first try, no warnings, about 10 KB flash).
- [ ] Optional: a TMP1075 breakout (or any 3.3 V I2C sensor) so the I2C code runs against real hardware before the dev board.

## 1. Day 1: probe and toolchain

1. [ ] On the LP-MSPM0G3519, pull the NRST, SWDIO, SWCLK, TXD and RXD jumpers on J101 so its own MSPM0 is off the probe lines.
2. [ ] **Before plugging in, measure J102 pin 1 against GND** with the LP-MSPM0G3519 on USB. Write down the voltage. This answers the open J301 question: does the probe drive 3.3 V onto the target?
3. [ ] Connect J102 → 10-pin cable → LaunchPad P4, plus the 2-wire power cable, polarity checked.
4. [ ] UniFlash: new configuration, CC2340R53, Texas Instruments XDS110 USB Debug Probe. "Verify" (connect) must read the device. Save the `.ccxml`; `make flash` will use it.
5. [ ] Flash `firmware/build/launchpad/batterybank_launchpad.out`. Expected: red LED blinks at 1 Hz; the XDS110 UART COM port at 115200 8N1 shows the banner and the reset reason; BTN-1 prints a line.
6. [ ] Reset with the LaunchPad reset button, then power-cycle: the banner shows `PIN` and then `POR`.

## 2. Days 2–4: dev-board risks on the LaunchPad

| # | Test | Pass condition | Source |
|---|---|---|---|
| T1 | **CCFG bootloader trigger off.** Build has "Default FCFG bootloader, with CCFG settings", pin trigger disabled. Hold DIO21 low (jumper to GND) and reset | App starts (banner prints). Repeat with the SDK default CCFG to see the bootloader take over, then recover by flashing over SWD | Review 4 A-1, checklist §1.4 |
| T2 | **Mass-erase recovery.** With a CCFG that blocks the app, UniFlash chip erase over SWD | Device is erased and reflashes | Recovery path for the dev board |
| T3 | **WDT with the debugger halted.** Enable the WDT, halt at a breakpoint for longer than the period | Record whether the target resets. Decides how we debug with the WDT on | Checklist §1.5 |
| T4 | **Reset to first GPIO write.** First line of `main` restores two outputs from retained RAM; scope RESET and the pin | Time from reset release to pin valid, well under 16 ms, with the BLE stack not yet started | Review 4 C-6 / A-8 |
| T5 | **Standby keeps GPIO states**, wake on a falling edge with the internal pull off | Output stays driven through Standby; a button edge wakes it; no wake while the line is low | Checklist §4 IRQ_N, CHG_INH |
| T6 | **LF RCOSC only** (crystal unused) with BLE advertising | Phone sees stable advertising over an hour; connection holds | Review 4 A-8 |
| T7 | **I2C0 at 100 kHz**: 9-pulse bus clear, clock stretching tolerated, TMP1075 one-shot and shutdown (if the breakout is bought) | Clean scope trace; reads match a thermometer within ±1 °C | Checklist §4 boot order |
| T8 | **Standby current**, meter in the 3V3 path (jumpers on the LaunchPad) | Record µA with and without BLE advertising; compare with `power-budget.md` | Power budget |
| T9 | **BLE OTA (on-chip)** with a full-size image from a phone (TI SimpleLink Connect) | Image updates and boots; a failed transfer leaves the old image running | Reason we chose this part |

Results go in a new section at the end of this file, with dates.

## 3. After that: firmware before the dev board

- [ ] Drivers: BQ40Z50 (SMBus, MAC commands), TPS25751 (INT_EVENT1 read/clear, source PDO changes), TMP1075 (modes per state).
- [ ] IRQ_N dispatcher that reads and clears all seven sources and loops until the line is high.
- [ ] Supervision state machine: CHG_INH rules, charge and source sharing, ship mode, WDT servicing only from the supervision loop. Runs on the LaunchPad against fake devices.
- [ ] BLE GATT service: status (cells, SOC, ports, temperatures) and the ship-mode command.
- [ ] Dev-board SysConfig (`firmware/boards/devboard.syscfg`) with the pin map from `cc2340-pin-budget.md`.

Sources: [SWRU637 LP-EM-CC2340R5x user guide](https://www.ti.com/document-viewer/lit/html/SWRU637/GUID-18285EA1-79FC-463F-9DEE-3CC9A858A0CB), [TI CC2340R5MODA product page](https://www.ti.com/product/CC2340R5MODA), [LPF3 SDK on GitHub](https://github.com/TexasInstruments/simplelink-lowpower-f3-sdk).
