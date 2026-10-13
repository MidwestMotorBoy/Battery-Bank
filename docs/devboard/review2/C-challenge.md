# Reviewer C, challenge round (round 2): attacks on A-findings.md and B-findings.md

Lead's questions assigned to me: 1–8. Everything below is re-derived from the datasheets, TRM SLUUBK0B (scratchpad/ti_docs/sluubk0b.txt), nets.txt and parts.txt.
- The Taiyo Yuden DC-bias curves were rendered from datasheets/*.pdf with KiCad's bundled Python and PyMuPDF.
- LRB521S/LRB520S data comes from the LRC PDFs B downloaded (B_dl/) and the LCSC C132124 page.

Verdict summary:
- **A-1:** DOWNGRADE to MINOR.
- **A-2:** UPHOLD the physics, DOWNGRADE to MINOR (it concerns a DNP option value).
- **A-3:** UPHOLD MAJOR, with an AMEND to the fix.
- **A-4, A-5, A-6, A-7, A-8, A-9, A-11, A-12:** UPHOLD MINOR.
- **A-10:** AMEND (it stays MINOR).
- **B-1, B-2, B-6:** UPHOLD MINOR.
- **B-3:** UPHOLD MINOR with corrected numbers. The replacement LRB520S-40T1G (C132124) is verified in stock.
- **B-4:** UPHOLD MINOR, low priority.
- **B-5:** UPHOLD and AMEND. The DC-bias figure is worse than the design assumed: worst case about 72 µF against the 80 µF minimum.

---

## Lead's questions

### Q1 (A-1): what do the TPS25751s offer before the MCU writes anything, and what does the gauge do with defaults?
- **No configuration in the repo.**
  - docs/project/tps25751-eeprom-programming.md describes only the mechanics: memory map, PBMx/FLxx/GAID flow and the region-update procedure. It contains no source-PDO content.
  - The only written limit is first-review firmware item 3 / #3: the MCU lowers USB1's offer when USB2 attaches.
  - So today nothing in the bundle plan limits the source PDOs. A is right that the limit lives only in MCU firmware.
- **"MCU dead → both ports source 100 W" is very unlikely as stated.**
  - With the MCU dead, EN_5V1/2 are pulled low (R432/R532 100k; TPS62933 EN pull-up 0.7 µA × 100k = 70 mV < 1.17 V falling threshold), so PP5V = 0.
  - tps25751 §6 (Type-C Source table) specifies IRp1.5 and IRp3.0 only for 4.75 V < VPP5V < 5.5 V. VOC_5 needs VPP5V > 3.8 V.
  - With PP5V at 0, the port cannot advertise more than default USB current. It also has no vSafe5V source (PP5V is the 5 V source switch, RPP_5V).
  - Whether a bundle could make the BQ25756 supply vSafe5V on PPHV in reverse mode is configuration-dependent and not shown in the datasheet. I treat it as unlikely.
  - The realistic trigger is therefore the MCU alive with EN_5V high but its PDO arbitration wrong or hung. That is first review #3 again.
- **Gauge defaults (TRM SLUUBK0B):**
  - §15.9.7: OCD1 threshold −6000 mA, delay 6 s.
  - §15.9.8: OCD2 −8000 mA, 3 s.
  - §15.9.9: recovery 5 s, latch limit 0 (no latch).
  - §15.9.10.5: AOLD:Threshold default 0xF4 → OLDV = 4, OLDD = 0xF.
  - §15.2.6.1: AFE Protection Control default 0x70, so RSNS = 0 (half thresholds).
  - Table A-1: setting 4 = −19.42 mV, which is 19.4 A at RS101 = 1 mΩ. With the ±2.5 mV offset and ±5 % scale (bq40z50 §7.31) the range is 16.9–21.9 A.
  - Table A-3: delay 0xF = 31 ms.
- **Check against A's numbers:**
  - My re-solve of A's equation I·(V_ocv − 0.13·I) = 213 W gives 17.6 A at 14.4 V and 24.0 A at 12.0 V; A's arithmetic is right.
  - 24 A is cut by AOLD in ≤ 31 ms.
  - 17.6 A may sit under AOLD (16.9 A minimum) and is cut by OCD2 after 3 s. Then 5 s off, then retry.
  - Q102 per FET: 17.6² × 8.7 mΩ = 2.7 W for 3 s out of every 8 s, about 1.0 W average. At RθJA 60 °C/W that is +60 °C, so Tj ≈ 105 °C at 45 °C ambient, below 150 °C.
  - F101 at 117 % of its rating for 3 s does not open: the opening time is specified only at 350 % (≤ 5 s); 100 % holds ≥ 4 h.
  - Cells: 17.6 A for 3 s against the 16.8 A (3C) maximum is negligible.
  - With the planned configuration (OCD1 10–11 A, OLD 16–20 A) it trips sooner.
  - The "thermal runaway within tens of seconds" claim needs a sustained 24 A, which AOLD prevents.
- **Verdict on A-1: DOWNGRADE to MINOR (configuration robustness).**
  - Pack-side hardware (gauge AFE and OCD) bounds the fault. The result is nuisance trip-cycling, not damage.
  - Keep A's fix: bundle defaults safe for both ports with no MCU (≤ 60 W/port, IBAT_REV 10 A), plus OLD ≤ 16 A.
  - This is the configuration half of first review #3, not a new hardware gap.

### Q2 (A-2): the 2 kΩ, F101 DNP, D102 orientation, and board vs option
- **The 2 kΩ is real.** bq40z50 Fig 6-1 (rendered, A/pineq2.png) shows DSG pump → switch → node → 2 kΩ → DSG pin, with the DSGOFF switch to VSS and a Zener to PACK.
  - Fall-time fit (§7.18 tF: VDSG(ON) to 1 V, 4.7 nF + 5.1 k), modelling the pin as V = Vc·Ri/(Ri + 5.1k) with Vc decaying at τ = (Ri + 5.1k)·4.7 nF from 28 V:
    - Ri = 1 k gives 44 µs, matching the 40 µs typical.
    - Ri = 15 k gives about 300 µs, matching the maximum.
  - So the internal pull-down path is about 1 k typical and up to about 15 k worst case. A's "2 k, up to ≈ 20 k" is in the same range.
- **D102 orientation:** D102.1 (K) is on DSG (U101 pin 28 side) and D102.2 (A) on DSG_G. It conducts when DSG_G is above DSG, i.e. at turn-off, bypassing R111. That matches A's description.
- **Re-derived turn-off with C109 = 0.1 µF and D102 fitted:**
  - τ = Ri × (0.1 µF + Ciss) ≈ 0.1–0.2 ms typical, up to about 1.5 ms worst.
  - During a hard short PACK_P ≈ 0 and Q102 is in its linear region while the gate falls from about 11 V to 2 V. That takes τ·ln(5.5) ≈ 0.17–0.34 ms typical.
  - Peak power is V²/(4·R_source) = 16.8²/(4 × 0.091 Ω) ≈ 780 W, against about 300–550 W allowed at 0.1–0.3 ms (A/soa.png, AGM Fig 14).
  - The SOA is exceeded. A's physics stands.
- **What bridges F101 while it is DNP:** nothing. CELL_P_RAW = {BT104.1, F101.1, J101.5, R104.1}. With F101 out, CELL_P, FET_MID, PACK_P and BAT (via D101 on CELL_P) are disconnected from the cells. No short-circuit current can flow until F101 is fitted.
- **Board vs option:** C109 is DNP on the board as built. The finding is about the value written in the sheet note and C109's Notes field ("fit if inrush trips SCD … 0.1 µF ~1 V/ms").
- **Verdict on A-2: UPHOLD the technical claim, DOWNGRADE to MINOR.**
  - Change the DNP value to 4.7 nF and fix the note before anyone fits it. A's 4.7 nF turn-on (7–17 V/ms → 2–5 A inrush) and turn-off (τ ≈ 11 µs) re-derive correctly.
  - It would be MAJOR only if the 0.1 µF were fitted by default.

### Q3 (A-3): a reversed or deep-discharged cell, and the precharge interplay
- **TRM §4.9:** "The gauge enters PRECHARGE mode if 1. Min cell voltage1..4 < Precharge Start Voltage OR 2. Max cell voltage1..4 < Charging Voltage Low − Charging Voltage Hysteresis and not in CHARGE mode."
  - Condition 1 is per cell (minimum cell). With FET Options[PCHG_COMM] = 0 (default, §15.2.1.x) the precharge FET is used, and this board has none (PCHG NC). So in PRECHARGE the CHG FET stays off, and Q101's body diode blocks charge current.
  - "Setting Precharge Start Voltage and Charging Voltage Low = 0 mV disables the precharge function." That is first-review firmware item 4.
- **Reversed cell:**
  - VC(n) − VC(n−1) ≈ −3.6 V, which violates the absolute maximum (VCn ≥ VC(n−1) − 0.3 V). It is clamped by the internal diode at about −0.7 V, and the ADC range is −0.2 to 5 V (bq40z50 §7.10).
  - The reported cell voltage is therefore ≤ 0 V, which is below a 2.5 V Precharge Start in the default configuration. Charging is blocked.
  - With item 4's 0 mV settings, nothing in the gauge blocks charging. CUV opens DSG only (TRM §2.2).
  - The BQ25756 sees the stack (3 × 3.6 − 3.6 = 7.2 V) and precharges it. Charge stops only when a healthy cell hits COV, after the three good cells gain about 0.6 V each.
  - The reversed cell is driven further into reverse at precharge current for up to the precharge safety timer. EVE §12.2.4 prohibits this.
  - CHG_INH is low whenever the MCU is not running (R417), which is common on a dev board.
- **Verdict on A-3: UPHOLD MAJOR. AMEND the fix.**
  - SLUUBK0B §15.4.9.2: Charging Voltage Low defaults to **2900 mV**. Condition 2 then enters PRECHARGE (CHG FET off) whenever every cell is below about 2.9 V minus hysteresis.
  - That happens to a pack recovering from CUV, with all cells at 2.5–2.9 V. Keeping the defaults (A's fix) would also stop USB from reviving a normally CUV-tripped pack.
  - The fix should be: Precharge Start Voltage = 2500 mV (blocks any cell below 2.5 V, including a reversed one), and Charging Voltage Low ≤ Precharge Start (2500 mV or 0) so condition 2 never fires above 2.5 V.
  - Reconcile firmware item 4 and circuit-description §2 accordingly. Item 4's stated reason for disabling (the BQ25756 does precharge itself) is still valid. The gauge precharge state is being used here only as a per-cell charge block.

### Q4 (A-4/A-5): F101 DNP as built
- **As assembled (F101 DNP):** the only connection from the cells to the board circuits is through the VC filters (R101–R104 to VC1–VC4 / C101–C104). CELL_P, BAT (D101 anode on CELL_P), VCC (R106 from FET_MID) and PACK_P are all unpowered, so U101 has VC1–VC4 driven by the cells with BAT and VCC dead.
- **J104 (bench PACK_P)** powers PACK_P. Q102's body diode (source = PACK_P → drain = FET_MID) then powers FET_MID and, via R106, VCC. BAT stays dead because D101 needs CELL_P, which is reachable only through Q101's channel (CHG off; its body diode points toward CELL_P, so with no FET on, CELL_P charges to about PACK_P − 0.7 V through it). The gauge therefore runs from VCC only.
- **After F101 is fitted** (the intended operating state) BAT is powered normally. The BAT-off/VC-on state is real during the cell check and after F101 opens. A-5's point stands for both.
- **A-4:** TP101 is on CELL_P (nets.txt), dead while F101 is out. BT104 can only be checked at F101 pad 1, R104 pad 1 or J101.5 (DNP). UPHOLD MINOR.
- **A-5:** moving D101's anode to CELL_P_RAW matches TI Fig 9-1 (D1 anode on the J2.1/4P node with R20; checked in A/bat.png) and makes the gauge readable by EV2400 before F101 is fitted. Fault current via R105 (100 Ω) is ≤ 168 mA into a shorted BAT path, so leaving it unfused is acceptable. UPHOLD MINOR.

### Q5 (A-6): end-of-discharge current, and whether 15 A is right
- The product rule is 100 W total out (first-review firmware item 3). 2 × 100 W is a fault case (A-1), bounded by the gauge.
- Pack current = (P_out/η + housekeeping)/V_pack_loaded, with η ≈ 0.94 for BQ25756 reverse mode at 20 V / 5 A (TI's curve region) and housekeeping about 0.3 A:
  - 3.6 V/cell (14.4 V): 7.4 + 0.3 = 7.7 A.
  - 3.0 V/cell (12.0 V): 8.9 + 0.3 = 9.2 A.
  - 2.5 V/cell (10.0 V, EVE cut-off and CUV default 2500 mV, SLUUBK0B §15.9.1.1): 10.6 + 0.3 = 10.9 A.
- So **about 11 A is the right worst-case continuous figure.** The 16.8 A figure is the 2 × 100 W fault and should not size the fuse.
- **Prosemi 1206FA datasheet p.2:** In = I_input_max / (0.70 × Ktemp). With Ktemp ≈ 0.95 at 50 °C: In ≥ 10.9/0.665 = 16.4 A. At 60–70 °C beside 2 W of protection FETs, Ktemp is about 0.9 and In ≥ 17.3 A.
- **Verdict on A-6: UPHOLD MINOR.**
  - 15 A meets a plain 75 % derating at 25 °C (10.9/15 = 73 %) but fails the maker's own rule once Ktemp < 1.
  - 1206FA-20A is the better choice, provided SCD clears a hard short first (A's N-2: SCD1 + tDETECT ≤ about 250 µs).
  - The 11 A only occurs in the last few minutes of a 100 W discharge, so this is margin, not a functional failure.

### Q6 (B-3): LRB521S-40T1G leakage, and the reverse voltage the diodes see
- **Datasheet (LRC, B_dl/1809291620_LRC-LRB521S-40T1G_C135802.pdf p.1):** IR max 20 µA at VR = 10 V and 90 µA at 40 V (25 °C). Tj max 125 °C.
- **Typical VR–IR curve** (p.2, rendered A/lrb_ir.png), read at VR = 20 V:

  | Ta | IR typ at 20 V |
  |---|---|
  | 25 °C | ≈ 4 µA |
  | 75 °C | ≈ 120 µA |
  | 125 °C | ≈ 1.8 mA |
  | 150 °C | ≈ 20 mA |

  - That is ×15 per 50 °C, about ×1.72 per 10 °C.
  - The 25 °C max/typ ratio is about 5 (20 µA max against ≈ 4 µA typ at 10 V).
  - The dowosemi second-source sheet gives RθJA = 667 K/W and PD 150 mW.
- **Reverse voltage, from the circuit:**
  - **Buck charging (VAC 20 V → VBAT 12–16.8 V):** leg A switches. D404 sees BTST1 − DRV_SUP ≈ SW1 = VAC (≤ 22.5 V ACOV) while HS1 is on, D = 0.6–0.84. Leg B's HS2 is held on, so **D405 sees VBAT (12–16.8 V) almost 100 % of the time.**
  - **Reverse (boost to 20 V from the pack):** leg B's HS2 is on, so D405 sees VBAT continuously. Leg A switches, so D404 sees 20 V for (1 − D_boost) of each cycle.
  - B analysed only D404 at 85 % duty. **D405 has the continuous stress.**
- **Self-heating (P = VR·IR·duty, loop gain = P·ln(1.72)/10 °C·RθJA = P × 36 /W, so runaway when P > ≈ 28 mW):**
  - Typical part at Tj 100 °C, 20 V: IR ≈ 120 µA × 15^0.5 ≈ 0.47 mA → 9 mW → +6 °C. Stable.
  - Max-leakage part (×5): 2.3 mA → 47 mW → runaway. The ×5 part crosses 28 mW at Tj ≈ 90 °C.
  - The diodes sit beside the BTST caps at the half-bridges, where B-2 shows the board may reach the TS hot cutoff of about 94.5 °C before charging stops. So runaway of a worst-case diode in the hottest corner is plausible. B's "4–8 mA, 0.1 W" over-states the typical case by about 10×, but the conclusion holds for worst-case parts.
- **Replacement:** LRB520S-40T1G, LCSC **C132124**. The LCSC page shows LRC, 40 V, 200 mA, SOD-523, IR 1 µA, 37 450 in stock. Datasheet (B_dl/DOC013491952.pdf): IR max 1 µA at 10 V and 10 µA at 40 V (9–20× lower); VF max 0.39 V at 10 mA and 0.55 V at 100 mA.
  - Average bootstrap current is about Qg·fsw ≈ 6 nC × 0.6 MHz ≈ 4 mA, so the extra VF is about 0.1 V on a 5 V DRV_SUP. That is negligible against the refresh threshold.
  - Same footprint and pinout (pad 1 = cathode).
- **Verdict on B-3: UPHOLD MINOR.** The swap to C132124 is warranted and free. Measure D405 (not only D404) at bring-up.

### Q7 (B-4): EVE maximum charge current
- eve-inr21700-58e.pdf §3.4: "Maximum Charge 5.6A(1C) … (not for cycle life)". §12.2.1: "Charging current shall be less than maximum charge current specified".
- bq25756 §5.5: KICHG = 48 / 50 / 52 A·kΩ at RBAT = 5 mΩ. Worst case 52 / (9.1 k × 0.99) / 0.99 (RBAT −1 %) = 5.83 A. That is 4 % above 5.6 A, so technically a violation.
- **When it binds:** only when ICHG_REG ≥ the pin value.
  - With SafeMode and no bundle, the sink path never closes, so there is no charging at all.
  - With the bundle, ICHG_REG = 2.8 A, and EN_CHG_BIT_RESET_BEHAVIOR = 0 stops charging on watchdog expiry.
  - So the pin ceiling binds only if firmware or the bundle writes ICHG_REG above about 5.5 A (a bug), or the bundle omits the reset-behaviour bit.
- **Verdict on B-4: UPHOLD MINOR (low priority).** It needs a configuration error to bind, but the 9.53 k fix (5.57 A max, 5.25 A nominal) costs nothing.

### Q8 (B-5): where the 80 µF is stated, and the DC-bias arithmetic
- **Source:** bq25756 §5.3 Recommended Operating Conditions: "CIN Buck input capacitance (minimum value after derating) 80 µF" and "COUT Buck output capacitance (minimum value after derating) 80 µF" (pdftotext -raw). B's citation is correct.
- **DC bias:** GMK325BJ226MM-P (rendered from datasheets/gmk325bj226mm.pdf p.2, "DC Bias Char."):

  | DC bias | ΔC | Effective (of 22 µF) |
  |---|---|---|
  | 15 V | ≈ −62 % | 8.4 µF |
  | 20 V | ≈ −73 % | **5.9 µF** |
  | 21 V | ≈ −75 % | 5.5 µF |

  - Temperature: about −7 % at 85 °C.
  - **The design's 8.5 µF per part (README item 16) is the 15 V value, not the 20 V one.**
- **Worst case at 20 V, 85 °C, −20 % tolerance:**
  - MLCCs: 4 × 5.9 × 0.8 × 0.93 = 17.6 µF.
  - Polymer C421: 68 × 0.8 = 54.4 µF. Polymer has no DC-bias loss, and the temperature effect is small and positive.
  - **Total about 72 µF < 80 µF** (B had 77.5 µF).
  - Nominal at 20 V: 23.6 + 68 = 91.6 µF. README item 16's "34 + 68 ≈ 100 µF" is optimistic.
- **Battery side (TMK325ABJ476MM, rendered):** at 16.8 V ≈ −77 %, so 10.8 µF each. 3 × 10.8 × 0.8 × 0.9 = 23 µF, plus 80 µF polymer, = 103 µF ≥ 80 µF. OK.
- **Caveat:** at 600 kHz the 68 µF / 30 mΩ polymer is ESR-dominated (corner 1/(2π·68 µ·0.03) ≈ 78 kHz). TI still counts "a combination of ceramic and bulk" (§7.2.1.2.5).
- **Verdict on B-5: UPHOLD MINOR, AMEND the numbers (the deficit is worse).** Fix as B proposes: C421 → 100 µF 35 V polymer (gives about 98 µF worst case), or a fifth 22 µF MLCC (+4.4 µF, still short at about 77 µF). The polymer change is the better fix.

---

## Remaining MAJOR / hardware-change MINOR items

### A-7 vs A: UPHOLD MINOR
- Q101/Q102 at 11 A: 11² × 6.0 mΩ × 1.45 = 1.05 W each, and no sensor nearby.
- The TH305-on-PA7 option was agreed in round 1. PA7 is ADC1_IN2 (DS13258 Table 15). NTC_EN load becomes 0.83 mA at 25 °C.

### A-8 vs A: UPHOLD MINOR
- TS absolute maximum is VREG + 0.3 = 2.1 V (§7.1).
- Cans are at 4.2 / 8.4 / 12.6 V above VSS for BT102–BT104. A 10 k NTC body touching a can injects (12.6 − 2.1)/10 k ≈ 1 mA.
- The fix (insulated sensors plus an optional series 1 k footprint) is right.

### A-9 vs A: UPHOLD MINOR
- I traced the reverse path: GND → Q402 LS body diode → SW2 → Q402 HS body diode → BAT_SNS_P → R427/R430 → PACK_P. That is two drops, about −1.4 V, and the same through each TPS62933.
- C432/C532 polymers would see about −1.4 V.
- A keyed connector costs nothing.

### A-10 vs A: AMEND (stays MINOR)
- §7.12 gives VOH ≥ 3.5 V at 0 µA and ≥ 1.8 V at −10 µA (VBAT > 5.5 V). As a Thevenin source: Voc ≥ 3.5 V, R_out ≤ 170 k.
- With R117 = 470 k as the only load: VG ≥ 3.5 × 470/640 = 2.57 V, against 2N7002 Vth(max) 2.5 V at ID = 250 µA. The needed ID is only 33 µA, so the required VGS is a little lower.
- So the gate drive is marginal, not "only 1.8 V". BSS138 (Vth 0.8–1.5 V) or R117 = 1 MΩ (VG ≥ 2.97 V) fixes it. Keep MINOR.

### A-11 vs A: UPHOLD MINOR
- §9.2.2.1.3 asks for Kelvin at 4P/1N.
- 5.6 A × (3–8 mΩ lead + terminal) = 17–45 mV error on cells 1 and 4 during the learning cycle the welded pack exists for.

### A-12 vs A: UPHOLD MINOR
- IPC-2221 external: 0.048 × 20^0.44 × 271^0.725 = 0.048 × 3.74 × 58.0 = 10.4 A at ΔT 20 °C for 2.5 mm × 70 µm. That is below the 11 A design point.

### B-1 vs B: UPHOLD MINOR
- bq25756 §6.3.6 reverse-mode enable conditions do not include CE (B's citation). CHG_INH is charge-only.
- The documentation fix is required. The HIZ-forcing hardware is reasonably deferred to rev 2.

### B-2 vs B: UPHOLD MINOR
- My recomputation of the TS hot point: Rp = 0.34375 × 1.8 k / 0.65625 = 0.943 k → R_NTC = 1/(1/0.943 − 1/5.6) = 1.134 k → T = 1/(1/298.15 + ln(0.1134)/3435) = 367.7 K = 94.5 °C.
- X5R parts are rated to 85 °C (GMK and TMK spec sheets). TS_T5 = 00b (about 81 °C) is the cheap fix.

### B-6 vs B: UPHOLD MINOR
- tps25751 §9.4.1.2.2.3 asks for PPHV decoupling at the IC. In nets.txt the PPHV net has only C409 (1 µF, the BQ25756 VAC cap) and TP402. DNP pads are cheap.
- If fitted, count them in README item 15's sink-bulk/slew-rate reasoning.

### B-7 vs B: UPHOLD (configuration)
- XAL7030-222: Irms 10 A at 20 °C rise, 12.9 A at 40 °C rise.
- 117 W/0.93/10 V = 12.6 A. Only the IBAT_REV / PDO configuration bounds it.

---

## Missed by everyone

### X-1 [MINOR] README item 16 / B-5 used the 15 V DC-bias value for the 35 V 22 µF MLCCs on the USB side
- Measured from the Taiyo Yuden curve: 5.9 µF each at 20 V, not 8.5 µF. See Q8.
- The USB-side bank is about 92 µF nominal and about 72 µF worst case, against the BQ25756's 80 µF minimum.
- Fold into B-5 (C421 → 100 µF 35 V polymer). Correct README item 16's "34 + 68 ≈ 100 µF".

### X-2 [MAJOR-supporting AMEND to A-3] Charging Voltage Low default 2900 mV
- With PCHG_COMM = 0 and no precharge FET, this default blocks USB charging of any pack whose highest cell is below about 2.9 V. That is every pack recovering from a CUV trip.
- Any configuration that keeps the gauge precharge state as a charge block must lower Charging Voltage Low to ≤ Precharge Start Voltage (SLUUBK0B §4.9 condition 2, §15.4.9.2).

### X-3 [NOTE] BTST2 diode (D405) carries the continuous reverse bias
- VBAT 12–16.8 V on D405 at about 100 % duty in buck charging (HS2 held on), and on D404 at 20 V in reverse mode.
- Bring-up thermal checks should cover both diodes per port.

### X-4 [NOTE] With F101 DNP, SW101 (CELL_P → R118 → PACK_P) cannot wake anything
- CELL_P is floating. The wake button and the cell check both depend on F101 being fitted first.
- If A-5 is adopted, the gauge is at least powered pre-F101. Add this to the bring-up order in the sheet note.

---

## Post-exchange amendments (round 2)

- **Q7 / B-4:** B points out that ICHG_REG is "Reset by: WATCHDOG" back to its POR value (0x190 = 20 A; bq25756 register 0x02). After any watchdog expiry or bundle fault, only EN_CHG_BIT_RESET_BEHAVIOR = 0 keeps the pin ceiling from binding, and that holds only if the bundle sets it. Agreed. B-4 stays MINOR, and its priority rises slightly: the 9.53 k swap is the hardware backstop for that configuration dependency.
- **Q8 / B-5:** A read the same GMK325 curve as about 6.8 µF at 20 V, giving about 75 µF worst case; I read 5.9 µF and about 72 µF. Either reading is below 80 µF. The fix is agreed with B: C421/C521 → 100 µF 35 V polymer.
- **Peer verdicts on C-findings:** A and B both downgrade C-3 to NOTE, and A downgrades C-5 to NOTE (B is fine with NOTE). Both are accepted and amended in C-findings.md. C-1 is upheld by both: 100 k plus a DNP 1 nF at CE, with A's polarity-swap alternative left to the lead. C-2, C-4, C-6 and C-7 are upheld by both.
