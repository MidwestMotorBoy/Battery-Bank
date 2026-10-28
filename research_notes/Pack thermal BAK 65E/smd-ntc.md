# SMD NTCs on the board for TS1 / TS4 (2026-10-28)

Logan asked whether the two front-cell NTCs (TS1 on C1, TS4 on C4) can be SMD parts on the board instead of the wired beads taped to the cans (`ntc-placement.md`). This note checks how well a board-mounted NTC tracks the hottest point of the front cell, picks the spot, and retunes the derate for it. Logan chose the switch on 2026-10-28: TH101 / TH104 on B.Cu at |y| 15.5 mm, z 29 mm.

Code: `smd.py` (probes and policy runs on `pack3d.py`) and `island.py` (local model of an isolated copper island). Numbers: `renders/smd.json` (stage where the 3-D model first assumed it), `renders/smd_p0.json` (`SMD_LAYOUT=p0`, port 1's stage on the `Production` board on the morning of 10-28) and `renders/smd_p0b.json` (`SMD_LAYOUT=p0b`, after Logan's 10-27 "Layout in progress" commit, the layout of record). Same assumptions as the README: 25 °C ambient, still air, 14 mΩ cells, P0 losses, policy p42c (42 → 46 °C discharge ramp, 42 → 44.5 °C charge ramp) unless stated.

## How it works

An SMD NTC soldered to the board reads the board copper under its pads. In the filler zone the stage's heat runs from the board through the gel into the can, so the board is always hotter than the can it cools into. How much hotter depends on how close the spot is to the FETs and inductor, and on how much power flows. So the spot matters more than anything else.

## Reading minus the hottest point of the same can

Layout of record (p0b): Q401 / Q402 at (|y|, z) (9.6, 41.7) / (14.1, 41.6), L401 at (11.8, 48.9), U403 BQ25756 at (11.4, 31.0) turned 90°, RBAT R427 at (18.2, 36.5). R424 and port 2 aren't placed yet: R424 is put beside L401 and port 2 is mirrored onto C1. Range over each run (after the first 3 min):

| B.Cu spot (\|y\|, z) | 100 W | 30 W | Charge | Pass-through |
| --- | --- | --- | --- | --- |
| Over the old bead spot, under L401 (12.9, 48) | +1.1 to +8.4 K | +0.7 to +1.7 K | +1.2 to +4.3 K | +2.7 to +9.4 K |
| z 38, beside the FETs (12.9, 38) | +1.0 to +7.4 K | +0.6 to +1.8 K | +1.0 to +4.0 K | +2.6 to +8.1 K |
| z 33 (12.9, 33) | +1.0 to +4.5 K | +0.6 to +1.4 K | +1.0 to +2.7 K | +2.2 to +5.1 K |
| Under U403 (12.9, 28.5) | +1.0 to +3.0 K | +0.6 to +1.1 K | +1.0 to +1.7 K | +1.7 to +4.0 K |
| **Outboard of U403, zone corner (15.5, 29)** | **+0.9 to +2.9 K** | **+0.6 to +1.1 K** | **+0.9 to +1.8 K** | **+1.6 to +3.8 K** |
| Inboard of U403 (7.5, 29) | +0.5 to +3.9 K | +0.6 to +1.0 K | +0.6 to +2.3 K | +1.5 to +4.5 K |
| Just below the zone (12.9, 26) | +0.5 to +3.2 K | +0.6 to +0.8 K | +0.5 to +1.8 K | +1.2 to +3.7 K |
| Wired bead on the stripe (10-24 design) | −0.5 to −0.2 K | −0.3 to −0.1 K | −0.4 to −0.2 K | −0.9 to −0.3 K |

- Near the FETs and inductor the error swings by 6–7 K with load: 8 K high in the 100 W burst, about 1 K at rest. No single threshold shift fixes that. The first-pass runs show it: shifting all thresholds up 6 K to win back the burst let the pack charge with the can at 46.1–46.7 °C straight after a 100 W discharge, over BAK's 45 °C limit, because the board had cooled to within 1.3 K of the can.
- In the corner of the filler zone farthest from the FETs and inductor, the board is cooled by the gel more than it is heated by the stage. At (15.5, 29) it reads 0.6–3.8 K high in every case and never low, and +0.6 to +1.0 K through the 100 W-then-charge sequence. That is the chosen spot: KiCad (115.5, 112.48) for TH104 and (84.5, 112.48) for TH101, 0.5 mm in from the zone's outer edge. Just below the zone (z 26) reads about the same, but the gel may not reach there.
- The spot moves with the stage. With the stage where the model first assumed it (BQ25756 at z 28–32, inductor at z 34–41), the zone's bottom read +0.6 to +4.0 K. With the 10-28-morning layout (stage at z 41–51), z 33 read 0.2–2.8 K and z 28.5 read up to 0.5 K low. If port 1's stage moves again, put the new positions in `p0b_src_boxes()` and rerun `SMD_LAYOUT=p0b python smd.py probes4 table`.

## A thermally isolated island doesn't help much

`island.py`: a 2 × 2.5 mm B.Cu island with a 0.4–0.8 mm moat and all inner copper and vias cleared under it still reads 60–73 % of the board-to-can difference (52 % with a 1.5 mm gel gap). The gel around it is at board temperature, so isolating it from the FR4 only takes out about a third of the error. Moving the part does more. The model's number is the board copper under the pads, so keep the inner planes under the NTC; a part that is half isolated would read between the board and the local can, which at this spot is cooler than the hottest point and could read low.

## Derate with the SMD at (15.5, 29)

| Policy (hottest NTC) | 100 W: full power | 100 W: energy in 40 min | 100 W: hottest can / part / outer face | 60 W: energy in 40 min, hottest can | Charge 5 → 95 % (can) | Pass-through after 2 h | 100 W, then charge at once: can while charging |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Wired bead, 42 → 46 °C (10-24 design) | 7.2 min | 47.2 Wh | 46.2 / 59.8 / 48.9 °C | 40.2 Wh, 46.2 °C | 93 min (43.1 °C) | 65 % | 44.6 °C (first-pass layout) |
| SMD, 42 → 46 °C | 4.7 min | 44.6 Wh | 44.6 / 55.6 / 45.5 °C | | 98 min (41.8 °C) | 53 % | 43.4 °C |
| **SMD, 44 → 48 °C (recommended)** | **6.0 min** | **47.1 Wh** | **46.6 / 58.0 / 47.4 °C** | **40.2 Wh, 46.6 °C** | **98 min (41.8 °C)** | **53 %** | **43.7 °C** |

- Because the SMD reads 1–3 K high under load, the 10-24 thresholds would cost 2.6 Wh in the first 40 min at 100 W. Moving the **discharge** ramp up 2 K (44 → 48 °C, 40 W held to 52 °C, then to 0 at 59 °C under the gauge's 60 °C OTD) gives back the same energy as the wired design, with the can 0.4 K warmer and the board 1.8 K cooler.
- Leave the **charge** ramp at 42 → 44.5 °C. The sensor reads high, so charging slows a little early: 98 instead of 93 min, and pass-through reaches 53 % instead of 65 % after 2 h. In exchange the can stays at or below 43.7 °C while charging in every run, and the minimum offset (0.6 K) is too small to shift the charge ramp safely toward BAK's 45 °C.
- Keep the gauge settings (OTC 45 °C, recovery 42 °C, OTD 60 °C, T4 44 °C). The gauge already uses the hottest cell sensor for its over-temperature checks and the coldest for its under-temperature checks (TRM SLUUBK0 §2.8), and the back-cell NTCs (TS2, TS3) stay wired. Charge temperature ranges follow `Temperature()`, which must be set to the hottest sensor (`DA Configuration[CTEMP1:0]` = 0, 0).

## What else changes

- Part: NCP15XH103F03RC (0402, LCSC C77131, the same part as TH401), TH101 / TH104 on B.Cu, 90°, locked, in a 1.1 × 2.2 mm notch at the outer edge of `KO_B_gap_filler_L` / `_R` (that keep-out bans B.Cu footprints). At 0.35 mm tall it sits under 2.75 mm of gel. Its low side goes to CELL_1N (gauge VSS) by its own trace, not through the zone's copper pour.
- Gone: J102 / J107, `KO_B_ntc_C1` / `_C4`, the foam caps, the taped leads and their four solder joints, and the insulation worry (the board isn't at can potential). The front-cell part of assembly step 2 goes away, but the gel has to reach the zone's bottom outer corner.
- Lost: the sensor no longer touches the cell. If the gel is short or voided over the part, it reads the board alone, which is high (safe, but it costs burst time).
- P0 check (spec Testing): a thermocouple on each front can's stripe at the hottest spot (z 40–48) and one beside where the NTC faces the can, compared with TS1 / TS4 through a 100 W run, a charge and a 100 W-then-charge sequence. If TS1 / TS4 read more than 1 K differently from this table, move the discharge ramp by the difference.
