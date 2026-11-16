"""straighten_apply.py in.kicad_pcb out.kicad_pcb spec.json      (KiCad python)
Apply a spec from straighten.py: remove the listed tracks by id, add the new segments (integer nanometres), refill the
zones and save. Nothing else on the board is touched. The board's .kicad_pro must sit beside in.kicad_pcb (net classes)."""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); spec = json.load(open(sys.argv[3]))
L = {"F": pcbnew.F_Cu, "In1": pcbnew.In1_Cu, "In2": pcbnew.In2_Cu, "In3": pcbnew.In3_Cu, "In4": pcbnew.In4_Cu, "B": pcbnew.B_Cu}
dele = set(spec['del']); gone = 0
ALL = list(b.GetTracks())                   # kept to the end: a removed track that Python frees early crashes the zone filler
for t in ALL:
    if t.GetClass() == 'PCB_TRACK' and t.m_Uuid.AsString() in dele: b.Remove(t); gone += 1
assert gone == len(dele), (gone, len(dele))
new = []
for s in spec['add']:
    net = b.FindNet(s['net']); assert net is not None, s['net']
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(int(s['x1']), int(s['y1']))); t.SetEnd(pcbnew.VECTOR2I(int(s['x2']), int(s['y2'])))
    t.SetWidth(int(s['w'])); t.SetLayer(L[s['l']]); t.SetNet(net); b.Add(t); new.append(t)
b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[2])
print('removed', gone, 'added', len(new))
