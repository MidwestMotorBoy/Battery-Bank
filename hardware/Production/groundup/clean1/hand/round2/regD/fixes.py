#!/usr/bin/env python3
"""regD round-2 fixes: region x 79..100, y 103..120. Rerunnable: builds spec.json from r2/geo.json."""
import sys
S='/tmp/clean1'
D=S+'/agents/regD'
sys.path.insert(0, S+'/tools'); from fixlib import Fix
import io, contextlib
f = Fix(S+'/r2/geo.json', region=(79,103,100,120))
_id0 = f._id
def _id(i):
    # 4-character prefixes from dump.py: if a prefix is ambiguous on the whole board, take the one track inside the region
    if i in f.by: return i
    m = [k for k in f.by if k.startswith(i)]
    if len(m) > 1: m = [k for k in m if f._own(f.by[k])]
    if len(m) != 1: raise ValueError('id prefix %r matches %d tracks' % (i, len(m)))
    return m[0]
f._id = _id
def q(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()): return fn(*a)
via = lambda x, y: q(f.via, x, y)
pad = f.pad
def mm(p): return (p[0]/1e6, p[1]/1e6)
def P(x, y): return (int(round(x*1e6)), int(round(y*1e6)))
def off(p, dx, dy): return (p[0]+int(round(dx*1e6)), p[1]+int(round(dy*1e6)))

# ---- spot 1: ACN_F / ACP_F on F around C514 / U503.29,30 (Kelvin filter nets)
def spot_acn():
    c2 = pad('C514.2'); c1 = pad('C514.1'); u29 = pad('U503.29'); u30 = pad('U503.30'); c516 = pad('C516.1')
    # ACN_F feed: one diagonal from (81.45,107.15), straight down into the cap pad centre
    a = f.pt(81.45, 107.15, 'F')
    k = (c2[0], a[1] + (c2[0]-a[0]))
    f.replace(['3770ae20','27765f7e','f2752c0a'], [a, k, c2])
    # cap -> pin: 45 out of the cap centre, then straight into the pin; T for the C516 branch on the straight part
    b = (c2[0] + (u29[1]-c2[1]), u29[1])
    tx = P(84.125, 0)[0]; t = (tx, u29[1])
    f.replace(['440850ca'], [c2, b, t, u29])
    # branch to C516.1: up, 45, straight up into the pad centre
    y1 = P(0, 108.2745)[1]; d = c516[0]-tx
    f.replace(['97d40bed','ae37270e','480f24c2','803b922c'], [t, (tx, y1), (c516[0], y1-d), c516])
    # ACP_F: the via diagonal, the pin track and the track to C515 meet in one node on the cap pad's vertical centre line
    # (0.044 mm below the pad centre: the via and the pad are not on one diagonal)
    v = via(81.325, 108.4245); j = (c1[0], v[1] + (c1[0]-v[0]))
    f.replace(['1b6aadfe','fff37d96'], [v, j])
    e = f.pt(83.124, 111.4, 'F')
    f.replace(['d8deb4be'], [j, e])
    f.replace(['454ce5b8'], [u30, (c1[0] + (j[1]-u30[1]), u30[1]), j])


def cham(pts, legs):
    """pts: polyline (nm tuples); legs: {index of interior corner: leg in mm}. Returns the polyline with those 90 degree corners cut at 45."""
    out=[pts[0]]
    for i in range(1, len(pts)-1):
        L = legs.get(i)
        if not L: out.append(pts[i]); continue
        L = int(round(L*1e6)); p = pts[i]; a = pts[i-1]; b = pts[i+1]
        def step(q):
            dx = q[0]-p[0]; dy = q[1]-p[1]; assert dx == 0 or dy == 0, 'chamfer needs an axis-parallel leg'
            return (p[0] + (L if dx > 0 else -L if dx < 0 else 0), p[1] + (L if dy > 0 else -L if dy < 0 else 0))
        out += [step(a), step(b)]
    out.append(pts[-1]); return out

# ---- F layer
def spot_btst2():      # BTST2: the two diagonals at C513.1 were 0.07 mm out of line; one straight diagonal with its node on the pad's centre line
    a = f.pt(90.264, 107.801, 'F'); e = f.pt(90.87, 105.454, 'F')
    d = e[0]-a[0]
    f.replace(['d923fe2b','f694','e9ec'], [a, (e[0], a[1]-d), e])

def spot_drvsup_c511():   # DRV_SUP at C511.1 / U503.23: pin track and via track both end on the pad's centre line; the bypass link below the pad goes
    c = pad('C511.1'); u = pad('U503.23')
    f.replace(['185e15e7','e95a3b36'], [u, (u[0], c[1]+10000)])      # 0.01 below the centre line: keeps the move at 0.29 mm
    a = f.pt(88.375, 106.7745, 'F')
    f.replace(['4331'], [a, (a[0], c[1])])
    f.delete(['1862','a91dbd5a'])

def spot_drvsup_d511():   # DRV_SUP at D511.1: leave the pad centre straight, no jog inside the pad
    p = pad('D511.1'); e = f.pt(100.025, 112.7745, 'F'); d = e[1]-p[1]
    f.replace(['4d29','63fd','ba51'], [p, (e[0]-d, p[1]), e])

def spot_regn_pin():      # REGN U503.24 -> via: one straight (0.01 mm off the pin centre, clearance to C512.1) and one 45 into the via
    v = via(87.475, 105.0745); u = pad('U503.24'); x = P(87.574, 0)[0]
    f.replace(['49279ead','c2327484','8218aa3e'], [v, (x, v[1] + (x-v[0])), (x, u[1])])

def spot_srn_r529():      # SRN_F R529.2 -> via: straight out of the pad, one 45 into the via
    p = pad('R529.2'); v = via(92.975, 106.8745); d = v[0]-p[0]
    f.replace(['0967','f0ab','da7d','402f7138'], [p, (p[0], v[1]-d), v])

def spot_srn_c517():      # SRN_F into C517.2: straight in at the pad centre height instead of the dip below the pad
    a = f.pt(95.625, 111.5745, 'F'); c = pad('C517.2'); d = c[1]-a[1]
    f.replace(['ba60','a871','1de2','cf03','ee21'], [a, (a[0]-d, c[1]), c])

def spot_srp_via():       # SRP_F: the pin track passed over its via 0.17 mm off centre; route pin -> via centre -> pad centre
    u = pad('U503.14'); v = via(91.925, 111.3245); c = pad('C517.1')
    d1 = u[1]-v[1]; d2 = v[1]-c[1]
    f.replace(['fa49','4ced'], [u, (v[0]-d1, u[1]), v, (c[0]-d2, v[1]), c])

def spot_vc4():           # NOT USED: the jog is forced, y=120.0 is 0.10 mm from the VC3 via (clearance 0.15)
    a = f.pt(94.2505, 120.0, 'F'); c = pad('C101.1'); d = a[1]-c[1]
    f.replace(['1397','8095','a6db'], [a, (c[0]+d, a[1]), c])

def spot_batsns():        # BAT_SNS_P: the 45 ended on the corner of R528.1; extend it to the pad centre
    a = f.pt(94.274, 103.71, 'F'); f.replace(['5a07865a'], [a, pad('R528.1')])

def spot_packp_tap():     # PACK_P into R527.2: two collinear pieces -> one (same geometry)
    f.replace(['8feb798d','6b3a3931'], [f.pt(94.874, 105.15, 'F'), f.pt(94.284, 105.15, 'F')])

def spot_packp_tie():     # PACK_P via (96.45,104.9): V-shaped stub -> one 45 piece from the via centre into pad R527.2
    v = via(96.45, 104.9); f.replace(['299a500e','5f692749'], [v, off(v, -0.3, 0.3)])

def spot_fetmid():        # FET_MID R106.1 -> via: '<' of two diagonals -> straight up and a short 45 inside the via
    a = f.pt(100.01, 115.2095, 'F'); v = via(99.925, 114.7245); d = a[0]-v[0]
    f.replace(['02e29bef','c850e2ae'], [a, (a[0], v[1]+d), v])

def spot_lodrv2():        # NOT USED (gate drive, lead said keep; it would lengthen the track by 0.012 mm). LODRV2: 0.15 mm neck past C510.2 -> the run moved 0.015 mm away from the pad so that 0.2 mm fits; one width R547.1 -> U503.21
    r = pad('R547.1'); x = P(89.66, 0)[0]; e = f.pt(89.065, 108.45, 'F'); d = x-e[0]
    f.replace(['411381f9','cf51','c0216b3b','bb32a052','f73b'], [r, (x, r[1] + (x-r[0])), (x, e[1]-d), e], w=0.2)

def spot_3v3_r517():      # NOT USED (tried, looked no better: the 0.25 mm 45 piece of a 0.4 mm track shows between via and pad). 3V3 (0.4 mm) into R517.2: ran along the top edge of the pad and turned inside it; 45 out of the via, straight in on the centre line
    v = via(94.775, 112.6745); c = pad('R517.2'); d = c[1]-v[1]
    f.replace(['35e1','61ab'], [v, (v[0]-d, c[1]), c])

def spot_cell4p_d101():   # CELL_4P into D101.2: arrived 0.15 mm above the pad centre and turned inside the pad; now straight in on the centre line
    a = f.pt(91.625, 116.8245, 'F'); c = pad('D101.2'); d = a[1]-c[1]
    f.replace(['0b17','f11c','928d'], [a, (a[0]+d, c[1]), c])

# ---- In2
def spot_ts4_in2():
    p = [f.pt(94.05,108.45,'In2'), f.pt(94.05,109.85,'In2'), f.pt(92.1,111.8,'In2'), f.pt(89.775,111.8,'In2'), f.pt(89.775,113.3745,'In2'),
         f.pt(90.625,113.3745,'In2'), f.pt(90.625,115.9245,'In2'), f.pt(89.475,115.9245,'In2'), f.pt(89.475,122.3245,'In2')]
    h1 = (p[5][0]-p[4][0])//2; h2 = (p[6][0]-p[7][0])//2
    n = [p[2]] + cham([p[2], p[3], p[4]], {1: 0.4})[1:3] + [(p[4][0], p[4][1]-h1), (p[5][0], p[5][1]+h1), (p[6][0], p[6][1]-h2), (p[7][0], p[7][1]+h2), p[8]]
    f.replace(['5b9f','264e','f132','5d59','5cdf','f672'], n)

def spot_scl1_in2():
    p = [f.pt(94.975,103.9745,'In2'), f.pt(93.575,103.9745,'In2'), f.pt(93.575,106.9245,'In2'), f.pt(93.425,107.0745,'In2'), f.pt(93.425,107.7745,'In2'),
         f.pt(96.525,107.7745,'In2'), f.pt(96.525,113.2745,'In2')]
    f.replace(['06d2','036d','987b','7ccd','64d0','39a1'], cham(p, {1: 0.4, 4: 0.35, 5: 0.4}))

def spot_scl2_in2():
    p = [f.pt(85.375,113.986,'In2'), f.pt(85.375,109.6245,'In2'), f.pt(83.025,109.6245,'In2'), via(83.025,102.0245)]
    f.replace(['4cf8','c83e','8621'], cham(p, {1: 0.4, 2: 0.4}))

def spot_pphv_in2():
    p = [via(84.375,114.9745), f.pt(83.525,114.9745,'In2'), via(83.525,116.6245)]
    f.replace(['a395','96ed'], cham(p, {1: 0.4}))

def spot_regn_in2():
    p = [via(87.625,104.4745), f.pt(88.325,104.4745,'In2'), f.pt(88.325,105.0745,'In2')]
    f.replace(['697a','3c08'], cham(p, {1: 0.3}))
    p = [f.pt(88.325,109.2245,'In2'), f.pt(84.825,109.2245,'In2'), f.pt(84.825,106.3245,'In2')]
    f.replace(['9ef2','85c8'], cham(p, {1: 0.4}))

def spot_u506fb_in2():
    p = [via(96.075,113.6745), f.pt(96.075,108.5245,'In2'), via(94.725,108.5245)]
    f.replace(['9dd7','a987'], cham(p, {1: 0.4}))

# ---- In3
def spot_cell3_in3():
    p = [f.pt(92.475,117.2245,'In3'), f.pt(93.425,117.2245,'In3'), f.pt(93.425,115.1745,'In3'), f.pt(96.675,115.1745,'In3'), f.pt(96.675,114.3745,'In3')]
    f.replace(['12c8','ba8e','d158','b078'], cham(p, {1: 0.4, 2: 0.4, 3: 0.35}))
    p = [f.pt(97.775,113.2745,'In3'), f.pt(97.775,112.3245,'In3'), f.pt(98.725,112.3245,'In3')]
    f.replace(['c861','dbfa'], cham(p, {1: 0.3}))

def spot_cell1n_in3():    # (a single 45 would leave the old line by 0.47 mm; HighCurrent net, limit 0.30)
    p = [f.pt(82.525,112.0245,'In3'), f.pt(93.825,112.0245,'In3'), f.pt(93.825,112.9745,'In3')]
    f.replace(['5073','0f83'], cham(p, {1: 0.4}))

def spot_ts1_in3():
    p = [f.pt(81.775,116.3745,'In3'), f.pt(81.775,119.1745,'In3'), f.pt(88.175,119.1745,'In3')]
    f.replace(['ccec','d44c'], cham(p, {1: 0.4}))

def spot_drvsup_in3():
    p = [f.pt(100.025,110.8245,'In3'), f.pt(90.175,110.8245,'In3'), f.pt(90.175,109.4245,'In3'), f.pt(88.825,109.4245,'In3'), via(88.825,106.3245)]
    f.replace(['2479','1207','b057','1122'], cham(p, {1: 0.4, 2: 0.4, 3: 0.4}))

def spot_srn_in3():
    p = [f.pt(94.375,109.4745,'In3'), f.pt(92.975,109.4745,'In3'), f.pt(92.975,108.3745,'In3')]
    f.replace(['2867','591c'], cham(p, {1: 0.4}))

def spot_packp_in3():
    p = [via(79.525,106.7745), f.pt(82.425,106.7745,'In3'), via(82.425,105.8245)]
    f.replace(['8893','add7'], cham(p, {1: 0.4}))

# ---- B
def spot_cell1n_b():      # CELL_1N to TH101.2: ended on the pad corner; 45 out of the via, straight into the pad centre
    v = via(82.425,112.1245); c = pad('TH101.2'); d = v[1]-c[1]
    f.replace(['6e24','7e67aa96'], [v, (v[0]+d, c[1]), c])

def spot_ts_b():          # TS: 0.15 mm side-step in a vertical run
    a = f.pt(92.75,107.7995,'B'); e = f.pt(92.4255,110.5245,'B'); d = a[0]-e[0]
    f.replace(['d1b3','0d8b','b49b','4fa6'], [a, (a[0], e[1]-d), e])

def spot_gnd_b():         # GND C211.2 -> via: 18 degree piece -> straight, 45, straight (balanced, 0.21 mm from the old line)
    c = pad('C211.2'); v = via(99.525,107.3245); d = v[1]-c[1]; h = (v[0]-c[0]-d)//2
    f.replace(['15fe86ea'], [c, (c[0]+h, c[1]), (c[0]+h+d, v[1]), v])

def spot_pack_b():        # U101-PACK: 0.05 mm step inside a long diagonal between two vias; one diagonal centred between them
    a = f.pt(95.425,116.5245,'B'); v = via(97.425,119.7245); k = (a[0], P(0,117.7995)[1]); d = v[1]-k[1]
    f.replace(['0fa1','2d160f9d','726c28e6','eb345398','89494670'], [a, k, (k[0]+d, v[1]), v])

# ---- In4
def spot_en5v2_in4():     # EN_5V2: 0.15 mm side-step in a diagonal, moved into the corner before it
    a = f.pt(97.45,116.1,'In4'); e = f.pt(99.8,117.6,'In4'); d = e[1]-a[1]
    f.replace(['588c','216b2b43','d4775fd4'], [a, (e[0]-d, a[1]), e])

SPOTS = [spot_acn, spot_btst2, spot_drvsup_c511, spot_drvsup_d511, spot_regn_pin, spot_srn_r529, spot_srn_c517, spot_srp_via, spot_batsns,
         spot_packp_tap, spot_packp_tie, spot_fetmid, spot_cell4p_d101,
         spot_ts4_in2, spot_scl1_in2, spot_scl2_in2, spot_pphv_in2, spot_regn_in2, spot_u506fb_in2,
         spot_cell3_in3, spot_cell1n_in3, spot_ts1_in3, spot_drvsup_in3, spot_srn_in3, spot_packp_in3,
         spot_cell1n_b, spot_ts_b, spot_gnd_b, spot_pack_b, spot_en5v2_in4]
if __name__ == '__main__':
    only = sys.argv[1:]
    for s in SPOTS:
        if only and s.__name__ not in only and not (only[0] == '-x' and s.__name__ not in only): continue
        try: s()
        except Exception as e: print('SPOT', s.__name__, 'ERROR', e); raise
    ok = f.check(D+'/spec.json', maxexc=0.8, out=D+'/after_geo.json')
    print('OK' if ok else 'FAILED', len(f.dele), 'del', len(f.adds), 'add')
