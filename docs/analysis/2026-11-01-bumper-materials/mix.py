"""Cap-end drop with mixed slab and pad materials (1 m; prints only)"""
import numpy as np, resin as R, drop as D, contact as C
rc = R.rc_case('bottom')
def bottom(slab_mat, slab_fill, pad_mat, pad_fill, t_scale=1.0):
    p = R.MATS[slab_mat]; q = R.MATS[pad_mat]
    rcx = dict(rc)
    if t_scale != 1.0:
        th = rc['thick'].copy(); m = rc['part'] == rc['names'].index('bumpb_slab'); th[m] *= t_scale; rcx['thick'] = th
    C.SCALE['tpu'] = C.SCALE['gyroid'] = p['E']; C.MAT['bumpb_slab'] = C.MAT['bumpt_slab'] = f'gyroid{round(slab_fill*100)}'
    dl, Fc = D.force_curve(rcx, dmax=9.0, step=0.01)
    D.PRM['PAD_FILL'] = pad_fill
    Fp0, _ = D.pad_curve()
    def Fp(x):   # pad stiffness in its own material
        s = C.SCALE['gyroid']; C.SCALE['tpu'] = C.SCALE['gyroid'] = q['E']; f = Fp0(x); C.SCALE['tpu'] = C.SCALE['gyroid'] = s; return f
    tr = D.simulate(dl, Fc, None, F_sc=Fp, eta=p['eta'], dt=2e-7)
    C.SCALE['tpu'] = C.SCALE['gyroid'] = 1.0
    return round(float(np.abs(tr[:, 8]).max())), round(float(tr[:, 1].max()*1e3), 2)
print('TPU slab 30 + TPU pad 15', bottom('TPU 95A (FDM)', .30, 'TPU 95A (FDM)', .15))
print('TPU slab 30 + 50A pad 45', bottom('TPU 95A (FDM)', .30, 'Flexible 50A', .45))
for t in (1.0, 5/3, 2.0):
    print(f'80A slab 40 x{t:.2f} thick + 80A pad 30', bottom('Flexible 80A V2', .40, 'Flexible 80A V2', .30, t))
    print(f'80A slab 40 x{t:.2f} thick + 50A pad 45', bottom('Flexible 80A V2', .40, 'Flexible 50A', .45, t))
