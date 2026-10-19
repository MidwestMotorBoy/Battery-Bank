"""One-shot (rev A8, part 2): schematic review 4's documentation and BOM items, A-2's procedure text, and D-5's
J104 clamp (docs/devboard/schematic-review-4-2026-10-14.md). Edits every sheet in place. Run once from DevBoard/,
after tools/review4_fixes.py:
    python tools/review4_docs.py
then tools/place_fields.py gauge.kicad_sch, ERC, and the board flow (reset_board.py, netlist_to_board.py, place_blocks.py).

    A-2   R312 / R301 Notes and MCU sheet note 10: EV2400 work only with 3V3 up (J104) and U301 in reset
    A-11, A-12, B-10, C-12, C-13, D-9   stale Notes, sheet notes, heading, sheet name, address text
    D-5   D105 SMAJ18A clamp on the J104 side of D104 (J104 moves 7.62 mm right to make room)
    D-8   revision log A7 + A8 entries; every title block to A8
    D-11  MPN on the fitted parts that had only an LCSC number; Sourcing for U301 and J301; J301 out of the CPL
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sch_edit as F  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def rd(name):
    return open(os.path.join(ROOT, name), encoding="utf-8").read()


def wr(name, s):
    open(os.path.join(ROOT, name), "w", encoding="utf-8", newline="\n").write(s)


def setp(s, ref, **kv):
    """Set properties on a symbol, adding (hidden) any that don't exist yet."""
    a, b = F.sym_span(s, ref)
    blk = s[a:b]
    at = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+) \d+\)", blk)
    x, y = float(at.group(1)), float(at.group(2))
    for k, v in kv.items():
        if f'(property "{k}"' in blk:
            blk = F.set_prop(blk, k, v)
        else:
            i = blk.index("\n\t\t(pin ") if "\n\t\t(pin " in blk else blk.index("\n\t\t(instances")
            blk = blk[:i] + F.prop(k, v, x, y, True) + blk[i:]
    return s[:a] + blk + s[b:]


def flag(s, ref, name, val):
    a, b = F.sym_span(s, ref)
    blk, n = re.subn(r"\(" + name + r" (yes|no)\)", f"({name} {val})", s[a:b], count=1)
    assert n == 1, (ref, name)
    return s[:a] + blk + s[b:]


def rev(s, r="A8"):
    s, n = re.subn(r'\(rev "[^"]*"\)', f'(rev "{r}")', s, count=1)
    assert n == 1
    return s


def rep(s, old, new):
    assert s.count(old) == 1, old[:80]
    return s.replace(old, new)


# ================================================================== mcu.kicad_sch
s = rd("mcu.kicad_sch")
s = setp(s, "R301", Notes="3V3 -> 3V3_MCU link (VDDS). Never remove it while 3V3 is up: the bus pull-ups would then drive "
                          "SCL/SDA of an unpowered U301 above its VDDS + 0.3 V abs max (review 4 A-2)")
s = setp(s, "R302", Notes="RSTN pull-up: SWRS349A fig. 9-1 R1 (100k), with C304 = C92 as the power-on reset")
s = setp(s, "R312", Notes="Feeds the SMBus/I2C pull-ups from 3V3. Keep it fitted: do EV2400 work with J104 powered "
                          "(3V3 up) and U301 held in reset (SW301 or J301 nRESET). Feeding TP308 with 3V3 down drives the "
                          "unpowered CC2340's SCL/SDA above its VDDS + 0.3 V abs max (review 4 A-2)")
s = setp(s, "R315", Notes="DNP spare IRQ_N pull-up (R314 is the one fitted)")
s = setp(s, "R319", Notes="Series resistor to J303: CHG_INH can be forced from the header without fighting DIO24")
s = setp(s, "R321", Notes="Z61 series element of the antenna pi match (TI LaunchPad: 0R). Retune on this board")
s = setp(s, "U301", Sourcing="TI.com (CC2340R5MODAN0MHAR), consigned to JLC for placement; JLC C55046847 had no stock "
                             "on 2026-10-14")
s = setp(s, "J301", Sourcing="Hand-fit, not JLC assembled. Samtec part to be replaced by an unkeyed 2x5 1.27 mm header "
                             "JLC stocks (silk shows pin 1 and the cable-key side)")
s = flag(s, "J301", "in_pos_files", "no")
s = rep(s, '(text "I2C1 + IRQ PULL-UPS"', '(text "I2C0 + IRQ PULL-UPS"')
s = rep(s, r"10. R312 feeds the SMBus pull-ups: remove it and supply TP308 for EV2400 work.",
        r"10. R312 feeds the SMBus pull-ups. EV2400 work only with 3V3 up (J104 powered) and U301 held in reset:\n"
        r"    an unpowered CC2340 can't take bus voltage (VDDS + 0.3 V max). Never feed TP308 with 3V3 down (review 4 A-2).")
s = rev(s)
wr("mcu.kicad_sch", s)
print("mcu.kicad_sch done")

# ================================================================== gauge.kicad_sch
s = rd("gauge.kicad_sch")
s = setp(s, "Q103", Notes="BTP_INT level shift onto the shared open-drain IRQ_N (inverts: IRQ_N low while BTP_INT is high). "
                          "AO3400A Vgs(th) 0.65-1.45 V against BTP_INT VOH >= 1.8 V at 10 uA (DS 7.12); JLC basic, same "
                          "part as Q104. Firmware: BTP_POL = 1 whenever BTP_EN = 1 (review 4 D-2)")
s = setp(s, "R117", Notes="Holds Q103 off when BTP_INT floats (BTP_INT VOH is at most about 3.5 V)")
s = setp(s, "TP107", Value="IRQ_N")
s = setp(s, "J102", Notes="Wired 10k B3435 NTC (Semitec 103AT-2 class, epoxy bead with insulated leads) taped to the side "
                          "of BT101, over its sleeve. The can is that cell's negative terminal (at VSS) and the TS pins are "
                          "rated 2.1 V: keep the sensor insulated. Gauge internal 18k pull-up; enable TS1 in data flash")
s = setp(s, "R127", Value="0R")
s = setp(s, "RS101", MPN="PA2512FKE7W0R001E", Notes="1 mOhm 1 % 2 W sense resistor (YAGEO)")
for r in ("BT101", "BT102", "BT103", "BT104"):
    s = setp(s, r, MPN="BH-21700-B1BJ001 (MYOUNG)")
s = setp(s, "D101", MPN="BAT54WS (R+O)")
for r in ("Q101", "Q102"):
    s = setp(s, r, MPN="AGM404AP1 (AGMSEMI)")
s = setp(s, "U101", MPN="BQ40Z50RSMR-R2")
s = rep(s, r"8. Q103 buffers BTP_INT (its high level has no maximum; PA6 takes 4 V unpowered): GAUGE_BTP is active low.",
        r"8. Q103 buffers BTP_INT onto the shared open-drain IRQ_N (CC2340 DIO11): IRQ_N is low while BTP_INT is high.\n"
        r"   Keep BTP disabled, or set BTP_POL = 1 with BTP_EN = 1, or IRQ_N is held low (review 4 D-2).")
s = rep(s, r"11. SW101 wakes the gauge from SHUTDOWN without USB; J104 feeds PACK_P from a current-limited bench supply.",
        r"11. SW101 wakes the gauge from SHUTDOWN without USB; J104 feeds PACK_P from a current-limited bench supply\n"
        r"    (12-16 V, limit <= 0.5 A). D105 clamps a mis-set supply before D104; it is a crowbar, not a regulator.")

# D-5: J104 moves 7.62 right; its two wires are redrawn; D105 drops from the J104-side wire to GND.
s = F.move_item(s, "symbol", None, 304.8, 58.42, 312.42, 58.42)                 # J104
s = F.drop(s, r"\n\t\(wire\n\t\t\(pts\n\t\t\t\(xy 293\.37 58\.42\) \(xy 299\.72 58\.42\)")
s = F.drop(s, r"\n\t\(wire\n\t\t\(pts\n\t\t\t\(xy 299\.72 60\.96\) \(xy 294\.64 60\.96\)")
s = F.move_item(s, "symbol", None, 294.64, 60.96, 302.26, 60.96)                # J104 pin 2 GND symbol
GAUGE = F.paths_of(s, "D104")[0][0]
pwr_n = max(int(m) for f in ("MonolithDev.kicad_sch", "gauge.kicad_sch", "power.kicad_sch", "mcu.kicad_sch",
                             "usb_port.kicad_sch")
            for m in re.findall(r'\(reference "#PWR(\d+)"\)', s if f == "gauge.kicad_sch" else rd(f))) + 1  # global
add = F.wire(293.37, 58.42, 307.34, 58.42) + F.wire(307.34, 60.96, 302.26, 60.96) + F.junction(297.18, 58.42)
add += F.clone(s, "#PWR130", [(GAUGE, f"#PWR{pwr_n}")], 297.18, 66.04, 0, [])
la = s.index("\n\t(lib_symbols")
lb = F.block_end(s, la + 2)
if '(symbol "Device:D_Zener"' not in s[la:lb]:                                  # (the gauge sheet has it: D103)
    dev = open(r"C:/Program Files/KiCad/10.0/share/kicad/symbols/Device.kicad_sym", encoding="utf-8").read()
    i = dev.index('(symbol "D_Zener"')
    z = dev[i:F.block_end(dev, i)].replace('(symbol "D_Zener"', '(symbol "Device:D_Zener"', 1)
    lib = s[la:lb]
    k = lib.rindex(")")
    s = s[:la] + lib[:k] + "\t" + z + "\n\t" + lib[k:] + s[lb:]
add += F.new_symbol("Device:D_Zener", [(GAUGE, "D105")], "SMAJ18A", 297.18, 62.23, ["1", "2"],
                    [("Footprint", "Diode_SMD:D_SMA"),
                     ("Datasheet", "https://www.littelfuse.com/assetdocs/littelfuse-tvs-diode-smaj-datasheet"),
                     ("Description", "18 V standoff unidirectional TVS, SMA"), ("LCSC", "C148219"),
                     ("MPN", "SMAJ18A (Littelfuse)"),
                     ("Notes", "J104 overvoltage clamp (review 4 D-5): 18 V standoff, 20-22.1 V breakdown, so a bench "
                               "supply left above about 22 V is clamped before it reaches the 25 V parts on PACK_P. On "
                               "the header side of D104, so it draws nothing from the pack. Sacrificial: keep the bench "
                               "current limit low. Cathode (pin 1) to the J104 line")], rot=270)
s = F.insert_items(s, add)
s = rev(s)
wr("gauge.kicad_sch", s)
print("gauge.kicad_sch done (D105 added, J104 moved)")

# ================================================================== power.kicad_sch
s = rd("power.kicad_sch")
s = setp(s, "U204", MPN="TPS62177DQCR")
s = rep(s, r"6. SLEEP low = sleep mode (internal pull-down); MCU PB4 drives it high for full load.",
        r"6. SLEEP low = sleep mode (internal 1.4 uA pull-down); CC2340 DIO21 (3V3_SLEEP) drives it, and R313 220k\n"
        r"   holds it high while U301 is in reset or unprogrammed.")
s = rep(s, r"8. U201/U202 are hand-soldered (DigiKey/Mouser); JLC has no stock. Not in the JLC BOM/CPL.",
        r"8. U201 is hand-soldered (DigiKey/Mouser; not in the JLC BOM/CPL). U202 (INA190A1) is JLC-placed.")
s = rep(s, r"10. U203 EN is left open (internal 300 nA pull-up enables it). EN must stay below 6.5 V: never tie it to LDO_IN.",
        r"10. U203 (HT7550-1) has no EN pin: it runs whenever JP202 feeds it (30 V operating, 33 V abs max).")
s = rev(s)
wr("power.kicad_sch", s)
print("power.kicad_sch done")

# ================================================================== usb_port.kicad_sch (shared by both ports)
s = rd("usb_port.kicad_sch")
s = setp(s, "R417", Notes="CE pull-up to 3V3: charging is inhibited unless the MCU drives CHG_INH (DIO24) low. Reset, "
                          "WDT reset, ROM bootloader or an unprogrammed MCU all inhibit (pins float). CC2340 Standby "
                          "keeps the GPIO state, so a low CHG_INH keeps charging in Standby. With 3V3 down (dead pack) CE "
                          "reads low, so USB can still revive the pack. MCU low through R435/R535: CE = 3.3 x 1k/48k = "
                          "0.07 V (VIL max 0.4 V)")
s = setp(s, "R435", Notes="CHG_INH from the MCU (DIO24): low allows charging; high or hi-Z (reset, WDT reset, ROM "
                          "bootloader, unprogrammed) stops it at the CE pin via the R417/R517 pull-up, independent of the "
                          "TPS25751. Keep DIS_CE_PIN = 0")
s = setp(s, "R441", Notes="TPD4S201 FLT pull-up (open drain; 1.7-300 kOhm to 2.7-5.5 V). FLT -> GPIO3 = "
                          "Fault_Input_Event (33): CC or SBU OVP (and an ESD-triggered OVP) forces Type-C error recovery, "
                          "as on TI's TPS25751EVM")
s = setp(s, "C451", Notes="TPD4S201 VBIAS (ESD support), 0.1 uF 50 V X7R. The part's own clamps hold VBIAS to about 28 V "
                          "(-Q1 6.3.1); the >= 63 V footnote is about capacitance loss, and 50 V X7R keeps more than the "
                          "0.04 uF effective minimum. TI's EVM uses 50 V (review 4 C-1/C-13)")
for r in ("C431", "C434", "C435"):
    s = setp(s, r, Notes="Battery-side ripple MLCC (C431/C434/C435 and C531/C534/C535; cost-down 2026-10-14, was 47 uF "
                         "1210): the 100 uF polymer C432/C532 carries the bulk, bank about 114 uF effective (>= 80). The "
                         "worst battery-side ripple is about 1.5 A rms (reverse buck to 9 V 3 A); check their temperature "
                         "at bring-up")
GATE = "0R; raise to a few ohms (<= 4.7 Ohm; above that add a turn-off diode, or turn-off eats the 45 ns dead time) to slow the edges"
s = setp(s, "R444", Notes=f"HIDRV1 -> Q401/Q501 high-side gate (EVM R8). {GATE}")
s = setp(s, "R445", Notes=f"LODRV1 -> Q407/Q507 low-side gate (EVM R20). {GATE}")
s = setp(s, "R446", Notes=f"HIDRV2 -> Q402/Q502 high-side gate (EVM R3). {GATE}")
s = setp(s, "R447", Notes=f"LODRV2 -> Q408/Q508 low-side gate (EVM R17). {GATE}")
s = setp(s, "R448", Notes="BTST1 pin -> C412/D404 (C512/D504) (EVM R13). 0R; raise to a few ohms to slow the switching edges")
s = setp(s, "R449", Notes="BTST2 pin -> C413/D405 (C513/D505) (EVM R23). 0R; raise to a few ohms to slow the switching edges")
s = setp(s, "L401", Notes="Cost-down 2026-10-14 (was Coilcraft XAL7030-222): 2.2 uH, DCR 9 mOhm max; Isat 18 A and Irms "
                          "12 A are typical values (L -17 % at 15 A, soft saturation; about 30-33 C rise at 12 A). Review 2 "
                          "B-7 worst-case peak 15.4 A. 11.5 x 10 x 4 mm, FXL1040 footprint. Check its temperature at bring-up")
s = setp(s, "L402", Notes="Cost-down 2026-10-14 (was SRP5030T-3R3M): 3.3 uH, 38 mOhm max, Irms 5 A, Isat 8 A defined at a "
                          "40 % drop (not like-for-like with the SRP5030T); fine, as the 5.8 A IHS limit is a fault-only peak")
s = setp(s, "C403", MPN="CL21A106KAYNNNE")
s = setp(s, "C404", MPN="CL21A106KAYNNNE")
s = setp(s, "C405", MPN="CL10A106KP8NNNC")
s = setp(s, "R418", MPN="RT0805BRD07100KL")
s = setp(s, "R419", MPN="RT0805BRD0710KL")
s = setp(s, "R434", MPN="RT0805BRD0720KL")
s = setp(s, "U401", MPN="TPS25751DREFR")
s = setp(s, "U402", MPN="M24512-DFMC6TG")
s = setp(s, "U403", MPN="BQ25756RRVR")
s = setp(s, "U404", MPN="TPS62933DRLR")
s = rep(s, r"11. CHG_INH (rev A5): R417 pulls CE up to 3V3, so charging needs the MCU to drive CHG_INH low through R435.\n"
           r"    Reset, IWDG reset, a hang or an unprogrammed MCU stop charging; a dead pack (3V3 down) still charges.",
        r"11. CHG_INH (rev A5): R417 pulls CE up to 3V3, so charging needs the MCU (DIO24) to drive CHG_INH low through R435.\n"
        r"    Reset, WDT reset, the ROM bootloader or an unprogrammed MCU stop charging; CC2340 Standby keeps the pin state.\n"
        r"    A dead pack (3V3 down) still charges.")
s = rev(s)
wr("usb_port.kicad_sch", s)
print("usb_port.kicad_sch done")

# ================================================================== MonolithDev.kicad_sch
s = rd("MonolithDev.kicad_sch")
s = rep(s, '(property "Sheetname" "MCU and NTCs"', '(property "Sheetname" "MCU and Sensors"')
s = rep(s, r"4.  MCU and NTCs:  CC2340R5MODA", r"4.  MCU and Sensors:  CC2340R5MODA")
s = rep(s, r"Gauge BQ40Z50-R2 = 0x0B on the same SDA/SCL bus (STM32WB I2C1, 100 kHz)",
        r"Same SDA/SCL bus (CC2340 I2C0, 100 kHz): gauge BQ40Z50-R2 0x0B, TMP1075 U302-U306 0x48-0x4C")
s = rep(s, r"                Author: Logan (hand review) + Claude Code.",
        r"                Author: Logan (hand review) + Claude Code.\n"
        r"A7  2026-10-14  U301 STM32WB1MMC -> CC2340R5MODA with RF match C313-C315/R321; TMP1075 U302-U306 (U305/U306 DNP)\n"
        r"                replace TH301-TH305, NTC_EN and their dividers; IRQ1/IRQ2/GAUGE_BTP -> one open-drain IRQ_N\n"
        r"                (R314 pull-up, R315/R114 DNP); R313 fitted; TMP1075 footprint with 0.3 mm vias.  Author: Claude Code.\n"
        r"A8  2026-10-14  Review 4 (docs/devboard/schematic-review-4-2026-10-14.md): R313 220k, R314 47k, R304/R305 3.3k,\n"
        r"                R322-R324 series resistors at J302/J303, C401/C402 220p, D401/D501 TVS2200, snubber R 1206,\n"
        r"                TP415-TP421 probe pads, D105 J104 clamp; Notes, sheet text and MPNs updated; sheet 4 renamed\n"
        r"                MCU and Sensors.  Author: Claude Code.  Reviewer: 4-agent review + Logan.")
s = rev(s)
wr("MonolithDev.kicad_sch", s)
print("MonolithDev.kicad_sch done")
