import os, sys  # peec.py, loops.py, board.py, sx.py, run_all_defs.py live in hardware/Production/groundup/compare/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../hardware/Production/groundup/compare'))
if 'PCB' not in os.environ: sys.exit('Set PCB to the hand-routed board: git show 8dd9eb6:hardware/Production/Monolith.kicad_pcb > hand.kicad_pcb')
import numpy as np, json
from peec import Model, LAYERS, REF, FP, SEG, VIA, ZON
from scipy import ndimage
E0=8.854e-12
SWN=['/USB Port 1/SW1','/USB Port 1/SW2','/USB Port 2/SW1','/USB Port 2/SW2','/USB Port 1/SW_5V','/USB Port 2/SW_5V','/3V3 Rail/SW_3V3']
allnets=sorted(set([p['net'] for fp in FP for p in fp['pads'] if p['net']]+[s['net'] for s in SEG if s['net']]+[z['net'] for z in ZON if z['net']]))
res={}
h=0.05
for sw in SWN:
    xs=[s['x1'] for s in SEG if s['net']==sw]+[s['x2'] for s in SEG if s['net']==sw]+[p['x'] for fp in FP for p in fp['pads'] if p['net']==sw]+[v['x'] for v in VIA if v['net']==sw]
    ys=[s['y1'] for s in SEG if s['net']==sw]+[s['y2'] for s in SEG if s['net']==sw]+[p['y'] for fp in FP for p in fp['pads'] if p['net']==sw]+[v['y'] for v in VIA if v['net']==sw]
    for z in ZON:
        if z['net']==sw:
            for L,pts in z['fills']: xs+= [q[0] for q in pts]; ys+=[q[1] for q in pts]
    box=(min(xs)-1.5,max(xs)+1.5,min(ys)-1.5,max(ys)+1.5)
    m=Model(box,allnets,h=h)
    sid=m.nid[sw]; r={'box':box,'layers':{},'vias':sum(1 for v in VIA if v['net']==sw)}
    for L in LAYERS:
        lab=m.lab[L]; msk=lab==sid; a=msk.sum()*h*h
        if a<0.01: continue
        # neighbours within 0.5 mm on same layer
        dist=ndimage.distance_transform_edt(~msk)*h
        near={}
        for nid in np.unique(lab[(dist<=0.5)&(lab>0)&(~msk)]):
            nn=m.nets[nid-1]; mm=(lab==nid)&(dist<=0.5)
            near[nn]=dict(cells=int(mm.sum()), dmin=round(float(dist[mm].min()),3))
        r['layers'][L]=dict(area=round(float(a),2),near=near)
    tot=sum(v['area'] for v in r['layers'].values())
    # capacitance: outer layers to adjacent GND plane (0.2 mm, er 4.4); inner to planes both sides
    C=0
    for L,v in r['layers'].items():
        if L in('F.Cu','B.Cu'): C+=E0*4.4*v['area']*1e-6/0.2e-3
        else: C+=2*E0*4.5*v['area']*1e-6/0.3e-3
    r['total_area']=round(tot,2); r['C_pF']=round(C*1e12,1)
    res[sw]=r
    print(sw, 'total %.1f mm2'%tot, {L:v['area'] for L,v in r['layers'].items()}, 'vias',r['vias'],'C~%.1f pF'%(C*1e12))
    for L,v in r['layers'].items():
        print('   ',L,{k.split('/')[-1]:(d['dmin'],d['cells']) for k,d in v['near'].items() if k!=sw})
json.dump(res,open('swarea.json','w'),indent=1)
