"""Autoroute the remaining signals with Freerouting, keeping all the hand/scripted power routing.

    "C:/Program Files/KiCad/10.0/bin/python.exe" tools/autoroute.py <java.exe> <freerouting-2.5.0.jar> <work_dir> [passes]

Freerouting 2.5.0 needs Java 25 (Eclipse Temurin 25 JRE); its native CLI build crashes on this board (GraalVM
serialization error) and then hangs. The fanout stage (a via on every SMD pin) is switched off.

1. Export the board to Specctra DSN (pcbnew.ExportSpecctraDSN).
2. Post-process the DSN:
   - In1 (solid GND plane) becomes a "power" layer, so no signal is routed on it;
   - the In2 GND fill is removed from the DSN, so signals may use In2 (KiCad's zone refill carves around them);
   - every existing wire and via is "protect" (Freerouting must not rip up the power routing);
   - power classes only have small taps left: HighCurrent 0.3 mm / 0.25 mm clearance (the board's "HighCurrent copper
     to small signals" rule), Power 0.4 mm, GND 0.3 mm; signals keep 0.2 mm / 0.15 mm.
3. Run freerouting-cli, import the .ses back (pcbnew.ImportSpecctraSES), refill zones, save.
The project file is restored after the save (pcbnew rewrites it). KiCad's SES import replaces every track and via, so
the items route_power.py and fanout_gnd.py own are re-matched by geometry afterwards and their .uuids files are
rewritten.
"""
import os
import re
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "MonolithDev.kicad_pcb")
PRO = os.path.join(HERE, "..", "MonolithDev.kicad_pro")
SIDECARS = [os.path.join(HERE, n) for n in ("route_power.uuids", "fanout_gnd.uuids")]
JAVA, JAR, WORK = sys.argv[1], sys.argv[2], sys.argv[3]
PASSES = sys.argv[4] if len(sys.argv) > 4 else "40"
os.makedirs(WORK, exist_ok=True)
dsn, ses = os.path.join(WORK, "board.dsn"), os.path.join(WORK, "board.ses")


def key(t):
    """Geometry key that survives the DSN/SES round trip (1 um grid)."""
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        return ("via", p.x // 1000, p.y // 1000, t.GetNetname())
    a, b = t.GetStart(), t.GetEnd()
    ends = tuple(sorted(((a.x // 1000, a.y // 1000), (b.x // 1000, b.y // 1000))))
    return ("trk", t.GetLayer(), ends, t.GetWidth() // 1000, t.GetNetname())


pro_backup = open(PRO, encoding="utf-8").read()
board = pcbnew.LoadBoard(PCB)
owned = {f: set(open(f).read().split()) for f in SIDECARS if os.path.exists(f)}
owned_keys = {f: {key(t) for t in board.GetTracks() if t.m_Uuid.AsString() in ids} for f, ids in owned.items()}
zone_ids = {f: [z.m_Uuid.AsString() for z in board.Zones() if z.m_Uuid.AsString() in ids] for f, ids in owned.items()}
assert pcbnew.ExportSpecctraDSN(board, dsn)

s = open(dsn, encoding="utf-8").read()
s, n = re.subn(r'(\(layer "In1\.Cu \(GND\)"\s*\(type )signal', r"\1power", s)
assert n == 1
s, n = re.subn(r'\n\s*\(plane GND \(polygon "In2\.Cu \(power\)".*?\)\)', "", s, flags=re.S)
assert n == 1, n
s = s.replace("(type route)", "(type protect)")


def set_rule(cls, width, clearance):
    """Rewrite the (rule (width ..) (clearance ..)) block of one DSN net class."""
    global s
    i = s.index("(class %s " % cls)
    j = s.index("(rule", i)
    end = s.index("  )", s.index("(clearance", j))
    seg = re.sub(r"\(width [\d.]+\)", "(width %d)" % width, s[j:end])
    seg = re.sub(r"\(clearance [\d.]+\)", "(clearance %d)" % clearance, seg, count=1)
    s = s[:j] + seg + s[end:]


set_rule("HighCurrent", 300, 250)
set_rule("Power", 400, 150)
set_rule("GND", 300, 150)
open(dsn, "w", encoding="utf-8").write(s)

cmd = [JAVA, "-jar", JAR, "--gui.enabled=false", "--router.fanout.enabled=false",
       "--router.autorouter.max_passes=" + PASSES, "--router.optimizer.max_threads=16", "-de", dsn, "-do", ses]
print(" ".join(cmd), flush=True)
r = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
print(r.stdout[-4000:], r.stderr[-2000:])
assert os.path.exists(ses), "no session file"

board = pcbnew.LoadBoard(PCB)
assert pcbnew.ImportSpecctraSES(board, ses)
new_ids = {f: [t.m_Uuid.AsString() for t in board.GetTracks() if key(t) in ks] for f, ks in owned_keys.items()}
for f in owned:
    print("%s: re-matched %d of %d" % (os.path.basename(f), len(new_ids[f]), len(owned_keys[f])))
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(PCB)
for f in owned:
    open(f, "w", newline="\n").write("\n".join(zone_ids[f] + new_ids[f]) + "\n")
open(PRO, "w", encoding="utf-8", newline="\n").write(pro_backup)
print("imported", ses)
