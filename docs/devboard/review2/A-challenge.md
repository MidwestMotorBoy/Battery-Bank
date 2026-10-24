# Reviewer A — challenge round (round 2) against B-findings.md and C-findings.md

Lead's questions assigned to A: 6 (B-3), 7 (B-4), 8 (B-5), 9 (C-1/B-17), 10 (C-3). All were re-derived independently.
Datasheet figures were rendered with PyMuPDF and read off the plots.

---

## Lead's questions

### Q6 / B-3 vs B: AMEND. B's leakage is about 10× too high for a typical part, but a max-spec part near the TS cutoff does reach marginal thermal stability. Keep it MINOR and swap the part.

**LRB521S-40T1G datasheet** (LRC Rev.O, fetched from chipdip; saved in scratchpad/review2/A/dl1/e.pdf):
- IR max is 20 µA at 10 V and 90 µA at 40 V, at 25 °C. Tj max is 125 °C.
- The VR–IR curve family (typical) at VR = 20 V, read from the rendered plot:

  | Ta | IR (typ) |
  |---|---|
  | 25 °C | ≈ 4 µA |
  | 75 °C | ≈ 120 µA |
  | 125 °C | ≈ 1.8 mA |
  | 150 °C | ≈ 20 mA |

- Leakage therefore doubles about every 12.8 °C (×15 from 75 to 125 °C).
- At 100 °C it is about 0.5 mA typical, not the 4–8 mA B estimated from a generic 2×/10 °C rule applied to the max spec.

**Reverse voltage seen:**
- D404 (BTST1): the cathode is at SW1 + V_BTST and the anode at DRV_SUP (≈ 5 V). VR ≈ VAC = 20 V (up to ACOV 22.5 V) while HS1 is on, which is D ≈ 0.85 in buck mode from 20 V to a 16.8 V pack.
- D405 (BTST2): in buck mode HS2 is held on, so SW2 = VBAT and VR ≈ 16.8 V nearly 100 % of the time. In reverse boost mode at 20 V out, D405 sees ≈ 20 V and D404 sees VBAT.

**Self-heating:**
- No thermal resistance is given for the LRB521S. The LRB520S sheet gives RθJA = 500 °C/W (30 × 25 mm FR4 pad); B used 667 K/W.
- Typical part at a 95 °C board (the TS cutoff, 94.5 °C, B-2): IR(100 °C) ≈ 0.5 mA, so P = 20 V × 0.5 mA × 0.85 = 8.5 mW → +4–6 °C → Tj ≈ 101 °C. Stable. The runaway criterion Rth·dP/dT = 500 × 0.054·P < 1 requires P < 37 mW.
- Max-spec part: 25 °C IR max/typ is about 20/4, so ×5 → 2.5 mA at 100 °C → 42 mW → +21–28 °C → Tj ≈ 120 °C, where IR is ≈ ×3.7 higher. **Thermal runaway is possible at a 90–95 °C local board with a worst-case part.**
- The bootstrap droop from leakage is negligible: 2.5 mA × 1.4 µs / 0.1 µF = 35 mV.

**Replacement:** LRC **LRB520S-40T1G, LCSC C132124**. LCSC datasheet (S-LRB520S-40T1G Rev.D, fetched):
- Same SOD-523, same 40 V, IO 200 mA, Tj 125 °C, RθJA 500 °C/W.
- IR max 1 µA at 10 V and 10 µA at 40 V: 9–20× lower.
- VF max 0.39 V at 10 mA and 0.55 V at 100 mA, against 0.30/0.45 V for the LRB521S. That is ≈ +0.1 V at the refresh pulse, which only matters at VAC ≈ 5 V (B already flagged that headroom).

**Verdict:** keep MINOR, with B's numbers corrected as above. Swap to LRB520S-40T1G (C132124) and measure D404 temperature at bring-up.

### Q7 / B-4 vs B: UPHOLD MINOR, and add the two-port case
- **EVE limit:** eve-inr21700-58e §3.4 / §7.2 (and docs/archive/eve-58e-datasheet-notes.md) say "Maximum Charge 5.6A(1C) … (not for cycle life)", charge temperature 0–45 °C ambient. No higher continuous charge rating exists, so 5.6 A is the absolute charge maximum.
- **Ceiling math, re-derived:**
  - I = KICHG / R_ICHG × (5 mΩ / RBAT).
  - KICHG max 52 A·kΩ (bq25756 §5.5), 9.1 k −1 %, RBAT −1 %: 52 / 9.009 / 0.99 = 5.83 A. That is 4 % over EVE's maximum.
  - Minimum: 48 / 9.191 / 1.01 = 5.17 A.
- **When it applies:** ICHG_REG POR is 20 A, so the pin is the effective limit at POR. That covers the window between BQ25756 POR and the TPS25751 configuration write on a dead-battery attach, a blank or failed EEPROM, and after a watchdog reset if EN_CHG_BIT_RESET_BEHAVIOR is not set.
- **Missed by B: two ports in that same window** charge at 2 × 5.17–5.83 = 10.3–11.7 A, which is 1.9–2.1C. Gauge OCC1 (≈ 6 A planned) catches it after its delay. This is the larger exceedance.
- **Fix:** B's R413/R513 = 9.53 k checks out: 52 / (9.53 × 0.99) / 0.99 = 5.57 A ≤ 5.6 A; nominal 5.25 A. Keep OCC1 ≈ 6 A with a short delay as the two-port backstop.

### Q8 / B-5 vs B: UPHOLD MINOR. B's DC-bias figure was optimistic, so the shortfall is slightly larger than B states
- **Source of the 80 µF:** bq25756 §5.3 Recommended Operating Conditions (B_txt/bq25756.t.txt line 525): "CIN Buck input capacitance (minimum value after derating) 80 µF"; COUT is the same (line 527). §7.2.1.2.5 asks for the bulk to be split across RAC_SNS. That supports B-6, not B-5.
- **GMK325BJ226MM DC bias**, read from the rendered Taiyo Yuden "DC Bias Char." plot: −60 % at 15 V, **≈ −69 % at 20 V** (→ 6.8 µF, not the design's 8.5 µF), −76 % at 25 V.
- **Temperature:** "Capacitance Temp." gives about −7 % at 85 °C (B used −15 %).
- **Totals** at 20 V, with C421 68 µF polymer ±20 % (no bias loss):
  - Nominal: 4 × 6.8 + 68 = 95 µF. OK.
  - −20 % tolerance on all parts, 25 °C: 21.8 + 54.4 = 76 µF.
  - Plus 85 °C on the MLCCs: 20.3 + 54.4 = **75 µF < 80 µF**.
- **Battery side, for comparison:** TMK325ABJ476MM is ≈ −78 % at 16.8 V (10.3 µF each) and −10 % at 85 °C. 3 × 10.3 × 0.8 × 0.9 + 80 = 102 µF ≥ 80. OK.
- **Fix:** B's fifth 22 µF or a 100 µF 35 V polymer for C421 is right. Polymer is the better choice: it adds no DC-bias-dependent capacitance and keeps the PPHV sink-bulk story of README item 15 unchanged.

### Q9 / C-1 + B-17 vs C and B: UPHOLD 100 k, with the margin re-derived. A polarity swap is the more robust option; I list it for the lead
- **CE limits:** bq25756 §5.5 Logic I/O (B_txt line 1171–1177): CE VIH 1.3 V min, VIL 0.4 V max, IIN_BIAS 1 µA. Pin table: "do not leave floating"; there is no internal pull.
- **100 k, MCU unpowered or reset** (PB8 analog / hi-Z): CE = 1 µA × 100 k = 0.1 V < 0.4 V. Fail-open is preserved, and dead-battery revival still works.
- **100 k, MCU in Standby with the APC pull-up** (25–55 kΩ):
  - PB8 load is two branches of (1 k + 100 k) in parallel = 50.5 k.
  - Worst RPU 55 k: PB8 = 3.3 × 50.5/105.5 = 1.58 V. CE = 1.58 × 100/101 = 1.56 V.
  - Including the 1 µA high-level leakage per CE pin (2 µA × ~26 k Thevenin ≈ 0.05 V): CE ≈ 1.51 V > 1.3 V.
  - **Margin is ≈ 0.2 V.** It works, but it is thin.
  - Anything below about 82 k fails: 47 k gives CE ≈ 0.98 V.
- **Noise:** the SW-node coupling peak is set by charge sharing (C_stray × ΔV / C_pin+trace), not by the pull-down value. With 0.1 pF × 20 V on about 7 pF that is ≈ 0.3 V either way; 100 k only stretches it from ≈ 70 ns to ≈ 0.7 µs. Still below VIH. B's DNP 1 nF at CE removes it (RC with R435 = 1 µs).
- **Alternative: swap polarity** (pull-up from CE to 3V3, MCU drives PB8 low to allow charging):
  - Unpowered (dead pack, 3V3 down, and the TPS62177 actively pulls its output to GND per first-review #9): CE ≈ 0 V, so charging is allowed and dead-pack revival is preserved.
  - Powered but the MCU not actively enabling (reset, unprogrammed, hung, brown-out): CE high, charging inhibited. That is the fail-safe direction for the "software is the second layer" decision.
  - Costs:
    - Firmware is required to charge at all; on bring-up, force it via J303.6 (R319).
    - Sleep current is drawn through the pull-up while charging is enabled.
    - In Standby the APC pull-down must hold PB8 low against the pull-up. Use Stop2 while charging, as C already recommends.
  - It inverts decision Q2's stated intent, so it belongs to the lead or owner. **For rev 1 as built, 100 k is the minimal correct fix.**

### Q10 / C-3 vs C: DOWNGRADE to NOTE (keep the 100 Ω as a free robustness tweak). 30–31.5 V is an upper bound, not a credible typical
- **Loop:** PACK_P has no local bulk near JP202. C206 sits behind R201 (10 Ω), and C201 is DNP 22 nF. The source is the charger polymer/MLCC banks, so loop L is set by the PACK_P route: microstrip over In1 GND at 0.1 mm is ≈ 0.3–0.5 nH/mm, 50–100 mm, + ≈ 5–10 nH for the jumper header. Total L ≈ 30–60 nH.
- **C204** 1 µF 50 V 0805 X7R at 16.8 V ≈ 0.6–0.7 µF. Z0 = √(45 nH / 0.65 µF) ≈ 0.26 Ω. Ring frequency ≈ 1 MHz.
- **Damping R:** contact resistance during jumper insertion (sliding, initially point contact: tens to hundreds of mΩ), + C432 polymer ESR 30 mΩ in series with the source path, + trace (≥ 10–20 mΩ), + MLCC ESR ≈ 5 mΩ. That is 60–150 mΩ, so ζ = 0.12–0.29.
- **Overshoot** = exp(−πζ/√(1−ζ²)) = 0.69–0.39 → peak **23–28 V** from 16.8 V, 24–29 V from 17.5 V.
- C's ζ = 0.07 needs the whole loop at ≈ 35 mΩ including the contact, which is not realistic for a 2.54 mm shunt being pushed on. A finite contact-closure time (≥ the 1 µs ring period) lowers it further.
- **Against limits:** below the 32 V absolute maximum (tps709 §6.1) in every case. Only the most pessimistic combination touches the 30 V recommended maximum, and only for the ringing interval.
- **Fix:** the 100 Ω series resistor is still sensible. Drop at ~0.1 mA is 10 mV, and it costs a 0603. But this is not a MINOR defect.

---

## Other MAJOR / hardware-change MINOR items

### B-1 vs B: UPHOLD MINOR
- Confirmed in bq25756 §6.3.6 (B_txt lines ~2610–2655): reverse enable needs BAT > 3.8 V, EN_REV = 1, TS in window; CE is absent. Once running, reverse mode continues to 2.5 V.
- This is consistent with my A-1. The real fix is the EEPROM default PDOs + IBAT_REV, plus gauge CUV/OCD. The optional HIZ hardware is rev 2.

### B-2 vs B: UPHOLD MINOR
- Taiyo Yuden "Capacitance Temp." curves stop at 85 °C (X5R), and both curves are already falling steeply at 85 °C (−7 % / −10 %).
- B's TS math, re-checked: Rp = 0.3437 × 1.8 k / (1 − 0.3437) = 0.943 k → NTC = 1/(1/0.943 − 1/5.6) = 1.134 k → T = 367.7 K = 94.5 °C. Correct.
- The configuration fix (TS_T5 = 00b → ≈ 81 °C) is the cheap answer.

### B-6 vs B: UPHOLD MINOR (DNP pads)
- TPS25751 §9.4.1.2.2.3 asks for PPHV decoupling at the IC, and bq25756 §7.2.1.2.5–6 explicitly asks for bulk split across RAC_SNS/RBAT_SNS (B_txt lines 5522, 5558).

### B-7 vs B: UPHOLD (configuration only)
- It is the per-port view of my A-1. IBAT_REV = 10 A caps it.

### C-2 vs C: UPHOLD MINOR (cosmetic)
- InGaN at 0.5 mA is dim but visible. A 330 Ω resistor is free.

### C-4 vs C: UPHOLD MINOR
- One GND test point on a board whose purpose is scope work is a real testability gap.
- From my scope, add: a TP on CELL_P_RAW (A-4), and GND points near the gauge column labelled GND (TP102 is CELL_N, "not GND").

### C-5 vs C: DOWNGRADE to NOTE
- FTSH-105-01-L-DV-K is the shrouded part ARM's Cortex 10-pin debug guide shows. The shroud keys FFSD cables, which is the usual intent.
- Only the "pin 7 removed" wording in the notes/README is wrong. No hardware change is needed unless the owner wants pin-7 keying.

### C-6 vs C: UPHOLD MINOR
- Confirmed for my sheet: C101–C104, C107, C108, R105–R116 have no LCSC.

### C-7 vs C: UPHOLD MINOR
- TP308 at 5 V would exceed the TPS25751 I2Ct 4 V and the unpowered STM32 FT 4 V limits.
- Better still: prefer J104 for EV2400 work.

### B-17
- See Q9.

---

## Missed by everyone

### M-1 [MINOR] CHG_INH polarity choice (expanded in Q9)
- The present "pull-down = charge allowed" scheme loses the inhibit on every reset/Standby/hang while the board is powered. That is exactly when the "software second layer" is absent.
- A pull-up-to-3V3 scheme keeps dead-pack revival (3V3 is dead then, and the TPS62177's 175 Ω discharge holds CE low) and fails safe when the MCU is powered but not commanding.
- This is a design-intent decision for the lead.

### M-2 [NOTE] Reverse (source) mode runs the pack down to 0.6 V/cell unless the gauge acts
- bq25756 §6.3.6: once running, reverse mode continues to VBAT = 2.5 V. On 4S that is 0.63 V/cell.
- So the only cut-off for a sourcing port is gauge CUV (DSG off). Neither the MCU nor CHG_INH can stop it (B-1), and the TPS25751 only acts if configured.
- Add to the gauge configuration checklist:
  - CUV must be enabled.
  - Use a short CUV delay.
  - Set CUV ≥ 2.8 V/cell (loaded) if F101 stays 15 A (A-6 amendment).
- Also set the BQ25756 battery-side reverse UV, if the TPS25751 bundle can write a VBAT_REV_UV-type threshold (B to confirm the register).

### M-3 [NOTE] Two-port POR charge window (from Q7)
- 10.3–11.7 A (≈ 2C) until the TPS25751 bundles write ICHG_REG.
- The first review's #2 "sum kept by configuration" has an unconfigured gap:
  - after BQ25756 POR (a dead-battery attach), and
  - after any BQ25756 watchdog reset of ICHG_REG, if the BQ25756 is not otherwise kept configured while idle.
- Whether a normal attach with a live pack also has the gap depends on when the TPS25751 bundle writes ICHG_REG (B to confirm).
- Gauge OCC1 delay must be short (≤ 1–2 s) to bound it.
