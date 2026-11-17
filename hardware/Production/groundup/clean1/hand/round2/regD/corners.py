import sys, json, math, collections
S='/tmp/clean1'
sys.path.insert(0, S+'/tools'); import geolib as G
from shapely.geometry import Polygon, Point
fn=sys.argv[1] if len(sys.argv)>1 else S+'/r2/geo.json'
g=G.load(fn); MM=1e-6; R=(79,103,100,120)
LN=['F','In1','In2','In3','In4','B']
def corners(g):
    out=[]
    groups=collections.defaultdict(list)
    for t in g['tracks']: groups[(t['net'],t['l'])].append(t)
    for (net,l),ts in groups.items():
        nodes=collections.defaultdict(list)
        for t in ts:
            a,b=G.P(t); nodes[a].append((t,b)); nodes[b].append((t,a))
        pads=[(Polygon(p['L'][l]),p) for p in g['pads'] if p['net']==net and l in p['L'] and len(p['L'][l])>=3]
        vias=[v for v in g['vias'] if v['net']==net and LN.index(v['top'])<=LN.index(l)<=LN.index(v['bot'])]
        for pt,lst in nodes.items():
            if not (R[0]<=pt[0]*MM<R[2] and R[1]<=pt[1]*MM<R[3]): continue
            if len(lst)!=2: continue
            (t1,a),(t2,b)=lst
            ax,ay=a[0]-pt[0],a[1]-pt[1]; bx,by=b[0]-pt[0],b[1]-pt[1]
            la,lb=math.hypot(ax,ay),math.hypot(bx,by)
            ang=math.degrees(math.acos(max(-1,min(1,(ax*bx+ay*by)/la/lb))))
            if ang>100: continue
            P=Point(pt)
            inpad=any(poly.contains(P) for poly,_ in pads); inv=any(math.hypot(v['x']-pt[0],v['y']-pt[1])<=v['d']/2 for v in vias)
            out.append((l,net,pt,round(ang),la*MM,lb*MM,inpad or inv,t1,t2,a,b))
    return out
if __name__=='__main__':
    for l,net,pt,ang,la,lb,hid,t1,t2,a,b in sorted(corners(g),key=lambda c:(c[0],c[1])):
        print('%-3s %-26s (%.4f,%.4f) ang %d legs %.3f %.3f %s w %.2f/%.2f %s %s'%(l,net[-26:],pt[0]*MM,pt[1]*MM,ang,la,lb,'in pad/via' if hid else 'OPEN',t1['w']*MM,t2['w']*MM,t1['id'][:4],t2['id'][:4]))
