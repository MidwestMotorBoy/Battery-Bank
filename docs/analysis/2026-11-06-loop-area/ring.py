"""Ringing numbers from the loop inductances (no board needed).

The script that wrote ring.json on 2026-11-06 was not kept. This one recomputes the ring.json fields that the README
uses from hot_all.json and gate.json, with the same assumptions, and checks them against ring.json:

Hot loops (SW node at the rising edge):
    L     = eff_all + 0.3 nH FET package                  [nH]
    f     = 1 / (2 pi sqrt(L C)),  C = Coss                [MHz]
    Z0    = sqrt(L / C)                                    [ohm]
    dv    = L I / tr   (ring above the rail, 3 ns edge)    [V]
    peak  = V + dv     (expected SW peak)                  [V]
    bound = V + I Z0   (instant edge, worst case)          [V]
    tau   = Q / (pi f), Q = 8                              [ns]
Gate loops (series R-L-C, as scope.py):
    L = loop L + 1 nH package, C = Ciss (1180 pF HS, 1070 pF LS), R_off = 1.0 + 2.3 ohm
    f = 1 / (2 pi sqrt(L C)), zeta_off = R_off/2 sqrt(C/L), turn-off overshoot = exp(-pi zeta / sqrt(1 - zeta^2))

ring.json also carries EdB, lim and Icm, which this study does not use and this script does not recompute.
python3 ring.py  -> prints both tables, asserts the match, writes gate_ring.json
"""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
hot = json.load(open(os.path.join(HERE, 'hot_all.json'))); gate = json.load(open(os.path.join(HERE, 'gate.json')))
ring = json.load(open(os.path.join(HERE, 'ring.json')))
# (hot_all.json key, ring.json lab, rail V, switched current I [A], edge tr [s], Coss [F]), as in scope.py
SPEC = [('P1 VBUS leg (Q401)', 'Port 1 VBUS leg', 21, 5.0, 3e-9, 170e-12),
        ('P2 VBUS leg (Q501)', 'Port 2 VBUS leg', 21, 5.0, 3e-9, 170e-12),
        ('P1 PACK leg (Q402)', 'Port 1 PACK leg', 16.8, 6.8, 3e-9, 170e-12),
        ('P2 PACK leg (Q502)', 'Port 2 PACK leg', 16.8, 6.8, 3e-9, 170e-12),
        ('P1 5V buck (U404)', 'Port 1 5 V buck', 16.8, 3.0, 2e-9, 80e-12),
        ('P2 5V buck (U504)', 'Port 2 5 V buck', 16.8, 3.0, 2e-9, 80e-12),
        ('3V3 buck (U204)', '3V3 buck', 16.8, 0.5, 2e-9, 30e-12)]
Q = 8.0
byl = {r['lab']: r for r in ring}
print(f"{'loop':22s} {'L nH':>6s} {'f MHz':>6s} {'dv V':>5s} {'peak V':>7s} {'bound V':>8s} {'FET V':>6s}")
for k, lab, V, I, tr, C in SPEC:
    L = hot[k]['eff_all'] + 0.3e-9
    f = 1 / (2 * math.pi * math.sqrt(L * C)); Z0 = math.sqrt(L / C); dv = L * I / tr
    r = dict(L=L * 1e9, f=f / 1e6, Z0=Z0, dv=dv, peak=V + dv, bound=V + I * Z0, tau=Q / (math.pi * f) * 1e9)
    for a, b in r.items(): assert abs(b - byl[lab][a]) < 1e-6 * max(1, abs(b)), (lab, a, b, byl[lab][a])
    print(f"{k:22s} {r['L']:6.2f} {r['f']:6.0f} {dv:5.2f} {r['peak']:7.1f} {r['bound']:8.1f} {byl[lab]['vmax']:6d}")
out = {}
print(f"\n{'gate loop':24s} {'L nH':>5s} {'f MHz':>6s} {'zeta':>5s} {'overshoot':>9s}")
for k, o in gate.items():
    L = o['L'] + 1e-9; C = 1180e-12 if 'HS' in k else 1070e-12
    f = 1 / (2 * math.pi * math.sqrt(L * C)); z = (1.0 + 2.3) / 2 * math.sqrt(C / L)
    ov = math.exp(-math.pi * z / math.sqrt(1 - z * z)) if z < 1 else 0.0
    out[k] = dict(L_nH=round(o['L'] * 1e9, 2), f_MHz=round(f / 1e6, 1), zeta_off=round(z, 2), overshoot_off=round(ov, 3))
    print(f"{k:24s} {o['L']*1e9:5.1f} {f/1e6:6.0f} {z:5.2f} {ov*100:8.0f} %")
json.dump(out, open(os.path.join(HERE, 'gate_ring.json'), 'w'), indent=1)
print('\nring.json fields match.')
