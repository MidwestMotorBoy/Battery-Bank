"""Build the production schematic from the dev board schematic (re-runnable).

Copies the DevBoard schematic sheets, symbol/footprint libraries and project file into Production/ as the
'Monolith' project, then strips everything the production board doesn't carry (decided 2026-10-17):

  * removes dev-only parts by reference and prunes the wires, labels, junctions, no-connects and power
    symbols left dangling;
  * replaces 0 ohm links and jumpers with a wire between their two pins;
  * cell holders -> wire pads to the welded pack (16 AWG pack +/-, small pads for the taps), NTC headers ->
    2-pad wire footprints, EV2400 header -> three gauge pogo pads, SWD header J301 -> Tag-Connect TC2030-NL;
  * keeps a few dev test points as factory test pads (PACK_P, GND, 3V3, VBUS per port).

Run from the repo root or anywhere:  "C:/Program Files/KiCad/10.0/bin/python.exe" Production/tools/make_production.py
Then check:                          ... Production/tools/check_netlist.py
"""
import os
import re
import shutil
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schlib import anchors, new_uuids, on_segment, sheet_pins, symbols, top_blocks, wires  # noqa: E402
import siz240dt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.normpath(os.path.join(HERE, ".."))
DEV = os.path.normpath(os.path.join(PROD, "..", "DevBoard"))
KICAD_SYM = r"C:\Program Files\KiCad\10.0\share\kicad\symbols\Connector.kicad_sym"

SHEETS = ["gauge.kicad_sch", "power.kicad_sch", "mcu.kicad_sch", "usb_port.kicad_sch"]
ROOT_DEV, ROOT = "MonolithDev.kicad_sch", "Monolith.kicad_sch"

# ------------------------------------------------------------------ what goes
REMOVE = {
    "gauge.kicad_sch": [
        "BT101", "BT102", "BT103", "BT104",          # cell holders -> wire pads (added below)
        "J103",                                      # EV2400 header -> pogo pads (added below)
        "J104", "D104", "D105",                      # bench PACK_P supply
        "R127",                                      # DNP fuse bypass
        "R114",                                      # DNP BTP pull-up
        "SW101", "R118",                             # gauge wake button
        "C109", "D102",                              # DNP Q102 options
        "TP101", "TP102", "TP103", "TP104", "TP105", "TP107", "TP108",
    ],
    "power.kicad_sch": [
        "U201", "U202", "U203", "JP201", "JP202",    # sleep-current amps and their supply
        "R202", "R203", "R204", "R205", "R206", "R208",
        "C201", "C202", "C203", "C204", "C205",
        "TP201", "TP202", "TP203", "TP204", "TP205", "TP206", "TP207", "TP208", "TP209",
        "#FLG201",                                   # PACK_LP flag (net is PACK_P now)
    ],
    "mcu.kicad_sch": [
        "J301",                                      # 10-pin SWD -> TC2030-NL (added below)
        "J302", "R322", "R323",                      # UART header
        "J303", "R317", "R318", "R319", "R324",      # spare-GPIO header
        "SW301",                                     # reset button
        "D301", "R306", "R307",                      # status LED
        "R315",                                      # DNP pull-up
        "TP302", "TP303", "TP304", "TP307", "TP308", "TP309",
        "#FLG302",                                   # 3V3_MCU flag (net is 3V3 now)
    ],
    "usb_port.kicad_sch": [
        "J402",                                      # I2Cc logic-analyser header
        "R450", "C454", "R451", "C455",              # DNP snubbers
        "C447",                                      # DNP feed-forward cap
        "C435",                                      # battery-side bank 3 -> 2 x 22u (cap sims 2026-10-17, B2)
        "Q403", "Q404", "Q405", "Q406",              # liquid detection removed (2026-10-17): SBU pull FETs
        "R436", "R437", "R438", "R439",              # ... SBU sense resistors
        "R442", "R443",                              # ... FET gate holds
        "C432",                                      # per-port hybrid -> one shared PACK_P hybrid C208 (pack_bus_sims A2)
        "C445",                                      # buck input 2 -> 1 x 10u 50V on the shared bus (pack_bus_sims A2)
        "D406", "D407", "D408", "D409",              # gate turn-off diodes: gates driven directly
        "#FLG404", "#FLG406",                        # 3V3_PD / 5V_IN flags (nets are 3V3 / PACK_P now)
    ] + ["TP4%02d" % n for n in range(2, 22)],
}
LINKS = {  # two-pin parts replaced by a wire
    ROOT: ["R1", "R2", "R3", "R4"],
    "power.kicad_sch": ["R201", "R207"],
    "mcu.kicad_sch": ["R301", "R312"],
    "usb_port.kicad_sch": ["R401", "R431", "R440", "R448", "R449", "R444", "R445", "R446", "R447"],
}
# labels renamed after a link joins two named nets (old -> new), per sheet
RENAME = {  # labels on nets a link joined: new label name, ("pwr", net) to put that power symbol there instead,
    #          or "" to delete a label left on a single pin (the pin then gets a no-connect)
    ROOT: {"P1_ADCIN1": "P1_LDO_3V3", "P1_ADCIN2": ("pwr", "GND"), "P2_ADCIN1": ("pwr", "GND"),
           "P2_ADCIN2": ("pwr", "GND")},
    "power.kicad_sch": {"PACK_LP": ("pwr", "PACK_P"), "3V3_BUCK": ("pwr", "3V3"), "LDO_IN": ""},
    "mcu.kicad_sch": {"3V3_MCU": ("pwr", "3V3"), "SMB_PU": ("pwr", "3V3"),
                      "UART_TX": "", "UART_RX": "", "LED_DRV": ""},
    "usb_port.kicad_sch": {"DP": "DPDN_DCP", "DN": "DPDN_DCP", "BTST1_C": "BTST1", "BTST2_C": "BTST2",
                           "HG1": "HIDRV1", "LG1": "LODRV1", "HG2": "HIDRV2", "LG2": "LODRV2",
                           "3V3_PD": ("pwr", "3V3"), "5V_IN": ("pwr", "PACK_P")},
}
NEW_PARTS = {"C208": {"1": ("TP106", "1"), "2": ("TP109", "1")}}  # check_netlist: pin -> a dev pin on the same net
# labels left on single pins after liquid detection went: per label name, what happens at each pin's owner.
# TPS25751 GPIO4-7 unused -> GND (datasheet pin table); TPD4S201 system-side SBU pins -> no-connect (grounding them
# would short a cable's SBU lines whenever the SBU switch is on).
PIN_ACTIONS = {"usb_port.kicad_sch": {
    "SBU1_SNS": {"U401": "GND", "U405": "NC"}, "SBU2_SNS": {"U401": "GND", "U405": "NC"},
    "LIQ_PU": {"U401": "GND"}, "LIQ_PD": {"U401": "GND"}}}
# check_netlist: pins that deliberately change net (port 1 refs; port 2 follows). "GND" or None (left unconnected)
NET_MOVES = {("U401", "26"): "GND", ("U401", "27"): "GND", ("U401", "36"): "GND", ("U401", "37"): "GND",
             ("U405", "15"): None, ("U405", "14"): None}
TC2030_AT = (297.18, 106.68)  # under the SWD heading on the MCU sheet (was the DEBUG HEADERS area)
EXTRA_NC = {ROOT: [(220, 124.46)]}  # port 2's LDO_3V3 sheet pin: only port 1's strap used it
PAD = "TestPoint:TestPoint_Pad_D1.5mm"
FOOTPRINT = {  # kept parts whose footprint changes
    "gauge.kicad_sch": {"TP106": PAD, "TP109": PAD,
                        "J102": "Connector_Wire:SolderWire-0.15sqmm_1x02_P4mm_D0.5mm_OD1.5mm",
                        "J105": "Connector_Wire:SolderWire-0.15sqmm_1x02_P4mm_D0.5mm_OD1.5mm",
                        "J106": "Connector_Wire:SolderWire-0.15sqmm_1x02_P4mm_D0.5mm_OD1.5mm",
                        "J107": "Connector_Wire:SolderWire-0.15sqmm_1x02_P4mm_D0.5mm_OD1.5mm"},
    "mcu.kicad_sch": {"TP301": PAD},
    "usb_port.kicad_sch": {"TP401": PAD},
}
VALUE = {
    "gauge.kicad_sch": {"J102": "Cell 1 NTC wires", "J105": "Cell 2 NTC wires",
                        "J106": "Cell 3 NTC wires", "J107": "Cell 4 NTC wires"},
}
SWAP = {  # parts changed in place: new lib_id and properties (pins land on the same points)
    "usb_port.kicad_sch": {
        "C443": ("Device:C", {
            "Value": "22u 25V", "Footprint": "Capacitor_SMD:C_1206_3216Metric", "LCSC": "C12891",
            "MPN": "CL31A226KAHNNNE",
            "Notes": "PP5V bulk, third 22 uF 1206 with C441/C442 (about 33 uF effective at 5.16 V; was a 100 uF polymer "
                     "on the dev board). Each port's PP5V is a dedicated supply, so USB PD cSrcBulk (10 uF min) applies, "
                     "not cSrcBulkShared (120 uF): docs/devboard/cap-reduction-sims-2026-10-17.md, P3"}),
    },
}


def P(fp, lcsc, mpn, value=None):
    """Footprint/part swap that keeps the symbol (production passive downsizing, 2026-10-17)."""
    props = {"Footprint": fp, "LCSC": lcsc, "MPN": mpn}
    if value:
        props["Value"] = value
    return (None, props)


R0201, R0402, C0201, C0402 = ("Resistor_SMD:R_0201_0603Metric", "Resistor_SMD:R_0402_1005Metric",
                              "Capacitor_SMD:C_0201_0603Metric", "Capacitor_SMD:C_0402_1005Metric")
SOD882 = P("Diode_SMD:D_SOD-882", "C549279", "BAT54L,315 (Nexperia)")
DOWNSIZE = {  # extended parts and 0201 allowed on production; 0201 only where both nets stay <= 5.5 V
    "gauge.kicad_sch": {
        **{r: P(R0402, "C25076", "0402WGF1000TCE") for r in ("R101", "R102", "R103", "R104")},  # no open holders
        "R110": P(R0402, "C26086", "0402WGJ0106TCE", "10M 5%"),
        "R112": P(R0402, "C26086", "0402WGJ0106TCE", "10M 5%"),
        "R117": P(R0402, "C25790", "0402WGF4703TCE"),
        "R115": P(R0201, "C270366", "0201WMF1000TEE"),
        "R116": P(R0201, "C270366", "0201WMF1000TEE"),
        "RS101": P("Resistor_SMD:R_1206_3216Metric", "C154629", "LR1206-21R001F4 (Ralec, 75 ppm)", "1m 1% 1W"),
        "D101": SOD882,
    },
    "mcu.kicad_sch": {
        **{c: P(C0201, "C307380", "CL03A104KO3NNNC", "0.1u 16V") for c in ("C302", "C303", "C304")},
        "R302": P(R0201, "C270364", "0201WMF1003TEE"),
        "R304": P(R0201, "C270350", "0201WMF3301TEE"),
        "R305": P(R0201, "C270350", "0201WMF3301TEE"),
        "R313": P(R0201, "C473458", "0201WMF2203TEE"),
        "R314": P(R0201, "C270345", "0201WMF4702TEE"),
    },
    "usb_port.kicad_sch": {
        "R402": P(R0201, "C270350", "0201WMF3301TEE"),
        "R403": P(R0201, "C270350", "0201WMF3301TEE"),
        "R404": P(R0201, "C473048", "0201WMF1002TEE"),
        "R410": P(R0402, "C25893", "0402WGF4022TCE"),
        "R412": P(R0201, "C423536", "0201WMF4022TEE"),
        "R413": P(R0402, "C25926", "0402WGF9101TCE"),
        "R414": P(R0402, "C25891", "0402WGF3601TCE"),
        "R415": P(R0402, "C25871", "0402WGF1801TCE"),
        "R416": P(R0402, "C25908", "0402WGF5601TCE"),
        "R417": P(R0201, "C270345", "0201WMF4702TEE"),
        "R420": P(R0402, "C25077", "0402WGF100JTCE"),
        **{r: P(R0201, "C473048", "0201WMF1002TEE") for r in ("R421", "R422", "R423")},
        "R424": P("Resistor_SMD:R_0805_2012Metric", "C728267", "PA0805FRE470R005L", "5m 0.5W (RAC)"),
        "R427": P("Resistor_SMD:R_1206_3216Metric", "C252653", "MA120610FR005MZ (50 ppm)", "5m 1W (RBAT)"),
        "R432": P(R0201, "C270364", "0201WMF1003TEE"),
        "R433": P(R0402, "C25750", "0402WGF1203TCE"),
        "R435": P(R0201, "C270365", "0201WMF1001TEE"),
        **{r: P(R0201, "C270364", "0201WMF1003TEE") for r in ("R441", "R442", "R443")},
        "C408": P(C0201, "C307380", "CL03A104KO3NNNC", "0.1u 16V"),
        "C410": P(C0402, "C23733", "CL05A475MP5NRNC", "4.7u 10V"),
        "C411": P(C0402, "C23733", "CL05A475MP5NRNC", "4.7u 10V"),
        "C414": P(C0402, "C92361", "CL05A474KA5NNNC"),
        "C417": P(C0402, "C92361", "CL05A474KA5NNNC"),
        "C439": P(C0402, "C7419416", "FCC0402B333K500AT"),
        "TH401": P(R0402, "C77131", "NCP15XH103F03RC"),
        # 0.8 mm board (stack-up 2026-10-17): the 0.8 mm version of the same IP68 connector, identical land pattern
        "J401": P("MonolithDev:USB_C_Receptacle_ShouHan_TYPE-C_16PCB0.8_IP68", "C55629727",
                  "TYPE-C 16PCB0.8 IP68 (Shou Han)", "TYPE-C 16PCB0.8 IP68"),
        # 10x10 -> 7.8x7.6x3.1 mm: 13.7 mOhm max, Irms 13 A (40 C rise), Isat 17 A at a 40 % drop. Worst case (20 V 5 A
        # reverse from a 10 V pack) ~10.7 A rms, ~12.4 A peak: ~1.6 W DCR loss, L near 1.7 uH at the peak (L/RSNS
        # 0.34 uH/mOhm, inside TI's 0.05-1.26 stability range). Measure inductor temperature on the dev board.
        "L401": P("MonolithDev:L_Coilank_APS0730", "C49261221", "APS0730M2R2F (Coilank)"),
    },
}
for _sheet, _parts in DOWNSIZE.items():
    SWAP.setdefault(_sheet, {}).update(_parts)
WIRE16 = "Connector_Wire:SolderWire-1.5sqmm_1x01_D1.7mm_OD3.9mm"   # 16 AWG pack leads
WIRE26 = "Connector_Wire:SolderWire-0.15sqmm_1x01_D0.5mm_OD1.5mm"  # cell tap leads
# new one-pin pads on the gauge sheet: (ref, value, footprint, (old ref, old pin) whose position it takes)
GAUGE_PADS = [
    ("J108", "PACK- (CELL_N)", WIRE16, ("BT101", "2")),
    ("J109", "CELL1 tap", WIRE26, ("BT101", "1")),
    ("J110", "CELL2 tap", WIRE26, ("BT102", "1")),
    ("J111", "CELL3 tap", WIRE26, ("BT103", "1")),
    ("J112", "PACK+ (CELL_P_RAW)", WIRE16, ("BT104", "1")),
    ("TP110", "SMBC", PAD, ("J103", "2")),
    ("TP111", "SMBD", PAD, ("J103", "3")),
    ("TP112", "GND", PAD, ("J103", "1")),
]
# the pogo pads get their own spaced row (J103's pins were 2.54 mm apart), tied by a global label or GND symbol
POGO_AT = {"TP110": ((355.6, 152.4), "SCL"), "TP111": ((370.84, 152.4), "SDA"), "TP112": ((386.08, 152.4), "GND")}


def uid():
    return str(uuid.uuid4())


def cut(s, spans):
    for a, b in sorted(set(spans), reverse=True):
        ls = s.rfind("\n", 0, a)
        s = s[:ls] + s[b:]
    return s


def insert_top(s, text):
    """Insert depth-1 items before the sheet's closing block (sheet_instances / embedded_fonts / end)."""
    for tail in ("\n\t(sheet_instances", "\n\t(embedded_fonts"):
        i = s.find(tail)
        if i >= 0:
            return s[:i] + text + s[i:]
    i = s.rstrip().rfind(")")
    return s[:i] + text.lstrip("\n") + "\n" + s[i:]


def wire_text(p, q):
    return ('\n\t(wire\n\t\t(pts\n\t\t\t(xy %g %g) (xy %g %g)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n'
            '\t\t)\n\t\t(uuid "%s")\n\t)' % (p[0], p[1], q[0], q[1], uid()))


def label_text(name, p, angle=0):
    just = "left bottom" if angle == 0 else "right bottom"
    return ('\n\t(label "%s"\n\t\t(at %g %g %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            '\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)' % (name, p[0], p[1], angle, just, uid()))


def nc_text(p):
    return '\n\t(no_connect\n\t\t(at %g %g)\n\t\t(uuid "%s")\n\t)' % (p[0], p[1], uid())


def set_prop(blk, prop, value):
    return re.sub(r'(\(property "%s" )"[^"]*"' % prop, lambda m: m.group(1) + '"%s"' % value, blk, count=1)


def clone(template, ref, value, footprint, at, old_ref):
    """Copy a placed symbol block to a new position/reference."""
    blk = new_uuids(template)
    x0, y0 = map(float, re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+)", blk).groups())
    dx, dy = at[0] - x0, at[1] - y0

    def shift(m):
        return "(at %g %g" % (round(float(m.group(1)) + dx, 2), round(float(m.group(2)) + dy, 2))
    blk = re.sub(r"\(at ([-\d.]+) ([-\d.]+)", shift, blk)
    blk = set_prop(blk, "Reference", ref)
    blk = set_prop(blk, "Value", value)
    blk = set_prop(blk, "Footprint", footprint)
    return blk.replace('(reference "%s")' % old_ref, '(reference "%s")' % ref)


def connection_state(s):
    syms = symbols(s)
    ws = wires(s)
    ends = {}
    for w in ws:
        for p in w["p"]:
            ends[p] = ends.get(p, 0) + 1
    labels = []
    for h in ("label", "global_label", "hierarchical_label"):
        labels += anchors(s, h)
    pins = {}
    for y in syms:
        for n, p in y["pins"].items():
            pins.setdefault(p, []).append(y)
    return syms, ws, ends, labels, pins


def split_wires(s):
    """Split wires at interior labels, T-joins and pins, so pruning a dangling end keeps what hangs mid-wire."""
    syms, ws, ends, labels, pins = connection_state(s)
    pts = set(ends) | {x["p"] for x in labels} | set(pins) | {x["p"] for x in anchors(s, "junction")}
    spans, add = [], ""
    for w in ws:
        mid = [p for p in pts if on_segment(p, w["p"])]
        if not mid:
            continue
        a = w["p"][0]
        mid.sort(key=lambda p: abs(p[0] - a[0]) + abs(p[1] - a[1]))
        chain = [a] + mid + [w["p"][1]]
        spans.append((w["a"], w["b"]))
        add += "".join(wire_text(p, q) for p, q in zip(chain, chain[1:]))
    return insert_top(cut(s, spans), add), len(spans)


def prune(s):
    """Remove wires/labels/junctions/no-connects/power symbols that no longer connect anything. Repeat to a fixpoint."""
    total = 0
    while True:
        syms, ws, ends, labels, pins = connection_state(s)
        sheet_pts = set(sheet_pins(s))
        lab_pts = {x["p"] for x in labels} | sheet_pts
        spans = []

        def through(p, skip=None):
            return any(on_segment(p, w["p"]) for w in ws if w is not skip)
        for w in ws:
            for p in w["p"]:
                if ends[p] > 1 or p in lab_pts or p in pins or through(p, w):
                    continue
                spans.append((w["a"], w["b"]))
                break
        for x in labels:
            p = x["p"]
            if p not in ends and p not in pins and p not in sheet_pts and not through(p):
                spans.append((x["a"], x["b"]))
        for y in syms:
            if not y["power"]:
                continue
            p = list(y["pins"].values())[0]
            if p not in ends and len(pins[p]) == 1 and p not in lab_pts and not through(p):
                spans.append((y["a"], y["b"]))
        for x in anchors(s, "junction"):
            p = x["p"]
            deg = ends.get(p, 0) + len(pins.get(p, [])) + 2 * sum(on_segment(p, w["p"]) for w in ws)
            if deg < 3:
                spans.append((x["a"], x["b"]))
        for x in anchors(s, "no_connect"):
            if x["p"] not in pins and x["p"] not in sheet_pts:
                spans.append((x["a"], x["b"]))
        if not spans:
            return s, total
        total += len(set(spans))
        s = cut(s, spans)


def attached(s):
    """Set of (ref, pin) attached to something."""
    syms, ws, ends, labels, pins = connection_state(s)
    lab_pts = {x["p"] for x in labels} | set(sheet_pins(s)) | {x["p"] for x in anchors(s, "no_connect")}
    out = set()
    for y in syms:
        for n, p in y["pins"].items():
            if p in ends or p in lab_pts or len(pins[p]) > 1 or any(on_segment(p, w["p"]) for w in ws):
                out.add((y["ref"], n))
    return out


def edit_symbols(s, sheet):
    out, last = [], 0
    for y in symbols(s):
        blk = s[y["a"]:y["b"]]
        if y["ref"] in FOOTPRINT.get(sheet, {}):
            blk = set_prop(blk, "Footprint", FOOTPRINT[sheet][y["ref"]])
        if y["ref"] in VALUE.get(sheet, {}):
            blk = set_prop(blk, "Value", VALUE[sheet][y["ref"]])
        if y["ref"] in SWAP.get(sheet, {}):
            lib, props = SWAP[sheet][y["ref"]]
            if lib:
                blk = re.sub(r'\(lib_id "[^"]+"\)', '(lib_id "%s")' % lib, blk, count=1)
            for k, v in props.items():
                assert '(property "%s" ' % k in blk, (y["ref"], k)
                blk = set_prop(blk, k, v)
        out += [s[last:y["a"]], blk]
        last = y["b"]
    out.append(s[last:])
    return "".join(out)


PWR_N = [9000]


def clone_power(src, at):
    """Copy a power symbol block to `at` (rotation 0) with fresh hidden #PWR references."""
    b = new_uuids(src)
    x0, y0 = map(float, re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+)", b).groups())
    b = re.sub(r"\(at ([-\d.]+) ([-\d.]+)",
               lambda m: "(at %g %g" % (round(float(m.group(1)) - x0 + at[0], 2), round(float(m.group(2)) - y0 + at[1], 2)), b)
    b = re.sub(r"\n\t\t\(at ([-\d.]+) ([-\d.]+) [-\d.]+\)", lambda m: "\n\t\t(at %s %s 0)" % m.groups(), b, count=1)

    def fresh(m):
        PWR_N[0] += 1
        return '%s"#PWR%04d"' % (m.group(1), PWR_N[0])
    return "\n\t" + re.sub(r'(\(property "Reference" |\(reference )"#PWR[^"]*"', fresh, b)


def power_template(s, value):
    for y in symbols(s):
        if y["power"] and '(property "Value" "%s"' % value in s[y["a"]:y["b"]]:
            return s[y["a"]:y["b"]]
    raise KeyError(value)


def swap_fets(s):
    """Each BQ25756 leg's two PGQ04N070 -> one SiZ240DT: high side becomes unit A, low side unit B (siz240dt.py)."""
    if '(symbol "%s"' % siz240dt.LIB_ID not in s:
        i = s.index("\n\t(lib_symbols") + len("\n\t(lib_symbols")
        s = s[:i] + "\n" + siz240dt.lib_symbol() + s[i:]
    syms = {y["ref"]: y for y in symbols(s)}
    reps = []
    for hs, ls in siz240dt.LEGS:
        for ref, unit in ((hs, 1), (ls, 2)):
            y = syms[ref]
            reps.append((y["a"], y["b"], siz240dt.convert(s[y["a"]:y["b"]], unit, hs)))
    for a, b, txt in sorted(reps, reverse=True):
        s = s[:a] + txt + s[b:]
    return s


def pin_actions(s, sheet, templates):
    """Apply PIN_ACTIONS to labels sitting directly on a pin: GND symbol in their place, or a no-connect flag."""
    acts = PIN_ACTIONS.get(sheet, {})
    if not acts:
        return s
    owner = {}
    for y in symbols(s):
        for p in y["pins"].values():
            owner.setdefault(p, y["ref"])
    spans, add, to_gnd = [], "", []
    for x in anchors(s, "label"):
        if x["name"] not in acts:
            continue
        what = acts[x["name"]].get(owner.get(x["p"]))
        assert what, (x["name"], x["p"], owner.get(x["p"]))
        spans.append((x["a"], x["b"]))
        if what == "GND":
            to_gnd.append(x["p"])
        else:
            add += nc_text(x["p"])
    if to_gnd:  # U401 GPIO4-7 sit in the rows above GPIO11, whose wire already runs left to GND: join that wire
        g11 = {y["ref"]: y for y in symbols(s)}["U401"]["pins"]["13"]
        corner = next(q for w in wires(s) if g11 in w["p"] for q in w["p"] if q != g11)
        assert corner[1] == g11[1] and all(p[0] == g11[0] for p in to_gnd), (corner, g11, to_gnd)
        for p in to_gnd:
            add += wire_text(p, (corner[0], p[1]))
        rail = sorted({(corner[0], p[1]) for p in to_gnd} | {corner}, key=lambda q: q[1])
        for a, b in zip(rail, rail[1:]):  # end-to-end segments, so every stub meets a wire end (no mid-wire T)
            add += wire_text(a, b)
        add += "".join('\n\t(junction\n\t\t(at %g %g)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "%s")\n\t)'
                       % (q[0], q[1], uid()) for q in rail[1:])
    return insert_top(cut(s, spans), add)


def rename_labels(s, sheet, templates):
    spans, adds = [], ""
    for x in anchors(s, "label"):
        if x["name"] in RENAME.get(sheet, {}):
            new = RENAME[sheet][x["name"]]
            spans.append((x["a"], x["b"]))
            if isinstance(new, tuple) and x["p"] in set(sheet_pins(s)):
                # sheet pins sit off the 1.27 mm grid: step out to the grid with a short wire
                q = (round(round((x["p"][0] + 2.54) / 1.27) * 1.27, 2), x["p"][1])
                adds += wire_text(x["p"], q) + clone_power(templates[new[1]], q)
            elif isinstance(new, tuple):
                adds += clone_power(templates[new[1]], x["p"])
            elif new:
                adds += "\n\t" + s[x["a"]:x["b"]].replace('(label "%s"' % x["name"], '(label "%s"' % new, 1)
    s = cut(s, spans)
    return insert_top(s, adds) if adds else s


def add_tc2030(s, old):
    """J301 (10-pin Cortex SWD) -> J301 Tag-Connect TC2030-NL, wired by labels and power symbols."""
    lib = open(KICAD_SYM, encoding="utf-8").read()
    m = re.search(r'\n\t\(symbol "Conn_ARM_SWD_TagConnect_TC2030"\n', lib)
    a = m.start() + 2
    from schlib import block_end
    sym = lib[a:block_end(lib, a)]
    sym = sym.replace('(symbol "Conn_ARM_SWD_TagConnect_TC2030"', '(symbol "Connector:Conn_ARM_SWD_TagConnect_TC2030"', 1)
    sym = "\n".join("\t" + ln for ln in sym.split("\n"))
    i = s.index("\n\t(lib_symbols") + len("\n\t(lib_symbols")
    s = s[:i] + "\n\t" + sym + s[i:]

    syms = {y["ref"]: y for y in symbols(s)}
    tmpl = s[syms["TP301"]["a"]:syms["TP301"]["b"]]          # any symbol on this sheet for the instance path
    blk = clone(tmpl, "J301", "TC2030-NL", "Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical", TC2030_AT, "TP301")
    blk = blk.replace('(lib_id "Connector:TestPoint")', '(lib_id "Connector:Conn_ARM_SWD_TagConnect_TC2030")')
    blk = set_prop(blk, "Description", "Tag-Connect TC2030-NL footprint (no part fitted); XDS110 via TC2030-CTX cable")
    blk = re.sub(r'\n\t\t\(pin "1"\n\t\t\t\(uuid "[^"]+"\)\n\t\t\)',
                 "".join('\n\t\t(pin "%d"\n\t\t\t(uuid "%s")\n\t\t)' % (n, uid()) for n in range(1, 7)), blk)
    s = insert_top(s, "\n\t" + blk)

    pins = {y["ref"]: y for y in symbols(s)}["J301"]["pins"]
    gnd = pins["5"]
    v33 = pins["1"]
    add = clone_power(power_template(s, "3V3"), v33) + clone_power(power_template(s, "GND"), gnd)
    add += label_text("SWDIO", pins["2"]) + label_text("NRST", pins["3"]) + label_text("SWCLK", pins["4"])
    add += nc_text(pins["6"])
    u = {y["ref"]: y for y in symbols(s)}["U301"]["pins"]
    add += label_text("SWDIO", u["20"], 180) + label_text("SWCLK", u["19"], 180)
    return insert_top(s, add)


def add_gauge_pads(s, old):
    syms = {y["ref"]: y for y in symbols(s)}
    tmpl = s[syms["TP106"]["a"]:syms["TP106"]["b"]]
    add = ""
    glabel = {}
    for a, b in top_blocks(s, "global_label"):
        m = re.match(r'\(global_label "([^"]+)"[\s\S]*?\(at [-\d.]+ [-\d.]+ 180\)', s[a:b])
        if m:
            glabel.setdefault(m.group(1), s[a:b])
    gnd = next(s[y["a"]:y["b"]] for y in symbols(s) if y["lib"] == "power:GND")
    for ref, value, fp, (oref, opin) in GAUGE_PADS:
        if ref not in POGO_AT:
            add += "\n\t" + clone(tmpl, ref, value, fp, old[oref]["pins"][opin], "TP106")
            continue
        at, net = POGO_AT[ref]
        add += "\n\t" + clone(tmpl, ref, value, fp, at, "TP106")
        if net == "GND":
            add += clone_power(gnd, at)
        else:
            b = new_uuids(glabel[net])
            x0, y0 = map(float, re.search(r"\(at ([-\d.]+) ([-\d.]+)", b).groups())
            b = re.sub(r"\(at ([-\d.]+) ([-\d.]+)", lambda m: "(at %g %g" % (
                round(float(m.group(1)) - x0 + at[0], 2), round(float(m.group(2)) - y0 + at[1], 2)), b)
            add += "\n\t" + b
    return insert_top(s, add)


SHARED_BULK_AT = (63.5, 133.35)  # power sheet, under the 3V3 rail


def add_shared_bulk(s):
    """One 100 uF hybrid on PACK_P for both chargers' battery sides and both TPS62933 inputs (pack_bus_sims.py A2).
    Cloned from the dev board's per-port C432 (usb_port sheet), which P0 removes."""
    from schlib import block_end
    dev = open(os.path.join(DEV, "usb_port.kicad_sch"), encoding="utf-8").read()
    if '(symbol "Device:C_Polarized"' not in s:
        a = dev.index('\n\t\t(symbol "Device:C_Polarized"') + 1
        lib = dev[a:block_end(dev, a + 2)]
        i = s.index("\n\t(lib_symbols") + len("\n\t(lib_symbols")
        s = s[:i] + "\n" + lib + s[i:]
    c432 = next(y for y in symbols(dev) if y["ref"] == "C432")
    blk = new_uuids(dev[c432["a"]:c432["b"]])
    x0, y0 = c432["at"][:2]
    at = SHARED_BULK_AT
    blk = re.sub(r"\(at ([-\d.]+) ([-\d.]+)", lambda m: "(at %g %g" % (
        round(float(m.group(1)) - x0 + at[0], 2), round(float(m.group(2)) - y0 + at[1], 2)), blk)
    blk = set_prop(blk, "Reference", "C208")
    for prop, dy in (("Reference", -1.27), ("Value", 1.27)):  # text right of the body, clear of the PACK_P symbol
        blk = re.sub(r'(\(property "%s" "[^"]*"\s*\(at )[-\d.]+ [-\d.]+ [-\d.]+\)' % prop,
                     lambda m: m.group(1) + "%g %g 0)" % (at[0] + 6.35, round(at[1] + dy, 2)), blk, count=1)
    blk = set_prop(blk, "Notes", "Shared PACK_P bulk for both chargers' battery sides and both TPS62933 inputs "
                   "(replaces the per-port C432/C532). Place it between the two power stages, on PACK_P beside the "
                   "RBAT pads: Production/tools/pack_bus_sims.py option A2")
    host = next(y for y in symbols(s) if y["ref"] == "C206")
    hb = s[host["a"]:host["b"]]
    ha = hb.index("\n\t\t(instances") + 3
    inst = hb[ha:block_end(hb, ha)].replace('(reference "C206")', '(reference "C208")')
    ba = blk.index("\n\t\t(instances") + 3
    blk = blk[:ba] + inst + blk[block_end(blk, ba):]
    s = insert_top(s, "\n\t" + blk)
    pins = {y["ref"]: y for y in symbols(s)}["C208"]["pins"]
    add = clone_power(power_template(s, "PACK_P"), pins["1"]) + clone_power(power_template(s, "GND"), pins["2"])
    head = next((a, b) for a, b in top_blocks(s, "text") if "3.3 V ALWAYS-ON RAIL" in s[a:b])
    t = new_uuids(s[head[0]:head[1]])
    t = re.sub(r'\(text "[^"]*"', '(text "PACK_P SHARED BULK  (both chargers + both 5 V buck inputs)"', t, count=1)
    t = re.sub(r"\(at [-\d.]+ [-\d.]+", "(at 40.64 116.84", t, count=1)
    add += "\n\t" + t
    return insert_top(s, add)


TITLE = {
    ROOT: "Monolith production board - top level",
    "gauge.kicad_sch": "Monolith production board - cells and gauge",
    "power.kicad_sch": "Monolith production board - 3V3 rail",
    "mcu.kicad_sch": "Monolith production board - MCU",
    "usb_port.kicad_sch": "Monolith production board - USB-C port",
}


def title_block(s, sheet):
    s = re.sub(r'\(title "[^"]*"\)', '(title "%s")' % TITLE[sheet], s, count=1)
    s = re.sub(r'\(date "[^"]*"\)', '(date "2026-10-17")', s, count=1)
    s = re.sub(r'\(rev "[^"]*"\)', '(rev "P0")', s, count=1)
    s = re.sub(r'\(company "[^"]*"\)', '(company "Monolith 100 W battery bank - production")', s, count=1)
    s = re.sub(r'\(comment 3 "[^"]*"\)', '(comment 3 "P0: dev board rev A8 stripped by Production/tools/make_production.py; not reviewed")', s, count=1)
    return s


def process(sheet, src):
    s = open(src, encoding="utf-8").read()
    s = s.replace('(project "MonolithDev"', '(project "Monolith"')
    s, _ = split_wires(s)
    before = attached(s)
    old = {y["ref"]: y for y in symbols(s)}
    drop = set(REMOVE.get(sheet, [])) | set(LINKS.get(sheet, []))
    missing = drop - set(old)
    assert not missing, (sheet, missing)
    templates = {}
    for y in old.values():
        if y["power"]:
            v = re.search(r'\(property "Value" "([^"]*)"', s[y["a"]:y["b"]]).group(1)
            templates.setdefault(v, s[y["a"]:y["b"]])
    spans, add = [], ""
    for ref in drop:
        spans.append((old[ref]["a"], old[ref]["b"]))
    if sheet != ROOT:  # root straps are joined by renaming their sheet-pin labels instead
        for ref in LINKS.get(sheet, []):
            p = old[ref]["pins"]
            assert len(p) == 2, ref
            add += wire_text(p["1"], p["2"])
    s = cut(s, spans)
    s = insert_top(s, add)
    if sheet == "gauge.kicad_sch":
        s = add_gauge_pads(s, old)
    s, n = prune(s)
    if sheet == "power.kicad_sch":
        s = add_shared_bulk(s)
    if sheet == "mcu.kicad_sch":  # after pruning, so its pins can't catch J301's old wires
        s = add_tc2030(s, old)
        s, n2 = prune(s)
        n += n2
    s = rename_labels(s, sheet, templates)
    s = pin_actions(s, sheet, templates)
    s, n2 = prune(s)
    n += n2
    s = insert_top(s, "".join(nc_text(p) for p in EXTRA_NC.get(sheet, [])))
    s = edit_symbols(s, sheet)
    if sheet == "usb_port.kicad_sch":
        s = swap_fets(s)
    s = title_block(s, sheet)
    # pins that were connected before and are now open get a no-connect flag
    now = attached(s)
    cur = {y["ref"]: y for y in symbols(s)}
    opened = sorted(rp for rp in before - now if rp[0] in cur and rp[0] not in drop and not cur[rp[0]]["power"])
    s = insert_top(s, "".join(nc_text(cur[r]["pins"][p]) for r, p in opened))
    open(os.path.join(PROD, sheet), "w", encoding="utf-8", newline="\n").write(s)
    print("%-20s removed %3d parts, %d links, pruned %3d items, new no-connects: %s"
          % (sheet, len(REMOVE.get(sheet, [])), len(LINKS.get(sheet, [])), n, ", ".join("%s.%s" % rp for rp in opened) or "-"))


APS0730 = """(footprint "L_Coilank_APS0730"
\t(version 20241229)
\t(generator "make_production.py")
\t(layer "F.Cu")
\t(descr "Inductor, Coilank APS0730 (APS-F series), 7.8x7.6x3.1mm, datasheet land pattern a 2.8 / b 7.4 / c 7.2 (datasheets/aps0730.pdf)")
\t(tags "inductor molded APS0730")
\t(property "Reference" "REF**" (at 0 -5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
\t(property "Value" "L_Coilank_APS0730" (at 0 5 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
\t(attr smd)
\t(pad "1" smd rect (at -2.55 0) (size 2.3 7.2) (layers "F.Cu" "F.Paste" "F.Mask"))
\t(pad "2" smd rect (at 2.55 0) (size 2.3 7.2) (layers "F.Cu" "F.Paste" "F.Mask"))
\t(fp_rect (start -3.8 -3.9) (end 3.8 3.9) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))
\t(fp_line (start -1.2 -4.02) (end 1.2 -4.02) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
\t(fp_line (start -1.2 4.02) (end 1.2 4.02) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
\t(fp_rect (start -4.05 -4.15) (end 4.05 4.15) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
\t(fp_text user "${REFERENCE}" (at 0 0 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
)
"""


def main():
    for f in ("MonolithDev.kicad_sym", "sym-lib-table", "fp-lib-table"):
        shutil.copy2(os.path.join(DEV, f), os.path.join(PROD, f))
    if os.path.isdir(os.path.join(PROD, "MonolithDev.pretty")):
        shutil.rmtree(os.path.join(PROD, "MonolithDev.pretty"))
    shutil.copytree(os.path.join(DEV, "MonolithDev.pretty"), os.path.join(PROD, "MonolithDev.pretty"))
    with open(os.path.join(PROD, "MonolithDev.pretty", "L_Coilank_APS0730.kicad_mod"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write(APS0730)
    with open(os.path.join(PROD, "MonolithDev.pretty", "Vishay_PowerPAIR_3x3S.kicad_mod"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write(siz240dt.footprint())
    lib = os.path.join(PROD, "MonolithDev.kicad_sym")
    t = open(lib, encoding="utf-8").read()
    if '(symbol "SiZ240DT"' not in t:
        t = t.rstrip()[:-1].rstrip() + "\n" + siz240dt.library_entry() + "\n)\n"
        open(lib, "w", encoding="utf-8", newline="\n").write(t)
    pro = open(os.path.join(DEV, "MonolithDev.kicad_pro"), encoding="utf-8").read()
    pro = pro.replace('"MonolithDev.kicad_pro"', '"Monolith.kicad_pro"').replace('"MonolithDev.kicad_sch"', '"Monolith.kicad_sch"')
    pro = pro.replace('"name": "MonolithDev"', '"name": "Monolith"')
    if not os.path.exists(os.path.join(PROD, "Monolith.kicad_pro")):  # it holds the board's rules from here on
        open(os.path.join(PROD, "Monolith.kicad_pro"), "w", encoding="utf-8", newline="\n").write(pro)

    process(ROOT, os.path.join(DEV, ROOT_DEV))
    for sh in SHEETS:
        process(sh, os.path.join(DEV, sh))


if __name__ == "__main__":
    main()
