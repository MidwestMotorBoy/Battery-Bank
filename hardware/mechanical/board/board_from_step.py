"""Real P0 board for the mechanical model: KiCad STEP (board + every part's 3D model) -> board/monolith_board.npz in the
pack frame (mm), one triangle mesh per footprint, so the cup model can draw the real board and check every part against
the cup, carrier, rails, sleeves and filler instead of the old slab + USB-C envelopes (P.side_board_dummy).

Make the STEP from the saved board (KiCad 10):
  kicad-cli pcb export step --subst-models --no-dnp --force -o hardware/mechanical/board/Monolith_board.step \
      hardware/Production/Monolith.kicad_pcb
(the STEP itself is ~13 MB and git-ignored; the .npz is what the model reads). Re-run both after any board change.
Needs cadquery-ocp (the mechanical venv; monolith_step.py needs it too).
Run: python board/board_from_step.py [Monolith_board.step]

Frame: KiCad STEP (X, Y, Z) = (KiCad x, -KiCad y, up from B.Cu) -> pack (x, y, z) = (sb_xb0 + Z, X - 100, sb_z_mid + 100 + Y),
the inverse of monolith_shell.kicad(); a pure rotation (no mirror)."""
import os, sys, numpy as np
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
for _n in ('Edge', 'Shell', 'Face'):              # OCP 7.x names these TopoDS.Edge_s ...; 8.x TopoDS.Edge ...
    if not hasattr(TopoDS, _n): setattr(TopoDS, _n, getattr(TopoDS, _n + '_s'))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import monolith_shell as S

def name(l):
    a = TDataStd_Name()
    return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), a) else '?'
def tris(shape, defl):
    """triangle soup (n, 3, 3) of a located shape, in the STEP frame"""
    BRepMesh_IncrementalMesh(shape, defl, False, 0.5, True)
    out, ex = [], TopExp_Explorer(shape, TopAbs_FACE)
    while ex.More():
        f = TopoDS.Face(ex.Current()); loc = TopLoc_Location()
        t = BRep_Tool.Triangulation_s(f, loc)
        if t is not None:
            tr = loc.Transformation()
            P = np.array([[*t.Node(i).Transformed(tr).Coord()] for i in range(1, t.NbNodes() + 1)])
            T = np.array([t.Triangle(i).Get() for i in range(1, t.NbTriangles() + 1)]) - 1
            if f.Orientation() == TopAbs_REVERSED: T = T[:, ::-1]
            out.append(P[T])
        ex.Next()
    return np.concatenate(out) if out else np.zeros((0, 3, 3))
def to_pack(V):
    X, Y, Z = V[..., 0], V[..., 1], V[..., 2]
    return np.stack([S.sb_xb0 + Z, X - 100.0, S.sb_z_mid + 100.0 + Y], -1)

def read(path, defl=0.05):
    doc = TDocStd_Document(TCollection_ExtendedString('board'))
    r = STEPCAFControl_Reader(); r.SetNameMode(True); r.ReadFile(path); r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    top = TDF_LabelSequence(); st.GetFreeShapes(top)
    comps = TDF_LabelSequence(); st.GetComponents_s(top.Value(1), comps)
    parts = {}
    for i in range(1, comps.Length() + 1):
        c = comps.Value(i); ref = TDF_Label(); st.GetReferredShape_s(c, ref)
        n, model = name(c), name(ref)
        key = 'PCB' if model.endswith('_PCB') else n
        V = to_pack(tris(st.GetShape_s(c), defl if key != 'PCB' else 0.02)).astype(np.float32)
        parts[key] = np.concatenate([parts[key], V]) if key in parts else V
        parts.setdefault('_model_' + key, np.array(model))
    return parts

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'Monolith_board.step')
    p = read(src)
    np.savez_compressed(os.path.join(HERE, 'monolith_board.npz'), **p)
    n = sum(len(v) for k, v in p.items() if not k.startswith('_'))
    print(f"wrote board/monolith_board.npz: {sum(1 for k in p if not k.startswith('_'))} bodies, {n} triangles")
