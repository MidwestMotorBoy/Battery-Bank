# SMD NTCs on the board for TS1 / TS4 (2026-10-28)

Logan asked whether the two front-cell NTCs (TS1 on C1, TS4 on C4) can be SMD parts on the board instead of the wired beads taped to the cans (`ntc-placement.md`). This note checks how well a board-mounted NTC tracks the hottest point of the front cell, and what that does to the derate. Code: `smd.py` (probes and policy runs on `pack3d.py`) and `island.py` (local model of an isolated copper island); numbers: `renders/smd.json` (stage where the 3-D model assumed it) and `renders/smd_p0.json` (stage where it sits on the `Production` board now). Same assumptions as the README: 25 °C ambient, still air, 14 mΩ cells, P0 losses, policy p42c (42 → 46 °C discharge ramp, 42 → 44.5 °C charge ramp).

## How it works

An SMD NTC soldered to the board reads the board copper under its pads. In the filler zone, the stage's heat runs from the board through the gel into the can, so the board is always hotter than the can it cools into. How much hotter depends on how close the spot is to the FETs and inductor, and on how much power is flowing. That makes the spot matter more than anything else.

## Reading minus the hottest point of the same can

Stage where it is on the `Production` board today: Q401 / Q402 at z 44–50, L401 at |y| 4.3, z 47, U403 at |y| 17.4, z 46. RBAT and port 2 aren't placed yet: RBAT is put beside the FETs and port 2 is mirrored onto C1. Range over each run (after the first 3 min):

| B.Cu spot (\|y\|, z) | 100 W | 30 W | Charge | Pass-through |
| --- | --- | --- | --- | --- |
| Over the bead's spot, under the FETs (12.9, 48) | +1.5 to +10.2 K | +0.9 to +2.5 K | +1.5 to +5.6 K | +3.7 to +11.3 K |
| Where J102 / J107 are now (14.7, 66) | +1.6 to +9.1 K | +1.3 to +1.7 K | +2.0 to +4.2 K | +3.4 to +11.0 K |
| Filler zone, z 38 | +1.0 to +3.9 K | +0.6 to +1.0 K | +1.0 to +2.2 K | +1.8 to +4.5 K |
| **Filler zone, bottom end, z 33 (12.9, 33)** | **+0.3 to +2.5 K** | **+0.2 to +0.6 K** | **+0.3 to +1.4 K** | **+0.8 to +2.8 K** |
| Filler zone, z 28.5 | −0.5 to +2.2 K | −0.3 to +0.5 K | −0.4 to +1.2 K | −0.1 to +1.9 K |
| Wired bead on the stripe (today) | −0.3 to −0.1 K | −0.1 K | −0.2 to −0.1 K | −0.4 to −0.2 K |

- Over the FETs, the error swings by about 9 K with load: 10 K high in the 100 W burst, 1.5 K at rest. No single threshold shift fixes that. The model shows it: shifting all thresholds up 6 K to win back the burst lets the pack charge with the can at 46.1–46.7 °C straight after a 100 W discharge, over BAK's 45 °C limit, because the board has cooled to within 1.3 K of the can by then.
- At the bottom end of the filler zone, about 10 mm below the stage, the board is cooled by the gel more than it is heated by the stage. There it reads 0.0–2.8 K high in every case, with the cool-down-then-charge case included (+0.4 to +0.8 K), and never low. z 28.5 reads up to 0.5 K low, so z 33 is the spot.
- With the stage where the 3-D model first assumed it (BQ25756 at z 28–32, inductor at z 34–41), the same zone-bottom spot read +0.6 to +4.0 K. The spot has to be the end of the filler zone farthest from the FETs and inductor, and has to be rechecked if port 1's stage moves.

## A thermally isolated island doesn't help much

`island.py`: a 2 × 2.5 mm B.Cu island with a 0.4–0.8 mm moat and all inner copper and vias cleared under it still reads 60–73 % of the board-to-can difference (52 % with a 1.5 mm gel gap). The gel around it is at board temperature, so isolation from the FR4 only takes out about a third of the error. Moving the part does more than isolating it.

## Derate with the SMD at z 33, thresholds unchanged

| | Wired bead (today) | SMD at z 33 |
| --- | --- | --- |
| 100 W: full power | 7.2 min | 5.8 min |
| 100 W: energy in the first 40 min | 47.1 Wh | 46.1 Wh |
| 100 W: hottest can / part / outer face | 45.8 / 60.1 / 51.4 °C | 45.4 / 58.0 / 49.7 °C |
| Charge 5 → 95 %, one 100 W charger | 93 min, can 42.8 °C | 95 min, can 42.5 °C |
| Pass-through, charge after 2 h | 63 % | 58 % |
| 100 W to empty, then charge at once: hottest can with current flowing | 44.6 °C (first-pass stage layout) | 44.1 °C |

- No retune is needed. The sensor reads a little high, so the limits act a little early: about 1 Wh less in the first 40 minutes, 2 minutes more to charge, and 5 % less charge in pass-through. All the misses are on the safe side.
- Keep the gauge settings (OTC 45 °C, recovery 42 °C, OTD 60 °C, T4 44 °C). The gauge already uses the hottest cell sensor for its over-temperature checks and the coldest for its under-temperature checks (TRM SLUUBK0 §2.8), and the back-cell NTCs (TS2, TS3) stay wired. Charge temperature ranges follow `Temperature()`, which must be set to the hottest sensor (`DA Configuration[CTEMP1:0]` = 0, 0).
- If P0 shows the SMD reading more than 1 K high through a 100 W run, the discharge ramp can move up by that amount. Leave the charge ramp alone unless the cool-down-then-charge test agrees.

## What else changes

- Part: NCP15XH103F03RC (0402, already TH401 on the BOM), on B.Cu at KiCad (112.9, 108.5) for TS4 and (87.1, 108.5) for TS1 (KiCad x = 100 + y, y = 141.47 − z). Both are inside `KO_B_gap_filler_R` / `_L`, which bans B.Cu footprints, so they need an exception. At 0.35 mm tall, the part sits under 2.75 mm of gel. Put the pads on the zone's copper pour so the part reads the board there. Route the low side back to the gauge's VSS (CELL_1N) as its own trace, not through the pour.
- Gone: J102 / J107, `KO_B_ntc_C1` / `_C4`, the foam caps, the taped leads and their solder joints, and the insulation worry (the board isn't at can potential). The assembly step for the front NTCs goes away.
- Lost: the sensor no longer touches the cell. If the gel is short or voided under the part, it reads the board alone, which is high (safe). If port 1's stage moves on the board, rerun `SMD_LAYOUT=p0 python smd.py p0 p0b table` with the new positions in `p0_src_boxes()`.
- P0 check (spec Testing): keep a thermocouple on each front can's stripe beside where the bead was, and compare it with TS1 / TS4 through a 100 W run, a charge and a 100 W-then-charge sequence.
