#!/usr/bin/env python3
# regC batch 1: F and B spots
import sys
S='/tmp/clean1'
sys.path.insert(0,S+'/tools'); from fixlib import Fix
def batch1(f):
    q=True
    # S1 ACN_F pad escape into R526.2: 45 deg piece inside the pad, tap exit point at the pad edge unchanged (0.025 mm)
    p=f.pad('R526.2'); a=f.pt(81.025,87.3745,'F')
    f.replace(['a749e517','d34fb2e1'],[a,(p[0]-(a[1]-p[1]),a[1]),p])
    # S2 SS_5V: diagonal ends on the centre of C539.1 (bend moved 0.13 mm up the vertical)
    p=f.pad('C539.1'); a=f.pt(93.775,87.0745,'F')
    f.replace(['23625673','1d9706c5','ea36493f'],[a,(a[0],p[1]-(p[0]-a[0])),p])
    # S3 P1_LDO_3V3: one 45 deg piece into the centre of R441.1 (was 45 + off-angle); the forced 0.25 neck ends at the bend
    p=f.pad('R441.1'); a=f.pt(100.125,85.0745,'F'); b=(a[0],p[1]-(p[0]-a[0]))
    f.replace(['776a3d61'],[a,b])
    f.replace(['8ea0404b','6fc6d722'],[b,p])
    # S4 AC_SNS_N: end extended inside R424.2 to the pad's vertical centre line (tap exit point unchanged)
    p=f.pad('R424.2'); a=f.pt(104.85,86.85,'F')
    f.replace(['bcac7f70'],[a,(p[0],a[1])])
    # S5 GND R432.2 -> via: bend hidden in the pad, straight into the via centre
    p=f.pad('R432.2'); v=f.via(116.325,86.8745,q)
    f.replace(['161e2e58','b61a502e'],[p,(p[0]+(p[1]-v[1]),v[1]),v])
    # S6 PACK_P at TP106: the 0.25 branch joins the 0.5 trunk at its end on the pad centre line (one node), no fat stub
    v=f.via(101.075,91.75,q); j=f.pt(100.3,92.1495,'F')
    f.replace(['13ea63b9','7c3e18f8'],[v,(v[0]-(j[1]-v[1]),j[1]),j])
    # S9 GND thermistor pads -> via: bend hidden in the pad
    for pad,ids,vx in (('TH501.2',['08e294d4','e2af05a2'],87.225),('TH401.2',['f73e2d75','7be9defc'],110.251)):
        p=f.pad(pad); v=f.via(vx,102.4245,q)
        f.replace(ids,[p,(p[0]+(v[1]-p[1]),v[1]),v])
    # S10 GND C538.2 / C438.2 -> via in pad: the track now runs over the centre of the GND via it used to clip
    for pad,ids,v2x,v1x in (('C538.2',['194ad8bc','1eaed92f','287089ca'],89.4,89.374),('C438.2',['b77060fa','3756d03d','f156c325'],112.426,112.4)):
        p=f.pad(pad); v2=f.via(v2x,98.83,q); v1=f.via(v1x,98.15,q); c=(v2[0],v1[1])
        f.replace(ids,[v2,c,(c[0]+(c[1]-p[1]),p[1]),p])
    # S11 REGN: no 0.08 mm piece at the pad, diagonal straight from the centre of the pad
    a=f.pt(105.82,102.35,'F'); v=f.via(106.625,102.0245,q)
    f.replace(['e25da370','b92daf8c','62cfd336'],[a,(a[0]+(a[1]-v[1]),v[1]),v])
    # S22 SBU_FLT on B: clean 45 deg entry into the via (was a 0.21 mm hook)
    v0=f.via(101.725,87.7245,q); v1=f.via(104.075,86.3745,q); y=v1[1]+300000
    f.replace(['c6bb5764','8cbb4340','5e4051a1'],[v0,(v0[0]+(v0[1]-y),y),(v1[0]-300000,y),v1])
def s7(f,dy=0):
    # S7 Q509-D: staircase (90 deg corner + 0.3 mm flat) -> one 45
    a=f.pt(98.325,96.9745,'F'); p=f.pad('U506.5'); d=int(dy*1e6)
    f.replace(['f34a8258','159ac6eb','3d8cd9b5','deb31513'],[a,(a[0],p[1]-725500-1000000+d),(p[0],p[1]-725500+d),p])
if __name__=='__main__':
    f=Fix(S+'/r2/geo.json',region=(79,86,121.5,103))
    batch1(f); s7(f,float(sys.argv[1]) if len(sys.argv)>1 else 0)
    f.check(S+'/agents/regC/spec1.json',maxexc=0.8,out=S+'/agents/regC/after1.json')
