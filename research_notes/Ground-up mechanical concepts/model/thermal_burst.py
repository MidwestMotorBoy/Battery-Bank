"""Lumped burst model (estimates, not measurements): board (B), Al cover/lid (L), cells (K), ambient 25 C. Forward Euler, 1 s steps.
Conductances are hand estimates; the dev-board 100 W thermal run should replace them. Run: python thermal_burst.py"""
import numpy as np
AMB = 25.0
# capacities (J/K): board 12.7 g bare FR4/Cu + ~10 g of parts; cells 284 g at ~0.95 J/gK; Al 0.90 J/gK
CB, CK = 20.0, 270.0
G_K_AMB = 0.13          # cells -> skin -> air (side walls; TPU-capped ends barely count)
DESIGNS = {
 # name: (Al mass g, G board->Al, G Al->air, G board->cells, G board->air direct)
 'current: 1.0 mm cover, gap pad, air gap to cells':        (9.5, 2.0, 0.039, 0.04, 0.0),
 'hybrid: 3 mm CNC lid':                                     (35.8, 2.0, 0.053, 0.04, 0.0),
 'no Al, board in air (no coupling)':                        (0.0, 0.0, 0.0, 0.04, 0.021),
 'no Al, board coupled to the cells (vias + gap filler)':    (0.0, 0.0, 0.0, 0.30, 0.021),
}
PROF = {100: (5.5, 4.8), 60: (2.5, 1.7), 30: (1.0, 0.4), 'charge88': (2.6, 2.7)}   # (board loss, cell I2R) W
def sim(d, steps, tmax=4*3600, stop=None):
    al, gbl, gla, gbk, gba = DESIGNS[d]; CL = max(al*0.90, 1e-6)
    B = L = K = AMB; out = []; t = 0
    for prof, dur in steps:
        pb, pk = PROF[prof]
        for _ in range(int(dur)):
            qbl = gbl*(B - L); qbk = gbk*(B - K)
            dB = (pb - qbl - qbk - gba*(B - AMB)) / CB
            dL = (qbl - gla*(L - AMB)) / CL if al else 0.0
            dK = (pk + qbk - G_K_AMB*(K - AMB)) / CK
            B += dB; K += dK; L = L + dL if al else AMB; t += 1
            out.append((t, B, L, K))
            if stop and stop(B, K): return np.array(out)
    return np.array(out)
BOARD_LIM, CELL_LIM = 65.0, 55.0       # board copper node (leaves ~15 K for FET-local rise below the 81 C TS stop); cell OT for discharge
if __name__ == '__main__':
    print('1) 100 W from 25 C: minutes until the board node hits 65 C or the cells hit 55 C')
    for d in DESIGNS:
        r = sim(d, [(100, 4*3600)], stop=lambda B, K: B >= BOARD_LIM or K >= CELL_LIM)
        t, B, L, K = r[-1]; why = 'board' if B >= BOARD_LIM else ('cells' if K >= CELL_LIM else 'none in 4 h')
        print(f'   {d:55s} {t/60:6.1f} min  (limit: {why}; board {B:.0f}, cells {K:.0f})')
    print('2) steady state (board / cells, C) at 30 W and 60 W')
    for d in DESIGNS:
        s = []
        for p in (30, 60):
            r = sim(d, [(p, 6*3600)]); s.append(f'{p} W: {r[-1,1]:.0f} / {r[-1,3]:.0f}')
        print(f'   {d:55s} ' + '   '.join(s))
    print('3) 10 min at 100 W, then 30 W for 2 h: peak board / peak cells')
    for d in DESIGNS:
        r = sim(d, [(100, 600), (30, 7200)]); print(f'   {d:55s} {r[:,1].max():.0f} / {r[:,3].max():.0f}')
    print('4) charging at 88 W for 60 min from 25 C: board / cells at the end (cells must stay under 45 C)')
    for d in DESIGNS:
        r = sim(d, [('charge88', 3600)]); print(f'   {d:55s} {r[-1,1]:.0f} / {r[-1,3]:.0f}')
