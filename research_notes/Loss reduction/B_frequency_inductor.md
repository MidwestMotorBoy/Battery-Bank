# B — Switching frequency and the inductor

Researcher B, 2026-10-21. This is research only: nothing in the repo was changed.
- Model copy: `C:\Users\Logan\AppData\Local\Temp\claude\C--Users-Logan-Documents-BatteryBank\e185e067-8e49-4b1c-9840-e0e47a30eac1\scratchpad\model\freq_ind_B.py`. It imports `heat_sources_B.py`, an untouched copy of the model. The output is in `out.txt` beside it.
- Cap-sim sweep: `...\scratchpad\sims\hardware\Production\tools\fsweep.py`. It runs `low_profile_sims.py` from d994c3a with FSW and L changed.

## 1. What is there today, and what it really loses

**FSW_SYNC.** R412 is 40.2 kΩ. From bq25756.pdf eq. 3, R = 1 / (10·(f·5 pF − 500 n)), which gives **598 kHz**.
- The allowed range is **200–600 kHz** (ROC p.7), and the same range applies to SYNC.
- Table 6-2 (p.22) gives 200 k → 200 kHz, 133 k → 250 kHz, 100 k → 300 kHz, 66.7 k → 400 kHz, 57.1 k → 450 kHz and 50 k → 500 kHz.
- The tolerance is ±15 % (EC table: 425–575 kHz at 50 k). So today's setting sits right at the ROC maximum.
- Changing the frequency is **one resistor**.
- There is no external compensation: the loop is integrated and auto-tuned. The IC toggles SW for about 40 ms at start-up to "determine the correct compensation values for a given set of passives" (§6.3.3.3).

**Inductor rules** (ROC p.7 and §7.2.1.2.4):
- L from **2.2 to 15 µH** and DCR from 1.75 to 60 mΩ.
- I_sat > I_L + ΔI/2.
- Ripple 20–40 % of the maximum inductor current.
- Time constant 0.05–1.26 µH/mΩ. TI's own designs (10 µH/12 mΩ and 10 µH/19 mΩ) only fit if this means **L/DCR**, not L/R_SNS as schematic note 15 reads it. Today's part gives 0.16 µH/mΩ.
- The datasheet shows **no cycle-by-cycle inductor current limit**. BAT_OCP is 120–170 mV across the 5 mΩ RBAT, about 24–34 A averaged. So saturation margin is protected only by the part itself.

**Boost RHP zero** (eq. 35). At the 10 V → 20 V corner (R_load 3.4 Ω, D′ = 0.5), it is about 85 kHz with 1.6 µH. It drops to about 40 kHz with 3.3 µH and about 29 kHz with 4.7 µH. All of these are far above TI's worked example (11 kHz, which needed ≥ 80 µF), so a larger L is not a stability problem.

**L401/L501: Coilank APS0730M2R2F** (LCSC C49261221, 1,552 in stock, $0.56).
- 2.2 µH, 7.8 × 7.6 × 3.1 mm.
- **13.7 mΩ max** (aps0730.pdf p.6; the misaligned table reads 13.7 mΩ, Irms 13 A, Isat 17 A at a 40 % drop, confirmed by the LCSC listing).
- About 1.7 µH at 12 A (README).

**Corrections to the model** (all in the copy; deltas below are against a baseline run through the same copy):
- **Inductor DCR: 12 → about 15 mΩ.** The 12 mΩ figure is below the 25 °C maximum. Typical is about 12.5 mΩ, and the winding runs ×1.2 at 75–85 °C.
- **Ripple:** ΔI²/12 is now added to the FET and inductor I².
- **Core loss now follows volt-seconds and f.** It uses P = 0.20 W·k·(f/600k)^1.3·(ΔB/ΔB₀)^2.1, a Steinmetz form for metal-composite cores. It is anchored to the model's 0.20 W at a 4 A p-p ripple.
- **Gate drive is now V_AC × Qg × f**: 13.4 nC for the switching pair (siz240dt.pdf p.2; BQ25756 eq. 29), plus 0.03 W for the IC. This is the same correction researcher A found, so count it once.

Corrected losses, frequency- and inductor-dependent rows only:

| Today, 600 kHz | 30 W | 100 W | 100 W at 12 V | 88 W charging | 117 W from 10 V |
|---|---|---|---|---|---|
| Switching + dead time | 0.33 | 0.87 | 1.08 | 0.65 | 1.44 |
| Inductor DCR + core | 0.17 + 0.08 | 0.91 + 0.11 | 1.46 + 0.16 | 0.49 + 0.11 | 2.65 + 0.18 |
| Gate drive + IC | 0.10 | 0.19 | 0.19 | 0.19 | 0.19 |
| I_L / ΔI / I_pk, A | 3.3 / 2.7 / 4.7 | 7.8 / 3.5 / 9.5 | 9.8 / 4.4 / 12.0 | 5.6 / 3.3 / 7.3 | **13.2 / 5.2 / 15.9** |

The inductor row reads **1.03 W at 100 W** (the brief has 0.92) and **1.62 W at 12 V** (the brief has 1.3). At the 117 W hardware ceiling it is **2.8 W**, with 1.6 µH left at 13 A. Two things fall out of that:
- L at full load is already below the 2.2 µH ROC minimum.
- The 40 K-rise Irms of 13 A is used up.

The 117 W row counts only the board's losses in the current. The original model also adds the cell I²R to the battery current, which overstates I_L by about 5 % at 100 W.

## 2. Why a lower frequency alone doesn't pay at 3.2 mm

In a fixed body, L ∝ N² and DCR ∝ N², so **DCR ∝ L ∝ 1/f** for constant ripple. Core loss at constant ripple barely moves (∝ f^0.25). Switching loss is only 0.87 W at 100 W, so halving f saves at most about 0.45 W, and the bigger inductor in the same body more than gives that back. Same footprint, model results:

| Frequency, part (all 7.8 × 7.6 × 3.1) | 30 W | 100 W | 100 W at 12 V | 88 W charging | 117 W from 10 V |
|---|---|---|---|---|---|
| 500 kHz, APS0730M2R2F | −0.04 | −0.17 | −0.21 | −0.09 | −0.30 |
| 400 kHz, APS0730M3R3F (18 mΩ, I_sat 13 A) | −0.09 | −0.08 | **+0.06** | −0.11 | **+0.52** |
| 300 kHz, APS0730M4R7F (26.7 mΩ, I_sat 12.2 A) | −0.05 | **+0.41** | **+1.04** | +0.03 | **+2.81** (I_pk 16.7 A > I_sat) |

Negative means a saving. **The win has to come from a lower-loss inductor, with frequency trimmed second.**

## 3. Candidates (JLC API, 2026-10-21; DCR at 25 °C)

| Part | LCSC / stock / price | L, DCR typ/max | I_sat | Irms (ΔT) | Size, mm | Fit |
|---|---|---|---|---|---|---|
| APS0730M2R2F (today) | C49261221 / 1,552 / $0.56 | 2.2 µH, ~12.5 / 13.7 mΩ | 17 A (−40 %) | 13 A (40 K) | 7.8 × 7.6 × 3.1 | — |
| **Coilcraft XGL7030-222MEC** | **not at JLC** (C9900146794 is a dead placeholder). Coilcraft: €2.47 ×1, €2.17 ×100, €0.99 ×400, in stock | 2.2 µH, **7.3 / 8.8 mΩ** | 9.7 A (−20 %), 14.5 A (−30 %) | 12.0 A (20 K), 16.3 A (40 K) | ~7.5 × 7.5 × 3.1 | Fits today's courtyard; new land pattern |
| XGL7030-332MEC | same | 3.3 µH, 10.4 / 12.5 mΩ | 12.0 A (−30 %) | 10.2 / 13.8 A | same | Holds 2.2 µH at 13 A |
| XGL6030-222MEC | C3911448 / 182 / $9.16 | 2.2 µH, 10.3 mΩ max | 12.2 A | 12 A | 6.7 × 6.5 × 3.1 | Fits; poor value |
| Würth 74439344022 (XHMI 6030) | C2651174 / 1,049 / $3.25 | 2.2 µH, 10.5 mΩ max | 16 A | **8 A** | 6.65 × 6.45, 2.4–3 (check) | Irms too low |
| APS1030M2R2A / FXL1030-2R2 | C47327237 / 975 / $0.33; C52204855 / 507 / $0.38 | 2.2 µH, 9 mΩ | 14 A | 11 A | 11.5 × 10 × 3.0 | +56 mm² per port |
| IHLP5050CEER2R2M01 | C845090 / 1,000 / $1.55 | 2.2 µH, 7.2 mΩ | 29 A | 16 A | 13.2 × 12.9 × 3.0 | +112 mm² per port |
| *4 mm:* APS1040M2R2A | C47327242 / 10,850 / $0.24 | 2.2 µH, 6.9 mΩ | 18 A | 12 A | 11.5 × 10 × 4.0 | +0.8 mm and +56 mm² |
| *6 mm:* XGL6060-222MEC | C3911671 / 1,018 / $12.54 | 2.2 µH, 4.9 mΩ | 16 A | 20.7 A | 6.7 × 6.5 × 6.1 | +2.9 mm |
| *5 mm:* MPL-AL6050-2R2 | C6675303 / 25 / $1.67 | 2.2 µH, 8.3 mΩ | 15 A | 12 A | 6.6 × 6.4 × 5.0 | +1.8 mm, no gain |

Sources:
- Coilcraft XGL7030 product page and datasheet Doc 1736-1 (DCR, I_sat at 10/20/30 %, Irms, 80 V rating, 1.03–1.10 g).
- XAL7030 drawing: 7.5 ± 0.5 mm square, 3.1 mm max (xal7030.pdf p.2). The XGL7030 uses the same 16 mm tape and 12 mm pitch. **Confirm the XGL7030 drawing and land pattern before committing.**
- Other parts: the JLC/LCSC parametrics.

Coilcraft publishes core loss only through its online analyzer, which wouldn't load here. Its XGL-vs-XAL page claims "lowest AC loss" (XGL4020 runs 30 K cooler than XAL4020 at 1 MHz). The model therefore gives XGL **half** the APS0730's core loss. If it is equal instead, subtract about 0.06 W at 100 W from the XGL savings.

## 4. Recommendation

**R1, do it: L401/L501 → XGL7030-222MEC, keep 598 kHz.** Saving per active port, from the model:

| | 30 W | 100 W | 100 W at 12 V | 88 W charging | 117 W from 10 V |
|---|---|---|---|---|---|
| R1: XGL7030-222, 600 kHz | **−0.11** | **−0.52** | **−0.92** | **−0.23** | **−1.78** |
| R2: R1 + R412 → 49.9 k (500 kHz) | −0.17 | −0.70 | −1.14 | −0.33 | −2.11 |
| R1 at 450 kHz (57.6 k) | −0.19 | −0.78 | −1.24 | −0.37 | −2.25 |
| R1 at 400 kHz (66.5 k) | −0.21 | −0.85 | −1.32 | −0.41 | −2.37 |
| XGL7030-332 at 500 kHz | −0.16 | −0.49 | −0.76 | −0.26 | −1.27 |

- **Inductor heat:** at 100 W it goes from 1.03 to 0.59 W. At the 117 W corner it goes from 2.8 to 1.6 W, roughly +31 K instead of +48 K by the makers' Irms figures. That relieves the hottest part next to Q401.
- **Peak current is unchanged** (15.7 A at the corner). XGL's soft roll-off gives about 1.6 µH at 13 A, the same as today.
- **Cost:** about +$1.6 per part at prototype quantity (+$3.2 per board), or +$0.5 at 400+. It must be **consigned or bought through JLC global sourcing**, the same arrangement as the SiZ240DT.
- **Area:** 0, or slightly less. **Height:** same, 3.1 mm. **Weight:** at most +0.3 g each.
- **Fallback:** if a stocked part is wanted, use APS1030M2R2A. It gives about 0.38 W at 100 W but costs +56 mm² per port.

**R2, try on P0, don't commit blind: 500 kHz.** It is a 0201 swap and adds another −0.18 W at 100 W and −0.06 W at 30 W. The costs:
- Ripple becomes 6.2 A at the corner, 48 % of I_L_max, above TI's 40 % guideline.
- The peak becomes 16.2 A.
- USB-side bus ripple goes from 160 to 189 mV, and PACK_P from 78 to 102 mV.
- Cap stress stays at 43 % of rating.
- Not recommended: 400 kHz with 2.2 µH (60 % ripple, peak 17 A, USB ripple 231 mV), and anything at 300 kHz or lower.
- Benefit: it moves the setting off the 600 kHz ROC ceiling.

**Taller parts don't pay.**
- **4 mm** (APS1040M2R2A) saves the same as R1 (−0.55 W) but needs a 115 mm² footprint.
- **5–6 mm** (XGL6060-222, or -332 at 400 kHz) adds only −0.2 to −0.5 W beyond R1 at 100 W.
- The cover, gap pad and standoffs move out 1:1. The pack's board-normal dimension goes from 59.6 mm to about 60.4 mm (4 mm part), 61.4 mm (5 mm) or 62.5 mm (6 mm). That is +1.3–4.9 % in volume, plus taller H101–H104.
- A cover window over the inductor could hide 0.8 mm, but it gives up heat spreading and the seal.

**Risks:**
- **Availability:** single-source Coilcraft, not at JLC.
- **Land pattern:** an unverified footprint swap.
- **Core-loss uncertainty:** ±0.06 W.
- **The 2.2 µH ROC minimum:** violated at full load by both today's part and R1, about 1.6 µH. The XGL7030-332 is the conservative choice that honours it (2.2 µH at 13 A, 34 % ripple at 500 kHz), at about 0.2 W less saving.
- **At 500 kHz:** more ripple, peak current and conducted-EMI ripple at the fundamental. The auto-tuned loop recalibrates by itself.
- **SOA, short-circuit and inrush:** unchanged.
- **Firmware/config:** none for R1. For R2, check that no firmware or doc assumes 600 kHz (`cap_sims.py` FSW).

## 5. Interactions

- **Area A (FETs):**
    - Every f-proportional term scales with frequency: edge, Coss, dead time, gate and Qrr.
    - A's R1 (9 V DRV_SUP) raises Qg per cycle. A's R2 (BSZ018 in leg B) has Qrr 55 nC and Coss 690 pF, which costs about 0.3 W at 600 kHz in the light modes.
    - With A's R2 fitted, **500 kHz becomes more valuable**: re-run `freq_ind_B.py` with A's FET constants.
    - Lower inductor heat also leaves thermal budget for Q401.
- **Bulk caps:** no re-sizing at ≥ 450 kHz. Below 400 kHz the CA55 polymer reaches 52–62 % of its rating and USB ripple reaches 300–350 mV (`fsweep.py`).
- **Thermal models:** about 0.4 W less in the charger zone at 100 W.
- **Docs:** schematic note 15 should read L/DCR. If R2 is adopted, the 598 kHz references in circuit-description and `cap_sims.py` change too.

## 6. What to measure on P0

1. **Inductor temperature:** thermocouple on the inductor top at 100 W reverse from 14.4 V and 12 V, and at the 117 W corner. Do it with the APS0730 on one port and the XGL7030 on the other, so the comparison runs on the same board.
2. **Inductor current:** current probe in series with L (or a Rogowski probe), at 117 W from about 10–11 V. Record I_pk and ΔI against the 15.7 A / 5.2 A prediction, and look for a cusp in the ramps, which would mean the core is saturating.
3. **Efficiency A/B:** input and output power with 4-wire meters at 30 W, 100 W and 88 W charging. Do it at 598 kHz, then with R412 = 49.9 k. Check FSW on SW1/SW2 each time.
4. **Ripple and stability:** USB-side and PACK_P ripple at 500 kHz against 189 / 102 mV, and a 1 ↔ 5 A load step at 20 V with each inductor and frequency.
5. **Core loss:** at 30 W, inductor temperature rise against DCR·I²; the excess is the core loss.

## 7. Cross-examination (round 2)

These checks used the datasheets, the Coilcraft drawings, and re-runs of my model copy (`scratchpad\model\xexam.py`) and the cap sims (`fsweep.py`, with the pack resistance lowered).

### My own saturation concern, and footprint confirmed

**Coilcraft's L-vs-I curves** (product page, xgl7030-222c.gif and -332c.gif):
- **XGL7030-222:** 2.0 µH at 5 A, 1.72 µH at 10 A, **≈1.58 µH at 13 A**, 1.48 µH at 15.7 A. My model matched this to within 0.03 µH.
- **XGL7030-332:** **≈2.2 µH at 13 A**. The curve ends at 13.3 A.

The BQ25756 ROC minimum is 2.2 µH (p.7). TI's own designs all use 10 µH, including the EVM's IHLP6767GZ at 250 kHz (sluuct7 BOM). The -222 is therefore always below the minimum under load. Today's APS0730 has the same problem, at 1.6 µH. It is a pre-existing excursion, not one the swap creates.

**The -332 is the cleaner call. Revised recommendation: XGL7030-332MEC with R412 = 49.9 kΩ (500 kHz).** It meets every TI guideline:
- L ≥ 2.2 µH to 13 A;
- ripple at the 117 W corner 4.5 A = 34 % of I_L_max, and still ≤ 40 % at the −15 % oscillator tolerance (425 kHz);
- peak 15.4 A;
- L/DCR 0.32 µH/mΩ.

Its savings are **0.16 / 0.49 / 0.76 / 0.26 W** (30 / 100 / 100 at 12 V / 88 W charging), and 1.27 W at the 117 W corner.

The -222 at 600 kHz (0.11 / 0.52 / 0.92 / 0.23 W) stays as the alternative if P0 shows the auto-tuned loop is happy at 1.6 µH. The loop is tuned at about 0 A, so a 27 % L drop at full load is the open question.

The -332 has one drawback. Its corner-case heat is 2.2 W, against 1.6 W for the -222, and its rms rating of 13.8 A at 40 K is close to the corner's 13.1 A. Measure it against the thermal throttle.

**Footprint is confirmed** (Coilcraft drawing xgl7030d.gif):
- Body 7.50 ± 0.5 mm square, 3.1 mm max.
- Terminals 1.60 mm wide, 3.12 mm apart; terminal span ≈ ±1.56 to ±3.16 mm.
- Recommended land: 1.78 × 6.50 mm pads, 4.72 mm gap.

Today's APS0730 pads (2.3 × 7.2 mm at ±2.55 mm, so they span ±1.40 to ±3.70 mm) **fully cover the XGL terminals**. The XGL7030 is a drop-in on the existing footprint, and the body envelope (8.0 mm max) is the same as the APS0730's (8.05 mm). The Coilcraft land is optional and would be 0.9 mm wider overall.

### Q1: the 9 V gate drive in A and E

**Effect on frequency-dependent loss** (model with T_EDGE 10 → 7 ns, FET 9.5 mΩ, gate Qg ≈ 27 nC drawn from V_pack):
- Overlap loss falls.
- Gate loss rises (V_pack × Qg × f: about 0.23 W against 0.16 W at 600 kHz).
- Dead-time and Coss terms are unchanged, because TI fixes the dead time at 45 ns (REG0x3C).
- The f-proportional total stays about the same: ≈1.0 W at 100 W either way.

My savings move by ≤ 0.05 W. The -332 at 500 kHz becomes 0.15 / 0.46 / 0.72 / 0.26 W, and the 500 kHz step is worth the same with or without A/E.

**Ringing.** Overshoot per edge depends on dv/dt and loop inductance, not on f. Ringing and snubber loss (C·V²·f, if R450/C454 get fitted) fall about 17 % at 500 kHz. Faster 9 V edges argue for the lower frequency, not against it.

**Watch for double counting:** A's R1 and E's item 3 are the same change (DRV_SUP at 9 V). Count about 0.43–0.45 W at 100 W once.

### Q2: D's P60B, lower source impedance

**Inductor and ceiling: no change.**
- Peak inductor current is set by power ÷ terminal voltage. The 117 W from 10 V corner is still about 13 A I_L and 15.4 A peak.
- A lower-resistance pack sags less, so that corner is reached later in the discharge, and less often.
- My savings with 13 mΩ cells: 0.16 / 0.45 / 0.67 / 0.27 W for the -332 at 500 kHz. They are slightly lower only because the battery current is lower.

**Bus damping.** Re-running `pack_bus_sims` with the pack at 30–45 mΩ instead of 50–85 mΩ lowers the PACK_P damping margin from 19.9 to 18.5 dB. That is still adequate. Ripple is unchanged.

**The short-circuit estimate is the real problem** (D and C). Both computed the bolted-short current from **DC (10 s) resistance**. The SCD delay is 100–400 µs, and on that timescale the cells look like their **AC impedance**. The P60B datasheet (v0.1, which I checked) gives **6.5 mΩ AC** at 30 % SOC and 12.8 mΩ DC.

Recomputed bolted short at 16.8 V:
- **P60B:** 4 × 6.5 + nickel 4–8.5 + FETs 4.2–8.8 + fuse 2.5 + shunt 1 + copper 2 + the short ~5 → about 45–55 mΩ. That gives **≈300–370 A**, not 185 A.
- **58E:** AC ≤ 18 mΩ per cell → ≈190–220 A.

At 350 A, a hot XRS120N04D (2.6 mΩ) dissipates ≈320 W at about 0.9 V for the whole SCD delay. That exceeds C's own reading of its 100 µs SOA (≈210 A at 1 V).

**P60B plus XRS needs the SCD threshold and delay at their minimums and a real short test.** Otherwise it needs the BSZ018N04LS6 (IDpulse 633 A, characterized SOA). The cell's own rating (100 A max discharge) is also exceeded, but only for microseconds.

### Most serious flaw in each other area

- **A:**
    - The leg-B split (BSZ018: Coss 690 pF, Qrr ~55 nC) is costed only at the 30 W 9 V point. **It also hard-switches in the buck-boost band.** E shows a 15 V contract on a ~14.4 V pack puts both legs in buck-boost, which A's model doesn't represent. The +0.18 W penalty probably applies to 45 W charging and 15 V sourcing as well.
    - The TPS7A4101's 50 mA rating exactly meets TI's "≥ 50 mA" with no margin. The TPS7A16 fallback is the right part.
    - **Agree otherwise.** A's mode table matches TI table 6-1, and its 13.4 nC gate correction matches mine.
- **C:**
    - **Verified:** F101 is gone; the gauge sheet has only F102 (WSFB1514). So the fuse correction to about 2.5 mΩ is right, and it lowers everyone's baseline. I also agree with keeping the 1 mΩ shunt.
    - **Not verified:** the XRS120N04D's SOA is a generic drawing from an obscure vendor. C's short-circuit current uses DC resistance (see Q2). Conditionally agree: adopt it with the 58E. With the P60B, prefer the BSZ018N04LS6.
- **D:**
    - **Verified:** the P60B figures (6.0/5.85 Ah, 6.0 A standard / 30 A maximum charge, 100 A maximum discharge, 6.5/12.8 mΩ, 75 g maximum). But the sheet is **version 0.1, preliminary**, and it lists a 1.8 V discharge cut-off, which needs clarifying with Molicel.
    - The short-circuit current is understated about 2× (Q2).
    - The near-empty ×1.5 factor and the 8.5 mΩ nickel are estimates, not measurements. P0 should measure them.
    - Agree with the direction, and that it is the largest single lever. Not to be committed before a short test.
- **E:**
    - The TPS25751S external-path idea is unverified for source mode with the BQ25756. E says so, and I agree it is blocked until TI confirms.
    - One minor datasheet ambiguity: §6.3.3.2 enables REGN from BAT in reverse mode, but its loss equation uses VAC. Gate loss while sourcing is therefore 14.4–20 V × Qg × f (0.12–0.16 W). This doesn't change any conclusion.
    - The PFM, sink-policy and sense-resistor arguments check out against the datasheet.

**Revised B saving: XGL7030-332 + 500 kHz, 0.16 / 0.49 / 0.76 / 0.26 W** (1.27 W at the 117 W corner). This is additive with A or E's 9 V drive (0.15 / 0.46 / 0.72 / 0.26 W combined). Cost: about +$1.6 per inductor, hand-supplied, plus one 0201 resistor change. No change to footprint, area or height.
