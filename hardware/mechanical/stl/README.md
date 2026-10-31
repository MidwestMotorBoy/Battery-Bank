# Print files, by material

All files are in millimetres and in the pack's own frame (z along the cells, port end up), so every part lands in place
when files are imported together. Files with several copies of a part (rails, sleeves) hold every copy in its fitted
position. Lay them out on the build plate yourself, or ask JLC3DP to print the bodies as separate parts.

`python monolith_cup.py stl` and `python monolith_coupons.py` (in `hardware/mechanical/`) write these files. Don't
move them by hand: the scripts put each part in its material's folder (`STL_MAT` in `monolith_cup.py`).

## `MJF_PA12/`: JLC3DP, MJF PA12-HP nylon

| File | Part (exploded-view no.) | Per pack | Notes |
|---|---|---|---|
| `monolith_cup_cup.stl` | Cup (11) | 1 | No surface finish (see below). |
| `monolith_cup_cap.stl` | Bottom cap (14) | 1 | The O-ring groove and the seal faces must stay bare. |
| `monolith_cup_carrier.stl` | Cell carrier (1) | 1 | |
| `monolith_cup_rails.stl` | Board rail blocks (2) | 4 | All four in one file. |
| `coupons/monolith_coupon_A_seal_bore_ladder.stl` | Fit coupon A | 1 set | Print the coupons first. |
| `coupons/monolith_coupon_B1_cup_mouth.stl` | Fit coupon B1 | 1 set | |
| `coupons/monolith_coupon_B2_cap.stl` | Fit coupon B2 (the real cap) | 1 set | |
| `coupons/monolith_coupon_C1_carrier.stl` | Fit coupon C1 (the real carrier) | 1 set | |
| `coupons/monolith_coupon_C2_rails.stl` | Fit coupon C2 (the real rails) | 1 set | |

Order these in PA12-HP, the material the fit checks assume, in grey or dyed black. Don't use spray paint: JLC's paint
is 0.1–0.2 mm thick, which is more than the USB-C seal bores and the O-ring groove can take.

## `TPU_95A/`: FDM, TPU 95A (at home or JLC3DP)

| File | Part (exploded-view no.) | Per pack | Print settings |
|---|---|---|---|
| `monolith_cup_bumpb.stl` | Bottom bumper with the vent grille (16) | 1 | One print, face down: 5 walls, 4 top and 4 bottom layers, 30 % gyroid. |
| `monolith_cup_bumpt.stl` | Top bumper with the port numbers (17) | 1 | Same as the bottom bumper. |
| `monolith_cup_pad.stl` | Cap pad (12) | 1 | 15 % gyroid. |
| `monolith_cup_sleeve.stl` | Post sleeves (10) | 4 | All four in one file, printed solid. |
| `coupons/monolith_coupon_C3_sleeves.stl` | Fit coupon C3 (the real sleeves) | 1 set | |

## `not_printed/`: bought, cut or dispensed (for fit checks and CAD only)

| File | Part | What it really is |
|---|---|---|
| `monolith_cup_oring.stl` | O-ring (13) | 2.0 mm silicone or NBR O-ring, bought (parts tracker). |
| `monolith_cup_foam.stl` | Preload rings (5) | Cut from silicone sponge sheet with hollow punches. |
| `monolith_cup_filler.stl` | Gap filler (8) | Parker GEL 30, dispensed. |
| `monolith_cup_vent.stl` | Pressure vent (19) | 12 mm adhesive ePTFE patch, bought. |
