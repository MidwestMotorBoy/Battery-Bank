"""STEP model of the Shou Han TYPE-C 16PCB0.8 IP68 mid-mount receptacle (J401/J501), for the KiCad 3D view and the
enclosure design. Geometry taken from the maker's vector drawing (datasheets/usb-c-16pcb0.8-ip68.pdf, rev A5):
the outline strokes of every view were extracted, scaled (10.888 pt/mm, cross-checked against 10.25, 9.64, 7.45,
8.34 and 2.56) and measured; the numbers below are those measurements.

Needs the OpenCascade Python bindings (OCP, e.g. from `pip install --target DIR cadquery`; only OCP is used, so VTK
does not have to load). Run with a matching Python (KiCad 10's python is 3.11):
    python make_3d_usbc.py [dir_containing_OCP]
Writes ../3dmodels/USB_C_Receptacle_ShouHan_TYPE-C_16PCB0.8_IP68.step

Frame (KiCad model frame for the footprint): origin at the board-edge centre, X across the connector, +Y into the
board, Z up from the board top. Depths d below are from the mating face; Y = d - 1.949 (front leg centre d = 2.899
sits on the footprint slot at 0.95 mm inside the edge). Heights are from the receptacle centreline, which is 0.827
above the board top ("0.83" on the drawing).

Measured (drawing geometry; drawing dimension in brackets):
  shell lip      d 0.000-0.496   9.655 x 3.869  [9.64, 3.86]  corner R1.654
  seal ring      d 0.496-1.499   10.25 x 4.453  [10.25+-0.15, 4.45+-0.15]  corners R1.907, front/back edges R0.2
  front housing  d 1.499-2.502   10.05 x 3.868  corners R0.51 (fitted to the corners visible past the ring)
  main body      d 2.502-6.348   10.007 wide, +1.885 / -1.632  [10.00]  (bottom flush with the 0.8 mm board bottom)
  rear           d 6.348-7.450   9.588 wide, +1.939 / -1.632  [7.45 overall]
  mouth          8.354 x 2.568 stadium  [8.34 +0.06/-0.02, 2.56+-0.04]; lead-in 8.64 x 2.856 at the face
  legs (4)       0.70 wide at d 2.546-3.251 and 5.659-6.354  [2.90, 3.10, 0.70]; 0.20 sheet, bend R0.1/R0.3,
                 shelf on the board top, foot x 5.70-5.91 down to the board bottom; tips 11.81 [11.60+-0.25]
  tails (16)     0.209 wide, 0.154 thick on the board top, d 7.450-8.255 [0.80], x +-3.312/3.091 (A1,B12 / B1,A12),
                 +-2.513/2.292 (A4,B9 / B4,A9), +-1.752, +-1.251, +-0.749, +-0.253
Drawing inconsistencies (all inside the stated tolerances): the front view draws the ring 10.36 x 4.35 while the
top and side views draw 10.25 x 4.45 (the dimensioned value, used here); leg tips are drawn 11.81 apart against the
11.60 +-0.25 dimension (the drawn geometry is used, since it matches the footprint slots at +-5.80).
Not defined by the drawing (assumed): plug cavity depth 6.20 (USB-C receptacle convention), tongue 6.70 x 0.70
starting 0.95 behind the face, main body / rear corner radius R0.30, the shell inside the ring continues the lip
profile. None of these change the outside envelope.
"""
import os
import sys

if len(sys.argv) > 1:
    sys.path.insert(0, sys.argv[1])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeWire
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakePrism
from OCP.BRep import BRep_Tool
from OCP.GC import GC_MakeArcOfCircle, GC_MakeSegment
from OCP.gp import gp_Pnt, gp_Vec
from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDocStd import TDocStd_Document
from OCP.TopAbs import TopAbs_EDGE, TopAbs_VERTEX
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.XCAFDoc import XCAFDoc_ColorType, XCAFDoc_DocumentTool

HERE = os.path.dirname(os.path.abspath(__file__))
# Board thickness: 0.8 (TYPE-C 16PCB0.8 IP68) or 1.6 (TYPE-C 16PCB1.6 IP68). The two variants share the land pattern,
# notch and body; the body drops through the board so that its bottom is flush with the board bottom.
BOARD_T = float(sys.argv[1]) if len(sys.argv) > 1 else 0.8
OUT = os.path.join(HERE, "..", "3dmodels", f"USB_C_Receptacle_ShouHan_TYPE-C_16PCB{BOARD_T:g}_IP68.step")

ZC = 1.632 - BOARD_T - 0.005  # receptacle centreline above the board top (0.827 on the 0.8 mm board: "0.83")
Y0 = -1.949                   # mating face (Y = d + Y0)


def Y(d):
    return d + Y0


def rrect(w, zlo, zhi, r, d0, d1):
    """Rounded rectangle in the XZ plane (width w centred on X = 0, Z zlo..zhi relative to the centreline, corner
    radius r) extruded from depth d0 to d1."""
    y = Y(d0)
    x1, z0, z1 = w / 2, ZC + zlo, ZC + zhi
    P = lambda x, z: gp_Pnt(x, y, z)
    wire = BRepBuilderAPI_MakeWire()
    pts = [(-x1 + r, z0), (x1 - r, z0), (x1, z0 + r), (x1, z1 - r), (x1 - r, z1), (-x1 + r, z1), (-x1, z1 - r), (-x1, z0 + r)]
    cen = [None, (x1 - r, z0 + r), None, (x1 - r, z1 - r), None, (-x1 + r, z1 - r), None, (-x1 + r, z0 + r)]
    for i in range(8):
        a, b = pts[i], pts[(i + 1) % 8]
        if i % 2 == 0:            # straight
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) > 1e-6:
                wire.Add(BRepBuilderAPI_MakeEdge(GC_MakeSegment(P(*a), P(*b)).Value()).Edge())
        else:                     # 90 degree arc a -> b around cen
            c = cen[i]
            m = ((a[0] + b[0]) / 2 - c[0], (a[1] + b[1]) / 2 - c[1])
            k = r / (m[0] ** 2 + m[1] ** 2) ** 0.5
            mid = P(c[0] + m[0] * k, c[1] + m[1] * k)
            wire.Add(BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(P(*a), mid, P(*b)).Value()).Edge())
    face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()
    return BRepPrimAPI_MakePrism(face, gp_Vec(0, d1 - d0, 0)).Shape()


def box(x0, x1, y0, y1, z0, z1):
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), x1 - x0, y1 - y0, z1 - z0).Shape()


def fuse(*s):
    out = s[0]
    for t in s[1:]:
        out = BRepAlgoAPI_Fuse(out, t).Shape()
    return out


def cut(a, b):
    return BRepAlgoAPI_Cut(a, b).Shape()


def fillet_end_loops(shape, ys, r):
    """Fillet every edge lying in one of the planes Y = ys (the outer loops of the end faces)."""
    mk = BRepFilletAPI_MakeFillet(shape)
    ex = TopExp_Explorer(shape, TopAbs_EDGE)
    while ex.More():
        e = TopoDS.Edge_s(ex.Current())
        vy = []
        vx = TopExp_Explorer(e, TopAbs_VERTEX)
        while vx.More():
            vy.append(BRep_Tool.Pnt_s(TopoDS.Vertex_s(vx.Current())).Y())
            vx.Next()
        if vy and any(all(abs(v - yy) < 1e-6 for v in vy) for yy in ys):
            mk.Add(r, e)
        ex.Next()
    return mk.Shape()


# --- shell / housing (PA9T, black) -------------------------------------------------------------------------------
lip_profile = dict(w=9.655, zlo=-1.934, zhi=1.935, r=1.654)
shell = fuse(rrect(d0=0.000, d1=1.499, **lip_profile),                       # lip, continuing inside the seal
             rrect(10.05, -1.929, 1.939, 0.51, 1.499, 2.502),                # front housing
             rrect(10.007, -1.632, 1.885, 0.30, 2.502, 6.348),               # main body (bottom flush with board bottom)
             rrect(9.588, -1.632, 1.939, 0.30, 6.348, 7.450))                # rear
mouth = rrect(8.354, -1.284, 1.284, 1.284, -0.01, 6.20)                      # plug opening (stadium)
leadin = rrect(8.64, -1.428, 1.428, 1.428, -0.01, 0.20)                      # lead-in at the face
shell = cut(cut(shell, mouth), leadin)

# --- IP68 seal ring (silicone, red) --------------------------------------------------------------------------------
ring = rrect(10.25, -2.2265, 2.2265, 1.907, 0.496, 1.499)
ring = fillet_end_loops(ring, (Y(0.496), Y(1.499)), 0.2)
ring = cut(ring, rrect(d0=0.4, d1=1.6, **lip_profile))                       # sits on the shell

# --- tongue (LCP, black) -------------------------------------------------------------------------------------------
tongue = box(-3.35, 3.35, Y(0.95), Y(6.20), ZC - 0.35, ZC + 0.35)

# --- mounting legs (SUS, Ni): 0.2 sheet, shelf on the board top, R0.1/R0.3 bend, foot to the board bottom ---------
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.gp import gp_Ax2, gp_Dir
legs = []
for sx in (-1, 1):
    for d0, d1 in ((2.546, 3.251), (5.659, 6.354)):
        y0, y1 = Y(d0), Y(d1)
        shelf = box(5.0035 if sx > 0 else -5.6, 5.6 if sx > 0 else -5.0035, y0, y1, 0.0, 0.2)
        foot = box(5.7 if sx > 0 else -5.9, 5.9 if sx > 0 else -5.7, y0, y1, -BOARD_T - 0.009, -0.1)
        # bend: quarter annulus, centre (+-5.6, -0.1), R0.1 / R0.3, axis along Y
        outer = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(sx * 5.6, y0, -0.1), gp_Dir(0, 1, 0)), 0.3, y1 - y0).Shape()
        inner = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(sx * 5.6, y0, -0.1), gp_Dir(0, 1, 0)), 0.1, y1 - y0).Shape()
        quad = box(5.6 if sx > 0 else -5.9, 5.9 if sx > 0 else -5.6, y0, y1, -0.1, 0.2)
        bend = cut(BRepAlgoAPI_Cut(outer, inner).Shape(), cut(box(-6.2, 6.2, y0 - 0.1, y1 + 0.1, -0.5, 0.5), quad))
        legs.append(fuse(shelf, bend, foot))
legs = fuse(*legs)

# --- SMT tails (gold flash) ----------------------------------------------------------------------------------------
TAILS = (-3.312, -3.091, -2.513, -2.292, -1.752, -1.251, -0.749, -0.253,
         0.253, 0.749, 1.251, 1.752, 2.292, 2.513, 3.091, 3.312)
tails = fuse(*[box(x - 0.1045, x + 0.1045, Y(7.45), Y(8.255), 0.0, 0.154) for x in TAILS])

doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
shapes = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
colors = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
for name, shape, rgb in (("shell", shell, (0.10, 0.10, 0.11)),       # PA9T black
                         ("seal", ring, (0.80, 0.12, 0.10)),         # red silicone ring
                         ("tongue", tongue, (0.16, 0.16, 0.17)),     # LCP black
                         ("legs", legs, (0.78, 0.78, 0.80)),         # SUS, Ni plated
                         ("contacts", tails, (0.85, 0.70, 0.30))):   # gold flash
    label = shapes.AddShape(shape, False)
    TDataStd_Name.Set_s(label, TCollection_ExtendedString(name))
    colors.SetColor(label, Quantity_Color(*rgb, Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
w = STEPCAFControl_Writer()
w.SetColorMode(True)
w.SetNameMode(True)
w.Transfer(doc, STEPControl_AsIs)
assert w.Write(os.path.normpath(OUT)) == IFSelect_RetDone
print("wrote", os.path.normpath(OUT))
