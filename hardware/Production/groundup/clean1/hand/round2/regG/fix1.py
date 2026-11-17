#!/usr/bin/env python3
# regG round-2 fixes. Rerunnable: python3 fix1.py  -> spec.json, after_geo.json
import sys
S='/tmp/clean1'
sys.path.insert(0,S+'/tools')
from fixlib import Fix
D=S+'/agents/regG/'
f=Fix(S+'/r2/geo.json',region=(100,120,121.5,137.5))
def N(x,y): return (int(round(x*1e6)),int(round(y*1e6)))
def V(x,y): return f.via(x,y,quiet=True)
SKIP=set(sys.argv[1:])
def spot(name):
    return name not in SKIP

# ---------------- F
if spot('F1'):   # CHG_G F: vertical ends 0.03 E of the via centre instead of a 0.14 jog (x limited by D103.1 clearance)
    a=V(99.925,124.3245); v=V(100.475,126.7745)
    f.replace(['3b6c24f3','421cb577','08c973a2'],[a,(100505000,a[1]),(100505000,v[1])])
if spot('F2'):   # CHG_G F via -> R110.1: jog hidden in the via (0.0695, needed for C114.2 clearance), one diagonal, end 0.03 from the pad centre on its centre line
    v=V(102.975,132.1245); p=f.pad('R110.1'); ex=p[0]-30000; sy=p[1]+(ex-v[0])
    f.replace(['8b5e49d0','8f7a24b9','590bab3d'],[v,(v[0],sy),(ex,p[1])])
if spot('F3'):   # U102-V1 blob in R122.2 / via: keep horizontal + one 45 into the via centre
    f.delete(['1734afb1','488a5dbf'])
if spot('F4'):   # U102-V1 via -> C115.1: one straight piece ending on the pad's vertical centre line
    v=V(103.325,134.2745); p=f.pad('C115.1')
    f.replace(['4187333b','a39e60a2'],[v,(p[0],v[1])])
if spot('F5'):   # U102-V2 off-angle piece
    a=f.pad('R121.2'); b=f.pad('C114.1')
    y=a[1]; x2=N(102.6,0)[0]; dy=y-b[1]
    f.replace(['63390b1d','a54a54ab','c6d4d505'],[a,(x2,y),(x2+dy,b[1]),b])
if spot('F6'):   # TS3 via -> J119.1: 45 first, then into the pad along its centre line
    v=V(102.275,136.6245); p=f.pad('J119.1'); d=v[1]-p[1]
    f.replace(['88e51c9c','cb2dcf7f'],[v,(v[0]+d,p[1]),p])
if spot('F7'):   # SWDIO into U301.20 from the top along the pad axis (as SWCLK next to it)
    a=f.pt(116.425,124.2245,'F'); p=f.pad('U301.20'); y2=N(0,125.1316)[1]; dx=p[0]-a[0]
    f.replace(['2d71223f','3c4d709b'],[a,(a[0],y2-dx),(p[0],y2),p])
if spot('F8'):   # NRST into U301.14 / via: L on the pad centre line
    a=f.pt(109.95,124.08,'F'); v=V(111.425,124.3745)
    f.replace(['153a8252','676a0a9a','720b35c5'],[a,(v[0],a[1]),v])
if spot('F9'):   # 3V3 via -> R313.1: bend outside the pad, straight entry
    v=V(107.425,124.3745); p=f.pad('R313.1'); dx=p[0]-v[0]
    f.replace(['e94759ba','9ab221f7'],[v,(p[0],v[1]+dx),p])
if spot('F10'):  # 3V3 via -> R314.1
    v=V(120.575,126.9745); p=f.pad('R314.1'); dx=p[0]-v[0]
    f.replace(['3867fde3','f3af30e3'],[v,(p[0],v[1]+dx),p])

if spot('F11'):  # Q104-G into Q104.1: step down outside the pad, enter along the pad centre line (was a bend inside the pad)
    a=f.pt(116.925,130.9245,'F'); p=f.pad('Q104.1'); d=p[1]-a[1]; x=N(118.0,0)[0]
    f.replace(['4678256d','0d3cf9c4'],[a,(x,a[1]),(x+d,p[1]),p])

# ---------------- In2
if spot('I2a'):  # CHG_G In2 wide run onto the via centre line (0.1 mm)
    a=V(100.475,126.7745); v=V(106.275,127.4245); d=v[1]-a[1]
    f.replace(['2556cd01','8b8cc703','697337aa'],[a,(a[0]+d,v[1]),v])
if spot('I2b'):  # CHG_INH In2 90 degree corner
    v=V(104.375,132.7245); e=f.pt(108.975,129.4745,'In2')
    f.replace(['646caf88','2fe8b498'],[v,(v[0],e[1]+400000),(v[0]+400000,e[1]),e])
if spot('I2c'):  # SDA In2: diag carried on, corners at 45
    a=f.pt(110.825,128.7245,'In2'); v=V(107.875,134.0745); y=N(0,129.9745)[1]
    f.replace(['92d87116','8d1849fa','ca045e90','5929407d'],[a,(a[0]-(y-a[1]),y),(v[0]+400000,y),(v[0],y+400000),v])
if spot('I2d'):  # NRST In2: three 90 degree corners
    a=f.pt(111.175,127.2745,'In2'); e=f.pt(112.575,132.1745,'In2'); y1=N(0,129.5245)[1]; x2=N(114.425,0)[0]; c=400000
    f.replace(['99dc4d92','5464b039','499798ca','b90e22b3'],[a,(a[0],y1-c),(a[0]+c,y1),(x2-c,y1),(x2,y1+c),(x2,e[1]-c),(x2-c,e[1]),e])
if spot('I2e'):  # SCL In2 tee + jog -> one fork
    t=f.pt(111.125,122.0745,'In2'); b=f.pt(112.025,122.9745,'In2'); e=f.pt(111.275,123.6745,'In2'); k=(e[0],t[1]+(e[0]-t[0]))
    f.replace(['6162ef5d','c07bb063','dde03a99','a60f878d'],[t,k,b])
    f.add('SCL','In2',200000,[k,e])
# I2f (3V3 In2 neck at via 114.475,120.1245): left as is, see report
if spot('I2g'):  # CELL_1N In2 ends in J120.1 -> pad centre
    v=V(104.975,134.3745); p=f.pad('J120.1'); dx=p[0]-v[0]
    f.replace(['b72c221c','b169ac05'],[v,(p[0],v[1]+dx),p])
    a=f.pt(106.225,136.6245,'In2'); dy=a[1]-p[1]
    f.replace(['6d7b476f'],[a,(a[0]-dy,p[1]),p])
if spot('I2h'):  # CELL_1N In2 ends in J118.1 -> pad centre
    a=f.pt(113.725,129.0245,'In2'); p=f.pad('J118.1'); dy=a[1]-p[1]
    f.replace(['8ffd24ff'],[a,(a[0]-dy,p[1]),p])
    b=f.pt(112.268,127.2315,'In2')
    f.add('/Cells and Gauge/CELL_1N','In2',200000,[b,p])

if spot('I2i'):  # 3V3 In2 (0.3): 90 degree corner + 0.85 E + short SE -> one diagonal
    a=f.pt(116.525,123.0245,'In2'); v=V(117.675,129.4745); y0=N(0,125.6745)[1]; dx=v[0]-a[0]
    f.replace(['4a5b8869','107d18d3','4fbfae8c','73b814f7'],[a,(a[0],y0),(v[0],y0+dx),v])

# ---------------- In3
if spot('I3a'):  # CELL_4P In3 into J116.1 centre (run moves 0.049)
    a=f.pt(105.875,135.1245,'In3'); p=f.pad('J116.1'); dy=p[1]-a[1]
    f.replace(['a334606b','ae7469bd'],[a,(a[0]+dy,p[1]),p])
if spot('I3b'):  # IRQ_N In3 hook round its own via
    a=f.pt(115.325,126.7245,'In3'); v=V(116.975,126.8745); y=N(0,127.2745)[1]
    f.replace(['d527061b','cc36cc37','1a9ae9a8'],[a,(a[0]+(y-a[1]),y),(v[0]-(y-v[1]),y),v])
if spot('I3c'):  # IRQ_N In3 two 90 degree corners
    a=f.pt(99.225,125.8745,'In3'); e=f.pt(105.275,127.2245,'In3'); x=N(101.275,0)[0]; c=400000
    f.replace(['9c53913f','11a391c5','ccceb06b'],[a,(x-c,a[1]),(x,a[1]+c),(x,e[1]-c),(x+c,e[1]),e])
if spot('I3d'):  # SDA In3 wiggle
    v=V(107.025,125.3745); e=f.pt(109.425,125.8745,'In3'); x1=N(107.875,0)[0]
    f.replace(['81cbf647','647154f6','5ec507ad','b222287f','b4f10c73','07339752'],[v,(x1,v[1]),(x1+(e[1]-v[1]),e[1]),e])
if spot('I3e'):  # GAUGE_FUSE In3: one diagonal, end 0.03 from the via centre
    a=V(110.275,121.3745); v=V(112.625,123.0745); ex=v[0]-30000; d=v[1]-a[1]
    f.replace(['f806a28c','2b8e3bbc','d388a3dc'],[a,(ex-d,a[1]),(ex,v[1])])
if spot('I3f'):  # Q104-G In3 V under a via -> flat bottom
    a=f.pt(109.575,134.6245,'In3'); e=f.pt(111.075,134.3245,'In3'); y=N(0,135.0745)[1]
    f.replace(['0f5e81a2','0bcded76'],[a,(a[0]+(y-a[1]),y),(e[0]-(y-e[1]),y),e])
if spot('I3g'):  # NRST In3 90 degree corner
    a=V(111.425,124.3745); v=V(116.025,121.8245); c=400000
    f.replace(['3f5f888e','dc6bd620'],[a,(v[0]-c,a[1]),(v[0],a[1]-c),v])

# ---------------- B
if spot('B1'):   # 3V3 B through the via centre
    a=f.pt(102.625,135.0245,'B'); m=V(106.225,133.8745); v=V(106.775,133.5245)
    f.replace(['8535610d','adafcb67'],[a,(m[0]-(a[1]-m[1]),a[1]),m,(m[0]+(m[1]-v[1]),v[1]),v])
if spot('B2'):   # TS2 B 90 degree peak -> flat top
    a=f.pt(110.875,124.0745,'B'); e=f.pt(114.046,126.2455,'B'); c=200000; y=a[1]-c
    k=f.pt(111.375,123.5745,'B')
    f.replace(['846a3592','ffdb16e3'],[a,(a[0]+c,y),(k[0]+(y-k[1]),y),e])

ok=f.check(D+'spec.json',maxexc=0.8,out=D+'after_geo.json')
print('OK' if ok else 'FAILED')
