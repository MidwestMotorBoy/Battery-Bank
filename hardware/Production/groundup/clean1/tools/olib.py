"""olib.py: helpers for the overlaps agent (copper cover tests, node graph)"""
import json, sys, math, collections, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geolib as G
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
MM=1e-6; LN=G.LN
def tpoly(t, extra=0):
    a,b=G.P(t)
    return (Point(a) if a==b else LineString([a,b])).buffer(t['w']/2+extra, 16)
class Board:
    def __init__(s,g):
        s.g=g; s.T={t['id']:t for t in g['tracks']}
        s.by=collections.defaultdict(list)
        for t in g['tracks']: s.by[(t['net'],t['l'])].append(t)
        s.pads=collections.defaultdict(list); s.vias=collections.defaultdict(list); s.fills=collections.defaultdict(list)
        for p in g['pads']:
            for l,pts in p['L'].items():
                if len(pts)>=3: s.pads[(p['net'],l)].append((Polygon(pts),p))
        for v in g['vias']:
            for l in LN[LN.index(v['top']):LN.index(v['bot'])+1]: s.vias[(v['net'],l)].append(v)
        for f in g['fills']:
            for outer,holes in f['polys']:
                if len(outer)>=3: s.fills[(f['net'],f['l'])].append((Polygon(outer,holes).buffer(0),f['name']))
    def find(s,pfx):
        m=[t for t in s.g['tracks'] if t['id'].startswith(pfx)]
        assert len(m)==1,(pfx,len(m)); return m[0]
    def other_copper(s,t,fills=True,exclude=()):
        """union of the same-net copper on the layer of t, without t itself (and without ids in exclude)"""
        k=(t['net'],t['l']); gs=[]
        for u in s.by[k]:
            if u['id']!=t['id'] and u['id'] not in exclude: gs.append(tpoly(u))
        for poly,p in s.pads[k]: gs.append(poly)
        for v in s.vias[k]:
            if t['l'] in v['flash']: gs.append(Point(v['x'],v['y']).buffer(v['d']/2,16))
        if fills:
            for poly,n in s.fills[k]: gs.append(poly)
        return unary_union(gs) if gs else Polygon()
    def uncovered(s,t,fills=True,exclude=()):
        """area (mm2) of the copper of t not covered by other copper of its net on its layer"""
        return tpoly(t).difference(s.other_copper(t,fills,exclude).buffer(200)).area*1e-12
    def in_fill(s,net,l,pt):
        return [n for poly,n in s.fills[(net,l)] if poly.covers(Point(pt))]
    def at(s,net,l,pt):
        r=[]
        for poly,p in s.pads[(net,l)]:
            if poly.covers(Point(pt)): r.append('pad:%s.%s'%(p['ref'],p['n']))
        for v in s.vias[(net,l)]:
            d=math.hypot(v['x']-pt[0],v['y']-pt[1])
            if d<=v['d']/2: r.append('via:%s(off %.3f)'%(v['id'][:8],d*MM))
        for u in s.by[(net,l)]:
            a,b=G.P(u)
            if pt in (a,b): r.append('end:%s'%u['id'][:8])
            elif a!=b and LineString([a,b]).distance(Point(pt))<=u['w']/2: r.append('body:%s(off %.3f)'%(u['id'][:8],LineString([a,b]).distance(Point(pt))*MM))
        for n in s.in_fill(net,l,pt): r.append('fill:'+n)
        return r
