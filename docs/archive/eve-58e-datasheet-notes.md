# EVE INR21700-58E — Datasheet Notes

> **Archived 2026-10-24.** The EVE INR21700-58E was dropped on 2026-10-21 for the FEB 21700G, which was itself replaced by the BAK N21700CX-65E on 2026-10-23. The current cell is in [`docs/spec.md`](../spec.md) (Cells and pack). Kept for the history of the cell choice.

**Source:** EVE Energy product specification PBRI-INR21700/58E-D06-01, Version B (2025-03-11)
**Download (PDF, 874 kB):** https://www.nkon.nl/en/amfile/file/download/file/806/product/5882/
(Linked from NKON's product page: https://www.nkon.nl/en/eve-inr21700-58e-5700mah-16-8a.html)

## Key specs
| Item | Value |
|---|---|
| Capacity | 5600 mAh min, 5700 mAh nominal (0.2C, 2.50 V cut-off) |
| Nominal voltage | 3.60 V |
| Charge voltage | 4.20 ± 0.05 V, CCCV, 0.112 A cut-off |
| Standard charge | 1.12 A (0.2C) |
| Max charge | 5.6 A (1C), not for cycle life |
| Standard discharge | 1.12 A (0.2C) to 2.50 V |
| Max discharge | 16.8 A (3C) to 2.50 V, not for cycle life |
| Voltage range | 2.50–4.20 V |
| Initial impedance | ≤ 18 mΩ (AC 1 kHz) |
| Weight | 71.0 ± 2.0 g |
| Dimensions | 70.80 ± 0.20 mm tall, 21.50 ± 0.20 mm diameter (with sleeve) |
| Charge temp (ambient) | 0 to 45 °C |
| Discharge temp (ambient) | -20 to 60 °C |
| Cell surface limits | Charge 0–60 °C (release < 45 °C); discharge -20–70 °C (release < 60 °C) |
| Rate capability | ≥ 97% @ 0.5C, ≥ 95% @ 1C, ≥ 93% @ 2C, ≥ 90% @ 3C |
| Cold capacity | ≥ 70% at -20 °C, ≥ 95% at 55 °C |
| Cycle life | ≥ 70% after 500 cycles (0.5C charge / 1C discharge to 3.0 V) |
| Shipped at | 3.40–3.60 V |
| Long-term storage | Cycle once every 3+ months, store at 3.45–3.60 V, 0–25 °C, dry |

## Energy
- Per cell: 20.5 Wh nominal (20.2 Wh at min capacity)
- 4S pack: **82.1 Wh nominal** (80.6 Wh min) — label the pack 82 Wh; under the 100 Wh carry-on limit
- ≈ 289 Wh/kg

## Design implications for Monolith
- **Cell spacing / cavity:** EVE recommends > 1 mm between cells. Max diameter 21.7 mm → 2x2 inner cavity ≈ 44.5–45 mm (not 42.5 mm).
- **Cold charging:** set BQ40Z50 to inhibit charging below 0 °C.
- **Thermistor:** place at mid-cell, 30–34 mm up from the bottom.
- **Sleep current:** pack draw should stay under 10 µA in sleep (BQ40Z50 + STM32WB budget).
- **Charge rate:** target ~0.5C (≈ 2.8 A at pack voltage) for cycle life; 1C max.
- **Matched cells:** don't mix makers or types; order all four together.
- **Connections:** EVE says to weld strip to the cell, never solder directly to the cell.
- **Shock:** EVE recommends shock absorption around cells in the pack.

## Compared with Samsung INR21700-58E (CC5493F101)
Samsung: 5330 mAh min (≈ 5490 typical), 3.64 V nominal, 10.7 A continuous, 74 g max, 21.78 × 71 mm max, discharge -10 to 60 °C, ≥ 80% after 500 cycles. ≈ 19.4–20.0 Wh/cell, ≈ 78–80 Wh for 4S.
**Decision (2026-10-10):** stay with EVE — more Wh, lighter, slimmer, better cold discharge. Samsung's better cycle-life spec isn't worth the trade for a hiking pack.
