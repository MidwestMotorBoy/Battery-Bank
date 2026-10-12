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
fp = FP("BatteryHolder_MYOUNG_BH-21700-B1BJ001", "MYOUNG BH-21700-B1BJ001 SMT single 21700 holder, pad 1 = +",
        "21700 battery holder SMT")
for num, x in (("1", -43.05), ("2", 43.05)):
    fp.smd(num, x, 0, 7.5, 9.0)
fp.npth(-34.0, 8.5, 4.0)
fp.npth(34.0, -8.5, 4.0)
fp.rect(-41.25, -12.5, 41.25, 12.5, "F.Fab", 0.1)
fp.circle(0, 0, 10.5, "F.Fab", 0.1)
fp.line(-41.4, -12.65, 41.4, -12.65, "F.SilkS")
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
#    (drawn on Edge.Cuts here). Signal pads 1.0 long, centred 6.15 from the edge.
fp = FP("USB_C_Receptacle_ShouHan_TYPE-C_16PCB0.8_IP68",
        "Shou Han TYPE-C 16PCB0.8 IP68 USB 2.0 receptacle, mid-mount in a 10.2 x 5.65 board-edge cutout, origin = board edge",
        "USB C Type-C receptacle USB2.0 16P mid-mount")
yp = -6.15
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
        "net tie bridge high current")
fp.extra.append('(net_tie_pad_groups "1,2")')
fp.smd("1", -2.0, 0, 3.0, 3.0, layers=("F.Cu", "F.Mask"))
fp.smd("2", 2.0, 0, 3.0, 3.0, layers=("F.Cu", "F.Mask"))
fp.poly([(-2.0, -1.5), (2.0, -1.5), (2.0, 1.5), (-2.0, 1.5)], "F.Cu")
crt(fp, -3.75, -1.75, 3.75, 1.75)
fp.write(-2.5, 2.5)

# ---------------------------------------------------------------------------
# 7. TI RRV0036A VQFN-36 5 x 6 mm (BQ25756). From Antmicro's open hardware library (Apache-2.0, via
#    partreel.com); checked against bq25756.pdf p.81 land pattern: pads 0.25 x 0.6 at (+/-2.4, +/-2.9),
#    EP 3.6 x 4.6, pin 1 top of the left column. Thermal vias are added in layout.
src = os.path.join(HERE, "third_party", "antmicro_bq25756errvr.kicad_mod")
dst = os.path.join(LIB, "TI_VQFN-36-1EP_RRV0036A_5x6mm_P0.5mm.kicad_mod")
s = open(src, encoding="utf-8").read()
s = re.sub(r'\(footprint "[^"]+"', '(footprint "TI_VQFN-36-1EP_RRV0036A_5x6mm_P0.5mm"', s, count=1)
s = re.sub(r'(\(property "Value" )"[^"]+"', r'\1"TI_VQFN-36-1EP_RRV0036A_5x6mm_P0.5mm"', s, count=1)
with open(dst, "w", newline="\n") as fh:
    fh.write(s)
print("wrote", os.path.basename(dst)[:-10])
