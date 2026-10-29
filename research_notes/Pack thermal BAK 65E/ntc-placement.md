# Front-cell NTC placement and the retuned derate (2026-10-24)

The 10-23 model found that a cell NTC at mid-length, facing the pack centre, reads up to 8.5 K below the hottest point of the front cell's can: the stripe that faces the board over the gap filler. This note finds a better spot for the two front-cell NTCs (C1 on TS1, C4 on TS4) on the current board and carrier, and retunes the firmware and gauge thresholds for it. Code: `ntc.py` (with small additions to `pack3d.py`); numbers: `renders/ntc.json`. Same assumptions as the README: 25 °C ambient, still air, 14 mΩ cells, P0 parts, stage positions assumed.

## 1. Where the NTC should go

Each front cell's can was sampled at 80 spots (8 angles round from the board-facing line × 10 heights) through the 100 W, 60 W, charge and pass-through cases. The table gives how far each spot reads below the hottest point of the same can, worst moment of the run (C4, the cell under the USB1 stage; C1 reads about half of these).

| Spot on C4 | 100 W | 60 W | Charge | Pass-through |
| --- | --- | --- | --- | --- |
| Mid-length, facing the pack centre (10-23 assumption) | 8.5 K | 4.0 K | 4.5 K | 9.5 K |
| Board-facing line, z 56 (just above the filler, the 10-23 suggestion) | 5.1 K | 2.5 K | 2.8 K | 5.7 K |
| Board-facing line, z 54.5 | 4.2 K | 2.0 K | 2.3 K | 4.7 K |
| **7° outboard of the line, z 50** | **0.9 K** | **0.5 K** | **0.6 K** | **1.0 K** |
| 7° outboard, z 40 | 0.7 K | 0.2 K | 0.3 K | 0.7 K |
| 15° outboard, z 50 | 3.3 K | 1.6 K | 1.8 K | 3.7 K |
| 25° outboard, z 50 | 5.4 K | 2.5 K | 2.9 K | 6.0 K |

The hot stripe is narrow and it ends where the filler ends (z 53). Just above the filler the can is already 4–6 K cooler, so "above the filler" only recovers about a third of the error. The spot that reads the stripe is **inside the filler zone, on the stripe**: within about 7° (1.3 mm) of the board-facing line and anywhere from z 40 to 50.

**Chosen spot:** 7° outboard of the board-facing line (|y| = 12.9 mm), z = 48 mm (shell frame). With the NTC there the model's hottest NTC reads 0.2–0.3 K under the hottest can point in every case.

Why 7° outboard and z 48:
- Outboard of the line, the leads can leave upward beside the carrier rail (the rail and its B.Cu keep-out cover |y| 6.5–11.3 from z 55 up), not through it.
- At z 48 the bead is 5 mm inside the top of the filler zone, so the leads get out of the gel quickly.
- The gap from can to B.Cu there is about 2.9 mm, so a bead up to 2.0 mm across fits with tape under and over it.

**What the model can't see:** the NTC bead itself. Gel over a bead couples it to the board copper above, which runs hotter than the can. A 1-D estimate (epoxy bead, Kapton, 1.2 mm of gel to the board) puts that bias at +2–4 K, reading high. High is the safe side but costs burst time, so cover the bead with a small closed-cell silicone foam cap (about 4 × 5 mm, 1.5 mm thick) before the gel goes on. The leads also conduct board heat into the bead: run them along the can, taped down, for at least 10 mm before they cross to the board.

## 2. Fitting it to the board and carrier

Shell frame to KiCad: KiCad x = 100 + y, KiCad y = 141.47 − z (from the PACK holes and the gap-filler keep-outs on the `Production` board).

| | C4 (TS4, J107) | C1 (TS1, J102) |
| --- | --- | --- |
| Bead centre under the board | KiCad (112.9, 93.5) | KiCad (87.1, 93.5) |
| Lead run (taped to the can, \|y\| 12–14.5) | z 48 → 64, KiCad y 93.5 → 77.5 | same, mirrored |
| Wire pads, 2 × Ø0.5 THT, 4 mm pitch along z | KiCad (113.4, 77.47) and (113.4, 73.47) | (86.6, 77.47) and (86.6, 73.47) |
| New B.Cu keep-out `KO_B_ntc_C4` / `_C1` | x 111.8–115.0, y 72.5–95.5 | x 85.0–88.2, y 72.5–95.5 |

- The pads sit 2.5 mm below the CELL1 / CELL3 slots (z 72). **As placed (2026-10-24):** at |y| 13.4 J107's pad overlapped the GND pad of C406 (port 1's VBUS cap, F.Cu), so both pad pairs went to |y| 14.7 (KiCad x 114.7 / 85.3) and the keep-outs to x 111.5–116.05 / 83.95–88.5, y 72.13–96.48 (`monolith_shell.py` `sb_ntc_pads()`, `sb_ntc_runs()`). The leads still run at |y| 12–14.5 and bend out 0.2 mm to the pads.
- **Conflict:** C421 (47 µF 35 V, Kemet D, B.Cu) sits at KiCad (113.8, 82.0), on the C4 lead run. It also breaks the B.Cu height rule there (2.8 mm part, 2.3 mm limit, about 3.0 mm of real gap at |y| 13.8). The board README already puts the USB-side tantalums in the centre strip near the ports; C421 has to move either way.
- The back-cell NTCs (TS2, TS3 on J105, J106) stay where they were. The back cells run about 5 K cooler and never set the limit.

## 3. Thresholds for the new spot

Every limit was tuned against an NTC that read 4–9 K low, so moving the NTC without retuning cuts the 100 W burst from 6.2 to 1.7 min. Five discharge ramps were run with the NTC at the chosen spot (sustain 40 W in all):

| Policy (hottest NTC) | Full power | Energy, first 40 min | Hottest can | Hottest part | Outer face |
| --- | --- | --- | --- | --- | --- |
| 33 → 39 °C, NTC at the old spot (today's spec) | 6.2 min | 40.8 Wh | 42.5 °C | 58.5 °C | 47.7 °C |
| 33 → 39 °C, NTC at the new spot | 1.7 min | 36.5 Wh | 42.1 °C | 48.3 °C | 41.7 °C |
| 40 → 44 °C | 5.5 min | 44.2 Wh | 44.0 °C | 57.4 °C | 46.7 °C |
| **42 → 46 °C (recommended)** | **6.8 min** | **46.9 Wh** | **45.9 °C** | **59.5 °C** | **48.7 °C** |
| 44 → 48 °C | 6.8 min | 49.1 Wh | 47.6 °C | 60.0 °C | 50.0 °C |
| 46 → 50 °C | 6.8 min | 51.3 Wh | 49.6 °C | 60.9 °C | 51.2 °C |

- The full-power burst stops growing at 6.8 min: from there the 55 °C board ramp ends it, not the cells.
- **42 → 46 °C** gives 15 % more energy in the first 40 minutes than today's policy. The outer face stays within 1 K of today's, and the cans stay 14 K under BAK's 60 °C. Total energy is about the same (88.8 Wh); it just comes out sooner.
- 44 → 48 °C is close to what the 10-23 "40 → 44 °C on the old NTC" run did to the real can. It gives another 2 Wh for a 50 °C outer face. Try it on P0 if the case doesn't feel too hot in the hand.
- At 35 °C ambient, 42 → 46 °C gives 1.3 min of full power and 33.2 Wh in 40 minutes (today's: 0 min, 28.8 Wh). The hottest can reaches 50.3 °C.
- Above the ramp: hold 40 W to 50 °C, then ramp to 0 at 58 °C, under the gauge's 60 °C OTD. The old 45 → 55 °C step was set for an NTC that read up to 8.5 K low.

**Charging.** BAK allows charging from 0 to 45 °C. The old NTC hid how hot the stripe got: with the 40 → 45 °C ramp, the stripe reached 44.6 °C while charging and 48.0 °C in pass-through, above BAK's limit, while the NTC read 41 and 43 °C. With the NTC on the stripe:

| Charge ramp (hottest NTC) | 5 → 95 % on one 100 W charger | Trimmed after | Hottest can | Pass-through, charge after 2 h |
| --- | --- | --- | --- | --- |
| 40 → 45 °C, old spot (today) | 89 min | 33 min | 44.6 °C | 83 % (can 48.0 °C) |
| 40 → 44.5 °C, new spot | 99 min | 18 min | 41.7 °C | 62 % (can 43.9 °C) |
| **42 → 44.5 °C, new spot (recommended)** | **93 min** | **25 min** | **42.9 °C** | **64 % (can 44.3 °C)** |

The ramp ends at 44.5 °C so the gauge's 45 °C OTC stays a backstop and isn't the normal stop. Pass-through charges more slowly than before because the old charge rate only looked safe.

## 4. Gauge settings that go with it

- OTC 45 °C (recovery 42 °C), OTD 60 °C, UTC 0 °C: unchanged.
- Charge temperature ranges: T4 moves from 40 to **44 °C**, so the gauge's 2275 mA warm current sits under the firmware ramp and doesn't cut in with a step at 40 °C (firmware uses the lower of the two). T1 0 / T2 5 / T3 15 / T5 45 °C are unchanged.
- The protections and ranges must act on the hottest of TS1–TS4. Check how the BQ40Z50-R2 combines the four sensors (max or average) in the TRM and set it to max.
- The gauge also uses temperature for Impedance Track. A sensor that reads the stripe sits a few kelvin above the cell's average, so its resistance model sees a slightly warmer cell. Check the remaining-capacity prediction at the end of the P0 learning cycle.

## 5. Check on P0

- A thermocouple taped beside each front NTC, and one on the stripe away from it, through a 100 W run and a charge. If the NTC reads more than 1 K off the stripe, move the thresholds by the offset.
- With and without the foam cap on one cell, to measure the gel bias.
