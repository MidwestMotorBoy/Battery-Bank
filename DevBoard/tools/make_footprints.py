"""Generate the project footprint library MonolithDev.pretty.

Every footprint is drawn from the datasheet in ../../datasheets (page noted per footprint).
Coordinates are KiCad's (mm, +y down, top view) unless a helper says otherwise.

    python tools/make_footprints.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "MonolithDev.pretty")
STD = "(stroke (width {w}) (type solid))"

# 3D models borrowed from KiCad's library: same body and pin-1 corner (checked against the KiCad footprint each model
# belongs to, or built by tools/make_3d_usbc.py; rotation in degrees about Z, KiCad turns positive angles clockwise seen from the top: checked in a 3D render). Not modelled: net tie (no part). STM32WB1MMC, UFDFPN8 and the SMT test loop come from tools/make_3d_simple.py.
M3D = "${KICAD10_3DMODEL_DIR}/"
MODELS = {
    "Infineon_PG-TDSON-8-57_HalfBridge": ("Package_TO_SOT_SMD.3dshapes/TDSON-8-1.step", 270),    # single-FET body
    "AGM_PDFN-8_3.3x3.3mm_P0.65mm": ("Package_SON.3dshapes/VSON-8_3.3x3.3mm_P0.65mm_NexFET.step", 270),
    "TI_RSM0032A_VQFN-32_4x4mm_P0.4mm_EP1.4x1.4mm": ("Package_DFN_QFN.3dshapes/QFN-32-1EP_4x4mm_P0.4mm_EP2.65x2.65mm.step", 0),
    "TI_VQFN-36-1EP_RRV0036A_5x6mm_P0.5mm": ("Package_DFN_QFN.3dshapes/QFN-36-1EP_5x6mm_P0.5mm_EP3.6x4.6mm.step", 0),
    "TI_WQFN-38-2EP_REF0038A_6x4mm_P0.4mm_2oz": ("Package_DFN_QFN.3dshapes/Texas_RNQ0040A_WQFN-40-1EP_6x4mm_P0.4mm_EP4.7x2.7mm.step", 0),
    "USB_C_Receptacle_ShouHan_TYPE-C_16PCB0.8_IP68": ("${KIPRJMOD}/3dmodels/USB_C_Receptacle_ShouHan_TYPE-C_16PCB0.8_IP68.step", 0),  # tools/make_3d_usbc.py
    "BatteryHolder_MYOUNG_BH-21700-B1BJ001": [   # tools/make_3d_holder.py; the cell is a separate model (provisional height)
        ("${KIPRJMOD}/3dmodels/BatteryHolder_MYOUNG_BH-21700-B1BJ001.step", 0),
        ("${KIPRJMOD}/3dmodels/Cell_EVE_INR21700-58E_in_BH-21700.step", 0)],
    "ST_LGA-77_STM32WB1MMC_6.5x10mm": ("${KIPRJMOD}/3dmodels/ST_LGA-77_STM32WB1MMC_6.5x10mm.step", 0),  # tools/make_3d_simple.py
    "ST_UFDFPN-8-1EP_2x3mm_P0.5mm_EP1.2x1.4mm": ("${KIPRJMOD}/3dmodels/ST_UFDFPN-8-1EP_2x3mm_P0.5mm.step", 0),  # tools/make_3d_simple.py
    "TestPoint_Harwin_S2761_0603": ("${KIPRJMOD}/3dmodels/TestPoint_Harwin_S2761_0603.step", 0),  # tools/make_3d_simple.py
    "TI_YFF0009_DSBGA-9_P0.4mm": ("${KIPRJMOD}/3dmodels/TI_YFF0009_DSBGA-9.step", 0),  # tools/make_3d_simple.py
    "TLC_WSFB_4x3mm": ("${KIPRJMOD}/3dmodels/TLC_WSFB_4x3mm.step", 0),  # tools/make_3d_simple.py
    "L_Coilank_APS0530": ("Inductor_SMD.3dshapes/L_Bourns_SRP5030T.step", 0),   # same body class (5.7 x 5.2 x 3.0)
    "Samtec_FTSH-105-01-xx-DV-K_2x05_P1.27mm": ("Connector_PinHeader_1.27mm.3dshapes/PinHeader_2x05_P1.27mm_Vertical_SMD.step", 0),
}


def model_block(name):
    if name not in MODELS:
        return ""
    entries = MODELS[name] if isinstance(MODELS[name], list) else [MODELS[name]]
    return "".join(_one_model(path, rot) for path, rot in entries)


def _one_model(path, rot):
    full = path if path.startswith("${") else M3D + path
    return (f'\t(model "{full}"\n\t\t(offset\n\t\t\t(xyz 0 0 0)\n\t\t)\n\t\t(scale\n\t\t\t(xyz 1 1 1)\n'
            f'\t\t)\n\t\t(rotate\n\t\t\t(xyz 0 0 {rot})\n\t\t)\n\t)\n')


def with_model(s, name):
    """Replace any (model ...) blocks in a footprint file string with the one from MODELS."""
    while "\n\t(model " in s:
        a = s.index("\n\t(model ") + 1
        d, i = 0, a + 1                        # a is the tab; count from the opening paren
        while True:
            d += {"(": 1, ")": -1}.get(s[i], 0)
            i += 1
            if d == 0:
                break
        s = s[:a] + s[i:].lstrip("\n")
    k = s.rstrip().rindex(")")
    return s[:k] + model_block(name) + s[k:]


def f(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") if v != 0 else "0"


class FP:
    def __init__(self, name, descr, tags, attr="smd"):
        self.name, self.descr, self.tags, self.attr = name, descr, tags, attr
        self.items = []
        self.extra = []

    # --- graphics -------------------------------------------------------
    def line(self, x0, y0, x1, y1, layer, w=0.12):
        self.items.append(f'(fp_line (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) {STD.format(w=f(w))} (layer "{layer}"))')

    def rect(self, x0, y0, x1, y1, layer, w=0.12, fill=False):
        fl = "yes" if fill else "no"
        self.items.append(f'(fp_rect (start {f(x0)} {f(y0)}) (end {f(x1)} {f(y1)}) {STD.format(w=f(w))} (fill {fl}) (layer "{layer}"))')

    def circle(self, x, y, r, layer, w=0.12):
        self.items.append(f'(fp_circle (center {f(x)} {f(y)}) (end {f(x + r)} {f(y)}) {STD.format(w=f(w))} (fill no) (layer "{layer}"))')

    def poly(self, pts, layer, w=0, fill=True):
        p = " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts)
        self.items.append(f'(fp_poly (pts {p}) {STD.format(w=f(w))} (fill {"yes" if fill else "no"}) (layer "{layer}"))')

    def text(self, s, x, y, layer, size=1.0):
        self.items.append(f'(fp_text user "{s}" (at {f(x)} {f(y)}) (layer "{layer}") (effects (font (size {f(size)} {f(size)}) (thickness {f(size * 0.15)}))))')

    # --- pads -----------------------------------------------------------
    def smd(self, num, x, y, w, h, layers=("F.Cu", "F.Paste", "F.Mask"), shape="rect", extra=""):
        L = " ".join(f'"{l}"' for l in layers)
        rr = " (roundrect_rratio 0.25)" if shape == "roundrect" else ""
        self.items.append(f'(pad "{num}" smd {shape} (at {f(x)} {f(y)}) (size {f(w)} {f(h)}) (layers {L}){rr}{extra})')

    def smd_box(self, num, x0, y0, x1, y1, **kw):
        self.smd(num, (x0 + x1) / 2, (y0 + y1) / 2, abs(x1 - x0), abs(y1 - y0), **kw)

    def paste(self, x, y, w, h):
        self.smd("", x, y, w, h, layers=("F.Paste",))

    def custom(self, num, pts, anchor, layers=("F.Cu", "F.Mask")):
        """Custom-shape SMD pad from an absolute polygon; anchor (x, y) must lie inside the polygon."""
        ax, ay = anchor
        rel = " ".join(f"(xy {f(x - ax)} {f(y - ay)})" for x, y in pts)
        L = " ".join(f'"{l}"' for l in layers)
        self.items.append(
            f'(pad "{num}" smd custom (at {f(ax)} {f(ay)}) (size 0.2 0.2) (layers {L}) '
            f'(options (clearance outline) (anchor rect)) '
            f'(primitives (gr_poly (pts {rel}) (width 0) (fill yes))))')

    def npth(self, x, y, d):
        self.items.append(f'(pad "" np_thru_hole circle (at {f(x)} {f(y)}) (size {f(d)} {f(d)}) (drill {f(d)}) (layers "*.Cu" "*.Mask"))')

    def slot(self, num, x, y, pw, ph, dw, dh):
        self.items.append(f'(pad "{num}" thru_hole oval (at {f(x)} {f(y)}) (size {f(pw)} {f(ph)}) (drill oval {f(dw)} {f(dh)}) (layers "*.Cu" "*.Mask"))')

    # --- output ---------------------------------------------------------
    def write(self, ref_y, val_y):
        head = (f'(footprint "{self.name}"\n\t(version 20241229)\n\t(generator "make_footprints.py")\n\t(layer "F.Cu")\n'
                f'\t(descr "{self.descr}")\n\t(tags "{self.tags}")\n'
                f'\t(property "Reference" "REF**" (at 0 {f(ref_y)} 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))\n'
                f'\t(property "Value" "{self.name}" (at 0 {f(val_y)} 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))\n'
                f'\t(attr {self.attr})\n')
        body = "".join(f"\t{e}\n" for e in self.extra + self.items)
        body += '\t(fp_text user "${REFERENCE}" (at 0 0 0) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.08))))\n'
        body += model_block(self.name)
        with open(os.path.join(LIB, self.name + ".kicad_mod"), "w", newline="\n") as fh:
            fh.write(head + body + ")\n")
        print("wrote", self.name)


def crt(fp, x0, y0, x1, y1):
    fp.rect(x0, y0, x1, y1, "F.CrtYd", 0.05)


def flip(pts):
    """Datasheet drawings are y-up; KiCad is y-down."""
    return [(x, -y) for x, y in pts]


os.makedirs(LIB, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. MYOUNG BH-21700-B1BJ001 SMT 21700 holder. bh-21700-b1bj001.pdf, "PCB Layout Diagram".
#    The layout is labelled "bottom view" but is the top view flipped about the long axis
#    (checked against the top view: + terminal and molded "+" on the left, left peg low).
#    Pads 7.5 x 9.0, outer pad edges 93.6 apart; pegs (dia 3.2) into 4.0 holes at +/-34, 8.5.
#    Rev A5: added the dia 2.25 hole for the + terminal tab (missing before; the holder would not seat flat).
fp = FP("BatteryHolder_MYOUNG_BH-21700-B1BJ001", "MYOUNG BH-21700-B1BJ001 SMT single 21700 holder, pad 1 = +",
        "21700 battery holder SMT")
for num, x in (("1", -43.05), ("2", 43.05)):
    fp.smd(num, x, 0, 7.5, 9.0)
fp.npth(-34.0, 8.5, 4.0)
fp.npth(34.0, -8.5, 4.0)
# + terminal locating tab: the side view shows a fork below the seating plane 38.60 from the centre at the + end;
# the layout gives its hole as dia 2.25, 11.50 off the pad centreline (bottom view -> y flipped, like the pegs).
fp.npth(-38.6, -11.5, 2.25)
fp.rect(-41.25, -12.5, 41.25, 12.5, "F.Fab", 0.1)
fp.circle(0, 0, 10.5, "F.Fab", 0.1)
fp.line(-41.4, -12.65, -40.1, -12.65, "F.SilkS")            # gap over the + tab hole
fp.line(-37.1, -12.65, 41.4, -12.65, "F.SilkS")
fp.line(-41.4, 12.65, 41.4, 12.65, "F.SilkS")
for x in (-41.4, 41.4):
    fp.line(x, -12.65, x, -4.75, "F.SilkS")
    fp.line(x, 4.75, x, 12.65, "F.SilkS")
fp.text("+", -36.5, 0, "F.SilkS", 2.5)
fp.text("-", 36.5, 0, "F.SilkS", 2.5)
crt(fp, -47.3, -13.0, 47.3, 13.0)
fp.write(-14.2, 14.2)

# ---------------------------------------------------------------------------
# 2. Shou Han TYPE-C 16PCB0.8 IP68 mid-mount receptacle. usb-c-16pcb0.8-ip68.pdf p.1 "Recommend P.C.B layout".
#    Origin = board edge centre; board interior is -y. Needs a 10.20 wide x 5.65 deep edge cutout
#    (drawn on Edge.Cuts here). Signal pads 1.0 long, 5.85-6.85 mm from the edge (see yp).
fp = FP("USB_C_Receptacle_ShouHan_TYPE-C_16PCB0.8_IP68",
        "Shou Han TYPE-C 16PCB0.8 IP68 USB 2.0 receptacle, mid-mount in a 10.2 x 5.65 board-edge cutout, origin = board edge",
        "USB C Type-C receptacle USB2.0 16P mid-mount")
yp = -6.35   # maker's layout: pads 5.65-6.65 from the edge, starting right on the notch's back edge. Moved
             # 0.2 mm in (5.85-6.85) for JLC's 0.2 mm copper-to-routed-edge rule (edge tolerance is +/-0.2 mm).
for nums, x, w in ((("A1", "B12"), -3.2, 0.6), (("A4", "B9"), -2.4, 0.6), (("B8",), -1.75, 0.3), (("A5",), -1.25, 0.3),
                   (("B7",), -0.75, 0.3), (("A6",), -0.25, 0.3), (("A7",), 0.25, 0.3), (("B6",), 0.75, 0.3),
                   (("A8",), 1.25, 0.3), (("B5",), 1.75, 0.3), (("B4", "A9"), 2.4, 0.6), (("B1", "A12"), 3.2, 0.6)):
    for n in nums:
        fp.smd(n, x, yp, w, 1.0)
for x in (-5.8, 5.8):
    for y in (-0.95, -4.05):
        fp.slot("SH", x, y, 0.9, 1.4, 0.5, 1.0)
# board cutout
fp.line(-5.1, 0, -5.1, -5.65, "Edge.Cuts", 0.1)
fp.line(-5.1, -5.65, 5.1, -5.65, "Edge.Cuts", 0.1)
fp.line(5.1, -5.65, 5.1, 0, "Edge.Cuts", 0.1)
fp.text("PCB edge", 0, 0.8, "Dwgs.User", 0.6)
fp.line(-7, 0, 7, 0, "Dwgs.User", 0.1)
fp.rect(-5.0, -6.4, 5.0, 2.5, "F.Fab", 0.1)
crt(fp, -6.5, -7.0, 6.5, 2.75)
fp.write(-8.0, 3.6)

# ---------------------------------------------------------------------------
# 3. Infineon PG-TDSON-8-57 half-bridge (IAUC45N04S6L063H). iauc45n04s6l063h.pdf p.8 "Footprint".
#    Pins 1 G_HS, 2/3 phase, 4 G_LS, 5/6 LS source (ground), 7/8 HS drain (battery).
#    Datasheet coordinates are y-up from package centre. The HS drain pad (8) and the phase pad (3)
#    each sit next to their lead bar; the datasheet joins them with copper under solder mask, so
#    connect each pair with copper in layout (same net). Paste uses the datasheet stencil
#    (0.15 mm stencil), copper pads carry no paste of their own.
fp = FP("Infineon_PG-TDSON-8-57_HalfBridge",
        "Infineon PG-TDSON-8-57 dual N-FET half-bridge (IAUC45N04S6L063H), land and stencil per datasheet",
        "TDSON-8-57 half-bridge Infineon")
CU = ("F.Cu", "F.Mask")
for num, x in (("1", -1.905), ("4", 1.905)):
    fp.smd(num, x, 2.97, 0.6, 1.4, layers=CU)                                   # gates, y-up -2.97
fp.smd_box("2", -0.935, 2.23, -0.335, 3.67, layers=CU)
fp.custom("3", flip([(-1.155, -1.61), (0.935, -1.61), (0.935, -3.67), (0.335, -3.67), (0.335, -2.54),
                     (-0.335, -2.54), (-0.335, -2.33), (-1.155, -2.33)]), anchor=(0, 1.9))
fp.smd_box("3", 0.285, -1.31, 2.205, 1.29, layers=CU)                        # phase pad, y-up -1.29..1.31
fp.custom("8", flip([(-2.205, 1.80), (-0.335, 1.80), (-0.335, 2.50), (-1.605, 2.50), (-1.605, 3.67), (-2.205, 3.67)]), anchor=(-1.27, -2.15))
fp.smd_box("7", -0.935, -3.67, -0.335, -2.40, layers=CU)
fp.smd_box("8", -2.205, -1.30, -0.285, 1.09, layers=CU)                       # HS drain pad, y-up -1.09..1.30
fp.custom("5", flip([(0.335, 1.80), (2.205, 1.80), (2.205, 3.67), (1.605, 3.67), (1.605, 2.50), (0.335, 2.50)]), anchor=(1.27, -2.15))
fp.smd_box("6", 0.335, -3.67, 0.935, -2.40, layers=CU)
# stencil apertures (y-up in the datasheet -> negate)
for x in (-1.905, -0.635, 0.635, 1.905):
    for y in (3.045, -3.045):
        fp.paste(x, -y, 0.5, 1.15)
fp.paste(-1.245, -2.05, 0.87, 0.4)
fp.paste(1.27, -2.06, 0.67, 0.4)
for y in (0.595, -0.405):
    fp.paste(-1.245, -y, 1.05, 0.75)
for y in (0.49, -0.51):
    fp.paste(1.24, -y, 1.15, 0.75)
fp.paste(-0.15, 1.96, 1.57, 0.6)
fp.rect(-2.575, -3.0, 2.575, 3.0, "F.Fab", 0.1)
fp.line(-2.0, 3.0, -2.575, 2.425, "F.Fab", 0.1)
fp.line(-2.75, -2.3, -2.75, 2.3, "F.SilkS")
fp.line(2.75, -2.3, 2.75, 2.3, "F.SilkS")
fp.circle(-2.6, 3.85, 0.15, "F.SilkS", 0.3)                                  # pin 1 dot
crt(fp, -2.95, -4.1, 2.95, 4.25)
fp.write(-4.9, 5.0)

# ---------------------------------------------------------------------------
# 4. ST STM32WB1MMC SiP-LGA77, 6.5 x 10 mm. stm32wb1mmc.pdf p.17 fig. 11 and table 3.
#    Pad centres were read from the vector drawing (bottom view) and mirrored in x for the top view.
#    The drawing labels two centre pads "73"; by the serpentine order the lower-middle one is 72.
#    1:1 NSMD lands (pad = package lead size).
fp = FP("ST_LGA-77_STM32WB1MMC_6.5x10mm",
        "STM32WB1MMC Bluetooth module, SiP-LGA77 6.5 x 10 mm, 0.45/0.5 mm pitch (DS14096 fig. 11)",
        "STM32WB1MMC LGA77 module BLE")
pads = {}
for i, y in enumerate((-4.55, -3.95, -3.35, -2.75, -2.15, -1.52, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.53)):
    pads[1 + i] = (2.78, y)                                                     # 1..18 right column (bottom view)
for i, x in enumerate((2.25, 1.8, 1.35, 0.9, 0.45, 0.0, -0.45, -0.9, -1.35, -1.8, -2.25)):
    pads[19 + i] = (x, 4.53)                                                    # 19..29 bottom row
for i, y in enumerate((4.53, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5, 0.0, -0.5, -1.0, -1.52, -2.15, -2.75, -3.35, -3.95, -4.55)):
    pads[30 + i] = (-2.77, y)                                                   # 30..47 left column
for i, y in enumerate((-4.55, -3.95, -3.35, -2.75, -2.15)):
    pads[48 + i] = (-2.25, y)                                                   # 48..52 inner left
for i, x in enumerate((-2.25, -1.8, -1.35, -0.9, -0.45, 0.0, 0.45, 0.9, 1.35, 1.8, 2.25)):
    pads[53 + i] = (x, -1.52)                                                   # 53..63 inner row
for i, y in enumerate((-2.15, -2.75, -3.35, -3.95, -4.55)):
    pads[64 + i] = (2.25, y)                                                    # 64..68 inner right
for n, (x, y) in zip(range(69, 78), ((0.95, 0.45), (0.95, 1.5), (0.95, 2.55), (0.0, 2.55), (0.0, 1.5), (0.0, 0.45),
                                     (-0.95, 0.45), (-0.95, 1.5), (-0.95, 2.55))):
    pads[n] = (x, y)
corner = {6, 18, 30, 42}
outer_col = set(range(1, 19)) | set(range(30, 48))
inner_col = set(range(48, 53)) | set(range(64, 69))
for n, (xb, y) in sorted(pads.items()):
    x = -xb                                                                     # bottom view -> top view
    if n >= 69:
        w = h = 0.6
    elif n in corner:
        w = h = 0.35
    elif n in outer_col:
        w, h = 0.35, 0.30
    elif n in inner_col:
        w = h = 0.30
    else:
        w, h = 0.30, 0.35
    fp.smd(str(n), x, y, w, h)
fp.rect(-3.25, -5.0, 3.25, 5.0, "F.Fab", 0.1)
fp.line(-3.25, -4.4, -2.65, -5.0, "F.Fab", 0.1)
fp.line(-3.4, -5.15, 3.4, -5.15, "F.SilkS")
fp.line(-3.4, 5.15, 3.4, 5.15, "F.SilkS")
fp.line(-3.4, -5.15, -3.4, -4.8, "F.SilkS")
fp.circle(-3.65, -4.55, 0.12, "F.SilkS", 0.24)
crt(fp, -3.5, -5.25, 3.5, 5.25)
fp.text("Antenna keep-out: see ST hardware guidelines", 0, -6.4, "Cmts.User", 0.5)
fp.write(-6.0, 6.0)

# ---------------------------------------------------------------------------
# 5. ST UFDFPN8 2 x 3 mm (M24512-DF). m24512.pdf p.30 fig. 16 recommended footprint:
#    leads 0.3 x 0.6 at 0.5 pitch, rows 1.3 from centre, exposed pad 1.4 x 1.2.
#    ST: the exposed pad goes to VSS or floats -> numbered 4 (VSS) here.
#    Drawn with pins 1-4 down the left side (pin 1 top-left), so x = row axis.
fp = FP("ST_UFDFPN-8-1EP_2x3mm_P0.5mm_EP1.2x1.4mm",
        "ST UFDFPN8 (MLP8) 2 x 3 mm, 0.5 mm pitch, exposed pad tied to VSS (pin 4); DS6520 fig. 16",
        "UFDFPN8 DFN-8 MLP8 M24512")
for i in range(4):
    y = -0.75 + 0.5 * i
    fp.smd(str(1 + i), -1.3, y, 0.6, 0.3, shape="roundrect")
    fp.smd(str(8 - i), 1.3, y, 0.6, 0.3, shape="roundrect")
fp.smd("4", 0, 0, 1.2, 1.4, layers=("F.Cu", "F.Mask"))
fp.paste(0, 0, 1.0, 1.2)
fp.rect(-1.5, -1.0, 1.5, 1.0, "F.Fab", 0.1)
fp.line(-1.5, -0.6, -1.1, -1.0, "F.Fab", 0.1)
fp.line(-0.85, -1.15, 0.85, -1.15, "F.SilkS")
fp.line(-0.85, 1.15, 0.85, 1.15, "F.SilkS")
fp.circle(-1.85, -1.1, 0.1, "F.SilkS", 0.2)
crt(fp, -1.85, -1.25, 1.85, 1.25)
fp.write(-2.0, 2.0)

# ---------------------------------------------------------------------------
# 6. 10 A copper link between two nets (replaces the 2512 0R at R430/R530). Net tie: two 3 x 3 pads
#    joined by a 3 mm wide copper bar; widen with zones in layout as needed.
fp = FP("NetTie-2_SMD_3x3mm_Bridge3mm", "Net tie, two 3 x 3 mm pads joined by 3 mm copper, for a ~10 A link",
        "net tie bridge high current", attr="smd exclude_from_pos_files exclude_from_bom")
fp.extra.append('(net_tie_pad_groups "1,2")')
fp.smd("1", -2.0, 0, 3.0, 3.0, layers=("F.Cu", "F.Mask"))
fp.smd("2", 2.0, 0, 3.0, 3.0, layers=("F.Cu", "F.Mask"))
fp.poly([(-2.0, -1.5), (2.0, -1.5), (2.0, 1.5), (-2.0, 1.5)], "F.Cu")
crt(fp, -3.75, -1.75, 3.75, 1.75)
fp.write(-2.5, 2.5)

# ---------------------------------------------------------------------------
# 8. AGMSEMI AGM404AP1 PDFN3.3x3.3 (protection FETs Q101/Q102). agm404ap1.pdf p.7, first table (typ.):
#    D 3.1 along the lead rows, E 3.0 body, E1 3.3 over the leads, e 0.65, b 0.3, L 0.4 (source/gate leads),
#    drain pad D1 2.45 x E2 1.52 reached from the drain-side lead tips through L1 0.33 + H 0.415.
#    No land pattern in the datasheet: leads get 0.4 x 0.75 lands (0.3 mm toe, 0.05 mm heel); the drain
#    side is one 2.45 mm wide land from 0.3 mm past the lead tips to the drain pad's inner edge.
#    Top view, pin 1 bottom-left: 1-3 S, 4 G along the bottom; 5-8 D along the top (5 above pin 4).
#    The drain land is pad 5; pads 6-8 overlap it so every symbol pin has a pad.
fp = FP("AGM_PDFN-8_3.3x3.3mm_P0.65mm", "AGMSEMI PDFN3.3x3.3 (AGM404AP1) single N-FET, S 1-3, G 4, D 5-8 + drain pad",
        "PDFN3.3x3.3 DFN3333 MOSFET AGM404AP1")
xs = (-0.975, -0.325, 0.325, 0.975)
for i, x in enumerate(xs):
    fp.smd(str(1 + i), x, 1.575, 0.4, 0.75)
fp.smd_box("5", -1.225, -1.95, 1.225, 0.615, layers=("F.Cu", "F.Mask"))
for n, x in zip(("6", "7", "8"), xs[::-1][1:]):
    fp.smd(n, x, -1.65, 0.4, 0.6, layers=("F.Cu", "F.Mask"))
for x in (-0.6, 0.6):
    for y in (-1.35, -0.25):
        fp.paste(x, y, 0.95, 0.85)
fp.rect(-1.55, -1.5, 1.55, 1.5, "F.Fab", 0.1)
fp.line(-1.55, 1.1, -1.15, 1.5, "F.Fab", 0.1)
fp.line(-1.75, -1.0, -1.75, 1.0, "F.SilkS")
fp.line(1.75, -1.0, 1.75, 1.0, "F.SilkS")
fp.circle(-1.45, 2.25, 0.1, "F.SilkS", 0.2)
crt(fp, -1.75, -2.2, 1.75, 2.2)
fp.write(-3.0, 3.0)

# ---------------------------------------------------------------------------
# 7. TI RRV0036A VQFN-36 5 x 6 mm (BQ25756). From Antmicro's open hardware library (Apache-2.0, via
#    partreel.com); checked against bq25756.pdf p.81 land pattern: pads 0.25 x 0.6 at (+/-2.4, +/-2.9),
#    EP 3.6 x 4.6, pin 1 top of the left column. Thermal vias are added in layout.
src = os.path.join(HERE, "third_party", "antmicro_bq25756errvr.kicad_mod")
dst = os.path.join(LIB, "TI_VQFN-36-1EP_RRV0036A_5x6mm_P0.5mm.kicad_mod")
s = open(src, encoding="utf-8").read()
s = re.sub(r'\(footprint "[^"]+"', '(footprint "TI_VQFN-36-1EP_RRV0036A_5x6mm_P0.5mm"', s, count=1)
s = re.sub(r'(\(property "Value" )"[^"]+"', r'\1"TI_VQFN-36-1EP_RRV0036A_5x6mm_P0.5mm"', s, count=1)
s = s.replace("(size 0.7 0.7)", "(size 1 1)")                 # JLC legend: text >= 0.8 mm
s = with_model(s, "TI_VQFN-36-1EP_RRV0036A_5x6mm_P0.5mm")       # the Antmicro .glb is not shipped
with open(dst, "w", newline="\n") as fh:
    fh.write(s)
print("wrote", os.path.basename(dst)[:-10])

# ---------------------------------------------------------------------------
# 9. TI REF0038A WQFN-38 (TPS25751), KiCad's footprint with the two solder-mask-defined power pads (20-22 PPHV,
#    23-25 VBUS) trimmed 0.025 mm on their shared edge: KiCad/TI leave 0.125 mm of copper between them, JLC needs
#    0.15 mm on 2 oz outer copper. The mask openings, and so the soldered area, are TI's.
src = r"C:/Program Files/KiCad/10.0/share/kicad/footprints/Package_DFN_QFN.pretty/Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4.kicad_mod"
name = "TI_WQFN-38-2EP_REF0038A_6x4mm_P0.4mm_2oz"
s = open(src, encoding="utf-8").read()
s = re.sub(r'\(footprint "[^"]+"', f'(footprint "{name}"', s, count=1)
s = re.sub(r'(\(property "Value" )"[^"]+"', lambda m: m.group(1) + f'"{name}"', s, count=1)
for num, y0, y1 in (("20", "0.6625", "0.675"), ("23", "-0.6625", "-0.675")):
    s, n = re.subn(r'(\(pad "' + num + r'" smd roundrect\s*\(at 2\.925 )' + re.escape(y0) + r'\)(\s*\(size 0\.65 )1\.2\)',
                   lambda m: m.group(1) + y1 + ")" + m.group(2) + "1.175)", s)
    assert n == 1, num
# the exposed pads' thermal vias join the inner planes solid (a relief ring blocks the heat path and pinches the GND
# plane between the GND and PD_DRAIN via rows)
s, n = re.subn(r'(\(drill 0\.2\)\s*\(property pad_prop_heatsink\))', r'\1\n\t\t(zone_connect 2)', s)
assert n == 8, n
s = with_model(s, name)                                          # KiCad 10 ships no REF0038A model
with open(os.path.join(LIB, name + ".kicad_mod"), "w", newline="\n") as fh:
    fh.write(s)
print("wrote", name)

# ---------------------------------------------------------------------------
# 10. TI RSM0032A VQFN-32 4 x 4 mm, 0.4 mm pitch (BQ40Z50-R2). bq40z50-r2.pdf, RSM0032A package outline
#     (4219107/A): thermal pad 1.4 +/-0.05 ("2X 2.8" on the outline is the lead span, 7 x 0.4). Example board
#     layout: 32X (0.6) x (0.2) lands on a (3.8) span, thermal land (1.4), NSMD 0.05 mask. Example stencil:
#     one (1.3) aperture on the thermal pad, "86 % printed solder coverage" (1.3^2 / 1.4^2). KiCad's generic
#     VQFN-32 4x4 has a 2.8 mm pad, which leaves 0.2 mm to the leads and floods the part with paste.
#     Pins 1-8 down the left side (pin 1 top), 9-16 along the bottom, 17-24 up the right, 25-32 along the top.
fp = FP("TI_RSM0032A_VQFN-32_4x4mm_P0.4mm_EP1.4x1.4mm",
        "TI RSM0032A VQFN-32 4 x 4 mm, 0.4 mm pitch, 1.4 mm thermal pad (BQ40Z50-R2); TI example land pattern and stencil",
        "VQFN-32 RSM0032A BQ40Z50")
for i in range(8):
    o = -1.4 + 0.4 * i
    fp.smd(str(1 + i), -1.9, o, 0.6, 0.2, shape="roundrect")
    fp.smd(str(9 + i), o, 1.9, 0.2, 0.6, shape="roundrect")
    fp.smd(str(17 + i), 1.9, -o, 0.6, 0.2, shape="roundrect")
    fp.smd(str(25 + i), -o, -1.9, 0.2, 0.6, shape="roundrect")
fp.smd("33", 0, 0, 1.4, 1.4, layers=("F.Cu", "F.Mask"))
fp.paste(0, 0, 1.3, 1.3)
fp.rect(-2.0, -2.0, 2.0, 2.0, "F.Fab", 0.1)
fp.line(-2.0, -1.5, -1.5, -2.0, "F.Fab", 0.1)
for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
    fp.line(sx * 2.11, sy * 1.71, sx * 2.11, sy * 2.11, "F.SilkS")
    fp.line(sx * 1.71, sy * 2.11, sx * 2.11, sy * 2.11, "F.SilkS")
fp.circle(-2.55, -1.4, 0.1, "F.SilkS", 0.2)
crt(fp, -2.45, -2.45, 2.45, 2.45)
fp.write(-3.2, 3.2)

# ---------------------------------------------------------------------------
# 11. SMT test point, Harwin S2761-46R and the JLC-stocked equivalent ronghe RH-S2761-46R (C55121754): a formed
#     loop 1.60 x 0.80 x 1.15 mm that Harwin states "conforms to 1608 Metric (0603 Imperial) package/footprint
#     size", soldered at both ends. Land pattern = KiCad's R_0603_1608Metric (0.8 x 0.95 pads at +/-0.825). Both
#     pads are pin 1 and marked as jumpered (the loop joins them), so the ratsnest asks for no copper between them.
fp = FP("TestPoint_Harwin_S2761_0603",
        "SMT test point loop, Harwin S2761-46R / ronghe RH-S2761-46R (LCSC C55121754), 1608 metric land pattern",
        "test point loop SMT S2761 0603")
fp.extra.append("(duplicate_pad_numbers_are_jumpers yes)")
fp.smd("1", -0.825, 0, 0.8, 0.95, shape="roundrect")
fp.smd("1", 0.825, 0, 0.8, 0.95, shape="roundrect")
fp.rect(-0.8, -0.4, 0.8, 0.4, "F.Fab", 0.1)
fp.line(-0.237, -0.735, 0.237, -0.735, "F.SilkS")
fp.line(-0.237, 0.735, 0.237, 0.735, "F.SilkS")
crt(fp, -1.48, -0.73, 1.48, 0.73)
fp.write(-1.5, 1.5)

# ---------------------------------------------------------------------------
# 12. Samtec FTSH-105-01-x-DV-K, 2 x 5 1.27 mm SMT header with keying shroud (J301 SWD). Samtec "RECOMMENDED PCB
#     LAYOUT FOR FTSH-1XX-XX-XXX-DV-XXX" (rev G): pads .029 x .110 (0.74 x 2.79) on .050 (1.27) pitch, .270 (6.86)
#     over the outer pad ends, so pad centres at +/-2.035 and a 1.28 mm gap between rows. Pin 1 top left, odd pins left,
#     even pins right (same numbering as KiCad's generic PinHeader_2x05_P1.27mm_Vertical_SMD). Shroud outline taken as
#     5.08 x 9.65 (.200 wide, positions x 1.27 + 3.30); courtyard covers pads and shroud.
fp = FP("Samtec_FTSH-105-01-xx-DV-K_2x05_P1.27mm",
        "Samtec FTSH-105-01-x-DV-K 2x05 1.27 mm SMT header with keying shroud; Samtec recommended PCB layout (rev G)",
        "Samtec FTSH SWD Cortex debug 2x05 1.27mm keyed")
for i in range(5):
    y = -2.54 + 1.27 * i
    fp.smd(str(2 * i + 1), -2.035, y, 2.79, 0.74)
    fp.smd(str(2 * i + 2), 2.035, y, 2.79, 0.74)
fp.rect(-2.54, -4.825, 2.54, 4.825, "F.Fab", 0.1)
fp.line(-2.54, -3.6, -1.6, -4.825, "F.Fab", 0.1)
fp.line(-3.6, -5.0, 3.6, -5.0, "F.SilkS")
fp.line(-3.6, 5.0, 3.6, 5.0, "F.SilkS")
fp.circle(-3.9, -3.3, 0.15, "F.SilkS", 0.3)
crt(fp, -3.7, -5.1, 3.7, 5.1)
fp.write(-6.2, 6.2)

# ---------------------------------------------------------------------------
# 13. TLC Electronic WSFB three-terminal battery protector (F102, WSFB1514, LCSC C42463217). Datasheet "WSFB Series"
#     rev A/2 p.3 "Board and Solder Layout Recommend": heater pad (3) C1 1.20 x D2 1.60 on the left, its left edge
#     C2 1.55 from the fuse pads; fuse pads (1 top, 2 bottom) C3 2.40 x D3/D5 1.55 with a D4 0.90 gap; heater pad top
#     D1 1.20 below the top fuse pad's top edge (same land pattern as the Littelfuse ITV4030). Body 4.0 x 3.0 x 1.0 max,
#     heater side on the left. Origin = centre of the land pattern (3.95 x 4.0).
fp = FP("TLC_WSFB_4x3mm",
        "TLC Electronic WSFB 3-terminal battery protector (fuse 1-2, heater 3), datasheet recommended land pattern",
        "SCP self control fuse chemical fuse battery WSFB")
fp.smd("3", -1.375, 0, 1.2, 1.6)
fp.smd("1", 0.775, -1.225, 2.4, 1.55)
fp.smd("2", 0.775, 1.225, 2.4, 1.55)
fp.rect(-2.0, -1.5, 2.0, 1.5, "F.Fab", 0.1)
fp.line(-2.15, -1.6, -2.15, -0.95, "F.SilkS")
fp.line(-2.15, 0.95, -2.15, 1.6, "F.SilkS")
fp.circle(2.35, -2.2, 0.1, "F.SilkS", 0.2)                  # pin 1 (top fuse pad, cell side)
crt(fp, -2.25, -2.25, 2.25, 2.25)
fp.write(-3.0, 3.0)

# ---------------------------------------------------------------------------
# 14. TI YFF0009 DSBGA-9 (U405/U505, TPD2S300YFFR). Datasheet SLVSDL1 pp. 34-36 (4219552/A): 3 x 3 balls on a
#     0.4 mm pitch, body 1.33-1.39 mm square, 0.625 mm max height. Land pattern: 0.23 mm round NSMD copper with a
#     0.05 mm mask expansion; stencil 0.25 mm square, 0.1 mm thick. Ball A1 top left in the top view, rows A-C down,
#     columns 1-3 to the right. Origin = array centre.
fp = FP("TI_YFF0009_DSBGA-9_P0.4mm", "TI YFF0009 DSBGA-9, 0.4 mm pitch, 1.36 mm body (TPD2S300YFF)",
        "DSBGA WCSP YFF 9 0.4mm TPD2S300")
#     Escape: the centre ball B2 (GND) is boxed in by the other eight (0.17 mm between ball edges: no trace or via fits
#     between them, even at JLC's 0.09 mm minimum), so it drops through a via-in-pad to the In1 GND plane: 0.15 mm
#     drill in a 0.25 mm pad (JLC's minimum via; 5:1 aspect ratio on the 0.8 mm board), 0.16 mm from the neighbours.
#     Order the board with via-in-pad filled and capped (JLC POFV, extra cost on 4 layers) so solder can't wick away.
#     The eight outer balls escape outward on F.Cu.
for r, row in enumerate("ABC"):
    for c in range(3):
        x, y = (c - 1) * 0.4, (r - 1) * 0.4
        if row + str(c + 1) == "B2":
            fp.items.append(f'(pad "B2" thru_hole circle (at {f(x)} {f(y)}) (size 0.25 0.25) (drill 0.15) '
                            f'(layers "*.Cu" "F.Mask") (remove_unused_layers no) (solder_mask_margin 0.04))')
        else:
            fp.smd(f"{row}{c + 1}", x, y, 0.23, 0.23, layers=("F.Cu", "F.Mask"), shape="circle",
                   extra=" (solder_mask_margin 0.05)")
        fp.paste(x, y, 0.25, 0.25)
fp.rect(-0.68, -0.68, 0.68, 0.68, "F.Fab", 0.1)
fp.line(-0.68, -0.38, -0.38, -0.68, "F.Fab", 0.1)
for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
    fp.line(sx * 0.8, sy * 0.5, sx * 0.8, sy * 0.8, "F.SilkS")
    fp.line(sx * 0.5, sy * 0.8, sx * 0.8, sy * 0.8, "F.SilkS")
fp.circle(-1.0, -1.0, 0.08, "F.SilkS", 0.16)                # ball A1
crt(fp, -0.95, -0.95, 0.95, 0.95)
fp.write(-1.6, 1.6)

# ---------------------------------------------------------------------------
# 15. Coilank APS0530 molded power inductor (L402/L502, APS0530M3R3H, LCSC C49073587; cost-down 2026-10-14).
#     Datasheet "APSW-H Series" p.1: body A 5.2 +/- 0.3 x B 6.0 max x C 3.0 max, terminals at the B ends.
#     Recommended pattern: F 6.0 overall, G 2.5 pad width, H 2.2 gap, so each pad is 1.9 x 2.5 at x = +/-2.05.
fp = FP("L_Coilank_APS0530", "Inductor, Coilank APS0530, 6.0x5.2x3.0mm, datasheet recommended land pattern",
        "inductor molded APS0530")
fp.smd("1", -2.05, 0, 1.9, 2.5)
fp.smd("2", 2.05, 0, 1.9, 2.5)
fp.rect(-3.0, -2.6, 3.0, 2.6, "F.Fab", 0.1)
fp.line(-1.0, -2.75, 1.0, -2.75, "F.SilkS")
fp.line(-1.0, 2.75, 1.0, 2.75, "F.SilkS")
crt(fp, -3.25, -2.85, 3.25, 2.85)
fp.write(-3.6, 3.6)
