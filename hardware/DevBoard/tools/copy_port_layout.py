"""Copy part of one USB port's layout onto the other port (a partial "replicate layout").

KiCad's Repeat Layout and the ReplicateLayout plugin work on whole sheet instances; this copies only a chosen
list of refs. For each source ref (5xx) its twin (4xx) is placed at the same offset from the destination anchor
as the source has from the source anchor, with the same rotation and side. Tracks and vias whose net belongs to
the copied parts and that lie inside the source group's bounding box are copied too, nets renamed
(/USB Port 2/X -> /USB Port 1/X, Net-(U503-FB) -> Net-(U403-FB), global nets unchanged). Tracks and vias already
inside the destination box on those nets are removed first.

Usage (from DevBoard/): python tools/copy_port_layout.py [--dry-run]
Edit SRC_ANCHOR / DST_ANCHOR / REFS below. Restores MonolithDev.kicad_pro after saving (pcbnew rewrites it).
"""
import os
import re
import shutil
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
BOARD = os.path.join(ROOT, "MonolithDev.kicad_pcb")
PRO = os.path.join(ROOT, "MonolithDev.kicad_pro")

SRC_ANCHOR, DST_ANCHOR = "U503", "U403"
# BQ25756 controller block of port 2 (selection copied from KiCad 2026-10-17)
REFS = ["U503", "U502"] + [f"R{n}" for n in list(range(509, 524)) + [525, 526, 528, 529, 535, 548, 549]] + \
       [f"C{n}" for n in range(508, 520)] + ["D504", "D505"]
MARGIN = pcbnew.FromMM(1.0)
DRY = "--dry-run" in sys.argv


def twin(ref):
    m = re.match(r"([A-Z]+)5(\d\d)$", ref)
    assert m, ref
    return f"{m.group(1)}4{m.group(2)}"


# Nets whose port-1 name is not the plain rename (labelled on the root sheet for the PD address straps)
NET_OVERRIDE = {"/USB Port 2/LDO_3V3": "/P1_LDO_3V3"}


def map_net(name):
    if name in NET_OVERRIDE:
        return NET_OVERRIDE[name]
    if name.startswith("/USB Port 2/"):
        return "/USB Port 1/" + name[len("/USB Port 2/"):]
    if name.startswith("Net-(") or name.startswith("unconnected-("):
        return re.sub(r"\b([A-Z]+)5(\d\d)\b", r"\g<1>4\2", name)
    if "Port 2" in name or "Port 1" in name:
        raise ValueError(name)
    return name                                    # global net (GND, 3V3, PACK_P, CHG_INH, ...)


pro_backup = open(PRO, "rb").read()
b = pcbnew.LoadBoard(BOARD)
nets = {n: b.FindNet(n) for n in []}


def net(name):
    if name not in nets:
        nets[name] = b.FindNet(name)
    return nets[name]


src_a = b.FindFootprintByReference(SRC_ANCHOR).GetPosition()
dst_a = b.FindFootprintByReference(DST_ANCHOR).GetPosition()
d = dst_a - src_a
print(f"offset {pcbnew.ToMM(d.x):.3f}, {pcbnew.ToMM(d.y):.3f} mm")

# ---- source group: bounding box and nets
sbox = None
src_nets = set()
for r in REFS:
    f = b.FindFootprintByReference(r)
    bb = f.GetBoundingBox(False)
    if sbox is None:
        sbox = pcbnew.BOX2I(bb.GetPosition(), bb.GetSize())
    else:
        sbox.Merge(bb)
    for p in f.Pads():
        if p.GetNetname():
            src_nets.add(p.GetNetname())
sbox.Inflate(MARGIN)
dbox = pcbnew.BOX2I(sbox.GetPosition() + d, sbox.GetSize())
dst_nets = {map_net(n) for n in src_nets}
missing = sorted(n for n in dst_nets if not net(n))
if missing:
    print("WARNING: no such destination net:", missing)


def inside(item, box):
    if isinstance(item, pcbnew.PCB_VIA):
        return box.Contains(item.GetPosition())
    return box.Contains(item.GetStart()) and box.Contains(item.GetEnd())


src_tracks = [t for t in b.GetTracks() if t.GetNetname() in src_nets and inside(t, sbox)]
old_dst = [t for t in b.GetTracks() if t.GetNetname() in dst_nets and inside(t, dbox)]
print(f"source: {len(REFS)} parts, {sum(isinstance(t, pcbnew.PCB_VIA) for t in src_tracks)} vias, "
      f"{sum(not isinstance(t, pcbnew.PCB_VIA) for t in src_tracks)} segments/arcs")
print(f"destination box already holds {len(old_dst)} tracks/vias on these nets: removed")

if DRY:
    sys.exit(0)

# ---- parts
for r in REFS:
    s = b.FindFootprintByReference(r)
    t = b.FindFootprintByReference(twin(r))
    if t is None:
        print("no twin for", r)
        continue
    if t.IsFlipped() != s.IsFlipped():
        t.Flip(t.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    t.SetOrientation(s.GetOrientation())
    t.SetPosition(s.GetPosition() + d)
    # keep reference/value text where they sit on the source
    for st, tt in ((s.Reference(), t.Reference()), (s.Value(), t.Value())):
        tt.SetPosition(st.GetPosition() + d)
        tt.SetTextAngle(st.GetTextAngle())
        tt.SetVisible(st.IsVisible())

# ---- tracks and vias
for t in old_dst:
    b.Remove(t)
n_new = 0
for t in src_tracks:
    c = t.Duplicate()
    c.Move(d)
    nn = net(map_net(t.GetNetname()))
    if nn is None:
        continue
    c.SetNet(nn)
    b.Add(c)
    n_new += 1
print("copied", n_new, "tracks/vias")

b.Save(BOARD)
open(PRO, "wb").write(pro_backup)
print("saved", BOARD)
