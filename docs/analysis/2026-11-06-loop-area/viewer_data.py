import os, sys  # peec.py, loops.py, board.py, sx.py, run_all_defs.py live in hardware/Production/groundup/compare/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../hardware/Production/groundup/compare'))
if 'PCB' not in os.environ: sys.exit('Set PCB to the hand-routed board: git show 8dd9eb6:hardware/Production/Monolith.kicad_pcb > hand.kicad_pcb')
import json, numpy as np
from peec import padpoly, REF, ZC
hot=json.load(open('segs_hot.json')); gate=json.load(open('segs_gate.json'))
hres=json.load(open('hot_all.json')); gres=json.load(open('gate.json'))
H={'C_0402':0.5,'C_0603':0.8,'C_0805':1.0,'C_1206':1.2,'C_1210':1.6,'CP_EIA':2.0,'Vishay':0.75,'SOT-583':0.6,'WSON':0.8,'QFN':0.9,'R_0402':0.35,'R_0201':0.25}
def body(ref):
    fp=REF[ref]; pts=[q for p in fp['pads'] if p['net'] or p['num'] for q in padpoly(p)]
    xs=[q[0] for q in pts]; ys=[q[1] for q in pts]
    name=fp['fp'].split(':')[1]; h=0.8
    for k,v in H.items():
        if name.startswith(k) or k in name: h=v
    bot=fp['layer']=='B.Cu'
    return dict(ref=ref,x0=min(xs),x1=max(xs),y0=min(ys),y1=max(ys),h=h,bot=bot,val=fp['val'])
def pads(refs):
    out=[]
    for r in refs:
        for p in REF[r]['pads']:
            if not p['net']: continue
            L='B.Cu' if REF[r]['layer']=='B.Cu' else 'F.Cu'
            out.append([round(v,3) for q in padpoly(p) for v in q]+[ZC[L]])
    return out
D={'layers':ZC,'loops':[]}
for k,v in hot.items():
    o=hres[k]; best=v['best']
    D['loops'].append(dict(id=k,kind='hot',title=k.replace('P1','Port 1').replace('P2','Port 2'),box=v['box'],
        bodies=[body(r) for r in v['refs']],pads=pads(v['refs']),best=best,
        segs={'best':v['best_segs'],'all':v['all_segs']},
        info={'best':f"{best} only: {o['caps'][best]*1e9:.2f} nH board, loop area {np.linalg.norm(o['area'][best]):.1f} mm²",
              'all':f"All caps: {o['eff_all']*1e9:.2f} nH effective, loop area {np.linalg.norm(o['area']['all']):.1f} mm²"}))
for k,v in gate.items():
    o=gres[k]
    D['loops'].append(dict(id=k,kind='gate',title=k.replace('P1','Port 1').replace('P2','Port 2'),box=v['box'],
        bodies=[body(r) for r in v['refs']],pads=pads(v['refs']),segs={'g':v['segs']},
        info={'g':f"{o['L']*1e9:.1f} nH, loop area {np.linalg.norm(o['area']):.1f} mm²"}))
json.dump(D,open('viewer.json','w'),separators=(',',':'))
print(len(json.dumps(D))/1e6,'MB')
