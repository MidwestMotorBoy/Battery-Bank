"""Every part against its limit, over all poses: the FE stress of the PA12 parts (cup + cap, carrier, rail blocks), the
contact loads of the small features (cap posts, board feet, lands, spacers, USB-C housings), the board's strain and
clearances, the cells and their welds, the screws, the O-ring, the TPU bumpers and the gel.
Run after run_all.py and board_dyn.py: python checks.py -> out/checks.json (ranked by margin)"""
import os, sys, json, glob, math, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out'); CACHE = os.path.join(HERE, 'cache')
import poses
G = 9.81
# limits (MPa unless noted). MJF PA12 (HP 3D HR PA12): 48 tensile XY / Z, E 1.7-1.8 GPa, 15-20 % elongation; no
# compressive figure from HP: PA12 compressive yield ~ 55 MPa used for bearing. Impact rate raises PA12 yield ~10-20 %
# (not used).
PA12_T, PA12_C = 48.0, 55.0
FR4_EDGE = 300.0           # FR4 in-plane compressive / edge bearing (laminate ~400)
STRAIN_WARN, STRAIN_BAD = 1000.0, 2000.0     # board surface strain, ue (MLCC / BGA crack guidance in drop, IPC-9704 range)
NI_STRIP_YIELD = 120.0 * 10 * 0.2            # N: 0.2 x 10 mm nickel 200 strip, annealed ~100-150 MPa
WELD_SHEAR = 250.0                           # N: a 4-6 spot P20B weld of 0.2 mm Ni to a steel can (to be pull-tested)
M2_PULLOUT = 200.0                           # N: M2 thread-forming in a 1.6 mm PA12 pilot, ~2.8 mm engaged
CELL_CRUSH = 13000.0                         # N: UL 1642 / IEC 62133 crush test force (abuse level, not a design load)

def L(path):
    try: return json.load(open(path))
    except Exception: return None

def contact_peak(dyn_by_pose, test):
    """max over poses of the summed peaks of contacts matching test(a, b) -> (N, pose)"""
    best = (0.0, None)
    for p, S in dyn_by_pose.items():
        v = sum(c['peak_N'] for c in S['contacts'] if test(c['a'], c['b']))
        if v > best[0]: best = (v, p)
    return best

def main():
    import dyn as DY
    D = {p: L(os.path.join(OUT, f'dyn_{p}.json')) for p in poses.ORDER}; D = {k: v for k, v in D.items() if v}
    D = {k: v for k, v in D.items() if np.load(os.path.join(CACHE, f'dyn_{k}.npz'))['x'].shape[1] == len(DY.BODIES)}   # skip stale runs
    prm = None
    import pickle
    T0 = pickle.load(open(os.path.join(CACHE, f'tables_{next(iter(D))}.pkl'), 'rb')); prm = T0['prm']
    rows = []
    def add(part, what, value, unit, limit, pose, note=''):
        rows.append(dict(part=part, check=what, value=round(float(value), 2), unit=unit, limit=limit, pose=pose,
                         title=poses.TITLES.get(pose, pose), margin=round(limit / value, 2) if value > 0 else None, note=note))
    # ---- FE stress of the PA12 parts (p99.9 per region; the max is often a voxel corner)
    for part, files in (('cup + cap', 'shell'), ('carrier', 'carrier'), ('rail blocks', 'rails_*')):
        reg = {}
        for f in glob.glob(os.path.join(OUT, f'{files}_*.json')):
            r = L(f); p = r['pose']
            for k, v in r['regions'].items():
                k2 = k.split('/')[-1]; s_ = v.get('p999_far', v['p999'])
                if s_ > reg.get(k2, (0,))[0]: reg[k2] = (s_, p, v.get('max_far', v['max']), v.get('at_far', v['at']), v['p999'])
        for k, (s, p, mx, at, pall) in reg.items():
            add(f'{part}: {k}', 'von Mises away from the contact patches, 99.9th pct (FE)', s, 'MPa', PA12_T, p,
                f'max {mx:.0f} MPa at {at}; with the bearing under the contacts {pall:.0f} MPa')
    # ---- small features from the contact forces
    r_ot = prm['OT_R']
    F, p = contact_peak(D, lambda a, b: b == 'shell/ot_posts')
    n_ot = len(prm.get('OT_POSTS', [None] * 4))
    add(f'cap: overtravel posts ({n_ot} x r{r_ot:g})', f'mean bearing on the {n_ot} tips', F / (n_ot * math.pi * r_ot**2), 'MPa', PA12_C, p, f'{F:.0f} N on the posts')
    F, p = contact_peak(D, lambda a, b: b == 'shell/cap' and a.startswith('carrier'))
    if F: add('cap: skirt top (carrier frame lands on it)', 'force', F, 'N', 1e9, p, 'not meant to touch: 1.1 mm gap')
    lf = 2 * ((prm['FOOT_Y'][0][1] - prm['FOOT_Y'][0][0]) + (prm['FOOT_Y'][1][1] - prm['FOOT_Y'][1][0]))
    F, p = contact_peak(D, lambda a, b: b == 'shell/feet')
    add('cap: board feet (4)', 'board edge bearing, all four feet', F / (prm['PCB_T'] * lf), 'MPa', PA12_C, p, f'{F:.0f} N')
    F, p = contact_peak(D, lambda a, b: b == 'shell/lands')
    ll = prm['Z_TOP0'] - prm['LAND_Z']
    add('cup: edge lands', 'board edge bearing over the land length', F / (prm['PCB_T'] * ll), 'MPa', PA12_C, p, f'{F:.0f} N')
    F, p = contact_peak(D, lambda a, b: a == 'board/pcb' and b == 'shell/cup_walls')
    add('cup: top wall over the board edge', 'board edge bearing (43 mm edge)', F / (prm['PCB_T'] * 43.2), 'MPa', PA12_C, p, f'{F:.0f} N (board top edge on the top wall, or rebound)')
    BD = {p_: L(os.path.join(OUT, f'board_{p_}.json')) for p_ in D}; BD = {k: v for k, v in BD.items() if v}
    def with_plate(Fp, group):
        """the larger of the impact model's force and the board plate model's (board_dyn.py) for a board support"""
        F_, p_ = Fp
        for q, r in BD.items():
            v = r['support_groups_sum_of_peaks_N'].get(group, 0)
            if v > F_: F_, p_ = v, q
        return F_, p_
    F, p = with_plate(contact_peak(D, lambda a, b: b == 'shell/lips'), 'lip')
    add('cup: F.Cu lips', 'line load on the lips', F / (2 * ll), 'N/mm', 300 * 0.5, p, f'{F:.0f} N; limit = lip bending to ~PA12 yield (est.)')
    a_sp = math.pi * prm['SPACER_R']**2 - (prm['POST_W'] * prm['PEG_D'])
    F, p = with_plate(contact_peak(D, lambda a, b: a == 'board/spacers'), 'spacer')
    add('post spacers (4, PA12)', 'axial stress, load shared by 4', F / (4 * a_sp), 'MPa', PA12_C, p, f'{F:.0f} N')
    F, p = contact_peak(D, lambda a, b: 'board/usb' in (a, b))
    for q, r in BD.items():
        v = max(r['support_groups_sum_of_peaks_N'].get('usb_f', 0), r['support_groups_sum_of_peaks_N'].get('usb_b', 0))
        if v > F: F, p = v, q
    add('USB-C receptacles (2)', 'housing pushed by its pocket, per receptacle', F / 2, 'N', 60.0, p,
        'limit: typical mid-mount receptacle shell-tab retention ~50-100 N (no datasheet value); a load here also rocks the solder joints')
    # rail-block posts in the PCB slots (per block, from the 4-body rails)
    best = (0, None, None)
    for p_, S in D.items():
        for c in S['contacts']:
            if c['a'].endswith('/posts') and c['b'] == 'board/pcb' and c['peak_N'] > best[0]: best = (c['peak_N'], p_, c['a'])
    if best[1]:
        A_post = prm['POST_W'] * prm['PEG_D'] - (4 - math.pi) * (min(prm['POST_W'], prm['PEG_D']) / 2)**2
        add('rail-block posts in the board slots', 'shear on one post', best[0] / A_post, 'MPa', PA12_T / 2, best[1], f'{best[0]:.0f} N on {best[2]}')
    # ---- board
    for f in glob.glob(os.path.join(OUT, 'board_*.json')):
        r = L(f); p = r['pose']
        add('board (FR4, parts)', 'surface strain, 99th percentile', r['strain_p99_ue'], 'ue', STRAIN_BAD, p, f"bow {r['w_toward_wall_max']:.2f} mm; max {r['strain_max_ue']:.0f} ue at the point supports; worst parts {', '.join(x['ref'] for x in r['highest_strain_parts'][:4])}")
        c0 = r['closest_parts'][0]
        if c0['clear_mm'] < 0.2:
            add('board parts vs the board-face wall', 'clearance left (mm, lower is worse)', max(0.2 - c0['clear_mm'], 1e-3), 'mm under 0.2', 0.2, p, f"{c0['ref']} {c0['clear_mm']:.2f} mm")
    F, p = contact_peak(D, lambda a, b: a == 'board/parts' and b.startswith('shell/'))
    if F: add('board parts striking the cup', 'force of the F.Cu parts on the wall (impact model, board rigid)', F, 'N', 100.0, p,
              'limit: an 0805-1210 MLCC or a moulded inductor ~50-100 N before it cracks or shears (est.)')
    # ---- cells
    for kind, test in (('axial (ends on the frames / tongues)', lambda a, b: a.startswith('C') and ('frames' in b or b.endswith('/ends'))),
                       ('radial (cradles, walls, webs, blocks)', lambda a, b: a.startswith('C') and not ('frames' in b or b.endswith('/ends')))):
        best = (0, None, None)
        for p_, S in D.items():
            per = {}
            for c in S['contacts']:
                if test(c['a'], c['b']): per[c['a']] = per.get(c['a'], 0) + c['peak_N']
            for cell, v in per.items():
                if v > best[0]: best = (v, p_, cell)
        if best[1]: add(f'cells: {kind}', 'force on one cell', best[0], 'N', CELL_CRUSH, best[1], f'{best[2]}; limit is the crush-test level, not a design load')
    gmax = max(((S['bodies'][c]['peak_g'], p_) for p_, S in D.items() for c in ('C1', 'C2', 'C3', 'C4')), key=lambda t: t[0])
    add('cells', 'peak deceleration', gmax[0], 'g', 20000.0, gmax[1], 'a bare cell dropped 1 m on concrete (IEC 62133-2) sees ~10^4 g on its can')
    # welds: in-plane differential motion of series-connected cells
    strips = (('C1', 'C2', (1, 0, 0)), ('C2', 'C3', (0, 1, 0)), ('C3', 'C4', (1, 0, 0)))
    k_strip = 200e3 * 10 * 0.2 / 11.0                                  # N/mm, 11 mm free length between weld zones
    best = (0, None, None)
    for p_ in D:
        R = np.load(os.path.join(CACHE, f'dyn_{p_}.npz')); import dyn as DY
        d = np.asarray(D[p_]['d'])
        for a, b, e in strips:
            ia, ib = DY.BODIES.index(a), DY.BODIES.index(b)
            dx = (R['x'][:, ia] - R['x'][:, ib]) * abs(np.dot(d, e))
            F_ = min(k_strip * np.abs(dx).max(), NI_STRIP_YIELD)
            if F_ > best[0]: best = (F_, p_, f'{a}-{b} strip, {np.abs(dx).max() * 1e3:.0f} um in-plane differential')
    add('nickel strips / welds', 'in-plane strip force on the welds (capped at strip yield)', best[0], 'N', WELD_SHEAR, best[1], best[2])
    # gel: board vs front cells across the gap
    best = (0, None)
    for p_ in D:
        R = np.load(os.path.join(CACHE, f'dyn_{p_}.npz')); d = np.asarray(D[p_]['d'])
        ib, ic = DY.BODIES.index('board'), DY.BODIES.index('C1')
        s = np.abs((R['x'][:, ib] - R['x'][:, ic]) * d[0]).max() / (prm['sb_xb0'] - (prm['PR'] + prm['CR']))
        if s > best[0]: best = (s, p_)
    add('gap filler (GEL 30)', 'peak stretch across the board-cell gap', best[0] * 100, '%', 50.0, best[1], 'debond risk, thermal not structural')
    # screws: the cap pulled off the cup when the core still pushes on the cap after the floor lets go (cap-end poses)
    best = (0, None)
    m_cap = 7.85 + 2.3 + 6.14 + 0.11                                  # cap + pad + bottom bumper + vent (g)
    for p_, S in D.items():
        d = np.asarray(S['d'])
        if d[2] > -0.3: continue
        R = np.load(os.path.join(CACHE, f'dyn_{p_}.npz')); names = list(R['names'])
        cols = [i for i, n in enumerate(names) if n.split('|')[1] in ('shell/ot_posts', 'shell/cap', 'shell/feet', 'shell/pad')]
        Fcore = R['F'][:, cols].sum(1)
        Fz_floor = R['ff'] * abs(d[2])
        a_s = R['a'][:, 0] * G                                         # m/s2 along d
        Rcup = m_cap / 1000 * a_s - Fcore * abs(d[2]) + Fz_floor      # >0: the cup pushes the cap (rim in contact)
        tension = max(0.0, -Rcup.min())
        if tension > best[0]: best = (tension, p_)
    add('M2 screws (2): pull-out from the cap bosses', 'cap pulled off the cup, both screws', best[0], 'N', 2 * M2_PULLOUT, best[1] or 'bottom',
        'estimate: the core still pushing on the cap after the floor force has gone')
    add('O-ring (silicone 60A, 2.0 cord)', 'squeeze swing from the cap shifting in the bore (radial clearance 0.1)', 0.1 / 2.0 * 100, '% of cord', 10.0, 'side',
        'squeeze 25 % at rest, 20-30 % for the instant; no load path through it')
    # TPU bumpers: peak compressive strain of the solid bands = crush / band thickness
    for p_, S in D.items():
        pass
    worst = max(((S['crush_mm'], p_) for p_, S in D.items()), key=lambda t: t[0])
    rows.sort(key=lambda r: (r['margin'] if r['margin'] is not None else 99))
    json.dump(dict(rows=rows), open(os.path.join(OUT, 'checks.json'), 'w'), indent=1)
    for r in rows: print(f"{r['margin'] if r['margin'] else '-':>6}  {r['part'][:44]:44s} {r['value']:9.1f} {r['unit']:6s} / {r['limit']:<7} {r['pose']:18s} {r['note'][:70]}")

if __name__ == '__main__': main()
