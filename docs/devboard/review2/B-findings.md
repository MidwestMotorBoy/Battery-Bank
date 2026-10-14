# Reviewer B findings: usb_port.kicad_sch (port 1 = 4xx, port 2 = 5xx), first pass

Scope: TPS25751D U401/U501, BQ25756 U403/U503 + power stage, TPS62933 U404/U504, connector/ESD/TVS, EEPROM, root straps R1–R4.
Sources: nets.txt, parts.txt, sheet text, datasheets in `datasheets/`. I extracted them with `pdftotext -table`, which keeps the table columns. Section and table numbers below are the printed ones.

**Summary: CRITICAL 0, MAJOR 0, MINOR 8 (B-17 joint with C), NOTE 9.**
Round 2 amendments: B-3 has real datasheet numbers (lower risk, still MINOR; replace with LRB520S-40T1G, C132124). B-5 worst case is now 75 µF, using A's rendered DC-bias curve. B-1 now argues A-1 is MINOR.
I found no board-damaging or non-functional error in the port sheet.
- The one MAJOR-level issue that touches my scope is dual-port 100 W sourcing with no MCU. It is Reviewer A's item; I sent supporting evidence: per-port reverse-mode limits, IBAT_REV POR = 20 A, and the fact that CE has no effect in reverse mode.
- B-1 below is the port-side half of it.

---

### B-1 [MINOR] CHG_INH (CE) cannot stop reverse/source mode; nothing independent of the TPS25751 stops a port from draining the pack
- **Where:** CHG_INH → R435/R535 → CE_N (U403.7/U503.7). The sheet note 11, README item 18 and firmware item 12 describe it as the MCU's independent inhibit.
- **Evidence (bq25756 SLUSEN5A):**
  - §6.3.6 lists the reverse-mode enable conditions: SRN > 3.8 V, DRV_SUP in window, EN_REV = 1, TS in the BHOT/BCOLD window. CE is not among them.
  - §6.3.6 also says that once running, reverse mode continues down to VBAT = 2.5 V (SRN), which is 0.6 V/cell for 4S.
  - CE only appears in the charge-enable conditions (§6.3.4: "EN_CHG = 1 and CE pin is LOW").
  - §6.3.3.6: HIZ (EN_HIZ = 1 or ILIM_HIZ > VIH_ILIM_HIZ = 3.7 V min, §5.5) stops switching in reverse mode as well.
  - EN_REV is reset by WATCHDOG (Table 6-22), but the TPS25751, not the MCU, services the watchdog.
- **Effect:**
  - When firmware item 12's triggers fire (gauge silent or misconfigured, FET stuck), CHG_INH stops charging only.
  - A port that is sourcing keeps discharging the pack, with only the gauge (OCD/CUV) and F101 behind it.
  - The MCU's only other lever is I2C to the TPS25751 (it is on the same SDA/SCL), so the "second layer" for discharge is software over I2C, not the hardware line it is described as.
  - It also means CHG_INH does nothing for Reviewer A's both-ports-at-100-W case.
- **Arithmetic:**
  - The ILIM_HIZ pin limits the USB side in both directions. bq25756 Table 7-6 (Fig 7-18) lists "Reverse Mode current regulation (IAC_REV): HW limit" from the ILIM resistor.
  - KILIM = 48–52 A·kΩ at 2 mΩ, so 19.2–20.8 A·kΩ at 5 mΩ. With 3.6 k ±1 % that is 5.28–5.84 A, so up to ≈117 W per port at 20 V.
  - On the pack side that is 2 × 117 / 0.93 / 12 V ≈ 21 A with both ports. IBAT_REV POR = 00b = 20 A (Table 6-50).
- **Proposed fix:**
  - (a) Document that CHG_INH is charge-only.
  - (b) Firmware/EEPROM: the bundle defaults must be safe without the MCU. That means PDOs ≤ ~45–60 W per port and IBAT_REV = 10 A (or 5 A) written by the TPS25751 config. This is A's MAJOR; I support it.
    - AMENDED in round 2: I now argue A-1 should be MINOR. The gauge's default AOLD (19.4 A, 31 ms, an AFE hardware comparator) and OCD2 (8 A, 3 s) bound the overload. See B-challenge.md.
    - The cleanest no-MCU fix is per-port bundles. Each TPS25751 has its own EEPROM, so USB1 can be 100 W and USB2 20–30 W, which builds the product rule into hardware.
  - (c) Optional hardware: let the MCU force HIZ on both chargers. VIH is 3.7 V, so 3V3 can't do it directly, and REGN collapses in HIZ, so REGN can't hold it there either. A small PMOS from PP5V or a PACK_P-derived 5 V clamp, gated by an NMOS from PB8, would work. Probably rev 2.
- **Confidence:** high on the datasheet facts (CE is not a reverse-mode condition; HIZ stops reverse); medium on the severity judgement.

### B-2 [MINOR] X5R MLCCs at the FETs are rated to 85 °C, but the charger's TS hot cutoff is 94.5 °C board temperature at the same spot
- **Where:** C420/C423/C424/C427 (GMK325BJ226MM, X5R) and C431/C434/C435 (TMK325ABJ476MM, X5R), and the 5xx equivalents. They straddle or sit directly behind Q401/Q402. TH401/TH501 is "beside FETs" (parts.txt).
- **Evidence:**
  - gmk325bj226mm.pdf: "Operating Temp. Range (EIA) −55 to +85" (X5R). TMK325ABJ476MM is also X5R.
  - The TS network (R415 1.8 k, R416 5.6 k, 10 k B3435) with TS_T5 POR = 10b = 34.375 % (bq25756 Table 6-24) suspends charging only at 94.5 °C.
  - In reverse mode, BHOT POR = 01b = 34.2 % (Table 6-26) gives the same ≈ 95 °C.
- **Arithmetic:**
  - TS ratio = Rp / (1.8 k + Rp), with Rp = 5.6 k ∥ R_NTC.
  - At 34.375 %: Rp = 0.943 k → R_NTC = 1.134 k → T = 1 / (1/298.15 + ln(0.1134)/3435) = 367.7 K = 94.5 °C.
  - The capacitors can therefore legitimately run 10 °C above their rating before anything trips. The firmware 20 W throttle exists but depends on the MCU.
- **Proposed fix:**
  - Config: TS_T5 = 00b (41.2 %) gives a hot cutoff at about 81 °C. Check: Rp = 1.261 k → NTC 1.628 k → 80.7 °C. Set BHOT = 00b (37.7 %), about 87 °C.
  - Or move the FET-adjacent MLCCs to X7R (125 °C). The 22 µF 35 V 1210 X7R is a different, less derated part; check stock.
- **Confidence:** high on the ratings and math; medium on whether the real board temperature at the capacitors gets near TH401's reading.

### B-3 [MINOR] Bootstrap diodes D404/D405/D504/D505 (LRB521S-40) are ultra-low-VF parts with high reverse leakage, reverse-biased at about VAC for most of each cycle
- **Where:** D404/D405 anode on DRV_SUP, cathode on BTST1/BTST2 (Net-(D404-K), Net-(D405-K)). Same on port 2.
- **Evidence:**
  - LRC LRB521S-40T1G datasheet (LCSC C135802, via search summary; the PDF itself is not in `datasheets/`): IR max 20 µA at 10 V and 90 µA at 40 V (25 °C), Tj max 125 °C, 150 mW, Rth ≈ 667 K/W (second-source sheet).
  - Orientation, rating and source are correct: pad 1 = K on BTST. Reverse voltage is BTST − DRV_SUP ≈ SW, up to about 22.5 V (ACOV) plus ringing, so 40 V gives about 56 % before ringing. That is fine.
- **Arithmetic (order of magnitude):**
  - At 20 V the 25 °C leakage is about 40 µA.
  - Schottky leakage rises about 2× per 10 °C, so at Tj ≈ 90–100 °C it is ×100–200, about 4–8 mA.
  - Buck from 20 V, HS1 on about 85 % of the time: P ≈ 20 V × 6 mA × 0.85 ≈ 0.1 W, which is +68 °C at 667 K/W. That is thermal-runaway territory in a hot corner.
  - It also drains the 0.1 µF bootstrap cap: 6 mA × 1.6 µs / 0.1 µF ≈ 0.1 V per cycle. That is tolerable; the refresh comparator covers it.
- **Proposed fix:**
  - Use a low-leakage Schottky with ≥ 40 V rating. Candidates: LRB520S-40T1G (C132124, LCSC lists about 1 µA, needs a datasheet check), or a BAS40/BAT46-class diode.
  - Trade-off: higher VF at the refresh peak. At VAC = 5 V, REGN is 4.35 V min and R420 drops about 0.15 V, so the bootstrap reaches only about 3.6–3.9 V against VBTST_REFRESH 2.7–3.9 V (bq25756 §5.5). Keep VF ≤ 0.4 V at about 50 mA.
  - At minimum, measure D404's case temperature at 20 V / 5 A charge on the bench.
- **Confidence:** medium. The leakage figures come from a summary of the LRC sheet; I could not download the PDF.
- **AMENDED in round 2:** I now have the real LRC datasheet (LCSC C135802 PDF, "Rev.O", saved in B_dl/) and the Dowo second-source sheet. Corrections:
  - **LRC ratings:** VR 40 V, IO 200 mA, IFSM 4 A, **Tj max 125 °C**.
  - **LRC leakage:** IR ≤ 20 µA at 10 V and ≤ 90 µA at 40 V (25 °C). The IR dispersion map gives a typical 6.86 µA at 40 V.
  - **LRC VR–IR curves:** read at the right-hand end, about 30–40 V: Ta 75 °C ≈ 10² to 10³ µA, Ta 125 °C ≈ 10³ to 10⁴ µA. Tick-label reading, so treat as ±½ decade.
  - **Dowo sheet:** RθJA 667 K/W, PD 150 mW, and its reverse curve at Ta = 100 °C approaches 1 mA.
  - **Actual reverse voltage:**
    - D404 sees VAC (≤ 22.5 V) whenever HS1 is on. That is about 85 % of the time in buck from 20 V, and 100 % in boost mode, where the buck leg sits with HS1 on.
    - D405 sees VBAT (≤ 16.8 V) whenever HS2 is on, which is 100 % of the time in buck mode.
    - So the reverse bias is effectively DC, not 50 % duty.
  - **Corrected heating at 20 V:** about 0.2–0.5 mA at 85 °C and about 1 mA at 100 °C → 4–20 mW → +3 to +13 °C self-heating at 667 K/W. Runaway needs about 100 °C local ambient with a max-leakage part, not the 85–90 °C I implied. Tj max is only 125 °C.
  - **Severity:** still MINOR, but lower risk than first stated.
  - **Recommended part:** LRB520S-40T1G (LRC, C132124). Same SOD-523 footprint, VR 40 V, IR ≤ 1 µA at 10 V and ≤ 10 µA at 40 V (LRC "Low IR" sheet, chipdip DOC013491952). That is 9–20× lower leakage. VF ≤ 0.55 V at 100 mA, against 0.45 V; at the 10–50 mA bootstrap refresh current the difference is about 0.1 V.

### B-4 [MINOR] Worst-case ICHG hardware ceiling (5.17–5.83 A) exceeds the EVE 1C maximum (5.6 A)
- **Where:** R413/R513 9.1 k 1 %, R427/R527 5 mΩ 1 %.
- **Evidence:** bq25756 §5.5 KICHG = 48 / 50 / 52 A·kΩ at RBAT = 5 mΩ. EVE 58E §3.4: "Maximum Charge 5.6A(1C) … (not for cycle life)".
- **Arithmetic:**
  - Maximum: 52 / (9.1 × 0.99) = 5.77 A, and with RBAT −1 % it is 5.83 A.
  - Minimum: 48 / (9.1 × 1.01) / 1.01 = 5.17 A.
  - The ceiling is reached only when ICHG_REG ≥ the pin value. ICHG_REG POR is 0x190 (20 A) and is reset by WATCHDOG, so it matters exactly when the configuration did not take.
  - Gauge OCC1 ≈ 6 A catches it only after seconds.
- **Proposed fix:** R413/R513 = 9.53 k 1 %. Maximum = 52 / (9.53 × 0.99) / 0.99 = 5.57 A ≤ 5.6 A; nominal 5.25 A.
- **Confidence:** high. This is a margin issue only; the first review accepted "≈1C".

### B-5 [MINOR] USB-side bulk meets the BQ25756 80 µF minimum only nominally; with tolerance and temperature it is about 77 µF
- **Where:** AC_SNS_N bank: C420/C423/C424/C427 (4 × 22 µF 35 V X5R 1210) and C421 (68 µF polymer).
- **Evidence:**
  - bq25756 §5.3: CIN ≥ 80 µF "minimum value after derating". In reverse mode this bank is the output capacitance.
  - The README item 16 figure "≥ 88 µF at −20 %" applies the tolerance to the polymer only.
- **Arithmetic:**
  - MLCCs at 20 V, using the design's own 8.5 µF each: 34 µF.
  - −20 % tolerance on everything: 27.2 + 54.4 = 81.6 µF.
  - X5R at 85 °C (about −15 %): 23.1 + 54.4 = 77.5 µF, which is below 80 µF.
  - The battery side is fine: 36 + 100 µF, ≥ 109 µF in the same worst case.
- **Proposed fix:** a fifth 22 µF MLCC (or a DNP pad for one), or a 100 µF 35 V polymer for C421/C521.
- **Confidence:** medium. The 8.5 µF DC-bias figure is the design's own; I couldn't read the curve values from the Taiyo Yuden PDF text.
- **AMENDED in round 2:** Reviewer A rendered the GMK325BJ226MM DC-bias plot.
  - It shows −69 % at 20 V, so 6.8 µF per part, and only −7 % at 85 °C.
  - Worst case: 4 × 6.8 × 0.8 × 0.93 + 54.4 = 20.2 + 54.4 ≈ 75 µF, against 80 µF. The conclusion stands, with a larger shortfall.
  - Reviewer C rendered the same plot and read −73 % at 20 V, 5.9 µF per part, which gives about 72 µF worst case. C also reads 8.5 µF as the 15 V value. The two renders differ by a few percent; take 72–75 µF.
  - Fix changed: a fifth MLCC reaches only about 77 µF. **Use a 100 µF 35 V polymer for C421/C521**, about 98 µF worst case.

### B-6 [MINOR] PPHV pins have no local decoupling, and all bulk sits on the converter side of both sense resistors (TI asks for a split)
- **Where:**
  - PPHV net: only C409 (1 µF, the BQ25756 VAC cap) and TP402. The bank is behind R424 (5 mΩ) at Q401.
  - VBUS: C406 4.7 µF plus D401, no HF caps.
  - BAT side: all caps on BAT_SNS_P, none on VBAT_SYS.
- **Evidence:**
  - tps25751 §9.4.1.2.1 Fig 9-26: PPHV has C12/C13 22 µF + C14 0.1 µF, and §9.4.1.2.2.3 says "Place the PPHV decoupling capacitors … as close as possible to TPS25751D".
  - §9.4.1.2.2.4: four 10 nF caps plus the TVS "as close as possible to the connector VBUS pins".
  - bq25756 §7.2.1.2.5/6: "Given total bulk input capacitance, it is recommended to distribute equally on either side of RAC_SNS" (and likewise RBAT_SNS). Fig 7-18 shows 80 µF on each side.
- **Effect:**
  - The TPS25751's PPHV switch and its fast OVP/RCP comparators see the PCB inductance to the remote bank.
  - When sourcing through PPHV, the switch-side node has only 1 µF locally.
  - Expect more ringing on PPHV/VBUS at load steps and unplug, and possible nuisance RCP/OVP.
- **Proposed fix:**
  - Add 0.1 µF + 10–22 µF 50 V at the U401/U501 PPHV pins (can be DNP pads). PPHV total must stay ≤ 100 µF-equivalent per README item 15.
  - Add 2–4 × 10 nF 50 V at J401/J501 VBUS.
  - Optionally move one 47 µF to the VBAT_SYS side of R427.
- **Confidence:** medium. These are reference-design deviations, not proven failures.

### B-7 [MINOR] Reverse mode at a low pack runs the inductor above its 20 °C-rise Irms rating, and Q402 at about 2 W
- **Where:** L401/L501 XAL7030-222, Q402/Q502, R430/R530 "Link 10A". Case: sourcing 20 V from a 10–12 V pack.
- **Evidence:**
  - xal7030.pdf: -222 is 2.2 µH ±20 %, DCR 13.7 / 15.07 mΩ, Isat 18.0 A (30 % drop), Irms 10.0 A (20 °C rise) / 12.9 A (40 °C rise).
  - The ILIM hardware ceiling is 5.84 A on the USB side (B-1).
  - iauc45n04s6l063h: RDS(on) 8.5 mΩ max at 4.5 V.
- **Arithmetic:**
  - At the 100 W product rule from a 12 V pack: 100 / 0.94 / 12 = 8.9 A average. That is fine.
  - At the hardware ceiling with no firmware (5.84 A × 20 V = 117 W) from 10 V: 117 / 0.93 / 10 = 12.6 A average.
  - Ripple at D = 0.5 with L −20 % and f −15 %: 10 × 0.5 / (1.76 µ × 507 k) = 5.6 A p-p, so peak 15.4 A < 18 A Isat. OK.
  - Irms ≈ 12.7 A, which is the 40 °C-rise point. Inductor loss ≈ 12.7² × 15 mΩ = 2.4 W.
  - Q402 (both dies): conduction 12.6² × 0.5 × 12.8 mΩ (hot) × 2 ≈ 2.0 W, plus about 0.9 W switching and dead-time loss ≈ 2.9 W in one 5 × 6 package.
  - The R430 link carries 12.6 A against its "10 A" label.
- **Proposed fix:** IBAT_REV = 10 A in the EEPROM config (it then caps this case at about 10 A). Use the firmware cell-voltage-dependent PDO limit. Measure the L401/Q402 temperature at bring-up.
- **Confidence:** medium-high (arithmetic from datasheet values).

### B-8 [NOTE] TPS25751D straps, addresses and dead-battery mode: verified
- **Port 1:** R1 (0 R) LDO_3V3 → ADCIN1 gives decoded value 7; R2 ADCIN2 → GND gives 0.
- **Port 2:** R3 and R4 tie both ADCINs to GND, decoded 0/0.
- **tps25751 Table 8-6:** (7, 0) is SafeMode, index #1 (0x20); (0, 0) is SafeMode, index #2 (0x21). The ADCIN1 column order was recovered with `pdftotext -raw`: 7 5 2 1 7 3 4 3 7 0 6 5 against ADCIN2 5 5 0 7 3 3 0 7 0 0 0 7.
- **No collisions:** gauge 0x0B on the main bus; each private I2Cc bus has the BQ25756 at 0x6B and the EEPROM at 0x50 (ID page 0x58).
- **Port separation:** only GND, PACK_P, 3V3, SDA, SCL and CHG_INH are shared between ports. IRQ1/IRQ2 and EN_5V1/EN_5V2 map correctly.
- **Fused pads:** footprint pads 20/23/32/34 are the PPHV/VBUS_IN/VBUS/PP5V groups. DRAIN 15/30/EP40 are floating together, as TI requires.
- **Capacitors vs tps25751 §6.4:**
  - C405: 10 µF 10 V 0603 at 1.5 V ≤ 12 µF max.
  - C404 + C408 ≤ 25 µF.
  - C406 at 20 V within 1–10 µF.
  - CC: 330 pF ±5 % + ESD2CAN24 4.2 pF max = 351 pF, inside 200–480 pF.
- **Dead-battery attach:** VIN_3V3 is down, so the VBUS LDO supplies LDO_3V3 (18 mA spec, §6.6). It powers the EEPROM, the I2Cc pull-ups and R404. The VIN_3V3 switch is unidirectional (§9.3.1.1), so nothing back-feeds 3V3.
- **Dead-battery sequence:**
  - SafeMode keeps the sink path open until the EEPROM bundle runs.
  - The charger then charges PACK_P. If the gauge FETs are off (fresh FET_EN = 0), it only charges the bank to VFB (16.8 V). The 3V3/MCU then boot and the gauge wakes on PACK (first review Q4).
  - CHG_INH floats low (R417), so charging is allowed with the MCU dead. As intended.

### B-9 [NOTE] BQ25756 pin pass and math: verified
- **Pins:** all 37 pins match Table 4-1. Pin 17 is to PGND; NC 15/16/31 are left floating as required.
- **ACOV:**
  - Window: 1.184 × 18.37 = 21.75 V to 1.206 × 19.08 = 23.01 V, above PD 21 V max and below the SMAJ22A 24.4 V breakdown.
  - Ratio: 1 + (R409 + R410)/R411. Worst case 18.37–19.08 with 1 %.
- **ACUV and input floor:**
  - ACUV trip: 4.02–4.19 V.
  - VACUV_DPM floor: 1.198 × 3.675 = 4.40 V to 1.222 × 3.784 = 4.62 V.
- **ILIM:** 5.28–5.84 A.
- **FB:** 0.1 % divider plus RFBG 33–55 Ω, as in the first review.
- **TS:** open NTC reads 75.3–76.0 % with 1 % parts, which is > VT1_RISE max 73.85 %: caught in charge mode, missed in reverse mode (BCOLD 77.15 %). Already known.
- **Gate drive:**
  - Logic-level FETs (VGS(th) 1.2–2.0 V, Qg about 6 nC at 5 V). Gate supply about 4 × 6 nC × 690 kHz = 17 mA; REGN limit is 70 mA.
  - PREGN at VAC = 20 V: 15 × 24 nC × 690 kHz = 0.25 W, within the 1 W SOA (§6.3.3.2).
  - Bootstrap 0.1 µF droop: 6 nC / 0.1 µF = 0.06 V.
- **CE level:** CHG_INH at 3.3 V × 10/11 = 3.0 V ≥ VIH 1.3 V. 0.3 mA per port. CE abs max is 6 V.
- **Pull-up rails:** STAT/PG to 3V3; INT to LDO_3V3. All are within the 6 V and 40 V abs max.

### B-10 [NOTE] TPS62933: verified
- **Pins:** 1 RT (to GND = 1.2 MHz, Table 7-1), 2 EN (100 k pull-down; 0.7 µA pull-up gives 0.07 V, so off by default), 3 VIN, 4 GND, 5 SW, 6 BST (0.1 µF), 7 SS (33 nF ≥ 6.8 nF), 8 FB.
- **Inductor:** SRP5030T-3R3M has Isat 8 A > IHS_LIMIT 5.8 A max, and Irms 5 A.
- **Ripple:** (16.8 − 5.08) × 0.302 / (3.3 µ × 1.2 M) = 0.89 A p-p.
- **Soft-start inrush** into about 300 µF: about 0.3 A.
- **Sheet text is stale:** the block title says "5.00 V" (the divider gives 5.08 V), and the BQ25756 block says "ILIM 5.5 A" (5.6 A). Cosmetic.

### B-11 [NOTE] Firmware/config items found in the BQ25756 datasheet (not in the first review's list)
- **EN_PFM:** POR = 1. TI §6.3.3.4 / Table 6-22: "recommended to disable PFM … when termination is enabled and set lower than 2A". The plan is ITERM = 0.25 A, so the config must write EN_PFM = 0.
- **IBAT_REV:** POR = 20 A (Table 6-50). The TPS25751 bundle should write 10 A (see B-1/B-7).
- **TS_T5/BHOT:** see B-2.
- **Watchdog:** EN_REV and EN_CHG reset on WATCHDOG. Confirm the TPS25751 firmware pets the BQ25756 watchdog (or sets WATCHDOG = 00). Otherwise sourcing drops out every 40 s.

### B-12 [NOTE] Port-to-itself loop
- **Case:** with a C-to-C cable from J401 to J501, one DRP port sources from PACK_P and the other sinks into PACK_P.
- **Effect:** about 6–10 % loss as heat until firmware notices.
- **Fix:** firmware should detect both ports attached with one as source and one as sink, and the partner's VID/PID or Source Caps equal to its own, then refuse the contract. TPS25751 config may offer "Unconstrained power"/USB-comms bits that help.

### B-13 [NOTE] D401 drawn with the bidirectional symbol Device:D_TVS (pins A1/A2), but SMAJ22A is unidirectional
- Pad 1 (cathode on D_SMA) lands on VBUS and pad 2 on GND, so assembly polarity is correct.
- The schematic just doesn't show it. Use Device:D_TVS (unidirectional, K/A) for clarity.

### B-14 [NOTE] PP5V (vSafe5V source) depends on the MCU (EN_5Vx)
- With the MCU dead, the TPS62933 is off and PP5V = 0. The TPS25751 then can't source vSafe5V, so the port can't act as a source at all.
- This is by design (it doubles as a safety interlock), but it should be stated in the circuit description §7.4.

### B-15 [NOTE] Two unsynchronised 600 kHz chargers share PACK_P
- The two oscillators are ±15 %, so the beat lands anywhere from 0 to about 90 kHz on PACK_P and the cells.
- It is filtered by each BAT_SNS_P bank (behind R427/R430), so it is probably harmless to the gauge.
- FSW_SYNC could take an MCU clock (200–600 kHz) on rev 2 if EMI or audible noise appears. Bring-up check.

### B-17 [MINOR, joint with C] R417/R517 10k pull-downs defeat CHG_INH while the MCU is in Standby/Shutdown
Raised by Reviewer C; I checked the CE side and agree.
- **Why it fails:** in Standby, PB8 holds only the PWR pull-up (25–55 kΩ). The node sees 11k ∥ 11k = 5.5k, so CE = 0.54 V < VIH 1.3 V (bq25756 §5.5 Logic I/O).
- **Fix:** R417/R517 = 100k. Worst case CE = 1.56 V > 1.3 V; with the MCU off, 1 µA × 100k = 0.1 V < VIL 0.4 V.
- **Optional:** a DNP 1 nF from CE to PGND for noise. CE (pin 7) is opposite the SW pins.
- CE_N carries nothing else. Keep DIS_CE_PIN = 0.

### B-16 [NOTE] Hot-unplug at 5 A and the 20 V-source/sink case: no issue found
- **Sinking:** the bank (about 100 µF) holds PPHV. TPS25751 RCP (§8.3.3.2.2) opens GATE_VBUS when PPHV > VBUS + VRCP. The BQ25756 drops out at ACUV/VINDPM.
- **Sourcing, load removal:** the inductor energy is ½ × 2.2 µ × 10.5² = 121 µJ into ≥ 100 µF, which is ΔV ≈ 0.06 V. No TVS stress.
- **Ports are independent:** PPHV/VAC are per port; they meet only on PACK_P (pass-through is limited by the sinking port's ICHG at its RBAT).
