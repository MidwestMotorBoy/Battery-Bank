"""channel.py [spec.json]: same-channel test. For every net+layer the spec changes, the faces enclosed between the deleted and
the added centre lines are built; any pad, via, hole or track of ANOTHER net that touches such a face means the track moved
across it (or closer round it). Prints the offenders; none = same channel."""
import sys, json, collections
S='/tmp/clean1'
sys.path.insert(0, S+'/tools'); import geolib as G
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union, polygonize
g0=G.load(S+'/r2/geo.json'); spec=json.load(open(sys.argv[1] if len(sys.argv)>1 else S+'/agents/regD/spec.json')); MM=1e-6
LN=['F','In1','In2','In3','In4','B']
by={t['id']:t for t in g0['tracks']}
old=collections.defaultdict(list); new=collections.defaultdict(list)
for i in spec['del']: t=by[i]; old[(t['net'],t['l'])].append(LineString(G.P(t)))
for a in spec['add']: new[(a['net'],a['l'])].append(LineString([(a['x1'],a['y1']),(a['x2'],a['y2'])]))
bad=0
for k in sorted(set(old)|set(new)):
    net,l=k
    faces=list(polygonize(unary_union(old[k]+new[k])))
    area=sum(f.area for f in faces)*1e-12
    hits=[]
    for f in faces:
        if f.area < 1e6: continue
        for p in g0['pads']:
            if p['net']!=net and l in p['L'] and len(p['L'][l])>=3 and Polygon(p['L'][l]).intersects(f): hits.append('pad %s.%s %s'%(p['ref'],p['n'],p['net']))
            if p.get('hole') and Point(p['x'],p['y']).distance(f)==0 and p['net']!=net: hits.append('hole %s.%s'%(p['ref'],p['n']))
        for v in g0['vias']:
            if v['net']!=net and LN.index(v['top'])<=LN.index(l)<=LN.index(v['bot']) and Point(v['x'],v['y']).buffer(v['d']/2).intersects(f): hits.append('via %s (%.3f,%.3f)'%(v['net'],v['x']*MM,v['y']*MM))
        for t in g0['tracks']:
            if t['l']==l and t['net']!=net and G.tgeom(t).buffer(t['w']/2).intersects(f): hits.append('track %s %s'%(t['net'],t['id'][:8]))
    print('%-30s %-3s faces %d area %.3f mm2 %s'%(net,l,len(faces),area,('FOREIGN: '+'; '.join(sorted(set(hits)))) if hits else 'ok'))
    bad+=bool(hits)
print('nets with a foreign item between old and new path:', bad)
