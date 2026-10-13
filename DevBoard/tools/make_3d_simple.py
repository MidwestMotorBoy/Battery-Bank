"""STEP models for packages KiCad does not ship, from the makers' package drawings (envelope accuracy):

  STM32WB1MMC (U301): LCSC EasyEDA model checked against datasheets/stm32wb1mmc.pdf fig. 11 / table 3 (10.0 x 6.5,
      1.372 +-0.046 tall, pin A1 top-left in the top view = footprint pad 1).
  M24512 (U402/U502), UFDFPN8 2 x 3 mm, datasheets/m24512.pdf: body 3.0 x 2.0 (pins on the 2.0 mm ends, as the
      footprint), height 0.55 typ (0.60 max).
  SMT test loop RH-S2761-46R / Harwin S2761-46R (45 test points): 1.60 x 0.80 x 1.15 formed strip on an 0603 land.

Frames match the KiCad footprints (origin = footprint origin, +Y = footprint -y, Z up from the board).
Needs OCP (see make_3d_usbc.py); run with KiCad 10's Python 3.11:  python make_3d_simple.py [dir_containing_OCP]
"""
import os
import sys

if len(sys.argv) > 1:
    sys.path.insert(0, sys.argv[1])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_ColorType, XCAFDoc_DocumentTool

M = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "3dmodels")


def box(x0, x1, y0, y1, z0, z1):
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), x1 - x0, y1 - y0, z1 - z0).Shape()


def dot(x, y, z, d=0.4, h=0.01):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, y, z), gp_Dir(0, 0, 1)), d / 2, h).Shape()


def fuse(*s):
    out = s[0]
    for t in s[1:]:
        out = BRepAlgoAPI_Fuse(out, t).Shape()
    return out


def save(name, parts):
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    for label, shape, rgb in parts:
        lab = st.AddShape(shape, False)
        TDataStd_Name.Set_s(lab, TCollection_ExtendedString(label))
        ct.SetColor(lab, Quantity_Color(*rgb, Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)
    w = STEPCAFControl_Writer(); w.SetColorMode(True); w.SetNameMode(True); w.Transfer(doc, STEPControl_AsIs)
    path = os.path.normpath(os.path.join(M, name + ".step"))
    assert w.Write(path) == IFSelect_RetDone
    print("wrote", path)


# STM32WB1MMC: LCSC's EasyEDA model (3dmodels/source/, SolidWorks export 2023-08-12), checked against ST's drawing:
# 6.5 x 10.0 x 1.372 total (ST: 1.372 +-0.046), 3 x 3 centre 0.6 pads in the lower half and the inner row at +1.49
# (ST 1.52) as in the footprint, so no rotation. Its pads end 0.02 below its origin: lifted 0.02 onto the board.
# Falls back to a plain envelope if the source file is missing.
from OCP.STEPControl import STEPControl_Reader
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.gp import gp_Trsf, gp_Vec
SRC = os.path.join(M, "source", "LGA-77_L10.0-W6.5-STM32WB1MMCH6TR_easyeda.step")
if os.path.exists(SRC):
    rd = STEPControl_Reader(); rd.ReadFile(SRC); rd.TransferRoots()
    t = gp_Trsf(); t.SetTranslation(gp_Vec(0, 0, 0.02))
    module = BRepBuilderAPI_Transform(rd.OneShape(), t, True).Shape()
else:
    module = box(-3.25, 3.25, -5.0, 5.0, 0.03, 1.372)
save("ST_LGA-77_STM32WB1MMC_6.5x10mm", [
    ("module", module, (0.55, 0.56, 0.58)),                                       # sputtered shield top
    ("pin A1 mark", dot(-2.55, 4.3, 1.372), (0.9, 0.9, 0.9)),
])
# M24512 UFDFPN8: 3.0 (X) x 2.0 (Y) x 0.55, pin 1 top-left
save("ST_UFDFPN-8-1EP_2x3mm_P0.5mm", [
    ("package", box(-1.5, 1.5, -1.0, 1.0, 0.0, 0.55), (0.12, 0.12, 0.13)),
    ("pin 1 mark", dot(-1.05, 0.55, 0.55, 0.25), (0.9, 0.9, 0.9)),
])
# S2761 test loop: 0.2 strip, legs at the pad ends, arch 1.15 high, 0.8 wide
save("TestPoint_Harwin_S2761_0603", [
    ("loop", fuse(box(-0.8, -0.6, -0.4, 0.4, 0.0, 1.15), box(0.6, 0.8, -0.4, 0.4, 0.0, 1.15),
                  box(-0.8, 0.8, -0.4, 0.4, 0.95, 1.15),
                  box(-0.8, -0.35, -0.4, 0.4, 0.0, 0.2), box(0.35, 0.8, -0.4, 0.4, 0.0, 0.2)), (0.85, 0.85, 0.87)),
])
