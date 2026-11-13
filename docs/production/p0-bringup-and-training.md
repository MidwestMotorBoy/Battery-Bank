# Production P0: bring-up and gauge training

_Started 2026-10-18. The dev board is skipped: P0 of the production board is the first board built. It is used to train the BQ40Z50-R2 and to run the checks that were planned for the dev board. A second spin happens only if these checks call for one._

## Equipment

- **SWD:** XDS110 (LP-MSPM0G3519 LaunchPad) on J301. **Use a `.ccxml` with Power Selection = "Target supplied power"**, not the LaunchPad's `lp_em_cc2340r53_xds110.ccxml`. That one is set to "Probe supplied power", and the probe then drives 3.3 V on pin 1 (measured 2026-10-20), which is J301 VCC, the board's 3V3 rail. Power the board from its own pack.
- **Gauge:** EV2400 (clone) with TI BQStudio on J302.
- **Cable:** one Tag-Connect TC2030-IDC-NL serves both J301 and J302; its 2×3 0.1″ end takes the jumper wires. A TC2030-CLIP only works on the bare board: once the board is on the carrier, the cells are behind it, and two of J302's guide holes sit over the bottom block of the right-hand rail (check the plug seats; for long training runs tack wires to J302 pads 1 / 5 / 6 instead).
- **TPS25751 loader:** a 3.3 V USB-I2C adapter (FT232H, MCP2221A or similar) on J302 pins 1 SDA / 6 SCL / 5 GND, with pin 3 NRST held low so the MCU stays off the bus, plus a host script that loads each controller's bundle (PBMs / PBMc, then FLad / FLwd / FLvy, `docs/firmware/tps25751-eeprom-programming.md`). BQStudio has no TPS25751 patch flow. Neither the bundles nor the script exist yet (checked 2026-11-13): both are needed before stage 3.
- **Log output:** a 3.3 V USB-UART adapter, RX on J301 pin 6 (UART_TX = CC2340 DIO18, added 2026-11-07), GND on J301 pin 5.
- **Power:**
    - current-limited bench supply (≥ 150 W for the 100 W reverse test);
    - USB-C PD charger with 20 V;
    - DC electronic load with a CV mode, on 20 AWG leads, plus about 2,000 µF;
    - USB power meter and an e-marked 5 A cable;
    - USB-C PD trigger or USB-C electronic load for port tests.
- **Measurement:**
    - DMM;
    - scope with a ground spring;
    - thermocouple or IR camera.

## Pads on P0

The refdes and pin numbers below come from the schematic. KiCad coordinates are for the script-built board on `master` (`Monolith.kicad_pcb`, commit `dd34285`), the design since 2026-11-13. The wire holes, J301 / J302 and the NTCs sit where they sat on the earlier hand-routed board (`8dd9eb6`); most other parts moved.

| Pads | Use |
|---|---|
| J301 (TC2030-NL, "SWD") | CC2340 flash and debug: VCC, SWDIO, NRST, SWCLK, GND |
| J302 (TC2030-NL, "GAUGE") | 1 SDA, 2 CHG_INH, 3 NRST, 4 nc, 5 GND, 6 SCL |
| J108 / J112 | Pack − / +: Ø1.5 mm plated holes for the 18 AWG PACK wires (TE 100G0111-1.00-0) |
| J109–J111 | Cell taps CELL1–CELL3: Ø0.8 mm plated holes for 28 AWG sense wires (TE 55A0111-28-9) |
| J115 / J116 | Gauge Kelvin 1N / 4P: Ø0.8 mm plated holes for 28 AWG wires (TE 55A0111-28-9) |
| J117 / J118, J119 / J120 | Back-cell NTC wires: TS2 and its return, TS3 and its return (returns on CELL_1N). The front-cell NTCs are TH101 / TH104 on the board |
| J113 / J114 | PACK_P / GND, 20 AWG load wires for the learning-cycle discharge, and the bench-supply input for bring-up without cells |
| TP113 (WAKE) + PACK_P | Gauge wake: TP113 (92.45, 130.75) is CELL_P through R118 4.7 kΩ. Connect it to PACK_P for ≥ 0.5 s. The nearest PACK_P pad is C111 pad 2 (94.12, 127.60), 3.6 mm away and small; a jumper lead to J113 or to C444 pad 1 (119.05, 86.17) is easier. (On the hand-routed board TP113 sat 5.2 mm from C444 pad 1 and could be bridged directly.) |
| TP109, TP301 | GND, 3V3 |
| TP412 / TP512 | GND per port |
| Port probe points (no test pads; TP401–TP406 / TP501–TP506 are not on the board) | VBUS C406.1 / C506.1, PPHV R424.1 / R524.1, PP5V C443.1 / C543.1, REGN D410.2 / D510.2, DRV_SUP C411.1 / C511.1, LDO_3V3 C404.1 / C504.1, SW1 / SW2 on the L401 / L501 pads, GND C423.2 / C523.2 |
| Other probe points | SW_5V L402.1 / L502.1, SW_3V3 L201.1, gauge VCC R106.2, BAT R105.2, PBI C105.1, IRQ_N Q103.3, CELL_P F102.2, PACK_P C444.1 |
| J301 pin 6 | UART_TX (CC2340 DIO18, UART0 TX) for bring-up logs |

A wrong plug is harmless: if the SWD cable goes onto J302, the probe drives only CHG_INH and NRST, and its other pins are inputs. **Never put a probe on TP113**: it sits behind 4.7 kΩ to the 16.8 V cell stack.

## 0. Bare board without cells

_Worked out 2026-10-31 from the master netlist and TI's documents (BQ25756, TPS25751, BQ40Z50-R2 TRM SLUUBK0, BQ25756EVM SLUUCT7). Not yet tried on hardware._

**USB-C alone doesn't power the board.** Everything except the two TPS25751s runs from PACK_P (the TPS62177 has VIN and EN on PACK_P), and with no cells only a BQ25756 or a supply on J113 can drive PACK_P.

| Block | USB-C only, blank board | USB-C only, EEPROMs and MCU programmed | Bench supply on J113 |
|---|---|---|---|
| TPS25751 U401 / U501 | Boots from VBUS (dead battery), finds no patch, sits in PTCH. The ADCIN straps are SafeMode, so the sink switch to PPHV stays open | Loads the EEPROM, closes the sink path, sets up its BQ25756 | Runs from 3V3; the MCU can load the patch and write the EEPROM |
| BQ25756 U403 / U503 | Off (PPHV = 0) | On, and charging is enabled because CE_N's 47k pull-up goes to the dead 3V3 rail. With no battery it charges the PACK_P MLCCs to 16.9 V (FB 100k / 10k on 1.536 V), terminates, sags and restarts | I2C alive from SRN; REGN off until VAC appears |
| 3V3, CC2340 | Off | Follow PACK_P. A blank MCU leaves CHG_INH floating, R417 pulls CE_N high, charging stops and 3V3 drops again: a power-cycling loop | On |
| BQ40Z50 | Off | Wakes on VCC (Q102 body diode from PACK_P), but VC1–VC4 float | Same |
| Q101 / Q102 | Off | Off: a factory gauge has Mfg Status Init 0x0000 (`FET_EN` = 0), and its charge pump needs BAT ≥ 2.2 V | Off until the cell simulator is on and BQStudio toggles them |
| 9 V drive U406 / U506 | Off | Off unless the config drives GPIO6 low; needs REGN | Off (no REGN without VAC) |
| BQ294700 | Off | Off | Off until the cell simulator is on |

TI's EVM guide tests the BQ25756 without a battery only with a two-quadrant supply or an electronic load in CV mode, plus about 2,000 µF across the battery terminals. Never debug from USB alone.

**Stages** (R124 / R126 stay off throughout):

1. **Unpowered.** R124 / R126 not fitted. Resistance to GND on PACK_P, 3V3, both VBUS, PPHV, PP5V and REGN; CELL_P (J112) to CELL_N (J108) and each tap hole. Fit 10 kΩ resistors on J117–J120 (TS2 / TS3) or the wired NTCs: the default Temperature Enable is 0x06 (TS1 + TS2), so an open input reads very cold.
2. **USB-C smoke test (optional).** A 5 V charger through a USB power meter, nothing else connected. Expect 3.3 V on that port's LDO_3V3, 0 V on PPHV and PACK_P, a few mA.
3. **Bench supply on J113 (+) / J114 (−).** 12 V at 50 mA, then 14.4 V at 100 mA. Check 3V3 at TP301 and LDO_3V3 on both ports. Flash the CC2340 (target-supplied power; a P0 `.ccxml`, not the LaunchPad one `gmake flash` defaults to). Load each TPS25751 bundle and write both EEPROMs with the I2C loader (Equipment), then read back IO Config (0x5C) on 0x20 and 0x21 and the BQ25756 registers through `I2Cr` against the P0 configuration list (section 3a). The gauge answers on J302, but its cell readings mean nothing yet: don't write data flash.
4. **Cell simulator** (`p0-assembly.md`, Materials) on the seven holes, connected with its supply off, all pins at once.
    - **First set the gauge to 4S:** DA Configuration CC = 4 cell, [NR] = 1, [IN_SYSTEM_SLEEP] = 1, CTEMP = 00 (the factory default is 3S, which reads VC4 as VC3), plus the rest of the section 3 data flash list.
    - Taps at 3.6 V on a DMM, then in BQStudio; voltage calibration.
    - **FET test:** toggle DSG on (MAC 0x0020), then lift the J113 lead. PACK_P should stay up, about 0.5 V below CELL_P, through Q101's body diode. Toggle CHG on (0x001F) and the drop goes. CHG_G and DSG_G sit about 11.5 V above their sources. Raise the simulator's current limit first, since the board's load now comes through J112.
    - **Set FET_EN** once the toggle test passes: MAC 0x0022 while UNSEALED, then confirm ManufacturingStatus()[FET_EN] = 1 (it is copied to Mfg Status Init, so it survives a reset). Without it Q101 / Q102 stay off on real cells after any gauge reset.
    - **Second-level OVP (optional):** toggle both FETs off first so PACK_P isn't driven, then raise the simulator to 17.6 V (4.4 V per cell). U102 (BQ294700, 4.35 V) OUT, on R124's empty pad, goes high after its delay. F102 can't blow with R124 off. Go no higher.
    - **Current calibration:** a 2 A or larger supply on J112 / J108 with the ladder still on the taps, both FETs on, and the DC load on J113 / J114, so the current flows through RS101.
5. **USB-C with a "battery" on PACK_P.** CHG FET off (toggle or gauge reset), so the charger can't push the ladder up. On J113 / J114 put an electronic load in CV mode at 14.4 V with about 2,000 µF, or the bench supply at 14.4 V plus the CC load set above the ICHG you program (the charger then holds CC and the supply covers the rest). CHG_INH low from firmware, or J302 pin 2 held low with the MCU in reset.
    - PD contracts at 5 / 9 / 15 / 20 V; charging at 0.5 A, then 3.25 A per port.
    - 9 V drive: GPIO6 low, DRV_SUP steps from REGN minus D410 (about 4.3 V) to about 9.1–9.3 V. Needs PACK_P ≥ 10 V.
    - On a 5 V / 3 A contract with the 9 V drive off, measure DRV_SUP under load and read DRV_OKZ: worst case is 3.96 V against the 4.0 V recommended minimum.
    - Measure the charger's CV voltage on PACK_P with VFB_REG as configured (target 16.80–16.82 V) before any real-cell charge.
    - Switch nodes on the scope at low power.
    - Source (reverse) mode with the J113 supply as the battery: 20 V at 3 A out takes about 4.5 A from 14.4 V. 100 W runs wait for the cells or a supply of 150 W or more.
6. **Cells:** section 1 below.

**Risks and rules:**

| Risk | Rule |
|---|---|
| J113 bypasses the gauge's OCD / SCD, Q101 / Q102 and F102 | The supply's current limit is the only protection: start at 50 mA, check polarity there, raise it only when a test needs it |
| PACK_P caps are 35 V parts, the TPS62177 28 V, the BQ25756 FB divider sets the charger's CV | Keep PACK_P ≤ 17 V |
| Permanent fail: a factory gauge has Enabled PF A–D = 0x00 and `PF_EN` = `FUSE_EN` = 0, so the simulator can't latch a PF. Once they're on, a floating tap or back-fed ladder can, clearing it needs full access, and a fuse PF also tries to blow F102 | Leave `PF_EN`, `FUSE_EN` and the PF enables off until the board is on real cells with R124 / R126 fitted |
| Floating or partly connected taps | Connect the simulator with its supply off, all seven pins at once |
| With CHG on, a J113 supply above the simulator, or the charger, drives the ladder (16.85 V = 4.21 V per cell at the BQ25756's default VFB_REG) | Keep CHG off whenever something else drives PACK_P |
| Gauge balancing (behind 100 Ω) pulls a 1 kΩ ladder tap well down | Static checks only; use four supplies or a 100 Ω ladder for balancing tests |

## 1. Assembly

1. **Bare board first** (`p0-assembly.md` step 0, and section 0 below): check R124 and R126 are not fitted, power PACK_P from a bench supply on J113 / J114, flash it, add the cell simulator and check the gauge talks, before it meets the cells.
2. **Pack:** with USB unplugged, solder PACK− (J108), then 1N (J115) and CELL1–CELL3 (J109–J111) bottom-up, then 4P (J116), then PACK+ (J112). A floating tap can trip U102, which blows F102 once R124 / R126 are fitted (gauge sheet notes 15 and 16).
3. **Fit R124 and R126** (5.1 kΩ 0402, F.Cu) only after all seven voltages read right at the pads: each step one cell, 2.5–4.2 V.
4. **NTCs:** the front-cell NTCs (TS1, TS4) are TH101 / TH104 on the board, under the gap filler (`research_notes/Pack thermal BAK 65E/smd-ntc.md`). The back-cell NTCs (TS2, TS3) are taped at mid-height, facing the pack centre. Insulated sensors only.
5. **Cell check:** measure each cell at the tap pads before going further.

## 2. First power

1. **Wake the gauge** with USB unplugged: connect TP113 to PACK_P with a jumper lead (J113 or C444 pad 1) for ≥ 0.5 s, or put the J113 supply on at or below the pack voltage. Wake-on-USB is unproven; try it separately (section 4).
2. **Check the rails:** with USB unplugged, PACK_P at TP106 should read the stack (about 14 V), and 3V3 at TP301. 16.8–16.9 V with USB in means the charger is regulating PACK_P and the FETs are still off: FET_EN wasn't set (stage 4).
3. The CC2340 and both EEPROMs were programmed in stage 3; no re-flash is needed.

## 3. Gauge training (BQStudio on J302)

To keep the MCU off the SMBus while BQStudio is connected:
- **Hold the MCU in reset:** J302 pin 3 (NRST) to GND.
- **Keep charging enabled:** J302 pin 2 (CHG_INH) to GND. In reset, the chargers are disabled unless CHG_INH is held low.
- **Never connect the EV2400 with 3V3 down.** An unpowered CC2340 can't take bus voltage.

Steps:

1. **Basic data flash:**
    - 4 cells, design capacity 6,500 mAh (BAK N21700CX-65E, 6,350 mAh minimum);
    - Temperature Enable = 0x1F (TSInt + TS1–TS4) and **Temperature Mode = 0x01** (TSInt is the FET sensor, TS1–TS4 are cells). The default 0x04 makes TS2, the back-cell NTC on J117, a FET sensor, which drops C2 from OTC / UTC and the charge ranges while DAStatus2 still shows it;
    - protection thresholds per `docs/spec.md` (Battery management and protection): OTC 45 °C, UTC 0 °C, OTD 60 °C, OCC ≈ 5 A, OCD1 ≈ 12 A, OCD2 ≈ 14 A, CUV at ≥ 2.8 V per cell, SCD1 and SCD2 as listed there;
    - **FET Options (0x4887) = 0x24**, i.e. `[OTFET]` = 1. The default 0x20 leaves OTFET = 0, so an OTD/OTC trip only sets the flag and never opens the FETs, and the 60 °C OTD backstop does nothing (rev 7 board review, 2026-10-30). Read it back after writing;
    - charge algorithm temperature ranges T1 0 / T2 5 / T3 15 / T4 44 / T5 45 °C (T4 moved from 40 °C on 2026-10-24; unchanged by the 10-28 move of the front NTCs onto the board; OTC recovery 42 °C) with charging current 650 / 3250 / 4550 / 2275 mA, charging voltage 4.20 V (`docs/spec.md`);
    - the cell thermistors that matter are on the front cells (C1 / C4, the pair the board heats), so the hottest cells are seen;
    - **COV 4,250 mV on all four temperature ranges** (default 4,300 mV is past BAK's 4.25 V absolute limit), recovery about 4,100 mV, delay 1 s. SOV about 4,350–4,400 mV before PF is enabled;
    - **Charging Voltage Low ≤ 2,500 mV** (default 2,900 mV). PCHG isn't connected, so with the default a pack drained below 2.9 V per cell can't recover over USB. Keep Precharge Start 2,500 mV and PCHG_COMM 0;
    - Shutdown Voltage 2,700 mV (default 1,750 mV);
    - **UTD** about −20 °C trip / −15 °C recovery, or disabled with firmware derating (the default 0 °C trip opens DSG unconditionally, so the pack and BLE go dead in a cold tent; BAK allows discharge to −20 °C). UTC recovery 1–2 °C (default 5 °C blocks the 0–5 °C 0.65 A band after a trip);
    - Ship Delay ≥ 60 s; BTP_EN 0, or BTP_POL 1 if BTP is used;
    - GAUGE_EN (MAC 0x0021) and LF_EN before the learning cycle;
    - Min Blow Fuse Voltage 10,500 mV, PACK_FUSE 0 (second-level protection);
    - read every item back after writing. Test: all simulator taps at 2.85–2.9 V, CHG turns on with USB.
2. **Chemistry:** select the BAK 65E chemistry ID if it's in TI's database (unlikely). Otherwise run TI's GPCCHEM flow first: a slow (~C/10) discharge with rests, logged and submitted to TI's GPCCHEM tool.
3. **Calibration:**
    - voltage (DMM at the taps);
    - current (known DC load on J113/J114 through RS101);
    - temperature (TS1–TS4);
    - CC offset with no load.
4. **Learning cycle** (TI's procedure for the BQ40Z50):
    1. Charge to full from the USB charger.
    2. Rest ≥ 2 h.
    3. Discharge at ~C/5 (≈ 1.3 A) on J113/J114 to the termination voltage.
    4. Rest ≥ 5 h.
    5. Charge to full again.
    6. Confirm the update status shows a completed learning cycle.
5. **Protection enables:** with R124 / R126 fitted and the pack stable, set Enabled PF A–D, PF_EN and FUSE_EN, read them back, then SEAL.
6. **Export** the data flash as the golden image and commit it to the repo. Later boards load it (p0-assembly step 3.2).

## 3a. P0 configuration lists (to write before stage 3)

There is no single P0 list for the TPS25751 bundle yet, and `docs/devboard/bringup-config-checklist.md` is dev-board only: its GPIO6 liquid-detect line, GPIO4/5 ADC, GPIO7 output and EN_ICHG_PIN = 1 would break P0. The P0 items so far:

- **TPS25751 (both ports):** liquid detection and BC1.2 off; GPIO0/1/2/4/5/7/11 no event, no output, no ADC (they are tied to GND); GPIO3 = fault_input_event_port1 (TPD6S300 FLT); GPIO6 = output, initial high (DRV9_OFF, 9 V drive off); PPHV soft-start 0 or 1 (usb_port sheet note 9); DIS_CE_PIN 0 (note 11); DIS_STAT_PINS 1 (note 13).
- **BQ25756:** VFB_REG 0x0F or 0x0E (16.80–16.82 V; the POR value gives 16.85 V and up to about 17.0 V at tolerance); EN_ICHG_PIN 0 with ICHG_REG 3.25 A (R413 stays 11.8 kΩ, so a watchdog reset falls back to a 4.07–4.45 A pin cap); EN_JEITA 0; IBAT_REV 10 A (the reverse-mode backstop in `docs/spec.md`; the POR value is 20 A, and the dev-board plan held it at 5 A until the 9 V gate-drive test passed); WATCHDOG 00 unless the TPS25751 feeds it; EN_CHG_BIT_RESET_BEHAVIOR (REG0x17 bit 3) 0; ITERM / IPRECHG about 0.25–0.5 A. ICHG_REG is clamped at 0.4 A minimum, so firmware uses EN_CHG / CHG_INH below that.

## 4. Checks that the dev board would have done

| Check | How | Decision it feeds |
|---|---|---|
| Switch-node ringing, both legs, both directions | Scope on the L401 / L501 pads with the ground spring on TP412 / TP512, gate links at 0 Ω | Keep 0 Ω or fit 2.2–10 Ω gate resistors (R444–R447 / R544–R547) |
| SiZ240DT and inductor temperatures at the worst case (XGL7030-332 on both ports) | Reverse 20 V / 5 A from a ~10 V pack, then forward 20 V / 3 A | Thermal throttle limits; XAL7070 fallback for the inductor |
| PP5V load step 0.5 → 3 A | Scope on C443.1 | C443 size (P3: estimated ~190 mV) |
| PD voltage transitions 5 → 20 V with several chargers | Watch VBUS and source resets, with and without firmware SRYR/SRDY sequencing | Firmware sequence required or not |
| PD contract survives an MCU reset (LaunchPad T4, moved here 2026-10-20) | Laptop on a 20 V contract with the e-marked 5 A cable. Force a watchdog reset; scope RST, EN_5V1 and PP5V (C443.1) together | EN_5Vx back high before PP5V falls below 4.75 V (review 4 C-6: 8–80 ms window); the laptop must not see a disconnect |
| Gauge wakes on USB plug-in | Gauge in SHUTDOWN, plug in a 5 V-only charger and a PD charger | Whether the WAKE pad can go in the next spin. Keep automatic ship mode off in firmware until this passes |
| Ship mode holds | Enter ship by MAC and by a simulated CUV; scope PACK_P and measure pack current for ≥ 60 s | PACK_P is left near 2.9 V with only µA of bleed, above the gauge's 2.05–2.45 V start-up threshold: if it re-wakes, lengthen Ship Delay or add a bleed |
| Idle sink detection with EN_5V low | Idle pack, EN_5Vx low, plug in a phone; scope IRQ_N, EN_5V1, PP5V, VBUS, CC | If it fails, EN_5V stays high in idle (~45 µA per port) |
| BLE range | iPhone RSSI at 1, 3 and 10 m in the closed cup, bare and in a backpack | U301 sits in a corner with 6.3 mm of ground on one side (TI asks ≥ 10 mm): retune C313 / C315 / R321, or move U301 in a later spin |
| Sleep current | DMM in series with one pack lead | Firmware power states (estimate ~400 µA with the two TPD6S300s) |
| USB-side bank stress | T593V C421/C456 temperature at reverse 20 V 5 A from a low pack (model: worst part 43 % of rating, an MLCC) | Bank OK, or add a fifth 22u 1210 |

## 5. Production boards

Each board gets the golden image and its own calibration through J302, using the same cable and the same NRST/CHG_INH holds. The J113/J114 load pads and the WAKE pad can stay as they are, or be dropped in a later spin once the checks above pass.
