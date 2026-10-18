"""U405 TPD4S201 (CC + SBU protector) -> TPD2S300 (CC only) on production (2026-10-17).

Liquid detection is gone, so SBU needs no protector: the connector's SBU pins become no-connects. CC keeps
short-to-VBUS OVP (24 V DC tolerant) and IEC 61000-4-2 ESD: the TPS25751's own CC pins are 26 V abs max but only
+-1 kV HBM, and TI's TPS25751 EVM protects them externally. Datasheet: datasheets/tpd2s300.pdf (SLVSDL1).
Pins (YFF WCSP-9, 0.4 mm): A1 C_CC1, A2 VBIAS (0.1 uF >= 35 V to GND), A3 C_CC2, B1 CC1, B2 GND, B3 CC2, C1 FLT
(open drain), C2 VPWR (2.7-22 V), C3 VM (2.7-4.5 V = normal CC/PD/FRS mode). VPWR and VM go to LDO_3V3.
CON_CC 30-120 pF, the same as the TPD4S201, so C401/C402 (220 pF) stay inside the TPS25751's 480 pF CC limit.
"""
import siz240dt as _s

LIB_ID = "MonolithDev:TPD2S300"
FOOTPRINT = "MonolithDev:TI_YFF0009_DSBGA-9_P0.4mm"
LCSC, MPN, VALUE = "C2650411", "TPD2S300YFFR (TI)", "TPD2S300YFFR"
# (pin number, net label or "GND" for a power symbol) per pin; labels are the sheet's existing local nets
PIN_NETS = {"A1": "C_CC1", "A3": "C_CC2", "A2": "VBIAS", "B1": "CC1", "B3": "CC2", "C1": "SBU_FLT",
            "C2": "LDO_3V3", "C3": "LDO_3V3", "B2": "GND"}
PINS = [("bidirectional", -15.24, 3.81, 0, "C_CC1", "A1"), ("bidirectional", -15.24, 1.27, 0, "C_CC2", "A3"),
        ("passive", -15.24, -3.81, 0, "VBIAS", "A2"), ("bidirectional", 15.24, 3.81, 180, "CC1", "B1"),
        ("bidirectional", 15.24, 1.27, 180, "CC2", "B3"), ("open_collector", 15.24, -3.81, 180, "~{FLT}", "C1"),
        ("power_in", -2.54, 8.89, 270, "VPWR", "C2"), ("power_in", 2.54, 8.89, 270, "VM", "C3"),
        ("power_in", 0, -8.89, 90, "GND", "B2")]


def lib_symbol(name='"MonolithDev:TPD2S300"', short="TPD2S300"):
    body = ('\t\t\t(symbol "%s_0_1"\n\t\t\t\t(rectangle\n\t\t\t\t\t(start -12.7 6.35)\n\t\t\t\t\t(end 12.7 -6.35)\n'
            '\t\t\t\t\t(stroke\n\t\t\t\t\t\t(width 0.254)\n\t\t\t\t\t\t(type default)\n\t\t\t\t\t)\n\t\t\t\t\t(fill\n'
            '\t\t\t\t\t\t(type background)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)' % short)
    pins = "\n".join(_s._pin(k, x, y, a, n, num) for k, x, y, a, n, num in PINS)
    return "\n".join([
        "\t\t(symbol %s" % name,
        "\t\t\t(pin_names\n\t\t\t\t(offset 1.016)\n\t\t\t)",
        "\t\t\t(exclude_from_sim no)\n\t\t\t(in_bom yes)\n\t\t\t(on_board yes)\n\t\t\t(in_pos_files yes)",
        "\t\t\t(duplicate_pin_numbers_are_jumpers no)",
        _s._prop("Reference", "U", -12.7, 7.62, False),
        _s._prop("Value", "TPD2S300", -12.7, -7.62, False),
        _s._prop("Footprint", FOOTPRINT, 0, 0, True),
        _s._prop("Datasheet", "https://www.ti.com/lit/ds/symlink/tpd2s300.pdf", 0, 0, True),
        _s._prop("Description", "USB Type-C CC short-to-VBUS OVP + IEC ESD, 2 channels, WCSP-9", 0, 0, True),
        body,
        '\t\t\t(symbol "%s_1_1"\n%s\n\t\t\t)' % (short, pins),
        "\t\t\t(embedded_fonts no)",
        "\t\t)"])


def library_entry():
    txt = lib_symbol('"TPD2S300"')
    return "\n".join(ln[1:] if ln.startswith("\t") else ln for ln in txt.split("\n"))
