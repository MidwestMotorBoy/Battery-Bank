# E: USB side, sense resistors, fixed losses and system policy

Area E of the loss-reduction study. Research only: nothing in the repo was changed. The model variants are in a copy of `heat_sources.py` plus `e_variants.py` in my scratch area. The copy adds three things the original lacks:

- explicit REGN gate-drive loss;
- the buck-boost band, where both legs switch;
- VBUS board copper.

Sources are the datasheets in `datasheets/`, `git show d994c3a:` design files, and LCSC (checked 2026-10-21).

## 1. Current parts and what they really lose

| Item | Part / setting | Check | Verdict |
|---|---|---|---|
| PPHV switch | TPS25751D internal, "16 mΩ" typ (tps25751.pdf p.2), 14–22 mΩ over −20…150 °C (fig. 6-5) | 18 mΩ warm × 5² = 0.45 W | Model right |
| USB-C contacts | ShouHan 16P IP68: **40 mΩ/pin max** (usb-c-16pcb1.6-ip68.pdf, note 3); 4 VBUS + 4 GND contacts in parallel → 20 mΩ loop max | Model 10 mΩ typ | Right, but 0.5 W at the 20 mΩ limit |
| VBUS copper | connector → TVS → PPHV → RAC, 70 µm F.Cu (~0.25 mΩ/sq) | not in model | **+2 mΩ loop, +0.05 W at 5 A** |
| RAC / RBAT | 5 mΩ each (R424 0805, R427 1206) | I² checks out | Right |
| Gate drive | REGN LDO fed from the converter's *input* rail (bq25756.pdf §6.3.3.2): VBAT in reverse, VAC in forward. P = V_in × Qg × f (eq. 29); SiZ240DT Qg 6.9 + 6.5 nC/leg at 4.5 V (siz240dt.pdf p.2) | 14.4 V × 13.4 nC × 600 kHz = **0.12 W** sourcing, **0.16 W** charging at 20 V, **×2 in buck-boost** | Model's flat 0.10 W is a little low |
| BQ25756 IQ | 0.75 mA IQ_VAC / IQ_REV (p.8) | 11–15 mW | OK |
| House (3V3: CC2340, 2 × TPS25751 at 3–6 mA active, pull-ups; TPS62177 ~88 %) | power-budget.md | 40–75 mW | Model's 0.05 W is fine |

**Corrected baseline (W):** 2.04 at 30 W, 11.43 at 100 W, 17.11 at 100 W with a 12 V pack, 6.71 at 88 W charging. The brief had 2.0 / 11.3 / 17.0 / 6.6.

Two corrections to the scenarios:

1. **"30 W at 9 V 3.3 A" is not a legal fixed PDO.** 9 V tops out at 3 A, which is 27 W. A 30 W phone takes 9 V 3 A, 15 V 2 A or PPS.
2. **15 V against a ~14.4 V pack lands in the buck-boost band** (both legs switching), which the original model doesn't represent.

**A loss the model doesn't have: the 5 V path.** 5 V contracts don't go through the BQ25756. They go TPS62933 (1.2 MHz, 76/32 mΩ FETs, tps62933.pdf p.6) → PP5V switch (36 mΩ typ, 53 mΩ at 125 °C; tps25751.pdf p.11). At 5 V 3 A that is roughly:

- buck: 0.5 W conduction + 0.25 W switching + inductor;
- PP5V switch: 0.33–0.48 W.

That is **≈1.3–1.6 W for 15 W out (~90 %)**, a worse ratio than 30 W through the BQ25756.

## 2. Candidates

| Change | Part | LCSC / stock / price | Key specs (cited) | Fit / height |
|---|---|---|---|---|
| External PPHV path | **TPS25751SRSMR** (PP_EXT gate drivers instead of internal PPHV) | C22460852, 286 pcs, $2.31 | Same PD core; GATE_VBUS / GATE_VSYS ≈ 8.8 V gate drive (fig. 6-7/6-8); comparison table: "bi-directional external path" (p.3) | QFN-32 4 × 4 (D is 4 × 6): −8 mm² |
| …its FETs | **TI CSD87501L** dual common-drain (TI's own TPS25751S reference) | C701751, 102 pcs, $1.02 | 30 V; RS1S2(on) 6.6 typ / 7.8 max at 10 V, 9.3 at 4.5 V; Qg 15 nC at 4.5 V ([TI SLPS523B](https://www.ti.com/lit/gpn/CSD87501L)) | LGA 3.37 × 1.47, 0.2 mm tall: +5 mm² plus routing |
| …40 V alternative | 2 × AGM404AP1 (already on the BOM) back-to-back | as Q101 | 4.4 mΩ typ at 10 V (agm404ap1.pdf) | 2 × 5 × 6 mm: +60 mm², hard to fit |
| Lower RAC | 2 mΩ 0805 | (basic Yageo/Uniroyal 2 mΩ exist) | bq25756.pdf: RAC "typically 2 mΩ, can be changed to 5 mΩ; **in USB-PD applications a 5 mΩ is recommended**" (§7.2.1.2.7) | same footprint |
| Lower RBAT | 3 mΩ 1206 | — | "fixed at 5 mΩ; **using a different value is not recommended**" (§7.2.1.2.7) | same footprint |
| Separate gate supply | 36 V SOT-23-6 buck at ~9 V into DRV_SUP, e.g. **TPS560430X** | C524782 / C523980, ~2.4k pcs, ~$0.35–0.60 | DRV_SUP accepts 4.5–12 V (§6.3.3.2), OVP 13.2 V (p.11); SiZ240DT 6.7/7.0 mΩ typ at 10 V vs ~10 mΩ at 4.5 V, Qg 15.2 / 14.2 nC at 10 V | ~30–35 mm² per port (IC + 1 small inductor + 3 passives), < 2 mm tall |
| DRV_SUP from PP5V | no new part: R420 link moves from REGN to PP5V | — | removes the LDO drop only (5 V gate unchanged) | 0 mm² |

**TPS25751S risk.** The EVM guide lists the charger-integration (BQ) configurations only as "TPS25751D + BQ" (slvucp9 §4.3.1.2). Datasheet fig. 8-16 also draws PP_EXT as a *sink* path. Source-mode PP_EXT with BQ25756 control isn't confirmed. Ask TI (E2E) before committing.

## 3. Recommendation and watts saved

Savings come from the model copy, in the order 30 W / 100 W / 100 W at 12 V / 88 W charging.

| # | Change | Type | Saved (W) | Cost / area / height |
|---|---|---|---|---|
| 1 | **EN_PFM = 1 while sourcing, 0 while charging** | **firmware** (I2Cw through the TPS25751 on each role change) | 0 / 0 / 0 / 0 at these points. **About 0.3–0.45 W saved per port when attached at no or light load** (forced PWM at 600 kHz ≈ 0.12 gate + 0.2 core + 0.07 Coss + 0.06 dead time + ripple I²R ≈ 0.45–0.5 W) | free |
| 2 | **Sink policy: prefer 20 V over 15 V when charging** | **TPS25751 config** (sink PDO preference) | 45 W charge: 2.73 → 2.34 W (**−0.39**); −0.48 at a 16 V pack | free |
| 3 | **DRV_SUP ≈ 9 V from a small buck** (FET 13 → ~9.5 mΩ warm; gate loss rises) | part + config | **0.03 / 0.45 / 0.80 / 0.20** | ~$1–1.5/board, +35–70 mm², < 2 mm |
| 3b | (if 3 is rejected) DRV_SUP from PP5V | link move + firmware (PP5V must be on whenever the charger runs) | 0.07 / 0.08 / 0.07 / 0.10 | free |
| 4 | TPS25751S + CSD87501L (PPHV 18 → ~8 mΩ warm) | part + full re-config, **only if TI confirms** | 0.12 / 0.30 / 0.34 / 0.17 | ≈ +$0.9/port, ≈ 0 mm² net, re-layout of the port corner |
| — | RAC 5 → 2 mΩ | rejected | 0.035 / 0.09 / 0.10 / 0.05 | — |
| — | RBAT 5 → 3 mΩ | rejected | 0.01 / 0.15 / 0.26 / 0.06 | — |

Items 3 and 4 together: **0.15 / 0.75 / 1.13 / 0.37 W**. Totals go to 1.89 / 10.68 / 15.97 / 6.34 W.

**Why the sense resistors stay at 5 mΩ:**

- **RAC.** The TPS25751 writes IAC_DPM itself on every contract (contract current + INDPM margin, EVM Q12). All register LSBs are defined for 5 mΩ (REG0x06, REG0x0A, REG0x2D). With 2 mΩ every written limit would be **2.5× too high**, so a 3 A adapter would be allowed 7.9 A. TI moved its own EVM from 2 mΩ to 5 mΩ for exactly this reason (slvucp9 table 1-1, note 1). Accuracy at 2 mΩ is also only ±7 % at 5 A (p.9), and worse at 3 A. That eats a 5 % INDPM margin. The gain is under 0.1 W.
- **RBAT.** TI says fixed. A change scales the following:
    - ICHG_REG, IPRECHG, ITERM, IBAT_REV and the IBAT ADC;
    - the ICHG pin limit (9.1 kΩ would allow ~9.2 A);
    - the VICHG_OC comparator.

  A watchdog reset puts ICHG_REG back to its 20 A default, so the pin limit is the backstop that would be wrong. Not worth 0.15 W.

**PD voltage when sourcing.** The sink picks the voltage, and PD source power rules require 9, 15 and 20 V for a 100 W PDP, so firmware can't steer it. For reference, total loss at 30 W:

| Pack | 9 V | 15 V | 20 V |
|---|---|---|---|
| 14.4 V | 2.04 W | 1.81 W | 1.50 W |
| 12 V | 2.22 W | 1.81 W | 1.88 W |

The lowest-current option wins, except when the pack sits near the USB voltage (buck-boost band).

What firmware *can* do:
- (a) **Offer 60 W or less on the second port** while one is busy. The dual-port "80 + 20 W" rule already does this.
- (b) **Keep the idle port's charger fully off:** EN_REV = 0, ADC off. The ADC costs 0.5 mA, about 7 mW at 14.4 V (p.8, §6.3.7). Poll TS_ADC one-shot only on the active port.
- (c) **Throttle earlier at a low pack voltage.** 100 W at 12 V costs 5.7 W more than at 14.4 V.

"Use one port's charger" already holds: each charger is hard-wired to its own connector.

**Dead time:** keep the 45 ns default (REG0x3C = 0; the minimum). Fix ringing with the R444–R447 gate resistors, not longer dead time: each +30 ns costs ~0.1 W at 100 W.

**Quiescent / MCU:** 0.05–0.08 W total. Nothing worth over 20 mW is left: Standby between supervision polls, TPS62177 SLEEP in idle.

**5 V path (optional):** TPS62933 RT floating gives 500 kHz (tps62933.pdf p.3), saving ~0.15 W at 15 W out. It needs L402 at 4.7 µH: at 3.3 µH and 16.8 V the peak reaches ~4.1 A against the 4.2 A minimum HS limit. That is a part change. Low priority.

**Risks:**
- **PFM:** VBUS ripple and load-step undershoot against PD vSrcValid, and audible noise. TI gives no reverse-mode PFM data.
- **9 V DRV_SUP:**
    - TI requires DRV_SUP off whenever the converter is disabled (§6.3.3.2). One option is to enable each port's buck from that port's REGN, but the one-shot ADC also raises REGN, so confirm with TI.
    - Higher HS-gate swing gives faster edges (EMI) and higher bootstrap-diode stress; LRB520S-40 is fine at 9 V.
    - A 10 V pack drops DRV_SUP to ~9.7 V (100 % duty), which is fine.
- **TPS25751S:**
    - BQ-integration support is unknown.
    - A 30 V FET sits under a 28 V TVS clamp (2 V of margin; TI's own reference accepts it).
    - Inrush SOA of a PicoStar FET during PP_EXT soft-start: about 0.06 A × 20 V for ~50 ms. Check it against the CSD87501L SOA curve.
    - LGA placement at JLC.

## 4. Interactions

- **DRV_SUP voltage and the FET area:** whoever picks the charger FETs should compare at 9 V gate, not 4.5 V. A FET that is best at 4.5 V may not be best at 9 V, and Qg at 9 V doubles. Gate loss scales with f_sw, so a lower frequency (another area) helps the 9 V option.
- **Lower f_sw** also shrinks the PFM gain, and needs more L.
- **Pack-path and cell changes:** lower battery current makes RBAT even less worth touching.
- **TPS25751S:** frees ~8 mm² under the controller but adds FET routing at the crowded port corner.

## 5. What to measure on P0

1. **No-load and 0.5 A input power from the pack**, sourcing 9 V and 20 V, with EN_PFM = 0 and then 1. Scope VBUS ripple and a 0.1 → 3 A step.
2. **VBUS → PPHV drop at 3 A and 5 A** (TP401/TP402) for R_PPHV. **Connector drop** from plug to TP401 at 5 A.
3. **REGN LDO temperature** and pack current with the converter idle versus switching (gate charge × f).
4. **Bench test for DRV_SUP:** lift R420, feed DRV_SUP 9 V from a bench supply, and compare efficiency at 60/100 W against REGN drive. This is the cheapest way to settle item 3 before adding a part.
5. **Charging from a 45 W adapter** at 15 V versus 20 V contracts: input and battery power from the BQ25756 ADCs plus a meter.
6. **5 V 3 A:** pack power versus output power, and TPS62933 temperature.

## Sources

- datasheets/bq25756.pdf (SLUSEN5A): §5.3, §5.5 pp.8–12, §6.3.3.2–6.3.3.4, §6.3.5.1.1.1, REG0x02/06/0A/2D/2F/3C, §7.2.1.2.7–8
- datasheets/tps25751.pdf (SLVSH93A): pp.2–3, 11–14, figs. 6-5, 6-7, 6-8, 8-16
- datasheets/tps25751evm-slvucp9.pdf (table 1-1 note 1, §4.3.1.2), bq25756evm-sluuct7.pdf
- datasheets/siz240dt.pdf p.2, tps62933.pdf pp.3, 6, usb-c-16pcb1.6-ip68.pdf
- [CSD87501L LCSC](https://www.lcsc.com/product-detail/C701751.html), [TI CSD87501L datasheet](https://www.ti.com/lit/gpn/CSD87501L), [TPS25751SRSMR LCSC](https://www.lcsc.com/product-detail/C22460852.html), [TPS560430X LCSC](https://www.lcsc.com/product-image/C524782.html)

## Cross-examination (round 2)

Checked against the datasheets and the model copy (`e_variants.py`), not against the other files' own claims.

### 1. DRV_SUP at 9 V: A's TPS7A4101 LDO against my TPS560430 buck

Gate current at 9 V is about 26.5 nC per leg (siz240dt.pdf p.2, Qg at 10 V scaled) × 600 kHz = **16 mA**, or 32 mA in buck-boost. Both supplies run from PACK_P in every mode, including charging.

| Supply | Input power at 14.4 V | Model saving vs today (30 / 100 / 100 at 12 V / 88 chg, W) |
|---|---|---|
| Buck, ~85 % at 16 mA | 0.17 W | 0.03 / 0.45 / 0.80 / 0.20 |
| LDO (input = Vpack × I) | 0.23 W | −0.03 / 0.38 / 0.77 / 0.13 |
| A's own model, LDO with GPIO gating | — | 0.00 / 0.43 / 0.72 / 0.22 |

- **The buck wins by only 0.01–0.09 W:** about 0.01 W at a 12 V pack and 0.09 W at 16.8 V.
- **The buck costs more:**
    - a second switcher beside the gate driver, with its own EMI;
    - an inductor (+10 mm²);
    - the same enable problem.
- **Verdict: take A's LDO** (TPS7A4101, or TPS7A1601 for 100 mA of margin, since buck-boost needs 32 mA). Withdraw my buck.

**The TI rule, exact wording.** From bq25756.pdf §6.3.3.2 *REGN Regulator*, p.21: "When the converter is disabled, the DRV_SUP supply needs to be disabled such that BTST1/BTST2 and DRV_SUP pins are not biased."

**A's EN = REGN doesn't fully meet it.** §6.3.7, p.31 says: "When the system load is powered from the battery (the input source is removed, or the device is in HIZ mode), enabling the ADC automatically powers up REGN." The checklist's TS_ADC one-shot poll every second would therefore wake the 9 V LDO with the converter off.

**Fix:**
- EN = REGN through 100 k, AND an open-drain MCU GPIO pulling EN low. DIO12, DIO18 and DIO20 are free on production; one GPIO per port.
- Firmware releases the GPIO only while that port's converter runs (charging, or sourcing a contract above 5 V). It never polls ADC on an idle port.
- An unprogrammed MCU leaves the GPIO floating, so EN follows REGN. The dead-pack charge path still works through A's Schottky REGN→DRV_SUP fallback.
- The C411 decay after a converter stop (4.7 µF) is the same as with REGN drive. Still ask TI E2E what "biased" protects against.
- This applies equally to any external DRV_SUP source.

### 2. The 5 V path, quantified, and the fix

**Today, 5 V 3 A (15 W) from a 14.4 V pack.** Mostly estimated, because the TPS62933 efficiency curves aren't readable as text.

TPS62933 at 1.2 MHz:

| Loss in the TPS62933 | W | Basis |
|---|---|---|
| High-side conduction | 0.32 | 76 mΩ, tps62933.pdf p.6, ×1.3 warm |
| Low-side conduction | 0.24 | 32 mΩ ×1.3 |
| Edges and dead time | 0.3 | ~8 ns edges |
| L402 DCR | ~0.2 | 15–25 mΩ assumed |
| Bias | 0.02 | |
| **Buck total** | **≈ 1.1** | |

Downstream and upstream of the buck:
- PP5V switch, about 44 mΩ warm (36 typ / 53 at 125 °C, tps25751.pdf p.11): 0.40 W.
- Contacts and VBUS copper: 0.11 W.
- Cells and pack path: 0.15 W.
- House: 0.05 W.

**Total ≈ 1.8 W, ~89 %.**

**Fix: source the 5 V PDO from PPHV, through the BQ25756 in reverse mode.**
- The TPS25751 TRM register 0x32 field *Power Path for PDO 1* (SLVUCR8B p.36) allows "0h = PP5V, 2h = PP_EXT". PP_EXT means PPHV on the TPS25751D (TRM table 2-1).
- The BQ25756 regulates reverse VAC at 5 V (VAC_REV = 0x00FA, ±2 %, p.10).
- Model, 5 V 3 A through the BQ25756 buck, including cells: **1.43 W** (1.42–1.46 over 12–16.4 V). That is **about 0.4 W saved at 15 W** (~2.5 points).
- The 5→9/20 V renegotiation also stays on one path, with no PP5V→PPHV handover.
- PP5V/TPS62933 stays: it powers the PD state machine, Rp and VCONN (TI E2E). It then idles in PFM.
- **Config only, no part change.** EN_PFM = 1 in reverse (item 1 of §3) keeps light 5 V loads efficient.

**To confirm before relying on it:**
- that the TPS25751's charger integration commands EN_REV and VAC_REV = 5 V and IAC_REV for PDO1 / implicit contracts (TI or bench);
- tVBUSON: the BQ25756 needs about 40 ms of start-up tuning (§6.3.3.3), well inside 275 ms;
- 5 V short-circuit behaviour: IAC_REV regulation replaces the PP5V current limit, the same protection 9–20 V already rely on.

**Fallback (part change):** TPS62933 RT floating = 500 kHz (p.3) with L402 at 4.7 µH. Saves about 0.13 W.

### 3. Double counting

- **DRV_SUP 9 V:** my item 3 and A's R1 are the same change. **Count it once, using A's figures** (0.00 / 0.43 / 0.72 / 0.22), and drop mine from any sum.
- **Gate-drive correction:** A, B and I each found that the model's 0.10 W lump is low (VAC × Qg × f). It is a baseline correction, counted once, not a saving.
- **Not additive:** C's fuse correction (5 → 2.5 mΩ) and D's nickel correction (5 → 8.5 mΩ) move the shared baseline in opposite directions, by −0.16 and +0.21 W at 100 W.
- **I² feedback:** savings from different areas don't add exactly. Lower battery current shrinks every I² term, so the sum overstates the combination by about 3–5 %.
- **Sink voltage preference:** TRM table 3-23, *Auto Neg RDO Priority* = 0 (default) already picks the higher voltage when PDO power ties (15 V 3 A vs 20 V 2.25 A). That item is "keep the default and keep 20 V inside ANMaxVoltage", not a new saving.

### 4. The most serious flaw in each finding

**A (charger FETs)** — **Agree with R1 and the LDO**, with the gating fix.
- EN = REGN is not equivalent to "converter enabled": the ADC raises REGN (p.31). This violates the p.21 rule A itself cites. Fix as above.
- Secondary: R2's +0.18 W at 30 W rests on the √Qgd edge scaling A admits is uncertain. Measure it before choosing R2.

**B (frequency, inductor)** — **Agree with R1**, but prefer XGL7030-**332** (as B's own conservative option), and verify the land pattern.
- Coilcraft rates the XGL7030-222 I_sat at 5.5 A (−10 %), 9.7 A (−20 %) and 14.5 A (−30 %) ([Coilcraft XGL7030](https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/xgl/xgl7030/)).
    - At the 117 W corner peak (15.7–15.9 A) it is beyond its last published point (L < 1.54 µH). Ripple and peak then rise further, so B's "same as today, 1.6 µH" is optimistic at the peak.
    - At 100 W the 9.5 A peak sits right at the −20 % point.
- The "time constant 0.05–1.26 µH/mΩ" (bq25756.pdf §7.2.1.2.4) is ambiguous in TI's text. B's L/DCR reading is plausible but unconfirmed.

**C (pack path)** — **Agree with the swap**, conditional on the measured turn-off at the SCD test (C's own §6 item 3). Make that test a P0 gate.
- The short-circuit turn-off estimate (13 µs Miller time, 22 mJ) scales from the **typical** CHG/DSG fall time (40 µs into 4.7 nF, bq40z50-r2 §7.18).
- The **maximum** is 300 µs. The XRS120N04D (≈4.3 nF effective) could then sit on the plateau for roughly 7× longer, about 100 µs at ~1.7 kW ≈ 170 mJ. That is well past its SOA. The AGM404AP1 at a third of the charge would see about a third of that.
- The datasheet quality of an obscure brand adds risk.

**D (cells, interconnect)** — **Agree with the nickel/copper option A and the P0 DCR measurement.** The P60B case is not proven until both cells are measured the same way.
- The P60B saving (2.5 W at 100 W) compares Molicel's datasheet DC-IR (a short pulse) with an estimated 58E DC value built from other makers' longer-step ratios. The two numbers aren't measured the same way, so the 0.55× ratio is unverified.
- The ×1.5 near-empty factor is generic, not 58E data.
- D is also stale in two places:
    - it cites "F101 I²t", but F101 was deleted in rev A6 (C: only F102 remains);
    - it assigns short-circuit sign-off to "area B" instead of C.

### Revised recommendation (area E, de-duplicated)

| Item | Type | Saved, W (30 / 100 / 100 at 12 V / 88 chg) |
|---|---|---|
| EN_PFM = 1 while sourcing | firmware | 0 at these points; 0.3–0.45 W per port at light load |
| **5 V PDO from PPHV via BQ25756** | TPS25751 config | **≈ 0.4 W at 15 W, 5 V** (not in the four columns) |
| Keep Auto Neg RDO Priority = higher voltage | config check | protects about 0.4 W at 45 W charging |
| DRV_SUP 9 V | **= A's R1** (LDO + GPIO gating) | counted under A |
| TPS25751S + CSD87501L | part, only if TI confirms the BQ integration | 0.12 / 0.30 / 0.34 / 0.17 |
| RAC / RBAT reduction | rejected | — |

Sources added: bq25756.pdf pp.10, 21, 31; TPS25751 TRM SLVUCR8B pp.36, 42 (table 2-1, register 0x32, table 3-23); [Coilcraft XGL7030](https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/xgl/xgl7030/).
