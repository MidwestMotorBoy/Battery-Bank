#!/usr/bin/env python3
"""regB round 2 fixes, against r2/geo.json. Rerunnable: python3 fix1.py  -> spec.json, after_geo.json"""
import sys
S = '/tmp/clean1'
D = S + '/agents/regB'
sys.path.insert(0, S + '/tools'); from fixlib import Fix
f = Fix(S + '/r2/geo.json', region=(100, 69, 121.5, 86))
def nm(x, y): return (int(round(x * 1e6)), int(round(y * 1e6)))
LDO = '/P1_LDO_3V3'

# ---- F1  LDO: C452.1 blob, off-angle 0.3 track to U405.10, neck to via (101.525,75.5745)
c452 = f.pad('C452.1'); vA = f.via(102.975, 74.7245); vB = f.via(101.525, 75.5745)
# cap -> via under pin 10: one 45 piece up-right, then straight into the via (old: 2.1 mm off-angle track to the pin centre)
f.replace(['015508d0'], [c452, (c452[0] + (c452[1] - vA[1]), vA[1]), vA])                 # 0.3
# pin 10 neck: the 0.5 stub from the via stops 0.15 short of pad 9 (clearance); 0.3 straight on to the pad's centre line
f.replace(['655ba998'], [f.pt(102.975, 74.2245), (vA[0], f.pad('U405.10')[1])])               # 0.3
# cap -> via (101.525,75.5745): one 45 piece (ends 0.0145 mm off the via centre), one width
# (ends 0.0205 mm left of the via centre, at the via's y: CC2 below is exactly 0.15 away, as before)
d = vB[1] - c452[1]
f.replace(['9bd33278', 'a830aaf9'], [c452, (c452[0] + d, c452[1] + d)], w=0.5)

# ---- F2  LDO: U402.8 blob
# feed from the upper left and the 0.25 track to the lower left both end on the pad's long centre line, 0.05 below centre
# (the feed's 45 line passes 0.035 from the pad centre; the junction it starts from belongs to the next region and stays)
j = f.pt(99.775, 83.5745); u8 = f.pad('U402.8'); e = (u8[0], j[1] + (u8[0] - j[0]))
a = nm(100.35, 84.1495)
assert a[1] - j[1] == a[0] - j[0] and e[1] - j[1] == e[0] - j[0]
f.replace(['0e19ff92', '64bb6508'], [j, a])                                                   # 0.6 feed, one 45 piece
f.replace(['19e4a319'], [a, e])                                                               # 0.4 neck (pad 7 is 0.15 away), collinear, 0.283 long (was 0.285)
# lower track: straight on up from the end of the x = 100.125 track, then one 45 piece into the pad. It lies left of the
# old copper, so the GND pour neck under pad U402.7 does not get thinner (a vertical at the pad axis made it 0.02 mm thinner).
k = f.pt(100.125, 85.0745)
f.replace(['a93ff7e5', 'a8cee9d9', '21893a15'], [k, (k[0], e[1] + (e[0] - k[0])), e])       # 0.25

# ---- F3  LDO: R403.1, branch to R404.1 becomes a 90 degree T on the 0.4 trunk
r404 = f.pad('R404.1'); t = nm(100.405, 79.575)
f.replace(['b30f2549', '1aa4b188'], [r404, t])                                                # 0.3
f.split('89624f43', t)

# ---- F4  LDO: C404.1
c404 = f.pad('C404.1'); v1 = f.via(105.625, 74.7245); v2 = f.via(106.825, 77.0245); u1 = f.pad('U401.1')
f.replace(['a6cd3dff', '4daba5a5', '58f4b69a'], [v1, (c404[0], v1[1] + (c404[0] - v1[0])), c404])        # 0.3, jog hidden in the pad
f.replace(['7f10380e', 'f52fa343'], [v2, (c404[0], v2[1])])                                              # 0.5, via stub straight in, T on the pad's centre line
f.replace(['9aa105d7'], [c404, (c404[0], v2[1]), (c404[0], u1[1] - (c404[0] - u1[0])), u1])              # 0.6, straight down then 45 into pin 1

# ---- F5  3V3: via (107.725,75.4745) -> C403.1 one straight 45 line, T to U401.38 on it
v3 = f.via(107.725, 75.4745); c403 = f.pad('C403.1'); bot = f.pt(108.275, 78.35)
tt = (bot[0], v3[1] + (bot[0] - v3[0])); en = (v3[0] + (c403[1] - v3[1]), c403[1])           # ends 0.0245 mm left of the pad centre
f.replace(['ad29679b', 'dd3bab27'], [v3, tt], w=0.3)
f.replace(['812d4665', '8d98cd3f', '286a0ff2'], [tt, en], w=0.3)
f.replace(['3b38efb8'], [bot, tt])

# ---- F6  PACK_P: pin U404.3 -> via -> via in C446.1, one straight line at x = 115.200
pA = f.via(115.225, 85.3245); pB = f.via(115.175, 85.9245); u3 = f.pad('U404.3'); x = (pA[0] + pB[0]) // 2
f.replace(['e06c5da9', 'b3028da9', '39556191', '36eba7ff', 'e48f1a2c'], [(x, u3[1]), (x, pA[1]), (x, pB[1])])

# ---- F7  PPHV: via -> R424.1, stub removed, two collinear pieces merged
pv = f.via(104.925, 85.7745)
f.replace(['aabc57b5', '1579e49a', '05e54f3e'], [pv, f.pt(105.312, 85.3875)])

# ---- F8  SBU_FLT on F: pin 19 -> one 45 line -> down; via branch joins as a 90 degree T
u19 = f.pad('U401.19'); sv = f.via(102.375, 83.2745); lo = f.pt(102.575, 85.9245)
c = u19[0] + u19[1]                                # x + y of the new line
tx = (c - (sv[1] - sv[0])) // 2; T = (tx, c - tx)
assert (c - (sv[1] - sv[0])) % 2 == 0
f.replace(['c614f03b', '8ad18ae8', '72fe273f', '9daa74df', '3d581a00', 'aff0483c'], [u19, T, (lo[0], c - lo[0]), lo])
f.replace(['75f5a8a1', '21cca5ce', 'b7bf8e5a'], [sv, T])

# ---- F9  C_CC1: jog moved into the first via, 45 corner before pin 4
ca = f.via(102.525, 71.7245); cb = f.via(102.925, 71.2245); u4 = f.pad('U405.4')
f.replace(['1e387324', 'a6262874'], [ca, (ca[0], cb[1] + (cb[0] - ca[0])), cb])
f.replace(['9d8f98ee', 'dd08963a'], [cb, (u4[0] - 250000, cb[1]), (u4[0], cb[1] + 250000), u4])

# ---- F10 VBIAS: the 90 degree peak over pins 2 and 1 becomes a flat with 45 corners
u3b = f.pad('U405.3'); vv = f.via(105.625, 71.9745); y1 = 71349500; y0 = y1 - 200000
f.replace(['8eb60775', '8a2a78d0', 'acc13255', '0c724e96'], [u3b, (u3b[0], y1), (u3b[0] + 200000, y0), (vv[0] - 200000, y0), (vv[0], y1), vv])

# ---- F11 CELL3 on In2: end at the centre of J111.1 instead of inside its rim
j1 = f.pad('J111.1'); b0 = f.pt(113.625, 75.9745, 'In2')
yb = 70224500
f.replace(['21f70389'], [b0, (b0[0], yb), (j1[0], yb - (j1[0] - b0[0])), j1])

# ---- F12 SDA on In4: jog at the via made short enough to sit inside the via
s0 = f.pt(100.9, 80.8, 'In4'); sv4 = f.via(102.725, 75.9245)
yy = 77650000
f.replace(['8d7d3f5a', '4c3ff5c9', 'ae14bcbb'], [s0, (s0[0], yy), (s0[0] + (yy - sv4[1]), sv4[1]), sv4])

# ---- F13 (SBU_FLT on B at via 102.375,83.2745: shortening the jog brings the track within 0.25 of the PPHV via; left as is)

# ---- F14 I2CC_SCL on In3: 90 corner -> 45, bump of 0.15 removed
p0 = f.pt(104.225, 82.4245, 'In3'); p1 = f.pt(102.175, 83.7745, 'In3')
f.replace(['e184751d', 'e7028805', 'bd6570d8', 'ba6fa015'], [p0, (p0[0], p1[1] - 200000), (p0[0] - 200000, p1[1]), p1])

# ---- F15 I2CC_SDA on In3: 90 corner -> 45
q0 = f.pt(105.475, 81.7745, 'In3'); q1 = f.pt(107.725, 83.9245, 'In3')
f.replace(['9cb9eb5f', '44c34f80'], [q0, (q1[0] - 300000, q0[1]), (q1[0], q0[1] + 300000), q1])

# ---- F16 VBIAS on In3: 90 corner -> 45
w0 = f.via(101.525, 73.1245); w1 = f.pt(105.375, 72.2245, 'In3')
f.replace(['36225606', 'f694f4bc'], [w0, (w0[0], w1[1] + 300000), (w0[0] + 300000, w1[1]), w1])

# ---- F17 LDO on In3: two 90 corners -> 45 (0.25 legs)
l0 = f.via(113.125, 74.4745); l1 = f.pt(106.825, 77.0245, 'In3'); xc = 114425000; kk = 250000
f.replace(['6edc0e93', '896ae54c', '5ad0e073'], [l0, (xc - kk, l0[1]), (xc, l0[1] + kk), (xc, l1[1] - kk), (xc - kk, l1[1]), l1])

# ---- F18 CC1 on In3: 90 corner -> 45
m0 = f.pt(102.525, 77.8245, 'In3'); m1 = f.pt(111.625, 80.9745, 'In3')
f.replace(['0049dd91', '9e94e5e2'], [m0, (m1[0] - 300000, m0[1]), (m1[0], m0[1] + 300000), m1])

# ---- F19 PP5V on In2: Z with two 90 corners -> one 45 piece
n0 = f.via(111.625, 86.0245); n1 = f.pt(112.125, 80.3745, 'In2'); ny = 84924500
f.replace(['91b2dd1a', '7b067019', 'fa5b9979'], [n0, (n0[0], ny + (n1[0] - n0[0])), (n1[0], ny), n1])

# ---- F20 90 degree hooks inside pads -> one 45 degree piece inside the pad (only where the pad hides the whole jog;
#      the same change at U404.8, R403.2, C402.2, C446.2 would put the bend at the pad/via rim, so those stay)
# E2(a, c): a = far end (exact), c = pad centre; the straight piece keeps its line, the last piece becomes a 45
E2 = lambda a, c: [a, (c[0] + (1 if a[0] > c[0] else -1) * abs(a[1] - c[1]), a[1]), c] if abs(a[0] - c[0]) > abs(a[1] - c[1]) else [a, (a[0], c[1] + (1 if a[1] > c[1] else -1) * abs(a[0] - c[0])), c]
f.replace(['6ca40235', '3b765ef8'], E2(f.pt(110.575, 69.0245, 'F'), f.pad('J401.A1')))
f.replace(['185c2e21', '8031a17f'], E2(f.via(108.7, 80.9), f.pad('U401.32')))

# ---- (CC2 at C402.1: the short straight + 45 out of the pad stays; a 45 straight from the pad centre would bend inside the pad corner)

ok = f.check(D + '/spec.json', maxexc=0.8, out=D + '/after_geo.json')
print('OK' if ok else 'FAILED')
import geolib as G, json
g1 = G.load(D + '/after_geo.json'); ex = G.excursion(f.g, g1)
for k, v in sorted(ex.items(), key=lambda kv: -kv[1][0]):
    if v[0] > 0.05: print('  excursion %.3f  %s %s  class %s  at %s' % (v[0], k[0], k[1], f.g['netclass'].get(k[0]), v[1]))
