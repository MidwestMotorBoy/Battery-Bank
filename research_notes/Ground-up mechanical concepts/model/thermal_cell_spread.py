"""Cup design, cells split into the front pair (gap filler to the board) and the back pair: how far apart do they run,
and what do PA12 webs or a gap-filler bead in the front-back gaps buy? Lumped estimates, 25 C ambient, not measurements.
Front-back conductances come from integrating k / gap across the two gaps (C1-C2, C4-C3) over the 70.8 mm cell length:
air alone 0.032 W/K; the carrier's PA12 webs (+-4.5 mm about the tangent, 0.05 mm air at each face) 0.11 W/K;
a gap-filler bead (k 3) about 2.0 W/K. Run: python thermal_cell_spread.py"""
import numpy as np
AMB, CB, CK2 = 25.0, 20.0, 135.0          # board; each cell pair (J/K)
G_B_F, G_B_AIR = 0.30, 0.021              # board -> front pair (vias + filler); board -> air (W/K)
G_SKIN = 0.065                            # each pair -> skin -> air
PROF = {100: (5.5, 4.8), 60: (2.5, 1.7), 30: (1.0, 0.4), 'charge88': (2.6, 2.7)}   # (board loss, cell I2R) W
COUP = {'air in the gaps': 0.032, 'PA12 webs (carrier)': 0.11, 'gap-filler bead': 2.0}
BOARD_LIM, CELL_LIM = 65.0, 55.0
def sim(gfb, steps, stop=None):
    B = F = K = AMB; out = []
    for p, dur in steps:
        pb, pk = PROF[p]
        for _ in range(int(dur)):
            qbf = G_B_F*(B - F); qfk = gfb*(F - K)
            B += (pb - qbf - G_B_AIR*(B - AMB)) / CB
            F += (pk/2 + qbf - qfk - G_SKIN*(F - AMB)) / CK2
            K += (pk/2 + qfk - G_SKIN*(K - AMB)) / CK2
            out.append((B, F, K))
            if stop and stop(B, F): return np.array(out)
    return np.array(out)
def summary(g):
    r = sim(g, [(100, 4*3600)], stop=lambda B, F: B >= BOARD_LIM or F >= CELL_LIM)
    lim = 'board' if r[-1, 0] >= BOARD_LIM else 'front cells'
    b = sim(g, [(100, 600), (30, 7200)]); s60 = sim(g, [(60, 6*3600)]); s30 = sim(g, [(30, 6*3600)]); ch = sim(g, [('charge88', 3600)])
    return dict(t100=len(r)/60, lim=lim, burst=(b[:, 1].max(), b[:, 2].max()), s60=(s60[-1, 1], s60[-1, 2]),
                spread30=(s30[:, 1] - s30[:, 2]).max(), charge=(ch[-1, 1], ch[-1, 2]), spread_max=max((b[:, 1]-b[:, 2]).max(), (ch[:, 1]-ch[:, 2]).max()))
if __name__ == '__main__':
    print(f"{'front-back coupling':24s}{'100 W until':>18s}{'burst peak F/B':>16s}{'60 W F/B':>12s}{'charge F/B':>13s}{'spread 30 W':>13s}{'max spread':>12s}")
    for name, g in COUP.items():
        s = summary(g)
        print(f"{name:24s}{s['t100']:7.1f} min ({s['lim']:>11s}){s['burst'][0]:8.0f} /{s['burst'][1]:3.0f}{s['s60'][0]:7.0f} /{s['s60'][1]:3.0f}"
              f"{s['charge'][0]:8.0f} /{s['charge'][1]:3.0f}{s['spread30']:11.1f} K{s['spread_max']:10.1f} K")
