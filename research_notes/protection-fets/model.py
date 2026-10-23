import math
# name, Rtyp, Rmax (mOhm @10V), Qg10, Qgs, Qgd, Qg_at_plateau_end (nC), Vpl_ds, area_rel_vs_BSZ018, stock, price10, tjmax
P = [
 ("BSZ018N04LS6 (now)",   1.6, 1.8, 31, 5.6, 3.8, 9.4, 2.6, 1.0,  93, 1.52,175),
 ("TPHR8504PL",           0.70,0.85,103,12.4,25, 49, 3.0, 1.0*1.8/0.85, 29273, 0.79,175),
 ("BSC007N04LS6",         0.62,0.70, 94,17, 11.2,28.2,2.6, 1.8/0.70, 1471, 1.25,175),
 ("NTMFS5C410NL",         0.65,0.82,143,21.4,22,43.4,2.7, 1.8/0.82, 3954, 1.01,175),
 ("CSD18510Q5B",          0.79,0.96,118,28, 21, 49, 2.8, 1.8/0.96, 813, 1.20,150),
 ("BSC014N04LS",          1.1, 1.4, 61,11, 9.8,20.8,2.5, 1.2*1.8/1.4, 6834, None,175),
 ("HYG015N04LS1C2",       1.4, 1.7, 59,15, 8.5,23.5,3.0, 1.8/1.7, 16302, 0.49,175),
]
VB=16.8; Rext=0.040  # loop outside the two FETs (cells at 8 mohm AC each)
Rg=6e3; Vg0=13.5; Vpl=4.5; tdet=15e-6
I_load=105/14.0  # pack current at 100 W out
def zth(t, arel):
    us=t*1e6
    z = 0.2*(us/100)**0.5 if us<=100 else 0.2*(us/100)**0.756
    return z/arel
def run(delay, speedup):
    print(f"\nSCD delay {delay*1e6:.0f} us, {'PNP speed-up on Q102 (Rc sized for ~6 us Miller)' if speedup else 'gate via 5.1k only'}")
    print(f"{'part':22s} {'I_sc':>5s} {'P_on':>5s} {'t_on':>5s} {'dT_on':>6s} {'t_M':>5s} {'E_lin':>6s} {'dT_lin':>6s} {'I2t%':>5s} {'loss100W':>8s}")
    for n,Rt,Rm,Qg,Qgs,Qgd,Qpe,Vds_pl,arel,st,pr,tj in P:
        Rhot=Rm*1.3e-3
        I=VB/(Rext+2*Rhot)
        Ceff=(Qg-Qpe)*1e-9/(10-Vds_pl)
        if speedup:
            # Rc chosen so Miller time ~6 us at Vpl; pre-plateau through same Rc
            Ig_m=Qgd*1e-9/6e-6; Rc=(Vpl-0.7)/Ig_m
            tpre=Rc*Ceff*math.log((Vg0-0.7)/(Vpl-0.7)); tM=6e-6
        else:
            tpre=Rg*Ceff*math.log(Vg0/Vpl); tM=Qgd*1e-9/(Vpl/Rg)
        ton=tdet+delay+tpre
        Pon=I*I*Rhot
        dTon=Pon*zth(ton,arel)
        Plin=VB**2/(6*(Rext+Rhot))
        Elin=Plin*tM
        dTlin=Plin*zth(ton+tM,arel)-Plin*zth(ton,arel) + Plin*zth(tM,arel)*0  # approx superposition
        dTlin=Plin*zth(tM,arel)
        i2t=I*I*ton
        loss=2*I_load**2*Rt*1.25e-3
        extra=f" Rc~{Rc/1e3:.1f}k" if speedup else ""
        print(f"{n:22s} {I:5.0f} {Pon:5.0f} {ton*1e6:5.0f} {dTon:6.0f} {tM*1e6:5.1f} {Elin*1e3:6.1f} {dTlin:6.0f} {'':5s} {loss:8.3f}{extra}")
for d in (61e-6, 0):
    for s in (False, True):
        run(d,s)
