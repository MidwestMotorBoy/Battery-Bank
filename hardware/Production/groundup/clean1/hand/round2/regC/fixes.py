#!/usr/bin/env python3
# regC: all fixes, against r2/geo.json.  python3 fixes.py  -> spec.json, after_geo.json, chk output
import sys
S='/tmp/clean1'
sys.path.insert(0,S+'/tools'); from fixlib import Fix
U=1000000
def mm(v): return int(round(v*U))
def batch_F(f):
    q=True
    # S1 ACN_F (Kelvin, filtered side) into R526.2: off-angle pad escape -> one 45 deg piece hidden in the pad.
    #    The run is lifted 0.0095 mm so that the bend lies wholly inside the pad; the point where the track leaves the pad moves 0.015 mm.
    p=f.pad('R526.2'); a=f.pt(79.575,88.8245,'F'); y=mm(87.365)
    f.replace(['a398f888','d34fb2e1','a749e517'],[a,(a[0]+(a[1]-y),y),(p[0]-(y-p[1]),y),p])
    # S2 SS_5V: diagonal ends on the centre of C539.1 (bend moved 0.13 mm down the vertical), no 0.13 mm piece in the pad
    p=f.pad('C539.1'); a=f.pt(93.775,87.0745,'F')
    f.replace(['23625673','1d9706c5','ea36493f'],[a,(a[0],p[1]-(p[0]-a[0])),p])
    # S3 P1_LDO_3V3: one 45 deg piece into the centre of R441.1 (was 45 + off-angle); the forced 0.25 neck ends at the bend
    p=f.pad('R441.1'); a=f.pt(100.125,85.0745,'F'); b=(a[0],p[1]-(p[0]-a[0]))
    f.replace(['776a3d61'],[a,b])
    f.replace(['8ea0404b','6fc6d722'],[b,p])
    # S5 GND R432.2 -> via: straight into the via centre; the 0.125 mm offset is taken up on the pad's centre line inside the pad
    p=f.pad('R432.2'); v=f.via(116.325,86.8745,q)
    f.replace(['161e2e58','b61a502e'],[p,(p[0],v[1]),v])
    # S6 PACK_P at TP106: the 0.25 branch meets the 0.5 trunk at one point on the pad's centre line; fat 0.225 stub and 0.15 stub removed
    v=f.via(101.075,91.75,q); j=f.pt(100.3,92.1495,'F')
    f.replace(['13ea63b9','7c3e18f8'],[v,(j[0]+(j[1]-v[1]),v[1]),j])
    f.delete(['7d24f4cc'])
    # S9 GND thermistor pads -> via: one 45 deg piece hidden in the pad; the straight run ends 0.0145 mm from the via centre (tolerance 0.03)
    for pad,ids,vx in (('TH501.2',['08e294d4','e2af05a2'],87.225),('TH401.2',['f73e2d75','7be9defc'],110.251)):
        p=f.pad(pad); v=f.via(vx,102.4245,q); y=mm(102.41)
        f.replace(ids,[p,(p[0]+(y-p[1]),y),(v[0],y)])
    # S10 GND C538.2 / C438.2 -> via in pad: the track now runs over the centre of the GND via it used to clip at its edge
    for pad,ids,v2x,v1x in (('C538.2',['194ad8bc','1eaed92f','287089ca'],89.4,89.374),('C438.2',['b77060fa','3756d03d','f156c325'],112.426,112.4)):
        p=f.pad(pad); v2=f.via(v2x,98.83,q); v1=f.via(v1x,98.15,q); c=(v2[0],v1[1])
        f.replace(ids,[v2,c,(c[0]+(c[1]-p[1]),p[1]),p])
    # S11 REGN: no 0.08 mm piece at the pad, diagonal straight from the pad centre
    a=f.pt(105.82,102.35,'F'); v=f.via(106.625,102.0245,q)
    f.replace(['e25da370','b92daf8c','62cfd336'],[a,(a[0]+(a[1]-v[1]),v[1]),v])
    # S7 Q509-D: staircase (90 deg corner + 0.3 mm flat) -> one 45; bend 0.03 mm inside U506.5 for clearance to Q409.2
    a=f.pt(98.325,96.9745,'F'); p=f.pad('U506.5'); yb=mm(102.1545)
    f.replace(['f34a8258','159ac6eb','3d8cd9b5','deb31513'],[a,(a[0],yb-(p[0]-a[0])),(p[0],yb),p])
def batch_B(f):
    # S22 SBU_FLT on B: clean 45 deg entry into the via (was a 0.21 mm hook); cannot go straight in: PPHV (HighCurrent) 0.25 mm rule
    v0=f.via(101.725,87.7245,True); v1=f.via(104.075,86.3745,True); y=v1[1]+300000
    f.replace(['c6bb5764','8cbb4340','5e4051a1'],[v0,(v0[0]+(v0[1]-y),y),(v1[0]-300000,y),v1])
def batch_In2(f):
    # I1 I2CC_SCL (port 1) on In2: eight 90 deg corners -> 45s (three jogs become one diagonal each, two corners get 0.3 mm chamfers)
    a=f.pt(94.225,87.375,'In2'); b=f.pt(94.975,103.9745,'In2')
    pts=[a,(94.225,87.9495),(94.575,88.2995),(94.575,90.6745),(94.075,91.1745),(94.075,93.7245),(94.375,94.0245),(95.475,94.0245),
         (95.775,94.3245),(95.775,96.4745),(94.975,97.2745),b]
    f.replace(['cab40618','c924e3c8','215b7638','e9ef7cce','928e648d','e9a6f875','7f4c208a','0bb3e856','947cb780'],pts)
    # I2 REGN (port 2) on In2: 90 deg corner -> 45
    a=f.pt(93.575,103.4745,'In2'); v=f.via(95.275,96.2245,True)
    f.replace(['5ad4f467','ffe71e58'],[a,(a[0],v[1]+300000),(a[0]+300000,v[1]),v])
    # I3 CELL3 on In2: first of two 90 deg corners -> 45 (the second corner is the end of a track of the region below)
    a=f.pt(98.025,96.2745,'In2'); b=f.pt(98.925,101.1245,'In2')
    f.replace(['2e58ecf4','ddffec8e'],[a,(a[0],b[1]-300000),(a[0]+300000,b[1]),b])
    # I4 EN_5V1 on In2: two 90 deg corners and a 0.3 mm stub -> the existing diagonal extended down to the vertical
    a=f.pt(115.325,103.2,'In2'); b=f.pt(116.975,99.6745,'In2'); y=mm(100.7745)
    f.replace(['f8d46ba2','1883da34','a1ac2e76','4b50469c'],[a,(a[0],b[1]+(b[0]-a[0])),b])
    # I5 DRV9_OFF on In2: two 90 deg corners -> 45 (legs 0.4 mm)
    a=f.pt(102.925,97.0245,'In2'); b=f.pt(112.125,85.9245,'In2'); y=mm(88.6745)
    f.replace(['125902f9','5d263e08','0e737c0b'],[a,(a[0],y+400000),(a[0]+400000,y),(b[0]-400000,y),(b[0],y-400000),b])
if __name__=='__main__':
    f=Fix(S+'/r2/geo.json',region=(79,86,121.5,103))
    which=sys.argv[1] if len(sys.argv)>1 else 'FBI'
    if 'F' in which: batch_F(f)
    if 'B' in which: batch_B(f)
    if 'I' in which: batch_In2(f)
    out=S+'/agents/regC/'
    f.check(out+'spec.json',maxexc=0.8,out=out+'after_geo.json')
