# A — Charger FET conduction losses

Researcher A, 2026-10-21. This is research only: nothing in the repo was changed. The model copy and the variant script are in the scratchpad:
- `C:\Users\Logan\AppData\Local\Temp\claude\C--Users-Logan-Documents-BatteryBank\e185e067-8e49-4b1c-9840-e0e47a30eac1\scratchpad\a\heat_sources.py`
- `...\scratchpad\a\fet_variants.py`, which sets a FET for each switch position and the gate-drive source.

## 1. The current parts and what they really lose

Each port has two **SiZ240DT** half-bridges. Q401 is leg A, on the USB side. Q402 is leg B, on the battery side.

| SiZ240DT (siz240dt.pdf p.2–3) | Ch-1 (high side) | Ch-2 (low side) |
|---|---|---|
| RDS(on) at 4.5 V, typ / max | 9.41 / 12.25 mΩ | 10.07 / 13.30 mΩ |
| RDS(on) at 10 V, typ / max | 6.71 / 8.05 mΩ | 7.01 / 8.41 mΩ |
| Qg at 4.5 V / 10 V | 6.9 / 15.2 nC | 6.5 / 14.2 nC |
| Qgd · Coss at 20 V · Qrr | 1 nC · 230 pF · ~10 nC | 1 nC · 170 pF · ~9.5 nC |
| VGS(th) · VGS max | 1.1–2.4 V · +20/−16 V | same |

**Checking the model.** The conduction formula 2·R·I² is right. Whatever the duty cycle, one leg's high side is on 100 % of the time while the other leg's two FETs share the period.
- 13 mΩ is the typical 4.5 V value × 1.38, which is a junction at about 95–100 °C. That is a fair "hot typical".
- The low side is a little worse: 10.07 × 1.38 = 13.9 mΩ.
- A maximum-spec part when hot is about 17–18 mΩ. Treat the conduction row as **−0 / +30 %**.
- Inductor ripple adds only about 1–2 % (I_rms² factor at 3 A peak-to-peak).

**Corrections.**
- **Gate drive is under-counted.**
    - REGN is an LDO from VAC, so its gate power is VAC × Qg × f (bq25756.pdf §6.3.3.2, eq. 29).
    - Only the switching leg's two FETs are charged each cycle: 20 V × 13.4 nC × 600 kHz = **0.17 W** at the 20 V operating points.
    - The model's "gate drive + IC" lump is 0.10 W, so the 20 V cases are low by about 0.1 W.
    - The model also has no Qrr term (about 10 nC × 20 V × 600 kHz ≈ 0.12 W). It may be hidden in T_EDGE.
- **The heat is split evenly between the packages, not concentrated.**
    - At 100 W reverse, the always-on leg B high side makes **0.78 W** in one die.
    - Leg A makes 0.77 W of conduction plus all of the 0.87 W switching, so **Q401 (leg A) is the hottest package**, at about 1.6 W at 14.4 V and about 2.3 W at 12 V.

**Which FET does what** (BQ25756 table 6-1; review 4 B-1):

| Mode | 100 % on | Hard-switched | Sync (its Qrr is hit) |
|---|---|---|---|
| Reverse boost 20 V (60–100 W) | leg B high side | leg A low side | leg A high side |
| Forward buck, 88 W charging | leg B high side | leg A high side | leg A low side |
| Reverse buck 9 V (30 W) | leg A high side | leg B high side | leg B low side |
| Forward boost from 5/9 V | leg A high side | leg B low side | leg B high side |

So the **leg B high side carries the full battery current at 100 % duty in both heavy modes**, and it switches only in the light modes (≤ 30 W). It is the one position where a large die costs almost nothing.

## 2. Candidates (JLC API queried 2026-10-21)

| Part | LCSC | JLC stock / $ at 100 | Package, height | RDS(on) at 4.5 V typ/max | at 10 V max | Qg 4.5 / 10 V | Qgd | Coss | Qrr | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| **SiZ240DT** (today) | C3289403 | **2** / 0.81 (hand-supply) | PowerPAIR 3×3S | 9.4 / 12.25 (HS) | 8.05 | 6.9 / 15.2 | 1.0 | 230 | ~10 | siz240dt.pdf p.2 |
| **BSZ018N04LS6** (Infineon, Tj 175 °C) | C534643 | 202 / 1.10 | TSDSON-8FL 3.3×3.3, ~1.0 mm | **2.1 / 2.7** | 1.8 | 15 / 31 | 3.8 | 690 | 55 (at 20 A, 400 A/µs) | DS rev 2.1 p.4–5; VGS(th) 1.3–2.3 V |
| **TPN2R304PL** (Toshiba) | C5802634 | 1917 / 0.51 | TSON-Adv 3.1×3.3×0.85 | — / 4.0 | 2.3 | — / 41 | n/a | Qoss 27 nC | 30 | Toshiba product page; VGS(th) 1.4–2.4 V |
| PGQ04N070 (JinYu, dev-board part) | C49384056 | 4791 / 0.10 | PDFN3333 | 7.2 / 10 | 5.1 typ | ~7 / 14.7 | 2.5 | 309 | 15 | review4 B-2; LCSC |
| IAUC45N04S6L063H (5×6 half-bridge) | C3288896 | 62 / 0.71 | TDSON-8 5×6 | 7.4 / 8.5 | 6.3 | — / 10 (13 max) | 2.1 | 174 | 8 | iauc45n04s6l063h.pdf p.2–3 |
| IAUC60N04S6L045H (5×6 half-bridge) | C3278715 | 251 / 0.78 | TDSON-8 5×6 | ~5.3 / ~6.1 (est.) | 4.5 | — / 19 | ~3 | 325 | ~12 | LCSC parametrics only; datasheet not read |
| BSC010N04LS6 (5×6 single) | C7220836 | 1524 / 0.63 | TDSON-8 5×6 | ~1.4 | 1.0 | — / 67 | — | — | — | LCSC; too much Qg, too much area |

**Rejected:**
- IAUC60N04S6N050: VGS(th) 3 V, not logic-level.
- 3×3 half-bridges at 30 V (SiZ340): the README rules these out.
- Paralleling two SiZ240DT per leg: it doubles Coss and Qg on the switching leg and adds about 17 mm² per leg. It gets only about 0.39 W at 100 W (half of the leg B high-side share).
- Whole-stage 5×6 half-bridges:
    - IAUC45 everywhere saves only 0.21 W at 100 W, because its larger Qgd and Coss give back the gain.
    - IAUC60 on leg A *raises* switching loss by about 0.4 W at 100 W.
    - Both also add about 19 mm² per leg.
    - At 600 kHz, leg A's hard-switched duty favours a small die; SiZ240DT's Qgd = 1 nC is very good.

**Gate drive (bq25756.pdf):**
- DRV_SUP may be fed externally at **4.0–12 V** (p.7, ROC; pin 23 text p.5: "external supply up to 12V").
- DRV_OVP is 12.8 / 13.2 / 13.6 V (p.12).
- BTST−SW has an absolute maximum of **14 V** (p.6).
- The supply must be able to deliver ≥ 50 mA and **must be off whenever the converter is disabled** (§6.3.3.2).
- TI's EVM allows 4–11 V on DRV_SUP and has an EXT_DRV jumper (SLUUCT7 operating table).
- At 9 V the SiZ240DT runs at about 6.8 / 7.1 mΩ typical, against 9.4 / 10.1 mΩ at 4.5 V. That is about 30 % lower, and its gate is rated +20 V.

## 3. Recommendation

> **Revised after cross-examination.** See the last section:
> - The LDO's EN must be an AND of the MCU GPIO and REGN, not REGN alone.
> - R1's 100 W saving is −0.38 to −0.43 W.
> - R2 also costs about +0.2 W when charging from 9 V.

The model's results (`fet_variants.py`, change in charger FET conduction + switching + gate drive):

| Variant | 30 W | 100 W | 100 W, 12 V | 88 W charging |
|---|---|---|---|---|
| **R1: external 9 V DRV_SUP, gated off below ~45 W** | 0.00 | **−0.43** | **−0.72** | **−0.22** |
| R1, always on (EN = REGN only) | +0.05 | −0.43 | −0.72 | −0.22 |
| **R2: R1 + leg B split, BSZ018N04LS6 high side + PGQ04N070 low side** | +0.18 | **−0.87** | **−1.42** | **−0.46** |
| R2 with TPN2R304PL (cheaper, well stocked) | +0.29 | −0.84 | −1.37 | −0.44 |
| Leg B split only, REGN drive | +0.18 | −0.60 | −0.96 | −0.32 |
| Both legs IAUC45 (5×6) | −0.04 | −0.21 | −0.37 | −0.10 |

With R2, FET conduction at 100 W goes from 1.55 W to 0.72 W. The leg B high-side die drops from 0.78 W to 0.14 W (from 1.23 W to 0.22 W at 12 V), and leg A's conduction drops from 0.77 W to 0.58 W.

**R1: feed DRV_SUP from a 9 V LDO off PACK_P. Do this.** Per port:
- **U (new):** TPS7A4101DGNR (C111739, 10.6k in stock, $0.80, MSOP-8-EP, 50 V in, 50 mA, EN), set to 9 V.
    - 50 mA exactly meets TI's "≥ 50 mA" text, against about 20 mA of real load.
    - For margin, use TPS7A1601QDGNRQ1 (C2862225, 5k in stock, $1.91, 100 mA, 60 V).
    - At 16.8 V it dissipates ≤ 0.16 W.
- **EN:** 100 k from REGN to EN, plus an optional open-drain MCU GPIO to EN.
    - REGN exists only while the converter is enabled, which meets the "off when disabled" rule.
    - With the GPIO, firmware can drop to REGN drive below ~45 W (the 30 W case is then 0.00 W instead of +0.05 W). It also gives a free A/B efficiency test.
- **R420 (10 Ω REGN→DRV_SUP) becomes a Schottky diode REGN→DRV_SUP** (the LRB520S-40 already in the BOM). This is required:
    - The P0 wake-up path charges through the BQ25756 while PACK_P is dead or the protection FETs are open.
    - With PACK_P dead the LDO has no input, and REGN − 0.35 V ≈ 4.6 V keeps DRV_SUP above DRV_UVP (3.7 V).
- **C411/C511** go from 4.7 µF 10 V 0402 to **4.7 µF 25 V 0805** (CL21A475KAQNNNE, C1779, basic part). A 10 V part at 9 V is out of rating and loses most of its capacitance.
- **Cost, area, weight and height:**
    - About $1.0–2.1 per port.
    - About 20–25 mm² per port: MSOP plus 2 resistors and an input cap, and the cap grows from 0402 to 0805.
    - Under 0.1 g, and well under 3.2 mm tall.
    - No power-stage relayout.
- **Margins:**
    - BTST−SW is about 8.6 V against the 14 V absolute maximum.
    - DRV_SUP is 9 V against a 12.8 V minimum OVP.
    - D404/D405 (40 V) and C412/C413 (0.1 µF 50 V) are fine.
    - It also helps review 4 B-1: the high side held on 100 % starts from about 8.6 V instead of about 4.4 V, far above the 2.7–3.9 V refresh floor.

**R2: split leg B into a large-die high side and a small low side. Do it if the board can take about 15 mm² more per port.**
- **Parts:** BSZ018N04LS6 in the leg B high-side position, and PGQ04N070 (or a SiZ240-class small die) as the leg B low side.
- **Footprint:** both use the standard PDFN3333 S1–3 / G4 / D5–8 pinout, which the dev-board library already has.
- **Area:** leg B goes from one 16.6 mm² courtyard to two of about 15.6 mm², about +15 mm² per port and about 30 mm² for the board. It also reopens the leg B placement and SW2 routing.
- **Cost:** +$0.39 per port. It also removes one hand-supplied SiZ240DT per port, because both new parts are stocked at JLC. BSZ018N04LS6 has only 202 in stock, so for volume the fallback is TPN2R304PL ($0.51, 1.9k in stock).
- **Height:** ≤ 1.0 mm.
- **The price is +0.18 W at 30 W.** In 9 V reverse buck, the big die becomes the hard-switched FET: Coss 690 pF and Qgd 3.8 nC against 230 pF and 1 nC. That penalty is the least certain number here, because the edge term scales roughly with √Qgd.
- **Choose R2 if** 100 W heat is the constraint the design is built around. Choose R1 alone if 30 W runtime matters more.

**Risks:**
- **Ringing and EMI:** about 3× faster turn-on at 9 V raises dv/dt and the SW1/SW2 overshoot against the 40 V FETs (review 4 B-6). The 0 Ω gate links R444–R447 can take 2.2–4.7 Ω, and B-5 caps them at 4.7 Ω.
- **Turn-off from 9 V:** it takes about 3 ns longer to reach the plateau, which is still well inside the 45 ns dead time.
- **SOA and short circuit:** not worse. The BSZ018 die is larger. The current limits (ILIM, IBAT_REV) and the BQ40Z50 short-circuit protection are unchanged. There is no inrush change.
- **Firmware:** optional DRV_SUP gating by contract power, and handling DRV_OKZ_FLAG.
- **Bootstrap:** a bigger leg B high side needs the bootstrap cap C413/C513 at ≥ 0.22 µF (review 4 rule: Qg > 15 nC).

## 4. Interactions with other areas

- **Switching frequency (area B/C):** at a lower fsw the switching penalty of a large die shrinks.
    - At ~400 kHz, a 5×6 IAUC60 on leg A might pay off.
    - A 9 V drive cuts the edge loss on whichever FET is hard-switched.
    - The gate-drive cost (Vpack × Qg × f) scales with fsw.
- **Inductor:** no direct change. Lower FET heat leaves more thermal budget for the APS0730.
- **TH401/TH501:** they must stay on the hottest FET copper, which is now leg A (Q401).
- **Thermal model:** about 0.9 W less at 100 W, mostly at the leg B position.
- **Idle and sleep current:** none, because the LDO is off without REGN.
- **Pack path (other researcher):** none.

## 5. What to measure (on P0: there is no dev board after 2026-10-18)

1. Leg A and leg B die temperatures (thermocouple or IR) at 100 W reverse from 12 V and 14.4 V, and at 88 W charging, with DRV_SUP at REGN and then at 9 V. Use the GPIO for an A/B on the same board.
2. VDS(on) of the leg B high side by Kelvin probe at 5 A and 8 A, hot. This gives the real RDS(on) against the 13 mΩ assumption.
3. HG2−SW2 and HG1−SW1 in 100 % modes, with the minimum gate voltage over a long hold (B-1). BTST−SW peak against 14 V.
4. SW1/SW2 overshoot at 9 V drive with 0 Ω and with 2.2 Ω gate links.
5. 30 W, 9 V efficiency with the split leg B, to confirm or disprove the +0.18 W penalty.
6. Dead-pack wake-up through the Schottky fallback (PACK_P = 0, charging from 5 V and 20 V), and a DRV_OKZ flag check.

## Cross-examination (round 2)

### (1) DRV_SUP from an LDO or a buck: settled with numbers

**Gate charge.** Gate charge at 9 V drive, by interpolating between siz240dt.pdf's 4.5 V and 10 V values (p.2):
- SiZ240DT: 13.7 nC (HS, at 8.5 V after the bootstrap diode) + 12.6 nC (LS) = 26.3 nC per switching leg.
- With R2's leg B (BSZ018 + PGQ04N070): about 40 nC.

**DRV_SUP current at 598 kHz**, plus about 2 mA of driver bias (assumed):

| Case | Current |
|---|---|
| One leg switching (buck or boost) | **~18 mA** |
| Both legs switching (buck-boost band, e.g. 15 V out from 14–16 V) | ~34 mA |
| R2, both legs switching | ~42 mA |

**Supply input power** (LDO: V_pack × I; buck: 9 V × I / η, with η ≈ 0.80 at 18 mA, assumed for a TPS560430-class part):

| Pack | LDO in | LDO dissipation | Buck in | Buck advantage |
|---|---|---|---|---|
| 16.8 V | 0.30 W | (16.8 − 9) × 18 mA = **0.14 W**; 0.27 W at 34 mA | 0.20 W | 0.10 W |
| 14.4 V | 0.26 W | 0.10 W | 0.20 W | 0.06 W |
| 12 V | 0.22 W | 0.05 W | 0.20 W | 0.02 W |
| 10 V | 0.18 W | 0.02 W | 0.20 W (near max duty) | −0.02 W |

**Light load.** Below ~45 W, both versions are switched off and DRV_SUP falls back to REGN through the Schottky. Their light-load cost is then **zero**, with the LDO's 25 µA quiescent current only while it is enabled. Left on, either one costs about +0.05 W at 30 W (§3).

**Verdict: the LDO.**
- The buck gains at most 0.06 W at the nominal 100 W point, and about 0 W near empty, where the heat matters most.
- That doesn't pay for a third switcher per port, at a different frequency right beside the gate drivers. That switcher brings an inductor, a hot loop and an EMI source, about +10 mm² more than the LDO, and dropout or duty limits at a 10 V pack.
- E's buck is a valid alternative if a later layout finds the area. The physics is the same; it is not a second saving.

**Part choice.**
- R1 alone, at 34 mA worst case: TPS7A4101 (50 mA) is enough.
- With R2, at 42 mA: use **TPS7A1601QDGNRQ1** (C2862225, 100 mA, 60 V, 5k in stock, $1.91). It runs at about 16 K rise at 0.27 W in MSOP-8.

**The sequencing rule** (bq25756.pdf §6.3.3.2: "When the converter is disabled, the DRV_SUP supply needs to be disabled"). E is right that EN = REGN alone is not enough: §6.3.7 says "enabling the ADC automatically powers up REGN", so a one-shot TS/IBAT ADC read on an idle port would bring up 9 V on DRV_SUP. The revised circuit is per port:
- The **LDO EN is an AND of an MCU GPIO and REGN.**
    - The GPIO drives EN through 10 kΩ, with a 100 kΩ pull-down.
    - A small Schottky runs from EN (anode) to REGN (cathode), so EN is clamped to ≤ 0.3 V whenever REGN is off.
    - This needs one diode and two resistors, and no logic IC.
- **Firmware:**
    - Assert the GPIO only after REVERSE_STAT or CHARGE_STAT shows the converter switching, and only for contracts ≥ 45 W.
    - Deassert it before EN_REV = 0 or a charge disable.
    - On any INT or fault flag, deassert first and then read the registers.
- **When the MCU is reset or 3V3 is down**, EN is pulled low, the LDO is off, and DRV_SUP = REGN − V_F through the REGN→DRV_SUP Schottky. That is exactly today's TI-standard connection, which is what keeps the dead-pack wake-up path working.
- **Residual window:** the converter stops on its own (fault or VAC loss) while REGN stays up, until firmware reacts. DRV_SUP then sits at 9 V instead of REGN with the drivers idle. Whenever REGN is off, the LDO is off, so DRV_SUP is never biased with the IC unpowered, which is what the note is about.
- **Ask TI (E2E)** whether a ms-scale window is acceptable. If it isn't, take EN from the BQ25756 PG pin (open drain, pulled to REGN) instead of REGN.

**The baseline gate-drive figure is uncertain.** E reads REGN as fed from VBAT in reverse mode; I assumed VAC. The datasheet only gives eq. 29 with VAC and doesn't say. With VBAT, the baseline reverse gate loss is 0.12 W instead of 0.17 W, so **R1 at 100 W saves −0.38 W instead of −0.43 W**. Charging is unchanged.

### (2) Double counting

- **The REGN gate-drive correction** (~+0.1 W at 20 V) appears in A, B and E. Count it **once**, in the baseline.
- **E item 3 (9 V DRV_SUP from a buck) is my R1.** Count it once:
    - **−0.38 to −0.43 W at 100 W**, −0.72 W at 12 V, −0.22 W charging.
    - E's −0.45 / −0.80 / −0.20 is the same physics.
- **B (inductor, 500 kHz) and A are almost independent:**
    - Conduction saving doesn't depend on f.
    - At 500 kHz, R1's switching gain (−0.09 W) and its gate penalty (+0.05 W) both scale by 0.83: a net change of about +0.01 W.
    - R2's light-load penalty falls from +0.18 to about +0.15 W.
    - B's larger ripple raises FET I_rms² by about 1 %, under 0.01 W after R1/R2.
    - So B's and A's savings add to within ±0.03 W.
- **C and D lower the battery current** through less upstream loss, which shrinks A's I²-based savings by about 1–2 %. D's corrected near-empty cell resistance raises the 12 V current and slightly enlarges them.
- So: **add A, B, C and D directly, and don't add E-3 on top of A-R1.**

### (3) The other areas: main flaw and verdict

**B (inductor, frequency): agree with R1 (XGL7030-222) and with trying 500 kHz on P0.**
- Its physics checks out: DCR ∝ L ∝ 1/f in a fixed body, and its gate correction matches mine.
- **Most serious flaw:** the saturation margin rests on an unverified part.
    - At the 117 W corner the peak is 15.9 A, already past the XGL7030-222's −30 % point (14.5 A).
    - The BQ25756 has no cycle-by-cycle inductor limit (B's own finding).
    - "~1.6 µH at 13 A" comes from a roll-off curve B couldn't load, and the core loss is assumed to be half the APS0730's.
    - Prefer B's own conservative option, **XGL7030-332**, if P0 shows a cusp.
- **Its estimate of my R2's light-mode penalty (~0.3 W) is high for 9 V sourcing.** There the leg B *low* side (PGQ, 15 nC) is the sync FET, so BSZ018's Qrr doesn't recover.
- **But it is right for forward boost** (charging from a 9 V / 27 W adapter), where BSZ018 is the sync FET. I hadn't modelled that mode. By hand: +0.08 W edges (PGQ Qgd), +0.04 W Coss and +0.17 W Qrr (30 vs 10 nC × 14.4 V × 598 kHz), minus 0.06 W conduction, for **net ≈ +0.2 W**. I adopt that.
- **Stock:** XGL7030 isn't at JLC, so it is hand-supplied like the SiZ240DT.

**C (pack path): agree with XRS120N04D for Q101/Q102. I verified the F102 1.0–3.0 mΩ (tlc-wsfb1514.pdf p.1) and AGM 4.4/6.0 mΩ at 10 V.**
- **Most serious unverified claim: the 13 µs short-circuit turn-off.**
    - It assumes a 0.57 mA gate pull-down from the plateau. TI only gives a DSG fall time of 40 typ / **300 max µs into 4.7 nF** (bq40z50-r2 §7.18), and the XRS (~4.3 nF equivalent) is near that load.
    - At ~200 A, a slow max-spec turn-off would sit in the linear region for tens of µs. C's 22 mJ estimate also compares a 13 µs event against the 10 µs SOA line.
    - **Measure the DSG turn-off at a real SCD trip on P0** before trusting it.
    - Together with D's cells, the prospective short rises further (below).
- **Stock contention:** C's fallback (BSZ018N04LS6, 202 at JLC) is the same part as my R2 leg-B high side. Two per board each would exhaust the stock at about 50 boards. My R2 fallback is TPN2R304PL (1.9k in stock), so give BSZ018 to whichever area needs it more.

**D (cells, nickel): agree with nickel option A now, and with the P60B once it is buyable.**
- **Most serious flaw:** the headline "100 W at 12 V = 23.6 W" rests on an assumed ×1.5 near-empty DCR factor for a cell with no published DC data, and that number drives the thermal conclusion. It needs the P0 load-step measurement D lists before anyone redesigns around it.
- **Two errors:**
    - It cites "F101 I²t", but F101 was deleted. The fuse is F102 (verified in gauge.kicad_sch).
    - It assigns the pack-FET SOA check to "area B"; it belongs to C.
- **Its short-circuit numbers don't reconcile with C's** (C: ~185–200 A with the 58E; D: 125 A with the 58E). At 16.8 V with P60B (4 × 13 mΩ) plus ~19 mΩ of path after C's FET swap, the bolted short is about **235 A**.
    - That is beyond the XRS's ~80–120 A 1 ms line at 0.5–1 V. The SCD delay setting is then load-bearing for **both** C and D together.
    - The combined case must be signed off as one item.

**E (USB side, policy): agree with EN_PFM while sourcing, the 20 V sink preference, and keeping RAC/RBAT at 5 mΩ.**
- The TI quotes are checked: §7.2.1.2.7.
- **Most serious unverified claim: TPS25751S + CSD87501L.**
    - E itself flags that no TI material shows PP_EXT as a BQ25756-controlled *source* path.
    - A 30 V FET sits under a 28 V TVS clamp.
    - Keep it out of the plan until TI answers.
- **"REGN fed from VBAT in reverse" is plausible but not stated in the datasheet** (see above).
- E's DRV_SUP-from-PP5V fallback (3b) **gives no gate-voltage gain**, and it ties charger operation to PP5V being on. That is a new failure mode for 0.08 W, so I wouldn't do it.
- E's PFM idle saving (0.3–0.45 W per attached idle port) is real and **independent of A**. PFM also cuts the hours when the 9 V drive would run, and the GPIO gate keeps it off then anyway.

### Revised recommendation (A)

1. **R1, firm:** a 9 V DRV_SUP per port from a PACK_P LDO.
    - EN = GPIO AND REGN (diode clamp), with the REGN→DRV_SUP Schottky fallback replacing R420. C411/C511 become 4.7 µF 25 V 0805.
    - Enable it only for contracts ≥ 45 W.
    - TPS7A4101, or TPS7A1601-Q1 if R2 is done.
    - **Saves −0.38 to −0.43 W at 100 W, −0.72 W at 100 W from 12 V, −0.22 W charging, 0 W at 30 W.**
    - About $1–2 and 25 mm² per port.
2. **R2, conditional:** split leg B (BSZ018N04LS6 or TPN2R304PL high side + PGQ04N070 low side). Do it only if P0 thermals at 100 W bind.
    - Gains another **−0.44 W at 100 W** (−0.70 W at 12 V, −0.24 W charging).
    - Costs **≈ +0.2 W in 9 V modes** (30 W sourcing and 27 W charging), +15 mm² per port, and a leg B re-layout.
    - At 500 kHz (B), that penalty is about +0.15 W.
3. **The P0 A/B test is now free with the GPIO.** Toggle the 9 V drive at 100 W and read the efficiency change directly. That settles R1 before anyone commits to R2.
