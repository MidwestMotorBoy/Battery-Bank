# Monolith — Next Actions
_From the 2026-10-09 session · updated 2026-10-11_

## Changes on 2026-10-11
- **Total output raised to 100 W (from 80 W).** Electrically fine: each BQ25756 port can do 20 V × 5 A, and the connector is rated 5 A / 20 V. The limits are heat and current, so 100 W is treated as a thermally limited rating, not a guaranteed continuous one.
- **Why it's thermally limited:** at 100 W out the pack supplies ~107 W after converter losses, ~9 A at the 12 V low end (~1.6C). Heat is ~7–8 W in the converters plus ~4–6 W inside the cells (4 × ≤18 mΩ at 7.5–9 A), so ~12–14 W in a small sealed, potted box (vs ~10 W at 80 W). A full pack only lasts ~45 min at 100 W, which limits how hot it can get, but firmware must still throttle.
- **Cell wear:** EVE rates cycle life at 1C discharge (5.6 A, ~80 W at nominal). 100 W runs above that; occasional use is fine, constant 100 W use shortens cell life.
- **USB2 guaranteed 20 W minimum** whenever a device is attached, so USB1 is capped at 80 W while USB2 is in use, and can take the full 100 W when USB2 is empty. USB2's 20 W is delivered at 9 V and above (9 V × 2.22 A); at 5 V it's capped at 2.5 A (12.5 W) by the PP5V current limit.
- **Thermal throttle: both ports drop to 20 W.** When the pack gets too hot, every active port is cut to 20 W (40 W total with both in use), regardless of USB1 priority. Full power comes back once it has cooled past a lower threshold.
- **PCB and heatsink temperature monitoring added.** Besides the cell thermistor, the board gets NTCs at each power stage, at the USB-C connectors, and under the aluminum heatsink plate. Any working sensor can trigger the 20 W throttle.
- **Broken sensors are ignored, not treated as hot.** Firmware drops a faulted NTC and keeps running at full power on the working ones, as long as at least 3 of the 4 board NTCs are working. Only below that does it fall back to the 20 W limit.
- **Charging plan set.** Normal charging is 0.5C (2.8 A). An optional fast mode charges at 1C (5.6 A) between 20% and 80% SOC. (Interpreted "1A" as 1C — confirm.)
- **Fast charge is an option in the iPhone app**, off by default (gentle 0.5C charging unless turned on).
- **Max SOC is user-settable over Bluetooth**, from a custom iPhone app. **Default 95%.**
- **Both ports can charge at the same time** (e.g. two solar panels, or a panel plus a charger). Firmware-only; no extra hardware.
- **Solar panel in use: Dark Energy 15 W USB-C panel.** Charging must work from a small, possibly 5 V-only, non-PD source.
- **iPhone app planned** as the pack's main interface: live status, temperatures, settings.
- **PCB: one double-sided board.** All ICs, fine-pitch and hot parts on the top side (assembled by JLC, facing the aluminum heatsink plate). The bottom side, facing the cells, holds only parts that are easy to hand-solder. This should avoid the two-board stack; the stack stays as a fallback if the floorplan doesn't fit.
- **BQ25756 switching FETs: Infineon IAUC45N04S6L063H** (JLC C3288896, 62 in stock, ~$1.18; JLC-assembled, top side). A 40 V high-side/low-side pair in one TDSON-8 5 × 6 mm package, logic-level, 6.3 mΩ at 10 V, 13 nC gate charge. Two per BQ25756 (one per buck-boost leg), four per board. 40 V chosen over 30 V parts (CSD87381P) for hot-plug margin on a 20 V port. The 40 V CSD88584Q5DC and FDMD8540L were rejected: 68–81 nC of gate charge is built for ~20 kHz motor drive, far too much for 300–600 kHz. Drop-in backup in the same footprint: IAUC60N04S6L045H (JLC C3278715, 4.5 mΩ, 19 nC). The Vishay SiZ240DT (3.3 × 3.3, ~7 nC) is a better fit electrically but isn't stocked at JLC.
- **TVS diode on each port's VBUS** (SMA, ~22 V standoff class, e.g. SMAJ22A; exact part TBD) so cable hot-plug spikes clamp below the FETs' 40 V rating.
- **BQ25756 inductor: Coilcraft XAL7030-222MEC, 2.2 µH, top side** (JLC C19191686, 459 in stock, ~$13.80 at JLC; cheaper from Coilcraft direct). 7.5 × 7.5 × ~3.1 mm, 0.83–0.86 g, 13.7 mΩ typical / 15.1 max, Isat 18 A (30% drop), Irms 10 A (20 °C rise) / 12.9 A (40 °C rise). Both BQ25756s run at their **600 kHz maximum** (R_FSW = 40 kΩ on FSW_SYNC; range is 200–600 kHz). Ripple ~3.6 A peak-to-peak; worst case (100 W from a 12 V pack, ~8.8 A) peaks at ~10.6 A, well under Isat. Worst-case copper loss ~1.2 W, into the plate via the gap pad. TI's EVM-style inductor (10 µH IHLP-6767 at 250 kHz, ~17 × 17 × 7 mm) is roughly 10–12 g by size estimate, so this saves ~20 g across both ports.
- **Why this one:** chosen to keep the gap pad thin. At ~3 mm it's no taller than the USB-C connectors or the bottom-side 5 V inductors. Rejected: XAL7070-332 (7 mm tall, would set a thick gap pad); moving the inductors to the bottom (same total stack height, puts their heat into the cells, and the XAL's under-body terminals can't be hand-soldered with an iron); XGL6030-222 (0.7 g but in soft saturation at the worst case); XAL8080 (3 g, 8 mm, unneeded margin).
- **600 kHz cost:** FET switching loss roughly doubles vs 300 kHz (an estimated few tenths of a watt per stage at full power with the IAUC45N04S6L063H); gate drive is ~4 × 6.5 nC × 600 kHz ≈ 16 mA per BQ25756 worst case, which is fine.
- **Port TVS picked: Littelfuse SMAJ22A** (JLC C148220, ~$0.13; alt Vishay SMAJ22AHE3, C1978443). 22 V standoff, 24.4–26.9 V breakdown, 35.5 V clamp at 11.3 A, 400 W SMA. Clamps below the 40 V FET rating; top side next to each connector.
- **BQ25756 sense resistors picked: Yageo PA2010FKE470R005Z, 5 mΩ 1% 2 W 2010, ±50 ppm/°C** (JLC C7256567) for both input (RAC) and battery (RBAT) sense, one part number for all four. 5 mΩ is TI's recommended value and matches the EVM. Worst case 0.39 W on the battery side (8.8 A).
- **Gauge shunt picked: Yageo PA2512FKE7W0R001E, 1 mΩ 1% 2 W 2512, ±50 ppm/°C** (LCSC C326570, bottom side, hand-solder). 10 mV / 0.1 W at 10 A.
- **TPS62933 switching at 1.2 MHz** (RT tied straight to GND, no resistor), so the inductor drops to TI's 3.3 µH table value. On-time at 16.8 V in is ~250 ns, well above the 70 ns minimum.
- **TPS62933 inductors picked: Bourns SRP5030T-3R3M, 3.3 µH** (LCSC C189931, bottom, hand-solder). 5.7 × 5.2 × 3.0 mm, Isat 8 A (above the TPS62933's 5.8 A max switch limit), 38 mΩ. Ripple ~0.9 A (~30% of 3 A).
- **TPS62177 inductor picked: Bourns SRN4018TA-100M, 10 µH** (LCSC C2044417, bottom, hand-solder). 4 × 4 × 1.8 mm, Isat 1.5 A (above the 1.2 A max switch limit), 150 mΩ. TI's datasheet recommends 10 µH (the earlier 2.5 × 2 mm placeholder was too small).
- **Precision resistor values (all Yageo RT thin film, 0.1%, ±25 ppm/°C; seven unique values):**
  - 10.0 kΩ 0805 (C110775): 4 board-NTC bias resistors + both BQ25756 FB bottom resistors
  - 100 kΩ 0805 (C122537): both BQ25756 FB top resistors. 100k/10k gives an 11:1 divider, so 16.8 V needs VFB = 1.527 V, inside the BQ25756's programmable 1.504–1.566 V range; firmware sets VFB_REG to match
  - 40.2 kΩ 0805 (C865475): BQ25756 FSW_SYNC, ~600 kHz
  - 105 kΩ + 20.0 kΩ 0805 (C865128, C469660): TPS62933 feedback, 0.8 V × (1 + 105/20) = 5.00 V
  - 1.74 kΩ 0603 (C784581) + 5.11 kΩ 0603 (C705788): BQ25756 TS network (RT1 / RT2), see TS plan below
  - 5.11 kΩ (same part): BQ25756 ICHG pin, hardware charge-current ceiling 50 A·kΩ / 5.11 kΩ ≈ 9.8 A (covers 1C plus pass-through load)
  - 3.65 kΩ 0603 (C705773): BQ25756 ILIM_HIZ, hardware input-current ceiling 20 A·kΩ / 3.65 kΩ ≈ 5.5 A (with 5 mΩ RAC, KILIM = 50 A·kΩ × 2/5 = 20 A·kΩ)
  - 137 kΩ + 40.2 kΩ + 10.0 kΩ: BQ25756 ACUV/ACOV divider from VAC (ACUV at the 137k/40.2k junction, ACOV at 40.2k/10k): 22.5 V overvoltage stop, 4.1 V undervoltage stop, 4.5 V hardware input-regulation floor (protects weak 5 V sources and panels)
  - Nine unique 0.1% values in total: 10k, 100k, 40.2k, 105k, 20k, 1.74k, 5.11k, 3.65k, 137k
- **BQ25756 capacitors: all-ceramic bank, mostly hand-soldered on the bottom.** The datasheet asks for ≥ 80 µF effective on both the USB side and the battery side after DC-bias derating. Per port:
  - USB side: 10 × Taiyo Yuden GMK325BJ226MM-P, 22 µF 35 V X5R 1210 (JLC C778721, ~$0.34). ~8 µF each at 20 V → ~80 µF. 35 V rating sits just under the SMAJ22A's 35.5 V clamp; MLCCs tolerate brief transients above rating.
  - Battery side: 7 × Taiyo Yuden TMK325ABJ476MM-P, 47 µF 25 V X5R 1210 (JLC C90142, ~$0.68). ~13 µF each at 16.8 V → ~90 µF.
  - Two of each on top at the FETs (high-frequency loop, plus a 0.1 µF each side); the remaining 8 + 5 hand-soldered on the bottom directly under the power stage, connected through via arrays. 1210s are ~2.5 mm tall, inside the 3 mm bottom height budget.
  - Board total: 34 × 1210 (8 on top, 26 on the bottom), roughly 2 g. Derating figures are estimates; confirm against Taiyo Yuden's DC-bias curves.
- **I2C architecture decided: each TPS25751 is the I2C master for its own BQ25756; the STM32WB talks only to the two TPS25751s and the gauge.** Reasons: the STM32WB15 has only one I2C peripheral; the BQ25756s would otherwise collide on one bus; and TI confirms the TPS25751 doesn't support multi-master, so the charger can't sit on both buses. With the TPS25751 in charge, it sets the BQ25756 source voltage before PS_RDY, which is the TI-tested path for PD sourcing. The STM32WB reaches the chargers through the TPS25751's "I2Cr"/"I2Cw" 4CC passthrough commands for our own charge policy (current, VFB, MPPT, ADC reads). One bus from the STM32WB: BQ40Z50-R2 (SMBus 0x0B) + TPS25751 #1 and #2 at different addresses set by ADCIN1/2. Source: TI E2E thread 1320328.
- **TPS25751 manual findings (partial; the full TRM PDF couldn't be fetched past the register chapter):**
  - 'I2Cr' / 'I2Cw' are 4CC tasks that run a read/write on the TPS25751's I2C controller bus. Reported DATA1 layout from TI forum threads (not yet confirmed against the TRM): target address, register, byte count, then data. Early TPS25750 firmware had bugs here that TI fixed in later configuration-tool releases, so use current firmware.
  - Host events to watch on IRQ: Plug Insert/Removal, New Contract as Provider / Consumer, Sink Transition Completed, Power Swap Complete, Power Event (OVP/ILIM/TSD), Overcurrent, Unable to Source, Ext DCDC Source/Sink Safe State. The STM32WB re-applies its charge settings after each contract or role event.
  - How much charger setup the TPS25751 does on its own is set in TI's Application Customization Tool configuration, not documented in the register chapter. Plan: let it handle PD voltage/current transitions; the STM32WB owns charge current, VFB and MPPT through I2Cw.
  - Dead battery: with no 3.3 V the TPS25751 runs from VBUS, presents Rd, and reports dead-battery boot in BOOT_FLAGS (0x2D) until the host clears it with 'DBfg'.
  - TI forum note: I2C pull-ups on the TPS25751's buses go to its LDO_3V3 (one user's I2C failure was fixed by this).
- **TPS25751 strapping decided (from datasheet Table 8-2, Table 8-5 and the pin-strapping table):** both ports use the **SafeMode** dead-battery option, which TI recommends when the PD controller manages the battery charger or loads its patch from EEPROM. In SafeMode the sink path stays off until the configuration loads; with an EEPROM that happens from VBUS power alone, so a dead pack still charges.
  - Port 1 (USB1): ADCIN1 tied to LDO_3V3 (value 7), ADCIN2 tied to GND (value 0) → address index #1 = **0x20**
  - Port 2 (USB2): ADCIN1 and ADCIN2 both tied to GND (0, 0) → index #2 = **0x21**
  - No divider resistors needed. STM32WB bus: 0x0B gauge, 0x20 and 0x21 PD controllers; no conflicts.
  - Rejected: AlwaysEnableSink (meant for an external controller managing the charger) and NegotiateHighVoltage (TI: not valid with a supported battery charger or EEPROM patch).
- **EEPROM per port: ST M24512-DFMC6TG, 512 Kbit, DFN8 2 × 3 mm** (JLC C222237, ~$0.57, top side; upsized from 256 Kbit). Each TPS25751 needs its own EEPROM (TI: they can't be shared), at 7-bit address 0x50 on that port's controller bus, alongside its BQ25756. TI's EEPROM layout is fixed at 32 KB (pointers at 0x0000/0x0400, regions at 0x0800 and 0x4400, up to 15 KB each), so 256 Kbit would also fit exactly; the 512 Kbit part is cheaper and leaves the upper half unused. Full details in `claude/tps25751-eeprom-programming.md`.
- **EEPROM programming plan: all in-system, by the STM32WB, no extra pads** (TI app notes SLVAFL1 and SLVAFV8):
  1. Flash the STM32WB once over SWD (new bottom-side pogo pads, see below). Its firmware carries the TPS25751 patch bundle (~16 KB).
  2. On every boot the STM32WB reads each TPS25751's MODE register (0x03). A blank or corrupt EEPROM leaves the controller waiting in PTCH mode; the STM32WB then pushes the bundle over I2Ct with 'PBMs' … 'PBMc' (SLVAFV8), which puts it in APP mode.
  3. In APP mode the STM32WB writes the EEPROM through the TPS25751: 'FLrd' (get the inactive region address), 'FLad' (set start address), 'FLwd' (32 bytes per write, address auto-increments), 'FLvy' (verify), then 'GAID' (cold reset) so it reboots from EEPROM (SLVAFL1).
  4. The old bundle stays valid until the new one verifies, so a power cut mid-update can't brick a port.
  - Result: first-time programming happens automatically at the first power-up after the STM32WB is flashed, and PD configuration changes can ship later inside a Bluetooth firmware update.
  - TPS25750 (the older part) couldn't program its EEPROM itself; this flow is TPS25751-specific.
  - Until programmed, each port is in SafeMode with no sink path and no PD; power the first boot from a bench supply on the pack pads.
- **STM32WB SWD programming pads added (bottom side, bare copper like the gauge pads):** SWDIO, SWCLK, NRST, 3V3, GND at 2.54 mm pitch, for an ST-LINK through a pogo probe. Needed before potting; after potting, updates go over Bluetooth.
- **Patch loading: one small I2C EEPROM per TPS25751** on its controller bus (shared with its BQ25756), so each port boots and negotiates USB-C power by itself even if the STM32WB firmware is broken. Important for a potted pack: the ports keep working while you reflash the MCU over Bluetooth. Alternative: the STM32WB loads the patch bundle over I2Ct (TI app note SLVAFV8), saving two parts but making the ports depend on MCU firmware.
- **TPS25751 interrupts:** each controller's I2Ct_IRQ (open-drain, active low) gets its own STM32WB pin, using the STM32's internal pull-up (no resistor; ~80 µA only while an event is pending, so firmware clears events promptly). USB1 → PA0, USB2 → PA2: separate EXTI lines (0 and 2), and both are the STM32WB15's wake-up pins, so a plug-in can wake the MCU from any sleep mode. Interrupt mask (0x16) to enable: Ready for Patch, CMD1 Complete, Plug Insert/Removal, New Contract as Provider, New Contract as Consumer, Sink Transition Completed, Power Swap Complete, Power Event (OVP/ILIM/TSD), Overcurrent, Unable to Source, Ext DCDC Source/Sink Safe State, Status / Power Status updates. Clear via 0x18 after each read of 0x14.
- **STM32WB1MMC pin map (first pass).** The module brings out PA0–PA14 and PB0, PB1, PB2, PB4–PB8. Alternate functions below follow the standard STM32WB mapping; confirm each in STM32CubeMX for the WB1MMC before the schematic:
  | Pin | Use |
  |---|---|
  | PA0 | USB1 TPS25751 IRQ (EXTI0, WKUP) |
  | PA2 | USB2 TPS25751 IRQ (EXTI2, WKUP) |
  | PB6 / PB7 | I2C1 SCL / SDA: gauge 0x0B, PD controllers 0x20 / 0x21; 4.7 kΩ pull-ups to 3.3 V; 100 kHz (SMBus for the gauge) |
  | PA1 | NTC TH1, USB1 power stage (ADC1) |
  | PA3 | NTC TH2, USB2 power stage (ADC1) |
  | PA4 | NTC TH3, connectors (ADC1) |
  | PA5 | NTC TH4, heatsink plate (ADC1) |
  | PB0 | NTC divider supply (high only while sampling, so the dividers draw nothing in sleep) |
  | PB1 | TPS62933 enable, USB1 PP5V |
  | PB2 | TPS62933 enable, USB2 PP5V |
  | PA13 / PA14 / NRST | SWDIO / SWCLK / reset, to the SWD pogo pads |
  | BOOT0 | pulled low |
  | Spare | PA6–PA12, PB4, PB5, PB8 (ADC-capable spares: PA6–PA9) |
- **Bluetooth updates (STM32WB):** no strap pins are needed, but Bluetooth flashing does need an initial SWD program; the STM32's built-in ROM bootloader has no Bluetooth path. Plan, based on ST's BLE_Ota example in STM32CubeWB:
  - SWD-flash once before potting: ST's BLE_Ota loader at the start of flash, our application after it, and option bytes set to always boot from main flash (nSWBOOT0 = 0, nBOOT0 = 1) so the BOOT0 pin is ignored. Keep a pull-down on BOOT0 anyway.
  - Check the module's Bluetooth stack (CPU2 wireless stack) and FUS versions; install or update them over SWD with STM32CubeProgrammer if needed. Later stack updates can also go over Bluetooth through the loader.
  - The application enters update mode on a bonded command from the iPhone app (sets a flag, resets into the loader); the loader is never overwritten by application updates.
  - Brick protection for the potted pack: the loader checks the application's CRC before jumping, and the application must feed the independent watchdog. If the application is invalid or keeps watchdog-resetting, the loader stays in Bluetooth update mode instead of booting it.
- **Bluetooth pairing is buttonless (proposed).** The pack has no button or display, so plugging in a USB cable is the "I'm holding it" signal:
  - Pairing is accepted only for ~2 minutes after a USB device or charger is plugged into either port (the TPS25751 plug-insert interrupt opens the window), or anytime while the pack has no bonded phone yet (first setup).
  - Bluetooth LE Secure Connections; iOS shows its normal "Pair" prompt. Optional extra: a 6-digit passkey printed on the pack (iOS asks for it during pairing).
  - Outside the window, new pairing requests are refused; already-bonded phones reconnect normally. Writes (settings, firmware updates) need a bonded phone.
  - Up to ~4 bonded phones. To clear them without the app (lost phone): a plug gesture, e.g. plug and unplug a cable 5 times within 15 seconds.
- At 100 kHz, loading an ~11 KB patch over I2C takes ~1 s per port; the EEPROM write time is dominated by command polling (~10–15 s per port, first boot only).
- **Board stack-up decided: 4 layers, 0.8 mm thick** (the connector requires it, see below).
  - Weight: the bare 44 × 44 mm board is ~2.9 g at 0.8 mm vs ~4.3 g at 1.2 mm and ~5.7 g at 1.6 mm. Potting stiffens it, and the cap wall takes plug forces, so a thin board is fine.
  - **USB-C connector drawing checked (Shou Han TYPE-C 16PCB0.8 IP68, C55629727, rev A5 2026-04-01):** mid-mount; the body sits in a **10.2 mm wide × 4.7 mm deep notch at the board edge**, held by four slotted plated shell holes (1.0 × 1.4 mm slots, 11.6 mm across), with the 12 SMT signal/power pads in a row just behind the notch (6.4 mm span, 0.30/0.60 mm pads, 1.0 mm long). Made for a 0.8 mm board, so the C55629727 variant is the one to order. About 1.8 mm above and below the board (4.45 mm tall flange), so it fits both height budgets.
  - Front sealing flange with silicone ring: 10.25 × 4.45 mm, sticks out **2.9 mm past the board edge**. The cap wall opening seals on that ring. Consequence: the port-side board edge has to sit ~2.9 mm behind the cap's outer face, so the board likely shrinks ~1 mm in that direction (44 → ~43 mm), depending on cap wall thickness.
  - Ratings: 5 A, 20 V, IP68 (1.5 m, 30 min), −35 to +80 °C, 10,000 cycles, insertion 0.5–2.0 kgf. Contact resistance up to 40 mΩ per pin: at 5 A through 4 VBUS + 4 GND pins that's up to ~0.5 W in each connector, another reason for big VBUS/GND copper and the connector NTC.
  - Layers: L1 top parts + power pours; L2 solid ground; L3 power planes (pack bus, each port's VBUS); L4 bottom parts + second pack-bus pour.
  - Copper: aim for 2 oz outer / 1 oz inner if JLC offers it at 0.8 mm, otherwise go to 1.0 mm. 10 A needs ~4.7 mm of 1 oz outer copper for a 20 °C rise (~2.4 mm at 2 oz), easily met with pours on two layers over these short runs.
  - A thin board also heats faster for hand-soldering the 16 AWG pads and bottom-side caps.
- **Gap pad height mismatch:** tallest top parts are the XAL7030s (~3.1 mm); the FETs and ICs are ~1 mm. A flat plate resting near the inductor tops leaves ~2 mm over the FETs. Plan a stepped pad: thin (~0.5 mm) over the inductors, ~2.5 mm pieces over the FET pairs and BQ25756s (soft pads compress ~20–30%). Alternative: a soft gap filler or a thermally conductive potting compound under the plate (heavier: ~2–3 g/cm³ vs ~1.1).
- **FET losses at 600 kHz (IAUC45N04S6L063H, estimates):** worst case (100 W out from a 12 V pack, 8.8 A, boosting to 20 V) ≈ 2.6 W per charger: conduction 1.6 W (two FETs in the path at ~10 mΩ hot with ~5 V drive), switching ~0.5 W, dead-time diode ~0.3 W, Qrr + Coss ~0.15 W. At 300 kHz it would be ~2.1 W, so 600 kHz costs ~0.5 W per charger in the worst case. Typical 60 W from a mid pack: ~0.85 W per charger. Per-package dissipation ≤ ~1.3 W, fine with copper + gap pad (RthJC 3.7 K/W).
- **Sleep budget corrected: ~150 µA, not ~40 µA.** The earlier figure missed the gauge and chargers. BQ40Z50-R2 SLEEP with DSG on 75 µA; 2 × BQ25756 battery quiescent ~17 µA each (ADC off; spec'd at 28 V); 2 × TPS25751 56 µA each at 3.3 V plus STM32WB (~15 µA with slow advertising, estimate) → ~35 µA at the pack through the TPS62177; TPS62177 Iq ~5 µA; 2 × TPS62933 off ~4 µA (estimate). About 1.3 Ah/year, **~2% per month self-discharge** while idle.
- **Storage mode: skipped (decided 2026-10-11).** The pack idles at ~150 µA (~2%/month); top it up before trips. The BQ40Z50-R2 low-voltage shutdown still protects a forgotten pack from over-discharge.
- **BQ25756 TS plan:** each charger gets its own 10 kΩ NTC (same 0603 part as the board NTCs) beside its FETs, as a hardware backup that works even if the STM32WB hangs. Divider RT1 = 1.74 kΩ, RT2 = 5.11 kΩ from REGN puts the hot cutoff (34.4% of REGN) at ~95 °C and the cold cutoff (73.25%) at ~-20 °C. The BQ25756's JEITA "cool/warm" bands land at ~13 °C and ~80 °C; set their current/voltage reductions to none in firmware, since cell temperature is the gauge's job. Two extra NTCs per board (TH5, TH6).
- **Datasheet checks done:** 2.2 µH is the minimum inductance the BQ25756 datasheet allows (2.2–15 µH), so the XAL7030-222 is at the floor. Gate drive is ~4 × 6.5 nC × 600 kHz ≈ 16 mA from REGN (spec 20 mA, limit 70 mA); fine, but REGN dissipates ~0.25 W from a 20 V input. In boost mode the 225 ns forced high-side time caps duty at ~86% at 600 kHz, enough for 5 V → 16.8 V (needs ~70%).
- **Battery connection enlarged:** pack + and − come in on 16 AWG silicone wires through Ø1.8 mm plated holes in 7 × 5.5 mm pads at the port edge, soldered both sides, with ~20 vias into the inner power plane. The top side above both holes is kept clear so soldering them can't reflow anything.
- **Gauge shunt moved** to the bottom side right next to the B− pad. The AGM404AP1 protection FETs (Q5/Q6) moved outboard on the top so nothing sits above the shunt.
- **Floorplan published** ("Monolith PCB Floorplan" artifact, v3): ~74% of the top side claimed. Fits on paper, but tight.
- **Inductor split:** the three small-converter inductors (two TPS62933 5 V bucks, one TPS62177 3.3 V buck) go on the hand-soldered bottom side to free top-side space. The two big BQ25756 inductors stay on top against the gap pad, because they dissipate ~0.5–1 W each at full power and that heat should go to the plate, not the cells. If the floorplan still doesn't fit, the BQ25756 inductors are the next candidates to move.

## Changes on 2026-10-10
- **Cell confirmed:** EVE INR21700-58E stays the pick over the Samsung 58E (more Wh, lighter, slimmer, better cold discharge). Specs and design notes in `claude/eve-58e-datasheet-notes.md`.
- **Housing cavity corrected:** cells are up to 21.7 mm wide (not 21 mm) and EVE recommends > 1 mm between cells, so the 2x2 inner cavity is ~44.5–45 mm, outer ~46–46.5 mm with 0.8 mm FR4. The earlier 42.5 mm figure was wrong.
- **Pack energy:** 82 Wh nominal (80.6 Wh min); use 82 Wh on the label.
- **Cell vendor:** the store found online is **18650batterystore.com**; the earlier notes said 18650battery.com. Confirm the right site before ordering.
- **New design rules from the datasheet:** no charging below 0 °C, thermistor at mid-cell (30–34 mm from the bottom).
- **Gauge part upgraded:** BQ40Z50-R2 instead of the plain BQ40Z50 (TI's newer drop-in; adds JEITA/adaptive charging and a black-box recorder). Order the "-R2" suffix: BQ40Z50RSMR-R2 or BQ40Z50RSMT-R2.
- **Gauge programmer ordered:** EV2400-compatible clone adapter from Amazon, to use with TI BQStudio.
- **Separate training board:** the production board is tight on space, so chemistry ID and the learning cycle happen on a small dedicated training board. The result is exported as a golden image and loaded onto the production board, which then gets its own calibration.
- **Production gauge access:** three bottom-side pogo-pin test pads (SMBus clock, data, ground), no connector.
- **Resistor tolerance:** 0.1% resistors everywhere except the current shunt, which is assumed 1%.
- **3.3 V rail:** TPS62177DQCR buck (kept over an LDO by choice; the TPS70933 LDO was a close alternative).
- **Why a TPS62933 on each port's PP5V:** per the TPS25751 datasheet and TI's EVM, a port's 5 V output comes from the TPS25751's internal PP5V switch (up to 3 A), and PP5V also powers VCONN for e-marked cables. 9/15/20 V come from the BQ25756 through the high-voltage path. Sourcing 5 V from the BQ25756 instead is configurable but unproven (one TI forum thread ended with the charger faulting).
- **Sleep target relaxed:** each TPS25751 draws 56 µA from 3.3 V in sleep and stays powered so it can detect a phone being plugged in (cutting its supply breaks sink detection). With two ports that's ~40 µA total at the pack, ~6–7%/year. The BQ40Z50-R2's low-voltage shutdown protects a stored pack from over-discharge.
- **5 V bias rail dropped:** the TPS25751 runs from the 3.3 V rail (3.0–3.6 V) and the BQ25756 has its own internal supply.
- **Two identical ports:** both USB-C ports are the same — bidirectional (charge in or power out), 5–20 V, up to 5 A. Each port gets its own TPS25751 + BQ25756 + TPS62933. This replaced the earlier 65 W port 1 + 5 V-only port 2 plan; the TPS25810 and port 2 load switch are dropped.
- **USB-C connector (from a separate chat):** Shou Han TYPE-C 16PCB IP68 family, a JLC/LCSC library part. The datasheet rates it 5 A / 20 V; IP68 (1.5 m for 30 min) includes the dust-tight "6", so it meets the IP65-or-better requirement. Right-angle, so the ports exit the side wall of the top cap. Replaces the Amphenol 12402082E512A (IPX8, no dust rating, 16-week lead time) and the GCT USB4725 (IP67 but not in JLC's library).
- **Heatsink (from a separate chat):** a JLC aluminum-core PCB used as a flat heat-spreader plate over the power stage, with a gap pad to the FETs and inductors. Finned heatsinks were ruled out because fins buried in potting do nothing.
- **Pass-through charging:** charge the pack from one port while powering a device from the other at the same time. One BQ25756 runs in charge mode and the other in reverse mode, both on the shared pack bus. The rest is firmware.
- **USB1 gets priority** when both ports are powering devices.

## Decisions locked in
- **Pack:** 4S1P, 2x2 bundle of EVE INR21700-58E bare flat-tops (82 Wh nominal, under the 100 Wh airline carry-on limit)
- **Cell source:** 18650batterystore.com (verify domain; ~$5.99/cell)
- **Connections:** spot-welded nickel, not spring contacts
- **Welder:** kWeld complete kit + kCap ultracapacitor module, bought direct from keenlab
- **Housing walls:** 0.8 mm blank FR4 panels used as plain fiberglass plates (chosen for stiffness and flatness; roughly the same weight as 1.2 mm Tough 2000 resin)
- **Housing cavity:** ~44.5–45 mm inner square for the 2x2 bundle with > 1 mm cell spacing
- **Wall corners:** interlocking finger joints at the four vertical corners, with dog-bone reliefs at inside corners and ~0.1 mm clearance per side
- **End caps:** printed caps at top and bottom (Tough 2000), each with a continuous square groove ~1.2 mm wide x 3–4 mm deep that the panel edges seat into, with at least 1.2 mm of resin on each side of the groove
- **Bottom cap:** shallow pockets to locate the 2x2 cell bundle and hold the > 1 mm spacing
- **Top cap:** holds the potted double-sided PCB and the two USB-C ports, which exit through its side walls
- **Sealing:** IP65 via bonded seams: fill the end-cap grooves about half to two-thirds with neutral-cure RTV or structural epoxy before pressing panels in, bond the finger joints, and seal FR4 cut edges
- **PCB:** one double-sided board. Top side = all ICs, fine-pitch and hot parts (including both BQ25756 inductors), assembled by JLC (single-sided assembly), facing the heatsink plate. Bottom side = only easy hand-solder parts (including the three small-buck inductors), facing the cells (see PCB layout below). Two-board stack only as a fallback
- **Ports:** two identical USB-C PD ports, bidirectional, 5–20 V, up to 5 A each (5 A needs an e-marked cable; with a normal 3 A cable a port tops out at 60 W); 5 V limited to 2.5 A by the PP5V current-limit setting; **100 W total output**, thermally limited
- **Power sharing:** USB1 has priority. USB1 alone: up to 100 W (20 V × 5 A). Both ports in use: USB2 is guaranteed 20 W, USB1 gets up to 80 W, and USB2 can rise above 20 W with whatever USB1 isn't using
- **Thermal throttle:** when hot, every active port drops to 20 W (both ports equal, priority ignored); restores with hysteresis once cooled
- **Temperature sensing:** cell thermistor on the BQ40Z50-R2, plus 4 board NTCs (each BQ25756 power stage, the USB-C connectors, under the heatsink plate) read by the STM32WB. Any working sensor can trigger the throttle
- **Sensor faults:** a broken NTC is ignored and the pack runs on the working ones; full power stays available while at least 3 of 4 board NTCs work. Below 3, fall back to the 20 W limit. The cell thermistor is handled by the BQ40Z50-R2 itself
- **Pass-through:** supported — one port charging while the other powers a device
- **Charging (see Charging plan below):** BQ40Z50-R2 decides, STM32WB relays to the charging BQ25756(s). 0.5C by default; optional 1C fast window 20–80% from the app; stop at the max SOC (default 95%). JEITA 0–45 °C. Either or both ports can charge. Solar MPPT in the BQ25756
- **Max SOC:** user-settable over Bluetooth, default 95%, stored in the pack so it applies without the phone present
- **Fast charge:** app setting, default off
- **Solar:** Dark Energy 15 W USB-C panel is the reference source; must charge reliably from it, including 5 V-only (non-PD) output
- **iPhone app:** custom app over Bluetooth LE (STM32WB) for status, temperatures and settings (see iPhone app section)
- **USB-C connector:** Shou Han TYPE-C 16PCB IP68, right-angle SMT, 16-pin, rated 5 A / 20 V (per datasheet), IP68 1.5 m / 30 min, 10,000 mating cycles, operating range up to 80 °C. Variants by board thickness: C55629727 (0.8), C55629728 (1.2), C55629729 (1.6); ~$0.49 each
- **Heatsink:** JLC single-sided aluminum-core board as a spreader plate over the PCB's top side; bare aluminum facing in against a thermal gap pad over the FETs and BQ25756 inductors, solder-mask side facing out (silkscreen for port labels/logo); notched clear of the STM32WB antenna
- **Protection / balancing / SOC:** TI BQ40Z50-R2 (1–4S, Impedance Track gauging), SMBus to the STM32WB
- **Gauge programming:** EV2400-compatible clone + TI BQStudio (Windows); STM32WB handles telemetry and can also read/configure the gauge
- **Gauge training:** separate training board; golden image + per-board calibration on production
- **Production gauge access:** bottom-side pogo pads for SMBC, SMBD, GND
- **Resistors:** 0.1% everywhere (dividers, thermistor bias, feedback networks); current shunt 1%, low tempco (metal element, ≤ 50 ppm/°C)
- **3.3 V always-on rail:** TI TPS62177DQCR fixed 3.3 V buck — 4.75–28 V in, 500 mA, ~4.8 µA Iq in sleep mode, WSON-10 2x3 mm. LCSC C91241 (JLC Extended). Powers the STM32WB and both TPS25751s (VIN_3V3)
- **Per-port 5 V (PP5V):** one TI TPS62933DRLR per port feeding that port's TPS25751 PP5V pin — 5 V output (internal 3 A switch) and VCONN. 3.8–30 V in, 3 A, SOT-583 1.6x2.1 mm, ~12 µA Iq. LCSC C3200405 (JLC Extended; one part number for both). Each enabled only when its port needs 5 V or VCONN
- **PD controller (x2):** TPS25751DREFR, LCSC C30169739 (JLC Extended), always powered from 3.3 V
- **BQ25756 switching FETs (x4):** Infineon IAUC45N04S6L063H 40 V half-bridge, TDSON-8 5 × 6, JLC C3288896 (backup IAUC60N04S6L045H, C3278715, same footprint)
- **Port VBUS TVS (x2):** Littelfuse SMAJ22A (C148220)
- **Port CC and D+/D− ESD (x4, 2 per port):** TI ESD2CAN24DBZRQ1 (C5736151), ±24 V working voltage so a CC/D± short to 20 V VBUS doesn't destroy it
- **Charger sense resistors (x4):** Yageo PA2010FKE470R005Z 5 mΩ 2010
- **Gauge shunt:** Yageo PA2512FKE7W0R001E 1 mΩ 2512 (bottom)
- **Small-buck inductors (bottom):** Bourns SRP5030T-3R3M (x2, TPS62933 at 1.2 MHz), Bourns SRN4018TA-100M (TPS62177)
- **Battery leads:** 16 AWG silicone wire through Ø1.8 mm plated holes, top side kept clear above them
- **Charger / PD power stage (x2):** BQ25756RRVR, LCSC C19272232 (JLC Extended); bidirectional buck-boost, sources 9/15/20 V through the TPS25751 high-voltage path and charges the pack from either port. Built-in solar MPPT, input voltage/current regulation, TS/JEITA input, 16-bit ADC
- **Gauge part:** BQ40Z50RSMR-R2, LCSC C2845123 (JLC Extended)
- **Sleep current:** ~150 µA total at the pack when idle (~2%/month); no storage mode
- **Schematic + PCB tool:** ProtoFlow (free tier), with KiCad for final cleanup

## PCB layout (double-sided, bottom side hand-soldered)
**Rule:** JLC assembles the top side only. The bottom side holds nothing you can't hand-solder with an ordinary iron: no QFN/WSON/BGA, no parts with hidden pads, nothing smaller than 0603.

**Top side — JLC-assembled, facing the gap pad and aluminum plate (outside of the pack):**
- Every IC: both BQ25756s, both TPS25751s, both TPS62933s, the TPS62177, the BQ40Z50-R2 and the STM32WB1MMC (all are QFN/WSON/SOT-583 or modules with pads underneath — not hand-solder parts)
- BQ25756 power stages: switching FETs, **both BQ25756 inductors**, sense resistors; plus the protection FETs (AGM404AP1). The BQ25756 inductors dissipate ~0.5–1 W each at full power, so they need the gap pad and plate
- Every decoupling cap and every part that has to sit right at an IC pin (input/output caps of each converter, bootstrap caps, compensation, the BQ40Z50-R2's cell-tap filter caps, buck feedback dividers)
- Both USB-C connectors at the board edge
- All four board NTCs (power stages, connectors, heatsink) — they have to touch what they're watching
- The STM32WB1MMC in the corner under the plate's antenna notch. Its antenna can't face the cells: the metal cans would block most of its range

**Bottom side — hand-soldered by you, facing the cells. Only large, easy parts:**
- **The three small-buck inductors:** one per TPS62933 (x2) and one for the TPS62177. Each sits directly under its IC so the switch-node path through the board is as short as possible. Losses are small (~0.3–0.5 W per TPS62933 inductor at a full 3 A, near zero for the TPS62177's)
- Gauge current shunt (2512 or 2010 size, Kelvin pads), near where the pack's main leads come in
- Pads for the pack's main + / − leads, the cell-tap wires and the cell thermistor wire
- NTC bias resistors, I2C/SMBus pull-ups and other non-critical resistors, in 0805 (0603 at the smallest)
- The BQ25756 bulk capacitors: per port 8 × 22 µF 35 V and 5 × 47 µF 25 V, all 1210, directly under each power stage
- The SMBus pogo pads (bare copper, nothing to solder)

**Choosing and placing the bottom-side inductors:**
- Pick shielded inductors whose solder terminals stick out past the body (visible end caps or L-shaped leads), not molded types with pads hidden underneath, so an iron can reach them
- Keep them low-profile (aim ≤ ~3 mm tall) so they clear the cells, insulation and potting
- Connect each inductor to its IC's switch node and output through several vias (e.g. 4–6 per pad for the 3 A TPS62933s). Keep the switch-node copper on the bottom just big enough for the pads, to limit noise facing the cells
- The input/output capacitors stay on top at the IC pins; only the inductor moves to the bottom
- Inductor pads tied to power copper soak up heat: use a decent iron with a wide tip (or warm the board on a hot plate first) so the joints wet properly

**Things to get right on the bottom side:**
- Use 0805 for bottom-side resistors where you can — much easier to hand-solder than 0603 — including the 0.1% ones (0.1% resistors are readily available in 0805)
- Keep bottom parts low-profile so they clear the cell tops and nickel strip with room for potting and insulation
- Put an insulating layer (fish paper or Kapton) between the board's bottom side and the cell tops / nickel strip, in addition to the potting, so a shifted part can never touch a cell terminal
- The cells warm up too at high load (~4–6 W at 100 W out), so the bottom side isn't cold, just much cooler than the power stages
- Route the heat from the top-side power stages into the plate, not down into the cells: thermal vias under the FET/IC pads go to internal copper and the top-side gap pad
- Keep top-side parts and their copper clear of any bottom-side pad you'll heat with an iron, so hand-soldering the bottom doesn't reflow something on top
- Since JLC only assembles one side, this stays on cheaper single-sided assembly
- If the floorplan runs out of room: move a few more passives to the bottom first; then, if needed, the two BQ25756 inductors (low-DCR parts with exposed terminations, and recheck cell temperatures in the thermal test). Never move ICs to the bottom

## Charging plan
**Control:** the BQ40Z50-R2 is the authority (it knows cell voltages, temperature and SOC). The STM32WB reads its requested charge voltage/current and SOC and sets the charging BQ25756(s) over I2C. Each BQ25756's own TS input and safety timers are hardware backups if firmware hangs.

**Stages (4S EVE 58E, 1C = 5.6 A):**
| Stage | When | Current | Notes |
|---|---|---|---|
| Precharge | any cell < ~3.0 V | ~0.56 A (C/10) | until all cells recover above ~3.0 V |
| Normal | default, all SOC | 2.8 A (0.5C) | |
| Fast (app option, off by default) | SOC 20–80% | 5.6 A (1C) | only if charger(s), temperature and heat allow; otherwise 0.5C or whatever the input allows |
| Constant voltage | pack reaches 16.8 V (4.20 V/cell) | tapers | only reached when max SOC is 100% |
| Stop | SOC reaches the max SOC (default 95%), or current < ~0.11 A (0.02C) at 100% | 0 | |
| Recharge | pack drops a few percent below the stop point | restart | avoids constant top-up while plugged in |

**Max SOC limit (set from the iPhone app):**
- Choices like 60/70/80/90/95/100%, **default 95%**, stored in STM32WB flash so the pack obeys it with no phone around.
- When the limit is below 100%, charging stops when the gauge's SOC reaches it. If the limit is below 80%, the fast window simply ends at the limit.
- A lower limit also lowers the pass-through "full" point: the charging BQ25756 holds the pack at the limit and supplies the output load instead of charging further.
- The gauge balances cells near the top of charge, so a pack that rarely reaches 100% can drift out of balance. Plan a "charge to 100% once" button in the app, and an automatic full charge every ~10–20 cycles or month, so balancing and the gauge's capacity learning stay healthy. At 95% this matters less than at 80%, but keep it.
- Optional "trip mode" shortcut in the app: set 100% for the night before a trip, then fall back to the everyday limit afterward.

**Dual-port charging (both ports sinking):**
- Each BQ25756 regulates its own port; each is input-limited by its own source (its PD contract, or MPPT for a panel).
- Firmware splits the target cell current between the two: set each charger's current to what its source can supply, capped so the total matches the stage target (0.5C, or 1C in fast mode). The gauge's net-current reading closes the loop.
- In constant voltage near the top, only one charger regulates 16.8 V; the other is set a little lower (or held at a fixed current) so the two don't fight.
- With both ports charging there's no free port for an output device, so pass-through doesn't apply. If a device is plugged into one port while both were charging, that port switches to output per the pass-through rules.
- Two panels in sun is the main case: each gets its own MPPT, so they don't drag each other down the way panels wired together can.

**Power needed for 1C:** 5.6 A into the cells is ~80–94 W across the 14–16.8 V range, ~90–100 W from the charger(s) after losses. Needs a 100 W charger and a 5 A e-marked cable, or two chargers sharing it. With smaller chargers the rate is simply input-limited: 65 W ≈ 3.8–4 A, 45 W ≈ 2.7 A.

**Estimated charge time from empty:** at 0.5C, ~2.5 h to 100% and ~1.7 h to 80% with a ≥ 50 W charger. With fast mode and 100 W: ~1.5–1.7 h to 100%, about an hour to 80%. 30 W ≈ 3.5 h; 20 W ≈ 5 h.

**Solar (Dark Energy 15 W panel):**
- Expect well under 15 W in practice — roughly 8–12 W into the cells in good sun after panel and converter losses — so ~7–10 hours of strong sun for a full charge, about an hour of good sun per ~10% SOC. A second panel on the other port roughly doubles that.
- Many small panels output 5 V only (no PD) through their own regulator. The pack must accept plain 5 V USB-C power (no PD contract) as a sink, read the panel's advertised USB-C current, and boost 5 V up to the pack with the BQ25756.
- Use the BQ25756's input-voltage regulation (VINDPM) and MPPT so the pack never pulls the panel's voltage down far enough to make it reset. Panels with a built-in regulator often drop out and restart when overloaded or shaded; the pack must back off and recover gracefully, not stop charging.
- Detect a solar-like source (5 V-only / low and fluctuating input) and switch to solar behavior automatically.
- Confirm the panel's actual USB-C output (voltage, current, PD or not) before writing the solar code.

**Temperature rules:**
- No charging below 0 °C or above 45 °C (ambient), per EVE. A panel sitting in sun can heat the pack: keep the pack in shade with only the panel in the sun.
- JEITA via the gauge: reduced current near the cold edge, reduced voltage near the hot edge.
- 1C only when the cell thermistor is in a comfortable band (e.g. ~15–35 °C) and no board sensor is near its throttle point; otherwise drop to 0.5C.
- Board thermal throttle applies during charging: charge current is cut before anything else.

**Input handling:**
- Request the highest PD option the charger offers, up to what the current stage needs.
- Cap input current at the negotiated contract (or the USB-C Rp current for non-PD sources); back off if the input voltage sags (VINDPM), so weak or cheap chargers don't collapse.

**Pass-through:** the charge setpoint is raised by the output load so the cells still get their target current, within the input contract and the stage limits.

## iPhone app
**Plan:** a custom iOS app (Swift / SwiftUI + Apple's CoreBluetooth framework) talking to the STM32WB over Bluetooth LE. The pack must work fully without the app; the app only reads status and changes stored settings.

**What it shows (read / live notifications):**
- SOC %, remaining Wh, time to empty / time to full
- Pack voltage, each cell voltage, current in/out, power per port
- Charge stage and any limiting reason (charger too small, too cold, too hot, max SOC reached, solar limited)
- Port states: attached, sourcing/sinking, negotiated voltage and current, solar detected
- All temperatures, throttle state, and which sensors are working or broken
- Cell health from the gauge: full-charge capacity, cycle count, state of health

**What it sets (writes):**
- Max SOC limit (60–100%, default 95%), plus "charge to 100% once" and trip mode
- Fast charge on/off (default off)
- Later: anything else that's safe to tune (e.g. USB2 minimum), never the hard safety limits

**Bluetooth design:**
- Use the standard Battery Service (0x180F) for the basic SOC %, so iOS and other tools can show it, plus one custom service for everything else
- Version the custom service from the start (a protocol version characteristic) so firmware and app can change independently
- Require pairing/bonding for any write, so a stranger nearby can't change your settings; reads can be open or bonded-only
- Validate every written value in firmware (range checks, ignore nonsense), and store settings in flash with a checksum
- Keep the radio's duty cycle low: advertise slowly when idle, notify faster only while the app is connected, to protect the ~150 µA idle budget
- Consider over-the-air firmware updates (the STM32WB supports them) so the potted pack can still get firmware fixes

**Getting the app on your phone:** a free Apple ID lets Xcode install the app on your own iPhone, but it expires after about 7 days and needs reinstalling. The paid Apple Developer Program (about $99/year) removes that and adds TestFlight for sharing with others.

## Open decisions
- [ ] **Confirm "1A for 20–80%" means 1C (5.6 A) fast charging in the 20–80% window.** If it really means 1 A, that's slower than the 0.5C default and the plan needs changing

## To order
- [x] EV2400-compatible clone adapter (Amazon) — ordered 2026-10-10
- [ ] 4x EVE INR21700-58E bare flat-top, same order/batch (18650batterystore.com — confirm domain)
- [ ] kWeld complete kit + kCap (keenlab)
- [ ] 6V/12V charger to fill the kCap
- [ ] 0.15 mm pure nickel strip
- [ ] STM32WB1MMC dev board
- [ ] ST-LINK V3 (or V2) for SWD programming, plus a 5-pin pogo probe for the SWD pads
- [ ] A few spring-loaded pogo pins (e.g. P75-series) to build a small hand-held probe for the production pads
- [ ] Thermal gap pad sized to cover the power-stage FETs and BQ25756 inductors (and the heatsink NTC)
- [ ] Fish paper or Kapton sheet to insulate the PCB's bottom side from the cell tops and nickel strip
- [ ] Bottom-side hand-solder parts (three small-buck inductors, shunt, 0805 resistors, any 1206 bulk caps) — order from LCSC alongside the JLC assembly so they arrive together
- [ ] For testing fast charge: a 100 W USB-C PD charger and a 5 A e-marked cable
- [ ] A USB-C power meter (inline tester) to check what the Dark Energy panel actually outputs
- [ ] Decide on the Apple Developer Program (~$99/year) vs free 7-day installs

## Gauge adapter checks (when it arrives)
- [ ] Install TI BQStudio on a Windows PC and plug the adapter in
- [ ] Confirm BQStudio recognizes it as an EV2400 (and any firmware/driver prompt completes) — do this inside the Amazon return window
- [ ] Confirm it connects over SMBus (clock, data, ground only; the pack powers the gauge, not the adapter)
- [ ] Before writing anything to a gauge, read and save its full data flash as a backup
- [ ] Keep the USB connection stable during writes (no hubs or loose cables); a dropout mid-write can corrupt the gauge

## Dev board (replaces the gauge-only training board, 2026-10-11)
A roomy prototype of the whole production circuit, no space limits, for gauge training, firmware/app bring-up and current measurement.
- [ ] Same circuit and parts as production: BQ40Z50-R2 gauge (same shunt, cell-tap filters, thermistor, protection FETs), STM32WB1MMC module, TPS62177 3.3 V rail, and **both** USB port chains (TPS25751 + EEPROM + BQ25756 + TPS62933 + TVS, ×2), decided 2026-10-11 to test both PD controllers + gauge sharing the STM32WB I2C bus, pass-through, dual-port charging and USB1/USB2 power sharing. Second port adds roughly $35–45 in parts per board and no new JLC part setup fees (same part numbers). Each charger power stage is a straight copy of the production layout so switching/thermal results carry over (decided 2026-10-11); everything else roomy
- [ ] Real headers instead of pogo pads: SWD (ST-LINK), UART debug, EV2400 SMBus (SMBC, SMBD, GND)
- [ ] 0 Ω links / jumpers between blocks so each can be powered and debugged alone; test points on every rail and I2C line
- [ ] **Split power path for sleep-current measurement:** after the gauge shunt and protection FETs, the pack bus splits:
  - High-current branch, direct (no shunt): the BQ25756 power stages and the TPS62933 5 V converters
  - Low-current branch through a **10 Ω measurement resistor**: TPS62177 (→ STM32WB and both TPS25751s). The gauge stays on its own BAT feed from the cells (TI requires it so the gauge survives with its FETs off); optional DNP 10 Ω + third INA190 on that feed. Normal draw is a few mA (~80 mV drop at 8 mA), so no bypass switch is needed
  - Both branches sit after the gauge shunt, so gauge readings and protection are unchanged
  - High-current blocks (BQ25756s, TPS62933s) get **no** measurement shunt or bypass (decided 2026-10-11). Their sleep draw (~17 µA per BQ25756, a few µA per TPS62933 off) comes from datasheets, or from total pack current minus the 10 Ω branch measured with a bench meter
- [ ] **Scope outputs:** two TI INA190 current-sense amps on the 10 Ω (high-side, very low input bias): gain 500 → 5 mV/µA, ~1 mA full scale (sleep detail); gain 25 → 0.25 V/mA, ~20 mA full scale (Bluetooth bursts). BNC or SMA connectors plus test points. Amps powered by an on-board TI TPS70950 5 V LDO (C96028) fed from the pack bus outside the 10 Ω, so their current isn't measured and no external supply is needed. INA190A5IDDFR (gain 500) + INA190A1IDDFR (gain 25, C1852068), SMA outputs, enable jumper. Note the offset (~±1.5 µA) with the load link open. Clip the scope ground only to board ground. Check INA190 stock at JLC
- [ ] **Cells:** four MYOUNG BH-21700-B1BJ001 21700 spring holders (JLC C20606791, JLC-assembled; backup Keystone 1121), clearly marked, in series, plus a fuse; check each cell voltage before closing the fuse since open holders accept a reversed cell; good for a few amps only, so 100 W and thermal tests use the welded pack. Wire the gauge's cell-voltage taps to the cell end of each contact (Kelvin) so spring resistance isn't learned as cell impedance
- [ ] Pack connector beside the holders so the final learning cycle runs on the real welded pack (learned capacity belongs to those cells)
- [ ] 4 layers, ~100 × 80 mm
- [ ] Draft it in ProtoFlow first, before the production board

## Gauge training (BQ40Z50-R2, on the dev board)
Follow TI app note SLUA903, "Achieving the Successful Learning Cycle."
- [ ] Weld the real 4S pack first, then connect it to the training board with temporary leads, so the learned capacity belongs to the actual cells
- [ ] Calibrate voltage, current (sense resistor) and temperature in BQStudio
- [ ] Look for the EVE 58E in BQStudio's chemistry list; if it's missing, log a slow (~C/10) discharge with rests and submit it to TI's GPCCHEM tool for a chemistry ID
- [ ] Configure data flash: 4 cells, 4.20 V/cell, design capacity 5600 mAh, all four cell Qmax = 5600 mAh, terminate voltage ~3.0 V/cell (12.0 V pack), charge temp 0–45 °C, sense resistor value, protection thresholds
- [ ] Enable gauging and check Update Status starts at 0x04
- [ ] Run the learning cycle: discharge to empty → rest ~5 h → full charge → rest ~2 h → discharge at C/5–C/10 (~0.6–1.1 A) to terminate voltage → rest; repeat until Update Status shows the completed value in SLUA903. Only rest at full or empty.
- [ ] Export the learned data flash file and commit it to the GitHub repo as the golden image

## Production board gauge setup (before potting)
- [ ] Hand-solder the bottom-side parts (inductors first, they need the most heat), then inspect every joint (and check nothing on the top side reflowed or shifted)
- [ ] Power each converter up and check its output before connecting loads: 3.3 V rail first, then each 5 V buck — a bad bottom-side inductor joint shows up here
- [ ] Load the golden image onto the production BQ40Z50-R2 through the pogo pads
- [ ] Calibrate this board: current gain is the priority (the 1% shunt is the largest error source; calibration takes it from ±1% to the meter's accuracy), then current offset, voltage and temperature (~10 min with a bench supply, multimeter and known load). Temperature matters most near the 0 °C charge cutoff, since the NTC's own tolerance dominates over the 0.1% bias resistor
- [ ] Confirm the gauge reads sensible SOC, voltage, current and temperature over SMBus, both in BQStudio and from the STM32WB
- [ ] Check every board NTC reads room temperature (within a degree or two of each other) before potting. A sensor that's already dead before potting can't be fixed afterward, so all 4 must pass here
- [ ] Confirm the iPhone app connects, bonds, reads everything and can change the max SOC and fast-charge setting before potting
- [ ] Save a final data flash backup of the production gauge to the repo
- [ ] Only then pot the PCB. Potting covers the pads, so any later reconfiguration has to go through the STM32WB

## Design work
- [ ] **Floorplan first:** place every part's real footprint on a ~44 × 44 mm outline, split top/bottom per the PCB layout section (all ICs, pin-critical parts and the BQ25756 inductors on top; only hand-solderable parts, including the three small-buck inductors, on the bottom), using TI's EVM layouts for the BQ25756 and TPS25751 as the starting point. Confirm it fits on one board before committing to the schematic details
- [ ] Choose the layer count (4 layers likely: power planes for the 10 A path and thermal vias, signals on outer layers) and the board thickness, then pick the matching Shou Han connector variant
- [ ] Add BQ40Z50-R2 to the schematic: cell taps, sense resistor, thermistor, protection FETs (AGM404AP1), SMBus to STM32WB. Network values (100 Ω + 0.1 µF VC filters, 30 V diode + 100 Ω BAT feed, 2.2 µF PBI, 100 Ω + 0.1 µF sense filter, 5.1 kΩ gate resistors + 10 MΩ gate-source, unused pins) are in the dev board circuit description on the `dev-board` branch; production uses the same. BTP_INT optional to an STM32WB pin
- [ ] Add three bottom-side pogo pads for SMBC, SMBD and GND: ~1.5 mm round exposed copper, no solder mask, 2.54 mm pitch in a straight line, silkscreen labels, no connector
- [ ] Size the main power path for 100 W out: ~9 A pack current at the 12 V low end, ~10 A with margin. Check the AGM404AP1 protection FETs (Rds(on) heat at 10 A), the shunt and the main copper against that
- [x] Pick the current shunt: Yageo PA2512FKE7W0R001E, 1 mΩ 1% 50 ppm 2512 (C326570). Kelvin-route the sense lines to the gauge
- [ ] Set the BQ40Z50-R2 discharge overcurrent threshold just above the 100 W draw (~10–11 A), well under the cells' 16.8 A maximum; set charge overcurrent just above 1C (~6–6.5 A)
- [ ] Place the gauge shunt between the cells and the shared bus that both BQ25756s connect to, so the gauge measures the pack's net current during pass-through and dual-port charging
- [ ] Size the nickel strip for ~10 A between cells (0.15 mm pure nickel is marginal at that current; consider a double layer or wider strip)
- [ ] Use 0.1% resistors for both BQ25756 charge-voltage feedback dividers (set the 16.8 V charge limit) and all other dividers and bias resistors
- [ ] Configure BQ40Z50-R2 limits from the EVE datasheet: 4.20 V charge, charge inhibit below 0 °C and above 45 °C, discharge -20 to 60 °C; JEITA ranges for reduced current (cold) and reduced voltage (hot)
- [ ] Place the thermistor at mid-cell (30–34 mm up from the bottom)
- [ ] Board temperature sensors: 10 kΩ NTCs (1%, B ≈ 3380–3435, 0603, JLC Basic parts, top side) at four spots, with 0.1% bias resistors (0805, can go on the bottom) into STM32WB ADC inputs:
  - one beside each BQ25756's switching FETs / inductor (x2, hottest board parts)
  - one between the two USB-C connectors, on their VBUS/GND copper (connector rated only to 80 °C)
  - one directly under the aluminum heatsink plate, on a copper pad the gap pad presses against, so it reads close to the plate temperature
- [ ] Count the free ADC pins on the STM32WB1MMC against the 4 board NTCs. If it's short, use an analog mux, combine the two connector/plate spots, or use a small I2C digital sensor on the existing bus
- [ ] Power the NTC dividers from a GPIO (or switched 3.3 V) so they draw nothing in sleep; only sample while a port is active or charging, to stay inside the ~150 µA idle budget
- [ ] Wire the BQ25756 TS inputs per TI's EVM so each charger also has its own hardware temperature cutoff, independent of firmware. This also covers a power stage whose board NTC has died
- [ ] Confirm each BQ25756 can charge the 4S pack from a plain 5 V input (boost from 5 V up to 16.8 V) at useful current, and that each TPS25751 sinks 5 V from a non-PD source (Rp current advertisement only)
- [x] Sleep budget totalled: ~150 µA idle (see 2026-10-11 changes). Measure the real number on the first board, especially BLE advertising and the BQ25756s at 16 V
- [ ] Set the BQ40Z50-R2 low-voltage shutdown so a stored, empty pack switches itself off before over-discharge
- [ ] Write STM32WB SMBus code to read gauge data (SOC, voltage, current, temp, Update Status) and log it over Bluetooth; plan for it to be the only way into the gauge after potting. Keep the MCU asleep between radio events
- [ ] Charging firmware: run the stage table in the Charging plan — read SOC, cell voltages and temperature from the gauge, pick the stage, and write charge current/voltage to the charging BQ25756(s). Re-evaluate every few seconds and on any gauge alarm
- [ ] Charging firmware: fast mode only when enabled in the app; add hysteresis around the 20% and 80% switch points (e.g. ±2%) so the rate doesn't flip back and forth
- [ ] Charging firmware: only enter 1C when the input contract(s) can supply it, the cell thermistor is in the comfortable band, and no board sensor is near its throttle point; fall back to 0.5C otherwise
- [ ] Charging firmware: negotiate the input PD contract for the current stage (up to 20 V × 5 A for 1C), set BQ25756 input current limit to the contract and enable VINDPM so a weak charger isn't collapsed
- [ ] Charging firmware (dual-port): when both ports are sinking, split the target cell current between the two chargers based on what each source can supply, close the loop on the gauge's net current, and let only one charger regulate 16.8 V in constant voltage
- [ ] Charging firmware (solar): detect a solar-like source (5 V-only / non-PD, low or fluctuating power), enable MPPT and VINDPM, ride through the panel dropping out and restarting in shade, and report "solar limited" to the app
- [ ] Charging firmware: keep the BQ25756 safety timers on as a backup
- [ ] Charging firmware: stop at the stored max SOC (default 95%); after stopping, only restart once the pack drops a few percent below that point
- [ ] Charging firmware: store max SOC, fast-charge setting and other settings in STM32WB flash with a checksum and safe defaults (95%, fast off); a corrupted or out-of-range setting falls back to the default
- [ ] Charging firmware: "charge to 100% once" and the periodic full-charge balancing cycle (every ~10–20 cycles or month) when the max SOC is below 100%
- [ ] Charging firmware: report stage, charge current, input power per port, estimated time to full and any limiting reason (charger too small, too cold, too hot, max SOC reached, solar limited) over Bluetooth
- [ ] Power-sharing firmware (USB1 priority, 100 W total): USB1 alone advertises up to 20 V × 5 A (100 W, only with an e-marked 5 A cable). When USB2 attaches, USB1 drops to at most 80 W and USB2 advertises at least 20 W (5 V × 2.5 A, 9 V × 2.22 A, and higher-voltage PDOs at 20 W), plus any budget USB1 isn't using
- [ ] Power-sharing firmware: if USB2 attaches while USB1 holds a contract above 80 W, send USB1 new source capabilities capped at 80 W first, wait for its device to renegotiate, then enable USB2's 20 W. If USB1 attaches or asks for more while USB2 holds more than 20 W, lower USB2 first. Never let the two contracts total more than 100 W, even briefly
- [ ] Power-sharing firmware: when either port detaches or drops its request, give the freed budget back (USB1 first)
- [ ] Pass-through firmware: when one port is sinking from a charger, set the other port to source-only (not dual-role) so a phone or laptop plugged into it gets power instead of trying to charge the pack. Exception: if the other port also has a charger or panel, both charge (dual-port charging)
- [ ] Pass-through firmware: hold the cells' target charge rate by closing the loop on the gauge's net current. The charging BQ25756 only sees its own output current, so raise its setpoint by the output load (up to what the input contract allows)
- [ ] Pass-through firmware: at full charge or at the max SOC limit, keep the charging BQ25756 holding the pack there and supplying the output load instead of terminating; let the gauge decide when the cells are full
- [ ] Pass-through firmware: request the input PD contract to cover battery charge plus output load, and reduce output power if the charger can't supply enough
- [ ] Pass-through firmware: detect a cable looped between the pack's own two ports (both ports attached, one sinking and one sourcing at matching power, or our own PD identity on the far end) and refuse to transfer power
- [ ] Thermal throttle firmware: ~12–14 W of heat at 100 W out (converters + cell I²R) inside a sealed, potted cap, more during pass-through and ~8–9 W during 1C charging. Sample all working sensors — cell thermistor (via the gauge), both power-stage NTCs, the connector NTC and the heatsink NTC. Each gets its own throttle point; when any working one crosses it, re-advertise every active output port at 20 W (5 V × 2.5 A, 9 V × 2.22 A, 15 V × 1.33 A, 20 V × 1 A), ignoring USB1 priority, and drop charging to 0.5C or less. Lower contracts before anything else so the total never spikes
- [ ] Thermal throttle firmware: use the heatsink NTC as the touch-temperature guard, since the plate is the outside surface you hold. Set its throttle point so the plate stays comfortable to hold (roughly mid-40s °C as a starting point; confirm in testing)
- [ ] Thermal throttle firmware: hold 20 W until every working sensor falls a set margin below its throttle point (hysteresis, e.g. 5–10 °C), then restore the normal 100 W / USB1-priority sharing. Keep it from bouncing on and off
- [ ] Thermal throttle firmware: above a hard limit (cells near 60 °C discharging / 45 °C charging, connector near 80 °C, power stage at its limit) turn the outputs and charging off entirely, with the BQ25756 TS inputs and the BQ40Z50-R2's own over-temperature protection as hardware backups
- [ ] Sensor-fault firmware: mark an NTC as broken if it reads open or shorted (ADC near the rails), sits outside a plausible range (e.g. below -40 °C or above 150 °C), jumps faster than heat can physically move, or disagrees wildly with the others while the pack is idle. Ignore a broken sensor rather than treating it as hot
- [ ] Sensor-fault firmware: keep full power while at least 3 of the 4 board NTCs work. With 2 or fewer working, fall back to the 20 W limit (and 0.5C charging), since too much of the board is unwatched
- [ ] Sensor-fault firmware: when a sensor drops out, don't let its last reading linger. Re-check broken sensors periodically and bring one back only after several good readings in a row
- [ ] Sensor-fault firmware: report which sensors are working or broken over Bluetooth, so a dead sensor gets noticed even though the pack keeps running normally
- [ ] Thermal throttle firmware: report all temperatures and the throttle state over Bluetooth so it's clear why a laptop is charging slowly; at 20 W many laptops will charge slowly or only slow their drain
- [ ] Thermal validation: on the first built pack, run 100 W into a load from full to empty and log every sensor over Bluetooth; also check the plate's outside surface with a thermometer to see how it tracks the heatsink NTC. Set the throttle points and hysteresis from that data
- [ ] Thermal validation: repeat the 100 W run with one sensor disabled in firmware at a time, to confirm the remaining 3 still catch overheating before anything exceeds its rating
- [ ] Charging validation: charge from empty with a 100 W charger and 5 A cable in fast mode, logging stage, SOC, cell voltages and all temperatures; confirm the 1C window holds without throttling and the cells stay balanced. Repeat in normal mode, with 65 W and 30 W chargers, with max SOC at 95% and 80%, and with two chargers on both ports at once
- [ ] Solar validation: measure the Dark Energy panel's real USB-C output with an inline meter (voltage, current, PD or not), then charge the pack from it in full sun and in passing clouds/shade; confirm it charges steadily, recovers from panel dropouts, and that two panels on both ports add up
- [ ] 3.3 V rail: TPS62177 and its input/output caps on the top side, inductor on the bottom directly under it (per its datasheet's inductor value, tight switching loop, short via path); wire its sleep/SNOOZE pin to an STM32WB GPIO; size its load for the STM32WB (including radio peaks) plus two TPS25751s (up to ~6 mA active each)
- [ ] Per-port TPS62933 (x2): IC and caps on top, inductor on the bottom directly under it; feeds that port's TPS25751 PP5V with at least 10 µF placed directly at the PP5V pin; enable when the port needs 5 V or VCONN. Lay out both from one shared design (set frequency with RT, pick an inductor rated well above 3 A with exposed terminations and ≤ ~3 mm height, output caps for 5 V / 3 A)
- [ ] Set each TPS25751's PP5V current limit so the 5 V output plus VCONN (up to ~315 mA) stays within the TPS62933's 3 A (the 2.3–2.7 A ILIM setting, advertising 5 V at 2.5 A)
- [ ] Confirm each TPS25751 + BQ25756 pair is configured for a 4S profile (16.8 V charge voltage) with charge current up to 1C (5.6 A); check TI's TPS25751EVM user guide (SLVUCP9) for the BQ25756 wiring
- [ ] **Charger capacitors:** confirm the 1210 bank's effective capacitance at 20 V (USB side) and 16.8 V (battery side) with Taiyo Yuden's DC-bias data, and confirm the BQ25756's ≥ 80 µF requirement in the datasheet's recommended operating conditions; add or remove 1210s to match
- [ ] Lay out the bottom-side cap fields with a dense via array to the top-side power stage (bulk caps only; the 2 + 2 high-frequency caps stay on top at the FETs)
- [ ] Check the Bourns SRP5030T and SRN4018TA drawings: confirm the terminations are reachable with an iron, and size the pads with extensions for hand soldering
- [x] BQ25756 ILIM_HIZ = 3.65 kΩ (~5.5 A) and ICHG = 5.11 kΩ (~9.8 A); with 5 mΩ RAC, KILIM = 20 A·kΩ. Still check how the IAC_DPM register step scales with 5 mΩ
- [x] BQ25756 TS: own NTC per charger, RT1 1.74k / RT2 5.11k (-20 to 95 °C window)
- [x] FB divider: FBG goes high-impedance when the input is outside the ACUV/ACOV window, so the 100k/10k divider draws nothing with no input. Check FBG in reverse (sourcing) mode
- [ ] Get the full TPS25751 Technical Reference Manual (SLVUCR8) PDF into the project (download blocked here) and confirm: I2Cr/I2Cw DATA1 format and what the configuration tool makes the TPS25751 write to the BQ25756
- [ ] Set up the TPS25751 + BQ25756 configuration in TI's Application Customization Tool (web) for a 4S, bidirectional, 5–20 V / 5 A port; export the patch for the EEPROM
- [ ] Confirm the BQ25756 I2C address (expected 0x6B) for I2Cw
- [x] TPS25751 straps: port 1 ADCIN1=LDO_3V3, ADCIN2=GND (0x20, SafeMode); port 2 both GND (0x21, SafeMode); EEPROM per port (M24256-BFMC6TG)
- [x] EEPROM programming plan: in-system via the STM32WB (PBMs/PBMc boot load, then FLrd/FLad/FLwd/FLvy/GAID), see 2026-10-11 changes
- [x] Read SLVAFL1 and SLVAFV8A in full; command formats, memory map, boot/recovery flow written up in `claude/tps25751-eeprom-programming.md`
- [x] TPS25751 IRQs: USB1 → PA0, USB2 → PA2, internal pull-ups (see pin map)
- [ ] Confirm the STM32WB1MMC pin map in STM32CubeMX (I2C1 on PB6/PB7, ADC channels on PA1/PA3/PA4/PA5, SWD on PA13/PA14) and check the module's layout guide for any pins reserved for the radio
- [ ] In TI's Application Customization Tool, export both the Full Flash binary and the Low Region binary (C array) for the firmware
- [ ] Add 5 SWD pogo pads (SWDIO, SWCLK, NRST, 3V3, GND) on the bottom side and to the floorplan
- [ ] Firmware: store the patch bundle with a version number; on boot compare each TPS25751's running version and update its EEPROM only when newer
- [ ] Set both BQ25756s to 600 kHz (R_FSW = 40 kΩ, 0.1%); confirm 2.2 µH against the inductor-selection section of the BQ25756 datasheet (ripple, current-sense and compensation assumptions)
- [ ] Compute FET switching and gate-drive loss at 600 kHz with the IAUC45N04S6L063H, including its resistance at 4.5–5 V gate drive
- [ ] Thermal/bench test the XAL7030-222 at 100 W from a low pack (~12–13 V): check inductor temperature and peak current against the BQ25756 current limit
- [ ] Size each BQ25756 power stage (FETs chosen: IAUC45N04S6L063H; inductor, sense resistors) for 20 V × 5 A on the USB side and ~6 A on the battery side, so either port can carry the full 100 W out or a 1C charge in; pick a low-DCR inductor to keep its heat down
- [ ] Confirm JLC's own stock for all Extended parts in the cart when setting up the assembly order (LCSC stock was healthy on 2026-10-10)
- [x] USB-C connector drawing checked: mid-mount, needs the 0.8 mm board (C55629727), 10.2 × 4.7 mm notch
- [ ] Confirm JLC offers 2 oz outer copper on a 0.8 mm 4-layer board (else 1 oz outer with pours on more layers)
- [ ] Top cap: port openings sized to seal on the connectors' 10.25 × 4.45 mm silicone-ringed flange; set the port-side board edge ~2.9 mm behind the cap's outer face and shrink the board to suit
- [ ] USB-C connector: tie every VBUS and GND pad to generous copper so the board pulls heat away at 5 A (the 5 A rating usually assumes all pins connected and a stated temperature rise)
- [ ] USB-C connector: keep it away from the hottest converter parts (rated only to 80 °C) and design the cap wall to take plug-insertion force, not the solder joints. Seal the connector to the cap; the IP68 rating covers the connector, not the cap joint
- [ ] USB-C connector: the 20 V / 5 A rating exactly matches the port spec with no margin, and it rules out 28 V EPR later
- [ ] Heatsink plate: draw it in KiCad as a one-layer board with only the outline and non-plated holes, choose aluminum base material at JLC, and notch it clear of the STM32WB antenna (keep that corner potting or plastic only). Check JLC's current thickness and dielectric options at order time
- [ ] Heatsink plate: make the gap pad cover the heatsink NTC's copper pad as well as the FETs and BQ25756 inductors, so that NTC actually sees the plate
- [ ] Label the ports "USB1" (priority) and "USB2" on the outside, e.g. in the aluminum plate's silkscreen or molded into the top cap next to each opening
- [ ] Draw the four FR4 wall panels with finger joints and dog-bone reliefs, sized for the ~44.5–45 mm inner cavity; order them as blank 0.8 mm boards
- [ ] Model the two printed end caps with the sealant groove, cell pockets (bottom) and PCB/port mounts (top), using the corrected cavity size; top cap needs side-wall openings for the two right-angle USB-C ports, a seat for the aluminum plate, and enough depth for bottom-side parts (inductors are the tallest) plus the insulation layer above the cells
- [ ] Place the USB-C ports and a Bluetooth antenna window clear of cells, nickel and the aluminum plate

## Bluetooth firmware + iPhone app work
- [ ] Define the BLE GATT layout: standard Battery Service (0x180F) for SOC %, plus a custom service with a protocol-version characteristic, a status characteristic (notify), a temperatures/sensors characteristic (notify), a ports characteristic (notify) and a settings characteristic (read/write: max SOC, fast charge, charge-to-100%-once, trip mode)
- [ ] Write the GATT layout down as a shared spec in the repo, so firmware and app agree on byte layouts and units
- [ ] STM32WB firmware: require pairing/bonding for writes; range-check every write; persist settings to flash
- [ ] STM32WB firmware: slow advertising when idle, faster notifications only while connected; measure the average current against the sleep budget
- [ ] STM32WB firmware: port ST's BLE_Ota loader (check it supports the WB15/WB1MMC), add CRC check + watchdog-failure fallback into update mode, and bonded-only update entry from the app
- [ ] Start the app on the STM32WB dev board before the pack exists: scan, connect, bond, read a fake status, write a max SOC value
- [ ] iOS app (SwiftUI + CoreBluetooth): dashboard (SOC, Wh, time to empty/full, power per port, solar input), detail screens (cells, temperatures, sensor health, charge stage and limiting reason), settings (max SOC slider defaulting to 95%, fast-charge toggle defaulting off, charge-to-100%-once, trip mode)
- [ ] iOS app: reconnect automatically to the bonded pack, handle the pack going out of range, and show the last known values with a timestamp
- [ ] iOS app: show a clear warning when the pack reports throttling, a broken sensor or a gauge fault

## ProtoFlow work
ProtoFlow's free tier covers the whole flow: AI schematic drafting from a plain-English description, real parts from JLCPCB/LCSC/DigiKey/Mouser, ERC, PCB layout, the ProtoRoute autorouter, DRC, SPICE simulation, and Gerber/drill/BOM/pick-and-place export. It reads and writes KiCad projects.
- [ ] Install ProtoFlow (desktop, free tier, no card needed)
- [ ] Draft the training board first (gauge circuit only)
- [ ] Describe the production circuit in plain English and draft the schematic: 4S pack, BQ40Z50-R2, AGM404AP1 FETs, two identical PD ports (TPS25751 + BQ25756 + TPS62933 each, Shou Han IP68 USB-C) on a shared pack bus, TPS62177 3.3 V buck, STM32WB1MMC, and four board NTCs (each power stage, connectors, under the heatsink plate) into the STM32WB ADC
- [ ] Check every generated symbol and footprint against its datasheet (pin numbers, pad sizes); run ERC
- [ ] Pick parts JLC actually carries where possible. 0.1% resistors are usually JLC "extended" parts with a per-part setup fee, so consolidate onto as few unique values as possible
- [ ] Set up the board: layer count, outline, JLC design rules, top-side-only assembly, before placing anything
- [ ] Place by function and side per the PCB layout section: all ICs, pin-critical parts and the BQ25756 inductors on top; the three small-buck inductors directly under their ICs on the bottom; only hand-solderable 0805+/2512 parts and pads elsewhere on the bottom; decoupling caps at IC pins, connectors at the edge, NTCs right at the spots they're meant to watch, STM32WB module under the plate's antenna notch
- [ ] Mark bottom-side parts as "do not populate" in the JLC BOM/pick-and-place, and keep a separate hand-solder BOM for them
- [ ] Hand-route the high-current path (cells → FETs → chargers → PD ports) with wide copper first, sized for ~10 A on the pack side and 5 A per port
- [ ] Autoroute the remaining small-signal nets with ProtoRoute, then review the result
- [ ] Run DRC against JLC rules and check the 3D view, including bottom-side part heights (especially the inductors) against the cells
- [ ] Simulate the TPS62177 and TPS62933 rails in SPICE before committing, including the extra via resistance/inductance to the bottom-side inductors
- [ ] Export Gerbers, drill, BOM and pick-and-place; also export to KiCad for any final cleanup and to commit to the repo
- [ ] Watch the free-tier AI allowance; only look at a paid tier if it runs out mid-project

## Admin
- [x] GitHub push access works (repo MidwestMotorBoy/battery-bank). Dev board circuit description is on branch `dev-board` at `docs/devboard/circuit-description.md`
- [ ] The `master` README, netlists and BOM still describe the older design (BQ77915 protector, TPS25810 5 V port, TPS709 LDO, Amphenol connector); update them once the production schematic is redone
