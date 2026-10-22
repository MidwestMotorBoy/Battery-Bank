# D: the cells and their interconnect

Researcher D, 2026-10-21. This is research only: nothing in the repo was changed. The model runs used a copy of `heat_sources.py` plus a variant script in my scratch area. Cell resistances were swapped per scenario: one value at mid charge, one near empty.

## 1. The current parts and what they really lose

### Cells: 4 × EVE INR21700-58E in 4S1P

**Datasheet** (`datasheets/eve-inr21700-58e.pdf`):
- Capacity 5.6 Ah min, 5.7 Ah nominal (§3.1).
- AC 1 kHz impedance: "18 mΩ", measured at shipping charge level (§7.4).
- Maximum charge 5.6 A (1C), "not for cycle life" (§3.4).
- Maximum discharge 16.8 A (§3.6).
- Weight 71.0 ± 2 g (§3.8).
- 70 % capacity after 500 cycles at 0.5C charge / 1C discharge (§7.7).
- 70 % capacity at −20 °C (§7.6).

Batemo's own measurement: 71.1 g, 5.57 Ah, 20.29 Wh at C/10 ([Batemo](https://www.batemo.com/products/batemo-cell-explorer/eve-energy-inr21700-58e/)). That puts the pack at about 81 Wh.

**Independent DC resistance data for the 58E doesn't exist publicly:**
- lygte-info (HKJ) never tested it. His 21700 index stops at the Samsung 50G/48X, LG M50T and Molicel P42A.
- Mooch's 58E result isn't public.
- Batemo has measured its DC resistance but redacts the number.
- The only user report is "about 13 mΩ". That is an AC meter reading, and from a vendor page.

So I sized it from datasheets of the same cell class, which state both AC and DC values:

| Cell (energy class) | AC 1 kHz | DC, 50 % charge | DC/AC | Source |
|---|---|---|---|---|
| LG M58T (5.57 Ah) | 15 mΩ | 20 mΩ (6 A→1 A step, §4.2.2) | 1.33 | [LG spec rev 1.4](https://18650baterie.pl/wp-content/uploads/2025/05/Datasheet-LG-M58T.pdf) §4.2 |
| LG M50LT | 15 ± 6 | 23 ± 6 | 1.5 | [M50LT spec](https://evwest.com/support/21700_M50LT_datasheet.pdf) |
| Molicel M50A | 15 | 25 (10 A, 10 s) | 1.67 | [M50A V3](https://www.rosebatteries.com/hubfs/INR21700M50A-V3-80097.pdf?hsLang=en) |

The 58E's AC figure is 18 mΩ maximum, and real cells read about 13–16 mΩ. Applying a DC/AC ratio of 1.3–1.6 gives **about 20–25 mΩ DC at 50 % charge, new, 25 °C**. The model's **22 mΩ is a fair mid-charge, new-cell value**: keep it.

What the model gets wrong is that it uses 22 mΩ everywhere. The cell resistance moves with three things:

| Condition | Factor on DC resistance | Basis |
|---|---|---|
| Near empty (3.0–3.3 V/cell, the "12 V" case) | ×1.4–1.6 | Typical for NMC/graphite-Si. The 58E loses 5–10 % of capacity between 0.2C and 2C (§7.5), which is consistent. |
| Aged to about 80 % capacity (≈300–500 cycles) | ×1.3–1.5 | Typical. EVE allows 70 % capacity at 500 cycles (§7.7). |
| Cold, 0 °C | ×2–3 | LG cuts the M58T's pulse limit from 15 A to 9 A below 0 °C (§2.9.2). |
| Warm cans, 35–45 °C | ×0.8–0.85 | Partly offsets the rise at 100 W. |

**Corrected cell loss with 33 mΩ in the near-empty case:**

| Case | Model today | Corrected |
|---|---|---|
| 100 W, 12 V pack | 8.3 W | **13.9 W** (total 23.6 W) |
| 100 W, 12 V pack, aged cells | — | **≈20 W** |
| 100 W nominal | 5.26 W | 5.3 W (about right) |

The near-empty 100 W case is therefore the real thermal worst case, and it is cell-dominated.

The ±20 % uncertainty on DC resistance makes measuring it on P0 worthwhile (§5). I haven't added the entropic heat term; it is ±0.1–0.3 W at 8 A.

### Nickel interconnect

I recomputed the nickel from the geometry:
- **Layout:** `monolith_shell.py` puts the cells on a 2×2 grid at about a 22.9 mm pitch.
- **Parts:** `p0-assembly.md` gives the materials: three 0.15 × 7 mm series strips, and two 0.2 × 7 mm PACK tabs that split into 0.2 × 4.2 mm power fingers about 12 mm long.
- **Pure nickel resistivity:** ρ = 6.99 µΩ·cm at 20 °C, rising about 0.6 %/K.

| Piece | Length used | R at 20 °C |
|---|---|---|
| Series strip 0.15 × 7, weld to weld | ≈19 mm | 1.27 mΩ, ×3 = 3.8 mΩ |
| PACK tab: 0.2 × 7 (12 mm) + finger 0.2 × 4.2 (12 mm) | | 0.6 + 1.0 = 1.6 mΩ, ×2 = 3.2 mΩ |
| Welds (8 joints) + 2 slot solder joints | | ≈1.0 mΩ (estimate) |
| **Total** | | **≈8.0 mΩ, ≈8.5 mΩ warm** |

The model's 5 mΩ is about 40 % low. The assembly doc's "about 1 mΩ per tab" counted only the fingers. At 100 W the nickel makes 0.51 W, not 0.30 W.

If the strip turns out to be nickel-plated steel ("hilumin", or a fake "pure nickel"), it is 2–3 times worse: about 20 mΩ and 1.2 W at 100 W.

## 2. Candidates

All of these fit a 4S pack under 100 Wh. Prices are US hobby retail, checked 2026-10-21 ([IMR Batteries 21700 list](https://www.imrbatteries.com/collections/21700-batteries), [18650battery.com Molicel](https://18650battery.com/collections/vendors?q=Molicel)). None of these are JLC parts: cells are hand-supplied either way.

| Cell | Capacity / energy (4S pack) | AC / DC resistance | Weight | Charge / discharge rating | Price, stock | Notes |
|---|---|---|---|---|---|---|
| **EVE 58E** (today) | 5.7 Ah, 20.3 Wh (81 Wh) | ≤18 / ≈22 est. | 71 g | 5.6 A max (1C) / 16.8 A | $5.99, in stock | Cycle life: 70 % @ 500 |
| LG M58T | 5.57 Ah min, 20.0 Wh min (80 Wh) | 15 / 20 (spec) | 73.2 g max | 5 A (≤10 cycles) / 12.5 A | not at US hobby shops | Only about 15 % better; worse charge rating |
| Samsung 50S | 5.0 Ah, 18 Wh (72 Wh) | ≤14 / ≈16 est. | 72 g max | 6 A / 25 A | $6.99, in stock | −9 Wh for −27 % R: poor trade |
| Molicel P50B | 5.0 Ah, 18.0 Wh (72 Wh) | 6.5 / **12.8** typ | 71 g max | 5 A / 60 A | $9.99, in stock | [datasheet](https://www.molicel.com/wp-content/uploads/Product-Data-Sheet-of-INR-21700-P50B-80122.pdf); −9 Wh |
| EVE 50PL | 5.0 Ah (72 Wh) | ≤7 (vendor copy) / — | ≈70–72 g | — / 50–70 A | $6.99, in stock | No official DC figure found |
| **Molicel P60B** | **6.0 Ah typ / 5.85 min, 21.6 Wh (86.4 Wh)** | 6.5 / **12.8** typ | **75 g max** | **6 A std, 30 A max** / 100 A | **pre-order 2026** ([United Lithium](https://unitedlithium.us/pages/molicel-inr-21700-p60b)); expect ≈$10–12 | [datasheet](https://www.molicel.com/wp-content/uploads/Product-Data-Sheet-of-INR-21700-P60B_80145.pdf); 21.35 mm max diameter, 70.13 mm max length |
| Tenpower 60XG | 6.0 Ah, 21.6 Wh (86 Wh) | ≤5 (V0.1 draft) / — | 73–76 g | 3 A std, 16 A max / 40 A | $9.99, **sold out** | Tabless; draft spec only |
| Molicel M65A | 6.5 Ah (93.6 Wh) | 11.5 / 26–27 (prelim.) | 72.5–74.5 g | — / 26 A | $11.99, sold out | More energy at the **same** loss |

Notes on the table:
- EVE 58E values are from its datasheet sections cited above. The 22 mΩ DC figure is my estimate.
- LG M58T values are from its spec, §2.1, 2.9, 2.12 and 4.2.
- Samsung 50S values are from the [Samsung spec](https://www.dnkpower.com/wp-content/uploads/2022/07/SAMSUNG-INR21700-50S-Cell-Specification.pdf), §3 and 7.5; its 60 %-after-250-cycles figure is at 25 A, so it isn't comparable.
- **Didn't qualify:**
  - Samsung 53G and 58E: energy cells, no lower resistance.
  - EVE 50E: about 35 mΩ.
  - BAK 45D: 4.5 Ah, sold out.

## 3. Recommendation

### Cells: switch to the Molicel P60B once it can be bought from a real distributor; until then, stay on the 58E

The P60B is the only cell in the table that is both larger than the 58E and roughly half its DC resistance. The P50B has the same 12.8 mΩ, but it costs 9 Wh.

I modelled the P60B at 13 mΩ mid-charge and 19.5 mΩ near empty, with nickel at the corrected 8.5 mΩ:

| Total loss (W) | 30 W | 100 W | 100 W @ 12 V | 88 W charging |
|---|---|---|---|---|
| 58E, corrected | 2.01 | 11.58 | 23.6 | 6.71 |
| P60B | 1.82 | 9.08 | 16.2 | 5.67 |
| **Saved** | **0.19** | **2.5** | **7.5** | **1.04** |
| P60B + nickel option A (below) | 1.80 | 8.79 | 15.6 | 5.54 |
| **Saved, both** | **0.21** | **2.8** | **8.0** | **1.17** |

The saving is in the cans: 5.3 → 3.0 W of cell heat at 100 W, and 13.9 → 7.3 W near empty.

**Other gains:**
- **Energy:** +5 Wh nameplate (86.4 vs 81 Wh), still under 100 Wh. On top of that, about 2 % more of the stored energy reaches the port at 100 W.
- **Charging:** a 6 A standard charge clears the known B-4 finding. There, the 5.17–5.83 A hardware ICHG ceiling exceeds the 58E's 5.6 A maximum.

**Costs:**
- **Money:** about +$16–24 per pack.
- **Weight:** up to +16 g by datasheet maximum, likely +6–10 g in practice.
- **Board:** no board area or height change.

**Risks:**
- **Availability.** It is pre-order only, and Alibaba listings at $2–8 are probably fakes. Buy from Molicel-authorised distributors only.
- **Mechanics.** The cell is up to 0.7 mm shorter and 0.15 mm thinner:
  - That eats the 0.4 mm axial preload, so the floor spacer needs re-sizing from measured cells.
  - The cage and crush ribs need a fit check.
- **Gauge.** It needs a new BQ40Z50 ChemID, or a GPC/learning run. P0 is doing that anyway (J302).
- **Short circuit.** This is the important one. *(Corrected in the cross-examination below: the right figures are ≈200 A → 300–365 A at 16.8 V.)* My first estimate was that the pack's bolted-short current rises from about 125 A to about 185 A (4 × 13 mΩ plus about 25 mΩ of path). The AGM404AP1 pulse SOA during the BQ40Z50 SCD delay and the F101 I²t must be re-checked. That belongs to area B; it is not a reason to keep the 58E, but it must be signed off.

If the P60B can't be had, the Tenpower 60XG is the alternative (draft spec, restocks). The P50B only makes sense if 72 Wh is acceptable.

### Interconnect: series strips to 0.2 × 10 mm pure nickel, PACK tails to 0.2 mm copper

This is option A:
- **Series strips:** 0.2 × 10 mm pure nickel. That is the welder the assembly doc already calls for, and a 10 mm strip still sits inside the 21 mm + ring.
- **PACK tails:** 0.2 mm copper with a 0.15 mm nickel weld pad at the cell end. Copper also solders into the plated slots far better than nickel.
- **Result:** 8.5 → about 4.1 mΩ, worth **0.26 W at 100 W**, 0.47 W near empty and 0.14 W charging. At 30 W it saves nothing that matters (0.02 W).
- **Cost:** about $3 and under 1 g.

Option B, a full copper–nickel sandwich (0.2 mm copper under 0.15 mm nickel everywhere):
- It reaches about 2.6 mΩ, worth another **0.09 W**.
- It adds 0.15–0.2 mm per end: about +0.3 mm pack length, or less preload.
- It needs a kWeld-class welder. Forum users report 0.15 mm nickel over 0.2 mm copper at about 1.7 kA / 140 J on a modified kWeld ([esk8 thread](https://forum.esk8.news/t/kweld-spot-welder/6926?page=41)). One user found 0.3 mm nickel peeled off a basic welder.
- Not worth it for 0.09 W.

## 4. Interactions

- **B (pack path).** Lower cell resistance means a higher short-circuit current (above), and SCD/OCD thresholds in the BQ40Z50 may need re-tuning. Lower cell resistance also raises the voltage at a given charge level under load, which makes under-voltage cut-off at 100 W less likely: more runtime from the same cells.
- **Thermal model.** Cell heat drops by 2.3 W at 100 W and about 6.6 W near empty. The near-empty case should be added to the thermal sheet with corrected resistances: today's model under-states it by about 6.6 W.
- **Charger.** The P60B removes the ICHG-ceiling-over-cell-maximum finding. A higher charge current could then be allowed, but that is area-A/firmware territory.
- **Mechanical.** Spacer and cage tolerances; +0.3 mm pack length only with option B.

## 5. What to measure (there is no dev board: on P0 and on the bench)

1. **Incoming cells.**
   - AC 1 kHz resistance with a YR1035-class meter on every cell. Match each set of four to within 1 mΩ.
   - Weight and dimensions (length for the spacer).
2. **DC resistance per cell.** Read the BQ40Z50 cell voltages over SMBus during a 1 A → 8 A load step at 80 %, 50 % and 10 % charge. Calculate it from ΔV/ΔI at 1 s, 10 s and 5 min. The 5-minute value is the one that sets the heat. Repeat at 0 °C if possible.
3. **Nickel.**
   - Four-wire mΩ across each strip and tab at 5 A from a bench supply, before and after the drop and vibration tests.
   - A salt-water check of the strip to rule out plated steel.
4. **Can temperatures** with thermocouples at 100 W from 50 % charge and from 15 % charge, 58E vs P60B. This checks the corrected model directly.

## Sources

- [EVE 58E Batemo page](https://www.batemo.com/products/batemo-cell-explorer/eve-energy-inr21700-58e/)
- [LG M58T spec](https://18650baterie.pl/wp-content/uploads/2025/05/Datasheet-LG-M58T.pdf)
- [LG M50LT spec](https://evwest.com/support/21700_M50LT_datasheet.pdf)
- [Molicel M50A](https://www.rosebatteries.com/hubfs/INR21700M50A-V3-80097.pdf?hsLang=en)
- [Molicel P50B](https://www.molicel.com/wp-content/uploads/Product-Data-Sheet-of-INR-21700-P50B-80122.pdf)
- [Molicel P60B](https://www.molicel.com/wp-content/uploads/Product-Data-Sheet-of-INR-21700-P60B_80145.pdf)
- [Samsung 50S spec](https://www.dnkpower.com/wp-content/uploads/2022/07/SAMSUNG-INR21700-50S-Cell-Specification.pdf)
- [Tenpower 60XG listing](https://18650battery.com/products/tenpower-60xg-21700-6000mah-60a-battery)
- [IMR Batteries 21700 stock](https://www.imrbatteries.com/collections/21700-batteries)
- [United Lithium P60B](https://unitedlithium.us/pages/molicel-inr-21700-p60b)
- [lygte-info battery index](https://lygte-info.dk/info/batteryIndex.html)
- [kWeld forum](https://forum.esk8.news/t/kweld-spot-welder/6926?page=41)

## Cross-examination (2026-10-21, after reading A, B, C and E)

### 1. Re-checking my own P60B case

**The 12.8 mΩ DC figure has not been confirmed independently.**
- The only source is Molicel's own one-page sheet ([P60B data sheet 80145](https://www.molicel.com/wp-content/uploads/Product-Data-Sheet-of-INR-21700-P60B_80145.pdf)). Its AC 6.5 mΩ / DC 12.8 mΩ are **digit-for-digit the P50B's figures**, which looks like a template carry-over, not a new measurement.
- No Mooch, lygte-info or other bench test of the P60B exists. About:Energy has measured DC resistance against charge level and temperature, but only behind a login ([Voltt P60B](https://www.aboutenergy.io/voltt-battery-library/molicel-p60b)). Its only public result is a measured **5.86 Ah**.
- An AliExpress "review" quoting ≈3.5 mΩ is not credible.
- My estimate: the P60B's DC resistance is probably in the P50B class (≈11–15 mΩ). I would not bank the 2.5 W until it is measured.

**Availability: it can't be bought today.**
- About:Energy says the **P60B is now sold as the INR-21700-P60C**.
- IMR Batteries lists the P60C as "upcoming", and United Lithium is taking 2026 pre-orders.
- GTD, which claims Molicel authorisation, lists the P60C (6000/5850 mAh, 75 g, 6 A standard / 30 A maximum charge) with no stock or price.
- 18650battery.com, IMR and Fogstar (a UK authorised distributor) don't stock it. Neither did my earlier checks of NKON or 18650batterystore.
- **It is not buyable for P0.**

**Honest fallback: P0 keeps the 58E** ($5.99, in stock at IMR, and the pack, gauge plan and tray are already built around it). The P50B and 50PL are in stock with ≈half the resistance, but they cost 9 Wh (−11 %). That isn't worth 2.3 W for a first build.

**What to do now:**
- Fit nickel option A on P0.
- Size the cage and floor spacer to also take a 21.2–21.35 × 70.0–70.13 mm cell.
- Buy P60C cells for an A/B test once an authorised distributor ships them, and measure their resistance (§5) before committing.

### 2. The near-empty correction changes everyone's 12 V savings

**The case itself.** With 33 mΩ cells the 100 W / 12 V case draws **10.3 A, not 9.7 A**, and totals **23.6 W, not 17.0 W**.
- I read the model's 12 V as the open-circuit voltage at near-empty (3.0 V/cell). That is the reading under which its current formula (P + all losses) / V is right; B's "cell loss is over-counted in the current" is only true if 12 V is the terminal voltage.
- Under that reading, the **58E's terminal voltage at 100 W is ≈10.5 V (2.64 V/cell)**, at the BQ40Z50's cell under-voltage threshold. The 58E can't really sustain 100 W there, so E's "throttle earlier at a low pack voltage" becomes a requirement, not an option.
- The P60B would sit at ≈11.2 V.

**Effect on the other areas' 12 V savings.** I re-ran each area's main resistance change in my model copy, with the corrected nickel:

| Area change | 12 V saving, cells at 22 mΩ (as each researcher ran it) | 12 V saving, corrected 58E (33 mΩ) | 12 V saving, P60B (19.5 mΩ) |
|---|---|---|---|
| C: F102 2.5 mΩ + XRS120N04D | 1.10 W | **1.34 W** | 1.06 W |
| A: FET 13 → 9.5 mΩ (≈ R1, 9 V drive) | 0.88 | **1.07** | 0.85 |
| B: inductor DCR 15 → 8.8 mΩ (XGL7030, DCR part only) | 0.41 | **0.50** | 0.39 |
| E: PPHV 18 → 8 mΩ (USB side) | 0.34 | **0.38** | 0.33 |

**Rule of thumb:**
- With the 58E kept, multiply every pack-side 12 V saving by **≈1.22**. That is (10.3/9.7)², plus each watt saved also cutting cell I²R by ≈0.23 W. USB-side savings scale by ≈1.12.
- With the P60B, the factor is ≈0.97: the original numbers stand.
- The savings at 30 W, 100 W nominal and 88 W charging are unchanged, because the cells sit mid-charge there.

### 3. C's protection FETs and fuse against the real short-circuit current

My own "185 A" was wrong in both directions: it used DC resistance and 14.4 V. A short is cleared in tens to hundreds of µs, so the cells' **ohmic (≈1 kHz AC) resistance** sets the current, at up to **16.8 V**:

| | Cells, 4 × AC | Rest of loop: FETs, fuse, shunt, nickel, copper, plus the short itself | Prospective current at 16.8 V |
|---|---|---|---|
| 58E | 56–72 mΩ | ≈20 mΩ | **≈180–220 A**. This agrees with review 2's ≈185 A and C's 195–200 A |
| P60B | ≈26 mΩ | ≈20–30 mΩ | **≈300–365 A** |

**C's XRS120N04D, by C's own reading of its Fig. 10:**
- The 100 µs line allows about 210 A at ≈1 V.
- At 365 A × 2.6 mΩ (hot) ≈ 0.95 V, each FET dissipates ≈340 W.
- That is **outside its 100 µs SOA** with the P60B. With the 58E (≈200 A, ≈0.5 V, ≈100 W) it is fine, as C says.

**SCD timing.** C's "SCD delay ≤ ~120 µs" rule is too loose for low-resistance cells. bq40z50-r2 §7.32 gives:
- SCD2 delay 0–458 µs in 30.5 µs steps;
- tDETECT up to 160 µs near the threshold, much faster with large overdrive;
- SCD2 threshold 44–200 mV over the 1 mΩ RS101, i.e. 44–200 A (§7.31).

**What changes with the P60B:**
- SCD2 at ≈100–120 A with **0–30 µs delay**.
- **BSZ018N04LS6** for Q101/Q102 rather than the XRS. It has a 633 A pulse rating and 1.8 mΩ maximum; its datasheet SOA still needs checking at ≈0.7 V / 100 µs.
- Hard-short tests on P0 with a current probe.

**F102 fuse:** its interrupt rating is **50 A**, which is below even the 58E's ≈200 A. As C notes, the FETs are the only thing that clears a hard short. The P60B makes that 1.5–1.8× worse.

**RS101 shunt** (1206, 1 W) takes ≈130 W for ≈100 µs (≈13 mJ). Check its pulse curve if the P60B goes ahead.

### 4. The other four reports: the most serious flaw or unverified claim in each

**A (charger FETs).**
- **Double count with E.** A's R1 (9 V DRV_SUP from an LDO, −0.43 W at 100 W) and E's item 3 (9 V DRV_SUP from a buck, −0.45 W) are **the same saving**. Count it once.
- **REGN gating.** A's "REGN exists only while the converter is enabled" is confirmed by bq25756 §6.3.3.2: REGN is on only with VAC OK and charge enabled, or with EN_REV = 1. But E's question remains open: does the one-shot ADC also raise REGN? If it does, the LDO is on while the converter is off, against TI's "must be disabled" rule. Measure it on P0.
- **The R2 penalty is likely under-stated.** A puts it at +0.18 W at 30 W; B estimates ≈0.3 W from BSZ018's Qrr (55 nC) and Coss (690 pF).
- **Stock conflict.** BSZ018N04LS6 (202 at JLC) is now wanted by both A (2 per board) and C/D (2 per board).
- I agree with R1. R2 is optional.

**B (frequency and inductor).**
- **XGL7030-222 saturation.** I_sat is 9.7 A at −20 % and 14.5 A at −30 %. B's own corner peak is 15.9 A, and at 100 W from 12 V the peak is ≈12 A. So the XGL runs past −30 % at the corner. "Same 1.6 µH as today at 13 A" needs Coilcraft's L-vs-I curve; it isn't shown. The BQ25756 has no cycle-by-cycle limit, as B notes.
- **Core loss.** The "half the APS0730 core loss" figure is assumed.
- I agree with R1 only if the XGL7030-332 (2.2 µH at 13 A) is the default, or the -222's curve is checked. The 500 kHz trial on P0 is fine.

**C (pack path).**
- **Short circuit (above).** C's analysis used a ≈90 mΩ DC loop. That is valid for the 58E, but fails with low-resistance cells.
- **XRS datasheet quality.** C admits it: a generic SOA drawing and blank cells. The SOA is the very curve the short-circuit case relies on.
- I agree with the XRS **for the 58E**. With the P60B: BSZ018N04LS6 plus a fast SCD2.
- C's fuse correction (5 → 2.5 mΩ, F101 deleted) is right and matters to everyone's baseline.

**E (USB side, fixed losses).**
- **EN_PFM in reverse mode.** E's 0.3–0.45 W idle-port saving is the least verified claim. TI publishes no reverse-mode PFM data, and VBUS ripple and load-step undershoot against PD vSrcValid could fail.
- **TPS25751S.** The external-path variant is unconfirmed for source mode with the BQ25756 (E says so).
- **DRV_SUP overlaps with A** (above).
- E's "30 W at 9 V 3.3 A isn't a legal PDO" is correct: the model's 30 W point is really 27 W, or 15 V 2 A.
- E's 5 V-path loss (≈1.3–1.6 W at 15 W) is a real gap in everyone's model.

### Revised recommendation (D)

| Change | 30 W | 100 W | 100 W @ 12 V | 88 W charging | Status |
|---|---|---|---|---|---|
| **P0:** keep 58E; nickel option A (0.2 × 10 mm Ni strips, 0.2 mm Cu PACK tails) | 0.02 | **0.26** | 0.47 | 0.14 | Do it. ≈$3, <1 g |
| P0: cage/spacer tolerant of P60C dimensions; firmware throttle at low pack voltage (needed with the 58E) | — | — | — | — | Do it |
| **Later:** P60C (ex-P60B), only with measured resistance, BSZ018N04LS6 in Q101/Q102 and SCD2 ≤ 30 µs | 0.19 | **2.5** | **7.5** | 1.0 | When an authorised distributor ships; +$16–24, +6–16 g |

**Model correction for everyone:** cells 22 mΩ mid-charge / 33 mΩ near empty; nickel 8.5 mΩ. The baseline at 100 W from 12 V is **23.6 W, not 17.0**.
