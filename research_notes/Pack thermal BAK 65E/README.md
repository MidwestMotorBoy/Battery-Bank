# Pack thermal model: BAK N21700CX-65E in the cup (2026-10-23)

A 3-D finite-volume model of the P0 power module (four BAK 65E cells in 4S1P, the P0 board, gap filler) inside the MJF PA12 cup, run with the 10-21 charge and thermal policy in the loop. Interactive report with all the renders: <https://claude.ai/artifact/48csm6CzS7dAmMu56cYMhL>. The PNGs in `renders/` are the same maps.

## Results (25 °C ambient, still air, model values)

| Case | Full power | To empty / full | Hottest can | Hottest board part | Within one cell | Outer skin |
| --- | --- | --- | --- | --- | --- | --- |
| Idle | | | +0.1 K | +0.1 K | | |
| 30 W out | never derates | 179 min, 90 Wh | 36.8 °C | 40.4 °C | 2.9 K | 36.8 °C |
| 60 W out | 30 min, then 40 W | 114 min | 42.5 °C | 48.9 °C | 5.7 K | 42.4 °C |
| 100 W out, one port | 6.2 min, then 40 W | 111 min, 89 Wh | 42.5 °C | 58.5 °C | 10.4 K | 47.7 °C |
| 100 W out, 65 + 35 W | 7.8 min | 107 min | 41.6 °C | 49.3 °C | 7.2 K | 43.1 °C |
| Charge, one 100 W charger | trimmed after 33 min | 89 min, 5 → 95 % | 44.6 °C | 53.2 °C | | 46.3 °C |
| Charge, two 45 W chargers | trimmed after 43 min | 85 min | | 47.3 °C | | |
| Pass-through (100 W in, 30 W out) | charge trimmed after 6 min | 83 % after 2 h | 48.0 °C | 61.8 °C | 11.8 K | 53.6 °C |

- At 100 W out the pack makes about 6.1 W of heat: 2.3 W in the cells and 3.8 W on the board. The FEB estimate was about 12 W (6.5 W in the cells). The power stage is now the main heat source.
- The 100 W burst ends when the hottest cell NTC reaches 33 °C, mostly from the USB1 stage heating C4 through the gap filler. The stage is about 1 K short of the 55 °C board ramp by then.
- Front cells run about 5 K above the back pair at 100 W. Within a cell, the hot stripe faces the board over the filler.
- The mid-length NTC facing the pack centre reads up to 8.5 K below the hottest can point at 100 W and 4.5 K while charging. Follow-up (2026-10-24, `ntc-placement.md`): the front NTCs move onto the hot stripe inside the filler zone (7° outboard, z 48), which reads within 0.3 K, and the derate is retuned to 42 → 46 °C.

## Gap filler

About 4.5 g (1.5 cc) of a 3–3.6 W/m·K dispensable silicone, between the B.Cu via zone and the two front cells over each stage (|y| 7–16 mm, z 27–53 mm). The bond line is 2.75 mm at the tangent and about 3.8 mm at the edges, so it must be a gel or cure-in-place filler, not a pad.

- Decided 2026-10-24 for P0 and the gift packs: Parker Chomerics THERM-A-GAP GEL 30 (3.5 W/m·K, SG 3.1, one part, pre-cured, reworkable; 10 cc syringe 65-00-GEL30-0010). Comparison of seven options: `gap-filler-options.md`.
- Laird Tflex CR350S, listed here earlier as a room-temperature cure, needs an oven cure (70 °C then 100 °C) and is out.
- Without filler, the board ramp ends the 100 W burst after 2 min and the hottest part runs 4.1 K hotter (6.4 K while charging). A 6 W/m·K grade, a wider zone, beads between cells and a parts-to-wall pad each buy 1–6 K for 4–11 g; not worth it. Filler between the cans and the cup wall does nothing (0.15 mm gap).

## Cell temperature spread and a graphite wrap (`sheet.py`)

The spread comes from the board, not the cells: the stage's heat goes into the front cell under it (C4 for USB1) through the gap filler. A graphite heat-spreader wrap round the four-cell bundle, in the 0.275 mm cell-to-cup gap and 65 mm tall, spreads it over all four cells. It is modelled as extra conductances along the sheet with full contact where it touches a can. Panasonic PGS grades: 70 µm, 750–950 W/m·K, 1.1 g/cc; 25 µm, 1500–1700 W/m·K, 2.1 g/cc. A PET-laminated type is needed because the bare sheet conducts electricity: A-SM is about 90 µm finished from the 70 µm base.

| Case | Cell-to-cell, peak / average | Within one cell, peak | Hottest can | Hottest part |
| --- | --- | --- | --- | --- |
| 100 W, no wrap | 6.4 / 4.3 K | 10.4 K | 42.5 °C | 58.5 °C |
| 100 W, 70 µm wrap (about 1.2 g) | 4.2 / 2.3 K | 5.6 K | 40.0 °C | 54.5 °C |
| 100 W, 25 µm wrap (about 0.8 g) | 4.7 / 2.7 K | 6.5 K | 40.4 °C | 54.8 °C |
| Charging, no wrap | 6.0 / 4.8 K | 6.4 K | 44.6 °C | 53.2 °C |
| Charging, 70 µm wrap | 3.0 / 2.6 K | 3.1 K | 42.4 °C | 51.1 °C |
| Pass-through, no wrap | 9.1 / 6.4 K | 11.8 K | 48.0 °C | 61.8 °C |
| Pass-through, 70 µm wrap | 5.4 / 3.5 K | 6.6 K | 45.0 °C | 60.4 °C |

With the 70 µm wrap, the 100 W burst grows from 6.2 to 6.8 min, and the first 40 minutes deliver 43.7 Wh instead of 40.8 Wh. Charging takes 83 min instead of 89. In pass-through the pack reaches 95 % instead of 83 % after 2 h. For scale, the USABC EV target is under 3 K cell-to-cell.

## Sensitivity (100 W, first 40 min)

| Change | Full power | Energy in 40 min |
| --- | --- | --- |
| Baseline | 6.2 min | 40.8 Wh |
| Cell DCR 12 or 16 mΩ | about the same | within 1 Wh |
| Front NTCs on the board-facing side | 3.8 min | 39.1 Wh |
| 35 °C ambient | 0 min | 28.7 Wh |
| Pack pocket (h = 4 W/m²K) | 6.0 min | 38.1 Wh |
| Cell derate 40 → 44 °C | 6.8 min (board ramp limits) | 48.9 Wh |

## Assumptions

Cell DC resistance 14 mΩ at 25 °C (BAK gives only ≤ 8 mΩ AC), 1.8× at empty, Arrhenius in temperature; checked against BatteryRealData's 25 A test. Exterior h = 10 W/m²K (convection plus radiation). P0 parts from the four loss cuts, 9 V gate drive off. Stage positions are assumed (USB1 over C4, USB2 over C1) because P0 placement isn't final. Full list in the report.

## Files

- `pack3d.py`: geometry, materials, voxel grid, electrical and loss model, firmware policy, cases.
- `network.py`: lumped thermal circuit (8 nodes) extracted from the 3-D model, with capacities fitted to its transients; `build_network_page.py` and `network_template.html` draw it (report: <https://claude.ai/artifact/EwEruQGBk4FTVFuvoE97Kr>).
- `ntc.py`: front-cell NTC spots (80 probes per cell) and the derate retuned for the chosen spot; results in `renders/ntc.json`, write-up in `ntc-placement.md`.
- `smd.py`: board-mounted SMD NTCs for TS1 / TS4 (spots on B.Cu, policy runs, stage at its `Production` position with `SMD_LAYOUT=p0`); `island.py`: local model of an isolated NTC island; write-up in `smd-ntc.md`.
- `fill.py`: gap-filler variants. `sheet.py`: graphite wrap variants. `sens.py`: sensitivity runs. `jobs.py`: runs everything on 4 cores (about 1.5 h).
- `render.py`: thermal maps and chart series. `summary.py`: summary table.
- `make_text.py` and `page_template.html` with `build_page.py OUT_DIR`: builds the report.
- `results/` (ignored) holds the per-run `.npz` files and grid caches.
