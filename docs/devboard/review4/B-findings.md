# Reviewer B: USB port power stage (usb_port.kicad_sch, port 1 = 4xx, port 2 = 5xx), round 1

**Scope:**
- U403 BQ25756, pin by pin, with every programming resistor.
- The discrete half-bridge Q401/Q402/Q407/Q408 (PGQ04N070, README items 37–38, never reviewed before).
- R444–R451, C454/C455, C430/C438, L401, R424/R427, both capacitor banks, R430.
- The PP5V buck U404 TPS62933 with L402, C439–C447, R431–R434.
- Derating, fault injection, POR behaviour, and stale Notes and README text for these parts.

**Sources:**
- Datasheets:
    - `datasheets/bq25756.pdf` (SLUSEN5A, rev. Aug 2026; page numbers are the printed ones).
    - `bq25756evm-sluuct7.pdf` (SLUUCT7D, fig. 3-1, rendered).
    - `tps62933.pdf` (SLUSEA4D).
    - `tps25751.pdf` (SLVSH93A §6.4, §6.8).
    - `lrb520s-40t1g.pdf`, `smaj22a.pdf`, `iauc45n04s6l063h.pdf`.
- Netlist files: `nets.txt`, `parts.txt`.
- Fetched for this review: LCSC datasheet URLs are `https://www.lcsc.com/datasheet/<LCSC#>.pdf`, which redirect to `datasheet.lcsc.com`. All are saved in `scratch-b/`:
    - **PGQ04N070** (JinYu V2.0, 2023/08): `scratch-b/pgq04n070.pdf`, from `https://datasheet.lcsc.com/datasheet/pdf/e20fee161cf2d03e892f54f65caf3924.pdf?productCode=C49384056`.
    - SMMS1040-2R2M (SXN): `smms1040-2r2m.pdf`, C149591.
    - APS0530M3R3H (Coilank): `aps0530m3r3h.pdf`, C49073587.
    - JIERR MA25V100M6x6: `jierr-ma25v100m6x6.pdf`, C46550465.
    - Honor HV1V107M0607PZ: `honor-hv1v107m0607pz.pdf`, C5246554.
    - R+O SMAJ22A: `smaj22a-ro.pdf`, C41376403.
    - ChuangHui SS221M160: `chuanghui-ss221m160.pdf`, C25503905.
    - The Samsung CL31A226/CL31A106 catalogue (C12891/C13585) has no DC-bias curves.
- Arithmetic: `scratch-b/calc_b.py` (output reproduced where cited).
- Port comparison: `scratch-b/port_compare.py`.
- Figures rendered and read:
    - PGQ04N070 p.1 (pinout), p.3 (fig. 2/3/4/6), p.6 (package).
    - SMMS1040-2R2M L/ΔT curve (p.15).
    - BQ25756 fig. 4-1.
    - EVM fig. 3-1.

**Peer answers relied on:**
- A: CC2340 GPIOs latch in Standby (SWRS349A §8.11), are hi-Z with no pulls in reset, and have no internal pull at boot.
- C: the TPS25751 bundle writes the BQ25756 IAC_DPM/VAC_DPM from the PD contract (SLVUCP9B §4.3.1.2 Q12/Q13); C owns that CONFIG line.
- D: C432/C532 leakage goes into the rev A7 power budget.

**Summary:** 0 CRITICAL, 1 MAJOR, 6 MINOR, 2 CONFIG, 1 DOC, 7 NOTE.
- **After round 2:** unchanged; there were no grade changes.
- B-1 is amended with a concrete FET spec, candidate parts and an interim IBAT_REV = 5 A CONFIG.
- B-2 and B-14 are amended. See "After round 2" at the end.
- Top 3: B-1 (high-side gate voltage sags to the bootstrap-refresh threshold while the FET carries 10 A), B-2 (FET loss budget is understated 2–3×, with a lower Tj max), B-3 (snubber resistor power).

---

### B-1 [MAJOR] The high-side FETs that sit 100 % on (Q402 in reverse boost, at up to 10–12.6 A) run their gate down to the BQ25756 bootstrap-refresh threshold (2.7–3.9 V), where the PGQ04N070 is not specified and is barely enhanced
- **Where:**
    - Q402/Q502 (HG2, BTST2_C/C413, D405) and Q401/Q501 (HG1, C412, D404).
    - Worst mode: reverse boost (source 20 V from a 11–16.8 V pack), where Q402 is ON for the whole cycle and carries the full battery current.
- **Evidence:**
    - **The FET stays on (verified).** BQ25756 Table 6-1 (p.21–22): in boost mode the "HS BUCK FET" is ON and in buck mode the "HS BOOST FET" is ON. In reverse mode the battery-side leg is the input leg, so with the pack below VAC_REV, Q402 is ON 100 %.
    - **When the bootstrap refreshes (verified).** §5.5 PWM DRIVERS: VBTST1/2_REFRESH = **2.7 / 3.1 / 3.9 V** (min/typ/max), "BTST falling, VBTST − VSW when low-side refresh pulse is requested". So the high-side gate (HIDRV = BTST while on) can sag to 2.7–3.9 V before it is topped up.
    - **The sag is slow but certain (inferred).** BTST is drained by D405 reverse leakage (LRB520S-40: ≤ 1 µA at 10 V and ≤ 10 µA at 40 V at 25 °C, rising about 30× when hot), the driver bias and IGSS. That gives about 50 µA, so 0.1 µF goes from 4.3 V to 3.1 V in about 2.4 ms. The gate spends most of each refresh period well below 4.5 V.
    - **Starting voltage (verified arithmetic).** REGN 4.8 V min (§5.5), minus R420 drop 0.17 V (4 FETs × 6.9 nC × 600 kHz × 10 Ω), minus D405 VF 0.39 V at 10 mA, gives **4.24 V**. That is already below the 4.5 V rating point.
    - **The PGQ04N070 sheet:**
        - VGS(th) is 1.0 / 1.8 / **2.5 V**.
        - RDS(on) is specified only at 10 V and 4.5 V (p.2).
        - Fig. 2 (rendered, typical, 25 °C): VGS = 3 V reaches only about 11 A at VDS = 0.5 V and about 17 A at 2 V. That is about 35 mΩ at 10 A, against 7 mΩ at 4.5 V.
        - VGS = 3.5 V is about 14 mΩ.
        - A part at the 2.5 V threshold maximum has about 0.7 V less overdrive than the typical curve. With (VGS − Vth)² scaling, its saturation current at VGS = 3.0 V is only about 3 A.
    - **The IAUC45N04S6L063H it replaced** had VGS(th) of 2.0 V max (p.2) and Tj max of 175 °C.
- **Effect:**
    - Typical parts: at 10 A, Q402 dissipates about 1 W at 4.3 V gate but about 3.5 W just before each refresh. The average is about 1.4 W (25 °C) to 1.9 W (hot) instead of 1.36 W.
    - Worst case (high-threshold PGQ04N070 with a 2.7–3.1 V refresh BQ25756): Q402 leaves the ohmic region at 10 A, VDS rises to volts, and it heats until it fails. Nothing current-limits it, because IBAT_REV and ILIM regulate average current, not FET VDS.
    - The same applies, at lower current, to Q401 in forward boost (input ≤ 5.8 A) and reverse buck (3 A), and to Q402 in forward buck (≤ 5.8 A).
- **Proposed fix:**
    - (a) For the four high-side positions (Q401/Q402/Q501/Q502), use a FET with VGS(th) max ≤ 2.0 V and RDS(on) guaranteed at VGS = 2.5–3 V. A 40 V PDFN3333 "2.5 V-rated" part fits; the IAUC45's die was in this class. The low sides can stay PGQ04N070, because LODRV is DRV_SUP ≈ 4.6 V and is never refresh-limited.
    - (b) Before committing to PGQ04N070 for production, probe HG2–SW2 and VDS(Q402) at bring-up in reverse mode at 20 V / 5 A from a 12 V pack. Note the refresh interval and the minimum VGS, then repeat hot.
    - (c) Ask TI (E2E) whether the BQ25756 also refreshes periodically, independent of the comparator. If it does, the gate never reaches 2.7 V and this drops to MINOR.
    - A higher DRV_SUP (up to 12 V, §4 pin 23) only lengthens the time above the threshold. The minimum is still set by VBTST_REFRESH.
- **Confidence:** verified for the datasheet facts (refresh threshold, 100 % on-time, unspecified RDS(on) below 4.5 V, fig. 2 curve). Inferred for the droop rate and the worst-case saturation current (no leakage spec for BTST; Id_sat scaling is first-order).

### B-2 [MINOR] FET loss budget for the discrete stage is 2–3× the cost-down estimate, in a package with no published RθJA and a 150 °C Tj max
- **Where:** Q401/Q402/Q407/Q408 (and 5xx); `cost-down-2026-10-14.md` A16; README item 38.
- **Evidence:**
    - PGQ04N070 (p.1–2): Tj max 150 °C (IAUC45: 175 °C). Only RθJC = 4.46 °C/W is given; there is no RθJA. RDS(on) at 4.5 V is 10 mΩ max (25 °C), ×1.36 at 100 °C (fig. 3).
    - Driver: 3.4 Ω on / 1.0 Ω off (§5.5) plus the FET's 3.1 Ω internal RG. Qgd 2.5 nC.
    - Dead time 45 ns (§5.5). VSD 0.8 V typ / 1.2 V max. Qrr 15 nC. fsw 598 kHz (B-15).
- **Arithmetic (`calc_b.py`; RDS 13.6 mΩ hot at VGS 4.5 V, before the B-1 penalty):**

    | Case | Q402 (HS2, 100 % on) | Q407 (LS1, hard-switched) | Q401 (HS1, sync rectifier) | Stage |
    |---|---|---|---|---|
    | Reverse 100 W, 12 V pack (8.9 A) | 1.07 W | 1.36 W | 1.20 W | 3.6 W |
    | Reverse 100 W, 11.2 V pack (9.6 A) | 1.25 W | 1.55 W | 1.30 W | 4.1 W |
    | Reverse, IBAT_REV = 10 A | 1.36 W | 1.64 W | 1.37 W | 4.4 W |
    | Reverse, no config, 10 V pack (12.6 A, ILIM ceiling 117 W) | 2.16 W | 2.37 W | 1.80 W | 6.3 W |
    | Forward buck 20 → 16.8 V, 5.77 A | 0.45 W | 0.50 W | 0.94 W (Q401 switching) | 1.9 W |

    - Plus L401 at about 1.0–1.8 W (DCR alone) in the same area.
    - The cost-down's "about 0.5 W per FET, split across two packages per leg" is wrong in two ways:
        - Q402 carries the whole battery current continuously in reverse boost.
        - The two FETs of a leg conduct alternately; they never share current.
    - With a typical PDFN3333 RθJA of 40–60 °C/W, 1.5 W gives +60 to +90 °C at the junction above ambient (inferred; the maker publishes none). The no-config case (2.4 W) can approach the 150 °C limit unless TS (TH401) trips first: board 94.5 °C at POR, 81 °C with TS_T5/BHOT = 00b.
- **Proposed fix:**
    - Keep the checklist items IBAT_REV = 10 A and TS_T5/BHOT = 00b. They are now load-bearing for FET Tj, not just the X5R MLCCs.
    - At bring-up, thermocouple Q402 and Q407 at 100 W reverse from about 12 V.
    - Correct the cost-down A16 text.
    - For production, the layout must spread copper per FET (drain pad into a plane with vias). Consider 5 × 6 mm parts for Q402/Q407, the two hottest positions.
- **Confidence:** verified arithmetic from datasheet values; inferred thermal resistance.

### B-3 [MINOR] Snubber resistors R450/R451 (and 5xx) are 0805 125 mW; the EVM uses 750 mW parts, and the Note's own sizing rule needs 0.3–0.55 W
- **Where:** R450/C454 (SW1), R451/C455 (SW2); DNP.
- **Evidence:**
    - The EVM fig. 3-1 (rendered) labels R14/R15 "3.30, 750mW".
    - Our R450 is UNI-ROYAL 0805W8F330KT5E (LCSC C16257: 3.3 Ω, 125 mW).
    - The Note says "C about 3x the node capacitance". The SW node is 2 × Coss ≈ 600 pF at 20 V (PGQ fig. 5), so C ≈ 1.8 nF and P ≈ C·V²·f = 1.8 n × 22.6² × 598 k = **0.55 W**.
    - Even 330 pF gives 0.10 W; only the 33 pF placeholder (10 mW) is safe.
- **Proposed fix:** change the R450/R451 footprints to 1206 wide-terminal or 2010 (≥ 0.5–0.75 W, EVM class). Alternatively, add to the Note that C above about 330 pF needs a bigger resistor.
- **Confidence:** verified.

### B-4 [MINOR] Battery-side polymer C432/C532 is permanently biased from PACK_P; its datasheet leakage limit is 500 µA each
- **Where:** C432/C532 (JIERR MA25V100M6x6) on BAT_SNS_P → R427 → VBAT_SYS → R430 → PACK_P. Nothing switches it out.
- **Evidence:**
    - JIERR p.1: leakage "I ≤ 0.2CV or 500 µA (whichever is greater)" at rated voltage after 2 min. That is 500 µA per cap, 1 mA for the pair, against the 150 µA sleep budget.
    - At 16.8 V (67 % of rated) the real figure is normally far lower, but nothing guarantees it.
    - C421 (Honor, 700 µA max) is not biased in sleep. The Q401/Q402 body diodes (anode SW1/SW2 → cathode AC_SNS_N/BAT_SNS_P) block the pack from AC_SNS_N.
- **Proposed fix:** measure it at bring-up (the Note already asks). For production, choose a polymer whose datasheet gives a µA-class leakage limit, or a hybrid with a 0.01CV spec. D carries it in the rev A7 budget (FETs-on idle only; ship mode isolates PACK_P).
- **Confidence:** verified (spec); the real leakage is unknown.

### B-5 [MINOR] Gate-resistor tuning guidance has no upper bound; above about 10 Ω, turn-off eats the 45 ns dead time
- **Where:** R444–R447 (and 5xx) Notes: "raise to a few ohms".
- **Evidence:** turn-off goes through the same resistor. τ = (1.0 Ω driver + 3.1 Ω RG + Rext) × about 1.2 nF, then the Miller plateau. Time to reach VGS(th) min (1 V):

    | Rext | Turn-off time |
    |---|---|
    | 0 Ω | 11 ns |
    | 4.7 Ω | 24 ns |
    | 10 Ω | 39 ns |

    The dead time is fixed at 45 ns (§5.5 tDT1/tDT2). Hot, VGS(th) is lower, so the margin shrinks further: cross-conduction risk.
- **Proposed fix:** add "≤ 4.7 Ω; above that, add a turn-off diode across the resistor" to the Notes and the README tuning text.
- **Confidence:** inferred (first-order RC estimate from datasheet values).

### B-6 [MINOR] Voltage margin of the 40 V FETs and the 30 V-rated inductors is thin under ringing and surge; snubbers are DNP
- **Where:** Q401/Q407 (SW1, USB side), L401, L402; SMAJ22A D401.
- **Evidence (verified):**

    | Source | Peak | Against 40 V FET |
    |---|---|---|
    | ACOV trip max (1.206 V × 19.08) | 23.0 V | 58 % before ringing |
    | SMAJ22A VC at 11.3 A (R+O sheet) | 35.5 V | 89 % |

    - Above ACOV the charger stops, so 23.0 V is the highest steady VAC.
    - The 35.5 V surge reaches PPHV only while the TPS25751 sink switch is closed, filtered by the 100 µF bank behind 5 mΩ.
    - PGQ04N070 edges are fast (tf 4.9 ns, Crss 5.8 pF; p.2), so ringing of +30–50 % on a 23 V step is plausible.
    - SMMS1040 and APS0530 both list "Absolute maximum voltage 30 VDC".
- **Proposed fix:**
    - At bring-up, measure SW1 overshoot at 22 V input and in reverse at 20 V / 5 A, using TP405/TP412.
    - Keep the snubber pads (with B-3 fixed).
    - The IAUC45 was also 40 V, so this is no regression. It is a margin item against the 50 % guideline.
- **Confidence:** verified ratings; inferred ringing.

### B-7 [MINOR, joint with C; C owns] TPS62933 output limit (valley 2.9 A min) is at or below a 3 A PDO plus VCONN
- **Where:** U404/U504, L402, PP5V → TPS25751 PP5V (only load per `nets.txt`: C407/C441–C443/C447/L402/R433/TP403/U401.34).
- **Evidence (TPS62933 §8.5):** ILS_LIMIT is 2.9 A min; IHS_LIMIT is 4.2 A min.
- **Arithmetic:**
    - Ripple is 0.63 A p-p (10 V in) to 1.34 A p-p (16.8 V, L −20 %, f 1.0 MHz).
    - The guaranteed DC output is 3.2–3.5 A (3.35 A at 16.8 V nominal).
    - 3 A plus 0.3 A VCONN sits at the edge. The TPS25751 ILIM5V setting 3 clamps only at 3.04–3.58 A.
    - Behaviour (§9.3.x p.24–25): cycle-by-cycle valley limit with frequency foldback, so PP5V sags. Hiccup happens only below 65 % UVP after 256 µs; the off time is 10.5 × tSS ≈ 50 ms.
    - Thermal at 3.3 A: about 1 W, RθJA_EVM 60 °C/W, so about +60 °C. No objection.
- **Proposed fix:** C's finding (ILIM5V choice / accept as overload-only). From my side, consider RT floating (500 kHz) to halve the switching loss and ripple. That needs L ≈ 6.8 µH per Table 10-2.
- **Confidence:** verified.

### B-8 [CONFIG] JEITA with an NTC on the FETs: below about 19 °C board temperature the charger drops to 20 % of ICHG and needs about 24 °C to leave
- **Where:** TS network R415 1.8k / R416 5.6k / TH401 (and 5xx); bringup checklist §3 "EN_JEITA = 0, **or** set TS_T2/JEITA_ISETC".
- **Evidence:**
    - POR: EN_JEITA = 1, JEITA_ISETC = 01b (20 %), TS_T2 = 01b (REG0x1C/0x1B, p.46).
    - VT2 is 68.25 % rising / 66.95 % falling (§5.5). With this network that maps to cool entry at **19.3 °C** and exit at **23.9 °C** (B3435; B3380 gives 19.2/23.8).
    - On a bench at 18 °C a port charges at 20 % (about 1.1 A). At 1.1 A the FETs barely self-heat, so it may never leave the cool region.
    - The other thresholds, recomputed:

        | Threshold | Temperature |
        |---|---|
        | T1 cold | −7.6 °C |
        | T3 warm (VFB × 97.6 %) | 73.9 °C |
        | T5 hot (POR) | 94.5 °C |
        | T5 = 00b | 80.8 °C |
        | BHOT 01b (POR) | 94.5 °C |
        | BHOT 00b | 87.7 °C |
        | Open NTC | 75.3–76.0 % (caught as cold in charge mode only) |

        These match review 2.
- **Proposed fix:** make **EN_JEITA = 0** mandatory in the bundle (re-raised from review 1 item 2 with the hysteresis numbers). JEITA has no meaning for a FET-mounted sensor; T1/T5 stay active.
- **Confidence:** verified.

### B-9 [CONFIG] VFB_REG must be written; the POR value regulates 16.70–16.96 V (4.17–4.24 V/cell)
- **Where:** R418/R419 (0.1 %), FBG.
- **Evidence:**
    - VFB_NOM is 1.536 V at POR; accuracy ±0.5 % (0–85 °C); RFBG 33–55 Ω (§5.5).
    - The POR band is 16.70–16.96 V (nominal 16.83 V).
    - With VFB_REG = 0x0F (1.534 V): 16.68–16.94 V, nominal 16.81 V.
    - This is a review 1 item. It is restated because the ±0.5 % reference tolerance alone allows 4.235 V/cell even when configured. The gauge COV (≤ 4.25 V, checklist) is the backstop.
- **Proposed fix:** nothing new in hardware. Keep VFB_REG = 0x0F in the checklist. Consider 0x0E (1.532 V) if bench measurements of a sample sit high.
- **Confidence:** verified arithmetic.

### B-10 [DOC] Stale Notes and text for this sheet's power parts
- **R417/R517 and R435/R535 Notes, sheet note 11:**
    - They say "MCU (PB8)", "IWDG reset" and "Standby all inhibit".
    - On the CC2340, CHG_INH is DIO24. Its GPIOs latch in Standby, so Standby no longer inhibits by itself.
    - Reset, unprogrammed, bootloader and WDT reset still inhibit (Reviewer A, SWRS349A §8.11; A lists this as A-11).
    - The bringup checklist §4 "PB8 … Use Stop0–2, never Standby" is likewise STM32 text (A's area).
- **R441/R541 Note:** says "TPD2S300 FLT"; the part is now the TPD4S201 (C's part; flagged for completeness).
- **circuit-description §7.3:**
    - USB-side polymer is listed as "ChuangHui SV680M350… 68 µF". It is the Honor HV1V107M0607PZ 100 µF (C5246554).
    - FSW and RAC2 are listed as "C17678" (0805). They are C12447 (0603).
    - "VFB_REG set to ~1.527 V". Should be 0x0F = 1.534 V.
    - TS "TH5 / TH6 … ~−20 °C to ~95 °C window". Should be TH401/TH501, −7.6 to 94.5 °C.
    - The bootstrap diode is listed as "LRB521S-40T1G, C135802". It is the LRB520S-40T1G, C132124.
    - "CE pulled low (charge enabled)". It is now R417 47k to 3V3 with CHG_INH.
    - The open line "check how ACUV/ACOV behave in reverse mode" is still open.
- **circuit-description §7.4:**
    - "Output 2 × 22 µF 35 V 1206". C441/C442 are 25 V (CL31A226KAHNNNE), and the 220 µF polymer C443 is not mentioned.
    - §8 says "0 Ω links (0805) … PACK_P to each TPS62933". It is now the solder jumper R431/R531.
- **cost-down A3 and the C431/C434/C435 Notes:** "check temperature in boost-mode charging (5.5 A, 9 V → 16.8 V)" is not a real operating point.
    - A 9 V PDO is ≤ 3 A (27 W), giving a battery current of about 1.5 A and a battery-cap ripple of IBAT·√(VBAT/VAC − 1) ≈ 1.4 A rms.
    - The largest battery-side ripple is reverse buck to 9 V / 3 A: 3·√(D(1−D)) ≈ 1.5 A rms.
    - Both are fine for 3 × 1206 + polymer.
- **cost-down A16 and README item 38:**
    - "about 0.5 W per FET … split across two packages" is wrong: see B-2.
    - "fully on from REGN (5 V)" is wrong for the high sides: they get 4.24 V at best and sag to VBTST_REFRESH (B-1).
- **L401 Note / circuit-description:**
    - "Isat 18 A, Irms 12 A" are **typical** values (SMMS table header "Typical").
    - The rendered curve gives ΔT about 30–33 °C at 12 A and 40 °C at about 13 A. L is −17 % at 15 A and −21 % at 18 A, so it saturates softly.
- **L402 Note:**
    - "Isat 8 A (review 2: > 5.8 A IHS limit)". APS defines Isat at **−40 %** L ("Lo to drop approximately 40 %", p.1); the SRP5030T it replaced used a smaller drop.
    - Not like-for-like. It is still acceptable: soft carbonyl core, and IHS max 5.8 A is a fault-only peak.
- **Confidence:** verified (text against parts.txt and the datasheets).

### B-11 [NOTE] PGQ04N070 against the shared AGM_PDFN-8 footprint: pinout and land match
- **Package (p.1 drawing, rendered):** "S S S G" on one row with the pin-1 dot at the first S; "D D D D" opposite.
- **Footprint:** pads 1–3 S and 4 G at y = +1.575 (x = −0.975 → +0.975); pads 5–8 D; pad 5 is the 2.45 × 2.565 drain land, covering D2 2.35–2.55 × E2 1.635–1.835 plus the drain leads.
- **Dimensions:** b 0.30 lead against 0.40 pad. L 0.3–0.5 against a 0.75 pad that extends 0.3 mm beyond the 3.3 mm body.
- **Option 2 package:** its split drain pad (2 × D3 1.035) also lands inside pad 5.
- **Symbol and netlist:** S = .1–.3, G = .4, D = .5–.8 for Q401/Q402/Q407/Q408 in `nets.txt` (SW1/SW2/GND/AC_SNS_N/BAT_SNS_P as intended).
- **Caveat:** the JinYu sheet does not number the pins; standard PDFN3333 numbering is assumed (inferred). Verify with the first reel's marking dot.

### B-12 [NOTE] BQ25756 pin pass and programming math: verified
- **Pins:** all 37 against Table 4-1 and fig. 4-1 (rendered).
    - Footprint pads 1–10 left, 11–18 bottom, 19–28 right, 29–36 top, 37 EP 3.6 × 4.6. Matches the RRV drawing.
    - NC 15/16/31 floating ("do not tie to PGND"). PGND 17/22/37 on GND; there is no separate AGND, so no split is needed.
    - VAC 32/33 both on PPHV with the ACUV/ACOV top on the same net. In layout, take the divider from pin 33 (§4 pin 33 text).
- **ICHG** 9.1k: 5.22–5.77 A. **ILIM** 3.6k with KILIM × 2/5 (§6.3.5.1.1): 5.28–5.84 A.
- **ACOV:** trip 21.75–23.01 V (nominal 22.46 V), release about 21.5 V. **ACUV:** trip 4.02–4.19 V. **VACUV_DPM** floor: 4.40–4.62 V.
- **FSW:** 40.2k gives 598 kHz (Table 6-2: 40k → 600 kHz), ±15 % = 509–688 kHz. That is at the top of the 200–600 kHz recommended range; the 2.2 µH minimum L still holds.
- **L/DCR** = 2.2/7.2 = 0.31 µH/mΩ, inside 0.05–1.26 (§7.2.1.2.4). DCR 7.2–9 mΩ ≥ RDCR min 1.75 mΩ.
- **Gate drive:**
    - Qg(5 V) about 6.9 nC (fig. 6). REGN load is 16.6 mA for 4 FETs, against the 70 mA limit.
    - PREGN = (22.6 − 5) × 27.7 nC × 598 k = 0.29 W, against the 1 W SOA.
    - Boot droop per cycle: 0.07 V.
    - Induced VGS (Crss/Ciss) is 0.13 V. Not an issue.
    - DRV_SUP 4.63 V min > VDRV_UVPZ 3.7 V, also at VAC = 5 V (REGN 4.35 V → 4.18 V).
- **D404/D405:** 40 V against a reverse bias of at most VAC (23 V), 58 %. VF 0.39 V at 10 mA.
- **C412/C413:** 0.1 µF 50 V X7R. BTST−SW abs max 14 V against 5 V.
- **Filters:** ACP/ACN and SRP/SRN are 10 Ω + 0.1 µF CM + 0.47 µF diff, as the EVM.
    - Polarity: ACP on PPHV (R424.1), ACN on AC_SNS_N; SRP on BAT_SNS_P, SRN on VBAT_SYS. Forward current makes both positive.
    - Normal differential is ≤ 63 mV (12.6 A × 5 mΩ) against ±0.3 V abs max. A shorted-bank pulse above 60 A would exceed it, but the 20 Ω/0.47 µF filter (τ 9.4 µs) and 10 Ω pin current limit cover it.
- **FB top** from VBAT_SYS (battery side of RBAT), as TI does. FBG goes hi-Z outside the ACUV/ACOV window, so there is no battery drain (pin 11 text).
- **CE:** R417 47k to 3V3, R435 1k from CHG_INH.
    - Low gives 0.07 V (VIL 0.4 V); hi-Z gives about 3.3 V (VIH 1.3 V); abs max 6 V.
    - With 3V3 down, CE is low and a dead pack still charges.
    - CE does not gate reverse mode (§6.3.6, review 2 B-1).
- **STAT/PG/INT:** open drain to 3V3 / LDO_3V3, within the 6 V / 40 V abs max. They cannot back-power anything.

### B-13 [NOTE] L401, sense resistors, banks and R430 at the worst operating points: within ratings

| Case | Ripple p-p (nominal → L −20 %, f −15 %) | Peak | Irms |
|---|---|---|---|
| Forward buck 20 → 10 V, 5.77 A | 3.8 → 5.6 A | 8.6 A | 6.0 A |
| Forward boost 5 V / 9 V, 3 A in | 3.9–4.7 A | ≤ 5.3 A | |
| Reverse 100 W from 11.2 V (9.6 A) | 5.5 A | 12.4 A | 9.7 A |
| Reverse ceiling, no config, 10 V (12.6 A) | | 15.4 A | 12.7 A |

- The ceiling case peak (15.4 A) is below Isat 18 A typ, and L falls only about 17 % at 15 A (curve). Irms 12.7 A is at the ΔT ≈ 40 °C point.
- **R424/R427** PA2010 5 mΩ 2 W: at most 0.17 W (RAC, 5.84 A) and 0.79 W (RBAT, 12.6 A); 0.5 W at IBAT_REV 10 A.
- **R430:** 3 mm × 3 mm 2 oz bridge, about 0.25 mΩ, 40 mW at 12.6 A. The "10 A" label is exceeded only in the no-config ceiling case.
- **USB-side bank:**
    - Worst case 80 (polymer −20 %) + 4 × 6.8 × 0.8 × 0.93 = **100 µF ≥ 80 µF**.
    - Ripple about 4.4 A rms (reverse 11.2 → 20 V, 5 A). The MLCCs take most of it, about 0.75 A in C421 against 1.5 A rated.
- **Battery-side bank:**
    - Worst case 80 + 3 × about 4.5 × 0.8 × 0.93 ≈ **90 µF ≥ 80 µF**. The 4.5 µF per cap at 16.8 V is inferred from a typical 1206 25 V X5R; the Samsung catalogue has no curve.
    - Ripple ≤ 1.5 A rms (B-10). C432 is rated 2.65 A.
    - Distribution "equally on either side of RAC/RBAT" (§7.2.1.2.5/6) is still not followed (review 2 B-6, closed).

### B-14 [NOTE] Fault injection on paper
- **VBUS shorted while sourcing:**
    - The 4-switch topology can always block. Q402 (battery-side HS) is the input switch in reverse, and its body diode points SW2 → BAT, so there is no free-wheel path from the pack.
    - The reverse UVP (VAC < 80 % VAC_REV, REG0x1E) stops it. The bank's 25 mJ dump into the short is the TPS25751 PPHV switch's job (C).
- **Battery-side short (BAT_SNS_P or VBAT_SYS to GND):**
    - From VAC there is no body-diode path: Q401 body diode SW1 → AC_SNS_N.
    - The charger falls to trickle (VBAT_SHORT 2.8–3.2 V) and has VICHG_OC at 120–170 mV / 5 mΩ.
    - From the pack it is a pack short through R427/R430, handled by gauge SCD and F102 (D).
- **Pack disconnected while charging at 5.5 A** (gauge opens CHG): 70 µJ inductor energy into about 100 µF gives about 44 mV. The charger then regulates the bank to VFB; BAT_OVP is 104 %.
- **VBUS hot-plug at 20 V:** the FET bank never sees it directly.
    - The PPHV switch is open at attach. It closes only after negotiation, with slew control (0.35–3.8 V/ms, README item 15), so inrush into the bank is ≤ 0.5 A.
    - Non-compliant live 20 V plug: C406 4.7 µF + C450 + D401 at the connector; the TVS starts at 24.4 V. VBUS-side stress is C's.
- **Reverse 20 V / 5 A:** see B-1/B-2. Electrically OK; thermally the limiting case.
- **Never configured (blank EEPROM):** the BQ25756 starts in default mode and charges (§6.4 p.37):
    - ICHG 5.2–5.8 A (pin), input ≤ 5.84 A (pin), VBAT 16.70–16.96 V, JEITA on (B-8), timers 2 h / 12 h.
    - EN_REV = 0, so there is no sourcing.
    - It charges only when CE is low: 3V3 down, or the MCU driving CHG_INH low. An unprogrammed MCU leaves it hi-Z, so CE is high and there is no charge.
    - IAC_DPM stays at maximum, so a 3 A PDO could be over-drawn up to 5.8 A until C's Q12/Q13 config is in place.
    - Acceptable with the gauge COV as backstop.

### B-15 [NOTE] TPS62933 (U404/U504): pin pass and design equations
- **Pins:** RT → GND (1.2 MHz, 1.0–1.35 MHz).
    - EN: DIO3 / EN_5V1 with R432 100k pull-down. 0.7 µA × 100k = 0.07 V, so it is off in MCU reset. 3.3 V drive against the 1.21–1.28 V threshold and 6 V abs max.
    - VIN: from PACK_P via R431.
    - BST: C440 0.1 µF 50 V (≥ 16 V required).
    - SS: C439 33 nF, tSS 4.8 ms, inrush into about 250 µF about 0.26 A.
    - FB: 107k/20.0k 0.1 %.
- **Vout:** 5.08 V nominal; 5.00–5.16 V at 0–85 °C; 4.97–5.19 V full range. Above the 4.9 V TPS25751 minimum except at the extreme cold corner of VFB (784 mV, below 0 °C).
- **Inductor:** 3.3 µH at 1.2 MHz matches Table 10-2 (5 V, 1.2 MHz: 3.3 µH, Cout 20 µF typical / 10 µF minimum). Ripple ≥ 10 % of 3 A at all VIN.
- **Duty and input range:** tON = 224 ns at 16.8 V, above the minimum. PACK_P 10–16.8 V is inside 3.8–30 V (abs max 32 V).
- **Output capacitance:** about 250 µF effective (2 × 22 µF + 220 µF polymer, needed for PD cSrcBulkShared 120 µF). That is 12× TI's typical value; §10.2.2.8 asks for "a careful study of start-up at full load and loop stability". Bring-up: a load-step test with C447 (10 pF FF) fitted and not fitted.
- **Input caps:** 2 × 10 µF 50 V 1206 (about 5 µF each at 16.8 V) + 0.1 µF. Ripple 1.4 A rms total.
- **R431 bridge:** two 0.4 × 0.5 mm 2 oz bars, about 0.15 mΩ, carrying ≤ 1.73 A (3 A out from 10 V). Fine.
- **APS0530 land:** F 6.0 / G 2.5 / H 2.2 → 1.9 × 2.5 pads at ±2.05. Matches `L_Coilank_APS0530`.
- **SMMS1040 land:** 4.1 / 13.6 / 5.4 → KiCad `L_Changjiang_FXL1040` (4.1 × 4.1 pads at ±4.75). Matches.

### B-16 [NOTE] Port 2 is an exact copy of port 1
- `scratch-b/port_compare.py` maps 4xx → 5xx: 382 pins per port.
- The only net differences are the ADCIN1/ADCIN2 straps (intended) and the LDO_3V3 net name (port 1's is `/P1_LDO_3V3`). Connectivity is identical (C's naming).
- All 4xx/5xx part values, footprints, MPNs, LCSC numbers and Notes match. The 5xx Notes say "Q401" etc., which is harmless.

### B-17 [NOTE] Worst-case derating table, power parts on this sheet

| Part | Rating | Worst applied | Stress | Comment |
|---|---|---|---|---|
| Q401/Q407 VDS | 40 V | 23.0 V (ACOV) + ring; 35.5 V surge | 58 % / 89 % | B-6 |
| Q402/Q408 VDS | 40 V | 16.8 V + ring | 42 % | |
| FET VGS | ±20 V | 5 V | 25 % | |
| FET Tj | 150 °C | about 110–130 °C at 100 W reverse (inferred) | | B-1/B-2 |
| D404/D405 VR | 40 V | 23 V | 58 % | |
| C420/C423/C424/C427 (35 V X5R 1210) | 35 V / 85 °C | 23 V / TS cutoff 81 °C (config) | 66 % | |
| C421 polymer | 35 V, 1.5 A rms | 23 V, about 0.75 A | 66 % / 50 % | |
| C431/C434/C435 (25 V X5R 1206) | 25 V | 16.8 V | 67 % | above the 50 % guideline; capacitance still OK (B-13) |
| C432 polymer | 25 V, 2.65 A | 16.8 V, ≤ 1.5 A | 67 % / 57 % | B-4 |
| C430/C438/C409/C412/C413 | 50 V | 23 V | 46 % | |
| C410/C411 | 25 V | 5 V | 20 % | |
| C444/C445 | 50 V | 16.8 V | 34 % | |
| C441/C442 | 25 V | 5.2 V | 21 % | |
| C443 | 16 V | 5.2 V | 33 % | |
| L401 | 18 A sat (typ), 12 A rms (typ), 30 VDC | 15.4 A peak, 12.7 A rms (ceiling) / 12.4 A, 9.7 A (100 W) | 86 % / 106 % ceiling | |
| L402 | 8 A sat (−40 %), 5 A rms | 3.7 A peak, 3.3 A | 46 % / 66 % | |
| R424 | 2 W | 0.17 W | 9 % | |
| R427 | 2 W | 0.79 W (ceiling) / 0.5 W | 40 % / 25 % | |
| R450/R451 | 0.125 W | 0.55 W if sized per the Note | 440 % | B-3 |
| U404 | 3 A | 3.0–3.3 A | 100–110 % | B-7 |
| U403 PREGN | 1 W SOA | 0.29 W | 29 % | |

---

## Checked and correct (coverage list)
- U403: all 37 pins, abs max per pin, NC handling, PGND/EP.
- ICHG, ILIM (KILIM scaling), FB with RFBG, ACUV/ACOV/VACUV_DPM, FSW, TS thresholds (charge and reverse), CE levels, FBG behaviour.
- BTST caps, D404/D405 orientation and rating, REGN/DRV_SUP caps and the R420 drop, REGN load and SOA.
- ACP/ACN and SRP/SRN filters, polarity and abs max.
- PGQ04N070: VDS, VGS, Vth, RDS(on) against temperature, Qg at 5 V, dead time against turn-off, dv/dt turn-on, body-diode and Qrr losses, footprint pin by pin, package dimensions.
- L401: value, Isat/Irms against all modes, L/DCR window, footprint. L402: value, Isat, ripple, footprint.
- R424/R427 power and sense voltage. R430 current.
- Both banks: ≥ 80 µF after bias, tolerance and temperature. Polymer voltage, ripple and leakage. MLCC voltage stress.
- TPS62933: every pin, FB, EN, SS, BST, RT, inductor, caps, VIN range, current limit, thermal, R431.
- Port 2 netlist and parts identical to port 1.
- Fault cases: VBUS short sourcing, battery-side short, pack disconnect, hot-plug, reverse 100 W, POR and never configured, CE.

---

## After round 2

**Challenges answered:** A-challenge (B-1, B-2), C-challenge (B-1, B-2, B-6, B-14) and D-challenge (B-1, B-2, B-4). There was no DISPUTE against any B item.

**Final grades:** no grade changes.
- 0 CRITICAL, 1 MAJOR (B-1), 6 MINOR (B-2 to B-7), 2 CONFIG (B-8, B-9), 1 DOC (B-10), 7 NOTE (B-11 to B-17).
- B-1 now also carries an interim CONFIG fix: IBAT_REV = 5 A.

### B-1 [MAJOR, confirmed by A, C and D]: AMEND (the evidence is stronger; the fix is now concrete)

**Amendments accepted:**
- **Start voltage (C):** the gate starts each refresh period at about **4.0–4.2 V**, not 4.24 V. D405 carries the refresh pulse at hundreds of mA, not at the 10 mA VF test point (LRB520S-40: VF ≤ 0.55 V at 100 mA).
- **A typical part also fails (D):**
    - PGQ04N070 fig. 4 at VGS 3.0 V needs VDS ≈ 0.8 V for 12.6 A, about 10 W while the gate sits there.
    - Fig. 8 typical at VGS 2.7 V gives only about 8–9 A even at VDS = 5 V.
    - So with a BQ25756 that refreshes at its 2.7 V minimum, **even a typical PGQ04N070 cannot carry 10–12.6 A**. A maximum-threshold part (2.5 V) passes about 1 A at 3.0 V.
    - D's sawtooth average for a typical part at 12.6 A: **≈ 2–2.5 W hot, ≈ 3 W cold**, against the 1.36–2.16 W in B-2.
- **Direct evidence in fig. 6 (C):** the Miller plateau sits at about 3.0 V at 20 A. A gate held near 3 V is at the edge of saturation by the datasheet's own curve.
- **Fix (c) does not block the change (C):** agreed. The datasheet describes only the comparator, so the design must work to it.
- **Neither DRV_SUP nor C413 moves the floor:** it is set by VBTST_REFRESH (C and D confirm).

**Fix (a), made concrete.** Two specs, because the two high sides see different voltages and currents:

| Position | Duty-100 % case | VDS seen | Spec for the replacement |
|---|---|---|---|
| **Q402/Q502** (battery-side HS) | Reverse boost at 9–12.6 A; forward buck ≤ 5.8 A | VBAT ≤ 16.8 V + ring | Single N-FET, PDFN3333 (DFN 3.3 × 3.3), pins S 1–3 / G 4 / D 5–8 (fits `AGM_PDFN-8_3.3x3.3mm_P0.65mm`). VDS ≥ 30 V with a VDS-spike rating ≥ 36 V. **VGS(th) max ≤ 1.5 V. RDS(on) max specified at VGS = 2.5 V, ≤ 5 mΩ.** VGS rating ≥ ±12 V. Qg(4.5 V) ≤ 40 nC. If Qg > 15 nC, raise C413/C513 to 0.22 µF so the per-cycle droop stays ≤ 0.2 V when it switches. |
| **Q401/Q501** (USB-side HS) | Forward boost at ≤ IAC_DPM (≈ 3 A, C-11; ≤ 5.8 A unconfigured); reverse buck ≤ 3 A | VAC ≤ 23 V + ring | PDFN3333, same pinout. **VDS ≥ 40 V. VGS(th) max ≤ 2.0 V.** RDS(on) at 4.5 V ≤ 10 mΩ. A typical transfer curve showing ≥ 10 A at VGS 2.7 V. A 2.5 V RDS(on) spec is preferred, but none exists at 40 V in this package (see below). |
| **Q407/Q408** (low sides) | never refresh-limited (LODRV = DRV_SUP ≈ 4.6 V) | | Keep PGQ04N070 |

- **The 30 V choice for Q402** puts 16.8 V at 56 % of rating. A 30 % ring (about 22 V) is 73 %. That is above the 50 % guideline but inside a 36 V spike rating. Measure SW2 at bring-up; the R451/C455 snubber pads are there.

**Candidates.** Datasheets are fetched to `scratch-b/cand/`. LCSC stock could **not** be verified from this machine: the LCSC search API returns "Access Denied" and the JLC database is not downloaded. The lead or Logan should check stock in a browser.

| Part | Role | Key data (datasheet, read) | Status |
|---|---|---|---|
| **AOS AON7520** | Q402/Q502 | 30 V (VDS spike 36 V, 100 ns); VGS ±12 V; **VGS(th) 0.5 / 0.85 / 1.2 V**; **RDS(on) < 3.1 mΩ at VGS = 2.5 V**, < 2.1 mΩ at 4.5 V; Qg(4.5 V) 37 nC typ; RθJA 45 typ / 55 max °C/W steady state; DFN 3.3 × 3.3 EP, pins S 1–3 / G 4 / D 5–8 (p.1, rendered). https://www.aosmd.com/res/datasheets/AON7520.pdf | Meets the Q402 spec. Distributors list it as **NRND**. Use it as the reference for the spec, not a long-term part. |
| **Vishay SiS488DN** | Q401/Q501 | 40 V; VGS(th) 1.1–**2.2** V; RDS(on) 7.5 mΩ max at 4.5 V; PowerPAK 1212-8 (3.3 × 3.3, S 1–3 / G 4 / D 5–8). https://www.vishay.com/docs/62882/sis488dn.pdf | Vth max is 0.2 V over the target. Acceptable only with IAC_DPM ≤ 3 A (C-11) plus a transfer-curve check at 2.7 V. |
| **Vishay SiSA72DN** | Q401/Q501 (fallback) | 40 V; VGS(th) 1.1–2.4 V; RDS(on) 4.8 mΩ max at 4.5 V; PowerPAK 1212-8. https://www.vishay.com/docs/75680/sisa72dn.pdf | Not compliant (Vth max 2.4 V). Listed to show where the 40 V class tops out. |

- **Also checked and rejected** (VGS(th) max 2.2–2.6 V, no 2.5 V spec): AON7400A, AON7408, AON7522E, AON7528, AON7536, AON7506, AONR32320C. Their datasheets are in `scratch-b/cand/`.
- **The search result:**
    - I found no 40 V PDFN3333 part with an RDS(on) spec at 2.5 V. I searched Vishay's PowerPAK 1212-8 range, onsemi, Panjit, VBsemi and the LCSC listings.
    - 2.5 V-rated parts in this package are 20–30 V.
    - That is why the spec is split by position.
- **If no compliant 40 V part is found for Q401**, keep a PGQ04N070-class part there, but:
    - limit IAC_DPM to ≤ 3 A (C-11) and reverse-buck output to ≤ 3 A;
    - verify at bring-up that Q401 stays ohmic at VGS 2.7–3.1 V and 3 A.
    - At 3 A the fig. 8 typical part has margin. Only the high-threshold tail fails.

**Interim CONFIG (D's addition, accepted):**
- Until the high sides are changed, the bundle writes **IBAT_REV = 11b (5 A)** (bq25756 Table 6-50: 00b 20 A, 01b 15 A, 10b 10 A, 11b 5 A). This replaces the checklist's 10 A for boards with PGQ04N070 on Q402/Q502.
- At 5 A, fig. 4 typical at VGS 3.0 V gives about 0.15 V, about 0.75 W. That caps reverse output at about 57 W from a 12 V pack (5 A × 12 V × 0.95).
- The source PDOs must match: 20 V ≤ 2.5 A, or 15 V ≤ 3 A. Otherwise the BQ25756 sags VAC under IBAT_REV regulation and the sink sees an under-voltage.
- Restore 10 A only after the fix-(a) FETs are fitted.

**Bring-up check (b) stands.** Probe HG2–SW2 and VDS(Q402) in reverse mode at the IBAT_REV limit, record the refresh interval and the minimum VGS, then repeat with the board hot.

**Confidence:** verified for the candidates' datasheet limits and pinouts (AON7520 p.1 rendered). Stock and lifecycle are unverified.

### B-2 [MINOR]: AMEND (folding in B-1 and A's per-position split; grade stays MINOR)

**Per-position table** (reverse 100 W, 12 V pack, I_L 8.87 A; RDS 13.6 mΩ max hot; A's attribution):

| Position | A's split, 4.5 V drive | With the B-1 refresh sag (typical part, hot) |
|---|---|---|
| Q402 HS2, 100 % on | 1.10 W | **1.4–1.8 W** at 8.9–9.6 A (C); **2–2.5 W** at 12.6 A (D) |
| Q407 LS1, hard-switched (including Q401's Qrr) | 1.44 W | 1.44 W |
| Q401 HS1, synchronous rectifier (conduction + dead time) | 1.04 W | 1.04 W |
| Q408 LS2 | off | off |
| **Stage** | 3.6 W | **≈ 3.9–4.3 W** (9.6 A) |

- **Qrr placement:** A is right that Q401's body-diode Qrr dissipates in the FET that turns on (Q407). Moved; the stage total is unchanged.
- **Grade:** MINOR holds, per A: Tj ≈ T_copper + P × (4.46 + about 5) °C/W, and the TS stop (81 °C with TS_T5 = 00b) bounds the copper, giving Tj ≤ about 110 °C. It holds **on two conditions**:
    - (1) TH401/TH501 sits on the Q402/Q407 copper. This is a layout requirement and must go into the README/layout notes.
    - (2) B-1 is fixed, or the interim IBAT_REV = 5 A applies. A saturated Q402 is not bounded by TS, because it heats in milliseconds.
- **Published RθJA for the package class:** AON7520 gives 45 typ / 55 max °C/W steady state for DFN 3.3 × 3.3 EP. This replaces my inferred 40–60 °C/W.
- **The cost-down A16 DOC correction stands** (B-10).

### B-14 [NOTE]: AMEND (C), conceded
- TPS25751 table 8-6 (SafeMode): "The device does not enable the sink path. USB PD is disabled until configuration is loaded." §8.4.1: without an EEPROM it waits for a host.
- Replace the "Never configured" bullet with:
    - "**Blank EEPROM:** the TPS25751 never closes PPHV, so the BQ25756 never sees VAC from USB. No charging.
    - **Configured bundle that does not write the BQ25756:** default mode charges at ICHG 5.2–5.8 A (pin), VBAT 16.70–16.96 V, JEITA on, whenever CE is low.
    - **Bundle without Q12/Q13:** IAC_DPM stays at the 5.3–5.8 A pin ceiling (C-11)."

### B-6 [MINOR]: AGREE with C's addition
- A TVS2200-class flat clamp (C-4) lowers the PPHV surge from 35.5 V to about 28 V. That improves the FET margin here (89 % → 70 %) as well as C-4.
- The lead should decide the two together.

### B-4 [MINOR]: no change
D carries it in the rev A7 budget, FETs-on idle only.

### Not challenged
B-3, B-5, B-7 (owned by C as C-5), B-8 to B-13, B-15 to B-17 stand as written.
