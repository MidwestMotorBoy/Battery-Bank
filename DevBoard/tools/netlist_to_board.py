"""Apply a kicad-cli XML netlist to MonolithDev.kicad_pcb: pad nets, footprint symbol links and values.

The KiCad MCP's sync_schematic_to_board mishandles the reused usb_port sheet (it left port 1 unconnected and
dropped the sheet prefixes, merging the two ports' nets), so nets come from kicad-cli's netlist instead.
This updates footprints that already exist on the board; it never adds or removes footprints (a footprint
missing from the board is reported). Check the result with `kicad-cli pcb drc --schematic-parity`.

    kicad-cli sch export netlist --format kicadxml -o net.xml MonolithDev.kicad_sch
    python tools/netlist_to_board.py net.xml
"""
import os
import re
import sys
import uuid
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "MonolithDev.kicad_pcb")
BS = chr(92)

root = ET.parse(sys.argv[1]).getroot()
comps = {}
for c in root.iter("comp"):
    sp = c.find("sheetpath")
    props = {p.get("name"): p.get("value") for p in c.iter("property")}
    comps[c.get("ref")] = dict(path=sp.get("tstamps") + c.findtext("tstamps"), value=c.findtext("value"),
                               sheetname=props.get("Sheetname", ""), sheetfile=props.get("Sheetfile", ""))
padnet = {}
for n in root.iter("net"):
    for nd in n.iter("node"):
        padnet[(nd.get("ref"), nd.get("pin"))] = n.get("name")


def q(s):
    return s.replace(BS, BS + BS).replace('"', BS + '"')


def blocks(s, head, indent="\t"):
    for m in re.finditer(r"\n" + indent + r"\(" + head + r"\b", s):
        a = m.start() + 1
        d, i = 0, a
        while True:
            c = s[i]
            if c == '"':
                i += 1
                while s[i] != '"':
                    i += 2 if s[i] == BS else 1
            elif c == "(":
                d += 1
            elif c == ")":
                d -= 1
                if d == 0:
                    break
            i += 1
        yield a, i + 1


FIELD_SKIP = {"Footprint", "Reference", "Value"}
for c in root.iter("comp"):
    comps[c.get("ref")]["fields"] = {f.get("name"): (f.text or "") for f in c.iter("field") if f.get("name") not in FIELD_SKIP}
    comps[c.get("ref")]["footprint"] = c.findtext("footprint") or ""
    comps[c.get("ref")]["dnp"] = any(p.get("name") == "dnp" for p in c.iter("property"))
KICAD_FP = r"C:/Program Files/KiCad/10.0/share/kicad/footprints"
force = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else set()


def lib_body(lib_id):
    lib, name = lib_id.split(":", 1)
    d = os.path.join(HERE, "..", lib + ".pretty") if lib == "MonolithDev" else os.path.join(KICAD_FP, lib + ".pretty")
    src = open(os.path.join(d, name + ".kicad_mod"), encoding="utf-8").read()
    body = src[src.find("\n\t(descr") + 1 if "\n\t(descr" in src else src.find("\n\t(property") + 1:src.rstrip().rfind(")")]
    return "\n".join("\t" + l if l else l for l in body.rstrip("\n").split("\n")) + "\n"


def replace_fp(blk, ref, lib_id):
    """Swap in the library footprint, keeping position/uuid. Only for unrotated top-side parts."""
    at = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+)( [-\d.]+)?\)", blk)
    if (at.group(3) and float(at.group(3)) != 0) or '\n\t\t(layer "F.Cu")' not in blk:
        print(f"  {ref}: rotated or bottom-side, change its footprint in KiCad instead")
        return blk
    x, y = float(at.group(1)), float(at.group(2))
    fu = re.search(r'\n\t\t\(uuid "([^"]+)"\)', blk).group(1)
    body = lib_body(lib_id)
    body = re.sub(r'(\(property "Reference" )"[^"]*"', lambda m: f'{m.group(1)}"{ref}"', body, count=1)
    body = re.sub(r'(\(property "[^"]+" "(?:[^"\\]|\\.)*"\n\t\t\t\(at )([-\d.]+) ([-\d.]+)',
                  lambda m: f"{m.group(1)}{x + float(m.group(2)):g} {y + float(m.group(3)):g}", body)
    print(f"  {ref}: footprint -> {lib_id}")
    return f'\t(footprint "{lib_id}"\n\t\t(layer "F.Cu")\n\t\t(uuid "{fu}")\n\t\t(at {x:g} {y:g})\n{body}\t)'


s = open(PCB, encoding="utf-8").read()
reps = []
for a, b in blocks(s, "footprint"):
    blk = s[a:b]
    ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
    lib_id = re.match(r'\t\(footprint "([^"]+)"', blk).group(1)
    if ref in comps and comps[ref]["footprint"] and (lib_id != comps[ref]["footprint"] or ref in force):
        reps.append((a, b, replace_fp(blk, ref, comps[ref]["footprint"])))
for a, b, blk in sorted(reps, reverse=True):
    s = s[:a] + blk + s[b:]

out, seen, pads_set = [], set(), 0
for a, b in blocks(s, "footprint"):
    blk = s[a:b]
    ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
    if ref not in comps:
        continue                                       # board-only parts (mounting holes)
    seen.add(ref)
    c = comps[ref]
    blk = re.sub(r'\n\t\t\((path|sheetname|sheetfile) "[^"]*"\)', "", blk)
    link = f'\n\t\t(path "{c["path"]}")\n\t\t(sheetname "{q(c["sheetname"])}")\n\t\t(sheetfile "{q(c["sheetfile"])}")'
    k = re.search(r"\n\t\t\((attr|fp_|pad |embedded_fonts|model|duplicate_pad)", blk).start()
    blk = blk[:k] + link + blk[k:]
    blk = re.sub(r'(\(property "Value" ")[^"]*(")', lambda m: m.group(1) + q(c["value"]) + m.group(2), blk, count=1)
    fx, fy = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+)", blk).groups()
    for name, val in c["fields"].items():          # symbol fields (LCSC, MPN, Notes...) as hidden properties
        pat = re.compile(r'(\(property "' + re.escape(q(name)) + r'" ")((?:[^"\\]|\\.)*)(")')
        if pat.search(blk):
            blk = pat.sub(lambda m: m.group(1) + q(val) + m.group(3), blk, count=1)
            continue
        prop = (f'\n\t\t(property "{q(name)}" "{q(val)}"\n\t\t\t(at {fx} {fy} 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(hide yes)\n'
                f'\t\t\t(uuid "{uuid.uuid4()}")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n\t\t\t\t\t(thickness 0.15)\n'
                f'\t\t\t\t)\n\t\t\t)\n\t\t)')
        vm = list(blocks(blk, "property", "\t\t"))[-1]
        blk = blk[:vm[1]] + prop + blk[vm[1]:]
    pads = []
    for pa, pb in blocks(blk, "pad", "\t\t"):
        pblk = blk[pa:pb]
        num = re.search(r'\(pad "([^"]*)"', pblk).group(1)
        pblk = re.sub(r'\n\t\t\t\(net (?:\d+ )?"[^"]*"\)', "", pblk)
        net = padnet.get((ref, num)) if num else None
        if net is not None:
            k2 = pblk.find("\n\t\t\t(uuid")
            k2 = k2 if k2 >= 0 else pblk.rfind("\n\t\t)")
            pblk = pblk[:k2] + f'\n\t\t\t(net "{q(net)}")' + pblk[k2:]
            pads_set += 1
        pads.append((pa, pb, pblk))
    for pa, pb, pblk in sorted(pads, reverse=True):
        blk = blk[:pa] + pblk + blk[pb:]
    out.append((a, b, blk))
for a, b, blk in sorted(out, reverse=True):
    s = s[:a] + blk + s[b:]
open(PCB, "w", encoding="utf-8", newline="\n").write(s)
missing = sorted(set(comps) - seen)
print(f"footprints updated {len(seen)}, pad nets set {pads_set}, not on board: {missing}")
