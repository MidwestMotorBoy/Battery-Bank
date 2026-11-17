import sys, json, math, collections
S='/tmp/clean1'
sys.path.insert(0,S+'/tools')
import geolib as G
from fixlib import Fix, _nm
MM=1e-6
BASE=S+'/r2/geo.json'
REG=(79,69,100,86)
_ob={}
def obst(g):
    k=id(g)
    if k not in _ob: _ob[k]=G.Obst(g)
    return _ob[k]
def gaps(f, net, l, w, pts, slack=0.12, skip=()):
    """min gaps of a polyline (mm or nm pts) against other-net items of the BASE geometry (deleted tracks of f are ignored)"""
    ob=obst(f.g); pts=[_nm(p) for p in pts]; W=int(round(w*1e6))
    for a,b in zip(pts,pts[1:]):
        t=dict(id='new',net=net,l=l,w=W,x1=a[0],y1=a[1],x2=b[0],y2=b[1])
        res=[r for r in ob.near(t,slack=int(slack*1e6)) if not (r[2]=='track' and r[3] in f.dele)]
        res.sort()
        print('  piece (%.4f,%.4f)->(%.4f,%.4f) w%.2f len %.3f'%(a[0]*MM,a[1]*MM,b[0]*MM,b[1]*MM,w,math.hypot(b[0]-a[0],b[1]-a[1])*MM))
        for gap,need,kind,name,onet in res[:6]:
            print('      gap %.4f need %.2f %s %s %s %s'%(gap*MM,need*MM,kind,name[:8] if kind in('track','via','viahole') else name,onet,'  <<< VIOL' if gap<need-1000 else ''))
def maxw(f, net, l, pts, cands=(0.8,0.6,0.5,0.4,0.35,0.3,0.25,0.2)):
    ob=obst(f.g); pts=[_nm(p) for p in pts]
    for w in cands:
        W=int(round(w*1e6)); ok=True
        for a,b in zip(pts,pts[1:]):
            t=dict(id='new',net=net,l=l,w=W,x1=a[0],y1=a[1],x2=b[0],y2=b[1])
            for gap,need,kind,name,onet in ob.near(t):
                if kind=='track' and name in f.dele: continue
                if gap<need-1000: ok=False
        if ok: return w
    return None
def excs(f, spec_fn):
    g0=f.g; spec=json.load(open(spec_fn)); g1=G.apply_spec(g0,spec); ex=G.excursion(g0,g1)
    SENS_CLS=('HighCurrent','Power','GND','Kelvin','GateDrive'); import re
    znets={z['net'] for z in g0['zones']} if g0.get('zones') and isinstance(g0['zones'][0],dict) and 'net' in g0['zones'][0] else set()
    names={'EN_5V1','/USB Port 1/I2CC_SCL','/USB Port 2/SBU_FLT','/Cells and Gauge/TS4','Net-(U403-FB)','Net-(U503-FB)'}
    out=[]
    for (net,l),(d,where) in sorted(ex.items(), key=lambda kv:-kv[1][0]):
        sens = g0['netclass'].get(net) in SENS_CLS or net in znets or l in('In1','In4') or net in names or re.search(r'/DPDN|/D[PN]$|USB_D|/(SRP|SRN|ACP|ACN)(_F)?$|/DRV_SUP$',net)
        out.append((d,net,l,where,bool(sens)))
        print('  exc %.3f %s %s at %s %s'%(d,net,l,where,'SENSITIVE' if sens else ''))
    return out
