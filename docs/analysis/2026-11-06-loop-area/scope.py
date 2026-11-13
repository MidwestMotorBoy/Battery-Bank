import json, math, numpy as np, sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT=sys.argv[1]
def slug(k):  # 'P1 VBUS leg (Q401)' -> 'p1-vbus-q401': file names follow the loop name, not the list order
    return '-'.join(k.lower().replace('gate ','').replace('leg ','').replace('buck ','').replace('(','').replace(')','').split())
hot=json.load(open('hot_all.json')); gate=json.load(open('gate.json'))
def sim_sw(V, L, C, Q, I, tr, Ron=0.006, T=40e-9, dt=0.5e-12):
    """HS turn-on: rail V -> L,R -> HS switch (R falls over tr) -> SW node, Coss to GND, load I out of SW,
    LS body diode clamps SW at -0.7 V. Backward-Euler (stiff while the switch is open)."""
    R=math.sqrt(L/C)/Q
    n=int(T/dt); t=np.arange(n)*dt; v=np.empty(n); i=0.0; vs=-0.7; t0=5e-9
    for k in range(n):
        tt=t[k]-t0
        if tt<0: rs=1e4
        elif tt<tr: rs=math.exp(math.log(1e4)+(math.log(Ron)-math.log(1e4))*tt/tr)
        else: rs=Ron
        i=(i+dt*(V-vs+dt*I/C)/L)/(1+dt*(R+rs)/L+dt*dt/(L*C))
        vs=vs+dt*(i-I)/C
        if vs< -0.7: vs=-0.7
        v[k]=vs
    return t,v
def sim_gate(Vdrv, L, C, Rt, T=60e-9, dt=5e-12, rise=True):
    n=int(T/dt); t=np.arange(n)*dt; v=np.empty(n); i=0.0; vg=0.0 if rise else Vdrv; t0=8e-9
    for k in range(n):
        u=(Vdrv if rise else 0.0) if t[k]>=t0 else (0.0 if rise else Vdrv)
        di=(u-vg-i*Rt)/L; i+=di*dt; vg+=i/C*dt; v[k]=vg
    return t,v
BG='#0e1210'; GR='#2b3a30'; TR='#f2d23c'; BAD='#ff5a4e'; TXT='#c9d4cc'
def scope(ax, t, v, vbad, vdiv, tdiv, title, readout, ylo, refline=None, refl=''):
    ax.set_facecolor(BG)
    for s in ax.spines.values(): s.set_color(GR)
    x0=t[0]*1e9; ax.set_xlim(x0,x0+10*tdiv); ax.set_ylim(ylo,ylo+8*vdiv)
    ax.set_xticks(np.arange(x0,x0+10*tdiv+1e-9,tdiv)); ax.set_yticks(np.arange(ylo,ylo+8*vdiv+1e-9,vdiv))
    ax.grid(True,color=GR,lw=0.7); ax.tick_params(colors=TXT,labelsize=7,length=0)
    ax.set_xticklabels([]); ax.set_yticklabels([])
    if refline is not None:
        ax.axhline(refline,color='#6f8fa8',lw=0.9,ls=(0,(4,3))); ax.text(x0+0.1*tdiv,refline+0.12*vdiv,refl,color='#8fb0c8',fontsize=7)
    if vbad is not None: ax.plot(t*1e9,vbad,color=BAD,lw=1.0,alpha=0.85)
    ax.plot(t*1e9,v,color=TR,lw=1.5)
    ax.text(x0+0.1*tdiv,ylo+7.55*vdiv,title,color='white',fontsize=8.5,weight='bold',va='center')
    ax.text(x0+9.9*tdiv,ylo+0.35*vdiv,f'{vdiv:g} V/div   {tdiv:g} ns/div',color=TXT,fontsize=7,ha='right')
    ax.text(x0+9.9*tdiv,ylo+7.55*vdiv,readout,color=TR,fontsize=7.5,ha='right',va='center',family='DejaVu Sans Mono')
def ringf(sig,t,start):
    s=sig[t>start]; tt=t[t>start]; m=s-s[-len(s)//4:].mean()
    zc=tt[1:][(m[:-1]<0)&(m[1:]>=0)]
    return 1/np.mean(np.diff(zc[:4])) if len(zc)>2 else float('nan')
spec=[('P1 VBUS leg (Q401)','Port 1 VBUS leg, SW1 rising',21,5.0,3e-9,170e-12),
 ('P2 VBUS leg (Q501)','Port 2 VBUS leg, SW1 rising',21,5.0,3e-9,170e-12),
 ('P1 PACK leg (Q402)','Port 1 PACK leg, SW2 rising',16.8,6.8,3e-9,170e-12),
 ('P2 PACK leg (Q502)','Port 2 PACK leg, SW2 rising',16.8,6.8,3e-9,170e-12),
 ('P1 5V buck (U404)','Port 1 5 V buck, SW_5V rising',16.8,3.0,2e-9,80e-12),
 ('P2 5V buck (U504)','Port 2 5 V buck, SW_5V rising',16.8,3.0,2e-9,80e-12),
 ('3V3 buck (U204)','3V3 buck, SW_3V3 rising',16.8,0.5,2e-9,30e-12)]
res={}
order=list(hot.keys())
ring=json.load(open('ring.json'))
def sw_wave(V,tr,dv,f,tau,T=40e-9,dt=5e-12,t0=5e-9):
    """SW rising edge: raised-cosine edge -0.7 V -> V over tr, then a damped ring (f, tau) whose
    first peak above the rail is dv (the ringing table's L*I/tr estimate)"""
    t=np.arange(int(T/dt))*dt; u=np.clip((t-t0)/tr,0,1)
    edge=-0.7+(V+0.7)*(1-np.cos(np.pi*u))/2
    te=t0+tr; x=np.clip(t-te,0,None)
    r=np.exp(-x/tau)*np.sin(2*np.pi*f*x)*(1-np.exp(-x/0.12e-9)); r*=dv/r.max()
    return t,edge+r
for (k,title,V,I,tr,C),R in zip(spec,ring):
    assert title.startswith(R['lab']), (title, R['lab'])   # ring.json is in this list's order, not hot_all.json's
    f=R['f']*1e6; tau=R['tau']*1e-9; dv=R['dv']
    t,v=sw_wave(V,tr,dv,f,tau); _,vb=sw_wave(V,tr,4*dv,f/2,25/(np.pi*f/2))
    pk=v.max(); pkb=vb.max()
    fig,axs=plt.subplots(1,2,figsize=(6.4,2.6)); fig.patch.set_facecolor(BG)
    scope(axs[0],t,v,vb,5,4,'Edge',f'pk {pk:.1f} V',-5,refline=V,refl=f'rail {V:g} V')
    axs[0].text(t[0]*1e9+9.9*4,-5+1.0*5,f'FET limit {R["vmax"]} V: 1 div above screen',color=TXT,fontsize=6.3,ha='right')
    zoff=V-3  # zoom: 1 V/div, rail 3 divs up
    m=t>=5e-9+tr-1e-9
    scope(axs[1],t[m],v[m],vb[m],1,2,'Zoom on the ring',f'+{dv:.1f} V  {R["f"]:.0f} MHz',zoff,refline=V,refl='rail')
    axs[1].text(t[m][0]*1e9+0.2,zoff+0.35*1,f'red: 4x loop L -> +{4*dv:.1f} V, {R["f"]/2:.0f} MHz',color=BAD,fontsize=6.6,bbox=dict(facecolor=BG,edgecolor='none',pad=1.5))
    fig.suptitle(title,color='white',fontsize=9,x=0.02,ha='left',weight='bold')
    fig.tight_layout(pad=0.3,rect=(0,0,1,0.92)); fig.savefig(f'{OUT}/hot-{slug(k)}.png',dpi=150,facecolor=BG); plt.close(fig)
    res[k]=dict(pk=float(pk),dv=dv,f=R['f'],pkbad=float(pkb))
    print(title, f'pk {pk:.2f} dv {dv:.2f} f {R["f"]:.0f} bad pk {pkb:.1f}')
for i,(k,o) in enumerate(gate.items()):
    hs='HS' in k; C=1180e-12 if hs else 1070e-12; L=o['L']+1e-9
    t,vr=sim_gate(9,L,C,3.4+2.3,rise=True); _,vf=sim_gate(9,L,C,1.0+2.3,rise=False)
    _,vbad=sim_gate(9,4*L,C,1.0+2.3,rise=False)
    fig,axs=plt.subplots(1,2,figsize=(6.4,2.6)); fig.patch.set_facecolor(BG)
    scope(axs[0],t,vr,None,2,5,'Turn-on (Vgs)',f'pk {vr.max():.1f} V',-4,refline=9,refl='9 V drive')
    scope(axs[1],t,vf,vbad,2,5,'Turn-off (Vgs)',f'min {vf.min():.1f} V',-4,refline=0,refl='0 V')
    axs[1].text(t[0]*1e9+0.5,-4+0.35*2,f'red: 4x loop L -> min {vbad.min():.1f} V',color=BAD,fontsize=6.8,bbox=dict(facecolor=BG,edgecolor='none',pad=1.5))
    fig.suptitle(k.replace('P1','Port 1').replace('P2','Port 2')+' gate drive',color='white',fontsize=9,x=0.02,ha='left',weight='bold')
    fig.tight_layout(pad=0.3,rect=(0,0,1,0.92)); fig.savefig(f'{OUT}/gate-{slug(k)}.png',dpi=150,facecolor=BG); plt.close(fig)
    res[k]=dict(on_pk=float(vr.max()),off_min=float(vf.min()),bad_min=float(vbad.min()))
    print(k, f'on pk {vr.max():.2f} off min {vf.min():.2f} bad {vbad.min():.2f}')
json.dump(res,open('scope.json','w'),indent=1)
