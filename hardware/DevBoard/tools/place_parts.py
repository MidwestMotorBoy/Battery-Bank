"""Placement for the Monolith dev board (run with KiCad's python: "C:/Program Files/KiCad/10.0/bin/python.exe").

1. Mechanical: board outline (with gaps for the USB-C notches), mounting holes, USB-C connectors (locked).
2. Hand placement of everything that matters electrically (FIXED, PORT): holders, gauge core, both charger power
   trains (port 2 is port 1 shifted down), regulators, connectors, MCU.
3. Auto placement of the remaining small parts: each goes to the nearest free spot (courtyards never overlap)
   to the pads it connects to, inside its block's region.

Coordinates are board mm from the top-left corner (KiCad adds ORIGIN). Re-running places everything again.

    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/place_parts.py
    python tools/setup_board.py        # always afterwards: pcbnew rewrites the .kicad_pro with default rules
"""
import math
import os
import re
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "MonolithDev.kicad_pcb")
ORIGIN = (50.0, 50.0)
W, H = 196.0, 115.0
USB_Y = (32.0, 68.0)
NOTCH_W = 10.2
HOLES = {"H1": (4, 4), "H2": (106, 4), "H3": (192, 4), "H4": (4, 111), "H5": (106, 111), "H6": (192, 111)}

# block regions (x0, y0, x1, y1) for auto placement
REGION = {
    "1": (110, 13, 136, 101),     # gauge column
    "2": (136, 88, 196, 115),     # sleep-current section along the bottom
    "3": (110, 0, 196, 13),       # MCU + headers along the top
    "4": (136, 13, 196, 50),      # port 1
    "5": (136, 50, 196, 88),      # port 2
    "0": (110, 0, 196, 115),
}

# ---- hand placement (board mm, rotation deg) ------------------------------------------------------------
FIXED = {
    # cells: + on the left; BT101 (CELL_N end) at the top
    "BT101": (55, 15, 0), "BT102": (55, 43, 0), "BT103": (55, 71, 0), "BT104": (55, 99, 0),
    # gauge core: shunt by BT101's - contact, protection FETs and fuse down the column
    # RS101 turned so its CELL_N pad faces BT101's - contact and its GND pad drops into the GND planes
    "RS101": (115, 20, 270), "U101": (123, 42, 0), "Q101": (130, 24, 0), "Q102": (130, 32, 0),
    # BQ40Z50 cell-input filter ladder (TI fig. 9-1): 100R per tap in a column (1206 so an open cell's fault
    # current doesn't burn them), 0.1u between adjacent VC nodes staggered in two columns right at the VC pins;
    # nodes VC4..VC1, CELL_N at 2.5 mm pitch
    "R104": (112.6, 37.6, 0), "R103": (112.6, 40.1, 0), "R102": (112.6, 42.6, 0), "R101": (112.6, 45.1, 0),
    "C101": (116.0, 38.85, 90), "C102": (117.8, 41.35, 90), "C103": (116.0, 43.85, 90), "C104": (117.8, 46.35, 90),
    "F102": (114, 96, 90), "J101": (113, 108, 0), "J103": (132.5, 92.5, 0),
    # cell NTC headers (TS1..TS4), each beside the tap test point of the cell it watches
    "J102": (106.3, 20.0, 0), "J105": (106.3, 47.0, 0), "J106": (106.3, 75.0, 0), "J107": (106.3, 103.0, 0),
    # sleep-current section: R_MEAS, amplifiers, LDO, 3.3 V buck; output probe loops on the bottom edge
    "R201": (150, 96, 0), "U201": (160, 95, 0), "U202": (160, 104, 0), "U203": (146, 105, 0),
    "U204": (180, 96, 0), "L201": (184.3, 96, 0), "JP201": (140, 103, 0),
    # MCU top band; antenna (pin-1 end) at the top edge
    "U301": (150, 5.8, 0), "J301": (118.8, 6, 90), "J302": (131, 6, 90), "J303": (168, 6, 90),
}

# one charger port in a local frame: Q401 left, L401 centre, Q402 right; input caps above Q401, output caps
# below Q402, BQ25756 below the inductor. The frame is turned 180 deg onto the board so the input side faces
# the USB-C edge and the output side faces the pack bus.
PORT = {
    "Q01": (-11, 0, 0), "L01": (0, 0, 0), "Q02": (11, 0, 180),
    "U03": (0, 9.6, 90),
    "R24": (-20.3, -9.0, 90), "R27": (20.3, 9.0, 270), "R30": (21.8, 16.3, 0),   # RBAT: VBAT_SYS pad toward R30
}
# Bulk banks: one row of 1210 MLCCs right behind each half-bridge (they carry the switching-frequency ripple), the
# 0603 HF cap (C30 / C38, placed below) straddling the FET's drain and ground pads, one more MLCC stood on end beside
# the FET's drain edge, and the solid polymer bulk cap (C21 / C32, no DC-bias loss) one row further back.
for ref, (x, y) in {"C20": (-11, -7.75), "C24": (-15.6, -7.75), "C27": (-6.4, -7.75)}.items():
    PORT[ref] = (x, y, 0)
PORT["C23"] = (-16.1, 0, 270)
PORT["C21"] = (-11, -13.0, 0)        # 68u 35V polymer, + pad on the same side as the MLCCs' pad 1
for ref, (x, y) in {"C31": (11, 7.75), "C35": (15.6, 7.75)}.items():
    PORT[ref] = (x, y, 180)
PORT["C34"] = (15.9, 0.35, 270)
PORT["C32"] = (13.3, 13.0, 180)      # 100u 25V polymer
PORT_CENTRE = {"4": (158, 31.5), "5": (158, 68.5)}
PORT_EXTRA = {  # board offsets from the port centre for the PD controller side (not turned)
    "U01": (19, -8, 0),
    "U04": (25.84, 15.5, 0), "L02": (32.39, 14.5, 0), "C43": (25.5, -14.5, 0),
}

# ---- structured placement (board mm, port 1; port 2 is the same layout 37 mm lower) ------------------------
# Support parts sit in rows and columns on the side of the pin they serve, all parts in a row turned the same way
# (0/180 picked so the signal pad faces its pin). ("col", refs, x centre, top y, rot) stacks downwards;
# ("row", refs, left x, y centre, rot) runs rightwards; ("at", ref, x, y, rot) centres one courtyard on (x, y).
PORT_LAYOUT = [
    # BQ25756 (U403): FB divider + SRP/SRN filter + DRV_SUP left, programming resistors and TS above, ACUV/ACOV
    # divider, FSW and ACP/ACN filter right
    ("col", ["R418", "R419", "C417", "C419", "C418"], 151.4, 13.05, 0, 0.05),
    ("row", ["R414", "R413", "R416", "R415", "R417", "TH401"], 153.55, 17.2, 90, 0.08),
    ("row", ["R412", "R411", "R410", "R409"], 161.75, 20.63, 90, 0.08),
    ("row", ["C414", "C415", "C416"], 161.75, 23.88, 90, 0.08), ("at", "C409", 168.3, 23.88, 0),  # VAC cap (0805)
    # HF caps straddling each half-bridge's drain and ground pads (0603 pad pitch = the FET's pad pitch), smallest
    # loop on the board; output-sense series resistors and the I2CC header left of Q402
    ("at", "C430", 168.8, 36.6, 0),
    ("at", "C438", 146.9, 26.5, 0),
    # SRP/SRN series resistors beside RBAT, each at the pad it senses (Kelvin taps short, out of the current path)
    ("at", "R428", 135.1, 24.45, 90), ("at", "R429", 135.1, 20.35, 90),
    ("at", "J402", 137.95, 31.0, 0),
    # TPS25751 (U401): supply caps left, address straps (divider top / bottom / 0R) and EEPROM above,
    # VBUS/PP5V caps right, CC caps between the ESD parts and the connector (VBUS TVS D401 beside them)
    ("col", ["R401", "C403", "C404", "C408", "C405"], 171.7, 16.4, 0, 0.08),
    ("row", ["R1"], 163.475, 13.88, 0, 0.08),
    ("row", ["R2"], 163.475, 15.51, 0, 0.08),
    ("at", "U402", 175.1, 14.65, 0),
    ("row", ["R402", "R403", "R404"], 173.55, 17.5, 90, 0.08),
    # VBUS cap right of U401's VBUS power pad (the VBUS feed passes over its VBUS pad); the PP5V cap (0603) above U401
    # beside PP5V pin 34, clear of the VBUS pad
    ("fix", "C406", 183.75, 23.0, 270), ("fix", "C407", 176.5, 20.0, 0),
    ("row", ["R425", "R426"], 176.6, 34.9, 90, 0.08),
    # TPS62933 5 V buck in a line, hot loop first: input bulk, 0.1u straddling VIN/GND (pins 3/4), U404, BST cap
    # between the SW/BST pins and L402, L402 touching; FB/SS/EN above U404, output caps above L402
    ("at", "C444", 177.2, 46.6, 90), ("at", "C445", 179.64, 46.6, 90), ("at", "C446", 181.66, 47.5, 90),
    ("at", "C440", 186.03, 47.0, 90),
    ("row", ["R433", "R434", "C439"], 180.0, 40.8, 90, 0.05),
    ("at", "C447", 181.5, 38.05, 0),                    # DNP feed-forward cap, right above R433 (in parallel)
    ("at", "R435", 158.5, 14.3, 0),                     # CHG_INH -> CE series resistor, above the ICHG/CE row
    # gate-drive support (tools/route_power.py routes it): each BTST cap right under its BTST/SW pins, BTST pad inner
    # (the bootstrap loop stays on F.Cu, no vias); DRV_SUP cap, REGN cap and the REGN->DRV_SUP 10R stacked left of
    # the IC between Q402 and L401 (F.Cu lanes from pins 23/24 under C413); both bootstrap diodes right of C412,
    # reached through In2/B.Cu. Fixed rotations ("fix"): pad order matters here, not nearest-pin scoring.
    ("fix", "C413", 155.5, 26.2, 180), ("fix", "C412", 160.5, 26.2, 0),
    ("fix", "C411", 151.1, 24.6, 90), ("fix", "R420", 152.95, 27.55, 90), ("fix", "C410", 151.1, 28.4, 270),
    ("fix", "D405", 164.0, 26.3, 0), ("fix", "D404", 164.0, 28.25, 0),
    ("at", "R432", 182.4, 43.6, 0),
    ("row", ["C441", "C442"], 186.0, 41.9, 0, 0.05),
    # probe field under the power stage: SW test points straight below their inductor pads, pull-ups under
    # their test points; VBUS and PP5V at the connector edge
    ("at", "TP402", 139.2, 39.6, 0), ("at", "TP404", 144.3, 39.6, 0),
    ("at", "TP407", 149.4, 39.6, 0), ("at", "TP406", 154.5, 39.6, 0), ("at", "TP405", 159.6, 39.6, 0),
    ("at", "TP411", 139.2, 45.6, 0), ("at", "TP409", 144.3, 45.6, 0), ("at", "TP410", 149.4, 45.6, 0),
    ("at", "TP408", 154.5, 45.6, 0),
    ("at", "R423", 139.2, 48.65, 0), ("at", "R421", 144.3, 48.65, 0), ("at", "R422", 149.4, 48.65, 0),
    ("at", "R431", 160.3, 48.1, 0),
    ("at", "TP401", 192.6, 15.6, 0), ("at", "TP403", 192.6, 20.9, 0),
    # rev A5: scope-ground loop beside the SW1/SW2 probe points (TH304 moved 1 mm left to make room), PPHV and VBUS
    # HF caps by their pins, CE_N and LDO_3V3 probe pads
    ("at", "TP412", 162.2, 43.6, 0),
    ("at", "C449", 179.24, 27.35, 0), ("fix", "C450", 185.6, 23.3, 270),  # VBUS cap: VBUS pad in the VBUS strip, GND pad below it
    ("at", "TP413", 161.6, 14.37, 0), ("at", "TP414", 177.87, 29.83, 0),  # CE_N pad beside R435
]
PORT_DY = 37.0

LAYOUT = [
    # gauge: BAT/PBI/PACK/VCC parts in a row over the top pins, gate resistors beside each FET (series left,
    # 10M gate-source right), pack bypass caps under Q102, SMBus series resistors right, sense filter left
    ("row", ["C105", "R105", "D101", "R113", "R106"], 118.3, 37.2, 90, 0.08),
    ("at", "R109", 127.3, 24.0, 90), ("at", "R110", 132.8, 24.0, 90),
    ("at", "R111", 127.3, 32.0, 90), ("at", "R112", 132.8, 32.0, 90),
    # ESD caps across the FET pair (TI fig. 9-2 C1/C2, CELL_P -> PACK_P), in the gap between Q101 and Q102
    ("at", "C110", 127.8, 28.0, 0), ("at", "C111", 131.2, 28.0, 0),
    ("row", ["C108", "C107"], 128.2, 36.7, 90, 0.08),
    ("col", ["R115", "R116"], 127.4, 41.125, 0, 0.08),
    ("at", "R114", 124.0, 46.3, 90),
    ("at", "C106", 119.45, 45.3, 90),
    ("row", ["R108", "R107"], 116.825, 49.4, 90, 0.05),
    # Q102 gate extras (DNP) in a row left of R111: R111 bypass diode, VGS clamp, gate cap
    ("at", "D102", 125.3, 32.0, 90), ("at", "D103", 123.0, 32.0, 90), ("at", "C109", 120.9, 32.0, 90),
    # BTP_INT level shift by the gauge's BTP pin, gate pull-down beside R114
    ("at", "Q103", 131.35, 40.67, 90), ("at", "R117", 121.82, 46.61, 90),
    # wake button, its series resistor and the bench PACK_P header just above the pack probe field
    ("at", "SW101", 128.11, 48.81, 90), ("at", "R118", 126.4, 54.62, 90), ("at", "J104", 131.16, 56.41, 90),
    # SMB_PU test loop next to the EV2400 header
    ("at", "TP308", 120.5, 90.5, 0),
    # cell-tap test points beside the holder contact each one measures
    ("at", "TP102", 106.3, 15.0, 0), ("at", "TP103", 106.3, 43.0, 0),
    ("at", "TP104", 106.3, 71.0, 0), ("at", "TP105", 106.3, 99.0, 0),
    # pack and system probe field
    ("at", "TP101", 113.5, 62.0, 0), ("at", "TP106", 119.85, 62.0, 0), ("at", "TP107", 126.2, 62.0, 0),
    ("at", "TP301", 132.55, 62.0, 0),
    ("at", "TP302", 113.5, 68.0, 0), ("at", "TP303", 119.85, 68.0, 0), ("at", "TP304", 126.2, 68.0, 0),
    ("at", "TP305", 132.55, 68.0, 0),
    # MCU: antenna link at its pins, BOOT0/NRST/decoupling column at the supply corner, 3V3 link and status LED
    # beside it; NTC dividers as a 4-row array (TH1..TH4), I2C pull-ups by SDA/SCL
    ("fix", "R303", 145.4, 4.75, 180),          # ANT_IN pad (1) towards U301 so the two RF links don't cross
    # (both columns sit back from the module's pins: a 2 mm via channel for the left-side signal pins, route_power.py)
    ("col", ["R302", "C304", "C301", "C302", "C303"], 143.0, 5.6, 0, 0.1),
    ("col", ["R301", "D301", "R306", "R307"], 139.7, 5.0, 0, 0.1),
    ("col", ["R308", "R309", "R310", "R311"], 161.0, 4.4, 0, 0.1),
    ("col", ["C308", "C309", "C310", "C311"], 164.4, 4.62, 0, 0.54),
    ("col", ["R314", "R315", "R304", "R305"], 156.2, 6.0, 0, 0.1),     # 2 mm via channel right of the module
    ("at", "R312", 158.5, 10.6, 90),
    # bring-up aids: reset button between the SWD and UART headers; J303 series resistors under pins 3-5;
    # BOOT0 pad under the MCU
    ("at", "SW301", 128.0, 11.2, 0),
    # TH5 divider (R320 from NTC_EN, C312 at the ADC node) under J303, left of the override resistors
    ("at", "R320", 168.0, 10.6, 90), ("at", "C312", 170.2, 10.6, 90),
    ("at", "R316", 173.08, 10.6, 90), ("at", "R317", 175.62, 10.6, 90), ("at", "R318", 178.16, 10.6, 90),
    ("at", "R319", 180.7, 10.6, 90),
    ("at", "TP306", 147.6, 13.2, 0),
    # board NTCs where they sense: TH1/TH2 beside each port's power stage, TH3 between the USB-C connectors,
    # TH4 in the probe row under port 1's stage (heatsink position)
    ("at", "TH301", 142.0, 34.4, 0), ("at", "TH302", 142.0, 34.4 + PORT_DY, 0),
    ("at", "TH303", 192.5, 50.1, 0), ("at", "TH304", 158.6, 45.35, 0),
    # TH5 between the protection FETs Q101/Q102, right of C111 (both drains within about 4 mm)
    ("at", "TH305", 133.6, 27.79, 90),
    # sleep-current section: Kelvin 0R taps above R_MEAS, amp decoupling left of each amp, input filter and
    # output resistors right, LDO caps either side, 3.3 V buck caps along its flow
    ("at", "R202", 148.4, 92.9, 90), ("at", "R203", 151.6, 92.9, 90),
    ("at", "C202", 156.3, 94.0, 90), ("at", "C203", 156.3, 103.0, 90),
    ("at", "C201", 163.5, 94.35, 90), ("at", "R204", 163.5, 97.9, 90), ("at", "R205", 163.5, 103.0, 90),
    ("at", "R206", 143.0, 100.0, 90), ("at", "C204", 142.85, 105.0, 90), ("at", "C205", 149.2, 105.0, 90),
    ("at", "TP204", 172.0, 96.0, 0), ("at", "C206", 176.9, 96.0, 90), ("at", "R208", 180.0, 99.6, 90),
    ("at", "TP205", 180.0, 103.6, 0), ("at", "C207", 187.95, 96.0, 90), ("at", "R207", 190.6, 96.0, 90),
    # 3V3_SLEEP probe pad and its optional pull-up (DNP) beside the TPS62177
    ("at", "R313", 187.0, 103.0, 0), ("at", "TP307", 191.0, 103.0, 0),
    # rev A5 probe points: LDO input/output pads by the LDO caps, cell top before F101, scope-ground loops in a third
    # row of the pack probe field
    ("at", "TP206", 145.46, 101.35, 0), ("at", "TP207", 148.82, 101.58, 0),
    # sleep-current outputs (replace the SMAs): each amp output loop with its own GND loop 4.5 mm away for a short
    # probe ground lead, in a row along the bottom edge under the amps
    ("at", "TP201", 162.0, 110.5, 0), ("at", "TP208", 166.5, 110.5, 0),
    ("at", "TP202", 173.0, 110.5, 0), ("at", "TP209", 177.5, 110.5, 0),
    ("at", "TP108", 117.25, 97.4, 0),
    ("at", "TP109", 113.5, 74.0, 0), ("at", "TP309", 119.85, 74.0, 0),
    # J104 series Schottky (reverse-lead / back-feed protection) between the bench header and the probe field
    ("at", "D104", 121.9, 56.4, 0),
]

# small silkscreen notes (text, x, y): UART pin functions over J302 (pin 1 = MCU TX out)
# and a warning under TP102: CELL_N is the gauge ground, a scope ground there bypasses RS101
PIN_NOTES = [("TX", 131.0, 3.3), ("RX", 133.54, 3.3), ("G", 136.08, 3.3), ("not GND", 106.3, 17.6)]

# connector pinouts on the silkscreen (pin number -> text), placed beside each pin on the side with room
PIN_LABELS = {
    "J101": {"1": "B-", "2": "C1", "3": "C2", "4": "C3", "5": "B+"},                     # welded pack
    "J102": {"1": "TS1", "2": "-"}, "J105": {"1": "TS2", "2": "-"},                     # cell NTCs (- = CELL_N)
    "J106": {"1": "TS3", "2": "-"}, "J107": {"1": "TS4", "2": "-"},
    "J103": {"1": "GND", "2": "SCL", "3": "SDA", "4": "NC"},                            # EV2400 SMBus
    "J104": {"1": "+", "2": "-"},                                                       # bench supply
    "J303": {"1": "3V3", "2": "TH5", "3": "NTC", "4": "5V1", "5": "5V2", "6": "INH", "7": "G"},
    "J402": {"1": "SDA", "2": "SCL", "3": "G"}, "J502": {"1": "SDA", "2": "SCL", "3": "G"},
    "J301": {"1": "1"},                                                                 # SWD pin 1
}
# what a part is for, beside its courtyard
PART_LABELS = {"SW101": "WAKE", "SW301": "RESET", "JP201": "AMP EN", "JP202": "MEAS PWR", "J301": "SWD"}

# silkscreen block titles (text, x, y, rotation)
TITLES = [("PORT 1", 134.8, 46.0, 90), ("PORT 2", 134.8, 46.0 + PORT_DY, 90), ("GAUGE", 121.5, 17.0, 0),
          ("MCU", 116.5, 12.6, 0), ("SLEEP CURRENT", 148.5, 111.5, 0),
          ("FIT CELLS BEFORE USB", 55.0, 113.3, 0)]


def k(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(ORIGIN[0] + x), pcbnew.FromMM(ORIGIN[1] + y))


PRO = os.path.join(HERE, "..", "MonolithDev.kicad_pro")
pro_backup = open(PRO, encoding="utf-8").read()      # pcbnew's save rewrites the project with default rules
board = pcbnew.LoadBoard(PCB)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

# ---- 1. mechanical --------------------------------------------------------------------------------------
for ref, (x, y) in HOLES.items():
    fps[ref].SetPosition(k(x, y))
for ref, yc in (("J401", USB_Y[0]), ("J501", USB_Y[1])):
    fps[ref].SetLocked(False)
    fps[ref].SetOrientationDegrees(90)
    fps[ref].SetPosition(k(W, yc))
    fps[ref].SetLocked(True)

# ---- 2. hand placement ----------------------------------------------------------------------------------
placed = {}


def put(ref, x, y, rot):
    fp = fps[ref]
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(k(x, y))
    placed[ref] = fp


for ref, (x, y, r) in FIXED.items():
    put(ref, x, y, r)
for blk, (cx, cy) in PORT_CENTRE.items():
    for suf, (x, y, r) in PORT.items():
        put(suf[0] + blk + suf[1:], cx - x, cy - y, (r + 180) % 360)
    for suf, (x, y, r) in PORT_EXTRA.items():
        put(suf[0] + blk + suf[1:], cx + x, cy + y, r)
# USB-C front end, placed from the connector (J501 sits 36 mm below J401, the rest of port 2 37 mm): CC ESD D402
# with its CC caps above the CC/DP/DN pin rows, the DP/DN ESD D403 in line with the data pins, the VBUS TVS D401
# lying below them, its VBUS pad against the connector's lower VBUS pins (offsets from (W, USB_Y))
CONN_EXTRA = {"D02": (183.0, -4.0, 90), "C02": (185.38, -4.0, 90), "C01": (186.435, -4.0, 90),
              "D01": (184.85, 3.5, 180)}   # D403 (D+/D- ESD) removed 2026-10-14: D+/D- shorted by R440
for blk, yc in (("4", USB_Y[0]), ("5", USB_Y[1])):
    for suf, (x, dy, r) in CONN_EXTRA.items():
        put(suf[0] + blk + suf[1:], x, yc + dy, r)
for ref in list(HOLES) + ["J401", "J501"]:
    placed[ref] = fps[ref]


# ---- 3. auto placement ----------------------------------------------------------------------------------
def crt_tp(fp):
    """Test points reserve room for their net-name label above them (placed there in the silk pass)."""
    r = crt(fp)
    if fp.GetReference().startswith("TP"):
        r = (r[0] - pcbnew.FromMM(2.2), r[1] - pcbnew.FromMM(1.6), r[2] + pcbnew.FromMM(2.2), r[3])
    return r


def crt(fp, margin=0.25):
    """Courtyard bounding box (F.CrtYd graphics, else pads) in board units, grown by margin mm."""
    bbs = [g.GetBoundingBox() for g in fp.GraphicalItems() if g.GetLayer() == pcbnew.F_CrtYd]
    if not bbs:
        bbs = [p.GetBoundingBox() for p in fp.Pads()]
    m = pcbnew.FromMM(margin)
    return (min(b.GetLeft() for b in bbs) - m, min(b.GetTop() for b in bbs) - m,
            max(b.GetRight() for b in bbs) + m, max(b.GetBottom() for b in bbs) + m)


def hit(r, rects):
    return any(r[0] < q[2] and q[0] < r[2] and r[1] < q[3] and q[1] < r[3] for q in rects)


def box_at(fp, rot, cx, cy):
    """Turn fp to rot and move it so its courtyard centre lands on board mm (cx, cy)."""
    fp.SetOrientationDegrees(rot % 360)
    fp.SetPosition(k(cx, cy))
    r = crt(fp, 0)
    p = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(p.x - ((r[0] + r[2]) // 2 - p.x), p.y - ((r[1] + r[3]) // 2 - p.y)))


def pad_score(fp):
    """Summed distance from each signal pad to the nearest placed pad on the same net (GND ignored)."""
    s = 0
    for p in fp.Pads():
        n = p.GetNetname()
        pts = [q.GetPosition() for f in placed.values() if f is not fp for q in f.Pads() if q.GetNetname() == n]
        if n and n != "GND" and pts:
            s += min(math.hypot(p.GetPosition().x - q.x, p.GetPosition().y - q.y) for q in pts)
    return s


def struct_put(ref, cx, cy, rot):
    fp = fps[ref]
    best = None
    for r in (rot, rot + 180):
        box_at(fp, r, cx, cy)
        sc = pad_score(fp)
        if best is None or sc < best[0] - 1:
            best = (sc, r)
    box_at(fp, best[1], cx, cy)
    placed[ref] = fp


def size(ref, rot):
    fp = fps[ref]
    fp.SetOrientationDegrees(rot % 360)
    r = crt(fp, 0)
    return pcbnew.ToMM(r[2] - r[0]), pcbnew.ToMM(r[3] - r[1])


def run_layout(items):
    done = []
    for it in items:
        kind = it[0]
        if kind == "at":
            _, ref, x, y, rot = it
            struct_put(ref, x, y, rot)
            done.append(ref)
        elif kind == "fix":                      # exact rotation, no 0/180 choice
            _, ref, x, y, rot = it
            box_at(fps[ref], rot, x, y)
            placed[ref] = fps[ref]
            done.append(ref)
        elif kind == "col":
            _, refs, x, y, rot, gap = it
            for ref in refs:
                h = size(ref, rot)[1]
                struct_put(ref, x, y + h / 2, rot)
                y += h + gap
                done.append(ref)
        elif kind == "row":
            _, refs, x, y, rot, gap = it
            for ref in refs:
                w = size(ref, rot)[0]
                struct_put(ref, x + w / 2, y, rot)
                x += w + gap
                done.append(ref)
    return done


def port2(ref):
    return {"R1": "R3", "R2": "R4"}.get(ref) or re.sub(r"^([A-Z]+)4(\d\d)$", r"\g<1>5\2", ref)


for ref in run_layout(PORT_LAYOUT):        # port 2: identical copy of port 1, PORT_DY lower
    a, b = fps[ref], fps[port2(ref)]
    b.SetOrientationDegrees(a.GetOrientationDegrees())
    b.SetPosition(pcbnew.VECTOR2I(a.GetPosition().x, a.GetPosition().y + pcbnew.FromMM(PORT_DY)))
    placed[port2(ref)] = b
run_layout(LAYOUT)

rects = [crt(fp) for ref, fp in placed.items()]
a, b = k(141, 0), k(159, 4.2)              # STM32WB1MMC antenna end (pin-1 end, top edge): nothing else here
rects.append((a.x, a.y, b.x, b.y))
for yc in USB_Y:                          # keep the "USB n" label spot (silk pass) free
    a, b = k(W - 7.2, yc + 7.4), k(W - 0.2, yc + 9.4)
    rects.append((a.x, a.y, b.x, b.y))
holder_keepout = [(pcbnew.FromMM(ORIGIN[0] + 0), pcbnew.FromMM(ORIGIN[1]), pcbnew.FromMM(ORIGIN[0] + 109.5),
                   pcbnew.FromMM(ORIGIN[1] + H))]
pads_by_net = {}
for ref, fp in placed.items():
    for p in fp.Pads():
        pads_by_net.setdefault(p.GetNetname(), []).append(p.GetPosition())


def target(fp):
    pts = []
    for p in fp.Pads():
        n = p.GetNetname()
        if n and n != "GND" and not n.startswith("unconnected") and n in pads_by_net:
            pts += pads_by_net[n]
    if not pts:
        return None
    return (sum(q.x for q in pts) / len(pts), sum(q.y for q in pts) / len(pts))


def block(ref):
    m = re.match(r"[A-Z]+(\d+)$", ref)
    d = m.group(1) if m else "0"
    return d[0] if len(d) == 3 else "0"


todo = [r for r in fps if r not in placed]
todo.sort(key=lambda r: -(lambda b: b[2] - b[0])(crt(fps[r], 0)) * (lambda b: b[3] - b[1])(crt(fps[r], 0)))
failed = []
for npass in range(3):                   # pass 2: parts whose neighbours were placed later; pass 3: any region
    for ref in [r for r in todo if r not in placed]:
        fp = fps[ref]
        t = target(fp)
        x0, y0, x1, y1 = REGION[block(ref) if npass < 2 else "0"]
        if t is None:
            t = (pcbnew.FromMM(ORIGIN[0] + (x0 + x1) / 2), pcbnew.FromMM(ORIGIN[1] + (y0 + y1) / 2))
        best = None
        step = pcbnew.FromMM(0.5)
        for rot in (0, 90):
            fp.SetOrientationDegrees(rot)
            for ring in range(0, 120):
                cands = []
                for i in range(-ring, ring + 1):
                    for j in (-ring, ring):
                        cands += [(i, j), (j, i)]
                found = None
                for i, j in sorted(set(cands), key=lambda c: math.hypot(*c)):
                    x, y = t[0] + i * step, t[1] + j * step
                    fp.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
                    r = crt_tp(fp)
                    if r[0] < pcbnew.FromMM(ORIGIN[0] + x0) or r[2] > pcbnew.FromMM(ORIGIN[0] + x1) or \
                       r[1] < pcbnew.FromMM(ORIGIN[1] + y0) or r[3] > pcbnew.FromMM(ORIGIN[1] + y1):
                        continue
                    if hit(r, rects) or hit(r, holder_keepout):
                        continue
                    found = (math.hypot(i, j), rot, x, y)
                    break
                if found:
                    break
            if found and (best is None or found[0] < best[0]):
                best = found
        if best is None:
            failed.append(ref)
            continue
        _, rot, x, y = best
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
        placed[ref] = fp
        rects.append(crt_tp(fp))
        for p in fp.Pads():
            pads_by_net.setdefault(p.GetNetname(), []).append(p.GetPosition())
    todo = [r for r in todo if r not in placed]

# ---- 4. silkscreen: labels only where the spec asks (test points by net name, connectors, jumpers, holders)
for ref, fp in fps.items():
    pre = re.match(r"[A-Z]+", ref).group(0)
    fp.Reference().SetVisible(pre in ("J", "JP", "BT") and ref not in ("J401", "J501"))
    if pre == "TP":
        v = fp.Value()
        v.SetLayer(pcbnew.F_SilkS)
        v.SetVisible(True)
        v.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
        v.SetTextThickness(pcbnew.FromMM(0.15))
        v.SetTextAngleDegrees(0)


def box(b, m=0.15):
    m = pcbnew.FromMM(m)
    return (b.GetLeft() - m, b.GetTop() - m, b.GetRight() + m, b.GetBottom() + m)


# test-point labels: first free spot around the pad, clear of pads, footprint silk and earlier labels
obst = []
for fp in fps.values():
    obst += [box(p.GetBoundingBox()) for p in fp.Pads()]
    obst += [box(g.GetBoundingBox(), 0.1) for g in fp.GraphicalItems() if g.GetLayer() == pcbnew.F_SilkS]
    if fp.Reference().IsVisible() and not re.match(r"JP?\d", fp.GetReference()):
        obst.append(box(fp.Reference().GetBoundingBox(), 0.1))
edge = (pcbnew.FromMM(ORIGIN[0] + 0.5), pcbnew.FromMM(ORIGIN[1] + 0.5),
        pcbnew.FromMM(ORIGIN[0] + W - 0.5), pcbnew.FromMM(ORIGIN[1] + H - 0.5))
unplaced_labels = []
for txt, x, y in PIN_NOTES:               # reserve the pin-note spots before placing labels
    a, b = k(x - 0.5 * len(txt) - 0.3, y - 0.6), k(x + 0.5 * len(txt) + 0.3, y + 0.6)
    obst.append((a.x, a.y, b.x, b.y))
# connector pin labels and part-purpose labels (placed before the reference / test-point labels so they get the spots
# next to the pins): 0.8 mm text, clear of pads, silk, other labels and other parts. Pins in a column get text turned
# 90 degrees along the column (needs ~1 mm beside the pin); pins in a row get upright text above or below.
TXT_H = 0.8
EXTRA_SILK = []                            # (text, x, y, angle) in board mm, written with the outline below
crts = {r: crt(f, 0.05) for r, f in fps.items()}


def text_box(txt, x, y, ang=0):
    L = 0.72 * TXT_H * max(len(txt), 1) + 0.2
    w, h = (L, TXT_H + 0.2) if ang == 0 else (TXT_H + 0.2, L)
    a, b = k(x - w / 2, y - h / 2), k(x + w / 2, y + h / 2)
    return (a.x, a.y, b.x, b.y)


def free_spot(txt, x, y, owner, ang=0):
    r = text_box(txt, x, y, ang)
    if not (r[0] > edge[0] and r[1] > edge[1] and r[2] < edge[2] and r[3] < edge[3]):
        return None
    if hit(r, obst) or hit(r, [c for o, c in crts.items() if o != owner]):
        return None
    return r


missing = []
for ref, labels in PIN_LABELS.items():
    fp = fps[ref]
    pads = {p.GetNumber(): p for p in fp.Pads()}
    pts = {n: (pcbnew.ToMM(p.GetPosition().x) - ORIGIN[0], pcbnew.ToMM(p.GetPosition().y) - ORIGIN[1]) for n, p in pads.items()}
    cx = sum(q[0] for q in pts.values()) / len(pts); cy = sum(q[1] for q in pts.values()) / len(pts)
    xs = [q[0] for q in pts.values()]; ys = [q[1] for q in pts.values()]
    vertical = (max(ys) - min(ys)) >= (max(xs) - min(xs))      # pins in a column: labels left or right
    cx0, cy0, cx1, cy1 = [pcbnew.ToMM(v) - o for v, o in zip(crts[ref], (ORIGIN[0], ORIGIN[1], ORIGIN[0], ORIGIN[1]))]
    ang = 90 if vertical and ref != "J301" else 0

    def tang(txt):
        return 0 if txt in "+-" else ang

    def spot(n, txt, sgn):
        px, py = pts[n]
        L = 0.72 * TXT_H * len(txt) + 0.2
        if ref == "J301":                                       # 2-row SWD: "1" outboard of pin 1
            sgn2 = 1 if px > cx else -1
            return px + sgn2 * ((cx1 - cx0) / 2 - abs(px - cx) + 0.25 + L / 2), py
        if vertical:
            half = TXT_H / 2 if tang(txt) else L / 2
            return ((cx1 + 0.25 + half) if sgn > 0 else (cx0 - 0.25 - half)), py
        return px, ((cy1 + 0.2 + TXT_H / 2) if sgn > 0 else (cy0 - 0.2 - TXT_H / 2))

    def fit(n, t, sgn, taken):                                  # nudge along the row / column by up to 1 mm
        x, y = spot(n, t, sgn)
        for d in (0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5):
            xx, yy = (x, y + d) if vertical else (x + d, y)
            bx = free_spot(t, xx, yy, ref, tang(t))
            if bx and not hit(bx, taken):
                return (t, xx, yy, tang(t)), bx
        return None

    placed_all = False
    for sgn in (+1, -1):                                        # 1) all pins on one side
        got = []
        for n, t in labels.items():
            f = fit(n, t, sgn, [bx for _, bx in got])
            if not f:
                break
            got.append(f)
        else:
            for lab, bx in got:
                EXTRA_SILK.append(lab); obst.append(bx)
            placed_all = True
            break
    if not placed_all:                                          # 2) pin by pin, whichever side has room
        for n, t in labels.items():
            for sgn in (+1, -1):
                f = fit(n, t, sgn, [])
                if f:
                    EXTRA_SILK.append(f[0]); obst.append(f[1])
                    break
            else:
                missing.append(f"{ref}.{n}")
for ref, txt in PART_LABELS.items():
    x0, y0, x1, y1 = [pcbnew.ToMM(v) for v in crts[ref]]
    x0, x1, y0, y1 = x0 - ORIGIN[0], x1 - ORIGIN[0], y0 - ORIGIN[1], y1 - ORIGIN[1]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w = 0.72 * TXT_H * len(txt) + 0.2
    for x, y in ((cx, y0 - 0.65), (cx, y1 + 0.65), (x0 - w / 2 - 0.3, cy), (x1 + w / 2 + 0.3, cy),
                 (cx, y0 - 1.6), (cx, y1 + 1.6), (x0 - w / 2 - 1.2, cy), (x1 + w / 2 + 1.2, cy)):
        bx = free_spot(txt, x, y, ref)
        if bx:
            EXTRA_SILK.append((txt, x, y, 0)); obst.append(bx)
            break
    else:
        missing.append(ref)
print("pin/part labels without room:", missing)

for ref, fp in sorted(fps.items(), key=lambda kv: (not kv[0].startswith("TP"), kv[0])):
    if not (ref.startswith("TP") or re.match(r"JP?\d", ref)):
        continue
    # test points: net name centred just above the loop (same spot on every one; port test points carry no
    # P1/P2 prefix, the PORT 1 / PORT 2 block titles say which port); connectors: start from the courtyard edges,
    # falling back to a label turned along the left or right edge
    v, c = (fp.Value(), fp.GetPosition()) if ref.startswith("TP") else (fp.Reference(), fp.GetPosition())
    if not v.IsVisible():
        continue
    if not ref.startswith("TP"):
        x0, y0, x1, y1 = crt(fp, 0)
        hw, hh = (x1 - x0) / 2e6, (y1 - y0) / 2e6
        cands = [(0, -hh - 0.8, 0), (0, hh + 0.8, 0), (-hw - 2.0, 0, 0), (hw + 2.0, 0, 0), (-hw - 3.5, 0, 0),
                 (hw + 3.5, 0, 0), (0, -hh - 1.8, 0), (0, hh + 1.8, 0), (-hw + 1, -hh - 0.8, 0), (hw - 1, hh + 0.8, 0),
                 (-hw - 0.8, 0, 90), (hw + 0.8, 0, 90), (-hw - 1.9, 0, 90), (hw + 1.9, 0, 90),
                 (-hw - 2.6, 0, 90), (hw + 2.6, 0, 90),
                 (-hw - 0.8, hh + 1.75, 90), (hw + 0.8, hh + 1.75, 90),      # in line with a pin-label column
                 (-hw - 0.8, -hh - 1.75, 90), (hw + 0.8, -hh - 1.75, 90)]
        c = pcbnew.VECTOR2I((x0 + x1) // 2, (y0 + y1) // 2)
    else:
        cands = [(0, -2.4, 0), (0, -2.8, 0), (0, 2.4, 0), (-3.2, 0, 0), (3.2, 0, 0), (-4.2, 0, 0), (4.2, 0, 0)]
    # connector references boxed in by their pin labels fall back to the pin-label text size
    sizes = [None] if ref.startswith("TP") else [(1.0, 0.15), (0.8, 0.15)]
    found = False
    for sz in sizes:
        if sz:
            v.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(sz[0]), pcbnew.FromMM(sz[0])))
            v.SetTextThickness(pcbnew.FromMM(sz[1]))
        for dx, dy, ang in cands:
            v.SetTextAngleDegrees(ang)
            v.SetPosition(pcbnew.VECTOR2I(c.x + pcbnew.FromMM(dx), c.y + pcbnew.FromMM(dy)))
            r = box(v.GetBoundingBox(), 0.05)
            if r[0] > edge[0] and r[1] > edge[1] and r[2] < edge[2] and r[3] < edge[3] and not hit(r, obst):
                obst.append(r)
                found = True
                break
        if found:
            break
    if not found:
        v.SetVisible(False)             # no clear spot: hide rather than print over other silk
        unplaced_labels.append(ref)
print("test-point labels hidden (no free spot):", unplaced_labels)


# outline last: creating PCB_SHAPEs earlier breaks the SWIG wrappers of footprint graphics
for d in list(board.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts or (d.GetLayer() == pcbnew.F_SilkS and d.GetClass() == "PCB_TEXT"):
        board.Remove(d)
segs = [((0, 0), (W, 0)), ((0, H), (W, H)), ((0, 0), (0, H))]
y = 0.0
for yc in USB_Y:
    segs.append(((W, y), (W, yc - NOTCH_W / 2)))
    y = yc + NOTCH_W / 2
segs.append(((W, y), (W, H)))
for a, b in segs:
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(k(*a)); s.SetEnd(k(*b))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1))
    board.Add(s)
for txt, yc in (("USB 1", USB_Y[0]), ("USB 2", USB_Y[1])):     # port labels beside the connectors
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(1.2))); t.SetTextThickness(pcbnew.FromMM(0.2))
    t.SetPosition(k(W - 4.5, yc + 7.6))                       # just below the connector
    board.Add(t)
for txt, x, y, ang in [(t, x, y, 0) for t, x, y in PIN_NOTES] + EXTRA_SILK:
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8))); t.SetTextThickness(pcbnew.FromMM(0.15))
    t.SetPosition(k(x, y)); t.SetTextAngleDegrees(ang)
    board.Add(t)
for txt, x, y, rot in TITLES:              # block titles
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(1.2))); t.SetTextThickness(pcbnew.FromMM(0.2))
    t.SetPosition(k(x, y)); t.SetTextAngleDegrees(rot)
    board.Add(t)
# antenna keep-out: no tracks, vias or pours on any copper layer around the STM32WB1MMC antenna end (pin-1 end at the
# top edge). ST gives no keep-out drawing for the module; this follows its reference PCB (module at the board edge,
# nothing past the antenna end) and covers the placement-reserved strip either side of and above the module.
for z in list(board.Zones()):
    if z.GetZoneName() == "ANT_KEEPOUT":
        board.Remove(z)
ux0, uy0, ux1, uy1 = (v / 1e6 - o for v, o in zip(crt(fps["U301"], 0), (ORIGIN[0], ORIGIN[1], ORIGIN[0], ORIGIN[1])))
z = pcbnew.ZONE(board)
z.SetZoneName("ANT_KEEPOUT")
z.SetIsRuleArea(True)
z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
(z.SetDoNotAllowZoneFills if hasattr(z, "SetDoNotAllowZoneFills") else z.SetDoNotAllowCopperPour)(True)
z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
z.SetLayerSet(pcbnew.LSET.AllCuMask())
ol = z.Outline(); ol.NewOutline()
for x, y in ((141, 0), (159, 0), (159, 4.2), (ux1, 4.2), (ux1, uy0), (ux0, uy0), (ux0, 4.2), (141, 4.2)):
    pt = k(x, y); ol.Append(pt.x, pt.y)
board.Add(z)
boxes = {ref: crt(fp, 0) for ref, fp in fps.items() if not ref.startswith("H")}
refs = sorted(boxes)
clash = [(a, b) for i, a in enumerate(refs) for b in refs[i + 1:] if hit(boxes[a], [boxes[b]])]
print("courtyard overlaps:", clash)
board.Save(PCB)
# KiCad-library footprints whose 3D model file KiCad 10 does not ship: point them at a same-size shipped model
# (text pass: pcbnew's Models() returns copies, so assigning m_Filename there does not stick)
MODEL_SUBST = {
    "Button_Switch_SMD.3dshapes/SW_Push_1P1T_XKB_TS-1187A.step":
        "Button_Switch_SMD.3dshapes/SW_SPST_TL3342.step",   # 5.2 mm tact, pads +/-3.15/1.9 vs +/-3.0/1.875
}
pcb_text = open(PCB, encoding="utf-8").read()
for old, new in MODEL_SUBST.items():
    pcb_text = pcb_text.replace(old, new)
open(PCB, "w", encoding="utf-8", newline="\n").write(pcb_text)
open(PRO, "w", encoding="utf-8", newline="\n").write(pro_backup)
print(f"placed {len(placed)} / {len(fps)}; not placed: {sorted(set(failed) - set(placed))}")
