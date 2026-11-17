import sys, json, math, collections
S='/tmp/clean1'
sys.path.insert(0,S+'/tools')
import geolib as G
from fixlib import Fix, _nm
from shapely.geometry import LineString, Point, Polygon
MM=1e-6
REGION=(79,69,121.5,103)
_ob={}
def obst(g):
    k=id(g)
    if k not in _ob: _ob[k]=G.Obst(g)
    return _ob[k]
def maxw(g, net, l, pts, show=3, skip=()):
    """max legal width (mm) of each piece of polyline pts (mm floats or nm ints) of net on layer l, with the limiting items"""
    ob=obst(g); pts=[_nm(p) for p in pts]; res=[]
    for a,b in zip(pts,pts[1:]):
        t=dict(id='?',x1=a[0],y1=a[1],x2=b[0],y2=b[1],w=0,l=l,net=net)
        lim=[]
        for gap,need,kind,name,onet in ob.near(t,slack=1500000):
            if name in skip: continue
            lim.append((2*(gap-need)*MM,kind,name if kind!='track' else name[:8],onet))
        lim.sort()
        res.append(lim[0][0] if lim else 9)
        print('  (%.4f,%.4f)->(%.4f,%.4f) maxw %.3f  %s'%(a[0]*MM,a[1]*MM,b[0]*MM,b[1]*MM,res[-1],'; '.join('%.3f %s %s %s'%x for x in lim[:show])))
    return res
def inreg(t):
    x=(t['x1']+t['x2'])/2*MM; y=(t['y1']+t['y2'])/2*MM
    return REGION[0]<=x<REGION[2] and REGION[1]<=y<REGION[3]
def merge_collinear(g):
    """spec (against g) that merges collinear same net/layer/width pieces meeting at a node of degree 2 with no via or pad centre there"""
    LN=['F','In1','In2','In3','In4','B']
    viaat=collections.defaultdict(set); padat=collections.defaultdict(set)
    for v in g['vias']:
        a,b=LN.index(v['top']),LN.index(v['bot'])
        for l in LN[a:b+1]: viaat[(v['net'],l)].add((v['x'],v['y'],v['d']))
    pads=collections.defaultdict(list)
    for p in g['pads']:
        for l,pts in p['L'].items():
            if len(pts)>=3: pads[(p['net'],l)].append((p['x'],p['y']))
    groups=collections.defaultdict(list)
    for t in g['tracks']: groups[(t['net'],t['l'])].append(t)
    dele=[]; add=[]; log=[]
    for (net,l),ts in groups.items():
        nodes=collections.defaultdict(list)
        for t in ts:
            nodes[(t['x1'],t['y1'])].append(t); nodes[(t['x2'],t['y2'])].append(t)
        # other-layer check not needed (no via there)
        alive={t['id']:dict(t) for t in ts}
        changed=True
        while changed:
            changed=False
            nodes=collections.defaultdict(list)
            for t in alive.values():
                nodes[(t['x1'],t['y1'])].append(t); nodes[(t['x2'],t['y2'])].append(t)
            for p,tt in nodes.items():
                if len(tt)!=2: continue
                a,b=tt
                if a['id']==b['id'] or a['w']!=b['w']: continue
                if not (inreg(a) and inreg(b)): continue
                if any(math.hypot(v[0]-p[0],v[1]-p[1])<v[2]/2 for v in viaat.get((net,l),())): continue
                if any(math.hypot(q[0]-p[0],q[1]-p[1])<50000 for q in pads.get((net,l),())): continue
                oa=(a['x1'],a['y1']) if (a['x2'],a['y2'])==p else (a['x2'],a['y2'])
                ob_=(b['x1'],b['y1']) if (b['x2'],b['y2'])==p else (b['x2'],b['y2'])
                d1=(p[0]-oa[0],p[1]-oa[1]); d2=(ob_[0]-p[0],ob_[1]-p[1])
                if d1[0]*d2[1]-d1[1]*d2[0]!=0 or d1[0]*d2[0]+d1[1]*d2[1]<=0: continue
                # tee_unsplit guard: no other end of the net on this layer lies at p (len(tt)==2 covers it)
                n=dict(a); n['id']='m%d'%len(log); n['x1'],n['y1']=oa; n['x2'],n['y2']=ob_; n['new']=True
                del alive[a['id']]; del alive[b['id']]; alive[n['id']]=n
                log.append((net,l,p[0]*MM,p[1]*MM,a['w']*MM)); changed=True; break
        orig={t['id'] for t in ts}
        for t in ts:
            if t['id'] not in alive: dele.append(t['id'])
        for i,t in alive.items():
            if i not in orig: add.append(dict(net=net,l=l,w=t['w'],x1=t['x1'],y1=t['y1'],x2=t['x2'],y2=t['y2']))
    return dict(**{'del':dele,'add':add}),log
