# FEB 21700G: charge cap and temperature derating plan (2026-10-21)

The owner chose energy over bursts and leans toward the FEB 21700G (6.5 Ah, 93.6 Wh pack; see `G_feb_21700g.md`). This is the plan for keeping the pack inside the cell's limits. Model and sheet: `research_notes/Ground-up mechanical concepts/model/feb_limits.py` / `feb_limits.png`. Simulated numbers are estimates.

## The cell's limits ([diy500amp listing](https://diy500amp.com/products/feb-21700-battery-cell-6500mah-13a-ultra-high-capacity-energy-cell?variant=42624877330503))
| | below 0 °C | 0–5 °C | 5–15 °C | 15–35 °C | 35–45 °C | 45–60 °C | above 60 °C |
|---|---|---|---|---|---|---|---|
| Charge | none | 0.65 A | 3.25 A | 4.55 A | 4.55 A | none | none |
| Discharge | 6.5 A (to −20 °C) | 13 A | 13 A | 13 A | 6.5 A | 3.25 A | none |

The listing gives these against **ambient** temperature. The pack has no ambient sensor, so the plan applies them to the **hottest cell** (conservative), and the open question below decides whether that can be relaxed.

## The ramps (linear, never above the table)
- **Charge** (pack current): 0 A at ≤ 0 °C → 0.65 A by 1 °C; 0.65 → 3.25 A over 5.0–6.5 °C; 3.25 → 4.55 A over 15.0–16.5 °C; 4.55 A to 40 °C; linear to 0 A at 45 °C.
- **Discharge** (battery current): 0 at −20 °C → 6.5 A by −19 °C; 6.5 → 13 A over 0–1.5 °C; 13 A to 33 °C; 13 → 6.5 A over 33–35 °C; 6.5 A to 43 °C; 6.5 → 3.25 A over 43–45 °C; 3.25 A to 55 °C; linear to 0 at 60 °C.
- **Board** ramp unchanged: full at 60 °C → zero at 75 °C board copper.

## Where each limit lives
**Hardware (works with no firmware):**
1. **R_ICHG (R4xx/R5xx on ICHG) 9.1 kΩ → 11.5 kΩ 1 %** *(applied as 11.8 kΩ, LCSC C93752: 11.5 kΩ isn't confirmed at LCSC; ceiling 4.07–4.45 A)*. The BQ25756 pin ceiling becomes 48–52 A·kΩ / 11.5 kΩ = 4.17–4.52 A (bq25756 §5.5; RBAT 5 mΩ), under the 4.55 A maximum even if the configuration never loads. Today's 9.1 kΩ allows up to 5.83 A.
2. **IBAT_REV = 10 A** in each TPS25751 bundle (already planned): under the 13 A maximum.
3. **BQ40Z50 protections:** OTC 45 °C and UTC 0 °C (open CHG); OTD 60 °C (opens DSG); OCD1 ≈ 12 A / OCD2 ≈ 14 A; CUV at the chosen discharge floor. The cell sensors must be on the **front cells** (the pair the board heats in the cup), or the hottest cells are never seen.

**Gauge charge algorithm (BQ40Z50 temperature ranges):** T1 0 / T2 5 / T3 15 / T4 40 / T5 45 °C; charging current 650 / 3250 / 4550 / (High Temp range) 2275 mA; charging voltage 4.20 V (optionally 4.10–4.15 V in the High Temp range). The gauge's ChargingCurrent() is then a coarse version of the ramp.

**Firmware, once a second (it already polls the gauge and each charger's TS_ADC; mcu-io-power-states.md):**
- **Charge:** ICHG_REG = min(gauge ChargingCurrent(), charge ramp at the hottest cell, 4.55 A). With both ports sinking, split it so the sum stays under the ramp.
- **Discharge:** the allowed output power P = min(discharge ramp × pack voltage × ~0.9, board ramp × asked). Apply it by re-advertising Source Capabilities (PDO current = P / contract voltage) in ~5 W steps with ~2 K hysteresis, so sinks renegotiate instead of the output sagging; share P across both ports. Keep the low-pack-voltage PDO limit.
- **Order on the way down:** lower the PDOs first, then IBAT_REV is only a backstop; the gauge's OTD/OCD are the last resort.

## What it does (cup + P0 build)
| | 25 °C ambient | 35 °C ambient |
|---|---|---|
| 30 W, full to empty | 2.97 h, no derate, cells 38 °C | 2.97 h, no derate, cells 48 °C |
| 100 W asked, table read by cell temperature | 4.9 min at 100 W, 25 Wh in 20 min, then ~45–50 W | ~85 W at once, 20 Wh in 20 min, then ~45 W |
| 100 W asked, table read by ambient | 10.3 min at 100 W, 28 Wh in 20 min, then ~50–55 W | 22 Wh in 20 min |
| Charging, 88 W offered | 2.0 h (cells sit at the 40–45 °C ramp) | |
| Charging at 10 °C / 3 °C ambient | 1.5 h / 1.8 h (board heat warms the cells into the 4.55 A band) | |

Total energy delivered at 100 W asked: ~87 Wh either way.

## Open questions
1. **Ambient or cell temperature?** Ask the seller/FEB which the derating table means, or read Mooch's / BatteryRealData's test. If it's ambient, firmware can estimate ambient from the back cells at idle and run the gentler column; 100 W bursts double from ~5 to ~10 min.
2. **Cell resistance:** 30 mΩ DC at mid charge is my estimate from the ≤ 25 mΩ spec. A 10 s step test at a few charge levels on P0 sets the real curve.
3. **Warm charging is the slowest case** (2 h at 25 °C) because the cup couples board heat into the cells. A lower charge input (e.g. 60 W PDO request) may finish as fast with less heat; worth a quick model run.
4. **Gauge chemistry ID** for the FEB (likely needs a GPC run), and the discharge floor (spec 2.5 V; the cycle test used 2.75 V).
5. **Fit:** up to 21.85 × 71.15 mm: cell pitch, cup bore, frame windows and webs need ~0.4 mm more.
