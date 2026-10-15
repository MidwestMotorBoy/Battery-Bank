# Reviewer A: MCU sheet (mcu.kicad_sch), board-wide I2C/SMBus and IRQ_N (round 1)

**Scope:**
- U301 CC2340R5MODA, pin by pin: RF match, RSTN/SW301, SWD J301, UART J302, J303, LED, ROM bootloader, pin map.
- U302–U306 TMP1075, pin by pin and address straps.
- The shared SCL/SDA bus: CC2340, 5 × TMP1075, 2 × TPS25751 I2Ct, BQ40Z50 SMBus, J103.
- The IRQ_N wire-OR.
- State analysis of every MCU-driven net.
- Stale documentation on and about this sheet.

**Sources:**
- `datasheets/cc2340r5moda.pdf`, SWRS349A (July 2026). Rendered: fig. 6-1 p.6, fig. 9-1 p.50, fig. 9-2 p.52. Text: table 6-1 pp.6–8, table 6-18 p.11, §7.1/7.3/7.6 pp.12–13, §7.18.4 GPIO DC pp.26–27, §8.6–8.11 pp.41–43.
- `datasheets/tmp1075.pdf`, SBOS854F. Rendered: fig. 5-3/table 5-1 p.4, table 7-2 p.14. Text: §6.5 pp.6–7, §7.4 pp.19–20, table 7-5 p.21, §8.2–8.4 pp.25–27.
- `tps62177.pdf` (SLEEP pin, EC table and "Sleep Mode Operation"), `tps62933.pdf` (EN, EC table), `ao3400a.pdf`, `stm32wb15cc.pdf` (DS13258 table 15, PB6/PB7 = FT_f).
- TI CC23xx TRM SWCU193, ROM serial bootloader table 8-38 (web): https://ti.com/document-viewer/lit/html/SWCU193/GUID-93C18248-3D8F-40C6-BD16-D38F8539967E
- SimpleLink Low Power F3 SDK 8.10 user's guide, "Device Configuration (CCFG)" (web): https://dev.ti.com/tirex/content/simplelink_lowpower_f3_sdk_8_10_01_02/docs/ble5stack/ble_user_guide/html/sysconfig/device-configuration-cc23xx.html
- `nets.txt`, `parts.txt`, `erc.txt`, `DevBoard/MonolithDev.kicad_pcb` (footprint positions via pcbnew; the board is not routed yet), the sheet text in `mcu.kicad_sch` and `MonolithDev.kicad_sch`, `cc2340-pin-budget.md`, README item 40, `mcu-io-power-states.md`, `bringup-config-checklist.md`, `power-budget.md`.
- Peer answers: D (BQ40Z50 BTP, broadcasts, bus-low behaviour) and C (TPS25751 I2Ct addresses, IRQ, back-power), recorded where used.
- Scripts and renders: `scratch-a/`.

**Summary (round 1): 0 CRITICAL, 2 MAJOR, 5 MINOR, 3 CONFIG, 2 DOC, 3 NOTE.**

**After round 2 (final): 0 CRITICAL, 1 MAJOR (A-2), 6 MINOR (A-1b, A-5, A-6, A-7, A-9, A-10), 4 CONFIG (A-1, A-3, A-4, A-8), 2 DOC, 3 NOTE.**
- A-1 changed from MAJOR to CONFIG (required, blocking before first flash).
- Its hardware part is split out as A-1b, MINOR: R313 → 220k.
- See "After round 2" at the end.

---

### A-1 [MAJOR] DIO21 (3V3_SLEEP) is the CC23xx default ROM-bootloader trigger pin, active low at reset. Firmware drives it low in S2, so a reset from S2 can strand the MCU in the ROM bootloader
- **Where:** U301.15 DIO21_A10, net 3V3_SLEEP (R313 470k to 3V3, U204.8 ~SLEEP, TP307).
- **Evidence:**
  - **The default trigger pin is DIO21, verified (TI web docs).** The SDK 8.10 CCFG page lists three SysConfig choices. The standard selection is "Default FCFG bootloader", which gives serial IO configuration index 2 (UART RX/TX on DIO22/DIO20) and a pin trigger on DIO21, active low on reset.
  - **The ROM checks the trigger on every boot.** TRM SWCU193 §8.4 (table 8-35): with an invalid CCFG, or a CCFG that keeps the FCFG parameters, the ROM serial bootloader is invoked as part of every boot. It "determines whether the serial bootloader is triggered (or not) within a few microseconds".
  - **A sheet note and the pin plan rely on this pin being low.** Note 9 and the pin plan have firmware drive 3V3_SLEEP low in S2: TPS62177 sleep mode, which "costs 7 µA". `cc2340-pin-budget.md` lists DIO21 as "otherwise unused". Neither mentions the strap.
  - **The release after a reset is a slow RC, inferred.**
    - On a WDT reset (WDT runs in Standby, SWRS349A §8.6), a BOD reset or a pin reset while the pin is driven low, the pin goes hi-Z and recharges through R313.
    - The source is 470k, against the TPS62177's internal pull-down: 1.4 µA at 3.3 V, about 2.4 MΩ (tps62177 EC table ILKG_SLEEP; "a pulldown resistor internally connected").
    - That gives τ ≈ (470k ∥ 2.4M) × ~15–20 pF ≈ 6–8 µs, and ≈ 0.9 τ (about 7 µs) to reach the ~1.6 V typical input switch point.
    - That is the same order as "a few microseconds" for the ROM decision.
    - If the I/O latch from Standby stays set through the reset, the pin stays low throughout. I did not find this in SWRS349A.
  - **The steady-state high level is also marginal against spec, verified arithmetic.**
    - Divider: 3.3 V × 2.36 M / (2.36 M + 0.47 M) = 2.75 V typical.
    - With a −30 % internal resistor (inferred tolerance): 2.57 V.
    - VIH = 0.8 × VDDS = 2.64 V (SWRS349A §7.18.4 p.27).
    - So the pin only reads high by the typical switch point, not the guaranteed VIH.
  - **Consequence.** The MCU sits in the ROM bootloader waiting for a host. Pins stay hi-Z: CHG_INH is inhibited and EN_5Vx are off, so it is safe. But the pack is dead to BLE and USB-PD supervision until the next reset or power cycle. The product has no reset button.
- **Proposed fix:**
  1. **CONFIG (required).** In SysConfig → Device Configuration, either select "Any bootloader forbidden" (production), or "Default FCFG bootloader, with CCFG settings" with the pin trigger disabled or moved. A safe dev-board choice is DIO3 active high: R432's 100k holds it low, and J303 pin 1 → pin 4 forces it high through R317.
  2. Add this to `bringup-config-checklist.md` and the sheet notes (note 8 says "the CCFG backdoor pin" without naming it).
  3. Optional hardware: R313 → 220k raises the level to 3.02 V typical (2.9 V with −30 %) at 15 µA in S2. With fix 1 this is not needed.
- **Confidence:** default trigger pin and VIH arithmetic verified (TI SDK doc and datasheet). Timing race inferred.

### A-2 [MAJOR] The documented "EV2400 with 3V3 dead" procedure (R312 removed, TP308 fed) puts 3.3 V on the unpowered CC2340's SCL/SDA, over its abs max. This is a rev A7 regression: the STM32 pins were 5 V tolerant
- **Where:** R304/R305 (SMB_PU), R312 (Notes: "Remove to isolate … then feed TP308 for EV2400 work"), sheet note 10, J103, U301.9 DIO6, U301.10 DIO8. Also R301 ("MCU 3V3 link").
- **Evidence:**
  - **CC2340 abs max is exceeded when unpowered, verified.**
    - "Voltage on any digital pin: −0.3 to VDDS + 0.3, max 4.1 V" (SWRS349A §7.1 p.12).
    - With 3V3 = 0 and TP308 at 3.3 V, each line drives (3.3 − ~0.6) / 4.7k ≈ 0.6 mA into the DIO6/DIO8 clamp diodes.
    - That phantom-powers VDDS, and through R301 the whole 3V3 rail: TMP1075s, TPS25751 VIN_3V3 and so on. The MCU may half-boot.
  - **The old part was 5 V tolerant, verified.** The rev A6 STM32WB PB6/PB7 were FT_f (DS13258 table 15). So review 1 item #9's fix (R312 + TP308) was safe for the old MCU and is not safe now.
  - **The same mechanism appears if R301 is removed** (to isolate or measure the MCU) while 3V3 is up. SDA/SCL (4.7k), CHG_INH (R417/R517 47k + 1k), IRQ_N (100k) and 3V3_SLEEP (470k) all feed DIO pins from 3V3.
  - **The TMP1075s are not at risk.** "SCL, SDA, A0 and A1 lines can be pulled up to a supply higher than V+" (tmp1075 §8.2.1).
  - **The TPS25751 I2Ct pin structure is unspecified.** C confirms there is no power-off leakage spec (inferred risk only).
- **Proposed fix:**
  - **Procedure, preferred:** for gauge work with the pack FETs off, power PACK_P from J104 so that 3V3 is up. Keep R312 fitted.
  - Rewrite note 10 and the R312 Notes property. Feed TP308 only when 3V3 is present, or only with R301 removed and U301 accepted as back-powered.
  - Check whether the EV2400's SMBus port has its own pull-ups, which would back-power U301 with 3V3 dead even with R312 out.
  - Add to R301's Notes: "ammeter link: never leave open with 3V3 up."
  - **Hardware option for rev 2.0:** 1k series resistors in DIO6/DIO8 limit the clamp current to ~2.7 mA. That is still out of spec, so the procedure is the real fix.
- **Confidence:** verified (datasheet abs max and the STM32 table). The EV2400 pull-ups are unknown.

### A-3 [CONFIG] IRQ_N wire-ORs seven latched, level-type sources, but Standby only wakes on a pin edge. One source that stays asserted masks every other source and blocks wake
- **Where:** IRQ_N: U401.10 and U501.10 I2Ct_IRQ, Q103 drain (BTP), U302–U306 ALERT, R314 100k, U301.21 DIO11, TP304, TP107, J303.2.
- **Evidence:**
  - **Wake is edge-only, verified.** SWRS349A table 8-3 p.43: Standby wakes on "pin edge". There is no level wake.
  - **Every source is a latched level:**
    - **TMP1075, verified.** The defaults at power-up are CFGR 00FFh, LLIM 4B00h = 75 °C, HLIM 5000h = 80 °C (table 7-5 p.21). That is comparator mode (TM = 0) with POL = 0, active low (§7.4.4.3).
      - In comparator mode, ALERT "remains active until the temperature falls below TLOW" (§7.4.4.1).
      - U302/U303 sit on the port power-stage copper. The BQ25756 TS warm point is 74 °C and the hot stop is 94.5 °C (R415 Notes). So at 100 W the 80 °C default trip is a normal operating condition, and IRQ_N would stay low for the whole hot period.
      - The SMBus Alert Response is "ignored in comparator mode".
    - **TPS25751 (C, from TRM SLVUCR8B §3.2.6).** IRQ stays low while any unmasked INT_EVENT1 bit is set, until the host writes INT_CLEAR1. INT_EVENT1 resets to 0x08 (PlugInsertOrRemoval). So if the EEPROM mask enables it, IRQ goes low right after boot.
    - **BQ40Z50 BTP via Q103 (D, TRM "Battery Trip Point").** It is latched until the host writes BTPDischargeSet/BTPChargeSet.
      - With BTP_EN = 1 and the default BTP_POL = 0 (asserted low), the pin idles high through the internal weak pull-up. Q103 inverts, so IRQ_N is stuck low permanently.
      - D is raising BTP_POL = 1 as their CONFIG item.
- **Proposed fix (firmware rules; add to the checklist and `mcu-io-power-states.md`):**
  1. At boot, configure every TMP1075 to TM = 1 (interrupt mode; any register read, an ARA or SD clears it) with the wanted THIGH/TLOW. Set unused limits to the rails (TLOW = −128 °C, THIGH = +127.9375 °C) to disable ALERT, per §7.4.4.
  2. At boot, read and clear INT_EVENT1 on 0x20 and 0x21. D: BTP_POL = 1 whenever BTP_EN = 1.
  3. The ISR loops: read all seven sources and clear them until DIO11 reads high. Re-check the level after the loop.
  4. Never enter Standby with DIO11 low. If it can't be cleared (a source stuck), fall back to RTC polling and log the source.
  5. TMP1075 in interrupt mode answers the SMBus Alert Response Address 0x0C, which finds the alerting sensor in one read (§7.3.2.6).
- **Confidence:** verified for the TMP1075 and CC2340. The TPS25751 and BQ40Z50 behaviour is from peers C and D (their datasheet citations).

### A-4 [CONFIG] TMP1075 shutdown/one-shot and the "hardware over-temperature interrupt while firmware sleeps" can't both be had; the power-up default also costs about 30–60 µA until firmware configures the sensors
- **Where:** U302–U304 (U305/U306 DNP). `cc2340-pin-budget.md` "Idle current" and "Optional".
- **Evidence:**
  - **The plan claims both.** The pin budget says firmware keeps the sensors in shutdown for one-shot readings, at 0.37 µA typical each, "about 1 µA for three in S2". It also says ALERT on IRQ_N gives "a hardware over-temperature interrupt that works even while firmware sleeps".
  - **They are mutually exclusive.** SD "shut[s] down all device circuitry except the serial interface" (§7.4.1), so there are no conversions and no comparisons. In interrupt mode a shutdown command also clears ALERT (§7.4.4.2).
  - **Shutdown current max is 3.5 µA each over temperature** (0.37 µA typical at 25 °C only; §6.5 p.7), so three can draw up to 10.5 µA.
  - **The power-up default is continuous conversion at 27.5 ms: 10 µA typical, 20 µA max each** (§6.5 p.7). That is 30–60 µA for three until firmware writes CFGR. In the unprogrammed or bootloader state this stays.
- **Proposed fix:** pick one per state and document it in `mcu-io-power-states.md` and `power-budget.md`.
  - **S2:** SD = 1, no hardware alert. The cells and stages are cool with no cable.
  - **S0/S1:** continuous at R = 11 (220 ms, 2.7 µA typical) with TM = 1 and the derating THIGH, so ALERT protects even if firmware stalls.
  - Correct the "1 µA" figure.
- **Confidence:** verified (datasheet).

### A-5 [MINOR] R314 100k on a ~250 mm, 15-pad IRQ_N net: weak leakage margin against VIH = 0.8·VDDS, and a high-impedance node routed past both switching stages
- **Where:** R314 (R315, R114 DNP), IRQ_N. The pads span U301 (200,55) to U303 (190,122) and U304 (243,93). The placement MST is ≈ 247 mm (Manhattan, `scratch-a/mstlen.py`). The net is unrouted.
- **Evidence:**
  - **Required high level:** VIH = 0.8 × 3.3 = 2.64 V (SWRS349A §7.18.4). That allows only 0.66 V / 100k = 6.6 µA of total leakage.
  - **Leakage budget:**
    - Q103 AO3400A IDSS: 1 µA max at 25 °C and 5 µA at TJ = 55 °C, specified at VDS = 30 V (ao3400a EC table). That is pessimistic at 3.3 V, but it is the only spec.
    - 5 × TMP1075 IIN: ±0.25 µA (§6.5).
    - 2 × TPS25751: unspecified.
    - The worst-case sum is ≈ 6–7 µA, right at the limit (inferred, because IDSS is specified at 30 V).
  - **Rise time:** τ = 100k × (≈ 35 pF trace + ≈ 100 pF AO3400A Coss at low VDS + pins) ≈ 15–20 µs. That is fine for an interrupt, but the node is high impedance for most of its length, next to 600 kHz half-bridges (R412 FSW). Coupled spikes can make false falling edges.
  - **Cost of a lower value:** the pull-up costs current only while a source is asserted, and every source is cleared promptly by firmware (A-3).
- **Proposed fix:**
  - R314 → 33k–47k: 70–100 µA only while asserted. Leakage margin rises to 14–20 µA.
  - Route IRQ_N on an inner layer between planes, away from SW nodes.
  - Enable the DIO11 input hysteresis.
- **Confidence:** arithmetic verified. The leakage worst case and coupling are inferred.

### A-6 [MINOR] SCL/SDA with 4.7k pull-ups and ≈ 90–100 pF: the 10–90 % rise is ≈ 1 µs, at TMP1075's "< 1 µs" limit. 400 kHz is not possible
- **Where:** R304/R305 4.7k via R312. The bus has 12 pads: U301, U302–U306, U401, U501, R115/R116 (gauge), J103, TP302/TP303. The placement MST is 280 mm (SCL) and 289 mm (SDA).
- **Evidence:**
  - **Capacitance estimate (inferred):**
    - Trace: ≈ 285 mm × 0.12–0.15 pF/mm (inner stripline) ≈ 35–43 pF.
    - Pins: TMP1075 5 pF each (§6.5) × 3 fitted, CC2340 ≈ 5 pF, TPS25751 × 2 ≈ 10–20 pF, gauge plus J103 and test points ≈ 10–15 pF.
    - Total ≈ 90–100 pF.
  - **Rise time:**
    - 0.8473 × 4.7k × 95 pF = 0.38 µs (30–70 %). That passes Standard mode (1 µs) and fails Fast mode (0.3 µs).
    - 2.2RC = 0.98 µs (10–90 %), against TMP1075 §8.3: "positive edge less than 1 µs by using a pullup resistor < 10 kΩ".
  - **Speed is set to 100 kHz anyway.** D: the gauge is SMBus 1.1, [XL] = 0, 100 kHz. The top-sheet note also says 100 kHz.
  - **Pull-up current limits:** 3.3 V / 3.3k = 1 mA, within TMP1075's 3 mA recommendation (§8.2.1), and the gauge VOL stays fine through R115/R116 100 Ω.
- **Proposed fix:**
  - R304/R305 → 3.3k: 2.2RC ≈ 0.69 µs.
  - Firmware: I2C at 100 kHz; see A-8.
  - Route SCL/SDA as a pair on an inner layer.
- **Confidence:** inferred (capacitance estimate; the board is unrouted).

### A-7 [MINOR] J303 pin 2 (IRQ_N) has no series resistor and sits next to pin 1 (3V3_MCU). A habitual 2.54 mm shunt on pins 1–2 shorts every asserting open-drain sink straight across 3V3
- **Where:** J303.1 3V3_MCU, J303.2 IRQ_N (direct), J303.3 NC. Note 11 says "J303 overrides … without shorting the MCU". That covers pins 4–6 only.
- **Evidence:**
  - From `nets.txt`, J303.2 sits on IRQ_N with no resistor.
  - With a shunt on 1–2 and a source asserting:
    - A TMP1075 ALERT is specified at 3 mA (VOL table §6.5).
    - The TPS25751 I2Ct_IRQ is unknown.
    - Q103 would conduct amps from the 3V3 rail (the TPS62177 limits at ~0.5 A+).
  - DIO11 is an input, so the MCU itself is not hurt, but the sources are.
- **Proposed fix:**
  - Add 1k in series with J303.2. It is a probe, and 1k is harmless at 100k pull-up impedance.
  - Or swap pins 2 and 3, so the NC pin sits next to 3V3.
  - Silkscreen "no shunts on 1–2".
- **Confidence:** verified (netlist). The damage threshold is inferred.

### A-8 [CONFIG] CC2340 pin and peripheral settings the hardware depends on (not in any checklist yet)
- **Where:** U301 all DIOs. `bringup-config-checklist.md` §4 is still STM32-only (see A-12).
- **Items:**
  1. **I2C0** on DIO6 (mux 2, I2C0SCL) and DIO8 (mux 4, I2C0SDA), 100 kHz, internal pulls off. At init, clock 9 SCL pulses (bus clear). C notes that the TPS25751 sees SCL/SDA low while 3V3 is dead, and may be mid-transaction when 3V3 comes up. Allow gauge clock stretching (SMBus up to 25 ms).
  2. **DIO11 IRQ_N:** input, internal pull **off**. The internal pull-up is 170–393 µA at Vpad = 0 at 3.8 V (§7.18.4 p.27), so ≈ 200 µA while IRQ_N is asserted. Falling-edge wake. See A-3.
  3. **DIO12 LED:** set the high-drive option. Measured from §7.18.4:
     - High drive: ≈ 53 Ω (0.53 V at 10 mA), giving ≈ 3.6 mA with Vf = 1.9 V.
     - Standard drive: ≈ 240 Ω (0.48 V at 2 mA), giving ≈ 2.5 mA. That is above the 2 mA rating point.
     - Keep the LED off in S2. The TPS62177 sleep-mode limit is 15 mA, and BLE TX at +8 dBm is < 11 mA (SWRS349A p.1).
  4. **DIO20 UART RX:** enable the internal pull-up, so the input doesn't float with J302 unplugged.
  5. **WDT:** confirm the debugger stall behaviour. The WDT "cannot be stopped once enabled" (§8.6), and a halted target will be reset.
  6. **CCFG bootloader:** see A-1.
  7. **DIO3/DIO4:** keep them as GPIO; never enable LFXT. Table 6-18 allows these pins as GPIO. They are plain GPIO3/GPIO4 at mux 0 (table 6-1 p.8).
- **Confidence:** verified (datasheet numbers).

### A-9 [MINOR] J302 (UART) has no series resistors: a powered USB-UART adapter on an unpowered board back-powers U301 through DIO20, and the ROM bootloader can't use J302 anyway
- **Where:** J302.1 UART_TX (DIO18), J302.2 UART_RX (DIO20), J302.3 GND.
- **Evidence:**
  - **Back-power:** an adapter TX idles high (3.3 V) into DIO20 with VDDS = 0. That exceeds the VDDS + 0.3 V abs max (§7.1), the same mechanism as A-2. It is current-limited only by the adapter's driver.
  - **Bootloader:** the ROM serial bootloader pin sets (TRM table 8-38):
    - Index 0: RX DIO20, TX **DIO6**.
    - Index 1: RX DIO12, TX DIO13. DIO13 is not bonded out on the module (table 6-1).
    - Index 2: RX DIO22, TX DIO20. DIO22 is not bonded out.
    - So no index matches J302's TX = DIO18. Index 0 works only with TX taken from TP303 (SCL). The bootloader leaves SDA (DIO8) as an input, so no I2C START can occur, and the I2C devices ignore the traffic (inferred).
    - SWD (J301) is therefore the only clean programming and recovery path. Note 8 implies a UART backdoor.
- **Proposed fix:**
  - 1k series on J302.1 and J302.2 for rev 2.0, or a note: "connect the adapter only with 3V3 up".
  - Note 8: "Recovery = SWD (J301). ROM UART only as index 0, RX = J302.2, TX = TP303 (SCL)".
- **Confidence:** pin table verified (TRM web page). Back-power verified from abs max.

### A-10 [MINOR] RF match: C314 (Z60) has no value or MPN, and C313/C315 are 0402 where TI's BOM uses 0201
- **Where:** C313 15p (GRM1555C1H150JA01D, 0402), C314 "TBD DNP" (no MPN), C315 1p (GRM1555C1H1R0BA01D, 0402), R321 0R 0402.
- **Evidence:**
  - Topology is correct (see "Checked and correct").
  - TI's CA1 is GRM0335C1H150GA01D, 0201 ±2 % (table 9-1 p.50).
  - The pad parasitics of 0402 versus 0201 shift the match slightly. TI says to retune anyway (§9.3.1.1).
  - C314 with no value can't be ordered for the retune.
- **Proposed fix:**
  - Give C314 a placeholder value and MPN (e.g. 1.0 pF C0G, GRM1555C1H1R0BA01D) and keep it DNP.
  - Note in the Notes property that the match was characterised on 0201.
  - No change needed for production unless the retune shows a problem.
- **Confidence:** verified.

### A-11 [DOC] Stale Notes properties on MCU-driven parts
- **Where and evidence (parts.txt):**
  - **R302** (now the RSTN 100k pull-up) reads "TPS25751 I2Ct_IRQ is open drain and needs an external pull-up (Table 5-1)". It should read "RSTN pull-up, SWRS349A fig. 9-1 R1 (100k) with C304 = C92".
  - **R313** reads "DNP: fit to keep the TPS62177 out of sleep mode …". It is fitted at 470k (README item 40).
  - **R321** reads "MCU 3V3 link". It is Z61 of the antenna pi match.
  - **R319** reads "… without fighting PB8". It should name DIO24.
  - **R435/R535** (port sheet, MCU-driven net) read "CHG_INH from the MCU (PB8) … (reset, IWDG reset, unprogrammed)". This should be DIO24 / WDT.
  - **R312** reads "feed TP308 for EV2400 work". See A-2.
- **Proposed fix:** rewrite as above.
- **Confidence:** verified.

### A-12 [DOC] Stale sheet text, sheet name and companion documents
- **Where and evidence:**
  1. **Sheet name "MCU and NTCs"**, in `MonolithDev.kicad_sch` and the sheet index line "4. MCU and NTCs". There are no NTCs on it since rev A7. It should be "MCU and Sensors".
  2. **mcu.kicad_sch heading "I2C1 + IRQ PULL-UPS".** The CC2340 has I2C0 (table 6-7).
  3. **The top-sheet text** "TPS25751 ADDRESS / DEAD-BATTERY STRAPS" ends "Gauge BQ40Z50-R2 = 0x0B on the same SDA/SCL bus (STM32WB I2C1, 100 kHz)". It should name the CC2340 I2C0 and add TMP1075 0x48–0x4C. The 0x20/0x21 values are correct (C: SLVSH93A tables 8-2/8-5/8-6).
  4. **`bringup-config-checklist.md`** (header still "rev A6") has these STM32 items:
     - §0 "U301 STM32WB1MMC … LGA-77";
     - §1.4 "Set the MCU option bytes: IWDG_SW…";
     - §4 "CHG_INH (PB8)", "Use Stop0–2, never Standby", "IWDG", "Stop2 only", "PB4 goes high first", "NTC_EN high only while sampling".
     - On the CC2340, Standby *is* the BLE sleep mode, and GPIOs latch in it (§8.11). The STM32 reason for "never Standby" (outputs go hi-Z) no longer applies.
     - The A-1, A-3, A-4 and A-8 items are missing.
  5. **`mcu-io-power-states.md`** carries a header saying it is out of date (pending rewrite, README item 40). It is still the document §4 points firmware to. It needs the rewrite before firmware starts.
  6. **`power-budget.md`** (rev A5):
     - It lists the STM32WB15/STM32WB1MMC currents.
     - It gives "Status LED ≈ 1 mA". R306 Notes now say about 4 mA; my estimate is 2.5–3.6 mA (A-8).
     - It has no TMP1075 line: 30–60 µA until configured, 1.1–10.5 µA in shutdown (A-4).
  7. **README item 40 "Not done yet"** says "LCSC numbers for U301–U306, C313–C315, R321 and R313". parts.txt now has LCSC for all of these except U301 (priced at TI.com, commit 7713eed) and C314 (TBD).
  8. **`cc2340-pin-budget.md`:**
     - "I2C SCL can only go on pin 9 (DIO6) or pin 11 (DIO24)". Pin 19 (DIO17/SWDCK) is also I2C0SCL (table 6-7). The conclusion still stands, because that pin is SWD.
     - "Accuracy: ±1 °C max". The DSG package is ±1 °C only from −40 to 75 °C, and ±2 °C to 125 °C (§6.5). The derating band is 80–95 °C, so it is ±2 °C there.
- **Proposed fix:** update as listed. Rewrite the checklist §0/§1/§4 and `mcu-io-power-states.md` for the CC2340 before firmware work.
- **Confidence:** verified.

### N-1 [NOTE] CC2340R5MODA operating ambient is −40 to +85 °C (junction also 85 °C), lower than everything else on the board
- SWRS349A §7.3 p.12.
- U301 sits at the top edge (200, 55), ≈ 31 mm from U302 (port 1 stage).
- This is fine on the bench. For the product enclosure, keep the module away from the FET/inductor heat and check the case ambient at 100 W.

### N-2 [NOTE] VDDS falling-slew limit (1 mV/µs, §7.3) is met
- The 3V3 effective capacitance at 3.3 V bias is roughly C207 22 µF (≈ 15 µF) + C301 4.7 µF (≈ 3 µF) + C403/C503 10 µF each (≈ 7 µF each) ≈ 32 µF.
- The load is 8–15 mA (power-budget.md).
- That gives a collapse rate of 0.25–0.47 mV/µs, under the 1 mV/µs limit. The rising-slew limit of 100 mV/µs is met easily by the TPS62177 soft start. (Inferred derating.)

### N-3 [NOTE] When the ROM bootloader runs (blank part, or A-1), the index-2 SPI pins are inputs on DIO11 (CS = IRQ_N), DIO24 (CLK = CHG_INH) and DIO12 (POCI = LED)
- TRM table 8-38.
- The interface's TX pin is enabled only after a host accesses it. CHG_INH is held high by R417/R517, so no SCLK edges occur. So the board stays in its safe hi-Z state.
- The LED could light only if the ROM ever chose SPI. Inferred, and harmless.

---

## Checked and correct

**U301 CC2340R5MODA**
- **Pinout:** all 24 symbol pins and footprint pads match fig. 6-1 and table 6-1 (pins 1–9 down the left, 10–15 along the bottom, 16–24 up the right; checked against the `.kicad_mod` pad coordinates). All 7 GND pins (1, 2, 5, 8, 22, 23, 24) and both VDDS pins (6, 7) are connected.
- **Mux:**
  - SCL DIO6 = I2C0SCL mux 2; SDA DIO8 = I2C0SDA mux 4.
  - UART TX DIO18 = UART0TXD mux 3; RX DIO20 = UART0RXD mux 3.
  - SWD on DIO16/DIO17.
  - DIO11 is wake-capable ("All digital I/Os are interrupt and wake-up capable", §8.7; table 8-3 "Wake-up on pin edge" in Standby).
  - High-drive pins are DIO12, DIO16, DIO17 and DIO24, which matches the LED and CHG_INH choices.
- **DIO3/DIO4 as GPIO** are allowed: they are GPIO3/GPIO4 at mux 0, the LFOSC is used, and fig. 9-1 shows Y1 as optional.
- **VDDS:** 3.3 V is inside the 1.71–3.8 V operating range and under the 4.1 V abs max. The DCDC needs ≥ 2.2 V, which is met.
- **Decoupling:** fig. 9-1 shows no external VDDS decoupling (the module has its own). C301 4.7 µF + C302/C303 100 nF is extra and fine.
- **Reset:** R302 100k + C304 100 nF equals TI's R1/C92 (§9.1). τ = 10 ms.
  - SW301 shorts only C304 (0.33 µC, negligible).
  - J301.10 nRESET is on the same node; an open-drain probe pull is fine.
- **RF match:** RFIO pin 4 → C313 15 pF (CA1) → node (C314 shunt Z60 DNP) → R321 0 Ω (Z61) → ANT_IN pin 3 with C315 1 pF shunt (Z62). This matches fig. 9-1 and the §9.3.1.1 LaunchPad values exactly.
  - The parts are placed within 4 mm of pads 3/4 and outside the fig. 9-2 keep-out (C315 at x = 195.3, keep-out from x = 196.5).
- **J301 SWD (FTSH 2×5):** pin 1 VTref = 3V3_MCU, 2 SWDIO, 3 GND, 4 SWCLK, 5 GND, 6 SWO NC, 7 key NC (shrouded, -K), 8 NC, 9 GNDdetect = GND, 10 nRESET. This is the standard Arm Cortex 10-pin, which the TI XDS110 10-pin also uses.
  - The footprint numbering is odd on one side and even on the other.
  - CC2340 has no SWO, so pin 6 NC is correct.
- **State analysis (reset, unprogrammed, bootloader, brown-out; pins hi-Z):**
  - CHG_INH: R417/R517 47k hold CE high, so charging is inhibited. Driven low, DIO24 sinks 2 × 3.3/48k = 0.14 mA, and CE = 0.07 V.
  - EN_5V1/EN_5V2: R432/R532 100k against the TPS62933 Ip of 0.7 µA gives 0.07 V, below the 1.1 V disable threshold (tps62933 EC), so the bucks are off. With 3V3 dead the EN pull-up current flows into the dead VDDS clamp at µA level.
  - 3V3_SLEEP: 2.75 V typical, so the regulator is in normal mode. The TPS62177 VH is 0.9 V. See A-1 for the CC2340 side.
  - LED: off.
  - J303 overrides through R317–R319 1k: a header against a driving pin is 3.3 mA. A standard-drive pin's VOL rises to about 0.35 V, so the MCU wins (EN stays below 1.1 V), as the Notes intend.
  - In Standby, GPIOs latch (§8.11), so CHG_INH, EN_5Vx and 3V3_SLEEP hold their state, and the WDT runs in Standby (§8.6).

**TMP1075 (U302–U306)**
- **DSG pinout:** 1 SDA, 2 SCL, 3 ALERT, 4 GND, 5 A2, 6 A1, 7 A0, 8 V+, EP 9 = GND (fig. 5-3, table 5-1). This matches the netlist and the KiCad DSG footprint.
- **Address straps** against table 7-2 (rendered p.14):
  - U302 A2/A1/A0 = 0/0/0 → 1001000 = 0x48.
  - U303 0/0/1 → 0x49.
  - U304 0/1/0 → 0x4A.
  - U305 0/1/1 → 0x4B.
  - U306 1/0/0 → 0x4C.
  - All are correct. A2 is used only at GND/V+ as required, and A0/A1 at GND/V+ as §8.3 recommends.
- **Supply:** V+ = 3.3 V, inside 1.7–5.5 V.
- **Decoupling and pads:** 0.1 µF (C308–C312) is at least TI's 0.01 µF. The EP is soldered to GND, which suits the thermal coupling (§8.4, mechanical note 3).
- **ALERT** is open drain, abs max 6.5 V on the non-N part, active low by default (POL = 0), with defaults of 80/75 °C in comparator mode (behaviour: A-3).
- **The MPN TMP1075DSGR is the non-N part,** so it supports 32 addresses and A1/A2.

**I2C/SMBus bus**
- **Addresses:** BQ40Z50 0x0B; TPS25751 0x20 (P1, ADCIN1 = LDO_3V3, ADCIN2 = GND) and 0x21 (P2, both GND), the same in BOOT and APP (C); TMP1075 0x48–0x4C.
  - The reserved responders are TMP1075 general call 0x00 (reset on 0x06) and ARA 0x0C (interrupt mode only).
  - There are no conflicts. The EEPROM (0x50) and BQ25756 are on the private I2Cc buses.
  - The gauge broadcasts ([BCAST], [HPE], [CPE]) default off (D), so the CC2340 is the only master, and the EV2400 is used procedurally.
- **Levels:**
  - Every device on the bus is on 3V3, and the pull-ups go to 3V3. CC2340 VIH is 2.64 V, which a 3.3 V idle meets.
  - VIL is 0.66 V. Gauge VOL of 0.4 V plus 100 Ω × 0.7 mA gives 0.47 V, and TMP1075 VOL is 0.4 V max at 3 mA, both below it.
  - TMP1075 VIH is 0.7 V+ = 2.31 V.
- **Dead 3V3:** R304/R305 become 4.7k pull-downs. The gauge treats bus-low for 2 s or more as "SMBus off" and sleeps; it is not a shutdown trigger, since PRES is tied to VSS (D, DS 8.3.15.1/9.2.2.2.4).
  - The gauge SMBC/SMBD are rated −0.3 to 30 V, so 3.3 V on an unpowered gauge is harmless (D).
  - TPS25751 with VBUS present and 3V3 at 0 V: the pins are pulled to 0 V, so no path into 3V3 (C).

**IRQ_N**
- **Every source is open drain:** TPS25751 I2Ct_IRQ (symbol open_collector), TMP1075 ALERT, and Q103 drain to GND. None can drive the net high, so nothing pulls it above 3V3 and there is no back-power path.
- **R314 to 3V3 is the only pull-up;** R315/R114 are DNP.
- **Q103 gate** is referenced to CELL_N with R117 470k. With BTP_EN = 0, BTP_INT sits low and Q103 is off (D).

**ERC**
- `erc.txt` has no entries on /MCU and NTCs/. The 8 known warnings are all U401/U501 GPIO-to-PWR_FLAG.
- **Symbol pin types** are consistent with this: ALERT and I2Ct_IRQ are open_collector, and the CC2340 DIOs are bidirectional.

---

## After round 2

These are my answers to the challenges in B-challenge.md, C-challenge.md and D-challenge.md that concern A items.

### A-1: AMEND → **CONFIG (required, blocking before first flash)**, plus a new **A-1b [MINOR]** R313 → 220k

**Conceded: the grade.**
- B, C and D all show that the trigger comes from the boot configuration, not from silicon:
    - TRM SWCU193 §8.5.1.2: the FCFG defaults apply only without a valid CCFG.
    - `bootCfg.pBldrVtor` can be `FORBID`.
- The stranded state is safe. D's state table verifies it:
    - CHG_INH is hi-Z, so R417/R517 inhibit both chargers.
    - EN_5Vx are hi-Z, so PP5V is off.
    - The TPS62177 stays in normal mode.
    - The gauge and U102/F102 protect the cells independently.
- That is the brief's CONFIG definition, so MAJOR overstated it.
- It stays a **required, blocking** checklist line, because a default SysConfig build ships with the trigger armed. In the product, with no button or J301, a stranded unit would stay dead to BLE and PD until CUV (D: about 6–7 months at about 0.85 mA).

**Conceded: the timing race is not the live mechanism.**
- D cites SWRS349A §7.17.2: Reset/Shutdown → Active takes 350–450 µs, "includes device ROM bootcode execution time".
- The R313 recharge (τ ≈ 7 µs) settles long before the ROM samples.
- I withdraw the RC race as a mechanism.

**Absorbed: two live mechanisms.**
1. **The steady-state level, at every power-on (not only after S2).**
    - TPS62177 ILKG_SLEEP = 1.4 µA is a typical value with no maximum. B, C and D each read the render; my `scratch-a/tps62177_sleepleak.png` agrees.
    - The divider is 0.834 × VDDS typical against VIH = 0.8 × VDDS.
    - So a stronger-than-typical internal pull-down can trigger the bootloader on any boot.
2. **The Shutdown latch** (D, SWRS349A §8.11: "In Shutdown mode … the I/Os are latched").
    - If firmware enters Shutdown with DIO21 low, the next boot sees DIO21 low deterministically.

**Final fix: CONFIG.**
- Production CCFG: "Any bootloader forbidden" (`pBldrVtor = FORBID`).
- Dev board: "Default FCFG bootloader, with CCFG settings", with the pin trigger disabled or moved to DIO3 active-high. J303 pin 1 → pin 4 forces it through R317, and R432 holds it low otherwise.
- Firmware rule: drive DIO21 high before Shutdown and before any deliberate reset (D).
- Note 8 should name the trigger pin.

**A-1b [MINOR]: R313 470k → 220k** (I choose B/C's value over D's 100k). DIO21 reads high when the pull-down is at least 4 × R313:

| R313 | Typical level (pull-down 2.36 MΩ) | Holds VIH (0.8·VDDS) until the pull-down is stronger than | Cost in S2 (DIO21 low) |
|---|---|---|---|
| 470k (now) | 2.75 V | 1.88 MΩ (1.25× typical) | 7 µA |
| **220k** | 3.02 V | 0.88 MΩ (**2.7× typical**) | 15 µA (≈ +2.5 µA at the pack) |
| 100k | 3.17 V | 0.40 MΩ (5.9× typical) | 33 µA (≈ +8 µA at the pack, about 3 % of the D-3 idle budget) |

- **Why 220k is enough.** An on-die resistor that is 2.7× low is far outside normal process spread (typically ±20–30 %, inferred).
- **What it is for.** The only job of the hardware margin is insurance against a missed CCFG setting. With the CCFG fix, the TPS62177 side (VH 0.9 V) is robust even at 470k.
- **Why not 100k.** It buys margin we don't need for 4× the S2 cost. If the lead prefers 100k, I don't object.

### A-2: **MAJOR stands** (agreed by B, C and D), amended

**Absorbed: D's EV2400 point.**
- Review 1 decision Q5 (`schematic-review-2026-10-12.md`) records "EV2400 pull-ups are 20 k to 3.3 V".
- So a connected EV2400 alone injects about (3.3 − 0.6)/20k ≈ 0.13 mA per line into a dead CC2340, even with R312 removed and TP308 unfed (inferred from the record; not measured).
- There is therefore **no** "3V3 dead" EV2400 procedure that respects the CC2340's abs max.

**Absorbed: C's half-powered bus point.**
- The injected current lifts the whole 3V3 rail through R301 to about 1.5–2.5 V.
- That is around the TPS25751 VIN_3V3 UVLO (2.44–2.76 V) and the CC2340 BOD.
- Half-powered TPS25751 I2Ct pins, TMP1075s and the CC2340 then sit on the same SDA/SCL the EV2400 is using. They can hold or glitch the bus during a gauge data-flash write.
- This is a functional risk even if no part is damaged.

**C's trace confirms the procedure is actually instructed.** It appears in:
- `bringup-config-checklist.md` §2 step 4 ("With 3V3 down, remove R312 and feed TP308");
- the R312 Notes property.
That is what makes the condition credible on every fresh board (FETs off, so PACK_P and 3V3 are dead).

**Final fix (procedure and documentation, no hardware):**
1. For all gauge and EV2400 work, turn J104 on. It powers PACK_P through D104, so 3V3 is up. Keep R312 fitted.
2. Hold the CC2340 off the bus while the EV2400 masters it: SW301 or J301 nRESET held low, or firmware idle with I2C released. This also avoids multi-master collisions.
    - Holding reset inhibits charging (CHG_INH hi-Z) and turns PP5V off. That is fine on the bench.
3. Rewrite checklist §2 step 4, the R312 Notes and sheet note 10.
4. Add to R301's Notes: "never leave open with 3V3 up".
5. The rev 2.0 hardware option (series R in DIO6/DIO8) is unchanged.

**Residual after the rewrite: DOC** (C's point 3). Grade for this review: **MAJOR**, fix by procedure only, no rework.

### A-3, A-4, A-5, A-6, A-7, A-9: no change
- **A-3, A-4, A-5, A-6, A-7, A-9:** B, C and D all AGREE; no disputes.
- **A-6:** D adds that 3.3k keeps the gauge VOL inside 0.4 V at 1 mA (DS 7.11: 0.4 V at 1.5 mA). Absorbed.
- **A-7:** D adds that Q103 (about 48 mΩ at VGS 2.5 V) would carry up to the TPS62177's 1.0–1.2 A current limit through a 1–2 shunt. Absorbed.

### A-8 [CONFIG]: two items added from round 2
8. **EN_5Vx after reset (from my C-6 challenge).** PP5V's ≈ 250 µF holds Rp (> 4.75 V) for about 8–80 ms after an MCU reset, depending on the VCONN load. Firmware should restore EN_5V1/EN_5V2 from retained state as its first action after reset, before BLE stack init.
9. **DIO21 before Shutdown or reset.** Drive it high (D, A-1 above).

### A-10, A-11, A-12, N-1, N-3: no challenges; unchanged
- C independently found R302's stale Notes (already in A-11).

### N-2: amended
- D-14 computes about 1.9 mV/µs at the very start of a collapse at the 38 mA peak load. That exceeds §7.3's 1 mV/µs.
- Near the 1.67 V BOD it is about 0.7 mV/µs, and a brown-out normally happens at low load.
- It stays a NOTE. If bring-up shows bad resets on brown-out, TI's remedy is 10 µF on VDDS (§7.3 footnote 3): C301 4.7 µF → 10 µF in rev 2.0.

### Final severity per item

| Item | Round 1 | Final |
|---|---|---|
| A-1 | MAJOR | **CONFIG** (required, blocking before first flash) |
| A-1b | — | **MINOR** (R313 → 220k) |
| A-2 | MAJOR | **MAJOR** (procedure fix only) |
| A-3 | CONFIG | CONFIG |
| A-4 | CONFIG | CONFIG |
| A-5 | MINOR | MINOR |
| A-6 | MINOR | MINOR |
| A-7 | MINOR | MINOR |
| A-8 | CONFIG | CONFIG (items 8 and 9 added) |
| A-9 | MINOR | MINOR |
| A-10 | MINOR | MINOR |
| A-11 | DOC | DOC |
| A-12 | DOC | DOC |
| N-1, N-2, N-3 | NOTE | NOTE (N-2 amended) |
