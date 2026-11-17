#!/usr/bin/env python3
# neck.py: for every new track on In2/In3, list foreign copper (vias, tracks, pads on that layer) whose edge-to-edge
# distance to the net's copper got smaller and is below 1.0 mm (plane neck = distance - 2 x 0.25 zone clearance)
import sys,json,math
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
S='/tmp/clean1'
g0=json.load(open(S+'/r2/geo.json')); g1=json.load(open(sys.argv[1]))
ids0={t['id'] for t in g0['tracks']}; ids1={t['id'] for t in g1['tracks']}
LN=['F','In1','In2','In3','In4','B']
def tg(t): return LineString([(t['x1'],t['y1']),(t['x2'],t['y2'])]).buffer(t['w']/2)
for l in ['In2','In3']:
    new=[t for t in g1['tracks'] if t['l']==l and t['id'] not in ids0]
    nets=sorted({t['net'] for t in new})
    for net in nets:
        nn=[t for t in new if t['net']==net]
        old=unary_union([tg(t) for t in g0['tracks'] if t['l']==l and t['net']==net])
        aft=unary_union([tg(t) for t in g1['tracks'] if t['l']==l and t['net']==net])
        zone=unary_union([tg(t) for t in nn]).buffer(1200000)
        obs=[]
        for v in g0['vias']:
            a,b=LN.index(v['top']),LN.index(v['bot'])
            if a<=LN.index(l)<=b and v['net']!=net: obs.append(('via %s (%.3f,%.3f)'%(v['net'],v['x']/1e6,v['y']/1e6),Point(v['x'],v['y']).buffer(v['d']/2)))
        for t in g1['tracks']:
            if t['l']==l and t['net']!=net: obs.append(('track %s (%.3f,%.3f)-(%.3f,%.3f)'%(t['net'],t['x1']/1e6,t['y1']/1e6,t['x2']/1e6,t['y2']/1e6),tg(t)))
        for p in g0['pads']:
            if l in p['L'] and len(p['L'][l])>=3 and p['net']!=net: obs.append(('pad %s.%s %s'%(p['ref'],p['n'],p['net']),Polygon(p['L'][l])))
        print('##',l,net)
        for name,o in obs:
            if not o.intersects(zone): continue
            d0=old.distance(o)/1e6; d1=aft.distance(o)/1e6
            if d1<d0-0.001 and d1<1.0: print('   %-70s %.3f -> %.3f   (plane neck %.3f -> %.3f)'%(name,d0,d1,d0-0.5,d1-0.5))
