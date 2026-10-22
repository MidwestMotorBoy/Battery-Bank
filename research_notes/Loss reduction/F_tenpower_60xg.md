# Tenpower 60XG instead of the EVE 58E (2026-10-21)

Question from the owner: what if the pack used Tenpower INR21700-60XG cells? Estimates, not measurements.

## The cell
| | EVE INR21700-58E (today) | Tenpower INR21700-60XG |
|---|---|---|
| Capacity | 5.6–5.8 Ah | 6.0 Ah nominal, 5.9 Ah min (draft datasheet V0.1, Dec 2025) |
| Pack energy (4S, 3.6 V) | 82 Wh | **86.4 Wh** (still < 100 Wh) |
| AC 1 kHz resistance | ≤ 18 mΩ (datasheet §7.4) | **≤ 5 mΩ** (draft datasheet); retailers claim < 3 mΩ |
| DC resistance (my estimate) | ~21 mΩ mid, ~33 near empty | ~8 mΩ mid (range 6–11), ~13 near empty |
| Construction | tabbed energy cell, NMC | full-tab (tabless) power cell, NCA |
| Discharge rating | ~11 A | 40 A continuous (Mooch-tested, per cellsaviors), 60 A with a 75 °C cut-off, 160 A 3 s pulse |
| Standard / test charge | | 0.5C (3 A) standard; the cycle test charges at 6 A (1C) |
| Cycle life (spec) | | ≥ 60 % after 500 cycles at 6 A charge / 40 A discharge (a harsh test) |
| Size | 21.5 × 70.8 mm | ≤ 21.5 × ≤ 70.5 mm (fits; ~0.3 mm shorter) |
| Mass | ~71 g | 72–76 g (+4 to +20 g per pack) |
| Price / availability | | ~$10 a cell (IMR, sold out at the time of writing); also listed by NKON, 18650batterystore, flashlightgo |

Sources: [IMR Batteries listing](https://imrbatteries.com/products/tenpower-60xg-21700-6000mah-60a-battery), [cellsaviors database](https://cellsaviors.com/cell-database/tenpower-60xg), Tenpower draft datasheet V0.1 hosted by [NKON](https://www.nkon.nl/fr/amfile/file/download/file/1843/product/6073/) and [a reseller](https://www.lithiumlifepo4-battery.com/photo/lithiumlifepo4-battery/document/103029/TENPOWER%C2%A0PRODUCT%C2%A0SPECIFICATION%C2%A0INR21700-60XG%C2%A0%C2%A0V0.1%C2%A0251209(1)(1)(1).pdf), [About:Energy library](https://www.aboutenergy.io/voltt-battery-library/tenpower-60xg). Mooch has a preliminary 60XG test on Patreon (not read here).

## Thermal result (thermal_rundown.py, cup with webs, 25 °C)
| | 58E, cup + P0 cuts | **60XG, cup + P0 cuts** (8 mΩ) | 60XG pessimistic (11 mΩ) |
|---|---|---|---|
| Heat at 100 W, mid charge | 9.6 W | **6.3 W** | 7.0 W |
| Heat at 100 W, near empty | 14.5 W | **8.1 W** | 9.5 W |
| 100 W from full: minutes at full power | 12.6 | **19.1** | 17.0 |
| Energy in the first 20 min | 30.2 Wh | **33.3 Wh** | 32.8 Wh |
| 100 W from 25 %: minutes at full power | 7.6 | **11.8** | 10.5 |
| 88 W charge, empty to full | 94 min | **82 min** | 86 min |
| 30 W, full to empty | 2.6 h, cells 36 °C | 2.8 h, cells 34 °C | 2.8 h |
| Energy delivered at 100 W asked | 76.5 Wh | 82.0 Wh | 81.6 Wh |

The cup with 60XG cells charges faster than today's tray with 58Es (78–84 min), which removes the cup's main thermal cost.

## The catch: short circuit
Bolted-short current at 16.8 V over the 0.1–1 ms trip window, using AC cell resistance:
| | Today's pack path | With the P0 cuts |
|---|---|---|
| 58E | 170–200 A | 190–230 A |
| 60XG | 355–425 A | **460–590 A** |

- The AGM404AP1 (today) and the XRS120N04D (C50314144) aren't safe there: area C put the XRS outside its SOA already at ~300–365 A.
- Needs the Infineon BSZ018N04LS6 (1.6/1.8 mΩ, IDpulse 633 A, EAS 189 mJ; C534643, 202 at JLC, ~$1.10) on the same footprint, or 5 × 6 mm parts, plus the BQ40Z50's shortest SCD delay (area C/D: ≤ ~30 µs). Turn-off energy at ~550 A with a ~13 µs Miller plateau is tens of mJ per FET: inside the EAS rating but with little margin. Needs a controlled short test on P0.
- F102 (TLC WSFB1514) can only interrupt 50 A, so it can't clear a short if a protection FET fails shorted. With ~500 A available, pick a fuse with a much higher breaking capacity.

## Other changes it brings
- Gauge: NCA, not the 58E's chemistry. The BQ40Z50 needs a matching chemistry ID; Tenpower is unlikely to be in TI's database, so expect a GPC characterization run.
- Labels and README: 86.4 Wh, 6.0 Ah.
- The cell frame and floor spacer: re-fit for ≤ 70.5 mm (shorter is fine with the pad preload).
- Cycle life at our gentle rates (≤ 1C) is probably fine but unproven; power cells usually trade some cycle life for rate.
- It's a 2026 cell with only a draft datasheet; buy from an authorised distributor.

## Verdict
Thermally it's the single best change found: it beats all four P0 board cuts combined, and makes 100 W bursts and fast charging comfortable in the cup. Adopt it only together with the short-circuit work (BSZ018N04LS6 FETs, shortest SCD delay, a higher-breaking-capacity fuse, a P0 short test) and a gauge chemistry characterization.
