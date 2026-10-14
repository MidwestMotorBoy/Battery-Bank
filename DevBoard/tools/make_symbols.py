"""Generate MonolithDev.kicad_sym: symbols for dev board parts that KiCad doesn't ship.

Pin numbers checked against the datasheets in ../../datasheets (2026-10-11).
Run: python make_symbols.py  (writes ../MonolithDev.kicad_sym)
"""
import os

G = 2.54
F = '(effects (font (size 1.27 1.27)))'
FH = '(effects (font (size 1.27 1.27)) (hide yes))'


def q(s):
    return '"' + str(s) + '"'


def prop(name, val, x=0.0, y=0.0, hide=False):
    return f'    (property {q(name)} {q(val)} (at {x:.2f} {y:.2f} 0) {FH if hide else F})'


def pin_s(num, name, x, y, ang, etype="passive", hide=False, ln=G):
    h = " (hide yes)" if hide else ""
    return (f'      (pin {etype} line (at {x:.2f} {y:.2f} {ang}) (length {ln}){h}\n'
            f'        (name {q(name)} {F}) (number {q(num)} {F}))')


def symbol(name, ref, left, right, fp="", ds="", desc="", width=15.24, top=None, bottom=None):
    """left/right: lists of (num, name, type) or None for a gap. Stacked pins: num may be a list."""
    top = top or []
    bottom = bottom or []
    n = max(len(left), len(right), 1)
    h2 = (n - 1) * G / 2
    W = width / 2
    H = h2 + G
    if top or bottom:
        H = max(H, h2 + G)
    pins = []

    def add(entries, side):
        for i, e in enumerate(entries):
            if e is None:
                continue
            nums, nm, et = e
            nums = nums if isinstance(nums, list) else [nums]
            y = round(h2 - i * G, 2)
            x, a = (-W - G, 0) if side == "L" else (W + G, 180)
            for k, nn in enumerate(nums):
                pins.append(pin_s(nn, nm, x, y, a, et if (k == 0 or et != PI) else "passive", hide=k > 0))

    add(left, "L")
    add(right, "R")
    for side, entries in (("T", top), ("B", bottom)):
        m = len(entries)
        for i, e in enumerate(entries):
            nums, nm, et = e
            nums = nums if isinstance(nums, list) else [nums]
            x = round((i - (m - 1) / 2) * G * 2, 2)
            y, a = (H + G, 270) if side == "T" else (-H - G, 90)
            for k, nn in enumerate(nums):
                pins.append(pin_s(nn, nm, x, y, a, et if (k == 0 or et != PI) else "passive", hide=k > 0))
    body = (f'      (rectangle (start {-W:.2f} {H:.2f}) (end {W:.2f} {-H:.2f}) '
            f'(stroke (width 0.254) (type default)) (fill (type background)))')
    return (f'  (symbol {q(name)} (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            + prop("Reference", ref, -W, H + 1.27) + "\n"
            + prop("Value", name, -W, -H - 1.27) + "\n"
            + prop("Footprint", fp, hide=True) + "\n"
            + prop("Datasheet", ds, hide=True) + "\n"
            + prop("Description", desc, hide=True) + "\n"
            + f'    (symbol "{name}_0_1"\n{body})\n'
            + f'    (symbol "{name}_1_1"\n' + "\n".join(pins) + "))")


P, PI, PO, I, O, B, OC, NC = "passive", "power_in", "power_out", "input", "output", "bidirectional", "open_collector", "no_connect"
TI = "https://www.ti.com/lit/ds/symlink/"
syms = []

# BQ40Z50-R2, RSM VQFN-32 4x4, EP = 33 (VSS). Datasheet table 6-1.
syms.append(symbol("BQ40Z50-R2", "U",
    left=[(32, "BAT", PI), (26, "VCC", PI), (1, "PBI", P), (24, "PTCEN", I), None,
          (2, "VC4", I), (3, "VC3", I), (4, "VC2", I), (5, "VC1", I), None,
          (8, "SRP", I), (6, "SRN", I), None, (27, "PACK", I), None,
          (10, "TS1", I), (11, "TS2", I), (12, "TS3", I), (13, "TS4", I), (23, "PTC", I)],
    right=[(31, "CHG", O), (28, "DSG", O), (30, "PCHG", O), (25, "FUSE", P), None,
           (19, "SMBC", B), (18, "SMBD", B), (15, "BTP_INT", O), (16, "PRES/SHUTDN", I), (17, "DISP", I), None,
           (20, "LEDCNTLA", P), (21, "LEDCNTLB", P), (22, "LEDCNTLC", P), None,
           ([7, 14, 29], "NC", NC), None, None, None, ([9, 33], "VSS", PI)],
    fp="Package_DFN_QFN:VQFN-32-1EP_4x4mm_P0.4mm_EP2.8x2.8mm",
    ds=TI + "bq40z50-r2.pdf", desc="1-4S Impedance Track gas gauge and protector", width=20.32))

# BQ25756, RRV VQFN-36 5x6, EP = 37 (PGND). Pins per docs/monolith_port1_netlist.csv (checked vs TI datasheet).
syms.append(symbol("BQ25756", "U",
    left=[([32, 33], "VAC", PI), (30, "ACP", I), (29, "ACN", I), (34, "ACUV", I), (35, "ACOV", I), None,
          (1, "SCL", I), (2, "SDA", B), (3, "~{INT}", OC), (4, "~{STAT1}", OC), (5, "~{STAT2}", OC), (6, "~{PG}", OC), (7, "~{CE}", I), None,
          (36, "FSW_SYNC", I), (9, "ICHG", P), (10, "ILIM_HIZ", P), (8, "TS", I)],
    right=[(27, "HIDRV1", O), (26, "BTST1", P), (28, "SW1", P), (25, "LODRV1", O), None,
           (19, "HIDRV2", O), (20, "BTST2", P), (18, "SW2", P), (21, "LODRV2", O), None,
           (14, "SRP", I), (13, "SRN", I), (12, "FB", I), (11, "FBG", P), None,
           (24, "REGN", PO), (23, "DRV_SUP", PI), ([15, 16, 31], "NC", NC), ([17, 22, 37], "PGND", PI)],
    fp="",
    ds=TI + "bq25756.pdf", desc="Bidirectional 4-switch buck-boost charge controller", width=20.32))

# INA190A5IDDFR, DDF SOT-23-8. Datasheet section 5.
syms.append(symbol("INA190A5_DDF", "U",
    left=[(7, "IN+", I), (8, "IN-", I), None, (2, "ENABLE", I), (3, "REF", I)],
    right=[(1, "VS", PI), None, (5, "OUT", O), (6, "NC", NC), (4, "GND", PI)],
    fp="Package_TO_SOT_SMD:TSOT-23-8", ds=TI + "ina190.pdf",
    desc="INA190A5 current-sense amplifier, gain 500, DDF package", width=12.7))

# TPS70950DBVR, SOT-23-5. Datasheet table 5-1 (TPS709 DBV: IN 1, GND 2, EN 3, NC 4, OUT 5).
syms.append(symbol("TPS70950DBV", "U",
    left=[(1, "IN", PI), (3, "EN", I)], right=[(5, "OUT", PO), (4, "NC", NC)], bottom=[(2, "GND", PI)],
    fp="Package_TO_SOT_SMD:SOT-23-5", ds=TI + "tps709.pdf", desc="5.0 V 150 mA 1 uA Iq LDO", width=12.7))

# ESD2CAN24DBZRQ1, SOT-23: IO 1, 2; GND 3.
syms.append(symbol("ESD2CAN24", "D",
    left=[(1, "IO1", P), (2, "IO2", P)], right=[(3, "GND", P), None],
    fp="Package_TO_SOT_SMD:SOT-23", ds=TI + "esd2can24-q1.pdf", desc="2-ch 24 V bidirectional ESD diode", width=10.16))

# Infineon IAUC45N04S6L063H half-bridge, PG-TDSON-8-57: 1 G (high side), 2/3 phase, 4 G (low side), 5/6 ground, 7/8 battery.
syms.append(symbol("IAUC45N04S6L063H", "Q",
    left=[(1, "G_HS", I), None, (4, "G_LS", I)],
    right=[([7, 8], "D_HS", P), ([2, 3], "PHASE", P), ([5, 6], "S_LS", P)],
    fp="", ds="https://www.infineon.com/dgdl/Infineon-IAUC45N04S6L063H-DataSheet-v01_00-EN.pdf",
    desc="40 V 6.3 mOhm N-channel half-bridge (high side D = pins 7,8; low side S = pins 5,6)", width=12.7))

# AGM404AP1 single N-FET, PDFN3.3x3.3: S 1-3, G 4, D 5-8.
syms.append(symbol("AGM404AP1", "Q",
    left=[(4, "G", I)], right=[([5, 6, 7, 8], "D", P), ([1, 2, 3], "S", P)],
    fp="Package_TO_SOT_SMD:TDSON-8-1", ds="https://www.lcsc.com/datasheet/C41349455.pdf",
    desc="40 V 4.4 mOhm N-MOSFET, PDFN3.3x3.3", width=7.62))

# STM32WB1MMC module, 77 pads. DS14096 table 1.
gnd = [1, 2, 3, 4, 15, 17, 19, 24, 31] + list(range(43, 78))
syms.append(symbol("STM32WB1MMC", "U",
    left=[(20, "VDDSMPS", PI), (16, "VDDA", PI), (18, "VBAT", PI), None, (23, "NRST", B), (22, "BOOT0", I), None,
          (6, "ANT_IN", P), (7, "ANT_OUT", P), None,
          (35, "PA13/SWDIO", B), (34, "PA14/SWCLK", B), (38, "PA9/USART1_TX", B), (36, "PA10/USART1_RX", B), None,
          (27, "PB6/I2C1_SCL", B), (25, "PB7/I2C1_SDA", B), None, ([5, 8], "VSSRF", PI), (21, "VSSSMPS", PI), (gnd, "VSS", PI)],
    right=[(37, "PA0", B), (11, "PA1", B), (13, "PA2", B), (28, "PA3", B), (9, "PA4", B), (39, "PA5", B),
           (12, "PA6", B), (29, "PA7", B), (10, "PA8", B), (32, "PA11", B), (30, "PA12", B), None,
           (41, "PB0", B), (40, "PB1", B), (42, "PB2", B), (33, "PB4", B), (26, "PB5", B), (14, "PB8", B)],
    fp="", ds="https://www.st.com/resource/en/datasheet/stm32wb1mmc.pdf",
    desc="STM32WB15 Bluetooth LE module with integrated antenna", width=22.86))

# BQ294700DSGR, DSG WSON-8 2x2, EP = 9 (VSS). Datasheet SLUSB15K table 5-1. Cell inputs and right-side pins on a
# 7.62 mm pitch so the 1k / 0.1 uF filter ladder (fig. 8-1) lines up with them on the sheet.
syms.append(symbol("BQ294700", "U",
    left=[(2, "V4", I), None, None, (3, "V3", I), None, None, (4, "V2", I), None, None, (5, "V1", I)],
    right=[(1, "VDD", PI), None, None, ([6, 9], "VSS", PI), None, None, (7, "CD", P), None, None, (8, "OUT", O)],
    fp="Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm", ds=TI + "bq2947.pdf",
    desc="2-4S Li-ion second-level overvoltage protector, 4.35 V OVP, active-high CMOS output", width=12.7))

# TLC Electronic WSFB1514 three-terminal battery protector (self-control fuse, 4 cells): fuse 1-2 (two elements in
# series), heater from their midpoint to pin 3. Datasheet "WSFB Series" rev A/2, p.3 "Device Circuit".
syms.append(symbol("WSFB1514", "F",
    left=[(1, "1", P)], right=[(2, "2", P)], bottom=[(3, "HTR", P)],
    fp="MonolithDev:TLC_WSFB_4x3mm", ds="https://www.lcsc.com/datasheet/C42463217.pdf",
    desc="3-terminal self-control fuse, 4 cells: fuse 1-2, heater to pin 3 (blown by a FET to VSS)", width=7.62))

lib = "(kicad_symbol_lib (version 20241209) (generator \"make_symbols.py\") (generator_version \"1.0\")\n" + "\n".join(syms) + "\n)\n"
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "MonolithDev.kicad_sym")
with open(out, "w", newline="\n") as f:
    f.write(lib)
print("wrote", os.path.normpath(out), len(syms), "symbols")
