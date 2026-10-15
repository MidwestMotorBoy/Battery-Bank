# Reviewer D: cells, gauge and protection; 3V3 and sleep current; system level (rev A7), round 1

**Scope**
- `gauge.kicad_sch`:
    - U101 BQ40Z50-R2 pin by pin;
    - BT101–BT104 and the VC ladder; RS101 and the SRP/SRN filter;
    - Q101/Q102 drive; PBI/VCC/BAT; TS1–TS4;
    - the BTP_INT → Q103 → IRQ_N gauge side; SMBus, J103, SW101, J104;
    - U102/F102: only the changes since review 3, plus C1/C2/P1;
    - the cost-down swaps on this sheet.
- `power.kicad_sch`: TPS62177 3V3 rail, R_MEAS/INA190s, JP201/JP202, HT7550-1.
- System level:
    - power tree and states; back-powering; fault injection;
    - the rev A7 sleep budget;
    - the whole-board BOM pass (411 parts);
    - ERC and the revision log.

**Sources**
- Datasheets (text and tables extracted with PyMuPDF; figures rendered and viewed):
    - bq40z50-r2.pdf (SLUSCS4C) and its TRM bq40z50-r2-trm-sluubk0.pdf (SLUUBK0B);
    - bq2947.pdf, tps62177.pdf (SLVSB35C), ina190.pdf, tps25751.pdf (SLVSH93A);
    - cc2340r5moda.pdf (SWRS349A), tmp1075.pdf, tpd4s201-q1.pdf, m24512.pdf;
    - agm404ap1.pdf, ao3400a.pdf.
- Fetched for this review, saved in `scratch-d/dl/`:
    - **HT75xx-1** Holtek Rev 2.30 (2014), from https://www.farnell.com/datasheets/2047678.pdf;
    - a Chinese-language copy from atta.szlcsc.com;
    - **FNR4030S** Changjiang, from https://datasheet.lcsc.com/datasheet/pdf/a0b12ba9dfe6b9e66b6bb852b7c71c03.pdf (the table was rendered and read).
- LCSC product-page descriptions for all 93 LCSC numbers in parts.txt (`scratch-d/lcsc_desc.tsv`).
- Review inputs: nets.txt, parts.txt, net.xml, erc.txt.
- Board positions from `MonolithDev.kicad_pcb` (pcbnew, read only).
- git diff of gauge, power and top sheets from 07c6e43 (review 3) to HEAD.

**Peer answers relied on**
- **C:** TPD4S201 VPWR 112/160 µA. TPS25751 VIN_3V3 has no documented behaviour between 2.87 and 3.0 V and no switchover to the VBUS LDO.
- **B:** C432/C532 polymer leakage is up to 500 µA each (spec max). B owns the C431/C434/C435 voltage and DC-bias derating.
- **A:** I answered A's BTP, broadcast and SMBus-low questions (BTP_POL/BTP_EN, BCAST, bus-low = SLEEP).

**Summary (round 1):** 0 CRITICAL, 0 MAJOR, 3 MINOR (D-3, D-5, D-6), 4 CONFIG (D-1, D-2, D-4, D-7), 4 DOC (D-8 to D-11), 7 NOTE (D-12 to D-18). D-3 (+DOC), D-4 (+MINOR) and D-11 (+MINOR) carry a second tag.

**After round 2:** counts unchanged, with no grade changes. D-1, D-3 (pack idle ≈ 240 µA), D-4 (1.4 µA is typical) and D-7 (100 kHz) are amended. D-6 and D-7 merge into A-9 and A-6. See "After round 2" at the end.

---

### D-1 [CONFIG] The gauge's default removable-pack mode ([NR] = 0), with PRES tied to VSS, means a latched protection can never clear; the checklist never sets [NR]
- **Where:**
    - U101 pin 16 PRES/SHUTDN is on CELL_N (net CELL_N: `U101.16(PRES/SHUTDN_16)`).
    - DA Configuration [NR] and [IN_SYSTEM_SLEEP]; `bringup-config-checklist.md` §2.5.
- **Evidence:**
    - DA Configuration defaults to 0x12, so NR (bit 2) = 0, "Use PRES, REMOVABLE mode (default)" (TRM 15.2.x, DA Configuration). Verified.
    - With [NR] = 0, every latched protection clears only on a "Low-high-low transition on PRES pin". This covers COVL, OCDL, AOLDL, ASCCL and ASCDL (TRM 2.6–2.7 latch tables, e.g. OCD "Latch Reset([NR] = 0)"). TRM 2.7: "The recovery condition for removable pack ([NR] = 0) is based on the transition on the PRES pin, while … embedded pack ([NR] = 1) is based on the Reset time." Verified.
    - PRES is hard-wired to VSS, so it can never transition. AOLDL is enabled by default (Enabled Protections A = 0xFF, bit 7).
    - So once a latch limit is reached (a PACK_P short on the bench, for example), DSG stays off until the gauge is reset. 3V3 is fed only from PACK_P, so the MCU is also dead. Only USB, J104 (charger powering PACK_P) or the EV2400 can recover it. Inferred: how the gauge treats Latch Limit = 0 is not stated.
    - The checklist sets [IN_SYSTEM_SLEEP] = 1. TRM 5.3.2 describes that bit as "an option for removable packs (that is, DA Config[NR] = 0)". The checklist therefore implicitly keeps [NR] = 0 without saying so.
- **Proposed fix (configuration):** add [NR] to the checklist table with a stated choice.
    - **Preferred: [NR] = 1** (embedded pack, which is what a power bank is). Latches then clear after each protection's Reset time.
        - The sleep-entry row "(OperationStatus()[PRES] = 0 OR DA Config[NR] = 1)" is then met (TRM 5.3.1 table).
        - For the bus condition, keep [IN_SYSTEM_SLEEP] = 1 ("no communication for Bus Timeout"). Its effect with NR = 1 is not stated in TRM 5.3.2, so confirm sleep entry across R105 at bring-up.
        - Alternatively, the MCU enters sleep with MAC 0x0011 SLEEP, which skips the bus-low check (TRM 5.3.1 note 1).
        - Keep EMSHUT_EN = 0: SHUTDN is tied low, so no transition can occur.
    - **Or keep [NR] = 0:** document that latched faults need MAC DeviceReset (or a SHUTDOWN/wake cycle) from the MCU or the EV2400. Firmware must then send it when USB revives the board.
- **Confidence:** high on the TRM text and the netlist. Medium on the board-level consequence, because the Latch Limit semantics at the default of 0 are unconfirmed.

### D-2 [CONFIG] The gauge BTP output idles HIGH if BTP is enabled with its default polarity, which pins the shared IRQ_N low through Q103
- **Where:**
    - U101.15 BTP_INT → Q103 (AO3400A) gate, with R117 470k to CELL_N. Q103 drain is on IRQ_N, shared with U401/U501 I2Ct_IRQ, U302–U306 ALERT, U301 DIO11 and R314 100k.
- **Evidence:**
    - IO Config default 0x00: BTP_EN = 0 and BTP_POL = 0, and the TRM says "0 = BTP pin is asserted low when BTP is triggered (default)" (TRM 15.2.1.6 IO Config).
    - DS 8.3.7: "An internal weak pullup is applied when the BTP feature is active." So with BTP_EN = 1 and the default POL = 0, the pin idles high (VOH ≥ 1.8 V at 10 µA, DS 7.12). Q103 then conducts and IRQ_N is held low permanently. Every other interrupt on the wire-OR is masked, including TMP1075 over-temperature and PD attach.
    - BTP is a latched level. It stays asserted until the host writes BTPDischargeSet() 0x4A or BTPChargeSet() 0x4B (TRM "Battery Trip Point", 12.x). Firmware must therefore clear it before it can see other IRQ_N sources.
    - With BTP_EN = 0, R117 holds the gate low and Q103 is off. That is safe.
    - Nothing in `bringup-config-checklist.md` or the circuit description mentions BTP_POL/BTP_EN. Answer sent to A.
- **Proposed fix (configuration):**
    - Add to the checklist: "IO Config: BTP_POL = 1 whenever BTP_EN = 1; after changing BTP_POL, write BTPDischargeSet/BTPChargeSet once (TRM)".
    - Firmware must treat IRQ_N as level-sensitive and service BTP by rewriting the threshold. Or leave BTP_EN = 0 and poll RSOC.
- **Confidence:** high (TRM default table, DS 8.3.7, netlist).

### D-3 [MINOR + DOC] The rev A7 idle budget is about 235 µA, not 161 µA; `power-budget.md` is still rev A5 (STM32, TPD2S300, NTC dividers)
- **Where:** 3V3 rail loads, R313, U302–U304, U405/U505 VPWR, C432/C532; `docs/devboard/power-budget.md`.
- **Evidence (3V3 idle, typ, verified per datasheet line):**

| Load | Source | 3V3 idle |
|---|---|---|
| 2 × TPS25751 sleep | DS 6.7, 56 µA each | 112 µA |
| 2 × TPD4S201 VPWR (C's item) | -Q1 DS 5.7, 112 typ / 160 max | 224 µA (320 max) |
| 3 × TMP1075 at the default rate (R1R0 = 00) | DS 6.5, 10 typ / 20 max | 30 µA (60 max); ≈ 8 µA at R1R0 = 11; ≈ 1 µA in shutdown/one-shot |
| CC2340 standby + BLE advertising | SWRS349A 7.9, 0.71 µA + adv. *est.* | ≈ 15 µA |
| Gauge SMBC/SMBD internal 1 MΩ pull-downs | DS 7.11 RPD | 6.6 µA |
| R313 470k while DIO21 holds sleep mode | 3.3 V / 470k | 7 µA |
| 2 × M24512 standby | | ≤ 4 µA |
| **Total** | | **≈ 400 µA typ** (≈ 525 µA max), against 147 µA in the A5 doc |

- **At the pack:**
    - The 3V3 branch is 400 µA × 3.3/(0.8 × 14.4) + 4.8 µA TPS62177 sleep IQ ≈ **119 µA** (was 47).
    - Total idle: gauge 75 + U102 1–2 + chargers 34 + bucks 4 + 119 ≈ **235 µA typ**. That is about 2.9 %/month of 5.8 Ah, against 161 µA / about 2 %/month in the doc.
    - Plus the C432/C532 polymer leakage (B's MINOR): ≤ 500 µA each at rated voltage, typically far less at 16.8 V, and only while the FETs are on.
- The doc is stale:
    - its datasheet row lists the STM32WB15;
    - it still has "2 × TPD2S300 ≈ 8.5 µA", "NTC dividers (5 × 10k)" and "CHG_INH (PB8)";
    - it has no R313 or TMP1075 line.
- **Active 3V3 (for the record):**
    - CC2340 +8 dBm TX 10.7 mA + idle 1.2 (7.10/7.9);
    - LED ≈ 3.9 mA;
    - 2 × TPS25751 active sink up to 6 mA each (DS 6.7);
    - I2C and I2Cc pull-ups when low ≈ 4 mA; STAT1/STAT2/PG 10k pull-ups when low ≈ 2 mA; CE pull-ups 0.14 mA.
    - Total about **38 mA peak**, well inside the TPS62177's 500 mA. R201 drops about 0.14 V at 10 V in.
- **Proposed fix:**
    - Rewrite `power-budget.md` for rev A7 with the table above.
    - Make "TMP1075 in shutdown/one-shot" a firmware requirement. It saves about 29 µA.
    - Keep C's TPD4S201 item as the main driver.
    - Hardware is acceptable as is. The TPD4S201 must stay powered for CC attach detection (C).
- **Confidence:** high on the per-part datasheet numbers. Medium on the CC2340 advertising average (estimated) and the 80 % sleep-mode efficiency.

### D-4 [CONFIG / MINOR] TPS62177 sleep mode (IOUT_SLEEP 15 mA) can be exceeded by the CC2340 at +8 dBm with the LED on, or by a PD attach
- **Where:** U204 pin 8 ~SLEEP on net 3V3_SLEEP (U301 DIO21, R313 470k to 3V3).
- **Evidence:**
    - TPS62177 DS 7.5: IOUT_SLEEP = 15 mA (SLEEP low, 3.3 V, 10 µH). DS 8.4.4: an overload in sleep mode droops VOUT "until the PG pin goes Low", then the device returns to normal mode. PG falling is 87–93 % (2.87–3.07 V).
    - In sleep mode with no cable, the peak load is about 16 mA: CC2340 TX +8 dBm 10.7 mA (SWRS349A 7.10) + idle ~1.2 mA + LED (R306 330 Ω, KT-0603R Vf ≈ 2.0–2.4 V) 2.7–3.9 mA. At 0 dBm with the LED off it is about 6.7 mA, which is fine.
    - On an attach, a TPS25751 goes to 3–6 mA active (DS 6.7) within milliseconds, before the MCU can raise SLEEP. C confirms the 2.87 V dip is below the TPS25751's 3.0 V operating range but above its 2.44–2.64 V UVLO. Nothing resets, but the liquid-detect "dry" reading drops about 10 % (C's CONFIG).
    - R313 at 470k against the 1.4 µA max SLEEP pull-down (DS 7.5 ILKG_SLEEP) gives ≥ 2.75 V, which is above VH 0.9 V. The rail boots in normal mode. Also, "Sleep mode is not entered until soft-start is complete" (DS 8.4.4). Verified.
- **Proposed fix:**
    - Firmware rules in the checklist (A's MCU side):
        - in TPS62177 sleep mode, keep the LED off and TX power at ≤ +4 dBm (7.9 mA);
        - leave sleep mode on any IRQ_N edge;
        - never enter sleep mode with a cable attached (already in the checklist).
    - Optional hardware: none needed. The PG fallback keeps the rail above every UVLO on the 3V3 rail.
- **Confidence:** high on the datasheet limits. Medium on how often the overlap occurs.

### D-5 [MINOR] J104 bench input has no overvoltage limit; a bench supply above about 25 V exceeds the 25 V PACK_P parts, and above 28–30 V several ICs
- **Where:** J104 → D104 SS34 → PACK_P.
- **Evidence (abs max / recommended on PACK_P):**
    - C432/C532 polymer and C431/C434/C435 (5xx) MLCCs: 25 V;
    - TPS62177 VIN: 28 V operating, 30 V abs max (DS 7.1/7.3);
    - U101 PACK pin: 26 V recommended, 30 V abs max (DS 7.1/7.3);
    - HT7550-1: 30 V operating, 33 V abs max (Holtek Rev 2.30 p.2 and p.7).
    - D104 only blocks reverse polarity. The checklist says 12–16 V, but nothing on the board says so. A bench supply left at 24 or 30 V from another job is a credible mistake.
- **Proposed fix:**
    - Silkscreen "12–16 V, current-limited" at J104.
    - Optionally a 20 V TVS (e.g. SMAJ18A) after D104. That is cheap, and D104 limits the TVS current to the bench limit.
- **Confidence:** high on the ratings. The likelihood is a judgment call.

### D-6 [MINOR] A USB-UART adapter on J302 back-powers the whole 3V3 rail through the CC2340 RX pin when the board is off
- **Where:**
    - J302.2 UART_RX → U301.17 DIO20 directly. There is no series resistor (net `/MCU and NTCs/UART_RX`: J302.2, U301.17 only).
    - 3V3_MCU → R301 0R → 3V3 → U401/U501 VIN_3V3, U302–U304, the gauge SMBus pull-ups and others.
- **Evidence:**
    - A 3.3 V adapter idles TX high. With 3V3 down, current flows through the DIO20 ESD clamp into VDDS and on to every 3V3 load.
    - SWRS349A abs max: DIOx ≤ VDDS + 0.3 V (line 1485). With VDDS = 0 this is violated.
    - The partially powered rail (≈ 2–2.5 V) sits near the TPS25751 VIN_3V3 UVLO (2.44–2.76 V, DS 6.6) and the CC2340 BOD (1.67 V). That gives undefined, brown-out-like states, and it can upset the TPS25751 dead-battery decision at the next VBUS attach (C's area: DBfg).
    - J301 (SWD) is fine: its pin 1 is a VTref sense.
- **Proposed fix:**
    - 1k in series in UART_RX (and TX) at J302.
    - Note in the checklist: "connect the UART adapter only with 3V3 up".
    - A owns the pin and should confirm.
- **Confidence:** medium (inferred mechanism, standard clamp-diode behaviour).

### D-7 [CONFIG] The gauge runs SMBus 1.1 at 100 kHz by default ([XL] = 0) on a bus shared with 400 kHz-capable parts
- **Where:** SCL/SDA (U101 via R115/R116, U301, U302–U306, U401/U501 I2Ct).
- **Evidence:**
    - SBS Configuration: "XL (Bit 3): Enables 400-kHz COM mode … 0 = Normal SBS bus speed (default)" (TRM 15.2.x SBS Configuration).
    - [BCAST] = 0 by default (same register), so the gauge never masters the bus. The checklist keeps it 0.
    - If the CC2340 runs the bus at 400 kHz for the TMP1075s or TPS25751s, the gauge sees out-of-spec traffic. Whether it can false-match is not specified.
- **Proposed fix:** either run the whole shared bus at 100 kHz (A's firmware), or set [XL] = 1 and keep the bus at ≤ 400 kHz. Add the choice to the checklist.
- **Confidence:** high on the defaults. The risk at 400 kHz is unquantified.

### D-8 [DOC] Top-sheet revision log has no A7 entry, and four title blocks still say rev A6
- **Where:** `MonolithDev.kicad_sch` REVISION LOG text and title blocks.
- **Evidence:**
    - The log ends at A6. That entry still says "U301 consigned" (the STM32).
    - Title blocks: MonolithDev, gauge, power and usb_port all say `(rev "A6")`; only mcu says A7.
    - The gauge sheet did change in A7: Q103 drain moved to IRQ_N, R114 became DNP (git diff 07c6e43..HEAD, `(dnp no)` → `(dnp yes)`), and TP107 moved to IRQ_N.
- **Fix:** add "A7 2026-10-14: CC2340R5MODA (U301), TMP1075 U302–U306 replace TH301–TH305/NTC_EN, IRQ_N wire-OR (R315/R114 DNP), R313 470k fitted, RF match C313–C315/R321". Bump the gauge and top title blocks to A7.
- **Confidence:** high.

### D-9 [DOC] Stale `Notes` properties and sheet notes (BOM pass)
All verified against the current netlist:

| Ref / place | Stale text | Now |
|---|---|---|
| R302 | "TPS25751 I2Ct_IRQ is open drain and needs an external pull-up" | 100k RSTN pull-up for the CC2340 (net NRST) |
| R313 | "DNP: fit to keep the TPS62177 out of sleep mode …" | Fitted 470k (README item 40) |
| R314, R315 | TPS25751 IRQ pull-up only | IRQ_N wire-OR pull-up (R314) / DNP spare (R315) |
| Q103 | "GAUGE_BTP active low", "PA6 allows 4.0 V unpowered", "~2.6 V guaranteed BTP_INT drive" | Net is IRQ_N, the pin is CC2340 DIO11, and DS 7.12 guarantees VOH ≥ 1.8 V at 10 µA (3.5 V at 0 µA) |
| R117 | "10-20 uA BTP source gives 4.7-9.4 V gate" | BTP_INT VOH is at most about 3.5 V (DS 7.12); the gate never sees 4.7–9.4 V |
| TP107 | Value "GAUGE_BTP" | Sits on IRQ_N |
| R435/R535 | "MCU (PB8)", "IWDG reset" | DIO24, WDT |
| R417/R517 | "… unprogrammed or Standby all inhibit" | CC2340 Standby **retains** GPIO output state, so a low CHG_INH keeps charging in Standby. Flag to A (semantics changed) |
| R441/R541 | "TPD2S300 FLT pull-up" | TPD4S201 |
| J102 | "(VSS above VSS)" | Typo: the BT101 can is at VSS |
| C531/C534/C535, R544–R549 (port 2) | Name the port-1 refs (C432, Q401, C412) | Shared-sheet text; say "C432/C532" etc. |
| R127 | Value "0R DNP" plus the DNP flag (parts.txt "0R DNP DNP") | Value "0R" |
| Gauge sheet note 8 | "PA6 takes 4 V unpowered: GAUGE_BTP is active low" | IRQ_N / DIO11 |
| Power sheet note 6 | "MCU PB4 drives it high" | DIO21, plus the R313 pull-up |
| Power sheet note 8 | "U201/U202 are hand-soldered … JLC has no stock" | U202 is JLC-placed (README 14) |
| Power sheet note 10 | "U203 EN … internal 300 nA pull-up … never tie it to LDO_IN" | HT7550-1 has no EN pin (TPS709 text) |
| Sheet name "MCU and NTCs" | Sheetname property | Title block says "MCU and board temperature"; no NTCs remain |
| README item 40 "Not done yet" | "LCSC numbers for U301–U306, C313–C315, R321 and R313" | All present except U301 (TI) and C314 (DNP) |
| README item 37 / checklist §0 | "U301: bought from ST and consigned" / "STM32WB1MMC: buy from ST" | CC2340, TI.com |

- **Fix:** update the Notes and sheet notes as in the right column.
- **Confidence:** high.

### D-10 [DOC] `bringup-config-checklist.md` is still rev A6 (STM32 option bytes, PB4/PB8, Stop2, NTC_EN, IWDG, TH305)
- **Where:** checklist §0 (U301 STM32), §1.4 (option bytes), §4 (PB8, IWDG, Stop2, PB4, NTC_EN, TH305).
- **Evidence:** grep of the file (lines 20, 32, 107, 116–126). Its rev A7 replacements are D-1, D-2, D-4 and D-7 here, plus A's WDT/standby items.
- **Fix:** rewrite §0, §1 and §4 for the CC2340: DIO map, WDT, Standby GPIO retention, R313, TMP1075 shutdown/one-shot and ALERT limits. Add [NR], BTP_POL and [XL].
- **Confidence:** high.

### D-11 [DOC / MINOR] BOM fields: MPN missing on 28 fitted parts; J301 and U301 have no LCSC, no `Sourcing` and no position-file exclusion
- **Evidence (net.xml property scan, fitted and not excluded from the BOM):**
    - **No MPN (LCSC present):**
        - BT101–BT104, D101, Q101, Q102, U101, U204;
        - RS101 (its MPN sits in Notes);
        - C403/C404/C405 and C503/C504/C505;
        - R418/R419/R434 and R518/R519/R534;
        - U401–U404 and U501–U504.
    - **No LCSC, by design and documented:**
        - the pin headers (`Sourcing` holds the LCSC number, position file excluded);
        - U201 (`Sourcing` DigiKey/Mouser).
    - **J301** Samtec FTSH-105: no LCSC, no `Sourcing`, **not** `exclude_from_pos_files`. Its Notes say "Hand-fit, not in the JLC BOM", but the CPL will list it.
    - **U301** CC2340R5MODA: no LCSC and no `Sourcing`. Its procurement path (TI.com, consigned to JLC) lives only in the README and commit 7713eed.
- **Fix:**
    - Fill the MPN fields. The LCSC descriptions in `scratch-d/lcsc_desc.tsv` give the exact MPNs.
    - J301: add `exclude_from_pos_files` and `Sourcing`.
    - U301: add `Sourcing` = "TI.com, consign to JLC".
- **Confidence:** high.

### D-12 [NOTE] HT7550-1 (U203) checked against PACK_P: 30 V operating, 33 V abs max, pinout and caps correct
- Holtek Rev 2.30:
    - p.2: abs max "Supply Voltage −0.3V to 33V"; SOT89 PD 0.5 W.
    - p.3: SOT89 pins 1 GND / 2 VIN / 3 VOUT.
    - p.7 (HT7550-1): VIN max 30 V, VOUT 4.85–5.15 V, IQ 2.5/4 µA, dropout 25/55 mV at 1 mA.
- The netlist matches: U203.1 GND, .2 LDO_IN, .3 5V_AMP. The KiCad SOT-89-3 tab is pad 2 = VIN.
- PACK_P 16.8 V is 56 % of the 30 V operating maximum.
- The JP202 hot-plug ring (review 2 C-3, 23–30 V) stays below 33 V abs max.
    - A rough check: Z0 = √(100 nH / 5 µF effective) ≈ 0.14 Ω. Contact plus ESR of about 50 mΩ gives ζ ≈ 0.18, an overshoot of about 56 %, and a peak of about 26 V.
- VOUT max 5.15 V is below INA190 VS 5.5 V.
- With JP202 open, the INA190 inputs at 16.8 V and VS = 0 are inside abs max: IN± ≤ 42 V to GND, input current ≤ 5 mA (INA190 6.1). Unpowered input leakage is not specified (inferred OK).

### D-13 [NOTE] TPS62177 rail verified
- Pinout DS §6 matches the netlist (1 PGND, 2 VIN, 3 EN, 4 NC→GND, 5 FB→GND as TI recommends for the fixed part, 6 AGND, 7 PG, 8 SLEEP, 9 SW, 10 VOS, EP→GND).
- EN tied to VIN (abs max VIN + 0.3). SLEEP is on a 3.3 V net (abs max 7 V).
- Input range: 4.75–28 V against PACK_P 10–16.8 V. UVLO is 4.6 V rising and 2.9 V falling.
- L201 FNR4030S100MT: 10 µH ±20 %, DCR 0.130 Ω max, Isat 1.95 A min / 2.4 typ, Irms 1.5/1.6 A (Changjiang table, rendered). That is above the 1.2 A maximum current limit. The land (1.1 × 3.7 pads at ±1.5 mm) matches KiCad `L_Changjiang_FNR4030S`.
- C207 22 µF 25 V 0805 X5R plus the rail's other caps (C301 4.7 µF, C403/C503 10 µF each) give about 30 µF effective. That is inside the 10 µH × 22–100 µF stable region (DS Table 2).
- C206 2.2 µF 50 V X7R 1206 matches DS 9.2.2.2.4 "2.2 µF is sufficient".
- R_MEAS: R201 10 Ω 1206 0.25 W drops about 0.14 V at the 38 mA active peak (2 mW).
- CC2340 rising slew 10 mV/µs (soft start) is below its 100 mV/µs limit (SWRS349A 7.3).
- PG has a 100k pull-up to 3V3_BUCK and is unused except at TP205. That is fine: the CC2340 has its own BOD.

### D-14 [NOTE] Power-up and state analysis (inferred where marked)
- **Cells only, fresh gauge:**
    - FETs off (Mfg Status Init 0x0000). PACK_P is isolated, so 3V3 is down.
    - SW101 wakes the gauge through R118 4.7k. Its maximum power transfer is 14.4²/(4 × 4.7k) ≈ 11 mW, below the boot load, so while the button is held the TPS62177 hiccups between its 4.6 V start and 2.9 V stop. PACK stays above VSTARTUP (2.45 V max), so the wake works. Harmless (inferred).
- **USB only, no cells:**
    - Unprogrammed MCU: hiccup loop. CE is low with 3V3 dead, the charger raises PACK_P, 3V3 rises, the hi-Z CHG_INH pulls CE high, the charger stops, and the cycle repeats. This is known: "flash the MCU first, never attach USB with no cells" (review 2 D1, checklist §2).
    - The gauge keeps CHG off with no cells only because Precharge Start Voltage stays at 2.5 V (review 2 A-3). That also stops U102/F102 seeing VC4 at PACK_P (inferred).
- **J104 only, no cells:** the intended flash path. 3V3 is up; FETs are off, so CELL_P is isolated by Q101's body diode.
- **Ship mode (MAC 0x0010):**
    - FETs open. The TPS62177 pulls PACK_P down to its 2.9 V stop, and the residual loads take it below the 3000 mV Charger Present Threshold default (TRM Power:Shutdown), so SHUTDOWN completes.
    - With USB attached it never completes, because PACK_P is held up. That is expected.
- **Brown-out:** CUV opens DSG, PACK_P collapses and the MCU loses power. That is expected.
    - 3V3 falls no faster than about (38 mA + 19 mA active discharge)/30 µF ≈ 1.9 mV/µs at the 38 mA peak, and about 0.7 mV/µs near the 1.7 V BOD.
    - SWRS349A 7.3 asks for ≤ 1 mV/µs falling (inferred OK at the BOD point; flag to A).
- **Cell insertion with no external power:**
    - The gauge (BAT from CELL_P_RAW) and the PACK_P loads return their current to CELL_N, so an empty slot is pulled negative (VCn diode), never above 4.35 V. U102 does not trip (inferred).
    - P1's hazard (an empty slot sees PACK_P minus the cells) needs USB or J104 power, as the checklist and gauge note 15 say. C1/C2/P1 are present in the checklist and gauge note 15. Verified.
- **Back-powering checks:**
    - SMBus pull-ups into an unpowered gauge: SMBC/SMBD are rated −0.3 to 30 V with only 100k/1 MΩ internally (DS 7.1, fig. 6-2), so there is no clamp path. With 3V3 dead, the bus is low, which is the gauge's "SMBus off" state, and the gauge sleeps (DS 8.3.15.1, 9.2.2.2.4).
    - IRQ_N: every source is open drain, with no path.
    - TPS25751 LDO_3V3 → VIN_3V3: the VIN_3V3 switch opens in dead-battery start (DS 8.3.2). No back-feed into 3V3 (inferred from the text).
    - CE, STAT and PG pull-ups to a dead 3V3 sit on inputs or open drains, with no path.

### D-15 [NOTE] Fault injection
- **Reverse cell:** unchanged since review 1 #7 and review 2 N-4. The new U102 inputs add (3.6 − 0.7)/2 kΩ ≈ 1.5 mA through R119–R122. No OV trip.
- **Missing cell:** see D-14.
- **PACK_P short:**
    - Gauge SCD opens Q101/Q102. D103 clamps Q102 VGS.
    - Turn-off avalanche of the cell-wiring inductance: about ½ × 200 nH × (200 A)² ≈ 4 mJ, against the AGM404AP1's 81 mJ EAS (DS Table 1). OK (inferred).
    - R118 limits the SW101 current into the short to 3.6 mA.
- **J104 reversed:** D104 (SS34, 40 V) blocks it. OK. For overvoltage see D-5.
- **IRQ_N high level, leakage worst case** (flag to A for the full sum): AO3400A IDSS is 1 µA at 25 °C and 5 µA at 55 °C, specified at 30 V; it is far lower at 3.3 V. Across 100k, 5 µA is only 0.5 V.

### D-16 [NOTE] ERC triage
- All 8 warnings are U401/U501 GPIO0/1/2/11 (Bidirectional) on the GND net, which carries #FLG105 (Power output). They are benign.
- These GPIOs are configured as inputs (README 35/36; checklist §3), so tying them to GND is per TI (unused GPIO). 0 errors.
- Two ignored checks hide two classes of problem: "Global label only appears once" and "Four connection points". I scanned nets.txt instead.
    - No single-pin nets exist apart from the explicit `unconnected-` pins (U101 LEDCNTLA–C/NC/PCHG, INA190 NC, J103.4, J301.6–8, J303.3), and each of those is a datasheet-allowed no-connect.
    - The two-pin nets are all intentional.

### D-17 [NOTE] Cost-down parts on my sheets, rating against stress
- **C105** CL31B225KBHNNNE: 2.2 µF 50 V X7R 1206 (LCSC) on PBI (≤ 16.8 V, 34 %). Meets DS 9.2.2.2.2.
- **C206** same part on PACK_LP (34 %).
- **C204** CL31A106KBHNNNE: 10 µF 50 V X5R 1206 on LDO_IN (34 %, ring ≤ 30 V = 60 %).
- **C205** CL21A106KAYNNNE: 10 µF 25 V X5R 0805 on 5 V (20 %).
- **D103** C19077412: BZT52C15, SOD-123, 350 mW (LCSC). Same ratings as before.
- **Q103** AO3400A: Vth 0.65–1.45 V (≤ 1.5 V as review 2 asked), VGS ±12 V against BTP ≤ 3.5 V, VDS 30 V against 3.3 V. At VGS ≥ 1.8 V it sinks far more than R314's 33 µA.
- **L201** FNR4030S: see D-13.
- **U203** HT7550-1: see D-12.
- **D301** KT-0603R: Vf 2.4 V per LCSC, so R306 330 Ω gives 2.7–3.9 mA (Notes say about 4 mA; fine).

### D-18 [NOTE] Whole-board BOM pass: package, voltage, dielectric and power
- **Package against footprint:** I checked all 93 LCSC numbers against the footprint size code. Every one matches. Examples:
    - 0402: C307331, C13533, C76950/C76952, C17168;
    - 0603 and 0805 parts as listed;
    - 1206: C12891, C13585, C29823, C50254, C17901/C17903;
    - 1210: C778721;
    - SOD-123/323/523, SMA, SOT-23, SOT-89-3, WSON-8/10, PDFN 3.3, VQFN.
    - C46550465 (D6.3 × L6) sits on CP_Elec_6.3x5.8, which has the same land.
- **Voltage:**
    - Every cap on CELL_*, PBI, the VC/V ladders, PACK_P (other than B's C431/C434/C435 25 V and C432 25 V polymer, "see B"), VBUS (C406 50 V, C450 50 V), VAC (C409 50 V) and PPHV (C449 50 V) is 50 V-rated.
    - AC_SNS_N 35 V parts at ≤ 22.5 V ACOV: 64 % (B/C).
    - 3V3 and 5 V caps are 10–25 V.
- **Dielectric:** C0G on RF (C313/C315), CC (C401/C402), snubbers (C454/C455) and FF (C447). Timing caps (C117 CD, C304, C439) are X7R; that is acceptable for their wide-tolerance uses.
- **Resistor power:**
    - R101–R104 1206 for open-cell current;
    - R118 60 mW in 0603 (100 mW) only while SW101 is held into a short;
    - R201 1206; RS101 2 W at 0.1 W (10 A);
    - R424/R427 2 W at 0.16 W.
- **DNP intent:** consistent everywhere I checked:
    - C109/D102 option; R114/R315; U305/U306 with C311/C312; C201; C314 TBD; C447; R450/C454 and R451/C455; J101; R127.
    - R313 fitted, R440 fitted (D-9 for R313's Notes).

## Checked and correct
- **U101, all 33 pins** against DS Table 6-1 and fig. 9-12:
    - PBI 2.2 µF; VC1–VC4 with 100 Ω 1206 + 0.1 µF ladder to the correct cells; VC4 from CELL_P_RAW;
    - SRP = CELL_N side, SRN = GND side of RS101 (charge positive), 100 Ω + 0.1 µF differential;
    - TS1–TS4 each on a J10x NTC to CELL_N. **No TS input lost its NTC in rev A7.**
    - BTP_INT → Q103 + R117; PRES, DISP, PTC and PTCEN at VSS; LEDCNTLx and NC open (allowed);
    - FUSE → R126 → Q104 gate; VCC 100 Ω to FET_MID; PACK 10k to PACK_P;
    - CHG/DSG 5.1k series with 10 MΩ to the source; BAT via D101 + R105; EP to VSS.
    - Abs max: CHG/DSG 28.8 V < 32 V; PACK 16.8 < 26 V; SMBus 3.3 V; TS ≤ VREG.
- **SMBus:**
    - 4.7k pull-ups to SMB_PU (R312 from 3V3) give 0.7 mA, inside VOL 0.4 V at 1.5 mA.
    - J103 order 1 VSS, 2 SCL, 3 SDA, 4 NC.
    - 100 Ω series resistors R115/R116.
- **Q101/Q102 AGM404AP1:** VGS 10.5–12 V on drive (DS 7.18) within ±20 V; VDS 40 V; avalanche 81 mJ.
- **U102/F102:** no circuit change since review 3 (git diff). C1/C2/P1 are in the checklist and gauge note 15.
- **TPS62177:** see D-13. **HT7550-1:** see D-12.
- **INA190s:**
    - IN+ = PACK_P side, IN− = PACK_LP side; REF = GND; ENABLE via JP201 with a 100k pull-down (abs max 6 V);
    - VS 5 V; outputs through 49.9 Ω to the loops.
- **Power tree:**
    - Every 3V3 load is sourced only via PACK_P → R201 → TPS62177.
    - The gauge is fed from the cells (BAT) and from PACK_P (PACK/VCC).
    - The INA190 supply comes from PACK_P via JP202, ahead of R_MEAS.
- **ERC:** 8 known benign warnings, 0 errors (D-16).
- **LCSC:** all 93 LCSC numbers resolve to the stated MPN and value (`scratch-d/lcsc_desc.tsv`).

## Cross-references agreed with A (during round 1)
- D-6 duplicates A-9, with the same back-power mechanism as A-2. A proposes 1k on both J302.1 and J302.2. Use A-9 as the primary ID.
- D-7 duplicates A-6. A shows 4.7k with about 95 pF fails 400 kHz rise time, so the answer is "keep the shared bus at 100 kHz", not XL = 1. Use A-6 as the primary ID.
- D-4: A's A-8 item 3 already has the LED off in S2. The TX ≤ +4 dBm and exit-on-IRQ_N rules are D's additions.
- TMP1075 shutdown against ALERT: A-4 is primary. The D-3 budget assumes shutdown/one-shot.
- R417/R517/R435/R535 Standby semantics: A agrees (CC2340 §8.11, GPIOs latched in standby). The DOC entries are in A-11 and in D-9.

## After round 2

| Item | Challenge | Response | Final severity |
|---|---|---|---|
| D-1 | A: AMEND. The discharge latches (AOLDL/ASCDL/OCDL) set XDSG only, so CHG stays on and USB can revive PACK_P. The MCU can then send MAC 0x0041 DeviceReset. Every Latch Limit defaults to 0 with undocumented meaning. B and C: no objection. | **Concede and amend.** The consequence is "discharge dead until USB (or J104/EV2400) plus a DeviceReset from firmware", not "dead until gauge reset by hand". Charge latches (COVL/ASCCL) leave DSG on and the board alive. Checklist additions: (1) [NR] = 1 preferred; (2) set every Latch Limit explicitly, non-zero, e.g. TI EVM values, rather than rely on 0; (3) firmware sends DeviceReset at boot when SafetyStatus()[xxxL] is set; (4) bring-up test: a deliberate current-limited short on J104 to learn what Latch Limit = 0 does. | CONFIG |
| D-2 | A: AGREE (matches A-3). B and C: no objection. | Unchanged. | CONFIG |
| D-3 | A: AMEND. TPS62177 figs. 11/12 give about 72–75 % at 0.4 mA from 14.4 V, and the curves already include IQ, so adding 4.8 µA double-counts it. That makes the 3V3 branch about 126 µA at the pack and the total about 240 µA. B and C: AGREE. | **Concede.** Corrected: 3V3 idle ≈ 400 µA typ (525 max). At the pack, 400 × 3.3/(0.73 × 14.4) ≈ 126 µA, with no separate IQ term. Pack idle ≈ **240 µA typ** (≈ 230 µA with the TMP1075s in shutdown), about 290 µA with maximum TPD4S201/TMP1075, plus the C432/C532 leakage line (B-4). | MINOR + DOC |
| D-4 | A and B: 1.4 µA ILKG_SLEEP is the TYP column with no maximum (rendered EC table; I confirmed it in my challenge). C: AGREE, but "keep normal mode whenever a cable could attach" is the safer config. | **Concede the number:** R313/pull-down gives 2.75 V *typical*, not a minimum. The TPS62177 side (VH 0.9 V) is still met even with a 10× stronger pull-down. The CC2340 VIH side belongs to A-1 (CONFIG + MINOR R313). **Amend the fix with C's point:** an attach load arrives before the MCU can react, so firmware should either stay in normal mode (about 17 µA more IQ at VIN, about 5 µA at the pack after conversion) or accept the PG-fallback dip to 2.87 V, which C showed is above every UVLO. Choose at bring-up after scoping 3V3 during an attach in sleep mode. LED off and TX ≤ +4 dBm in sleep mode stand. | CONFIG (+ MINOR) |
| D-5 | B: AGREE. Add the port-stage parts: C431/C434/C435 25 V, C432/C532 polymer 25 V, TPS62933 VIN 30 V. SMAJ18A clamps a current-limited bench supply at about 20–22 V. | **Accept the addition.** The fix stands: silkscreen plus SMAJ18A after D104. | MINOR |
| D-6 | A: duplicate of A-9. | Merge; A-9 primary. | MINOR (as A-9) |
| D-7 | A: duplicate of A-6. XL = 1 alone is insufficient because the rise time limits the bus to 100 kHz. | **Concede.** The fix is "shared bus at 100 kHz, [XL] = 0". Merge; A-6 primary. | CONFIG (as A-6) |
| D-8 to D-11 | A: D-9's extra rows checked correct. No other challenge. | Unchanged. D-9 overlaps A-11; merge the shared rows (R302, R313, R435/R535). | DOC |
| D-12 to D-18 | A: D-14 falling-slew is acceptable (about 0.7 mV/µs near the BOD); C301 → 10 µF is an option for rev 2.0. No other challenge. | Accepted. I add A's C301 option to D-14. | NOTE |

**Final counts (after round 2):** 0 CRITICAL, 0 MAJOR, 3 MINOR (D-3, D-5, D-6/A-9), 4 CONFIG (D-1, D-2, D-4, D-7/A-6), 4 DOC (D-8 to D-11), 7 NOTE (D-12 to D-18). No grade changed. D-1, D-3, D-4 and D-7 are amended in content, and D-6/D-7 merge into A-9/A-6.
