"""Drawing tidy for the production schematic (re-runnable; run right after make_production.py).

  * deletes leftovers of the link merges: a wire whose two ends carry only same-name labels, or only power
    symbols of the same net;
  * turns the gauge pogo pads to face away from their labels and shows the pack pad values;
  * deletes headings of removed blocks, renames the rest, rewrites the sheet notes, root index and revision log;
  * renames the sheets 'Sleep Current and 3V3' -> '3V3 Rail' and 'MCU and Sensors' -> 'MCU'.

Electrical content is unchanged: check_netlist.py must still pass afterwards.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_production import PROD, ROOT, cut, insert_top, prune, wire_text  # noqa: E402
from schlib import anchors, on_segment, sheet_pins, symbols, top_blocks, wires  # noqa: E402

BS = chr(92)
NL = BS + "n"  # a line break inside a KiCad text string


def T(*lines):
    return NL.join(lines)


# ---------------------------------------------------------------- texts: first line -> new text (None deletes it)
TEXTS = {
    ROOT: {
        "MONOLITH DEV BOARD - SHEET INDEX": T(
            "MONOLITH PRODUCTION BOARD - SHEET INDEX",
            "2.  Cells and Gauge:  welded 4S pack pads, BQ40Z50-R2 gauge, protection FETs, BQ294700 + F102 second-level protection, SMBus pogo pads",
            "3.  3V3 Rail:  TPS62177 always-on 3V3",
            "4.  MCU:  CC2340R5MODA, Tag-Connect TC2030-NL SWD pads",
            "5.  USB Port 1  /  6.  USB Port 2  (one sheet file):  TPS25751D + TPD4S201 + BQ25756 + TPS62933 per port",
            "Rails (power symbols): PACK_P, 3V3, GND, CELL_N (gauge VSS only)",
            "Spec and open items: Production/README.md.  Derived from the dev board rev A8 (DevBoard/, history in DevBoard/README.md)."),
        "REVISION LOG": T(
            "REVISION LOG",
            "P0  2026-10-17  Dev board rev A8 with the dev-only parts removed (Production/tools/make_production.py, tidy_production.py):",
            "                sleep-current section, bench supply, cell holders, headers, buttons, status LED, test points, DNP options",
            "                and 0R links. Added pack wire pads, gauge pogo pads, TC2030-NL SWD pads, factory test pads.",
            "                Author: Claude Code.  Reviewer: none yet.",
            "Dev board history (A0-A8): DevBoard/README.md and the DevBoard root sheet."),
        "TPS25751 ADDRESS / DEAD-BATTERY STRAPS": T(
            "TPS25751 ADDRESS / DEAD-BATTERY STRAPS (SafeMode)",
            "Port 1: ADCIN1 tied to its LDO_3V3, ADCIN2 to GND  -> I2C 0x20",
            "Port 2: ADCIN1 and ADCIN2 to GND                   -> I2C 0x21",
            "Same SDA/SCL bus (CC2340 I2C0, 100 kHz): gauge BQ40Z50-R2 0x0B"),
    },
    "gauge.kicad_sch": {
        "WAKE + BENCH SUPPLY": None,
        "HOST SMBus (gauge 0x0B) / EV2400": "GAUGE SMBus (0x0B) + POGO PADS",
        "TEST POINTS / POWER FLAGS": "FACTORY TEST PADS",
        "CELL STACK (4S)": "PACK WIRES  (welded 4S EVE INR21700-58E)",
        "Holders BT101-BT104 OR welded pack": T(
            "J108 PACK- and J112 PACK+: 16 AWG leads in 1.7 mm plated holes. J109-J111: cell tap wires.",
            "Connect with USB unplugged, in order: PACK-, CELL1, CELL2, CELL3, PACK+ (note 15)."),
        "NOTES": T(
            "NOTES",
            "1. CELL_N = gauge VSS (cell 1 negative). GND = system ground, on the far side of RS101.",
            "2. Kelvin-route SRP/SRN from the RS101 pads; R107/R108/C106 at the IC.",
            "3. VC taps are separate thin traces from the tap pads J109-J111 and from the J108/J112 pads;",
            "    VC4 from CELL_P_RAW (before F102) so fuse drop is not read as cell voltage.",
            "4. TS1-TS4: one wired 10k NTC per cell on J102, J105-J107, taped to the cell at mid-height; insulated sensors only",
            "    (cans 0-12.6 V above VSS, TS 2.1 V max). PTC, PTCEN, PRES, DISP tied to VSS per datasheet.",
            "5. VCC fed from FET common drain via R106 (TI R13). PACK sense via R113 10k (TI R15).",
            "6. BAT fed from CELL_P_RAW (cell top, before F102) via D101 + R105 (TI fig. 9-12).",
            "7. Diamonds are PWR_FLAGs (ERC only, no part): each sits where its rail is sourced through a passive part.",
            "8. Q103 buffers BTP_INT onto the shared open-drain IRQ_N (CC2340 DIO11): IRQ_N is low while BTP_INT is high.",
            "   Keep BTP disabled, or set BTP_POL = 1 with BTP_EN = 1, or IRQ_N is held low (review 4 D-2).",
            "9. D103 clamps Q102 VGS at 15 V in a hard short. The dev board's C109/D102 inrush options are not on P0.",
            "10. No wake button: the gauge leaves SHUTDOWN when PACK_P comes up, i.e. when USB is plugged in (TPS25751 dead-battery",
            "    sink + BQ25756 charging with 3V3 down, USB sheet note 11). Confirm on the dev board.",
            "11. TP110-TP112 = SMBus pogo pads (SMBC, SMBD, GND) for an EV2400 / BQStudio: golden image and calibration.",
            "    Only with 3V3 up and U301 held in reset (MCU sheet note 10).",
            "12. TP106 PACK_P and TP109 GND are factory test pads.",
            "13. ESD caps (TI): C110+C111 in series across the FET pair (fig. 9-2 C1/C2), C107+C108 across PACK+/PACK- (sec. 9.2.2.1.5).",
            "14. Second level (TI fig. 9-11): U102 BQ294700 (4.35 V/cell, CD 0.1u = 1-2 s) or the gauge FUSE pin turns Q104 on;",
            "    F102's heater then blows its fuse, permanently opening the cell top. F102 is also the pack's only overcurrent fuse.",
            "15. Connect the pack with USB unplugged, PACK- first, then the taps bottom-up, then PACK+: a floating tap can read",
            "    > 4.35 V, U102 trips after 1-2 s and F102 blows. Gauge data flash: COV Delay 1 s, Min Blow Fuse Voltage 10500 mV."),
    },
    "power.kicad_sch": {
        "SLEEP-CURRENT MEASUREMENT": None,
        "AMPLIFIER SUPPLY": None,
        "NOTES": T(
            "NOTES",
            "1. PACK_P -> TPS62177 -> 3V3 (MCU + both TPS25751). Gauge BAT is NOT on this rail (TI: gauge must stay powered",
            "   with the FETs off).",
            "2. SLEEP low = sleep mode (internal 1.4 uA pull-down); CC2340 DIO21 (3V3_SLEEP) drives it, and R313 220k",
            "   holds it high while U301 is in reset or unprogrammed.",
            "3. PG is not used.",
            "4. U204 pin 4 (NC) goes to GND, as TI recommends.",
            "5. Diamonds are PWR_FLAGs (ERC only, no part): each sits where its rail is sourced through a passive part.",
            "6. The dev board's sleep-current section (R201 R_MEAS, 2 x INA190, HT7550-1) is not on P0: PACK_LP is PACK_P.",
            "   Measure sleep current on the dev board."),
    },
    "mcu.kicad_sch": {
        "BRING-UP AIDS": "3V3_SLEEP PULL-UP",
        "STATUS LED": None,
        "DEBUG HEADERS": "SWD  (Tag-Connect TC2030-NL)",
        "TEST POINTS": "FACTORY TEST PAD",
        "NOTES": T(
            "NOTES",
            "1. U301 antenna end at a board edge, ground 10-20 mm each side; keep-out in the footprint (fig. 9-2).",
            "2. C301-C303 at the VDDS pads. R302 + C304 = power-on reset (SWRS349A fig. 9-1 R1/C92); no reset button.",
            "3. C313 = CA1. R321/C314/C315 = Z61/Z60/Z62 pi match (TI: 0R, DNP, 1 pF); retune on the board.",
            "4. No 32 kHz crystal: LFOSC calibrated against the 48 MHz crystal. DIO3/DIO4 are GPIOs.",
            "5. Pins: DIO6 SCL, DIO8 SDA, DIO24 CHG_INH, DIO3/4 EN_5V1/2, DIO21 3V3_SLEEP, DIO11 IRQ_N.",
            "   Spare (no-connect): DIO12, DIO18, DIO20, the dev board's LED and UART pins (docs/devboard/cc2340-pin-budget.md).",
            "6. IRQ_N = TPS25751 IRQ x2 + gauge BTP (Q103), all open-drain. One pull-up: R314 47k.",
            "   Firmware polls each source to find which.",
            "7. Diamonds are PWR_FLAGs (ERC only, no part) where a rail is sourced through a passive part.",
            "8. J301 = Tag-Connect TC2030-NL pads (no part fitted): XDS110 through a TC2030-CTX cable (10-pin Cortex to TC2030).",
            "   SWO (pin 6) not used. The debugger drives NRST. Bootloader: ROM bootloader on a blank part or the CCFG backdoor pin.",
            "9. R313 220k holds 3V3_SLEEP high in reset (pins float; TPS62177 pulls down 1.4 uA typ).",
            "   Costs 15 uA while driven low in S2. DIO21 is also the default ROM-bootloader pin:",
            "   disable or move that trigger in the CCFG before the first flash (review 4 A-1).",
            "10. R304/R305 SMBus pull-ups go to 3V3. Gauge pogo-pad work (TP110-TP112) only with 3V3 up and U301 held in reset",
            "    (NRST low through J301): an unpowered CC2340 can't take bus voltage (VDDS + 0.3 V max).",
            "11. DIO24 = CHG_INH: LOW allows charging. High or hi-Z stops both chargers",
            "    (R417/R517 pull CE up), so reset/hang/unprogrammed stops charging.",
            "12. Watchdog: CC2340 WDT runs in active, idle and standby and can't be stopped once enabled.",
            "    GPIOs latch in standby; IRQ_N wakes it on an edge (SWRS349A 8.6, 8.11).",
            "13. Temps: gauge DAStatus2 (cells, FETs); charger NTCs via TPS25751 'I2Cr' (BQ25756 REG0x37).",
            "14. TP301 3V3 is a factory test pad."),
    },
    "usb_port.kicad_sch": {
        "TEST POINTS / POWER FLAGS": "FACTORY TEST PAD",
        "GATE / BOOTSTRAP TUNING": "GATE RESISTORS + TURN-OFF DIODES",
        "BATTERY-SIDE BULK": "BATTERY-SIDE BULK: 2 x 22u MLCC + 100u hybrid polymer (87 uF effective, >= 80 uF)",
        "PP5V SUPPLY  TPS62933": "PP5V SUPPLY  TPS62933 (1.2 MHz, 5.16 V, 3 x 22u out)  - 5 V source + VCONN",
        "NOTES  (this sheet is used twice": T(
            "NOTES  (this sheet is used twice: USB Port 1 = 4xx, USB Port 2 = 5xx)",
            "1. Address straps are on the root sheet: port 1 ADCIN1 = LDO_3V3, ADCIN2 = GND (0x20);",
            "   port 2 ADCIN1 = ADCIN2 = GND (0x21). Both are SafeMode (TPS25751 table 8-6).",
            "2. Unused TPS25751 GPIOs (0, 1, 2, 11) tied to GND per datasheet (KiCad ERC flags this; expected).",
            "   Never configure them as outputs.",
            "3. CC and SBU are protected by U405 (TPD4S201, below); C401/C402 (220 pF) on the controller side.",
            "   D+ and D- are tied together at the connector (net DPDN_DCP: passive BC1.2 DCP); the TPS25751 does no BC1.2.",
            "   Liquid detection (TI fig. 9-8): GPIO4/5 read SBU1/2 through U405 (TPD4S201: CC and SBU OVP + ESD);",
            "   GPIO6 = liquid_pmos_control (LIQ_PU), GPIO7 = liquid_nmos_control (LIQ_PD) in the TPS25751 configuration.",
            "   U405 FLT -> GPIO3 = Fault_Input_Event (SBU_FLT, R441): an SBU short to VBUS forces error recovery.",
            "   R442/R443 hold the liquid-detect FETs off while GPIO6/7 are Hi-Z.",
            "   D401 = TVS2200 flat clamp on VBUS (28 V at 40 A 8/20 us; TI's pick for the TPS25751).",
            "4. Kelvin-route ACP/ACN from R424 and SRP/SRN from R427; filter parts at the IC.",
            "5. Two MLCCs of each bulk bank plus C430/C438 at the FETs; the bulk caps (C421 polymer, C432 hybrid polymer) and remaining MLCCs",
            "   one row back. Polymer carries the bulk (no DC-bias loss), MLCCs carry the switching-frequency ripple.",
            "   Battery side is 2 x 22u + hybrid (C435 removed: docs/devboard/cap-reduction-sims-2026-10-17.md, B2: 87 uF,",
            "   hybrid at 63 % of its ripple rating). Still on hold: C427 (USB side, polymer at 85 % in the worst reverse case).",
            "6. I2Cc pull-ups go to this TPS25751's own LDO_3V3 (TI guidance).",
            "7. The charger battery side is PACK_P directly; take SRN/FB from R427's pad, not from the pour.",
            "8. VAC is taken before R424 per TI typical application; DRV_SUP fed from REGN via R420.",
            "9. PPHV bulk (BQ25756 input bank) exceeds the 100 uF USB PD cSnkBulkPd: the TPS25751D sink switch soft-start limits",
            "   inrush (C x SS: about 125 uF effective x 0.47 V/ms max = 0.06 A at SS setting 0).",
            "   Set PPHV soft-start to setting 0 or 1 in the TPS25751 configuration.",
            "10. Diamonds are PWR_FLAGs (ERC only, no part): each sits where its rail is sourced through a passive part.",
            "11. CHG_INH: R417 pulls CE up to 3V3, so charging needs the MCU (DIO24) to drive CHG_INH low through R435.",
            "    Reset, WDT reset, the ROM bootloader or an unprogrammed MCU stop charging; CC2340 Standby keeps the pin state.",
            "    A dead pack (3V3 down) still charges. Keep DIS_CE_PIN = 0.",
            "12. Gate drive: R444-R447 10R at the FET gates with D406-D409 for fast turn-off. BTST is wired straight to its cap",
            "    and there are no snubbers (removed in P0 before any bring-up data: add them back if the dev board shows ringing).",
            "13. TP401 VBUS is a factory test pad.",
            "14. PP5V output: C441-C443 3 x 22u 1206 (about 33 uF effective) plus C407 10u at the PP5V pin. Each port's PP5V is",
            "    its own TPS62933, a dedicated supply: USB PD cSrcBulk (10 uF min) applies, not the 120 uF cSrcBulkShared the",
            "    TPS25751 table cites. Estimated 0.5 -> 3 A step undershoot about 190 mV (cap sims P3); measure it on the dev board."),
    },
}
MOVE_TEXT = {"usb_port.kicad_sch": {"Charger battery side joins PACK_P here": (459.74, 35.56)}}
SHEET_NAMES = {"Sleep Current and 3V3": "3V3 Rail", "MCU and Sensors": "MCU"}
COMMENT1 = {"gauge.kicad_sch": "Welded 4S pack pads, BQ40Z50-R2 gauge/protector, protection FETs",
            "power.kicad_sch": "TPS62177 3V3 always-on rail",
            "mcu.kicad_sch": "CC2340R5MODA, TC2030-NL SWD pads"}
SHOW_VALUE = ["J108", "J109", "J110", "J111", "J112", "TP110", "TP111", "TP112"]


def text_body(blk):
    i = blk.index('"') + 1
    j = i
    while blk[j] != '"':
        j += 2 if blk[j] == BS else 1
    return i, j


def edit_texts(s, sheet):
    reps = []
    for a, b in top_blocks(s, "text"):
        blk = s[a:b]
        i, j = text_body(blk)
        first = blk[i:j].split(NL)[0]
        for key, new in TEXTS.get(sheet, {}).items():
            if first.startswith(key) and not (key == "NOTES" and first != "NOTES"):
                if new is None:
                    reps.append((s.rfind("\n", 0, a), b, ""))
                else:
                    reps.append((a + i, a + j, new))
                break
        for key, (x, y) in MOVE_TEXT.get(sheet, {}).items():
            if first.startswith(key):
                m = re.search(r"\(at [-\d.]+ [-\d.]+", blk)
                reps.append((a + m.start(), a + m.end(), "(at %g %g" % (x, y)))
    for a, b, new in sorted(reps, reverse=True):  # back to front, so earlier offsets stay valid
        s = s[:a] + new + s[b:]
    return s


def merge_wires(s):
    """Join collinear wire pairs meeting at a bare point (two wire ends, nothing else there)."""
    n = 0
    while True:
        ws = wires(s)
        ends = {}
        for w in ws:
            for p in w["p"]:
                ends.setdefault(p, []).append(w)
        busy = {x["p"] for h in ("label", "global_label", "hierarchical_label", "junction", "no_connect") for x in anchors(s, h)}
        busy |= {p for y in symbols(s) for p in y["pins"].values()} | set(sheet_pins(s))
        for p, ww in ends.items():
            if len(ww) != 2 or p in busy or any(on_segment(p, w["p"]) for w in ws):
                continue
            a = [q for q in ww[0]["p"] if q != p][0]
            b = [q for q in ww[1]["p"] if q != p][0]
            if abs((p[0] - a[0]) * (b[1] - a[1]) - (p[1] - a[1]) * (b[0] - a[0])) > 1e-3:
                continue
            s = insert_top(cut(s, [(ww[0]["a"], ww[0]["b"]), (ww[1]["a"], ww[1]["b"])]), wire_text(a, b))
            n += 1
            break
        else:
            return s, n


def junk_wires(s):
    """Wires left from link merges: both ends carry only same-name labels, or only same-value power symbols."""
    ws = wires(s)
    ends = {}
    for w in ws:
        for p in w["p"]:
            ends[p] = ends.get(p, 0) + 1
    labels = {}
    for x in anchors(s, "label"):
        labels.setdefault(x["p"], []).append(x)
    syms = symbols(s)
    at_pin = {}
    for y in syms:
        val = re.search(r'\(property "Value" "([^"]*)"', s[y["a"]:y["b"]]).group(1)
        for p in y["pins"].values():
            at_pin.setdefault(p, []).append((y, val))
    spans = []
    for w in ws:
        p, q = w["p"]
        if ends[p] != 1 or ends[q] != 1:
            continue
        lp, lq = labels.get(p, []), labels.get(q, [])
        pp, pq = at_pin.get(p, []), at_pin.get(q, [])
        if len(lp) == len(lq) == 1 and not pp and not pq and lp[0]["name"] == lq[0]["name"]:
            spans += [(w["a"], w["b"]), (lp[0]["a"], lp[0]["b"]), (lq[0]["a"], lq[0]["b"])]
        elif (not lp and not lq and len(pp) == len(pq) == 1 and pp[0][0]["power"] and pq[0][0]["power"]
              and pp[0][1] == pq[0][1]):
            spans += [(w["a"], w["b"]), (pp[0][0]["a"], pp[0][0]["b"]), (pq[0][0]["a"], pq[0][0]["b"])]
    return cut(s, spans), len(spans) // 3


def set_field(blk, prop, x, y, hide, justify=None):
    m = re.search(r'\n\t\t\(property "%s" "[^"]*"\n' % prop, blk)
    a = m.start() + 3
    from schlib import block_end
    e = block_end(blk, a)
    p = blk[a:e]
    p = re.sub(r"\(at [-\d.]+ [-\d.]+ [-\d.]+\)", "(at %g %g 0)" % (x, y), p, count=1)
    p = p.replace("\n\t\t\t(hide yes)", "")
    if hide:
        p = p.replace("\n\t\t\t(show_name", "\n\t\t\t(hide yes)\n\t\t\t(show_name", 1)
    if justify and "(justify" not in p:
        p = p.replace("\n\t\t\t\t)\n\t\t\t)", "\n\t\t\t\t)\n\t\t\t\t(justify %s)\n\t\t\t)" % justify, 1)
    return blk[:a] + p + blk[e:]


def pads(s):
    out, last = [], 0
    for y in symbols(s):
        blk = s[y["a"]:y["b"]]
        x0, y0 = y["at"][:2]
        if y["ref"] in SHOW_VALUE:  # text right of the pad, clear of the wire label on its pin
            blk = set_field(blk, "Reference", x0 + 2.54, y0 - 5.08, False, "left")
            blk = set_field(blk, "Value", x0 + 2.54, y0 - 2.54, False, "left")
        out += [s[last:y["a"]], blk]
        last = y["b"]
    out.append(s[last:])
    return "".join(out)


def main():
    for sheet in [ROOT, "gauge.kicad_sch", "power.kicad_sch", "mcu.kicad_sch", "usb_port.kicad_sch"]:
        path = os.path.join(PROD, sheet)
        s = open(path, encoding="utf-8").read()
        s, nm = merge_wires(s)
        s, nj = junk_wires(s)
        s, npr = prune(s)
        s = edit_texts(s, sheet)
        if sheet == "gauge.kicad_sch":
            s = pads(s)
        if sheet == ROOT:
            for old, new in SHEET_NAMES.items():
                s = s.replace('(property "Sheetname" "%s"' % old, '(property "Sheetname" "%s"' % new)
        if sheet in COMMENT1:
            s = re.sub(r'\(comment 1 "[^"]*"\)', '(comment 1 "%s")' % COMMENT1[sheet], s, count=1)
        s = re.sub(r'\(comment 2 "[^"]*"\)', '(comment 2 "Spec + open items: Production/README.md")', s, count=1)
        open(path, "w", encoding="utf-8", newline="\n").write(s)
        print("%-20s merged %d wire pairs, junk link wires %d, pruned %d" % (sheet, nm, nj, npr))


if __name__ == "__main__":
    main()
