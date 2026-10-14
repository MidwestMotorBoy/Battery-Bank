# Reviewer C findings: MCU and NTCs, Sleep Current and 3V3, cross-sheet interfaces, BOM-wide pass

Scope: mcu.kicad_sch (U301 and 3xx), power.kicad_sch (2xx), the shared I2C/SMBus bus, global labels, power-up and reset states, and the BOM.
Inputs: nets.txt, parts.txt and erc.rpt (rev A4, 2026-10-12). Datasheets were extracted with pdftotext (C_txt/). LCSC part pages were fetched where noted.

Summary (AMENDED in round 2): 0 CRITICAL, 0 MAJOR, 5 MINOR, 13 NOTE. (First pass: 7 MINOR, 11 NOTE; C-3 and C-5 were downgraded to NOTE after Reviewer A's challenge.) My two sheets are in good shape after rev A4. Every rev A4 change in my scope checks out (see "Verified" at the end). The minors are margin, testability and BOM-hygiene items, plus one firmware-architecture limit on CHG_INH (C-1).

---

### C-1 [MINOR] CHG_INH can't be held asserted while the MCU is in Standby, Shutdown or reset. The inhibit is lost exactly when firmware is not running.
- **Where:** U301 PB8 (net CHG_INH) → R435/R535 1k → CE_N, with R417/R517 10k to GND (usb_port sheet). R319 goes to J303.6.
- **Evidence:**
  - DS13258 §3 (power modes table, notes 7/8): in Standby/Shutdown the I/Os float unless the PWR pull-up/pull-down (APC) is configured.
  - DS13258 I/O static characteristics: RPU = 25 / 40 / 55 kΩ (min/typ/max).
  - bq25756 §6.5 (logic I/O): CE VIH = 1.3 V min, VIL = 0.4 V max, leakage 1 µA max.
  - In reset, PB8 is an analog input (DS13258 Table 14 legend: "all I/Os are set as analog inputs during and after reset").
- **Worst-case math:**
  - PB8 sees two branches of 1k + 10k to GND in parallel, 5.5 kΩ.
  - Standby pull-up, best case RPU = 25 kΩ: node = 3.3 × 5.5/(25 + 5.5) = 0.60 V, so CE = 0.60 × 10/11 = 0.54 V < 1.3 V. CE reads low and charging is enabled.
  - At typical and maximum RPU it is lower still.
  - So firmware can't keep both chargers inhibited across Standby/Shutdown, a watchdog reset, a brown-out, or a debugger reset.
- **Accepted design point:** fail-open (charging allowed) when the MCU is off is a deliberate decision (Q2; R435 note). It keeps a dead pack recoverable from USB.
- **The gap:** the inhibit disappears on every low-power transition and every reset, and nothing in the docs says so. It is the only second protection layer (decision Q2 / rev2-changes 1b).
- **Proposed fix (cheap, keeps fail-open):** raise R417/R517 to 100k.
  - Off/reset: CE = 1 µA × 100k ≤ 0.1 V < VIL 0.4 V. Still fail-open.
  - Standby with APC pull-up at RPU 55 kΩ worst case: node = 3.3 × 50.5/(55 + 50.5) = 1.58 V, so CE = 1.56 V > 1.3 V. Marginal, but it holds. At typical 40 kΩ, CE ≈ 1.8 V.
  - Optionally add 1 nF at CE for noise.
- **Firmware either way:**
  - Use Stop2, not Standby, while inhibiting. Stop keeps output states.
  - Keep the inhibit reason in a backup register so that after a reset PB8 is re-asserted before the gauge is polled.
  - If R417 is not changed, document "Standby/Shutdown = inhibit released".
- **Coordination:** sent to Reviewer B, because R417/R517 are on the usb_port sheet. **B agreed and re-derived the numbers.**
  - Nothing else on CE_N depends on the 10k.
  - Standby margin with 100k is 0.26 V.
  - 220k was rejected: leakage would put 0.22 V on CE, too close to VIL.
  - B adds a DNP 1 nF from CE to PGND, because CE (pin 7) faces the SW-node pins.
  - B also notes that CE stops charging only. It has no effect on reverse/source mode (B-1), so firmware cannot use CHG_INH to stop sourcing.
- **Confidence:** high on the math. Medium on whether the lead prefers a firmware rule to a part change.
- **AMENDED in round 2:**
  - **Margin corrected.** Reviewer A included the 1 µA CE high-level leakage per charger. Thevenin at the PB8 node with RPU = 55 kΩ: R_th = 55k ∥ 50.5k = 26.3k. Two chargers × 1 µA × 26.3k = 53 mV lower, so CE ≈ 1.51 V. The margin over VIH is about 0.2 V, not 0.26 V. Any pull-down below about 82 kΩ fails. 100 kΩ stands.
  - **A also proposes swapping the polarity** (pull-up to 3V3; MCU pulls low to allow charging). This fails safe whenever 3V3 is alive but the MCU is not commanding.
    - It also blocks USB charging on a fresh board with an unprogrammed MCU, and while SWD holds reset.
    - The dead-pack case still works: 3V3 is off, so the pull-up has no source.
    - That is a policy change from decision Q2's "fail open", so it is for the lead to decide. Both options are electrically sound.

### C-2 [MINOR] D301 (Everlight 19-217/GHC emerald-green InGaN, Vf 3.3 V at 20 mA) on 3.3 V through 1 kΩ will be very dim or barely visible
- **Where:** PB5 → R306 1k → D301 (C72043) → R307 0R → GND.
- **Evidence:**
  - LCSC C72043 page: 19-217/GHC-YR1S2/3T, emerald green 518 nm, Vf 3.3 V at 20 mA, 199 mcd.
  - InGaN Vf at about 0.5–1 mA is roughly 2.6–2.8 V (typical InGaN I–V; not in the LCSC page). PB5 VOH drop is about 0.1 V.
- **Worst case:** I = (3.3 − 0.1 − 2.7)/1k ≈ 0.5 mA, about 0.25 % of the rated current, roughly 3–5 mcd. Visible indoors, invisible in daylight. With a high-Vf bin (up to about 2.9 V at 0.5 mA) it is about 0.3 mA.
- **Proposed fix:** either
  - keep the LED and make R306 330 Ω (≈ 1.5 mA, still sleep-friendly since R307 is pulled for measurements), or
  - use an AlGaInP 570 nm green (Vf about 2.0 V) at 1 k.
- **Confidence:** medium-high. The LED will light, just weakly.

### C-3 [NOTE] (AMENDED in round 2: was MINOR) Fitting JP202 hot-plugs 16.8 V onto a bare MLCC. Ringing on LDO_IN can approach the TPS70950 32 V absolute maximum.
- **Where:** PACK_P → JP202 (2.54 mm shunt) → LDO_IN → C204 (1 µF 50 V 0805) → U203 IN. No series resistance.
- **Evidence (tps709):**
  - §6.1: VIN absolute maximum is 32 V.
  - §6.3: VIN recommended maximum is 30 V.
  - §8.1.1: "An input capacitor is necessary if line transients greater than 10 V in magnitude are anticipated." Fitting JP202 is exactly such a transient.
- **Worst-case math (assumed values, stated):**
  - Loop L from the PACK_P bulk (C432 etc. at the chargers) through the PACK_P route and the jumper: about 50–100 nH.
  - C204 effective capacitance at 16.8 V: about 0.6–0.7 µF.
  - Loop R (two shunt contacts, trace, MLCC ESR): about 50 mΩ.
  - Z0 = √(75 nH / 0.65 µF) = 0.34 Ω, so ζ = R/(2·Z0) ≈ 0.07.
  - Overshoot ≈ exp(−πζ/√(1−ζ²)) ≈ 0.80, so the peak is about 1.8 × 16.8 = 30 V.
  - From J104 or charger BAT_OVP (17.5 V), the peak is about 31.5 V.
  - That is above the 30 V operating maximum and within 0.5–2 V of the 32 V absolute maximum.
  - Contact bounce repeats the event.
- **Contrast:** the TPS62177 input is damped by R201 (10 Ω), so it has no such problem.
- **Proposed fix:** a 100 Ω 0603 in series in LDO_IN, between JP202 and C204.
  - Load is about 1 µA (LDO) + 2 × 48 µA (INA190 IQ) ≈ 0.1 mA, so the drop is 10 mV. Dropout margin is unaffected (16.8 V in, 5 V out).
  - ζ becomes > 100, so there is no overshoot.
- **Confidence:** medium. The parasitics are estimates; the mechanism is standard (ceramic-input hot-plug).
- **AMENDED in round 2: downgraded to NOTE.**
  - Reviewer A's loop estimate is L 30–60 nH, R 60–150 mΩ, giving ζ 0.12–0.29 and a 23–29 V peak.
  - I don't accept that C432's 30 mΩ ESR sits in series: the 3 × 47 µF MLCCs in parallel make the source ESR only a few mΩ. A sliding jumper contact is tens of mΩ or more, though.
  - So the realistic peak is about 25–30 V. That stays under the 32 V absolute maximum in both estimates and only briefly touches the 30 V recommended maximum.
  - The 100 Ω series resistor is still a free tweak, not a required fix.

### C-4 [MINOR] Testability: the whole board has one GND test point (TP203, at the SMA connectors), and several rails have no test point
- **Where:** net GND in nets.txt.
  - The only TP on GND is TP203.
  - Other GND access points are connector pins: J103.1, J104.2, J301.3/5/9, J302.3, J303.7, J402.3, J502.3.
- **Rails with no test point:**
  - 5V_AMP (U203 output, the INA190 supply).
  - LDO_IN.
  - 3V3_MCU, reachable only via the J301.1 and J303.1 header pins.
  - P1_LDO_3V3 and /USB Port 2/LDO_3V3: the TPS25751 LDO, the dead-battery indicator, and the EEPROM/I2Cc pull-up rail.
  - LDO_1V5 (×2), 5V_IN (×2), DRV_SUP (×2), and BAT_SNS_P/VBAT_SYS (×2).
  - CE_N (×2): the CHG_INH result at the charger pin. It can only be read at the R417 pad.
- **Evidence:**
  - circuit-description §8 asks for "SW1x/SW2x (scope-probe friendly, with nearby GND)".
  - The README says each port has a 2 × 5 probe field. With no GND point in it, every SW1/SW2/REGN/PG probe needs a long ground lead or a clip to a connector shell. On SW nodes at 600 kHz with tens of ns edges, that makes the measurement meaningless.
- **Proposed fix:**
  - Add a GND test point (Keystone 5000 class, or a ground-spring pad) in each port's probe field, beside the MCU block and beside the gauge (labelled GND, not CELL_N).
  - Add a test point on 5V_AMP, on each LDO_3V3 (dead-battery debugging: is the TPS25751 running from VBUS or VIN_3V3?), and on each CE_N.
- **Confidence:** high.

### C-5 [NOTE] (AMENDED in round 2: was MINOR) J301 MPN "FTSH-105-01-L-DV-K" has a keying shroud, not pin 7 removed. The part notes and README say "Keyed (pin 7 removed)".
- **Where:** J301 Notes and MPN, README item 17 ("keyed SWD header (Samtec FTSH-105-01-L-DV-K)"), review m15.
- **Evidence:**
  - Samtec FTSH datasheet ordering options (as quoted by distributor pages for this part): "–K = Keying Shroud for mating with FFSD (Style –01 only)".
  - Polarization (an omitted pin) is a separate "–XXX" position code, for example FTSH-105-01-L-DV-007-K.
- **Effect:**
  - With the part as ordered, all 10 pins are present.
  - A probe cable whose pin-7 socket is plugged (the Arm Cortex 10-pin "KEY" position) won't seat.
  - Shrouded FFSD cables will be keyed by the shroud, which is probably what was wanted.
  - The shroud also enlarges the body compared with KiCad's generic `PinHeader_2x05_P1.27mm_Vertical_SMD` courtyard. It is not a Samtec land pattern: pads are at ±1.95 mm, 2.4 × 0.74 mm.
- **Proposed fix:**
  - Decide between shroud (-K) and pin 7 removed (-007-K for both), then correct the notes and README.
  - Check the footprint against Samtec's FTSH-1xx-01-xxx-DV-K recommended layout and shroud outline before placement freezes.
- **Confidence:** medium. This is from the Samtec ordering key as quoted, not from the PDF in the repo.
- **AMENDED in round 2: downgraded to NOTE.**
  - The shrouded -K part is the Arm-recommended keyed header, so the part choice is fine.
  - Only the notes' "pin 7 removed" wording is wrong.
  - Still check the footprint against Samtec's land pattern and shroud outline.

### C-6 [MINOR] The BOM fix for m21 is incomplete: 107 placed (non-DNP, non-hand-fit) parts still have no LCSC number, including parts in the 3V3 power path
- **Where:** parts.txt. Rows with LCSC empty, not DNP, excluding TP/J/BT and the R430/R530 net ties: 107.
- **In my scope:**
  - C204, C206, C207 (TPS62177 output cap).
  - R202, R203, R206, R207 (3V3 link), R208.
  - R301 (MCU 3V3 link), R302 (BOOT0 pull-down), R303 (antenna 0R), R304/R305 (SMBus pull-ups), R306, R307.
  - R1–R4 (PD address straps: a missing R1 changes port 1's I2C address and dead-battery mode).
  - R401/R501 (VIN_3V3 links).
- **Elsewhere:** C101–C104, C107, C108, R105–R116 (gauge), and most 4xx/5xx passives: C407, C410–C419, C430, C438–C446, R402–R404, R417 (CE pull-down), R420–R429, R432 (EN_5V pull-down), and the port 2 copies.
- **Effect:**
  - JLC's BOM matcher either guesses or leaves the part off.
  - Missing R207/R301/R401/R501 means no 3V3 to the MCU or PD controllers.
  - Missing R417/R432 floats CE and EN.
  - The first review's m21 was closed as "Fixed for the listed parts", so this is the remainder.
- **Proposed fix:** assign JLC basic parts. For example: 0R 0603 C21189, 0R 0805 C17477, 10k 0603 C25804, 100k 0603 C25803, 4.7k 0603 C23162, 1k 0603 C21190, 100R 0603 C22775, 0.1 µF 50 V 0603 C14663.
- **Confidence:** high on the count. The suggested LCSC numbers are from memory and should be verified, except C21189, C25803, C23162 and C21190, which are already used in this BOM.

### C-7 [MINOR] The 3V3 rail feeds both TPS25751 VIN_3V3 pins, whose I2Ct pins are rated 4 V absolute maximum. TP308 (bench pull-up feed for EV2400 work) has no voltage limit on silk or in the notes.
- **Where:**
  - TP308 / SMB_PU → R304/R305 → SDA/SCL → U401/U501 I2Ct_SDA/SCL, U301 PB6/PB7, U101 SMBD/SMBC.
  - Sheet note 10: "remove it and supply TP308 for EV2400 work while 3V3 is down".
- **Evidence:**
  - tps25751 §6.1.1: I2Ct_SCL, I2Ct_SDA −0.3 to 4 V.
  - DS13258: FT_f pins are VDD + 4.0 V, which is 4.0 V when the MCU is unpowered (3V3 down is exactly this case).
- **Effect:** a 5 V bench supply, or a 5 V EV2400 VOUT setting, on TP308 exceeds both limits while the board is unpowered.
- **Open question (low confidence):** TI does not say whether the I2Ct pins are fail-safe with VIN_3V3 = 0. If they have an ESD path to LDO_3V3, a 3.3 V TP308 partly back-powers each TPS25751, about (3.3 − 0.6)/4.7k ≈ 0.5 mA per line. A half-powered target could load the bus during EV2400 work.
- **Proposed fix:**
  - Silk "3.3 V MAX" at TP308 and add it to sheet note 10.
  - Prefer J104 (bench PACK_P), so the whole 3V3 domain is properly powered, over TP308.
  - At bring-up, check the SDA/SCL idle level with TP308 at 3.3 V and 3V3 = 0.
- **Confidence:** high on the limit, low on the back-power question.

---

### C-8 [NOTE] Sleep-current budget items not covered by Q7
1. **Gauge SMBus pull-downs:** bq40z50 §7.11 gives RPD 0.7–1.3 MΩ on SMBC and SMBD. Against R304/R305 on 3V3 that is 2 × 3.3 V/1 MΩ ≈ 6.6 µA (5–9.4 µA), continuous, through R_MEAS.
2. **TPS25751 sleep current:** IVIN_3V3,Sleep is 56 µA typ each (tps25751 §6.5), so 112 µA, which dominates the 3V3 branch. Firmware cannot lower it except via the TPS25751 sleep configuration.
3. **Gauge never sleeps (from Reviewer A):** the gauge sleeps only on SMBus low for Bus Timeout unless [IN_SYSTEM_SLEEP] = 1, so it stays at INORMAL ≈ 336 µA. This is pack drain, not R_MEAS: the gauge's BAT/VCC come from CELL_P/FET_MID via D101/R105 and R106. Fix is in A's item ([IN_SYSTEM_SLEEP] = 1, [SLEEPCHG] = 1).
4. **INA190A5 floor:** offset ±15 µV × 500 = ±7.5 mV. REF = GND, so a negative offset clips at 0 V. The resolution floor is therefore about 1.5 µA on 10 Ω (ina190 §6.5). Document it for anyone reading sub-2 µA results.
5. **Measurement bandwidth:** R201 and C206 (≈ 1.3 µF effective at 12 V) form a 1/(2π·10·1.3 µF) ≈ 12 kHz low-pass on the current R_MEAS sees. That is below both INA190 bandwidths (27/45 kHz), so TPS62177 PFM bursts look smoothed. The average is correct, but document it.

### C-9 [NOTE] Firmware: WKUP polarity for IRQ1/IRQ2, and pins that can't wake the MCU
- PA0 (WKUP1) and PA2 (WKUP4) are the only Standby/Shutdown wake pins (DS13258 §3, note 8: "The I/Os with wake-up from Standby/Shutdown capability are PA0 and PA2").
- TPS25751 I2Ct_IRQ is active low (open drain, R314/R315 100k pull-ups), so PWR_CR4.WUPPx must be set to falling/low polarity.
- GAUGE_BTP (PA6) can't wake from Standby (already firmware item 10), and nothing else can.

### C-10 [NOTE] Firmware: TPS62177 sleep-mode load
- In sleep mode (SLEEP low) the converter supplies 15 mA (tps62177 §7.5, IOUT_SLEEP).
- In MCU Standby/Shutdown PB4 floats, and the internal pull-down selects sleep mode (§8.4.4) unless APC holds PB4 high (40 kΩ vs the 1.4 µA leak: fine).
- If a cable is attached while the MCU sleeps, the load becomes:
  - one TPS25751 in Active Sink, 3–6 mA (IVIN_3V3,ActSnk), plus
  - MCU wake at 64 MHz, a few mA, plus
  - BLE TX, about 5–9 mA.
- That approaches or exceeds 15 mA. TI says the converter can briefly deliver more "to allow micro controllers to wake up and drive the sleep signal High".
- Firmware: drive PB4 high as the first instruction after wake or reset, and keep sleep mode out of any state with the radio active (extends firmware item 7).

### C-11 [NOTE] Firmware: system-bootloader pin sharing (BOOT0 via TP306)
- DS13258 Table 15 marks the bootloader interfaces: I2C1 (boot) on PB6/PB7, USART1 (boot) on PA9/PA10, SPI1 (boot) on PA4 NSS / PA5 SCK / PA6 MISO / PA7 MOSI.
- In bootloader mode the STM32 therefore becomes an I2C target on the shared SMBus (address per AN2606, not in the repo; confirm it isn't 0x0B/0x20/0x21).
- SPI1 MISO lands on PA6 (GAUGE_BTP, the Q103 drain).
- PA4 (NSS) is pulled low by the TH303 divider while NTC_EN floats, so SPI1 is selected. If the bootloader drives MISO high while Q103 is on, the pin fights a 2N7002. This is unlikely (DR is 0 until the SPI sync byte arrives), but use the UART bootloader with the gauge quiet.
- PA7 (SPI MOSI, boot) floats on J303.2. AN2606 asks for unused bootloader RX pins at a defined level. SCK (PA5) is held low by TH304's divider, so false SPI detection is unlikely.

### C-12 [NOTE] TH301–TH304 / TH401 / TH501 B-constant labelling
- The value "10k B3435" matches B25/85.
- LCSC C13564 (NCP18XH103F03RB) lists B25/50 = 3380 K.
- Firmware and the BQ25756 TS calculations (R415/R416 note) must use the same constant, ideally Murata's R-T table, or the readings disagree by about 0.5–1 °C at 75–95 °C.

### C-13 [NOTE] R201 power rating differs from the description
- R201 is 1206W4F100JT5E, 1/4 W (LCSC C17903). circuit-description §3 says "10 Ω (1 %, 0.5 W, 1206 or larger)".
- Normal operation is fine:
  - Start-up: 0.2 A × 10 Ω for about 0.35 ms = 0.4 W pulse, as the part note says.
  - Steady state at 30 mA on 3V3 from 10 V: < 2 mW.
- If U204 fails short VIN–GND, R201 dissipates 16.8²/10 = 28 W and acts as the fuse. That is acceptable (a 1/4 W thick-film part opens quickly), but note it, and keep R201 away from the INA190s and the holders.
- Update the description or the part.

### C-14 [NOTE] PB5 LED glows during reset
- DS13258 Table 15 note 10: "PB5 pin is configured as input with pull up active under reset if NRST pin is active".
- While SW301 or a debugger holds NRST low, D301 draws (3.3 − 2.6)/(40k + 1k) ≈ 17 µA. It glows faintly.
- Harmless. Keep in mind when measuring reset-state current.

### C-15 [NOTE] JP201/JP202 shunts are not in the BOM
- The headers are listed: JP202 is C492401 (PZ254V-11-02P); JP201 has no MPN/LCSC. The 2.54 mm shunt caps are not.
- The board then arrives with the amplifier section unpowered and disabled (safe), but the bring-up kit needs two shunts.
- Add a "2.54 mm shunt ×2 (hand)" BOM line.

### C-16 [NOTE] Gauge broadcast mode must stay off ([BCAST] = 0)
- bq40z50 §8.3.15: "SMBus v1.1 with MASTER mode".
- With broadcasts enabled, the gauge masters the bus to 0x08/0x09, colliding with the STM32's I2C1 transactions. Nothing on this board listens at 0x09.
- Sent to Reviewer A for the configuration list.

### C-17 [NOTE] Root sheet: the port 2 sheet's LDO_3V3 pin is unconnected (intended)
- `/USB Port 2/LDO_3V3` has no root connection. Port 2 straps ADCIN1 to GND (R3), so it isn't needed.
- The project ERC ignores "Global label only appears once". I checked every global label by hand: CHG_INH, EN_5V1/2, GAUGE_BTP, IRQ1/2, SCL, SDA and 3V3_SLEEP each appear on at least two sheets.

### C-18 [NOTE] Main I2C bus loading
- Pull-ups are 4.7k to 3.3 V, so pull-up current is 0.70 mA (0.87 mA with the EV2400's 20k).
- Estimated bus capacitance:
  - About 20–25 cm of trace on 0.1 mm prepreg at about 1.5–2 pF/cm: about 40–50 pF.
  - Devices: STM32 about 5 pF, gauge 5 pF (§7.11), two TPS25751 about 10 pF each.
  - Two test points plus J103.
  - Total about 80–100 pF without a cable, about 150–200 pF with the EV2400 cable.
- tr = 0.8473 × 4.7k × 200 pF ≈ 0.80 µs. That is under the 1 µs Standard-mode/SMBus limit, so 100 kHz is fine.
- 400 kHz would need about 1.5k (tr ≤ 300 ns) and is ruled out anyway: the gauge in SMBus 1.1 mode is limited to 100 kHz (§7.33 fSMB).
- The TPS25751 doesn't need 400 kHz, because the configuration loads from EEPROM.
- Addresses: gauge 0x0B, U401 0x20 (ADCIN1 = 7, ADCIN2 = 0 → index #1, SafeMode), U501 0x21 (0/0 → #2, SafeMode), from tps25751 Tables 8-2, 8-5 and 8-6. No collision.

---

## Verified (no finding)

**U301 (STM32WB1MMC)**
- All 77 pins match the DS14096 Figure 4 pinout: VSS 1–4/15/17/19/24/31/43–77, VSSRF 5/8, ANT_IN 6, ANT_OUT 7, VDDA 16, VBAT 18, VDDSMPS 20, VSSSMPS 21, BOOT0 22, NRST 23, and the GPIOs.
- VDDA, VBAT and VDDSMPS are all on 3V3_MCU. The module has its SMPS components and filtering internal (DS14096 §3).
- PB0–PB2 are NC per §7. R303 0R joins ANT_IN–ANT_OUT, which is the internal-antenna option. I could not render Figure 2; the text supports "connected".

**MCU peripheral functions (DS13258 Table 15)**
- I2C1: PB6 = I2C1_SCL, PB7 = I2C1_SDA (FT_f).
- USART1: PA9 TX (FT_fa), PA10 RX (FT_f).
- ADC: PA1 = ADC1_IN6, PA3 = IN8, PA4 = IN9, PA5 = IN10.
- WKUP1 = PA0, WKUP4 = PA2.
- PB4 has the NJTRST pull-up after reset (note 8), so the TPS62177 boots in normal mode, as the README claims.
- PB8 is FT_f.

**Pin tolerance and drive levels**
- Every connected GPIO is FT, FT_a or FT_f, and no pin sees more than 3.3 V from on-board sources (IRQ pull-ups, R114, SMB_PU, R316–R319).
- No back-power into the MCU with R301 removed: FT pins have no clamp to VDD.
- EXTI lines: 0 (IRQ1), 2 (IRQ2), 6 (BTP). No collision.
- NTC_EN on PA8 drives 4 dividers: 0.66 mA at 25 °C, 1.3 mA at 125 °C.
- R308–R311 at 1 % gives ΔT = 1 %/(B/T²): 0.26 °C at 25 °C, 0.41 °C at 100 °C. The note is correct.

**Debug and bring-up headers**
- J301 Cortex 10-pin: 1 VTref = 3V3_MCU, 2 SWDIO, 3/5/9 GND, 4 SWCLK, 6–8 NC, 10 nRESET.
- SW301/C304 on NRST. BOOT0: 10k pull-down plus the TP306 pad.

**U204 (TPS62177)**
- Pins 1 PGND, 2 VIN, 3 EN = VIN (EN absolute maximum VIN + 0.3 V), 4 NC → GND (TI: "recommended to be connected to AGND but can be left floating", so the rev A4 change is correct), 5 FB → GND (fixed-output recommendation), 6 AGND, 7 PG → R208 to 3V3_BUCK, 8 SLEEP (absolute maximum 7 V), 9 SW, 10 VOS, 11 PAD → GND.
- The KiCad footprint WSON-10 EP 0.84 × 2.4 cites tps62177.pdf.
- L201: SRN4018TA-100M, Isat 1.5 A against the 1 A current limit.
- Soft-start: 10 mV/µs into about 50 µF on the rail is about 0.5 A, the 525 mA start-up limit. VIN droop through R201 is about 2 V from a 10 V pack, well above the UVLO falling threshold of 2.9 V.

**U203 (TPS70950DBVR, plain DBV pinout)**
- IN 1, GND 2, EN 3, NC 4, OUT 5 (Table 5-1; not the A/B variants).
- EN left open is allowed: §7.4, "EN is pulled high by a 300-nA current source; therefore, EN can be left floating". The rev A4 fix is correct.
- C205 4.7 µF 25 V 0805 keeps about 3 µF at 5 V, more than the 1.5 µF minimum.

**U201/U202 (INA190, DDF)**
- Pins VS 1, ENABLE 2, REF 3 → GND, GND 4, OUT 5, NC 6, IN+ 7, IN− 8. Inputs are rated to 42 V regardless of VS. ENABLE is driven (jumper plus 100k).
- Full scale: A5 is (5 − 0.04)/(500 × 10 Ω) = 0.99 mA; A1 is 19.8 mA.

**Global labels, levels on both sides**
- CHG_INH: high gives CE = 3.0 V > 1.3 V; reset/off gives 0 V.
- EN_5V1/2: TPS62933 EN rising threshold is 1.21–1.28 V. With the MCU off, Ip 0.7 µA × 100k = 70 mV, so the converter stays off.
- IRQ1/2: VOL 0.4 V at 2 mA.
- GAUGE_BTP: 3.3 V maximum.
- 3V3_SLEEP: 3.3 V against a 7 V absolute maximum.

**Unprogrammed MCU or MCU in reset**
- CHG_INH low (charging allowed), EN_5V off, NTC dividers unpowered, SLEEP high (normal mode), LED off.

**Capacitor voltage stress on PACK_P / VBUS / PPHV / PMID nets (all ≤ 67 %)**
- PACK_P 16.8 V: 25 V parts at 67 %, 50 V parts at 34 %.
- PPHV/AC_SNS_N 20 V: 35 V parts at 57 %.
- VBUS 20 V: C406 50 V (LCSC C20416422 is TCC0805X7R475K500FT, 4.7 µF 50 V X7R 0805, consistent with the value).
- CC lines: 330 pF 50 V C0G.

**LCSC spot-check: pages fetched, MPN and value match**
- C13564, C23185, C91241, C96028, C2044417, C5456183 (out of stock), C2762602, C135802, C173427, C2838894 (15 A / 32 V; 150 A at 32 V, 300 A at 24 V), C22872, C22980, C23260, C122537, C110775, C469660, C2907567 (2512 0R, 1 W), C41349455, C7502694, C13533, C492401, C72043.

**Resistor power at worst case**
- R431/R531 2512 0R (1 W) at 1.7 A: with a typical jumper maximum of 50 mΩ, 1.7² × 0.05 = 0.14 W, well within 1 W. The current rating is not listed on LCSC; check the FOJAN datasheet for ≥ 2 A.
- R424/R427 at 8.5 A (100 W at 12 V, one port): 0.36 W of 2 W.
- R118: 60 mW.
- R409: 2 mW.
- R420: about 6 mW.
- R316–R319 into a short: 3.3 mA.
