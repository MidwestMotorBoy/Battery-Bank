"""Linear thermal derate, one model for all three designs (lumped estimates, 25 C ambient, not measurements).
Nodes: board (B), Al cover/lid (L, where there is one), front cell pair (F, faces the board), back cell pair (K).
Firmware derate is linear, not a step: the allowed power falls from full to zero across a temperature band,
on whichever sensor is worst (board copper, hottest cell). Losses scale with power:
  board loss  = 0.024 P + 3.1e-4 P^2  (fits ~1.0 W at 30 W, ~2.5 W at 60 W, ~5.5 W at 100 W: schematic review 4)
  cell I2R    = 6.5e-4 P^2            (4 x ~30 mOhm FEB 21700G at 14.4 V; ~6.5 W at 100 W. Was 4.8e-4 for the EVE 58E)
  charging    = board 2.6 W and cells 3.7 W at 88 W (FEB), same shape. CC-CV taper is ignored.
Run: python thermal_derate.py  -> prints the scenario table; thermal_derate_visuals.py draws the sheet."""
import numpy as np
AMB = 25.0
CB, CPAIR = 20.0, 135.0                     # board (+ parts), each cell pair (J/K)
G_SKIN = 0.065                              # each cell pair -> skin -> air (W/K)
PACK_WH = 93.6                              # FEB 21700G, 6.5 Ah x 14.4 V (was 82 Wh with the EVE 58E)
# design: Al mass (g), board->Al, Al->air, board->front pair, front<->back pair, board->air (W/K)
DESIGNS = {
    'Current: 1 mm Al cover':  dict(al=9.5,  gbl=2.0, gla=0.039, gbf=0.04, gfk=0.06,  gba=0.0),    # TPU cage bands between the cells
    'Hybrid: 3 mm CNC lid':    dict(al=35.8, gbl=2.0, gla=0.053, gbf=0.04, gfk=0.032, gba=0.0),
    'Cup: coupled + PA12 webs': dict(al=0.0, gbl=0.0, gla=0.0,   gbf=0.30, gfk=0.11,  gba=0.021),
}
# linear derate bands (full power at or below the first temperature, zero at the second)
BANDS = dict(board=(60.0, 75.0),            # board copper: stays clear of the 81 C TS hardware stop
             cell_dis=(45.0, 55.0),         # hottest cell, discharging (cell limit 60 C)
             cell_chg=(40.0, 45.0))         # hottest cell, charging (cell limit 45 C)
def ramp(t, band):
    lo, hi = band
    return float(np.clip((hi - t) / (hi - lo), 0.0, 1.0))
def loss_dis(p): return 0.024*p + 3.1e-4*p*p, 6.5e-4*p*p
def loss_chg(p):
    x = p / 88.0; return 2.6*(0.4*x + 0.6*x*x), 3.7*x*x
def run(design, demand, mode='dis', hours=6.0, derate=True, dt=1.0):
    """demand: W (constant). Returns dict of arrays: t (min), P delivered, B, L, F, K, energy (Wh)."""
    d = DESIGNS[design]; CL = d['al']*0.90
    B = L = F = K = AMB; E = 0.0; rec = []
    for i in range(int(hours*3600/dt)):
        if derate:
            f = ramp(B, BANDS['board'])
            f = min(f, ramp(max(F, K), BANDS['cell_dis' if mode == 'dis' else 'cell_chg']))
        else: f = 1.0
        p = demand * f
        pb, pc = (loss_dis if mode == 'dis' else loss_chg)(p)
        qbl = d['gbl']*(B - L) if CL else 0.0; qbf = d['gbf']*(B - F); qfk = d['gfk']*(F - K)
        B += dt*(pb - qbl - qbf - d['gba']*(B - AMB)) / CB
        if CL: L += dt*(qbl - d['gla']*(L - AMB)) / CL
        F += dt*(pc/2 + qbf - qfk - G_SKIN*(F - AMB)) / CPAIR
        K += dt*(pc/2 + qfk - G_SKIN*(K - AMB)) / CPAIR
        # energy out of (discharge) or into (charge) the cells
        E += dt/3600 * ((p + pb + pc) if mode == 'dis' else (p - pb - pc))
        rec.append((i*dt/60, p, B, L if CL else np.nan, F, K, E))
        if E >= PACK_WH: break
    a = np.array(rec)
    return dict(t=a[:, 0], P=a[:, 1], B=a[:, 2], L=a[:, 3], F=a[:, 4], K=a[:, 5], E=a[:, 6])
def out_wh(r, minutes):
    """energy delivered at the port in the first `minutes` (1 s steps)"""
    return r['P'][r['t'] < minutes].sum() / 3600
def at(r, minutes, key='E'):
    i = np.searchsorted(r['t'], minutes); return r[key][min(i, len(r[key]) - 1)]

if __name__ == '__main__':
    print('30 W continuous, until empty (no derate engages if the peak stays under the bands)')
    for n in DESIGNS:
        r = run(n, 30.0)
        print(f"   {n:28s} {r['t'][-1]/60:4.2f} h   peak board {r['B'].max():4.0f} C   peak cells F/B {r['F'].max():3.0f}/{r['K'].max():3.0f} C   min power {r['P'].min():4.1f} W")
    print('100 W demand, linear derate, until empty')
    for n in DESIGNS:
        r = run(n, 100.0)
        print(f"   {n:28s} empty at {r['t'][-1]:5.1f} min   delivered in 20 min {out_wh(r, 20):4.1f} Wh   "
              f"P at 20 min {at(r, 20, 'P'):5.1f} W   mean P {np.mean(r['P']):5.1f} W   peak board {r['B'].max():3.0f}  cells {r['F'].max():3.0f}/{r['K'].max():3.0f}")
    print('88 W charge demand, linear derate, empty to full')
    for n in DESIGNS:
        r = run(n, 88.0, mode='chg')
        print(f"   {n:28s} full at {r['t'][-1]:5.1f} min   mean P {np.mean(r['P']):5.1f} W   peak board {r['B'].max():3.0f}  cells {r['F'].max():3.0f}/{r['K'].max():3.0f}")
