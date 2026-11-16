"""dumpgeo.py board.kicad_pcb out.json   (KiCad python)
Everything straighten.py needs, in integer nanometres: tracks with their ids, vias (and on which layers each has a pad),
pads (outline per copper layer, hole), filled zones, rule areas, board outline, unplated holes, copper-layer graphics,
and the net class of every net."""
import pcbnew, sys, json
b = pcbnew.LoadBoard(sys.argv[1])
CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu]; LN = ['F', 'In1', 'In2', 'In3', 'In4', 'B']
def polys(ps):
    r = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i); pts = [(o.CPoint(j).x, o.CPoint(j).y) for j in range(o.PointCount())]; hs = []
        for h in range(ps.HoleCount(i)):
            hh = ps.Hole(i, h); hs.append([(hh.CPoint(j).x, hh.CPoint(j).y) for j in range(hh.PointCount())])
        r.append([pts, hs])
    return r
out = dict(tracks=[], vias=[], pads=[], fills=[], keepouts=[], edge=[], npth=[], gfx=[], netclass={}, zones=[])
for n, ni in b.GetNetsByName().items():
    out['netclass'][str(n)] = str(ni.GetNetClassName())
for t in b.GetTracks():
    c = t.GetClass()
    if c == 'PCB_VIA':
        p = t.GetPosition()
        out['vias'].append(dict(id=t.m_Uuid.AsString(), x=p.x, y=p.y, d=t.GetWidth(pcbnew.F_Cu), drill=t.GetDrill(), net=str(t.GetNetname()),
                                top=LN[CU.index(t.TopLayer())], bot=LN[CU.index(t.BottomLayer())], flash=[n for l, n in zip(CU, LN) if t.FlashLayer(l)],
                                rul=bool(t.GetRemoveUnconnected()), locked=bool(t.IsLocked())))
    elif c == 'PCB_TRACK':
        s = t.GetStart(); e = t.GetEnd()
        out['tracks'].append(dict(id=t.m_Uuid.AsString(), x1=s.x, y1=s.y, x2=e.x, y2=e.y, w=t.GetWidth(), l=LN[CU.index(t.GetLayer())], net=str(t.GetNetname()), locked=bool(t.IsLocked())))
    else:
        out.setdefault('other', []).append(c)
for f in b.GetFootprints():
    for p in f.Pads():
        c = p.GetPosition(); ds = p.GetDrillSize()
        d = dict(ref=str(f.GetReference()), n=str(p.GetNumber()), net=str(p.GetNetname()), x=c.x, y=c.y, L={}, npth=p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH, hole=None)
        if ds.x > 0:
            s = p.GetEffectiveHoleShape(); sg = s.GetSeg(); d['hole'] = [sg.A.x, sg.A.y, sg.B.x, sg.B.y, s.GetWidth()]
        for l, n in zip(CU, LN):
            if p.IsOnLayer(l):
                ps = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps, l, 0, 2000, pcbnew.ERROR_OUTSIDE)
                d['L'][n] = polys(ps)[0][0] if ps.OutlineCount() else []
        out['pads'].append(d)
    for g in f.GraphicalItems():
        if g.GetLayer() in CU: out['gfx'].append(dict(ref=str(f.GetReference()), cls=g.GetClass(), l=LN[CU.index(g.GetLayer())]))
for g in b.GetDrawings():
    if g.GetLayer() in CU:
        bb = g.GetBoundingBox(); out['gfx'].append(dict(ref='', cls=g.GetClass(), l=LN[CU.index(g.GetLayer())], bb=[bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()]))
def flag(z, *names):
    for n in names:
        if hasattr(z, n): return bool(getattr(z, n)())
    return None
ZZ = [(z, '') for z in b.Zones()] + [(z, str(f.GetReference())) for f in b.GetFootprints() for z in f.Zones()]
for z, ref in ZZ:
    lay = [n for l, n in zip(CU, LN) if z.IsOnLayer(l)]
    if z.GetIsRuleArea():
        out['keepouts'].append(dict(name=str(z.GetZoneName()), ref=ref, layers=lay, polys=polys(pcbnew.SHAPE_POLY_SET(z.Outline())),
                                    notracks=flag(z, 'GetDoNotAllowTracks'), novias=flag(z, 'GetDoNotAllowVias'), nofill=flag(z, 'GetDoNotAllowZoneFills', 'GetDoNotAllowCopperPour'),
                                    nopads=flag(z, 'GetDoNotAllowPads'), nofp=flag(z, 'GetDoNotAllowFootprints')))
        continue
    out['zones'].append(dict(id=z.m_Uuid.AsString(), net=str(z.GetNetname()), name=str(z.GetZoneName()), layers=lay, prio=z.GetAssignedPriority(), clearance=z.GetLocalClearance(),
                             minw=z.GetMinThickness(), outline=polys(pcbnew.SHAPE_POLY_SET(z.Outline())), teardrop=bool(z.IsTeardropArea()) if hasattr(z, 'IsTeardropArea') else None))
    for l, n in zip(CU, LN):
        if z.IsOnLayer(l):
            out['fills'].append(dict(net=str(z.GetNetname()), l=n, name=str(z.GetZoneName()), polys=polys(pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(l)))))
ps = pcbnew.SHAPE_POLY_SET(); ok = b.GetBoardPolygonOutlines(ps, False)
out['edge'] = polys(ps); out['edge_ok'] = bool(ok)
json.dump(out, open(sys.argv[2], 'w'))
print('tracks', len(out['tracks']), 'vias', len(out['vias']), 'pads', len(out['pads']), 'fills', len(out['fills']), 'keepouts', len(out['keepouts']), 'edge', len(out['edge']), 'gfx', len(out['gfx']), 'other', out.get('other'))
