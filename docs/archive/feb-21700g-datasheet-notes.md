# FEB 21700G (68E) 6500 mAh: cell notes

> **Archived 2026-10-24.** The FEB 21700G was the pack's cell from 2026-10-21 to 2026-10-23, when the BAK N21700CX-65E replaced it. The current cell and its limits are in [`docs/spec.md`](../spec.md) (Cells and pack). Firmware still uses the charge ramp from this table until BAK sends its temperature-stepped profile.

**The pack's cell since 2026-10-21**, replacing the EVE INR21700-58E (see [`eve-58e-datasheet-notes.md`](eve-58e-datasheet-notes.md) for the old cell). Chosen for energy: the bank lives at trail loads (phones, tablets, headlamps), and 100 W is only for brief bursts. The comparison against the 58E and the Tenpower 60XG is in `research_notes/Loss reduction/G_feb_21700g.md`.

Source: the [diy500amp listing](https://diy500amp.com/products/feb-21700-battery-cell-6500mah-13a-ultra-high-capacity-energy-cell?variant=42624877330503), which quotes the maker's data sheet; dimensions also from [Batemo](https://www.batemo.com/ja/wp-json/wp/v2/product/136335). No independent test is public yet (Mooch has a Patreon-only update on the "FEB 21700G (68E)"; the listing links BatteryRealData lab tests). Confirm against the maker's sheet before P0.

## Ratings
| | Value |
|---|---|
| Capacity | 6500 mAh nominal, 6350 mAh minimum |
| Nominal voltage / energy | 3.6 V / 23.4 Wh per cell |
| Pack (4S1P) | 14.4 V, 6.5 Ah, **93.6 Wh** (91.4 Wh minimum): under the 100 Wh carry-on limit |
| Charge voltage | 4.20 V |
| Standard charge | 3.25 A (0.5C) |
| Maximum charge | **4.55 A at 15–45 °C**; 3.25 A at 5–15 °C; 0.65 A at 0–5 °C; none below 0 °C or above 45 °C |
| Maximum continuous discharge | **13 A at 0–35 °C**; 6.5 A at −20–0 °C and 35–45 °C; 3.25 A at 45–60 °C; none above 60 °C (the listing says "not a recommended long-term pack current") |
| Discharge cut-off | 2.5 V (the cycle-life test uses 2.75 V; we use ≥ 2.8 V) |
| Internal resistance | ≤ 25 mΩ initial (method not stated; almost certainly AC 1 kHz). Our DC estimate: ~30 mΩ mid-charge, ~50 mΩ near empty |
| Cycle life | 500 cycles to ≥ 70 % at 3.25 A charge / 6.5 A discharge, 4.20–2.75 V |
| Temperature (ambient) | charge 0–45 °C, discharge −20–60 °C, both with the current derating above |
| Dimensions | 21.65 ± 0.2 × 70.95 ± 0.2 mm (Batemo: 21.7 × 71.1) |
| Mass | 75 g (Batemo: 73.4 g) |
| Protection | none (bare industrial cell) |
| Price | $7.49 (diy500amp, 2026-10-21) |

## What it means for the design
- **Mechanical** (`hardware/mechanical/monolith_shell.py` for the cells, board and slots; `monolith_cup.py` for the enclosure): designed to 21.85 mm diameter and 71.1 mm length. Cell pitch 23.25 mm (was 22.9); same board outline. The five bottom slots move 0.30 mm on the board. The cup with these cells: 59.8 × 51.9 × 97.2 mm, about 384 g.
- **Charger:** R413/R513 (ICHG) 9.1 k → 11.8 k: hardware ceiling 4.07–4.45 A, under 4.55 A.
- **Gauge:** design capacity 6,500 mAh; temperature ranges and protections per `docs/firmware/charge-and-thermal-policy.md`; a new chemistry ID (likely a GPCCHEM run).
- **Firmware:** charge current follows a linear ramp on the hottest cell inside the table above; discharge keeps the 100 W offer but starts a linear derate at ~33 °C down to ~40 W (`docs/firmware/charge-and-thermal-policy.md`).
- **Heat:** about 12 W at 100 W out (vs ~10 W with the 58E): the cells' resistance is the largest term. At 30 W, nothing derates: ~3 h full to empty.
- **Short circuit:** ~150–170 A available (lower than the 58E's ~200 A), so the protection FETs and F102 have more margin.
- **The table's temperature:** the listing gives it against ambient; we apply it to the hottest cell until FEB confirms which.
