from slib import *
f = mk()
MMf = 1e-6
def P(x, y): return (int(round(x * 1e6)), int(round(y * 1e6)))

# 1 DRV_SUP port 2, In3: 90 degree corner at (100.025, 110.8245) -> 0.3 mm chamfer
chamfer(f, '728f9cb3', '8a952fc7', 0.3)

# 2 DSG_G F: blob inside pad D103.1 -> one diagonal into the pad centre
v = f.via(99.225, 123.0245); p = f.pad('D103.1')
f.replace(['ff62e4ae', 'a97e80e5', '25168725'], [v, (v[0], p[1] - (p[0] - v[0])), p])

# 3 CHG_G In3: "<" kink at (95.15, 119.7995) -> the vertical at x = 95.925 runs straight down to the diagonal
a = f.pt(95.925, 118.2745, 'In3'); b = f.pt(97.175, 121.8245, 'In3')
f.replace(['4dd83404', 'b376de36', 'b8ce91c6'], [a, (a[0], b[1] - (b[0] - a[0])), b])

# 4 CELL_1N In3: 90 degree corner at (96.525, 120.4245) -> chamfer
chamfer(f, 'bfd0d195', 'c441d0d5', 0.4)

# 5 CE_N port 1 In2 stub in via (110.575, 120.1745): tried the diagonal from the via centre -> 0.099 mm to the ILIM via (111.175, 118.9745). Forced, left.

# 6 3V3 In2: off-angle 0.4 neck (0.269 mm, dx 0.25 dy 0.1) into via (114.475, 120.1245) -> the 0.6 piece runs 0.15 mm on, one 45 degree
#   0.4 piece (0.141 mm) into the via centre. A straight horizontal entry would need a neck of at least 0.282 mm (SWCLK via
#   (114.375, 120.7745)), longer than the neck is now, so it is not used.
v = f.via(114.475, 120.1245); k = (v[0] - 100000, v[1] - 100000)
f.replace(['f14e5602'], [f.pt(113.725, 120.0245, 'In2'), k])
f.replace(['874b7a89'], [k, v])

# 7 GAUGE_FUSE B: "<" corner at (107.775, 119.8745) -> clipped with a vertical piece
a = f.pt(108.725, 118.9245, 'B'); b = f.pt(109.275, 121.3745, 'B'); x = P(108.375, 0)[0]
f.replace(['b70a10d2', '031cc147'], [a, (x, a[1] + (a[0] - x)), (x, b[1] - (b[0] - x)), b])

# 8 DRV_SUP port 2, F at C511.1 / U503.23: pin track and via track each ended inside the pad -> one polyline pin - pad - via
pin = f.pad('U503.23'); v = f.via(88.825, 106.3245)
f.replace(['fe2a57d3', '23844c05', '26a1710c'], [pin, (pin[0], v[1] + (v[0] - pin[0])), v])


# ---------------- batch 2: charger twins and F-layer survey
def dg(a, b):
    """corner point for 'straight from a, then a 45 degree piece into b'"""
    return f.L(a, b, first='straight')[1]

# 9 twin match, hidden jogs at diode pads: port 1 has one 45 degree piece, port 2 had a 90 degree stub
v = f.via(84.025, 104.2745); p = f.pad('D510.2')            # REGN
f.replace(['34d8b587', '698f2d68'], f.L(v, p, first='straight'))
v = f.via(85.45, 104.71); p = f.pad('D504.1')               # BTST1
f.replace(['bb82e127', 'cfa4e04f'], f.L(v, p, first='straight'))
v = f.via(90.775, 104.6245); p = f.pad('D505.2')            # DRV_SUP (jog at the pad end: at the via end it would poke out of the via)
f.replace(['79044799', '346b94c0'], f.L(v, p, first='straight'))
v = f.via(83.525, 106.1245); p = f.pad('D510.1') if False else f.pt(83.424, 105.55, 'F')
f.replace(['6ece24f5', 'b3781119'], f.L(v, p, first='straight'))

# 10 PACK_P F, via (93.825, 113.6245) to R113.1: flat + diag + 0.11 flat -> diag + flat (mirror of the R518.1 side)
v = f.via(93.825, 113.6245); p = f.pad('R113.1')
f.replace(['ac82a9f7', '64945558', 'fab7c81e'], f.L(v, p, first='diag'))

# 11 Net-(U403-FB) F: bump between via (110.625, 114.5245) and R419.1 -> straight down, 45 degree piece inside the pad
v = f.via(110.625, 114.5245); p = f.pad('R419.1')
f.replace(['4b3f5c7c', 'd1f176f1', 'b2a1c19d'], f.L(v, p, first='straight'))

# 12 Net-(U101-VC2) F at C103.1, hook into via (92.375, 123.0745): one diagonal would make a 45 degree pair with the other exit of the pad. Left.

# 13 REGN port 1 F, R415.1 to via (109.125, 119.6745): 0.16 mm flat between two diagonals -> two 0.3 mm flats
p = f.pad('R415.1'); v = f.via(109.125, 119.6745); a = f.pt(108.2155, 119.9745, 'F')
b = (a[0] + 300000, a[1]); c = (b[0] + (b[1] - v[1]), v[1])
f.replace(['63665d82', 'a04ed204', '6937fd4f'], [a, b, c, v])

# 14 CELL_1N F in the U102 thermal pad: staircase (down, 0.225 right, 0.25 down, right) -> down, one diagonal, right
top = f.pt(98.975, 130.2745, 'F'); c = f.pad('U102.9'); pin = f.pt(100.15, 131.75, 'F')
m = (c[0], pin[1]); k = (top[0], m[1] - (m[0] - top[0]))
f.replace(['83979084'], [top, k])
f.replace(['41a1e28e', 'e9ee44e6', '2ca8f0b0'], [k, m, pin])

# 15 CHG_INH F hook round via (104.375, 132.7245): a straight chain track - via - via puts two bends half inside the vias. Left.


# ---------------- batch 3: In2 survey
# 16 3V3 In2: 2.03 mm long 0.3 mm neck between two 0.6 mm pieces, (113.925, 115.62) .. (113.725, 117.57); the hole of the ILIM via
#    (114.225, 117.0245) forces a neck at x = 113.725. Left as round 2 left it. Variant B (no neck): 0.6 mm through
#    (113.925, 115.6245) (113.925, 116.2245) (113.525, 116.6245) (113.525, 117.3745) (113.725, 117.5745): chk-clean, excursion 0.2 mm,
#    but the 0.28 mm jog back is shorter than the track is wide and the audit counts 2 end_off_track for it.

# 17 CELL_1N In2, 0.2 mm stub out of via (115.025, 116.9745): the diagonal from the via centre comes 0.174 mm from the J301 hole (0.2 needed). Forced, left.

# 18 CE_N port 1 In2: branch left the tee with a 0.28 diagonal + 0.35 vertical dog-leg -> tee moved along the through track, branch straight
v = f.via(111.575, 114.1245); e1 = f.pt(112.925, 115.4745, 'In2'); e2 = f.pt(113.325, 112.7245, 'In2')
T = (v[0] + 175000, v[1] + 175000)
f.replace(['7edba77c', 'd61efd25', '1f13248f', 'd8ca8754', 'e3682773'], [v, T, e1])
f.add('/USB Port 1/CE_N', 'In2', 0.2, [T, e2])

# 19 TS4 In2: 90 degree corner in open space at (93.475, 128.0245) -> 0.3 mm chamfer
chamfer(f, '9c1ec5b2', '5b665a2b', 0.3)


# ---------------- batch 4: In3 and B survey
# 20 I2CC_SCL In3 (sensitive): 0.2 mm jog (99.625, 113.5245)-(99.825, 113.7245) in the middle of the run; the DRV_SUP via
#    (100.025, 113.2245) needs y >= 113.70 there, so the whole flat goes to y = 113.7245 (excursion 0.2 mm)
f.replace(['f2ec1ac2', '92b3cd07', 'd8d91546', 'b31a51d1'], [P(98.375, 113.2745), P(98.825, 113.7245), P(100.225, 113.7245)])

# 21 I2CC_SCL In3 (sensitive): staircase (106.0..107.6, 112.87..114.175) of three diagonals, a flat and a vertical -> one diagonal
#    half way between the old steps (excursion 0.25 mm)
f.replace(['f23e51f1', 'c2a79a4b', 'f9cc335a', '78c6014d', 'de0d3cc1', '5277c58f', '6ea61e19'],
          [P(101.075, 112.8745), P(106.325, 112.8745), P(107.6255, 114.175), P(108.59, 114.175)])

# 22 3V3 In3 (0.3 mm, inside its own pour): four 90 degree corners -> 0.4 mm chamfers; the diagonal + 0.45 vertical + 90 degree corner
#    next to the J302 hole -> one diagonal
y1 = 131024499; y2 = 133024499; yb = 133724500
f.replace(['e8b02485', '0a44d180', '3d057fde', '230eac86', '8aa4146f', '0b15d87a', 'a8dc3ae1', '3adcdc78'],
          [P(117.675, 129.4745), P(117.175, 129.4745), P(116.775, 129.8745), (116775000, y1 - 400000), (116375000, y1),
           (115275000, y1), (114875000, y1 + 400000), (114875000, y2 - 400000), (114475000, y2), (111825000, y2),
           (111825000 - (yb - y2), yb), P(110.025, 133.7245)])

# 23 /USB Port 2/TS B: 0.4 mm flat between two diagonals at (92.025..92.4255, 110.5245) -> the first diagonal runs on to x = 92.75
f.replace(['ee1b1aed', '63c80dd5', 'ec318723', '9c28383c'], [P(89.475, 113.0745), P(92.75, 109.7995), P(92.75, 107.7995)])

# 24 BTP_INT B: diagonal, 0.4 flat, diagonal with the tee, 0.35 stub into via (97.925, 122.3245) -> the first diagonal runs straight
#    on into the via (its line is 0.035 mm off the via centre: 0.05 mm piece inside the via), tee moves 0.28 mm along the branch
T = P(96.525, 120.9745)
f.replace(['08b7e669', '347acb19', '1b01a663', 'c2b5b02e', 'a7e49c17', '4a44b8e8'],
          [P(94.425, 118.8745), T, P(97.875, 122.3245), f.via(97.925, 122.3245)])
f.replace(['cbf0dcf0'], [T, P(94.925, 122.5745)])

if __name__ == '__main__':
    finish(f, 'spec.json')
