"""Check the production netlist against the dev board's (run after make_production.py).

Every pin that survives must sit on the same net as on the dev board, except where a 0 ohm link was replaced by a
wire (those nets merge). The new pads and the TC2030 must land on the nets of the pins they replace.
"""
import collections
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_production as mp  # noqa: E402

CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"


def netlist(sch):
    out = os.path.join(tempfile.gettempdir(), "chk_%s.xml" % os.path.basename(sch))
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", out, sch], check=True, capture_output=True)
    pin = {}
    for n in ET.parse(out).getroot().iter("net"):
        for x in n.iter("node"):
            pin[(x.get("ref"), x.get("pin"))] = n.get("name")
    return pin


def both_ports(refs, sheet):
    out = set(refs)
    if sheet == "usb_port.kicad_sch":
        out |= {r[:-3] + "5" + r[-2:] for r in refs if r[-3] == "4"}
    return out


old = netlist(os.path.join(mp.DEV, mp.ROOT_DEV))
new = netlist(os.path.join(mp.PROD, mp.ROOT))
gone, links = set(), set()
for sh, refs in mp.REMOVE.items():
    gone |= both_ports(refs, sh)
for sh, refs in mp.LINKS.items():
    links |= both_ports(refs, sh)

parent = {}


def find(a):
    while parent.get(a, a) != a:
        a = parent[a]
    return a


for r in links:
    a, b = find(old[(r, "1")]), find(old[(r, "2")])
    parent[a] = b

expect = {}
for (r, p), n in old.items():
    if r not in gone and r not in links:
        expect[(r, p)] = find(n)
for ref, _, _, (oref, opin) in mp.GAUGE_PADS:
    expect[(ref, "1")] = find(old[(oref, opin)])
for p, (oref, opin) in {"1": ("J301", "1"), "2": ("J301", "2"), "3": ("J301", "10"), "4": ("J301", "4"), "5": ("J301", "3")}.items():
    expect[("J301", p)] = find(old[(oref, opin)])

bad = []
missing = sorted(k for k in expect if k not in new)
extra = sorted(k for k in new if k not in expect and not (k[0] == "J301" and k[1] == "6"))
groups = collections.defaultdict(set)
for k, n in expect.items():
    if k in new:
        groups[n].add(new[k])
for n, s in groups.items():
    if len(s) > 1:
        bad.append("old net %s split into %s" % (n, sorted(s)))
inv = collections.defaultdict(set)
for k, n in expect.items():
    if k in new:
        inv[new[k]].add(n)
for n, s in inv.items():
    if len(s) > 1:
        bad.append("new net %s joins old nets %s" % (n, sorted(s)))
print("pins checked: %d   missing: %s   unexpected: %s" % (len(expect), missing or "-", extra or "-"))
print("\n".join(bad) if bad else "net partition matches the dev board (plus link merges)")
print("parts: dev %d -> production %d" % (len({r for r, _ in old}), len({r for r, _ in new})))
