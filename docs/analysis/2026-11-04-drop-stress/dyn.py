"""Multi-body impact of a 1 m drop along one pose direction d (no rotation): the shell lands on the floor through the
10-31 study's bumper force-crush curve, and the bodies inside (4 cells, carrier, rail blocks, board) are free masses
that meet each other and the shell through gap contacts from contacts.py (force = K_W x overlap volume, with contact
damping), the TPU pad through its gyroid law. Gives every contact's force against time and its peak.
Run: python dyn.py [pose ...] -> out/dyn_<pose>.json, cache/dyn_<pose>.npz"""
import os, sys, json, pickle, time, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, 'cache'); OUT = os.path.join(HERE, 'out')
sys.path.append(os.path.normpath(os.path.join(HERE, '..', '2026-10-31-drop-1m')))
import contact as FC, poses

G = 9.81
BODIES = ['shell', 'C1', 'C2', 'C3', 'C4', 'carrier', 'rails_tp', 'rails_tn', 'rails_bp', 'rails_bn', 'board']
E_PA12 = 1700.0
H_EFF = 2.5                                    # mm of PA12 behind a contact surface (Winkler layer)
K_W = E_PA12 / H_EFF                           # N/mm per mm3 of overlap
ZETA = 0.10                                    # contact damping (PA12 on PA12 / steel / FR4: restitution ~0.7)
ETA = 0.35                                     # bumper unloading / loading force (TPU hysteresis), as the 10-31 study
H_U = 0.0005; U_MAX = 1.0                      # resampled tables: penetration past first touch, mm
# series springs (N/mm) for what the Winkler layer leaves out: a cell's own give across and along its axis (can + jelly
# roll; lateral plate-crush slopes of 18650 / 21700 cells are ~4-10 kN/mm, axial ~20-50), and the USB-C receptacle
# moving on its solder tabs before its housing bears. PA12 structure compliance comes from the FE (fe_shell.py) later.
K_SERIES = dict(cell_radial=8e3, cell_axial=30e3, usb=3e3)
CELLS = ('C1', 'C2', 'C3', 'C4')

def series_kind(a, b):
    ab = (a, b)
    if any(k in CELLS for k in ab):
        o = b if a in CELLS else a
        if o in CELLS: return 'cell_radial2'                                 # can on can: both cans give
        return 'cell_axial' if o == 'carrier/frames' or o.endswith('/ends') else 'cell_radial'
    if 'board/usb' in ab: return 'usb'
    return None

def with_series(Fu, u, k):
    """the Winkler law F(u) in series with a spring k: u_total = u(F) + F / k, resampled on u"""
    if k is None: return Fu
    ut = u + Fu / k
    return np.interp(u, ut, Fu)
PAD_T_FREE = None                              # set from the params (installed + printed proud)

PART_BODY = {}
def body_of(k): return PART_BODY.get(k, k.split('/')[0])

def load(pose):
    return pickle.load(open(os.path.join(CACHE, f'tables_{pose}.pkl'), 'rb'))

def structure_k(pose):
    """per-contact structural springs from the FE (cup / cap flex at the patch, carrier flex), N/mm, if computed"""
    out = {}
    for f in (f'shellc_{pose}.json', f'corec_{pose}.json'):
        p = os.path.join(CACHE, f)
        if not os.path.exists(p): continue
        for k, v in json.load(open(p)).items():
            out[k] = 1 / (1 / out[k] + 1 / v['k_N_per_mm']) if k in out else v['k_N_per_mm']
    return out

def board_flex():
    import board_dyn
    try: return board_dyn.flex()
    except Exception as e:
        print('  board flex not available:', e, flush=True); return {}

def board_c(a, b, bfx):
    """the board's give (mm/N along x) at the contact a-b, if one side is the board"""
    if body_of(a) != 'board' and body_of(b) != 'board': return 0.0
    o = b if body_of(a) == 'board' else a; me = a if o == b else b
    if body_of(o).startswith('rails_'): return bfx.get(body_of(o), 0.0)
    if me == 'board/spacers': return bfx.get('spacers', 0.0)
    if me == 'board/usb': return bfx.get('usb', 0.0)
    if o == 'shell/lips': return bfx.get('lips', 0.0)
    return 0.0

def build_contacts(T, k_w=K_W, k_series=None, use_structure=True):
    """list of contacts: dict(a, b (body names), sense, feature, g0, Fu (force on the uniform u grid, N), slope)"""
    prm = T['prm']; d = T['d']; out = []; PART_BODY.update(T.get('part_body', {}))
    ks = dict(K_SERIES, **(k_series or {})); ks['cell_radial2'] = ks['cell_radial'] / 2
    kst = structure_k(T['pose']) if use_structure else {}
    bfx = board_flex()
    u = np.arange(0, U_MAX + H_U / 2, H_U)
    t_inst = prm['FR_B0'] - prm['Z_MOUTH']; t_free = t_inst + prm['PAD_PROUD']; e0 = prm['PAD_PROUD'] / t_free
    sig = lambda e: FC.gyroid(np.clip(e, 0, 0.97), round(prm['PAD_FILL'], 2))
    for (a, b), tb in T['pairs'].items():
        for sense in ('+', '-'):
            t = tb[sense]
            if t is None: continue
            g0, dl, V = t
            Vu = np.interp(g0 + u, dl, V); Vu = np.maximum(Vu - Vu[0], 0)          # zero force at first touch
            if b == 'shell/pad':
                dz = abs(d[2])
                if dz < 0.05: continue                                               # pad works along z only
                i = np.searchsorted(u, 0.02); A = max((Vu[i] - Vu[0]) / (u[i] * dz), 1.0)   # contact area (horizontal)
                pz = Vu / A                                                          # mean z squeeze, mm
                Fu = A * (sig(e0 + pz / t_free) - sig(e0)) * dz                      # its component along d
                kind = 'pad'
            else:
                kind = series_kind(a, b) or 'rigid'
                k1, k2 = ks.get(kind), kst.get(f'{a}|{b}|{sense}')
                c_b = board_c(a, b, bfx) * d[0]**2                                   # the board's own bending give
                if c_b > 1e-7: k2 = 1 / ((1 / k2 if k2 else 0) + c_b); kind += '+board' if kind != 'rigid' else ''
                k = None if k1 is None and k2 is None else 1 / ((1 / k1 if k1 else 0) + (1 / k2 if k2 else 0))
                Fu = with_series(k_w * Vu, u, k)
                if k2: kind += '+FE'
            if Fu[-1] <= 0: continue
            out.append(dict(a=a, b=b, A=body_of(a), B=body_of(b), sense=sense, g0=float(g0), Fu=Fu, kind=kind))
    return out, u

def simulate(T, contacts, u, v0=None, t_end=5e-3, dt=5e-8, zeta=ZETA, eta=ETA, rec=1e-6, floor_scale=1.0):
    m = np.array([T['masses'][k] for k in BODIES]) / 1000.0           # kg
    v0 = np.sqrt(2 * G * 1.0) if v0 is None else v0
    n = len(BODIES); idx = {k: i for i, k in enumerate(BODIES)}
    ia = np.array([idx[c['A']] for c in contacts]); ib = np.array([idx[c['B']] for c in contacts])
    sg = np.array([1.0 if c['sense'] == '+' else -1.0 for c in contacts])
    g0 = np.array([c['g0'] for c in contacts]); Fu = np.vstack([c['Fu'] for c in contacts])
    nu = Fu.shape[1]; slope = np.diff(Fu, axis=1) / H_U; slope = np.hstack([slope, slope[:, -1:]])
    mred = m[ia] * m[ib] / (m[ia] + m[ib])
    dlf, Ff = T['floor']; Ff = Ff * floor_scale
    x = np.zeros(n); v = np.full(n, v0); xmax = 0.0; t = 0.0
    hist_t, hist_F, hist_x, hist_a, hist_ff = [], [], [], [], []
    nxt = 0.0; nc = len(contacts); rows = np.arange(nc)
    while t < t_end:
        # floor on the shell (m, + toward the floor)
        dmm = x[0] * 1e3
        if dmm > 0:
            fl = np.interp(dmm, dlf, Ff)
            ff = fl if (v[0] >= 0 and x[0] >= xmax - 1e-12) else fl * eta
            xmax = max(xmax, x[0])
        else: ff = 0.0
        # contacts: delta (mm) = sense * (x_A - x_B)
        dl = sg * (x[ia] - x[ib]) * 1e3; uu = dl - g0
        on = uu > 0
        f = np.zeros(nc)
        if on.any():
            q = np.clip(uu[on] / H_U, 0, nu - 1.000001); i0 = q.astype(int); w = q - i0
            r = rows[on]
            fe = Fu[r, i0] * (1 - w) + Fu[r, i0 + 1] * w
            ext = uu[on] > U_MAX                                              # beyond the table: last slope
            if ext.any(): fe[ext] = Fu[r[ext], -1] + slope[r[ext], -1] * (uu[on][ext] - U_MAX)
            k_t = np.maximum(slope[r, i0], 1.0) * 1e3                         # N/m
            c = 2 * zeta * np.sqrt(k_t * mred[r])
            vrel = sg[r] * (v[ia[r]] - v[ib[r]])
            f[r] = np.maximum(fe + c * vrel, 0.0)
        # forces along d: A is pushed back (-sense), B forward (+sense)
        F = np.zeros(n); F[0] -= ff
        np.add.at(F, ia, -sg * f); np.add.at(F, ib, sg * f)
        a = F / m
        v += a * dt; x += v * dt; t += dt
        if t >= nxt:
            hist_t.append(t); hist_F.append(f.copy()); hist_x.append(x.copy()); hist_a.append(a / G); hist_ff.append(ff); nxt += rec
        if t > 3e-4 and np.all(v < -0.05) and ff == 0: break
    return dict(t=np.array(hist_t), F=np.array(hist_F), x=np.array(hist_x) * 1e3, a=np.array(hist_a), ff=np.array(hist_ff))

def summary(T, contacts, R):
    out = dict(pose=T['pose'], title=poses.TITLES[T['pose']], d=np.round(T['d'], 4).tolist(), floor_peak_N=float(R['ff'].max()),
               crush_mm=float(R['x'][:, 0].max()), bodies={}, contacts=[])
    for i, k in enumerate(BODIES):
        out['bodies'][k] = dict(peak_g=float(np.abs(R['a'][:, i]).max()), travel_mm=float((R['x'][:, i] - R['x'][:, 0]).max()))
    for j, c in enumerate(contacts):
        Fj = R['F'][:, j]
        if Fj.max() <= 0.5: continue
        i = int(Fj.argmax())
        out['contacts'].append(dict(a=c['a'], b=c['b'], sense=c['sense'], g0=round(c['g0'], 4), peak_N=round(float(Fj.max()), 1),
                                    t_ms=round(float(R['t'][i] * 1e3), 4), kind=c['kind']))
    out['contacts'].sort(key=lambda c: -c['peak_N'])
    return out

def run(pose, k_w=K_W, tag='', k_series=None, use_structure=True, **kw):
    T = load(pose); contacts, u = build_contacts(T, k_w, k_series, use_structure)
    t0 = time.time(); R = simulate(T, contacts, u, **kw)
    S = summary(T, contacts, R); S['k_w'] = k_w; S['runtime_s'] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    json.dump(S, open(os.path.join(OUT, f'dyn_{pose}{tag}.json'), 'w'), indent=1)
    np.savez_compressed(os.path.join(CACHE, f'dyn_{pose}{tag}.npz'), t=R['t'], F=R['F'], x=R['x'], a=R['a'], ff=R['ff'],
                        names=np.array([f"{c['a']}|{c['b']}|{c['sense']}" for c in contacts]))
    return S, R, contacts

if __name__ == '__main__':
    todo = sys.argv[1:] or poses.ORDER
    for p in todo:
        if not os.path.exists(os.path.join(CACHE, f'tables_{p}.pkl')): print('no tables for', p); continue
        S, R, c = run(p)
        b = S['bodies']
        print(f"{p:18s} floor {S['floor_peak_N']:7.0f} N crush {S['crush_mm']:.2f}  g: shell {b['shell']['peak_g']:5.0f} "
              + ' '.join(f"{k} {b[k]['peak_g']:5.0f}" for k in BODIES[1:]) + f"  ({S['runtime_s']} s)", flush=True)
        for cc in S['contacts'][:8]: print(f"     {cc['a']:8s} {cc['sense']} {cc['b']:18s} {cc['peak_N']:8.0f} N  g0 {cc['g0']:.3f}  t {cc['t_ms']:.3f} ms")
