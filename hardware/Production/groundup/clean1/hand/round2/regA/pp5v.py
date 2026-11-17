# PP5V run C542.1 -> R533.1 on F: two options (A: 0.30 with two necks, B: 0.25 with one neck). Usage: pp5v.py A|B
import sys; sys.path.insert(0,'.')
from mylib import *
opt=sys.argv[1]
f=Fix(BASE,region=(90,78,100,92))
net='/USB Port 2/PP5V'
ids=['65eb239f','bd9cb157','de880531','7abfc162','2745c5b5','b5e2a774','d0523210','d1903c9d','d87bf92e','d68556e6','77d389b1','113e0aab','6e14c20e','7cd35e04','fb19a9fa','a93135a6','a5b41408','ea82ebbd','53753834','c6561bab','937db3b5']
old=[f.by[f._id(i)] for i in ids]
sq0=sum(G.tlen(t)/t['w'] for t in old); L0=sum(G.tlen(t) for t in old)*MM
print('NOW: pieces %d, length %.3f mm, squares %.2f, widths %s'%(len(old),L0,sq0,sorted({t['w']*MM for t in old})))
W=0.3 if opt=='A' else 0.25
xv=94.9 if opt=='A' else 94.925          # vertical beside C542.2 (0.30 needs 0.025 more room)
xe=96.75 if opt=='A' else 96.725         # vertical beside the FB via (same)
p_stub=(96.125,80.1945)                  # end of the 0.8 stub from C542.1, 0.03 mm shorter so that the 0.30 diagonal clears the corner of C542.2
pad=f.pad('R533.1')
segs=[]   # (w, [pts])
c=96.425
b1=(c,84.7245); b2=(c,85.1)
E=(c-0.075,84.7245-0.075); Fp=(c+0.075,85.1+0.075)
top=[p_stub,(xv,80.1945+(96.125-xv)),(xv,84.7245-(c-xv)),E]
segs.append((W,top))
segs.append((0.2,[E,b1,b2,Fp]))
y3=86.1245
mid=[Fp,(97.025,85.1+0.6),(97.025,y3),(c,y3+0.6)]
segs.append((W,mid))
if opt=='A':
    segs.append((0.25,[(c,y3+0.6),(c,87.9)]))
    low0=(c,87.9)
else: low0=(c,y3+0.6)
y4=89.3245
ye=90.4995-(xe-96.75)
low=[low0,(c,y4),(xe,y4+(xe-c)),(xe,ye),(96.175,91.0745),(pad[0]*MM+(91.0745-pad[1]*MM),91.0745),pad]
segs.append((W,low))
f.delete(ids)
for w,pts in segs: f.add(net,'F',w,pts)
# dangling 0.8 stub at R533.1 (leads nowhere) 
f.delete(['ecf3fc8e','14bba9a8'])
# 0.8 stub at C542.1: one straight piece on the pad's vertical centre line instead of the slanted lump
f.replace(['2145cd10','c8799488'],[(96.125,79.425),p_stub])
new=[a for a in f.adds if not (a['w']==800000)]
sq1=sum(math.hypot(a['x2']-a['x1'],a['y2']-a['y1'])/a['w'] for a in new); L1=sum(math.hypot(a['x2']-a['x1'],a['y2']-a['y1']) for a in new)*MM
print('OPTION %s: pieces %d, length %.3f mm, squares %.2f'%(opt,len(new),L1,sq1))
import collections
c2=collections.defaultdict(float)
for a in new: c2[a['w']*MM]+=math.hypot(a['x2']-a['x1'],a['y2']-a['y1'])*MM
print('   length per width:',dict(c2))
for w,pts in segs: gaps(f,net,'F',w,pts,slack=0.03)
ok=f.check('pp5v_opt%s.json'%opt,maxexc=0.3,out='pp5v_opt%s_geo.json'%opt)
excs(f,'pp5v_opt%s.json'%opt)
