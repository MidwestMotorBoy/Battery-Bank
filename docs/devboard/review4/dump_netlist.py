"""Write parts.txt and nets.txt from net.xml (KiCad netlist) for the review team."""
import os, sys, xml.etree.ElementTree as ET
d = os.path.dirname(os.path.abspath(__file__))
r = ET.parse(os.path.join(d, "net.xml")).getroot()
with open(os.path.join(d, "parts.txt"), "w", encoding="utf-8") as f:
    for c in r.iter("comp"):
        p = {x.get("name"): x.get("value") for x in c.iter("property")}
        dnp = " DNP" if "dnp" in p or p.get("DNP") else ""
        sheet = p.get("Sheetname", "")
        f.write(f'{c.get("ref")}\t{c.findtext("value")}{dnp}\t{c.findtext("footprint")}\t{sheet}\t'
                f'MPN={p.get("MPN", p.get("Manufacturer Part Number", ""))}\tLCSC={p.get("LCSC", "")}\t{p.get("Notes", "")}\n')
with open(os.path.join(d, "nets.txt"), "w", encoding="utf-8") as f:
    for n in r.iter("net"):
        nodes = " ".join(f'{x.get("ref")}.{x.get("pin")}({x.get("pinfunction") or ""})' for x in n.iter("node"))
        f.write(f'{n.get("name")}: {nodes}\n')
