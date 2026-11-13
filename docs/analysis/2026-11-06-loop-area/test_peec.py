# validation: parallel-plate strip line: two strips w wide, l long, stacked d apart (F.Cu & In1), shorted at one end, port at other.
import os, sys  # peec.py, loops.py, board.py, sx.py, run_all_defs.py live in hardware/Production/groundup/compare/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../hardware/Production/groundup/compare'))
if 'PCB' not in os.environ: sys.exit('Set PCB to the hand-routed board: git show 8dd9eb6:hardware/Production/Monolith.kicad_pcb > hand.kicad_pcb')
import numpy as np, peec, math
from peec import Model, ZC
class Fake(Model):
    def __init__(s,h,w,l,layers):
        s.box=(0,l,0,w); s.h=h; s.layers=layers; s.W=int(round(l/h)); s.H=int(round(w/h)); s.nets=['A','B']; s.nid={'A':1,'B':2}
        s.lab={L:np.full((s.H,s.W),i+1,np.int32) for i,L in enumerate(layers)}
for h in (0.5,0.25):
  for w,l in ((2,10),(4,10)):
    m=Fake(h,w,l,['F.Cu','In1.Cu'])
    # groups: port P = left column F.Cu, N = left column In1 ; short right column via stamps
    import peec as P
    m.gid={}; 
    # manual build: emulate groups by masks
    H,W=m.H,m.W; n=0; nodeid={}
    gid={'P':0,'N':1,'RA':2,'RB':3}; n=4
    for L,gl,gr in (('F.Cu','P','RA'),('In1.Cu','N','RB')):
        ids=np.arange(n,n+H*W).reshape(H,W); n+=H*W; ids[:,0]=gid[gl]; ids[:,-1]=gid[gr]; nodeid[L]=ids
    m.N=n; m.nodeid=nodeid; m.gid=gid
    br=[]
    for L in m.layers:
        ids=nodeid[L]; z=ZC[L]; t=P.TH[L]
        for r in range(H):
            for c in range(W-1):
                if ids[r,c]!=ids[r,c+1]: br.append((ids[r,c],ids[r,c+1],0,(c+1)*h,(r+.5)*h,z,h,h,t))
        for r in range(H-1):
            for c in range(W):
                if ids[r,c]!=ids[r+1,c]: br.append((ids[r,c],ids[r+1,c],1,(c+.5)*h,(r+1)*h,z,h,h,t))
    m.br=np.array(br,float); m.K()
    L=m.solve(('P','N'),[('RA','RB',1e15)])
    d=ZC['In1.Cu']-ZC['F.Cu']
    print(h,w,l,'PEEC %.3f nH'%(L*1e9),' mu0*l*d/w %.3f nH'%(4e-7*math.pi*l*d/w*1e-3*1e9))
