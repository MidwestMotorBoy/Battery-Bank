# regA round 2: hand fixes in x 79..100, y 69..86 (against r2/geo.json).  python3 fix.py  -> spec.json, after_geo.json, chk.txt
import sys; sys.path.insert(0,'.')
from mylib import *
f=Fix(BASE,region=REG)
V=lambda x,y: f.via(x,y,quiet=True)
P=f.pad
CHK=[]   # (net, layer, w, pts) to print gaps for
def rep(ids,pts,**kw):
    f.replace(ids,pts,**kw); t=f.by[f._id(ids[0])]
    CHK.append((kw.get('net',t['net']),kw.get('l',t['l']),(kw['w'] if 'w' in kw else t['w']*MM),pts))

# ---- S1 CC1: U505.12 -> via -> C501.1 (off-angle pad escape, tee_unsplit, two ends inside the via)
p=P('U505.12'); v=V(95.525,75.4745); c=P('C501.1')
vv=(v[0]+20000,v[1])                      # both F tracks end 0.02 mm beside the via centre: the diagonal then clears C502.1 by 0.156 without a jog
rep(['b838f7c8','337833f1','9528f5cd'],[p,(p[0],vv[1]-(vv[0]-p[0])),vv])
rep(['16300256'],[vv,(vv[0]+(c[1]-vv[1]),c[1])])
# ---- S2 CC2: via -> C502.1, one diagonal from the via centre to the pad's centre line
v=V(94.975,75.8245); c=P('C502.1')
rep(['bc602f89','4a4eb654','3ac6a54d'],[v,(v[0]+(c[1]-v[1]),c[1])])
# ---- S3 CHG_INT: R504.2 / U501.18 (0.077 mm jog inside the pad)
u=P('U501.18'); r=P('R504.2'); a=f.pt(79.325,85.1245)
rep(['8468632c','1bd7c332','eea71f11','27692d5b'],[a,(a[0],u[1]+(r[0]-a[0])),(r[0],u[1]),u])
# ---- S4 C_CC1: exact centre of U505.4; 45 degree corner before U505.7
t=f.pt(94.75,70.1995); p=P('U505.4')
rep(['5075016c','869929e1'],[t,(p[0],t[1]+(p[0]-t[0])),p])
a=f.pt(93.575,71.3745); p=P('U505.7')
rep(['4ba9d16b','8ad05709'],[a,(a[0],p[1]-250000),(a[0]+250000,p[1]),p])
# ---- S5 DRV9_OFF: leave R555.2 from its centre; one node for the T
p=P('R555.2'); T=(89.175,76.0245); e1=f.pt(89.775,75.4245); e2=f.pt(89.175,78.6245)
rep(['ecc948e7','79251a02','ba725e6f','443835c1'],[p,(p[0]+(76024500-p[1]),76024500),T])
rep(['1ba10976'],[T,e1])
rep(['2fe8efaf','707d2c13'],[T,e2])
# ---- S6 I2CC_SCL: exact centre of R503.2
p=P('R503.2'); e=f.pt(84.175,75.8745)
rep(['96d34708','73440ea4'],[p,(p[0],e[1]-(p[0]-e[0])),e])
# (jog at the via (81.175,82.5245) of I2CC_SCL left: one 45 degree piece, pad end 0.0245 off centre = inside tolerance)
# ---- S7 LDO_1V5 corner above U501.4: left as it is (a 45 degree corner only fits with three 0.2 mm pieces between C506-side pad and U501.5)
# ---- S8a LDO_3V3 at C508.1 / U502.8 / R502.1 / R503.1
c=P('C508.1'); u=P('U502.8'); r2=P('R502.1'); r3=P('R503.1'); h=f.pt(84.075,72.2745)
q=(c[0]+55000,c[1])
rep(['2ad21730'],[c,q])                                                    # 0.5 mm, 0.055 long: the widest that clears C508.2 at the pad centre
rep(['5709bce4','b0d95db7'],[q,(q[0]+(q[1]-h[1]),h[1]),h])                 # 0.6
rep(['dbd54497','67aa8e0d'],[h,(r3[0],h[1]+(r3[0]-h[0])),(r3[0],73174500)]) # 0.8
rep(['9c9b714a'],[(r3[0],73174500),r3])                                    # 0.5 neck straight into R503.1
s=(c[0],u[1])                                                              # 0.02 mm beside the centre of U502.8, on its centre line
rep(['f276de3c'],[c,s])
rep(['fe91cca1','c14656d3'],[s,(82.9,u[1]*MM),(82.9+(u[1]-r2[1])*MM,r2[1]*MM),r2])
# ---- S8b LDO_3V3: branch to R555.1 round the 3V3 via (was a hook)
T=f.pt(86.175,74.2245); p=P('R555.1'); xb=T[0]+150000
rep(['65329284','4a003ab4','d57df49d'],[T,(xb,T[1]+150000),(xb,p[1]-180000-(xb-p[0])),(p[0],p[1]-180000),p])
# ---- S8c LDO_3V3: C504.1 -> via -> U501.1 (random-angle piece on top of the via, 0.124 mm piece in the pad)
a=f.pt(85.225,76.0245); e=f.pt(85.9005,76.7); b=f.pt(85.6,77.5245)
rep(['f131c60e','5df2ca1b'],[e,(e[0],b[1]-(e[0]-b[0])),b])
# ---- S8d LDO_3V3: via (82.275,77.5245) -> R504.1 at one width (0.4), the 0.2 neck beside the SCL via removed by moving the diagonal 0.106 mm
v=V(82.275,77.5245); p=P('R504.1'); xv=80425000
rep(['94f5d9ad','d0695c3e','858ad29a','125d7f6e','a7060cd6'],[v,(v[0]-150000,v[1]),(xv,v[1]+(v[0]-150000-xv)),(xv,p[1]-(xv-p[0])),p],w=0.4)
# ---- S8g LDO_3V3 corner at (91.275,75.324): left (a chamfer gives diagonal-flat-diagonal, which reads as a staircase)
# ---- S8e LDO_3V3 at C552.1: the 0.6 mm piece from the pad corner to the pad centre (a blob standing out of the pad) -> 0.2 like the track; it lies inside the pad
rep(['ef75d578'],[f.pt(94.35,76.27),P('C552.1')],w=0.2)
# ---- S9 PD_DRAIN: pins 15 and 30 into the exposed pad (ends were on its rounded corner)
p=P('U501.15'); rep(['3162c39e'],[p,(83.3,81.8),(83.55,82.05)])
p=P('U501.30'); rep(['9dbf3780'],[p,(85.9,81.8),(85.65,82.05)])
# ---- S10 PPHV: R525.1 joins the vertical in a T instead of a 45 degree V at the tap node (tap piece into R524.1 untouched)
a=f.pt(83.275,84.4745); n=f.pt(83.275,85.75); p=P('R525.1'); T=(n[0],p[1])
rep(['07d49b02'],[a,T,n])
rep(['e7d1ed04','1df0cca3'],[p,T])
# ---- S12 SW_5V: one junction instead of two 0.13 mm apart. The diagonal from C540.2 (other region, untouched) ends at (92.4,85.98);
#      it is continued 0.184 mm on its own line to (92.53,85.85), and the vertical from L502.1 moves 0.13 mm to x=92.53 so that all three meet there.
n=f.pt(92.4,85.98); p=P('U504.5'); j=(n[0]+(n[1]-p[1]),p[1])
rep(['bb4669d1'],[n,j])
rep(['650e0b08'],[(j[0],84200000),j])
rep(['1e60a522'],[j,p])
# ---- S13 VBIAS: 0.081 mm piece inside C551.1
f.delete(['362a483e'])
# ---- S14 VBUS: U501.32 and C550.1 entries
f.delete(['9e140a3e'])
v=V(87.85,81.0); p=P('C550.1')
rep(['33aea070','098e8712'],[v,(p[0],v[1]+(v[0]-p[0])),p])
# ---- S15 3V3: link between the two vias, bar and the C503.1 branch
va=V(85.825,74.7245); vb=V(85.725,75.8245); xl=85700000; e=f.pt(86.475,75.8245)
rep(['4d739499','7abc77e3','fcffc0cf'],[va,(xl,va[1]+(va[0]-xl)),(xl,vb[1])],w=0.2)
rep(['dbfc084f'],[(xl,vb[1]),e])
top=f.pt(86.925,76.2745); bot=f.pt(86.925,77.1245); c=P('C503.1'); T=(top[0],c[1])
rep(['857e952c','c5d44ebf'],[top,T,bot])
rep(['7c18d9bc','26cfcdb2'],[c,T],w=0.6)
# ---- S16 GND: 0.035 mm off-angle track between U502.1 and the via that sits in the pad (redundant: via in pad)
f.delete(['f1091a8e'])
# (0.075 mm piece at U501.12 left: it lies inside the copper of the GND track between pins 11 and 12)
# ---- B: CELL1 end 0.05 mm inside the rim of J109.1 -> 0.29 mm further in
e=f.pt(85.825,74.0245,l='B')
rep(['5db824ff'],[(85.825,69.8345),e])
# ---- In2: GND link between two vias (two 90 degree corners -> one diagonal); I2CC_SCL corner
v1=V(91.225,80.7245); v2=V(92.025,77.5245)
rep(['12893755','e19b07b8','ad66508c'],[v1,(v1[0],v2[1]+(v2[0]-v1[0])),v2])
v=V(81.175,82.5245); e=f.pt(82.275,80.4745,l='In2')
rep(['28e86295','645e7003'],[v,(e[0]-300000,v[1]),(e[0],v[1]-300000),e])
# ---- In3: 90 degree corners of IRQ_N and SCL
v=V(103.075,76.9745); e=f.pt(80.525,80.2245,l='In3')
rep(['7ba77bd8','637a344c'],[v,(e[0]+300000,v[1]),(e[0],v[1]+300000),e])
a=f.pt(84.825,78.3245,l='In3'); e=f.pt(81.025,79.4745,l='In3')
rep(['1fd2f683','c4cf10d1'],[a,(e[0]+300000,a[1]),(e[0],a[1]+300000),e])

if '--gaps' in sys.argv:
    for net,l,w,pts in CHK:
        print(net,l); gaps(f,net,l,w,pts,slack=0.02)
ok=f.check('spec.json',maxexc=0.8,out='after_geo.json')
excs(f,'spec.json')
