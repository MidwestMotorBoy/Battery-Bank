#!/usr/bin/env python3
"""north, round 3: hand fixes in x 79..121.5, y 69..103 against r3/geo.json.   python3 fix1.py -> spec1.json, after1_geo.json"""
import sys
from mylib import *
f = Fix(S + '/r3/geo.json', region=REGION)
P = f.pad
V = lambda x, y: f.via(x, y, quiet=True)
LDO = '/P1_LDO_3V3'

# ---- N1  P1_LDO_3V3 on F, U402.8 -> R441.1 along x = 100.125: was 0.25 for 3.5 mm with a 0.4 end piece.
#      0.4 from the pin down to y = 86.40 (0.4 clears GND pad U402.1 down to 86.42), 0.25 neck beside the pad,
#      0.4 again from the bend at (100.125, 87.645) (existing 0.4 diagonal into R441.1, untouched). Collinear pieces merged.
e = f.pt(100.55, 84.3495); k = f.pt(100.125, 84.7745); b = f.pt(100.125, 87.645); n = (100125000, 86400000)
f.replace(['5e17bc0d', 'f0b9a8c6'], [e, k, n], w=0.4)
f.replace(['8a2c528d'], [n, b])                                            # 0.25 neck, 1.245 mm (0.98 forced by the pad)
# ---- N2  P1_LDO_3V3 on F, R403.1 -> T (100.025, 81.1245): 0.2 between the 0.4 trunk and the 0.25 feed -> 0.25 like the feed
f.setw(['ef1ff3cd', '4d7eb7bc'], 0.25)
# ---- N3  PD_DRAIN port 1: pin 15 / pin 30 ties end well inside the exposed pad, the same form as port 2 (U501)
p = P('U401.15'); f.replace(['df624ac9'], [p, (p[0] + 625000, p[1]), (p[0] + 875000, p[1] + 250000)])
p = P('U401.30'); f.replace(['b78483c4'], [p, (p[0] - 625000, p[1]), (p[0] - 875000, p[1] + 250000)])
# ---- N4  I2CC_SDA port 1 on In3: 90 degree corner at (114.225, 86.5245) -> 45 with 0.4 mm legs
a = f.pt(114.225, 85.1245, 'In3'); c = f.pt(115.425, 86.5245, 'In3')
f.replace(['47058cdd', '95d3ceb5'], [a, (a[0], c[1] - 400000), (a[0] + 400000, c[1]), c])
# ---- N5  I2CC_SCL port 1 on In3 (solver-proven: corners only). Z with two 90 degree corners at x = 95.425 -> one 45 piece through
#      the middle of the old vertical; 90 degree corner + 0.25 mm piece at (96.675, 84.4745) -> the following diagonal starts 0.25 earlier;
#      90 degree corner below the T at (99.175, 83.9245) -> 45 branch with 0.3 mm legs.
v = V(94.375, 84.9245); d = f.pt(96.975, 83.9245, 'In3'); y1 = 84474500
f.replace(['6681599b', '66305081', '9421522d', 'ae02a745', '266ab79a'],
          [v, (95200000, v[1]), (95200000 + (v[1] - y1), y1), (d[0] - (y1 - d[1]), y1), d])
T = f.pt(99.175, 83.9245, 'In3'); r = f.pt(101.725, 84.2245, 'In3')
f.replace(['b246b0f3', '309942e5'], [T, (T[0] + (r[1] - T[1]), r[1]), r])
# ---- N6  PACK_P on F, C546.1 -> via (96.425, 85.8745): three pieces (0.12 straight, 45, straight) across the old y = 86 border -> two
p = P('C546.1'); v = V(96.425, 85.8745)
f.replace(['2ca10e30', 'e977944c', 'dffb6cd6'], [p, (v[0] - (p[1] - v[1]), p[1]), v])          # bend on the pad's centre line, 45 into the via centre

if __name__ == '__main__':
    ok = f.check('spec1.json', maxexc=0.8, out='after1_geo.json')
    g1 = G.load('after1_geo.json'); g0 = f.g
    ex = G.excursion(g0, g1)
    for k_, (d_, w_) in sorted(ex.items(), key=lambda kv: -kv[1][0]): print('  exc %.3f mm at %s  %s %s  class %s' % (d_, w_, k_[0], k_[1], g0['netclass'].get(k_[0], 'Default')))
