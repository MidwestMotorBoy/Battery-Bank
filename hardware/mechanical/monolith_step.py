"""STEP export of the Monolith cup pack: one file per part plus the assembled pack, all in the pack frame (mm), so any
set of part files imported together lands in place.
The model is a mesh model (manifold3d / numpy), so the STEP bodies are faceted B-rep solids: coplanar triangles are
merged into single planar faces, but round faces (cells, bores, O-ring, wires) stay as flat facets at the model's 48
segments per circle. Good for fit checks, sections, drawings and placing features; not true cylinders to dimension from.
Needs the mechanical venv plus cadquery-ocp (pip install cadquery-ocp).
The board (part 09) is the routed P0 board straight from KiCad (board/Monolith_board.step, see board/board_from_step.py),
true B-rep with every part's model, names and colours, moved into the pack frame; without that file it falls back to
the old slab + USB-C envelopes and the B.Cu BLE envelope.
Run: python monolith_step.py [outdir]   -> outdir/parts/*.step, outdir/monolith_pack_assembly.step (default ./step)"""
import os, sys, numpy as np
from OCP.gp import gp_Pnt, gp_Trsf
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDF import TDF_LabelSequence
from OCP.TopoDS import TopoDS_Shell, TopoDS_Compound, TopoDS
from OCP.BRep import BRep_Builder
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, \
    BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeFix import ShapeFix_Solid
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SHELL, TopAbs_SOLID, TopAbs_FACE
from OCP.GProp import GProp_GProps
from OCP.TopLoc import TopLoc_Location
from OCP.BRepGProp import BRepGProp
from OCP.STEPControl import STEPControl_AsIs
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.Interface import Interface_Static
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf
from OCP.TDataStd import TDataStd_Name
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.IFSelect import IFSelect_RetDone
import manifold3d as M3
for _n in ('Edge', 'Shell', 'Face'):              # OCP 7.x names these TopoDS.Edge_s ...; 8.x TopoDS.Edge ...
    if not hasattr(TopoDS, _n): setattr(TopoDS, _n, getattr(TopoDS, _n + '_s'))
import monolith_cup as K, monolith_shell as S, monolith_parts as P
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- mesh -> solid ----------------
def indexed(V, tol=1e-5):
    """triangle soup (n, 3, 3) -> unique vertices, triangles; drops triangles that collapse"""
    V = np.asarray(V, float).reshape(-1, 3)
    u, inv = np.unique(np.round(V / tol).astype(np.int64), axis=0, return_inverse=True)
    pts = np.zeros((len(u), 3)); np.add.at(pts, inv.ravel(), V); pts /= np.bincount(inv.ravel())[:, None]
    T = inv.reshape(-1, 3)
    return pts, T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 2] != T[:, 0])]
def from_manifold(m):
    me = m.to_mesh(); me.merge()
    return np.asarray(me.vert_properties)[:, :3].astype(float), np.asarray(me.tri_verts).astype(np.int64)
def fix_slivers(pts, T, eps=1e-9):
    """zero-area triangles (a, b, c with c on edge ab) can't become faces: drop each one and split its neighbour across
    ab at c, which keeps the mesh closed"""
    T = [tuple(t) for t in T]
    for _ in range(1000):
        P_ = pts[np.array(T)]; ar = np.linalg.norm(np.cross(P_[:, 1] - P_[:, 0], P_[:, 2] - P_[:, 0]), axis=1) / 2
        bad = np.flatnonzero(ar < eps)
        if not len(bad): return np.array(T)
        i = bad[0]; t = T[i]
        L = [np.linalg.norm(pts[t[(k + 1) % 3]] - pts[t[k]]) for k in range(3)]; k = int(np.argmax(L))
        a, b, c = t[k], t[(k + 1) % 3], t[(k + 2) % 3]           # c lies on a-b
        j = next(j for j, u in enumerate(T) if j != i and any(u[m] == b and u[(m + 1) % 3] == a for m in range(3)))
        u = T[j]; m = next(m for m in range(3) if u[m] == b and u[(m + 1) % 3] == a); d = u[(m + 2) % 3]
        T = [v for n, v in enumerate(T) if n not in (i, j)] + [(b, c, d), (c, a, d)]
    raise RuntimeError('sliver fix did not converge')
def components(T):
    """split triangles into vertex-connected bodies"""
    par = np.arange(T.max() + 1)
    def find(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for a, b, c in T:
        ra, rb, rc = find(a), find(b), find(c); par[rb] = ra; par[find(rc)] = ra
    roots = np.array([find(t[0]) for t in T])
    return [T[roots == r] for r in np.unique(roots)]
def closed(T):
    E = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1)
    return (np.unique(E, axis=0, return_counts=True)[1] == 2).all()
def shell_shared(pts, T):
    """shell with shared vertices and edges, straight from the indexed mesh (no sewing)"""
    vx = {}; ed = {}; B = BRep_Builder(); sh = TopoDS_Shell(); B.MakeShell(sh)
    def v(i):
        if i not in vx: vx[i] = BRepBuilderAPI_MakeVertex(gp_Pnt(*pts[i])).Vertex()
        return vx[i]
    def e(i, j):
        k = (min(i, j), max(i, j))
        if k not in ed: ed[k] = BRepBuilderAPI_MakeEdge(v(k[0]), v(k[1])).Edge()
        return ed[k] if i == k[0] else TopoDS.Edge(ed[k].Reversed())
    for a, b, c in T:
        w = BRepBuilderAPI_MakeWire(e(a, b), e(b, c), e(c, a))
        f = BRepBuilderAPI_MakeFace(w.Wire(), True)
        if f.IsDone(): B.Add(sh, f.Face())
    sh.Closed(True); return sh
def shell_sewn(pts, T, tol=2e-3):
    sw = BRepBuilderAPI_Sewing(tol)
    for a, b, c in T:
        w = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(gp_Pnt(*pts[a]), gp_Pnt(*pts[b])).Edge(),
                                    BRepBuilderAPI_MakeEdge(gp_Pnt(*pts[b]), gp_Pnt(*pts[c])).Edge(),
                                    BRepBuilderAPI_MakeEdge(gp_Pnt(*pts[c]), gp_Pnt(*pts[a])).Edge())
        f = BRepBuilderAPI_MakeFace(w.Wire(), True)
        if f.IsDone(): sw.Add(f.Face())
    sw.Perform(); ex = TopExp_Explorer(sw.SewedShape(), TopAbs_SHELL)
    return TopoDS.Shell(ex.Current())
def solid(pts, T):
    sh = shell_shared(pts, T) if closed(T) else shell_sewn(pts, T)
    fx = ShapeFix_Solid(BRepBuilderAPI_MakeSolid(sh).Solid()); fx.Perform(); s = fx.Solid()   # orientation outward
    u = ShapeUpgrade_UnifySameDomain(s, True, True, False); u.Build(); return u.Shape()
def solids(mesh):
    pts, T = mesh
    return [solid(pts, t) for t in components(T)]
def volume(sh):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(sh, g); return g.Mass()
def mesh_volume(pts, T):
    a, b, c = pts[T[:, 0]], pts[T[:, 1]], pts[T[:, 2]]; return np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6
def compound(shapes):
    B = BRep_Builder(); c = TopoDS_Compound(); B.MakeCompound(c)
    for s in shapes: B.Add(c, s)
    return c
def count(sh, kind):
    n, ex = 0, TopExp_Explorer(sh, kind)
    while ex.More(): n += 1; ex.Next()
    return n

# ---------------- parts ----------------
def soup(V): return indexed(V)
def mf(m):
    pts, T = from_manifold(m.simplify(1e-6)); pts, T = indexed(pts[T])   # collapses coincident vertices
    return pts, fix_slivers(pts, T)
def box_union(fn):
    """parts drawn as overlapping boxes (the sense wires): rebuild each box as a solid and union them, so every wire
    is one closed body"""
    rec, orig = [], P._box
    def box(x0, x1, y0, y1, z0, z1):
        rec.append(M3.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))); return orig(x0, x1, y0, y1, z0, z1)
    P._box = box
    try: fn()
    finally: P._box = orig
    return mf(K.U(*rec))
def cells():
    c = P.cell_solid(); return np.vstack([K.mv(c, (x, y, S.sb_z_cell0)) for x, y in K.CELLS])
def bumper_parts(top):
    b, s = K.bumper(top); return [('band', mf(b)), ('slab (15 % infill zone)', mf(s))]
# file name, description (from monolith_cup.PARTS), colour key, [(body name, (pts, tris))]
def part_list():
    D = {k: name + ', ' + mat for _, name, mat, k in K.PARTS}
    D.update(tails='Nickel PACK pads and CELL1 / CELL3 tongues', pwire='PACK wires, 18 AWG power + 28 AWG Kelvin (square stand-ins)',
             swire='Sense wires CELL1-3, 28 AWG (square stand-ins)', ble='BLE module envelope on B.Cu')
    L = [('01_carrier', 'carrier', [('carrier', mf(K.carrier()))]),
         ('02_board_rails', 'rails', [('rail', mf(K.rails()))]),
         ('03_cells_C1-C4', 'cell', [('cell', soup(cells()))]),
         ('04_insulator_rings', 'insul', [('ring', mf(K.insul_rings()))]),
         ('05_preload_foam_rings', 'foam', [('foam', mf(K.foam()))]),
         ('06_nickel_series_strips', 'nickel', [('strip', soup(P.nickel_strips('strips')))]),
         ('07a_nickel_pack_pads_tongues', 'tails', [('nickel', soup(P.nickel_strips('tails')))]),
         ('07b_pack_wires_18awg_kelvin_28awg', 'pwire', [('wire', soup(P.pack_wires()))]),
         ('07c_sense_wires_28awg', 'swire', [('wire', box_union(P.sense_wires))]),
         ('08_gap_filler', 'filler', [('filler', mf(K.filler()))]),
         *([] if os.path.exists(KICAD_STEP) else
           [('09a_board_dummy', 'board', [('board', soup(P.side_board_dummy()))]),
            ('09b_ble_module_envelope', 'ble', [('ble', soup(P.ble_module()))])]),
         ('10_retaining_sleeves', 'sleeve', [('sleeve', mf(K.sleeves()))]),
         ('11_cup', 'cup', [('cup', mf(K.cup()))]),
         ('12_cap_pad', 'pad', [('pad', mf(K.pad()))]),
         ('13_oring', 'oring', [('oring', mf(K.oring()))]),
         ('14_cap', 'cap', [('cap', mf(K.cap()))]),
         ('15_screws_M2', 'screw', [('screw', mf(K.screws()))]),
         ('16_bumper_bottom', 'bumpb', bumper_parts(False)),
         ('17_bumper_top', 'bumpt', bumper_parts(True))]
    return [(f, D.get(k, k), k, b) for f, k, b in L]
COLOUR = dict(K.C, bumpb=K.C['bump'], bumpt=K.C['bump'], tails=K.C['tail'], pwire=K.C['wire'], swire=K.C['wire'])

# ---------------- the real board ----------------
KICAD_STEP = os.path.join(HERE, 'board', 'Monolith_board.step')
def board_trsf():
    """KiCad STEP frame -> pack frame (board/board_from_step.py)"""
    t = gp_Trsf(); t.SetValues(0, 0, 1, S.sb_xb0, 1, 0, 0, -100.0, 0, 1, 0, S.sb_z_mid + 100.0); return t
def add_kicad_board(doc, st):
    """read the KiCad board STEP into doc (names and colours kept) and return its root label, unplaced"""
    r = STEPCAFControl_Reader(); r.SetNameMode(True); r.SetColorMode(True)
    before = TDF_LabelSequence(); st.GetFreeShapes(before)
    assert r.ReadFile(KICAD_STEP) == IFSelect_RetDone and r.Transfer(doc), KICAD_STEP
    after = TDF_LabelSequence(); st.GetFreeShapes(after)
    old = {before.Value(i + 1).Tag() for i in range(before.Length())}
    new = [after.Value(i + 1) for i in range(after.Length()) if after.Value(i + 1).Tag() not in old]
    assert len(new) == 1, len(new); return new[0]
def write_board(path, aroot=None, ast=None):
    """parts/09_board_kicad.step: the KiCad board placed in the pack frame; and the same board in the assembly"""
    doc, st, _ = new_doc(); lab = add_kicad_board(doc, st)
    top = st.NewShape(); TDataStd_Name.Set_s(top, TCollection_ExtendedString('board_kicad'))
    st.AddComponent(top, lab, TopLoc_Location(board_trsf())); st.UpdateAssemblies()
    write(doc, path, '09_board_kicad')
    if ast is not None:
        alab = add_kicad_board(ast[0], ast[1])
        TDataStd_Name.Set_s(ast[1].AddComponent(aroot, alab, TopLoc_Location(board_trsf())), TCollection_ExtendedString('board_kicad'))

# ---------------- STEP ----------------
def new_doc():
    d = TDocStd_Document(TCollection_ExtendedString('XmlOcaf'))
    return d, XCAFDoc_DocumentTool.ShapeTool_s(d.Main()), XCAFDoc_DocumentTool.ColorTool_s(d.Main())
def label(st, ct, shape, name, rgb):
    lab = st.AddShape(shape, False)
    TDataStd_Name.Set_s(lab, TCollection_ExtendedString(name))
    ct.SetColor(lab, Quantity_Color(*(c / 255 for c in rgb), Quantity_TOC_RGB), XCAFDoc_ColorSurf); return lab
def write(doc, path, name):
    Interface_Static.SetCVal_s('write.step.schema', 'AP214IS'); Interface_Static.SetCVal_s('write.step.unit', 'MM')
    Interface_Static.SetCVal_s('write.step.product.name', name)
    w = STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True)
    w.Transfer(doc, STEPControl_AsIs)
    assert w.Write(path) == IFSelect_RetDone, path
def bodies_of(body_list):
    out = []
    for bname, mesh in body_list:
        ss = solids(mesh); n = len(ss)
        out += [(bname if n == 1 else f'{bname} {i + 1}', s, mesh_volume(*mesh) / n if n else 0) for i, s in enumerate(ss)]
    return out

if __name__ == '__main__':
    out = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, 'step')
    os.makedirs(os.path.join(out, 'parts'), exist_ok=True)
    adoc, ast, act = new_doc()
    top = ast.NewShape(); TDataStd_Name.Set_s(top, TCollection_ExtendedString('Monolith pack'))
    bad = 0
    for fname, desc, key, body_list in part_list():
        rgb = COLOUR[key]; bs = bodies_of(body_list)
        doc, st, ct = new_doc()
        for bname, s, _ in bs: label(st, ct, s, bname, rgb)
        write(doc, os.path.join(out, 'parts', fname + '.step'), fname)
        # assembly: one component per part, its bodies inside
        part = compound([s for _, s, _ in bs]); plab = ast.AddShape(part, False)
        pname = fname[3:] if fname[2] == '_' else fname[4:]; TDataStd_Name.Set_s(plab, TCollection_ExtendedString(pname))
        act.SetColor(plab, Quantity_Color(*(c / 255 for c in rgb), Quantity_TOC_RGB), XCAFDoc_ColorSurf)
        TDataStd_Name.Set_s(ast.AddComponent(top, plab, TopLoc_Location()), TCollection_ExtendedString(pname))
        v_step = sum(volume(s) for _, s, _ in bs); v_mesh = sum(mesh_volume(*m) for _, m in body_list)
        ok = all(BRepCheck_Analyzer(s).IsValid() for _, s, _ in bs) and abs(v_step - v_mesh) <= 1e-3 * abs(v_mesh) + 1e-3
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {fname:36s} bodies {len(bs):2d}  faces {sum(count(s, TopAbs_FACE) for _, s, _ in bs):5d}  "
              f"vol {v_step:9.1f} mm3 (mesh {v_mesh:9.1f})  {desc}")
    if os.path.exists(KICAD_STEP):
        write_board(os.path.join(out, 'parts', '09_board_kicad.step'), top, (adoc, ast))
        print('ok  09_board_kicad                      the routed P0 board from KiCad, every part (board/Monolith_board.step)')
    else: print('no board/Monolith_board.step: the board is the old slab + envelopes')
    ast.UpdateAssemblies()
    write(adoc, os.path.join(out, 'monolith_pack_assembly.step'), 'Monolith pack')
    print('wrote', out, '' if not bad else f'({bad} part(s) failed the checks)')
