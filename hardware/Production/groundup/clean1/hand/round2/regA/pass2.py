import sys; sys.path.insert(0,'.')
from mylib import *
from shapely.geometry import LineString, Point, Polygon
g=G.load(BASE)
def pad(name):
    r,n=name.split('.'); p=[p for p in g['pads'] if p['ref']==r and p['n']==n][0]; return Polygon(p['L']['F'])
def via(x,y):
    v=min(g['vias'],key=lambda v:math.hypot(v['x']*MM-x,v['y']*MM-y)); return Point(v['x'],v['y']).buffer(v['d']/2,64), v
a=pad('C546.2'); b=pad('C544.2'); v,vv=via(95.925,84.975); print(vv['x'],vv['y'],vv['net'])
print('C546.2-C544.2 dist',a.distance(b)*MM,'via-C544.2',v.distance(b)*MM)
from shapely.ops import nearest_points
p,q=nearest_points(a,b); print((p.x*MM,p.y*MM),(q.x*MM,q.y*MM))
p,q=nearest_points(v,b); print((p.x*MM,p.y*MM),(q.x*MM,q.y*MM))
print(list(b.exterior.coords)[:40])
c=pad('C544.1'); v2,vv2=via(95.925,87.27); print(vv2['x'],vv2['y'],vv2['net'],'via-C544.1',v2.distance(c)*MM)
v3,vv3=via(96.425,85.8745); v4,vv4=via(97.525,85.4245); print('via78-via84',v3.distance(v4)*MM, 'via78-C544.2',v3.distance(b)*MM,'via78-C544.1',v3.distance(c)*MM, 'via84-C544.1', v4.distance(c)*MM)
