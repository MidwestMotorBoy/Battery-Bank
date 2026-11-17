#!/usr/bin/env python3
# regE fixes, batch 1. Run: python3 fix1.py  -> spec.json, after_geo.json
import sys
S = '/tmp/clean1'
sys.path.insert(0, S + '/tools')
from fixlib import Fix
D = S + '/agents/regE/'
f = Fix(S + '/r2/geo.json', region=(100, 103, 121.5, 120))
def o(p, dx, dy): return (p[0] + int(round(dx * 1e6)), p[1] + int(round(dy * 1e6)))
def X(p, q): return (p[0], q[1])          # x of p, y of q
V = lambda x, y: f.via(x, y, quiet=True)
P = f.pad

def batch_3v3():
    A = V(114.325, 113.7245); B = V(113.925, 114.1745); C = V(114.525, 114.3245); Dv = V(114.025, 114.8245); Fv = V(113.45, 118.2)
    kA = (C[0], A[1] + (C[0] - A[0]))                      # 45 degree corner between A and C
    # F: A -> C as diag + vertical (was an L with its corner inside via A)
    f.replace(['ccdeea0b', '14b22db8'], [A, kA, C])
    # F: C301.1 -> C303.1 -> C302.1 one straight column, 0.4 throughout (was 0.4 / 0.021 jog / 0.25 neck)
    c1 = P('C301.1'); c3 = P('C303.1'); c2 = P('C302.1')
    f.replace(['8b1541df', 'a87e4055', 'addae3ac', 'dc245ad8'], [c1, (c3[0], c1[1] + (c1[0] - c3[0])), c3, c2], w=0.4)
    # F: via -> R417.2 with a 45 degree jog instead of a 90
    v = V(117.825, 112.7245); r = P('R417.2')
    f.replace(['c2f3e6a6', '783c6892'], [v, (v[0] - (r[1] - v[1]), r[1]), r])
    # In2: the 3V3 feed redrawn on the same line as on F: A - C - corner - T - neck, T - D
    f.delete(['ef7bdc10', '2fb32efa', 'ed2f52d9', '67d3ecff', 'c59696b4', '08429ca8', 'f615468c', 'df509198', 'db295f0b'])
    k2 = o(C, 0, 0.7); T = o(k2, -0.15, 0.15); n0 = o(k2, -0.6, 0.6); tee = f.pt(113.725, 117.5745, 'In2')
    f.add('3V3', 'In2', 0.6, [A, kA, C, k2, T, n0])
    f.add('3V3', 'In2', 0.5, [T, Dv])
    f.add('3V3', 'In2', 0.3, [n0, o(n0, 0, 0.8), (tee[0], n0[1] + 800000 + (n0[0] - tee[0])), tee])
    # In3 (inside the 3V3 pour): stitch pieces B-C, B-A and the tie stub, all from the via centre
    f.delete(['37ba1241', '0c65d209', '848544e6', '50996557', '21747d37', 'dfc063e5'])
    f.add('3V3', 'In3', 0.6, [B, o(B, 0.15, 0.15), C])      # same shape as the F piece
    f.add('3V3', 'In3', 0.6, [A, kA, C])                    # same shape as on F and In2 (was an off-angle 0.8 stub from B that only overlapped via A)
    f.add('3V3', 'In3', 0.3, [B, o(B, -0.2, -0.2)])
    v = V(117.825, 112.7245)
    f.replace(['e46ed6f5', '642d48b4'], [v, o(v, -0.2, -0.2)])
    # B: via - via link, one width 0.3 (was 0.8 off-angle / 0.2 / 0.3), run moved 0.05 up to clear the GND via at 0.3
    v1 = V(111.475, 117.6245)
    f.delete(['9789abe8', '55913b10', '5853bfeb'])
    y = 117825000
    f.add('3V3', 'B', 0.3, [v1, (v1[0] + (y - v1[1]), y), (Fv[0] - (Fv[1] - y), y), Fv])

batch_3v3()

def jog(a, b, first='diag'):
    """a -> b with one 45 degree piece and one straight piece (exact nm)."""
    return Fix.L(a, b, first=first)

def batch_F_top():
    # REGN: pin U403.24 straight up to via V1 (hidden 45 jog into the via), V1 -> C410.1 on the pad's centre line; pad -> V2 kept
    pin = P('U403.24'); V1 = V(110.675, 104.3245); c = P('C410.1')
    f.delete(['19b964f3', '4f89c1f4', 'a69a3646', '126ae043', '29b31f95', '321ea3cc', 'a79e8bf6', 'd2bd6c36'])
    x = 110603000                                          # 0.013 off the pin centre: 0.153 to C412.1, and the jog sits inside via V1
    f.add('/USB Port 1/REGN', 'F', 0.2, [(x, pin[1]), (x, V1[1] + (V1[0] - x)), V1])
    f.add('/USB Port 1/REGN', 'F', 0.2, [V1, (V1[0] + (V1[1] - c[1]), c[1]), c])
    # DRV_SUP into C411.1: end on the pad's horizontal centre line
    c = P('C411.1'); t = f.pt(111.091, 108.3245, 'F')
    f.replace(['e94a0280'], [t, (t[0], c[1])])
    # LODRV2 at R447.1: the 45 leaves the pad centre (no 0.06 stub)
    # (left as it is: the 0.06 mm piece on the pad centre line keeps the bend outside the pad)
    # SW2 via -> C413.2: 45 jog instead of a 0.064 mm 90 degree hook
    v = V(113.226, 106.0); c = P('C413.2')
    f.replace(['1592716c', '29f86fb5'], jog(v, c, 'straight'))
    # DRV_SUP via -> D405.2
    v = V(113.825, 104.3245); d = P('D405.2')
    f.replace(['6f1ffeb6', 'fbae7630'], jog(v, d, 'diag'))
    # SRP_F via -> R428.2
    v = V(115.825, 104.3245); r = P('R428.2')
    f.replace(['384c805b', '5415b144'], jog(v, r, 'diag'))
    # BAT_SNS_P: the diagonal runs on to the centre of R428.1 (ended on the pad corner)
    # and the 45 / 0.36 vertical / 45 staircase becomes one 45 that enters the pad along its centre line. Tap node (117.6, 103.05) unchanged.
    r = P('R428.1'); t = f.pt(117.6, 103.05, 'F')
    f.replace(['9646825f', 'e44cdf02', 'cd3e48b1'], [t, (r[0], t[1] + (t[0] - r[0])), r])
    # GND via -> C419.2
    # BTST1 via -> D404.1
    v = V(108.476, 104.71); d = P('D404.1')
    f.replace(['a40705d0', '4de8c183'], jog(v, d, 'straight'))
    # REGN via -> D410.2
    v = V(107.125, 104.2745); d = P('D410.2')
    f.replace(['c6ac0308', '5e9bd0ce'], jog(v, d, 'straight'))

def batch_F_mid():
    # SRP_F pin 14 -> C417.1: was one 8.7 degree slanted piece; now pin escape, 45, straight between the two SRN_F vias, 45 into the pad centre
    pin = P('U403.14'); c = P('C417.1'); v = V(115.775, 111.0245)
    y = 111340000
    a = (114070000, pin[1]); b = (a[0] + (pin[1] - y), y); d = (c[0] - (y - c[1]), y)
    f.replace(['050439fe'], [pin, a, b, d, c])
    f.replace(['75af1279', '94257e01'], jog(v, c, 'straight'))
    # FB: flatten the bump after the via
    v = V(114.425, 112.6745); e = f.pt(115.925, 112.7245, 'F')
    f.replace(['02d35fa7', 'addbacf7', '9043d03e', '08a3f2de'], jog(v, e, 'diag'))
    # FBG via -> pin 11
    # PPHV via -> pin 33
    # ACUV pin 34: 0.15 only next to the PPHV via, 0.2 up to there
    pin = P('U403.34'); t = f.pt(107.3405, 111.99, 'F'); m = (107690000, pin[1])
    f.delete(['b6aed809'])
    f.add('Net-(U403-ACUV)', 'F', 0.2, [t, m]); f.add('Net-(U403-ACUV)', 'F', 0.15, [m, pin])
    # ACN_F: C416.1 -> tee without the dent
    c = P('C416.1'); t = f.pt(107.725, 108.2245, 'F')
    e = (c[0], 107420000)                                  # leave the pad along its centre line, then one 45
    f.replace(['8b01f265', 'cc8b4ab5', '6e80c179', 'c0436b9b'], [c, e, (t[0], e[1] + (c[0] - t[0])), t])
    # ACN_F: C414.2 leaves the pad centre on the 45
    # U406 FB: both ends on the pad centres with one 45 each
    a = P('U406.2'); x = 102175000; t = f.pt(102.175, 110.4245, 'F')
    f.replace(['d2fa9dde', 'f6921141'], [a, (x, a[1] + (x - a[0])), t])

def batch_F_low():
    # SRN_F R429 pad -> long vertical: one 45 instead of 45 / 0.29 vertical / 45
    a = f.pt(115.59, 105.65, 'F'); e = f.pt(114.926, 109.3, 'F')
    f.replace(['4df2c3b2', 'da1aedee', '337aab5b', '645ea617'], [a, (e[0], a[1] + (a[0] - e[0])), e])
    # PPHV C409.1 -> R409.1: one 45 and one vertical instead of stub / 45 / vertical / 45 / stub
    a = P('C409.1'); b = P('R409.1')
    f.replace(['8b1699d5', 'fef4b40a', '7c7ad367', 'dd3f91a0', 'a1ecf9c0'], [a, (b[0], a[1] + (a[0] - b[0])), b])
    # ACN_F into pin 36: the 45 runs straight through the tee point to the pin (was 45 / 0.25 horizontal / 45)
    a = f.pt(106.475, 108.9745, 'F'); tee = f.pt(107.725, 109.275, 'F'); pin = f.pt(107.94, 109.49, 'F')
    f.replace(['2724b3f2', 'ad69e188', '2d1f80c9', 'db2ee53b'], [a, (tee[0] - (tee[1] - a[1]), a[1]), tee, pin])
    # DRV_SUP at Q? pad (102.85, 112.2): leave the pad along its centre line, then the long 45 (was 45 through the pad corner + 0.6 mm horizontal)
    a = f.pt(102.85, 112.2, 'F'); e = f.pt(105.575, 110.0745, 'F')
    f.replace(['2d9c2238', 'bbf81e17', 'b41eaf01'], [a, (e[0] - (a[1] - e[1]), a[1]), e])
    # (REGN 0.16 mm step at (108.2-108.4, 119.97) left: one straight 45 would pass R411.2 (GND) at 0.126 mm)
    # SDA R305.2 -> U301.10: was one 29 degree piece
    a = P('R305.2'); b = P('U301.10'); x1 = 110300000
    f.replace(['89ca4da6'], [a, (x1, a[1]), (x1 + (b[1] - a[1]), b[1]), b])
    # GND via -> U301.8: 45 between the 3V3 via and pad 9, ends on the pad's centre line
    v = V(112.871, 118.373); u = P('U301.8'); s = (112959000, v[1])
    f.replace(['f8327444'], [v, s, (u[0], s[1] + (u[0] - s[0]))])
    # ACOV via -> R411.1
    v = V(108.225, 118.3245); r = P('R411.1')
    f.replace(['144c2e21', '1f1c05c0'], jog(v, r, 'diag'))
    # UART_TX via -> J301.6
    v = V(119.075, 114.3745); j = P('J301.6')
    f.replace(['27e219d9', '7fc18971'], jog(v, j, 'straight'))

batch_F_top(); batch_F_mid(); batch_F_low()

def batch_inner():
    # In2 ACP_F: drop the 0.2 mm horizontal step just before the via (the 0.55 mm one above it gets 0.75 long)
    a = f.pt(104.55, 107.8, 'In2'); v = V(107.125, 109.6245)
    f.replace(['5e256920', 'e8067c3a', '82f399e1', 'a07bba66'], [a, (v[0] - (v[1] - a[1]), a[1]), v])
    # In2 CE_N: 90 degree peak -> chamfer
    a = f.pt(112.125, 113.9245, 'In2'); b = f.pt(114.125, 113.1245, 'In2'); pk = f.pt(113.525, 112.5245, 'In2')
    f.replace(['f99863ff', '8b6b3fb1'], [a, o(pk, -0.2, 0.2), o(pk, 0.2, 0.2), b])
    # In2 FB: 90 degree corner + 0.2 mm piece -> one 45
    a = f.pt(116.425, 112.2245, 'In2'); b = f.pt(116.85, 110.0495, 'In2')
    f.replace(['3a0a4ea7', '854f4a36', 'a3eda611'], [a, (a[0], b[1] + (b[0] - a[0])), b])
    # In2 REGN: the branch that ran 0.25 mm under its own trunk for 1.2 mm now tees off the trunk; the 90 degree corners get a 0.3 mm chamfer
    t = f.pt(110.125, 115.0245, 'In2'); n = (110125000, 109174500)
    f.delete(['26b67db6', '837f6ced'])
    f.replace(['40631f83'], [t, n])
    a = f.pt(107.775, 105.9745, 'In2'); k1 = f.pt(107.775, 109.1745, 'In2'); b = f.pt(111.325, 105.0745, 'In2'); k2 = f.pt(111.325, 109.1745, 'In2')
    f.replace(['59521d8c', 'd92506fa', 'c615e8b8'], [a, o(k1, 0, -0.3), o(k1, 0.3, 0), n, o(k2, -0.3, 0), o(k2, 0, -0.3), b])
    v1 = V(110.675, 104.3245); k = f.pt(110.675, 105.0745, 'In2')
    f.replace(['a746d67c', '9e4fcebc'], [v1, o(k, 0, -0.2), o(k, 0.2, 0), b])
    # In3 FET_MID: 90 degree corner -> 0.3 mm chamfer
    a = f.pt(99.925, 114.7245, 'In3'); k = f.pt(100.975, 114.7245, 'In3'); v = V(100.975, 117.0245)
    f.replace(['c92578ee', '57c5c9d9'], [a, o(k, -0.3, 0), o(k, 0, 0.3), v])
    # In3 SRN_F: via -> via without the V detour
    v = V(114.825, 110.7745); b = f.pt(114.375, 111.2245, 'In3')
    f.replace(['795cc36c', '700a79bc', 'ebddc1a0'], [v, b])
    # In3 SRP_F: via exit without the bump, and the 90/90 staircase replaced by the 45 that was already there, made longer
    v = V(115.825, 104.3245); e = f.pt(117.475, 108.5745, 'In3'); x = 115925000
    f.replace(['fa398a98', 'd9d957ef', '8e8bc4ca', '2e28677d', 'e36691d1', '904c4786', '89b9bcb4', 'cce3a06b'],
              [v, (x, v[1] + (x - v[0])), (x, e[1] - (e[0] - x)), e])
    # (In3 DRV_SUP 90 degree corner at (112.625, 104.3245) left: sensitive net, the 45 version would move it 0.27 mm)
    # B TS4: the diagonal runs on to the centre line of TH104.1 (ended on the pad corner)
    a = f.pt(114.875, 112.3245, 'B'); p = P('TH104.1')
    x = p[0] - 20000                                        # 0.02 short of the centre line keeps the in-pad extension under 0.30 mm (TS4 is a sensitive net)
    f.replace(['2e09c770'], [a, (x, a[1] + (x - a[0]))])

batch_inner()

def batch_corners():
    # 90 degree corners in open space on the inner layers -> 45 (all moves under 0.30 mm; these nets are sensitive, nothing else of them is touched)
    q = lambda x, y, l: (int(round(x * 1e6)), int(round(y * 1e6)))
    # In2 EN_5V1 corner (112.65, 103.2): 0.3 mm chamfer
    f.replace(['0e39e25f', 'ce8b9149'], [q(115.325, 103.2, 0), q(112.95, 103.2, 0), q(112.65, 103.5, 0), q(112.65, 105.0, 0)])
    # In2 EN_5V1 staircase (112.65,110.4745) / (111.625,110.4745) / (111.625,112.9745) / (111.075,112.9745):
    # two 0.3 mm chamfers on the upper step, the lower 0.55 mm step becomes one 45 (drawn below the old step, away from the GND via at 110.84,112.54)
    f.replace(['fe4b0ed5', '91ae0ab9', '3ab9c738', '5c9f4b06', 'c62f56f3'],
              [q(112.65, 109.4, 0), q(112.65, 110.1745, 0), q(112.35, 110.4745, 0), q(111.925, 110.4745, 0), q(111.625, 110.7745, 0),
               q(111.625, 112.9745, 0), q(111.075, 113.5245, 0), q(111.075, 114.3245, 0)])
    # In3 I2CC_SCL: the 45 from the left runs on to the long horizontal (was 45 / 0.55 vertical / 90); the 0.4 mm 90/90 step becomes a 45;
    # the corner at (107.375, 113.2745) gets a 0.3 mm chamfer
    f.replace(['e9d97143', '237661ea', '0dfb0ae9', '1427f9a2', '58a70c09', '1a168915'],
              [q(100.225, 113.7245, 0), q(101.075, 112.8745, 0), q(105.975, 112.8745, 0), q(106.375, 113.2745, 0),
               q(107.075, 113.2745, 0), q(107.375, 113.5745, 0), q(107.375, 113.9745, 0)])
    # In3 DRV_SUP: the existing 45 made longer instead of 90 + 0.55 vertical + 45
    f.replace(['5d43043e', 'ab464908', '252d2e31'], [V(113.825, 104.3245), q(113.175, 104.3245, 0), q(112.325, 105.1745, 0)])

batch_corners()
if __name__ == '__main__':
    ok = f.check(D + 'spec.json', maxexc=0.8, out=D + 'after_geo.json')
    print('OK' if ok else 'FAILED')
