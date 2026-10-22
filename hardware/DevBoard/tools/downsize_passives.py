"""Rev A8 passive downsizing (2026-10-16): one-shot, from the 2026-10-16 sheets. See README item 45.

Moves resistors and capacitors to the smallest package that keeps their rating, never below 0402, and never turns a
JLC basic part into an extended one. Sets Footprint, LCSC, MPN and (where the rating changes) Value.
Already applied: do not --apply it again. Some swaps chain (C409 C28323 -> C15849, and C15849 -> C52923 for C452;
C410/C411 C1779 -> C19666, and C19666 -> C23733 for C301), so a second run would shrink C409/C410/C411 again.
Dry run by default:  python -I tools/downsize_passives.py .   (add --apply to write; line endings are kept)
"""
import re, sys, glob, os
D = sys.argv[1]; apply = '--apply' in sys.argv
mpn = {
 "C307331": "CL05B104KB54PNC",
 "C15195": "CL05B103KB5NNNC",
 "C52923": "CL05A105KA5NQNC",
 "C15525": "CL05A106MQ5NUNC",
 "C23733": "CL05A475MP5NRNC",
 "C96446": "CL10A106MA8NRNC",
 "C15849": "CL10A105KB8NNNC",
 "C19666": "CL10A475KO8NNNC",
 "C377773": "CL21A225KBQNNNE",
 "C440198": "GRM21BR61H106KE43L",
 "C17168": "0402WGF0000TCE",
 "C25076": "0402WGF1000TCE",
 "C25905": "0402WGF5101TCE",
 "C25744": "0402WGF1002TCE",
 "C25900": "0402WGF4701TCE",
 "C11702": "0402WGF1001TCE",
 "C25794": "0402WGF5102TCE",
 "C25120": "0402WGF499JTCE",
 "C25741": "0402WGF1003TCE",
 "C25890": "0402WGF3301TCE",
 "C25104": "0402WGF3300TCE",
 "C25792": "0402WGF4702TCE",
 "C25077": "0402WGF100JTCE",
 "C26083": "0402WGF1004TCE",
 "C25768": "0402WGF2202TCE",
 "C25808": "0603WAF1203T5E",
 "C445619": "ERA2AEB104X",
 "C191915": "ERA2AEB103X",
 "C32298": "0402WGF1373TCE"
}
C4, C6, C8 = "Capacitor_SMD:C_0402_1005Metric", "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric"
R4, R6 = "Resistor_SMD:R_0402_1005Metric", "Resistor_SMD:R_0603_1608Metric"
# old LCSC -> (new LCSC, footprint, new Value or None, only these refs or None)
M = {
 "C14663": ("C307331", C4, None, None),
 "C57112": ("C15195", C4, None, None),
 "C15849": ("C52923", C4, "1u 25V", None),
 "C19702": ("C15525", C4, "10u 6.3V", None),
 "C19666": ("C23733", C4, "4.7u 10V", None),
 "C15850": ("C96446", C6, None, None),
 "C28323": ("C15849", C6, None, None),
 "C1779":  ("C19666", C6, "4.7u 16V", None),
 "C50254": ("C377773", C8, None, None),
 "C13585": ("C440198", C8, None, {"C204"}),
 "C21189": ("C17168", R4, None, {"R1","R2","R3","R4","R202","R203","R307","R312","R440"}),
 "C22775": ("C25076", R4, None, None),
 "C23186": ("C25905", R4, None, None),
 "C25804": ("C25744", R4, None, None),
 "C23162": ("C25900", R4, None, None),
 "C21190": ("C11702", R4, None, None),
 "C23196": ("C25794", R4, None, None),
 "C23185": ("C25120", R4, None, None),
 "C25803": ("C25741", R4, None, None),
 "C22978": ("C25890", R4, None, None),
 "C23138": ("C25104", R4, None, None),
 "C25819": ("C25792", R4, None, None),
 "C22859": ("C25077", R4, None, {"R425","R426","R428","R429"}),
 "C22935": ("C26083", R4, None, None),
 "C17414": ("C25744", R4, None, None),
 "C17560": ("C25768", R4, None, None),
 "C17436": ("C25808", R6, None, None),
 "C122537": ("C445619", R4, None, None),
 "C110775": ("C191915", R4, None, None),
 "C22872": ("C32298", R4, None, None),
}
def prop(blk, name):
    m = re.search(r'\(property "%s" "([^"]*)"' % name, blk); return m.group(1) if m else None
def setprop(blk, name, val):
    n, k = re.subn(r'(\(property "%s" ")[^"]*(")' % name, lambda m: m.group(1)+val+m.group(2), blk, count=1)
    assert k == 1, (name, blk[:200]); return n
total = 0; used = {k: 0 for k in M}
for f in sorted(glob.glob(os.path.join(D, "*.kicad_sch"))):
    raw = open(f, "rb").read(); crlf = b"\r\n" in raw; t = raw.decode("utf8").replace("\r\n", "\n")
    parts = re.split(r'(?m)(?=^\t\(symbol\n\t\t\(lib_id )', t)
    changed = 0
    for i, blk in enumerate(parts):
        if not blk.startswith("\t(symbol\n\t\t(lib_id "): continue
        # cut block at its end so we don't touch following top-level items
        end = blk.find("\n\t)\n"); body, rest = blk[:end+4], blk[end+4:]
        lc, ref = prop(body, "LCSC"), prop(body, "Reference")
        if lc not in M: continue
        new, fp, val, only = M[lc]
        if only and ref not in only: continue
        refs = re.findall(r'\(reference "([^"]+)"\)', body)
        body = setprop(body, "Footprint", fp); body = setprop(body, "LCSC", new)
        if prop(body, "MPN") is not None: body = setprop(body, "MPN", mpn[new])
        else: print("  no MPN field", ref)
        if val: body = setprop(body, "Value", val)
        parts[i] = body + rest; changed += 1; used[lc] += 1
        print(os.path.basename(f), ref, refs, lc, "->", new, fp.split(":")[1], val or "")
    total += changed
    if apply and changed:
        out = "".join(parts)
        open(f, "wb").write((out.replace("\n", "\r\n") if crlf else out).encode("utf8"))
print("symbols changed:", total)
print("unused map entries:", [k for k, v in used.items() if not v])
