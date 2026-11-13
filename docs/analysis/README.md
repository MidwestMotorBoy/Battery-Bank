# Analysis

Model studies of the whole pack and its board. Each folder has its own README with the results, the figures, the scripts that made them and the assumptions. Every number is a model value until the bench tests.

Every study here used the **hand-routed board** (its copper and its part positions; the board file at commit `8dd9eb6`) and the cup as it was on the study's date. Since 2026-11-13 the design is the script-built board on `master` (commit `dd34285`), and no study has been rerun for it. What carries over: everything about the cup, bumpers, carrier and cells, because the outline, holes, connectors, B.Cu parts and main inductors are the same on both boards. What does not: copper loss and path resistance, loop inductance, and the part-to-wall gaps of the F.Cu capacitors in the drop models (C434 and C524 moved about 13 mm and C420 about 5 mm; C531 moved 0.4 mm and turned 90°). The script-built board's own loop, copper-loss and 100 W burst numbers are in the solver comparison linked below. Each README opens with a status block that gives the geometry it ran on and says, for each finding, whether it was fixed, superseded by a later study, or is still open.

| Folder | What it covers |
|---|---|
| [`2026-10-31-thermal-25w-20w/`](2026-10-31-thermal-25w-20w/README.md) | USB1 at 25 W and USB2 at 20 W together, full to empty, at 25 / 35 / 40 °C, with the firmware derate on and off. Model cup with 1.2 mm walls and no rail spines; not rerun since |
| [`2026-10-31-drop-1m/`](2026-10-31-drop-1m/README.md) | First 1 m drop study, six poses, lumped two-mass model: bumper crush, peak g, PA12 stress, board flex, PEBA against TPU. Led to the 30 % slabs, the screw counterbores and the inductor wall pockets (PR #50). Its board and stress results are superseded by the two later drop studies |
| [`2026-11-01-bumper-materials/`](2026-11-01-bumper-materials/README.md) | Formlabs elastic resins against FDM TPU 95A for the bumpers, cap pad and sleeves, and engineered slabs (gyroid against vertical-wall honeycomb, 2026-11-05). Analysis only: TPU 95A with 30 % gyroid slabs stays |
| [`2026-11-04-drop-stress/`](2026-11-04-drop-stress/README.md) | 1 m drops with contact between every moving part (lumped 1-DOF bodies, Morley-plate board): part loads, stress, board strain, the 2026-11-05 cup fixes (PR #64), a gap-filler sensitivity bracket. Newest result for the board-face, cap-end and narrow-side drops |
| [`2026-11-05-inner-copper/`](2026-11-05-inner-copper/README.md) | Inner copper weight, 0.5 against 1 against 2 oz: power-path resistance, copper loss at 100 W, burst time and part temperatures. 1 oz recommended if cheap; not decided, the board stays 2 oz outer / 0.5 oz inner |
| [`2026-11-06-loop-area/`](2026-11-06-loop-area/README.md) | Inductance of every hot loop and gate-drive loop from a 3D partial-inductance solve on the real copper, switch-node areas, and ringing estimates. No loop needs a fix |
| [`2026-11-11-drop-3d/`](2026-11-11-drop-3d/README.md) | Full 3D explicit model (OpenCourant) of the 1 m back-face drop, runs 2 to 9: the rail spines and B.Cu edge lands (PR #69), rail tongue tip clearance, 0.7 mm wall pockets. The overtravel post chamfer that followed (PR #70) has not been rerun |

How the drop studies fit together, and where each drop pose stands today, is summarised in the root [`README.md`](../../README.md#drop-1-m-onto-concrete).

Related work elsewhere in the repo:

- The pack thermal model itself is in [`research_notes/Pack thermal BAK 65E/`](../../research_notes/Pack%20thermal%20BAK%2065E/README.md), with the loss-reduction study next to it in [`research_notes/`](../../research_notes/).
- The copper resistance of every power path and the current-sense tap checks are in the routed-board review, [`docs/reviews/2026-10-30-routed-board/`](../reviews/2026-10-30-routed-board/README.md).
- The solver comparison of the script-built (ground-up) layout against the hand-routed board, with the new board's hot loops, gate loops, copper loss and 100 W burst time, is in [`hardware/Production/groundup/compare/`](../../hardware/Production/groundup/compare/README.md).
- The enclosure's own design checks are in [`docs/mechanical-design.md`](../mechanical-design.md).
