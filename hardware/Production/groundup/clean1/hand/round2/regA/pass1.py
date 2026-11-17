import sys; sys.path.insert(0,'.')
from mylib import *
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
g=G.load(BASE); net='/USB Port 2/PP5V'
ob=G.Obst(g)
def obs(x0,y0,x1,y1,l='F'):
    out=[]
    for gm,r,onet,kind,name,hole in ob.items[l]:
        if onet==net: continue
        b=gm.bounds
        if b[2]<x0*1e6 or b[0]>x1*1e6 or b[3]<y0*1e6 or b[1]>y1*1e6: continue
        out.append((gm.buffer(r) if r else gm, kind, name, onet))
    return out
O=obs(94,82.5,98.5,88)
for gm,kind,name,onet in O:
    b=gm.bounds; print(kind,name[:8],onet,'%.3f %.3f %.3f %.3f'%tuple(v*MM for v in b))
U=unary_union([o[0] for o in O])
def ok(pts,w,clr=0.15):
    ls=LineString([(x*1e6,y*1e6) for x,y in pts])
    return U.distance(ls)-w*1e6/2 >= clr*1e6-500
def gap(pts,w):
    ls=LineString([(x*1e6,y*1e6) for x,y in pts]); return (U.distance(ls)-w*1e6/2)*MM
# the pass alone: short vertical piece with diag leads
import itertools
best={}
for w in (0.3,0.25,0.2):
    sols=[]
    for ci in range(0,61):
        c=96.2+ci*0.005
        for y1i in range(0,60):
            y1=84.4+y1i*0.0125
            for y2i in range(0,60):
                y2=y1+y2i*0.0125
                if y2>85.5: break
                # neck piece: diag lead-in 0.3 long, vertical, diag lead-out 0.3
                pts=[(c-0.25,y1-0.25),(c,y1),(c,y2),(c+0.25,y2+0.25)]
                if ok(pts,w): sols.append((y2-y1,c,y1,y2))
    print('w',w,'solutions',len(sols))
    if sols:
        sols.sort(); print('  shortest vertical',sols[:5]); 
