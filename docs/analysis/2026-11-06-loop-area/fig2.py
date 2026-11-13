import os, sys  # peec.py, loops.py, board.py, sx.py, run_all_defs.py live in hardware/Production/groundup/compare/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../hardware/Production/groundup/compare'))
if 'PCB' not in os.environ: sys.exit('Set PCB to the hand-routed board: git show 8dd9eb6:hardware/Production/Monolith.kicad_pcb > hand.kicad_pcb')
import pickle, numpy as np, sys, math
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.colors import LinearSegmentedColormap, LogNorm, ListedColormap, PowerNorm
from peec import Model, padpoly, LAYERS, FP, SEG, ZON, REF
OUT=sys.argv[1]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'figure.facecolor':'#fcfcfb','axes.facecolor':'#fcfcfb'})
HEAT = LinearSegmentedColormap.from_list('h', [(1,0.95,0.85,0),(0.98,0.75,0.45,0.55),(0.93,0.42,0.18,0.85),(0.7,0.15,0.05,1),(0.35,0.02,0.0,1)])
allnets=sorted(set([p['net'] for fp in FP for p in fp['pads'] if p['net']]+[s['net'] for s in SEG if s['net']]+[z['net'] for z in ZON if z['net']]))
def netcolor(n, loopnets):
    if n=='GND': return (0.80,0.80,0.80)
    if n in loopnets: return loopnets[n]
    return (0.90,0.90,0.88)
def panel(ax, box, h, cur, L, loopnets, refs, vmax, title):
    m=Model(box, allnets, h=0.05, layers=[L]); lab=m.lab[L]
    img=np.ones(lab.shape+(3,))*0.985
    for nid in np.unique(lab):
        if nid==0: continue
        img[lab==nid]=netcolor(allnets[nid-1], loopnets)
    ext=(box[0],box[0]+lab.shape[1]*0.05,box[2]+lab.shape[0]*0.05,box[2])
    ax.imshow(img,extent=ext,interpolation='nearest')
    c=cur.copy(); 
    ax.imshow(np.ma.masked_less(c, vmax*0.06), extent=(box[0],box[0]+c.shape[1]*h,box[2]+c.shape[0]*h,box[2]), cmap=HEAT, norm=PowerNorm(0.6,vmin=vmax*0.06,vmax=vmax), interpolation='nearest')
    for fp in FP:
        if fp['ref'] not in refs: continue
        onl = fp['layer']==L
        for p in fp['pads']:
            if p['net'] and (L in p['layers'] or '*.Cu' in p['layers']):
                ax.add_patch(Polygon(padpoly(p),fill=False,lw=0.6,ec='#222'))
        if onl:
            ax.text(fp['x'],fp['y'],fp['ref'],fontsize=7.5,ha='center',va='center',color='#0b3d91',weight='bold',
                    bbox=dict(boxstyle='round,pad=0.12',fc='white',ec='none',alpha=0.75))
    ax.set_xlim(box[0],box[1]); ax.set_ylim(box[3],box[2]); ax.set_aspect('equal')
    ax.set_title(title,fontsize=9,loc='left',weight='bold'); ax.tick_params(labelsize=7)
def figure(key, d, mp, fn, title, sub, loopnets, refs, maxpanels=4):
    box=d['box']; h=d['h']
    pk={L:np.percentile(mp[L],99.7) for L in mp}
    Ls=[L for L in LAYERS if pk.get(L,0)>0.15*max(pk.values())][:maxpanels-1]
    plan=sum(mp[L] for L in mp)
    vmax=max(pk[L] for L in Ls)
    n=len(Ls)+1; fig,axs=plt.subplots(1,n,figsize=(3.6*n+0.4,3.9),squeeze=False)
    names={'F.Cu':'F.Cu (top)','In1.Cu':'In1 (GND)','In2.Cu':'In2','In3.Cu':'In3','In4.Cu':'In4 (GND)','B.Cu':'B.Cu (bottom)'}
    panel(axs[0][0],box,h,plan,'F.Cu',loopnets,refs,np.percentile(plan,99.7),'All layers, seen from the top')
    for ax,L in zip(axs[0][1:],Ls):
        panel(ax,box,h,mp[L],L,loopnets,refs,vmax,names[L])
    fig.suptitle(title,x=0.01,y=0.995,ha='left',fontsize=11,weight='bold')
    fig.text(0.01,0.925,sub,fontsize=8.5,color='#52514e',ha='left')
    fig.tight_layout(rect=(0,0,1,0.9)); fig.savefig(fn,dpi=130); plt.close(fig)
BLUE=(0.55,0.70,0.95); PURP=(0.80,0.65,0.95); GREEN=(0.65,0.88,0.65); PINK=(0.97,0.72,0.85); TEAL=(0.6,0.88,0.88); YEL=(0.98,0.85,0.5)
def slug(k):  # 'P1 VBUS leg (Q401)' -> 'p1-vbus-q401': file names follow the loop name, not the list order
    return '-'.join(k.lower().replace('gate ','').replace('leg ','').replace('buck ','').replace('(','').replace(')','').split())
import json
hot=json.load(open('hot_all.json')); maps=pickle.load(open('maps_all.pkl','rb'))
spec=[
 ('P1 VBUS leg (Q401)','Port 1 VBUS-side hot loop (Q401, SW1)','/USB Port 1/AC_SNS_N',['Q401','C430','C420','C423','C424','C427','C456','C421','L401']),
 ('P2 VBUS leg (Q501)','Port 2 VBUS-side hot loop (Q501, SW1)','/USB Port 2/AC_SNS_N',['Q501','C530','C520','C523','C524','C527','C556','C521','L501']),
 ('P1 PACK leg (Q402)','Port 1 PACK-side hot loop (Q402, SW2)','/USB Port 1/BAT_SNS_P',['Q402','C438','C431','C434','L401']),
 ('P2 PACK leg (Q502)','Port 2 PACK-side hot loop (Q502, SW2)','/USB Port 2/BAT_SNS_P',['Q502','C538','C531','C534','L501']),
 ('P1 5V buck (U404)','Port 1 5 V buck input loop (U404)','PACK_P',['U404','C446','C444','C209','C210','C213','L402']),
 ('P2 5V buck (U504)','Port 2 5 V buck input loop (U504)','PACK_P',['U504','C546','C544','L502']),
 ('3V3 buck (U204)','3V3 buck input loop (U204)','PACK_P',['U204','C206','L201']),
]
for i,(k,t,pn,refs) in enumerate(spec):
    o=hot[k]; best=min(o['caps'],key=o['caps'].get)
    sub=f"Effective {o['eff_all']*1e9:.2f} nH with all caps (ESL incl.)  |  {best}: {o['caps'][best]*1e9:.2f} nH board, carries {o['share'][best]*100:.0f} %  |  loop area {np.linalg.norm(o['area']['all']):.1f} mm²   (blue/purple/green = loop net, grey = GND, heat = HF current)"
    figure(k,maps[k],maps[k]['mall'],f'{OUT}/hot-{slug(k)}.png',t,sub,{pn:PURP if 'AC_SNS' in pn else (GREEN if 'BAT' in pn else BLUE)},refs)
g=json.load(open('gate.json')); gm=pickle.load(open('maps_gate.pkl','rb'))
for i,(k,d) in enumerate(gm.items()):
    p=k[1]; U='U403' if p=='1' else 'U503'
    Q=k.split('(')[1][:-1]; legA='leg A' in k; hs='HS' in k
    num=('1' if legA else '2')
    # map correctly: leg A HS=R444/R544, LS=R445/R545; leg B HS=R446/R546, LS=R447/R547
    idx={(True,True):'4',(True,False):'5',(False,True):'6',(False,False):'7'}[(legA,hs)]
    rr=f'R{4 if p=="1" else 5}4{idx}'
    drv=f'/USB Port {p}/{"HIDRV" if hs else "LODRV"}{num}'; gnet=f'/USB Port {p}/{"HG" if hs else "LG"}{num}'; ret=f'/USB Port {p}/SW{num}' if hs else 'GND'
    ln={drv:BLUE,gnet:TEAL}
    if hs: ln[ret]=PINK
    o=g[k]
    sub=f"L = {o['L']*1e9:.1f} nH  |  loop area {np.linalg.norm(o['area']):.1f} mm²   (blue = driver trace, teal = gate after {rr}, pink = SW return, grey = GND, heat = HF current)"
    figure(k,d,d['map'],f'{OUT}/gate-{slug(k)}.png',f'{k.replace("P1","Port 1").replace("P2","Port 2")} gate-drive loop',sub,ln,[U,Q,rr],maxpanels=4)
print('done')
