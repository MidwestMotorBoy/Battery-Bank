# MonolithDev MCU firmware

Firmware for U301 on the dev board, a TI CC2340R5MODA (BLE, 512 KB flash / 64 KB RAM). Until the dev board exists it runs on the **LP-EM-CC2340R53 LaunchPad**, which has the same memory. The plan for that phase is [`../docs/devboard/launchpad-cc2340-plan.md`](../docs/devboard/launchpad-cc2340-plan.md).

**Status (2026-10-15):** skeleton only. It was written before any TI tools were installed on this machine, so the first build will probably need fixes. Paste the full error output into the chat.

## Install (once)

Install everything under `C:\ti` (the default). Paths with spaces break TI's build tools.

1. **Code Composer Studio** 20.4 or newer: <https://www.ti.com/tool/CCSTUDIO>. In the installer's device list, tick the **SimpleLink CC23xx** family (low-power wireless). It brings:
   - the TI Arm Clang compiler (`ccs/tools/compiler/ti-cgt-armllvm_*`);
   - SysConfig (`ccs/utils/sysconfig_*`);
   - `gmake` (`ccs/utils/bin/gmake.exe`);
   - the XDS110 USB drivers and DSLite, the command-line flasher.
   
   We don't use the CCS IDE to build. It's installed for these tools, and it's handy for single-stepping later.
2. **SimpleLink Low Power F3 SDK**, the latest version: <https://www.ti.com/tool/download/SIMPLELINK-LOWPOWER-F3-SDK>. It installs as `C:\ti\simplelink_lowpower_f3_sdk_<version>`.
3. **UniFlash**, latest: <https://www.ti.com/tool/UNIFLASH>. Day 1 uses it to check the probe connection and to save the target configuration (`.ccxml`).
4. **Point the build at the tools.** In `firmware/`, copy `tools.mak.example` to `tools.mak`. Then make the three version numbers in it match the folder names that actually exist under `C:\ti`: the SDK, `sysconfig_*` and `ti-cgt-armllvm_*`.
5. **Put gmake on the Git Bash path.** Add this line to `~/.bashrc`, with the version folder fixed to match yours, then open a new Git Bash:
   ```bash
   export PATH="$PATH:/c/ti/ccs2040/ccs/utils/bin"
   ```

Then check the installs. All three commands should print a version:

```bash
gmake --version
```
```bash
/c/ti/ccs2040/ccs/tools/compiler/ti-cgt-armllvm_4.0.4.LTS/bin/tiarmclang --version
```
```bash
ls /c/ti/ | grep simplelink_lowpower_f3_sdk
```

## Build

From Git Bash in `firmware/`:

```bash
gmake
```

The output goes to `build/launchpad/batterybank_launchpad.out`, with a `.hex` and a `.map` next to it. `gmake clean` removes `build/`.

## Flash

**First time (day 1):** follow the plan's section 1 for the probe wiring, then:

1. Open UniFlash, choose device **CC2340R53**, connection **Texas Instruments XDS110 USB Debug Probe**, then click **Start**.
2. Click **Verify** under Settings & Utilities, or just connect. It must read the device.
3. Save the target configuration as `firmware/targets/lp_em_cc2340r53_xds110.ccxml`.
4. Load `build/launchpad/batterybank_launchpad.out` and click **Load Image**.

**After that:**

```bash
gmake flash
```

## What the skeleton does

- It prints a banner and the reset reason on the XDS110 UART: 115200 8N1, on the COM port called "XDS110 Class Application/User UART".
- The red LED blinks at 1 Hz.
- BTN-1 stands in for IRQ_N. Each press logs a falling edge.
- **CCFG:** LF clock from LF RCOSC, and the bootloader's pin trigger is off. Both choices are explained in `boards/launchpad.syscfg`.

## Layout

| Path | What |
|---|---|
| `Makefile` | Command-line build in the style of TI's SDK example makefiles. SysConfig generates into `build/<board>/syscfg` |
| `tools.mak.example` | Tool paths. Copy it to `tools.mak`, which git ignores |
| `boards/launchpad.syscfg` | LaunchPad pins (from TI's board file) and CCFG |
| `boards/devboard.syscfg` | To do: dev-board pin map from `docs/devboard/cc2340-pin-budget.md` |
| `app/` | Application sources |
| `targets/` | `.ccxml` target configurations saved from UniFlash |

**NoRTOS for now.** The bring-up tests don't need an RTOS. TI's BLE stack for the CC23xx runs on FreeRTOS, so the app moves to FreeRTOS at the BLE step (plan test T6).
