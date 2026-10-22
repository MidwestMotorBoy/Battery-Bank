"""STEP models of the MYOUNG BH-21700-B1BJ001 cell holder (BT101-BT104) and the EVE INR21700/58E cell sitting in it.

Holder: LCSC's EasyEDA model (3dmodels/source/BAT-SMD_L82.5-W25-BH-21700-B1BJ001_easyeda.step, SolidWorks export
2024-06-11) corrected against MYOUNG's drawing (datasheets/bh-21700-b1bj001.pdf, 2023-11-10):
  - checked by hidden-line overlay: the top view (outline 82.5 x 25.0, pegs, terminals, pockets) matches the drawing;
  - the side walls were 1.0-1.5 mm too high in the middle: the housing is clipped to the drawing's side profile
    (3dmodels/source/BH-21700-B1BJ001_side_profile_mm.json: ends 15.62, shoulders 9.84, centre dip 6.88);
  - the EasyEDA logo embossed on the side is dropped;
  - the + terminal's locating tab is added: 1.50 wide, 1.20 below the seating plane, 38.60 from the centre at the +
    end, 11.50 off the axis (drawing end view and PCB layout; matches the footprint's dia 2.25 hole).
  - the EasyEDA side walls started their end slopes 1.0-2.3 mm further in than the drawing: the 1.5 mm wall strips
    (|y| 11.0-12.5) are filled up to the drawn profile.
  Internal contact springs are as EasyEDA modelled them.

Cell: EVE INR21700/58E outline (datasheets/eve-inr21700-58e.pdf Fig. 1): dia 21.50 +-0.20 x 70.80 +-0.20 with tube;
+ end: cap dia 16.9 x 1.1, crimp band dia 21.5 x 4.07, groove dia 16.9 x 0.96 (scaled from the figure).
Position (PROVISIONAL, not given by MYOUNG's drawing): + cap against the + contact at X = -36.75, axis at Z = 13.18
(the EasyEDA cradle floor at Z = 2.6 plus the cell radius). Measure a populated holder and set CELL_AXIS_Z.

Needs the OpenCascade Python bindings (OCP); run with KiCad 10's Python 3.11:
    python make_3d_holder.py [dir_containing_OCP]
"""
import json
import os
import sys

if len(sys.argv) > 1:
    sys.path.insert(0, sys.argv[1])
from OCP.Bnd import Bnd_Box
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Fuse
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt, gp_Vec
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDocStd import TDocStd_Document
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.XCAFDoc import XCAFDoc_ColorType, XCAFDoc_DocumentTool

HERE = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(HERE, "..", "3dmodels")
SRC = os.path.join(M, "source", "BAT-SMD_L82.5-W25-BH-21700-B1BJ001_easyeda.step")
PROFILE = os.path.join(M, "source", "BH-21700-B1BJ001_side_profile_mm.json")
OUT_HOLDER = os.path.join(M, "BatteryHolder_MYOUNG_BH-21700-B1BJ001.step")
OUT_CELL = os.path.join(M, "Cell_EVE_INR21700-58E_in_BH-21700.step")

CELL_AXIS_Z = 13.18           # PROVISIONAL: measure on a populated holder
CELL_PLUS_X = -36.75          # + cap face against the + contact (EasyEDA terminal)


def bbox(s):
    b = Bnd_Box(); BRepBndLib.Add_s(s, b); return b.Get()


def box(x0, x1, y0, y1, z0, z1):
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), x1 - x0, y1 - y0, z1 - z0).Shape()


def save(path, parts):
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    for name, shape, rgb in parts:
        lab = st.AddShape(shape, False)
        TDataStd_Name.Set_s(lab, TCollection_ExtendedString(name))
        ct.SetColor(lab, Quantity_Color(*rgb, Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)
    w = STEPCAFControl_Writer(); w.SetColorMode(True); w.SetNameMode(True); w.Transfer(doc, STEPControl_AsIs)
    assert w.Write(os.path.normpath(path)) == IFSelect_RetDone
    print("wrote", os.path.normpath(path))


# ---- holder -----------------------------------------------------------------------------------------------------
r = STEPControl_Reader(); r.ReadFile(SRC); r.TransferRoots()
solids = []
ex = TopExp_Explorer(r.OneShape(), TopAbs_SOLID)
while ex.More():
    solids.append(ex.Current()); ex.Next()
vol = lambda s: (lambda b: (b[3] - b[0]) * (b[4] - b[1]) * (b[5] - b[2]))(bbox(s))
housing = max(solids, key=vol)
terminals = [s for s in solids if s is not housing and vol(s) > 50]          # the two terminals; the logo letters are tiny
assert len(terminals) == 2, len(terminals)

prof = json.load(open(PROFILE))
poly = BRepBuilderAPI_MakePolygon()
pts = [(-41.4, -3.0), (-41.4, prof[0][1])] + [tuple(p) for p in prof] + [(41.4, prof[-1][1]), (41.4, -3.0)]
for x, z in pts:
    poly.Add(gp_Pnt(x, -20.0, z))
poly.Close()
clip = BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(poly.Wire()).Face(), gp_Vec(0, 40.0, 0)).Shape()
housing = BRepAlgoAPI_Common(housing, clip).Shape()
# the EasyEDA side walls (1.5 thick at |y| 11.0-12.5) start their end slopes 1-2.3 mm further in than the drawing:
# fill the wall strips up to the drawn profile so the model is never smaller than the part
fill = None
for sx in (-1, 1):
    for sy in (-1, 1):
        b = box(min(sx * 28.4, sx * 33.6), max(sx * 28.4, sx * 33.6), min(sy * 11.0, sy * 12.5), max(sy * 11.0, sy * 12.5), 9.0, 15.7)
        fill = b if fill is None else BRepAlgoAPI_Fuse(fill, b).Shape()
housing = BRepAlgoAPI_Fuse(housing, BRepAlgoAPI_Common(fill, clip).Shape()).Shape()

tab = box(-38.6 - 0.175, -38.6 + 0.175, 11.5 - 0.75, 11.5 + 0.75, -1.2, 0.2)    # + terminal locating tab (0.35 sheet)
terminals = BRepAlgoAPI_Fuse(BRepAlgoAPI_Fuse(terminals[0], terminals[1]).Shape(), tab).Shape()
save(OUT_HOLDER, [("housing", housing, (0.10, 0.10, 0.11)),          # PA66 black
                  ("terminals", terminals, (0.78, 0.78, 0.80))])     # 304 stainless, Ni plated

# ---- cell --------------------------------------------------------------------------------------------------------
def cyl(d, x0, length):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x0, 0, CELL_AXIS_Z), gp_Dir(1, 0, 0)), d / 2, length).Shape()


x = CELL_PLUS_X
cap = cyl(16.9, x, 1.10); x += 1.10
band = cyl(21.5, x, 4.07); x += 4.07
groove = cyl(16.9, x, 0.96); x += 0.96
body = cyl(21.5, x, 70.80 - (x - CELL_PLUS_X))
can = BRepAlgoAPI_Fuse(BRepAlgoAPI_Fuse(band, groove).Shape(), body).Shape()
save(OUT_CELL, [("cell tube", can, (0.15, 0.35, 0.75)),              # EVE blue sleeve
                ("positive cap", cap, (0.80, 0.80, 0.82))])
