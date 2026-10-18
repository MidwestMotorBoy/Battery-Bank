# Production P0: bring-up and gauge training

_Started 2026-10-18. The dev board is skipped: P0 of the production board is the first board built. It is used to train the BQ40Z50-R2 and to run the checks that were planned for the dev board. A second spin happens only if these checks call for one._

## Equipment

- **SWD:** XDS110 (LP-MSPM0G3519 LaunchPad) on J301.
- **Gauge:** EV2400 (clone) with TI BQStudio on J302.
- **Cable:** one Tag-Connect TC2030-IDC-NL serves both J301 and J302; its 2×3 0.1″ end takes the jumper wires. Add a TC2030-CLIP to hold it hands-free during long runs.
- **Power:**
    - USB-C PD charger with 20 V;
    - DC electronic load (constant current) on 20 AWG leads;
    - USB-C PD trigger or USB-C electronic load for port tests.
- **Measurement:**
    - DMM;
    - scope with a ground spring;
    - thermocouple or IR camera.

## Pads on P0

| Pads | Use |
|---|---|
| J301 (TC2030-NL, "SWD") | CC2340 flash and debug: VCC, SWDIO, NRST, SWCLK, GND |
| J302 (TC2030-NL, "GAUGE") | 1 SDA, 2 CHG_INH, 3 NRST, 4 nc, 5 GND, 6 SCL |
| J108 / J112 | Pack − / + (16 AWG) |
| J109–J111 | Cell taps CELL1–CELL3 |
| J102, J105–J107 | Cell NTCs |
| J113 / J114 | PACK_P / GND, 20 AWG load wires for the learning-cycle discharge |
| TP113 (WAKE) + TP106 (PACK_P) | Gauge wake: bridge the two pads with tweezers. TP113 is CELL_P through R118 4.7 kΩ. |
| TP109, TP301 | GND, 3V3 |
| Per port: TP401–TP406, TP412 (5xx on port 2) | VBUS, PPHV, PP5V, REGN, SW1, SW2, GND (1.0 mm pads) |

A wrong plug is harmless: if the SWD cable goes onto J302, the probe drives only CHG_INH and NRST, and its other pins are inputs. **Never put a probe on TP113**: it sits behind 4.7 kΩ to the 16.8 V cell stack.

## 1. Assembly

1. **Pack:** with USB unplugged, solder PACK− (J108), then CELL1–CELL3 (J109–J111) bottom-up, then PACK+ (J112). A floating tap can trip U102, which blows F102 (gauge sheet note 15).
2. **NTCs:** fit the four cell NTCs (insulated, taped at cell mid-height).
3. **Cell check:** measure each cell at the tap pads before going further.

## 2. First power

1. **Wake the gauge** by plugging in a USB charger. Wake-on-USB is unproven. If the gauge doesn't wake, bridge TP113 to TP106 for a moment.
2. **Check the rails:** 3V3 at TP301, then PACK_P at TP106.
3. **Flash the CC2340** through J301. The TPS25751 EEPROM configuration must be loaded before PD sourcing works.

## 3. Gauge training (BQStudio on J302)

To keep the MCU off the SMBus while BQStudio is connected:
- **Hold the MCU in reset:** J302 pin 3 (NRST) to GND.
- **Keep charging enabled:** J302 pin 2 (CHG_INH) to GND. In reset, the chargers are disabled unless CHG_INH is held low.
- **Never connect the EV2400 with 3V3 down.** An unpowered CC2340 can't take bus voltage.

Steps:

1. **Basic data flash:**
    - 4 cells, design capacity 5,800 mAh;
    - TS1–TS4 enabled;
    - FET temperature sensor configured;
    - protection thresholds per the design notes;
    - COV delay 1 s and Min Blow Fuse Voltage 10,500 mV (second-level protection).
2. **Chemistry:** select the EVE INR21700-58E chemistry ID if it's in TI's database. Otherwise run TI's GPCCHEM flow first.
3. **Calibration:**
    - voltage (DMM at the taps);
    - current (known DC load on J113/J114 through RS101);
    - temperature (TS1–TS4);
    - CC offset with no load.
4. **Learning cycle** (TI's procedure for the BQ40Z50):
    1. Charge to full from the USB charger.
    2. Rest ≥ 2 h.
    3. Discharge at ~C/5 (≈ 1.2 A) on J113/J114 to the termination voltage.
    4. Rest ≥ 5 h.
    5. Charge to full again.
    6. Confirm the update status shows a completed learning cycle.
5. **Export** the data flash as the golden image and commit it to the repo.

## 4. Checks that the dev board would have done

| Check | How | Decision it feeds |
|---|---|---|
| Switch-node ringing, both legs, both directions | Scope on TP405/TP406 with the ground spring on TP412, gate links at 0 Ω | Keep 0 Ω, fit 2.2–10 Ω, or fit the DNP snubbers |
| SiZ240DT and APS0730 temperatures at the worst case | Reverse 20 V / 5 A from a ~10 V pack, then forward 20 V / 3 A | Thermal throttle limits; XAL7070 fallback for the inductor |
| PP5V load step 0.5 → 3 A | Scope on TP403 | C443 size (P3: estimated ~190 mV) |
| PD voltage transitions 5 → 20 V with several chargers | Watch VBUS and source resets, with and without firmware SRYR/SRDY sequencing | Firmware sequence required or not |
| Gauge wakes on USB plug-in | Gauge in SHUTDOWN, plug in a charger | Whether the WAKE pad can go in the next spin |
| Sleep current | DMM in series with one pack lead | Firmware power states (target ~150 µA) |
| USB-side bank stress | CA55 C421/C456 temperature at reverse 20 V 5 A from a low pack (model: worst part 43 % of rating, an MLCC) | Bank OK, or add a fifth 22u 1210 |

## 5. Production boards

Each board gets the golden image and its own calibration through J302, using the same cable and the same NRST/CHG_INH holds. The J113/J114 load pads and the WAKE pad can stay as they are, or be dropped in a later spin once the checks above pass.
