"""Overlay the STEP model's hidden-line projections (red) on the drawing's outline strokes (black), per view."""
import sys, json, math
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw
from OCP.STEPControl import STEPControl_Reader
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection

step, segs_path, outdir = sys.argv[2], sys.argv[3], sys.argv[4]
S, ZC, Y0 = 10.888, 0.827, -1.949
r = STEPControl_Reader(); r.ReadFile(step); r.TransferRoots(); shape = r.OneShape()
segs = json.load(open(segs_path))


def project(view_dir, x_dir):
    algo = HLRBRep_Algo(); algo.Add(shape)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*view_dir), gp_Dir(*x_dir))))
    algo.Update(); algo.Hide()
    h = HLRBRep_HLRToShape(algo)
    polys = []
    for comp in (h.VCompound(), h.OutLineVCompound(), h.Rg1LineVCompound()):
        if comp is None or comp.IsNull():
            continue
        ex = TopExp_Explorer(comp, TopAbs_EDGE)
        while ex.More():
            c = BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current()))
            d = GCPnts_QuasiUniformDeflection(c, 0.002)
            if d.IsDone():
                polys.append([(d.Value(i).X(), d.Value(i).Y()) for i in range(1, d.NbPoints() + 1)])
            ex.Next()
    return polys


# drawing-to-view-mm maps (view coords: u right, v up), and the model projection set-up giving the same u, v
VIEWS = {
    # front: u = X, v = Z - ZC ; looking from the front (-Y) toward +Y
    'front': (lambda p: ((p[0] - 141.6) / S, (496.1 - p[1]) / S), (0, -1, 0), (1, 0, 0), lambda u, v: (u, v - ZC)),
    # top: u = X, v = -d (front at the bottom) ; looking down
    'top': (lambda p: ((p[0] - 141.6) / S, -(395.0 - p[1]) / S), (0, 0, 1), (1, 0, 0), lambda u, v: (u, -(v - Y0))),
    # side: u = height above the centreline (drawing: up = left), v = -d
    'side': (lambda p: ((303.0 - p[0]) / S, -(395.0 - p[1]) / S), (1, 0, 0), (0, 0, 1), lambda u, v: (u - ZC, v + Y0)),   # projector v = -Y
}
for name, (dmap, vdir, xdir, mmap) in VIEWS.items():
    model = project(vdir, xdir)
    model = [[mmap(*q) for q in pl] for pl in model]
    draw = []
    for s in segs[name]:
        if s['w'] < 0.7:
            continue
        p = s['p']
        if s['k'] == 'c':
            a, b, c, e = p
            p = [((1-t)**3*a[0]+3*(1-t)**2*t*b[0]+3*(1-t)*t*t*c[0]+t**3*e[0], (1-t)**3*a[1]+3*(1-t)**2*t*b[1]+3*(1-t)*t*t*c[1]+t**3*e[1]) for t in [i/10 for i in range(11)]]
        draw.append([dmap(q) for q in p])
    allp = [q for pl in draw + model for q in pl]
    u0, u1 = min(q[0] for q in allp) - 0.4, max(q[0] for q in allp) + 0.4
    v0, v1 = min(q[1] for q in allp) - 0.4, max(q[1] for q in allp) + 0.4
    PX = 90
    im = Image.new('RGB', (int((u1 - u0) * PX), int((v1 - v0) * PX)), 'white'); g = ImageDraw.Draw(im)
    T = lambda q: ((q[0] - u0) * PX, (v1 - q[1]) * PX)
    for k in range(math.ceil(u0), int(u1) + 1):
        g.line([T((k, v0)), T((k, v1))], fill=(225, 225, 245))
    for k in range(math.ceil(v0), int(v1) + 1):
        g.line([T((u0, k)), T((u1, k))], fill=(225, 225, 245))
    for pl in draw:
        g.line([T(q) for q in pl], fill=(0, 0, 0), width=2)
    for pl in model:
        if len(pl) > 1:
            g.line([T(q) for q in pl], fill=(230, 0, 0), width=1)
    im.save(f'{outdir}/overlay_{name}.png')
    print(name, im.size, 'model edges', len(model))
