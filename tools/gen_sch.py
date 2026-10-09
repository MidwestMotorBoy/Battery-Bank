import uuid, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import gen
ROOT = "87221f23-e3e9-4980-bed8-cd30d4c8eaab"
U = lambda: str(uuid.uuid4())
F = '(effects (font (size 1.27 1.27))'
def q(s): return '"' + str(s).replace('"', "'") + '"'
G = 2.54
# ---------- library symbols ----------
def prop_lib(ref, val):
    return (f'(property "Reference" {q(ref)} (at 0 0 0) {F}))\n(property "Value" {q(val)} (at 0 0 0) {F}))\n'
            f'(property "Footprint" "" (at 0 0 0) {F} (hide yes)))\n(property "Datasheet" "" (at 0 0 0) {F} (hide yes)))\n'
            f'(property "Description" "" (at 0 0 0) {F} (hide yes)))')
def pin(num, name, x, y, ang, ln=2.54):
    return f'(pin passive line (at {x:.2f} {y:.2f} {ang}) (length {ln}) (name {q(name)} {F})) (number {q(num)} {F})))'
def libsym(name, ref, pins, rect, hide=False, extra=""):
    h = "(pin_numbers hide) (pin_names (offset 0) hide)" if hide else "(pin_names (offset 1.016))"
    x0, y0, x1, y1 = rect
    return (f'(symbol "Monolith:{name}" {h} (exclude_from_sim no) (in_bom yes) (on_board yes)\n{prop_lib(ref, name)}\n'
            f'(symbol "{name}_0_1" (rectangle (start {x0} {y0}) (end {x1} {y1}) (stroke (width 0.254) (type default)) (fill (type background))){extra})\n'
            f'(symbol "{name}_1_1"\n' + "\n".join(pins) + "))")
LIB = {}; PINPOS = {}       # PINPOS[sym][num] = (dx, dy_lib, side)
def ic(name, pins):
    n = len(pins); nl = (n + 1) // 2; W = 15.24; top = (nl - 1) * G / 2; H = top + G
    out = []; pos = {}
    for i, (num, nm) in enumerate(pins):
        if i < nl: x, y, a, side = -W - G, top - i * G, 0, "L"
        else: j = n - 1 - i; x, y, a, side = W + G, top - j * G, 180, "R"
        out.append(pin(num, nm, x, y, a)); pos[str(num)] = (x, y, side)
    LIB[name] = libsym(name, "U", out, (-W, H, W, -H)); PINPOS[name] = pos
def two(name, ref):
    LIB[name] = libsym(name, ref, [pin("1", "~", 0, 3.81, 270, 1.27), pin("2", "~", 0, -3.81, 90, 1.27)], (-1.016, 2.54, 1.016, -2.54), hide=True)
    PINPOS[name] = {"1": (0, 3.81, "R"), "2": (0, -3.81, "R")}
ic("TPS25751D", [(p, n) for p, n, _ in gen.parts[0][5]])
ic("BQ25756", [(p, n) for p, n, _ in gen.parts[1][5]])
for n, r in (("R", "R"), ("C", "C"), ("L", "L"), ("TVS", "D"), ("NTC", "RT")): two(n, r)
LIB["NFET"] = libsym("NFET", "Q", [pin("D", "D", 0, 5.08, 270), pin("G", "G", -5.08, 0, 0), pin("S", "S", 0, -5.08, 90)], (-2.54, 2.54, 2.54, -2.54))
PINPOS["NFET"] = {"D": (0, 5.08, "R"), "G": (-5.08, 0, "L"), "S": (0, -5.08, "R")}
two("FUSE", "F"); two("LED", "D")
GNDP = [1, 2, 3, 4, 5, 8, 15, 17, 19, 21, 24, 31] + list(range(43, 78))
WBN = {6: "ANT_IN", 7: "ANT_OUT", 9: "PA4", 10: "PA8", 11: "PA1", 12: "PA6", 13: "PA2", 14: "PB8", 16: "VDDA", 18: "VBAT", 20: "VDDSMPS", 22: "BOOT0", 23: "NRST",
       25: "PB7", 26: "PB5", 27: "PB6", 28: "PA3", 29: "PA7", 30: "PA12", 32: "PA11", 33: "PB4", 34: "PA14", 35: "PA13", 36: "PA10", 37: "PA0", 38: "PA9", 39: "PA5",
       40: "PB1", 41: "PB0", 42: "PB2"}
ic("STM32WB1MMC", [(k, WBN[k]) for k in sorted(WBN)] + [(k, "VSSRF" if k in (5, 8) else "VSSSMPS" if k == 21 else "VSS") for k in GNDP])
ic("TPS25810", [(1, "FAULT"), (2, "IN1"), (3, "IN1"), (4, "IN2"), (5, "AUX"), (6, "EN"), (7, "CHG"), (8, "CHG_HI"), (9, "REF_RTN"), (10, "REF"), (11, "CC1"), (12, "GND"),
                (13, "CC2"), (14, "OUT"), (15, "OUT"), (16, "DEBUG"), (17, "AUDIO"), (18, "POL"), (19, "UFP"), (20, "LD_DET"), ("EP", "Thermal pad")])
LIB["PAD"] = libsym("PAD", "W", [pin("1", "~", 2.54, 0, 180, 2.54)], (-1.27, 1.27, 0, -1.27), hide=True)
PINPOS["PAD"] = {"1": (2.54, 0, "R")}
ic("BQ77915", [(i + 1, n) for i, n in enumerate("VDD AVDD VC5 VC4 VC3 VC2 VC1 VC0 VSS SRP SRN DSG CHG LD LPWR CBI OCDP TS VTB CCFG CBO PRES CTRC CTRD".split())])
ic("TPS70933DBV", [(1, "IN"), (2, "GND"), (3, "EN"), (4, "NC"), (5, "OUT")])
ic("TPS62933DRL", [(1, "RT"), (2, "EN"), (3, "VIN"), (4, "GND"), (5, "SW"), (6, "BST"), (7, "SS"), (8, "FB")])
ic("USB_C_Port", [("VBUS", "VBUS"), ("CC1", "CC1"), ("CC2", "CC2"), ("D+", "D+"), ("D-", "D-"), ("GND", "GND")])
ic("EEPROM_I2C", [("1", "SCL"), ("2", "GND"), ("3", "SDA"), ("4", "VCC"), ("5", "WP")])
# ---------- placement ----------
body = []; netcheck = {}
TI = "https://www.ti.com/lit/ds/symlink/"
DS = {"U1": TI + "tps25751.pdf", "U2": TI + "bq25756.pdf", "U4": TI + "bq77915.pdf", "U5": TI + "tps709.pdf", "U6": TI + "tps62933.pdf",
      "D1": TI + "tvs2200.pdf", "U8": TI + "tps25810.pdf", "U7": "https://www.st.com/resource/en/datasheet/stm32wb1mmc.pdf", "J2": "https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/c12402082.pdf", "J1": "https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/c12402082.pdf"}
def place(sym, ref, val, x, y, nets, status=""):
    pins = PINPOS[sym]; isic = len(pins) > 3
    top = max(p[1] for p in pins.values())
    rx, ry = (x, y - (top + 6.35)) if isic else (x - 2.54, y - 1.27)
    vx, vy = (x, y - (top + 3.81)) if isic else (x - 2.54, y + 1.27)
    j = "" if isic else " (justify right)"
    if sym == "NFET": rx, ry, vx, vy, j = x + 3.81, y - 1.27, x + 3.81, y + 1.27, " (justify left)"
    s = (f'(symbol (lib_id "Monolith:{sym}") (at {x:.2f} {y:.2f} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")\n'
         f'(property "Reference" {q(ref)} (at {rx:.2f} {ry:.2f} 0) {F}{j}))\n(property "Value" {q(val)} (at {vx:.2f} {vy:.2f} 0) {F}{j}))\n'
         f'(property "Footprint" "" (at {x:.2f} {y:.2f} 0) {F} (hide yes)))\n(property "Datasheet" {q(DS.get(ref, ""))} (at {x:.2f} {y:.2f} 0) {F} (hide yes)))\n'
         f'(property "Status" {q(status)} (at {x:.2f} {y:.2f} 0) {F} (hide yes)))\n'
         + "".join(f'(pin {q(n)} (uuid "{U()}"))\n' for n in pins)
         + f'(instances (project "BatteryBank" (path "/{ROOT}" (reference {q(ref)}) (unit 1)))))')
    body.append(s)
    for num, (dx, dy, side) in pins.items():
        net = nets.get(num, ""); px, py = x + dx, y - dy
        if not net:
            body.append(f'(no_connect (at {px:.2f} {py:.2f}) (uuid "{U()}"))'); continue
        ang, just = (180, "right") if side == "L" else (0, "left")
        body.append(f'(label {q(net)} (at {px:.2f} {py:.2f} {ang}) {F} (justify {just} bottom)) (uuid "{U()}"))')
        netcheck.setdefault(net, []).append(f"{ref}.{num}")
def text(t, x, y, size=2.0):
    body.append(f'(text {q(t)} (exclude_from_sim no) (at {x} {y} 0) (effects (font (size {size} {size})) (justify left bottom)) (uuid "{U()}"))')
text("Monolith top board: all blocks. DRAFT 3, generated from the TI pin tables.", 25.4, 20.32, 3)
text("Connections are made by net labels at each pin. Parts marked TBD are not final. Port 1 ESD protection is not drawn yet.", 25.4, 27.94)
p = {x[0]: x for x in gen.parts}
place("TPS25751D", "U1", "TPS25751D", 127, 101.6, {str(a): c for a, b, c in p["U1"][5]}, "pinout from TI datasheet")
place("BQ25756", "U2", "BQ25756", 279.4, 101.6, {str(a): c for a, b, c in p["U2"][5]}, "pinout from TI datasheet")
place("USB_C_Port", "J1", "12402082E512A", 43.18, 58.42, {"VBUS": "VBUS1", "CC1": "P1_CC1", "CC2": "P1_CC2", "D+": "P1_DP", "D-": "P1_DN", "GND": "GND"}, "pin numbers pending Amphenol drawing")
place("EEPROM_I2C", "U3", "24C-series EEPROM (TBD)", 43.18, 101.6, {"1": "CHG_SCL", "2": "GND", "3": "CHG_SDA", "4": "PD_3V3", "5": "GND"}, "size, address and pinout to confirm")
text("Power stage", 381, 45.72)
for i, (ref, d, g, s, role) in enumerate([("Q1", "AC_SNS_N", "HG1", "SW1", "buck high"), ("Q2", "SW1", "LG1", "GND", "buck low"), ("Q4", "BAT_SNS_P", "HG2", "SW2", "boost high"), ("Q3", "SW2", "LG2", "GND", "boost low")]):
    place("NFET", ref, "40V N-FET TBD, " + role, 393.7 + (i // 2) * 60.96, 63.5 + (i % 2) * 30.48, {"D": d, "G": g, "S": s}, "part to be selected")
text("Cell protector", 96.52, 149.86)
prot = dict(zip(range(1, 25), ["PROT_VDD", "PROT_AVDD", "PROT_VC4", "PROT_VC4", "PROT_VC3", "PROT_VC2", "PROT_VC1", "PROT_VC0", "BAT_NEG", "BAT_NEG", "PROT_SNS",
    "PROT_DSG", "PROT_CHG", "PROT_LD", "", "BAT_NEG", "PROT_OCDP", "PROT_TS", "PROT_VTB", "PROT_AVDD", "", "PROT_PRES", "BAT_NEG", "BAT_NEG"]))
place("BQ77915", "U4", "BQ7791501", 127, 175.26, {str(k): v for k, v in prot.items()}, "pinout from TI datasheet; 4S strapping to confirm")
text("3.3V and 5V rails", 248.92, 149.86)
place("TPS70933DBV", "U5", "TPS70933DBV", 279.4, 162.56, {"1": "VBAT_SYS", "2": "GND", "3": "", "4": "", "5": "3V3"}, "pinout from TI datasheet")
place("TPS62933DRL", "U6", "TPS62933", 279.4, 187.96, {"1": "GND", "2": "", "3": "VBAT_SYS", "4": "GND", "5": "BUCK_SW", "6": "BUCK_BST", "7": "BUCK_SS", "8": "BUCK_FB"}, "pinout from TI datasheet")
text("Protection FETs (low side)", 381, 149.86)
place("NFET", "Q5", "30V N-FET TBD, discharge", 393.7, 167.64, {"D": "PROT_MID", "G": "PROT_DSG_G", "S": "PROT_SNS"}, "part to be selected")
place("NFET", "Q6", "30V N-FET TBD, charge", 454.66, 167.64, {"D": "PROT_MID", "G": "PROT_CHG_G", "S": "GND"}, "part to be selected")
text("Battery wire pads", 485.14, 182.88)
for i, (ref, net) in enumerate([("W1", "BAT_POS"), ("W2", "CELL3"), ("W3", "CELL2"), ("W4", "CELL1"), ("W5", "BAT_NEG")]):
    place("PAD", ref, "wire pad", 495.3, 190.5 + i * 7.62, {"1": net}, "")
text("Bluetooth MCU (integrated antenna: ANT_IN tied to ANT_OUT)", 518.16, 40.64)
wb = {6: "ANT_LOOP", 7: "ANT_LOOP", 9: "VBAT_SENSE", 10: "LED1", 11: "CHG_STAT1", 12: "LED2", 13: "CHG_STAT2", 14: "LED3", 16: "3V3", 18: "3V3", 20: "3V3", 22: "MCU_BOOT0", 23: "MCU_NRST",
      25: "HOST_SDA", 26: "HOST_IRQ", 27: "HOST_SCL", 28: "CHG_PG", 29: "LED4", 30: "P2_FAULT", 32: "P2_ATTACH", 33: "", 34: "SWCLK", 35: "SWDIO", 36: "DBG_RX", 37: "", 38: "DBG_TX",
      39: "", 40: "", 41: "", 42: ""}
wb.update({k: "GND" for k in GNDP})
place("STM32WB1MMC", "U7", "STM32WB1MMC", 546.1, 101.6, {str(k): v for k, v in wb.items()}, "pad table from ST datasheet; pin functions to confirm in CubeMX")
text("Debug pads", 624.84, 45.72)
for i, (ref, net) in enumerate([("W6", "SWDIO"), ("W7", "SWCLK"), ("W8", "MCU_NRST"), ("W9", "3V3"), ("W10", "GND"), ("W11", "DBG_TX"), ("W12", "DBG_RX")]):
    place("PAD", ref, "test pad", 635, 55.88 + i * 7.62, {"1": net}, "")
text("Port 2: 5V 3A, standalone", 25.4, 205.74)
place("USB_C_Port", "J2", "12402082E512A", 43.18, 223.52, {"VBUS": "VBUS2", "CC1": "P2_CC1", "CC2": "P2_CC2", "D+": "P2_DCP", "D-": "P2_DCP", "GND": "GND"}, "pin numbers pending Amphenol drawing")
p2 = {1: "P2_FAULT", 2: "5V", 3: "5V", 4: "5V", 5: "5V", 6: "5V", 7: "5V", 8: "5V", 9: "P2_REF_RTN", 10: "P2_REF", 11: "P2_CC1", 12: "GND", 13: "P2_CC2", 14: "VBUS2", 15: "VBUS2",
      16: "", 17: "", 18: "", 19: "P2_ATTACH", 20: "", "EP": "GND"}
place("TPS25810", "U8", "TPS25810", 127, 226.06, {str(k): v for k, v in p2.items()}, "pinout from TI datasheet; REF and REF_RTN order to confirm")
T = "TBD"
two_pin = [("L","L1","4.7uH 12A TBD","SW1","SW2"),("R","R1","5m 1%","PPHV","AC_SNS_N"),("R","R2","5m 1%","BAT_SNS_P","VBAT_SYS"),
 ("C","C1","100n","BTST1","SW1"),("C","C2","100n","BTST2","SW2"),("C","C3","4.7u","REGN","GND"),("C","C4","4.7u","REGN","GND"),
 ("C","C5","1u 35V","CHG_VAC","GND"),("R","R3","10R","PPHV","CHG_VAC")]
two_pin += [("C",f"C{n}","22u 35V","AC_SNS_N","GND") for n in range(6,10)] + [("C","C10","68u 25V poly","PPHV","GND")]
two_pin += [("C",f"C{n}","22u 25V","BAT_SNS_P","GND") for n in range(11,15)] + [("C","C15","68u 25V poly","VBAT_SYS","GND")]
two_pin += [("R","R4","243k 0.1%","VBAT_SYS","CHG_FB"),("R","R5","24.9k 0.1%","CHG_FB","CHG_FBG"),("R","R6","16.9k","CHG_ICHG","GND"),
 ("R","R7","4.02k","CHG_ILIM","GND"),("R","R8","66.5k","CHG_FSW","GND"),("R","R9","5.23k","REGN","CHG_TS"),("R","R10","30.1k","CHG_TS","GND"),
 ("NTC","RT1","10k 103AT","CHG_TS","GND"),("R","R11",T,"CHG_VAC","CHG_ACOV"),("R","R12",T,"CHG_ACOV","CHG_ACUV"),("R","R13",T,"CHG_ACUV","GND"),
 ("R","R14","10k","CHG_CE_N","GND"),("R","R15","10k","PD_3V3","CHG_INT"),("R","R16","3.3k","PD_3V3","CHG_SDA"),("R","R17","3.3k","PD_3V3","CHG_SCL"),
 ("R","R18","4.7k","3V3","HOST_SDA"),("R","R19","4.7k","3V3","HOST_SCL"),("R","R20","10k","3V3","HOST_IRQ"),
 ("R","R21","100k","3V3","CHG_STAT1"),("R","R22","100k","3V3","CHG_STAT2"),("R","R23","100k","3V3","CHG_PG"),
 ("C","C16","10u","PD_3V3","GND"),("C","C17","10u","PD_1V5","GND"),("C","C18","10u","3V3","GND"),("C","C19","4.7u 35V","VBUS1","GND"),
 ("C","C20","22u","5V","GND"),("C","C21","330p","P1_CC1","GND"),("C","C22","330p","P1_CC2","GND"),
 ("R","R24",T,"PD_3V3","ADCIN1"),("R","R25",T,"ADCIN1","GND"),("R","R26",T,"PD_3V3","ADCIN2"),("R","R27",T,"ADCIN2","GND"),("TVS","D1","TVS2200","VBUS1","GND")]
two_pin += [("FUSE","F1","15A","BAT_POS","VBAT_SYS"),("R","R30","33R","BAT_POS","PROT_VC4"),("R","R31","33R","CELL3","PROT_VC3"),("R","R32","33R","CELL2","PROT_VC2"),
 ("R","R33","33R","CELL1","PROT_VC1"),("R","R34","33R","BAT_NEG","PROT_VC0"),("C","C30","1u","PROT_VC4","PROT_VC3"),("C","C31","1u","PROT_VC3","PROT_VC2"),
 ("C","C32","1u","PROT_VC2","PROT_VC1"),("C","C33","1u","PROT_VC1","PROT_VC0"),("R","R35","1k","BAT_POS","PROT_VDD"),("C","C34","1u 35V","PROT_VDD","BAT_NEG"),
 ("C","C35","1u","PROT_AVDD","BAT_NEG"),("R","R36","3m 1% 1W","BAT_NEG","PROT_SNS"),("R","R37","4.53k","PROT_DSG","PROT_DSG_G"),("R","R38","1M","PROT_DSG_G","PROT_SNS"),
 ("R","R39","1k","PROT_CHG","PROT_CHG_G"),("R","R40","1M","PROT_CHG_G","GND"),("R","R41","470k","PROT_LD","GND"),("R","R42","196k","PROT_OCDP","BAT_NEG"),
 ("R","R43","10k 1%","PROT_VTB","PROT_TS"),("NTC","RT2","10k 103AT","PROT_TS","BAT_NEG"),("R","R44",T,"PROT_VDD","PROT_PRES"),
 ("C","C40","1u 35V","VBAT_SYS","GND"),("C","C41","2.2u","3V3","GND"),
 ("L","L2","3.3uH 5A","BUCK_SW","5V"),("C","C42","100n","BUCK_BST","BUCK_SW"),("C","C43","33n","BUCK_SS","GND"),("R","R45","53.6k","5V","BUCK_FB"),
 ("R","R46","10k","BUCK_FB","GND"),("C","C44","10p","5V","BUCK_FB"),("C","C45","10u 35V","VBAT_SYS","GND"),("C","C46","10u 35V","VBAT_SYS","GND"),
 ("C","C47","100n 35V","VBAT_SYS","GND"),("C","C48","22u 10V","5V","GND"),("C","C49","22u 10V","5V","GND")]
two_pin += [("R","R47","100k 1%","P2_REF","P2_REF_RTN"),("R","R48","100k","3V3","P2_ATTACH"),("R","R49","100k","3V3","P2_FAULT"),("C","C50","100n","5V","GND"),
 ("C","C51","10u 10V","VBUS2","GND"),("C","C52","100u 6.3V poly","5V","GND"),("TVS","D2","5V TVS TBD","VBUS2","GND"),
 ("R","R50","2M 1%","VBAT_SYS","VBAT_SENSE"),("R","R51","402k 1%","VBAT_SENSE","GND"),("C","C55","100n","VBAT_SENSE","GND"),
 ("C","C56","4.7u","3V3","GND"),("C","C57","100n","3V3","GND"),("C","C58","100n","MCU_NRST","GND"),("R","R52","10k","MCU_BOOT0","GND")]
for n in range(1, 5):
    two_pin += [("R", f"R{52 + n}", "1k", f"LED{n}", f"LED{n}_A"), ("LED", f"D{9 + n}", "green 0603", f"LED{n}_A", "GND")]
text("Passives (each pin is tied to the net named beside it)", 25.4, 254)
for i, (sym, ref, val, n1, n2) in enumerate(two_pin):
    place(sym, ref, val, 30.48 + (i % 20) * 35.56, 266.7 + (i // 20) * 22.86, {"1": n1, "2": n2}, "value to confirm" if val != T else "value to be set")
lib = "\n".join(LIB.values())
sch = (f'(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")\n(uuid "{ROOT}")\n(paper "A1")\n'
       f'(title_block (title "Monolith top board") (rev "draft 3"))\n(lib_symbols\n{lib}\n)\n' + "\n".join(body) +
       '\n(sheet_instances (path "/" (page "1")))\n)\n')
assert sch.count("(") == sch.count(")"), (sch.count("("), sch.count(")"))
open("/mnt/user-data/outputs/BatteryBank/BatteryBank.kicad_sch", "w", newline="\n").write(sch)
# compare against the CSV netlist source
ref_nets = {}
for ref, part, val, pkg, st, pins in gen.parts[:2]:
    for a, b, c in pins:
        if c: ref_nets.setdefault(c, []).append(f"{ref}.{a}")
single = sorted(k for k, v in netcheck.items() if len(v) < 2)
missing = [k for k in ref_nets if k not in netcheck]
import collections
syms = sum(1 for b in body if b.startswith("(symbol"))
print("symbols", syms, "labels", sum(len(v) for v in netcheck.values()), "nets", len(netcheck), "bytes", len(sch))
print("single-node nets:", single); print("IC nets missing:", missing)

import csv
with open("/mnt/user-data/outputs/BatteryBank/monolith_netlist.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["net", "connections", "pins"])
    for k in sorted(netcheck): w.writerow([k, len(netcheck[k]), " ".join(netcheck[k])])
