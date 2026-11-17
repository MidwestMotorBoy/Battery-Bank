#!/usr/bin/env python3
"""regF round 2 fixes. Run: python3 fix1.py  -> spec.json, after_geo.json"""
import sys, json
S = '/tmp/clean1'
sys.path.insert(0, S + '/tools')
from fixlib import Fix
D = S + '/agents/regF/'
f = Fix(S + '/r2/geo.json', region=(79, 120, 100, 137.5))
SKIP = set(sys.argv[1:])
def spot(name):
    return name not in SKIP

# ---------------- F ----------------
if spot('sw3v3'):   # SW_3V3 U204.9 -> L201.1: two off-angle pieces -> one straight H on the pin's centre line, widths as before
    p = f.pad('U204.9'); L = f.pad('L201.1')
    f.replace(['0cac7fe5', '41bda556'], [p, (84575000, p[1])])
    f.replace(['2129f215'], [(84575000, p[1]), (L[0], p[1] + (L[0] - 84575000))])       # 0.8 piece inside the pad, ends on its centre line
if 0 and spot('btp'):   # REJECTED: x = 97.9 is 0.225 from CELL_1N (needs 0.25)
    pass
if 0:     # BTP_INT via -> U101.15: one straight V on the pin centre line (via 0.025 off)
    p = f.pad('U101.15'); v = f.via(97.925, 122.3245)
    f.replace(['394c5c0a', '95a419af'], [p, (p[0], v[1])])
if 0 and spot('ts1'):   # REJECTED: an end at the pad centre is 0.20 from the CELL_1N end in U101.9 (needs 0.25)
    pass
if 0:     # TS1 via -> U101.10
    p = f.pad('U101.10'); v = f.via(95.875, 122.3245)
    f.replace(['e6f15ca5'], [p, (p[0], v[1])])
if 0:   # REJECTED: an end at the pad centre of U101.16 is 0.225 from the BTP_INT end in U101.15 (needs 0.25); r1 stopped it short on purpose     # CELL_1N U101.16 -> via
    p = f.pad('U101.16'); v = f.via(98.175, 124.4245)
    f.replace(['37d4c763', 'a1da1978'], [p, (p[0], v[1] - (p[0] - v[0])), v])
if spot('u9'):      # CELL_1N via -> U101.9 as one diagonal with a 90 degree T for the branch
    v = f.via(94.425, 124.0245); p = f.pad('U101.9'); br = f.pt(95.675, 124.4245, 'F')
    e = (p[0], v[1] - (p[0] - v[0]))                       # on the pad's centre line
    s = (br[0] - br[1]); J = ((v[0] + v[1] + s) // 2, (v[0] + v[1] - s) // 2)
    assert (v[0] + v[1] + s) % 2 == 0
    f.replace(['6896c860', '5201ab59', 'a6f931d2', '44628b61', '752f56bd'], [v, J, e])
    f.replace(['5c8f4379'], [J, br])
if spot('r123'):    # CELL_4P R119.1 -> via in R123.2
    a = f.pad('R119.1'); v = f.via(96.175, 129.7245)
    f.replace(['02cf79be', '9146865f', '5ec6c020'], f.L(a, v, first='diag'))
if spot('srn'):     # SRN: pin -> via (hidden 45 jog at the via), via -> C106.2 straight
    pin = f.pad('U101.6'); v = f.via(93.825, 121.5245); c = f.pad('C106.2')
    f.replace(['4207cdbc', '800671d9', 'eb88a019'], [pin, (v[0] + (pin[1] - v[1]), pin[1]), v])
    f.add('/Cells and Gauge/SRN', 'F', 0.2, [v, (c[0], v[1])])
if spot('srp'):     # SRP at C106.1: micro pieces + dogleg -> V out of the pad on its centre line, one 45 onto the long diagonal
    c = f.pad('C106.1'); b = f.pt(93.025, 123.4245, 'F')
    f.replace(['618d2726', '0ad631b9', 'e8b99aa3'], [c, (c[0], b[1] - (c[0] - b[0])), b])
if spot('vc3'):     # VC3: node at the via the track passes
    t = f.by[f._id('61fa913f')]; v = f.via(93.825, 120.4245)
    f.split('61fa913f', (v[0], t['y1']))
if spot('vc2'):     # VC2 at C103.1: track along the pad's lower edge -> into the pad centre from below; via in the pad corner joined by an L inside the pad
    A = f.via(91.825, 123.3745); B = f.via(92.375, 123.0745); c = f.pad('C103.1')
    f.replace(['455c3697'], [A, (c[0], A[1] - (c[0] - A[0])), c])
    f.replace(['9ba74443'], [c, (B[0], c[1]), B])
if spot('v4'):      # U102-V4: one straight H pin -> R119.2 -> C112.1 (0.02 off both centres)
    pin = f.pad('U102.2'); r = f.pad('R119.2'); c = f.pad('C112.1'); y = 131230000
    f.replace(['1bca7914', 'fb03d91d', '2d82900f', '911de132'], [(pin[0], y), (r[0], y), (c[0], y), c])
if spot('vdd'):     # U102-VDD: acute V at R123.1 -> straight H R123.1 -> pin with C116.1 on a 90 degree T
    pin = f.pad('U102.1'); r = f.pad('R123.1'); c = f.pad('C116.1'); y = 130730000
    f.replace(['bfae91b4', '77988eb5', 'b91de07e'], [(r[0], y), (c[0], y), (pin[0], y)])
    f.replace(['302dc5b0'], [c, (c[0], y)])
if spot('c110'):    # Net-(C110-Pad2): via -> pad centre line
    v = f.via(98.725, 127.3745); c = f.pad('C110.2')
    f.replace(['bb70a883'], [v, (v[0] + (c[1] - v[1]), c[1])])
if spot('packp'):   # PACK_P C111.2 -> via (91.3,130.4): stair at the pad -> one H; hook at the via -> V in line + hidden jog
    c = f.pad('C111.2'); v = f.via(91.3, 130.4); xv = 91225000
    m = f.pt(91.95, 129.3, 'F'); h = f.pt(91.5, 129.3, 'F')            # the H jog round the CELL_1N via stays (forced by H101 / that via)
    f.replace(['68e5a6e3', 'e2240bcf', 'e691f091', 'a4f678b4'], [c, (m[0] + (m[1] - c[1]), c[1]), m])
    f.replace(['b1a501dc', '1b5ca3b0', '2ca780c8'], [h, (xv, h[1] + (h[0] - xv)), (xv, v[1] - (v[0] - xv)), v])
if spot('tp301'):   # 3V3 via -> TP301.1: copper outside the pad kept (0.4 to the via, 0.8 blob), inside the pad one 0.8 H ending on the pad's centre line
    c = f.pad('TP301.1'); a = f.pt(88.575, 122.5245, 'F')
    f.replace(['54da8a05', 'cbc2b7df'], [a, (c[0], a[1])])
if spot('gndtiny'): # GND: 0.035 mm off-angle piece between a pad centre and the via inside that pad
    f.delete(['3cb402c4'])

# ---------------- In2 ----------------
if spot('vc1in2'):  # VC1: acute junction + staircase -> straight diagonal via-via with a 45 branch
    q = f.pt(94.275, 119.6745, 'In2'); R = f.via(95.575, 121.1745); pb = f.pt(93.625, 120.9245, 'In2')
    q2 = (q[0], R[1] - (R[0] - q[0])); T = (R[0] - (R[1] - pb[1]), pb[1])
    f.replace(['699c2c75', 'ff68fafc', '826fa1d1'], [q, q2, T, R])
    f.replace(['7d1a84be', 'aefc45d8', 'bb1000db'], [pb, T])
if 0:   # REJECTED: x = 92.925 is 0.125 from the H101 slot (needs 0.2)  # TS3: vertical in line with the via instead of a 0.2 jog at the via
    a = f.pt(93.425, 126.5745, 'In2'); v = f.via(92.925, 129.2245)
    f.replace(['a91bc600', 'a3a3aed7', 'fd7ae319'], [a, (v[0], a[1] + (a[0] - v[0])), v])
if spot('ts4in2'):  # TS4 0.15: 90 degree corner -> 45
    a = f.pt(89.475, 122.3245, 'In2'); v = f.via(90.275, 124.3745)
    f.replace(['a4807af3', '83580778', 'fe040b1d'], [a, (v[0], a[1] + (v[0] - a[0])), v])
if spot('cell3in2'):  # CELL3: 90 degree corner in open plane -> 45
    a = f.pt(86.825, 118.1745, 'In2'); v = f.via(88.325, 133.7745); c = 400000
    f.replace(['b4c77ef9', 'f8d52254'], [a, (a[0], v[1] - c), (a[0] + c, v[1]), v])
if spot('j115'):    # CELL_1N -> J115.1: end at the pad centre
    a = f.pt(90.725, 132.0745, 'In2'); p = f.pad('J115.1')
    f.replace(['96626557'], [a, (a[0], p[1] - (p[0] - a[0])), p])

if spot('c1nin2'):  # CELL_1N: 0.15 mm nick at a 90 degree turn -> a proper 45 (0.4)
    v = f.via(91.725, 129.8745); e = f.pt(90.425, 131.7745, 'In2'); c = 400000
    f.replace(['49b217f2', '69ea0dd1', 'bced87c5'], [v, (e[0] + c, v[1]), (e[0], v[1] + c), e])

# ---------------- B ----------------
if spot('btpB'):    # BTP_INT: hook at the junction -> 90 degree T
    a = f.pt(96.525, 120.5745, 'B'); b = f.pt(96.875, 120.9245, 'B'); e = f.pt(94.925, 122.5745, 'B')
    s = a[0] - a[1]; k = e[0] + e[1]; T = ((k + s) // 2, (k - s) // 2); assert (k + s) % 2 == 0
    f.replace(['e3686891'], [a, T, b])
    f.replace(['9cceac56', 'eaf82baa'], [T, e], w=200000)
if spot('j110'):    # CELL2 -> J110.1: the long diagonal runs straight on into the pad, bend inside the pad, end at the pad centre
    a = f.pt(95.325, 130.2745, 'B'); p = f.pad('J110.1')
    f.replace(['f99703ce', '11394312'], [a, (p[0], a[1] + (p[0] - a[0])), p])
if 0:   # REJECTED: the shifted diagonal is 0.154 from CELL2 (needs 0.25)    # TS3: long diagonal in line with the via
    a = f.pt(96.875, 132.9245, 'B'); v = f.via(92.925, 129.2245)
    f.replace(['275d07b4', '5b578a18', '16a139cf'], [a, (v[0] + (a[1] - v[1]), a[1]), v])
if spot('v33B'):    # 3V3 0.15: 0.1 mm jog removed, one vertical at x = 98.225 (0.15 to the vias on both sides)
    a = f.pt(97.55, 124.65, 'B'); J = f.pt(97.3503, 130.3997, 'B'); x = 98225000
    f.replace(['0e402df4', '625ef4d0', 'a8c8cfd0', '852ee6a0', '72a97481'], [a, (x, a[1] + (x - a[0])), (x, J[1] - (x - J[0])), J])

# ---------------- In3 ----------------
if spot('x1n'):     # CELL_1N four-way blob -> one + node between four vias
    A = f.via(91.275, 124.4745); B = f.via(92.075, 125.1245); C = f.via(94.425, 124.0245); Dv = f.via(91.725, 124.0245)
    N = (Dv[0], A[1])
    f.replace(['f0a8f70e', 'fadb9c7c', '5ad14426', '92a43e24'], [Dv, N, (N[0], B[1] - (B[0] - N[0])), B])
    f.replace(['36448be5', '97bc899c'], [A, N])
    f.replace(['fa3d22ea', '521a7b55', '8c571265'], [N, (C[0] - (N[1] - C[1]), N[1]), C])
if spot('irq'):     # IRQ_N: two small jogs and a 90 degree corner -> straight H and a 45
    a = f.pt(94.575, 123.3245, 'In3'); b = f.pt(88.625, 120.9745, 'In3'); c = 300000
    f.replace(['66bb944a', 'a2b4c4fe', '8e886de3', 'bffce587', 'fdbf9688', '55e18b56'], [a, (a[0], b[1] + c), (a[0] - c, b[1]), b])
if spot('cell1in3'):  # CELL1: Z with two 90 degree corners -> one diagonal
    a = f.pt(101.075, 130.9745, 'In3'); b = f.pt(92.675, 132.1245, 'In3'); x = 97075000; h = b[1] - a[1]
    f.replace(['73c18ca3', '39b43c25', 'a9eff3e3'], [a, (x + h // 2, a[1]), (x - h // 2, b[1]), b])
if spot('cell3in3'):  # CELL3: two 90 degree corners -> 45 (0.25: the lower one wraps the corner of pad J114.1)
    a = f.pt(97.075, 135.6245, 'In3'); b = f.pt(90.375, 134.4245, 'In3'); x = 94275000; c = 250000
    f.replace(['62b8e74a', 'cfa47dc2', 'caabbc5d'], [a, (x + c, a[1]), (x, a[1] - c), (x, b[1] + c), (x - c, b[1]), b])
if spot('cellp'):   # CELL_P: staircase -> one diagonal and one H
    a = f.pt(97.875, 127.5745, 'In3'); b = f.pt(99.725, 128.0745, 'In3')
    f.replace(['dfb1a18d', 'c30ad894', 'bf1c4757', 'f002de90', 'e43124f6'], [a, (a[0] + (b[1] - a[1]), b[1]), b])

if __name__ == '__main__':
    ok = f.check(D + 'spec.json', maxexc=0.8, out=D + 'after_geo.json')
    print('OK' if ok else 'FAIL')
