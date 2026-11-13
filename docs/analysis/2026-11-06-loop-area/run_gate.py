import os, sys  # peec.py, loops.py, board.py, sx.py, run_all_defs.py live in hardware/Production/groundup/compare/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../hardware/Production/groundup/compare'))
if 'PCB' not in os.environ: sys.exit('Set PCB to the hand-routed board: git show 8dd9eb6:hardware/Production/Monolith.kicad_pcb > hand.kicad_pcb')
import json, pickle
from loops import *
res={}; maps={}
G=[]
for p,U,Q1,Q2,R in (('1','U403','Q401','Q402',('R444','R445','R446','R447')),('2','U503','Q501','Q502',('R544','R545','R546','R547'))):
    n=lambda s: f'/USB Port {p}/{s}'
    G += [
     (f'P{p} HS gate leg A ({Q1})', [n('HIDRV1'),n('HG1'),n('SW1'),'GND'], U,'27',['28'], R[0], Q1, ['1','9']),
     (f'P{p} LS gate leg A ({Q1})', [n('LODRV1'),n('LG1'),'GND'], U,'25',['17','22','37'], R[1], Q1, ['8','5','6','7']),
     (f'P{p} HS gate leg B ({Q2})', [n('HIDRV2'),n('HG2'),n('SW2'),'GND'], U,'19',['18'], R[2], Q2, ['1','9']),
     (f'P{p} LS gate leg B ({Q2})', [n('LODRV2'),n('LG2'),'GND'], U,'21',['17','22','37'], R[3], Q2, ['8','5','6','7']),
    ]
for name,nets,U,dp,rp,R,Q,qp in G:
    box=autobox([U,R,Q],2.0)
    o,m,I=gate_loop(name,box,nets,None,U,dp,rp,R,Q,qp,h=0.15)
    a=np.array(o['area'])
    print(f"{name}: L={o['L']*1e9:.2f} nH |A|={np.linalg.norm(a):.2f} mm2 (Az {a[2]:.2f}, vert {np.hypot(a[0],a[1]):.2f}) N={o['nodes']} {o['t']:.0f}s",flush=True)
    res[name]=o; maps[name]={'box':m.box,'h':m.h,'map':currmap(m,I)}
    del m
json.dump(res,open('gate.json','w'),indent=1,default=float); pickle.dump(maps,open('maps_gate.pkl','wb'))
