# Analysis

Model studies of the whole pack. Each folder has its own README with the results, the figures, the scripts that made them and the assumptions. Every number is a model value until the bench tests.

| Folder | What it covers |
|---|---|
| [`2026-10-31-thermal-25w-20w/`](2026-10-31-thermal-25w-20w/README.md) | USB1 at 25 W and USB2 at 20 W together, full to empty, at 25 / 35 / 40 °C, with the firmware derate on and off |
| [`2026-10-31-drop-1m/`](2026-10-31-drop-1m/README.md) | 1 m drop onto concrete in six poses: bumper crush, peak g, stress in the nylon parts, board flex |
| [`2026-11-04-drop-stress/`](2026-11-04-drop-stress/README.md) | 1 m drops with contact between every moving part (lumped 1-DOF bodies, Morley-plate board): part loads, stress, board strain, the 2026-11-05 cup fixes |
| [`2026-11-11-drop-3d/`](2026-11-11-drop-3d/README.md) | Full 3D explicit model (OpenCourant) of the 1 m back-face drop, runs 2–9: the rail spines (mid-board prop), B.Cu edge lands, rail tongue clearance, wall pockets |

Older studies live in [`research_notes/`](../../research_notes/) (the pack thermal model, loss reduction) and in [`docs/mechanical-design.md`](../mechanical-design.md) (the cup's design checks).
