# Schematic review 4: rev A7 team review (2026-10-14)

Fourth review of the MonolithDev schematic, at **rev A7** (`hardware/DevBoard/README.md` item 40). Four reviewers worked in parallel. They then challenged each other's findings in a second round and defended or conceded in a third. The deepest look went to the four change sets no review had covered yet:

- **Item 37:** cost-down.
- **Item 38:** discrete charger FETs.
- **Item 39:** 6-layer board and the TPD4S201.
- **Item 40:** the CC2340R5MODA MCU, the TMP1075 sensors and the shared IRQ_N line.

Everything else got a fresh-eyes pass.

| Reviewer | Scope |
|---|---|
| A | MCU sheet: CC2340R5MODA, RF match, TMP1075 ×5, the shared I2C/SMBus bus, the IRQ_N wire-OR, MCU state analysis |
| B | USB port power stage: BQ25756, PGQ04N070 FETs, L401, sense resistors, capacitor banks, TPS62933 PP5V buck |
| C | USB-C front end and PD: TPS25751, TPD4S201, liquid detection, J401, EEPROM, SMAJ22A, PD-level and connector faults |
| D | Cells, gauge and protection; the 3V3 and sleep-current sheet; power tree, sleep budget, state and fault analysis; whole BOM; ERC |

**Method**

- Every reviewer followed the same steps:
    - pin-by-pin datasheet pass on every IC in scope;
    - net-by-net trace of the exported netlist;
    - ERC triage, power tree, worst-case derating, and state and fault analysis;
    - a BOM pass, and a check of every Notes property.
- The team brief, netlist dumps, per-reviewer findings, challenges and scratch work (fetched datasheets, scripts, page renders) are in [`review4/`](review4/).
- The lead re-checked both majors against the datasheets (see each item).

## Result

| Critical | Major | Minor (hardware) | Configuration / procedure | Documentation |
|---|---|---|---|---|
| 0 | 2 | 20 | 12 | 9 |

Duplicates found by more than one reviewer are counted once. After the follow-up at the end of this report, B-1 is MINOR: **1 major, 21 minor**.

**Nothing is wired wrongly.** The checks that came back clean are listed under "Checked and correct" at the end.

**The two majors**

- **B-1** is a component choice in the cost-down. The high-side charger FETs aren't specified at the gate voltage the BQ25756's bootstrap actually gives them.
- **A-2** is a bench procedure the CC2340 swap made unsafe.

## What the challenge round changed

- **A-1 (DIO21 is the CC2340's bootloader trigger pin): MAJOR → CONFIG** (blocking before the first flash), plus a new MINOR, A-1b.
    - B, C and D showed the trigger is a factory default in the boot configuration (CCFG), which the firmware image always sets. It is not silicon behaviour.
    - D traced the stranded state (CHG_INH high, PP5V off, 3V3 in normal mode) and showed it is safe.
    - A's reset-timing race was withdrawn: the ROM boot takes 350–450 µs, so the pin settles long before it is sampled.
    - What stands is a steady-state margin problem. R313 470k against the TPS62177's 1.4 µA SLEEP pull-down, which is typical with no maximum, gives 0.834 × VDDS against a required 0.8 × VDDS. That is why R313 should become 220k (A-1b).
- **C-1 (TPD4S201 VBIAS cap rated 50 V; the footnote says ≥ 63 V): MINOR → NOTE.**
    - B showed VBIAS is clamped to about 28 V by the part's own ESD clamps.
    - The 63/100 V footnote is about losing capacitance at voltage. A 50 V X7R still keeps more than the 0.04 µF minimum, and TI's EVM uses 50 V.
- **B-1: stays MAJOR, with stronger evidence.**
    - C and D independently confirmed the BQ25756 has no forced bootstrap refresh for a high side held on.
    - D showed that even a *typical* PGQ04N070 can't carry 12.6 A once the gate is down at the 2.7 V refresh minimum.
    - B could not find a 40 V part with on-resistance guaranteed at 2.5 V, so the fix is now split by position (below).
- **A-2: stays MAJOR, broadened.**
    - D found that the EV2400's own 20 kΩ pull-ups inject current into a dead CC2340 even with R312 out. So no "3V3 dead" EV2400 procedure is safe.
    - C added that a half-powered bus during a data-flash write risks corrupting the gauge's configuration.
- **D-1 (gauge removable-pack mode latches faults): narrowed, and a new hazard added.**
    - A showed a discharge latch can be cleared: USB restores PACK_P, then the MCU sends DeviceReset.
    - A also found every Latch Limit defaults to 0, and the TRM doesn't say whether 0 means "disabled" or "latch on the first trip".
- **C-4 (VBUS TVS): stays MINOR, with corrected evidence.**
    - The 35.5 V clamp is a 10/1000 µs rating. A live 20 V hot-plug lands at about 27–29 V, at the 28 V abs max of the TPS25751 and TPD4S201.
    - SMAJ18A was rejected for VBUS: a low-breakdown unit conducts at a legal 21 V PPS voltage. **TVS2200DRVR** is recommended (TI's own pick for the TPS25751).
- **B-2 (FET losses): stays MINOR, with figures revised.**
    - A recomputed each FET position; the split moves but the stage total holds. With B-1's penalty on Q402 the stage is about 3.9–4.3 W at 100 W reverse from a 12 V pack, against the cost-down's 0.5 W per FET.
    - MINOR holds only if TH401/TH501 sits on the high-side FET copper, and B-1 is fixed or IBAT_REV is capped.
- **D-3 (idle budget):**
    - A found a double-counted regulator quiescent current and an optimistic efficiency.
    - The rev A7 idle drain is **about 240 µA typical** (230 µA with the TMP1075s in shutdown, 290 µA at maximum ratings). `power-budget.md` still says 161 µA.
- **B-14 (charging with a blank EEPROM): amended by C.** With a blank EEPROM the TPS25751 never closes PPHV, so there is no USB charging at all. The IAC_DPM risk exists only with a configured bundle that doesn't write the BQ25756 (C-11).
- **Merged:**
    - D-6 into A-9 (UART back-power);
    - D-7 into A-6 and A-8 (bus speed);
    - D-9 into A-11 (stale Notes);
    - B-7 into C-5 (PP5V headroom).

## MAJOR

### B-1. The always-on high-side charger FETs run on a sagging bootstrap gate where the PGQ04N070 isn't specified

- **Where:** Q402/Q502 (battery-side high side); also Q401/Q501 in forward boost.
- **The problem:**
    - In reverse boost (sourcing USB from the pack), the BQ25756 holds Q402 on 100 % of the time at 9–12.6 A (datasheet table 6-1).
    - Its gate is the bootstrap capacitor, which the chip refreshes only when it has fallen to **2.7 / 3.1 / 3.9 V (min/typ/max)** (§5.5, VBTST_REFRESH). The only forced refresh pulse goes to the other high side (§6.3.3.3).
    - The gate therefore sweeps from about 4.0–4.2 V (REGN through D405) down to that threshold, over and over.
    - The PGQ04N070's Rds(on) is specified only at 4.5 V and 10 V gate, and its threshold is 1.0–2.5 V.
    - At a 3 V gate the typical output curve (datasheet fig. 2) needs about 0.4 V across the FET to carry 10 A, roughly 40 mΩ, and saturates around 12–15 A.
    - A part near the 2.5 V threshold maximum, at the 2.7 V refresh minimum, carries only a few amps. It drops out of full conduction and overheats.
    - The Infineon part it replaced had a 2.0 V maximum threshold, so the design had more margin before the cost-down.
- **Lead check:** VBTST_REFRESH 2.7/3.1/3.9 V (bq25756.pdf p.12), VGS(TH) 1/1.8/2.5 V, Rds(on) only at 4.5 V and 10 V (PGQ04N070 p.2), and the fig. 2 curves. **Confirmed.**
- **Fix (hardware), by position:**

| Position | Spec | Candidate |
|---|---|---|
| Q402/Q502 (battery-side high side, held on in reverse) | PDFN3333 pinout S 1–3 / G 4 / D 5–8. Vds ≥ 30 V with spike rating ≥ 36 V (PACK_P ≤ 16.8 V). Vgs(th) max ≤ 1.5 V. Rds(on) ≤ 5 mΩ guaranteed at Vgs 2.5 V. Vgs rating ≥ ±12 V. Qg(4.5 V) ≤ 40 nC. If Qg > 15 nC, C413/C513 go to 0.22 µF. | AOS **AON7520**: 30 V, Vgs(th) 0.5–1.2 V, < 3.1 mΩ at 2.5 V, Qg 37 nC. Listed NRND, so treat it as the spec reference. |
| Q401/Q501 (USB-side high side, held on in forward boost) | Same package and pinout. Vds ≥ 40 V. Vgs(th) max ≤ 2.0 V. Rds(on) ≤ 10 mΩ at 4.5 V. Typical curve showing ≥ 10 A at a 2.7 V gate. | Vishay **SiS488DN** (40 V, Vgs(th) max 2.2 V): usable only with IAC_DPM ≤ 3 A. |
| Q407/Q408 and Q507/Q508 (low sides) | Keep PGQ04N070. They are driven from REGN directly, so the refresh floor never limits them. | — |

- **LCSC stock for the candidates could not be checked** (LCSC search blocked from the reviewer's session). Check in a browser before choosing.
- **Interim config until the FETs change:** IBAT_REV = 11b (5 A). That caps reverse output at about 57 W from a 12 V pack, so the source PDOs must match (20 V ≤ 2.5 A).
- **Bring-up:** scope HG2–SW2 at full reverse load and confirm the refresh behaviour. Ask TI whether any periodic refresh exists.
- **Sources:** [review4/B-findings.md](review4/B-findings.md) B-1 and "After round 2"; C-challenge Q1; D-challenge Q1; `review4/scratch-b/pgq04n070.pdf`, `scratch-b/cand/`.

### A-2. The documented "EV2400 with 3V3 dead" procedure overdrives the unpowered CC2340

- **Where:**
    - `bringup-config-checklist.md` §2 step 4: "With 3V3 down, remove R312 and feed TP308".
    - R312's Notes and the MCU sheet's note 10.
    - The nets: SMB_PU → R304/R305 → SCL/SDA → U301 DIO6/DIO8.
- **The problem:**
    - The CC2340's abs max on any digital pin is **VDDS + 0.3 V** (SWRS349A §7.1). With VDDS = 0, 3.3 V on SCL/SDA is about 3 V over it.
    - About 0.6 mA per line flows through the clamp diodes and lifts the whole 3V3 rail to roughly 1.5–2.5 V. That leaves the TPS25751s, TMP1075s and the CC2340 half-powered on the bus the EV2400 is using to write gauge data flash.
    - The EV2400's own 20 kΩ pull-ups inject about 0.13 mA per line even with R312 removed and TP308 unfed.
    - This is a rev A7 regression: the STM32's PB6/PB7 were 5 V tolerant (DS13258 table 15).
    - A fresh board has its gauge FETs off, so 3V3 *is* dead, and the checklist sends every board through this step.
    - Removing R301 while 3V3 is up does the same thing.
- **Lead check:** the abs-max table (cc2340r5moda.pdf p.12) and the checklist text (line 43). **Confirmed.**
- **Fix (procedure and docs; no hardware change):**
    - Do all EV2400 work with J104 powered, so PACK_P feeds 3V3 through D104. Keep R312 fitted.
    - Hold the CC2340 in reset (SW301, or J301 nRESET) while the EV2400 owns the bus.
    - Rewrite checklist §2 step 4, R312's Notes and sheet note 10. Add "never remove with 3V3 up" to R301's Notes.
- **Sources:** [review4/A-findings.md](review4/A-findings.md) A-2 and "After round 2"; C-challenge Q2; D-challenge.

## MINOR: hardware changes (proposed, not made)

| # | Item | Proposed change |
|---|---|---|
| A-1b | R313 470k against the TPS62177 SLEEP pull-down gives zero guaranteed margin on DIO21's input-high level (see A-1) | R313 → **220k**: 3.02 V typical, and still high with a pull-down 2.7× typical. Costs 15 µA while firmware holds SLEEP low in S2. |
| A-5 | R314 100k on IRQ_N (about 250 mm, 15 pads), routed past both switching stages: thin leakage and noise margin | R314 → 33–47k. Route IRQ_N on an inner layer away from the SW nodes. Enable DIO11 input hysteresis. |
| A-6 | SCL/SDA with 4.7k and about 90–100 pF: rise time about 1 µs, at the TMP1075's limit, so 400 kHz is not possible | R304/R305 → 3.3k. Run the bus at 100 kHz (the gauge defaults to 100 kHz anyway: D-7). Route as a pair on an inner layer. |
| A-7 | J303 pin 2 (IRQ_N) sits next to pin 1 (3V3) with no series resistor: a shunt on 1–2 shorts the rail through every asserting sink | 1k in series at J303.2, or swap pins 2 and 3. Silkscreen "no shunt on 1–2". |
| A-9 (+D-6) | J302 UART has no series resistors: a powered USB-UART adapter back-powers the whole 3V3 rail through DIO20 when the board is off. No ROM UART bootloader option uses J302's TX pin. | 1k in series on J302.1 and J302.2. Note: "connect the adapter only with 3V3 up; recovery is SWD (J301)". |
| A-10 | C314 (Z60) has no value or MPN. C313/C315 are 0402 where TI's characterised match uses 0201. | Give C314 a placeholder (e.g. 1.0 pF C0G GRM1555C1H1R0BA01D), still DNP. Note the 0201 characterisation; retune on the real board anyway. |
| B-2 | Stage losses about 3.9–4.3 W at 100 W reverse from 12 V, against the cost-down's 0.5 W per FET. 150 °C Tj max. | Layout: TH401/TH501 on the Q402/Q407 copper, so the charger's TS stop caps the FET temperature. Fix B-1, or cap IBAT_REV. Correct the cost-down document. |
| B-3 | DNP snubber resistors R450/R451/R550/R551 are 0805 125 mW; the Note's own sizing needs 0.3–0.55 W (the EVM uses 750 mW) | Footprint → 1206 wide-terminal or 2010. |
| B-4 | Battery-side polymer C432/C532 sits permanently on PACK_P, with a datasheet leakage limit of 500 µA each | Measure at bring-up (the Note already asks). Production: a polymer with a µA-class leakage spec. |
| B-5 | Gate-resistor tuning guidance has no upper bound; above about 10 Ω turn-off eats the 45 ns dead time | Add "≤ 4.7 Ω; above that, add a turn-off diode" to the Notes and the README. |
| B-6 | 40 V FETs and 30 V inductors: 58 % stress at the ACOV trip (23 V) and 89 % at the SMAJ22A clamp | Decide together with C-4 (TVS2200). Measure the switch-node ringing; fit the snubbers if needed. |
| C-2 | The TPD4S201 draws 112 µA typ / 160 µA max per port at all times (the TPD2S300 drew about 4 µA). It can't be switched off: unpowered, it presents its dead-battery Rd, so the port could only sink. | Accept on the dev board and record it in the budget (D-3). For production, look at a lower-Iq protector. |
| C-3 | CC capacitance: 330 pF plus 40–120 pF inside the TPD4S201 = up to 466 pF, against the TPS25751's 480 pF maximum | C401/C402/C501/C502 → **220 pF** C0G 0402 (TI's EVM value with this protector), same footprint. |
| C-4 | SMAJ22A clamps at 35.5 V (10/1000 µs); a live 20 V hot-plug lands at about 27–29 V, at the 28 V abs max of everything on VBUS. The fitted LCSC C41376403 is an R+O part, not the Littelfuse part whose datasheet we hold. | D401/D501 → **TVS2200DRVR** (LCSC C523793, JLC extended, about $0.20). Needs a new WSON-6 2 × 2 mm footprint. Optionally keep the SMAJ22A footprint in parallel on the dev board. |
| C-5 (+B-7) | The TPS62933 valley current limit allows about 3.2–3.5 A out, against the TPS25751's 3 A VBUS plus VCONN on PP5V | Accept and test at bring-up (3 A load plus VCONN). Optionally ILIM5V setting 2 and a 5 V ≤ 2.4 A PDO. Production: a 4 A buck. |
| C-6 | Every new source attach (vSafe5V, the attached Rp, VCONN) needs PP5V, which the MCU gates through EN_5Vx. "Sourcing doesn't depend on the MCU" is wrong. | Accept the dependency. CONFIG: restore EN_5Vx first after any reset (PP5V holds up about 16 ms at 5 mA). Fix the docs. |
| C-7 | The PPHV switch has no current clamp: a VBUS short while sourcing 20 V relies on VBUS-UVLO turn-off and the BQ25756's reverse undervoltage stop (about 26 mJ into the switch) | Bench test: a current-limited short while sourcing, checking ACP−ACN stays within ±0.3 V. |
| C-8 | No test pads on CC1/CC2, SBU_FLT, the SBU sense nodes or the liquid-detect gate nets | 1 mm pads on the trace (no stubs on CC), both ports. |
| D-3 | Rev A7 idle drain is about 240 µA typical, not the 161 µA in `power-budget.md` (still rev A5). The 3V3 rail idles near 400 µA: TPD4S201 224, TPS25751 112, TMP1075 30, CC2340 about 15, R313 7. B-4's polymer leakage adds to this. | Rewrite `power-budget.md`. Measure at bring-up. |
| D-5 | J104 has no overvoltage limit: above about 25 V the 25 V PACK_P caps fail first, then the ICs | Silkscreen "12–16 V, current-limited". Optional SMAJ18A after D104 (D104 limits its current). |

Also from D-11: 28 fitted parts have no MPN, and J301 and U301 have no LCSC number, Sourcing note or position-file exclusion. These are BOM fields, not wiring.

## Configuration, firmware and procedure

| # | Item | Setting / rule |
|---|---|---|
| A-1 | **Blocking before the first flash.** DIO21 (3V3_SLEEP) is the default ROM-bootloader trigger (active low) in the SDK's default CCFG. GPIOs latch through Standby and Shutdown. | In SysConfig, select a bootloader setting without the DIO21 trigger, or move it to an unused state. Drive DIO21 high before Shutdown or any deliberate reset. |
| A-3 | IRQ_N joins seven latched level sources, but Standby wakes only on an edge. One stuck source masks the rest. | TMP1075s in interrupt mode. Clear every source at boot (both TPS25751 INT_EVENT1, the gauge BTP, the TMP1075s). Loop in the handler until the line reads high. Never enter Standby with IRQ_N low. |
| A-4 | TMP1075 shutdown and a hardware over-temperature alert while firmware sleeps are mutually exclusive. Until configured they draw 30–60 µA. | Choose per power state, and document it in `mcu-io-power-states.md` and `power-budget.md`. |
| A-8 | CC2340 pin and peripheral settings the hardware depends on | I2C at 100 kHz, IRQ_N input with hysteresis, LED drive, UART RX pull-up, watchdog. Restore EN_5V1/EN_5V2 as the first action after reset (C-6). |
| B-1 | Interim until the high-side FETs change | IBAT_REV = 11b (5 A), and source PDOs ≤ 20 V 2.5 A. |
| B-8 | JEITA with the NTC on the FETs: below about 19 °C the charger drops to 20 % current and needs about 24 °C to leave | **EN_JEITA = 0**, mandatory (T1/T5 stay active). |
| B-9 | The POR VFB_REG regulates 16.70–16.96 V | Write VFB_REG = 0x0F (already in the checklist). Consider 0x0E if samples measure high. |
| C-9 | Liquid-detect thresholds must allow for SBU leakage (≤ 3.2 µA), GPIO leakage and LDO_3V3 sag (about 0.42 V droop on the 100k pull-up). The tool defaults may assume the EVM's 249k. | Set thresholds for 100k / 1M. Wet-receptacle test at bring-up. |
| C-10 | I2Ct_IRQ is latched and its mask comes from the EEPROM | Read and clear INT_EVENT1 on both TPS25751s at start-up. Send a 9-clock bus clear at MCU init. |
| C-11 | Bundle questions Q12/Q13 (the BQ25756 IAC_DPM/VAC_DPM track the PD contract) are not on the checklist | Add them. |
| D-1 | The gauge defaults to removable-pack mode ([NR] = 0) with PRES tied to VSS, so latched faults can't clear by PRES. Every Latch Limit defaults to 0 (meaning undocumented). | [NR] = 1. Set every Latch Limit explicitly to a non-zero value. Firmware sends DeviceReset (0x0041) at boot when a latch bit is set. Do a deliberate current-limited bench short on J104 at bring-up. |
| D-2 | BTP enabled with its default polarity idles high, so Q103 holds IRQ_N low permanently. BTP stays latched until the host clears it. | BTP_POL = 1 whenever BTP_EN = 1, or leave BTP disabled. |
| D-4 | TPS62177 sleep mode (15 mA) is exceeded by +8 dBm TX plus the LED, or by a USB attach. The rail dips to about 2.87 V and recovers; nothing resets. | Stay in normal mode while a cable could attach (about +5 µA), or accept the dip. Decide after scoping 3V3 during an attach. |
| A-2 | (procedure) | See MAJOR A-2: EV2400 work only with J104 powered and the CC2340 held in reset. |

## Documentation

| # | Where | Fix |
|---|---|---|
| A-11 (+D-9) | Stale Notes properties | R302 (now the RSTN pull-up; the note describes a TPS25751 IRQ pull-up), R313 (says DNP; fitted at 470k), R314/R315, R312, R319, R321, Q103, R117, TP107 (labelled GAUGE_BTP, now IRQ_N), R417/R517 and R435/R535 (STM32 PB8, "Standby inhibits"). Gauge sheet note 8; power sheet notes 6, 8 and 10. |
| A-12 | Sheet text and companion documents | Sheet name "MCU and NTCs", the "I2C1" heading, the top-sheet address note. `mcu-io-power-states.md` (STM32 throughout), and README item 40's "not done yet" list. |
| B-10 | Power-stage text | R417/R435 Notes. `circuit-description.md` §7.3/7.4: old polymer, LCSC numbers, diode, CE wiring, TS window, output-cap voltage. The cost-down's impossible "5.5 A, 9 V → 16.8 V" boost point. README item 38's "fully on from REGN". L401/L402 Isat figures are typical, or defined at a 40 % drop. |
| C-12 | R441/R541 Notes | Say TPD2S300; should be "TPD4S201 FLT pull-up … FLT → GPIO3 = Fault_Input_Event (33)". |
| C-13 | C451/C551 Notes | Cite the 28 V clamp and the 0.04 µF effective minimum instead of the 40 V ring (C-1 is now NOTE). |
| C-14 | `circuit-description.md` §7, `power-budget.md` | §7 still names the TPD2S300, its SMAJ22A LCSC number disagrees with the BOM, the ESD paragraph mixes three revisions, it promises ADCIN divider footprints that were removed, and it says "CE pulled low". `power-budget.md` lists the TPD2S300 current. |
| D-8 | Top sheet and title blocks | No A7 entry in the revision log. Four title blocks (top, gauge, power, usb_port) still say A6. |
| D-10 | `bringup-config-checklist.md` | Still rev A6 (STM32 option bytes, PB4/PB8, Stop2, NTC_EN, IWDG, TH305). Rewrite for the CC2340, and add every CONFIG item above. |
| D-11 | BOM fields | MPN on the 28 fitted parts without one. LCSC, Sourcing and position-file handling for J301 and U301. |

## Checked and correct

**MCU sheet (A)**
- U301 pinout against the datasheet and footprint.
- The pin mux: I2C on DIO6/DIO8, UART on DIO18/DIO20, SWD on DIO16/DIO17, and DIO11 wake.
- RF match topology against TI fig. 9-1.
- RSTN R302/C304 against TI's R1/C92.
- The J301 SWD pinout.
- All five TMP1075 address straps (0x48–0x4C).
- No I2C address conflicts: gauge 0x0B, TPS25751 0x20/0x21, TMP1075 0x48–0x4C.
- The reset and unprogrammed state of every MCU-driven net: CHG_INH inhibits, EN_5Vx off, 3V3 stays in normal mode.
- VDDS falling slew.

**Port power stage (B)**
- PGQ04N070 pinout against the shared AGM PDFN footprint.
- BQ25756 pin pass and every programming resistor: ICHG 5.22–5.77 A, ILIM 5.28–5.84 A, ACOV 21.75–23.0 V, FSW 598 kHz, the TS thresholds.
- L401, the sense resistors, the ≥ 80 µF banks and R430 within their ratings.
- TPS62933 design equations. Its output capacitance is 12× TI's typical value, so do a loop and start-up test.
- Port 2 is an exact copy of port 1.

**USB-C front end (C)**
- TPS25751 pin pass, PPHV/PP5V limits, and SafeMode addresses 0x20/0x21.
- TPD4S201 pin by pin, and its footprint against the RGR0020C land pattern.
- Dead-battery wiring and the dead-battery/no-battery boot sequence.
- FLT → GPIO3 as Fault_Input_Event (review 3 H1 carried over).
- Liquid-detect gate pulls (review 3 H2).
- J401 pinout.
- vSafe0V discharge about 24 ms, against 650 ms.
- 5/9/15/20 V source and sink supported.
- EPR, reverse-cable and short-to-VBUS cases analysed (protocol-protected only, about 28 V hardware ceiling).

**Gauge, power and system (D)**
- U101, all 33 pins; no TS input lost its NTC in A7.
- U102/F102 unchanged since review 3; its C1/C2/P1 items are in the checklist.
- HT7550-1: 30 V operating, 33 V abs max.
- TPS62177 pinout, inductor and caps.
- All 93 LCSC numbers resolve to the stated part.
- Every package matches its footprint.
- ERC: 8 known warnings, all benign, 0 errors.

## Follow-up (2026-10-14, after the review)

### B-1 re-graded: MAJOR → MINOR (verify at bring-up)

All four reviewers worked from the datasheet. It documents only the bootstrap-refresh comparator (VBTST_REFRESH 2.7/3.1/3.9 V) and says nothing about how a high side is held on at 100 % duty. TI's own material says more:

- **The chip has an undocumented charge pump.** A TI applications engineer (Ethan Galloway) states on E2E that "the high-side FETs are powered by a charge pump during a 100% duty-cycle". In a BQ25756E thread he says the charge pump works only while the buck or boost side is at 100 % duty, and that the non-E part behaves the same. So the gate does not simply sag to the comparator threshold and get refreshed: the pump holds it up, and the comparator is the backstop.
    - [E2E 1635491](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1635491/bq25756-bq25756-buck-boost-charger-stability-issues-and-unexpected-current-draw), read in full.
    - [E2E 1381108](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1381108/bq25756e-bq25756e), known only from search excerpts; TI blocks automated access.
- **The pump is weak.** In the same thread TI says the high-side FETs "can't have pull down resistors on them". A 10 kΩ gate pull-down draws about 0.4–0.5 mA, so the pump sources less than that. Our high-side gates have no pull-downs (HG1/HG2 connect only to R444/R446 and the gate). Verified in the netlist.
- **TI's own reference uses the same threshold class as ours.**
    - TI's BQ25756 EVM uses Vishay SiR680LDP at Q1–Q4 (SLUUCT7 schematic). Its Vgs(th) maximum is 2.5 V, the same as the PGQ04N070's.
    - When a user's FETs had a 2.6–3.6 V threshold, TI called that a potential problem and suggested SiR680LDP or SiR880BDP.
    - So a 1.0–2.5 V threshold is inside what TI designs with.
- **What remains is margin, not a defect.**
    - The pump's output voltage and current are unspecified.
    - The PGQ04N070 is a smaller die than the SiR680LDP (7.2 mΩ typ at 4.5 V against 3.55 mΩ max), so it has less current capability if the gate settles below 4.5 V.
    - The pump also has to supply D405's reverse leakage while Q402 is held on. The diode then sits at about VBAT reverse bias. LRB520S-40: ≤ 1 µA at 10 V and 25 °C, rising steeply with temperature.

**New disposition (B-1, MINOR):**
- Keep the PGQ04N070.
- At bring-up, scope HIDRV2–SW2 (Q402) in reverse boost at full load, hot (board at 70–80 °C), and HIDRV1–SW1 (Q401) in forward boost from 5/9 V. Pass if the gate stays at 4.5 V or more.
- Keep IBAT_REV ≤ 5 A until that measurement is done.
- B's replacement spec (AON7520 / SiS488DN class) becomes the fallback if the gate sags.

Totals after this change: **0 critical, 1 major (A-2), 21 minor.**

### Storage and the idle drain (added after the review)

| | Pack drain | Effect |
|---|---|---|
| Idle (FETs on, 3V3 up, both ports armed) | about 240 µA typ, 290 µA max, plus C432/C532 polymer leakage (spec max 0.5 mA each, unmeasured) | about 3 %/month typ (+ 1–2 %/month cell self-discharge), up to about 16 %/month if the polymer leakage were at spec max |
| Ship mode (gauge SHUTDOWN, MAC 0x0010) | about 3–4 µA (gauge 1.6 + U102 1–2) | about 0.05 %/month; cell self-discharge dominates |

**Where the idle 240 µA goes:**
- the 3V3 branch, about 126 µA at the pack: two TPD4S201 about 70, two TPS25751 about 35, TMP1075 about 9, the rest about 12;
- the gauge sleeping, 75 µA;
- the two BQ25756 battery-side Iq, 34 µA;
- U102 and the bucks, about 6 µA.

**New CONFIG item S-1: gauge Shutdown Voltage.**
- The default is **1750 mV/cell** (TRM §5.4 and 15.5.2.1), and the checklist doesn't set it.
- In idle, the pack runs down to CUV. DSG then opens and the board goes dark, but the gauge (75–336 µA) and U102 keep drawing from the cells until the lowest cell reaches 1.75 V. That takes weeks to a few months, and leaves the cells deeply over-discharged.
- Fix:
    - Set Shutdown Voltage to about 2700 mV, below CUV, so CUV still trips first, but well above damage.
    - Firmware enters ship mode (MAC 0x0010) on an app command, after two weeks with no cable or button activity, or at RSOC ≤ 5 %.
    - USB charger attach or SW101 wakes the board. A phone plugged in can't wake it, because the port is unpowered and the TPD4S201 presents only Rd.
    - Store at 40–60 % SOC. EVE rates storage at shipping SOC for 1 year at −20 to 25 °C.
- **Decided (2026-10-14):**
    - Shutdown Voltage is 2700 mV.
    - Ship mode is entered by an app command, after two weeks with no cable or button activity, or at RSOC ≤ 5 % (decided 2026-10-15).
    - A USB charger or SW101 wakes the board.
    - Boards are stored at 40–60 %.
    - Recorded in `bringup-config-checklist.md` (gauge table, §4 and §5) and `mcu-io-power-states.md` (state S5).

## Status

- **Applied in rev A8 (2026-10-14, `hardware/DevBoard/README.md` item 41):** A-1b, A-5, A-6, A-7, A-9, A-10, B-3 (1206 0.66 W; the 2010 didn't fit), C-3, C-4 (TVS2200DRVR) and C-8. The board is synced.
- **Decided:** S-1 (Shutdown Voltage 2700 mV, ship mode), and B-1 (keep the PGQ04N070; gate-drive test at bring-up). Both are recorded in the checklist.
- **Closed in rev A8 part 2 (2026-10-14, `hardware/DevBoard/README.md` item 42):** A-2 (procedure, Notes and sheet note), D-5 (D105 SMAJ18A on J104), all DOC items (A-11, A-12, B-10, C-12–C-14, D-8–D-11), and every CONFIG item, now written into `bringup-config-checklist.md` and `mcu-io-power-states.md`.
- **B-4 closed (2026-10-15):** C432/C532 changed to the Panasonic EEH-ZA1E101XP hybrid polymer: same 100 µF and 30 mΩ, leakage limit 25 µA instead of 500 µA (`hardware/DevBoard/README.md` item 43).
- **Left to bring-up:** the MINORs that are measurements or production choices (B-2, B-5, B-6, C-2, C-5–C-7, D-3), each with a line in the checklist §5.
- **Open decisions:** J301's replacement header. (Ship-mode SOC threshold: 5 %, decided 2026-10-15.)