"""3D models for the production board's parts that KiCad doesn't ship (2026-10-22).

Writes STEP files into Production/3dmodels/ with step_mesh.py (pure Python) and attaches them:
  * from LCSC's EasyEDA library (OBJ meshes in 3dmodels/source/, fetched 2026-10-22; EasyEDA's STEP endpoint is gone):
      - Vishay_PowerPAIR_3x3S.step   SiZ240DT, LCSC C3289403 (EasyEDA 'POWERPAIR-8_L3.0-W3.0-P0.65-BL-EP')
      - Texas_RUK0020B_WQFN-20-1EP_3x3mm_P0.4mm.step   TPD6S300, LCSC C2649810 ('WQFN-20_L3.0-W3.0-H0.8-P0.40-TL-EP1.7')
    Both meshes are turned -90 deg about Z: in EasyEDA's frame the PowerPAIR paddles stack along Y and the WQFN pin-1
    dot sits bottom-left; here they match the footprints (paddles along X, larger one on +X; pin 1 top-left).
  * stand-ins (no model from TI, Coilank or LCSC; envelope only, from the datasheets):
      - TI_MHA0024A_CC2340R5MODA_7x10mm.step  CC2340R5MODA, SWRS349A MHA0024A: 7 x 10 mm substrate, 6.5 x 6.3 mm
        shield, 2.3 mm max; the antenna end (footprint y -5 .. -1.8) is bare substrate with a gold meander.
      - L_Coilank_APS0730.step  APS0730M2R2F, datasheets/aps0730.pdf: 7.6 x 7.8 x 3.1 mm molded body, end terminals.
      - SolderWire-0.15sqmm_1x02_P4mm_standin.step / SolderWire-0.5sqmm_1x01_standin.step: insulated wire stubs for
        the NTC and learning-cycle load wire pads (KiCad has no Connector_Wire models).
  * copied from DevBoard/3dmodels/ (made by DevBoard/tools/make_3d_*.py): the M24512 UFDFPN-8, the TLC WSFB fuse and
    the ShouHan USB-C 1.6 mm.
No model on purpose: test pads, tail slots, peg holes, Tag-Connect footprints (nothing is fitted there).

Run (any Python 3):  python Production/tools/make_3d_models.py            -> writes the STEP files
                     python Production/tools/make_3d_models.py --board  -> also sets the model paths on the board's
                                                                           footprints (as text; board closed in KiCad)
make_production.py calls attach_library() so the generated MonolithDev footprints carry the same models.
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.normpath(os.path.join(HERE, ".."))
DEV = os.path.normpath(os.path.join(PROD, "..", "DevBoard"))
OUT = os.path.join(PROD, "3dmodels")
SRC = os.path.join(OUT, "source")
sys.path.insert(0, HERE)
from step_mesh import Mesh, read_obj, write_step  # noqa: E402

P = "${KIPRJMOD}/3dmodels/"
STOCK = "${KICAD10_3DMODEL_DIR}/"
# footprint lib id -> model path. MonolithDev ones also go into the .kicad_mod files (attach_library).
MODELS = {
    "MonolithDev:Vishay_PowerPAIR_3x3S": P + "Vishay_PowerPAIR_3x3S.step",
    "MonolithDev:TI_RUK0020B_WQFN-20-1EP_3x3mm_P0.4mm_EP1.7x1.7mm_Via0.3": P + "Texas_RUK0020B_WQFN-20-1EP_3x3mm_P0.4mm.step",
    "MonolithDev:TI_MHA0024A_CC2340R5MODA_7x10mm": P + "TI_MHA0024A_CC2340R5MODA_7x10mm.step",
    "MonolithDev:L_Coilank_APS0730": P + "L_Coilank_APS0730.step",
    "MonolithDev:ST_UFDFPN-8-1EP_2x3mm_P0.5mm_EP1.2x1.4mm": P + "ST_UFDFPN-8-1EP_2x3mm_P0.5mm.step",
    "MonolithDev:TLC_WSFB_4x3mm": P + "TLC_WSFB_4x3mm.step",
    "MonolithDev:USB_C_Receptacle_ShouHan_TYPE-C_16PCB1.6_IP68": P + "USB_C_Receptacle_ShouHan_TYPE-C_16PCB1.6_IP68.step",
    # stock footprints whose stock model name doesn't exist in KiCad 10's library (board only)
    "Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm":
        STOCK + "Package_SON.3dshapes/WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm.step",
    "Connector_Wire:SolderWire-0.15sqmm_1x02_P4mm_D0.5mm_OD1.5mm": P + "SolderWire-0.15sqmm_1x02_P4mm_standin.step",
    "Connector_Wire:SolderWire-0.5sqmm_1x01_D0.9mm_OD2.1mm": P + "SolderWire-0.5sqmm_1x01_standin.step",
}
FROM_DEV = ["ST_UFDFPN-8-1EP_2x3mm_P0.5mm.step", "TLC_WSFB_4x3mm.step", "USB_C_Receptacle_ShouHan_TYPE-C_16PCB1.6_IP68.step"]

GOLD, SILVER, TIN, WHITE = (0.83, 0.67, 0.13), (0.78, 0.78, 0.8), (0.85, 0.85, 0.85), (0.95, 0.95, 0.95)
SUBSTRATE, MOLD, BLACK = (0.13, 0.32, 0.2), (0.22, 0.22, 0.24), (0.08, 0.08, 0.08)


def cc2340r5moda():
    m = Mesh()
    t = 0.9                                         # substrate (the 2.3 mm max height is substrate + shield)
    m.box(SUBSTRATE, -3.5, 3.5, -5.0, 5.0, 0.0, t)
    m.box(SILVER, -3.25, 3.25, -4.75, 1.55, t, 2.2)  # 6.5 x 6.3 shield over the radio, clear of the antenna end
    for i in range(9):                               # castellated pads 1-9 / 16-24 on the long sides, 1.0 mm pitch
        y = 4.4 - i
        m.box(GOLD, -3.5, -3.3, y - 0.3, y + 0.3, 0.0, t)
        m.box(GOLD, 3.3, 3.5, y - 0.3, y + 0.3, 0.0, t)
    for i in range(6):                               # pads 10-15 along the end opposite the antenna
        x = -2.5 + i
        m.box(GOLD, x - 0.3, x + 0.3, -5.0, -4.8, 0.0, t)
    zt = (t, t + 0.03)                               # printed antenna: a meander across the bare end
    for k, y in enumerate((2.2, 2.8, 3.4, 4.0, 4.6)):
        m.box(GOLD, -2.6, 2.6, y - 0.12, y + 0.12, *zt)
        x = 2.6 if k % 2 == 0 else -2.6
        if k < 4:
            m.box(GOLD, x - 0.12, x + 0.12, y, y + 0.6, *zt)
    m.cylinder(WHITE, -2.9, 4.55, 0.15, t, t + 0.02, 12)   # pin-1 mark (pad 1 is at footprint (-3.25, -4.4))
    return m


def aps0730():
    m = Mesh()
    m.box(MOLD, -3.8, 3.8, -3.9, 3.9, 0.12, 3.1)
    for s in (-1, 1):                                # bottom terminals over the pads (x +-2.55, 2.3 x 7.2), up the ends
        m.box(SILVER, s * 1.45, s * 3.85, -3.6, 3.6, 0.0, 0.12)
        m.box(SILVER, s * 3.8, s * 3.85, -3.6, 3.6, 0.12, 1.2)
    return m


def wire(pitch, n, od, cond):
    m = Mesh()
    for k in range(n):
        x = k * pitch
        m.cylinder(BLACK, x, 0, od / 2, 0.0, 6.0, 16)
        m.cylinder(TIN, x, 0, cond / 2, 6.0, 6.6, 12)
    return m


def easyeda(src):
    m = Mesh()
    m.merge(read_obj(os.path.join(SRC, src)), rot_z=-90)
    return m


BUILD = {
    "Vishay_PowerPAIR_3x3S.step": lambda: easyeda("POWERPAIR-8_L3.0-W3.0-P0.65-BL-EP_C3289403_easyeda.obj"),
    "Texas_RUK0020B_WQFN-20-1EP_3x3mm_P0.4mm.step": lambda: easyeda("WQFN-20_L3.0-W3.0-H0.8-P0.40-TL-EP1.7_C2649810_easyeda.obj"),
    "TI_MHA0024A_CC2340R5MODA_7x10mm.step": cc2340r5moda,
    "L_Coilank_APS0730.step": aps0730,
    "SolderWire-0.15sqmm_1x02_P4mm_standin.step": lambda: wire(4.0, 2, 1.5, 0.5),
    "SolderWire-0.5sqmm_1x01_standin.step": lambda: wire(0.0, 1, 2.1, 0.9),
}


def model_block(path, indent):
    t = indent
    return ('%s(model "%s"\n%s\t(offset\n%s\t\t(xyz 0 0 0)\n%s\t)\n%s\t(scale\n%s\t\t(xyz 1 1 1)\n%s\t)\n'
            '%s\t(rotate\n%s\t\t(xyz 0 0 0)\n%s\t)\n%s)' % ((t, path) + (t,) * 10))


def _end(s, i):
    d = 0
    while True:
        c = s[i]
        if c == '"':
            i += 1
            while s[i] != '"':
                i += 2 if s[i] == "\\" else 1
        elif c == "(":
            d += 1
        elif c == ")":
            d -= 1
            if d == 0:
                return i + 1
        i += 1


def set_model(blk, path, indent):
    """Replace every (model ...) at this indent in a footprint block with one model, or add it before the end."""
    spans = [(m.start(), _end(blk, m.start() + len(indent) + 1)) for m in re.finditer(r"\n%s\(model " % indent, blk)]
    for a, b in reversed(spans):
        blk = blk[:a] + blk[b:]
    i = blk.rstrip().rfind(")")
    return blk[:i].rstrip() + "\n" + model_block(path, indent) + "\n" + indent[:-1] + blk[i:]


def attach_library(pretty):
    """Set the model on each MonolithDev footprint in MODELS (called by make_production.py)."""
    for lib, path in MODELS.items():
        nick, name = lib.split(":", 1)
        f = os.path.join(pretty, name + ".kicad_mod")
        if nick != "MonolithDev" or not os.path.exists(f):
            continue
        s = open(f, encoding="utf-8").read()
        s = set_model(s.rstrip() + "\n", path, "\t")
        open(f, "w", encoding="utf-8", newline="\n").write(s)


def attach_board(pcb):
    """Set the model paths on the board's footprint instances (text edit, so KiCad 10's python isn't involved)."""
    lock = os.path.join(os.path.dirname(pcb), "~" + os.path.basename(pcb) + ".lck")
    if os.path.exists(lock):
        sys.exit("%s is open in KiCad: save and close the PCB editor first" % pcb)
    s = open(pcb, encoding="utf-8").read()
    reps, count = [], {}
    for m in re.finditer(r'\n\t\(footprint "([^"]+)"', s):
        if m.group(1) in MODELS:
            a = m.start() + 1
            b = _end(s, a)
            reps.append((a, b, set_model(s[a:b], MODELS[m.group(1)], "\t\t")))
            count[m.group(1)] = count.get(m.group(1), 0) + 1
    for a, b, t in reversed(reps):
        s = s[:a] + t + s[b:]
    open(pcb, "w", encoding="utf-8", newline="\n").write(s)
    for k, n in sorted(count.items()):
        print("%-75s x%d" % (k, n))


def main():
    os.makedirs(OUT, exist_ok=True)
    for name in FROM_DEV:
        shutil.copy2(os.path.join(DEV, "3dmodels", name), os.path.join(OUT, name))
        print("copied   %s" % name)
    for name, build in BUILD.items():
        n = write_step(os.path.join(OUT, name), name[:-5], build())
        print("wrote    %-50s %5d faces" % (name, n))
    if "--board" in sys.argv:
        attach_board(os.path.join(PROD, "Monolith.kicad_pcb"))


if __name__ == "__main__":
    main()
