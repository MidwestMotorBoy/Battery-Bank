import os, sys  # peec.py, loops.py, board.py, sx.py, run_all_defs.py live in hardware/Production/groundup/compare/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../hardware/Production/groundup/compare'))
if 'PCB' not in os.environ: sys.exit('Set PCB to the hand-routed board: git show 8dd9eb6:hardware/Production/Monolith.kicad_pcb > hand.kicad_pcb')
import json, numpy as np, sys
from loops import *
from run_all_defs import HOT, GATES
def segs(m, I, elems, frac=0.035):
    br=m.br; ng=len(m.gid); mx=np.abs(I).max()
    keep=np.abs(I)>frac*mx
    out=[]
    for k in np.nonzero(keep)[0]:
        a=br[k,9:12]; b=br[k,12:15]; i=I[k]
        if i<0: a,b,i=b,a,-i
        out.append([round(a[0],2),round(a[1],2),round(a[2],3),round(b[0],2),round(b[1],2),round(b[2],3),round(i/mx,3),0])
        # supernode legs
        for col,E in ((0,br[k,9:12]),(1,br[k,12:15])):
            nd=int(br[k,col])
            if nd<ng and abs(I[k])>0.15*mx:
                C=m.gcent[nd]; out.append([round(C[0],2),round(C[1],2),round(C[2],3),round(E[0],2),round(E[1],2),round(E[2],3),round(abs(I[k])/mx,3),2])
    for gf,gt,cur,zoff in elems:
        P0=m.gcent[m.gid[gf]]; Q0=m.gcent[m.gid[gt]]
        if cur<0: P0,Q0,cur=Q0,P0,-cur
        P=P0.copy(); Q=Q0.copy(); P[2]+=zoff; Q[2]+=zoff
        for A,B in ((P0,P),(P,Q),(Q,Q0)):
            out.append([round(A[0],2),round(A[1],2),round(A[2],3),round(B[0],2),round(B[1],2),round(B[2],3),round(min(1,cur/mx),3),1])
    return out
res={}
which=sys.argv[1]
if which=='hot':
    for name, box, pnet, caps, dev, dp, sp in HOT:
        o,m=hot_loop(name, box, pnet, caps, dev, dp, sp, h=0.3)
        best=min(o['caps'],key=o['caps'].get)
        res[name]={'box':box,'refs':[dev]+caps,'best':best,
                   'best_segs':segs(m,m.curr[best],m.elems[best]),'all_segs':segs(m,m.curr['all'],m.elems['all'])}
        print(name,len(res[name]['best_segs']),len(res[name]['all_segs']),flush=True); del m
else:
    for name,nets,U,dp,rp,R,Q,qp in GATES:
        box=autobox([U,R,Q],2.0)
        o,m,I=gate_loop(name,box,nets,None,U,dp,rp,R,Q,qp,h=0.15)
        res[name]={'box':box,'refs':[U,R,Q],'segs':segs(m,I,m.elems['g'],frac=0.05)}
        print(name,len(res[name]['segs']),flush=True); del m
json.dump(res,open(f'segs_{which}.json','w'))
