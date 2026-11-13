# Print files, by material

All files are in millimetres and in the pack's own frame (z along the cells, port end up), so every part lands in place
when files are imported together. Files with several copies of a part (rails, spacers) hold every copy in its fitted
position. Lay them out on the build plate yourself, or ask JLC3DP to print the bodies as separate parts.

`python monolith_cup.py stl` (in `hardware/mechanical/`) writes these files. Don't move them by hand: the script puts
each part in its material's folder (`STL_MAT` in `monolith_cup.py`). The files match the model at commit c9b707f
(2026-11-12: 0.3 mm chamfer on the cap's overtravel post tops), regenerated and checked byte for byte on 2026-11-13.

## `MJF_PA12/`: JLC3DP, MJF PA12-HP nylon

| File | Part (exploded-view no.) | Per pack | Notes |
|---|---|---|---|
| `monolith_cup_cup.stl` | Cup (11) | 1 | No surface finish (see below). |
| `monolith_cup_cap.stl` | Bottom cap (14) | 1 | The O-ring groove and the seal faces must stay bare. |
| `monolith_cup_carrier.stl` | Cell carrier (1) | 1 | |
| `monolith_cup_rails.stl` | Board rails (2) | 2 | Both in one file; one rail per side (bottom and top block joined by a spine since 2026-11-11). |
| `monolith_cup_spacer.stl` | Post spacers (10) | 4 | All four in one file. Ø4 × 3.3 mm with crush ribs in the bore (2026-11-03; TPU sleeves before). |

Order these in PA12-HP, the material the fit checks assume, in grey or dyed black. Don't use spray paint: JLC's paint
is 0.1–0.2 mm thick, which is more than the USB-C seal bores and the O-ring groove can take.

### No fit coupons

There are no fit coupons: Logan dropped them on 2026-11-07, because the real parts cost about the same, so the first
cup, cap and core are the fit test (`ordering/README.md`, H01). The coupon STLs were removed from the repo on
2026-11-13. `monolith_coupons.py` still writes them (into a git-ignored `coupons/` folder here) if a test piece is ever
wanted.

## `TPU_95A/`: FDM, TPU 95A (at home or JLC3DP)

| File | Part (exploded-view no.) | Per pack | Print settings |
|---|---|---|---|
| `monolith_cup_bumpb.stl` | Bottom bumper with the vent grille (16) | 1 | One print, face down: 5 walls, 4 top and 4 bottom layers, 30 % gyroid. |
| `monolith_cup_bumpt.stl` | Top bumper with the port numbers (17) | 1 | Same as the bottom bumper. |
| `monolith_cup_pad.stl` | Cap pad (12) | 1 | 15 % gyroid. Printed height 9.8 mm: the file is 1.2 mm taller than the installed pad (`PAD_PROUD`, since 2026-11-07), and that is the core's preload. Don't scale it. |

## `not_printed/`: bought, cut or dispensed (for fit checks and CAD only)

| File | Part | What it really is |
|---|---|---|
| `monolith_cup_oring.stl` | O-ring (13) | 58 × 54 × 2 mm NBR O-ring, bought (parts tracker H07). The file is the ring as squeezed in its groove. |
| `monolith_cup_foam.stl` | Preload rings (5) | Cut from 1 mm EVA foam sheet with hollow punches (parts tracker C09; silicone sheet until 2026-10-31). |
| `monolith_cup_filler.stl` | Gap filler (8) | Parker GEL 30, dispensed: two zones, about 1.9 g each (3.8 g per pack, model value). |
| `monolith_cup_vent.stl` | Pressure vent (19) | 12 mm adhesive ePTFE patch, bought. |
