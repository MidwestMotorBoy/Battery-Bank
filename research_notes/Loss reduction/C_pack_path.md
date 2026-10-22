# C — Pack path: protection FETs, fuse, gauge shunt, copper

Sources: `git show d994c3a:hardware/Production/gauge.kicad_sch` (part fields), `docs/devboard/circuit-description.md`, `docs/devboard/bringup-config-checklist.md`, `docs/devboard/review2/A-findings.md`, the datasheets in `datasheets/`, plus the XRS120N04D, BSZ018N04LS6 and TPN2R304PL datasheets from LCSC. JLC stock and prices come from JLC's parts API, read 2026-10-21. The model runs are in a copy at `scratchpad/model/run_c.py`; the repo model was not edited.

## 1. What is in the path today, and what it really costs

| Part | What it is | Resistance used | Source |
|---|---|---|---|
| Q101, Q102 | AGM404AP1 (LCSC C41349455), back-to-back high-side N-FETs | 4.4 mΩ typ / 6.0 max at VGS 10 V, 25 °C. The model uses 5.7 warm (×1.3) | agm404ap1.pdf Table 3 |
| Gate drive | BQ40Z50 CHG/DSG charge pump, 5.1 kΩ series, 10 MΩ G–S | V(FETON) = 10.5 / 11.5 / 12 V above BAT for VBAT ≥ 4.92 V. **So the 10 V RDS(on) row is the right one at every pack voltage (10–16.8 V)** | bq40z50-r2.pdf §7.18 |
| **"F101"** | **No longer exists.** F101 (Prosemi 1206FA-15A) was deleted in rev A6. The only fuse is **F102, TLC WSFB1514** (C42463217): a 3-terminal self-control fuse, 15 A rated, 50 A interrupt, 36 V | **Rfuse 1.0–3.0 mΩ** | tlc-wsfb1514.pdf p.1 |
| RS101 | 1 mΩ 1 % 1 W 1206, Ralec LR1206-21R001F4 (C154629), 75 ppm | 1.0 mΩ | part fields |
| Copper, nickel | board pours; nickel tails | 2 + 5 mΩ, both estimates | model |

**Correction:** the model's `fuse = 0.005` is the old F101 at its hottest (review 2, A-6: 1206FA-15A is 3.9 mΩ cold). F102 is 1–3 mΩ per its datasheet. I use **2.5 mΩ warm**. That alone takes the pack-path line from 1.46 to **1.30 W at 100 W**, and from 2.31 to 2.06 W at 12 V. The FET figure (2 × 5.7 mΩ) is right for typical parts. A max-RDS part running hot (6.0 × 1.3) would add another ~0.26 W at 100 W.

## 2. The owner's candidate: LCSC C50314144

**It is the XNRUSEMI XRS120N04D.** It is an N-channel 40 V split-gate trench MOSFET in a PDFN3333-8L package, pinned S-S-S-G / D-D-D-D, the same pinout as the AGM404AP1.

| Spec | XRS120N04D | AGM404AP1 (today) | Source (XRS / AGM) |
|---|---|---|---|
| VDS | 40 V | 40 V | p.1 / Table 1 |
| **RDS(on) at VGS 10 V** | **2.1 typ / 2.8 max mΩ** (ID 20 A) | 4.4 / 6.0 mΩ | p.2 / Table 3 |
| RDS(on) at 4.5 V | 2.8 / 3.8 mΩ | 6.6 / 8.5 mΩ | p.2 |
| RDS(on) vs temperature | ×1.22 at 75 °C, ×1.35 at 100 °C | ~×1.3–1.45 | Fig 6 / review 2 |
| Qg (0–10 V) / Qgd | 42.6 nC / 7.2 nC | 13.5 nC / 2.6 nC | p.2 / Table 3 |
| Ciss | 2625 pF | 842 pF | p.2 |
| VGS(th) | 1.2–2.2 V | 1.2–2.2 V | |
| IDM / EAS | 480 A / 180 mJ (IAS 30 A, 0.5 mH) | 184 A / 81 mJ | p.1 / Table 1 |
| RθJC / RθJA | 1.9 / 60 °C/W | 4.5 / 60 °C/W | p.1 |
| SOA, single pulse at Tc 25 °C (read from Fig 10) | 10 µs: ≈ 400 A at 16.8 V. 100 µs: ≈ 210 A at 1 V, 56 A at 10 V. 1 ms: ≈ 15 A at 10 V | 100 µs ≈ 550 W, 1 ms ≈ 160 W (review 2 A-2) | Fig 10 |
| IDSS at 100 °C | 100 µA max | (25 °C only: 1 µA) | p.2 |
| Package height | 0.80 mm max | 0.90 mm max | p.6 / p.7 |
| Land | Exposed pad 2.49 × 1.80 mm, 0.65 mm pitch, recommended pattern on p.6 | Same class | |
| JLC | **Extended, 5,010 in stock, $0.27 (1+) / $0.214 (50+)** | Extended, **477 in stock**, $0.146 | JLC API |

**Footprint fit.** The existing `MonolithDev:AGM_PDFN-8_3.3x3.3mm_P0.65mm` footprint (drain pad 2.45 × 2.565 mm including the drain fingers, 0.4 mm leads at 0.65 mm pitch, pin 4 = G) suits the XRS outline. The exposed pad D2 (2.39–2.59 mm) is within 0.07 mm of our pad width, and the pinout matches. **Drop-in: change the LCSC, MPN and Value fields only.** Area, height and weight do not change (the XRS is 0.1 mm thinner).

**Gate charge against the charge pump.** TI specifies the CHG/DSG rise and fall times into a **4.7 nF** load through 5.1 kΩ: rise 200 typ / 500 max µs to 35 %, fall 40 typ / 300 max µs (bq40z50-r2 §7.18). The XRS behaves like about 42.6 nC / 10 V ≈ 4.3 nF, so it is still inside TI's own test load. The AGM is about 1.4 nF.
- **Turn-on** takes ~3× longer, still well under a millisecond. That is a benefit: it slows the inrush into the ~100 µF PACK_P bank, which review 2 put at ~185 A peak with the fast AGM.
- **Turn-off at a short:** the Miller plateau (~3.5 V) through ~6 kΩ is ≈ 7.2 nC / 0.57 mA ≈ **13 µs**, against ≈ 5 µs for the AGM. Average dissipation then is ≈ ½ × 16.8 V × 200 A ≈ 1.7 kW for 13 µs ≈ 22 mJ. That sits under the XRS 10 µs SOA line (~6.7 kW at 16.8 V). Any wiring-inductance avalanche (~4 mJ at 200 nH, 200 A) is far below its 180 mJ EAS.

**Short-circuit SOA during the SCD delay** is where the lower RDS really helps. The prospective short current rises a little, from ≈ 185 A to ≈ 195–200 A, because the loop loses ~6 mΩ out of ~90 mΩ. While the FETs are fully on during the SCD delay, each one dissipates 200² × 2.6 mΩ ≈ **104 W at ~0.5 V**. The AGM, at 185 A and 8.7 mΩ hot, dissipates ≈ 300 W at 1.6 V, right at its 100 µs limit. The XRS 100 µs line allows ~200 W at that point. Its 1 ms line at 0.5–1 V allows only ~80–120 A, though. **The checklist rule stands: set the SCD1 delay to the shortest setting that doesn't nuisance-trip, ≤ ~120 µs.**

**SCD/OCD timing and gauge accuracy are unaffected.** Every current protection (OCD1/2, OLD, SCD, SCC) and the coulomb counter sense across RS101, not the FETs (§7.31, §7.14). The thresholds, delays and calibration stay as they are. One side effect: the gauge's internal sensor stands in for "FET temperature". With half the FET heat, OTD now has more margin; it doesn't need retuning.

**Caveats.**
- XNRUSEMI is an obscure brand. The datasheet's text layer is broken, the BVDSS temperature-coefficient cells are blank, and the SOA is a generic drawing.
- It has one source, though its JLC stock is 10× the AGM's.
- IDSS reaches 100 µA at 100 °C. That only matters with the FETs off and hot.

**Verdict on C50314144: adopt it.** It is a genuine pin- and land-compatible part with half the RDS(on) at the BQ40Z50's real gate drive, more short-circuit margin during the SCD delay, and better avalanche, thermal and stock figures. The cost is about +$0.14 per board.

## 3. Other options

| Option | MPN / LCSC | Key data (10 V gate) | JLC stock / price | Fit | Comment |
|---|---|---|---|---|---|
| **A: XRS120N04D** | C50314144 | 2.1 / 2.8 mΩ, Qg 42.6 nC | 5,010 / $0.21 | drop-in | **recommended** |
| B: Infineon BSZ018N04LS6 | C534643 | 1.6 / 1.8 mΩ, Qg 31 nC, Qgd 3.8 nC, EAS 189 mJ, IDpulse 633 A, Tj 175 °C (datasheet Tables 2, 4, 6) | 202 / $1.10 | drop-in (PG-TSDSON-8 FL, same pinout) | best part, fully characterized; +$1.9/board; low stock |
| C: Toshiba TPN2R304PL | C5802634 | 1.8 / 2.3 mΩ, Qg 41 nC, EAS 39 mJ (datasheet §5, §6) | 1,917 / $0.51 | TSON Advance 3.1 × 3.1 body: check the land | weaker avalanche rating |
| D: NCE NCEP4065QU / HUASHUO HSBB4072 | C502974 / C5341685 | 2.2 mΩ (listing only) | 959 / $0.49; 2,917 / $0.27 | 3.3 × 3.3, not checked | second sources if A runs out |
| 5 × 6 mm parts (BSC019N04LS C534301, JSMSEMI SNCEP40T13GU C49206924) | | ~1.5 mΩ | 3,507 / $0.39; 4,823 / $0.26 | **+~38 mm² for two** | only ~0.05 W better than A: not worth the area |
| Common-drain dual | onsemi EFC4C002NLTDG C895362 | 2.6 mΩ per switch, **30 V**, WLCSP | 9 / $3.54 | new footprint | 30 V is too thin for 16.8 V plus transients; WLCSP; no 40 V low-RDS dual at JLC. A dual saves area, not milliohms |
| Lower-R fuse | WSFB 20 A class / Dexerials SFJ | ≈ −1 mΩ | none at JLC (hand-supplied) | different footprints | saves ≤ 0.06 W at 100 W and weakens the backstop (15 A element, 200 % < 1 min). **Keep F102** |
| Shunt 0.5 mΩ | | −0.5 mΩ | | 1206 fits | saves 0.035 W at 100 W. It would double the CC offset (±10 µV → ±20 mA, §7.14) and the OLD/SCD steps (OLD floor 16.6 A, 5.6 A steps) and the ±2.5 mV comparator offset → ±5 A. **Keep 1 mΩ**: it's the right value for an 11 A OCD1 / 16–20 A OLD |

## 4. Recommendation and savings (model copy)

**Change:** Q101 and Q102 → **XRS120N04D (C50314144)**, with BSZ018N04LS6 as the premium/fallback part on the same footprint. Keep F102, RS101 and the copper. Also fix the model's fuse value to 2.5 mΩ.

Pack-path loss and the saving in total pack loss (the model iterates, so I² feedback is included):

| | 30 W | 100 W | 100 W, 12 V | 88 W chg |
|---|---|---|---|---|
| Model as is (fuse 5, FETs 2 × 5.7) | 0.12 | 1.46 | 2.31 | 0.78 |
| Corrected baseline (F102 2.5 mΩ) | 0.11 | 1.30 | 2.06 | 0.70 |
| **+ XRS120N04D (2 × 2.1 × 1.22)** | **0.08** | **0.92** | **1.45** | **0.50** |
| **Saved by the FET swap** | **0.03** | **0.45** | **0.77** | **0.18** |
| XRS at max RDS (2.8 mΩ): saved | 0.02 | 0.33 | 0.57 | 0.13 |
| BSZ018N04LS6 instead: saved | 0.04 | 0.53 | 0.91 | 0.21 |
| + shunt 0.5 mΩ (not recommended): extra | 0.003 | 0.035 | 0.06 | 0.014 |

Against the brief's table, the 100 W total falls from 11.3 to **10.7 W** (12 V pack: 17.0 → 15.9 W). Of that, 0.18 / 0.31 W is the fuse correction and 0.45 / 0.77 W the FETs. Per FET at 100 W from a 12 V pack, heat goes from ~0.55 W to ~0.24 W.

**Cost +$0.14/board, area 0, height −0.1 mm, weight ≈ 0.**

**Risks:**
1. The vendor's datasheet quality. Verify RDS(on) on the first boards (§6).
2. Turn-off is ~3× slower. Measure it.
3. The SCD delay must stay short.
4. Single source. BSZ018N04LS6 is the qualified fallback.

**Firmware/config:** none required. Recheck OTD/OTC once, since the FETs now run cooler.

## 5. Interactions

- **Every area:** the fuse correction lowers the shared baseline by 0.15–0.3 W, so use the corrected numbers.
- **Thermal/mechanical:** heat at the pack-input corner roughly halves.
- **Safety (shared with the protection reviews):** the short-circuit current rises ~5 %, which makes the FETs, not F102 (50 A interrupt), the only thing that can clear a hard short. That was already true.
- **Inrush:** slower turn-on lowers the PACK_P inrush. That eases review 2's C109 question; leave C109 unfitted.
- **Charger area:** none directly. A lower battery current from other savings reduces this path by I².

## 6. What to measure on P0 (no dev board, per 2026-10-18)

1. **Kelvin VDS across Q101 + Q102 and across F102** at 5 A and 10 A, with a load on PACK_P and current from the gauge. Expect ≈ 4.2–5.6 mΩ for the pair and 1–3 mΩ for the fuse. Repeat warm, after 10 min at 100 W.
2. **CHG/DSG gate voltage to source** with both FETs on, at 10 V and 16.8 V pack. Expect 10.5–12 V.
3. **Turn-on and turn-off waveforms** (gate, VDS, current probe):
   - FET_EN into the PACK_P bank: inrush peak.
   - A controlled SCD test through a low-ohm load with the SCD threshold set low: confirm the trip delay setting plus tDETECT ≤ ~160 µs, a Miller plateau of ~10–20 µs, and no ringing past 40 V.
4. **Thermal camera at 100 W from a ~12 V pack** on Q101/Q102, F102 and RS101. Compare against the gauge's internal FET temperature.
5. **Gauge calibration** (CC offset and gain) is unchanged by this, but confirm the current reads correctly at 1 A and 10 A.

## 7. Cross-examination (round 2)

### 7.1 D's Molicel P60B and the short circuit

**D's 125 → 185 A understates the short-circuit current.** A hard short is cleared by the BQ40Z50's SCD, typically in 0.1–1 ms. On that time scale a cell looks closer to its ohmic (≈ 1 kHz AC) resistance than to its 10 s DC resistance, so I bound the current with both. Path today: nickel 8.5 mΩ (D's corrected figure), F102 2 mΩ, RS101 1 mΩ, copper 2 mΩ, plus the FETs.

| Prospective short at 16.8 V | DC cell R | Ohmic (AC) cell R |
|---|---|---|
| 58E + AGM404AP1 (2 × 4.4 mΩ) | 4 × 22 → **≈ 150 A** | 4 × 15 → **≈ 200 A** |
| P60B + XRS120N04D (2 × 2.1 mΩ) | 4 × 12.8 → **≈ 245 A** | 4 × 6.5 → **≈ 385 A** |
| P60B + AGM404AP1 | ≈ 230 A | ≈ 350 A |

A short at a charger FET goes through that port's 5 mΩ RBAT and lands about 10 % lower.

**FET heating during the SCD delay, per FET.** Each FET dissipates I² × R_hot:
- P60B with the XRS (2.4 mΩ hot): 145–355 W.
- P60B with the AGM (5.7 mΩ hot): **300–700 W**. That exceeds the AGM's ≈ 550 W / 100 µs rating (review 2, A-2).
- **So the P60B makes the FET change mandatory, not optional.**

**Is the XRS itself good enough? Its datasheet doesn't agree with itself.**
- Its transient-thermal curve (Fig 11: ≈ 0.05 × 1.9 = 0.1 K/W at 100 µs) predicts only ~35 K at 355 W.
- Its drawn SOA (Fig 10, 100 µs line ≈ 155 A at 1.7 V ≈ 260 W) says 355 W is over the limit.
- Infineon's BSZ018N04LS6 is a similar 3.3 × 3.3 die with a characterized curve (Diagram 4). It gives Zth ≈ 0.2 K/W at 100 µs and ≈ 0.4 K/W at 250 µs: ΔTj ≈ 70 K and ≈ 140 K at 345 W.
- Neither part survives the ohmic-case current for a full millisecond. Both survive ≲ 150 µs.

**F102 (WSFB1514).** The datasheet gives no I²t number, but its cut-time curve (p.3, "Cut Time by Current Operation") reads ≈ 1 s at 50 A, 60 ms at 100 A and 12 ms at 150 A, so ≈ 270–600 A²s to melt.
- A 385 A short cleared in 200 µs passes about 30 A²s, so the fuse doesn't blow or age during a normal SCD trip.
- But its **interrupt rating is 50 A at 36 V**. At 245–385 A it can't safely open a short if a FET fails shorted. That was already true at 150–200 A with the 58E; the P60B makes it worse.
- Note: "F101" in D's text no longer exists. It was replaced by F102 in rev A6.

**BQ40Z50 SCD settings** (§7.31–7.32), with the 1 mΩ shunt:
- **Threshold:** 22–100 A (RSNS = 0) or 44–200 A (RSNS = 1).
- **Delay:** 0–915 µs in 61 µs steps, plus tDETECT ≤ 160 µs.
- **With the P60B, set:**
  - SCD1 with RSNS = 1, ≈ 133–155 A, delay 61 µs.
  - SCD2 lower, ≈ 89–100 A, at ≤ 244 µs.
- That keeps the full-current window ≲ 220 µs.
- The P0 inrush test must confirm that FET_EN turn-on into the PACK_P bank doesn't trip it. The XRS's slower gate helps here.
- No shunt change is needed. A 385 A × 200 µs pulse puts about 30 mJ into RS101, a few kelvin.

**Verdict:**
- **With the 58E:** my recommendation holds unchanged. Use the XRS120N04D.
- **If the P60B is adopted:**
  - Use **BSZ018N04LS6 for Q101/Q102** (633 A pulse, Tj 175 °C, characterized SOA and Zth). Keep the XRS as the stocked alternative only after a P0 short test passes.
  - Make the short SCD settings above mandatory.
  - Flag F102's 50 A interrupt rating as the remaining single-fault gap.

### 7.2 A's use of BSZ018N04LS6 (leg B high side)

**There's no electrical conflict, but there is a stock conflict.**
- JLC has **202** pieces. A needs 2 per board, and mine (if the P60B goes ahead) needs 2 more, so 4 per board: ≈ 50 boards before the stock runs out.

**A has also left one penalty unmodelled.**
- In **forward boost** (charging from a 5 V or 9 V adapter), the leg B high side is the synchronous FET. Its 55 nC Qrr is then hit every cycle: ≈ 55 nC × 16.8 V × 600 kHz ≈ **0.5 W**, plus the Coss of a 690 pF part.
- A's scenarios include 9 V *reverse* buck but no 5/9 V *charging* case.

**Suggestion:**
- A uses **XRS120N04D** (5,010 stocked, $0.21; Qrr 18.4 nC, Coss 560 pF, 2.1 mΩ at 10 V / 2.8 mΩ at 4.5 V) or TPN2R304PL in leg B.
- The BSZ018 stock is kept for Q101/Q102 if the P60B is adopted.
- The 5/9 V charging case gets re-run.

### 7.3 Most serious flaw or unverified claim, per report

- **A:**
  - **Flaw:** the leg B Qrr penalty in forward boost above is missing.
  - **Duplication:** R1 (9 V DRV_SUP) is E's item 3; count it once.
  - **Smaller point:** A writes P_REGN with VAC (eq. 29), but §6.3.3.2 says REGN in reverse mode runs whenever BAT > 3.8 V, so the reverse-mode supply is probably the pack (E's reading). That changes the gate-power figures slightly.
  - **Otherwise:** agree. A 9 V DRV_SUP is within the 4.5–12 V external range (§6.3.3.2) and under DRV_OVP 12.8 V min.
- **B:**
  - **Flaw:** the XGL7030-222 is rated only **9.7 A at −20 %** and 14.5 A at −30 %. B's 117 W corner peaks at ≈ 15.7 A, beyond the −30 % point.
  - **Unverified:** "1.6 µH at 13 A, same as today" isn't taken from a curve. Ripple, and therefore peak current, grow as L sags. The halved core loss is also assumed.
  - **Agreed:** I couldn't find any peak or cycle-by-cycle inductor current limit in bq25756.pdf either; only the averaged BAT/AC limits.
  - **Overall:** agree with R1. Prefer B's own conservative XGL7030-332, or require a scope check of I_L at the corner on P0.
- **D:**
  - **Flaw:** the short-circuit current is understated (§7.1), and the protection follow-up is assigned to "area B"; the pack path is area C.
  - **Agreed:** the nickel correction (8.5 mΩ) and the near-empty cell resistance correction. Both enlarge the pack-path baseline.
  - **Overall:** the P60B case is real, but conditional on §7.1.
- **E:**
  - **Most serious:** the TPS25751S + CSD87501L external path. CSD87501L is **30 V** under a 28 V TVS clamp; 2 V of margin doesn't cover hot-plug ringing. And TI hasn't confirmed BQ integration in source mode. I'd reject it unless TI confirms *and* a 40 V dual is used.
  - **Unmeasured:** the PFM no-load saving (≈ 0.45 W).
  - **Agreed:** keeping RAC/RBAT at 5 mΩ is well argued.

### 7.4 Revised recommendation

| Case | Q101/Q102 | Saving (30 / 100 / 100 at 12 V / 88 chg, W) |
|---|---|---|
| Cells stay 58E | **XRS120N04D** (C50314144), as in §4 | **0.03 / 0.45 / 0.77 / 0.18** |
| P60B adopted | **BSZ018N04LS6** (C534643), plus the SCD settings above | 0.04 / 0.53 / 0.91 / 0.21 |

Further notes:
- **Cost:** about +$1.9 per board with the BSZ018.
- **Larger baseline:** with D's nickel (8.5 mΩ), the pack-path baseline is about 0.2 W larger at 100 W. The FET savings are the same.
- **Unchanged in both cases:** keep F102 and RS101 (1 mΩ). No firmware changes beyond the SCD configuration.
