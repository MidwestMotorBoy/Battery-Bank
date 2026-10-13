# TPS25751 EEPROM programming — firmware reference
_From TI app notes SLVAFL1 (EEPROM Update Over I2C, Oct 2024) and SLVAFV8A (EC loads a patch bundle, Jul 2025). Written 2026-10-11._

## Hardware this assumes (Monolith)
- Two TPS25751s on the STM32WB's single I2C bus (I2Ct): USB1 at 0x20, USB2 at 0x21 (ADCIN straps, SafeMode). Gauge BQ40Z50-R2 at 0x0B on the same bus.
- Each TPS25751 has its own EEPROM (ST M24512-DFMC6TG) at 0x50 on its own controller bus (I2Cc), shared with its BQ25756.
- Each TPS25751's I2Ct_IRQ goes to its own STM32WB GPIO (needed for Ready-for-Patch and CMD1-complete interrupts).
- STM32WB is flashed over SWD pogo pads before potting.

## Two image files from TI's USBCPD Application Customization Tool (web GUI)
- **Full Flash binary**: the complete EEPROM image, region pointers and both regions. Must be written the very first time so the region headers are correct. Up to 32 KB.
- **Low Region binary**: just the patch bundle (config + FW patch). Used for loading over I2Ct (PBM) and for later EEPROM updates. TI's example is 0x2C80 = 11,392 bytes. Export as a C array and compile it into the STM32WB firmware.

## EEPROM memory map (fixed by TI)
| Address | Contents |
|---|---|
| 0x0000 | LowRegionStart pointer (0x0000_0800 when valid, 0 when erased) |
| 0x03FC | LowAppConfigOffset |
| 0x0400 | HighRegionStart pointer (0x0000_4400 when valid, 0 when erased) |
| 0x07FC | HighAppConfigOffset |
| 0x0800 | Low region patch bundle (Header_ID 0xACE0_0001) |
| 0x4400 | High region patch bundle (Header_ID 0xACE0_0001) |

Each region holds up to 0x3C00 = 15 KB. The layout uses exactly 32 KB (256 Kbit); the 512 Kbit part just has an unused upper half.

## Boot behavior
- The controller reads the Low region header first, then the High region; at most two attempts, then it aborts.
- On abort (or no/blank EEPROM): BOOT_STATUS (0x2D) is updated, INT_EVENT.ReadyForPatch asserts, MODE (0x03) reads "PTCH", and it waits forever for the host to load a patch (PBM) or send GAID.
- SafeMode: the sink path stays off until a configuration is running.

## Running a 4CC command (all FLxx, PBMx, GAID)
1. If it takes input, write the input to DATA1 (register 0x09).
2. Write the 4 ASCII characters to CMD1 (register 0x08).
3. Wait for CMD1 to read 0x00000000 (success) or "!CMD" (0x21 0x43 0x4D 0x44, failure). Poll every ~10 ms or use the CMD1-complete interrupt.
4. On success, read the output from DATA1.
- Register writes use SMBus block format: [addr][reg][byte count][data…]. Reads: [addr][reg] restart [addr+R] → byte count, data.

## Loading a patch over I2Ct (PTCH → APP), SLVAFV8A
1. Wait for I2Ct_IRQ low (Ready for Patch), confirm MODE = "PTCH".
2. Set the interrupt mask (0x16) to enable CMD1 Complete; clear interrupts (0x18, write 11 × 0xFF).
3. DATA1 = bundle size (4 bytes, little-endian), burst target address (0x30), timeout (e.g. 0x32 = 3.2 s). Read DATA1 back to confirm (500 µs between write and read).
4. CMD1 = "PBMs". Wait for IRQ; CMD1 must clear and DATA1 byte 0 (PatchStartStatus) must be 0 (4/5/6 = bad size/address/timeout).
5. Plain I2C writes of the Low Region binary to address 0x30, in bursts up to 4095 bytes, 500 µs between bursts (the pointer auto-increments across bursts).
6. Clear interrupts, CMD1 = "PBMc", wait for IRQ, CMD1 clear.
7. Wait 20 ms, read DATA1, then MODE must read "APP ".
- Load the two controllers one at a time (both use burst address 0x30).

## EEPROM commands (TPS25751 must be in APP mode), SLVAFL1
| 4CC | Input | Output | Purpose |
|---|---|---|---|
| FLrd | 4 B address | 16 B | Read EEPROM at address |
| FLad | 4 B address | 1 B status | Set write start address |
| FLwd | up to 64 B (TI writes 32-byte pages) | 1 B status | Write at current address, auto-increments |
| FLvy | 4 B region start address | 1 B status | Verify the patch bundle at that address |
| GAID | none | none | Cold reset; reboot from EEPROM |
- Status byte = output byte [1] in TI's example; 0 means OK.
- TI's example waits ~75 µs between FLwd writes.

## Safe update of one region: UpdateRegionOfEeprom(target)
Update the region the controller did NOT boot from (read BOOT_STATUS 0x2D: if region0 error/invalid, update Low; otherwise update High).
1. WriteRegionPointer(target, 0): erase the target's pointer so a half-written region is never booted.
2. FLad(target bundle address: 0x0800 low / 0x4400 high), then FLwd the Low Region binary in 32-byte chunks.
3. FLvy(target bundle address). If it passes, WriteRegionPointer(target, bundle address).
4. WriteRegionPointer(old region, 0) so the next boot uses the new region.
5. GAID to reboot onto the new bundle. Optionally repeat into the other region so both match.
- WriteRegionPointer(p, v): FLad(pointer address 0x0000 or 0x0400) → FLwd(4-byte v) → FLrd(pointer address) and confirm it reads v.
- A power cut at any step leaves at least one valid region.

## Monolith boot flow (STM32WB firmware)
For each TPS25751 at every STM32WB boot:
1. Read MODE (0x03). "APP " → read its patch version; if the firmware carries a newer bundle, run UpdateRegionOfEeprom, then GAID.
2. "PTCH" with ReadyForPatch → read BOOT_STATUS (0x2D) for the reason, load the Low Region binary by PBM (→ APP), then repair the EEPROM:
   - Blank EEPROM (first power-up): write the Full Flash image from 0x0000 with FLad/FLwd (or write both regions plus both pointers from the Low Region binary), verify with FLvy, then GAID.
   - Corrupt region: UpdateRegionOfEeprom on the bad region.
3. Dead-battery start (VBUS came up before 3V3): the TPS25751 keeps its VIN_3V3 switch open and runs LDO_3V3 (EEPROM, I2Cc pull-ups) from VBUS until the host clears the dead-battery flag (tps25751 §8.3.2; TRM 4CC "DBfg"). Once 3V3 is up, check the flag and send DBfg, or the controller resets when the cable is pulled.
4. Log the result over Bluetooth.
- First-time programming time estimate: ~32 KB in 32-byte FLwd commands ≈ 1,000 commands; at ~10 ms per command handshake that's ~10–15 s per port.

## Known limits
- SafeMode can't charge from USB until a configuration runs. On a fresh board, power the first boot from a bench supply on the pack pads.
- Double fault: pack fully dead AND an EEPROM corrupt means no USB recovery, since the STM32WB can't run to repair it. Very unlikely given the two-region scheme; accepted.
- Bluetooth firmware updates can carry a new Low Region binary, so PD configuration can change after potting.
