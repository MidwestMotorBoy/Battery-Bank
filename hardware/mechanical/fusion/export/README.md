# Fusion exports of the printed parts (true arcs)

Written by `../export_parts.py` from the parametric Fusion model that `../monolith_fusion.py` builds (2026-11-05).
Same frame and units as `hardware/mechanical/stl/`: millimetres, pack frame (z along the cells, port end up), every part
in its fitted position, multi-copy parts (rails, sleeves) with all copies in one file.

The difference from `hardware/mechanical/stl/` is the geometry. Those files come from the mesh model, where every round
face is a 48-sided polygon. Here the STEP files carry real cylinders, arcs and fillets, and the STLs are tessellated by
Fusion to 0.01 mm chord deviation. JLC3DP takes either STEP or STL.

| Folder / file | Part | Volume (mm³) | Mesh-model STL (mm³) |
|---|---|---|---|
| `MJF_PA12/monolith_cup` | Cup | 32496 | 32485 |
| `MJF_PA12/monolith_cap` | Bottom cap | 7538 | 7536 |
| `MJF_PA12/monolith_carrier` | Cell carrier | 8982 | 9024 |
| `MJF_PA12/monolith_rails` | Board rail blocks (4) | 1138 | 1138 |
| `TPU_95A/monolith_sleeves` | Retaining sleeves (4) | 36.3 | 36.2 |
| `TPU_95A/monolith_bumper_top` | Top bumper | 19435 | 19428 |
| `TPU_95A/monolith_bumper_bottom` | Bottom bumper | 11256 | 11240 |

All STLs are watertight and their bounding boxes match the mesh-model files exactly. The carrier is 42 mm³ lighter
because true circles cut the thin web cusps between the cells a little deeper than the polygons do.

Known differences and gaps:
- Text (port digits, `91 Wh`) is Arial Bold, not DejaVu Sans Bold. Cap heights are the same (4 mm, 7 mm) and the
  rating still clears the vent pocket, but the glyph shapes differ.
- The TPU cap pad and the fit coupons are not in the parametric model yet. Keep using `hardware/mechanical/stl/` for
  those.
- Board-derived features (the wall pockets over L401 / L501) are fixed geometry. After a board change, re-run
  `monolith_cup.py`, update `WALL_POCKETS` in `monolith_fusion.py` and rebuild.
