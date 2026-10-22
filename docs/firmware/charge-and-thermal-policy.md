# Charge and thermal policy (firmware notes)

Decided 2026-10-21: the pack uses **FEB 21700G (68E) 6500 mAh** cells, 4S1P, 14.4 V nominal, **93.6 Wh**. The goal is energy for trail loads (phones, tablets, headlamps, a watch); 100 W is for brief bursts only. These notes are the design intent for firmware; numbers come from lumped thermal models in `research_notes/Ground-up mechanical concepts/model/` (`feb_limits.py`, `thermal_rundown.py`) and must be re-tuned on P0.

Background: `research_notes/Loss reduction/G_feb_21700g.md` (why this cell), `H_feb_limits_plan.md` (where each limit lives), `summary.md` (loss cuts and the DRV_SUP enable).

## 1. The cell's limits
From the [diy500amp listing](https://diy500amp.com/products/feb-21700-battery-cell-6500mah-13a-ultra-high-capacity-energy-cell?variant=42624877330503) (read against the hottest cell, which is conservative: the listing says ambient):

| | < 0 °C | 0–5 °C | 5–15 °C | 15–35 °C | 35–45 °C | 45–60 °C | > 60 °C |
|---|---|---|---|---|---|---|---|
| Charge, max | none | 0.65 A | 3.25 A | 4.55 A | 4.55 A | none | none |
| Discharge, max | 6.5 A (to −20 °C) | 13 A | 13 A | 13 A | 6.5 A | 3.25 A | none |

Charge to 4.20 V. Discharge floor: the spec says 2.5 V, its cycle test used 2.75 V; use **≥ 2.8 V per cell** for life. Resistance ≤ 25 mΩ (spec); about 30 mΩ DC mid-charge and about 50 mΩ near empty (estimate), so heat rises sharply late in a discharge.

## 2. Principles
- **Linear ramps, not steps.** Every limit is a straight line from full to reduced across a temperature band, so power never jumps and the pack doesn't oscillate.
- **Ramps stay on or under the cell's table at every temperature.**
- **Act on the hottest sensor.** In the cup design the board heats the two *front* cells; those are the hottest. Cell sensors must be on the front cells.
- **Layers:** hardware ceilings (no firmware) → gauge protections and charge algorithm → this firmware policy. Firmware is the smoothest and lowest layer; the others are backstops.
- **Lower the PD offer, don't sag the output.** Discharge limits are applied by re-advertising Source Capabilities so sinks renegotiate cleanly.

## 3. Charging
**Current vs hottest cell (pack current):**

| Hottest cell | Charge current |
|---|---|
| ≤ 0 °C | 0 (gauge UTC also blocks) |
| 1–4.9 °C | 0.65 A |
| 5.0 → 6.5 °C | ramp 0.65 → 3.25 A |
| 6.5–15 °C | 3.25 A |
| 15.0 → 16.5 °C | ramp 3.25 → 4.55 A |
| 16.5–40 °C | 4.55 A |
| 40 → 45 °C | ramp 4.55 → 0 A (gauge OTC at 45 °C) |

**Loop (once a second):** `ICHG_REG = min(gauge ChargingCurrent(), ramp(hottest cell), 4.55 A)`, written to each BQ25756 through its TPS25751 (`I2Cr/I2Cw`). With both ports sinking, split it so the sum stays under the ramp.

**Backstops:** R_ICHG 11.5 kΩ (pin ceiling 4.17–4.52 A even if nothing is configured); gauge temperature ranges T1 0 / T2 5 / T3 15 / T4 40 / T5 45 °C with 650 / 3250 / 4550 / 2275 mA; gauge OTC 45 °C, UTC 0 °C. BQ25756 JEITA stays **off** (its NTC is on the FET copper, not the cells).

**What to expect (model, 88 W offered, empty to full):** ~2.0 h at 25 °C ambient (the board's heat holds the front cells in the 40–45 °C ramp), ~1.5 h at 10 °C, ~1.8 h at 3 °C.
- **Self-warming in the cold:** the board's heat warms cold cells up through the 0.65 A and 3.25 A bands into the 4.55 A band within tens of minutes. Don't fight it.
- **To explore on P0:** when warm, asking for less input (e.g. a 60 W PDO) may finish as fast with less heat, because the cells stay below the 40 °C ramp.
- **Optional user setting:** a "longevity" charge to 4.10 V (about −10 % capacity, noticeably longer cycle life).

## 4. Discharge: burst, then a sustainable level
The owner's approach: **don't cap the offer below 100 W; lower where the derate starts instead.** The model supports it, with one refinement: **two numbers matter.**
- **Where the ramp starts** sets how long a burst lasts.
- **Where the ramp ends (the sustain power)** sets how warm the cells sit for the rest of the discharge.

**Starting policy (tune on P0):**
| Hottest cell | Allowed output |
|---|---|
| ≤ 33 °C | 100 W (full offer) |
| 33 → 39 °C | ramp 100 → 40 W |
| 39–45 °C | 40 W, and never above the FEB table (6.5 A above ~35 °C, ≈ 85 W at 14.4 V) |
| 45 → 55 °C | the FEB table falls to 3.25 A (≈ 40 W); generic ramp to 0 at 55 °C |
| ≥ 60 °C | 0 (gauge OTD) |

Plus the **board ramp**, lowered to **55 → 70 °C** board copper (from 60 → 75), and the low-pack-voltage limit (less power as the pack empties: the cells' resistance rises ~1.6× near empty).

**What it does (model, 100 W asked, from full):**
| Policy | Full power at 25 °C | at 10 °C | Hottest cell at 25 °C |
|---|---|---|---|
| FEB table only | ~5 min | ~13 min | 46 °C |
| Ramp from 33 °C to 40 W (recommended start) | ~4 min | ~12 min | 45 °C |
| Ramp from 30 °C to 35 W | ~3 min | ~10.5 min | 42 °C |

At 35 °C ambient the cells start inside the ramp, so there is no full-power burst: that's intended. At 30 W (typical trail use) nothing derates in any of these: 2.97 h full to empty, cells ≤ 38 °C at 25 °C.

**Implementation:**
- `P_allow = min(100 W, comfort_ramp(hottest cell), FEB_table(hottest cell) × V_pack × 0.9, board_ramp(board TS), low_voltage_limit(V_pack))`.
- Re-advertise Source Caps when `P_allow` crosses a 5 W step; go **down** at once, go **up** only after 2 K of cooling and ≥ 10 s (hysteresis, so a laptop isn't renegotiated every second).
- Two ports share `P_allow`; the port with the higher contract gives way first.
- Hardware backstops: IBAT_REV 10 A; gauge OCD1 ≈ 12 A, OTD 60 °C.

## 5. Sensors and timing
- Inputs: gauge cell temperatures (front cells; BQ40Z50 TS / TMP1075), gauge die (protection FETs), each charger's TS_ADC (FET copper), pack voltage.
- Poll once a second (already planned in `docs/devboard/mcu-io-power-states.md`). The board reacts in ~1 min, the cells in ~5–10 min, so 1 s is plenty.
- Don't poll a charger's ADC while its converter is off (it powers REGN and with it the DRV_SUP LDO enable: see `research_notes/Loss reduction/summary.md`).

## 6. Open items
1. **Ambient vs cell temperature** for the FEB table: ask FEB/the seller or read Mooch / BatteryRealData. If ambient, estimate ambient from the back cells at idle and relax the 35 °C step; bursts at 25 °C roughly double.
2. **Measure the FEB resistance curve** on P0 (10 s step at several charge levels) and re-fit the models.
3. **Gauge chemistry ID** for the FEB (likely a GPC characterization run).
4. **Tune the start temperature and sustain power** on P0 with real loads; the numbers above are a starting point.
